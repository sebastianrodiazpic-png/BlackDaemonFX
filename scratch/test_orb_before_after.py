"""Replay fiel ANTES vs DESPUÉS para ORB (London + New York) sobre 2 años de M5 real."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from strategy.orb import new_york_orb as orb
from strategy.orb.asset_rules import (
    ASSET_CONFIG,
    audit_volume_confirmation,
    check_range_amplitude,
    get_asset_rules,
)
from tools.replay_orb_sweep_expanded import managed_simulator

HIST_DIR = ROOT / "storage" / "analysis" / "orb_sweep_expanded" / "history"
START_DATE = pd.Timestamp("2024-10-03", tz="UTC")

ORB_SYMBOLS = [
    "XAUUSD",
    "BTCUSD",
    "USDCAD",
    "GBPUSD",
    "AUDUSD",
    "EURUSD",
    "US Oil",
    "Wall Street 30",
    "US Tech 100",
    "US SP 500",
]

POINTS = {
    "XAUUSD": 0.01,
    "BTCUSD": 0.01,
    "USDCAD": 0.00001,
    "GBPUSD": 0.00001,
    "AUDUSD": 0.00001,
    "EURUSD": 0.00001,
    "US Oil": 0.001,
    "Wall Street 30": 0.1,
    "US Tech 100": 0.1,
    "US SP 500": 0.1,
}


def load_m5(symbol: str) -> pd.DataFrame:
    fname = symbol.replace(" ", "_") + "_M5.csv"
    path = HIST_DIR / fname
    if not path.exists():
        path = ROOT / "data" / "historical" / fname
    if not path.exists():
        path = ROOT / "data" / "forex_historical" / fname
    df = pd.read_csv(path)
    df["time"] = pd.to_datetime(df["time"], utc=True)
    df = df[df["time"] >= START_DATE - pd.Timedelta(days=10)].drop_duplicates("time").sort_values("time").reset_index(drop=True)
    df["time_ny"] = df["time"].dt.tz_convert("America/New_York")
    df["ny_date"] = df["time_ny"].dt.date
    df["ny_minute"] = df["time_ny"].dt.hour * 60 + df["time_ny"].dt.minute
    return df


def run_orb_symbol(symbol: str, df: pd.DataFrame, mode: str = "BEFORE") -> list[dict]:
    """
    mode == 'BEFORE':
      - Clave de sesión compartida por día (`day`), por lo que:
        1) El ATR congelado en Londres (03:15 NY) se reutiliza en Nueva York (09:45 NY).
        2) Si Londres ejecuta una señal en `day`, `_session_signal_memory[symbol] = day` bloquea Nueva York ese mismo día.
        3) `_evaluate_sweep` usa max_entry_min = 955 (15:55 NY) por el bug de `entry_cutoff_minute_ny`.
        4) Sin régimen Crabel ni Breakaway FVG Retest.
    mode == 'AFTER':
      - Clave de sesión separada `(day, session_name)` para ATR congelado y memoria de señal (Londres no bloquea ni contamina NY).
      - Ventana institucional real: Londres 03:15–05:30 NY (195..330 min) y NY 09:45–11:30 NY (585..690 min).
      - En SWEEP: exige vela MSS con cuerpo direccional real (body_ratio >= 0.45) y alineación con VWAP/POC.
      - En RETEST / Breakaway FVG: incluye régimen Crabel (0.35 <= OR/ATR <= 1.50) + Breakaway FVG Retest con mecha de absorción.
    """
    point = POINTS.get(symbol, 0.0001)
    rules = get_asset_rules(symbol)
    is_index = orb.is_orb_index_symbol(symbol)
    is_crypto = "BTC" in symbol.upper() or "ETH" in symbol.upper()
    london_applicable = (not is_index) and (not is_crypto)

    buffer_pct = float(rules.get("atr_buffer", 0.05))
    max_atr_ratio = float(rules.get("max_range_atr_ratio", 2.5))
    req_vol = bool(rules.get("require_volume", False))
    allowed_dirs = rules.get("allowed_directions")
    retest_allowed = "RETEST" in (rules.get("allowed_modes") or []) or is_index

    trades = []
    highs = df["high"].to_numpy(float)
    lows = df["low"].to_numpy(float)
    opens = df["open"].to_numpy(float)
    closes = df["close"].to_numpy(float)
    times = df["time"].to_numpy()

    for day, group in df.groupby("ny_date", sort=True):
        if day.weekday() >= 5 or pd.Timestamp(day, tz="UTC") < START_DATE:
            continue

        frozen_atr_by_key: dict[str, float] = {}
        used_signal_by_key: set[str] = set()

        sessions_to_run = []
        if london_applicable:
            sessions_to_run.append(("LONDON", 180, 195, 540 if mode == "BEFORE" else 330))
        sessions_to_run.append(("NEW_YORK", 570, 585, 955 if mode == "BEFORE" else 690))

        for sess_name, open_min, range_end_min, cutoff_min in sessions_to_run:
            state_key = str(day) if mode == "BEFORE" else f"{day}_{sess_name}"

            minutes = group["ny_minute"]
            opening = group[(minutes >= open_min) & (minutes < range_end_min)]
            if len(opening) != 3:
                continue

            open_pos = int(opening.index[0])
            if open_pos < 16:
                continue

            if state_key in frozen_atr_by_key:
                atr = frozen_atr_by_key[state_key]
            else:
                hist_slice = df.iloc[max(0, open_pos - 14) : open_pos + 3]
                atr = orb.NewYorkORBStrategy._average_true_range(hist_slice, 14)
                if not atr or not math.isfinite(atr) or atr <= 0:
                    continue
                frozen_atr_by_key[state_key] = atr

            range_high = float(opening["high"].max())
            range_low = float(opening["low"].min())
            range_size = range_high - range_low
            mid = (range_high + range_low) / 2.0
            if range_size <= 0:
                continue

            amp = check_range_amplitude(range_high, range_low, atr, max_atr_ratio)
            if not amp["isValid"]:
                continue

            or_atr_ratio = range_size / atr
            post_indices = group[(minutes >= range_end_min) & (minutes < cutoff_min)].index.to_list()
            if not post_indices:
                continue

            buffer = buffer_pct * atr
            lookback_mss = 5

            for offset, idx in enumerate(post_indices):
                if state_key in used_signal_by_key:
                    break

                bar_close = closes[idx]
                bar_open = opens[idx]
                bar_high = highs[idx]
                bar_low = lows[idx]
                bar_span = max(1e-9, bar_high - bar_low)
                bar_body_ratio = abs(bar_close - bar_open) / bar_span

                # 1. Evaluar SWEEP + MSS
                signal_found = None
                for earlier in range(max(0, offset - lookback_mss), offset):
                    sweep_idx = post_indices[earlier]
                    if sweep_idx < 3:
                        continue
                    sw_close = closes[sweep_idx]
                    if not (range_low < sw_close < range_high):
                        continue
                    before_low = float(np.min(lows[sweep_idx - 3 : sweep_idx]))
                    before_high = float(np.max(highs[sweep_idx - 3 : sweep_idx]))

                    sell = highs[sweep_idx] > range_high + buffer and bar_close < min(before_low, mid)
                    buy = lows[sweep_idx] < range_low - buffer and bar_close > max(before_high, mid)
                    if not sell and not buy:
                        continue

                    direction = "SELL" if sell else "BUY"
                    if allowed_dirs and direction not in allowed_dirs:
                        continue

                    if mode == "AFTER":
                        # Filtro oficial ICT/Crabel: la vela MSS debe tener desplazamiento real (body_ratio >= 0.42)
                        # y el barrido no debe provenir de un rango muerto (< 0.30 ATR)
                        if bar_body_ratio < 0.42 or or_atr_ratio < 0.30:
                            continue

                    side = -1 if sell else 1
                    sess_slice = df.iloc[open_pos : idx + 1]
                    vwap = orb.NewYorkORBStrategy._session_vwap(sess_slice)
                    poc = orb.NewYorkORBStrategy._session_poc(sess_slice)
                    if not any(lvl is not None and side * (bar_close - lvl) > 0 for lvl in (vwap, poc)):
                        continue

                    if req_vol:
                        ev = audit_volume_confirmation(df.iloc[max(0, idx - 350) : idx + 1], df["time"].iloc[sweep_idx], "RETEST", True)
                        if not ev["confirmed"]:
                            continue

                    stop_loss = highs[sweep_idx] + buffer if sell else lows[sweep_idx] - buffer
                    signal_found = (direction, stop_loss, "SWEEP")
                    break

                # 2. Evaluar BREAKOUT + RETEST (y Breakaway FVG Retest en AFTER)
                if signal_found is None and offset >= 1 and (retest_allowed or mode == "AFTER"):
                    # En AFTER, también permitimos Breakaway FVG Retest de alta compresión (Crabel 0.35 <= OR/ATR <= 1.35)
                    crabel_compression_ok = (0.35 <= or_atr_ratio <= 1.35) if mode == "AFTER" else True
                    if retest_allowed or (mode == "AFTER" and crabel_compression_ok):
                        for b_off in range(max(0, offset - 3), offset):
                            b_idx = post_indices[b_off]
                            b_close = closes[b_idx]
                            b_open = opens[b_idx]
                            b_span = max(1e-9, highs[b_idx] - lows[b_idx])
                            b_body_ratio = abs(b_close - b_open) / b_span
                            prev_c = closes[b_idx - 1]

                            bo_up = prev_c <= range_high + buffer and b_close > range_high + buffer and b_body_ratio >= 0.50
                            bo_dn = prev_c >= range_low - buffer and b_close < range_low - buffer and b_body_ratio >= 0.50
                            if not bo_up and not bo_dn:
                                continue

                            direction = "BUY" if bo_up else "SELL"
                            if allowed_dirs and direction not in allowed_dirs:
                                continue

                            # Verificar FVG de ruptura (3 velas hasta b_idx o b_idx+1)
                            has_fvg = False
                            fvg_bound = range_high if bo_up else range_low
                            if b_idx >= 2:
                                if bo_up and lows[b_idx] > highs[b_idx - 2]:
                                    has_fvg = True
                                    fvg_bound = float(lows[b_idx])
                                elif bo_dn and highs[b_idx] < lows[b_idx - 2]:
                                    has_fvg = True
                                    fvg_bound = float(highs[b_idx])

                            if mode == "BEFORE":
                                # En BEFORE solo toca exactamente el borde del OR
                                touched_or = (bar_low <= range_high + buffer and bar_close > range_high) if bo_up else (bar_high >= range_low - buffer and bar_close < range_low)
                                if not touched_or:
                                    continue
                            else:
                                # En AFTER (Crabel + Breakaway FVG):
                                # Si el rango está hipertrofiado (> 1.45 ATR), exige FVG de ruptura obligatorio
                                if or_atr_ratio > 1.45 and not has_fvg:
                                    continue
                                if not retest_allowed and not has_fvg:
                                    continue
                                touch_level = max(range_high, fvg_bound) if (bo_up and has_fvg) else (min(range_low, fvg_bound) if (bo_dn and has_fvg) else (range_high if bo_up else range_low))
                                touched = (bar_low <= touch_level + buffer and bar_close > range_high and bar_close > bar_open) if bo_up else (bar_high >= touch_level - buffer and bar_close < range_low and bar_close < bar_open)
                                # Mecha de rechazo a favor >= 25% del rango
                                wick_fav = (min(bar_open, bar_close) - bar_low) / bar_span if bo_up else (bar_high - max(bar_open, bar_close)) / bar_span
                                if not (touched and wick_fav >= 0.25):
                                    continue

                            side = 1 if direction == "BUY" else -1
                            sess_slice = df.iloc[open_pos : idx + 1]
                            vwap = orb.NewYorkORBStrategy._session_vwap(sess_slice)
                            poc = orb.NewYorkORBStrategy._session_poc(sess_slice)
                            if not any(lvl is not None and side * (bar_close - lvl) > 0 for lvl in (vwap, poc)):
                                continue

                            stop_loss = mid
                            signal_found = (direction, stop_loss, "RETEST")
                            break

                if signal_found is not None and idx + 1 < len(df):
                    direction, stop_loss, sig_type = signal_found
                    sim = managed_simulator(df, idx + 1, direction, stop_loss, point)
                    if sim is not None and sim["spread_to_sl"] <= 0.18:
                        used_signal_by_key.add(state_key)
                        trades.append({
                            "symbol": symbol,
                            "session": sess_name,
                            "type": sig_type,
                            "net_r": sim["net_r_ext"],
                            "is_win": sim["net_r_ext"] > 0.05,
                        })
                        break

    return trades


if __name__ == "__main__":
    for sym in ORB_SYMBOLS:
        df = load_m5(sym)
        tb = run_orb_symbol(sym, df, "BEFORE")
        ta = run_orb_symbol(sym, df, "AFTER")
        wb = 100 * np.mean([t["is_win"] for t in tb]) if tb else 0.0
        wa = 100 * np.mean([t["is_win"] for t in ta]) if ta else 0.0
        rb = np.sum([t["net_r"] for t in tb]) if tb else 0.0
        ra = np.sum([t["net_r"] for t in ta]) if ta else 0.0
        print(f"{sym:<16} | BEFORE: {len(tb):>3} tr, WR={wb:>5.1f}%, R={rb:>+6.1f} | AFTER: {len(ta):>3} tr, WR={wa:>5.1f}%, R={ra:>+6.1f}")
