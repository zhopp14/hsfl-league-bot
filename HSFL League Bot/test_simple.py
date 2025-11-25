import os

cwd = os.getcwd()

with open('simple_test.txt', 'w') as f:
    f.write(f"Current directory: {cwd}\n")
    f.write("Script executed successfully\n")
