from datetime import datetime
import discord

from game.data import EQUIP_SLOTS, ITEMS, ZONES, get_live_events, MUSEUM_COLLECTIONS, MUSEUM_ARTIFACT_TEXT
from game.leveling import xp_to_next_level
from game.helpers import calculate_equipment_bonuses


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
    dirty_tickets,
    quest_status,
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
    embed.add_field(name="🎟 Dirty Tickets", value=str(dirty_tickets), inline=True)
    embed.add_field(name="⭐ Level", value=str(player["level"]), inline=True)
    embed.add_field(name="🎒 Items", value=str(inventory_count), inline=True)
    embed.add_field(name="✨ XP", value=build_xp_bar(player["xp"], player["level"]), inline=False)

    bonuses = calculate_equipment_bonuses(equipment)
    bonus_lines = []
    if bonuses["xp_boost"] > 0:
        bonus_lines.append(f"✨ +{int(bonuses['xp_boost'] * 100)}% XP Gain")
    if bonuses["coin_boost"] > 0:
        bonus_lines.append(f"💰 +{int(bonuses['coin_boost'] * 100)}% Coin Gain")
    if bonuses["loot_value"] > 0:
        bonus_lines.append(f"💎 +{int(bonuses['loot_value'] * 100)}% Item Value")
    if bonuses["drop_bonus"] > 0:
        bonus_lines.append(f"🎯 +{int(bonuses['drop_bonus'] * 100)}% Rare Chance")
    if bonuses["extra_item_chance"] > 0:
        bonus_lines.append(f"🎁 +{int(bonuses['extra_item_chance'] * 100)}% Extra Item Chance")

    if bonus_lines:
        embed.add_field(name="✨ Active Bonuses", value="\n".join(bonus_lines), inline=False)

    embed.add_field(name="🗑️ Total Dives", value=str(player["total_dives"]), inline=True)
    embed.add_field(name="👑 Title", value=player["current_title"], inline=True)
    embed.add_field(name="🗺️ Zone", value=zone, inline=True)

    recent_text = "\n".join(recent_finds[-3:]) if recent_finds else "None yet"
    embed.add_field(name="🪄 Recent Finds", value=recent_text, inline=False)

    if quest_status:
        embed.add_field(name="🎯 Daily Quest", value=quest_status, inline=False)

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

    equipment_map = {entry.get("slot", ""): entry.get("item_id") for entry in equipment if isinstance(entry, dict) and "item_id" in entry}
    lines = []
    for slot in EQUIP_SLOTS:
        item_id = equipment_map.get(slot)
        if item_id:
            item = ITEMS.get(item_id, {"name": item_id, "emoji": "✨"})
            lines.append(f"{item.get('emoji', '✨')} **{item['name']}** — {slot.title()}")
        else:
            lines.append(f"▫️ **{slot.title()}** — Empty")
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
    attachment_filename=None,
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

    if attachment_filename:
        embed.set_thumbnail(url=f"attachment://{attachment_filename}")
    elif isinstance(item.get("image"), str) and item["image"].startswith("http"):
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

def museum_home_embed(username: str, discovered_item_ids: set[str]) -> discord.Embed:
    total_discovered = len(discovered_item_ids)
    total_artifacts = sum(len(collection["item_ids"]) for collection in MUSEUM_COLLECTIONS.values())

    embed = discord.Embed(
        title="🏛️ Trash Museum",
        description=(
            "\"Most people see garbage. You preserve history.\"\n\n"
            f"**Curator:** {username}\n"
            f"**Discovery Progress:** {total_discovered}/{total_artifacts} artifacts"
        ),
        color=0xC27C2C,
    )

    for collection_id, collection in MUSEUM_COLLECTIONS.items():
        item_ids = collection["item_ids"]
        discovered = sum(1 for item_id in item_ids if item_id in discovered_item_ids)
        embed.add_field(
            name=f"{collection['emoji']} {collection['name']}",
            value=(
                f"{collection['description']}\n"
                f"**Progress:** {discovered}/{len(item_ids)}"
            ),
            inline=False,
        )

    embed.set_footer(text="Choose a collection to browse its artifacts")
    return embed


def museum_collection_embed(
    username: str,
    collection_id: str,
    discovered_item_ids: set[str],
    page: int,
    total_pages: int,
):
    collection = MUSEUM_COLLECTIONS[collection_id]
    item_ids = collection["item_ids"]
    per_page = 6
    start = page * per_page
    end = start + per_page
    current_ids = item_ids[start:end]

    lines = []
    for item_id in current_ids:
        item = ITEMS.get(item_id, {"name": item_id, "emoji": "✨", "rarity": "Unknown"})
        discovered = item_id in discovered_item_ids
        if discovered:
            lines.append(
                f"✅ {item.get('emoji', '✨')} **{item['name']}**\n"
                f"{item.get('rarity', 'Unknown')} artifact recovered"
            )
        else:
            lines.append(
                "❔ **Unknown Artifact**\n"
                "Undiscovered relic. Keep diving, mixing, and refining."
            )

    embed = discord.Embed(
        title=f"{collection['emoji']} {collection['name']}",
        description="\n\n".join(lines),
        color=0x5865F2,
    )
    embed.add_field(
        name="Collection Notes",
        value=collection["description"],
        inline=False,
    )
    embed.set_footer(text=f"{username} • Page {page + 1}/{total_pages}")
    return embed


def museum_artifact_embed(item_id: str, discovered: bool) -> discord.Embed:
    item = ITEMS.get(item_id, {"name": item_id, "emoji": "✨", "rarity": "Unknown", "flavor": ""})
    lore = MUSEUM_ARTIFACT_TEXT.get(item_id, {})

    if discovered:
        description = (
            f"{item.get('emoji', '✨')} **{item['name']}**\n"
            f"**Status:** Collected ✅\n"
            f"**Rarity:** {item.get('rarity', 'Unknown')}\n\n"
            f"*{lore.get('museum_text') or item.get('flavor', 'Recovered from the underground junk world.')}*"
        )
        origin_text = lore.get("origin", "Origin not yet archived.")
        color = RARITY_COLORS.get(item.get("rarity", "Common"), 0x5865F2)
    else:
        description = (
            "❔ **Unknown Artifact**\n"
            "**Status:** Undiscovered\n\n"
            "Its details are still obscured. Recover it in the field to archive it here."
        )
        origin_text = "Unknown origin"
        color = 0x4E5D94

    embed = discord.Embed(
        title="🏛️ Artifact Card",
        description=description,
        color=color,
    )
    embed.add_field(name="Origin", value=origin_text, inline=False)

    image_path = item.get("image")
    if discovered and isinstance(image_path, str) and image_path.startswith("http"):
        embed.set_thumbnail(url=image_path)

    return embed


def museum_home_embed(
    museum_level: int,
    museum_xp: int,
    collections_completed: int,
    total_collections: int,
    next_collection_info: tuple[str, str, int, int] | None = None,
) -> discord.Embed:
    """Museum home view showing level, XP, and next collection."""
    xp_for_level = 100
    xp_in_current_level = museum_xp % xp_for_level
    
    embed = discord.Embed(
        title="🏛️ Museum",
        description=f"Your personal archive of discovered treasures and memories.",
        color=0xFFD700,
        timestamp=datetime.utcnow(),
    )
    
    embed.add_field(
        name="📚 Level",
        value=f"**{museum_level}** — {xp_in_current_level}/{xp_for_level} XP to next level",
        inline=False,
    )
    
    embed.add_field(
        name="🎯 Collections",
        value=f"**{collections_completed} / {total_collections}** completed",
        inline=True,
    )
    
    embed.add_field(
        name="✨ Total XP",
        value=f"**{museum_xp}** XP earned",
        inline=True,
    )
    
    if next_collection_info:
        collection_key, collection_name, progress, total = next_collection_info
        embed.add_field(
            name="📍 Next Collection",
            value=f"**{collection_name}**\n{progress}/{total} items discovered",
            inline=False,
        )
    
    return embed


def museum_collections_embed(
    collections_data: dict[str, dict],
    discovered_item_ids: set[str],
    completed_collections: set[str],
) -> discord.Embed:
    """List all collections with progress."""
    embed = discord.Embed(
        title="📖 Collections",
        description="Your museum archives. Complete collections for bonuses.",
        color=0x9B59B6,
        timestamp=datetime.utcnow(),
    )
    
    for collection_key, collection_data in collections_data.items():
        required_items = set(collection_data.get("item_ids", []))
        discovered = len(required_items & discovered_item_ids)
        total = len(required_items)
        is_complete = collection_key in completed_collections
        
        emoji = collection_data.get("emoji", "📦")
        name = collection_data.get("name", collection_key)
        
        if is_complete:
            status = f"{emoji} ✅ **{name}** (Complete)"
        else:
            status = f"{emoji} **{name}**"
        
        progress_bar = "🟩" * discovered + "⬜" * (total - discovered)
        value = f"{progress_bar}\n{discovered}/{total} items"
        
        embed.add_field(name=status, value=value, inline=False)
    
    return embed
