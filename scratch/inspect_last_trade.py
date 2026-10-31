import openpyxl

wb = openpyxl.load_workbook("storage/exports/deriv_demo_trading_report.xlsx", read_only=True)
sheet = wb["Trades"]
rows = list(sheet.iter_rows(values_only=True))
header = rows[0]
r = rows[-1]
d = dict(zip(header, r))
for k, v in d.items():
    if v is not None:
        print(f"{k}: {v}")
