import asyncio
import os
import stat
import discord
from discord.ext import commands
import yt_dlp
import urllib.request
import tarfile
import platform
import time
import json
from keep_alive import keep_alive  

# --- SMART FFMPEG DOWNLOADER ---
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
intents.messages = True 

bot = commands.Bot(command_prefix=">", intents=intents, help_command=None)

PREMIUM_USERS = [149017434425665333] 
SECRET_PREMIUM_KEY = "ROADTO3K"  
music_queues = {} 
active_effects = {} 
spam_tracker = {}
raid_tracker = []

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} - DJ & Security Guardian Online!")

# --- 🌟 ATTRACTIVE CUSTOM HELP MENU ---
@bot.command(name="help")
async def custom_help(ctx):
    embed = discord.Embed(
        title="🌟 RC Music & Guardian Bot",
        description="Welcome to the ultimate DJ and Security bot for the **Road To 3K Music Fest**! Here is everything I can do:",
        color=discord.Color.from_rgb(43, 45, 49) 
    )
    
    embed.add_field(name="🎵 Music Commands", value="`>play [song]` - Play a track or add to queue\n`>skip` - Skip current track\n`>stop` - Stop music & clear queue", inline=False)
    embed.add_field(name="🎛️ VIP DJ Effects (Premium)", value="`>bass` - Extreme Bass Boost\n`>8d` - 8D Surround Sound\n`>nightcore` - Nightcore Mode\n`>normal` - Reset audio\n`>volume [0-100]` - Set volume\n`>claim_premium [key]` - Unlock VIP features", inline=False)
    embed.add_field(name="🖼️ Profile Commands", value="`>avatar [@user]` - View high-res Avatar\n`>banner [@user]` - View user Banner", inline=False)
    embed.add_field(name="🛡️ Security & Admin", value="`>backup_create` - Save server layout\n`>backup_load` - Restore server layout\n`>kick / >ban` - Moderation\n\n*(🛡️ Anti-Nuke, Anti-Raid & Anti-Spam are 24/7 Active Automatically)*", inline=False)
    
    if bot.user.avatar: embed.set_thumbnail(url=bot.user.avatar.url)
    embed.set_footer(text="Vibing for the Road To 3K Music Fest!", icon_url=ctx.author.display_avatar.url if ctx.author.display_avatar else None)
    await ctx.send(embed=embed)

# --- 🛡️ ADVANCED SECURITY SYSTEM ---
@bot.event
async def on_message(message):
    if message.author.bot or message.author.id in PREMIUM_USERS or message.author.id == message.guild.owner_id:
        await bot.process_commands(message)
        return
    author_id = message.author.id
    current_time = time.time()
    if author_id not in spam_tracker: spam_tracker[author_id] = []
    spam_tracker[author_id] = [msg_time for msg_time in spam_tracker[author_id] if current_time - msg_time < 5]
    spam_tracker[author_id].append(current_time)
    if len(spam_tracker[author_id]) > 5:
        try:
            await message.delete()
            await message.channel.send(f"⚠️ {message.author.mention}, Stop spamming! You might get kicked.", delete_after=3)
        except: pass
    await bot.process_commands(message)

@bot.event
async def on_member_join(member):
    current_time = time.time()
    global raid_tracker
    raid_tracker = [join_time for join_time in raid_tracker if current_time - join_time < 10]
    raid_tracker.append(current_time)
    if len(raid_tracker) > 4:
        try:
            await member.kick(reason="Anti-Raid: Mass joining detected!")
            channel = member.guild.system_channel
            if channel: await channel.send("🚨 **ANTI-RAID TRIGGERED:** Mass joining detected! Kicking suspicious accounts.")
        except: pass

@bot.event
async def on_guild_channel_delete(channel):
    async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
        user = entry.user
        if user.id not in PREMIUM_USERS and user.id != channel.guild.owner_id:
            try:
                await channel.guild.ban(user, reason="Anti-Nuke: Unauthorised Channel Deletion")
                await channel.guild.create_text_channel(name=channel.name, category=channel.category)
            except: pass

@bot.event
async def on_guild_role_delete(role):
    async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
        user = entry.user
        if user.id not in PREMIUM_USERS and user.id != role.guild.owner_id:
            try: await role.guild.ban(user, reason="Anti-Nuke: Unauthorised Role Deletion")
            except: pass

@bot.command()
@commands.has_permissions(administrator=True)
async def backup_create(ctx):
    await ctx.send("⏳ Creating server backup... Please wait.")
    backup_data = {
        "roles": [{"name": r.name, "color": r.color.value} for r in ctx.guild.roles if r.name != "@everyone"],
        "categories": [{"name": c.name} for c in ctx.guild.categories],
        "channels": [{"name": c.name, "type": str(c.type), "category": c.category.name if c.category else None} for c in ctx.guild.channels]
    }
    with open(f"backup_{ctx.guild.id}.json", "w") as f: json.dump(backup_data, f, indent=4)
    await ctx.send("✅ **Backup Created Successfully!**\nUse `>backup_load` to restore.")

@bot.command()
@commands.has_permissions(administrator=True)
async def backup_load(ctx):
    if not os.path.exists(f"backup_{ctx.guild.id}.json"):
        return await ctx.send("❌ No backup found for this server! Create one using `>backup_create`")
    await ctx.send("⚠️ **Restoring Server... This might take some time!**")
    with open(f"backup_{ctx.guild.id}.json", "r") as f: backup_data = json.load(f)
    existing_categories = [c.name for c in ctx.guild.categories]
    for cat in backup_data["categories"]:
        if cat["name"] not in existing_categories: await ctx.guild.create_category(cat["name"])
    await ctx.send("✅ Server Layout Restored (Basic Recovery Complete)!")

def get_audio_options(guild_id):
    effect = active_effects.get(guild_id, "normal")
    base_options = '-vn -b:a 64k'
    if effect == "bass": base_options += ' -af "bass=g=15,dynaudnorm=f=200"' 
    elif effect == "8d": base_options += ' -af "apulsator=hz=0.09"'
    elif effect == "nightcore": base_options += ' -af "asetrate=44100*1.25,atempo=1.25"'
    return {'options': base_options}

# --- 🎵 YOUTUBE MUSIC BYPASS SYSTEM (NO JS CHALLENGE) ---
async def play_next(ctx):
    if ctx.guild.id in music_queues and len(music_queues[ctx.guild.id]) > 0:
        song = music_queues[ctx.guild.id].pop(0) 
        file_name = f"audio_{ctx.guild.id}"
        if os.path.exists(file_name):
            try: os.remove(file_name)
            except: pass

        # 🔥 YAHAN CHANGE KIYA HAI: Sirf Android Client use karega (Web hata diya taaki JS error na aaye)
        ydl_opts_dl = {
            'format': 'bestaudio/best', 
            'outtmpl': file_name, 
            'quiet': True,
            'cookiefile': 'cookies.txt', 
            'extractor_args': {'youtube': ['player_client=android']} # Sirf Android Mobile API
        }
        
        msg = await ctx.send(f"⏳ **Downloading track via Android API...**")
        
        def download_song():
            with yt_dlp.YoutubeDL(ydl_opts_dl) as ydl: 
                ydl.extract_info(song['webpage_url'], download=True)
                
        try:
            await asyncio.to_thread(download_song)
            
            def after_play(error):
                coro = play_next(ctx)
                fut = asyncio.run_coroutine_threadsafe(coro, bot.loop)
                try: fut.result()
                except: pass

            audio_opts = get_audio_options(ctx.guild.id)
            source = discord.FFmpegPCMAudio(file_name, executable="./ffmpeg", **audio_opts)
            source = discord.PCMVolumeTransformer(source)
            ctx.voice_client.play(source, after=after_play)
            
            embed = discord.Embed(title="🎵 Now Playing", description=f"**{song['title']}**", color=discord.Color.green())
            if song['thumbnail']: embed.set_image(url=song['thumbnail']) 
            current_effect = active_effects.get(ctx.guild.id, "normal").upper()
            if current_effect != "NORMAL": embed.add_field(name="🎛️ Active Effect", value=f"**{current_effect}**", inline=False)
            embed.set_footer(text="Vibing for the Road To 3K Music Fest at Royal Club!")
            await msg.delete()
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Playback Error. Skipping to next track...")
            print(f"Download Error: {e}")
            await play_next(ctx) 
    else:
        await ctx.send("🎶 Queue is empty! DJ needs more tracks.")

@bot.command()
async def play(ctx, *, query: str = None):
    if not query: return await ctx.send("❌ Please provide a song name!")
    if not ctx.author.voice: return await ctx.send("❌ Please join a voice channel first! 🎧")

    if ctx.voice_client is None:
        try: await ctx.author.voice.channel.connect(timeout=60.0)
        except: return await ctx.send("❌ Failed to connect to the voice channel.")

    await ctx.send("🔍 **Searching YouTube Music...**")
    
    # 🔥 YAHAN CHANGE KIYA HAI: 'ytsearch' ki jagah 'ytmsearch' (YouTube Music) lagaya hai
    ydl_opts_search = {
        'format': 'bestaudio', 
        'quiet': True, 
        'noplaylist': True,
        'cookiefile': 'cookies.txt', 
        'extractor_args': {'youtube': ['player_client=android']} # Sirf Android Mobile API
    }
    
    def search_song():
        with yt_dlp.YoutubeDL(ydl_opts_search) as ydl:
            # YouTube Music par search karega (isme JS error almost nahi aata)
            return ydl.extract_info(f"ytmsearch:{query}", download=False)
            
    try:
        info = await asyncio.to_thread(search_song)
        if 'entries' in info and len(info['entries']) > 0: 
            info = info['entries'][0]
        else: 
            return await ctx.send("❌ Track not found on YouTube Music.")
            
        song_data = {
            'title': info.get('title', 'Unknown Title'),
            'thumbnail': info.get('thumbnail', ''),
            'webpage_url': info.get('webpage_url', info.get('url'))
        }

        if ctx.guild.id not in music_queues: music_queues[ctx.guild.id] = []
        music_queues[ctx.guild.id].append(song_data)
        
        if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
            await play_next(ctx)
        else:
            embed = discord.Embed(title="📝 Added to Queue", description=f"**{song_data['title']}**", color=discord.Color.blue())
            if song_data['thumbnail']: embed.set_thumbnail(url=song_data['thumbnail'])
            await ctx.send(embed=embed)
            
    except Exception as e:
        await ctx.send("❌ Search failed! YouTube might be rate-limiting. Try again.")
        print(f"Search Error: {e}")

@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop() 
        await ctx.send("⏭️ **Song Skipped!**")
    else: await ctx.send("❌ No music is playing right now.")

# --- 🖼️ CUSTOM PROFILE COMMANDS ---
@bot.command(aliases=['av', 'pfp'])
async def avatar(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title=f"📸 {member.display_name}'s Avatar", color=discord.Color.purple())
    if member.display_avatar: embed.set_image(url=member.display_avatar.url)
    embed.set_footer(text="Road To 3K Music Fest")
    await ctx.send(embed=embed)

@bot.command()
async def banner(ctx, member: discord.Member = None):
    member = member or ctx.author
    user = await bot.fetch_user(member.id)
    if user.banner:
        embed = discord.Embed(title=f"🌌 {member.display_name}'s Banner", color=discord.Color.purple())
        embed.set_image(url=user.banner.url)
        embed.set_footer(text="Road To 3K Music Fest")
        await ctx.send(embed=embed)
    else: await ctx.send(f"❌ **{member.display_name}** does not have a custom banner!")

# --- 👑 PREMIUM & EFFECTS COMMANDS ---
@bot.command()
async def claim_premium(ctx, key: str = None):
    if ctx.author.id in PREMIUM_USERS: return await ctx.send("✅ You are already a **Premium User**! ⭐")
    if key == SECRET_PREMIUM_KEY:
        PREMIUM_USERS.append(ctx.author.id)
        embed = discord.Embed(title="🎉 Premium VIP Claimed!", description="**Welcome to the VIP Lounge!**", color=discord.Color.gold())
        await ctx.send(embed=embed)
    else: await ctx.send("❌ **Invalid Key!**")

@bot.command()
async def bass(ctx):
    if ctx.author.id not in PREMIUM_USERS: return await ctx.send("❌ **VIP Only!**")
    active_effects[ctx.guild.id] = "bass"
    await ctx.send("🔊 **Extreme Bass Boost Activated!**")

@bot.command()
async def nightcore(ctx):
    if ctx.author.id not in PREMIUM_USERS: return await ctx.send("❌ **VIP Only!**")
    active_effects[ctx.guild.id] = "nightcore"
    await ctx.send("✨ **Nightcore Mode Activated!**")

@bot.command(name="8d")
async def eight_d(ctx):
    if ctx.author.id not in PREMIUM_USERS: return await ctx.send("❌ **VIP Only!**")
    active_effects[ctx.guild.id] = "8d"
    await ctx.send("🎧 **8D Surround Audio Activated!**")

@bot.command()
async def normal(ctx):
    if ctx.author.id not in PREMIUM_USERS: return await ctx.send("❌ **VIP Only!**")
    active_effects[ctx.guild.id] = "normal"
    await ctx.send("✅ Audio effects reset to **Normal**.")

@bot.command()
async def volume(ctx, vol: int):
    if ctx.author.id not in PREMIUM_USERS: return await ctx.send("❌ **VIP Only!**")
    if not ctx.voice_client: return await ctx.send("❌ I am not in a voice channel.")
    if not ctx.voice_client.source: return await ctx.send("❌ DJ is not playing anything right now!")
    if not 0 <= vol <= 100: return await ctx.send("❌ Volume must be between 0 and 100.")
    ctx.voice_client.source.volume = vol / 100
    await ctx.send(f"🔊 Volume changed to **{vol}%**")

@bot.command()
async def stop(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        music_queues[ctx.guild.id] = [] 
        ctx.voice_client.stop()
        await ctx.send("🛑 Music stopped and queue cleared.")
    else: await ctx.send("❌ No music is playing right now.")

# --- 🛡 MODERATION ---
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

keep_alive()  
bot.run(os.getenv('DISCORD_TOKEN'))
