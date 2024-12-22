import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
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
    app = get_app("task_app")  # Check if the app already exists
except ValueError:
    # Save the credentials to a temporary file
    with open('firebase_creds.json', 'w') as f:
        f.write(firebase_creds)

    # Initialize the app with the credentials
    cred = credentials.Certificate('firebase_creds.json')
    app = initialize_app(cred, name="task_app")

    # Optionally remove the temporary file after initializing
    os.remove('firebase_creds.json')

# Access Firestore with the app
db = firestore.client(app)



class TaskboardCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def check_leader_or_core(self, interaction: discord.Interaction, project_data):
        """Check if the user is a project leader or has a Core Team or Management role."""
        core_team_role = discord.utils.get(interaction.guild.roles, name="Core Team")
        management_role = discord.utils.get(interaction.guild.roles, name="Management")

        # Check if the user has Core Team, Management, or is the project leader
        if core_team_role in interaction.user.roles or management_role in interaction.user.roles:
            return True
        # Check if the user is the project leader (using the leader tag in the project doc)
        project_leader_tag = project_data.get('leader')
        if project_leader_tag and interaction.user.mention == project_leader_tag:
            return True
        
        # If the user is not authorized
        await interaction.response.send_message("You do not have permission to give tasks.", ephemeral=True)
        return False

    async def get_project_data(self, interaction: discord.Interaction):
        """Get project data based on the channel where the command was invoked."""
        project_channel_id = str(interaction.channel.id)
        try:
            project_doc = db.collection("projects").where("channel_id", "==", project_channel_id).get()
            if not project_doc:
                await interaction.response.send_message("This command can only be used in a project channel.", ephemeral=True)
                return None
            project_data = project_doc[0].to_dict()
            project_id = project_doc[0].id  # Use the document ID as the project ID
            project_data['project_id'] = project_id  # Add project_id to the data for easier access
            return project_data
        except Exception as e:
            print(f"Error fetching project data: {e}")
            await interaction.response.send_message("An error occurred while fetching project data.", ephemeral=True)
            return None


    async def get_project_role(self, interaction: discord.Interaction, project_data):
        """Fetch the project role from the project document."""
        project_role_id = project_data.get('role_id')
        project_role = discord.utils.get(interaction.guild.roles, id=int(project_role_id))
        return project_role

    @app_commands.command(name="give_task", description="Assign a task to a user in the project.")
    async def give_task(self, interaction: discord.Interaction, 
                        task_name: str, 
                        task_description: str, 
                        deadline_days: int, 
                        assigned_user: discord.User):
        """Assign a task to a user, create task data, and store it in Firestore."""
        
        # Defer response to make sure the bot waits
        await interaction.response.defer()
    
        print("Fetching project data...")  # Debugging line
        # Get project data to ensure this is a valid project channel
        project_data = await self.get_project_data(interaction)
        if not project_data:
            print("Project data not found")  # Debugging line
            return
    
        print("Checking user authorization...")  # Debugging line
        # Check if the user is authorized (Project leader/Core Team/Management)
        if not await self.check_leader_or_core(interaction, project_data):
            print("User not authorized")  # Debugging line
            return
    
        project_id = project_data.get('project_id')  # Access project_id from the document's ID
    
        # Ensure the assigned user is a member of the project role
        project_role = await self.get_project_role(interaction, project_data)
        if project_role and project_role not in assigned_user.roles:
            print(f"{assigned_user} is not a member of the project role")  # Debugging line
            await interaction.followup.send(f"{assigned_user.mention} is not a member of the project role.", ephemeral=True)
            return
    
        # Generate the task ID
        task_number = len(db.collection("tasks").where("project_id", "==", project_id).get()) + 1
        task_id = f"{assigned_user.name}_{task_number}"
    
        # Calculate the deadline date from the current date and the number of days
        deadline_date = (datetime.utcnow() + timedelta(days=deadline_days)).strftime("%Y-%m-%d %H:%M:%S")
    
        # Prepare the task data
        task_data = {
            "task_name": task_name,
            "task_description": task_description,
            "deadline": deadline_date,
            "task_status": "On going",
            "task_id": task_id,
            "project_id": project_id,
            "assigned_by": str(interaction.user),
            "assigned_to": str(assigned_user),
            "created_at": datetime.utcnow().isoformat()
        }
    
        try:
            print("Saving task data...")  # Debugging line
            # Save task data in the assigned user's tasks collection
            user_id = str(assigned_user.id)
            db.collection("users").document(user_id).collection("tasks").document(task_id).set(task_data)
    
        except Exception as e:
            print(f"Error while saving task: {e}")  # Debugging line
            await interaction.followup.send(f"Failed to assign the task: {e}", ephemeral=True)
            return
    
        # Create an embed to notify the user
        embed = discord.Embed(
            title=f"{task_name}",
            description=task_description,
            color=discord.Color.orange()
        )
        embed.add_field(name="Deadline", value=deadline_date, inline=False)
        embed.add_field(name="Assigned To", value=assigned_user.mention, inline=False)
        embed.add_field(name="Assigned By", value=interaction.user.mention, inline=False)
        embed.add_field(name="Task ID", value=task_id, inline=False)
        embed.set_footer(text=f"Project: {project_data.get('name')}")
    
        # Notify the assigned user and the project channel
        await interaction.followup.send(embed=embed)
        await interaction.followup.send(f"{assigned_user.mention}")

    @app_commands.command(name="tasklist", description="Fetch a list of tasks for a user.")
    async def tasklist(self, interaction: discord.Interaction, target: discord.User = None):
        """Fetch tasks for a specific user."""
        if target is None:
            # If no user is specified, fetch tasks for the command invoker
            target = interaction.user

        # Fetch tasks for the specific user
        user_tasks = db.collection("users").document(str(target.id)).collection("tasks").get()
        if not user_tasks:
            await interaction.response.send_message(f"{target.mention} has no tasks assigned.", ephemeral=True)
            return

        task_list = []
        numbererr = 1
        for task in user_tasks:
            task_data = task.to_dict()
            deadline = task_data['deadline']
            task_name = task_data['task_name']
            task_status = task_data['task_status']
            task_list.append(f"**{numbererr}. {task_name}** - {task_status}\nDeadline: {deadline}")
            numbererr += 1

        task_list_str = "\n\n".join(task_list)
        embed = discord.Embed(
            title=f"Tasks Assigned to {target.name}",
            description=task_list_str,
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed)


    @app_commands.command(name="project_tasklist", description="Fetch a list of tasks for a specific project.")
    async def project_tasklist(self, interaction: discord.Interaction, role: discord.Role = None):
        if role is None:
            await interaction.response.send_message('Please provide a project role for input.', ephemeral=True)
            return
    
        # Defer response to allow time for processing
        await interaction.response.defer()
    
        # Fetch project data
        project_doc = db.collection("projects").where("role_id", "==", str(role.id)).get()
        if not project_doc:
            await interaction.followup.send("No project found.", ephemeral=True)
            return None
    
        project_data = project_doc[0].to_dict()
        project_id = project_doc[0].id  # Use the document ID as the project ID
        project_data['project_id'] = project_id   
    
        # Check if the user has authorization
        if not await self.check_leader_or_core(interaction, project_data):
            await interaction.followup.send("You are not authorized to use this command.", ephemeral=True)
            return
    
        project_name = project_data.get('name')
    
        # Get members with the role
        members_with_role = role.members
        if not members_with_role:
            await interaction.followup.send("No members found with this role.", ephemeral=True)
            return
    
        # Prepare task list
        all_tasks = []
        for member in members_with_role:
            # Fetch only tasks belonging to the project for each member
            user_tasks = db.collection("users").document(str(member.id)).collection("tasks").where("project_id", "==", project_id).get()
            for task in user_tasks:
                task_data = task.to_dict()
                task_name = task_data['task_name']
                task_status = task_data['task_status']
                deadline = task_data['deadline']
                all_tasks.append(f"{member.mention}: **{task_name}** - {task_status}\nDeadline: {deadline}")
    
        if not all_tasks:
            await interaction.followup.send("No tasks found for members in this role within the specified project.", ephemeral=True)
            return
    
        # Send the tasks in an embed
        task_list_str = "\n\n".join(all_tasks)
        embed = discord.Embed(
            title=f"{project_name} Tasks",
            description=task_list_str,
            color=discord.Color.orange()
        )
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(TaskboardCog(bot))
