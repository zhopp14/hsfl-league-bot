import urllib.parse

import disnake
from disnake.ext import commands

from utils.database import Database
from utils.embed import Embed

async def pickup_host(guild_id, member):
  data = await Database.get_data('PickupHostRole', guild_id)
  if data is None:
    return True
  
  # Handle both list and dict formats
  if isinstance(data, list):
    role_ids = data
  elif isinstance(data, dict):
    role_ids = data.values()
  else:
    return True
      
  for row in role_ids:
    try:
      for role in member.roles:
        if int(role.id) == int(row):
          return True
    except (ValueError, TypeError):
      continue
            
  return False

async def get_pickup_roles(guild):
  roles = []
  pickup_role = await Database.get_data('PickupRole', guild.id)
  if pickup_role is None:
    return
  
  # Handle both list and dict formats
  if isinstance(pickup_role, list):
    role_ids = pickup_role
  elif isinstance(pickup_role, dict):
    role_ids = pickup_role.values()
  else:
    return
    
  for role_id in role_ids:
    try:
      role = guild.get_role(int(role_id))
      if role:
        roles.append(role.mention)
    except (ValueError, TypeError):
      continue
      
  return roles

async def get_pickup_channels(guild):
  channels = []
  pickup_channel = await Database.get_data('PickupChannel', guild.id)
  if pickup_channel is None:
    return
  
  # Handle both list and dict formats
  if isinstance(pickup_channel, list):
    channel_ids = pickup_channel
  elif isinstance(pickup_channel, dict):
    channel_ids = pickup_channel.values()
  else:
    return
    
  for channel_id in channel_ids:
    channel = guild.get_channel_or_thread(int(channel_id))
    if channel:
      channels.append(channel)
      
  return channels

class PickupGameLink(disnake.ui.View):
  def __init__(self, game_link, member):
    super().__init__(timeout=None)
    self.game_link = game_link
    self.member = member

    self.add_item(disnake.ui.Button(label='Game Link', url=game_link, emoji='🔗')) 
    self.add_item(disnake.ui.Button(label='End Game', style=disnake.ButtonStyle.red, custom_id=f"pickup-{member.id}")) 

class PickupCommands(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  @commands.Cog.listener()
  async def on_button_click(self, inter):
    custom_id = inter.component.custom_id
    if custom_id == f"pickup-{inter.author.id}":
      await inter.message.delete()
    
  
  @commands.slash_command()
  async def pickup(self, inter, game_link: str, description: str = None):
    """
    Start a pickup game
    Parameters
    ----------
    game_link: The link where the game is getting played
    description: Any information about the game
    """
    pickup_host_ = await pickup_host(inter.guild.id, inter.author)
    if not pickup_host_:
      return await inter.response.send_message("You are not a pickup host", ephemeral=True)
    
    parsed_url = urllib.parse.urlparse(game_link)
    if not parsed_url.scheme in ('http', 'https'):
      return await inter.response.send_message("Make sure you are sending a vaild game link", ephemeral=True)
    
    p_roles = await get_pickup_roles(inter.guild)
    if p_roles:
      ping = "".join(p_roles)
    else:
      ping = None

    embed = Embed(
        title = "Pickup Game",
        description = f"Started by {inter.author.mention} `{inter.author.display_name}`\n > **Description**: {description}"
    )
    embed.set_thumbnail(url=inter.author.display_avatar.url or None)
    embed.set_footer(text="Make sure there is nothing fishy about the link!")

    p_channel = await get_pickup_channels(inter.guild)
    if p_channel:
      for channel in p_channel:
        await channel.send(embed=embed, content=ping, allowed_mentions=disnake.AllowedMentions(roles=True), view=PickupGameLink(game_link, inter.author))
        await inter.response.send_message(f"Pickup has been sent to {channel.mention}", ephemeral=True)
    else:
      await inter.response.send_message(embed=embed, content=ping, allowed_mentions=disnake.AllowedMentions(roles=True), view=PickupGameLink(game_link, inter.author))

  
  @commands.slash_command()
  async def qbb(self, inter, against: disnake.Member, game_link: str, description: str = None):
    """
    Start a qbb game
    Parameters
    ----------
    against: The player you are going against
    game_link: The link where the game is getting played
    description: Any information about the game
    """
    pickup_host_ = await pickup_host(inter.guild.id, inter.author)
    if not pickup_host_:
      return await inter.response.send_message("You are not a pickup host", ephemeral=True)
    
    parsed_url = urllib.parse.urlparse(game_link)
    if not parsed_url.scheme in ('http', 'https'):
      return await inter.response.send_message("Make sure you are sending a vaild game link", ephemeral=True)
    
    p_roles = await get_pickup_roles(inter.guild)
    if p_roles:
      ping = "".join(p_roles)
    else:
      ping = None

    embed = Embed(
        title = "QBB Game",
        description = f"{inter.author.mention} `{inter.author.display_name}` vs {against.mention} `{against.display_name}`\n > **Description**: {description}"
    )
    embed.set_thumbnail(url=inter.guild.icon or None)
    embed.set_footer(text="Make sure there is nothing fishy about the link!")

    p_channel = await get_pickup_channels(inter.guild)
    if p_channel:
      for channel in p_channel:
        await channel.send(embed=embed, content=ping, allowed_mentions=disnake.AllowedMentions(roles=True), view=PickupGameLink(game_link, inter.author))
        await inter.response.send_message(f"Pickup has been sent to {channel.mention}", ephemeral=True)
    else:
      await inter.response.send_message(embed=embed, content=ping, allowed_mentions=disnake.AllowedMentions(roles=True), view=PickupGameLink(game_link, inter.author))


def setup(bot):
  bot.add_cog(PickupCommands(bot))