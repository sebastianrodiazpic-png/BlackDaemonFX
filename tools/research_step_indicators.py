"""Investigación (solo lectura): batería de 4 estrategias de indicadores en la familia Step — 21-oct-2026.

Reglas PRE-REGISTRADAS (fijadas antes de medir; sin optimización). Señal al cierre de la vela M15 i con velas cerradas
(H1 alineada por su hora de cierre); SELL es el espejo exacto.

  D · RSI(2) DE CONNORS (reversión dentro de tendencia)
      H1: cierre > EMA200 H1.   M15: RSI(2) < 10.
  E · SUPERTREND (seguimiento de tendencia)
      M15: Supertrend(10, 3) cambia a alcista en la vela i.   H1: cierre > EMA50 H1.
  F · MACD + EMA200 (cruce en zona de descuento)
      M15: la línea MACD(12, 26) cruza por encima de su señal (9) con MACD < 0 y cierre > EMA200 M15.
  G · RUPTURA KELTNER + ADX (impulso)
      M15: cierre cruza por encima del canal Keltner superior (EMA20 + 2 × ATR10).   H1: ADX14 H1 >= 25.

Ejecución y gestión idénticas a tools/research_synthetic_indicators.py (contrato del bot): entrada en la apertura
siguiente (BUY al ask), stop 1,5 × ATR14 H1, TP1 1R (50 %) + runner 2R (50 %) con BE tras TP1, máximo 200 velas,
spread = mediana causal de 96 velas, tope spread/SL 2 %, una operación por símbolo y estrategia.

Criterio de aprobación (por estrategia sobre los 12 Step; corrección por 4 pruebas):
  R/op > 0 en el año 0 y en el año 1; t >= 2,5; >= 3 de 4 semestres > 0; p azar < 0,0125.
Predicción previa (diagnóstico tools/research_step_diagnostics.py: paseo aleatorio): ninguna supera; R/op ≈ −coste.

Uso:   .venv/Scripts/python.exe tools/research_step_indicators.py --workers 3
Salida: storage/analysis/step_indicators_{trades,random}.csv y step_indicators_report.md
"""
from __future__ import annotations

import argparse
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import tools.research_synthetic_indicators as base  # noqa: E402

OUT = ROOT / "storage" / "analysis"
STRATEGIES = ("D_RSI2", "E_SUPERTREND", "F_MACD", "G_KELTNER")
STEP_FOLDERS = ("Step Indices", "Multi Step Indices", "Skewed Step")
WARMUP_DAYS = 30


def supertrend_dir(df: pd.DataFrame, n: int = 10, mult: float = 3.0) -> np.ndarray:
    """Dirección del Supertrend clásico (+1 alcista, -1 bajista) con ATR de Wilder."""
    a = base.atr(df, n).to_numpy()
    h, l, c = df["high"].to_numpy(), df["low"].to_numpy(), df["close"].to_numpy()
    hl2 = (h + l) / 2
    up, dn = hl2 - mult * a, hl2 + mult * a
    fup, fdn = up.copy(), dn.copy()
    d = np.ones(len(c), int)
    for i in range(1, len(c)):
        fup[i] = max(up[i], fup[i - 1]) if c[i - 1] > fup[i - 1] else up[i]
        fdn[i] = min(dn[i], fdn[i - 1]) if c[i - 1] < fdn[i - 1] else dn[i]
        d[i] = 1 if c[i] > fdn[i - 1] else -1 if c[i] < fup[i - 1] else d[i - 1]
    d[: n + 1] = 0
    return d


def step_features(m15: pd.DataFrame, h1: pd.DataFrame) -> pd.DataFrame:
    f = base.features(m15, h1).reset_index(drop=True)
    hh = h1.copy()
    hh["h_ema200b"] = base.ema(hh["close"], 200)
    hh["close_time"] = hh["time"] + pd.Timedelta(hours=1)
    f = pd.merge_asof(f, hh[["close_time", "h_ema200b"]], on="close_time", direction="backward")
    c = f["close"]
    f["rsi2"] = base.rsi(c, 2)
    f["st"] = supertrend_dir(f)
    macd = base.ema(c, 12) - base.ema(c, 26)
    f["macd"], f["macd_sig"] = macd, base.ema(macd, 9)
    f["ema200"] = base.ema(c, 200)
    mid = base.ema(c, 20)
    a10 = base.atr(f, 10)
    f["kc_up"], f["kc_lo"] = mid + 2 * a10, mid - 2 * a10
    return f


def step_signals(f: pd.DataFrame) -> dict[str, np.ndarray]:
    c, c1 = f["close"], f["close"].shift(1)
    st, st1 = f["st"], f["st"].shift(1)
    m, s, m1, s1 = f["macd"], f["macd_sig"], f["macd"].shift(1), f["macd_sig"].shift(1)
    d_buy = (f.h_close > f.h_ema200b) & (f.rsi2 < 10)
    d_sell = (f.h_close < f.h_ema200b) & (f.rsi2 > 90)
    e_buy = (st == 1) & (st1 == -1) & (f.h_close > f.h_ema50)
    e_sell = (st == -1) & (st1 == 1) & (f.h_close < f.h_ema50)
    f_buy = (m > s) & (m1 <= s1) & (m < 0) & (c > f.ema200)
    f_sell = (m < s) & (m1 >= s1) & (m > 0) & (c < f.ema200)
    g_buy = (c > f.kc_up) & ~(c1 > f.kc_up.shift(1)) & (f.h_adx >= 25)
    g_sell = (c < f.kc_lo) & ~(c1 < f.kc_lo.shift(1)) & (f.h_adx >= 25)

    def side(b, sl):
        return np.where(b.fillna(False), 1, np.where(sl.fillna(False), -1, 0))

    return {"D_RSI2": side(d_buy, d_sell), "E_SUPERTREND": side(e_buy, e_sell),
            "F_MACD": side(f_buy, f_sell), "G_KELTNER": side(g_buy, g_sell)}


def run_symbol(symbol: str, family: str, seed: int):
    import MetaTrader5 as mt5
    if not mt5.initialize():
        return symbol, [], [], "MT5_INIT"
    mt5.symbol_select(symbol, True)
    begin = base.START - timedelta(days=WARMUP_DAYS)
    frames = {}
    for name, tf in (("M15", mt5.TIMEFRAME_M15), ("H1", mt5.TIMEFRAME_H1)):
        rates = mt5.copy_rates_range(symbol, tf, begin, datetime.now(timezone.utc))
        if rates is None or len(rates) < 500:
            mt5.shutdown()
            return symbol, [], [], "SIN_DATOS"
        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
        frames[name] = df
    info = mt5.symbol_info(symbol)
    mt5.shutdown()
    if info is None:
        return symbol, [], [], "SIN_INFO"
    f = step_features(frames["M15"], frames["H1"])
    raw = f["spread"].where(f["spread"] > 0)
    spreads = (raw.shift(1).rolling(96, min_periods=1).median().bfill().fillna(float(info.spread))
               * float(info.point)).to_numpy(float)
    arrays = tuple(f[k].to_numpy(float) for k in ("open", "high", "low", "close", "h_atr"))
    valid = (f["close_time"] >= pd.Timestamp(base.START)).to_numpy()
    trades, randoms = [], []
    rng = np.random.default_rng(seed)
    for strat, sig in step_signals(f).items():
        busy_until, n = -1, 0
        for i in np.flatnonzero((sig != 0) & valid):
            if i <= busy_until:
                continue
            t = base.trade_at(i, int(sig[i]), f, arrays, spreads)
            if not isinstance(t, dict):
                continue
            busy_until = t["exit_idx"]
            trades.append({"symbol": symbol, "family": family, "strategy": strat, **t})
            n += 1
        pool = np.flatnonzero(valid[:-2])
        for i in (rng.choice(pool, size=min(len(pool), n), replace=False) if n else []):
            t = base.trade_at(int(i), int(rng.choice((-1, 1))), f, arrays, spreads)
            if isinstance(t, dict):
                randoms.append({"symbol": symbol, "family": family, "strategy": strat, "r": t["r"]})
    return symbol, trades, randoms, "OK"


def passes(s: dict) -> bool:
    sem_pos = sum(1 for v in s["sem"] if np.isfinite(v) and v > 0)
    return bool(s["y0"] > 0 and s["y1"] > 0 and s["t"] >= 2.5 and sem_pos >= 3 and s["p_azar"] < 0.0125)


def write_report(tr: pd.DataFrame, rn: pd.DataFrame, path: Path) -> dict:
    rng = np.random.default_rng(11)
    head, sep = base.HEAD.split("\n")
    L = ["# Batería de indicadores en la familia Step — replay 2 años (pre-registrado 21-oct-2026)", "",
         f"Periodo {base.START:%Y-%m-%d} → hoy (año 0 < {base.SPLIT:%Y-%m-%d} ≤ año 1). "
         "Criterio: R/op > 0 en ambos años, t ≥ 2,5, ≥ 3/4 semestres > 0, p azar < 0,0125.", "",
         "## Global por estrategia", "", "| estrategia | veredicto |" + head[1:], "|---|---" + sep[1:]]
    verdicts = {}
    for strat in STRATEGIES:
        d = tr[tr.strategy == strat]
        if d.empty:
            continue
        s = base.summary(d, rn[rn.strategy == strat], rng)
        verdicts[strat] = passes(s)
        L.append(f"| {strat} | {'SUPERA' if verdicts[strat] else 'NO SUPERA'} " + base.fmt(s))
    L += ["", "## Por estrategia y familia", "", "| estrategia | familia | cumple |" + head[1:], "|---|---|---" + sep[1:]]
    for strat in STRATEGIES:
        for fam, g in tr[tr.strategy == strat].groupby("family"):
            s = base.summary(g, rn[(rn.strategy == strat) & (rn.family == fam)], rng)
            L.append(f"| {strat} | {fam} | {'sí' if passes(s) else 'no'} " + base.fmt(s))
    L += ["", "## R/op por símbolo (año 0 / año 1)", "", "| símbolo | " + " | ".join(STRATEGIES) + " |",
          "|---|" + "---|" * len(STRATEGIES)]
    t_all = pd.to_datetime(tr["time"], utc=True)
    for sym in sorted(tr.symbol.unique()):
        cells = []
        for strat in STRATEGIES:
            g = tr[(tr.symbol == sym) & (tr.strategy == strat)]
            tg = t_all[g.index]
            a, b = g[tg < base.SPLIT].r, g[tg >= base.SPLIT].r
            cells.append(f"{g.r.mean():+.3f} ({a.mean():+.3f}/{b.mean():+.3f}, {len(g)})" if len(g) else "—")
        L.append(f"| {sym} | " + " | ".join(cells) + " |")
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return verdicts


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workers", type=int, default=3)
    args = ap.parse_args()
    import MetaTrader5 as mt5
    mt5.initialize()
    syms = sorted((x.name, x.path.rsplit("\\", 1)[0]) for x in mt5.symbols_get() if x.path.rsplit("\\", 1)[0] in STEP_FOLDERS)
    mt5.shutdown()
    trades, randoms = [], []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futs = [pool.submit(run_symbol, s, fam, k) for k, (s, fam) in enumerate(syms)]
        for done, fut in enumerate(as_completed(futs), 1):
            sym, tr, rn, st = fut.result()
            trades += tr
            randoms += rn
            print(f"[{done}/{len(syms)}] {sym}: {len(tr)} ops {st}", flush=True)
    tr, rn = pd.DataFrame(trades), pd.DataFrame(randoms)
    OUT.mkdir(parents=True, exist_ok=True)
    tr.to_csv(OUT / "step_indicators_trades.csv", index=False)
    rn.to_csv(OUT / "step_indicators_random.csv", index=False)
    print(write_report(tr, rn, OUT / "step_indicators_report.md"))


if __name__ == "__main__":
    main()
