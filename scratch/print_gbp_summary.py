import json

with open("scratch/gbp_5y_replay_results.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print("| Instrumento | Categoría | ADR (pips) | Spread (pips) | Trades 5A | Trades/Día | Win Rate % | Profit Factor | Net R (5A) | Ganancia USD ($100/R) |")
print("|---|---|---|---|---|---|---|---|---|---|")

tot_trades = 0
tot_r = 0.0

for sym, info in data.items():
    meta = info["metadata"]
    opt = info["optimized_multistrategy"]
    tot_trades += opt["trades_5y"]
    tot_r += opt["net_r"]
    cat = meta["category"].split("(")[0].strip()
    adr = meta["avg_daily_range_pips"]
    sp = meta["spread_pips"]
    tr = opt["trades_5y"]
    dr = opt["daily_rate"]
    wr = opt["win_rate"]
    pf = opt["profit_factor"]
    nr = opt["net_r"]
    usd = opt["projected_usd_profit_100_per_r"]
    print(f"| **{sym}** | {cat} | {adr:.0f} | {sp:.1f} | {tr:,} | {dr:.1f} | {wr:.2f}% | {pf:.2f} | +{nr:,.2f} R | +${usd:,.2f} |")

print(f"\nTOTAL GLOBAL: {tot_trades:,} operaciones | +{tot_r:,.2f} R netos acumulados | +${tot_r*100:,.2f} USD")
