import re
from datetime import datetime

import disnake
from disnake.ext import commands

from utils.database import Database
from utils.embed import Embed
from utils.tools import has_role, premium_user_check, guild_members, search_embed_ids
from utils.signing_tools import team_check, send_notfication_channel, get_team_owner, roster_cap, auto_detect_team, check_channel_config
from utils.config import SETTINGS, Links, BotEmojis

async def get_trade_channel(inter):
  """Looks for TradingChannel then SigningChannel then current channel"""
  trade_channel_id = await Database.get_data('TradingChannel', inter.guild.id)
  if trade_channel_id:
    # Handle both list and dict formats
    if isinstance(trade_channel_id, list) and trade_channel_id:
      channel_id = trade_channel_id[0]
    elif isinstance(trade_channel_id, dict) and trade_channel_id:
      channel_id = list(trade_channel_id.values())[0]
    else:
      channel_id = None
    
    if channel_id:
      try:
        trade_channel = inter.guild.get_channel_or_thread(int(channel_id))
        if trade_channel:
          return trade_channel
      except (ValueError, TypeError):
        pass

  sign_channel_id = await Database.get_data('SigningChannel', inter.guild.id)
  if sign_channel_id:
    # Handle both list and dict formats
    if isinstance(sign_channel_id, list) and sign_channel_id:
      channel_id = sign_channel_id[0]
    elif isinstance(sign_channel_id, dict) and sign_channel_id:
      channel_id = list(sign_channel_id.values())[0]
    else:
      channel_id = None
    
    if channel_id:
      try:
        sign_channel = inter.guild.get_channel_or_thread(int(channel_id))
        if sign_channel:
          return sign_channel
      except (ValueError, TypeError):
        pass

  return inter.channel


class BaseView(disnake.ui.View):
    def __init__(self, inter, team, team_members, author_team, author_members):
        super().__init__()
        self.inter = inter
        # Roles
        self.team = team
        self.author_team = author_team
        # Players on the roles
        self.team_members = team_members
        self.author_members = author_members

        # Players that are going to be used in the trade
        self.team_members_trade = []
        self.author_members_trade = []
        self.add_item(SubmitTrade(self))

        self.team_members_options = [          disnake.SelectOption(label=member.name, value=member.id)
           for member in team_members
        ]
        
        
        self.author_members_options = [
            disnake.SelectOption(label=member.name, value=str(member.id))
            for member in self.author_members
        ]
        
        
        # Thanks chatgpt :!)
        # Check if there are more than 25 options
        if len(self.author_members_options) > 25:
            # Split options into chunks of 25
            option_chunks = [self.author_members_options[i:i + 25] for i in range(0, len(self.author_members_options), 25)]

            # Create and add AuthorTeamUserSelect components for each chunk
            for chunk in option_chunks:
                self.add_item(AuthorTeamUserSelect(self, chunk))
        else:
            self.add_item(AuthorTeamUserSelect(self, self.author_members_options))


        if len(self.team_members_options) > 25:
            # Split options into chunks of 25
            option_chunks = [self.team_members_options[i:i + 25] for i in range(0, len(self.team_members_options), 25)]

            # Create and add TeamUserSelect components for each chunk
            for chunk in option_chunks:
                self.add_item(TeamUserSelect(self, chunk))
        else:
            self.add_item(TeamUserSelect(self, self.team_members_options))



class AuthorTeamUserSelect(disnake.ui.StringSelect):
    def __init__(self, base_view, options):
        self.base_view = base_view
        self.inter = base_view.inter
        super().__init__(options=options, placeholder=f"{base_view.author_team.name} players")


    async def callback(self, inter: disnake.MessageInteraction):
        await inter.response.defer(ephemeral=True)

        member = await self.inter.guild.get_or_fetch_member(self.values[0])
        if member.bot:
           return await inter.send("Bots can't be used in trades", ephemeral=True)
        
        coach = await has_role('FranchiseRole', inter.guild.id, member)
        if coach:
           return await inter.send("You are not able to trade coaches", ephemeral=True)
        
        trade_list = self.base_view.author_members_trade

        if member in trade_list:
           return await inter.send(f"{member.mention} is already being used as a trade piece", ephemeral=True)

        trade_list.append(member)
        message = [member.mention for member in trade_list]
        message = ' '.join(message)

        embed = inter.message.embeds[0]
        embed.set_field_at(index = 0, name = embed.fields[0].name, value=message)
        await inter.message.edit(embed=embed)


class TeamUserSelect(disnake.ui.StringSelect):
    def __init__(self, base_view, options):
        self.base_view = base_view
        self.inter = base_view.inter
        super().__init__(options=options, placeholder=f"{base_view.team.name} players")


    async def callback(self, inter: disnake.MessageInteraction):
        await inter.response.defer(ephemeral=True)
        member = await self.inter.guild.get_or_fetch_member(self.values[0])
        if member.bot:
           return await inter.send("Bots can't be used in trades", ephemeral=True)
        
        coach = await has_role('FranchiseRole', inter.guild.id, member)
        if coach:
           return await inter.send("You are not able to trade coaches", ephemeral=True)

        trade_list = self.base_view.team_members_trade

        if member in trade_list:
           return await inter.send(f"You are already trading for {member.mention}", ephemeral=True)

        trade_list.append(member)
        message = [member.mention for member in trade_list]
        message = ' '.join(message)

        embed = inter.message.embeds[0]
        embed.set_field_at(index = 1, name = embed.fields[1].name, value=message)
        await inter.message.edit(embed=embed)
        

class SubmitTrade(disnake.ui.Button):
  def __init__(self, base_view):  
    self.base_view = base_view
    super().__init__(label="Submit Trade", style=disnake.ButtonStyle.green)

  async def callback(self, inter):
    await inter.response.defer(ephemeral=True)

    # checking if each team list is not empty
    if not any([self.base_view.author_members_trade, self.base_view.team_members_trade]): 
      return await inter.send("Put players for both teams", ephemeral=True)


    author_team = self.base_view.author_team
    team = self.base_view.team

    author_team_cap_check = await roster_cap(inter.guild, author_team, len(self.base_view.author_members_trade) - 1)
    if not author_team_cap_check[0]:
       return await inter.send(f"This trade would put the {author_team.mention} over the cap space", ephemeral=True)

    team_cap_check = await roster_cap(inter.guild, team, len(self.base_view.team_members_trade) - 1)
    if not team_cap_check[0]:
       return await inter.send(f"This trade would put the {team.mention} over the cap space", ephemeral=True)


    trade_embed = Embed(
      title = f'Trade Offer',
      description = f"The {author_team.mention} have sent a trade offer to the {team.mention}",
    )
    fields = inter.message.embeds[0].fields
    trade_embed.add_field(name = f"{author_team.name} Gets", value = fields[1].value)
    trade_embed.add_field(name = f"{team.name} Gets", value = fields[0].value)
 
    channel = await get_trade_channel(self.base_view.inter)
    team_owner = await get_team_owner(inter.guild, team)

    await channel.send(embed=trade_embed, view=AcceptDeclineTrade(self.base_view.inter), content=team_owner.mention if team_owner else None, allowed_mentions=disnake.AllowedMentions(users=True))
    await inter.send(f"The trade has been sent to {channel.mention}. Now waiting for the {team} to responded", ephemeral=True)
    await inter.message.edit(view=None)


class AcceptDeclineTrade(disnake.ui.View):
  def __init__(self, inter):
    super().__init__()
    self.add_item(disnake.ui.Button(
       label = "Accept Trade",
       emoji = BotEmojis.check_mark,
       style = disnake.ButtonStyle.green,
       custom_id = f"accept_trade-{inter.guild.id}"
       )
    )

    self.add_item(disnake.ui.Button(
       label = "Decline Trade",
       emoji = BotEmojis.x_mark,
       style = disnake.ButtonStyle.red,
       custom_id = f"decline_trade-{inter.guild.id}"
       )
    )


class TradeBlockRemovePlayer(disnake.ui.View):
  def __init__(self, guild):
    super().__init__()
    self.add_item(disnake.ui.Button(label='Remove', style=disnake.ButtonStyle.red, custom_id=f'trade_block_remove-{guild.id}'))


class TradeCommands(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  @commands.Cog.listener()
  async def on_button_click(self, inter):
      custom_id = inter.component.custom_id
      if custom_id == f"accept_trade-{inter.guild.id}":    
          guild = inter.guild
          await inter.response.defer(ephemeral=True)

          # Getting teams again
          teams = await search_embed_ids(inter.message.embeds[0].description, 'role', guild)
          author_team = teams[0] # author_team
          team = teams[1] # team

          team_members = await guild_members(inter.guild, team)
          owner = await get_team_owner(inter.guild, team)
          if not inter.author in team_members and not owner:
             return await inter.send(f"You are not the owner of the {team.mention}", ephemeral=True)

          # Getting users
          author_trade_users = await search_embed_ids(inter.message.embeds[0].fields[1].value, 'user', guild)
          team_trade_users = await search_embed_ids(inter.message.embeds[0].fields[0].value, 'user', guild)

          # Adding and remove roles
          # team1 role go to users2, etc
          for user in author_trade_users:
             await user.add_roles(team)
             await user.remove_roles(author_team)
             await Database.delete_data('TradeBlock', f'{guild.id}/{user.id}')
          for user in team_trade_users:
             await user.add_roles(author_team)
             await user.remove_roles(team)
             await Database.delete_data('TradeBlock', f'{guild.id}/{user.id}')

          # Sending messages
          # trade channel
          trade_embed = Embed(
            title = f'Trade Accepted',
            description = f"The {team.mention} have **accepted** the {author_team.mention} trade offer",
          )
          await trade_embed.league_embed(inter.guild, inter.author, team)
          fields = inter.message.embeds[0].fields
          trade_embed.add_field(name = f"{team} Receives", value = fields[0].value)
          trade_embed.add_field(name = f"{author_team} Receives", value = fields[1].value)

          author_team_owner = await get_team_owner(inter.guild, author_team)

          channel = await get_trade_channel(inter)
          await channel.send(embed=trade_embed, content=author_team_owner.mention if author_team_owner else None, allowed_mentions=disnake.AllowedMentions(users=True))


          # coach who clicked button
          await inter.send("Trade Accepted", ephemeral=True)

          # notfi owner
          await send_notfication_channel(inter.guild, trade_embed, inter.guild.owner.mention) 

          # get rid of buttons
          await inter.message.edit(content=f"This trade has been accepted", view=None)


      if custom_id == f"decline_trade-{inter.guild.id}":    
          guild = inter.guild
          await inter.response.defer(ephemeral=True)
          # check who is clicking, on team1, is coach

          # Getting teams again
          teams = await search_embed_ids(inter.message.embeds[0].description, 'role', guild)
          author_team = teams[0] # author_team
          team = teams[1] # team

          team_members = await guild_members(inter.guild, team)
          owner = await get_team_owner(inter.guild, team)
          if not inter.author in team_members and not owner:
             return await inter.send(f"You are not the owner of the {team.mention}", ephemeral=True)


          # Sending messages
          # trade channel
          trade_embed = Embed(
            title = f'Trade Declined',
            description = f"The {team.mention} have **declined** the {author_team.mention} trade offer, below was what was offered",
          )
          await trade_embed.league_embed(inter.guild, inter.author, team)
          fields = inter.message.embeds[0].fields
          trade_embed.add_field(name = f"{team} Receives", value = fields[0].value)
          trade_embed.add_field(name = f"{author_team} Receives", value = fields[1].value)

          author_team_owner = await get_team_owner(inter.guild, author_team)

          channel = await get_trade_channel(inter)
          await channel.send(embed=trade_embed, content=author_team_owner.mention if author_team_owner else None, allowed_mentions=disnake.AllowedMentions(users=True))



          # coach who clicked button
          await inter.send("Trade Declined", ephemeral=True)

          # get rid of buttons
          await inter.message.edit(content=f"This trade has been declined", view=None)

      if custom_id == f'trade_block_remove-{inter.guild.id}':
         guild = inter.guild
         await inter.response.defer(ephemeral=True)

         # Getting teams again
         teams = await search_embed_ids(inter.message.embeds[0].description, 'role', guild)
         team = teams[0] # team

         team_members = await guild_members(guild, team)
         owner = await get_team_owner(guild, team)
         if not inter.author in team_members and not owner:
            return await inter.send(f"You are not the owner of the {team.mention}", ephemeral=True)

         player = await search_embed_ids(inter.message.embeds[0].description, 'user', guild)
         await Database.delete_data('TradeBlock', f'{guild.id}/{player[0].id}')
         await inter.delete_original_message()

 
  @commands.slash_command(name='trade-block')
  async def trade_block(self, inter, player: disnake.Member, team: disnake.Role = None):
    """
    Add a player to the trade block
    Parameters
    ----------
    player: The player to add to the trade block
    team: The team adding the player to the trade block
    """
    guild = inter.guild
    author = inter.author
    await inter.response.defer(ephemeral=True)

    coach = await has_role('FranchiseRole', guild.id, author)
    if not coach:
      return await inter.send('You have to be a coach to use this command', ephemeral=True)

    check_channel_, channel_error = await check_channel_config(inter, 'Trades')
    if not check_channel_:
      return await inter.send(channel_error if channel_error else "You can't use that command in this channel", ephemeral=True)

    if team is None:
      team = await auto_detect_team(guild.id, author)

    db_team_role = await has_role('TeamRole', guild.id, author, 'id')
    if db_team_role:
      team_role = guild.get_role(int(db_team_role))
    else:
      team_role = team

    if not team_role:
      return await inter.send(f"You are not assigned to a team. Please use the `team` parameter", ephemeral=True)

    if team_role not in author.roles:
      return await inter.send(f"You are not on the {team_role}", ephemeral=True)

    if team_role not in player.roles:
      return await inter.send(f'{player.mention} is not on that team', ephemeral=True)

    trade_block = await Database.get_data('TradeBlock', f'{guild.id}/{player.id}')
    if trade_block:
       return await inter.send(f"{player.mention} is already on the trade block", ephemeral=True)

    channel = await get_trade_channel(inter)
    embed = Embed(
      title = "Trade Block",
      description = f'The {team_role.mention} have added {player.mention} `{player.display_name}` to the trade block'
    )  
    await embed.league_embed(guild=guild, user=author, role=team_role)
    message = await channel.send(embed=embed, view=TradeBlockRemovePlayer(guild))
    await inter.send(f"Message has been sent to {channel.mention}", ephemeral=True)
    await Database.add_data('TradeBlock', {guild.id: {player.id: {'channel': channel.id, 'message': message.id}}})

  @commands.slash_command()
  async def trade(self, inter, team: disnake.Role, your_team: disnake.Role = None):
    """
    Trade with another team
    Parameters
    ----------
    team: The team you want to trade with
    your_team: If you don't have teams saved, manually put your team
    """
    guild = inter.guild
    author = inter.author
    await inter.response.defer()

    coach_role_check = await has_role('FranchiseRole', inter.guild.id, inter.author)
    if not coach_role_check:
        return await inter.send("You have to be a coach to use this command")

    check_channel_, channel_error = await check_channel_config(inter, 'Trades')
    if not check_channel_:
      return await inter.send(channel_error if channel_error else "You can't use that command in this channel")

    if your_team is None:
      your_team = await auto_detect_team(guild.id, author)

    db_author_role = await has_role('TeamRole', guild.id, author, 'id')
    if db_author_role:
      author_team_role = guild.get_role(int(db_author_role))
    else:
      author_team_role = your_team

    if not author_team_role:
      return await inter.send(f"You are not assigned to a team. Please use the `your_team` parameter")

    if team == author_team_role:
       return await inter.send("You can't trade with yourself")

    
    if author_team_role not in author.roles:
      return await inter.send(f"You are not on the {author_team_role}")


    # Checks for team trading with
    db_team_role = await team_check(guild.id, team)
    if not db_team_role:
       return await inter.send(f"{team.mention} is not in the teams database")

    # Doing this here bc we can't use await in the __init__ for the options and we aren't able to easiy edit the options
    team_members = await guild_members(guild, team)
    if len(team_members) == 0:
       return await inter.send(f"{team.mention} has no players")
    author_team_members = await guild_members(guild, author_team_role)
    if len(author_team_members) == 0:
       return await inter.send(f"{author_team_role.mention} has no players")
    

    embed = Embed(title="Propose Trade")
    embed.add_field(name = f"{author_team_role.name} (Trading away)", value=' ')
    embed.add_field(name = f"{team.name} (Trading for)", value=' ')

    await inter.send(embed=embed, view=BaseView(inter, team, team_members, author_team_role, author_team_members))
  
def setup(bot):
  bot.add_cog(TradeCommands(bot))