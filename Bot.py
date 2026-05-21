import asyncio
import os
import discord
from discord.ext import commands
import yt_dlp
import urllib.request
import re
import json

# --- AUTO FFMPEG DOWNLOADER FOR CLOUD ---
# यह रेंडर क्लाउड पर बिना किसी डिस्क स्पेस एरर के FFmpeg सेटअप कर देगा
if not os.path.exists("./ffmpeg"):
    print("Downloading light FFmpeg binary...")
    import zipfile
    url = "https://github.com/ffbinaries/ffbinaries-prebuilt/releases/download/v4.1/ffmpeg-4.1-linux-64.zip"
    urllib.request.urlretrieve(url, "ffmpeg.zip")
    with zipfile.ZipFile("ffmpeg.zip", "r") as zip_ref:
        zip_ref.extractall(".")
    os.chmod("./ffmpeg", 0o755)
    os.remove("ffmpeg.zip")
    print("FFmpeg setup completed successfully!")

# --- BOT CONFIGURATION ---
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix=">", intents=intents)

# 🌟 PREMIUM USERS & WHITE-LIST LIST (आपकी Discord ID)
PREMIUM_USERS = [149017434425665333]

ydl_opts = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'skip_download': True,
    'nocheckcertificate': True
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -verify_hostname 0',
    'options': '-vn -b:a 64k'
}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} - System Online on Cloud!')

# --- 🎵 ULTRA STABLE PLAY COMMAND (BYPASSES BLOCK) ---
@bot.command()
async def play(ctx, *, query: str = None):
    if not query:
        return await ctx.send("❌ Please provide a song name! Example: `>play tum hi ho`")
    if not ctx.author.voice:
        return await ctx.send("❌ Please join a voice channel first! 🎧")

    if ctx.voice_client is None:
        await ctx.author.voice.channel.connect()
    
    voice_client = ctx.voice_client

    try:
        await ctx.send("🎵 Searching via secure cloud gateway...")
        
        # 1. Scraping YouTube safely without API keys
        search_keyword = query.replace(" ", "+")
        req = urllib.request.Request(
            f"https://www.youtube.com/results?search_query={search_keyword}",
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        
        video_id = None
        with urllib.request.urlopen(req) as response:
            video_ids = re.findall(r"watch\?v=(\S{11})", response.read().decode())
            if video_ids:
                video_id = video_ids[0]

        if not video_id:
            return await ctx.send("❌ Track not found. Try another name.")

        # 2. Proxy streaming via Cobalt (Bypasses all 403 / Bot Verification errors)
        payload = {
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "downloadMode": "audio",
            "audioFormat": "mp3"
        }
        
        api_req = urllib.request.Request("https://api.cobalt.tools/api/json", method="POST")
        api_req.add_header('Content-Type', 'application/json')
        api_req.add_header('Accept', 'application/json')
        
        with urllib.request.urlopen(api_req, data=json.dumps(payload).encode()) as response:
            res_data = json.loads(response.read().decode())
            if res_data.get("status") in ["redirect", "stream"]:
                audio_url = res_data["url"]
                title = res_data.get("text", query)
            else:
                return await ctx.send("❌ Streaming node busy. Please try again in a second.")

        if voice_client.is_playing():
            voice_client.stop()

        # 3. Play the clean audio stream
        source = discord.FFmpegPCMAudio(audio_url, executable="./ffmpeg", **ffmpeg_options)
        source = discord.PCMVolumeTransformer(source)
        voice_client.play(source)

        embed = discord.Embed(title="🎵 Now Playing", description=f"**{title}**", color=discord.Color.orange())
        embed.set_footer(text="Vibing for the Road To 3K Music Fest at Royal Club!")
        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"❌ Playback Error. Please try again.")
        print(f"Error details: {e}")

# --- 🌟 VOLUME COMMAND (PREMIUM ONLY) ---
@bot.command()
async def volume(ctx, vol: int):
    if ctx.author.id not in PREMIUM_USERS:
        return await ctx.send("❌ **Premium Only:** This command is reserved for premium users! ⭐")
    if not ctx.voice_client:
        return await ctx.send("❌ I am not in a voice channel.")
    if not 0 <= vol <= 100:
        return await ctx.send("❌ Volume must be between 0 and 100.")
    ctx.voice_client.source.volume = vol / 100
    await ctx.send(f"🔊 Volume changed to **{vol}%**")

# --- STOP COMMAND ---
@bot.command()
async def stop(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("🛑 Music stopped.")
    else:
        await ctx.send("❌ No music is playing right now.")

# --- 🛡️ MODERATION COMMANDS ---
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.send(f"✅ {member.mention} has been kicked. Reason: {reason}")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f"✅ {member.mention} has been banned. Reason: {reason}")

# --- ⚡ ANTI-NUKE SYSTEM (AUTOMATIC RESTORE) ---
@bot.event
async def on_guild_channel_delete(channel):
    async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
        user = entry.user
        if user.id not in PREMIUM_USERS and user.id != channel.guild.owner_id:
            try:
                await channel.guild.ban(user, reason="Anti-Nuke: Unauthorised Channel Deletion")
                # Deleted channel को तुरंत वापस क्रिएट करना
                await channel.guild.create_text_channel(name=channel.name, category=channel.category)
            except Exception as e:
                print(f"Anti-Nuke Error: {e}")

@bot.event
async def on_guild_role_delete(role):
    async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
        user = entry.user
        if user.id not in PREMIUM_USERS and user.id != role.guild.owner_id:
            try:
                await role.guild.ban(user, reason="Anti-Nuke: Unauthorised Role Deletion")
            except Exception as e:
                print(f"Anti-Nuke Error: {e}")

# यह टोकन को Render की environment variables से सुरक्षित तरीके से उठाएगा
bot.run(os.getenv('DISCORD_TOKEN'))

