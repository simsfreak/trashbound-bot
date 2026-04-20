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
