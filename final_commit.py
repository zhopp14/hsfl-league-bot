#!/usr/bin/env python3
import subprocess
import os
import sys

os.chdir('c:\\Users\\zacha\\Downloads\\League Bot')

try:
    # Stage the file
    subprocess.run(['git', 'add', 'HSFL League Bot/cogs/sign.py'], check=True)
    
    # Commit
    result = subprocess.run(['git', 'commit', '-m', 'Remove channel restriction from release and promote commands'], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        print("Commit successful:")
        print(result.stdout)
    else:
        print("Commit output:")
        print(result.stdout)
        print(result.stderr)
    
    # Push
    result = subprocess.run(['git', 'push', 'origin', 'main'], 
                          capture_output=True, text=True)
    
    print("\nPush result:")
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    print("Return code:", result.returncode)
    
    if result.returncode == 0:
        print("\n✓ Successfully pushed to GitHub!")
    else:
        print("\n✗ Push may have failed")
        
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
