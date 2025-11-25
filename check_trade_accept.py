
with open("HSFL League Bot/cogs/trade.py") as f:
    lines = f.readlines()

# Find AcceptDeclineTrade class
for i in range(len(lines)):
    if "class AcceptDeclineTrade" in lines[i]:
        print(f"Found class at line {i+1}: {lines[i].rstrip()}")
        for j in range(i, min(len(lines), i+150)):
            print(f"{j+1:4d}: {lines[j].rstrip()}")
            if j > i and lines[j].strip().startswith("class "):
                break
        break
