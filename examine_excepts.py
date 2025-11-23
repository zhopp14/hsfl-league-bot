with open('HSFL League Bot/cogs/league.py') as f:
    lines = f.readlines()
    for ln in [107, 255, 406, 623, 706, 1122, 1235, 1336]:
        start = max(0, ln - 4)
        end = min(len(lines), ln + 3)
        print(f'\n==== Lines {start+1}-{end+1} ====')
        for i in range(start, end):
            marker = '>>>' if i == ln else '   '
            print(f'{marker} {i+1:4d}: {lines[i]}', end='')
