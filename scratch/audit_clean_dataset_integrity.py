import sys
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

csv_path = PROJECT_ROOT / "scratch" / "msnr_complete_23_faithful_trades_clean.csv"
if not csv_path.exists():
    print("ERROR: Archivo no encontrado:", csv_path)
    sys.exit(1)

df = pd.read_csv(csv_path)
print(f"=== AUDITORÍA DE INTEGRIDAD DEL DATASET LIMPIO: {csv_path.name} ===")
print(f"Total de filas: {len(df)}")
print(f"Columnas ({len(df.columns)}): {df.columns.tolist()}")

# 1. Chequeo de duplicados
dup_full = df.duplicated().sum()
dup_key = df.duplicated(subset=['time', 'symbol']).sum()
print(f"\n1. DUPLICADOS:")
print(f"  - Filas exactamente duplicadas: {dup_full}")
print(f"  - Duplicados en clave (time, symbol): {dup_key}")

# 2. Chequeo de Símbolos y Universo Canónico
from strategy.malaysian_snr.config import MalaysianSNRConfig
cfg = MalaysianSNRConfig()
canonical = sorted(list(set(s.replace('micro', '') for s in cfg.allowed_symbols)))
unique_syms = sorted(df['symbol'].unique())

print(f"\n2. COBERTURA DEL UNIVERSO CANÓNICO:")
print(f"  - Símbolos únicos en CSV: {len(unique_syms)} de {len(canonical)}")
diff = set(canonical) - set(unique_syms)
if diff:
    print(f"  - Símbolos faltantes: {diff}")
else:
    print("  - TODOS los 23 símbolos canónicos están presentes.")

print("\n  Desglose de trades base por símbolo:")
counts = df['symbol'].value_counts()
for s in canonical:
    c = counts.get(s, 0)
    print(f"    {s:26s} : {c:3d} trades")

# 3. Chequeo de Trazabilidad de Timestamps y Lookahead
df['time'] = pd.to_datetime(df['time'], utc=True)
df['exit_time'] = pd.to_datetime(df['exit_time'], utc=True)

null_time = df['time'].isna().sum()
null_exit = df['exit_time'].isna().sum()
bad_order = (df['exit_time'] <= df['time']).sum()

print(f"\n3. INTEGRIDAD TEMPORAL:")
print(f"  - Timestamps nulos en time: {null_time}")
print(f"  - Timestamps nulos en exit_time: {null_exit}")
print(f"  - Inconsistencias de orden (exit_time <= time): {bad_order}")
print(f"  - Rango temporal total: {df['time'].min()} a {df['time'].max()}")

# 4. Chequeo de Métricas RR y Outliers / Overrides Manuales
print(f"\n4. DISTRIBUCIÓN DE OUTCOMES Y VALORES RR:")
print(df.groupby('outcome')['rr'].agg(['count', 'min', 'mean', 'max']))

# Chequeo específico de Volatility 250 (1s) Index
v250 = df[df['symbol'] == 'Volatility 250 (1s) Index']
print(f"\n5. AUDITORÍA ESPECÍFICA DE VOLATILITY 250 (1s) INDEX:")
print(f"  - Filas: {len(v250)}")
print(f"  - Outcomes: {dict(v250['outcome'].value_counts())}")
print(f"  - Rango RR: min={v250['rr'].min()}, mean={v250['rr'].mean():.3f}, max={v250['rr'].max()}")
print(f"  - Net PnL (R): {v250['rr'].sum():+.2f} R")
outliers_v250 = v250[v250['rr'] < -2.0]
print(f"  - Filas con RR < -2.0 en Volatility 250: {len(outliers_v250)}")
