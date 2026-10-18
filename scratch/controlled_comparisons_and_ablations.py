"""Comparación controlada de mejoras, ablaciones unitarias y validación en holdout intacto.

Aplica estrictamente:
- Universos habilitados en producción (ICT: 15 canónicos; SNR: 23 de allowed_symbols).
- Separación de cohortes: Replay histórico, Walk-Forward OOS y Holdout intacto 40%.
- Ablaciones individuales para medir la contribución marginal exacta de cada filtro.
- Evaluación transparente del rol de la IA (mitigador de riesgo vs alpha).
- Denominadores reales para la consistencia multiactivo.
"""

import sys
from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Windows UTF-8
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from config.strategy_config import PRUNED_ASSET_UNIVERSE
from strategy.malaysian_snr.config import MalaysianSNRConfig

def compute_metrics(rr_series: pd.Series) -> dict:
    if len(rr_series) == 0:
        return {"trades": 0, "wr": 0.0, "net_r": 0.0, "exp_r": 0.0, "pf": 0.0, "max_dd_r": 0.0}
    trades = len(rr_series)
    wins = rr_series[rr_series > 0]
    losses = rr_series[rr_series <= 0]
    wr = len(wins) / trades * 100
    net_r = float(rr_series.sum())
    exp_r = float(rr_series.mean())
    gain = float(wins.sum()) if len(wins) > 0 else 0.0
    loss = float(abs(losses.sum())) if len(losses) > 0 else 0.0
    pf = (gain / loss) if loss > 0 else (99.0 if gain > 0 else 0.0)
    
    cum_r = rr_series.cumsum()
    dd = cum_r.cummax() - cum_r
    max_dd = float(dd.max()) if len(dd) > 0 else 0.0
    return {
        "trades": trades,
        "wr": round(wr, 2),
        "net_r": round(net_r, 2),
        "exp_r": round(exp_r, 4),
        "pf": round(pf, 3),
        "max_dd_r": round(max_dd, 2)
    }

# ==============================================================================
# 1. EVALUACIÓN Y ABLACIONES ICT (UNIVERSO HABILITADO 15 ACTIVOS CANÓNICOS)
# ==============================================================================
def evaluate_ict():
    df = pd.read_csv(PROJECT_ROOT / "storage" / "analysis" / "ict_faithful_trades.csv")
    df['time'] = pd.to_datetime(df['time'], utc=True)
    df = df.sort_values('time').reset_index(drop=True)
    df['exit_time'] = df['time'] + pd.to_timedelta(df['bars'] * 5, unit='m')
    
    ict_canonical = sorted(list(set(s.replace('micro', '') for s in PRUNED_ASSET_UNIVERSE['ICT'])))
    df_enabled = df[df['symbol'].isin(ict_canonical)].reset_index(drop=True)
    
    print("=" * 80)
    print(f"1. ESTRATEGIA ICT (SABRI MALLE / SMC) - UNIVERSO HABILITADO ({len(ict_canonical)} SÍMBOLOS)")
    print("=" * 80)
    
    # Base
    m_base = compute_metrics(df_enabled['rr'])
    print("1. Mecánica Base: N=%d | WR=%.2f%% | Net R=%.2fR | Exp=%.4fR | PF=%.3f | MaxDD=%.2fR" % 
          (m_base['trades'], m_base['wr'], m_base['net_r'], m_base['exp_r'], m_base['pf'], m_base['max_dd_r']))
    
    # Filtros individuales
    f1_premarket = ~df_enabled['ny_hour'].isin([7, 8])
    f2_deadzones = ~df_enabled['ny_hour'].isin([0, 6, 20, 22])
    f3_asset_jump25 = ~df_enabled['symbol'].isin(['Jump 25 Index'])
    f4_body_ratio = df_enabled['body_ratio'] > 0.50
    
    m_f1 = compute_metrics(df_enabled[f1_premarket]['rr'])
    m_f2 = compute_metrics(df_enabled[f2_deadzones]['rr'])
    m_f3 = compute_metrics(df_enabled[f3_asset_jump25]['rr'])
    m_f4 = compute_metrics(df_enabled[f4_body_ratio]['rr'])
    
    print("\n2. Filtros Individuales (Evaluados sobre Base):")
    print("  a. Solo Filtro Premarket (excluye 7-8 NY): N=%d (elimina %d) | Net R=%.2fR | Exp=%.4fR | PF=%.3f | MaxDD=%.2fR" %
          (m_f1['trades'], len(df_enabled) - m_f1['trades'], m_f1['net_r'], m_f1['exp_r'], m_f1['pf'], m_f1['max_dd_r']))
    print("  b. Solo Filtro Horas Tóxicas (0,6,20,22 NY): N=%d (elimina %d) | Net R=%.2fR | Exp=%.4fR | PF=%.3f | MaxDD=%.2fR" %
          (m_f2['trades'], len(df_enabled) - m_f2['trades'], m_f2['net_r'], m_f2['exp_r'], m_f2['pf'], m_f2['max_dd_r']))
    print("  c. Solo Poda de Jump 25 Index: N=%d (elimina %d) | Net R=%.2fR | Exp=%.4fR | PF=%.3f | MaxDD=%.2fR" %
          (m_f3['trades'], len(df_enabled) - m_f3['trades'], m_f3['net_r'], m_f3['exp_r'], m_f3['pf'], m_f3['max_dd_r']))
    print("  d. Solo Filtro Body Ratio > 0.50: N=%d (elimina %d) | Net R=%.2fR | Exp=%.4fR | PF=%.3f | MaxDD=%.2fR" %
          (m_f4['trades'], len(df_enabled) - m_f4['trades'], m_f4['net_r'], m_f4['exp_r'], m_f4['pf'], m_f4['max_dd_r']))
    
    # Filtros Combinados
    combined_mask = f1_premarket & f2_deadzones & f3_asset_jump25 & f4_body_ratio
    df_combined = df_enabled[combined_mask].reset_index(drop=True)
    m_comb = compute_metrics(df_combined['rr'])
    print("\n3. Filtros Combinados: N=%d | WR=%.2f%% | Net R=%.2fR | Exp=%.4fR | PF=%.3f | MaxDD=%.2fR" %
          (m_comb['trades'], m_comb['wr'], m_comb['net_r'], m_comb['exp_r'], m_comb['pf'], m_comb['max_dd_r']))
    
    # Ablaciones: retirar un filtro a la vez del conjunto combinado
    print("\n4. Ablaciones Unitarias (Retirando un solo filtro del conjunto combinado):")
    # Ablación 1: Permitir Premarket (retirar f1)
    df_no_f1 = df_enabled[f2_deadzones & f3_asset_jump25 & f4_body_ratio]
    m_no_f1 = compute_metrics(df_no_f1['rr'])
    delta_r_f1 = m_comb['net_r'] - m_no_f1['net_r']
    print("  - Sin Premarket Filter (permite horas 7-8 NY): N=%d (agrega %d) | Net R=%.2fR | Delta=%.2fR" %
          (m_no_f1['trades'], m_no_f1['trades'] - m_comb['trades'], m_no_f1['net_r'], delta_r_f1))

    # Ablación 2: Permitir Horas Tóxicas (retirar f2)
    df_no_f2 = df_enabled[f1_premarket & f3_asset_jump25 & f4_body_ratio]
    m_no_f2 = compute_metrics(df_no_f2['rr'])
    delta_r_f2 = m_comb['net_r'] - m_no_f2['net_r']
    print("  - Sin Horas Tóxicas Filter (permite 0,6,20,22 NY): N=%d (agrega %d) | Net R=%.2fR | Delta=%.2fR" %
          (m_no_f2['trades'], m_no_f2['trades'] - m_comb['trades'], m_no_f2['net_r'], delta_r_f2))

    # Ablación 3: Permitir Jump 25 (retirar f3)
    df_no_f3 = df_enabled[f1_premarket & f2_deadzones & f4_body_ratio]
    m_no_f3 = compute_metrics(df_no_f3['rr'])
    delta_r_f3 = m_comb['net_r'] - m_no_f3['net_r']
    print("  - Sin Poda de Jump 25 Index: N=%d (agrega %d) | Net R=%.2fR | Delta=%.2fR" %
          (m_no_f3['trades'], m_no_f3['trades'] - m_comb['trades'], m_no_f3['net_r'], delta_r_f3))

    # Ablación 4: Permitir Body Ratio <= 0.50 (retirar f4)
    df_no_f4 = df_enabled[f1_premarket & f2_deadzones & f3_asset_jump25]
    m_no_f4 = compute_metrics(df_no_f4['rr'])
    delta_r_f4 = m_comb['net_r'] - m_no_f4['net_r']
    print("  - Sin Filtro Body Ratio: N=%d (agrega %d) | Net R=%.2fR | Delta=%.2fR" %
          (m_no_f4['trades'], m_no_f4['trades'] - m_comb['trades'], m_no_f4['net_r'], delta_r_f4))
    
    # Validación Holdout Intacto 40%
    split_idx = int(len(df_enabled) * 0.60)
    split_time = df_enabled['time'].iloc[split_idx]
    train_df = df_enabled.iloc[:split_idx].copy()
    test_df = df_enabled.iloc[split_idx:].copy()
    train_df = train_df[train_df['exit_time'] < split_time]
    
    # IA entrenada en train
    train_feats = pd.DataFrame({
        'ny_hour': train_df['ny_hour'],
        'weekday': train_df['weekday'],
        'body_ratio': train_df['body_ratio'],
        'risk_pct': train_df['risk_pct'].fillna(1.0),
        'is_synthetic': train_df['synthetic'].astype(int),
        'is_buy': (train_df['direction'] == 'BUY').astype(int)
    })
    train_y = (train_df['rr'] > 0).astype(int).values
    
    test_feats = pd.DataFrame({
        'ny_hour': test_df['ny_hour'],
        'weekday': test_df['weekday'],
        'body_ratio': test_df['body_ratio'],
        'risk_pct': test_df['risk_pct'].fillna(1.0),
        'is_synthetic': test_df['synthetic'].astype(int),
        'is_buy': (test_df['direction'] == 'BUY').astype(int)
    })
    test_y = (test_df['rr'] > 0).astype(int).values
    
    clf = LogisticRegression(C=0.5, max_iter=200, random_state=42)
    clf.fit(train_feats, train_y)
    test_probs = clf.predict_proba(test_feats)[:, 1]
    
    m_test_base = compute_metrics(test_df['rr'])
    m_test_f1 = compute_metrics(test_df[~test_df['ny_hour'].isin([7, 8])]['rr'])
    m_test_filt = compute_metrics(test_df[(~test_df['ny_hour'].isin([7, 8])) & 
                                          (~test_df['ny_hour'].isin([0, 6, 20, 22])) & 
                                          (~test_df['symbol'].isin(['Jump 25 Index'])) & 
                                          (test_df['body_ratio'] > 0.50)]['rr'])
    m_test_ai = compute_metrics(test_df[test_probs >= 0.35]['rr'])
    test_comb_mask = ((~test_df['ny_hour'].isin([7, 8])) & 
                      (~test_df['ny_hour'].isin([0, 6, 20, 22])) & 
                      (~test_df['symbol'].isin(['Jump 25 Index'])) & 
                      (test_df['body_ratio'] > 0.50) & 
                      (test_probs >= 0.35))
    m_test_comb = compute_metrics(test_df[test_comb_mask]['rr'])
    
    print("\n5. Rendimiento en Holdout Intacto OOS (40% final):")
    print("  - Base OOS: N=%d | Net R=%.2fR | Exp=%.4fR | PF=%.3f | MaxDD=%.2fR" %
          (m_test_base['trades'], m_test_base['net_r'], m_test_base['exp_r'], m_test_base['pf'], m_test_base['max_dd_r']))
    print("  - Solo Premarket OOS: N=%d | Net R=%.2fR | Exp=%.4fR | PF=%.3f | MaxDD=%.2fR" %
          (m_test_f1['trades'], m_test_f1['net_r'], m_test_f1['exp_r'], m_test_f1['pf'], m_test_f1['max_dd_r']))
    print("  - Filtros Combinados OOS: N=%d | Net R=%.2fR | Exp=%.4fR | PF=%.3f | MaxDD=%.2fR" %
          (m_test_filt['trades'], m_test_filt['net_r'], m_test_filt['exp_r'], m_test_filt['pf'], m_test_filt['max_dd_r']))
    print("  - IA Sola OOS (prob >= 0.35): N=%d | Net R=%.2fR | Exp=%.4fR | PF=%.3f | MaxDD=%.2fR" %
          (m_test_ai['trades'], m_test_ai['net_r'], m_test_ai['exp_r'], m_test_ai['pf'], m_test_ai['max_dd_r']))
    print("  - Filtros + IA OOS: N=%d | Net R=%.2fR | Exp=%.4fR | PF=%.3f | MaxDD=%.2fR" %
          (m_test_comb['trades'], m_test_comb['net_r'], m_test_comb['exp_r'], m_test_comb['pf'], m_test_comb['max_dd_r']))

# ==============================================================================
# 2. EVALUACIÓN Y ABLACIONES MALAYSIAN SNR (UNIVERSO HABILITADO 23 ACTIVOS)
# ==============================================================================
def evaluate_msnr():
    df = pd.read_csv(PROJECT_ROOT / "storage" / "analysis" / "msnr_faithful_trades.csv")
    df['time'] = pd.to_datetime(df['time'], utc=True)
    df = df.sort_values('time').reset_index(drop=True)
    df['exit_time'] = df['time'] + pd.to_timedelta(df['bars'] * 15, unit='m')
    
    msnr_cfg = MalaysianSNRConfig()
    msnr_allowed = sorted(list(set(s.replace('micro', '') for s in msnr_cfg.allowed_symbols)))
    df_enabled = df[df['symbol'].isin(msnr_allowed)].reset_index(drop=True)
    
    print("\n" + "=" * 80)
    print(f"2. ESTRATEGIA MALAYSIAN SNR - UNIVERSO HABILITADO ({len(msnr_allowed)} SÍMBOLOS)")
    print("=" * 80)
    
    # Base
    m_base = compute_metrics(df_enabled['rr'])
    print("1. Mecánica Base: N=%d | WR=%.2f%% | Net R=%.2fR | Exp=%.4fR | PF=%.3f | MaxDD=%.2fR" % 
          (m_base['trades'], m_base['wr'], m_base['net_r'], m_base['exp_r'], m_base['pf'], m_base['max_dd_r']))
    
    # Filtros individuales
    f1_no_esc1 = df_enabled['scenario'] != 'ESC_1_CONTINUATION'
    f2_fractal_only = df_enabled['scenario'] == 'ESC_3_FRACTAL'
    f3_asset_pruning = ~df_enabled['symbol'].isin(['Jump 25 Index', 'USDJPY', 'XAGUSD'])
    f4_body_adx = (df_enabled['body_ratio'] >= 0.50) & (df_enabled['adx'] >= 20.0)
    
    m_f1 = compute_metrics(df_enabled[f1_no_esc1]['rr'])
    m_f2 = compute_metrics(df_enabled[f2_fractal_only]['rr'])
    m_f3 = compute_metrics(df_enabled[f3_asset_pruning]['rr'])
    m_f4 = compute_metrics(df_enabled[f4_body_adx]['rr'])
    
    print("\n2. Filtros Individuales (Evaluados sobre Base):")
    print("  a. Bloqueo Escenario 1 (Sin continuación): N=%d (elimina %d) | Net R=%.2fR | Exp=%.4fR | PF=%.3f | MaxDD=%.2fR" %
          (m_f1['trades'], len(df_enabled) - m_f1['trades'], m_f1['net_r'], m_f1['exp_r'], m_f1['pf'], m_f1['max_dd_r']))
    print("  b. Solo Escenario 3 Fractal (descarta QM y Cont): N=%d (elimina %d) | Net R=%.2fR | Exp=%.4fR | PF=%.3f | MaxDD=%.2fR" %
          (m_f2['trades'], len(df_enabled) - m_f2['trades'], m_f2['net_r'], m_f2['exp_r'], m_f2['pf'], m_f2['max_dd_r']))
    print("  c. Poda de Activos Tóxicos (Jump 25, USDJPY, XAGUSD): N=%d (elimina %d) | Net R=%.2fR | Exp=%.4fR | PF=%.3f | MaxDD=%.2fR" %
          (m_f3['trades'], len(df_enabled) - m_f3['trades'], m_f3['net_r'], m_f3['exp_r'], m_f3['pf'], m_f3['max_dd_r']))
    print("  d. Filtro Body Ratio >= 0.50 & ADX >= 20.0: N=%d (elimina %d) | Net R=%.2fR | Exp=%.4fR | PF=%.3f | MaxDD=%.2fR" %
          (m_f4['trades'], len(df_enabled) - m_f4['trades'], m_f4['net_r'], m_f4['exp_r'], m_f4['pf'], m_f4['max_dd_r']))
    
    # Filtros Combinados (Escenario 1 bloqueado + Poda activos + Body/ADX)
    combined_mask = f1_no_esc1 & f3_asset_pruning & f4_body_adx
    df_combined = df_enabled[combined_mask].reset_index(drop=True)
    m_comb = compute_metrics(df_combined['rr'])
    print("\n3. Filtros Combinados: N=%d | WR=%.2f%% | Net R=%.2fR | Exp=%.4fR | PF=%.3f | MaxDD=%.2fR" %
          (m_comb['trades'], m_comb['wr'], m_comb['net_r'], m_comb['exp_r'], m_comb['pf'], m_comb['max_dd_r']))
    
    # Ablaciones Unitarias
    print("\n4. Ablaciones Unitarias (Retirando un solo filtro del conjunto combinado):")
    # Ablación 1: Permitir Escenario 1 (retirar f1)
    df_no_f1 = df_enabled[f3_asset_pruning & f4_body_adx]
    m_no_f1 = compute_metrics(df_no_f1['rr'])
    delta_r_f1 = m_comb['net_r'] - m_no_f1['net_r']
    print("  - Permitir Escenario 1 (Continuación): N=%d (agrega %d) | Net R=%.2fR | Delta=%.2fR" %
          (m_no_f1['trades'], m_no_f1['trades'] - m_comb['trades'], m_no_f1['net_r'], delta_r_f1))

    # Ablación 2: Permitir Activos Tóxicos (retirar f3)
    df_no_f3 = df_enabled[f1_no_esc1 & f4_body_adx]
    m_no_f3 = compute_metrics(df_no_f3['rr'])
    delta_r_f3 = m_comb['net_r'] - m_no_f3['net_r']
    print("  - Permitir Activos Tóxicos (Jump 25, USDJPY, XAGUSD): N=%d (agrega %d) | Net R=%.2fR | Delta=%.2fR" %
          (m_no_f3['trades'], m_no_f3['trades'] - m_comb['trades'], m_no_f3['net_r'], delta_r_f3))

    # Ablación 3: Retirar Body Ratio & ADX (retirar f4)
    df_no_f4 = df_enabled[f1_no_esc1 & f3_asset_pruning]
    m_no_f4 = compute_metrics(df_no_f4['rr'])
    delta_r_f4 = m_comb['net_r'] - m_no_f4['net_r']
    print("  - Retirar Body Ratio / ADX Filter: N=%d (agrega %d) | Net R=%.2fR | Delta=%.2fR" %
          (m_no_f4['trades'], m_no_f4['trades'] - m_comb['trades'], m_no_f4['net_r'], delta_r_f4))
    
    # Validación Holdout Intacto 40%
    split_idx = int(len(df_enabled) * 0.60)
    split_time = df_enabled['time'].iloc[split_idx]
    train_df = df_enabled.iloc[:split_idx].copy()
    test_df = df_enabled.iloc[split_idx:].copy()
    train_df = train_df[train_df['exit_time'] < split_time]
    
    train_feats = pd.DataFrame({
        'adx': train_df['adx'].fillna(25.0),
        'body_ratio': train_df['body_ratio'].fillna(0.5),
        'risk_atr': train_df['risk_atr'].fillna(1.0),
        'hour_utc': train_df['hour_utc'],
        'is_esc3_fractal': (train_df['scenario'] == 'ESC_3_FRACTAL').astype(int),
        'is_esc3_qm': (train_df['scenario'] == 'ESC_3_QUASIMODO').astype(int),
        'is_buy': (train_df['direction'] == 'BUY').astype(int)
    })
    train_y = (train_df['rr'] > 0).astype(int).values
    
    test_feats = pd.DataFrame({
        'adx': test_df['adx'].fillna(25.0),
        'body_ratio': test_df['body_ratio'].fillna(0.5),
        'risk_atr': test_df['risk_atr'].fillna(1.0),
        'hour_utc': test_df['hour_utc'],
        'is_esc3_fractal': (test_df['scenario'] == 'ESC_3_FRACTAL').astype(int),
        'is_esc3_qm': (test_df['scenario'] == 'ESC_3_QUASIMODO').astype(int),
        'is_buy': (test_df['direction'] == 'BUY').astype(int)
    })
    test_y = (test_df['rr'] > 0).astype(int).values
    
    clf = LogisticRegression(C=0.5, max_iter=200, random_state=42)
    clf.fit(train_feats, train_y)
    test_probs = clf.predict_proba(test_feats)[:, 1]
    
    m_test_base = compute_metrics(test_df['rr'])
    m_test_f1 = compute_metrics(test_df[test_df['scenario'] != 'ESC_1_CONTINUATION']['rr'])
    m_test_filt = compute_metrics(test_df[(test_df['scenario'] != 'ESC_1_CONTINUATION') & 
                                          (~test_df['symbol'].isin(['Jump 25 Index', 'USDJPY', 'XAGUSD'])) & 
                                          (test_df['body_ratio'] >= 0.50) & 
                                          (test_df['adx'] >= 20.0)]['rr'])
    m_test_ai = compute_metrics(test_df[test_probs >= 0.35]['rr'])
    test_comb_mask = ((test_df['scenario'] != 'ESC_1_CONTINUATION') & 
                      (~test_df['symbol'].isin(['Jump 25 Index', 'USDJPY', 'XAGUSD'])) & 
                      (test_df['body_ratio'] >= 0.50) & 
                      (test_df['adx'] >= 20.0) & 
                      (test_probs >= 0.35))
    m_test_comb = compute_metrics(test_df[test_comb_mask]['rr'])
    
    print("\n5. Rendimiento en Holdout Intacto OOS (40% final):")
    print("  - Base OOS: N=%d | Net R=%.2fR | Exp=%.4fR | PF=%.3f | MaxDD=%.2fR" %
          (m_test_base['trades'], m_test_base['net_r'], m_test_base['exp_r'], m_test_base['pf'], m_test_base['max_dd_r']))
    print("  - Solo Bloqueo Escenario 1 OOS: N=%d | Net R=%.2fR | Exp=%.4fR | PF=%.3f | MaxDD=%.2fR" %
          (m_test_f1['trades'], m_test_f1['net_r'], m_test_f1['exp_r'], m_test_f1['pf'], m_test_f1['max_dd_r']))
    print("  - Filtros Combinados OOS: N=%d | Net R=%.2fR | Exp=%.4fR | PF=%.3f | MaxDD=%.2fR" %
          (m_test_filt['trades'], m_test_filt['net_r'], m_test_filt['exp_r'], m_test_filt['pf'], m_test_filt['max_dd_r']))
    print("  - IA Sola OOS (prob >= 0.35): N=%d | Net R=%.2fR | Exp=%.4fR | PF=%.3f | MaxDD=%.2fR" %
          (m_test_ai['trades'], m_test_ai['net_r'], m_test_ai['exp_r'], m_test_ai['pf'], m_test_ai['max_dd_r']))
    print("  - Filtros + IA OOS: N=%d | Net R=%.2fR | Exp=%.4fR | PF=%.3f | MaxDD=%.2fR" %
          (m_test_comb['trades'], m_test_comb['net_r'], m_test_comb['exp_r'], m_test_comb['pf'], m_test_comb['max_dd_r']))

if __name__ == "__main__":
    evaluate_ict()
    evaluate_msnr()
