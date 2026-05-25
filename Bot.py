import discord, os, yt_dlp
from discord.ext import commands
from keep_alive import keep_alive

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=">", intents=intents, help_command=None)

@bot.event
async def on_ready():
    await bot.tree.sync() # Slash commands sync
    print(f"✅ {bot.user.name} is fresh and ready!")

@bot.hybrid_command(name="ping", description="Check latency")
async def ping(ctx):
    await ctx.send(f"🏓 Pong! {round(bot.latency * 1000)}ms")

# यहाँ से हम एक-एक करके नई कमांड्स जोड़ेंगे
keep_alive()
bot.run(os.getenv('DISCORD_TOKEN'))
