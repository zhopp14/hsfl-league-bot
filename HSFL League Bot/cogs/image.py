import random

import disnake
from disnake.ext import commands

from utils.embed import Embed


class ImageCommands(commands.Cog):
    """Fun image-oriented utilities that do not rely on external anime APIs."""

    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command()
    async def ship(self, inter: disnake.GuildCommandInteraction, name1: str, name2: str = None):
        """Calculate the playful compatibility score between two names."""
        if name2 is None:
            name2 = inter.author.display_name

        love_name = f"{name1[: len(name1) // 2].strip()} {name2[len(name2) // 2 :].strip()}"

        score = random.randint(0, 100)
        filled_progbar = round(score / 100 * 10)
        counter_ = "█" * filled_progbar + "‍ ‍" * (10 - filled_progbar)

        embed = Embed(
            title=f"{name1} ❤ {name2}",
            description=f"**Love %**\n`{counter_}` **{score}%**\n**Love Name** {love_name}",
            color=0xDEADBF,
        )

        await inter.response.send_message(embed=embed)


def setup(bot):
    bot.add_cog(ImageCommands(bot))