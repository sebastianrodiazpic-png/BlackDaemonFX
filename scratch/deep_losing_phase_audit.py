import sqlite3
import json
import pandas as pd
import numpy as np

db_path = r'C:/Users/sebas/AppData/Local/BlackDaemonFx/trading_bot.sqlite3'
conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)

# 1. Total trades by date (last 10 days)
q_by_date = """
SELECT date(entry_time) as trade_date,
       count(*) as total_trades,
       sum(case when result = 'WIN' or net_pnl > 0 then 1 else 0 end) as wins,
       sum(case when result = 'LOSS' or net_pnl < 0 then 1 else 0 end) as losses,
       sum(case when result = 'BREAK_EVEN' or net_pnl = 0 then 1 else 0 end) as be,
       round(sum(net_pnl), 2) as total_pnl,
       round(avg(realized_rr), 3) as avg_realized_rr
FROM trades
WHERE status = 'CLOSED'
GROUP BY trade_date
ORDER BY trade_date DESC
LIMIT 15
"""
df_date = pd.read_sql_query(q_by_date, conn)
print("=== DESGLOSE DIARIO DE OPERACIONES ===")
print(df_date.to_string(index=False))

# 2. Performance by Strategy (recent period)
q_strat = """
SELECT 
    case 
        when setup_reason like '%TREND_PULLBACK%' then 'TREND_PULLBACK'
        when setup_reason like '%MALAYSIAN_SNR%' or setup_reason like '%MSNR%' then 'MALAYSIAN_SNR'
        when setup_reason like '%ORB%' then 'ORB'
        when setup_reason like '%ICT%' or setup_reason like '%SMC%' then 'ICT_SMC'
        when setup_reason like '%RSI2%' then 'CONNORS_RSI2'
        when setup_reason like '%CARRY%' then 'FX_CARRY'
        else 'OTHER'
    end as strategy,
    count(*) as total_ops,
    sum(case when net_pnl > 0 then 1 else 0 end) as wins,
    sum(case when net_pnl < 0 then 1 else 0 end) as losses,
    round(100.0 * sum(case when net_pnl > 0 then 1 else 0 end) / count(*), 1) as win_rate_pct,
    round(sum(net_pnl), 2) as total_net_pnl,
    round(avg(realized_rr), 3) as avg_realized_rr
FROM trades
WHERE status = 'CLOSED' AND entry_time >= '2026-10-28'
GROUP BY strategy
ORDER BY total_net_pnl ASC
"""
df_strat = pd.read_sql_query(q_strat, conn)
print("\n=== RENDIMIENTO POR ESTRATEGIA (DESDE 28-OCT) ===")
print(df_strat.to_string(index=False))

# 3. Performance by Instrument (recent period)
q_inst = """
SELECT instrument,
       count(*) as total,
       sum(case when net_pnl > 0 then 1 else 0 end) as wins,
       sum(case when net_pnl < 0 then 1 else 0 end) as losses,
       round(100.0 * sum(case when net_pnl > 0 then 1 else 0 end) / count(*), 1) as win_rate,
       round(sum(net_pnl), 2) as total_pnl,
       round(avg(realized_rr), 3) as avg_rr
FROM trades
WHERE status = 'CLOSED' AND entry_time >= '2026-10-28'
GROUP BY instrument
ORDER BY total_pnl ASC
LIMIT 20
"""
df_inst = pd.read_sql_query(q_inst, conn)
print("\n=== PEORES INSTRUMENTOS EN FASE RECIENTE (DESDE 28-OCT) ===")
print(df_inst.to_string(index=False))

# 4. Exit reason analysis
q_exit = """
SELECT exit_reason,
       count(*) as count,
       round(sum(net_pnl), 2) as total_pnl,
       round(avg(realized_rr), 3) as avg_rr
FROM trades
WHERE status = 'CLOSED' AND entry_time >= '2026-10-28'
GROUP BY exit_reason
ORDER BY count DESC
"""
df_exit = pd.read_sql_query(q_exit, conn)
print("\n=== MOTIVOS DE SALIDA (EXIT REASONS) ===")
print(df_exit.to_string(index=False))

# 5. Detailed inspection of last 20 losses
q_losses = """
SELECT id, instrument, direction, entry_time, exit_time, entry_price, stop_loss, exit_price,
       planned_rr, realized_rr, net_pnl, exit_reason, setup_reason, details_json
FROM trades
WHERE status = 'CLOSED' AND net_pnl < 0
ORDER BY id DESC
LIMIT 20
"""
cur = conn.cursor()
cur.execute(q_losses)
loss_rows = cur.fetchall()

print(f"\n=== ANÁLISIS DETALLADO DE LAS ÚLTIMAS {len(loss_rows)} PÉRDIDAS ===")
mfe_list = []
hc_scores = []
hc_grades = []
hc_actions = []

for r in loss_rows:
    tid, sym, direct, t_in, t_out, p_in, sl, p_out, p_rr, r_rr, pnl, exit_r, setup_r, d_json = r
    
    mfe = None
    mae = None
    hc_data = None
    if d_json:
        try:
            d = json.loads(d_json)
            mfe = d.get('max_favorable_excursion_rr')
            mae = d.get('max_adverse_excursion_rr')
            # Look for human criteria
            meta = d.get('metadata') or {}
            hc_data = meta.get('human_criteria') or d.get('human_criteria')
        except Exception:
            pass
            
    if mfe is not None:
        mfe_list.append(mfe)
    if hc_data:
        hc_scores.append(hc_data.get('score'))
        hc_grades.append(hc_data.get('grade'))
        hc_actions.append(hc_data.get('action'))
        
    strat_short = setup_r.split('|')[0].strip() if setup_r else 'UNKNOWN'
    print(f"ID {tid} | {sym} {direct} | Strat: {strat_short} | PnL: {pnl:.2f} | R: {r_rr:.2f} | Exit: {exit_r} | MFE: {mfe}R | In: {t_in} -> Out: {t_out}")
    if hc_data:
        print(f"   -> HumanCriteria: Score={hc_data.get('score')} | Grade={hc_data.get('grade')} | Action={hc_data.get('action')} | Reason={hc_data.get('reason')}")

if mfe_list:
    print(f"\nMFE promedio en trades perdedores: {np.mean(mfe_list):.3f}R")
    high_mfe = [x for x in mfe_list if x >= 0.70]
    print(f"Trades perdedores que llegaron a >= +0.70R antes de perderse: {len(high_mfe)} de {len(mfe_list)} ({100*len(high_mfe)/len(mfe_list):.1f}%)")
    very_high = [x for x in mfe_list if x >= 0.90]
    print(f"Trades perdedores que llegaron a >= +0.90R (a milímetros de TP1) antes de perderse: {len(very_high)} de {len(mfe_list)} ({100*len(very_high)/len(mfe_list):.1f}%)")

print("\nAuditoría inicial completada.")
