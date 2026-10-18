import pandas as pd
from pathlib import Path

csv_dir = Path("data")
files = list(csv_dir.rglob("*.csv"))

results = []
for f in files:
    try:
        df = pd.read_csv(f, nrows=5)
        time_col = None
        for col in ['time', 'datetime', 'Date', 'timestamp']:
            if col in df.columns:
                time_col = col
                break
        if not time_col:
            continue
            
        # Leer primera y ultima linea
        df_head = pd.read_csv(f, nrows=2)
        # Contar filas totales aprox
        with open(f, 'rb') as fp:
            line_count = sum(1 for _ in fp) - 1
            
        df_tail = pd.read_csv(f, skiprows=max(1, line_count - 2), header=None)
        start_time = df_head[time_col].iloc[0]
        # el header original
        end_time = df_tail.iloc[-1, df.columns.get_loc(time_col)]
        
        results.append({
            "file": f.name,
            "bars": line_count,
            "start": str(start_time),
            "end": str(end_time)
        })
    except Exception as e:
        pass

df_res = pd.DataFrame(results)
if not df_res.empty:
    df_res = df_res.sort_values(by="bars", ascending=False)
    print(df_res.head(30).to_string(index=False))
