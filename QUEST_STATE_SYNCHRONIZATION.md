# Quest State Synchronization - Complete Implementation

## Overview

The quest system now has full state synchronization across all UI elements. Once a player accepts a quest, every component reflects that state consistently until the quest is abandoned or completed.

## Architecture

### Three-Layer Synchronization

```
Database Layer (db/queries.py)
├─ set_active_quest(user_id, quest_id)      ← Accept quest
├─ abandon_quest(user_id, quest_id)         ← Abort quest
├─ get_active_quest(user_id)                ← Check current state
└─ Progress tracking (auto-resets on abort)

UI Layer (ui/views.py)
├─ GeneratedQuestView:
│  ├─ Shows [✅ Accept] for available quests
│  ├─ Shows [❌ Abort] for active quest
│  └─ Disables other quests when one active
│
└─ ProfileView:
   ├─ [🗑️ Dive] when no quest active
   └─ [📜 Quest Dive] when quest active + conditions met

Application State
└─ self.active_quest_id tracks current active quest in view
```

## User Flow

### 1. Accept Quest

```
Player in GeneratedQuestView:
  ├─ Views available quests
  └─ Clicks [✅ Accept Quest] on desired quest
        │
        ↓
  Calls: queries.set_active_quest(user_id, quest_id)
        │
        ├─ Deactivates any previous active quest
        ├─ Sets this quest as is_active = TRUE
        └─ Updates player.active_quest_id
        │
        ↓
  View Updates:
  ├─ self.active_quest_id = quest_id
  ├─ Shows success message
  └─ Next quest browsing shows:
     • "🟢 This quest is currently active!"
     • Other quests: "🔒 Cannot accept until this is abandoned"
     │
     ↓
  Player Goes to Profile:
  └─ [🗑️ Dive] → [📜 Quest Dive] (if conditions met)
```

### 2. Browse While Quest Active

```
Player clicks [🎯 Quests] while quest active:
  │
  ├─ GeneratedQuestView.__init__()
  │  └─ Calls: queries.get_active_quest(owner_id)
  │     └─ Sets: self.active_quest_id = "quest_12345"
  │
  └─ When viewing active quest:
     ├─ Shows:  "🟢 This quest is currently active!"
     ├─ Shows:  "[❌ Abort Quest]" button
     └─ Shows:  "[✅ Accept Quest]" button is HIDDEN/DISABLED
  
  When viewing OTHER quests:
     ├─ Shows:  "🔒 Another quest is active"
     ├─ Shows:  "[✅ Accept Quest]" button is DISABLED/GRAYED
     └─ Clicking shows: "Cannot accept until active is abandoned"
```

### 3. Abort Quest

```
Player clicks [❌ Abort Quest] on active quest:
  │
  ├─ Calls: queries.abandon_quest(user_id)
  │  ├─ Sets: is_active = FALSE
  │  ├─ Sets: abandoned_at = NOW()
  │  ├─ Clears: player.active_quest_id = NULL
  │  └─ Resets: progress to 0
  │
  ├─ View Updates:
  │  ├─ self.active_quest_id = None
  │  ├─ Shows: "✋ Quest Abandoned"
  │  └─ Shows: "Dive button returned to normal"
  │
  └─ Profile Updates on Next Visit:
     ├─ [📜 Quest Dive] → [🗑️ Dive] (automatically)
     └─ Button rechecks quest state
```

### 4. Quest Completion

```
Player completes quest (progress >= target):
  │
  ├─ handle_dive_completion() marks quest complete
  │  └─ progress_generated_quest() finishes
  │
  ├─ queries.get_active_quest() returns NULL
  │  (because completed quests excluded from active query)
  │
  └─ Next Profile Visit:
     ├─ ProfileView.__init__() checks quest state
     ├─ can_use_quest_dive() returns False
     └─ [📜 Quest Dive] → [🗑️ Dive] (automatically)
```

## Code Implementation

### GeneratedQuestView.__init__()

```python
def __init__(self, owner_id: int, is_admin: bool):
    super().__init__(timeout=300)
    self.owner_id = owner_id
    self.is_admin = is_admin
    self.current_quest_index = 0
    self.quests = []
    
    # Track active quest to show correct buttons/state
    self.active_quest_id = None
    active_quest = queries.get_active_quest(owner_id)
    if active_quest:
        self.active_quest_id = active_quest["quest_id"]
```

### Accept Quest Button

```python
@discord.ui.button(label="✅ Accept Quest", style=discord.ButtonStyle.primary, row=0)
async def accept_quest_button(self, interaction, button):
    quest = self._get_current_quest()
    
    # Prevent accepting multiple quests
    if self.active_quest_id and quest["quest_id"] != self.active_quest_id:
        # Show: "Another quest is active. Abort it first."
        return
    
    # Accept quest in database
    if queries.set_active_quest(interaction.user.id, quest["quest_id"]):
        self.active_quest_id = quest["quest_id"]
        # Show success message
        # Button state will update on next view
```

### Abort Quest Button

```python
@discord.ui.button(label="❌ Abort Quest", style=discord.ButtonStyle.danger, row=0)
async def abort_quest_button(self, interaction, button):
    if queries.abandon_quest(interaction.user.id):
        self.active_quest_id = None
        # Show: "Quest Abandoned. Dive button returned to normal."
        # Next ProfileView creation will show [🗑️ Dive] again
```

### Embed State Display

```python
def build_embed(self, interaction):
    # ... quest details ...
    
    # Show quest state based on active_quest_id
    if self.active_quest_id and quest["quest_id"] == self.active_quest_id:
        embed.add_field(
            name="🟢 Status",
            value="**This quest is currently active!**\nClick [❌ Abort Quest] to abandon it.",
            inline=False
        )
    elif self.active_quest_id:
        embed.add_field(
            name="🔒 Status",
            value="Another quest is currently active. Abort it first to accept this one.",
            inline=False
        )
```

### ProfileView Dynamic Button

```python
class ProfileView(discord.ui.View):
    def __init__(self, owner_id: int, is_admin: bool):
        super().__init__(timeout=300)
        
        # Check if quest is TRULY active
        is_quest_dive = can_use_quest_dive(owner_id)
        
        if is_quest_dive:
            label = "📜 Quest Dive"     # Green
            style = discord.ButtonStyle.success
        else:
            label = "🗑️ Dive"          # Blue
            style = discord.ButtonStyle.primary
        
        # Button updates automatically next time view is created
```

## State Transitions

### Visual State Map

```
┌─────────────────────────────────┐
│ No Quest Selected               │
│ • Dive button: [🗑️ Dive]       │
│ • GeneratedQuestView shows:     │
│   [✅ Accept] on all quests    │
└──────────────┬──────────────────┘
               │ Player clicks [✅ Accept]
               ↓
┌─────────────────────────────────┐
│ Quest Accepted (not active yet) │
│ • Dive button: [🗑️ Dive]       │
│ • GeneratedQuestView shows:     │
│   🟢 Active: [❌ Abort]        │
│   🔒 Other:  [❌ Disabled]     │
└──────────────┬──────────────────┘
               │ Player moves to correct zone
               │ Current time in window
               ↓
┌─────────────────────────────────┐
│ Quest ACTIVE                    │
│ • Dive button: [📜 Quest Dive] │
│ • GeneratedQuestView shows:     │
│   🟢 Active: [❌ Abort]        │
│   🔒 Other:  [❌ Disabled]     │
└──────────────┬──────────────────┘
         ↙            ↘
    [❌ Abort]   [Complete]
        ↓            ↓
    Abandoned    Completed
        ↓            ↓
    [🗑️ Dive]   [🗑️ Dive]
    (normal)     (normal)
```

## Database Changes Required

No new database changes needed! Existing functions used:
- `queries.set_active_quest(user_id, quest_id)` - Sets active quest
- `queries.abandon_quest(user_id)` - Clears active quest
- `queries.get_active_quest(user_id)` - Fetches active quest

### What `set_active_quest` Does:

```sql
-- 1. Deactivate previous active quest
UPDATE generated_quests
SET is_active = FALSE
WHERE user_id = $1 AND is_active = TRUE

-- 2. Activate new quest
UPDATE generated_quests
SET is_active = TRUE
WHERE user_id = $1 AND quest_id = $2

-- 3. Update player's tracking
UPDATE players
SET active_quest_id = $2
WHERE user_id = $1
```

### What `abandon_quest` Does:

```sql
-- 1. Deactivate quest
UPDATE generated_quests
SET is_active = FALSE,
    abandoned_at = NOW(),
    progress = 0
WHERE user_id = $1 AND quest_id = $2

-- 2. Clear player's tracking
UPDATE players
SET active_quest_id = NULL
WHERE user_id = $1
```

## Synchronization Guarantees

### ✅ Only One Active Quest

- `set_active_quest` deactivates all others before setting new one
- `get_active_quest` only returns quests with `is_active = TRUE`
- UI tracks `self.active_quest_id` for instant feedback

### ✅ Button Always Reflects State

- ProfileView checks quest state on EVERY creation
- GeneratedQuestView checks on__init__
- No stale state = button always correct

### ✅ Abort Clears Everything

- Clears `is_active` flag
- Sets `abandoned_at` timestamp
- Resets progress to 0
- Clears `player.active_quest_id`
- Buttons auto-update on next view

### ✅ Completion Resets State

- Quest marked `is_completed = TRUE`
- `get_active_quest()` only returns non-completed quests
- ProfileView automatically shows normal Dive button

## Testing Scenarios

### Scenario 1: Accept → View Profile → Dive
```
1. [🎯 Quests] → View quest → [✅ Accept]
   ✓ Message shows acceptance
   ✓ self.active_quest_id = quest_id

2. [🏠 Back] → Profile view created
   ✓ ProfileView.__init__ checks quest state
   ✓ Button changes to [📜 Quest Dive] (if conditions met)
   ✓ [📜 Quest Dive] button visible

3. [📜 Quest Dive] → Dive completes
   ✓ Progress updates
   ✓ New ProfileView created
   ✓ Button state rechecks
```

### Scenario 2: Abort Quest
```
1. [🎯 Quests] while quest active
   ✓ Shows "🟢 This quest is active"
   ✓ [❌ Abort Quest] button visible

2. [❌ Abort Quest]
   ✓ calls queries.abandon_quest()
   ✓ self.active_quest_id = None
   ✓ Message: "Quest Abandoned"

3. [🏠 Back] → Profile
   ✓ ProfileView checks quest
   ✓ get_active_quest() returns None
   ✓ Button changes to [🗑️ Dive]
```

### Scenario 3: Browse Other Quests When One Active
```
1. [🎯 Quests] with active quest
   ✓ self.active_quest_id = "active_quest_id"

2. [🎲 Next] to view other quest
   ✓ Shows: "🔒 Another quest is active"
   ✓ [✅ Accept] button is disabled/greyed
   ✓ Clicking shows error message

3. Return to active quest with [🎲 Next]
   ✓ Shows: "🟢 This quest is active"
   ✓ [❌ Abort Quest] button visible
   ✓ Shows abort option
```

## Edge Cases Handled

| Scenario | Behavior |
|----------|----------|
| **Quest expires by time** | `get_active_quest()` excluded by `expires_at` check |
| **Quest completed** | `is_completed = TRUE` excluded from active query |
| **Multiple buttons clicked** | Database enforces only 1 active at a time |
| **Page reload mid-quest** | `active_quest_id` rechecked from DB on view creation |
| **Browser tab left open** | Next interaction rechecks DB state |
| **Complete while browsing** | `get_active_quest()` returns None, button resets |

## Performance Notes

- **Single database query** per view: `get_active_quest()`
- **Instant UI feedback** via `self.active_quest_id` tracking
- **No polling needed** - state checked on interaction
- **Zero impact** on normal dives

## Future Enhancements

Potential improvements:
- [ ] Show progress countdown on quest in GeneratedQuestView
- [ ] Add quest expiration timer in UI
- [ ] Show "Quest almost done!" warning at 90% progress
- [ ] Add quest completion animation
- [ ] Track quest completion history
