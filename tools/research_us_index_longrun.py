"""Investigación (solo lectura): validación de RSI2 y NIGHT con 5 años de Dukascopy (2021 → hoy) (PRE-REGISTRO del
22-oct-2026, ver REGISTRO_CAMBIOS_ESTRATEGIA.md).

RSI2: reglas del worker (strategy/connors_rsi2/rsi2_daily.py: RSI(2) D1 < 10 sobre SMA200, solo largos, stop 2 × ATR14
D1, dos entradas TP1 1R / runner 2R con BE, salida tras cierre D1 > SMA5 o 10 velas D1), camino H1.
NIGHT: compra en la apertura de la vela H1 de las 16:00 NY y venta en la apertura de la H1 de las 09:00 NY y de las
10:00 NY del siguiente día hábil (Dukascopy no da M30: la salida real de las 09:30 queda entre ambas); stop 1 × ATR14 D1.
Costes: spread mediano del broker y swap actual del broker por noche.
Criterio: R/op > 0 en 2021-2022, 2023-2024 y 2025-hoy; t por día >= 2,0; p azar < 0,05.

Uso:   .venv/Scripts/python.exe tools/research_us_index_longrun.py
Salida: storage/analysis/us_index_longrun_{trades,random}.csv y us_index_longrun_report.md
"""
from __future__ import annotations

import sys
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import tools.research_forex_indicators as fx  # noqa: E402
import tools.research_synthetic_indicators as base  # noqa: E402
from strategy.connors_rsi2.rsi2_daily import daily_indicators  # noqa: E402
from tools.research_commodity_longrun import extend_daily_with_hourly  # noqa: E402

EXT = ROOT / "storage" / "external_data" / "dukascopy"
OUT = ROOT / "storage" / "analysis"
BROKER = {"US500": "US SP 500", "USTEC": "US Tech 100", "US30": "Wall Street 30", "US2000": "US Small Cap 2000"}
NIGHT_SYMBOLS = ("US500", "USTEC")
# 5 años de datos (decisión del usuario, 22-oct-2026): Dukascopy desde 2021; la SMA200 diaria deja señales desde ~nov-2021.
PERIODS = (("2021-2022", "2021-01-01", "2023-01-01"), ("2023-2024", "2023-01-01", "2025-01-01"), ("2025-hoy", "2025-01-01", "2100-01-01"))
NY = ZoneInfo("America/New_York")
fx.SPREAD_CAP = 1.0


def load(name, mt5):
    d1 = pd.read_csv(EXT / f"{name}_daily_bid.csv", parse_dates=["time"])
    h1 = pd.read_csv(EXT / f"{name}_hourly_bid.csv", parse_dates=["time"]).reset_index(drop=True)
    d1 = extend_daily_with_hourly(d1[d1["volume"] > 0].reset_index(drop=True), h1[h1["volume"] > 0])
    sym = BROKER[name]
    mt5.symbol_select(sym, True)
    info = mt5.symbol_info(sym)
    m = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M15, 0, 20_000)
    spread = float(np.median(m["spread"][m["spread"] > 0])) * float(info.point)
    bd = pd.DataFrame(mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_D1, 0, 3000))
    bd["day"] = pd.to_datetime(bd["time"], unit="s").dt.date
    j = pd.merge(d1.assign(day=d1.time.dt.date)[["day", "close"]], bd[["day", "close"]], on="day", suffixes=("_d", "_b"))
    corr = float(j.close_d.pct_change().corr(j.close_b.pct_change())) if len(j) > 60 else float("nan")
    return {"d1": d1, "h1": h1, "info": info, "spread": spread, "corr": corr, "overlap": len(j),
            "level": float((j.close_d / j.close_b).median()) if len(j) else float("nan"), "from": d1.time.iat[0]}


def h1_at(h1, t):
    return int(np.searchsorted(h1["time"].values, pd.Timestamp(t).tz_convert(None).to_datetime64()))


def rsi2_trades(name, inst, rng, randoms):
    d = daily_indicators(inst["d1"]).reset_index(drop=True)
    h1, out, busy = inst["h1"], [], None
    spreads = np.full(len(h1), inst["spread"])

    def plan(i):
        k = next((k for k in range(i + 1, min(i + 11, len(d))) if d.close.iat[k] > d.sma_exit.iat[k]), min(i + 10, len(d) - 1))
        return d.time.iat[i] + pd.Timedelta(days=1), d.time.iat[k] + pd.Timedelta(days=1)

    for i in np.flatnonzero(d["signal"].to_numpy()):
        entry, exit_ = plan(i)
        if busy is not None and entry <= busy:
            continue
        t = fx.trade(1, h1_at(h1, entry), h1_at(h1, exit_), 2 * float(d.atr.iat[i]), h1, spreads, inst["info"])
        if isinstance(t, dict):
            busy = h1.time.iat[t["exit_idx"]]
            out.append({"symbol": name, "strategy": "RSI2", "time": entry, **t})
    valid = np.flatnonzero(d.sma_trend.notna().to_numpy()[:-12])
    for i in (rng.choice(valid, size=len(out), replace=True) if out else []):
        entry, exit_ = plan(int(i))
        t = fx.trade(1, h1_at(h1, entry), h1_at(h1, exit_), 2 * float(d.atr.iat[i]), h1, spreads, inst["info"])
        if isinstance(t, dict):
            randoms.append({"symbol": name, "strategy": "RSI2", "time": entry, "r": t["r"]})
    return out


def night_trades(name, inst, exit_hour, rng, randoms):
    d, h1 = inst["d1"].copy(), inst["h1"]
    d["atr"] = base.atr(d, 14)
    d["avail"] = d.time + pd.Timedelta(days=1)
    local = h1.time.dt.tz_convert(NY)
    h1d = h1.assign(ny_date=local.dt.date, ny_hour=local.dt.hour, wd=local.dt.weekday)
    opens = h1d[(h1d.ny_hour == 16) & (h1d.wd < 5)]
    exits = h1d[(h1d.ny_hour == exit_hour) & (h1d.wd < 5)]
    exit_times = exits.time.values  # datetime64 UTC sin zona
    o, hi, lo = h1.open.to_numpy(float), h1.high.to_numpy(float), h1.low.to_numpy(float)
    info, sp = inst["info"], inst["spread"]
    rate = float(info.swap_long) * float(info.point)
    atr_at = pd.merge_asof(opens[["time"]], d[["avail", "atr"]], left_on="time", right_on="avail", direction="backward")["atr"].to_numpy()
    out = []
    for (j, row), atr in zip(opens.iterrows(), atr_at):
        k_t = exit_times[np.searchsorted(exit_times, row.time.to_datetime64(), side="right")] if (exit_times > row.time.to_datetime64()).any() else None
        if k_t is None or not np.isfinite(atr) or atr <= 0:
            continue
        k = int(np.searchsorted(h1.time.values, k_t))
        fill, risk = o[j] + sp, float(atr)
        sl, px, end = fill - risk, None, k
        for i in range(j, k):
            if i > j and o[i] <= sl:
                px, end = o[i], i
                break
            if lo[i] <= sl:
                px, end = sl, i
                break
        px = o[k] if px is None else px
        nights = max(1, (h1.time.iat[end].normalize() - h1.time.iat[j].normalize()).days)
        out.append({"symbol": name, "strategy": f"NIGHT_{exit_hour:02d}h", "time": row.time, "r": (px - fill) / risk + nights * rate / risk,
                    "tp1": False, "exit_idx": end, "direction": "BUY"})
    # azar: misma duración y stop, a horas aleatorias
    for _ in range(len(out)):
        j = int(rng.integers(300, len(h1) - 40))
        span = int(rng.integers(15, 20))
        a = atr_at[int(rng.integers(len(atr_at)))]
        if not np.isfinite(a):
            continue
        fill, sl, px = o[j] + sp, o[j] + sp - a, None
        for i in range(j, j + span):
            if lo[i] <= sl:
                px = sl
                break
        px = o[j + span] if px is None else px
        randoms.append({"symbol": name, "strategy": f"NIGHT_{exit_hour:02d}h", "time": h1.time.iat[j], "r": (px - fill) / a + rate / a})
    return out


def summarize(g, rn, rng):
    t = pd.to_datetime(g.time, utc=True)
    per = [g[(t >= pd.Timestamp(a, tz="UTC")) & (t < pd.Timestamp(b, tz="UTC"))].r for _, a, b in PERIODS]
    by_day = g.groupby(t.dt.date).r.mean()
    return {"ops": len(g), "r": g.r.mean(), "t": base.tstat(g.r), "tday": base.tstat(by_day), "days": len(by_day),
            "wr": (g.r > 0).mean(), "per": [(x.mean() if len(x) else np.nan, len(x)) for x in per],
            "p": base.chance_p(g, rn, rng), "rnd": rn.r.mean() if len(rn) else np.nan}


def verdict(s):
    pos = [m for m, _ in s["per"] if np.isfinite(m)]
    if s["r"] <= 0 or sum(m <= 0 for m in pos) >= 2:
        return "RETIRAR"
    if all(m > 0 for m in pos) and len(pos) == 3 and s["tday"] >= 2.0 and s["p"] < 0.05:
        return "MANTENER"
    return "NO CONCLUYENTE"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    import MetaTrader5 as mt5
    mt5.initialize()
    rng = np.random.default_rng(41)
    trades, randoms, fid = [], [], []
    for name in BROKER:
        try:
            inst = load(name, mt5)
        except FileNotFoundError:
            fid.append(f"- {name}: sin datos descargados")
            continue
        ok = np.isfinite(inst["corr"]) and inst["corr"] >= 0.95
        fid.append(f"- {name} → {BROKER[name]}: Dukascopy desde {inst['from']:%Y-%m-%d}; correlación con el broker "
                   f"{inst['corr']:.3f} ({inst['overlap']} días); nivel {inst['level']:.3f} -> {'INCLUIDO' if ok else 'EXCLUIDO'}")
        if not ok:
            continue
        trades += rsi2_trades(name, inst, rng, randoms)
        if name in NIGHT_SYMBOLS:
            for hour in (9, 10):
                trades += night_trades(name, inst, hour, rng, randoms)
        print(name, "ok", flush=True)
    mt5.shutdown()
    tr, rn = pd.DataFrame(trades), pd.DataFrame(randoms)
    tr.to_csv(OUT / "us_index_longrun_trades.csv", index=False)
    rn.to_csv(OUT / "us_index_longrun_random.csv", index=False)
    rng = np.random.default_rng(43)
    head = "| ops | R/op | t | t día (días) | acierto | 2021-22 | 2023-24 | 2025-hoy | p azar | azar R/op |"
    sep = "|---:|---:|---:|---|---:|---|---|---|---:|---:|"

    def line(label, s, v=""):
        per = " | ".join(f"{m:+.3f} ({n})" if np.isfinite(m) else "—" for m, n in s["per"])
        return (f"| {label} |{(' ' + v + ' |') if v else ''} {s['ops']} | {s['r']:+.4f} | {s['t']:+.2f} | {s['tday']:+.2f} ({s['days']}) | "
                f"{s['wr']:.1%} | {per} | {s['p']:.3f} | {s['rnd']:+.4f} |")

    L = ["# Validación de RSI2 y NIGHT con 5 años de Dukascopy (pre-registro 22-oct-2026)", "", "## Fidelidad", "", *fid, "",
         "## Veredicto", "", "| estrategia | veredicto " + head, "|---|---" + sep]
    out = {}
    for strat in sorted(tr.strategy.unique()):
        s = summarize(tr[tr.strategy == strat], rn[rn.strategy == strat], rng)
        out[strat] = verdict(s)
        L.append(line(strat, s, out[strat]))
    L += ["", "## Por índice", "", "| estrategia · índice " + head, "|---" + sep]
    for (strat, sym), g in tr.groupby(["strategy", "symbol"]):
        L.append(line(f"{strat} · {sym}", summarize(g, rn[(rn.strategy == strat) & (rn.symbol == sym)], rng)))
    (OUT / "us_index_longrun_report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
