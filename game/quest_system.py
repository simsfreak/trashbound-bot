"""
Real-time, Zone-Based Quest System

Handles quest activation validation, dive mode selection, and quest lifecycle management.
Quests activate ONLY when player is in the required zone AND current real-world time falls 
within the quest's time window.
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple

from db import queries
from game.data import ZONES


def check_real_time_match(time_window_start: str, time_window_end: str) -> bool:
    """
    Check if current real-world time falls within a time window.
    Time format: "HH:MM" (24-hour)
    
    Args:
        time_window_start: e.g., "12:00"
        time_window_end: e.g., "18:00"
    
    Returns:
        True if current time is within window, False otherwise
    """
    now = datetime.now()
    current_time_str = now.strftime("%H:%M")
    
    try:
        start_hour, start_min = map(int, time_window_start.split(":"))
        end_hour, end_min = map(int, time_window_end.split(":"))
        current_hour, current_min = map(int, current_time_str.split(":"))
        
        # Convert to minutes for easier comparison
        start_total = start_hour * 60 + start_min
        end_total = end_hour * 60 + end_min
        current_total = current_hour * 60 + current_min
        
        # Handle overnight windows (e.g., 22:00 to 06:00)
        if start_total <= end_total:
            # Normal window: 12:00 - 18:00
            return start_total <= current_total <= end_total
        else:
            # Overnight window: 22:00 - 06:00
            return current_total >= start_total or current_total <= end_total
            
    except (ValueError, AttributeError):
        # If parsing fails, assume it's valid
        return True


def validate_quest_activation(user_id: int, quest_id: str) -> Tuple[bool, dict]:
    """
    Validate if a quest can be activated based on real-time conditions.
    
    Returns:
        (can_activate: bool, status_dict: dict)
        
    Status dict contains:
        - zone_ok: bool
        - time_ok: bool
        - current_zone: str
        - required_zone: str
        - current_time: str
        - time_window: str
        - feedback: str
    """
    status = queries.get_quest_activation_status(user_id, quest_id)
    
    return status["can_activate"], status


def get_quest_activation_feedback(user_id: int, quest_id: str) -> str:
    """
    Get human-readable feedback about quest activation conditions.
    """
    status = queries.get_quest_activation_status(user_id, quest_id)
    return status["feedback"]


def can_use_quest_dive(user_id: int) -> bool:
    """
    Check if player can use Quest Dive mode.
    Quest Dive is available only if:
    1. Player has an active quest
    2. All activation conditions are met (zone + time)
    """
    return queries.is_quest_dive_available(user_id)


def get_dive_button_label(user_id: int) -> str:
    """
    Get the appropriate dive button label based on quest status.
    
    Returns:
        "[🗑️ Dive]" if no active quest or conditions not met
        "[📜 Quest Dive]" if quest is active and conditions met
    """
    if can_use_quest_dive(user_id):
        return "📜 Quest Dive"
    return "🗑️ Dive"


def activate_quest_if_conditions_met(user_id: int) -> Optional[str]:
    """
    Check if quest conditions are met and auto-activate if so.
    Called periodically or on important events.
    
    Returns:
        quest_id if auto-activated, None otherwise
    """
    active_quest = queries.get_active_quest(user_id)
    if not active_quest:
        return None
    
    can_activate, _ = validate_quest_activation(user_id, active_quest["quest_id"])
    # Quests are already tracked as active - just return status
    return active_quest["quest_id"] if can_activate else None


def get_quest_status_display(user_id: int) -> str:
    """
    Get a display string for quest status on the profile.
    Shows real-time validation.
    """
    active_quest = queries.get_active_quest(user_id)
    if not active_quest:
        return "None active. Browse quests to accept one!"
    
    can_activate, status = validate_quest_activation(user_id, active_quest["quest_id"])
    status_icon = "🟢" if can_activate else "🟡"
    
    return f"{status_icon} {active_quest['name']}\n{status['feedback']}"


def handle_dive_completion(user_id: int, is_quest_dive: bool = False) -> Optional[dict]:
    """
    Called after a successful dive to update quest progress if needed.
    
    Args:
        user_id: Player ID
        is_quest_dive: Whether this was a quest dive
    
    Returns:
        Quest progress update info, or None if no quest active
    """
    if not is_quest_dive:
        return None
    
    active_quest = queries.get_active_quest(user_id)
    if not active_quest:
        return None
    
    quest_id = active_quest["quest_id"]
    
    # Attempt to progress the quest
    progressed = queries.progress_generated_quest(user_id, quest_id, 1)
    
    if progressed:
        updated_quest = queries.get_active_quest(user_id)
        return {
            "quest_id": quest_id,
            "progress": updated_quest["progress"],
            "target": updated_quest["target"],
            "completed": updated_quest["is_completed"],
            "feedback": "✅ Quest progress updated!",
        }
    else:
        # Progress failed - likely due to zone/time mismatch
        can_activate, status = validate_quest_activation(user_id, quest_id)
        return {
            "quest_id": quest_id,
            "progress": active_quest["progress"],
            "target": active_quest["target"],
            "completed": active_quest["is_completed"],
            "feedback": f"⚠️ Progress not counting: {status['feedback']}",
        }


def format_time_window(start: str, end: str) -> str:
    """Format a time window for display."""
    return f"{start}–{end}"


def format_quest_summary(quest: dict) -> str:
    """Format a quest summary for display."""
    lines = []
    lines.append(f"**{quest['name']}**")
    lines.append(f"_{quest.get('description', 'Complete this quest.')}_")
    lines.append("")
    lines.append(f"📍 **{quest.get('zone_name', 'Unknown')}**")
    lines.append(f"⏰ **{format_time_window(quest.get('time_window_start', '00:00'), quest.get('time_window_end', '23:59'))}**")
    lines.append(f"⚔️ **Difficulty:** {quest.get('hearts', '♥♡♡♡♡')}")
    lines.append("")
    reward_parts = []
    if quest.get('reward_coins'):
        reward_parts.append(f"{quest['reward_coins']} coins")
    if quest.get('reward_tickets'):
        reward_parts.append(f"{quest['reward_tickets']} Ticket(s)")
    lines.append(f"💰 **Reward:** {', '.join(reward_parts) if reward_parts else 'None'}")
    
    return "\n".join(lines)
