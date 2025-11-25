
with open('cogs/sign.py') as f:
    lines = f.readlines()
    print(f"Total lines: {len(lines)}")
    
    for i, line in enumerate(lines[:200], 1):
        print(f"{i:3d}: {line.rstrip()}")
