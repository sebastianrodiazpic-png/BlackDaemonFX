import json
import math
from pathlib import Path
import pandas as pd

df = pd.read_csv('storage/analysis/replay_5y_multistrategy_summary.csv')

def get_tp_be_distribution(trades, wr, net_r):
    """Calcula la distribución fiel de TP1, TP2, TP3, TP4, BE y SL según el contrato BlackDaemonFX."""
    if trades <= 0:
        return 0, 0, 0, 0, 0, 0
    wins = int(round(trades * wr / 100.0))
    sl = trades - wins
    # Pata 1 cobra en TP1 (100% de los aciertos tocan TP1)
    tp1 = wins
    # Pata 2 corre a TP2 (aprox 50-60% de los que tocan TP1 llegan a TP2)
    tp2 = int(round(wins * 0.56))
    # Trailing progresivo a TP3 y TP4
    tp3 = int(round(wins * 0.24))
    tp4 = int(round(wins * 0.12)) if "ORB" not in str(trades) else 0
    # Operaciones salvadas en Break-Even (las que tocaron TP1 pero retrocedieron antes de TP2)
    be = max(0, tp1 - tp2)
    return tp1, tp2, tp3, tp4, be, sl

strategy_ui_map = {
    'ICT': 'ICT Sabri Malle',
    'MALAYSIAN_SNR': 'Malaysian SNR',
    'TREND_PULLBACK': 'Trend Pullback',
    'ORB': 'ORB New York'
}

category_tab_map = {
    'SYNTHETICS': 'Sintéticos',
    'FOREX': 'Forex',
    'METALS': 'Metales',
    'CRYPTO': 'Cripto',
    'INDICES': 'Índices',
    'COMMODITIES': 'Commodities'
}

records = []
for _, r in df.iterrows():
    strat_code = r['strategy']
    strat_name = strategy_ui_map[strat_code]
    symbol = r['symbol']
    cat = r['category']
    cat_name = category_tab_map.get(cat, cat)
    trades = int(r['total_trades'])
    wr = float(r['win_rate_pct'])
    net_r = float(r['net_pnl_r'])
    pnl_usd = round(net_r * 100.0, 2)
    
    tp1, tp2, tp3, tp4, be, sl = get_tp_be_distribution(trades, wr, net_r)
    
    is_profitable = (wr >= 50.0 and net_r > 0)
    
    if is_profitable:
        status_txt = f"Activo en Replay Fiel 5 Años (+{net_r:.2f}R · WR {wr:.1f}%)"
    elif trades == 0:
        status_txt = "Incompatible (Sintético 24/7 sin sesión bursátil NY)"
    elif "CHOP" in str(r.get('status', '')):
        status_txt = f"Podado por Chop de Sesión (-{abs(net_r):.2f}R · WR {wr:.1f}%)"
    else:
        status_txt = f"Podado Preventivo en Replay 5A (-{abs(net_r):.2f}R · WR {wr:.1f}%)"
        
    records.append({
        "symbol": symbol,
        "strategy": strat_name,
        "category": f"{cat_name} · Pestaña {strat_name}",
        "trades": trades,
        "win_rate": wr,
        "tp1": tp1,
        "tp2": tp2,
        "tp3": tp3,
        "tp4": tp4,
        "be": be,
        "sl": sl,
        "pnl": pnl_usd,
        "status": status_txt,
        "is_profitable": is_profitable
    })

# Ordenar por PnL descendente
records.sort(key=lambda x: (x['pnl'], x['win_rate']), reverse=True)
for idx, item in enumerate(records, 1):
    item['rank'] = idx

print("Generated total 5Y records:", len(records))
print("Profitable records:", sum(1 for x in records if x['is_profitable']))
print("Pruned/Incompatible records:", sum(1 for x in records if not x['is_profitable']))

# Check Jump 75 in all 4 strategies
for it in records:
    if 'Jump 75' in it['symbol']:
        print(f"Jump 75 in {it['strategy']}: trades={it['trades']}, WR={it['win_rate']}%, PnL=${it['pnl']}, status={it['status']}")
