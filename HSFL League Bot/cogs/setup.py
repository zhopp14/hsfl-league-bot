import urllib.parse


import disnake
from disnake.ext import commands

from utils.config import SETTINGS, not_premium_message, Links
from utils.database import Database
from utils.embed import Embed
from utils.tools import (format_database_data, has_perms, parse_duration,
                         premium_guild_check, premium_user_check)

role_choices = [role["name"] for role in SETTINGS.values() if "Role" in role["name"]]
channel_choices = [
    channel["name"] for channel in SETTINGS.values() if "Channel" in channel["name"]
]
toggle_choices = [toggle for toggle in SETTINGS.keys() if "Toggle" in toggle]
limit_choices = [limit for limit in SETTINGS.keys() if "Limit" in limit]
cooldown_choices = [limit for limit in SETTINGS.keys() if "Cooldown" in limit]

async def setting_embed(sd: dict, pretty_data: str = None):
    embed = Embed(
        title=f"{sd['name']} Settings",
    )
    if pretty_data:
        if pretty_data == "No data":
            len_data = "0"
        else:
            len_data = pretty_data.split(", ")
            len_data = len(len_data)

        embed.description = f"**__Current Data__**\n`Max:` {sd['max']} (You currently have {len_data})\n`Items:` {pretty_data}"
    else:
        embed.description = f"{sd['desc']}"
    return embed


async def get_setting_type(setting_data: dict, inter: disnake.MessageInteraction):
    guild = setting_data["guild"]
    if guild:
        return inter.guild
    else:
        return inter.author



# sd = setting_data
async def add_objects_database(inter, sd: dict, objects: list, max: int):
    await inter.response.defer()
    setting_type = await get_setting_type(sd, inter)
    current_data = await Database.get_data(sd['table'], setting_type.id)
    
    # Handle both list and dict formats
    if current_data is None:
        current_data = []
    elif isinstance(current_data, dict):
        # If it's a dict, extract the list from the first value
        if current_data:
            current_data = list(current_data.values())[0] if isinstance(list(current_data.values())[0], list) else []
        else:
            current_data = []
    elif not isinstance(current_data, list):
        current_data = []
      
    OBJECTS_TO_NOT_ADD_REASONS = ""
    objects_to_remove = []
    for object in objects:
        if type(object) == disnake.Role:
            if await has_perms(object):
                objects_to_remove.append(object)
                OBJECTS_TO_NOT_ADD_REASONS += f"{object.mention} has perms, to prevent abuse, roles with permissions aren't allowed on the bot\n"
        if str(object.id) in [str(item) for item in current_data]:
            objects_to_remove.append(object)
            OBJECTS_TO_NOT_ADD_REASONS += (
                f"\n{object.mention} is already in the `{sd['name']}` table"
            )
    
    # Remove objects that shouldn't be added
    for obj in objects_to_remove:
        if obj in objects:
            objects.remove(obj)

    new = len(current_data) + len(objects)
    if new > max:
        return await inter.send(
            f"You can only have **up to {max} items** in the {sd['name']} table, **If you add these items you will be at {new}**. Remove some items to add new ones. Ending command",
            ephemeral=True,
        )

    if not objects:
        embed = Embed(
            title="All Entrys Failed :(",
            description=f"`Current data:` {await format_database_data(inter, sd['table'], setting_type.id)}",
        )
        embed.add_field(name="Not Adding", value=OBJECTS_TO_NOT_ADD_REASONS)
        return await inter.send(embed=embed, ephemeral=True)

    # Add Objects
    await Database.add_data(
      sd["table"], {setting_type.id: [object.id for object in objects]}
    )

    embed = Embed(
        title="Data Added",
        description=f"`Current data:` {await format_database_data(inter, sd['table'], setting_type.id)}",
    )
    items = [object.mention for object in objects]
    embed.add_field(name="Added", value=", ".join(items))

    if OBJECTS_TO_NOT_ADD_REASONS:
        embed.add_field(name="Not Added", value=OBJECTS_TO_NOT_ADD_REASONS)

    objects.clear()
    return await inter.send(embed=embed, ephemeral=True)


async def remove_objects_database(inter, sd: dict, objects: list):
    await inter.response.defer()
    setting_type = await get_setting_type(sd, inter)
    current_data = await Database.get_data(sd['table'], setting_type.id)
    
    # Handle both list and dict formats
    if current_data is None:
        current_data = []
    elif isinstance(current_data, dict):
        # If it's a dict, extract the list from the first value
        if current_data:
            current_data = list(current_data.values())[0] if isinstance(list(current_data.values())[0], list) else []
        else:
            current_data = []
    elif not isinstance(current_data, list):
        current_data = []
  
    OBJECTS_TO_NOT_REMOVE_REASONS = ""
    objects_to_remove = []
    for object in objects:
        if str(object.id) not in [str(item) for item in current_data]:
            objects_to_remove.append(object)
            OBJECTS_TO_NOT_REMOVE_REASONS += (
                f"\n{object.mention} is not in the {sd['name']} table"
            )
    
    # Remove objects that aren't in the database
    for obj in objects_to_remove:
        if obj in objects:
            objects.remove(obj)
          
    if not objects:
        embed = Embed(
            title="All Entrys Failed :(",
            description=f"`Current data:` {await format_database_data(inter, sd['table'],  setting_type.id)}",
        )
        embed.add_field(name="Not Removing", value=OBJECTS_TO_NOT_REMOVE_REASONS)
        return await inter.send(embed=embed, ephemeral=True)

    # Remove Objects
    for object in objects:
        await Database.delete_data(sd['table'], f"{setting_type.id}/{object.id}")

    embed = Embed(
        title="Data Removed",
        description=f"`Current data:` {await format_database_data(inter, sd['table'], setting_type.id)}",
    )
    items = [object.mention for object in objects]
    embed.add_field(name="Removed", value=", ".join(items))

    if OBJECTS_TO_NOT_REMOVE_REASONS:
        embed.add_field(name="Not Removed", value=OBJECTS_TO_NOT_REMOVE_REASONS)

    return await inter.send(embed=embed, ephemeral=True)


async def toggle_settings(inter: disnake.GuildCommandInteraction, sd: dict):
    await inter.response.defer()
    premium_check_ = await premium_guild_check(inter.guild.id)
    if sd['premium'] and not premium_check_:
      return await inter.send(not_premium_message, ephemeral=True)

    setting_type = await get_setting_type(sd, inter)
    table = sd["table"]

    current_data = await Database.get_data(table, setting_type.id)
    embed = await setting_embed(sd)

    if sd['on_status'] == None:
      if current_data is None or current_data == "Off":  # currently off or no data (means on), so turn off
          await Database.add_data(table, {setting_type.id: "Off"})
          return await inter.send(
              f"❌ **{table} is now off**", embed=embed, ephemeral=True
          )
      else:  # on, so turn off by deleting data
          await Database.delete_data(table, setting_type.id)
          return await inter.send(f"✅ **{table} is now on**", embed=embed, ephemeral=True)

    if sd['on_status'] == "On":
      if current_data == "On": 
          await Database.add_data(table, {setting_type.id: "Off"})
          return await inter.send(
              f"❌ **{table} is now off**", embed=embed, ephemeral=True
          )
      else: # current_data == "Off" or None
          await Database.add_data(table, {setting_type.id: 'On'})
          return await inter.send(f"✅ **{table} is now on**", embed=embed, ephemeral=True)  


async def limit_settings(inter, sd: dict, amount: int):
    await inter.response.defer()
    premium_check_ = await premium_guild_check(inter.guild.id)
    if sd['premium'] and not premium_check_:
      return await inter.send(not_premium_message, ephemeral=True)

    max = sd['max']
    if amount > max:
      return await inter.send(f"The highest number you can put for the {sd['name']} is {max} (You put {amount})", ephemeral=True)

    table = sd['table']
    if not amount or amount == 0:
      
      current_data = await Database.get_data(table, inter.guild.id)
      if not current_data:
        return await inter.send(f"You have no data in the {sd['name']} table to delete")
        
      await Database.delete_data(table, inter.guild.id)
      embed = Embed(title=f"{table} Removed", description=f"The {table} has been removed")
      return await inter.send(embed=embed)

    await Database.add_data(table, {inter.guild.id: amount})
    embed = Embed(title=f"{table} Set", description=f"The {table} has been set to: **{amount}**")
    await inter.send(embed=embed)

async def cooldown_settings(inter, sd, time):
  return


class ChannelsDropdown(disnake.ui.ChannelSelect):
    def __init__(self, inter: disnake.GuildCommandInteraction, add_or_remove: str, setting_data: dict, max: int):
        self.inter = inter
        self.add_or_remove = add_or_remove
        self.setting_data = setting_data
        self.max = max

        super().__init__(
            placeholder="Select channels",
            row=0,
            max_values=setting_data["max"],
            channel_types=[
                disnake.ChannelType.text,
                disnake.ChannelType.news,
                disnake.ChannelType.news_thread,
                disnake.ChannelType.public_thread,
                disnake.ChannelType.private_thread,
            ],
        )

    async def callback(self, inter: disnake.MessageInteraction):
        if self.add_or_remove == "Add":
            await add_objects_database(
                inter, self.setting_data, self.values, self.max
            )
        else:
            await remove_objects_database(
                inter, self.setting_data, self.values
            )




class RolesDropdown(disnake.ui.RoleSelect):
    def __init__(self, inter: disnake.GuildCommandInteraction, add_or_remove: str, setting_data: dict, max: int):
        self.inter = inter
        self.add_or_remove = add_or_remove
        self.setting_data = setting_data
        self.max = max

        super().__init__(
            placeholder="Select roles", row=0, max_values=setting_data["max"]
        )

    async def callback(self, inter: disnake.MessageInteraction):
        if self.add_or_remove == "Add":
            await add_objects_database(
                inter, self.setting_data, self.values, self.max
            )
        else:
            await remove_objects_database(
                inter, self.setting_data, self.values
            )




class ViewAdd(disnake.ui.View):
    def __init__(self, view, inter: disnake.GuildCommandInteraction, add_or_remove: str, setting_data: dict, max: int = None):
        super().__init__()
        self.inter = inter
        self.setting_data = setting_data
        self.max = max
        self.add_item(view(inter, add_or_remove, setting_data, max))

    @disnake.ui.button(label="Back", row=1, emoji="◀")
    async def back_button(
        self, button: disnake.ui.Button, inter: disnake.MessageInteraction
    ):
        embed = await setting_embed(self.setting_data)
        await inter.response.edit_message(
            embed=embed, view=AddRemoveButtons(inter, self.setting_data)
        )

    async def on_timeout(self):
        await self.inter.edit_original_message(
            view=None,
            content="Command has expired, run `/setup` to use the command again",
        )

    async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
        if inter.author.id != self.inter.author.id:
            await inter.response.send_message("This is not your menu!", ephemeral=True)
            return False
        return True



class AddRemoveButtons(disnake.ui.View):
    def __init__(self, inter, setting_data: dict):
        super().__init__()
        self.inter = inter
        self.setting_data = setting_data

    async def on_timeout(self):
        await self.inter.edit_original_message(
            view=None,
            content="Command has expired, run `/setup` to use the command again",
        )

    async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
        if inter.author.id != self.inter.author.id:
            await inter.response.send_message("This is not your menu!", ephemeral=True)
            return False
        return True

    @disnake.ui.button(label="Add", style=disnake.ButtonStyle.green)
    async def add_button(
        self, button: disnake.ui.Button, inter: disnake.MessageInteraction
    ):
        await inter.response.defer()
        sd = self.setting_data
        setting_type = await get_setting_type(sd, self.inter)

        premium_check_ = await premium_guild_check(inter.guild.id)
        if sd['premium'] and not premium_check_:
          return await inter.send(not_premium_message, ephemeral=True)
          
        if premium_check_:
          max = sd['premium_max']
        else:
          max = sd['max']
      
        current_data = await Database.get_data(sd["table"], setting_type.id)
        
        # Handle both list and dict formats
        if current_data is None:
            current_data = []
        elif isinstance(current_data, dict):
            if current_data:
                current_data = list(current_data.values())[0] if isinstance(list(current_data.values())[0], list) else []
            else:
                current_data = []
        elif not isinstance(current_data, list):
            current_data = []
    
        if current_data:
            if len(current_data) >= max:
                return await inter.send(
                    f"You can only have **up to {max} items** in the {sd['name']} table, **you currenty have {len(current_data)}**. Remove some items to add new ones. Ending command",
                    ephemeral=True,
                )

        pretty_data = await format_database_data(
            self.inter, sd["table"], setting_type.id
        )
        embed = await setting_embed(sd, pretty_data)

        if "Role" in sd["name"]:
            await inter.edit_original_message(
                embed=embed,
                view=ViewAdd(RolesDropdown, self.inter, "Add", sd, max),
            )
        else:  # channel
            await inter.edit_original_message(
                embed=embed,
                view=ViewAdd(ChannelsDropdown, self.inter, "Add", sd, max),
            )

    @disnake.ui.button(label="Remove", style=disnake.ButtonStyle.red)
    async def remove_button(
        self, button: disnake.ui.Button, inter: disnake.MessageInteraction
    ):
        await inter.response.defer()
        sd = self.setting_data
        setting_type = await get_setting_type(sd, self.inter)

        premium_check_ = await premium_guild_check(inter.guild.id)
        if sd['premium'] and not premium_check_:
          return await inter.send(not_premium_message, ephemeral=True)

    
        current_data = await Database.get_data(sd["table"], setting_type.id)
        if current_data is None:
            return await inter.send("You don't have any data...", ephemeral=True)
        
        # Handle both list and dict formats
        if isinstance(current_data, dict):
            if not current_data:
                return await inter.send("You don't have any data...", ephemeral=True)
        elif isinstance(current_data, list):
            if not current_data:
                return await inter.send("You don't have any data...", ephemeral=True)

        pretty_data = await format_database_data(
            self.inter, sd["table"], setting_type.id
        )
        embed = await setting_embed(sd, pretty_data)

        if "Role" in sd["name"]:
            await inter.edit_original_message(
                embed=embed,
                view=ViewAdd(RolesDropdown, self.inter, "Remove", sd),
            )
        else:  # channel
            await inter.edit_original_message(
                embed=embed,
                view=ViewAdd(ChannelsDropdown, self.inter, "Remove", sd),
            )


class ServerInviteUrl(disnake.ui.View):
  def __init__(self, server_invite):
    super().__init__(timeout=None)
    self.server_invite = server_invite

    self.add_item(disnake.ui.Button(label='Server Invite', url=server_invite, emoji='🔗')) 

class SetupCommands(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  @commands.slash_command()  # setup
  @commands.has_permissions(administrator=True)
  @commands.bot_has_permissions(embed_links=True)
  async def setup(self, inter: disnake.GuildCommandInteraction):
    return

  @setup.sub_command()
  async def roles(self, inter, setting: str = commands.Param(choices=role_choices)):
    """Role settings"""
    embed = await setting_embed(SETTINGS[setting])
    await inter.response.send_message(
        embed=embed, view=AddRemoveButtons(inter, SETTINGS[setting])
    )

  @setup.sub_command()
  async def channels(self, inter, setting: str = commands.Param(choices=channel_choices)):
    """Channel settings"""
    embed = await setting_embed(SETTINGS[setting])
    await inter.response.send_message(
      embed=embed, view=AddRemoveButtons(inter, SETTINGS[setting])
    )

  @setup.sub_command()
  async def toggle(self, inter, setting: str = commands.Param(choices=toggle_choices)):
    "On/off settings"
    await toggle_settings(inter, SETTINGS[setting])

  @setup.sub_command()
  async def limit(self, inter, setting: str = commands.Param(choices=limit_choices), amount: int = None):
    await limit_settings(inter, SETTINGS[setting], amount)

  #@setup.sub_command()
  #async def cooldown(self, inter, setting: str = commands.Param(choices=limit_choices), time: int = None):
    #time = parse_duration(time)
    #await cooldown_settings(inter, SETTINGS[setting], time)
  
  @setup.sub_command(name="auto-roles-update")
  async def auto_roles_update(self, inter, role: disnake.Role, channel: disnake.TextChannel = None, description: str = None, add_or_remove: str = commands.Param(choices=['Add', 'Remove'], default='Add')):
    if channel == None: channel = inter.channel

    if add_or_remove == 'Add':
        data = await Database.get_data("AutoUpdateRoles", inter.guild.id)
        if not data:
            data = []

        max_limit = 5 if await premium_guild_check(inter.guild) else 1
        if len(data) >= max_limit:
            return await inter.response.send_message(f"You can have only {max_limit} auto role updates at a time (Premium users can have 5 {Links.premium_link})")

        await Database.add_data('AutoUpdateRoles', {inter.guild.id: {role.id: {'channel': channel.id, 'description': description}}})

        embed = Embed(title="Auto Roles Update Set", description=f"{role.mention} will now have all its members and who is currently active in the {channel.mention} channel")
        embed.set_footer(text="The embed will update every 10 minutes")
        await inter.response.send_message(embed=embed)

    if add_or_remove == 'Remove':
        data = await Database.get_data("AutoUpdateRoles", f"{inter.guild.id}/{role.id}")
        if not data:
            return await inter.response.send_message("You have no data cuh", ephemeral=True)
        
        await Database.delete_data("AutoUpdateRoles", f"{inter.guild.id}/{role.id}")
        embed = Embed(title = "Auto Role Deleted", description=f"The {role.mention} won't get updated anymore")
        await inter.response.send_message(embed=embed)
'''
  @setup.sub_command()
  async def bump(self, inter, server_invite: str, server_description: str, bump_channel: disnake.TextChannel):
        """
        Add your server's invite and description so your able to use /bump
        Parameters
        ----------
        server_invite: The invite link to your server
        server_description: A description about your server
        bump_channel: The channel you want other servers to be sent
        """
        guild = inter.guild
        await inter.response.defer()

        parsed_url = urllib.parse.urlparse(server_invite)
        if not parsed_url.scheme in ('http', 'https'):
            return await inter.send("Make sure you are sending a vaild server link")
        
        if len(server_description) > 4096:
            return await inter.send("Your server description has to be under 4096 characters")    

        if not bump_channel.permissions_for(guild.me).send_messages:
            return await inter.send("I don't have permission to send messages in that channel and that is required for this command")

        await Database.add_data('Bump', guild.id, {'invite': server_invite, 'description': server_description, 'channel': bump_channel.id})
    
        await inter.send(f"Bumped Data Saved, here is a preview: (Other bumps will be sent to {bump_channel.mention})")
        preview_embed = Embed(
            title = guild.name,
            description = server_description
        ).set_footer(text = f"{guild.member_count} Members").set_thumbnail(url = guild.icon or None)
        await inter.send(embed=preview_embed, view=ServerInviteUrl(server_invite))
'''


def setup(bot):
  bot.add_cog(SetupCommands(bot))