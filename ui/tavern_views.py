# ═══════════════════════════════════════════════════════════════════
# THE TAVERN VIEWS
# ═══════════════════════════════════════════════════════════════════

import discord
from db import queries
from game.data import TAVERN_FOOD


class TavernMainView(discord.ui.View):
    """Main tavern view with all menu options."""
    def __init__(self, owner_id: int, is_admin: bool):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.is_admin = is_admin

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            return False
        return True

    @discord.ui.button(label="🍓 Food Shop", style=discord.ButtonStyle.primary, row=0)
    async def food_shop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        from ui.embeds import tavern_food_shop_embed
        embed = tavern_food_shop_embed()
        await interaction.response.edit_message(
            embed=embed,
            view=TavernFoodShopView(self.owner_id, self.is_admin),
            attachments=[],
        )

    @discord.ui.button(label="🎟️ Redeem Tickets", style=discord.ButtonStyle.success, row=0)
    async def redeem_tickets_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        from ui.embeds import tavern_ticket_redeem_embed
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
        from ui.views import show_profile
        await show_profile(interaction, self.owner_id, self.is_admin)


class TavernFoodShopView(discord.ui.View):
    """Food shop view for purchasing food."""
    def __init__(self, owner_id: int, is_admin: bool):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.is_admin = is_admin

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
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
        from ui.embeds import tavern_main_embed
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
        from ui.embeds import tavern_main_embed
        embed = tavern_main_embed(interaction.user.display_name)
        await interaction.response.edit_message(
            embed=embed,
            view=TavernMainView(self.owner_id, self.is_admin),
            attachments=[],
        )
