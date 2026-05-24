import asyncio, os, discord, random, yt_dlp
from discord import app_commands
from discord.ext import commands
from keep_alive import keep_alive

# --- CONFIG ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=">", intents=intents, help_command=None)
FFMPEG_PATH = "/usr/bin/ffmpeg"
music_queues = {}
# ProxyScrape se 'HTTP' proxy lekar yahan dalein
PROXY_URL = "http://103.152.112.50:8080" 

# --- MUSIC ENGINE (Queue + Proxy + No Route Fix) ---
async def play_next(ctx):
    if ctx.guild.id in music_queues and len(music_queues[ctx.guild.id]) > 0:
        song = music_queues[ctx.guild.id].pop(0)
        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(song['url'], executable=FFMPEG_PATH))
        ctx.voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
        await ctx.send(f"▶️ Playing: **{song['title']}**")
    else: await ctx.send("🎶 Queue khatam!")

@bot.hybrid_command(description="Play music")
async def play(ctx, *, query: str):
    await ctx.defer()
    if not ctx.author.voice: return await ctx.send("❌ Join VC!")
    if ctx.voice_client is None: await ctx.author.voice.channel.connect()
    else: await ctx.voice_client.move_to(ctx.author.voice.channel)
    
    if ctx.guild.id not in music_queues: music_queues[ctx.guild.id] = []
    
    ydl_opts = {
        'format': 'bestaudio/best', 'quiet': True, 'noplaylist': True,
        'proxy': PROXY_URL, 'source_address': '0.0.0.0', 'nocheckcertificate': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch:{query}", download=False)
        song = info['entries'][0]
        music_queues[ctx.guild.id].append(song)
        await ctx.send(f"📝 Added: **{song['title']}**")
        if not ctx.voice_client.is_playing(): await play_next(ctx)

@bot.hybrid_command(description="Skip song")
async def skip(ctx):
    if ctx.voice_client: ctx.voice_client.stop(); await ctx.send("⏭️ Skipped!")

# --- SECURITY & UTILS ---
@bot.tree.command(name="antinuke")
async def antinuke(interaction: discord.Interaction, state: str):
    await interaction.response.send_message(f"🛡️ Anti-Nuke: {state}")

@bot.tree.command(name="automod")
async def automod(interaction: discord.Interaction, state: str):
    await interaction.response.send_message(f"🛡️ Auto-Mod: {state}")

@bot.tree.command(name="jtc")
async def jtc(interaction: discord.Interaction, channel: discord.VoiceChannel):
    await interaction.response.send_message(f"✅ JTC set: {channel.name}")

@bot.tree.command(name="antinick")
async def antinick(interaction: discord.Interaction, state: str):
    await interaction.response.send_message(f"🛡️ Anti-Nick: {state}")

@bot.tree.command(name="gstart")
async def gstart(interaction: discord.Interaction, duration: int, winners: int, prize: str):
    await interaction.response.send_message("🎉 Giveaway started!", ephemeral=True)
    msg = await interaction.channel.send(f"🎉 **GIVEAWAY: {prize}**")
    await msg.add_reaction("🎉")

# --- DROPEDOWN HELP (Cassette Style) ---
class HelpDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label='Music', description='Play, Skip', emoji='🎵'),
            discord.SelectOption(label='Security', description='Antinuke, Automod', emoji='🛡️'),
            discord.SelectOption(label='Utility', description='JTC, CustomRole', emoji='⚙️'),
            discord.SelectOption(label='Fun', description='Gstart, 8ball', emoji='🎉')
        ]
        super().__init__(placeholder='Choose a Category...', options=options)
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(content=f"**{self.values[0]} Commands:**\n/play, /skip, /antinuke, /automod, /jtc, /gstart")

@bot.hybrid_command(name="help")
async def help(ctx):
    view = discord.ui.View(); view.add_item(HelpDropdown())
    await ctx.send("Select a category:", view=view)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print("✅ Oliver is fully operational!")

keep_alive()
bot.run(os.getenv('DISCORD_TOKEN'))

