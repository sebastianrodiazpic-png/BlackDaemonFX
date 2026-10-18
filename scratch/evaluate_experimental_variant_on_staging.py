"""
scratch/evaluate_experimental_variant_on_staging.py
===================================================
Evaluador pasivo de la variante experimental (ATR <= 1.2 en Metales/Forex, Body >= 0.50 en Sintéticos)
sobre la base aislada de STAGING (shadow_research_staging.sqlite3).

Garantías:
1. Conexión de solo lectura a storage/runtime/shadow_research_staging.sqlite3 (?mode=ro).
2. Salida aislada en scratch/shadow_experimental_variant_staging.sqlite3.
3. Deduplicación por shadow_signal_id.
4. Separación estricta de contrafactuales: pérdidas evitadas vs ganancias omitidas.
"""

import sqlite3
import json
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STAGING_DB = PROJECT_ROOT / "storage" / "runtime" / "shadow_research_staging.sqlite3"
OUT_DB = PROJECT_ROOT / "scratch" / "shadow_experimental_variant_staging.sqlite3"

SYNTHS = set([
    'Boom 1000 Index', 'Boom 300 Index', 'Crash 1000 Index', 'Crash 600 Index',
    'Jump 10 Index', 'Jump 25 Index', 'Jump 50 Index', 'Step Index', 'Step Index 200',
    'Step Index 400', 'Volatility 250 (1s) Index', 'Volatility 50 (1s) Index',
    'Volatility 90 Index', 'Crash 500 Index', 'Crash 300 Index'
])
FOREX = set(['AUDNZD', 'EURCHF', 'EURGBP', 'EURUSD', 'GBPAUD', 'GBPJPY', 'GBPUSD', 'USDJPY'])
METALS_INDICES = set(['XAUUSD', 'XAGUSD', 'Wall Street 30', 'US Tech 100'])

def get_subfamily(sym):
    if sym in SYNTHS:
        return 'SYNTH'
    elif sym in FOREX:
        return 'FOREX'
    elif sym in METALS_INDICES:
        return 'METALS'
    return 'OTHER'

def main():
    if not STAGING_DB.exists():
        print(f"[ERROR] Staging database not found at {STAGING_DB}")
        return

    con_ro = sqlite3.connect(f"file:{STAGING_DB}?mode=ro", uri=True)
    df = pd.read_sql("""
        SELECT id, timestamp, strategy, variant, symbol, direction, entry_price,
               stop_loss, take_profit_1, take_profit_2, mechanical_decision, rejection_reason,
               final_action, features_json, simulated_outcome, simulated_rr, market_outcome, market_rr
        FROM shadow_signals
        WHERE strategy = 'MSNR'
        ORDER BY timestamp ASC, id ASC
    """, con_ro)
    con_ro.close()

    print(f"Total señales MSNR leídas de staging: {len(df)}")

    con_out = sqlite3.connect(OUT_DB)
    cur_out = con_out.cursor()
    cur_out.execute("DROP TABLE IF EXISTS experimental_staging_audit;")
    cur_out.execute("""
        CREATE TABLE experimental_staging_audit (
            shadow_signal_id INTEGER PRIMARY KEY,
            timestamp TEXT,
            symbol TEXT,
            subfamily TEXT,
            direction TEXT,
            v4_status TEXT,
            experimental_filter_status TEXT,
            exclusion_reason TEXT,
            market_outcome TEXT,
            market_rr REAL,
            simulated_outcome TEXT,
            simulated_rr REAL,
            contrafactual_impact TEXT,
            evaluated_at TEXT
        );
    """)

    now_iso = datetime.now(timezone.utc).isoformat()
    rows_to_insert = []

    for _, row in df.iterrows():
        sig_id = row['id']
        sym = row['symbol']
        subfam = get_subfamily(sym)
        v4_status = row['final_action']
        mkt_outcome = row['market_outcome']
        mkt_rr = float(row['market_rr'] or 0.0)
        sim_out = row['simulated_outcome']
        sim_rr = float(row['simulated_rr'] or 0.0)

        feat = {}
        if row['features_json']:
            try:
                feat = json.loads(row['features_json'])
            except Exception:
                pass

        risk_atr = feat.get('risk_atr')
        body_ratio = feat.get('body_ratio')

        exp_status = "ACCEPTED"
        excl_reason = "NONE"

        if subfam in ('METALS', 'FOREX') and risk_atr is not None and risk_atr > 1.2:
            exp_status = "FILTERED_BY_ATR"
            excl_reason = f"ATR {risk_atr:.2f} > 1.2"
        elif subfam == 'SYNTH' and body_ratio is not None and body_ratio < 0.50:
            exp_status = "FILTERED_BY_BODY"
            excl_reason = f"BodyRatio {body_ratio:.2f} < 0.50"

        # Impacto contrafactual
        if exp_status != "ACCEPTED":
            if mkt_outcome == 'SL_LOSS':
                impact = "AVOIDED_LOSS"
            elif mkt_outcome == 'TP1_WIN':
                impact = "MISSED_GAIN"
            else:
                impact = "FILTERED_PENDING"
        else:
            impact = "EXECUTED"

        rows_to_insert.append((
            sig_id, row['timestamp'], sym, subfam, row['direction'],
            v4_status, exp_status, excl_reason, mkt_outcome, mkt_rr,
            sim_out, sim_rr, impact, now_iso
        ))

    cur_out.executemany("""
        INSERT INTO experimental_staging_audit VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, rows_to_insert)
    con_out.commit()

    print(f"Insertadas {len(rows_to_insert)} filas en {OUT_DB}")

    # Resumen
    df_res = pd.read_sql("SELECT v4_status, experimental_filter_status, market_outcome, count(*), round(sum(market_rr), 4) FROM experimental_staging_audit GROUP BY v4_status, experimental_filter_status, market_outcome", con_out)
    print("\nResumen Comparativo en Staging:")
    print(df_res.to_string())

    con_out.close()

if __name__ == '__main__':
    main()
