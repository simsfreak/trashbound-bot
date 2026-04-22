# ═══════════════════════════════════════════════════════════════════
# ZONE FARMING VIEWS - COMPLETE ZONE ACTIVITY SYSTEM
# ═══════════════════════════════════════════════════════════════════

import discord
import asyncio
import math
from db import queries
from game.zones import ZONES_META
from game.zone_logic import (
    simulate_zone_activity, get_stage_message, STAGE_MESSAGES,
    start_zone_session, get_active_zone_session, complete_zone_session,
    check_zone_cooldown, record_zone_action
)
from ui.embeds import (
    zone_selector_embed, zone_info_embed, zone_active_embed,
    zone_harvest_embed, zone_completion_embed, zone_cooldown_embed
)


class ZoneSelectorView(discord.ui.View):
    """Main zone selector showing all available zones."""
    
    def __init__(self, owner_id: int, is_admin: bool):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.is_admin = is_admin
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This zone selector isn't yours.", ephemeral=True)
            return False
        return True
    
    @discord.ui.button(label="🎣 Fishing", style=discord.ButtonStyle.primary, row=0)
    async def fishing_zone_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._enter_zone(interaction, "fishing")
    
    @discord.ui.button(label="🌿 Botany", style=discord.ButtonStyle.primary, row=0)
    async def botany_zone_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._enter_zone(interaction, "botany")
    
    @discord.ui.button(label="🏺 Archaeology", style=discord.ButtonStyle.primary, row=0)
    async def archaeology_zone_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._enter_zone(interaction, "archaeology")
    
    @discord.ui.button(label="♻️ Scavenge", style=discord.ButtonStyle.primary, row=1)
    async def scavenge_zone_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._enter_zone(interaction, "scavenge")
    
    @discord.ui.button(label="🏠 Back", style=discord.ButtonStyle.secondary, row=1)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        from ui.views import show_profile
        await show_profile(interaction, self.owner_id, self.is_admin)
    
    async def _enter_zone(self, interaction: discord.Interaction, zone_id: str):
        """Enter a zone - check if unlocked, then show zone page."""
        player = queries.get_player(interaction.user.id)
        zone = ZONES_META.get(zone_id)
        
        if not zone:
            await interaction.response.send_message("❌ Zone not found.", ephemeral=True)
            return
        
        # Check if unlocked
        if player["level"] < zone["unlock_level"]:
            await interaction.response.send_message(
                f"🔒 **{zone['name']}** unlocks at Level {zone['unlock_level']}\n"
                f"You're currently Level {player['level']}",
                ephemeral=True,
            )
            return
        
        # Check for active zone session
        active_zone = queries.get_zone_event(interaction.user.id, zone_id)
        
        if active_zone and active_zone["is_active"]:
            # Resume active zone
            await self._show_active_zone(interaction, zone_id, active_zone)
        else:
            # Show zone main page with mission data if it exists
            embed = zone_info_embed(zone_id, player["level"], active_zone)
            view = ZoneMainPageView(self.owner_id, self.is_admin, zone_id)
            await interaction.response.edit_message(embed=embed, view=view, attachments=[])
    
    async def _show_active_zone(self, interaction: discord.Interaction, zone_id: str, zone_event: dict):
        """Show active zone with mission progress."""
        zone = ZONES_META.get(zone_id)
        
        # Calculate time remaining
        from datetime import datetime
        started_at = datetime.fromisoformat(zone_event["started_at"].replace("Z", "+00:00"))
        now = datetime.utcnow().replace(tzinfo=started_at.tzinfo)
        elapsed = (now - started_at).total_seconds()
        time_remaining = max(0, int(3600 - elapsed))
        
        embed = zone_active_embed(zone_id, zone_event, time_remaining)
        view = ZoneActiveView(self.owner_id, self.is_admin, zone_id)
        await interaction.response.edit_message(embed=embed, view=view, attachments=[])


class ZoneMainPageView(discord.ui.View):
    """Zone main page showing details and allowing mission start."""
    
    def __init__(self, owner_id: int, is_admin: bool, zone_id: str):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.is_admin = is_admin
        self.zone_id = zone_id
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This zone isn't yours.", ephemeral=True)
            return False
        return True
    
    @discord.ui.button(label="⬅️ Easy", style=discord.ButtonStyle.secondary, row=0)
    async def difficulty_easy(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._start_mission(interaction, "Easy")
    
    @discord.ui.button(label="→ Medium", style=discord.ButtonStyle.secondary, row=0)
    async def difficulty_medium(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._start_mission(interaction, "Medium")
    
    @discord.ui.button(label="⚡ Hard", style=discord.ButtonStyle.secondary, row=0)
    async def difficulty_hard(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._start_mission(interaction, "Hard")
    
    @discord.ui.button(label="✅ Activate Mission", style=discord.ButtonStyle.success, row=1)
    async def activate_mission(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Default to Medium if not selected
        await self._start_mission(interaction, "Medium")
    
    @discord.ui.button(label="🏠 Back", style=discord.ButtonStyle.secondary, row=1)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = queries.get_player(interaction.user.id)
        embed = zone_selector_embed(player["level"], player.get("current_zone_id"))
        view = ZoneSelectorView(self.owner_id, self.is_admin)
        await interaction.response.edit_message(embed=embed, view=view, attachments=[])
    
    async def _start_mission(self, interaction: discord.Interaction, difficulty: str):
        """Start a new zone mission."""
        player = queries.get_player(interaction.user.id)
        
        # Check if already has active zone
        active_zone = queries.get_zone_event(interaction.user.id)
        if active_zone:
            await interaction.response.send_message(
                "❌ You already have an active zone session!\n"
                "Complete or abandon it before starting a new one.",
                ephemeral=True,
            )
            return
        
        # Start mission
        mission = await start_zone_session(interaction.user.id, self.zone_id, difficulty)
        
        # Show active zone page
        zone = ZONES_META.get(self.zone_id)
        embed = zone_active_embed(self.zone_id, mission, 3600)  # 1 hour = 3600 sec
        view = ZoneActiveView(self.owner_id, self.is_admin, self.zone_id)
        
        await interaction.response.edit_message(embed=embed, view=view, attachments=[])


class ZoneActiveView(discord.ui.View):
    """Active zone page with activity button and mission display."""
    
    def __init__(self, owner_id: int, is_admin: bool, zone_id: str):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.is_admin = is_admin
        self.zone_id = zone_id
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This zone isn't yours.", ephemeral=True)
            return False
        return True
    
    @discord.ui.button(label="🎣 Cast", style=discord.ButtonStyle.primary, row=0)
    async def activity_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Generic activity button - dynamically labeled for each zone."""
        zone = ZONES_META.get(self.zone_id)
        activity_verb = zone.get("activity_verb", "Activity")
        
        # Check cooldown
        cooldown_check = await check_zone_cooldown(interaction.user.id, self.zone_id)
        if cooldown_check["on_cooldown"]:
            embed = zone_cooldown_embed(self.zone_id, cooldown_check["remaining_sec"])
            await interaction.response.edit_message(embed=embed, view=self, attachments=[])
            return
        
        # Check if active zone is still valid
        active_zone = await get_active_zone_session(interaction.user.id, self.zone_id)
        if not active_zone or active_zone.get("expired"):
            # Session expired - show completion page
            embed = discord.Embed(
                title="⏰ Zone Session Expired",
                description="Your 1-hour window has closed. Click [Complete] to finalize rewards.",
                color=0xED4245,
            )
            view = ZoneExpiredView(self.owner_id, self.is_admin, self.zone_id)
            await interaction.response.edit_message(embed=embed, view=view, attachments=[])
            return
        
        # Perform activity
        result = await simulate_zone_activity(interaction.user.id, self.zone_id)
        
        # Record the action for cooldown
        await record_zone_action(interaction.user.id, self.zone_id)
        
        if result["success"]:
            # Show stage messages then result
            embed = discord.Embed(
                title=f"🎣 {activity_verb.upper()} - Stage 1",
                description=result["stage1_message"],
                color=0x5865F2,
            )
            await interaction.response.edit_message(embed=embed, view=None, attachments=[])
            await asyncio.sleep(1.0)
            
            embed = discord.Embed(
                title=f"🎣 {activity_verb.upper()} - Stage 2",
                description=result["stage2_message"],
                color=0x5865F2,
            )
            await interaction.edit_original_response(embed=embed)
            await asyncio.sleep(1.0)
            
            # Success result
            item = result.get("item", {})
            embed = zone_harvest_embed(item.get("id"), 1)
            await interaction.edit_original_response(embed=embed, view=self, attachments=[])
            
            # Update mission progress
            queries.add_zone_harvest(interaction.user.id, self.zone_id, item.get("id"))
        else:
            # Failure
            embed = discord.Embed(
                title=f"❌ {activity_verb} FAILED",
                description=result["final_message"],
                color=0xED4245,
            )
            await interaction.response.edit_message(embed=embed, view=self, attachments=[])
    
    @discord.ui.button(label="✅ Complete", style=discord.ButtonStyle.success, row=1)
    async def complete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Complete zone session and claim rewards."""
        active_zone = await get_active_zone_session(interaction.user.id, self.zone_id)
        if not active_zone:
            await interaction.response.send_message("No active zone session.", ephemeral=True)
            return
        
        rewards = await complete_zone_session(interaction.user.id, self.zone_id)
        embed = zone_completion_embed(self.zone_id, active_zone, rewards)
        
        # Back to zone selector
        view = BackToZoneSelector(self.owner_id, self.is_admin)
        await interaction.response.edit_message(embed=embed, view=view, attachments=[])
    
    @discord.ui.button(label="🏠 Back", style=discord.ButtonStyle.secondary, row=1)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = queries.get_player(interaction.user.id)
        embed = zone_selector_embed(player["level"], player.get("current_zone_id"))
        view = ZoneSelectorView(self.owner_id, self.is_admin)
        await interaction.response.edit_message(embed=embed, view=view, attachments=[])


class ZoneExpiredView(discord.ui.View):
    """View for expired zone session."""
    
    def __init__(self, owner_id: int, is_admin: bool, zone_id: str):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.is_admin = is_admin
        self.zone_id = zone_id
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This zone isn't yours.", ephemeral=True)
            return False
        return True
    
    @discord.ui.button(label="✅ Complete Mission", style=discord.ButtonStyle.success, row=0)
    async def complete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        active_zone = await get_active_zone_session(interaction.user.id, self.zone_id)
        if active_zone:
            rewards = await complete_zone_session(interaction.user.id, self.zone_id)
            embed = zone_completion_embed(self.zone_id, active_zone, rewards)
            view = BackToZoneSelector(self.owner_id, self.is_admin)
            await interaction.response.edit_message(embed=embed, view=view, attachments=[])
    
    @discord.ui.button(label="❌ Abandon", style=discord.ButtonStyle.danger, row=0)
    async def abandon_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        queries.complete_zone_event(interaction.user.id, self.zone_id)
        await interaction.response.send_message("Mission abandoned.", ephemeral=True)
        
        player = queries.get_player(interaction.user.id)
        embed = zone_selector_embed(player["level"], player.get("current_zone_id"))
        view = ZoneSelectorView(self.owner_id, self.is_admin)
        await interaction.response.edit_message(embed=embed, view=view, attachments=[])


class BackToZoneSelector(discord.ui.View):
    """Simple view to return to zone selector."""
    
    def __init__(self, owner_id: int, is_admin: bool):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.is_admin = is_admin
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            return False
        return True
    
    @discord.ui.button(label="🗺️ Back to Zones", style=discord.ButtonStyle.primary, row=0)
    async def back_zones(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = queries.get_player(interaction.user.id)
        embed = zone_selector_embed(player["level"], player.get("current_zone_id"))
        view = ZoneSelectorView(self.owner_id, self.is_admin)
        await interaction.response.edit_message(embed=embed, view=view, attachments=[])
    
    @discord.ui.button(label="🏠 Back to Profile", style=discord.ButtonStyle.secondary, row=0)
    async def back_profile(self, interaction: discord.Interaction, button: discord.ui.Button):
        from ui.views import show_profile
        await show_profile(interaction, self.owner_id, self.is_admin)


# For compatibility with existing code that references ZoneSelectorNewView
class ZoneSelectorNewView(ZoneSelectorView):
    """Alias for ZoneSelectorView for backward compatibility."""
    pass
