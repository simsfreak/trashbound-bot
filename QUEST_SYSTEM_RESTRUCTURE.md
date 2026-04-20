# Real-Time, Zone-Based Quest System - Implementation Guide

## Overview

The quest system has been restructured to support **real-time, zone-based quest activation** with a clear UX that makes quests feel like intentional missions. Quests only progress when the player meets BOTH conditions:
1. Currently in the required zone
2. Current real-world time falls within the quest's time window

---

## Core Architecture

### Database Changes

**New columns added to `generated_quests` table:**
- `time_window_start` (TEXT): Quest active start time (e.g., "12:00")
- `time_window_end` (TEXT): Quest active end time (e.g., "18:00")
- `abandoned_at` (TIMESTAMP): When quest was abandoned (NULL if active)

**New columns added to `players` table:**
- `current_real_date` (DATE): Today's date for tracking quest resets
- `last_quest_activation_check` (TIMESTAMP): Last time we checked activation

### Quest Lifecycle

```
GENERATED → ACCEPTED → ACTIVE (if time+zone match) → COMPLETED → REDEEMED
                    ↓
              ABANDONED (can happen anytime)
```

**States:**
- **Generated**: Quest created, in browseable list
- **Accepted**: Player has accepted but conditions may not be met
- **Active**: Player has accepted AND conditions are met (can earn progress)
- **Completed**: Quest objective fulfilled
- **Redeemed**: Rewards claimed
- **Abandoned**: Player gave up on it

---

## Key Features

### 1. Profile Display

Shows real-time information:
- **Local date/time**: Current real-world datetime
- **Active Zone**: Which zone player is currently in
- **Active Quest**: Name, required zone, required time window, and activation status
  - 🟢 Green indicator: All conditions met, progress is counting
  - 🟡 Yellow indicator: Conditions not met, progress will NOT count

Example:
```
🕐 Mon, Apr 20 • 14:35
📍 Back Alley • 🌅 Morning
📜 Active Quest
🟢 Treasure Dive (Back Alley)
📍 Back Alley
⏰ 12:00–18:00
✅ All conditions met. Progress is counting!
```

### 2. Quest Selection Flow

**Player Actions:**
1. Opens quest browser with `/quests` or quest button
2. Sees batch of 5 randomized quests with [🎲 Next] to cycle
3. Each quest shows:
   - Quest name and flavor text
   - 📍 Zone requirement
   - ⏰ Time window (e.g., "12:00–18:00")
   - ⚔️ Difficulty (hearts: ♥♥♡♡♡)
   - 💰 Rewards
   - Requirement status with feedback
4. Clicks [✅ Accept Quest] to lock it in
5. Quest becomes active immediately, but progress only counts if conditions are met

**Important:** Accepting a quest does NOT activate it immediately. It just adds it to the player's active quest list. Activation happens when conditions are met.

### 3. Real-Time Activation Conditions

A quest becomes **progress-active** ONLY when:

1. **Zone Match**: Player's `current_zone_id` == Quest's `zone_id`
2. **Time Match**: Current real-world time falls within the quest's time window

**Time Window Logic:**
- Normal window (12:00 → 18:00): Progress if 12:00 ≤ NOW ≤ 18:00
- Overnight window (22:00 → 06:00): Progress if NOW ≥ 22:00 OR NOW ≤ 06:00

**Validation:**
```python
# In game/quest_system.py
status = validate_quest_activation(user_id, quest_id)
if status["can_activate"]:
    # All conditions met, progress will count
    print(status["feedback"])  # "✅ All conditions met..."
else:
    # Conditions not met
    print(status["feedback"])  # Lists what's wrong
```

### 4. Zone System

Players activate zones via the 🗺️ Zones button:
- Select from unlocked zones
- [✅ Set Active] to travel there
- Zone determines loot pool for dives

**Free Dive vs Quest Dive:**
- **[🗑️ Dive]**: Default button when no active quest or conditions not met
  - Uses default loot pool (all zone-appropriate items)
  - Always available
  
- **[📜 Quest Dive]**: Appears when active quest conditions are met
  - Uses zone-specific loot ONLY
  - Progresses active quest
  - Still applies equipment bonuses

### 5. Dive Modes

**Implementation:**
```python
# In ui/views.py - ProfileView
def get_dive_button_label(user_id):
    if can_use_quest_dive(user_id):
        return "📜 Quest Dive"
    return "🗑️ Dive"
```

**Free Dive Flow:**
1. Click [🗑️ Dive]
2. Get random item from zone
3. Gain coins/XP
4. Inventory updated
5. No quest progress

**Quest Dive Flow:**
1. Verify quest conditions are still met
2. Click [📜 Quest Dive]
3. Get item from zone
4. Gain coins/XP
5. **Quest progress incremented**
6. Check if quest completed
7. Inventory updated

### 6. Quest Abandonment

**Add [❌ Abandon Quest] button when quest is active:**
```python
@discord.ui.button(label="❌ Abandon Quest", style=discord.ButtonStyle.danger)
async def abandon_quest(self, interaction, button):
    if queries.abandon_quest(interaction.user.id):
        # Quest marked as abandoned
        # active_quest_id set to NULL
        # Reset zone to back_alley (optional)
```

**Effects:**
- Marks quest with `abandoned_at` timestamp
- Clears player's `active_quest_id`
- Player can accept a new quest

### 7. Loot Separation

**CRITICAL: Free Dive and Quest Dive loot pools must NEVER overlap.**

**Implementation:**
```python
# In game/helpers.py
def roll_item_for_zone(zone_id, quest_mode=False):
    """
    Roll item for a zone.
    
    Args:
        zone_id: Which zone
        quest_mode: If True, use ONLY zone-specific items
                   If False, use default+zone items
    """
    if quest_mode:
        # ONLY items where zone_id in item["zone_ids"]
        items = [(id, data) for id, data in ITEMS.items() 
                 if zone_id in data.get("zone_ids", [])]
    else:
        # Default loot pool - doesn't depend on zone
        items = [...]
    
    return random.choice(weighted_pool)
```

**Item Configuration (game/data.py):**
```python
ITEMS = {
    "scrap_metal": {
        "zone_ids": ["back_alley", "apartment_bins"],  # Where this can drop
        ...
    },
    ...
}
```

---

## Query Functions Added

### Quest State Management

```python
# Abandon the active quest
queries.abandon_quest(user_id, quest_id=None)

# Check real-time activation conditions
is_valid, feedback = queries.check_quest_real_time_conditions(user_id, quest_id)

# Get comprehensive activation status
status = queries.get_quest_activation_status(user_id, quest_id)
# Returns: {zone_ok, time_ok, can_activate, feedback, current_zone, required_zone, ...}

# Check if Quest Dive button should show
available = queries.is_quest_dive_available(user_id)

# Get paginated accepted quests for browsing
quests = queries.get_accepted_quests_page(user_id, page=0)

# Count available quests
count = queries.count_available_quests(user_id)
```

---

## Helper Functions (game/quest_system.py)

```python
# Check if current time is in window
is_time_match = check_real_time_match("12:00", "18:00")

# Validate quest can be activated
can_activate, status_dict = validate_quest_activation(user_id, quest_id)

# Get dive button label
label = get_dive_button_label(user_id)  # "🗑️ Dive" or "📜 Quest Dive"

# Auto-activate if conditions met
quest_id = activate_quest_if_conditions_met(user_id)

# Get profile display text
display = get_quest_status_display(user_id)

# Handle post-dive progression
progress_info = handle_dive_completion(user_id, is_quest_dive=True)

# Format for UI
formatted = format_quest_summary(quest_dict)
```

---

## UI Components

### GeneratedQuestView
- Paginated quest browser
- Shows batch of 5 quests
- [🎲 Next] to cycle through
- [✅ Accept Quest] to lock one in
- [🔄 Refresh] to generate new batch
- Requirement status with real-time validation

### Quest Dive Button
- Conditionally shows based on `is_quest_dive_available()`
- Changes label and styling based on availability
- Validates conditions before allowing dive
- Progresses quest on successful dive

### Profile Display
- Shows real-world date/time
- Shows active quest with status indicator
- Shows requirement feedback

---

## UX Feedback

### Success Cases
- ✅ "All conditions met. Progress is counting!"
- 🟢 Green indicator on profile
- Dive completes, quest progress increments
- Completion shows progress bar

### Warning Cases
- 🟡 Yellow indicator: Some conditions not met
- "⏰ Time mismatch: Need 12:00–18:00. Current: 14:35"
- "📍 Zone mismatch: Need Back Alley. You're in Mall Rear Lot"
- Dive completes, but quest progress DOES NOT increment

### Error Cases
- ❌ Quest not found or abandoned
- ❌ Player not found
- "No active quest. Accept one to get started!"

---

## Real-World Time Integration

### How It Works

```python
from datetime import datetime

# In validation functions:
now = datetime.now()  # Gets system time

# Parse time windows
current_time = now.strftime("%H:%M")  # e.g., "14:35"

# Compare with quest window
# If 14:35 is in [12:00, 18:00] → MATCH
```

### Timezone Considerations

The system uses the **server's local time** via `datetime.now()`. 

**To use UTC instead:**
```python
now = datetime.utcnow()
```

**To use player's local timezone:**
```python
# Store player_timezone in database
# Use pytz: now = datetime.now(pytz.timezone(player_timezone))
```

---

## Testing Checklist

- [ ] Quest accepts successfully
- [ ] Active quest shows on profile with 🟢 green when conditions met
- [ ] Active quest shows 🟡 yellow when conditions not met
- [ ] [📜 Quest Dive] button appears only when conditions met
- [ ] [🗑️ Dive] button appears when conditions not met
- [ ] Quest Dive increments progress when conditions met
- [ ] Free Dive does not increment quest progress
- [ ] Quest progress shows correctly on profile
- [ ] Completing quest marks it as completed
- [ ] Abandoned quests are marked properly
- [ ] Time window validation works correctly
- [ ] Zone mismatch prevents progress
- [ ] Loot pools don't overlap between free/quest dives

---

## Configuration & Customization

### Quest Time Windows

Define in quest generator:
```python
quest = {
    "time_window_start": "12:00",  # Customize per quest type
    "time_window_end": "18:00",
    ...
}
```

### Loot Pools

Configure in `game/data.py`:
```python
ITEMS = {
    "scrap_metal": {
        "zone_ids": ["back_alley", "apartment_bins"],  # Where it drops
        ...
    }
}
```

### Difficulty Scaling

Quests scale rewards by difficulty:
```python
base_reward = 150
multiplier = 0.5 + (difficulty * 0.3)  # 0.8 (diff 1) to 2.0 (diff 5)
final_reward = int(base_reward * multiplier)
```

---

## Known Limitations & Future Enhancements

### Current Limitations
1. Time windows are 24-hour format only
2. No support for weekly/monthly quests yet
3. No quest markers on zones (optional future feature)
4. Auto-save of quest attempts (could add)

### Potential Enhancements
1. **Dynamic quest generation** based on player level
2. **Multi-stage quests** (e.g., find item → deliver → craft)
3. **Seasonal quests** that reset daily
4. **Group quests** (multiple players work together)
5. **Quest chains** (complete quest A to unlock quest B)
6. **Time-extension items** that temporarily extend quest windows
7. **Mobile app** with push notifications for quest activation
8. **Leaderboards** for fastest quest completions

---

## Troubleshooting

### Quest not progressing even though conditions appear met
1. Check server time matches player expectations
2. Verify `time_window_start` and `time_window_end` format
3. Ensure zone IDs match exactly
4. Check if quest was marked as completed or redeemed

### Loot overlap in free/quest dives
1. Verify all items have correct `zone_ids` in ITEMS dict
2. Ensure roll functions check `quest_mode` parameter
3. Run query to find items appearing in both pools

### Quest button not showing [📜 Quest Dive]
1. Check `is_quest_dive_available()` returns True
2. Verify active quest exists and is not marked as completed
3. Confirm time window contains current time
4. Ensure player zone matches quest zone

---

## Code Examples

### Accepting a Quest (UI)
```python
@discord.ui.button(label="✅ Accept Quest")
async def accept_quest(self, interaction, button):
    quest = self._get_current_quest()
    
    # Set as active
    queries.set_active_quest(interaction.user.id, quest["quest_id"])
    
    # Check conditions
    can_activate, status = validate_quest_activation(
        interaction.user.id, 
        quest["quest_id"]
    )
    
    embed = discord.Embed(
        title="✅ Quest Accepted!",
        description=f"You've accepted **{quest['name']}**"
    )
    
    if not can_activate:
        embed.description += f"\n\n⚠️ Conditions not met:\n{status['feedback']}"
    
    await interaction.response.edit_message(embed=embed)
```

### Performing a Dive (Logic)
```python
async def dive_button(self, interaction, button):
    user_id = interaction.user.id
    is_quest_dive = can_use_quest_dive(user_id)
    
    # Roll item
    item_id, item = roll_item_for_zone(
        player["current_zone_id"],
        quest_mode=is_quest_dive
    )
    
    # Add to inventory
    queries.add_item_to_inventory(user_id, item_id, 1)
    
    # Progress quest if applicable
    if is_quest_dive:
        progress_info = handle_dive_completion(user_id, is_quest_dive=True)
        if progress_info["progress"] >= progress_info["target"]:
            embed.add_field(
                name="🎉 Quest Complete!",
                value=f"Completed: {progress_info['quest_id']}"
            )
```

### Checking Activation (Periodic)
```python
async def periodic_quest_check():
    """Called every minute to check quest activations"""
    for player_id in active_players:
        activate_quest_if_conditions_met(player_id)
        # Could send notification if quest just activated
```

---

## API Reference

See `db/queries.py` and `game/quest_system.py` for full function signatures and docstrings.
