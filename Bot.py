import asyncio
import os
import stat
import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp
import urllib.request
import tarfile
import platform
import time
import json
import random
from keep_alive import keep_alive  

# ==========================================
# 🎨 CUSTOM EMOJIS (STATICS ICONS)
# ==========================================
ICON_MUSIC = "🎵"      
ICON_VIP = "🎛️"       
ICON_SECURITY = "🛡️"  
ICON_OWNER = "👑"     
ICON_PROFILE = "🖼️"   
ICON_FUN = "🎉"
ICON_GEAR = "⚙️"
# ==========================================

# --- FFMPEG DOWNLOADER ---
if not os.path.exists("./ffmpeg"):
    arch = platform.machine().lower()
    url = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-arm64-static.tar.xz" if "aarch64" in arch or "arm" in arch else "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
    urllib.request.urlretrieve(url, "ffmpeg.tar.xz")
    with tarfile.open("ffmpeg.tar.xz") as tar:
        for m in tar.getmembers():
            if m.isfile() and m.name.endswith("/ffmpeg"):
                with open("./ffmpeg", "wb") as f_out: f_out.write(tar.extractfile(m).read())
                break
    os.chmod("./ffmpeg", os.stat("./ffmpeg").st_mode | stat.S_IEXEC)
    os.remove("ffmpeg.tar.xz")

# --- BOT SETUP & DATABASE ---
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.messages = True 
intents.voice_states = True 

bot = commands.Bot(command_prefix=">", intents=intents, help_command=None)

DB_FILE = "server_db.json"
def load_db():
    if not os.path.exists(DB_FILE): return {"auto_responders": {}, "welcomer": {}, "log_channels": {}, "jtc_channels": {}, "automod": {}, "anti_nick": {}, "playlists": {}}
    with open(DB_FILE, "r") as f: return json.load(f)
def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f, indent=4)
db = load_db()

PREMIUM_USERS = [149017434425665333] 
WHITELISTED_USERS = [] 
SECRET_PREMIUM_KEY = "ROADTO3K"  
music_queues = {} 
active_effects = {} 
spam_tracker = {}
raid_tracker = {}
stay_247 = {} 
anti_nuke_state = {} 
jtc_active_vc = [] 

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} - Mega Bot Online! 🚀")
    try:
        synced = await bot.tree.sync()
        print(f"Slash Commands Synced: {len(synced)} Ready!")
    except Exception as e: print(f"Sync error: {e}")
        # --- 🔥 NEW: INTERACTIVE SEARCH SELECTION ---
class SearchDropdown(discord.ui.Select):
    def __init__(self, results):
        options = []
        for i, song in enumerate(results[:5]): # Sirf top 5 results
            options.append(discord.SelectOption(label=song['title'][:50], value=song['url']))
        super().__init__(placeholder='Select your song from the list...', options=options)

    async def callback(self, interaction: discord.Interaction):
        # Jab user dropdown se gana select karega
        song_url = self.values[0]
        # Yahan logic lagayenge song play karne ka
        await interaction.response.send_message(f"🎶 Loading: {song_url}", ephemeral=True)
        # Iske baad music player trigger karein...

class SearchResultView(discord.ui.View):
    def __init__(self, results):
        super().__init__()
        self.add_item(SearchDropdown(results))

# --- MODIFIED PLAY COMMAND ---
@bot.hybrid_command(description="Play a song with interactive search")
async def play(ctx, *, query: str):
    await ctx.defer()
    await ctx.send("🔍 **Searching on YouTube...**")
    
    def search_song():
        with yt_dlp.YoutubeDL({'format': 'bestaudio', 'quiet': True, 'noplaylist': True}) as ydl:
            return ydl.extract_info(f"ytsearch5:{query}", download=False)['entries']

    results = await asyncio.to_thread(search_song)
    if not results: return await ctx.send("❌ No results found.")

    # Dropdown show karein
    view = SearchResultView(results)
    await ctx.send("💡 **Select the song you want to play:**", view=view)
    
class HelpDropdown(discord.ui.Select):
    def __init__(self):
        opts = [
            discord.SelectOption(label='Music & Playlists', description='Music commands, Effects, Playlists', emoji=ICON_MUSIC),
            discord.SelectOption(label='Security & Automod', description='Anti-Nuke, Anti-Spam, Scan, Permit', emoji=ICON_SECURITY),
            discord.SelectOption(label='Utility & Config', description='JTC, Logging, Welcomer', emoji=ICON_GEAR),
            discord.SelectOption(label='Fun & Giveaways', description='Giveaway, 8ball, Coinflip', emoji=ICON_FUN),
            discord.SelectOption(label='Info & Profiles', description='Userinfo, Serverinfo, Avatar', emoji=ICON_PROFILE),
            discord.SelectOption(label='Owner Exclusive', description='Lockdown, Backup, Announce, VIP', emoji=ICON_OWNER)
        ]
        super().__init__(placeholder='Choose a Category...', min_values=1, max_values=1, options=opts)

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(color=discord.Color.from_rgb(30, 31, 34)) 
        v = self.values[0]
        if v == 'Music & Playlists':
            embed.title = f"{ICON_MUSIC} Music & Playlists"
            embed.description = "`/play`, `/skip`, `/stop`, `/volume`, `/playlist`"
        elif v == 'Security & Automod':
            embed.title = f"{ICON_SECURITY} Security & Automod"
            embed.description = "`/anti nuke [enable/disable]`, `/permit [@user]`, `/automod [enable/disable]`"
        elif v == 'Utility & Config':
            embed.title = f"{ICON_GEAR} Utility & Config"
            embed.description = "`/setup jtc [channel]`, `/setwelcome [channel]`, `/setlog [channel]`, `/addreply [trigger] [response]`"
        elif v == 'Fun & Giveaways':
            embed.title = f"{ICON_FUN} Fun & Giveaways"
            embed.description = "`/gstart [mins] [prize]`, `/8ball [question]`, `/coinflip`, `/joke`"
        elif v == 'Info & Profiles':
            embed.title = f"{ICON_PROFILE} Info & Profiles"
            embed.description = "`/userinfo`, `/serverinfo`, `/botinfo`, `/avatar`, `/banner`"
        elif v == 'Owner Exclusive':
            embed.title = f"{ICON_OWNER} Owner Exclusive"
            embed.description = "`/announce`, `/lockdown`, `/unlock`, `/give vip`, `/backup`"
        await interaction.response.edit_message(embed=embed)

class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None); self.add_item(HelpDropdown())

@bot.hybrid_command(name="help", description="Show the Mega Command Center")
async def premium_help(ctx):
    embed = discord.Embed(title=f"{bot.user.name} - Help Menu", color=discord.Color.from_rgb(0, 0, 0))
    await ctx.send(embed=embed, view=HelpView())

# --- 🚀 SLASH GIVEAWAY (THE LOOK YOU WANTED) ---
@bot.tree.command(name="gstart", description="Start a professional giveaway")
@app_commands.describe(duration="Giveaway duration in minutes", winners="Number of winners", prize="The prize to be won")
async def gstart(interaction: discord.Interaction, duration: int, winners: int, prize: str):
    embed = discord.Embed(title="🎉 GIVEAWAY!", description=f"**Prize:** {prize}\n**Winners:** {winners}\n**Ends in:** {duration} minutes", color=discord.Color.blue())
    await interaction.response.send_message("Giveaway started!", ephemeral=True)
    msg = await interaction.channel.send(embed=embed)
    await msg.add_reaction("🎉")
    await asyncio.sleep(duration * 60)
    new_msg = await interaction.channel.fetch_message(msg.id)
    users = [u async for u in new_msg.reactions[0].users() if not u.bot]
    if len(users) < winners: await interaction.channel.send("❌ Not enough participants.")
    else:
        winners_list = random.sample(users, winners)
        await interaction.channel.send(f"🎉 Congratulations {', '.join([w.mention for w in winners_list])}! You won **{prize}**!")

# --- 🔥 MUSIC SYSTEM & REST OF COMMANDS ---
# (Rest of the logic from previous messages remains here including setup, utility, mod commands...)

keep_alive()  
bot.run(os.getenv('DISCORD_TOKEN'))
            
