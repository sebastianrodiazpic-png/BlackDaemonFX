"""Investigación (solo lectura): ¿se apartan los índices Step del paseo aleatorio? — 21-oct-2026.

Antes de diseñar reglas con indicadores para la familia Step se mide si existe alguna desviación explotable:
  * Deriva: media del rendimiento por vela M15 en 2 años (t de la media) y por año.
  * Autocorrelación de rendimientos (retardos 1-5) en M1 (≈ 70 días) y M15 (2 años).
  * Ratio de varianzas de Lo-MacKinlay VR(q), q = 2, 4, 8, 16, 32 sobre M15 (z robusto a heterocedasticidad).
    VR > 1 = persistencia (favorece tendencia/ruptura); VR < 1 = reversión (favorece reversión a la media).
  * Rachas en M1: P(sube | k velas seguidas al alza), k = 1..4, frente a P(sube) incondicional.
  * Estacionalidad horaria: media del rendimiento por hora UTC (t de la hora más extrema).
  * Coste: spread típico frente a la volatilidad (ATR14 H1 × 1,5) = peaje mínimo por operación en R.
Un movimiento explotable debe ser estable en ambos años y superar el coste; con 12 símbolos y muchas pruebas, solo
cuentan |z| > 3 consistentes.

Uso:   .venv/Scripts/python.exe tools/research_step_diagnostics.py
Salida: storage/analysis/step_diagnostics_report.md
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "storage" / "analysis"
START = datetime(2024, 10, 21, tzinfo=timezone.utc)
SPLIT = pd.Timestamp("2025-10-21", tz="UTC")
STEP_FOLDERS = ("Step Indices", "Multi Step Indices", "Skewed Step")


def tmean(x) -> float:
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    return float(x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))) if len(x) > 2 and x.std(ddof=1) > 0 else 0.0


def autocorr(r: np.ndarray, lag: int) -> tuple[float, float]:
    r = r - r.mean()
    rho = float(np.dot(r[lag:], r[:-lag]) / np.dot(r, r))
    return rho, rho * np.sqrt(len(r))


def variance_ratio(r: np.ndarray, q: int) -> tuple[float, float]:
    """Lo-MacKinlay con z robusto a heterocedasticidad (rendimientos solapados)."""
    n = len(r)
    mu = r.mean()
    d = r - mu
    var1 = np.dot(d, d) / (n - 1)
    rq = np.convolve(r, np.ones(q), "valid") - q * mu
    m = q * (n - q + 1) * (1 - q / n)
    varq = np.dot(rq, rq) / m
    vr = varq / var1
    d2 = d ** 2
    theta = 0.0
    for j in range(1, q):
        delta = np.dot(d2[j:], d2[:-j]) / (np.dot(d, d) ** 2)
        theta += (2 * (q - j) / q) ** 2 * delta
    return float(vr), float((vr - 1) / np.sqrt(theta))


def runs(r: np.ndarray, kmax: int = 4) -> list[tuple[int, float, float, int]]:
    up = (r > 0).astype(int)
    nz = r != 0
    base = up[nz].mean()
    out = []
    for k in range(1, kmax + 1):
        streak = np.ones(len(r) - k, bool)
        for j in range(1, k + 1):
            streak &= up[k - j:len(r) - j] == 1
        nxt = up[k:][streak & nz[k:]]
        if len(nxt) > 30:
            p = nxt.mean()
            z = (p - base) / np.sqrt(base * (1 - base) / len(nxt))
            out.append((k, float(p), float(z), int(len(nxt))))
    return out


def load(mt5, sym, tf, start=None, count=None):
    rates = (mt5.copy_rates_range(sym, tf, start, datetime.now(timezone.utc)) if start
             else mt5.copy_rates_from_pos(sym, tf, 0, count))
    if rates is None or len(rates) < 500:
        return None
    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
    return df


def analyze(mt5, sym):
    info = mt5.symbol_info(sym)
    m15 = load(mt5, sym, mt5.TIMEFRAME_M15, start=START)
    m1 = load(mt5, sym, mt5.TIMEFRAME_M1, count=99_000)
    h1 = load(mt5, sym, mt5.TIMEFRAME_H1, start=START)
    if m15 is None or m1 is None or h1 is None or info is None:
        return None
    r15 = m15["close"].diff().dropna().to_numpy()
    r1 = m1["close"].diff().dropna().to_numpy()
    t15 = m15["time"].iloc[1:].reset_index(drop=True)
    y0, y1 = r15[(t15 < SPLIT).to_numpy()], r15[(t15 >= SPLIT).to_numpy()]
    pc = h1["close"].shift()
    tr = pd.concat([h1.high - h1.low, (h1.high - pc).abs(), (h1.low - pc).abs()], axis=1).max(axis=1)
    risk = 1.5 * float(tr.ewm(alpha=1 / 14, adjust=False).mean().median())
    spr = m15["spread"][m15["spread"] > 0]
    spread = float(spr.median() if len(spr) else info.spread) * float(info.point)
    hours = pd.Series(r15).groupby(t15.dt.hour.to_numpy())
    hour_t = hours.apply(tmean)
    steps = np.unique(np.round(np.abs(np.diff(m1["close"].to_numpy()[-2000:])), 6))
    return {
        "symbol": sym, "m15_bars": len(m15), "m1_desde": f"{m1['time'].iloc[0]:%Y-%m-%d}",
        "deriva_t": tmean(r15), "deriva_t_y0": tmean(y0), "deriva_t_y1": tmean(y1),
        "deriva_R_dia": float(r15.mean() * 96 / risk),
        "ac_m1": [autocorr(r1, k) for k in range(1, 6)], "ac_m15": [autocorr(r15, k) for k in range(1, 6)],
        "ac_m15_y0": autocorr(y0, 1), "ac_m15_y1": autocorr(y1, 1),
        "vr": [(q, *variance_ratio(r15, q)) for q in (2, 4, 8, 16, 32)],
        "vr_y0": variance_ratio(y0, 8), "vr_y1": variance_ratio(y1, 8),
        "runs": runs(r1), "hora_t_max": float(hour_t.abs().max()), "hora_peor": int(hour_t.abs().idxmax()),
        "coste_R": spread / risk, "pasos_m1_ejemplo": len(steps),
    }


def main():
    import MetaTrader5 as mt5
    if not mt5.initialize():
        sys.exit("MT5 no disponible")
    syms = sorted(x.name for x in mt5.symbols_get() if x.path.rsplit("\\", 1)[0] in STEP_FOLDERS)
    rows = []
    for s in syms:
        mt5.symbol_select(s, True)
        res = analyze(mt5, s)
        print(s, "ok" if res else "SIN DATOS", flush=True)
        if res:
            rows.append(res)
    mt5.shutdown()

    L = ["# Diagnóstico de aleatoriedad de los índices Step (21-oct-2026)", "",
         f"M15 desde {START:%Y-%m-%d} (2 años; año 0 < {SPLIT:%Y-%m-%d} ≤ año 1), M1 últimas ~99.000 velas.", "",
         "## Deriva y coste", "", "| símbolo | velas M15 | t deriva | t año 0 | t año 1 | deriva R/día | coste spread R/op |",
         "|---|---:|---:|---:|---:|---:|---:|"]
    for r in rows:
        L.append(f"| {r['symbol']} | {r['m15_bars']} | {r['deriva_t']:+.2f} | {r['deriva_t_y0']:+.2f} | {r['deriva_t_y1']:+.2f} | "
                 f"{r['deriva_R_dia']:+.4f} | {r['coste_R']:.4f} |")
    L += ["", "## Autocorrelación (ρ y z)", "", "| símbolo | M1 lag1 | M1 lag2 | M1 lag3 | M15 lag1 | M15 lag2 | M15 lag1 año0 | M15 lag1 año1 |",
          "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        f = lambda a: f"{a[0]:+.4f} ({a[1]:+.1f})"
        L.append(f"| {r['symbol']} | {f(r['ac_m1'][0])} | {f(r['ac_m1'][1])} | {f(r['ac_m1'][2])} | {f(r['ac_m15'][0])} | "
                 f"{f(r['ac_m15'][1])} | {f(r['ac_m15_y0'])} | {f(r['ac_m15_y1'])} |")
    L += ["", "## Ratio de varianzas M15 (VR y z)", "", "| símbolo | q=2 | q=4 | q=8 | q=16 | q=32 | q=8 año0 | q=8 año1 |",
          "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        g = lambda v: f"{v[-2]:.3f} ({v[-1]:+.1f})"
        L.append(f"| {r['symbol']} | " + " | ".join(g(v) for v in r["vr"]) + f" | {g(r['vr_y0'])} | {g(r['vr_y1'])} |")
    L += ["", "## Rachas M1: P(sube | k subidas seguidas) (z, n)", "", "| símbolo | k=1 | k=2 | k=3 | k=4 | hora UTC más extrema (t) |",
          "|---|---|---|---|---|---|"]
    for r in rows:
        cells = [f"{p:.3f} ({z:+.1f}, {n})" for _, p, z, n in r["runs"]]
        L.append(f"| {r['symbol']} | " + " | ".join(cells + ["—"] * (4 - len(cells))) + f" | {r['hora_peor']} h ({r['hora_t_max']:.1f}) |")
    L += ["", "Lectura: con 12 símbolos × decenas de pruebas, |z| > 3 aparece por azar a veces; solo cuenta una desviación "
          "con el mismo signo en ambos años y con tamaño suficiente para cubrir el coste."]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "step_diagnostics_report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
