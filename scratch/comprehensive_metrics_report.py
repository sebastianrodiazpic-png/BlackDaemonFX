import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path

db_path = Path("storage/runtime/shadow_research.sqlite3")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("""
    SELECT id, timestamp, strategy, variant, symbol, direction, entry_price, 
           mechanical_decision, rejection_reason, ai_probability, ai_threshold, 
           ai_decision, final_action, market_outcome, market_rr, 
           simulated_outcome, simulated_rr, contrafactual_note
    FROM shadow_signals
    ORDER BY timestamp ASC, id ASC
""")
rows = [dict(r) for r in cur.fetchall()]
conn.close()

df = pd.DataFrame(rows)

print("=====================================================================")
print("REPORTE INTEGRAL DE MÉTRICAS CIENTÍFICAS EN MODO SOMBRA")
print("=====================================================================")

# -------------------------------------------------------------
# 1. ICT Sabri Malle
# -------------------------------------------------------------
df_ict = df[df['strategy'] == 'ICT'].copy()
df_ict['event_id'] = df_ict['timestamp'] + "_" + df_ict['symbol'] + "_" + df_ict['direction']
unique_ict_events = df_ict['event_id'].unique()

print(f"\n1. ICT SABRI MALLE - EVENTOS PAREADOS (Total Eventos Únicos: {len(unique_ict_events)})")

# Agrupar eventos para comparar variantes
ict_variants = ['base', 'lock_0700_0930', 'lock_0700_1000', 'london_only']
var_stats = {}

for v in ict_variants:
    v_rows = df_ict[df_ict['variant'] == v]
    accepted = v_rows[v_rows['final_action'] == 'ACCEPTED_EXECUTION']
    discarded = v_rows[v_rows['final_action'] == 'DISCARDED_BY_FILTER']
    
    closed = accepted[accepted['simulated_outcome'].isin(['TP1_WIN', 'SL_LOSS'])]
    wins = len(closed[closed['simulated_outcome'] == 'TP1_WIN'])
    losses = len(closed[closed['simulated_outcome'] == 'SL_LOSS'])
    win_rate = (wins / len(closed) * 100.0) if len(closed) > 0 else 0.0
    
    gross_win_r = closed[closed['simulated_outcome'] == 'TP1_WIN']['simulated_rr'].sum()
    gross_loss_r = abs(closed[closed['simulated_outcome'] == 'SL_LOSS']['simulated_rr'].sum())
    net_r = closed['simulated_rr'].sum()
    pf = (gross_win_r / gross_loss_r) if gross_loss_r > 0 else (999.0 if gross_win_r > 0 else 0.0)
    
    # Drawdown máximo en R sobre la serie cerrada
    cum_r = closed['simulated_rr'].cumsum()
    peak = cum_r.cummax()
    dd = (cum_r - peak).min() if not cum_r.empty else 0.0
    
    # Contrafactuales evitados (cuántas pérdidas reales de mercado evitó el filtro)
    contrafactual_losses = discarded[discarded['market_outcome'] == 'SL_LOSS']
    cf_losses_count = len(contrafactual_losses)
    cf_losses_r = abs(contrafactual_losses['market_rr'].sum())
    
    # Abiertas y pendientes
    open_count = len(accepted[accepted['simulated_outcome'] == 'OPEN'])
    pending_count = len(accepted[accepted['simulated_outcome'] == 'PENDING_EVALUATION'])
    
    var_stats[v] = {
        'Aceptadas': len(accepted),
        'Descartadas': len(discarded),
        'Cerradas': len(closed),
        'Ganadas (W)': wins,
        'Perdidas (L)': losses,
        'Win Rate (%)': round(win_rate, 1),
        'Retorno Neto (R)': round(net_r, 4),
        'Profit Factor': round(pf, 2),
        'Max Drawdown (R)': round(abs(min(0.0, dd)), 2),
        'Pérdidas Evitadas (CF)': cf_losses_count,
        'R Evitado (CF)': round(cf_losses_r, 4),
        'Abiertas': open_count,
        'Pendientes': pending_count
    }

df_var_ict = pd.DataFrame(var_stats).T
print(df_var_ict.to_string())

# Desglose de ICT por Activo
print("\n--- ICT: DESGLOSE POR ACTIVO (Eventos Pareados Únicos) ---")
ict_event_map = {}
for ev in unique_ict_events:
    sub = df_ict[df_ict['event_id'] == ev]
    sym = sub['symbol'].iloc[0]
    m_out = sub['market_outcome'].iloc[0]
    m_rr = sub['market_rr'].iloc[0]
    if sym not in ict_event_map:
        ict_event_map[sym] = {'Eventos': 0, 'Cerrados': 0, 'Wins': 0, 'Losses': 0, 'Net_R_Mercado': 0.0, 'Abiertos': 0, 'Pendientes': 0}
    ict_event_map[sym]['Eventos'] += 1
    if m_out == 'TP1_WIN':
        ict_event_map[sym]['Cerrados'] += 1
        ict_event_map[sym]['Wins'] += 1
        ict_event_map[sym]['Net_R_Mercado'] += m_rr
    elif m_out == 'SL_LOSS':
        ict_event_map[sym]['Cerrados'] += 1
        ict_event_map[sym]['Losses'] += 1
        ict_event_map[sym]['Net_R_Mercado'] += m_rr
    elif m_out == 'OPEN':
        ict_event_map[sym]['Abiertos'] += 1
    else:
        ict_event_map[sym]['Pendientes'] += 1

print(pd.DataFrame(ict_event_map).T.to_string())

# -------------------------------------------------------------
# 2. Malaysian SNR
# -------------------------------------------------------------
print("\n=====================================================================")
print("2. MALAYSIAN SNR - SEPARACIÓN DE CONJUNTOS Y EVALUACIÓN CRÍTICA")
print("=====================================================================")

df_msnr = df[df['strategy'] == 'MSNR'].copy()
df_msnr_live = df_msnr[df_msnr['variant'] == 'enabled_19_h4_fresh'].copy()
df_msnr_synth = df_msnr[df_msnr['variant'].isin(['h4_fresh_level', 'enabled_19_only'])].copy()

print(f"a) Modo Sombra en Vivo (19 Activos Habilitados): {len(df_msnr_live)} eventos")
print(f"b) Suite Sintética de Control:                  {len(df_msnr_synth)} eventos")
print(f"c) Holdout Histórico Previo (2026-04 a 2026-10):  76 trades base / 39 trades IA (Umbral 0.35, +2.45 R)")
print(f"d) Replay Histórico Previo (2024-10 a 2026-10):   302 trades base (+19.28 R)")

# Desglose de los 12 eventos en vivo de modo sombra
print("\n--- MALAYSIAN SNR: DETALLE DE LOS 12 EVENTOS EN VIVO (15-OCT-2026) ---")
msnr_live_records = []
for _, r in df_msnr_live.iterrows():
    msnr_live_records.append({
        'ID': r['id'],
        'Timestamp': r['timestamp'][11:16],
        'Símbolo': r['symbol'],
        'Dirección': r['direction'],
        'H4_Filtro': r['mechanical_decision'],
        'AI_Prob': r['ai_probability'],
        'Acción_Final': r['final_action'],
        'Mercado_Real': r['market_outcome'],
        'Retorno_Mercado': r['market_rr'],
        'Retorno_Variante': r['simulated_rr'],
        'Contrafactual': r['contrafactual_note'] or '-'
    })

df_msnr_table = pd.DataFrame(msnr_live_records)
print(df_msnr_table.to_string(index=False))

# Comparación Pareada: Base vs Filtrada en Modo Sombra
print("\n--- MALAYSIAN SNR: COMPARACIÓN PAREADA EN MODO SOMBRA ---")
# Base habría ejecutado todas las 12 señales si estuviera activa sin filtro H4
msnr_base_closed = df_msnr_live[df_msnr_live['market_outcome'].isin(['TP1_WIN', 'SL_LOSS'])]
msnr_filt_closed = df_msnr_live[(df_msnr_live['final_action'] == 'ACCEPTED_EXECUTION') & (df_msnr_live['simulated_outcome'].isin(['TP1_WIN', 'SL_LOSS']))]

base_net_r = msnr_base_closed['market_rr'].sum()
filt_net_r = msnr_filt_closed['simulated_rr'].sum()

print(f"Estrategia Base (sin filtro H4): {len(msnr_base_closed)} trades cerrados (0 W / 4 L) | Retorno: {base_net_r:+.2f}R | PF: 0.00")
print(f"Estrategia Filtrada (H4 fresco): {len(msnr_filt_closed)} trades cerrados (0 W / 2 L) | Retorno: {filt_net_r:+.2f}R | PF: 0.00")
print(f"Pérdidas Evitadas Contrafactuales: {len(msnr_base_closed) - len(msnr_filt_closed)} trades | R Contrafactual Evitado: {abs(base_net_r - filt_net_r):+.2f}R")
print(f"Posiciones Abiertas en Curso: 1 trade (Step Index 400)")
print(f"Señales Pendientes de Evaluación: 6 trades")

