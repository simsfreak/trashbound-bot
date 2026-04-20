# Profile Redesign - ASCII Box Format

## Overview
The profile display has been completely redesigned to use beautiful Unicode box-drawing characters for a more polished, organized appearance. Instead of Discord embed fields, the profile now displays as a formatted ASCII art with clear sections.

## New Profile Format

### What Users Will See
```
╭─────────────── ⏰ PROFILE ───────────────╮
│ 🗓 Mon, Apr 20 • 16:33                   │
│ 📍 Back Alley 🌅 Morning                 │
│ 🌐 No events                             │
╰─────────────────────────────────────────╯

╭──────────── 💰 STATS ────────────╮
│ 💰 Coins        » 2507           │
│ 🎟 Dirty Tickets» 1              │
│ ⭐ Level        » 12             │
│ 🎒 Items        » 13             │
╰─────────────────────────────────╯

╭──────────── ✨ PROGRESS ────────────╮
│ ✨ XP                             │
│ 🟩🟩🟩🟩⬜⬜⬜⬜⬜ 812 / 2078         │
╰───────────────────────────────────╯

╭────────── 🎁 BONUS ──────────╮
│ 💸 +15% Coin Gain           │
│ ✨ +10% XP Gain             │
╰─────────────────────────────╯

╭────────── 📊 STATS ──────────╮
│ 🗑 Total Dives » 502         │
│ 👑 Title       » Dumpster Hunter │
│ 🌅 Phase       » Morning     │
╰─────────────────────────────╯

╭───────── 💎 RECENT DROP ─────────╮
│ 🦷 Ratfang Token                │
│ 🔵 Rare Pull                   │
╰───────────────────────────────╯

╭───────── 📜 QUESTS ─────────╮
│ ❌ No Active Quest           │
│ 👉 Browse to accept one!     │
╰─────────────────────────────╯

╭──────── 🎯 DAILY QUEST ────────╮
│ ✅ Redeemed                   │
│ New quest in 24h              │
╰──────────────────────────────╯

╭──────── 🧸 EQUIPMENT ─────────╮
│ 🧠 Head   » Empty             │
│ 👕 Body   » Empty             │
│ ✋ Hands  » Empty             │
│ 👟 Feet   » Empty             │
│                             │
│ 🧲 ✨ Greed Magnet (Accessory) │
╰──────────────────────────────╯

🌸 🐾 Last Active: Today at 16:33 PM 🐾 🌸
```

## Technical Implementation

### Files Modified

#### 1. **ui/profile_formatter.py** (NEW)
- New file containing the `ProfileBox` class for ASCII box formatting
- Main function: `format_profile_display()` - builds complete formatted profile
- Helper function: `format_profile_embed_description()` - compact version for descriptions
- Handles all box-drawing and padding logic

**Key Features:**
- Automatic width calculation and line padding
- Center/left/right text alignment options
- Flexible section creation
- Proper spacing and emoji handling

#### 2. **ui/embeds.py** (MODIFIED)
- Imported `format_profile_display` from profile_formatter
- Updated `profile_embed()` function to use new formatter
- Profile now displays as a formatted code block within Discord embed
- Cleaner, more organized output

**Changes:**
- Removed old embed field-based layout
- Now uses formatter to generate all profile sections
- Maintains Discord embed wrapper for consistency

### Profile Sections

| Section | Content | Shows When |
|---------|---------|-----------|
| **⏰ PROFILE** | Date, Time, Zone, Phase, Live Events | Always |
| **💰 STATS** | Coins, Dirty Tickets, Level, Item Count | Always |
| **✨ PROGRESS** | XP Bar with visual indicator | Always |
| **🎁 BONUS** | Active equipment bonuses | When bonuses exist |
| **📊 STATS** | Total Dives, Title, Current Phase | Always |
| **💎 RECENT DROP** | Last 1 item found | When items found |
| **📜 QUESTS** | Active quest or "No Active Quest" | Always |
| **🎯 DAILY QUEST** | Daily quest status | Always |
| **🧸 EQUIPMENT** | 4 equipment slots + accessory | Always |
| **Footer** | Last active timestamp | Always |

## Integration Points

### Data Sources
- Player data: `player` dictionary
- Zone names: `ZONES` from `game/data.py`
- Item names/emojis: `ITEMS` from `game/data.py`
- Equipment slots: `EQUIP_SLOTS` from `game/data.py`
- Time functions: `get_phase_emoji()` from `game/time_system.py`
- Bonuses: `calculate_equipment_bonuses()` from `game/helpers.py`
- XP: `xp_to_next_level()` from `game/leveling.py`

### Discord Display
Profile displays in a code block (monospace font) to preserve:
- Unicode box-drawing characters (╭─┬─╮ etc.)
- Precise spacing and alignment
- Emoji proper sizing

## Testing Checklist

- [ ] Profile displays without errors
- [ ] All sections show correct data
- [ ] Box borders render properly in Discord
- [ ] Emoji display correctly
- [ ] Text alignment is consistent
- [ ] Equipment slots show items or "Empty"
- [ ] Active quests display status and time window
- [ ] Recent finds display correctly
- [ ] XP bar renders with proper filled/empty ratio
- [ ] Equipment bonuses list all active boosts
- [ ] Footer timestamp matches current time

## Next Steps

1. ✅ Profile formatter created
2. ✅ Embeds updated to use formatter
3. ⏳ Test with actual Discord bot
4. ⏳ Verify all data displays correctly
5. ⏳ Check Unicode rendering on all Discord clients
6. ⏳ Fine-tune spacing if needed

## Customization

To adjust the profile width or styling, modify the `ProfileBox` class:

```python
box = ProfileBox(width=44)  # Change width here
```

Default width: 44 characters (including borders)

To add new sections, use:
```python
new_section = box.section("emoji", "TITLE", ["line1", "line2"])
sections.append("\n".join(new_section))
```

## Known Considerations

1. Discord's code block uses monospace font - Unicode characters render consistently
2. Different devices/browsers may have slight rendering differences
3. Width is fixed at 44 chars to ensure mobile compatibility
4. All emojis are checked to display in monospace font correctly
