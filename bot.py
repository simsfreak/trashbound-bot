import logging
import discord
from discord.ext import commands

from config import DISCORD_TOKEN, GUILD_ID
from db.database import run_schema

logging.basicConfig(level=logging.INFO)

TEST_GUILD = discord.Object(id=int(GUILD_ID))
intents = discord.Intents.default()

INITIAL_EXTENSIONS = [
    "cogs.profile",
]

class TrashboundBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        run_schema()

        for ext in INITIAL_EXTENSIONS:
            await self.load_extension(ext)

        synced = await self.tree.sync(guild=TEST_GUILD)
        logging.info(f"Synced {len(synced)} commands to guild")

    async def on_ready(self):
        logging.info(f"Logged in as {self.user}")

bot = TrashboundBot()
bot.run(DISCORD_TOKEN)

TEST_GUILD = discord.Object(id=int(GUILD_ID))
intents = discord.Intents.default()

user_data = {}

loot_table = [
    ("Old Shoe", 5, "Common"),
    ("Scrap Metal", 10, "Common"),
    ("Broken Phone", 25, "Rare"),
    ("Mystery Box", 50, "Epic"),
    ("Legendary Trash Crown 👑", 200, "Legendary"),
]

colors = {
    "Common": 0x95A5A6,
    "Rare": 0x3498DB,
    "Epic": 0x9B59B6,
    "Legendary": 0xF1C40F,
}


def get_player(user: discord.abc.User) -> dict:
    user_id = str(user.id)
    if user_id not in user_data:
        user_data[user_id] = {
            "coins": 0,
            "inventory": [],
            "level": 1,
            "zone": "Back Alley",
            "title": "Trash Rookie",
            "last_dive": 0,
        }
    return user_data[user_id]


def update_title(data: dict) -> None:
    if data["coins"] > 500:
        data["title"] = "Dumpster Diver 👑"
    elif data["coins"] > 100:
        data["title"] = "Trash Hunter"
    else:
        data["title"] = "Trash Rookie"


def build_profile_embed(user: discord.abc.User) -> discord.Embed:
    data = get_player(user)
    update_title(data)

    embed = discord.Embed(
        title=f"{user.display_name} — {data['title']}",
        description="Your dumpster diving profile",
    )
    embed.add_field(name="💰 Coins", value=str(data["coins"]), inline=True)
    embed.add_field(name="⭐ Level", value=str(data["level"]), inline=True)
    embed.add_field(name="📍 Zone", value=data["zone"], inline=True)
    embed.add_field(name="🎒 Inventory Items", value=str(len(data["inventory"])), inline=False)

    highlights = data["inventory"][-3:] if data["inventory"] else ["Nothing yet"]
    embed.add_field(
        name="Recent Finds",
        value="\n".join(f"- {item}" for item in highlights),
        inline=False,
    )
    return embed


class ProfileView(discord.ui.View):
    def __init__(self, owner_id: int):
        super().__init__(timeout=300)
        self.owner_id = owner_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "This profile menu isn't yours. Use /profile to open your own.",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(label="Dive", emoji="🗑️", style=discord.ButtonStyle.primary)
    async def dive_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = get_player(interaction.user)

        if time.time() - data["last_dive"] < 5:
            await interaction.response.send_message(
                "⏳ You need to catch your breath before diving again...",
                ephemeral=True,
            )
            return

        data["last_dive"] = time.time()

        item, value, rarity = random.choice(loot_table)
        data["coins"] += value
        data["inventory"].append(item)
        update_title(data)

        embed = build_profile_embed(interaction.user)
        embed.color = colors.get(rarity, 0xFFFFFF)
        embed.description = (
            f"🗑️ You dig through the trash...\n"
            f"🪤 Something smells terrible...\n\n"
            f"✨ You found **{item}** ({rarity})!\n"
            f"💰 +{value} coins"
        )

        await interaction.response.edit_message(
            embed=embed,
            view=ProfileView(interaction.user.id),
        )

    @discord.ui.button(label="Inventory", emoji="🎒", style=discord.ButtonStyle.secondary)
    async def inventory_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = get_player(interaction.user)

        if data["inventory"]:
            inventory_text = "\n".join(f"- {item}" for item in data["inventory"][-10:])
        else:
            inventory_text = "Your inventory is empty."

        embed = discord.Embed(
            title=f"{interaction.user.display_name}'s Inventory",
            description=inventory_text,
        )
        embed.add_field(name="Total Items", value=str(len(data["inventory"])))
        embed.add_field(name="Coins", value=str(data["coins"]))

        await interaction.response.edit_message(
            embed=embed,
            view=ProfileView(interaction.user.id),
        )

    @discord.ui.button(label="Sell", emoji="💰", style=discord.ButtonStyle.success)
    async def sell_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = get_player(interaction.user)

        if not data["inventory"]:
            await interaction.response.send_message(
                "You have nothing to sell.",
                ephemeral=True,
            )
            return

        sold_count = len(data["inventory"])
        sell_value = sold_count * 3
        data["coins"] += sell_value
        data["inventory"].clear()
        update_title(data)

        embed = build_profile_embed(interaction.user)
        embed.description = f"💰 You sold {sold_count} item(s) for {sell_value} coins."

        await interaction.response.edit_message(
            embed=embed,
            view=ProfileView(interaction.user.id),
        )

    @discord.ui.button(label="Travel", emoji="🧭", style=discord.ButtonStyle.secondary)
    async def travel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = get_player(interaction.user)

        zones = ["Back Alley", "Apartment Bins", "Mall Rear Lot", "Restaurant Dumpster"]
        current_index = zones.index(data["zone"])
        next_index = (current_index + 1) % len(zones)
        data["zone"] = zones[next_index]

        embed = build_profile_embed(interaction.user)
        embed.description = f"🧭 You traveled to **{data['zone']}**."

        await interaction.response.edit_message(
            embed=embed,
            view=ProfileView(interaction.user.id),
        )

    @discord.ui.button(label="Refresh", emoji="🪪", style=discord.ButtonStyle.secondary)
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = build_profile_embed(interaction.user)
        await interaction.response.edit_message(
            embed=embed,
            view=ProfileView(interaction.user.id),
        )


class TrashboundBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.tree.clear_commands(guild=TEST_GUILD)
        self.tree.add_command(ping, guild=TEST_GUILD)
        self.tree.add_command(profile, guild=TEST_GUILD)
        self.tree.add_command(dive, guild=TEST_GUILD)
        synced = await self.tree.sync(guild=TEST_GUILD)
        logging.info(f"Synced {len(synced)} commands to guild")


bot = TrashboundBot()


@bot.event
async def on_ready():
    logging.info(f"Logged in as {bot.user}")


@app_commands.command(name="ping", description="Check if the bot is alive")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("pong 🗑️")


@app_commands.command(name="profile", description="Open your dumpster diving profile")
async def profile(interaction: discord.Interaction):
    get_player(interaction.user)
    embed = build_profile_embed(interaction.user)
    await interaction.response.send_message(
        embed=embed,
        view=ProfileView(interaction.user.id),
        ephemeral=False,
    )


@app_commands.command(name="dive", description="Search a dumpster for loot")
async def dive(interaction: discord.Interaction):
    data = get_player(interaction.user)

    if time.time() - data["last_dive"] < 5:
        await interaction.response.send_message(
            "⏳ You need to catch your breath before diving again...",
            ephemeral=True,
        )
        return

    data["last_dive"] = time.time()

    item, value, rarity = random.choice(loot_table)
    data["coins"] += value
    data["inventory"].append(item)
    update_title(data)

    embed = discord.Embed(
        description=(
            f"🗑️ You dig through the trash...\n"
            f"🪤 Something smells terrible...\n\n"
            f"✨ You found **{item}** ({rarity})!\n"
            f"💰 +{value} coins\n"
            f"💰 Total coins: {data['coins']}"
        ),
        color=colors.get(rarity, 0xFFFFFF),
    )

    await interaction.response.send_message(embed=embed)


bot.run(TOKEN)
