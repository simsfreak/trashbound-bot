import discord

from db.queries import save_contact_message, grant_player_xp, grant_player_coins, grant_player_tickets, add_item_to_inventory


class ContactAdminModal(discord.ui.Modal, title="Contact Admin"):
    subject = discord.ui.TextInput(label="Subject", max_length=100)
    message = discord.ui.TextInput(label="Message", style=discord.TextStyle.paragraph, max_length=1000)

    async def on_submit(self, interaction: discord.Interaction):
        save_contact_message(
            user_id=interaction.user.id,
            username=interaction.user.name,
            subject=str(self.subject),
            message=str(self.message),
        )
        await interaction.response.send_message("Your message was sent to admin.", ephemeral=True)


class GrantXPModal(discord.ui.Modal, title="Grant XP"):
    user_id = discord.ui.TextInput(label="User ID", max_length=20)
    xp_amount = discord.ui.TextInput(label="XP Amount", max_length=10)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id = int(self.user_id)
            xp_amount = int(self.xp_amount)
            
            if grant_player_xp(user_id, xp_amount):
                await interaction.response.send_message(
                    f"✅ Granted {xp_amount} XP to user {user_id}",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"❌ User {user_id} not found",
                    ephemeral=True
                )
        except ValueError:
            await interaction.response.send_message(
                "❌ Invalid input. User ID and XP must be numbers.",
                ephemeral=True
            )


class GrantCoinsModal(discord.ui.Modal, title="Grant Coins"):
    user_id = discord.ui.TextInput(label="User ID", max_length=20)
    coins_amount = discord.ui.TextInput(label="Coins Amount", max_length=10)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id = int(self.user_id)
            coins_amount = int(self.coins_amount)
            
            if grant_player_coins(user_id, coins_amount):
                await interaction.response.send_message(
                    f"✅ Granted {coins_amount} coins to user {user_id}",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"❌ User {user_id} not found",
                    ephemeral=True
                )
        except ValueError:
            await interaction.response.send_message(
                "❌ Invalid input. User ID and coins must be numbers.",
                ephemeral=True
            )


class GrantTicketsModal(discord.ui.Modal, title="Grant Tickets"):
    user_id = discord.ui.TextInput(label="User ID", max_length=20)
    tickets_amount = discord.ui.TextInput(label="Tickets Amount", max_length=10)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id = int(self.user_id)
            tickets_amount = int(self.tickets_amount)
            
            if grant_player_tickets(user_id, tickets_amount):
                await interaction.response.send_message(
                    f"✅ Granted {tickets_amount} tickets to user {user_id}",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"❌ User {user_id} not found",
                    ephemeral=True
                )
        except ValueError:
            await interaction.response.send_message(
                "❌ Invalid input. User ID and tickets must be numbers.",
                ephemeral=True
            )


class GrantItemsModal(discord.ui.Modal, title="Grant Items"):
    user_id = discord.ui.TextInput(label="User ID", max_length=20)
    item_id = discord.ui.TextInput(label="Item ID", max_length=50)
    quantity = discord.ui.TextInput(label="Quantity", max_length=5, default="1")

    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id = int(self.user_id)
            qty = int(self.quantity)
            
            add_item_to_inventory(user_id, str(self.item_id), qty)
            await interaction.response.send_message(
                f"✅ Granted {qty}x {self.item_id} to user {user_id}",
                ephemeral=True
            )
        except ValueError:
            await interaction.response.send_message(
                "❌ Invalid input. User ID and quantity must be numbers.",
                ephemeral=True
            )
