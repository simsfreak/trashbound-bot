from datetime import datetime
import discord

from game.data import EQUIP_SLOTS, ITEMS, ZONES, get_live_events, MUSEUM_COLLECTIONS, MUSEUM_ARTIFACT_TEXT
from game.leveling import xp_to_next_level
from game.helpers import calculate_equipment_bonuses
from game.icons import get_icon, format_stat_line as format_stat_icon, format_status_bar
from game.neon_data import STATS, SURVIVAL_METRICS, PROGRESSION_TITLES, get_title_for_level
from ui.panel_formatter import PanelFormatter, formatter
from ui.ui_config import COLORS, RARITIES, PAGINATION


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
    """Build profile dashboard using new panel system (MODE A - DASHBOARD)."""
    from datetime import datetime as dt
    from ui.panel_formatter import PanelFormatter
    
    fmt = PanelFormatter(width=50)
    
    # Build panel sections
    sections = []
    
    # HEADER
    sections.append(fmt.header(f"👤 {player['username']}"))
    
    # STATS SECTION
    sections.append(fmt.section_header("📊", "RESOURCES"))
    sections.append(fmt.line(f"{get_icon('caps')} Caps        » {player.get('coins', 0)}"))
    sections.append(fmt.line(f"⭐ Level        » {player.get('level', 1)}"))
    sections.append(fmt.line(f"{get_icon('inventory')} Items      » {inventory_count}"))
    sections.append(fmt.line(f"🎟  Tickets     » {dirty_tickets}"))
    
    sections.append(fmt.blank_line())
    
    # PROGRESS SECTION (XP Bar)
    needed_xp = xp_to_next_level(player.get('level', 1))
    current_xp = player.get('xp', 0)
    if needed_xp > 0:
        filled = int((current_xp / needed_xp) * 10)
        bar = "█" * filled + "░" * (10 - filled)
    else:
        bar = "█" * 10
    
    sections.append(fmt.section_header("✨", "PROGRESS"))
    sections.append(fmt.line(f"XP Progress"))
    sections.append(fmt.line(f"{bar} {current_xp}/{needed_xp}"))
    
    sections.append(fmt.blank_line())
    
    # QUEST SECTION
    sections.append(fmt.section_header("📜", "QUESTS"))
    if active_quest_info:
        status_icon = active_quest_info.get("status", "🟡")
        sections.append(fmt.line(f"{status_icon} {active_quest_info['name']}"))
        sections.append(fmt.line(f"📍 {active_quest_info['zone']}"))
        sections.append(fmt.line(f"⏰ {active_quest_info['time_window']}"))
    else:
        sections.append(fmt.line("No active quest"))
    
    sections.append(fmt.blank_line())
    
    # RECENT DROP SECTION
    sections.append(fmt.section_header("💎", "RECENT"))
    if recent_finds:
        sections.append(fmt.line(recent_finds[0][:44]))
    else:
        sections.append(fmt.line("None yet"))
    
    # FOOTER
    sections.append(fmt.footer())
    
    panel_text = "\n".join(sections)
    
    embed = discord.Embed(
        description=f"```\n{panel_text}\n```",
        color=COLORS["primary"],
    )
    
    if avatar_url:
        embed.set_thumbnail(url=avatar_url)
    
    embed.set_footer(text="Neon Wastes Survival")
    return embed


def dive_processing_embed(zone_name, text):
    """Processing embed during a scavenge - MODE C (Event)."""
    from ui.panel_formatter import PanelFormatter
    
    fmt = PanelFormatter(width=50)
    
    sections = []
    sections.append(fmt.header(f"🧭 SCAVENGING"))
    sections.append(fmt.section_header("🗺️", f"{zone_name}"))
    
    # Split text into lines for panel
    for line in text.split("\n"):
        if line.strip():
            sections.append(fmt.line(line[:44]))
    
    sections.append(fmt.blank_line())
    sections.append(fmt.line("Searching...", align="center"))
    sections.append(fmt.footer())
    
    panel_text = "\n".join(sections)
    
    return discord.Embed(
        description=f"```\n{panel_text}\n```",
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
    """Embed for item loot result - MODE C (Event)."""
    from ui.panel_formatter import PanelFormatter
    
    fmt = PanelFormatter(width=50)
    
    item = ITEMS[item_id]
    rarity = item.get("rarity", "Common")
    
    sections = []
    sections.append(fmt.header("💎 LOOT FOUND"))
    sections.append(fmt.section_header(item.get('emoji', '✨'), item['name'][:30]))
    sections.append(fmt.line(f"Rarity: {rarity}"))
    
    if item.get("flavor"):
        flavor_lines = item['flavor'].split("\n")
        for fl in flavor_lines[:2]:
            sections.append(fmt.line(f"*{fl[:42]}*"))
    
    sections.append(fmt.blank_line())
    
    # Rewards
    sections.append(fmt.section_header("🎁", "REWARDS"))
    sections.append(fmt.line(f"{get_icon('caps')} Coins      » {player['coins']}"))
    sections.append(fmt.line(f"⭐ Level      » {player['level']}"))
    sections.append(fmt.line(f"🧭 Dives      » {player['total_dives']}"))
    
    needed = xp_to_next_level(player.get("level", 1))
    current = player.get("xp", 0)
    if needed > 0:
        filled = int((current / needed) * 8)
        bar = "█" * filled + "░" * (8 - filled)
    else:
        bar = "█" * 8
    sections.append(fmt.line(f"✨ XP  {bar}"))
    
    if leveled_up:
        sections.append(fmt.blank_line())
        sections.append(fmt.line("⬆️ LEVEL UP!", align="center"))
    
    if unlocked_zone_names:
        sections.append(fmt.blank_line())
        sections.append(fmt.section_header("🔓", "NEW ZONES"))
        for zone in unlocked_zone_names[:2]:
            sections.append(fmt.line(f"→ {zone[:38]}"))
    
    sections.append(fmt.footer())
    
    panel_text = "\n".join(sections)
    
    embed = discord.Embed(
        description=f"```\n{panel_text}\n```",
        color=RARITY_COLORS.get(rarity, COLORS["secondary"]),
    )
    
    if avatar_url:
        embed.set_author(name=player["username"], icon_url=avatar_url)
    
    if attachment_filename:
        embed.set_thumbnail(url=f"attachment://{attachment_filename}")
    elif isinstance(item.get("image"), str) and item["image"].startswith("http"):
        embed.set_thumbnail(url=item["image"])
    
    return embed


def inventory_embed(username: str, lines: list[str], page: int, total_pages: int) -> discord.Embed:
    """Inventory list using MODE B (List) - New Panel System."""
    from ui.panel_formatter import PanelFormatter
    
    fmt = PanelFormatter(width=50)
    
    sections = []
    sections.append(fmt.header(f"🎒 {username}'s Vault"))
    sections.append(fmt.section_header("📦", "LOOT"))
    
    if not lines:
        sections.append(fmt.line("(empty)"))
    else:
        for line in lines[:8]:  # Show max 8 items per page in panel
            # Truncate long item descriptions to fit
            if len(line) > 44:
                line = line[:41] + "..."
            sections.append(fmt.line(line))
    
    if total_pages > 1:
        sections.append(fmt.blank_line())
        sections.append(fmt.line(f"Page {page + 1}/{total_pages}", align="center"))
    
    sections.append(fmt.footer())
    
    panel_text = "\n".join(sections)
    
    embed = discord.Embed(
        description=f"```\n{panel_text}\n```",
        color=COLORS["accent"],
    )
    if total_pages > 1:
        embed.set_footer(text=f"Page {page + 1}/{total_pages}")
    return embed


def zone_embed(player, zone_id, unlocked_zone_ids, zone_loot_lines, index, total):
    """Zone selector embed - MODE B (List)."""
    from ui.panel_formatter import PanelFormatter
    
    fmt = PanelFormatter(width=50)
    zone = ZONES[zone_id]
    unlocked = zone_id in unlocked_zone_ids
    current = zone_id == player["current_zone_id"]
    
    sections = []
    sections.append(fmt.header(f"🗺️ Zone {index + 1}/{total}"))
    
    if current:
        sections.append(fmt.section_header("✅", f"{zone['name']} (CURRENT)"))
        status_color = COLORS["success"]
    elif unlocked:
        sections.append(fmt.section_header("✅", zone['name']))
        status_color = COLORS["success"]
    else:
        sections.append(fmt.section_header("🔒", f"{zone['name']} (Level {zone['unlock_level']})"))
        status_color = COLORS["danger"]
    
    # Description
    desc_lines = zone['description'].split("\n")
    for desc in desc_lines[:2]:
        if desc.strip():
            sections.append(fmt.line(f"*{desc[:42]}*"))
    
    sections.append(fmt.blank_line())
    sections.append(fmt.section_header("🧭", "Finds"))
    
    if zone_loot_lines:
        for loot in zone_loot_lines[:4]:
            sections.append(fmt.line(loot[:44]))
    else:
        sections.append(fmt.line("???"))
    
    sections.append(fmt.footer())
    
    panel_text = "\n".join(sections)
    
    embed = discord.Embed(
        description=f"```\n{panel_text}\n```",
        color=status_color,
    )
    return embed


def mix_lab_embed(inventory_map, mix_lines):
    """Crafting lab embed - MODE B (List)."""
    from ui.panel_formatter import PanelFormatter
    
    fmt = PanelFormatter(width=50)
    
    sections = []
    sections.append(fmt.header("⚒️ CRAFTING"))
    sections.append(fmt.section_header("🔨", "RECIPES"))
    
    if not mix_lines:
        sections.append(fmt.line("No recipes available"))
    else:
        for recipe in mix_lines[:6]:
            sections.append(fmt.line(recipe[:44]))
    
    sections.append(fmt.footer())
    
    panel_text = "\n".join(sections)
    
    return discord.Embed(
        description=f"```\n{panel_text}\n```",
        color=COLORS["secondary"],
    )


def mix_result_embed(title: str, result_text: str) -> discord.Embed:
    """Crafting result embed - MODE C (Event)."""
    from ui.panel_formatter import PanelFormatter
    
    fmt = PanelFormatter(width=50)
    
    sections = []
    sections.append(fmt.header("✨ CRAFTED"))
    sections.append(fmt.section_header("🔨", title))
    
    for line in result_text.split("\n")[:4]:
        if line.strip():
            sections.append(fmt.line(line[:44]))
    
    sections.append(fmt.footer())
    
    panel_text = "\n".join(sections)
    
    return discord.Embed(
        description=f"```\n{panel_text}\n```",
        color=COLORS["secondary"]
    )


def events_embed() -> discord.Embed:
    """World events embed - MODE C (Event)."""
    from ui.panel_formatter import PanelFormatter
    
    fmt = PanelFormatter(width=50)
    
    sections = []
    sections.append(fmt.header("🌍 EVENTS"))
    
    live = get_live_events()
    
    if not live:
        sections.append(fmt.section_header("🌫️", "STATUS"))
        sections.append(fmt.line("No active events"))
    else:
        sections.append(fmt.section_header("✨", "ACTIVE EVENTS"))
        for event in live[:3]:
            sections.append(fmt.line(f"{event.get('emoji', '✨')} {event['name'][:35]}"))
            desc = event.get("description", "")
            if desc:
                sections.append(fmt.line(f"  {desc[:40]}"))
    
    sections.append(fmt.footer())
    
    panel_text = "\n".join(sections)
    
    embed = discord.Embed(
        description=f"```\n{panel_text}\n```",
        color=COLORS["warning"]
    )
    return embed


def help_embed() -> discord.Embed:
    """Help/tutorial embed - MODE B (List)."""
    from ui.panel_formatter import PanelFormatter
    
    fmt = PanelFormatter(width=50)
    
    sections = []
    sections.append(fmt.header("❓ HELP"))
    sections.append(fmt.section_header("🧭", "BASICS"))
    sections.append(fmt.line("Scavenge ruins for items"))
    sections.append(fmt.line("Manage your inventory"))
    sections.append(fmt.line("Complete contracts"))
    sections.append(fmt.line("Survive the wastes"))
    sections.append(fmt.blank_line())
    sections.append(fmt.section_header("💡", "TIPS"))
    sections.append(fmt.line("Better gear = better loot"))
    sections.append(fmt.line("Collect all artifacts"))
    sections.append(fmt.line("Complete daily quests"))
    sections.append(fmt.footer())
    
    panel_text = "\n".join(sections)
    
    embed = discord.Embed(
        description=f"```\n{panel_text}\n```",
        color=COLORS["info"]
    )
    return embed

def pawn_shop_embed(bundle_item_ids: list[str]) -> discord.Embed:
    """Pawn shop trading embed - MODE B (List)."""
    from ui.panel_formatter import PanelFormatter
    
    fmt = PanelFormatter(width=50)
    
    sections = []
    sections.append(fmt.header("🏚️ PAWN SHOP"))
    
    if not bundle_item_ids:
        sections.append(fmt.section_header("🛄", "STATUS"))
        sections.append(fmt.line("You have nothing to trade."))
    else:
        sections.append(fmt.section_header("💼", "YOUR OFFER"))
        counts = {}
        for item_id in bundle_item_ids:
            counts[item_id] = counts.get(item_id, 0) + 1
        
        for item_id, qty in list(counts.items())[:6]:
            item = ITEMS.get(item_id, {"name": item_id, "emoji": "✨"})
            sections.append(fmt.line(f"{item.get('emoji','✨')} {item['name']} x{qty}"))
    
    sections.append(fmt.blank_line())
    sections.append(fmt.line("Choose your deal wisely.", align="center"))
    sections.append(fmt.footer())
    
    panel_text = "\n".join(sections)
    
    return discord.Embed(
        description=f"```\n{panel_text}\n```",
        color=COLORS["warning"],
    )


def pawn_offer_result_embed(title: str, description: str) -> discord.Embed:
    """Pawn trade result embed - MODE C (Event)."""
    from ui.panel_formatter import PanelFormatter
    
    fmt = PanelFormatter(width=50)
    
    sections = []
    sections.append(fmt.header("💰 TRADE RESULT"))
    sections.append(fmt.section_header("💸", title))
    
    for line in description.split("\n")[:4]:
        if line.strip():
            sections.append(fmt.line(line[:44]))
    
    sections.append(fmt.footer())
    
    panel_text = "\n".join(sections)
    
    return discord.Embed(
        description=f"```\n{panel_text}\n```",
        color=COLORS["success"],
    )

def museum_home_embed(username: str, discovered_item_ids: set[str]) -> discord.Embed:
    """Museum home showing collections - MODE B (List)."""
    from ui.panel_formatter import PanelFormatter
    
    fmt = PanelFormatter(width=50)
    
    total_discovered = len(discovered_item_ids)
    total_artifacts = sum(len(collection["item_ids"]) for collection in MUSEUM_COLLECTIONS.values())
    
    sections = []
    sections.append(fmt.header("🏛️ ARCHIVE"))
    sections.append(fmt.section_header("📚", f"Curator: {username}"))
    sections.append(fmt.line(f"Artifacts: {total_discovered}/{total_artifacts}"))
    sections.append(fmt.blank_line())
    
    sections.append(fmt.section_header("📦", "COLLECTIONS"))
    
    for collection_id, collection in list(MUSEUM_COLLECTIONS.items())[:5]:
        item_ids = collection["item_ids"]
        discovered = sum(1 for item_id in item_ids if item_id in discovered_item_ids)
        progress = f"{discovered}/{len(item_ids)}"
        name_short = collection['name'][:35]
        sections.append(fmt.line(f"{collection['emoji']} {name_short} {progress}"))
    
    sections.append(fmt.footer())
    
    panel_text = "\n".join(sections)
    
    return discord.Embed(
        description=f"```\n{panel_text}\n```",
        color=COLORS["warning"],
    )


def museum_collection_embed(
    username: str,
    collection_id: str,
    discovered_item_ids: set[str],
    page: int,
    total_pages: int,
):
    """Museum collection page - MODE B (List)."""
    from ui.panel_formatter import PanelFormatter
    
    fmt = PanelFormatter(width=50)
    
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
            lines.append(f"✅ {item.get('emoji', '✨')} {item['name'][:25]} [{rarity_icon}]")
        else:
            lines.append("❔ ???")

    sections = []
    sections.append(fmt.header(f"📦 {collection['emoji']}"))
    sections.append(fmt.section_header("📚", collection['name'][:30]))
    
    for line in lines:
        sections.append(fmt.line(line[:44]))
    
    if total_pages > 1:
        sections.append(fmt.blank_line())
        sections.append(fmt.line(f"Page {page + 1}/{total_pages}", align="center"))
    
    sections.append(fmt.footer())
    
    panel_text = "\n".join(sections)

    embed = discord.Embed(
        description=f"```\n{panel_text}\n```",
        color=COLORS["accent"],
    )
    embed.set_footer(text=f"{username} • Page {page + 1}/{total_pages}")
    return embed


def museum_artifact_embed(item_id: str, discovered: bool) -> discord.Embed:
    """Museum artifact detail card - MODE C (Event)."""
    from ui.panel_formatter import PanelFormatter
    
    fmt = PanelFormatter(width=50)
    
    item = ITEMS.get(item_id, {"name": item_id, "emoji": "✨", "rarity": "Unknown", "flavor": ""})
    lore = MUSEUM_ARTIFACT_TEXT.get(item_id, {})

    sections = []
    sections.append(fmt.header("🏛️ ARTIFACT"))
    
    if discovered:
        sections.append(fmt.section_header(item.get('emoji', '✨'), item['name'][:30]))
        sections.append(fmt.line(f"Rarity: {item.get('rarity', 'Unknown')}"))
        sections.append(fmt.line("Status: ✅ Collected"))
        sections.append(fmt.blank_line())
        
        text = lore.get('museum_text') or item.get('flavor', 'A relic.')
        for line in text.split("\n")[:3]:
            sections.append(fmt.line(f"*{line[:42]}*"))
        color = RARITY_COLORS.get(item.get("rarity", "Common"), COLORS["info"])
    else:
        sections.append(fmt.section_header("❔", "UNKNOWN"))
        sections.append(fmt.line("Status: 🔒 Undiscovered"))
        sections.append(fmt.blank_line())
        sections.append(fmt.line("Discover this item in"))
        sections.append(fmt.line("the wasteland to archive"))
        color = COLORS["danger"]
    
    sections.append(fmt.footer())
    
    panel_text = "\n".join(sections)
    
    embed = discord.Embed(
        description=f"```\n{panel_text}\n```",
        color=color,
    )

    if discovered and isinstance(item.get("image"), str) and item["image"].startswith("http"):
        embed.set_thumbnail(url=item["image"])

    return embed


def museum_collections_embed(
    collections_data: dict[str, dict],
    discovered_item_ids: set[str],
    completed_collections: set[str],
) -> discord.Embed:
    """List all collections with progress - MODE B (List)."""
    from ui.panel_formatter import PanelFormatter
    
    fmt = PanelFormatter(width=50)
    
    sections = []
    sections.append(fmt.header("📖 COLLECTIONS"))
    sections.append(fmt.section_header("📚", "ALL ARCHIVES"))
    
    for collection_key, collection_data in list(collections_data.items())[:6]:
        required_items = set(collection_data.get("item_ids", []))
        discovered = len(required_items & discovered_item_ids)
        total = len(required_items)
        is_complete = collection_key in completed_collections
        
        emoji = collection_data.get("emoji", "📦")
        name = collection_data.get("name", collection_key)[:25]
        
        if is_complete:
            sections.append(fmt.line(f"{emoji} ✅ {name}"))
        else:
            sections.append(fmt.line(f"{emoji} {name} {discovered}/{total}"))
    
    sections.append(fmt.footer())
    
    panel_text = "\n".join(sections)
    
    embed = discord.Embed(
        description=f"```\n{panel_text}\n```",
        color=0x9B59B6,
        timestamp=datetime.utcnow(),
    )
    
    return embed


def admin_panel_embed(unread_count: int = 0) -> discord.Embed:
    """Admin panel home - MODE A (Dashboard)."""
    from ui.panel_formatter import PanelFormatter
    
    fmt = PanelFormatter(width=50)
    
    sections = []
    sections.append(fmt.header("🛠️ ADMIN"))
    sections.append(fmt.section_header("⚙️", "TOOLS"))
    sections.append(fmt.line(f"📬 Messages ({unread_count} unread)"))
    sections.append(fmt.line("🎁 Grant Tools"))
    sections.append(fmt.line("🌍 Events"))
    sections.append(fmt.blank_line())
    sections.append(fmt.footer())
    
    panel_text = "\n".join(sections)
    
    embed = discord.Embed(
        description=f"```\n{panel_text}\n```",
        color=0xED4245,
        timestamp=datetime.utcnow(),
    )
    
    return embed


def admin_messages_embed(messages: list[dict], page: int = 1, per_page: int = 5) -> discord.Embed:
    """List all contact messages - MODE B (List)."""
    from ui.panel_formatter import PanelFormatter
    
    fmt = PanelFormatter(width=50)
    
    total = len(messages)
    total_pages = (total + per_page - 1) // per_page
    start_idx = (page - 1) * per_page
    end_idx = min(start_idx + per_page, total)
    
    sections = []
    sections.append(fmt.header("📬 MESSAGES"))
    sections.append(fmt.section_header("📧", f"Page {page}/{total_pages}"))
    
    for i, msg in enumerate(messages[start_idx:end_idx], 1):
        status_icon = "✉️" if msg["status"] == "open" else "✅"
        username = msg.get("username", "Unknown")[:20]
        subject = msg.get("subject", "No subject")[:25]
        sections.append(fmt.line(f"{status_icon} {i}. {username}"))
        sections.append(fmt.line(f"   {subject}"))
    
    if total_pages > 1:
        sections.append(fmt.blank_line())
        sections.append(fmt.line(f"Page {page}/{total_pages}", align="center"))
    
    sections.append(fmt.footer())
    
    panel_text = "\n".join(sections)
    
    embed = discord.Embed(
        description=f"```\n{panel_text}\n```",
        color=0x5865F2,
        timestamp=datetime.utcnow(),
    )
    
    return embed


def admin_message_detail_embed(message: dict) -> discord.Embed:
    """Show full message details - MODE C (Event)."""
    from ui.panel_formatter import PanelFormatter
    
    fmt = PanelFormatter(width=50)
    
    sections = []
    sections.append(fmt.header("📧 MESSAGE"))
    sections.append(fmt.section_header("👤", f"From: {message.get('username', 'Unknown')[:25]}"))
    sections.append(fmt.line(f"Subject: {message.get('subject', 'N/A')[:36]}"))
    sections.append(fmt.blank_line())
    sections.append(fmt.section_header("📝", "CONTENT"))
    
    msg_text = message.get("message", "")
    for line in msg_text.split("\n")[:4]:
        if line.strip():
            sections.append(fmt.line(line[:44]))
    
    sections.append(fmt.footer())
    
    panel_text = "\n".join(sections)
    
    embed = discord.Embed(
        description=f"```\n{panel_text}\n```",
        color=0x5865F2,
        timestamp=datetime.utcnow(),
    )
    
    return embed


def admin_grant_success_embed(action: str, player_name: str, details: str) -> discord.Embed:
    """Grant action success confirmation - MODE C (Event)."""
    from ui.panel_formatter import PanelFormatter
    
    fmt = PanelFormatter(width=50)
    
    sections = []
    sections.append(fmt.header("✅ GRANTED"))
    sections.append(fmt.section_header("✨", action))
    sections.append(fmt.line(f"Player: {player_name[:30]}"))
    sections.append(fmt.blank_line())
    sections.append(fmt.section_header("📊", "DETAILS"))
    
    for line in details.split("\n"):
        if line.strip():
            sections.append(fmt.line(line[:44]))
    
    sections.append(fmt.footer())
    
    panel_text = "\n".join(sections)
    
    embed = discord.Embed(
        description=f"```\n{panel_text}\n```",
        color=0x2ECC71,
        timestamp=datetime.utcnow(),
    )
    
    return embed
