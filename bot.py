import logging
import discord
from discord.ext import commands

from config import DISCORD_TOKEN, GUILD_ID
from db.database import run_schema

logging.basicConfig(level=logging.INFO)

TEST_GUILD = discord.Object(id=int(GUILD_ID))
intents = discord.Intents.default()

INITIAL_EXTENSIONS = [
    "cogs.profile",
]

class TrashboundBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        run_schema()

        for ext in INITIAL_EXTENSIONS:
            await self.load_extension(ext)

        self.tree.copy_global_to(guild=TEST_GUILD)
        synced = await self.tree.sync(guild=TEST_GUILD)
        logging.info(f"Synced {len(synced)} commands to guild")

    async def on_ready(self):
        logging.info(f"Logged in as {self.user}")

bot = TrashboundBot()
bot.run(DISCORD_TOKEN)
