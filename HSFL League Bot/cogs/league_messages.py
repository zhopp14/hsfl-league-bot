import random
from io import BytesIO

import disnake
from disnake.ext import commands

from utils.config import SPORTS_LEAGUES
from utils.embed import Embed
from utils.roles import Roles
from utils.tools import get_user_response, search_role_emoji

# can make quick changes to it - edit button
# a setting that saves the teams you use for quikcer crap
# add an image that shows what the settings do

async def get_custom_teams(self, inter):  
    response = await get_user_response(self, inter)
    if not response:
        return await inter.send(
            "The custom teams response has timed out",
            ephemeral=True,
        )
      
    teams_list = [team.strip() for team in response.split(",") if team.strip()]
    return teams_list

async def message_settings_embed(teams, settings):
  teams = settings.get('league_name', teams)
  if isinstance(teams, list):
    teams = ', '.join(teams)
    
  type = settings['type']
  design = " ".join(
        f"{key}: **{value}**" for key, value in settings.items() if key != "type" and key != 'league_name'
    )
  embed = Embed(
      title = "League Message Maker",
      description = f"**__Settings__**\n`Teams:` {teams}\n`Type:` {type}\n `Design:` {design}"
  )
  return embed

async def make_message(inter, teams, settings):
  try:
    if not teams or len(teams) == 0:
      await inter.send("No teams provided. Please select teams first.", ephemeral=True)
      return
    
    design_teams = await apply_settings(inter, teams, settings)
    
    type = settings.get('type', 'Schedule: Random')
    symbol = settings.get('Symbol') if settings.get('Symbol') else ''
    
    if type == "Schedule: Random":
      if len(design_teams) < 2:
        await inter.send("You need at least 2 teams to create a schedule.", ephemeral=True)
        return
      message = await create_random_schedule(design_teams, symbol)
    elif type == "Schedule: Round-Robin":
      if len(design_teams) < 2:
        await inter.send("You need at least 2 teams to create a schedule.", ephemeral=True)
        return
      message = await create_round_robin(design_teams, symbol)
    elif type == 'Standing: Standings':
      message = await create_standings(design_teams, symbol)
    else:
      await inter.send(f"Unknown message type: {type}", ephemeral=True)
      return

    await send_message(inter, message)
  except Exception as e:
    import traceback
    traceback.print_exc()
    await inter.send(f"Error creating message: {str(e)}", ephemeral=True)

async def apply_settings(inter, teams, settings):
    design_teams = []
    mention_roles = settings['Mention Roles']
    emojis = settings['Emojis']
  
    for team in teams:
        role = team
        emoji = None

        if mention_roles:
            role_mention = disnake.utils.get(inter.guild.roles, name=team)
            role = role_mention.mention if role_mention else team

        if emojis:
            emoji = await search_role_emoji(inter.guild, team)
            emoji = emoji or None

        if emoji:
          design_teams.append(f"{emoji} {role}")
        else:
          design_teams.append(f"{role}")

    return design_teams

async def send_message(inter, message):
    design = f"\n★ ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬ ★\n{message}\n★ ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬ ★"

    try:
        embed = Embed(
          title=f"{inter.guild.name}",
            description=message,
            color=disnake.Color.random()
        )
        if inter.guild.icon:
            embed.set_thumbnail(url=inter.guild.icon)
      
        await inter.send(embed=embed)
    except (disnake.HTTPException, Exception) as e:
        try:
            await inter.send("Please wait... ", ephemeral=True)
            data = BytesIO(design.encode("utf-8"))
            await inter.send(
                file=disnake.File(data, filename=f"{inter.guild.name}_BreadWinnerB.txt")
            )
        except Exception:
            await inter.send(f"Error sending message: {str(e)}", ephemeral=True)


async def create_random_schedule(teams, symbol):
    """
    Generate the first round of a single-elimination knockout tournament schedule.
    
    :param teams: List of team names
    :return: List of match pairs for the first round
    """
    if not teams or len(teams) < 2:
        return "Not enough teams for a schedule"
    
    teams_copy = teams.copy()
    random.shuffle(teams_copy)
    matches = []
    num_matches = len(teams_copy) // 2
    
    for match_num in range(num_matches):
        match = (teams_copy[2 * match_num], teams_copy[2 * match_num + 1])
        formatted_match = f"{match[0]} @ {match[1]}"
        matches.append(formatted_match)

    if matches:
        first_match = f" {symbol} {matches[0]}"
        matches[0] = first_match
        return f"\n {symbol} ".join(matches)
    return "No matches generated"

# https://gist.github.com/ih84ds/be485a92f334c293ce4f1c84bfba54c9,
async def create_round_robin(teams, symbol):
    """Create a schedule for the players in the list and return it"""
    if not teams or len(teams) < 2:
        return "Not enough teams for a schedule"
    
    s = []
    teams_copy = teams.copy()

    if len(teams_copy) % 2 == 1:
        teams_copy = teams_copy + [None]
    # manipulate map (array of indexes for list) instead of list itself
    # this takes advantage of even/odd indexes to determine home vs. away
    n = len(teams_copy)
    map = list(range(n))
    mid = n // 2
    for i in range(n - 1):
        l1 = map[:mid]
        l2 = map[mid:]
        l2.reverse()
        round = []
        for j in range(mid):
            t1 = teams_copy[l1[j]]
            t2 = teams_copy[l2[j]]
            if t1 is None or t2 is None:
                continue
            if j == 0 and i % 2 == 1:
                # flip the first match only, every other round
                # (this is because the first match always involves the last player in the list)
                round.append((t2, t1))
            else:
                round.append((t1, t2))
        if round:
            s.append(round)
        # rotate list by n/2, leaving last element at the end
        map = map[mid:-1] + map[:mid] + map[-1:]

    schedule = s
    if not schedule:
        return "No schedule generated"

    return "\n\n".join([f"Round {round_num + 1}:\n" + "\n".join([f"{symbol}  {match[0]} vs. {match[1]}" for match in round_matches if match[0] and match[1]]) for round_num, round_matches in enumerate(schedule)])

async def create_standings(teams, symbol):
  s = []
  for team in teams:
    s.append(f"{team} **0-0**")
  return f"\n {symbol} ".join(s)

class SelectTeamsView(disnake.ui.View):
    def __init__(self, command_self, inter):
        super().__init__()
        self.inter = inter
        self.command_self = command_self
        self.add_item(SelectTeams(command_self))

    async def on_timeout(self):
        await self.inter.edit_original_message(
            view=None,
            content="Command has expired, run `/league-messages` to use the command again",
        )

    async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
        if inter.author.id != self.inter.author.id:
            await inter.response.send_message("This is not your menu!", ephemeral=True)
            return False
        return True

class SelectTeams(disnake.ui.StringSelect):
    def __init__(self, command_self):
        self.command_self = command_self

        options = [
            disnake.SelectOption(label=league['league'], emoji=league['emoji'])
            for league in SPORTS_LEAGUES
        ]
        
        options.append(disnake.SelectOption(label="Custom Teams", emoji="✨"))
        super().__init__(
              placeholder="Pick the teams you want", options=options
        )

    async def callback(self, inter: disnake.MessageInteraction):
        await inter.response.defer()

        league = self.values[0]
        if league == "Custom Teams":
          await inter.send("Send the teams you want to use with a comma between each team. Like this: \n\n Dallas Cowboys,New York Knicks,Atlanta United FC,Baltimore Royals", ephemeral=True)
          teams = await get_custom_teams(self.command_self, inter)
          embed = Embed(title="League Messages Maker", description=f"**__Settings__**\n`Teams:` {', '.join(teams)}\n`Type:` Schedule: Random\n`Design:` Default")  
          await inter.edit_original_message(embed=embed, view=LeagueMessagesMenu(inter, teams, self.command_self))
        else:
          embed = Embed(title="League Messages Maker", description=f"**__Settings__**\n`Teams:` {league}\n`Type:` Schedule: Random\n`Design:` Default")      
          league_ = league.lower().replace(" ", "_")
          teams = getattr(Roles, league_)
          await inter.edit_original_message(embed=embed, view=LeagueMessagesMenu(inter, teams, self.command_self, {'league_name': league}))


      
class LeagueMessagesMenu(disnake.ui.View):
    def __init__(self, inter, teams: list, command_self, settings: dict = None):
      super().__init__()
      self.inter = inter
      self.teams = teams
      self.command_self = command_self
      self.settings = {
        'type': 'Random',
        'Mention Roles': False,
        'Emojis': False,
        'Symbol': None
      }
      if settings:
        self.settings.update(settings)

      #self.add_item(SelectTeams(command_self))

    async def on_timeout(self):
        await self.inter.edit_original_message(
          view=None,
          content="Command has expired, run `/league-messages` to use the command again",
        )
  
    async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
        if inter.author.id != self.inter.author.id:
            await inter.response.send_message("This is not your menu!", ephemeral=True)
            return False
        return True

    @disnake.ui.button(label="Create Message", style=disnake.ButtonStyle.green)
    async def create_message_button(self, button, inter):
      await inter.response.defer()
      try:
        await make_message(inter, self.teams, self.settings)
      except Exception as e:
        await inter.send(f"Error creating message: {str(e)}", ephemeral=True)
      
    @disnake.ui.button(label="Type")
    async def message_type_button(self, button, inter):
      await inter.response.edit_message(view = MessageType(inter, self.teams, self.command_self, self.settings))

    @disnake.ui.button(label="Design")
    async def message_design_button(self, button, inter):
      await inter.response.edit_message(view = MessageDesign(inter, self.teams, self.command_self, self.settings))


class MessageType(disnake.ui.View):
    def __init__(self, inter, teams, command_self, settings):
      super().__init__()
      self.inter = inter
      self.teams = teams
      self.command_self = command_self
      self.settings = settings

    async def on_timeout(self):
        await self.inter.edit_original_message(
          view=None,
          content="Command has expired, run `/league-message` to use the command again",
        )
  
    async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
        if inter.author.id != self.inter.author.id:
            await inter.response.send_message("This is not your menu!", ephemeral=True)
            return False
        return True

    @disnake.ui.button(label="Schedules:", disabled=True, row=0)
    async def schedule_types(self, button, inter):
      return
  
    @disnake.ui.button(label="Random", row=0)
    async def random_schedule_button(self, button, inter):
      self.settings['type'] = "Schedule: Random"
      embed = await message_settings_embed(self.teams, self.settings)
      await inter.response.edit_message(embed=embed, view=LeagueMessagesMenu(inter, self.teams, self.command_self, self.settings))

    @disnake.ui.button(label="Round Robin", row=0)
    async def round_robin_schedule_button(self, button, inter):
      self.settings['type'] = 'Schedule: Round-Robin'
      embed = await message_settings_embed(self.teams, self.settings)
      await inter.response.edit_message(embed=embed, view=LeagueMessagesMenu(inter, self.teams, self.command_self, self.settings))

    @disnake.ui.button(label="Standings:", disabled=True, row=1)
    async def standings_types(self, button, inter):
      return

    @disnake.ui.button(label="Standings", row=1)
    async def standings_standing(self, button, inter):
      self.settings['type'] = 'Standing: Standings'
      embed = await message_settings_embed(self.teams, self.settings)
      await inter.response.edit_message(embed=embed, view=LeagueMessagesMenu(inter, self.teams, self.command_self, self.settings))

class MessageDesign(disnake.ui.View):
    def __init__(self, inter, teams, command_self, settings):
      super().__init__()
      self.inter = inter
      self.teams = teams
      self.command_self = command_self
      self.settings = settings

    async def on_timeout(self):
        await self.inter.edit_original_message(
          view=None,
          content="Command has expired, run `/league-messages` to use the command again",
        )
  
    async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
        if inter.author.id != self.inter.author.id:
            await inter.response.send_message("This is not your menu!", ephemeral=True)
            return False
        return True

    @disnake.ui.button(label="Mention Roles")
    async def mention_roles_button(self, button, inter):
      self.settings['Mention Roles'] = True
      embed = await message_settings_embed(self.teams, self.settings)
      await inter.response.edit_message(embed=embed, view=LeagueMessagesMenu(inter, self.teams, self.command_self, self.settings))
      await inter.send("This uses the roles you have in your server, if you don't have a role for a team. It won't get pinged", ephemeral=True)

    @disnake.ui.button(label="Emojis")
    async def emojis_button(self, button, inter):
      self.settings['Emojis'] = True
      embed = await message_settings_embed(self.teams, self.settings)
      await inter.response.edit_message(embed=embed, view=LeagueMessagesMenu(inter, self.teams, self.command_self, self.settings))
      await inter.send("This uses the emojis you have in your server, if you don't have a emoji for a team. An emoji won't get used", ephemeral=True)

    @disnake.ui.button(label="Symbol")
    async def symbol_button(self, button, inter):
      await inter.response.send_message("Send your symbol", ephemeral=True)
      response = await get_user_response(self.command_self, inter)
      if not response:
        return await inter.send("The custom symbol response has timed out", ephemeral=True)
          
      self.settings['Symbol'] = response
      embed = await message_settings_embed(self.teams, self.settings)
      try:
        await inter.message.edit(embed=embed, view=LeagueMessagesMenu(inter, self.teams, self.command_self, self.settings))
      except Exception:
        # If we can't edit the original message, send a new one
        await inter.send(embed=embed, view=LeagueMessagesMenu(inter, self.teams, self.command_self, self.settings), ephemeral=True)


class LeagueMessagesCommands(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  @commands.slash_command(name="league-messages")
  @commands.cooldown(1, 20, commands.BucketType.user)
  async def league_messages(self, inter):
    """Make a league message for things like schedules, standings, etc"""
    embed = Embed(title="League Message Maker", description="Pick the teams you want to use for your message, scroll to the bottom to use custom teams")
    await inter.response.send_message(embed=embed, view=SelectTeamsView(self, inter))




  @commands.slash_command()
  @commands.cooldown(1, 20, commands.BucketType.user)
  async def schedule(self, inter):
    """Use /league-messages"""
    await inter.response.send_message("You `/league_messages`, you can also edit and make the schedule look better with `/embed`")

  @commands.slash_command()
  @commands.cooldown(1, 20, commands.BucketType.user)
  async def standings(self, inter):
    """Use /league-messages"""
    await inter.response.send_message("You `/league_messages`, you can also edit and make the standings look better with `/embed`")

  @commands.slash_command()
  @commands.cooldown(1, 20, commands.BucketType.user)
  async def leaderboard(self, inter):
    """Use /league-messages"""
    await inter.response.send_message("You `/league_messages`, you can also edit and make the leaderboard look better with `/embed`")


def setup(bot):
  bot.add_cog(LeagueMessagesCommands(bot))