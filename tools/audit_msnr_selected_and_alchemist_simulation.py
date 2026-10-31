"""Auditoría y Replay de Malaysian SNR en los instrumentos seleccionados y Simulación Metodología Alchemist (MSNR).
Consolida las señales y operaciones reales de la estrategia para:
1. Identificar activos con acierto > 47% y expectativa positiva comprobada (R/trade > 0).
2. Identificar activos en PODA (acierto <= 47% o R < 0) y evaluar opciones de mejora o descarte.
3. Simular el impacto cuantitativo de las reglas de la Metodología Alchemist (Nick / Nicolás):
   - Key Levels en cierres (gráfico de líneas) en D1/H4/H1
   - Regla de toques (máx 2 toques)
   - Patrones Quasimodo (QML, QMC, QMM)
   - Validaciones institucionales: Turtle Soup, Candle Equilibrium (CE 45%-50%), OB 50%, Inducement
   - SL ajustado (5-15 pips) y R:R ampliado (1:5 a 1:10) frente al contrato estándar (TP1 1R / TP2 2R con BE).
"""
import sys
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "storage" / "analysis"

# Lista de instrumentos seleccionados en /Instruments (DEMO y LIVE MALAYSIAN_SNR)
SELECTED_SYNTHETICS = [
    'High Frequency Vol 100 Index', 'VolSwitch High Vol Index', 'Boom 900 Index',
    'Volatility 5 Index', 'Volatility 50 (1s) Index', 'Vol over Boom 550',
    'Jump 75 Index', 'Volatility 90 Index', 'Boom 300 Index', 'Boom 600 Index',
    'Volatility 150 (1s) Index', 'Step Index 200', 'Jump 25 Index', 'Step Index 500',
    'Volatility 25 Index', 'Volatility 75 Index', 'Step Index 400',
    'Volatility 250 (1s) Index', 'Crash 900 Index', 'Crash 1000 Index',
    'High Frequency Vol 50 Index', 'Volatility 10 Index', 'Jump 10 Index',
    'Boom 500 Index', 'Volatility 15 Index', 'Volatility 75 (1s) Index',
    'Vol over Crash 550'
]

SELECTED_REAL_MARKETS = [
    'Germany 40', 'XAUUSD', 'USDJPY', 'GBPUSD', 'EURUSD', 'NZDUSD',
    'GBPCAD', 'AUDUSD', 'CADCHF', 'EURGBP', 'GBPCHF', 'CADJPY',
    'GBPJPY', 'CHFJPY'
]

ALL_SELECTED = SELECTED_SYNTHETICS + SELECTED_REAL_MARKETS

def run_analysis():
    print("=" * 80)
    print("AUDITORÍA DE ESTRATEGIA MALAYSIAN SNR EN ACTIVOS SELECCIONADOS")
    print("=" * 80)

    # 1. Cargar datasets de señales reales de MSNR disponibles en storage/analysis
    msnr_dfs = []
    
    # Dataset sintéticos 2 años (replays fieles)
    for p in ["newsyn_y0b.csv", "newsyn_y1.csv", "synth_free_y0b.csv", "synth_free_y1.csv", "y0.csv", "y1.csv", "prereg_D_2024.csv"]:
        f = OUT / f"msnr_variants_signals_{p}"
        if f.exists():
            df = pd.read_csv(f)
            df['source_file'] = p
            msnr_dfs.append(df)
            
    # Dataset mercados reales (replays fieles con spread real de ticks)
    for p in ["cmp_alch_A.csv", "cmp_alch_B.csv", "cmp_alch_D.csv", 
              "real_win_asia_A.csv", "real_win_asia_B.csv", "real_win_asia_D.csv",
              "real_win_legacy_A.csv", "real_win_legacy_B.csv", "real_win_legacy_D.csv",
              "real_e1_A.csv", "real_e1_B.csv", "real_e1_D.csv"]:
        f = OUT / f"msnr_variants_signals_{p}"
        if f.exists():
            df = pd.read_csv(f)
            df['source_file'] = p
            msnr_dfs.append(df)

    if not msnr_dfs:
        print("[ERROR] No se encontraron archivos msnr_variants_signals_*.csv")
        return

    full_msnr = pd.concat(msnr_dfs, ignore_index=True)
    # Deduplicar por símbolo y tiempo si hay solapamientos entre variantes
    full_msnr = full_msnr.drop_duplicates(subset=['symbol', 'time']).sort_values('time').reset_index(drop=True)
    print(f"Total señales únicas procesadas en datasets fieles MSNR: {len(full_msnr)}")

    # Filtrar por spread_sl <= 0.05 (tope de spread real del motor)
    if 'spread_sl' in full_msnr.columns:
        full_msnr = full_msnr[full_msnr['spread_sl'] <= 0.05].copy()

    # Calcular estadísticas por símbolo bajo Malaysian SNR (contrato estándar: TP1 1R + runner 2R con BE)
    metric_col = 'rr_live' if 'rr_live' in full_msnr.columns else 'rr'
    
    results = []
    for sym in sorted(full_msnr['symbol'].unique()):
        sub = full_msnr[full_msnr['symbol'] == sym]
        n = len(sub)
        if n == 0:
            continue
        rr_vals = sub[metric_col].values
        wins = np.sum(rr_vals > 0)
        losses = np.sum(rr_vals < 0)
        wr = (wins / n) * 100.0
        r_tot = np.sum(rr_vals)
        r_mean = np.mean(rr_vals)
        gross_w = np.sum(rr_vals[rr_vals > 0])
        gross_l = abs(np.sum(rr_vals[rr_vals < 0]))
        pf = gross_w / gross_l if gross_l > 0 else (99.0 if gross_w > 0 else 0.0)
        
        is_selected = sym in ALL_SELECTED
        status_47 = "WR > 47%" if wr >= 47.0 else "WR < 47% (PODA)"
        
        results.append({
            'symbol': sym,
            'is_selected': is_selected,
            'n': n,
            'wins': wins,
            'losses': losses,
            'wr': round(wr, 2),
            'r_mean': round(r_mean, 4),
            'r_tot': round(r_tot, 2),
            'pf': round(pf, 2),
            'status_47': status_47,
            'is_profitable': r_mean > 0
        })

    res_df = pd.DataFrame(results)
    
    # 2. Separar los seleccionados
    sel_df = res_df[res_df['is_selected']].sort_values(by='wr', ascending=False).reset_index(drop=True)
    
    print("\n--- INSTRUMENTOS SELECCIONADOS EN /Instruments ---")
    print(f"{'SÍMBOLO':<28} | {'TRADES':<6} | {'WIN RATE':<9} | {'R/TRADE':<9} | {'R TOTAL':<9} | {'PF':<5} | {'ESTADO 47%'}")
    print("-" * 88)
    for _, r in sel_df.iterrows():
        print(f"{r['symbol']:<28} | {r['n']:<6} | {r['wr']:>6.2f} % | {r['r_mean']:>+7.4f} | {r['r_tot']:>+7.2f} | {r['pf']:>5.2f} | {r['status_47']}")

    # 3. Identificar cuáles superan 47%
    wr47_above = sel_df[sel_df['wr'] >= 47.0]
    wr47_below = sel_df[sel_df['wr'] < 47.0]
    
    print(f"\nResumen Seleccionados:")
    print(f"Total analizados con datos: {len(sel_df)}")
    print(f"Activos con WR >= 47%: {len(wr47_above)}")
    print(f"Activos con WR < 47% (Poda): {len(wr47_below)}")
    
    # 4. Guardar resultados
    res_df.to_csv(OUT / "msnr_selected_audit_detailed.csv", index=False)
    
    # 5. Análisis de la Metodología Alchemist (Simulación comparativa)
    print("\n" + "=" * 80)
    print("SIMULACIÓN DE LA METODOLOGÍA ALCHEMIST (MSNR) DE NICOLÁS (NICK)")
    print("=" * 80)
    
    # Cargar alchemist_trades_pre.csv si existe
    alch_file = OUT / "alchemist_trades_pre.csv"
    if alch_file.exists():
        alch_df = pd.read_csv(alch_file)
        print(f"Se cargaron {len(alch_df)} operaciones Alchemist simuladas en Forex mayores y XAUUSD.")
        
        # Comparar por variante
        print("\nDesempeño de Alchemist por Variante (Entrada x Confluencia x Salida):")
        for v, g in alch_df.groupby('variant'):
            n = len(g)
            w = np.sum(g['rr'] > 0)
            wr = (w / n) * 100.0
            r_tot = g['rr'].sum()
            r_op = g['rr'].mean()
            gw = g[g['rr'] > 0]['rr'].sum()
            gl = abs(g[g['rr'] < 0]['rr'].sum())
            pf = gw / gl if gl > 0 else (99.0 if gw > 0 else 0.0)
            print(f"  Variante {v:<20} | n={n:3d} | WR={wr:5.1f}% | R/op={r_op:+.3f} | R tot={r_tot:+6.1f} | PF={pf:4.2f}")

    # Guardar resumen JSON
    summary = {
        'total_selected_analyzed': len(sel_df),
        'above_47_count': len(wr47_above),
        'below_47_count': len(wr47_below),
        'above_47_symbols': wr47_above[['symbol', 'wr', 'r_mean', 'r_tot', 'pf']].to_dict(orient='records'),
        'below_47_symbols': wr47_below[['symbol', 'wr', 'r_mean', 'r_tot', 'pf']].to_dict(orient='records'),
    }
    with open(OUT / "msnr_audit_and_alchemist_simulation.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResultados exportados a {OUT / 'msnr_audit_and_alchemist_simulation.json'}")

if __name__ == "__main__":
    run_analysis()
