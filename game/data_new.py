from datetime import datetime
import random

ZONES = {
    "back_alley": {
        "name": "Back Alley",
        "unlock_level": 1,
        "description": "Soggy boxes, lost sneakers, and low-tier treasure.",
        "banner": "🗑️ ╔═ BACK ALLEY ═╗",
        "unicode_style": "⌁ damp / shady / beginner luck ⌁",
        "danger": "Low",
        "luck": "Slightly cursed",
    },
    "apartment_bins": {
        "name": "Apartment Bins",
        "unlock_level": 3,
        "description": "Household leftovers, mystery decor, and weird little jackpots.",
        "banner": "🏢 ╔═ APARTMENT BINS ═╗",
        "unicode_style": "✦ domestic chaos / hidden jackpots ✦",
        "danger": "Medium",
        "luck": "Nosy gremlin good",
    },
    "restaurant_dumpster": {
        "name": "Restaurant Dumpster",
        "unlock_level": 5,
        "description": "Greasy chaos, cursed leftovers, and surprisingly good loot.",
        "banner": "🍔 ╔═ RESTAURANT DUMPSTER ═╗",
        "unicode_style": "⚠ greasy / loud / reward-heavy ⚠",
        "danger": "Medium",
        "luck": "Suspiciously tasty",
    },
    "mall_rear_lot": {
        "name": "Mall Rear Lot",
        "unlock_level": 8,
        "description": "Discarded fashion, promo junk, and elite trash energy.",
        "banner": "🛍️ ╔═ MALL REAR LOT ═╗",
        "unicode_style": "⟡ glossy / expensive / high-tier rot ⟡",
        "danger": "High",
        "luck": "Luxury filth",
    },
}

# 300 ITEMS - COMPLETELY REWORKED (EMOJI ONLY, NO IMAGES)
ITEMS = {}

# COMMON ITEMS (60)
_common_items = [
    ("crushed_soda_can", "🥤 Crushed Soda Can", "3 coins", "Flat and thirsty."),
    ("damp_newspaper", "📰 Damp Newspaper", "2 coins", "Still somewhat readable."),
    ("lost_sock", "🧦 Lost Sock", "1 coin", "Where's its pair?"),
    ("moldy_bread", "🍞 Moldy Bread Chunk", "2 coins", "Definitely not eating this."),
    ("bent_toothbrush", "🪥 Bent Toothbrush", "2 coins", "Bristles at odd angles."),
    ("torn_cardboard", "📦 Torn Cardboard Piece", "1 coin", "Structural integrity: questionable."),
    ("empty_shampoo", "🧴 Empty Shampoo Bottle", "2 coins", "Every last drop gone."),
    ("tissue_bundle", "🧻 Used Tissue Bundle", "1 coin", "Don't ask."),
    ("dead_battery", "🪫 Dead Battery", "3 coins", "0% charge. 0% hope."),
    ("sticky_wrapper", "🍬 Sticky Candy Wrapper", "1 coin", "Still tacky."),
    ("rusty_paperclip", "🧷 Rusty Paperclip", "1 coin", "Oxidized perfection."),
    ("juice_box_husk", "🧃 Juice Box Husk", "1 coin", "Sucked dry."),
    ("greasy_takeout", "🥡 Greasy Takeout Box", "2 coins", "Stains tell stories."),
    ("soap_stub", "🧼 Slippery Soap Stub", "2 coins", "Barely there."),
    ("dusty_feather", "🪶 Dusty Feather", "2 coins", "Once flew free."),
    ("cold_fry_packet", "🍟 Cold Fry Packet", "1 coin", "Grease congealed."),
    ("melted_ice_cup", "🧊 Melted Ice Cup", "1 coin", "Former beverage vessel."),
    ("empty_spray_can", "🧯 Empty Spray Can", "2 coins", "Pressure released."),
    ("scratched_coin", "🪙 Scratched Coin", "5 coins", "Worn smooth."),
    ("broken_toy_piece", "🧩 Broken Toy Piece", "1 coin", "Happiness fractured."),
    ("glass_shard", "🪟 Glass Shard", "2 coins", "Sharp and shiny."),
    ("frayed_rope_bit", "🪢 Frayed Rope Bit", "1 coin", "Unraveling story."),
    ("single_glove", "🧤 Single Glove", "2 coins", "One hand's loss."),
    ("torn_plush_ear", "🧸 Torn Plush Ear", "1 coin", "Floppy no more."),
    ("scratched_cd", "📀 Scratched CD", "3 coins", "Data... damaged?"),
    ("old_sponge", "🧽 Old Sponge", "1 coin", "Crusty with purpose."),
    ("bent_nail", "🪜 Bent Nail", "2 coins", "Can't straighten out."),
    ("splintered_wood", "🪵 Splintered Wood Chip", "1 coin", "Ouch-inducing."),
    ("cracked_lighter", "🧯 Cracked Lighter Shell", "2 coins", "Flint still there."),
    ("plastic_lid", "🧊 Plastic Lid", "1 coin", "From something sealed."),
    ("bent_staple_strip", "📎 Bent Staple Strip", "1 coin", "Binding integrity: low."),
    ("bottle_cap", "🧯 Bottle Cap", "1 coin", "Pop! ...gone."),
    ("plastic_spoon", "🥄 Cheap Plastic Spoon", "1 coin", "Bends if you look at it."),
    ("straw_wrapper", "🧃 Straw Wrapper", "1 coin", "Hollow victory."),
    ("soap_wrapper", "🧼 Soap Wrapper", "1 coin", "Empty promise of cleanliness."),
    ("feather_clump", "🪶 Feather Clump", "2 coins", "Matted together."),
    ("crumpled_receipt", "📄 Crumpled Receipt", "1 coin", "Proof of purchase. Proof of waste."),
    ("toilet_paper_core", "🧻 Toilet Paper Core", "1 coin", "The unsung hero."),
    ("sock_fragment", "🧦 Sock Fragment", "1 coin", "Tiny textile scrap."),
    ("lotion_tube", "🧴 Lotion Smear Tube", "2 coins", "Mostly empty. Mostly sticky."),
    ("battery_shell", "🪫 Battery Shell", "1 coin", "Depleted container."),
    ("ice_cream_stick", "🧊 Ice Cream Stick", "1 coin", "Sweet memories, wooden remains."),
    ("juice_straw", "🧃 Juice Straw", "1 coin", "Bent and useless."),
    ("soda_tab", "🧯 Soda Tab", "1 coin", "Twist-off proof."),
    ("loose_thread_ball", "🧵 Loose Thread Ball", "2 coins", "Tangled mess."),
    ("weak_magnet", "🧲 Weak Magnet Piece", "2 coins", "Barely pulls."),
    ("soap_sliver", "🧼 Soap Sliver", "1 coin", "Final fragment."),
    ("small_pebble", "🪨 Small Pebble", "1 coin", "Rocky reject."),
    ("tape_scrap", "📦 Tape Scrap", "1 coin", "Still sticky."),
    ("safety_pin", "🧷 Safety Pin", "1 coin", "Secured nothing."),
    ("rust_dust", "🧯 Rust Dust Pile", "1 coin", "Oxidized dreams."),
    ("plastic_fragment", "🧴 Plastic Fragment", "1 coin", "Brittle shard."),
    ("paper_scrap", "🧻 Paper Scrap", "1 coin", "Worthless parchment."),
    ("puzzle_piece", "🧩 Puzzle Piece", "1 coin", "Part of something lost."),
    ("stuffing_fluff", "🧸 Stuffing Fluff", "1 coin", "Polyester dreams."),
    ("rubber_glove_tip", "🧤 Rubber Glove Tip", "1 coin", "Fingertip of utility."),
    ("bark_strip", "🪵 Bark Strip", "1 coin", "Tree skin scrap."),
    ("grease_rag", "🧼 Grease Smear Rag", "1 coin", "Barely a rag anymore."),
    ("ice_wrapper", "🧊 Ice Wrapper", "1 coin", "Frosty packaging."),
    ("drink_seal_film", "🧃 Drink Seal Film", "1 coin", "Protective nothing."),
]

for item_id, name, coins_text, flavor in _common_items:
    ITEMS[item_id] = {
        "name": name,
        "rarity": "Common",
        "coins": int(coins_text.split()[0]),
        "xp": 1,
        "flavor": flavor,
    }

# UNCOMMON ITEMS (80)
_uncommon_items = [
    ("polished_coin", "🪙 Polished Coin", "8 coins", "Shiny with intent."),
    ("half_full_bottle", "🧴 Half-Full Bottle", "5 coins", "Hydration potential."),
    ("patched_plush", "🧸 Patched Plush Toy", "6 coins", "Repair job complete."),
    ("reinforced_box", "📦 Reinforced Box Piece", "4 coins", "Sturdier than usual."),
    ("steel_clip", "🧷 Steel Clip", "4 coins", "Holds things firmly."),
    ("sealed_juice_pack", "🧃 Sealed Juice Pack", "5 coins", "Still sealed!"),
    ("metal_spoon", "🥄 Metal Spoon", "6 coins", "Doesn't bend."),
    ("playable_cd", "📀 Playable CD", "8 coins", "Data intact!"),
    ("working_lighter", "🧯 Working Lighter", "7 coins", "Flicks to life."),
    ("scented_soap", "🧼 Scented Soap Bar", "6 coins", "Still smells good."),
    ("matching_gloves", "🧤 Matching Gloves", "7 coins", "A pair!"),
    ("pair_socks", "🧦 Pair of Socks", "6 coins", "Sock reunion."),
    ("clean_feather", "🪶 Clean Feather", "5 coins", "Pristine plume."),
    ("toy_fragment_set", "🧩 Toy Fragment Set", "6 coins", "Multiple pieces!"),
    ("paper_roll", "🧻 Paper Roll", "4 coins", "Unused stock."),
    ("rechargeable_battery", "🪫 Rechargeable Battery", "8 coins", "Second life possible."),
    ("ice_box_lid", "🧊 Ice Box Lid", "5 coins", "Cooling capacity remains."),
    ("strong_rope", "🪢 Strong Rope Piece", "7 coins", "Doesn't fray."),
    ("functional_magnet", "🧲 Functional Magnet", "8 coins", "Still pulls!"),
    ("half_shampoo", "🧴 Shampoo Bottle (Half)", "6 coins", "Enough for several washes."),
    ("notebook_page", "📄 Notebook Page", "4 coins", "Clean and blank."),
    ("energy_drink_can", "🧃 Energy Drink Can", "6 coins", "Still has that metallic shine."),
    ("smooth_glass", "🪟 Smooth Glass Piece", "5 coins", "Edges worn safe."),
    ("half_spray_can", "🧯 Spray Can (Half)", "6 coins", "Still has pressure."),
    ("button_eye_toy", "🧸 Button Eye Toy", "5 coins", "Watching forever."),
    ("box_of_clips", "🧷 Box of Clips", "7 coins", "Organized collection."),
    ("wooden_handle", "🪵 Wooden Handle", "6 coins", "Grip intact."),
    ("cooler_brick", "🧊 Cooler Brick", "7 coins", "Cold retention potential."),
    ("soap_brick", "🧼 Soap Brick", "6 coins", "Solid cleaning power."),
    ("coin_stack", "🪙 Coin Stack", "12 coins", "Multiple denominations."),
    ("sealed_package", "📦 Sealed Package", "8 coins", "What's inside?"),
    ("work_gloves", "🧤 Work Gloves", "7 coins", "Built for labor."),
    ("warm_socks", "🧦 Warm Socks", "6 coins", "Insulation included."),
    ("strong_magnet", "🧲 Strong Magnet", "9 coins", "Pulls firmly."),
    ("puzzle_set", "🧩 Puzzle Set", "7 coins", "Pieces together!"),
    ("lotion_bottle", "🧴 Lotion Bottle", "6 coins", "Half-full luxury."),
    ("drink_pack", "🧃 Drink Pack", "5 coins", "Sealed beverage."),
    ("refillable_can", "🧯 Refillable Can", "7 coins", "Ready for more."),
    ("rope_coil", "🪢 Rope Coil", "8 coins", "Organized length."),
    ("storage_lid", "🧊 Storage Lid", "6 coins", "Keeps things in."),
    ("carved_stick", "🪵 Carved Stick", "7 coins", "Someone's handiwork."),
    ("mini_plush", "🧸 Mini Plush", "6 coins", "Tiny companion."),
    ("feather_charm", "🪶 Feather Charm", "5 coins", "Decorative plume."),
    ("clip_bundle", "🧷 Clip Bundle", "6 coins", "Organized chaos."),
    ("soft_paper_roll", "🧻 Soft Paper Roll", "5 coins", "Premium texture."),
    ("music_disc", "📀 Music Disc", "9 coins", "Data preserved."),
    ("soap_block", "🧼 Soap Block", "6 coins", "Industrial strength."),
    ("clean_bottle", "🧴 Clean Bottle", "5 coins", "Usable container."),
    ("magnet_ring", "🧲 Magnet Ring", "8 coins", "Circular pull."),
    ("coin_bundle", "🪙 Coin Bundle", "15 coins", "Significant collection."),
    ("juice_crate_piece", "🧃 Juice Crate Piece", "4 coins", "Structural element."),
    ("spray_nozzle", "🧯 Spray Nozzle", "6 coins", "Functional part."),
    ("rubber_gloves", "🧤 Rubber Gloves", "7 coins", "Protection in pairs."),
    ("thick_socks", "🧦 Thick Socks", "6 coins", "Maximum cushioning."),
    ("cooling_pack", "🧊 Cooling Pack", "7 coins", "Temperature control."),
    ("toy_set", "🧩 Toy Set", "8 coins", "Complete collection."),
    ("plush_doll", "🧸 Plush Doll", "7 coins", "Huggable companion."),
    ("feather_stack", "🪶 Feather Stack", "6 coins", "Layered softness."),
    ("clip_set", "🧷 Clip Set", "6 coins", "Organized holding."),
    ("soap_stack", "🧼 Soap Stack", "7 coins", "Multiple bars."),
    ("polished_coin_stack", "🪙 Polished Coin Stack", "18 coins", "Gleaming fortune."),
    ("ribbon_roll", "🎀 Ribbon Roll", "8 coins", "Decorative material."),
    ("bottle_collection", "🧴 Bottle Collection", "9 coins", "Plastic treasury."),
    ("feather_bundle", "🪶 Feather Bundle", "8 coins", "Fluffy mass."),
    ("magnet_collection", "🧲 Magnet Collection", "10 coins", "Attractive force."),
    ("puzzle_collection", "🧩 Puzzle Collection", "9 coins", "Many pieces."),
    ("plush_collection", "🧸 Plush Collection", "10 coins", "Soft squad."),
]

for item_id, name, coins_text, flavor in _uncommon_items:
    ITEMS[item_id] = {
        "name": name,
        "rarity": "Uncommon",
        "coins": int(coins_text.split()[0]),
        "xp": 2,
        "flavor": flavor,
    }

# RARE ITEMS (80) - Weird lucky finds
_rare_items = [
    ("ratfang_token", "🦷 Ratfang Token", "15 coins", "Proof of alley citizenship."),
    ("velvet_rust_ribbon", "🎀 Velvet Rust Ribbon", "18 coins", "Fancy decay."),
    ("mooncap_charm", "🌙 Mooncap Charm", "16 coins", "Celestial trinket."),
    ("gilded_drain_key", "🗝️ Gilded Drain Key", "20 coins", "Unlocks secrets."),
    ("cracked_halo_shard", "😇 Cracked Halo Shard", "22 coins", "Fallen grace."),
    ("saints_soda_tab", "🥤 Saint's Soda Tab", "14 coins", "Blessed beverage proof."),
    ("mothglass_pendant", "🦋 Mothglass Pendant", "19 coins", "Delicate attraction."),
    ("music_box_tooth", "🎵 Music Box Tooth", "17 coins", "Melodic fragment."),
    ("goldvein_spoon", "🥄 Goldvein Spoon", "21 coins", "Precious utility."),
    ("wishing_wire_loop", "🔗 Wishing Wire Loop", "18 coins", "Circular desire."),
    ("porcelain_knuckle", "🦴 Porcelain Knuckle", "16 coins", "Fine-boned relic."),
    ("star_stained_locket", "🌟 Star-Stained Locket", "20 coins", "Celestial container."),
    ("copperheart_fuse", "🔌 Copperheart Fuse", "19 coins", "Powered by love?"),
    ("floodborn_coin_bloom", "🪙 Floodborn Coin Bloom", "22 coins", "Water-born wealth."),
    ("whisperfoil_scrap", "✨ Whisperfoil Scrap", "18 coins", "Silent material."),
    ("neon_prayer_clip", "📿 Neon Prayer Clip", "17 coins", "Glowing devotion."),
    ("cinderlace_relic", "🕯️ Cinderlace Relic", "20 coins", "Burned beauty."),
    ("crown_pulltab", "👑 Crown Pulltab", "21 coins", "Regal opening."),
    ("shimmergut_marble", "🫧 Shimmergut Marble", "19 coins", "Iridescent orb."),
    ("gravewax_charm", "🪦 Gravewax Charm", "16 coins", "Respectfully haunting."),
    ("alley_eye_bead", "🧿 Alley Eye Bead", "18 coins", "The alley watches."),
    ("cracked_luck_orb", "🔮 Cracked Luck Orb", "20 coins", "Fortune fractured."),
    ("singing_coin", "🪙 Singing Coin", "22 coins", "Melodic metal."),
    ("fate_thread_bundle", "🧵 Fate Thread Bundle", "19 coins", "Woven destiny."),
    ("spirit_plush_core", "🧸 Spirit Plush Core", "17 coins", "Essence of comfort."),
    ("echo_feather", "🪶 Echo Feather", "18 coins", "Resounding plume."),
    ("pulse_magnet", "🧲 Pulse Magnet", "20 coins", "Beating attraction."),
    ("memory_soap", "🧼 Memory Soap", "16 coins", "Cleansing nostalgia."),
    ("lucky_parcel", "📦 Lucky Parcel", "21 coins", "Sealed fortune."),
    ("knot_of_fortune", "🪢 Knot of Fortune", "19 coins", "Tied luck."),
    ("binding_clip", "🧷 Binding Clip", "17 coins", "Fate fastener."),
    ("whisper_stick", "🪵 Whisper Stick", "18 coins", "Silent wood."),
    ("ember_can", "🧯 Ember Can", "20 coins", "Smoldering spray."),
    ("nectar_bottle", "🧃 Nectar Bottle", "22 coins", "Liquid sweetness."),
    ("phantom_glove", "🧤 Phantom Glove", "19 coins", "Ghostly protection."),
    ("traveler_sock", "🧦 Traveler Sock", "16 coins", "Journey-worn comfort."),
    ("frozen_coin", "🧊 Frozen Coin", "21 coins", "Icy wealth."),
    ("destiny_piece", "🧩 Destiny Piece", "18 coins", "Fated fragment."),
    ("worn_guardian_toy", "🧸 Worn Guardian Toy", "17 coins", "Protective companion."),
    ("storm_feather", "🪶 Storm Feather", "20 coins", "Thunder-touched plume."),
    ("watcher_bead", "🧿 Watcher Bead", "19 coins", "Ever-vigilant orb."),
    ("glow_bottle", "🧴 Glow Bottle", "22 coins", "Luminescent vessel."),
    ("double_coin", "🪙 Double Coin", "25 coins", "Twice the wealth."),
    ("lucky_pin", "🧷 Lucky Pin", "18 coins", "Secured fortune."),
    ("purity_soap", "🧼 Purity Soap", "19 coins", "Cleansing essence."),
    ("spirit_wood", "🪵 Spirit Wood", "20 coins", "Sentient timber."),
    ("radiant_juice", "🧃 Radiant Juice", "21 coins", "Glowing beverage."),
    ("core_magnet", "🧲 Core Magnet", "22 coins", "Essential attraction."),
    ("puzzle_core", "🧩 Puzzle Core", "19 coins", "Central mystery."),
    ("soul_plush", "🧸 Soul Plush", "20 coins", "Essence doll."),
    ("wing_feather", "🪶 Wing Feather", "21 coins", "Flight fragment."),
    ("mystic_bead", "🧿 Mystic Bead", "23 coins", "Esoteric sphere."),
    ("essence_bottle", "🧴 Essence Bottle", "22 coins", "Concentrated being."),
    ("ancient_coin", "🪙 Ancient Coin", "26 coins", "Aged fortune."),
    ("sacred_pin", "🧷 Sacred Pin", "19 coins", "Holy fastener."),
    ("blessed_soap", "🧼 Blessed Soap", "20 coins", "Sanctified cleansing."),
    ("old_growth_stick", "🪵 Old Growth Stick", "21 coins", "Aged timber."),
    ("elixir_bottle", "🧃 Elixir Bottle", "24 coins", "Magical draught."),
    ("gravity_magnet", "🧲 Gravity Magnet", "23 coins", "Pulling force."),
    ("final_piece", "🧩 Final Piece", "20 coins", "Completion fragment."),
]

for item_id, name, coins_text, flavor in _rare_items:
    ITEMS[item_id] = {
        "name": name,
        "rarity": "Rare",
        "coins": int(coins_text.split()[0]),
        "xp": 5,
        "flavor": flavor,
    }

# EPIC ITEMS (50) - Beautiful junk relics
_epic_items = [
    ("rustbound_crown_frag", "👑 Rustbound Crown Fragment", "60 coins", "Majestic oxidation."),
    ("voidglass_shard", "🌌 Voidglass Shard", "65 coins", "Bottomless fragment."),
    ("embercore_bottle", "🔥 Embercore Bottle", "70 coins", "Burning essence."),
    ("all_seeing_bead", "🧿 All-Seeing Bead", "68 coins", "Omniscient orb."),
    ("kings_lost_coin", "🪙 King's Lost Coin", "72 coins", "Royal fortune."),
    ("fateweaver_thread", "🧵 Fateweaver Thread", "66 coins", "Destiny material."),
    ("celestial_feather", "🪶 Celestial Feather", "70 coins", "Heaven-touched plume."),
    ("core_singularity_magnet", "🧲 Core Singularity Magnet", "75 coins", "Reality-bending pull."),
    ("guardian_heart_plush", "🧸 Guardian Heart Plush", "64 coins", "Protective essence."),
    ("worldpiece_fragment", "🧩 Worldpiece Fragment", "70 coins", "Universal shard."),
    ("tidebound_relic", "🌊 Tidebound Relic", "68 coins", "Ocean-locked artifact."),
    ("echo_orb", "🔮 Echo Orb", "71 coins", "Resounding sphere."),
    ("ancient_root_core", "🪵 Ancient Root Core", "67 coins", "Primordial timber."),
    ("liquid_luck_vial", "🧴 Liquid Luck Vial", "73 coins", "Concentrated fortune."),
    ("eternal_binding_clip", "🧷 Eternal Binding Clip", "65 coins", "Forever-fastened."),
    ("purified_essence_block", "🧼 Purified Essence Block", "69 coins", "Condensed purity."),
    ("timefrozen_core", "🧊 Timefrozen Core", "70 coins", "Temporal preservation."),
    ("radiance_flask", "🧃 Radiance Flask", "72 coins", "Glowing container."),
    ("phantom_grip", "🧤 Phantom Grip", "66 coins", "Spectral protection."),
    ("wanderer_relic", "🧦 Wanderer Relic", "68 coins", "Journey artifact."),
    ("fortune_cluster", "🪙 Fortune Cluster", "76 coins", "Wealth constellation."),
    ("void_eye_charm", "🧿 Void Eye Charm", "71 coins", "Abyssal watcher."),
    ("skyfall_feather", "🪶 Skyfall Feather", "69 coins", "Falling star plume."),
    ("polarity_core", "🧲 Polarity Core", "73 coins", "Balanced attraction."),
    ("dream_plush", "🧸 Dream Plush", "67 coins", "Slumber companion."),
    ("origin_fragment", "🧩 Origin Fragment", "70 coins", "Primordial piece."),
    ("essence_core", "🧴 Essence Core", "72 coins", "Being-concentrated."),
    ("infinity_pin", "🧷 Infinity Pin", "74 coins", "Endless fastener."),
    ("soul_cleanser", "🧼 Soul Cleanser", "71 coins", "Spirit purifier."),
    ("frozen_star", "🧊 Frozen Star", "70 coins", "Crystallized celestial."),
    ("liquid_starlight", "🧃 Liquid Starlight", "75 coins", "Captured brilliance."),
    ("shadow_grip", "🧤 Shadow Grip", "68 coins", "Dark protection."),
    ("timeless_sock", "🧦 Timeless Sock", "66 coins", "Eternal footwear."),
    ("elderwood_core", "🪵 Elderwood Core", "72 coins", "Ancient timber heart."),
    ("myth_coin", "🪙 Myth Coin", "78 coins", "Legendary wealth."),
    ("cosmic_bead", "🧿 Cosmic Bead", "74 coins", "Universe sphere."),
    ("nova_feather", "🪶 Nova Feather", "73 coins", "Exploding plume."),
    ("singularity_ring", "🧲 Singularity Ring", "76 coins", "Point of no return."),
    ("eternal_plush", "🧸 Eternal Plush", "71 coins", "Forever friend."),
    ("creation_piece", "🧩 Creation Piece", "75 coins", "Making fragment."),
    ("core_relic", "🧴 Core Relic", "72 coins", "Essence artifact."),
    ("binding_fate", "🧷 Binding Fate Pin", "73 coins", "Destiny fastener."),
    ("cleansing_origin", "🧼 Cleansing Origin", "71 coins", "Purification source."),
    ("frozen_eternity", "🧊 Frozen Eternity", "76 coins", "Forever frozen."),
    ("beacon_cloth", "🧣 Beacon Cloth", "70 coins", "Guiding textile."),
    ("fortune_knot", "🪢 Fortune Knot", "74 coins", "Tied success."),
    ("harmony_feather", "🪶 Harmony Feather", "72 coins", "Balanced plume."),
    ("core_magnet_elite", "🧲 Elite Core Magnet", "77 coins", "Premium pull."),
    ("victory_plush", "🧸 Victory Plush", "73 coins", "Winning companion."),
]

for item_id, name, coins_text, flavor in _epic_items:
    ITEMS[item_id] = {
        "name": name,
        "rarity": "Epic",
        "coins": int(coins_text.split()[0]),
        "xp": 10,
        "flavor": flavor,
    }

# LEGENDARY ITEMS (30) - Myth-level garbage miracles
_legendary_items = [
    ("crown_of_dump_king", "👑 Crown of the Dump King", "200 coins", "Absolute garbage royalty."),
    ("heart_of_void_pile", "🌌 Heart of the Void Pile", "220 coins", "Boundless darkness core."),
    ("eternal_ember_relic", "🔥 Eternal Ember Relic", "210 coins", "Undying flame artifact."),
    ("fallen_halo_core", "😇 Fallen Halo Core", "225 coins", "Celestial downfall."),
    ("infinite_coin_bloom", "🪙 Infinite Coin Bloom", "240 coins", "Unlimited wealth flower."),
    ("eye_of_lost_things", "🧿 Eye of Lost Things", "230 coins", "All-finding orb."),
    ("wing_of_forgotten", "🪶 Wing of the Forgotten", "215 coins", "Memory-touched plume."),
    ("gravity_well_core", "🧲 Gravity Well Core", "235 coins", "Attraction singularity."),
    ("soulbound_plush_king", "🧸 Soulbound Plush King", "220 coins", "Spirit-bound majesty."),
    ("final_reality_piece", "🧩 Final Reality Piece", "225 coins", "Ultimate fragment."),
    ("ocean_memory_core", "🌊 Ocean Memory Core", "228 coins", "Aquatic remembrance."),
    ("orb_of_endless_finds", "🔮 Orb of Endless Finds", "232 coins", "Infinite discovery."),
    ("worldroot_fragment", "🪵 Worldroot Fragment", "218 coins", "Earth's foundation shard."),
    ("essence_of_fortune", "🧴 Essence of Fortune", "238 coins", "Luck distilled."),
    ("pin_of_binding_fate", "🧷 Pin of Binding Fate", "227 coins", "Destiny locked."),
    ("purity_core", "🧼 Purity Core", "222 coins", "Absolute cleanliness."),
    ("time_crystal", "🧊 Time Crystal", "240 coins", "Temporal imprisonment."),
    ("elixir_of_overflow", "🧃 Elixir of Overflow", "235 coins", "Abundance liquid."),
    ("hand_of_diver", "🧤 Hand of the Diver", "226 coins", "Scrapper's destiny."),
    ("step_of_endless", "🧦 Step of the Endless", "229 coins", "Infinite journey."),
    ("coin_of_all_luck", "🪙 Coin of All Luck", "245 coins", "Universal fortune."),
    ("all_seeing_core", "🧿 All-Seeing Core", "233 coins", "Omniscience sphere."),
    ("celestial_wing_core", "🪶 Celestial Wing Core", "231 coins", "Heaven's feather heart."),
    ("core_of_pulling_fate", "🧲 Core of Pulling Fate", "237 coins", "Destiny attraction."),
    ("heart_of_companions", "🧸 Heart of Companions", "224 coins", "Friendship essence."),
    ("piece_of_everything", "🧩 Piece of Everything", "228 coins", "Universal component."),
    ("liquid_infinity", "🧴 Liquid Infinity", "242 coins", "Boundless potion."),
    ("fate_anchor", "🧷 Fate Anchor", "230 coins", "Destiny's lock."),
    ("cleansing_origin", "🧼 Cleansing Origin", "226 coins", "Purity source."),
    ("frozen_eternity", "🧊 Frozen Eternity", "244 coins", "Forever crystallized."),
]

for item_id, name, coins_text, flavor in _legendary_items:
    ITEMS[item_id] = {
        "name": name,
        "rarity": "Legendary",
        "coins": int(coins_text.split()[0]),
        "xp": 20,
        "flavor": flavor,
    }

# REMAINING COMMON + UNCOMMON + RARE + EPIC + LEGENDARY (items 251-300)
_remaining_items = [
    ("sticky_drink_pouch", "🧃 Sticky Drink Pouch", "Common", "2 coins", "Adhesive packaging."),
    ("damp_napkin_ball", "🧻 Damp Napkin Ball", "Common", "1 coin", "Crumpled moisture."),
    ("cracked_lotion_pump", "🧴 Cracked Lotion Pump", "Common", "2 coins", "Broken dispenser."),
    ("inside_out_sock", "🧦 Inside-Out Sock", "Common", "1 coin", "Textile reversal."),
    ("splinter_bundle", "🪵 Splinter Bundle", "Common", "2 coins", "Painful collection."),
    ("bent_safety_pin", "🧷 Bent Safety Pin", "Common", "1 coin", "Compromised security."),
    ("frosted_plastic_lid", "🧊 Frosted Plastic Lid", "Common", "1 coin", "Icy covering."),
    ("flattened_snack_box", "📦 Flattened Snack Box", "Common", "1 coin", "Compressed cardboard."),
    ("greasy_soap_chunk", "🧼 Greasy Soap Chunk", "Common", "2 coins", "Oily cleanser."),
    ("leaking_battery_shell", "🪫 Leaking Battery Shell", "Common", "1 coin", "Hazardous container."),
    ("sealed_mystery_drink", "🧃 Sealed Mystery Drink", "Uncommon", "8 coins", "Unknown beverage."),
    ("half_clean_bottle", "🧴 Half-Clean Bottle", "Uncommon", "6 coins", "Partially sanitized."),
    ("mismatched_sock_pair", "🧦 Mismatched Sock Pair", "Uncommon", "7 coins", "Unlikely couple."),
    ("smooth_driftwood", "🪵 Smooth Driftwood Piece", "Uncommon", "8 coins", "Wave-worn wood."),
    ("reinforced_clip", "🧷 Reinforced Clip", "Uncommon", "7 coins", "Heavy-duty fastener."),
    ("clean_soap_bar", "🧼 Clean Soap Bar", "Uncommon", "6 coins", "Unused luxury."),
    ("worn_coin_stack", "🪙 Worn Coin Stack", "Uncommon", "10 coins", "Weathered fortune."),
    ("packed_supply_box", "📦 Packed Supply Box", "Uncommon", "9 coins", "Full container."),
    ("strong_pull_magnet", "🧲 Strong Pull Magnet", "Uncommon", "10 coins", "Powerful attraction."),
    ("cooling_gel_pack", "🧊 Cooling Gel Pack", "Uncommon", "8 coins", "Temperature control."),
    ("repaired_plush_toy", "🧸 Repaired Plush Toy", "Uncommon", "8 coins", "Restored companion."),
    ("linked_puzzle_set", "🧩 Linked Puzzle Set", "Uncommon", "9 coins", "Connected pieces."),
    ("utility_gloves", "🧤 Utility Gloves", "Uncommon", "8 coins", "Practical protection."),
    ("pressurized_canister", "🧃 Pressurized Canister", "Uncommon", "7 coins", "Sealed pressure."),
    ("polished_feather", "🪶 Polished Feather", "Uncommon", "6 coins", "Refined plume."),
    ("echoing_coin", "🪙 Echoing Coin", "Rare", "18 coins", "Resonant wealth."),
    ("alleywatch_charm", "🧿 Alleywatch Charm", "Rare", "20 coins", "Guardian sphere."),
    ("tangle_fate_thread", "🧵 Tangle of Fate Thread", "Rare", "19 coins", "Complex destiny."),
    ("glow_residue_bottle", "🧴 Glow Residue Bottle", "Rare", "21 coins", "Luminous container."),
    ("murmur_feather", "🪶 Murmur Feather", "Rare", "18 coins", "Whispering plume."),
    ("flicker_magnet_core", "🧲 Flicker Magnet Core", "Rare", "20 coins", "Fluctuating pull."),
    ("hollow_eyed_plush", "🧸 Hollow-Eyed Plush", "Rare", "17 coins", "Empty gaze toy."),
    ("missing_corner_piece", "🧩 Missing Corner Piece", "Rare", "19 coins", "Incomplete fragment."),
    ("whisperbranch", "🪵 Whisperbranch", "Rare", "21 coins", "Murmuring timber."),
    ("luckbound_pin", "🧷 Luckbound Pin", "Rare", "20 coins", "Fortune fastener."),
    ("memory_foam_soap", "🧼 Memory Foam Soap", "Rare", "19 coins", "Remembering cleanser."),
    ("fizzing_elixir_can", "🧃 Fizzing Elixir Can", "Rare", "22 coins", "Bubbling magic."),
    ("twinflip_coin", "🪙 Twinflip Coin", "Rare", "23 coins", "Double-sided wealth."),
    ("gutter_eye_bead", "🧿 Gutter Eye Bead", "Rare", "21 coins", "Street-watching orb."),
    ("driftwing_feather", "🪶 Driftwing Feather", "Rare", "20 coins", "Wandering plume."),
    ("voidblink_eye", "🧿 Voidblink Eye", "Epic", "75 coins", "Blinking void orb."),
    ("fortune_spiral_coin", "🪙 Fortune Spiral Coin", "Epic", "80 coins", "Swirling wealth."),
    ("pulsecore_magnet", "🧲 Pulsecore Magnet", "Epic", "78 coins", "Heartbeat attraction."),
    ("distilled_luck_vial", "🧴 Distilled Luck Vial", "Epic", "82 coins", "Pure fortune."),
    ("skyfract_feather", "🪶 Skyfract Feather", "Epic", "79 coins", "Sky-broken plume."),
    ("fragment_of_pattern", "🧩 Fragment of Pattern", "Epic", "76 coins", "Design shard."),
    ("throne_of_scraps_frag", "👑 Throne of Scraps (Fragment)", "Legendary", "240 coins", "Regal discard piece."),
    ("core_of_endless_heap", "🌌 Core of the Endless Heap", "Legendary", "245 coins", "Infinite dump center."),
    ("prime_coin_of_fortune", "🪙 Prime Coin of Fortune", "Legendary", "250 coins", "Ultimate wealth."),
    ("watching_thing", "🧿 The Watching Thing", "Legendary", "255 coins", "Omniscient entity."),
]

for item_id, name, rarity, coins_text, flavor in _remaining_items:
    ITEMS[item_id] = {
        "name": name,
        "rarity": rarity,
        "coins": int(coins_text.split()[0]),
        "xp": {"Common": 1, "Uncommon": 2, "Rare": 5, "Epic": 10, "Legendary": 20}[rarity],
        "flavor": flavor,
    }

# ═══════════════════════════════════════════════════════════════════
# EXCLUSIVE COLLECTIBLES (4 CATEGORIES)
# ═══════════════════════════════════════════════════════════════════

EXCLUSIVE_ITEMS = {
    "plush_bun": {"name": "🧸 Plush Bun", "category": "Toys", "flavor": "Squishy with endless charm."},
    "ribbon_bear": {"name": "🎀 Ribbon Bear", "category": "Toys", "flavor": "Tied with the finest bow."},
    "pocket_carousel": {"name": "🎠 Pocket Carousel", "category": "Toys", "flavor": "Spinning joy miniaturized."},
    "tiny_doll": {"name": "🪆 Tiny Doll", "category": "Toys", "flavor": "Complete set of one."},
    "plushie_moon": {"name": "🌙 Plushie Moon", "category": "Toys", "flavor": "Soft as starlight."},
    "cuddly_star": {"name": "⭐ Cuddly Star", "category": "Toys", "flavor": "Radiant and huggable."},
    "magic_box": {"name": "🎁 Magic Box", "category": "Toys", "flavor": "Wonders contained."},
    "joy_bell": {"name": "🔔 Joy Bell", "category": "Toys", "flavor": "Happiness in miniature."},
    "dream_cloud": {"name": "☁️ Dream Cloud", "category": "Toys", "flavor": "Softness personified."},
    
    "shiba_inu": {"name": "🐶 Shiba Inu", "category": "Dogs", "flavor": "Doge origins eternal."},
    "corgi": {"name": "🦴 Corgi", "category": "Dogs", "flavor": "Short legs, big love."},
    "golden_retriever": {"name": "🐕 Golden Retriever", "category": "Dogs", "flavor": "Loyalty in golden fur."},
    "dachshund": {"name": "🐕‍🦺 Dachshund", "category": "Dogs", "flavor": "Long boi energy."},
    "husky": {"name": "🐕 Husky", "category": "Dogs", "flavor": "Winter spirit captured."},
    "poodle": {"name": "🐩 Poodle", "category": "Dogs", "flavor": "Fluff and elegance."},
    "beagle": {"name": "🐕 Beagle", "category": "Dogs", "flavor": "Snoofer approved."},
    "bulldog": {"name": "🐾 Bulldog", "category": "Dogs", "flavor": "Wrinkled and wonderful."},
    "pug": {"name": "🐕 Pug", "category": "Dogs", "flavor": "Squishy faced perfection."},
    
    "calico_cat": {"name": "🐱 Calico Cat", "category": "Cats", "flavor": "Tricolor chaos gremlin."},
    "moon_cat": {"name": "🌙 Moon Cat", "category": "Cats", "flavor": "Nocturnal mystery."},
    "black_cat": {"name": "🐈 Black Cat", "category": "Cats", "flavor": "Shadows given form."},
    "orange_cat": {"name": "🧡 Orange Cat", "category": "Cats", "flavor": "The brain cell collective."},
    "tabby_cat": {"name": "🐯 Tabby Cat", "category": "Cats", "flavor": "Striped sophistication."},
    "white_cat": {"name": "⚪ White Cat", "category": "Cats", "flavor": "Snow made furry."},
    "siamese_cat": {"name": "👁️ Siamese Cat", "category": "Cats", "flavor": "Elegant and demanding."},
    "persian_cat": {"name": "☁️ Persian Cat", "category": "Cats", "flavor": "Fluff overload."},
    "ragdoll_cat": {"name": "💙 Ragdoll Cat", "category": "Cats", "flavor": "Floppy bundle of love."},
    
    "seraph_wings": {"name": "🌟 Seraph Wings", "category": "Wings", "flavor": "Celestial radiance."},
    "ember_wings": {"name": "🔥 Ember Wings", "category": "Wings", "flavor": "Burning beauty."},
    "void_wings": {"name": "🌌 Void Wings", "category": "Wings", "flavor": "Darkness given flight."},
    "frost_wings": {"name": "❄️ Frost Wings", "category": "Wings", "flavor": "Crystalline majesty."},
}

# ═══════════════════════════════════════════════════════════════════
# PAWN SHOP DATA
# ═══════════════════════════════════════════════════════════════════

PAWN_TICKETS = [
    {"qty": 1, "price": 1000, "emoji": "🎟️"},
    {"qty": 5, "price": 4500, "emoji": "🎟️"},
    {"qty": 10, "price": 8500, "emoji": "🎟️"},
]

PAWN_BUFFERS = [
    {"name": "Novice Buffer", "emoji": "🧃", "bonus": "+10% XP", "price": 250, "duration_hours": 2},
    {"name": "Basic Buffer", "emoji": "🧪", "bonus": "+15% XP", "price": 400, "duration_hours": 2},
    {"name": "Greater Buffer", "emoji": "🍵", "bonus": "+20% XP", "price": 575, "duration_hours": 2},
    {"name": "Advanced Buffer", "emoji": "🧴", "bonus": "+25% XP", "price": 775, "duration_hours": 2},
    {"name": "Elite Buffer", "emoji": "🧪💖", "bonus": "+35% XP", "price": 1150, "duration_hours": 2},
    {"name": "Master Buffer", "emoji": "🌟", "bonus": "+50% XP", "price": 1850, "duration_hours": 2},
    {"name": "Legendary Buffer", "emoji": "👑", "bonus": "+75% XP", "price": 3200, "duration_hours": 2},
]

PAWN_AMULETS = [
    {"name": "Worn Amulet", "emoji": "🍀", "bonus": "+10% Luck", "price": 600, "duration_hours": 2},
    {"name": "Polished Amulet", "emoji": "🌙", "bonus": "+15% Luck", "price": 950, "duration_hours": 2},
    {"name": "Enchanted Amulet", "emoji": "🌠", "bonus": "+25% Luck", "price": 1650, "duration_hours": 2},
    {"name": "Lucky Star Amulet", "emoji": "👑", "bonus": "+35% Luck", "price": 2750, "duration_hours": 2},
]

PAWN_SPECIALS = [
    {"name": "Coming Soon", "emoji": "🪄", "description": "Mysterious rewards await..."},
    {"name": "Coming Soon", "emoji": "🪄", "description": "Mysterious rewards await..."},
    {"name": "Coming Soon", "emoji": "🪄", "description": "Mysterious rewards await..."},
    {"name": "Coming Soon", "emoji": "🪄", "description": "Mysterious rewards await..."},
]

# DROP TABLE SYSTEM
DROP_RATES = {
    "Common": 0.65,
    "Uncommon": 0.25,
    "Rare": 0.08,
    "Epic": 0.018,
    "Legendary": 0.002,
}

# EXCLUSIVE GACHA WEIGHTS
EXCLUSIVE_WEIGHTS = {
    "Toys": 0.40,
    "Dogs": 0.25,
    "Cats": 0.25,
    "Wings": 0.10,
}

def get_random_exclusive():
    """Randomly select an exclusive item based on category weights."""
    category = random.choices(
        list(EXCLUSIVE_WEIGHTS.keys()),
        weights=list(EXCLUSIVE_WEIGHTS.values())
    )[0]
    
    category_items = [item for item in EXCLUSIVE_ITEMS.values() if item["category"] == category]
    return random.choice(category_items) if category_items else None

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
