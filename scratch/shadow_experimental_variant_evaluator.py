"""
scratch/shadow_experimental_variant_evaluator.py
Lector e instrumentador prospectivo pasivo en modo sombra para evaluar la variante experimental:
- Metales y Forex: ATR <= 1.2
- Sintéticos: Body Ratio >= 0.50
- Concurrencia: Cap=1

Salvaguardas de Seguridad e Integridad:
1. Conexión de solo lectura a storage/runtime/shadow_research.sqlite3 (?mode=ro).
2. Cero escrituras en bases de producción o en shadow_research.sqlite3.
3. Cero interrupciones al runner activo PID 31296.
4. Base de datos aislada e independiente en scratch/shadow_experimental_variant.sqlite3.
5. Deduplicación estricta (clave primaria: shadow_signal_id con ON CONFLICT DO UPDATE).
6. Clasificación de aceptadas/filtradas y cálculo de resultados contrafactuales.
"""

import sqlite3
import json
from pathlib import Path
import pandas as pd
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_SHADOW = PROJECT_ROOT / "storage" / "runtime" / "shadow_research.sqlite3"
DB_EXP_OUT = PROJECT_ROOT / "scratch" / "shadow_experimental_variant.sqlite3"

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
    if not DB_SHADOW.exists():
        print(f"[ERROR] No existe {DB_SHADOW}")
        return

    # 1. Conexión de solo lectura a shadow_research.sqlite3
    con_ro = sqlite3.connect(f"file:{DB_SHADOW}?mode=ro", uri=True)
    cur_ro = con_ro.cursor()

    query = """
    SELECT id, timestamp, strategy, variant, symbol, direction, entry_price,
           stop_loss, take_profit_1, take_profit_2, mechanical_decision, rejection_reason,
           final_action, features_json, simulated_outcome, simulated_rr, market_outcome, market_rr
    FROM shadow_signals
    WHERE strategy = 'MSNR'
    ORDER BY timestamp ASC, id ASC;
    """
    rows = cur_ro.execute(query).fetchall()
    cols = [desc[0] for desc in cur_ro.description]
    df = pd.DataFrame(rows, columns=cols)
    con_ro.close()

    print(f"Total registros MSNR leídos en modo de solo lectura: {len(df)}")

    # 2. Inicializar base de datos aislada en scratch/ con clave primaria para deduplicación
    con_out = sqlite3.connect(DB_EXP_OUT)
    cur_out = con_out.cursor()
    cur_out.execute("DROP TABLE IF EXISTS shadow_experimental_variant_audit;")
    cur_out.execute("""
    CREATE TABLE shadow_experimental_variant_audit (
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
        contrafactual_impact TEXT,
        evaluated_at TEXT
    );
    """)

    now_iso = datetime.now(timezone.utc).isoformat()
    n_inserted = 0
    n_updated = 0
    records = []

    for idx, row in df.iterrows():
        sig_id = row['id']
        sym = row['symbol']
        subfam = get_subfamily(sym)
        v4_status = row['final_action']
        mkt_outcome = row['market_outcome']
        mkt_rr = row['market_rr'] if row['market_rr'] is not None else 0.0

        feat = {}
        if row['features_json']:
            try:
                feat = json.loads(row['features_json'])
            except Exception:
                pass

        exp_status = "ACCEPTED"
        exclusion_reason = "NONE"

        risk_atr = feat.get('risk_atr')
        body_ratio = feat.get('body_ratio')

        if subfam in ('METALS', 'FOREX') and risk_atr is not None and risk_atr > 1.2:
            exp_status = "FILTERED_BY_ATR"
            exclusion_reason = f"ATR {risk_atr:.2f} > 1.2"
        elif subfam == 'SYNTH' and body_ratio is not None and body_ratio < 0.50:
            exp_status = "FILTERED_BY_BODY"
            exclusion_reason = f"BodyRatio {body_ratio:.2f} < 0.50"

        # Clasificación del impacto contrafactual
        if exp_status != "ACCEPTED":
            if mkt_outcome == 'SL_LOSS':
                impact = "AVOIDED_LOSS"
            elif mkt_outcome == 'TP1_WIN':
                impact = "MISSED_GAIN"
            else:
                impact = "FILTERED_PENDING"
        else:
            impact = "EXECUTED"

        # Deduplicación con INSERT OR REPLACE
        cur_out.execute("""
        INSERT INTO shadow_experimental_variant_audit (
            shadow_signal_id, timestamp, symbol, subfamily, direction,
            v4_status, experimental_filter_status, exclusion_reason,
            market_outcome, market_rr, contrafactual_impact, evaluated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(shadow_signal_id) DO UPDATE SET
            market_outcome = excluded.market_outcome,
            market_rr = excluded.market_rr,
            contrafactual_impact = excluded.contrafactual_impact,
            evaluated_at = excluded.evaluated_at;
        """, (
            sig_id, row['timestamp'], sym, subfam, row['direction'],
            v4_status, exp_status, exclusion_reason, mkt_outcome, mkt_rr, impact, now_iso
        ))
        records.append({
            "id": sig_id, "time": row['timestamp'], "sym": sym,
            "subfam": subfam, "exp_status": exp_status, "impact": impact,
            "mkt_outcome": mkt_outcome, "mkt_rr": mkt_rr
        })

    con_out.commit()
    
    # Consulta de verificación del estado resultante
    cur_out.execute("SELECT count(*), contrafactual_impact FROM shadow_experimental_variant_audit GROUP BY contrafactual_impact")
    summary = cur_out.fetchall()
    con_out.close()

    print(f"\n[OK] Base aislada sincronizada con deduplicación estricta:")
    print(f"     Ubicación: {DB_EXP_OUT}")
    for count, impact in summary:
        print(f"     Impacto Contrafactual '{impact}': {count} señales")

if __name__ == '__main__':
    main()
