import discord
from discord.ext import commands
import os  # Import os to fetch environment variables
import asyncio
from flask import Flask
import threading
from dotenv import load_dotenv  # Import load_dotenv to load .env variables

# Load environment variables from .env file
load_dotenv()
# Get the token from environment variables (stored in Replit secrets)
TOKEN = os.getenv("DISCORD_TOKEN")

# Define the bot with necessary intents
intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.messages = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Event: When the bot is ready
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} - {bot.user.id}')
    try:
        # Set the bot's status to "Listening to Nexions"
        activity = discord.Activity(type=discord.ActivityType.listening, name="Nexions")
        await bot.change_presence(activity=activity)
        print("Bot status set to 'Listening to Nexions'")

        # Sync all slash commands globally
        await bot.tree.sync()
        print("Slash commands synced globally!")
    except Exception as e:
        print(f"Failed to sync commands or set status: {e}")

# Dynamically load all cogs, excluding non-cog files
async def load_cogs():
    for filename in os.listdir('./cogs'):
        # Load only Python files and exclude non-cog utility files
        if filename.endswith('.py') and filename not in ['__init__.py', 'firebase.py']:
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                print(f'Loaded Cog: {filename[:-3]}')
            except Exception as e:
                print(f'Failed to load Cog {filename[:-3]}: {e}')


# Run the bot and web server
async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)

# Start the bot
asyncio.run(main())
