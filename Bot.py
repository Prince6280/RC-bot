import asyncio, os, discord, random, yt_dlp
from discord import app_commands
from discord.ext import commands
from keep_alive import keep_alive

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=">", intents=intents, help_command=None)
FFMPEG_PATH = "/usr/bin/ffmpeg"

# --- DROPEDOWN HELP MENU ---
class HelpDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label='Music', description='Play, Stop, Skip', emoji='🎵'),
            discord.SelectOption(label='Security', description='Antinuke, Automod, Antinick', emoji='🛡️'),
            discord.SelectOption(label='Utility', description='JTC, Auto-responder, Audit Logs', emoji='⚙️'),
            discord.SelectOption(label='Fun/Giveaway', description='Gstart, 8ball, Fun', emoji='🎉'),
        ]
        super().__init__(placeholder='Choose a Category...', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(title=f"{self.values[0]} Commands", color=discord.Color.blurple())
        if self.values[0] == 'Music': embed.description = "/play, /stop"
        elif self.values[0] == 'Security': embed.description = "/antinuke, /automod, /antinick"
        elif self.values[0] == 'Utility': embed.description = "/jtc, /auditlogs, /customrole"
        elif self.values[0] == 'Fun/Giveaway': embed.description = "/gstart"
        await interaction.response.edit_message(embed=embed)

class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(HelpDropdown())

# --- ALL COMMANDS ---
@bot.hybrid_command(name="help")
async def help(ctx):
    embed = discord.Embed(title="Oliver Help Menu", description="Select a category!", color=0x2f3136)
    await ctx.send(embed=embed, view=HelpView())

@bot.tree.command(name="antinuke", description="Toggle Anti-Nuke")
async def antinuke(interaction: discord.Interaction, state: str):
    await interaction.response.send_message(f"🛡️ Anti-Nuke: {state.upper()}")

@bot.tree.command(name="automod", description="Toggle Auto-Mod")
async def automod(interaction: discord.Interaction, state: str):
    await interaction.response.send_message(f"🛡️ Auto-Mod: {state.upper()}")

@bot.tree.command(name="jtc", description="Setup JTC Voice")
async def jtc(interaction: discord.Interaction, channel: discord.VoiceChannel):
    await interaction.response.send_message(f"✅ JTC set to {channel.name}")

@bot.tree.command(name="antinick", description="Enable/Disable Anti-Nick")
async def antinick(interaction: discord.Interaction, state: str):
    await interaction.response.send_message(f"🛡️ Anti-Nick: {state.upper()}")

@bot.tree.command(name="gstart", description="Start a giveaway")
async def gstart(interaction: discord.Interaction, duration: int, winners: int, prize: str):
    await interaction.response.send_message("🎉 Giveaway started!", ephemeral=True)
    msg = await interaction.channel.send(f"🎉 **GIVEAWAY: {prize}**")
    await msg.add_reaction("🎉")

# --- PROXY LIST (Ek valid HTTP proxy yahan paste karein) ---
# Tip: ProxyScrape se "HTTP" proxy uthayein aur yahan rakhein
PROXY_URL = "http://103.152.112.50:8080" 

# --- MUSIC ENGINE WITH PROXY & QUEUE ---
async def play_next(ctx):
    if ctx.guild.id in music_queues and len(music_queues[ctx.guild.id]) > 0:
        song = music_queues[ctx.guild.id].pop(0)
        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(song['url'], executable=FFMPEG_PATH))
        ctx.voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
        await ctx.send(f"▶️ Playing: **{song['title']}**")
    else:
        await ctx.send("🎶 Queue khatam!")

@bot.hybrid_command(description="Play music with Proxy")
async def play(ctx, *, query: str):
    await ctx.defer()
    if not ctx.author.voice: return await ctx.send("❌ Join VC!")
    
    if ctx.voice_client is None: await ctx.author.voice.channel.connect()
    else: await ctx.voice_client.move_to(ctx.author.voice.channel)
    
    if ctx.guild.id not in music_queues: music_queues[ctx.guild.id] = []
    
    # Proxy-Powered Search
    ydl_opts = {
        'format': 'bestaudio', 'quiet': True, 'noplaylist': True,
        'proxy': PROXY_URL,
        'user_agent': 'Mozilla/5.0'
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch:{query}", download=False)
            song = info['entries'][0]
            music_queues[ctx.guild.id].append(song)
            await ctx.send(f"📝 Added: **{song['title']}**")
            if not ctx.voice_client.is_playing(): await play_next(ctx)
        except Exception as e: await ctx.send(f"❌ Proxy/Search Error: {e}")

@bot.hybrid_command(description="Skip current song")
async def skip(ctx):
    if ctx.voice_client: ctx.voice_client.stop(); await ctx.send("⏭️ Skipped!")

# --- DROPEDOWN HELP (Wahi 'Cassette' jaisa style) ---
class HelpDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label='Music', description='Play, Skip, Stop', emoji='🎵'),
            discord.SelectOption(label='Security', description='Antinuke, Automod', emoji='🛡️'),
            discord.SelectOption(label='Giveaway', description='Gstart', emoji='🎉')
        ]
        super().__init__(placeholder='Choose a Category...', options=options)
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(content=f"**{self.values[0]} Commands:**\n/play, /skip, /gstart, /antinuke")

@bot.hybrid_command(name="help")
async def help(ctx):
    view = discord.ui.View(); view.add_item(HelpDropdown())
    await ctx.send("Select a category:", view=view)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print("✅ Oliver is fully Proxy-Ready & Synced!")
@bot.event
async def on_ready():
    await bot.tree.sync()
    print("✅ Oliver is fully loaded with all commands!")

keep_alive()
bot.run(os.getenv('DISCORD_TOKEN'))
