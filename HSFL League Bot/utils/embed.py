from typing import Union

import disnake
#import random

from utils.config import Images, BotEmojis, Colors

# error message embeds
      
class Embed(disnake.Embed):
    def __init__(
      self, 
      # Embed parts
      title: str = None,
      description: str = None,
      url: str = None,
      timestamp = None, #datetime.datetime
      color: disnake.Colour = None,

      guild: disnake.Guild = None,
      user: Union[disnake.User, disnake.Member] = None,
      role: disnake.Role = None
    ):
        super().__init__(title=title, description=description, url=url, timestamp=timestamp)
        self.timestamp = disnake.utils.utcnow()
      
        if color:
          self.color = color
        else:
          self.color = self._embed_color(guild)

        if user:
          self._user_footer(user)

    def _embed_color(self, guild = None):
        """If a color is not set, then set one"""
        if guild:
          color = guild.me.color or None
          color = disnake.Embed.get_default_color() if color == disnake.Color.default() else color
        else:
          color = disnake.Embed.get_default_color()
        return color

    def _user_footer(self, user):
      user_avatar = user.display_avatar.url or Images.bot_logo
      self.set_footer(text = user.display_name, icon_url = user_avatar)

    def quick_embed(self, title, description):
      self.title = title
      self.description = description
      return self
  
    def success_embed(self):
      #self.title = f"{self.title}"
      self.color = Colors.green
      return self

    def loading_embed(self):
      #self.title = f"{self.title}"
      self.color = Colors.light_blue
      return self
  
    def question_embed(self):
      #self.title = f"{self.title}"
      self.color = Colors.blue
      return self
  
    def info_embed(self):
      #self.title = f"{self.title}"
      self.color = Colors.green
      return self
  
    def warn_embed(self):
      #self.title = f"{self.title}"
      self.color = Colors.yellow
      return self
  
    def danger_embed(self):
      #self.set_thumbnail(url=Images.prohibited)
      self.title = f"{BotEmojis.prohibited} {self.title}"
      self.color = Colors.red
      return self
  
    async def league_embed(self, guild, user, role):
      from utils.tools import search_role_emoji
      author_icon = guild.icon or Images.bot_logo
      team_emoji = await search_role_emoji(guild, role.name)
      thumbnail = team_emoji.url if team_emoji else author_icon

      self.set_author(name = f"{guild.name} Transactions", icon_url=author_icon)
      self.set_thumbnail(url=thumbnail)
      self.color = role.color or self._embed_color(guild)
      self.set_footer = self._user_footer(user) 