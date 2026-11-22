import pandas as pd
import json

print("=== MSNR DATA FOR STEP INDEXES ===")
df_msnr = pd.read_csv('storage/analysis/replay_5y_msnr_synthetics_comparison.csv')
for s in ['Step Index', 'Step Index 200', 'Step Index 400', 'Step Index 500']:
    row = df_msnr[df_msnr['symbol'] == s]
    if not row.empty:
        r = row.iloc[0]
        print(f"{s}: Base Trades={r['trades_base']} (WR={r['wr_base']}%, R={r['r_base']}) | Opt Trades={r['trades_opt']} (WR={r['wr_opt']}%, R={r['r_opt']}) | Freq/mes={r['frecuencia_mensual_opt']}")

print("\n=== ICT V1 DATA FOR STEP INDEXES ===")
df_ict = pd.read_csv('storage/analysis/ict_5y_by_symbol.csv')
for s in ['Step Index', 'Step Index 200', 'Step Index 400', 'Step Index 500']:
    row = df_ict[df_ict['symbol'] == s]
    if not row.empty:
        r = row.iloc[0]
        print(f"{s}: Trades={r['n']} | WR={r['wr_pct']:.2f}% | Avg R={r['avg_r']:.4f} | Tot R={r['tot_r']:.2f} | PF={r['pf']:.2f} | MaxDD={r['max_dd_r']:.2f}R | Span={r['span_years']}y")

print("\n=== ICT V2 IMPROVED DATA FOR STEP INDEXES ===")
df_ict2 = pd.read_csv('storage/analysis/ict_5y_v2_improved_by_symbol.csv')
for s in ['Step Index', 'Step Index 200', 'Step Index 400', 'Step Index 500']:
    row = df_ict2[df_ict2['symbol'] == s]
    if not row.empty:
        r = row.iloc[0]
        print(f"{s}: Trades={r['v2_n']} | WR={r['v2_wr']:.2f}% | Avg R={r['v2_avg_r']:.4f} | Tot R={r['v2_tot_r']:.2f} | PF={r['v2_pf']:.2f} | MaxDD={r['v2_max_dd']:.2f}R | Span={r['span_years']}y")

print("\n=== STEP 300 MSNR DATA ===")
try:
    with open('storage/analysis/msnr_v21_two_years_20261011/results/Step_Index_300.json') as f:
        d = json.load(f)
        b_m = d['versions']['baseline']['metrics']
        v_m = d['versions']['v21']['metrics']
        print(f"Step Index 300 Baseline: Trades={b_m['trades']}, WR={b_m['win_pct']}%, Tot R={b_m['total_r']}, PF={b_m['profit_factor']}, MaxDD={b_m['max_drawdown_r']}R")
        print(f"Step Index 300 v21: Trades={v_m['trades']}, WR={v_m['win_pct']}%, Tot R={v_m['total_r']}, PF={v_m['profit_factor']}, MaxDD={v_m['max_drawdown_r']}R")
except Exception as e:
    print("Step 300 error:", e)
