import discord, os, asyncio
from discord.ext import commands
from keep_alive import keep_alive

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=">", intents=intents, help_command=None)

async def load_extensions():
    # Cogs folder ke andar ki files load karega
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')

async def main():
    keep_alive()
    async with bot:
        await load_extensions()
        await bot.start(os.getenv('DISCORD_TOKEN'))

asyncio.run(main())
