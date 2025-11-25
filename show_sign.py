
with open("HSFL League Bot/cogs/sign.py") as f:
    lines = f.readlines()
    
for i, line in enumerate(lines, 1):
    print(f"{i:4d}: {line.rstrip()}")
