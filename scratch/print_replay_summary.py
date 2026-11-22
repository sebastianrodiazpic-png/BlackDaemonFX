import json

with open('scratch/commodities_crypto_5y_replay_results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for sym, stats in data.items():
    print(f"{sym}: trades={stats['trades']}, wr={stats['win_rate']}%, net_r={stats['net_r']}, pf={stats['profit_factor']}")
