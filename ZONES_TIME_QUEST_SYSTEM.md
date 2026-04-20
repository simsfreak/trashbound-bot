# Zones, Time Phases, and Quest Requirements System

## Overview

This document explains how the immersive zone/time/quest system works together to create dynamic, session-based gameplay without real-world time constraints. The system allows players to accept quests anytime, but progress only counts when both zone AND time requirements are met.

---

## Time Phase System

### How It Works

The game uses a **session-based time system** with three phases, not tied to real-world time:

| Phase | Emoji | Probability | Description |
|-------|-------|-------------|-------------|
| **Morning** | 🌅 | 30% | Fresh dumpsters, bright light, easier to spot things |
| **Evening** | 🌆 | 30% | Golden hour, mixed light, moderate difficulty |
| **Night** | 🌙 | 40% | Dark, mysterious, rare items appear, hardest but rewarding |

### Phase Transitions

Players have two ways to change phases:

1. **Cycle (Sequential)**: 🌅 Morning → 🌆 Evening → 🌙 Night → 🌅 Morning...
   - Press ⏰ **Phase** button on profile
   - Shows transition message: "The world changes around you... 🌅 Morning → 🌆 Evening"

2. **Random**: Any phase can be chosen randomly
   - System uses weighted randomization (40% night preference)
   - Happens naturally during certain activities

### Phase Matching Logic

Time requirements are **flexible and intuitive**:
- Quest requires "morning" → player in "morning" = ✅ match
- Quest requires "any" or "all" → any phase = ✅ match
- Phase mismatch shows feedback: "⚠️ Time mismatch: Need 🌙 Night"

---

## Zone System

### The Four Zones

Players can only be in **one active zone at a time**:

| Zone | ID | Emoji | Vibe | Loot Type |
|------|----|----|------|-----------|
| **Back Alley** | `back_alley` | 🔍 | Urban, cramped, treasure among debris | Small items, vintage goods |
| **Apartment Bins** | `apartment_bins` | 🏢 | Residential, personal discards | Household items, quirky finds |
| **Restaurant Dumpster** | `restaurant_dumpster` | 🍽️ | Culinary, aromatic, sometimes gross | Food items, cookware, specialty goods |
| **Mall Rear Lot** | `mall_rear_lot` | 🛍️ | Retail, organized chaos, bulk items | Electronics, fashion, premium goods |

### Zone Persistence

- Zones are stored in `players.current_zone_id`
- Players keep their zone until they explicitly change it
- Zone affects what items are available in generated loot

### Changing Zones

*(Feature for future implementation - currently zones exist but zone-switching UI not yet built)*

---

## Quest Requirements

### Requirement Model

Every quest has TWO required conditions:

```
✅ Quest Accepted = Zone match AND Time match
```

- **Zone**: `zone_id` - which zone to be in
- **Time**: `time` - which phase(s) to be in

### Requirement Checking Flow

```
1. Player views quest
   → System checks: player_zone == quest_zone?
   → System checks: player_phase matches quest_phase?

2. Build feedback message:
   ✅ "All conditions met. Ready to start!"
   ⚠️ "Zone mismatch: Need Restaurant Dumpster"
   ⚠️ "Time mismatch: Need 🌙 Night"

3. Display in quest embed under "📍 Requirements" field

4. Player clicks "✅ Accept Quest"
   → Quest accepted regardless of conditions
   → If conditions not met: Show warning about progress

5. During progress update:
   → Check conditions again
   → Only increment progress if BOTH match
   → Provide feedback if conditions not met
```

### Player Experience

**Scenario: Player accepts unmet quest**

```
Player sees:
"⚠️ Zone mismatch: Need Back Alley
⚠️ Time mismatch: Need 🌙 Night"

Clicks "✅ Accept Quest" anyway

Gets confirmation:
"Quest Accepted! ✅
...
⚠️ Note: Progress will only count when the following conditions are met:
⚠️ Zone mismatch: Need Back Alley
⚠️ Time mismatch: Need 🌙 Night"

Player then:
1. Navigates to Back Alley (changes zone)
2. Cycles time to Night
3. Returns to quest panel to work on quest
4. Progress now counts because conditions are met
```

---

## Data Structure

### Database Schema

```sql
-- Players table
current_zone_id TEXT NOT NULL DEFAULT 'back_alley'
current_time_phase TEXT NOT NULL DEFAULT 'morning'

-- Quests (in game logic, not stored DB)
{
  "id": "quest_123",
  "name": "Quest Name",
  "zone_id": "back_alley",      -- Required zone
  "time": "morning",             -- Required phase
  "description": "Task details",
  "reward_coins": 50,
  "reward_tickets": 1,
  ...
}
```

### Query Functions

Key functions in `db/queries.py`:

```python
# Get current state
get_current_zone(user_id)           → str (zone_id)
get_current_time_phase(user_id)     → str (phase)

# Set current state
set_current_zone(user_id, zone_id)  → bool
set_current_time_phase(user_id, phase) → bool

# Transitions
cycle_time_phase(user_id)           → str (new phase)
randomize_time_phase(user_id)       → str (new phase)

# Initialization
initialize_player_time_and_zone(user_id, zone_id, phase) → None
```

---

## Implementation Details

### Time System Module

Location: `game/time_system.py`

Helper functions for phase management:

```python
get_phase_info(phase)              # Returns dict with metadata
get_phase_emoji(phase)             # Returns emoji
get_phase_name(phase)              # Returns full name
get_random_phase()                 # Returns random phase (40% night bias)
get_next_phase(current_phase)      # Returns next in cycle
is_phase_match(player_phase, quest_phase)  # Returns bool
get_phase_full_description(phase)  # Returns immersive flavor text
```

### Quest Display Integration

Location: `ui/views.py` - GeneratedQuestView class

```python
def build_embed(self, interaction: discord.Interaction = None) → discord.Embed:
    # Builds quest display
    # If interaction provided, includes requirement status field
    
    zone_match, time_match, feedback = self._get_requirement_status(interaction, quest)
    embed.add_field(name="📍 Requirements", value=feedback, inline=False)

def _get_requirement_status(self, interaction, quest) → tuple[bool, bool, str]:
    # Returns: (zone_match: bool, time_match: bool, feedback_text: str)
    # Checks if player's current zone/time match quest requirements
```

### UI Components

**Profile View** (shows player state):
- Display: 📍 **Zone** • 🌅 **Morning**
- Button: ⏰ **Phase** - Click to cycle to next phase

**Quest View** (shows quest requirements):
- Display: 📍 Requirements field with feedback
- Shows both needed AND what player currently has
- Updates dynamically when zone/phase changes

---

## Design Principles

### 1. **Immersion Over Mechanics**
- Phases feel like the world changing, not game difficulty settings
- Zones feel like different locations to explore, not arbitrary gating
- Requirements create narrative: "The back alley at night is where the rare stuff is"

### 2. **Player Agency**
- Players can always accept quests (no blocking)
- Players can always change zones/phases (freedom)
- Progress only counts when conditions met (consequences feel natural)

### 3. **Clear Communication**
- Requirement feedback uses consistent ✅/⚠️ indicators
- Shows required state AND current state side-by-side
- Warning messages explain how to make progress count

### 4. **Session-Based, Not Real-Time**
- No waiting for real-world time to pass
- Player controls when time/zone changes happen
- Creates infinite possibilities within a single play session

### 5. **Layered Progression**
- Easy quests: Often "all phases" in "any zone" (always progress)
- Medium quests: Specific phase but common zone
- Hard quests: Rare zone + specific phase combo (planning required)

---

## Future Enhancements

### Phase Two
- **Zone Switching UI**: Button or modal to change zones
- **Zone-Specific Loot**: Items only appear in matching zones
- **Phase-Specific Encounters**: Different events in different phases

### Phase Three
- **Time Duration**: Phases last X game actions, then auto-rotate
- **Phase Events**: Random events happen during phase transitions
- **Zone Maps**: Visual representation of zones player is in

### Long Term
- **Multi-Phase Quests**: "Find X in morning, then Y at night"
- **Zone Requirements for Progression**: Unlock new zones via leveling
- **Phase Bonuses**: +50% coins for night quests, etc.

---

## Testing Checklist

- [ ] Accept quest when all conditions met → shows ✅
- [ ] Accept quest when zone mismatches → shows ⚠️ + warning
- [ ] Accept quest when time mismatches → shows ⚠️ + warning
- [ ] Accept quest when both mismatch → shows both ⚠️
- [ ] Cycle phase → updates display in real-time
- [ ] Change zone → updates display (when UI implemented)
- [ ] Quest progress increments when conditions met
- [ ] Quest progress blocked when conditions not met

---

## Summary Table

| Element | Current State | Effect | Player Sees |
|---------|---------------|--------|------------|
| Time Phase | Stored in DB | Affects quest progress | 🌅/🌆/🌙 emoji in profile |
| Zone | Stored in DB | Affects loot & quest progress | 📍 in profile |
| Quest Accept | No validation | Always succeeds | ✅ Accepted! |
| Quest Progress | Validated | Only counts if conditions met | ✅ Progress updated OR ⚠️ Conditions not met |
| Requirements Display | Dynamic | Checks on every view | 📍 Requirements field in quest embed |

