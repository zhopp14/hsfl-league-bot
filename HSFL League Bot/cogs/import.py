import asyncio
import copy
import csv
import io
import json
import os
import re
from dataclasses import dataclass, field
from typing import Optional

import disnake
from disnake.ext import commands
import aiohttp

try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:  # pragma: no cover - optional dependency
    gspread = None
    Credentials = None

from utils.config import BotEmojis
from utils.database import Database
from utils.embed import Embed
from utils.tools import has_role, premium_guild_check


@dataclass
class ManualImportEntry:
    """Represents a single manual import entry collected from the modal."""

    identifier: str
    category: str
    stats: dict[str, str]
    contract: Optional[str] = None
    demands: Optional[str] = None


@dataclass
class ManualImportSession:
    """Tracks all manual entries gathered during an interactive session."""

    guild_id: int
    week: Optional[int]
    entries: list[ManualImportEntry] = field(default_factory=list)


class ManualImportModal(disnake.ui.Modal):
    """Collects a single player/category/stat block from the user."""

    def __init__(
        self,
        cog: "Import",
        user_id: int,
        action: str = "add",
        entry_id: Optional[int] = None,
        prefills: Optional[ManualImportEntry] = None,
    ):
        self.cog = cog
        self.user_id = user_id
        self.action = action  # "add" or "edit"
        self.entry_id = entry_id

        default_identifier = prefills.identifier if prefills else ""
        default_category = prefills.category if prefills else ""
        default_contract = prefills.contract or "" if prefills else ""
        default_demands = prefills.demands or "" if prefills else ""
        default_stats = ""
        if prefills and prefills.stats:
            default_stats = "\n".join(f"{key}={value}" for key, value in prefills.stats.items())

        components = [
            disnake.ui.TextInput(
                label="Player Identifier",
                placeholder="Discord ID, username, or display name",
                custom_id="identifier",
                style=disnake.TextInputStyle.short,
                max_length=120,
                value=default_identifier,
            ),
            disnake.ui.TextInput(
                label="Stat Category",
                placeholder="PASSING, RUSHING, DEFENSE, etc.",
                custom_id="category",
                style=disnake.TextInputStyle.short,
                max_length=60,
                value=default_category,
            ),
            disnake.ui.TextInput(
                label="Stats (one per line, name=value)",
                placeholder="CMP=22\nATT=30\nYDS=250",
                custom_id="stats",
                style=disnake.TextInputStyle.paragraph,
                max_length=1800,
                value=default_stats,
            ),
            disnake.ui.TextInput(
                label="Contract (optional)",
                placeholder="Leave blank to keep unchanged",
                custom_id="contract",
                style=disnake.TextInputStyle.short,
                required=False,
                max_length=120,
                value=default_contract,
            ),
            disnake.ui.TextInput(
                label="Demands (optional)",
                placeholder="Leave blank to keep unchanged",
                custom_id="demands",
                style=disnake.TextInputStyle.short,
                required=False,
                max_length=120,
                value=default_demands,
            ),
        ]

        super().__init__(title="Manual Stat Import Entry", components=components)

    async def callback(self, interaction: disnake.ModalInteraction) -> None:
        session = self.cog.manual_sessions.get(self.user_id)
        if not session:
            await interaction.response.send_message(
                "Your manual import session expired. Start a new `/manual_import` command to continue.",
                ephemeral=True,
            )
            return

        identifier = interaction.text_values.get("identifier", "").strip()
        category = interaction.text_values.get("category", "").strip() or "General"
        stats_text = interaction.text_values.get("stats", "").strip()
        contract = interaction.text_values.get("contract") or None
        demands = interaction.text_values.get("demands") or None

        if not identifier or not stats_text:
            await interaction.response.send_message(
                f"{BotEmojis.x_mark} Identifier and at least one stat are required.",
                ephemeral=True,
            )
            return

        stats: dict[str, str] = {}
        errors: list[str] = []

        for line_num, line in enumerate(stats_text.splitlines(), start=1):
            stripped = line.strip()
            if not stripped:
                continue
            if "=" not in stripped:
                errors.append(f"Line {line_num}: '{line}' is missing '=' (use name=value).")
                continue

            name, value = [part.strip() for part in stripped.split("=", 1)]
            if not name or not value:
                errors.append(f"Line {line_num}: '{line}' must include both a name and value.")
                continue
            stats[name] = value

        if errors:
            formatted = "\n".join(errors[:5])
            if len(errors) > 5:
                formatted += f"\n...and {len(errors) - 5} more issues"
            await interaction.response.send_message(
                f"{BotEmojis.x_mark} Could not save this entry:\n```{formatted}```",
                ephemeral=True,
            )
            return

        new_entry = ManualImportEntry(
            identifier=identifier,
            category=category,
            stats=stats,
            contract=contract,
            demands=demands,
        )

        if self.action == "edit" and self.entry_id is not None:
            if 0 <= self.entry_id < len(session.entries):
                session.entries[self.entry_id] = new_entry
                await interaction.response.send_message(
                    f"{BotEmojis.check_mark} Updated entry for `{identifier}` in `{category}`.",
                    ephemeral=True,
                )
                return

        session.entries.append(new_entry)
        await interaction.response.send_message(
            f"{BotEmojis.check_mark} Added `{identifier}` under `{category}` with {len(stats)} stat values.",
            ephemeral=True,
        )


def _format_manual_entry(entry: ManualImportEntry, index: int, week: Optional[int]) -> str:
    """
    Produce a human-readable summary of a staged manual import entry.
    """
    header = f"Entry {index + 1}: **{entry.identifier}** → {entry.category}"
    if week is not None:
        header += f" (week {week})"

    details = []
    if entry.contract:
        details.append(f"• Contract: {entry.contract}")
    if entry.demands:
        details.append(f"• Demands: {entry.demands}")

    stats_preview = list(entry.stats.items())
    if stats_preview:
        lines = []
        for stat_name, stat_value in stats_preview[:8]:
            lines.append(f"- {stat_name}: {stat_value}")
        if len(stats_preview) > 8:
            lines.append(f"... and {len(stats_preview) - 8} more stats")
        details.append("Stats:\n" + "\n".join(lines))
    else:
        details.append("No stat fields supplied.")

    return f"{header}\n" + "\n".join(details)


class ManualEntrySelect(disnake.ui.StringSelect):
    """Dropdown used to choose a staged entry for edit or deletion."""

    def __init__(
        self,
        parent_view: "EntryManagerView",
        session: ManualImportSession,
    ):
        options = []
        for idx, entry in enumerate(session.entries[:25]):
            label = f"{idx + 1}. {entry.identifier}"[:100]
            description = f"{entry.category} • {len(entry.stats)} stats"[:100]
            options.append(
                disnake.SelectOption(
                    label=label,
                    description=description,
                    value=str(idx),
                )
            )

        super().__init__(
            placeholder="Select an entry to manage",
            options=options,
            min_values=1,
            max_values=1,
        )
        self.parent_view = parent_view
        self.session = session

    async def callback(self, interaction: disnake.MessageInteraction) -> None:
        if interaction.author.id != self.parent_view.requester_id:
            await interaction.response.send_message(
                f"{BotEmojis.x_mark} This manager belongs to someone else.",
                ephemeral=True,
            )
            return

        index = int(self.values[0])
        if index >= len(self.session.entries):
            await interaction.response.send_message(
                f"{BotEmojis.warn} That entry is no longer available. Refresh and try again.",
                ephemeral=True,
            )
            return

        entry = self.session.entries[index]
        detail = _format_manual_entry(entry, index, self.session.week)
        action_view = EntryActionView(
            self.parent_view.cog,
            self.parent_view.requester_id,
            self.session,
            index,
        )
        await interaction.response.edit_message(content=detail, view=action_view)


class EntryManagerView(disnake.ui.View):
    """Secondary view that lets staff edit or remove staged manual import entries."""

    def __init__(
        self,
        cog: "Import",
        requester_id: int,
        session: ManualImportSession,
    ):
        super().__init__(timeout=300)
        self.cog = cog
        self.requester_id = requester_id
        self.session = session

        if session.entries:
            self.add_item(ManualEntrySelect(self, session))

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        if interaction.author.id != self.requester_id:
            await interaction.response.send_message(
                f"{BotEmojis.x_mark} This manager belongs to someone else. Use your own `/manual_import` session.",
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True

    @disnake.ui.button(label="Clear All", style=disnake.ButtonStyle.danger, emoji="🧹")
    async def clear_all(
        self,
        button: disnake.ui.Button,
        interaction: disnake.MessageInteraction,
    ) -> None:
        self.session.entries.clear()
        await interaction.response.edit_message(
            content=f"{BotEmojis.warn} All staged entries were removed.",
            view=None,
        )

    @disnake.ui.button(label="Close", style=disnake.ButtonStyle.secondary, emoji="❌")
    async def close(
        self,
        button: disnake.ui.Button,
        interaction: disnake.MessageInteraction,
    ) -> None:
        await interaction.response.edit_message(
            content=f"{BotEmojis.warn} Closed the entry manager.",
            view=None,
        )
        self.stop()


class EntryActionView(disnake.ui.View):
    """Actions that operate on a specific staged entry."""

    def __init__(
        self,
        cog: "Import",
        requester_id: int,
        session: ManualImportSession,
        entry_index: int,
    ):
        super().__init__(timeout=300)
        self.cog = cog
        self.requester_id = requester_id
        self.session = session
        self.entry_index = entry_index

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        if interaction.author.id != self.requester_id:
            await interaction.response.send_message(
                f"{BotEmojis.x_mark} This manager belongs to someone else. Use your own `/manual_import` session.",
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True

    @disnake.ui.button(label="Edit Entry", style=disnake.ButtonStyle.primary, emoji="🛠️")
    async def edit_entry(
        self,
        button: disnake.ui.Button,
        interaction: disnake.MessageInteraction,
    ) -> None:
        if self.entry_index >= len(self.session.entries):
            await interaction.response.send_message(
                f"{BotEmojis.warn} That entry no longer exists. Re-open the manager to refresh.",
                ephemeral=True,
            )
            return

        entry = self.session.entries[self.entry_index]
        await interaction.response.send_modal(
            ManualImportModal(
                self.cog,
                self.requester_id,
                action="edit",
                entry_id=self.entry_index,
                prefills=entry,
            )
        )

    @disnake.ui.button(label="Delete Entry", style=disnake.ButtonStyle.danger, emoji="🗑️")
    async def delete_entry(
        self,
        button: disnake.ui.Button,
        interaction: disnake.MessageInteraction,
    ) -> None:
        if self.entry_index >= len(self.session.entries):
            await interaction.response.send_message(
                f"{BotEmojis.warn} That entry no longer exists. Re-open the manager to refresh.",
                ephemeral=True,
            )
            return

        removed = self.session.entries.pop(self.entry_index)

        if not self.session.entries:
            await interaction.response.edit_message(
                content=f"{BotEmojis.warn} Removed `{removed.identifier}`. No staged entries remain.",
                view=None,
            )
            return

        manager_view = EntryManagerView(self.cog, self.requester_id, self.session)
        await interaction.response.edit_message(
            content=f"{BotEmojis.warn} Removed `{removed.identifier}`. Select another entry to manage:",
            view=manager_view,
        )

    @disnake.ui.button(label="Back to List", style=disnake.ButtonStyle.secondary, emoji="⬅️")
    async def back_to_list(
        self,
        button: disnake.ui.Button,
        interaction: disnake.MessageInteraction,
    ) -> None:
        manager_view = EntryManagerView(self.cog, self.requester_id, self.session)
        await interaction.response.edit_message(
            content="Select a staged entry to manage:",
            view=manager_view,
        )


class ManualImportView(disnake.ui.View):
    """Interactive view that allows staff to stage multiple manual entries before committing them."""

    def __init__(self, cog: "Import", user_id: int):
        super().__init__(timeout=600)
        self.cog = cog
        self.user_id = user_id

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        if interaction.author.id != self.user_id:
            await interaction.response.send_message(
                f"{BotEmojis.x_mark} This session belongs to someone else. Run `/manual_import` to start your own.",
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self) -> None:
        self.cog.manual_sessions.pop(self.user_id, None)

    @disnake.ui.button(label="Add Player Stats", style=disnake.ButtonStyle.primary, emoji="➕")
    async def add_player(
        self,
        button: disnake.ui.Button,
        interaction: disnake.MessageInteraction,
    ) -> None:
        await interaction.response.send_modal(ManualImportModal(self.cog, self.user_id))

    @disnake.ui.button(label="Preview Entries", style=disnake.ButtonStyle.secondary, emoji="📋")
    async def preview(
        self,
        button: disnake.ui.Button,
        interaction: disnake.MessageInteraction,
    ) -> None:
        session = self.cog.manual_sessions.get(self.user_id)
        if not session or not session.entries:
            await interaction.response.send_message(
                f"{BotEmojis.warn} No entries staged yet. Use **Add Player Stats** first.",
                ephemeral=True,
            )
            return

        preview_lines = []
        for entry in session.entries[:10]:
            preview_lines.append(
                f"- {entry.identifier} → {entry.category} ({len(entry.stats)} stats)"
            )
        if len(session.entries) > 10:
            preview_lines.append(f"...and {len(session.entries) - 10} more entries")

        await interaction.response.send_message(
            "\n".join(preview_lines),
            ephemeral=True,
        )

    @disnake.ui.button(label="Manage Entries", style=disnake.ButtonStyle.secondary, emoji="⚙️")
    async def manage(
        self,
        button: disnake.ui.Button,
        interaction: disnake.MessageInteraction,
    ) -> None:
        session = self.cog.manual_sessions.get(self.user_id)
        if not session or not session.entries:
            await interaction.response.send_message(
                f"{BotEmojis.warn} There are no staged entries to manage yet.",
                ephemeral=True,
            )
            return

        manager_view = EntryManagerView(self.cog, self.user_id, session)
        await interaction.response.send_message(
            "Select a staged entry to review or modify:",
            view=manager_view,
            ephemeral=True,
        )

    @disnake.ui.button(label="Submit to Database", style=disnake.ButtonStyle.success, emoji="💾")
    async def submit(
        self,
        button: disnake.ui.Button,
        interaction: disnake.MessageInteraction,
    ) -> None:
        session = self.cog.manual_sessions.get(self.user_id)
        if not session or not session.entries:
            await interaction.response.send_message(
                f"{BotEmojis.warn} Add at least one entry before submitting.",
                ephemeral=True,
            )
            return

        imported, updated, errors, master_entries = await self.cog.process_manual_session(
            interaction, session
        )

        master_sync_result: Optional[tuple[bool, str]] = None
        if master_entries:
            master_sync_result = await self.cog.push_to_master_sheet_entries(master_entries)

        self.cog.manual_sessions.pop(self.user_id, None)
        self.stop()

        embed = Embed(
            title="Manual Import Complete",
            description="All staged entries have been processed."
        )
        if session.week is not None:
            embed.description += f" (week {session.week})"

        embed.add_field(
            name=f"{BotEmojis.check_mark} Results",
            value=(
                f"**Imported:** {imported} new entries\n"
                f"**Updated:** {updated} existing entries\n"
                f"**Total Staged:** {imported + updated}"
            ),
            inline=False,
        )

        if errors:
            display = "\n".join(errors[:10])
            if len(errors) > 10:
                display += f"\n...and {len(errors) - 10} more issues"
            embed.add_field(
                name=f"{BotEmojis.warn} Issues",
                value=f"```{display}```",
                inline=False,
            )

        if master_sync_result:
            success, message = master_sync_result
            field_name = (
                f"{BotEmojis.check_mark} Master Sheet"
                if success
                else f"{BotEmojis.warn} Master Sheet"
            )
            embed.add_field(name=field_name, value=message, inline=False)

        await interaction.response.edit_message(embed=embed, view=None)

    @disnake.ui.button(label="Cancel Session", style=disnake.ButtonStyle.danger, emoji="✖️")
    async def cancel(
        self,
        button: disnake.ui.Button,
        interaction: disnake.MessageInteraction,
    ) -> None:
        self.cog.manual_sessions.pop(self.user_id, None)
        self.stop()
        await interaction.response.edit_message(
            content=f"{BotEmojis.warn} Manual import session cancelled.",
            embed=None,
            view=None,
        )


class Import(commands.Cog):
    """
    Handles importing data from stat sheets into the master database
    Supports Google Sheets URLs and CSV file attachments
    """

    MASTER_ID_ENV_KEYS = ("MASTER_SHEET_ID", "MASTERSHEET_ID")
    MASTER_GID_ENV_KEYS = ("MASTER_SHEET_GID", "MASTERSHEET_GID")
    DEFAULT_MASTER_SHEET_ID = "1qMlCBIut2HX6daBXVSWC0hFP_RZ8cpqLoyptW1pUXz4"
    DEFAULT_MASTER_SHEET_GID = 708235940

    IDENTIFIER_FIELDS = {
        "user_id",
        "discord_id",
        "discord id",
        "id",
        "username",
        "user",
        "name",
        "player",
    }

    IGNORED_IDENTIFIERS = {
        "username",
        "name",
        "player",
        "stream link",
        "streamer + media",
        "stat taker",
        "coach",
        "team",
        "teams",
        "position",
        "pos",
        "total",
    }

    GOOGLE_SCOPES = (
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/spreadsheets",
    )

    def __init__(self, bot):
        self.bot = bot
        self.manual_sessions: dict[int, ManualImportSession] = {}
        self.gspread_init_error: Optional[str] = None
        self.gspread_client = self._init_gspread_client()

    def _init_gspread_client(self):
        """
        Attempt to initialise a Google Sheets service account client using environment variables.

        Supported variables:
            - GOOGLE_SERVICE_ACCOUNT_FILE: path to the service-account JSON file.
            - GOOGLE_SERVICE_ACCOUNT_JSON: raw JSON string with service account credentials.
        """
        self.gspread_init_error = None
        if not (gspread and Credentials):
            return None

        credentials = None
        file_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
        raw_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

        if not file_path and not raw_json:
            default_candidate = os.path.join(os.getcwd(), "service-account.json")
            if os.path.exists(default_candidate):
                file_path = default_candidate

        try:
            if raw_json:
                info = json.loads(raw_json)
                credentials = Credentials.from_service_account_info(
                    info,
                    scopes=self.GOOGLE_SCOPES,
                )
            elif file_path:
                if not os.path.exists(file_path):
                    self.gspread_init_error = f"Service account file '{file_path}' was not found."
                    return None

                credentials = Credentials.from_service_account_file(
                    file_path,
                    scopes=self.GOOGLE_SCOPES,
                )
        except Exception as exc:  # pragma: no cover - defensive
            self.gspread_init_error = f"Failed to load Google credentials: {exc}"
            return None

        if not credentials:
            return None

        try:
            return gspread.authorize(credentials)
        except Exception as exc:  # pragma: no cover - defensive
            self.gspread_init_error = f"Failed to authorise Google Sheets client: {exc}"
            return None

    def _get_master_sheet_target(self) -> tuple[Optional[str], Optional[int]]:
        """
        Resolve the master sheet ID and gid from environment variables or defaults.
        """
        sheet_id: Optional[str] = None
        for key in self.MASTER_ID_ENV_KEYS:
            value = os.getenv(key)
            if value:
                sheet_id = value.strip()
                break

        if not sheet_id:
            sheet_id = self.DEFAULT_MASTER_SHEET_ID

        gid: Optional[int] = None
        for key in self.MASTER_GID_ENV_KEYS:
            value = os.getenv(key)
            if value:
                try:
                    gid = int(value)
                    break
                except ValueError:
                    continue

        if gid is None:
            gid = self.DEFAULT_MASTER_SHEET_GID

        return sheet_id, gid

    @staticmethod
    def _parse_sheet_url(url: str) -> tuple[str, Optional[int]]:
        """
        Extract the document ID and optional gid from a Google Sheets URL.
        """
        sheet_id_match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", url)
        if not sheet_id_match:
            raise ValueError("Invalid Google Sheets URL format.")

        sheet_id = sheet_id_match.group(1)
        gid_match = re.search(r"[#&]gid=(\d+)", url)
        gid = int(gid_match.group(1)) if gid_match else None
        return sheet_id, gid

    async def _fetch_sheet_via_service_account(self, sheet_id: str, gid: Optional[int]) -> Optional[str]:
        """Use a Google service account (if configured) to download worksheet data safely."""
        if not self.gspread_client:
            return None

        async def _run() -> str:
            def _download() -> str:
                spreadsheet = self.gspread_client.open_by_key(sheet_id)

                worksheet = None
                if gid is not None:
                    worksheet = spreadsheet.get_worksheet_by_id(int(gid))

                if worksheet is None:
                    worksheet = spreadsheet.sheet1

                values = worksheet.get_all_values()
                if not values:
                    return ""

                buffer = io.StringIO()
                writer = csv.writer(buffer)
                writer.writerows(values)
                return buffer.getvalue()

            return await asyncio.to_thread(_download)

        try:
            return await _run()
        except gspread.exceptions.WorksheetNotFound as exc:
            raise ValueError(
                "Google Sheets tab not found. Double-check the gid value or sheet name."
            ) from exc
        except gspread.exceptions.APIError as exc:
            raise ValueError(
                "Google Sheets API returned an error. Ensure the service account has access to this sheet."
            ) from exc
        except Exception as exc:  # pragma: no cover - defensive
            raise ValueError(f"Failed to download sheet via service account: {exc}") from exc

    async def fetch_google_sheet(self, url: str) -> str:
        """
        Fetches data from a Google Sheets URL
        Converts the shareable URL to CSV export format
        """
        # Convert Google Sheets URL to CSV export format
        # Example: https://docs.google.com/spreadsheets/d/SHEET_ID/edit
        # To: https://docs.google.com/spreadsheets/d/SHEET_ID/export?format=csv&gid=0

        sheet_id, gid = self._parse_sheet_url(url)

        # First attempt: use a service account if configured (handles private sheets)
        service_result = await self._fetch_sheet_via_service_account(sheet_id, gid)
        if service_result is not None:
            if not service_result.strip():
                raise ValueError(
                    "The sheet appears to be empty. Make sure the tab contains data."
                )
            return service_result

        gid_param = gid if gid is not None else 0
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid_param}"

        async with aiohttp.ClientSession() as session:
            async with session.get(csv_url) as response:
                if response.status == 403:
                    raise ValueError(
                        "Google denied access to the sheet. Share it with 'Anyone with the link' (Viewer) or provide a CSV file."
                    )
                if response.status != 200:
                    raise ValueError(f"Failed to fetch sheet: HTTP {response.status}")

                text = await response.text()

                # If Google returns an HTML page, the sheet isn't publicly accessible.
                if "<!DOCTYPE html" in text[:200].lower() or "<html" in text[:200].lower():
                    raise ValueError(
                        "Received an HTML page instead of CSV data. Make sure the Google Sheet is shared with 'Anyone with the link' and try again."
                    )

                return text

    def parse_csv_data(self, csv_text: str) -> list:
        """Parse CSV text into row dictionaries with category awareness."""

        rows = list(csv.reader(io.StringIO(csv_text)))
        if not rows:
            return []

        parsed_data = []
        current_headers = None
        current_header_map = None
        current_category = "General"

        for row in rows:
            normalized_cells = [(cell or "").strip() for cell in row]
            if not any(normalized_cells):
                continue

            lower_cells = [cell.lower() for cell in normalized_cells]

            # Detect category labels (single cell like PASSING, RUSHING, etc.)
            if len([cell for cell in normalized_cells if cell]) == 1 and normalized_cells[0].isupper():
                current_category = normalized_cells[0]
                continue

            # Detect header rows (contain identifier keywords)
            if {cell for cell in lower_cells if cell} & self.IDENTIFIER_FIELDS:
                seen = {}
                current_headers = []
                current_header_map = {}
                for idx, header in enumerate(normalized_cells):
                    header = header or f"Column_{idx + 1}"
                    header = header.strip() or f"Column_{idx + 1}"
                    base = header.lower()
                    count = seen.get(base, 0)
                    if count:
                        unique_header = f"{header}_{count + 1}"
                        current_headers.append(unique_header)
                        seen[base] = count + 1
                    else:
                        current_headers.append(header)
                        seen[base] = 1
                    current_header_map[idx] = current_headers[-1]
                continue

            if not current_headers:
                continue

            values = list(row)
            record = {header: "" for header in current_headers}
            for idx, value in enumerate(values):
                header = current_header_map.get(idx)
                if header is not None:
                    record[header] = value

            record["__category"] = current_category
            parsed_data.append(record)

        return parsed_data

    @staticmethod
    def _split_key_suffix(key: str) -> tuple[str, str]:
        if not key:
            return "", ""
        parts = key.rsplit("_", 1)
        if len(parts) == 2 and parts[1].isdigit():
            return parts[0], f"_{parts[1]}"
        return key, ""

    def _extract_player_rows(self, row: dict) -> list[dict]:
        suffix_map = {}
        for key, value in row.items():
            if key.startswith("__"):
                continue
            base, suffix = self._split_key_suffix(key)
            suffix_map.setdefault(suffix, {})[base] = value

        player_rows = []
        for suffix, data in suffix_map.items():
            if not any((str(val).strip() for val in data.values() if val not in (None, ""))):
                continue
            player_rows.append({**data, "__suffix": suffix})

        return player_rows

    def _match_field(self, row: dict, *candidates: str):
        """Return the value for the first matching header name (case-insensitive)."""

        normalized = {}
        for key, value in row.items():
            normalized_key = (key or "").strip().lower()
            if normalized_key:
                normalized[normalized_key] = value

        for candidate in candidates:
            candidate = candidate.strip().lower()
            for key, value in normalized.items():
                if key == candidate or key.startswith(f"{candidate}_"):
                    return value
        return None

    @staticmethod
    def _to_number(value: object) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)

        text = str(value).strip()
        if not text:
            return None

        if text.endswith("%"):
            text = text[:-1].strip()

        text = text.replace(",", "")

        try:
            return float(text)
        except ValueError:
            return None

    def _store_stats_fields(
        self,
        base_data: dict,
        category: str,
        stats_fields: dict,
        week: Optional[int],
    ) -> None:
        stats = base_data.setdefault("stats", {})

        if week is None:
            category_bucket = stats.setdefault(category, {})
            category_bucket.update(stats_fields)
            return

        weeks_bucket = stats.setdefault("weeks", {})
        week_bucket = weeks_bucket.setdefault(f"week_{week}", {})
        category_bucket = week_bucket.setdefault(category, {})
        category_bucket.update(stats_fields)

        meta = stats.setdefault("meta", {})
        meta['last_import_week'] = week
        weeks_imported = meta.setdefault('weeks_imported', [])
        if week not in weeks_imported:
            weeks_imported.append(week)

    def _recalculate_season_totals(self, stats: dict) -> None:
        weeks_bucket = stats.get("weeks")
        if not weeks_bucket:
            stats.pop("season_totals", None)
            return

        totals: dict[str, dict[str, float]] = {}
        last_strings: dict[str, dict[str, str]] = {}

        for week_data in weeks_bucket.values():
            for category, fields in week_data.items():
                category_totals = totals.setdefault(category, {})
                category_strings = last_strings.setdefault(category, {})

                for key, value in fields.items():
                    numeric_value = self._to_number(value)
                    if numeric_value is not None:
                        category_totals[key] = category_totals.get(key, 0.0) + numeric_value
                    else:
                        category_strings[key] = str(value)

        season_totals: dict[str, dict[str, object]] = {}
        for category, fields in totals.items():
            category_total_values: dict[str, object] = {}
            for key, total in fields.items():
                if total.is_integer():
                    category_total_values[key] = int(total)
                else:
                    category_total_values[key] = round(total, 3)

            # Include non-numeric last values if they were never numeric
            for key, value in last_strings.get(category, {}).items():
                category_total_values.setdefault(key, value)

            season_totals[category] = category_total_values

        # Include categories that only had string values
        for category, values in last_strings.items():
            season_totals.setdefault(category, {})
            for key, value in values.items():
                season_totals[category].setdefault(key, value)

        stats["season_totals"] = season_totals

    @staticmethod
    def _create_master_entry(
        identifier: str,
        category: str,
        week: Optional[int],
        stats_fields: dict[str, object],
        contract: Optional[object] = None,
        demands: Optional[object] = None,
    ) -> dict:
        return {
            "identifier": (identifier or "").strip(),
            "category": category or "General",
            "week": week,
            "contract": contract,
            "demands": demands,
            "stats": {
                key: "" if value is None else str(value)
                for key, value in stats_fields.items()
            },
        }

    def _prepare_master_entries_from_parsed(
        self,
        data: list[dict],
        week: Optional[int],
    ) -> list[dict]:
        master_entries: list[dict] = []

        for row in data:
            category = row.get("__category", "General")
            player_rows = self._extract_player_rows(row)

            for player_data in player_rows:
                player_copy = dict(player_data)
                player_copy.pop("__suffix", None)

                user_identifier = self._match_field(
                    player_copy,
                    "user_id",
                    "discord_id",
                    "discord id",
                    "id",
                    "username",
                    "user",
                    "name",
                    "player",
                )

                if isinstance(user_identifier, str):
                    user_identifier = user_identifier.strip()

                if not user_identifier:
                    continue

                identifier_lower = user_identifier.lower()
                if (
                    identifier_lower in self.IGNORED_IDENTIFIERS
                    or identifier_lower.startswith("team ")
                ):
                    continue

                contract = player_copy.get("contract")
                demands = player_copy.get("demands")

                stats_fields: dict[str, object] = {}
                for key, value in player_copy.items():
                    if key.startswith("__"):
                        continue
                    key_lower = (key or "").strip().lower()
                    if key_lower in self.IDENTIFIER_FIELDS or key_lower in {"contract", "demands"}:
                        continue
                    if value not in (None, ""):
                        stats_fields[key] = value

                if not stats_fields and contract is None and demands is None:
                    continue

                master_entries.append(
                    self._create_master_entry(
                        identifier=user_identifier,
                        category=category,
                        week=week,
                        stats_fields=stats_fields,
                        contract=contract,
                        demands=demands,
                    )
                )

        return master_entries

    @staticmethod
    def _build_master_matrix(entries: list[dict]) -> list[list[object]]:
        if not entries:
            return []

        include_contract = any(entry.get("contract") not in (None, "") for entry in entries)
        include_demands = any(entry.get("demands") not in (None, "") for entry in entries)

        stat_keys: set[str] = set()
        for entry in entries:
            stats = entry.get("stats") or {}
            stat_keys.update(stats.keys())

        ordered_stats = sorted(stat_keys)

        header = ["Identifier", "Category", "Week"]
        if include_contract:
            header.append("Contract")
        if include_demands:
            header.append("Demands")
        header.extend(ordered_stats)

        matrix = [header]

        for entry in entries:
            row = [
                entry.get("identifier", ""),
                entry.get("category", ""),
                "" if entry.get("week") is None else str(entry.get("week")),
            ]

            if include_contract:
                row.append(entry.get("contract", ""))
            if include_demands:
                row.append(entry.get("demands", ""))

            stats = entry.get("stats") or {}
            for key in ordered_stats:
                row.append(stats.get(key, ""))

            matrix.append(row)

        return matrix

    def _copy_sheet_values_sync(
        self,
        source_sheet_id: str,
        source_gid: Optional[int],
        target_sheet_id: str,
        target_gid: Optional[int],
    ) -> int:
        """
        Blocking helper that clones all values from a source sheet into the configured master sheet.
        """
        if not self.gspread_client:
            raise RuntimeError("Google Sheets client not configured.")

        source_spreadsheet = self.gspread_client.open_by_key(source_sheet_id)
        source_sheet = (
            source_spreadsheet.get_worksheet_by_id(source_gid)
            if source_gid is not None
            else source_spreadsheet.sheet1
        )

        target_spreadsheet = self.gspread_client.open_by_key(target_sheet_id)
        target_sheet = (
            target_spreadsheet.get_worksheet_by_id(target_gid)
            if target_gid is not None
            else target_spreadsheet.sheet1
        )

        source_values = source_sheet.get_all_values()
        target_sheet.clear()

        if source_values:
            target_sheet.update("A1", source_values)

        # Subtract header row when reporting and guard against negative results.
        return max(len(source_values) - 1, 0)

    async def copy_sheet_to_master(
        self,
        source_sheet_id: str,
        source_gid: Optional[int],
    ) -> tuple[bool, str]:
        """
        Copy the entirety of a source worksheet into the configured master worksheet.
        """
        if not self.gspread_client:
            if self.gspread_init_error:
                return False, self.gspread_init_error
            return False, "Google Sheets client not configured."

        target_sheet_id, target_gid = self._get_master_sheet_target()
        if not target_sheet_id:
            return False, "Master sheet ID is not configured."

        try:
            rows_copied = await asyncio.to_thread(
                self._copy_sheet_values_sync,
                source_sheet_id,
                source_gid,
                target_sheet_id,
                target_gid,
            )
        except Exception as exc:  # pragma: no cover - defensive
            return False, f"Failed to clone source sheet: {exc}"

        if rows_copied <= 0:
            return True, "Source sheet contained only headers; master sheet cleared."

        return True, f"Copied {rows_copied} data rows from source sheet."

    def _push_master_sheet_sync(
        self,
        sheet_id: str,
        gid: Optional[int],
        matrix: list[list[object]],
    ) -> int:
        spreadsheet = self.gspread_client.open_by_key(sheet_id)  # type: ignore[union-attr]

        worksheet = None
        if gid is not None:
            try:
                worksheet = spreadsheet.get_worksheet_by_id(gid)
            except gspread.exceptions.WorksheetNotFound:
                worksheet = None

        if worksheet is None:
            worksheet = spreadsheet.sheet1

        existing = worksheet.get_all_values()

        header = matrix[0]
        appended_rows = matrix[1:]

        if not existing:
            worksheet.update("A1", [header])
            if appended_rows:
                worksheet.append_rows(appended_rows, value_input_option="RAW")
            return len(appended_rows)

        current_header = list(existing[0])
        missing_columns = [column for column in header if column not in current_header]
        if missing_columns:
            current_header.extend(missing_columns)
            worksheet.resize(
                rows=max(worksheet.row_count, 1),
                cols=len(current_header),
            )
            worksheet.update("A1", [current_header])

        header_index = {name: idx for idx, name in enumerate(current_header)}
        rows_to_append: list[list[object]] = []
        for row in appended_rows:
            row_map = {header[idx]: row[idx] for idx in range(len(header))}
            aligned = [row_map.get(name, "") for name in current_header]
            rows_to_append.append(aligned)

        if rows_to_append:
            worksheet.append_rows(rows_to_append, value_input_option="RAW")

        return len(rows_to_append)

    async def push_to_master_sheet_entries(
        self,
        entries: list[dict],
    ) -> tuple[bool, str]:
        if not entries:
            return False, "No entries to sync."

        if not self.gspread_client:
            if self.gspread_init_error:
                return False, self.gspread_init_error
            return False, "Google Sheets client not configured."

        sheet_id, gid = self._get_master_sheet_target()
        if not sheet_id:
            return False, "Master sheet ID is not configured."

        matrix = self._build_master_matrix(entries)
        if len(matrix) <= 1:
            return False, "Nothing to sync."

        try:
            appended = await asyncio.to_thread(
                self._push_master_sheet_sync,
                sheet_id,
                gid,
                matrix,
            )
        except Exception as exc:  # pragma: no cover - defensive
            return False, f"Failed to update master sheet: {exc}"

        if appended == 0:
            return False, "No rows were appended to the master sheet."

        return True, f"Appended {appended} row(s) to the master sheet."

    async def _resolve_user_identifier(
        self,
        inter: disnake.Interaction,
        identifier: str,
    ) -> tuple[Optional[str], Optional[str]]:
        """
        Convert a manual identifier into a Discord user ID or return an error message.
        """
        cleaned = (identifier or "").strip()
        if not cleaned:
            return None, "Missing user identifier"

        lowered = cleaned.lower()
        if lowered in self.IGNORED_IDENTIFIERS or lowered.startswith("team "):
            return None, f"Identifier '{identifier}' looks like a team/header value."

        sanitized = cleaned.replace("/", "_")

        try:
            numeric_id = int(cleaned)
            return str(numeric_id), None
        except ValueError:
            def _match(member: disnake.Member) -> bool:
                target = lowered
                name_match = member.name.lower() == target
                display_match = member.display_name and member.display_name.lower() == target
                return name_match or display_match

            member = disnake.utils.find(_match, inter.guild.members)
            if member:
                return str(member.id), None

            return sanitized, None

    async def process_manual_session(
        self,
        inter: disnake.MessageInteraction,
        session: ManualImportSession,
    ) -> tuple[int, int, list[str], list[dict]]:
        """
        Persist the staged manual entries into the database.
        Returns counts of imported/updated records, any issues, and successful entries for downstream sync.
        """
        imported = 0
        updated = 0
        issues: list[str] = []
        master_entries: list[dict] = []

        for index, entry in enumerate(session.entries, start=1):
            user_id, error = await self._resolve_user_identifier(inter, entry.identifier)
            if error:
                issues.append(f"Entry {index}: {error}")
            if user_id is None:
                issues.append(f"Entry {index}: Missing user identifier")
                continue

            existing_data = await Database.get_data("Users", f"{session.guild_id}/{user_id}")
            is_update = isinstance(existing_data, dict)
            import_data = copy.deepcopy(existing_data) if is_update else {}

            if entry.contract:
                import_data["contract"] = entry.contract.strip()

            if entry.demands:
                try:
                    import_data["demands"] = int(entry.demands)
                except ValueError:
                    import_data["demands"] = entry.demands.strip()

            category = entry.category.strip() or "General"
            if entry.stats:
                self._store_stats_fields(import_data, category, entry.stats, session.week)
                stats_ref = import_data.get("stats", {})
                if session.week is not None and stats_ref:
                    self._recalculate_season_totals(stats_ref)

            if not entry.stats and "contract" not in import_data and "demands" not in import_data:
                issues.append(f"Entry {index}: No actionable data provided.")
                continue

            await Database.add_data("Users", {session.guild_id: {user_id: import_data}})

            stats_snapshot = {
                key: value
                for key, value in (entry.stats or {}).items()
                if value not in (None, "")
            }

            if stats_snapshot or entry.contract or entry.demands:
                master_entries.append(
                    self._create_master_entry(
                        identifier=entry.identifier,
                        category=category,
                        week=session.week,
                        stats_fields=stats_snapshot,
                        contract=entry.contract,
                        demands=entry.demands,
                    )
                )

            if is_update:
                updated += 1
            else:
                imported += 1

        return imported, updated, issues, master_entries

    async def import_to_database(
        self,
        inter: disnake.GuildCommandInteraction,
        data: list,
        guild_id: int,
        week: Optional[int] = None,
    ):
        """
        Imports parsed data into the Users database table
        Expected columns: user_id (Discord ID), and optional fields like contract, demands, etc.
        """
        imported_count = 0
        updated_count = 0
        errors = []

        for row_num, row in enumerate(data, start=2):  # Start at 2 because row 1 is headers
            try:
                category = row.get("__category", "General")
                player_rows = self._extract_player_rows(row)

                for player_data in player_rows:
                    suffix = player_data.pop("__suffix", "")

                    user_identifier = self._match_field(
                        player_data,
                        'user_id',
                        'discord_id',
                        'discord id',
                        'id',
                        'username',
                        'user',
                        'name',
                        'player',
                    )

                    if isinstance(user_identifier, str):
                        user_identifier = user_identifier.strip()

                    identifier_lower = (user_identifier or "").strip().lower()

                    non_identifier_values = [
                        value
                        for key, value in player_data.items()
                        if key.lower() not in self.IDENTIFIER_FIELDS and value not in (None, "")
                    ]

                    if not user_identifier:
                        continue

                    if identifier_lower in self.IGNORED_IDENTIFIERS or identifier_lower.startswith("team "):
                        continue

                    # Try to convert to int if it's a Discord ID
                    try:
                        user_id = str(int(user_identifier))
                    except ValueError:
                        def _match(member):
                            target = user_identifier.lower()
                            return (
                                member.name.lower() == target
                                or (member.display_name and member.display_name.lower() == target)
                            )

                        member = disnake.utils.find(_match, inter.guild.members)
                        if member:
                            user_id = str(member.id)
                        else:
                            user_id = user_identifier.replace("/", "_")

                    # Prepare data to import
                    import_data = {}

                    # Import contract or demands if present within this player section
                    contract = player_data.get('contract')
                    if contract:
                        import_data['contract'] = contract

                    demands = player_data.get('demands')
                    if demands:
                        try:
                            import_data['demands'] = int(demands)
                        except ValueError:
                            pass

                    stats_fields = {}
                    for key, value in player_data.items():
                        if value in (None, ""):
                            continue
                        key_lower = (key or "").strip().lower()
                        if key_lower in self.IDENTIFIER_FIELDS or key_lower in {"contract", "demands"}:
                            continue
                        stats_fields[key] = value

                    if not stats_fields and contract is None and demands is None:
                        continue

                    # Get existing user data
                    existing_data = await Database.get_data("Users", f"{guild_id}/{user_id}")
                    is_update = existing_data is not None and isinstance(existing_data, dict)
                    import_data = copy.deepcopy(existing_data) if is_update else {}

                    if contract:
                        import_data['contract'] = contract

                    if demands:
                        try:
                            import_data['demands'] = int(demands)
                        except ValueError:
                            import_data['demands'] = demands

                    if stats_fields:
                        self._store_stats_fields(import_data, category, stats_fields, week)
                        stats_ref = import_data.get('stats', {})
                        if week is not None and stats_ref:
                            self._recalculate_season_totals(stats_ref)

                    if is_update:
                        updated_count += 1
                    else:
                        imported_count += 1

                    await Database.add_data("Users", {guild_id: {user_id: import_data}})

            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")

        return imported_count, updated_count, errors

    @commands.slash_command()
    @commands.has_permissions(administrator=True)
    async def import_statsheet(
        self,
        inter: disnake.GuildCommandInteraction,
        statsheet: str = None,
        file: disnake.Attachment = None,
        week: Optional[int] = commands.Param(
            default=None,
            ge=1,
            le=100,
            description="Week number to store these stats under (optional)",
        ),
    ):
        """
        Import data from a stat sheet into the master database
        
        Parameters
        ----------
        statsheet: Google Sheets URL or CSV data (leave empty if using file attachment)
        file: CSV file attachment (optional if using statsheet parameter)
        week: Optional week number; if provided, stats are stored in week-specific buckets
        """
        await inter.response.defer(ephemeral=True)

        # Check if user has franchise role (optional check)
        franchise_check = await has_role("FranchiseRole", inter.guild.id, inter.author)
        if not franchise_check:
            # Still allow if they're admin, but warn
            if not inter.author.guild_permissions.administrator:
                return await inter.send(
                    "You need to have a Franchise Role or Administrator permissions to use this command.",
                    ephemeral=True
                )

        csv_data = None
        source_sheet_meta: Optional[tuple[str, Optional[int]]] = None

        # Get CSV data from either URL or file attachment
        if file:
            if not file.filename.endswith('.csv'):
                return await inter.send(
                    f"{BotEmojis.x_mark} Please attach a CSV file.",
                    ephemeral=True
                )
            
            try:
                csv_data = (await file.read()).decode('utf-8')
            except Exception as e:
                return await inter.send(
                    f"{BotEmojis.x_mark} Failed to read file: {str(e)}",
                    ephemeral=True
                )

        elif statsheet:
            # Check if it's a Google Sheets URL
            if 'docs.google.com/spreadsheets' in statsheet or 'drive.google.com' in statsheet:
                try:
                    source_sheet_meta = self._parse_sheet_url(statsheet)
                    csv_data = await self.fetch_google_sheet(statsheet)
                except Exception as e:
                    return await inter.send(
                        f"{BotEmojis.x_mark} Failed to fetch Google Sheet: {str(e)}",
                        ephemeral=True
                    )
            else:
                # Assume it's raw CSV data
                csv_data = statsheet

        else:
            return await inter.send(
                f"{BotEmojis.x_mark} Please provide either a Google Sheets URL, CSV data, or attach a CSV file.",
                ephemeral=True
            )

        # Parse CSV data
        try:
            parsed_data = self.parse_csv_data(csv_data)
            if not parsed_data:
                return await inter.send(
                    f"{BotEmojis.x_mark} No data found in the sheet. Make sure it has at least one data row.",
                    ephemeral=True
                )
        except Exception as e:
            return await inter.send(
                f"{BotEmojis.x_mark} Failed to parse CSV data: {str(e)}",
                ephemeral=True
            )

        # Import to database
        try:
            imported, updated, errors = await self.import_to_database(
                inter, parsed_data, inter.guild.id, week=week
            )

            master_entries = self._prepare_master_entries_from_parsed(parsed_data, week)
            master_sync_result: Optional[tuple[bool, str]] = None
            # Always attempt to sync parsed entries for downstream reporting.
            if master_entries:
                master_sync_result = await self.push_to_master_sheet_entries(master_entries)

            sheet_clone_result: Optional[tuple[bool, str]] = None
            if source_sheet_meta and self.gspread_client:
                sheet_clone_result = await self.copy_sheet_to_master(*source_sheet_meta)

            # Create result embed
            embed = Embed(
                title="Import Complete",
                description="Successfully imported data from stat sheet"
            )

            if week is not None:
                embed.description += f" (stored under week {week})"

            embed.add_field(
                name=f"{BotEmojis.check_mark} Results",
                value=f"**Imported:** {imported} new entries\n**Updated:** {updated} existing entries\n**Total Processed:** {imported + updated}",
                inline=False
            )

            file_attachment = None
            if errors:
                error_text = "\n".join(errors[:10])  # Show first 10 errors
                if len(errors) > 10:
                    error_text += f"\n... and {len(errors) - 10} more errors"
                embed.add_field(
                    name=f"{BotEmojis.warn} Errors",
                    value=f"```{error_text}```",
                    inline=False
                )

                # Provide full error log as downloadable file
                error_buffer = io.BytesIO("\n".join(errors).encode("utf-8"))
                file_attachment = disnake.File(fp=error_buffer, filename="import_errors.txt")

            if master_sync_result:
                success, message = master_sync_result
                field_name = (
                    f"{BotEmojis.check_mark} Master Sheet"
                    if success
                    else f"{BotEmojis.warn} Master Sheet"
                )
                embed.add_field(name=field_name, value=message, inline=False)

            if sheet_clone_result:
                success, message = sheet_clone_result
                field_name = (
                    f"{BotEmojis.check_mark} Sheet Clone"
                    if success
                    else f"{BotEmojis.warn} Sheet Clone"
                )
                embed.add_field(name=field_name, value=message, inline=False)

            embed.set_footer(text=f"Requested by {inter.author.display_name}")

            if file_attachment:
                await inter.send(embed=embed, file=file_attachment, ephemeral=True)
            else:
                await inter.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            await inter.send(
                f"{BotEmojis.x_mark} Failed to import data: {str(e)}",
                ephemeral=True
            )

    @commands.slash_command()
    @commands.has_permissions(administrator=True)
    async def manual_import(
        self,
        inter: disnake.GuildCommandInteraction,
        week: Optional[int] = commands.Param(
            default=None,
            ge=1,
            le=100,
            description="Week number to store these stats under (optional)",
        ),
    ):
        """Launch the manual stats entry workflow (staff only)."""
        await inter.response.defer(ephemeral=True)

        franchise_check = await has_role("FranchiseRole", inter.guild.id, inter.author)
        if not franchise_check and not inter.author.guild_permissions.administrator:
            return await inter.send(
                "You need to have a Franchise Role or Administrator permissions to use this command.",
                ephemeral=True,
            )

        session = ManualImportSession(guild_id=inter.guild.id, week=week)
        self.manual_sessions[inter.author.id] = session

        embed = Embed(
            title="Manual Stat Import",
            description=(
                "Use the buttons below to add player stat blocks manually. "
                "Each entry can include a category, stat values, and optional contract/demand updates."
            ),
        )
        if week is not None:
            embed.add_field(name="Week Target", value=f"Week {week}", inline=False)
        embed.add_field(
            name="How It Works",
            value=(
                "➕ **Add Player Stats** – Open the form and paste stats as `name=value` lines.\n"
                "📋 **Preview Entries** – Review what you have staged.\n"
                "💾 **Submit to Database** – Save everything in one step.\n"
                "✖️ **Cancel Session** – Discard staged entries if you change your mind."
            ),
            inline=False,
        )
        embed.set_footer(text="Only you can see this session. It will expire after 10 minutes of inactivity.")

        view = ManualImportView(self, inter.author.id)
        await inter.send(embed=embed, view=view, ephemeral=True)

    # Manual import lets staff stage multiple entries, edit them, then commit everything in one submission.
    @commands.slash_command()
    @commands.has_permissions(administrator=True)
    async def clear_statsheet(
        self,
        inter: disnake.GuildCommandInteraction,
        week: Optional[int] = commands.Param(
            default=None,
            ge=1,
            le=100,
            description="Week number to remove (leave empty to clear all stats)",
        ),
        player: Optional[str] = commands.Param(
            default=None,
            description="Only clear stats for this identifier (optional)",
        ),
        confirm: bool = commands.Param(
            default=False,
            description="Set to True when clearing everything without filters",
        ),
    ):
        # Clearing scope:
        #   - `player` set: restricts deletion to a single identifier.
        #   - `week` set: removes the week bucket and recalculates season totals.
        #   - neither set: wipes all stored stats (requires confirm=True).
        """Remove previously imported stats from the Users database."""
        await inter.response.defer(ephemeral=True)

        franchise_check = await has_role("FranchiseRole", inter.guild.id, inter.author)
        if not franchise_check and not inter.author.guild_permissions.administrator:
            return await inter.send(
                "You need to have a Franchise Role or Administrator permissions to use this command.",
                ephemeral=True,
            )

        if week is None and player is None and not confirm:
            return await inter.send(
                f"{BotEmojis.warn} This will wipe every stored stat. Re-run with `confirm=True` to proceed.",
                ephemeral=True,
            )

        target_user_id: Optional[str] = None
        if player:
            target_user_id, error = await self._resolve_user_identifier(inter, player)
            if error:
                return await inter.send(
                    f"{BotEmojis.warn} {error}",
                    ephemeral=True,
                )
            if not target_user_id:
                return await inter.send(
                    f"{BotEmojis.warn} Could not resolve `{player}` to a stored identifier.",
                    ephemeral=True,
                )

        guild_key = str(inter.guild.id)
        guild_data = await Database.get_data("Users", guild_key)
        if not isinstance(guild_data, dict) or not guild_data:
            return await inter.send(
                f"{BotEmojis.warn} No player data found for this server.",
                ephemeral=True,
            )

        updates: dict[str, dict] = {}
        deletions: list[str] = []
        players_cleared = 0
        weeks_removed = 0

        def _cleanup_stats_container(stats_container: dict) -> None:
            """
            Remove empty helper dictionaries after pruning week data.
            """
            if not isinstance(stats_container, dict):
                return

            weeks_bucket = stats_container.get("weeks")
            if isinstance(weeks_bucket, dict) and not weeks_bucket:
                stats_container.pop("weeks", None)

            meta = stats_container.get("meta")
            if isinstance(meta, dict) and week is not None:
                weeks_imported = meta.get("weeks_imported")
                if isinstance(weeks_imported, list):
                    meta["weeks_imported"] = [w for w in weeks_imported if w != week]
                    if not meta["weeks_imported"]:
                        meta.pop("weeks_imported", None)
                if not meta:
                    stats_container.pop("meta", None)

            if not stats_container:
                return

            if set(stats_container.keys()) == {"meta"} and not stats_container["meta"]:
                stats_container.clear()

        for raw_user_id, record in guild_data.items():
            if target_user_id is not None and str(raw_user_id) != str(target_user_id):
                continue

            if not isinstance(record, dict):
                continue

            stats = record.get("stats")
            if not isinstance(stats, dict):
                continue

            changed = False

            if week is None:
                record.pop("stats", None)
                changed = True
            else:
                weeks_bucket = stats.get("weeks")
                if isinstance(weeks_bucket, dict):
                    removed = weeks_bucket.pop(f"week_{week}", None)
                    if removed:
                        weeks_removed += 1
                        changed = True

                if changed:
                    self._recalculate_season_totals(stats)
                    _cleanup_stats_container(stats)
                    if not stats:
                        record.pop("stats", None)

            if changed:
                players_cleared += 1
                if record:
                    updates[str(raw_user_id)] = record
                else:
                    deletions.append(str(raw_user_id))

        if not updates and not deletions:
            return await inter.send(
                f"{BotEmojis.warn} No stats matched the provided filters.",
                ephemeral=True,
            )

        if updates:
            await Database.add_data("Users", {inter.guild.id: updates})
        for user_id in deletions:
            await Database.delete_data("Users", f"{inter.guild.id}/{user_id}")

        summary_bits = []
        if week is not None:
            summary_bits.append(f"Week {week} removed from {players_cleared} player(s).")
            if weeks_removed == 0 and players_cleared:
                summary_bits.append("No stored week buckets matched that number.")
        else:
            summary_bits.append(f"Cleared all stats for {players_cleared} player(s).")

        scope_text = (
            f"Player filter: `{player or 'All players'}`\n"
            f"Week filter: `{week or 'All weeks'}`"
        )

        embed = Embed(
            title="Statsheet Cleanup Complete",
            description=" ".join(summary_bits) if summary_bits else "Stats cleared successfully.",
            guild=inter.guild,
            user=inter.author,
        )
        embed.add_field(name="Scope", value=scope_text, inline=False)
        embed.set_footer(text="Season totals were recalculated for affected players.")

        await inter.send(embed=embed, ephemeral=True)


def setup(bot):
    bot.add_cog(Import(bot))

