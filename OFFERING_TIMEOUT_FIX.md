# Offering System Timeout Fix

## Problem
The offering system was timing out with Discord's "This interaction failed" message when users accepted or declined offers. This occurred because button handlers were not deferring the interaction immediately.

## Root Cause
Discord allows bots 3 seconds to acknowledge an interaction. The offering system button handlers were performing extensive async operations (sign checks, role management, database updates, sending messages) **without first deferring** the interaction. If any of these operations took time, Discord would timeout the interaction.

## Solution
Added `await inter.response.defer()` calls at the **beginning** of all button handlers in `cogs/sign.py` to immediately acknowledge the interaction. This tells Discord "I'm processing this" within the 3-second window, allowing the bot to perform the actual work afterward.

## Changes Made

### 1. **OfferButtons.accept_button** (Line 368)
```python
async def accept_button(self, button: disnake.ui.Button, inter):
    await inter.response.defer()  # ADDED
    sign_checks_ = await sign_checks(self.inter, self.team, self.member)
    # ... rest of method
```

### 2. **OfferButtons.decline_button** (Line 415)
```python
async def decline_button(self, button: disnake.ui.Button, inter):
    await inter.response.defer()  # ADDED
    embed = Embed(
        title='Offer Declined',
    # ... rest of method
```

### 3. **AcceptDeclineView.accept_button** (Line 255)
```python
async def accept_button(self, button, inter):
    await inter.response.defer()  # ADDED
    try:
        await self.kwargs['accept_function'](inter, self.kwargs)
    # ... rest of method
```

### 4. **AcceptDeclineView.decline_button** (Line 277)
```python
async def decline_button(self, button, inter):
    await inter.response.defer(ephemeral=True)  # ADDED
    try:
        await self.kwargs['decline_function'](inter, self.kwargs)
    # ... rest of method
```

## How This Fixes the Issue
1. When a user clicks the button, the handler runs
2. **Immediately** (within 1ms), `defer()` is called to acknowledge the interaction to Discord
3. Discord no longer times out - it knows the bot is processing
4. The bot can now safely take time performing sign checks, role updates, database operations, etc.
5. All async operations complete and responses are sent as planned

## Testing
- Run the bot and test offer acceptance/decline flows
- Verify no "This interaction failed" messages appear
- Confirm all offer logic (role assignments, notifications, database updates) still works correctly

## Files Modified
- `HSFL League Bot/cogs/sign.py` - Added defer() calls to 4 button handlers
