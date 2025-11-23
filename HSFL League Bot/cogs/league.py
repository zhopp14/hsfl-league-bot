import random
import urllib.parse
import logging

import disnake
from disnake.ext import commands

logger = logging.getLogger(__name__)

from utils.config import SETTINGS, Links, not_premium_message
from utils.database import Database
from utils.embed import Embed
from utils.signing_tools import send_notfication_channel, team_check, under_contract
from utils.tools import (
    format_database_data,
    get_user_response,
    guild_members,
    has_perms,
    has_role,
    premium_guild_check,
    premium_user_check,
    search_role_emoji,
    search_embed_ids,
)

NO_RINGS_ROAST = [
    "Bro has no rings 😂",
    "You have no rings and will never get one",
    "You realy thought you were going to have a ring?",
    "You are to bad to have a ring",
    "You fucking suck bro, why would you have a ring",
    "You have no lego rings, and will never get a wedding ring either. You loser 😂",
    "Maybe try looking for a ring next season. Trash can.",
    "You're not good enough for a ring",
    "You suck bro, you have no rings",
    "You have no rings, and will never have any",
    "Stop wasting your time running this command. You do not have any rings 💀",
    "Bro the only ring you have ever gotten is a Ring Pop. You fatass",
    "Fucking retard you suck at this game and will never get a ring you good for nothing sack of shit",
    "cuh has no rings 👎👎💯💯🔥🔥",
    "No rings? Not surprised",
    "You are beyond trash little bro we all know you do not have any rings",
    "You suck git no rings",
    "Tom Brady has 7 rings, and you have 0",
    "Giveup on all your dreams, you can't even win in lego football. Trash no rings lol 😆😆",
    "Did you really think you had a ring? lmao you're trash kid",
    "Dawg you're not even good at this game. You have no rings and won't ever get one",
    "Little bro you're fucking TRASH LMAO YOU DON'T HAVE ANY RINGS AND I MEAN ZERO RINGS LIKE NOTHING 😂😂",
    "You and I have the same amount of rings, and I have zero rings",
    "You have no rings cuh",
    "Shit can you have no rings",
    "You don't have any rings. Go get some bitches instead",
    "It's ok bro not everyone can get rings. Just try harder and one day you will get one. Nah, just kidding you fucking suck little dude. You won't ever win a ring LOL 😂",
    "How is it even possible to have no rings?",
    "I hope my kids don't grow up to be ringless like you. Loser.",
    "Kid you have zero rings and will never get any",
    "You really wish you had a ring huh? Yeah, you have none lol.",
    "No rings, No bitches, No money, No nothing. You suck at life",
    "if you want a ring. How bout you get good?",
    "Dumbass you don't have a ring",
    "Bro stop asking me if you have a ring. You will never get one df LMAO 💀💀",
    "You're trash kid no rings",
    "https://media.tenor.com/AO_jTkCSPP8AAAAM/itsbare-ring.gif",
]


# admin command
def error_embed(title, description):
    embed = Embed(title, description).danger_embed()
    return embed


user_choices = ["contract", "demands"]

# put in userinfo in pickup host, drafted info
# maybe from preium save how many pickups have happneddddd


async def update_game_embed(bot, inter, message_type):
    try:
        await inter.response.defer()
        await inter.send("Send a message", ephemeral=True, delete_after=5)
        response = await get_user_response(bot, inter)
        if not response:
            return await inter.send("Response has timed out", ephemeral=True)

        if message_type == "🎥 Stream Link":
            parsed_url = urllib.parse.urlparse(response)
            if not parsed_url.scheme in ("http", "https"):
                return await inter.send(
                    "Make sure you are sending a valid link, if you don't have a link then use the `Notes` button",
                    ephemeral=True,
                )

        if not inter.message.embeds or len(inter.message.embeds) == 0:
            return await inter.send("Could not find game embed to update", ephemeral=True)

        embed = inter.message.embeds[0]
        current_desc = embed.description or ""
        new_desc = (
            current_desc
            + f"\n > **{message_type}:** {response} - `{inter.author.display_name}`"
        )
        embed.description = new_desc
        await inter.edit_original_message(embed=embed)
    except Exception as e:
        logger.error(f"Error updating game embed: {e}", exc_info=True)
        try:
            await inter.send(f"Error updating game embed: {str(e)}", ephemeral=True)
        except Exception:
            pass


class LinkButton(disnake.ui.View):
    def __init__(self, button_name, button_url):
        super().__init__(timeout=None)
        self.add_item(disnake.ui.Button(label=button_name, url=button_url, emoji="🔗"))


class GameInformationView(disnake.ui.View):
    def __init__(self, inter):
        super().__init__(timeout=None)
        self.inter = inter

        self.add_item(
            disnake.ui.Button(
                label="Team Thread",
                emoji="🛠️",
                style=disnake.ButtonStyle.green,
                custom_id=f"teamthread-{inter.author.id}",
            )
        )

        self.add_item(
            disnake.ui.Button(
                label="Game Time",
                emoji="⏰",
                style=disnake.ButtonStyle.blurple,
                custom_id=f"gametime-{inter.author.id}",
            )
        )
        self.add_item(
            disnake.ui.Button(
                label="Stream Link",
                emoji="🎥",
                style=disnake.ButtonStyle.blurple,
                custom_id=f"streamlink-{inter.author.id}",
            )
        )

        self.add_item(
            disnake.ui.Button(
                label="Referee",
                emoji="🏁",
                style=disnake.ButtonStyle.blurple,
                custom_id=f"referee-{inter.author.id}",
            )
        )

        self.add_item(
            disnake.ui.Button(
                label="Scores Update",
                emoji="💯",
                style=disnake.ButtonStyle.blurple,
                custom_id=f"scoresupdate-{inter.author.id}",
            )
        )

        self.add_item(
            disnake.ui.Button(
                label="Notes",
                emoji="📝",
                style=disnake.ButtonStyle.blurple,
                custom_id=f"notes-{inter.author.id}",
            )
        )

        self.add_item(
            disnake.ui.Button(
                label="End Game",
                style=disnake.ButtonStyle.red,
                custom_id=f"endgame-{inter.author.id}",
            )
        )


class LeagueCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_button_click(self, inter):
        if not hasattr(inter, 'component') or not inter.component or not hasattr(inter.component, 'custom_id'):
            return
        
        custom_id = inter.component.custom_id
        
        if not custom_id:
            return

        try:
            og_author = custom_id.split("-")
            og_author_id = og_author[-1]  # The last part contains the ID

            staff = inter.channel.permissions_for(inter.author).administrator
            author = int(inter.author.id) == int(og_author_id)
        except (ValueError, AttributeError, IndexError):
            return

        if custom_id == f"teamthread-{og_author_id}":
            if not (staff or author):
                return await inter.response.send_message(
                    "You do not have access to use this button", ephemeral=True
                )

            try:
                if not inter.message.embeds or len(inter.message.embeds) == 0:
                    return await inter.response.send_message(
                        "Could not find game embed", ephemeral=True
                    )
                
                roles = await search_embed_ids(
                    inter.message.embeds[0].description, "role", inter.guild
                )
                
                if not roles or len(roles) < 2:
                    return await inter.response.send_message(
                        "Could not find both teams in the game", ephemeral=True
                    )

                thread_name = " vs ".join([role.name for role in roles])
                try:
                    thread = await inter.channel.create_thread(
                        name=thread_name,
                        type=disnake.ChannelType.private_thread,
                        invitable=False,
                    )
                except Exception as e:
                    return await inter.response.send_message(f"Error creating thread: {str(e)}", ephemeral=True)

                for role in roles:
                    try:
                        members = await guild_members(inter.guild, role)
                        for member in members:
                            try:
                                await thread.add_user(member)
                            except Exception:
                                pass  # Skip if can't add user
                    except Exception:
                        pass  # Skip if can't get members
                
                await inter.response.send_message(thread.jump_url, ephemeral=True)
            except Exception as e:
                logger.error(f"Error updating game embed: {e}", exc_info=True)
                try:
                    await inter.response.send_message(f"Error: {str(e)}", ephemeral=True)
                except Exception:
                    pass

        if custom_id == f"gametime-{og_author_id}":
            if staff or author:
                return await update_game_embed(self.bot, inter, "⏰ Game Time")

            try:
                coach = await has_role("FranchiseRole", inter.guild.id, inter.author)
                if not inter.message.embeds or len(inter.message.embeds) == 0:
                    return await inter.response.send_message(
                        "Could not find game embed", ephemeral=True
                    )
                
                roles = await search_embed_ids(
                    inter.message.embeds[0].description, "role", inter.guild
                )
                if coach:
                    for role in inter.author.roles:
                        if role in roles:
                            return await update_game_embed(self.bot, inter, "⏰ Game Time")
            except Exception as e:
                logger.error(f"Error: {e}", exc_info=True)
            
            return await inter.response.send_message(
                "You do not have access to use this button", ephemeral=True
            )

        if custom_id == f"streamlink-{og_author_id}":
            try:
                streamer = await has_role("StreamerRole", inter.guild.id, inter.author)
                if staff or author or streamer:
                    return await update_game_embed(self.bot, inter, "🎥 Stream Link")
            except Exception as e:
                logger.error(f"Error: {e}", exc_info=True)
            return await inter.response.send_message(
                "You do not have access to use this button", ephemeral=True
            )

        if custom_id == f"referee-{og_author_id}":
            try:
                referee = await has_role("RefereeRole", inter.guild.id, inter.author)
                if staff or author or referee:
                    return await update_game_embed(self.bot, inter, "🏁 Referee")
            except Exception as e:
                logger.error(f"Error: {e}", exc_info=True)
            return await inter.response.send_message(
                "You do not have access to use this button", ephemeral=True
            )

        if custom_id == f"scoresupdate-{og_author_id}":
            if staff or author:
                return await update_game_embed(self.bot, inter, "💯 Score")
            return await inter.response.send_message(
                "You do not have access to use this button", ephemeral=True
            )

        if custom_id == f"notes-{og_author_id}":
            if staff or author:
                return await update_game_embed(self.bot, inter, "📝 Note")
            return await inter.response.send_message(
                "You do not have access to use this button", ephemeral=True
            )

        if custom_id == f"endgame-{og_author_id}":
            if staff or author:
                return await inter.response.edit_message(
                    view=None, content="🎉 Game Over 🎉"
                )
            return await inter.response.send_message(
                "You do not have access to use this button", ephemeral=True
            )

    @commands.slash_command()
    async def gametime(self, inter):
        await inter.response.send_message("Use `/game`", ephemeral=True)

    @commands.slash_command()
    async def game(
        self,
        inter: disnake.GuildCommandInteraction,
        team1: disnake.Role,
        team2: disnake.Role,
    ):
        """
        Show live updates of a game
        Parameters
        ----------
        team1: Team 1
        team2: Team 2
        """
        try:
            # Get icons with proper fallbacks
            icon = None
            if inter.guild.icon:
                icon = inter.guild.icon.url
            elif inter.guild.me.avatar:
                icon = inter.guild.me.avatar.url
            
            coach_avatar = None
            if inter.author.display_avatar:
                coach_avatar = inter.author.display_avatar.url
            elif inter.guild.me.avatar:
                coach_avatar = inter.guild.me.avatar.url
            
            # Get team emojis
            team1_emoji = ""
            team2_emoji = ""
            try:
                team1_emoji_result = await search_role_emoji(inter.guild, team1.name)
                if team1_emoji_result:
                    team1_emoji = str(team1_emoji_result) + " "
            except Exception:
                pass
            
            try:
                team2_emoji_result = await search_role_emoji(inter.guild, team2.name)
                if team2_emoji_result:
                    team2_emoji = " " + str(team2_emoji_result)
            except Exception:
                pass

            embed = Embed(
                title="Game Information",
                description=f"{team1_emoji}{team1.mention} vs {team2.mention}{team2_emoji}",
            )
            
            if icon:
                embed.set_thumbnail(url=icon)
            
            embed.timestamp = disnake.utils.utcnow()
            
            if icon:
                embed.set_author(name=f"{inter.guild.name} Transactions", icon_url=icon)
            else:
                embed.set_author(name=f"{inter.guild.name} Transactions")
            
            if coach_avatar:
                embed.set_footer(text=f"{inter.author.name}", icon_url=coach_avatar)
            else:
                embed.set_footer(text=f"{inter.author.name}")

            await inter.response.send_message(embed=embed, view=GameInformationView(inter))
        except Exception as e:
            logger.error(f"Error creating game: {e}", exc_info=True)
            try:
                await inter.response.send_message(f"Error creating game: {str(e)}", ephemeral=True)
            except Exception:
                await inter.send(f"Error creating game: {str(e)}", ephemeral=True)

    @commands.slash_command()
    async def admin(self, inter: disnake.GuildCommandInteraction):
        return

    @admin.sub_command(name="user-clear")
    async def user_clear(
        self,
        inter,
        table: str = commands.Param(choices=user_choices, default=None),
        member: disnake.Member = None,
    ):
        """
        Clears all the data for users, put no table to remove all user data
        Parameters
        ----------
        table: To remove only one table
        member: Removes the data for only one player
        """
        pc = await premium_guild_check(inter.guild.id)
        if not pc:
            await inter.response.send_message(not_premium_message)

        user_data = await Database.get_data("Users", inter.guild.id)
        if user_data is None or not isinstance(user_data, dict):
            return await inter.response.send_message(
                "No users have any data", ephemeral=True
            )

        if member:  # test dis
            if table:
                delete = await Database.delete_data(
                    "Users", f"{inter.guild.id}/{str(member.id)}"
                )
                if not delete:
                    return await inter.response.send_message(
                        f"{member.mention} does not have any data", ephemeral=True
                    )
                embed = Embed(
                    title="Player Data Deleted",
                    description=f"{member.mention} {table} data has been deleted",
                    user=inter.author,
                )
                return await inter.response.send_message(embed=embed)
            else:
                delete = await Database.delete_data(
                    "Users", f"{inter.guild.id}/{str(member.id)}/{table}"
                )
                if not delete:
                    return await inter.response.send_message(
                        f"{member.mention} does not have any data", ephemeral=True
                    )
                embed = Embed(
                    title="Player Data Deleted",
                    description=f"{member.mention} {table} data has been deleted",
                    user=inter.author,
                )
                return await inter.response.send_message(embed=embed)
        else:
            if not table:
                delete = await Database.delete_data("Users", f"{inter.guild.id}")
                if not delete:
                    return await inter.response.send_message(
                        "No users currently have any data", ephemeral=True
                    )
                embed = Embed(
                    title="Data Wiped", description="All user data has been removed"
                )
                await inter.response.send_message(embed=embed)
            else:
                data = await Database.get_data("Users", f"{inter.guild.id}")
                for user_id, user_data in data.items():
                    delete = await Database.delete_data(
                        "Users", f"{inter.guild.id}/{str(user_id)}/{table}"
                    )
                    if not delete:
                        return await inter.response.send_message(
                            f"No users currently have any {table} data", ephemeral=True
                        )
                embed = Embed(
                    title="Data Wiped", description=f"All {table} data has been removed"
                )
                await inter.response.send_message(embed=embed)

    # make a command that shows all the current offers and amount ig
    # contract_data = await Database.get_db_key(guild.id, 'Users')
    # contract_len = 0
    # for user_id, user_data in contract_data.items():
    # for data in user_data:
    # if 'contract' in user_data:
    # contract_len  = contract_len + 1
    # embed.add_field(name="Current Contracts", value=f"{contract_len}")

    @commands.slash_command()
    async def userinfo(
        self, inter: disnake.GuildCommandInteraction, user: disnake.Member = None
    ):
        """
        Shows league information about a user
        Paremeters
        ----------
        user: The user to show information about
        """
        guild = inter.guild
        user = user or inter.author
        pl = Links.premium_link

        await inter.response.defer()
        embed = Embed(
            title=f"{user.name} Information", description=f"`ID:` {user.id}", user=user
        )
        embed.set_thumbnail(user.display_avatar)

        # loop through user data
        user_data = await Database.get_data("Users", f"{guild.id}/{user.id}")
        if user_data and isinstance(user_data, dict):
            for key, value in user_data.items():
                embed.add_field(name=key.capitalize(), value=str(value))

        user_p_check = await premium_user_check(self.bot, user)
        if not user_p_check:
            user_p_check = f"[False]({pl})"
        embed.add_field(name="Preimum User?", value=user_p_check)

        await inter.send(embed=embed)

    # team info

    @commands.slash_command()
    async def leagueinfo(self, inter: disnake.GuildCommandInteraction):
        """
        Shows information about a league
        """
        try:
            guild = inter.guild

            await inter.response.defer()
            await inter.send("🔄 Loading league information...", delete_after=2)
            
            embed = Embed(
                title=f"{guild.name} Information",
            )
            
            if guild.icon:
                embed.set_thumbnail(guild.icon)

            try:
                p_check = await premium_guild_check(inter.guild.id)
                if not p_check:
                    p_check = f"[False]({Links.premium_link})"
                embed.add_field(name="Premium?", value=p_check)
            except Exception as e:
                logger.error(f"Error checking premium: {e}", exc_info=True)
                embed.add_field(name="Premium?", value="Unknown")

            try:
                roster_cap = await Database.get_data("RosterCap", guild.id)
                if roster_cap is None:
                    roster_cap = "No roster cap set"
                else:
                    roster_cap = str(roster_cap)
                embed.add_field(name="Roster Cap", value=roster_cap)
            except Exception as e:
                logger.error(f"Error getting roster cap: {e}", exc_info=True)
                embed.add_field(name="Roster Cap", value="No roster cap set")

            try:
                demand_limit = await Database.get_data("DemandLimit", guild.id)
                if demand_limit is None:
                    demand_limit = "No demand limit set"
                else:
                    demand_limit = str(demand_limit)
                embed.add_field(name="Demand Limit", value=demand_limit)
            except Exception as e:
                logger.error(f"Error getting demand limit: {e}", exc_info=True)
                embed.add_field(name="Demand Limit", value="No demand limit set")

            try:
                suspended_data = await Database.get_data("Suspensions", guild.id)
                if suspended_data and isinstance(suspended_data, dict):
                    suspended_text = []
                    for user_id, user_data in suspended_data.items():
                        try:
                            if isinstance(user_data, dict):
                                user = guild.get_member(int(user_id))
                                if user:
                                    duration = user_data.get('duration', 'N/A')
                                    reason = user_data.get('reason', 'N/A')
                                    bail = user_data.get('bail', 'N/A')
                                    suspended_text.append(
                                        f"{user.mention} - duration: {duration}, reason: {reason}, bail: {bail}"
                                    )
                        except (ValueError, KeyError) as e:
                            logger.error(f"Error processing suspended user {user_id}: {e}", exc_info=True)
                            continue
                    
                    if suspended_text:
                        suspended_field_value = "\n".join(suspended_text)
                        embed.add_field(
                            name="Suspended Users", value=suspended_field_value, inline=False
                        )
            except Exception as e:
                logger.error(f"Error getting suspensions: {e}", exc_info=True)

            await inter.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in leagueinfo command: {e}", exc_info=True)
            try:
                await inter.send(f"An error occurred: {str(e)}", ephemeral=True)
            except Exception:
                pass

    @commands.slash_command()
    async def lfp(
        self,
        inter: disnake.ApplicationCommandInteraction,
        team: disnake.Role,
        description: str,
    ):
        """
        Send a message that your are currently looking for players
        Parameters
        ----------
        team: The team looking for players
        description: What the team is looking for
        """
        try:
            await inter.response.defer()
            await inter.send("🔄 Processing LFP request...", delete_after=2)
            
            # Check if user is a coach
            coach_check = await has_role("FranchiseRole", inter.guild.id, inter.author)
            if not coach_check:
                return await inter.send(
                    embed=error_embed(
                        "❌ Not a Coach", "You have to be a coach to use this command. You need a Franchise Role."
                    ),
                    delete_after=10,
                )

            # Check if user is on the team
            if team not in inter.author.roles:
                return await inter.send(
                    embed=error_embed("❌ Not On Team", f"You're not on the `{team.name}` team"),
                    delete_after=10,
                )

            # Check if team is in database
            try:
                team_check_ = await team_check(inter.guild.id, team)
                if not team_check_:
                    return await inter.send(
                        embed=error_embed(
                            "❌ Team Not in Database",
                            f"The `{team}` role is not in the teams database. Add it using `/setup` first.",
                        ),
                        delete_after=10,
                    )
            except Exception as e:
                return await inter.send(
                    embed=error_embed(
                        "❌ Error",
                        f"Error checking team database: {str(e)}"
                    ),
                    delete_after=10,
                )

            # Create and send embed
            try:
                embed = Embed(
                    title="Looking For Player",
                    description=f"The {team.mention} are currently looking for players \n > **Description:** {description}\n > **Coach:** {inter.author.mention} `{inter.author.display_name}`",
                )
                await embed.league_embed(user=inter.author, guild=inter.guild, role=team)
                await inter.send(embed=embed)
            except Exception as e:
                return await inter.send(
                    embed=error_embed(
                        "❌ Error",
                        f"Error creating LFP message: {str(e)}"
                    ),
                    delete_after=10,
                )
        
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            try:
                await inter.send(
                    embed=error_embed("❌ Error", f"An error occurred: {str(e)}"),
                    delete_after=10,
                )
            except Exception:
                pass

    @commands.slash_command()
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def disband(self, inter: disnake.GuildCommandInteraction, team: disnake.Role):
        """
        Gets rid of all the players and coaches on a team
        Parameters
        ----------
        team: The team to disband
        """
        await inter.response.defer()

        if await has_perms(team):
            return await inter.response.send_message(
                "To prevent abuse, roles with permissions aren't allowed to be used in signing commands",
                ephemeral=True,
            )

        team_check_ = await team_check(inter.guild.id, team)
        if not team_check_:
            return await inter.send(
                embed=error_embed(
                    "Team Not in Database",
                    f"The `{team}` role is not in the teams database()",
                ),
                delete_after=10,
            )

        removed_members = []
        removed_coaches = []
        error_members = []

        members = await guild_members(inter.guild, team)
        for member in members:
            # if team in member.roles:
            try:
                await member.remove_roles(team)
                removed_members.append(member.mention)
            except disnake.Forbidden:
                error_members.append(member.mention)
                continue

            coach_role_check = await has_role("FranchiseRole", inter.guild.id, member)
            if coach_role_check:
                role_id = await has_role("FranchiseRole", inter.guild.id, member, "id")
                coach_role = inter.guild.get_role(int(role_id))
                await member.remove_roles(coach_role)
                removed_coaches.append(f"{member.mention} - {coach_role.mention}")

        if removed_members:
            embed = Embed(
                title="Team Disbanded",
                description=f"The {team.mention} have been disbanded \n > **Command By:** {inter.author.mention} `{inter.author.display_name}`",
            )
            await embed.league_embed(user=inter.author, guild=inter.guild, role=team)
            player_amount = len(removed_members)
            embed.add_field(
                name=f"Players - {player_amount}", value=" ".join(removed_members)
            )

        if removed_coaches:
            embed.add_field(name="Coaches", value="\n".join(removed_coaches))

        if error_members:
            embed.add_field(
                name="I was unable to remove these users roles",
                value="".join(error_members),
            )

        if embed:
            await inter.send(embed=embed)
            await send_notfication_channel(inter.guild, embed)
        else:
            await inter.send("I could find no players on that team", ephemeral=True)

    @commands.slash_command()
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def swap(
        self,
        inter: disnake.GuildCommandInteraction,
        team1: disnake.Role,
        team2: disnake.Role,
    ):
        """
        Swaps the teams players are on
        Parameters
        ----------
        team1: These players get the role from "team2"
        team2: These players get the role from "team1"
        """
        await inter.response.defer()

        if await has_perms(team1) or await has_perms(team2):
            return await inter.response.send_message(
                "To prevent abuse, roles with permissions aren't allowed to be used in signing commands",
                ephemeral=True,
            )

        good_members_1 = []
        error_members_1 = []

        good_members_2 = []
        error_members_2 = []

        team1_members = await guild_members(inter.guild, team1)
        for member in team1_members:
            try:
                await member.remove_roles(team1)
                await member.add_roles(team2)
                good_members_1.append(member.mention)
            except disnake.Forbidden:
                error_members_1.append(member.mention)
                continue

        team2_members = await guild_members(inter.guild, team2)
        for member in team2_members:
            try:
                await member.remove_roles(team2)
                await member.add_roles(team1)
                good_members_2.append(member.mention)
            except disnake.Forbidden:
                error_members_2.append(member.mention)
                continue

        if good_members_1 and good_members_2:
            # not using embed.league_embed, bc we using 2 emojis and using the emojis in the description
            icon = inter.guild.icon or inter.guild.me.avatar.url
            coach_avatar = inter.author.display_avatar.url or inter.guild.me.avatar.url

            embed = Embed(
                title="Team Swap Results",
                description=f"The {team1.mention} and {team2.mention} have been swapped \n > **Command By:** {inter.author.mention} `{inter.author.display_name}`",
            )
            embed.set_thumbnail(url=icon)
            embed.timestamp = disnake.utils.utcnow()
            embed.set_author(name=f"{inter.guild.name} Transactions", icon_url=icon)
            embed.set_footer(text=f"{inter.author.name}", icon_url=coach_avatar)

            team1_emoji = await search_role_emoji(inter.guild, team1.name) or ""
            team1_players = " ".join(good_members_1)

            team2_emoji = await search_role_emoji(inter.guild, team2.name) or ""
            team2_players = " ".join(good_members_2)

            embed.add_field(
                name="Players",
                value=f"{team1_emoji} {team1.mention}: {team1_players}\n{team2_emoji} {team2.mention}: {team2_players}",
            )

            if error_members_1:
                embed.add_field(
                    name=f"I was unable to switch these players for {team1.name}",
                    value=" ".join(error_members_1),
                    inline=False,
                )
            if error_members_2:
                embed.add_field(
                    name=f"I was unable to switch these players for {team2.name}",
                    value=" ".join(error_members_2),
                    inline=True,
                )

            await inter.send(embed=embed)
            await send_notfication_channel(inter.guild, embed)
        else:
            await inter.send(
                "I could not find players on both those teams", ephemeral=True
            )

    @commands.slash_command()
    async def members(self, inter: disnake.GuildCommandInteraction, role: disnake.Role):
        """Show all the members that have a certain role"""
        await inter.response.defer()

        members_list = []
        coaches_list = []

        members = await guild_members(inter.guild, role)
        for member in members:
            members_list.append(
                f"**{member.display_name}** ({member.mention}, `{member.id}`)"
            )

            coach = await has_role("FranchiseRole", inter.guild.id, member)
            if coach:
                coaches_list.append(f"{member.display_name}")

        embed = Embed(
            title=f"{role} - {len(members)}",
            description="\n".join(members_list),
            color=role.color,
        )
        emoji = await search_role_emoji(inter.guild, role.name) or None
        embed.set_thumbnail(url=emoji.url if emoji else None)

        if coaches_list:
            embed.add_field(name="Coaches", value=", ".join(coaches_list))

        await inter.send(embed=embed)

    # challenge-ruling - your_team, other_team, reason, proof

    @commands.slash_command(name="challenge-play")
    async def challenge_play(
        self,
        inter: disnake.GuildCommandInteraction,
        opposing_team: disnake.Role,
        reason: str,
        proof: disnake.Attachment,
        your_team: disnake.Role = None,
        more_proof1: disnake.Attachment = None,
        more_proof2: disnake.Attachment = None,
    ):
        """
        Challenge a play or ruling
        Parameters
        ----------
        opposing_team: The team you are putting the challenge againsted
        reason: The reason why you are challenging
        proof: The proof that the ruling is wrong
        your_team: If you don't have teams saved, manually put your team
        more_proof1: Extra proof
        more_proof2: Extra proof
        """
        try:
            await inter.response.defer(ephemeral=True)
            await inter.send("🔄 Processing challenge...", ephemeral=True, delete_after=2)
            
            guild = inter.guild
            author = inter.author

            # Check if user is a coach
            coach_role_check = await has_role("FranchiseRole", inter.guild.id, inter.author)
            if not coach_role_check:
                return await inter.send(
                    "❌ You have to be a coach to use this command. You need a Franchise Role.", 
                    ephemeral=True
                )

            # Checks for author's team role
            try:
                db_author_role = await has_role("TeamRole", guild.id, author, "id")
                if db_author_role:
                    author_team_role = guild.get_role(int(db_author_role))
                else:
                    author_team_role = your_team
            except Exception as e:
                return await inter.send(
                    f"❌ Error checking your team role: {str(e)}", 
                    ephemeral=True
                )

            if not author_team_role:
                return await inter.send(
                    f"❌ You don't have [team roles saved]({Links.premium_link}), so please use the `your_team` parameter",
                    ephemeral=True,
                )

            if opposing_team == author_team_role:
                return await inter.send("❌ You can't challenge yourself", ephemeral=True)

            if author_team_role not in author.roles:
                return await inter.send(
                    f"❌ You are not on the {author_team_role.mention} team", 
                    ephemeral=True
                )

            # Check if opposing team is in database
            try:
                db_team_role = await team_check(guild.id, opposing_team)
                if not db_team_role:
                    return await inter.send(
                        f"❌ {opposing_team.mention} is not in the teams database. Add it using `/setup` first.",
                        ephemeral=True,
                    )
            except Exception as e:
                return await inter.send(
                    f"❌ Error checking team database: {str(e)}", 
                    ephemeral=True
                )
            
            # Get referee role
            try:
                ref = await Database.get_data('RefereeRole', inter.guild.id)
                if ref is None:
                    return await inter.send(
                        "❌ There is no referee role set up. Use `/setup roles referee role` to set one.",
                        ephemeral=True,
                    )

                # Handle both list and dict formats
                if isinstance(ref, list):
                    role_ids = ref
                elif isinstance(ref, dict):
                    role_ids = ref.values()
                else:
                    return await inter.send(
                        "❌ Invalid referee role data. Please reconfigure using `/setup roles referee role`",
                        ephemeral=True,
                    )

                refs = []
                for role_id in role_ids:
                    try:
                        role = inter.guild.get_role(int(role_id))
                        if role:
                            refs.append(role.mention)
                    except (ValueError, TypeError):
                        continue
                
                if not refs:
                    return await inter.send(
                        "❌ No valid referee roles found. Please set up referee roles using `/setup roles referee role`",
                        ephemeral=True,
                    )
            except Exception as e:
                return await inter.send(
                    f"❌ Error getting referee roles: {str(e)}", 
                    ephemeral=True
                )

            # Get referee channel
            try:
                channel_data = await Database.get_data("RefereeChannel", inter.guild.id)
                if channel_data is None:
                    return await inter.send(
                        "❌ There is no referee channel set up. Use `/setup channels referee channel` to set one.",
                        ephemeral=True,
                    )
                
                # Handle both list and dict formats
                if isinstance(channel_data, list) and channel_data:
                    channel_id = channel_data[0]
                elif isinstance(channel_data, dict) and channel_data:
                    channel_id = list(channel_data.values())[0]
                else:
                    return await inter.send(
                        "❌ Invalid referee channel data. Please reconfigure using `/setup channels referee channel`",
                        ephemeral=True,
                    )
                
                try:
                    channel = inter.guild.get_channel_or_thread(int(channel_id))
                    if not channel:
                        return await inter.send(
                            "❌ Referee channel not found. The channel may have been deleted. Please reconfigure using `/setup channels referee channel`",
                            ephemeral=True,
                        )
                except (ValueError, TypeError) as e:
                    return await inter.send(
                        f"❌ Invalid referee channel ID: {str(e)}. Please reconfigure using `/setup channels referee channel`",
                        ephemeral=True,
                    )
            except Exception as e:
                return await inter.send(
                    f"❌ Error getting referee channel: {str(e)}", 
                    ephemeral=True
                )

            # Get team emojis
            try:
                team1_emoji = await search_role_emoji(inter.guild, author_team_role.name) or ""
                team2_emoji = await search_role_emoji(inter.guild, opposing_team.name) or ""
            except Exception:
                team1_emoji = ""
                team2_emoji = ""

            # Build proof URLs
            proof_urls = [proof.url]
            if more_proof1:
                proof_urls.append(more_proof1.url)
            if more_proof2:
                proof_urls.append(more_proof2.url)
            proof_text = "\n".join(proof_urls)

            # Create and send embed
            try:
                embed = Embed(
                    title="Challenge Sent",
                    description=f"{team1_emoji} {author_team_role.mention} has challenged {team2_emoji} {opposing_team.mention} \n > **Reason:** {reason} \n > **Challenged By:** {inter.author.mention} `{inter.author.display_name}`",
                )
                embed.set_thumbnail(url="https://breadwinner.dev/images/referee_image.png")
                
                await channel.send(
                    embed=embed,
                    content=f"{''.join(refs)} \n **Proof:** \n {proof_text}",
                    allowed_mentions=disnake.AllowedMentions(roles=True),
                )

                await inter.send(
                    f"✅ Your challenge has been sent to {channel.mention}, please wait for a referee response",
                    ephemeral=True,
                )
            except disnake.Forbidden:
                return await inter.send(
                    f"❌ I don't have permission to send messages in {channel.mention}. Please check bot permissions.",
                    ephemeral=True,
                )
            except Exception as e:
                return await inter.send(
                    f"❌ Error sending challenge: {str(e)}", 
                    ephemeral=True
                )
        
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            try:
                await inter.send(
                    f"❌ An error occurred while processing your challenge: {str(e)}", 
                    ephemeral=True
                )
            except Exception:
                pass

    @commands.slash_command()
    async def referee(
        self,
        inter: disnake.GuildCommandInteraction,
        challenging_team: disnake.Role,
        opposing_team: disnake.Role,
        call_on_the_field: str,
        ruling: str,
    ):
        """
        Make a call on a challenged play
        Parameters
        ----------
        challenging_team: The team that challenged the play
        opposing_team: The other team
        call_on_the_field: The play they were challenging
        ruling: The outcome of the challenge
        """
        try:
            await inter.response.defer(ephemeral=True)
            await inter.send("🔄 Processing referee decision...", ephemeral=True, delete_after=2)
            
            # Check if user is a referee
            ref = await has_role("RefereeRole", inter.guild.id, inter.author)
            if not ref:
                return await inter.send("❌ You're not a referee. You need a Referee Role to use this command.", ephemeral=True)

            # Get referee channel
            try:
                channel_data = await Database.get_data("RefereeChannel", inter.guild.id)
                if channel_data is None:
                    return await inter.send(
                        "❌ There is no referee channel set up. Use `/setup channels referee channel` to set one.",
                        ephemeral=True,
                    )
                
                # Handle both list and dict formats
                if isinstance(channel_data, list) and channel_data:
                    channel_id = channel_data[0]
                elif isinstance(channel_data, dict) and channel_data:
                    channel_id = list(channel_data.values())[0]
                else:
                    return await inter.send(
                        "❌ Invalid referee channel data. Please reconfigure using `/setup channels referee channel`",
                        ephemeral=True,
                    )
                
                try:
                    channel = inter.guild.get_channel_or_thread(int(channel_id))
                    if not channel:
                        return await inter.send(
                            "❌ Referee channel not found. The channel may have been deleted. Please reconfigure using `/setup channels referee channel`",
                            ephemeral=True,
                        )
                except (ValueError, TypeError) as e:
                    return await inter.send(
                        f"❌ Invalid referee channel ID: {str(e)}. Please reconfigure using `/setup channels referee channel`",
                        ephemeral=True,
                    )
            except Exception as e:
                return await inter.send(
                    f"❌ Error getting referee channel: {str(e)}", 
                    ephemeral=True
                )

            # Get team emojis
            try:
                team1_emoji = await search_role_emoji(inter.guild, challenging_team.name) or ""
                team2_emoji = await search_role_emoji(inter.guild, opposing_team.name) or ""
            except Exception:
                team1_emoji = ""
                team2_emoji = ""

            # Create and send embed
            try:
                embed = Embed(
                    title="Referee Decision",
                    description=f"{team1_emoji} {challenging_team.mention} challenged {team2_emoji} {opposing_team.mention} \n > **Challenged Item:** {call_on_the_field} \n > **Decision:** {ruling} \n > **Referee:** {inter.author.mention} `{inter.author.display_name}`",
                )
                embed.set_thumbnail(url="https://breadwinner.dev/images/referee_image.png")
                
                await channel.send(
                    embed=embed,
                    content=f"{challenging_team.mention} {opposing_team.mention}",
                    allowed_mentions=disnake.AllowedMentions(roles=True),
                )

                await inter.send(
                    f"✅ Your decision has been sent to {channel.mention}", 
                    ephemeral=True
                )
            except disnake.Forbidden:
                return await inter.send(
                    f"❌ I don't have permission to send messages in {channel.mention}. Please check bot permissions.",
                    ephemeral=True,
                )
            except Exception as e:
                return await inter.send(
                    f"❌ Error sending decision: {str(e)}", 
                    ephemeral=True
                )
        
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            try:
                await inter.send(
                    f"❌ An error occurred while processing your decision: {str(e)}", 
                    ephemeral=True
                )
            except Exception:
                pass

    @commands.slash_command()
    async def stream(
        self,
        inter: disnake.GuildCommandInteraction,
        team1: disnake.Role,
        team2: disnake.Role,
        stream_link: str,
    ):
        """
        Annouce a stream
        Parameters
        ----------
        team1: Team 1
        team2: Team 2
        stream_link: Where the stream is happening
        """
        try:
            await inter.response.defer(ephemeral=True)
            await inter.send("🔄 Processing stream announcement...", ephemeral=True, delete_after=2)
            
            guild = inter.guild
            
            # Check if user is a streamer
            streamer = await has_role("StreamerRole", guild.id, inter.author)
            if not streamer:
                return await inter.send("❌ You are not a streamer. You need a Streamer Role to use this command.", ephemeral=True)

            # Validate stream link
            try:
                import urllib.parse
                parsed_url = urllib.parse.urlparse(stream_link)
                if not parsed_url.scheme in ("http", "https"):
                    return await inter.send("❌ Invalid stream link. Please provide a valid HTTP or HTTPS URL.", ephemeral=True)
            except Exception:
                return await inter.send("❌ Invalid stream link format.", ephemeral=True)

            # Get streaming channels
            try:
                channel_ids = await Database.get_data("StreamingChannel", guild.id)
                if channel_ids is None:
                    channel_ids = [inter.channel.id]
                else:
                    # Handle both list and dict formats
                    if isinstance(channel_ids, list):
                        channel_ids = channel_ids
                    elif isinstance(channel_ids, dict):
                        channel_ids = list(channel_ids.values())
                    else:
                        channel_ids = [inter.channel.id]
            except Exception as e:
                return await inter.send(f"❌ Error getting streaming channels: {str(e)}", ephemeral=True)

            # Get team emojis
            try:
                team1_emoji = await search_role_emoji(inter.guild, team1.name) or ""
                team2_emoji = await search_role_emoji(inter.guild, team2.name) or ""
            except Exception:
                team1_emoji = ""
                team2_emoji = ""

            # Create embed
            embed = Embed(
                title=f"{guild.name} Stream",
                description=f"{team1_emoji} {team1.mention} vs {team2_emoji} {team2.mention} \n > **Streamer:** {inter.author.mention} `{inter.author.display_name}`",
            )
            if guild.icon:
                embed.set_thumbnail(guild.icon.url)
            
            # Send to channels
            sent_channels = []
            failed_channels = []
            for channel_id in channel_ids:
                try:
                    channel = guild.get_channel_or_thread(int(channel_id))
                    if channel:
                        await channel.send(embed=embed, view=LinkButton("Watch", stream_link))
                        sent_channels.append(channel.mention)
                    else:
                        failed_channels.append(str(channel_id))
                except disnake.Forbidden:
                    failed_channels.append(f"{channel_id} (no permission)")
                except (ValueError, TypeError, Exception) as e:
                    failed_channels.append(f"{channel_id} (error: {str(e)})")
                    continue
            
            if sent_channels:
                message = f"✅ Stream sent to {', '.join(sent_channels)}"
                if failed_channels:
                    message += f"\n⚠️ Failed to send to {len(failed_channels)} channel(s)"
                await inter.send(message, ephemeral=True)
            else:
                await inter.send("❌ Failed to send stream to any channels. Check that streaming channels are set up correctly.", ephemeral=True)
        
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            try:
                await inter.send(f"❌ An error occurred: {str(e)}", ephemeral=True)
            except Exception:
                pass

    @commands.slash_command()
    async def ringcheck(
        self, inter: disnake.GuildCommandInteraction, member: disnake.Member = None
    ):
        """
        Show off your rings
        Parameters
        ----------
        member: The member to check for rings
        """
        if not member:
            member = inter.author

        guild = inter.guild
        has_rings = []
        rings = await Database.get_data("RingRole", guild.id)
        if rings is None:
            return await inter.send("This server has no ring roles set :sob:", ephemeral=True)

        # Handle both list and dict formats
        if isinstance(rings, list):
            role_ids = rings
        elif isinstance(rings, dict):
            role_ids = rings.values()
        else:
            return await inter.send("Invalid ring role data", ephemeral=True)

        has_rings = []
        for role_id in role_ids:
            try:
                role = guild.get_role(int(role_id))
                if role and role in member.roles:
                    has_rings.append(role)
            except (ValueError, TypeError):
                continue

        if not has_rings:
            roast = random.choice(NO_RINGS_ROAST)
            return await inter.send(roast)  # ROAST LIST

        has_rings = [role.mention for role in has_rings]
        embed = Embed(
            title=f"Ring Check - {len(has_rings)}", description=", ".join(has_rings)
        )
        embed.set_author(
            name=member.name,
            icon_url=member.display_avatar.url or None,
            url=Links.premium_link,
        )
        embed.set_thumbnail(url="https://breadwinner.dev/images/ring")
        await inter.send(embed=embed)

    @commands.slash_command()
    async def config(self, inter: disnake.GuildCommandInteraction):
        """Shows the server's current settings"""
        await inter.response.defer()
        guild = inter.guild
        embed = Embed(title="Server Settings")

        for value in SETTINGS.values():
            table = value["table"]
            data = await Database.get_data(table, guild.id)
            if data is not None:
                if isinstance(data, (dict, list)):
                    embed.add_field(
                        name=table,
                        value=await format_database_data(inter, table, guild.id),
                        inline=False,
                    )
                else:
                    embed.add_field(name=table, value=str(data), inline=False)

        await inter.edit_original_message(embed=embed, content=None)


def setup(bot):
    bot.add_cog(LeagueCommands(bot))