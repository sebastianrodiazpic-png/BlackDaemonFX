import pandas as pd
import numpy as np
from zoneinfo import ZoneInfo
from pathlib import Path

df = pd.read_csv('storage/analysis/ict_faithful_trades.csv')
time_col = [c for c in df.columns if 'time' in c.lower() or 'date' in c.lower()][0]
df['time_utc'] = pd.to_datetime(df[time_col], utc=True)
ny_tz = ZoneInfo("America/New_York")
df['time_ny'] = df['time_utc'].dt.tz_convert(ny_tz)
df['ny_hour_exact'] = df['time_ny'].dt.hour
df['ny_minute_exact'] = df['time_ny'].dt.minute
df['time_ny_float'] = df['ny_hour_exact'] + df['ny_minute_exact'] / 60.0

print("=================================================================")
print("ICT TIME FILTER FORENSIC AUDIT: 07:00-09:00 vs 07:00-09:30 NY")
print("=================================================================")
print(f"Total Trades in ict_faithful_trades.csv: {len(df)}")
print(f"Net R Total: {df['rr'].sum():.2f} R, Mean R: {df['rr'].mean():.4f} R")

# Window 1: 07:00 to 09:00 NY (hours 7 and 8)
mask_07_09 = (df['time_ny_float'] >= 7.0) & (df['time_ny_float'] < 9.0)
df_filtered_07_09 = df[~mask_07_09]
print(f"\n1. Bloqueo 07:00 - 09:00 NY:")
print(f"   Trades eliminados: {mask_07_09.sum()} ({mask_07_09.sum()/len(df)*100:.1f}%) | PnL eliminado: {df[mask_07_09]['rr'].sum():.2f} R")
print(f"   Trades restantes: {len(df_filtered_07_09)} | PnL restante: {df_filtered_07_09['rr'].sum():.2f} R | Expectativa: {df_filtered_07_09['rr'].mean():.4f} R | WinRate: {(df_filtered_07_09['rr'] > 0).mean()*100:.2f}%")

# Window 2: 07:00 to 09:30 NY (hours 7, 8 and first 30 mins of 9)
mask_07_0930 = (df['time_ny_float'] >= 7.0) & (df['time_ny_float'] < 9.5)
df_filtered_07_0930 = df[~mask_07_0930]
print(f"\n2. Bloqueo 07:00 - 09:30 NY:")
print(f"   Trades eliminados: {mask_07_0930.sum()} ({mask_07_0930.sum()/len(df)*100:.1f}%) | PnL eliminado: {df[mask_07_0930]['rr'].sum():.2f} R")
print(f"   Trades restantes: {len(df_filtered_07_0930)} | PnL restante: {df_filtered_07_0930['rr'].sum():.2f} R | Expectativa: {df_filtered_07_0930['rr'].mean():.4f} R | WinRate: {(df_filtered_07_0930['rr'] > 0).mean()*100:.2f}%")

# Window 3: Bloqueo completo 07:00 to 10:00 NY (hours 7, 8, 9)
mask_07_10 = (df['time_ny_float'] >= 7.0) & (df['time_ny_float'] < 10.0)
df_filtered_07_10 = df[~mask_07_10]
print(f"\n3. Bloqueo 07:00 - 10:00 NY:")
print(f"   Trades eliminados: {mask_07_10.sum()} ({mask_07_10.sum()/len(df)*100:.1f}%) | PnL eliminado: {df[mask_07_10]['rr'].sum():.2f} R")
print(f"   Trades restantes: {len(df_filtered_07_10)} | PnL restante: {df_filtered_07_10['rr'].sum():.2f} R | Expectativa: {df_filtered_07_10['rr'].mean():.4f} R | WinRate: {(df_filtered_07_10['rr'] > 0).mean()*100:.2f}%")

# Session Breakdown: London vs NY vs Asia
print("\n--- Desglose por Sesiones Canónicas ---")
london_mask = (df['time_ny_float'] >= 2.0) & (df['time_ny_float'] < 5.0)
ny_am_mask = (df['time_ny_float'] >= 9.5) & (df['time_ny_float'] < 12.0)
asia_mask = (df['time_ny_float'] >= 19.0) | (df['time_ny_float'] < 0.0)

print(f"Londres (02:00 - 05:00 NY): {london_mask.sum()} trades | Net R: {df[london_mask]['rr'].sum():.2f} R | WinRate: {(df[london_mask]['rr']>0).mean()*100:.2f}% | Mean R: {df[london_mask]['rr'].mean():.4f} R")
print(f"NY AM Post-Open (09:30 - 12:00 NY): {ny_am_mask.sum()} trades | Net R: {df[ny_am_mask]['rr'].sum():.2f} R | WinRate: {(df[ny_am_mask]['rr']>0).mean()*100:.2f}% | Mean R: {df[ny_am_mask]['rr'].mean():.4f} R")
print(f"Asia / Noche (19:00 - 00:00 NY): {asia_mask.sum()} trades | Net R: {df[asia_mask]['rr'].sum():.2f} R | WinRate: {(df[asia_mask]['rr']>0).mean()*100:.2f}% | Mean R: {df[asia_mask]['rr'].mean():.4f} R")

# Breakdown by Asset Class
print("\n--- Desglose por Clase de Activo ---")
for synth, grp in df.groupby('synthetic'):
    label = "Sintéticos" if synth else "Financieros (Forex, Metales, Índices, Cripto)"
    print(f"{label:45s}: {len(grp):4d} trades | Net R: {grp['rr'].sum():.2f} R | WinRate: {(grp['rr']>0).mean()*100:.2f}% | Mean R: {grp['rr'].mean():.4f} R")
