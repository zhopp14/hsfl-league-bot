import subprocess
import sys

def run_cmd(cmd, desc):
    print(f"\n{'='*50}")
    print(f"{desc}")
    print(f"{'='*50}")
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    print(f"Return code: {result.returncode}")
    return result

# Change to repo directory
import os
os.chdir(r'c:\Users\zacha\Downloads\League Bot')

try:
    # Status
    run_cmd('git status --short', '1. GIT STATUS')
    
    # Add
    run_cmd('git add "HSFL League Bot/cogs/sign.py"', '2. GIT ADD')
    
    # Commit
    result = run_cmd('git commit -m "Remove channel restriction from release and promote commands"', '3. GIT COMMIT')
    
    # Log
    run_cmd('git log --oneline -1', '4. LATEST COMMIT')
    
    # Push
    result = run_cmd('git push origin main', '5. GIT PUSH')
    
    if result.returncode == 0:
        print("\n" + "="*50)
        print("✓ SUCCESSFULLY PUSHED TO GITHUB!")
        print("="*50)
    else:
        print("\n" + "="*50)
        print("✗ PUSH FAILED")
        print("="*50)
        
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
