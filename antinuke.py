import discord
from discord import app_commands
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=">", intents=intents)

# एंटी-न्यूक स्टेटस स्टोर करने के लिए एक वेरिएबल
antinuke_status = False

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'बोट ऑनलाइन है: {bot.user}')

# --- Antinuke Slash Commands ---
@bot.tree.command(name="antinuke", description="एंटी-न्यूक सिस्टम को चालू या बंद करें")
@app_commands.describe(action="enable या disable चुनें")
@app_commands.choices(action=[
    app_commands.Choice(name="Enable", value="enable"),
    app_commands.Choice(name="Disable", value="disable")
])
async def antinuke(interaction: discord.Interaction, action: str):
    global antinuke_status
    
    if action == "enable":
        antinuke_status = True
        await interaction.response.send_message("✅ एंटी-न्यूक सिस्टम चालू कर दिया गया है।")
    else:
        antinuke_status = False
        await interaction.response.send_message("❌ एंटी-न्यूक सिस्टम बंद कर दिया गया है।")

bot.run('YOUR_BOT_TOKEN_HERE')
