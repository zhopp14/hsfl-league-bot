#!/usr/bin/env python
import subprocess
import os

os.chdir(r'C:\Users\zacha\Downloads\League Bot\HSFL League Bot')

print("Git Status:")
result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
print(result.stdout)

print("\nAdding changes...")
result = subprocess.run(['git', 'add', 'utils/signing_tools.py'], capture_output=True, text=True)
print(result.stdout or "Added successfully")

print("\nCommitting changes...")
result = subprocess.run(['git', 'commit', '-m', 
'''Fix channel configuration type mismatch bug

- Convert channel IDs to strings when storing in database for consistency
- Convert channel IDs back to integers when retrieving from database
- Fix set_channel_config() to properly detect duplicate channels
- Fix remove_channel_config() to properly remove channels
- Fix get_channel_config() to return integers instead of strings
- Fix get_all_channel_config() to return integers for all channel IDs

This fixes the issue where /channel set command was not working because
integer channel IDs were not matching string IDs stored in the database.'''],
capture_output=True, text=True)
print(result.stdout)
if result.returncode != 0:
    print("Error:", result.stderr)

print("\nPushing to GitHub...")
result = subprocess.run(['git', 'push'], capture_output=True, text=True)
print(result.stdout)
if result.returncode != 0:
    print("Error:", result.stderr)
else:
    print("Successfully pushed to GitHub!")
