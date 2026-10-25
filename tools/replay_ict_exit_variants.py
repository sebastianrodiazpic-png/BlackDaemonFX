"""Replay fiel ICT (entrada limitada): mismas señales con varias gestiones de salida — 20-oct-2026.

Objetivo: medir cómo cambian el acierto (operaciones con R > 0) y el R/trade al mover TP1 y el objetivo del runner,
siempre dentro del contrato operativo: 1 % en 2 patas, la pata 1 cierra en TP1 y el runner pasa a BE solo tras TP1.

Para que todas las variantes vean exactamente las mismas operaciones, la ocupación del símbolo ("un trade activo")
se fija con la gestión actual (TP1 1R + runner 2R) y el resto de variantes se evalúan sobre esos mismos fills.

Uso:
    .venv/Scripts/python.exe tools/replay_ict_exit_variants.py --days 365 --workers 6 [--end-days-ago 365] [--tag y0]
Salida: storage/analysis/ict_exit_variants{_tag}.csv
"""
from __future__ import annotations

import argparse
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "storage" / "analysis"
LIMIT_BARS = 8
# (TP1 en R, objetivo del runner en R). La primera es la gestión actual.
VARIANTS = {
    "tp1_1.0_r2": (1.0, 2.0), "tp1_0.8_r2": (0.8, 2.0), "tp1_0.6_r2": (0.6, 2.0), "tp1_1.2_r2": (1.2, 2.0),
    "tp1_1.0_r3": (1.0, 3.0), "tp1_0.8_r3": (0.8, 3.0), "tp1_1.0_r1.5": (1.0, 1.5), "tp1_0.8_r1.5": (0.8, 1.5),
}


def run_symbol(symbol: str, days: int, end_days_ago: int = 0, phantom_busy: bool = False):
    import MetaTrader5 as mt5
    from datetime import datetime, timedelta, timezone
    from strategy.ict.config import ICTSabriMalleConfig
    from strategy.ict.ict_strategy import ICTSabriMalleStrategy
    from tools.replay_ict_limit_entry import load_frames_until
    from tools.replay_ict_live_faithful import HistoricalProvider, load_frames
    from tools.replay_msnr_live_faithful import simulate

    if not mt5.initialize():
        return symbol, [], "MT5_INIT"
    mt5.symbol_select(symbol, True)
    end = datetime.now(timezone.utc) - timedelta(days=end_days_ago)
    frames = load_frames(mt5, symbol, days) if end_days_ago == 0 else load_frames_until(mt5, symbol, days, end)
    info = mt5.symbol_info(symbol)
    mt5.shutdown()
    if frames is None or info is None:
        return symbol, [], "SIN_DATOS"
    spread = float(info.spread) * float(info.point)
    cfg = ICTSabriMalleConfig(excluded_symbols=())
    strat = ICTSabriMalleStrategy(HistoricalProvider(frames, spread), cfg)
    provider = strat.data_provider if hasattr(strat, "data_provider") else None
    m15 = frames["M15"].reset_index(drop=True)
    h, l, c, o = (m15[k].values.astype(float) for k in ("high", "low", "close", "open"))
    start_cut = m15["time"].iloc[-1] - pd.Timedelta(days=days)
    mid_cut = start_cut + pd.Timedelta(days=days / 2)
    n = len(m15)
    spreads = np.full(n, spread)
    hp = HistoricalProvider(frames, spread)
    strat = ICTSabriMalleStrategy(hp, cfg)

    def outcome(direction, fill_idx, fill, sl, tp1_rr, tp2_rr):
        sign = 1 if direction == "BUY" else -1
        risk = sign * (fill - sl)
        if risk <= 0:
            return None
        hit = (l[fill_idx] <= sl) if sign > 0 else (h[fill_idx] + spread >= sl)
        if hit:
            return -1.0, "SL_EN_VELA_FILL", 1
        start = fill_idx + 1
        if start >= n - 1:
            return None
        rr, out, bars = simulate(direction, fill, sl, fill + sign * tp1_rr * risk, fill + sign * tp2_rr * risk,
                                 h[start:], l[start:], c[start:], opens=o[start:], spreads=spreads[start:],
                                 leg1_weight=cfg.leg1_risk_ratio, leg2_weight=cfg.leg2_risk_ratio)
        return rr, out, bars + 1

    rows, busy = [], -1
    for i in range(100, n - 2):
        if m15["time"].iloc[i] < start_cut or i <= busy:
            continue
        hp.now = m15["time"].iloc[i] + pd.Timedelta(minutes=15)
        res = strat.analyze_symbol(symbol, now_utc=hp.now.to_pydatetime())
        if not res.get("valid"):
            continue
        sig = res["signal"]
        d, sl, lim = sig["direction"], float(sig["stop_loss"]), float(sig["entry_price"])
        sign = 1 if d == "BUY" else -1
        next_ask = o[i + 1] + spread
        if (next_ask <= lim) if sign > 0 else (o[i + 1] >= lim):
            fill_idx, fill = i + 1, (next_ask if sign > 0 else o[i + 1])
        else:
            fill_idx = next((j for j in range(i + 1, min(n - 1, i + 1 + LIMIT_BARS))
                             if (sign > 0 and l[j] + spread <= lim) or (sign < 0 and h[j] >= lim)), None)
            if fill_idx is None:
                continue
            fill = lim
        risk = sign * (fill - sl)
        if risk <= 0:
            continue
        if spread / risk > 0.02:  # tope spread/SL 2 % como en vivo
            if phantom_busy:  # la señal descartada "ocupa" el símbolo hasta su resultado virtual
                r = outcome(d, fill_idx, fill, sl, *VARIANTS["tp1_1.0_r2"])
                if r is not None:
                    busy = fill_idx + r[2]
            continue
        rec = dict(symbol=symbol, time=str(hp.now), period="H1_first" if hp.now < mid_cut else "H2_last",
                   direction=d, spread_sl=spread / risk)
        base_bars = None
        for name, (tp1, tp2) in VARIANTS.items():
            r = outcome(d, fill_idx, fill, sl, tp1, tp2)
            if r is None:
                rec[name] = np.nan
                continue
            rec[name], rec[f"{name}_out"] = r[0], r[1]
            if base_bars is None:
                base_bars = r[2]
        if base_bars is None:
            continue
        busy = fill_idx + base_bars
        rows.append(rec)
    return symbol, rows, "OK"


def main():
    from config.ict_instrument_policy import ict_active_symbols
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=365)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--symbols", type=str, default="")
    ap.add_argument("--end-days-ago", type=int, default=0)
    ap.add_argument("--tag", type=str, default="")
    ap.add_argument("--phantom-busy", action="store_true",
                    help="una señal descartada por spread bloquea el símbolo hasta su resultado virtual")
    args = ap.parse_args()
    syms = [s.strip() for s in args.symbols.split(",") if s.strip()] or list(ict_active_symbols("SYNTHETICS"))
    rows = []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futs = {pool.submit(run_symbol, s, args.days, args.end_days_ago, args.phantom_busy): s for s in syms}
        for f in as_completed(futs):
            s, rr, status = f.result()
            rows += rr
            print(f"{s}: {status} operaciones={len(rr)}", flush=True)
    df = pd.DataFrame(rows)
    suffix = f"_{args.tag}" if args.tag else ""
    df.to_csv(OUT / f"ict_exit_variants{suffix}.csv", index=False)
    print(f"\n{len(df)} operaciones")
    for name in VARIANTS:
        r = df[name].dropna()
        halves = df.groupby("period")[name].mean()
        print(f"{name:14s} n={len(r)} R/t={r.mean():+.3f} acierto={(r > 0).mean():.1%} "
              f"mitades {halves.get('H1_first', np.nan):+.3f} / {halves.get('H2_last', np.nan):+.3f}")


if __name__ == "__main__":
    main()
