"""
ROOT NAVIGATION SYSTEM

Provides consistent navigation buttons for all screens.
All views should include these 8 core buttons for consistency.
"""

import discord
from ui.ui_config import ACTION_BUTTONS


def get_root_nav_buttons(row: int = 1) -> list:
    """
    Get all 8 root navigation buttons in a list.
    
    Returns:
        List of 8 Button objects for the core actions
    """
    buttons = [
        ScavengeButton(row=row),
        InventoryButton(row=row),
        CraftButton(row=row),
        ShelterButton(row=row + 1),
        NetworkButton(row=row + 1),
        ContractsButton(row=row + 1),
        MapButton(row=row + 2),
        StoryButton(row=row + 2),
    ]
    return buttons


class NavigationButton(discord.ui.Button):
    """Base class for navigation buttons."""
    
    def __init__(self, emoji: str, label: str, action: str, row: int = 1):
        super().__init__(
            emoji=emoji,
            label=label,
            style=discord.ButtonStyle.primary,
            custom_id=f"nav_{action}",
            row=row,
        )
        self.action = action


class ScavengeButton(NavigationButton):
    """🧭 Scavenge button."""
    
    def __init__(self, row: int = 1):
        super().__init__("🧭", "Scavenge", "scavenge", row)
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        # To be implemented in main game logic
        pass


class InventoryButton(NavigationButton):
    """🎒 Inventory button."""
    
    def __init__(self, row: int = 1):
        super().__init__("🎒", "Inventory", "inventory", row)
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        # To be implemented in main game logic
        pass


class CraftButton(NavigationButton):
    """⚒️ Craft button."""
    
    def __init__(self, row: int = 1):
        super().__init__("⚒️", "Craft", "craft", row)
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        # To be implemented in main game logic
        pass


class ShelterButton(NavigationButton):
    """🏚️ Shelter button."""
    
    def __init__(self, row: int = 2):
        super().__init__("🏚️", "Shelter", "shelter", row)
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        # To be implemented in main game logic
        pass


class NetworkButton(NavigationButton):
    """📡 Network button."""
    
    def __init__(self, row: int = 2):
        super().__init__("📡", "Network", "network", row)
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        # To be implemented in main game logic
        pass


class ContractsButton(NavigationButton):
    """📜 Contracts button."""
    
    def __init__(self, row: int = 2):
        super().__init__("📜", "Contracts", "contracts", row)
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        # To be implemented in main game logic
        pass


class MapButton(NavigationButton):
    """🗺️ Map button."""
    
    def __init__(self, row: int = 3):
        super().__init__("🗺️", "Map", "map", row)
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        # To be implemented in main game logic
        pass


class StoryButton(NavigationButton):
    """📖 Story button."""
    
    def __init__(self, row: int = 3):
        super().__init__("📖", "Story", "story", row)
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        # To be implemented in main game logic
        pass
