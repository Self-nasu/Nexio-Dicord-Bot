import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import random
import string
from firebase_admin import credentials, firestore, initialize_app, get_app
import os
from dotenv import load_dotenv  # Import load_dotenv to load .env variables

# Load environment variables from .env file
load_dotenv()
# Retrieve Firebase credentials from Replit secrets
firebase_creds = os.getenv('FIREBASE_CREDENTIALS')

# Firebase initialization
try:
    app = get_app("projects_app")  # Check if the app already exists
except ValueError:
    # Save the credentials to a temporary file
    with open('firebase_creds.json', 'w') as f:
        f.write(firebase_creds)

    # Initialize the app with the credentials
    cred = credentials.Certificate('firebase_creds.json')
    app = initialize_app(cred, name="projects_app")

    # Optionally remove the temporary file after initializing
    os.remove('firebase_creds.json')

# Access Firestore with the app
db = firestore.client(app)


class ProjectsCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def check_core_team_role(self, interaction: discord.Interaction):
        """Check if the user has the Core Team role."""
        core_team_role = discord.utils.get(interaction.guild.roles, name="Core Team")
        if core_team_role not in interaction.user.roles:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return False
        return True

    @app_commands.command(name="createproject", description="Create a new project and add it to the database.")
    async def create_project(self, interaction: discord.Interaction, 
                             project_name: str, 
                             project_description: str, 
                             project_github_link: str, 
                             project_prototype_link: str = None, 
                             project_image: discord.Attachment = None, 
                             project_leader: discord.Member = None):
        # Check Core Team role
        if not await self.check_core_team_role(interaction):
            return

        # Acknowledge the interaction and defer the response
        await interaction.response.defer(ephemeral=True)
        
        # Generate a unique project ID
        project_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

        # Prepare project data
        project_data = {
            "name": project_name,
            "description": project_description,
            "github_link": project_github_link,
            "prototype_link": project_prototype_link,
            "image_url": project_image.url if project_image else None,
            "leader": project_leader.mention if project_leader else "Unknown",
            "created_at": datetime.utcnow().isoformat()
        }

        # Add to Firestore
        try:
            # Create the project channel
            category = interaction.guild.get_channel(1318943943391580161)  # Project category ID
            project_channel = await category.create_text_channel(name=f"{project_name}")

            # Create the project role
            project_role = await interaction.guild.create_role(name=project_name)

            # Store the project channel and role IDs as strings
            project_data["channel_id"] = str(project_channel.id)
            project_data["role_id"] = str(project_role.id)

            # Add the project data to Firestore
            db.collection("projects").document(project_id).set(project_data)
        except Exception as e:
            await interaction.followup.send(f"Failed to add project to database: {e}", ephemeral=True)
            return

        # Create the embed
        embed = discord.Embed(title=project_name, description=project_description, color=discord.Color.green())
        embed.add_field(name="Project ID", value=project_id, inline=False)
        embed.add_field(name="GitHub Link", value=project_github_link, inline=False)
        if project_prototype_link:
            embed.add_field(name="Prototype Link", value=project_prototype_link, inline=False)
        embed.add_field(name="Leader", value=project_leader.mention if project_leader else "Not specified", inline=False)
        if project_image:
            embed.set_image(url=project_image.url)

        # Send the embed to the specific channel
        project_announcement_channel = interaction.guild.get_channel(1318945614804942878)
        await project_announcement_channel.send(embed=embed)

        # Assign role to the leader
        if project_leader:
            await project_leader.add_roles(project_role)

        # Set permissions for the role in the project channel
        permissions = {
            project_role: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                send_messages_in_threads=True,
                create_public_threads=True,
                create_private_threads=True,
                attach_files=True,
                add_reactions=True,
                use_external_emojis=True,
                use_external_stickers=True,
                read_message_history=True
            ),
            interaction.guild.default_role: discord.PermissionOverwrite(
                view_channel=False  # Deny view_channel for @everyone
            )
        }
        await project_channel.edit(overwrites=permissions)

        # Final confirmation message
        await interaction.followup.send(f"Project {project_name} created successfully!", ephemeral=True)

    @app_commands.command(name="add_member", description="Add a member to the project role.")
    async def add_member(self, interaction: discord.Interaction, member: discord.Member):
        # Get the project role name from the project channel name
        project_channel_name = interaction.channel.name
        project_role_name = project_channel_name.replace("", "")  # Adjust to match your naming conventions
        project_role = discord.utils.get(interaction.guild.roles, name=project_role_name)

        # Retrieve the project document from the database
        project_doc = db.collection("projects").where("channel_id", "==", str(interaction.channel.id)).get()

        if not project_doc:
            await interaction.response.send_message("Project not found in the database.", ephemeral=True)
            return

        project_data = project_doc[0].to_dict()

        # Retrieve the stored channel and role IDs from the database
        stored_channel_id = project_data.get("channel_id")
        stored_role_id = project_data.get("role_id")

        # Check if the command is run in the correct project channel
        if str(interaction.channel.id) != stored_channel_id:
            await interaction.response.send_message(f"This {stored_channel_id} command can only be used in the correct project channel.", ephemeral=True)
            return

        # Check if the user is the project leader
        project_leader_mention = project_data.get("leader")
        if interaction.user.mention != project_leader_mention:
            await interaction.response.send_message("Only the project leader can use this command.", ephemeral=True)
            return

        # Retrieve the project role from the stored role ID
        project_role = discord.utils.get(interaction.guild.roles, id=int(stored_role_id))
        if not project_role:
            await interaction.response.send_message("Project role not found.", ephemeral=True)
            return

        # Add the member to the project role
        try:
            await member.add_roles(project_role)
            await interaction.response.send_message(f"{member.mention} has been added to the project {project_role_name}.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Failed to add member to the project role: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ProjectsCog(bot))
