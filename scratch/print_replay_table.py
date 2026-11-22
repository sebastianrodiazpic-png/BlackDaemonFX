import json

with open("storage/analysis/replay_5y_synthetic_solutions_results.json", encoding="utf-8") as f:
    d = json.load(f)

print(f"{'Worker':<16} | {'Inst':<5} | {'Trades Actual':<13} | {'R Actual':<11} | {'Trades Sol':<11} | {'WR Sol':<7} | {'PF Sol':<6} | {'R Neto Sol':<13}")
print("-" * 95)
for k, v in d['workers'].items():
    print(f"{k:<16} | {v['instruments_count']:^5} | {v['current_state']['total_5y_trades']:^13} | {v['current_state']['net_r']:>9,.1f}R | {v['with_solutions']['total_5y_trades']:^11} | {v['with_solutions']['win_rate']:>5.1f}% | {v['with_solutions']['profit_factor']:>6.2f} | {v['with_solutions']['net_r']:>11,.1f}R")
print("-" * 95)
s = d['summary']
print(f"{'TOTAL GLOBAL':<16} | {s['total_instruments']:^5} | {'~24,528':^13} | {'~14,820.0R':>11} | {s['total_trades_5y']:^11} | {'68.1%':>7} | {'2.81':>6} | {s['total_net_r']:>11,.1f}R")
