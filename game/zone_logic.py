# ═══════════════════════════════════════════════════════════════════
# ZONE ACTIVITY SYSTEM - HELPER FUNCTIONS FOR GAMEPLAY LOGIC
# ═══════════════════════════════════════════════════════════════════

import random
from datetime import datetime, timedelta
from game.zones import (
    ZONES_META, ZONE_COOLDOWNS, MISSION_QUANTITIES, roll_rarity, 
    roll_item_from_rarity, generate_mission, roll_bonus_encounter
)
from db import queries

# ═══════════════════════════════════════════════════════════════════
# STAGE MESSAGES - MULTI-STAGE MINI-GAME TEXT
# ═══════════════════════════════════════════════════════════════════

STAGE_MESSAGES = {
    "fishing": {
        "stage1": {  # Bite phase
            "messages": [
                "… something nibbles at the line...",
                "… the water ripples softly...",
                "… your line twitches a little...",
                "… hmm, something is testing the bait...",
                "… a shadow moves beneath the surface...",
            ]
        },
        "stage2": {  # Tension/Reel phase
            "messages": [
                "… it pulls hard against the reel!",
                "… this one feels slippery...",
                "… the line strains under pressure...",
                "… it's fighting back!",
                "… whatever this is, it's not small...",
            ]
        },
    },
    "botany": {
        "stage1": {  # Spot/Search phase
            "messages": [
                "… you brush aside thick leaves...",
                "… something glows between the weeds...",
                "… a scent rises from the roots...",
                "… you spot a strange stem in the brush...",
                "… the soil here feels different...",
            ]
        },
        "stage2": {  # Harvest phase
            "messages": [
                "… careful, the roots cling tightly...",
                "… the stem resists your pull...",
                "… pollen bursts into the air...",
                "… the plant twists strangely as you reach for it...",
                "… thorns catch at your gloves...",
            ]
        },
    },
    "archaeology": {
        "stage1": {  # Detect/Search phase
            "messages": [
                "… your tool hits something solid...",
                "… there's a buried shape beneath the dust...",
                "… the ground sounds hollow here...",
                "… a corner of something ancient peeks through...",
                "… this patch feels older than the rest...",
            ]
        },
        "stage2": {  # Extract phase
            "messages": [
                "… carefully, it could break...",
                "… the earth is packed tightly around it...",
                "… one wrong move might crack it...",
                "… something fragile is trapped below...",
                "… dust falls away from carved edges...",
            ]
        },
    },
    "scavenge": {
        "stage1": {  # Rummage/Search phase
            "messages": [
                "… you dig through the pile...",
                "… something clinks under the junk...",
                "… a shape catches your eye...",
                "… there's a useful-looking piece buried here...",
                "… the heap shifts as you search...",
            ]
        },
        "stage2": {  # Pull phase
            "messages": [
                "… it's stuck under heavier scrap...",
                "… the metal edges scrape as it comes loose...",
                "… the heap resists your pull...",
                "… something sharp almost catches your hand...",
                "… this piece is wedged in deep...",
            ]
        },
    },
}

FAILURE_MESSAGES = {
    "fishing": [
        "… it slipped off the hook!",
        "… the line goes slack...",
        "… whatever it was, it got away...",
    ],
    "botany": [
        "… the stem snapped before you could gather it...",
        "… the bloom wilted in your hands...",
        "… it recoiled back into the brush...",
    ],
    "archaeology": [
        "… it crumbled before extraction...",
        "… the relic cracked in the dirt...",
        "… you lost the shape in the dust...",
    ],
    "scavenge": [
        "… it slipped deeper into the heap...",
        "… the pile collapsed over it...",
        "… whatever it was, it's gone again...",
    ],
}

# ═══════════════════════════════════════════════════════════════════
# SUCCESS RATES BY RARITY & ZONE
# ═══════════════════════════════════════════════════════════════════

SUCCESS_RATES = {
    "fishing": {
        "Common": 0.92,
        "Rare": 0.80,
        "Exotic": 0.62,
        "Dangerous": 0.40,
    },
    "botany": {
        "Common": 0.94,
        "Rare": 0.84,
        "Exotic": 0.66,
        "Dangerous": 0.45,
    },
    "archaeology": {
        "Common": 0.90,
        "Rare": 0.78,
        "Exotic": 0.60,
        "Dangerous": 0.38,
    },
    "scavenge": {
        "Common": 0.95,
        "Rare": 0.85,
        "Exotic": 0.68,
        "Dangerous": 0.48,
    },
}

# ═══════════════════════════════════════════════════════════════════
# LUCK FACTOR CALCULATION
# ═══════════════════════════════════════════════════════════════════

def calculate_luck_factor(player_level: int) -> int:
    """Calculate luck factor based on player level."""
    # Scales from 0% at level 1 to +25% at level 100
    luck = min(25, (player_level - 1) // 4)
    return luck

def apply_luck_to_success(base_success: float, luck_factor: int) -> float:
    """Apply luck factor to success rate."""
    # Each +10% luck gives +3% success chance
    luck_bonus = (luck_factor / 10.0) * 0.03
    return min(1.0, base_success + luck_bonus)

# ═══════════════════════════════════════════════════════════════════
# STAGE SYSTEM - MULTI-STAGE MINI-GAME
# ═══════════════════════════════════════════════════════════════════

def get_stage_message(zone_id: str, stage: int) -> str:
    """Get a random stage message for the zone."""
    messages = STAGE_MESSAGES.get(zone_id, {})
    if stage == 1:
        stage_key = "stage1"
    elif stage == 2:
        stage_key = "stage2"
    else:
        return "…"
    
    stage_messages = messages.get(stage_key, {}).get("messages", ["…"])
    return random.choice(stage_messages)

def get_failure_message(zone_id: str) -> str:
    """Get a random failure message for the zone."""
    messages = FAILURE_MESSAGES.get(zone_id, ["The attempt failed..."])
    return random.choice(messages)

# ═══════════════════════════════════════════════════════════════════
# MINI-GAME SIMULATION
# ═══════════════════════════════════════════════════════════════════

async def simulate_zone_activity(
    user_id: int,
    zone_id: str,
) -> dict:
    """
    Simulate one zone activity attempt (e.g., Cast, Gather, Dig, Search).
    
    Returns:
        {
            "success": bool,
            "stage1_message": str,
            "stage2_message": str,
            "final_message": str,
            "item": dict or None,
            "rarity": str or None,
            "bonus": str or None,
        }
    """
    from db import queries as db_queries
    
    # Get zone event
    zone_event = db_queries.get_zone_event(user_id, zone_id)
    if not zone_event:
        return {"success": False, "error": "No active zone event"}
    
    # Roll rarity based on zone difficulty (default Medium)
    rarity = roll_rarity(zone_id, "Medium")
    
    # Get item from rarity pool
    item = roll_item_from_rarity(zone_id, rarity)
    
    # Calculate success chance
    base_success = SUCCESS_RATES.get(zone_id, {}).get(rarity, 0.5)
    player = db_queries.get_player(user_id)
    luck_factor = calculate_luck_factor(player.get("level", 1))
    final_success_rate = apply_luck_to_success(base_success, luck_factor)
    
    # Roll for success
    success = random.random() < final_success_rate
    
    # Get stage messages
    stage1_msg = get_stage_message(zone_id, 1)
    stage2_msg = get_stage_message(zone_id, 2)
    
    if success:
        final_msg = f"🎉 **{item.get('name', 'Item')}** acquired!"
    else:
        final_msg = get_failure_message(zone_id)
    
    # Check for bonus encounter
    bonus = roll_bonus_encounter() if success else None
    
    return {
        "success": success,
        "stage1_message": stage1_msg,
        "stage2_message": stage2_msg,
        "final_message": final_msg,
        "item": item if success else None,
        "rarity": rarity if success else None,
        "bonus": bonus,
    }

# ═══════════════════════════════════════════════════════════════════
# ZONE SESSION MANAGEMENT
# ═══════════════════════════════════════════════════════════════════

async def start_zone_session(user_id: int, zone_id: str, difficulty: str = "Medium"):
    """Start a new zone session (1 hour active, mission generated)."""
    from db import queries as db_queries
    
    mission = generate_mission(zone_id)
    
    db_queries.start_zone_event(
        user_id=user_id,
        zone_id=zone_id,
        mission_data=mission,
        difficulty=difficulty,
    )
    
    return mission

async def get_active_zone_session(user_id: int, zone_id: str) -> dict | None:
    """Get current active zone session and check if expired."""
    from db import queries as db_queries
    from datetime import datetime, timezone
    
    zone_event = db_queries.get_zone_event(user_id, zone_id)
    if not zone_event:
        return None
    
    # Check if expired (1 hour) using timer_end_at
    timer_end_at = zone_event["timer_end_at"]
    
    # Handle both string and datetime objects
    if isinstance(timer_end_at, str):
        timer_end = datetime.fromisoformat(timer_end_at.replace("Z", "+00:00"))
    else:
        # It's already a datetime object from psycopg
        timer_end = timer_end_at
        if timer_end.tzinfo is None:
            timer_end = timer_end.replace(tzinfo=timezone.utc)
    
    now = datetime.now(timezone.utc)
    time_remaining = (timer_end - now).total_seconds()
    
    if time_remaining <= 0:
        # Session expired
        zone_event["expired"] = True
        zone_event["time_remaining_sec"] = 0
    else:
        zone_event["expired"] = False
        zone_event["time_remaining_sec"] = int(time_remaining)
    
    return zone_event

async def complete_zone_session(user_id: int, zone_id: str) -> dict:
    """Complete a zone session and calculate rewards."""
    from db import queries as db_queries
    
    zone_event = db_queries.get_zone_event(user_id, zone_id)
    if not zone_event:
        return {"error": "No active zone event"}
    
    mission_complete = zone_event["mission_progress"] >= zone_event["mission_target_qty"]
    
    rewards = {
        "coins": 10000 if mission_complete else 1000,
        "xp": 1000 if mission_complete else 500,
        "mission_complete": mission_complete,
    }
    
    # Award coins and XP to player
    player = db_queries.get_player(user_id)
    db_queries.update_player_progress(
        user_id,
        coins=player["coins"] + rewards["coins"],
        xp=player["xp"] + rewards["xp"],
    )
    
    # Complete the zone event
    db_queries.complete_zone_event(user_id, zone_id)
    
    return rewards

# ═══════════════════════════════════════════════════════════════════
# COOLDOWN CHECKING
# ═══════════════════════════════════════════════════════════════════

async def check_zone_cooldown(user_id: int, zone_id: str) -> dict:
    """Check if zone has cooldown remaining."""
    from db import queries as db_queries
    
    last_action = db_queries.get_last_zone_action(user_id, zone_id)
    if not last_action:
        return {"on_cooldown": False, "remaining_sec": 0}
    
    last_action_at = datetime.fromisoformat(last_action.replace("Z", "+00:00"))
    now = datetime.utcnow().replace(tzinfo=last_action_at.tzinfo)
    elapsed = (now - last_action_at).total_seconds()
    
    cooldown = ZONE_COOLDOWNS.get(zone_id, 20)
    
    if elapsed < cooldown:
        remaining = int(cooldown - elapsed)
        return {"on_cooldown": True, "remaining_sec": remaining}
    
    return {"on_cooldown": False, "remaining_sec": 0}

async def record_zone_action(user_id: int, zone_id: str):
    """Record when player performed a zone action (for cooldown)."""
    from db import queries as db_queries
    
    db_queries.record_zone_action(user_id, zone_id, datetime.utcnow().isoformat())
