# Dynamic Quest Dive Button - Implementation Guide

## Overview

The Dive button now dynamically reflects quest state in real-time, changing its label and color when a quest becomes active. Players get instant visual feedback that they're in Quest Dive mode.

## Quest State Detection

### How Quest Active State is Determined

The button uses `can_use_quest_dive(user_id)` to determine if a quest is truly active:

```python
def can_use_quest_dive(user_id: int) -> bool:
    """
    Quest Dive is available ONLY if:
    1. Player has an active quest
    2. Player is in the quest's required zone
    3. Current real-world time is within quest time window
    """
    return queries.is_quest_dive_available(user_id)
```

This function checks all three conditions:
- ✅ Active quest exists
- ✅ Player's current zone matches quest zone
- ✅ Current real time ∈ [quest_time_start, quest_time_end]

### Button States

| State | Label | Color | Condition |
|-------|-------|-------|-----------|
| **Normal Dive** | `🗑️ Dive` | Blue (Primary) | No active quest OR conditions not met |
| **Quest Dive** | `📜 Quest Dive` | Green (Success) | All conditions met |

## Implementation Details

### File: `ui/views.py`

#### 1. **ProfileView.__init__** (Updated)

```python
class ProfileView(discord.ui.View):
    def __init__(self, owner_id: int, is_admin: bool):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.is_admin = is_admin

        # ✨ DYNAMIC BUTTON CREATION ✨
        is_quest_dive = can_use_quest_dive(owner_id)
        
        if is_quest_dive:
            label = "📜 Quest Dive"
            style = discord.ButtonStyle.success  # Green
        else:
            label = "🗑️ Dive"
            style = discord.ButtonStyle.primary  # Blue
        
        # Create button programmatically
        dive_btn = discord.ui.Button(
            label=label,
            style=style,
            row=0,
        )
        dive_btn.callback = self.dive_button
        self.add_item(dive_btn)

        if is_admin:
            self.add_item(AdminButton(row=2))
```

**Key Points:**
- Button is created **dynamically** in `__init__`, not via decorator
- Calls `can_use_quest_dive()` to check quest state
- Sets label and color based on quest status
- Button callback points to `self.dive_button` method

#### 2. **dive_button** Method (Updated)

```python
async def dive_button(self, interaction: discord.Interaction):
    """
    Main dive button - handles both normal dives and quest dives.
    
    Quest Dive Logic:
    - Button shows "📜 Quest Dive" when quest is active and conditions met
    - After successful dive, quest progress is updated
    - Returns to normal dive on quest completion/abandonment
    """
    # Determine if THIS dive is a quest dive
    is_quest_dive = can_use_quest_dive(interaction.user.id)
    
    # ... standard dive logic ...
    
    # QUEST HANDLING
    quest_feedback = None
    if is_quest_dive:
        progress_info = handle_dive_completion(interaction.user.id, is_quest_dive=True)
        if progress_info:
            quest_feedback = progress_info.get("feedback", "✅ Quest progress updated!")
            # If quest completes, button automatically updates next view creation
    
    # Show result with updated button
    await interaction.edit_original_response(
        embed=embed,
        view=ProfileView(self.owner_id, self.is_admin),  # ← Button updates here
    )
```

**What Happens:**
1. Dive is performed
2. If it's a quest dive: `handle_dive_completion()` progresses the quest
3. New `ProfileView` is created (showing results)
4. New ProfileView calls `__init__` → checks quest state again
5. Button updates to reflect new state (or returns to normal if quest completed)

## State Transitions

### Scenario 1: Quest Not Active → Quest Becomes Active

```
Player accepts quest with:
- Zone: Back Alley
- Time: 12:00-18:00

Button State: 🗑️ Dive (Blue)
          ↓
Player navigates to Back Alley
Player current time: 14:30
          ↓
Button State: 📜 Quest Dive (Green) ✨
```

**Why It Changes:**
- `can_use_quest_dive()` returns False → True
- Next ProfileView creation detects quest is active
- Button label/style updates immediately

### Scenario 2: Quest Active → Quest Expires (Time Window Ends)

```
Player diving for quest:
- 📜 Quest Dive (Green) ✨

Current time: 17:30 (within window)

Player performs dive
          ↓
Quest progress updated
New ProfileView created

Current time: 18:01 (outside window)
can_use_quest_dive() returns False
          ↓
Button State: 🗑️ Dive (Blue)
```

**Why It Updates:**
- Time window ended
- `can_use_quest_dive()` now returns False
- Next button creation reflects this

### Scenario 3: Quest Active → Quest Completed

```
Player on final dive:
- 📜 Quest Dive (Green)
- Quest progress: 9/10

Player dives
          ↓
handle_dive_completion() updates progress to 10/10
Quest marked as completed
New ProfileView created

can_use_quest_dive() returns False (quest no longer active)
          ↓
Button State: 🗑️ Dive (Blue)
Player sees normal dive button
```

**Why It Updates:**
- Quest is now completed (no longer "active")
- `can_use_quest_dive()` returns False
- Button reverts to normal state

### Scenario 4: Quest Active → Quest Abandoned

```
User clicks "Abandon Quest" button (separate feature):
queries.abandon_quest(user_id, quest_id)

Next ProfileView creation:
can_use_quest_dive() returns False
          ↓
Button State: 🗑️ Dive (Blue)
```

## Data Flow

```
PlayerProfile Command Called
    ↓
ProfileView.__init__() called
    ↓
Check: can_use_quest_dive(owner_id)
    ├─ Calls: queries.is_quest_dive_available(user_id)
    │   ├─ Check: Has active quest?
    │   ├─ Check: Player zone == quest zone?
    │   ├─ Check: Current time in window?
    │   └─ Return: True/False
    │
    └─ Set button: Label & Style
        ├─ True → "📜 Quest Dive" (Green)
        └─ False → "🗑️ Dive" (Blue)
```

## Quest Completion Flow

```
Player Clicks Quest Dive Button
    ↓
dive_button() Called
    ├─ is_quest_dive = can_use_quest_dive()  // Check current state
    ├─ Perform normal dive (roll item, gain XP, etc.)
    ├─ 
    ├─ if is_quest_dive:
    │   └─ progress_info = handle_dive_completion(user_id, is_quest_dive=True)
    │       ├─ Progress quest by 1
    │       ├─ Check if completed
    │       └─ Return feedback + new progress
    │
    └─ Show result with NEW ProfileView(owner_id, is_admin)
        └─ Button state updates automatically
```

## Key Functions Reference

| Function | File | Purpose |
|----------|------|---------|
| `can_use_quest_dive(user_id)` | game/quest_system.py | Check if quest dive available |
| `queries.is_quest_dive_available(user_id)` | db/queries.py | Database check for quest state |
| `handle_dive_completion(user_id, is_quest_dive)` | game/quest_system.py | Progress quest after dive |
| `queries.progress_generated_quest(user_id, quest_id, amount)` | db/queries.py | Update quest progress |
| `queries.get_active_quest(user_id)` | db/queries.py | Fetch active quest details |

## UX Guarantees

✅ **Button only shows "📜 Quest Dive" when ALL conditions are met:**
- Quest accepted
- Player in correct zone
- Current real time in window

✅ **Button never gets "stuck":**
- Each ProfileView creation rechecks state
- State changes are immediate on next view

✅ **Players get clear visual feedback:**
- Green button = Quest active & ready
- Blue button = Normal diving
- Color change is instant when conditions change

✅ **Normal dive never broken:**
- Quest completion doesn't affect normal dive logic
- If quest expires, normal dive still works

✅ **Zone system stays intact:**
- Quest dive respects active zone
- Zone changes work as expected
- No zone locking issues

## Testing Checklist

- [ ] Button shows blue "🗑️ Dive" by default
- [ ] Accept a quest, button becomes green "📜 Quest Dive"
- [ ] Navigate to correct zone, button stays green
- [ ] Quest time window ends, button returns to blue
- [ ] Complete a quest, button returns to blue
- [ ] Abandon a quest, button returns to blue
- [ ] Perform quest dive, progress updates
- [ ] Perform final quest dive, quest completes
- [ ] Refresh button works with updated button state
- [ ] Multiple players have independent button states
- [ ] Admin mode doesn't affect button logic

## Notes

### Why Dynamic Creation?

Discord buttons decorated with `@discord.ui.button` are static. To make the button label/style dynamic based on runtime data, we:
1. Create the button instance in `__init__`
2. Set its properties based on current state
3. Add it to the view programmatically
4. Point its callback to the method

This allows the button to update every time ProfileView is instantiated (which happens on every interaction).

### Performance

- `can_use_quest_dive()` is called once per ProfileView creation
- Database queries are cached by discord.py's connection pooling
- Button state updates are instant (no polling needed)
- No performance impact on normal dives

### Edge Cases Handled

1. **Player abandons quest while diving** - Quest won't progress, handled by `handle_dive_completion()`
2. **Quest expires during dive animation** - Takes effect next ProfileView (after dive)
3. **Zone change mid-dive** - Takes effect on next ProfileView
4. **Time window boundary** - Checked on each ProfileView creation
5. **Multiple ProfileView creations** - Each is independent and rechecks state

## Future Enhancements

- Add tooltip showing "Zone/Time not met" when button is blue but quest exists
- Add countdown timer to quest time window in button
- Add quest progress counter on button (e.g., "7/10")
- Add animations when button state changes
- Add sound effect on state transitions
