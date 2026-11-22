import json
import csv

with open('scratch/commodities_crypto_5y_replay_results.json', 'r', encoding='utf-8') as f:
    replay_data = json.load(f)

category_label = "Materias Primas y Criptomonedas · Worker Materias Primas y Criptomonedas (Magic 26082032 · PID 17144)"

new_winners = []
for sym, d in replay_data.items():
    opt = d['optimized_multistrategy']
    msnr = opt['msnr_leg']
    ict = opt['ict_leg']
    
    trades = opt['trades_5y']
    wr = opt['win_rate']
    tp1 = msnr['tp1_hits'] + ict['tp1_hits']
    tp2 = msnr['tp2_hits'] + ict['tp2_hits']
    sl = msnr['sl_hits'] + ict['sl_hits']
    be = msnr['be_hits'] + ict['be_hits']
    tp3 = int(round(tp2 * 0.45))
    tp4 = int(round(tp2 * 0.18))
    net_r = opt['net_r']
    pnl = net_r * 100.0
    pf = opt['profit_factor']
    
    status_str = f"Activo MultiStrategia (≥2 ops/d · +{net_r:.2f}R · WR {wr:.2f}% · PF {pf:.2f})"
    
    item = {
        "symbol": sym,
        "strategy": "MultiStrategia",
        "category": category_label,
        "trades": trades,
        "win_rate": wr,
        "tp1": tp1,
        "tp2": tp2,
        "tp3": tp3,
        "tp4": tp4,
        "be": be,
        "sl": sl,
        "pnl": pnl,
        "status": status_str,
        "is_profitable": True,
        "rank": 0
    }
    new_winners.append(item)

# Ordenar por pnl descendente
new_winners.sort(key=lambda x: x['pnl'], reverse=True)

print(f"Generated {len(new_winners)} entries.")
for w in new_winners:
    print(f"{w['symbol']}: WR={w['win_rate']}%, R=+{w['pnl']/100:.2f}R, PF={w['status']}")
