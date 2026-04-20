# Quest System - Quick Start Integration Guide

## For Developers: How to Integrate the New Quest System

### 1. Import the New Modules

```python
# In your views.py or command files
from game.quest_system import (
    can_use_quest_dive,
    get_dive_button_label,
    handle_dive_completion,
    validate_quest_activation,
)

from db import queries
```

### 2. Update Dive Button Logic

In `ui/views.py`, modify the ProfileView's dive button:

```python
@discord.ui.button(label="🗑️ Dive", style=discord.ButtonStyle.primary, row=0)
async def dive_button(self, interaction: discord.Interaction, button: discord.ui.Button):
    # Determine if this is a quest dive
    is_quest_dive = can_use_quest_dive(interaction.user.id)
    
    # ... existing dive logic ...
    
    # After rolling item:
    if is_quest_dive:
        # Handle quest progression
        progress_info = handle_dive_completion(interaction.user.id, is_quest_dive=True)
        if progress_info and progress_info["completed"]:
            embed.add_field(
                name="🎉 Quest Complete!",
                value=f"Progress: {progress_info['progress']}/{progress_info['target']}"
            )
    
    # Update button for next time
    button.label = get_dive_button_label(interaction.user.id)
```

### 3. Add Abandon Quest Button

In ProfileView, add this button:

```python
@discord.ui.button(label="❌ Abandon", style=discord.ButtonStyle.danger, row=1)
async def abandon_quest(self, interaction: discord.Interaction, button: discord.ui.Button):
    active_quest = queries.get_active_quest(interaction.user.id)
    
    if not active_quest:
        await interaction.response.send_message(
            "No active quest to abandon.",
            ephemeral=True
        )
        return
    
    if queries.abandon_quest(interaction.user.id):
        embed = discord.Embed(
            title="❌ Quest Abandoned",
            description=f"You gave up on **{active_quest['name']}**",
            color=0xED4245
        )
        await interaction.response.edit_message(embed=embed, view=ProfileView(...))
    else:
        await interaction.response.send_message(
            "Failed to abandon quest.",
            ephemeral=True
        )
```

**Note:** Only show this button if quest is active:

```python
# In ProfileView.__init__
if queries.get_active_quest(owner_id):
    self.add_item(AbandonQuestButton())
```

### 4. Verify Loot Pool Separation

In `game/helpers.py`, update `roll_item_for_zone()`:

```python
def roll_item_for_zone(zone_id: str, rare_bonus: float = 0.0, quest_mode: bool = False) -> tuple[str, dict]:
    """
    Roll item for a zone.
    
    Args:
        zone_id: Which zone to get loot from
        rare_bonus: Rarity multiplier from equipment
        quest_mode: If True, use ONLY zone-specific items
    """
    
    if quest_mode:
        # Quest Dive: ONLY zone-specific items
        items = [
            (item_id, item_data)
            for item_id, item_data in ITEMS.items()
            if zone_id in item_data.get("zone_ids", [])
        ]
    else:
        # Free Dive: Use existing default pool
        items = get_items_for_zone(zone_id)
    
    # ... existing weighting logic ...
    return random.choice(weighted_pool)
```

### 5. Update Dive Button Call

Pass `quest_mode` to the roll function:

```python
# In dive_button
is_quest_dive = can_use_quest_dive(interaction.user.id)

item_id, item = roll_item_for_zone(
    player["current_zone_id"],
    rare_bonus=equipment_bonuses["drop_bonus"],
    quest_mode=is_quest_dive  # Pass this parameter
)
```

### 6. Test the Integration

Use this test sequence:

```python
# Test 1: Check quest availability
user_id = 123456789
active_quest = queries.get_active_quest(user_id)
print(f"Active quest: {active_quest['name'] if active_quest else 'None'}")

# Test 2: Check if Quest Dive available
can_dive = can_use_quest_dive(user_id)
print(f"Can use Quest Dive: {can_dive}")

# Test 3: Get button label
label = get_dive_button_label(user_id)
print(f"Button should show: {label}")

# Test 4: Validate activation
can_activate, status = validate_quest_activation(user_id, active_quest["quest_id"])
print(f"Conditions met: {can_activate}")
print(f"Feedback: {status['feedback']}")

# Test 5: Simulate dive
progress_info = handle_dive_completion(user_id, is_quest_dive=True)
print(f"Quest progress: {progress_info['progress']}/{progress_info['target']}")
```

### 7. Common Issues & Solutions

**Issue: Quest button not showing [📜 Quest Dive]**
```python
# Debug: Check what's happening
print(f"Active quest: {queries.get_active_quest(user_id)}")
print(f"Quest dive available: {can_use_quest_dive(user_id)}")

# Solution: Both must be true
# 1. Active quest exists
# 2. Zone matches AND time is in window
```

**Issue: Progress not incrementing**
```python
# Debug: Check why progress failed
progress_info = handle_dive_completion(user_id, is_quest_dive=True)
print(f"Feedback: {progress_info['feedback']}")

# Solution: Usually zone or time mismatch
# Check: Player zone == Quest zone
# Check: Current time in quest window
```

**Issue: Loot pool wrong**
```python
# Verify ITEMS config
for item_id, item in ITEMS.items():
    zones = item.get("zone_ids", [])
    print(f"{item_id}: zones={zones}")

# Verify quest_mode parameter
print(f"Quest mode: {quest_mode}")
print(f"Items available: {len(items)}")
```

---

## Configuration

### Set Quest Time Windows

When generating quests, set time windows:

```python
quest = {
    "name": "Morning Treasure Hunt",
    "time_window_start": "06:00",
    "time_window_end": "12:00",
    # ...
}
```

### Common Time Windows

```python
QUEST_TIME_WINDOWS = {
    "morning": ("06:00", "12:00"),      # Early birds
    "afternoon": ("12:00", "18:00"),    # Post-lunch grind
    "evening": ("18:00", "00:00"),      # After work
    "night": ("20:00", "04:00"),        # Late night
    "overnight": ("22:00", "06:00"),    # Midnight to dawn
    "all_day": ("00:00", "23:59"),      # No time restriction
}
```

---

## API Reference

### High-Level Functions

```python
# Check if quest conditions are met
can_activate, status = validate_quest_activation(user_id, quest_id)

# Determine which dive button to show
label = get_dive_button_label(user_id)  # "🗑️ Dive" or "📜 Quest Dive"

# Handle post-dive quest progression
progress_info = handle_dive_completion(user_id, is_quest_dive=True)

# Get human-readable activation feedback
feedback = get_quest_activation_feedback(user_id, quest_id)

# Check if player can use Quest Dive
available = can_use_quest_dive(user_id)
```

### Database Functions

```python
# Get player's active quest
quest = queries.get_active_quest(user_id)

# Check real-time conditions
is_valid, feedback = queries.check_quest_real_time_conditions(user_id, quest_id)

# Get full status
status = queries.get_quest_activation_status(user_id, quest_id)

# Abandon active quest
queries.abandon_quest(user_id)

# Accept a quest as active
queries.set_active_quest(user_id, quest_id)

# Progress a quest
queries.progress_generated_quest(user_id, quest_id, progress_amount=1)

# Complete and redeem
queries.redeem_generated_quest(user_id, quest_id)
```

---

## Event Hooks

Consider adding these event hooks for notifications:

```python
# When quest becomes active (conditions met)
async def on_quest_activated(user_id: str, quest_id: str):
    """Called when real-time conditions are first met for a quest"""
    user = await bot.fetch_user(user_id)
    quest = queries.get_active_quest(user_id)
    await user.send(f"🟢 **{quest['name']}** is now active! Quest Dive available.")

# When quest conditions fail (e.g., time window closes)
async def on_quest_deactivated(user_id: str, quest_id: str):
    """Called when conditions stop being met"""
    user = await bot.fetch_user(user_id)
    quest = queries.get_active_quest(user_id)
    await user.send(f"🟡 **{quest['name']}** is no longer active. Conditions changed.")

# When quest completes
async def on_quest_completed(user_id: str, quest_id: str):
    """Called when quest objective is achieved"""
    user = await bot.fetch_user(user_id)
    quest = queries.get_active_quest(user_id)
    await user.send(f"🎉 **{quest['name']}** completed! Ready to redeem.")
```

---

## Debugging

### Enable Debug Logging

```python
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("quest_system")

# In quest validation
logger.debug(f"Checking quest {quest_id} for user {user_id}")
logger.debug(f"Zone match: {zone_ok} (player: {player_zone}, quest: {quest_zone})")
logger.debug(f"Time match: {time_ok} (now: {current_time}, window: {time_start}–{time_end})")
logger.debug(f"Can activate: {can_activate}")
```

### Common Debug Commands

```python
# Check player state
player = queries.get_player(user_id)
print(f"Zone: {player['current_zone_id']}")
print(f"Level: {player['level']}")

# Check active quest
quest = queries.get_active_quest(user_id)
print(f"Quest: {quest['name']}")
print(f"Zone: {quest['zone_id']}")
print(f"Time window: {quest['time_window_start']}–{quest['time_window_end']}")
print(f"Progress: {quest['progress']}/{quest['target']}")

# Check activation
status = queries.get_quest_activation_status(user_id, quest['quest_id'])
print(f"Activation: {status}")
```

---

## Deployment Checklist

- [ ] Database migrations run successfully
- [ ] All new imports added to relevant files
- [ ] Dive button logic updated
- [ ] Abandon quest button added
- [ ] Loot pool separation verified
- [ ] Time window validation tested
- [ ] Zone matching tested
- [ ] Profile display shows quest info
- [ ] Button labels update correctly
- [ ] Progress tracking works
- [ ] Quest completion works
- [ ] Staging tests pass
- [ ] Ready for production

---

## Support

- Full documentation: See `QUEST_SYSTEM_RESTRUCTURE.md`
- Implementation details: See `game/quest_system.py`
- Database queries: See `db/queries.py`
- Error messages: Check feedback strings in validation functions

**For issues or questions**, refer to the troubleshooting section in the main documentation.
