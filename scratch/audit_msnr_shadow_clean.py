import sqlite3
import pandas as pd
from pathlib import Path

db_path = Path("storage/runtime/shadow_research.sqlite3")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("""
    SELECT id, timestamp, variant, symbol, direction, entry_price, stop_loss, take_profit_1,
           mechanical_decision, rejection_reason, ai_probability, ai_threshold,
           ai_decision, final_action, simulated_outcome, simulated_rr
    FROM shadow_signals
    WHERE strategy = 'MSNR'
    ORDER BY timestamp ASC, id ASC
""")
msnr_rows = [dict(r) for r in cur.fetchall()]
conn.close()

df_msnr = pd.DataFrame(msnr_rows)
print("=====================================================================")
print("AUDITORÍA EXCLUSIVA DE MALAYSIAN SNR EN MODO SOMBRA")
print("=====================================================================")
print(f"Total registros MSNR en shadow_signals: {len(df_msnr)}")

# Clasificar suite sintética vs eventos en vivo
# La suite sintética usó timestamp fijo 2026-10-15T14:00:00 con variantes 'h4_fresh_level' y 'enabled_19_only'
df_live_shadow = df_msnr[df_msnr['variant'] == 'enabled_19_h4_fresh'].copy()
df_synthetic = df_msnr[df_msnr['variant'].isin(['h4_fresh_level', 'enabled_19_only'])].copy()

print(f"\n1. Eventos observados en vivo en modo sombra: {len(df_live_shadow)}")
print(f"2. Eventos de la suite sintética de verificación: {len(df_synthetic)}")

print("\n--- DETALLE DE LOS EVENTOS OBSERVADOS EN VIVO (19 ACTIVOS HABILITADOS) ---")
for idx, r in df_live_shadow.iterrows():
    print(f"ID #{r['id']:02d} | {r['timestamp']} | {r['symbol']:16s} {r['direction']:4s} | "
          f"Mecánico: {r['mechanical_decision']:8s} ({r['rejection_reason']}) | "
          f"AI Prob: {r['ai_probability']:.2f} (Th: {r['ai_threshold']}) | "
          f"Acción Final: {r['final_action']:20s} | "
          f"Simulado: {r['simulated_outcome']} ({r['simulated_rr']:+.2f}R)")

# Contabilizar estados
completed = df_live_shadow[df_live_shadow['simulated_outcome'].isin(['TP1_WIN', 'SL_LOSS', 'BE'])]
open_pos = df_live_shadow[df_live_shadow['simulated_outcome'] == 'SIMULATED_OPEN']
pending = df_live_shadow[df_live_shadow['simulated_outcome'] == 'PENDING_EVALUATION']
closed_other = df_live_shadow[df_live_shadow['simulated_outcome'] == 'CLOSED_OTHER']

print(f"\n--- ESTADO DE LOS EVENTOS EN VIVO ---")
print(f"  - Completados (cerrados): {len(completed)}")
print(f"  - Abiertos (en curso):    {len(open_pos)}")
print(f"  - Pendientes evaluación:  {len(pending)}")
print(f"  - Otros / Slippage:       {len(closed_other)}")

# Comparación Pareada sobre los eventos en vivo: Base vs Filtrada
# La base habría ejecutado todas las señales que son del universo habilitado
# La filtrada solo ejecuta si H4 fresco (mitigaciones < 2) y AI prob >= 0.35
print("\n--- COMPARACIÓN PAREADA: BASE VS FILTRADA EN SOMBRA ---")
base_r = 0.0
filtered_r = 0.0
base_trades = 0
filtered_trades = 0

for idx, r in df_live_shadow.iterrows():
    out = r['simulated_outcome']
    rr = r['simulated_rr']
    act = r['final_action']
    
    # En la base: se habría tomado todo lo que cerró
    if out in ['TP1_WIN', 'SL_LOSS']:
        base_r += rr
        base_trades += 1
    
    # En la filtrada: solo se toma si fue ACCEPTED_EXECUTION
    if act == 'ACCEPTED_EXECUTION' and out in ['TP1_WIN', 'SL_LOSS']:
        filtered_r += rr
        filtered_trades += 1

print(f"Estrategia Base en Sombra (sin filtro H4 fresco): {base_trades} trades cerrados, Retorno: {base_r:+.2f}R")
print(f"Estrategia Filtrada en Sombra (H4 fresco + AI 0.35): {filtered_trades} trades cerrados, Retorno: {filtered_r:+.2f}R")
print(f"Diferencial directo en eventos cerrados: {filtered_r - base_r:+.2f}R")
