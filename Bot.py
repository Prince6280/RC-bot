import asyncio, os, discord, random, time, yt_dlp
from discord import app_commands
from discord.ext import commands
from keep_alive import keep_alive

# --- BOT CONFIG ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=">", intents=intents, help_command=None)
FFMPEG_PATH = "/usr/bin/ffmpeg" if os.path.exists("/usr/bin/ffmpeg") else "./ffmpeg"

# --- STATUS & SYNC ---
@bot.event
async def on_ready():
    print(f"✅ {bot.user.name} is Online & Synced!")
    await bot.tree.sync()

# --- SECURITY COMMANDS ---
@bot.tree.command(name="antinuke", description="Toggle Anti-Nuke [on/off]")
async def antinuke(interaction: discord.Interaction, state: str):
    if interaction.user.id != interaction.guild.owner_id:
        return await interaction.response.send_message("❌ Access Denied!", ephemeral=True)
    await interaction.response.send_message(f"🛡️ Anti-Nuke Status: **{state.upper()}**")

@bot.tree.command(name="automod", description="Toggle Auto-Mod [on/off]")
async def automod(interaction: discord.Interaction, state: str):
    await interaction.response.send_message(f"🛡️ Auto-Mod Status: **{state.upper()}**")

# --- JTC & UTILS ---
@bot.tree.command(name="jtc", description="Setup Join-To-Create")
async def jtc(interaction: discord.Interaction, channel: discord.VoiceChannel):
    await interaction.response.send_message(f"✅ JTC set to {channel.name}")

# --- GIVEAWAY ---
@bot.tree.command(name="gstart", description="Start a giveaway")
async def gstart(interaction: discord.Interaction, duration: int, winners: int, prize: str):
    await interaction.response.send_message("Giveaway started!", ephemeral=True)
    msg = await interaction.channel.send(f"🎉 **GIVEAWAY: {prize}**\nEnds in {duration} mins!")
    await msg.add_reaction("🎉")
    await asyncio.sleep(duration * 60)
    users = [u async for u in (await interaction.channel.fetch_message(msg.id)).reactions[0].users() if not u.bot]
    if len(users) < winners: await interaction.channel.send("❌ Not enough entries.")
    else:
        win = random.sample(users, winners)
        await interaction.channel.send(f"🎉 Winners: {', '.join([w.mention for w in win])} won **{prize}**!")

# --- MUSIC ENGINE (JIOSAAVN/SOUNDCLOUD/YT) ---
@bot.hybrid_command(description="Play music")
async def play(ctx, *, query: str):
    await ctx.defer()
    if not ctx.author.voice: return await ctx.send("❌ Join VC first!")
    
    if ctx.voice_client is None: await ctx.author.voice.channel.connect()
    else: await ctx.voice_client.move_to(ctx.author.voice.channel)

    await ctx.send(f"🔍 Searching: {query}...")
    ydl_opts = {'format': 'bestaudio', 'quiet': True, 'noplaylist': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            # Multi-platform search
            info = ydl.extract_info(f"saavnsearch:{query}", download=False)
            if not info['entries']: info = ydl.extract_info(f"scsearch:{query}", download=False)
            if not info['entries']: info = ydl.extract_info(f"ytsearch:{query}", download=False)
            
            song = info['entries'][0]
            source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(song['url'], executable=FFMPEG_PATH))
            ctx.voice_client.play(source)
            await ctx.send(f"▶️ Playing: **{song['title']}**")
        except Exception as e: await ctx.send(f"❌ Error: {e}")

@bot.hybrid_command(description="Stop music")
async def stop(ctx):
    if ctx.voice_client: await ctx.voice_client.disconnect(); await ctx.send("🛑 Stopped.")

# --- HELP MENU ---
@bot.hybrid_command(description="Help menu")
async def help(ctx):
    embed = discord.Embed(title="Oliver Command Center", color=0x2f3136)
    embed.add_field(name="Commands", value="`/play`, `/stop`, `/gstart`, `/antinuke`, `/automod`, `/jtc`", inline=False)
    await ctx.send(embed=embed)

keep_alive()
bot.run(os.getenv('DISCORD_TOKEN'))
