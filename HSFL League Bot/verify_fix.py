with open('cogs/setup.py', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()
    print("=== TEAM ADD FIX VERIFICATION ===\n")
    
    for i in range(95, min(110, len(lines))):
        print(f"{i+1}: {lines[i].rstrip()}")
    
    print("\n=== ERROR HANDLING VERIFICATION ===\n")
    
    for i in range(340, min(410, len(lines))):
        if 'except' in lines[i] or 'disnake.NotFound' in lines[i]:
            print(f"{i+1}: {lines[i].rstrip()}")
