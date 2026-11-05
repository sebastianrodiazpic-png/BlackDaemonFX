import sqlite3
import json
import pandas as pd
import numpy as np

db_path = r'C:/Users/sebas/AppData/Local/BlackDaemonFx/trading_bot.sqlite3'
conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)

query = """
SELECT id, instrument, direction, entry_time, exit_time, entry_price, stop_loss, take_profit, exit_price,
       planned_rr, realized_rr, risk_amount, net_pnl, exit_reason, details_json
FROM trades
WHERE status = 'CLOSED' AND setup_reason LIKE '%TREND_PULLBACK%'
ORDER BY id DESC
"""
df = pd.read_sql_query(query, conn)
print(f"Total TREND_PULLBACK trades: {len(df)}")
print(f"Wins: {len(df[df['net_pnl'] > 0])} | Losses: {len(df[df['net_pnl'] < 0])}")
print(f"Total PnL: {df['net_pnl'].sum():.2f}")

# Breakdown by instrument for TREND_PULLBACK
inst_summary = df.groupby('instrument').agg(
    total=('id', 'count'),
    wins=('net_pnl', lambda x: (x > 0).sum()),
    losses=('net_pnl', lambda x: (x < 0).sum()),
    win_rate=('net_pnl', lambda x: round(100.0 * (x > 0).sum() / len(x), 1)),
    pnl=('net_pnl', 'sum'),
    avg_r=('realized_rr', 'mean')
).sort_values(by='pnl')

print("\n=== RENDIMIENTO DE TREND_PULLBACK POR INSTRUMENTO ===")
print(inst_summary.to_string())

# Inspect MFE / MAE in details_json
mfe_vals = []
mae_vals = []
holding_hours = []

for idx, row in df.iterrows():
    d = json.loads(row['details_json']) if row['details_json'] else {}
    mfe = d.get('max_favorable_excursion_rr')
    mae = d.get('max_adverse_excursion_rr')
    if mfe is not None:
        mfe_vals.append(mfe)
    if mae is not None:
        mae_vals.append(mae)
    try:
        t_in = pd.to_datetime(row['entry_time'])
        t_out = pd.to_datetime(row['exit_time'])
        dur = (t_out - t_in).total_seconds() / 3600.0
        holding_hours.append(dur)
    except Exception:
        pass

print(f"\nMFE promedio de TREND_PULLBACK: {np.mean(mfe_vals):.3f}R" if mfe_vals else "No MFE data")
print(f"MAE promedio de TREND_PULLBACK: {np.mean(mae_vals):.3f}R" if mae_vals else "No MAE data")
print(f"Tiempo de tenencia promedio: {np.mean(holding_hours):.2f} horas" if holding_hours else "No holding data")

# Breakdown by direction
print("\n=== RENDIMIENTO POR DIRECCIÓN (BUY vs SELL) ===")
print(df.groupby('direction').agg(
    total=('id', 'count'),
    wins=('net_pnl', lambda x: (x > 0).sum()),
    losses=('net_pnl', lambda x: (x < 0).sum()),
    win_rate=('net_pnl', lambda x: round(100.0 * (x > 0).sum() / len(x), 1)),
    pnl=('net_pnl', 'sum')
).to_string())
