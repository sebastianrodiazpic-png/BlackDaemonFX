"""Offline MSNR audit. Reads saved candles and never connects to a broker."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from strategy.malaysian_snr.config import MalaysianSNRConfig
from tools.replay_msnr_live_faithful import replay_frames

ESTIMATED_SPREADS = {"Boom 1000 Index": 1.75, "Crash 1000 Index": 1.75,
                     "Step Index": .10, "XAUUSD": .59, "BTCUSD": 18.424}


def load_cached_frames(symbol):
    prefix = symbol.replace(" ", "_")
    directory = ROOT / "data" / "historical"
    def read(tf):
        path = directory / f"{prefix}_{tf}.csv"
        if not path.exists():
            return None
        frame = pd.read_csv(path)
        frame["time"] = pd.to_datetime(frame.time, utc=True)
        return frame.sort_values("time").drop_duplicates("time").reset_index(drop=True)
    h1, m15 = read("H1"), read("M15")
    if h1 is None:
        raise ValueError(f"No cached H1 for {symbol}")
    if m15 is None:
        m5 = read("M5")
        if m5 is None:
            raise ValueError(f"No cached M15/M5 for {symbol}")
        bars = m5.set_index("time").resample("15min", label="left", closed="left")
        m15 = bars.agg({"open":"first", "high":"max", "low":"min", "close":"last"})
        m15 = m15[bars.close.count() == 3].dropna().reset_index()
    # Available CSVs have no D1. This UTC aggregation is a documented proxy;
    # native broker D1 can have a different trading-day boundary.
    d1 = h1.set_index("time").resample("1D", label="left", closed="left").agg(
        {"open":"first", "high":"max", "low":"min", "close":"last"}).dropna().reset_index()
    return {"H1":h1, "M15":m15, "D1":d1}


def statistics(frame):
    if frame.empty:
        return {"trades":0, "win_pct":None, "expectancy_r":None, "total_r":0,
                "expectancy_ci95":None, "profit_factor":None, "max_drawdown_r":None}
    rr = frame.rr.to_numpy(dtype=float)
    mean = float(rr.mean())
    error = 1.96 * float(rr.std(ddof=1)) / np.sqrt(len(rr)) if len(rr) > 1 else float("inf")
    cumulative = np.r_[0., rr.cumsum()]
    loss = -float(rr[rr < 0].sum())
    return {"trades":len(rr), "win_pct":round(100 * float((rr > 0).mean()),2),
            "expectancy_r":round(mean,4), "total_r":round(float(rr.sum()),3),
            "expectancy_ci95":[float(round(mean-error,4)),float(round(mean+error,4))] if len(rr) >= 30 and np.isfinite(error) else None,
            "profit_factor":round(float(rr[rr > 0].sum()) / loss,3) if loss else None,
            "max_drawdown_r":round(float((np.maximum.accumulate(cumulative)-cumulative).max()),3)}


def legacy_audit():
    frame = pd.read_csv(ROOT / "storage" / "analysis" / "msnr_faithful_trades.csv")
    frame["time"] = pd.to_datetime(frame.time, utc=True)
    cutoff = frame.time.min() + (frame.time.max() - frame.time.min()) * .7
    # This holdout is diagnostic only: the existing allowlist was already
    # selected using this entire dataset, so it is not an untouched test set.
    rows = []
    for symbol, group in frame.groupby("symbol"):
        rows.append({"symbol":symbol, "all":statistics(group),
                     "last_30pct":statistics(group[group.time >= cutoff])})
    return {"overall":statistics(frame), "period_start":str(frame.time.min()),
            "period_end":str(frame.time.max()), "diagnostic_cutoff":str(cutoff),
            "symbols":rows, "holdout_is_untouched":False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--symbols", default="Boom 1000 Index,Crash 1000 Index,Step Index,XAUUSD,BTCUSD")
    parser.add_argument("--spread-multiplier", type=float, default=1.)
    parser.add_argument("--cost-r", type=float, default=0.)
    parser.add_argument("--output", default="storage/analysis/msnr_causal_audit")
    args = parser.parse_args()
    if args.days <= 0 or args.spread_multiplier < 0 or args.cost_r < 0:
        parser.error("days must be positive; costs must be non-negative")
    out = ROOT / args.output
    out.mkdir(parents=True, exist_ok=True)
    cfg = MalaysianSNRConfig()
    metadata = {"strategy_version":cfg.strategy_version, "days":args.days,
                "cost_r":args.cost_r, "spread_multiplier":args.spread_multiplier,
                "d1_source":"UTC H1 aggregation, not native broker D1", "symbols":[],
                "legacy":legacy_audit()}
    trades = []
    for symbol in args.symbols.split(","):
        symbol = symbol.strip()
        try:
            frames = load_cached_frames(symbol)
            spread = ESTIMATED_SPREADS[symbol] * args.spread_multiplier
            print(f"{symbol}: causal replay {args.days}d", flush=True)
            results = replay_frames(symbol, frames, args.days, cfg, spread, args.cost_r)
            frame = pd.DataFrame(results)
            stats = statistics(frame)
            stats.update(symbol=symbol, m15_start=str(frames["M15"].time.min()),
                         m15_end=str(frames["M15"].time.max()), estimated_spread=spread)
            metadata["symbols"].append(stats)
            trades.extend(results)
            print(f"  {stats}", flush=True)
        except (ValueError, KeyError) as exc:
            metadata["symbols"].append({"symbol":symbol, "error":str(exc)})
    pd.DataFrame(trades).to_csv(out / "trades.csv", index=False)
    metadata["overall"] = statistics(pd.DataFrame(trades))
    (out / "metrics.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = ["# Auditoría Malaysian SNR: causalidad y selección", "",
             f"Versión: {cfg.strategy_version}. Ventana: últimos {args.days} días de cada archivo.",
             "R = riesgo inicial total de ambas piernas. Cada activo se simula por separado; no se aplican límites de cartera.", "",
             "| Activo | Trades | Aciertos | R/trade | IC95 aproximado | Total R |",
             "|---|---:|---:|---:|---|---:|"]
    for row in metadata["symbols"]:
        if "error" not in row:
            win = f"{row['win_pct']}%" if row['win_pct'] is not None else "Sin operaciones"
            mean = row['expectancy_r'] if row['expectancy_r'] is not None else "—"
            interval = row['expectancy_ci95'] if row['expectancy_ci95'] is not None else "Muestra insuficiente"
            lines.append(f"| {row['symbol']} | {row['trades']} | {win} | {mean} | {interval} | {row['total_r']} |")
    lines += ["", "Los intervalos son aproximaciones descriptivas que asumen independencia; no demuestran ventaja ni consideran dependencia entre trades. No se muestran con menos de 30 trades.",
              "El spread es una estimación fija; no incluye comisión ni swaps salvo el costo adicional indicado. No se incluyen latencia, disponibilidad ni ejecución real del broker.",
              f"Multiplicador de spread: {args.spread_multiplier}; costo adicional por trade: {args.cost_r}R.",
              "D1 se reconstruye de H1 con límites UTC: no sustituye validación con D1 nativo del proveedor en vivo.",
              "Estos datos no son cotizaciones actuales. La allowlist existente fue elegida con el histórico previo; este replay reutiliza parte de esos datos y no es un test independiente.",
              "El modelo IA entrenado con el replay antiguo y los scores de confirmación 85/90 no acreditan una probabilidad de éxito para esta versión.",
              "No se enviaron órdenes, no se reinició ningún bot ni se reemplazaron los informes históricos."]
    (out / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Report: {out / 'report.md'}", flush=True)


if __name__ == "__main__":
    main()
