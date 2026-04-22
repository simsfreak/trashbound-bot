from datetime import datetime
import random

ZONES = {
    "fishing": {
        "name": "🎣 Fishing Zone",
        "unlock_level": 1,
        "description": "Fish the murky waters for aquatic treasures. Roll, catch, and discover what lurks beneath.",
        "banner": "🎣 ╔═ FISHING ZONE ═╗",
        "unicode_style": "⌊ wet / liquid / rewarding ⌋",
        "danger": "Low-Medium",
        "luck": "Splash zone good",
    },
    "botany": {
        "name": "🌿 Botany Zone",
        "unlock_level": 2,
        "description": "Gather rare plants and herbs from the overgrown district. Each flower tells a story.",
        "banner": "🌿 ╔═ BOTANY ZONE ═╗",
        "unicode_style": "✿ green / discovery / quality ✿",
        "danger": "Medium",
        "luck": "Nature's blessing",
    },
    "archaeology": {
        "name": "🏺 Archaeology Zone",
        "unlock_level": 3,
        "description": "Dig up ancient relics from forgotten burial grounds. History awaits the patient digger.",
        "banner": "🏺 ╔═ ARCHAEOLOGY ZONE ═╗",
        "unicode_style": "⚱ old / cursed / precious ⚱",
        "danger": "Medium-High",
        "luck": "Tomb whispers",
    },
    "scavenge": {
        "name": "♻️ Scavenge Zone",
        "unlock_level": 4,
        "description": "Sift through the junkyard for valuable trash. One person's garbage is your treasure.",
        "banner": "♻️ ╔═ SCAVENGE ZONE ═╗",
        "unicode_style": "⟲ abundant / chaotic / lucky ⟲",
        "danger": "Low",
        "luck": "Junk luck supreme",
    },
}

# ═══════════════════════════════════════════════════════════════════
# 300 ITEMS - COMPLETELY REWORKED (EMOJI ONLY, NO PNG IMAGES)
# ═══════════════════════════════════════════════════════════════════
ITEMS = {}

# COMMON ITEMS (60) - Basic trash everyone finds
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
    ("sticky_drink_pouch", "🧃 Sticky Drink Pouch", "2 coins", "Adhesive packaging."),
    ("damp_napkin_ball", "🧻 Damp Napkin Ball", "1 coin", "Crumpled moisture."),
    ("cracked_lotion_pump", "🧴 Cracked Lotion Pump", "2 coins", "Broken dispenser."),
    ("inside_out_sock", "🧦 Inside-Out Sock", "1 coin", "Textile reversal."),
    ("splinter_bundle", "🪵 Splinter Bundle", "2 coins", "Painful collection."),
    ("bent_safety_pin", "🧷 Bent Safety Pin", "1 coin", "Compromised security."),
    ("frosted_plastic_lid", "🧊 Frosted Plastic Lid", "1 coin", "Icy covering."),
    ("flattened_snack_box", "📦 Flattened Snack Box", "1 coin", "Compressed cardboard."),
    ("greasy_soap_chunk", "🧼 Greasy Soap Chunk", "2 coins", "Oily cleanser."),
    ("leaking_battery_shell", "🪫 Leaking Battery Shell", "1 coin", "Hazardous container."),
]

for item_id, name, coins_text, flavor in _common_items:
    ITEMS[item_id] = {
        "name": name,
        "rarity": "Common",
        "coins": int(coins_text.split()[0]),
        "xp": 1,
        "flavor": flavor,
        "zone_ids": ["fishing", "botany", "archaeology", "scavenge"],
    }

# UNCOMMON ITEMS (80) - Mid-tier finds
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
    ("soap_stack", "🧼 Soap Stack", "7 coins", "Multiple bars."),
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
    ("polished_coin_stack", "🪙 Polished Coin Stack", "18 coins", "Gleaming fortune."),
    ("ribbon_roll", "🎀 Ribbon Roll", "8 coins", "Decorative material."),
    ("bottle_collection", "🧴 Bottle Collection", "9 coins", "Plastic treasury."),
    ("feather_bundle", "🪶 Feather Bundle", "8 coins", "Fluffy mass."),
    ("magnet_collection", "🧲 Magnet Collection", "10 coins", "Attractive force."),
    ("puzzle_collection", "🧩 Puzzle Collection", "9 coins", "Many pieces."),
    ("plush_collection", "🧸 Plush Collection", "10 coins", "Soft squad."),
    ("sealed_mystery_drink", "🧃 Sealed Mystery Drink", "8 coins", "Unknown beverage."),
    ("half_clean_bottle", "🧴 Half-Clean Bottle", "6 coins", "Partially sanitized."),
    ("mismatched_sock_pair", "🧦 Mismatched Sock Pair", "7 coins", "Unlikely couple."),
    ("smooth_driftwood", "🪵 Smooth Driftwood Piece", "8 coins", "Wave-worn wood."),
    ("reinforced_clip", "🧷 Reinforced Clip", "7 coins", "Heavy-duty fastener."),
    ("clean_soap_bar", "🧼 Clean Soap Bar", "6 coins", "Unused luxury."),
    ("worn_coin_stack", "🪙 Worn Coin Stack", "10 coins", "Weathered fortune."),
    ("packed_supply_box", "📦 Packed Supply Box", "9 coins", "Full container."),
    ("strong_pull_magnet", "🧲 Strong Pull Magnet", "10 coins", "Powerful attraction."),
    ("cooling_gel_pack", "🧊 Cooling Gel Pack", "8 coins", "Temperature control."),
    ("repaired_plush_toy", "🧸 Repaired Plush Toy", "8 coins", "Restored companion."),
    ("linked_puzzle_set", "🧩 Linked Puzzle Set", "9 coins", "Connected pieces."),
    ("utility_gloves", "🧤 Utility Gloves", "8 coins", "Practical protection."),
    ("pressurized_canister", "🧃 Pressurized Canister", "7 coins", "Sealed pressure."),
    ("polished_feather", "🪶 Polished Feather", "6 coins", "Refined plume."),
]

for item_id, name, coins_text, flavor in _uncommon_items:
    ITEMS[item_id] = {
        "name": name,
        "rarity": "Uncommon",
        "coins": int(coins_text.split()[0]),
        "xp": 2,
        "flavor": flavor,
        "zone_ids": ["back_alley", "apartment_bins", "restaurant_dumpster"],
    }

# RARE ITEMS (80)
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
    ("echoing_coin", "🪙 Echoing Coin", "18 coins", "Resonant wealth."),
    ("alleywatch_charm", "🧿 Alleywatch Charm", "20 coins", "Guardian sphere."),
    ("tangle_fate_thread", "🧵 Tangle of Fate Thread", "19 coins", "Complex destiny."),
    ("glow_residue_bottle", "🧴 Glow Residue Bottle", "21 coins", "Luminous container."),
    ("murmur_feather", "🪶 Murmur Feather", "18 coins", "Whispering plume."),
    ("flicker_magnet_core", "🧲 Flicker Magnet Core", "20 coins", "Fluctuating pull."),
    ("hollow_eyed_plush", "🧸 Hollow-Eyed Plush", "17 coins", "Empty gaze toy."),
    ("missing_corner_piece", "🧩 Missing Corner Piece", "19 coins", "Incomplete fragment."),
    ("whisperbranch", "🪵 Whisperbranch", "21 coins", "Murmuring timber."),
    ("luckbound_pin", "🧷 Luckbound Pin", "20 coins", "Fortune fastener."),
    ("memory_foam_soap", "🧼 Memory Foam Soap", "19 coins", "Remembering cleanser."),
    ("fizzing_elixir_can", "🧃 Fizzing Elixir Can", "22 coins", "Bubbling magic."),
    ("twinflip_coin", "🪙 Twinflip Coin", "23 coins", "Double-sided wealth."),
    ("gutter_eye_bead", "🧿 Gutter Eye Bead", "21 coins", "Street-watching orb."),
    ("driftwing_feather", "🪶 Driftwing Feather", "20 coins", "Wandering plume."),
]

for item_id, name, coins_text, flavor in _rare_items:
    ITEMS[item_id] = {
        "name": name,
        "rarity": "Rare",
        "coins": int(coins_text.split()[0]),
        "xp": 5,
        "flavor": flavor,
        "zone_ids": ["restaurant_dumpster", "mall_rear_lot"],
    }

# EPIC ITEMS (50)
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
    ("voidblink_eye", "🧿 Voidblink Eye", "75 coins", "Blinking void orb."),
]

for item_id, name, coins_text, flavor in _epic_items:
    ITEMS[item_id] = {
        "name": name,
        "rarity": "Epic",
        "coins": int(coins_text.split()[0]),
        "xp": 10,
        "flavor": flavor,
        "zone_ids": ["scavenge"],
    }

# LEGENDARY ITEMS (36)
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
    ("liquid_infinity", "🧃 Liquid Infinity", "242 coins", "Boundless potion."),
    ("fate_anchor", "🧷 Fate Anchor", "230 coins", "Destiny's lock."),
    ("throne_of_scraps_frag", "👑 Throne of Scraps (Fragment)", "240 coins", "Regal discard piece."),
    ("core_of_endless_heap", "🌌 Core of the Endless Heap", "245 coins", "Infinite dump center."),
    ("prime_coin_of_fortune", "🪙 Prime Coin of Fortune", "250 coins", "Ultimate wealth."),
    ("watching_thing", "🧿 The Watching Thing", "255 coins", "Omniscient entity."),
    ("fortune_spiral_coin", "🪙 Fortune Spiral Coin", "80 coins", "Swirling wealth."),
    ("pulsecore_magnet", "🧲 Pulsecore Magnet", "78 coins", "Heartbeat attraction."),
    ("distilled_luck_vial", "🧴 Distilled Luck Vial", "82 coins", "Pure fortune."),
    ("skyfract_feather", "🪶 Skyfract Feather", "79 coins", "Sky-broken plume."),
    ("fragment_of_pattern", "🧩 Fragment of Pattern", "76 coins", "Design shard."),
]

for item_id, name, coins_text, flavor in _legendary_items:
    ITEMS[item_id] = {
        "name": name,
        "rarity": "Legendary",
        "coins": int(coins_text.split()[0]),
        "xp": 20,
        "flavor": flavor,
        "zone_ids": ["scavenge"],
    }

# ═══════════════════════════════════════════════════════════════════
# ZONE MISSION REWARDS (Unopened Boxes & Rewards)
# ═══════════════════════════════════════════════════════════════════

ZONE_REWARDS = {
    "dirty_tickets_50": {
        "name": "🎟️ Dirty Tickets x50",
        "type": "tickets",
        "emoji": "🎟️",
        "rarity": "Common",
        "kind": "reward",
    },
    "dirty_tickets_200": {
        "name": "🎟️ Dirty Tickets x200",
        "type": "tickets",
        "emoji": "🎟️",
        "rarity": "Rare",
        "kind": "reward",
    },
    "ticket_bundle_50": {
        "name": "🎟️ Ticket Bundle x50",
        "type": "tickets",
        "emoji": "🎟️",
        "rarity": "Common",
        "kind": "reward",
    },
    "ticket_bundle_200": {
        "name": "🎟️ Ticket Bundle x200",
        "type": "tickets",
        "emoji": "🎟️",
        "rarity": "Epic",
        "kind": "reward",
    },
    "azure_zone_box": {
        "name": "🎁 Azure Zone Box",
        "type": "zone_box",
        "emoji": "🎁",
        "rarity": "Rare",
        "kind": "reward",
        "xp_reward": 1000,
    },
    "crimson_zone_box": {
        "name": "🎁 Crimson Zone Box",
        "type": "zone_box",
        "emoji": "🎁",
        "rarity": "Epic",
        "kind": "reward",
        "xp_reward": 2000,
    },
    "golden_zone_box": {
        "name": "🎁 Golden Zone Box",
        "type": "zone_box",
        "emoji": "🎁",
        "rarity": "Epic",
        "kind": "reward",
        "xp_reward": 2000,
    },
    "heavy_coin_bag": {
        "name": "💰 Heavy Coin Bag",
        "type": "coin_bag",
        "emoji": "💰",
        "rarity": "Legendary",
        "kind": "reward",
        "coin_reward": 10000,
    },
}

# Add reward items to ITEMS dict
for reward_id, reward_data in ZONE_REWARDS.items():
    ITEMS[reward_id] = reward_data


# ═══════════════════════════════════════════════════════════════════
# MUSEUM RELIC SYSTEM - 50 RELICS IN 10 SETS
# ═══════════════════════════════════════════════════════════════════

RELICS = {
    # SET 1 — 🏙️ LOST CITY ARCHIVE
    "relic_echo_coin_fragment": {
        "name": "Echo Coin Fragment",
        "emoji": "🪙",
        "rarity": "common_relic",
        "set_id": "lost_city_archive",
        "set_name": "🏙️ Lost City Archive",
        "set_index": 1,
        "source_zones": ["archaeology", "scavenge"],
        "description": "A damaged coin that hums faintly when touched.",
    },
    "relic_royal_brick_shard": {
        "name": "Royal Brick Shard",
        "emoji": "🧱",
        "rarity": "common_relic",
        "set_id": "lost_city_archive",
        "set_name": "🏙️ Lost City Archive",
        "set_index": 2,
        "source_zones": ["archaeology"],
        "description": "A clay brick with faded gold leaf markings.",
    },
    "relic_cracked_royal_vase": {
        "name": "Cracked Royal Vase",
        "emoji": "🏺",
        "rarity": "rare_relic",
        "set_id": "lost_city_archive",
        "set_name": "🏙️ Lost City Archive",
        "set_index": 3,
        "source_zones": ["archaeology"],
        "description": "A ceremonial vase with three vertical cracks, still holding water.",
    },
    "relic_forgotten_idol_head": {
        "name": "Forgotten Idol Head",
        "emoji": "🗿",
        "rarity": "exotic_relic",
        "set_id": "lost_city_archive",
        "set_name": "🏙️ Lost City Archive",
        "set_index": 4,
        "source_zones": ["archaeology"],
        "description": "A stone face worn smooth by time, but the eyes remain sharply carved, as if still watching.",
    },
    "relic_burned_decree_scroll": {
        "name": "Burned Decree Scroll",
        "emoji": "📜",
        "rarity": "ancient_relic",
        "set_id": "lost_city_archive",
        "set_name": "🏙️ Lost City Archive",
        "set_index": 5,
        "source_zones": ["archaeology"],
        "description": "Partially burned parchment with unreadable text, edges charred to ash.",
    },

    # SET 2 — 🌊 SUNKEN DEPTHS COLLECTION
    "relic_barnacle_anchor_charm": {
        "name": "Barnacle Anchor Charm",
        "emoji": "⚓",
        "rarity": "common_relic",
        "set_id": "sunken_depths",
        "set_name": "🌊 Sunken Depths",
        "set_index": 6,
        "source_zones": ["fishing", "scavenge"],
        "description": "A tiny anchor crusted with old barnacles, somehow still magnetizing.",
    },
    "relic_drowned_sailor_shell": {
        "name": "Drowned Sailor Shell",
        "emoji": "🐚",
        "rarity": "rare_relic",
        "set_id": "sunken_depths",
        "set_name": "🌊 Sunken Depths",
        "set_index": 7,
        "source_zones": ["fishing"],
        "description": "A conch that echoes with distant whale song when held to ear.",
    },
    "relic_tideglass_orb": {
        "name": "Tideglass Orb",
        "emoji": "🫧",
        "rarity": "rare_relic",
        "set_id": "sunken_depths",
        "set_name": "🌊 Sunken Depths",
        "set_index": 8,
        "source_zones": ["fishing"],
        "description": "A sphere of sea-glass containing a single bubble that never pops.",
    },
    "relic_crystal_tide_scale": {
        "name": "Crystal Tide Scale",
        "emoji": "🐟",
        "rarity": "exotic_relic",
        "set_id": "sunken_depths",
        "set_name": "🌊 Sunken Depths",
        "set_index": 9,
        "source_zones": ["fishing"],
        "description": "A fish scale that refracts light into colors that don't exist in nature.",
    },
    "relic_abyss_bell_core": {
        "name": "Abyss Bell Core",
        "emoji": "🌊",
        "rarity": "ancient_relic",
        "set_id": "sunken_depths",
        "set_name": "🌊 Sunken Depths",
        "set_index": 10,
        "source_zones": ["fishing"],
        "description": "The rusted bronze core of a massive bell, cold despite warm weather.",
    },

    # SET 3 — 🌿 OVERGROWTH HERBARIUM
    "relic_alley_moss_seal": {
        "name": "Alley Moss Seal",
        "emoji": "🌱",
        "rarity": "common_relic",
        "set_id": "overgrowth_herbarium",
        "set_name": "🌿 Overgrowth Herbarium",
        "set_index": 11,
        "source_zones": ["botany"],
        "description": "Moss shaped exactly like a official seal, soft as velvet.",
    },
    "relic_whisper_leaf_vein": {
        "name": "Whisper Leaf Vein",
        "emoji": "🍃",
        "rarity": "rare_relic",
        "set_id": "overgrowth_herbarium",
        "set_name": "🌿 Overgrowth Herbarium",
        "set_index": 12,
        "source_zones": ["botany"],
        "description": "A pressed leaf with veins that glow faintly in darkness.",
    },
    "relic_glow_petal_core": {
        "name": "Glow Petal Core",
        "emoji": "🌸",
        "rarity": "rare_relic",
        "set_id": "overgrowth_herbarium",
        "set_name": "🌿 Overgrowth Herbarium",
        "set_index": 13,
        "source_zones": ["botany"],
        "description": "A flower petal that emits bioluminescence when squeezed.",
    },
    "relic_pulsecap_heart": {
        "name": "Pulsecap Heart",
        "emoji": "🍄",
        "rarity": "exotic_relic",
        "set_id": "overgrowth_herbarium",
        "set_name": "🌿 Overgrowth Herbarium",
        "set_index": 14,
        "source_zones": ["botany"],
        "description": "A mushroom cap that pulses like a beating heart.",
    },
    "relic_thornlight_seed_crown": {
        "name": "Thornlight Seed Crown",
        "emoji": "🌹",
        "rarity": "ancient_relic",
        "set_id": "overgrowth_herbarium",
        "set_name": "🌿 Overgrowth Herbarium",
        "set_index": 15,
        "source_zones": ["botany"],
        "description": "Thorned seeds arranged in a perfect spiral, radiating soft light.",
    },

    # SET 4 — ⚙️ INDUSTRIAL REMNANTS
    "relic_factory_bolt_mark_i": {
        "name": "Factory Bolt Mark I",
        "emoji": "🔩",
        "rarity": "common_relic",
        "set_id": "industrial_remnants",
        "set_name": "⚙️ Industrial Remnants",
        "set_index": 16,
        "source_zones": ["scavenge"],
        "description": "A factory bolt stamped with manufacturing date from an era no records contain.",
    },
    "relic_copper_fuse_spine": {
        "name": "Copper Fuse Spine",
        "emoji": "🔌",
        "rarity": "common_relic",
        "set_id": "industrial_remnants",
        "set_name": "⚙️ Industrial Remnants",
        "set_index": 17,
        "source_zones": ["scavenge"],
        "description": "A copper spine from a circuit board, still slightly warm.",
    },
    "relic_machine_prayer_cog": {
        "name": "Machine Prayer Cog",
        "emoji": "⚙️",
        "rarity": "rare_relic",
        "set_id": "industrial_remnants",
        "set_name": "⚙️ Industrial Remnants",
        "set_index": 18,
        "source_zones": ["scavenge"],
        "description": "A gear with sacred symbols carved into its teeth.",
    },
    "relic_core_battery_relic": {
        "name": "Core Battery Relic",
        "emoji": "🔋",
        "rarity": "exotic_relic",
        "set_id": "industrial_remnants",
        "set_name": "⚙️ Industrial Remnants",
        "set_index": 19,
        "source_zones": ["scavenge"],
        "description": "A battery that maintains constant charge despite being corroded.",
    },
    "relic_foremans_command_tool": {
        "name": "Foreman's Command Tool",
        "emoji": "🛠️",
        "rarity": "ancient_relic",
        "set_id": "industrial_remnants",
        "set_name": "⚙️ Industrial Remnants",
        "set_index": 20,
        "source_zones": ["scavenge"],
        "description": "A wrench engraved with names of workers long forgotten.",
    },

    # SET 5 — 🧸 CHILDHOOD REMAINS
    "relic_button_eye_plush_core": {
        "name": "Button Eye Plush Core",
        "emoji": "🧸",
        "rarity": "common_relic",
        "set_id": "childhood_remains",
        "set_name": "🧸 Childhood Remains",
        "set_index": 21,
        "source_zones": ["scavenge"],
        "description": "Stuffing from a toy, still holding the scent of old fabric.",
    },
    "relic_pocket_carousel_horse": {
        "name": "Pocket Carousel Horse",
        "emoji": "🎠",
        "rarity": "rare_relic",
        "set_id": "childhood_remains",
        "set_name": "🧸 Childhood Remains",
        "set_index": 22,
        "source_zones": ["scavenge"],
        "description": "A tiny wooden horse that still spins when wound.",
    },
    "relic_ribbon_bear_heart": {
        "name": "Ribbon Bear Heart",
        "emoji": "🎀",
        "rarity": "rare_relic",
        "set_id": "childhood_remains",
        "set_name": "🧸 Childhood Remains",
        "set_index": 23,
        "source_zones": ["scavenge"],
        "description": "A silk ribbon folded into the shape of a heart, wrapped in threads.",
    },
    "relic_hollow_doll_vessel": {
        "name": "Hollow Doll Vessel",
        "emoji": "🪆",
        "rarity": "exotic_relic",
        "set_id": "childhood_remains",
        "set_name": "🧸 Childhood Remains",
        "set_index": 24,
        "source_zones": ["scavenge"],
        "description": "A porcelain doll torso that echoes when you whisper into it.",
    },
    "relic_lullaby_music_cylinder": {
        "name": "Lullaby Music Cylinder",
        "emoji": "🍼",
        "rarity": "ancient_relic",
        "set_id": "childhood_remains",
        "set_name": "🧸 Childhood Remains",
        "set_index": 25,
        "source_zones": ["scavenge"],
        "description": "A music box cylinder that plays a melody no record contains.",
    },

    # SET 6 — 🛐 SHRINE OF SMALL THINGS
    "relic_wax_prayer_stub": {
        "name": "Wax Prayer Stub",
        "emoji": "🕯️",
        "rarity": "common_relic",
        "set_id": "shrine_of_small_things",
        "set_name": "🛐 Shrine of Small Things",
        "set_index": 26,
        "source_zones": ["scavenge"],
        "description": "A candle stub melted into a prayer shape.",
    },
    "relic_rust_bead_rosary": {
        "name": "Rust Bead Rosary",
        "emoji": "📿",
        "rarity": "rare_relic",
        "set_id": "shrine_of_small_things",
        "set_name": "🛐 Shrine of Small Things",
        "set_index": 27,
        "source_zones": ["scavenge"],
        "description": "Beads strung on rusted wire, each with a name scratched in.",
    },
    "relic_alley_eye_charm": {
        "name": "Alley Eye Charm",
        "emoji": "🧿",
        "rarity": "rare_relic",
        "set_id": "shrine_of_small_things",
        "set_name": "🛐 Shrine of Small Things",
        "set_index": 28,
        "source_zones": ["scavenge"],
        "description": "A protective amulet shaped like an eye that blinks in your pocket.",
    },
    "relic_halo_nail_fragment": {
        "name": "Halo Nail Fragment",
        "emoji": "⛪",
        "rarity": "exotic_relic",
        "set_id": "shrine_of_small_things",
        "set_name": "🛐 Shrine of Small Things",
        "set_index": 29,
        "source_zones": ["scavenge"],
        "description": "A nail from a shrine's halo decoration, surrounded by a faint glow.",
    },
    "relic_cracked_saint_halo": {
        "name": "Cracked Saint Halo",
        "emoji": "😇",
        "rarity": "ancient_relic",
        "set_id": "shrine_of_small_things",
        "set_name": "🛐 Shrine of Small Things",
        "set_index": 30,
        "source_zones": ["scavenge"],
        "description": "A broken halo from a saint statue, radiating old faith.",
    },

    # SET 7 — 🚇 BELOW THE STREETS
    "relic_tunnel_token": {
        "name": "Tunnel Token",
        "emoji": "🚇",
        "rarity": "common_relic",
        "set_id": "below_the_streets",
        "set_name": "🚇 Below the Streets",
        "set_index": 31,
        "source_zones": ["scavenge"],
        "description": "A transit token from a system that no longer exists on any map.",
    },
    "relic_emergency_lamp_cap": {
        "name": "Emergency Lamp Cap",
        "emoji": "🧯",
        "rarity": "common_relic",
        "set_id": "below_the_streets",
        "set_name": "🚇 Below the Streets",
        "set_index": 32,
        "source_zones": ["scavenge"],
        "description": "The glass cap of an emergency lamp, still glowing faintly.",
    },
    "relic_gutter_gate_key": {
        "name": "Gutter Gate Key",
        "emoji": "🗝️",
        "rarity": "rare_relic",
        "set_id": "below_the_streets",
        "set_name": "🚇 Below the Streets",
        "set_index": 33,
        "source_zones": ["scavenge"],
        "description": "A key to a gate below the city streets, warm to the touch.",
    },
    "relic_transit_warning_plate": {
        "name": "Transit Warning Plate",
        "emoji": "🪤",
        "rarity": "exotic_relic",
        "set_id": "below_the_streets",
        "set_name": "🚇 Below the Streets",
        "set_index": 34,
        "source_zones": ["scavenge"],
        "description": "A warning sign from a transit system, written in no known language.",
    },
    "relic_last_station_seal": {
        "name": "Last Station Seal",
        "emoji": "🚪",
        "rarity": "ancient_relic",
        "set_id": "below_the_streets",
        "set_name": "🚇 Below the Streets",
        "set_index": 35,
        "source_zones": ["scavenge"],
        "description": "A seal from the final platform of a subway that descended too far.",
    },

    # SET 8 — 🌙 NIGHT MARKET ECHOES
    "relic_lantern_trade_token": {
        "name": "Lantern Trade Token",
        "emoji": "🪙",
        "rarity": "common_relic",
        "set_id": "night_market_echoes",
        "set_name": "🌙 Night Market Echoes",
        "set_index": 36,
        "source_zones": ["scavenge"],
        "description": "A trading token from a market that only opened after dark.",
    },
    "relic_perfume_glass_shard": {
        "name": "Perfume Glass Shard",
        "emoji": "🧴",
        "rarity": "rare_relic",
        "set_id": "night_market_echoes",
        "set_name": "🌙 Night Market Echoes",
        "set_index": 37,
        "source_zones": ["scavenge"],
        "description": "Broken glass from a perfume bottle, still carrying exotic scent.",
    },
    "relic_velvet_stall_tag": {
        "name": "Velvet Stall Tag",
        "emoji": "🪭",
        "rarity": "rare_relic",
        "set_id": "night_market_echoes",
        "set_name": "🌙 Night Market Echoes",
        "set_index": 38,
        "source_zones": ["scavenge"],
        "description": "A stall marker embroidered with forgotten sigils.",
    },
    "relic_moon_vendor_mask_piece": {
        "name": "Moon Vendor Mask Piece",
        "emoji": "🎭",
        "rarity": "exotic_relic",
        "set_id": "night_market_echoes",
        "set_name": "🌙 Night Market Echoes",
        "set_index": 39,
        "source_zones": ["scavenge"],
        "description": "A fragment of a vendor's mask, worn for transactions made in shadow.",
    },
    "relic_market_moon_sigil": {
        "name": "Market Moon Sigil",
        "emoji": "🌙",
        "rarity": "ancient_relic",
        "set_id": "night_market_echoes",
        "set_name": "🌙 Night Market Echoes",
        "set_index": 40,
        "source_zones": ["scavenge"],
        "description": "A seal proving transaction in the night market, still binding.",
    },

    # SET 9 — 🐟 BEASTS OF THE BROKEN WATERS
    "relic_rustfang_tooth": {
        "name": "Rustfang Tooth",
        "emoji": "🦷",
        "rarity": "rare_relic",
        "set_id": "beasts_of_broken_waters",
        "set_name": "🐟 Beasts of Broken Waters",
        "set_index": 41,
        "source_zones": ["fishing"],
        "description": "A tooth from a creature that adapted to broken waters, still sharp.",
    },
    "relic_puffer_spine_core": {
        "name": "Puffer Spine Core",
        "emoji": "🐡",
        "rarity": "rare_relic",
        "set_id": "beasts_of_broken_waters",
        "set_name": "🐟 Beasts of Broken Waters",
        "set_index": 42,
        "source_zones": ["fishing"],
        "description": "A spine from a mutated puffer fish, hardened to crystal.",
    },
    "relic_prismfin_scale": {
        "name": "Prismfin Scale",
        "emoji": "🐠",
        "rarity": "exotic_relic",
        "set_id": "beasts_of_broken_waters",
        "set_name": "🐟 Beasts of Broken Waters",
        "set_index": 43,
        "source_zones": ["fishing"],
        "description": "A scale that refracts reality itself.",
    },
    "relic_scrapjaw_crest_plate": {
        "name": "Scrapjaw Crest Plate",
        "emoji": "🦈",
        "rarity": "ancient_relic",
        "set_id": "beasts_of_broken_waters",
        "set_name": "🐟 Beasts of Broken Waters",
        "set_index": 44,
        "source_zones": ["fishing"],
        "description": "A crest plate from a creature made of metal and flesh.",
    },
    "relic_leviathan_eye_pearl": {
        "name": "Leviathan Eye Pearl",
        "emoji": "👁️",
        "rarity": "forbidden_relic",
        "set_id": "beasts_of_broken_waters",
        "set_name": "🐟 Beasts of Broken Waters",
        "set_index": 45,
        "source_zones": ["fishing"],
        "description": "An eye from something vast and unknowable, now pearlified.",
    },

    # SET 10 — 🩸 THE ERASED TRUTH
    "relic_watchers_iris": {
        "name": "Watcher's Iris",
        "emoji": "🧿",
        "rarity": "exotic_relic",
        "set_id": "erased_truth",
        "set_name": "🩸 The Erased Truth",
        "set_index": 46,
        "source_zones": ["archaeology", "scavenge"],
        "description": "An iris that sees things that should not be seen.",
    },
    "relic_glitch_memory_strip": {
        "name": "Glitch Memory Strip",
        "emoji": "📼",
        "rarity": "exotic_relic",
        "set_id": "erased_truth",
        "set_name": "🩸 The Erased Truth",
        "set_index": 47,
        "source_zones": ["scavenge"],
        "description": "A data strip that glitches with half-remembered moments.",
    },
    "relic_reflection_that_isnt_yours": {
        "name": "Reflection That Isn't Yours",
        "emoji": "🪞",
        "rarity": "ancient_relic",
        "set_id": "erased_truth",
        "set_name": "🩸 The Erased Truth",
        "set_index": 48,
        "source_zones": ["scavenge"],
        "description": "A mirror shard showing a person who isn't you.",
    },
    "relic_null_origin_shard": {
        "name": "Null Origin Shard",
        "emoji": "🕳️",
        "rarity": "ancient_relic",
        "set_id": "erased_truth",
        "set_name": "🩸 The Erased Truth",
        "set_index": 49,
        "source_zones": ["archaeology"],
        "description": "A fragment of nothing, absence given form.",
    },
    "relic_the_first_object": {
        "name": "The First Object",
        "emoji": "👁️‍🗨️",
        "rarity": "forbidden_relic",
        "set_id": "erased_truth",
        "set_name": "🩸 The Erased Truth",
        "set_index": 50,
        "source_zones": ["archaeology"],
        "description": "The wound around which the world shattered.",
    },
}

# Museum Sets with lore and rewards
MUSEUM_SETS = {
    "lost_city_archive": {
        "name": "🏙️ Lost City Archive",
        "emoji": "🏙️",
        "set_number": 1,
        "lore": "A city once ruled by order, wealth, and ceremony vanished without collapse, as if memory itself had been cut away.",
        "rewards": {
            "tickets": 100,
            "museum_box": "museum_box_i",
            "story_fragment": True,
        },
    },
    "sunken_depths": {
        "name": "🌊 Sunken Depths",
        "emoji": "🌊",
        "set_number": 2,
        "lore": "These relics come from beneath black water where something old still moves beneath the tide.",
        "rewards": {
            "tickets": 120,
            "title": "Sunken Curio",
            "story_fragment": True,
        },
    },
    "overgrowth_herbarium": {
        "name": "🌿 Overgrowth Herbarium",
        "emoji": "🌿",
        "set_number": 3,
        "lore": "Plants in Broken Reality do not merely grow. Some remember. Some watch. Some bloom around forgotten grief.",
        "rewards": {
            "museum_box": "botanical_cache",
            "bonus": "+3% Loot Luck",
            "story_fragment": True,
        },
    },
    "industrial_remnants": {
        "name": "⚙️ Industrial Remnants",
        "emoji": "⚙️",
        "set_number": 4,
        "lore": "A machine district once ran day and night until the workers vanished and the engines began speaking only in sparks.",
        "rewards": {
            "coins": 10000,
            "title": "Rustwright",
            "story_fragment": True,
        },
    },
    "childhood_remains": {
        "name": "🧸 Childhood Remains",
        "emoji": "🧸",
        "set_number": 5,
        "lore": "These relics are soaked in innocence and loss. Something terrible happened quietly here.",
        "rewards": {
            "exclusive": "museum_plush",
            "tickets": 150,
            "story_fragment": True,
        },
    },
    "shrine_of_small_things": {
        "name": "🛐 Shrine of Small Things",
        "emoji": "🛐",
        "set_number": 6,
        "lore": "People prayed over broken things here. Maybe because broken things were all they had left.",
        "rewards": {
            "bonus": "+5% Relic Drop Chance",
            "title": "Curator's Blessing",
            "story_fragment": True,
        },
    },
    "below_the_streets": {
        "name": "🚇 Below the Streets",
        "emoji": "🚇",
        "set_number": 7,
        "lore": "Below the city is another city, and beneath that another. Some doors were never meant to be reopened.",
        "rewards": {
            "museum_box": "museum_box_ii",
            "title": "Deep Diver",
            "story_fragment": True,
        },
    },
    "night_market_echoes": {
        "name": "🌙 Night Market Echoes",
        "emoji": "🌙",
        "set_number": 8,
        "lore": "A market opened only at night, and only for those who had already lost something they could never replace.",
        "rewards": {
            "coins": 15000,
            "title": "Night Merchant",
            "story_fragment": True,
        },
    },
    "beasts_of_broken_waters": {
        "name": "🐟 Beasts of Broken Waters",
        "emoji": "🐟",
        "set_number": 9,
        "lore": "Some creatures adapted. Some transformed. Some were never natural to begin with.",
        "rewards": {
            "exclusive": "tidefin_wings",
            "tickets": 250,
            "story_fragment": True,
        },
    },
    "erased_truth": {
        "name": "🩸 The Erased Truth",
        "emoji": "🩸",
        "set_number": 10,
        "lore": "These relics do not belong to the world as it is. They belong to the event that broke it.",
        "rewards": {
            "title": "Witness of the Break",
            "museum_box": "museum_box_iii",
            "story_fragment": True,
        },
    },
}

# Relic drop rate biases by zone
RELIC_DROP_BIASES = {
    "base": {
        "common_relic": 0.52,
        "rare_relic": 0.26,
        "exotic_relic": 0.13,
        "ancient_relic": 0.07,
        "forbidden_relic": 0.02,
    },
    "scavenge": {
        "common_relic": 0.60,  # +8%
        "rare_relic": 0.29,    # +3%
        "exotic_relic": 0.09,  # -4%
        "ancient_relic": 0.03, # -4%
        "forbidden_relic": -0.01,  # -3% (clamped to 0)
    },
    "archaeology": {
        "common_relic": 0.44,  # -8%
        "rare_relic": 0.30,    # +4%
        "exotic_relic": 0.17,  # +4%
        "ancient_relic": 0.10, # +3%
        "forbidden_relic": -0.01,  # -3% (clamped to 0)
    },
    "botany": {
        "common_relic": 0.49,  # -3%
        "rare_relic": 0.29,    # +3%
        "exotic_relic": 0.18,  # +5%
        "ancient_relic": 0.05, # -2%
        "forbidden_relic": -0.01,  # -3% (clamped to 0)
    },
    "fishing": {
        "common_relic": 0.48,  # -4%
        "rare_relic": 0.28,    # +2%
        "exotic_relic": 0.17,  # +4%
        "ancient_relic": 0.08, # +1%
        "forbidden_relic": -0.01,  # -3% (clamped to 0)
    },
    "deep_mission": {
        "common_relic": 0.40,  # -12%
        "rare_relic": 0.22,    # -4%
        "exotic_relic": 0.19,  # +6%
        "ancient_relic": 0.13, # +6%
        "forbidden_relic": 0.06,  # +4%
    },
}

# Museum story chapters
MUSEUM_STORY_CHAPTERS = [
    {
        "chapter": 1,
        "title": "The Vanishing City",
        "set_id": "lost_city_archive",
        "text": "The city did not collapse.\nThere were no ruins at first.\nNo fire. No flood. No war.\n\nPeople simply began forgetting.\n\nStreets emptied.\nDoors stayed open.\nShops remained stocked.\nThe city remained... but the memory of it did not.",
    },
    {
        "chapter": 2,
        "title": "The Bell Beneath",
        "set_id": "sunken_depths",
        "text": "When the first district disappeared from memory, the waters changed.\n\nFishermen reported hearing bells from below the surface.\nSome followed the sound.\nNone returned unchanged.\n\nThe sea kept what the city had lost.",
    },
    {
        "chapter": 3,
        "title": "The Garden That Listened",
        "set_id": "overgrowth_herbarium",
        "text": "After the forgetting began, plants spread into walls, alleys, train lines, and homes.\n\nSome flowers bloomed only where people had cried.\nSome roots wrapped around objects no one remembered owning.\n\nThe world was growing over its own missing pieces.",
    },
    {
        "chapter": 4,
        "title": "The Last Shift",
        "set_id": "industrial_remnants",
        "text": "Factories kept running long after the workers vanished.\n\nMachines stamped, sparked, and assembled products for owners who no longer existed.\n\nSome say the engines learned the rhythms of human hands,\nand continued out of grief.",
    },
    {
        "chapter": 5,
        "title": "The Silent Nursery",
        "set_id": "childhood_remains",
        "text": "The children were gone before anyone realized they had been there.\n\nTheir rooms remained.\nTheir toys remained.\nSongs remained inside cracked music cylinders.\n\nThe Museum found the first real proof in a doll that whispered a name no record contained.",
    },
    {
        "chapter": 6,
        "title": "What They Worshipped",
        "set_id": "shrine_of_small_things",
        "text": "Shrines appeared in alleyways and broken rooms.\n\nNo god names were written.\nOnly circles.\nEyes.\nHands.\nAnd little offerings left beside shattered everyday things.\n\nPeople had begun praying to survival itself.",
    },
    {
        "chapter": 7,
        "title": "The Last Platform",
        "set_id": "below_the_streets",
        "text": "The transit tunnels below the city should have ended.\nInstead, they deepened.\n\nTracks continued into darkness beyond any map.\nDoors opened onto stations with no district above them.\n\nSomeone had built for a future that never arrived.",
    },
    {
        "chapter": 8,
        "title": "The Price of Wanting",
        "set_id": "night_market_echoes",
        "text": "At the night market, objects were traded for memories.\n\nA ring for a childhood.\nA lantern for a first love.\nA coat for the sound of your mother's voice.\n\nThose who bargained left smiling...\nuntil they realized what was missing.",
    },
    {
        "chapter": 9,
        "title": "What Swims Below",
        "set_id": "beasts_of_broken_waters",
        "text": "The broken waters are alive with adaptation.\n\nFish with glass bones.\nSharks with iron jaws.\nEyes that reflect things not present.\n\nThe sea did not merely mutate.\nIt was fed.",
    },
    {
        "chapter": 10,
        "title": "The Fracture",
        "set_id": "erased_truth",
        "text": "The Museum's oldest records agree on only one thing:\n\nThe world broke around a single object.\n\nNo one remembers who found it first.\nNo one remembers what it truly was.\nOnly that after it appeared, memory began to peel away from reality.\n\nThe relic known only as The First Object is not a remnant.\n\nIt is the wound.",
    },
]

# Rarity display settings for relics
RELIC_RARITY_INFO = {
    "common_relic": {
        "name": "Common Relic",
        "emoji": "⚪",
        "color": 0x808080,
        "description": "Low-tier historical junk with weak echoes",
    },
    "rare_relic": {
        "name": "Rare Relic",
        "emoji": "🔵",
        "color": 0x0000FF,
        "description": "Meaningful objects with stronger identity",
    },
    "exotic_relic": {
        "name": "Exotic Relic",
        "emoji": "🟣",
        "color": 0x800080,
        "description": "Strange items tied to mystery zones",
    },
    "ancient_relic": {
        "name": "Ancient Relic",
        "emoji": "🟠",
        "color": 0xFF8C00,
        "description": "Old world artifacts with strong lore",
    },
    "forbidden_relic": {
        "name": "Forbidden Relic",
        "emoji": "🔴",
        "color": 0xFF0000,
        "description": "Corrupted, dangerous, hidden truth items",
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

# ═══════════════════════════════════════════════════════════════════
# EXCLUSIVE COLLECTIBLES (36 ITEMS, 4 CATEGORIES)
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

MUSEUM_COLLECTIONS = {
    "basic_treasures": {
        "name": "Basic Treasures",
        "emoji": "🧩",
        "description": "The humble scraps that started every great alley career.",
        "item_ids": [
            "crushed_soda_can",
            "damp_newspaper",
            "lost_sock",
            "moldy_bread",
            "bent_toothbrush",
            "torn_cardboard",
            "empty_shampoo",
            "tissue_bundle",
        ],
    },
    "uncommon_finds": {
        "name": "Uncommon Finds",
        "emoji": "⭐",
        "description": "Decent discoveries from the mid-tier locations.",
        "item_ids": [
            "polished_coin",
            "half_full_bottle",
            "patched_plush",
            "reinforced_box",
            "steel_clip",
            "sealed_juice_pack",
            "metal_spoon",
            "playable_cd",
        ],
    },
    "rare_relics": {
        "name": "Rare Relics",
        "emoji": "🌟",
        "description": "Weird lucky finds with celestial significance.",
        "item_ids": [
            "ratfang_token",
            "velvet_rust_ribbon",
            "mooncap_charm",
            "gilded_drain_key",
            "cracked_halo_shard",
            "saints_soda_tab",
            "mothglass_pendant",
            "music_box_tooth",
        ],
    },
    "epic_artifacts": {
        "name": "Epic Artifacts",
        "emoji": "👑",
        "description": "Beautiful junk relics of legendary magnitude.",
        "item_ids": [
            "rustbound_crown_frag",
            "voidglass_shard",
            "embercore_bottle",
            "all_seeing_bead",
            "kings_lost_coin",
            "fateweaver_thread",
            "celestial_feather",
            "core_singularity_magnet",
        ],
    },
    "legendary_treasures": {
        "name": "Legendary Treasures",
        "emoji": "💎",
        "description": "Myth-level garbage miracles of absolute power.",
        "item_ids": [
            "crown_of_dump_king",
            "heart_of_void_pile",
            "eternal_ember_relic",
            "fallen_halo_core",
            "infinite_coin_bloom",
            "eye_of_lost_things",
            "wing_of_forgotten",
            "gravity_well_core",
        ],
    },
}

MUSEUM_ARTIFACT_TEXT = {
    "crushed_soda_can": {
        "origin": "Usually recovered from beginner dives in the Back Alley.",
        "museum_text": "A discarded classic. Every scrapper remembers their first one.",
    },
    "polished_coin": {
        "origin": "Commonly pulled from alleys and apartment bins.",
        "museum_text": "The backbone of the junk economy.",
    },
    "ratfang_token": {
        "origin": "Recovered from household piles and unstable mixes.",
        "museum_text": "Proof of alley citizenship and rat respect.",
    },
}

# ═══════════════════════════════════════════════════════════════════
# DROP TABLE SYSTEM
# ═══════════════════════════════════════════════════════════════════
DROP_RATES = {
    "Common": 0.65,
    "Uncommon": 0.25,
    "Rare": 0.08,
    "Epic": 0.018,
    "Legendary": 0.002,
}

# ═══════════════════════════════════════════════════════════════════
# EXCLUSIVE GACHA WEIGHTS
# ═══════════════════════════════════════════════════════════════════
EXCLUSIVE_WEIGHTS = {
    "Toys": 0.40,
    "Dogs": 0.25,
    "Cats": 0.25,
    "Wings": 0.10,
}

# ═══════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════
def get_random_exclusive():
    """Randomly select an exclusive item based on category weights."""
    category = random.choices(
        list(EXCLUSIVE_WEIGHTS.keys()),
        weights=list(EXCLUSIVE_WEIGHTS.values())
    )[0]
    
    category_items = [item for item in EXCLUSIVE_ITEMS.values() if item["category"] == category]
    return random.choice(category_items) if category_items else None

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

# ═══════════════════════════════════════════════════════════════════
# THE TAVERN - FOOD & DRINKS MENU
# ═══════════════════════════════════════════════════════════════════
TAVERN_FOOD = [
    {"id": "strawberry_milk", "name": "🍓 Strawberry Milk", "hunger_restored": 25, "price": 120, "emoji": "🍓"},
    {"id": "brown_sugar_boba", "name": "🧋 Brown Sugar Boba", "hunger_restored": 50, "price": 260, "emoji": "🧋"},
    {"id": "berry_smoothie", "name": "🫐 Berry Smoothie", "hunger_restored": 75, "price": 390, "emoji": "🫐"},
    {"id": "bbq_rib_plate", "name": "🍖 BBQ Rib Plate", "hunger_restored": 100, "price": 700, "emoji": "🍖"},
    {"id": "berry_ice_cream", "name": "🍨 Berry Ice Cream", "hunger_restored": 100, "price": 680, "emoji": "🍨"},
]
