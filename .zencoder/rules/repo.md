---
description: Repository Information Overview
alwaysApply: true
---

# HSFL League Bot Information

## Summary
HSFL League Bot (codenamed "Bread Bot") is a feature-rich Discord bot built with disnake that manages fantasy sports leagues, player rosters, drafts, trades, and signing events. The bot uses Firebase for data integration and provides modular functionality through 25 specialized cogs, handling everything from league management to player statistics and team organization.

## Structure
- **main.py**: Bot entry point with `AutoShardedInteractionBot` implementation, intents configuration, and cog loader
- **cogs/** (25 modules): Modular command handlers including league management, drafts, trades, pickups, role management, events, emojis, fonts, and media handling
- **utils/** (8 modules): Utility modules for configuration, embeddings, database operations, role management, signing tools, and tools
- **database/** (10 JSON files): Local storage for channels (notification, referee, pickup, offering, signing, streaming), franchise roles, suspensions, and user data
- **service-account.json**: Google Firebase service account credentials (project_id: forward-vial-425500-s3)

## Language & Runtime
**Language**: Python  
**Version**: 3.13.2  
**Framework**: disnake 2.x (Discord.py fork)  
**Bot Architecture**: AutoShardedInteractionBot with global command syncing

## Dependencies
**Main Dependencies**:
- `disnake`: Discord bot framework with slash commands and interactions
- `aiohttp`: Async HTTP client for API calls
- `google-cloud-*`: Firebase/Google Cloud integration
- `beautifulsoup4` (bs4): HTML/XML parsing
- `fuzzywuzzy`: Fuzzy string matching for player name matching
- `requests`: HTTP library
- `unidecode`: Unicode text conversion

**Development Tools**:
- Python 3.13.2 (built-in: asyncio, json, io, datetime, typing, re, csv, pathlib, random, collections)

## Application Structure

### Main Entry Point
**main.py** (main.py:1-70):
- Initializes `AutoShardedInteractionBot` with intents (message_content, members enabled)
- Default embed color: `0xECDEC1` (tan)
- Dynamically loads all cogs from `./cogs` directory on startup
- Slash commands: `/load` (owner-only cog loader), auto-sync enabled

### Core Modules

**Cog System** (25 command modules):
- **league.py**: League creation, management, and statistics
- **draft.py**: Draft mechanics and management
- **trade.py**: Trade processing and validation
- **pickups.py**: Player pickup system
- **sign.py**: Player signing and registration
- **suspended.py**: Suspension management with datetime tracking
- **roles.py**: Discord role creation and color management (HSL adjustment)
- **role_manager.py**: Role assignment and management tools
- **database_manager.py, import.py, export.py**: Data persistence (IO, JSON)
- **events.py**: Event handling and notifications
- **emojis.py, fonts.py, symbol.py**: Custom emoji and font management
- **image.py**: Image generation and processing
- **templates.py, league_messages.py**: Message templating
- **mod.py, fun.py, guess_player.py**: Moderation and entertainment
- **snipe.py**: Message sniping functionality
- **utils.py**: Generic utility commands

**Utils Module** (8 utilities):
- **config.py**: Configuration classes (Links, Colors, Images, BotEmojis, Emojis, Ids, Roles, Settings, SPORTS_LEAGUES, FONTS_LIST)
- **embed.py**: Custom embed wrapper
- **database.py**: JSON database operations
- **tools.py**: Utility functions (premium checks, role adjustments, responses, formatting)
- **signing_tools.py**: Signing event utilities with notification
- **roles.py**: Role mapping and data
- **emojis.py**: Emoji definitions
- **paginator.py**: Pagination utilities

### Data Storage
**JSON Database** (10 files in `database/`):
- Channel configurations: NotficationChannel, RefereeChannel, PickupChannel, OfferingChannel, SigningChannel, StreamingChannel
- Settings: FranchiseRole, AutoUpdateRoles, Suspensions
- User data: Users

## Build & Installation

**Prerequisites**:
- Python 3.13+
- Discord bot token with appropriate permissions
- Google Firebase service account JSON

**Installation**:
```bash
pip install disnake aiohttp google-cloud beautifulsoup4 fuzzywuzzy requests unidecode
```

**Running the Bot**:
```bash
python main.py
```

The bot loads all cogs automatically on startup from the `cogs/` directory and connects with sharding support enabled.

## Configuration

**Main Configuration** (utils/config.py):
- **Links**: Discord servers, OAuth2, Roblox group, YouTube, Top.gg voting
- **Colors**: Branding colors (raffia tan, brown, light red, white, blues)
- **Emojis**: 50+ custom emoji mappings for league status, roles, teams
- **Images**: Bot logo and status indicator URLs
- **Ids**: Discord role/channel/user IDs
- **Settings**: Premium features, league rules, sports league configs
- **Sports Leagues**: League-specific configuration

**Firebase Integration**:
- Service account authentication via `service-account.json`
- Project ID: forward-vial-425500-s3

## Key Features
- **Slash Commands**: Full slash command support with global syncing
- **Modular Architecture**: 25 independent cogs loaded dynamically
- **Premium System**: Premium user checks and exclusive features
- **Fuzzy Matching**: Player name matching with fuzzywuzzy
- **HTML Parsing**: Web scraping capabilities with BeautifulSoup
- **Async Operations**: Full async/await support with aiohttp
- **Role Management**: HSL color adjustment and role creation
- **Message Sniping**: Message capture and recovery
- **Event System**: Custom event handling and notifications
- **Data Export**: CSV/JSON export functionality
