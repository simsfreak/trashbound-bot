import random
from game.data import ITEMS, ZONES

def get_zone_name(zone_id: str) -> str:
    return ZONES.get(zone_id, {}).get("name", zone_id)

def get_items_for_zone(zone_id: str) -> list[tuple[str, dict]]:
    return [
        (item_id, item_data)
        for item_id, item_data in ITEMS.items()
        if zone_id in item_data["zone_ids"]
    ]

def roll_item_for_zone(zone_id: str) -> tuple[str, dict]:
    items = get_items_for_zone(zone_id)
    if not items:
        raise RuntimeError(f"No items available for zone: {zone_id}")
    return random.choice(items)
