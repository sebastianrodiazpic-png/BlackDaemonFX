"""ORB SWEEP ampliado + gestión completa del bot (solo lectura; no toca el bot).

Señal: `sweep_signal` de tools/replay_orb_nunez_2y.py (paridad señal a señal con el modo vivo,
tests/test_orb_sweep_mode.py). Gestión simulada = contrato operativo:
  * 1% total en 2 patas de 0.5%: pata 1 cierra en TP1 (1R).
  * Pata 2: tras TP1, SL a Break Even + spread (+ swap si cruza noches); objetivo TP2 (2R).
  * Extensión progresiva (igual que el motor vivo, runner_extension_*): al llegar a 2R se fija +1R y se evalúa
    `evaluate_runner_continuation` (M5, 80 velas cerradas); si continúa, objetivo 3R (guard 2.5R -> +2R);
    al llegar a 3R se fija +2.5R y se vuelve a evaluar; si continúa, objetivo 4R. Sin continuación: cierre.
Se informa la variante FIJA (TP2) y la EXTENDIDA sobre las mismas señales.

Uso:
  python tools/replay_orb_sweep_expanded.py --fetch        # descarga M5 de los símbolos nuevos
  python tools/replay_orb_sweep_expanded.py --workers 6
Salida: storage/analysis/orb_sweep_expanded_trades.csv y _report.md
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
import tools.replay_orb_nunez_2y as R  # noqa: E402

OUT = ROOT / "storage" / "analysis"
# Histórico propio: no se sobrescribe storage/analysis/orb_nunez_2y (lo usa el test de paridad del SWEEP).
CACHE = OUT / "orb_sweep_expanded"
R.OUT = CACHE
SYMBOLS = ["XAUUSD", "XAGUSD", "US Oil", "UK Brent Oil", "US Tech 100", "Wall Street 30", "US SP 500",
           "US Small Cap 2000", "US Mid Cap 400", "BTCUSD", "ETHUSD", "EURUSD", "GBPUSD", "USDJPY",
           "USDCAD", "AUDUSD", "USDCHF", "NZDUSD", "XAUEUR"]
FIRST_TRIGGER, FIRST_LOCK, GUARD_TRIGGER, GUARD_LOCK = 2.0, 1.0, 2.5, 2.0
SECOND_TRIGGER, SECOND_LOCK, MAX_TARGET = 3.0, 2.5, 4.0


def managed_simulator(df, first, direction, stop, point):
    """Simula FIJA (TP2) y EXTENDIDA (TP3/TP4 progresivo) sobre la misma entrada."""
    from strategy.execution.runner_extension_manager import evaluate_runner_continuation
    if first >= len(df):
        return None
    side = 1 if direction == "BUY" else -1
    b = df.iloc[first]
    spread = max(0.0, float(b.spread) * point)
    entry = float(b.open) + (spread if side == 1 else 0.0)
    risk = side * (entry - stop)
    if risk <= 0 or not np.isfinite(risk):
        return None
    be = entry + side * spread

    def px(rr):
        return entry + side * rr * risk

    def run(extend):
        leg1 = None
        sl, target, stage = stop, px(2.0), 0
        for k in range(first, len(df)):
            bar = df.iloc[k]
            sp = max(0.0, float(bar.spread) * point)
            hi = float(bar.high) + (sp if side == -1 else 0.0)
            lo = float(bar.low) + (sp if side == -1 else 0.0)
            fav, adv = (hi, lo) if side == 1 else (lo, hi)
            if side * (adv - sl) <= 0:  # stop (primero en caso de ambigüedad)
                open_px = float(bar.open) + (sp if side == -1 else 0.0)
                fill = open_px if side * (open_px - sl) < 0 else sl
                r2 = side * (fill - entry) / risk
                return (leg1 if leg1 is not None else r2), r2, k
            if leg1 is None and side * (fav - px(1.0)) >= 0:
                leg1, sl = 1.0, be
                if side * (adv - be) <= 0:
                    return 1.0, side * (be - entry) / risk, k
            if leg1 is None:
                continue
            if not extend:
                if side * (fav - target) >= 0:
                    return leg1, 2.0, k
                continue
            # Extensión progresiva
            if stage == 0 and side * (fav - px(FIRST_TRIGGER)) >= 0:
                sl, stage = px(FIRST_LOCK), 1
                hist = df.iloc[max(0, k - 79):k + 1]
                if not evaluate_runner_continuation(hist, direction=direction, stage_rr=FIRST_TRIGGER).continue_runner:
                    return leg1, FIRST_TRIGGER, k
                target = px(SECOND_TRIGGER)
            elif stage == 1 and side * (fav - px(GUARD_TRIGGER)) >= 0 and side * (fav - px(SECOND_TRIGGER)) < 0:
                sl = px(GUARD_LOCK) if side * (px(GUARD_LOCK) - sl) > 0 else sl
            if stage == 1 and side * (fav - px(SECOND_TRIGGER)) >= 0:
                sl, stage = px(SECOND_LOCK), 2
                hist = df.iloc[max(0, k - 79):k + 1]
                if not evaluate_runner_continuation(hist, direction=direction, stage_rr=SECOND_TRIGGER).continue_runner:
                    return leg1, SECOND_TRIGGER, k
                target = px(MAX_TARGET)
            if stage == 2 and side * (fav - target) >= 0:
                return leg1, MAX_TARGET, k
        return None

    fixed, ext = run(False), run(True)
    if fixed is None or ext is None:
        return None
    nights = max(0, (df.time.iloc[ext[2]] - b.time).days)
    return {"entry_time": str(b.time), "entry_price": entry, "stop_loss": stop, "risk_distance": risk,
            "spread_entry": spread, "spread_to_sl": spread / risk,
            "leg1_r": fixed[0], "leg2_r": fixed[1], "net_r": 0.5 * (fixed[0] + fixed[1]),
            "leg2_r_ext": ext[1], "net_r_ext": 0.5 * (ext[0] + ext[1]), "nights_ext": nights,
            "closed": True, "leg1_exit": None, "leg2_exit": None, "leg1_reason": None, "leg2_reason": None,
            "tp1_price": px(1.0), "tp2_price": px(2.0), "be_price": be, "ambiguity_bars": 0}


def run_one(symbol):
    import strategy.orb.new_york_orb as orb
    R.OUT = CACHE
    R.START = pd.Timestamp("2024-10-03", tz="UTC")
    R.END = pd.Timestamp.now(tz="UTC").normalize()
    # Símbolos sin mercado ORB propio: perfil genérico de investigación (el de EURUSD en el replay base).
    original = orb.classify_orb_market
    orb.classify_orb_market = lambda s: original(s) or "EURUSD"
    try:
        s, cov, trades, _ = R.run_symbol(symbol, simulator=managed_simulator)
    except Exception as exc:  # símbolo sin perfil ORB o sin datos
        return symbol, {"status": f"ERROR {type(exc).__name__}: {exc}"}, []
    return s, cov, [t for t in trades if t["variant"] in ("SWEEP", "HTF_SWEEP")]


def stats(r):
    r = pd.Series(r, dtype=float).dropna()
    if len(r) < 3:
        return dict(n=len(r), m=np.nan, t=np.nan, pf=np.nan, wr=np.nan)
    gl = -r[r < 0].sum()
    return dict(n=len(r), m=r.mean(), t=r.mean() / (r.std(ddof=1) / np.sqrt(len(r))),
                pf=r[r > 0].sum() / gl if gl else np.inf, wr=100 * (r > 0).mean())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()
    if args.fetch:
        CACHE.mkdir(parents=True, exist_ok=True)
        R.SYMBOLS = SYMBOLS
        R.START = pd.Timestamp("2024-10-03", tz="UTC")
        R.END = pd.Timestamp.now(tz="UTC").normalize()
        R.fetch()
        return
    rows = []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for f in as_completed([pool.submit(run_one, s) for s in SYMBOLS]):
            s, cov, tr = f.result()
            rows += tr
            print(f"{s}: {cov.get('status')} {cov.get('first', '')[:10]}->{cov.get('last', '')[:10]} trades={len(tr)}", flush=True)
    t = pd.DataFrame(rows)
    t.to_csv(OUT / "orb_sweep_expanded_trades.csv", index=False)
    t["ts"] = pd.to_datetime(t.signal_time, utc=True)
    mid = t.ts.quantile(0.5)
    t["mitad"] = np.where(t.ts <= mid, 1, 2)
    L = ["# ORB SWEEP ampliado — gestión 1% en 2 patas, BE, TP2 fijo vs extensión TP3/TP4\n",
         f"Señal con paridad del modo vivo; mitades separadas en {mid.date()}.\n",
         "| variante | símbolo | n | R/t FIJA | R/t EXTENDIDA | t ext | PF ext | WR ext | mitad1 ext | mitad2 ext |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for (v, s), g in sorted(t.groupby(["variant", "symbol"]), key=lambda kv: -kv[1].net_r_ext.mean()):
        a, e = stats(g.net_r), stats(g.net_r_ext)
        e1, e2 = stats(g[g.mitad == 1].net_r_ext), stats(g[g.mitad == 2].net_r_ext)
        L.append(f"| {v} | {s} | {e['n']} | {a['m']:+.3f} | {e['m']:+.3f} | {e['t']:+.2f} | {e['pf']:.2f} | {e['wr']:.1f} | {e1['m']:+.3f} | {e2['m']:+.3f} |")
    for v, g in t.groupby("variant"):
        a, e = stats(g.net_r), stats(g.net_r_ext)
        L.append(f"| {v} | **TODOS** | {e['n']} | {a['m']:+.3f} | {e['m']:+.3f} | {e['t']:+.2f} | {e['pf']:.2f} | {e['wr']:.1f} | "
                 f"{stats(g[g.mitad == 1].net_r_ext)['m']:+.3f} | {stats(g[g.mitad == 2].net_r_ext)['m']:+.3f} |")
    (OUT / "orb_sweep_expanded_report.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
