import ast
import sys

files_to_check = [
    'utils/signing_tools.py',
    'cogs/teams.py',
    'cogs/sign.py',
    'cogs/trade.py'
]

all_ok = True
for filepath in files_to_check:
    try:
        with open(filepath, 'r') as f:
            ast.parse(f.read())
        print(f"✓ {filepath}: OK")
    except SyntaxError as e:
        print(f"✗ {filepath}: SYNTAX ERROR at line {e.lineno}: {e.msg}")
        all_ok = False
    except Exception as e:
        print(f"✗ {filepath}: ERROR - {e}")
        all_ok = False

if all_ok:
    print("\n✓ All files are valid!")
    sys.exit(0)
else:
    print("\n✗ Some files have errors")
    sys.exit(1)
