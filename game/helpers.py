from game.data import ITEMS
import random


def get_recent_finds_from_inventory_rows(inventory_rows: list[tuple[str, int]]) -> list[str]:
    names = []
    for item_id, qty in inventory_rows[:3]:
        item = ITEMS.get(item_id)
        if item:
            names.append(item["name"])
    return names


def can_mix_inventory(inventory_rows: list[tuple[str, int]]) -> bool:
    total_common = 0
    for item_id, qty in inventory_rows:
        item = ITEMS.get(item_id)
        if item and item["rarity"] == "Common":
            total_common += qty
    return total_common >= 2


def perform_mix(inventory_rows: list[tuple[str, int]]) -> tuple[str, int] | None:
    common_ids = []
    for item_id, qty in inventory_rows:
        item = ITEMS.get(item_id)
        if item and item["rarity"] == "Common":
            common_ids.extend([item_id] * qty)

    if len(common_ids) < 2:
        return None

    crafted_options = [
        ("mystery_box", 1),
        ("broken_phone", 1),
        ("scrap_metal", 2),
    ]
    return random.choice(crafted_options)
