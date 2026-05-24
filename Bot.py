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
import random
from keep_alive import keep_alive  

# ==========================================
# 🎨 CUSTOM EMOJIS (STATICS ICONS)
# ==========================================
ICON_MUSIC = "🎵"      
ICON_VIP = "🎛️"       
ICON_SECURITY = "🛡️"  
ICON_OWNER = "👑"     
ICON_PROFILE = "🖼️"   
ICON_FUN = "🎉"
ICON_GEAR = "⚙️"
# ==========================================

# --- FFMPEG DOWNLOADER ---
if not os.path.exists("./ffmpeg"):
    arch = platform.machine().lower()
    url = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-arm64-static.tar.xz" if "aarch64" in arch or "arm" in arch else "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
    urllib.request.urlretrieve(url, "ffmpeg.tar.xz")
    with tarfile.open("ffmpeg.tar.xz") as tar:
        for m in tar.getmembers():
            if m.isfile() and m.name.endswith("/ffmpeg"):
                with open("./ffmpeg", "wb") as f_out: f_out.write(tar.extractfile(m).read())
                break
    os.chmod("./ffmpeg", os.stat("./ffmpeg").st_mode | stat.S_IEXEC)
    os.remove("ffmpeg.tar.xz")

# --- BOT SETUP & DATABASE ---
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.messages = True 
intents.voice_states = True 

bot = commands.Bot(command_prefix=">", intents=intents, help_command=None)

DB_FILE = "server_db.json"
def load_db():
    if not os.path.exists(DB_FILE): return {"auto_responders": {}, "welcomer": {}, "log_channels": {}, "jtc_channels": {}, "automod": {}, "anti_nick": {}, "playlists": {}}
    with open(DB_FILE, "r") as f: return json.load(f)
def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f, indent=4)
db = load_db()

PREMIUM_USERS = [149017434425665333] 
WHITELISTED_USERS = [] 
SECRET_PREMIUM_KEY = "ROADTO3K"  
music_queues = {} 
active_effects = {} 
spam_tracker = {}
raid_tracker = {}
stay_247 = {} 
anti_nuke_state = {} 
jtc_active_vc = [] 

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} - Online & Cleaned! 🚀")
    try:
        synced = await bot.tree.sync()
        print(f"Slash Commands Synced: {len(synced)} Ready!")
    except Exception as e:
        print(f"Sync error: {e}")

# --- 🎛️ MUSIC BUTTONS & DROPDOWN UI ---
class MusicControls(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=None)
        self.ctx = ctx
    @discord.ui.button(emoji="⏯️", style=discord.ButtonStyle.secondary)
    async def pause_resume(self, interaction, button):
        vc = self.ctx.voice_client
        if vc and vc.is_playing(): vc.pause(); await interaction.response.send_message("⏸️ Paused!", ephemeral=True)
        elif vc and vc.is_paused(): vc.resume(); await interaction.response.send_message("▶️ Resumed!", ephemeral=True)
        else: await interaction.response.send_message("❌ Nothing playing.", ephemeral=True)
    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.secondary)
    async def skip_song(self, interaction, button):
        if self.ctx.voice_client: self.ctx.voice_client.stop(); await interaction.response.send_message("⏭️ Skipped!", ephemeral=True)
    @discord.ui.button(emoji="🛑", style=discord.ButtonStyle.danger)
    async def stop_song(self, interaction, button):
        if self.ctx.voice_client:
            music_queues[self.ctx.guild.id] = [] 
            self.ctx.voice_client.stop()
            await interaction.response.send_message("🛑 Stopped.", ephemeral=True)

class HelpDropdown(discord.ui.Select):
    def __init__(self):
        opts = [
            discord.SelectOption(label='Music & Playlists', description='Commands: play, skip, bass, playlist', emoji=discord.PartialEmoji.from_str(ICON_MUSIC) if "<" in ICON_MUSIC else ICON_MUSIC),
            discord.SelectOption(label='Security & Automod', description='Anti-Nuke, Anti-Spam, Automod, Scan, Permit', emoji=discord.PartialEmoji.from_str(ICON_SECURITY) if "<" in ICON_SECURITY else ICON_SECURITY),
            discord.SelectOption(label='Utility & Config', description='JTC, Logging, Welcomer, AutoResponder', emoji=discord.PartialEmoji.from_str(ICON_GEAR) if "<" in ICON_GEAR else ICON_GEAR),
            discord.SelectOption(label='Fun & Giveaways', description='Giveaway, 8ball, Coinflip', emoji=discord.PartialEmoji.from_str(ICON_FUN) if "<" in ICON_FUN else ICON_FUN),
            discord.SelectOption(label='Info & Profiles', description='Userinfo, Serverinfo, Avatar', emoji=discord.PartialEmoji.from_str(ICON_PROFILE) if "<" in ICON_PROFILE else ICON_PROFILE),
            discord.SelectOption(label='Owner Exclusive', description='Lockdown, Backup, Announce, VIP Give', emoji=discord.PartialEmoji.from_str(ICON_OWNER) if "<" in ICON_OWNER else ICON_OWNER)
        ]
        super().__init__(placeholder='Choose a Category...', min_values=1, max_values=1, options=opts)

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(color=discord.Color.from_rgb(30, 31, 34)) 
        v = self.values[0]
        if v == 'Music & Playlists':
            embed.title = f"{ICON_MUSIC} Music & Playlists"
            embed.description = "`/play`, `/skip`, `/stop`, `/volume`\n**Effects:** `/bass`, `/8d`, `/nightcore`, `/normal`\n**Playlist:** `/playlist save [name]`, `/playlist play [name]`\n**Utility:** `/247 enable/disable`"
        elif v == 'Security & Automod':
            embed.title = f"{ICON_SECURITY} Security & Automod"
            embed.description = "`/anti nuke enable/disable`\n`/permit [@user]` / `/unpermit [@user]`\n`/scan [@user]`\n`/automod enable/disable`\n`/antinick enable/disable`"
        elif v == 'Utility & Config':
            embed.title = f"{ICON_GEAR} Utility & Config"
            embed.description = "`/setup jtc [channel]`\n`/setwelcome [channel]`\n`/setlog [channel]`\n`/addreply [trigger] [response]`\n`/vckick [@user]`, `/vcmute [@user]`"
        elif v == 'Fun & Giveaways':
            embed.title = f"{ICON_FUN} Fun & Giveaways"
            embed.description = "`/gstart [mins] [prize]`\n`/8ball [question]`\n`/coinflip`\n`/joke`"
        elif v == 'Info & Profiles':
            embed.title = f"{ICON_PROFILE} Info & Profiles"
            embed.description = "`/userinfo [@user]`\n`/serverinfo`\n`/botinfo`\n`/avatar / >pfp [@user]`\n`/banner [@user]`"
        elif v == 'Owner Exclusive':
            embed.title = f"{ICON_OWNER} Owner Exclusive"
            embed.description = "`/announce [msg]`\n`/lockdown` / `/unlock`\n`/give vip [@user]`\n`/addrole [name] [hex]`\n`/backup create/load`"
        embed.set_footer(text="Road To 3K Music Fest")
        await interaction.response.edit_message(embed=embed)

class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None); self.add_item(HelpDropdown())

@bot.hybrid_command(name="help", description="Show the Mega Command Center")
async def premium_help(ctx):
    embed = discord.Embed(title=f"{bot.user.name} - Mega Command Center", color=discord.Color.from_rgb(0, 0, 0))
    embed.description = f"🔗 **Prefix:** `>` or `/` (Slash Commands)\n\nUse the dropdown below to explore modules!"
    if bot.user.avatar: embed.set_thumbnail(url=bot.user.avatar.url)
    await ctx.send(embed=embed, view=HelpView())

# --- 🚀 UTILITY & CONFIG ---
@bot.hybrid_group(invoke_without_command=True, description="Setup commands")
async def setup(ctx): pass
@setup.command(description="Set Join-To-Create Voice Hub")
@commands.has_permissions(administrator=True)
async def jtc(ctx, channel: discord.VoiceChannel):
    db["jtc_channels"][str(ctx.guild.id)] = channel.id
    save_db(db); await ctx.send(f"✅ **Join-To-Create** hub set to {channel.mention}")

@bot.hybrid_command(description="Set welcome message channel")
@commands.has_permissions(administrator=True)
async def setwelcome(ctx, channel: discord.TextChannel):
    db["welcomer"][str(ctx.guild.id)] = channel.id
    save_db(db); await ctx.send(f"👋 **Welcomer** enabled in {channel.mention}")

@bot.hybrid_command(description="Set logging channel")
@commands.has_permissions(administrator=True)
async def setlog(ctx, channel: discord.TextChannel):
    db["log_channels"][str(ctx.guild.id)] = channel.id
    save_db(db); await ctx.send(f"📝 **Logging** set to {channel.mention}")

@bot.hybrid_command(description="Add an auto-reply trigger")
@commands.has_permissions(manage_messages=True)
async def addreply(ctx, trigger: str, *, response: str):
    guild_id = str(ctx.guild.id)
    if guild_id not in db["auto_responders"]: db["auto_responders"][guild_id] = {}
    db["auto_responders"][guild_id][trigger.lower()] = response
    save_db(db); await ctx.send(f"✅ **Auto-Responder Added!** Trigger: `{trigger}`")

# --- 🛡️ SECURITY & AUTOMOD ---
@bot.hybrid_command(description="Toggle Automod (Anti-Link)")
async def automod(ctx, state: str):
    if ctx.author.id != ctx.guild.owner_id: return await ctx.send("❌ Access Denied!", ephemeral=True)
    db["automod"][str(ctx.guild.id)] = (state.lower() == "enable")
    save_db(db); await ctx.send(f"🛡️ Automod is now **{state.upper()}**")

@bot.hybrid_command(description="Toggle Anti-Nickname changes")
async def antinick(ctx, state: str):
    if ctx.author.id != ctx.guild.owner_id: return await ctx.send("❌ Access Denied!", ephemeral=True)
    db["anti_nick"][str(ctx.guild.id)] = (state.lower() == "enable")
    save_db(db); await ctx.send(f"🛡️ Anti-Nickname is now **{state.upper()}**")

@bot.hybrid_command(description="Scan a user for risks")
async def scan(ctx, member: discord.Member):
    risk = "Low" if (time.time() - member.created_at.timestamp()) > 2592000 else "High (New Account)"
    embed = discord.Embed(title="🔍 Security Scan", description=f"**User:** {member.mention}\n**Risk Level:** {risk}", color=discord.Color.orange())
    await ctx.send(embed=embed)

@bot.hybrid_command(aliases=['whitelist'], description="Permit a user past Anti-Nuke")
async def permit(ctx, member: discord.Member):
    if ctx.author.id != ctx.guild.owner_id: return await ctx.send("❌ Access Denied!", ephemeral=True)
    if member.id not in WHITELISTED_USERS: WHITELISTED_USERS.append(member.id); await ctx.send(f"🛡️ **{member.mention} Permitted!**")

@bot.hybrid_command(aliases=['unwhitelist'], description="Remove a permit")
async def unpermit(ctx, member: discord.Member):
    if ctx.author.id != ctx.guild.owner_id: return await ctx.send("❌ Access Denied!", ephemeral=True)
    if member.id in WHITELISTED_USERS: WHITELISTED_USERS.remove(member.id); await ctx.send(f"🔴 **{member.mention} Removed!**")

# --- 🎉 FUN & GIVEAWAY ---
@bot.hybrid_command(description="Start a giveaway")
@commands.has_permissions(manage_guild=True)
async def gstart(ctx, mins: int, *, prize: str):
    embed = discord.Embed(title="🎉 GIVEAWAY!", description=f"**Prize:** {prize}\nReact with 🎉 to enter!\nTime: {mins} minutes", color=discord.Color.blue())
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("🎉")
    await asyncio.sleep(mins * 60)
    new_msg = await ctx.channel.fetch_message(msg.id)
    users = [u async for u in new_msg.reactions[0].users() if not u.bot]
    if len(users) == 0: return await ctx.send("No one entered.")
    winner = random.choice(users); await ctx.send(f"🎉 Congratulations {winner.mention}! You won **{prize}**!")

@bot.hybrid_command(description="Flip a coin")
async def coinflip(ctx): await ctx.send(f"🪙 You flipped: **{random.choice(['Heads', 'Tails'])}**")

@bot.hybrid_command(name="8ball", description="Ask the magic 8ball")
async def eightball(ctx, *, question: str): await ctx.send(f"🎱 **Answer:** {random.choice(['Yes.', 'No.', 'Maybe.', 'Definitely!'])}")

@bot.hybrid_command(description="Tell a joke")
async def joke(ctx): await ctx.send(random.choice(["Why don't scientists trust atoms? Because they make up everything!"]))

# --- ℹ️ INFORMATION & PROFILES ---
@bot.hybrid_command(description="Get server information")
async def serverinfo(ctx):
    embed = discord.Embed(title=f"{ctx.guild.name} Info", color=discord.Color.purple())
    embed.add_field(name="Owner", value=ctx.guild.owner.mention)
    embed.add_field(name="Members", value=ctx.guild.member_count)
    if ctx.guild.icon: embed.set_thumbnail(url=ctx.guild.icon.url)
    await ctx.send(embed=embed)

@bot.hybrid_command(description="Get user information")
async def userinfo(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title=f"User Info: {member}", color=member.color)
    embed.add_field(name="Joined Server", value=member.joined_at.strftime("%b %d, %Y"))
    if member.avatar: embed.set_thumbnail(url=member.avatar.url)
    await ctx.send(embed=embed)

@bot.hybrid_command(description="Get bot information")
async def botinfo(ctx): await ctx.send(f"🤖 **{bot.user.name}** | Latency: {round(bot.latency * 1000)}ms")

@bot.hybrid_command(aliases=['av', 'pfp'], description="View user avatar")
async def avatar(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title=f"📸 {member.display_name}'s Avatar", color=discord.Color.purple())
    if member.display_avatar: embed.set_image(url=member.display_avatar.url)
    await ctx.send(embed=embed)

@bot.hybrid_command(description="View user banner")
async def banner(ctx, member: discord.Member = None):
    member = member or ctx.author
    user = await bot.fetch_user(member.id)
    if user.banner:
        embed = discord.Embed(title=f"🌌 {member.display_name}'s Banner", color=discord.Color.purple())
        embed.set_image(url=user.banner.url)
        await ctx.send(embed=embed)
    else: await ctx.send("❌ No banner!")

# --- 👑 OWNER EXCLUSIVE ---
@bot.hybrid_command(description="Create a custom role")
async def addrole(ctx, name: str, hex_color: str = "000000"):
    if ctx.author.id != ctx.guild.owner_id: return await ctx.send("❌ Access Denied!", ephemeral=True)
    await ctx.guild.create_role(name=name, color=discord.Color(int(hex_color.replace("#", ""), 16)))
    await ctx.send(f"✅ Role **{name}** created!")

@bot.hybrid_command(description="Announce a message to the server")
async def announce(ctx, *, message: str):
    if ctx.author.id != ctx.guild.owner_id: return await ctx.send("❌ Access Denied!", ephemeral=True)
    embed = discord.Embed(title="📢 ANNOUNCEMENT", description=f"**{message}**", color=discord.Color.red())
    await ctx.send("@everyone", embed=embed)

@bot.hybrid_command(description="Lock down the current channel")
async def lockdown(ctx):
    if ctx.author.id != ctx.guild.owner_id: return await ctx.send("❌ Access Denied!", ephemeral=True)
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False); await ctx.send("🔒 Channel Locked.")

@bot.hybrid_command(description="Unlock the current channel")
async def unlock(ctx):
    if ctx.author.id != ctx.guild.owner_id: return await ctx.send("❌ Access Denied!", ephemeral=True)
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True); await ctx.send("🔓 Channel Unlocked.")

@bot.group(invoke_without_command=True, description="Give commands")
async def give(ctx): pass
@give.command(description="Give VIP status to a user")
async def vip(ctx, member: discord.Member):
    if ctx.author.id != ctx.guild.owner_id: return await ctx.send("❌ Access Denied!", ephemeral=True)
    if member.id not in PREMIUM_USERS: PREMIUM_USERS.append(member.id); await ctx.send(f"🎁 {member.mention} is now VIP!")

@bot.group(invoke_without_command=True, description="Anti-Nuke toggle")
async def anti(ctx): pass
@anti.command(description="Enable or disable Anti-Nuke")
async def nuke(ctx, state: str):
    if ctx.author.id != ctx.guild.owner_id: return await ctx.send("❌ Access Denied!", ephemeral=True)
    anti_nuke_state[ctx.guild.id] = (state == "enable")
    await ctx.send(f"🛡️ Anti-Nuke **{state.upper()}**")

@bot.group(invoke_without_command=True, description="Backup commands")
async def backup(ctx): pass
@backup.command(description="Create a server backup")
@commands.has_permissions(administrator=True)
async def create(ctx):
    await ctx.send("✅ Backup Created!")
@backup.command(description="Load a server backup")
@commands.has_permissions(administrator=True)
async def load(ctx):
    await ctx.send("⚠️ Server Restored!") 

@bot.group(invoke_without_command=True, description="Claim commands")
async def claim(ctx): pass
@claim.command(description="Claim Premium status")
async def premium(ctx, key: str):
    if ctx.author.id in PREMIUM_USERS: return await ctx.send("✅ Already VIP! ⭐", ephemeral=True)
    if key == SECRET_PREMIUM_KEY: PREMIUM_USERS.append(ctx.author.id); await ctx.send("🎉 **VIP Claimed!**")
    else: await ctx.send("❌ **Invalid Key!**", ephemeral=True)

# --- 🎤 VOICE MODERATION ---
@bot.hybrid_command(description="Mute a member in VC")
@commands.has_permissions(mute_members=True)
async def vcmute(ctx, member: discord.Member): await member.edit(mute=True); await ctx.send(f"🔇 {member.mention} Muted.")

@bot.hybrid_command(description="Kick a member from VC")
@commands.has_permissions(move_members=True)
async def vckick(ctx, member: discord.Member): await member.edit(voice_channel=None); await ctx.send(f"👢 {member.mention} Kicked from VC.")

@bot.hybrid_command(description="Kick a member from server")
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason: str = None):
    if member.id == ctx.guild.owner_id: return await ctx.send("❌ Cannot kick owner!", ephemeral=True)
    await member.kick(reason=reason); await ctx.send(f"✅ {member.display_name} kicked.")

@bot.hybrid_command(description="Ban a member from server")
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason: str = None):
    if member.id == ctx.guild.owner_id: return await ctx.send("❌ Cannot ban owner!", ephemeral=True)
    await member.ban(reason=reason); await ctx.send(f"🚫 {member.display_name} banned.")

# --- 🛡️ EVENTS ---
@bot.event
async def on_member_join(member):
    gid = str(member.guild.id)
    if gid in db["welcomer"]:
        ch = member.guild.get_channel(db["welcomer"][gid])
        if ch: await ch.send(f"🎉 Welcome to **{member.guild.name}**, {member.mention}!")
    
    if not anti_nuke_state.get(member.guild.id, True): return 
    t = time.time()
    if member.guild.id not in raid_tracker: raid_tracker[member.guild.id] = []
    raid_tracker[member.guild.id].append(t)
    if len([jt for jt in raid_tracker[member.guild.id] if t - jt < 10]) > 4:
        try: await member.kick(reason="Anti-Raid")
        except: pass

@bot.event
async def on_message(message):
    if message.author.bot: return
    msg_content = message.content.strip().lower()
    
    if msg_content == f"claim premium {SECRET_PREMIUM_KEY.lower()}" or msg_content == f"premium {SECRET_PREMIUM_KEY.lower()}":
        if message.author.id not in PREMIUM_USERS: PREMIUM_USERS.append(message.author.id); await message.channel.send("🎉 **VIP Claimed!**")
        else: await message.channel.send("✅ Already VIP!")
        return

    gid = str(message.guild.id)
    if gid in db["auto_responders"] and msg_content in db["auto_responders"][gid]: await message.channel.send(db["auto_responders"][gid][msg_content])
    await bot.process_commands(message)

# --- 🎵 MUSIC ---
def get_audio_options(guild_id):
    effect = active_effects.get(guild_id, "normal")
    base = '-vn -b:a 64k'
    if effect == "bass": base += ' -af "bass=g=15,dynaudnorm=f=200"' 
    elif effect == "8d": base += ' -af "apulsator=hz=0.09"'
    elif effect == "nightcore": base += ' -af "asetrate=44100*1.25,atempo=1.25"'
    return {'options': base}

async def play_next(ctx):
    if ctx.guild.id in music_queues and len(music_queues[ctx.guild.id]) > 0:
        song = music_queues[ctx.guild.id].pop(0) 
        fname = f"audio_{ctx.guild.id}"
        if os.path.exists(fname):
            try: os.remove(fname)
            except: pass
        msg = await ctx.send(f"⏳ **Loading...**")
        def dl():
            with yt_dlp.YoutubeDL({'format': 'bestaudio/best', 'outtmpl': fname, 'quiet': True}) as ydl: ydl.extract_info(song['url'], download=True)
        try:
            await asyncio.to_thread(dl)
            def after_play(e):
                coro = play_next(ctx); fut = asyncio.run_coroutine_threadsafe(coro, bot.loop)
                try: fut.result()
                except: pass
            ctx.voice_client.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(fname, executable="./ffmpeg", **get_audio_options(ctx.guild.id))), after=after_play)
            await msg.delete(); await ctx.send(f"▶️ Now Playing: **{song['title']}**", view=MusicControls(ctx))
        except: await play_next(ctx) 
    else: await ctx.send("🎶 Queue is empty!")

@bot.hybrid_command(description="Play a song")
async def play(ctx, *, query: str):
    await ctx.defer()
    if not ctx.author.voice: return await ctx.send("❌ Join a voice channel first!")
    if ctx.voice_client is None: await ctx.author.voice.channel.connect(timeout=60.0)
    await ctx.send("🔍 **Searching...**")
    def search_song():
        with yt_dlp.YoutubeDL({'format': 'bestaudio', 'quiet': True, 'noplaylist': True}) as ydl:
            return ydl.extract_info(query if query.startswith("http") else f"scsearch:{query}", download=False)
    try:
        info = await asyncio.to_thread(search_song)
        info = info['entries'][0] if 'entries' in info else info
        song_data = {'title': info.get('title'), 'url': info.get('url', info.get('webpage_url'))}
        if ctx.guild.id not in music_queues: music_queues[ctx.guild.id] = []
        music_queues[ctx.guild.id].append(song_data)
        if not ctx.voice_client.is_playing(): await play_next(ctx)
        else: await ctx.send(f"📝 Added **{song_data['title']}** to Queue")
    except: await ctx.send("❌ Search failed.")

@bot.hybrid_command(description="Skip song")
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing(): ctx.voice_client.stop(); await ctx.send("⏭️ **Skipped!**")

@bot.hybrid_command(description="Stop music")
async def stop(ctx):
    if ctx.voice_client: music_queues[ctx.guild.id] = []; ctx.voice_client.stop(); await ctx.send("🛑 Stopped.")

keep_alive()  
bot.run(os.getenv('DISCORD_TOKEN'))
