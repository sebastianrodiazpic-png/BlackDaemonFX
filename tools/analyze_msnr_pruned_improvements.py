"""Test de mejoras sobre activos de Malaysian SNR que caen en PODA (WR < 47% o R < 0).
Evalúa:
1. Asimetría direccional (Boom solo BUY, Crash solo SELL, Pares solo tendencia H1).
2. Filtro de ADX H1 (ADX >= 25 o >= 30).
3. Filtro de Body Ratio (vela de quiebre sólida >= 60%).
4. Filtro de sesiones horarias (solo Londres 08-11 UTC o solo NY 13-17 UTC).
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "storage" / "analysis"

PRUNED_OR_LOSING = [
    'Boom 600 Index', 'Boom 900 Index', 'Crash 1000 Index', 'EURUSD', 'AUDUSD', 'CHFJPY',
    'Volatility 10 Index', 'Volatility 150 (1s) Index', 'Volatility 50 (1s) Index', 'Volatility 25 Index',
    'Crash 900 Index', 'GBPJPY', 'CADJPY'
]

def analyze_improvements():
    # Cargar todos los datasets
    msnr_dfs = []
    for p in ["newsyn_y0b.csv", "newsyn_y1.csv", "synth_free_y0b.csv", "synth_free_y1.csv", "y0.csv", "y1.csv", "prereg_D_2024.csv"]:
        f = OUT / f"msnr_variants_signals_{p}"
        if f.exists():
            df = pd.read_csv(f)
            msnr_dfs.append(df)
            
    for p in ["cmp_alch_A.csv", "cmp_alch_B.csv", "cmp_alch_D.csv", 
              "real_win_asia_A.csv", "real_win_asia_B.csv", "real_win_asia_D.csv",
              "real_win_legacy_A.csv", "real_win_legacy_B.csv", "real_win_legacy_D.csv",
              "real_e1_A.csv", "real_e1_B.csv", "real_e1_D.csv"]:
        f = OUT / f"msnr_variants_signals_{p}"
        if f.exists():
            df = pd.read_csv(f)
            msnr_dfs.append(df)

    full = pd.concat(msnr_dfs, ignore_index=True).drop_duplicates(subset=['symbol', 'time']).reset_index(drop=True)
    if 'spread_sl' in full.columns:
        full = full[full['spread_sl'] <= 0.05].copy()

    print("=" * 80)
    print("ANÁLISIS DE MEJORAS PARA ACTIVOS EN PODA / RESULTADO NEGATIVO")
    print("=" * 80)

    for sym in PRUNED_OR_LOSING:
        sub = full[full['symbol'] == sym].copy()
        if len(sub) < 5:
            continue
            
        base_n = len(sub)
        base_w = np.sum(sub['rr_live'] > 0)
        base_wr = (base_w / base_n) * 100
        base_r = sub['rr_live'].sum()
        base_rop = sub['rr_live'].mean()
        
        print(f"\n--- {sym} (Base: n={base_n}, WR={base_wr:.1f}%, R tot={base_r:+.2f}, R/op={base_rop:+.3f}) ---")
        
        # Mejora 1: Asimetría direccional
        for d in ['BUY', 'SELL']:
            d_sub = sub[sub['direction'] == d]
            if len(d_sub) >= 3:
                dn = len(d_sub)
                d_wr = (np.sum(d_sub['rr_live'] > 0) / dn) * 100
                d_r = d_sub['rr_live'].sum()
                d_rop = d_sub['rr_live'].mean()
                print(f"  [Dirección {d:<4}] n={dn:3d} | WR={d_wr:5.1f}% | R tot={d_r:+6.2f} | R/op={d_rop:+.3f}")
                
        # Mejora 2: Filtro ADX si existe en columnas
        if 'adx' in sub.columns:
            for adx_th in [25.0, 30.0]:
                adx_sub = sub[sub['adx'] >= adx_th]
                if len(adx_sub) >= 3:
                    an = len(adx_sub)
                    a_wr = (np.sum(adx_sub['rr_live'] > 0) / an) * 100
                    a_r = adx_sub['rr_live'].sum()
                    a_rop = adx_sub['rr_live'].mean()
                    print(f"  [Filtro ADX>={adx_th}] n={an:3d} | WR={a_wr:5.1f}% | R tot={a_r:+6.2f} | R/op={a_rop:+.3f}")

        # Mejora 3: Filtro Body Ratio si existe
        if 'body_ratio' in sub.columns:
            for br_th in [0.60, 0.70]:
                br_sub = sub[sub['body_ratio'] >= br_th]
                if len(br_sub) >= 3:
                    bn = len(br_sub)
                    b_wr = (np.sum(br_sub['rr_live'] > 0) / bn) * 100
                    b_r = br_sub['rr_live'].sum()
                    b_rop = br_sub['rr_live'].mean()
                    print(f"  [Filtro Body>={br_th}] n={bn:3d} | WR={b_wr:5.1f}% | R tot={b_r:+6.2f} | R/op={b_rop:+.3f}")

if __name__ == "__main__":
    analyze_improvements()
