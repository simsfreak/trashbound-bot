# Web Game Refactoring Plan - Detailed Analysis

## COMPLETE FILE CLASSIFICATION

### 📋 DISCORD INTERFACE LAYER (UI Only - Keep for Bot, Create API Equivalents for Web)

| File | Purpose | Discord Deps | Action | Target | Keep For Discord? |
|------|---------|--------------|--------|--------|-------------------|
| **bot.py** | Bot init, slash sync, ready handler | discord.py, discord.ext.commands | Refactor: Extract init, add mode flag | Keep bot.py as-is OR create api/main.py alongside | ✅ YES |
| **cogs/profile.py** | /profile slash command | discord, app_commands | Refactor: Create API endpoint /api/player/profile | api/routes/player.py | ✅ YES |
| **ui/views.py** | Buttons, select menus, view handlers | discord.ui | KEEP as-is: Only used by Discord bot | Keep ui/views.py | ✅ YES |
| **ui/embeds.py** | Embed rendering | discord.Embed | KEEP as-is: Only used by Discord bot | Keep ui/embeds.py | ✅ YES |
| **ui/modals.py** | Modal forms | discord.ui.Modal | KEEP as-is: Only used by Discord bot | Keep ui/modals.py | ✅ YES |

---

### 🎮 GAME LOGIC (Pure Functions - No Changes, Reuse for Both)

| File | Purpose | Discord Deps | Lines | Status | Action |
|------|---------|--------------|-------|--------|--------|
| **game/data.py** | Item defs, zones, collections | ❌ NONE | ~900 | ✅ PERFECT | Import in api/services.py |
| **game/helpers.py** | Dice rolls, bonuses, calcs | ❌ NONE | ~300 | ✅ PERFECT | Import in api/services.py |
| **game/leveling.py** | XP->Level math | ❌ NONE | ~15 | ✅ PERFECT | Import in api/services.py |
| **game/rarities.py** | Rarity emoji/color data | ❌ NONE | ~40 | ✅ PERFECT | Import in api/services.py |

**Action:** Zero changes needed. These are already perfect for reuse.

---

### 💾 DATABASE LAYER (Shared - Used by Both Bot & Web)

| File | Purpose | Discord Deps | Status | Action |
|------|---------|--------------|--------|--------|
| **db/database.py** | PostgreSQL schema, connection pool | ❌ NONE | ✅ REUSABLE | Keep as-is, use in api/ |
| **db/queries.py** | All player/item/game queries | ❌ NONE | ✅ REUSABLE | Keep as-is, use in api/ |

**Action:** Zero changes. These work perfectly for both Discord bot and web backend.

---

### ⚙️ CONFIG

| File | Purpose | Updates Needed | Status |
|------|---------|-----------------|--------|
| **config.py** | Discord token, guild ID, admin IDs | ✅ ADD: API_PORT, FRONTEND_URL, DATABASE_URL, WEB_MODE | UPDATE |
| **requirements.txt** | Dependencies | ✅ ADD: fastapi, uvicorn, pydantic, python-cors | UPDATE |

---

## 🚀 STEP-BY-STEP REFACTORING ROADMAP

### ✅ PHASE 1: Verify Game Logic Separation (Check Current State)
**Status:** Already done! ✅
- ✅ game/data.py has NO discord imports
- ✅ game/helpers.py has NO discord imports  
- ✅ game/leveling.py has NO discord imports
- ✅ db/queries.py has NO discord imports (only db/database)
- ✅ db/database.py has NO discord imports

**Action:** NOTHING - Proceed to Phase 2

---

### 📝 PHASE 2: Update Config & Dependencies (15 min)
**Create new environment variables:**
```
# Add to .env
WEB_API_PORT=8000
WEB_FRONTEND_URL=http://localhost:3000
DATABASE_URL=postgresql://...  # Already exists
DISCORD_TOKEN=...              # Already exists
```

**Update requirements.txt:**
```
discord.py==2.3.2           # Keep
fastapi==0.104.1            # NEW
uvicorn==0.24.0             # NEW
pydantic==2.5.0             # NEW
python-multipart==0.0.6     # NEW
python-cors==4.0.0          # NEW
psycopg==3.1.12             # Already there
```

---

### 🔧 PHASE 3: Create Backend API Layer (2-3 hours)

**Create folder structure:**
```
api/
├── __init__.py
├── main.py                    # FastAPI app + startup
├── schemas.py                 # Pydantic models for requests/responses
├── services.py                # Business logic (calls game/helpers + db/queries)
└── routes/
    ├── __init__.py
    ├── auth.py               # POST /api/login, POST /api/guest
    ├── player.py             # GET /api/player, GET /api/player/{id}
    ├── dive.py               # POST /api/dive, GET /api/dive/result
    ├── inventory.py          # GET /api/inventory, POST /api/equip
    ├── museum.py             # GET /api/museum, GET /api/collections
    └── admin.py              # POST /api/admin/grant-xp, etc
```

**Key Principles:**
- Each route file handles ONE feature area
- Each route calls functions from game/helpers.py OR db/queries.py
- NO game logic in routes - only API input/output handling
- Use Pydantic schemas to validate input
- Return JSON, not Discord embeds

---

### 🎨 PHASE 4: Create Web Frontend (2-3 hours)

**Create folder structure:**
```
web/
├── index.html               # Single-page HTML
├── styles.css               # Styling
├── app.js                   # Vanilla JS (or React if preferred)
└── assets/                  # UI images, icons
```

**Simple Vanilla JS approach:**
- One HTML page with divs for each screen (home, profile, dive, inventory)
- app.js controls which div is visible
- Fetch API calls to http://localhost:8000/api/...
- Update UI based on JSON responses

**Alternative React approach:**
```
web/
├── package.json
├── public/index.html
└── src/
    ├── App.jsx
    ├── pages/
    │   ├── Home.jsx
    │   ├── Profile.jsx
    │   ├── Dive.jsx
    │   └── Inventory.jsx
    └── api.js               # Axios/fetch wrapper
```

---

### 📱 PHASE 5: Keep Discord Bot Working (No Changes)
- bot.py stays exactly the same
- All Discord UI/commands stay exactly the same
- Both bot.py and api/main.py use same database
- Both use same game/helpers.py logic

---

## 📊 DEPENDENCY MAP

**What imports what (for web backend):**
```
api/main.py
├── fastapi
├── uvicorn
├── api/routes/         (all route files)
└── config.py

api/routes/dive.py
├── db.queries          (get_player, add_item, update_progress, etc)
├── game.helpers        (roll_item_for_zone, calculate_equipment_bonuses, etc)
├── game.data           (ZONES, ITEMS, get_live_events, etc)
├── game.leveling       (apply_xp, xp_to_next_level)
└── api.schemas         (request/response models)

api/services.py
├── db.queries
├── game.helpers
├── game.data
└── game.leveling
```

**Database stays the same:**
```
Both api/main.py and bot.py
└── db/queries.py
    └── db/database.py
        └── PostgreSQL
```

---

## 🎯 CONCRETE EXAMPLES

### Example 1: Converting /dive Command to API

**CURRENT (Discord):**
```python
# In cogs/profile.py or ui/views.py
@discord.ui.button(label="🗑️ Dive")
async def dive_button(self, interaction: discord.Interaction):
    # Hundreds of lines of Discord-specific code
    # Calls game.helpers.roll_item_for_zone()
    # Calls db.queries.add_item_to_inventory()
    # Renders discord.Embed with results
    # Sends interaction reply
```

**NEW API ENDPOINT:**
```python
# In api/routes/dive.py
@router.post("/api/dive")
async def start_dive(user_id: int):
    # Get player
    player = queries.get_player(user_id)
    
    # Call game logic (SAME CODE)
    item_id, item = helpers.roll_item_for_zone(
        player["current_zone_id"],
        rare_bonus=...
    )
    
    # Calculate rewards (SAME CODE)
    gained_xp = apply_xp(...)
    gained_coins = int(...)
    
    # Save to database (SAME CODE)
    queries.add_item_to_inventory(...)
    queries.update_player_progress(...)
    
    # Return JSON (NOT Discord embed)
    return {
        "player_id": user_id,
        "item_id": item_id,
        "item_name": item["name"],
        "gained_xp": gained_xp,
        "gained_coins": gained_coins,
        "new_level": player["level"],
        "status": "success"
    }
```

**Key difference:** Returns plain JSON, not Discord Embed

---

### Example 2: UI Layer stays separate

**Discord Bot still has:**
```python
# ui/views.py - STAYS 100% THE SAME
class ProfileView(discord.ui.View):
    @discord.ui.button(label="🗑️ Dive")
    async def dive_button(self, interaction):
        # Still makes game.helpers calls
        # Still calls db.queries
        # Renders discord.Embed
        # Sends as Discord message
```

**Web Frontend has:**
```javascript
// web/app.js - NEW
async function startDive(userId) {
    const response = await fetch('http://localhost:8000/api/dive', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({user_id: userId})
    });
    const data = await response.json();
    // Update HTML with data
    displayDiveResult(data);
}
```

---

## ⚠️ IMPORTANT: What NOT to Change

1. ❌ Do NOT rewrite game/helpers.py functions
2. ❌ Do NOT change database schema
3. ❌ Do NOT modify game/data.py item definitions
4. ❌ Do NOT change db/queries.py
5. ❌ Do NOT touch Discord bot UI/commands (unless you want to)
6. ❌ Do NOT duplicate game logic

**✅ ONLY:**
1. Create new api/ folder with routes
2. Create new web/ folder with frontend
3. Update config.py with new env vars
4. Update requirements.txt

---

## 🔄 Deployment Strategy

### Discord Bot (Existing)
```bash
# Railway:
python bot.py
```

### Web Backend (New)
```bash
# Railway:
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Web Frontend (New)
```bash
# Netlify/Vercel:
npm build
```

### Both can run simultaneously:
- Same PostgreSQL database
- Same game logic
- Different entry points (bot.py vs api/main.py)

---

## 📋 COMPLETION CHECKLIST

### Phase 1: Preparation
- [ ] Update config.py with new env vars
- [ ] Update requirements.txt with FastAPI deps
- [ ] Verify game/helpers.py has no Discord imports
- [ ] Verify db/queries.py works independently

### Phase 2: Backend API
- [ ] Create api/main.py
- [ ] Create api/schemas.py
- [ ] Create api/routes/auth.py (login/guest)
- [ ] Create api/routes/player.py (profile)
- [ ] Create api/routes/dive.py (main game loop)
- [ ] Create api/routes/inventory.py (items)
- [ ] Create api/routes/museum.py (collections)
- [ ] Test all endpoints with curl/Postman

### Phase 3: Frontend
- [ ] Create web/index.html
- [ ] Create web/app.js
- [ ] Implement login screen
- [ ] Implement profile/dashboard
- [ ] Implement dive screen
- [ ] Implement inventory screen
- [ ] Test with API backend

### Phase 4: Polish
- [ ] CORS configuration
- [ ] Error handling
- [ ] Input validation
- [ ] Session management
- [ ] Mobile responsive design
- [ ] Deployment testing

---

## 🆘 WHERE TO START

**Recommend this order:**
1. Read through this entire document
2. Create api/ folder structure
3. Create api/main.py (FastAPI setup)
4. Create api/schemas.py (Pydantic models)
5. Create api/routes/auth.py (simplest endpoint)
6. Create api/routes/player.py
7. Test endpoints with curl
8. Create web/index.html with basic UI
9. Connect web to API
10. Iterate on remaining routes

**Do NOT start with:**
- Rewriting game/helpers.py
- Changing database schema
- Modifying Discord bot

---

## 💡 KEY INSIGHTS

1. **Your code is already 80% ready** - game/helpers.py has zero Discord deps
2. **Database layer is already clean** - db/queries.py is import-ready
3. **This is mostly UI layer work** - Create API routes and web pages
4. **Both can coexist** - Discord bot and web backend share database
5. **Zero breaking changes** - Discord bot works exactly the same

This is a refactoring, not a rewrite. You're moving the UI layer, not the game engine.
