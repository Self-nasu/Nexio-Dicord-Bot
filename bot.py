import discord
from discord.ext import commands
import os
import asyncio
from flask import Flask
import threading
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Define intents
intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.messages = True
intents.members = True

# Create bot instance
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} - {bot.user.id}')
    try:
        # Set bot activity
        activity = discord.Activity(type=discord.ActivityType.listening, name="Nexions")
        await bot.change_presence(activity=activity)
        print("Bot status set to 'Listening to Nexions'")

        # Sync slash commands
        await bot.tree.sync()
        print("Slash commands synced globally!")
    except Exception as e:
        print(f"Failed to sync commands or set status: {e}")

# Load cogs
async def load_cogs():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and filename not in ['__init__.py', 'firebase.py']:
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                print(f'Loaded Cog: {filename[:-3]}')
            except Exception as e:
                print(f'Failed to load Cog {filename[:-3]}: {e}')

# Main entry point
async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)

# Run the bot
asyncio.run(main())
