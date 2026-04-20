import random
from datetime import datetime, timedelta

from game.data import DIRTY_DRAW_POOL, ITEMS, ZONES, get_live_events, MUSEUM_COLLECTIONS
from game.rarities import RARITY_BADGES, RARITY_FX

DIVE_STARTERS = [
    "🗑️ You shove both hands into the pile.",
    "🗑️ You start kicking through wet cardboard with confidence.",
    "🗑️ You descend into the garbage like a professional menace.",
]

DIVE_MIDPOINTS = [
    "*clank... rustle... something shifts under the pile...*",
    "*a rat judges you and leaves... something shiny remains...*",
    "*the dumpster coughs up a suspicious little prize...*",
]

DIVE_REACTIONS = [
    "The pile coughed up something decent.",
    "Certified gremlin success.",
    "A messy win is still a win.",
    "You rummaged with style.",
    "Trash luck is kinda cracked today.",
    "A tiny victory for the dumpster elite.",
    "The alley provided. Barely, but still.",
]

RANDOM_DIVE_EVENTS = [
    {"text": "🐀 A rat bails out mid-dive and drops loose coins.", "bonus_coins": 12, "bonus_xp": 0},
    {"text": "✨ You uncover a tiny hidden stash.", "bonus_coins": 0, "bonus_xp": 8},
    {"text": "💥 The pile collapses in your favor. Goblin miracle.", "bonus_coins": 18, "bonus_xp": 6},
    {"text": "🫠 You stepped in something unholy. Character building.", "bonus_coins": 0, "bonus_xp": 0},
]

TITLE_STYLES = [
    (20, "👑 ✨ ★ 𝙂𝙖𝙧𝙗𝙖𝙜𝙚 𝙍𝙤𝙮𝙖𝙡𝙩𝙮 ★ ✨ 👑"),
    (12, "⚙️ ⟡ 𝘿𝙪𝙢𝙥𝙨𝙩𝙚𝙧 𝙃𝙪𝙣𝙩𝙚𝙧 ⟡ ⚙️"),
    (6, "🔩 ✦ 𝙎𝙘𝙧𝙖𝙥 𝙎𝙚𝙚𝙠𝙚𝙧 ✦ 🔩"),
    (1, "🗑️ 𝙏𝙧𝙖𝙨𝙝 𝙍𝙤𝙤𝙠𝙞𝙚"),
]



def determine_title(level: int) -> str:
    for min_level, title in TITLE_STYLES:
        if level >= min_level:
            return title
    return TITLE_STYLES[-1][1]



def get_zone_name(zone_id: str) -> str:
    return ZONES.get(zone_id, {}).get("name", zone_id)



def get_items_for_zone(zone_id: str) -> list[tuple[str, dict]]:
    return [
        (item_id, item_data)
        for item_id, item_data in ITEMS.items()
        if zone_id in item_data.get("zone_ids", [])
    ]



def roll_item_for_zone(zone_id: str, rare_bonus: float = 0.0) -> tuple[str, dict]:
    items = get_items_for_zone(zone_id)
    if not items:
        raise RuntimeError(f"No items available for zone: {zone_id}")

    weighted_pool: list[tuple[str, dict]] = []
    for item_id, item_data in items:
        rarity = item_data["rarity"]
        base_weight = {
            "Common": 70,
            "Uncommon": 18,
            "Rare": 8,
            "Epic": 3,
            "Legendary": 1,
            "Mythic": 0.2,
        }.get(rarity, 1)
        if rarity in {"Rare", "Epic", "Legendary", "Mythic"}:
            base_weight *= 1 + rare_bonus
        weighted_pool.extend([(item_id, item_data)] * max(1, int(round(base_weight))))

    return random.choice(weighted_pool)



def get_recent_finds_from_inventory_rows(inventory_rows: list[tuple[str, int]]) -> list[str]:
    names = []
    for item_id, _qty in inventory_rows[:3]:
        item = ITEMS.get(item_id)
        if item:
            names.append(f"{item.get('emoji', '✨')} {item['name']} • {RARITY_BADGES.get(item['rarity'], item['rarity'])}")
    return names



def can_mix_inventory(inventory_rows: list[tuple[str, int]]) -> bool:
    total_common = 0
    for item_id, qty in inventory_rows:
        item = ITEMS.get(item_id)
        if item and item["rarity"] == "Common":
            total_common += qty
    return total_common >= 2



def find_available_recipe(inventory_map: dict[str, int]) -> dict | None:
    for recipe in MIX_RECIPES:
        if all(inventory_map.get(item_id, 0) >= qty for item_id, qty in recipe["ingredients"].items()):
            return recipe
    return None


def calculate_equipment_bonuses(equipment_rows: list[dict]) -> dict[str, float]:
    xp_boost = 0.0
    coin_boost = 0.0
    drop_bonus = 0.0
    extra_item_chance = 0.0
    loot_value = 0.0
    for entry in equipment_rows:
        if not isinstance(entry, dict):
            continue
        item = ITEMS.get(entry.get("item_id", ""))
        if not item:
            continue
        effects = item.get("effects", {})
        xp_boost += float(effects.get("xp_boost", 0))
        coin_boost += float(effects.get("coin_boost", 0))
        drop_bonus += float(effects.get("drop_bonus", 0))
        extra_item_chance += float(effects.get("extra_item_chance", 0))
        loot_value += float(effects.get("loot_value", 0))
    return {
        "xp_boost": xp_boost,
        "coin_boost": coin_boost,
        "drop_bonus": drop_bonus,
        "extra_item_chance": extra_item_chance,
        "loot_value": loot_value,
    }


def roll_dirty_draw_reward(ticket_count: int = 1) -> list[tuple[str, dict]]:
    if ticket_count <= 0:
        return []

    weights = [entry.get("weight", 1) for entry in DIRTY_DRAW_POOL]
    item_ids = [entry["item_id"] for entry in DIRTY_DRAW_POOL]
    results: list[tuple[str, dict]] = []
    for _ in range(ticket_count):
        item_id = random.choices(item_ids, weights=weights, k=1)[0]
        results.append((item_id, ITEMS.get(item_id, {})))
    return results



def perform_chaos_mix(inventory_rows: list[tuple[str, int]], extra_rare_bonus: float = 0.0) -> tuple[str, int] | None:
    common_ids: list[str] = []
    for item_id, qty in inventory_rows:
        item = ITEMS.get(item_id)
        if item and item["rarity"] == "Common":
            common_ids.extend([item_id] * qty)

    if len(common_ids) < 2:
        return None

    crafted_options = [
        ("golden_potion", 1, 6 + extra_rare_bonus),
        ("glitch_charm", 1, 14 + extra_rare_bonus),
        ("iron_gloves", 1, 22),
        ("sole_stompers", 1, 22),
        ("scrap_metal", 2, 36),
    ]
    weighted: list[tuple[str, int]] = []
    for item_id, qty, weight in crafted_options:
        weighted.extend([(item_id, qty)] * max(1, int(round(weight))))
    return random.choice(weighted)



def get_random_dive_reaction() -> str:
    return random.choice(DIVE_REACTIONS)



def get_random_dive_starter() -> str:
    return random.choice(DIVE_STARTERS)



def get_random_dive_midpoint() -> str:
    return random.choice(DIVE_MIDPOINTS)



def maybe_roll_dive_event() -> dict | None:
    if random.random() <= 0.35:
        return random.choice(RANDOM_DIVE_EVENTS)
    return None



def get_item_card_line(item_id: str, qty: int = 1) -> str:
    item = ITEMS[item_id]
    badge = RARITY_BADGES.get(item["rarity"], item["rarity"])
    return f"{item.get('emoji', '✨')} **{item['name']}** x{qty}\n{badge} • *{item.get('flavor', 'A strange little treasure.')}*"



def get_rarity_fx_text(rarity: str) -> str:
    return RARITY_FX.get(rarity, "weird little trash energy")



def get_effect_remaining_text(expires_at: datetime) -> str:
    remaining = max(timedelta(0), expires_at - datetime.utcnow())
    total_seconds = int(remaining.total_seconds())
    hours, rem = divmod(total_seconds, 3600)
    minutes, _seconds = divmod(rem, 60)
    if hours:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"



def get_world_status_lines() -> list[str]:
    live = get_live_events()
    if not live:
        return ["🌫️ Nothing major is live right now. The dumpster spirits are resting."]
    return [f"{event['emoji']} **{event['name']}** — {event['profile_line']}" for event in live]


def get_collection_progress_all(discovered_item_ids: set[str], museum_collections: dict) -> dict[str, int]:
    """Calculate progress for all collections."""
    progress: dict[str, int] = {}
    for collection_key, collection_data in museum_collections.items():
        required_items = set(collection_data.get("item_ids", []))
        discovered = len(required_items & discovered_item_ids)
        progress[collection_key] = discovered
    return progress


def is_collection_complete(discovered_item_ids: set[str], required_item_ids: list[str]) -> bool:
    """Check if a collection is complete."""
    required_set = set(required_item_ids)
    return required_set.issubset(discovered_item_ids)


def calculate_museum_bonuses(completed_collections: set[str]) -> dict[str, float]:
    """Calculate bonuses from completed collections."""
    bonuses: dict[str, float] = {
        "xp_boost": 0.0,
        "coin_boost": 0.0,
        "drop_bonus": 0.0,
    }
    
    # Each collection grants specific bonuses
    collection_rewards = {
        "salvaged_basics": {"xp_boost": 0.05},
        "tech_relics": {"coin_boost": 0.05},
        "glitched_objects": {"drop_bonus": 0.03},
        "rat_market": {"coin_boost": 0.08, "drop_bonus": 0.02},
        "crafted_gear": {"xp_boost": 0.08, "coin_boost": 0.05},
        "crown_artifacts": {"xp_boost": 0.10, "coin_boost": 0.10, "drop_bonus": 0.05},
    }
    
    for collection_key in completed_collections:
        rewards = collection_rewards.get(collection_key, {})
        for bonus_type, bonus_value in rewards.items():
            bonuses[bonus_type] += bonus_value
    
    return bonuses


def get_next_incomplete_collection(discovered_item_ids: set[str], museum_collections: dict, completed_collections: set[str]) -> tuple[str, str, int, int] | None:
    """Find the next collection closest to completion."""
    best_key: str | None = None
    best_name: str | None = None
    best_progress: int = -1
    best_total: int = 0
    
    for collection_key, collection_data in museum_collections.items():
        if collection_key in completed_collections:
            continue
        
        required_items = set(collection_data.get("item_ids", []))
        discovered = len(required_items & discovered_item_ids)
        total = len(required_items)
        
        # Prefer collections closest to completion
        if discovered > best_progress:
            best_key = collection_key
            best_name = collection_data.get("name", collection_key)
            best_progress = discovered
            best_total = total
    
    if best_key:
        return (best_key, best_name, best_progress, best_total)
    return None
