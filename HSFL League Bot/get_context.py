with open('cogs/league.py') as f:
    lines = f.readlines()

# Line numbers where bare excepts are (converted to 0-based indexing)
bare_excepts = [255, 406, 623, 706, 1122, 1235, 1336]

for line_num in bare_excepts:
    start = max(0, line_num - 3)
    end = min(len(lines), line_num + 3)
    print(f"\n=== Context around line {line_num + 1} ===")
    for i in range(start, end):
        marker = ">>>" if i == line_num else "   "
        print(f"{marker} {i+1:4d}: {lines[i]}", end='')
