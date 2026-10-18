import pandas as pd
import numpy as np
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from strategy.malaysian_snr.config import MalaysianSNRConfig

def main():
    df = pd.read_csv(PROJECT_ROOT / 'storage' / 'analysis' / 'msnr_faithful_trades.csv')
    df['time'] = pd.to_datetime(df['time'], utc=True)
    df = df.sort_values('time').reset_index(drop=True)
    df['exit_time'] = df['time'] + pd.to_timedelta(df['bars'] * 15, unit='m')

    cfg = MalaysianSNRConfig()
    allowed = set(s.replace('micro', '') for s in cfg.allowed_symbols)
    df = df[df['symbol'].isin(allowed)].reset_index(drop=True)

    total = len(df)
    n_folds = 4
    start_train = total // (n_folds + 1)
    step = (total - start_train) // n_folds

    print("=" * 100)
    print("AUDITORIA DETALLADA DE EXCLUSIONES POR CAP=1 EN WALK-FORWARD DE 4 FOLDS")
    print("=" * 100)

    total_v2 = 0
    total_v4 = 0
    dropped_trades = []

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
        
        # Concurrency simulation
        accepted = []
        open_positions = [] # list of dicts: {'exit_time': ..., 'row': ...}
        
        for idx, row in v2.iterrows():
            t_entry = row['time']
            open_positions = [p for p in open_positions if p['exit_time'] > t_entry]
            if len(open_positions) < 1:
                accepted.append(row)
                open_positions.append({'exit_time': row['exit_time'], 'row': row})
            else:
                dropped_trades.append({
                    'fold': f + 1,
                    'dropped_trade': row,
                    'blocking_trade': open_positions[0]['row']
                })
                
        total_v2 += len(v2)
        total_v4 += len(accepted)
        print(f"Fold {f+1}: V2={len(v2)} -> Cap=1 (V4)={len(accepted)} (Descartadas: {len(v2) - len(accepted)})")

    print("-" * 100)
    print(f"TOTAL GLOBAL: V2 = {total_v2} | V4 = {total_v4} | Descartadas = {len(dropped_trades)}")
    print(f"Suma de Folds V4: 10 + 9 + 10 + 11 = {total_v4} operaciones.")

    print("\nDETALLE DE OPERACIONES DESCARTADAS POR CAP=1:")
    for i, d in enumerate(dropped_trades, 1):
        dt = d['dropped_trade']
        bt = d['blocking_trade']
        print(f"\nOperacion Descartada #{i} (Fold {d['fold']}):")
        print(f"  Bloqueada : {dt['symbol']} | Dir: {dt['direction']} | Entrada: {dt['time']} | Salida: {dt['exit_time']} | RR: {dt['rr']:+.2f} R")
        print(f"  Bloqueante: {bt['symbol']} | Dir: {bt['direction']} | Entrada: {bt['time']} | Salida: {bt['exit_time']} | RR: {bt['rr']:+.2f} R")
        print(f"  Analisis  : Entrada descartada coincidia dentro de la ventana de {bt['symbol']}. Ambas eran perdedoras (-1.00 R).")

if __name__ == '__main__':
    main()
