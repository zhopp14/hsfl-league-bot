import disnake
from disnake.ext import commands

from utils.database import Database
from utils.embed import Embed
from utils.signing_tools import (
    get_coach_team,
    set_coach_team,
    remove_coach_team,
    get_team_coaches,
    validate_team_ownership,
    team_check,
    set_channel_config,
    remove_channel_config,
    get_channel_config,
    get_all_channel_config,
)
from utils.tools import has_role, guild_members


def error_embed(title, description):
    return Embed(title, description).danger_embed()


def success_embed(title, description):
    embed = Embed(title, description)
    embed.set_color(0x00FF00)
    return embed


class TeamManagementCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command()
    async def team(self, inter: disnake.GuildCommandInteraction):
        """Team management commands for owners, coaches, and staff"""
        pass

    @team.sub_command()
    async def set_owner(
        self,
        inter: disnake.GuildCommandInteraction,
        coach: disnake.Member,
        team: disnake.Role,
    ):
        """
        Assign a coach/owner to a team for transaction automation
        Parameters
        ----------
        coach: The coach or staff member to assign
        team: The team to assign them to
        """
        await inter.response.defer()

        has_admin = inter.author.guild_permissions.administrator
        if not has_admin:
            return await inter.send(
                embed=error_embed(
                    "Permission Denied",
                    "Only server administrators can assign team ownership",
                ),
                ephemeral=True,
            )

        is_team = await team_check(inter.guild.id, team)
        if not is_team:
            return await inter.send(
                embed=error_embed("Invalid Team", f"`{team.name}` is not a valid team"),
                ephemeral=True,
            )

        coach_mapping = await Database.get_data("CoachTeamMapping", inter.guild.id)
        if not coach_mapping:
            coach_mapping = {}
        elif not isinstance(coach_mapping, dict):
            return await inter.send(
                embed=error_embed(
                    "Database Error", "Invalid coach mapping data structure"
                ),
                ephemeral=True,
            )

        old_team_id = coach_mapping.get(str(coach.id))
        if old_team_id and str(old_team_id) == str(team.id):
            return await inter.send(
                embed=error_embed(
                    "Already Assigned",
                    f"{coach.mention} is already assigned to {team.mention}",
                ),
                ephemeral=True,
            )

        coach_mapping[str(coach.id)] = str(team.id)
        await Database.add_data("CoachTeamMapping", {inter.guild.id: coach_mapping})

        embed = success_embed(
            "Coach Assigned",
            f"{coach.mention} has been assigned to {team.mention}",
        )
        embed.add_field(
            name="Auto-Detection",
            value="This coach can now use `/offer`, `/release`, and `/demand` without specifying a team",
        )
        await inter.send(embed=embed)

    @team.sub_command()
    async def remove_owner(
        self,
        inter: disnake.GuildCommandInteraction,
        coach: disnake.Member,
    ):
        """
        Remove a coach/owner from team assignment
        Parameters
        ----------
        coach: The coach to remove from assignment
        """
        await inter.response.defer()

        has_admin = inter.author.guild_permissions.administrator
        if not has_admin:
            return await inter.send(
                embed=error_embed(
                    "Permission Denied",
                    "Only server administrators can remove team assignments",
                ),
                ephemeral=True,
            )

        coach_mapping = await Database.get_data("CoachTeamMapping", inter.guild.id)
        if not coach_mapping or not isinstance(coach_mapping, dict):
            return await inter.send(
                embed=error_embed(
                    "Not Assigned", f"{coach.mention} is not assigned to any team"
                ),
                ephemeral=True,
            )

        if str(coach.id) not in coach_mapping:
            return await inter.send(
                embed=error_embed(
                    "Not Assigned", f"{coach.mention} is not assigned to any team"
                ),
                ephemeral=True,
            )

        team_id = coach_mapping[str(coach.id)]
        team = inter.guild.get_role(int(team_id))
        team_mention = team.mention if team else f"Team (ID: {team_id})"

        del coach_mapping[str(coach.id)]
        await Database.add_data("CoachTeamMapping", {inter.guild.id: coach_mapping})

        embed = success_embed(
            "Coach Removed",
            f"{coach.mention} has been removed from {team_mention}",
        )
        await inter.send(embed=embed)

    @team.sub_command()
    async def info(
        self,
        inter: disnake.GuildCommandInteraction,
        team: disnake.Role,
    ):
        """
        Display team information, roster, and coaching staff
        Parameters
        ----------
        team: The team to get information about
        """
        await inter.response.defer()

        is_team = await team_check(inter.guild.id, team)
        if not is_team:
            return await inter.send(
                embed=error_embed("Invalid Team", f"`{team.name}` is not a valid team"),
                ephemeral=True,
            )

        team_members = await guild_members(inter.guild, team)
        team_coaches = await get_team_coaches(inter.guild, team)

        embed = Embed(
            title=f"{team.name} Information",
            description=f"Roster size: **{len(team_members)}** members",
        )
        embed.set_color(team.color)

        if team_coaches:
            coach_mentions = "\n".join([coach.mention for coach in team_coaches])
            embed.add_field(
                name=f"Coaches/Owners ({len(team_coaches)})",
                value=coach_mentions,
                inline=False,
            )

        if team_members:
            member_list = "\n".join([m.mention for m in team_members[:25]])
            if len(team_members) > 25:
                member_list += f"\n... and {len(team_members) - 25} more"
            embed.add_field(
                name=f"Roster ({len(team_members)})",
                value=member_list,
                inline=False,
            )

        await inter.send(embed=embed)

    @team.sub_command()
    async def list(self, inter: disnake.GuildCommandInteraction):
        """List all teams with their assigned coaches"""
        await inter.response.defer()

        team_data = await Database.get_data("TeamRole", inter.guild.id)
        if not team_data:
            return await inter.send(
                embed=error_embed("No Teams", "No teams have been set up yet"),
                ephemeral=True,
            )

        team_ids = team_data if isinstance(team_data, list) else list(team_data.values())
        coach_mapping = await Database.get_data("CoachTeamMapping", inter.guild.id)

        embed = Embed(
            title="Team Management List",
            description=f"Total teams: **{len(team_ids)}**",
        )

        for team_id in team_ids:
            team = inter.guild.get_role(int(team_id))
            if not team:
                continue

            coaches = []
            if coach_mapping and isinstance(coach_mapping, dict):
                for coach_id, assigned_team_id in coach_mapping.items():
                    if str(assigned_team_id) == str(team_id):
                        member = inter.guild.get_member(int(coach_id))
                        if member:
                            coaches.append(member.mention)

            team_members = await guild_members(inter.guild, team)
            coach_info = ", ".join(coaches) if coaches else "None assigned"

            embed.add_field(
                name=f"{team.name}",
                value=f"Coaches: {coach_info}\nRoster: {len(team_members)} members",
                inline=False,
            )

        await inter.send(embed=embed)

    @team.sub_command()
    async def check_assignment(
        self,
        inter: disnake.GuildCommandInteraction,
        coach: disnake.Member = None,
    ):
        """
        Check which team a coach is assigned to (admin only or self)
        Parameters
        ----------
        coach: The coach to check (leave empty to check yourself)
        """
        await inter.response.defer()

        target = coach or inter.author
        
        has_admin = inter.author.guild_permissions.administrator
        if coach and coach.id != inter.author.id and not has_admin:
            return await inter.send(
                embed=error_embed(
                    "Permission Denied",
                    "You can only check your own assignment unless you're an admin",
                ),
                ephemeral=True,
            )

        assigned_team = await get_coach_team(inter.guild.id, target)
        if not assigned_team:
            embed = Embed(
                title="Team Assignment",
                description=f"{target.mention} is not assigned to any team",
            )
            embed.set_color(0xFF9900)
            return await inter.send(embed=embed)

        embed = success_embed(
            "Team Assignment",
            f"{target.mention} is assigned to {assigned_team.mention}",
        )
        await inter.send(embed=embed)

    @commands.slash_command()
    async def channel(self, inter: disnake.GuildCommandInteraction):
        """Channel configuration commands for transaction types"""
        pass

    @channel.sub_command()
    async def set(
        self,
        inter: disnake.GuildCommandInteraction,
        channel_type: str,
        channel: disnake.TextChannel,
    ):
        """
        Set a channel for a command type
        Parameters
        ----------
        channel_type: The command type (Transactions, Offers, Demands, Trades, Pickups, etc)
        channel: The channel to configure
        """
        await inter.response.defer()

        has_admin = inter.author.guild_permissions.administrator
        if not has_admin:
            return await inter.send(
                embed=error_embed(
                    "Permission Denied",
                    "Only server administrators can configure channels",
                ),
                ephemeral=True,
            )

        success, message = await set_channel_config(inter.guild.id, channel_type, channel.id)
        if not success:
            return await inter.send(
                embed=error_embed("Configuration Failed", message),
                ephemeral=True,
            )

        embed = success_embed(
            "Channel Configured",
            f"{channel.mention} has been added to **{channel_type}** commands",
        )
        await inter.send(embed=embed)

    @channel.sub_command()
    async def remove(
        self,
        inter: disnake.GuildCommandInteraction,
        channel_type: str,
        channel: disnake.TextChannel,
    ):
        """
        Remove a channel from a command type
        Parameters
        ----------
        channel_type: The command type to remove the channel from
        channel: The channel to remove
        """
        await inter.response.defer()

        has_admin = inter.author.guild_permissions.administrator
        if not has_admin:
            return await inter.send(
                embed=error_embed(
                    "Permission Denied",
                    "Only server administrators can modify channel configurations",
                ),
                ephemeral=True,
            )

        success, message = await remove_channel_config(inter.guild.id, channel_type, channel.id)
        if not success:
            return await inter.send(
                embed=error_embed("Removal Failed", message),
                ephemeral=True,
            )

        embed = success_embed(
            "Channel Removed",
            f"{channel.mention} has been removed from **{channel_type}** commands",
        )
        await inter.send(embed=embed)

    @channel.sub_command()
    async def list(self, inter: disnake.GuildCommandInteraction):
        """List all configured channels by command type"""
        await inter.response.defer()

        all_config = await get_all_channel_config(inter.guild.id)
        if not all_config:
            return await inter.send(
                embed=error_embed("No Channels", "No channels have been configured yet"),
                ephemeral=True,
            )

        embed = Embed(
            title="Channel Configuration",
            description=f"Configured command types: **{len(all_config)}**",
        )

        for channel_type, channel_ids in all_config.items():
            if not isinstance(channel_ids, list):
                continue

            channels = []
            for ch_id in channel_ids:
                try:
                    ch = inter.guild.get_channel(int(ch_id))
                    if ch:
                        channels.append(ch.mention)
                except (ValueError, TypeError):
                    continue

            channel_info = ", ".join(channels) if channels else "No valid channels"
            embed.add_field(
                name=f"{channel_type}",
                value=channel_info,
                inline=False,
            )

        await inter.send(embed=embed)

    @channel.sub_command()
    async def clear(
        self,
        inter: disnake.GuildCommandInteraction,
        channel_type: str,
    ):
        """
        Clear all channels for a specific command type
        Parameters
        ----------
        channel_type: The command type to clear
        """
        await inter.response.defer()

        has_admin = inter.author.guild_permissions.administrator
        if not has_admin:
            return await inter.send(
                embed=error_embed(
                    "Permission Denied",
                    "Only server administrators can clear configurations",
                ),
                ephemeral=True,
            )

        all_config = await get_all_channel_config(inter.guild.id)
        if not all_config or channel_type not in all_config:
            return await inter.send(
                embed=error_embed("Not Found", f"No channels configured for **{channel_type}**"),
                ephemeral=True,
            )

        del all_config[channel_type]
        await Database.add_data("ChannelConfig", {inter.guild.id: all_config})

        embed = success_embed(
            "Channels Cleared",
            f"All channels for **{channel_type}** have been cleared",
        )
        await inter.send(embed=embed)


def setup(bot):
    bot.add_cog(TeamManagementCommands(bot))
