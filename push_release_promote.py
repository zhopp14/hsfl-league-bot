#!/usr/bin/env python
import subprocess
import os
import sys

os.chdir(r'C:\Users\zacha\Downloads\League Bot')

print("Git Status:")
result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
print(result.stdout)

print("\nAdding changes...")
result = subprocess.run(['git', 'add', 'HSFL League Bot/cogs/sign.py'], capture_output=True, text=True)
print(result.stdout or "Added successfully")

print("\nCommitting changes...")
result = subprocess.run(['git', 'commit', '-m', 
'''Remove channel restriction from release and promote commands

- Remove channel_config check from transaction_checks() function
- Release and promote commands now work in any channel
- Transactions still logged to Transactions channel via send_to_channel_type()
- Fixes issue where commands were locked to specific channels'''],
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
    
# Get commit hash and diff stats
print("\nCommit details:")
result = subprocess.run(['git', 'log', '-1', '--format=%H'], capture_output=True, text=True)
commit_hash = result.stdout.strip()[:7]
print(f"Commit: {commit_hash}")

result = subprocess.run(['git', 'diff', 'HEAD~1', '--stat'], capture_output=True, text=True)
print(result.stdout)
