import json

with open("scratch/gbp_5y_replay_results.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print("| Instrumento | MSNR Base (Ops/Día - WR) | ICT Base (Ops/Día - WR) | Combined Base (Ops/Día) | MultiStrategia Optimizada (Ops/Día - WR) | Delta Ops/Día | Delta R Neto |")
print("|---|---|---|---|---|---|---|")

for sym, info in data.items():
    base = info["baseline"]
    opt = info["optimized_multistrategy"]
    m_base = base["msnr"]
    i_base = base["ict"]
    m_dr = base["daily_rate_msnr"]
    i_dr = base["daily_rate_ict"]
    c_dr = base["daily_rate_combined"]
    
    o_dr = opt["daily_rate"]
    o_wr = opt["win_rate"]
    
    net_base_r = m_base["net_r"] + i_base["net_r"]
    net_opt_r = opt["net_r"]
    delta_r = net_opt_r - net_base_r
    
    print(f"| **{sym}** | {m_dr} ({m_base['win_rate']}%) | {i_dr} ({i_base['win_rate']}%) | {c_dr} ops/d | **{o_dr} ({o_wr:.1f}%)** | **+{o_dr - c_dr:.2f} ops/d** | **+{delta_r:,.1f} R** |")
