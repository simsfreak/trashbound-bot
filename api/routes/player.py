from fastapi import APIRouter, HTTPException
from db import queries
from game.data import ITEMS
from api.schemas import PlayerResponse, InventoryResponse, InventoryItemResponse

router = APIRouter()


@router.get("/{user_id}", response_model=dict)
async def get_player(user_id: int):
    """Get full player profile"""
    try:
        player = queries.get_player(user_id)
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        return {
            "status": "success",
            "player": PlayerResponse(**player)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving player: {str(e)}")


@router.get("/{user_id}/inventory", response_model=dict)
async def get_inventory(user_id: int):
    """Get player inventory with item details"""
    try:
        player = queries.get_player(user_id)
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        inventory = queries.get_inventory(user_id)
        
        # Enrich with item data
        items = []
        for item_id, qty in inventory:
            if item_id in ITEMS:
                item_data = ITEMS[item_id]
                items.append(InventoryItemResponse(
                    item_id=item_id,
                    quantity=qty,
                    name=item_data.get("name", item_id),
                    rarity=item_data.get("rarity", "common"),
                    emoji=item_data.get("emoji", "🗑️")
                ))
        
        return {
            "status": "success",
            "user_id": user_id,
            "items": items
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving inventory: {str(e)}")


@router.get("/{user_id}/equipment", response_model=dict)
async def get_equipment(user_id: int):
    """Get player equipment"""
    try:
        player = queries.get_player(user_id)
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        equipment = queries.get_player_equipment(user_id)
        
        # Enrich with item data
        equipped = {}
        for slot, item_id in equipment.items():
            if item_id and item_id in ITEMS:
                item_data = ITEMS[item_id]
                equipped[slot] = {
                    "item_id": item_id,
                    "name": item_data.get("name", item_id),
                    "rarity": item_data.get("rarity", "common"),
                    "emoji": item_data.get("emoji", "🗑️")
                }
            else:
                equipped[slot] = None
        
        return {
            "status": "success",
            "user_id": user_id,
            "equipment": equipped
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving equipment: {str(e)}")
