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
            return False
        return True
    
    @discord.ui.button(label="🎣 Fishing", style=discord.ButtonStyle.primary, row=0)
    async def fishing_zone_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            print(f"DEBUG: Fishing button clicked by {interaction.user.id}")
            await self._enter_zone(interaction, "fishing")
        except Exception as e:
            print(f"ERROR IN FISHING BUTTON: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            try:
                await interaction.response.send_message(f"🎣 Fishing Error: {str(e)}", ephemeral=True)
            except:
                await interaction.followup.send(f"🎣 Fishing Error: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label="🌿 Botany", style=discord.ButtonStyle.primary, row=0)
    async def botany_zone_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            print(f"DEBUG: Botany button clicked by {interaction.user.id}")
            await self._enter_zone(interaction, "botany")
        except Exception as e:
            print(f"ERROR IN BOTANY BUTTON: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            try:
                await interaction.response.send_message(f"🌿 Botany Error: {str(e)}", ephemeral=True)
            except:
                await interaction.followup.send(f"🌿 Botany Error: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label="🏺 Archaeology", style=discord.ButtonStyle.primary, row=0)
    async def archaeology_zone_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            print(f"DEBUG: Archaeology button clicked by {interaction.user.id}")
            await self._enter_zone(interaction, "archaeology")
        except Exception as e:
            print(f"ERROR IN ARCHAEOLOGY BUTTON: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            try:
                await interaction.response.send_message(f"🏺 Archaeology Error: {str(e)}", ephemeral=True)
            except:
                await interaction.followup.send(f"🏺 Archaeology Error: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label="♻️ Scavenge", style=discord.ButtonStyle.primary, row=1)
    async def scavenge_zone_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            print(f"DEBUG: Scavenge button clicked by {interaction.user.id}")
            await self._enter_zone(interaction, "scavenge")
        except Exception as e:
            print(f"ERROR IN SCAVENGE BUTTON: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            try:
                await interaction.response.send_message(f"♻️ Scavenge Error: {str(e)}", ephemeral=True)
            except:
                await interaction.followup.send(f"♻️ Scavenge Error: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label="🏠 Back", style=discord.ButtonStyle.secondary, row=1)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        print(f"DEBUG: Zone selector back button clicked")
        try:
            from ui.views import show_profile
            print(f"DEBUG: Imported show_profile")
            await show_profile(interaction, self.owner_id, self.is_admin)
            print(f"DEBUG: Called show_profile")
        except Exception as e:
            print(f"Error in ZoneSelectorView.back_button: {e}")
            import traceback
            traceback.print_exc()
            await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)
    
    async def _enter_zone(self, interaction: discord.Interaction, zone_id: str):
        """Enter a zone - check if unlocked, then show zone page."""
        print(f"\nDEBUG: _enter_zone called for zone_id='{zone_id}' (type: {type(zone_id).__name__}), user_id={interaction.user.id}")
        await interaction.response.defer()
        print(f"DEBUG: Deferred interaction")
        
        try:
            print(f"DEBUG: In try block for zone_id='{zone_id}'")
            print(f"DEBUG: About to call get_player with user_id={interaction.user.id}")
            player = queries.get_player(interaction.user.id)
            print(f"DEBUG: Got player: level={player.get('level')}, type={type(player)}")
            print(f"DEBUG: About to get ZONES_META for zone_id='{zone_id}'")
            zone = ZONES_META.get(zone_id)
            print(f"DEBUG: Got zone object, zone={zone is not None}, name={zone.get('name') if zone else 'NOT FOUND'}")
            
            if not zone:
                print(f"DEBUG: Zone '{zone_id}' NOT FOUND in ZONES_META")
                await interaction.followup.send("❌ Zone not found.", ephemeral=True)
                return
            
            # Check if unlocked
            unlock_level = zone.get("unlock_level")
            player_level = player.get("level")
            print(f"DEBUG: Checking unlock - player_level={player_level}, required={unlock_level}")
            if player_level < unlock_level:
                print(f"DEBUG: Zone locked for player")
                await interaction.followup.send(
                    f"🔒 **{zone['name']}** unlocks at Level {unlock_level}\n"
                    f"You're currently Level {player_level}",
                    ephemeral=True,
                )
                return
            
            print(f"DEBUG: Zone unlocked, checking for active session...")
            # Check for active zone session
            active_zone = queries.get_zone_event(interaction.user.id, zone_id)
            print(f"DEBUG: Active zone result: {active_zone is not None}")
            
            if active_zone and active_zone["is_active"]:
                print(f"DEBUG: Resuming active zone")
                # Resume active zone
                await self._show_active_zone(interaction, zone_id, active_zone)
            else:
                print(f"DEBUG: Showing zone main page")
                # Show zone main page with mission data if it exists
                embed = zone_info_embed(zone_id, player_level, active_zone)
                view = ZoneMainPageView(self.owner_id, self.is_admin, zone_id)
                print(f"DEBUG: Editing response with embed and view")
                await interaction.edit_original_response(embed=embed, view=view, attachments=[])
        except Exception as e:
            print(f"\n{'='*60}")
            print(f"ERROR in _enter_zone:")
            print(f"  Exception type: {type(e).__name__}")
            print(f"  Exception message: {str(e)}")
            print(f"  Zone ID: {zone_id}")
            print(f"  User ID: {interaction.user.id} (type: {type(interaction.user.id)})")
            print(f"{'='*60}\n")
            import traceback
            traceback.print_exc()
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
    
    async def _show_active_zone(self, interaction: discord.Interaction, zone_id: str, zone_event: dict):
        """Show active zone with mission progress."""
        try:
            zone = ZONES_META.get(zone_id)
            
            # Calculate time remaining from timer_end_at
            from datetime import datetime
            timer_end = datetime.fromisoformat(zone_event["timer_end_at"].replace("Z", "+00:00"))
            now = datetime.utcnow().replace(tzinfo=timer_end.tzinfo)
            time_remaining = max(0, int((timer_end - now).total_seconds()))
            
            embed = zone_active_embed(zone_id, zone_event, time_remaining)
            view = ZoneActiveView(self.owner_id, self.is_admin, zone_id)
            await interaction.edit_original_response(embed=embed, view=view, attachments=[])
        except Exception as e:
            print(f"Error in _show_active_zone: {e}")
            import traceback
            traceback.print_exc()
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)


class ZoneMainPageView(discord.ui.View):
    """Zone main page showing details and allowing mission start."""
    
    def __init__(self, owner_id: int, is_admin: bool, zone_id: str):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.is_admin = is_admin
        self.zone_id = zone_id
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:

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
        try:
            await interaction.response.defer()
            player = queries.get_player(interaction.user.id)
            embed = zone_selector_embed(player["level"])
            view = ZoneSelectorView(self.owner_id, self.is_admin)
            await interaction.edit_original_response(embed=embed, view=view, attachments=[])
        except Exception as e:
            print(f"Error in ZoneMainPageView.back_button: {e}")
            import traceback
            traceback.print_exc()
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
    
    async def _start_mission(self, interaction: discord.Interaction, difficulty: str):
        """Start a new zone mission."""
        await interaction.response.defer()
        
        try:
            player = queries.get_player(interaction.user.id)
            
            # Check if already has active zone in THIS zone
            active_zone = queries.get_zone_event(interaction.user.id, self.zone_id)
            if active_zone and active_zone.get("is_active"):
                await interaction.followup.send(
                    "❌ You already have an active mission in this zone!\n"
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
            
            await interaction.edit_original_response(embed=embed, view=view, attachments=[])
        except Exception as e:
            print(f"Error in ZoneMainPageView._start_mission: {e}")
            import traceback
            traceback.print_exc()
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)


class ZoneActiveView(discord.ui.View):
    """Active zone page with activity button and mission display."""
    
    def __init__(self, owner_id: int, is_admin: bool, zone_id: str):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.is_admin = is_admin
        self.zone_id = zone_id
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            return False
        return True
    
    @discord.ui.button(label="🎣 Cast", style=discord.ButtonStyle.primary, row=0)
    async def activity_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Generic activity button - dynamically labeled for each zone."""
        await interaction.response.defer()
        
        try:
            zone = ZONES_META.get(self.zone_id)
            activity_verb = zone.get("activity_verb", "Activity")
            
            # Check cooldown
            cooldown_check = await check_zone_cooldown(interaction.user.id, self.zone_id)
            if cooldown_check["on_cooldown"]:
                embed = zone_cooldown_embed(self.zone_id, cooldown_check["remaining_sec"])
                await interaction.edit_original_response(embed=embed, view=self, attachments=[])
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
                await interaction.edit_original_response(embed=embed, view=view, attachments=[])
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
                await interaction.edit_original_response(embed=embed, view=None, attachments=[])
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
                rarity = result.get("rarity", "Common")
                embed = zone_harvest_embed(self.zone_id, item.get("id"), rarity)
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
                await interaction.edit_original_response(embed=embed, view=self, attachments=[])
        except Exception as e:
            print(f"Error in ZoneActiveView.activity_button: {e}")
            import traceback
            traceback.print_exc()
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label="✅ Complete", style=discord.ButtonStyle.success, row=1)
    async def complete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Complete zone session and claim rewards."""
        await interaction.response.defer()
        
        try:
            active_zone = await get_active_zone_session(interaction.user.id, self.zone_id)
            if not active_zone:
                await interaction.followup.send("No active zone session.", ephemeral=True)
                return
            
            rewards = await complete_zone_session(interaction.user.id, self.zone_id)
            embed = zone_completion_embed(self.zone_id, active_zone, rewards)
            
            # Back to zone selector
            view = BackToZoneSelector(self.owner_id, self.is_admin)
            await interaction.edit_original_response(embed=embed, view=view, attachments=[])
        except Exception as e:
            print(f"Error in ZoneActiveView.complete_button: {e}")
            import traceback
            traceback.print_exc()
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label="🏠 Back", style=discord.ButtonStyle.secondary, row=1)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.defer()
            player = queries.get_player(interaction.user.id)
            embed = zone_selector_embed(player["level"])
            view = ZoneSelectorView(self.owner_id, self.is_admin)
            await interaction.edit_original_response(embed=embed, view=view, attachments=[])
        except Exception as e:
            print(f"Error in ZoneActiveView.back_button: {e}")
            import traceback
            traceback.print_exc()
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)


class ZoneExpiredView(discord.ui.View):
    """View for expired zone session."""
    
    def __init__(self, owner_id: int, is_admin: bool, zone_id: str):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.is_admin = is_admin
        self.zone_id = zone_id
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            return False
        return True
    
    @discord.ui.button(label="✅ Complete Mission", style=discord.ButtonStyle.success, row=0)
    async def complete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        try:
            active_zone = await get_active_zone_session(interaction.user.id, self.zone_id)
            if active_zone:
                rewards = await complete_zone_session(interaction.user.id, self.zone_id)
                embed = zone_completion_embed(self.zone_id, active_zone, rewards)
                view = BackToZoneSelector(self.owner_id, self.is_admin)
                await interaction.edit_original_response(embed=embed, view=view, attachments=[])
        except Exception as e:
            print(f"Error in ZoneExpiredView.complete_button: {e}")
            import traceback
            traceback.print_exc()
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label="❌ Abandon", style=discord.ButtonStyle.danger, row=0)
    async def abandon_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        try:
            queries.complete_zone_event(interaction.user.id, self.zone_id)
            
            player = queries.get_player(interaction.user.id)
            embed = zone_selector_embed(player["level"])
            view = ZoneSelectorView(self.owner_id, self.is_admin)
            await interaction.edit_original_response(embed=embed, view=view, attachments=[])
        except Exception as e:
            print(f"Error in ZoneExpiredView.abandon_button: {e}")
            import traceback
            traceback.print_exc()
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)


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
        try:
            await interaction.response.defer()
            player = queries.get_player(interaction.user.id)
            embed = zone_selector_embed(player["level"])
            view = ZoneSelectorView(self.owner_id, self.is_admin)
            await interaction.edit_original_response(embed=embed, view=view, attachments=[])
        except Exception as e:
            print(f"Error in BackToZoneSelector.back_zones: {e}")
            import traceback
            traceback.print_exc()
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label="🏠 Back to Profile", style=discord.ButtonStyle.secondary, row=0)
    async def back_profile(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            from ui.views import show_profile
            await show_profile(interaction, self.owner_id, self.is_admin)
        except Exception as e:
            print(f"Error in BackToZoneSelector.back_profile: {e}")
            import traceback
            traceback.print_exc()
            await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)


# For compatibility with existing code that references ZoneSelectorNewView
class ZoneSelectorNewView(ZoneSelectorView):
    """Alias for ZoneSelectorView for backward compatibility."""
    pass
