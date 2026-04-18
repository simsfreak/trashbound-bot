import discord
from game.data import ITEMS, ZONES
from game.rarities import RARITY_COLORS
from game.leveling import xp_to_next_level


def profile_embed(player: dict, inventory_count: int = 0, recent_finds: list[str] | None = None) -> discord.Embed:
    current_zone = ZONES[player["current_zone_id"]]["name"]
    xp_needed = xp_to_next_level(player["level"])
    recent_finds = recent_finds or []

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
    embed.add_field(name="🎒 Inventory", value=str(inventory_count), inline=True)
    embed.add_field(name="📍 Zone", value=current_zone, inline=True)

    recent_text = "\n".join(f"• {item}" for item in recent_finds[-3:]) if recent_finds else "• Nothing yet"

    embed.add_field(name="\u200b", value="\u200b", inline=False)
    embed.add_field(name="Recent Finds", value=recent_text, inline=False)

    return embed


def dive_result_embed(player: dict, item_id: str, leveled_up: bool) -> discord.Embed:
    item = ITEMS[item_id]
    zone_name = ZONES[player["current_zone_id"]]["name"]
    rarity = item["rarity"]

    desc = (
        f"🗑️ You searched **{zone_name}**.\n"
        f"\n"
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

    embed.add_field(name="\u200b", value="\u200b", inline=False)
    embed.add_field(name="💰 Coins", value=str(player["coins"]), inline=True)
    embed.add_field(name="⭐ Level", value=str(player["level"]), inline=True)
    embed.add_field(name="📍 Zone", value=zone_name, inline=True)

    return embed


def inventory_embed(username: str, lines: list[str], page: int, total_pages: int) -> discord.Embed:
    embed = discord.Embed(
        title=f"🎒 {username}'s Inventory",
        description="\n".join(lines) if lines else "Your inventory is empty.",
        color=0x5865F2,
    )
    embed.set_footer(text=f"Page {page + 1} / {total_pages}")
    return embed


def zones_embed(player: dict, zone_lines: list[str]) -> discord.Embed:
    embed = discord.Embed(
        title="🗺️ Dumpster Zones",
        description="\n".join(zone_lines) if zone_lines else "No zones found.",
        color=0x57F287,
    )
    embed.set_footer(text=f"Current zone: {ZONES[player['current_zone_id']]['name']}")
    return embed


def mix_result_embed(result_text: str) -> discord.Embed:
    return discord.Embed(
        title="🧪 Mixing Bench",
        description=result_text,
        color=0x9B59B6,
    )
