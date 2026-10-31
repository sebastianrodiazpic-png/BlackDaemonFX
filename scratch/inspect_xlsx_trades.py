import openpyxl
from pathlib import Path

wb = openpyxl.load_workbook("storage/exports/deriv_demo_trading_report.xlsx", read_only=True)
sheet = wb["Trades"]
rows = list(sheet.iter_rows(values_only=True))
header = rows[0]
print(f"Total trades: {len(rows)-1}")
print("Header:", header)

print("\nLast 10 trades:")
for r in rows[-10:]:
    d = dict(zip(header, r))
    print(f"ID={d.get('id')} | {d.get('instrument')} | {d.get('direction')} | Status={d.get('status')} | Result={d.get('result')} | Entry={d.get('entry_time')} | Exit={d.get('exit_time')} | NetR={d.get('net_r')}")
