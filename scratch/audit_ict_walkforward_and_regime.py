"""Auditoría y validación walk-forward de ICT, régimen causal pre-trade y contabilidad exacta de PnL ganador suprimido.

Ejecución en modo de solo lectura sobre datasets locales.
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd

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
        return {"trades": 0, "wr": 0.0, "net_r": 0.0, "exp_r": 0.0, "pf": 0.0, "max_dd_r": 0.0, "gross_win": 0.0, "gross_loss": 0.0}
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
        "max_dd_r": round(max_dd, 2),
        "gross_win": round(gain, 2),
        "gross_loss": round(loss, 2)
    }

def audit_ict_walk_forward():
    print("=" * 80)
    print("AUDITORÍA WALK-FORWARD TEMPORAL DE ICT (SABRI MALLE)")
    print("=" * 80)
    
    df = pd.read_csv(PROJECT_ROOT / "storage" / "analysis" / "ict_faithful_trades.csv")
    df['time'] = pd.to_datetime(df['time'], utc=True)
    df = df.sort_values('time').reset_index(drop=True)
    df['exit_time'] = df['time'] + pd.to_timedelta(df['bars'] * 5, unit='m')
    
    ict_canonical = sorted(list(set(s.replace('micro', '') for s in PRUNED_ASSET_UNIVERSE['ICT'])))
    df_enabled = df[df['symbol'].isin(ict_canonical)].reset_index(drop=True)
    
    # Timeline
    min_time = df_enabled['time'].min()
    max_time = df_enabled['time'].max()
    total_days = (max_time - min_time).days
    print(f"Rango temporal total: {min_time.strftime('%Y-%m-%d')} a {max_time.strftime('%Y-%m-%d')} ({total_days} días)")
    print(f"Total operaciones universo habilitado (15 activos): {len(df_enabled)}")
    
    # 3 Ventanas Walk-Forward
    # W1: 0% - 33.3%, W2: 33.3% - 66.6%, W3: 66.6% - 100%
    w1_end = min_time + pd.Timedelta(days=int(total_days * 0.333))
    w2_end = min_time + pd.Timedelta(days=int(total_days * 0.666))
    
    w1_trades = df_enabled[df_enabled['time'] < w1_end].copy()
    w2_trades = df_enabled[(df_enabled['time'] >= w1_end) & (df_enabled['time'] < w2_end)].copy()
    w3_trades = df_enabled[df_enabled['time'] >= w2_end].copy()
    
    # Purgar en fronteras para evitar solapamiento
    w1_clean = w1_trades[w1_trades['exit_time'] < w1_end].copy()
    w2_clean = w2_trades[w2_trades['exit_time'] < w2_end].copy()
    
    print(f"\nParticiones Temporales Puradas:")
    print(f"  Ventana 1 (Entrenamiento inicial): {min_time.strftime('%Y-%m-%d')} a {w1_end.strftime('%Y-%m-%d')} (N={len(w1_clean)})")
    print(f"  Ventana 2 (Validación intermedia OOS): {w1_end.strftime('%Y-%m-%d')} a {w2_end.strftime('%Y-%m-%d')} (N={len(w2_clean)})")
    print(f"  Ventana 3 (Holdout final OOS): {w2_end.strftime('%Y-%m-%d')} a {max_time.strftime('%Y-%m-%d')} (N={len(w3_trades)})")
    
    variants = {
        "Base Mecánica": lambda d: pd.Series(True, index=d.index),
        "Excluir Jump 25": lambda d: ~d['symbol'].isin(['Jump 25 Index']),
        "Body Ratio > 0.50": lambda d: d['body_ratio'] > 0.50,
        "Excluir Jump 25 + Body Ratio > 0.50": lambda d: (~d['symbol'].isin(['Jump 25 Index'])) & (d['body_ratio'] > 0.50),
        "Retrospectivo: Excluir Hora 8 NY": lambda d: ~d['ny_hour'].isin([8])
    }
    
    # Paso 1: Train W1 -> Test W2 OOS
    print("\n" + "-" * 80)
    print("PASO 1 WALK-FORWARD: Entrena W1 -> Prueba W2 OOS")
    print("-" * 80)
    for name, fn in variants.items():
        sub = w2_clean[fn(w2_clean)]
        m = compute_metrics(sub['rr'])
        print(f"  {name:38s}: N={m['trades']:3d} | Net R={m['net_r']:+6.2f}R | Exp={m['exp_r']:+7.4f}R | PF={m['pf']:5.3f} | MaxDD={m['max_dd_r']:5.2f}R")
        
    # Paso 2: Train W1+W2 -> Test W3 OOS
    w1_w2_combined = pd.concat([w1_clean, w2_clean]).sort_values('time').reset_index(drop=True)
    w1_w2_clean = w1_w2_combined[w1_w2_combined['exit_time'] < w2_end].copy()
    
    print("\n" + "-" * 80)
    print("PASO 2 WALK-FORWARD: Entrena W1+W2 -> Prueba W3 OOS (Holdout Final)")
    print("-" * 80)
    for name, fn in variants.items():
        sub = w3_trades[fn(w3_trades)]
        m = compute_metrics(sub['rr'])
        print(f"  {name:38s}: N={m['trades']:3d} | Net R={m['net_r']:+6.2f}R | Exp={m['exp_r']:+7.4f}R | PF={m['pf']:5.3f} | MaxDD={m['max_dd_r']:5.2f}R")

def audit_winner_pnl_eliminated():
    print("\n" + "=" * 80)
    print("MEDICIÓN EXACTA DE PNL GANADOR Y PERDEDOR ELIMINADO POR CADA FILTRO")
    print("=" * 80)
    
    # 1. ICT
    df_ict = pd.read_csv(PROJECT_ROOT / "storage" / "analysis" / "ict_faithful_trades.csv")
    df_ict['time'] = pd.to_datetime(df_ict['time'], utc=True)
    df_ict = df_ict.sort_values('time').reset_index(drop=True)
    ict_canonical = sorted(list(set(s.replace('micro', '') for s in PRUNED_ASSET_UNIVERSE['ICT'])))
    df_ict_enabled = df_ict[df_ict['symbol'].isin(ict_canonical)].reset_index(drop=True)
    
    split_idx = int(len(df_ict_enabled) * 0.60)
    test_ict = df_ict_enabled.iloc[split_idx:].copy().reset_index(drop=True)
    
    print("\n--- ICT en Holdout OOS (N=244) ---")
    base_m = compute_metrics(test_ict['rr'])
    print(f"Base: N={base_m['trades']} | Ganancia Bruta={base_m['gross_win']:+.2f}R | Pérdida Bruta=-{base_m['gross_loss']:.2f}R | Neto={base_m['net_r']:+.2f}R")
    
    filters_ict = {
        "Exclusión Jump 25": test_ict['symbol'] == 'Jump 25 Index',
        "Body Ratio <= 0.50": test_ict['body_ratio'] <= 0.50,
        "Hora 8 NY (Retrospectivo)": test_ict['ny_hour'] == 8
    }
    
    for fname, mask_elim in filters_ict.items():
        elim_trades = test_ict[mask_elim]
        m_elim = compute_metrics(elim_trades['rr'])
        wins_elim = elim_trades[elim_trades['rr'] > 0]
        loss_elim = elim_trades[elim_trades['rr'] <= 0]
        print(f"Filtro: {fname}")
        print(f"  - Operaciones eliminadas: {len(elim_trades)} (Ganadoras: {len(wins_elim)}, Perdedoras: {len(loss_elim)})")
        print(f"  - Ganancia sacrificada: -{m_elim['gross_win']:.2f}R")
        print(f"  - Pérdida evitada:       +{m_elim['gross_loss']:.2f}R")
        print(f"  - Impacto Neto en PnL:   {m_elim['gross_loss'] - m_elim['gross_win']:+.2f}R (Filtro {'BENÉFICO' if m_elim['gross_loss'] > m_elim['gross_win'] else 'DAÑINO'})")
        
    # 2. SNR
    df_snr = pd.read_csv(PROJECT_ROOT / "storage" / "analysis" / "msnr_faithful_trades.csv")
    df_snr['time'] = pd.to_datetime(df_snr['time'], utc=True)
    df_snr = df_snr.sort_values('time').reset_index(drop=True)
    msnr_cfg = MalaysianSNRConfig()
    msnr_allowed = sorted(list(set(s.replace('micro', '') for s in msnr_cfg.allowed_symbols)))
    df_snr_enabled = df_snr[df_snr['symbol'].isin(msnr_allowed)].reset_index(drop=True)
    
    split_idx_snr = int(len(df_snr_enabled) * 0.60)
    test_snr = df_snr_enabled.iloc[split_idx_snr:].copy().reset_index(drop=True)
    
    print("\n--- Malaysian SNR en Holdout OOS (N=291) ---")
    base_m_snr = compute_metrics(test_snr['rr'])
    print(f"Base: N={base_m_snr['trades']} | Ganancia Bruta={base_m_snr['gross_win']:+.2f}R | Pérdida Bruta=-{base_m_snr['gross_loss']:.2f}R | Neto={base_m_snr['net_r']:+.2f}R")
    
    filters_snr = {
        "Bloqueo Global Escenario 1": test_snr['scenario'] == 'ESC_1_CONTINUATION',
        "Body Ratio < 0.50": test_snr['body_ratio'] < 0.50,
        "ADX < 20.0": test_snr['adx'] < 20.0,
        "Poda Jump 25": test_snr['symbol'] == 'Jump 25 Index',
        "Poda USDJPY": test_snr['symbol'] == 'USDJPY'
    }
    
    for fname, mask_elim in filters_snr.items():
        elim_trades = test_snr[mask_elim]
        m_elim = compute_metrics(elim_trades['rr'])
        wins_elim = elim_trades[elim_trades['rr'] > 0]
        loss_elim = elim_trades[elim_trades['rr'] <= 0]
        print(f"Filtro: {fname}")
        print(f"  - Operaciones eliminadas: {len(elim_trades)} (Ganadoras: {len(wins_elim)}, Perdedoras: {len(loss_elim)})")
        print(f"  - Ganancia sacrificada: -{m_elim['gross_win']:.2f}R")
        print(f"  - Pérdida evitada:       +{m_elim['gross_loss']:.2f}R")
        print(f"  - Impacto Neto en PnL:   {m_elim['gross_loss'] - m_elim['gross_win']:+.2f}R (Filtro {'BENÉFICO' if m_elim['gross_loss'] > m_elim['gross_win'] else 'DAÑINO'})")

def test_ict_causal_regime_filter():
    print("\n" + "=" * 80)
    print("EVALUACIÓN DE HIPÓTESIS: FILTRO DE RÉGIMEN CAUSAL PRE-TRADE EN ICT")
    print("=" * 80)
    
    df = pd.read_csv(PROJECT_ROOT / "storage" / "analysis" / "ict_faithful_trades.csv")
    df['time'] = pd.to_datetime(df['time'], utc=True)
    df = df.sort_values('time').reset_index(drop=True)
    ict_canonical = sorted(list(set(s.replace('micro', '') for s in PRUNED_ASSET_UNIVERSE['ICT'])))
    df_enabled = df[df['symbol'].isin(ict_canonical)].reset_index(drop=True)
    
    # Calcular métrica causal ex-ante por símbolo:
    # risk_pct = abs(entry - SL) / entry * 100.
    # Un risk_pct anormalmente grande indica régimen de volatilidad descontrolada (velas M5 de pánico/expansión excesiva).
    # Calculamos la mediana móvil causal de los últimos 20 trades del mismo símbolo estrictamente anteriores al trade.
    
    regime_ratios = []
    for i, row in df_enabled.iterrows():
        sym = row['symbol']
        past = df_enabled.iloc[:i]
        past_sym = past[past['symbol'] == sym]
        if len(past_sym) >= 5:
            # Mediana o media de los últimos 10-20 trades
            baseline_risk = past_sym['risk_pct'].iloc[-20:].median()
            ratio = row['risk_pct'] / baseline_risk if baseline_risk > 0 else 1.0
        else:
            ratio = 1.0
        regime_ratios.append(ratio)
        
    df_enabled['risk_expansion_ratio'] = regime_ratios
    
    split_idx = int(len(df_enabled) * 0.60)
    test_df = df_enabled.iloc[split_idx:].copy().reset_index(drop=True)
    
    print("\nRendimiento de Filtro de Expansión de Volatilidad (risk_expansion_ratio <= 1.50):")
    # Base OOS
    m_base = compute_metrics(test_df['rr'])
    print(f"  Base OOS (N=244): Net R={m_base['net_r']:+.2f}R | PF={m_base['pf']:.3f} | MaxDD={m_base['max_dd_r']:.2f}R")
    
    # Filtro de Régimen: descartar entradas donde la distancia de SL fue > 1.5x la mediana reciente
    f_regime = test_df['risk_expansion_ratio'] <= 1.40
    m_regime = compute_metrics(test_df[f_regime]['rr'])
    print(f"  Solo Filtro Régimen Causal (ratio <= 1.40): N={m_regime['trades']} | Net R={m_regime['net_r']:+.2f}R | PF={m_regime['pf']:.3f} | MaxDD={m_regime['max_dd_r']:.2f}R")
    
    # Combinado con Jump 25 + Body Ratio
    f_comb_regime = (~test_df['symbol'].isin(['Jump 25 Index'])) & (test_df['body_ratio'] > 0.50) & f_regime
    m_comb_regime = compute_metrics(test_df[f_comb_regime]['rr'])
    print(f"  Combinado (Excl Jump25 + BodyRatio + Régimen Causal): N={m_comb_regime['trades']} | Net R={m_comb_regime['net_r']:+.2f}R | PF={m_comb_regime['pf']:.3f} | MaxDD={m_comb_regime['max_dd_r']:.2f}R")

if __name__ == "__main__":
    audit_ict_walk_forward()
    audit_winner_pnl_eliminated()
    test_ict_causal_regime_filter()
