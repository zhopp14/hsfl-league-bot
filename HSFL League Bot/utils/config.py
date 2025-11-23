from utils.emojis import Emojis
from utils.roles import Roles

class Links:
    template_server = "https://discord.gg/xQs94q4bvE"
    support_server = "https://discord.gg/cT9rmtf"

    breadwinner_invite = "https://discord.com/oauth2/authorize?client_id=730594098695635014&permissions=314432&scope=bot%20applications.commands"

    roblox_group = "https://www.roblox.com/groups/9861497/Bread-Winner-V2#!/about"
    roblox_group_store = "https://www.roblox.com/groups/9861497/Bread-Winner-V2#!/store"

    youtube_channel = ("https://www.youtube.com/channel/UCQY8Yq4RXRdThDbKyLGmTtA",)
    signing_video = "https://youtu.be/GIic9B7QIXQ"

    topgg = "https://top.gg/bot/730594098695635014"
    topgg_vote = "https://top.gg/bot/730594098695635014/vote"

    premium_link = "https://www.patreon.com/BreadWinnerB"


class Colors:
    red = 0xFF0000
    yellow = 0xFFFF00
    green = 0x00800
    blue = 0x0000FF
    light_blue = 0x09a1b8
    
    # Bot Colors
    raffia = 0xECDEC1 # tan
    raw_umber = 0x693C1E # brown
    fuzzy_wuzzy_brown = 0xC15B4E # light red
    white = 0xFFFFFF

class Images:
    bot_logo = "https://breadwinner.dev/images/bwb_logo.png"
    info = "https://cdn.discordapp.com/emojis/1071919537357869098.png"
    inquiry = "https://cdn.discordapp.com/emojis/1071919527086002208.png"
    prohibited = "https://cdn.discordapp.com/emojis/1071919518106005574.png"
    warn = "https://cdn.discordapp.com/emojis/1071919508702380122.png"

class BotEmojis:
    check_mark = "✅"
    x_mark = "❌"
  
    info = "ℹ️"
    inquiry = "❓"

  
    prohibited = "⛔"
    warn = "⚠️"

class Ids:
  bk_server = 731297050880376832
  premium_role = 1135639148460507146
  premium_lite_role = 1153139505033920564
  boost_role = 816853222781091851 
  bread_logs_channel = 1088251834369593455
  bi_log_channel = 1136061620498477150 # bread ideas


# auto setup keywords
class Keywords:
  FRANCHISE_ROLES_KEYWORDS = ["franchise owner", "university president", "athletic director", "governor", "club owner", "sports director", "coach", "manager"]
  FREE_AGENT_ROLES_KEYWORDS = ["free age"]
  SUSPENED_ROLES_KEYWORDS = ['suspened', 'suspension']
  TRANSACTION_CHANNELS_KEYWORDS = ["transaction", 'sign', 'release', 'promote', 'demote']
  TEAM_ROLES_KEYWORDS = Roles.nfl + Roles.nba + Roles.mlb + Roles.nhl + Roles.soccer + Roles.fcf + Roles.usfl + Roles.xfl + Roles.football_fusion + Roles.ultimate_football + Roles.college
  OFFER_CHANNELS_KEYWORDS = ["offer", 'free agent', 'free agency', 'agencie']
  DEMAND_CHANNELS_KEYWORDS = ["demand"]

SPORTS_LEAGUES = [
    {'league': 'NFL', 'emoji': Emojis.nfl_logos[6]},
    {'league': 'NBA', 'emoji': Emojis.nba_logos[4]},
    {'league': 'MLB', 'emoji': Emojis.mlb_logos[2]},
    {'league': 'NHL', 'emoji': Emojis.nhl_logos[2]},
    {'league': 'Soccer', 'emoji': Emojis.soccer[0]},
    {'league': 'FCF', 'emoji': Emojis.fcf[0]},
    {'league': 'USFL', 'emoji': Emojis.usfl[0]},
    {'league': 'XFL', 'emoji': Emojis.xfl[0]},
    {'league': 'Football Fusion', 'emoji': Emojis.football_fusion[2]},
    {'league': 'Ultimate Football', 'emoji': Emojis.ultimate_football[0]},
    {'league': 'College', 'emoji': Emojis.college_conferences[8]}
]

# messages

not_premium_message = f"You are not a premium user or not in a premium guild {Links.premium_link}"

vote_locked_message = f"To use access feature you have to vote for the bot: {Links.topgg_vote}"

welcome_message = f"<:3DBreadWinnerB:939604485142093844> **Thanks for inviting me to your server** <:3DBreadWinnerB:939604485142093844>\n\n**See my commands with:** `/cmds`\nIf you ever need help, come stop by to my home\n{Links.support_server}"

error_support_message = f"`Having issues or need more help? Try joining the support server:` <{Links.support_server}>"

# data

FONTS_LIST = [
    "Ａｅｓｔｈｅｔｉｃ",
    "𝗕𝗼𝗹𝗱",
    "Ⓒⓘⓡⓒⓛⓔ",
    "𝑰𝒕𝒂𝒍𝒊𝒄",
    "𝙄𝙩𝙖𝙡𝙞𝙘𝙗𝙤𝙡𝙙",
    "𝘐𝘵𝘢𝘭𝘪𝘤𝘴𝘢𝘯𝘴",
    "𝖲𝖺𝗇𝗌",
    "𝐒𝐞𝐫𝐢𝐟",
]

# new type of setting, setup time - time before you can demand
SETTINGS = {
    "Franchise Role": {
        "name": "Franchise Role",
        "table": "FranchiseRole",
        "guild": True,
        "premium": False,
        "premium_max": 10,
        "max": 5,
        "desc": "Roles that are able to use: `/offer`, `/release`, `/promote`, `/demote`",
    },
    "Free Agent Role": {
        "name": "Free Agent Role",
        "table": "FreeAgentRole",
        "guild": True,
        "premium": False,
        "premium_max": 10,
        "max": 5,
        "desc": "Roles that get removed when signed and added when released or if a user demands",
    },
    "After Sign Role": {
        "name": "After Sign Role",
        "table": "AfterSignRole",
        "guild": True,
        "premium": False,
        "premium_max": 10,
        "max": 5,
        "desc": "Roles that get added after a user is signed and removed when a user is released",
    },
    "Pickup Host Role": {
        "name": "Pickup Host Role",
        "table": "PickupHostRole",
        "guild": True,
        "premium": False,
        "premium_max": 3,
        "max": 1,
        "desc": "Roles that are able to use pickup commands",
    },  
    "Pickup Role": {
        "name": "Pickup Role",
        "table": "PickupRole",
        "guild": True,
        "premium": False,
        "premium_max": 3,
        "max": 1,
        "desc": "Roles that get pinged for pickup commands",
    },    
    "Team Role": {
        "name": "Team Role",
        "table": "TeamRole",
        "guild": True,
        "premium": True,
        "premium_max": 80,
        "max": 25, # can only grab up to 25 roles in a select
        "desc": "Roles that get used in signing commands (You can only add 25 teams at a time, but you can add up to 80)",
    },  
    "Ring Roles": {
        "name": "Ring Roles",
        "table": "RingRole",
        "guild": True,
        "premium": False,
        "premium_max": 3,
        "max": 1, 
        "desc": "For users to show off there rings",
    },      
    "Referee Role": {
        "name": "Referee Role",
        "table": "RefereeRole",
        "guild": True,
        "premium": False,
        "premium_max": 3,
        "max": 1, 
        "desc": "Roles that get used for anything referee related",
    },   
    "Steamer Role": {
        "name": "Steamer Role",
        "table": "StreamerRole",
        "guild": True,
        "premium": False,
        "premium_max": 3,
        "max": 1, 
        "desc": "Roles that get used for anything stream related",
    },        
    "Suspension Role": {
        "name": "Suspension Role",
        "table": "SuspensionRole",
        "guild": True,
        "premium": True,
        "premium_max": 3,
        "max": 1,
        "desc": "Roles that get added after a user is suspended and removed when there unsuspended",
    },   
    "Signing Channel": {
        "name": "Signing Channel",
        "table": "SigningChannel",
        "guild": True,
        "premium": False,
        "premium_max": 3,
        "max": 1,
        "desc": "Channels where: `/release`, `/promote`, `/demote` are able to be used",
    },
    "Offering Channel": {
        "name": "Offering Channel",
        "table": "OfferingChannel",
        "guild": True,
        "premium": False,
        "premium_max": 3,
        "max": 1,
        "desc": "Channels where: `/offer` can be used",
    },
    "Demanding Channel": {
        "name": "Demanding Channel",
        "table": "DemandingChannel",
        "guild": True,
        "premium": False,
        "premium_max": 3,
        "max": 1,
        "desc": "Channels where: `/demand` can be used",
    },
    "Trading Channel": {
        "name": "Trading Channel",
        "table": "TradingChannel",
        "guild": True,
        "premium": False,
        "premium_max": 1,
        "max": 1,
        "desc": "Channels where: All things related to trades are sent",
    },
    "Referee Channel": {
        "name": "Referee Channel",
        "table": "RefereeChannel",
        "guild": True,
        "premium": False,
        "premium_max": 1,
        "max": 1,
        "desc": "Channels where: All things related to referees are sent",
    },    
    "Pickup Channel": {
        "name": "Pickup Channel",
        "table": "PickupChannel",
        "guild": True,
        "premium": False,
        "premium_max": 3,
        "max": 1,
        "desc": "Channels where pickups are sent",
    },  
    "Streaming Channel": {
        "name": "Streaming Channel",
        "table": "StreamingChannel",
        "guild": True,
        "premium": False,
        "premium_max": 3,
        "max": 1,
        "desc": "Channels where: All things related to referees are sent",
    },     
    "Notfication Channel": {
        "name": "Notfication Channel",
        "table": "NotficationChannel",
        "guild": True,
        "premium": True,
        "premium_max": 3,
        "max": 1,
        "desc": "Where various messages get send like: suspensions, roles/channels added and removed from the bot and other things like that"
    },

    # Use different code, saved as `int` in database, 'max' is for a range, no premium_max
    "Limit RosterCap": {
        "name": "Roster Cap",
        "table": "RosterCap",
        "guild": True,
        "premium": True,
        "max": 52,
        "desc": "Determines the amount of users that can be on a team at one time",
    },
    "Limit Demand": {
        "name": "Demand Limit",
        "table": "DemandLimit",
        "guild": True,
        "premium": True,
        "max": 10,
        "desc": "Determines the amount of times a player can demand",
    },  
    #"Limit SalaryCap": {
    #    "name": "Salary Cap",
    #    "table": "SalaryCap",
    #    "guild": True,
    #    "premium": True,
    #    "max": 1000000000, # i billion, ig
    #    "desc": "Determines the amount of salary that can be used on a team",
    #},
  
    # use different code and have no max
    "Toggle Signing": {
        "name": "Signing",
        "table": "Signing",
        "guild": True,
        "premium": False,
        "on_status": None,
        "desc": "Determines if: `/offer`, `/release`, `/promote`, `/demote` are able to be used",
    },
    "Toggle Demand": {
        "name": "Demands",
        "table": "Demand",
        "guild": True,
        "premium": False,
        "on_status": None,
        "desc": "Determines if: `/demand` can be used",
    },
    "Toggle GhostPing": {
        "name": "Ghost Ping System",
        "table": "GhostPing",
        "guild": True,
        "premium": False,
        "on_status": None,
        "desc": "Determines if the Ghost Ping:tm: System will activate ",
    },
    "Toggle OfferDMs": {
        "name": "Offer DMs System",
        "table": "OfferDM",
        "guild": True,
        "premium": True,
        "on_status": "On",
        "desc": "Determines if users click the accept and decline offer buttons in the server or in their DMs",
    },  
}
