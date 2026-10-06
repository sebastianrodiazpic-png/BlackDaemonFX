import os
import sys
import pickle
import pandas as pd

sys.path.insert(0, os.path.abspath("."))
from backtesting.historical_multibot_analysis import (
    HistoricalEngine, simulate_dual_leg_trade, compute_performance_metrics, SPREADS
)

def run_grid():
    with open("storage/analysis/signals_cache.pkl", "rb") as f:
        data = pickle.load(f)

    engine = HistoricalEngine(data_dir="data/historical")

    target_pairs = [
        (1.0, 2.0),
        (1.0, 2.5),
        (1.2, 2.5),
        (1.5, 2.5),
        (1.5, 3.0),
        (1.5, 3.5),
        (2.0, 3.0),
        (2.0, 3.5),
        (2.0, 4.0),
    ]

    selected_symbols = ["XAUUSD", "XAGUSD", "Wall Street 30", "US Tech 100"]

    results = []
    print("\n=== GRID DE OBJETIVOS (TP1 / TP2) ===")
    for rr1, rr2 in target_pairs:
        trades = []
        # Gold Cuartos Adaptive
        m5_gold = engine.loaded_data["XAUUSD"]["m5"]
        for sig in data["gq_signals_adaptive"]:
            t = simulate_dual_leg_trade(sig, m5_gold, SPREADS["XAUUSD"], rr_tp1=rr1, rr_tp2=rr2)
            if t: trades.append(t)
        # ORB
        for sym in selected_symbols:
            m5_s = engine.loaded_data[sym]["m5"]
            for sig in data["orb_signals_optimized"][sym]:
                t = simulate_dual_leg_trade(sig, m5_s, SPREADS.get(sym, 0.5), rr_tp1=rr1, rr_tp2=rr2)
                if t: trades.append(t)

        m = compute_performance_metrics(trades)
        results.append({
            "TP1_R": rr1,
            "TP2_R": rr2,
            "Trades": m["total_trades"],
            "WinRate%": m["win_rate_pct"],
            "Leg1_WR%": m["leg1_win_rate_pct"],
            "Leg2_WR%": m["leg2_win_rate_pct"],
            "Leg2_BE%": m["leg2_break_even_rate_pct"],
            "ProfitFactor": m["profit_factor"],
            "NetReturn%": m["net_return_pct"],
            "MaxDD%": m["max_drawdown_pct"],
            "Expectancy_R": m["expectancy_r"]
        })
        print(f"TP1={rr1}R | TP2={rr2}R -> WinRate={m['win_rate_pct']}% | Leg1_WR={m['leg1_win_rate_pct']}% | Leg2_WR={m['leg2_win_rate_pct']}% | Leg2_BE={m['leg2_break_even_rate_pct']}% | PF={m['profit_factor']} | NetReturn={m['net_return_pct']}% | MaxDD={m['max_drawdown_pct']}% | ExpR={m['expectancy_r']}")

    df_res = pd.DataFrame(results)
    df_res.to_csv("storage/analysis/target_grid_results.csv", index=False)
    print("\nSummary Table:")
    print(df_res.to_string(index=False))

if __name__ == "__main__":
    run_grid()
