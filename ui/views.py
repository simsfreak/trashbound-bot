import asyncio
import math
import random

import discord

from db import queries
from game.data import ITEMS, MIX_RECIPES, ZONES, get_live_events
from game.helpers import (
    can_mix_inventory,
    determine_title,
    find_available_recipe,
    get_effect_remaining_text,
    get_item_card_line,
    get_random_dive_midpoint,
    get_random_dive_reaction,
    get_random_dive_starter,
    get_recent_finds_from_inventory_rows,
    maybe_roll_dive_event,
    perform_chaos_mix,
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
    profile_embed,
    zone_embed,
)
from ui.modals import ContactAdminModal


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
            await interaction.response.send_message(
                f"{get_item_card_line(item_id)}",
                ephemeral=True,
            )


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

    @discord.ui.button(label="🛠️ Fixed Recipe", style=discord.ButtonStyle.success, row=0)
    async def fixed_recipe(self, interaction: discord.Interaction, button: discord.ui.Button):
        inventory_map = queries.get_inventory_map(interaction.user.id)
        recipe = find_available_recipe(inventory_map)
        if recipe is None:
            embed = mix_result_embed("🧪 Mix Failed", "No fixed recipe is ready yet. Keep collecting ingredients.")
            await interaction.response.edit_message(embed=embed, view=self)
            return

        for item_id, qty in recipe["ingredients"].items():
            queries.remove_item_from_inventory(interaction.user.id, item_id, qty)
        queries.add_item_to_inventory(interaction.user.id, recipe["result_item_id"], recipe["result_qty"])
        result_item = ITEMS[recipe["result_item_id"]]
        embed = mix_result_embed(
            "🛠️ Recipe Complete",
            f"You forged:\n\n{result_item['emoji']} **{result_item['name']}** x{recipe['result_qty']}\n"
            f"{result_item['rarity']} • {result_item.get('kind', 'item').title()}\n"
            f"*{result_item.get('flavor', '')}*",
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🎲 Chaos Mix", style=discord.ButtonStyle.primary, row=0)
    async def chaos_mix(self, interaction: discord.Interaction, button: discord.ui.Button):
        inventory_rows = queries.get_inventory(interaction.user.id)
        if not can_mix_inventory(inventory_rows):
            embed = mix_result_embed("🎲 Chaos Mix", "You need at least **2 Common items** to chaos-mix something cursed.")
            await interaction.response.edit_message(embed=embed, view=self)
            return

        common_consumed = 0
        for item_id, qty in inventory_rows:
            if common_consumed >= 2:
                break
            if ITEMS.get(item_id, {}).get("rarity") == "Common":
                consume = min(qty, 2 - common_consumed)
                queries.remove_item_from_inventory(interaction.user.id, item_id, consume)
                common_consumed += consume

        rare_bonus = 4 if any(event["key"] == "unstable_mix" for event in get_live_events()) else 0
        result = perform_chaos_mix(inventory_rows, extra_rare_bonus=rare_bonus)
        if result is None:
            embed = mix_result_embed("🎲 Chaos Mix", "The lab ate your hopes and gave nothing back.")
            await interaction.response.edit_message(embed=embed, view=self)
            return
        result_item_id, qty = result
        queries.add_item_to_inventory(interaction.user.id, result_item_id, qty)
        item = ITEMS[result_item_id]
        embed = mix_result_embed(
            "🎲 Chaos Mix Result",
            f"The bench sparks, screams, then spits out:\n\n"
            f"{item['emoji']} **{item['name']}** x{qty}\n"
            f"{item['rarity']} • {item.get('kind', 'item').title()}\n"
            f"*{item.get('flavor', '')}*",
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
        embed = mix_result_embed(
            "🧃 Potion Brewed",
            f"{item['emoji']} **{item['name']}** x1\n{item['rarity']} • Consumable\n*{item['use_text']}*",
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="⚠️ Overcharge", style=discord.ButtonStyle.danger, row=1)
    async def overcharge(self, interaction: discord.Interaction, button: discord.ui.Button):
        inventory_rows = queries.get_inventory(interaction.user.id)
        common_ids = [item_id for item_id, qty in inventory_rows for _ in range(qty) if ITEMS.get(item_id, {}).get("rarity") == "Common"]
        if len(common_ids) < 4:
            embed = mix_result_embed("⚠️ Overcharge", "Need at least **4 Common items** to overcharge the lab.")
            await interaction.response.edit_message(embed=embed, view=self)
            return
        consumed = 0
        for item_id, qty in inventory_rows:
            if consumed >= 4:
                break
            if ITEMS.get(item_id, {}).get("rarity") == "Common":
                take = min(qty, 4 - consumed)
                queries.remove_item_from_inventory(interaction.user.id, item_id, take)
                consumed += take
        result_item_id = random.choice(["golden_potion", "glitch_charm", "rat_king_sigil"])
        queries.add_item_to_inventory(interaction.user.id, result_item_id, 1)
        item = ITEMS[result_item_id]
        embed = mix_result_embed(
            "⚠️ Overcharge Success",
            f"The bench almost exploded. Worth it.\n\n{item['emoji']} **{item['name']}** x1\n{item['rarity']} • {item.get('kind', 'item').title()}",
        )
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

    @discord.ui.button(label="🧪 Mix", style=discord.ButtonStyle.success, row=0)
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

    @discord.ui.button(label="❓ Help", style=discord.ButtonStyle.secondary, row=1)
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
            description="Admin tools are coming next:\n• View messages\n• Grant XP\n• Grant coins\n• Trigger events",
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
        await interaction.edit_original_response(embed=dive_processing_embed(zone_name, get_random_dive_starter()), view=None)
    else:
        await interaction.response.edit_message(embed=dive_processing_embed(zone_name, get_random_dive_starter()), view=None)

    await asyncio.sleep(1.0)
    await interaction.edit_original_response(embed=dive_processing_embed(zone_name, get_random_dive_midpoint()), view=None)
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

    original_item = ITEMS[item_id]
    temporary_item = dict(original_item)
    temporary_item["coins"] = gained_coins
    temporary_item["xp"] = gained_xp
    ITEMS[item_id] = temporary_item

    try:
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
    finally:
        ITEMS[item_id] = original_item

        image_path = ITEMS[item_id].get("image")

    if image_path and not image_path.startswith("http"):
        file = discord.File(image_path, filename="item.png")
        embed.set_thumbnail(url="attachment://item.png")

        await interaction.edit_original_response(
            embed=embed,
            attachments=[file],
            view=DiveResultView(owner_id, is_admin),
        )
    else:
        await interaction.edit_original_response(
            embed=embed,
            view=DiveResultView(owner_id, is_admin),
        )


def _split_live_events() -> tuple[str | None, str | None]:
    weekend_event = None
    seasonal_event = None
    for event in get_live_events():
        if event.get("type") == "weekend" and weekend_event is None:
            weekend_event = f"{event.get('emoji', '')} {event.get('name', 'Weekend Event')}".strip()
        elif event.get("type") == "seasonal" and seasonal_event is None:
            seasonal_event = f"{event.get('emoji', '')} {event.get('name', 'Seasonal Event')}".strip()
    return weekend_event, seasonal_event


def _format_active_effect_lines(active_effects: list[dict]) -> list[str]:
    lines: list[str] = []
    for effect in active_effects[:4]:
        lines.append(f"{effect['label']} — {get_effect_remaining_text(effect['expires_at'])}")
    return lines


def _format_equipped_lines(equipment: list[dict]) -> list[str]:
    lines: list[str] = []
    for entry in equipment[:4]:
        item = ITEMS.get(entry["item_id"], {"name": entry["item_id"], "emoji": "✨", "equip_bonus": ""})
        bonus = item.get("equip_bonus", "No passive listed")
        lines.append(f"{item.get('emoji', '✨')} {item['name']} — {bonus}")
    return lines


def build_profile_embed_for_user(user: discord.abc.User | discord.Member) -> discord.Embed:
    player = queries.get_player(user.id)
    inventory = queries.get_inventory(user.id)
    recent_finds = get_recent_finds_from_inventory_rows(inventory)
    active_effects = queries.get_active_effects(user.id)
    equipment = queries.get_equipment(user.id)
    weekend_event, seasonal_event = _split_live_events()

    try:
        return profile_embed(
            player=player,
            inventory_count=sum(q for _, q in inventory),
            recent_finds=recent_finds,
            active_effects=_format_active_effect_lines(active_effects),
            equipped_lines=_format_equipped_lines(equipment),
            weekend_event=weekend_event,
            seasonal_event=seasonal_event,
            avatar_url=user.display_avatar.url,
        )
    except TypeError:
        return profile_embed(
            player=player,
            inventory_count=sum(q for _, q in inventory),
            recent_finds=recent_finds,
            active_effects=active_effects,
            equipment=equipment,
            avatar_url=user.display_avatar.url,
        )


async def show_profile(interaction: discord.Interaction, owner_id: int, is_admin: bool) -> None:
    embed = build_profile_embed_for_user(interaction.user)
    if interaction.response.is_done():
        await interaction.edit_original_response(embed=embed, view=ProfileView(owner_id, is_admin))
    else:
        await interaction.response.edit_message(embed=embed, view=ProfileView(owner_id, is_admin))
