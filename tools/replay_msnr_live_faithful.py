"""Replay FIEL de Malaysian SNR.

A diferencia de replay_malaysian_snr_full_universe.py, este script ejecuta el
MalaysianSNRStrategy.analyze_symbol REAL (con Fresh, Storyline D1, Killzones,
retest M15, Quasimodo y obstacle awareness) en cada cierre de vela M15, usando
SOLO velas cerradas hasta ese instante (sin lookahead).

Ejecucion realista:
  * La señal se genera al cierre de la vela M15 t; la entrada es a mercado en la
    APERTURA de la vela siguiente (+ spread real del simbolo en BUY).
  * SL estructural se conserva; targets se calculan con el fill y se limitan
    al techo estructural de la señal cuando existe un obstáculo.
  * Si SL y TP caen en la misma vela, gana el SL (peor caso).
  * Doble pierna: TP1=2R (50%), runner (50%) con BE al tocar TP1.
  * Un solo trade activo por simbolo (igual que el guardian en vivo).

Salida: storage/analysis/msnr_faithful_trades.csv y msnr_faithful_report.md
Uso:  python tools/replay_msnr_live_faithful.py --days 90 --symbols "Volatility 25 Index,XAUUSD"
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from strategy.malaysian_snr.config import MalaysianSNRConfig  # noqa: E402
from strategy.malaysian_snr.malaysian_snr_strategy import MalaysianSNRStrategy  # noqa: E402

DEFAULT_SYMBOLS = [
    "Volatility 10 Index", "Volatility 25 Index", "Volatility 75 Index",
    "Step Index", "Jump 25 Index", "Boom 1000 Index", "Crash 1000 Index",
    "XAUUSD", "XAGUSD", "BTCUSD", "US Tech 100", "Wall Street 30",
    "EURUSD", "USDJPY", "US Oil",
]
TF_MINUTES = {"M15": 15, "H1": 60, "D1": 1440}
MAX_HOLD_BARS = 200


class HistoricalProvider:
    """Expone SOLO velas cerradas hasta `self.now` (sin lookahead)."""

    def __init__(self, frames: dict[str, pd.DataFrame]):
        self.now = None
        self._frames = {}
        for tf, df in frames.items():
            close_ts = (df["time"] + pd.Timedelta(minutes=TF_MINUTES[tf])).values.astype("datetime64[ns]")
            self._frames[tf] = (df.reset_index(drop=True), close_ts)

    def get_candles(self, symbol, timeframe, count=100):
        df, close_ts = self._frames[timeframe]
        idx = int(np.searchsorted(close_ts, np.datetime64(self.now.tz_convert("UTC").tz_localize(None)), side="right"))
        return df.iloc[max(0, idx - count):idx].copy()


def load_frames(mt5, symbol: str, days: int):
    end = datetime.now(timezone.utc)
    frames = {}
    for tf, const, extra in (("M15", mt5.TIMEFRAME_M15, 5), ("H1", mt5.TIMEFRAME_H1, 10), ("D1", mt5.TIMEFRAME_D1, 40)):
        rates = mt5.copy_rates_range(symbol, const, end - timedelta(days=days + extra), end)
        if rates is None or len(rates) < 50:
            return None
        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
        frames[tf] = df
    return frames


def simulate(direction, entry, sl, tp1, tp2, h, l, c, *, opens=None, spreads=None,
             leg1_weight=0.5, leg2_weight=0.5, cost_r=0.0):
    """Devuelve (rr_total, resultado) sobre arrays M15 posteriores al fill."""
    risk = abs(entry - sl)
    if risk <= 0 or len(h) == 0:
        return 0.0, "NO_DATA", 0
    sign = 1 if direction == "BUY" else -1
    tp1_rr = sign * (tp1 - entry) / risk
    tp2_rr = sign * (tp2 - entry) / risk
    def pnl(move1, move2):
        return leg1_weight * move1 + leg2_weight * move2 - cost_r

    leg1_done = False
    for i in range(min(len(h), MAX_HOLD_BARS)):
        # MT5 candle OHLC are bid prices; short positions close on ask.
        spread = float(spreads[i]) if spreads is not None else 0.0
        shift = spread if direction == "SELL" else 0.0
        high, low = h[i] + shift, l[i] + shift
        active_sl = entry if leg1_done else sl
        if opens is not None:
            opening = opens[i] + shift
            if sign * (opening - active_sl) <= 0:
                move = sign * (opening - entry) / risk
                return (pnl(tp1_rr, move) if leg1_done else pnl(move, move)), "GAP_SL", i + 1
        if direction == "BUY":
            hit_sl = low <= active_sl
            hit_tp1, hit_tp2 = high >= tp1, high >= tp2
        else:
            hit_sl = high >= active_sl
            hit_tp1, hit_tp2 = low <= tp1, low <= tp2
        if not leg1_done:
            if hit_sl:
                return pnl(-1.0, -1.0), "SL", i + 1
            if hit_tp1:
                leg1_done = True
                # Unknown intrabar order: allow a return to BE after TP1.
                hit_new_be = low <= entry if direction == "BUY" else high >= entry
                if hit_new_be:
                    return pnl(tp1_rr, 0.0), "TP1+BE_AMBIGUOUS", i + 1
                if hit_tp2:
                    return pnl(tp1_rr, tp2_rr), "TP2", i + 1
        else:
            if hit_sl:
                return pnl(tp1_rr, 0.0), "TP1+BE", i + 1
            if hit_tp2:
                return pnl(tp1_rr, tp2_rr), "TP2", i + 1
    n = min(len(h), MAX_HOLD_BARS) - 1
    if n < 0:
        return 0.0, "NO_DATA", 0
    exit_price = c[n] + (float(spreads[n]) if direction == "SELL" and spreads is not None else 0.0)
    r = float(sign * (exit_price - entry) / risk)
    return (pnl(tp1_rr, r) if leg1_done else pnl(r, r)), "TIMEOUT", n + 1


def replay_symbol(mt5, symbol: str, days: int, cfg: MalaysianSNRConfig):
    mt5.symbol_select(symbol, True)
    frames = load_frames(mt5, symbol, days)
    if frames is None:
        print(f"  {symbol}: datos insuficientes")
        return []
    info = mt5.symbol_info(symbol)
    spread = float(info.spread) * float(info.point) if info else 0.0

    return replay_frames(symbol, frames, days, cfg, spread)


def replay_frames(symbol: str, frames: dict, days: int, cfg: MalaysianSNRConfig,
                  spread: float, cost_r: float = 0.0):
    """Same causal detector for saved data and terminal data; no order sending."""

    provider = HistoricalProvider(frames)
    strat = MalaysianSNRStrategy(provider, cfg)
    m15 = frames["M15"].reset_index(drop=True)
    h, l, c, o = (m15[k].values.astype(float) for k in ("high", "low", "close", "open"))
    start_cut = m15["time"].iloc[-1] - pd.Timedelta(days=days)
    trades, busy_until = [], -1

    for i in range(100, len(m15) - 2):
        if m15["time"].iloc[i] < start_cut or i <= busy_until:
            continue
        provider.now = m15["time"].iloc[i] + pd.Timedelta(minutes=15)  # cierre de la vela i
        res = strat.analyze_symbol(symbol, now_utc=provider.now.to_pydatetime())
        if not res.get("valid"):
            continue
        sig = res["signal"]
        direction = sig["direction"]
        fill = o[i + 1] + (spread if direction == "BUY" else 0.0)
        sl = sig["stop_loss"]
        sign = 1 if direction == "BUY" else -1
        sig_risk = sign * (fill - sl)
        if sig_risk <= 0:
            continue
        rr2 = float(sig["runner_rr"])
        if sig.get("obstacle_level"):
            room_rr = sign * (sig["tp2_price"] - fill) / sig_risk
            if room_rr < cfg.tp1_min_rr:
                continue
            rr2 = min(rr2, room_rr)
        tp1, tp2 = fill + sign * cfg.tp1_min_rr * sig_risk, fill + sign * rr2 * sig_risk
        # Only fully closed outcome bars are available at the dataset boundary.
        future_end = len(m15) - 1
        rr_total, outcome, bars = simulate(direction, fill, sl, tp1, tp2,
            h[i + 1:future_end], l[i + 1:future_end], c[i + 1:future_end],
            opens=o[i + 1:future_end], spreads=np.full(future_end - i - 1, spread),
            leg1_weight=cfg.leg1_risk_ratio, leg2_weight=cfg.leg2_risk_ratio, cost_r=cost_r)
        busy_until = i + bars
        trades.append({
            "symbol": symbol, "time": str(provider.now), "exit_time": str(m15["time"].iloc[i + bars] + pd.Timedelta(minutes=15)),
            "strategy_version": cfg.strategy_version, "scenario": sig["scenario"],
            "direction": direction, "adx": sig["adx"], "body_ratio": sig["body_ratio"],
            "runner_rr": rr2, "risk_atr": sig_risk / sig["atr"] if sig.get("atr") else np.nan,
            "hour_utc": provider.now.hour, "outcome": outcome, "rr": round(rr_total, 3), "bars": bars,
            "entry_price": fill, "stop_loss": sl, "tp1_price": tp1, "tp2_price": tp2,
            "estimated_spread": spread, "extra_cost_r": cost_r,
        })
    return trades


def bucket_table(df: pd.DataFrame, col: str, bins=None):
    d = df.copy()
    if bins is not None:
        d[col] = pd.cut(d[col], bins=bins)
    g = d.groupby(col, observed=True).agg(trades=("rr", "size"), win_pct=("rr", lambda s: 100 * (s > 0).mean()),
                                         exp_r=("rr", "mean"), total_r=("rr", "sum")).round(2)
    return g.reset_index()


def write_report(df: pd.DataFrame, path: Path, days: int):
    lines = [f"# Malaysian SNR - Replay FIEL ({days} dias, estrategia real, sin lookahead)\n"]
    tot = len(df)
    lines.append(f"- Trades: **{tot}** | Win% (rr>0): **{100*(df.rr>0).mean():.1f}%** | "
                 f"Expectativa: **{df.rr.mean():+.3f} R/trade** | Total: **{df.rr.sum():+.1f} R**\n")
    sections = [("Por simbolo", "symbol", None), ("Por escenario", "scenario", None),
                ("Por direccion", "direction", None), ("Por ADX", "adx", [0, 20, 25, 30, 40, 100]),
                ("Por body ratio", "body_ratio", [0, .5, .6, .7, .8, 1.0]),
                ("Por hora UTC", "hour_utc", [-1, 6, 10, 12, 16, 20, 24])]
    for title, col, bins in sections:
        t = bucket_table(df, col, bins)
        lines.append(f"\n## {title}\n\n| {col} | trades | win% | R/trade | R total |\n|---|---|---|---|---|")
        for _, r in t.sort_values("exp_r", ascending=False).iterrows():
            lines.append(f"| {r[col]} | {int(r.trades)} | {r.win_pct} | {r.exp_r:+} | {r.total_r:+} |")
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=90)
    ap.add_argument("--symbols", type=str, default=",".join(DEFAULT_SYMBOLS))
    args = ap.parse_args()

    import MetaTrader5 as mt5
    if not mt5.initialize():
        raise SystemExit("No se pudo inicializar MT5")
    cfg = MalaysianSNRConfig()
    out = PROJECT_ROOT / "storage" / "analysis"
    out.mkdir(parents=True, exist_ok=True)
    all_trades = []
    for sym in [s.strip() for s in args.symbols.split(",") if s.strip()]:
        print(f"[{sym}] replay...", flush=True)
        tr = replay_symbol(mt5, sym, args.days, cfg)
        if tr:
            d = pd.DataFrame(tr)
            print(f"  {len(d)} trades | win {100*(d.rr>0).mean():.1f}% | {d.rr.mean():+.3f} R/trade | {d.rr.sum():+.1f} R", flush=True)
        else:
            print("  0 trades", flush=True)
        all_trades += tr
    mt5.shutdown()
    if not all_trades:
        print("Sin trades.")
        return
    df = pd.DataFrame(all_trades)
    df.to_csv(out / "msnr_faithful_trades.csv", index=False)
    write_report(df, out / "msnr_faithful_report.md", args.days)
    print(f"\nReporte: {out / 'msnr_faithful_report.md'}")


if __name__ == "__main__":
    main()
