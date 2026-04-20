from fastapi import APIRouter, HTTPException
from db import queries
from api.schemas import LoginRequest, PlayerResponse, SuccessResponse
import uuid

router = APIRouter()


@router.post("/login", response_model=dict)
async def login(request: LoginRequest):
    """Player login or create account"""
    try:
        # Generate user ID from username hash
        user_id = hash(request.username) % (10**9)
        
        # Ensure player exists in database
        queries.ensure_player(user_id, request.username)
        
        player = queries.get_player(user_id)
        if not player:
            raise HTTPException(status_code=500, detail="Failed to create player")
        
        return {
            "status": "success",
            "user_id": user_id,
            "player": PlayerResponse(**player)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Login failed: {str(e)}")


@router.post("/guest", response_model=dict)
async def guest_login():
    """Create temporary guest account"""
    try:
        # Generate unique guest ID
        guest_id = int(uuid.uuid4().int % (10**9))
        guest_name = f"Guest_{guest_id}"
        
        queries.ensure_player(guest_id, guest_name)
        player = queries.get_player(guest_id)
        
        if not player:
            raise HTTPException(status_code=500, detail="Failed to create guest account")
        
        return {
            "status": "success",
            "user_id": guest_id,
            "player": PlayerResponse(**player)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Guest login failed: {str(e)}")
