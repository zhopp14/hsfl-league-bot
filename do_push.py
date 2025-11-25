import subprocess
import sys

files = [
    "HSFL League Bot/utils/signing_tools.py",
    "HSFL League Bot/cogs/sign.py",
    "HSFL League Bot/cogs/teams.py",
    "HSFL League Bot/cogs/trade.py",
]

subprocess.run(["git", "add"] + files, check=False)
subprocess.run(["git", "commit", "-m", "Auto-detect team from user's team role membership in offer command"], check=False)
result = subprocess.run(["git", "push"], capture_output=True, text=True)
print(result.stdout)
print(result.stderr)
sys.exit(result.returncode)
