import asyncio, os, discord, random, yt_dlp
from discord import app_commands
from discord.ext import commands
from keep_alive import keep_alive

# --- BOT CONFIG ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=">", intents=intents, help_command=None)
FFMPEG_PATH = "/usr/bin/ffmpeg"

@bot.event
async def on_ready():
    print(f"✅ Oliver {bot.user.name} is ONLINE!")
    await bot.tree.sync()

# --- MUSIC ENGINE (SOUNDCLOUD & YOUTUBE) ---
@bot.hybrid_command(description="Play a song")
async def play(ctx, *, query: str):
    await ctx.defer()
    if not ctx.author.voice: return await ctx.send("❌ Pehle VC join karo!")
    
    # Voice Connection
    channel = ctx.author.voice.channel
    if ctx.voice_client is None: await channel.connect()
    else: await ctx.voice_client.move_to(channel)

    await ctx.send(f"🔍 Searching: {query}...")

    # YDL Options with User Agent to avoid IP Blocks
    ydl_opts = {
        'format': 'bestaudio',
        'quiet': True,
        'noplaylist': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            # Pehle SoundCloud try karega, phir YouTube
            info = ydl.extract_info(f"scsearch:{query}", download=False)
            if not info['entries']: info = ydl.extract_info(f"ytsearch:{query}", download=False)
            
            song = info['entries'][0]
            source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(song['url'], executable=FFMPEG_PATH))
            ctx.voice_client.play(source)
            await ctx.send(f"▶️ Playing: **{song['title']}**")
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

@bot.hybrid_command(description="Stop music")
async def stop(ctx):
    if ctx.voice_client: await ctx.voice_client.disconnect(); await ctx.send("🛑 Stopped.")

# --- SECURITY & GIVEAWAY SLASH ---
@bot.tree.command(name="antinuke", description="Toggle Anti-Nuke [on/off]")
async def antinuke(interaction: discord.Interaction, state: str):
    await interaction.response.send_message(f"🛡️ Anti-Nuke Status: **{state.upper()}**")

@bot.tree.command(name="gstart", description="Start a professional giveaway")
async def gstart(interaction: discord.Interaction, duration: int, winners: int, prize: str):
    await interaction.response.send_message("🎉 Giveaway started!", ephemeral=True)
    msg = await interaction.channel.send(f"🎉 **GIVEAWAY: {prize}**\nEnds in {duration} mins!")
    await msg.add_reaction("🎉")
    await asyncio.sleep(duration * 60)
    users = [u async for u in (await interaction.channel.fetch_message(msg.id)).reactions[0].users() if not u.bot]
    if len(users) < winners: await interaction.channel.send("❌ Not enough entries.")
    else:
        win = random.sample(users, winners)
        await interaction.channel.send(f"🎉 Winners: {', '.join([w.mention for w in win])} won **{prize}**!")

# --- HELP ---
@bot.hybrid_command(description="Help menu")
async def help(ctx):
    embed = discord.Embed(title="Oliver Command Center", color=0x2f3136)
    embed.add_field(name="Commands", value="/play, /stop, /gstart, /antinuke, /automod", inline=False)
    await ctx.send(embed=embed)

keep_alive()
bot.run(os.getenv('DISCORD_TOKEN'))
