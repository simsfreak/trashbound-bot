# Quest State Detection - Technical Reference

## Quest Active State Detection Summary

### Single Source of Truth

```
can_use_quest_dive(user_id)  ← All button decisions based on this
    ↓
queries.is_quest_dive_available(user_id)  ← Database validation
```

## Complete Detection Logic

### Level 1: `game/quest_system.py` - `can_use_quest_dive()`

```python
def can_use_quest_dive(user_id: int) -> bool:
    """
    Check if player can use Quest Dive mode.
    Quest Dive is available only if:
    1. Player has an active quest
    2. All activation conditions are met (zone + time)
    """
    return queries.is_quest_dive_available(user_id)
```

**Entry Point:** Simple wrapper that delegates to database query

---

### Level 2: `db/queries.py` - `is_quest_dive_available()`

This function checks THREE critical conditions:

```python
def is_quest_dive_available(user_id: int) -> bool:
    """
    Checks if a quest is truly active right now.
    
    Returns True ONLY if ALL conditions are met:
    1. Player has an active quest (quest_id not null, is_active=true)
    2. Player is in the quest's required zone
    3. Current real-world time is within the quest's time window
    """
    
    # Step 1: Get active quest
    active_quest = get_active_quest(user_id)
    if not active_quest:
        return False  # No active quest
    
    # Step 2: Get player's current zone
    player = get_player(user_id)
    player_zone_id = player["current_zone_id"]
    quest_zone_id = active_quest["zone_id"]
    
    if player_zone_id != quest_zone_id:
        return False  # Player not in quest zone
    
    # Step 3: Check time window
    time_start = active_quest["time_window_start"]  # e.g., "12:00"
    time_end = active_quest["time_window_end"]      # e.g., "18:00"
    
    return check_real_time_match(time_start, time_end)
```

---

### Level 3: `game/quest_system.py` - `check_real_time_match()`

Real-time validation logic:

```python
def check_real_time_match(time_window_start: str, time_window_end: str) -> bool:
    """
    Check if current real-world time falls within a time window.
    Time format: "HH:MM" (24-hour)
    
    Handles BOTH normal and overnight windows:
    - Normal: 12:00 - 18:00
    - Overnight: 22:00 - 06:00
    """
    now = datetime.now()
    current_time_str = now.strftime("%H:%M")
    
    # Parse times to minutes
    start_hour, start_min = map(int, time_window_start.split(":"))
    end_hour, end_min = map(int, time_window_end.split(":"))
    current_hour, current_min = map(int, current_time_str.split(":"))
    
    # Convert to minutes for comparison
    start_total = start_hour * 60 + start_min      # e.g., 720 (12:00)
    end_total = end_hour * 60 + end_min            # e.g., 1080 (18:00)
    current_total = current_hour * 60 + current_min # e.g., 870 (14:30)
    
    if start_total <= end_total:
        # NORMAL window (12:00 - 18:00)
        return start_total <= current_total <= end_total
    else:
        # OVERNIGHT window (22:00 - 06:00)
        # Valid if: time >= 22:00 OR time <= 06:00
        return current_total >= start_total or current_total <= end_total
```

---

## Three-Condition Truth Table

### Condition 1: Has Active Quest?

```
Checks: active_quest = queries.get_active_quest(user_id)

Returns True if:
✅ SELECT quest_id FROM generated_quests 
   WHERE user_id = ? 
   AND is_active = true 
   AND abandoned_at IS NULL
   AND completed_at IS NULL
   LIMIT 1

Returns False if:
❌ No quest found
❌ is_active = false
❌ abandoned_at IS NOT NULL
❌ completed_at IS NOT NULL
```

### Condition 2: Player in Quest Zone?

```
Checks: player.current_zone_id == active_quest.zone_id

Returns True if:
✅ SELECT current_zone_id FROM players WHERE user_id = ?
   ← Matches quest's zone_id

Returns False if:
❌ Zone IDs don't match
❌ Player hasn't set zone yet
```

### Condition 3: Current Time in Window?

```
Checks: is_time_between(now.time(), quest.time_start, quest.time_end)

Examples:

Quest: 12:00 - 18:00
✅ 12:00 - In window (start)
✅ 14:30 - In window (middle)
✅ 18:00 - In window (end)
❌ 11:59 - Before window
❌ 18:01 - After window

Quest: 22:00 - 06:00 (Overnight)
✅ 22:00 - In window (start, after midnight)
✅ 23:30 - In window (night)
✅ 00:30 - In window (after midnight)
✅ 04:00 - In window (morning)
✅ 06:00 - In window (end)
❌ 07:00 - After window
❌ 14:00 - During day (gap in overnight)
❌ 21:59 - Before window
```

---

## State Transition Diagram

```
┌─────────────────────────────────────────┐
│ Player Opens Profile                    │
│ ProfileView.__init__() called           │
└────────────┬────────────────────────────┘
             │
             v
┌─────────────────────────────────────────┐
│ Check: can_use_quest_dive(user_id)      │
│                                         │
│ ├─ queries.is_quest_dive_available()    │
│ │  ├─ Active quest?         → Condition 1
│ │  ├─ Correct zone?         → Condition 2
│ │  └─ Correct time?         → Condition 3
│ │                                       │
│ └─ Return: True/False                   │
└────────────┬────────────────────────────┘
             │
      ┌──────┴──────┐
      │             │
      v             v
    FALSE          TRUE
      │             │
      v             v
  🗑️ Dive      📜 Quest Dive
  Blue Button  Green Button
```

---

## When Button State Updates

### Automatic Updates (No Action Needed)

The button state rechecks and updates automatically in these scenarios:

1. **After every ProfileView creation**
   - Button recreated in `__init__`
   - Calls `can_use_quest_dive()` fresh
   - State reflects current conditions

2. **After every interaction**
   - Click any button → new ProfileView shown
   - Button rechecks state
   - Updates if conditions changed

3. **After player advances time phase**
   - Click ⏰ Phase button
   - Zone might have changed
   - New ProfileView rechecks

4. **After successful dive**
   - Dive completes
   - New ProfileView shown
   - Quest progress updated
   - Button reflects new state

### Examples of State Changing

```
EXAMPLE 1: Time Window Starts
─────────────────────────────
Quest: Back Alley, 12:00-18:00

11:59 AM: Button = 🗑️ Dive (Blue)
          can_use_quest_dive() = False
          (Time not in window)

12:00 PM: Button = 📜 Quest Dive (Green) ✨
          can_use_quest_dive() = True
          (Time now in window)

18:01 PM: Button = 🗑️ Dive (Blue)
          can_use_quest_dive() = False
          (Time window ended)


EXAMPLE 2: Player Changes Zone
───────────────────────────────
Quest: Back Alley, any time

At Back Alley: Button = 📜 Quest Dive (Green)
               can_use_quest_dive() = True

Click 🗺️ Zones → Select Apartment Bins

At Apartment: Button = 🗑️ Dive (Blue)
              can_use_quest_dive() = False
              (Zone mismatch)

Back to Back Alley (if time still valid):
              Button = 📜 Quest Dive (Green)
              can_use_quest_dive() = True


EXAMPLE 3: Quest Completion
─────────────────────────────
Progress: 9/10

Click Quest Dive → Dive happens
Progress: 10/10 ✨

New ProfileView created:
get_active_quest() = None (quest completed)
can_use_quest_dive() = False
Button = 🗑️ Dive (Blue)
```

---

## Database Queries Used

### Query 1: Check Active Quest

```sql
SELECT 
  quest_id, 
  zone_id, 
  time_window_start, 
  time_window_end,
  progress,
  target
FROM generated_quests
WHERE user_id = $1
  AND is_active = true
  AND abandoned_at IS NULL
  AND completed_at IS NULL
LIMIT 1
```

### Query 2: Get Player Zone

```sql
SELECT current_zone_id
FROM players
WHERE id = $1
```

### Query 3: Check Time in Window

```python
# No database query needed - pure datetime logic
now = datetime.now()
# Compare with quest.time_window_start and .time_window_end
```

---

## Pseudocode: Complete Flow

```
function build_profile():
    user_id = current_user.id
    
    # Create the view - button gets created here
    view = ProfileView(user_id, is_admin)
    
    # Inside ProfileView.__init__():
    quest_dive_active = can_use_quest_dive(user_id)
    
    if quest_dive_active:
        button_label = "📜 Quest Dive"
        button_color = GREEN
    else:
        button_label = "🗑️ Dive"
        button_color = BLUE
    
    dive_button = create_button(
        label = button_label,
        style = button_color,
        callback = self.dive_button
    )
    view.add_item(dive_button)
    
    # Show the view to user
    send_message(embed, view)


function on_dive_button_click(interaction):
    # Re-check current state
    is_quest_dive = can_use_quest_dive(interaction.user.id)
    
    # Perform dive logic
    item, xp, coins = roll_dive()
    
    # If it was a quest dive, progress it
    if is_quest_dive:
        quest_progress = handle_dive_completion(
            user_id=interaction.user.id,
            is_quest_dive=True
        )
        
        if quest_progress.completed:
            # Quest is done, button will be reset next view
            pass
    
    # Show results with fresh ProfileView
    new_view = ProfileView(user_id, is_admin)
    # ← Button state rechecked here automatically
    
    show_results(dive_result_embed, new_view)
```

---

## Summary Table

| Aspect | Details |
|--------|---------|
| **Detection Function** | `can_use_quest_dive(user_id)` |
| **Database Check** | `queries.is_quest_dive_available(user_id)` |
| **Conditions Required** | 3 (Active, Zone, Time) |
| **Update Frequency** | Every ProfileView creation |
| **Updates Automatic?** | Yes - no manual refresh needed |
| **Time Logic** | Handles normal + overnight windows |
| **Performance** | O(1) database queries, instant updates |
| **Breakable By** | Requires deliberately changing quest state (complete/abandon) |
