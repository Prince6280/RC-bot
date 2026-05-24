import asyncio
import os
import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp
import random
import time
from keep_alive import keep_alive

# --- BOT CONFIG ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=">", intents=intents, help_command=None)

# --- FFMPEG FIX ---
FFMPEG_PATH = "/usr/bin/ffmpeg" if os.path.exists("/usr/bin/ffmpeg") else "./ffmpeg"

# --- 🔥 SMART SEARCH: JIOSAAVN -> SOUNDCLOUD -> YOUTUBE ---
def get_song_url(query):
    ydl_opts = {'format': 'bestaudio', 'quiet': True, 'noplaylist': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            # 1. JioSaavn Priority (Indian Music King)
            search_terms = [f"saavnsearch:{query}", f"scsearch:{query}", f"ytsearch:{query}"]
            for term in search_terms:
                info = ydl.extract_info(term, download=False)
                if info and info.get('entries'):
                    return info['entries'][0]
        except: return None
    return None

@bot.event
async def on_ready():
    print(f"✅ Oliver is Online (JioSaavn Integrated)")
    await bot.tree.sync()

@bot.hybrid_command(description="Play music from JioSaavn, SoundCloud or YouTube")
async def play(ctx, *, query: str):
    await ctx.defer()
    if not ctx.author.voice: return await ctx.send("❌ Pehle VC mein join ho jao!")
    
    # Connect VC
    if ctx.voice_client is None: await ctx.author.voice.channel.connect()
    else: await ctx.voice_client.move_to(ctx.author.voice.channel)

    await ctx.send(f"🔍 **Searching JioSaavn/SoundCloud:** {query}")
    song = get_song_url(query)
    
    if not song: return await ctx.send("❌ Song nahi mila! Kuch aur try karo.")
    
    # Play
    try:
        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(song['url'], executable=FFMPEG_PATH))
        ctx.voice_client.play(source)
        await ctx.send(f"▶️ Now Playing: **{song['title']}**")
    except Exception as e:
        await ctx.send(f"❌ Playback Error: {e}")

@bot.hybrid_command(description="Stop music")
async def stop(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("🛑 Stopped.")

keep_alive()
bot.run(os.getenv('DISCORD_TOKEN'))
