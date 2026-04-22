# ═══════════════════════════════════════════════════════════════════
# ZONE SYSTEM - FISHING, BOTANY, ARCHAEOLOGY, SCAVENGE
# ═══════════════════════════════════════════════════════════════════
# Comprehensive zone-based farming system with missions, drop rates,
# and difficulty-based loot tables.
# ═══════════════════════════════════════════════════════════════════

import random

# ═══════════════════════════════════════════════════════════════════
# 🎣 FISHING ZONE - BASE DROP RATES
# ═══════════════════════════════════════════════════════════════════
FISHING_BASE_RATES = {
    "Common": 0.62,
    "Rare": 0.24,
    "Exotic": 0.10,
    "Dangerous": 0.04,
}

FISHING_POOLS = {
    "Common": [
        {"id": "rustfin_minnow", "name": "🐟 Rustfin Minnow", "weight": 18},
        {"id": "alley_carp", "name": "🐟 Alley Carp", "weight": 18},
        {"id": "tinwater_guppy", "name": "🐟 Tinwater Guppy", "weight": 14},
        {"id": "scrapscale_fish", "name": "🐟 Scrapscale Fish", "weight": 14},
        {"id": "drift_puddle_fish", "name": "🐟 Drift Puddle Fish", "weight": 10},
    ],
    "Rare": [
        {"id": "neon_alleyfish", "name": "🐠 Neon Alleyfish", "weight": 12},
        {"id": "glassfin_swimmer", "name": "🐠 Glassfin Swimmer", "weight": 12},
        {"id": "glowtail_snapper", "name": "🐠 Glowtail Snapper", "weight": 8},
        {"id": "moon_ripple_fish", "name": "🐠 Moon Ripple Fish", "weight": 8},
        {"id": "shimmer_gill", "name": "🐠 Shimmer Gill", "weight": 5},
    ],
    "Exotic": [
        {"id": "bubble_core_puffer", "name": "🐡 Bubble Core Puffer", "weight": 8},
        {"id": "voidcurrent_eel", "name": "🐡 Voidcurrent Eel", "weight": 8},
        {"id": "prismscale_drifter", "name": "🐡 Prismscale Drifter", "weight": 5},
        {"id": "static_surge_fish", "name": "🐡 Static Surge Fish", "weight": 5},
        {"id": "crystal_tidefish", "name": "🐡 Crystal Tidefish", "weight": 3},
    ],
    "Dangerous": [
        {"id": "scrapjaw_shark", "name": "🦈 Scrapjaw Shark", "weight": 6},
        {"id": "rustfang_shark", "name": "🦈 Rustfang Shark", "weight": 6},
        {"id": "voidbite_leviathan", "name": "🦈 Voidbite Leviathan", "weight": 4},
        {"id": "ironfin_devourer", "name": "🦈 Ironfin Devourer", "weight": 4},
        {"id": "deep_gutter_beast", "name": "🦈 Deep Gutter Beast", "weight": 2},
    ],
}

FISHING_WEIGHT_RANGES = {
    "Common": (0.4, 2.5),
    "Rare": (1.5, 4.5),
    "Exotic": (3.0, 8.0),
    "Dangerous": (6.0, 25.0),
}

# ═══════════════════════════════════════════════════════════════════
# 🌿 BOTANY ZONE - BASE DROP RATES
# ═══════════════════════════════════════════════════════════════════
BOTANY_BASE_RATES = {
    "Common": 0.58,
    "Rare": 0.26,
    "Exotic": 0.12,
    "Dangerous": 0.04,
}

BOTANY_POOLS = {
    "Common": [
        {"id": "alley_moss", "name": "🌱 Alley Moss", "weight": 18},
        {"id": "cracked_root_weed", "name": "🌿 Cracked Root Weed", "weight": 18},
        {"id": "rust_clover", "name": "🍀 Rust Clover", "weight": 14},
        {"id": "dry_stem_grass", "name": "🌾 Dry Stem Grass", "weight": 14},
        {"id": "tiny_scrap_cactus", "name": "🌵 Tiny Scrap Cactus", "weight": 10},
    ],
    "Rare": [
        {"id": "glow_petal_bloom", "name": "🌸 Glow Petal Bloom", "weight": 12},
        {"id": "sunlit_alley_flower", "name": "🌼 Sunlit Alley Flower", "weight": 12},
        {"id": "neon_pollen_bud", "name": "🌺 Neon Pollen Bud", "weight": 8},
        {"id": "whisper_leaf", "name": "🍃 Whisper Leaf", "weight": 8},
        {"id": "softlight_tulip", "name": "🌷 Softlight Tulip", "weight": 5},
    ],
    "Exotic": [
        {"id": "radiant_core_blossom", "name": "🌻 Radiant Core Blossom", "weight": 8},
        {"id": "pulsecap_mushroom", "name": "🍄 Pulsecap Mushroom", "weight": 8},
        {"id": "thornlight_rose", "name": "🌹 Thornlight Rose", "weight": 5},
        {"id": "halo_bloom", "name": "🌼 Halo Bloom", "weight": 5},
        {"id": "spirit_vine", "name": "🌿 Spirit Vine", "weight": 3},
    ],
    "Dangerous": [
        {"id": "venom_spore_plant", "name": "🪴 Venom Spore Plant", "weight": 6},
        {"id": "toxic_puffcap", "name": "🍄 Toxic Puffcap", "weight": 6},
        {"id": "grasping_root", "name": "🌿 Grasping Root", "weight": 4},
        {"id": "bloodthorn_rose", "name": "🌹 Bloodthorn Rose", "weight": 4},
        {"id": "devour_vine", "name": "🌱 Devour Vine", "weight": 2},
    ],
}

BOTANY_QUALITY_TIERS = ["Wilted", "Fresh", "Vibrant", "Pristine", "Mutated"]
BOTANY_QUALITY_RATES = {
    "Wilted": 0.20,
    "Fresh": 0.35,
    "Vibrant": 0.25,
    "Pristine": 0.15,
    "Mutated": 0.05,
}

# ═══════════════════════════════════════════════════════════════════
# 🏺 ARCHAEOLOGY ZONE - BASE DROP RATES
# ═══════════════════════════════════════════════════════════════════
ARCHAEOLOGY_BASE_RATES = {
    "Common": 0.66,
    "Rare": 0.22,
    "Exotic": 0.09,
    "Dangerous": 0.03,
}

ARCHAEOLOGY_POOLS = {
    "Common": [
        {"id": "broken_pottery", "name": "🪨 Broken Pottery", "weight": 18},
        {"id": "cracked_brick_piece", "name": "🧱 Cracked Brick Piece", "weight": 18},
        {"id": "old_wood_fragment", "name": "🪵 Old Wood Fragment", "weight": 14},
        {"id": "faded_coin", "name": "🪙 Faded Coin", "weight": 14},
        {"id": "lost_fragment", "name": "🧩 Lost Fragment", "weight": 10},
    ],
    "Rare": [
        {"id": "engraved_vase_piece", "name": "🏺 Engraved Vase Piece", "weight": 12},
        {"id": "ancient_coin", "name": "🪙 Ancient Coin", "weight": 12},
        {"id": "mini_statue_head", "name": "🗿 Mini Statue Head", "weight": 8},
        {"id": "old_bead_chain", "name": "📿 Old Bead Chain", "weight": 8},
        {"id": "watcher_stone", "name": "🧿 Watcher Stone", "weight": 5},
    ],
    "Exotic": [
        {"id": "forgotten_idol", "name": "🗿 Forgotten Idol", "weight": 8},
        {"id": "royal_vessel_shard", "name": "🏺 Royal Vessel Shard", "weight": 8},
        {"id": "all_seeing_charm", "name": "🧿 All-Seeing Charm", "weight": 5},
        {"id": "lost_script_tablet", "name": "📜 Lost Script Tablet", "weight": 5},
        {"id": "timeworn_relic_coin", "name": "🪙 Timeworn Relic Coin", "weight": 3},
    ],
    "Dangerous": [
        {"id": "cursed_skull_relic", "name": "☠️ Cursed Skull Relic", "weight": 6},
        {"id": "haunted_idol", "name": "🗿 Haunted Idol", "weight": 6},
        {"id": "forbidden_tablet", "name": "📜 Forbidden Tablet", "weight": 4},
        {"id": "eye_of_the_buried", "name": "🧿 Eye of the Buried", "weight": 4},
        {"id": "sealed_tomb_piece", "name": "⚰️ Sealed Tomb Piece", "weight": 2},
    ],
}

ARCHAEOLOGY_CONDITION_TIERS = ["Broken", "Worn", "Preserved", "Ancient", "Cursed"]
ARCHAEOLOGY_CONDITION_RATES = {
    "Broken": 0.30,
    "Worn": 0.35,
    "Preserved": 0.20,
    "Ancient": 0.10,
    "Cursed": 0.05,
}

# ═══════════════════════════════════════════════════════════════════
# ♻️ SCAVENGE ZONE - BASE DROP RATES
# ═══════════════════════════════════════════════════════════════════
SCAVENGE_BASE_RATES = {
    "Common": 0.70,
    "Rare": 0.20,
    "Exotic": 0.08,
    "Dangerous": 0.02,
}

SCAVENGE_POOLS = {
    "Common": [
        {"id": "used_paper_scrap", "name": "🧻 Used Paper Scrap", "weight": 18},
        {"id": "dead_battery", "name": "🔋 Dead Battery", "weight": 18},
        {"id": "cracked_bottle", "name": "🧴 Cracked Bottle", "weight": 14},
        {"id": "torn_box", "name": "📦 Torn Box", "weight": 14},
        {"id": "lost_sock", "name": "🧦 Lost Sock", "weight": 10},
    ],
    "Rare": [
        {"id": "polished_coin", "name": "🪙 Polished Coin", "weight": 12},
        {"id": "strong_magnet", "name": "🧲 Strong Magnet", "weight": 12},
        {"id": "clean_bottle", "name": "🧴 Clean Bottle", "weight": 8},
        {"id": "sealed_box", "name": "📦 Sealed Box", "weight": 8},
        {"id": "mini_plush", "name": "🧸 Mini Plush", "weight": 5},
    ],
    "Exotic": [
        {"id": "alley_eye_bead", "name": "🧿 Alley Eye Bead", "weight": 8},
        {"id": "echo_coin", "name": "🪙 Echo Coin", "weight": 8},
        {"id": "spirit_plush", "name": "🧸 Spirit Plush", "weight": 5},
        {"id": "pulse_magnet", "name": "🧲 Pulse Magnet", "weight": 5},
        {"id": "lucky_package", "name": "📦 Lucky Package", "weight": 3},
    ],
    "Dangerous": [
        {"id": "toxic_waste_chunk", "name": "☣️ Toxic Waste Chunk", "weight": 6},
        {"id": "unstable_battery_core", "name": "🔋 Unstable Battery Core", "weight": 6},
        {"id": "corrupt_canister", "name": "🧪 Corrupt Canister", "weight": 4},
        {"id": "watching_scrap", "name": "🧿 Watching Scrap", "weight": 4},
        {"id": "glitch_metal_piece", "name": "⚠️ Glitch Metal Piece", "weight": 2},
    ],
}

SCAVENGE_STATE_TIERS = ["Ruined", "Used", "Clean", "Odd", "Glitched"]
SCAVENGE_STATE_RATES = {
    "Ruined": 0.35,
    "Used": 0.35,
    "Clean": 0.15,
    "Odd": 0.10,
    "Glitched": 0.05,
}

# ═══════════════════════════════════════════════════════════════════
# DIFFICULTY MODIFIERS (ALL ZONES)
# ═══════════════════════════════════════════════════════════════════
DIFFICULTY_MODIFIERS = {
    "Easy": {
        "Common": +0.10,
        "Rare": -0.06,
        "Exotic": -0.03,
        "Dangerous": -0.01,
    },
    "Medium": {
        "Common": 0.0,
        "Rare": 0.0,
        "Exotic": 0.0,
        "Dangerous": 0.0,
    },
    "Hard": {
        "Common": -0.12,
        "Rare": +0.06,
        "Exotic": +0.04,
        "Dangerous": +0.02,
    },
}

# ═══════════════════════════════════════════════════════════════════
# MISSION GENERATION - RARITY TARGETING
# ═══════════════════════════════════════════════════════════════════
MISSION_RARITY_WEIGHTS = {
    "Common": 0.55,
    "Rare": 0.28,
    "Exotic": 0.12,
    "Dangerous": 0.05,
}

MISSION_QUANTITIES = {
    "Common": (20, 35),      # 20-35 needed
    "Rare": (10, 20),        # 10-20 needed
    "Exotic": (5, 10),       # 5-10 needed
    "Dangerous": (1, 5),     # 1-5 needed
}

# ═══════════════════════════════════════════════════════════════════
# ACTION COOLDOWNS PER ZONE (seconds)
# ═══════════════════════════════════════════════════════════════════
ZONE_COOLDOWNS = {
    "fishing": 20,          # ~180 attempts in 1 hour
    "botany": 18,           # ~200 attempts in 1 hour
    "archaeology": 25,      # ~144 attempts in 1 hour
    "scavenge": 15,         # ~240 attempts in 1 hour
}

# ═══════════════════════════════════════════════════════════════════
# BONUS ENCOUNTER SYSTEM
# ═══════════════════════════════════════════════════════════════════
BONUS_ENCOUNTER_ODDS = {
    "nothing_special": 0.89,
    "bonus_drop": 0.07,
    "rarity_upgrade": 0.02,
    "mission_double_count": 0.015,
    "danger_encounter": 0.005,
}

# ═══════════════════════════════════════════════════════════════════
# ZONE REWARDS (COMPLETION)
# ═══════════════════════════════════════════════════════════════════
ZONE_REWARDS = {
    "ticket_amounts": [50, 100, 1000],
    "xp_boxes": [
        {"name": "Zone Blue Box", "xp": 1000, "emoji": "🟦"},
        {"name": "Zone Red Box", "xp": 2000, "emoji": "🟥"},
        {"name": "Zone Yellow Box", "xp": 2000, "emoji": "🟨"},
    ],
    "money_bags": {
        "completed": 10000,      # $10,000 for mission success
        "incomplete": 1000,      # $1,000 for incomplete mission
    },
}

# ═══════════════════════════════════════════════════════════════════
# ZONE METADATA
# ═══════════════════════════════════════════════════════════════════
ZONES_META = {
    "fishing": {
        "name": "🎣 Fishing Zone",
        "emoji": "🎣",
        "activity_verb": "Catch",
        "unlock_level": 1,
        "description": "Fish the murky waters for aquatic treasures.",
        "cooldown": ZONE_COOLDOWNS["fishing"],
        "base_rates": FISHING_BASE_RATES,
        "item_pools": FISHING_POOLS,
        "metadata_type": "weight",
        "metadata_ranges": FISHING_WEIGHT_RANGES,
    },
    "botany": {
        "name": "🌿 Botany Zone",
        "emoji": "🌿",
        "activity_verb": "Collect",
        "unlock_level": 2,
        "description": "Gather rare plants and herbs from the overgrown district.",
        "cooldown": ZONE_COOLDOWNS["botany"],
        "base_rates": BOTANY_BASE_RATES,
        "item_pools": BOTANY_POOLS,
        "metadata_type": "quality",
        "metadata_tiers": BOTANY_QUALITY_TIERS,
        "metadata_rates": BOTANY_QUALITY_RATES,
    },
    "archaeology": {
        "name": "🏺 Archaeology Zone",
        "emoji": "🏺",
        "activity_verb": "Excavate",
        "unlock_level": 3,
        "description": "Dig up ancient relics from forgotten burial grounds.",
        "cooldown": ZONE_COOLDOWNS["archaeology"],
        "base_rates": ARCHAEOLOGY_BASE_RATES,
        "item_pools": ARCHAEOLOGY_POOLS,
        "metadata_type": "condition",
        "metadata_tiers": ARCHAEOLOGY_CONDITION_TIERS,
        "metadata_rates": ARCHAEOLOGY_CONDITION_RATES,
    },
    "scavenge": {
        "name": "♻️ Scavenge Zone",
        "emoji": "♻️",
        "activity_verb": "Recover",
        "unlock_level": 4,
        "description": "Sift through the junkyard for valuable trash.",
        "cooldown": ZONE_COOLDOWNS["scavenge"],
        "base_rates": SCAVENGE_BASE_RATES,
        "item_pools": SCAVENGE_POOLS,
        "metadata_type": "state",
        "metadata_tiers": SCAVENGE_STATE_TIERS,
        "metadata_rates": SCAVENGE_STATE_RATES,
    },
}

# ═══════════════════════════════════════════════════════════════════
# ZONE HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def get_adjusted_rates(zone_id: str, difficulty: str = "Medium") -> dict:
    """Get drop rates adjusted by difficulty."""
    zone_meta = ZONES_META.get(zone_id)
    if not zone_meta:
        return {}
    
    base_rates = zone_meta["base_rates"].copy()
    modifier = DIFFICULTY_MODIFIERS.get(difficulty, {})
    
    adjusted = {}
    for rarity, rate in base_rates.items():
        adjusted[rarity] = max(0, min(1, rate + modifier.get(rarity, 0)))
    
    # Normalize so they sum to 1
    total = sum(adjusted.values())
    if total > 0:
        adjusted = {k: v/total for k, v in adjusted.items()}
    
    return adjusted

def roll_rarity(zone_id: str, difficulty: str = "Medium") -> str:
    """Roll a rarity based on zone and difficulty."""
    rates = get_adjusted_rates(zone_id, difficulty)
    rarities = list(rates.keys())
    weights = list(rates.values())
    return random.choices(rarities, weights=weights, k=1)[0]

def roll_item_from_rarity(zone_id: str, rarity: str) -> dict:
    """Roll an item from a specific rarity pool in a zone."""
    zone_meta = ZONES_META.get(zone_id)
    if not zone_meta:
        return {}
    
    item_pools = zone_meta["item_pools"]
    rarity_pool = item_pools.get(rarity, [])
    
    if not rarity_pool:
        return {}
    
    items = [item for item in rarity_pool]
    weights = [item.get("weight", 1) for item in items]
    selected = random.choices(items, weights=weights, k=1)[0]
    return selected

def generate_mission(zone_id: str) -> dict:
    """Generate a random mission for a zone."""
    # Roll target rarity
    target_rarity = random.choices(
        list(MISSION_RARITY_WEIGHTS.keys()),
        weights=list(MISSION_RARITY_WEIGHTS.values()),
        k=1
    )[0]
    
    # Roll target item
    zone_meta = ZONES_META.get(zone_id)
    if not zone_meta:
        return {}
    
    item_pools = zone_meta["item_pools"]
    target_item = roll_item_from_rarity(zone_id, target_rarity)
    
    # Roll quantity
    qty_range = MISSION_QUANTITIES.get(target_rarity, (1, 5))
    target_qty = random.randint(qty_range[0], qty_range[1])
    
    return {
        "zone_id": zone_id,
        "target_item_id": target_item.get("id"),
        "target_item_name": target_item.get("name"),
        "target_rarity": target_rarity,
        "target_qty": target_qty,
        "progress": 0,
    }

def roll_bonus_encounter() -> str | None:
    """Roll a special bonus encounter."""
    encounter = random.choices(
        list(BONUS_ENCOUNTER_ODDS.keys()),
        weights=list(BONUS_ENCOUNTER_ODDS.values()),
        k=1
    )[0]
    return None if encounter == "nothing_special" else encounter


# ═══════════════════════════════════════════════════════════════════
# ZONE MISSION REWARD SYSTEM
# ═══════════════════════════════════════════════════════════════════

REWARD_POOL = {
    "dirty_tickets_50": {
        "name": "🎟️ Dirty Tickets x50",
        "type": "tickets",
        "qty": 50,
        "weight": 30,
    },
    "dirty_tickets_200": {
        "name": "🎟️ Dirty Tickets x200",
        "type": "tickets",
        "qty": 200,
        "weight": 15,
    },
    "ticket_bundle_50": {
        "name": "🎟️ Ticket Bundle x50",
        "type": "tickets",
        "qty": 50,
        "weight": 20,
    },
    "ticket_bundle_200": {
        "name": "🎟️ Ticket Bundle x200",
        "type": "tickets",
        "qty": 200,
        "weight": 10,
    },
    "azure_zone_box": {
        "name": "🎁 Azure Zone Box",
        "type": "zone_box",
        "xp_reward": 1000,
        "weight": 15,
    },
    "crimson_zone_box": {
        "name": "🎁 Crimson Zone Box",
        "type": "zone_box",
        "xp_reward": 2000,
        "weight": 12,
    },
    "golden_zone_box": {
        "name": "🎁 Golden Zone Box",
        "type": "zone_box",
        "xp_reward": 2000,
        "weight": 12,
    },
    "heavy_coin_bag": {
        "name": "💰 Bag of Money",
        "type": "coin_bag",
        "coin_reward": 10000,
        "weight": 8,
    },
}

REWARD_RARITY_WEIGHTS = {
    "Common": 0.40,
    "Rare": 0.35,
    "Exotic": 0.20,
    "Legendary": 0.05,
}


def roll_mission_rewards(count: int = None) -> list[dict]:
    """
    Roll 1-2 random rewards for mission completion.
    
    Args:
        count: Number of rewards (1 or 2). If None, randomly chosen.
    
    Returns:
        List of reward dicts with id, name, type, and metadata.
    """
    if count is None:
        count = random.choices([1, 2], weights=[0.6, 0.4], k=1)[0]
    
    count = min(2, max(1, count))  # Clamp between 1-2
    
    reward_ids = list(REWARD_POOL.keys())
    reward_weights = [REWARD_POOL[rid]["weight"] for rid in reward_ids]
    
    selected = random.choices(reward_ids, weights=reward_weights, k=count)
    
    rewards = []
    for reward_id in selected:
        reward = REWARD_POOL[reward_id].copy()
        reward["id"] = reward_id
        rewards.append(reward)
    
    return rewards


# ═══════════════════════════════════════════════════════════════════
# MUSEUM RELIC DROP SYSTEM
# ═══════════════════════════════════════════════════════════════════

def roll_relic_drop(zone_id: str = None) -> dict | None:
    """
    Check if a relic should drop and roll its rarity.
    
    Args:
        zone_id: The zone where the relic is dropped from.
                Can be: "fishing", "botany", "archaeology", "scavenge", or None for special events.
    
    Returns:
        Relic dict with id, name, emoji, rarity if drop succeeds.
        None if no relic drops (94% of the time).
    """
    from game.data import RELICS, RELIC_DROP_BIASES
    
    # 6% base relic drop chance
    if random.random() > 0.06:
        return None
    
    # Relic dropped! Now roll rarity with zone biases
    biases = RELIC_DROP_BIASES.get(zone_id or "base", RELIC_DROP_BIASES["base"])
    
    # Clamp negative values to 0
    biases = {k: max(0, v) for k, v in biases.items()}
    
    # Normalize to valid probabilities
    total = sum(biases.values())
    if total == 0:
        biases = RELIC_DROP_BIASES["base"]
        total = sum(biases.values())
    
    # Roll rarity
    rarities = list(biases.keys())
    weights = [biases[r] for r in rarities]
    chosen_rarity = random.choices(rarities, weights=weights, k=1)[0]
    
    # Get all relics of this rarity that can drop from this zone
    matching_relics = []
    for relic_id, relic_data in RELICS.items():
        if relic_data["rarity"] == chosen_rarity:
            # Check if this relic can drop from this zone
            if zone_id is None or zone_id in relic_data["source_zones"]:
                matching_relics.append((relic_id, relic_data))
    
    if not matching_relics:
        # Fallback: try without zone filter
        matching_relics = [
            (relic_id, relic_data)
            for relic_id, relic_data in RELICS.items()
            if relic_data["rarity"] == chosen_rarity
        ]
    
    if not matching_relics:
        return None
    
    # Pick random relic
    relic_id, relic_data = random.choice(matching_relics)
    
    return {
        "id": relic_id,
        "name": relic_data["name"],
        "emoji": relic_data["emoji"],
        "rarity": chosen_rarity,
        "set_id": relic_data["set_id"],
        "description": relic_data["description"],
    }

