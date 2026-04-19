from datetime import datetime

import discord

from game.data import HELP_TEXT, ITEMS, MIX_RECIPES, ZONES, get_live_events
from game.helpers import get_effect_remaining_text, get_item_card_line, get_rarity_fx_text
from game.leveling import xp_to_next_level
from game.rarities import RARITY_BADGES, RARITY_COLORS



def build_xp_bar(current_xp: int, level: int, size: int = 8) -> str:
    needed = xp_to_next_level(level)
    if needed <= 0:
        return "🟩" * size

    filled = round((current_xp / needed) * size)
    filled = max(0, min(size, filled))
    empty = size - filled
    return f"{'🟩' * filled}{'⬜' * empty} {current_xp}/{needed}"



def profile_embed(
    player: dict,
    inventory_count: int,
    recent_finds: list[str],
    active_effects: list[dict],
    equipment: list[dict],
    avatar_url: str,
) -> discord.Embed:
    current_zone = ZONES[player["current_zone_id"]]["name"]
    recent_text = "\n".join(f"• {item}" for item in recent_finds[-3:]) if recent_finds else "• Nothing yet"
    xp_bar = build_xp_bar(player["xp"], player["level"])

    embed = discord.Embed(
        title=f"{player['username']} — {player['current_title']}",
        description=(
            f"🫧 Tiny trash empire online.\n"
            f"📍 Currently scavenging in **{current_zone}**.\n"
            f"🌐 {' | '.join(event['name'] for event in get_live_events()) if get_live_events() else 'No live world event'}"
        ),
        color=0x2C2F33,
        timestamp=datetime.utcnow(),
    )
    embed.set_thumbnail(url=avatar_url)
    embed.set_author(name=player["username"], icon_url=avatar_url)

    embed.add_field(name="💰 Coins", value=str(player["coins"]), inline=True)
    embed.add_field(name="⭐ Level", value=str(player["level"]), inline=True)
    embed.add_field(name="🎒 Inventory", value=str(inventory_count), inline=True)
    embed.add_field(name="✨ XP Progress", value=xp_bar, inline=False)
    embed.add_field(name="🗑️ Total Dives", value=str(player["total_dives"]), inline=True)
    embed.add_field(name="🗺️ Active Zone", value=current_zone, inline=True)
    embed.add_field(name="👑 Title Aura", value=player["current_title"], inline=False)

    if active_effects:
        effect_lines = []
        for effect in active_effects[:4]:
            effect_lines.append(f"⏳ **{effect['label']}** — {get_effect_remaining_text(effect['expires_at'])}")
        embed.add_field(name="⏳ Active Effects", value="\n".join(effect_lines), inline=False)
    else:
        embed.add_field(name="⏳ Active Effects", value="• None live right now", inline=False)

    if equipment:
        equipment_lines = []
        for entry in equipment[:4]:
            item = ITEMS.get(entry["item_id"], {"name": entry["item_id"], "emoji": "✨", "equip_bonus": ""})
            bonus = item.get("equip_bonus", "No passive listed")
            equipment_lines.append(f"{item.get('emoji', '✨')} **{item['name']}** — {bonus}")
        embed.add_field(name="🧥 Equipped", value="\n".join(equipment_lines), inline=False)
    else:
        embed.add_field(name="🧥 Equipped", value="• Nothing equipped yet", inline=False)

    embed.add_field(name="🪄 Recent Finds", value=recent_text, inline=False)
    embed.set_footer(text="Live junk. Loud profile. Goblin hours.")
    return embed



def dive_processing_embed(zone_name: str, stage_text: str) -> discord.Embed:
    return discord.Embed(
        title="🗑️ Diving...",
        description=f"**{zone_name}**\n\n{stage_text}",
        color=0x5865F2,
    )



def dive_result_embed(
    player: dict,
    item_id: str,
    leveled_up: bool,
    reaction_text: str | None = None,
    event_text: str | None = None,
    bonus_text: str | None = None,
    unlocked_zone_names: list[str] | None = None,
    avatar_url: str | None = None,
) -> discord.Embed:
    item = ITEMS[item_id]
    zone = ZONES[player["current_zone_id"]]
    zone_name = zone["name"]
    rarity = item["rarity"]
    item_emoji = item.get("emoji", "✨")
    flavor = item.get("flavor", "A strange little treasure.")
    rarity_label = RARITY_BADGES.get(rarity, rarity)

    desc = (
        f"{item_emoji} **{item['name']}**\n"
        f"{rarity_label}\n"
        f"✦ {get_rarity_fx_text(rarity)}\n\n"
        f"💰 +{item['coins']} coins\n"
        f"⭐ +{item['xp']} XP\n"
        f"📍 Found in **{zone_name}**\n\n"
        f"*{flavor}*"
    )

    if event_text:
        desc += f"\n\n{event_text}"
    if bonus_text:
        desc += f"\n{bonus_text}"
    if reaction_text:
        desc += f"\n\n_{reaction_text}_"
    if leveled_up:
        desc += f"\n\n⬆️ You leveled up to **Level {player['level']}**!"
    if unlocked_zone_names:
        desc += f"\n🔓 New zones unlocked: **{', '.join(unlocked_zone_names)}**"

    embed = discord.Embed(
        title="✨ Dumpster Dive Result",
        description=desc,
        color=RARITY_COLORS.get(rarity, 0xFFFFFF),
    )
    if avatar_url:
        embed.set_author(name=player["username"], icon_url=avatar_url)
    if item.get("image", "").startswith("http"):
        embed.set_thumbnail(url=item["image"])
    embed.add_field(name="💰 Coins", value=str(player["coins"]), inline=True)
    embed.add_field(name="⭐ Level", value=str(player["level"]), inline=True)
    embed.add_field(name="🎒 Total Dives", value=str(player["total_dives"]), inline=True)
    embed.add_field(name="✨ XP Progress", value=build_xp_bar(player["xp"], player["level"]), inline=False)
    return embed



def inventory_embed(username: str, lines: list[str], page: int, total_pages: int) -> discord.Embed:
    embed = discord.Embed(
        title=f"🎒 {username}'s Loot Vault",
        description="\n\n".join(lines) if lines else "Your bag is empty. Time to dig up something cursed and cute.",
        color=0x5865F2,
    )
    embed.set_footer(text=f"Page {page + 1} / {total_pages} • Pick an item from the dropdown to use or equip it")
    return embed



def zone_embed(player: dict, zone_id: str, unlocked_zone_ids: set[str], zone_loot_lines: list[str], index: int, total: int) -> discord.Embed:
    zone = ZONES[zone_id]
    unlocked = zone_id in unlocked_zone_ids
    current = zone_id == player["current_zone_id"]
    status = "🟢 CURRENT" if current else ("✅ UNLOCKED" if unlocked else f"🔒 Unlocks at Level {zone['unlock_level']}")

    embed = discord.Embed(
        title=f"🗺️ Zone Selector ({index + 1}/{total})",
        description=(
            f"{zone['banner']}\n"
            f"{zone['unicode_style']}\n\n"
            f"{status}\n"
            f"*{zone['description']}*"
        ),
        color=0x57F287 if unlocked else 0xED4245,
    )
    embed.add_field(name="⚠ Danger", value=zone["danger"], inline=True)
    embed.add_field(name="🍀 Luck", value=zone["luck"], inline=True)
    embed.add_field(name="📍 Zone Name", value=zone["name"], inline=True)
    embed.add_field(name="🎁 Possible Finds", value="\n".join(zone_loot_lines) if zone_loot_lines else "???", inline=False)
    embed.set_footer(text="Use Set Active to make this your dive zone")
    return embed



def mix_lab_embed(inventory_map: dict[str, int], mix_lines: list[str]) -> discord.Embed:
    embed = discord.Embed(
        title="🧪 Goblin Mix Lab",
        description=(
            "Five filthy ways to cook garbage into glory:\n"
            "1. Fixed recipe forge\n"
            "2. Chaos mix\n"
            "3. Potion brewing\n"
            "4. Gear forging\n"
            "5. Overcharge ritual\n\n"
            "Available recipes right now:\n"
            f"{'\n'.join(mix_lines)}"
        ),
        color=0x9B59B6,
    )
    common_count = sum(qty for item_id, qty in inventory_map.items() if ITEMS.get(item_id, {}).get("rarity") == "Common")
    embed.add_field(name="🧱 Common Junk Count", value=str(common_count), inline=True)
    embed.add_field(name="🎒 Total Unique Items", value=str(len(inventory_map)), inline=True)
    embed.add_field(name="⚡ Lab Status", value="unstable but gorgeous", inline=True)
    return embed



def mix_result_embed(title: str, result_text: str) -> discord.Embed:
    return discord.Embed(title=title, description=result_text, color=0x9B59B6)



def events_embed() -> discord.Embed:
    live = get_live_events()
    embed = discord.Embed(
        title="✨ World Events",
        description="The world is messier on purpose.",
        color=0xEB459E,
    )
    if not live:
        embed.add_field(name="🌫️ Right Now", value="No special event is live.", inline=False)
    else:
        for event in live:
            embed.add_field(
                name=f"{event['emoji']} {event['name']}",
                value=f"{event['description']}\n*{event['profile_line']}*",
                inline=False,
            )
    embed.set_footer(text="Weekend events rotate. Seasonal events hit when the calendar gets weird.")
    return embed



def help_embed() -> discord.Embed:
    return discord.Embed(title="❓ How to Play", description=HELP_TEXT, color=0xFAA61A)
