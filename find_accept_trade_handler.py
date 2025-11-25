
with open("HSFL League Bot/cogs/trade.py") as f:
    content = f.read()

# Find accept_trade handler
if "accept_trade" in content:
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if "accept_trade" in line.lower() and "def" in line.lower():
            print(f"Found at line {i+1}")
            for j in range(max(0, i-5), min(len(lines), i+60)):
                print(f"{j+1:4d}: {lines[j]}")
            print("\n")
