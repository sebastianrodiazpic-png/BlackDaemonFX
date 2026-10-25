"""Investigación (solo lectura): materias primas con 15 años de datos externos — reglas del PRE-REGISTRO del 22-oct-2026
(ver REGISTRO_CAMBIOS_ESTRATEGIA.md, entrada "PRE-REGISTRO: materias primas con datos externos").

Datos: storage/external_data/ (Dukascopy D1 bid/ask y H1 bid, COT de la CFTC, FRED DFII10).
  P1 · Momentum 12 meses (mensual).  P2 · COT contrario (semanal).  P3 · Oro/plata con tipos reales (diario).
Gestión principal: contrato de dos entradas (TP1 1R + runner 2R con BE) en camino H1; la regla cierra lo que quede.
Referencia informativa: una posición con stop y salida por regla.
Costes: spread = máx(mediana ask − bid de Dukascopy, mediana M15 del broker); swap actual del broker por noche.

Uso:   .venv/Scripts/python.exe tools/research_commodity_longrun.py
Salida: storage/analysis/commodity_longrun_{trades,random}.csv y commodity_longrun_report.md
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import tools.research_forex_indicators as fx  # noqa: E402
import tools.research_synthetic_indicators as base  # noqa: E402

EXT = ROOT / "storage" / "external_data"
OUT = ROOT / "storage" / "analysis"
# WTI y cacao omitidos por decisión del usuario (22-oct-2026), antes de ver resultados.
BROKER = {"XAUUSD": "XAUUSD", "XAGUSD": "XAGUSD", "BRENT": "UK Brent Oil"}
COT_NAME = {"XAUUSD": "GOLD", "XAGUSD": "SILVER", "BRENT": "BRENT", "WTI": "WTI", "COCOA": "COCOA"}
# 5 años (decisión del usuario, 22-oct-2026, antes de ver resultados): operaciones desde 2021; el diario anterior solo
# sirve para calentar indicadores (SMA, ATR, momentum de 12 meses, z-score del COT).
EVAL_START = pd.Timestamp("2021-01-01", tz="UTC")
PERIODS = (("2021-2022", "2021-01-01", "2023-01-01"), ("2023-2024", "2023-01-01", "2025-01-01"), ("2025-hoy", "2025-01-01", "2100-01-01"))
STRATEGIES = ("P1_MOM12", "P2_COT", "P3_REALRATE")
fx.SPREAD_CAP = 1.0  # en swing diario el spread es pequeño frente al stop; no se aplica el tope intradía


def extend_daily_with_hourly(d1: pd.DataFrame, h1: pd.DataFrame) -> pd.DataFrame:
    """Dukascopy solo publica velas D1 de años cerrados: los días posteriores se agregan desde las H1 (día UTC)."""
    last = d1["time"].max()
    extra = h1[h1["time"] >= last + pd.Timedelta(days=1)]
    if extra.empty:
        return d1
    g = extra.groupby(extra["time"].dt.floor("D"))
    days = pd.DataFrame({"time": g["time"].min().dt.floor("D"), "open": g["open"].first(), "high": g["high"].max(),
                         "low": g["low"].min(), "close": g["close"].last(), "volume": g["volume"].sum()}).reset_index(drop=True)
    return pd.concat([d1, days[days["volume"] > 0]], ignore_index=True)


# ----------------------------------------------------------------------------- datos
def load_instrument(name, mt5):
    d1 = pd.read_csv(EXT / "dukascopy" / f"{name}_daily_bid.csv", parse_dates=["time"])
    ask = pd.read_csv(EXT / "dukascopy" / f"{name}_daily_ask.csv", parse_dates=["time"])
    h1 = pd.read_csv(EXT / "dukascopy" / f"{name}_hourly_bid.csv", parse_dates=["time"])
    d1 = extend_daily_with_hourly(d1[d1["volume"] > 0].reset_index(drop=True), h1[h1["volume"] > 0])
    sp = pd.merge(d1[["time", "close"]], ask[["time", "close"]], on="time", suffixes=("_b", "_a"))
    duka_spread = float((sp.close_a - sp.close_b).clip(lower=0).tail(500).median())
    sym = BROKER[name]
    mt5.symbol_select(sym, True)
    info = mt5.symbol_info(sym)
    m = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M15, 0, 20_000)
    broker_spread = float(np.median(m["spread"][m["spread"] > 0])) * float(info.point) if m is not None and (m["spread"] > 0).any() else 0.0
    bd = pd.DataFrame(mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_D1, 0, 3000))
    bd["time"] = pd.to_datetime(bd["time"], unit="s", utc=True)
    # fidelidad: correlación de rendimientos diarios en el tramo común
    j = pd.merge(d1[["time", "close"]].assign(day=d1.time.dt.date), bd[["time", "close"]].assign(day=bd.time.dt.date),
                 on="day", suffixes=("_d", "_b"))
    corr = float(j.close_d.pct_change().corr(j.close_b.pct_change())) if len(j) > 60 else float("nan")
    level = float((j.close_d / j.close_b).median()) if len(j) else float("nan")
    d1["atr20"] = base.atr(d1, 20)
    d1["sma50"] = d1["close"].rolling(50).mean()
    return {"d1": d1, "h1": h1.reset_index(drop=True), "info": info, "spread": max(duka_spread, broker_spread),
            "corr": corr, "level": level, "overlap": len(j), "from": d1.time.iat[0]}


def h1_index(h1, t):
    return int(np.searchsorted(h1["time"].values, pd.Timestamp(t).tz_convert(None).to_datetime64()))


def run_trade(inst, sign, entry_day, exit_day, risk):
    """Contrato de dos entradas en camino H1 desde la apertura de `entry_day` hasta la de `exit_day`."""
    h1 = inst["h1"]
    if pd.Timestamp(entry_day) < max(EVAL_START, h1.time.iat[0]):
        return None
    j, end = h1_index(h1, entry_day), h1_index(h1, exit_day)
    if j >= len(h1) - 1 or end <= j:
        return None
    spreads = np.full(len(h1), inst["spread"])
    t = fx.trade(sign, j, end, risk, h1, spreads, inst["info"])
    if not isinstance(t, dict):
        return None
    # referencia: una posición, stop + regla
    o, hi, lo = h1.open.to_numpy(float), h1.high.to_numpy(float), h1.low.to_numpy(float)
    fill = o[j] + (inst["spread"] if sign > 0 else 0.0)
    sl = fill - sign * risk
    shift = inst["spread"] if sign < 0 else 0.0
    px, k = None, end
    for i in range(j, min(end, len(h1) - 1)):
        if (sign > 0 and lo[i] <= sl) or (sign < 0 and hi[i] + shift >= sl):
            px, k = sl, i
            break
    if px is None:
        k = min(end, len(h1) - 1)
        px = o[k] + shift
    nights = max(0, (h1.time.iat[k].normalize() - h1.time.iat[j].normalize()).days)
    rate = float(inst["info"].swap_long if sign > 0 else inst["info"].swap_short)
    t["r_single"] = sign * (px - fill) / risk + nights * rate * float(inst["info"].point) / risk
    return t


# ----------------------------------------------------------------------------- estrategias
def p1_signals(inst):
    d = inst["d1"]
    month_end = d.groupby(d.time.dt.to_period("M")).tail(1).reset_index(drop=True)
    month_end["ret12"] = month_end["close"] / month_end["close"].shift(12) - 1
    out = []
    for i in range(12, len(month_end) - 1):
        sign = 1 if month_end.ret12.iat[i] > 0 else -1
        entry = d[d.time > month_end.time.iat[i]].time
        if entry.empty:
            break
        k = next((k for k in range(i + 1, len(month_end)) if np.sign(month_end.ret12.iat[k]) != sign), len(month_end) - 1)
        ex = d[d.time > month_end.time.iat[k]].time
        out.append((month_end.time.iat[i], sign, entry.iat[0], ex.iat[0] if len(ex) else d.time.iat[-1],
                    3 * float(d.loc[d.time == month_end.time.iat[i], "atr20"].iat[0])))
    return out


def p2_signals(inst, name, cot):
    d = inst["d1"]
    c = cot[cot.market == COT_NAME[name]].sort_values("date").reset_index(drop=True)
    if c.empty:
        return []
    net = (c.m_money_positions_long_all - c.m_money_positions_short_all) / c.open_interest_all
    c["z"] = (net - net.rolling(156).mean()) / net.rolling(156).std(ddof=0)
    out = []
    for i in np.flatnonzero((c.z.abs() > 2).to_numpy()):
        sign = -1 if c.z.iat[i] > 2 else 1
        tradable = c.date.iat[i] + pd.Timedelta(days=6)
        entry = d[d.time >= tradable]
        if entry.empty:
            continue
        e_idx = entry.index[0]
        k = next((k for k in range(i + 1, len(c)) if abs(c.z.iat[k]) < 0.5), None)
        ex_by_rule = d[d.time >= c.date.iat[k] + pd.Timedelta(days=6)].index[0] if k is not None and (d.time >= c.date.iat[k] + pd.Timedelta(days=6)).any() else len(d) - 1
        x_idx = min(ex_by_rule, e_idx + 30, len(d) - 1)
        out.append((c.date.iat[i], sign, d.time.iat[e_idx], d.time.iat[x_idx], 2 * float(d.atr20.iat[max(e_idx - 1, 0)])))
    return out


def p3_signals(inst, rr):
    d = inst["d1"].copy()
    d["day"] = d.time.dt.tz_convert(None).dt.normalize()
    r = rr.copy()
    r["d20"] = r["v"] - r["v"].shift(20)
    r["day"] = r["date"] + pd.Timedelta(days=1)  # dato del día t disponible al día siguiente
    d = pd.merge_asof(d.sort_values("day"), r[["day", "d20"]].sort_values("day"), on="day", direction="backward")
    cond = np.where((d.d20 < 0) & (d.close > d.sma50), 1, np.where((d.d20 > 0) & (d.close < d.sma50), -1, 0))
    out = []
    for i in np.flatnonzero(cond != 0):
        if i + 1 >= len(d):
            break
        sign = int(cond[i])
        k = next((k for k in range(i + 1, min(i + 31, len(d))) if np.sign(d.d20.iat[k]) == -sign), min(i + 30, len(d) - 1))
        out.append((d.time.iat[i], sign, d.time.iat[i + 1], d.time.iat[min(k + 1, len(d) - 1)], 2 * float(d.atr20.iat[i])))
    return out


def execute(name, inst, strat, sigs, rng, randoms):
    trades, busy = [], None
    for sig_t, sign, entry, exit_, risk in sigs:
        if busy is not None and entry <= busy:
            continue
        t = run_trade(inst, sign, entry, exit_, risk)
        if t:
            busy = inst["h1"].time.iat[t["exit_idx"]]
            trades.append({"symbol": name, "strategy": strat, "time": entry, **t})
    # azar: mismas duraciones y riesgo que las señales reales, fechas y sentidos aleatorios
    d = inst["d1"]
    for _ in range(len(trades)):
        sig_t, sign, entry, exit_, risk = sigs[int(rng.integers(len(sigs)))]
        span = max(1, int((exit_ - entry).days))
        first = max(250, int(np.searchsorted(d.time.values, EVAL_START.tz_convert(None).to_datetime64())))
        start = d.time.iat[int(rng.integers(first, len(d) - span - 2))]
        stop_day = start + pd.Timedelta(days=span)
        t = run_trade(inst, int(rng.choice((-1, 1))), start, stop_day, risk)
        if t:
            randoms.append({"symbol": name, "strategy": strat, "time": start, "r": t["r"]})
    return trades


def summarize(g, rn, rng):
    t = pd.to_datetime(g.time, utc=True)
    per = [g[(t >= pd.Timestamp(a, tz="UTC")) & (t < pd.Timestamp(b, tz="UTC"))].r for _, a, b in PERIODS]
    return {"ops": len(g), "r": g.r.mean(), "r1": g.r_single.mean(), "t": base.tstat(g.r),
            "tday": base.tstat(g.groupby(t.dt.date).r.mean()), "wr": (g.r > 0).mean(), "tp1": g.tp1.mean(),
            "per": [(x.mean() if len(x) else np.nan, len(x)) for x in per], "p": base.chance_p(g, rn, rng),
            "rnd": rn.r.mean() if len(rn) else np.nan}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    import MetaTrader5 as mt5
    mt5.initialize()
    cot = pd.read_csv(EXT / "cot_disaggregated.csv")
    cot["date"] = pd.to_datetime(cot["report_date_as_yyyy_mm_dd"], utc=True)
    rr = pd.read_csv(EXT / "fred_DFII10.csv")
    rr.columns = ["date", "v"]
    rr["date"] = pd.to_datetime(rr["date"])
    rr["v"] = pd.to_numeric(rr["v"], errors="coerce")
    rr = rr.dropna()
    rng = np.random.default_rng(29)
    insts, trades, randoms, fidelity = {}, [], [], []
    for name in BROKER:
        try:
            inst = load_instrument(name, mt5)
        except FileNotFoundError:
            fidelity.append(f"- {name}: sin datos descargados")
            continue
        ok = np.isfinite(inst["corr"]) and inst["corr"] >= 0.95
        fidelity.append(f"- {name}: Dukascopy desde {inst['from']:%Y-%m-%d}; correlación de rendimientos con el broker "
                        f"{inst['corr']:.3f} en {inst['overlap']} días; nivel Dukascopy/broker {inst['level']:.3f}; "
                        f"spread usado {inst['spread']:.4f} -> {'INCLUIDO' if ok else 'EXCLUIDO'}")
        if not ok:
            continue
        insts[name] = inst
        trades += execute(name, inst, "P1_MOM12", p1_signals(inst), rng, randoms)
        trades += execute(name, inst, "P2_COT", p2_signals(inst, name, cot), rng, randoms)
        if name in ("XAUUSD", "XAGUSD"):
            trades += execute(name, inst, "P3_REALRATE", p3_signals(inst, rr), rng, randoms)
        print(name, "ok", flush=True)
    mt5.shutdown()
    tr, rn = pd.DataFrame(trades), pd.DataFrame(randoms)
    OUT.mkdir(parents=True, exist_ok=True)
    tr.to_csv(OUT / "commodity_longrun_trades.csv", index=False)
    rn.to_csv(OUT / "commodity_longrun_random.csv", index=False)
    rng = np.random.default_rng(31)
    head = ("| ops | R/op (dos entradas) | R/op una posición | t | t día | acierto | TP1 | 2021-22 | 2023-24 | 2025-hoy | "
            "p azar | azar R/op |")
    sep = "|---:|---:|---:|---:|---:|---:|---:|---|---|---|---:|---:|"

    def line(label, s, verdict=""):
        per = " | ".join(f"{m:+.3f} ({n})" if np.isfinite(m) else "—" for m, n in s["per"])
        return (f"| {label} |{(' ' + verdict + ' |') if verdict else ''} {s['ops']} | {s['r']:+.4f} | {s['r1']:+.4f} | "
                f"{s['t']:+.2f} | {s['tday']:+.2f} | {s['wr']:.1%} | {s['tp1']:.0%} | {per} | {s['p']:.3f} | {s['rnd']:+.4f} |")

    L = ["# Materias primas con 5 años de datos externos (2021 → hoy) — replay del pre-registro (22-oct-2026)", "",
         "## Fidelidad de los datos", "", *fidelity, "",
         "## Global por estrategia", "", "| estrategia | veredicto " + head, "|---|---" + sep]
    verdicts = {}
    for strat in STRATEGIES:
        g = tr[tr.strategy == strat]
        if g.empty:
            continue
        s = summarize(g, rn[rn.strategy == strat], rng)
        ok = (all(np.isfinite(m) and m > 0 for m, _ in s["per"]) and s["t"] >= 2.4 and s["tday"] >= 2.0 and s["p"] < 0.0167)
        verdicts[strat] = "SUPERA" if ok else "NO SUPERA"
        L.append(line(strat, s, verdicts[strat]))
    L += ["", "## Por instrumento (exploratorio)", "", "| estrategia · instrumento " + head, "|---" + sep]
    for (strat, sym), g in tr.groupby(["strategy", "symbol"]):
        L.append(line(f"{strat} · {sym}", summarize(g, rn[(rn.strategy == strat) & (rn.symbol == sym)], rng)))
    (OUT / "commodity_longrun_report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(verdicts)


if __name__ == "__main__":
    main()
