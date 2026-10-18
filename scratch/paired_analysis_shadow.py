import sqlite3
import json
import pandas as pd
from pathlib import Path

db_path = Path("storage/runtime/shadow_research.sqlite3")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# 1. Obtener todas las señales de shadow_signals
cur.execute("""
    SELECT id, timestamp, strategy, variant, symbol, direction, entry_price, stop_loss,
           take_profit_1, mechanical_decision, rejection_reason, ai_probability,
           ai_threshold, ai_decision, final_action, simulated_outcome, simulated_rr
    FROM shadow_signals
    ORDER BY timestamp ASC, id ASC
""")
rows = [dict(r) for r in cur.fetchall()]
conn.close()

df = pd.DataFrame(rows)
print(f"Total registros individuales en shadow_signals: {len(df)}")

# 2. Análisis Pareado de Eventos de Mercado para ICT
df_ict = df[df['strategy'] == 'ICT'].copy()

# Definir la clave única del evento de mercado
df_ict['event_key'] = df_ict['timestamp'] + "_" + df_ict['symbol'] + "_" + df_ict['direction'] + "_" + df_ict['entry_price'].astype(str)

events = df_ict['event_key'].unique()
print(f"Total eventos de mercado únicos evaluados para ICT: {len(events)}")

paired_records = []
for ev in events:
    sub = df_ict[df_ict['event_key'] == ev]
    t = sub['timestamp'].iloc[0]
    sym = sub['symbol'].iloc[0]
    direction = sub['direction'].iloc[0]
    price = sub['entry_price'].iloc[0]
    ai_prob = sub['ai_probability'].iloc[0]
    
    # Extraer decision y resultado de cada variante
    var_map = {}
    for _, r in sub.iterrows():
        v = r['variant']
        var_map[v] = {
            'action': r['final_action'],
            'mech': r['mechanical_decision'],
            'rej_reason': r['rejection_reason'],
            'sim_outcome': r['simulated_outcome'],
            'sim_rr': r['simulated_rr']
        }
    
    paired_records.append({
        'event_key': ev,
        'timestamp': t,
        'symbol': sym,
        'direction': direction,
        'entry_price': price,
        'ai_prob': ai_prob,
        'base_action': var_map.get('base', {}).get('action'),
        'base_outcome': var_map.get('base', {}).get('sim_outcome'),
        'base_rr': var_map.get('base', {}).get('sim_rr', 0.0),
        'lock_930_action': var_map.get('lock_0700_0930', {}).get('action'),
        'lock_930_rej': var_map.get('lock_0700_0930', {}).get('rej_reason'),
        'lock_930_outcome': var_map.get('lock_0700_0930', {}).get('sim_outcome'),
        'lock_930_rr': var_map.get('lock_0700_0930', {}).get('sim_rr', 0.0),
        'lock_1000_action': var_map.get('lock_0700_1000', {}).get('action'),
        'lock_1000_rej': var_map.get('lock_0700_1000', {}).get('rej_reason'),
        'lock_1000_outcome': var_map.get('lock_0700_1000', {}).get('sim_outcome'),
        'lock_1000_rr': var_map.get('lock_0700_1000', {}).get('sim_rr', 0.0),
        'london_action': var_map.get('london_only', {}).get('action'),
        'london_rej': var_map.get('london_only', {}).get('rej_reason'),
        'london_outcome': var_map.get('london_only', {}).get('sim_outcome'),
        'london_rr': var_map.get('london_only', {}).get('sim_rr', 0.0),
    })

df_paired = pd.DataFrame(paired_records)
print("\n=== RESUMEN PAREADO DE EVENTOS ICT (Muestra de primeros 10 eventos) ===")
cols_show = ['timestamp', 'symbol', 'direction', 'base_action', 'base_outcome', 'base_rr', 
             'lock_930_action', 'lock_1000_action', 'london_action']
print(df_paired[cols_show].to_string())

# 3. Métricas pareadas agregadas para ICT
print("\n=== RESULTADOS AGREGADOS PAREADOS POR VARIANTE ICT ===")
print("Base:")
print(df_paired['base_action'].value_counts())
print(df_paired['base_outcome'].value_counts())
print("Total R Base:", df_paired['base_rr'].sum())

print("\nLock 07:00-09:30:")
print(df_paired['lock_930_action'].value_counts())
print(df_paired['lock_930_outcome'].value_counts())
print("Total R Lock 07:00-09:30:", df_paired['lock_930_rr'].sum())

print("\nLock 07:00-10:00:")
print(df_paired['lock_1000_action'].value_counts())
print(df_paired['lock_1000_outcome'].value_counts())
print("Total R Lock 07:00-10:00:", df_paired['lock_1000_rr'].sum())

print("\nLondon Only:")
print(df_paired['london_action'].value_counts())
print(df_paired['london_outcome'].value_counts())
print("Total R London Only:", df_paired['london_rr'].sum())

# 4. Análisis de Malaysian SNR
df_msnr = df[df['strategy'] == 'MSNR'].copy()
print("\n=== MALAYSIAN SNR: REGISTROS EN SHADOW ===")
print(df_msnr[['id', 'timestamp', 'variant', 'symbol', 'direction', 'mechanical_decision', 
               'rejection_reason', 'ai_probability', 'final_action', 'simulated_outcome', 'simulated_rr']].to_string())
