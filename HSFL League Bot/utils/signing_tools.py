import disnake
import unidecode

from utils.config import Links, Keywords, SETTINGS
from utils.database import Database
from utils.embed import Embed
from utils.tools import premium_guild_check, get_mentions, guild_members

async def team_check(guild_id: int, team: disnake.Role):
  """Checks if the role being used is in the teams database"""
  team_data = await Database.get_data("TeamRole", guild_id)
  if team_data is None or not isinstance(team_data, (list, dict)):
    return False
    
  # Handle both list and dict formats
  if isinstance(team_data, list):
    team_ids = team_data
  else:
    team_ids = team_data.values() if isinstance(team_data, dict) else []
    
  for team_id in team_ids:
    try:
      if int(team.id) == int(team_id):
        return True
    except (ValueError, TypeError):
      continue
  return False  

async def get_team_owner(guild: disnake.Guild, team: disnake.Role):
  """Find a user with a top FranchiseRole on the team, list[0]"""
  coach_roles = await Database.get_data('FranchiseRole', guild.id)
  if coach_roles is None or not isinstance(coach_roles, (list, dict)):
    return None

  # Handle both list and dict formats
  if isinstance(coach_roles, list):
    role_ids = coach_roles
  else:
    role_ids = coach_roles.values() if isinstance(coach_roles, dict) else []

  if not role_ids:
    return None

  team_users = await guild_members(guild, team)
  owner_role_id = role_ids[0]

  try:
    owner_role = guild.get_role(int(owner_role_id))
  except (ValueError, TypeError):
    return None

  if not owner_role:
     return None

  for user in team_users:
    if owner_role in user.roles:
       return user
  return None

async def send_notfication_channel(guild: disnake.Guild, embed: disnake.Embed, content: str = None):
  channel_ids = await Database.get_data("NotficationChannel", guild.id)
  if channel_ids is None:
    return
  
  # Handle both list and dict formats
  if isinstance(channel_ids, list):
    ids = channel_ids
  elif isinstance(channel_ids, dict):
    ids = channel_ids.values()
  else:
    return
    
  for channel_id in ids:
    try:
      channel = guild.get_channel_or_thread(int(channel_id))
      if channel:
        await channel.send(embed=embed, content=content, allowed_mentions=disnake.AllowedMentions.all())
    except (ValueError, TypeError, AttributeError):
      continue
    except Exception as e:
      print(f"Error sending to notification channel {channel_id}: {e}")
      continue


async def send_to_channel_type(guild: disnake.Guild, channel_type: str, embed: disnake.Embed, content: str = None):
  """
  Send an embed to all configured channels for a specific command type.
  
  channel_type: The command type (e.g., 'Transactions', 'Offers', 'Demands')
  embed: The embed to send
  content: Optional content message
  """
  channel_ids = await get_channel_config(guild.id, channel_type)
  if not channel_ids:
    return
  
  for channel_id in channel_ids:
    try:
      channel = guild.get_channel_or_thread(int(channel_id))
      if channel:
        await channel.send(embed=embed, content=content, allowed_mentions=disnake.AllowedMentions.all())
    except (ValueError, TypeError, AttributeError):
      continue
    except Exception as e:
      print(f"Error sending to {channel_type} channel {channel_id}: {e}")
      continue


async def roster_cap(guild: disnake.Guild, team: disnake.Role, add_amount: int = 0):
  """
  Checks if your under the league's roster cap
  add_amount: Checking if multiple users can fix the cap, like for trading 
  """
  cap = await Database.get_data('RosterCap', guild.id)
  if cap is None:
      return True, f'[No roster cap set]({Links.premium_link})'

  try:
      cap_value = int(cap)
  except (ValueError, TypeError):
      return True, f'[No roster cap set]({Links.premium_link})'

  current_cap = len(await guild_members(guild, team)) + add_amount
  #current_cap = sum(1 for member in await guild.chunk() if team in member.roles)

  if current_cap >= cap_value:
      return False, f'The {team.name} are currently at or over the roster cap ({current_cap}/{cap_value})'
  return True, f'{current_cap}/{cap_value}'


async def under_contract(guild: disnake.Guild, member: disnake.Member):
  contract = await Database.get_data('Users', guild.id)
  if contract is None or not isinstance(contract, dict):
    return False, 'No contract data'
  
  user_data = contract.get(str(member.id))
  if user_data and isinstance(user_data, dict) and "contract" in user_data:
    return True, f"{member.display_name} is currently under contract, a DM is being sent to see if they want to terminate the contract \n **Contract Details:** {user_data['contract']}"
  
  return False, f'{member.display_name} not on a contract'


async def suspension_check(guild_id, member: disnake.Member):
  """Checks if a user is suspeneded"""
  data = await Database.get_data("Suspensions", guild_id)
  if data is None or not isinstance(data, dict):
    return False, 'No suspension data'
    
  user_suspension = data.get(str(member.id))
  if user_suspension and isinstance(user_suspension, dict):
    duration = user_suspension.get('duration', 'Unknown')
    return True, f"**{member.display_name}** is suspended and can't be signed till: `{duration}`"
  
  return False, f'{member.display_name} is not suspended'  


async def demand_limit_check(guild_id, member):
  demand_limit = await Database.get_data('DemandLimit', guild_id)
  if demand_limit is None:
    return True, f'[No demand limit set]({Links.premium_link})' 

  try:
      limit_value = int(demand_limit)
  except (ValueError, TypeError):
      return True, f'[No demand limit set]({Links.premium_link})'

  # 10
  user_demands = await Database.get_data("Users", f'{guild_id}/{member.id}/demands')
  if user_demands is None:
    return True, 'Able to demand'

  try:
      demands_value = int(user_demands)
  except (ValueError, TypeError):
      demands_value = 0

  if limit_value <= demands_value:
    return False, f'Unable to demand, you have already used all your demands (demand limit: {limit_value})'
  return True, 'Able to demand'

# Rings
# Logs?
async def auto_setup(guild):
    embed = Embed(
        title = "Signing System has been Automatically Setup!",
        description = "See the more settings with `/setup` or use `/helpsigning` for help",
    )

    for name, keywords in [
        ("Franchise Role", Keywords.FRANCHISE_ROLES_KEYWORDS),
        ("Free Agent Role", Keywords.FREE_AGENT_ROLES_KEYWORDS),
        ('Team Role', Keywords.TEAM_ROLES_KEYWORDS),
        ("Suspension Role", Keywords.SUSPENED_ROLES_KEYWORDS),
        ("Signing Channel", Keywords.TRANSACTION_CHANNELS_KEYWORDS),
        ("Offering Channel", Keywords.OFFER_CHANNELS_KEYWORDS),
        ("Demanding Channel", Keywords.DEMAND_CHANNELS_KEYWORDS)
    ]:
        
        max_limit = SETTINGS[name].get('max')
        ids = [
            str(item.id)
            for item in (guild.roles if "Role" in name else guild.channels)
            if any(keyword.lower() in unidecode.unidecode(item.name).lower() for keyword in keywords)
        ][:max_limit]
        if ids:
            premium_setting = SETTINGS[name].get("premium")
            if premium_setting:
              p_check = await premium_guild_check(guild.id)
              if not p_check:
                continue # consider trying preiume message
                
            table = name.replace(" ", "")
            await Database.add_data(table, {guild.id: ids})
            mentions = await get_mentions(ids, guild)
            embed.add_field(name = name, value = ", ".join(mentions))

    return embed if len(embed.fields) > 0 else None



# make look cooler?
async def auto_add_object(object):
    """PREMIUM: Same as auto_setup but just when a user creates a role or channel"""
    p_check = await premium_guild_check(object.guild.id)
    if not p_check:
      return
  
    embed = Embed(
        title="Role/Channel Added to the Database!",
    )
    embed.set_footer(text="You can remove this with /setup")

    async def check_and_validate_data(current_data, max_limit):
        if current_data and str(object.id) in current_data:
            return None
        if current_data and len(current_data) >= max_limit:
            return None
        return True

    for name, keywords in [
        ("Franchise Role", Keywords.FRANCHISE_ROLES_KEYWORDS),
        ("Free Agent Role", Keywords.FREE_AGENT_ROLES_KEYWORDS),
        ('Team Role', Keywords.TEAM_ROLES_KEYWORDS),
        ("Suspension Role", Keywords.SUSPENED_ROLES_KEYWORDS),
        ("Signing Channel", Keywords.TRANSACTION_CHANNELS_KEYWORDS),
        ("Offering Channel", Keywords.OFFER_CHANNELS_KEYWORDS),
        ("Demanding Channel", Keywords.DEMAND_CHANNELS_KEYWORDS)
    ]:
        table = name.replace(" ", "")
        object_name = [keyword for keyword in keywords if keyword in unidecode.unidecode(object.name).lower()]

        if type(object) == disnake.Role:
            if object_name and 'Role' in table:
                max_limit = SETTINGS[name].get('max')
                current_data = await Database.get_data(table, object.guild.id)
                validation_result = await check_and_validate_data(current_data, max_limit)
                if validation_result is None:
                    return None
                await Database.add_data(table, {object.guild.id: [object.id]})
                embed.add_field(name=name, value=object.mention)
        else:
            if object_name and 'Channel' in table:
                max_limit = SETTINGS[name].get('max')
                current_data = await Database.get_data(table, object.guild.id)
                validation_result = await check_and_validate_data(current_data, max_limit)
                if validation_result is None:
                    return None
                  
                await Database.add_data(table, {object.guild.id: [object.id]})
                embed.add_field(name=name, value=object.mention)

    return embed if len(embed.fields) > 0 else None


async def get_coach_team(guild_id: int, member: disnake.Member) -> disnake.Role:
  """
  Get the team assigned to a coach/staff member.
  Returns the team Role if found, None otherwise.
  """
  coach_mapping = await Database.get_data('CoachTeamMapping', guild_id)
  if not coach_mapping or not isinstance(coach_mapping, dict):
    return None
  
  team_id = coach_mapping.get(str(member.id))
  if not team_id:
    return None
  
  try:
    team = member.guild.get_role(int(team_id))
    return team
  except (ValueError, TypeError):
    return None


async def set_coach_team(guild_id: int, coach_id: int, team: disnake.Role) -> tuple[bool, str]:
  """
  Assign a coach/staff member to a team.
  Returns (success: bool, message: str)
  """
  coach_mapping = await Database.get_data('CoachTeamMapping', guild_id)
  if not coach_mapping:
    coach_mapping = {}
  elif not isinstance(coach_mapping, dict):
    return False, "Invalid coach mapping data"
  
  coach_mapping[str(coach_id)] = str(team.id)
  await Database.add_data('CoachTeamMapping', {guild_id: coach_mapping})
  return True, f"Coach {coach_id} assigned to {team.mention}"


async def remove_coach_team(guild_id: int, coach_id: int) -> tuple[bool, str]:
  """
  Remove a coach/staff member from team assignment.
  Returns (success: bool, message: str)
  """
  coach_mapping = await Database.get_data('CoachTeamMapping', guild_id)
  if not coach_mapping or not isinstance(coach_mapping, dict):
    return False, "No coach mapping found"
  
  if str(coach_id) not in coach_mapping:
    return False, "This coach is not assigned to a team"
  
  del coach_mapping[str(coach_id)]
  await Database.add_data('CoachTeamMapping', {guild_id: coach_mapping})
  return True, f"Coach removed from team assignment"


async def get_team_coaches(guild: disnake.Guild, team: disnake.Role) -> list[disnake.Member]:
  """
  Get all coaches/staff assigned to a team.
  Returns list of Member objects.
  """
  coach_mapping = await Database.get_data('CoachTeamMapping', guild.id)
  if not coach_mapping or not isinstance(coach_mapping, dict):
    return []
  
  team_coaches = []
  for coach_id, assigned_team_id in coach_mapping.items():
    if str(team.id) == str(assigned_team_id):
      try:
        member = await guild.fetch_member(int(coach_id))
        if member:
          team_coaches.append(member)
      except (ValueError, TypeError, disnake.NotFound):
        continue
  
  return team_coaches


async def validate_team_ownership(guild_id: int, member: disnake.Member, team: disnake.Role) -> tuple[bool, str]:
  """
  Validate that a member has the right to execute commands for a team.
  Checks if member is assigned as coach/owner for this team.
  Returns (is_valid: bool, message: str)
  """
  assigned_team = await get_coach_team(guild_id, member)
  if not assigned_team:
    return False, f"You are not assigned as a coach/owner for any team"
  
  if assigned_team.id != team.id:
    return False, f"You are assigned to {assigned_team.mention}, not {team.mention}"
  
  return True, "Valid team ownership"


async def auto_detect_team(guild_id: int, member: disnake.Member) -> disnake.Role:
  """
  Automatically detect the team for a coach/staff member.
  Returns the team Role if found, None otherwise.
  """
  return await get_coach_team(guild_id, member)


async def set_channel_config(guild_id: int, channel_type: str, channel_id: int) -> tuple[bool, str]:
  """
  Set a channel for a specific command type.
  channel_type: 'Transactions', 'Offers', 'Demands', 'Trades', etc.
  Returns (success: bool, message: str)
  """
  channel_config = await Database.get_data('ChannelConfig', guild_id)
  if not channel_config:
    channel_config = {}
  elif not isinstance(channel_config, dict):
    return False, "Invalid channel config data"
  
  if channel_type not in channel_config:
    channel_config[channel_type] = []
  elif not isinstance(channel_config[channel_type], list):
    channel_config[channel_type] = []
  
  if channel_id not in channel_config[channel_type]:
    channel_config[channel_type].append(channel_id)
  else:
    return False, f"Channel {channel_id} is already configured for {channel_type}"
  
  await Database.add_data('ChannelConfig', {guild_id: channel_config})
  return True, f"Channel configured for {channel_type}"


async def remove_channel_config(guild_id: int, channel_type: str, channel_id: int) -> tuple[bool, str]:
  """
  Remove a channel from a specific command type.
  Returns (success: bool, message: str)
  """
  channel_config = await Database.get_data('ChannelConfig', guild_id)
  if not channel_config or not isinstance(channel_config, dict):
    return False, f"No channels configured for {channel_type}"
  
  if channel_type not in channel_config:
    return False, f"No channels configured for {channel_type}"
  
  if not isinstance(channel_config[channel_type], list):
    return False, f"Invalid configuration for {channel_type}"
  
  if channel_id not in channel_config[channel_type]:
    return False, f"Channel {channel_id} is not configured for {channel_type}"
  
  channel_config[channel_type].remove(channel_id)
  
  if not channel_config[channel_type]:
    del channel_config[channel_type]
  
  await Database.add_data('ChannelConfig', {guild_id: channel_config})
  return True, f"Channel removed from {channel_type}"


async def get_channel_config(guild_id: int, channel_type: str) -> list[int]:
  """
  Get all channel IDs configured for a specific command type.
  Returns list of channel IDs.
  """
  channel_config = await Database.get_data('ChannelConfig', guild_id)
  if not channel_config or not isinstance(channel_config, dict):
    return []
  
  channels = channel_config.get(channel_type, [])
  if isinstance(channels, list):
    return channels
  return []


async def get_all_channel_config(guild_id: int) -> dict:
  """
  Get all channel configurations for the guild.
  Returns dict of channel_type: [channel_ids]
  """
  channel_config = await Database.get_data('ChannelConfig', guild_id)
  if not channel_config or not isinstance(channel_config, dict):
    return {}
  return channel_config


async def check_channel_config(inter: disnake.GuildCommandInteraction, channel_type: str) -> tuple[bool, str]:
  """
  Check if a command is being used in an allowed channel for the given type.
  Returns (is_allowed: bool, error_message_or_empty_string: str)
  """
  channel_ids = await get_channel_config(inter.guild.id, channel_type)
  
  if not channel_ids:
    return True, ""
  
  if inter.channel.id in channel_ids:
    return True, ""
  
  channel_mentions = []
  for ch_id in channel_ids:
    try:
      channel = inter.guild.get_channel(int(ch_id))
      if channel:
        channel_mentions.append(channel.mention)
    except (ValueError, TypeError):
      continue
  
  if channel_mentions:
    return False, f"You can only use this command in: {', '.join(channel_mentions)}"
  
  return False, f"No valid channels configured for {channel_type}"