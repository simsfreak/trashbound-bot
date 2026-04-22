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


def zone_embed(player, zone_id, unlocked_zone_ids, zone_loot_lines, index, total):
    zone = ZONES[zone_id]
    unlocked = zone_id in unlocked_zone_ids
    current = zone_id == player["current_zone_id"]
    status = "🟢 CURRENT" if current else ("✅ UNLOCKED" if unlocked else f"🔒 Unlocks at Level {zone['unlock_level']}")

    embed = discord.Embed(
        title=f"🗺️ Zone Selector ({index + 1}/{total})",
        description=f"**{zone['name']}**\n{status}\n\n*{zone['description']}*",
        color=0x57F287 if unlocked else 0xED4245,
    )
    embed.add_field(name="🎁 Possible Finds", value="\n".join(zone_loot_lines) if zone_loot_lines else "???", inline=False)
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
