import discord
from game.data import ITEMS, ZONES
from game.rarities import RARITY_COLORS
from game.leveling import xp_to_next_level


def profile_embed(player: dict) -> discord.Embed:
    current_zone = ZONES[player["current_zone_id"]]["name"]
    xp_needed = xp_to_next_level(player["level"])

    embed = discord.Embed(
        title=f"{player['username']} — {player['current_title']}",
        description="Your dumpster diving profile",
        color=0x2C2F33,
    )
    embed.add_field(name="💰 Coins", value=str(player["coins"]), inline=True)
    embed.add_field(name="⭐ Level", value=str(player["level"]), inline=True)
    embed.add_field(name="📍 Zone", value=current_zone, inline=True)
    embed.add_field(name="✨ XP", value=f"{player['xp']} / {xp_needed}", inline=False)
    embed.add_field(name="🗑️ Total Dives", value=str(player["total_dives"]), inline=False)
    return embed


def dive_result_embed(player: dict, item_id: str, leveled_up: bool) -> discord.Embed:
    item = ITEMS[item_id]
    zone_name = ZONES[player["current_zone_id"]]["name"]
    rarity = item["rarity"]

    desc = (
        f"🗑️ You searched **{zone_name}**.\n\n"
        f"✨ You found **{item['name']}**\n"
        f"🎖️ Rarity: **{rarity}**\n"
        f"💰 +{item['coins']} coins\n"
        f"⭐ +{item['xp']} XP"
    )

    if leveled_up:
        desc += f"\n\n⬆️ You leveled up to **Level {player['level']}**!"

    embed = discord.Embed(
        title="Dumpster Dive Result",
        description=desc,
        color=RARITY_COLORS.get(rarity, 0xFFFFFF),
    )
    return embed
