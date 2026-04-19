from datetime import datetime
import discord

from game.data import ITEMS, ZONES, get_live_events, MUSEUM_COLLECTIONS, MUSEUM_ARTIFACT_TEXT
from game.leveling import xp_to_next_level


RARITY_COLORS = {
    "Common": 0x95A5A6,
    "Uncommon": 0x2ECC71,
    "Rare": 0x3498DB,
    "Epic": 0x9B59B6,
    "Legendary": 0xF1C40F,
    "Mythic": 0xE91E63,
}


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
    live_names = [f"{event.get('emoji', '✨')} {event['name']}" for event in get_live_events()]

    embed = discord.Embed(
        title=f"{player['username']} — {player['current_title']}",
        description=(
            f"📍 **{zone}**\n"
            f"🌐 {' • '.join(live_names) if live_names else 'No live world event'}"
        ),
        color=0x2C2F33,
        timestamp=datetime.utcnow(),
    )

    if avatar_url:
        embed.set_thumbnail(url=avatar_url)
        embed.set_author(name=player["username"], icon_url=avatar_url)

    embed.add_field(name="💰 Coins", value=str(player["coins"]), inline=True)
    embed.add_field(name="⭐ Level", value=str(player["level"]), inline=True)
    embed.add_field(name="🎒 Items", value=str(inventory_count), inline=True)
    embed.add_field(name="✨ XP", value=build_xp_bar(player["xp"], player["level"]), inline=False)
    embed.add_field(name="🗑️ Total Dives", value=str(player["total_dives"]), inline=True)
    embed.add_field(name="👑 Title", value=player["current_title"], inline=True)
    embed.add_field(name="🗺️ Zone", value=zone, inline=True)

    recent_text = "\n".join(recent_finds[-3:]) if recent_finds else "None yet"
    embed.add_field(name="🪄 Recent Finds", value=recent_text, inline=False)

    if active_effects:
        lines = []
        for effect in active_effects[:4]:
            if isinstance(effect, dict):
                label = effect.get("label", "Effect")
                expires = effect.get("expires_at", "soon")
                lines.append(f"⏳ {label} — {expires}")
            else:
                lines.append(str(effect))
        embed.add_field(name="⏳ Active Effects", value="\n".join(lines), inline=False)

    if equipment:
        lines = []
        for entry in equipment[:4]:
            if isinstance(entry, dict) and "item_id" in entry:
                item = ITEMS.get(entry["item_id"], {"name": entry["item_id"], "emoji": "✨"})
                lines.append(f"{item.get('emoji', '✨')} {item['name']}")
            else:
                lines.append(str(entry))
        embed.add_field(name="🧥 Equipped", value="\n".join(lines), inline=False)

    return embed


def dive_processing_embed(zone_name, text):
    return discord.Embed(
        title="🗑️ Diving...",
        description=f"**{zone_name}**\n\n{text}",
        color=0x5865F2,
    )


def dive_result_embed(
    player,
    item_id,
    leveled_up,
    reaction_text=None,
    event_text=None,
    bonus_text=None,
    unlocked_zone_names=None,
    avatar_url=None,
):
    item = ITEMS[item_id]
    rarity = item.get("rarity", "Common")

    lines = [
        f"{item.get('emoji', '✨')} **{item['name']}**",
        f"{rarity}",
    ]

    if item.get("flavor"):
        lines.append(f"*{item['flavor']}*")

    if event_text:
        lines.append(event_text)
    if bonus_text:
        lines.append(bonus_text)
    if reaction_text:
        lines.append(f"_{reaction_text}_")
    if leveled_up:
        lines.append(f"⬆️ You leveled up to **Level {player['level']}**!")
    if unlocked_zone_names:
        lines.append(f"🔓 New zones unlocked: **{', '.join(unlocked_zone_names)}**")

    embed = discord.Embed(
        title="✨ Loot Found!",
        description="\n\n".join(lines),
        color=RARITY_COLORS.get(rarity, 0x57F287),
    )

    if avatar_url:
        embed.set_author(name=player["username"], icon_url=avatar_url)

    if isinstance(item.get("image"), str) and item["image"].startswith("http"):
        embed.set_thumbnail(url=item["image"])

    embed.add_field(name="💰 Coins", value=str(player["coins"]), inline=True)
    embed.add_field(name="⭐ Level", value=str(player["level"]), inline=True)
    embed.add_field(name="🗑️ Total Dives", value=str(player["total_dives"]), inline=True)
    embed.add_field(name="✨ XP", value=build_xp_bar(player["xp"], player["level"]), inline=False)
    return embed


def inventory_embed(username: str, lines: list[str], page: int, total_pages: int) -> discord.Embed:
    embed = discord.Embed(
        title=f"🎒 {username}'s Loot Vault",
        description="\n\n".join(lines) if lines else "Your bag is empty.",
        color=0x5865F2,
    )
    embed.set_footer(text=f"Page {page + 1}/{total_pages}")
    return embed


def zone_embed(player, zone_id, unlocked_zone_ids, zone_loot_lines, index, total):
    zone = ZONES[zone_id]
    unlocked = zone_id in unlocked_zone_ids
    current = zone_id == player["current_zone_id"]
    status = "🟢 CURRENT" if current else ("✅ UNLOCKED" if unlocked else f"🔒 Unlocks at Level {zone['unlock_level']}")

    embed = discord.Embed(
        title=f"🗺️ Zone Selector ({index + 1}/{total})",
        description=f"**{zone['name']}**\n{status}\n\n*{zone['description']}*",
        color=0x57F287 if unlocked else 0xED4245,
    )
    embed.add_field(name="🎁 Possible Finds", value="\n".join(zone_loot_lines) if zone_loot_lines else "???", inline=False)
    return embed


def mix_lab_embed(inventory_map, mix_lines):
    return discord.Embed(
        title="🧪 Goblin Mix Lab",
        description="Available recipes right now:\n" + ("\n".join(mix_lines) if mix_lines else "None"),
        color=0x9B59B6,
    )


def mix_result_embed(title: str, result_text: str) -> discord.Embed:
    return discord.Embed(title=title, description=result_text, color=0x9B59B6)


def events_embed() -> discord.Embed:
    embed = discord.Embed(title="✨ World Events", description="The world is messier on purpose.", color=0xEB459E)
    live = get_live_events()
    if not live:
        embed.add_field(name="🌫️ Right Now", value="No special event is live.", inline=False)
    else:
        for event in live:
            embed.add_field(name=f"{event.get('emoji', '✨')} {event['name']}", value=event.get("description", ""), inline=False)
    return embed


def help_embed() -> discord.Embed:
    return discord.Embed(title="❓ How to Play", description="Dive, loot, mix, and survive the junk economy.", color=0xFAA61A)

def pawn_shop_embed(bundle_item_ids: list[str]) -> discord.Embed:
    from game.data import ITEMS

    if not bundle_item_ids:
        desc = "The pawn shop owner stares at you.\n\nYou have nothing worth trading."
    else:
        lines = []
        counts = {}
        for item_id in bundle_item_ids:
            counts[item_id] = counts.get(item_id, 0) + 1

        for item_id, qty in counts.items():
            item = ITEMS.get(item_id, {"name": item_id, "emoji": "✨"})
            lines.append(f"{item.get('emoji','✨')} **{item['name']}** x{qty}")

        desc = (
            "🏚️ *The pawn shop owner squints at your junk...*\n\n"
            "**Your Offer Pile:**\n"
            + "\n".join(lines)
            + "\n\nChoose your deal carefully..."
        )

    embed = discord.Embed(
        title="🏚️ Sketchy Pawn Shop",
        description=desc,
        color=0x8B5E3C,
    )
    return embed


def pawn_offer_result_embed(title: str, description: str) -> discord.Embed:
    return discord.Embed(
        title=title,
        description=description,
        color=0xD4AF37,
    )
