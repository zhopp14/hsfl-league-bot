try:
    import main
    print("main.py: OK")
except SyntaxError as e:
    print(f"main.py: SYNTAX ERROR - {e}")
except Exception as e:
    print(f"main.py: IMPORT ERROR - {e}")

try:
    from cogs import league
    print("cogs/league.py: OK")
except SyntaxError as e:
    print(f"league.py: SYNTAX ERROR - {e}")
except Exception as e:
    print(f"league.py: IMPORT ERROR (expected, missing dependencies)")
