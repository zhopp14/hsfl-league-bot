
import subprocess
import sys
import os

os.chdir(".")

# Add files
print("Adding files...")
result = subprocess.run([
    "git", "add", 
    "HSFL League Bot/cogs/sign.py",
    "OFFERING_TIMEOUT_FIX.md"
], capture_output=True, text=True)

if result.returncode != 0:
    print(f"Error adding files: {result.stderr}")
    sys.exit(1)

print("Files added")

# Commit
print("Committing...")
result = subprocess.run([
    "git", "commit", "-m",
    """Fix offering system timeout issues by deferring interactions

- Add defer() calls to OfferButtons.accept_button
- Add defer() calls to OfferButtons.decline_button  
- Add defer() calls to AcceptDeclineView.accept_button
- Add defer() calls to AcceptDeclineView.decline_button

This ensures Discord interactions are acknowledged within the 3-second window, preventing 'This interaction failed' errors during offer acceptance/decline operations."""
], capture_output=True, text=True)

if result.returncode != 0:
    print(f"Error committing: {result.stderr}")
    sys.exit(1)

print(result.stdout)

# Push
print("Pushing...")
result = subprocess.run([
    "git", "push", "origin", "main"
], capture_output=True, text=True)

if result.returncode != 0:
    print(f"Error pushing: {result.stderr}")
    sys.exit(1)

print(result.stdout)
print("\nPush completed successfully!")
