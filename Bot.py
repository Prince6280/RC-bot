import asyncio
import os
import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp
import random
import time
import json
from keep_alive import keep_alive

# --- BOT CONFIG ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=">", intents=intents, help_command=None)

# Database (Simple JSON)
DB_FILE = "server_db.json"
def load_db():
    if not os.path.exists(DB_FILE): return {"auto_responders": {}, "welcomer": {}, "jtc_channels": {}, "automod": {}, "anti_nick": {}}
    with open(DB_FILE, "r") as f: return json.load(f)
db = load_db()

# --- 🚀 SLASH COMMANDS SYNC ON START ---
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user.name}")
    try:
        synced = await bot.tree.sync()
        print(f"✨ Synced {len(synced)} slash commands!")
    except Exception as e:
        print(f"❌ Sync Error: {e}")

# --- 🎙️ BULLETPROOF VOICE JOIN LOGIC ---
async def join_vc(ctx):
    if not ctx.author.voice:
        await ctx.send("❌ Pehle voice channel mein join ho jao!")
        return None
    channel = ctx.author.voice.channel
    try:
        if ctx.voice_client is None:
            return await channel.connect(timeout=60.0)
        else:
            await ctx.voice_client.move_to(channel)
            return ctx.voice_client
    except Exception as e:
        await ctx.send(f"❌ Connection Error: {e}")
        return None

@bot.hybrid_command(description="Play a song")
async def play(ctx, *, query: str):
    await ctx.defer()
    vc = await join_vc(ctx)
    if not vc: return
    
    await ctx.send(f"🔍 Searching: {query}...")
    def search(): return yt_dlp.YoutubeDL({'format': 'bestaudio', 'quiet': True, 'noplaylist': True}).extract_info(query if query.startswith("http") else f"scsearch:{query}", download=False)
    
    try:
        info = await asyncio.to_thread(search)
        info = info['entries'][0] if 'entries' in info else info
        url = info.get('url', info.get('webpage_url'))
        
        # Audio Play
        if vc.is_playing(): vc.stop()
        vc.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(url, executable="./ffmpeg")))
        await ctx.send(f"▶️ Now playing: **{info['title']}**")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.hybrid_command(description="Stop music")
async def stop(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("🛑 Stopped.")

# --- 🎉 GIVEAWAY SLASH COMMAND ---
@bot.tree.command(name="gstart", description="Start a professional giveaway")
@app_commands.describe(duration="Minutes", winners="Winners Count", prize="Prize Name")
async def gstart(interaction: discord.Interaction, duration: int, winners: int, prize: str):
    embed = discord.Embed(title="🎉 GIVEAWAY!", description=f"**Prize:** {prize}\n**Winners:** {winners}\n**Ends in:** {duration} minutes", color=discord.Color.blue())
    await interaction.response.send_message("Giveaway started!", ephemeral=True)
    msg = await interaction.channel.send(embed=embed)
    await msg.add_reaction("🎉")
    await asyncio.sleep(duration * 60)
    new_msg = await interaction.channel.fetch_message(msg.id)
    users = [u async for u in new_msg.reactions[0].users() if not u.bot]
    if len(users) < winners: await interaction.channel.send("❌ Not enough entries.")
    else:
        win = random.sample(users, winners)
        await interaction.channel.send(f"🎉 Winner(s): {', '.join([w.mention for w in win])}! Won **{prize}**!")

# --- 🛡️ UTILS & AUTOMOD (Brief) ---
@bot.hybrid_command(description="Scan a user for risk")
async def scan(ctx, member: discord.Member):
    risk = "High" if (time.time() - member.created_at.timestamp()) < 2592000 else "Low"
    await ctx.send(f"🔍 **Scan Result for {member.name}:** {risk} Risk")

@bot.hybrid_command(description="Set welcome channel")
@commands.has_permissions(administrator=True)
async def setwelcome(ctx, channel: discord.TextChannel):
    db["welcomer"][str(ctx.guild.id)] = channel.id
    save_db(db); await ctx.send(f"👋 Welcome channel set to {channel.mention}")

# --- 👑 OWNER COMMANDS ---
@bot.hybrid_command(description="Announce something")
async def announce(ctx, *, message: str):
    if ctx.author.id != ctx.guild.owner_id: return await ctx.send("❌ Access Denied!", ephemeral=True)
    await ctx.send("@everyone " + message)

# --- 🛡️ EVENTS ---
@bot.event
async def on_member_join(member):
    gid = str(member.guild.id)
    if gid in db["welcomer"]:
        ch = member.guild.get_channel(db["welcomer"][gid])
        if ch: await ch.send(f"🎉 Welcome {member.mention}!")

keep_alive()
bot.run(os.getenv('DISCORD_TOKEN'))
