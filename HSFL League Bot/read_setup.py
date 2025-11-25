with open('cogs/setup.py', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()
    print(f"Total lines: {len(lines)}")
    for i in range(200, min(350, len(lines))):
        print(f"{i+1}: {lines[i].rstrip()}")
