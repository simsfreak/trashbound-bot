import os
import logging
import discord
from discord.ext import commands
from discord import app_commands

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")

if not TOKEN:
    raise RuntimeError("Missing DISCORD_TOKEN")

if not GUILD_ID:
    raise RuntimeError("Missing GUILD_ID")

TEST_GUILD = discord.Object(id=int(GUILD_ID))

intents = discord.Intents.default()


class TrashboundBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        synced = await self.tree.sync(guild=TEST_GUILD)
        logging.info(f"Synced {len(synced)} commands to guild")


bot = TrashboundBot()


@bot.event
async def on_ready():
    logging.info(f"Logged in as {bot.user}")


@bot.tree.command(name="ping", description="Check if the bot is alive", guild=TEST_GUILD)
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("pong 🗑️")


bot.run(TOKEN)
