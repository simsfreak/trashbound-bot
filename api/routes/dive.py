from fastapi import APIRouter, HTTPException
from db import queries
from game.helpers import roll_item_for_zone, calculate_equipment_bonuses
from game.leveling import apply_xp
from game.data import ITEMS, ZONES
from api.schemas import DiveRequest, DiveResultResponse

router = APIRouter()


@router.post("/start", response_model=dict)
async def start_dive(request: DiveRequest):
    """Execute a dive and return results"""
    try:
        user_id = request.user_id
        player = queries.get_player(user_id)
        
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        # Get equipped items
        equipment_rows = queries.get_equipped_items(user_id)
        
        # Calculate equipment bonuses (SAME LOGIC AS DISCORD BOT)
        equipment_bonuses = calculate_equipment_bonuses(equipment_rows)
        
        # Get current zone
        zone_id = player.get("current_zone_id", "back_alley")
        
        # Roll item (SAME LOGIC AS DISCORD BOT)
        item_id, item = roll_item_for_zone(
            zone_id=zone_id,
            rare_bonus=equipment_bonuses.get("drop_bonus", 0.0)
        )
        
        # Calculate rewards with bonuses (SAME LOGIC AS DISCORD BOT)
        base_coins = int(item.get("coins", 10))
        base_xp = int(item.get("xp", 5))
        
        gained_coins = int(base_coins * (1 + equipment_bonuses.get("coin_boost", 0.0)))
        gained_xp = int(base_xp * (1 + equipment_bonuses.get("xp_boost", 0.0)))
        
        # Check for extra items from equipment
        extra_item_chance = equipment_bonuses.get("extra_item_chance", 0.0)
        if extra_item_chance > 0 and __import__("random").random() < extra_item_chance:
            extra_item_id, extra_item = roll_item_for_zone(zone_id, rare_bonus=0.0)
            queries.add_item_to_inventory(user_id, extra_item_id, 1)
        
        # Apply XP and level up (SAME LOGIC AS DISCORD BOT)
        new_xp, new_level, leveled_up = apply_xp(
            current_xp=player.get("xp", 0),
            current_level=player.get("level", 1),
            gained_xp=gained_xp
        )
        
        # Update coins and totals
        new_coins = player.get("coins", 0) + gained_coins
        new_dives = player.get("total_dives", 0) + 1
        
        # Save to database (SAME QUERIES AS DISCORD BOT)
        queries.add_item_to_inventory(user_id, item_id, 1)
        queries.update_player_progress(
            user_id=user_id,
            coins=new_coins,
            xp=new_xp,
            level=new_level,
            current_title=player.get("current_title", "Trasher"),
            total_dives=new_dives
        )
        
        # Progress daily quest
        try:
            queries.progress_daily_quest(user_id, "dive_count", 1)
        except:
            pass  # Quest system might not be active
        
        # Check and complete collections for museum
        try:
            queries.check_and_complete_collections(user_id)
        except:
            pass  # Museum system might not be active
        
        # Return dive result
        return {
            "status": "success",
            "item_id": item_id,
            "item_name": item.get("name", item_id),
            "item_rarity": item.get("rarity", "common"),
            "item_emoji": item.get("emoji", "🗑️"),
            "gained_xp": gained_xp,
            "gained_coins": gained_coins,
            "new_level": new_level,
            "leveled_up": leveled_up,
            "new_total_coins": new_coins
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dive failed: {str(e)}")
