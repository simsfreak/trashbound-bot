import discord
from db import queries
from game.helpers import roll_item_for_zone
from game.leveling import apply_xp
from ui.embeds import profile_embed, dive_result_embed
from ui.modals import ContactAdminModal

def determine_title(level: int) -> str:
    if level >= 20:
        return "Garbage Royalty"
    if level >= 12:
        return "Dumpster Hunter"
    if level >= 6:
        return "Scrap Seeker"
    return "Trash Rookie"


class ProfileView(discord.ui.View):
    def __init__(self, owner_id: int, is_admin: bool):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.is_admin = is_admin

        if is_admin:
            self.add_item(AdminButton())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This menu isn't yours. Open your own with /profile.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Dive", emoji="🗑️", style=discord.ButtonStyle.primary)
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

    @discord.ui.button(label="Inventory", emoji="🎒", style=discord.ButtonStyle.secondary)
    async def inventory_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        inventory = queries.get_inventory(interaction.user.id)
        lines = [f"• {item_id} x{qty}" for item_id, qty in inventory] or ["Your inventory is empty."]
        embed = discord.Embed(title="🎒 Inventory", description="\n".join(lines[:10]), color=0x5865F2)
        await interaction.response.edit_message(embed=embed, view=ProfileView(self.owner_id, self.is_admin))

    @discord.ui.button(label="Zones", emoji="🗺️", style=discord.ButtonStyle.secondary)
    async def zones_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        from game.data import ZONES
        unlocked = set(queries.get_unlocked_zone_ids(interaction.user.id))
        player = queries.get_player(interaction.user.id)

        lines = []
        for zone_id, zone in ZONES.items():
            marker = "✅" if zone_id in unlocked else "🔒"
            current = " (Current)" if zone_id == player["current_zone_id"] else ""
            lines.append(f"{marker} **{zone['name']}** — unlocks at level {zone['unlock_level']}{current}")

        embed = discord.Embed(title="🗺️ Zones", description="\n".join(lines), color=0x57F287)
        await interaction.response.edit_message(embed=embed, view=ProfileView(self.owner_id, self.is_admin))

    @discord.ui.button(label="Events", emoji="🎉", style=discord.ButtonStyle.secondary)
    async def events_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🎉 Events",
            description="No live events yet.\nSoon this page will show active event progress and rewards.",
            color=0xEB459E,
        )
        await interaction.response.edit_message(embed=embed, view=ProfileView(self.owner_id, self.is_admin))

    @discord.ui.button(label="Instructions", emoji="📖", style=discord.ButtonStyle.secondary)
    async def instructions_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="📖 How to Play",
            description=(
                "• Use **Dive** to search your current zone.\n"
                "• Gain **coins** and **XP** from items.\n"
                "• Level up to unlock **new zones**.\n"
                "• Open **Inventory** to view your loot.\n"
                "• Check **Events** for special content."
            ),
            color=0xFAA61A,
        )
        await interaction.response.edit_message(embed=embed, view=ProfileView(self.owner_id, self.is_admin))

    @discord.ui.button(label="Contact Admin", emoji="📨", style=discord.ButtonStyle.secondary)
    async def contact_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ContactAdminModal())

    @discord.ui.button(label="Refresh", emoji="🔄", style=discord.ButtonStyle.secondary)
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = queries.get_player(interaction.user.id)
        await interaction.response.edit_message(
            embed=profile_embed(player),
            view=ProfileView(self.owner_id, self.is_admin),
        )


class AdminButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Admin", emoji="🛠️", style=discord.ButtonStyle.danger)

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🛠️ Admin Panel",
            description="Admin tools are coming next:\n• View messages\n• Grant XP\n• Grant coins\n• Trigger events",
            color=0xED4245,
        )
        await interaction.response.edit_message(embed=embed, view=self.view)
