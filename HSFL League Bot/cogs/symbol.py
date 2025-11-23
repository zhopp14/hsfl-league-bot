import disnake
from disnake.ext import commands

from utils.config import Links
from utils.embed import Embed

bars_options = [ #10
      "═══",
      "---", 
      "———", 
      "▬▬▬", 
      "┈┈", 
      "╼╼", 
      "╾╾", 
      "'‎‎‎‎‎‎‎‎‎‎‎‎ ‎‎‎‎‎‎ ‎‎‎‎‎‎ ‎‎‎‎‎‎‎‎‎‎‎‎‎‎‎‎‎‎'",
      "＝＝",
      "≣≣≣"
]

brackets_options = [ # 12
  "【 】",
  "〚 〛",
  "《 》",
  "『 』",
  "〘 〙",
  "〖 〗",
  "〈 〉",
  "（ ）",
  "「 」",
  "« »",
  "‹ ›"
]

lines_options = [ # 6
  "┃",
  "╵",
  "╷",
  "┇",
  "║",
  "▕▏",
]

dots_options = [ # 9
  "•",
  "・",
  "⦿",
  "⦾",
  "○",
  "◦",
  "∙",
  "⁍",
  "⁌"
]

stars_options = [ # 9
  "★",
  "⍟",
  "✩",
  "✦",
  "✧",
  "✪",
  "✫",
  "✬",
  "⭒",
]

dividers_options = [ # 13
  " ⠀⠀⠀⠀⠀⠀𝙁𝙧𝙖𝙣𝙘𝙝𝙞𝙨𝙚⠀⠀⠀⠀⠀",
  " ▬▬▬▬ 👤 Franchise 👤 ▬▬▬▬", 
  "■▬▬▬▬▬〔👤〕▬▬▬▬▬■", 
  " ▬▬▬▬・𝙁𝙧𝙖𝙣𝙘𝙝𝙞𝙨𝙚・▬▬▬▬",
  "「          ⁣⁣𝗙𝗿𝗮𝗻𝗰𝗵𝗶𝘀𝗲           ⁣」", 
  "━━━━━━━┃ 👤 ┃━━━━━━━",
  "■▬▬▬▬﹝𝙁𝙧𝙖𝙣𝙘𝙝𝙞𝙨𝙚﹞▬▬▬▬■", 
  "👤 | Franchise",
  "‎‎‎‎‎▕▏𝗙𝗿𝗮𝗻𝗰𝗵𝗶𝘀𝗲▕▏",
  "▴         𝗙𝗿𝗮𝗻𝗰𝗵𝗶𝘀𝗲         ▴",
  "▬▬▬▬▬𝙁𝙧𝙖𝙣𝙘𝙝𝙞𝙨𝙚▬▬▬▬▬",
  "‎‎‎‎‎--------𝙁𝙧𝙖𝙣𝙘𝙝𝙞𝙨𝙚--------",
  "‎‎‎‎👤"
]


class SymbolsMenu(disnake.ui.View):
    def __init__(self, inter):
      super().__init__()
      self.inter = inter
      self.message_ = "Pick your symbols"

    async def on_timeout(self):
        await self.inter.edit_original_message(
            view=None,
            content="Command has expired, run `/symbols` to use the command again",
        )

  
    async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:   
        if inter.author.id != self.inter.author.id:
            await inter.response.send_message("This is not your menu!", ephemeral=True)
            return False
        return True


    @disnake.ui.button(label="Bars")
    async def bars_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.send_message(content="Bar Symbols", view=SymbolDropdownView(bars_options), ephemeral=True)

    @disnake.ui.button(label="Brackets")
    async def brackets_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.send_message(content="Bracket Symbols", view=SymbolDropdownView(brackets_options), ephemeral=True)

    @disnake.ui.button(label="Lines")
    async def lines_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.send_message(content="Line Symbols", view=SymbolDropdownView(lines_options), ephemeral=True)

    @disnake.ui.button(label="Dots")
    async def dots_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.send_message(content="Dot Symbols", view=SymbolDropdownView(dots_options), ephemeral=True)

    @disnake.ui.button(label="Stars")
    async def stars_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.send_message(content="Star Symbols", view=SymbolDropdownView(stars_options), ephemeral=True)

    @disnake.ui.button(label="Dividers")
    async def dividers_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.send_message(content="Dividers", view=SymbolDropdownView(dividers_options), ephemeral=True)


class SymbolDropdown(disnake.ui.Select):
    def __init__(self, symbol_list, max_value):
        options = []
      
        for symbol in symbol_list:
          options.append(disnake.SelectOption(label=symbol, value=symbol))
          
        super().__init__(placeholder="Choose your symbols", max_values=max_value, options=options)
      
    async def callback(self, interaction: disnake.MessageInteraction):
      
        labels = [thing for thing in self.values]
        await interaction.response.send_message(f"{', '.join(labels)}", ephemeral=True)

class SymbolDropdownView(disnake.ui.View):
    def __init__(self, symbol_list):
        super().__init__()
        self.symbol_list = symbol_list
        self.max_value = len(symbol_list)


        self.add_item(SymbolDropdown(self.symbol_list, self.max_value))

class SymbolCommands(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  @commands.slash_command()
  async def symbol(self, inter: disnake.ApplicationCommandInteraction):
    """Use symbols to make your creations look even better"""
    template_server = Links.template_server
    embed = Embed(
      title="Symbols Menu", 
      description=f"You can also see all the bot's symbols in the [template server]({template_server})"
    )
    await inter.response.send_message(embed = embed, view=SymbolsMenu(inter))

def setup(bot):
  bot.add_cog(SymbolCommands(bot))