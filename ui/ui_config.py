"""
UI CONFIGURATION FOR NEON WASTES

Centralized configuration for all UI/UX elements:
  - Panel dimensions and styling
  - Color scheme (Discord embed colors)
  - Button styles
  - Navigation structure
  - Text formatting rules
"""

import discord

# ══════════════════════════════════════════════════════════════════════════════
# PANEL DIMENSIONS
# ══════════════════════════════════════════════════════════════════════════════

PANEL_WIDTH = 50  # Standard panel width in characters
PANEL_COMPACT_WIDTH = 40  # Compact panel width
PANEL_WIDE_WIDTH = 60  # Wide panel width (for complex layouts)

# ══════════════════════════════════════════════════════════════════════════════
# DISCORD EMBED COLORS (Neon Wastes theme)
# ══════════════════════════════════════════════════════════════════════════════

COLORS = {
    # Primary UI
    "primary": 0x00FF9F,        # Neon green
    "secondary": 0xFF006E,      # Neon pink/magenta
    "accent": 0x00D9FF,         # Neon cyan
    
    # Status
    "success": 0x00FF41,        # Green - positive
    "warning": 0xFFB700,        # Orange - caution
    "danger": 0xFF0055,         # Red - critical
    "info": 0x00D9FF,           # Cyan - information
    
    # Rarity
    "common": 0x808080,         # Gray
    "uncommon": 0x00FF41,       # Green
    "rare": 0x0099FF,           # Blue
    "epic": 0xFF00FF,           # Magenta
    "legendary": 0xFFFF00,      # Yellow
    "mythic": 0xFF6600,         # Orange
    
    # Radiation & Anomalies
    "radiation": 0x90EE90,      # Light green (radioactive feel)
    "anomaly": 0xFF00FF,        # Magenta
    "contamination": 0x00FF00,  # Bright green
    
    # UI Panels
    "panel_bg": 0x0A0E27,       # Dark blue (Discord dark mode)
    "panel_header": 0x1A1E3F,   # Slightly lighter
}

# ══════════════════════════════════════════════════════════════════════════════
# ROOT NAVIGATION (8 core buttons - appears on most screens)
# ══════════════════════════════════════════════════════════════════════════════

ROOT_NAVIGATION = [
    {
        "label": "🧭 Scavenge",
        "custom_id": "nav_scavenge",
        "style": discord.ButtonStyle.primary,
        "emoji": "🧭",
        "action": "scavenge",
    },
    {
        "label": "🎒 Inventory",
        "custom_id": "nav_inventory",
        "style": discord.ButtonStyle.primary,
        "emoji": "🎒",
        "action": "inventory",
    },
    {
        "label": "⚒️ Craft",
        "custom_id": "nav_craft",
        "style": discord.ButtonStyle.primary,
        "emoji": "⚒️",
        "action": "craft",
    },
    {
        "label": "🏚️ Shelter",
        "custom_id": "nav_shelter",
        "style": discord.ButtonStyle.primary,
        "emoji": "🏚️",
        "action": "shelter",
    },
    {
        "label": "📡 Network",
        "custom_id": "nav_network",
        "style": discord.ButtonStyle.primary,
        "emoji": "📡",
        "action": "network",
    },
    {
        "label": "📜 Contracts",
        "custom_id": "nav_contracts",
        "style": discord.ButtonStyle.primary,
        "emoji": "📜",
        "action": "contracts",
    },
    {
        "label": "🗺️ Map",
        "custom_id": "nav_map",
        "style": discord.ButtonStyle.primary,
        "emoji": "🗺️",
        "action": "map",
    },
    {
        "label": "📖 Story",
        "custom_id": "nav_story",
        "style": discord.ButtonStyle.primary,
        "emoji": "📖",
        "action": "story",
    },
]

# ══════════════════════════════════════════════════════════════════════════════
# NAVIGATION BUTTONS (Back, Profile, etc)
# ══════════════════════════════════════════════════════════════════════════════

NAVIGATION_BUTTONS = {
    "back": {
        "label": "↩️ Back",
        "emoji": "↩️",
        "style": discord.ButtonStyle.secondary,
    },
    "profile": {
        "label": "🏠 Profile",
        "emoji": "🏠",
        "style": discord.ButtonStyle.primary,
    },
    "refresh": {
        "label": "🔄 Refresh",
        "emoji": "🔄",
        "style": discord.ButtonStyle.secondary,
    },
    "next": {
        "label": "➡️ Next",
        "emoji": "➡️",
        "style": discord.ButtonStyle.secondary,
    },
    "prev": {
        "label": "⬅️ Previous",
        "emoji": "⬅️",
        "style": discord.ButtonStyle.secondary,
    },
}

# ══════════════════════════════════════════════════════════════════════════════
# ACTION BUTTONS (Combat, Interaction, etc)
# ══════════════════════════════════════════════════════════════════════════════

ACTION_BUTTONS = {
    "fight": {
        "label": "⚔️ Fight",
        "emoji": "⚔️",
        "style": discord.ButtonStyle.danger,
    },
    "skill": {
        "label": "💥 Skill",
        "emoji": "💥",
        "style": discord.ButtonStyle.primary,
    },
    "fuse": {
        "label": "⚡ Fuse",
        "emoji": "⚡",
        "style": discord.ButtonStyle.primary,
    },
    "sync": {
        "label": "📡 Sync",
        "emoji": "📡",
        "style": discord.ButtonStyle.primary,
    },
    "enter": {
        "label": "☢️ Enter",
        "emoji": "☢️",
        "style": discord.ButtonStyle.danger,
    },
    "proceed": {
        "label": "💀 Proceed",
        "emoji": "💀",
        "style": discord.ButtonStyle.danger,
    },
    "inspect": {
        "label": "🔍 Inspect",
        "emoji": "🔍",
        "style": discord.ButtonStyle.secondary,
    },
    "details": {
        "label": "📖 Details",
        "emoji": "📖",
        "style": discord.ButtonStyle.secondary,
    },
}

# ══════════════════════════════════════════════════════════════════════════════
# TEXT FORMATTING RULES
# ══════════════════════════════════════════════════════════════════════════════

TEXT_RULES = {
    "style": "terminal",  # terminal, atmospheric, narrative
    "tone": ["short", "sharp", "atmospheric"],
    "avoid": ["verbose", "comedic-heavy", "debug-text", "over-explaining"],
    "max_line_length": 48,  # For panel formatting
    "section_limit": "2-5 lines",  # Per section
}

# ══════════════════════════════════════════════════════════════════════════════
# SECTION HEADER MAPPING
# ══════════════════════════════════════════════════════════════════════════════

SECTION_HEADERS = {
    "stats": ("📊", "STATS"),
    "profile": ("👤", "PROFILE"),
    "loadout": ("🎒", "LOADOUT"),
    "resources": ("💰", "RESOURCES"),
    "status": ("⚠️", "STATUS"),
    "signal_data": ("📡", "SIGNAL DATA"),
    "contracts": ("📜", "CONTRACTS"),
    "inventory": ("🎒", "INVENTORY"),
    "equipment": ("🛠️", "EQUIPMENT"),
    "anomalies": ("🧪", "ANOMALIES"),
    "effects": ("✨", "EFFECTS"),
    "danger": ("⚠️", "DANGER"),
}

# ══════════════════════════════════════════════════════════════════════════════
# RARITY DEFINITIONS
# ══════════════════════════════════════════════════════════════════════════════

RARITIES = {
    "Common": {
        "emoji": "⬜",
        "color": COLORS["common"],
        "drop_weight": 50,
    },
    "Uncommon": {
        "emoji": "🟩",
        "color": COLORS["uncommon"],
        "drop_weight": 30,
    },
    "Rare": {
        "emoji": "🟦",
        "color": COLORS["rare"],
        "drop_weight": 12,
    },
    "Epic": {
        "emoji": "🟪",
        "color": COLORS["epic"],
        "drop_weight": 6,
    },
    "Legendary": {
        "emoji": "🟨",
        "color": COLORS["legendary"],
        "drop_weight": 1.5,
    },
    "Mythic": {
        "emoji": "🟧",
        "color": COLORS["mythic"],
        "drop_weight": 0.5,
    },
}

# ══════════════════════════════════════════════════════════════════════════════
# DANGER LEVELS
# ══════════════════════════════════════════════════════════════════════════════

DANGER_LEVELS = {
    "Low": {
        "emoji": "🟢",
        "color": COLORS["success"],
        "description": "Safe for beginners",
    },
    "Medium": {
        "emoji": "🟡",
        "color": COLORS["warning"],
        "description": "Some risk involved",
    },
    "High": {
        "emoji": "🟠",
        "color": COLORS["danger"],
        "description": "Experienced scavengers only",
    },
    "Extreme": {
        "emoji": "🔴",
        "color": 0xFF0000,
        "description": "For the desperate or foolish",
    },
}

# ══════════════════════════════════════════════════════════════════════════════
# TIMEOUTS
# ══════════════════════════════════════════════════════════════════════════════

TIMEOUTS = {
    "button_default": 300,          # 5 minutes
    "button_short": 120,            # 2 minutes
    "button_long": 600,             # 10 minutes
    "modal_default": 600,           # 10 minutes
    "embed_refresh_min": 30,        # Minimum refresh interval
}

# ══════════════════════════════════════════════════════════════════════════════
# PAGINATION
# ══════════════════════════════════════════════════════════════════════════════

PAGINATION = {
    "items_per_page": 5,
    "max_pages": 20,
    "show_page_counter": True,
}

# ══════════════════════════════════════════════════════════════════════════════
# CONFIRMATION SETTINGS
# ══════════════════════════════════════════════════════════════════════════════

CONFIRMATION = {
    "require_confirm": True,
    "timeout": 60,
    "ephemeral": True,
}

# ══════════════════════════════════════════════════════════════════════════════
# ERROR MESSAGES
# ══════════════════════════════════════════════════════════════════════════════

ERROR_MESSAGES = {
    "not_owner": "This interface isn't yours.",
    "not_found": "That item or zone doesn't exist.",
    "insufficient_resources": "Not enough resources.",
    "insufficient_level": "You're not experienced enough yet.",
    "on_cooldown": "You need to wait before doing that again.",
    "already_active": "An action is already in progress.",
    "permission_denied": "You don't have access to that.",
    "server_error": "Something went wrong. Try again later.",
}

# ══════════════════════════════════════════════════════════════════════════════
# SUCCESS MESSAGES
# ══════════════════════════════════════════════════════════════════════════════

SUCCESS_MESSAGES = {
    "action_complete": "✨ Done!",
    "item_acquired": "🎁 Item acquired!",
    "level_up": "⬆️ You leveled up!",
    "new_zone": "🔓 New zone unlocked!",
    "contract_accepted": "📜 Contract accepted!",
}

# ══════════════════════════════════════════════════════════════════════════════
# PROGRESS BARS
# ══════════════════════════════════════════════════════════════════════════════

PROGRESS_BAR = {
    "filled": "█",
    "empty": "░",
    "default_length": 10,
}

# ══════════════════════════════════════════════════════════════════════════════
# ANIMATION / VISUAL EFFECTS
# ══════════════════════════════════════════════════════════════════════════════

VISUAL_EFFECTS = {
    "loading": ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
    "shimmer": ["✨", "🌟", "⭐"],
    "alert": ["⚠️", "🚨"],
}
