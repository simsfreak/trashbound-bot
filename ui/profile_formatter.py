"""
ASCII Box Profile Formatter

Creates beautiful Unicode box-formatted profile displays with organized sections.
"""

from datetime import datetime
from typing import Optional, List, Tuple


class ProfileBox:
    """Helper for creating pretty ASCII box sections"""
    
    # Box drawing characters
    TOP_LEFT = "╭"
    TOP_RIGHT = "╮"
    BOTTOM_LEFT = "╰"
    BOTTOM_RIGHT = "╯"
    HORIZONTAL = "─"
    VERTICAL = "│"
    
    def __init__(self, width: int = 42):
        """
        Initialize box formatter.
        
        Args:
            width: Total width of the box (including borders and padding)
        """
        self.width = width
        self.content_width = width - 4  # Account for borders and padding
    
    def pad_line(self, text: str, align: str = "left") -> str:
        """
        Pad text to content width.
        
        Args:
            text: Text to pad
            align: "left", "center", or "right"
        """
        # Remove ANSI codes for length calculation (if any)
        display_len = len(text)
        
        if len(text) >= self.content_width:
            return text[:self.content_width]
        
        padding = self.content_width - display_len
        
        if align == "center":
            left_pad = padding // 2
            right_pad = padding - left_pad
            return " " * left_pad + text + " " * right_pad
        elif align == "right":
            return " " * padding + text
        else:  # left
            return text + " " * padding
    
    def section_header(self, emoji: str, title: str) -> str:
        """Create a section header with decorative dashes"""
        title_text = f" {emoji} {title} "
        dash_count = self.width - 4 - len(title_text)  # Account for corners
        left_dashes = dash_count // 2
        right_dashes = dash_count - left_dashes
        
        return f"{self.TOP_LEFT}{self.HORIZONTAL * left_dashes}{title_text}{self.HORIZONTAL * right_dashes}{self.TOP_RIGHT}"
    
    def section_line(self, text: str = "", align: str = "left") -> str:
        """Create a line within a section"""
        padded = self.pad_line(text, align)
        return f"{self.VERTICAL} {padded} {self.VERTICAL}"
    
    def section_footer(self) -> str:
        """Create a section footer"""
        return f"{self.BOTTOM_LEFT}{self.HORIZONTAL * (self.width - 2)}{self.BOTTOM_RIGHT}"
    
    def section(self, emoji: str, title: str, lines: List[str]) -> List[str]:
        """
        Create a complete section with header, lines, and footer.
        
        Args:
            emoji: Section emoji
            title: Section title
            lines: List of content lines
        
        Returns:
            List of formatted lines
        """
        result = [self.section_header(emoji, title)]
        for line in lines:
            result.append(self.section_line(line))
        result.append(self.section_footer())
        return result


def format_profile_display(
    player: dict,
    inventory_count: int,
    recent_finds: List[str],
    active_effects: List[dict],
    equipment: List[dict],
    dirty_tickets: int,
    active_quest_info: Optional[dict] = None,
    daily_quest: Optional[dict] = None,
    live_events: List[dict] = None,
) -> str:
    """
    Format complete profile as beautiful ASCII boxes.
    
    Returns:
        Formatted profile string suitable for Discord code block
    """
    from game.data import ZONES, ITEMS, EQUIP_SLOTS
    from game.time_system import get_phase_emoji
    from game.leveling import xp_to_next_level
    from game.helpers import calculate_equipment_bonuses
    
    box = ProfileBox(width=44)
    sections = []
    
    # ═════════════════════════════════════════
    # HEADER - Date/Time/Zone/Events
    # ═════════════════════════════════════════
    now = datetime.now()
    date_str = now.strftime("%a, %b %d")
    time_str = now.strftime("%H:%M")
    zone_name = "Unknown"
    if player.get("current_zone_id") in ZONES:
        zone_name = ZONES[player["current_zone_id"]]["name"]
    
    time_phase = player.get("current_time_phase", "morning")
    phase_emoji = get_phase_emoji(time_phase)
    
    # Get live events
    event_text = ""
    if live_events:
        event_names = [f"{e.get('emoji', '✨')} {e['name']}" for e in live_events[:1]]
        event_text = event_names[0] if event_names else "No events"
    else:
        event_text = "No live events"
    
    header_lines = [
        f"🗓 {date_str} • {time_str}",
        f"📍 {zone_name} {phase_emoji}",
        f"🌐 {event_text}",
    ]
    sections.append("\n".join(box.section("⏰", "PROFILE", header_lines)))
    
    # ═════════════════════════════════════════
    # STATS
    # ═════════════════════════════════════════
    stats_lines = [
        f"💰 Coins        » {player.get('coins', 0)}",
        f"🎟 Dirty Tickets» {dirty_tickets}",
        f"⭐ Level        » {player.get('level', 1)}",
        f"🎒 Items        » {inventory_count}",
    ]
    sections.append("\n".join(box.section("💰", "STATS", stats_lines)))
    
    # ═════════════════════════════════════════
    # PROGRESS - XP Bar
    # ═════════════════════════════════════════
    needed_xp = xp_to_next_level(player.get("level", 1))
    current_xp = player.get("xp", 0)
    if needed_xp > 0:
        filled = int((current_xp / needed_xp) * 10)
        bar = "🟩" * filled + "⬜" * (10 - filled)
    else:
        bar = "🟩" * 10
    
    progress_lines = [
        f"✨ XP",
        f"{bar} {current_xp} / {needed_xp}",
    ]
    sections.append("\n".join(box.section("✨", "PROGRESS", progress_lines)))
    
    # ═════════════════════════════════════════
    # BONUSES - Equipment effects
    # ═════════════════════════════════════════
    bonuses = calculate_equipment_bonuses(equipment)
    bonus_lines = []
    
    if bonuses["coin_boost"] > 0:
        bonus_lines.append(f"💸 +{int(bonuses['coin_boost'] * 100)}% Coin Gain")
    if bonuses["xp_boost"] > 0:
        bonus_lines.append(f"✨ +{int(bonuses['xp_boost'] * 100)}% XP Gain")
    if bonuses["loot_value"] > 0:
        bonus_lines.append(f"💎 +{int(bonuses['loot_value'] * 100)}% Item Value")
    if bonuses["drop_bonus"] > 0:
        bonus_lines.append(f"🎯 +{int(bonuses['drop_bonus'] * 100)}% Rare Chance")
    if bonuses["extra_item_chance"] > 0:
        bonus_lines.append(f"🎁 +{int(bonuses['extra_item_chance'] * 100)}% Extra Item")
    
    if bonus_lines:
        sections.append("\n".join(box.section("🎁", "BONUS", bonus_lines)))
    
    # ═════════════════════════════════════════
    # PROFILE STATS
    # ═════════════════════════════════════════
    title = player.get("current_title", "Trash Rookie")
    phase_name = {"morning": "Morning", "evening": "Evening", "night": "Night"}.get(time_phase, "Unknown")
    
    stat_lines = [
        f"🗑 Total Dives » {player.get('total_dives', 0)}",
        f"👑 Title       » {title}",
        f"🌅 Phase       » {phase_name}",
    ]
    sections.append("\n".join(box.section("📊", "STATS", stat_lines)))
    
    # ═════════════════════════════════════════
    # RECENT DROP
    # ═════════════════════════════════════════
    recent_lines = recent_finds[:1] if recent_finds else ["None yet"]
    sections.append("\n".join(box.section("💎", "RECENT DROP", recent_lines)))
    
    # ═════════════════════════════════════════
    # QUESTS - Active Quest
    # ═════════════════════════════════════════
    if active_quest_info:
        status_icon = active_quest_info.get("status", "🟡")
        quest_lines = [
            f"{status_icon} {active_quest_info['name']}",
            f"📍 {active_quest_info['zone']}",
            f"⏰ {active_quest_info['time_window']}",
        ]
    else:
        quest_lines = [
            "❌ No Active Quest",
            "👉 Browse to accept one!",
        ]
    sections.append("\n".join(box.section("📜", "QUESTS", quest_lines)))
    
    # ═════════════════════════════════════════
    # DAILY QUEST
    # ═════════════════════════════════════════
    if daily_quest:
        if daily_quest.get("redeemed"):
            quest_status = "✅ Redeemed"
            quest_detail = "New quest in 24h"
        elif daily_quest.get("completed"):
            quest_status = "🎉 Completed"
            quest_detail = "Ready to redeem!"
        else:
            quest_status = f"⏳ In Progress"
            progress = daily_quest.get("progress", 0)
            target = daily_quest.get("target", 1)
            quest_detail = f"{progress}/{target}"
        
        daily_lines = [
            f"{quest_status}",
            f"{quest_detail}",
        ]
    else:
        daily_lines = ["⏳ No daily quest"]
    
    sections.append("\n".join(box.section("🎯", "DAILY QUEST", daily_lines)))
    
    # ═════════════════════════════════════════
    # EQUIPMENT
    # ═════════════════════════════════════════
    slot_map = {e.get("slot", ""): e.get("item_id") for e in equipment if isinstance(e, dict) and e.get("slot")}
    equip_lines = []
    
    # Map slots to emojis
    SLOT_EMOJIS = {
        "head": "🧠",
        "body": "👕",
        "hands": "✋",
        "feet": "👟",
        "accessory": "🧲"
    }
    
    for slot in EQUIP_SLOTS if EQUIP_SLOTS else ["head", "body", "hands", "feet"]:
        slot_emoji = SLOT_EMOJIS.get(slot, "▫️")
        item_id = slot_map.get(slot)
        
        if item_id:
            item = ITEMS.get(item_id, {"name": item_id, "emoji": "✨"})
            equip_lines.append(f"{slot_emoji} {slot.title():6} » {item.get('emoji', '✨')} {item['name']}")
        else:
            equip_lines.append(f"{slot_emoji} {slot.title():6} » Empty")
    
    # Accessory
    accessory = slot_map.get("accessory")
    if accessory:
        item = ITEMS.get(accessory, {"name": accessory, "emoji": "✨"})
        equip_lines.append(f"")
        equip_lines.append(f"🧲 {item.get('emoji', '✨')} {item['name']} (Accessory)")
    
    sections.append("\n".join(box.section("🧸", "EQUIPMENT", equip_lines)))
    
    # ═════════════════════════════════════════
    # FOOTER
    # ═════════════════════════════════════════
    footer = f"🌸 🐾 Last Active: Today at {now.strftime('%I:%M %p')} 🐾 🌸"
    
    # Combine all sections
    result = "\n".join(sections)
    result += "\n\n" + footer
    
    return result


def format_profile_embed_description(
    player: dict,
    inventory_count: int,
    recent_finds: List[str],
    active_quest_info: Optional[dict] = None,
    live_events: Optional[List[dict]] = None,
) -> str:
    """
    Format compact profile header for embed description.
    
    Returns just the header section for use as embed description.
    """
    from game.data import ZONES
    from game.time_system import get_phase_emoji
    
    box = ProfileBox(width=44)
    
    now = datetime.now()
    date_str = now.strftime("%a, %b %d")
    time_str = now.strftime("%H:%M")
    
    zone_name = "Unknown"
    if player.get("current_zone_id") in ZONES:
        zone_name = ZONES[player["current_zone_id"]]["name"]
    
    time_phase = player.get("current_time_phase", "morning")
    phase_emoji = get_phase_emoji(time_phase)
    
    event_text = "No events"
    if live_events:
        event_names = [f"{e.get('emoji', '✨')} {e['name']}" for e in live_events[:1]]
        event_text = event_names[0] if event_names else "No events"
    
    header_lines = [
        f"🗓 {date_str} • {time_str}",
        f"📍 {zone_name} {phase_emoji}",
        f"🌐 {event_text}",
    ]
    
    return "\n".join(box.section("⏰", "PROFILE", header_lines))
