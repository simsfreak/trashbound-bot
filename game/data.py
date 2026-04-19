from datetime import datetime

ZONES = {
    "back_alley": {
        "name": "Back Alley",
        "unlock_level": 1,
        "description": "Soggy boxes, lost sneakers, and low-tier treasure.",
        "banner": "🗑️ ╔═ BACK ALLEY ═╗",
        "unicode_style": "⌁ damp / shady / beginner luck ⌁",
        "danger": "Low",
        "luck": "Slightly cursed",
        "image": "assets/zones/back_alley.png",
    },
    "apartment_bins": {
        "name": "Apartment Bins",
        "unlock_level": 3,
        "description": "Household leftovers, mystery decor, and weird little jackpots.",
        "banner": "🏢 ╔═ APARTMENT BINS ═╗",
        "unicode_style": "✦ domestic chaos / hidden jackpots ✦",
        "danger": "Medium",
        "luck": "Nosy gremlin good",
        "image": "assets/zones/apartment_bins.png",
    },
    "restaurant_dumpster": {
        "name": "Restaurant Dumpster",
        "unlock_level": 5,
        "description": "Greasy chaos, cursed leftovers, and surprisingly good loot.",
        "banner": "🍔 ╔═ RESTAURANT DUMPSTER ═╗",
        "unicode_style": "⚠ greasy / loud / reward-heavy ⚠",
        "danger": "Medium",
        "luck": "Suspiciously tasty",
        "image": "assets/zones/restaurant_dumpster.png",
    },
    "mall_rear_lot": {
        "name": "Mall Rear Lot",
        "unlock_level": 8,
        "description": "Discarded fashion, promo junk, and elite trash energy.",
        "banner": "🛍️ ╔═ MALL REAR LOT ═╗",
        "unicode_style": "⟡ glossy / expensive / high-tier rot ⟡",
        "danger": "High",
        "luck": "Luxury filth",
        "image": "assets/zones/mall_rear_lot.png",
    },
}

ITEMS = {
    "old_shoe": {
        "name": "Old Shoe",
        "rarity": "Common",
        "coins": 5,
        "xp": 5,
        "zone_ids": ["back_alley"],
        "image": "assets/items/old_shoe.png",
        "emoji": "👟",
        "flavor": "Still has main character energy somehow.",
        "kind": "material",
    },
    "scrap_metal": {
        "name": "Scrap Metal",
        "rarity": "Common",
        "coins": 10,
        "xp": 7,
        "zone_ids": ["back_alley", "apartment_bins"],
        "image": "https://raw.githubusercontent.com/simsfreak/trashbound-bot/main/assets/items/scrap_metal.png",
        "emoji": "🔩",
        "flavor": "Rusty, crunchy, and weirdly valuable.",
        "kind": "material",
    },
    "broken_phone": {
        "name": "Broken Phone",
        "rarity": "Rare",
        "coins": 25,
        "xp": 20,
        "zone_ids": ["apartment_bins"],
        "image": "assets/items/broken_phone.png",
        "emoji": "📱",
        "flavor": "Screen destroyed. Aura intact.",
        "kind": "material",
    },
    "mystery_box": {
        "name": "Mystery Box",
        "rarity": "Epic",
        "coins": 50,
        "xp": 35,
        "zone_ids": ["restaurant_dumpster", "mall_rear_lot"],
        "image": "assets/items/mystery_box.png",
        "emoji": "🎁",
        "flavor": "Suspicious. Glorious. Probably unstable.",
        "kind": "material",
    },
    "trash_crown": {
        "name": "Trash Crown",
        "rarity": "Legendary",
        "coins": 200,
        "xp": 60,
        "zone_ids": ["mall_rear_lot"],
        "image": "assets/items/trash_crown.png",
        "emoji": "👑",
        "flavor": "Proof that garbage can, in fact, be royalty.",
        "kind": "material",
    },
    "iron_gloves": {
        "name": "Iron Gloves",
        "rarity": "Uncommon",
        "coins": 30,
        "xp": 0,
        "zone_ids": [],
        "image": "",
        "emoji": "🧤",
        "flavor": "Rough forged and ready for deeper digging.",
        "kind": "equipment",
        "equip_slot": "hands",
        "equip_bonus": "+10% bonus coins on dive",
    },
    "sole_stompers": {
        "name": "Sole Stompers",
        "rarity": "Uncommon",
        "coins": 28,
        "xp": 0,
        "zone_ids": [],
        "image": "",
        "emoji": "🥾",
        "flavor": "Two dead shoes became one chaotic upgrade.",
        "kind": "equipment",
        "equip_slot": "feet",
        "equip_bonus": "+5 flat XP on dive",
    },
    "glitch_charm": {
        "name": "Glitch Charm",
        "rarity": "Rare",
        "coins": 65,
        "xp": 0,
        "zone_ids": [],
        "image": "",
        "emoji": "📿",
        "flavor": "It vibrates like it knows a secret route to loot.",
        "kind": "equipment",
        "equip_slot": "trinket",
        "equip_bonus": "+8% bonus rare chance",
    },
    "golden_potion": {
        "name": "Golden Potion",
        "rarity": "Epic",
        "coins": 120,
        "xp": 0,
        "zone_ids": [],
        "image": "",
        "emoji": "🧃",
        "flavor": "Liquid goblin ambition. Drink responsibly. Or not.",
        "kind": "consumable",
        "effect_id": "xp_boost",
        "effect_label": "XP Boost",
        "effect_multiplier": 1.5,
        "duration_minutes": 60,
        "use_text": "+50% XP for 1 hour of play",
    },
    "rat_king_sigil": {
        "name": "Rat King Sigil",
        "rarity": "Legendary",
        "coins": 220,
        "xp": 0,
        "zone_ids": [],
        "image": "",
        "emoji": "🐀",
        "flavor": "The alley now respects your filth credentials.",
        "kind": "equipment",
        "equip_slot": "charm",
        "equip_bonus": "+12% extra item chance",
    },
    "burned_scrap": {
        "name": "Burned Scrap",
        "rarity": "Rare",
        "coins": 45,
        "xp": 18,
        "zone_ids": [],
        "image": "",
        "emoji": "🔥",
        "flavor": "Still warm. Still somehow useful.",
        "kind": "event",
    },
    "frozen_phone": {
        "name": "Frozen Phone",
        "rarity": "Rare",
        "coins": 50,
        "xp": 22,
        "zone_ids": [],
        "image": "",
        "emoji": "🧊",
        "flavor": "The screen is dead. The vibes are immaculate.",
        "kind": "event",
    },
}

MIX_RECIPES = [
    {
        "key": "iron_gloves_recipe",
        "name": "Forge Iron Gloves",
        "ingredients": {"scrap_metal": 2},
        "result_item_id": "iron_gloves",
        "result_qty": 1,
        "description": "🔩 Scrap Metal x2 → 🧤 Iron Gloves x1",
    },
    {
        "key": "sole_stompers_recipe",
        "name": "Sole Stompers",
        "ingredients": {"old_shoe": 2},
        "result_item_id": "sole_stompers",
        "result_qty": 1,
        "description": "👟 Old Shoe x2 → 🥾 Sole Stompers x1",
    },
    {
        "key": "glitch_charm_recipe",
        "name": "Glitch Charm",
        "ingredients": {"scrap_metal": 1, "broken_phone": 1},
        "result_item_id": "glitch_charm",
        "result_qty": 1,
        "description": "🔩 Scrap Metal x1 + 📱 Broken Phone x1 → 📿 Glitch Charm x1",
    },
    {
        "key": "golden_potion_recipe",
        "name": "Golden Potion",
        "ingredients": {"mystery_box": 1, "scrap_metal": 2},
        "result_item_id": "golden_potion",
        "result_qty": 1,
        "description": "🎁 Mystery Box x1 + 🔩 Scrap Metal x2 → 🧃 Golden Potion x1",
    },
    {
        "key": "rat_king_recipe",
        "name": "Rat King Sigil",
        "ingredients": {"trash_crown": 1, "mystery_box": 1},
        "result_item_id": "rat_king_sigil",
        "result_qty": 1,
        "description": "👑 Trash Crown x1 + 🎁 Mystery Box x1 → 🐀 Rat King Sigil x1",
    },
]

WEEKEND_EVENTS = [
    {
        "key": "rat_kings_blessing",
        "name": "Rat King's Blessing",
        "emoji": "🐀",
        "type": "weekend",
        "profile_line": "Rats are hoarding shiny nonsense all weekend.",
        "description": "Bonus extra-item chance. The alley is squeaking with greed.",
        "coin_multiplier": 1.0,
        "xp_multiplier": 1.0,
        "extra_item_chance": 0.20,
        "rare_bonus": 0.03,
        "event_item_id": None,
    },
    {
        "key": "gold_rush",
        "name": "Gold Rush Weekend",
        "emoji": "💰",
        "type": "weekend",
        "profile_line": "Coins are hitting different right now.",
        "description": "+50% coins on all dives this weekend.",
        "coin_multiplier": 1.5,
        "xp_multiplier": 1.0,
        "extra_item_chance": 0.0,
        "rare_bonus": 0.02,
        "event_item_id": None,
    },
    {
        "key": "unstable_mix",
        "name": "Unstable Mix Weekend",
        "emoji": "🧪",
        "type": "weekend",
        "profile_line": "The bench is hissing. Good sign honestly.",
        "description": "Mixing gets a little more chaotic and a little more rewarding.",
        "coin_multiplier": 1.0,
        "xp_multiplier": 1.0,
        "extra_item_chance": 0.10,
        "rare_bonus": 0.05,
        "event_item_id": None,
    },
    {
        "key": "dumpster_fire",
        "name": "Dumpster Fire",
        "emoji": "🔥",
        "type": "weekend",
        "profile_line": "Everything is mildly on fire and wildly profitable.",
        "description": "+30% XP. Small chance to find Burned Scrap.",
        "coin_multiplier": 1.0,
        "xp_multiplier": 1.3,
        "extra_item_chance": 0.0,
        "rare_bonus": 0.03,
        "event_item_id": "burned_scrap",
    },
]

SEASONAL_EVENTS = [
    {
        "key": "cursed_trash",
        "name": "Cursed Trash",
        "emoji": "🎃",
        "type": "seasonal",
        "months": [10],
        "profile_line": "The dumpsters are whispering again.",
        "description": "Spooky pulls and cursed flavor all month.",
        "coin_multiplier": 1.0,
        "xp_multiplier": 1.15,
        "extra_item_chance": 0.05,
        "rare_bonus": 0.04,
        "event_item_id": None,
    },
    {
        "key": "frozen_finds",
        "name": "Frozen Finds",
        "emoji": "❄️",
        "type": "seasonal",
        "months": [12, 1],
        "profile_line": "The loot is cold but weirdly premium.",
        "description": "Icy pulls, calmer chaos, and occasional Frozen Phone drops.",
        "coin_multiplier": 1.0,
        "xp_multiplier": 1.1,
        "extra_item_chance": 0.05,
        "rare_bonus": 0.05,
        "event_item_id": "frozen_phone",
    },
    {
        "key": "broken_reality",
        "name": "Broken Reality",
        "emoji": "🃏",
        "type": "seasonal",
        "months": [4],
        "profile_line": "Nothing feels correct and that kind of rules.",
        "description": "Luck spikes, labels feel cursed, and loot tables get goofy.",
        "coin_multiplier": 1.0,
        "xp_multiplier": 1.0,
        "extra_item_chance": 0.10,
        "rare_bonus": 0.06,
        "event_item_id": None,
    },
]

HELP_TEXT = (
    "• **Dive** runs a multi-step scavenging sequence with random chaos.\n"
    "• **Loot** lets you inspect items and use potions / equip crafted gear.\n"
    "• **Mix** opens the goblin lab with fixed recipes and chaos mixing.\n"
    "• **Zones** is an interactive map where you can set your active zone.\n"
    "• **Events** shows the live weekend and seasonal world modifiers."
)



def get_active_weekend_event(now: datetime | None = None) -> dict | None:
    now = now or datetime.utcnow()
    if now.weekday() not in {4, 5, 6}:
        return None
    return WEEKEND_EVENTS[now.isocalendar().week % len(WEEKEND_EVENTS)]



def get_active_seasonal_event(now: datetime | None = None) -> dict | None:
    now = now or datetime.utcnow()
    for event in SEASONAL_EVENTS:
        if now.month in event["months"]:
            return event
    return None



def get_live_events(now: datetime | None = None) -> list[dict]:
    now = now or datetime.utcnow()
    live: list[dict] = []
    weekend = get_active_weekend_event(now)
    seasonal = get_active_seasonal_event(now)
    if weekend:
        live.append(weekend)
    if seasonal:
        live.append(seasonal)
    return live
