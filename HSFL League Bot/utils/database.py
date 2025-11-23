import json
import os
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Any, Optional, Dict
import shutil
import logging

DATABASE_DIR = Path("database")
BACKUP_DIR = Path("database/backups")
LOCK_DIR = Path("database/locks")
MAX_BACKUPS = 10

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    """
    Local JSON-based database system
    Stores all data in JSON files within the 'database' folder
    Maintains the same API as the remote database for compatibility
    """
    
    def __init__(self):
        """
        Initialize database directory if it doesn't exist
        """
        DATABASE_DIR.mkdir(exist_ok=True)
        BACKUP_DIR.mkdir(exist_ok=True, parents=True)
        LOCK_DIR.mkdir(exist_ok=True, parents=True)
    
    def _get_lock_file(self, key: str) -> Path:
        """
        Get the lock file path for a database key
        """
        safe_key = str(key).replace("/", "_").replace("\\", "_")
        return LOCK_DIR / f"{safe_key}.lock"
    
    async def _acquire_lock(self, key: str, timeout: float = 5.0) -> bool:
        """
        Acquire a lock for database operations
        Returns True if lock acquired, False if timeout
        """
        lock_file = self._get_lock_file(key)
        start_time = asyncio.get_event_loop().time()
        
        while True:
            try:
                lock_file.touch(exist_ok=False)
                return True
            except FileExistsError:
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > timeout:
                    logger.warning(f"Lock timeout for key: {key}")
                    return False
                await asyncio.sleep(0.1)
    
    async def _release_lock(self, key: str):
        """
        Release a lock after database operations
        """
        lock_file = self._get_lock_file(key)
        try:
            lock_file.unlink(missing_ok=True)
        except Exception as e:
            logger.error(f"Error releasing lock for {key}: {e}")
    
    async def _create_backup(self, file_path: Path) -> bool:
        """
        Create a backup of the database file before writing
        """
        if not file_path.exists():
            return True
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = file_path.stem
            backup_path = BACKUP_DIR / f"{file_name}_{timestamp}.json"
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, shutil.copy2, file_path, backup_path)
            
            await self._cleanup_old_backups(file_name)
            logger.info(f"Backup created: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Error creating backup for {file_path}: {e}")
            return False
    
    async def _cleanup_old_backups(self, file_name: str):
        """
        Remove old backups, keeping only the most recent MAX_BACKUPS
        """
        try:
            backups = sorted(BACKUP_DIR.glob(f"{file_name}_*.json"), reverse=True)
            for old_backup in backups[MAX_BACKUPS:]:
                old_backup.unlink()
        except Exception as e:
            logger.error(f"Error cleaning up backups: {e}")
    
    def _get_file_path(self, key: str) -> Path:
        """
        Get the file path for a database key
        Converts key to a safe filename
        """
        safe_key = str(key).replace("/", "_").replace("\\", "_")
        return DATABASE_DIR / f"{safe_key}.json"
    
    async def _load_file(self, file_path: Path) -> dict:
        """
        Load data from a JSON file (async) with validation
        Returns empty dict if file doesn't exist or is corrupted
        """
        if not file_path.exists():
            return {}
        
        try:
            loop = asyncio.get_event_loop()
            def _read():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            data = await loop.run_in_executor(None, _read)
            
            if not isinstance(data, dict):
                logger.warning(f"Invalid data structure in {file_path}, expected dict")
                return {}
            
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Corrupted JSON file {file_path}: {e}")
            await self._attempt_recovery(file_path)
            return {}
        except IOError as e:
            logger.error(f"Error loading database file {file_path}: {e}")
            return {}
    
    async def _attempt_recovery(self, file_path: Path):
        """
        Attempt to recover from a corrupted file by using the latest backup
        """
        try:
            file_name = file_path.stem
            backups = sorted(BACKUP_DIR.glob(f"{file_name}_*.json"), reverse=True)
            
            if backups:
                logger.info(f"Attempting recovery for {file_path} using {backups[0]}")
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, shutil.copy2, backups[0], file_path)
                logger.info(f"Successfully recovered {file_path}")
                return True
        except Exception as e:
            logger.error(f"Recovery failed for {file_path}: {e}")
        
        return False
    
    async def _save_file(self, file_path: Path, data: dict):
        """
        Save data to a JSON file (async) with locking and backups
        Creates parent directories if needed
        """
        file_path.parent.mkdir(parents=True, exist_ok=True)
        key = file_path.stem
        
        if not await self._acquire_lock(key):
            raise IOError(f"Failed to acquire lock for {file_path} - concurrent write detected")
        
        try:
            await self._create_backup(file_path)
            
            loop = asyncio.get_event_loop()
            def _write():
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            await loop.run_in_executor(None, _write)
            logger.info(f"Successfully saved {file_path}")
        except IOError as e:
            logger.error(f"Error saving database file {file_path}: {e}")
            raise
        finally:
            await self._release_lock(key)
    
    def _get_nested_value(self, data: dict, path: str):
        """
        Get a nested value from a dictionary using a path string
        Path format: "key1/key2/key3" or "key1"
        Handles both string and integer keys (converts to string for lookup)
        """
        if not path:
            return data
        
        if not isinstance(data, dict):
            return None
        
        keys = path.split('/')
        current = data
        
        for key in keys:
            # Try string key first (most common)
            if isinstance(current, dict) and key in current:
                current = current[key]
            # Try integer key if string lookup fails
            elif isinstance(current, dict):
                try:
                    int_key = int(key)
                    if int_key in current:
                        current = current[int_key]
                    else:
                        return None
                except (ValueError, TypeError):
                    return None
            else:
                return None
        
        return current
    
    def _set_nested_value(self, data: dict, path: str, value):
        """
        Set a nested value in a dictionary using a path string
        Creates intermediate dictionaries as needed
        """
        if not path:
            return
        
        keys = path.split('/')
        current = data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def _validate_data(self, data: Any) -> bool:
        """
        Validate data before saving to ensure it's serializable
        """
        try:
            json.dumps(data)
            return True
        except (TypeError, ValueError) as e:
            logger.error(f"Data validation failed: {e}")
            return False
    
    def _delete_nested_value(self, data: dict, path: str):
        """
        Delete a nested value from a dictionary using a path string
        """
        if not path:
            return
        
        keys = path.split('/')
        current = data
        
        for key in keys[:-1]:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return
        
        if isinstance(current, dict) and keys[-1] in current:
            del current[keys[-1]]
    
    @staticmethod
    async def get_db_all():
        """
        Get all database keys and their data
        Returns a dictionary of all keys and values
        """
        db = Database()
        result = {}
        
        if not DATABASE_DIR.exists():
            return result
        
        for file_path in DATABASE_DIR.glob("*.json"):
            key = file_path.stem.replace("_", "/")
            data = await db._load_file(file_path)
            result[key] = data
        
        return result
    
    @staticmethod
    async def get_data(key, path=None):
        """
        Get data from the database
        key: The main database key (e.g., "Users", "FranchiseRole")
        path: Optional nested path (e.g., "123456789/987654321/contract" or integer guild_id)
        """
        db = Database()
        file_path = db._get_file_path(key)
        data = await db._load_file(file_path)
        
        if path is None:
            return data if data else None
        
        # Convert path to string for consistency (keys are stored as strings)
        if isinstance(path, int):
            path = str(path)
        elif isinstance(path, (list, tuple)):
            path = '/'.join(str(p) for p in path)
        else:
            path = str(path)
        
        result = db._get_nested_value(data, path)
        return result if result is not None else None
    
    @staticmethod
    async def get_db_prefix(prefix=None):
        """
        Get all keys that start with a prefix
        """
        db = Database()
        result = {}
        
        if not DATABASE_DIR.exists():
            return result
        
        prefix_str = str(prefix) if prefix else ""
        
        for file_path in DATABASE_DIR.glob("*.json"):
            key = file_path.stem.replace("_", "/")
            if key.startswith(prefix_str):
                data = await db._load_file(file_path)
                result[key] = data
        
        return result
    
    @staticmethod
    async def get_db_keys():
        """
        Get all database keys
        Returns a list of all keys
        """
        db = Database()
        keys = []
        
        if not DATABASE_DIR.exists():
            return keys
        
        for file_path in DATABASE_DIR.glob("*.json"):
            key = file_path.stem.replace("_", "/")
            keys.append(key)
        
        return keys
    
    @staticmethod
    async def add_data(key, value):
        """
        Add or update data in the database
        key: The main database key
        value: The data to store (can be dict, list, or primitive)
        
        If value is a dict with nested paths like {guild_id: {user_id: data}},
        it will merge with existing data
        """
        db = Database()
        
        if not db._validate_data(value):
            raise ValueError(f"Invalid data structure for key {key} - data is not JSON serializable")
        
        file_path = db._get_file_path(key)
        existing_data = await db._load_file(file_path)
        
        def convert_ints_to_strings(obj):
            """
            Convert integers to strings for JSON compatibility
            """
            if isinstance(obj, int):
                return str(obj)
            elif isinstance(obj, dict):
                return {k: convert_ints_to_strings(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_ints_to_strings(elem) for elem in obj]
            else:
                return obj
        
        value = convert_ints_to_strings(value)
        
        if isinstance(value, dict) and isinstance(existing_data, dict):
            def deep_merge(base, update):
                """
                Deep merge two dictionaries
                """
                for key, val in update.items():
                    if key in base and isinstance(base[key], dict) and isinstance(val, dict):
                        deep_merge(base[key], val)
                    else:
                        base[key] = val
                return base
            
            existing_data = deep_merge(existing_data, value)
        else:
            existing_data = value
        
        await db._save_file(file_path, existing_data)
        return existing_data
    
    @staticmethod
    async def delete_data(key, path=None):
        """
        Delete data from the database
        key: The main database key
        path: Optional nested path to delete specific data
        If path is None, deletes the entire key
        """
        db = Database()
        file_path = db._get_file_path(key)
        
        if not file_path.exists():
            return None
        
        data = await db._load_file(file_path)
        
        if path is None:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, file_path.unlink)
            return {"deleted": True}
        
        db._delete_nested_value(data, path)
        await db._save_file(file_path, data)
        return data
    
    @staticmethod
    async def verify_integrity():
        """
        Verify database integrity and attempt recovery of corrupted files
        Returns a report of issues found and fixed
        """
        db = Database()
        report = {
            "checked": 0,
            "corrupted": 0,
            "recovered": 0,
            "errors": []
        }
        
        if not DATABASE_DIR.exists():
            return report
        
        for file_path in DATABASE_DIR.glob("*.json"):
            report["checked"] += 1
            try:
                data = await db._load_file(file_path)
                if not data and file_path.exists():
                    report["corrupted"] += 1
                    if await db._attempt_recovery(file_path):
                        report["recovered"] += 1
                    else:
                        report["errors"].append(f"Failed to recover {file_path}")
            except Exception as e:
                report["errors"].append(f"Error checking {file_path}: {e}")
        
        logger.info(f"Database integrity check complete: {report}")
        return report
    
    @staticmethod
    async def get_backup_status():
        """
        Get information about available backups
        """
        if not BACKUP_DIR.exists():
            return {}
        
        backup_info = {}
        for file_name in {f.stem.rsplit('_', 1)[0] for f in BACKUP_DIR.glob("*.json")}:
            backups = sorted(BACKUP_DIR.glob(f"{file_name}_*.json"), reverse=True)
            backup_info[file_name] = {
                "count": len(backups),
                "latest": backups[0].name if backups else None,
                "oldest": backups[-1].name if backups else None
            }
        
        return backup_info
    
    @staticmethod
    async def restore_from_backup(key: str, backup_name: str):
        """
        Restore a database file from a specific backup
        """
        try:
            backup_path = BACKUP_DIR / backup_name
            if not backup_path.exists():
                logger.error(f"Backup file not found: {backup_name}")
                return False
            
            db = Database()
            file_path = db._get_file_path(key)
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, shutil.copy2, backup_path, file_path)
            logger.info(f"Successfully restored {key} from {backup_name}")
            return True
        except Exception as e:
            logger.error(f"Error restoring from backup: {e}")
            return False
    
    @staticmethod
    async def export_database(export_path: str = None):
        """
        Export entire database to a single JSON file with timestamp
        Useful for manual backups
        """
        try:
            if export_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                export_path = f"database_export_{timestamp}.json"
            
            db = Database()
            all_data = await Database.get_db_all()
            
            loop = asyncio.get_event_loop()
            def _export():
                with open(export_path, 'w', encoding='utf-8') as f:
                    json.dump(all_data, f, indent=2, ensure_ascii=False)
            
            await loop.run_in_executor(None, _export)
            logger.info(f"Database exported to {export_path}")
            return export_path
        except Exception as e:
            logger.error(f"Error exporting database: {e}")
            return None
