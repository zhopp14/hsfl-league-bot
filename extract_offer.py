import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('HSFL League Bot/cogs/sign.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

lines = content.split('\n')
for i, line in enumerate(lines[435:500], 436):
    print(f"{i:4d}: {line}")
