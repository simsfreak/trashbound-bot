import asyncio
import math
import os
import random

import discord

from db import queries
from game.data import ITEMS, MIX_RECIPES, REFINE_RECIPES, ZONES, get_live_events, MUSEUM_COLLECTIONS
from game.helpers import (
    determine_title,
    get_item_card_line,
    get_random_dive_midpoint,
    get_random_dive_reaction,
    get_random_dive_starter,
    get_recent_finds_from_inventory_rows,
    maybe_roll_dive_event,
    roll_item_for_zone,
)
from game.leveling import apply_xp
from ui.embeds import (
    dive_processing_embed,
    dive_result_embed,
    events_embed,
    help_embed,
    inventory_embed,
    mix_lab_embed,
    mix_result_embed,
    museum_artifact_embed,
    museum_collection_embed,
    museum_home_embed,
    pawn_offer_result_embed,
    pawn_shop_embed,
    profile_embed,
    zone_embed,
)
from ui.modals import ContactAdminModal


PAWN_REWARD_WEIGHTS: list[tuple[str, int]] = [
    ("scrap_metal", 30),
    ("old_shoe", 20),
    ("broken_phone", 16),
    ("mystery_box", 12),
    ("golden_potion", 8),
    ("iron_gloves", 6),
    ("glitch_charm", 4),
    ("rat_king_sigil", 3),
    ("trash_crown", 1),
]


def _weighted_reward_item_id() -> str:
    item_ids = []
    weights = []
    for item_id, weight in PAWN_REWARD_WEIGHTS:
        if item_id in ITEMS:
            item_ids.append(item_id)
            weights.append(weight)
    if not item_ids:
        return next(iter(ITEMS))
    return random.choices(item_ids, weights=weights, k=1)[0]


def _get_mixable_inventory_rows(user_id: int) -> list[tuple[str, int]]:
    rows = queries.get_inventory(user_id)
    mixable_rows: list[tuple[str, int]] = []
    for item_id, qty in rows:
        item = ITEMS.get(item_id, {})
        if item.get("kind") in {"material", "event", "failure"}:
            mixable_rows.append((item_id, qty))
    return mixable_rows


def _flatten_item_rows(rows: list[tuple[str, int]]) -> list[str]:
    expanded: list[str] = []
    for item_id, qty in rows:
        expanded.extend([item_id] * qty)
    return expanded


def _choose_pawn_bundle(user_id: int, max_items: int = 3) -> list[str]:
    inventory_rows = queries.get_inventory(user_id)
    pool: list[str] = []
    for item_id, qty in inventory_rows:
        item = ITEMS.get(item_id, {})
        kind = item.get("kind", "junk")
        if kind in {"junk", "material"} or item.get("pawnable", True):
            pool.extend([item_id] * qty)

    if not pool:
        return []

    random.shuffle(pool)
    return pool[: min(max_items, len(pool))]


def _bundle_counts(item_ids: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item_id in item_ids:
        counts[item_id] = counts.get(item_id, 0) + 1
    return counts


def _bundle_lines(item_ids: list[str]) -> list[str]:
    counts = _bundle_counts(item_ids)
    lines = []
    for item_id, qty in counts.items():
        item = ITEMS.get(item_id, {"name": item_id, "emoji": "✨", "coins": 0})
        lines.append(f"{item.get('emoji', '✨')} **{item['name']}** x{qty}")
    return lines


def _bundle_coin_offer(item_ids: list[str]) -> int:
    total = 0
    for item_id in item_ids:
        total += int(ITEMS.get(item_id, {}).get("coins", 0))
    return max(1, int(round(total * 1.15)))


def _remove_bundle_from_inventory(user_id: int, item_ids: list[str]) -> bool:
    counts = _bundle_counts(item_ids)
    for item_id, qty in counts.items():
        ok = queries.remove_item_from_inventory(user_id, item_id, qty)
        if not ok:
            return False
    return True


def _apply_coin_gain(user_id: int, gained_coins: int) -> None:
    player = queries.get_player(user_id)
    queries.update_player_progress(
        user_id=user_id,
        coins=player["coins"] + gained_coins,
        xp=player["xp"],
        level=player["level"],
        current_title=player["current_title"],
        total_dives=player["total_dives"],
    )


def _find_available_refine_recipe(inventory_map: dict[str, int]) -> dict | None:
    for recipe in REFINE_RECIPES:
        if all(inventory_map.get(item_id, 0) >= qty for item_id, qty in recipe["ingredients"].items()):
            return recipe
    return None


class InventoryActionSelect(discord.ui.Select):
    def __init__(self, parent_view: "InventoryView"):
        self.parent_view = parent_view
        options: list[discord.SelectOption] = []
        for item_id, qty in parent_view.current_page_items():
            item = ITEMS.get(item_id, {"name": item_id, "rarity": "Unknown", "kind": "junk", "emoji": "✨"})
            action = "Use" if item.get("kind") == "consumable" else ("Equip" if item.get("kind") == "equipment" else "Inspect")
            options.append(
                discord.SelectOption(
                    label=item["name"][:100],
                    value=item_id,
                    description=f"{item.get('rarity', 'Unknown')} • Qty {qty} • {action}"[:100],
                    emoji=item.get("emoji", "✨"),
                )
            )
        if not options:
            options = [discord.SelectOption(label="No items", value="noop", description="Go dive for loot first")]
        super().__init__(placeholder="Use / equip an item from this page", min_values=1, max_values=1, options=options, row=2)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "noop":
            await interaction.response.send_message("Nothing to use yet. Go get filthy first.", ephemeral=True)
            return

        item_id = self.values[0]
        item = ITEMS[item_id]
        kind = item.get("kind")

        if kind == "consumable":
            ok = queries.remove_item_from_inventory(interaction.user.id, item_id, 1)
            if not ok:
                await interaction.response.send_message("You don't have that item anymore.", ephemeral=True)
                return
            queries.add_active_effect(
                user_id=interaction.user.id,
                effect_id=item["effect_id"],
                source_item_id=item_id,
                label=item["effect_label"],
                multiplier=item["effect_multiplier"],
                duration_minutes=item["duration_minutes"],
            )
            await interaction.response.send_message(
                f"{item['emoji']} **{item['name']}** activated — {item['use_text']}",
                ephemeral=True,
            )
        elif kind == "equipment":
            slot = item.get("equip_slot", "misc")
            queries.equip_item(interaction.user.id, slot, item_id)
            await interaction.response.send_message(
                f"{item['emoji']} **{item['name']}** equipped in **{slot}**. {item.get('equip_bonus', '')}",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(get_item_card_line(item_id), ephemeral=True)


class InventoryView(discord.ui.View):
    def __init__(self, owner_id: int, is_admin: bool, items: list[tuple[str, int]], page: int = 0, page_size: int = 6):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.is_admin = is_admin
        self.items = items
        self.page = page
        self.page_size = page_size
        self.refresh_select()

    def refresh_select(self) -> None:
        for child in list(self.children):
            if isinstance(child, InventoryActionSelect):
                self.remove_item(child)
        self.add_item(InventoryActionSelect(self))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This inventory isn't yours.", ephemeral=True)
            return False
        return True

    def current_page_items(self) -> list[tuple[str, int]]:
        start = self.page * self.page_size
        end = start + self.page_size
        return self.items[start:end]

    def page_lines(self) -> list[str]:
        lines = []
        for item_id, qty in self.current_page_items():
            item = ITEMS.get(item_id, {"name": item_id, "rarity": "Unknown", "coins": 0, "emoji": "✨", "kind": "junk"})
            kind = item.get("kind", "junk").title()
            use_text = item.get("use_text") or item.get("equip_bonus") or item.get("flavor", "")
            lines.append(
                f"{item.get('emoji', '✨')} **{item['name']}**\n"
                f"{item['rarity']} • {kind} • Qty: {qty} • Sell: {item['coins']}\n"
                f"*{use_text}*"
            )
        return lines

    @property
    def total_pages(self) -> int:
        return max(1, math.ceil(len(self.items) / self.page_size))

    @discord.ui.button(label="⬅️ Back", style=discord.ButtonStyle.secondary, row=0)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
        self.refresh_select()
        embed = inventory_embed(interaction.user.display_name, self.page_lines(), self.page, self.total_pages)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="➡️ Next", style=discord.ButtonStyle.secondary, row=0)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page < self.total_pages - 1:
            self.page += 1
        self.refresh_select()
        embed = inventory_embed(interaction.user.display_name, self.page_lines(), self.page, self.total_pages)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🔄 Reload", style=discord.ButtonStyle.secondary, row=1)
    async def reload_inventory(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.items = queries.get_inventory(interaction.user.id)
        self.refresh_select()
        embed = inventory_embed(interaction.user.display_name, self.page_lines(), self.page, self.total_pages)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🏠 Back to Profile", style=discord.ButtonStyle.primary, row=1)
    async def back_to_profile(self, interaction: discord.Interaction, button: discord.ui.Button):
        await show_profile(interaction, self.owner_id, self.is_admin)


class ZoneSelectorView(discord.ui.View):
    def __init__(self, owner_id: int, is_admin: bool, zone_ids: list[str], index: int = 0):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.is_admin = is_admin
        self.zone_ids = zone_ids
        self.index = index

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("That map isn't yours.", ephemeral=True)
            return False
        return True

    def current_zone_id(self) -> str:
        return self.zone_ids[self.index]

    def build_embed(self, interaction: discord.Interaction) -> discord.Embed:
        player = queries.get_player(interaction.user.id)
        unlocked_zone_ids = set(queries.get_unlocked_zone_ids(interaction.user.id))
        zone_id = self.current_zone_id()
        loot_lines = []
        for item_id, item in ITEMS.items():
            if zone_id in item.get("zone_ids", []):
                loot_lines.append(f"{item.get('emoji', '✨')} {item['name']} • {item['rarity']}")
        return zone_embed(player, zone_id, unlocked_zone_ids, loot_lines[:6], self.index, len(self.zone_ids))

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.secondary, row=0)
    async def previous_zone(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index = (self.index - 1) % len(self.zone_ids)
        await interaction.response.edit_message(embed=self.build_embed(interaction), view=self)

    @discord.ui.button(label="✅ Set Active", style=discord.ButtonStyle.success, row=0)
    async def set_active_zone(self, interaction: discord.Interaction, button: discord.ui.Button):
        zone_id = self.current_zone_id()
        unlocked = set(queries.get_unlocked_zone_ids(interaction.user.id))
        if zone_id not in unlocked:
            await interaction.response.send_message("That zone is still locked. Keep grinding, goblin.", ephemeral=True)
            return
        queries.set_current_zone(interaction.user.id, zone_id)
        await interaction.response.edit_message(embed=self.build_embed(interaction), view=self)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.secondary, row=0)
    async def next_zone(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index = (self.index + 1) % len(self.zone_ids)
        await interaction.response.edit_message(embed=self.build_embed(interaction), view=self)

    @discord.ui.button(label="🏠 Back", style=discord.ButtonStyle.primary, row=1)
    async def back_to_profile(self, interaction: discord.Interaction, button: discord.ui.Button):
        await show_profile(interaction, self.owner_id, self.is_admin)


class PawnShopView(discord.ui.View):
    def __init__(self, owner_id: int, is_admin: bool, bundle_item_ids: list[str] | None = None):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.is_admin = is_admin
        self.bundle_item_ids = bundle_item_ids or []

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This sketchy deal isn't yours.", ephemeral=True)
            return False
        return True

    def ensure_bundle(self, user_id: int) -> None:
        if not self.bundle_item_ids:
            self.bundle_item_ids = _choose_pawn_bundle(user_id)

    def build_embed(self, user_id: int) -> discord.Embed:
        self.ensure_bundle(user_id)
        return pawn_shop_embed(self.bundle_item_ids)

    @discord.ui.button(label="🎁 Blind Box Deal", style=discord.ButtonStyle.primary, row=0)
    async def blind_box(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.ensure_bundle(interaction.user.id)
        if not self.bundle_item_ids:
            await interaction.response.edit_message(
                embed=pawn_offer_result_embed("
