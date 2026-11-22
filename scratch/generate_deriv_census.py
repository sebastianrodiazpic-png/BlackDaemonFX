import sqlite3
import pandas as pd
import json

# 1. Load 5Y Replay results from storage/analysis/tabla_comparativa_todos_instrumentos_tripartita_5y.csv
df_5y = pd.read_csv('storage/analysis/tabla_comparativa_todos_instrumentos_tripartita_5y.csv')

# 2. Load live DB trades
p = r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3"
conn = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
df_live = pd.read_sql_query("""
    SELECT instrument, 
           count(id) as live_trades, 
           sum(case when result='WIN' or net_pnl > 0 then 1 else 0 end) as live_wins, 
           sum(net_pnl) as live_pnl
    FROM trades 
    GROUP BY instrument
""", conn)
conn.close()

live_map = {row['instrument']: row for _, row in df_live.iterrows()}

# 3. Aggregate 5Y results by symbol (weighted by trades across strategies)
symbols_5y = {}
for _, r in df_5y.iterrows():
    sym = r['symbol']
    strat = r['strategy']
    cat = r['category']
    t = r['trades_despues']
    w = r['wins_despues']
    net_r = r['r_neto_despues']
    dec = r['decision']
    status = r['status_despues']
    
    if sym not in symbols_5y:
        symbols_5y[sym] = {
            "symbol": sym,
            "category": cat,
            "total_5y_trades": 0,
            "total_5y_wins": 0,
            "total_5y_r": 0.0,
            "strategies_profitable": 0,
            "strategies_tested": 0,
            "primary_decision": status
        }
    
    if t > 0:
        symbols_5y[sym]["total_5y_trades"] += t
        symbols_5y[sym]["total_5y_wins"] += w
        symbols_5y[sym]["total_5y_r"] += net_r
        symbols_5y[sym]["strategies_tested"] += 1
        if net_r > 0 and (w / t) >= 0.50:
            symbols_5y[sym]["strategies_profitable"] += 1

# Calculate aggregated WR
aggregated_list = []
for sym, data in symbols_5y.items():
    tot_t = data["total_5y_trades"]
    tot_w = data["total_5y_wins"]
    wr_5y = round((tot_w / tot_t) * 100.0, 1) if tot_t > 0 else 0.0
    r_5y = round(data["total_5y_r"], 1)
    
    # live stats
    live = live_map.get(sym)
    l_trades = live['live_trades'] if live is not None else 0
    l_wins = live['live_wins'] if live is not None else 0
    l_wr = round((l_wins / l_trades) * 100.0, 1) if l_trades > 0 else 0.0
    l_pnl = round(live['live_pnl'], 2) if live is not None and pd.notnull(live['live_pnl']) else 0.0
    
    # Classification rule
    # Grupo A: Rentable (WR 5Y >= 55% y R 5Y > 50R y (l_pnl >= -50 o l_trades < 10 o l_pnl > 0))
    # Grupo B: Podar (WR 5Y < 50% o R 5Y <= 0 o spread excesivo o l_pnl < -200 con WR < 45%)
    # Grupo C: Candidato a Desbloquear / Alta Convicción (WR 5Y > 58% y l_trades < 5)
    
    if wr_5y < 50.0 or r_5y <= 0.0 or (l_trades >= 30 and l_wr < 42.0 and l_pnl < -200):
        action = "PODAR"
        reason = f"Expectativa negativa (WR 5Y {wr_5y}%, {r_5y}R)" if r_5y <= 0 else f"Destrucción en vivo ({l_trades} trades, {l_wr}% WR, {l_pnl} USD)"
    elif l_trades <= 3 and wr_5y >= 58.0 and r_5y > 100.0:
        action = "DESBLOQUEAR_ALTA_CONVICCION"
        reason = f"Excelente potencial 5Y ({wr_5y}% WR, +{r_5y}R) pero sin trades en vivo ({l_trades} ops)"
    else:
        action = "DEJAR_ACTIVO_RENTABLE"
        reason = f"Rentable confirmado ({wr_5y}% WR 5Y, +{r_5y}R)"
    
    aggregated_list.append({
        "symbol": sym,
        "category": data["category"],
        "action": action,
        "wr_5y": wr_5y,
        "r_5y": r_5y,
        "trades_5y": tot_t,
        "live_trades": l_trades,
        "live_wr": l_wr,
        "live_pnl": l_pnl,
        "reason": reason
    })

df_all = pd.DataFrame(aggregated_list)
print("=== RESUMEN POR ACCIÓN RECOMENDADA ===")
print(df_all['action'].value_counts())

print("\n--- GRUPO: DESBLOQUEAR ALTA CONVICCIÓN ---")
print(df_all[df_all['action'] == 'DESBLOQUEAR_ALTA_CONVICCION'][['symbol', 'category', 'wr_5y', 'r_5y', 'live_trades', 'reason']].to_string())

print("\n--- TOP PODAR (PEORES CASOS) ---")
print(df_all[df_all['action'] == 'PODAR'].sort_values(by="r_5y")[['symbol', 'category', 'wr_5y', 'r_5y', 'live_trades', 'live_pnl', 'reason']].head(20).to_string())

print("\n--- TOP DEJAR ACTIVOS RENTABLES ---")
print(df_all[df_all['action'] == 'DEJAR_ACTIVO_RENTABLE'].sort_values(by="r_5y", ascending=False)[['symbol', 'category', 'wr_5y', 'r_5y', 'live_trades', 'live_wr', 'live_pnl']].head(20).to_string())

df_all.to_csv("scratch/censo_completo_activos_deriv.csv", index=False)
print("\nGuardado censo en scratch/censo_completo_activos_deriv.csv")
