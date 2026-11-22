import re
import json
import sqlite3
import pandas as pd

# 1. Parse WINNERS_DATA and LOSERS_DATA from strategy_bases_page.py
with open("dashboard/strategy_bases_page.py", "r", encoding="utf-8") as f:
    text = f.read()

# Extract WINNERS_DATA
match_winners = re.search(r"const WINNERS_DATA = (\[.*?\]);", text, re.DOTALL)
winners_data = []
if match_winners:
    raw_w = match_winners.group(1)
    # clean trailing commas before closing braces/brackets if any
    raw_w = re.sub(r",\s*([\]}])", r"\1", raw_w)
    try:
        winners_data = json.loads(raw_w)
    except Exception as e:
        print("JSON parse error winners:", e)
        # fallback regex extract
        pass

print(f"Total entries in WINNERS_DATA: {len(winners_data)}")

# 2. Get active instruments from /Instruments
p = r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3"
conn = sqlite3.connect(f"file:{p}?mode=ro", uri=True)

df_profiles = pd.read_sql_query("SELECT source, selection_profile, selected_symbols_json FROM instrument_selection_profile_preferences WHERE source='DEMO'", conn)
instruments_active = {}
for _, row in df_profiles.iterrows():
    prof = row['selection_profile']
    try:
        for s in json.loads(row['selected_symbols_json']):
            instruments_active.setdefault(s, set()).add(prof)
    except:
        pass

# 3. Get live trades from DB
df_trades = pd.read_sql_query("SELECT instrument, count(id) as live_trades, sum(case when result='WIN' or net_pnl > 0 then 1 else 0 end) as live_wins, sum(net_pnl) as live_pnl, max(entry_time) as last_trade FROM trades GROUP BY instrument", conn)
trades_dict = {row['instrument']: row for _, row in df_trades.iterrows()}
conn.close()

# 4. Compare by category / strategy
rows_comparison = []
for w in winners_data:
    sym = w.get("symbol")
    strat = w.get("strategy")
    bases_trades = w.get("trades", 0)
    bases_wr = w.get("win_rate", 0.0)
    bases_pnl = w.get("pnl", 0.0)
    
    in_instruments = sym in instruments_active
    active_profiles = list(instruments_active.get(sym, []))
    
    live_info = trades_dict.get(sym)
    live_cnt = live_info['live_trades'] if live_info is not None else 0
    live_wins = live_info['live_wins'] if live_info is not None else 0
    live_wr = round((live_wins / live_cnt) * 100.0, 1) if live_cnt > 0 else 0.0
    live_pnl = round(live_info['live_pnl'], 2) if live_info is not None and pd.notnull(live_info['live_pnl']) else 0.0
    last_tr = str(live_info['last_trade'])[:10] if live_info is not None and pd.notnull(live_info['last_trade']) else "-"
    
    rows_comparison.append({
        "symbol": sym,
        "strategy": strat,
        "bases_trades": bases_trades,
        "bases_wr": bases_wr,
        "bases_pnl": bases_pnl,
        "in_instruments": in_instruments,
        "profiles": ",".join(active_profiles[:2]),
        "live_trades": live_cnt,
        "live_wr": live_wr,
        "live_pnl": live_pnl,
        "last_trade": last_tr
    })

df_comp = pd.DataFrame(rows_comparison)
print(f"Comparados {len(df_comp)} pares de estrategia")

# Filter MultiStrategia
df_multi = df_comp[df_comp['strategy'] == 'MultiStrategia']
print("\n=== MULTIESTRATEGIA EN /Strategy-bases VS EN VIVO ===")
print(df_multi[['symbol', 'bases_trades', 'bases_wr', 'in_instruments', 'live_trades', 'live_wr', 'live_pnl', 'last_trade']].to_string())

# Save full comparison to CSV for easy inspection
df_comp.to_csv("scratch/comparison_bases_vs_live.csv", index=False)
print("\nGuardado en scratch/comparison_bases_vs_live.csv")
