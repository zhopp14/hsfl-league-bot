# Team Management & Auto-Detection System

## Overview

The new Team Management System streamlines transaction workflows by automatically detecting team assignments for coaches and staff members. This eliminates the need to manually specify a team parameter for most transaction commands.

## New Database Table

### CoachTeamMapping
**Location**: Database storage system
**Structure**: `{ guild_id: { coach_id: team_id, ... } }`
**Purpose**: Stores the relationship between coaches/owners and their assigned teams

## New Commands

### `/team set_owner`
**Description**: Assign a coach/owner to a team for auto-detection
**Parameters**:
- `coach` (Member, required): The coach or staff member to assign
- `team` (Role, required): The team to assign them to

**Behavior**:
- Admin-only command
- Validates that the team exists in TeamRole database
- Prevents duplicate assignments (shows error if coach already assigned to same team)
- Stores assignment for auto-detection in transaction commands
- Provides confirmation with auto-detection enabled notice

**Example**:
```
/team set_owner coach:@Coach_Name team:@Team_Name
```

### `/team remove_owner`
**Description**: Remove a coach/owner from team assignment
**Parameters**:
- `coach` (Member, required): The coach to remove from assignment

**Behavior**:
- Admin-only command
- Verifies coach is assigned to a team before removing
- Clears auto-detection for that coach
- Provides confirmation with previous team mention

**Example**:
```
/team remove_owner coach:@Coach_Name
```

### `/team info`
**Description**: Display detailed team information including coaches and roster
**Parameters**:
- `team` (Role, required): The team to get information about

**Returns**:
- Team role color
- List of assigned coaches/owners
- Current roster with member count
- Truncated member list (first 25, with count of remaining)

**Example**:
```
/team info team:@Team_Name
```

### `/team list`
**Description**: Display all teams with their coaching assignments
**Parameters**: None

**Returns**:
- Total team count
- For each team:
  - Team name
  - Assigned coaches (or "None assigned")
  - Roster size

**Example**:
```
/team list
```

### `/team check_assignment`
**Description**: Check which team a coach is assigned to
**Parameters**:
- `coach` (Member, optional): The coach to check (defaults to yourself)

**Behavior**:
- Users can check their own assignment without admin
- Admins can check any coach's assignment
- Shows "Not assigned" if coach has no team assignment
- Shows assigned team mention if assignment exists

**Example**:
```
/team check_assignment
/team check_assignment coach:@Coach_Name
```

## Updated Transaction Commands

### `/offer` (Player Signing Offer)
**Changes**:
- `team` parameter is now **optional**
- If team is omitted, auto-detects from coach's assignment
- Falls back to manual entry error if no assignment exists

**Command Flow**:
1. Coach runs `/offer member:@Player`
2. System checks coach's assigned team
3. If found: Uses assigned team automatically
4. If not found: Shows error directing to `/team set_owner`

**Example**:
```
# With assignment
/offer member:@Player_Name

# Without assignment (still works)
/offer member:@Player_Name team:@Team_Name
```

### `/release` (Player Release)
**Changes**:
- `team` parameter is now **optional**
- Automatically detects team from coach's assignment
- Fallback to manual entry if no assignment

**Command Flow**:
1. Coach runs `/release member:@Player_Name`
2. System checks coach's assigned team
3. Uses assigned team or shows error

### `/demand` (Demand Release)
**Changes**:
- `team` parameter is now **optional**
- Auto-detects team from player's team membership
- Determines which team player is on and auto-fills

**Command Flow**:
1. Player runs `/demand`
2. System finds player's team from team roles
3. Automatically processes demand from that team

### `/trade-block` (Add to Trade Block)
**Changes**:
- `team` parameter is now **optional**
- Auto-detects team from coach's assignment
- Coach no longer needs to specify team

**Command Flow**:
1. Coach runs `/trade-block player:@Player_Name`
2. System finds coach's assigned team
3. Adds player to trade block for that team

### `/trade` (Propose Trade)
**Changes**:
- `your_team` parameter now auto-detects from coach's assignment
- Falls back to manual entry if no assignment

**Command Flow**:
1. Coach runs `/trade team:@Other_Team`
2. System auto-detects coach's own team
3. Builds trade interface with both teams

## Auto-Detection Logic

### Coach/Owner Detection
For `/offer`, `/release`, `/trade-block`, `/trade`:
1. Coach runs command
2. System checks `CoachTeamMapping[guild_id][coach_id]`
3. If entry exists: Uses that team role ID
4. If not found: Returns error with `/team set_owner` instruction

### Team Detection for Players
For `/demand`:
1. Player runs command (no team parameter required)
2. System iterates through all team roles in guild
3. Finds which team the player has a role in
4. Auto-fills that team for the demand

## Validation & Safety

### Team Ownership Validation
- Only validates that coach is assigned to the team
- Does not re-check team membership (existing validation still applies)
- Allows coaches to manage their team even if they don't have the role

### Duplicate Prevention
- `/team set_owner` prevents assigning same coach to same team twice
- Shows "Already assigned" error
- Allows re-assigning coach to a different team (overwrites previous)

### Data Integrity
- CoachTeamMapping uses string keys for coach IDs
- CoachTeamMapping stores team IDs as strings
- All role/member lookups convert to int before fetching

## Database Operations

### Fetching Coach's Team
```python
coach_mapping = await Database.get_data('CoachTeamMapping', guild_id)
team_id = coach_mapping.get(str(coach_id))
team = guild.get_role(int(team_id))
```

### Setting Coach's Team
```python
coach_mapping = await Database.get_data('CoachTeamMapping', guild_id)
coach_mapping[str(coach_id)] = str(team.id)
await Database.add_data('CoachTeamMapping', {guild_id: coach_mapping})
```

### Getting All Coaches for a Team
```python
coach_mapping = await Database.get_data('CoachTeamMapping', guild_id)
team_coaches = [
    await guild.fetch_member(int(cid)) 
    for cid, tid in coach_mapping.items() 
    if str(tid) == str(team.id)
]
```

## Error Messages

### Team Not Set
**When**: Coach tries to use optional team command without assignment
**Message**: "Team Required: You must specify a team or have an assigned team in `/team set_owner`"
**Resolution**: Run `/team set_owner coach:@You team:@YourTeam`

### Invalid Team
**When**: Admin tries to assign coach to role not in TeamRole database
**Message**: "Invalid Team: `{role.name}` is not a valid team"
**Resolution**: Ensure the role is added to team setup via `/setup`

### Already Assigned
**When**: Admin tries to assign coach to team they're already assigned to
**Message**: "Already Assigned: {mention} is already assigned to {team.mention}"
**Resolution**: Use `/team remove_owner` first, or assign to different team

### Not Assigned
**When**: Checking coach assignment who has none, or removing coach with no assignment
**Message**: "Not Assigned: {mention} is not assigned to any team"
**Resolution**: Use `/team set_owner` to assign the coach

## Migration Guide

### From Manual Team Entry to Auto-Detection

**Before** (manual every time):
```
/offer member:@Player team:@My_Team
/release member:@Player team:@My_Team
/trade-block player:@Player team:@My_Team
```

**After** (one-time setup):
```
/team set_owner coach:@You team:@My_Team

/offer member:@Player
/release member:@Player
/trade-block player:@Player
```

### Setup Steps
1. Admin runs: `/team set_owner coach:@Coach_Name team:@Team_Name`
2. Repeat for all coaches/owners
3. Coaches can verify with: `/team check_assignment`
4. Coaches can now use streamlined commands

## Troubleshooting

### Auto-Detection Not Working
**Symptom**: Command still requires team parameter
**Cause**: Coach not assigned via `/team set_owner`
**Fix**: Admin runs `/team set_owner coach:@Coach_Name team:@Team_Name`

### Team Shows as Invalid
**Symptom**: "Invalid Team" error when setting owner
**Cause**: Team role not in TeamRole database
**Fix**: Add team role via `/setup TeamRole` or ensure role name matches detection keywords

### Coach Assignment Not Showing Up
**Symptom**: `/team check_assignment` shows "Not assigned"
**Cause**: Database entry not created
**Fix**: Re-run `/team set_owner` for that coach

### Multiple Teams Issue
**Symptom**: Command uses wrong team
**Cause**: Coach assigned to one team but has roles for multiple
**Fix**: Verify coach assignment with `/team check_assignment`, update if needed

## Permissions & Authorization

- **Admin Only**: `/team set_owner`, `/team remove_owner`, `/team list`
- **Self or Admin**: `/team check_assignment`
- **Anyone**: `/team info` (read-only)
- **Transaction Commands**: Original coach/player checks still apply

## Performance Considerations

- Coach team lookups: O(1) dictionary access
- Team roster display: Cached via guild.chunk() if needed
- No database scans required for standard operations
- All lookups use indexed guild role/member caches

## Future Enhancements

- Bulk assign coaches to teams (CSV upload)
- Inherit team assignment from Discord role hierarchy
- Automatic coach detection based on role prefix
- Team statistics dashboard showing coaches per team
- Audit log of coach assignments and changes
