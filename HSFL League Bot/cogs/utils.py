import random
from typing import Optional, Union

import disnake
from disnake.ext import commands

from utils.config import Links, error_support_message
from utils.embed import Embed


class AvatarLinks(disnake.ui.View):
  def __init__(self, member):
    super().__init__()
    self.member = member

    png_link = self.member.display_avatar.with_format('png').url
    jpg_link = self.member.display_avatar.with_format('jpg').url
    webp_link = self.member.display_avatar.with_format('webp').url
    
    self.add_item(disnake.ui.Button(label='PNG', url=png_link, emoji='🔗')) 
    self.add_item(disnake.ui.Button(label='JPG', url=jpg_link, emoji='🔗'))
    self.add_item(disnake.ui.Button(label='WEBP', url=webp_link, emoji='🔗'))


class UtilsCommands(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  @commands.slash_command()
  async def premium(self, inter):
    await inter.response.send_message(f"{Links.premium_link}")

  @commands.slash_command()
  async def helpsigning(self, inter: disnake.ApplicationCommandInteraction):
    """Shows you how to setup the signing system"""
    signing_video = Links.signing_video
    await inter.response.send_message(f"Try watching this video: **{signing_video}**\n\n{error_support_message}")
      
  @commands.slash_command()
  async def avatar(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member = None):
    """
    Shows your ugly profile picture
    Parameters
    ----------
    member: The member to get the avatar from
    """
    if member == None: member = inter.author
          
    embed = Embed(title=f"{member.display_name}", color=member.color, user=inter.author)
    embed.set_image(url=member.display_avatar)
    embed.set_footer(text=f"I rate your avatar {random.randint(1, 10)}/10")
    await inter.response.send_message(embed=embed, view=AvatarLinks(member))

  @commands.slash_command()
  async def membercount(self, inter: disnake.GuildCommandInteraction):
    """Shows how many people are in a server, includes bots"""
    guild = inter.guild
    count = guild.member_count
    embed = Embed(
      title="Membercount",
      description=f"{guild.name} member count is **{count}**",
      guild=guild,
      user=inter.author
    )
    embed.set_thumbnail(url=guild.icon)
    await inter.response.send_message(embed=embed)

def setup(bot):
  bot.add_cog(UtilsCommands(bot))