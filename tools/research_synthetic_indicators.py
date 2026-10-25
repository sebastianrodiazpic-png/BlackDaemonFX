"""Investigación (solo lectura): tres estrategias de indicadores clásicos en TODOS los sintéticos — 21-oct-2026.

Reglas PRE-REGISTRADAS (fijadas antes de medir; no se optimiza ningún parámetro). Señal al cierre de la vela M15 i,
solo con velas cerradas (H1 alineada por su hora de cierre). Espejo exacto para SELL.

  A · TENDENCIA (EMA + ADX + retroceso RSI)
      H1: EMA50 > EMA200, cierre H1 > EMA50 y ADX14 H1 >= 20.
      M15: retroceso (RSI14 < 40 en alguna de las 5 velas previas) y RSI14 cruza hacia arriba 50 (RSI[i-1] < 50 <= RSI[i]).
  B · REVERSIÓN A LA MEDIA (Bollinger + RSI en rango)
      H1: ADX14 H1 < 20.
      M15: la vela i-1 cierra bajo la banda inferior Bollinger(20, 2) con RSI14 < 30 y la vela i vuelve a cerrar dentro.
  C · RUPTURA TRAS COMPRESIÓN (Bollinger squeeze + Donchian)
      M15: en alguna de las 5 últimas velas el ancho de Bollinger(20, 2) estuvo en el 20 % más bajo de las 120 previas,
      y la vela i cierra por encima del máximo Donchian de las 20 velas anteriores (la i-1 no lo hacía).
      H1: cierre H1 > EMA50 H1.

Ejecución y gestión (contrato del bot): entrada a mercado en la apertura de la vela siguiente (BUY al ask), stop de
1,5 × ATR14 H1 (cerrada) desde el fill, TP1 1R (50 %), runner 2R (50 %) con BE tras TP1, máximo 200 velas M15, SL gana
si coinciden en la vela, spread = mediana causal de las 96 velas M15 previas (el spread de los sintéticos escala con el
precio), tope spread/SL 2 % y una operación por símbolo y estrategia.

Ajustes de viabilidad hechos tras una prueba de 2 símbolos y ANTES de medir el universo (21-oct-2026): el stop pasó de
1,5 × ATR M15 a 1,5 × ATR H1 (con el de M15 el spread superaba el 2 % del riesgo casi siempre), el spread de mediana
global a mediana causal móvil, y el retroceso de A de "RSI cruza 40 y cierre > EMA20" (≈ 5 señales por trimestre) a
"RSI < 40 en 5 velas y cruce de 50". Las reglas B y C no cambiaron.

Criterio de aprobación (por estrategia, sobre todo el universo; corrección por 3 pruebas):
  R/op > 0 en el año 0 y en el año 1; t >= 2,4; al menos 3 de 4 semestres > 0; prueba de azar p < 0,0167
  (entradas en velas y direcciones aleatorias con la misma gestión, mismo símbolo y mismo número de operaciones).
  Los cortes por familia son exploratorios: una familia solo puede ir a prueba demo si además cumple el criterio dentro
  de sí misma.

Uso:   .venv/Scripts/python.exe tools/research_synthetic_indicators.py --workers 3
Salida: storage/analysis/synthetic_indicators_trades.csv, synthetic_indicators_random.csv y _report.md
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
from tools.replay_msnr_live_faithful import simulate  # noqa: E402

OUT = ROOT / "storage" / "analysis"
START = datetime(2024, 10, 21, tzinfo=timezone.utc)
SPLIT = pd.Timestamp("2025-10-21", tz="UTC")
WARMUP_DAYS = 20
SPREAD_CAP = 0.02
STOP_ATR = 1.5
STRATEGIES = ("A_TENDENCIA", "B_REVERSION", "C_RUPTURA")
SYNTHETIC_FOLDERS = ("Volatility Indices", "Crash Boom Indices", "Step Indices", "Range Break", "Jump Indices",
                     "DEX Indices", "Drift Switching Indices", "Multi Step Indices", "Hybrid Indices", "Skewed Step",
                     "Trek Indices", "Volatility Switch Indices", "Spot Volatility Indices", "Crash Boom Flip Indices",
                     "Laddered Volatility Indices", "Volatility Crash/Boom Indices")


# ----------------------------------------------------------------------------- indicadores
def ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()


def rsi(close: pd.Series, n: int = 14) -> pd.Series:
    d = close.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    pc = df["close"].shift()
    tr = pd.concat([df["high"] - df["low"], (df["high"] - pc).abs(), (df["low"] - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()


def adx(df: pd.DataFrame, n: int = 14) -> pd.Series:
    up = df["high"].diff()
    dn = -df["low"].diff()
    plus_dm = np.where((up > dn) & (up > 0), up, 0.0)
    minus_dm = np.where((dn > up) & (dn > 0), dn, 0.0)
    a = atr(df, n)
    plus_di = 100 * pd.Series(plus_dm, index=df.index).ewm(alpha=1 / n, adjust=False).mean() / a
    minus_di = 100 * pd.Series(minus_dm, index=df.index).ewm(alpha=1 / n, adjust=False).mean() / a
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    return dx.ewm(alpha=1 / n, adjust=False).mean()


def features(m15: pd.DataFrame, h1: pd.DataFrame) -> pd.DataFrame:
    """Indicadores M15 + H1 alineados por hora de cierre (solo velas cerradas)."""
    m = m15.copy()
    c = m["close"]
    m["ema20"] = ema(c, 20)
    m["rsi"] = rsi(c)
    m["atr"] = atr(m)
    mid = c.rolling(20).mean()
    sd = c.rolling(20).std(ddof=0)
    m["bb_up"], m["bb_lo"] = mid + 2 * sd, mid - 2 * sd
    bw = (m["bb_up"] - m["bb_lo"]) / mid.abs().replace(0, np.nan)
    q20 = bw.shift(1).rolling(120).quantile(0.2)
    m["sqz"] = (bw <= q20).astype(float).rolling(5).max().fillna(0).astype(bool)
    m["don_hi"] = m["high"].shift(1).rolling(20).max()
    m["don_lo"] = m["low"].shift(1).rolling(20).min()
    m["close_time"] = m["time"] + pd.Timedelta(minutes=15)

    h = h1.copy()
    h["h_ema50"] = ema(h["close"], 50)
    h["h_ema200"] = ema(h["close"], 200)
    h["h_adx"] = adx(h)
    h["h_atr"] = atr(h)
    h["h_close"] = h["close"]
    h["close_time"] = h["time"] + pd.Timedelta(hours=1)
    cols = ["close_time", "h_ema50", "h_ema200", "h_adx", "h_atr", "h_close"]
    return pd.merge_asof(m.sort_values("close_time"), h[cols].sort_values("close_time"), on="close_time",
                         direction="backward")


def signals(f: pd.DataFrame) -> dict[str, np.ndarray]:
    """Devuelve, por estrategia, un array con +1 (BUY), -1 (SELL) o 0 en cada vela M15 cerrada."""
    c, r = f["close"], f["rsi"]
    r1, c1 = r.shift(1), c.shift(1)
    up_trend = (f.h_ema50 > f.h_ema200) & (f.h_close > f.h_ema50) & (f.h_adx >= 20)
    dn_trend = (f.h_ema50 < f.h_ema200) & (f.h_close < f.h_ema50) & (f.h_adx >= 20)
    dipped = r.shift(1).rolling(5).min() < 40
    spiked = r.shift(1).rolling(5).max() > 60
    a_buy = up_trend & dipped & (r1 < 50) & (r >= 50)
    a_sell = dn_trend & spiked & (r1 > 50) & (r <= 50)

    ranging = f.h_adx < 20
    b_buy = ranging & (c1 < f.bb_lo.shift(1)) & (r1 < 30) & (c > f.bb_lo)
    b_sell = ranging & (c1 > f.bb_up.shift(1)) & (r1 > 70) & (c < f.bb_up)

    c_buy = f.sqz & (c > f.don_hi) & ~(c1 > f.don_hi.shift(1)) & (f.h_close > f.h_ema50)
    c_sell = f.sqz & (c < f.don_lo) & ~(c1 < f.don_lo.shift(1)) & (f.h_close < f.h_ema50)

    def side(b, s):
        return np.where(b.fillna(False), 1, np.where(s.fillna(False), -1, 0))

    return {"A_TENDENCIA": side(a_buy, a_sell), "B_REVERSION": side(b_buy, b_sell), "C_RUPTURA": side(c_buy, c_sell)}


# ----------------------------------------------------------------------------- simulación
def trade_at(i: int, sign: int, f: pd.DataFrame, arrays, spreads: np.ndarray):
    """Entrada en la apertura de i+1. Devuelve dict de la operación, "SPREAD" (tope) o None (sin datos)."""
    o, h, l, c, a = arrays
    spread = float(spreads[i])
    j = i + 1
    if j >= len(o) or not np.isfinite(a[i]) or a[i] <= 0:
        return None
    risk = STOP_ATR * a[i]
    if spread / risk > SPREAD_CAP:
        return "SPREAD"
    fill = o[j] + (spread if sign > 0 else 0.0)
    sl = fill - sign * risk
    tp1, tp2 = fill + sign * risk, fill + sign * 2 * risk
    direction = "BUY" if sign > 0 else "SELL"
    r, outcome, bars = simulate(direction, fill, sl, tp1, tp2, h[j:], l[j:], c[j:], opens=o[j:], spreads=spreads[j:])
    return {"time": f["close_time"].iloc[i], "direction": direction, "r": float(r), "outcome": outcome,
            "bars": int(bars), "exit_idx": j + max(int(bars) - 1, 0), "spread_sl": spread / risk}


def run_symbol(symbol: str, family: str, seed: int):
    import MetaTrader5 as mt5
    if not mt5.initialize():
        return symbol, [], [], "MT5_INIT"
    mt5.symbol_select(symbol, True)
    begin = START - timedelta(days=WARMUP_DAYS)
    end = datetime.now(timezone.utc)
    frames = {}
    for name, tf in (("M15", mt5.TIMEFRAME_M15), ("H1", mt5.TIMEFRAME_H1)):
        rates = mt5.copy_rates_range(symbol, tf, begin, end)
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
    f = features(frames["M15"], frames["H1"]).reset_index(drop=True)
    raw = f["spread"].where(f["spread"] > 0) if "spread" in f else pd.Series(np.nan, index=f.index)
    spreads = (raw.shift(1).rolling(96, min_periods=1).median().bfill()
               .fillna(float(info.spread)) * float(info.point)).to_numpy(float)
    arrays = tuple(f[k].to_numpy(float) for k in ("open", "high", "low", "close", "h_atr"))
    valid = (f["close_time"] >= pd.Timestamp(START)).to_numpy()
    first_time = f["time"].iloc[0]
    trades, randoms = [], []
    rng = np.random.default_rng(seed)
    for strat, sig in signals(f).items():
        busy_until, n, skipped = -1, 0, 0
        for i in np.flatnonzero((sig != 0) & valid):
            if i <= busy_until:
                continue
            t = trade_at(i, int(sig[i]), f, arrays, spreads)
            if t is None:
                continue
            if t == "SPREAD":
                skipped += 1
                continue
            busy_until = t["exit_idx"]
            trades.append({"symbol": symbol, "family": family, "strategy": strat, **t})
            n += 1
        # prueba de azar: mismas operaciones, velas y direcciones aleatorias, misma gestión
        pool = np.flatnonzero(valid[:-2])
        for i in rng.choice(pool, size=min(len(pool), max(n, 0)), replace=False) if n else []:
            t = trade_at(int(i), int(rng.choice((-1, 1))), f, arrays, spreads)
            if isinstance(t, dict):
                randoms.append({"symbol": symbol, "family": family, "strategy": strat, "r": t["r"]})
    ratio = np.nanmedian(spreads / (STOP_ATR * arrays[4]))
    return symbol, trades, randoms, f"OK desde {first_time:%Y-%m-%d} spread/riesgo mediano {ratio:.3f}"


# ----------------------------------------------------------------------------- informe
def tstat(x) -> float:
    x = np.asarray(x, float)
    return float(x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))) if len(x) > 2 and x.std(ddof=1) > 0 else 0.0


def chance_p(obs: pd.DataFrame, rnd: pd.DataFrame, rng, reps: int = 4000) -> float:
    """P(media aleatoria >= media observada) remuestreando, por símbolo, tantas operaciones aleatorias como reales."""
    if obs.empty or rnd.empty:
        return float("nan")
    groups = {s: g["r"].to_numpy() for s, g in rnd.groupby("symbol")}
    counts = obs.groupby("symbol").size()
    total = counts.sum()
    sims = np.zeros(reps)
    for s, k in counts.items():
        pool = groups.get(s)
        if pool is None or len(pool) == 0:
            continue
        sims += rng.choice(pool, size=(reps, k), replace=True).sum(axis=1)
    return float((sims / total >= obs["r"].mean()).mean())


def summary(df: pd.DataFrame, rnd: pd.DataFrame, rng) -> dict:
    t = pd.to_datetime(df["time"], utc=True)
    y0, y1 = df[t < SPLIT], df[t >= SPLIT]
    halves = [df[(t >= START_TS + pd.DateOffset(months=6 * k)) & (t < START_TS + pd.DateOffset(months=6 * (k + 1)))]
              for k in range(4)]
    eq = np.concatenate([[0.0], np.cumsum(df.sort_values("time")["r"].to_numpy() * 0.01)])  # 1 % por operación, suma simple
    peak = np.maximum.accumulate(eq)
    return {
        "ops": len(df), "r_op": df["r"].mean() if len(df) else np.nan, "t": tstat(df["r"]),
        "wr": (df["r"] > 0).mean() if len(df) else np.nan,
        "y0": y0["r"].mean() if len(y0) else np.nan, "y1": y1["r"].mean() if len(y1) else np.nan,
        "n0": len(y0), "n1": len(y1),
        "sem": [h["r"].mean() if len(h) else np.nan for h in halves],
        "p_azar": chance_p(df, rnd, rng), "r_total": df["r"].sum(),
        "dd_1pct_sum": float((eq - peak).min()),
    }


START_TS = pd.Timestamp(START)


def passes(s: dict) -> bool:
    sem_pos = sum(1 for v in s["sem"] if np.isfinite(v) and v > 0)
    return bool(s["y0"] > 0 and s["y1"] > 0 and s["t"] >= 2.4 and sem_pos >= 3 and s["p_azar"] < 0.0167)


def fmt(s: dict) -> str:
    sem = " / ".join(f"{v:+.3f}" if np.isfinite(v) else "—" for v in s["sem"])
    return (f"| {s['ops']} | {s['r_op']:+.4f} | {s['t']:+.2f} | {s['wr']:.1%} | {s['y0']:+.4f} ({s['n0']}) | "
            f"{s['y1']:+.4f} ({s['n1']}) | {sem} | {s['p_azar']:.3f} | {s['r_total']:+.1f} |")


HEAD = ("| ops | R/op | t | acierto | año 0 | año 1 | semestres | p azar | R total |\n"
        "|---:|---:|---:|---:|---:|---:|---|---:|---:|")


def write_report(tr: pd.DataFrame, rnd: pd.DataFrame, status: dict, path: Path):
    rng = np.random.default_rng(7)
    lines = ["# Estrategias de indicadores en sintéticos — replay 2 años (pre-registrado 21-oct-2026)", "",
             f"Periodo: {START:%Y-%m-%d} → hoy; año 0 < {SPLIT:%Y-%m-%d} ≤ año 1. Símbolos: {len(status)}. "
             "Criterio: R/op > 0 en ambos años, t ≥ 2,4, ≥ 3/4 semestres > 0, p azar < 0,0167.", ""]
    lines += ["## Resultado global por estrategia", "", "| estrategia | veredicto |" + HEAD.split("\n")[0][1:],
              "|---|---" + HEAD.split("\n")[1][1:]]
    verdicts = {}
    for strat in STRATEGIES:
        d = tr[tr.strategy == strat]
        if d.empty:
            continue
        s = summary(d, rnd[rnd.strategy == strat], rng)
        verdicts[strat] = passes(s)
        lines.append(f"| {strat} | {'SUPERA' if verdicts[strat] else 'NO SUPERA'} " + fmt(s))
    for strat in STRATEGIES:
        d = tr[tr.strategy == strat]
        if d.empty:
            continue
        lines += ["", f"## {strat} por familia (exploratorio)", "", "| familia | cumple |" + HEAD.split("\n")[0][1:],
                  "|---|---" + HEAD.split("\n")[1][1:]]
        for fam, g in d.groupby("family"):
            s = summary(g, rnd[(rnd.strategy == strat) & (rnd.family == fam)], rng)
            lines.append(f"| {fam} | {'sí' if passes(s) else 'no'} " + fmt(s))
        lines += ["", f"### {strat}: símbolos con R/op > 0 en ambos años y ≥ 30 operaciones", "",
                  "| símbolo | ops | R/op | t | año 0 | año 1 |", "|---|---:|---:|---:|---:|---:|"]
        for sym, g in d.groupby("symbol"):
            t = pd.to_datetime(g["time"], utc=True)
            a, b = g[t < SPLIT]["r"], g[t >= SPLIT]["r"]
            if len(g) >= 30 and len(a) and len(b) and a.mean() > 0 and b.mean() > 0:
                lines.append(f"| {sym} | {len(g)} | {g.r.mean():+.4f} | {tstat(g.r):+.2f} | {a.mean():+.4f} | {b.mean():+.4f} |")
    lines += ["", "## Estado de datos por símbolo", ""] + [f"- {k}: {v}" for k, v in sorted(status.items())]
    lines += ["", "Nota: la lista de símbolos positivos en ambos años es exploratoria (muchas comparaciones); "
              "por azar se esperan varios. No justifica activar símbolos sin una prueba demo con criterio fijado."]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return verdicts


def universe():
    import MetaTrader5 as mt5
    mt5.initialize()
    out = sorted((x.name, x.path.rsplit("\\", 1)[0]) for x in mt5.symbols_get()
                 if x.path.rsplit("\\", 1)[0] in SYNTHETIC_FOLDERS)
    mt5.shutdown()
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--symbols", default="", help="lista separada por comas (por defecto todos los sintéticos)")
    ap.add_argument("--tag", default="")
    args = ap.parse_args()
    syms = universe()
    if args.symbols:
        wanted = {s.strip() for s in args.symbols.split(",")}
        syms = [x for x in syms if x[0] in wanted]
    print(f"{len(syms)} sintéticos", flush=True)
    trades, randoms, status = [], [], {}
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futs = {pool.submit(run_symbol, s, fam, k): s for k, (s, fam) in enumerate(syms)}
        for done, fut in enumerate(as_completed(futs), 1):
            sym, tr, rn, st = fut.result()
            trades += tr
            randoms += rn
            status[sym] = st
            print(f"[{done}/{len(syms)}] {sym}: {len(tr)} ops · {st}", flush=True)
    tr, rn = pd.DataFrame(trades), pd.DataFrame(randoms)
    sfx = f"_{args.tag}" if args.tag else ""
    OUT.mkdir(parents=True, exist_ok=True)
    tr.to_csv(OUT / f"synthetic_indicators_trades{sfx}.csv", index=False)
    rn.to_csv(OUT / f"synthetic_indicators_random{sfx}.csv", index=False)
    verdicts = write_report(tr, rn, status, OUT / f"synthetic_indicators_report{sfx}.md")
    print(verdicts)


if __name__ == "__main__":
    main()
