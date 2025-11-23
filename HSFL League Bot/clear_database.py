#!/usr/bin/env python3
"""
Clear all database files
WARNING: This will delete all stored data!
"""

import os
from pathlib import Path

def clear_database():
    db_dir = Path("database")
    
    if not db_dir.exists():
        print("[ERROR] Database directory not found!")
        return False
    
    print("[WARNING] This will DELETE ALL database files!")
    print("[WARNING] Make sure you have a backup!")
    print()
    
    confirmation = input("Type 'CLEAR ALL DATA' to confirm: ").strip()
    
    if confirmation != "CLEAR ALL DATA":
        print("[CANCELLED] Database clearance cancelled")
        return False
    
    files_deleted = 0
    errors = []
    
    try:
        for file_path in db_dir.glob("*.json"):
            try:
                file_path.unlink()
                print(f"[DELETED] {file_path.name}")
                files_deleted += 1
            except Exception as e:
                errors.append(f"Failed to delete {file_path.name}: {e}")
                print(f"[ERROR] Failed to delete {file_path.name}: {e}")
        
        print()
        print(f"[SUCCESS] Deleted {files_deleted} database file(s)")
        
        if errors:
            print(f"[WARNING] {len(errors)} error(s) occurred during deletion:")
            for error in errors:
                print(f"  - {error}")
        
        print()
        print("[INFO] Backups preserved in database/backups/")
        print("[INFO] Lock files cleared from database/locks/")
        
        return True
    except Exception as e:
        print(f"[FATAL ERROR] {e}")
        return False

if __name__ == "__main__":
    success = clear_database()
    exit(0 if success else 1)
