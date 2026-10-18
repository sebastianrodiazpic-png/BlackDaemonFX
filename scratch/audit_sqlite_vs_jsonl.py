import sqlite3
import json
import pandas as pd
from pathlib import Path

db_path = Path("storage/runtime/shadow_research.sqlite3")
jsonl_path = Path("storage/runtime/shadow_events.jsonl")

print("=====================================================================")
print("AUDITORÍA CRUZADA INTEGRAL: SQLITE VS JSONL EN MODO SOMBRA")
print("=====================================================================")

# 1. Leer SQLite
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute("SELECT * FROM shadow_signals ORDER BY id ASC")
sqlite_rows = [dict(r) for r in cur.fetchall()]
conn.close()

print(f"Total registros en shadow_signals (SQLite): {len(sqlite_rows)}")

# 2. Leer JSONL
jsonl_events = []
if jsonl_path.exists():
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            line_str = line.strip()
            if line_str:
                try:
                    jsonl_events.append(json.loads(line_str))
                except Exception as e:
                    print(f"Error parseando línea {idx+1} de JSONL: {e}")

print(f"Total eventos en shadow_events.jsonl: {len(jsonl_events)}")

# 3. Auditar todas las filas descartadas en SQLite
df_sql = pd.DataFrame(sqlite_rows)
discarded_sql = df_sql[df_sql['final_action'] == 'DISCARDED_BY_FILTER']
accepted_sql = df_sql[df_sql['final_action'] == 'ACCEPTED_EXECUTION']

print(f"\n--- AUDITORÍA DE FILAS EN SQLITE ---")
print(f"Total filas Aceptadas:  {len(accepted_sql)}")
print(f"Total filas Descartadas: {len(discarded_sql)}")

# Verificar condiciones de integridad en descartadas
disc_non_zero_rr = discarded_sql[discarded_sql['simulated_rr'] != 0.0]
disc_bad_outcome = discarded_sql[discarded_sql['simulated_outcome'] != 'AVOIDED']

print(f"\nVerificación de Descartadas:")
print(f"  * Descartadas con simulated_rr != 0.0: {len(disc_non_zero_rr)}")
print(f"  * Descartadas con simulated_outcome != 'AVOIDED': {len(disc_bad_outcome)}")
if not disc_non_zero_rr.empty:
    print("    Inconsistencias encontradas en simulated_rr:")
    print(disc_non_zero_rr[['id', 'timestamp', 'strategy', 'variant', 'symbol', 'simulated_rr']])
if not disc_bad_outcome.empty:
    print("    Inconsistencias encontradas en simulated_outcome:")
    print(disc_bad_outcome[['id', 'timestamp', 'strategy', 'variant', 'symbol', 'simulated_outcome']])

# Verificar condiciones en aceptadas
acc_null_outcome = accepted_sql[accepted_sql['simulated_outcome'].isnull()]
print(f"\nVerificación de Aceptadas:")
print(f"  * Aceptadas con simulated_outcome nulo: {len(acc_null_outcome)}")
print(f"  * Distribución de simulated_outcome en Aceptadas:")
print(accepted_sql['simulated_outcome'].value_counts().to_string())

# 4. Comparar contenido con JSONL
# Verificar si el número coincide y qué contiene el JSONL
print(f"\n--- ANÁLISIS DE JSONL (LOG SECUENCIAL EN TIEMPO REAL) ---")
if jsonl_events:
    df_jsonl = pd.DataFrame(jsonl_events)
    print(f"Estrategias en JSONL: {df_jsonl['strategy'].value_counts().to_dict()}")
    print(f"Acciones en JSONL: {df_jsonl['final_action'].value_counts().to_dict()}")
    # Ver si JSONL tiene simulated_outcome
    if 'simulated_outcome' in df_jsonl.columns:
        print(f"Distribución simulated_outcome en JSONL (al momento de emitir la señal):")
        print(df_jsonl['simulated_outcome'].value_counts().to_dict())

# 5. Análisis de correspondencia pareada por evento de mercado
print(f"\n--- AUDITORÍA DE CONSISTENCIA DE MARKET_OUTCOME POR EVENTO DE MERCADO ---")
# Para cada (timestamp, symbol, direction), verificar que market_outcome y market_rr sean IDÉNTICOS en todas las variantes
grouped = df_sql.groupby(['timestamp', 'symbol', 'direction'])
inconsistent_events = 0
for (t, s, d), grp in grouped:
    m_outs = grp['market_outcome'].unique()
    m_rrs = grp['market_rr'].unique()
    if len(m_outs) > 1 or len(m_rrs) > 1:
        print(f"INCONSISTENCIA EN EVENTO: {t} | {s} {d} -> market_outcomes: {m_outs}, market_rrs: {m_rrs}")
        inconsistent_events += 1

if inconsistent_events == 0:
    print("Todos los eventos de mercado pareados tienen exactamente el mismo market_outcome y market_rr en todas sus variantes.")

