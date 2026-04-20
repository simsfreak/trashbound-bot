# CODE TRANSFORMATION GUIDE
## Exact Changes for Web Game Refactoring

---

## 📍 PART 1: KEEP EVERYTHING IN `/game/` FOLDER

### File: game/leveling.py
**Status:** ✅ KEEP AS-IS - NO CHANGES

```python
# This is PERFECT for web backend - pure math, no Discord
def xp_to_next_level(level: int) -> int:
    return 50 + (level * 25) + (level * level * 5)

def apply_xp(current_xp: int, current_level: int, gained_xp: int) -> tuple[int, int, bool]:
    xp = current_xp + gained_xp
    level = current_level
    leveled_up = False
    while xp >= xp_to_next_level(level):
        xp -= xp_to_next_level(level)
        level += 1
        leveled_up = True
    return xp, level, leveled_up
```

**Usage in web backend:**
```python
# In api/routes/dive.py
from game.leveling import apply_xp

new_xp, new_level, leveled_up = apply_xp(
    current_xp=player["xp"],
    current_level=player["level"],
    gained_xp=100
)
```

---

### File: game/helpers.py
**Status:** ✅ KEEP AS-IS - Functions like these are ready:

```python
# KEEP ALL THESE - They have NO Discord dependencies
def roll_item_for_zone(zone_id: str, rare_bonus: float = 0.0) -> tuple[str, dict]:
    # Pure game logic, no Discord

def calculate_equipment_bonuses(equipment_rows: list[dict]) -> dict[str, float]:
    # Pure calculation, no Discord

def perform_chaos_mix(inventory_rows: list[tuple[str, int]], extra_rare_bonus: float = 0.0) -> tuple[str, int] | None:
    # Pure logic, no Discord
```

**Usage in web backend:**
```python
# In api/routes/dive.py
from game.helpers import roll_item_for_zone, calculate_equipment_bonuses

item_id, item = roll_item_for_zone(zone_id="back_alley", rare_bonus=0.05)
bonuses = calculate_equipment_bonuses(equipment=[...])
```

---

### File: game/data.py
**Status:** ✅ KEEP AS-IS - Pure constants

```python
# KEEP ALL OF THIS - No Discord imports
ZONES = {...}
ITEMS = {...}
EQUIP_SLOTS = [...]
DAILY_QUEST_TEMPLATES = [...]
MUSEUM_COLLECTIONS = {...}
DIRTY_DRAW_POOL = [...]
```

**Usage in web backend:**
```python
# In api/routes/dive.py
from game.data import ZONES, ITEMS

zone_name = ZONES[player["current_zone_id"]]["name"]
item_data = ITEMS[item_id]
```

---

### File: game/rarities.py
**Status:** ✅ KEEP AS-IS - Pure emoji/color mapping

```python
# KEEP - No Discord dependencies
RARITY_BADGES = {...}
RARITY_FX = {...}
```

---

## 📍 PART 2: KEEP DATABASE LAYER AS-IS

### File: db/database.py
**Status:** ✅ KEEP AS-IS - No changes

```python
# This stays EXACTLY the same
# Both Discord bot AND web backend use this
from contextlib import contextmanager
import psycopg
from config import DATABASE_URL

@contextmanager
def get_conn():
    conn = psycopg.connect(DATABASE_URL)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def run_schema() -> None:
    # Runs database migrations
    with get_conn() as conn:
        # ... schema creation
```

---

### File: db/queries.py
**Status:** ✅ KEEP AS-IS - Already perfect for both!

```python
# These functions work for BOTH Discord bot and web backend
def get_player(user_id: int) -> dict | None:
    # ...

def add_item_to_inventory(user_id: int, item_id: str, quantity: int = 1) -> None:
    # ...

def update_player_progress(...) -> None:
    # ...

def get_inventory(user_id: int) -> list[tuple[str, int]]:
    # ...

# ALL OF THESE ARE READY FOR WEB USE - NO CHANGES NEEDED
```

**Usage in web backend:**
```python
# In api/routes/dive.py
from db import queries

player = queries.get_player(user_id)
queries.add_item_to_inventory(user_id, item_id, 1)
queries.update_player_progress(...)
```

---

## 📍 PART 3: DISCORD UI LAYER - KEEP AS-IS FOR BOT

### File: ui/views.py
**Status:** ✅ KEEP AS-IS - Only used by Discord bot

```python
# This STAYS - Discord bot uses it
# Web backend does NOT use this
class ProfileView(discord.ui.View):
    @discord.ui.button(label="🗑️ Dive")
    async def dive_button(self, interaction: discord.Interaction):
        # All this Discord-specific code stays
        # But now we can extract the logic to an API endpoint
```

**For web backend:** Don't import or use this at all

---

### File: ui/embeds.py
**Status:** ✅ KEEP AS-IS - Only used by Discord bot

```python
# This STAYS - Discord bot uses it for rendering
# Web backend creates JSON responses instead
def profile_embed(player, ...):
    # This returns discord.Embed - perfect for bot
    # Web backend doesn't need this
```

---

### File: ui/modals.py
**Status:** ✅ KEEP AS-IS - Only used by Discord bot

```python
# This STAYS - Discord bot uses it for forms
class GrantXPModal(discord.ui.Modal):
    # ...

# Web backend doesn't need modals - uses JSON validation instead
```

---

### File: cogs/profile.py
**Status:** ✅ KEEP AS-IS - Only used by Discord bot

```python
# This STAYS - Discord slash commands
@app_commands.command(name="profile")
async def profile(self, interaction: discord.Interaction):
    # Web backend has /api/player/profile instead
```

---

## 📍 PART 4: CONFIG - UPDATE

### File: config.py
**Status:** ⚠️ UPDATE - Add new variables

**CURRENT:**
```python
import os

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_USER_IDS = {257973526286434305}
```

**UPDATED:**
```python
import os

# Existing
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_USER_IDS = {257973526286434305}

# NEW - For web backend
WEB_API_PORT = int(os.getenv("WEB_API_PORT", "8000"))
WEB_FRONTEND_URL = os.getenv("WEB_FRONTEND_URL", "http://localhost:3000")
WEB_MODE = os.getenv("WEB_MODE", "false").lower() == "true"

# These are optional - only needed if both run simultaneously
CORS_ORIGINS = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:3001",
    WEB_FRONTEND_URL,
]
```

---

## 📍 PART 5: REQUIREMENTS.TXT - UPDATE

### Current:
```
discord.py==2.3.2
psycopg==3.1.12
python-dotenv==1.0.0
```

### Updated:
```
# Keep existing
discord.py==2.3.2
psycopg==3.1.12
python-dotenv==1.0.0

# Add for web backend
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
python-multipart==0.0.6
fastapi-cors==0.0.6
```

---

## 📍 PART 6: NEW - CREATE `/api` FOLDER

### Create: api/__init__.py
```python
# Empty file to make api a package
```

---

### Create: api/main.py
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import CORS_ORIGINS, WEB_API_PORT
from api.routes import auth, player, dive, inventory, museum, admin

# Initialize app
app = FastAPI(
    title="Trashbound Web API",
    description="Backend API for Trashbound game",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(player.router, prefix="/api/player", tags=["player"])
app.include_router(dive.router, prefix="/api/dive", tags=["dive"])
app.include_router(inventory.router, prefix="/api/inventory", tags=["inventory"])
app.include_router(museum.router, prefix="/api/museum", tags=["museum"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

@app.on_event("startup")
async def startup():
    # Run database schema on startup
    from db.database import run_schema
    run_schema()

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=WEB_API_PORT)
```

---

### Create: api/schemas.py
```python
from pydantic import BaseModel
from typing import Optional

# Request schemas (what client sends)
class LoginRequest(BaseModel):
    username: str

class DiveRequest(BaseModel):
    user_id: int

class EquipItemRequest(BaseModel):
    user_id: int
    item_id: str

class GrantXPRequest(BaseModel):
    user_id: int
    xp_amount: int

# Response schemas (what server returns)
class PlayerResponse(BaseModel):
    user_id: int
    username: str
    level: int
    xp: int
    coins: int
    dirty_tickets: int
    total_dives: int

class ItemResponse(BaseModel):
    item_id: str
    name: str
    rarity: str
    emoji: str
    coins: int
    xp: int

class DiveResultResponse(BaseModel):
    item_id: str
    item_name: str
    gained_xp: int
    gained_coins: int
    new_level: int
    leveled_up: bool
```

---

### Create: api/routes/__init__.py
```python
# Empty file
```

---

### Create: api/routes/auth.py
**EXAMPLE - Login/Guest:**

```python
from fastapi import APIRouter
from db import queries
from api.schemas import LoginRequest, PlayerResponse

router = APIRouter()

@router.post("/login")
async def login(request: LoginRequest):
    """Player login or create account"""
    user_id = hash(request.username) % (10**9)  # Generate ID from username
    
    # Ensure player exists in database
    queries.ensure_player(user_id, request.username)
    
    player = queries.get_player(user_id)
    return {
        "status": "success",
        "user_id": user_id,
        "player": PlayerResponse(**player)
    }

@router.post("/guest")
async def guest_login():
    """Create temporary guest account"""
    import uuid
    guest_id = int(uuid.uuid4().int % (10**9))
    guest_name = f"Guest_{guest_id}"
    
    queries.ensure_player(guest_id, guest_name)
    player = queries.get_player(guest_id)
    
    return {
        "status": "success",
        "user_id": guest_id,
        "player": PlayerResponse(**player)
    }
```

---

### Create: api/routes/player.py
**EXAMPLE - Get Player State:**

```python
from fastapi import APIRouter, HTTPException
from db import queries
from api.schemas import PlayerResponse

router = APIRouter()

@router.get("/{user_id}")
async def get_player(user_id: int):
    """Get full player profile"""
    player = queries.get_player(user_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    return PlayerResponse(**player)

@router.get("/{user_id}/inventory")
async def get_inventory(user_id: int):
    """Get player inventory"""
    inventory = queries.get_inventory(user_id)
    return {
        "user_id": user_id,
        "items": [{"item_id": item_id, "quantity": qty} for item_id, qty in inventory]
    }
```

---

### Create: api/routes/dive.py
**EXAMPLE - Main Game Action:**

```python
from fastapi import APIRouter, HTTPException
from db import queries
from game.helpers import roll_item_for_zone, calculate_equipment_bonuses
from game.leveling import apply_xp
from game.data import ITEMS, ZONES
from api.schemas import DiveResultResponse
import random

router = APIRouter()

@router.post("/start")
async def start_dive(user_id: int):
    """Execute a dive and return results"""
    player = queries.get_player(user_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # Get equipment bonuses (SAME LOGIC AS DISCORD BOT)
    equipment = queries.get_equipped_items(user_id)
    equipment_bonuses = calculate_equipment_bonuses(equipment)
    
    # Roll item (SAME LOGIC AS DISCORD BOT)
    item_id, item = roll_item_for_zone(
        player["current_zone_id"],
        rare_bonus=equipment_bonuses["drop_bonus"]
    )
    
    # Calculate rewards (SAME LOGIC AS DISCORD BOT)
    bonus_coins = 0  # Could roll random event here
    bonus_xp = 0
    gained_coins = int(item["coins"]) + bonus_coins
    gained_coins = int(gained_coins * (1 + equipment_bonuses["coin_boost"]))
    
    gained_xp = int(item["xp"]) + bonus_xp
    gained_xp = int(gained_xp * (1 + equipment_bonuses["xp_boost"]))
    
    # Apply XP and level up (SAME LOGIC AS DISCORD BOT)
    new_xp, new_level, leveled_up = apply_xp(player["xp"], player["level"], gained_xp)
    
    # Save to database (SAME QUERIES AS DISCORD BOT)
    new_coins = player["coins"] + gained_coins
    new_dives = player["total_dives"] + 1
    
    queries.add_item_to_inventory(user_id, item_id, 1)
    queries.update_player_progress(
        user_id=user_id,
        coins=new_coins,
        xp=new_xp,
        level=new_level,
        current_title=player["current_title"],  # Or calculate title
        total_dives=new_dives
    )
    queries.progress_daily_quest(user_id, "dive_count", 1)
    
    # Return JSON response (NOT Discord Embed)
    return {
        "status": "success",
        "item_id": item_id,
        "item_name": item["name"],
        "gained_xp": gained_xp,
        "gained_coins": gained_coins,
        "new_level": new_level,
        "leveled_up": leveled_up,
        "new_total_coins": new_coins
    }
```

---

### Create: api/routes/inventory.py
**EXAMPLE - Item Management:**

```python
from fastapi import APIRouter, HTTPException
from db import queries
from game.data import ITEMS

router = APIRouter()

@router.post("/equip")
async def equip_item(user_id: int, item_id: str):
    """Equip an item"""
    success = queries.equip_item(user_id, item_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to equip item")
    return {"status": "success", "message": f"Equipped {item_id}"}

@router.post("/unequip")
async def unequip_item(user_id: int, slot: str):
    """Unequip item from slot"""
    success = queries.unequip_item(user_id, slot)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to unequip item")
    return {"status": "success", "message": f"Unequipped from {slot}"}
```

---

### Create: api/routes/museum.py
```python
from fastapi import APIRouter
from db import queries
from game.helpers import get_next_incomplete_collection

router = APIRouter()

@router.get("/{user_id}")
async def get_museum(user_id: int):
    """Get museum data"""
    discovered = queries.get_discovered_item_ids(user_id)
    completed = queries.get_completed_collections(user_id)
    player = queries.get_player(user_id)
    
    return {
        "user_id": user_id,
        "museum_level": player.get("museum_level", 1),
        "museum_xp": player.get("museum_xp", 0),
        "discovered_items": list(discovered),
        "completed_collections": list(completed)
    }
```

---

### Create: api/routes/admin.py
```python
from fastapi import APIRouter, HTTPException
from db import queries
from config import ADMIN_USER_IDS

router = APIRouter()

@router.post("/grant-xp")
async def grant_xp(admin_id: int, user_id: int, xp_amount: int):
    """Admin: Grant XP to player"""
    if admin_id not in ADMIN_USER_IDS:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    success = queries.grant_player_xp(user_id, xp_amount)
    if not success:
        raise HTTPException(status_code=404, detail="Player not found")
    return {"status": "success", "message": f"Granted {xp_amount} XP"}
```

---

## 📍 PART 7: NEW - CREATE `/web` FOLDER

### Create: web/index.html
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trashbound Web</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div id="app">
        <!-- Home Screen -->
        <div id="screen-home" class="screen active">
            <h1>🗑️ Trashbound</h1>
            <button onclick="showLogin()">Login</button>
            <button onclick="startGuest()">Play as Guest</button>
        </div>

        <!-- Profile Screen -->
        <div id="screen-profile" class="screen">
            <h2>Profile</h2>
            <div id="player-info"></div>
            <button onclick="showDive()">🗑️ Dive</button>
            <button onclick="showInventory()">🎒 Inventory</button>
            <button onclick="logout()">Logout</button>
        </div>

        <!-- Dive Screen -->
        <div id="screen-dive" class="screen">
            <h2>Diving...</h2>
            <p id="dive-result"></p>
            <button onclick="showProfile()">Back to Profile</button>
        </div>

        <!-- Inventory Screen -->
        <div id="screen-inventory" class="screen">
            <h2>Inventory</h2>
            <div id="inventory-items"></div>
            <button onclick="showProfile()">Back</button>
        </div>
    </div>

    <script src="app.js"></script>
</body>
</html>
```

---

### Create: web/styles.css
```css
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: Arial, sans-serif;
    background-color: #1a1a1a;
    color: #fff;
    padding: 20px;
}

#app {
    max-width: 600px;
    margin: 0 auto;
}

.screen {
    display: none;
    padding: 20px;
    background-color: #222;
    border-radius: 8px;
    margin-bottom: 20px;
}

.screen.active {
    display: block;
}

h1, h2 {
    margin-bottom: 20px;
}

button {
    display: block;
    width: 100%;
    padding: 10px;
    margin: 10px 0;
    background-color: #5865F2;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 16px;
}

button:hover {
    background-color: #4752C4;
}

input {
    width: 100%;
    padding: 8px;
    margin: 8px 0;
    border: 1px solid #444;
    border-radius: 4px;
    background-color: #333;
    color: white;
}
```

---

### Create: web/app.js
```javascript
const API_URL = "http://localhost:8000/api";
let currentUserId = null;

// Screen Management
function showScreen(screenName) {
    document.querySelectorAll(".screen").forEach(s => s.classList.remove("active"));
    document.getElementById(`screen-${screenName}`).classList.add("active");
}

async function showLogin() {
    const username = prompt("Enter username:");
    if (!username) return;
    
    try {
        const response = await fetch(`${API_URL}/auth/login`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({username})
        });
        const data = await response.json();
        
        if (data.status === "success") {
            currentUserId = data.user_id;
            await showProfile();
        }
    } catch (error) {
        alert("Login failed: " + error.message);
    }
}

async function startGuest() {
    try {
        const response = await fetch(`${API_URL}/auth/guest`, {
            method: "POST"
        });
        const data = await response.json();
        
        if (data.status === "success") {
            currentUserId = data.user_id;
            await showProfile();
        }
    } catch (error) {
        alert("Guest login failed: " + error.message);
    }
}

async function showProfile() {
    if (!currentUserId) return;
    
    try {
        const response = await fetch(`${API_URL}/player/${currentUserId}`);
        const player = await response.json();
        
        const info = `
            Level: ${player.level}<br>
            XP: ${player.xp}<br>
            Coins: ${player.coins}<br>
            Dives: ${player.total_dives}
        `;
        document.getElementById("player-info").innerHTML = info;
        showScreen("profile");
    } catch (error) {
        alert("Failed to load profile: " + error.message);
    }
}

async function showDive() {
    showScreen("dive");
    
    try {
        const response = await fetch(`${API_URL}/dive/start`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({user_id: currentUserId})
        });
        const result = await response.json();
        
        if (result.status === "success") {
            const resultText = `
                Found: ${result.item_name}<br>
                Coins: +${result.gained_coins}<br>
                XP: +${result.gained_xp}<br>
                Level: ${result.new_level}
            `;
            document.getElementById("dive-result").innerHTML = resultText;
        }
    } catch (error) {
        alert("Dive failed: " + error.message);
    }
}

async function showInventory() {
    showScreen("inventory");
    
    try {
        const response = await fetch(`${API_URL}/player/${currentUserId}/inventory`);
        const data = await response.json();
        
        let html = "";
        data.items.forEach(item => {
            html += `<div>${item.item_id} x${item.quantity}</div>`;
        });
        document.getElementById("inventory-items").innerHTML = html;
    } catch (error) {
        alert("Failed to load inventory: " + error.message);
    }
}

function logout() {
    currentUserId = null;
    showScreen("home");
}
```

---

## 🎯 SUMMARY

| Component | Location | Status | Action |
|-----------|----------|--------|--------|
| Game Logic | game/ | ✅ Keep | Import in api/routes/ |
| Database | db/ | ✅ Keep | Use as-is |
| Discord UI | ui/ + cogs/ | ✅ Keep | Don't touch |
| Config | config.py | ⚠️ Update | Add WEB_* vars |
| Dependencies | requirements.txt | ⚠️ Update | Add FastAPI |
| Backend API | api/ | ✨ NEW | Create |
| Web Frontend | web/ | ✨ NEW | Create |

---

## 🚀 RUN BOTH SIMULTANEOUSLY

**Terminal 1 - Discord Bot (existing):**
```bash
python bot.py
```

**Terminal 2 - Web Backend (new):**
```bash
python -m uvicorn api.main:app --reload
```

**Terminal 3 - Web Frontend (optional):**
```bash
# If using simple HTML/JS
python -m http.server 3000 --directory web

# Or if using React
npm start
```

Both use the same PostgreSQL database. Same gameplay rules. Both are identical except for UI layer.
