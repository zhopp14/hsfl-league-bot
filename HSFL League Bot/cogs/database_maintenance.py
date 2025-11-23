import disnake
from disnake.ext import commands
from utils.database import Database


class DatabaseMaintenance(commands.Cog):
    """
    Database maintenance commands for checking integrity and backups
    """
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.slash_command(name="db_health")
    @commands.is_owner()
    async def db_health(self, inter: disnake.ApplicationCommandInteraction):
        """
        Check database health and integrity
        """
        await inter.response.defer()
        
        report = await Database.verify_integrity()
        
        embed = disnake.Embed(
            title="Database Health Check",
            color=disnake.Color.green() if report["errors"] == [] else disnake.Color.orange()
        )
        
        embed.add_field(name="Files Checked", value=str(report["checked"]), inline=True)
        embed.add_field(name="Corrupted Files", value=str(report["corrupted"]), inline=True)
        embed.add_field(name="Recovered Files", value=str(report["recovered"]), inline=True)
        
        if report["errors"]:
            errors_text = "\n".join(report["errors"][:5])
            if len(report["errors"]) > 5:
                errors_text += f"\n... and {len(report['errors']) - 5} more"
            embed.add_field(name="Errors", value=f"```\n{errors_text}\n```", inline=False)
        else:
            embed.add_field(name="Status", value="✅ All databases healthy", inline=False)
        
        await inter.followup.send(embed=embed)
    
    @commands.slash_command(name="db_backups")
    @commands.is_owner()
    async def db_backups(self, inter: disnake.ApplicationCommandInteraction):
        """
        Show available database backups
        """
        await inter.response.defer()
        
        backup_status = await Database.get_backup_status()
        
        if not backup_status:
            await inter.followup.send("No backups found")
            return
        
        embed = disnake.Embed(
            title="Database Backups",
            color=disnake.Color.blue()
        )
        
        for key, info in backup_status.items():
            value = f"**Count**: {info['count']}\n"
            value += f"**Latest**: {info['latest'] or 'None'}\n"
            value += f"**Oldest**: {info['oldest'] or 'None'}"
            embed.add_field(name=key, value=value, inline=False)
        
        await inter.followup.send(embed=embed)
    
    @commands.slash_command(name="db_export")
    @commands.is_owner()
    async def db_export(self, inter: disnake.ApplicationCommandInteraction):
        """
        Export entire database as a backup file
        """
        await inter.response.defer()
        
        export_path = await Database.export_database()
        
        if export_path:
            await inter.followup.send(f"✅ Database exported to `{export_path}`")
        else:
            await inter.followup.send("❌ Failed to export database")
    
    @commands.slash_command(name="db_clear")
    @commands.is_owner()
    async def db_clear(self, inter: disnake.ApplicationCommandInteraction):
        """
        Clear all database files (WITH CONFIRMATION)
        WARNING: This will delete all stored data!
        """
        await inter.response.defer()
        
        embed = disnake.Embed(
            title="Database Clearance Warning",
            description="This action will **DELETE ALL DATA** in the database!",
            color=disnake.Color.red()
        )
        embed.add_field(name="Data That Will Be Lost", value="Users, Franchises, Suspensions, Channels, Roles, Settings", inline=False)
        embed.add_field(name="This is irreversible", value="Make sure you have a backup!", inline=False)
        
        def check(button_inter):
            return button_inter.author.id == inter.author.id
        
        view = disnake.ui.View()
        
        async def confirm_callback(button_inter):
            await button_inter.response.defer()
            
            try:
                from pathlib import Path
                import shutil
                
                db_dir = Path("database")
                files_deleted = 0
                
                for file_path in db_dir.glob("*.json"):
                    if file_path.name != ".gitkeep":
                        file_path.unlink()
                        files_deleted += 1
                
                result_embed = disnake.Embed(
                    title="Database Cleared",
                    description=f"Successfully deleted {files_deleted} database files",
                    color=disnake.Color.green()
                )
                result_embed.add_field(name="Files Deleted", value=str(files_deleted), inline=False)
                result_embed.add_field(name="Note", value="Backups and lock files were preserved", inline=False)
                
                await button_inter.followup.send(embed=result_embed)
            except Exception as e:
                await button_inter.followup.send(f"❌ Error clearing database: {e}")
        
        async def cancel_callback(button_inter):
            await button_inter.response.defer()
            await button_inter.followup.send("Database clearance cancelled")
        
        confirm_button = disnake.ui.Button(label="Yes, Clear All Data", style=disnake.ButtonStyle.danger)
        cancel_button = disnake.ui.Button(label="Cancel", style=disnake.ButtonStyle.secondary)
        
        confirm_button.callback = confirm_callback
        cancel_button.callback = cancel_callback
        
        view.add_item(confirm_button)
        view.add_item(cancel_button)
        
        await inter.followup.send(embed=embed, view=view)


def setup(bot):
    bot.add_cog(DatabaseMaintenance(bot))
