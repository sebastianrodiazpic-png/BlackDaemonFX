import openpyxl
from pathlib import Path

path = Path("storage/exports/deriv_demo_trading_report.xlsx")
if path.exists():
    wb = openpyxl.load_workbook(path, read_only=True)
    print("Sheets:", wb.sheetnames)
    sheet = wb.active
    rows = list(sheet.iter_rows(values_only=True))
    header = rows[0] if rows else []
    print("Header:", header[:10])
    print(f"Total rows: {len(rows)}")
    if len(rows) > 1:
        print("\nLast 5 trades:")
        for r in rows[-5:]:
            print(" ", r[:10])
else:
    print("Excel file does not exist")
