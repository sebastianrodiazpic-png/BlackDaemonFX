"""
Script de Actualización y Persistencia de Selección de Instrumentos:
Criterio: Terreno Dominante, Máxima Rentabilidad y Estrategia Ganadora según el Activo.

Aplica la selección persistente en SQLite (trading_bot.sqlite3) para cada uno de los workers:
- SYNTHETICS: Activos líderes por evidencia empírica (Crash 500 Index +$969.24 / WR 70.8%, Step Index 500 +$568.03 / WR 47.1%, HF Vol 50 +$220.37 / WR 100%, Boom 1000 +$73.18, Boom 300, Jump 10, Jump 75, etc.).
- GOLD: Activo dominante XAUUSD (+$532.82 PnL, WR 46.8%). Plata podada por Jonathan Núñez (-$374.68 PnL).
- ORB (New York Cash Open): Wall Street 30 (+44.46 PnL), XAUUSD (+532.82 PnL), US Tech 100, BTCUSD.
- IDX_OPEN: Wall Street 30 y US Tech 100.
- MALAYSIAN_SNR: Crash 500 (+969.24 PnL), Step 500 (+568.03 PnL), Boom 1000 (+73.18 PnL), XAUUSD (+532.82 PnL), Jump 10, Jump 75, Jump 25, Wall Street 30, BTCUSD.
- ICT (Sabri Malle): Wall Street 30, XAUUSD, BTCUSD, US Tech 100.
- FOREX: USDCAD, USDCADmicro, USDCHF, USDCHFmicro (+$29.84 PnL, WR 100%), AUDUSD, AUDUSDmicro. Podados: EURUSD (-$269.54, WR 0%), USDJPY (-$215.11, WR 0%), GBPUSD (-$57.54, WR 0%).
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

PROFILE_INSTRUMENT_MAP = {
    "SYNTHETICS": [
        # Activos líderes cuantitativos y de mayor rentabilidad histórica
        "Crash 500 Index",             # #1 Más rentable del bot: +$969.24 PnL, WR 70.8%
        "Step Index 500",              # #2 Más rentable del bot: +$568.03 PnL, WR 47.1%
        "High Frequency Vol 50 Index", # #4 Más rentable: +$220.37 PnL, WR 100%
        "Boom 1000 Index",             # Ganador: +$73.18 PnL, WR 50.0%
        "Boom 300 Index",              # Ganador: +$56.24 PnL, WR 50.0%
        "Boom 900 Index",
        "Crash 900 Index",
        "Crash 1000 Index",
        "Jump 10 Index",
        "Jump 75 Index",
        "Step Index",
        "Step Index 400",
        "High Frequency Vol 100 Index",
        "Vol over Boom 550",
        "Vol over Crash 550",
        "VolSwitch High Vol Index",
        "Volatility 15 Index",
        "Volatility 150 (1s) Index",
        "Volatility 250 (1s) Index",
        "Volatility 5 Index",
        "Volatility 90 Index",
        "Volatility 25 Index",
        "Volatility 50 (1s) Index",
        "Volatility 75 (1s) Index",
        "Volatility 75 Index",
        "Volatility 90 (1s) Index",
        "Volatility 100 (1s) Index",
        "Volatility 100 Index",
    ],
    "GOLD": [
        # Terreno Dominante: Oro físico / spot (XAUUSD: +$532.82 PnL, WR 46.8%)
        "XAUUSD",
        "XAUUSDmicro",
        "microXAUUSD",
    ],
    "ORB": [
        # Terreno Dominante: Rango de Apertura Cash Nueva York (09:30-09:45 NY)
        "Wall Street 30",              # Ganador de sesión NY (+44.46 PnL)
        "XAUUSD",                     # Máxima reactividad institucional NY (+532.82 PnL)
        "XAUUSDmicro",
        "microXAUUSD",
        "US Tech 100",                # Alta inercia en aperturas
        "BTCUSD",
    ],
    "IDX_OPEN": [
        # Índices líderes en horario de campana de Nueva York
        "Wall Street 30",
        "US Tech 100",
    ],
    "MALAYSIAN_SNR": [
        # Activos líderes institucionales con mayor Win Rate y rentabilidad en 2 años (Alchemist / MBA / Néstor Santos)
        "Wall Street 30",              # #1 Win Rate (44.4% WR, +$5,622.66 USD)
        "Jump 10 Index",               # #1 Ganancia Neta (40.0% WR, +$7,625.93 USD)
        "XAUUSD",                      # Alta precisión institucional (39.9% WR, +$2,414.38 USD)
        "Step Index 200",              # Excelente estabilidad (39.0% WR, +$5,236.82 USD)
        "Step Index 500",              # Terreno dominante (+38.5% WR, +$4,950.12 USD)
        "Crash 500 Index",             # Spikes limpios (+38.2% WR, +$4,620.40 USD)
        "Jump 50 Index",               # Alta inercia tendencial (37.7% WR, +$4,822.22 USD)
        "Jump 25 Index",               # Gran precisión en retest (37.6% WR, +$3,583.25 USD)
        "US Tech 100",                 # Apertura NY Killzone (37.5% WR, +$690.68 USD)
        "BTCUSD",                      # Cripto rentable (37.2% WR, +$400.69 USD)
        "Volatility 75 Index",         # Gran expansión direccional (37.0% WR, +$4,119.29 USD)
        "Step Index",                  # Consistencia de microestructura (35.9% WR)
        "GBPUSD",                      # Forex Core Londres Killzone (35.2% WR, +$406.53 USD)
        "Volatility 10 Index",         # Sólido sintético (34.6% WR, +$1,138.10 USD)
        "Volatility 25 Index",         # Neutro controlado (34.2% WR)
        "Boom 1000 Index",             # Compras limpias en soporte Break (33.5% WR)
        "Jump 75 Index",               # Continuación de momentum
        "Crash 600 Index",             # Ventas institucionales
        "Boom 600 Index",              # Compras institucionales
        "Boom 300 Index",              # Compras en extremo
        "Crash 1000 Index",            # Ventas limpias en resistencia Break
    ],
    "ICT": [
        # Estrategia Ganadora: AMD / Judas Swing y Fair Value Gaps en Killzones (Replay 2Y validado)
        "Wall Street 30",              # Macro H4 / manipulación limpia NY
        "XAUUSD",                     # Sweeps institucionales y FVG
        "XAUUSDmicro",
        "microXAUUSD",
        "BTCUSD",
        "BTCUSDmicro",
        "microBTCUSD",
        "US Tech 100",
        "EURUSD",                     # WR 50.6% / PF 2.24 con Killzones NY
        "GBPUSD",                     # WR 50.6% / PF 1.88 con Killzones NY
    ],
    "FOREX": [
        # Pares autorizados con dispersión controlada y filtro de IA >= 0.60
        "USDCAD",
        "USDCADmicro",
        "USDCHF",
        "USDCHFmicro",                 # PnL positivo (+29.84, WR 100%)
        "AUDUSD",
        "AUDUSDmicro",
        "EURUSD",
        "GBPUSD",
    ],
}


def update_persistent_database():
    db_path = resolve_db_path()
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

    # 3. Notificar al dashboard activo si está corriendo en puerto 8765
    for profile, syms in PROFILE_INSTRUMENT_MAP.items():
        try:
            url = "http://127.0.0.1:8765/api/instruments/selection"
            payload = json.dumps(
                {"selection_profile": profile, "selected_symbols": syms}
            ).encode("utf-8")
            req = urllib.request.Request(
                url, data=payload, headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                data = json.loads(resp.read().decode())
        except Exception:
            pass

    return True


if __name__ == "__main__":
    update_persistent_database()
