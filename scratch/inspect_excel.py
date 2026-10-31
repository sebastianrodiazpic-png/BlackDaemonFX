import pandas as pd
import openpyxl

path = 'storage/exports/deriv_demo_trading_report.xlsx'
wb = openpyxl.load_workbook(path, read_only=True)
print("Sheets:", wb.sheetnames)

for sheet in wb.sheetnames[:3]:
    df = pd.read_excel(path, sheet_name=sheet, nrows=5)
    print(f"\n--- Sheet: {sheet} ---")
    print("Columns:", list(df.columns))
    print(df.head(2))

# Load trades sheet to see distributions
df_trades = pd.read_excel(path, sheet_name="Trades")
print("\nTotal trades in Excel:", len(df_trades))
if 'realized_rr' in df_trades.columns:
    print("realized_rr stats:\n", df_trades['realized_rr'].describe())
elif 'R:R Realizado' in df_trades.columns:
    print("R:R Realizado stats:\n", df_trades['R:R Realizado'].describe())
