import pandas as pd

try:
    df_60 = pd.read_csv('storage/analysis/replay_malaysian_snr_60_assets_2y_summary.csv')
    print("Columns in 60_assets_2y_summary:", df_60.columns.tolist())
    print(df_60.head(10))
except Exception as e:
    print("Error reading 60 summary:", e)

try:
    df_2y = pd.read_csv('storage/analysis/replay_malaysian_snr_2y_summary.csv')
    print("\nColumns in 2y_summary:", df_2y.columns.tolist())
    print(df_2y.head(10))
except Exception as e:
    print("Error reading 2y summary:", e)
