import asyncio

import aiohttp
import disnake
from disnake.ext import commands

from utils.config import Links
from utils.embed import Embed
from utils.emojis import Emojis

# Number is a discord server id
EMOJI_COMMANDS = {
    "NFL": {
        "help_image": "https://breadwinner.dev/images/nfl_emoji_help.png",
        "emoji": Emojis.nfl_logos[6],
        "description": "Teams, neon teams, and logos",
        "Normal": 1057136078861123725,
        "Neon": 1057137537656827924,
        "Neon2": 1057137611040378891,
        "Helmet": 1057137691621331004,
        "3d": 1057136419371491428,
        "Logos": 1057136290044313640,
    },
    "NBA": {
        "help_image": "https://breadwinner.dev/images/nba_emoji_help.png",
        "emoji": Emojis.nba_logos[4],
        "description": "Teams and logos",
        "Teams": 1057136573063381043,
        "Logos": 1057136623478919238,
    },
    "MLB": {
        "help_image": "https://breadwinner.dev/images/mlb_emoji_help.png",
        "emoji": Emojis.mlb_logos[2],
        "description": "Teams and logos",
        "Teams": 1057136476019769475,
        "Logos": 1057136517174284438,
    },
    "NHL": {
        "help_image": "https://breadwinner.dev/images/nhl_emoji_help.png",
        "emoji": Emojis.nhl_logos[2],
        "description": "Teams and logos",
        "Teams": 1055313505311535205,
        "Logos": 1057128362763636899,
    },
    "College": {
        "help_image": "https://breadwinner.dev/images/college_emoji_help.png",
        "emoji": Emojis.college_conferences[8],
        "description": "Teams, neon teams, and logos",
        # Normal
        "ACC": 1075597096775860244,
        "Big Ten": 1075593576689447007,
        "Big 12": 1075593621992116284,
        "Pac 12": 1075594992908763209,
        "SEC": 1075595045534695424,
        "More/Extra": 1057136623478919238,
        # Neon
        "Neon ACC": 1075911596720791632,
        "Neon Big Ten": 1075911742837760183,
        "Neon Big 12": 1075911781299527712,
        "Neon Pac 12": 1075919474059923506,
        "Neon SEC": 1075919528636207114,
        "Neon More/Extra": 1075971807615656058,
        # Logos
        "Bowls": 1095022877939617862,
        "Conferences": 1095023012471914678,
        "Helmet": 1057137773762576476,
    },
    "Other": {
        "help_image": "https://breadwinner.dev/images/other_leagues_emoji_help.png",
        "emoji": Emojis.football_fusion[2],
        "description": "Football Fusion, Ultimate Football, XFL, etc.",
        "Football Fusion": 1057137391661490287,
        "Ultimate Football": 1106985158424412200,
        "FCF": 1057137891131785327,
        "USFL": 1057137838149357628,
        "XFL": 1057137806331359262,
        "Soccer": 1094016748363198534,
    },
    "Media": {
        "help_image": "https://breadwinner.dev/images/media_emoji_help.png",
        "emoji": Emojis.social_media[0],
        "description": "Social Media, Devtraits, Divisons, etc.",
        "Departments": 1095010658682142772,
        "Devtraits": 1057137491292979200,
        "Divisons": 1095010782196007043,
        "General Symbols": 1057137422351220827,
        "General Symbols Neon": 1057137456979390526,
        "Numbers": 1095010945941639259,
        "Rings": 1095010856581996656,
        "Social Media": 1057137574696714281,
        "Stars": 1095011069262577756,
    },
}


async def emoji_space_check(
    inter: disnake.MessageInteraction, emoji_guild: disnake.Guild
) -> str:
    """Checks if your server has enough emoji spaces to run the command"""
    emoji_count = sum(1 for emoji in inter.guild.emojis if not emoji.animated)
    emoji_limit = inter.guild.emoji_limit

    available_space = emoji_limit - emoji_count
    required_space = len(emoji_guild.emojis)

    if available_space < required_space:
        emojis_to_delete = required_space - available_space
        return (
            f"This command needs {required_space} emoji spaces, "
            f"but you only have {available_space} available. "
            f"Please **delete {emojis_to_delete} emojis**"
        )


async def create_emojis(inter: disnake.MessageInteraction, emoji_guild: disnake.Guild, dash: bool) -> str:
    """Creates the emojis in your server"""
    async with aiohttp.ClientSession() as session:
        tasks = []
        for emoji in emoji_guild.emojis:
            async with session.get(emoji.url) as response:
                emoji_image = await response.read()
                name = emoji.name.replace("_", "") if not dash else emoji.name
                tasks.append(inter.guild.create_custom_emoji(name=f"BWB_{name}", image=emoji_image))
        
        try:
            await asyncio.gather(*tasks)
        except (disnake.HTTPException, disnake.NotFound, ValueError) as e:
            return f"An error occurred creating emojis: {e}\nPlease report this"
        
    return "Your emojis have been made"

async def emoji_command(
    inter: disnake.MessageInteraction, guild: disnake.Guild, dash: bool
) -> None:
    """Adds the 'emoji_space_check' and 'create_emoji' functions together"""
    emoji_guild = guild

    # Space check
    space_check = await emoji_space_check(inter, emoji_guild)
    if space_check:
        return await inter.response.send_message(embed=Embed(title="Not Enough Emojis Spaces", description=space_check).danger_embed(), ephemeral=True)
      
    # Make emojis
    await inter.response.defer()
    result = await create_emojis(inter, emoji_guild, dash)

    # Send result message
    #result_message = (
    #    f"__**{emoji_guild.name}**__\n"
    #    f"{result}"
    #)
    embed = Embed(title=f'{emoji_guild.name} Results', description=result, user=inter.author, guild=inter.guild)
    await inter.send(embed=embed, content=inter.author.mention, allowed_mentions=disnake.AllowedMentions(users=True))


class EmojiEmbedDropdownView(disnake.ui.View):
    def __init__(self, inter: disnake.MessageInteraction):
        super().__init__()
        self.inter = inter

        self.add_item(EmojiEmbed())

  
    async def on_timeout(self):
        await self.inter.edit_original_message(
            view=None,
            content="Command has expired, run `/emoji` to use the command again",
        )

  
    async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
        if inter.author.id != self.inter.author.id:
            await inter.response.send_message("This is not your menu!", ephemeral=True)
            return False
        return True

class EmojiEmbed(disnake.ui.Select):
    """Emoji help menu dropdown view"""

    def __init__(self):
        options = [
            disnake.SelectOption(
                label=command,
                description=details["description"],
                emoji=details["emoji"],
            )
            for command, details in EMOJI_COMMANDS.items()
        ]

        super().__init__(
            placeholder="Pick the type of emojis you want", options=options
        )

    async def callback(self, inter: disnake.MessageInteraction):
        embed = Embed(
            title=f"{self.values[0]} Emojis",
            description="Pick the type of emojis you want",
            user=inter.author
        )
        embed.set_image(url=EMOJI_COMMANDS[self.values[0]]["help_image"])

        await inter.response.edit_message(
            embed=embed, view=EmojiCommandButton(inter, self.values[0])
        )

class EmojiButton(disnake.ui.Button):
    def __init__(self, league: str, label: str, dash_button: disnake.ui.Button):
        super().__init__(label=label)
        self.league = league
        self.dash_button = dash_button

        self.emoji_command_queue = {}
        self.processing_emoji_command = False

        self.emojis_added = 0
  
    async def process_emoji_command_queue(self) -> None:
         while self.emoji_command_queue:
            _, data = self.emoji_command_queue.popitem()
            await asyncio.sleep(2)
            await emoji_command(**data)

  
    async def callback(self, inter: disnake.MessageInteraction) -> None:
        dash_button_color = self.dash_button.style

        dash = True if dash_button_color is disnake.ButtonStyle.green else False
        guild_id = EMOJI_COMMANDS[self.league][self.label]

        guild = disnake.utils.get(inter.bot.guilds, id=guild_id)
        added_emojis = len(guild.emojis)

        self.emojis_added += added_emojis
        if self.emojis_added >= 50:
            self.emojis_added = 0
            return await inter.send(embed=Embed(title="50 Emoji Limit", description="Discord has a strict policy where only 50 emojis can be made a hour, this command will put you over that limit. **I recommend waiting a hour before you make these emojis**").warn_embed())
      
        if self.processing_emoji_command:  # True
            self.emoji_command_queue[guild.id] = {
                "inter": inter,
                "guild": guild,
                "dash": dash,
            }
        else:
            self.processing_emoji_command = True
            await emoji_command(inter, guild, dash)
            await self.process_emoji_command_queue()
            self.processing_emoji_command = False
      


class EmojiCommandButton(disnake.ui.View):
    def __init__(self, inter: disnake.MessageInteraction, league: str):
        super().__init__()
        self.inter = inter
        self.league = league
        self.dash_button = disnake.ui.Button(style=disnake.ButtonStyle.green)
        self.add_item(EmojiEmbed())

        for name, id in EMOJI_COMMANDS[league].items():
            if name not in ['help_image', 'emoji', 'description']:
                self.add_item(
                    EmojiButton(label=name, league=league, dash_button=self.dash_button)
                )

    @disnake.ui.button(label="Dash?", style=disnake.ButtonStyle.green, row=1)
    async def dash_button_button(
        self, button: disnake.ui.Button, inter: disnake.MessageInteraction
    ) -> None:
        if button.style == disnake.ButtonStyle.green:
            button.style = disnake.ButtonStyle.red
            await inter.send("Emoji names will no longer use dashes and will look like this: \n `DallasCowboys`", ephemeral=True)
        else:  # if red
            button.style = disnake.ButtonStyle.green
            await inter.send("Emoji names will now use dashes and will look like this: \n `Dallas_Cowboys`", ephemeral=True)

        self.dash_button.style = button.style
        await inter.message.edit(view=self)

  
    async def on_timeout(self):
        await self.inter.edit_original_message(
            view=None,
            content="Command has expired, run `/emojis` to use the command again",
        )

    async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
        if inter.author.id != self.inter.author.id:
            await inter.response.send_message("This is not your menu!", ephemeral=True)
            return False
        return True


class EmojiCommands(commands.Cog):
    def __init__(self, bot: commands.AutoShardedInteractionBot):
        self.bot = bot

    @commands.slash_command()
    @commands.cooldown(1, 20, commands.BucketType.user)
    @commands.bot_has_permissions(manage_emojis=True)
    @commands.has_permissions(manage_emojis=True)  
    async def emojis(self, inter: disnake.GuildCommandInteraction):
        """Add league emojis to your server with the Emoji Menu\u2122""" # tm logo
        link = Links.template_server
        description = f"See all the emojis at once [here]({link})"

        embed = Embed(
            title="Bread Winner B's Emoji Menu:tm:",
            description=description,
            user=inter.author
        )
        embed.set_image(
            url="https://breadwinner.dev/images/emojis_command_banner"
        )

        await inter.response.defer()
        await inter.send(embed=embed, view=EmojiEmbedDropdownView(inter))


def setup(bot):
    bot.add_cog(EmojiCommands(bot))