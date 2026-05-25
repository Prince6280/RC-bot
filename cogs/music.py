import discord, yt_dlp, asyncio
from discord.ext import commands

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}

    async def play_next(self, ctx):
        if ctx.guild.id in self.queues and len(self.queues[ctx.guild.id]) > 0:
            song = self.queues[ctx.guild.id].pop(0)
            source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(song['url'], executable="/usr/bin/ffmpeg"))
            ctx.voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop))
            await ctx.send(f"▶️ Now Playing: **{song['title']}**")
        else:
            await ctx.send("🎶 Queue finished!")

    @commands.hybrid_command(name="play", description="Play music")
    async def play(self, ctx, *, query: str):
        await ctx.defer()
        if not ctx.author.voice: return await ctx.send("❌ Join VC first!")
        
        if ctx.voice_client is None: await ctx.author.voice.channel.connect()
        else: await ctx.voice_client.move_to(ctx.author.voice.channel)
        
        ydl_opts = {'format': 'bestaudio', 'default_search': 'scsearch', 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            song = info['entries'][0]
            
            if ctx.guild.id not in self.queues: self.queues[ctx.guild.id] = []
            self.queues[ctx.guild.id].append({'title': song['title'], 'url': song['url']})
            
            await ctx.send(f"📝 Added to queue: **{song['title']}**")
            if not ctx.voice_client.is_playing():
                await self.play_next(ctx)

    @commands.hybrid_command(name="skip", description="Skip song")
    async def skip(self, ctx):
        if ctx.voice_client:
            ctx.voice_client.stop()
            await ctx.send("⏭️ Song skipped!")

async def setup(bot):
    await bot.add_cog(Music(bot))
