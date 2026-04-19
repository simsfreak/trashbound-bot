import asyncio
import math
import os
import random

import discord

from db import queries
from game.data import ITEMS, MIX_RECIPES, REFINE_RECIPES, ZONES, get_live_events, MUSEUM_COLLECTIONS
from ui.embeds import (
    dive_processing_embed,
    dive_result_embed,
    events_embed,
    help_embed,
    inventory_embed,
    mix_lab_embed,
    mix_result_embed,
    pawn_offer_result_embed,
    pawn_shop_embed,
    profile_embed,
    zone_embed,
    museum_home_embed,
    museum_collection_embed,
    museum_artifact_embed,
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
        if item.get("mixable", item.get("kind", "junk") == "junk"):
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
            await interaction.response.send_message(f"{get_item_card_line(item_id)}", ephemeral=True)


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
                embed=pawn_offer_result_embed("🏚️ Sketchy Pawn Shop", "The owner squints at your empty hands. No junk, no deal."),
                view=self,
            )
            return

        if not _remove_bundle_from_inventory(interaction.user.id, self.bundle_item_ids):
            await interaction.response.send_message("You don't have those exact rummages anymore.", ephemeral=True)
            return

        reward_item_id = _weighted_reward_item_id()
        queries.add_item_to_inventory(interaction.user.id, reward_item_id, 1)
        reward_item = ITEMS.get(reward_item_id, {"name": reward_item_id, "emoji": "✨", "rarity": "Unknown"})
        result_text = (
            "You take the risky box. The owner cackles.\n\n"
            f"Disposed bundle:\n{chr(10).join(_bundle_lines(self.bundle_item_ids))}\n\n"
            f"You received:\n{reward_item.get('emoji', '✨')} **{reward_item['name']}**\n"
            f"{reward_item.get('rarity', 'Unknown')}\n"
            f"*{reward_item.get('flavor', 'No refunds. No crying.')}*"
        )
        self.bundle_item_ids = _choose_pawn_bundle(interaction.user.id)
        await interaction.response.edit_message(embed=pawn_offer_result_embed("🎁 Blind Box Deal", result_text), view=self)

    @discord.ui.button(label="💰 Take Coins", style=discord.ButtonStyle.success, row=0)
    async def take_coins(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.ensure_bundle(interaction.user.id)
        if not self.bundle_item_ids:
            await interaction.response.edit_message(
                embed=pawn_offer_result_embed("🏚️ Sketchy Pawn Shop", "The owner shrugs. No rummage pile, no coins."),
                view=self,
            )
            return

        offer = _bundle_coin_offer(self.bundle_item_ids)
        if not _remove_bundle_from_inventory(interaction.user.id, self.bundle_item_ids):
            await interaction.response.send_message("You don't have those exact rummages anymore.", ephemeral=True)
            return

        _apply_coin_gain(interaction.user.id, offer)
        result_text = (
            f"You take the safer deal and pocket **{offer} coins**.\n\n"
            f"Sold bundle:\n{chr(10).join(_bundle_lines(self.bundle_item_ids))}\n\n"
            "The owner grins like he still got the better end."
        )
        self.bundle_item_ids = _choose_pawn_bundle(interaction.user.id)
        await interaction.response.edit_message(embed=pawn_offer_result_embed("💰 Sketchy Cashout", result_text), view=self)

    @discord.ui.button(label="🔄 New Offers", style=discord.ButtonStyle.secondary, row=1)
    async def reroll_offers(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.bundle_item_ids = _choose_pawn_bundle(interaction.user.id)
        await interaction.response.edit_message(embed=self.build_embed(interaction.user.id), view=self)

    @discord.ui.button(label="🏠 Back", style=discord.ButtonStyle.secondary, row=1)
    async def back_to_profile(self, interaction: discord.Interaction, button: discord.ui.Button):
        await show_profile(interaction, self.owner_id, self.is_admin)


class MixLabView(discord.ui.View):
    def __init__(self, owner_id: int, is_admin: bool):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.is_admin = is_admin

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This lab isn't yours.", ephemeral=True)
            return False
        return True

    def build_embed(self, user_id: int) -> discord.Embed:
        inventory_map = queries.get_inventory_map(user_id)
        available_lines = []
        for recipe in MIX_RECIPES:
            ready = all(inventory_map.get(item_id, 0) >= qty for item_id, qty in recipe["ingredients"].items())
            available_lines.append(f"{'✅' if ready else '🔒'} {recipe['description']}")
        return mix_lab_embed(inventory_map, available_lines)

    @discord.ui.button(label="🎲 Start Mixing", style=discord.ButtonStyle.primary, row=0)
    async def chaos_mix(self, interaction: discord.Interaction, button: discord.ui.Button):
        inventory_rows = _get_mixable_inventory_rows(interaction.user.id)
        mix_pool = _flatten_item_rows(inventory_rows)

        if len(mix_pool) < 5:
            embed = mix_result_embed(
                "🎲 Mix Lobby",
                "You need at least **5 mixable rummage items** before you can start the blender of bad decisions.",
            )
            await interaction.response.edit_message(embed=embed, view=self)
            return

        chosen_item_ids = random.sample(mix_pool, 5)
        warning_lines = _bundle_lines(chosen_item_ids)

        if random.random() < 0.55:
            for item_id, qty in _bundle_counts(chosen_item_ids).items():
                queries.remove_item_from_inventory(interaction.user.id, item_id, qty)

            reward_count = 2 if random.random() < 0.25 else 1
            reward_ids: list[str] = []
            for _ in range(reward_count):
                reward_id = _weighted_reward_item_id()
                reward_ids.append(reward_id)
                queries.add_item_to_inventory(interaction.user.id, reward_id, 1)

            reward_lines = []
            for reward_id in reward_ids:
                reward_item = ITEMS.get(reward_id, {"name": reward_id, "emoji": "✨", "rarity": "Unknown"})
                reward_lines.append(f"{reward_item.get('emoji', '✨')} **{reward_item['name']}** — {reward_item.get('rarity', 'Unknown')}")

            embed = mix_result_embed(
                "🧪 Mix Success",
                "The goblin blender somehow worked.\n\n"
                f"Consumed:\n{chr(10).join(warning_lines)}\n\n"
                f"Gained:\n{chr(10).join(reward_lines)}",
            )
            await interaction.response.edit_message(embed=embed, view=self)
            return

        for item_id, qty in _bundle_counts(chosen_item_ids).items():
            queries.remove_item_from_inventory(interaction.user.id, item_id, qty)

        embed = mix_result_embed(
            "💥 Mix Failure",
            "You lost the mix.\n\n"
            f"Disposed:\n{chr(10).join(warning_lines)}\n\n"
            "The pile smoked, hissed, and gave you absolutely nothing back.",
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🧃 Brew Potion", style=discord.ButtonStyle.secondary, row=1)
    async def brew_potion(self, interaction: discord.Interaction, button: discord.ui.Button):
        inventory_map = queries.get_inventory_map(interaction.user.id)
        recipe = next((r for r in MIX_RECIPES if r["result_item_id"] == "golden_potion"), None)
        if recipe is None or not all(inventory_map.get(item_id, 0) >= qty for item_id, qty in recipe["ingredients"].items()):
            embed = mix_result_embed("🧃 Brew Potion", "Need **Mystery Box x1 + Scrap Metal x2** to brew Golden Potion.")
            await interaction.response.edit_message(embed=embed, view=self)
            return
        for item_id, qty in recipe["ingredients"].items():
            queries.remove_item_from_inventory(interaction.user.id, item_id, qty)
        queries.add_item_to_inventory(interaction.user.id, "golden_potion", 1)
        item = ITEMS["golden_potion"]
        embed = mix_result_embed("🧃 Potion Brewed", f"{item['emoji']} **{item['name']}** x1\n{item['rarity']} • Consumable\n*{item['use_text']}*")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🏠 Back", style=discord.ButtonStyle.primary, row=2)
    async def back_to_profile(self, interaction: discord.Interaction, button: discord.ui.Button):
        await show_profile(interaction, self.owner_id, self.is_admin)


class DiveResultView(discord.ui.View):
    def __init__(self, owner_id: int, is_admin: bool):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.is_admin = is_admin

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("That loot isn't yours.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="🗑️ Dive Again", style=discord.ButtonStyle.primary, row=0)
    async def dive_again(self, interaction: discord.Interaction, button: discord.ui.Button):
        await run_dive_sequence(interaction, self.owner_id, self.is_admin)

    @discord.ui.button(label="🏠 Back to Profile", style=discord.ButtonStyle.secondary, row=0)
    async def back_to_profile(self, interaction: discord.Interaction, button: discord.ui.Button):
        await show_profile(interaction, self.owner_id, self.is_admin)


class ProfileView(discord.ui.View):
    def __init__(self, owner_id: int, is_admin: bool):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.is_admin = is_admin
        if is_admin:
            self.add_item(AdminButton(row=3))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This menu isn't yours. Open your own with /profile.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="🗑️ Dive", style=discord.ButtonStyle.primary, row=0)
    async def dive_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await run_dive_sequence(interaction, self.owner_id, self.is_admin)

    @discord.ui.button(label="🎒 Loot", style=discord.ButtonStyle.secondary, row=0)
    async def inventory_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        inventory = queries.get_inventory(interaction.user.id)
        view = InventoryView(self.owner_id, self.is_admin, inventory, page=0)
        embed = inventory_embed(interaction.user.display_name, view.page_lines(), view.page, view.total_pages)
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="🏚️ Pawn Shop", style=discord.ButtonStyle.success, row=0)
    async def pawn_shop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = PawnShopView(self.owner_id, self.is_admin)
        await interaction.response.edit_message(embed=view.build_embed(interaction.user.id), view=view)

    @discord.ui.button(label="🧪 Mix", style=discord.ButtonStyle.secondary, row=1)
    async def mix_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = MixLabView(self.owner_id, self.is_admin)
        await interaction.response.edit_message(embed=view.build_embed(interaction.user.id), view=view)

    @discord.ui.button(label="🗺️ Zones", style=discord.ButtonStyle.success, row=1)
    async def zones_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        zone_ids = list(ZONES.keys())
        current_zone_id = queries.get_player(interaction.user.id)["current_zone_id"]
        start_index = zone_ids.index(current_zone_id)
        view = ZoneSelectorView(self.owner_id, self.is_admin, zone_ids=zone_ids, index=start_index)
        await interaction.response.edit_message(embed=view.build_embed(interaction), view=view)

    @discord.ui.button(label="✨ Events", style=discord.ButtonStyle.danger, row=1)
    async def events_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=events_embed(), view=ProfileView(self.owner_id, self.is_admin))

    @discord.ui.button(label="❓ Help", style=discord.ButtonStyle.secondary, row=2)
    async def instructions_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=help_embed(), view=ProfileView(self.owner_id, self.is_admin))

    @discord.ui.button(label="💌 Contact Admin", style=discord.ButtonStyle.secondary, row=2)
    async def contact_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ContactAdminModal())

    @discord.ui.button(label="🔄 Refresh", style=discord.ButtonStyle.secondary, row=2)
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await show_profile(interaction, self.owner_id, self.is_admin)


class AdminButton(discord.ui.Button):
    def __init__(self, row: int = 2):
        super().__init__(label="Admin", emoji="🛠️", style=discord.ButtonStyle.danger, row=row)

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🛠️ Admin Panel",
            description="Admin tools are coming next:\n• View messages\n• Grant XP\n• Grant coins\n• Grant items\n• Trigger events",
            color=0xED4245,
        )
        await interaction.response.edit_message(embed=embed, view=self.view)


async def run_dive_sequence(interaction: discord.Interaction, owner_id: int, is_admin: bool) -> None:
    player = queries.get_player(interaction.user.id)
    rare_bonus = 0.0
    coin_multiplier = 1.0
    xp_multiplier = 1.0
    extra_item_chance = 0.0
    event_text_parts: list[str] = []

    for event in get_live_events():
        rare_bonus += float(event.get("rare_bonus", 0.0))
        coin_multiplier *= float(event.get("coin_multiplier", 1.0))
        xp_multiplier *= float(event.get("xp_multiplier", 1.0))
        extra_item_chance += float(event.get("extra_item_chance", 0.0))
        event_text_parts.append(f"{event['emoji']} **{event['name']}** is live")

    equipped = queries.get_equipment(interaction.user.id)
    for entry in equipped:
        item = ITEMS.get(entry["item_id"], {})
        if item.get("equip_slot") == "hands":
            coin_multiplier *= 1.10
        if item.get("equip_slot") == "feet":
            xp_multiplier += 5 / max(1, ITEMS.get("scrap_metal", {}).get("xp", 1))
        if item.get("equip_slot") == "trinket":
            rare_bonus += 0.08
        if item.get("equip_slot") == "charm":
            extra_item_chance += 0.12

    xp_effect = queries.get_effect_multiplier(interaction.user.id, "xp_boost")
    xp_multiplier *= xp_effect

    zone_name = ZONES[player["current_zone_id"]]["name"]

    if interaction.response.is_done():
        await interaction.edit_original_response(embed=dive_processing_embed(zone_name, get_random_dive_starter()), view=None, attachments=[])
    else:
        await interaction.response.edit_message(embed=dive_processing_embed(zone_name, get_random_dive_starter()), view=None, attachments=[])

    await asyncio.sleep(1.0)
    await interaction.edit_original_response(embed=dive_processing_embed(zone_name, get_random_dive_midpoint()), view=None, attachments=[])
    await asyncio.sleep(1.0)

    item_id, item = roll_item_for_zone(player["current_zone_id"], rare_bonus=rare_bonus)
    gained_coins = max(1, int(round(item["coins"] * coin_multiplier)))
    gained_xp = max(1, int(round(item["xp"] * xp_multiplier)))

    bonus_event = maybe_roll_dive_event()
    bonus_text = None
    if bonus_event:
        gained_coins += bonus_event["bonus_coins"]
        gained_xp += bonus_event["bonus_xp"]
        bonus_text = bonus_event["text"]

    new_xp, new_level, leveled_up = apply_xp(player["xp"], player["level"], gained_xp)
    new_title = determine_title(new_level)
    new_coins = player["coins"] + gained_coins
    new_dives = player["total_dives"] + 1

    queries.add_item_to_inventory(interaction.user.id, item_id, 1)
    queries.update_player_progress(
        user_id=interaction.user.id,
        coins=new_coins,
        xp=new_xp,
        level=new_level,
        current_title=new_title,
        total_dives=new_dives,
    )
    unlocked_zone_ids = queries.unlock_zones_for_level(interaction.user.id, new_level)
    unlocked_zone_names = [ZONES[zone_id]["name"] for zone_id in unlocked_zone_ids]

    if extra_item_chance > 0 and random.random() <= extra_item_chance:
        extra_item_id, _extra_item = roll_item_for_zone(player["current_zone_id"], rare_bonus=rare_bonus)
        queries.add_item_to_inventory(interaction.user.id, extra_item_id, 1)
        bonus_text = (bonus_text + "\n" if bonus_text else "") + f"🎁 Bonus drop: {ITEMS[extra_item_id]['emoji']} **{ITEMS[extra_item_id]['name']}**"

    for event in get_live_events():
        event_item_id = event.get("event_item_id")
        if event_item_id and random.random() <= 0.12:
            queries.add_item_to_inventory(interaction.user.id, event_item_id, 1)
            bonus_text = (bonus_text + "\n" if bonus_text else "") + f"{ITEMS[event_item_id]['emoji']} Event drop: **{ITEMS[event_item_id]['name']}**"

    updated_player = queries.get_player(interaction.user.id)
    reaction_text = get_random_dive_reaction()
    event_text = " • ".join(event_text_parts) if event_text_parts else None

    embed = dive_result_embed(
        updated_player,
        item_id,
        leveled_up,
        reaction_text=reaction_text,
        event_text=event_text,
        bonus_text=bonus_text,
        unlocked_zone_names=unlocked_zone_names,
        avatar_url=interaction.user.display_avatar.url,
    )

    image_path = ITEMS[item_id].get("image")
    if image_path and not image_path.startswith("http") and os.path.exists(image_path):
        safe_name = f"{item_id}_{random.randint(1000, 999999)}.png"
        file = discord.File(image_path, filename=safe_name)
        embed.set_image(url=f"attachment://{safe_name}")
        await interaction.edit_original_response(
            embed=embed,
            attachments=[file],
            view=DiveResultView(owner_id, is_admin),
        )
    else:
        await interaction.edit_original_response(
            embed=embed,
            attachments=[],
            view=DiveResultView(owner_id, is_admin),
        )


def build_profile_embed_for_user(user: discord.abc.User | discord.Member) -> discord.Embed:
    player = queries.get_player(user.id)
    inventory = queries.get_inventory(user.id)
    recent_finds = get_recent_finds_from_inventory_rows(inventory)
    active_effects = queries.get_active_effects(user.id)
    equipment = queries.get_equipment(user.id)

    return profile_embed(
        player=player,
        inventory_count=sum(q for _, q in inventory),
        recent_finds=recent_finds,
        active_effects=active_effects,
        equipment=equipment,
        avatar_url=user.display_avatar.url,
    )

def build_museum_home_embed_for_user(user: discord.abc.User | discord.Member) -> discord.Embed:
    discovered = queries.get_discovered_item_ids(user.id)
    return museum_home_embed(user.display_name, discovered)
class MuseumCollectionSelect(discord.ui.Select):
    def __init__(self, owner_id: int, is_admin: bool):
        self.owner_id = owner_id
        self.is_admin = is_admin
        options = [
            discord.SelectOption(
                label=collection["name"][:100],
                value=collection_id,
                description=collection["description"][:100],
                emoji=collection.get("emoji", "🏛️"),
            )
            for collection_id, collection in MUSEUM_COLLECTIONS.items()
        ]
        super().__init__(
            placeholder="Choose a museum collection",
            min_values=1,
            max_values=1,
            options=options,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction):
        collection_id = self.values[0]
        view = MuseumCollectionView(self.owner_id, self.is_admin, collection_id=collection_id, page=0)
        embed = view.build_embed(interaction.user)
        await interaction.response.edit_message(embed=embed, view=view)


class MuseumArtifactSelect(discord.ui.Select):
    def __init__(self, parent_view: "MuseumCollectionView"):
        self.parent_view = parent_view
        options: list[discord.SelectOption] = []

        for item_id in parent_view.current_page_item_ids():
            item = ITEMS.get(item_id, {"name": item_id, "emoji": "✨"})
            discovered = item_id in parent_view.discovered_item_ids
            options.append(
                discord.SelectOption(
                    label=(item["name"] if discovered else "Unknown Artifact")[:100],
                    value=item_id,
                    description=("View archived artifact card" if discovered else "Undiscovered artifact entry")[:100],
                    emoji=item.get("emoji", "❔") if discovered else "❔",
                )
            )

        super().__init__(
            placeholder="Inspect an artifact card",
            min_values=1,
            max_values=1,
            options=options,
            row=2,
        )

    async def callback(self, interaction: discord.Interaction):
        item_id = self.values[0]
        view = MuseumArtifactView(
            self.parent_view.owner_id,
            self.parent_view.is_admin,
            self.parent_view.collection_id,
            item_id,
            self.parent_view.page,
        )
        embed = view.build_embed(interaction.user)
        await interaction.response.edit_message(embed=embed, view=view)


class MuseumHomeView(discord.ui.View):
    def __init__(self, owner_id: int, is_admin: bool):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.is_admin = is_admin
        self.add_item(MuseumCollectionSelect(owner_id, is_admin))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This museum ledger isn't yours.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="🏠 Back to Profile", style=discord.ButtonStyle.primary, row=1)
    async def back_to_profile(self, interaction: discord.Interaction, button: discord.ui.Button):
        await show_profile(interaction, self.owner_id, self.is_admin)


class MuseumCollectionView(discord.ui.View):
    def __init__(self, owner_id: int, is_admin: bool, collection_id: str, page: int = 0):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.is_admin = is_admin
        self.collection_id = collection_id
        self.page = page
        self.discovered_item_ids: set[str] = set()
        self.add_item(MuseumArtifactSelect(self))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This collection isn't yours.", ephemeral=True)
            return False
        return True

    @property
    def total_pages(self) -> int:
        item_count = len(MUSEUM_COLLECTIONS[self.collection_id]["item_ids"])
        return max(1, math.ceil(item_count / 6))

    def current_page_item_ids(self) -> list[str]:
        item_ids = MUSEUM_COLLECTIONS[self.collection_id]["item_ids"]
        start = self.page * 6
        end = start + 6
        return item_ids[start:end]

    def build_embed(self, user: discord.abc.User | discord.Member) -> discord.Embed:
        self.discovered_item_ids = queries.get_discovered_item_ids(user.id)
        return museum_collection_embed(
            user.display_name,
            self.collection_id,
            self.discovered_item_ids,
            self.page,
            self.total_pages,
        )

    @discord.ui.button(label="⬅️ Back", style=discord.ButtonStyle.secondary, row=0)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
        self.clear_items()
        self.add_item(MuseumArtifactSelect(self))
        embed = self.build_embed(interaction.user)
        self._rebuild_buttons()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="➡️ Next", style=discord.ButtonStyle.secondary, row=0)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page < self.total_pages - 1:
            self.page += 1
        self.clear_items()
        self.add_item(MuseumArtifactSelect(self))
        embed = self.build_embed(interaction.user)
        self._rebuild_buttons()
        await interaction.response.edit_message(embed=embed, view=self)

    def _rebuild_buttons(self):
        # preserve nav/buttons after select refresh
        if not any(isinstance(child, discord.ui.Button) and child.label == "⬅️ Back" for child in self.children):
            pass  # buttons are class-defined and persist automatically

    @discord.ui.button(label="🏛️ Collections", style=discord.ButtonStyle.primary, row=1)
    async def back_to_museum_home(self, interaction: discord.Interaction, button: discord.ui.Button):
        await show_museum_home(interaction, self.owner_id, self.is_admin)

    @discord.ui.button(label="🏠 Profile", style=discord.ButtonStyle.secondary, row=1)
    async def back_to_profile(self, interaction: discord.Interaction, button: discord.ui.Button):
        await show_profile(interaction, self.owner_id, self.is_admin)
        

async def show_museum_home(interaction: discord.Interaction, owner_id: int, is_admin: bool) -> None:
    embed = build_museum_home_embed_for_user(interaction.user)
    view = MuseumHomeView(owner_id, is_admin)
    if interaction.response.is_done():
        await interaction.edit_original_response(embed=embed, view=view, attachments=[])
    else:
        await interaction.response.edit_message(embed=embed, view=view, attachments=[])

    )

class MuseumCollectionSelect(discord.ui.Select):
    def __init__(self, owner_id: int, is_admin: bool):
        self.owner_id = owner_id
        self.is_admin = is_admin
        options = [
            discord.SelectOption(
                label=collection["name"][:100],
                value=collection_id,
                description=collection["description"][:100],
                emoji=collection.get("emoji", "🏛️"),
            )
            for collection_id, collection in MUSEUM_COLLECTIONS.items()
        ]
        super().__init__(
            placeholder="Choose a museum collection",
            min_values=1,
            max_values=1,
            options=options,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction):
        collection_id = self.values[0]
        view = MuseumCollectionView(self.owner_id, self.is_admin, collection_id=collection_id, page=0)
        embed = view.build_embed(interaction.user)
        await interaction.response.edit_message(embed=embed, view=view)


class MuseumArtifactSelect(discord.ui.Select):
    def __init__(self, parent_view: "MuseumCollectionView"):
        self.parent_view = parent_view
        options: list[discord.SelectOption] = []

        for item_id in parent_view.current_page_item_ids():
            item = ITEMS.get(item_id, {"name": item_id, "emoji": "✨"})
            discovered = item_id in parent_view.discovered_item_ids
            options.append(
                discord.SelectOption(
                    label=(item["name"] if discovered else "Unknown Artifact")[:100],
                    value=item_id,
                    description=("View archived artifact card" if discovered else "Undiscovered artifact entry")[:100],
                    emoji=item.get("emoji", "❔") if discovered else "❔",
                )
            )

        super().__init__(
            placeholder="Inspect an artifact card",
            min_values=1,
            max_values=1,
            options=options,
            row=2,
        )

    async def callback(self, interaction: discord.Interaction):
        item_id = self.values[0]
        view = MuseumArtifactView(
            self.parent_view.owner_id,
            self.parent_view.is_admin,
            self.parent_view.collection_id,
            item_id,
            self.parent_view.page,
        )
        embed = view.build_embed(interaction.user)
        await interaction.response.edit_message(embed=embed, view=view)


class MuseumHomeView(discord.ui.View):
    def __init__(self, owner_id: int, is_admin: bool):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.is_admin = is_admin
        self.add_item(MuseumCollectionSelect(owner_id, is_admin))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This museum ledger isn't yours.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="🏠 Back to Profile", style=discord.ButtonStyle.primary, row=1)
    async def back_to_profile(self, interaction: discord.Interaction, button: discord.ui.Button):
        await show_profile(interaction, self.owner_id, self.is_admin)


class MuseumCollectionView(discord.ui.View):
    def __init__(self, owner_id: int, is_admin: bool, collection_id: str, page: int = 0):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.is_admin = is_admin
        self.collection_id = collection_id
        self.page = page
        self.discovered_item_ids: set[str] = set()
        self.add_item(MuseumArtifactSelect(self))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This collection isn't yours.", ephemeral=True)
            return False
        return True

    @property
    def total_pages(self) -> int:
        item_count = len(MUSEUM_COLLECTIONS[self.collection_id]["item_ids"])
        return max(1, math.ceil(item_count / 6))

    def current_page_item_ids(self) -> list[str]:
        item_ids = MUSEUM_COLLECTIONS[self.collection_id]["item_ids"]
        start = self.page * 6
        end = start + 6
        return item_ids[start:end]

    def build_embed(self, user: discord.abc.User | discord.Member) -> discord.Embed:
        self.discovered_item_ids = queries.get_discovered_item_ids(user.id)
        return museum_collection_embed(
            user.display_name,
            self.collection_id,
            self.discovered_item_ids,
            self.page,
            self.total_pages,
        )

    @discord.ui.button(label="⬅️ Back", style=discord.ButtonStyle.secondary, row=0)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
        self.clear_items()
        self.add_item(MuseumArtifactSelect(self))
        embed = self.build_embed(interaction.user)
        self._rebuild_buttons()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="➡️ Next", style=discord.ButtonStyle.secondary, row=0)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page < self.total_pages - 1:
            self.page += 1
        self.clear_items()
        self.add_item(MuseumArtifactSelect(self))
        embed = self.build_embed(interaction.user)
        self._rebuild_buttons()
        await interaction.response.edit_message(embed=embed, view=self)

    def _rebuild_buttons(self):
        # preserve nav/buttons after select refresh
        if not any(isinstance(child, discord.ui.Button) and child.label == "⬅️ Back" for child in self.children):
            pass  # buttons are class-defined and persist automatically

    @discord.ui.button(label="🏛️ Collections", style=discord.ButtonStyle.primary, row=1)
    async def back_to_museum_home(self, interaction: discord.Interaction, button: discord.ui.Button):
        await show_museum_home(interaction, self.owner_id, self.is_admin)

    @discord.ui.button(label="🏠 Profile", style=discord.ButtonStyle.secondary, row=1)
    async def back_to_profile(self, interaction: discord.Interaction, button: discord.ui.Button):
        await show_profile(interaction, self.owner_id, self.is_admin)

        )
        
    
async def show_profile(interaction: discord.Interaction, owner_id: int, is_admin: bool) -> None:
    embed = build_profile_embed_for_user(interaction.user)
    if interaction.response.is_done():
        await interaction.edit_original_response(embed=embed, view=ProfileView(owner_id, is_admin), attachments=[])
    else:
        await interaction.response.edit_message(embed=embed, view=ProfileView(owner_id, is_admin), attachments=[])
