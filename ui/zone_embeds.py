# ═══════════════════════════════════════════════════════════════════
# ZONE ACTIVITY SYSTEM - EMBED BUILDERS
# ═══════════════════════════════════════════════════════════════════
# Embeds for zone selector, main page, active missions, results, and completion.

import discord
from datetime import datetime
from game.zones import ZONES_META
from game.data import ITEMS


RARITY_COLORS = {
    "Common": 0x95A5A6,
    "Rare": 0x3498DB,
    "Exotic": 0x9B59B6,
    "Dangerous": 0xE74C3C,
}

ZONE_EMOJIS = {
    "fishing": "🎣",
    "botany": "🌿",
    "archaeology": "🏺",
    "scavenge": "♻️",
}


def zone_selector_embed(player_level: int) -> discord.Embed:
    """Show all 4 zones with their status and unlock info."""
    embed = discord.Embed(
        title="🗺️ ZONE SELECTOR 🗺️",
        description="Choose a zone to farm items, complete missions, and gather resources.",
        color=0x2C3E50,
    )
    
    embed.add_field(
        name="💡 Tips",
        value="Zones unlock as you level up. Harder zones have better rewards!",
        inline=False,
    )
    
    for zone_id, zone_meta in ZONES_META.items():
        unlock_level = zone_meta["unlock_level"]
        is_unlocked = player_level >= unlock_level
        
        status = f"✅ UNLOCKED" if is_unlocked else f"🔒 LEVEL {unlock_level}"
        emoji = zone_meta["emoji"]
        name = zone_meta["name"]
        description = zone_meta["description"]
        
        embed.add_field(
            name=f"{emoji} {name}",
            value=f"{description}\n**Status:** {status}",
            inline=False,
        )
    
    embed.set_footer(text="Click zone button below to enter or get info")
    return embed


def zone_info_embed(zone_id: str, player_level: int) -> discord.Embed:
    """Zone main page: current time, status, danger level, luck, cooldown, mission targets."""
    zone = ZONES_META.get(zone_id)
    if not zone:
        return discord.Embed(title="❌ Zone Not Found", color=0xFF0000)
    
    # Get current time (player's local)
    now = datetime.now()
    current_time = now.strftime("%I:%M %p")
    
    # Danger level (placeholder - would be calculated from mission data)
    danger_levels = ["Low", "Medium", "High"]
    danger_level = danger_levels[(player_level - zone["unlock_level"]) % 3]
    
    # Luck factor: (player_level - 1) / 4, capped at 25%
    luck_factor = min(25, max(0, int((player_level - 1) / 4)))
    
    # Action cooldown
    cooldown = zone.get("cooldown", 20)
    
    # Build title with zone emoji
    emoji = zone.get("emoji", "✨")
    title = f"{emoji} {zone['name']}"
    
    embed = discord.Embed(
        title=title,
        description=zone.get("description", ""),
        color=0x34495E,
    )
    
    # Zone Info Section
    embed.add_field(
        name="⏰ CURRENT TIME",
        value=current_time,
        inline=True,
    )
    
    embed.add_field(
        name="📍 STATUS",
        value="Open ✅",  # Would be dynamic based on time windows
        inline=True,
    )
    
    embed.add_field(
        name="⏳ NEXT OPENING",
        value="~ 2 Hours",  # Would be calculated from zone windows
        inline=True,
    )
    
    embed.add_field(
        name="⚠️ DANGER LEVEL",
        value=danger_level,
        inline=True,
    )
    
    embed.add_field(
        name="🍀 LUCK FACTOR",
        value=f"+{luck_factor}%",
        inline=True,
    )
    
    embed.add_field(
        name="⌛ ACTION COOLDOWN",
        value=f"{cooldown}s",
        inline=True,
    )
    
    # Placeholder for mission (would be fetched from database)
    embed.add_field(
        name="🎯 TODAY'S CHALLENGE",
        value="[Mission data coming from database]",
        inline=False,
    )
    
    embed.set_footer(text="Select difficulty and activate mission to start")
    return embed


def zone_active_embed(zone_id: str, mission_data: dict, time_remaining_sec: int) -> discord.Embed:
    """Active mission display with progress bar, timer, and reward pool."""
    zone = ZONES_META.get(zone_id)
    if not zone:
        return discord.Embed(title="❌ Zone Not Found", color=0xFF0000)
    
    emoji = zone.get("emoji", "✨")
    title = f"{emoji} ACTIVE IN {zone['name']}"
    
    # Format time remaining
    minutes, seconds = divmod(time_remaining_sec, 60)
    time_str = f"{int(minutes):02d}:{int(seconds):02d}"
    
    # Mission progress display
    target_item_id = mission_data.get("mission_target_item_id", "unknown")
    target_qty = mission_data.get("mission_target_qty", 0)
    progress = mission_data.get("mission_progress", 0)
    
    item = ITEMS.get(target_item_id, {"name": target_item_id, "emoji": "✨"})
    
    embed = discord.Embed(
        title=title,
        color=0x27AE60,
    )
    
    embed.add_field(
        name="🎯 MISSION",
        value=f"Collect {target_qty} {item.get('emoji', '✨')} **{item['name']}**",
        inline=False,
    )
    
    # Progress bar
    bar_length = 10
    filled = min(bar_length, int((progress / max(target_qty, 1)) * bar_length))
    progress_bar = "🟩" * filled + "⬜" * (bar_length - filled)
    
    embed.add_field(
        name="📊 PROGRESS",
        value=f"{progress_bar} {progress}/{target_qty}",
        inline=False,
    )
    
    embed.add_field(
        name="⏱️ TIME REMAINING",
        value=time_str,
        inline=True,
    )
    
    embed.add_field(
        name="📍 STATUS",
        value="✅ READY TO COMPLETE" if progress >= target_qty else "🟨 IN PROGRESS",
        inline=True,
    )
    
    # Placeholder reward pool
    embed.add_field(
        name="🎁 RANDOM REWARD POOL",
        value="[Rewards from zone]",
        inline=False,
    )
    
    embed.add_field(
        name="📝 INSTRUCTIONS",
        value="Collect items to progress mission. Complete button unlocks when mission is done or time expires.",
        inline=False,
    )
    
    embed.set_footer(text="Each activity has a cooldown | Mission expires after 1 hour")
    return embed


def zone_harvest_embed(zone_id: str, item_id: str, rarity: str, metadata_type: str = None, 
                       metadata_value: str = None, mission_progress: int = 0, 
                       mission_target: int = 0) -> discord.Embed:
    """Single activity result: item name, rarity, metadata, mission progress."""
    zone = ZONES_META.get(zone_id)
    item = ITEMS.get(item_id, {"name": item_id, "emoji": "✨"})
    
    if not zone:
        return discord.Embed(title="❌ Zone Not Found", color=0xFF0000)
    
    # Get result message based on zone
    zone_names = {
        "fishing": "CATCH RESULT",
        "botany": "GATHER RESULT",
        "archaeology": "DIG RESULT",
        "scavenge": "SEARCH RESULT",
    }
    result_name = zone_names.get(zone_id, "RESULT")
    emoji = zone.get("emoji", "✨")
    
    embed = discord.Embed(
        title=f"{emoji} {result_name}",
        color=RARITY_COLORS.get(rarity, 0x95A5A6),
    )
    
    # Item name and rarity
    embed.add_field(
        name="🎯 YOU FOUND",
        value=f"{item.get('emoji', '✨')} **{item['name']}**",
        inline=False,
    )
    
    embed.add_field(
        name="💎 RARITY",
        value=rarity,
        inline=True,
    )
    
    # Metadata (weight, quality, condition, state)
    if metadata_type and metadata_value:
        metadata_labels = {
            "weight": f"⚖️ Weight: {metadata_value} kg",
            "quality": f"✨ Quality: {metadata_value}",
            "condition": f"🟢 Condition: {metadata_value}",
            "state": f"🪙 State: {metadata_value}",
        }
        metadata_display = metadata_labels.get(metadata_type, f"{metadata_type}: {metadata_value}")
        embed.add_field(
            name="📋 DETAILS",
            value=metadata_display,
            inline=True,
        )
    
    # Mission progress
    if mission_target > 0:
        embed.add_field(
            name="🎯 MISSION PROGRESS",
            value=f"{mission_progress} / {mission_target}",
            inline=False,
        )
    
    embed.set_footer(text="Activity has a cooldown before next attempt")
    return embed


def zone_completion_embed(zone_id: str, mission_data: dict, rewards: dict) -> discord.Embed:
    """Mission completion: mission progress and final rewards."""
    zone = ZONES_META.get(zone_id)
    if not zone:
        return discord.Embed(title="❌ Zone Not Found", color=0xFF0000)
    
    emoji = zone.get("emoji", "✨")
    embed = discord.Embed(
        title=f"⏰ ZONE SESSION ENDED - {emoji} {zone['name']}",
        color=0xF39C12,
    )
    
    # Mission progress
    target_qty = mission_data.get("mission_target_qty", 0)
    final_progress = mission_data.get("mission_progress", 0)
    
    item_id = mission_data.get("mission_target_item_id", "unknown")
    item = ITEMS.get(item_id, {"name": item_id, "emoji": "✨"})
    
    completion_status = "✅ COMPLETE" if final_progress >= target_qty else "🟨 INCOMPLETE"
    
    embed.add_field(
        name="🎯 MISSION PROGRESS",
        value=f"{item.get('emoji', '✨')} **{item['name']}**\n{final_progress} / {target_qty} {completion_status}",
        inline=False,
    )
    
    # Rewards
    coins = rewards.get("coins", 0)
    xp = rewards.get("xp", 0)
    
    embed.add_field(
        name="🎁 REWARDS EARNED",
        value=f"💰 **{coins:,}** Coins\n✨ **{xp}** XP",
        inline=True,
    )
    
    # Bonus rewards
    if rewards.get("bonus_items"):
        bonus_text = "\n".join([f"{b.get('emoji', '✨')} {b['name']}" for b in rewards["bonus_items"]])
        embed.add_field(
            name="🧿 BONUS ITEMS",
            value=bonus_text,
            inline=True,
        )
    
    embed.add_field(
        name="📝 INSTRUCTIONS",
        value="Click [Complete Mission] to claim rewards and return to zone selector.",
        inline=False,
    )
    
    embed.set_footer(text="Session window has expired")
    return embed


def zone_cooldown_embed(zone_id: str, cooldown_remaining_sec: int) -> discord.Embed:
    """Cooldown timer display."""
    zone = ZONES_META.get(zone_id)
    if not zone:
        return discord.Embed(title="❌ Zone Not Found", color=0xFF0000)
    
    emoji = zone.get("emoji", "✨")
    embed = discord.Embed(
        title=f"⏳ ACTION ON COOLDOWN - {emoji} {zone['name']}",
        description=f"You must wait before attempting another activity.",
        color=0xE74C3C,
    )
    
    # Format time remaining
    minutes, seconds = divmod(cooldown_remaining_sec, 60)
    time_str = f"{int(minutes):02d}:{int(seconds):02d}" if minutes > 0 else f"{int(seconds):02d}s"
    
    embed.add_field(
        name="⏱️ TIME REMAINING",
        value=time_str,
        inline=False,
    )
    
    embed.set_footer(text="Cooldown prevents spam and adds difficulty balance")
    return embed
