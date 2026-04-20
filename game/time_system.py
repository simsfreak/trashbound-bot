"""
Time Phase System

Simple, immersive time system using three phases:
- Morning 🌅 (early, fresh, discovery time)
- Evening 🌆 (late afternoon, transition time)
- Night 🌙 (dark, mysterious, eerie time)

No real-world clock dependencies. Session-based or randomly assigned.
"""

import random
from datetime import datetime, timedelta

# ==================== TIME PHASES ====================

TIME_PHASES = {
    "morning": {
        "name": "Morning",
        "emoji": "🌅",
        "description": "Fresh dumpsters, early moods, clear skies.",
        "flavor": "⌁ dawn breaks over the alleys ⌁",
        "loot_vibe": "Fresh finds are more common.",
    },
    "evening": {
        "name": "Evening",
        "emoji": "🌆",
        "description": "Transition time, golden light fading, shops closing.",
        "flavor": "⌁ the sun dips. the city changes. ⌁",
        "loot_vibe": "Mixed loot, anything could appear.",
    },
    "night": {
        "name": "Night",
        "emoji": "🌙",
        "description": "Dark, mysterious, eerie, full of secrets.",
        "flavor": "⌁ shadows settle. the alleys wake up. ⌁",
        "loot_vibe": "Rare finds emerge under moonlight.",
    },
}

# ==================== PHASE HELPERS ====================

def get_phase_info(phase: str) -> dict:
    """Get complete information about a time phase."""
    return TIME_PHASES.get(phase, TIME_PHASES["morning"])


def get_all_phases() -> list[str]:
    """Get list of all time phase IDs."""
    return list(TIME_PHASES.keys())


def get_phase_emoji(phase: str) -> str:
    """Get emoji for a time phase."""
    return get_phase_info(phase)["emoji"]


def get_phase_name(phase: str) -> str:
    """Get display name for a time phase."""
    return get_phase_info(phase)["name"]


# ==================== RANDOM PHASE ASSIGNMENT ====================

def get_random_phase() -> str:
    """
    Get a random time phase.
    Weighted slightly toward night (more mysterious feeling).
    """
    return random.choices(
        ["morning", "evening", "night"],
        weights=[30, 30, 40],
        k=1
    )[0]


def get_random_phase_different_from(current_phase: str) -> str:
    """Get a random phase that's different from current phase."""
    other_phases = [p for p in get_all_phases() if p != current_phase]
    return random.choice(other_phases)


# ==================== CYCLING (for session-based time) ====================

def get_next_phase(current_phase: str) -> str:
    """
    Get the next phase in cycle: morning → evening → night → morning
    """
    phases = ["morning", "evening", "night"]
    try:
        current_idx = phases.index(current_phase)
        next_idx = (current_idx + 1) % len(phases)
        return phases[next_idx]
    except ValueError:
        return "morning"


def cycle_to_next_phase(current_phase: str) -> tuple[str, str]:
    """
    Cycle to next phase and return (old_phase, new_phase).
    Useful for displaying phase changes.
    """
    next_phase = get_next_phase(current_phase)
    return (current_phase, next_phase)


# ==================== PHASE MATCHING ====================

def phases_match(phase1: str, phase2: str) -> bool:
    """Check if two phase strings refer to the same phase."""
    return phase1.lower().strip() == phase2.lower().strip()


def is_phase_match(player_phase: str, required_phase: str) -> bool:
    """
    Check if player's current phase matches quest requirement.
    Returns True if phases match, False if they don't.
    """
    return phases_match(player_phase, required_phase)


# ==================== PHASE DESCRIPTIONS ====================

def get_phase_full_description(phase: str) -> str:
    """Get full, immersive description of a time phase."""
    info = get_phase_info(phase)
    return f"{info['emoji']} **{info['name']}**\n_{info['description']}_\n{info['flavor']}"


def get_phase_loot_description(phase: str) -> str:
    """Get loot description for a phase (what drops look like)."""
    info = get_phase_info(phase)
    return f"{info['emoji']} {info['loot_vibe']}"


# ==================== MISMATCH FEEDBACK ====================

def get_phase_mismatch_message(player_phase: str, required_phase: str) -> str:
    """
    Generate a clear, friendly message explaining phase mismatch.
    Shows what player has vs. what's needed.
    """
    player_info = get_phase_info(player_phase)
    required_info = get_phase_info(required_phase)
    
    return (
        f"⏰ **Time Mismatch**\n\n"
        f"📍 **You are in:** {player_info['emoji']} {player_info['name']}\n"
        f"📍 **Quest requires:** {required_info['emoji']} {required_info['name']}\n\n"
        f"Come back when it's {required_info['name'].lower()} to progress on this quest."
    )


# ==================== ZONE + TIME COMBO ====================

def get_environment_description(zone_name: str, phase: str) -> str:
    """
    Get atmospheric description of zone at specific time.
    Combines zone flavor with time phase flavor.
    """
    phase_info = get_phase_info(phase)
    return f"{phase_info['emoji']} {zone_name} — {phase_info['name']}\n{phase_info['flavor']}"


def describe_quest_requirements(zone_name: str, phase: str, quest_name: str) -> str:
    """
    Describe where and when a quest should be completed.
    """
    phase_info = get_phase_info(phase)
    return (
        f"🎯 **{quest_name}**\n\n"
        f"📍 **Zone:** {zone_name}\n"
        f"⏰ **Time:** {phase_info['emoji']} {phase_info['name']}\n"
        f"💡 {phase_info['loot_vibe']}"
    )
