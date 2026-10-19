"""
Script de Actualización y Persistencia de Selección de Instrumentos:
Criterio: Terreno Dominante, Máxima Rentabilidad y Estrategia Ganadora según el Activo.

Aplica la selección persistente en SQLite (trading_bot.sqlite3) para cada uno de los workers:
- SYNTHETICS: Activos líderes por evidencia empírica (Crash 500 Index +$969.24 / WR 70.8%, Step Index 500 +$568.03 / WR 47.1%, HF Vol 50 +$220.37 / WR 100%, Boom 1000 +$73.18, Boom 300, Jump 10, Jump 75, etc.).
- GOLD: Activo dominante XAUUSD (+$532.82 PnL, WR 46.8%). Plata podada (-$374.68 PnL).
- ORB (New York Cash Open): Wall Street 30 (+44.46 PnL), XAUUSD (+532.82 PnL), US Tech 100, BTCUSD.
- IDX_OPEN: Wall Street 30 y US Tech 100.
- MALAYSIAN_SNR: Crash 500 (+969.24 PnL), Step 500 (+568.03 PnL), Boom 1000 (+73.18 PnL), XAUUSD (+532.82 PnL), Jump 10, Jump 75, Jump 25, Wall Street 30, BTCUSD.
- ICT (Sabri Malle): Wall Street 30, XAUUSD, XAGUSD, BTCUSD, US Oil, US Tech 100, US SP 500.
- FOREX: 14 pares rentables y sus variantes micro (EURUSD, GBPUSD, USDCAD, USDCHF, AUDUSD, USDJPY, AUDJPY, AUDNZD, CADCHF, CHFJPY, EURCHF, GBPCAD, EURJPY, GBPJPY) 100% activos y libres de poda.
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

from dashboard.realtime_dashboard import DEFAULT_PRIORITIZED_SYMBOLS

PROFILE_INSTRUMENT_MAP = {
    profile: list(symbols)
    for profile, symbols in DEFAULT_PRIORITIZED_SYMBOLS.items()
}


def update_persistent_database(db_path_override: str | None = None):
    db_path = db_path_override or resolve_db_path()
    print(f"Actualizando selección en base persistente: {db_path}")
    if not os.path.exists(db_path):
        print(f"Error: No existe {db_path}")
        return False

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")

    # 1. Actualizar instrument_selection_profile_preferences para TODOS los perfiles
    for source in ["DEMO", "LIVE"]:
        for profile, symbols in PROFILE_INSTRUMENT_MAP.items():
            cur.execute(
                "SELECT id, version FROM instrument_selection_profile_preferences WHERE source = ? AND selection_profile = ?",
                (source, profile),
            )
            row = cur.fetchone()
            syms_json = json.dumps(symbols, ensure_ascii=False)
            if row:
                row_id, version = row
                cur.execute(
                    "UPDATE instrument_selection_profile_preferences SET selected_symbols_json = ?, version = ?, updated_at = ? WHERE id = ?",
                    (syms_json, (version or 1) + 1, now_str, row_id),
                )
            else:
                cur.execute(
                    "INSERT INTO instrument_selection_profile_preferences (source, selection_profile, selected_symbols_json, version, updated_at) VALUES (?, ?, ?, 1, ?)",
                    (source, profile, syms_json, now_str),
                )

    # 2. Actualizar instrument_selection_preferences global (unión de todos los símbolos activos)
    all_selected = set()
    for sym_list in PROFILE_INSTRUMENT_MAP.values():
        all_selected.update(sym_list)
    combined = sorted(list(all_selected))
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

    print(f"  [EXITO] Base SQLite actualizada con criterio de terreno dominante / máxima rentabilidad:")
    for profile, syms in PROFILE_INSTRUMENT_MAP.items():
        print(f"    - {profile:15s}: {len(syms):2d} activos activos.")
    print(f"    - GLOBAL COMBINADO: {len(combined)} activos únicos.")

    # 3. Sincronizar en caliente el dashboard activo en puerto 8765 (si está en ejecución)
    try:
        urllib.request.urlopen("http://127.0.0.1:8765/performance", timeout=3.0).read()
    except Exception:
        pass

    live_catalog_by_profile: dict[str, set[str]] = {}
    try:
        raw_inst = urllib.request.urlopen("http://127.0.0.1:8765/api/instruments", timeout=3.0).read().decode("utf-8")
        inst_data = json.loads(raw_inst)
        for group in inst_data.get("instrument_catalog") or []:
            prof = str(group.get("selection_profile") or "").upper()
            if prof:
                live_catalog_by_profile.setdefault(prof, set()).update(group.get("symbols") or [])
    except Exception:
        live_catalog_by_profile = {}

    for profile, syms in PROFILE_INSTRUMENT_MAP.items():
        try:
            allowed_live = live_catalog_by_profile.get(profile)
            filtered_syms = [s for s in syms if s in allowed_live] if allowed_live else list(syms)
            if not filtered_syms:
                continue
            url = "http://127.0.0.1:8765/api/instruments/selection"
            payload = json.dumps(
                {"selection_profile": profile, "selected_symbols": filtered_syms}
            ).encode("utf-8")
            req = urllib.request.Request(
                url, data=payload, headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                json.loads(resp.read().decode())
        except Exception:
            pass

    return True


if __name__ == "__main__":
    update_persistent_database()

