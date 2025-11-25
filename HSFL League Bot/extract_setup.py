import sys
content = open('cogs/setup.py', 'r', encoding='utf-8', errors='ignore').read()
lines = content.split('\n')
for i in range(200, len(lines)):
    sys.stdout.write(f"{i+1}: {lines[i]}\n")
    if i > 450:
        break
