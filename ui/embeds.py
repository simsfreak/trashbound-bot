import discord
from game.data import ITEMS, ZONES
from game.rarities import RARITY_COLORS
from game.leveling import xp_to_next_level


RARITY_LABELS = {
    "Common": "⚪ Common find",
    "Uncommon": "🟢 Uncommon find",
    "Rare": "🔵 Rare find",
    "Epic": "🟣 Epic find",
    "Legendary": "🟡 Legendary find",
    "Mythic": "💖 Mythic find",
}


def build_xp_bar(current_xp: int, level: int, size: int = 8) -> str:
    needed = xp_to_next_level(level)
    if needed <= 0:
        return "🟩" * size

    filled = round((current_xp / needed) * size)
    filled = max(0, min(size, filled))
    empty = size - filled
    return f"{'🟩' * filled}{'⬜' * empty} {current_xp}/{needed}"


def profile_embed(player: dict, inventory_count: int = 0, recent_finds: list[str] | None = None) -> discord.Embed:
    current_zone = ZONES[player["current_zone_id"]]["name"]
    recent_finds = recent_finds or []

    recent_text = "\n".join(f"• {item}" for item in recent_finds[-3:]) if recent_finds else "• Nothing yet"
    xp_bar = build_xp_bar(player["xp"], player["level"])

    embed = discord.Embed(
        title=f"{player['username']} — {player['current_title']} ✨",
        description=(
            f"Back on the grind, little trash legend.\n"
            f"Currently scavenging in **{current_zone}**."
        ),
        color=0x2C2F33,
    )

    embed.add_field(name="💰 Coins", value=str(player["coins"]), inline=True)
    embed.add_field(name="⭐ Level", value=str(player["level"]), inline=True)
    embed.add_field(name="📍 Zone", value=current_zone, inline=True)

    embed.add_field(name="✨ XP Progress", value=xp_bar, inline=False)

    embed.add_field(name="🗑️ Total Dives", value=str(player["total_dives"]), inline=True)
    embed.add_field(name="🎒 Inventory", value=str(inventory_count), inline=True)
    embed.add_field(name="🏷️ Title", value=player["current_title"], inline=True)

    embed.add_field(name="Recent Finds", value=recent_text, inline=False)
    embed.set_footer(text="Tiny trash empire in progress.")
    return embed


def dive_result_embed(player: dict, item_id: str, leveled_up: bool, reaction_text: str | None = None) -> discord.Embed:
    item = ITEMS[item_id]
    zone = ZONES[player["current_zone_id"]]
    zone_name = zone["name"]
    rarity = item["rarity"]
    item_emoji = item.get("emoji", "✨")
    flavor = item.get("flavor", "A strange little treasure.")
    rarity_label = RARITY_LABELS.get(rarity, rarity)

    desc = (
        f"🗑️ You searched **{zone_name}**.\n\n"
        f"{item_emoji} You found **{item['name']}**\n"
        f"{rarity_label}\n"
        f"💰 +{item['coins']} coins\n"
        f"⭐ +{item['xp']} XP\n\n"
        f"*{flavor}*"
    )

    if reaction_text:
        desc += f"\n\n_{reaction_text}_"

    if leveled_up:
        desc += f"\n\n⬆️ You leveled up to **Level {player['level']}**!"

    embed = discord.Embed(
        title="Dumpster Dive Result",
        description=desc,
        color=RARITY_COLORS.get(rarity, 0xFFFFFF),
    )

    if item.get("image", "").startswith("http"):
        embed.set_thumbnail(url=item["image"])

    embed.add_field(name="💰 Coins", value=str(player["coins"]), inline=True)
    embed.add_field(name="⭐ Level", value=str(player["level"]), inline=True)
    embed.add_field(name="📍 Zone", value=zone_name, inline=True)
    embed.add_field(name="✨ XP Progress", value=build_xp_bar(player["xp"], player["level"]), inline=False)

    return embed


def inventory_embed(username: str, lines: list[str], page: int, total_pages: int) -> discord.Embed:
    embed = discord.Embed(
        title=f"🎒 {username}'s Loot",
        description="\n\n".join(lines) if lines else "Your bag is empty. Time to dig up something cute.",
        color=0x5865F2,
    )
    embed.set_footer(text=f"Page {page + 1} / {total_pages}")
    return embed


def zones_embed(player: dict, zone_lines: list[str]) -> discord.Embed:
    embed = discord.Embed(
        title="🗺️ Dumpster Zones",
        description="\n\n".join(zone_lines) if zone_lines else "No zones found.",
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
