from datetime import datetime
import discord

from game.data import ITEMS, ZONES, get_live_events, MUSEUM_COLLECTIONS, MUSEUM_ARTIFACT_TEXT, EXCLUSIVE_ITEMS
from game.leveling import xp_to_next_level


RARITY_COLORS = {
    "Common": 0x95A5A6,
    "Uncommon": 0x2ECC71,
    "Rare": 0x3498DB,
    "Epic": 0x9B59B6,
    "Legendary": 0xF1C40F,
    "Mythic": 0xE91E63,
}


def build_xp_bar(current_xp: int, level: int, size: int = 8) -> str:
    needed = xp_to_next_level(level)
    if needed <= 0:
        return "🟩" * size

    filled = round((current_xp / needed) * size)
    filled = max(0, min(size, filled))
    empty = size - filled
    return f"{'🟩' * filled}{'⬜' * empty} {current_xp}/{needed}"


def profile_embed(
    player,
    inventory_count,
    recent_finds,
    active_effects,
    equipment,
    avatar_url,
):
    """Reorganized profile embed with sections for Equipment, Stats, Activity, and Recent Finds."""
    
    # ═══════ HEADER SECTION ═══════
    embed = discord.Embed(
        title=f"🧍 PROFILE 🧍",
        description=(
            f"👤 {player['username']}\n"
            f"⚙️ ✧ {player['current_title']} ✧ ⚙️"
        ),
        color=0x2C2F33,
        timestamp=datetime.utcnow(),
    )
    
    if avatar_url:
        embed.set_thumbnail(url=avatar_url)

    # ═══════ EQUIPMENT SECTION ═══════
    equipment_lines = []
    if equipment:
        # Organize by slot
        equipped_by_slot = {item.get("slot"): item for item in equipment if isinstance(item, dict) and "item_id" in item}
        
        for slot in ["Head", "Left Hand", "Right Hand", "Feet"]:
            if slot in equipped_by_slot:
                item_id = equipped_by_slot[slot]["item_id"]
                item = ITEMS.get(item_id, {"name": item_id})
                equipment_lines.append(f"  {slot:12} » {item.get('emoji', '✨')} {item['name']}")
            else:
                equipment_lines.append(f"  {slot:12} » [Empty]")
    else:
        for slot in ["Head", "Left Hand", "Right Hand", "Feet"]:
            equipment_lines.append(f"  {slot:12} » [Empty]")
    
    embed.add_field(
        name="🎒 EQUIPMENT",
        value="\n".join(equipment_lines),
        inline=False
    )

    # ═══════ STATS SECTION ═══════
    hunger_bar = "🟩" * (player.get("hunger", 100) // 20) + "⬜" * (5 - (player.get("hunger", 100) // 20))
    
    stats_lines = [
        f"  💰 Coins   » {player['coins']:,}",
        f"  ⭐ Level   » {player['level']}",
        f"  🎒 Loots   » {inventory_count}",
        f"  ❤️ Hunger » {hunger_bar} {player.get('hunger', 100)}/100",
    ]
    
    embed.add_field(
        name="💰 STATS",
        value="\n".join(stats_lines),
        inline=False
    )

    # ═══════ PROGRESSION SECTION ═══════
    xp_bar = build_xp_bar(player["xp"], player["level"], size=10)
    embed.add_field(
        name="✨ PROGRESSION",
        value=f"  {xp_bar}",
        inline=False
    )

    # ═══════ ACTIVITY SECTION ═══════
    zone_name = ZONES.get(player["current_zone_id"], {}).get("name", "Unknown")
    activity_lines = [
        f"  🗑️ Dives  » {player['total_dives']}",
        f"  📍 Zone   » {zone_name}",
    ]
    
    if player.get("last_dive_at"):
        from datetime import datetime as dt
        try:
            last_dive = dt.fromisoformat(player["last_dive_at"].replace("Z", "+00:00"))
            activity_lines.append(f"  🕒 Last Active » {last_dive.strftime('%I:%M %p')}")
        except:
            pass
    
    embed.add_field(
        name="📊 ACTIVITY",
        value="\n".join(activity_lines),
        inline=False
    )

    # ═══════ RECENT FINDS SECTION ═══════
    recent_text = "\n".join(recent_finds[-5:]) if recent_finds else "  None yet"
    embed.add_field(
        name="🎁 RECENT FINDS",
        value=recent_text,
        inline=False
    )

    # ═══════ ACTIVE EFFECTS (if any) ═══════
    if active_effects:
        effect_lines = []
        for effect in active_effects[:4]:
            if isinstance(effect, dict):
                label = effect.get("label", "Effect")
                expires = effect.get("expires_at", "soon")
                effect_lines.append(f"  ⏳ {label} — {expires}")
        
        if effect_lines:
            embed.add_field(
                name="⏳ ACTIVE BUFFS",
                value="\n".join(effect_lines),
                inline=False
            )

    embed.set_footer(text="Use buttons below to interact")
    return embed


def dive_processing_embed(zone_name, text):
    return discord.Embed(
        title="🗑️ Diving...",
        description=f"**{zone_name}**\n\n{text}",
        color=0x5865F2,
    )


def dive_result_embed(
    player,
    item_id,
    leveled_up,
    reaction_text=None,
    event_text=None,
    bonus_text=None,
    unlocked_zone_names=None,
    avatar_url=None,
    attachment_filename=None,
):
    item = ITEMS[item_id]
    rarity = item.get("rarity", "Common")

    lines = [
        f"{item.get('emoji', '✨')} **{item['name']}**",
        f"{rarity}",
    ]

    if item.get("flavor"):
        lines.append(f"*{item['flavor']}*")

    if event_text:
        lines.append(event_text)
    if bonus_text:
        lines.append(bonus_text)
    if reaction_text:
        lines.append(f"_{reaction_text}_")
    if leveled_up:
        lines.append(f"⬆️ You leveled up to **Level {player['level']}**!")
    if unlocked_zone_names:
        lines.append(f"🔓 New zones unlocked: **{', '.join(unlocked_zone_names)}**")

    embed = discord.Embed(
        title="✨ Loot Found!",
        description="\n\n".join(lines),
        color=RARITY_COLORS.get(rarity, 0x57F287),
    )

    if avatar_url:
        embed.set_author(name=player["username"], icon_url=avatar_url)

    embed.add_field(name="💰 Coins", value=str(player["coins"]), inline=True)
    embed.add_field(name="⭐ Level", value=str(player["level"]), inline=True)
    embed.add_field(name="🗑️ Total Dives", value=str(player["total_dives"]), inline=True)
    embed.add_field(name="✨ XP", value=build_xp_bar(player["xp"], player["level"]), inline=False)
    return embed


def inventory_embed(username: str, lines: list[str], page: int, total_pages: int) -> discord.Embed:
    embed = discord.Embed(
        title=f"🎒 {username}'s Loot Vault",
        description="\n\n".join(lines) if lines else "Your bag is empty.",
        color=0x5865F2,
    )
    embed.set_footer(text=f"Page {page + 1}/{total_pages}")
    return embed


def inventory_with_rewards_embed(
    username: str,
    equipment: dict[str, str],
    unopened_rewards: list[tuple[str, int]],
    page: int = 0,
    total_pages: int = 1,
) -> discord.Embed:
    """
    Enhanced inventory showing equipment + unopened rewards.
    
    Args:
        username: Player username
        equipment: Dict mapping slot names to item names
        unopened_rewards: List of (reward_name, quantity) tuples
        page: Current page of rewards
        total_pages: Total pages of rewards
    """
    from game.zones import REWARD_POOL
    
    # Equipment section
    equipment_lines = []
    for slot in ["Head", "Left Hand", "Right Hand", "Feet"]:
        item = equipment.get(slot, "[Empty]")
        equipment_lines.append(f"  {slot:12} » {item}")
    
    equipment_section = "🎒 **EQUIPMENT & REWARDS**\n" + "\n".join(equipment_lines)
    
    # Unopened rewards section with pagination
    per_page = 6
    start = page * per_page
    end = start + per_page
    current_rewards = unopened_rewards[start:end]
    
    reward_lines = []
    for reward_name, qty in current_rewards:
        reward_lines.append(f"  {qty}x {reward_name}")
    
    rewards_section = "\n\n🎁 **UNOPENED REWARDS**\n" + "\n".join(reward_lines) if reward_lines else ""
    
    description = equipment_section + rewards_section
    
    if not reward_lines and not equipment_lines:
        description = "Your inventory is empty!"
    
    embed = discord.Embed(
        title=f"📦 {username}'s Inventory",
        description=description,
        color=0x5865F2,
    )
    
    if unopened_rewards:
        embed.set_footer(text=f"Rewards Page {page + 1}/{total_pages} • Use buttons to manage")
    
    return embed


def mix_lab_embed(inventory_map, mix_lines):
    return discord.Embed(
        title="🧪 Goblin Mix Lab",
        description="Available recipes right now:\n" + ("\n".join(mix_lines) if mix_lines else "None"),
        color=0x9B59B6,
    )


def mix_result_embed(title: str, result_text: str) -> discord.Embed:
    return discord.Embed(title=title, description=result_text, color=0x9B59B6)


def events_embed() -> discord.Embed:
    embed = discord.Embed(title="✨ World Events", description="The world is messier on purpose.", color=0xEB459E)
    live = get_live_events()
    if not live:
        embed.add_field(name="🌫️ Right Now", value="No special event is live.", inline=False)
    else:
        for event in live:
            embed.add_field(name=f"{event.get('emoji', '✨')} {event['name']}", value=event.get("description", ""), inline=False)
    return embed


def help_embed() -> discord.Embed:
    return discord.Embed(title="❓ How to Play", description="Dive, loot, mix, and survive the junk economy.", color=0xFAA61A)

def pawn_shop_embed(bundle_item_ids: list[str]) -> discord.Embed:
    from game.data import ITEMS

    if not bundle_item_ids:
        desc = "The pawn shop owner stares at you.\n\nYou have nothing worth trading."
    else:
        lines = []
        counts = {}
        for item_id in bundle_item_ids:
            counts[item_id] = counts.get(item_id, 0) + 1

        for item_id, qty in counts.items():
            item = ITEMS.get(item_id, {"name": item_id, "emoji": "✨"})
            lines.append(f"{item.get('emoji','✨')} **{item['name']}** x{qty}")

        desc = (
            "🏚️ *The pawn shop owner squints at your junk...*\n\n"
            "**Your Offer Pile:**\n"
            + "\n".join(lines)
            + "\n\nChoose your deal carefully..."
        )

    embed = discord.Embed(
        title="🏚️ Sketchy Pawn Shop",
        description=desc,
        color=0x8B5E3C,
    )
    return embed


def pawn_offer_result_embed(title: str, description: str) -> discord.Embed:
    return discord.Embed(
        title=title,
        description=description,
        color=0xD4AF37,
    )

def museum_home_embed(username: str, discovered_item_ids: set[str]) -> discord.Embed:
    total_discovered = len(discovered_item_ids)
    total_artifacts = sum(len(collection["item_ids"]) for collection in MUSEUM_COLLECTIONS.values())

    embed = discord.Embed(
        title="🏛️ Trash Museum",
        description=(
            "\"Most people see garbage. You preserve history.\"\n\n"
            f"**Curator:** {username}\n"
            f"**Discovery Progress:** {total_discovered}/{total_artifacts} artifacts"
        ),
        color=0xC27C2C,
    )

    for collection_id, collection in MUSEUM_COLLECTIONS.items():
        item_ids = collection["item_ids"]
        discovered = sum(1 for item_id in item_ids if item_id in discovered_item_ids)
        embed.add_field(
            name=f"{collection['emoji']} {collection['name']}",
            value=(
                f"{collection['description']}\n"
                f"**Progress:** {discovered}/{len(item_ids)}"
            ),
            inline=False,
        )

    embed.set_footer(text="Choose a collection to browse its artifacts")
    return embed


def museum_collection_embed(
    username: str,
    collection_id: str,
    discovered_item_ids: set[str],
    page: int,
    total_pages: int,
):
    collection = MUSEUM_COLLECTIONS[collection_id]
    item_ids = collection["item_ids"]
    per_page = 6
    start = page * per_page
    end = start + per_page
    current_ids = item_ids[start:end]

    lines = []
    for item_id in current_ids:
        item = ITEMS.get(item_id, {"name": item_id, "emoji": "✨", "rarity": "Unknown"})
        discovered = item_id in discovered_item_ids
        if discovered:
            lines.append(
                f"✅ {item.get('emoji', '✨')} **{item['name']}**\n"
                f"{item.get('rarity', 'Unknown')} artifact recovered"
            )
        else:
            lines.append(
                "❔ **Unknown Artifact**\n"
                "Undiscovered relic. Keep diving, mixing, and refining."
            )

    embed = discord.Embed(
        title=f"{collection['emoji']} {collection['name']}",
        description="\n\n".join(lines),
        color=0x5865F2,
    )
    embed.add_field(
        name="Collection Notes",
        value=collection["description"],
        inline=False,
    )
    embed.set_footer(text=f"{username} • Page {page + 1}/{total_pages}")
    return embed


def museum_artifact_embed(item_id: str, discovered: bool) -> discord.Embed:
    item = ITEMS.get(item_id, {"name": item_id, "emoji": "✨", "rarity": "Unknown", "flavor": ""})
    lore = MUSEUM_ARTIFACT_TEXT.get(item_id, {})

    if discovered:
        description = (
            f"{item.get('emoji', '✨')} **{item['name']}**\n"
            f"**Status:** Collected ✅\n"
            f"**Rarity:** {item.get('rarity', 'Unknown')}\n\n"
            f"*{lore.get('museum_text') or item.get('flavor', 'Recovered from the underground junk world.')}*"
        )
        origin_text = lore.get("origin", "Origin not yet archived.")
        color = RARITY_COLORS.get(item.get("rarity", "Common"), 0x5865F2)
    else:
        description = (
            "❔ **Unknown Artifact**\n"
            "**Status:** Undiscovered\n\n"
            "Its details are still obscured. Recover it in the field to archive it here."
        )
        origin_text = "Unknown origin"
        color = 0x4E5D94

    embed = discord.Embed(
        title="🏛️ Artifact Card",
        description=description,
        color=color,
    )
    embed.add_field(name="Origin", value=origin_text, inline=False)

    return embed


def pawn_shop_main_embed(username: str) -> discord.Embed:
    embed = discord.Embed(
        title="🎒 Pawn Shop 🎒",
        description=(
            f"WELCOME, SHADY **{username}** !\n\n"
            f"💰 Spend wisely —\n"
            f"🎟️ Browse to your heart's content —"
        ),
        color=0x8B4513,
    )
    embed.set_footer(text="Choose your shopping category below")
    return embed


def pawn_shop_tickets_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🎟️ Dirty Tickets 🎟️",
        description="🎟️ BUY TICKETS\n\n*Redeem your tickets in The Tavern",
        color=0xDAA520,
    )
    embed.add_field(name="[🎟️] Dirty Ticket x1", value="🪙 1000", inline=False)
    embed.add_field(name="[🎟️] Dirty Ticket x5", value="🪙 4500", inline=False)
    embed.add_field(name="[🎟️] Dirty Ticket x10", value="🪙 8500", inline=False)
    embed.set_footer(text="Choose a ticket bundle or go back")
    return embed


def pawn_shop_items_embed(page: int = 0) -> discord.Embed:
    from game.data import PAWN_BUFFERS, PAWN_AMULETS
    
    embed = discord.Embed(
        title="🏪 ITEMS SHOP 🏪",
        description="⚗️ BUFFERS **All Effects last 2 Real Time hours\n",
        color=0x9B59B6,
    )
    
    # Add buffers
    for buffer_item in PAWN_BUFFERS:
        embed.add_field(
            name=f"{buffer_item['emoji']} {buffer_item['name']}",
            value=f"✨ {buffer_item['bonus']} 🪙 {buffer_item['price']}",
            inline=False,
        )
    
    embed.add_field(name="\u200b", value="🧿 AMULETS **All Effects last 2 Real Time hours", inline=False)
    
    # Add amulets
    for amulet_item in PAWN_AMULETS:
        embed.add_field(
            name=f"{amulet_item['emoji']} {amulet_item['name']}",
            value=f"💎 {amulet_item['bonus']} 🪙 {amulet_item['price']}",
            inline=False,
        )
    
    embed.set_footer(text="Click buttons below to purchase items")
    return embed


def pawn_shop_specials_embed() -> discord.Embed:
    from game.data import PAWN_SPECIALS
    
    embed = discord.Embed(
        title="🪄 Special Items 🪄",
        description="Exclusive limited-time offers",
        color=0xE91E63,
    )
    
    for special in PAWN_SPECIALS:
        embed.add_field(
            name=f"{special['emoji']} {special['name']}",
            value=special['description'],
            inline=False,
        )
    
    embed.set_footer(text="Check back soon for exclusive deals!")
    return embed


def pawn_shop_exchange_embed() -> discord.Embed:
    embed = discord.Embed(
        title="♻️ EXCHANGE LOOT ♻️",
        description="Convert your junk into something better",
        color=0x2ECC71,
    )
    
    embed.add_field(
        name="[♻️ ???] Trade Loot",
        value="Trade suspicious loot - AT YOUR OWN RISK",
        inline=False,
    )
    embed.add_field(
        name="[♻️ ???] Trade All",
        value="Trade ALL YOUR LOOTS for a random prize",
        inline=False,
    )
    embed.add_field(
        name="[♻️ ???] Sell Loot",
        value="Sell your Loots - 20% disposal fee",
        inline=False,
    )
    
    embed.set_footer(text="Choose an exchange option or go back")
    return embed


# ═══════════════════════════════════════════════════════════════════
# EXCLUSIVE COLLECTIBLES EMBEDS
# ═══════════════════════════════════════════════════════════════════

def exclusive_inventory_main_embed(username: str, exclusive_counts: dict) -> discord.Embed:
    """Main exclusive inventory embed showing all categories with counts."""
    embed = discord.Embed(
        title=f"🧸 {username}'s Exclusive Rares Collection 🧸",
        description="Your personal collection of exclusive collectibles. Choose a category to view items.",
        color=0xFF69B4,
    )
    
    total = sum(exclusive_counts.values())
    embed.add_field(
        name="📊 Collection Overview",
        value=(
            f"🧸 **Toys:** {exclusive_counts.get('Toys', 0)} items\n"
            f"🐶 **Dogs:** {exclusive_counts.get('Dogs', 0)} items\n"
            f"🐱 **Cats:** {exclusive_counts.get('Cats', 0)} items\n"
            f"🪽 **Wings:** {exclusive_counts.get('Wings', 0)} items\n"
            f"**Total:** {total} exclusives"
        ),
        inline=False,
    )
    
    embed.set_footer(text="Click a category button to browse your collection")
    return embed


def exclusive_category_embed(
    username: str,
    category: str,
    items: list[dict],
    page: int,
    total_pages: int,
    category_emoji: str = "✨",
) -> discord.Embed:
    """Embed showing paginated exclusive items in a category."""
    embed = discord.Embed(
        title=f"{category_emoji} {username}'s {category} Collection",
        description=f"Showing page {page + 1} of {total_pages}",
        color=0xFF69B4,
    )
    
    if items:
        for item in items:
            exclusive_id = item.get("exclusive_id", "unknown")
            name = item.get("name", exclusive_id)
            flavor = item.get("flavor", "A rare and precious collectible.")
            embed.add_field(name=name, value=flavor, inline=False)
    else:
        embed.description = "You don't have any items in this category yet!"
    
    embed.set_footer(text=f"Page {page + 1}/{total_pages} • {category_emoji} {category}")
    return embed


def exclusive_detail_embed(exclusive_item: dict) -> discord.Embed:
    """Embed showing detailed information about a single exclusive item."""
    name = exclusive_item.get("name", "Unknown Exclusive")
    category = exclusive_item.get("category", "Unknown")
    flavor = exclusive_item.get("flavor", "A mysterious exclusive collectible.")
    
    category_emoji = {
        "Toys": "🧸",
        "Dogs": "🐶",
        "Cats": "🐱",
        "Wings": "🪽",
    }.get(category, "✨")
    
    embed = discord.Embed(
        title=f"{category_emoji} {name}",
        description=flavor,
        color=0xFF69B4,
    )
    
    embed.add_field(name="Category", value=category, inline=True)
    embed.add_field(name="Rarity", value="Exclusive", inline=True)
    
    embed.set_footer(text="Use buttons to view more items or equip this exclusive")
    return embed


def exclusive_reward_embed(exclusive_item: dict) -> discord.Embed:
    """Embed for revealing a newly acquired exclusive reward."""
    name = exclusive_item.get("name", "Unknown Exclusive")
    category = exclusive_item.get("category", "Unknown")
    flavor = exclusive_item.get("flavor", "A mysterious exclusive collectible.")
    
    category_emoji = {
        "Toys": "🧸",
        "Dogs": "🐶",
        "Cats": "🐱",
        "Wings": "🪽",
    }.get(category, "✨")
    
    embed = discord.Embed(
        title="✨ EXCLUSIVE REWARD! ✨",
        description=(
            f"🎉 You've obtained a new exclusive!\n\n"
            f"{category_emoji} **{name}**\n"
            f"*{flavor}*\n\n"
            f"Added to your collection!"
        ),
        color=0xFF69B4,
    )
    
    embed.set_footer(text="Check your Exclusive Rares collection to view it!")
    return embed


# ═══════════════════════════════════════════════════════════════════
# THE TAVERN EMBEDS
# ═══════════════════════════════════════════════════════════════════

def tavern_main_embed(username: str) -> discord.Embed:
    """Main tavern welcome embed."""
    embed = discord.Embed(
        title="🍻 The Tavern 🍻",
        description=(
            f"🧔‍♂️ Fabian: Hey hey~ {username}! ✨\n"
            f"Welcome to my cozy tavern 💛\n"
            f"What can I do for ya today?"
        ),
        color=0x8B4513,
    )
    embed.set_footer(text="Choose an option below")
    return embed


def tavern_food_shop_embed() -> discord.Embed:
    """Food and drinks shop embed."""
    from game.data import TAVERN_FOOD
    
    embed = discord.Embed(
        title="🍓 FOOD & DRINKS SHOP 🍓",
        description="Restore your hunger with delicious treats!",
        color=0xFF69B4,
    )
    
    for food in TAVERN_FOOD:
        embed.add_field(
            name=f"{food['emoji']} {food['name']}",
            value=f"+{food['hunger_restored']} HP • 🪙 {food['price']}",
            inline=False,
        )
    
    embed.set_footer(text="Click buttons to purchase food")
    return embed


def tavern_ticket_redeem_embed(username: str, ticket_count: int) -> discord.Embed:
    """Ticket redemption embed."""
    embed = discord.Embed(
        title="🎟️ Ticket Counter 🎟️",
        description=(
            f"👩‍🍳 Martha: Hiya {username}! 💕\n"
            f"Cashing in your tickets today? 🎟️\n\n"
            f"🎟️ Dirty Tickets: **{ticket_count}**"
        ),
        color=0xDAA520,
    )
    embed.set_footer(text="Choose how many tickets to redeem")
    return embed


def tavern_redeem_single_embed(item_name: str) -> discord.Embed:
    """Single ticket redemption result."""
    embed = discord.Embed(
        title="🌟 Congratulations! 🌟",
        description=(
            f"🎟️ -1 Ticket deducted.\n"
            f"🎁 You received: **{item_name}**\n"
            f"💖 Added safely to your inventory!"
        ),
        color=0xFFD700,
    )
    return embed


def tavern_redeem_multi_embed(items: list[str], count: int) -> discord.Embed:
    """Multiple ticket redemption result."""
    items_text = "\n".join([f"🎁 {item}" for item in items])
    
    embed = discord.Embed(
        title="🌟 Congratulations! 🌟",
        description=(
            f"🎟️ -{count} Tickets redeemed.\n"
            f"✨ Loot incoming!!\n\n"
            f"{items_text}\n\n"
            f"so many goodies omg ✨\n"
            f"💖 All items safely to your inventory!"
        ),
        color=0xFFD700,
    )
    return embed


# ═══════════════════════════════════════════════════════════════════
# ZONE FARMING EMBEDS
# ═══════════════════════════════════════════════════════════════════

def zone_selector_embed(player_level: int, current_zone_id: str | None) -> discord.Embed:
    """Main zone selector showing all available zones."""
    embed = discord.Embed(
        title="🗺️ ZONE SELECTOR 🗺️",
        description="Choose a zone to farm items, complete missions, and gather resources.\n\n**Tips:** Zones unlock as you level up. Harder zones have better rewards!",
        color=0x2ECC71,
    )
    
    for zone_id, zone_data in ZONES.items():
        is_current = zone_id == current_zone_id
        is_unlocked = player_level >= zone_data["unlock_level"]
        
        if is_unlocked:
            status = "🟢 ACTIVE" if is_current else "✅ READY"
            color_marker = "🟢" if is_current else "🟢"
        else:
            status = f"🔒 Level {zone_data['unlock_level']}"
            color_marker = "🔴"
        
        zone_info = (
            f"{color_marker} **{zone_data['name']}**\n"
            f"Status: {status}\n"
            f"⏱️ Cooldown: {zone_data.get('cooldown', '???')}s"
        )
        
        embed.add_field(name=zone_data.get('unicode_style', zone_data['name']), value=zone_info, inline=False)
    
    embed.set_footer(text="Click zone button below to enter or get info")
    return embed


def zone_info_embed(zone_id: str, player_level: int) -> discord.Embed:
    """Detailed info about a single zone."""
    zone = ZONES[zone_id]
    is_unlocked = player_level >= zone["unlock_level"]
    
    if is_unlocked:
        description = (
            f"{zone['description']}\n\n"
            f"**Danger Level:** {zone['danger']}\n"
            f"**Luck Factor:** {zone['luck']}\n"
            f"**Action Cooldown:** {zone.get('cooldown', 'N/A')}s"
        )
        color = 0x2ECC71
    else:
        description = (
            f"*This zone is locked.*\n"
            f"**Unlocks at Level {zone['unlock_level']}**\n\n"
            f"Keep diving and leveling up to access this zone!"
        )
        color = 0xED4245
    
    embed = discord.Embed(
        title=f"🗺️ {zone['name']}",
        description=description,
        color=color,
    )
    
    embed.add_field(name="⚡ Challenge", value=zone.get('unicode_style', zone['name']), inline=False)
    embed.set_footer(text="Return to zone selector or enter this zone")
    return embed


def zone_active_embed(zone_id: str, mission_data: dict, time_remaining_sec: int | None = None) -> discord.Embed:
    """Embed showing active zone mission with reward pool."""
    from game.zones import REWARD_POOL
    
    zone = ZONES[zone_id]
    mission = mission_data or {}
    
    rarity = mission.get('target_rarity', 'Unknown')
    quantity = mission.get('target_quantity', 0)
    collected = mission.get('progress', 0)
    remaining = quantity - collected
    
    progress_bar = "🟩" * collected + "⬜" * max(0, remaining)
    
    mission_complete = collected >= quantity
    complete_status = "✅ READY TO COMPLETE" if mission_complete else "🔒 Complete when done"
    
    # Build reward pool list
    reward_pool_text = "**🎁 Random Reward Pool:**\n"
    for reward_id in REWARD_POOL.keys():
        reward = REWARD_POOL[reward_id]
        reward_name = reward.get('name', 'Unknown Reward')
        
        # Add reward details if applicable
        if reward.get('type') == 'zone_box':
            reward_pool_text += f"{reward_name} — {reward.get('xp_reward', 0)} XP\n"
        elif reward.get('type') == 'coin_bag':
            reward_pool_text += f"{reward_name} — ${reward.get('coin_reward', 0):,}\n"
        else:
            reward_pool_text += f"{reward_name}\n"
    
    description = (
        f"🎯 **MISSION:** Collect {quantity} {rarity} items\n"
        f"**Progress:** {collected}/{quantity}\n\n"
        f"{progress_bar}\n\n"
        f"**Status:** {complete_status}\n\n"
        f"{reward_pool_text}"
    )
    
    if time_remaining_sec and time_remaining_sec > 0:
        mins = time_remaining_sec // 60
        secs = time_remaining_sec % 60
        description += f"\n⏳ **Time Remaining:** {mins:02d}:{secs:02d}"
    
    embed = discord.Embed(
        title=f"⛏️ ACTIVE IN {zone['name']}",
        description=description,
        color=RARITY_COLORS.get(rarity, 0x5865F2),
    )
    
    embed.set_footer(text="Collect items to progress mission. Complete button available when done.")
    return embed


def zone_harvest_embed(item_id: str, quantity: int = 1) -> discord.Embed:
    """Embed for a harvest result from zone activity."""
    item = ITEMS.get(item_id, {"name": item_id, "emoji": "✨"})
    rarity = item.get("rarity", "Common")
    
    description = (
        f"✨ **{item['name']}** x{quantity}\n"
        f"Rarity: **{rarity}**\n\n"
        f"*{item.get('flavor', 'A curious find from the zone.')}*"
    )
    
    embed = discord.Embed(
        title="🎁 HARVEST!",
        description=description,
        color=RARITY_COLORS.get(rarity, 0x5865F2),
    )
    
    embed.set_footer(text="Item added to inventory • Continue harvesting or complete mission")
    return embed


def zone_completion_embed(zone_id: str, mission_data: dict, rewards: dict) -> discord.Embed:
    """Embed showing zone session completion and rewards."""
    zone = ZONES[zone_id]
    mission = mission_data or {}
    
    description = (
        f"✅ **{zone['name']} SESSION COMPLETE**\n\n"
        f"**Mission:** Collect {mission.get('target_quantity', 0)} {mission.get('target_rarity', 'Unknown')} items\n"
        f"**Status:** COMPLETED ✓\n\n"
        f"**Rewards Earned:**\n"
        f"💰 Coins: +{rewards.get('coins', 0)}\n"
        f"⭐ XP: +{rewards.get('xp', 0)}\n"
    )
    
    if rewards.get('bonus_encountered'):
        description += f"\n🎉 **Bonus:** {rewards['bonus_encountered']}"
    
    description += "\n\nReady for another session?"
    
    embed = discord.Embed(
        title="🏆 MISSION SUCCESS! 🏆",
        description=description,
        color=0xFFD700,
    )
    
    embed.set_footer(text="Return to zone selector to try another zone or continue")
    return embed


def zone_cooldown_embed(zone_id: str, cooldown_remaining_sec: int) -> discord.Embed:
    """Embed showing zone cooldown remaining."""
    zone = ZONES[zone_id]
    mins = cooldown_remaining_sec // 60
    secs = cooldown_remaining_sec % 60
    
    embed = discord.Embed(
        title="⏳ ZONE ON COOLDOWN",
        description=(
            f"**{zone['name']}** needs a break.\n\n"
            f"⏳ **Time Until Ready:** {mins:02d}:{secs:02d}\n\n"
            f"Try another zone in the meantime!"
        ),
        color=0xED4245,
    )
    
    embed.set_footer(text="Return to zone selector")
    return embed


def tavern_redeem_all_embed(items: list[str], count: int) -> discord.Embed:
    """All tickets redemption result."""
    items_text = "\n".join([f"🎁 {item}" for item in items[:10]])  # Show first 10
    more_text = f"\n... and {len(items) - 10} more!" if len(items) > 10 else ""
    
    embed = discord.Embed(
        title="🎉 JACKPOT?! 🎉",
        description=(
            f"🎟️ All Tickets Redeemed ({count})\n"
            f"🎁 Look at all this loot!!\n"
            f"🌸 your bag is thriving fr 🌸\n\n"
            f"{items_text}{more_text}\n\n"
            f"💖 All items safely to your inventory!"
        ),
        color=0xFFD700,
    )
    return embed


def exclusive_unlock_embed(exclusive_item: dict, username: str) -> discord.Embed:
    """Exclusive item unlock notification."""
    name = exclusive_item.get("name", "Unknown Exclusive")
    category = exclusive_item.get("category", "Unknown")
    flavor = exclusive_item.get("flavor", "A mysterious exclusive collectible.")
    
    category_emoji = {
        "Toys": "🧸",
        "Dogs": "🐶",
        "Cats": "🐱",
        "Wings": "🪽",
    }.get(category, "✨")
    
    embed = discord.Embed(
        title="🌟 Exclusive Unlocked! 🌟",
        description=(
            f"{name}\n\n"
            f"🏷️ Category: {category_emoji} {category}\n"
            f"💖 Added to Exclusive Inventory\n"
            f"Congratulations {username}!"
        ),
        color=0xFF69B4,
    )
    embed.set_footer(text="Use buttons to view collection or continue")
    return embed


# ═══════════════════════════════════════════════════════════════════
# ZONE MISSION REWARD REVEAL EMBEDS
# ═══════════════════════════════════════════════════════════════════

def zone_mission_reward_single_embed(username: str, reward: dict) -> discord.Embed:
    """
    Single reward reveal embed - EXACT format per spec.
    
    ╔══════════ 🎉 Mission Complete! 🎉 ══════════╗
      ✨ Great job, [Username]!
      You received:
    
      🎁 [Reward Name]
    
      💖 It has been added to your inventory.
    ╚══════════════════════════════════════════════╝
    """
    reward_name = reward.get('name', 'Unknown Reward')
    
    embed = discord.Embed(
        title="🎉 Mission Complete! 🎉",
        description=(
            f"✨ Great job, {username}!\n"
            f"You received:\n\n"
            f"{reward_name}\n\n"
            f"💖 It has been added to your inventory."
        ),
        color=discord.Color.gold(),
    )
    
    return embed


def zone_mission_reward_double_embed(username: str, rewards: list[dict]) -> discord.Embed:
    """
    Double reward reveal embed - EXACT format per spec.
    
    ╔══════════ 🌟 Mission Rewards 🌟 ══════════╗
      Amazing work, [Username]!
      You received:
    
      1. 🎁 [Reward Name]
      2. 🎁 [Reward Name]
    
      💖 Both rewards were added to your inventory.
    ╚════════════════════════════════════════════╝
    """
    reward_lines = []
    for i, reward in enumerate(rewards, 1):
        reward_name = reward.get('name', 'Unknown Reward')
        reward_lines.append(f"{i}. {reward_name}")
    
    embed = discord.Embed(
        title="🌟 Mission Rewards 🌟",
        description=(
            f"Amazing work, {username}!\n"
            f"You received:\n\n"
            + "\n".join(reward_lines) +
            f"\n\n💖 Both rewards were added to your inventory."
        ),
        color=discord.Color.gold(),
    )
    
    return embed


# ═══════════════════════════════════════════════════════════════════
# MUSEUM RELIC COLLECTION EMBEDS
# ═══════════════════════════════════════════════════════════════════

def museum_hub_embed(username: str, progress: dict) -> discord.Embed:
    """Main Museum Hub showing all 10 sets and progress."""
    from game.data import MUSEUM_SETS
    
    embed = discord.Embed(
        title="🏛️ MUSEUM",
        description="🧓 Curator: Welcome back, Diver.\nForgotten things are waiting to be remembered.",
        color=0x8B7355,
    )
    
    embed.add_field(
        name="📚 COLLECTIONS",
        value="\n".join([
            f"{MUSEUM_SETS[set_id]['emoji']} {MUSEUM_SETS[set_id]['name']:<30} {progress.get(set_id, {}).get('relics', 0)} / 5"
            for set_id in sorted(MUSEUM_SETS.keys(), key=lambda x: MUSEUM_SETS[x]["set_number"])
        ]),
        inline=False,
    )
    
    embed.set_footer(text="Use buttons below to explore the museum")
    return embed


def museum_sets_page_embed(page: int = 0) -> discord.Embed:
    """Paginated view of all 10 museum sets (5 per page)."""
    from game.data import MUSEUM_SETS
    
    all_sets = sorted(MUSEUM_SETS.items(), key=lambda x: x[1]["set_number"])
    start = page * 5
    end = start + 5
    page_sets = all_sets[start:end]
    
    embed = discord.Embed(
        title="📖 MUSEUM SETS",
        color=0x8B7355,
    )
    
    for set_id, set_data in page_sets:
        embed.add_field(
            name=f"{set_data['set_number']}. {set_data['name']}",
            value=set_data['lore'][:100] + "...",
            inline=False,
        )
    
    total_pages = (len(all_sets) + 4) // 5
    embed.set_footer(text=f"Page {page + 1} / {total_pages}")
    return embed


def museum_set_detail_embed(set_id: str, relics: list, player_relics: list) -> discord.Embed:
    """Show all 5 relics in a specific museum set."""
    from game.data import MUSEUM_SETS, RELICS, RELIC_RARITY_INFO
    
    if set_id not in MUSEUM_SETS:
        return discord.Embed(title="❌ Set Not Found", color=0xFF0000)
    
    set_data = MUSEUM_SETS[set_id]
    player_relic_ids = [r["relic_id"] for r in player_relics]
    
    embed = discord.Embed(
        title=f"{set_data['name']}",
        description=f"Progress: {len([r for r in player_relics if r['set_id'] == set_id])} / 5",
        color=0x8B7355,
    )
    
    # Find all relics for this set
    set_relics = [
        (rid, rdata) for rid, rdata in RELICS.items()
        if rdata["set_id"] == set_id
    ]
    
    for idx, (relic_id, relic_data) in enumerate(sorted(set_relics, key=lambda x: x[1].get("set_index", 0)), 1):
        collected = "✅" if relic_id in player_relic_ids else "❌"
        rarity_info = RELIC_RARITY_INFO.get(relic_data["rarity"], {})
        embed.add_field(
            name=f"{idx}. {relic_data['emoji']} {relic_data['name']} {collected}",
            value=f"*{rarity_info.get('name', 'Unknown')}*",
            inline=False,
        )
    
    embed.add_field(
        name="ℹ️ Set Description",
        value=set_data["lore"],
        inline=False,
    )
    
    return embed


def museum_relic_archive_embed(page: int, player_relics: list) -> discord.Embed:
    """Paginated archive of all discovered relics."""
    from game.data import RELICS, RELIC_RARITY_INFO
    
    # Group discovered relics by rarity
    discovered = sorted(
        [(r["relic_id"], RELICS[r["relic_id"]]) for r in player_relics],
        key=lambda x: list(RELIC_RARITY_INFO.keys()).index(x[1]["rarity"]) if x[1]["rarity"] in RELIC_RARITY_INFO else 999,
    )
    
    items_per_page = 5
    start = page * items_per_page
    end = start + items_per_page
    page_relics = discovered[start:end]
    
    embed = discord.Embed(
        title="🧿 RELIC ARCHIVE",
        color=0x8B7355,
    )
    
    if not page_relics:
        embed.description = "No relics discovered yet. Explore zones to find relics!"
        return embed
    
    for relic_id, relic_data in page_relics:
        rarity_info = RELIC_RARITY_INFO.get(relic_data["rarity"], {})
        emoji = rarity_info.get("emoji", "❓")
        embed.add_field(
            name=f"{relic_data['emoji']} {relic_data['name']}",
            value=f"{emoji} {rarity_info.get('name', 'Unknown Rarity')}",
            inline=False,
        )
    
    total_pages = max(1, (len(discovered) + items_per_page - 1) // items_per_page)
    embed.set_footer(text=f"Page {page + 1} / {total_pages} • {len(discovered)} relics discovered")
    return embed


def museum_relic_card_embed(relic_id: str) -> discord.Embed:
    """Individual relic card with full details."""
    from game.data import RELICS, MUSEUM_SETS, RELIC_RARITY_INFO
    
    if relic_id not in RELICS:
        return discord.Embed(title="❌ Relic Not Found", color=0xFF0000)
    
    relic = RELICS[relic_id]
    set_data = MUSEUM_SETS.get(relic["set_id"], {})
    rarity_info = RELIC_RARITY_INFO.get(relic["rarity"], {})
    
    embed = discord.Embed(
        title=f"🧿 RELIC ENTRY",
        color=rarity_info.get("color", 0x8B7355),
    )
    
    embed.add_field(
        name=f"{relic['emoji']} {relic['name']}",
        value="",
        inline=False,
    )
    
    embed.add_field(
        name="Rarity",
        value=f"{rarity_info.get('emoji', '❓')} {rarity_info.get('name', 'Unknown')}",
        inline=True,
    )
    
    embed.add_field(
        name="Set",
        value=f"{set_data.get('emoji', '❓')} {set_data.get('name', 'Unknown')}",
        inline=True,
    )
    
    zone_list = ", ".join([f"🏺 {z}" if z == "archaeology" else f"🎣 {z}" if z == "fishing" 
                           else f"🌿 {z}" if z == "botany" else f"♻️ {z}" if z == "scavenge" else z 
                           for z in relic.get("source_zones", [])])
    embed.add_field(
        name="Source",
        value=zone_list or "Unknown",
        inline=False,
    )
    
    embed.add_field(
        name="Description",
        value=f'"{relic["description"]}"',
        inline=False,
    )
    
    embed.set_footer(text="Collected relics are permanent in your archive")
    return embed


def museum_story_embed(chapter: int) -> discord.Embed:
    """Display a story chapter unlocked through museum progression."""
    from game.data import MUSEUM_STORY_CHAPTERS
    
    if chapter < 1 or chapter > len(MUSEUM_STORY_CHAPTERS):
        return discord.Embed(
            title="📜 STORY LOCKED",
            description="Complete more museum sets to unlock this chapter.",
            color=0x404040,
        )
    
    story_data = MUSEUM_STORY_CHAPTERS[chapter - 1]
    
    embed = discord.Embed(
        title=f"📜 MUSEUM STORY",
        description=f"**Chapter {chapter}: {story_data['title']}**",
        color=0x8B7355,
    )
    
    embed.add_field(
        name="Story",
        value=story_data["text"],
        inline=False,
    )
    
    embed.set_footer(text=f"Chapter {chapter} / 10")
    return embed


def museum_set_completion_embed(username: str, set_id: str) -> discord.Embed:
    """Celebration embed for completing a museum set."""
    from game.data import MUSEUM_SETS
    
    if set_id not in MUSEUM_SETS:
        return discord.Embed(title="❌ Set Not Found", color=0xFF0000)
    
    set_data = MUSEUM_SETS[set_id]
    
    embed = discord.Embed(
        title="🌟 SET COMPLETED! 🌟",
        description=f"{set_data['emoji']} {set_data['name']} is now complete!",
        color=0xFFD700,
    )
    
    # Format rewards
    rewards_text = []
    if "tickets" in set_data["rewards"]:
        rewards_text.append(f"🎟️ Dirty Tickets x{set_data['rewards']['tickets']}")
    if "coins" in set_data["rewards"]:
        rewards_text.append(f"💰 {set_data['rewards']['coins']:,} Coins")
    if "museum_box" in set_data["rewards"]:
        rewards_text.append(f"🎁 Museum Box")
    if "exclusive" in set_data["rewards"]:
        rewards_text.append(f"🧸 Exclusive Cosmetic Unlocked")
    if "title" in set_data["rewards"]:
        rewards_text.append(f"👑 Title: {set_data['rewards']['title']}")
    if "bonus" in set_data["rewards"]:
        rewards_text.append(f"✨ {set_data['rewards']['bonus']}")
    if set_data["rewards"].get("story_fragment"):
        rewards_text.append(f"📜 Story Fragment Unlocked")
    
    embed.add_field(
        name="Rewards",
        value="\n".join(rewards_text) or "Special recognition",
        inline=False,
    )
    
    embed.add_field(
        name="",
        value="💫 The Museum hums softly...\nSomething remembered you back.",
        inline=False,
    )
    
    embed.set_footer(text=f"Completion recognized on {datetime.utcnow().strftime('%Y-%m-%d')}")
    return embed

