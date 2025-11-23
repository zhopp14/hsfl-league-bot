import disnake
from disnake.ext import commands

from utils.config import Emojis, Links
from utils.embed import Embed

template_desc = f"Easily see all the templates at once [by clicking here]({Links.template_server})"

LEAGUE_TEMPLATES = {
    # Sports Leagues
    "NFL": {
        "templates": [
            "https://discord.new/UQCr7duAnayN",
            "https://discord.new/RF9tr4zgDuFg",
            "https://discord.new/7e8MCB5aeXwF",
            "https://discord.new/Tb8R23wmAtHY",
            "https://discord.new/KtSXUab4AqbH",
            "https://discord.new/NF9Vd2VRQzcF",
            "https://discord.new/NHTzMnHQFgFb",
            "https://discord.new/Etergu8T5CS7",
            "https://discord.new/q8aDDAkSEPHz",
            "https://discord.new/8avZ8MUDQ63F",
        ],
        "image": Emojis.nfl_logos[6],
    },
    "NBA": {
        "templates": [
            "https://discord.new/RcdbKzQheVf3",
            "https://discord.new/Xq3snEd8nMC3",
            "https://discord.new/e8S8X8wNXZ59",
            "https://discord.new/HWvXUdEkxFs9",
            "https://discord.new/sXFvYWQmFZ65",
            "https://discord.new/bzJZskRQBAM8",
            "https://discord.new/vVRg72n8kxdg",
            "https://discord.new/Aph47u5XG3vB",
            "https://discord.new/N2a47W6mzxxU",
            "https://discord.new/auZttxyB2cBW",
        ],
        "image": Emojis.nba_logos[4],
    },
    "MLB": {
        "templates": [
            "https://discord.new/FZnQsatHuMSc",
            "https://discord.new/kvC48PAy2Bn6",
            "https://discord.new/zycQ7Pwy6UyW",
            "https://discord.new/Jnd5fAUwQgzj",
            "https://discord.new/RrAZKKeacyyB",
            "https://discord.new/zerVbf3g8xxF",
            "https://discord.new/ddgWMT7assBa",
            "https://discord.new/z92962e3bnSV",
            "https://discord.new/jVNXzRmTzhYa",
            "https://discord.new/f6XmfTcBBKzG",
        ],
        "image": Emojis.mlb_logos[2],
    },
    "NHL": {
        "templates": [
            "https://discord.new/kGxKsN9fdZj4",
            "https://discord.new/vuywwAN6TMCz",
            "https://discord.new/HC4FSbEjhQpG",
            "https://discord.new/bEpkJK9wJ4pF",
            "https://discord.new/mmzu5pKt8jZX",
            "https://discord.new/ySuR8UCDNVmP",
            "https://discord.new/swJETH3f6hgD",
            "https://discord.new/2URa5bhQnETy",
            "https://discord.new/FJgq4AZ7QNWQ",
            "https://discord.new/8tuQ38U3rP2u",
        ],
        "image": Emojis.nhl_logos[2],
    },
    "Soccer": {
        "templates": [
            "https://discord.new/mgqTdD4g47s9",
            "https://discord.new/bSJWf6PJB3aE",
            "https://discord.new/VkfbuaScxWAQ",
            "https://discord.new/KmJdPqdVtGmJ",
            "https://discord.new/KzUhEpNtxRq5",
            "https://discord.new/9YT9aeznPXAf",
            "https://discord.new/rvMBvVjQd4N6",
            "https://discord.new/KPMZCWjUwzkM",
            "https://discord.new/FyxuYsMRw3Jy",
            "https://discord.new/qC7r4zGHNQrT",
        ],
        "image": "https://breadwinner.dev/images/soccer_ball.png"
    },
    "Football Fusion": {
        "templates": [
            "https://discord.new/62gFNuPfMAhR",
            "https://discord.new/QJN7zJWvh2pM",
            "https://discord.new/dQ2Pb6pVQazx",
            "https://discord.new/txTcsKNGj8cj",
            "https://discord.new/u9MrUhvuZYyk",
            "https://discord.new/KARCmm9xuVhY",
            "https://discord.new/WWSMEWrJ5DES",
            "https://discord.new/9Pt3dsBg4fjp",
            "https://discord.new/pEdKgjkJd76V",
            "https://discord.new/zRKfSGF2pQcE",
        ],
        "image": "https://breadwinner.dev/images/Football_Fusion.jpg"
    },
    "Ultimate Football": {
        "templates": [
            "https://discord.new/BAXTUeVUkbVm",
            "https://discord.new/hAvKdTy7Cwmk",
            "https://discord.new/awXZQhKBWgwJ",
            "https://discord.new/k2Z2CPwGZudC",
            "https://discord.new/MPY9Dxnfzjr5",
            "https://discord.new/h6KfsJVHG8u2",
            "https://discord.new/muCN2rNdDjy6",
            "https://discord.new/2FJ2rYAykeU2",
            "https://discord.new/hfgYRDDQbPCW",
            "https://discord.new/8AVYvw4FyGu5",
        ],
        "image": "https://breadwinner.dev/images/Ultimate_Football.png",
    },
    "College": {
        "templates": [
            "https://discord.new/uhwxW4vedd2P",
            "https://discord.new/szqd2ZdhVC9m",
            "https://discord.new/mEcEctwCdE8S",
            "https://discord.new/KJMfBcGeD8wm",
            "https://discord.new/NPABxvxUms7P",
            "https://discord.new/mKBTfrjgJzHs",
            "https://discord.new/WeTFjqXu7kMb",
            "https://discord.new/r6F7vbH4gGmk",
            "https://discord.new/kKWchA2YaEzV",
            "https://discord.new/xqdg946rYpDv",
        ],
        "image": Emojis.college_conferences[8],
    },
    "XFL": {
        "templates": [
            "https://discord.new/FYKpDccy5xVy",
            "https://discord.new/v8hpcFmdPC7E",
            "https://discord.new/BpRPQ9yq2FBu",
            "https://discord.new/kezp72z8PSRJ",
            "https://discord.new/xFBqnjTKbJPM",
            "https://discord.new/n38ZSpcCY9XD",
            "https://discord.new/JpQHCYCJNMXM",
            "https://discord.new/Y4YGCNUPEMh4",
            "https://discord.new/d9X2WdX72aDj",
            "https://discord.new/xh5ZcUxMuPgB",
        ],
        "image": "https://breadwinner.dev/images/XFL.png"
    },
    "USFL": {
        "templates": [
            "https://discord.new/8eCEQUTHNWBU",
            "https://discord.new/AdBZXTg7gzDn",
            "https://discord.new/Q4CXKtzhWKHg",
            "https://discord.new/hnqwkpYGNBRD",
            "https://discord.new/T3rkeKRfKysh",
            "https://discord.new/SjaQc3XNZ3GN",
            "https://discord.new/rcH33CMeNgBE",
            "https://discord.new/yfQZFWDxAS8g",
            "https://discord.new/h6t29YvqnYsp",
            "https://discord.new/5NAwMpu6y8yc",
        ],
        "image": "https://breadwinner.dev/images/USFL.png"
    },
    "FCF": {
        "templates": [
            "https://discord.new/naY2tV52EhCx",
            "https://discord.new/6NNwPDrr3Jbr",
            "https://discord.new/kADvkkzmaUGh",
            "https://discord.new/vB99rfRjPnFC",
            "https://discord.new/nvzsVsCzBuK5",
            "https://discord.new/fursBbVps7FW",
            "https://discord.new/EdydzeqWbnvE",
            "https://discord.new/ndFBxesdSV8r",
            "https://discord.new/9n7x7WM7Wzc3",
            "https://discord.new/WHqdcsBVm9pM",
        ],
        "image": "https://breadwinner.dev/images/FCF.png"
    },
    # Teamhubs/teamchats
    "Team Chat": {
        "templates": [
            "https://discord.new/Kk2KzaHN2dfK",
            "https://discord.new/zaJ8fYkgrjgS",
            "https://discord.new/nVE57P7cPaeK",
        ],
        "image": "https://breadwinner.dev/images/team_logo.jpg",
    },
    "Team Hubs": {
        "templates": [
            "https://discord.new/wvdqjn9Aq22K",
            "https://discord.new/JJRc8rf8gjPn",
            "https://discord.new/rK2HXAQEmSpf",
            "https://discord.new/ZrDx39EbfGxf",
            "https://discord.new/6pxjV6RTJtWu",
        ],
        "image": "https://breadwinner.dev/images/team_logo.jpg",
    },
    "Store": {
        "templates": [
            "https://discord.new/9nVcSAWbXnpR",
        ],
        # "image": "team_hubs_image.jpg"
    },
}


async def template_embed(inter, league):
    """Embed maker for template commands"""
    embed = Embed(
        title=f"{league} Templates",
        description=template_desc,
    )
    templates = LEAGUE_TEMPLATES[league]["templates"]
    message = " ".join(f"[{i + 1}]({template})" for i, template in enumerate(templates))

    embed.add_field(name="Templates", value=message)

    image = LEAGUE_TEMPLATES[league].get("image")
    if image:
        image = disnake.PartialEmoji.from_str(image)
        embed.set_thumbnail(image.url or image)  # for non-emojis

    await inter.edit_original_message(embed=embed)


class TemplateMenuDropdownView(disnake.ui.View):
    def __init__(self, inter: disnake.MessageInteraction):
        super().__init__()
        self.inter = inter

        self.add_item(TemplateMenu())

    async def on_timeout(self):
        await self.inter.edit_original_message(
            view=None,
            content="Command has expired, run `/templates` to use the command again",
        )

    async def interaction_check(self, inter: disnake.MessageInteraction) -> bool: 
        if inter.author.id != self.inter.author.id:
            await inter.response.send_message("This is not your menu!", ephemeral=True)
            return False
        return True


class TemplateMenu(disnake.ui.Select):
    def __init__(self):
        options = [
            disnake.SelectOption(label=league) for league in LEAGUE_TEMPLATES.keys()
        ]

        super().__init__(placeholder="Pick your template type", options=options)

    async def callback(self, inter: disnake.MessageInteraction):
        await inter.response.defer()
        type = self.values[0]
        await template_embed(inter, type)

class TemplateCommands(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  @commands.slash_command()
  async def templates(self, inter: disnake.ApplicationCommandInteraction):
    """Easily get started with create your servers with pre-built templates"""
    embed = Embed(title="Template Menu:tm:", description=template_desc)
    await inter.response.send_message(
      embed=embed, view=TemplateMenuDropdownView(inter)
    )

def setup(bot):
  bot.add_cog(TemplateCommands(bot))