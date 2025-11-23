import re
import os
import sys

base_path = r"c:\Users\zacha\Downloads\League Bot\HSFL League Bot"
os.chdir(base_path)

def fix_bare_excepts(filepath):
    """Replace bare except: with except Exception:"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Find all bare except: patterns and replace them
    pattern = r'\n(\s*)except:\s*\n'
    replacement = r'\n\1except Exception:\n'
    
    new_content = re.sub(pattern, replacement, content)
    
    if new_content != content:
        with open(filepath, 'w') as f:
            f.write(new_content)
        return True
    return False

files_to_fix = [
    "cogs/league.py",
    "cogs/draft.py", 
    "cogs/sign.py",
    "cogs/trade.py",
    "cogs/export.py",
    "cogs/suspended.py",
    "cogs/role_manager.py",
    "cogs/embed2.py",
    "cogs/snipe.py"
]

for filepath in files_to_fix:
    if os.path.exists(filepath):
        if fix_bare_excepts(filepath):
            print(f"Fixed: {filepath}")
        else:
            print(f"No changes: {filepath}")
    else:
        print(f"Not found: {filepath}")
