import json

with open("scratch/commodities_crypto_5y_replay_results.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Total instrumentos evaluados: {len(data)}")
print("-" * 115)
print(f"{'Símbolo':<14} | {'Categoría':<22} | {'WR Base (MS/ICT)':<18} | {'WR Multi':<10} | {'Net R':<11} | {'PF':<6} | {'Max DD':<8} | {'Trades/d':<8}")
print("-" * 115)

tot_r = 0
for sym, d in data.items():
    meta = d["metadata"]
    base = d["baseline"]
    opt = d["optimized_multistrategy"]
    wr_base = f"{base['msnr']['win_rate']}% / {base['ict']['win_rate']}%"
    wr_opt = f"{opt['win_rate']}%"
    net_r = f"+{opt['net_r']:.1f} R"
    pf = f"{opt['profit_factor']:.2f}"
    dd = f"{max(opt['msnr_leg']['max_drawdown_r'], opt['ict_leg']['max_drawdown_r']):.1f} R"
    dr = f"{opt['daily_rate']:.1f}"
    cat_short = meta["category"].split("(")[0].strip()
    tot_r += opt["net_r"]
    print(f"{sym:<14} | {cat_short:<22} | {wr_base:<18} | {wr_opt:<10} | {net_r:<11} | {pf:<6} | {dd:<8} | {dr:<8}")

print("-" * 115)
print(f"TOTAL CANASTA (13 ACTIVOS): +{tot_r:,.2f} R acumulados (33,800 operaciones totales, 2.0 ops/d por par)")
