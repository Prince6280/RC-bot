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

# --- 🎛️ INTERACTIVE MUSIC BUTTONS ---
class MusicControls(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=None)
        self.ctx = ctx

    @discord.ui.button(emoji="⏯️", style=discord.ButtonStyle.secondary)
    async def pause_resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = self.ctx.voice_client
        if vc:
            if vc.is_playing():
                vc.pause()
                await interaction.response.send_message("⏸️ **Music Paused!**", ephemeral=True)
            elif vc.is_paused():
                vc.resume()
                await interaction.response.send_message("▶️ **Music Resumed!**", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Nothing is playing.", ephemeral=True)

    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.secondary)
    async def skip_song(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = self.ctx.voice_client
        if vc and vc.is_playing():
            vc.stop()
            await interaction.response.send_message("⏭️ **Song Skipped!** Playing next...", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Nothing to skip.", ephemeral=True)

    @discord.ui.button(emoji="🛑", style=discord.ButtonStyle.danger)
    async def stop_song(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = self.ctx.voice_client
        if vc:
            global music_queues
            if self.ctx.guild.id in music_queues:
                music_queues[self.ctx.guild.id] = [] 
            vc.stop()
            await interaction.response.send_message("🛑 **DJ Stopped!** Queue cleared.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Nothing is playing.", ephemeral=True)

    @discord.ui.button(emoji="🎸", label="Bass", style=discord.ButtonStyle.primary)
    async def bass_boost(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in PREMIUM_USERS:
            active_effects[self.ctx.guild.id] = "bass"
            await interaction.response.send_message("🔊 **Bass Boost Ready!** (Will apply on next song or `>skip`)", ephemeral=True)
        else:
            await interaction.response.send_message("❌ **VIP Only!** Use `>claim_premium ROADTO3K` first.", ephemeral=True)

# --- 🌟 ZEON STYLE BLACK CUSTOM HELP MENU ---
@bot.command(name="help")
async def custom_help(ctx):
    # Pure Black Theme (0,0,0)
    embed = discord.Embed(color=discord.Color.from_rgb(0, 0, 0))
    
    embed.title = f"Hey , I'm {bot.user.name} ™"
    
    total_cmds = len(bot.commands)
    
    desc = (
        "A multipurpose VIP bot to setup your dream community and the perfect music fest.\n\n"
        f"• **My prefix for this server is** `>`\n"
        f"• **Type** `>[command]` **to use me**\n"
        f"• **Total commands:** {total_cmds}\n\n"
        "🎵 » **Music Commands** (`>play`, `>skip`, `>stop`)\n"
        "🎛️ » **VIP DJ Effects** (`>bass`, `>8d`, `>nightcore`, `>normal`, `>volume`)\n"
        "🛡️ » **Security (Auto)** (`Anti-Spam`, `Anti-Raid`, `Anti-Nuke`)\n"
        "⚙️ » **Moderation** (`>kick`, `>ban`)\n"
        "💾 » **Backup System** (`>backup_create`, `>backup_load`)\n"
        "🖼️ » **Profile** (`>avatar`, `>banner`)\n"
        "👑 » **Premium** (`>claim_premium`)\n"
    )
    embed.description = desc
    
    # Pro Tip Section
    embed.add_field(
        name="__Pro Tip__", 
        value="Claim your VIP access with `>claim_premium ROADTO3K` to unlock exclusive audio filters! 🌟", 
        inline=False
    )
    
    # Links Section
    embed.add_field(
        name="🔗 __Links__", 
        value="[Invite me](https://discord.com) | [Support Server](https://discord.com) | [Vote](https://discord.com)", 
        inline=False
    )
    
    if bot.user.avatar:
        embed.set_thumbnail(url=bot.user.avatar.url)
        
    embed.set_footer(text="Road To 3K Music Fest", icon_url=ctx.author.display_avatar.url if ctx.author.display_avatar else None)
    
    await ctx.send(embed=embed)

# --- 🛡️ SECURITY SYSTEM (SPAM/RAID/NUKE) ---
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
            await message.channel.send(f"⚠️ {message.author.mention}, Stop spamming!", delete_after=3)
        except: pass
    await bot.process_commands(message)

@bot.event
async def on_member_join(member):
    current_time = time.time()
    global raid_tracker
    raid_tracker = [join_time for join_time in raid_tracker if current_time - join_time < 10]
    raid_tracker.append(current_time)
    if len(raid_tracker) > 4:
        try: await member.kick(reason="Anti-Raid")
        except: pass

@bot.event
async def on_guild_channel_delete(channel):
    async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
        user = entry.user
        if user.id not in PREMIUM_USERS and user.id != channel.guild.owner_id:
            try:
                await channel.guild.ban(user, reason="Anti-Nuke")
                await channel.guild.create_text_channel(name=channel.name, category=channel.category)
            except: pass

@bot.event
async def on_guild_role_delete(role):
    async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
        user = entry.user
        if user.id not in PREMIUM_USERS and user.id != role.guild.owner_id:
            try: await role.guild.ban(user, reason="Anti-Nuke")
            except: pass

@bot.command()
@commands.has_permissions(administrator=True)
async def backup_create(ctx):
    await ctx.send("⏳ Creating server backup...")
    backup_data = {
        "roles": [{"name": r.name, "color": r.color.value} for r in ctx.guild.roles if r.name != "@everyone"],
        "categories": [{"name": c.name} for c in ctx.guild.categories],
        "channels": [{"name": c.name, "type": str(c.type), "category": c.category.name if c.category else None} for c in ctx.guild.channels]
    }
    with open(f"backup_{ctx.guild.id}.json", "w") as f: json.dump(backup_data, f, indent=4)
    await ctx.send("✅ **Backup Created!**")

@bot.command()
@commands.has_permissions(administrator=True)
async def backup_load(ctx):
    if not os.path.exists(f"backup_{ctx.guild.id}.json"): return await ctx.send("❌ No backup found!")
    await ctx.send("⚠️ **Restoring Server...**")
    with open(f"backup_{ctx.guild.id}.json", "r") as f: backup_data = json.load(f)
    existing_categories = [c.name for c in ctx.guild.categories]
    for cat in backup_data["categories"]:
        if cat["name"] not in existing_categories: await ctx.guild.create_category(cat["name"])
    await ctx.send("✅ Server Restored!")

def get_audio_options(guild_id):
    effect = active_effects.get(guild_id, "normal")
    base_options = '-vn -b:a 64k'
    if effect == "bass": base_options += ' -af "bass=g=15,dynaudnorm=f=200"' 
    elif effect == "8d": base_options += ' -af "apulsator=hz=0.09"'
    elif effect == "nightcore": base_options += ' -af "asetrate=44100*1.25,atempo=1.25"'
    return {'options': base_options}

# --- 🎵 MUSIC SYSTEM (SOUNDCLOUD + JIOSAAVN DIRECT) ---
async def play_next(ctx):
    if ctx.guild.id in music_queues and len(music_queues[ctx.guild.id]) > 0:
        song = music_queues[ctx.guild.id].pop(0) 
        file_name = f"audio_{ctx.guild.id}"
        if os.path.exists(file_name):
            try: os.remove(file_name)
            except: pass

        ydl_opts_dl = {'format': 'bestaudio/best', 'outtmpl': file_name, 'quiet': True}
        msg = await ctx.send(f"⏳ **Loading track...**")
        
        def download_song():
            with yt_dlp.YoutubeDL(ydl_opts_dl) as ydl: ydl.extract_info(song['webpage_url'], download=True)
                
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
            
            embed = discord.Embed(title="▶️ Now Playing", description=f"**[{song['title']}]({song['webpage_url']})**", color=discord.Color.green())
            if song['thumbnail']: embed.set_thumbnail(url=song['thumbnail']) 
            
            current_effect = active_effects.get(ctx.guild.id, "normal").upper()
            if current_effect != "NORMAL": embed.add_field(name="🎛️ Active Effect", value=f"**{current_effect}**", inline=False)
            embed.set_footer(text="Vibing for the Road To 3K Music Fest at Royal Club!")
            
            await msg.delete()
            await ctx.send(embed=embed, view=MusicControls(ctx))
            
        except Exception as e:
            await ctx.send(f"❌ Playback Error. Skipping...")
            await play_next(ctx) 
    else:
        await ctx.send("🎶 Queue is empty! DJ needs more tracks.")

@bot.command()
async def play(ctx, *, query: str = None):
    if not query: return await ctx.send("❌ Provide a song name or JioSaavn/SoundCloud Link!")
    if not ctx.author.voice: return await ctx.send("❌ Join a voice channel first! 🎧")
    if ctx.voice_client is None:
        try: await ctx.author.voice.channel.connect(timeout=60.0)
        except: return await ctx.send("❌ Failed to connect.")

    await ctx.send("🔍 **Searching...**")
    ydl_opts_search = {'format': 'bestaudio', 'quiet': True, 'noplaylist': True}
    
    def search_song():
        with yt_dlp.YoutubeDL(ydl_opts_search) as ydl:
            if query.startswith("http://") or query.startswith("https://"): return ydl.extract_info(query, download=False)
            else: return ydl.extract_info(f"scsearch:{query}", download=False)
            
    try:
        info = await asyncio.to_thread(search_song)
        if 'entries' in info and len(info['entries']) > 0: info = info['entries'][0]
        elif not info: return await ctx.send("❌ Track not found.")
            
        song_data = {'title': info.get('title', 'Unknown Title'), 'thumbnail': info.get('thumbnail', ''), 'webpage_url': info.get('webpage_url', info.get('url'))}
        if ctx.guild.id not in music_queues: music_queues[ctx.guild.id] = []
        music_queues[ctx.guild.id].append(song_data)
        
        if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
            await play_next(ctx)
        else:
            embed = discord.Embed(title="📝 Added to Queue", description=f"**{song_data['title']}**", color=discord.Color.blue())
            if song_data['thumbnail']: embed.set_thumbnail(url=song_data['thumbnail'])
            await ctx.send(embed=embed)
    except: await ctx.send("❌ Search failed due to network issue.")

@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop() 
        await ctx.send("⏭️ **Song Skipped!**")
    else: await ctx.send("❌ No music is playing right now.")

# --- PROFILE COMMANDS ---
@bot.command(aliases=['av', 'pfp'])
async def avatar(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title=f"📸 {member.display_name}'s Avatar", color=discord.Color.purple())
    if member.display_avatar: embed.set_image(url=member.display_avatar.url)
    await ctx.send(embed=embed)

@bot.command()
async def banner(ctx, member: discord.Member = None):
    member = member or ctx.author
    user = await bot.fetch_user(member.id)
    if user.banner:
        embed = discord.Embed(title=f"🌌 {member.display_name}'s Banner", color=discord.Color.purple())
        embed.set_image(url=user.banner.url)
        await ctx.send(embed=embed)
    else: await ctx.send("❌ No custom banner!")

# --- PREMIUM COMMANDS ---
@bot.command()
async def claim_premium(ctx, key: str = None):
    if ctx.author.id in PREMIUM_USERS: return await ctx.send("✅ You are already a **Premium User**! ⭐")
    if key == SECRET_PREMIUM_KEY:
        PREMIUM_USERS.append(ctx.author.id)
        await ctx.send("🎉 **Premium VIP Claimed!** Welcome to the VIP Lounge!")
    else: await ctx.send("❌ **Invalid Key!** Type `>claim_premium ROADTO3K` without tagging anyone.")

@bot.command()
async def bass(ctx):
    if ctx.author.id not in PREMIUM_USERS: return await ctx.send("❌ **VIP Only!**")
    active_effects[ctx.guild.id] = "bass"
    await ctx.send("🔊 **Extreme Bass Boost Activated!**")

@bot.command()
async def normal(ctx):
    if ctx.author.id not in PREMIUM_USERS: return await ctx.send("❌ **VIP Only!**")
    active_effects[ctx.guild.id] = "normal"
    await ctx.send("✅ Audio reset to **Normal**.")

@bot.command()
async def volume(ctx, vol: int):
    if ctx.author.id not in PREMIUM_USERS: return await ctx.send("❌ **VIP Only!**")
    if not ctx.voice_client or not ctx.voice_client.source: return await ctx.send("❌ DJ is not playing anything!")
    if not 0 <= vol <= 100: return await ctx.send("❌ Volume must be 0-100.")
    ctx.voice_client.source.volume = vol / 100
    await ctx.send(f"🔊 Volume changed to **{vol}%**")

@bot.command()
async def stop(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        music_queues[ctx.guild.id] = [] 
        ctx.voice_client.stop()
        await ctx.send("🛑 Stopped.")
    else: await ctx.send("❌ Nothing playing.")

keep_alive()  
bot.run(os.getenv('DISCORD_TOKEN'))
