import asyncio
import random
import time
from typing import List

import disnake
from disnake.ext import commands
from fuzzywuzzy import fuzz

from utils.embed import Embed


class Player:
    def __init__(self, name: str, position: str, hint: str):
        self.name = name
        self.position = position
        self.hint = hint  # draft class, when picked, teams played for, records, "was really good in 2006", probowls (awards), superbowls (maybe make this a list of hints)


PLAYERS_LIST = [
    # https://sportsnaut.com/nfl-top-100-players/
    Player("David Bakhtiari", "OT", "Colorado, 4th round 2013"),
    Player("Corey Linsley", "C", "Ohio State, 5th round 2015"),
    Player("Joe Thuney", "OG", "NC State, 3rd round 2016"),
    Player("A.J. Terrell", "CB", "Clemson, 1st round 2020 (Pick 16)"),
    Player("Tyler Lockett", "WR", "Kansas State, 3rd round 2015"),
    Player("Tremaine Edmunds", "LB", "Virginia Tech, 1st round 2018 (Pick 16)"),
    Player("Chris Olave", "WR", "Ohio State, 1st round in 2022 (Pick 11)"),
    Player("Dre Greenlaw", "LB", "Arkansas, 5th round 2019"),
    Player("Matt Milano", "LB", "Boston College, 5th round 2017"),
    Player("Tony Pollard", "RB", "Memphis, 4th round 2019"),
    Player("DK Metcalf", "WR", "Ole Miss, 2nd round 2019"),
    Player("Garrett Wilson", "WR", "Ohio State, 1st round 2022 (Pick 10)"),
    Player("Trevon Diggs", "CB", "Alabama, 2nd round 2020"),
    Player("Quenton Nelson", "OG", "Notre Dame, 1st round 2018 (Pick 6)"),
    Player("DeAndre Hopkins", "WR", "Clemson, 1st round 2013 (Pick 27)"),
    Player("Za’Darius Smith", "Edge", "Kentucky, 4th round 2015"),
    Player("DeVonta Smith", "WR", "Alabama, 1st round 2021 (Pick 10)"),
    Player("Austin Ekeler", "RB", "Western Colorado, Undrafted 2017"),
    Player("Micah Hyde", "S", "Iowa, 5th round 2013"),
    Player("Matthew Judon", "Edge", "Grand Valley State, 5th round 2016"),
    Player("Kirk Cousins", "QB", "Michigan State, 4th round 2012"),
    Player("Stephon Gilmore", "CB", "South Carolina, 1st round 2012 (Pick 10)"),
    Player("Joey Bosa", "Edge", "Ohio State, 1st round 2016 (Pick 3)"),
    Player("Darius Slay", "CB", "Mississippi State, 2nd round 2013 "),
    Player(
        "Shaquille Leonard", "LB", "Louisiana State University, 1st round 2017 (Pick 3)"
    ),
    Player("DeForest Buckner", "DT", "Oregon, 1st round 2016 (Pick 7)"),
    Player("Kevin Byard", "S", "Middle Tennessee State, 3rd round 2016"),
    Player("Charvarius Ward", "CB", "Middle Tennessee State, Undrafted 2018"),
    Player("Mark Andrews", "TE", "Oklahoma, 3rd round 2018"),
    Player("Zack Martin", "OG", "Notre Dame, 1st round 2014 (Pick 16)"),
    Player("Dak Prescott", "QB", "Mississippi State, 4th round 2016"),
    Player("Penei Sewell", "OT", "Oregon, 1st round 2021 (Pick 7)"),
    Player(
        "Jordan Mailata", "OT", "South Sydney Rabbitohs (Australia), 7th round 2018"
    ),
    Player("Derwin James", "S", "Florida State, 1st round 2018 (Pick 17)"),
    Player("Brandon Graham", "Edge", "Michigan, 1st round 2010 (Pick 13)"),
    Player("Jonathan Taylor", "RB", "Wisconsin, 2nd round 2020"),
    Player("Tua Tagovailoa", "QB", "Alabama, 1st round 2020 (Pick 5)"),
    Player("Tee Higgins", "WR", "Clemson, 2nd round 2020"),
    Player("Aaron Rodgers", "QB", "California, 1st round 2005 (Pick 24)"),
    Player("Von Miller", "Edge", "Texas A&M, 1st round 2011 (Pick 2)"),
    Player("Jaylen Waddle", "WR", "Alabama, 1st round 2021 (Pick 6)"),
    Player("Demario Davis", "LB", "Arkansas State, 3rd round 2012"),
    Player("Trevor Lawrence", "QB", "Clemson, 1st round 2021 (Pick 1)"),
    Player("Jaelan Phillips", "Edge", "Miami (FL), 1st round 2021 (Pick 18)"),
    Player("Derrick Brown", "DT", "Auburn, 1st round 2020 (Pick 7)"),
    Player("Amon-Ra St. Brown", "WR", "USC, 4th round 2021"),
    Player("Saquon Barkley", "RB", "Penn State, 1st round 2018 (Pick 2)"),
    Player("CeeDee Lamb", "WR", "Oklahoma, 1st round 2020 (Pick 17)"),
    Player("Jaire Alexander", "CB", "Louisville, 1st round 2018 (Pick 18)"),
    Player("Minkah Fitzpatrick", "S", "Alabama, 1st round 2018 (Pick 11)"),
    Player("Laremy Tunsil", "OT", "Mississippi, 1st round 2016 (Pick 13)"),
    Player("Derrick Henry", "RB", "Alabama, 2nd round 2016"),
    Player("Christian Wilkins", "DT", "Clemson, 1st round 2019 (Pick 13)"),
    Player("Christian Darrisaw", "OT", "Virginia Tech, 1st round 2021 (Pick 23)"),
    Player("Trey Hendrickson", "Edge", "Florida Atlantic, 3rd round 2017"),
    Player("Lavonte David", "LB", "Nebraska, 2nd round 2012"),
    Player("Bobby Wagner", "LB", "Utah State, 2nd round 2012"),
    Player("Haason Reddick", "Edge", "Temple, 1st round 2017 (Pick 13)"),
    Player("Rashawn Slater", "OT", "Northwestern, 1st round 2021 (Pick 13)"),
    Player("Lamar Jackson", "QB", "Louisville, 1st round 2018 (Pick 32)"),
    Player("Josh Jacobs", "RB", "Alabama, 1st round 2019 (Pick 24)"),
    Player("Joel Bitonio", "OG", "Nevada, 2nd round 2014 (Pick 35)"),
    Player("Jason Kelce", "C", "Cincinnati, 6th round 2011"),
    Player("Jeffery Simmons", "DT", "Mississippi State, 1st round 2019 (Pick 19)"),
    Player("Nick Chubb", "RB", "Georgia, 2nd round 2018"),
    Player("Tristan Wirfs", "OT", "Iowa, 1st round 2020 (Pick 13)"),
    Player("Ja’Marr Chase", "WR", "LSU, 1st round 2021 (Pick 5)"),
    Player("Justin Herbert", "QB", "Oregon, 1st round 2020 (Pick 6)"),
    Player("Creed Humphrey", "C", "Oklahoma, 2nd round 2021"),
    Player("Cooper Kupp", "WR", "Eastern Washington, 3rd round 2017"),
    Player("Jalen Ramsey", "CB", "Florida State, 1st round 2016 (Pick 5)"),
    Player("Chris Lindstrom", "OG", "Boston College, 1st round 2019 (Pick 14)"),
    Player("Fred Warner", "LB", "BYU, 3rd round 2018"),
    Player("A.J. Brown", "WR", "Ole Miss, 2nd round 2019"),
    Player("George Kittle", "TE", "Iowa, 5th round 2017"),
    Player("Cameron Heyward", "DT", "Ohio State, 1st round 2011 (Pick 31)"),
    Player("Quinnen Williams", "DT", "Alabama, 1st round 2019 (Pick 3)"),
    Player("Dexter Lawrence", "DT", "Clemson, 1st round 2019 (Pick 17)"),
    Player("Maxx Crosby", "Edge", "Eastern Michigan, 4th round 2019 (Pick 106)"),
    Player("Andrew Thomas", "OT", "Georgia, 1st round 2020 (Pick 4)"),
    Player("Stefon Diggs", "WR", "Maryland, 5th round 2015"),
    Player("Patrick Surtain II", "CB", "Alabama, 1st round 2021 (Pick 9)"),
    Player("Christian McCaffrey", "RB", "Stanford, 1st round 2017 (Pick 8)"),
    Player("Davante Adams", "WR", "Fresno State, 2nd round 2014"),
    Player("Lane Johnson", "OT", "Oklahoma, 1st round 2013 (Pick 4)"),
    Player("T.J. Watt", "Edge", "Wisconsin, 1st round 2017 (Pick 30)"),
    Player("Tyreek Hill", "WR", "West Alabama, 5th round 2016"),
    Player("Josh Allen", "QB", "Wyoming, 1st round 2018 (Pick 7)"),
    Player("Sauce Gardner", "CB", "Cincinnati, 1st round 2022 (Pick 4)"),
    Player("Nick Bosa", "DE", "Ohio State, 1st round 2019 (Pick 2)"),
    Player("Travis Kelce", "TE", "Cincinnati, 3rd round 2013"),
    Player("Myles Garrett", "Edge", "Texas A&M, 1st round 2017 (Pick 1)"),
    Player("Trent Williams", "OT", "Oklahoma, 1st round 2010 (Pick 4)"),
    Player("Justin Jefferson", "WR", "LSU, 1st round 2020 (Pick 22)"),
    Player("Jalen Hurts", "QB", "Alabama/Oklahoma, 2nd round 2020"),
    Player("Chris Jones", "DT", "Mississippi State, 2nd round 2016"),
    Player("Aaron Donald", "DT", "Pittsburgh, 1st round 2014 (Pick 13)"),
    Player("Micah Parsons", "LB", "Penn State, 1st round 2021 (Pick 12)"),
    Player("Joe Burrow", "QB", "LSU, 1st round 2020 (Pick 1)"),
    Player("Patrick Mahomes", "QB", "Texas Tech, 1st round 2017 (Pick 10)"),
]


async def player_search(a, b):
    ratio = fuzz.ratio(a.lower(), b.lower())
    return ratio


async def get_player_image(player_name: str) -> str:
    player_name = player_name.replace(" ", "_")
    player_image = f"https://breadwinner.dev/images/nfl_players/{player_name}"
    return player_image

async def get_new_random_player(old_player_index: int):
    new_player_index = random.randint(1, 5)
    player_index = (
            old_player_index + new_player_index
            if old_player_index + new_player_index < len(PLAYERS_LIST)
            else 0
        )
    return PLAYERS_LIST[player_index]

skip_count = {}

class GuessPlayerButtons(disnake.ui.View):
    def __init__(
        self,
        inter: disnake.MessageInteraction,
        embed: Embed,
        player: Player,
        player_index: int,
    ):
        super().__init__()
        self.inter = inter
        self.embed = embed

        self.skip_count = skip_count
        self.player = player
        self.player_index = player_index

    async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
        if inter.author.id != self.inter.author.id:
            await inter.response.send_message("This is not your menu!", ephemeral=True)
            return False
        return True

    def player_name(self) -> str:
        return self.player.name

    @disnake.ui.button(label="Hint")
    async def hint_button(
        self, button: disnake.ui.Button, inter: disnake.MessageInteraction
    ):
        await inter.response.send_message(
            f"Hint: {self.player.hint}", ephemeral=True, delete_after=2
        )

    @disnake.ui.button(label="Skip")
    async def skip_button(
        self, button: disnake.ui.Button, inter: disnake.MessageInteraction
    ):  

        skip_count = self.skip_count.get(inter.channel.id, {})
        if not skip_count:
            skip_count = self.skip_count[inter.channel.id] = 0
      
        if skip_count > 2:
          return await inter.response.send_message("You have reached the maximum number of skips for this game", ephemeral=True, delete_after=2)
          
        player = await get_new_random_player(self.player_index)

        embed = self.embed
        embed.description = f"Position: {player.position}"
        embed.set_image(url=await get_player_image(player.name))

        await inter.response.send_message(
            content="Skipped", ephemeral=True, delete_after=1
        )
        await self.inter.edit_original_message(embed=embed)
        self.player = player
        self.player_index = PLAYERS_LIST.index(player)
        self.skip_count[inter.channel.id] += 1


class GamesCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.player_limit = 5  # how long players before the game ends
        self.counter: dict[int, int] = {}
        self.correct_guesses: dict[int, int] = {}
        self.answers: dict[int, List[str]] = {}
        self.start_time: float = 0
        self.time_limit: int = 61  # Total time limit in seconds
  
    @commands.slash_command()
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def guessplayer(self, inter: disnake.ApplicationCommandInteraction):
        """
        Try to guess some of the players that beat your favorite team
        """
        await inter.response.defer()

        answers = self.answers.get(inter.channel.id, {})
        if not answers:
            answers = self.answers[inter.channel.id] = []

        self.start_time = time.time()

        await self.guess_player(inter)

        # After 5 players, display the score
        final_score = self.correct_guesses[inter.channel.id]
        answers = self.get_answers(inter.channel.id)

        embed = Embed(
            title="Game Ended",
            description=f"You got **{final_score}/{self.counter[inter.channel.id]} guesses right**\n\nCorrect Answers: \n{answers}",
        )
        await inter.edit_original_message(embed=embed, view=None)

        # Reset
        self.reset_game(inter.channel.id)

    async def guess_player(self, inter: disnake.ApplicationCommandInteraction):

        counter = self.counter.get(inter.channel.id)
        if not counter:
            counter = self.counter[inter.channel.id] = 0

        correct_guesses = self.correct_guesses.get(inter.channel.id)
        if not correct_guesses:
            correct_guesses = self.correct_guesses[inter.channel.id] = 0

        if counter >= self.player_limit:
            return

        player, player_index = self.get_random_player()
        if player.name in self.answers[inter.channel.id]:
            player = await get_new_random_player(player_index)
            player_index = PLAYERS_LIST.index(player)
            
            
        embed = Embed(
            title="What NFL player is this?", description=f"Position: {player.position}"
        )
        embed.set_image(url=await get_player_image(player.name))
        buttons = GuessPlayerButtons(inter, embed, player, player_index)

        message = await inter.edit_original_message(
            content=f"Time Remaining: {int(self.get_time_left())} seconds",
            embed=embed,
            view=buttons,
        )

        def check(m):  # message
            return m.author.id == inter.author.id and m.channel.id == inter.channel.id

        try:
            msg = await self.bot.wait_for(
                "message", timeout=self.get_time_left(), check=check
            )

            current_player_name = buttons.player_name()

            score = await self.calculate_score(current_player_name, msg.content.lower())

            if score >= 75.0:
                self.correct_guesses[inter.channel.id] += 1
                await inter.send("That was right", ephemeral=True, delete_after=1)
            else:
                await inter.send("That was wrong", ephemeral=True, delete_after=1)

        except asyncio.TimeoutError:
            await self.handle_timeout(inter)

        self.counter[inter.channel.id] += 1
        self.answers[inter.channel.id].append(current_player_name)
        await message.edit(embed=embed)
        await self.guess_player(inter)

    async def calculate_score(self, player_name: str, message_content: str) -> float:  

        list_name = player_name.lower().split(' ')
        if player_name.lower() in message_content.lower() or message_content.lower() in list_name:
            return 100.0  
        else:
            return await player_search(player_name, message_content)

    async def handle_timeout(self, inter: disnake.ApplicationCommandInteraction):
        final_score = self.correct_guesses[inter.channel.id]
        max_score = self.player_limit
        answers = self.get_answers(inter.channel.id)

        embed_timeout = Embed(
            title="Game Ended",
            description=f"You got **{final_score}/{max_score} guesses right**\n Time's up! You didn't finish the game in time\n\nCorrect Answers: \n{answers}",
        )
        await inter.edit_original_message(
            embed=embed_timeout, view=None, content="No time remaining"
        )

        self.reset_game(inter.channel.id)

    def get_answers(self, channel_id: int) -> str:
        return "\n".join(
            [f"{i+1}: {player}" for i, player in enumerate(self.answers[channel_id])]
        )

    def reset_game(self, channel_id: int):
        self.counter[channel_id] = 0
        self.correct_guesses[channel_id] = 0
        self.answers[channel_id] = []

    def get_random_player(self):
        player = random.choice(PLAYERS_LIST)
        player_index = PLAYERS_LIST.index(player)
        return player, player_index

    def get_time_left(self) -> float:
        elapsed_time = time.time() - self.start_time
        time_left = self.time_limit - elapsed_time
        return max(0.0, time_left)


def setup(bot):
    bot.add_cog(GamesCommands(bot))