from collections import defaultdict
from textwrap import shorten

import disnake
from disnake.ext import commands

from utils.database import Database
from utils.embed import Embed


class SnipeCommands(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.delsniped = defaultdict(lambda: defaultdict(dict))
    self.editsniped = defaultdict(lambda: defaultdict(dict))

  @commands.Cog.listener()
  async def on_message_delete(self, message: disnake.Message):
    try:
      file_attachment = message.attachments[0].proxy_url
      attachment_name = message.attachments[0].filename
    except IndexError:
      file_attachment = None
      attachment_name = None

    self.delsniped[message.channel.id] = {
      "author": message.author.name,
      "avatar_url": message.author.display_avatar,
      "content": message.content,
      "attachments": file_attachment,
      "file_name": attachment_name,
    }

    for member in message.mentions:
      gp_data = await Database.get_data('GhostPing', message.guild.id)
      # No data or not "Off" means on
      if gp_data != "Off" and not message.author.bot:
        content = message.content if message.content else "No Message"
        if len(content) > 768:
            content = shorten(content, width=756, placeholder="...") 

            embed = Embed(
              color=message.author.color,
              title="<:ghostping:782060673730740275> Ghost Ping Found <:ghostping:782060673730740275>",
            )
            embed.add_field(name="Pinged By", value=message.author.mention)
            embed.set_footer(text="To turn this off use /setup")
            embed.add_field(name="Content", value=content)
            try:
              await message.channel.send(embed=embed)
            except (disnake.Forbidden, disnake.HTTPException):
              return

  @commands.Cog.listener()
  async def on_raw_reaction_remove(self, payload: disnake.RawReactionActionEvent):
    try:
      channel = self.bot.get_channel(payload.channel_id)
      message = await channel.fetch_message(payload.message_id)
    except Exception:
      return
      
    self.delsniped[message.channel.id] = {
      "author": message.author.name,
      "avatar_url": message.author.display_avatar,
      "content": message.content,
      "reaction": payload.emoji,
    }

  @commands.Cog.listener()
  async def on_message_edit(self, before: disnake.Message, after: disnake.Message):
    try:
      bf_file_attachment = before.attachments[0].proxy_url
      bf_attachment_name = before.attachments[0].filename
    except IndexError:
      bf_file_attachment = None
      bf_attachment_name = None

    try:
      af_file_attachment = after.attachments[0].proxy_url
      af_attachment_name = after.attachments[0].filename
    except IndexError:
      af_file_attachment = None
      af_attachment_name = None

    self.editsniped[before.channel.id] = {
      "author": before.author.name,
      "avatar_url": before.author.display_avatar,
      # Before
      "bf_content": before.content or "No content",
      "bf_attachments": bf_file_attachment,
      "bf_file_name": bf_attachment_name,
      # After
      "af_content": after.content or "No content",
      "af_attachments": af_file_attachment,
      "af_file_name": af_attachment_name,
    }
    
    if before.type == disnake.MessageType.reply:
      return 
    
    for member in before.mentions:
      if str(member.id) in after.content:
        return

      gp_data = await Database.get_data('GhostPing', before.guild.id)
      # No data or not "Off" means on
      if gp_data != "Off" and not before.author.bot:
        content = before.content if before.content else "No Message"
        if len(content) > 768:
          content = shorten(content, width=756, placeholder="...")  

        embed = Embed(
          color=before.author.color,
          title="<:ghostping:782060673730740275> Edited Ghost Ping Found <:ghostping:782060673730740275>",
        )
        embed.add_field(name="Pinged By", value=before.author.mention)
        embed.set_footer(text="To turn this off use /setup")
        embed.add_field(name="Content", value=content)
        try:
          await before.channel.send(embed=embed)
        except (disnake.Forbidden, disnake.HTTPException):
          return

  @commands.slash_command()
  async def snipe(
    self,
    inter: disnake.GuildCommandInteraction,
    channel: disnake.TextChannel = None,
    ):
      """*Snipe* the last deleted message or reaction in a channel"""
      if not channel: channel = inter.channel

      snipe = self.delsniped.get(channel.id, {})
      if not snipe:
        return await inter.response.send_message("There's nothing to snipe!", ephemeral=True)

      # Text
      content = snipe["content"]
      if len(content) > 768:
        content = shorten(content, width=756, placeholder="...")

      embed = Embed(
        title=f"Message Sniped - {channel.name}",
        description=content,
        color=inter.author.color,
      )
      embed.set_author(name=snipe["author"], icon_url=snipe["avatar_url"])

      # Image
      attachment = snipe.get("attachments")
      file_name = snipe.get("file_name")
      if attachment:
        embed.add_field(
          name="Attachments", value=f"||[{file_name}]({attachment})||"
        )

      # Reaction
      if snipe.get("reaction"):
        embed.add_field(name="Reaction", value=snipe["reaction"])

      await inter.response.send_message(embed=embed)

  @commands.slash_command()
  async def editsnipe(
    self,
    inter: disnake.GuildCommandInteraction,
    channel: disnake.TextChannel = None,
  ):
    """*Snipe* the last message someone edited"""
    try:
      if not channel: 
        channel = inter.channel

      snipe = self.editsniped.get(channel.id, {})
      if not snipe:
        return await inter.response.send_message("There's nothing to snipe! No messages have been edited in this channel.", ephemeral=True)

      # Get content with defaults
      bf_content = snipe.get("bf_content", "No content")
      af_content = snipe.get("af_content", "No content")

      if len(bf_content) > 768:
        bf_content = shorten(bf_content, width=756, placeholder="...")
      if len(af_content) > 768:
        af_content = shorten(af_content, width=756, placeholder="...")

      embed = Embed(
        title=f"Message Edit Sniped - {channel.name}", 
        color=inter.author.color
      )
      embed.set_author(name=snipe.get("author", "Unknown"), icon_url=snipe.get("avatar_url"))
      embed.add_field(name="Before", value=bf_content, inline=False)
      embed.add_field(name="After", value=af_content, inline=False)

      # Image attachments
      bf_attachment = snipe.get("bf_attachments")
      bf_file_name = snipe.get("bf_file_name")

      af_attachment = snipe.get("af_attachments")
      af_file_name = snipe.get("af_file_name")
      
      if bf_attachment:
        embed.add_field(
          name="Before Attachment",
          value=f"||[{bf_file_name}]({bf_attachment})||",
          inline=False,
        )
      if af_attachment:
        embed.add_field(
          name="After Attachment", 
          value=f"||[{af_file_name}]({af_attachment})||",
          inline=False
        )

      await inter.response.send_message(embed=embed)
    except Exception as e:
      import traceback
      traceback.print_exc()
      try:
        await inter.response.send_message(f"Error: {str(e)}", ephemeral=True)
      except Exception:
        await inter.send(f"Error: {str(e)}", ephemeral=True)



def setup(bot):
  bot.add_cog(SnipeCommands(bot))