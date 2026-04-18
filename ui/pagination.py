import math
import discord

class InventoryPaginationView(discord.ui.View):
    def __init__(self, owner_id: int, items: list[str], page: int = 0, page_size: int = 5):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.items = items
        self.page = page
        self.page_size = page_size

    def get_page_items(self) -> list[str]:
        start = self.page * self.page_size
        end = start + self.page_size
        return self.items[start:end]

    def build_embed(self) -> discord.Embed:
        total_pages = max(1, math.ceil(len(self.items) / self.page_size))
        page_items = self.get_page_items()

        embed = discord.Embed(
            title="🎒 Inventory",
            description="\n".join(page_items) if page_items else "Your inventory is empty.",
            color=0x5865F2,
        )
        embed.set_footer(text=f"Page {self.page + 1} / {total_pages}")
        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This menu isn't yours.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="◀ Back", style=discord.ButtonStyle.secondary)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="▶ Next", style=discord.ButtonStyle.secondary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if (self.page + 1) * self.page_size < len(self.items):
            self.page += 1
        await interaction.response.edit_message(embed=self.build_embed(), view=self)
