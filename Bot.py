import asyncio
import os
import stat
import discord
from discord.ext import commands
import yt_dlp
import urllib.request
import tarfile
import platform
import re
import json
from keep_alive import keep_alive  

# --- SMART FFMPEG DOWNLOADER (FIX FOR -11 ARCHITECTURE ERROR) ---
if not os.path.exists("./ffmpeg"):
    arch = platform.machine().lower()
    print(f"Detected System Architecture: {arch}")
    
    if "aarch64" in arch or "arm" in arch:
        url = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-arm64-static.tar.xz"
    else:
        url = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
        
    print(f"Downloading official static FFmpeg for {arch}...")
    urllib.request.urlretrieve(url, "ffmpeg.tar.xz")
    
    print("Extracting FFmpeg binary...")
    with tarfile.open("ffmpeg.tar.xz") as tar:
        for member in tar.getmembers():
            if member.isfile() and member.name.endswith("/ffmpeg"):
                f_in = tar.extractfile(member)
                with open("./ffmpeg", "wb") as f_out:
                    f_out.write(f_in.read())
                break
                
    st = os.stat("./ffmpeg")
    os.chmod("./ffmpeg", st.st_mode | stat.S_IEXEC)
    os.remove("ffmpeg.tar.xz")
    print("FFmpeg setup completed successfully!")

# --- BOT CONFIGURATION ---
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix=">", intents=intents)

PREMIUM_USERS = [149017434425665333]

# --- 🔥 YAHAN CHANGE KIYA HAI (LOCAL DOWNLOAD SYSTEM) 🔥 ---
ydl_opts = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'outtmpl': 'audio_file', # Gane ko server par save karega
}

# Local file ke liye network options hata diye hain
ffmpeg_options = {
    'options': '-vn -b:a 64k'
}

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} - System Online on Cloud!")

# --- 🎵 ULTRA STABLE PLAY COMMAND (DOWNLOAD & PLAY) ---
@bot.command()
async def play(ctx, *, query: str = None):
    if not query:
        return await ctx.send("❌ Please provide a song name! Example: `>play moves shubh`")
    if not ctx.author.voice:
        return await ctx.send("❌ Please join a voice channel first! 🎧")

    if ctx.voice_client is None:
        try:
            await ctx.author.voice.channel.connect(timeout=60.0)
        except asyncio.TimeoutError:
            return await ctx.send("❌ Connection timeout. Server is slow, please try again.")
        except Exception as e:
            return await ctx.send("❌ Failed to connect to the voice channel.")

    voice_client = ctx.voice_client

    try:
        await ctx.send("⏳ **Downloading track to secure server... (Just 2-3 seconds)**")

        # Purana gana delete karna taaki storage full na ho
        if os.path.exists("audio_file"):
            try:
                os.remove("audio_file")
            except:
                pass

        # Naya gana download karna
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"scsearch:{query}", download=True)
            
            if 'entries' in info and len(info['entries']) > 0:
                info = info['entries'][0]
            else:
                return await ctx.send("❌ Track not found on SoundCloud. Try another name.")

            title = info.get('title', 'Unknown Title')

        if voice_client.is_playing():
            voice_client.stop()
        
        # Local audio_file ko play karna (100% bypasses all internet blocks)
        source = discord.FFmpegPCMAudio("audio_file", executable="./ffmpeg", **ffmpeg_options)
        source = discord.PCMVolumeTransformer(source)
        voice_client.play(source)

        embed = discord.Embed(title="🎵 Now Playing", description=f"**{title}**", color=discord.Color.green())
        embed.set_footer(text="Vibing for the Road To 3K Music Fest at Royal Club!")
        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"❌ Playback Error. Please try again.\n**Technical Error:** `{e}`")

# --- 🔊 VOLUME COMMAND (PREMIUM ONLY) ---
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

# --- 🛑 STOP COMMAND ---
@bot.command()
async def stop(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("🛑 Music stopped.")
    else:
        await ctx.send("❌ No music is playing right now.")

# --- 🛡 MODERATION COMMANDS ---
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
                await channel.guild.create_text_channel(name=channel.name, category=channel.category)
            except Exception as e:
                pass

@bot.event
async def on_guild_role_delete(role):
    async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
        user = entry.user
        if user.id not in PREMIUM_USERS and user.id != role.guild.owner_id:
            try:
                await role.guild.ban(user, reason="Anti-Nuke: Unauthorised Role Deletion")
            except Exception as e:
                pass

keep_alive()  
bot.run(os.getenv('DISCORD_TOKEN'))
