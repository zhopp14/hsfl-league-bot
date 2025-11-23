# Transactions Channel Logging

## Overview

The **Transactions** channel is a special channel type that automatically logs all major transaction events in your league. When you configure one or more channels for the "Transactions" channel type, they will receive real-time logs of signings, releases, promotions, and demotions.

## What Gets Logged to Transactions Channel

### 1. **Signings** (When Player Accepts Offer)
When a player accepts an offer to join a team, the Transactions channel receives:
- Player name and mention
- Team they joined
- Coach who made the offer
- Roster capacity info
- Contract details (if applicable)

**Command**: `/offer` → Player accepts

---

### 2. **Releases** (When Player is Released)
When a player is released from a team, the Transactions channel receives:
- Player name and mention
- Team they left
- Coach who released them
- Current roster capacity after release

**Commands**: 
- `/release` (normal release)
- Contract release acceptance

---

### 3. **Promotions** (When Player Promoted to Coach)
When a player is promoted to a coaching position, the Transactions channel receives:
- Player name and mention
- New coaching role they received
- Coach who promoted them

**Command**: `/promote`

---

### 4. **Demotions** (When Coach is Demoted)
When a coaching staff member is demoted, the Transactions channel receives:
- Coach name and mention
- Role they lost
- Coach who demoted them

**Command**: `/demote`

---

### 5. **Demote & Release** (Combined Action)
When a coach is demoted and released simultaneously, the Transactions channel receives:
- Coach name and mention
- Role they lost
- Team they left
- Coach who performed the action

**Scenario**: Using `/release` on a coach who accepts the demotion

---

## Setup

### Step 1: Create a Transactions Channel

Create a new Discord channel (usually named something like `#transactions` or `#transaction-log`).

```
Channel Name: #transactions
Topic: "All signing events, releases, and promotions"
```

### Step 2: Configure the Channel

As a server administrator, run:

```
/channel set channel_type:Transactions channel:#transactions
```

### Step 3: Verify

Run `/channel list` to confirm:

```
/channel list
```

You should see:
```
Transactions: #transactions
```

---

## Usage Example

### League Setup
```
/channel set channel_type:Transactions channel:#transactions
/channel set channel_type:Offers channel:#offers
/channel set channel_type:Demands channel:#demands
```

### Daily Operations

**Coach signs a player**:
```
/offer member:@Player contract:2yr
→ Player accepts in their DM
→ #transactions channel logs: "Player accepted offer to Team A"
```

**Coach releases a player**:
```
/release member:@Player
→ #transactions channel logs: "Player released from Team A"
```

**Coach promotes a player**:
```
/promote member:@Player coach_role:@Assistant_Coach
→ #transactions channel logs: "Player promoted to Assistant Coach"
```

**Coach demotes staff**:
```
/demote member:@Assistant_Coach
→ #transactions channel logs: "Assistant Coach demoted"
```

---

## Multiple Transactions Channels

You can assign multiple channels to receive all transaction logs:

```
/channel set channel_type:Transactions channel:#transactions
/channel set channel_type:Transactions channel:#admin-log
/channel set channel_type:Transactions channel:#league-history
```

Now all three channels receive real-time transaction logs.

---

## Advanced Usage

### Separate Channels by Event Type

While "Transactions" logs everything, you can also configure:

```
/channel set channel_type:Offers channel:#offers-only
/channel set channel_type:Demands channel:#demands-only
```

**Result**: 
- #transactions: All signings, releases, promotions, demotions
- #offers-only: Only signing offers (when accepted)
- #demands-only: Only demand events

### Archive Channel

Create a read-only archive channel that only receives transaction logs:

```
/channel set channel_type:Transactions channel:#transaction-archive
```

Then make `#transaction-archive` read-only so users can view history but not post.

### Admin-Only Logging

Configure a private admin channel:

```
/channel set channel_type:Transactions channel:#admin-transactions
```

Only admins can see this channel, providing private transaction logs.

---

## Log Format

All transaction logs follow a consistent format:

```
Title: [Event Type] (e.g., "Offer Accepted", "Franchise Releasing", "Franchise Promotion")

Description includes:
- Player/Coach involved with @mention
- Player/Coach display name
- Team involved
- Executing coach with @mention
- Additional info (roster cap, contract details, roles, etc.)

Color coding:
- Green accent for team colors
```

---

## Troubleshooting

### Logs Aren't Appearing

**Problem**: I configured the channel but logs aren't showing

**Solution**: 
1. Verify the channel is configured: `/channel list`
2. Check bot has permission to post in the channel
3. Try executing a command (e.g., `/offer`) to trigger a log entry

### Wrong Events Logging

**Problem**: I'm seeing events I didn't configure

**Solution**:
- Check your channel configuration with `/channel list`
- "Transactions" logs ALL transaction events
- To log only specific events, configure separate channel types

### Channel Not Found

**Problem**: Bot says "Channel not found" when sending logs

**Solution**:
1. Delete the old configuration: `/channel clear Transactions`
2. Recreate the channel if it was deleted
3. Reconfigure: `/channel set channel_type:Transactions channel:#transactions`

---

## Permissions

### Who Can Configure
- **Server Administrators only**
- Use `/channel set` to configure channels

### Who Can View
- **Anyone with access to the channel**
- Configure channel visibility based on your league rules

### Who Gets Logged
- **All transactions** regardless of who executes them
- Both player actions (accepting offers) and coach actions (releasing, promoting)

---

## Examples

### Complete League Setup
```
# Main transaction channels
/channel set channel_type:Transactions channel:#transactions

# Specific event channels
/channel set channel_type:Offers channel:#offers
/channel set channel_type:Demands channel:#demands
/channel set channel_type:Trades channel:#trades

# Admin logging
/channel set channel_type:Transactions channel:#admin-log
```

### Team-Specific Logging
You could create channels per team and manually configure them:
```
/channel set channel_type:Transactions channel:#team-a-log
/channel set channel_type:Transactions channel:#team-b-log
```

(Note: This sends logs to both channels, not filtered by team - if you need per-team logging, that would be a future feature)

---

## Performance

- **Real-time**: Logs appear instantly when events occur
- **No delay**: Transaction logging has no performance impact
- **Unlimited channels**: Can log to as many channels as needed
- **Reliable**: Uses same system as notification channels

---

## Summary

The **Transactions** channel type provides:
- ✅ **Real-time logging** of all transaction events
- ✅ **Multiple channel support** (log to many channels at once)
- ✅ **Clean embeds** with consistent formatting
- ✅ **No performance impact** on commands
- ✅ **Easy setup** with `/channel set` command
- ✅ **Comprehensive** (signings, releases, promotions, demotions)

**Quick Start**: `/channel set channel_type:Transactions channel:#transactions`
