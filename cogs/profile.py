import discord
from discord import app_commands
from discord.ext import commands

from config import ADMIN_USER_IDS
from db import queries
from game.helpers import get_recent_finds_from_inventory_rows
from ui.embeds import profile_embed
from ui.views import ProfileView


class ProfileCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="profile", description="Open your main lobby")
    async def profile(self, interaction: discord.Interaction):
        queries.ensure_player(interaction.user.id, interaction.user.name)
        player = queries.get_player(interaction.user.id)
        inventory = queries.get_inventory(interaction.user.id)
        effects = queries.get_active_effects(interaction.user.id)
        equipment = queries.get_equipment(interaction.user.id)
        is_admin = interaction.user.id in ADMIN_USER_IDS

        await interaction.response.send_message(
            embed=profile_embed(
                player=player,
                inventory_count=sum(q for _, q in inventory),
                recent_finds=get_recent_finds_from_inventory_rows(inventory),
                active_effects=effects,
                equipment=equipment,
                avatar_url=interaction.user.display_avatar.url,
            ),
            view=ProfileView(interaction.user.id, is_admin),
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(ProfileCog(bot))
