import py_compile
import os
import sys

files_to_check = [
    'main.py',
    'cogs/league.py',
    'cogs/draft.py',
    'cogs/sign.py',
    'cogs/export.py',
    'cogs/role_manager.py',
    'cogs/embed2.py',
    'cogs/snipe.py',
]

os.chdir(os.path.dirname(os.path.abspath(__file__)))

errors = []
for filepath in files_to_check:
    try:
        py_compile.compile(filepath, doraise=True)
        print(f"✓ {filepath}")
    except py_compile.PyCompileError as e:
        print(f"✗ {filepath}: {e}")
        errors.append((filepath, str(e)))

if errors:
    print(f"\n{len(errors)} file(s) with syntax errors")
    sys.exit(1)
else:
    print(f"\nAll {len(files_to_check)} files verified successfully!")
    sys.exit(0)
