with open(r'c:\Users\zacha\Downloads\League Bot\HSFL League Bot\cogs\teams.py', 'r') as f:
    lines = f.readlines()
    for i in range(35, min(165, len(lines))):
        print(f'{i+1:3d}: {lines[i]}', end='')
