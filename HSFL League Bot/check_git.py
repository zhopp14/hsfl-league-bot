import subprocess
import os

os.chdir(r'c:\Users\zacha\Downloads\League Bot\HSFL League Bot')

try:
    result = subprocess.run(['git', 'status', '--short'], capture_output=True, text=True, timeout=5)
    print("Exit code:", result.returncode)
    print("STDOUT:")
    print(result.stdout)
    print("STDERR:")
    print(result.stderr)
    
    print("\n--- Checking recent commits ---")
    result2 = subprocess.run(['git', 'log', '--oneline', '-5'], capture_output=True, text=True, timeout=5)
    print(result2.stdout)
    
except Exception as e:
    print(f"Error: {e}")
