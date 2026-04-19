import logging

import discord
from discord.ext import commands
from dotenv import load_dotenv

from config import DISCORD_TOKEN, GUILD_ID
from db.database import run_schema

load_dotenv()
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
        logging.info("Synced %s commands to guild", len(synced))

    async def on_ready(self):
        logging.info("Logged in as %s", self.user)


bot = TrashboundBot()
bot.run(DISCORD_TOKEN)
