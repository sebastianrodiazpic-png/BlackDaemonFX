"""
Script de Actualización y Persistencia de la Poda de Instrumentos:
Sintéticos y Forex en SQLite (trading_bot.sqlite3) y Configuración del Motor.

Aplica la poda y selección basada estrictamente en la evidencia del Replay de 2 años
y en `DEFAULT_PRIORITIZED_SYMBOLS` / `PRUNED_INSTRUMENTS_INFO` del Dashboard:

- ACTIVOS / PRIORIZADOS (26 Sintéticos Ganadores):
  * BOOM: Boom 1000 Index, Boom 300 Index, Boom 900 Index.
  * CRASH: Crash 500 Index, Crash 900 Index.
  * JUMP: Jump 10 Index, Jump 50 Index, Jump 75 Index.
  * STEP: Step Index, Step Index 400, Step Index 500.
  * VOLATILITY: High Frequency Vol 100 Index, High Frequency Vol 50 Index,
    Vol over Boom 550, Vol over Crash 550, VolSwitch High Vol Index,
    Volatility 15 Index, Volatility 150 (1s) Index, Volatility 25 Index,
    Volatility 250 (1s) Index, Volatility 5 Index, Volatility 50 (1s) Index,
    Volatility 75 (1s) Index, Volatility 75 Index, Volatility 90 (1s) Index,
    Volatility 90 Index.

- DESCARTADOS / PODADOS (Desactivados en checkbox):
  * Boom 500, 600, 50, 100, 150, 200, 99.
  * Crash 1000, 300, 600, 50, 100, 150, 200, 99.
  * Step Index 200, 300, Multi Step 2, 3, 4, Skew Step.
  * Jump 25, Jump 100.
  * Volatility 100, 100 (1s), 50, 10, 10 (1s), 30, 30 (1s), Vol over Crash 400,
    Vol over Boom 750, Spot Up - Volatility Up, Vol over Crash 750, etc.

- FOREX (10 Activos Seleccionados):
  * EURUSD, EURUSDmicro, USDJPY, USDJPYmicro, GBPUSD, GBPUSDmicro,
    USDCAD, USDCADmicro, USDCHF, USDCHFmicro.
"""

import sys
import os
import json
import sqlite3
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.database import resolve_db_path

PRIORITIZED_SYNTHETICS = [
    # BOOM (3 ganadores prioritarios)
    "Boom 1000 Index",
    "Boom 300 Index",
    "Boom 900 Index",
    # CRASH (2 ganadores prioritarios)
    "Crash 500 Index",
    "Crash 900 Index",
    # JUMP (3 ganadores prioritarios SMC)
    "Jump 10 Index",
    "Jump 50 Index",
    "Jump 75 Index",
    # STEP (3 ganadores prioritarios SMC)
    "Step Index",
    "Step Index 400",
    "Step Index 500",
    # VOLATILITY (15 ganadores cuantitativos del replay de 2 años)
    "High Frequency Vol 100 Index",
    "High Frequency Vol 50 Index",
    "Vol over Boom 550",
    "Vol over Crash 550",
    "VolSwitch High Vol Index",
    "Volatility 15 Index",
    "Volatility 150 (1s) Index",
    "Volatility 25 Index",
    "Volatility 250 (1s) Index",
    "Volatility 5 Index",
    "Volatility 50 (1s) Index",
    "Volatility 75 (1s) Index",
    "Volatility 75 Index",
    "Volatility 90 (1s) Index",
    "Volatility 90 Index",
]

PRIORITIZED_FOREX = [
    "EURUSD",
    "EURUSDmicro",
    "USDJPY",
    "USDJPYmicro",
    "GBPUSD",
    "GBPUSDmicro",
    "USDCAD",
    "USDCADmicro",
    "USDCHF",
    "USDCHFmicro",
]


def update_persistent_database():
    db_path = resolve_db_path()
    print(f"Actualizando selección en base persistente: {db_path}")
    if not os.path.exists(db_path):
        print(f"Error: No existe {db_path}")
        return False

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")

    # 1. Actualizar instrument_selection_profile_preferences para SYNTHETICS y FOREX
    for source in ["DEMO", "LIVE"]:
        # SYNTHETICS
        cur.execute(
            "SELECT id, version FROM instrument_selection_profile_preferences WHERE source = ? AND selection_profile = 'SYNTHETICS'",
            (source,),
        )
        row = cur.fetchone()
        synth_json = json.dumps(PRIORITIZED_SYNTHETICS, ensure_ascii=False)
        if row:
            row_id, version = row
            cur.execute(
                "UPDATE instrument_selection_profile_preferences SET selected_symbols_json = ?, version = ?, updated_at = ? WHERE id = ?",
                (synth_json, (version or 1) + 1, now_str, row_id),
            )
        else:
            cur.execute(
                "INSERT INTO instrument_selection_profile_preferences (source, selection_profile, selected_symbols_json, version, updated_at) VALUES (?, 'SYNTHETICS', ?, 1, ?)",
                (source, synth_json, now_str),
            )

        # FOREX
        cur.execute(
            "SELECT id, version FROM instrument_selection_profile_preferences WHERE source = ? AND selection_profile = 'FOREX'",
            (source,),
        )
        row = cur.fetchone()
        forex_json = json.dumps(PRIORITIZED_FOREX, ensure_ascii=False)
        if row:
            row_id, version = row
            cur.execute(
                "UPDATE instrument_selection_profile_preferences SET selected_symbols_json = ?, version = ?, updated_at = ? WHERE id = ?",
                (forex_json, (version or 1) + 1, now_str, row_id),
            )
        else:
            cur.execute(
                "INSERT INTO instrument_selection_profile_preferences (source, selection_profile, selected_symbols_json, version, updated_at) VALUES (?, 'FOREX', ?, 1, ?)",
                (source, forex_json, now_str),
            )

    # 2. Actualizar instrument_selection_preferences global
    combined = sorted(list(set(PRIORITIZED_SYNTHETICS + PRIORITIZED_FOREX)))
    comb_json = json.dumps(combined, ensure_ascii=False)
    for source in ["DEMO", "LIVE"]:
        cur.execute("SELECT id, version FROM instrument_selection_preferences WHERE source = ?", (source,))
        row = cur.fetchone()
        if row:
            row_id, version = row
            cur.execute(
                "UPDATE instrument_selection_preferences SET selected_symbols_json = ?, version = ?, updated_at = ? WHERE id = ?",
                (comb_json, (version or 1) + 1, now_str, row_id),
            )
        else:
            cur.execute(
                "INSERT INTO instrument_selection_preferences (source, selected_symbols_json, version, updated_at) VALUES (?, ?, 1, ?)",
                (source, comb_json, now_str),
            )

    conn.commit()
    conn.close()
    print(f"  [EXITO] Base SQLite actualizada:")
    print(f"    - SYNTHETICS: {len(PRIORITIZED_SYNTHETICS)} activos priorizados.")
    print(f"    - FOREX: {len(PRIORITIZED_FOREX)} activos autorizados.")

    # 3. Notificar al dashboard activo si está corriendo en puerto 8765
    try:
        url = "http://127.0.0.1:8765/api/instruments/selection"
        payload = json.dumps(
            {"selection_profile": "SYNTHETICS", "selected_symbols": PRIORITIZED_SYNTHETICS}
        ).encode("utf-8")
        req = urllib.request.Request(
            url, data=payload, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode())
            print(f"  [DASHBOARD SYNC] Estado del dashboard en vivo actualizado exitosamente: {data.get('message')}")
    except Exception as exc:
        print(f"  [DASHBOARD SYNC] Aviso (la base SQLite ya quedó persistida): {exc}")

    return True


if __name__ == "__main__":
    update_persistent_database()
