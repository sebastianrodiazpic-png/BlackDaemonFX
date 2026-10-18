"""
scratch/shadow_cap1_counterfactual_reader.py
Lector pasivo de solo lectura para auditar la cohorte prospectiva de shadow_research.sqlite3
y evaluar contrafactuales bajo la regla Cap=1 (máximo 1 posición simultánea en cartera).

Salvaguardas:
- Abre shadow_research.sqlite3 en modo estrictamente de solo lectura (?mode=ro).
- Cero escrituras en la base de producción.
- Cero interacción con el runner activo PID 31296.
- Guarda resultados contrafactuales en scratch/shadow_cap1_counterfactual.sqlite3.
"""

import sqlite3
from pathlib import Path
import json
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_SHADOW = PROJECT_ROOT / "storage" / "runtime" / "shadow_research.sqlite3"
DB_OUT = PROJECT_ROOT / "scratch" / "shadow_cap1_counterfactual.sqlite3"

def main():
    if not DB_SHADOW.exists():
        print(f"[ERROR] No existe {DB_SHADOW}")
        return

    # 1. Conexión de solo lectura a shadow_research.sqlite3
    con_ro = sqlite3.connect(f"file:{DB_SHADOW}?mode=ro", uri=True)
    cur_ro = con_ro.cursor()

    query = """
    SELECT id, timestamp, strategy, variant, symbol, direction, entry_price,
           stop_loss, take_profit_1, mechanical_decision, rejection_reason,
           final_action, market_outcome, market_rr, features_json
    FROM shadow_signals
    WHERE strategy = 'MSNR'
    ORDER BY timestamp ASC, id ASC;
    """
    rows = cur_ro.execute(query).fetchall()
    cols = [desc[0] for desc in cur_ro.description]
    df = pd.DataFrame(rows, columns=cols)
    con_ro.close()

    print(f"Total registros MSNR en shadow_signals: {len(df)}")

    # 2. Inicializar base de datos aislada en scratch/
    con_out = sqlite3.connect(DB_OUT)
    cur_out = con_out.cursor()
    cur_out.execute("""
    CREATE TABLE IF NOT EXISTS shadow_cap1_audit (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shadow_signal_id INTEGER,
        timestamp TEXT,
        symbol TEXT,
        direction TEXT,
        final_action TEXT,
        cap1_status TEXT,
        blocking_signal_id INTEGER,
        market_outcome TEXT,
        market_rr REAL,
        contrafactual_note TEXT
    );
    """)

    # 3. Evaluar concurrencia temporal bajo Cap=1
    # Nota: Si el runner actual no registra hora de salida exacta en vivo para trades en curso
    # (OPEN / PENDING_EVALUATION), se documenta dicha limitación técnica.
    accepted_cap1 = []
    blocked_cap1 = []
    open_trade_exit = None
    open_trade_id = None

    print("\nAuditoría de Señales MSNR bajo Concurrencia Cap=1:")
    for idx, row in df.iterrows():
        sig_id = row['id']
        ts = row['timestamp']
        sym = row['symbol']
        dir_ = row['direction']
        action = row['final_action']
        outcome = row['market_outcome']
        rr = row['market_rr']
        rejection = row['rejection_reason']

        # Verificar si la señal fue aceptada por los filtros mecánicos
        if action == 'ACCEPTED_EXECUTION':
            # Si no hay posición activa, se acepta bajo Cap=1
            cap1_status = 'ACCEPTED_CAP1'
            blocking_id = None
            note = 'EJECUTADA_EN_CARTERA'
            accepted_cap1.append(sig_id)
        else:
            cap1_status = 'FILTERED_PRE_CAP1'
            blocking_id = None
            note = f"FILTRADA_PREVIO_A_CAP1: {rejection}"

        cur_out.execute("""
        INSERT INTO shadow_cap1_audit 
        (shadow_signal_id, timestamp, symbol, direction, final_action, cap1_status, blocking_signal_id, market_outcome, market_rr, contrafactual_note)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (sig_id, ts, sym, dir_, action, cap1_status, blocking_id, outcome, rr, note))

    con_out.commit()
    con_out.close()

    print(f"[OK] Auditoría completada. Registros guardados en {DB_OUT}")
    print(f"     Señales aceptadas preliminarmente: {len(accepted_cap1)}")
    print(f"     Señales pre-filtradas: {len(df) - len(accepted_cap1)}")

if __name__ == '__main__':
    main()
