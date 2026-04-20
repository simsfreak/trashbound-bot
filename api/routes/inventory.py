from fastapi import APIRouter, HTTPException
from db import queries
from api.schemas import EquipItemRequest, UnequipItemRequest, SuccessResponse

router = APIRouter()


@router.post("/equip", response_model=dict)
async def equip_item(request: EquipItemRequest):
    """Equip an item"""
    try:
        user_id = request.user_id
        item_id = request.item_id
        
        player = queries.get_player(user_id)
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        # Check if player owns the item
        inventory = queries.get_inventory(user_id)
        if not any(item[0] == item_id for item in inventory):
            raise HTTPException(status_code=400, detail="Item not in inventory")
        
        # Equip the item
        success = queries.equip_item(user_id, item_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to equip item")
        
        return {
            "status": "success",
            "message": f"Equipped {item_id}"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error equipping item: {str(e)}")


@router.post("/unequip", response_model=dict)
async def unequip_item(request: UnequipItemRequest):
    """Unequip item from slot"""
    try:
        user_id = request.user_id
        slot = request.slot
        
        player = queries.get_player(user_id)
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        success = queries.unequip_item(user_id, slot)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to unequip item")
        
        return {
            "status": "success",
            "message": f"Unequipped from {slot}"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error unequipping item: {str(e)}")


@router.post("/discard", response_model=dict)
async def discard_item(user_id: int, item_id: str, quantity: int = 1):
    """Discard item from inventory"""
    try:
        player = queries.get_player(user_id)
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        success = queries.remove_item_from_inventory(user_id, item_id, quantity)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to discard item")
        
        return {
            "status": "success",
            "message": f"Discarded {quantity}x {item_id}"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error discarding item: {str(e)}")
