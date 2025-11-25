import subprocess
import os

os.chdir(r'c:\Users\zacha\Downloads\League Bot\HSFL League Bot')

result = subprocess.run(['git', 'status'], capture_output=True, text=True)

with open('git_test_result.txt', 'w') as f:
    f.write(f"Return code: {result.returncode}\n")
    f.write(f"STDOUT:\n{result.stdout}\n")
    f.write(f"STDERR:\n{result.stderr}\n")
