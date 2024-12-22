import discord
from discord.ext import commands

class ExampleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Slash command: Ping
    @discord.app_commands.command(name="ping", description="Responds with the bot's latency!")
    async def ping(self, interaction: discord.Interaction):
        """Responds with the bot's latency (ping)"""
        latency = round(self.bot.latency * 1000)  # Convert latency to milliseconds
        await interaction.response.send_message(f"Pong! 🏓 Latency: {latency}ms")

# Setup function to load the cog
async def setup(bot):
    await bot.add_cog(ExampleCog(bot))
