"""Audit Replay: Comparativa Cuantitativa de Mejoras ORB (2 Años).

Compara directamente la estrategia ORB actual frente a las mejoras extraídas
del análisis de los videos (Cutoff 11:30 NY, Retest de Alta Calidad/Envolvente,
Filtro de Liquidez Macro PDH/PDL, Stop Loss Técnico Ceñido y Calibración de TP).
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from strategy.orb import new_york_orb as orb
from strategy.orb.asset_rules import (
    audit_volume_confirmation,
    check_range_amplitude,
    evaluate_retest_quality,
    default_asset_profiles,
)

SYMBOLS = [
    'US Tech 100',
    'Wall Street 30',
    'US SP 500',
    'XAUUSD',
    'XAGUSD',
    'EURUSD',
    'BTCUSD',
    'US Oil',
]

OUT = ROOT / 'storage/analysis/orb_improvements_audit'
START = pd.Timestamp('2024-10-03', tz='UTC')
END = pd.Timestamp('2026-10-03', tz='UTC')

VARIANTS = [
    'BASELINE_CURRENT',
    'VAR1_CUTOFF_1130',
    'VAR2_HIGH_QUALITY_RETEST',
    'VAR3_MACRO_LIQUIDITY',
    'VAR4_TIGHT_SL_ROSELL',
    'VAR5_CALIBRATED_TP',
    'VAR6_FULL_OPTIMIZED',
]


def filename(symbol: str) -> str:
    return symbol.replace(' ', '_') + '_M5.csv'


def load(symbol: str):
    paths = [
        ROOT / 'storage/analysis/orb_nunez_2y/history' / filename(symbol),
        ROOT / 'data/historical' / filename(symbol),
        ROOT / 'data/forex_historical' / filename(symbol),
    ]
    frames = []
    for p in paths:
        if p.exists():
            df = pd.read_csv(p)
            df['time'] = pd.to_datetime(df['time'], utc=True)
            frames.append(df)
            break
    if not frames:
        return pd.DataFrame(), {'status': 'NO_DATA'}
    df = pd.concat(frames, ignore_index=True).drop_duplicates('time', keep='last').sort_values('time')
    df = df[(df.time >= START - pd.Timedelta(days=30)) & (df.time < END)].reset_index(drop=True)
    bad = (
        (~np.isfinite(df[['open', 'high', 'low', 'close']]).all(axis=1))
        | (df.high < df[['open', 'close', 'low']].max(axis=1))
        | (df.low > df[['open', 'close', 'high']].min(axis=1))
    )
    df = df[~bad].reset_index(drop=True)
    df['time_ny'] = df.time.dt.tz_convert('America/New_York')
    df['ny_date'] = df.time_ny.dt.date
    df['ny_minute'] = df.time_ny.dt.hour * 60 + df.time_ny.dt.minute
    return df, {'status': 'AVAILABLE', 'bars': len(df)}


def get_macro_liquidity(df: pd.DataFrame, idx: int, day) -> dict:
    """Calcula PDH (Previous Day High) y PDL (Previous Day Low)."""
    known = df.iloc[:idx]
    prev_days = known[known.ny_date < day]
    if prev_days.empty:
        return {'PDH': None, 'PDL': None}
    last_day = prev_days.ny_date.iloc[-1]
    prior = prev_days[prev_days.ny_date == last_day]
    return {
        'PDH': float(prior.high.max()),
        'PDL': float(prior.low.min()),
    }


def simulate_trade_dual_leg(
    df: pd.DataFrame,
    entry_idx: int,
    direction: str,
    stop_loss: float,
    point: float,
    tp1_rr: float = 1.0,
    tp2_rr: float = 2.0,
) -> dict | None:
    """Simula ejecución dual-leg: 0.5% riesgo en Leg1 y 0.5% en Leg2."""
    if entry_idx >= len(df):
        return None
    side = 1.0 if direction == 'BUY' else -1.0
    bar = df.iloc[entry_idx]
    spread = max(0.0, float(bar.spread) * point)
    entry_price = float(bar.open) + (spread if side == 1.0 else 0.0)
    risk_distance = side * (entry_price - stop_loss)
    if risk_distance <= 1e-9 or not np.isfinite(risk_distance):
        return None

    tp1_price = entry_price + side * tp1_rr * risk_distance
    tp2_price = entry_price + side * tp2_rr * risk_distance
    be_price = entry_price + side * spread

    closed = [False, False]
    leg_rr = [0.0, 0.0]
    leg_reason = [None, None]
    leg_exit_time = [None, None]

    future = df.iloc[entry_idx:]
    max_mfe_r = 0.0
    max_mae_r = 0.0

    for b in future.itertuples():
        spread_now = max(0.0, float(b.spread) * point)
        hi = float(b.high) + (spread_now if side == -1.0 else 0.0)
        lo = float(b.low) + (spread_now if side == -1.0 else 0.0)
        favorable, adverse = (hi, lo) if side == 1.0 else (lo, hi)

        # Seguimiento MFE / MAE
        cur_mfe = side * (favorable - entry_price) / risk_distance
        cur_mae = side * (entry_price - adverse) / risk_distance
        max_mfe_r = max(max_mfe_r, cur_mfe)
        max_mae_r = max(max_mae_r, cur_mae)

        stop_for_leg2 = be_price if closed[0] else stop_loss
        hit_initial_sl = side * (adverse - stop_loss) <= 0.0
        hit_tp1 = side * (favorable - tp1_price) >= 0.0
        hit_tp2 = side * (favorable - tp2_price) >= 0.0
        hit_be_leg2 = closed[0] and (side * (adverse - be_price) <= 0.0)

        t_str = str(b.time + pd.Timedelta(minutes=5))

        # Caso SL inicial
        if not closed[0] and hit_initial_sl:
            # Ambigüedad: si toca SL y TP1 en la misma barra, conservadoramente SL
            leg_rr[0] = -1.0
            leg_reason[0] = 'SL'
            leg_exit_time[0] = t_str
            closed[0] = True

            leg_rr[1] = -1.0
            leg_reason[1] = 'SL'
            leg_exit_time[1] = t_str
            closed[1] = True
            break

        # Leg 1 toca TP1
        if not closed[0] and hit_tp1:
            leg_rr[0] = tp1_rr
            leg_reason[0] = 'TP1'
            leg_exit_time[0] = t_str
            closed[0] = True

            # Si en la misma barra también retrocede al BE para Leg 2
            if side * (adverse - be_price) <= 0.0:
                leg_rr[1] = side * (be_price - entry_price) / risk_distance
                leg_reason[1] = 'BE'
                leg_exit_time[1] = t_str
                closed[1] = True
                break

        # Leg 2 cuando Leg 1 ya cerró
        if closed[0] and not closed[1]:
            if hit_be_leg2:
                leg_rr[1] = side * (be_price - entry_price) / risk_distance
                leg_reason[1] = 'BE'
                leg_exit_time[1] = t_str
                closed[1] = True
                break
            elif hit_tp2:
                leg_rr[1] = tp2_rr
                leg_reason[1] = 'TP2'
                leg_exit_time[1] = t_str
                closed[1] = True
                break

        if all(closed):
            break

    # Cada pierna arriesga 0.5R del total (suma de piernas)
    net_r = 0.5 * leg_rr[0] + 0.5 * leg_rr[1] if all(closed) else None
    outcome = (
        'FULL_WIN' if leg_reason == ['TP1', 'TP2']
        else 'PARTIAL_WIN_BE' if leg_reason == ['TP1', 'BE']
        else 'FULL_LOSS' if leg_reason == ['SL', 'SL']
        else 'OTHER'
    )

    return {
        'entry_time': str(bar.time),
        'entry_price': entry_price,
        'stop_loss': stop_loss,
        'risk_distance': risk_distance,
        'tp1_price': tp1_price,
        'tp2_price': tp2_price,
        'leg1_reason': leg_reason[0],
        'leg2_reason': leg_reason[1],
        'leg1_rr': leg_rr[0],
        'leg2_rr': leg_rr[1],
        'net_r': net_r,
        'outcome': outcome,
        'max_mfe_r': round(max_mfe_r, 2),
        'max_mae_r': round(max_mae_r, 2),
        'closed': all(closed),
    }


class ReplayProvider:
    def __init__(self, df: pd.DataFrame, point: float):
        self.df = df
        self.point = point
        self.index = 0

    def get_candles(self, symbol: str, timeframe: str, count: int = 350) -> pd.DataFrame:
        start_idx = max(0, self.index + 1 - count)
        return self.df.iloc[start_idx : self.index + 1].copy()

    def get_current_tick(self, symbol: str) -> dict:
        b = self.df.iloc[self.index]
        return {
            'time': b.time + pd.Timedelta(minutes=5),
            'bid': float(b.close),
            'ask': float(b.close) + float(b.spread) * self.point,
        }


def run_symbol_audit(symbol: str) -> dict:
    """Ejecuta todas las variantes sobre un símbolo para garantizar comparación limpia."""
    df, info = load(symbol)
    if df.empty or len(df) < 500:
        return {'symbol': symbol, 'status': 'NO_DATA', 'trades': []}

    fetch_audit_file = ROOT / 'storage/analysis/orb_nunez_2y/fetch_audit.json'
    point = 0.01
    if fetch_audit_file.exists():
        try:
            audit_data = json.loads(fetch_audit_file.read_text(encoding='utf-8'))
            point = float(audit_data.get(symbol, {}).get('point', 0.01))
        except Exception:
            pass

    # Configuraciones base de perfiles
    profiles = default_asset_profiles()
    profiles['EURUSD'] = dict(allowed_modes=['MOMENTUM', 'RETEST'], atr_buffer=0.05, max_range_atr_ratio=1.8, require_volume=False)
    profiles['USOIL'] = dict(allowed_modes=['MOMENTUM', 'RETEST'], atr_buffer=0.07, max_range_atr_ratio=2.0, require_volume=False)

    provider = ReplayProvider(df, point)

    # Instancias de estrategia para cada variante
    cfg_baseline = orb.ORBConfig(asset_profiles=profiles, entry_cutoff_enabled=False, require_high_quality_retest=False)
    strat_baseline = orb.NewYorkORBStrategy(provider, cfg_baseline)

    cfg_cutoff = orb.ORBConfig(asset_profiles=profiles, entry_cutoff_enabled=True, entry_cutoff_hour=11, entry_cutoff_minute=30, require_high_quality_retest=False)
    strat_cutoff = orb.NewYorkORBStrategy(provider, cfg_cutoff)

    cfg_high_qual = orb.ORBConfig(asset_profiles=profiles, entry_cutoff_enabled=False, require_high_quality_retest=True)
    strat_high_qual = orb.NewYorkORBStrategy(provider, cfg_high_qual)

    trades = []
    days = sorted(list(set(df.ny_date)))

    for day in days:
        if day.weekday() >= 5:
            continue
        day_bars = df[df.ny_date == day]
        opening = day_bars[(day_bars.ny_minute >= 570) & (day_bars.ny_minute < 585)]
        indices = day_bars[(day_bars.ny_minute >= 585) & (day_bars.ny_minute < 960)].index.tolist()

        if len(opening) != 3 or not indices:
            continue

        macro_levels = get_macro_liquidity(df, indices[0], day)
        pdh, pdl = macro_levels['PDH'], macro_levels['PDL']

        used_variants = set()

        for idx in indices:
            provider.index = idx
            now = df.time.iloc[idx] + pd.Timedelta(minutes=5)
            now_ny = df.time_ny.iloc[idx] + pd.Timedelta(minutes=5)
            bar = df.iloc[idx]

            # Evaluar señal baseline
            res_base = strat_baseline.analyze_symbol(symbol, now)
            sig_base = res_base.get('signal') if res_base.get('valid') else None

            # Si ya se evaluaron todas las variantes para el día, cortar
            if len(used_variants) == len(VARIANTS):
                break

            # ----------------------------------------------------
            # 1. BASELINE_CURRENT
            # ----------------------------------------------------
            if 'BASELINE_CURRENT' not in used_variants and sig_base:
                sim = simulate_trade_dual_leg(df, idx + 1, sig_base['direction'], float(sig_base['stop_loss']), point, 1.0, 2.0)
                if sim and sim['closed']:
                    trades.append({'variant': 'BASELINE_CURRENT', 'symbol': symbol, 'session_date': str(day), **sim})
                    used_variants.add('BASELINE_CURRENT')

            # ----------------------------------------------------
            # 2. VAR1_CUTOFF_1130
            # ----------------------------------------------------
            if 'VAR1_CUTOFF_1130' not in used_variants:
                res_cut = strat_cutoff.analyze_symbol(symbol, now)
                sig_cut = res_cut.get('signal') if res_cut.get('valid') else None
                if sig_cut:
                    sim = simulate_trade_dual_leg(df, idx + 1, sig_cut['direction'], float(sig_cut['stop_loss']), point, 1.0, 2.0)
                    if sim and sim['closed']:
                        trades.append({'variant': 'VAR1_CUTOFF_1130', 'symbol': symbol, 'session_date': str(day), **sim})
                        used_variants.add('VAR1_CUTOFF_1130')

            # ----------------------------------------------------
            # 3. VAR2_HIGH_QUALITY_RETEST
            # ----------------------------------------------------
            if 'VAR2_HIGH_QUALITY_RETEST' not in used_variants:
                res_hq = strat_high_qual.analyze_symbol(symbol, now)
                sig_hq = res_hq.get('signal') if res_hq.get('valid') else None
                if sig_hq:
                    sim = simulate_trade_dual_leg(df, idx + 1, sig_hq['direction'], float(sig_hq['stop_loss']), point, 1.0, 2.0)
                    if sim and sim['closed']:
                        trades.append({'variant': 'VAR2_HIGH_QUALITY_RETEST', 'symbol': symbol, 'session_date': str(day), **sim})
                        used_variants.add('VAR2_HIGH_QUALITY_RETEST')

            # ----------------------------------------------------
            # 4. VAR3_MACRO_LIQUIDITY (Cutoff 11:30 + Filtro PDH/PDL)
            # ----------------------------------------------------
            if 'VAR3_MACRO_LIQUIDITY' not in used_variants and sig_base and (now_ny.hour < 11 or (now_ny.hour == 11 and now_ny.minute <= 30)):
                atr = res_base.get('atr_frozen_m5') or 1.0
                dirn = sig_base['direction']
                ep = float(sig_base['entry_price'])
                block_liquidity = False
                if dirn == 'BUY' and pdh is not None and (ep >= pdh - 0.25 * atr):
                    block_liquidity = True  # Choque contra techo previo
                elif dirn == 'SELL' and pdl is not None and (ep <= pdl + 0.25 * atr):
                    block_liquidity = True  # Choque contra suelo previo

                if not block_liquidity:
                    sim = simulate_trade_dual_leg(df, idx + 1, dirn, float(sig_base['stop_loss']), point, 1.0, 2.0)
                    if sim and sim['closed']:
                        trades.append({'variant': 'VAR3_MACRO_LIQUIDITY', 'symbol': symbol, 'session_date': str(day), **sim})
                        used_variants.add('VAR3_MACRO_LIQUIDITY')

            # ----------------------------------------------------
            # 5. VAR4_TIGHT_SL_ROSELL (Cutoff 11:30 + SL Técnico Ceñido)
            # ----------------------------------------------------
            if 'VAR4_TIGHT_SL_ROSELL' not in used_variants and sig_base and (now_ny.hour < 11 or (now_ny.hour == 11 and now_ny.minute <= 30)):
                dirn = sig_base['direction']
                ep = float(sig_base['entry_price'])
                midpoint = float(sig_base['stop_loss'])
                atr = res_base.get('atr_frozen_m5') or (abs(ep - midpoint) * 0.5)
                buffer = 0.08 * atr

                # Stop ceñido en el extremo de la vela de retest o impulso
                if dirn == 'BUY':
                    retest_low = float(bar.low)
                    tight_sl = max(retest_low - buffer, midpoint)
                else:
                    retest_high = float(bar.high)
                    tight_sl = min(retest_high + buffer, midpoint)

                sim = simulate_trade_dual_leg(df, idx + 1, dirn, tight_sl, point, 1.0, 2.0)
                if sim and sim['closed']:
                    trades.append({'variant': 'VAR4_TIGHT_SL_ROSELL', 'symbol': symbol, 'session_date': str(day), **sim})
                    used_variants.add('VAR4_TIGHT_SL_ROSELL')

            # ----------------------------------------------------
            # 6. VAR5_CALIBRATED_TP (Cutoff 11:30 + TP1 1.0R / TP2 1.5R)
            # ----------------------------------------------------
            if 'VAR5_CALIBRATED_TP' not in used_variants and sig_base and (now_ny.hour < 11 or (now_ny.hour == 11 and now_ny.minute <= 30)):
                sim = simulate_trade_dual_leg(df, idx + 1, sig_base['direction'], float(sig_base['stop_loss']), point, 1.0, 1.5)
                if sim and sim['closed']:
                    trades.append({'variant': 'VAR5_CALIBRATED_TP', 'symbol': symbol, 'session_date': str(day), **sim})
                    used_variants.add('VAR5_CALIBRATED_TP')

            # ----------------------------------------------------
            # 7. VAR6_FULL_OPTIMIZED (Todas las mejoras combinadas)
            # ----------------------------------------------------
            if 'VAR6_FULL_OPTIMIZED' not in used_variants:
                res_hq = strat_high_qual.analyze_symbol(symbol, now)
                sig_hq = res_hq.get('signal') if res_hq.get('valid') else None
                if sig_hq and (now_ny.hour < 11 or (now_ny.hour == 11 and now_ny.minute <= 30)):
                    atr = res_hq.get('atr_frozen_m5') or 1.0
                    dirn = sig_hq['direction']
                    ep = float(sig_hq['entry_price'])
                    midpoint = float(sig_hq['stop_loss'])
                    buffer = 0.08 * atr

                    # Filtro Macro Liquidez
                    block = (dirn == 'BUY' and pdh is not None and ep >= pdh - 0.25 * atr) or (
                        dirn == 'SELL' and pdl is not None and ep <= pdl + 0.25 * atr
                    )
                    if not block:
                        if dirn == 'BUY':
                            tight_sl = max(float(bar.low) - buffer, midpoint)
                        else:
                            tight_sl = min(float(bar.high) + buffer, midpoint)

                        sim = simulate_trade_dual_leg(df, idx + 1, dirn, tight_sl, point, 1.0, 1.6)
                        if sim and sim['closed']:
                            trades.append({'variant': 'VAR6_FULL_OPTIMIZED', 'symbol': symbol, 'session_date': str(day), **sim})
                            used_variants.add('VAR6_FULL_OPTIMIZED')

    print(f'[-] Finalizado {symbol}: {len(trades)} operaciones auditadas.')
    return {'symbol': symbol, 'status': 'OK', 'trades': trades}


def compute_variant_metrics(trades: list[dict]) -> dict:
    df = pd.DataFrame(trades)
    if df.empty:
        return {}

    metrics = {}
    for var, grp in df.groupby('variant'):
        total = len(grp)
        tp1_hits = (grp['leg1_reason'] == 'TP1').sum()
        tp2_hits = (grp['leg2_reason'] == 'TP2').sum()
        be_saves = (grp['leg2_reason'] == 'BE').sum()
        full_wins = (grp['outcome'] == 'FULL_WIN').sum()
        partial_be = (grp['outcome'] == 'PARTIAL_WIN_BE').sum()
        full_losses = (grp['outcome'] == 'FULL_LOSS').sum()

        net_r = float(grp['net_r'].sum())
        gross_win = float(grp[grp['net_r'] > 0]['net_r'].sum())
        gross_loss = float(abs(grp[grp['net_r'] < 0]['net_r'].sum()))
        pf = gross_win / gross_loss if gross_loss > 0 else (99.0 if gross_win > 0 else 1.0)

        # Drawdown en R
        eq = grp['net_r'].cumsum()
        peak = np.maximum.accumulate(eq)
        dd = peak - eq
        max_dd_r = float(dd.max()) if len(dd) else 0.0

        metrics[var] = {
            'trades': total,
            'tp1_winrate_pct': round((tp1_hits / total) * 100.0, 1) if total else 0.0,
            'tp2_winrate_pct': round((tp2_hits / total) * 100.0, 1) if total else 0.0,
            'be_save_pct': round((be_saves / total) * 100.0, 1) if total else 0.0,
            'full_win_pct': round((full_wins / total) * 100.0, 1) if total else 0.0,
            'partial_be_pct': round((partial_be / total) * 100.0, 1) if total else 0.0,
            'full_loss_pct': round((full_losses / total) * 100.0, 1) if total else 0.0,
            'global_winrate_pct': round(((full_wins + partial_be) / total) * 100.0, 1) if total else 0.0,
            'net_r': round(net_r, 2),
            'profit_factor': round(pf, 2),
            'max_drawdown_r': round(max_dd_r, 2),
            'avg_mfe_r': round(float(grp['max_mfe_r'].mean()), 2) if total else 0.0,
            'avg_mae_r': round(float(grp['max_mae_r'].mean()), 2) if total else 0.0,
        }
    return metrics


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print('=' * 110)
    print(' AUDITORÍA CUANTITATIVA: REPLAY HISTÓRICO DE MEJORAS ORB (2 AÑOS / PERIODO COMPLETO M5)')
    print(' Evaluando 8 instrumentos en paralelo a través de 7 variantes comparativas...')
    print('=' * 110)

    all_trades = []
    symbol_results = {}

    with ProcessPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(run_symbol_audit, sym): sym for sym in SYMBOLS}
        for fut in as_completed(futures):
            res = fut.result()
            sym = res['symbol']
            tr = res.get('trades', [])
            all_trades.extend(tr)
            symbol_results[sym] = compute_variant_metrics(tr)

    global_metrics = compute_variant_metrics(all_trades)

    # Guardar resultados
    trades_df = pd.DataFrame(all_trades)
    trades_df.to_csv(OUT / 'all_variants_trades.csv', index=False)

    summary = {
        'global_metrics': global_metrics,
        'by_symbol': symbol_results,
    }
    (OUT / 'audit_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')

    print('\n' + '=' * 110)
    print(f'{"VARIANTE":26s} | {"TRADES":6s} | {"WR TP1":7s} | {"WR TP2":7s} | {"GLOBAL WR":9s} | {"FULL LOSS":9s} | {"NET R":9s} | {"PF":5s} | {"MAX DD":7s}')
    print('-' * 110)
    for var in VARIANTS:
        m = global_metrics.get(var, {})
        if not m:
            continue
        print(
            f"{var:26s} | {m['trades']:6d} | {m['tp1_winrate_pct']:6.1f}% | {m['tp2_winrate_pct']:6.1f}% | "
            f"{m['global_winrate_pct']:8.1f}% | {m['full_loss_pct']:8.1f}% | {m['net_r']:+8.2f}R | {m['profit_factor']:5.2f} | {m['max_drawdown_r']:6.1f}R"
        )
    print('=' * 110)


if __name__ == '__main__':
    main()
