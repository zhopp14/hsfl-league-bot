import io
import json
from typing import Any, Optional

import disnake
from disnake.ext import commands

from utils.config import BotEmojis
from utils.database import Database
from utils.embed import Embed
from utils.tools import has_role


def _truncate(text: str, limit: int = 1900) -> str:
    """
    Trim a string to Discord-safe length while keeping a clear indicator when truncated.
    """
    if len(text) <= limit:
        return text
    return f"{text[: limit - 20]}...\n[truncated]"


def _format_summary(value: Any) -> str:
    """
    Provide a concise, human-readable summary for a database entry preview.
    """
    if value is None:
        return "empty"
    if isinstance(value, dict):
        keys = list(value.keys())
        preview = ", ".join(str(k) for k in keys[:5])
        suffix = "" if len(keys) <= 5 else f", +{len(keys) - 5}"
        return f"dict ({len(keys)} keys: {preview}{suffix})"
    if isinstance(value, list):
        return f"list ({len(value)} items)"
    return f"{type(value).__name__}: {str(value)[:40]}"


def _build_nested_payload(path: Optional[str], payload: Any) -> Any:
    """
    Wrap a payload inside nested dictionaries so it can be merged at the requested path.
    """
    if not path:
        return payload
    keys = [part for part in str(path).split("/") if part]
    nested = payload
    for key in reversed(keys):
        nested = {key: nested}
    return nested


class EntryLookupModal(disnake.ui.Modal):
    """
    Modal that collects key/path input used to display a database entry.
    """

    def __init__(self, cog: "DatabaseManager", user_id: int):
        self.cog = cog
        self.user_id = user_id
        components = [
            disnake.ui.TextInput(
                label="Database Key",
                placeholder="Example: Users, FranchiseRole, Suspensions",
                custom_id="key",
                style=disnake.TextInputStyle.short,
                max_length=80,
            ),
            disnake.ui.TextInput(
                label="Path (optional)",
                placeholder="Nested path such as 123456789/987654321/stats",
                custom_id="path",
                style=disnake.TextInputStyle.short,
                required=False,
                max_length=200,
            ),
        ]
        super().__init__(title="View Database Entry", components=components)

    async def callback(self, interaction: disnake.ModalInteraction) -> None:
        if interaction.author.id != self.user_id:
            await interaction.response.send_message(
                f"{BotEmojis.x_mark} This modal was not opened by you.", ephemeral=True
            )
            return

        key = interaction.text_values.get("key", "").strip()
        path = interaction.text_values.get("path", "").strip() or None

        if not key:
            await interaction.response.send_message(
                f"{BotEmojis.x_mark} A database key is required.", ephemeral=True
            )
            return

        await self.cog.display_entry(interaction, key, path)


class EntryEditModal(disnake.ui.Modal):
    """
    Modal that collects data used to upsert database entries.
    """

    def __init__(self, cog: "DatabaseManager", user_id: int):
        self.cog = cog
        self.user_id = user_id
        components = [
            disnake.ui.TextInput(
                label="Database Key",
                placeholder="Users, FranchiseRole, Suspensions, etc.",
                custom_id="key",
                style=disnake.TextInputStyle.short,
                max_length=80,
            ),
            disnake.ui.TextInput(
                label="Path (optional)",
                placeholder="Nested path like 123456789/987654321",
                custom_id="path",
                style=disnake.TextInputStyle.short,
                required=False,
                max_length=200,
            ),
            disnake.ui.TextInput(
                label="JSON Payload",
                placeholder='{"contract": "10M", "demands": 2}',
                custom_id="payload",
                style=disnake.TextInputStyle.paragraph,
                max_length=1800,
            ),
        ]
        super().__init__(title="Add or Update Entry", components=components)

    async def callback(self, interaction: disnake.ModalInteraction) -> None:
        if interaction.author.id != self.user_id:
            await interaction.response.send_message(
                f"{BotEmojis.x_mark} This modal was not opened by you.", ephemeral=True
            )
            return

        key = interaction.text_values.get("key", "").strip()
        path = interaction.text_values.get("path", "").strip() or None
        payload_raw = interaction.text_values.get("payload", "").strip()

        if not key or not payload_raw:
            await interaction.response.send_message(
                f"{BotEmojis.x_mark} Both key and payload are required.", ephemeral=True
            )
            return

        try:
            payload = json.loads(payload_raw)
        except json.JSONDecodeError as exc:
            await interaction.response.send_message(
                f"{BotEmojis.x_mark} Invalid JSON: {exc}", ephemeral=True
            )
            return

        await self.cog.upsert_entry(interaction, key, path, payload)


class EntryDeleteModal(disnake.ui.Modal):
    """
    Modal that collects key/path input used to delete a database entry.
    """

    def __init__(self, cog: "DatabaseManager", user_id: int):
        self.cog = cog
        self.user_id = user_id
        components = [
            disnake.ui.TextInput(
                label="Database Key",
                placeholder="Key to delete data from",
                custom_id="key",
                style=disnake.TextInputStyle.short,
                max_length=80,
            ),
            disnake.ui.TextInput(
                label="Path (leave blank to delete whole key)",
                placeholder="Example: 123456789/987654321",
                custom_id="path",
                style=disnake.TextInputStyle.short,
                required=False,
                max_length=200,
            ),
            disnake.ui.TextInput(
                label="Type CONFIRM to delete",
                placeholder="CONFIRM",
                custom_id="confirm",
                style=disnake.TextInputStyle.short,
                max_length=10,
            ),
        ]
        super().__init__(title="Delete Database Entry", components=components)

    async def callback(self, interaction: disnake.ModalInteraction) -> None:
        if interaction.author.id != self.user_id:
            await interaction.response.send_message(
                f"{BotEmojis.x_mark} This modal was not opened by you.", ephemeral=True
            )
            return

        key = interaction.text_values.get("key", "").strip()
        path = interaction.text_values.get("path", "").strip() or None
        confirm = interaction.text_values.get("confirm", "").strip()

        if confirm.upper() != "CONFIRM":
            await interaction.response.send_message(
                f"{BotEmojis.warn} Deletion cancelled (confirmation text did not match).",
                ephemeral=True,
            )
            return

        if not key:
            await interaction.response.send_message(
                f"{BotEmojis.x_mark} A database key is required.", ephemeral=True
            )
            return

        await self.cog.delete_entry(interaction, key, path)


class EntryExportModal(disnake.ui.Modal):
    """
    Modal that collects a key used to export a data file.
    """

    def __init__(self, cog: "DatabaseManager", user_id: int):
        self.cog = cog
        self.user_id = user_id
        components = [
            disnake.ui.TextInput(
                label="Database Key",
                placeholder="Key to export, e.g. Users",
                custom_id="key",
                style=disnake.TextInputStyle.short,
                max_length=80,
            ),
        ]
        super().__init__(title="Export Database Key", components=components)

    async def callback(self, interaction: disnake.ModalInteraction) -> None:
        if interaction.author.id != self.user_id:
            await interaction.response.send_message(
                f"{BotEmojis.x_mark} This modal was not opened by you.", ephemeral=True
            )
            return

        key = interaction.text_values.get("key", "").strip()
        if not key:
            await interaction.response.send_message(
                f"{BotEmojis.x_mark} A database key is required.", ephemeral=True
            )
            return

        await self.cog.export_key(interaction, key)


class DatabaseManagerView(disnake.ui.View):
    """
    Persistent view that powers the interactive database manager workflow.
    """

    def __init__(
        self,
        cog: "DatabaseManager",
        requester_id: int,
        guild_id: int,
        keys: list[str],
    ):
        super().__init__(timeout=600)
        self.cog = cog
        self.requester_id = requester_id
        self.guild_id = guild_id
        self.keys = keys

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        if interaction.author.id != self.requester_id:
            await interaction.response.send_message(
                f"{BotEmojis.x_mark} This session belongs to someone else. Run `/database_manager` to open your own.",
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True

    async def refresh_summary(self, interaction: disnake.MessageInteraction) -> None:
        self.keys = await Database.get_db_keys()
        embed = await self.cog.build_summary_embed(
            guild=interaction.guild,
            user=interaction.author,
            keys=self.keys,
            session_owner=interaction.author,
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @disnake.ui.button(label="Refresh Overview", style=disnake.ButtonStyle.primary, emoji="🔄")
    async def refresh_button(
        self,
        button: disnake.ui.Button,
        interaction: disnake.MessageInteraction,
    ) -> None:
        await self.refresh_summary(interaction)

    @disnake.ui.button(label="View Entry", style=disnake.ButtonStyle.secondary, emoji="📂")
    async def view_button(
        self,
        button: disnake.ui.Button,
        interaction: disnake.MessageInteraction,
    ) -> None:
        await interaction.response.send_modal(EntryLookupModal(self.cog, self.requester_id))

    @disnake.ui.button(label="Add or Update", style=disnake.ButtonStyle.success, emoji="📝")
    async def edit_button(
        self,
        button: disnake.ui.Button,
        interaction: disnake.MessageInteraction,
    ) -> None:
        await interaction.response.send_modal(EntryEditModal(self.cog, self.requester_id))

    @disnake.ui.button(label="Delete Entry", style=disnake.ButtonStyle.danger, emoji="🗑️")
    async def delete_button(
        self,
        button: disnake.ui.Button,
        interaction: disnake.MessageInteraction,
    ) -> None:
        await interaction.response.send_modal(EntryDeleteModal(self.cog, self.requester_id))

    @disnake.ui.button(label="Export Key", style=disnake.ButtonStyle.secondary, emoji="📤")
    async def export_button(
        self,
        button: disnake.ui.Button,
        interaction: disnake.MessageInteraction,
    ) -> None:
        await interaction.response.send_modal(EntryExportModal(self.cog, self.requester_id))

    @disnake.ui.button(label="Close", style=disnake.ButtonStyle.secondary, emoji="❌")
    async def close_button(
        self,
        button: disnake.ui.Button,
        interaction: disnake.MessageInteraction,
    ) -> None:
        for item in self.children:
            item.disabled = True
        self.stop()
        await interaction.response.edit_message(
            content=f"{BotEmojis.warn} Database manager session closed.", embed=None, view=self
        )


class DatabaseManager(commands.Cog):
    """
    Provides a professional, staff-friendly dashboard for browsing and maintaining the local database.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def build_summary_embed(
        self,
        guild: disnake.Guild,
        user: disnake.Member,
        keys: list[str],
        session_owner: disnake.Member,
    ) -> disnake.Embed:
        """
        Generate an overview embed highlighting the current database structure.
        """
        embed = Embed(
            title="Database Control Center",
            description=(
                "Use the controls below to inspect entries, update records, or export snapshots. "
                "All actions run instantly against the live JSON database."
            ),
            guild=guild,
            user=session_owner,
        )

        if not keys:
            embed.add_field(
                name="No Keys Found",
                value="The `database/` directory is currently empty.",
                inline=False,
            )
            return embed

        for key in keys[:10]:
            data = await Database.get_data(key)  # type: ignore[arg-type]
            summary = _format_summary(data)
            embed.add_field(name=key, value=summary, inline=False)

        if len(keys) > 10:
            embed.set_footer(text=f"{len(keys)} keys total. Use Refresh to see updates.")

        return embed

    async def _ensure_permissions(
        self, inter: disnake.GuildCommandInteraction
    ) -> Optional[disnake.Message]:
        """
        Confirm the caller is either an administrator or holds the configured FranchiseRole.
        Returns an error response if the permission check fails.
        """
        has_franchise = await has_role("FranchiseRole", inter.guild.id, inter.author)
        if has_franchise or inter.author.guild_permissions.administrator:
            return None

        message = await inter.send(
            f"{BotEmojis.x_mark} You need Administrator permissions or the configured Franchise Role to manage the database.",
            ephemeral=True,
        )
        return message

    async def display_entry(
        self,
        interaction: disnake.ModalInteraction,
        key: str,
        path: Optional[str],
    ) -> None:
        """
        Retrieve a database value and present it to the user.
        """
        data = await Database.get_data(key, path)
        if data is None:
            await interaction.response.send_message(
                f"{BotEmojis.warn} No data found for `{key}`" + (f" at `{path}`." if path else "."),
                ephemeral=True,
            )
            return

        formatted = json.dumps(data, indent=2, ensure_ascii=False)

        if len(formatted) > 1800:
            buffer = io.BytesIO(formatted.encode("utf-8"))
            filename = f"{key.replace('/', '_')}"
            if path:
                filename += f"_{path.replace('/', '_')}"
            filename += ".json"
            await interaction.response.send_message(
                f"{BotEmojis.check_mark} Entry exported as `{filename}`.",
                file=disnake.File(buffer, filename=filename),
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"```json\n{_truncate(formatted)}\n```", ephemeral=True
        )

    async def upsert_entry(
        self,
        interaction: disnake.ModalInteraction,
        key: str,
        path: Optional[str],
        payload: Any,
    ) -> None:
        """
        Merge or overwrite data in the database at the provided key/path.
        """
        merged_payload = _build_nested_payload(path, payload)
        await Database.add_data(key, merged_payload)

        await interaction.response.send_message(
            f"{BotEmojis.check_mark} Data saved to `{key}`" + (f" at `{path}`." if path else "."),
            ephemeral=True,
        )

    async def delete_entry(
        self,
        interaction: disnake.ModalInteraction,
        key: str,
        path: Optional[str],
    ) -> None:
        """
        Delete the specified key or nested path from the database.
        """
        await Database.delete_data(key, path)
        target = f"`{key}`" if not path else f"`{key}` at `{path}`"
        await interaction.response.send_message(
            f"{BotEmojis.warn} Deleted {target}.", ephemeral=True
        )

    async def export_key(
        self,
        interaction: disnake.ModalInteraction,
        key: str,
    ) -> None:
        """
        Send the entire contents of a database key as a downloadable JSON file.
        """
        data = await Database.get_data(key)
        if data is None:
            await interaction.response.send_message(
                f"{BotEmojis.warn} No data stored under `{key}`.", ephemeral=True
            )
            return

        payload = json.dumps(data, indent=2, ensure_ascii=False)
        buffer = io.BytesIO(payload.encode("utf-8"))
        filename = f"{key.replace('/', '_')}.json"

        await interaction.response.send_message(
            f"{BotEmojis.check_mark} Exported `{key}`.", file=disnake.File(buffer, filename=filename), ephemeral=True
        )

    @commands.slash_command()
    async def database_manager(
        self,
        inter: disnake.GuildCommandInteraction,
    ):
        """
        Launch the interactive database management console (administrator / Franchise Role only).
        """
        await inter.response.defer(ephemeral=True)

        permission_failure = await self._ensure_permissions(inter)
        if permission_failure:
            return

        keys = await Database.get_db_keys()
        embed = await self.build_summary_embed(
            guild=inter.guild,
            user=inter.author,
            keys=keys,
            session_owner=inter.author,
        )

        view = DatabaseManagerView(
            cog=self,
            requester_id=inter.author.id,
            guild_id=inter.guild.id,
            keys=keys,
        )

        embed.add_field(
            name="Quick Tips",
            value=(
                "• **View Entry** – Inspect any key/path combination.\n"
                "• **Add or Update** – Paste JSON to merge or overwrite data.\n"
                "• **Delete Entry** – Remove nested paths or entire keys (with confirmation).\n"
                "• **Export Key** – Download a full JSON snapshot for audits."
            ),
            inline=False,
        )

        await inter.send(embed=embed, view=view, ephemeral=True)


def setup(bot: commands.Bot):
    bot.add_cog(DatabaseManager(bot))

