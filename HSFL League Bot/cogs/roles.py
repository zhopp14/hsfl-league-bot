from datetime import datetime

import disnake
from disnake.ext import commands

from utils.config import FONTS_LIST, Links, vote_locked_message
from utils.embed import Embed
from utils.emojis import Emojis
from utils.tools import (adjust_hue, adjust_saturation, darken_color,
                         font_message, lighten_color, make_discord_message,
                         vote_or_premium_user)

ROLE_COMMANDS = {
    "NFL": {
        "Teams": 1057136078861123725,
    },
    "NBA": {
        "Teams": 1057136573063381043,
    },
    "MLB": {
        "Teams": 1057136476019769475,
    },
    "NHL": {
        "Teams": 1055313505311535205,
    },
    "College": {
        "ACC": 1075597096775860244,      
        "Big Ten": 1075593576689447007,
        "Big 12": 1075593621992116284,
        "Pac 12": 1075594992908763209,
        "SEC": 1075595045534695424,
        "More/Extra": 1075972521553317949,
    },
    "Other": {
        "Football Fusion": 1057137391661490287,
        "Ultimate Football": 1106985158424412200,
        "FCF": 1057137891131785327,
        "USFL": 1057137838149357628,
        "XFL": 1057137806331359262,
        "Soccer": 1094016748363198534,
    },
}

# make it where they can do divions and conferences
# make the embed color be random teams color

def generate_role_color_embed(inter: disnake.MessageInteraction, guild: disnake.Guild, settings: dict):
    test_roles = guild.roles[1:3]
    image_content = []

    for role in test_roles:
        color = adjust_color(str(role.color), settings)
        image_content.extend([
            {"content": f"@{role.name}", "color": color, "mention": True},
            {"content": "\u200b", "color": "#FFFFFF"}
        ])

    current_date = datetime.utcnow().strftime("%H:%M %p")
    timestamp = f"Today at {current_date}"

    font = settings.get("Font", "None")
    color_settings = " ".join(
        f"{key}: {value}" for key, value in settings.items() if key not in ("Color_Image", "Font")
    )

    image = make_discord_message(
        inter.author.name,
        inter.author.display_avatar.url,
        timestamp,
        image_content[:-1]  # Remove the last empty content
    )
  
    color_embed = Embed(
        title=f"{guild.name} Roles",
        description=f"**__Settings__**\n`Font:` {font}\n`Color:`",
        user=inter.author
    ).set_image(image).set_footer(text=color_settings)

    settings['Color_Image'] = image

    return color_embed

def adjust_color(hex_color: str, settings: dict):
    color = hex_color
    adjustment_functions = {
        "Lighter": lighten_color,
        "Darker": darken_color,
        "Saturation": adjust_saturation,
        "Hue": adjust_hue
    }
    
    for key, value in settings.items():
        if value and isinstance(value, (int, float)) and value > 0:
            if key in adjustment_functions:
                color = adjustment_functions[key](color, value)
            
    return color


async def roles_space_check(inter: disnake.MessageInteraction, role_guild: disnake.Guild) -> str:
    """Checks if you have enough space in your guild to add the roles"""
    guild_roles = len(inter.guild.roles) - 1
    roles_to_add = len(role_guild.roles)
    
    available_space = 250 - guild_roles
    if roles_to_add > available_space:
        roles_to_delete = roles_to_add - available_space
        return f"You are trying to add {roles_to_add} roles, but you only have {guild_roles} spaces, please delete **{roles_to_delete} roles**"

async def add_roles(inter: disnake.MessageInteraction, role_guild: disnake.Guild, settings: dict):
    """Add the roles"""

    for role in reversed(role_guild.roles[1:-3]):
      hex_color = adjust_color(str(role.color), settings)
      r = int(hex_color[1:3], 16)
      g = int(hex_color[3:5], 16)
      b = int(hex_color[5:7], 16)
      
      # Create a disnake.Colour object from the RGB values
      color = disnake.Colour.from_rgb(r, g, b)
      
      
      font = settings.get('Font', None)
      if font:
          name = await font_message(role.name, font)
      else:
          name = role.name

      await inter.guild.create_role(name = name, color=color, hoist=True)
      
async def roles_command(inter: disnake.MessageInteraction, role_guild: disnake.Guild, settings: dict):
    "Adds the functions above all together"
    role_space = await roles_space_check(inter, role_guild)
    if role_space:  # not enough space
        await inter.response.send_message(role_space, ephemeral=True)
      
    await inter.response.defer()
    embed = Embed(
        title=f"{role_guild.name} roles",
        description="Please wait while your roles are trying to be made",
        user=inter.author
    )
    await inter.edit_original_message(embed=embed)

    await add_roles(inter, role_guild, settings)
    embed = Embed(
        title=f"{role_guild.name} roles",
        description="The roles have been made",
        user=inter.author
    )
    await inter.edit_original_message(embed=embed)


class RoleSelectDropdownView(disnake.ui.View):
    def __init__(self, inter: disnake.MessageInteraction, bot):
        super().__init__()
        self.inter = inter
        self.bot = bot
        self.add_item(RoleSelect(bot))

    async def on_timeout(self):
        await self.inter.edit_original_message(
            view=None,
            content="Command has expired, run `/roles` to use the command again",
        )

    async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
        if inter.author.id != self.inter.author.id:
            await inter.response.send_message("This is not your menu!", ephemeral=True)
            return False
        return True

class RoleSelect(disnake.ui.StringSelect):
    """Role help menu dropdown view"""

    def __init__(self, bot):
        self.bot = bot
        options = [
            disnake.SelectOption(
                label="NFL",
                emoji=Emojis.nfl_logos[6],
            ),
            disnake.SelectOption(
                label="NBA",
                emoji=Emojis.nba_logos[4],
            ),
            disnake.SelectOption(
                label="MLB",
                emoji=Emojis.mlb_logos[2],
            ),
            disnake.SelectOption(
                label="NHL",
                emoji=Emojis.nhl_logos[2],
            ),
            disnake.SelectOption(
                label="College",
                emoji=Emojis.college_conferences[8],
            ),
            disnake.SelectOption(
                label="Other",
                emoji=Emojis.football_fusion[2],
            ),          
        ]

        super().__init__(
            placeholder="Pick the type of roles you want", options=options
        )

    async def callback(self, inter: disnake.MessageInteraction):

        #embed.set_image(url=EMOJI_COMMANDS[self.values[0]]["help_image"])
      
        league = ROLE_COMMANDS[self.values[0]]
        if len(league) > 1: # For things like College 
            embed = Embed(
                title = f"{self.values[0]} Roles",
                description = "Pick the roles you want",
                user=inter.author
            )
            await inter.response.edit_message(embed=embed, view=LeagueSelect(inter, league, bot=self.bot))
        else:
            id = league['Teams']
            guild = disnake.utils.get(inter.bot.guilds, id=int(id))
            embed = Embed(
                title = f"{self.values[0]} Roles",
                description = "**__Settings__**\n`Font:` None\n`Color:` Default",
                user=inter.author
            )          
            embed.set_footer(text="Click the Font and Color buttons to change the roles settings!")
            await inter.response.edit_message(embed=embed, view=RoleMenu(inter, guild, bot=self.bot))



class LeagueSelectButtons(disnake.ui.Button):
    def __init__(self, label: str, league: dict, bot):
        super().__init__(label=label)
        self.league = league
        self.bot = bot

    async def callback(self, inter: disnake.MessageInteraction):
        league = self.league[self.label]
        guild = disnake.utils.get(inter.bot.guilds, id=int(league))
      
        embed = Embed(
          title = f"{guild.name} Roles",
          description = "**__Settings__**\n`Font:` None\n`Color:` Default",
          user = inter.author      
        )
    
        await inter.response.edit_message(embed=embed, view=RoleMenu(inter, guild, bot=self.bot))
        

class LeagueSelect(disnake.ui.View):
    """For leagues that have more then one option, like college"""
    def __init__(self, inter: disnake.MessageInteraction, league: dict, bot):
        super().__init__()
        self.inter = inter
        self.league = league   
        self.bot = bot
        self.add_item(RoleSelect(bot))

        for name, _ in league.items():
            self.add_item(
                LeagueSelectButtons(label=name, league=league, bot=bot)
            )

    async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
        if inter.author.id != self.inter.author.id:
            await inter.response.send_message("This is not your menu!", ephemeral=True)
            return False
        return True


class RoleMenu(disnake.ui.View):
    def __init__(self, inter: disnake.MessageInteraction, guild: disnake.Guild, settings: dict = None, bot = None):
        # bot is just for the premium_user_check UGH
        super().__init__()
        self.inter = inter
        self.guild = guild 
        self.settings = {
            'Font': None,
            'Lighter': 0.0, 
            'Darker': 0.0,
            'Saturation': 0.0,
            'Hue': 0,
            'Color_Image': None,
        }

        if settings:
            self.settings.update(settings)

        self.bot = bot
      
        self.add_item(RoleSelect(bot))
      
    async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
        if inter.author.id != self.inter.author.id:
            await inter.response.send_message("This is not your menu!", ephemeral=True)
            return False
        return True


    @disnake.ui.button(label="Create Roles", style=disnake.ButtonStyle.green, row=1)
    async def create_roles_button(self, button, inter):
        await roles_command(inter, self.guild, self.settings)

    @disnake.ui.button(label="Color", row=1)
    async def color_button(self, button, inter):
        embed = generate_role_color_embed(inter, self.guild, self.settings)
        await inter.response.edit_message(view=RoleColor(inter, self.guild, self.settings, self.bot), embed=embed)

    @disnake.ui.button(label="Font", row=1)
    async def font_button(self, button, inter):
        await inter.response.edit_message(view = RoleFont(inter, self.guild, self.settings, self.bot))



class RoleColor(disnake.ui.View):
    def __init__(self, inter: disnake.MessageInteraction, guild: disnake.Guild, settings: dict, bot):
        super().__init__()
        self.inter = inter
        self.guild = guild
        self.settings = settings
        self.bot = bot

    async def _update_embed(self, inter):
        embed = generate_role_color_embed(self.inter, self.guild, self.settings)
        await inter.response.edit_message(embed=embed)

    async def _handle_access(self, inter):
        access = await vote_or_premium_user(self.bot, inter.author)
        if access:
          return access
        return await inter.send(vote_locked_message + f" or be a premium user {Links.premium_link}", ephemeral=True)
      

    @disnake.ui.button(label="Done Editing Color", style=disnake.ButtonStyle.green, row=0)
    async def done_button(self, button, inter):
        await inter.response.edit_message(view=RoleMenu(inter, self.guild, self.settings, self.bot))

    @disnake.ui.button(label="Reset Color", style=disnake.ButtonStyle.red, row=0)
    async def reset_button(self, button, inter):
        if await self._handle_access(inter):
            self.settings.update({"Lighter": 0.0, "Darker": 0.0, 'Saturation': 0.0, 'Hue': 0})
            await self._update_embed(inter)

    @disnake.ui.button(label="Make Lighter", row=1)
    async def lighter_button(self, button, inter):
        if await self._handle_access(inter):
            if self.settings['Lighter'] == 1.0:
                return await inter.response.send_message("You're at the lightest it can go", ephemeral=True)
            self.settings['Lighter'] += 0.2
            await self._update_embed(inter)

    @disnake.ui.button(label="Make Darker", row=1)
    async def darker_button(self, button, inter):
        if await self._handle_access(inter):
            if self.settings['Darker'] == 1.0:
                return await inter.response.send_message("You're at the darkest it can go", ephemeral=True)
            self.settings['Darker'] += 0.2
            await self._update_embed(inter)

    @disnake.ui.button(label="Add Saturation", row=2)
    async def add_saturation_button(self, button, inter):
        if await self._handle_access(inter):
            if self.settings['Saturation'] == 1.0:
                return await inter.response.send_message("Your at the max it can go", ephemeral=True)
            self.settings['Saturation'] += 0.2
            await self._update_embed(inter)

    @disnake.ui.button(label="Remove Saturation", row=2)
    async def remove_saturation_button(self, button, inter):
        if await self._handle_access(inter):
            if self.settings['Saturation'] == 0.0:
                return await inter.response.send_message("Your at the lowest it can go", ephemeral=True)
            self.settings['Saturation'] -= 0.2
            await self._update_embed(inter)

    @disnake.ui.button(label="Add Hue", row=3)
    async def add_hue_button(self, button, inter):
        if await self._handle_access(inter):
            if self.settings['Hue'] == 360:
                return await inter.response.send_message("Your at the max it can go", ephemeral=True)
            self.settings['Hue'] += 20
            await self._update_embed(inter)
  
    @disnake.ui.button(label="Remove Hue", row=3)
    async def remove_hue_button(self, button, inter):
        if await self._handle_access(inter):
            if self.settings['Hue'] == 9:
                return await inter.response.send_message("Your at the lowest it can go", ephemeral=True)
            self.settings['Hue'] -= 20
            await self._update_embed(inter)


class RoleFontButtons(disnake.ui.Button):
    def __init__(self, label: str, guild: disnake.Guild, settings: dict, bot):
        self.guild = guild
        self.settings = settings
        self.bot = bot
        super().__init__(label=label)

    async def callback(self, inter: disnake.MessageInteraction):
        access = await vote_or_premium_user(self.bot, inter.author)
        if not access:
          return await inter.response.send_messag(vote_locked_message + f" or be a premium user {Links.premium_link}", ephemeral=True)
      
        self.settings['Font'] = self.label
      
        embed = Embed(
          title = f"{self.guild.name} Roles",
          user = inter.author      
        )

        image = self.settings['Color_Image']
        if image:
            embed.set_image(image)
            embed.description = f"**__Settings__**\n`Font:` {self.label}\n`Color:`"
        else:
            embed.description = f"**__Settings__**\n`Font:` {self.label}\n`Color:` Default"
    
        await inter.response.edit_message(embed=embed, view=RoleMenu(inter, self.guild, self.settings, self.bot))
        

class RoleFont(disnake.ui.View):
    def __init__(self, inter: disnake.MessageInteraction, guild: disnake.Guild, settings: dict, bot):
        super().__init__()
        self.inter = inter
        self.guild = guild
        self.settings = settings
        self.bot = bot
        self.add_item(RoleSelect(bot))

        for font in FONTS_LIST:
            self.add_item(
                RoleFontButtons(label=font, guild=guild, settings=settings, bot=bot)
            )

    async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
        if inter.author.id != self.inter.author.id:
            await inter.response.send_message("This is not your menu!", ephemeral=True)
            return False
        return True


class RolesCommands(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  @commands.slash_command()
  @commands.cooldown(1, 20, commands.BucketType.user)
  @commands.bot_has_permissions(manage_roles=True)
  @commands.has_permissions(manage_roles=True)  
  async def roles(self, inter: disnake.GuildCommandInteraction):
    """Add league roles to your server with the Role Menu\u2122""" # tm logo
    embed = Embed(
        title="Roles Menu",
        description="Pick the type of roles you want",
        user=inter.author
    )
    await inter.response.send_message(embed=embed, view=RoleSelectDropdownView(inter, self.bot))



def setup(bot):
  bot.add_cog(RolesCommands(bot))