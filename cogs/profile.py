import discord
from discord import app_commands
from discord.ext import commands

from config import ADMIN_USER_IDS
from db import queries
from game.helpers import get_effect_remaining_text, get_recent_finds_from_inventory_rows
from game.data import ITEMS, get_live_events
from ui.embeds import profile_embed
from ui.views import ProfileView


class ProfileCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="profile", description="Open your main lobby")
    async def profile(self, interaction: discord.Interaction):
        queries.ensure_player(interaction.user.id, interaction.user.name)

        player = queries.get_player(interaction.user.id)
        inventory = queries.get_inventory(interaction.user.id)
        effects = queries.get_active_effects(interaction.user.id)
        equipment = queries.get_equipment(interaction.user.id)
        is_admin = interaction.user.id in ADMIN_USER_IDS

        weekend_event = None
        seasonal_event = None
        for event in get_live_events():
            if event.get("type") == "weekend" and weekend_event is None:
                weekend_event = f"{event.get('emoji', '')} {event.get('name', 'Weekend Event')}".strip()
            elif event.get("type") == "seasonal" and seasonal_event is None:
                seasonal_event = f"{event.get('emoji', '')} {event.get('name', 'Seasonal Event')}".strip()

        active_effect_lines = [
            f"{effect['label']} — {get_effect_remaining_text(effect['expires_at'])}"
            for effect in effects[:4]
        ]

        equipped_lines = []
        for entry in equipment[:4]:
            item = ITEMS.get(entry["item_id"], {"name": entry["item_id"], "emoji": "✨", "equip_bonus": ""})
            bonus = item.get("equip_bonus", "No passive listed")
            equipped_lines.append(f"{item.get('emoji', '✨')} {item['name']} — {bonus}")

        try:
            embed = profile_embed(
                player=player,
                inventory_count=sum(q for _, q in inventory),
                recent_finds=get_recent_finds_from_inventory_rows(inventory),
                active_effects=active_effect_lines,
                equipped_lines=equipped_lines,
                weekend_event=weekend_event,
                seasonal_event=seasonal_event,
                avatar_url=interaction.user.display_avatar.url,
            )
        except TypeError:
            embed = profile_embed(
                player=player,
                inventory_count=sum(q for _, q in inventory),
                recent_finds=get_recent_finds_from_inventory_rows(inventory),
                active_effects=effects,
                equipment=equipment,
                avatar_url=interaction.user.display_avatar.url,
            )

        await interaction.response.send_message(
            embed=embed,
            view=ProfileView(interaction.user.id, is_admin),
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(ProfileCog(bot))
