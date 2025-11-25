import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('HSFL League Bot/utils/signing_tools.py', 'r', encoding='utf-8') as f:
    content = f.read()
    for i, line in enumerate(content.split('\n'), 1):
        print(f"{i:4d}: {line}")
