from typing import Union

import disnake
from disnake.ext import commands

from utils.embed import Embed

async def lock_channel(channel, role, author):
  overwrites = {role: disnake.PermissionOverwrite(send_messages=False)}
  await channel.edit(overwrites=overwrites, reason=f"Lock command ran by {author}")
          
async def unlock_channel(channel, role, author):
  if role in channel.overwrites:
    overwrites = channel.overwrites[role]
    overwrites.send_messages = True
    await channel.set_permissions(role, overwrite=overwrites, reason=f"Unlock command ran by {author}")
  else:
    overwrites = disnake.PermissionOverwrite(send_messages=True)
    await channel.set_permissions(role, overwrite=overwrites, reason=f"Unlock command ran by {author}")

class Confirm(disnake.ui.View):
    def __init__(self, inter):
        super().__init__(timeout=10.0)
        self.value = None
        self.inter = inter

    @disnake.ui.button(label="Confirm", style=disnake.ButtonStyle.green)
    async def confirm(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.send_message("Confirming...", ephemeral=True)
        self.value = True
        self.stop()

    @disnake.ui.button(label="Cancel", style=disnake.ButtonStyle.grey)
    async def cancel(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.send_message("Cancelling...", ephemeral=True)
        self.value = False
        self.stop()

    async def on_timeout(self):
        await self.inter.edit_original_message(
            view=None,
            content="Command has expired, run `/clearall` to use the command again",
        )

  
    async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
        if inter.author.id != self.inter.author.id:
            await inter.response.send_message("This is not your menu!", ephemeral=True)
            return False
        return True

class ModCommands(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  @commands.slash_command()
  @commands.bot_has_permissions(manage_channels=True)
  @commands.has_permissions(manage_channels=True)
  async def slowmode(
      self, 
      inter: disnake.GuildCommandInteraction, 
      channel: Union[disnake.TextChannel, disnake.Thread, disnake.ForumChannel, disnake.VoiceChannel] = None, 
      seconds: int = 0
    ):
        """Sets the slowmode of a channel, to turn it off run the command with no value
        Parameters
        ----------
        channel: The channel to put the slowmode on
        seconds: The amount of time the slowmode should be
        """
        if channel == None:
            channel = inter.channel
          
        if seconds > 120:
            return await inter.response.send_message("Amount can't be over 120 seconds", ephemeral=True)
          
        if seconds == 0:
            await channel.edit(slowmode_delay=seconds, reason=f"Slowmode command ran by {inter.author.name}")
            embed = Embed(title="Slowmode Off", description=f"Slowmode has been turned off in {channel.mention}")
            return await inter.response.send_message(embed=embed)
            
        else:
            await channel.edit(slowmode_delay=seconds, reason=f"Slowmode command ran by {inter.author.name}")
            embed = Embed(title="Slowmode On", description=f"Slowmode has been set to **{seconds} second(s)** in {channel.mention}, to turn this off, run the command without any value")
            return await inter.response.send_message(embed=embed)
  
  @commands.slash_command()
  @commands.has_permissions(manage_channels=True, manage_roles = True, manage_messages= True)
  @commands.bot_has_permissions(manage_channels=True, manage_roles=True)
  async def lock(
      self, 
      inter: disnake.GuildCommandInteraction, 
      channel: Union[disnake.TextChannel, disnake.Thread, disnake.ForumChannel, disnake.StageChannel, disnake.VoiceChannel, disnake.Thread] = None
  ):
        """Locks a channel, to unlock a channel run the command with no value
        Parameters
        ----------
        channel: The channel to lock or unlock    
        """
        channel = channel or inter.channel
        default_role = inter.guild.default_role
        is_locked = default_role not in channel.overwrites or channel.overwrites[default_role].send_messages is False
        
        if is_locked:
            await unlock_channel(channel, default_role, inter.author)
            embed_title = 'Channel Unlocked'
            embed_description = f"{channel.mention} has been unlocked"
        else:
            await lock_channel(channel, default_role, inter.author)
            embed_title = 'Channel Locked'
            embed_description = f"{channel.mention} has been locked"
        
        embed = Embed(title=embed_title, description=embed_description)
        await inter.response.send_message(embed=embed)

    
  @commands.slash_command()
  @commands.has_permissions(manage_channels=True)
  @commands.bot_has_guild_permissions(manage_channels=True)
  async def clearall(
      self, 
      inter: disnake.GuildCommandInteraction, 
      channel: Union[disnake.TextChannel, disnake.Thread, disnake.ForumChannel, disnake.StageChannel, disnake.VoiceChannel, disnake.Thread] = None
    ):  
          """Clears all the messages in a channel
          Parameters
          ----------
          channel: The channel to *nuke*   
          """  
          await inter.response.defer()
      
          if channel == None: channel = inter.channel

          view = Confirm(inter)
          confirm_message = await inter.channel.send(f"Are you sure you want to do this? This will delete **all** message in {channel.mention}", view=view)
          await view.wait()
      
          if view.value is None:
              return await confirm_message.edit("Timed out", ephemeral=True)
          if not view.value:  
              return await confirm_message.edit("Cancelled", ephemeral=True) 
            
          channel_name = f'{channel.name}'
          overwritess = channel.overwrites
          category = channel.category
          position = channel.position
          
          try:
            await channel.delete()
          except disnake.HTTPException:
            return await inter.response.send_message(f"Error with deleting the channel possible issues:\n1. {channel.mention} is a community channel (which aren't allow to be deleted)")
          new_channel = await inter.guild.create_text_channel(name=channel_name, overwrites=overwritess, category=category, position=position, reason=f"Clearall command ran by {inter.author} {inter.author.id}")
           
          embed = Embed(title='Channel Nuked', description=f"**{channel_name}** has been nuked, this message will disappear in 3 seconds")
          await new_channel.send(embed=embed, delete_after=3)
  
  @commands.slash_command()
  @commands.bot_has_permissions(manage_messages=True)
  @commands.has_permissions(manage_messages=True)
  async def clear(self, inter: disnake.GuildCommandInteraction, amount: int, member: disnake.Member = None):
        """Clears messages in a channel, won't delete pinned messages
        Parameters
        ----------
        amount: The amount of messages to delete  
        member: Deletes messages only from this person
        """
        def message_filter_non_pinned(m):
            return not m.pinned
    
        def message_filter_by_user(m):
            return m.author == member
    
        message_filter = message_filter_non_pinned if member is None else message_filter_by_user
        
        await inter.response.defer()
        deleted = await inter.channel.purge(limit=amount, check=message_filter)
        
        if member is None:
            description = f"**{len(deleted)}** messages have been deleted."
        else:
            description = f"**{len(deleted)}** messages from {member.mention} have been deleted."
        
        embed = Embed(
            title='Messages Purged',
            description=f"{description} This message will disappear in 3 seconds",
        )
        await inter.send(embed=embed, delete_after=3)

def setup(bot):
  bot.add_cog(ModCommands(bot))