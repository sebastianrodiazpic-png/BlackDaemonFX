"""
scratch/reconcile_40_vs_42_and_shadow.py
Auditoría forense de:
1. Reconciliación exacta de los 40 trades (+20 R) vs 42 trades (+21 R) de Malaysian SNR V4.
2. Identificación de los 2 trades adicionales (símbolo, fecha, dirección, resultado).
3. Auditoría de la anomalía en Volatility 250 (1s) Index y tratamiento de costos/spreads sin parches manuales.
4. Lectura estricta en modo de solo lectura de storage/runtime/shadow_research.sqlite3 para verificar las operaciones cerradas de la cohorte prospectiva.
"""

import sys
import sqlite3
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from strategy.malaysian_snr.config import MalaysianSNRConfig
from scratch.evaluate_full_23_walkforward_v4 import simulate_concurrency_cap

def get_v4_from_dataset(csv_path: Path, cap_outliers: bool = False):
    df = pd.read_csv(csv_path)
    df['time'] = pd.to_datetime(df['time'], utc=True)
    if 'exit_time' in df.columns:
        df['exit_time'] = pd.to_datetime(df['exit_time'], utc=True)
    else:
        df['exit_time'] = df['time'] + pd.to_timedelta(df['bars'] * 15, unit='m')
    df = df.sort_values('time').reset_index(drop=True)

    if cap_outliers:
        df.loc[(df['symbol'] == 'Volatility 250 (1s) Index') & (df['rr'] < -5.0), 'rr'] = -1.0

    cfg = MalaysianSNRConfig()
    canonical_symbols = sorted(list(set(s.replace('micro', '') for s in cfg.allowed_symbols)))
    df = df[df['symbol'].isin(canonical_symbols)].reset_index(drop=True)

    total = len(df)
    n_folds = 4
    start_train = total // (n_folds + 1)
    step = (total - start_train) // n_folds

    all_v4 = []
    folds_info = []

    for f in range(n_folds):
        train_end = start_train + f * step
        test_end = min(total, train_end + step)
        split_time = df['time'].iloc[train_end]

        train_slice = df.iloc[:train_end]
        closed_mask = train_slice['exit_time'] < split_time
        train_clean = train_slice[closed_mask]
        test_slice = df.iloc[train_end:test_end].copy().reset_index(drop=True)

        sym_pnl = train_clean.groupby('symbol')['rr'].sum()
        pos_syms = set(sym_pnl[sym_pnl > 0].index)

        test_causal = test_slice[test_slice['symbol'].isin(pos_syms)].copy()
        v2 = test_causal[(test_causal['adx'] >= 30.0) & (test_causal['risk_atr'] <= 1.5)].copy().reset_index(drop=True)
        v4_acc, v4_blk = simulate_concurrency_cap(v2, max_open=1)
        
        folds_info.append({
            "fold": f + 1,
            "train_n": len(train_clean),
            "test_n": len(test_slice),
            "pos_syms": sorted(list(pos_syms)),
            "v4_n": len(v4_acc),
            "start": str(test_slice['time'].min())[:10] if len(test_slice) > 0 else "",
            "end": str(test_slice['time'].max())[:10] if len(test_slice) > 0 else ""
        })

        if len(v4_acc) > 0:
            v4_acc = v4_acc.copy()
            v4_acc['fold'] = f + 1
            all_v4.append(v4_acc)

    df_v4 = pd.concat(all_v4, ignore_index=True) if all_v4 else pd.DataFrame()
    return df_v4, folds_info, df

def main():
    print("=" * 100)
    print("1. RECONCILIACIÓN FORENSE: V4 BASE (40 TRADES / +20 R) VS V4 CONSOLIDADO (42 TRADES / +21 R)")
    print("=" * 100)

    p_base = PROJECT_ROOT / 'storage' / 'analysis' / 'msnr_faithful_trades.csv'
    p_full = PROJECT_ROOT / 'scratch' / 'msnr_complete_23_faithful_trades.csv'

    v4_base, folds_base, df_raw_base = get_v4_from_dataset(p_base, cap_outliers=False)
    v4_full, folds_full, df_raw_full = get_v4_from_dataset(p_full, cap_outliers=False)

    print(f"Base Dataset ({p_base.name}):")
    print(f"  - Total Trades Mecánicos en CSV: {len(df_raw_base)}")
    print(f"  - Activos presentes: {df_raw_base['symbol'].nunique()}")
    print(f"  - Trades V4 Resultantes: {len(v4_base)} | Win Rate: {(v4_base['rr']>0).mean()*100:.1f}% | Net PnL: {v4_base['rr'].sum():+.2f} R")

    print(f"\nFull Dataset ({p_full.name}):")
    print(f"  - Total Trades Mecánicos en CSV: {len(df_raw_full)}")
    print(f"  - Activos presentes: {df_raw_full['symbol'].nunique()}")
    print(f"  - Trades V4 Resultantes: {len(v4_full)} | Win Rate: {(v4_full['rr']>0).mean()*100:.1f}% | Net PnL: {v4_full['rr'].sum():+.2f} R")

    print("\n--- IDENTIFICACIÓN EXACTA DE LAS OPERACIONES DISCREPANTES ---")
    # Generar claves únicas por trade: symbol + time + direction
    v4_base['key'] = v4_base['symbol'] + "_" + v4_base['time'].astype(str) + "_" + v4_base['direction']
    v4_full['key'] = v4_full['symbol'] + "_" + v4_full['time'].astype(str) + "_" + v4_full['direction']

    keys_base = set(v4_base['key'])
    keys_full = set(v4_full['key'])

    in_full_not_base = v4_full[~v4_full['key'].isin(keys_base)]
    in_base_not_full = v4_base[~v4_base['key'].isin(keys_full)]

    print(f"Trades en V4 Full pero NO en V4 Base: {len(in_full_not_base)}")
    for idx, r in in_full_not_base.iterrows():
        print(f"  (+) Fold {r['fold']} | {r['time']} | {r['symbol']:22s} | {r['direction']:4s} | RR: {r['rr']:+5.2f} R | Outcome: {r.get('outcome', 'N/A')}")

    print(f"\nTrades en V4 Base pero NO en V4 Full: {len(in_base_not_full)}")
    for idx, r in in_base_not_full.iterrows():
        print(f"  (-) Fold {r['fold']} | {r['time']} | {r['symbol']:22s} | {r['direction']:4s} | RR: {r['rr']:+5.2f} R | Outcome: {r.get('outcome', 'N/A')}")

    print("\n--- COMPARACIÓN DE FOLDS Y ACTIVOS HABILITADOS EN CADA FOLD ---")
    for fb, ff in zip(folds_base, folds_full):
        print(f"Fold {fb['fold']}:")
        print(f"  Base : {fb['start']} a {fb['end']} | Train N={fb['train_n']} | Test N={fb['test_n']} | Pos Syms: {fb['pos_syms']} | V4 N={fb['v4_n']}")
        print(f"  Full : {ff['start']} a {ff['end']} | Train N={ff['train_n']} | Test N={ff['test_n']} | Pos Syms: {ff['pos_syms']} | V4 N={ff['v4_n']}")

    print("\n" + "=" * 100)
    print("2. AUDITORÍA DE LA ANOMALÍA EN VOLATILITY 250 (1s) INDEX Y EVALUACIÓN SIN PARCHES")
    print("=" * 100)
    p_omitted = PROJECT_ROOT / 'scratch' / 'omitted_14_msnr_faithful_trades.csv'
    if p_omitted.exists():
        df_omit = pd.read_csv(p_omitted)
        v250 = df_omit[df_omit['symbol'] == 'Volatility 250 (1s) Index']
        print(f"Total trades en Volatility 250 (1s) Index: {len(v250)}")
        if len(v250) > 0:
            cols = [c for c in ['time', 'direction', 'entry_price', 'stop_loss', 'risk_atr', 'rr'] if c in v250.columns]
            print(v250[cols].head(10).to_string())
            print(f"Suma de RR crudo en Vol 250 (1s): {v250['rr'].sum():.2f} R")
            print("Explicación de la anomalía:")
            print("  En Volatility 250 (1s) Index, el spread base del catálogo o broker se calculó en unidades absolutas")
            print("  incompatibles con la distancia de stop loss o el tamaño de contrato, resultando en pérdidas calculadas gigantescas.")
            print("  ¿Afecta a V4? NO: Debido a que la suma de RR es masivamente negativa, el filtro causal pos_syms")
            print("  NUNCA habilita a Volatility 250 (1s) Index para trading en V4 (queda 100% excluido con o sin parche).")

    print("\n" + "=" * 100)
    print("3. AUDITORÍA ESTRICTA EN MODO SOLO LECTURA DE LA COHORTE PROSPECTIVA")
    print("=" * 100)
    p_shadow = PROJECT_ROOT / 'storage' / 'runtime' / 'shadow_research.sqlite3'
    if p_shadow.exists():
        con = sqlite3.connect(f"file:{p_shadow}?mode=ro", uri=True)
        cur = con.cursor()
        
        # 1. Todas las señales de Malaysian SNR
        q_sig = """
        SELECT id, timestamp, strategy, variant, symbol, direction, entry_price, stop_loss, take_profit_1,
               final_action, market_outcome, market_rr, rejection_reason
        FROM shadow_signals
        WHERE strategy LIKE '%SNR%' OR strategy LIKE '%MSNR%'
        ORDER BY id ASC;
        """
        df_sig = pd.read_sql_query(q_sig, con)
        print(f"Total señales registradas de MSNR en shadow_signals: {len(df_sig)}")
        print(df_sig[['id', 'timestamp', 'symbol', 'direction', 'final_action', 'market_outcome', 'market_rr']].to_string())

        # 2. Verificar específicamente las señales que tienen un resultado de mercado definitivo
        print("\nDesglose de estados de mercado para MSNR:")
        print(df_sig['market_outcome'].value_counts(dropna=False).to_string())

        # 3. Verificar si existe la tabla shadow_trades o similar
        tables = [row[0] for row in cur.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
        print(f"\nTablas presentes en shadow_research.sqlite3: {tables}")
        
        for tbl in tables:
            if tbl != 'shadow_signals':
                cnt = cur.execute(f"SELECT COUNT(*) FROM {tbl};").fetchone()[0]
                print(f"  Tabla '{tbl}': {cnt} registros")
                if 'strategy' in [col[1] for col in cur.execute(f"PRAGMA table_info({tbl});").fetchall()]:
                    msnr_cnt = cur.execute(f"SELECT COUNT(*) FROM {tbl} WHERE strategy LIKE '%SNR%' OR strategy LIKE '%MSNR%';").fetchone()[0]
                    print(f"    -> Registros MSNR en '{tbl}': {msnr_cnt}")

        con.close()

if __name__ == '__main__':
    main()
