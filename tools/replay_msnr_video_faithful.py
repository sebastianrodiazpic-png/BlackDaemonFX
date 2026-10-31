"""Replay FIEL del worker MSNR vídeos (escenario H4→H1) con la clase real `MSNRVideoStrategy` (solo lectura).

- Solo velas cerradas: la estrategia se evalúa en cada cierre H1 (el escenario solo cambia al cerrar una H1).
- Entrada en la apertura de la vela M15 siguiente (BUY al ask = +spread), SL de la señal, riesgo desde el fill.
- Tope spread/SL 2 % (como en vivo); una operación por símbolo hasta su resultado.
- Gestión del contrato: TP1 1R (50 %) + runner 2R con BE tras TP1 (`tools.replay_msnr_live_faithful.simulate`).
- La política de dirección del bot (Boom solo BUY, Crash solo SELL) la aplica la propia estrategia.

Uso: python tools/replay_msnr_video_faithful.py --start 2023-12-20 --end 2024-06-30 --workers 6 --tag D
Salida: storage/analysis/msnr_video_faithful_<tag>.csv
"""
from __future__ import annotations

import argparse
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "storage" / "analysis"
SPREAD_CAP = 0.02


def run_symbol(symbol, start, end, spread_override=None, all_markets=False, spread_cap=SPREAD_CAP):
    import MetaTrader5 as mt5
    from strategy.malaysian_snr.video_strategy import MSNRVideoConfig, MSNRVideoStrategy
    from tools.replay_msnr_live_faithful import HistoricalProvider, simulate

    start, end = pd.Timestamp(start, tz="UTC"), pd.Timestamp(end, tz="UTC")
    if not mt5.initialize():
        return symbol, [], "MT5_INIT"
    mt5.symbol_select(symbol, True)
    frames = {}
    for tf, const, warmup in (("M15", mt5.TIMEFRAME_M15, 2), ("H1", mt5.TIMEFRAME_H1, 15),
                              ("H4", mt5.TIMEFRAME_H4, 80), ("D1", mt5.TIMEFRAME_D1, 220)):
        rates = mt5.copy_rates_range(symbol, const, (start - timedelta(days=warmup)).to_pydatetime(),
                                     (end + timedelta(days=5)).to_pydatetime())
        if rates is None or len(rates) < 50:
            mt5.shutdown()
            return symbol, [], f"SIN_DATOS_{tf}"
        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
        frames[tf] = df
    info = mt5.symbol_info(symbol)
    mt5.shutdown()
    spread = float(spread_override) if spread_override else float(info.spread) * float(info.point)

    class Provider(HistoricalProvider):
        def get_current_tick(self, _symbol):
            m15, close_ts = self._frames["M15"]
            idx = int(np.searchsorted(close_ts, np.datetime64(self.now.tz_convert("UTC").tz_localize(None)), side="right"))
            price = float(m15["close"].iloc[max(0, idx - 1)])
            return {"bid": price, "ask": price + spread}

    provider = Provider(frames)
    strategy = MSNRVideoStrategy(provider, MSNRVideoConfig(synthetics_only=not all_markets))
    m15 = frames["M15"].reset_index(drop=True)
    o, h, l, c = (m15[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    m15_times = m15["time"].to_numpy(dtype="datetime64[ns]")
    h1_close = (frames["H1"]["time"] + pd.Timedelta(hours=1))
    h1_close = h1_close[(h1_close >= start) & (h1_close <= end)]
    mid = start + (end - start) / 2
    rows, busy_until = [], pd.Timestamp("1970-01-01", tz="UTC")
    for now in h1_close:
        if now < busy_until:
            continue
        provider.now = now + pd.Timedelta(seconds=1)
        res = strategy.analyze_symbol(symbol, now_utc=provider.now.to_pydatetime())
        if not res.get("valid"):
            continue
        sig = res["signal"]
        direction, sl = sig["direction"], float(sig["stop_loss"])
        sign = 1 if direction == "BUY" else -1
        i = int(np.searchsorted(m15_times, np.datetime64(now.tz_localize(None)), side="left"))
        if i >= len(m15) - 2:
            break
        fill = o[i] + (spread if sign > 0 else 0.0)
        risk = sign * (fill - sl)
        if risk <= 0 or spread / risk > spread_cap:
            continue
        rr, outcome, bars = simulate(direction, fill, sl, fill + sign * risk, fill + sign * 2.0 * risk,
                                     h[i:], l[i:], c[i:], opens=o[i:], spreads=np.full(len(m15) - i, spread))
        rows.append({"symbol": symbol, "time": str(now), "half": 1 if now < mid else 2, "direction": direction,
                     "fill": fill, "stop_loss": sl, "risk": risk, "spread_sl": spread / risk, "rr": rr,
                     "outcome": outcome, "bars": bars, "storyline_alignment": sig.get("storyline_alignment")})
        busy_until = pd.Timestamp(m15["time"].iloc[min(len(m15) - 1, i + max(1, bars))])
    return symbol, rows, "OK"


def main():
    from config.ict_instrument_policy import MSNR_ACTIVE
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--symbols", default="")
    ap.add_argument("--tag", default="")
    ap.add_argument("--spread-file", default="", help="JSON con el spread real de ticks por símbolo")
    ap.add_argument("--all-markets", action="store_true", help="quita la restricción de solo sintéticos")
    ap.add_argument("--spread-cap", type=float, default=SPREAD_CAP)
    args = ap.parse_args()
    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()] or list(MSNR_ACTIVE)
    import json
    spreads = {k: v["spread"] for k, v in json.load(open(args.spread_file, encoding="utf-8")).items()} if args.spread_file else {}
    rows = []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(run_symbol, s, args.start, args.end, spreads.get(s), args.all_markets, args.spread_cap): s
                   for s in symbols}
        for future in as_completed(futures):
            symbol, trades, status = future.result()
            rows += trades
            print(f"{symbol}: {status} operaciones={len(trades)}", flush=True)
    df = pd.DataFrame(rows)
    suffix = f"_{args.tag}" if args.tag else ""
    df.to_csv(OUT / f"msnr_video_faithful{suffix}.csv", index=False)
    if len(df):
        for name, part in (("TOTAL", df), ("mitad 1", df[df.half == 1]), ("mitad 2", df[df.half == 2])):
            r = part.rr
            t = r.mean() / (r.std(ddof=1) / np.sqrt(len(r))) if len(r) > 2 else float("nan")
            print(f"{name}: n={len(r)} R/op={r.mean():+.3f} t={t:+.2f} acierto={(r > 0).mean() * 100:.0f}%")


if __name__ == "__main__":
    main()
