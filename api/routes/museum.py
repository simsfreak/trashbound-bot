from fastapi import APIRouter, HTTPException
from db import queries
from game.helpers import get_next_incomplete_collection, get_collection_progress_all
from game.data import MUSEUM_COLLECTIONS
from api.schemas import MuseumResponse, CollectionProgressResponse

router = APIRouter()


@router.get("/{user_id}", response_model=dict)
async def get_museum(user_id: int):
    """Get museum data"""
    try:
        player = queries.get_player(user_id)
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        # Get discovered items and completed collections
        discovered = queries.get_discovered_item_ids(user_id)
        completed = queries.get_completed_collections(user_id)
        
        return {
            "status": "success",
            "museum_level": player.get("museum_level", 1),
            "museum_xp": player.get("museum_xp", 0),
            "discovered_count": len(discovered),
            "discovered_items": list(discovered),
            "completed_collections": list(completed),
            "total_collections": len(MUSEUM_COLLECTIONS),
            "total_items": sum(len(coll.get("items", [])) for coll in MUSEUM_COLLECTIONS.values())
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving museum: {str(e)}")


@router.get("/{user_id}/collections", response_model=dict)
async def get_collections(user_id: int):
    """Get museum collection progress"""
    try:
        player = queries.get_player(user_id)
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        discovered = queries.get_discovered_item_ids(user_id)
        completed = queries.get_completed_collections(user_id)
        
        collections = []
        for key, collection in MUSEUM_COLLECTIONS.items():
            collection_items = collection.get("items", [])
            discovered_in_collection = len([item for item in collection_items if item in discovered])
            total_in_collection = len(collection_items)
            progress_percent = int((discovered_in_collection / total_in_collection * 100) if total_in_collection > 0 else 0)
            
            collections.append({
                "collection_key": key,
                "collection_name": collection.get("name", key),
                "discovered_count": discovered_in_collection,
                "total_count": total_in_collection,
                "progress_percent": progress_percent,
                "is_completed": key in completed
            })
        
        return {
            "status": "success",
            "user_id": user_id,
            "collections": collections
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving collections: {str(e)}")


@router.get("/{user_id}/next-collection", response_model=dict)
async def get_next_collection(user_id: int):
    """Get next incomplete collection hint"""
    try:
        player = queries.get_player(user_id)
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        discovered = queries.get_discovered_item_ids(user_id)
        completed = queries.get_completed_collections(user_id)
        
        # Find next incomplete collection
        next_collection = None
        for key, collection in MUSEUM_COLLECTIONS.items():
            if key not in completed:
                next_collection = {
                    "key": key,
                    "name": collection.get("name", key),
                    "description": collection.get("description", ""),
                    "total_items": len(collection.get("items", []))
                }
                break
        
        if not next_collection:
            return {
                "status": "success",
                "message": "All collections completed!",
                "next_collection": None
            }
        
        return {
            "status": "success",
            "next_collection": next_collection
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving next collection: {str(e)}")
