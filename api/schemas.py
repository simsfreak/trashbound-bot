from pydantic import BaseModel
from typing import Optional

# ==================== REQUEST SCHEMAS ====================

class LoginRequest(BaseModel):
    username: str


class DiveRequest(BaseModel):
    user_id: int


class EquipItemRequest(BaseModel):
    user_id: int
    item_id: str


class UnequipItemRequest(BaseModel):
    user_id: int
    slot: str


class GrantXPRequest(BaseModel):
    user_id: int
    xp_amount: int


class GrantCoinsRequest(BaseModel):
    user_id: int
    coins_amount: int


class GrantTicketsRequest(BaseModel):
    user_id: int
    tickets_amount: int


class GrantItemRequest(BaseModel):
    user_id: int
    item_id: str
    quantity: int = 1


# ==================== RESPONSE SCHEMAS ====================

class ItemResponse(BaseModel):
    item_id: str
    name: str
    rarity: str
    emoji: str
    coins: int
    xp: int


class PlayerResponse(BaseModel):
    user_id: int
    username: str
    level: int
    xp: int
    coins: int
    dirty_tickets: int
    total_dives: int
    current_zone_id: Optional[str] = None
    current_title: Optional[str] = None
    museum_level: int = 1
    museum_xp: int = 0


class DiveResultResponse(BaseModel):
    status: str
    item_id: str
    item_name: str
    item_rarity: str
    gained_xp: int
    gained_coins: int
    new_level: int
    leveled_up: bool
    new_total_coins: int


class InventoryItemResponse(BaseModel):
    item_id: str
    quantity: int
    name: str
    rarity: str
    emoji: str


class InventoryResponse(BaseModel):
    user_id: int
    items: list[InventoryItemResponse]


class CollectionProgressResponse(BaseModel):
    collection_key: str
    collection_name: str
    discovered_count: int
    total_count: int
    progress_percent: int
    is_completed: bool


class MuseumResponse(BaseModel):
    user_id: int
    museum_level: int
    museum_xp: int
    discovered_count: int
    total_items: int
    completed_collections: int
    total_collections: int


class SuccessResponse(BaseModel):
    status: str
    message: str


class ErrorResponse(BaseModel):
    status: str
    detail: str
