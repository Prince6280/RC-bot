import discord
from discord.ext import commands

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="help", description="Show help menu")
    async def help(self, ctx):
        embed = discord.Embed(title="Oliver Help Menu", color=0x2f3136)
        embed.add_field(name="🛡️ Security", value="`>antinuke`, `>automod`", inline=False)
        embed.add_field(name="🎵 Music", value="`>play`, `>skip`", inline=False)
        embed.add_field(name="⚙️ Utility", value="`>jtc`, `>logs`", inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(General(bot))
