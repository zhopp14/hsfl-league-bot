import subprocess
import os

os.chdir(r'c:\Users\zacha\Downloads\League Bot')

with open('push_result.txt', 'w') as f:
    f.write("GITHUB PUSH LOG\n")
    f.write("="*50 + "\n\n")
    
    # Add
    f.write("1. Adding files...\n")
    r = subprocess.run(['git', 'add', 'HSFL League Bot/cogs/sign.py'], capture_output=True, text=True)
    f.write(f"Output: {r.stdout}\n")
    
    # Commit
    f.write("\n2. Committing changes...\n")
    r = subprocess.run(['git', 'commit', '-m', 'Remove channel restriction from release and promote commands'], capture_output=True, text=True)
    f.write(f"Output: {r.stdout}\n")
    f.write(f"Stderr: {r.stderr}\n")
    
    # Get last commit
    f.write("\n3. Latest commit:\n")
    r = subprocess.run(['git', 'log', '--oneline', '-1'], capture_output=True, text=True)
    f.write(f"{r.stdout}\n")
    
    # Push
    f.write("\n4. Pushing to GitHub...\n")
    r = subprocess.run(['git', 'push', 'origin', 'main'], capture_output=True, text=True)
    f.write(f"Output: {r.stdout}\n")
    f.write(f"Stderr: {r.stderr}\n")
    f.write(f"Return code: {r.returncode}\n")
    
    if r.returncode == 0:
        f.write("\n✓ PUSH SUCCESSFUL!\n")
    else:
        f.write("\n✗ PUSH FAILED\n")

print("Log written to push_result.txt")
