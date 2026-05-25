import discord, yt_dlp, asyncio
from discord.ext import commands

class MusicView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=None)
        self.ctx = ctx

    @discord.ui.button(label="⏸️/▶️", style=discord.ButtonStyle.primary)
    async def pause(self, inter: discord.Interaction, button: discord.ui.Button):
        if self.ctx.voice_client.is_playing(): self.ctx.voice_client.pause()
        else: self.ctx.voice_client.resume()
        await inter.response.defer()

    @discord.ui.button(label="⏭️ Skip", style=discord.ButtonStyle.secondary)
    async def skip(self, inter: discord.Interaction, button: discord.ui.Button):
        self.ctx.voice_client.stop()
        await inter.response.send_message("⏭️ Skipped!", ephemeral=True)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}
        self.volumes = {}

    import requests, random

# Free Proxy API से नई प्रॉक्सी लाने वाला फंक्शन
def fetch_fresh_proxy():
    try:
        # यहाँ हम एक ऐसी API का यूज़ कर रहे हैं जो लाइव प्रॉक्सी देती है
        response = requests.get("https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all")
        if response.status_code == 200:
            proxies = response.text.splitlines()
            return f"http://{random.choice(proxies)}"
    except:
        return "http://185.162.228.163:80" # Fallback (अगर API डाउन हो)


    @commands.hybrid_command(name="play")
    async def play(self, ctx, *, query: str):
        await ctx.defer()
        if not ctx.author.voice: return await ctx.send("❌ Join VC!")
        if not ctx.voice_client: await ctx.author.voice.channel.connect()

        # यहा 'ytsearch1:' जोड़ने से बॉट सिर्फ पहला सबसे सटीक रिज़ल्ट ही उठाएगा
        ydl_opts = {
            'format': 'bestaudio',
            'default_search': 'ytsearch1', 
            'quiet': True,
            'proxy': fetch_fresh_proxy() 
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(query, download=False)
                # 'entries' की जगह 'info' को चेक करना ज्यादा सुरक्षित है
                song = info['entries'][0]
            except Exception as e:
                return await ctx.send(f"❌ Error: {str(e)}")

            if ctx.guild.id not in self.queues: self.queues[ctx.guild.id] = []
            self.queues[ctx.guild.id].append({'title': song['title'], 'url': song['webpage_url']})
            await ctx.send(f"📝 Added: **{song['title']}**")
            
            if not ctx.voice_client.is_playing(): await self.play_next(ctx)
                

async def setup(bot):
    await bot.add_cog(Music(bot))
        
