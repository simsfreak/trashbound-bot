"""
NEON WASTES GAME DATA EXTENSIONS

New structures and data for Neon Wastes theme.
This extends the existing game/data.py with:
  - Character stats system (STR, AGI, INT, END, LCK)
  - Resource pools (caps, scrap, food, water, meds, cloth, wire)
  - Survival metrics (health, hunger, thirst, radiation, energy)
  - Difficulty levels and risk assessment
  - Neon Wastes zone descriptions
  - Contract templates
  - Anomaly system
"""

# ══════════════════════════════════════════════════════════════════════════════
# CHARACTER STAT SYSTEM
# ══════════════════════════════════════════════════════════════════════════════

STATS = {
    "STR": {  # Strength - Melee damage, carry capacity
        "name": "Strength",
        "emoji": "💪",
        "description": "Raw power and melee capability",
        "base": 5,
        "max": 20,
    },
    "AGI": {  # Agility - Dodge chance, crit rate, scavenge speed
        "name": "Agility",
        "emoji": "🏃",
        "description": "Speed and precision",
        "base": 5,
        "max": 20,
    },
    "INT": {  # Intelligence - Crafting success, anomaly resistance
        "name": "Intelligence",
        "emoji": "🧠",
        "description": "Reasoning and technical aptitude",
        "base": 5,
        "max": 20,
    },
    "END": {  # Endurance - Health pool, radiation resistance
        "name": "Endurance",
        "emoji": "🛡️",
        "description": "Durability and survivability",
        "base": 5,
        "max": 20,
    },
    "LCK": {  # Luck - Rare drop chance, critical event odds
        "name": "Luck",
        "emoji": "🍀",
        "description": "Fortune and fate",
        "base": 5,
        "max": 20,
    },
}

# ══════════════════════════════════════════════════════════════════════════════
# SURVIVAL METRICS
# ══════════════════════════════════════════════════════════════════════════════

SURVIVAL_METRICS = {
    "health": {
        "emoji": "❤️",
        "name": "Health",
        "description": "Life points. Reaches 0 = incapacitated",
        "base": 100,
        "max_scale": 1.5,  # Per END
    },
    "hunger": {
        "emoji": "🍖",
        "name": "Hunger",
        "description": "Satisfaction. Drains during scavenging",
        "base": 100,
        "max_scale": 1.0,
    },
    "thirst": {
        "emoji": "💧",
        "name": "Thirst",
        "description": "Hydration. Drains faster in hot zones",
        "base": 100,
        "max_scale": 1.0,
    },
    "radiation": {
        "emoji": "☢️",
        "name": "Radiation",
        "description": "Contamination. High levels cause damage",
        "base": 0,
        "max_scale": 0.5,  # Per END resistance
    },
    "energy": {
        "emoji": "⚡",
        "name": "Energy",
        "description": "Stamina for actions",
        "base": 100,
        "max_scale": 1.0,
    },
}

# ══════════════════════════════════════════════════════════════════════════════
# RESOURCE TYPES (Inventory resources)
# ══════════════════════════════════════════════════════════════════════════════

RESOURCES = {
    "caps": {
        "emoji": "🪙",
        "name": "Caps",
        "description": "Universal currency",
        "category": "currency",
    },
    "scrap": {
        "emoji": "🔩",
        "name": "Scrap",
        "description": "Crafting material",
        "category": "material",
    },
    "food": {
        "emoji": "🥫",
        "name": "Food",
        "description": "Consumable - restores hunger",
        "category": "consumable",
    },
    "water": {
        "emoji": "🧴",
        "name": "Water",
        "description": "Consumable - restores thirst",
        "category": "consumable",
    },
    "meds": {
        "emoji": "💊",
        "name": "Meds",
        "description": "Consumable - restores health",
        "category": "consumable",
    },
    "cloth": {
        "emoji": "🧵",
        "name": "Cloth",
        "description": "Crafting material",
        "category": "material",
    },
    "wire": {
        "emoji": "🔌",
        "name": "Wire",
        "description": "Crafting material",
        "category": "material",
    },
}

# ══════════════════════════════════════════════════════════════════════════════
# DIFFICULTY LEVELS
# ══════════════════════════════════════════════════════════════════════════════

DIFFICULTY_LEVELS = {
    1: {
        "name": "Trivial",
        "hearts": "♥",
        "emoji": "🟢",
        "coin_multiplier": 0.5,
        "xp_multiplier": 0.5,
        "risk": "Low",
    },
    2: {
        "name": "Easy",
        "hearts": "♥♥",
        "emoji": "🟢",
        "coin_multiplier": 0.75,
        "xp_multiplier": 0.75,
        "risk": "Low",
    },
    3: {
        "name": "Moderate",
        "hearts": "♥♥♥",
        "emoji": "🟡",
        "coin_multiplier": 1.0,
        "xp_multiplier": 1.0,
        "risk": "Medium",
    },
    4: {
        "name": "Hard",
        "hearts": "♥♥♥♥",
        "emoji": "🟠",
        "coin_multiplier": 1.5,
        "xp_multiplier": 1.5,
        "risk": "High",
    },
    5: {
        "name": "Lethal",
        "hearts": "♥♥♥♥♥",
        "emoji": "🔴",
        "coin_multiplier": 2.0,
        "xp_multiplier": 2.0,
        "risk": "Extreme",
    },
}

# ══════════════════════════════════════════════════════════════════════════════
# NEON WASTES ZONES (Re-themed versions)
# ══════════════════════════════════════════════════════════════════════════════

NEON_ZONES = {
    "scrap_yard": {
        "name": "Scrap Yard",
        "emoji": "🗑️",
        "unlock_level": 1,
        "description": "Derelict industrial zone. Rusted metal and forgotten tech.",
        "danger": "Low",
        "resources": ["scrap", "wire"],
        "risk_icon": "🟢",
        "biome": "industrial",
        "radiation_baseline": 10,  # Base radiation
    },
    "ruins": {
        "name": "Urban Ruins",
        "emoji": "🏚️",
        "unlock_level": 3,
        "description": "Collapsed buildings and rubble. Signs of old civilization.",
        "danger": "Medium",
        "resources": ["scrap", "cloth", "food"],
        "risk_icon": "🟡",
        "biome": "urban",
        "radiation_baseline": 20,
    },
    "underground": {
        "name": "Underground Station",
        "emoji": "🚇",
        "unlock_level": 5,
        "description": "Deep tunnels. Bioluminescent fungi glow in the dark.",
        "danger": "Medium",
        "resources": ["water", "meds", "wire"],
        "risk_icon": "🟡",
        "biome": "underground",
        "radiation_baseline": 30,
    },
    "neon_district": {
        "name": "Neon District",
        "emoji": "💡",
        "unlock_level": 8,
        "description": "Abandoned entertainment hub. Signs still flicker with stolen power.",
        "danger": "High",
        "resources": ["cloth", "wire", "scrap"],
        "risk_icon": "🟠",
        "biome": "neon",
        "radiation_baseline": 50,
    },
    "exclusion_zone": {
        "name": "Exclusion Zone",
        "emoji": "☢️",
        "unlock_level": 12,
        "description": "Highly contaminated area. Only the desperate venture here.",
        "danger": "Extreme",
        "resources": ["rare_artifacts", "anomalies"],
        "risk_icon": "🔴",
        "biome": "wasteland",
        "radiation_baseline": 100,
    },
}

# ══════════════════════════════════════════════════════════════════════════════
# CONTRACT TEMPLATES
# ══════════════════════════════════════════════════════════════════════════════

CONTRACT_TEMPLATES = {
    "hunt_order": {
        "name": "Hunt Order",
        "emoji": "⚔️",
        "description": "Eliminate a target",
        "objective_type": "eliminate",
        "base_reward_coins": 50,
        "base_reward_xp": 75,
    },
    "retrieval": {
        "name": "Retrieval Job",
        "emoji": "📦",
        "description": "Fetch a specific item",
        "objective_type": "collect",
        "base_reward_coins": 40,
        "base_reward_xp": 60,
    },
    "survey": {
        "name": "Survey Contract",
        "emoji": "📍",
        "description": "Explore and map an area",
        "objective_type": "explore",
        "base_reward_coins": 30,
        "base_reward_xp": 50,
    },
    "escort": {
        "name": "Escort Mission",
        "emoji": "👥",
        "description": "Protect someone through a zone",
        "objective_type": "protect",
        "base_reward_coins": 60,
        "base_reward_xp": 90,
    },
    "sabotage": {
        "name": "Sabotage Op",
        "emoji": "💣",
        "description": "Disable or destroy a structure",
        "objective_type": "destroy",
        "base_reward_coins": 75,
        "base_reward_xp": 100,
    },
}

# ══════════════════════════════════════════════════════════════════════════════
# ANOMALY TYPES
# ══════════════════════════════════════════════════════════════════════════════

ANOMALIES = {
    "radiation_spike": {
        "name": "Radiation Spike",
        "emoji": "☢️",
        "description": "Sudden burst of radiation",
        "effect": "increases_radiation",
        "severity": "medium",
    },
    "temporal_distortion": {
        "name": "Temporal Distortion",
        "emoji": "🌀",
        "description": "Time behaves strangely here",
        "effect": "warps_perception",
        "severity": "high",
    },
    "electromagnetic_storm": {
        "name": "EM Storm",
        "emoji": "⚡",
        "description": "Electromagnetic fields go haywire",
        "effect": "corrupts_tech",
        "severity": "high",
    },
    "void_rupture": {
        "name": "Void Rupture",
        "emoji": "🌌",
        "description": "Reality tears at the seams",
        "effect": "damages_psyche",
        "severity": "extreme",
    },
    "signal_echo": {
        "name": "Signal Echo",
        "emoji": "📡",
        "description": "Strange transmissions from nowhere",
        "effect": "attracts_attention",
        "severity": "medium",
    },
}

# ══════════════════════════════════════════════════════════════════════════════
# PLAYER PROGRESSION TITLES
# ══════════════════════════════════════════════════════════════════════════════

PROGRESSION_TITLES = {
    1: "Scavenger",
    5: "Waste Walker",
    10: "Scrap Collector",
    15: "Neon Hunter",
    20: "Zone Master",
    25: "Anomaly Touched",
    30: "Wasteland Legend",
}

# ══════════════════════════════════════════════════════════════════════════════
# STATUS EFFECTS
# ══════════════════════════════════════════════════════════════════════════════

STATUS_EFFECTS = {
    "contaminated": {
        "emoji": "☢️",
        "name": "Contaminated",
        "description": "Radiation poisoning",
        "damage_per_tick": 2,
        "duration": 300,  # seconds
    },
    "exhausted": {
        "emoji": "😵",
        "name": "Exhausted",
        "description": "Reduced movement speed",
        "stat_reduction": {"AGI": 2},
        "duration": 300,
    },
    "energized": {
        "emoji": "⚡",
        "name": "Energized",
        "description": "Increased damage output",
        "stat_boost": {"STR": 2},
        "duration": 180,
    },
    "shielded": {
        "emoji": "🛡️",
        "name": "Shielded",
        "description": "Reduced incoming damage",
        "damage_reduction": 0.25,
        "duration": 240,
    },
}

# ══════════════════════════════════════════════════════════════════════════════
# TIME PHASES (Day/Night Cycle)
# ══════════════════════════════════════════════════════════════════════════════

TIME_PHASES = {
    "dawn": {
        "emoji": "🌅",
        "name": "Dawn",
        "hour_range": (5, 7),
        "loot_multiplier": 0.8,
        "danger_multiplier": 0.9,
        "description": "The wasteland awakens",
    },
    "day": {
        "emoji": "☀️",
        "name": "Day",
        "hour_range": (7, 17),
        "loot_multiplier": 1.0,
        "danger_multiplier": 1.0,
        "description": "Standard scavenging conditions",
    },
    "dusk": {
        "emoji": "🌆",
        "name": "Dusk",
        "hour_range": (17, 19),
        "loot_multiplier": 1.2,
        "danger_multiplier": 1.1,
        "description": "Things move in the shadows",
    },
    "night": {
        "emoji": "🌙",
        "name": "Night",
        "hour_range": (19, 5),
        "loot_multiplier": 1.5,
        "danger_multiplier": 1.5,
        "description": "The wasteland hunts",
    },
}

# ══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def get_stat_multiplier(difficulty: int, stat_name: str) -> float:
    """
    Get reward multiplier based on difficulty and stat.
    Higher difficulty = higher rewards but more risk.
    """
    if difficulty < 1:
        difficulty = 1
    if difficulty > 5:
        difficulty = 5
    
    return DIFFICULTY_LEVELS[difficulty]["coin_multiplier"]


def get_zone_radiation(zone_id: str) -> int:
    """Get baseline radiation for a zone."""
    zone = NEON_ZONES.get(zone_id, {})
    return zone.get("radiation_baseline", 0)


def get_zone_resources(zone_id: str) -> list:
    """Get available resources in a zone."""
    zone = NEON_ZONES.get(zone_id, {})
    return zone.get("resources", [])


def get_title_for_level(level: int) -> str:
    """Get player title based on level."""
    for required_level in sorted(PROGRESSION_TITLES.keys(), reverse=True):
        if level >= required_level:
            return PROGRESSION_TITLES[required_level]
    return PROGRESSION_TITLES[1]
