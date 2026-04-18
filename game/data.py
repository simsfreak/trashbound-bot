ZONES = {
    "back_alley": {
        "name": "Back Alley",
        "unlock_level": 1,
        "description": "Your first grimy treasure spot.",
        "image": "assets/zones/back_alley.png",
    },
    "apartment_bins": {
        "name": "Apartment Bins",
        "unlock_level": 3,
        "description": "Household leftovers and hidden valuables.",
        "image": "assets/zones/apartment_bins.png",
    },
    "restaurant_dumpster": {
        "name": "Restaurant Dumpster",
        "unlock_level": 5,
        "description": "Greasy loot, weird food relics, and chaos.",
        "image": "assets/zones/restaurant_dumpster.png",
    },
    "mall_rear_lot": {
        "name": "Mall Rear Lot",
        "unlock_level": 8,
        "description": "Store returns, fashion junk, and jackpot finds.",
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
    },
    "scrap_metal": {
        "name": "Scrap Metal",
        "rarity": "Common",
        "coins": 10,
        "xp": 7,
        "zone_ids": ["back_alley", "apartment_bins"],
        "image": "https://raw.githubusercontent.com/simsfreak/trashbound-bot/main/assets/items/scrap_metal.png",
    },
    "broken_phone": {
        "name": "Broken Phone",
        "rarity": "Rare",
        "coins": 25,
        "xp": 20,
        "zone_ids": ["apartment_bins"],
        "image": "assets/items/broken_phone.png",
    },
    "mystery_box": {
        "name": "Mystery Box",
        "rarity": "Epic",
        "coins": 50,
        "xp": 35,
        "zone_ids": ["restaurant_dumpster", "mall_rear_lot"],
        "image": "assets/items/mystery_box.png",
    },
    "trash_crown": {
        "name": "Legendary Trash Crown 👑",
        "rarity": "Legendary",
        "coins": 200,
        "xp": 60,
        "zone_ids": ["mall_rear_lot"],
        "image": "assets/items/trash_crown.png",
    },
}
