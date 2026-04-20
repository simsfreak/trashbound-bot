"""
Dynamic Quest Generation System

Generates unlimited, varied quests using templates and randomization.
Supports difficulty scaling, zone affinity, and immersive flavor text.
"""

import random
from datetime import datetime, timedelta
from typing import Optional

# ==================== QUEST TEMPLATE DEFINITIONS ====================

QUEST_TEMPLATES = {
    # ========== EXPLORATION QUESTS ==========
    "scavenger_hunt": {
        "id": "scavenger_hunt",
        "name_template": "Scavenger Hunt: {rarity_name}",
        "description_template": "Find {item_count} {rarity_name} items.",
        "objective_type": "find_items",
        "default_difficulty": 2,
        "flavor_texts": [
            "The alley's got good vibes today. Time to hunt.",
            "Someone said there's treasure buried in the trash. Go find it.",
            "Your nose tingles. That means loot nearby.",
            "The dumpsters are calling. Answer them.",
            "Fresh finds await the bold scrapper.",
        ],
        "min_difficulty": 1,
        "max_difficulty": 5,
    },
    
    "treasure_dive": {
        "id": "treasure_dive",
        "name_template": "Treasure Dive ({zone_name})",
        "description_template": "Complete {dive_count} dive(s) and return with treasure.",
        "objective_type": "dive_count",
        "default_difficulty": 2,
        "flavor_texts": [
            "The zone's calling. Dive deep and come back richer.",
            "One person's trash, your wealth. Now go get it.",
            "Legends say the best finds happen at {time}. Prove them right.",
            "Your tools are ready. The zone awaits.",
            "Big dives, bigger rewards. You know the drill.",
        ],
        "min_difficulty": 1,
        "max_difficulty": 4,
    },
    
    # ========== LUCK-BASED QUESTS ==========
    "lucky_draw": {
        "id": "lucky_draw",
        "name_template": "Lucky Draw: {draw_count} Spins",
        "description_template": "Use the Dirty Draw {draw_count} time(s).",
        "objective_type": "dirty_draw_count",
        "default_difficulty": 3,
        "flavor_texts": [
            "The bench glows. The balls sing. Your luck awaits.",
            "Sometimes you gotta trust the chaos. Go spin.",
            "Those tickets won't use themselves.",
            "The draws are extra chaotic today. Perfect.",
            "Feeling lucky? The bench has ideas for you.",
        ],
        "min_difficulty": 2,
        "max_difficulty": 4,
    },
    
    # ========== EXCHANGE QUESTS ==========
    "zone_exchange": {
        "id": "zone_exchange",
        "name_template": "Zone Swap: {source_zone} → {dest_zone}",
        "description_template": "Collect items from {source_zone} and exchange them in {dest_zone}.",
        "objective_type": "zone_exchange",
        "default_difficulty": 3,
        "flavor_texts": [
            "Time to broker a deal. Zone to zone hustle.",
            "The trade routes are open. Make your move.",
            "Different zones want different trash. You're the middleman.",
            "This exchange is gonna be profitable.",
            "Supply meets demand. You're the connector.",
        ],
        "min_difficulty": 2,
        "max_difficulty": 5,
    },
    
    # ========== EQUIPMENT QUESTS ==========
    "gear_quest": {
        "id": "gear_quest",
        "name_template": "Gear Up: Find {gear_type}",
        "description_template": "Equip or acquire {item_count} piece(s) of {gear_type} equipment.",
        "objective_type": "equip_gear",
        "default_difficulty": 2,
        "flavor_texts": [
            "You're looking rough. Time for an upgrade.",
            "The trashosphere favors the well-equipped.",
            "Better gear = better finds. Go suit up.",
            "Your current loadout is... suboptimal.",
            "Fashion in the filth. Armor up.",
        ],
        "min_difficulty": 1,
        "max_difficulty": 3,
    },
    
    # ========== PAWN SHOP QUESTS ==========
    "pawn_master": {
        "id": "pawn_master",
        "name_template": "Pawn Master: Move {item_count} Items",
        "description_template": "Pawn {item_count} items to build your reputation.",
        "objective_type": "pawn_count",
        "default_difficulty": 2,
        "flavor_texts": [
            "The pawnbroker's got time. Bring them something good.",
            "Every transaction counts. Stack those profits.",
            "Money moves. Time to hustle.",
            "The vault's waiting for your contributions.",
            "Wealth builds one pawn at a time.",
        ],
        "min_difficulty": 1,
        "max_difficulty": 4,
    },
    
    # ========== RARE FIND QUESTS ==========
    "epic_hunter": {
        "id": "epic_hunter",
        "name_template": "Epic Hunter: Find {rarity_name} Items",
        "description_template": "Hunt down {item_count} {rarity_name}+ item(s).",
        "objective_type": "find_rarity",
        "default_difficulty": 4,
        "flavor_texts": [
            "The legends speak of items beyond common. Find them.",
            "Rare treasures hide in rare places. Go looking.",
            "Your collection needs some prestige.",
            "Only the best scrappers find what you're after.",
            "This hunt will separate you from amateurs.",
        ],
        "min_difficulty": 3,
        "max_difficulty": 5,
    },
    
    # ========== MIXED/SPECIAL QUESTS ==========
    "multi_task": {
        "id": "multi_task",
        "name_template": "Hustler's Mix",
        "description_template": "Complete {dive_count} dive(s), pawn {pawn_count} item(s), and earn {coin_target} coins.",
        "objective_type": "multi_objective",
        "default_difficulty": 4,
        "flavor_texts": [
            "A real hustler handles all angles. Show me you got range.",
            "Dives, deals, and dollars. All three.",
            "The streets respect those who juggle.",
            "Versatility is wealth. Prove you've got it.",
            "Master of many. That's what we need.",
        ],
        "min_difficulty": 2,
        "max_difficulty": 5,
    },
}

# ==================== DIFFICULTY CONFIGURATIONS ====================

DIFFICULTY_SCALING = {
    1: {  # Easy
        "hearts": "♥♡♡♡♡",
        "item_count_multiplier": 0.5,
        "action_multiplier": 0.6,
        "coin_reward_base": 150,
        "ticket_reward_base": 0,
        "description_suffix": "— Nice and easy.",
    },
    2: {  # Medium-Easy
        "hearts": "♥♥♡♡♡",
        "item_count_multiplier": 0.75,
        "action_multiplier": 0.8,
        "coin_reward_base": 200,
        "ticket_reward_base": 0,
        "description_suffix": "— Standard fare.",
    },
    3: {  # Medium
        "hearts": "♥♥♥♡♡",
        "item_count_multiplier": 1.0,
        "action_multiplier": 1.0,
        "coin_reward_base": 300,
        "ticket_reward_base": 1,
        "description_suffix": "— Fair challenge.",
    },
    4: {  # Hard
        "hearts": "♥♥♥♥♡",
        "item_count_multiplier": 1.5,
        "action_multiplier": 1.5,
        "coin_reward_base": 450,
        "ticket_reward_base": 1,
        "description_suffix": "— Toughened up.",
    },
    5: {  # Extreme
        "hearts": "♥♥♥♥♥",
        "item_count_multiplier": 2.0,
        "action_multiplier": 2.0,
        "coin_reward_base": 600,
        "ticket_reward_base": 2,
        "description_suffix": "— Legends only.",
    },
}

# ==================== REWARD CONFIGURATIONS ====================

RARITY_TIERS = {
    "Common": {"weight": 40, "emoji": "⚪", "difficulty_offset": -1},
    "Uncommon": {"weight": 30, "emoji": "🟢", "difficulty_offset": 0},
    "Rare": {"weight": 20, "emoji": "🔵", "difficulty_offset": 1},
    "Epic": {"weight": 8, "emoji": "🟣", "difficulty_offset": 2},
    "Legendary": {"weight": 2, "emoji": "🟡", "difficulty_offset": 3},
}

TIME_PERIODS = {
    "morning": {"emoji": "🌅", "mood": "Fresh and promising"},
    "evening": {"emoji": "🌆", "mood": "Deals and hustles"},
    "night": {"emoji": "🌙", "mood": "Chaos and big rewards"},
}

GEAR_TYPES = ["Gloves", "Boots", "Vest", "Visor", "Accessory", "Full Rig"]

DIFFICULTY_SCALING = {
    1: {
        "hearts": "♥♡♡♡♡",
        "item_count_multiplier": 0.8,
        "coin_reward_base": 100,
        "ticket_reward_base": 0,
        "description_suffix": "— A warm-up.",
    },
    2: {
        "hearts": "♥♥♡♡♡",
        "item_count_multiplier": 1.0,
        "coin_reward_base": 150,
        "ticket_reward_base": 0,
        "description_suffix": "— Standard fare.",
    },
    3: {
        "hearts": "♥♥♥♡♡",
        "item_count_multiplier": 1.2,
        "coin_reward_base": 200,
        "ticket_reward_base": 1,
        "description_suffix": "— A fair challenge.",
    },
    4: {
        "hearts": "♥♥♥♥♡",
        "item_count_multiplier": 1.5,
        "coin_reward_base": 300,
        "ticket_reward_base": 1,
        "description_suffix": "— For the bold.",
    },
    5: {
        "hearts": "♥♥♥♥♥",
        "item_count_multiplier": 2.0,
        "coin_reward_base": 500,
        "ticket_reward_base": 2,
        "description_suffix": "— Legends only.",
    },
}

# ==================== QUEST GENERATION FUNCTIONS ====================

def generate_random_quests(count: int = 3, difficulty_range: tuple = (1, 5)) -> list[dict]:
    """
    Generate random quests with varied templates and difficulty.
    
    Args:
        count: Number of quests to generate (default 3-5)
        difficulty_range: (min, max) difficulty range
    
    Returns:
        List of generated quest dictionaries
    """
    quests = []
    for _ in range(count):
        quest = generate_single_quest(difficulty_range)
        quests.append(quest)
    return quests


def generate_single_quest(difficulty_range: tuple = (1, 5)) -> dict:
    """
    Generate a single randomized quest.
    
    Combines:
    - Template (from QUEST_TEMPLATES)
    - Difficulty (1-5)
    - Zone affinity
    - Time of day
    - Flavor text
    - Calculated rewards
    """
    from game.data import ZONES
    
    # Pick random template
    template = random.choice(list(QUEST_TEMPLATES.values()))
    
    # Pick random difficulty within range and template bounds
    min_diff = max(template["min_difficulty"], difficulty_range[0])
    max_diff = min(template["max_difficulty"], difficulty_range[1])
    difficulty = random.randint(min_diff, max_diff)
    
    # Pick random zone and time
    zone_id = random.choice(list(ZONES.keys()))
    zone = ZONES[zone_id]
    time_period = random.choice(list(TIME_PERIODS.keys()))
    
    # Generate flavor text
    flavor_text = _generate_flavor_text(template, zone, time_period)
    
    # Generate quest data based on template type
    quest_data = _generate_objective_data(template, zone_id, difficulty)
    
    # Calculate rewards
    rewards = _calculate_rewards(template, difficulty)
    
    # Combine into quest object
    quest = {
        "quest_id": _generate_quest_id(),
        "template_id": template["id"],
        "name": quest_data["name"],
        "description": quest_data["description"],
        "objective_type": template["objective_type"],
        "zone_id": zone_id,
        "zone_name": zone["name"],
        "time": time_period,
        "difficulty": difficulty,
        "hearts": DIFFICULTY_SCALING[difficulty]["hearts"],
        "flavor_text": flavor_text,
        "progress": 0,
        "target": quest_data.get("target", 1),
        "reward_coins": rewards["coins"],
        "reward_tickets": rewards["tickets"],
        "objective_meta": quest_data.get("meta", {}),
        "generated_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(hours=24),
    }
    
    return quest


def _generate_quest_id() -> str:
    """Generate a unique quest ID."""
    import uuid
    return str(uuid.uuid4())


def _generate_flavor_text(template: dict, zone: dict, time_period: str) -> str:
    """
    Generate expressive flavor text by combining template and context.
    """
    base_flavor = random.choice(template["flavor_texts"])
    
    # Format with available context
    formatted = base_flavor.format(
        zone_name=zone.get("name", "the alley"),
        time=time_period,
        zone_emoji=zone.get("banner", "").split()[0] if zone.get("banner") else "🗑️",
        mood=TIME_PERIODS[time_period]["mood"],
    )
    
    # Add time/zone context emoji
    return f"{TIME_PERIODS[time_period]['emoji']} {formatted}"


def _generate_objective_data(template: dict, zone_id: str, difficulty: int) -> dict:
    """
    Generate quest-specific objective data based on template and difficulty.
    """
    from game.data import ZONES
    
    difficulty_config = DIFFICULTY_SCALING[difficulty]
    objective_type = template["objective_type"]
    
    if objective_type == "find_items":
        rarity = _pick_rarity_for_difficulty(difficulty)
        item_count = max(1, int(3 * difficulty_config["item_count_multiplier"]))
        return {
            "name": template["name_template"].format(rarity_name=rarity),
            "description": template["description_template"].format(item_count=item_count, rarity_name=rarity) 
                          + f" {difficulty_config['description_suffix']}",
            "target": item_count,
            "meta": {"rarity": rarity, "item_count": item_count},
        }
    
    elif objective_type == "dive_count":
        dive_count = max(1, int(2 + difficulty))
        zone = ZONES.get(zone_id, {})
        return {
            "name": template["name_template"].format(zone_name=zone.get("name", zone_id)),
            "description": template["description_template"].format(dive_count=dive_count)
                          + f" {difficulty_config['description_suffix']}",
            "target": dive_count,
            "meta": {"dive_count": dive_count},
        }
    
    elif objective_type == "dirty_draw_count":
        draw_count = max(1, int(1 + difficulty * 0.5))
        return {
            "name": template["name_template"].format(draw_count=draw_count),
            "description": template["description_template"].format(draw_count=draw_count)
                          + f" {difficulty_config['description_suffix']}",
            "target": draw_count,
            "meta": {"draw_count": draw_count},
        }
    
    elif objective_type == "zone_exchange":
        source_zone = zone_id
        all_zones = list(ZONES.keys())
        all_zones.remove(source_zone)
        dest_zone = random.choice(all_zones)
        item_count = max(1, int(2 + difficulty * 0.5))
        
        source_name = ZONES[source_zone]["name"]
        dest_name = ZONES[dest_zone]["name"]
        
        return {
            "name": template["name_template"].format(source_zone=source_name, dest_zone=dest_name),
            "description": template["description_template"].format(source_zone=source_name, dest_zone=dest_name)
                          + f" {difficulty_config['description_suffix']}",
            "target": item_count,
            "meta": {"source_zone": source_zone, "dest_zone": dest_zone, "item_count": item_count},
        }
    
    elif objective_type == "equip_gear":
        gear_type = random.choice(GEAR_TYPES)
        item_count = max(1, int(1 + difficulty * 0.5))
        return {
            "name": template["name_template"].format(gear_type=gear_type),
            "description": template["description_template"].format(item_count=item_count, gear_type=gear_type)
                          + f" {difficulty_config['description_suffix']}",
            "target": item_count,
            "meta": {"gear_type": gear_type, "item_count": item_count},
        }
    
    elif objective_type == "pawn_count":
        pawn_count = max(1, int(2 + difficulty * 0.5))
        return {
            "name": template["name_template"].format(item_count=pawn_count),
            "description": template["description_template"].format(item_count=pawn_count)
                          + f" {difficulty_config['description_suffix']}",
            "target": pawn_count,
            "meta": {"pawn_count": pawn_count},
        }
    
    elif objective_type == "find_rarity":
        rarity = _pick_rarity_for_difficulty(difficulty + 1)  # Higher rarity for epic hunters
        item_count = max(1, int(1 + difficulty * 0.5))
        return {
            "name": template["name_template"].format(rarity_name=rarity),
            "description": template["description_template"].format(item_count=item_count, rarity_name=rarity)
                          + f" {difficulty_config['description_suffix']}",
            "target": item_count,
            "meta": {"rarity": rarity, "item_count": item_count},
        }
    
    elif objective_type == "multi_objective":
        dive_count = max(1, int(2 + difficulty * 0.3))
        pawn_count = max(1, int(1 + difficulty * 0.5))
        coin_target = int(200 + difficulty * 100)
        return {
            "name": template["name_template"],
            "description": template["description_template"].format(
                dive_count=dive_count,
                pawn_count=pawn_count,
                coin_target=coin_target
            ) + f" {difficulty_config['description_suffix']}",
            "target": dive_count + pawn_count,  # Combined target
            "meta": {
                "dive_count": dive_count,
                "pawn_count": pawn_count,
                "coin_target": coin_target,
            },
        }
    
    # Fallback
    return {
        "name": "Unknown Quest",
        "description": "A mysterious objective awaits.",
        "target": 1,
        "meta": {},
    }


def _pick_rarity_for_difficulty(difficulty: int) -> str:
    """
    Pick a rarity tier based on difficulty.
    Higher difficulty has better chances for rare items.
    """
    # Create weighted pool based on difficulty
    weights = {}
    for rarity, config in RARITY_TIERS.items():
        # Adjust weight based on difficulty offset
        adjusted_weight = config["weight"] * (1 + config["difficulty_offset"] * (difficulty - 3) * 0.2)
        weights[rarity] = max(1, adjusted_weight)
    
    # Normalize weights
    total = sum(weights.values())
    weights = {k: v / total for k, v in weights.items()}
    
    return random.choices(list(weights.keys()), weights=list(weights.values()))[0]


def _calculate_rewards(template: dict, difficulty: int) -> dict:
    """
    Calculate quest rewards based on template and difficulty.
    """
    difficulty_config = DIFFICULTY_SCALING[difficulty]
    
    # Base rewards scaled by difficulty
    coins = int(difficulty_config["coin_reward_base"] * (1 + (difficulty - 1) * 0.15))
    tickets = difficulty_config["ticket_reward_base"]
    
    # Add some variance to make it feel less predictable
    coins = int(coins * random.uniform(0.9, 1.1))
    
    return {
        "coins": coins,
        "tickets": tickets,
    }


def regenerate_player_quests(user_id: int, count: int = 5) -> list[dict]:
    """
    Regenerate a fresh set of quests for a player.
    Stores them in the database for pagination.
    """
    from db import queries
    
    # Generate new quests
    quests = generate_random_quests(count=count)
    
    # Store them for the player
    for quest in quests:
        queries.store_generated_quest(user_id, quest)
    
    return quests


def get_next_quest_for_player(user_id: int) -> Optional[dict]:
    """
    Get the next unviewed quest for a player from their queue.
    """
    from db import queries
    
    return queries.get_next_generated_quest(user_id)


def accept_quest(user_id: int, quest_id: str) -> bool:
    """
    Accept a quest and set it as the player's active quest.
    """
    from db import queries
    
    return queries.set_active_quest(user_id, quest_id)


# ==================== ALIASES FOR COMPATIBILITY ====================

# Alias for views.py compatibility
generate_quest = generate_single_quest
