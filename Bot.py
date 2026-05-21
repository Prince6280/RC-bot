import asyncio
import os
import stat
import discord
from discord.ext import commands
import yt_dlp
import urllib.request
import tarfile
import platform
from keep_alive import keep_alive  

# --- SMART FFMPEG DOWNLOADER (100% CRASH FREE) ---
if not os.path.exists("./ffmpeg"):
    arch = platform.machine().lower()
    print(f"Detected System Architecture: {arch}")
    
    if "aarch64" in arch or "arm" in arch:
        url = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-arm64-static.tar.xz"
    else:
        url = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
        
    print(f"Downloading official static FFmpeg for {arch}...")
    urllib.request.urlretrieve(url, "ffmpeg.tar.xz")
    
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

# 🌟 PREMIUM USERS & QUEUE SYSTEM
PREMIUM_USERS = [149017434425665333]
SECRET_PREMIUM_KEY = "ROADTO3K"  # Is key ko use karke log premium claim karenge
music_queues = {} # Har server ki apni alag line (queue) hogi

ffmpeg_options = {
    'options': '-vn -b:a 64k'
}

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} - System Online on Cloud!")

# --- 🎵 CORE MUSIC SYSTEM (QUEUE, BANNER & AUTO-PLAY) ---
async def play_next(ctx):
    if ctx.guild.id in music_queues and len(music_queues[ctx.guild.id]) > 0:
        song = music_queues[ctx.guild.id].pop(0) # Queue me se pehla gana nikala
        file_name = f"audio_{ctx.guild.id}"
        
        if os.path.exists(file_name):
            try: os.remove(file_name)
            except: pass

        ydl_opts_dl = {'format': 'bestaudio/best', 'outtmpl': file_name, 'quiet': True}
        
        msg = await ctx.send(f"⏳ **Downloading track... (Just 2-3 seconds)**")
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts_dl) as ydl:
                ydl.extract_info(song['webpage_url'], download=True)
                
            # Gana khatam hone ke baad auto-next play karne ka logic
            def after_play(error):
                coro = play_next(ctx)
                fut = asyncio.run_coroutine_threadsafe(coro, bot.loop)
                try: fut.result()
                except: pass

            source = discord.FFmpegPCMAudio(file_name, executable="./ffmpeg", **ffmpeg_options)
            source = discord.PCMVolumeTransformer(source)
            ctx.voice_client.play(source, after=after_play)
            
            # --- MUSIC BANNER (THUMBNAIL) ---
            embed = discord.Embed(title="🎵 Now Playing", description=f"**{song['title']}**", color=discord.Color.green())
            if song['thumbnail']:
                embed.set_image(url=song['thumbnail']) # Yahan banner add ho raha hai
            embed.set_footer(text="Vibing for the Road To 3K Music Fest at Royal Club!")
            
            await msg.delete()
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Error playing next track: `{e}`")
            await play_next(ctx) # Agar ek me error aaye to agla try karo
    else:
        await ctx.send("🎶 Queue is empty! Ready for the next track.")

@bot.command()
async def play(ctx, *, query: str = None):
    if not query: return await ctx.send("❌ Please provide a song name! Example: `>play moves shubh`")
    if not ctx.author.voice: return await ctx.send("❌ Please join a voice channel first! 🎧")

    if ctx.voice_client is None:
        try: await ctx.author.voice.channel.connect(timeout=60.0)
        except: return await ctx.send("❌ Failed to connect to the voice channel.")

    await ctx.send("🔍 **Searching track...**")
    
    # Sirf details search karna (jaldi add karne ke liye)
    ydl_opts_search = {'format': 'bestaudio', 'quiet': True, 'noplaylist': True}
    with yt_dlp.YoutubeDL(ydl_opts_search) as ydl:
        info = ydl.extract_info(f"scsearch:{query}", download=False)
        if 'entries' in info and len(info['entries']) > 0:
            info = info['entries'][0]
        else:
            return await ctx.send("❌ Track not found. Try another name.")
            
        song_data = {
            'title': info.get('title', 'Unknown Title'),
            'thumbnail': info.get('thumbnail', ''),
            'webpage_url': info.get('webpage_url', info.get('url'))
        }

    # Gane ko Line (Queue) me lagana
    if ctx.guild.id not in music_queues:
        music_queues[ctx.guild.id] = []
    music_queues[ctx.guild.id].append(song_data)
    
    # Agar bot pehle se kuch nahi gaa raha, to music start karo
    if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
        await play_next(ctx)
    else:
        embed = discord.Embed(title="📝 Added to Queue", description=f"**{song_data['title']}**", color=discord.Color.blue())
        if song_data['thumbnail']: embed.set_thumbnail(url=song_data['thumbnail'])
        await ctx.send(embed=embed)

# --- ⏭️ SKIP COMMAND ---
@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop() # Stop karte hi auto-next trigger ho jayega
        await ctx.send("⏭️ **Song Skipped!** Playing next in queue...")
    else:
        await ctx.send("❌ No music is playing right now to skip.")

# --- 👑 PREMIUM CLAIM COMMAND ---
@bot.command()
async def claim_premium(ctx, key: str = None):
    if ctx.author.id in PREMIUM_USERS:
        return await ctx.send("✅ You are already a **Premium User**! ⭐")
        
    if key == SECRET_PREMIUM_KEY:
        PREMIUM_USERS.append(ctx.author.id)
        embed = discord.Embed(title="🎉 Premium Claimed!", description="**Welcome to the VIP Lounge!**\nYou now have access to exclusive commands like `>volume`.", color=discord.Color.gold())
        embed.set_footer(text="See you at the Road To 3K Music Fest!")
        await ctx.send(embed=embed)
    else:
        await ctx.send("❌ **Invalid Key!** Ask the admin for the secret premium key.")

# --- 🔊 VOLUME COMMAND (PREMIUM ONLY) ---
@bot.command()
async def volume(ctx, vol: int):
    if ctx.author.id not in PREMIUM_USERS:
        return await ctx.send("❌ **Premium Only:** Claim premium using `>claim_premium` first! ⭐")
    if not ctx.voice_client: return await ctx.send("❌ I am not in a voice channel.")
    if not 0 <= vol <= 100: return await ctx.send("❌ Volume must be between 0 and 100.")
    ctx.voice_client.source.volume = vol / 100
    await ctx.send(f"🔊 Volume changed to **{vol}%**")

# --- 🛑 STOP COMMAND ---
@bot.command()
async def stop(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        music_queues[ctx.guild.id] = [] # Queue clear kardi
        ctx.voice_client.stop()
        await ctx.send("🛑 Music stopped and queue cleared.")
    else:
        await ctx.send("❌ No music is playing right now.")

# --- 🛡 MODERATION & ANTI-NUKE ---
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

@bot.event
async def on_guild_channel_delete(channel):
    async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
        user = entry.user
        if user.id not in PREMIUM_USERS and user.id != channel.guild.owner_id:
            try:
                await channel.guild.ban(user, reason="Anti-Nuke: Unauthorised Channel Deletion")
                await channel.guild.create_text_channel(name=channel.name, category=channel.category)
            except Exception: pass

@bot.event
async def on_guild_role_delete(role):
    async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
        user = entry.user
        if user.id not in PREMIUM_USERS and user.id != role.guild.owner_id:
            try: await role.guild.ban(user, reason="Anti-Nuke: Unauthorised Role Deletion")
            except Exception: pass

keep_alive()  
bot.run(os.getenv('DISCORD_TOKEN'))
