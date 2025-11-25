
with open("HSFL League Bot/cogs/sign.py") as f:
    lines = f.readlines()

looking = False
start_line = 0

for i, line in enumerate(lines, 1):
    if "async def accept_button" in line:
        looking = True
        start_line = i
    if looking:
        print(f"{i:4d}: {line.rstrip()}")
        if i > start_line and line.strip() and not line.startswith(" ") and not line.startswith("\t"):
            break
        if i - start_line > 150:
            break
