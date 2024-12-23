import discord
from discord.ext import commands
from firebase_admin import credentials, firestore, initialize_app, get_app
from datetime import datetime
import os
from dotenv import load_dotenv  

load_dotenv()
firebase_creds = os.getenv('FIREBASE_CREDENTIALS')

try:
    app = get_app("user_app")  
except ValueError:
    with open('firebase_creds.json', 'w') as f:
        f.write(firebase_creds)

    cred = credentials.Certificate('firebase_creds.json')
    app = initialize_app(cred, name="user_app")

    os.remove('firebase_creds.json')

db = firestore.client(app)


class UsersCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="makeprofile", description="Create a profile for the user")
    async def makeprofile(
        self,
        interaction: discord.Interaction,
        display_name: str,
        github: str,
        password: str,
        bio: str = "Cool Awesome member of Nexio Developer Group",
        location: str = None
    ):
        await interaction.response.defer()

        # Validate inputs
        if len(display_name) > 15:
            await interaction.followup.send("Display name must be 15 characters or fewer.")
            return
        if len(bio.split()) > 25:
            await interaction.followup.send("Bio must be 25 words or fewer.")
            return
        if not github.startswith("https://github.com/"):
            await interaction.followup.send("GitHub link must be a valid GitHub profile URL.")
            return

        if not interaction.user.joined_at:
            await interaction.followup.send("Unable to retrieve the member's join date.")
            return

        user_id = str(interaction.user.id)
        user_data = {
            "discord_tag": str(interaction.user),
            "display_name": display_name,
            "bio": bio,
            "github": github,
            "password": password,
            "profile_img_url": interaction.user.display_avatar.url,
            "joined_at": interaction.user.joined_at.isoformat(),  
        }

        if location:
            user_data["location"] = location

        print(user_data)
        try:
            users_ref = db.collection("users")
            users_ref.document(user_id).set(user_data)
            await interaction.followup.send(
                f"Profile created successfully for {interaction.user.mention}!"
            )
        except Exception as e:
            await interaction.followup.send(
                f"An error occurred while creating the profile: {e}"
            )

    @discord.app_commands.command(name="userinfo", description="Fetch a user's profile from the database")
    async def userinfo(self, interaction: discord.Interaction, user: discord.User):

        await interaction.response.defer()  
        user_id = str(user.id)

        try:
          
            users_ref = db.collection("users")
            user_doc = users_ref.document(user_id).get()

            if not user_doc.exists:
                await interaction.followup.send(f"No profile found for {user.mention}.")
                return

            user_data = user_doc.to_dict()

            member_roles = user.roles

            join_date = datetime.fromisoformat(user_data.get('joined_at')).strftime("%d %b %Y")

            embed = discord.Embed(
                title=f"{user_data.get('display_name', user.name)}'s Profile",
                description=user_data.get('bio', "Member of Nexio Developer Group."),
                color=discord.Color.orange()
            )
            embed.set_thumbnail(url=user.display_avatar.url)
            embed.add_field(name="GitHub", value=user_data.get('github', "Not provided"), inline=False)
            embed.add_field(name="Location", value=user_data.get('location', "Not provided"), inline=True)
            embed.set_footer(text=f"Member since: {join_date}")

            verified = user_data.get('verified', False)
            if verified:
                embed.add_field(name="Verified", value="✅", inline=True)
            else:
                embed.add_field(name="Verified", value="Not Verified By Core Team", inline=True)

            await interaction.followup.send(embed=embed)  # This is now public

        except Exception as e:
            await interaction.followup.send(
                f"An error occurred while fetching the profile: {e}"
            )

    @discord.app_commands.command(name="verify", description="Verify a user (core team only)")
    async def verify(self, interaction: discord.Interaction, user: discord.User):

        if not any(role.name.lower() == "core team" for role in interaction.user.roles):
            await interaction.response.send_message("You do not have permission to verify users.", ephemeral=True)
            return

        user_id = str(user.id)
        try:
            users_ref = db.collection("users")
            user_doc = users_ref.document(user_id).get()

            if not user_doc.exists:
                await interaction.response.send_message(f"No profile found for {user.mention}.", ephemeral=True)
                return

            users_ref.document(user_id).update({"verified": True})
            await interaction.response.send_message(f"{user.mention} has been verified!", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(
                f"An error occurred while verifying the user: {e}", ephemeral=True
            )

    @discord.app_commands.command(name="update_bio", description="Update the bio of your profile")
    async def update_bio(self, interaction: discord.Interaction, bio: str):
        user_id = str(interaction.user.id)

        if len(bio.split()) > 25:
            await interaction.response.send_message("Description must be 25 words or fewer.", ephemeral=True)
            return

        try:
            users_ref = db.collection("users")
            user_doc = users_ref.document(user_id).get()

            if not user_doc.exists:
                await interaction.response.send_message(f"No profile found for {interaction.user.mention}.", ephemeral=True)
                return

            users_ref.document(user_id).update({"bio": bio})
            await interaction.response.send_message(f"Your bio has been updated to: {bio}", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(f"An error occurred while updating the bio: {e}", ephemeral=True)

    @discord.app_commands.command(name="update_name", description="Update the display name of your profile")
    async def update_name(self, interaction: discord.Interaction, display_name: str):
        user_id = str(interaction.user.id)

        if len(display_name) > 15:
            await interaction.response.send_message("Display name must be 15 characters or fewer.", ephemeral=True)
            return

        try:
            users_ref = db.collection("users")
            user_doc = users_ref.document(user_id).get()

            if not user_doc.exists:
                await interaction.response.send_message(f"No profile found for {interaction.user.mention}.", ephemeral=True)
                return

            users_ref.document(user_id).update({"display_name": display_name})
            await interaction.response.send_message(f"Your display name has been updated to: {display_name}", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(f"An error occurred while updating the display name: {e}", ephemeral=True)

    @discord.app_commands.command(name="update_github", description="Update the GitHub link of your profile")
    async def update_github(self, interaction: discord.Interaction, github: str):
        user_id = str(interaction.user.id)

        if not github.startswith("https://github.com/"):
            await interaction.response.send_message("GitHub link must be a valid GitHub profile URL.", ephemeral=True)
            return

        try:
            users_ref = db.collection("users")
            user_doc = users_ref.document(user_id).get()

            if not user_doc.exists:
                await interaction.response.send_message(f"No profile found for {interaction.user.mention}.", ephemeral=True)
                return

            users_ref.document(user_id).update({"github": github})
            await interaction.response.send_message(f"Your GitHub link has been updated to: {github}", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(f"An error occurred while updating the GitHub link: {e}", ephemeral=True)

    @discord.app_commands.command(name="update_location", description="Update the location of your profile")
    async def update_location(self, interaction: discord.Interaction, location: str):
        user_id = str(interaction.user.id)

        try:
            users_ref = db.collection("users")
            user_doc = users_ref.document(user_id).get()

            if not user_doc.exists:
                await interaction.response.send_message(f"No profile found for {interaction.user.mention}.", ephemeral=True)
                return

            users_ref.document(user_id).update({"location": location})
            await interaction.response.send_message(f"Your location has been updated to: {location}", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(f"An error occurred while updating the location: {e}", ephemeral=True)

    @discord.app_commands.command(name="update_app_password", description="Update Your App Password")
    async def update_location(self, interaction: discord.Interaction, newpass: str):
        user_id = str(interaction.user.id)

        try:
            users_ref = db.collection("users")
            user_doc = users_ref.document(user_id).get()

            if not user_doc.exists:
                await interaction.response.send_message(f"No profile found for {interaction.user.mention}.", ephemeral=True)
                return

            users_ref.document(user_id).update({"password": newpass})
            await interaction.response.send_message(f"Your Password updated", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(f"An error occurred while updating the location: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(UsersCog(bot))
