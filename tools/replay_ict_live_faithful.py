"""Replay FIEL de ICT Sabri Malle.

Ejecuta ICTSabriMalleStrategy.analyze_symbol REAL en cada cierre de vela M15 usando
SOLO velas cerradas (M15/H1/H4) hasta ese instante (sin lookahead).

Ejecucion realista (misma convencion que tools/replay_msnr_live_faithful.py):
  * Señal al cierre de la vela M15 t; entrada a mercado en la APERTURA de t+1 (+ spread en BUY).
  * SL de la señal (extremo del sweep); TP1=2R / runner calculados desde el fill real.
  * SL y TP en la misma vela -> gana el SL. Un trade activo por simbolo.
  * Variantes registradas por trade: rr (live: 50% @2R + runner @4R con BE),
    rr_r3 (runner 3R), rr_r2 (todo a 2R).

Uso: python tools/replay_ict_live_faithful.py --days 180 --symbols "XAUUSD,BTCUSD"
Salida: storage/analysis/ict_faithful_trades.csv y ict_faithful_report.md
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from strategy.ict.config import ICTSabriMalleConfig  # noqa: E402
from strategy.ict.ict_strategy import ICTSabriMalleStrategy, is_synthetic_asset  # noqa: E402
from tools.replay_msnr_live_faithful import simulate  # noqa: E402

NEW_YORK = ZoneInfo("America/New_York")
DEFAULT_SYMBOLS = [
    "Volatility 10 Index", "Volatility 25 Index", "Volatility 50 Index", "Volatility 75 Index",
    "Volatility 100 Index", "Step Index", "Jump 10 Index", "Jump 25 Index", "Jump 50 Index",
    "Jump 100 Index", "Boom 500 Index", "Boom 1000 Index", "Crash 500 Index", "Crash 1000 Index",
    "XAUUSD", "XAGUSD", "BTCUSD", "US Tech 100", "Wall Street 30", "US SP 500",
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD",
]
TF_MINUTES = {"M15": 15, "H1": 60, "H4": 240}
TF_COUNT = {"M15": 5, "H1": 10, "H4": 45}


class HistoricalProvider:
    """Expone SOLO velas cerradas hasta `self.now` (sin lookahead)."""

    def __init__(self, frames: dict[str, pd.DataFrame], spread: float):
        self.now = None
        self.spread = spread
        self._frames = {}
        for tf, df in frames.items():
            close_ts = (df["time"] + pd.Timedelta(minutes=TF_MINUTES[tf])).values.astype("datetime64[ns]")
            self._frames[tf] = (df.reset_index(drop=True), close_ts)

    def get_candles(self, symbol, timeframe, count=100):
        df, close_ts = self._frames[timeframe]
        idx = int(np.searchsorted(close_ts, np.datetime64(self.now.tz_convert("UTC").tz_localize(None)), side="right"))
        return df.iloc[max(0, idx - count):idx].copy()

    def get_current_tick(self, symbol):
        df, close_ts = self._frames["M15"]
        idx = int(np.searchsorted(close_ts, np.datetime64(self.now.tz_convert("UTC").tz_localize(None)), side="right"))
        price = float(df["close"].iloc[max(0, idx - 1)])
        return {"bid": price, "ask": price + self.spread}


def load_frames(mt5, symbol: str, days: int):
    end = datetime.now(timezone.utc)
    consts = {"M15": mt5.TIMEFRAME_M15, "H1": mt5.TIMEFRAME_H1, "H4": mt5.TIMEFRAME_H4}
    frames = {}
    for tf, const in consts.items():
        extra = TF_COUNT[tf] if tf != "H4" else 45
        rates = mt5.copy_rates_range(symbol, const, end - timedelta(days=days + extra), end)
        if rates is None or len(rates) < 50:
            return None
        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
        frames[tf] = df
    return frames


def replay_frames(symbol: str, frames: dict, days: int, cfg: ICTSabriMalleConfig, spread: float, cost_r: float = 0.0):
    provider = HistoricalProvider(frames, spread)
    strat = ICTSabriMalleStrategy(provider, cfg)
    m15 = frames["M15"].reset_index(drop=True)
    h, l, c, o = (m15[k].values.astype(float) for k in ("high", "low", "close", "open"))
    start_cut = m15["time"].iloc[-1] - pd.Timedelta(days=days)
    mid_cut = start_cut + pd.Timedelta(days=days / 2)
    trades, busy_until = [], -1
    synthetic = is_synthetic_asset(symbol)

    for i in range(100, len(m15) - 2):
        if m15["time"].iloc[i] < start_cut or i <= busy_until:
            continue
        provider.now = m15["time"].iloc[i] + pd.Timedelta(minutes=15)
        res = strat.analyze_symbol(symbol, now_utc=provider.now.to_pydatetime())
        if not res.get("valid"):
            continue
        sig = res["signal"]
        direction = sig["direction"]
        sign = 1 if direction == "BUY" else -1
        fill = o[i + 1] + (spread if direction == "BUY" else 0.0)
        sl = sig["stop_loss"]
        risk = sign * (fill - sl)
        if risk <= 0:
            continue
        future_end = len(m15) - 1
        args = (h[i + 1:future_end], l[i + 1:future_end], c[i + 1:future_end])
        kw = dict(opens=o[i + 1:future_end], spreads=np.full(future_end - i - 1, spread), cost_r=cost_r)

        def run(tp1_rr, tp2_rr):
            tp1 = fill + sign * tp1_rr * risk
            tp2 = fill + sign * tp2_rr * risk
            return simulate(direction, fill, sl, tp1, tp2, *args,
                            leg1_weight=cfg.leg1_risk_ratio, leg2_weight=cfg.leg2_risk_ratio, **kw)

        rr_live, outcome, bars = run(cfg.tp1_rr, cfg.runner_rr)
        rr_r3, _, _ = run(cfg.tp1_rr, 3.0)
        rr_r2, _, _ = run(2.0, 2.0)
        busy_until = i + bars
        ny = provider.now.tz_convert(NEW_YORK)
        trades.append({
            "symbol": symbol, "synthetic": synthetic, "time": str(provider.now),
            "period": "H1_first" if provider.now < mid_cut else "H2_last",
            "direction": direction, "ny_hour": ny.hour, "weekday": ny.dayofweek,
            "risk_pct": round(100 * risk / fill, 4), "body_ratio": sig["displacement_body_ratio"],
            "outcome": outcome, "rr": round(rr_live, 3), "rr_r3": round(rr_r3, 3), "rr_r2": round(rr_r2, 3),
            "bars": bars, "entry_price": fill, "stop_loss": sl,
        })
    return trades


def replay_symbol(mt5, symbol: str, days: int, cfg: ICTSabriMalleConfig):
    mt5.symbol_select(symbol, True)
    frames = load_frames(mt5, symbol, days)
    if frames is None:
        print(f"  {symbol}: datos insuficientes", flush=True)
        return []
    info = mt5.symbol_info(symbol)
    spread = float(info.spread) * float(info.point) if info else 0.0
    return replay_frames(symbol, frames, days, cfg, spread)


def table(df: pd.DataFrame, col: str, bins=None):
    d = df.copy()
    if bins is not None:
        d[col] = pd.cut(d[col], bins=bins)
    g = d.groupby(col, observed=True).agg(
        trades=("rr", "size"), win_pct=("rr", lambda s: 100 * (s > 0).mean()),
        exp_r=("rr", "mean"), total_r=("rr", "sum"),
        exp_r3=("rr_r3", "mean"), exp_r2=("rr_r2", "mean")).round(3)
    return g.reset_index()


def write_report(df: pd.DataFrame, path: Path, days: int):
    L = [f"# ICT Sabri Malle - Replay FIEL ({days} dias, estrategia real, sin lookahead)\n"]
    L.append(f"- Trades: **{len(df)}** | Win%: **{100 * (df.rr > 0).mean():.1f}%** | "
             f"Expectativa live (2R+runner 4R): **{df.rr.mean():+.3f} R** | Total: **{df.rr.sum():+.1f} R**")
    L.append(f"- Variante runner 3R: {df.rr_r3.mean():+.3f} R/trade | Todo a 2R: {df.rr_r2.mean():+.3f} R/trade\n")
    for title, col, bins in [("Por simbolo", "symbol", None), ("Sinteticos vs mercados", "synthetic", None),
                             ("Por direccion", "direction", None), ("Por hora NY", "ny_hour", None),
                             ("Por dia de semana (0=lun)", "weekday", None), ("Por periodo", "period", None),
                             ("Por riesgo %", "risk_pct", [0, .1, .25, .5, 1, 100]),
                             ("Por body ratio", "body_ratio", [0, .5, .6, .7, .8, 1.0])]:
        t = table(df, col, bins)
        L.append(f"\n## {title}\n\n| {col} | trades | win% | R/trade | R total | R/trade (runner3) | R/trade (2R) |\n|---|---|---|---|---|---|---|")
        for _, r in t.sort_values("exp_r", ascending=False).iterrows():
            L.append(f"| {r[col]} | {int(r.trades)} | {r.win_pct:.1f} | {r.exp_r:+} | {r.total_r:+} | {r.exp_r3:+} | {r.exp_r2:+} |")
    path.write_text("\n".join(L), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=90)
    ap.add_argument("--symbols", type=str, default=",".join(DEFAULT_SYMBOLS))
    args = ap.parse_args()

    import MetaTrader5 as mt5
    if not mt5.initialize():
        raise SystemExit("No se pudo inicializar MT5")
    cfg = ICTSabriMalleConfig()
    out = PROJECT_ROOT / "storage" / "analysis"
    out.mkdir(parents=True, exist_ok=True)
    all_trades = []
    for sym in [s.strip() for s in args.symbols.split(",") if s.strip()]:
        print(f"[{sym}] replay...", flush=True)
        tr = replay_symbol(mt5, sym, args.days, cfg)
        if tr:
            d = pd.DataFrame(tr)
            print(f"  {len(d)} trades | win {100 * (d.rr > 0).mean():.1f}% | {d.rr.mean():+.3f} R/trade | {d.rr.sum():+.1f} R", flush=True)
        else:
            print("  0 trades", flush=True)
        all_trades += tr
    mt5.shutdown()
    if not all_trades:
        print("Sin trades.")
        return
    df = pd.DataFrame(all_trades)
    df.to_csv(out / "ict_faithful_trades.csv", index=False)
    write_report(df, out / "ict_faithful_report.md", args.days)
    print(f"\nReporte: {out / 'ict_faithful_report.md'}")


if __name__ == "__main__":
    main()
