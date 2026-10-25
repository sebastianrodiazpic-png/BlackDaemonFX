"""Replay fiel ICT: entrada LIMITADA en signal["entry_price"] vs entrada a MERCADO, mismas señales.

ICTSabriMalleStrategy calcula entry_price en el 50% del FVG / nivel roto / mean threshold del OB y fija
SL/TP respecto a ese precio, pero el bot ejecuta a mercado. Aquí se miden ambas ejecuciones:
  * MERCADO: fill en la apertura de la vela siguiente (+spread en BUY), TPs desde el fill (como hoy).
  * LIMITE: orden limitada en entry_price válida LIMIT_BARS velas M15. BUY se llena si ask <= límite
    (bid low <= límite - spread); SELL si bid high >= límite. Si el SL se toca en la vela del fill = pérdida.
    Si el límite ya es alcanzable (lado "malo"), se trata como fill a mercado. Sin fill en plazo = no hay trade.
Cada modo respeta su propio "un trade activo por símbolo".

Uso: python tools/replay_ict_limit_entry.py --days 365 --workers 6
Salida: storage/analysis/ict_limit_entry_signals.csv y ict_limit_entry_report.md
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


def load_frames_until(mt5, symbol, days, end):
    """Como replay_ict_live_faithful.load_frames pero con fecha de fin explícita (para años previos)."""
    from datetime import timedelta
    consts = {"M15": mt5.TIMEFRAME_M15, "H1": mt5.TIMEFRAME_H1, "H4": mt5.TIMEFRAME_H4}
    extra = {"M15": 5, "H1": 10, "H4": 45}
    frames = {}
    for tf, const in consts.items():
        rates = mt5.copy_rates_range(symbol, const, end - timedelta(days=days + extra[tf]), end)
        if rates is None or len(rates) < 50:
            return None
        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
        frames[tf] = df
    return frames


def run_symbol(symbol: str, days: int, end_days_ago: int = 0):
    import MetaTrader5 as mt5
    from strategy.ict.config import ICTSabriMalleConfig
    from strategy.ict.ict_strategy import ICTSabriMalleStrategy, is_synthetic_asset
    from tools.replay_ict_live_faithful import HistoricalProvider, load_frames
    from tools.replay_msnr_live_faithful import simulate

    if not mt5.initialize():
        return symbol, [], "MT5_INIT"
    mt5.symbol_select(symbol, True)
    from datetime import datetime, timedelta, timezone
    end = datetime.now(timezone.utc) - timedelta(days=end_days_ago)
    frames = load_frames(mt5, symbol, days) if end_days_ago == 0 else load_frames_until(mt5, symbol, days, end)
    info = mt5.symbol_info(symbol)
    mt5.shutdown()
    if frames is None or info is None:
        return symbol, [], "SIN_DATOS"
    spread = float(info.spread) * float(info.point)
    cfg = ICTSabriMalleConfig(excluded_symbols=())
    provider = HistoricalProvider(frames, spread)
    strat = ICTSabriMalleStrategy(provider, cfg)
    m15 = frames["M15"].reset_index(drop=True)
    h, l, c, o = (m15[k].values.astype(float) for k in ("high", "low", "close", "open"))
    start_cut = m15["time"].iloc[-1] - pd.Timedelta(days=days)
    mid_cut = start_cut + pd.Timedelta(days=days / 2)
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
        rr, out, bars = simulate(direction, fill, sl, fill + sign * tp1_rr * risk, fill + sign * tp2_rr * risk,
                                 h[start:], l[start:], c[start:], opens=o[start:], spreads=spreads[start:],
                                 leg1_weight=cfg.leg1_risk_ratio, leg2_weight=cfg.leg2_risk_ratio)
        return rr, out, bars + (start - fill_idx), risk

    rows, busy = [], {"MERCADO": -1, "LIMITE": -1}
    for i in range(100, n - 2):
        if m15["time"].iloc[i] < start_cut:
            continue
        if i <= busy["MERCADO"] and i <= busy["LIMITE"]:
            continue
        provider.now = m15["time"].iloc[i] + pd.Timedelta(minutes=15)
        res = strat.analyze_symbol(symbol, now_utc=provider.now.to_pydatetime())
        if not res.get("valid"):
            continue
        sig = res["signal"]
        d, sl, lim = sig["direction"], float(sig["stop_loss"]), float(sig["entry_price"])
        sign = 1 if d == "BUY" else -1
        rec = dict(symbol=symbol, synthetic=is_synthetic_asset(symbol), time=str(provider.now),
                   period="H1_first" if provider.now < mid_cut else "H2_last", direction=d, limit=lim, stop_loss=sl,
                   close=float(c[i]), spread=spread)
        # MERCADO (comportamiento actual)
        if i > busy["MERCADO"]:
            fill = o[i + 1] + (spread if d == "BUY" else 0.0)
            r = outcome(d, i + 1, fill, sl, cfg.tp1_rr, cfg.runner_rr, check_fill_bar=False)
            if r:
                rec.update(mkt_rr=r[0], mkt_out=r[1], mkt_risk=r[3], mkt_fill=fill)
                busy["MERCADO"] = i + 1 + r[2]
        # LIMITE en entry_price
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
    return symbol, rows, "OK"


def stats(r):
    r = pd.Series(r, dtype=float).dropna()
    if len(r) < 3:
        return dict(n=len(r), m=np.nan, t=np.nan, pf=np.nan, wr=np.nan)
    gl = -r[r < 0].sum()
    return dict(n=len(r), m=r.mean(), t=r.mean() / (r.std(ddof=1) / np.sqrt(len(r))), pf=r[r > 0].sum() / gl if gl else np.inf,
                wr=100 * (r > 0).mean())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=365)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--symbols", type=str, default="")
    ap.add_argument("--end-days-ago", type=int, default=0, help="desplaza el fin del periodo (365 = año previo)")
    ap.add_argument("--tag", type=str, default="", help="sufijo de los ficheros de salida")
    args = ap.parse_args()
    if args.symbols:
        syms = [s.strip() for s in args.symbols.split(",") if s.strip()]
    else:
        syms = sorted(pd.read_csv(OUT / "ict_faithful_365d_v2_trades.csv", usecols=["symbol"]).symbol.unique())
    rows = []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futs = {pool.submit(run_symbol, s, args.days, args.end_days_ago): s for s in syms}
        for f in as_completed(futs):
            s, rr, status = f.result()
            rows += rr
            print(f"{s}: {status} señales={len(rr)}", flush=True)
    df = pd.DataFrame(rows)
    suffix = f"_{args.tag}" if args.tag else ""
    df.to_csv(OUT / f"ict_limit_entry_signals{suffix}.csv", index=False)
    L = ["# ICT — entrada LIMITADA (diseño de la estrategia) vs MERCADO (bot actual)\n",
         f"Replay fiel {args.days} días, {df.symbol.nunique()} símbolos, límite válido {LIMIT_BARS} velas M15.\n",
         "| universo | modo | n | R/trade | t | PF | WR% | mitad 1 | mitad 2 |", "|---|---|---|---|---|---|---|---|---|"]
    for uname, u in (("TODOS", df), ("Sintéticos", df[df.synthetic]), ("Mercados reales", df[~df.synthetic])):
        for mode, col in (("MERCADO", "mkt_rr"), ("LIMITE", "lim_rr")):
            if col not in u:
                continue
            a, b1, b2 = stats(u[col]), stats(u[u.period == "H1_first"][col]), stats(u[u.period == "H2_last"][col])
            L.append(f"| {uname} | {mode} | {a['n']} | {a['m']:+.3f} | {a['t']:+.2f} | {a['pf']:.2f} | {a['wr']:.1f} | {b1['m']:+.3f} | {b2['m']:+.3f} |")
    if "lim_fill" in df:
        L.append(f"\nFills del límite: {df.lim_fill.value_counts(dropna=False).to_dict()}")
    both = df.dropna(subset=["mkt_rr", "lim_rr"]) if {"mkt_rr", "lim_rr"} <= set(df) else df.iloc[0:0]
    if len(both):
        diff = both.lim_rr - both.mkt_rr
        L.append(f"\nMismas señales con ambos trades (n={len(both)}): límite − mercado = {diff.mean():+.3f} R/trade "
                 f"(t={diff.mean() / (diff.std(ddof=1) / np.sqrt(len(diff))):+.2f})")
    (OUT / f"ict_limit_entry_report{suffix}.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
