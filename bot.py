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
        self.tree.clear_commands(guild=TEST_GUILD)
        self.tree.add_command(ping, guild=TEST_GUILD)
        synced = await self.tree.sync(guild=TEST_GUILD)
        logging.info(f"Synced {len(synced)} commands to guild")


bot = TrashboundBot()


@bot.event
async def on_ready():
    logging.info(f"Logged in as {bot.user}")


@app_commands.command(name="ping", description="Check if the bot is alive")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("pong 🗑️")


bot.run(TOKEN)
