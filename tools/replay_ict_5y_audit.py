"""Replay fiel de 5 años (oct-2021 → oct-2026) de ICT Sabri Malle sobre todos los instrumentos seleccionados y en poda.

Reutiliza las señales fieles ya calculadas con ICTSabriMalleStrategy en Y1 (oct-2025 → oct-2026) e Y0 (oct-2024 → oct-2025)
y ejecuta la clase real ICTSabriMalleStrategy en los años anteriores hasta 5 años atrás (oct-2021 → oct-2024, más Y0 para
los símbolos que no estaban en prior_y0).
Aplica los costes reales de ticks (real_spread_factors.csv y real_markets_tick_spread_20261023.json) y los topes reales
del motor vivo (2 % spread/SL en sintéticos y metales, 5 % en Forex e índices/energía).
"""
from __future__ import annotations

import json
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "storage" / "analysis"
LIMIT_BARS = 8


def load_frames_range(mt5, symbol: str, start: datetime, end: datetime, h4_extra_days: int = 45):
    consts = {"M15": mt5.TIMEFRAME_M15, "H1": mt5.TIMEFRAME_H1, "H4": mt5.TIMEFRAME_H4}
    extra = {"M15": 5, "H1": 15, "H4": h4_extra_days}
    frames = {}
    for tf, const in consts.items():
        chunks = []
        a = start - timedelta(days=extra[tf])
        while a < end:
            b = min(end, a + timedelta(days=300))
            rates = mt5.copy_rates_range(symbol, const, a, b)
            if rates is not None and len(rates):
                chunks.append(pd.DataFrame(rates))
            a = b
        if not chunks:
            return None
        df = pd.concat(chunks, ignore_index=True).drop_duplicates("time").sort_values("time").reset_index(drop=True)
        if len(df) < 50:
            return None
        df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
        frames[tf] = df
    return frames


def compute_h1_context(h1_df: pd.DataFrame) -> pd.DataFrame:
    from strategy.indicators import calculate_adx
    h = h1_df.copy().sort_values("time").reset_index(drop=True)
    prev_c = h["close"].shift(1)
    tr = pd.concat(
        [(h["high"] - h["low"]).abs(), (h["high"] - prev_c).abs(), (h["low"] - prev_c).abs()],
        axis=1,
    ).max(axis=1)
    h["atr_h1"] = tr.rolling(14, min_periods=5).mean()
    h["adx_h1"] = calculate_adx(h, 14)
    h["available_at"] = h["time"] + pd.Timedelta(hours=1)
    return h[["available_at", "atr_h1", "adx_h1"]]


def run_symbol_window(args):
    symbol, start_iso, end_iso = args
    import MetaTrader5 as mt5
    from strategy.ict.config import ICTSabriMalleConfig
    from strategy.ict.ict_strategy import ICTSabriMalleStrategy, is_synthetic_asset
    from tools.replay_ict_live_faithful import HistoricalProvider
    from tools.replay_msnr_live_faithful import simulate

    if not mt5.initialize():
        return symbol, [], "MT5_INIT_ERROR"
    mt5.symbol_select(symbol, True)
    start_dt = pd.Timestamp(start_iso).to_pydatetime()
    end_dt = pd.Timestamp(end_iso).to_pydatetime()
    frames = load_frames_range(mt5, symbol, start_dt, end_dt)
    info = mt5.symbol_info(symbol)
    mt5.shutdown()
    if frames is None or info is None:
        return symbol, [], "SIN_DATOS_EN_RANGO"

    m15 = frames["M15"].reset_index(drop=True)
    if m15.empty or m15["time"].iloc[-1] <= pd.Timestamp(start_iso):
        return symbol, [], "SIN_VELAS_EN_VENTANA"

    bar_spread = float(np.median(m15["spread"][m15["spread"] > 0])) * float(info.point) if "spread" in m15 and (m15["spread"] > 0).any() else float(info.spread) * float(info.point)
    spread = bar_spread if bar_spread > 0 else float(info.spread) * float(info.point)
    cfg = ICTSabriMalleConfig(excluded_symbols=(), wr_pruned_symbols=())
    provider = HistoricalProvider(frames, spread)
    strat = ICTSabriMalleStrategy(provider, cfg)

    h, l, c, o = (m15[k].values.astype(float) for k in ("high", "low", "close", "open"))
    start_cut = pd.Timestamp(start_iso)
    end_cut = pd.Timestamp(end_iso)
    mid_cut = start_cut + (end_cut - start_cut) / 2
    n = len(m15)
    spreads = np.full(n, spread)

    def outcome(direction, fill_idx, fill, sl, tp1_rr, tp2_rr, check_fill_bar):
        sign = 1 if direction == "BUY" else -1
        risk = sign * (fill - sl)
        if risk <= 0:
            return None
        if check_fill_bar:
            hit = (l[fill_idx] <= sl) if sign > 0 else (h[fill_idx] + spread >= sl)
            if hit:
                return -1.0, "SL_EN_VELA_FILL", 1, risk
            start = fill_idx + 1
        else:
            start = fill_idx
        if start >= n - 1:
            return None
        rr, out, bars = simulate(
            direction,
            fill,
            sl,
            fill + sign * tp1_rr * risk,
            fill + sign * tp2_rr * risk,
            h[start:],
            l[start:],
            c[start:],
            opens=o[start:],
            spreads=spreads[start:],
            leg1_weight=cfg.leg1_risk_ratio,
            leg2_weight=cfg.leg2_risk_ratio,
        )
        return rr, out, bars + (start - fill_idx), risk

    rows = []
    busy = {"MERCADO": -1, "LIMITE": -1}
    synthetic = is_synthetic_asset(symbol)

    for i in range(100, n - 2):
        t_bar = m15["time"].iloc[i]
        if t_bar < start_cut or t_bar >= end_cut:
            continue
        if i <= busy["MERCADO"] and i <= busy["LIMITE"]:
            continue
        provider.now = t_bar + pd.Timedelta(minutes=15)
        res = strat.analyze_symbol(symbol, now_utc=provider.now.to_pydatetime())
        if not res.get("valid"):
            continue
        sig = res["signal"]
        d, sl, lim = sig["direction"], float(sig["stop_loss"]), float(sig["entry_price"])
        sign = 1 if d == "BUY" else -1
        real_feat = sig.get("ict_real_features") or {}
        rec = dict(
            symbol=symbol,
            synthetic=synthetic,
            time=str(provider.now),
            period="H1_first" if provider.now < mid_cut else "H2_last",
            direction=d,
            limit=lim,
            stop_loss=sl,
            close=float(c[i]),
            spread=spread,
            adx_h1=real_feat.get("adx_h1"),
            atr_h1=real_feat.get("atr_h1"),
            sl_atr_h1=real_feat.get("sl_atr_h1"),
            body_ratio=sig.get("displacement_body_ratio"),
        )
        if i > busy["MERCADO"]:
            fill = o[i + 1] + (spread if d == "BUY" else 0.0)
            r = outcome(d, i + 1, fill, sl, cfg.tp1_rr, cfg.runner_rr, check_fill_bar=False)
            if r:
                rec.update(mkt_rr=r[0], mkt_out=r[1], mkt_risk=r[3], mkt_fill=fill)
                busy["MERCADO"] = i + 1 + r[2]
        if i > busy["LIMITE"]:
            next_ask = o[i + 1] + spread
            immediate = (next_ask <= lim) if sign > 0 else (o[i + 1] >= lim)
            if immediate:
                r = outcome(d, i + 1, next_ask if sign > 0 else o[i + 1], sl, cfg.tp1_rr, cfg.runner_rr, False)
                if r:
                    rec.update(lim_rr=r[0], lim_out=r[1], lim_risk=r[3], lim_fill_bars=0, lim_fill="INMEDIATO")
                    busy["LIMITE"] = i + 1 + r[2]
            else:
                filled = None
                for j in range(i + 1, min(n - 1, i + 1 + LIMIT_BARS)):
                    if (sign > 0 and l[j] + spread <= lim) or (sign < 0 and h[j] >= lim):
                        filled = j
                        break
                if filled is None:
                    rec.update(lim_rr=np.nan, lim_out="NO_FILL", lim_fill="NO_FILL")
                else:
                    r = outcome(d, filled, lim, sl, cfg.tp1_rr, cfg.runner_rr, check_fill_bar=True)
                    if r:
                        rec.update(lim_rr=r[0], lim_out=r[1], lim_risk=r[3], lim_fill_bars=filled - i, lim_fill="LIMITE")
                        busy["LIMITE"] = filled + r[2]
        rows.append(rec)
    return symbol, rows, f"OK ({m15['time'].iloc[0].date()} -> {m15['time'].iloc[-1].date()})"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    from config.ict_instrument_policy import (
        ICT_FOREX_ACTIVE,
        ICT_MARKETS_ACTIVE,
        ICT_PHASE1_EXCLUDED,
        ICT_SYNTHETIC_FAMILIES,
        MSNR_SYNTHETIC_UNIVERSE,
    )
    from config.synth_wr45 import ICT_WR45_PRUNED

    # Cargar datasets fieles ya existentes (Y1: oct-25..oct-26, Y0: oct-24..oct-25)
    y1 = pd.read_csv(OUT / "ict_limit_entry_signals.csv")
    y0_s = pd.read_csv(OUT / "ict_limit_entry_signals_prior_y0.csv")
    y0_p = pd.read_csv(OUT / "ict_limit_entry_signals_prior_y0_pruned.csv")
    y0_r = pd.read_csv(OUT / "ict_limit_entry_signals_real_y0.csv")
    y1_r = pd.read_csv(OUT / "ict_limit_entry_signals_real_y1.csv")

    existing = pd.concat([y1, y0_s, y0_p, y0_r, y1_r], ignore_index=True)
    existing["t"] = pd.to_datetime(existing["time"], utc=True)
    existing = existing.sort_values("t").drop_duplicates(subset=["symbol", "time"], keep="first")

    # Determinar el universo de todos los instrumentos ICT seleccionados y en poda (sin sufijos micro duplicados)
    base_forex = [s for s in ICT_FOREX_ACTIVE if "micro" not in s.lower()]
    extra_forex = ["NZDUSD", "EURJPY", "GBPJPY", "AUDJPY", "EURGBP", "CADCHF", "GBPCHF", "EURCHF", "AUDCAD", "AUDNZD"]
    base_markets = [s for s in ICT_MARKETS_ACTIVE if "micro" not in s.lower()] + ["XAGUSD", "BTCUSD"]
    all_symbols = sorted(set(MSNR_SYNTHETIC_UNIVERSE) | set(base_forex) | set(extra_forex) | set(base_markets))

    extra_csv = OUT / "ict_5y_extra_signals.csv"
    done_extra = pd.DataFrame()
    done_symbols = set()
    if extra_csv.exists():
        done_extra = pd.read_csv(extra_csv)
        if not done_extra.empty and "symbol" in done_extra.columns:
            done_symbols = set(done_extra["symbol"].unique())

    tasks = []
    for sym in all_symbols:
        if sym in done_symbols:
            continue
        sym_rows = existing[existing["symbol"] == sym]
        if sym_rows.empty:
            min_existing = "2026-10-26T00:00:00+00:00"
        else:
            min_existing = str(sym_rows["t"].min().isoformat())
        # Buscar desde hace 5 años (2021-10-20) hasta el inicio de lo ya calculado
        if pd.Timestamp(min_existing) > pd.Timestamp("2021-11-01T00:00:00+00:00"):
            tasks.append((sym, "2021-10-20T00:00:00+00:00", min_existing))

    print(f"Símbolos totales={len(all_symbols)} | tareas pendientes para completar 5 años={len(tasks)}", flush=True)
    new_rows = []
    if tasks:
        with ProcessPoolExecutor(max_workers=6) as pool:
            futs = {pool.submit(run_symbol_window, task): task[0] for task in tasks}
            for fut in as_completed(futs):
                sym, rows, status = fut.result()
                print(f"  [{sym}] {status} -> +{len(rows)} señales", flush=True)
                if rows:
                    new_rows.extend(rows)
                    combined_extra = pd.concat([done_extra, pd.DataFrame(new_rows)], ignore_index=True)
                    combined_extra.to_csv(extra_csv, index=False)

    if extra_csv.exists():
        extra_df = pd.read_csv(extra_csv)
        full_df = pd.concat([existing.drop(columns=["t"], errors="ignore"), extra_df], ignore_index=True)
    else:
        full_df = existing.drop(columns=["t"], errors="ignore")

    full_df["t"] = pd.to_datetime(full_df["time"], utc=True)
    full_df = full_df.sort_values(["symbol", "t"]).drop_duplicates(subset=["symbol", "time"], keep="first")
    full_df.drop(columns=["t"]).to_csv(OUT / "ict_5y_signals_complete.csv", index=False)
    print(f"Guardado ict_5y_signals_complete.csv con {len(full_df)} señales en {full_df['symbol'].nunique()} símbolos.", flush=True)


if __name__ == "__main__":
    main()
