# Quest State Synchronization - Visual Summary

## Quick Reference

### Button State Rules

#### ProfileView Dive Button
```
No quest active:           [🗑️ Dive] (Blue)
Quest accepted:            [🗑️ Dive] (Blue) - waiting for conditions
Quest active + conditions: [📜 Quest Dive] (Green) ✨
Quest completed/abandoned: [🗑️ Dive] (Blue) - reset
```

#### GeneratedQuestView Accept Button
```
No quest active:              [✅ Accept] (Enabled)
This quest is active:         [❌ Abort] (Red) - enabled
Other quest is active:        [✅ Accept] (Disabled/Greyed)
```

### State Indicators
```
🟢 Green indicator   = This quest is currently active
🔒 Lock indicator    = Another quest is active, can't accept
✅ Check indicator   = Ready to accept
❌ Red indicator     = Abort/danger action
```

---

## Complete User Flow Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                    START: No Quest Active                       │
│                   Dive Button: [🗑️ Dive]                       │
└────────────────────────────────────────────────────────────────┘
                              │
                     [🎯 Quests button]
                              │
                              ↓
┌────────────────────────────────────────────────────────────────┐
│              GeneratedQuestView: Browse Quests                  │
│         All quests show: [✅ Accept] (enabled)                 │
│         Status: No active quest                                 │
└────────────────────────────────────────────────────────────────┘
                              │
                    [✅ Accept Quest]
                              │
                              ↓
           ┌──────────────────────────────────────┐
           │ queries.set_active_quest()           │
           │ • Deactivate previous (if any)       │
           │ • Set is_active = TRUE               │
           │ • Update player.active_quest_id      │
           └──────────────────────────────────────┘
                              │
                              ↓
┌────────────────────────────────────────────────────────────────┐
│            Quest Accepted Message                               │
│         ✅ Quest Accepted!                                     │
│         🟢 This quest is currently active!                     │
│         [❌ Abort Quest] button now visible                    │
│                                                                 │
│         IF conditions met: ✅ Conditions Met!                  │
│         IF conditions not met: ⚠️ Progress won't count until   │
│                                    zone/time correct           │
└────────────────────────────────────────────────────────────────┘
                    │                     │
                    │                     │
          [Abort Quest]           [🏠 Back to Profile]
            │                             │
            ↓                             ↓
    ABANDON FLOW              QUEST ACTIVE FLOW
            │                             │
            │        ┌────────────────────┘
            │        │
            │        ↓
            │   ┌─────────────────────────────────────────────┐
            │   │ Profile with Quest Active                  │
            │   │ Dive Button: [📜 Quest Dive] (Green) ✨    │
            │   │  (if zone + time conditions met)           │
            │   │                                             │
            │   │ OR                                           │
            │   │ Dive Button: [🗑️ Dive] (Blue)             │
            │   │  (if conditions NOT met, quest waiting)    │
            │   └─────────────────────────────────────────────┘
            │        │
            │        ├─→ [📜 Quest Dive]
            │        │    ├─ Dive completes
            │        │    ├─ Progress +1
            │        │    ├─ If progress >= target:
            │        │    │   Quest completed ✨
            │        │    │   get_active_quest() returns None
            │        │    └─ Next ProfileView shows [🗑️ Dive]
            │        │
            │        └─→ [🗑️ Dive]
            │             (waiting for correct zone/time)
            │
            ↓
    ┌────────────────────────────────────────────────┐
    │ queries.abandon_quest()                        │
    │ • Set is_active = FALSE                        │
    │ • Set abandoned_at = NOW()                     │
    │ • Reset progress = 0                           │
    │ • Clear player.active_quest_id = NULL          │
    └────────────────────────────────────────────────┘
            │
            ↓
    ┌────────────────────────────────────────────────┐
    │ Quest Abandoned Message                        │
    │ ✋ Quest Abandoned                              │
    │ Dive button returned to normal                 │
    └────────────────────────────────────────────────┘
            │
            ↓
    [🏠 Back to Profile]
            │
            ↓
    ┌────────────────────────────────────────────────┐
    │ Profile: Quest Reset                           │
    │ Dive Button: [🗑️ Dive] (Blue)                 │
    │ (Returns to normal state)                      │
    └────────────────────────────────────────────────┘
```

---

## Quest Browse State During Active Quest

```
┌──────────────────────────────────────────────────────┐
│         GeneratedQuestView: Another Quest Active     │
│                                                      │
│  Current Viewing: Quest #1 (NOT the active quest)   │
│  ┌─────────────────────────────────────────────┐   │
│  │ ⚔️ Quest #1 - Mystery Mission               │   │
│  │ 📍 Back Alley • 🌆 Evening • ♥♥♡♡♡         │   │
│  │ 💰 200 coins                                │   │
│  │ 🔒 Status: Another quest is active         │   │
│  │             Abort it first to accept this   │   │
│  │ [✅ Accept] (GREYED OUT/DISABLED)          │   │
│  └─────────────────────────────────────────────┘   │
│                                                      │
│  [🎲 Next] → Cycle to different quest              │
│                                                      │
│  Eventually view the ACTIVE quest:                 │
│  ┌─────────────────────────────────────────────┐   │
│  │ ⚔️ Quest #4 - Treasure Hunt                  │   │
│  │ 📍 Apartment Bins • 🌅 Morning • ♥♥♥♡♡     │   │
│  │ 💰 350 coins                                │   │
│  │ 🟢 Status: This quest is currently active! │   │
│  │           Click [❌ Abort Quest] to abandon │   │
│  │ [❌ Abort Quest] (ENABLED, RED)            │   │
│  └─────────────────────────────────────────────┘   │
│                                                      │
│  [🎲 Next] → Continue browsing                     │
└──────────────────────────────────────────────────────┘
```

---

## Timeout & Expiration Handling

```
Quest Active but:
├─ Time window ends
│  └─ next ProfileView creation:
│     └─ can_use_quest_dive() returns False
│        └─ [📜 Quest Dive] → [🗑️ Dive]
│
├─ Zone changed away
│  └─ next ProfileView creation:
│     └─ can_use_quest_dive() returns False
│        └─ [📜 Quest Dive] → [🗑️ Dive]
│
└─ Quest expires (24h timeout)
   └─ database marks expired
      └─ get_active_quest() returns None
         └─ [📜 Quest Dive] → [🗑️ Dive]
```

---

## Database State Tracking

### What Gets Stored

```
generated_quests table:
├─ quest_id           (identifier)
├─ user_id            (owner)
├─ is_active           (TRUE/FALSE) ← KEY
├─ is_completed        (TRUE/FALSE)
├─ abandoned_at        (timestamp or NULL)
├─ completed_at        (timestamp or NULL)
├─ progress            (0-target)
├─ target              (completion threshold)
├─ expires_at          (time limit)
└─ generated_at        (when created)

players table:
└─ active_quest_id     (quest_id or NULL) ← Tracking reference
```

### State Queries

```
Is quest active?
→ SELECT * FROM generated_quests
  WHERE user_id = ? AND is_active = TRUE
  LIMIT 1

Can player use Quest Dive?
→ SELECT *  FROM generated_quests
  WHERE user_id = ? AND is_active = TRUE
  AND zone_id = player.current_zone
  AND time window matches

Clear on abandon:
→ UPDATE generated_quests
  SET is_active = FALSE, abandoned_at = NOW()
  WHERE user_id = ? AND quest_id = ?
```

---

## UI Synchronization Points

```
Every ProfileView Creation:
├─ __init__() called
├─ can_use_quest_dive() checks:
│  ├─ Is quest active?
│  ├─ Player in correct zone?
│  └─ Current time in window?
└─ Button set based on result

Every GeneratedQuestView Creation:
├─ __init__() called
├─ queries.get_active_quest() called
├─ self.active_quest_id set
└─ Buttons/UI reflect state

Every Interaction (button click):
├─ New view created
├─ State rechecked from DB
└─ UI updated to match current state
```

---

## Summary Table

| State | Dive Button | Accept Btn | Abort Btn | Visual |
|-------|-------------|-----------|-----------|--------|
| **No quest** | 🗑️ Dive | ✅ All | ❌ None | Normal |
| **Quest accepted, conditions not met** | 🗑️ Dive | 🔒 This | ❌ None | Waiting |
| **Quest active, conditions met** | 📜 Quest Dive | 🔒 This | ✅ This | Active |
| **Other quest browsed while active** | 🗑️ Dive | 🔒 Other | ❌ Other | Locked |
| **Quest completed** | 🗑️ Dive | ✅ All | ❌ None | Normal |
| **Quest abandoned** | 🗑️ Dive | ✅ All | ❌ None | Normal |

---

## Key Implementation Details

### Accept Button Click Flow
```
[✅ Accept Quest] clicked
    │
    ├─ Check: is another quest active?
    │  └─ If yes: show error, return
    │
    ├─ Call: queries.set_active_quest(user_id, quest_id)
    │  └─ Deactivates others, activates this
    │
    ├─ Update: self.active_quest_id = quest_id
    │
    └─ Show: "✅ Quest Accepted!"
       └─ Next view shows quest as active
```

### Abort Button Click Flow
```
[❌ Abort Quest] clicked
    │
    ├─ Call: queries.abandon_quest(user_id)
    │  ├─ Sets is_active = FALSE
    │  ├─ Sets abandoned_at = NOW()
    │  └─ Clears player.active_quest_id
    │
    ├─ Update: self.active_quest_id = None
    │
    └─ Show: "✋ Quest Abandoned"
       └─ Next ProfileView shows normal Dive button
```

### Profile View Button Update
```
ProfileView created
    │
    ├─ Call: can_use_quest_dive(owner_id)
    │  └─ Returns: True/False
    │
    └─ If True:
       ├─ Label: "📜 Quest Dive"
       └─ Style: Green (Success)
       
    └─ If False:
       ├─ Label: "🗑️ Dive"
       └─ Style: Blue (Primary)
```

---

## Complete Synchronization Checklist

- ✅ Accept quest stores in database
- ✅ GeneratedQuestView tracks active_quest_id
- ✅ ProfileView checks quest state on creation
- ✅ Dive button updates automatically
- ✅ Browse UI shows accept/abort correctly
- ✅ Other quests disabled when one active
- ✅ Abort clears everything
- ✅ Completion auto-resets button
- ✅ No stale state issues
- ✅ All interactions rechecked from DB
