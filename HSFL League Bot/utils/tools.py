import asyncio
import re
import os
from datetime import timedelta

import aiohttp
import disnake
import requests
import unidecode
from colour import Color


from utils.config import Ids, SETTINGS
from utils.database import Database
from utils.embed import Embed

async def guild_members(guild: disnake.Guild, role: disnake.Role = None):
    # Check if the guild is chunked
    if not guild.chunked:
        # If not chunked, chunk the guild first
        await guild.chunk()

    # Return members with or without a specific role
    if role:
        return role.members
    return guild.members


async def search_embed_ids(what_to_search, type_of_id, guild):
    type_info = {
        'role': ('@&', guild.get_role),
        'channel': ('#', guild.get_channel_or_thread),
        'user': ('@', guild.get_or_fetch_member),
    }         

    type, fetch_method = type_info[type_of_id]
    find_teams = re.findall(rf'<{type}(\d+)>', what_to_search)
    ids = [int(match) for match in find_teams]
    ids_list = []
    for id in ids:
        try:
            obj = await fetch_method(id)
        except TypeError:
            obj = fetch_method(id)
        if obj:
            ids_list.append(obj)   
    return ids_list


async def search_role_emoji(guild, name):
    """Tries to find an emoji with the same name as the role."""
    target_name = unidecode.unidecode(name.replace(" ", "")).lower()

    for emoji in guild.emojis:
        emoji_name = unidecode.unidecode(
            emoji.name.replace("BWB_", "").replace("_", "").replace(" ", "")
        ).lower()
        if emoji_name == target_name:
            return emoji

    return None


async def get_font(font: str):
    """Font map, returns all the letters for the font"""
    font_map = {
        ('Ａｅｓｔｈｅｔｉｃ', "aesthetic"): "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ１２３４５６７８９0",
        ('𝗕𝗼𝗹𝗱', 'bold'): "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵𝟬",
        ("Ⓒⓘⓡⓒⓛⓔ", 'circle'): "ⒶⒷⒸⒹⒺⒻⒼⒽⒾⒿⓀⓁⓂⓃⓄⓅⓆⓇⓈⓉⓊⓋⓌⓍⓎⓏⓐⓑⓒⓓⓔⓕⓖⓗⓘⓙⓚⓛⓜⓝⓞⓟⓠⓡⓢⓣⓤⓥⓦⓧⓨⓩ①②③④⑤⑥⑦⑧⑨⓪",
        ("𝑰𝒕𝒂𝒍𝒊𝒄", "italic"): "𝑨𝑩𝑪𝑫𝑬𝑭𝑮𝑯𝑰𝑱𝑲𝑳𝑴𝑵𝑶𝑷𝑸𝑹𝑺𝑻𝑼𝑽𝑾𝑿𝒀𝒁𝒂𝒃𝒄𝒅𝒆𝒇𝒈𝒉𝒊𝒋𝒌𝒍𝒎𝒏𝒐𝒑𝒒𝒓𝒔𝒕𝒖𝒗𝒘𝒙𝒚𝒛1234567890",
        ("𝙄𝙩𝙖𝙡𝙞𝙘𝙗𝙤𝙡𝙙", 'italicbold'): "𝘼𝘽𝘾𝘿𝙀𝙁𝙂𝙃𝙄𝙅𝙆𝙇𝙈𝙉𝙊𝙋𝙌𝙍𝙎𝙏𝙐𝙑𝙒𝙓𝙔𝙕𝙖𝙗𝙘𝙙𝙚𝙛𝙜𝙝𝙞𝙟𝙠𝙡𝙢𝙣𝙤𝙥𝙦𝙧𝙨𝙩𝙪𝙫𝙬𝙭𝙮𝙯1234567890",
        ("𝘐𝘵𝘢𝘭𝘪𝘤𝘴𝘢𝘯𝘴", 'italicsans'): "𝘈𝘉𝘊𝘋𝘌𝘍𝘎𝘏𝘐𝘑𝘒𝘓𝘔𝘕𝘖𝘗𝘘𝘙𝘚𝘛𝘜𝘝𝘞𝘟𝘠𝘡𝘢𝘣𝘤𝘥𝘦𝘧𝘨𝘩𝘪𝘫𝘬𝘭𝘮𝘯𝘰𝘱𝘲𝘳𝘴𝘵𝘶𝘷𝘸𝘹𝘺𝘻1234567890",
        ("𝖲𝖺𝗇𝗌", 'sans'): "𝖠𝖡𝖢𝖣𝖤𝖥𝖦𝖧𝖨𝖩𝖪𝖫𝖬𝖭𝖮𝖯𝖰𝖱𝖲𝖳𝖴𝖵𝖶𝖷𝖸𝖹𝖺𝖻𝖼𝖽𝖾𝖿𝗀𝗁𝗂𝗃𝗄𝗅𝗆𝗇𝗈𝗉𝗊𝗋𝗌𝗍𝗎𝗏𝗐𝗑𝗒𝗓𝟣𝟤𝟥𝟦𝟧𝟨𝟩𝟪𝟫𝟢",
        ("𝐒𝐞𝐫𝐢𝐟", 'serif'): "𝐀𝐁𝐂𝐃𝐄𝐅𝐆𝐇𝐈𝐉𝐊𝐋𝐌𝐍𝐎𝐏𝐐𝐑𝐒𝐓𝐔𝐕𝐖𝐗𝐘𝐙𝐚𝐛𝐜𝐝𝐞𝐟𝐠𝐡𝐢𝐣𝐤𝐥𝐦𝐧𝐨𝐩𝐪𝐫𝐬𝐭𝐮𝐯𝐰𝐱𝐲𝐳𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗𝟎",
    }
    for key in font_map:
        if font in key:
            return font_map[key]
    return None


async def font_message(message: str, font: str):
    """Turns normal text into a font"""
    font_data = await get_font(font)
    translation_table = str.maketrans(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890", font_data
    )
    return message.translate(translation_table)


async def premium_user_check(bot, member: disnake.Member):
    """Checks if a user has the @Premium role in the Bread Kingdom Server"""
    #bk_guild = bot.get_guild(Ids.bk_server)
    #members = await guild_members(bk_guild)
    #if member in members:
    #    member = bk_guild.get_member(member.id)
    #    premium_role = disnake.utils.get(bk_guild.roles, id=Ids.premium_role)
    #    booster_role = disnake.utils.get(bk_guild.roles, id=Ids.boost_role)
    #    if premium_role in member.roles or booster_role in member.roles:
    #        return True

    #return False
    return True
async def premium_guild_check(guild_id):
  #data = await Database.get_data("Premium")
  #if not data:
  #  return False
    
  #for user_id, guild_ids in data.items():
  #  if str(guild_id) in guild_ids:
  #    return True
  #return False    
  return True
async def vote_check(user_id: int):
    #headers = {
    #  "Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjczMDU5NDA5ODY5NTYzNTAxNCIsImJvdCI6dHJ1ZSwiaWF0IjoxNjIxODE3MjM4fQ.yLCCA9hSs1FVH5qktLJKfJxiGOgLL3F5UQ5FXwTQntI"
    #}
    #async with aiohttp.ClientSession(headers=headers) as session:
    #    url = f"https://top.gg/api/bots/730594098695635014/check?userId={user_id}"
    #    async with session.get(url) as response:
    #        json = await response.json()
    #        if json['voted'] > 0:
    #            return True # Voted
    #        return False  
    return True
async def vote_or_premium_user(bot, member):
  """Short hand for using `premium_user_check` and `vote_check` at the same time"""
  #pu = await premium_user_check(bot, member)
  #if pu:
  #  return True
  #vc = await vote_check(member.id)
  #if vc:
  #  return True
  #return False
  return True

async def remove_all_premium_data(member: disnake.Member):
  """Removes all the premium data a user has, includes the guilds they have set"""
  premium_guilds = await Database.get_data("Premium", str(member.id))
        
  if not premium_guilds:
    return
        
  for guild in premium_guilds:
    for value in SETTINGS.values():
      if value['premium']:
        await Database.delete_data(value['table'], str(guild))
          
  await Database.delete_data("Premium", str(member.id))

async def remove_all_guild_data(guild_id):
  """Removes all the data a server has, includes premium data"""
  for value in SETTINGS.values():
    data = await Database.get_data(value['table'], guild_id)
    if data:
      await Database.delete_data(value['table'], guild_id)

    
  await Database.delete_data('Suspensions', guild_id)

  premium = await Database.get_data("Premium")
  if premium:
    for user_id, guild_ids in premium.items():
      if str(guild_id) in guild_ids:
        await Database.delete_data('Premium', f'{user_id}/{guild_id}')
              


async def valid_guild_object(inter, obj):
    """Checks if a user's response is a valid object in their guild (discord role, discord channel, etc.)"""
    try:
        obj_id = int(obj)
    except ValueError:
        return False

    try:
        item = inter.guild.get_role(obj_id) or inter.guild.get_channel_or_thread(obj_id)
        return item
    except ValueError:
        return False

    return False


async def format_database_data(inter, table, guild_id):
    """Shows data of a datatbase in a clean string"""
    data = await Database.get_data(table, guild_id)
    if data == None:
        return "No data"
  
    pretty_data = ""
    if isinstance(data, dict):
        for sub_key, sub_value in data.items():
            object_check = await valid_guild_object(inter, sub_value)
            if object_check:
                pretty_value = object_check.mention
            else:
                pretty_value = str(sub_value)
            pretty_data += f"{sub_key} : {pretty_value}\n"

    elif isinstance(data, list):
        for i, sub_value in enumerate(data):
            object_check = await valid_guild_object(inter, sub_value)
            pretty_value = object_check.mention if object_check else str(sub_value)
            pretty_data += pretty_value
            if i < len(data) - 1:
                pretty_data += ", "
  
    else:
        object_check = await valid_guild_object(inter, data)
        if object_check:
            pretty_value = object_check.mention
        else:
            pretty_value = str(data)
        pretty_data += pretty_value
  
    return pretty_data


async def has_perms(role: disnake.Role):
    """Checks if a role has perms"""
    permissions_to_check = [
        'administrator',
        'ban_members',
        'kick_members',
        'manage_emojis',
        'manage_guild',
        'manage_nicknames',
        'moderate_members',
        'manage_channels'
    ]

    return any(getattr(role.permissions, perm, False) for perm in permissions_to_check)


async def has_role(table, guild_id, member, role_id=None):
    """
    Checks if a user has a role that is in a table

    await has_role("FranchiseRole", ..., ...)
    checks if the user has a role that is in the FranchiseRole table
    """
    data = await Database.get_data(table, guild_id)
    if not data:
      return False
      
    for row in data:
      for role in member.roles:
        if int(role.id) == int(row):
          if role_id == 'id':
            return int(role.id)
          else:  
            return True
            
    return False


async def add_roles(inter, table: str, member: disnake.Member, guild: disnake.Guild = None):
    guild = guild if guild else inter.guild
  
    roles_data = await Database.get_data(table, guild.id)
    if roles_data is None:
        return

    # Handle both list and dict formats
    if isinstance(roles_data, list):
        role_ids = roles_data
    elif isinstance(roles_data, dict):
        role_ids = roles_data.values()
    else:
        return

    for role_id in role_ids:
        try:
            role = guild.get_role(int(role_id))
            if role:
                await member.add_roles(role)
        except disnake.NotFound:
            embed = Embed().quick_embed("Roles Warning", f"Role with ID {role_id} not found").warn_embed()
            await inter.send(embed=embed)
        except disnake.Forbidden:
            embed = Embed().quick_embed("Roles Warning", f"Permission denied to add role with ID {role_id} to {member.display_name}").warn_embed()
            await inter.send(embed=embed)
        except Exception as e:
            embed = Embed().quick_embed("Roles Warning", f"An error occurred while adding roles:\n\n{e}").warn_embed()
            await inter.send(embed=embed)


async def remove_roles(inter, table: str, member: disnake.Member, guild: disnake.Guild = None):
    guild = guild if guild else inter.guild
  
    roles_data = await Database.get_data(table, guild.id)
    if roles_data is None:
        return

    # Handle both list and dict formats
    if isinstance(roles_data, list):
        role_ids = roles_data
    elif isinstance(roles_data, dict):
        role_ids = roles_data.values()
    else:
        return

    for role_id in role_ids:
        try:
            role = guild.get_role(int(role_id))
            if role:
                await member.remove_roles(role)
        except disnake.NotFound:
            embed = Embed().quick_embed("Roles Warning", f"Role with ID {role_id} not found").warn_embed()
            await inter.send(embed=embed)
        except disnake.Forbidden:
            embed = Embed().quick_embed("Roles Warning", f"Permission denied to remove role with ID {role_id} to {member.display_name}").warn_embed()
            await inter.send(embed=embed)
        except Exception as e:
            embed = Embed().quick_embed("Roles Warning", f"An error occurred while removing roles:\n\n{e}").warn_embed()
            await inter.send(embed=embed)


async def get_mentions(items: list, guild: disnake.Guild):
    """Returns a list of mentions for roles and channels with the given IDs"""
    mentions = []
    for item_id in items:
        item = guild.get_role(int(item_id)) or guild.get_channel_or_thread(int(item_id))
        if item:
            mentions.append(item.mention)
    return mentions


async def get_user_response(self, inter, timeout: int = 30):
    """Gets a users response"""
    def check(m):
        return (m.author.id == inter.author.id)
    try:
        msg = await self.bot.wait_for("message", timeout=timeout, check=check)
      
        return msg.content

    except asyncio.TimeoutError:
        return await inter.send("Response timed out", ephemeral=True)


async def parse_duration(duration_str: str):
    duration_units = {
        "s": "seconds",
        "m": "minutes",
        "h": "hours",
        "d": "days",
        "w": "weeks",
        "second": "seconds",
        "seconds": "seconds",
        "minute": "minutes",
        "minutes": "minutes",
        "hour": "hours",
        "hours": "hours",
        "day": "days",
        "days": "days",
        "week": "weeks",
        "weeks": "weeks",
    }

    duration_pattern = re.compile(r"(\d+)\s*([a-z]+)", re.IGNORECASE)

    total_duration = timedelta()
    for match in duration_pattern.finditer(duration_str):
        value = int(match.group(1))
        unit = match.group(2).lower()
        if unit in duration_units:
            duration_unit = duration_units[unit]
            total_duration += timedelta(**{duration_unit: value})
        else:
            return None

    return total_duration


def make_discord_message(
    username: str,
    avatar_url: str, 
    timestamp: str, 
    content_list: list,
    username_color: str = "#FFFFFF"
):

    data = {
        "username": username,
        "avatar_url": avatar_url,
        "timestamp": timestamp,
        "content_list": content_list,
        "username_color": username_color,
    }
    response = requests.post("https://breadwinner.dev/generate_message", json=data)
    json = response.json()
    image_id = json['image_id']
  
    return f"https://breadwinner.dev/{image_id}"


# All made by ChatGPT lol

def lighten_color(hex_code, amount: int):
    # 0.0 - 1.0
    # Convert hex code to RGB
    hex_code = hex_code.lstrip('#')
    rgb = tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))

    # Calculate the lighter RGB values
    lighter_rgb = tuple(int(min(255, max(0, c + (255 - c) * amount))) for c in rgb)

    # Convert the lighter RGB values back to hex
    lighter_hex = '#%02x%02x%02x' % lighter_rgb

    return lighter_hex

def darken_color(hex_code, amount: int):
    # 0.0 - 1.0
    # Convert hex code to RGB
    hex_code = hex_code.lstrip('#')
    rgb = tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))

    # Calculate the darker RGB values
    darker_rgb = tuple(int(max(0, c - c * amount)) for c in rgb)

    # Convert the darker RGB values back to hex
    darker_hex = '#%02x%02x%02x' % darker_rgb

    return darker_hex


def adjust_saturation(hex_color, amount):
    # between 0.0 and 1.0
    color = Color(hex_color)
    color.saturation = amount
    return color.hex

def adjust_hue(hex_color: str, amount: float) -> str:
    #360 but wraps around
    # Convert hex code to RGB
    hex_color = hex_color.lstrip('#')
    rgb = tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))  # Normalize RGB values

    # Create a color object
    color = Color(rgb=rgb)

    # Convert RGB to HSL (Hue, Saturation, Lightness)
    hsl = list(color.get_hsl())

    # Adjust the hue
    hsl[0] += amount / 360.0  # Convert the amount from degrees to normalized value

    # Normalize the hue value to stay within the range [0, 1]
    hsl[0] = hsl[0] % 1.0

    # Convert HSL back to RGB
    adjusted_color = Color(hsl=tuple(hsl))
    adjusted_rgb = tuple(int(c * 255) for c in adjusted_color.rgb)  # Denormalize RGB values

    # Convert the adjusted RGB values back to hex
    adjusted_hex = "#{:02x}{:02x}{:02x}".format(*adjusted_rgb)

    return adjusted_hex