# Database System Guide

## Overview

The HSFL League Bot uses a JSON-based database system with built-in reliability features:

- **File Locking**: Prevents concurrent writes that could corrupt data
- **Automatic Backups**: Creates backups before every write operation
- **Corruption Detection**: Automatically detects and recovers corrupted files
- **Data Validation**: Ensures all data is JSON-serializable before saving
- **Integrity Checking**: Verifies database health on startup

## File Structure

```
database/
├── Users.json                    # User data and profiles
├── FranchiseRole.json           # Franchise role mappings
├── AutoUpdateRoles.json         # Auto-update role configurations
├── Suspensions.json             # User suspension records
├── NotficationChannel.json      # Notification channel settings
├── RefereeChannel.json          # Referee channel settings
├── PickupChannel.json           # Pickup channel settings
├── OfferingChannel.json         # Offering channel settings
├── SigningChannel.json          # Signing channel settings
├── StreamingChannel.json        # Streaming channel settings
├── backups/                     # Automatic backups (last 10 per file)
│   ├── Users_20250123_143022.json
│   ├── Users_20250123_142015.json
│   └── ...
└── locks/                       # Lock files during operations
```

## Usage Examples

### Basic Operations

```python
from utils.database import Database

# Get data
user_data = await Database.get_data("Users", "user_id_123")

# Add/update data
await Database.add_data("Users", {"user_id_123": {"name": "John"}})

# Delete data
await Database.delete_data("Users", "user_id_123")

# Get all data from a key
all_users = await Database.get_data("Users")
```

### Admin Commands

The bot includes maintenance commands for database management:

#### Check Database Health
```
/db_health
```
Verifies integrity of all database files and attempts recovery of corrupted files.
- Shows: Files checked, corrupted files, recovered files, any errors

#### View Backup Status
```
/db_backups
```
Shows available backups for each database file.
- Displays: Number of backups, latest backup, oldest backup

#### Export Database
```
/db_export
```
Creates a full database export as a single JSON file with timestamp.
- Useful for manual backups or data analysis
- File saved as: `database_export_YYYYMMDD_HHMMSS.json`

## How It Works

### Write Operations with Locking

1. Request write lock for the file
2. Wait up to 5 seconds for lock acquisition
3. If lock timeout, operation fails
4. Create backup of current file
5. Write new data atomically
6. Release lock

### Corruption Recovery

When a corrupted file is detected:
1. Log the error
2. Attempt recovery from latest backup
3. If recovery succeeds, database resumes normally
4. If recovery fails, empty dict is returned to prevent cascading failures

### Backup Cleanup

- Maximum 10 backups kept per file
- Oldest backups are automatically deleted
- Backups include timestamp: `filename_YYYYMMDD_HHMMSS.json`

## Troubleshooting

### Database Lock Timeout
**Problem**: "Failed to acquire lock for file - concurrent write detected"

**Solution**: 
- Check for multiple bot instances running
- Restart the bot to clear stuck locks
- Use `/db_health` to verify integrity

### Corrupted JSON Files
**Problem**: Database operations fail silently

**Solution**:
- Run `/db_health` to detect corruption
- Use `/db_backups` to see available backups
- System automatically recovers from latest backup

### Missing Backups
**Problem**: Backup recovery not available

**Solution**:
- Use `/db_export` to create a manual backup
- Configure backup location if needed
- Consider setting up regular exports

## Performance Considerations

- **Lock timeout**: 5 seconds per operation
- **Backup creation**: Happens before every write
- **Integrity check**: ~100ms for 10 files on startup
- **Concurrent operations**: Handled safely by file locking

## Monitoring

Check logs for database operations:
```
[DATABASE] Initializing database...
[DATABASE] Verifying database integrity...
[DATABASE] All database files healthy
```

Error logs will show:
- Corruption detection and recovery
- Lock acquisition failures
- Backup creation issues
- Data validation errors

## Best Practices

1. **Regular Exports**: Run `/db_export` weekly for manual backups
2. **Monitor Health**: Check `/db_health` regularly
3. **Review Backups**: Use `/db_backups` to ensure backups are being created
4. **Handle Errors**: Wrap database calls in try-except blocks
5. **Validate Data**: Ensure all data is JSON-serializable before saving

## Technical Details

### Data Validation
All data must be JSON-serializable:
- Dicts, lists, strings, numbers, booleans, null
- Not allowed: datetime objects, custom classes, circular references

### Lock Mechanism
- Uses filesystem empty files in `database/locks/`
- Non-blocking checks every 100ms
- 5-second timeout prevents deadlocks

### Backup Strategy
- COW (Copy-on-Write) for safety
- Timestamps prevent overwrites
- Automatic cleanup prevents disk space issues

## Recovery Procedures

### Manual Recovery from Backup
```python
# List available backups
backups = await Database.get_backup_status()

# Restore from specific backup
await Database.restore_from_backup("Users", "Users_20250123_143022.json")
```

### Full Database Export/Import
```python
# Export everything
export_file = await Database.export_database()

# Import manually by copying file back to database/
```

## Support

For database issues, check the logs and run:
```
/db_health          # Verify integrity
/db_backups         # Check backup status
/db_export          # Create manual backup
```
