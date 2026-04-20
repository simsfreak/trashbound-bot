# Pawn Owner Event System - Complete Implementation

## 🎭 Overview

A dynamic event system that makes the Pawn Owner feel **alive**, **unpredictable**, and **emotionally engaging**. Creates rare, meaningful interactions beyond normal daily dialogue, with special events that require player commitment and action.

---

## 🎲 Event Types & Triggers

### Probability Distribution
Each time a player chats with the Pawn Owner:
- **80%** - Normal Chat (default dialogue)
- **15%** - Enhanced Interaction (better rewards)
- **5%** - Special Event: "The Ask" (high relationship only)

### Relationship Requirements
```
Event Type    | Min Relationship | Trigger Chance
Normal        | 0+               | 80% (always available)
Enhanced      | 2+               | 15% (unlocks at ♥♥)
Special       | 4+               | 5% (requires ♥♥♥♥)
```

---

## 🔮 Special Event: "The Ask"

### What Is It?
A **timed objective** where the Pawn Owner requests a specific item. Creates emotional investment through:
- Mysterious dialogue
- Real time pressure (24-hour deadline)
- Relationship consequences
- Exclusive rewards

### Six Possible Requests

| Request | Item | Difficulty | Reward | Exclusive |
|---------|------|-----------|--------|-----------|
| 🔍 **Pristine Glass** | Perfect glass pane | Medium | 400₲ + 3🎟 | Gold Ring |
| 🪙 **Era Coins** | 3 matching coins | Hard | 500₲ + 4🎟 | Deal Charm |
| 📸 **Polaroid** | Intact photo | Easy | 300₲ + 2🎟 | Memory Pendant |
| ⏰ **Working Watch** | Functioning timepiece | Medium | 350₲ + 3🎟 | Time Bracelet |
| 🧥 **Leather Jacket** | Real leather coat | Hard | 450₲ + 3🎟 | Vagrant Coat |
| 🎵 **Vinyl Record** | Playable record | Easy | 280₲ + 2🎟 | Music Box Key |

### Player Choices

#### Option 1: Accept ✅
- Status: "active" (timed countdown begins)
- Deadline: 24 hours from now
- Effect: Neutral relationship change (+0)
- Next steps: Player must find the item

#### Option 2: Refuse ❌
- Relationship penalty: **-2**
- Dialogue: Disappointed pawnbroker
- Status: Request discarded
- Feel: Betrayal of trust

### Outcomes

#### Success ✓
Player finds item and completes within 24 hours:
- Relationship gain: **+2** (respect earned)
- Reward: Coins + Tickets + **Exclusive Item**
- Dialogue: Pride and satisfaction
- Effect: Pawnbroker trusts you more

#### Failure ✗
Deadline passes without completion:
- Relationship penalty: **-7** (broken promise)
- Status: Request marked "failed"
- Dialogue: Profound disappointment
- Effect: Significant trust damage
- Recovery time: Multiple successful chats needed

---

## 🎁 Exclusive Rewards

Six unique items that **cannot be obtained elsewhere**:

### 1. **Pawnbroker's Gold Ring** 💍
- Rarity: Epic
- Effects: +8% coin gain, relationship boost
- Flavor: "The real deal. He only gives these out once in a blue moon."

### 2. **Cursed Deal Charm** 🔮
- Rarity: Legendary  
- Effects: +12% rare drop chance, +5% rare chance boost
- Flavor: "Sealed with a promise, blessed by chaos."

### 3. **Memory Keeper Pendant** 🔗
- Rarity: Rare
- Effects: +6% XP gain
- Flavor: "Someone's forgotten memory, now yours."

### 4. **Time Thief's Bracelet** ⏰
- Rarity: Epic
- Effects: Speed boost, +25% quest timer efficiency
- Flavor: "It stopped ticking but still works somehow."

### 5. **Vagrant King Coat** 👑
- Rarity: Legendary
- Effects: +10% extra item chance, zone respect
- Flavor: "Worn by someone who owned the alleys."

### 6. **Music Box Key** 🎵
- Rarity: Rare
- Effects: +15% morale boost
- Flavor: "Winds up a melody you almost remember."

---

## 💔 Relationship Mechanics

### Relationship Point Changes

| Event | Change | Notes |
|-------|--------|-------|
| Normal chat | 0 | Baseline (no change) |
| Enhanced (liked) | +1 | Good answer |
| Enhanced (disliked) | -1 | Poor answer |
| Accept The Ask | 0 | Neutral test of character |
| Refuse The Ask | -2 | Betrayal |
| Complete The Ask | +2 | Respect earned |
| Fail The Ask | -7 | Broken promise |

### Relationship Levels

```
Level  | Points | Status        | Unlocks
-------|--------|---------------|----------
0      | 0      | Stranger      | Basic chat
1      | 1-2    | Acquaintance  | Normal events
2      | 3-5    | Friend        | Enhanced events
3      | 6-9    | Close Ally    | Better chat rewards
4      | 10+    | Trusted Ally  | "The Ask" unlocked
```

---

## 🗄️ Database Schema

### `pawn_requests` Table

```sql
CREATE TABLE pawn_requests (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,           -- Player ID
    request_id TEXT NOT NULL,          -- "pristine_glass", etc.
    item_name TEXT NOT NULL,           -- Display name
    flavor TEXT NOT NULL,              -- Immersive description
    reward_coins INTEGER NOT NULL,     -- 280-500 coins
    reward_tickets INTEGER NOT NULL,   -- 2-4 tickets
    reward_exclusive TEXT,             -- Exclusive item ID
    difficulty TEXT NOT NULL,          -- "easy", "medium", "hard"
    status TEXT NOT NULL,              -- "pending_choice" → "active" → "completed"/"failed"
    deadline TIMESTAMP NOT NULL,       -- 24 hours from creation
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

### Status Flow

```
pending_choice  →  Player decides
   ↓
accepted/refused
   ↓
active  →  Player hunts for item (24h countdown)
   ↓
completed/failed  →  Reward/penalty applied
```

---

## 🎮 Player Flow

### Step 1: Chat with Pawn Owner
```
Player: "💬 Chat with Owner" button
↓
System: Check if already chatted today? (Daily limit)
```

### Step 2: Event Type Check
```
System: Roll 1-100
↓
80 = Normal chat        (existing dialogue)
15 = Enhanced chat      (better choices/rewards)
5  = Special event      (if relationship ≥ 4)
```

### Step 3: Special Event Triggers
```
IF event == "special" AND relationship ≥ 4:
  - Generate random request
  - Show "The Ask" UI with accept/refuse buttons
ELSE IF event == "enhanced":
  - Show enhanced dialogue choices
  - Better rewards if player chooses wisely
ELSE:
  - Show normal pawn chat
```

### Step 4: Player Decision
```
Accept The Ask:
  ✓ Request marked "active"
  ✓ 24-hour countdown begins
  ✓ Player hunts for item
  
Refuse The Ask:
  ✗ Relationship -2
  ✗ Request discarded
  
Complete The Ask:
  ✓ Item delivered
  ✓ Relationship +2
  ✓ Exclusive item awarded
  ✓ Coins + Tickets received

Fail The Ask:
  ✗ 24 hours elapsed
  ✗ Relationship -7
  ✗ Pawnbroker disappointed
```

---

## 🎭 Immersive Dialogue Examples

### Normal Chat Choices
- "Listen intently" → Liked ✓
- "Half-pay attention" → Disliked ✗

### Pawnbroker Reactions (Normal)
- ✓ "Heh. You get how this town works."
- ✗ "Nah. Soft answer."

### The Ask - Acceptance
- "Good. I knew you would."
- "That's all I needed to hear."
- "Then we have a deal, friend."

### The Ask - Refusal
- "I see." [turns away] "So that's how it is..."
- "Fine. Forget I asked." [But he won't forget.]
- [Looks at you like he's seeing you for the first time. Doesn't like it.]

### The Ask - Success
- "Ah. You came through. Not many do."
- "Well, I'll be damned. Color me impressed."
- "Perfect. Exactly what I needed."

### The Ask - Failure
- "So you couldn't get it." [disappointment]
- "Time's up." [Nothing more needed.]
- "The clock ran out, huh? I really thought you could do it."

---

## 🔧 Core Functions

### game/pawn_events.py

```python
# Event triggering
pick_event_type(relationship: int) -> str
  # Returns: "normal", "enhanced", or "special"

generate_special_event() -> dict
  # Creates a random "The Ask" request

# Dialogue helpers
get_random_acceptance_dialogue() -> str
get_random_refusal_dialogue() -> str
get_random_success_dialogue() -> str
get_random_failure_dialogue() -> str

# Relationship calculation
calculate_relationship_change(
    event_type: str,
    choice_liked: bool = None,
    ask_outcome: str = None
) -> int

# Reward data
get_exclusive_reward_data(reward_id: str) -> dict
```

### db/queries.py

```python
# Storage
store_pawn_request(user_id: int, request_data: dict) -> bool
get_active_pawn_request(user_id: int) -> dict | None

# Status updates
update_pawn_request_status(user_id, request_id, status) -> bool
complete_pawn_request(user_id, request_id, coins, tickets, exclusive) -> bool
fail_pawn_request(user_id, request_id) -> bool
```

---

## 🎨 UI Views

### 1. **PawnEventView**
Shows normal/enhanced event with dialogue choices
- 2 buttons for choices
- Back button
- Dynamic title based on event type

### 2. **TheAskView**
Shows special request
- ✅ Accept button (green)
- ❌ Refuse button (red)
- Back button
- Shows: Item name, time limit, rewards

### 3. **ActivePawnRequestView**
Shows ongoing request with countdown
- ⏱️ Time remaining (real-time)
- "I Have It!" button (mark complete)
- Back button
- Prevents leaving without progress check

---

## ⚙️ Integration Points

### Daily Chat Limit
```python
# In update_pawn_chat():
last_pawn_chat_date = CURRENT_DATE
# Resets each day, allows ONE chat per day
```

### Active Request Blocking
```python
# In chat_button():
IF active_request.status == "active":
  # Show countdown view instead of new event
```

### Relationship Tracking
```python
# All interactions update pawn_relationship:
queries.update_pawn_chat(
    user_id,
    relationship_delta=+1  # or -2, -7, etc.
)
```

---

## 🚀 Safety & Design

### No Interference with Existing Systems
- ✅ Normal quest system untouched
- ✅ Daily quest system untouched
- ✅ Zone diving untouched
- ✅ Inventory management untouched

### Graceful Degradation
- If player hasn't relationship 4+ → No special events
- If request fails → Marked "failed", new events can trigger
- If player cancels → Request discarded cleanly

### Player Agency
- Refuse option always available
- No forced progression
- Can retry after failing previous asks
- Rewards feel meaningful (exclusive items)

---

## 📊 Relationship Progression Example

```
Day 1: Start (0 relationship)
  → Normal chat: +0
  → Day 1 end: 0 relationship

Day 2: Enhanced chat available (2+ relationship)
  → Need to reach 2 first from better chats

Day 5: Reach relationship 4+
  → Unlock "The Ask"
  → Get request for "Pristine Glass"
  
Day 5: Accept request
  → 24-hour countdown starts
  → Hunt for item
  
Day 6: Find and deliver item
  → "The Ask" completed
  → Relationship +2 (now 6)
  → Reward: Gold Ring + 400 coins
  
Day 7: Pawnbroker respects you more
  → Next request might be harder
  → Exclusive rewards stack
```

---

## 🎯 Outcome

A quest system that:
- **Feels alive** - Events are unpredictable
- **Emotionally engaging** - Dialogue carries weight
- **Respects time** - 24-hour commitment meaningful
- **Rewards loyalty** - Exclusive items signal trust
- **Punishes betrayal** - Refusal/failure have real costs
- **Stays safe** - Doesn't break existing systems

**Result:** Players care about the Pawn Owner relationship. They make real choices. Rewards feel earned. The system feels less like a game mechanic and more like a real relationship.
