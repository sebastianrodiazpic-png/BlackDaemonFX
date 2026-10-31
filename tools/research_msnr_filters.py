"""Búsqueda PRE-REGISTRADA de mejoras para Malaysian SNR sobre replays fieles por señal (solo lectura).

Conjuntos (tools/replay_msnr_variants.py, clase real, velas cerradas, tope spread/SL 2 %):
  A = msnr_variants_signals_synth_free_y0b.csv  (oct-2024 → oct-2025, ajustes por defecto)  → DESCUBRIR
  B = msnr_variants_signals_synth_free_y1.csv   (oct-2025 → oct-2026, ajustes por defecto)  → VALIDAR
  C = msnr_variants_signals_aud180_live.csv     (abr → oct-2026, ajustes REALES de la base)  → CONFIRMAR
Solo el universo activo de Malaysian SNR (config.ict_instrument_policy.MALAYSIAN_SNR_ACTIVE).

Protocolo (fijado antes de evaluar):
  * Cada hipótesis tiene una rejilla pequeña de umbrales. El umbral se ELIGE SOLO en A (mayor R/op con ≥ 40 % de las
    señales conservadas) y se aplica SIN TOCAR en B y C.
  * Se acepta si: (1) mejora la R/op frente a la base en A, B y C; (2) la R/op filtrada es > 0 en B y en C;
    (3) mejora en las dos mitades de B; (4) prueba de azar en B (quitar al azar la misma fracción de señales,
    5.000 veces): p < 0,05.
  * Gestión: R por operación con el contrato (TP1 1R + runner 2R con BE) = `rr_live`.
Hipótesis:
  H1 coste: spread/SL máximo ∈ {0,5 %, 1 %, 1,5 %}
  H2 stop: riesgo/ATR mínimo ∈ {0,3, 0,5, 0,7} y máximo ∈ {1,5, 2, 3}
  H3 confirmación: solo cierres de rechazo (excluir toques directos y/o barridos CRT)
  H4 escenario: excluir un escenario (Fractal, QMC, continuación…)
  H5 frescura: solo niveles FRESH
  H6 vela de ruptura: cuerpo mínimo ∈ {0,5, 0,6, 0,7}
  H7 régimen ADX: tramo bloqueado (a, b] con a ∈ {20, 25, 30} y b ∈ {35, 40, 50}
  H8 obstáculo: hueco mínimo hasta el obstáculo (en R) ∈ {1,5, 2, 3}
  H9 gestión: runner 1,5R / 3R / ambas a 1R / TP1 0,5R (mismas señales)
Uso: python tools/research_msnr_filters.py   → storage/analysis/msnr_filters_report.md
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "storage" / "analysis"
RNG = np.random.default_rng(20261025)


def load(tag):
    from config.ict_instrument_policy import MALAYSIAN_SNR_ACTIVE
    d = pd.read_csv(OUT / f"msnr_variants_signals_{tag}.csv")
    d = d[d.symbol.isin(MALAYSIAN_SNR_ACTIVE)].dropna(subset=["rr_live"]).copy()
    d["t"] = pd.to_datetime(d["time"], utc=True)
    d["half"] = np.where(d.t <= d.t.quantile(0.5), 1, 2)
    return d.reset_index(drop=True)


def m(r):
    r = pd.Series(r, dtype=float).dropna()
    return float(r.mean()) if len(r) else np.nan


def tstat(r):
    r = pd.Series(r, dtype=float).dropna()
    return float(r.mean() / (r.std(ddof=1) / np.sqrt(len(r)))) if len(r) > 2 else np.nan


def hypotheses():
    """(nombre, umbral, función máscara de señales CONSERVADAS)."""
    H = []
    for cap in (0.005, 0.01, 0.015):
        H.append(("H1 spread/SL ≤", cap, lambda d, c=cap: d.spread_sl <= c))
    for lo in (0.3, 0.5, 0.7):
        H.append(("H2 riesgo/ATR ≥", lo, lambda d, x=lo: d.risk_atr >= x))
    for hi in (1.5, 2.0, 3.0):
        H.append(("H2 riesgo/ATR ≤", hi, lambda d, x=hi: d.risk_atr <= x))
    H.append(("H3 sin toque directo", "-", lambda d: d.entry_confirmation != "DIRECT_TOUCH_RETEST"))
    H.append(("H3 sin barrido CRT", "-", lambda d: d.entry_confirmation != "CRT_M15_SWEEP_AND_ABSORPTION_CLOSE"))
    H.append(("H3 solo rechazo de zona", "-", lambda d: d.entry_confirmation == "M15_ZONE_REJECTION_CLOSE"))
    for sc in ("ESC_3_FRACTAL", "ESC_3_QMC", "ESC_1_CONTINUATION", "ESC_1_BREAKER_PAIR"):
        H.append(("H4 sin escenario", sc, lambda d, s=sc: d.scenario != s))
    H.append(("H5 solo FRESH", "-", lambda d: d.freshness.fillna("STRUCTURAL_REFERENCE") != "TESTED_ONCE"))
    for b in (0.5, 0.6, 0.7):
        H.append(("H6 cuerpo ruptura ≥", b, lambda d, x=b: d.body_ratio >= x))
    for a in (20, 25, 30):
        for b in (35, 40, 50):
            H.append(("H7 ADX bloqueado (a,b]", f"{a}-{b}", lambda d, x=a, y=b: ~((d.adx > x) & (d.adx <= y))))
    for room in (1.5, 2.0, 3.0):
        H.append(("H8 hueco obstáculo ≥ R", room, lambda d, x=room: d.obstacle_room_rr.isna() | (d.obstacle_room_rr >= x)))
    return H


def random_removal_p(d, keep_mask, n=5000):
    r = d.rr_live.to_numpy()
    k = int(keep_mask.sum())
    observed = r[keep_mask.to_numpy()].mean() - r.mean()
    if k == 0 or k == len(r):
        return np.nan
    hits = 0
    for _ in range(n):
        idx = RNG.choice(len(r), size=k, replace=False)
        hits += (r[idx].mean() - r.mean()) >= observed
    return hits / n


def main():
    A, B, C = load("synth_free_y0b"), load("synth_free_y1"), load("aud180_live")
    L = ["# Malaysian SNR — búsqueda pre-registrada de mejoras\n",
         f"Universo activo. A (descubrir) n={len(A)} R/op {m(A.rr_live):+.3f} · B (validar) n={len(B)} "
         f"R/op {m(B.rr_live):+.3f} (mitades {m(B[B.half == 1].rr_live):+.3f} / {m(B[B.half == 2].rr_live):+.3f}) · "
         f"C (ajustes reales, 180 d) n={len(C)} R/op {m(C.rr_live):+.3f}\n",
         "| Hipótesis | Umbral (elegido en A) | A conserva · R/op | B conserva · R/op | B mitades | C conserva · R/op | p azar B | Veredicto |",
         "|---|---|---|---|---|---|---|---|"]
    by_name = {}
    for name, thr, fn in hypotheses():
        by_name.setdefault(name, []).append((thr, fn))
    for name, options in by_name.items():
        # Elegir en A: mayor R/op con ≥ 40 % de señales conservadas.
        scored = []
        for thr, fn in options:
            keep = fn(A).fillna(False)
            if keep.mean() >= 0.40 and keep.sum() >= 40:
                scored.append((m(A[keep].rr_live), thr, fn))
        if not scored:
            L.append(f"| {name} | — | sin opción con ≥ 40 % | | | | | descartada |")
            continue
        _, thr, fn = max(scored, key=lambda x: x[0])
        kA, kB, kC = fn(A).fillna(False), fn(B).fillna(False), fn(C).fillna(False)
        b1, b2 = B[kB & (B.half == 1)].rr_live, B[kB & (B.half == 2)].rr_live
        base1, base2 = B[B.half == 1].rr_live, B[B.half == 2].rr_live
        p = random_removal_p(B, kB)
        ok = (m(A[kA].rr_live) > m(A.rr_live) and m(B[kB].rr_live) > m(B.rr_live) and m(C[kC].rr_live) > m(C.rr_live)
              and m(B[kB].rr_live) > 0 and m(C[kC].rr_live) > 0 and m(b1) > m(base1) and m(b2) > m(base2) and p < 0.05)
        L.append(f"| {name} | {thr} | {kA.mean() * 100:.0f} % · {m(A[kA].rr_live):+.3f} | {kB.mean() * 100:.0f} % · "
                 f"{m(B[kB].rr_live):+.3f} | {m(b1):+.3f} / {m(b2):+.3f} | {kC.mean() * 100:.0f} % · {m(C[kC].rr_live):+.3f} | "
                 f"{p:.3f} | {'**SUPERA**' if ok else 'no'} |")
    L += ["\n## H9 gestión (mismas señales; R/op)\n", "| Gestión | A | B | B mitades | C |", "|---|---|---|---|---|"]
    for col, label in (("rr_live", "TP1 1R + runner 2R (contrato)"), ("rr_r15", "runner 1,5R"), ("rr_r3", "runner 3R"),
                       ("rr_1r", "ambas a 1R"), ("rr_h05", "TP1 0,5R + runner 2R")):
        L.append(f"| {label} | {m(A[col]):+.3f} | {m(B[col]):+.3f} | {m(B[B.half == 1][col]):+.3f} / "
                 f"{m(B[B.half == 2][col]):+.3f} | {m(C[col]):+.3f} |")
    L += ["\n## Diagnóstico (solo informativo, no se elige nada aquí)\n"]
    for col in ("scenario", "entry_confirmation", "direction"):
        rows = []
        for key in sorted(set(A[col].dropna()) | set(B[col].dropna()) | set(C[col].dropna())):
            rows.append(f"| {key} | {(A[col] == key).sum()} · {m(A[A[col] == key].rr_live):+.3f} | "
                        f"{(B[col] == key).sum()} · {m(B[B[col] == key].rr_live):+.3f} | {(C[col] == key).sum()} · "
                        f"{m(C[C[col] == key].rr_live):+.3f} |")
        L += [f"\n**{col}** (n · R/op)\n", "| valor | A | B | C |", "|---|---|---|---|", *rows]
    (OUT / "msnr_filters_report.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
