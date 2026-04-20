# IMPLEMENTATION CHECKLIST
## Step-by-Step Guide to Convert Discord Game to Web Game

---

## ⏱️ ESTIMATED TIMELINE
- **Phase 1 (Config)**: 15 minutes
- **Phase 2 (Backend)**: 2-3 hours
- **Phase 3 (Frontend)**: 1-2 hours
- **Phase 4 (Testing)**: 1 hour
- **Phase 5 (Deployment)**: 1 hour
- **TOTAL**: ~6-8 hours of actual coding

---

## ✅ PHASE 1: SETUP (15 min)

### Step 1.1: Update config.py
- [ ] Open `config.py`
- [ ] Add these lines at the end:
```python
WEB_API_PORT = int(os.getenv("WEB_API_PORT", "8000"))
WEB_FRONTEND_URL = os.getenv("WEB_FRONTEND_URL", "http://localhost:3000")
CORS_ORIGINS = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8000",
    WEB_FRONTEND_URL,
]
```
- [ ] Update .env file with:
```
WEB_API_PORT=8000
WEB_FRONTEND_URL=http://localhost:3000
```

### Step 1.2: Update requirements.txt
- [ ] Open `requirements.txt`
- [ ] Add these lines:
```
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
python-multipart==0.0.6
```
- [ ] Run: `pip install -r requirements.txt`

### Step 1.3: Verify Game Logic Has No Discord Deps
- [ ] Check `game/helpers.py` - should have NO `import discord`
- [ ] Check `game/leveling.py` - should have NO `import discord`
- [ ] Check `game/data.py` - should have NO `import discord`
- [ ] Check `db/queries.py` - should have NO `import discord`
✅ They should all be clean!

---

## ✅ PHASE 2: BACKEND API (2-3 hours)

### Step 2.1: Create api/ folder structure
```bash
mkdir -p api/routes
touch api/__init__.py
touch api/routes/__init__.py
```

### Step 2.2: Create api/main.py
- [ ] Create file: `api/main.py`
- [ ] Copy code from CODE_TRANSFORMATION_GUIDE.md "Create: api/main.py"
- [ ] Run: `python -m uvicorn api.main:app --reload`
- [ ] Test: Open http://localhost:8000/docs (Swagger UI should appear)
- [ ] ✅ You should see "Swagger UI" with endpoints

### Step 2.3: Create api/schemas.py
- [ ] Create file: `api/schemas.py`
- [ ] Copy code from CODE_TRANSFORMATION_GUIDE.md "Create: api/schemas.py"
- [ ] These are just data models - no errors expected

### Step 2.4: Create api/routes/auth.py
- [ ] Create file: `api/routes/auth.py`
- [ ] Copy code from CODE_TRANSFORMATION_GUIDE.md "Create: api/routes/auth.py"
- [ ] Test with curl:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testplayer"}'
```
- [ ] ✅ Should return: `{"status": "success", "user_id": ..., "player": {...}}`

### Step 2.5: Create api/routes/player.py
- [ ] Create file: `api/routes/player.py`
- [ ] Copy code from CODE_TRANSFORMATION_GUIDE.md "Create: api/routes/player.py"
- [ ] Test:
```bash
curl http://localhost:8000/api/player/USER_ID_FROM_ABOVE
```
- [ ] ✅ Should return player data

### Step 2.6: Create api/routes/dive.py
- [ ] Create file: `api/routes/dive.py`
- [ ] Copy code from CODE_TRANSFORMATION_GUIDE.md "Create: api/routes/dive.py"
- [ ] Important: Make sure it calls `game.helpers.roll_item_for_zone()` and `db.queries.*`
- [ ] Test:
```bash
curl -X POST http://localhost:8000/api/dive/start \
  -H "Content-Type: application/json" \
  -d '{"user_id": USER_ID}'
```
- [ ] ✅ Should return dive results with item found, XP gained, etc

### Step 2.7: Create api/routes/inventory.py
- [ ] Create file: `api/routes/inventory.py`
- [ ] Copy code from CODE_TRANSFORMATION_GUIDE.md "Create: api/routes/inventory.py"

### Step 2.8: Create api/routes/museum.py
- [ ] Create file: `api/routes/museum.py`
- [ ] Copy code from CODE_TRANSFORMATION_GUIDE.md "Create: api/routes/museum.py"

### Step 2.9: Create api/routes/admin.py
- [ ] Create file: `api/routes/admin.py`
- [ ] Copy code from CODE_TRANSFORMATION_GUIDE.md "Create: api/routes/admin.py"

### Step 2.10: Test All API Endpoints
Run this script to test everything:
```bash
#!/bin/bash
API="http://localhost:8000/api"

# Test 1: Login
echo "Test 1: Login"
LOGIN=$(curl -s -X POST $API/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser"}')
USER_ID=$(echo $LOGIN | grep -o '"user_id":[0-9]*' | grep -o '[0-9]*')
echo "User ID: $USER_ID"

# Test 2: Get Player
echo "Test 2: Get Player"
curl -s $API/player/$USER_ID | python -m json.tool

# Test 3: Start Dive
echo "Test 3: Start Dive"
curl -s -X POST $API/dive/start \
  -H "Content-Type: application/json" \
  -d "{\"user_id\": $USER_ID}" | python -m json.tool

# Test 4: Get Inventory
echo "Test 4: Get Inventory"
curl -s $API/player/$USER_ID/inventory | python -m json.tool

echo "All tests complete!"
```

- [ ] ✅ All endpoints return JSON without errors

---

## ✅ PHASE 3: WEB FRONTEND (1-2 hours)

### Step 3.1: Create web/ folder
```bash
mkdir -p web
touch web/index.html
touch web/styles.css
touch web/app.js
```

### Step 3.2: Create web/index.html
- [ ] Create file: `web/index.html`
- [ ] Copy code from CODE_TRANSFORMATION_GUIDE.md "Create: web/index.html"

### Step 3.3: Create web/styles.css
- [ ] Create file: `web/styles.css`
- [ ] Copy code from CODE_TRANSFORMATION_GUIDE.md "Create: web/styles.css"

### Step 3.4: Create web/app.js
- [ ] Create file: `web/app.js`
- [ ] Copy code from CODE_TRANSFORMATION_GUIDE.md "Create: web/app.js"
- [ ] Edit line: `const API_URL = "http://localhost:8000/api";`
  - Change if running on different server

### Step 3.5: Serve Web Frontend
Option A - Simple HTTP Server:
```bash
cd web
python -m http.server 3000
```

Option B - Python web server:
```bash
cd web
python -m http.server --bind 127.0.0.1 3000
```

- [ ] Open http://localhost:3000 in browser
- [ ] ✅ You should see the Trashbound home screen

### Step 3.6: Test Web Frontend
- [ ] Click "Play as Guest"
- [ ] ✅ Should redirect to profile page
- [ ] Click "🗑️ Dive"
- [ ] ✅ Should show dive result (item found, coins, XP)
- [ ] Click "Back to Profile"
- [ ] ✅ Should show updated stats

---

## ✅ PHASE 4: VERIFY DISCORD BOT STILL WORKS (30 min)

### Step 4.1: Run Discord Bot
```bash
python bot.py
```

- [ ] Bot starts without errors
- [ ] Bot connects to Discord
- [ ] Use `/profile` command
- [ ] ✅ Should work exactly as before

### Step 4.2: Run Both Simultaneously
Keep 3 terminals open:
```
Terminal 1: python bot.py
Terminal 2: python -m uvicorn api.main:app --reload
Terminal 3: cd web && python -m http.server 3000
```

- [ ] Use `/profile` in Discord
- [ ] ✅ Works perfectly
- [ ] Use web frontend at http://localhost:3000
- [ ] ✅ Works perfectly
- [ ] Check database - both update same tables
- [ ] ✅ Player progress syncs between Discord and web

---

## ✅ PHASE 5: DEPLOYMENT (1 hour)

### Step 5.1: Deploy to Railway

#### Option A: Deploy Discord Bot (existing)
```bash
# In Railway dashboard:
# - Connect GitHub repo
# - Set DISCORD_TOKEN, GUILD_ID env vars
# - Run: python bot.py
```

#### Option B: Deploy Web Backend to Railway
```bash
# In Railway dashboard:
# - Connect GitHub repo
# - Set DATABASE_URL, WEB_API_PORT env vars
# - Run: python -m uvicorn api.main:app --host 0.0.0.0 --port $WEB_API_PORT
```

#### Option C: Deploy Web Frontend to Netlify
```bash
# In Netlify dashboard:
# - Connect GitHub repo
# - Set build command: echo "No build needed"
# - Set publish directory: web
# - Update web/app.js: const API_URL = "https://YOUR_RAILWAY_URL/api"
```

### Step 5.2: Verify Deployments
- [ ] Discord bot works on Railway
- [ ] Web backend works on Railway
- [ ] Web frontend works on Netlify
- [ ] All connected to same PostgreSQL database
- [ ] ✅ Both can be used simultaneously

---

## 🎯 TESTING MATRIX

| Feature | Discord Bot | Web Frontend | Status |
|---------|------------|------------|--------|
| Login/Create Player | ✅ /profile | ✅ "Login" button | ✅ |
| View Profile | ✅ Embed | ✅ JSON | ✅ |
| Dive & Get Item | ✅ Button | ✅ "Dive" button | ✅ |
| Level Up | ✅ Works | ✅ Works | ✅ |
| Inventory | ✅ Works | ✅ Works | ✅ |
| Equipment | ✅ Works | ✅ Works | ✅ |
| Museum | ✅ Works | ✅ Works | ✅ |
| Admin Tools | ✅ Works | ✅ Works | ✅ |

---

## ⚠️ COMMON ISSUES & FIXES

### Issue: CORS Error when frontend calls API
**Error:** `Access to XMLHttpRequest blocked by CORS`
**Fix:** Make sure `api/main.py` has CORSMiddleware configured
```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)
```

### Issue: Database connection fails
**Error:** `psycopg.OperationalError: connection failed`
**Fix:** Verify DATABASE_URL is correct in .env or Railway

### Issue: API returns 404
**Error:** `{"detail": "Not Found"}`
**Fix:** Make sure all routers are included in api/main.py:
```python
app.include_router(auth.router, prefix="/api/auth")
app.include_router(player.router, prefix="/api/player")
# etc
```

### Issue: "Player not found" when logging in
**Error:** `{"detail": "Player not found"}`
**Fix:** Make sure `queries.ensure_player()` is called in auth.py before get_player()

---

## 📋 FINAL CHECKLIST

### Code Organization
- [ ] game/ folder has NO Discord imports
- [ ] db/ folder has NO Discord imports
- [ ] api/ folder created with all routes
- [ ] web/ folder created with HTML/CSS/JS
- [ ] config.py updated with WEB_* vars
- [ ] requirements.txt updated with FastAPI

### API Endpoints
- [ ] POST /api/auth/login
- [ ] POST /api/auth/guest
- [ ] GET /api/player/{id}
- [ ] GET /api/player/{id}/inventory
- [ ] POST /api/dive/start
- [ ] POST /api/inventory/equip
- [ ] POST /api/inventory/unequip
- [ ] GET /api/museum/{id}
- [ ] POST /api/admin/grant-xp (if needed)

### Web Frontend
- [ ] Home screen with Login/Guest buttons
- [ ] Profile screen showing stats
- [ ] Dive screen with results
- [ ] Inventory screen showing items
- [ ] Back buttons for navigation
- [ ] API calls work without CORS errors

### Testing
- [ ] Curl tests pass for all endpoints
- [ ] Web frontend works in browser
- [ ] Discord bot still works with /profile
- [ ] Both update same database
- [ ] Player progress syncs

### Deployment
- [ ] Discord bot deployed to Railway
- [ ] Web backend deployed to Railway
- [ ] Web frontend deployed to Netlify
- [ ] All use same PostgreSQL
- [ ] All work without errors

---

## 🚀 NEXT STEPS AFTER COMPLETION

1. **Add More Features**
   - Premium currency system
   - Leaderboards
   - Multiplayer battles
   - Social features

2. **Improve UI**
   - React frontend
   - Mobile app
   - Better styling
   - Animations

3. **Optimize Backend**
   - Caching with Redis
   - Database indexing
   - Rate limiting
   - Monitoring

4. **Scale**
   - Multi-server deployment
   - Load balancing
   - Database replication
   - CDN for static assets

---

## 📞 SUPPORT

If you get stuck:
1. Check REFACTORING_PLAN.md for architecture overview
2. Check CODE_TRANSFORMATION_GUIDE.md for exact code
3. Verify all imports are correct
4. Check that database is accessible
5. Use curl to test API endpoints directly
6. Check browser console for JavaScript errors

Good luck! 🎉
