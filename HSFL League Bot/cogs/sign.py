import disnake
from disnake.ext import commands

from utils.config import BotEmojis, not_premium_message
from utils.database import Database
from utils.embed import Embed
from utils.signing_tools import (demand_limit_check, roster_cap,
                                 send_notfication_channel, suspension_check,
                                 team_check, under_contract, get_coach_team,
                                 validate_team_ownership, auto_detect_team,
                                 get_team_coaches, check_channel_config, send_to_channel_type)
from utils.tools import (format_database_data, has_perms, has_role,
                         premium_guild_check, add_roles, remove_roles)

# add demand amount to leaugeinto and userinfo


def error_embed(title, description):
  embed = Embed(title, description).danger_embed()
  return embed

async def check_toggle(table: str, guild_id: int):
  """Checks if a command is able to be used"""
  data = await Database.get_data(table, guild_id)
  if data is None:
      return True  # If no data, command is enabled by default
  if data == "Off":
      return False
  return True

async def check_channel(table: str, inter):
  """Checks if a command is being used in the right channel"""
  data = await Database.get_data(table, inter.guild.id)

  if data is None: # no data, does not matter where you do the command
    return True

  # Handle both list and dict formats
  if isinstance(data, list):
    channel_ids = data
  elif isinstance(data, dict):
    channel_ids = data.values()
  else:
    return True

  current_channel = inter.channel.id
  for channel_id in channel_ids:
    try:
      if int(current_channel) == int(channel_id):
        return True
    except (ValueError, TypeError):
      continue

  return await format_database_data(inter, table, inter.guild.id) 

async def transaction_checks(inter, on_table: str, channel_type: str, team: disnake.Role):
  """Checks all transactions commands use"""
  check_toggle_ = await check_toggle(on_table, inter.guild.id)
  if not check_toggle_:
      return "Transactions are currently off"

  if await has_perms(team):
      return "To prevent abuse, roles with permissions aren't allowed to be used in signing commands"

  if team > inter.author.top_role:
      return "To prevent abuse, roles that are higher then your highest role can't be used on the bot"
  
  return True

async def on_team(guild_id, member):
  signed_check = await has_role("TeamRole", guild_id, member)
  if signed_check:
    return f'**{member.display_name}** is already signed to a team'
  return True

async def on_same_team(guild_id, member1, member2):
  """Checks if two members are on the same team"""
  member1 = await has_role("TeamRole", guild_id, member1, 'id')
  member2 = await has_role("TeamRole", guild_id, member2, 'id')
  if member1 and member2:
    if member1 == member2:
      return True
  return False

  

async def premium_checks(inter, team: disnake.Role, member: disnake.Member = None):
  """Checks only premium guilds get to use + suspension_check"""
  team_check_ = await team_check(inter.guild.id, team)
  if not team_check_:
    return f"The `{team}` role is not in the teams database"

  if member != None:
    if member.bot:
      return f"**{member.display_name}** is a bot, and bot's can't be used in signing commands sadly :sob:"
  
  return True


async def promote_member(inter, member: disnake.Member, coach_role: disnake.Role):
    author_role_id = await has_role('FranchiseRole', inter.guild.id, inter.author, 'id')
    if not author_role_id:
        return False, "You don't have a franchise role"
    author_coach_role = inter.guild.get_role(int(author_role_id))
    if not author_coach_role:
        return False, "Your franchise role was not found"
  
    coach_roles = await Database.get_data("FranchiseRole", inter.guild.id)
    if coach_roles is None:
        return False, "No franchise roles configured"
    
    # Handle both list and dict formats
    if isinstance(coach_roles, list):
        role_ids = coach_roles
    elif isinstance(coach_roles, dict):
        role_ids = coach_roles.values()
    else:
        return False, "Invalid franchise role data"
    
    member_coach_role = None
    for ref in role_ids:
        try:
            if int(ref) == int(coach_role.id):
                member_coach_role = inter.guild.get_role(int(ref))
                break
        except (ValueError, TypeError):
            continue

    if member_coach_role is None:
        return False, 'That role is not in the database'

    if author_coach_role.position > member_coach_role.position:
        return True, member_coach_role
          
    if author_coach_role.position == member_coach_role.position:
        return False, "You have the same role position"
          
    if author_coach_role.position < member_coach_role.position:
        error_message = (f"Your role is not high enough\n"
                         f"{member_coach_role} <- His role\n"
                         f"{author_coach_role} <- Your role")
        return False, error_message

async def demote_command(inter, member: disnake.Member):
    member_coach_role = await has_role("FranchiseRole", inter.guild.id, member, "id")
    author_coach_role = await has_role("FranchiseRole", inter.guild.id, inter.author, "id")

    if not member_coach_role:
        return False, f"{member.display_name} is not even a coach BOZO"

    member_coach_role = inter.guild.get_role(int(member_coach_role))
    author_coach_role = inter.guild.get_role(int(author_coach_role))
    if author_coach_role.position > member_coach_role.position:
        return True, member_coach_role
      
    if author_coach_role.position == member_coach_role.position:
        return False, "Your role is not high enough (You have the same role position)"
      
    if author_coach_role.position < member_coach_role.position:
        error_message = (f"Your role is not high enough\n"
                         f"{member_coach_role} <- His role\n"
                         f"{author_coach_role} <- Your role")
        return False, error_message

async def sign_checks(inter, team, member):
  """Checks if you are able to be signed"""
  roster_check = await roster_cap(inter.guild, team)
  if not roster_check[0]:
      return False, roster_check[1]
    
  signed_check = await has_role("TeamRole", inter.guild.id, member)
  if signed_check:
    return False, 'You are already signed to a team'

  suspension_check_ = await suspension_check(inter, member)
  if suspension_check_[0]:
    return False, suspension_check_[1]

  return True, 'Able to be signed'

async def accept_release(inter, kwargs):
    command_inter = kwargs['inter']
    team = kwargs['team']
    member = kwargs['member']
    guild = kwargs['guild']
    await inter.response.defer()

    try:
      await member.remove_roles(team)
      await remove_roles(inter, 'AfterSignRole', member, guild)  
      await add_roles(inter, 'FreeAgentRole', member, guild)
    except Exception as e:
      await command_inter.send(e)

    embed = Embed(
        title='Franchise Releasing', 
        description=f'{member.mention} `{member.display_name}` has accepted their release request and has been **released** from the {team.mention} **with their contract terminated**\n > **Coach:** {inter.author.mention}',
    )
    await embed.league_embed(user=inter.author, guild=guild, role=team)
    await command_inter.send(embed=embed)

    await send_notfication_channel(guild, embed)
    await send_to_channel_type(guild, 'Transactions', embed)
    await inter.send(f"You have been released from the {team}", ephemeral=True)
    await Database.delete_data('Users', f"{guild.id}/{member.id}/contract")


async def decline_release(inter, kwargs):
    command_inter = kwargs['inter']
    team = kwargs['team']
    member = kwargs['member']
    guild = kwargs['guild']
    await inter.response.defer(ephemeral=True)

    embed = Embed(
        title='Franchise Release Declined', 
        description=f'{member.mention} `{member.display_name}` has declined their release request from the {team.mention} \n > **Coach:** {inter.author.mention}',
    )
    await embed.league_embed(user=inter.author, guild=guild, role=team)
    await command_inter.send(embed=embed)

    await inter.send(f"You have vetoed the release request from the {team}", ephemeral=True)


class AcceptDeclineView(disnake.ui.View):
  def __init__(self, **kwargs):
    super().__init__()
    self.kwargs = kwargs
    self.inter = kwargs['inter']
    self.inter_check = kwargs['inter_check']

  async def on_timeout(self):
    # might need tot make a functin for dis cringe
    await self.inter.edit_original_message(
      view=None,
      content="Command has expired, run `/release` to use the command again",
    )

  async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
    if inter.author.id != self.inter_check.id:
            await inter.response.send_message("This is not your menu!", ephemeral=True)
            return False
    return True

  @disnake.ui.button(
      label="Accept",
      emoji=BotEmojis.check_mark,
      style=disnake.ButtonStyle.green
  )
  async def accept_button(self, button, inter):
    await inter.response.defer()
    try:
      await self.kwargs['accept_function'](inter, self.kwargs)
    except Exception as e:
      try:
        if not inter.response.is_done():
          await inter.response.defer(ephemeral=True)
      except AttributeError:
        # If is_done doesn't exist, just try to defer
        try:
          await inter.response.defer(ephemeral=True)
        except Exception:
          pass
      await inter.send(f"Error: {str(e)}", ephemeral=True)


  @disnake.ui.button(
    label="Decline",
    emoji=BotEmojis.x_mark,
    style=disnake.ButtonStyle.red
  )
  async def decline_button(self, button, inter):
    await inter.response.defer(ephemeral=True)
    try:
      await self.kwargs['decline_function'](inter, self.kwargs)
    except Exception as e:
      try:
        if not inter.response.is_done():
          await inter.response.defer(ephemeral=True)
      except AttributeError:
        # If is_done doesn't exist, just try to defer
        try:
          await inter.response.defer(ephemeral=True)
        except Exception:
          pass
      await inter.send(f"Error: {str(e)}", ephemeral=True)


class DemoteThenRelease(disnake.ui.View):
    def __init__(self, inter, member: disnake.Member, team: disnake.Role, coach: disnake.Role, guild: disnake.Guild):
        super().__init__()
        self.inter = inter
        self.member = member
        self.team = team
        self.coach = coach
        self.guild = guild

    async def on_timeout(self):
        await self.inter.edit_original_message(
            view=None,
            content="Command has expired, run `/release` to use the command again",
        )

    async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
        if inter.author.id != self.inter.author.id:
            await inter.response.send_message("This is not your menu!", ephemeral=True)
            return False
        return True

    @disnake.ui.button(label="Demote then release?")
    async def button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
      await inter.response.defer()
      try:
        await self.member.remove_roles(self.coach)
        await self.member.remove_roles(self.team)
        await remove_roles(inter, 'AfterSignRole', self.member, self.guild)  
        await add_roles(inter, 'FreeAgentRole', self.member, self.guild)
      except Exception as e:
        await self.inter.send(e)


      embed = Embed(
          title='Franchise Releasing', 
          description=f'{self.member.mention} `{self.member.display_name}` has been **demoted and released** from the {self.team.mention}\n > **Coach:** {self.inter.author.mention}',
      )
      await embed.league_embed(user=self.inter.author, guild=self.inter.guild, role=self.team)
      await inter.send(embed=embed)
      await send_to_channel_type(self.inter.guild, 'Transactions', embed)
      await inter.message.edit(view=None)
      self.stop()


class OfferButtons(disnake.ui.View):
  def __init__(self, inter, member: disnake.Member, team: disnake.Role, guild: disnake.Guild, contract: str):
    super().__init__(timeout=870)#870
    self.inter = inter
    self.member = member
    self.team = team
    self.guild = guild
    self.contract = contract
    
  async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
        if inter.author.id != self.member.id:
            await inter.response.send_message("This is not your menu!", ephemeral=True)
            return False
        return True
    
    # find out issue with dis
  async def on_timeout(self):
    embed = Embed(
        title='Offer Timed Out', 
        description=f'The {self.team.mention} offer for {self.member.mention} `{self.member.display_name}` has timed out\n > **Coach:** {self.inter.author.mention} \n > **Contract:** {self.contract}',
    )
    await embed.league_embed(user=self.inter.author, guild=self.inter.guild, role=self.team)
    await self.inter.edit_original_message(view=None, embed=embed)
    self.stop()
    
  @disnake.ui.button(
    label = "Accept",
    emoji=BotEmojis.check_mark, 
    style = disnake.ButtonStyle.green 
  )
  async def accept_button(self, button: disnake.ui.Button, inter):
    await inter.response.defer()
    sign_checks_ = await sign_checks(self.inter, self.team, self.member)
    if not sign_checks_[0]:
      embed = Embed(title="Unable to be signed", description=sign_checks_[1])
      embed.set_footer(text="This a Bread Winner Premium only check, thanks for your support").danger_embed()
      return await inter.send(embed=embed, ephemeral=True)
    
    roster_check = await roster_cap(self.inter.guild, self.team)
    
    embed = Embed(
        title='Offer Accpeted', 
        description=f'{self.member.mention} `{self.member.display_name}` has **accepted**  the {self.team.name} offer\n > **Coach:** {self.inter.author.mention}\n > **Roster Cap:** {roster_check[1]} \n > **Contract:** {self.contract}',
    )
    await embed.league_embed(user=self.inter.author, guild=self.inter.guild, role=self.team)
    
    #await self.inter.message.edit(embed=embed, view=None)
    await self.inter.edit_original_message(embed=embed, view=None)
    await inter.send(f"You have been signed to the {self.team}", ephemeral=True)
    
    await send_to_channel_type(self.inter.guild, 'Transactions', embed)

    try:
      await self.member.add_roles(self.team)
      await add_roles(inter, 'AfterSignRole', self.member, self.guild)  
      await remove_roles(inter, 'FreeAgentRole', self.member, self.guild)
    except Exception as e:
        await self.inter.send(e)

    if self.contract:   
        await Database.add_data(
            'Users',
            {
                self.inter.guild.id: {
                    self.member.id: {'contract': self.contract}
                }
            },
        )     
    self.stop()
        

  @disnake.ui.button(
    label = "Decline",
    emoji=BotEmojis.x_mark, 
    style = disnake.ButtonStyle.red 
  )
  async def decline_button(self, button: disnake.ui.Button, inter):    

    await inter.response.defer()
    embed = Embed(
        title='Offer Declined', 
        description=f'{self.member.mention} `{self.member.display_name}` has **declined**  the {self.team.name} offer\n > **Coach:** {self.inter.author.mention} \n > **Contract:** {self.contract}',
    )
    await embed.league_embed(user=self.inter.author, guild=self.inter.guild, role=self.team)
    await self.inter.edit_original_message(embed=embed, view=None)
    await inter.send(f"You have declined the {self.team} offer", ephemeral=True)
    self.stop()  
    

class SignCommands(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  @commands.slash_command()
  async def sign(self, inter: disnake.GuildCommandInteraction):
    await inter.response.send_message("The sign command has been removed use `/offer`", ephemeral=True)


  @commands.slash_command()
  async def offer(self, inter: disnake.GuildCommandInteraction, member: disnake.Member, team: disnake.Role = None, contract: str = None):
    """
    Offer a player to your team
    Parameters
    ----------
    member: The player to offer
    team: The team to offer with (auto-detected if you're an assigned coach)
    contract: PREMIUM ONLY Add a contract to the offer
    """  
    await inter.response.defer()

    coach_role_check = await has_role('FranchiseRole', inter.guild.id, inter.author)
    if not coach_role_check:
        return await inter.send(embed=error_embed("Not a Coach", "You have to be a coach to use this command"), delete_after=10)

    if inter.author.id == member.id:
      return await inter.send(embed=error_embed("Can't Do That", "You can't run commands on yourself"), delete_after=10)

    if team is None:
      team = await auto_detect_team(inter.guild.id, inter.author)
      if team is None:
        return await inter.send(embed=error_embed("Team Required", "You must specify a team parameter"), delete_after=10)

    tr_checks = await transaction_checks(inter, "Signing", "Offers", team)
    if tr_checks != True:
      return await inter.send(embed=error_embed("Check Failed", tr_checks), delete_after=10)

    if team not in inter.author.roles:
      return await inter.send(embed=error_embed("Not On Team", f"You're not on the `{team.name}`"), delete_after=10)

    if team in member.roles:
      return await inter.send(embed=error_embed("Already Signed", f"**{member.display_name}** is already signed to the `{team}`"), delete_after=10)

    p_check = await premium_guild_check(inter.guild.id)
    if not p_check and contract:
      return await inter.send(embed=error_embed('Not Premium', not_premium_message), delete_after=10)

    if p_check:  
      p_checks = await premium_checks(inter, team, member)
      if p_checks != True:
        embed = error_embed('Unable to do this', p_checks)
        embed.set_footer(text="This a Bread Winner Premium only check, thanks for your support")
        return await inter.send(embed=embed, delete_after=10)

      sign_checks_ = await sign_checks(inter, team, member)
      if not sign_checks_[0]:
        embed = Embed(title="Unable to be signed", description=sign_checks_[1])
        embed.set_footer(text="This a Bread Winner Premium only check, thanks for your support").danger_embed()
        return await inter.send(embed=embed, delete_after=10)
      
    roster_check_ = await roster_cap(inter.guild, team)
    embed = Embed(
        title='Offer Notification', 
        description=f'{member.mention} `{member.display_name}` has been **offered** to join the {team.name}\n > **Coach:** {inter.author.mention} \n > **Roster Cap:** {roster_check_[1]} \n > **Contract:** {contract}',
    )

    await embed.league_embed(user=inter.author, guild=inter.guild, role=team)

    contract = contract or None
    view = OfferButtons(inter, member, team, inter.guild, contract)

    offer_dm = await Database.get_data('OfferDM', inter.guild.id)
    if offer_dm is not None and (offer_dm == 'On' or offer_dm == 'on'):
      try:
          m_embed = embed.copy()
          m_embed.description += f'\n > **Channel Link:** {inter.channel.jump_url}'
          await member.send(embed=m_embed, view=view)
      except disnake.HTTPException:
          embed.add_field(name="Message Not Send", value=f"\n > Due to {member.mention} privacy settings, I can't send the message to their DMs")
      await inter.send(embed=embed)
    else:
      try:
          m_embed = embed.copy()
          m_embed.description += f'\n > **Channel Link:** {inter.channel.jump_url}'
          await member.send(embed=m_embed)
      except disnake.HTTPException:
          embed.add_field(name="Message Not Send", value=f"\n > Due to {member.mention} privacy settings, I can't send the message to their DMs")
      await inter.send(embed=embed, view=view)


  @commands.slash_command()
  async def release(self, inter: disnake.GuildCommandInteraction, member: disnake.Member, team: disnake.Role = None):
    """
    Release a player from your team
    Parameters
    ----------
    member: The player to release
    team: The team to release the player from (auto-detected if you're an assigned coach)
    """  
    await inter.response.defer()
    
    coach_role_check = await has_role('FranchiseRole', inter.guild.id, inter.author)
    if not coach_role_check:
        return await inter.send(embed=error_embed("Not a Coach", "You have to be a coach to use this command"), delete_after=10)

    if inter.author.id == member.id:
      return await inter.send(embed=error_embed("Can't Do That", "You can't run commands on yourself"), delete_after=10)
    
    if team is None:
      team = await auto_detect_team(inter.guild.id, inter.author)
      if team is None:
        return await inter.send(embed=error_embed("Team Required", "You must specify a team parameter"), delete_after=10)
    
    tr_checks = await transaction_checks(inter, "Signing", "Transactions", team)
    if tr_checks != True:
      return await inter.send(embed=error_embed("Check Failed", tr_checks), delete_after=10)

    if team not in inter.author.roles:
      return await inter.send(embed=error_embed("Not On Team", f"You're not on the `{team.name}`"), delete_after=10)
    
    if not team in member.roles:
      return await inter.send(embed=error_embed("Not Signed", f"**{member.display_name}** is not signed to the `{team}`"), delete_after=10)
      
    p_check = await premium_guild_check(inter.guild.id)    
    if p_check:    
      p_checks = await premium_checks(inter, team, member)
      if p_checks != True:
        embed = error_embed('Unable to do this', p_checks)
        embed.set_footer(text="This a Bread Winner Premium only check, thanks for your support")
        return await inter.send(embed=embed, delete_after=10)
      under_contract_ = await under_contract(inter.guild, member)
      if under_contract_[0]:
          embed = error_embed(title="Under Contract", description=under_contract_[1])
          embed.set_footer(text="This a Bread Winner Premium only check, thanks for your support")
          await inter.send(embed=embed)   

          contract_release_embed = Embed(
              title="Release Request", 
              description=f"{inter.author.mention} `{inter.author.display_name}` has tried to release you, but as your currently under contract, you have the power to veto the release"
          )
          await embed.league_embed(user=inter.author, guild=inter.guild, role=team)
          #return await member.send(embed=contract_release_embed, view=ContractRelease(inter, member, team, inter.guild))
          return await member.send(embed=contract_release_embed, view=AcceptDeclineView(accept_function=accept_release, decline_function=decline_release, inter=inter, member=member, team=team, guild=inter.guild, inter_check=member))
        

    
    check_coach_member = await has_role('FranchiseRole', inter.guild.id, member)
    if check_coach_member:
        coach_role_id = await has_role('FranchiseRole', inter.guild.id, member, 'id')
        coach_role = inter.guild.get_role(int(coach_role_id))  
        return await inter.send(embed=error_embed(title="Coach", description=f"**{member.display_name}** is a coach, you can't release a coach, demote him first"), view=DemoteThenRelease(inter, member, team, coach_role, inter.guild))

    roster_cap_ = await roster_cap(inter.guild, team)
    # make delte 1 bc it gets len before you remove roles

    embed = Embed(
        title="Franchise Releasing", 
        description=f'{member.mention} `{member.display_name}` has been **released** from the {team.name} offer\n > **Coach:** {inter.author.mention}\n > **Roster Cap:** {roster_cap_[1]}',
    )
    await embed.league_embed(user=inter.author, guild=inter.guild, role=team)
    await inter.send(embed=embed)
    await send_to_channel_type(inter.guild, 'Transactions', embed)

    trade_block = await Database.get_data('TradeBlock', f'{inter.guild.id}/{member.id}')
    if trade_block is not None and isinstance(trade_block, dict):
      try:
        await Database.delete_data('TradeBlock', f'{inter.guild.id}/{member.id}')
        channel = inter.guild.get_channel_or_thread(int(trade_block.get('channel', 0)))
        if channel:
          message = await channel.fetch_message(int(trade_block.get('message', 0)))
          if message:
             await message.delete()
      except (ValueError, TypeError, disnake.NotFound, disnake.HTTPException):
        pass

    try:
      await member.remove_roles(team)
      await remove_roles(inter, 'AfterSignRole', member, inter.guild)  
      await add_roles(inter, 'FreeAgentRole', member, inter.guild)
    except Exception as e:
        await inter.send(e)


  @commands.slash_command()
  async def demand(self, inter: disnake.GuildCommandInteraction, team: disnake.Role = None):
    """
    Demand a release from a team
    Parameters
    ----------
    team: The team to demand from (auto-detected from your team membership)
    """
    await inter.response.defer()
    
    if team is None:
      team_data = await Database.get_data("TeamRole", inter.guild.id)
      if team_data:
        team_ids = team_data if isinstance(team_data, list) else list(team_data.values())
        for team_id in team_ids:
          team_role = inter.guild.get_role(int(team_id))
          if team_role and team_role in inter.author.roles:
            team = team_role
            break
      
      if team is None:
        return await inter.send(embed=error_embed("Not On Team", "You must be on a team to demand a release"), delete_after=10)
    
    tr_checks = await transaction_checks(inter, "Demand", "Demands", team)
    if tr_checks != True:
      return await inter.send(embed=error_embed("Check Failed", tr_checks), delete_after=10)

    if team not in inter.author.roles:
      return await inter.send(embed=error_embed("Not On Team", f"You're not on the `{team.name}`"), delete_after=10)

    coach_role_check = await has_role('FranchiseRole', inter.guild.id, inter.author)
    if coach_role_check:
        return await inter.send(embed=error_embed("Coach", "Coaches can't demand, get demoted first or released"), delete_after=10)

    p_check = await premium_guild_check(inter.guild.id)
    if p_check:  
      p_checks = await premium_checks(inter, team)
      if p_checks != True:
        embed = error_embed('Unable to do this', p_checks)
        embed.set_footer(text="This a Bread Winner Premium only check, thanks for your support")
        return await inter.send(embed=embed, delete_after=10)

      dlc = await demand_limit_check(inter.guild.id, inter.author)
      if not dlc[0]:
        embed = error_embed('At Demand Limit', dlc[1])
        embed.set_footer(text="This a Bread Winner Premium only check, thanks for your support")
        return await inter.send(embed=embed, delete_after=10)
    
      #under_contract_ = await under_contract(inter.guild, inter.author)
      #if under_contract_ != True: do dis

    roster_cap_ = await roster_cap(inter.guild, team)
    embed = Embed(
        title="Demand Complete", 
        description=f'{inter.author.mention} `{inter.author.display_name}` has **demanded** from the {team.name} \n > **Roster Cap:** {roster_cap_[1]} ',
    )
    await embed.league_embed(user=inter.author, guild=inter.guild, role=team)
    await inter.send(embed=embed)

    if p_check:
      demand_amount = await Database.get_data('Users', f"{inter.guild.id}/{inter.author.id}/demands")
      if demand_amount is None:
        await Database.add_data('Users', {inter.guild.id: {inter.author.id: {'demands': 1}}})     
      else:
        try:
          await Database.add_data('Users', {inter.guild.id: {inter.author.id: {'demands': int(demand_amount) + 1}}})
        except (ValueError, TypeError):
          await Database.add_data('Users', {inter.guild.id: {inter.author.id: {'demands': 1}}})    
        
    try:
      await inter.author.remove_roles(team)
      await remove_roles(inter, 'AfterSignRole', inter.author, inter.guild)  
      await add_roles(inter, 'FreeAgentRole', inter.author, inter.guild)
    except Exception as e:
      await inter.send(e)

# send message to notifcaion channel if a coach demands or maybe to the other coahes

  @commands.slash_command()
  async def promote(self, inter: disnake.GuildCommandInteraction, member: disnake.Member, coach_role: disnake.Role):  
    """
    Promote one of your players to a coach position
    Parameters
    ----------
    member: The player to promote
    coach_role: The coach position to promote your player to
    """
    await inter.response.defer()

    coach_role_check = await has_role('FranchiseRole', inter.guild.id, inter.author)
    if not coach_role_check:
        return await inter.send(embed=error_embed("Not a Coach", "You have to be a coach to use this command"), delete_after=10)

    if inter.author.id == member.id:
      return await inter.send(embed=error_embed("Can't Do That", "You can't run commands on yourself"), delete_after=10)
    
    tr_checks = await transaction_checks(inter, "Signing", "Transactions", coach_role)
    if tr_checks != True:
      return await inter.send(embed=error_embed("Check Failed", tr_checks), delete_after=10)

    p_check = await premium_guild_check(inter.guild.id)
    if p_check: 
      same_team = await on_same_team(inter.guild.id, inter.author, member)
      if not same_team:
        return await inter.send(embed=error_embed("Not Same Team", f"You and {member.display_name} are on different teams"), delete_after=10)
      
    promote = await promote_member(inter, member, coach_role.id)
    if promote[0]:
        try:
            await member.add_roles(promote[1])
        except Exception as e:
            await inter.send(e)

        embed = Embed(
            title="Franchise Promotion", 
            description=f'{member.mention} `{member.display_name}` has been **promoted** to {promote[1].mention} \n > **Coach:** {inter.author.mention}',
        )
        await embed.league_embed(user=inter.author, guild=inter.guild, role=promote[1])
        await inter.send(embed=embed)
        await send_to_channel_type(inter.guild, 'Transactions', embed)
    else:
        await inter.send(embed=error_embed("Promote Error", promote[1]), delete_after=10)


  @commands.slash_command()
  async def demote(self, inter: disnake.GuildCommandInteraction, member: disnake.Member):  
    """
    Demote one of your players from a coach position
    Parameters
    ----------
    member: The player to demote
    """
    await inter.response.defer()

    coach_role_check = await has_role('FranchiseRole', inter.guild.id, inter.author)
    if not coach_role_check:
        return await inter.send(embed=error_embed("Not a Coach", "You have to be a coach to use this command"), delete_after=10)

    if inter.author.id == member.id:
      return await inter.send(embed=error_embed("Can't Do That", "You can't run commands on yourself"), delete_after=10)
    check_toggle_ = await check_toggle('Signing', inter.guild.id)
    if not check_toggle_:
      return await inter.send(embed=error_embed("Off", "Transactions are currently off"), delete_after=10)

    demote = await demote_command(inter, member)
    if demote[0]:
      try:
          await member.remove_roles(demote[1])
      except Exception as e:
          await inter.send(e)

      embed = Embed(
            title="Franchise Demotion", 
            description=f'{member.mention} `{member.display_name}` has been **demoted** from {demote[1].mention} \n > **Coach:** {inter.author.mention}',
        )
      await embed.league_embed(user=inter.author, guild=inter.guild, role=demote[1])
      await inter.send(embed=embed)
      await send_to_channel_type(inter.guild, 'Transactions', embed)
    else:
      await inter.send(embed=error_embed("Demotion Error", demote[1]), delete_after=10)

def setup(bot):
  bot.add_cog(SignCommands(bot))