from datetime import datetime
import discord

from game.data import EQUIP_SLOTS, ITEMS, ZONES, get_live_events, MUSEUM_COLLECTIONS, MUSEUM_ARTIFACT_TEXT
from game.leveling import xp_to_next_level
from game.helpers import calculate_equipment_bonuses
from game.icons import get_icon, format_stat_line as format_stat_icon, format_status_bar
from game.neon_data import STATS, SURVIVAL_METRICS, PROGRESSION_TITLES, get_title_for_level
from ui.panel_formatter import PanelFormatter, formatter
from ui.ui_config import COLORS, RARITIES, PAGINATION
from ui.profile_formatter import format_profile_display


RARITY_COLORS = {
    "Common": COLORS["common"],
    "Uncommon": COLORS["uncommon"],
    "Rare": COLORS["rare"],
    "Epic": COLORS["epic"],
    "Legendary": COLORS["legendary"],
    "Mythic": COLORS["mythic"],
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
    active_quest_info=None,
):
    """
    Build profile dashboard using MODE A (Dashboard).
    
    Sections:
    - 📊 RESOURCES (caps, level, items)
    - ❤️ VITALS (health, hunger, thirst, radiation, energy)
    - 🛡️ EQUIPMENT (currently equipped gear)
    - 📜 QUESTS (active and daily quests)
    """
    from game.icons import format_status_bar
    
    # Prepare panel content
    panel_lines = []
    
    # ═════════════════════════════════════════════════════════════════
    # 📊 RESOURCES SECTION
    # ═════════════════════════════════════════════════════════════════
    resources_lines = [
        f"{get_icon('caps')} Caps: {player.get('coins', 0)}",
        f"⭐ Level: {player.get('level', 1)} — {get_title_for_level(player.get('level', 1))}",
        f"{get_icon('inventory')} Items: {inventory_count}",
    ]
    if dirty_tickets > 0:
        resources_lines.append(f"🎟 Tickets: {dirty_tickets}")
    
    panel_lines.append(("📊", "RESOURCES", resources_lines))
    
    # ═════════════════════════════════════════════════════════════════
    # ❤️ VITALS SECTION (Survival metrics)
    # ═════════════════════════════════════════════════════════════════
    vitals_lines = [
        format_status_bar("Health", 80, 100, bar_size=8),
        format_status_bar("Hunger", 70, 100, bar_size=8),
        format_status_bar("Thirst", 50, 100, bar_size=8),
    ]
    
    panel_lines.append(("❤️", "VITALS", vitals_lines))
    
    # ═════════════════════════════════════════════════════════════════
    # 🛡️ EQUIPMENT SECTION
    # ═════════════════════════════════════════════════════════════════
    slot_map = {e.get("slot", ""): e.get("item_id") for e in equipment if isinstance(e, dict) and e.get("slot")}
    equip_lines = []
    
    for slot in EQUIP_SLOTS if EQUIP_SLOTS else ["head", "body", "hands", "feet", "accessory"]:
        item_id = slot_map.get(slot)
        if item_id:
            item = ITEMS.get(item_id, {"name": item_id, "emoji": "✨"})
            equip_lines.append(f"[{item.get('emoji', '✨')}] {slot.title():10} {item['name']}")
        else:
            equip_lines.append(f"[ ] {slot.title():10} Empty")
    
    panel_lines.append(("🛡️", "EQUIPMENT", equip_lines))
    
    # ═════════════════════════════════════════════════════════════════
    # 📜 QUESTS SECTION
    # ═════════════════════════════════════════════════════════════════
    quest_lines = []
    
    if active_quest_info:
        status_icon = active_quest_info.get("status", "🟡")
        quest_lines.append(f"{status_icon} {active_quest_info['name']}")
        quest_lines.append(f"  Zone: {active_quest_info['zone']}")
        quest_lines.append(f"  Time: {active_quest_info['time_window']}")
    else:
        quest_lines.append("❌ No active quest")
    
    panel_lines.append(("📜", "QUESTS", quest_lines))
    
    # ═════════════════════════════════════════════════════════════════
    # BUILD DASHBOARD PANEL
    # ═════════════════════════════════════════════════════════════════
    now = datetime.now()
    description = f"📍 {now.strftime('%a, %b %d • %H:%M')}"
    
    panel_text = formatter.mode_a_dashboard(
        title="WASTELAND PROFILE",
        description=description,
        sections=panel_lines,
        footer_text="Use buttons below to navigate"
    )
    
    # ═════════════════════════════════════════════════════════════════
    # CREATE EMBED
    # ═════════════════════════════════════════════════════════════════
    embed = discord.Embed(
        title=f"👤 {player['username']}",
        description=f"```\n{panel_text}\n```",
        color=COLORS["primary"],
        timestamp=datetime.utcnow(),
    )

    if avatar_url:
        embed.set_thumbnail(url=avatar_url)
    
    embed.set_footer(text="Neon Wastes Survival")
    return embed


def dive_processing_embed(zone_name, text):
    """Processing embed during a scavenge."""
    return discord.Embed(
        title=f"{get_icon('scavenge')} Scavenging...",
        description=f"**{zone_name}**\n\n{text}",
        color=COLORS["accent"],
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
    """Embed for item loot result."""
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
        title=f"{get_icon('scavenge')} Loot Found!",
        description="\n\n".join(lines),
        color=RARITY_COLORS.get(rarity, COLORS["secondary"]),
    )

    if avatar_url:
        embed.set_author(name=player["username"], icon_url=avatar_url)

    if attachment_filename:
        embed.set_thumbnail(url=f"attachment://{attachment_filename}")
    elif isinstance(item.get("image"), str) and item["image"].startswith("http"):
        embed.set_thumbnail(url=item["image"])

    embed.add_field(name=f"{get_icon('caps')} Coins", value=str(player["coins"]), inline=True)
    embed.add_field(name="⭐ Level", value=str(player["level"]), inline=True)
    embed.add_field(name=f"{get_icon('scavenge')} Dives", value=str(player["total_dives"]), inline=True)
    
    needed = xp_to_next_level(player.get("level", 1))
    current = player.get("xp", 0)
    if needed > 0:
        filled = int((current / needed) * 8)
        bar = "█" * filled + "░" * (8 - filled)
    else:
        bar = "█" * 8
    
    embed.add_field(name="✨ XP", value=f"{bar} {current}/{needed}", inline=False)
    return embed


def inventory_embed(username: str, lines: list[str], page: int, total_pages: int) -> discord.Embed:
    """Inventory list using MODE B (List)."""
    panel_text = formatter.mode_b_list(
        title="INVENTORY",
        category_label=f"{get_icon('inventory')} YOUR LOOT",
        items=lines if lines else ["(empty)"],
        page_info=f"Page {page + 1}/{total_pages}" if total_pages > 1 else None,
        footer_text="Use buttons to navigate"
    )
    
    embed = discord.Embed(
        title=f"{get_icon('inventory')} {username}'s Vault",
        description=f"```\n{panel_text}\n```",
        color=COLORS["accent"],
    )
    if total_pages > 1:
        embed.set_footer(text=f"Page {page + 1}/{total_pages}")
    return embed


def zone_embed(player, zone_id, unlocked_zone_ids, zone_loot_lines, index, total):
    """Zone selector embed."""
    zone = ZONES[zone_id]
    unlocked = zone_id in unlocked_zone_ids
    current = zone_id == player["current_zone_id"]
    
    if current:
        status = f"{get_icon('success')} CURRENT ZONE"
        status_color = COLORS["success"]
    elif unlocked:
        status = f"✅ UNLOCKED"
        status_color = COLORS["success"]
    else:
        status = f"🔒 Unlocks at Level {zone['unlock_level']}"
        status_color = COLORS["danger"]

    embed = discord.Embed(
        title=f"{get_icon('map')} {zone['name']} ({index + 1}/{total})",
        description=f"{status}\n\n*{zone['description']}*",
        color=status_color,
    )
    embed.add_field(name=f"{get_icon('scavenge')} Possible Finds", value="\n".join(zone_loot_lines) if zone_loot_lines else "???", inline=False)
    return embed


def mix_lab_embed(inventory_map, mix_lines):
    """Crafting lab embed."""
    return discord.Embed(
        title=f"{get_icon('craft')} Crafting Lab",
        description="Available recipes right now:\n" + ("\n".join(mix_lines) if mix_lines else "None"),
        color=COLORS["secondary"],
    )


def mix_result_embed(title: str, result_text: str) -> discord.Embed:
    """Crafting result embed."""
    return discord.Embed(
        title=f"{get_icon('craft')} {title}",
        description=result_text,
        color=COLORS["secondary"]
    )


def events_embed() -> discord.Embed:
    """World events embed."""
    embed = discord.Embed(
        title=f"{get_icon('season')} World Events",
        description="The wasteland is in flux.",
        color=COLORS["warning"]
    )
    live = get_live_events()
    if not live:
        embed.add_field(name="🌫️ Right Now", value="No special event is live.", inline=False)
    else:
        for event in live:
            embed.add_field(name=f"{event.get('emoji', get_icon('anomaly'))} {event['name']}", value=event.get("description", ""), inline=False)
    return embed


def help_embed() -> discord.Embed:
    """Help/tutorial embed."""
    return discord.Embed(
        title="❓ How to Survive the Wastes",
        description="Scavenge resources, craft equipment, complete contracts, and survive.",
        color=COLORS["info"]
    )

def pawn_shop_embed(bundle_item_ids: list[str]) -> discord.Embed:
    """Pawn shop trading embed."""
    from game.data import ITEMS

    if not bundle_item_ids:
        desc = f"{get_icon('shelter')} The pawn broker stares at you.\n\nYou have nothing to trade."
    else:
        lines = []
        counts = {}
        for item_id in bundle_item_ids:
            counts[item_id] = counts.get(item_id, 0) + 1

        for item_id, qty in counts.items():
            item = ITEMS.get(item_id, {"name": item_id, "emoji": "✨"})
            lines.append(f"{item.get('emoji','✨')} **{item['name']}** x{qty}")

        desc = (
            f"{get_icon('shelter')} *The pawn broker squints at your goods...*\n\n"
            "**Your Offer:**\n"
            + "\n".join(lines)
            + "\n\nChoose your deal wisely."
        )

    embed = discord.Embed(
        title=f"{get_icon('shelter')} Trade Hub",
        description=desc,
        color=COLORS["warning"],
    )
    return embed


def pawn_offer_result_embed(title: str, description: str) -> discord.Embed:
    """Pawn trade result embed."""
    return discord.Embed(
        title=f"{get_icon('caps')} {title}",
        description=description,
        color=COLORS["success"],
    )

def museum_home_embed(username: str, discovered_item_ids: set[str]) -> discord.Embed:
    """Museum home showing collections."""
    total_discovered = len(discovered_item_ids)
    total_artifacts = sum(len(collection["item_ids"]) for collection in MUSEUM_COLLECTIONS.values())

    embed = discord.Embed(
        title="🏛️ Archive",
        description=(
            "Preserved history of the wasteland.\n\n"
            f"**Curator:** {username}\n"
            f"**Artifacts:** {total_discovered}/{total_artifacts} collected"
        ),
        color=COLORS["warning"],
    )

    for collection_id, collection in MUSEUM_COLLECTIONS.items():
        item_ids = collection["item_ids"]
        discovered = sum(1 for item_id in item_ids if item_id in discovered_item_ids)
        progress = f"{discovered}/{len(item_ids)}"
        embed.add_field(
            name=f"{collection['emoji']} {collection['name']}",
            value=f"{collection['description']}\n**Progress:** {progress}",
            inline=False,
        )

    embed.set_footer(text="Select a collection to view its items")
    return embed


def museum_collection_embed(
    username: str,
    collection_id: str,
    discovered_item_ids: set[str],
    page: int,
    total_pages: int,
):
    """Museum collection page."""
    collection = MUSEUM_COLLECTIONS[collection_id]
    item_ids = collection["item_ids"]
    per_page = 5
    start = page * per_page
    end = start + per_page
    current_ids = item_ids[start:end]

    lines = []
    for item_id in current_ids:
        item = ITEMS.get(item_id, {"name": item_id, "emoji": "✨", "rarity": "Unknown"})
        discovered = item_id in discovered_item_ids
        if discovered:
            rarity_icon = RARITIES.get(item.get("rarity", "Common"), {}).get("emoji", "✨")
            lines.append(f"✅ {item.get('emoji', '✨')} {item['name']} [{rarity_icon}]")
        else:
            lines.append("❔ ???")

    panel_text = formatter.mode_b_list(
        title="COLLECTION",
        category_label=f"{collection['emoji']} {collection['name']}",
        items=lines,
        page_info=f"Page {page + 1}/{total_pages}" if total_pages > 1 else None,
    )

    embed = discord.Embed(
        title=f"{collection['emoji']} {collection['name']}",
        description=f"```\n{panel_text}\n```",
        color=COLORS["accent"],
    )
    embed.add_field(name="ℹ️", value=collection["description"], inline=False)
    embed.set_footer(text=f"{username} • Page {page + 1}/{total_pages}")
    return embed


def museum_artifact_embed(item_id: str, discovered: bool) -> discord.Embed:
    """Museum artifact detail card."""
    item = ITEMS.get(item_id, {"name": item_id, "emoji": "✨", "rarity": "Unknown", "flavor": ""})
    lore = MUSEUM_ARTIFACT_TEXT.get(item_id, {})

    if discovered:
        description = (
            f"{item.get('emoji', '✨')} **{item['name']}**\n"
            f"**Rarity:** {item.get('rarity', 'Unknown')} {RARITIES.get(item.get('rarity', 'Common'), {}).get('emoji', '')}\n"
            f"**Status:** ✅ Collected\n\n"
            f"*{lore.get('museum_text') or item.get('flavor', 'A relic of the old world.')}*"
        )
        color = RARITY_COLORS.get(item.get("rarity", "Common"), COLORS["info"])
    else:
        description = (
            "❔ **Unknown Artifact**\n"
            "**Status:** 🔒 Undiscovered\n\n"
            "Its details remain obscured. Discover it in the wasteland to archive it."
        )
        color = COLORS["danger"]

    embed = discord.Embed(
        title="🏛️ Artifact",
        description=description,
        color=color,
    )

    if discovered and isinstance(item.get("image"), str) and item["image"].startswith("http"):
        embed.set_thumbnail(url=item["image"])

    return embed
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


def admin_panel_embed(unread_count: int = 0) -> discord.Embed:
    """Admin panel home."""
    embed = discord.Embed(
        title="🛠️ Admin Panel",
        description="Admin tools and utilities.",
        color=0xED4245,
        timestamp=datetime.utcnow(),
    )
    
    embed.add_field(
        name="📬 Contact Messages",
        value=f"📨 {unread_count} unread messages",
        inline=False,
    )
    
    embed.add_field(
        name="🎁 Grant Tools",
        value="Grant XP, Coins, Tickets, or Items to players.",
        inline=False,
    )
    
    embed.add_field(
        name="🌍 Events",
        value="Trigger or manage world events.",
        inline=False,
    )
    
    return embed


def admin_messages_embed(messages: list[dict], page: int = 1, per_page: int = 5) -> discord.Embed:
    """List all contact messages."""
    total = len(messages)
    total_pages = (total + per_page - 1) // per_page
    start_idx = (page - 1) * per_page
    end_idx = min(start_idx + per_page, total)
    
    embed = discord.Embed(
        title="📬 Contact Messages",
        description=f"Page {page}/{total_pages} ({total} total)",
        color=0x5865F2,
        timestamp=datetime.utcnow(),
    )
    
    for i, msg in enumerate(messages[start_idx:end_idx], 1):
        status_icon = "✉️" if msg["status"] == "open" else "✅"
        username = msg.get("username", "Unknown")
        subject = msg.get("subject", "No subject")
        created_at = msg.get("created_at", "Unknown date")
        
        embed.add_field(
            name=f"{status_icon} {i}. {username} — {subject}",
            value=f"ID: {msg['id']} | {created_at.strftime('%Y-%m-%d %H:%M') if hasattr(created_at, 'strftime') else created_at}",
            inline=False,
        )
    
    return embed


def admin_message_detail_embed(message: dict) -> discord.Embed:
    """Show full message details."""
    embed = discord.Embed(
        title=f"📧 Message from {message.get('username', 'Unknown')}",
        description=f"**Subject:** {message.get('subject', 'No subject')}",
        color=0x5865F2,
        timestamp=datetime.utcnow(),
    )
    
    embed.add_field(
        name="Message",
        value=message.get("message", "No message content"),
        inline=False,
    )
    
    embed.add_field(
        name="User ID",
        value=str(message.get("user_id", "Unknown")),
        inline=True,
    )
    
    embed.add_field(
        name="Message ID",
        value=str(message.get("id", "Unknown")),
        inline=True,
    )
    
    embed.add_field(
        name="Status",
        value=message.get("status", "unknown").title(),
        inline=True,
    )
    
    return embed


def admin_grant_success_embed(action: str, player_name: str, details: str) -> discord.Embed:
    """Grant action success confirmation."""
    embed = discord.Embed(
        title="✅ Admin Action Completed",
        description=f"**Action:** {action}\n**Player:** {player_name}",
        color=0x2ECC71,
        timestamp=datetime.utcnow(),
    )
    
    embed.add_field(
        name="Details",
        value=details,
        inline=False,
    )
    
    return embed
