import pandas as pd
import json

file_path = "storage/exports/deriv_demo_trading_report.xlsx"
df = pd.read_excel(file_path, sheet_name="Open Positions")
step_df = df[df['instrument'].astype(str).str.contains("Step", case=False, na=False)]

print("--- OPEN POSITIONS STEP INDEX ---")
for idx, row in step_df.iterrows():
    print(f"\n--- POSICIÓN {idx} ---")
    d = row.to_dict()
    for k, v in d.items():
        if pd.notna(v):
            print(f"  {k}: {v}")
