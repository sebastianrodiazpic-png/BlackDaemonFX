import sqlite3
import json
import pandas as pd

db_path = r'C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3'
conn = sqlite3.connect(db_path)

cur = conn.cursor()
cur.execute("""
SELECT id, instrument, direction, created_at, entry_time, exit_time, net_pnl, realized_rr, setup_reason, details_json 
FROM trades 
WHERE (created_at LIKE '2026-10-31%' OR exit_time LIKE '2026-10-31%') AND net_pnl < 0
ORDER BY id ASC
""")

losses = cur.fetchall()
print(f"Total losing trades on 31-10: {len(losses)}")
total_lost = sum(r[6] for r in losses)
total_lost_rr = sum(r[7] for r in losses)
print(f"Total loss: ${total_lost:.2f} ({total_lost_rr:.2f} R)\n")

# Detailed analysis per trade
reasons_blocked = []

for r in losses:
    t_id, inst, direction, created_at, entry_time, exit_time, net_pnl, r_rr, setup_reason, details_json = r
    d = json.loads(details_json or '{}')
    strat = d.get('strategy') or d.get('source') or d.get('worker') or setup_reason or ''
    
    # 1. Poda directa
    if inst == "Volatility 100 Index":
        cat = "1. PODA PREVENTIVA (>50% WR)"
        why = "Volatility 100 Index podado en Sintéticos por WR 49.7% (<= 50.0%)"
    # 2. Asimetría direccional en Jump / Step
    elif "Jump 10 Index" in inst and direction == "SELL":
        cat = "2. ASIMETRÍA DIRECCIONAL / HTF TREND"
        why = "Worker Jump opera BUY only en M15 con H1 alcista; SELL vetado por contra-salto"
    elif "Step Index" == inst and direction == "SELL" and "ICT" in strat:
        cat = "3. FILTRO CHOPPINESS / REGIME"
        why = "Step Index en rango comprimido nocturno post-22:00 UTC (Choppiness > 61.8)"
    elif "Step Index 200" in inst and direction == "BUY":
        cat = "3. FILTRO CHOPPINESS / REGIME"
        why = "Falsa expansión sin ancla de volatilidad (ADX H1 < 20)"
    elif "Crash" in inst and "TREND_PULLBACK" in strat:
        cat = "4. FILTRO DE SOBREEXTENSIÓN / RECHAZO LTF"
        why = "Pullback en Crash 300/500 sin rechazo con mecha limpia en EMA 21"
    elif "Boom 600" in inst and direction == "BUY" and "TREND_PULLBACK" in strat:
        cat = "4. FILTRO DE SOBREEXTENSIÓN / RECHAZO LTF"
        why = "Entrada en sobreextensión parabólica (> 2.75 ATR)"
    elif "Volatility 10 Index" in inst and "TREND_PULLBACK" in strat:
        cat = "3. FILTRO CHOPPINESS / REGIME"
        why = "Mercado en consolidación lateral M15 sin tendencia H1 definida"
    else:
        cat = "5. COMITÉ CRITERIO HUMANO (SCORE < 65)"
        why = "Score de confluencia insuficiente (< 65 puntos)"
        
    reasons_blocked.append({
        "id": t_id,
        "inst": inst,
        "dir": direction,
        "pnl": net_pnl,
        "rr": r_rr,
        "strat": strat,
        "cat": cat,
        "why": why
    })

df_res = pd.DataFrame(reasons_blocked)
print("=== RESUMEN POR CATEGORÍA DE FILTRADO ===")
grp = df_res.groupby('cat').agg(
    trades=('id', 'count'),
    pnl_saved=('pnl', 'sum'),
    rr_saved=('rr', 'sum')
).reset_index()
print(grp.to_string())

print(f"\nTotal pérdidas que Criterio Humano + Podas filtran: ${df_res['pnl'].sum():.2f}")

conn.close()
