"""Investigación (solo lectura): ¿qué condiciones separan trades ICT buenos de malos en sintéticos? — 20-oct-2026.

Parte del replay fiel ICT con entrada limitada (storage/analysis/ict_limit_entry_signals.csv, 365 días) y añade, por
señal, variables de contexto calculadas con velas H1 CERRADAS antes de la señal (sin mirar al futuro):
ADX(14), ATR(14), percentil de ATR en 30 días, distancia del SL en ATR, hora UTC, día, dirección, spread/SL y velas
hasta el fill del límite. Guarda storage/analysis/ict_slices_features.csv para cortar por tramos.

Uso:
    .venv/Scripts/python.exe tools/research_ict_slices.py            # descarga H1 de MT5 (caché) y construye la tabla
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
CACHE = OUT / "ict_slices_h1_cache"


def load_h1(mt5, symbol: str, start: datetime, end: datetime) -> pd.DataFrame | None:
    path = CACHE / f"{symbol.replace(' ', '_').replace('(', '').replace(')', '')}.pkl"
    if path.exists():
        return pd.read_pickle(path)
    mt5.symbol_select(symbol, True)
    rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_H1, start, end)
    if rates is None or len(rates) < 100:
        return None
    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    df.to_pickle(path)
    return df


def h1_features(h1: pd.DataFrame) -> pd.DataFrame:
    from strategy.malaysian_snr.malaysian_snr_strategy import compute_adx
    h = h1.copy()
    prev_close = h["close"].shift()
    tr = pd.concat([h["high"] - h["low"], (h["high"] - prev_close).abs(), (h["low"] - prev_close).abs()], axis=1).max(axis=1)
    h["atr"] = tr.rolling(14).mean()
    h["adx"] = compute_adx(h, 14)
    h["atr_pct30"] = h["atr"].rolling(24 * 30, min_periods=24 * 10).rank(pct=True)
    h["ret24_atr"] = (h["close"] - h["close"].shift(24)) / h["atr"]  # tendencia 24 h en ATR
    # La vela H1 que abre a las T está cerrada a T+1h: solo se puede usar desde ese momento.
    h["available_at"] = h["time"] + pd.Timedelta(hours=1)
    return h[["available_at", "atr", "adx", "atr_pct30", "ret24_atr"]]


def build(signals: pd.DataFrame) -> pd.DataFrame:
    import MetaTrader5 as mt5
    if not mt5.initialize():
        raise SystemExit("No se pudo inicializar MT5")
    try:
        start = signals["t"].min().to_pydatetime() - timedelta(days=45)
        end = signals["t"].max().to_pydatetime() + timedelta(days=1)
        parts = []
        for sym, g in signals.groupby("symbol"):
            h1 = load_h1(mt5, sym, start, end)
            if h1 is None:
                print(f"{sym}: sin H1")
                continue
            f = h1_features(h1).sort_values("available_at")
            g = g.sort_values("t")
            parts.append(pd.merge_asof(g, f, left_on="t", right_on="available_at", direction="backward"))
            print(f"{sym}: {len(g)} señales")
    finally:
        mt5.shutdown()
    return pd.concat(parts, ignore_index=True)


def main():
    from config.ict_instrument_policy import ict_active_symbols
    sig = pd.read_csv(OUT / "ict_limit_entry_signals.csv")
    sig = sig[sig["synthetic"] & sig["lim_rr"].notna()].copy()
    sig["t"] = pd.to_datetime(sig["time"], utc=True)
    sig["spread_sl"] = sig["spread"] / sig["lim_risk"]
    sig["active"] = sig["symbol"].isin(ict_active_symbols("SYNTHETICS"))
    df = build(sig)
    df["sl_atr"] = df["lim_risk"] / df["atr"]
    df["hour_utc"] = df["t"].dt.hour
    df["weekday"] = df["t"].dt.weekday
    df["half"] = np.where(df["t"] < df["t"].min() + (df["t"].max() - df["t"].min()) / 2, "H1", "H2")
    df["quarter"] = df["t"].dt.year.astype(str) + "Q" + df["t"].dt.quarter.astype(str)
    out = OUT / "ict_slices_features.csv"
    df.drop(columns=["available_at"]).to_csv(out, index=False)
    print(f"\n{len(df)} señales con contexto -> {out}")


if __name__ == "__main__":
    main()
