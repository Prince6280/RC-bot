import discord, yt_dlp, asyncio
from discord.ext import commands

class MusicPlayerView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=None)
        self.ctx = ctx

    @discord.ui.button(label="⏸️", style=discord.ButtonStyle.primary)
    async def pause_resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.ctx.voice_client.is_playing():
            self.ctx.voice_client.pause()
            button.label = "▶️"
        else:
            self.ctx.voice_client.resume()
            button.label = "⏸️"
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="⏭️", style=discord.ButtonStyle.secondary)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.ctx.voice_client.stop()
        await interaction.response.send_message("⏭️ Skipped!", ephemeral=True)

    @discord.ui.button(label="⏹️", style=discord.ButtonStyle.danger)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.ctx.voice_client.disconnect()
        await interaction.response.send_message("⏹️ Disconnected!", ephemeral=True)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}

    async def play_next(self, ctx):
        if ctx.guild.id in self.queues and len(self.queues[ctx.guild.id]) > 0:
            song = self.queues[ctx.guild.id].pop(0)
            ydl_opts = {'format': 'bestaudio', 'proxy': 'http://103.152.112.50:8080', 'quiet': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(song['url'], download=False)
                url = info['url']
            
            source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(url, executable="/usr/bin/ffmpeg"))
            ctx.voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop))
            
            embed = discord.Embed(title="Now Playing", description=f"**{song['title']}**", color=discord.Color.red())
            await ctx.send(embed=embed, view=MusicPlayerView(ctx))
        else:
            await ctx.send("🎶 Queue finished!")

    @commands.hybrid_command(name="play")
    async def play(self, ctx, *, query: str):
        await ctx.defer()
        if not ctx.author.voice: return await ctx.send("❌ Join VC!")
        if ctx.voice_client is None: await ctx.author.voice.channel.connect()
        
        ydl_opts = {'format': 'bestaudio', 'default_search': 'scsearch', 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            song = ydl.extract_info(query, download=False)['entries'][0]
            if ctx.guild.id not in self.queues: self.queues[ctx.guild.id] = []
            self.queues[ctx.guild.id].append({'title': song['title'], 'url': song['webpage_url']})
            await ctx.send(f"📝 Added to queue: **{song['title']}**")
            if not ctx.voice_client.is_playing(): await self.play_next(ctx)

async def setup(bot):
    await bot.add_cog(Music(bot))
            
