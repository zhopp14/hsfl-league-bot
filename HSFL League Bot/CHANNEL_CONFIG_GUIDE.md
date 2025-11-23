# Channel Configuration System Guide

## Overview

The League Bot now features a dynamic channel configuration system that allows admins to specify which channels specific command types can be executed in. Instead of hardcoding channels with specific naming conventions, you can now explicitly assign channels to command categories.

## Features

- **Dynamic Channel Assignment**: Set, remove, and manage channels for different command types
- **Multiple Channels Per Type**: Assign multiple channels to the same command type
- **Backward Compatible**: If no channels are configured, all channels are allowed (no restrictions)
- **Easy Management**: Simple admin commands to configure all settings
- **Flexible Categories**: Define your own command type names (e.g., "Transactions", "Offers", "Demands", "Trades", etc.)

## Command Types

The system supports any command type you define, but here are the recommended standard types:

- **Transactions**: `/offer`, `/release`, `/promote`, `/demote` commands
- **Offers**: `/offer` command only
- **Demands**: `/demand` command only
- **Trades**: `/trade`, `/trade-block` commands
- **Pickups**: Future pickup system commands

## Commands

### `/channel set <channel_type> <channel>`

Assign a channel to a command type. Admins only.

```
/channel set channel_type:Transactions channel:#transactions-log
/channel set channel_type:Offers channel:#offers
/channel set channel_type:Demands channel:#demands
/channel set channel_type:Trades channel:#trades
```

**Result**: The specified channel is added to the list of allowed channels for that command type.

### `/channel remove <channel_type> <channel>`

Remove a channel from a command type. Admins only.

```
/channel remove channel_type:Transactions channel:#transactions-log
```

**Result**: The channel is removed from the allowed channels list.

### `/channel list`

View all configured channels organized by command type.

```
/channel list
```

**Output**: Shows all command types and their assigned channels.

### `/channel clear <channel_type>`

Clear all channels for a specific command type. Admins only.

```
/channel clear channel_type:Transactions
```

**Result**: All channels are removed for that command type, allowing commands in any channel.

## Usage Examples

### Scenario 1: Enforce Transaction Channels

1. Create three channels:
   - `#transactions` - General signing transactions
   - `#offers` - Offer announcements
   - `#demands` - Demand announcements

2. Run commands:
   ```
   /channel set channel_type:Transactions channel:#transactions
   /channel set channel_type:Offers channel:#offers
   /channel set channel_type:Demands channel:#demands
   ```

3. Now:
   - `/offer` and `/release` can only be used in `#transactions` or `#offers`
   - `/demand` can only be used in `#demands`
   - `/trade` can only be used in `#trades` (if configured)

### Scenario 2: Multiple Channels Per Type

Allow transactions in multiple channels:

```
/channel set channel_type:Transactions channel:#transactions
/channel set channel_type:Transactions channel:#admin-zone
```

Now both `#transactions` and `#admin-zone` allow transaction commands.

### Scenario 3: No Restrictions

If you don't configure any channels for a command type, the command can be used in any channel:

```
/channel clear channel_type:Transactions
/channel clear channel_type:Offers
```

Now all transaction commands can be used anywhere.

## Implementation Details

### Database

Channels are stored in the `ChannelConfig` table with the following structure:

```
{
  guild_id: {
    "Transactions": [channel_id_1, channel_id_2],
    "Offers": [channel_id_3],
    "Demands": [channel_id_4],
    "Trades": [channel_id_5]
  }
}
```

### Channel Validation

When a command is executed:

1. System checks if the command type has any configured channels
2. If no channels configured → Command allowed everywhere
3. If channels configured → Command only allowed in those channels
4. User receives clear error message showing which channels are allowed

### Integration Points

The channel configuration system is integrated with:

- **`/offer`** - Uses `Offers` channel type
- **`/release`** - Uses `Transactions` channel type
- **`/demand`** - Uses `Demands` channel type
- **`/promote`** - Uses `Transactions` channel type
- **`/demote`** - Uses `Transactions` channel type
- **`/trade`** - Uses `Trades` channel type
- **`/trade-block`** - Uses `Trades` channel type

## Utility Functions (For Developers)

All functions are in `utils/signing_tools.py`:

### `set_channel_config(guild_id, channel_type, channel_id)`
Adds a channel to a command type.
- **Returns**: `(success: bool, message: str)`

### `remove_channel_config(guild_id, channel_type, channel_id)`
Removes a channel from a command type.
- **Returns**: `(success: bool, message: str)`

### `get_channel_config(guild_id, channel_type)`
Gets all channels for a command type.
- **Returns**: `list[int]` - List of channel IDs

### `get_all_channel_config(guild_id)`
Gets entire channel configuration for guild.
- **Returns**: `dict` - All channel configurations

### `check_channel_config(inter, channel_type)`
Validates if command is in allowed channel.
- **Returns**: `(is_allowed: bool, error_message: str)`

## Error Messages

| Scenario | Message |
|----------|---------|
| Command used in wrong channel | "You can only use this command in: #channel1, #channel2" |
| No channels configured for type | Command allowed everywhere |
| Invalid channel ID | "No valid channels configured for {type}" |

## Migration Guide

If you previously used the old hardcoded channel system:

1. The old system looked for channels with specific name patterns (SigningChannel, OfferingChannel, etc.)
2. The new system is completely separate and independent
3. **No old data is migrated** - you must reconfigure channels using the new system
4. The new system provides more flexibility and control

### Steps to Migrate

1. Identify which channels you want for each command type
2. Run `/channel set` commands to configure them
3. Test each command in the configured channels
4. Clear any old channel configuration from the old system if desired

## Performance

- Channel lookups: **O(1)** - Direct list membership check
- Maximum channels per type: Unlimited
- Maximum command types: Unlimited
- No performance impact from having many configured channels

## Troubleshooting

### Commands aren't restricted to channels

**Problem**: I configured channels but commands still work everywhere

**Solution**: Make sure you're using the command type names correctly. They are case-sensitive. Use `/channel list` to verify your configuration.

### Can't find my channel in the list

**Problem**: I created a channel but it doesn't appear in `/channel list`

**Solution**: Channels are listed by ID. Make sure you selected the right channel when running `/channel set`. The bot shows channel mentions (e.g., `#channel-name`) which match actual channels.

### Error: "Permission Denied"

**Problem**: Non-admin users can't configure channels

**Solution**: This is intentional. Only server administrators can change channel configurations. Have an admin run the `/channel` commands.

## Best Practices

1. **Organize by Purpose**: Use clear channel names that match command types (e.g., `#transactions` for "Transactions" type)
2. **Start Simple**: Begin with one channel per command type, then expand if needed
3. **Use Descriptions**: Add channel descriptions explaining what types of commands are allowed
4. **Test Configuration**: After setting channels, test by running commands to verify they're enforced
5. **Document Rules**: Post channel rules/purposes in each channel's topic or pinned message

## Advanced Usage

### Multiple Channel Types for Same Channel

You can assign the same channel to multiple command types:

```
/channel set channel_type:Transactions channel:#admin-zone
/channel set channel_type:Offers channel:#admin-zone
/channel set channel_type:Trades channel:#admin-zone
```

Now `#admin-zone` allows all three command types.

### Separate Channels by Category

Create specialized channels for different aspects:

```
/channel set channel_type:Offers channel:#offers-incoming
/channel set channel_type:Demands channel:#demands
/channel set channel_type:Trades channel:#trades-active
/channel set channel_type:Transactions channel:#general-transactions
```

### Event-Based Channels

Create temporary channels for events:

```
/channel set channel_type:Trades channel:#tournament-trades
```

Then clear after event:

```
/channel clear channel_type:Trades
```

## Summary

The new channel configuration system provides:
- **Flexibility**: Define your own command type categories
- **Control**: Precisely specify which channels allow which commands
- **Ease of Use**: Simple admin commands to manage everything
- **Scalability**: Works for any number of guilds and channels
- **Backward Compatibility**: If not configured, no restrictions apply
