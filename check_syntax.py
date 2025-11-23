import ast

files = [
    "HSFL League Bot/main.py",
    "HSFL League Bot/cogs/league.py",
    "HSFL League Bot/cogs/draft.py",
    "HSFL League Bot/cogs/sign.py",
    "HSFL League Bot/cogs/export.py",
    "HSFL League Bot/cogs/role_manager.py",
    "HSFL League Bot/cogs/embed2.py",
    "HSFL League Bot/cogs/snipe.py",
]

for f in files:
    try:
        with open(f) as file:
            ast.parse(file.read())
        print(f"OK: {f}")
    except SyntaxError as e:
        print(f"ERROR: {f} - {e}")
