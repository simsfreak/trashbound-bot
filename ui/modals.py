import discord
from db.queries import save_contact_message

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
