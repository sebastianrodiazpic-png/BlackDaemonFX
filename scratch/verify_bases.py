"""
scratch/verify_bases.py
"""
import json
import re

with open("dashboard/strategy_bases_page.py", "r", encoding="utf-8") as f:
    text = f.read()

m_win = re.search(r"const WINNERS_DATA = (\[.*?\]);", text, re.DOTALL)
winners = json.loads(m_win.group(1))

m_los = re.search(r"const LOSERS_DATA = (\[.*?\]);", text, re.DOTALL)
losers = json.loads(m_los.group(1))

for sym in ["Boom 1000 Index", "Crash 300 Index"]:
    print(f"\n=== {sym} EN WINNERS_DATA ===")
    matches = [w for w in winners if w["symbol"] == sym]
    for w in matches:
        print(f"#{w['rank']} | {w['symbol']} | {w['strategy']} | Trades: {w['trades']} | WR: {w['win_rate']}% | TP1: {w['tp1']} | TP2: {w['tp2']} | TP3: {w['tp3']} | TP4: {w['tp4']} | BE: {w['be']} | PnL: +${w['pnl']:,.2f} | {w['status']}")
    
    los_matches = [l for l in losers if l["symbol"] == sym]
    if los_matches:
        print(f"=== {sym} EN LOSERS_DATA / SUGERENCIAS ===")
        for l in los_matches:
            print(f"- {l['symbol']} | {l['strategy']} | {l['status']} | Razón: {l['reason']}")
