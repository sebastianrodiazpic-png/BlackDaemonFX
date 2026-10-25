"""Investigación (solo lectura): mercados aún no analizados — ETF y cripto del broker (24-oct-2026).

PRE-REGISTRO (fijado antes de ver resultados; datos D1 y camino H1 del broker MT5; spread mediano M15 del broker y swap
actual por noche; contrato de dos entradas: TP1 1R + runner 2R con BE tras TP1; la regla cierra lo que quede):
  RSI2 · ETF y cripto: reglas idénticas al worker RSI2 (strategy/connors_rsi2/rsi2_daily.py): cierre D1 > SMA200 y
         RSI(2) < 10, solo largos, stop 2 × ATR14 D1, salida tras cierre D1 > SMA5 o 10 velas D1.
  BRK  · Solo cripto: ruptura Donchian, cierre D1 > máximo de 20 días (BUY) o < mínimo (SELL), stop 2 × ATR14 D1,
         salida tras cierre D1 al otro lado del canal de 10 días o 40 velas D1.
Criterio: R/op > 0 en cada periodo; t agrupado por día >= 2,0; p azar < 0,05 (RSI2 en ETF: una prueba, confirma un
efecto ya validado) y < 0,025 en cripto (dos pruebas).
  Periodos ETF: 2023-10 → 2024-09, 2024-10 → 2025-09, 2025-10 → hoy.  Periodos cripto: 2019-2021, 2022-2023, 2024-hoy.

Uso:   .venv/Scripts/python.exe tools/research_etf_crypto.py
Salida: storage/analysis/etf_crypto_{trades,random}.csv y etf_crypto_report.md
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
from strategy.connors_rsi2.rsi2_daily import daily_indicators  # noqa: E402

OUT = ROOT / "storage" / "analysis"
fx.SPREAD_CAP = 1.0
ETFS = ("SPY.US", "IVV.US", "VOO.US", "VTI.US", "DIA.US", "IWM.US", "IJR.US", "XLK.US", "XLF.US", "XLE.US", "VNQ.US",
        "EFA.US", "EEM.US", "IEMG.US", "VEA.US", "VWO.US", "GLD.US", "SLV.US", "GDX.US", "IVW.US", "ARKK.US", "TQQQ.US")
CRYPTO = ("BTCUSD", "ETHUSD", "SOLUSD", "BNBUSD", "ADAUSD", "BCHUSD", "LTCUSD", "XRPUSD", "DOGUSD", "AVAUSD", "LNKUSD", "DOTUSD")
PERIODS = {"ETF": (("2023-10→2024-09", "2023-10-01", "2024-10-01"), ("2024-10→2025-09", "2024-10-01", "2025-10-01"),
                   ("2025-10→hoy", "2025-10-01", "2100-01-01")),
           "CRYPTO": (("2019-2021", "2019-01-01", "2022-01-01"), ("2022-2023", "2022-01-01", "2024-01-01"),
                      ("2024-hoy", "2024-01-01", "2100-01-01"))}


def load(mt5, sym):
    if not mt5.symbol_select(sym, True):
        return None
    info = mt5.symbol_info(sym)
    d = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_D1, 0, 5000)
    h = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_H1, 0, 99_000)
    m = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M15, 0, 20_000)
    if d is None or h is None or len(d) < 260 or info is None:
        return None
    d, h = pd.DataFrame(d), pd.DataFrame(h)
    for f in (d, h):
        f["time"] = pd.to_datetime(f["time"], unit="s", utc=True)
    spread = (float(np.median(m["spread"][m["spread"] > 0])) if m is not None and (m["spread"] > 0).any() else float(info.spread)) * float(info.point)
    return {"d1": d, "h1": h.reset_index(drop=True), "info": info, "spread": spread}


def h1_at(h1, t):
    return int(np.searchsorted(h1["time"].values, pd.Timestamp(t).tz_convert(None).to_datetime64()))


def simulate(inst, sign, entry_t, exit_t, risk):
    h1 = inst["h1"]
    if pd.Timestamp(entry_t) < h1.time.iat[0]:
        return None
    return fx.trade(sign, h1_at(h1, entry_t), h1_at(h1, exit_t), risk, h1, np.full(len(h1), inst["spread"]), inst["info"])


def rsi2_plans(inst):
    d = daily_indicators(inst["d1"]).reset_index(drop=True)
    out = []
    for i in np.flatnonzero(d["signal"].to_numpy()):
        k = next((k for k in range(i + 1, min(i + 11, len(d))) if d.close.iat[k] > d.sma_exit.iat[k]), min(i + 10, len(d) - 1))
        out.append((1, d.time.iat[i] + pd.Timedelta(days=1), d.time.iat[k] + pd.Timedelta(days=1), 2 * float(d.atr.iat[i])))
    return out, d


def brk_plans(inst):
    d = inst["d1"].copy()
    d["atr"] = base.atr(d, 14)
    hi20, lo20 = d.high.shift(1).rolling(20).max(), d.low.shift(1).rolling(20).min()
    hi10, lo10 = d.high.shift(1).rolling(10).max(), d.low.shift(1).rolling(10).min()
    out = []
    for i in range(30, len(d) - 1):
        sign = 1 if d.close.iat[i] > hi20.iat[i] else -1 if d.close.iat[i] < lo20.iat[i] else 0
        if not sign:
            continue
        k = next((k for k in range(i + 1, min(i + 41, len(d))) if (sign > 0 and d.close.iat[k] < lo10.iat[k]) or (sign < 0 and d.close.iat[k] > hi10.iat[k])),
                 min(i + 40, len(d) - 1))
        out.append((sign, d.time.iat[i] + pd.Timedelta(days=1), d.time.iat[k] + pd.Timedelta(days=1), 2 * float(d.atr.iat[i])))
    return out, d


def run(name, market, strat, inst, plans, rng, trades, randoms, both_sides):
    busy = None
    n0 = len(trades)
    for sign, entry, exit_, risk in plans:
        if busy is not None and entry <= busy:
            continue
        t = simulate(inst, sign, entry, exit_, risk)
        if isinstance(t, dict):
            busy = inst["h1"].time.iat[t["exit_idx"]]
            trades.append({"symbol": name, "market": market, "strategy": strat, "time": entry, **t})
    d = inst["d1"]
    for _ in range(len(trades) - n0):
        sign, entry, exit_, risk = plans[int(rng.integers(len(plans)))]
        span = max(1, (exit_ - entry).days)
        start = d.time.iat[int(rng.integers(220, len(d) - span - 2))] + pd.Timedelta(days=1)
        t = simulate(inst, int(rng.choice((-1, 1))) if both_sides else 1, start, start + pd.Timedelta(days=span), risk)
        if isinstance(t, dict):
            randoms.append({"symbol": name, "market": market, "strategy": strat, "time": start, "r": t["r"]})


def summary(g, rn, market, rng):
    t = pd.to_datetime(g.time, utc=True)
    per = [g[(t >= pd.Timestamp(a, tz="UTC")) & (t < pd.Timestamp(b, tz="UTC"))].r for _, a, b in PERIODS[market]]
    by_day = g.groupby(t.dt.date).r.mean()
    return {"ops": len(g), "r": g.r.mean(), "tday": base.tstat(by_day), "days": len(by_day), "wr": (g.r > 0).mean(),
            "per": [(x.mean() if len(x) else np.nan, len(x)) for x in per], "p": base.chance_p(g, rn, rng),
            "rnd": rn.r.mean() if len(rn) else np.nan}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    import MetaTrader5 as mt5
    mt5.initialize()
    rng = np.random.default_rng(53)
    trades, randoms, status = [], [], []
    for market, syms in (("ETF", ETFS), ("CRYPTO", CRYPTO)):
        for s in syms:
            inst = load(mt5, s)
            if inst is None:
                status.append(f"- {s}: sin datos")
                continue
            status.append(f"- {s}: D1 desde {inst['d1'].time.iat[0]:%Y-%m-%d}, H1 desde {inst['h1'].time.iat[0]:%Y-%m-%d}, spread {inst['spread']:.4f}")
            plans, _ = rsi2_plans(inst)
            run(s, market, "RSI2", inst, plans, rng, trades, randoms, both_sides=False)
            if market == "CRYPTO":
                plans, _ = brk_plans(inst)
                run(s, market, "BRK", inst, plans, rng, trades, randoms, both_sides=True)
            print(s, "ok", flush=True)
    mt5.shutdown()
    tr, rn = pd.DataFrame(trades), pd.DataFrame(randoms)
    tr.to_csv(OUT / "etf_crypto_trades.csv", index=False)
    rn.to_csv(OUT / "etf_crypto_random.csv", index=False)
    rng = np.random.default_rng(59)
    L = ["# ETF y cripto del broker — replay del pre-registro (24-oct-2026)", "", "## Datos", "", *status, "", "## Veredicto", "",
         "| mercado · estrategia | veredicto | ops | R/op | t día (días) | acierto | periodo 1 | periodo 2 | periodo 3 | p azar | azar R/op |",
         "|---|---|---:|---:|---|---:|---|---|---|---:|---:|"]
    for (market, strat), g in tr.groupby(["market", "strategy"]):
        s = summary(g, rn[(rn.market == market) & (rn.strategy == strat)], market, rng)
        alpha = 0.05 if (market, strat) == ("ETF", "RSI2") else 0.025
        ok = all(np.isfinite(m) and m > 0 for m, _ in s["per"]) and s["tday"] >= 2.0 and s["p"] < alpha
        per = " | ".join(f"{m:+.3f} ({n})" if np.isfinite(m) else "—" for m, n in s["per"])
        L.append(f"| {market} · {strat} | {'SUPERA' if ok else 'NO SUPERA'} | {s['ops']} | {s['r']:+.4f} | {s['tday']:+.2f} ({s['days']}) | "
                 f"{s['wr']:.1%} | {per} | {s['p']:.3f} | {s['rnd']:+.4f} |")
    L += ["", "## Por símbolo (exploratorio)", "", "| mercado · estrategia · símbolo | ops | R/op | acierto |", "|---|---:|---:|---:|"]
    for (market, strat, sym), g in tr.groupby(["market", "strategy", "symbol"]):
        L.append(f"| {market} · {strat} · {sym} | {len(g)} | {g.r.mean():+.4f} | {(g.r > 0).mean():.0%} |")
    (OUT / "etf_crypto_report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("informe: storage/analysis/etf_crypto_report.md")


if __name__ == "__main__":
    main()
