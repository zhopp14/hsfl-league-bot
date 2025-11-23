import random
import re
from io import BytesIO

import disnake
import unidecode
from disnake.ext import commands

from utils.config import SPORTS_LEAGUES, Links, not_premium_message
from utils.database import Database
from utils.embed import Embed
from utils.roles import Roles
from utils.tools import (get_user_response, guild_members, has_role,
                         parse_duration, premium_guild_check, add_roles, remove_roles)

# - Draft Picks - random, manually send a thingy with picks, snake draft

async def get_custom_teams(self, inter):  
    response = await get_user_response(self, inter)
    if not response:
        return await inter.send(
            "The custom teams response has timed out",
            ephemeral=True,
        )
      
    find_teams  = re.findall(r'<@&(\d+)>', response)
    if not find_teams:
        return await inter.send("Invaild roles")

    teams = []
    for role_id in find_teams:
       role = inter.guild.get_role(int(role_id))
       if role:
          teams.append(role)

    return teams


async def get_team_roles(inter, teams: list):
    """
    If people use the preset teams, like NFL or MLB, 
    we don't need the team names we need the actaully role. 
    So this is searching for a role with the team name or id
    """
    role_objects = []
    for team in teams:
        try:
           team = int(team)
           role = inter.guild.get_role(int(team))
        except ValueError:
            role = disnake.utils.get(inter.guild.roles, name=unidecode.unidecode(team))
        if role:
          mems = await guild_members(inter.guild, role)
          if len(mems) >= 1:
            role_objects.append(role)
    return role_objects


async def settings_embed(teams, settings):
    items = [object.mention for object in teams]
    teams = ', '.join(items)

    draft_picks = settings['Draft Picks']
    if isinstance(draft_picks, list): # custom
        draft_picks = 'Custom Draft Order'

    time_per_pick = f"`Time Per Pick`: {settings['Time Per Pick'] // 60}"

    settings = " ".join(
            f"`{key}:` {value}\n" for key, value in settings.items() if key != 'Draft Picks' or key != 'Time Per Pick'
        )
    embed = Embed(
        title = "League Message Maker",
        description = f"**__Settings__**\n`Teams:` {teams}\n`Draft Picks:` {draft_picks}\n{time_per_pick}\n{settings}"
    )
    return embed


async def team_threads(inter, settings, teams):
    channel = settings['Draft Channel']
    team_threads = {} # to send messages later
    for team in teams: # team = role
        try:
           thread = await channel.create_thread(name=f"{team.name} draft room", type=disnake.ChannelType.private_thread, invitable=False)
           embed = Embed(title="Draft Room", description="This is your draft room. When it is your turn to draft a message will be sent asking you to pick a player. Updates on rounds and draft will be sent here as well \n **Drafted Players:**")
           await thread.send(embed=embed)
           team_threads[team] = thread
        except Exception as e:
          return await inter.response.send_message(e, ephemeral=True)

        team_members = await guild_members(inter.guild, team)
        for member in team_members:
            coach = await has_role('FranchiseRole', inter.guild.id, member)
            if coach:
                await thread.add_user(member)

    await inter.send('Team draft rooms made. Note that only coaches can see the threads', ephemeral=True)   
    return team_threads       


async def make_draft_order(inter, teams, settings):
    draft_type = settings['Draft Picks']
    if draft_type == 'Random':
       draft_order = await random_draft_picks(teams, settings)
    elif draft_type == 'Snake':
       draft_order = await snake_draft_picks(teams, settings)
    else:
        # custom order
        draft_order = draft_type 

    return draft_order

    #draft_order = [
    #    {"Round": 1, "Teams": ['Team A', 'Team B', 'Team C']},
    #    {"Round": 2, "Teams": ['Team C', 'Team B', 'Team A']},
    #]


async def random_draft_picks(teams, settings):
    rounds = settings['Rounds']
    draft_order = []
    random.shuffle(teams)
  
    for round_number in range(1, rounds + 1):
        draft_order.append({"Round": round_number, "Teams": teams})
    
    return draft_order

async def snake_draft_picks(teams, settings):
    rounds = settings['Rounds']
    draft_order = []
    random.shuffle(teams)
  
    for round_number in range(1, rounds + 1):
        if round_number % 2 == 1:
            # Odd round: Keep the original order
            draft_order.append({"Round": round_number, "Teams": teams})
        else:
            # Even round: Reverse the order
            draft_order.append({"Round": round_number, "Teams": list(reversed(teams))})
    
    return draft_order



class SelectTeamsView(disnake.ui.View):
    def __init__(self, command_self, inter):
        super().__init__()
        self.inter = inter
        self.command_self = command_self
        self.add_item(SelectTeams(command_self))

    async def on_timeout(self):
        await self.inter.edit_original_message(
            view=None,
            content="Command has expired, run `/draft` to use the command again",
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
        options.append(disnake.SelectOption(label="TeamRole", emoji="⏰", description="Uses the roles you have in the TeamRole database"))
        super().__init__(
              placeholder="Pick the teams you want", options=options
        )

    async def callback(self, inter: disnake.MessageInteraction):
        await inter.response.defer()
        default_settings = f"`Draft Picks:` Random \n `Time Per Pick`: 3 minutes \n `Rounds`: 7 \n `Draft Channel`: {inter.channel} \n`Eligibility Role:` None"
        note = "**Note: Only teams with atleast one member are used in the draft**"

        league = self.values[0]
        if league == "Custom Teams":
          await inter.send("Ping all the teams you want to use. Like this: \n\n <@&861760674216673300> <@&868731458821423104> <@875552366357786674> @Baltimore Royals", ephemeral=True)
          teams = await get_custom_teams(self.command_self, inter)
          teams_ = [team.mention for team in teams]
          embed = Embed(title="Draft System", description=f"**__Settings__**\n`Teams:` {', '.join(teams_)}\n {default_settings}")  
          await inter.edit_original_message(embed=embed, view=DraftSettingsMenu(inter, teams, self.command_self))

        elif league == "TeamRole":
            pc = await premium_guild_check(inter.guild.id)
            if not pc:
              return await inter.send(not_premium_message, ephemeral=True)
        
            team_roles = await Database.get_data('TeamRole', inter.guild.id)
            if team_roles is None:
               return await inter.send("You have no teams in the database, set some with `/setup roles team roles`", ephemeral=True)
            
            # Handle both list and dict formats
            if isinstance(team_roles, list):
                role_ids = team_roles
            elif isinstance(team_roles, dict):
                role_ids = team_roles.values()
            else:
                return await inter.send("Invalid team role data", ephemeral=True)
            
            if not role_ids:
                return await inter.send("You have no teams in the database, set some with `/setup roles team roles`", ephemeral=True)

            # Convert to list format for get_team_roles
            team_roles_list = list(role_ids) if isinstance(role_ids, (list, dict)) else []
            teams = await get_team_roles(inter, team_roles_list)
            if not teams:
               return await inter.send(f"No roles found", ephemeral=True)
            teams_ = [team.mention for team in teams]

            embed = Embed(title="Draft System", description=f"**__Settings__**\n`Teams:` {', '.join(teams_)}\n {default_settings}\n\n{note}")  
            await inter.edit_original_message(embed=embed, view=DraftSettingsMenu(inter, teams, self.command_self))

        else:
            league_ = league.lower().replace(" ", "_")
            teams = getattr(Roles, league_)
            team_roles = await get_team_roles(inter, teams)
            if not team_roles:
                return await inter.send(f"No {league} roles found", ephemeral=True)
            
            teams_ = [team.mention for team in team_roles]
            embed = Embed(title="Draft System", description=f"**__Settings__**\n`Teams:` {', '.join(teams_)}\n {default_settings}\n\n{note}")  
            embed.set_footer(text=f"This searches your role for {league} teams, if you don't have a role for a team it won't show up")

            await inter.edit_original_message(embed=embed, view=DraftSettingsMenu(inter, team_roles, self.command_self))




class DraftSettingsMenu(disnake.ui.View):
    def __init__(self, inter, teams: list, command_self, settings: dict = None):
      super().__init__()
      self.inter = inter
      self.teams = teams
      self.command_self = command_self
      self.settings = {
        'Draft Picks': 'Random', # random, manually, snake?, lottery in the future
        'Rounds': 3,
        'Time Per Pick': 180, # in seconds 180 = 3 mins
        'Draft Channel': inter.channel,
        'Eligibility Role': None,
      }
      if settings:
        self.settings.update(settings)

    async def on_timeout(self):
        await self.inter.edit_original_message(
          view=None,
          content="Command has expired, run `/draft` to use the command again",
        )
  
    async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
        if inter.author.id != self.inter.author.id:
          await inter.response.send_message("This is not your menu!", ephemeral=True)
          return False
        return True


    async def do_draft(self, team_threads, draft_order, settings):

        async def notify_all_threads(embed):
            for thread in team_threads.values():
                try:
                    await thread.send(embed=embed)
                except disnake.Forbidden:
                    await self.inter.send(f"I do not have the right permissions to send a message to {thread.name}")
                except disnake.HTTPException:
                    continue
                except disnake.NotFound:
                    continue

        draft_channel = settings['Draft Channel']
        time_limit = settings['Time Per Pick']
        rounds = settings['Rounds']

        pc = await premium_guild_check(self.inter.guild.id)

        annouce_draft = Embed(title="The Draft has Started", description=f"**Amount of Rounds:** {rounds}\n**Started by:** {self.inter.author.mention} `{self.inter.author.display_name}`").set_thumbnail(url=self.inter.guild.icon or None)
        await draft_channel.send(embed=annouce_draft)

        for round_number, draft_pick in enumerate(draft_order, 1):
            # Notify all threads at the start of each round
            round_embed = Embed(title="New Round", description=f"Round **{round_number}** has started").set_thumbnail(url=self.inter.guild.icon or None)
            await notify_all_threads(round_embed)
            await draft_channel.send(embed=round_embed)

            # Notify each team in order
            for pick_number, team in enumerate(draft_pick['Teams']):
                    view = DraftPlayerView(self.inter, team_threads, team, draft_order, settings)

                    # How to draft message, we will update it with players you drafted
                    first_message = await team_threads[team].history(limit=1, oldest_first=True).flatten()

                    your_turn_embed = Embed(title="Your Turn in the Draft", description=f"{team.mention} It's your turn in round {round_number}. You have {time_limit // 60} minutes")
                    try:
                        your_turn_message = await team_threads[team].send(f"{team.mention}", embed=your_turn_embed, view=view, allowed_mentions=disnake.AllowedMentions(roles=True))
                    except Exception:
                        your_turn_message = await draft_channel.send(f"{team.mention}", embed=your_turn_embed, view=view, allowed_mentions=disnake.AllowedMentions(roles=True))

                    draft_turn = Embed(title=f"The {team.name} are now on the clock", description=f"The {team.mention} have {time_limit // 60} minutes to submit a pick")
                    await draft_turn.league_embed(user=self.inter.author, guild=self.inter.guild, role=team)
                    await draft_channel.send(embed=draft_turn)

                    await view.wait()
                    if view.player:
                            player = view.player
                            player_string = f"{player.mention} `{player.display_name}`"
                            coach = view.coach

                            await player.add_roles(team)
                            await add_roles(self.inter, 'AfterSignRole', player, self.inter.guild)  
                            await remove_roles(self.inter, 'FreeAgentRole', player, self.inter.guild)
                            await your_turn_message.edit(f"{coach.mention} has drafted {player_string}", view=None, embed=None)


                            first_message_embed = first_message[0].embeds[0]
                            new_desc = first_message_embed.description + f"\n {player_string} - `{coach.name}`"
                            setattr(first_message_embed, 'description', new_desc) # embed.description = ...
                            await first_message[0].edit(embed=first_message_embed)

                            picked_player = Embed(
                               title=f"Player Selected: Round {round_number}", 
                               description = f"The {team.mention} have selected {player_string} **with pick number {pick_number + 1}**"
                            )
                            await picked_player.league_embed(user=self.inter.author, guild=self.inter.guild, role=team)
                            await draft_channel.send(embed=picked_player)

                            if pc: # Save drafted data, if premium
                                await Database.add_data('Users', {self.inter.guild.id: {player.id: {'drafted': f"{round_number}, {pick_number + 1} ({team.name})"}}})
                                #await Database.add_data('Teams', {self.inter.guild.id: {team.id: {'Draft': f"{round_number}, {pick_number + 1} ({team.name})"}}}) 


        end_draft = Embed(title="Draft Ended", description=f"The draft has finished! \n **Rounds:** {round_number}").set_thumbnail(url=self.inter.guild.icon or None)
        await draft_channel.send(embed=end_draft)
        await notify_all_threads(end_draft)
        return


    @disnake.ui.button(label="Start Draft", style=disnake.ButtonStyle.green)
    async def start_draft_button(self, button, inter):
        await inter.response.defer()
        await inter.send("Making a thread for each team, this may take a while if you have a lot of teams", ephemeral=True)
        # Make a private thread for each team, sends a message saying how the draft works
        threads = await team_threads(inter, self.settings, self.teams)

        # Gets the order of how each team will pick
        draft_order = await make_draft_order(inter, self.teams, self.settings)

        await self.do_draft(threads, draft_order, self.settings)

    @disnake.ui.button(label="Draft Picks")
    async def draft_type_button(self, button, inter):
      await inter.response.edit_message(view = DraftPicksType(inter, self.teams, self.command_self, self.settings))

    @disnake.ui.button(label="Draft Rounds")
    async def draft_rounds_button(self, button, inter):
        await inter.response.defer()
        await inter.send("How many rounds do you want the draft to be?", ephemeral=True, delete_after=5)
        response = await get_user_response(self.command_self, inter)
        if not response:
            return await inter.send(
                "The response has timed out",
                ephemeral=True,
            )
      
        try:
           response = int(response)
        except ValueError:
           return await inter.send("Has to be a number like: 3, 7, 9", ephemeral=True)

        pc = await premium_guild_check(inter.guild.id)
        if response > 20 and not pc:
           return await inter.send(f"Non-premium users can't have a draft over 20 rounds {Links.premium_link}", ephemeral=True)

        self.settings['Rounds'] = response
        embed = await settings_embed(self.teams, self.settings)
        await inter.edit_original_message(embed=embed, view=DraftSettingsMenu(inter, self.teams, self.command_self, self.settings))


    @disnake.ui.button(label="Time Per Pick")
    async def time_per_pick_button(self, button, inter):
        await inter.response.defer()
        await inter.send("How long do coaches get per pick. Example: 3m 20 seconds", ephemeral=True, delete_after=5)
        response = await get_user_response(self.command_self, inter)
        if not response:
            return await inter.send(
                "The response has timed out",
                ephemeral=True,
            )
        pc = await premium_guild_check(inter.guild.id)
        if not pc:
            return await inter.send(not_premium_message)

        time = await parse_duration(response)
        time = time.total_seconds()
        if str(time) == "0:00":
            time = 180

        if time > 870: # 14:50 (max is 15, but need time to edit messages and stuff)
           return await inter.send("The max time you can put is 14 minutes and 50 seconds", ephemeral=True)

        if time <= 10:
            return await inter.send('Time has to be over 10 seconds', ephemeral=True)

        self.settings['Time Per Pick'] = time
        embed = await settings_embed(self.teams, self.settings)
        await inter.edit_original_message(embed=embed, view=DraftSettingsMenu(inter, self.teams, self.command_self, self.settings))


    @disnake.ui.button(label="Eligibility Role")
    async def eligibility_role_button(self, button, inter):
        await inter.response.defer()
        await inter.send("What role must a user have to be drafted? Mention a role", ephemeral=True, delete_after=5)
        response = await get_user_response(self.command_self, inter)
        if not response:
            return await inter.send(
                "The response has timed out",
                ephemeral=True,
            )
      
        # maybe with premium you can put mutilple roles they can have, roles they cant have, etc.
        role_id = re.findall(r'<@&(\d+)>', response)
        if not role_id:
           return await inter.send("That is not a vaild role", ephemeral=True)
        role = inter.guild.get_role(int(role_id[0]))
        if not role:
           return await inter.send("That role is invaild", ephemeral=True)
        
        self.settings['Eligibility Role'] = role
        embed = await settings_embed(self.teams, self.settings)
        await inter.edit_original_message(embed=embed, view=DraftSettingsMenu(inter, self.teams, self.command_self, self.settings))

    @disnake.ui.button(label="Draft Channel")
    async def draft_channel_button(self, button, inter):
        await inter.response.defer()
        await inter.send("What channel do you want draft annoucements to be sent? Mention a channel", ephemeral=True, delete_after=5)
        response = await get_user_response(self.command_self, inter)
        if not response:
            return await inter.send(
                "The response has timed out",
                ephemeral=True,
            )
      
        # maybe with premium you can put mutilple channels they can have, channels they cant have, etc.
        channel_id = re.findall(r'<#(\d+)>', response)
        if not channel_id:
           return await inter.send("That is not a vaild channel", ephemeral=True)
        channel = inter.guild.get_channel_or_thread(int(channel_id[0]))
        if not channel:
           return await inter.send("That channel is invaild", ephemeral=True)
        
        self.settings['Draft Channel'] = channel
        embed = await settings_embed(self.teams, self.settings)
        await inter.edit_original_message(embed=embed, view=DraftSettingsMenu(inter, self.teams, self.command_self, self.settings))

class DraftPicksType(disnake.ui.View):
    def __init__(self, inter, teams, command_self, settings):
      super().__init__()
      self.inter = inter
      self.teams = teams
      self.command_self = command_self
      self.settings = settings

    async def on_timeout(self):
        await self.inter.edit_original_message(
          view=None,
          content="Command has expired, run `/draft` to use the command again",
        )
  
    async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
        if inter.author.id != self.inter.author.id:
            await inter.response.send_message("This is not your menu!", ephemeral=True)
            return False
        return True

    @disnake.ui.button(label="Random")
    async def random_schedule_button(self, button, inter):
        self.settings['Draft Picks'] = "Random"
        embed = await settings_embed(self.teams, self.settings)
        await inter.response.edit_message(embed=embed, view=DraftSettingsMenu(inter, self.teams, self.command_self, self.settings))

    @disnake.ui.button(label="Snake")
    async def round_robin_schedule_button(self, button, inter):
        self.settings['Draft Picks'] = 'Snake'
        embed = await settings_embed(self.teams, self.settings)
        await inter.response.edit_message(embed=embed, view=DraftSettingsMenu(inter, self.teams, self.command_self, self.settings))


    @disnake.ui.button(label="Custom")
    async def standings_standing(self, button, inter):
        await inter.response.defer()
        await inter.send("To make a custom draft order you have to follow this format. Watch this video <https://youtu.be/LefzTSf3oWA> (You have 5 mins before this timeouts)", ephemeral=True)

        response = await get_user_response(self.command_self, inter, 360)
        if not response:
            return await inter.send(
                "The response has timed out",
                ephemeral=True,
            )
      
      # @team @team @team @team , @team @team @team @team

        rounds = response.split(',')
        pc = await premium_guild_check(inter.guild.id)

        custom_order = []
        for round_number, round_text in enumerate(rounds, start=1):
            if round_number > 20 and not pc:
                return await inter.send(f"Non-premium users can't have a draft over 20 rounds {Links.premium_link}", ephemeral=True)

            role_ids = re.findall(r'<@&(\d+)>', round_text)
            if not role_ids:
                return await inter.send("That gave some roles that were invaild", ephemeral=True)
            
            teams = await get_team_roles(inter, role_ids)

            if len(role_ids) != len(self.teams):
                return await inter.send(f"You can't have {len(role_ids)} picks in a round with {len(self.teams)} teams", ephemeral=True)

            if not all(team in self.teams for team in teams):
                return await inter.send("Invalid team(s) found in custom order", ephemeral=True)

            custom_order.append({'Round': round_number, 'Teams': teams})
            
        message = ""
        for round_info in custom_order:
            round_number = round_info['Round']
            team_order = round_info['Teams']
            teams_ = [team.name for team in team_order]
            message += f"\nRound {round_number}: {', '.join(teams_)}"

        data = BytesIO(message.encode("utf-8"))
        await inter.send(
            file=disnake.File(data, filename=f"{inter.guild.name}_Draft_Order_BreadWinnerB.txt"),
            content='Custom Order'
        )

        self.settings['Draft Picks'] = custom_order
        self.settings['Rounds'] = len(custom_order)
        embed = await settings_embed(self.teams, self.settings)
        await inter.message.edit(embed=embed, view=DraftSettingsMenu(inter, self.teams, self.command_self, self.settings))


class DraftPlayerView(disnake.ui.View):
   def __init__(self, inter, team_threads, team, draft_order, settings):
      super().__init__(timeout=settings['Time Per Pick']) # seconds
      self.player = None
      self.coach = None

      self.inter = inter
      self.team = team
      self.settings = settings

      self.add_item(DraftPlayer(inter, team_threads, draft_order, settings))

   async def on_timeout(self):
        draft_channel = self.settings['Draft Channel']
        passed_pick = Embed(title="Missed Pick", description=f"The {self.team.mention} did not use their draft picked and have been skipped")
        await passed_pick.league_embed(user=self.inter.author, guild=self.inter.guild, role=self.team)
        await draft_channel.send(embed=passed_pick)

   async def interaction_check(self, inter):
        coach = await has_role('FranchiseRole', inter.guild.id, inter.author)
        if not coach:
            await inter.response.send_message("You are unable to draft player as you are not a coach", ephemeral=True)
            return False
        if self.team not in inter.author.roles:
            await inter.send(f"{inter.author.mention} you are not on the {self.team.mention}", ephemeral=True)
            return False
        return True
                  

class DraftPlayer(disnake.ui.UserSelect):
    def __init__(self, inter, team_threads, draft_order, settings):
       super().__init__(placeholder="Pick the player you want to draft", max_values=1)
       self.inter = inter
       self.team_threads = team_threads
       self.draft_orders = draft_order
       self.settings = settings

    async def callback(self, inter):
        await inter.response.defer()

        draft_role = self.settings['Eligibility Role']
        player = self.values[0]
  
        if draft_role and draft_role not in player.roles:
            await inter.send(
                f"{player.mention} `{player.display_name}` is unable to be drafted as they do not have the {draft_role}. Draft someone else"
            ) 
        elif inter.author == player:
            await inter.send("You can't draft yourself you goon. Draft someone else")
        else:
            player_on_team = False
            
            # Loop through team roles and check if the player has any of them
            for team in self.team_threads.keys():
                if team in player.roles:
                    player_on_team = True
                    await inter.send(f"{player.mention} `{player.display_name}` is already on the {team}. Draft someone else")
                    break 
                    
            if not player_on_team:
                self.view.player = player
                self.view.coach = inter.author
                self.view.stop()

class DraftCommands(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  @commands.slash_command()
  @commands.has_permissions(administrator=True)
  @commands.bot_has_permissions(manage_channels=True, embed_links=True, manage_roles=True, manage_threads=True)
  async def draft(self, inter):
    """Draft System"""
    content = "**Watch this video for an example <>**"
    embed = Embed(
        title="Draft Setup",
        description="Pick the teams you want in the draft",
        user=inter.author
    )
    await inter.response.send_message(content=content, embed=embed, view=SelectTeamsView(self, inter))

def setup(bot):
  bot.add_cog(DraftCommands(bot))
