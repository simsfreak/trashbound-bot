import asyncio
import math
import discord
from datetime import datetime

from db import queries
from game.data import ITEMS, MIX_RECIPES, ZONES, MUSEUM_COLLECTIONS, TAVERN_FOOD
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
    pawn_shop_main_embed,
    pawn_shop_tickets_embed,
    pawn_shop_items_embed,
    pawn_shop_specials_embed,
    pawn_shop_exchange_embed,
    profile_embed,
    zone_embed,
    exclusive_inventory_main_embed,
    exclusive_category_embed,
    exclusive_detail_embed,
    exclusive_reward_embed,
    tavern_main_embed,
    tavern_food_shop_embed,
    tavern_ticket_redeem_embed,
    tavern_redeem_single_embed,
    tavern_redeem_multi_embed,
    tavern_redeem_all_embed,
    exclusive_unlock_embed,
)
from ui.modals import ContactAdminModal


def _safe_active_effects(user_id: int):
    """Get active effects with remaining time."""
    from datetime import datetime
    effects = queries.get_active_effects(user_id)
    result = []
    for effect in effects:
        if isinstance(effect, dict) and "expires_at" in effect:
            expires_at = effect["expires_at"]
            if isinstance(expires_at, str):
                # Parse ISO format string
                expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            
            remaining = expires_at - datetime.utcnow()
            if remaining.total_seconds() > 0:
                total_seconds = int(remaining.total_seconds())
                hours, rem = divmod(total_seconds, 3600)
                minutes, _seconds = divmod(rem, 60)
                time_str = f"{hours}h {minutes}m" if hours else f"{minutes}m"
                result.append({
                    "label": effect.get("label", "Effect"),
                    "expires_at": time_str,
                })
    return result


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

    def _build_dive_bonus_text(self, user_id: int, bonus_coins: int, bonus_xp: int, xp_multiplier: float, luck_bonus: float) -> str | None:
        """Build bonus text showing all active effects during a dive."""
        parts = []
        
        # Event/random bonuses
        if bonus_coins or bonus_xp:
            parts.append(f"🎉 Event Bonus: +{bonus_coins} coins, +{bonus_xp} XP")
        
        # XP buffer
        if xp_multiplier > 1.0:
            xp_boost_pct = int((xp_multiplier - 1.0) * 100)
            parts.append(f"⚡ XP Buffer Active: +{xp_boost_pct}% XP")
        
        # Luck amulet
        if luck_bonus > 0:
            luck_pct = int(luck_bonus * 100)
            parts.append(f"🍀 Luck Amulet Active: +{luck_pct}% Rarity Chance")
        
        return "\n".join(parts) if parts else None

    @discord.ui.button(label="🗑️ Dive", style=discord.ButtonStyle.primary, row=0)
    async def dive_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        import os

        player = queries.get_player(interaction.user.id)
        
        # Check hunger status
        current_hunger = player.get("hunger", 100)
        if current_hunger <= 0:
            await interaction.response.send_message(
                f"╔══════════ ⚠️ Status Warning ⚠️ ══════════╗\n"
                f"  🍖 {player['username']}'s tummy is angry! 😭\n"
                f"  Please visit The Tavern for some Food.\n"
                f"╚═══════════════════════════════════════════╝",
                ephemeral=True,
            )
            return
        elif current_hunger <= 25:
            await interaction.response.send_message(
                f"╔═══════════ 🍓 Hunger Notice 🍓 ═══════════╗\n"
                f"  🍖 {player['username']} is getting hungryyy...\n"
                f"  Maybe exchange loot at Pawn Shop and\n"
                f"  buy food 🍖 at The Tavern! (Currently: {current_hunger}%)\n"
                f"╚═══════════════════════════════════════════╝",
                ephemeral=True,
            )
        
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
        await asyncio.sleep(1.5)

        # Roll result with luck bonus
        luck_bonus = queries.get_luck_bonus(interaction.user.id)
        item_id, item = roll_item_for_zone(player["current_zone_id"], rare_bonus=luck_bonus)
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

        # Apply active XP buffer if available
        xp_multiplier = queries.get_xp_multiplier(interaction.user.id)
        if xp_multiplier > 1.0:
            gained_xp = int(gained_xp * xp_multiplier)

        new_xp, new_level, leveled_up = apply_xp(
            player["xp"],
            player["level"],
            gained_xp,
        )
        new_title = determine_title(new_level)
        new_dives = player["total_dives"] + 1
        new_coins = player["coins"] + gained_coins
        new_hunger = queries.reduce_hunger(interaction.user.id, 1)  # Reduce hunger by 1 per dive

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
            bonus_text=self._build_dive_bonus_text(interaction.user.id, bonus_coins, bonus_xp, xp_multiplier, luck_bonus),
            unlocked_zone_names=unlocked_zone_names or None,
            avatar_url=_avatar_url(interaction.user),
            attachment_filename=attachment_name,
        )

        # Stage 3: Show the result embed first without buttons
        if attachment_file:
            await interaction.edit_original_response(
                embed=embed,
                attachments=[attachment_file],
                view=None,
            )
        else:
            await interaction.edit_original_response(
                embed=embed,
                attachments=[],
                view=None,
            )
        
        # Give user time to read the result
        await asyncio.sleep(2.0)
        
        # Stage 4: Add buttons to allow user to continue
        try:
            if attachment_file:
                await interaction.edit_original_response(
                    embed=embed,
                    attachments=[attachment_file],
                    view=ProfileView(self.owner_id, self.is_admin),
                )
            else:
                await interaction.edit_original_response(
                    embed=embed,
                    attachments=[],
                    view=ProfileView(self.owner_id, self.is_admin),
                )
        except discord.errors.NotFound:
            # Message was deleted, that's okay
            pass

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

    @discord.ui.button(label="🍻 The Tavern", style=discord.ButtonStyle.success, row=0)
    async def tavern_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = tavern_main_embed(interaction.user.display_name)
        await interaction.response.edit_message(
            embed=embed,
            view=TavernMainView(self.owner_id, self.is_admin),
            attachments=[],
        )

    @discord.ui.button(label="🗺️ Zones", style=discord.ButtonStyle.success, row=1)
    async def zones_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        unlocked = queries.get_unlocked_zone_ids(interaction.user.id)
        view = ZoneSelectorView(self.owner_id, self.is_admin, unlocked or ["back_alley"], index=0)
        await interaction.response.edit_message(embed=view.build_embed(interaction), view=view, attachments=[])

    @discord.ui.button(label="🎒 Pawn Shop", style=discord.ButtonStyle.primary, row=1)
    async def pawn_shop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = pawn_shop_main_embed(interaction.user.display_name)
        await interaction.response.edit_message(
            embed=embed,
            view=PawnShopMainView(self.owner_id, self.is_admin),
            attachments=[],
        )

    @discord.ui.button(label="✨ Events", style=discord.ButtonStyle.danger, row=1)
    async def events_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            embed=events_embed(),
            view=ProfileView(self.owner_id, self.is_admin),
            attachments=[],
        )

    @discord.ui.button(label="🏛️ Museum", style=discord.ButtonStyle.secondary, row=1)
    async def museum_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        discovered = queries.get_discovered_item_ids(interaction.user.id)
        embed = museum_home_embed(interaction.user.display_name, discovered)
        await interaction.response.edit_message(
            embed=embed,
            view=MuseumHomeView(self.owner_id, self.is_admin),
            attachments=[],
        )

    @discord.ui.button(label="❓ Help", style=discord.ButtonStyle.secondary, row=1)
    async def instructions_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            embed=help_embed(),
            view=ProfileView(self.owner_id, self.is_admin),
            attachments=[],
        )

    @discord.ui.button(label="🧸 Exclusive Rares🪽", style=discord.ButtonStyle.primary, row=2)
    async def exclusive_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        exclusive_counts = queries.get_exclusive_counts(interaction.user.id)
        from ui.embeds import exclusive_inventory_main_embed
        embed = exclusive_inventory_main_embed(interaction.user.display_name, exclusive_counts)
        await interaction.response.edit_message(
            embed=embed,
            view=ExclusiveMainView(self.owner_id, self.is_admin),
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
        embed = discord.Embed(
            title="🛠️ Admin Panel",
            description="Admin tools are coming next:\n• View messages\n• Grant XP\n• Grant coins\n• Trigger events",
            color=0xED4245,
        )
        await interaction.response.edit_message(embed=embed, view=self.view)


class PawnShopMainView(discord.ui.View):
    def __init__(self, owner_id: int, is_admin: bool):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.is_admin = is_admin

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This pawn shop isn't yours.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="🎟️ Tickets", style=discord.ButtonStyle.primary, row=0)
    async def tickets_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = pawn_shop_tickets_embed()
        await interaction.response.edit_message(embed=embed, view=PawnShopTicketsView(self.owner_id, self.is_admin), attachments=[])

    @discord.ui.button(label="🏪 Items", style=discord.ButtonStyle.primary, row=0)
    async def items_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = pawn_shop_items_embed()
        await interaction.response.edit_message(embed=embed, view=PawnShopItemsView(self.owner_id, self.is_admin), attachments=[])

    @discord.ui.button(label="🪄 Specials", style=discord.ButtonStyle.primary, row=0)
    async def specials_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = pawn_shop_specials_embed()
        await interaction.response.edit_message(embed=embed, view=PawnShopSpecialsView(self.owner_id, self.is_admin), attachments=[])

    @discord.ui.button(label="♻️ Exchange", style=discord.ButtonStyle.primary, row=1)
    async def exchange_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = pawn_shop_exchange_embed()
        await interaction.response.edit_message(embed=embed, view=PawnShopExchangeView(self.owner_id, self.is_admin), attachments=[])

    @discord.ui.button(label="🏠 Back", style=discord.ButtonStyle.secondary, row=1)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await show_profile(interaction, self.owner_id, self.is_admin)


class PawnShopTicketsView(discord.ui.View):
    def __init__(self, owner_id: int, is_admin: bool):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.is_admin = is_admin

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This shop isn't yours.", ephemeral=True)
            return False
        return True

    async def purchase_ticket(self, interaction: discord.Interaction, qty: int, price: int):
        player = queries.get_player(interaction.user.id)
        if player["coins"] < price:
            await interaction.response.send_message(
                f"❌ You need 🪙 {price} but only have 🪙 {player['coins']}",
                ephemeral=True,
            )
            return
        
        new_coins = player["coins"] - price
        queries.update_player_progress(
            user_id=interaction.user.id,
            coins=new_coins,
            xp=player["xp"],
            level=player["level"],
            current_title=player["current_title"],
            total_dives=player["total_dives"],
        )
        
        await interaction.response.send_message(
            f"✅ Purchased 🎟️ Dirty Tickets x{qty} for 🪙 {price}!\n"
            f"Remaining: 🪙 {new_coins}",
            ephemeral=True,
        )

    @discord.ui.button(label="🎟️x1-🪙 1000", style=discord.ButtonStyle.success, row=0)
    async def buy_1_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.purchase_ticket(interaction, 1, 1000)

    @discord.ui.button(label="🎟️x5-🪙 4500", style=discord.ButtonStyle.success, row=0)
    async def buy_5_tickets(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.purchase_ticket(interaction, 5, 4500)

    @discord.ui.button(label="🎟️x10-🪙 8500", style=discord.ButtonStyle.success, row=1)
    async def buy_10_tickets(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.purchase_ticket(interaction, 10, 8500)

    @discord.ui.button(label="🏪 Back", style=discord.ButtonStyle.secondary, row=1)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = pawn_shop_main_embed(interaction.user.display_name)
        await interaction.response.edit_message(embed=embed, view=PawnShopMainView(self.owner_id, self.is_admin), attachments=[])


class PawnShopItemsView(discord.ui.View):
    def __init__(self, owner_id: int, is_admin: bool):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.is_admin = is_admin

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This shop isn't yours.", ephemeral=True)
            return False
        return True

    async def purchase_buffer(self, interaction: discord.Interaction, buffer_name: str, bonus_pct: float, price: int):
        player = queries.get_player(interaction.user.id)
        if player["coins"] < price:
            await interaction.response.send_message(
                f"❌ You need 🪙 {price} but only have 🪙 {player['coins']}",
                ephemeral=True,
            )
            return
        
        # Check if they already have an active XP buffer
        existing_effect = queries.get_active_effect(interaction.user.id, "xp_buffer")
        if existing_effect:
            await interaction.response.send_message(
                f"⏳ You already have **{existing_effect['label']}** active!\n"
                f"It expires in 2 hours. You cannot stack buffers.",
                ephemeral=True,
            )
            return
        
        # Deduct coins
        new_coins = player["coins"] - price
        queries.update_player_progress(
            user_id=interaction.user.id,
            coins=new_coins,
            xp=player["xp"],
            level=player["level"],
            current_title=player["current_title"],
            total_dives=player["total_dives"],
        )
        
        # Add effect (1.0 + bonus_pct as multiplier)
        multiplier = 1.0 + (bonus_pct / 100.0)
        queries.add_active_effect(
            user_id=interaction.user.id,
            effect_id="xp_buffer",
            label=f"{buffer_name} ({bonus_pct:.0f}% XP)",
            multiplier=multiplier,
            duration_hours=2,
            source_item_id=None,
        )
        
        await interaction.response.send_message(
            f"✅ Activated **{buffer_name}**!\n"
            f"⚡ +{bonus_pct:.0f}% XP for 2 real-time hours\n"
            f"Remaining coins: 🪙 {new_coins}",
            ephemeral=True,
        )

    async def purchase_amulet(self, interaction: discord.Interaction, amulet_name: str, luck_bonus: float, price: int):
        player = queries.get_player(interaction.user.id)
        if player["coins"] < price:
            await interaction.response.send_message(
                f"❌ You need 🪙 {price} but only have 🪙 {player['coins']}",
                ephemeral=True,
            )
            return
        
        # Check if they already have an active Luck amulet
        existing_effect = queries.get_active_effect(interaction.user.id, "luck_amulet")
        if existing_effect:
            await interaction.response.send_message(
                f"⏳ You already have **{existing_effect['label']}** active!\n"
                f"It expires in 2 hours. You cannot stack amulets.",
                ephemeral=True,
            )
            return
        
        # Deduct coins
        new_coins = player["coins"] - price
        queries.update_player_progress(
            user_id=interaction.user.id,
            coins=new_coins,
            xp=player["xp"],
            level=player["level"],
            current_title=player["current_title"],
            total_dives=player["total_dives"],
        )
        
        # Add effect (luck_bonus is stored directly as the percentage)
        queries.add_active_effect(
            user_id=interaction.user.id,
            effect_id="luck_amulet",
            label=f"{amulet_name} (+{luck_bonus:.0f}% Luck)",
            multiplier=luck_bonus / 100.0,  # Store as decimal multiplier
            duration_hours=2,
            source_item_id=None,
        )
        
        await interaction.response.send_message(
            f"✅ Activated **{amulet_name}**!\n"
            f"🍀 +{luck_bonus:.0f}% rarity chance for 2 real-time hours\n"
            f"Remaining coins: 🪙 {new_coins}",
            ephemeral=True,
        )

    @discord.ui.button(label="🧃-🪙 250", style=discord.ButtonStyle.success, row=0)
    async def buy_novice_buffer(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.purchase_buffer(interaction, "Novice Buffer", 10, 250)

    @discord.ui.button(label="🧪-🪙 400", style=discord.ButtonStyle.success, row=0)
    async def buy_basic_buffer(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.purchase_buffer(interaction, "Basic Buffer", 15, 400)

    @discord.ui.button(label="🍵-🪙 575", style=discord.ButtonStyle.success, row=0)
    async def buy_greater_buffer(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.purchase_buffer(interaction, "Greater Buffer", 20, 575)

    @discord.ui.button(label="🧴-🪙 775", style=discord.ButtonStyle.success, row=1)
    async def buy_advanced_buffer(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.purchase_buffer(interaction, "Advanced Buffer", 25, 775)

    @discord.ui.button(label="🧪💖-🪙 1150", style=discord.ButtonStyle.success, row=1)
    async def buy_elite_buffer(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.purchase_buffer(interaction, "Elite Buffer", 35, 1150)

    @discord.ui.button(label="🌟-🪙 1850", style=discord.ButtonStyle.success, row=2)
    async def buy_master_buffer(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.purchase_buffer(interaction, "Master Buffer", 50, 1850)

    @discord.ui.button(label="👑-🪙 3200", style=discord.ButtonStyle.success, row=2)
    async def buy_legendary_buffer(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.purchase_buffer(interaction, "Legendary Buffer", 75, 3200)

    @discord.ui.button(label="🍀-🪙 600", style=discord.ButtonStyle.secondary, row=3)
    async def buy_worn_amulet(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.purchase_amulet(interaction, "Worn Amulet", 10, 600)

    @discord.ui.button(label="🌙-🪙 950", style=discord.ButtonStyle.secondary, row=3)
    async def buy_polished_amulet(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.purchase_amulet(interaction, "Polished Amulet", 15, 950)

    @discord.ui.button(label="🌠-🪙 1650", style=discord.ButtonStyle.secondary, row=4)
    async def buy_enchanted_amulet(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.purchase_amulet(interaction, "Enchanted Amulet", 25, 1650)

    @discord.ui.button(label="👑-🪙 2750", style=discord.ButtonStyle.secondary, row=4)
    async def buy_lucky_star(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.purchase_amulet(interaction, "Lucky Star Amulet", 35, 2750)

    @discord.ui.button(label="🏪 Back", style=discord.ButtonStyle.secondary, row=4)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = pawn_shop_main_embed(interaction.user.display_name)
        await interaction.response.edit_message(embed=embed, view=PawnShopMainView(self.owner_id, self.is_admin), attachments=[])


class PawnShopSpecialsView(discord.ui.View):
    def __init__(self, owner_id: int, is_admin: bool):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.is_admin = is_admin

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This shop isn't yours.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="🏪 Back", style=discord.ButtonStyle.secondary, row=0)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = pawn_shop_main_embed(interaction.user.display_name)
        await interaction.response.edit_message(embed=embed, view=PawnShopMainView(self.owner_id, self.is_admin), attachments=[])


# ═══════════════════════════════════════════════════════════════════
# EXCLUSIVE COLLECTIBLES VIEWS
# ═══════════════════════════════════════════════════════════════════

class ExclusiveMainView(discord.ui.View):
    """Main view for exclusive inventory showing all categories."""
    def __init__(self, owner_id: int, is_admin: bool):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.is_admin = is_admin

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This collection isn't yours.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="🧸 Toys", style=discord.ButtonStyle.primary, row=0)
    async def toys_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        items = queries.get_exclusives_by_category(interaction.user.id, "Toys")
        from ui.embeds import exclusive_category_embed
        
        # Calculate pagination
        page_size = 5
        total_pages = max(1, (len(items) + page_size - 1) // page_size)
        
        embed = exclusive_category_embed(
            interaction.user.display_name,
            "Toys",
            items[:page_size],
            0,
            total_pages,
            "🧸",
        )
        await interaction.response.edit_message(
            embed=embed,
            view=ExclusiveCategoryView(self.owner_id, self.is_admin, "Toys", items, 0),
            attachments=[],
        )

    @discord.ui.button(label="🐶 Dogs", style=discord.ButtonStyle.secondary, row=0)
    async def dogs_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        items = queries.get_exclusives_by_category(interaction.user.id, "Dogs")
        from ui.embeds import exclusive_category_embed
        
        page_size = 5
        total_pages = max(1, (len(items) + page_size - 1) // page_size)
        
        embed = exclusive_category_embed(
            interaction.user.display_name,
            "Dogs",
            items[:page_size],
            0,
            total_pages,
            "🐶",
        )
        await interaction.response.edit_message(
            embed=embed,
            view=ExclusiveCategoryView(self.owner_id, self.is_admin, "Dogs", items, 0),
            attachments=[],
        )

    @discord.ui.button(label="🐱 Cats", style=discord.ButtonStyle.success, row=1)
    async def cats_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        items = queries.get_exclusives_by_category(interaction.user.id, "Cats")
        from ui.embeds import exclusive_category_embed
        
        page_size = 5
        total_pages = max(1, (len(items) + page_size - 1) // page_size)
        
        embed = exclusive_category_embed(
            interaction.user.display_name,
            "Cats",
            items[:page_size],
            0,
            total_pages,
            "🐱",
        )
        await interaction.response.edit_message(
            embed=embed,
            view=ExclusiveCategoryView(self.owner_id, self.is_admin, "Cats", items, 0),
            attachments=[],
        )

    @discord.ui.button(label="🪽 Wings", style=discord.ButtonStyle.danger, row=1)
    async def wings_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        items = queries.get_exclusives_by_category(interaction.user.id, "Wings")
        from ui.embeds import exclusive_category_embed
        
        page_size = 5
        total_pages = max(1, (len(items) + page_size - 1) // page_size)
        
        embed = exclusive_category_embed(
            interaction.user.display_name,
            "Wings",
            items[:page_size],
            0,
            total_pages,
            "🪽",
        )
        await interaction.response.edit_message(
            embed=embed,
            view=ExclusiveCategoryView(self.owner_id, self.is_admin, "Wings", items, 0),
            attachments=[],
        )

    @discord.ui.button(label="🏠 Back", style=discord.ButtonStyle.secondary, row=2)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await show_profile(interaction, self.owner_id, self.is_admin)


class ExclusiveCategoryView(discord.ui.View):
    """View for browsing exclusive items in a specific category with pagination."""
    def __init__(self, owner_id: int, is_admin: bool, category: str, items: list[dict], page: int = 0):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.is_admin = is_admin
        self.category = category
        self.items = items
        self.page = page
        self.page_size = 5

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This collection isn't yours.", ephemeral=True)
            return False
        return True

    @property
    def total_pages(self) -> int:
        return max(1, (len(self.items) + self.page_size - 1) // self.page_size)

    def current_page_items(self) -> list[dict]:
        start = self.page * self.page_size
        end = start + self.page_size
        return self.items[start:end]

    @discord.ui.button(label="⬅️ Prev", style=discord.ButtonStyle.secondary, row=0)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
        from ui.embeds import exclusive_category_embed
        category_emoji = {"Toys": "🧸", "Dogs": "🐶", "Cats": "🐱", "Wings": "🪽"}.get(self.category, "✨")
        embed = exclusive_category_embed(
            interaction.user.display_name,
            self.category,
            self.current_page_items(),
            self.page,
            self.total_pages,
            category_emoji,
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="➡️ Next", style=discord.ButtonStyle.secondary, row=0)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page < self.total_pages - 1:
            self.page += 1
        from ui.embeds import exclusive_category_embed
        category_emoji = {"Toys": "🧸", "Dogs": "🐶", "Cats": "🐱", "Wings": "🪽"}.get(self.category, "✨")
        embed = exclusive_category_embed(
            interaction.user.display_name,
            self.category,
            self.current_page_items(),
            self.page,
            self.total_pages,
            category_emoji,
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🏠 Back", style=discord.ButtonStyle.primary, row=1)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        exclusive_counts = queries.get_exclusive_counts(interaction.user.id)
        from ui.embeds import exclusive_inventory_main_embed
        embed = exclusive_inventory_main_embed(interaction.user.display_name, exclusive_counts)
        await interaction.response.edit_message(
            embed=embed,
            view=ExclusiveMainView(self.owner_id, self.is_admin),
            attachments=[],
        )


class PawnShopExchangeView(discord.ui.View):
    def __init__(self, owner_id: int, is_admin: bool):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.is_admin = is_admin

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This shop isn't yours.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="♻️ Trade Loot", style=discord.ButtonStyle.danger, row=0)
    async def trade_loot_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "🚧 Trade Loot feature coming soon!\nTrade suspicious items at your own risk.",
            ephemeral=True,
        )

    @discord.ui.button(label="♻️ Sell Loot", style=discord.ButtonStyle.danger, row=0)
    async def sell_loot_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "🚧 Sell Loot feature coming soon!\n20% disposal fee will be applied.",
            ephemeral=True,
        )

    @discord.ui.button(label="🏪 Back", style=discord.ButtonStyle.secondary, row=1)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = pawn_shop_main_embed(interaction.user.display_name)
        await interaction.response.edit_message(embed=embed, view=PawnShopMainView(self.owner_id, self.is_admin), attachments=[])


# ═══════════════════════════════════════════════════════════════════
# THE TAVERN VIEWS
# ═══════════════════════════════════════════════════════════════════

class TavernMainView(discord.ui.View):
    """Main tavern view with all menu options."""
    def __init__(self, owner_id: int, is_admin: bool):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.is_admin = is_admin

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This tavern isn't yours.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="🍓 Food Shop", style=discord.ButtonStyle.primary, row=0)
    async def food_shop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = tavern_food_shop_embed()
        await interaction.response.edit_message(
            embed=embed,
            view=TavernFoodShopView(self.owner_id, self.is_admin),
            attachments=[],
        )

    @discord.ui.button(label="🎟️ Redeem Tickets", style=discord.ButtonStyle.success, row=0)
    async def redeem_tickets_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        tickets = queries.get_player(interaction.user.id).get("dirty_tickets", 0)
        embed = tavern_ticket_redeem_embed(interaction.user.display_name, tickets)
        await interaction.response.edit_message(
            embed=embed,
            view=TavernTicketRedeemView(self.owner_id, self.is_admin, tickets),
            attachments=[],
        )

    @discord.ui.button(label="💬 Chat", style=discord.ButtonStyle.secondary, row=1)
    async def chat_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "🚧 Chat with Fabian coming soon! He's working on his jokes... 😂",
            ephemeral=True,
        )

    @discord.ui.button(label="🏞️ The Alley", style=discord.ButtonStyle.secondary, row=1)
    async def alley_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "🚧 The Alley area is still under construction!",
            ephemeral=True,
        )

    @discord.ui.button(label="🏠 Waterfront House", style=discord.ButtonStyle.secondary, row=1)
    async def waterfront_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "🚧 The Waterfront House is being renovated...",
            ephemeral=True,
        )

    @discord.ui.button(label="🏠 Back", style=discord.ButtonStyle.danger, row=2)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await show_profile(interaction, self.owner_id, self.is_admin)


class TavernFoodShopView(discord.ui.View):
    """Food shop view for purchasing food."""
    def __init__(self, owner_id: int, is_admin: bool):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.is_admin = is_admin

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This shop isn't yours.", ephemeral=True)
            return False
        return True

    async def purchase_food(self, interaction: discord.Interaction, food_id: str):
        """Purchase a food item."""
        # Find the food item
        food_item = None
        for food in TAVERN_FOOD:
            if food["id"] == food_id:
                food_item = food
                break
        
        if not food_item:
            await interaction.response.send_message("❌ Food item not found!", ephemeral=True)
            return
        
        player = queries.get_player(interaction.user.id)
        
        # Check if player has enough coins
        if player["coins"] < food_item["price"]:
            await interaction.response.send_message(
                f"❌ You need 🪙 {food_item['price']} but only have 🪙 {player['coins']}",
                ephemeral=True,
            )
            return
        
        # Deduct coins and restore hunger
        new_coins = player["coins"] - food_item["price"]
        new_hunger = queries.feed_player(interaction.user.id, food_item["hunger_restored"])
        
        queries.update_player_progress(
            user_id=interaction.user.id,
            coins=new_coins,
            xp=player["xp"],
            level=player["level"],
            current_title=player["current_title"],
            total_dives=player["total_dives"],
        )
        
        await interaction.response.send_message(
            f"✅ Purchased {food_item['emoji']} **{food_item['name']}**!\n"
            f"+{food_item['hunger_restored']} Hunger\n"
            f"Current: {new_hunger}/100 ❤️\n"
            f"Remaining coins: 🪙 {new_coins}",
            ephemeral=True,
        )

    @discord.ui.button(label="🍓", style=discord.ButtonStyle.primary, row=0)
    async def strawberry_milk_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.purchase_food(interaction, "strawberry_milk")

    @discord.ui.button(label="🧋", style=discord.ButtonStyle.primary, row=0)
    async def brown_sugar_boba_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.purchase_food(interaction, "brown_sugar_boba")

    @discord.ui.button(label="🫐", style=discord.ButtonStyle.primary, row=0)
    async def berry_smoothie_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.purchase_food(interaction, "berry_smoothie")

    @discord.ui.button(label="🍖", style=discord.ButtonStyle.primary, row=1)
    async def bbq_rib_plate_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.purchase_food(interaction, "bbq_rib_plate")

    @discord.ui.button(label="🍦", style=discord.ButtonStyle.primary, row=1)
    async def berry_ice_cream_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.purchase_food(interaction, "berry_ice_cream")

    @discord.ui.button(label="🍻 Back", style=discord.ButtonStyle.secondary, row=2)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = tavern_main_embed(interaction.user.display_name)
        await interaction.response.edit_message(
            embed=embed,
            view=TavernMainView(self.owner_id, self.is_admin),
            attachments=[],
        )


class TavernTicketRedeemView(discord.ui.View):
    """Ticket redemption view."""
    def __init__(self, owner_id: int, is_admin: bool, ticket_count: int):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.is_admin = is_admin
        self.ticket_count = ticket_count

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("These tickets aren't yours.", ephemeral=True)
            return False
        return True

    async def redeem_tickets(self, interaction: discord.Interaction, qty: int):
        """Redeem a specific quantity of tickets."""
        player = queries.get_player(interaction.user.id)
        current_tickets = player.get("dirty_tickets", 0)
        
        if current_tickets < qty:
            await interaction.response.send_message(
                f"❌ You only have 🎟️ {current_tickets} tickets!",
                ephemeral=True,
            )
            return
        
        # TODO: Implement ticket redemption logic
        # For now, just show a message
        await interaction.response.send_message(
            f"🚧 Ticket redemption is being implemented!\n"
            f"You have 🎟️ {qty} tickets to redeem.",
            ephemeral=True,
        )

    @discord.ui.button(label="🎟️ Redeem x1", style=discord.ButtonStyle.success, row=0)
    async def redeem_single_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.redeem_tickets(interaction, 1)

    @discord.ui.button(label="🎟️ Redeem x10", style=discord.ButtonStyle.success, row=0)
    async def redeem_ten_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.redeem_tickets(interaction, 10)

    @discord.ui.button(label="🎟️ Redeem ALL", style=discord.ButtonStyle.danger, row=0)
    async def redeem_all_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.redeem_tickets(interaction, self.ticket_count)

    @discord.ui.button(label="🍻 Back", style=discord.ButtonStyle.secondary, row=1)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = tavern_main_embed(interaction.user.display_name)
        await interaction.response.edit_message(
            embed=embed,
            view=TavernMainView(self.owner_id, self.is_admin),
            attachments=[],
        )
