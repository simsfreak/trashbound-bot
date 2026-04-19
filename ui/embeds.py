from datetime import datetime
import discord

from game.data import ITEMS, ZONES, get_live_events
from game.leveling import xp_to_next_level


def build_xp_bar(current_xp: int, level: int, size: int = 8) -> str:
    needed = xp_to_next_level(level)
    if needed <= 0:
        return "🟩" * size

    filled = round((current_xp / needed) * size)
    filled = max(0, min(size, filled))
    empty = size - filled
    return f"{'🟩' * filled}{'⬜' * empty} {current_xp}/{needed}"


def profile_embed(
    player,
    inventory_count,
    recent_finds,
    active_effects,
    equipment,
    avatar_url,
):
    zone = ZONES[player["current_zone_id"]]["name"]

    embed = discord.Embed(
        title=f"{player['username']} — {player['current_title']}",
        description=f"📍 {zone}",
        color=0x2C2F33,
        timestamp=datetime.utcnow(),
    )

    embed.set_thumbnail(url=avatar_url)

    embed.add_field(name="💰 Coins", value=str(player["coins"]))
    embed.add_field(name="⭐ Level", value=str(player["level"]))
    embed.add_field(name="🎒 Items", value=str(inventory_count))

    embed.add_field(
        name="XP",
        value=build_xp_bar(player["xp"], player["level"]),
        inline=False,
    )

    embed.add_field(
        name="Recent Finds",
        value="\n".join(recent_finds[-3:]) if recent_finds else "None",
        inline=False,
    )

    return embed


def dive_processing_embed(zone_name, text):
    return discord.Embed(
        title="🗑️ Diving...",
        description=f"{zone_name}\n\n{text}",
        color=0x5865F2,
    )


def dive_result_embed(player, item_id, leveled_up, avatar_url=None):
    item = ITEMS[item_id]

    embed = discord.Embed(
        title="✨ Loot Found!",
        description=f"{item['emoji']} **{item['name']}**\n{item['rarity']}",
        color=0x57F287,
    )

    if avatar_url:
        embed.set_author(name=player["username"], icon_url=avatar_url)

    embed.add_field(name="💰 Coins", value=str(player["coins"]))
    embed.add_field(name="⭐ Level", value=str(player["level"]))

    return embed
