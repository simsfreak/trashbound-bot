import discord
from game.data import ITEMS, ZONES
from game.rarities import RARITY_COLORS
from game.leveling import xp_to_next_level


def profile_embed(player: dict) -> discord.Embed:
    current_zone = ZONES[player["current_zone_id"]]["name"]
    xp_needed = xp_to_next_level(player["level"])

    embed = discord.Embed(
        title=f"{player['username']} — {player['current_title']}",
        description=(
            f"Welcome back to the grind.\n"
            f"Current zone: **{current_zone}**"
        ),
        color=0x2C2F33,
    )

    embed.add_field(name="💰 Coins", value=str(player["coins"]), inline=True)
    embed.add_field(name="⭐ Level", value=str(player["level"]), inline=True)
    embed.add_field(name="✨ XP", value=f"{player['xp']} / {xp_needed}", inline=True)

    embed.add_field(name="\u200b", value="\u200b", inline=False)

    embed.add_field(name="🗑️ Total Dives", value=str(player["total_dives"]), inline=True)
    embed.add_field(name="🎒 Inventory", value=str(player.get("inventory_count", 0)), inline=True)
    embed.add_field(name="📍 Zone", value=current_zone, inline=True)

    recent_finds = player.get("recent_finds", [])
    recent_text = "\n".join(f"• {item}" for item in recent_finds[-3:]) if recent_finds else "• Nothing yet"

    embed.add_field(name="\u200b", value="\u200b", inline=False)
    embed.add_field(name="Recent Finds", value=recent_text, inline=False)

    return embed
