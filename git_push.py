import subprocess
import os

os.chdir('c:\\Users\\zacha\\Downloads\\League Bot')

# Check status
print("=== Git Status ===")
result = subprocess.run(['git', 'status', '--short'], capture_output=True, text=True)
print(result.stdout if result.stdout else "No changes")
print(result.stderr if result.stderr else "")

# Add files
print("\n=== Adding files ===")
result = subprocess.run(['git', 'add', 'HSFL League Bot/cogs/sign.py'], capture_output=True, text=True)
print(result.stdout if result.stdout else "Done")
print(result.stderr if result.stderr else "")

# Commit
print("\n=== Committing ===")
result = subprocess.run(['git', 'commit', '-m', 'Remove channel restriction from release and promote commands'], capture_output=True, text=True)
print(result.stdout)
print(result.stderr if result.stderr else "")

# Push
print("\n=== Pushing ===")
result = subprocess.run(['git', 'push'], capture_output=True, text=True)
print(result.stdout)
print(result.stderr if result.stderr else "")

# Check log
print("\n=== Latest commits ===")
result = subprocess.run(['git', 'log', '--oneline', '-2'], capture_output=True, text=True)
print(result.stdout)
print(result.stderr if result.stderr else "")
