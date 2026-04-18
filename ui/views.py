import math
import discord

from db import queries
from game.data import ZONES, ITEMS
from game.helpers import roll_item_for_zone, get_recent_finds_from_inventory_rows, can_mix_inventory, perform_mix
from game.leveling import apply_xp
from ui.embeds import (
    profile_embed,
    dive_result_embed,
    inventory_embed,
    zones_embed,
    mix_result_embed,
)
from ui.modals import ContactAdminModal


def determine_title(level: int) -> str:
    if level >= 20:
        return "Garbage Royalty"
    if level >= 12:
        return "Dumpster Hunter"
    if level >= 6:
        return "Scrap Seeker"
    return "Trash Rookie"


class InventoryView(discord.ui.View):
    def __init__(self, owner_id: int, is_admin: bool, items: list[tuple[str, int]], page: int = 0, page_size: int = 6):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.is_admin = is_admin
        self.items = items
        self.page = page
        self.page_size = page_size

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This inventory isn't yours.", ephemeral=True)
            return False
        return True

    def page_lines(self) -> list[str]:
        start = self.page * self.page_size
        end = start + self.page_size
        page_items = self.items[start:end]

        lines = []
        for item_id, qty in page_items:
            item = ITEMS.get(item_id, {"name": item_id, "rarity": "Unknown", "coins": 0})
            lines.append(
                f"**{item['name']}**\n"
                f"Rarity: {item['rarity']} • Qty: {qty} • Sell: {item['coins']}"
            )
        return lines

    @property
    def total_pages(self) -> int:
        return max(1, math.ceil(len(self.items) / self.page_size))

    @discord.ui.button(label="◀ Back", style=discord.ButtonStyle.secondary, row=0)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
        embed = inventory_embed(interaction.user.display_name, self.page_lines(), self.page, self.total_pages)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="▶ Next", style=discord.ButtonStyle.secondary, row=0)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page < self.total_pages - 1:
            self.page += 1
        embed = inventory_embed(interaction.user.display_name, self.page_lines(), self.page, self.total_pages)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🏠 Back to Profile", style=discord.ButtonStyle.primary, row=1)
    async def back_to_profile(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = queries.get_player(interaction.user.id)
        inventory = queries.get_inventory(interaction.user.id)
        recent_finds = get_recent_finds_from_inventory_rows(inventory)
        embed = profile_embed(player, inventory_count=sum(q for _, q in inventory), recent_finds=recent_finds)
        await interaction.response.edit_message(
            embed=embed,
            view=ProfileView(self.owner_id, self.is_admin)
        )


class ProfileView(discord.ui.View):
    def __init__(self, owner_id: int, is_admin: bool):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.is_admin = is_admin

        if is_admin:
            self.add_item(AdminButton(row=2))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This menu isn't yours. Open your own with /profile.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Dive", emoji="🗑️", style=discord.ButtonStyle.primary, row=0)
    async def dive_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = queries.get_player(interaction.user.id)
        item_id, item = roll_item_for_zone(player["current_zone_id"])

        new_xp, new_level, leveled_up = apply_xp(player["xp"], player["level"], item["xp"])
        new_title = determine_title(new_level)
        new_coins = player["coins"] + item["coins"]
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
        queries.unlock_zones_for_level(interaction.user.id, new_level)

        updated_player = queries.get_player(interaction.user.id)
        embed = dive_result_embed(updated_player, item_id, leveled_up)

        await interaction.response.edit_message(
            embed=embed,
            view=ProfileView(self.owner_id, self.is_admin)
        )

    @discord.ui.button(label="Inventory", emoji="🎒", style=discord.ButtonStyle.secondary, row=0)
    async def inventory_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        inventory = queries.get_inventory(interaction.user.id)
        view = InventoryView(self.owner_id, self.is_admin, inventory, page=0)
        embed = inventory_embed(interaction.user.display_name, view.page_lines(), view.page, view.total_pages)
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="Mix", emoji="🧪", style=discord.ButtonStyle.success, row=0)
    async def mix_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        inventory = queries.get_inventory(interaction.user.id)

        if not can_mix_inventory(inventory):
            embed = mix_result_embed("You need at least **2 Common items** to mix something together.")
            await interaction.response.edit_message(embed=embed, view=ProfileView(self.owner_id, self.is_admin))
            return

        result = perform_mix(inventory)
        if result is None:
            embed = mix_result_embed("Mixing failed. Try collecting more junk.")
            await interaction.response.edit_message(embed=embed, view=ProfileView(self.owner_id, self.is_admin))
            return

        result_item_id, qty = result
        queries.add_item_to_inventory(interaction.user.id, result_item_id, qty)

        item = ITEMS[result_item_id]
        embed = mix_result_embed(
            f"You mashed together some junk and created:\n\n"
            f"✨ **{item['name']}** x{qty}\n"
            f"🎖️ Rarity: **{item['rarity']}**"
        )
        await interaction.response.edit_message(embed=embed, view=ProfileView(self.owner_id, self.is_admin))

    @discord.ui.button(label="Zones", emoji="🗺️", style=discord.ButtonStyle.success, row=1)
    async def zones_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        unlocked = set(queries.get_unlocked_zone_ids(interaction.user.id))
        player = queries.get_player(interaction.user.id)

        lines = []
        for zone_id, zone in ZONES.items():
            marker = "✅" if zone_id in unlocked else "🔒"
            current = " (Current)" if zone_id == player["current_zone_id"] else ""
            lines.append(f"{marker} **{zone['name']}** — unlock level {zone['unlock_level']}{current}")

        embed = zones_embed(player, lines)
        await interaction.response.edit_message(embed=embed, view=ProfileView(self.owner_id, self.is_admin))

    @discord.ui.button(label="Events", emoji="🎉", style=discord.ButtonStyle.danger, row=1)
    async def events_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🎉 Events",
            description="No live events yet.\nSoon this page will show active event progress and rewards.",
            color=0xEB459E,
        )
        await interaction.response.edit_message(embed=embed, view=ProfileView(self.owner_id, self.is_admin))

    @discord.ui.button(label="Instructions", emoji="📖", style=discord.ButtonStyle.secondary, row=1)
    async def instructions_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="📖 How to Play",
            description=(
                "• Use **Dive** to search your current zone.\n"
                "• Gain **coins** and **XP** from items.\n"
                "• Level up to unlock **new zones**.\n"
                "• Open **Inventory** to view your loot.\n"
                "• Use **Mix** to combine common junk.\n"
                "• Check **Events** for special content."
            ),
            color=0xFAA61A,
        )
        await interaction.response.edit_message(embed=embed, view=ProfileView(self.owner_id, self.is_admin))

    @discord.ui.button(label="Contact Admin", emoji="📨", style=discord.ButtonStyle.secondary, row=2)
    async def contact_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ContactAdminModal())

    @discord.ui.button(label="Refresh", emoji="🔄", style=discord.ButtonStyle.secondary, row=2)
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = queries.get_player(interaction.user.id)
        inventory = queries.get_inventory(interaction.user.id)
        recent_finds = get_recent_finds_from_inventory_rows(inventory)
        embed = profile_embed(
            player,
            inventory_count=sum(q for _, q in inventory),
            recent_finds=recent_finds,
        )
        await interaction.response.edit_message(
            embed=embed,
            view=ProfileView(self.owner_id, self.is_admin),
        )


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
