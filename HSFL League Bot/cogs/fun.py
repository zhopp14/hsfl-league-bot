import random
import re
import string

import aiohttp
import disnake
from bs4 import BeautifulSoup
from disnake.ext import commands

from utils.config import Emojis, Ids, Links
from utils.embed import Embed
from utils.tools import vote_or_premium_user

roast_list = [
    "YOU HONESTLY NEED TO STOP PLAYING THIS GAME", "GOD DAM YOU SUCK", "YOU FRICKING SUCK", "BRO EVEN I COULD BEAT YOU",
    "YOU ARE THE WORSE PLAYER I HAVE EVER SEEN IN MY WHOLE ENTRIE LIFE WHY ARE YOU SO FUCKING BAD OMG PLS GET BETTER IT MAKES ME MAD AND CRINGE HOW DOG SHIT YOU ARE", "YOUR TRASH", "YOUR ASS",
    "😂😂😂", "💀", "You are worse then bad", "You are the reason I don't have kids",
    "You make me sad", "End your life", "Your life has no purpose", "You would be the perfect person for an condom ad",
    "You make my eyes bleed", "You make me want to end my life", "My parents warned to avoid people like you", "You're lucky it's not lower",
    "didn't even know you could be this low", "Can you pls get better?", "YOUR ASS KID", "LMAOOOO",
    "bro come on...", "you suck", "how can you be so bad???", "Explain to me how you are so bad",
    "LMFAO", "You should be sad being this low", "Were you always this bad?", "Did your dad ever play catch with you?",
    "Are you ok?", "you shitter", "Your bad", "You suck",
    "Retire now", "Did you really think you were going to get something good??", "LMAOAO YOU SUCK", "lol try again",
    "Stop trying", "You need to get a LOT better", "Your fucking shit", "Watching you play makes me sad",
    "Your worse then Joe Flacco", "You play like your sped", "You play lego football", "Your ass kid",
    "Stop playing this game", "I could beat your ass", "Your 1v1 record is 1-50", "You look like Tom Brady",
    "You're a virgin", "You are dreaming that you play in LFG", "you dick ride main leaguers", "You have a small dick",
    "I could beat you in a 1v1", "You are the first one out in lob games", "Your worse then JaMarcus Russell", "LMAO YOUR SHIT",
]

async def fun_command_logger(self, inter, name: str, funny: str, is_good: bool):
    bread_logs_channel = self.bot.get_channel(Ids.bread_logs_channel)
    
    server_embed = Embed(
        title=f"{name} is having a {'Good' if is_good else 'Bad'} day",
        description=funny,
        color=inter.author.color,
        user = inter.author
    )
    server_embed.set_footer(text=inter.author.id)
    await bread_logs_channel.send(embed=server_embed)

    user_embed = Embed(
        title=f"Your {'Good' if is_good else 'Bad'} performance is being logged",
        description=f"Come see what people say about it in the [Bread Kingdom Server]({Links.support_server})",
        user = inter.author
    )
    await inter.send(embed=user_embed, ephemeral=True)


class FunCommands(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  @commands.slash_command()
  async def black(self, inter: disnake.ApplicationCommandInteraction, name: str = None):
    """
    See if you're black or not.
    
    Parameters
    ----------
    name: The person to find the blackness of.
    """
    name = name or inter.author.mention

    user_p_check = await vote_or_premium_user(self.bot, inter.author)
    if user_p_check:
        blackness = random.randint(15, 100)
        if blackness == 100:
            blackness = random.randint(101, 500)
    else:
        blackness = random.randint(0, 100)
    
    embed = Embed(
        title="Black Machine",
        description=f"{name} is **{blackness}%** black",
        color=0x000000,
    )
    
    await inter.send(embed=embed)
    
    if name == inter.author.mention:
        name = inter.author.name
        
    if blackness == 0:
        await fun_command_logger(self, inter, name, "They are 0% black", False)
    elif blackness == 100:
        await fun_command_logger(self, inter, name, "They are 100% black", True)


  @commands.slash_command()
  async def gay(self, inter, name: str = None):
      """
      Find out if today is the day your friends come out
      Parameters
      ----------
      name: The person to find the gayness of
      """
      if name is None:
          name = inter.author.mention
  
      user_p_check = await vote_or_premium_user(self.bot, inter.author)
      if user_p_check:
          gayness = random.randint(15, 100)
          if gayness == 100:
              gayness = random.randint(101, 500)
      else:
          gayness = random.randint(0, 100)
  
      if gayness == 0:
          gayStatusOptions = ["100% straight", "No homo", "Like girls"]
          gayColor = 0xFFDAE3
      elif gayness <= 33:
          gayStatusOptions = [
              "No homo",
              "Wearing socks",
              '"Only sometimes"',
              "Straight-ish",
              "No homo bro",
              "Girl-kisser",
              "Hella straight",
          ]
          gayColor = 0xFFC0CB
      elif 33 < gayness < 66:
          gayStatusOptions = [
              "Possible homo",
              "My gay-sensor is picking something up",
              "I can't tell if the socks are on or off",
              "Gay-ish",
              "Looking a bit homo",
              "lol half  g a y",
              "Only a little sus",
              "safely in between for now",
              "Only for the homies",
              "The socks were on",
          ]
          gayColor = 0xFF69B4
      elif gayness == 69:
          gayStatusOptions = ["haha funny number"]
          gayColor = 0xFF69B4
      else:
          gayStatusOptions = [
              "LOL YOU GAY XDDD FUNNY",
              "HOMO ALERT",
              "MY GAY-SENSOR IS OFF THE CHARTS",
              "STINKY GAY",
              "BIG GEAY",
              "THE SOCKS ARE OFF",
              "HELLA GAY",
              "Even the homes don't like it",
              "FULL HOMO",
          ]
          gayColor = 0xFF00FF
  
      gayStatus = random.choice(gayStatusOptions)
  
      emb = Embed(
          description=f"Gayness for **{name}**",
          color=disnake.Color(gayColor)
      )
      emb.add_field(name="Gayness:", value=f"{gayness}% gay")
      emb.add_field(name="Comment:", value=f"{gayStatus} :kiss_mm:")
      emb.set_author(
          name="Gay-Scanner™",
          icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb/a/a4/ICA_flag.svg/2000px-ICA_flag.svg.png",
      )
      await inter.send(embed=emb)
  
      if name == inter.author.mention:
          name = inter.author.name
  
      if gayness == 0:
          await fun_command_logger(self, inter, name, "They are 0% gay", True)
      elif gayness == 100:
          await fun_command_logger(self, inter, name, "They are 100% gay", False)


  @commands.slash_command(name="8ball")
  async def eightball(self, inter: disnake.ApplicationCommandInteraction, question: str):
      """
      Ask this 100% accurate 8ball a question
      Parameters
      ----------
      question: str
          The question to ask the 8ball
      """
      answers = [
          "Hell no", "No you idiot", "NO", "Yeah no", "lol no",
          "Don't ask stupid questions", "\ud83d\ude10", "You're weird for asking that",
          "I'm an 8ball, not a deal with your crap ball", "idc", "Don't really care",
          "never dumbass", "sure, I literally couldn't care less", "Yes",
          "Signs point to yes", "Concentrate and ask again", "yes???",
          "hell to the yes", "heck off, you know that's a no", "No, you ape",
          "no lmfao", "don't sass me bitch", "yes idiot",
          "ask again later when I'm less busy with your mum", "I have better things to do",
          "\ud83d\ude02\ud83e\udd23", "no???", "maybe", "don't count on it",
          "Is this a joke?", "get a life", "You're weird no", "yes!!!",
          "wtf are you asking me", "lol literally no", "smh fine", "Yes (only because you paid me)",
          "ok, whatever yes", "NOOOOOOOOOOOOOOOOOOOOOOOOOOO", "YESSSSSSSSSSSSSSSSSS",
          "I'll answer when I'm done talking with your mum",
          "https://tenor.com/view/boi-what-the-hell-boi-gif-22147158",
          "ok yes", "yes cuz you're a little bitch", "nah you're too gay", "Why are you asking me??",
      ]
      
      response = random.choice(answers)
      await inter.response.send_message(f"{question.rstrip('?')}?\n> 🎱 {response}")


  @commands.slash_command()
  async def pp(self, inter, name: str = None):
    """
    Shows how big your pp is
    Parameters
    ----------
    name: The person to the get pp size of
    """
    name = name or inter.author.mention
    user_p_check = await vote_or_premium_user(self.bot, inter.author)
    if user_p_check:
      size = random.randint(6, 16)
    else:
      size = random.randint(0, 16)

    if size == 16:
        size = random.randint(30, 100)
        if size == 100:
          size = random.randint(101, 2000)

    dong = "=" * size
    inches = f"{size} inch{' LOL' if size < 4 else 'es'}"

    embed = Embed(
        title="🍆 pp size 🍆",
        description=f"**{name}:** 8{dong}D",
        color=disnake.Color.random(),
    )
    embed.set_footer(text=inches)
    await inter.send(embed=embed)

    if name == inter.author.mention: name = inter.author.name
    if size > 90:
        await fun_command_logger(self, inter, name, f"He has a {size} inch pp 😎\n8{dong}D", True)

  @commands.slash_command()
  async def overall(self, inter, name: str = None):
      """
      See how bad you are in number form
      """
      if name is None:
          name = inter.author.mention
  
      user_p_check = await vote_or_premium_user(self.bot, inter.author)
      overall = random.randint(55, 100) if user_p_check else random.randint(40, 100)
  
      if overall >= 40 and overall < 70:
          color = disnake.Color(0xB87333)
          overall = f"{overall} {random.choice(roast_list)}"
      elif overall >= 70 and overall < 86:
          color = disnake.Color(0xFFD700)
      elif overall >= 86 and overall < 95:
          color = disnake.Color(0xDC143C)
      elif overall >= 95:
          color = disnake.Color(0x3498DB)
  
      embed = Embed(
          title="Overall",
          description=f"**{name}**'s overall is **{overall}**",
          color=color
      )
      await inter.send(embed=embed)
  
      if name == inter.author.mention:
          name = inter.author.name
  
      if overall == 40:
        await fun_command_logger(self, inter, name, f"{name} just got an overall of **40** bro is TRASH 💀", False)
      elif overall == 100:
        await fun_command_logger(self, inter, name, f"{name} just got an overall of **100** bro is SEXY 😳", True)

  @commands.slash_command()
  async def devtrait(self, inter, name: str = None):
      """
      Find out your shitty devtrait you have (ps. its not good)
      Parameters
      ----------
      name: The user to get the devtrait from
      """
      if name is None:
          name = inter.author.mention
  
      devtraits = [
          "Ankle Breaker", "Bazooka", "Blitz Radar", "Double Me", "First One Free",
          "Freight Train", "Gambler", "Max Security", "Pro Reads", "RAC'em Up",
          "Satellite", "Truzz", "Wrecking Ball", "YAC'em Up", "Avalanche", "Blitz",
          "Bottleneck", "Fearmonger", "Momentum Shift", "Reinforcement", "Relentless",
          "Run Stuffer", "Shutdown", "Unstoppable Force", "Zone Hawk"
      ]
  
      ps = {
          "red": f"<:SuperStar_X_Factor:850147331864789022> Superstar X Factor\nAbility: {random.choice(devtraits)}",
          "gold": "<:SuperStar_Dev:850147314165481533> Superstar Dev",
          "silver": "<:Star_Dev:850147296757678120> Star Dev",
          "hidden": "<:Hidden_Dev_Trait:850147349278883840> Hidden Dev Trait",
          "copper": "<:Normal_Dev:850147279288401950> Normal Dev",
          "nodev": f"No Dev - {random.choice(roast_list)}",
      }
      
      default_color = disnake.Color(0x000000)
      choice = random.choices(list(ps.values()))[0]
  
      color_mapping = {
          "copper": disnake.Color(0x9A5D33),
          "gold": disnake.Color(0xF8D26D),
          "red": disnake.Color(0xDC0C10),
          "silver": disnake.Color(0xABACB0),
          "hidden": disnake.Color(0x418EDF),
          "nodev": disnake.Color(0x000000),
      }
      color = color_mapping.get(choice, default_color)
  
      embed = Embed(
          title="Devtrait",
          description=f"**{name}**'s devtrait is **{choice}**",
          color=color,
      )
      await inter.response.send_message(embed=embed)


  @commands.slash_command(name="1v1")
  async def onevsone(self, inter, member: disnake.Member):
      """
      Lose in a 1v1 match
      Parameters
      ----------
      member: The person you are going to lose to
      """
      score_winner = random.randint(0, 10)

      winner, loser = (inter.author, member) if random.randint(0, 1) == 0 else (member, inter.author)
      insult = random.choice(roast_list)
      
      if score_winner == 10:
          score_text = f"10-0 {insult}"
      else:
          score_text = f"{score_winner}-10"
        
      embed = Embed(
          title=f"🏈 {winner.display_name} **vs** {loser.display_name} 🏈",
          description=f"{winner.mention} has won with the score **{score_text}**",
          color=winner.color,
      )
      await inter.response.send_message(embed=embed)

  @commands.slash_command()
  async def leaguename(self, inter, count: commands.Range[int, 1, 100] = 1):
    """
    Gives you really good names for your league
    Parameters
    ----------
    count: How many league names you want at once
    """
    length = random.choice([3, 4])
    letters = string.ascii_uppercase
    names = []
    for _ in range(count):
      name = ''.join(random.choice(letters) for _ in range(length))
      names.append(name)
    await inter.response.send_message(f"Your league's name should be: **{'**, **'.join(names)}**")

  @commands.slash_command()
  async def superbowl(self, inter: disnake.ApplicationCommandInteraction):
    """The 2023 Superbowl matchup"""
    superbowl_number = "57"
      
    # Teams
    nfc_team = random.choice(Emojis.nfl_nfc)
    afc_team = random.choice(Emojis.nfl_afc)
    # Emoji
    super_bowl_logo = Emojis.nfl_logos[8]

    scores = [0, 2, 3, 7, 9, 10, 14, 17, 21, 24, 27, 28, 32, 31, 35, 38, 54, 67, 220]
    score1, score2 = random.sample(scores, 2)
          
    await inter.response.send_message(
      f"‎‎‎‎**{super_bowl_logo} SuperBowl {superbowl_number}**\n\n {nfc_team} **{score1}** || **{score2}** {afc_team}"
    )

  @commands.slash_command()
  async def whodidit(self, inter: disnake.GuildCommandInteraction, did_what: str):
    """
    Who did it?
    Parameters
    ----------
    did_what: The thing they did
    """
    member = random.choice(await inter.guild.chuck())
    embed = Embed(
        title = f"Who {did_what}?",
        description = f"{member.name} was the one who did it",
        color = member.color
    )
    await inter.response.send_message(embed=embed)

  
  # API commands

  @commands.slash_command()
  async def age(self, inter, name: str):
    """
    Find out how old you are
    Parameters
    ----------
    name: The name to lookup the age of
    """

    x = re.search("<(@!(&!)?|#)[0-9]+>", name)
    if x:
      return await inter.response.send_message(
        "You can't ping someone, you have to type in a name (Example: Bob, Jackson, Tom)",
          ephemeral=True,
      )

    async with aiohttp.ClientSession() as session:
      name = name.lower().title()
      async with session.get(f"https://api.agify.io?name={name}") as resp:
        if resp.status != 200:
            return await inter.response.send_message(
              "Error: Unable to find age for the specified name.",
              ephemeral=True,
            )              
        r = await resp.json()
        embed = Embed(
          title=f"⌛ Age Guesser for {r['name']}", 
          color=inter.author.color
        )
        embed.add_field(name="`Age`:", value=r["age"])
        embed.add_field(name="`People with this name`:", value=r["count"])
        await inter.response.send_message(embed=embed)

  @commands.slash_command()
  async def roast(self, inter, name: str = None):
    """
    Roast your stupid friends ;)
    Parameters
    ----------
    name: The person to roast
    """
    if name is None:
      name = inter.author.mention
    
    async with aiohttp.ClientSession() as session:
      async with session.get(
        "https://evilinsult.com/generate_insult.php?lang=en&type=json"
      ) as resp:
          if resp.status != 200:
              return await inter.response.send_message(
                "Oops, something went wrong...", ephemeral=True)
          r = await resp.json()
          text = r["insult"]
          embed = Embed(
              title="Get Roasted Nerd",
              description=f"{name}, {text}",
              color=disnake.Color.random(),
          )
          await inter.response.send_message(embed=embed)


  @commands.slash_command(name="gangsta-name")
  async def gangsta_name(self, inter, name: str = None):
    """
    Trade in your weak-ass name for something harder
    Paremeters
    ----------
    name: The name to turn into a gangsta
    """
    name = name or inter.author.name
    # http://gangstaname.com/names/gangsta/generate?name=l#.ZCy7YXvMJEY
    url = f"http://gangstaname.com/names/gangsta/generate?name={name}#.ZCo3gXvMJEY"
      
    async with aiohttp.ClientSession() as session:
      async with session.get(url) as resp:
          if resp.status != 200:
              return await inter.response.send_message(
                "Oops, something went wrong...", ephemeral=True)
    
          soup = BeautifulSoup(await resp.text(), "html.parser")
          h2_tag = soup.find('h2', {'class': 'name'})
          text_content = h2_tag.text.strip()

          embed = Embed(title = "Gangsta Name", description = f"{name} gangsta name is: **{text_content}**", color = inter.author.color)  
          await inter.response.send_message(embed = embed)    

  @commands.slash_command()
  async def petname(self, inter, name: str = None):
    """
    Make a cute name to call your speical someone (doubt you have one tho)
    Paremeters
    ----------
    name: The name to turn into a pet name
    """
    name = name or inter.author.name
    url = f"http://gangstaname.com/names/pet/generate?name={name}#.ZCzAp3vMJEY"
      
    async with aiohttp.ClientSession() as session:
      async with session.get(url) as resp:
          if resp.status != 200:
              return await inter.response.send_message(
                "Oops, something went wrong...", ephemeral=True)
    
          soup = BeautifulSoup(await resp.text(), "html.parser")
          h2_tag = soup.find('h2', {'class': 'name'})
          text_content = h2_tag.text.strip()

          embed = Embed(title = "Pet Name", description = f"{name} pet name is: **{text_content}**", color = inter.author.color)  
          await inter.response.send_message(embed = embed) 
 
    
def setup(bot):
  bot.add_cog(FunCommands(bot))