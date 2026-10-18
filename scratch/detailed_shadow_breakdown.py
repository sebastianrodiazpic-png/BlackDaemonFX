import sqlite3
import pandas as pd
from pathlib import Path

db_path = Path("storage/runtime/shadow_research.sqlite3")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("""
    SELECT id, timestamp, strategy, variant, symbol, direction, entry_price, 
           mechanical_decision, rejection_reason, ai_probability, ai_decision,
           final_action, simulated_outcome, simulated_rr
    FROM shadow_signals
    ORDER BY timestamp ASC, id ASC
""")
rows = [dict(r) for r in cur.fetchall()]
conn.close()

df = pd.DataFrame(rows)

print("=====================================================================")
print("DESGLOSE CIENTÍFICO DE SEÑALES EN MODO SOMBRA (SHADOW RESEARCH)")
print("=====================================================================")

# 1. Total evaluaciones
print(f"Total registros en DB: {len(df)}")
print("\n--- DISTRIBUCIÓN POR ACCIÓN FINAL ---")
print(df['final_action'].value_counts())

# 2. Análisis por Variante ICT
print("\n=====================================================================")
print("ICT: ANÁLISIS DE LAS 4 VARIANTES SOBRE EVENTOS DE MERCADO PAREADOS")
print("=====================================================================")
df_ict = df[df['strategy'] == 'ICT'].copy()

# Eventos de mercado únicos
df_ict['event_id'] = df_ict['timestamp'] + " | " + df_ict['symbol'] + " | " + df_ict['direction']
unique_events = df_ict['event_id'].unique()
print(f"Eventos de mercado únicos observados para ICT: {len(unique_events)}")

# Para cada evento, ver qué pasó en cada variante
records = []
for ev in unique_events:
    sub = df_ict[df_ict['event_id'] == ev]
    t = sub['timestamp'].iloc[0]
    sym = sub['symbol'].iloc[0]
    direction = sub['direction'].iloc[0]
    
    # Determinar el resultado de mercado a partir de lo observado
    # (si alguna variante o la base lo tiene registrado)
    market_outcome = "PENDING"
    market_rr = 0.0
    for _, r in sub.iterrows():
        if r['simulated_outcome'] in ['TP1_WIN', 'SL_LOSS', 'BE', 'CLOSED_OTHER']:
            market_outcome = r['simulated_outcome']
            market_rr = r['simulated_rr']
            break
        elif r['simulated_outcome'] == 'SIMULATED_OPEN':
            market_outcome = 'OPEN'
            market_rr = 0.0

    # Analizar cada variante
    row_dict = {
        'event': ev,
        'timestamp': t,
        'symbol': sym,
        'direction': direction,
        'market_outcome': market_outcome,
        'market_rr': market_rr
    }
    for v in ['base', 'lock_0700_0930', 'lock_0700_1000', 'london_only']:
        v_sub = sub[sub['variant'] == v]
        if not v_sub.empty:
            act = v_sub['final_action'].iloc[0]
            rej = v_sub['rejection_reason'].iloc[0]
            # Si fue aceptada, su resultado es el del mercado. Si fue descartada, es 0.0 R
            if act == 'ACCEPTED_EXECUTION':
                v_rr = market_rr if market_outcome in ['TP1_WIN', 'SL_LOSS', 'BE'] else 0.0
                status = market_outcome
            else:
                v_rr = 0.0
                status = f"DESCARTADO ({rej})"
            row_dict[f'{v}_action'] = act
            row_dict[f'{v}_status'] = status
            row_dict[f'{v}_rr'] = v_rr
        else:
            row_dict[f'{v}_action'] = 'NO_DATA'
            row_dict[f'{v}_status'] = 'NO_DATA'
            row_dict[f'{v}_rr'] = 0.0
    records.append(row_dict)

df_ev = pd.DataFrame(records)

print("\n--- MATRIZ DE EVENTOS PAREADOS DE ICT ---")
for idx, r in df_ev.iterrows():
    print(f"Evento #{idx+1:02d}: {r['timestamp']} | {r['symbol']} {r['direction']} | Mercado: {r['market_outcome']} ({r['market_rr']:+.2f}R)")
    print(f"   Base: {r['base_action']} -> {r['base_rr']:+.2f}R")
    print(f"   Lock 0700-0930: {r['lock_0700_0930_action']} -> {r['lock_0700_0930_rr']:+.2f}R [{r['lock_0700_0930_status']}]")
    print(f"   Lock 0700-1000: {r['lock_0700_1000_action']} -> {r['lock_0700_1000_rr']:+.2f}R [{r['lock_0700_1000_status']}]")
    print(f"   London Only:    {r['london_only_action']} -> {r['london_only_rr']:+.2f}R [{r['london_only_status']}]")
    print("-" * 65)

print("\n--- RESUMEN CONSOLIDADO POR VARIANTE ICT ---")
for v in ['base', 'lock_0700_0930', 'lock_0700_1000', 'london_only']:
    tot_accepted = sum(df_ev[f'{v}_action'] == 'ACCEPTED_EXECUTION')
    tot_discarded = sum(df_ev[f'{v}_action'] == 'DISCARDED_BY_FILTER')
    tot_rr = df_ev[f'{v}_rr'].sum()
    closed_trades = df_ev[(df_ev[f'{v}_action'] == 'ACCEPTED_EXECUTION') & (df_ev['market_outcome'].isin(['TP1_WIN', 'SL_LOSS']))]
    wins = sum(closed_trades['market_outcome'] == 'TP1_WIN')
    losses = sum(closed_trades['market_outcome'] == 'SL_LOSS')
    pf = (closed_trades[closed_trades['market_outcome'] == 'TP1_WIN']['market_rr'].sum() / 
          abs(closed_trades[closed_trades['market_outcome'] == 'SL_LOSS']['market_rr'].sum())) if losses > 0 else 999.0
    print(f"Variante {v:18s}: Aceptadas={tot_accepted:2d}, Descartadas={tot_discarded:2d} | Cerradas={len(closed_trades):2d} (W:{wins}, L:{losses}) | Net R={tot_rr:+.2f}R | PF={pf:.2f}")

print("\n=====================================================================")
print("MALAYSIAN SNR: RESUMEN DE SEÑALES, FILTROS Y RESULTADOS OBSERVADOS")
print("=====================================================================")
df_msnr = df[df['strategy'] == 'MSNR'].copy()
for idx, r in df_msnr.iterrows():
    print(f"Señal #{r['id']:02d} | {r['timestamp']} | {r['symbol']:16s} {r['direction']:4s} | H4/Universo: {r['mechanical_decision']} ({r['rejection_reason']}) | AI: {r['ai_probability']:.2f} | Acción: {r['final_action']} | Simulado: {r['simulated_outcome']} ({r['simulated_rr']:+.2f}R)")

