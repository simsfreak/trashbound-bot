import random
from game.data import ITEMS, ZONES

DIVE_REACTIONS = [
    "The pile coughed up something decent.",
    "Certified gremlin success.",
    "A messy win is still a win.",
    "You rummaged with style.",
    "Trash luck is kinda cracked today.",
    "A tiny victory for the dumpster elite.",
    "The alley provided. Barely, but still.",
]


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


def get_recent_finds_from_inventory_rows(inventory_rows: list[tuple[str, int]]) -> list[str]:
    names = []
    for item_id, qty in inventory_rows[:3]:
        item = ITEMS.get(item_id)
        if item:
            names.append(f"{item.get('emoji', '✨')} {item['name']}")
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


def get_random_dive_reaction() -> str:
    return random.choice(DIVE_REACTIONS)
