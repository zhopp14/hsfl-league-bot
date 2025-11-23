"""
Role Management Cog
Provides comprehensive role management through an interactive menu system
Allows creating, editing, deleting, and managing roles through the bot
"""

import disnake
from disnake.ext import commands
from disnake import Color

from utils.embed import Embed
from utils.tools import get_user_response


class RoleManagerView(disnake.ui.View):
    """Main menu view for role management"""
    
    def __init__(self, bot, inter):
        super().__init__(timeout=300.0)
        self.bot = bot
        self.inter = inter
    
    async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
        if inter.author.id != self.inter.author.id:
            await inter.response.send_message("This is not your menu!", ephemeral=True)
            return False
        if not inter.author.guild_permissions.manage_roles:
            await inter.response.send_message("You need `Manage Roles` permission to use this command!", ephemeral=True)
            return False
        return True
    
    async def on_timeout(self):
        try:
            await self.inter.edit_original_message(
                view=None,
                content="Role management menu has expired. Run `/role-manager` again to use it.",
            )
        except Exception:
            pass
    
    @disnake.ui.button(label="Create Role", style=disnake.ButtonStyle.green, row=0)
    async def create_role_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.defer()
        await inter.send("What would you like to name the role?", ephemeral=True)
        name_response = await get_user_response(self.bot, inter)
        
        if not name_response:
            return await inter.send("Role creation cancelled - no name provided.", ephemeral=True)
        
        try:
            role = await inter.guild.create_role(
                name=name_response,
                reason=f"Role created by {inter.author} ({inter.author.id})"
            )
            embed = Embed(
                title="✅ Role Created",
                description=f"**Role:** {role.mention}\n**ID:** `{role.id}`\n**Name:** {role.name}",
                color=role.color
            )
            await inter.send(embed=embed, view=RoleEditView(self.bot, inter, role))
        except disnake.Forbidden:
            await inter.send("❌ I don't have permission to create roles. Make sure my role is above the role I'm trying to create.", ephemeral=True)
        except Exception as e:
            await inter.send(f"❌ Error creating role: {str(e)}", ephemeral=True)
    
    @disnake.ui.button(label="List Roles", style=disnake.ButtonStyle.blurple, row=0)
    async def list_roles_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.defer()
        
        roles = [role for role in inter.guild.roles if not role.managed and role != inter.guild.default_role]
        roles.sort(key=lambda r: r.position, reverse=True)
        
        if not roles:
            return await inter.send("No manageable roles found in this server.", ephemeral=True)
        
        # Split into chunks of 10 for embed fields
        role_chunks = [roles[i:i+10] for i in range(0, len(roles), 10)]
        
        embed = Embed(
            title="📋 Server Roles",
            description=f"Total manageable roles: **{len(roles)}**\n\nSelect a role to manage:",
            color=disnake.Color.blue()
        )
        
        # Show first chunk
        role_list = "\n".join([f"{i+1}. {role.mention} (`{role.id}`)" for i, role in enumerate(role_chunks[0])])
        embed.add_field(name="Roles (1-10)", value=role_list[:1024] or "None", inline=False)
        
        view = RoleListView(self.bot, inter, roles, 0)
        await inter.send(embed=embed, view=view, ephemeral=True)
    
    @disnake.ui.button(label="Delete Role", style=disnake.ButtonStyle.red, row=0)
    async def delete_role_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.defer()
        await inter.send("Mention the role you want to delete (e.g., @RoleName) or send the role ID:", ephemeral=True)
        role_response = await get_user_response(self.bot, inter)
        
        if not role_response:
            return await inter.send("Role deletion cancelled.", ephemeral=True)
        
        role = None
        # Try to parse as mention
        if role_response.startswith("<@&") and role_response.endswith(">"):
            role_id = int(role_response[3:-1])
            role = inter.guild.get_role(role_id)
        # Try to parse as ID
        else:
            try:
                role_id = int(role_response)
                role = inter.guild.get_role(role_id)
            except ValueError:
                # Try to find by name
                role = disnake.utils.get(inter.guild.roles, name=role_response)
        
        if not role:
            return await inter.send("❌ Role not found. Make sure you mention the role or provide a valid role ID.", ephemeral=True)
        
        if role.managed:
            return await inter.send("❌ Cannot delete managed roles (bot roles, integration roles, etc.).", ephemeral=True)
        
        if role >= inter.author.top_role and inter.author != inter.guild.owner:
            return await inter.send("❌ You cannot delete roles that are higher than or equal to your highest role.", ephemeral=True)
        
        if role >= inter.guild.me.top_role:
            return await inter.send("❌ I cannot delete roles that are higher than or equal to my highest role.", ephemeral=True)
        
        try:
            role_name = role.name
            role_id = role.id
            await role.delete(reason=f"Role deleted by {inter.author} ({inter.author.id})")
            embed = Embed(
                title="✅ Role Deleted",
                description=f"**Role:** {role_name}\n**ID:** `{role_id}`",
                color=disnake.Color.red()
            )
            await inter.send(embed=embed, ephemeral=True)
        except disnake.Forbidden:
            await inter.send("❌ I don't have permission to delete this role.", ephemeral=True)
        except Exception as e:
            await inter.send(f"❌ Error deleting role: {str(e)}", ephemeral=True)
    
    @disnake.ui.button(label="Find Role", style=disnake.ButtonStyle.grey, row=1)
    async def find_role_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.defer()
        await inter.send("Mention the role you want to manage (e.g., @RoleName) or send the role ID:", ephemeral=True)
        role_response = await get_user_response(self.bot, inter)
        
        if not role_response:
            return await inter.send("Role search cancelled.", ephemeral=True)
        
        role = None
        # Try to parse as mention
        if role_response.startswith("<@&") and role_response.endswith(">"):
            role_id = int(role_response[3:-1])
            role = inter.guild.get_role(role_id)
        # Try to parse as ID
        else:
            try:
                role_id = int(role_response)
                role = inter.guild.get_role(role_id)
            except ValueError:
                # Try to find by name
                role = disnake.utils.get(inter.guild.roles, name=role_response)
        
        if not role:
            return await inter.send("❌ Role not found. Make sure you mention the role or provide a valid role ID.", ephemeral=True)
        
        if role.managed:
            return await inter.send("❌ Cannot manage this role (it's a managed role like a bot role).", ephemeral=True)
        
        embed = self._create_role_info_embed(role)
        await inter.send(embed=embed, view=RoleEditView(self.bot, inter, role), ephemeral=True)
    
    def _create_role_info_embed(self, role: disnake.Role) -> Embed:
        """Helper to create role information embed"""
        embed = Embed(
            title=f"📝 Role: {role.name}",
            description=f"**ID:** `{role.id}`\n**Mention:** {role.mention}",
            color=role.color if role.color.value != 0 else disnake.Color.blue()
        )
        
        embed.add_field(name="Position", value=f"{role.position} (from bottom)", inline=True)
        embed.add_field(name="Members", value=len(role.members), inline=True)
        embed.add_field(name="Color", value=f"#{role.color.value:06x}" if role.color.value != 0 else "Default", inline=True)
        embed.add_field(name="Hoisted", value="✅ Yes" if role.hoist else "❌ No", inline=True)
        embed.add_field(name="Mentionable", value="✅ Yes" if role.mentionable else "❌ No", inline=True)
        embed.add_field(name="Managed", value="✅ Yes" if role.managed else "❌ No", inline=True)
        
        if role.permissions.value != 0:
            key_perms = []
            if role.permissions.administrator:
                key_perms.append("Administrator")
            if role.permissions.manage_guild:
                key_perms.append("Manage Server")
            if role.permissions.manage_roles:
                key_perms.append("Manage Roles")
            if role.permissions.manage_channels:
                key_perms.append("Manage Channels")
            if role.permissions.manage_messages:
                key_perms.append("Manage Messages")
            
            if key_perms:
                embed.add_field(name="Key Permissions", value=", ".join(key_perms[:5]), inline=False)
        
        return embed


class RoleListView(disnake.ui.View):
    """View for listing and selecting roles"""
    
    def __init__(self, bot, inter, roles, page):
        super().__init__(timeout=300.0)
        self.bot = bot
        self.inter = inter
        self.roles = roles
        self.page = page
    
    async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
        if inter.author.id != self.inter.author.id:
            await inter.response.send_message("This is not your menu!", ephemeral=True)
            return False
        return True
    
    @disnake.ui.button(label="◀ Previous", style=disnake.ButtonStyle.grey, row=0)
    async def previous_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        if self.page > 0:
            self.page -= 1
        await self._update_embed(inter)
    
    @disnake.ui.button(label="Next ▶", style=disnake.ButtonStyle.grey, row=0)
    async def next_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        max_pages = (len(self.roles) - 1) // 10
        if self.page < max_pages:
            self.page += 1
        await self._update_embed(inter)
    
    @disnake.ui.button(label="Select Role", style=disnake.ButtonStyle.green, row=0)
    async def select_role_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.send_message("Send the number of the role you want to manage (from the list above):", ephemeral=True)
        response = await get_user_response(self.bot, inter)
        
        if not response:
            return await inter.send("Selection cancelled.", ephemeral=True)
        
        try:
            index = int(response) - 1
            if 0 <= index < len(self.roles):
                role = self.roles[index]
                embed = RoleManagerView(self.bot, inter)._create_role_info_embed(role)
                await inter.send(embed=embed, view=RoleEditView(self.bot, inter, role), ephemeral=True)
            else:
                await inter.send("❌ Invalid number. Please select a number from the list.", ephemeral=True)
        except ValueError:
            await inter.send("❌ Please send a valid number.", ephemeral=True)
    
    async def _update_embed(self, inter: disnake.MessageInteraction):
        role_chunks = [self.roles[i:i+10] for i in range(0, len(self.roles), 10)]
        current_chunk = role_chunks[self.page] if self.page < len(role_chunks) else []
        
        embed = Embed(
            title="📋 Server Roles",
            description=f"Total manageable roles: **{len(self.roles)}**\nPage {self.page + 1} of {len(role_chunks)}",
            color=disnake.Color.blue()
        )
        
        start_num = self.page * 10
        role_list = "\n".join([f"{start_num + i + 1}. {role.mention} (`{role.id}`)" for i, role in enumerate(current_chunk)])
        embed.add_field(name=f"Roles ({start_num + 1}-{min(start_num + 10, len(self.roles))})", value=role_list[:1024] or "None", inline=False)
        
        await inter.response.edit_message(embed=embed, view=self)


class RoleEditView(disnake.ui.View):
    """View for editing role properties"""
    
    def __init__(self, bot, inter, role):
        super().__init__(timeout=300.0)
        self.bot = bot
        self.inter = inter
        self.role = role
    
    async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
        if inter.author.id != self.inter.author.id:
            await inter.response.send_message("This is not your menu!", ephemeral=True)
            return False
        if not inter.author.guild_permissions.manage_roles:
            await inter.response.send_message("You need `Manage Roles` permission!", ephemeral=True)
            return False
        if self.role >= inter.author.top_role and inter.author != inter.guild.owner:
            await inter.response.send_message("You cannot edit roles that are higher than or equal to your highest role.", ephemeral=True)
            return False
        return True
    
    async def on_timeout(self):
        try:
            await self.inter.edit_original_message(view=None)
        except Exception:
            pass
    
    @disnake.ui.button(label="Change Name", style=disnake.ButtonStyle.blurple, row=0)
    async def change_name_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.defer()
        await inter.send("What would you like to rename this role to?", ephemeral=True)
        new_name = await get_user_response(self.bot, inter)
        
        if not new_name:
            return await inter.send("Name change cancelled.", ephemeral=True)
        
        try:
            old_name = self.role.name
            await self.role.edit(name=new_name, reason=f"Role renamed by {inter.author} ({inter.author.id})")
            embed = Embed(
                title="✅ Role Name Changed",
                description=f"**Old Name:** {old_name}\n**New Name:** {new_name}",
                color=self.role.color if self.role.color.value != 0 else disnake.Color.green()
            )
            await inter.send(embed=embed, ephemeral=True)
            # Update the role reference
            self.role = inter.guild.get_role(self.role.id)
        except disnake.Forbidden:
            await inter.send("❌ I don't have permission to edit this role.", ephemeral=True)
        except Exception as e:
            await inter.send(f"❌ Error: {str(e)}", ephemeral=True)
    
    @disnake.ui.button(label="Change Color", style=disnake.ButtonStyle.blurple, row=0)
    async def change_color_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.defer()
        await inter.send("Send a hex color code (e.g., #FF0000 for red) or 'default' to remove color:", ephemeral=True)
        color_response = await get_user_response(self.bot, inter)
        
        if not color_response:
            return await inter.send("Color change cancelled.", ephemeral=True)
        
        try:
            if color_response.lower() == "default":
                new_color = disnake.Color.default()
            else:
                # Remove # if present
                hex_color = color_response.lstrip('#')
                # Convert to int
                color_int = int(hex_color, 16)
                new_color = disnake.Color(color_int)
            
            await self.role.edit(color=new_color, reason=f"Role color changed by {inter.author} ({inter.author.id})")
            embed = Embed(
                title="✅ Role Color Changed",
                description=f"**New Color:** #{new_color.value:06x}",
                color=new_color
            )
            await inter.send(embed=embed, ephemeral=True)
            self.role = inter.guild.get_role(self.role.id)
        except ValueError:
            await inter.send("❌ Invalid color format. Use a hex code like #FF0000 or 'default'.", ephemeral=True)
        except disnake.Forbidden:
            await inter.send("❌ I don't have permission to edit this role.", ephemeral=True)
        except Exception as e:
            await inter.send(f"❌ Error: {str(e)}", ephemeral=True)
    
    @disnake.ui.button(label="Toggle Hoist", style=disnake.ButtonStyle.grey, row=0)
    async def toggle_hoist_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.defer()
        try:
            new_hoist = not self.role.hoist
            await self.role.edit(hoist=new_hoist, reason=f"Role hoist toggled by {inter.author} ({inter.author.id})")
            embed = Embed(
                title="✅ Role Hoist Updated",
                description=f"**Hoisted:** {'✅ Yes' if new_hoist else '❌ No'}",
                color=self.role.color if self.role.color.value != 0 else disnake.Color.blue()
            )
            await inter.send(embed=embed, ephemeral=True)
            self.role = inter.guild.get_role(self.role.id)
        except disnake.Forbidden:
            await inter.send("❌ I don't have permission to edit this role.", ephemeral=True)
        except Exception as e:
            await inter.send(f"❌ Error: {str(e)}", ephemeral=True)
    
    @disnake.ui.button(label="Toggle Mentionable", style=disnake.ButtonStyle.grey, row=1)
    async def toggle_mentionable_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.defer()
        try:
            new_mentionable = not self.role.mentionable
            await self.role.edit(mentionable=new_mentionable, reason=f"Role mentionable toggled by {inter.author} ({inter.author.id})")
            embed = Embed(
                title="✅ Role Mentionable Updated",
                description=f"**Mentionable:** {'✅ Yes' if new_mentionable else '❌ No'}",
                color=self.role.color if self.role.color.value != 0 else disnake.Color.blue()
            )
            await inter.send(embed=embed, ephemeral=True)
            self.role = inter.guild.get_role(self.role.id)
        except disnake.Forbidden:
            await inter.send("❌ I don't have permission to edit this role.", ephemeral=True)
        except Exception as e:
            await inter.send(f"❌ Error: {str(e)}", ephemeral=True)
    
    @disnake.ui.button(label="View Info", style=disnake.ButtonStyle.green, row=1)
    async def view_info_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.defer()
        embed = RoleManagerView(self.bot, inter)._create_role_info_embed(self.role)
        await inter.send(embed=embed, ephemeral=True)
    
    @disnake.ui.button(label="Back to Menu", style=disnake.ButtonStyle.grey, row=1)
    async def back_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.defer()
        embed = Embed(
            title="🔧 Role Manager",
            description="Manage all roles in your server through this interactive menu.",
            color=disnake.Color.blue()
        )
        embed.add_field(
            name="Options",
            value="**Create Role** - Create a new role\n**List Roles** - View all server roles\n**Delete Role** - Remove a role\n**Find Role** - Search for a specific role",
            inline=False
        )
        await inter.send(embed=embed, view=RoleManagerView(self.bot, inter), ephemeral=True)


class RoleManagerCommands(commands.Cog):
    """Role management commands for creating and managing server roles"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.slash_command(name="role-manager")
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def role_manager(self, inter: disnake.GuildCommandInteraction):
        """
        Open the role management menu to create, edit, and manage roles
        """
        embed = Embed(
            title="🔧 Role Manager",
            description="Manage all roles in your server through this interactive menu.",
            color=disnake.Color.blue()
        )
        embed.add_field(
            name="Options",
            value="**Create Role** - Create a new role\n**List Roles** - View all server roles\n**Delete Role** - Remove a role\n**Find Role** - Search for a specific role",
            inline=False
        )
        embed.set_footer(text="You need Manage Roles permission to use this command")
        
        await inter.response.send_message(embed=embed, view=RoleManagerView(self.bot, inter), ephemeral=True)


def setup(bot):
    bot.add_cog(RoleManagerCommands(bot))

