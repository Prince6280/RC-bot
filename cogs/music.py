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

    def get_ydl_opts(self, bass=False):
        return {
            'format': 'bestaudio', 'default_search': 'scsearch', 'quiet': True,
            'proxy': 'http://185.162.228.163:80', # अपनी WORKING प्रॉक्सी यहाँ डालें
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}]
        }

    @commands.hybrid_command(name="play")
    async def play(self, ctx, *, query: str):
        await ctx.defer()
        if not ctx.author.voice: return await ctx.send("❌ Join VC!")
        if not ctx.voice_client: await ctx.author.voice.channel.connect()

        with yt_dlp.YoutubeDL(self.get_ydl_opts()) as ydl:
            song = ydl.extract_info(query, download=False)['entries'][0]
            if ctx.guild.id not in self.queues: self.queues[ctx.guild.id] = []
            self.queues[ctx.guild.id].append({'title': song['title'], 'url': song['webpage_url']})
            await ctx.send(f"📝 Added: **{song['title']}**")
            if not ctx.voice_client.is_playing(): await self.play_next(ctx)

    async def play_next(self, ctx):
        if self.queues.get(ctx.guild.id):
            song = self.queues[ctx.guild.id].pop(0)
            vol = self.volumes.get(ctx.guild.id, 0.5)
            # Bass filter: bass=g=10
            source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(song['url'], options="-af bass=g=10"), volume=vol)
            ctx.voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop))
            await ctx.send(f"▶️ Playing: **{song['title']}**", view=MusicView(ctx))

    @commands.hybrid_command(name="volume")
    async def volume(self, ctx, vol: int):
        self.volumes[ctx.guild.id] = vol / 100
        if ctx.voice_client and ctx.voice_client.source: ctx.voice_client.source.volume = vol / 100
        await ctx.send(f"🔊 Volume set to {vol}%")

    @commands.hybrid_command(name="stop")
    async def stop(self, ctx):
        await ctx.voice_client.disconnect()
        await ctx.send("⏹️ Stopped!")

async def setup(bot):
    await bot.add_cog(Music(bot))
        
