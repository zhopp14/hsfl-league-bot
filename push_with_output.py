#!/usr/bin/env python3
import subprocess
import os

os.chdir('c:\\Users\\zacha\\Downloads\\League Bot')

print("=" * 50)
print("PUSHING TO GITHUB")
print("=" * 50)

# Check for changes
print("\n1. Checking for changes...")
result = subprocess.run(['git', 'status', '--short'], capture_output=True, text=True)
if result.stdout.strip():
    print("Changes found:")
    print(result.stdout)
else:
    print("No changes to commit")

# Stage files
print("\n2. Staging files...")
result = subprocess.run(['git', 'add', '-A'], capture_output=True, text=True)
print("Staged files")

# Commit
print("\n3. Committing changes...")
result = subprocess.run(['git', 'commit', '-m', 'Remove channel restriction from release and promote commands'], 
                       capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)

# Get commit info
print("\n4. Getting commit info...")
result = subprocess.run(['git', 'log', '-1', '--format=%H'], capture_output=True, text=True)
commit_hash = result.stdout.strip()[:7]
print(f"Commit: {commit_hash}")

# Get stats
result = subprocess.run(['git', 'diff', 'HEAD~1', '--stat'], capture_output=True, text=True)
print(result.stdout)

# Push
print("\n5. Pushing to GitHub...")
result = subprocess.run(['git', 'push', 'origin', 'main'], capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print(result.stderr)

if result.returncode == 0:
    print("\n✓ Successfully pushed to GitHub!")
    print(f"Commit: {commit_hash}")
else:
    print(f"\n✗ Push failed with return code: {result.returncode}")

print("=" * 50)
