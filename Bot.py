import asyncio, os, discord, random, yt_dlp
from discord import app_commands
from discord.ext import commands
from keep_alive import keep_alive


# 1. Intents सेट करें
intents = discord.Intents.default()
intents.message_content = True

# 2. बॉट सेटअप (Prefix के साथ)
bot = commands.Bot(command_prefix=">", intents=intents)

@bot.event
async def on_ready():
    # स्लैश कमांड्स को सिंक करें
    await bot.tree.sync()
    print(f'बोट ऑनलाइन है: {bot.user}')


keep_alive()
bot.run(os.getenv('DISCORD_TOKEN'))

