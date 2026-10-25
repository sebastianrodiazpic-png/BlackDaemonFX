"""Investigación (solo lectura): re-medición de los replays de sintéticos de ICT y MSNR con el spread REAL — 23-oct-2026.

El campo `spread` de las velas MT5 es el mínimo del periodo; los replays lo usaron como coste. Aquí:
  1. Se mide por símbolo el factor = mediana del spread de ticks (últimos 2 días) / mediana del campo spread M15.
  2. Se recalcula cada operación de los replays guardados:
       R_real = R_replay − (factor − 1) × spread/riesgo       (un spread por operación: entrada BUY / salida SELL)
     y se descarta si factor × spread/riesgo > tope del motor (2 % en sintéticos), como haría el motor en vivo.
     Aproximación conservadora: usa la mediana del spread real; en vivo el tope mira el spread del momento y deja
     pasar las entradas en momentos de spread bajo.
  ICT: storage/analysis/ict_limit_entry_signals.csv (entrada límite virtual, gestión del contrato).
  MSNR: storage/analysis/msnr_variants_signals_synth_free_{y0b,y1}.csv (entrada a mercado, gestión real; símbolo libre).

Uso:   .venv/Scripts/python.exe tools/research_real_spread_recheck.py
Salida: storage/analysis/real_spread_factors.csv y real_spread_recheck_report.md
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "storage" / "analysis"
CAP = 0.02
SPLIT = pd.Timestamp("2025-10-21", tz="UTC")


def tstat(x):
    x = np.asarray(x, float)
    return float(x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))) if len(x) > 2 and x.std(ddof=1) > 0 else 0.0


def measure_factors(symbols):
    import MetaTrader5 as mt5
    mt5.initialize()
    rows = []
    since = datetime.now(timezone.utc) - timedelta(days=2)
    for s in symbols:
        if not mt5.symbol_select(s, True):
            continue
        info = mt5.symbol_info(s)
        ticks = mt5.copy_ticks_from(s, since, 1_500_000, mt5.COPY_TICKS_ALL)
        m = mt5.copy_rates_from_pos(s, mt5.TIMEFRAME_M15, 0, 2000)
        if ticks is None or len(ticks) < 100 or m is None:
            continue
        t = pd.DataFrame(ticks)
        tick_sp = float((t.ask - t.bid).median())
        bar_sp = float(np.median(m["spread"][m["spread"] > 0])) * float(info.point) if (m["spread"] > 0).any() else float("nan")
        rows.append({"symbol": s, "tick_spread": tick_sp, "bar_spread": bar_sp,
                     "factor": tick_sp / bar_sp if bar_sp and bar_sp > 0 else float("nan"),
                     "tick_p10": float((t.ask - t.bid).quantile(0.1))})
        print(f"{s}: factor {rows[-1]['factor']:.2f}", flush=True)
    mt5.shutdown()
    return pd.DataFrame(rows)


def recheck(df, rcol, spcol, factors, label):
    """df con columnas symbol, time, rcol (R del replay) y spcol (spread/riesgo del replay)."""
    d = df[["symbol", "time", rcol, spcol]].dropna().copy()
    d = d.merge(factors[["symbol", "factor"]], on="symbol", how="left")
    d["factor"] = d["factor"].fillna(1.0).clip(lower=1.0)
    d["t"] = pd.to_datetime(d["time"], utc=True)
    d["r_rep"] = d[rcol]
    d["pass_rep"] = d[spcol] <= CAP
    d["r_real"] = d[rcol] - (d["factor"] - 1) * d[spcol]
    d["pass_real"] = d["factor"] * d[spcol] <= CAP
    rows = []
    for sym, g in d.groupby("symbol"):
        a, b = g[g.pass_rep], g[g.pass_real]
        rows.append({"modelo": label, "symbol": sym, "factor": g.factor.iat[0],
                     "ops_rep": len(a), "r_rep": a.r_rep.mean() if len(a) else np.nan,
                     "ops_real_tope": len(b), "r_real_tope": b.r_real.mean() if len(b) else np.nan,
                     "r_real_sin_tope": g.r_real.mean(),
                     "y0_real": b[b.t < SPLIT].r_real.mean() if len(b) else np.nan,
                     "y1_real": b[b.t >= SPLIT].r_real.mean() if len(b) else np.nan})
    tot = {"rep": d[d.pass_rep], "real": d[d.pass_real]}
    return pd.DataFrame(rows), tot


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    from config.ict_instrument_policy import MSNR_ACTIVE, ict_active_symbols
    from strategy.ict.ict_strategy import is_synthetic_asset
    ict = pd.read_csv(OUT / "ict_limit_entry_signals.csv")
    ict = ict[ict["synthetic"].astype(bool)].copy()
    active_ict = {s for s in ict_active_symbols("SYNTHETICS")} if callable(ict_active_symbols) else set()
    ict["spread_sl"] = ict["spread"] / ict["lim_risk"]
    ict = ict[ict["lim_rr"].notna()]
    msnr = pd.concat([pd.read_csv(OUT / f"msnr_variants_signals_synth_free_{t}.csv") for t in ("y0b", "y1")])
    msnr = msnr[msnr["symbol"].map(is_synthetic_asset)]
    symbols = sorted(set(ict.symbol) | set(msnr.symbol))
    factors = measure_factors(symbols)
    factors.to_csv(OUT / "real_spread_factors.csv", index=False)

    ict_tab, ict_tot = recheck(ict, "lim_rr", "spread_sl", factors, "ICT")
    ms_tab, ms_tot = recheck(msnr, "rr_live", "spread_sl", factors, "MSNR")
    ict_tab["activo_hoy"] = ict_tab.symbol.isin(active_ict) if active_ict else np.nan
    ms_tab["activo_hoy"] = ms_tab.symbol.isin(set(MSNR_ACTIVE))

    def fmt(v, p=4):
        return f"{v:+.{p}f}" if isinstance(v, (int, float)) and np.isfinite(v) else "—"

    L = ["# Re-medición de ICT y MSNR en sintéticos con el spread real de ticks (23-oct-2026)", "",
         "Factor = mediana spread de ticks (2 días) / mediana campo spread M15. R_real = R_replay − (factor−1)·spread/riesgo; "
         "tope del motor 2 % aplicado al spread real. Veredicto por activo: SIGUE si R/op real > 0 en ambos años con ≥ 30 ops.", ""]
    for label, tab, tot in (("ICT (entrada límite)", ict_tab, ict_tot), ("MSNR (entrada a mercado)", ms_tab, ms_tot)):
        rr, re = tot["rep"], tot["real"]
        L += [f"## {label}", "",
              f"- Replay original (spread M15, tope 2 %): {len(rr)} ops, R/op {rr.r_rep.mean():+.4f} (t {tstat(rr.r_rep):+.2f})",
              f"- Con spread real y tope 2 %: {len(re)} ops, R/op {re.r_real.mean():+.4f} (t {tstat(re.r_real):+.2f}); "
              f"año 0 {re[re.t < SPLIT].r_real.mean():+.4f}, año 1 {re[re.t >= SPLIT].r_real.mean():+.4f}", "",
              "| símbolo | activo hoy | factor | ops replay | R/op replay | ops reales | R/op real | año 0 | año 1 | sin tope R/op | veredicto |",
              "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
        for _, r in tab.sort_values("r_real_tope", ascending=False, na_position="last").iterrows():
            ok = (r.ops_real_tope >= 30 and np.isfinite(r.y0_real) and np.isfinite(r.y1_real) and r.y0_real > 0 and r.y1_real > 0)
            v = "SIGUE" if ok else ("SIN OPERACIONES" if r.ops_real_tope == 0 else "NO")
            L.append(f"| {r.symbol} | {'sí' if r.activo_hoy is True else ('no' if r.activo_hoy is False else '—')} | {r.factor:.1f} | "
                     f"{r.ops_rep} | {fmt(r.r_rep)} | {r.ops_real_tope} | {fmt(r.r_real_tope)} | {fmt(r.y0_real)} | {fmt(r.y1_real)} | "
                     f"{fmt(r.r_real_sin_tope)} | {v} |")
        L.append("")
    (OUT / "real_spread_recheck_report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    pd.concat([ict_tab, ms_tab]).to_csv(OUT / "real_spread_recheck_by_symbol.csv", index=False)
    print("informe: storage/analysis/real_spread_recheck_report.md")


if __name__ == "__main__":
    main()
