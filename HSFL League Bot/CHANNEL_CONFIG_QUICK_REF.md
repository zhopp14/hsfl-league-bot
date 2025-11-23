# Channel Configuration - Quick Reference

## Admin Setup (One-time Setup)

```
/channel set channel_type:Transactions channel:#transactions
/channel set channel_type:Offers channel:#offers
/channel set channel_type:Demands channel:#demands
/channel set channel_type:Trades channel:#trades
```

## View Configuration

```
/channel list
```

## Manage Channels

```
# Add another channel to a type
/channel set channel_type:Transactions channel:#admin-transactions

# Remove a channel
/channel remove channel_type:Transactions channel:#admin-transactions

# Clear all channels for a type (allow everywhere)
/channel clear channel_type:Transactions
```

## Command-to-Channel Mapping

| Command | Channel Type | Example |
|---------|--------------|---------|
| `/offer` | Offers | #offers |
| `/release` | Transactions | #transactions |
| `/demand` | Demands | #demands |
| `/promote` | Transactions | #transactions |
| `/demote` | Transactions | #transactions |
| `/trade` | Trades | #trades |
| `/trade-block` | Trades | #trades |

## Examples

### Setup for Organized Leagues

```
/channel set channel_type:Transactions channel:#transactions
/channel set channel_type:Transactions channel:#admin-zone
/channel set channel_type:Offers channel:#offers
/channel set channel_type:Demands channel:#demands
/channel set channel_type:Trades channel:#trades
```

Result: Different command types restricted to specific channels, with admin-zone allowing all transactions.

### No Restrictions

```
/channel clear channel_type:Transactions
/channel clear channel_type:Offers
/channel clear channel_type:Demands
/channel clear channel_type:Trades
```

Result: All commands work in any channel.

### Single Channel for All

```
/channel set channel_type:Transactions channel:#all-transactions
/channel set channel_type:Offers channel:#all-transactions
/channel set channel_type:Demands channel:#all-transactions
/channel set channel_type:Trades channel:#all-transactions
```

Result: All transaction commands in one channel.

## Error Messages & Fixes

| Error | Solution |
|-------|----------|
| "You can only use this command in: #channel" | Use the command in the specified channel |
| "Permission Denied" | Have a server admin configure channels |
| "Channel already configured" | Remove the channel first, then re-add if needed |

## Notes

- Empty channel types (cleared) allow commands everywhere
- Multiple channels per type = commands work in any of those channels
- All setup is done by admins using `/channel` commands
- No code changes needed to add new command types or channels
