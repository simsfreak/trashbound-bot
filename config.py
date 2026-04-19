import os

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")
DATABASE_URL = os.getenv("DATABASE_URL")

ADMIN_USER_IDS = {
    1495265519891255538,
}

if not DISCORD_TOKEN:
    raise RuntimeError("Missing DISCORD_TOKEN")

if not GUILD_ID:
    raise RuntimeError("Missing GUILD_ID")

if not DATABASE_URL:
    raise RuntimeError("Missing DATABASE_URL")
