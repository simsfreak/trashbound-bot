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

from db import queries
from game.data import ITEMS, ZONES, MUSEUM_COLLECTIONS
from game.helpers import (
    determine_title,
    get_random_dive_midpoint,
    get_random_dive_reaction,
    get_random_dive_starter,
    get_recent_finds_from_inventory_rows,
    maybe_roll_dive_event,
    roll_item_for_zone,
)
from game.leveling import apply_xp
from ui.embeds import (
    dive_processing_embed,
    dive_result_embed,
    events_embed,
    help_embed,
    inventory_embed,
    mix_result_embed,
    museum_home_embed,
    profile_embed,
    zone_embed,
)
from ui.modals import ContactAdminModal


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

    return profile_embed(
        player=player,
        inventory_count=sum(qty for _, qty in inventory),
        recent_finds=recent_finds,
        active_effects=active_effects,
        equipment=equipment,
        avatar_url=_avatar_url(user),
    )


async def show_profile(interaction: discord.Interaction, owner_id: int, is_admin: bool):
    embed = build_profile_embed_for_user(interaction.user)
    await interaction.response.edit_message(
        embed=embed,
        view=ProfileView(owner_id, is_admin),
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
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="➡️ Next", style=discord.ButtonStyle.secondary, row=0)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page < self.total_pages - 1:
            self.page += 1
        embed = inventory_embed(interaction.user.display_name, self.page_lines(), self.page, self.total_pages)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🔄 Reload", style=discord.ButtonStyle.secondary, row=1)
    async def reload_inventory(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.items = queries.get_inventory(interaction.user.id)
        embed = inventory_embed(interaction.user.display_name, self.page_lines(), self.page, self.total_pages)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🏠 Back to Profile", style=discord.ButtonStyle.primary, row=1)
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
        await interaction.response.edit_message(embed=self.build_embed(interaction), view=self)

    @discord.ui.button(label="✅ Set Active", style=discord.ButtonStyle.success, row=0)
    async def set_active_zone(self, interaction: discord.Interaction, button: discord.ui.Button):
        zone_id = self.current_zone_id()
        unlocked = set(queries.get_unlocked_zone_ids(interaction.user.id))

        if zone_id not in unlocked:
            await interaction.response.send_message("That zone is still locked. Keep grinding.", ephemeral=True)
            return

        queries.set_current_zone(interaction.user.id, zone_id)
        await interaction.response.edit_message(embed=self.build_embed(interaction), view=self)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.secondary, row=0)
    async def next_zone(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index = (self.index + 1) % len(self.zone_ids)
        await interaction.response.edit_message(embed=self.build_embed(interaction), view=self)

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

    @discord.ui.button(label="🏠 Back to Profile", style=discord.ButtonStyle.primary)
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
        )


class PawnChatBackButton(discord.ui.Button):
    def __init__(self, row: int = 1):
        super().__init__(label="🏠 Back to Profile", style=discord.ButtonStyle.primary, row=row)

    async def callback(self, interaction: discord.Interaction):
        if not isinstance(self.view, PawnChatChoiceView):
            return
        await show_profile(interaction, self.view.owner_id, self.view.is_admin)

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
        item_id, item = roll_item_for_zone(player["current_zone_id"])
        event = maybe_roll_dive_event()

        bonus_coins = 0
        bonus_xp = 0
        event_text = None

        if event:
            bonus_coins = int(event.get("bonus_coins", 0))
            bonus_xp = int(event.get("bonus_xp", 0))
            event_text = event.get("text")

        gained_coins = int(item["coins"]) + bonus_coins
        gained_xp = int(item["xp"]) + bonus_xp

        new_xp, new_level, leveled_up = apply_xp(
            player["xp"],
            player["level"],
            gained_xp,
        )
        new_title = determine_title(new_level)
        new_dives = player["total_dives"] + 1
        new_coins = player["coins"] + gained_coins

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
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="🎟 Exchange", style=discord.ButtonStyle.success, row=0)
    async def mix_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            embed=mix_result_embed(
                    "🎟 Exchange",
                    "The pawn shop is being reworked...\n\nCome back soon 👀",
                ),
                view=ProfileView(self.owner_id, self.is_admin),
            )
    
    @discord.ui.button(label="🗺️ Zones", style=discord.ButtonStyle.success, row=1)
    async def zones_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        unlocked = queries.get_unlocked_zone_ids(interaction.user.id)
        view = ZoneSelectorView(self.owner_id, self.is_admin, unlocked or ["back_alley"], index=0)
        await interaction.response.edit_message(embed=view.build_embed(interaction), view=view)

    @discord.ui.button(label="✨ Events", style=discord.ButtonStyle.danger, row=1)
    async def events_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            embed=events_embed(),
            view=ProfileView(self.owner_id, self.is_admin),
        )

    @discord.ui.button(label="🏛️ Museum", style=discord.ButtonStyle.secondary, row=1)
    async def museum_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        discovered = queries.get_discovered_item_ids(interaction.user.id)
        embed = museum_home_embed(interaction.user.display_name, discovered)
        await interaction.response.edit_message(
            embed=embed,
            view=MuseumHomeView(self.owner_id, self.is_admin),
        )

    @discord.ui.button(label="❓ Help", style=discord.ButtonStyle.secondary, row=1)
    async def instructions_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            embed=help_embed(),
            view=ProfileView(self.owner_id, self.is_admin),
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
        )

    @discord.ui.button(label="💬 Chat", style=discord.ButtonStyle.secondary, row=1)
    async def pawn_chat_button(self, interaction: discord.Interaction, button: discord.ui.Button):
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
        embed.set_footer(text="Choose your answer carefully.")
        await interaction.response.edit_message(
            embed=embed,
            view=PawnChatChoiceView(self.owner_id, self.is_admin, story),
        )


class AdminButton(discord.ui.Button):
    def __init__(self, row: int = 2):
        super().__init__(label="Admin", emoji="🛠️", style=discord.ButtonStyle.danger, row=row)

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🛠️ Admin Panel",
            description="Admin tools are coming next:\n• View messages\n• Grant XP\n• Grant coins\n• Trigger events",
            color=0xED4245,
        )
        await interaction.response.edit_message(embed=embed, view=self.view)
