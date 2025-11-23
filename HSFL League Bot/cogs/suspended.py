from datetime import datetime

import disnake
from disnake.ext import commands, tasks

from utils.config import not_premium_message
from utils.database import Database
from utils.embed import Embed
from utils.signing_tools import send_notfication_channel
from utils.tools import parse_duration, premium_guild_check


async def suspension_duration(duration):
    duration = await parse_duration(duration)
    duration = duration + datetime.now()
    d_str = str(duration)

    find_miliseconds = d_str.find(".")
    if find_miliseconds != -1:
        d_str = d_str[:find_miliseconds]

    return d_str

async def handle_suspension_role(member, action):
  suspension_role = await Database.get_data("SuspensionRole", member.guild.id)
  if suspension_role is None:
    return
  
  # Handle both list and dict formats
  if isinstance(suspension_role, list):
    role_ids = suspension_role
  elif isinstance(suspension_role, dict):
    role_ids = suspension_role.values()
  else:
    return
  
  for role_id in role_ids:
    try:
      role = member.guild.get_role(int(role_id))
      if role:
        if action == "add":
          await member.add_roles(role)
        elif action == "remove":
          await member.remove_roles(role)
    except (ValueError, TypeError, Exception) as e:
      print(f"Error handling suspension role {role_id}: {e}")
      continue

async def send_embed_to_member(member, embed):
  try:
    await member.send(
      content=f"**You have been suspended in {member.guild.name}, here is the message they sent**",
      embed=embed,
    )
  except Exception:
    pass

class SuspenedCommands(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  @tasks.loop(minutes=5)
  async def suspend_check(self):
    await self.bot.wait_until_ready()
    suspension_data = await Database.get_data("Suspensions")
    if suspension_data is None or not isinstance(suspension_data, dict):
      return

    for guild_id, user_id in suspension_data.items():
      if not isinstance(user_id, dict):
        continue
      for user_id_, user_data in user_id.items():
        current_time = datetime.now()
        duration = user_data["duration"]
        if duration == "Permanently":
          continue
          duration = datetime.fromisoformat(duration)

          if current_time >= duration:
            await Database.delete_data(
              "Suspensions", f"{int(guild_id)}/{int(user_id_)}"
            )

            guild = self.bot.get_guild(int(guild_id))
            member = await guild.get_or_fetch_member(int(user_id_))

            embed = Embed(
              title="Player Unsuspended",
              description=f"**{member.mention} has been unsuspended**\n`Suspension Reason:` {user_data['reason']}\n`Unsuspended Reason:` Serverd your time",
            )
            embed.set_thumbnail(member.display_avatar)

            await send_notfication_channel(guild, embed)
            await handle_suspension_role(member, "remove")

            await send_embed_to_member(member, embed)

            break
  
  @commands.slash_command()
  @commands.has_permissions(manage_roles=True)
  async def suspend(
    self,
    inter: disnake.GuildCommandInteraction,
    member: disnake.Member,
    duration: str = "Permanently",
    reason: str = None,
    bail: str = None,
    send_suspend_embed_to_user: bool = True,
  ):
    """
    Suspened a user, they won't be able to get signed
    Parameters
    ----------
    member: The player to suspend
    duration: How to they are suspended, put nothing for a permanet suspension
    reason: The reason they are getting suspended
    bail: If there is a bail, like 1 dollar to get unsuspended quicker
    """
    p_check = await premium_guild_check(inter.guild.id)
    if not p_check:
      return await inter.response.send_message(not_premium_message, ephemeral=True)
      
    if not duration == "Permanently":
      duration = await suspension_duration(duration)
      duration = duration[:10]

    await Database.add_data(
      "Suspensions",
        {
          inter.guild.id: {
          member.id: {"reason": reason, "bail": bail, "duration": duration}
          }
        },
    )

    embed = Embed(
      title="Player Suspended",
      description=f"**{member.mention} has been suspended**\n`Suspended till:` **{duration}**\n`Reason:` {reason}\n`Bail:` {bail}",
    )
    embed.set_thumbnail(inter.guild.icon)
    await inter.response.send_message(embed=embed)

    if send_suspend_embed_to_user:
      await send_embed_to_member(member, embed)

    await handle_suspension_role(member, "add")
    await send_notfication_channel(inter.guild, embed)

  
  @commands.slash_command()
  async def unsuspend(
    self,
    inter: disnake.GuildCommandInteraction,
    member: disnake.Member,
    reason: str = None,
  ):
    """
    Unsuspened a user
    Parameters
    ----------
    member: The player to unsuspend
    reason: The reason they are getting unsuspended
    """
    p_check = await premium_guild_check(inter.guild.id)
    if not p_check:
      return await inter.response.send_message(not_premium_message, ephemeral=True)
      
    suspension_data = await Database.get_data("Suspensions", f"{inter.guild.id}/{member.id}")
    if suspension_data is None:
      return await inter.response.send_message("That user is not suspended", ephemeral=True)
    
    if not isinstance(suspension_data, dict):
      return await inter.response.send_message("Invalid suspension data", ephemeral=True)

    await Database.delete_data("Suspensions", f"{inter.guild.id}/{member.id}")
    embed = Embed(
        title="Player Unsuspended",
        description=f"**{member.mention} has been unsuspended**\n`Suspension Reason:` {suspension_data['reason']}\n`Unsuspended Reason:` {reason}",
      )
    embed.set_thumbnail(member.display_avatar)

    await inter.response.send_message(embed=embed)

    await handle_suspension_role(member, "remove")
    await send_notfication_channel(inter.guild, embed)

    await send_embed_to_member(member, embed)


def setup(bot):
  bot.add_cog(SuspenedCommands(bot))