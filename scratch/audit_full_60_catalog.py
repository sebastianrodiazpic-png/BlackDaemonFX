"""
scratch/audit_full_60_catalog.py
================================
Auditoría exhaustiva del universo completo de 60 instrumentos disponibles en data/cache_msnr.
Documenta:
- Símbolo y nombre canónico
- Familia de activos (Forex, Metales/Índices, Sintéticos, Crypto, Commodities)
- Barras M15, Fecha inicio, Fecha fin, Años exactos
- Barras H1, Fecha inicio, Fecha fin
- Existencia de vacíos temporales significativos
- Spread típico observado en Deriv MT5
- Clasificación de universos:
    * Catálogo general (60)
    * MSNR 19 Oficial Habilitado en SQLite
    * MSNR 23 Canónico Expandido
    * ICT 14 Oficial Habilitado
    * Universo Experimental Alternativo (60)
"""

import pickle
import pandas as pd
import numpy as np
from pathlib import Path

CACHE_DIR = Path("data/cache_msnr")

# Universos Oficiales
MSNR_19 = set([
    'Crash 500 Index', 'Crash 600 Index', 'Crash 1000 Index', 'Boom 1000 Index',
    'Boom 500 Index', 'Boom 300 Index', 'Step Index', 'Step Index 400',
    'Wall Street 30', 'XAUUSD', 'EURUSD', 'GBPUSD', 'USDJPY',
    'GBPJPY', 'GBPAUD', 'Jump 10 Index', 'Jump 25 Index', 'Jump 50 Index', 'BTCUSD'
])

MSNR_23 = set([
    'Boom 1000 Index', 'Boom 300 Index', 'Boom 500 Index', 'Crash 1000 Index',
    'Crash 500 Index', 'Crash 600 Index', 'Jump 10 Index', 'Jump 25 Index',
    'Jump 50 Index', 'Step Index', 'Step Index 200', 'Step Index 400',
    'Step Index 500', 'Volatility 250 (1s) Index', 'Volatility 50 (1s) Index',
    'Volatility 90 Index', 'XAUUSD', 'XAGUSD', 'Wall Street 30', 'EURUSD',
    'GBPUSD', 'USDJPY', 'AUDNZD'
])

ICT_14 = set([
    'XAUUSD', 'EURUSD', 'Jump 50 Index', 'Crash 300 Index', 'Boom 500 Index',
    'Boom 300 Index', 'Boom 1000 Index', 'Boom 600 Index', 'Jump 25 Index',
    'BTCUSD', 'Step Index 400', 'Wall Street 30', 'US Tech 100', 'US SP 500'
])

# Spreads típicos observados en Deriv MT5
SPREADS_DICT = {
    # Forex
    'AUDCAD': 0.00025, 'AUDCHF': 0.00025, 'AUDJPY': 0.025, 'AUDNZD': 0.00025, 'AUDUSD': 0.00018,
    'CADCHF': 0.00025, 'CADJPY': 0.025, 'CHFJPY': 0.028, 'EURAUD': 0.00025, 'EURCAD': 0.00025,
    'EURCHF': 0.00022, 'EURGBP': 0.00018, 'EURJPY': 0.022, 'EURNZD': 0.00030, 'EURUSD': 0.00015,
    'GBPAUD': 0.00028, 'GBPCAD': 0.00028, 'GBPCHF': 0.00028, 'GBPJPY': 0.026, 'GBPNZD': 0.00035,
    'GBPUSD': 0.00020, 'USDCAD': 0.00020, 'USDCHF': 0.00018, 'USDJPY': 0.018,
    # Metales & Índices
    'XAUUSD': 0.25, 'XAGUSD': 0.025, 'Wall_Street_30': 2.50, 'US_Tech_100': 1.25, 'US_SP_500': 0.50,
    'US_Oil': 0.04,
    # Cripto
    'BTCUSD': 15.0,
    # Sintéticos Boom / Crash
    'Boom_1000_Index': 0.50, 'Boom_300_Index': 0.20, 'Boom_500_Index': 0.50, 'Boom_600_Index': 0.60, 'Boom_900_Index': 0.60,
    'Crash_1000_Index': 0.50, 'Crash_300_Index': 0.30, 'Crash_500_Index': 0.50, 'Crash_600_Index': 0.50, 'Crash_900_Index': 0.60,
    # Sintéticos Jump / Step
    'Jump_10_Index': 2.50, 'Jump_25_Index': 1.50, 'Jump_50_Index': 2.00, 'Jump_75_Index': 3.00, 'Jump_100_Index': 4.00,
    'Step_Index': 0.10, 'Step_Index_200': 0.20, 'Step_Index_400': 0.40, 'Step_Index_500': 0.50,
    # Sintéticos Volatility
    'Volatility_10_Index': 0.50, 'Volatility_15_Index': 0.15, 'Volatility_25_Index': 0.50, 'Volatility_50_Index': 0.50,
    'Volatility_75_Index': 0.75, 'Volatility_90_Index': 0.90, 'Volatility_100_Index': 1.00,
    'Volatility_50_(1s)_Index': 0.05, 'Volatility_75_(1s)_Index': 0.075, 'Volatility_250_(1s)_Index': 0.0035
}

def clean_name(stem):
    # Convierte 'Boom_1000_Index' a 'Boom 1000 Index' salvo Volatility_250_(1s)_Index
    s = stem.replace("_M15", "")
    if "(1s)" in s:
        s_clean = s.replace("_", " ").replace("  ", " ").replace("(1s) ", "(1s) ")
        return s_clean
    return s.replace("_", " ")

def get_subfamily(sym_clean):
    s = sym_clean
    if any(s.startswith(x) for x in ['Boom', 'Crash']):
        return 'Sintético Crash/Boom'
    elif any(s.startswith(x) for x in ['Jump', 'Step']):
        return 'Sintético Jump/Step'
    elif s.startswith('Volatility'):
        return 'Sintético Volatility'
    elif s in ['XAUUSD', 'XAGUSD', 'Wall Street 30', 'US Tech 100', 'US SP 500']:
        return 'Metales & Índices'
    elif s == 'US Oil':
        return 'Commodities (Energía)'
    elif s == 'BTCUSD':
        return 'Criptomonedas'
    else:
        return 'Forex'

def main():
    m15_files = sorted(list(CACHE_DIR.glob("*_M15.pkl")))
    records = []
    
    for f in m15_files:
        stem = f.stem.replace("_M15", "")
        sym_clean = clean_name(stem)
        subfam = get_subfamily(sym_clean)
        
        with open(f, "rb") as pkl_f:
            df_m15 = pickle.load(pkl_f)
            
        t_col = 'time' if 'time' in df_m15.columns else 'datetime' if 'datetime' in df_m15.columns else None
        if t_col:
            times = pd.to_datetime(df_m15[t_col], utc=True)
        else:
            times = pd.to_datetime(df_m15.index, utc=True)
            
        n_m15 = len(df_m15)
        start_m15 = times.iloc[0]
        end_m15 = times.iloc[-1]
        days_m15 = (end_m15 - start_m15).total_seconds() / 86400.0
        years_m15 = days_m15 / 365.25
        
        # Verificar vacíos temporales esperados (delta promedio)
        deltas = times.diff().dt.total_seconds().dropna()
        max_gap_hours = deltas.max() / 3600.0 if len(deltas) > 0 else 0
        
        # H1
        h1_file = CACHE_DIR / f"{stem}_H1.pkl"
        n_h1 = 0
        if h1_file.exists():
            with open(h1_file, "rb") as h1_f:
                df_h1 = pickle.load(h1_f)
            n_h1 = len(df_h1)
            
        spread = SPREADS_DICT.get(stem, SPREADS_DICT.get(sym_clean, 0.0001))
        
        in_msnr_19 = sym_clean in MSNR_19 or stem in MSNR_19
        in_msnr_23 = sym_clean in MSNR_23 or stem in MSNR_23
        in_ict_14 = sym_clean in ICT_14 or stem in ICT_14
        
        records.append({
            "symbol": sym_clean,
            "raw_stem": stem,
            "family": subfam,
            "m15_rows": n_m15,
            "start_date": str(start_m15)[:10],
            "end_date": str(end_m15)[:10],
            "years_m15": round(years_m15, 2),
            "h1_rows": n_h1,
            "max_gap_hrs": round(max_gap_hours, 1),
            "spread_pts": spread,
            "in_msnr_19": in_msnr_19,
            "in_msnr_23": in_msnr_23,
            "in_ict_14": in_ict_14,
            "in_exp_60": True
        })
        
    df_all = pd.DataFrame(records)
    
    print("=" * 110)
    print("AUDITORÍA DE LOS 60 INSTRUMENTOS DISPONIBLES EN data/cache_msnr")
    print("=" * 110)
    print(df_all[['symbol', 'family', 'm15_rows', 'start_date', 'end_date', 'years_m15', 'spread_pts', 'in_msnr_19', 'in_msnr_23', 'in_ict_14']].to_string())
    
    print("\n" + "=" * 80)
    print("RESUMEN POR FAMILIA DE ACTIVOS:")
    print("=" * 80)
    fam_summary = df_all.groupby('family').agg(
        total_activos=('symbol', 'count'),
        m15_filas_media=('m15_rows', 'mean'),
        anios_media=('years_m15', 'mean'),
        anios_min=('years_m15', 'min'),
        anios_max=('years_m15', 'max')
    )
    print(fam_summary.to_string())
    
    print("\n" + "=" * 80)
    print("RESUMEN DE COBERTURA DE AÑOS M15:")
    print("=" * 80)
    print(f"Total instrumentos: {len(df_all)}")
    print(f"Instrumentos con exactamente 2.00 años (Oct 2024 - Oct 2026): {len(df_all[df_all['years_m15'] >= 1.99])}")
    print(f"Instrumentos con < 2.00 años: {len(df_all[df_all['years_m15'] < 1.99])}")
    for _, r in df_all[df_all['years_m15'] < 1.99].iterrows():
        print(f"  * {r['symbol']}: {r['years_m15']} años ({r['start_date']} a {r['end_date']}) - {r['m15_rows']} filas")
        
    # Guardar CSV de auditoría
    out_csv = Path("scratch/audit_full_60_catalog.csv")
    df_all.to_csv(out_csv, index=False)
    print(f"\n[OK] Guardado reporte completo en {out_csv}")

if __name__ == '__main__':
    main()
