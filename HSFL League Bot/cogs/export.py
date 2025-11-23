"""
Data Export Cog
Provides comprehensive data export functionality with multiple formats
Allows exporting user data, contracts, demands, and statistics in CSV or JSON format
"""

import csv
import io
import json
from datetime import datetime
from typing import Optional, Dict, List, Any

import disnake
from disnake.ext import commands

from utils.config import BotEmojis
from utils.database import Database
from utils.embed import Embed
from utils.tools import has_role, premium_guild_check


class ExportFormatView(disnake.ui.View):
    """View for selecting export format"""
    
    def __init__(self, bot, inter, data_type):
        super().__init__(timeout=300.0)
        self.bot = bot
        self.inter = inter
        self.data_type = data_type
    
    async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
        if inter.author.id != self.inter.author.id:
            await inter.response.send_message("This is not your menu!", ephemeral=True)
            return False
        return True
    
    async def on_timeout(self):
        try:
            await self.inter.edit_original_message(
                view=None,
                content="Export menu has expired. Run `/export` again to use it.",
            )
        except Exception:
            pass
    
    @disnake.ui.button(label="CSV Format", style=disnake.ButtonStyle.green, emoji="📊", row=0)
    async def csv_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.defer()
        await ExportCommands(self.bot).export_data(inter, self.data_type, "csv")
    
    @disnake.ui.button(label="JSON Format", style=disnake.ButtonStyle.blurple, emoji="📄", row=0)
    async def json_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.defer()
        await ExportCommands(self.bot).export_data(inter, self.data_type, "json")
    
    @disnake.ui.button(label="Cancel", style=disnake.ButtonStyle.red, row=0)
    async def cancel_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.edit_message(
            view=None,
            content="Export cancelled.",
        )


class ExportCommands(commands.Cog):
    """
    Handles exporting data from the database
    Supports CSV and JSON formats for various data types
    """
    
    def __init__(self, bot):
        self.bot = bot
    
    async def get_all_user_data(self, guild_id: int) -> Dict[str, Any]:
        """
        Retrieves all user data for a guild
        Returns a dictionary mapping user_id to user data
        """
        try:
            user_data = await Database.get_data("Users", str(guild_id))
            if user_data is None or not isinstance(user_data, dict):
                return {}
            return user_data
        except Exception as e:
            print(f"Error getting user data: {e}")
            return {}
    
    async def format_user_data_for_csv(self, guild: disnake.Guild, user_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Formats user data into CSV-friendly format
        Flattens nested structures and includes user information
        """
        csv_rows = []
        
        for user_id_str, user_info in user_data.items():
            try:
                user_id = int(user_id_str)
                member = guild.get_member(user_id)
                
                row = {
                    'user_id': user_id,
                    'discord_id': user_id,
                    'username': member.name if member else 'Unknown',
                    'display_name': member.display_name if member else 'Unknown',
                }
                
                if isinstance(user_info, dict):
                    # Add contract if exists
                    if 'contract' in user_info:
                        row['contract'] = user_info['contract']
                    
                    # Add demands if exists
                    if 'demands' in user_info:
                        row['demands'] = user_info['demands']
                    
                    # Add drafted info if exists
                    if 'drafted' in user_info:
                        row['drafted'] = user_info['drafted']
                    
                    # Flatten stats if they exist
                    if 'stats' in user_info and isinstance(user_info['stats'], dict):
                        for stat_key, stat_value in user_info['stats'].items():
                            row[f'stats_{stat_key}'] = stat_value
                    
                    # Add any other fields
                    for key, value in user_info.items():
                        if key not in ['contract', 'demands', 'drafted', 'stats']:
                            if isinstance(value, (str, int, float, bool)):
                                row[key] = value
                            elif isinstance(value, dict):
                                # Flatten nested dicts
                                for nested_key, nested_value in value.items():
                                    row[f'{key}_{nested_key}'] = nested_value
                            else:
                                row[key] = str(value)
                
                csv_rows.append(row)
            except (ValueError, TypeError) as e:
                print(f"Error processing user {user_id_str}: {e}")
                continue
        
        return csv_rows
    
    async def create_csv_file(self, data: List[Dict[str, Any]], filename: str) -> disnake.File:
        """
        Creates a CSV file from data
        """
        if not data:
            raise ValueError("No data to export")
        
        # Get all unique keys from all rows
        all_keys = set()
        for row in data:
            all_keys.update(row.keys())
        
        # Sort keys for consistent column order
        fieldnames = sorted(all_keys)
        # Put important fields first
        priority_fields = ['user_id', 'discord_id', 'username', 'display_name', 'contract', 'demands', 'drafted']
        fieldnames = [f for f in priority_fields if f in fieldnames] + [f for f in fieldnames if f not in priority_fields]
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(data)
        
        # Convert to bytes
        csv_bytes = output.getvalue().encode('utf-8-sig')  # UTF-8 with BOM for Excel compatibility
        output.close()
        
        # Create Discord file
        file_obj = io.BytesIO(csv_bytes)
        return disnake.File(file_obj, filename=filename)
    
    async def create_json_file(self, data: Dict[str, Any], filename: str) -> disnake.File:
        """
        Creates a JSON file from data
        """
        if not data:
            raise ValueError("No data to export")
        
        # Create JSON in memory
        json_str = json.dumps(data, indent=2, ensure_ascii=False, default=str)
        json_bytes = json_str.encode('utf-8')
        
        # Create Discord file
        file_obj = io.BytesIO(json_bytes)
        return disnake.File(file_obj, filename=filename)
    
    async def export_data(self, inter: disnake.MessageInteraction, data_type: str, format_type: str):
        """
        Main export function
        """
        try:
            await inter.send("🔄 Preparing export... This may take a moment.", ephemeral=True)
            
            guild_id = inter.guild.id
            
            if data_type == "users":
                # Export all user data
                user_data = await self.get_all_user_data(guild_id)
                
                if not user_data:
                    return await inter.send(
                        f"{BotEmojis.x_mark} No user data found to export.",
                        ephemeral=True
                    )
                
                if format_type == "csv":
                    # Format for CSV
                    csv_data = await self.format_user_data_for_csv(inter.guild, user_data)
                    
                    if not csv_data:
                        return await inter.send(
                            f"{BotEmojis.x_mark} No valid user data to export.",
                            ephemeral=True
                        )
                    
                    # Create filename with timestamp
                    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                    filename = f"{inter.guild.name}_users_export_{timestamp}.csv"
                    filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).strip()
                    
                    file = await self.create_csv_file(csv_data, filename)
                    
                    # Create summary embed
                    embed = Embed(
                        title="📊 Export Complete - CSV Format",
                        description=f"Successfully exported user data from **{inter.guild.name}**",
                        color=disnake.Color.green()
                    )
                    
                    embed.add_field(
                        name="📈 Export Statistics",
                        value=f"**Total Users:** {len(csv_data)}\n**Columns:** {len(csv_data[0].keys()) if csv_data else 0}\n**Format:** CSV (Excel Compatible)",
                        inline=False
                    )
                    
                    embed.add_field(
                        name="📋 Included Data",
                        value="• User IDs & Names\n• Contracts\n• Demands\n• Draft Information\n• Statistics\n• All Custom Fields",
                        inline=False
                    )
                    
                    embed.set_footer(text=f"Exported by {inter.author.display_name} • {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
                    
                    await inter.send(embed=embed, file=file, ephemeral=True)
                
                elif format_type == "json":
                    # Format for JSON (keep structure)
                    json_data = {
                        "guild_id": str(guild_id),
                        "guild_name": inter.guild.name,
                        "export_date": datetime.utcnow().isoformat(),
                        "total_users": len(user_data),
                        "users": user_data
                    }
                    
                    # Create filename with timestamp
                    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                    filename = f"{inter.guild.name}_users_export_{timestamp}.json"
                    filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).strip()
                    
                    file = await self.create_json_file(json_data, filename)
                    
                    # Create summary embed
                    embed = Embed(
                        title="📄 Export Complete - JSON Format",
                        description=f"Successfully exported user data from **{inter.guild.name}**",
                        color=disnake.Color.blue()
                    )
                    
                    embed.add_field(
                        name="📈 Export Statistics",
                        value=f"**Total Users:** {len(user_data)}\n**Format:** JSON (Structured Data)\n**Size:** {len(json.dumps(json_data, default=str))} characters",
                        inline=False
                    )
                    
                    embed.add_field(
                        name="📋 Data Structure",
                        value="• Complete nested structure preserved\n• All user fields included\n• Ready for import/backup\n• Machine-readable format",
                        inline=False
                    )
                    
                    embed.set_footer(text=f"Exported by {inter.author.display_name} • {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
                    
                    await inter.send(embed=embed, file=file, ephemeral=True)
            
            elif data_type == "contracts":
                # Export only contract data
                user_data = await self.get_all_user_data(guild_id)
                contract_data = {}
                
                for user_id_str, user_info in user_data.items():
                    if isinstance(user_info, dict) and 'contract' in user_info:
                        contract_data[user_id_str] = {
                            'user_id': user_id_str,
                            'contract': user_info['contract']
                        }
                
                if not contract_data:
                    return await inter.send(
                        f"{BotEmojis.x_mark} No contract data found to export.",
                        ephemeral=True
                    )
                
                if format_type == "csv":
                    csv_rows = []
                    for user_id_str, contract_info in contract_data.items():
                        try:
                            user_id = int(user_id_str)
                            member = inter.guild.get_member(user_id)
                            csv_rows.append({
                                'user_id': user_id,
                                'discord_id': user_id,
                                'username': member.name if member else 'Unknown',
                                'display_name': member.display_name if member else 'Unknown',
                                'contract': contract_info['contract']
                            })
                        except (ValueError, TypeError):
                            continue
                    
                    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                    filename = f"{inter.guild.name}_contracts_export_{timestamp}.csv"
                    filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).strip()
                    
                    file = await self.create_csv_file(csv_rows, filename)
                    
                    embed = Embed(
                        title="📊 Contracts Export - CSV Format",
                        description=f"Successfully exported contract data",
                        color=disnake.Color.green()
                    )
                    embed.add_field(name="📈 Statistics", value=f"**Total Contracts:** {len(csv_rows)}", inline=False)
                    embed.set_footer(text=f"Exported by {inter.author.display_name}")
                    
                    await inter.send(embed=embed, file=file, ephemeral=True)
                
                else:  # JSON
                    json_data = {
                        "guild_id": str(guild_id),
                        "guild_name": inter.guild.name,
                        "export_date": datetime.utcnow().isoformat(),
                        "total_contracts": len(contract_data),
                        "contracts": contract_data
                    }
                    
                    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                    filename = f"{inter.guild.name}_contracts_export_{timestamp}.json"
                    filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).strip()
                    
                    file = await self.create_json_file(json_data, filename)
                    
                    embed = Embed(
                        title="📄 Contracts Export - JSON Format",
                        description=f"Successfully exported contract data",
                        color=disnake.Color.blue()
                    )
                    embed.add_field(name="📈 Statistics", value=f"**Total Contracts:** {len(contract_data)}", inline=False)
                    embed.set_footer(text=f"Exported by {inter.author.display_name}")
                    
                    await inter.send(embed=embed, file=file, ephemeral=True)
            
            elif data_type == "demands":
                # Export only demands data
                user_data = await self.get_all_user_data(guild_id)
                demands_data = {}
                
                for user_id_str, user_info in user_data.items():
                    if isinstance(user_info, dict) and 'demands' in user_info:
                        demands_data[user_id_str] = {
                            'user_id': user_id_str,
                            'demands': user_info['demands']
                        }
                
                if not demands_data:
                    return await inter.send(
                        f"{BotEmojis.x_mark} No demands data found to export.",
                        ephemeral=True
                    )
                
                if format_type == "csv":
                    csv_rows = []
                    for user_id_str, demands_info in demands_data.items():
                        try:
                            user_id = int(user_id_str)
                            member = inter.guild.get_member(user_id)
                            csv_rows.append({
                                'user_id': user_id,
                                'discord_id': user_id,
                                'username': member.name if member else 'Unknown',
                                'display_name': member.display_name if member else 'Unknown',
                                'demands': demands_info['demands']
                            })
                        except (ValueError, TypeError):
                            continue
                    
                    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                    filename = f"{inter.guild.name}_demands_export_{timestamp}.csv"
                    filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).strip()
                    
                    file = await self.create_csv_file(csv_rows, filename)
                    
                    embed = Embed(
                        title="📊 Demands Export - CSV Format",
                        description=f"Successfully exported demands data",
                        color=disnake.Color.green()
                    )
                    embed.add_field(name="📈 Statistics", value=f"**Total Users with Demands:** {len(csv_rows)}", inline=False)
                    embed.set_footer(text=f"Exported by {inter.author.display_name}")
                    
                    await inter.send(embed=embed, file=file, ephemeral=True)
                
                else:  # JSON
                    json_data = {
                        "guild_id": str(guild_id),
                        "guild_name": inter.guild.name,
                        "export_date": datetime.utcnow().isoformat(),
                        "total_demands": len(demands_data),
                        "demands": demands_data
                    }
                    
                    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                    filename = f"{inter.guild.name}_demands_export_{timestamp}.json"
                    filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).strip()
                    
                    file = await self.create_json_file(json_data, filename)
                    
                    embed = Embed(
                        title="📄 Demands Export - JSON Format",
                        description=f"Successfully exported demands data",
                        color=disnake.Color.blue()
                    )
                    embed.add_field(name="📈 Statistics", value=f"**Total Users with Demands:** {len(demands_data)}", inline=False)
                    embed.set_footer(text=f"Exported by {inter.author.display_name}")
                    
                    await inter.send(embed=embed, file=file, ephemeral=True)
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            try:
                await inter.send(
                    f"{BotEmojis.x_mark} Error exporting data: {str(e)}",
                    ephemeral=True
                )
            except Exception:
                pass
    
    @commands.slash_command(name="export")
    @commands.has_permissions(administrator=True)
    async def export(
        self,
        inter: disnake.GuildCommandInteraction,
        data_type: str = commands.Param(
            choices={
                "All User Data": "users",
                "Contracts Only": "contracts",
                "Demands Only": "demands"
            },
            default="users"
        )
    ):
        """
        Export data from the database in CSV or JSON format
        
        Parameters
        ----------
        data_type: Type of data to export (All User Data, Contracts Only, or Demands Only)
        """
        await inter.response.defer(ephemeral=True)
        
        # Check permissions
        franchise_check = await has_role("FranchiseRole", inter.guild.id, inter.author)
        if not franchise_check:
            if not inter.author.guild_permissions.administrator:
                return await inter.send(
                    f"{BotEmojis.x_mark} You need to have a Franchise Role or Administrator permissions to use this command.",
                    ephemeral=True
                )
        
        # Create selection embed
        data_type_names = {
            "users": "All User Data",
            "contracts": "Contracts Only",
            "demands": "Demands Only"
        }
        
        embed = Embed(
            title="📤 Data Export",
            description=f"Export **{data_type_names.get(data_type, data_type)}** from your server database",
            color=disnake.Color.blue()
        )
        
        embed.add_field(
            name="📊 Available Formats",
            value="**CSV Format** - Excel-compatible spreadsheet\n**JSON Format** - Structured data format",
            inline=False
        )
        
        if data_type == "users":
            embed.add_field(
                name="📋 What's Included",
                value="• User IDs & Names\n• Contracts\n• Demands\n• Draft Information\n• Statistics\n• All Custom Fields",
                inline=False
            )
        elif data_type == "contracts":
            embed.add_field(
                name="📋 What's Included",
                value="• User IDs & Names\n• Contract Information",
                inline=False
            )
        elif data_type == "demands":
            embed.add_field(
                name="📋 What's Included",
                value="• User IDs & Names\n• Demand Counts",
                inline=False
            )
        
        embed.add_field(
            name="💡 Usage Tips",
            value="• CSV files work best with Excel/Sheets\n• JSON files preserve full data structure\n• Files are automatically timestamped\n• Large exports may take a moment",
            inline=False
        )
        
        embed.set_footer(text="Select a format below to begin export")
        
        await inter.send(embed=embed, view=ExportFormatView(self.bot, inter, data_type), ephemeral=True)


def setup(bot):
    bot.add_cog(ExportCommands(bot))

