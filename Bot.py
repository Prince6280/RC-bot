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

# 🌟 PREMIUM USERS, QUEUE & EFFECTS SYSTEM
PREMIUM_USERS = [149017434425665333]
SECRET_PREMIUM_KEY = "ROADTO3K"  
music_queues = {} 
active_effects = {} # Naya system: Har server ka apna audio effect

# --- 🎛️ DYNAMIC AUDIO FILTERS LOGIC ---
def get_audio_options(guild_id):
    effect = active_effects.get(guild_id, "normal")
    base_options = '-vn -b:a 64k'
    
    if effect == "bass":
        # Hardcore Bass Boost
        base_options += ' -af "bass=g=15,dynaudnorm=f=200"' 
    elif effect == "8d":
        # 8D Surround Audio Panning
        base_options += ' -af "apulsator=hz=0.09"'
    elif effect == "nightcore":
        # Fast & High Pitch
        base_options += ' -af "asetrate=44100*1.25,atempo=1.25"'
        
    return {'options': base_options}

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} - DJ System Online!")

# --- 🎵 CORE MUSIC SYSTEM ---
async def play_next(ctx):
    if ctx.guild.id in music_queues and len(music_queues[ctx.guild.id]) > 0:
        song = music_queues[ctx.guild.id].pop(0) 
        file_name = f"audio_{ctx.guild.id}"
        
        if os.path.exists(file_name):
            try: os.remove(file_name)
            except: pass

        ydl_opts_dl = {'format': 'bestaudio/best', 'outtmpl': file_name, 'quiet': True}
        msg = await ctx.send(f"⏳ **Downloading track for best quality...**")
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts_dl) as ydl:
                ydl.extract_info(song['webpage_url'], download=True)
                
            def after_play(error):
                coro = play_next(ctx)
                fut = asyncio.run_coroutine_threadsafe(coro, bot.loop)
                try: fut.result()
                except: pass

            # Yahan dynamic effects apply ho rahe hain
            audio_opts = get_audio_options(ctx.guild.id)
            source = discord.FFmpegPCMAudio(file_name, executable="./ffmpeg", **audio_opts)
            source = discord.PCMVolumeTransformer(source)
            ctx.voice_client.play(source, after=after_play)
            
            # --- MUSIC BANNER ---
            embed = discord.Embed(title="🎵 Now Playing", description=f"**{song['title']}**", color=discord.Color.green())
            if song['thumbnail']:
                embed.set_image(url=song['thumbnail']) 
            
            # Agar koi effect laga hai, to banner me show karo
            current_effect = active_effects.get(ctx.guild.id, "normal").upper()
            if current_effect != "NORMAL":
                embed.add_field(name="🎛️ Active Effect", value=f"**{current_effect}**", inline=False)
                
            embed.set_footer(text="Vibing for the Road To 3K Music Fest at Royal Club!")
            
            await msg.delete()
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Error playing next track: `{e}`")
            await play_next(ctx) 
    else:
        await ctx.send("🎶 Queue is empty! DJ needs more tracks.")

@bot.command()
async def play(ctx, *, query: str = None):
    if not query: return await ctx.send("❌ Please provide a song name! Example: `>play moves shubh`")
    if not ctx.author.voice: return await ctx.send("❌ Please join a voice channel first! 🎧")

    if ctx.voice_client is None:
        try: await ctx.author.voice.channel.connect(timeout=60.0)
        except: return await ctx.send("❌ Failed to connect to the voice channel.")

    await ctx.send("🔍 **Searching track...**")
    
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

    if ctx.guild.id not in music_queues:
        music_queues[ctx.guild.id] = []
    music_queues[ctx.guild.id].append(song_data)
    
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
        ctx.voice_client.stop() 
        await ctx.send("⏭️ **Song Skipped!** Playing next in queue...")
    else:
        await ctx.send("❌ No music is playing right now.")

# --- 👑 PREMIUM & EFFECTS COMMANDS ---
@bot.command()
async def claim_premium(ctx, key: str = None):
    if ctx.author.id in PREMIUM_USERS:
        return await ctx.send("✅ You are already a **Premium User**! ⭐")
        
    if key == SECRET_PREMIUM_KEY:
        PREMIUM_USERS.append(ctx.author.id)
        embed = discord.Embed(title="🎉 Premium VIP Claimed!", description="**Welcome to the VIP Lounge!**\nYou now have access to exclusive DJ Commands:\n`>volume`, `>bass`, `>8d`, `>nightcore`, `>normal`", color=discord.Color.gold())
        embed.set_footer(text="Ready for Road To 3K Music Fest!")
        await ctx.send(embed=embed)
    else:
        await ctx.send("❌ **Invalid Key!** Use `>claim_premium ROADTO3K`")

@bot.command()
async def bass(ctx):
    if ctx.author.id not in PREMIUM_USERS: return await ctx.send("❌ **VIP Only!** Claim premium first.")
    active_effects[ctx.guild.id] = "bass"
    await ctx.send("🔊 **Extreme Bass Boost Activated!** (It will apply to the next song or when you type `>skip`) 🎸")

@bot.command()
async def nightcore(ctx):
    if ctx.author.id not in PREMIUM_USERS: return await ctx.send("❌ **VIP Only!** Claim premium first.")
    active_effects[ctx.guild.id] = "nightcore"
    await ctx.send("✨ **Nightcore Mode Activated!** (It will apply to the next song or when you type `>skip`) 🚀")

@bot.command()
async def ad(ctx): # Function name cant be 8d in python, so using ad for 8D command mapping
    pass # Defined below properly as an alias

@bot.command(name="8d")
async def eight_d(ctx):
    if ctx.author.id not in PREMIUM_USERS: return await ctx.send("❌ **VIP Only!** Claim premium first.")
    active_effects[ctx.guild.id] = "8d"
    await ctx.send("🎧 **8D Surround Audio Activated!** (It will apply to the next song or when you type `>skip`) 🌀")

@bot.command()
async def normal(ctx):
    if ctx.author.id not in PREMIUM_USERS: return await ctx.send("❌ **VIP Only!** Claim premium first.")
    active_effects[ctx.guild.id] = "normal"
    await ctx.send("✅ Audio effects reset to **Normal**. (Will apply to the next song)")

# --- 🔊 VOLUME COMMAND ---
@bot.command()
async def volume(ctx, vol: int):
    if ctx.author.id not in PREMIUM_USERS: return await ctx.send("❌ **VIP Only!** Claim premium first.")
    if not ctx.voice_client: return await ctx.send("❌ I am not in a voice channel.")
    if not 0 <= vol <= 100: return await ctx.send("❌ Volume must be between 0 and 100.")
    ctx.voice_client.source.volume = vol / 100
    await ctx.send(f"🔊 Volume changed to **{vol}%**")

# --- 🛑 STOP COMMAND ---
@bot.command()
async def stop(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        music_queues[ctx.guild.id] = [] 
        ctx.voice_client.stop()
        await ctx.send("🛑 Music stopped and queue cleared.")
    else:
        await ctx.send("❌ No music is playing right now.")

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
