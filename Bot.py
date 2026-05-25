import discord, os, asyncio
from discord.ext import commands
from keep_alive import keep_alive

# Intents (Permissions)
intents = discord.Intents.all()

# Bot Setup
bot = commands.Bot(command_prefix=">", intents=intents, help_command=None)

# Cog Loader (ये फोल्डर से फाइलें लोड करता है)
async def load_extensions():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and filename != '__init__.py':
            await bot.load_extension(f'cogs.{filename[:-3]}')
            print(f"✅ Loaded: {filename}")

@bot.event
async def on_ready():
    await bot.tree.sync() # Slash Commands को Discord में रजिस्टर करने के लिए
    print(f"🚀 {bot.user.name} is ONLINE and Hybrid Mode is ACTIVE!")

async def main():
    keep_alive() # सर्वर को 24/7 जगाए रखने के लिए
    async with bot:
        await load_extensions()
        await bot.start(os.getenv('DISCORD_TOKEN'))

if __name__ == '__main__':
    asyncio.run(main())
