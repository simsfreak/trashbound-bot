"""
NEON WASTES ICON SYSTEM

Mandatory icon mapping for all UI elements.
Use these EXCLUSIVELY for consistency across the entire game.
"""

# ══════════════════════════════════════════════════════════════════════════════
# CORE SURVIVAL (Health, Hunger, Thirst, Radiation, Energy)
# ══════════════════════════════════════════════════════════════════════════════
SURVIVAL = {
    "health": "❤️",
    "hunger": "🍖",
    "thirst": "💧",
    "radiation": "☢️",
    "energy": "⚡",
}

# ══════════════════════════════════════════════════════════════════════════════
# CHARACTER STATS (STR, AGI, INT, END, LCK)
# ══════════════════════════════════════════════════════════════════════════════
STATS = {
    "strength": "💪",      # STR
    "agility": "🏃",       # AGI
    "intelligence": "🧠",  # INT
    "endurance": "🛡️",     # END
    "luck": "🍀",          # LCK
}

# Shorthand names for quick reference
STAT_SHORT = {
    "STR": "💪",
    "AGI": "🏃",
    "INT": "🧠",
    "END": "🛡️",
    "LCK": "🍀",
}

# ══════════════════════════════════════════════════════════════════════════════
# RESOURCES (Caps, Scrap, Food, Water, Meds, Cloth, Wire)
# ══════════════════════════════════════════════════════════════════════════════
RESOURCES = {
    "caps": "🪙",           # Currency
    "scrap": "🔩",          # Crafting material
    "food": "🥫",           # Consumable
    "water": "🧴",          # Consumable
    "meds": "💊",           # Consumable
    "cloth": "🧵",          # Crafting material
    "wire": "🔌",           # Crafting material
}

# ══════════════════════════════════════════════════════════════════════════════
# SYSTEMS & ACTIONS (Scavenge, Inventory, Craft, Fusion, Shelter, etc)
# ══════════════════════════════════════════════════════════════════════════════
SYSTEMS = {
    "scavenge": "🧭",       # Primary action
    "inventory": "🎒",      # Gear/items
    "craft": "⚒️",          # Crafting
    "fusion": "⚡",         # Enhancement
    "shelter": "🏚️",        # Base/home
    "network": "📡",        # Social/crew
    "contracts": "📜",      # Quests/jobs
    "map": "🗺️",            # Zones/travel
    "story": "📖",          # Narrative
    "crews": "👥",          # Teams
    "territory": "🏴",      # Control
    "season": "🌀",         # Events/phases
}

# ══════════════════════════════════════════════════════════════════════════════
# DANGER & SPECIAL STATUS
# ══════════════════════════════════════════════════════════════════════════════
STATUS = {
    "warning": "⚠️",        # Caution
    "alert": "🚨",          # Danger
    "breakthrough": "🌌",   # Major event
    "unknown": "❓",         # Mystery
    "anomaly": "🧪",        # Strange occurrence
    "enemy": "👾",          # Hostile
}

# ══════════════════════════════════════════════════════════════════════════════
# NAVIGATION BUTTONS
# ══════════════════════════════════════════════════════════════════════════════
NAVIGATION = {
    "back": "↩️",
    "profile": "🏠",
    "refresh": "🔄",
    "next": "➡️",
    "prev": "⬅️",
}

# ══════════════════════════════════════════════════════════════════════════════
# CORE ACTION BUTTONS (Root Navigation)
# These 8 buttons appear on most screens
# ══════════════════════════════════════════════════════════════════════════════
ACTION_BUTTONS = {
    "scavenge": "🧭",
    "inventory": "🎒",
    "craft": "⚒️",
    "shelter": "🏚️",
    "network": "📡",
    "contracts": "📜",
    "map": "🗺️",
    "story": "📖",
}

# ══════════════════════════════════════════════════════════════════════════════
# RISK / COMBAT ACTION BUTTONS
# ══════════════════════════════════════════════════════════════════════════════
COMBAT = {
    "fight": "⚔️",
    "skill": "💥",
    "fuse": "⚡",
    "sync": "📡",
    "enter": "☢️",
    "proceed": "💀",
}

# ══════════════════════════════════════════════════════════════════════════════
# UTILITY BUTTONS
# ══════════════════════════════════════════════════════════════════════════════
UTILITY = {
    "inspect": "🔍",
    "details": "📖",
    "track": "📍",
    "sell": "💰",
    "store": "📦",
    "use": "💊",
}

# ══════════════════════════════════════════════════════════════════════════════
# MASTER LOOKUP FUNCTION
# ══════════════════════════════════════════════════════════════════════════════
def get_icon(key: str, default: str = "✨") -> str:
    """
    Get an icon by key from any category.
    
    Usage:
        get_icon("health")      → "❤️"
        get_icon("scavenge")    → "🧭"
        get_icon("caps")        → "🪙"
        get_icon("unknown_key") → "✨"
    
    Args:
        key: Icon key (lowercase, with underscores)
        default: Fallback emoji if key not found
    
    Returns:
        The emoji for the key, or default if not found
    """
    all_icons = {
        **SURVIVAL,
        **STATS,
        **RESOURCES,
        **SYSTEMS,
        **STATUS,
        **NAVIGATION,
        **ACTION_BUTTONS,
        **COMBAT,
        **UTILITY,
    }
    return all_icons.get(key.lower(), default)


def format_stat_line(stat_name: str, value: int, stat_type: str = "stat") -> str:
    """
    Format a stat line consistently.
    
    Usage:
        format_stat_line("STR", 8)  → "[💪] STR 8"
    
    Args:
        stat_name: Stat name or shorthand (e.g., "STR", "strength")
        value: Stat value
        stat_type: Type of stat ("stat", "skill", etc.)
    
    Returns:
        Formatted stat line
    """
    if stat_name.upper() in STAT_SHORT:
        icon = STAT_SHORT[stat_name.upper()]
        short = stat_name.upper()
    else:
        icon = get_icon(stat_name, "✨")
        short = stat_name.upper()
    
    return f"[{icon}] {short} {value}"


def format_resource_line(resource_name: str, quantity: int) -> str:
    """
    Format a resource line consistently.
    
    Usage:
        format_resource_line("caps", 150)  → "🪙 Caps: 150"
    
    Args:
        resource_name: Resource name (e.g., "caps", "scrap")
        quantity: Quantity
    
    Returns:
        Formatted resource line
    """
    icon = get_icon(resource_name, "✨")
    label = resource_name.capitalize()
    return f"{icon} {label}: {quantity}"


def format_status_bar(label: str, current: int, max_val: int, size: int = 10) -> str:
    """
    Format a status bar consistently.
    
    Usage:
        format_status_bar("Health", 80, 100)  → "❤️ Health [████████░░] 80%"
    
    Args:
        label: Status label (e.g., "Health", "Hunger")
        current: Current value
        max_val: Maximum value
        size: Bar length
    
    Returns:
        Formatted status bar
    """
    icon = get_icon(label.lower(), "✨")
    if max_val <= 0:
        percentage = 0
        filled = 0
    else:
        percentage = int((current / max_val) * 100)
        filled = int((current / max_val) * size)
        filled = max(0, min(size, filled))
    
    empty = size - filled
    bar = "█" * filled + "░" * empty
    return f"{icon} {label.capitalize():10} [{bar}] {percentage}%"


def format_section_header(section_name: str) -> str:
    """
    Format a section header consistently.
    
    Usage:
        format_section_header("stats") → "📊 STATS"
    
    Args:
        section_name: Section name
    
    Returns:
        Formatted section header
    """
    icon = get_icon(section_name, "✨")
    return f"{icon} {section_name.upper()}"


# ══════════════════════════════════════════════════════════════════════════════
# PRESET ICON GROUPINGS FOR UI BUILDING
# ══════════════════════════════════════════════════════════════════════════════

# All stat icons in order
STAT_ICONS_ORDERED = [
    STAT_SHORT["STR"],
    STAT_SHORT["AGI"],
    STAT_SHORT["INT"],
    STAT_SHORT["END"],
    STAT_SHORT["LCK"],
]

# Root navigation buttons (8 core actions)
ROOT_NAV_BUTTONS = [
    (SYSTEMS["scavenge"], "Scavenge"),
    (SYSTEMS["inventory"], "Inventory"),
    (SYSTEMS["craft"], "Craft"),
    (SYSTEMS["shelter"], "Shelter"),
    (SYSTEMS["network"], "Network"),
    (SYSTEMS["contracts"], "Contracts"),
    (SYSTEMS["map"], "Map"),
    (SYSTEMS["story"], "Story"),
]

# Resource icons for inventory display
RESOURCE_ICONS_ORDERED = [
    (RESOURCES["caps"], "Caps"),
    (RESOURCES["scrap"], "Scrap"),
    (RESOURCES["food"], "Food"),
    (RESOURCES["water"], "Water"),
    (RESOURCES["meds"], "Meds"),
    (RESOURCES["cloth"], "Cloth"),
    (RESOURCES["wire"], "Wire"),
]
