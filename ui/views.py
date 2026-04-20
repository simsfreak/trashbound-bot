import asyncio
import math
import discord
import random

PAWN_STORIES = [
    {
        "text": "A kid dragged in a screaming toaster yesterday. What do you do?",
        "choices": [
            {"label": "Sell it anyway", "liked": True},
            {"label": "Throw it back outside", "liked": False},
        ],
    },
    {
        "text": "Someone tried pawning me a boot with teeth. Your move?",
        "choices": [
            {"label": "Ask if it bites", "liked": True},
            {"label": "Pretend I never saw it", "liked": False},
        ],
    },
    {
        "text": "A rat brought me a ring and demanded store credit. Thoughts?",
        "choices": [
            {"label": "Respect the hustle", "liked": True},
            {"label": "Ban the rat", "liked": False},
        ],
    },
    {
        "text": "Guy swore this cracked radio predicts the future. What now?",
        "choices": [
            {"label": "Offer half price", "liked": True},
            {"label": "Walk away slowly", "liked": False},
        ],
    },
]

from db import queries
from game.data import EQUIP_SLOTS, ITEMS, ZONES, MUSEUM_COLLECTIONS
from game.helpers import (
    calculate_equipment_bonuses,
    determine_title,
    get_random_dive_midpoint,
    get_random_dive_reaction,
    get_random_dive_starter,
    get_recent_finds_from_inventory_rows,
    maybe_roll_dive_event,
    roll_dirty_draw_reward,
    roll_item_for_zone,
)
from game.leveling import apply_xp

SLOT_EMOJIS = {
    "head": "🧢",
    "body": "🧥",
    "hands": "🧤",
    "feet": "👟",
    "accessory": "💍",
}
from ui.embeds import (
    dive_processing_embed,
    dive_result_embed,
    events_embed,
    help_embed,
    inventory_embed,
    mix_result_embed,
    museum_home_embed,
    museum_collections_embed,
    admin_panel_embed,
    admin_messages_embed,
    admin_message_detail_embed,
    admin_grant_success_embed,
    profile_embed,
    zone_embed,
)
from ui.modals import ContactAdminModal

def get_random_pawn_story():
    return random.choice(PAWN_STORIES)


def roll_pawn_chat_reward(relationship: int, liked: bool):
    if not liked:
        return 0, 0

    ticket_chance = 0.05
    if relationship >= 5:
        ticket_chance = 0.10
    if relationship >= 10:
        ticket_chance = 0.15

    if random.random() < ticket_chance:
        return 0, 1

    coins = random.randint(40, 120)
    if relationship >= 5:
        coins += 25

    return coins, 0

def _safe_active_effects(user_id: int):
    if hasattr(queries, "get_active_effects"):
        return queries.get_active_effects(user_id)
    return []


def _safe_equipment(user_id: int):
    if hasattr(queries, "get_equipped_items"):
        return queries.get_equipped_items(user_id)
    return []


def _avatar_url(user: discord.abc.User) -> str | None:
    try:
        return user.display_avatar.url
    except Exception:
        return None


def build_profile_embed_for_user(user: discord.abc.User) -> discord.Embed:
    queries.ensure_player(user.id, user.name)
    player = queries.get_player(user.id)
    inventory = queries.get_inventory(user.id)
    recent_finds = get_recent_finds_from_inventory_rows(inventory)
    active_effects = _safe_active_effects(user.id)
    equipment = _safe_equipment(user.id)
    daily_quest = queries.get_daily_quest(user.id)

    quest_status = None
    if daily_quest:
        if daily_quest["redeemed"]:
            quest_status = "✅ Quest redeemed. New quest will arrive after 24 hours."
        elif daily_quest["completed"]:
            quest_status = "🎉 Ready to redeem! Open Quests to claim your reward."
        else:
            quest_status = f"{daily_quest['name']} — {daily_quest['progress']}/{daily_quest['target']}"

    return profile_embed(
        player=player,
        inventory_count=sum(qty for _, qty in inventory),
        recent_finds=recent_finds,
        active_effects=active_effects,
        equipment=equipment,
        dirty_tickets=player.get("dirty_tickets", 0),
        quest_status=quest_status,
        avatar_url=_avatar_url(user),
    )


async def show_profile(interaction: discord.Interaction, owner_id: int, is_admin: bool):
    embed = build_profile_embed_for_user(interaction.user)
    await interaction.response.edit_message(
        embed=embed,
        view=ProfileView(owner_id, is_admin),
        attachments=[],
    )


class InventoryView(discord.ui.View):
    def __init__(self, owner_id: int, is_admin: bool, items: list[tuple[str, int]], page: int = 0, page_size: int = 6):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.is_admin = is_admin
        self.items = items
        self.page = page
        self.page_size = page_size

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This inventory isn't yours.", ephemeral=True)
            return False
        return True

    @property
    def total_pages(self) -> int:
        return max(1, math.ceil(len(self.items) / self.page_size))

    def current_page_items(self) -> list[tuple[str, int]]:
        start = self.page * self.page_size
        end = start + self.page_size
        return self.items[start:end]

    def page_lines(self) -> list[str]:
        lines = []
        for item_id, qty in self.current_page_items():
            item = ITEMS.get(
                item_id,
                {"name": item_id, "rarity": "Unknown", "coins": 0, "emoji": "✨", "kind": "junk"},
            )
            kind = item.get("kind", "junk").title()
            extra = item.get("use_text") or item.get("equip_bonus") or item.get("flavor", "")
            lines.append(
                f"{item.get('emoji', '✨')} **{item['name']}**\n"
                f"{item['rarity']} • {kind} • Qty: {qty} • Sell: {item['coins']}\n"
                f"*{extra}*"
            )
        return lines

    @discord.ui.button(label="⬅️ Back", style=discord.ButtonStyle.secondary, row=0)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
        embed = inventory_embed(interaction.user.display_name, self.page_lines(), self.page, self.total_pages)
        await interaction.response.edit_message(embed=embed, view=self, attachments=[])

    @discord.ui.button(label="➡️ Next", style=discord.ButtonStyle.secondary, row=0)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page < self.total_pages - 1:
            self.page += 1
        embed = inventory_embed(interaction.user.display_name, self.page_lines(), self.page, self.total_pages)
        await interaction.response.edit_message(embed=embed, view=self, attachments=[])

    @discord.ui.button(label="🔄 Reload", style=discord.ButtonStyle.secondary, row=1)
    async def reload_inventory(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.items = queries.get_inventory(interaction.user.id)
        embed = inventory_embed(interaction.user.display_name, self.page_lines(), self.page, self.total_pages)
        await interaction.response.edit_message(embed=embed, view=self, attachments=[])

    @discord.ui.button(label="🏠 Back to Profile", style=discord.ButtonStyle.primary, row=1)
    async def back_to_profile(self, interaction: discord.Interaction, button: discord.ui.Button):
        await show_profile(interaction, self.owner_id, self.is_admin)


class EquipItemSelect(discord.ui.Select):
    def __init__(self, owner_id: int, is_admin: bool, options: list[discord.SelectOption]):
        super().__init__(placeholder="Equip Gear", min_values=1, max_values=1, options=options)
        self.owner_id = owner_id
        self.is_admin = is_admin
        self.row = 0

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This gear menu isn't yours.", ephemeral=True)
            return

        item_id = self.values[0]
        item = ITEMS.get(item_id)
        if not item or not item.get("equip_slot"):
            await interaction.response.send_message("Could not equip that item. Make sure it is valid gear.", ephemeral=True)
            return

        current_equipment = queries.get_equipped_items(self.owner_id)
        old_item_id = next(
            (entry["item_id"] for entry in current_equipment if entry.get("slot") == item["equip_slot"]),
            None,
        )

        if not queries.equip_item(self.owner_id, item_id):
            await interaction.response.send_message("Could not equip that item. Make sure it is in your inventory.", ephemeral=True)
            return

        queries.progress_daily_quest(self.owner_id, "equip_item", 1)

        change_title = "Gear Equipped"
        change_text = f"{item.get('emoji', '✨')} **{item['name']}** equipped to {item['equip_slot'].title()} slot."
        if old_item_id:
            old_item = ITEMS.get(old_item_id, {"name": old_item_id, "emoji": "✨"})
            change_text += f" Returned {old_item.get('emoji', '✨')} **{old_item['name']}** to inventory."

        embed = EquipmentView(self.owner_id, self.is_admin).build_embed(
            interaction,
            change_field=(change_title, change_text),
            change_slot=item["equip_slot"],
        )

        await interaction.response.edit_message(
            embed=embed,
            view=EquipmentView(self.owner_id, self.is_admin),
            attachments=[],
        )


class UnequipItemSelect(discord.ui.Select):
    def __init__(self, owner_id: int, is_admin: bool, options: list[discord.SelectOption]):
        super().__init__(placeholder="Unequip Gear", min_values=1, max_values=1, options=options)
        self.owner_id = owner_id
        self.is_admin = is_admin
        self.row = 1

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This gear menu isn't yours.", ephemeral=True)
            return

        slot = self.values[0]
        current_equipment = queries.get_equipped_items(self.owner_id)
        old_item_id = next(
            (entry["item_id"] for entry in current_equipment if entry.get("slot") == slot),
            None,
        )
        if not old_item_id or not queries.unequip_item(self.owner_id, slot):
            await interaction.response.send_message("Could not unequip that slot right now.", ephemeral=True)
            return

        old_item = ITEMS.get(old_item_id, {"name": old_item_id, "emoji": "✨"})
        change_title = "Gear Unequipped"
        change_text = f"{old_item.get('emoji', '✨')} **{old_item['name']}** unequipped from {slot.title()} and returned to inventory."
        embed = EquipmentView(self.owner_id, self.is_admin).build_embed(
            interaction,
            change_field=(change_title, change_text),
            change_slot=slot,
        )

        await interaction.response.edit_message(
            embed=embed,
            view=EquipmentView(self.owner_id, self.is_admin),
            attachments=[],
        )


class EquipmentView(discord.ui.View):
    def __init__(self, owner_id: int, is_admin: bool):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.is_admin = is_admin

        inventory_map = queries.get_inventory_map(owner_id)
        select_options = []

        for item_id, qty in inventory_map.items():
            item = ITEMS.get(item_id)
            if not item or not item.get("equip_slot"):
                continue

            slot = item["equip_slot"].title()
            label = f"{item.get('emoji', '✨')} {item['name']}"
            description = f"{slot} • Qty: {qty} • {item['rarity']}"
            select_options.append(discord.SelectOption(label=label, description=description, value=item_id))

        if select_options:
            self.add_item(EquipItemSelect(owner_id, is_admin, select_options))

        current_equipment = queries.get_equipped_items(owner_id)
        unequip_options = []
        for entry in current_equipment:
            slot = entry.get("slot")
            item = ITEMS.get(entry.get("item_id"), {"name": entry.get("item_id"), "emoji": "✨"})
            if slot:
                unequip_options.append(
                    discord.SelectOption(
                        label=f"{item.get('emoji', '✨')} {item['name']}",
                        description=f"Unequip from {slot.title()}",
                        value=slot,
                    )
                )

        if unequip_options:
            self.add_item(UnequipItemSelect(owner_id, is_admin, unequip_options))

        self.add_item(EquipmentBackButton(row=2))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This gear menu isn't yours.", ephemeral=True)
            return False
        return True

    def build_embed(
        self,
        interaction: discord.Interaction,
        change_field: tuple[str, str] | None = None,
        change_slot: str | None = None,
    ) -> discord.Embed:
        player = queries.get_player(self.owner_id)
        current_equipment = queries.get_equipped_items(self.owner_id)
        inventory_map = queries.get_inventory_map(self.owner_id)

        slot_map = {
            entry.get("slot", ""): entry.get("item_id")
            for entry in current_equipment
            if isinstance(entry, dict) and entry.get("slot")
        }
        gear_lines = []
        for slot in EQUIP_SLOTS:
            item_id = slot_map.get(slot)
            slot_emoji = SLOT_EMOJIS.get(slot, "▫️")
            badge = "⭐ " if slot == change_slot else ""
            if item_id:
                item = ITEMS.get(item_id, {"name": item_id, "emoji": "✨"})
                gear_lines.append(f"{badge}{slot_emoji} **{slot.title()}** — {item.get('emoji', '✨')} {item['name']}")
            else:
                gear_lines.append(f"{badge}{slot_emoji} **{slot.title()}** — Empty")

        available_lines = []
        for item_id, qty in inventory_map.items():
            item = ITEMS.get(item_id)
            if item and item.get("equip_slot"):
                available_lines.append(f"{item.get('emoji', '✨')} **{item['name']}** x{qty} — {item['equip_slot'].title()}")
        if not available_lines:
            available_lines = ["No equipable gear in inventory."]

        embed = discord.Embed(
            title="🛠️ Gear Locker",
            description=(
                f"✨ **Equipped Gear**\n" + "\n".join(gear_lines[:6]) + "\n\n"
                f"🎒 **Inventory Gear**\n" + "\n".join(available_lines[:10])
            ),
            color=0x9B59B6,
        )

        return embed


class EquipmentBackButton(discord.ui.Button):
    def __init__(self, row: int = 1):
        super().__init__(label="🏠 Back to Profile", style=discord.ButtonStyle.primary, row=row)

    async def callback(self, interaction: discord.Interaction):
        if not isinstance(self.view, EquipmentView):
            return
        await show_profile(interaction, self.view.owner_id, self.view.is_admin)

# ==================== QUEST SESSION STORAGE ====================
# This stores quest batches per user for pagination
# Structure: {user_id: {"quests": [...], "index": 0}}
_ACTIVE_QUEST_SESSIONS = {}


class GeneratedQuestView(discord.ui.View):
    """
    Paginated quest view for the quest generation system.
    - Generates 3-5 quests on first load
    - Allows cycling through them with [🎲 Next]
    - Player can [✅ Accept] a quest to lock it in
    - Emojis and kawaii style throughout
    """
    def __init__(self, owner_id: int, is_admin: bool):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.is_admin = is_admin
        self.current_quest_index = 0
        self.quests = []

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This quest panel isn't yours. 🚫", ephemeral=True)
            return False
        return True

    def _get_zone_emoji(self, zone_id: str) -> str:
        """Get cute emoji for zone"""
        zone_emojis = {
            "back_alley": "🗑️",
            "apartment_bins": "🏢",
            "restaurant_dumpster": "🍔",
            "mall_rear_lot": "🛍️",
        }
        return zone_emojis.get(zone_id, "📍")

    def _get_time_emoji(self, time_str: str) -> str:
        """Get emoji for time of day"""
        time_emojis = {
            "morning": "🌅",
            "evening": "🌆",
            "night": "🌙",
        }
        return time_emojis.get(time_str, "⏰")

    def _build_progress_bar(self, current: int, target: int, length: int = 10) -> str:
        """Build a cute progress bar"""
        filled = int((current / target) * length) if target > 0 else 0
        filled = min(filled, length)
        empty = length - filled
        return "[" + "█" * filled + "░" * empty + "]"

    def _generate_quest_batch(self, count: int = 5) -> list:
        """Generate a batch of randomized quests"""
        from game.quest_generator import generate_quest
        
        quests = []
        for _ in range(count):
            try:
                # generate_quest handles all randomization internally
                quest = generate_quest()
                quests.append(quest)
            except Exception as e:
                # Skip if generation fails, fallback will handle it
                pass
        
        return quests if quests else self._generate_simple_quests(count)

    def _generate_simple_quests(self, count: int = 5) -> list:
        """Fallback: Generate simple quests from templates"""
        from game.data import DAILY_QUEST_TEMPLATES, ZONES
        
        quests = []
        zone_ids = list(ZONES.keys())
        times = ["morning", "evening", "night"]
        
        for i in range(min(count, len(DAILY_QUEST_TEMPLATES))):
            base = DAILY_QUEST_TEMPLATES[i]
            zone_id = random.choice(zone_ids)
            zone = ZONES[zone_id]
            time_of_day = random.choice(times)
            difficulty = random.randint(1, 5)
            
            # Build hearts display
            hearts = "♥" * difficulty + "♡" * (5 - difficulty)
            
            # Adjust reward based on difficulty
            base_coins = base.get("reward_coins", 150)
            multiplier = 0.5 + (difficulty * 0.3)
            reward_coins = int(base_coins * multiplier)
            
            quest = {
                "quest_id": f"quest_{self.owner_id}_{i}_{random.randint(1000, 9999)}",
                "template_id": base.get("quest_key", ""),
                "name": base.get("name", "Mystery Quest"),
                "description": base.get("description", "Complete this quest."),
                "objective_type": base.get("quest_type", "dive_count"),
                "zone_id": zone_id,
                "zone_name": zone.get("name", zone_id),
                "time": time_of_day,
                "difficulty": difficulty,
                "hearts": hearts,
                "flavor_text": base.get("flavor_text", "A quest awaits."),
                "progress": 0,
                "target": base.get("target", 1),
                "reward_coins": reward_coins,
                "reward_tickets": 1 if difficulty >= 3 else 0,
                "is_active": False,
                "is_completed": False,
                "is_redeemed": False,
            }
            quests.append(quest)
        
        return quests

    def _load_quests(self):
        """Load or generate quests for this user"""
        if self.owner_id in _ACTIVE_QUEST_SESSIONS:
            session = _ACTIVE_QUEST_SESSIONS[self.owner_id]
            self.quests = session.get("quests", [])
            self.current_quest_index = session.get("index", 0)
        
        if not self.quests:
            self.quests = self._generate_quest_batch(5)
            self.current_quest_index = 0
            _ACTIVE_QUEST_SESSIONS[self.owner_id] = {
                "quests": self.quests,
                "index": 0
            }

    def _save_session(self):
        """Save current session state"""
        _ACTIVE_QUEST_SESSIONS[self.owner_id] = {
            "quests": self.quests,
            "index": self.current_quest_index
        }

    def _get_current_quest(self) -> dict:
        """Get the quest at current index"""
        self._load_quests()
        if 0 <= self.current_quest_index < len(self.quests):
            return self.quests[self.current_quest_index]
        return None

    def build_embed(self) -> discord.Embed:
        """Build the quest display embed"""
        quest = self._get_current_quest()
        
        if not quest:
            return discord.Embed(
                title="🎯 Quests",
                description="No quests available right now. Check back soon! 🔄",
                color=0xEB459E
            )
        
        zone_emoji = self._get_zone_emoji(quest.get("zone_id", "back_alley"))
        time_emoji = self._get_time_emoji(quest.get("time", "morning"))
        hearts = quest.get("hearts", "♥♡♡♡♡")
        
        description = f"**{quest['name']}**\n_{quest.get('flavor_text', 'A quest awaits.')}_"
        
        embed = discord.Embed(
            title="✨ Quest Available",
            description=description,
            color=0xEB459E,
        )
        
        # Zone, time, difficulty row
        embed.add_field(name=f"{zone_emoji} Zone", value=quest.get("zone_name", "Unknown"), inline=True)
        embed.add_field(name=f"{time_emoji} Time", value=quest.get("time", "morning").capitalize(), inline=True)
        embed.add_field(name="⚔️ Difficulty", value=hearts, inline=True)
        
        # Task
        embed.add_field(name="📋 Task", value=quest['description'], inline=False)
        
        # Rewards
        reward_text = []
        if quest.get("reward_coins"):
            reward_text.append(f"{quest['reward_coins']} coins")
        if quest.get("reward_tickets"):
            reward_text.append(f"{quest['reward_tickets']} Ticket(s)")
        
        embed.add_field(
            name="💰 Rewards",
            value=", ".join(reward_text) if reward_text else "None",
            inline=False
        )
        
        # Quest counter
        embed.set_footer(text=f"Quest {self.current_quest_index + 1}/{len(self.quests)} • Click [🎲 Next] to see more")
        
        return embed

    @discord.ui.button(label="🎲 Next", style=discord.ButtonStyle.secondary, row=0)
    async def next_quest_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cycle to the next quest in the batch"""
        self._load_quests()
        self.current_quest_index = (self.current_quest_index + 1) % len(self.quests)
        self._save_session()
        
        embed = self.build_embed()
        await interaction.response.edit_message(embed=embed, view=self, attachments=[])

    @discord.ui.button(label="✅ Accept Quest", style=discord.ButtonStyle.primary, row=0)
    async def accept_quest_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Accept the currently displayed quest"""
        quest = self._get_current_quest()
        
        if not quest:
            embed = discord.Embed(
                title="❌ Error",
                description="No quest to accept.",
                color=0xED4245,
            )
            await interaction.response.edit_message(embed=embed, view=self, attachments=[])
            return
        
        # Store this quest as the active one
        quest["is_active"] = True
        
        embed = discord.Embed(
            title="✅ Quest Accepted!",
            description=f"You've accepted **{quest['name']}**\n\n_{quest['description']}_\n\n💰 **Reward:** {quest['reward_coins']} coins",
            color=0x57F287,
        )
        
        # Clear the session since they picked a quest
        if self.owner_id in _ACTIVE_QUEST_SESSIONS:
            del _ACTIVE_QUEST_SESSIONS[self.owner_id]
        
        await interaction.response.edit_message(embed=embed, view=self, attachments=[])

    @discord.ui.button(label="🔄 Refresh", style=discord.ButtonStyle.secondary, row=0)
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Regenerate a completely new batch of quests"""
        # Clear old quests
        if self.owner_id in _ACTIVE_QUEST_SESSIONS:
            del _ACTIVE_QUEST_SESSIONS[self.owner_id]
        
        self.quests = []
        self.current_quest_index = 0
        self._load_quests()
        
        embed = self.build_embed()
        await interaction.response.edit_message(embed=embed, view=self, attachments=[])

    @discord.ui.button(label="🏠 Back", style=discord.ButtonStyle.secondary, row=1)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Return to profile"""
        await show_profile(interaction, self.owner_id, self.is_admin)


class QuestView(discord.ui.View):
    def __init__(self, owner_id: int, is_admin: bool):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.is_admin = is_admin

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This quest panel isn't yours.", ephemeral=True)
            return False
        return True

    def _get_difficulty_hearts(self, difficulty: int) -> str:
        """Convert difficulty (1-5) to heart system (♥♥♥♡♡)"""
        filled = min(max(difficulty, 1), 5)
        empty = 5 - filled
        return "♥" * filled + "♡" * empty

    def _get_zone_emoji(self, zone_id: str) -> str:
        """Get emoji for zone"""
        zone_emojis = {
            "back_alley": "🗑️",
            "apartment_bins": "🏢",
            "restaurant_dumpster": "🍔",
            "mall_rear_lot": "🛍️",
        }
        return zone_emojis.get(zone_id, "📍")

    def _get_time_emoji(self, time_str: str) -> str:
        """Get emoji for time of day"""
        time_emojis = {
            "morning": "🌅",
            "evening": "🌆",
            "night": "🌙",
        }
        return time_emojis.get(time_str, "⏰")

    def build_embed(self) -> discord.Embed:
        quest = queries.get_daily_quest(self.owner_id)
        if not quest:
            return discord.Embed(title="🎯 Daily Quest", description="No active quest right now.", color=0xEB459E)

        zone_id = quest.get("zone_id", "back_alley")
        zone = ZONES.get(zone_id, {})
        zone_name = zone.get("name", zone_id)
        time_of_day = quest.get("time", "morning")
        difficulty = quest.get("difficulty", 1)
        flavor_text = quest.get("flavor_text", "A quest awaits.")

        status = "Completed" if quest["completed"] else "In progress"
        if quest["redeemed"]:
            status = "Redeemed"

        reward_parts = []
        if quest["reward_coins"]:
            reward_parts.append(f"{quest['reward_coins']} coins")
        if quest["reward_tickets"]:
            reward_parts.append(f"{quest['reward_tickets']} Dirty Ticket(s)")

        zone_emoji = self._get_zone_emoji(zone_id)
        time_emoji = self._get_time_emoji(time_of_day)
        difficulty_hearts = self._get_difficulty_hearts(difficulty)

        embed = discord.Embed(
            title="🎯 Daily Quest",
            description=f"**{quest['name']}**\n_{flavor_text}_",
            color=0xEB459E,
        )
        # Add zone and time info
        embed.add_field(name=f"{zone_emoji} Zone", value=zone_name, inline=True)
        embed.add_field(name=f"{time_emoji} Time", value=time_of_day.capitalize(), inline=True)
        embed.add_field(name=f"⚔️ Difficulty", value=difficulty_hearts, inline=True)
        
        # Add main task
        embed.add_field(name="Task", value=quest['description'], inline=False)
        
        # Add progress
        progress_bar = self._build_progress_bar(quest['progress'], quest['target'])
        embed.add_field(name="Progress", value=f"{progress_bar} {quest['progress']}/{quest['target']}", inline=False)
        
        # Add reward
        embed.add_field(name="💰 Reward", value=", ".join(reward_parts) or "None", inline=False)
        
        # Add status
        status_emoji = "✅" if quest["redeemed"] else "🎉" if quest["completed"] else "⏳"
        embed.add_field(name=f"{status_emoji} Status", value=status, inline=False)
        
        embed.set_footer(text=f"Expires: {quest['expires_at'].strftime('%Y-%m-%d %H:%M UTC')}")
        return embed

    def _build_progress_bar(self, current: int, target: int, length: int = 10) -> str:
        """Build a simple progress bar"""
        filled = int((current / target) * length) if target > 0 else 0
        filled = min(filled, length)
        empty = length - filled
        return "[" + "█" * filled + "░" * empty + "]"

    @discord.ui.button(label="Accept Quest", style=discord.ButtonStyle.primary, row=0)
    async def accept_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        quest = queries.get_daily_quest(self.owner_id)
        if not quest:
            embed = discord.Embed(
                title="🎯 Daily Quest",
                description="No active quest to accept.",
                color=0xED4245,
            )
            await interaction.response.edit_message(embed=embed, view=self, attachments=[])
            return

        # Quest is automatically accepted when displayed, just confirm
        embed = discord.Embed(
            title="✅ Quest Accepted",
            description=f"You've accepted: **{quest['name']}**\n\n{quest['description']}",
            color=0x57F287,
        )
        await interaction.response.edit_message(embed=embed, view=self, attachments=[])

    @discord.ui.button(label="Redeem", style=discord.ButtonStyle.success, row=0)
    async def redeem_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        quest = queries.get_daily_quest(self.owner_id)
        if not quest or not quest["completed"] or quest["redeemed"]:
            embed = discord.Embed(
                title="🎯 Daily Quest",
                description="That quest is not ready to redeem yet.",
                color=0xED4245,
            )
            await interaction.response.edit_message(embed=embed, view=self, attachments=[])
            return

        if queries.redeem_daily_quest(self.owner_id):
            reward_text = []
            if quest["reward_coins"]:
                reward_text.append(f"{quest['reward_coins']} coins")
            if quest["reward_tickets"]:
                reward_text.append(f"{quest['reward_tickets']} Dirty Ticket(s)")
            embed = discord.Embed(
                title="🎉 Quest Redeemed",
                description=(
                    f"You claimed {', '.join(reward_text)}."
                ),
                color=0x57F287,
            )
        else:
            embed = discord.Embed(
                title="🎯 Daily Quest",
                description="Unable to redeem that quest right now.",
                color=0xED4245,
            )
        await interaction.response.edit_message(embed=embed, view=self, attachments=[])

    @discord.ui.button(label="🏠 Back to Profile", style=discord.ButtonStyle.secondary, row=1)
    async def back_to_profile(self, interaction: discord.Interaction, button: discord.ui.Button):
        await show_profile(interaction, self.owner_id, self.is_admin)


class DirtyDrawView(discord.ui.View):
    def __init__(self, owner_id: int, is_admin: bool):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.is_admin = is_admin

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This Dirty Draw isn't yours.", ephemeral=True)
            return False
        return True

    def build_embed(self) -> discord.Embed:
        player = queries.get_player(self.owner_id)
        return discord.Embed(
            title="🎟 Dirty Draw",
            description=(
                f"Dirty Tickets: **{player.get('dirty_tickets', 0)}**\n\n"
                "Use your tickets to pull strange, useful loot from the muck."
            ),
            color=0xEB459E,
        )

    async def _draw(self, interaction: discord.Interaction, ticket_count: int):
        player = queries.get_player(interaction.user.id)
        if player.get("dirty_tickets", 0) < ticket_count:
            embed = discord.Embed(
                title="🎟 Not enough Dirty Tickets",
                description=(
                    f"You need {ticket_count} Dirty Ticket(s), but only have {player.get('dirty_tickets', 0)}."
                ),
                color=0xED4245,
            )
            await interaction.response.edit_message(embed=embed, view=self, attachments=[])
            return

        if not queries.use_dirty_tickets(interaction.user.id, ticket_count):
            embed = discord.Embed(
                title="🎟 Draw Failed",
                description="Unable to spend tickets right now. Try again later.",
                color=0xED4245,
            )
            await interaction.response.edit_message(embed=embed, view=self, attachments=[])
            return

        rewards = roll_dirty_draw_reward(ticket_count)
        reward_lines = []
        for item_id, item in rewards:
            if item:
                queries.add_item_to_inventory(interaction.user.id, item_id, 1)
                reward_lines.append(f"{item.get('emoji', '✨')} **{item['name']}**")
            else:
                reward_lines.append(f"✨ Unknown reward: {item_id}")

        queries.progress_daily_quest(interaction.user.id, "dive_count", 1)

        updated_player = queries.get_player(interaction.user.id)
        embed = discord.Embed(
            title="🎟 Dirty Draw Results",
            description=(
                "You tore open the muck and found:\n"
                + "\n".join(reward_lines)
                + f"\n\nDirty Tickets left: **{updated_player.get('dirty_tickets', 0)}**"
            ),
            color=0x57F287,
        )
        await interaction.response.edit_message(embed=embed, view=self, attachments=[])

    @discord.ui.button(label="Use x1", style=discord.ButtonStyle.success, row=0)
    async def use_one(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._draw(interaction, 1)

    @discord.ui.button(label="Use x5", style=discord.ButtonStyle.success, row=1)
    async def use_five(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._draw(interaction, 5)

    @discord.ui.button(label="🏠 Back to Profile", style=discord.ButtonStyle.secondary, row=2)
    async def back_to_profile(self, interaction: discord.Interaction, button: discord.ui.Button):
        await show_profile(interaction, self.owner_id, self.is_admin)


class ZoneSelectorView(discord.ui.View):
    def __init__(self, owner_id: int, is_admin: bool, zone_ids: list[str], index: int = 0):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.is_admin = is_admin
        self.zone_ids = zone_ids
        self.index = index

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("That map isn't yours.", ephemeral=True)
            return False
        return True

    def current_zone_id(self) -> str:
        return self.zone_ids[self.index]

    def build_embed(self, interaction: discord.Interaction) -> discord.Embed:
        player = queries.get_player(interaction.user.id)
        unlocked_zone_ids = set(queries.get_unlocked_zone_ids(interaction.user.id))
        zone_id = self.current_zone_id()

        loot_lines = []
        for item_id, item in ITEMS.items():
            if zone_id in item.get("zone_ids", []):
                loot_lines.append(f"{item.get('emoji', '✨')} {item['name']} • {item['rarity']}")

        return zone_embed(
            player=player,
            zone_id=zone_id,
            unlocked_zone_ids=unlocked_zone_ids,
            zone_loot_lines=loot_lines[:6],
            index=self.index,
            total=len(self.zone_ids),
        )

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.secondary, row=0)
    async def previous_zone(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index = (self.index - 1) % len(self.zone_ids)
        await interaction.response.edit_message(embed=self.build_embed(interaction), view=self, attachments=[])

    @discord.ui.button(label="✅ Set Active", style=discord.ButtonStyle.success, row=0)
    async def set_active_zone(self, interaction: discord.Interaction, button: discord.ui.Button):
        zone_id = self.current_zone_id()
        unlocked = set(queries.get_unlocked_zone_ids(interaction.user.id))

        if zone_id not in unlocked:
            await interaction.response.send_message("That zone is still locked. Keep grinding.", ephemeral=True)
            return

        queries.set_current_zone(interaction.user.id, zone_id)
        await interaction.response.edit_message(embed=self.build_embed(interaction), view=self, attachments=[])

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.secondary, row=0)
    async def next_zone(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index = (self.index + 1) % len(self.zone_ids)
        await interaction.response.edit_message(embed=self.build_embed(interaction), view=self, attachments=[])

    @discord.ui.button(label="🏠 Back", style=discord.ButtonStyle.primary, row=1)
    async def back_to_profile(self, interaction: discord.Interaction, button: discord.ui.Button):
        await show_profile(interaction, self.owner_id, self.is_admin)


class MuseumHomeView(discord.ui.View):
    def __init__(self, owner_id: int, is_admin: bool):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.is_admin = is_admin

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This museum page isn't yours.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="📖 All Collections", style=discord.ButtonStyle.primary, row=0)
    async def collections_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        from ui.embeds import museum_collections_embed
        
        discovered = queries.get_discovered_item_ids(interaction.user.id)
        completed_collections = queries.get_completed_collections(interaction.user.id)
        
        embed = museum_collections_embed(MUSEUM_COLLECTIONS, discovered, completed_collections)
        await interaction.response.edit_message(
            embed=embed,
            view=self,
            attachments=[],
        )

    @discord.ui.button(label="🏠 Back to Profile", style=discord.ButtonStyle.primary, row=0)
    async def back_to_profile(self, interaction: discord.Interaction, button: discord.ui.Button):
        await show_profile(interaction, self.owner_id, self.is_admin)

class PawnChatChoiceView(discord.ui.View):
    def __init__(self, owner_id: int, is_admin: bool, story: dict):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.is_admin = is_admin
        self.story = story

        for idx, choice in enumerate(story["choices"]):
            self.add_item(PawnChatChoiceButton(choice["label"], choice["liked"], row=0))

        self.add_item(PawnChatBackButton(row=1))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This conversation isn't yours.", ephemeral=True)
            return False
        return True

class PawnChatChoiceButton(discord.ui.Button):
    def __init__(self, label: str, liked: bool, row: int = 0):
        style = discord.ButtonStyle.success if liked else discord.ButtonStyle.secondary
        super().__init__(label=label, style=style, row=row)
        self.liked = liked

    async def callback(self, interaction: discord.Interaction):
        if not isinstance(self.view, PawnChatChoiceView):
            return

        player = queries.get_player(interaction.user.id)
        relationship = int(player.get("pawn_relationship", 0))

        coins_reward, ticket_reward = roll_pawn_chat_reward(relationship, self.liked)

        if self.liked:
            owner_text = random.choice([
                "Heh. You get how this town works.",
                "Not bad. You might survive around here.",
                "Now that's the kind of answer I respect.",
            ])
            relationship_delta = 1
        else:
            owner_text = random.choice([
                "Nah. Soft answer.",
                "You'd get eaten alive doing that.",
                "Wrong instinct. Cute, though.",
            ])
            relationship_delta = 0
            coins_reward = 0
            ticket_reward = 0
            
        queries.update_pawn_chat(
            interaction.user.id,
            relationship_delta=relationship_delta,
            coins_delta=coins_reward,
            dirty_ticket_delta=ticket_reward,
        )
        reward_lines = [owner_text]
        if coins_reward:
            reward_lines.append(f"💰 Under the table: **+{coins_reward} coins**")
        if ticket_reward:
            reward_lines.append(f"🎟 Under the table: **+{ticket_reward} Dirty Ticket**")
        if not coins_reward and not ticket_reward:
            reward_lines.append("You got attitude. No bonus.")

        updated_player = queries.get_player(interaction.user.id)
        reward_lines.append(f"🤝 Pawn Relationship: **{updated_player.get('pawn_relationship', 0)}**")

        embed = discord.Embed(
            title="💬 Pawn Owner Chat",
            description="\n\n".join(reward_lines),
            color=0x8B5E3C,
        )

        await interaction.response.edit_message(
            embed=embed,
            view=ProfileView(self.view.owner_id, self.view.is_admin),
            attachments=[],
        )


class PawnChatBackButton(discord.ui.Button):
    def __init__(self, row: int = 1):
        super().__init__(label="🏠 Back to Profile", style=discord.ButtonStyle.primary, row=row)

    async def callback(self, interaction: discord.Interaction):
        if not isinstance(self.view, PawnChatChoiceView):
            return
        await show_profile(interaction, self.view.owner_id, self.view.is_admin)

class PawnShopView(discord.ui.View):
    def __init__(self, owner_id: int, is_admin: bool):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.is_admin = is_admin

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("Not your shop session.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="💱 Exchange Loot", style=discord.ButtonStyle.success, row=0)
    async def exchange_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        inventory = queries.get_inventory(interaction.user.id)
        pawnable_items = []
        total_coins = 0

        for item_id, quantity in inventory:
            item = ITEMS.get(item_id)
            if not item or not item.get("pawnable", False):
                continue

            item_value = int(item.get("coins", 0)) * quantity
            if item_value <= 0:
                continue

            pawnable_items.append((item_id, quantity, item_value))
            total_coins += item_value

        if total_coins <= 0:
            embed = mix_result_embed(
                "💱 Exchange Loot",
                "You’ve got nothing good enough to pawn right now. Come back with some pawnable junk.",
            )
            await interaction.response.edit_message(
                embed=embed,
                view=PawnShopView(self.owner_id, self.is_admin),
                attachments=[],
            )
            return

        total_quantity = sum(quantity for _, quantity, _ in pawnable_items)
        exchanged_names = [f'{ITEMS[item_id]["name"]} x{quantity}' for item_id, quantity, _ in pawnable_items]

        for item_id, quantity, _ in pawnable_items:
            queries.remove_item_from_inventory(interaction.user.id, item_id, quantity)

        queries.add_player_coins(interaction.user.id, total_coins)
        if total_quantity > 0:
            queries.progress_daily_quest(interaction.user.id, "pawn_count", total_quantity)

        description_lines = [
            f"Pawned **{total_quantity}** items for **{total_coins} coins**.",
        ]
        if exchanged_names:
            description_lines.append("Exchanged:")
            description_lines.extend(exchanged_names[:6])
            if len(exchanged_names) > 6:
                description_lines.append("…and more pawnable junk.")

        embed = discord.Embed(
            title="💱 Exchange Loot",
            description="\n".join(description_lines),
            color=0xFFD700,
        )

        await interaction.response.edit_message(
            embed=embed,
            view=PawnShopView(self.owner_id, self.is_admin),
            attachments=[],
        )

    @discord.ui.button(label="🎟 Buy Tickets", style=discord.ButtonStyle.primary, row=0)
    async def buy_tickets_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = TicketShopView(self.owner_id, self.is_admin)
        await interaction.response.edit_message(
            embed=view.build_embed(),
            view=view,
            attachments=[],
        )

    @discord.ui.button(label="💬 Chat with Owner", style=discord.ButtonStyle.secondary, row=1)
    async def chat_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not queries.can_chat_with_pawn_owner(interaction.user.id):
            await interaction.response.send_message(
                "The pawn owner waves you off. Come back tomorrow.",
                ephemeral=True,
            )
            return

        story = get_random_pawn_story()

        embed = discord.Embed(
            title="💬 Pawn Owner",
            description=(
                f"**{interaction.user.display_name}**, listen up.\n\n"
                f"{story['text']}"
            ),
            color=0x8B5E3C,
        )

        await interaction.response.edit_message(
            embed=embed,
            view=PawnChatChoiceView(self.owner_id, self.is_admin, story),
            attachments=[],
        )

    @discord.ui.button(label="🏠 Back", style=discord.ButtonStyle.secondary, row=2)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await show_profile(interaction, self.owner_id, self.is_admin)


class TicketShopView(discord.ui.View):
    TICKET_PACKS = [
        (1, 1000),
        (5, 4500),
        (10, 8500),
    ]

    def __init__(self, owner_id: int, is_admin: bool):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.is_admin = is_admin

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This ticket shop isn't yours.", ephemeral=True)
            return False
        return True

    def build_embed(self) -> discord.Embed:
        player = queries.get_player(self.owner_id)
        ticket_lines = [
            f"Coins: **{player['coins']}**",
            f"Dirty Tickets: **{player['dirty_tickets']}**",
            "",
            "Ticket Packs:",
            "• Dirty Ticket x1 = 1000 coins",
            "• Dirty Ticket x5 = 4500 coins",
            "• Dirty Ticket x10 = 8500 coins",
        ]

        return discord.Embed(
            title="🎟 Ticket Shop",
            description="\n".join(ticket_lines),
            color=0x8B5E3C,
        )

    async def _purchase(self, interaction: discord.Interaction, ticket_count: int, coins_cost: int):
        player = queries.get_player(interaction.user.id)
        if player['coins'] < coins_cost:
            embed = discord.Embed(
                title="🎟 Not enough coins",
                description=(
                    f"You need **{coins_cost}** coins for that pack, but only have **{player['coins']}**.",
                ),
                color=0xED4245,
            )
            await interaction.response.edit_message(
                embed=embed,
                view=self,
                attachments=[],
            )
            return

        success = queries.buy_dirty_tickets(interaction.user.id, coins_cost, ticket_count)
        if not success:
            embed = discord.Embed(
                title="🎟 Not enough coins",
                description=(
                    f"You need **{coins_cost}** coins for that pack, but only have **{player['coins']}**.",
                ),
                color=0xED4245,
            )
            await interaction.response.edit_message(
                embed=embed,
                view=self,
                attachments=[],
            )
            return

        updated_player = queries.get_player(interaction.user.id)
        embed = discord.Embed(
            title="🎟 Ticket Purchase Complete",
            description=(
                f"Purchased **{ticket_count}** Dirty Ticket(s) for **{coins_cost}** coins.\n"
                f"You now have **{updated_player['dirty_tickets']}** Dirty Tickets and **{updated_player['coins']}** coins."
            ),
            color=0x57F287,
        )
        await interaction.response.edit_message(
            embed=embed,
            view=self,
            attachments=[],
        )

    @discord.ui.button(label="Buy x1", style=discord.ButtonStyle.success, row=0)
    async def buy_one(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._purchase(interaction, ticket_count=1, coins_cost=1000)

    @discord.ui.button(label="Buy x5", style=discord.ButtonStyle.success, row=1)
    async def buy_five(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._purchase(interaction, ticket_count=5, coins_cost=4500)

    @discord.ui.button(label="Buy x10", style=discord.ButtonStyle.success, row=2)
    async def buy_ten(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._purchase(interaction, ticket_count=10, coins_cost=8500)

    @discord.ui.button(label="🏠 Back to Pawn Shop", style=discord.ButtonStyle.secondary, row=3)
    async def back_to_pawn_shop(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🏚️ Pawn Shop",
            description=(
                f"Welcome back, **{interaction.user.display_name}**.\n\n"
                "I deal in junk, favors, and things people don’t ask about.\n\n"
                "What do you need?"
            ),
            color=0x8B5E3C,
        )
        await interaction.response.edit_message(
            embed=embed,
            view=PawnShopView(self.owner_id, self.is_admin),
            attachments=[],
        )


class ProfileView(discord.ui.View):
    def __init__(self, owner_id: int, is_admin: bool):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.is_admin = is_admin

        if is_admin:
            self.add_item(AdminButton(row=2))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "This menu isn't yours. Open your own with /profile.",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(label="🗑️ Dive", style=discord.ButtonStyle.primary, row=0)
    async def dive_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        import os

        player = queries.get_player(interaction.user.id)
        zone_name = ZONES[player["current_zone_id"]]["name"]

        starter = get_random_dive_starter()
        midpoint = get_random_dive_midpoint()

        # Stage 1
        await interaction.response.edit_message(
            embed=dive_processing_embed(zone_name, starter),
            view=None,
            attachments=[],
)
        await asyncio.sleep(1.0)

        # Stage 2
        await interaction.edit_original_response(
            embed=dive_processing_embed(zone_name, f"{starter}\n\n{midpoint}"),
            view=None,
            attachments=[],
)
        await asyncio.sleep(1.0)

        # Roll result
        equipment = _safe_equipment(interaction.user.id)
        equipment_bonuses = calculate_equipment_bonuses(equipment)

        item_id, item = roll_item_for_zone(
            player["current_zone_id"],
            rare_bonus=equipment_bonuses["drop_bonus"],
        )
        event = maybe_roll_dive_event()

        bonus_coins = 0
        bonus_xp = 0
        event_text = None

        if event:
            bonus_coins = int(event.get("bonus_coins", 0))
            bonus_xp = int(event.get("bonus_xp", 0))
            event_text = event.get("text")

        gained_coins = int(item["coins"]) + bonus_coins
        gained_coins = int(gained_coins * (1 + equipment_bonuses["coin_boost"] + equipment_bonuses["loot_value"]))
        gained_xp = int(item["xp"]) + bonus_xp
        gained_xp = int(gained_xp * (1 + equipment_bonuses["xp_boost"]))

        extra_item_triggered = random.random() < equipment_bonuses["extra_item_chance"]
        extra_items_text = None
        if extra_item_triggered:
            extra_items_text = f"{item.get('emoji', '✨')} {item['name']} x1"

        gear_bonus_lines = []
        if equipment_bonuses["coin_boost"]:
            gear_bonus_lines.append(f"💰 Gear Bonus: +{int(equipment_bonuses['coin_boost'] * 100)}% coins")
        if equipment_bonuses["loot_value"]:
            gear_bonus_lines.append(f"💎 Gear Bonus: +{int(equipment_bonuses['loot_value'] * 100)}% item value")
        if equipment_bonuses["xp_boost"]:
            gear_bonus_lines.append(f"✨ Gear Bonus: +{int(equipment_bonuses['xp_boost'] * 100)}% XP")
        if equipment_bonuses["drop_bonus"]:
            gear_bonus_lines.append(f"🎁 Gear Bonus: +{int(equipment_bonuses['drop_bonus'] * 100)}% rare chance")
        if extra_item_triggered:
            gear_bonus_lines.append(f"🎁 Extra Drop: {extra_items_text}")

        bonus_parts = []
        if bonus_coins or bonus_xp:
            bonus_parts.append(f"🎉 Event Bonus: +{bonus_coins} coins, +{bonus_xp} XP")
        if gear_bonus_lines:
            bonus_parts.extend(gear_bonus_lines)
        bonus_text = "\n".join(bonus_parts) if bonus_parts else None

        new_xp, new_level, leveled_up = apply_xp(
            player["xp"],
            player["level"],
            gained_xp,
        )
        new_title = determine_title(new_level)
        new_dives = player["total_dives"] + 1
        new_coins = player["coins"] + gained_coins

        queries.add_item_to_inventory(interaction.user.id, item_id, 1)
        if extra_item_triggered:
            queries.add_item_to_inventory(interaction.user.id, item_id, 1)
        unlocked_zone_ids = queries.unlock_zones_for_level(interaction.user.id, new_level)
        queries.update_player_progress(
            user_id=interaction.user.id,
            coins=new_coins,
            xp=new_xp,
            level=new_level,
            current_title=new_title,
            total_dives=new_dives,
        )
        queries.progress_daily_quest(interaction.user.id, "dive_count", 1)
        queries.check_and_complete_collections(interaction.user.id)

        updated_player = queries.get_player(interaction.user.id)
        unlocked_zone_names = [
            ZONES[zid]["name"]
            for zid in unlocked_zone_ids
            if zid in ZONES and ZONES[zid]["unlock_level"] == new_level
        ]

        attachment_file = None
        attachment_name = None
        image_path = item.get("image")

        if isinstance(image_path, str) and image_path:
            if image_path.startswith("http"):
                # URL image: let embeds.py use the URL directly
                attachment_name = None
                attachment_file = None
            else:
                # Local file: attach it so Discord can show the thumbnail
                if os.path.exists(image_path):
                    attachment_name = os.path.basename(image_path)
                    attachment_file = discord.File(image_path, filename=attachment_name)  
                

        embed = dive_result_embed(
            player=updated_player,
            item_id=item_id,
            leveled_up=leveled_up,
            reaction_text=get_random_dive_reaction(),
            event_text=event_text,
            bonus_text=(f"🎉 Bonus: +{bonus_coins} coins, +{bonus_xp} XP" if (bonus_coins or bonus_xp) else None),
            unlocked_zone_names=unlocked_zone_names or None,
            avatar_url=_avatar_url(interaction.user),
            attachment_filename=attachment_name,
        )

        if attachment_file:
            await interaction.edit_original_response(
                embed=embed,
                attachments=[attachment_file],
                view=ProfileView(self.owner_id, self.is_admin),
            )
        else:
            await interaction.edit_original_response(
                embed=embed,
                view=ProfileView(self.owner_id, self.is_admin),
            )

    @discord.ui.button(label="🎒 Loot", style=discord.ButtonStyle.secondary, row=0)
    async def inventory_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        inventory = queries.get_inventory(interaction.user.id)
        view = InventoryView(self.owner_id, self.is_admin, inventory, page=0)
        embed = inventory_embed(
            interaction.user.display_name,
            view.page_lines(),
            view.page,
            view.total_pages,
        )
        await interaction.response.edit_message(embed=embed, view=view, attachments=[])

    @discord.ui.button(label="🏚️ Pawn Shop", style=discord.ButtonStyle.success, row=0)
    async def pawnshop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🏚️ Pawn Shop",
            description=(
                f"Welcome back, **{interaction.user.display_name}**.\n\n"
                "I deal in junk, favors, and things people don’t ask about.\n\n"
                "What do you need?"
            ),
            color=0x8B5E3C,
        )

        await interaction.response.edit_message(
            embed=embed,
            view=PawnShopView(self.owner_id, self.is_admin),
            attachments=[],
        )

    @discord.ui.button(label="🗺️ Zones", style=discord.ButtonStyle.success, row=1)
    async def zones_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        unlocked = queries.get_unlocked_zone_ids(interaction.user.id)
        view = ZoneSelectorView(self.owner_id, self.is_admin, unlocked or ["back_alley"], index=0)
        await interaction.response.edit_message(embed=view.build_embed(interaction), view=view, attachments=[])

    @discord.ui.button(label="✨ Events", style=discord.ButtonStyle.danger, row=1)
    async def events_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            embed=events_embed(),
            view=ProfileView(self.owner_id, self.is_admin),
            attachments=[],
        )

    @discord.ui.button(label="🏛️ Museum", style=discord.ButtonStyle.secondary, row=1)
    async def museum_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        from game.helpers import get_next_incomplete_collection
        
        player = queries.get_player(interaction.user.id)
        discovered = queries.get_discovered_item_ids(interaction.user.id)
        completed_collections = queries.get_completed_collections(interaction.user.id)
        
        museum_level = player.get("museum_level", 1)
        museum_xp = player.get("museum_xp", 0)
        total_collections = len(MUSEUM_COLLECTIONS)
        collections_completed = len(completed_collections)
        
        next_info = get_next_incomplete_collection(discovered, MUSEUM_COLLECTIONS, completed_collections)
        
        embed = museum_home_embed(
            museum_level=museum_level,
            museum_xp=museum_xp,
            collections_completed=collections_completed,
            total_collections=total_collections,
            next_collection_info=next_info,
        )
        view = MuseumHomeView(self.owner_id, self.is_admin)
        await interaction.response.edit_message(
            embed=embed,
            view=view,
            attachments=[],
        )

    @discord.ui.button(label="🛠️ Gear", style=discord.ButtonStyle.secondary, row=3)
    async def gear_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = EquipmentView(self.owner_id, self.is_admin)
        await interaction.response.edit_message(
            embed=view.build_embed(interaction),
            view=view,
            attachments=[],
        )

    @discord.ui.button(label="� Quests", style=discord.ButtonStyle.secondary, row=3)
    async def quests_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = GeneratedQuestView(self.owner_id, self.is_admin)
        embed = view.build_embed()
        await interaction.response.edit_message(
            embed=embed,
            view=view,
            attachments=[],
        )

    @discord.ui.button(label="�🎟 Dirty Draw", style=discord.ButtonStyle.danger, row=3)
    async def dirty_draw_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = DirtyDrawView(self.owner_id, self.is_admin)
        await interaction.response.edit_message(
            embed=view.build_embed(),
            view=view,
            attachments=[],
        )

    @discord.ui.button(label="❓ Help", style=discord.ButtonStyle.secondary, row=1)
    async def instructions_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            embed=help_embed(),
            view=ProfileView(self.owner_id, self.is_admin),
            attachments=[],
        )

    @discord.ui.button(label="💌 Contact Admin", style=discord.ButtonStyle.secondary, row=2)
    async def contact_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ContactAdminModal())

    @discord.ui.button(label="🔄 Refresh", style=discord.ButtonStyle.secondary, row=2)
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = build_profile_embed_for_user(interaction.user)
        await interaction.response.edit_message(
            embed=embed,
            view=ProfileView(self.owner_id, self.is_admin),
            attachments=[],
        )


class AdminButton(discord.ui.Button):
    def __init__(self, row: int = 2):
        super().__init__(label="Admin", emoji="🛠️", style=discord.ButtonStyle.danger, row=row)

    async def callback(self, interaction: discord.Interaction):
        from ui.embeds import admin_panel_embed
        from db.queries import get_all_contact_messages
        
        messages = get_all_contact_messages()
        unread_count = sum(1 for m in messages if m.get("status") == "open")
        
        embed = admin_panel_embed(unread_count)
        view = AdminPanelView()
        
        await interaction.response.edit_message(embed=embed, view=view, attachments=[])


class AdminPanelView(discord.ui.View):
    """Admin panel home."""
    def __init__(self):
        super().__init__(timeout=600)

    @discord.ui.button(label="📬 View Messages", style=discord.ButtonStyle.primary, row=0)
    async def view_messages_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        from ui.embeds import admin_messages_embed
        from db.queries import get_all_contact_messages
        
        messages = get_all_contact_messages()
        embed = admin_messages_embed(messages, page=1)
        view = AdminMessagesView(messages, page=1)
        
        await interaction.response.edit_message(embed=embed, view=view, attachments=[])

    @discord.ui.button(label="💰 Grant Coins", style=discord.ButtonStyle.success, row=0)
    async def grant_coins_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        from ui.modals import GrantCoinsModal
        await interaction.response.send_modal(GrantCoinsModal())

    @discord.ui.button(label="✨ Grant XP", style=discord.ButtonStyle.success, row=1)
    async def grant_xp_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        from ui.modals import GrantXPModal
        await interaction.response.send_modal(GrantXPModal())

    @discord.ui.button(label="🎟 Grant Tickets", style=discord.ButtonStyle.success, row=1)
    async def grant_tickets_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        from ui.modals import GrantTicketsModal
        await interaction.response.send_modal(GrantTicketsModal())

    @discord.ui.button(label="🎁 Grant Items", style=discord.ButtonStyle.success, row=1)
    async def grant_items_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        from ui.modals import GrantItemsModal
        await interaction.response.send_modal(GrantItemsModal())

    @discord.ui.button(label="🏠 Back", style=discord.ButtonStyle.secondary, row=2)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await show_profile(interaction, interaction.user.id, True)


class AdminMessagesView(discord.ui.View):
    """List contact messages."""
    def __init__(self, messages: list[dict], page: int = 1, per_page: int = 5):
        super().__init__(timeout=600)
        self.messages = messages
        self.page = page
        self.per_page = per_page
        self.total_pages = (len(messages) + per_page - 1) // per_page
        
        # Disable prev/next if only one page
        if self.total_pages <= 1:
            self.previous_page.disabled = True
            self.next_page.disabled = True

    @discord.ui.button(label="◀ Previous", style=discord.ButtonStyle.secondary, row=0)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 1:
            self.page -= 1
            from ui.embeds import admin_messages_embed
            embed = admin_messages_embed(self.messages, self.page, self.per_page)
            view = AdminMessagesView(self.messages, self.page, self.per_page)
            await interaction.response.edit_message(embed=embed, view=view, attachments=[])

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.secondary, row=0)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page < self.total_pages:
            self.page += 1
            from ui.embeds import admin_messages_embed
            embed = admin_messages_embed(self.messages, self.page, self.per_page)
            view = AdminMessagesView(self.messages, self.page, self.per_page)
            await interaction.response.edit_message(embed=embed, view=view, attachments=[])

    @discord.ui.button(label="🏠 Back to Panel", style=discord.ButtonStyle.primary, row=1)
    async def back_to_panel(self, interaction: discord.Interaction, button: discord.ui.Button):
        from ui.embeds import admin_panel_embed
        from db.queries import get_all_contact_messages
        
        messages = get_all_contact_messages()
        unread_count = sum(1 for m in messages if m.get("status") == "open")
        embed = admin_panel_embed(unread_count)
        view = AdminPanelView()
        
        await interaction.response.edit_message(embed=embed, view=view, attachments=[])
