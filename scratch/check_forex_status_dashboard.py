import json
import sqlite3

with open("dashboard/realtime_dashboard.py", "r", encoding="utf-8") as f:
    text = f.read()

# Let's search for FOREX_3 and FOREX_4 in python logic
for line in text.split("\n"):
    if ("FOREX_3" in line or "FOREX_4" in line) and ("DISABLED" in line or "STANDBY" in line or "status" in line or "PRUNED" in line):
        print(line.strip())
