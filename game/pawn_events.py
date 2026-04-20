"""
Pawn Owner Event System

Creates rare, meaningful, and unpredictable interactions with the Pawn Owner.
Includes special events like "The Ask" that create timed objectives.
"""

import random
from datetime import datetime, timedelta
from typing import Optional

# ==================== EVENT TYPES ====================

EVENT_TRIGGERS = {
    "normal": {
        "weight": 80,
        "name": "Casual Chat",
        "description": "Normal pawn owner interaction",
        "min_relationship": 0,
    },
    "enhanced": {
        "weight": 15,
        "name": "Spicy Offer",
        "description": "The pawn owner has better things to discuss",
        "min_relationship": 2,
    },
    "special": {
        "weight": 5,
        "name": "The Ask",
        "description": "The pawn owner needs something from you",
        "min_relationship": 4,  # High relationship required
    },
}

# ==================== SPECIAL EVENT: "THE ASK" ====================

THE_ASK_REQUESTS = [
    {
        "id": "pristine_glass",
        "item_name": "Pristine Glass Pane",
        "flavor": "You know that pristine glass from the old mall? I need one. No cracks. No dust. Keep it clean. 24 hours. I'll owe you one.",
        "reward_coins": 400,
        "reward_tickets": 3,
        "reward_exclusive": "pawnbroker_gold_ring",
        "difficulty": "medium",
    },
    {
        "id": "era_coins",
        "item_name": "3 Era Coins",
        "flavor": "Bring me three era coins. Real ones. Not the trash-bin duplicates. 24 hours. And don't ask why.",
        "reward_coins": 500,
        "reward_tickets": 4,
        "reward_exclusive": "cursed_deal_charm",
        "difficulty": "hard",
    },
    {
        "id": "intact_polaroid",
        "item_name": "Intact Polaroid Photo",
        "flavor": "I need an undamaged polaroid. Still got the photo on it. Could be anyone. I just need to see someone's face. You got 24 hours.",
        "reward_coins": 300,
        "reward_tickets": 2,
        "reward_exclusive": "memory_keeper_pendant",
        "difficulty": "easy",
    },
    {
        "id": "working_watch",
        "item_name": "Working Watch",
        "flavor": "A watch that actually works. Ticking. Moving. Keeping time. One day. That's your window. Bring it to me.",
        "reward_coins": 350,
        "reward_tickets": 3,
        "reward_exclusive": "time_thief_bracelet",
        "difficulty": "medium",
    },
    {
        "id": "leather_jacket",
        "item_name": "Leather Jacket",
        "flavor": "Real leather. Worn but not destroyed. Size doesn't matter. Just bring me proof the alley still has standards. 24 hours.",
        "reward_coins": 450,
        "reward_tickets": 3,
        "reward_exclusive": "vagrant_king_coat",
        "difficulty": "hard",
    },
    {
        "id": "vinyl_record",
        "item_name": "Vinyl Record (playable)",
        "flavor": "Any record. Any band. Just make sure it's not scratched to hell. I want to hear what the trash has been listening to.",
        "reward_coins": 280,
        "reward_tickets": 2,
        "reward_exclusive": "music_box_key",
        "difficulty": "easy",
    },
]

# ==================== EXCLUSIVE REWARDS ====================

EXCLUSIVE_REWARDS = {
    "pawnbroker_gold_ring": {
        "name": "Pawnbroker's Gold Ring",
        "emoji": "💍",
        "rarity": "Epic",
        "flavor": "The real deal. The pawnbroker's personal ring. He only gives these out once in a blue moon.",
        "effects": {"coin_boost": 0.08, "relationship_boost": True},
    },
    "cursed_deal_charm": {
        "name": "Cursed Deal Charm",
        "emoji": "🔮",
        "rarity": "Legendary",
        "flavor": "Sealed with a promise, blessed by chaos. Carrying this feels... significant.",
        "effects": {"drop_bonus": 0.12, "rare_chance_boost": 0.05},
    },
    "memory_keeper_pendant": {
        "name": "Memory Keeper Pendant",
        "emoji": "🔗",
        "rarity": "Rare",
        "flavor": "Someone's forgotten memory, now yours to keep. It hums slightly.",
        "effects": {"xp_boost": 0.06},
    },
    "time_thief_bracelet": {
        "name": "Time Thief's Bracelet",
        "emoji": "⏰",
        "rarity": "Epic",
        "flavor": "It stopped ticking the moment he held it. But it still works somehow.",
        "effects": {"speedup": True, "quest_timer_boost": 0.25},
    },
    "vagrant_king_coat": {
        "name": "Vagrant King Coat",
        "emoji": "👑",
        "rarity": "Legendary",
        "flavor": "Leather aged to perfection. Worn by someone who walked the alleys like they owned them.",
        "effects": {"zone_respect": True, "extra_item_chance": 0.10},
    },
    "music_box_key": {
        "name": "Music Box Key",
        "emoji": "🎵",
        "rarity": "Rare",
        "flavor": "Winds up a melody you almost remember. Almost.",
        "effects": {"morale_boost": 0.15},
    },
}

# ==================== EVENT DIALOGUE ====================

ENHANCED_DIALOGUES = [
    {
        "opening": "The pawnbroker leans back and grins.",
        "choices": [
            {
                "label": "Listen intently",
                "liked": True,
                "reward_multiplier": 1.5,
                "flavor": "He likes your attention."
            },
            {
                "label": "Half-pay attention",
                "liked": False,
                "reward_multiplier": 0.8,
                "flavor": "He notices you're distracted."
            },
        ],
    },
    {
        "opening": "Something in his expression shifts. This isn't normal pawn chat.",
        "choices": [
            {
                "label": "Ask what he wants",
                "liked": True,
                "reward_multiplier": 1.4,
                "flavor": "Direct approach. He respects that."
            },
            {
                "label": "Make a joke",
                "liked": False,
                "reward_multiplier": 0.9,
                "flavor": "He doesn't laugh."
            },
        ],
    },
]

THE_ASK_ACCEPTANCE_DIALOGUES = [
    "He nods slowly. 'Good. I knew you would.' He slides a crumpled note across the desk. '24 hours. Don't forget.'",
    "'That's all I needed to hear.' His eyes gleam. 'Now go. Time's burning.'",
    "He smiles. It's not a friendly smile. 'Then we have a deal, friend.'",
    "'I knew you'd do right.' He places something small in your hand. 'Prove me right.'",
]

THE_ASK_REFUSAL_DIALOGUES = [
    "His face goes cold. 'I see.' He turns away. You hear him muttering. 'So that's how it is, then.'",
    "'Huh.' He goes back to organizing his shelves. You feel the chill.",
    "He looks at you like he's seeing you for the first time. And he doesn't like what he sees.",
    "'Fine. Forget I asked.' But he won't forget. You can tell.",
]

THE_ASK_SUCCESS_DIALOGUES = [
    "'Ah. You came through.' He holds the item carefully. 'Not many do. I won't forget this.'",
    "He examines it slowly, almost reverently. 'Perfect. Exactly what I needed. You're alright, friend.'",
    "'Well, I'll be damned.' He laughs—a real laugh. 'You actually did it. Color me impressed.'",
]

THE_ASK_FAILURE_DIALOGUES = [
    "'So you couldn't get it.' He doesn't sound angry. He sounds disappointed. Worse, somehow.",
    "'The clock ran out, huh?' He shakes his head slowly. 'I really thought you could do it.'",
    "'Time's up.' He doesn't need to say more. You failed. He knows. You know.",
]

# ==================== RELATIONSHIP IMPACT ====================

RELATIONSHIP_IMPACTS = {
    "chat_normal": 0,  # Neutral baseline
    "chat_enhanced_liked": 1,
    "chat_enhanced_disliked": -1,
    "ask_accepted": 0,  # Neutral—test of character
    "ask_refused": -2,  # Betrayal of trust
    "ask_completed": 2,  # Respect earned
    "ask_failed": -7,  # Broken promise
}

# ==================== CORE FUNCTIONS ====================

def pick_event_type(relationship: int) -> str:
    """
    Determine which event type to trigger based on relationship.
    
    Args:
        relationship: Player's pawn relationship score
        
    Returns:
        Event type: "normal", "enhanced", or "special"
    """
    # Only allow special events at high relationship
    available_events = ["normal", "enhanced"]
    if relationship >= EVENT_TRIGGERS["special"]["min_relationship"]:
        available_events.append("special")
    
    # Weight-based selection
    total_weight = sum(EVENT_TRIGGERS[e]["weight"] for e in available_events)
    rand = random.randint(0, total_weight - 1)
    
    cumulative = 0
    for event in available_events:
        weight = EVENT_TRIGGERS[event]["weight"]
        if rand < cumulative + weight:
            return event
        cumulative += weight
    
    return "normal"  # Fallback


def generate_special_event() -> dict:
    """
    Generate a "The Ask" special event.
    
    Returns:
        Dict containing:
        - request_id: Unique request ID
        - request_data: Item/objective info
        - deadline: 24 hours from now
        - status: "pending_choice"
    """
    request_data = random.choice(THE_ASK_REQUESTS)
    
    return {
        "request_id": request_data["id"],
        "item_name": request_data["item_name"],
        "flavor": request_data["flavor"],
        "reward_coins": request_data["reward_coins"],
        "reward_tickets": request_data["reward_tickets"],
        "reward_exclusive": request_data["reward_exclusive"],
        "difficulty": request_data["difficulty"],
        "deadline": datetime.utcnow() + timedelta(hours=24),
        "status": "pending_choice",  # pending_choice -> active -> completed/failed
        "created_at": datetime.utcnow(),
    }


def check_ask_deadline(ask_data: dict) -> str:
    """
    Check if a pending ask is past deadline.
    
    Args:
        ask_data: The active ask request
        
    Returns:
        "pending", "completed", or "failed"
    """
    if ask_data["status"] == "completed":
        return "completed"
    
    if ask_data["status"] == "failed":
        return "failed"
    
    if datetime.utcnow() > ask_data["deadline"]:
        return "failed"  # Deadline passed
    
    return "pending"


def get_random_acceptance_dialogue() -> str:
    """Get acceptance dialogue when player accepts The Ask"""
    return random.choice(THE_ASK_ACCEPTANCE_DIALOGUES)


def get_random_refusal_dialogue() -> str:
    """Get refusal dialogue when player refuses The Ask"""
    return random.choice(THE_ASK_REFUSAL_DIALOGUES)


def get_random_success_dialogue() -> str:
    """Get success dialogue when player completes The Ask"""
    return random.choice(THE_ASK_SUCCESS_DIALOGUES)


def get_random_failure_dialogue() -> str:
    """Get failure dialogue when player fails The Ask"""
    return random.choice(THE_ASK_FAILURE_DIALOGUES)


def get_enhanced_dialogue() -> dict:
    """Get random enhanced dialogue with choices"""
    return random.choice(ENHANCED_DIALOGUES)


def calculate_relationship_change(event_type: str, choice_liked: bool = None, ask_outcome: str = None) -> int:
    """
    Calculate relationship point change based on event and outcome.
    
    Args:
        event_type: "normal", "enhanced", or "special"
        choice_liked: For enhanced events, was the choice liked?
        ask_outcome: For special events, was it accepted/refused/completed/failed?
        
    Returns:
        Relationship point delta
    """
    if event_type == "normal":
        return RELATIONSHIP_IMPACTS["chat_normal"]
    
    elif event_type == "enhanced":
        if choice_liked:
            return RELATIONSHIP_IMPACTS["chat_enhanced_liked"]
        else:
            return RELATIONSHIP_IMPACTS["chat_enhanced_disliked"]
    
    elif event_type == "special":
        if ask_outcome == "accepted":
            return RELATIONSHIP_IMPACTS["ask_accepted"]
        elif ask_outcome == "refused":
            return RELATIONSHIP_IMPACTS["ask_refused"]
        elif ask_outcome == "completed":
            return RELATIONSHIP_IMPACTS["ask_completed"]
        elif ask_outcome == "failed":
            return RELATIONSHIP_IMPACTS["ask_failed"]
    
    return 0  # Default


def get_exclusive_reward_data(reward_id: str) -> Optional[dict]:
    """Get data for an exclusive reward item"""
    return EXCLUSIVE_REWARDS.get(reward_id)
