"""H1 — Momentum intradía en índices US (Gao, Han, Li y Zhou, 2018). Solo lectura; no toca el bot.

Reglas pre-registradas en storage/analysis/research_preregistro_20261019.md:
  * Señal: r1 = close(10:00 NY) / close(16:00 NY día previo) - 1   (variante: / open 09:30 NY).
  * Entrada en la apertura de la vela M5 de 15:30 NY en la dirección de r1; salida en el cierre de 15:55.
  * Coste: spread de la vela de entrada (columna `spread` en puntos del CSV de MT5).
  * Variante con SL a 1x ATR(14) de M30 para expresar el resultado en R.

Uso: python tools/research_intraday_momentum.py
Salida: storage/analysis/research_intraday_momentum_trades.csv y _report.md
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
HIST = ROOT / "storage" / "analysis" / "orb_nunez_2y" / "history"
OUT = ROOT / "storage" / "analysis"
SYMBOLS = {"US SP 500": "US_SP_500_M5.csv", "US Tech 100": "US_Tech_100_M5.csv", "Wall Street 30": "Wall_Street_30_M5.csv"}
NY = "America/New_York"


def symbol_points():
    try:
        import MetaTrader5 as mt5
        if not mt5.initialize():
            raise RuntimeError
        pts = {s: float(mt5.symbol_info(s).point) for s in SYMBOLS}
        mt5.shutdown()
        return pts
    except Exception:
        return {s: 0.01 for s in SYMBOLS}


def daily_trades(symbol, path, point):
    df = pd.read_csv(path)
    df["time"] = pd.to_datetime(df["time"], utc=True)
    df = df.sort_values("time").drop_duplicates("time").reset_index(drop=True)
    df["ny"] = df["time"].dt.tz_convert(NY)
    df["d"] = df["ny"].dt.date
    df["hm"] = df["ny"].dt.hour * 100 + df["ny"].dt.minute
    # ATR(14) de M30 conocido al inicio de cada vela (solo velas cerradas)
    m30 = df.set_index("time")[["high", "low", "close"]].resample("30min").agg(
        {"high": "max", "low": "min", "close": "last"}).dropna()
    tr = pd.concat([m30.high - m30.low, (m30.high - m30.close.shift()).abs(), (m30.low - m30.close.shift()).abs()], axis=1).max(axis=1)
    atr30 = tr.rolling(14).mean().shift(1)  # ATR de velas M30 ya cerradas
    rows, prev_close = [], None
    for d, g in df.groupby("d"):
        g = g.set_index("hm")
        need = [930, 955, 1530, 1555]
        if not all(k in g.index for k in need) or g.loc[930, "ny"].weekday() >= 5:
            prev_close = float(g.loc[1555, "close"]) if 1555 in g.index else prev_close
            continue
        c10, o930 = float(g.loc[955, "close"]), float(g.loc[930, "open"])
        entry_bar, exit_bar = g.loc[1530], g.loc[1555]
        o_entry = float(entry_bar["open"])
        spread = float(entry_bar.get("spread", 0) or 0) * point
        window = g.loc[[k for k in g.index if 1530 <= k <= 1555]]
        atr = atr30.asof(entry_bar["time"])
        for spec, base in (("PRINCIPAL", prev_close), ("SIN_NOCHE", o930)):
            if base is None or not np.isfinite(base):
                continue
            r1 = c10 / base - 1.0
            if r1 == 0:
                continue
            side = 1 if r1 > 0 else -1
            fill = o_entry + (spread if side > 0 else 0.0)
            exit_px = float(exit_bar["close"]) + (spread if side < 0 else 0.0)
            gross = side * (float(exit_bar["close"]) - o_entry)
            net = side * (exit_px - fill)
            rec = dict(symbol=symbol, date=str(d), spec=spec, direction="BUY" if side > 0 else "SELL",
                       r1_bps=1e4 * r1, entry=o_entry, exit=float(exit_bar["close"]), spread=spread,
                       gross_bps=1e4 * gross / o_entry, net_bps=1e4 * net / o_entry, atr30=atr)
            # Variante con SL 1x ATR M30 -> resultado en R
            if atr and np.isfinite(atr) and atr > 0:
                sl = fill - side * atr
                r_out = None
                for _, b in window.iterrows():
                    hi, lo = float(b["high"]), float(b["low"])
                    if (side > 0 and lo <= sl) or (side < 0 and hi + spread >= sl):
                        r_out = -1.0
                        break
                rec["r_sl"] = r_out if r_out is not None else net / atr
            rows.append(rec)
        prev_close = float(g.loc[1555, "close"])
    return rows


def summarize(t: pd.DataFrame, col: str, rng) -> dict:
    r = t[col].dropna()
    if len(r) < 5:
        return {}
    mid = pd.to_datetime(t["date"]).quantile(0.5)
    first = t[pd.to_datetime(t["date"]) <= mid][col].dropna()
    second = t[pd.to_datetime(t["date"]) > mid][col].dropna()
    # Test de azar: misma magnitud de movimiento, dirección aleatoria (el coste se mantiene)
    gross_col = "gross_bps" if col == "net_bps" else None
    if gross_col:
        g = t.loc[r.index, gross_col].values
        cost = (t.loc[r.index, gross_col] - t.loc[r.index, col]).values
        sims = np.array([(rng.choice([-1, 1], len(g)) * g - cost).mean() for _ in range(5000)])
    else:
        sims = np.array([(rng.choice([-1, 1], len(r)) * r.values).mean() for _ in range(5000)])
    gl = -r[r < 0].sum()
    return dict(n=len(r), media=r.mean(), t=r.mean() / (r.std(ddof=1) / np.sqrt(len(r))), wr=100 * (r > 0).mean(),
                pf=r[r > 0].sum() / gl if gl else np.inf, mitad1=first.mean(), mitad2=second.mean(),
                p_azar=(sims >= r.mean()).mean())


def main():
    pts = symbol_points()
    rows = []
    for s, f in SYMBOLS.items():
        rows += daily_trades(s, HIST / f, pts[s])
    t = pd.DataFrame(rows)
    t.to_csv(OUT / "research_intraday_momentum_trades.csv", index=False)
    rng = np.random.default_rng(2018)
    lines = ["# H1 — Momentum intradía en índices US (replay solo lectura)\n",
             f"Datos: M5 MT5 {t.date.min()} → {t.date.max()}. Reglas pre-registradas en `research_preregistro_20261019.md`.\n"]
    for spec in ("PRINCIPAL", "SIN_NOCHE"):
        for col, unit in (("net_bps", "bps netos"), ("r_sl", "R con SL 1×ATR M30")):
            lines.append(f"\n## {spec} — {unit}\n\n| segmento | n | media | t | WR% | PF | mitad 1 | mitad 2 | p azar |\n|---|---|---|---|---|---|---|---|---|")
            sub = t[t.spec == spec]
            for name, g in [("TODOS", sub)] + [(s, sub[sub.symbol == s]) for s in SYMBOLS] + \
                           [(f"dir {d}", sub[sub.direction == d]) for d in ("BUY", "SELL")]:
                m = summarize(g, col, rng)
                if m:
                    lines.append(f"| {name} | {m['n']} | {m['media']:+.3f} | {m['t']:+.2f} | {m['wr']:.1f} | {m['pf']:.2f} | "
                                 f"{m['mitad1']:+.3f} | {m['mitad2']:+.3f} | {m['p_azar']:.3f} |")
    (OUT / "research_intraday_momentum_report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    sys.exit(main())
