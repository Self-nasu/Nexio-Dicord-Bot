import discord
from discord.ext import commands

class UtilityCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.command()
    async def purge(self, ctx, amount):
        if amount.isdigit():
            amount = int(amount)
            if amount < 1:
                await ctx.send("Amount must be greater than 0")
                return

            deleted = await ctx.channel.purge(limit=amount + 1)
            await ctx.send(f"{len(deleted) - 1} Message(s) purged.", delete_after=30)
        else:
            await ctx.send("Please enter a valid number.", delete_after=1.5)
            await ctx.message.delete()

    @commands.command()
    async def clsuser(self, ctx, user: discord.Member):
        delete = 0
        async for message in ctx.channel.history(limit=500):
            if delete >= 100:
                break
            if message.author == user:
                await message.delete()
                delete += 1

        await ctx.send(f"Purged {delete} messages from {user.display_name}.", delete_after=30)
        await ctx.message.delete()

    @commands.command()
    async def clsbots(self, ctx):
        delete = 0
        async for message in ctx.channel.history(limit=500):
            if delete >= 100:
                break
            if message.author.bot:
                await message.delete()
                delete += 1

        await ctx.send(f"Purged {delete} bot message(s).", delete_after=30)
        await ctx.message.delete()

    @commands.command()
    async def cls(self, ctx):
        delete = 0
        async for message in ctx.channel.history(limit=400):
            if delete >= 100:
                break
            if not message.author.bot:
                await message.delete()
                delete += 1

        await ctx.send(f"Purged {delete} user message(s).", delete_after=30)

    # Slash command: Ping
    @discord.app_commands.command(name="ping", description="Responds with the bot's latency!")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)  # Convert latency to milliseconds
        await interaction.response.send_message(f"Pong! 🏓 Latency: {latency}ms")

# Setup function to load the cog
async def setup(bot):
    await bot.add_cog(UtilityCommands(bot))
