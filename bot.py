import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
import aiohttp
import asyncio
from settings import settings


class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

        self.session: aiohttp.ClientSession | None = None
        self.db = None

        self.activity = discord.CustomActivity("Checking Hetzner auction")
        self.status = discord.Status.online

    async def setup_hook(self):
        self.session = aiohttp.ClientSession()

        motor = AsyncIOMotorClient(connect=True)
        motor.get_io_loop = asyncio.get_running_loop
        self.db = motor.hetzner

        await self.load_extension("cogs.hetzner")
        await self.tree.sync()

    async def on_ready(self):
        print(f"Logged in as {self.user}")

    async def close(self):
        if self.session:
            await self.session.close()
        await super().close()


def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    bot = Bot()
    loop.run_until_complete(bot.start(settings.bot_token))


if __name__ == "__main__":
    main()
