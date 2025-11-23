import disnake, os, traceback, warnings, asyncio, logging
from disnake.ext import commands
from dotenv import load_dotenv
from utils.database import Database

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] [%(name)s] %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

# Suppress sync warnings for guilds where bot doesn't have permissions (403 errors)
# These warnings occur when the bot tries to sync commands to test guilds it doesn't have access to
warnings.filterwarnings("ignore", message=".*Failed to overwrite commands.*")
warnings.filterwarnings("ignore", message=".*SyncWarning.*")

intents = disnake.Intents.default()
intents.message_content = True
intents.members = True

disnake.Embed.set_default_color(0xECDEC1)


class Bread(commands.AutoShardedInteractionBot):
    def __init__(self):
        # Removed test_guilds to allow global command syncing to all servers
        super().__init__(intents=intents, activity=disnake.Game(name="nothing"), allowed_mentions=disnake.AllowedMentions(roles=False, everyone=False, users=False), chunk_guilds_at_startup = False, sync_commands_debug=False)
        self.bot = self

    async def start(self, *args, **kwargs):
      logger.info("Initializing database...")
      db_instance = Database()
      
      logger.info("Verifying database integrity...")
      try:
        integrity_report = await Database.verify_integrity()
        if integrity_report["corrupted"] > 0:
          logger.warning(f"Found {integrity_report['corrupted']} corrupted files")
          logger.info(f"Successfully recovered {integrity_report['recovered']} files")
        else:
          logger.info("All database files healthy")
        
        if integrity_report["errors"]:
          logger.error("Errors during database verification:")
          for error in integrity_report["errors"]:
            logger.error(f"  {error}")
      except Exception as e:
        logger.error(f"Error during integrity check: {e}", exc_info=True)

      logger.info("Loading cogs...")
      for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
          try:
            self.bot.load_extension(f'cogs.{filename[:-3]}')
            logger.info(f"Loaded cog: {filename}")
          except Exception as e:
            logger.error(f"Error loading {filename}: {e}", exc_info=True)
  
      await super().start(*args)
  
    async def on_ready(self):
      logger.info('Bot Online')
      logger.info(f'Logged in as {self.user}')
      logger.info(f'Bot is in {len(self.guilds)} guilds')
      
      # Commands will sync automatically with AutoShardedInteractionBot
      # Manual sync can be done via the /sync command if needed

bot = Bread()

@bot.slash_command()
@commands.is_owner()
async def load(inter, cogname: str):
    """
    Loads a cog
    Parameters
    ----------
    cogname: The cog to load
    """
    try:
      bot.load_extension(f"cogs.{cogname}")
    except Exception as e:
      await inter.response.send_message(
        f"```py\n{traceback.format_exc()}\n```\n\n{e}")
    else:
      await inter.response.send_message(
        f":gear: Successfully Loaded **{cogname}** Module!") 

@bot.slash_command()
@commands.is_owner()
async def unload(inter, cogname: str):
    """
    Unloads a cog
    Parameters
    ----------
    cogname: The cog to unload
    """
    try:
      bot.unload_extension(f"cogs.{cogname}")
    except Exception as e:
      await inter.response.send_message(
        f"```py\n{traceback.format_exc()}\n```\n\n{e}")
    else:
      await inter.response.send_message(
        f":gear: Successfully Unloaded **{cogname}** Module!")

@bot.slash_command()
@commands.is_owner()
async def reload(inter, cogname: str):
    """
    Loads and unloads a cog
    Parameters
    ----------
    cogname: The cog to reload
    """
    try:
      bot.unload_extension(f"cogs.{cogname}")
      bot.load_extension(f"cogs.{cogname}")
    except Exception as e:
      await inter.response.send_message(
        f"```py\n{traceback.format_exc()}\n```\n\n\n, {e}")
    else:
      await inter.response.send_message(
        f":gear: Successfully Reloaded the **{cogname}** module!")

@bot.slash_command()
@commands.is_owner()
async def sync(inter):
    """
    Syncs slash commands to Discord (owner only)
    Use this if commands don't appear after starting the bot
    """
    try:
      if hasattr(bot, 'tree') and bot.tree:
        synced = await bot.tree.sync()
        await inter.response.send_message(f"✅ Synced {len(synced)} command(s) to Discord!")
        print(f"Commands synced manually by {inter.author}")
      else:
        await inter.response.send_message("❌ Command tree not available. Commands should sync automatically.")
    except Exception as e:
      await inter.response.send_message(f"❌ Failed to sync commands: {e}")
            
token = os.getenv("DISCORD_TOKEN")
if not token:
    raise ValueError("DISCORD_TOKEN environment variable not set. Create a .env file with your bot token.")
bot.run(token)
