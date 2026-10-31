import json

with open("storage/analysis/orb_improvements_simulation_results.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for m_name in ["M1_BASELINE_ACTUAL", "M2_DESCUBRIMIENTO_PLENO", "M3_ATR_SWEEP_CALIBRADO"]:
    print(f"\n=================== {m_name} ===================")
    m = data[m_name]
    for sym, res in m["asset_breakdown"].items():
        print(f"  {sym:10s} | n={res['n']:3d} | WR={res['win_rate']:5.2f}% | R/op={res['r_op']:+6.4f} | Total={res['total_r']:+6.2f} R | PF={res['pf']:4.2f} | H1={res['h1_r']:+5.1f} | H2={res['h2_r']:+5.1f}")
