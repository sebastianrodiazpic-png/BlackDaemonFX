"""
Curación del Dataset de Operaciones Sintéticas para Meta-Labeling
BlackDaemonFX - Fase 1: Calibración y Microestructura 24/7

Extrae operaciones de sintéticos de storage/live_trading_bot.sqlite3,
excluye activos tóxicos podados, depura features de killzone bancaria
e integra métricas de microestructura y Criterio Humano.
"""

import sys
import os
from pathlib import Path

# Fix shadowing of standard library 'operator' by local tools/operator directory
if sys.path and (sys.path[0].endswith("tools") or sys.path[0].endswith("tools\\") or sys.path[0].endswith("tools/")):
    sys.path.pop(0)

import sqlite3
import json
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

EXCLUDED_TOXIC_SYMBOLS = {
    'Volatility 100 (1s) Index',
    'Crash 300 Index',
    'USDJPY',
    'USDJPYmicro',
    'EURUSD',
    'EURUSDmicro',
    'US SP 500'
}

SYNTHETIC_FEATURE_NAMES = [
    "trade_score",
    "confirmation_percentage",
    "confirmations_ratio",
    "adx",
    "adx_normalized",
    "atr_ratio",
    "structure_aligned",
    "spread_ratio",
    "spread_to_sl_ratio",
    "planned_rr",
    "direction_buy",
    "human_criteria_score",
    "is_boom",
    "is_crash",
    "is_volatility",
    "is_step",
    "is_jump"
]

def curate_synthetic_dataset(db_path: str | None = None, output_path: str | None = None) -> pd.DataFrame:
    db = db_path or str(PROJECT_ROOT / "storage" / "live_trading_bot.sqlite3")
    out = output_path or str(PROJECT_ROOT / "storage" / "ai" / "synthetic_meta_dataset_curated.csv")
    
    os.makedirs(os.path.dirname(out), exist_ok=True)
    
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    
    query = """
        SELECT id, instrument, direction, status, result, entry_time, exit_time, 
               net_pnl, realized_rr, planned_rr, strategy_version, details_json
        FROM trades
        WHERE status = 'CLOSED'
          AND result IN ('WIN', 'LOSS', 'BREAKEVEN')
          AND (
              instrument LIKE '%Index%' 
              OR instrument LIKE '%Vol%' 
              OR instrument LIKE '%Boom%' 
              OR instrument LIKE '%Crash%' 
              OR instrument LIKE '%Step%' 
              OR instrument LIKE '%Jump%'
          )
        ORDER BY id ASC
    """
    cur.execute(query)
    rows = cur.fetchall()
    conn.close()
    
    records = []
    for r in rows:
        tid, inst, direction, status, result, entry_time, exit_time, net_pnl, r_rr, p_rr, strat, d_json = r
        
        # Filtro de activos tóxicos podados
        if inst in EXCLUDED_TOXIC_SYMBOLS:
            continue
            
        if not d_json:
            continue
            
        try:
            d = json.loads(d_json)
        except Exception:
            continue
            
        meta = d.get('metadata', {})
        snap = meta.get('entry_learning_snapshot') or d.get('entry_learning_snapshot') or {}
        raw_feats = snap.get('features', {})
        
        # Criterio Humano (si existe en entry_decision)
        hc = d.get('entry_decision', {}).get('human_criteria', {})
        hc_score = hc.get('score')
        if hc_score is None:
            # Fallback proporcional al trade_score si no existía el módulo
            base_score = float(raw_feats.get('trade_score', 0.8) or 0.8)
            hc_score = base_score * 100.0 if base_score <= 1.0 else base_score
            
        # Target binario y realized R
        realized_r = float(r_rr) if r_rr is not None else (1.0 if result == 'WIN' else (-1.0 if result == 'LOSS' else 0.0))
        
        if result == 'WIN' or realized_r >= 0.5 or (net_pnl and net_pnl > 0.05):
            target_binary = 1
        elif result == 'LOSS' or realized_r < 0.0 or (net_pnl and net_pnl < -0.05):
            target_binary = 0
        else:
            # Breakeven puro: no penalizar como pérdida si net_pnl >= 0
            target_binary = 1 if (net_pnl is not None and net_pnl >= 0.0) else 0

        # Vector de features específico de sintéticos
        trade_score = float(raw_feats.get('trade_score', 0.8) or 0.8)
        conf_pct = float(raw_feats.get('confirmation_percentage', 0.85) or 0.85)
        conf_ratio = float(raw_feats.get('confirmations_ratio', 1.0) or 1.0)
        adx = float(raw_feats.get('adx', 25.0) or 25.0)
        adx_norm = float(raw_feats.get('adx_normalized', adx / 50.0) or (adx / 50.0))
        atr_ratio = float(raw_feats.get('atr_ratio', 0.02) or 0.02)
        struct_aligned = float(raw_feats.get('structure_aligned', 1.0) or 1.0)
        spread_ratio = float(raw_feats.get('spread_ratio', 0.0005) or 0.0005)
        spread_sl = float(raw_feats.get('spread_to_sl_ratio', 0.02) or 0.02)
        planned_rr = float(raw_feats.get('planned_rr', p_rr or 2.0) or 2.0)
        dir_buy = 1.0 if str(direction).upper() == 'BUY' else 0.0
        
        inst_u = inst.upper()
        is_boom = 1.0 if 'BOOM' in inst_u else 0.0
        is_crash = 1.0 if 'CRASH' in inst_u else 0.0
        is_vol = 1.0 if ('VOLATILITY' in inst_u or 'VOLSWITCH' in inst_u) else 0.0
        is_step = 1.0 if 'STEP' in inst_u else 0.0
        is_jump = 1.0 if 'JUMP' in inst_u else 0.0

        record = {
            "trade_id": tid,
            "instrument": inst,
            "direction": direction,
            "entry_time": entry_time,
            "strategy_version": strat,
            "trade_score": trade_score,
            "confirmation_percentage": conf_pct,
            "confirmations_ratio": conf_ratio,
            "adx": adx,
            "adx_normalized": adx_norm,
            "atr_ratio": atr_ratio,
            "structure_aligned": struct_aligned,
            "spread_ratio": spread_ratio,
            "spread_to_sl_ratio": spread_sl,
            "planned_rr": planned_rr,
            "direction_buy": dir_buy,
            "human_criteria_score": float(hc_score),
            "is_boom": is_boom,
            "is_crash": is_crash,
            "is_volatility": is_vol,
            "is_step": is_step,
            "is_jump": is_jump,
            "result": result,
            "net_pnl": net_pnl,
            "realized_rr": realized_r,
            "target": target_binary
        }
        records.append(record)
        
    df = pd.DataFrame(records)
    print(f"Dataset curado: {len(df)} operaciones sintéticas.")
    print(f"Distribución del target: Wins/Positivos = {sum(df['target'] == 1)} ({sum(df['target'] == 1)/len(df)*100:.1f}%), Losses = {sum(df['target'] == 0)}")
    
    df.to_csv(out, index=False)
    print(f"Guardado exitosamente en: {out}")
    return df

if __name__ == '__main__':
    curate_synthetic_dataset()
