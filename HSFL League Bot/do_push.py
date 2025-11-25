import subprocess
import os

os.chdir(r'c:\Users\zacha\Downloads\League Bot\HSFL League Bot')

output = []

try:
    output.append("=" * 50)
    output.append("Git Add...")
    result = subprocess.run(['git', 'add', '-A'], capture_output=True, text=True, timeout=10)
    output.append(f"Add result: {result.returncode}")
    if result.stderr:
        output.append(f"Error: {result.stderr}")
    
    output.append("\n" + "=" * 50)
    output.append("Git Commit...")
    result = subprocess.run(['git', 'commit', '-m', 'Remove set_owner and remove_owner commands'], capture_output=True, text=True, timeout=10)
    output.append(f"Commit result: {result.returncode}")
    output.append(f"Output: {result.stdout}")
    if result.stderr:
        output.append(f"Error: {result.stderr}")
    
    output.append("\n" + "=" * 50)
    output.append("Git Push...")
    result = subprocess.run(['git', 'push'], capture_output=True, text=True, timeout=30)
    output.append(f"Push result: {result.returncode}")
    output.append(f"Output: {result.stdout}")
    if result.stderr:
        output.append(f"Error: {result.stderr}")
    
    output.append("\n" + "=" * 50)
    output.append("Latest commits:")
    result = subprocess.run(['git', 'log', '--oneline', '-3'], capture_output=True, text=True, timeout=10)
    output.append(result.stdout)
    
except Exception as e:
    output.append(f"Exception: {e}")

with open('push_result.txt', 'w') as f:
    f.write('\n'.join(output))
    
print('\n'.join(output))
