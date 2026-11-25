import sqlite3
import pandas as pd
import numpy as np
import json

db_path = "file:storage/live_trading_bot.sqlite3?mode=ro"
conn = sqlite3.connect(db_path, uri=True)

df = pd.read_sql_query("SELECT * FROM trades", conn)

print("="*80)
print("1. RESUMEN GLOBAL DE EJECUCIÓN EN VIVO")
print("="*80)
print(f"Total trades registrados: {len(df)}")
if 'status' in df.columns:
    print("Status:", df['status'].value_counts().to_dict())
if 'result' in df.columns:
    print("Result:", df['result'].value_counts().to_dict())

closed = df[df['status'].isin(['CLOSED', 'closed']) | df['exit_time'].notnull()].copy()
print(f"Trades cerrados analizados: {len(closed)}")

if len(closed) > 0:
    closed['entry_time'] = pd.to_datetime(closed['entry_time'])
    closed['exit_time'] = pd.to_datetime(closed['exit_time'])
    
    total_net = closed['net_pnl'].sum()
    total_comm = closed['commission'].sum() if 'commission' in closed.columns else 0
    total_swap = closed['swap'].sum() if 'swap' in closed.columns else 0
    wins = closed[closed['net_pnl'] > 0]
    losses = closed[closed['net_pnl'] < 0]
    evens = closed[closed['net_pnl'] == 0]
    
    wr = len(wins) / len(closed) * 100 if len(closed) else 0
    gross_win = wins['net_pnl'].sum()
    gross_loss = abs(losses['net_pnl'].sum())
    pf = (gross_win / gross_loss) if gross_loss > 0 else np.nan
    avg_win = wins['net_pnl'].mean() if len(wins) else 0
    avg_loss = losses['net_pnl'].mean() if len(losses) else 0
    payoff = abs(avg_win / avg_loss) if avg_loss != 0 else np.nan
    
    print(f"Net PnL Total: ${total_net:,.2f} USD")
    print(f"Comisiones: ${total_comm:,.2f} | Swap: ${total_swap:,.2f}")
    print(f"Ganadoras: {len(wins)} | Perdedoras: {len(losses)} | Break-Even/Cero: {len(evens)}")
    print(f"Win Rate: {wr:.2f}% | Profit Factor: {pf:.2f} | Payoff (Avg Win / Avg Loss): {payoff:.2f}")
    print(f"Ganancia media: ${avg_win:.2f} | Pérdida media: ${avg_loss:.2f}")
    if 'realized_rr' in closed.columns:
        print(f"Realized R medio: {closed['realized_rr'].mean():.3f} R (Mediana: {closed['realized_rr'].median():.3f} R)")
        print(f"R acumulado: {closed['realized_rr'].sum():.2f} R")

print("\n" + "="*80)
print("2. DESGLOSE POR INSTRUMENTO (TOP PÉRDIDAS vs TOP GANANCIAS)")
print("="*80)
by_inst = closed.groupby('instrument').agg(
    n=('id', 'count'),
    net_pnl=('net_pnl', 'sum'),
    wr=('net_pnl', lambda x: (x > 0).mean() * 100),
    avg_pnl=('net_pnl', 'mean'),
    sum_r=('realized_rr', 'sum'),
    avg_r=('realized_rr', 'mean')
).sort_values('net_pnl')

print("--- TOP 15 ACTIVOS CON MAYORES PÉRDIDAS NETAS ---")
print(by_inst.head(15).to_string())

print("\n--- TOP 15 ACTIVOS MÁS RENTABLES ---")
print(by_inst.tail(15).iloc[::-1].to_string())

print("\n" + "="*80)
print("3. DESGLOSE POR MOTIVO DE SALIDA (EXIT_REASON)")
print("="*80)
by_exit = closed.groupby('exit_reason').agg(
    n=('id', 'count'),
    net_pnl=('net_pnl', 'sum'),
    wr=('net_pnl', lambda x: (x > 0).mean() * 100),
    avg_r=('realized_rr', 'mean')
).sort_values('net_pnl')
print(by_exit.to_string())

print("\n" + "="*80)
print("4. DESGLOSE POR ESTRATEGIA / SOURCE / SETUP_REASON")
print("="*80)
for col in ['source', 'strategy_version', 'setup_reason']:
    if col in closed.columns:
        print(f"\n--- Agrupado por {col} ---")
        g = closed.groupby(col).agg(
            n=('id', 'count'),
            net_pnl=('net_pnl', 'sum'),
            wr=('net_pnl', lambda x: (x > 0).mean() * 100),
            sum_r=('realized_rr', 'sum')
        ).sort_values('net_pnl')
        print(g.head(10).to_string())

print("\n" + "="*80)
print("5. ANÁLISIS DE RIESGO: SLIPPAGE Y PÉRDIDAS EXCESIVAS (> 1.05 R)")
print("="*80)
if 'realized_rr' in closed.columns:
    excessive_losses = closed[closed['realized_rr'] < -1.05]
    print(f"Trades con pérdida superior a 1.05 R (deslizamiento de SL/gap/spread): {len(excessive_losses)} ({len(excessive_losses)/len(closed)*100:.2f}%)")
    if len(excessive_losses) > 0:
        print(excessive_losses[['instrument', 'direction', 'exit_reason', 'realized_rr', 'net_pnl', 'entry_time']].sort_values('realized_rr').head(10).to_string())

print("\n" + "="*80)
print("6. DIRECCIÓN (BUY vs SELL) POR TIPO DE ACTIVO")
print("="*80)
dir_perf = closed.groupby(['direction']).agg(
    n=('id', 'count'),
    net_pnl=('net_pnl', 'sum'),
    wr=('net_pnl', lambda x: (x > 0).mean() * 100),
    avg_r=('realized_rr', 'mean')
)
print(dir_perf.to_string())

conn.close()
