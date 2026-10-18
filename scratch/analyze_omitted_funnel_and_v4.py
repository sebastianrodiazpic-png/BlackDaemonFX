"""
scratch/analyze_omitted_funnel_and_v4.py
Analiza el embudo de filtrado para los 14 activos omitidos y su consolidación
con la base histórica de 727 trades para formar el portafolio canónico completo de 23 activos.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from strategy.malaysian_snr.config import MalaysianSNRConfig

def main():
    p_orig = PROJECT_ROOT / 'storage' / 'analysis' / 'msnr_faithful_trades.csv'
    p_omit = PROJECT_ROOT / 'scratch' / 'omitted_14_msnr_faithful_trades.csv'

    df_orig = pd.read_csv(p_orig)
    df_omit = pd.read_csv(p_omit)

    cfg = MalaysianSNRConfig()
    canonical_symbols = sorted(list(set(s.replace('micro', '') for s in cfg.allowed_symbols)))

    # Filtrar df_orig a los que están en la allowlist canónica
    df_orig_canon = df_orig[df_orig['symbol'].isin(canonical_symbols)].copy()
    df_orig_canon['time'] = pd.to_datetime(df_orig_canon['time'], utc=True)
    df_orig_canon['exit_time'] = df_orig_canon['time'] + pd.to_timedelta(df_orig_canon['bars'] * 15, unit='m')

    df_omit['time'] = pd.to_datetime(df_omit['time'], utc=True)
    if 'exit_time' not in df_omit.columns:
        df_omit['exit_time'] = df_omit['time'] + pd.to_timedelta(df_omit['bars'] * 15, unit='m')
    else:
        df_omit['exit_time'] = pd.to_datetime(df_omit['exit_time'], utc=True)

    print(f"Trades en dataset original (filtrado a allowlist): {len(df_orig_canon)} (9 símbolos)")
    print(f"Trades en dataset de activos omitidos:            {len(df_omit)} (14 símbolos)")

    # Unificar datasets
    df_full = pd.concat([df_orig_canon, df_omit], ignore_index=True)
    df_full = df_full.sort_values('time').reset_index(drop=True)

    print(f"\nTotal trades en universo canónico COMPLETO de 23 activos: {len(df_full)}")
    print(f"Verificación de exit_time nulos: {df_full['exit_time'].isna().sum()}")

    # Análisis del embudo en los 14 omitidos
    print("\n" + "=" * 105)
    print("EMBUDO DE FILTRADO PARA LOS 14 ACTIVOS PREVIAMENTE OMITIDOS")
    print("=" * 105)
    print(f"{'Símbolo':26s} | {'Raw':4s} | {'Raw PnL':9s} | {'ADX>=30':7s} | {'ADX PnL':9s} | {'ADX+ATR<=1.5':12s} | {'ADX+ATR PnL':11s}")
    print("-" * 105)

    omitted_symbols = sorted(df_omit['symbol'].unique())
    for sym in omitted_symbols:
        s_raw = df_omit[df_omit['symbol'] == sym]
        s_adx = s_raw[s_raw['adx'] >= 30.0]
        s_adx_atr = s_adx[s_adx['risk_atr'] <= 1.5]

        n_raw = len(s_raw)
        p_raw = s_raw['rr'].sum()
        n_adx = len(s_adx)
        p_adx = s_adx['rr'].sum() if n_adx > 0 else 0.0
        n_atr = len(s_adx_atr)
        p_atr = s_adx_atr['rr'].sum() if n_atr > 0 else 0.0

        print(f"{sym:26s} | {n_raw:4d} | {p_raw:+8.2f}R | {n_adx:7d} | {p_adx:+8.2f}R | {n_atr:12d} | {p_atr:+10.2f}R")

    # Guardar dataset completo en scratch
    out_full_path = PROJECT_ROOT / 'scratch' / 'msnr_complete_23_faithful_trades.csv'
    df_full.to_csv(out_full_path, index=False)
    print(f"\nGuardado dataset consolidado de los 23 activos canónicos en:\n  {out_full_path}")

if __name__ == '__main__':
    main()
