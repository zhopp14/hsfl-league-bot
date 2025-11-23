import aiohttp
import disnake
from disnake.ext import commands, tasks

from utils.embed import Embed
from utils.config import Ids, welcome_message, SETTINGS, error_support_message
from utils.database import Database
from utils.tools import premium_user_check, remove_all_premium_data, premium_guild_check, has_role, remove_all_guild_data
from utils.signing_tools import suspension_check, send_notfication_channel, auto_setup, auto_add_object

async def notify_premium_member_leave(member: disnake.Member):
    message = (
        "Hey there, \n\n"
        "We noticed that you have left the Bread Kindom Server. It looks like you were part of our Premium community. We wanted to let you know that as a premium member, you were enjoying special benefits. **Unfortunately, leaving the server means you'll lose those benefits.**\n\n"
        "If you ever decide to come back, **just rejoin the server and ping doggysoggy. We'd be more than happy to help you regain your premium perks.**\n\n"
        "Thanks for being a part of our community, and sorry for any inconvenience. If you have any questions or concerns, feel free to reach out.\n\n"
        "Best regards,\n"
        "Bread Winner B"
    )
    embed = Embed(title='Losing Premium Benefits', description=message).warn_embed()
    await member.send(embed=embed)
    await remove_all_premium_data(member)


async def handle_coach_leave(member: disnake.Member):
    coach_check = await has_role('FranchiseRole', member.guild.id, member)
    if coach_check:
        team_role = await has_role("TeamRole", member.guild.id, member, 'id')
        if team_role:
            team = member.guild.get_role(int(team_role))
            embed = Embed(title="Franchise Coach has Left", description=f"{member.mention} `{member.display_name}`, a coach of the {team.mention} has left the server")
            await embed.league_embed(guild=member.guild, user=member, role=team)
            await send_notfication_channel(member.guild, embed)


async def handle_suspended_user_leave(member: disnake.Member):
    s_check = await suspension_check(member.guild.id, member)
    if s_check[0]:
        embed = Embed(
            title="Suspended User Left 😂",
            description=f"{member.mention} `{member.display_name}` who is currently suspended has left the server",
        )
        await send_notfication_channel(member.guild, embed)


async def delete_object_data(guild_id, object_id):
  for value in SETTINGS.values():
    data = await Database.get_data(value['table'], guild_id)
    if data is None:
      continue
      
    table = value['table']
    if isinstance(data, dict):
      for sub_key, sub_value in data.items():  
        if isinstance(sub_value, dict):
          for sub_sub_key, sub_sub_value in sub_value.items():
            if str(object_id) == str(sub_sub_value):
              await Database.delete_data(table, f"{guild_id}/{sub_key}/{sub_sub_key}")
        elif isinstance(sub_value, list): 
          for item in sub_value:
            if str(object_id) == str(item):
              await Database.delete_data(table, f"{guild_id}/{sub_key}/{item}")  
        else:
            if str(object_id) == str(sub_value):
              await Database.delete_data(table, f"{guild_id}/{sub_key}")
              
    elif isinstance(data, list):
      for item in data:
        if str(object_id) == str(item):
          await Database.delete_data(table, f"{guild_id}/{item}")
          
    else:
      await Database.delete_data(table, guild_id)


class Events(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    
  @commands.Cog.listener()
  async def on_member_remove(self, member: disnake.Member):
      bk_guild = self.bot.get_guild(Ids.bk_server)
      if member.guild == bk_guild:
          premium_role = disnake.utils.get(bk_guild.roles, id=Ids.premium_role)
          if premium_role in member.roles: 
              await notify_premium_member_leave(member)
  
      p_check = await premium_guild_check(member.guild.id)
      if not p_check:
          return
      
      await handle_coach_leave(member)
      await handle_suspended_user_leave(member)

      
      # log when a player on a team leaves, ping coaches?
  
  # log when a user switches team
  @commands.Cog.listener()
  async def on_member_update(self, before: disnake.Member, after: disnake.Member):
    bk_guild = self.bot.get_guild(Ids.bk_server)
    if before.guild == bk_guild:
      premium = await premium_user_check(self.bot, after)
      if not premium:
        await remove_all_premium_data(after)

  @commands.Cog.listener()
  async def on_guild_join(self, guild: disnake.Guild):
    # Welcome message, AutoSetup for Signing
    setup_embed = await auto_setup(guild)

    for channel in guild.text_channels:
      if (
          channel.permissions_for(guild.me).send_messages and                      channel.permissions_for(guild.me).embed_links
      ):
        await channel.send(welcome_message)
        if setup_embed:
          await channel.send(embed = setup_embed)
          break


  @commands.Cog.listener()
  async def on_guild_remove(self, guild: disnake.Guild):
    await remove_all_guild_data(guild.id)

   # check who made/delete a role or channel
  @commands.Cog.listener() # not really needed
  async def on_guild_role_create(self, role: disnake.Role):
    embed = await auto_add_object(role)
    if embed:
      await send_notfication_channel(role.guild, embed)

  @commands.Cog.listener()
  async def on_guild_role_update(self, before: disnake.Role, after: disnake.Role):
    embed = await auto_add_object(after)
    if embed:
      await send_notfication_channel(after.guild, embed)

  @commands.Cog.listener()
  async def on_guild_role_delete(self, role: disnake.Role):
    await delete_object_data(role.guild.id, role.id)
    # log?

  @commands.Cog.listener()
  async def on_guild_channel_create(self, channel: disnake.abc.GuildChannel):
    if channel.type.name in ['voice', 'stage', 'forum']:
      return
    embed = await auto_add_object(channel)
    if embed:
      await send_notfication_channel(channel.guild, embed)

  @commands.Cog.listener()
  async def on_guild_channel_update(self, before: disnake.abc.GuildChannel, after: disnake.abc.GuildChannel):
    if before.type.name in ['voice', 'stage', 'forum']:
      return
    embed = await auto_add_object(after)
    if embed:
      await send_notfication_channel(after.guild, embed)

  @commands.Cog.listener()
  async def on_guild_channel_delete(self, channel: disnake.abc.GuildChannel):
    await delete_object_data(channel.guild.id, channel.id)
    # log

  @commands.Cog.listener()
  async def on_thread_delete(self, thread: disnake.Thread):
    await delete_object_data(thread.guild.id, thread.id)
    # log
  
  @commands.Cog.listener()
  async def on_slash_command_error(
    self,
    inter: disnake.ApplicationCommandInteraction,
    error: disnake.ext.commands.CommandError,
  ):
    if isinstance(error, commands.errors.CommandOnCooldown):
      if await inter.bot.is_owner(inter.author):
          return inter.application_command.reset_cooldown(inter)
      seconds = error.retry_after
      m, s = divmod(seconds, 60)
      h, m = divmod(m, 60)
      d, h = divmod(h, 24)
      embed = Embed(
        title = "Command on Cooldown",
        description = f"You have to wait **{int(h)} hours, {int(m)} minutes and {int(s)} seconds** to use this command again",
      ).loading_embed()
      return await inter.response.send_message(embed=embed, content = error_support_message, ephemeral=True)

    elif isinstance(error, commands.errors.MissingPermissions):
        missing = [
          perm.replace("_", " ").replace("guild", "server").title()
          for perm in error.missing_permissions
        ]
        if len(missing) > 2:
          fmt = "{}, and {}".format("**, **".join(missing[:-1]), missing[-1])
          _message = ("You need the **{}** permission(s) to run this command".format(fmt))
        else:
          fmt = " and ".join(missing)
          _message = ("You need the **{}** permission(s) to run this command".format(fmt))

        embed = Embed(
          title = "Missing Permissions",
          description = f"{_message}",
        ).danger_embed()

        return await inter.response.send_message(embed = embed, content = error_support_message, ephemeral = True)


    elif isinstance(error, commands.errors.BotMissingPermissions):
        missing = [
          perm.replace("_", " ").replace("guild", "server").title()
          for perm in error.missing_permissions
        ]
        if len(missing) > 2:
          fmt = "{}, and {}".format("**, **".join(missing[:-1]), missing[-1])
          _message = ("I need the **{}** permission(s) to run this command".format(fmt))
        else:
          fmt = " and ".join(missing)
          _message = ("I need the **{}** permission(s) to run this command".format(fmt))

        embed = Embed(
          title = "Missing Permissions",
          description = f"{_message}",
        ).danger_embed()
        embed.set_footer(text = "The bot needs these permissions") 
       # some people have gotten confused

        return await inter.response.send_message(embed = embed, content = error_support_message, ephemeral = True)

    elif isinstance(error, commands.errors.NotOwner):
        return await inter.response.send_message(f"Only the one Mr.Doggy Soggy can use these commands \n {error_support_message}", ephemeral = True,)
    elif isinstance(error, commands.errors.CommandNotFound):
        return


def setup(bot):
  bot.add_cog(Events(bot))