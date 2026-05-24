import asyncio, os, discord, random, yt_dlp
from discord import app_commands
from discord.ext import commands
from keep_alive import keep_alive

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=">", intents=intents, help_command=None)
FFMPEG_PATH = "/usr/bin/ffmpeg"

# --- DROPEDOWN HELP MENU ---
class HelpDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label='Music', description='Play, Stop, Skip', emoji='🎵'),
            discord.SelectOption(label='Security', description='Antinuke, Automod, Antinick', emoji='🛡️'),
            discord.SelectOption(label='Utility', description='JTC, Auto-responder, Audit Logs', emoji='⚙️'),
            discord.SelectOption(label='Fun/Giveaway', description='Gstart, 8ball, Fun', emoji='🎉'),
        ]
        super().__init__(placeholder='Choose a Category...', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(title=f"{self.values[0]} Commands", color=discord.Color.blurple())
        if self.values[0] == 'Music': embed.description = "/play, /stop"
        elif self.values[0] == 'Security': embed.description = "/antinuke, /automod, /antinick"
        elif self.values[0] == 'Utility': embed.description = "/jtc, /auditlogs, /customrole"
        elif self.values[0] == 'Fun/Giveaway': embed.description = "/gstart"
        await interaction.response.edit_message(embed=embed)

class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(HelpDropdown())

# --- ALL COMMANDS ---
@bot.hybrid_command(name="help")
async def help(ctx):
    embed = discord.Embed(title="Oliver Help Menu", description="Select a category!", color=0x2f3136)
    await ctx.send(embed=embed, view=HelpView())

@bot.tree.command(name="antinuke", description="Toggle Anti-Nuke")
async def antinuke(interaction: discord.Interaction, state: str):
    await interaction.response.send_message(f"🛡️ Anti-Nuke: {state.upper()}")

@bot.tree.command(name="automod", description="Toggle Auto-Mod")
async def automod(interaction: discord.Interaction, state: str):
    await interaction.response.send_message(f"🛡️ Auto-Mod: {state.upper()}")

@bot.tree.command(name="jtc", description="Setup JTC Voice")
async def jtc(interaction: discord.Interaction, channel: discord.VoiceChannel):
    await interaction.response.send_message(f"✅ JTC set to {channel.name}")

@bot.tree.command(name="antinick", description="Enable/Disable Anti-Nick")
async def antinick(interaction: discord.Interaction, state: str):
    await interaction.response.send_message(f"🛡️ Anti-Nick: {state.upper()}")

@bot.tree.command(name="gstart", description="Start a giveaway")
async def gstart(interaction: discord.Interaction, duration: int, winners: int, prize: str):
    await interaction.response.send_message("🎉 Giveaway started!", ephemeral=True)
    msg = await interaction.channel.send(f"🎉 **GIVEAWAY: {prize}**")
    await msg.add_reaction("🎉")

# Yahan apni ProxyScrape se copy ki hui IP aur Port dalein
MY_PROXY = "http://YOUR_IP_HERE:PORT" 

@bot.hybrid_command(description="Play music with Proxy")
async def play(ctx, *, query: str):
    await ctx.defer()
    if not ctx.author.voice: return await ctx.send("❌ Pehle VC join karo!")
    
    # Connection
    channel = ctx.author.voice.channel
    if ctx.voice_client is None: await channel.connect()
    else: await ctx.voice_client.move_to(channel)

    await ctx.send(f"🔍 Searching with Proxy: {query}...")

    # YDL Options with Proxy
    ydl_opts = {
        'format': 'bestaudio',
        'quiet': True,
        'noplaylist': True,
        'proxy': MY_PROXY, # Yahan Proxy active hai
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            # Sirf YouTube Search use karenge (saavnsearch hata diya)
            info = ydl.extract_info(f"ytsearch:{query}", download=False)
            song = info['entries'][0]
            
            source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(song['url'], executable=FFMPEG_PATH))
            ctx.voice_client.play(source)
            await ctx.send(f"▶️ Now Playing: **{song['title']}**")
        except Exception as e:
            await ctx.send(f"❌ Proxy Error: {e}. ProxyScrape se nayi IP check karo!")

@bot.event
async def on_ready():
    await bot.tree.sync()
    print("✅ Oliver is fully loaded with all commands!")

keep_alive()
bot.run(os.getenv('DISCORD_TOKEN'))
