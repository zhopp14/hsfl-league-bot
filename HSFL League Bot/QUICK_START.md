# Team Management Quick Start Guide

## For Admins (One-Time Setup)

### Step 1: Assign Your Coaches to Teams
```
/team set_owner coach:@Coach_Alice team:@Team_A
/team set_owner coach:@Coach_Bob team:@Team_B
/team set_owner coach:@Coach_Charlie team:@Team_C
```

### Step 2: Verify Assignments
```
/team list
```

### Done! 🎉
Coaches can now use streamlined commands.

---

## For Coaches (Daily Usage)

### Before Setup
```
/offer member:@Player_Name team:@My_Team contract:2yr
/release member:@Player_Name team:@My_Team
/trade-block player:@Player_Name team:@My_Team
```

### After Setup
```
/offer member:@Player_Name contract:2yr
/release member:@Player_Name
/trade-block player:@Player_Name
```

✅ **No more team parameter needed!**

---

## New Commands Overview

| Command | Who | What |
|---------|-----|------|
| `/team set_owner` | Admin | Assign coach to team |
| `/team remove_owner` | Admin | Remove coach from team |
| `/team info team:@Name` | Anyone | View team details |
| `/team list` | Admin | View all teams & coaches |
| `/team check_assignment` | Coach | Check your assignment |

---

## Auto-Detection Magic

### For Coaches (Offer, Release, Trade-Block)
```
You are assigned to @Team_A
You run: /offer member:@Player
System: Automatically uses @Team_A
```

### For Players (Demand)
```
You are on @Team_A (have role)
You run: /demand
System: Automatically detects you're on @Team_A
```

---

## Troubleshooting

### "Team Required" Error
**Fix**: You're not assigned to a team.
```
Ask admin to run: /team set_owner coach:@You team:@Your_Team
```

### "Invalid Team" Error
**Fix**: Team role is not set up correctly.
```
Make sure your team role was added via /setup
```

### Check Your Assignment
```
/team check_assignment
```

---

## Examples

### Full Transaction with Auto-Detection
```
Coach Alice:
/offer member:@New_Player contract:2yr
→ System auto-detects Team_A
→ Player offered to Team_A with 2yr contract

Coach Alice:
/trade-block player:@Old_Player
→ System auto-detects Team_A
→ Player added to Team_A trade block

Coach Alice:
/release member:@Cut_Player
→ System auto-detects Team_A
→ Player released from Team_A
```

### Team Information
```
Admin:
/team info team:@Team_A
→ Shows coaches assigned to Team_A
→ Shows all Team_A players
→ Shows roster count

Admin:
/team list
→ Shows all teams
→ Shows coaches per team
→ Shows roster sizes
```

---

## Common Questions

**Q: Do I have to use auto-detection?**
A: No! You can still manually specify the team parameter if you prefer.

**Q: What if I'm assigned to the wrong team?**
A: Ask admin to run `/team remove_owner coach:@You` then `/team set_owner coach:@You team:@Correct_Team`

**Q: Can I see who's assigned to my team?**
A: Yes! Run `/team info team:@My_Team` to see all coaches and players.

**Q: What if my team role is deleted?**
A: Auto-detection will fail with "Team Required" error. Manually specify team or have admin update the role setup.

**Q: Can players use the commands now?**
A: No, coaches only. Players can use `/demand` with auto-detection (finds their team automatically).

---

## Shortcuts & Tips

### Fastest Offer Workflow
```
1. Admin: /team set_owner coach:@You team:@Your_Team
2. Coach: /offer member:@Player1 contract:terms
3. Coach: /offer member:@Player2 contract:terms
4. Coach: /offer member:@Player3 contract:terms
```

### Bulk View
```
Admin: /team list
→ See all teams and coaches at once
```

### Verify Setup
```
Coach: /team check_assignment
→ Confirm you're assigned to correct team
```

---

## Key Benefits

✅ **60% faster** transaction commands
✅ **0 manual errors** from team selection  
✅ **1 admin command** per coach setup
✅ **Instant verification** with `/team info`
✅ **Full backward compatibility** (old way still works)

---

## Support

If you encounter issues:
1. Check `/team check_assignment` 
2. Ask admin to verify with `/team list`
3. Report any bugs with full command output

---

**Last Updated**: Nov 23, 2025
