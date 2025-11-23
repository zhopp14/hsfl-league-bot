import disnake
from disnake.ext import commands

from utils.config import FONTS_LIST
from utils.embed import Embed
from utils.tools import font_message, premium_user_check
from utils.paginator import Menu

async def limit_check(bot, member: disnake.Member, message: str):
    """Premium users get higher limits for font commands"""
    premium = await premium_user_check(bot, member)
    max_text = 2000 if premium else 1000
    return len(message) > max_text

async def font_command(bot, inter: disnake.ApplicationCommandInteraction, message: str, font: str):
  limit = await limit_check(bot, inter.author, message)
  if not limit:
    text = await font_message(message, font)
    await inter.response.send_message(text)
  else:
    await inter.response.send_message("Your text is to big", ephemeral=True)

class FontCommands(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  @commands.slash_command(name="font-packs")
  async def font_packs(self, inter):
    """
    Shows you commonly used words in a font
    """
    words_list = [
        "Rules", "Information", "Franchise", "Applications", "Suspensions",
        "Tickets", "Chat", "Commands", "Partners", "Welcome", "Pickups",
        "Schedule", "LeaderBoard", "Transactions", "FreeAgency", "Demands", 
        "Verification"
    ]    

    font_words = [
        await font_message(word, font)
        for font in FONTS_LIST
        for word in words_list
    ]

    chunk_size = len(words_list)
    font_word_chunks = [font_words[i:i + chunk_size] for i in range(0, len(font_words), chunk_size)]

    embeds = [
        Embed(
            title="Font Pack",
            description="\n".join(words),
            color=disnake.Color.random()
        )
        for words in font_word_chunks
    ]
    
    await inter.response.send_message(embed=embeds[0], view=Menu(embeds))
    
  @commands.slash_command()
  async def aesthetic(self, inter, sentence: str):
    """
    Ｐｕｔｓ ｙｏｕｒ ｔｅｘｔ ｉｎ ａ ａｅｓｔｈｅｔｉｃ ｆｏｎｔ
    Parameters
    ----------
    sentence: Your text
    """
    await font_command(self.bot, inter, sentence, "aesthetic")
  
  @commands.slash_command()
  async def bold(self, inter, sentence: str):
    """
    𝗣𝘂𝘁𝘀 𝘆𝗼𝘂𝗿 𝘁𝗲𝘅𝘁 𝗶𝗻 𝗮 𝗯𝗼𝗹𝗱 𝗳𝗼𝗻𝘁
    Parameters
    ----------
    sentence: Your text
    """
    await font_command(self.bot, inter, sentence, "bold")

  @commands.slash_command()
  async def circle(self, inter, sentence: str):
    """
    Ⓟⓤⓣⓢ ⓨⓞⓤⓡ ⓣⓔⓧⓣ ⓘⓝ ⓐ ⓑⓘⓖⓒⓘⓡⓒⓛⓔ ⓕⓞⓝⓣ
    Parameters
    ----------
    sentence: Your text
    """
    await font_command(self.bot, inter, sentence, "circle")

  @commands.slash_command()
  async def italic(self, inter, sentence: str):
    """
    𝑷𝒖𝒕𝒔 𝒚𝒐𝒖𝒓 𝒕𝒆𝒙𝒕 𝒊𝒏 𝒂 𝒊𝒕𝒂𝒍𝒊𝒄 𝒇𝒐𝒏𝒕
    Parameters
    ----------
    sentence: Your text
    """
    await font_command(self.bot, inter, sentence, "italic")

  @commands.slash_command()
  async def italicbold(self, inter, sentence: str):
    """
    𝙋𝙪𝙩𝙨 𝙮𝙤𝙪𝙧 𝙩𝙚𝙭𝙩 𝙞𝙣 𝙖 𝙞𝙩𝙖𝙡𝙞𝙘𝙗𝙤𝙡𝙙 𝙛𝙤𝙣𝙩
    Parameters
    ----------
    sentence: Your text
    """
    await font_command(self.bot, inter, sentence, "italicbold")

  @commands.slash_command()
  async def italicsans(self, inter, sentence: str):
    """
    𝘗𝘶𝘵𝘴 𝘺𝘰𝘶𝘳 𝘵𝘦𝘹𝘵 𝘪𝘯 𝘢𝘯 𝘪𝘵𝘢𝘭𝘪𝘤 𝘴𝘢𝘯𝘴 𝘧𝘰𝘯𝘵
    Parameters
    ----------
    sentence: Your text
    """
    await font_command(self.bot, inter, sentence, "italicsans")

  @commands.slash_command()
  async def sans(self, inter, sentence: str):
    """
    𝖯𝗎𝗍𝗌 𝗒𝗈𝗎𝗋 𝗍𝖾𝗑𝗍 𝗂𝗇 𝖺𝗇 𝗌𝖺𝗇𝗌 𝖿𝗈𝗇𝗍
    Parameters
    ----------
    sentence: Your text
    """
    await font_command(self.bot, inter, sentence, "sans")

  @commands.slash_command()
  async def serif(self, inter, sentence: str):
    """
    𝐏𝐮𝐭𝐬 𝐲𝐨𝐮𝐫 𝐭𝐞𝐱𝐭 𝐢𝐧 𝐚 𝐬𝐞𝐫𝐢𝐟 𝐟𝐨𝐧𝐭
    Parameters
    ----------
    sentence: Your text
    """
    await font_command(self.bot, inter, sentence, "serif")
  
def setup(bot):
  bot.add_cog(FontCommands(bot))