from fastapi import APIRouter, HTTPException
from db import queries
from config import ADMIN_USER_IDS
from game.leveling import apply_xp
from api.schemas import GrantXPRequest, GrantCoinsRequest, GrantTicketsRequest, GrantItemRequest, SuccessResponse

router = APIRouter()


def check_admin(admin_id: int):
    """Check if user is admin"""
    if admin_id not in ADMIN_USER_IDS:
        raise HTTPException(status_code=403, detail="Not authorized - admin only")


@router.post("/grant-xp", response_model=dict)
async def grant_xp(admin_id: int, request: GrantXPRequest):
    """Admin: Grant XP to player"""
    try:
        check_admin(admin_id)
        
        user_id = request.user_id
        xp_amount = request.xp_amount
        
        player = queries.get_player(user_id)
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        # Apply XP with potential level ups
        new_xp, new_level, leveled_up = apply_xp(
            current_xp=player.get("xp", 0),
            current_level=player.get("level", 1),
            gained_xp=xp_amount
        )
        
        # Update player
        queries.update_player_progress(
            user_id=user_id,
            coins=player.get("coins", 0),
            xp=new_xp,
            level=new_level,
            current_title=player.get("current_title", "Trasher"),
            total_dives=player.get("total_dives", 0)
        )
        
        return {
            "status": "success",
            "message": f"Granted {xp_amount} XP to player {user_id}",
            "new_level": new_level,
            "leveled_up": leveled_up
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error granting XP: {str(e)}")


@router.post("/grant-coins", response_model=dict)
async def grant_coins(admin_id: int, request: GrantCoinsRequest):
    """Admin: Grant coins to player"""
    try:
        check_admin(admin_id)
        
        user_id = request.user_id
        coins_amount = request.coins_amount
        
        player = queries.get_player(user_id)
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        new_coins = player.get("coins", 0) + coins_amount
        
        # Update player
        queries.update_player_progress(
            user_id=user_id,
            coins=new_coins,
            xp=player.get("xp", 0),
            level=player.get("level", 1),
            current_title=player.get("current_title", "Trasher"),
            total_dives=player.get("total_dives", 0)
        )
        
        return {
            "status": "success",
            "message": f"Granted {coins_amount} coins to player {user_id}",
            "new_coins": new_coins
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error granting coins: {str(e)}")


@router.post("/grant-tickets", response_model=dict)
async def grant_tickets(admin_id: int, request: GrantTicketsRequest):
    """Admin: Grant dirty tickets to player"""
    try:
        check_admin(admin_id)
        
        user_id = request.user_id
        tickets_amount = request.tickets_amount
        
        player = queries.get_player(user_id)
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        # Use queries function to grant tickets
        success = queries.grant_player_tickets(user_id, tickets_amount)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to grant tickets")
        
        return {
            "status": "success",
            "message": f"Granted {tickets_amount} dirty tickets to player {user_id}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error granting tickets: {str(e)}")


@router.post("/grant-item", response_model=dict)
async def grant_item(admin_id: int, request: GrantItemRequest):
    """Admin: Grant item to player"""
    try:
        check_admin(admin_id)
        
        user_id = request.user_id
        item_id = request.item_id
        quantity = request.quantity
        
        player = queries.get_player(user_id)
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        # Add item to inventory
        queries.add_item_to_inventory(user_id, item_id, quantity)
        
        return {
            "status": "success",
            "message": f"Granted {quantity}x {item_id} to player {user_id}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error granting item: {str(e)}")
