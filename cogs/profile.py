import discord
from discord.ext import commands
from discord import app_commands

from db import queries
from config import ADMIN_USER_IDS
from ui.views import ProfileView, build_profile_embed_for_user


class ProfileCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="profile", description="Open your main lobby")
    async def profile(self, interaction: discord.Interaction):
        await interaction.response.defer()
        queries.ensure_player(interaction.user.id, interaction.user.name)
        is_admin = interaction.user.id in ADMIN_USER_IDS
        embed = build_profile_embed_for_user(interaction.user)
        await interaction.followup.send(embed=embed, view=ProfileView(interaction.user.id, is_admin))


async def setup(bot: commands.Bot):
    await bot.add_cog(ProfileCog(bot))
