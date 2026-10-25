"""Descarga de datos externos para investigar materias primas (aprobada por el usuario el 22-oct-2026). Solo lectura
del bot: escribe en storage/external_data/ (no versionado). Los ficheros se tratan como datos: CSV con pandas y .bi5
de Dukascopy con lzma de la librería estándar; no se ejecuta nada descargado.

  cot    · CFTC Disaggregated Futures Only (publicreporting.cftc.gov, dataset 72hh-3qpy): oro, plata, WTI, Brent, cacao.
  fred   · FRED: DFII10 (tipo real 10 años) y DTWEXBGS (dólar amplio).
  daily  · Dukascopy velas D1 bid y ask 2010 → hoy de XAUUSD, XAGUSD, BRENT, WTI y cacao (un .bi5 por año).
  hourly · Dukascopy velas H1 bid 2010 → hoy de los mismos (un .bi5 por mes).
  Índices US (US500, USTEC, US30, US2000): mismos ficheros, para validar RSI2 y NIGHT.

Uso:   .venv/Scripts/python.exe tools/download_commodity_external_data.py cot fred daily hourly [--instruments XAGUSD,BRENT] [--from-year 2021]
"""
from __future__ import annotations

import io
import lzma
import struct
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "storage" / "external_data"
UA = {"User-Agent": "Mozilla/5.0 (BlackDaemonFX research; personal use)"}
COT_MARKETS = {"088691": "GOLD", "084691": "SILVER", "067651": "WTI", "06765T": "BRENT", "073732": "COCOA"}
DUKA = {"XAUUSD": "XAUUSD", "XAGUSD": "XAGUSD", "BRENT": "BRENTCMDUSD", "WTI": "LIGHTCMDUSD", "COCOA": "COCOACMDUSD",
        # Índices US para validar RSI2 y NIGHT con historia larga (aprobado por el usuario el 22-oct-2026)
        "US500": "USA500IDXUSD", "USTEC": "USATECHIDXUSD", "US30": "USA30IDXUSD", "US2000": "USSC2000IDXUSD"}
FIRST_YEAR = 2010


def fetch(url: str, retries: int = 8, pause: float = 2.0) -> bytes | None:
    """GET con reintentos y espera creciente. None si el recurso no existe (404) o está vacío."""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=40) as resp:
                data = resp.read()
            time.sleep(pause)
            return data or None
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            time.sleep(pause * 4 * (attempt + 1))
        except Exception:
            time.sleep(pause * 4 * (attempt + 1))
    print(f"  FALLO tras {retries} intentos: {url}", flush=True)
    return None


def download_cot():
    cols = ("report_date_as_yyyy_mm_dd,market_and_exchange_names,cftc_contract_market_code,open_interest_all,"
            "prod_merc_positions_long,prod_merc_positions_short,swap_positions_long_all,swap__positions_short_all,"
            "m_money_positions_long_all,m_money_positions_short_all,other_rept_positions_long,other_rept_positions_short")
    codes = ",".join(f"'{c}'" for c in COT_MARKETS)
    url = ("https://publicreporting.cftc.gov/resource/72hh-3qpy.csv?$select=" + cols +
           f"&$where=cftc_contract_market_code%20in({codes})&$order=report_date_as_yyyy_mm_dd&$limit=50000")
    data = fetch(url.replace(" ", "%20"))
    df = pd.read_csv(io.BytesIO(data))
    df["market"] = df["cftc_contract_market_code"].astype(str).map(lambda c: COT_MARKETS.get(c.zfill(6), COT_MARKETS.get(c, c)))
    path = OUT / "cot_disaggregated.csv"
    df.to_csv(path, index=False)
    print(f"cot: {len(df)} filas -> {path} ({path.stat().st_size / 1e6:.2f} MB)", flush=True)
    print(df.groupby("market")["report_date_as_yyyy_mm_dd"].agg(["min", "max", "size"]), flush=True)


def download_fred():
    for sid in ("DFII10", "DTWEXBGS"):
        data = fetch(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}")
        path = OUT / f"fred_{sid}.csv"
        path.write_bytes(data)
        df = pd.read_csv(path)
        print(f"fred {sid}: {len(df)} filas {df.iloc[0, 0]} → {df.iloc[-1, 0]} ({path.stat().st_size / 1e3:.0f} KB)", flush=True)


def decode_bi5(raw: bytes, base: datetime, scale: float) -> pd.DataFrame:
    """Velas Dukascopy: registros big-endian de 24 bytes (segundos desde base, open, close, low, high, volumen)."""
    data = lzma.decompress(raw)
    rows = [struct.unpack(">5if", data[i:i + 24]) for i in range(0, len(data) - len(data) % 24, 24)]
    df = pd.DataFrame(rows, columns=["sec", "open", "close", "low", "high", "volume"])
    df["time"] = pd.Timestamp(base) + pd.to_timedelta(df["sec"], unit="s")
    for c in ("open", "close", "low", "high"):
        df[c] = df[c] / scale
    return df[["time", "open", "high", "low", "close", "volume"]]


def guess_scale(df_raw: pd.DataFrame, name: str) -> float:
    """Escala de precio de Dukascopy: se elige la que deja el precio en un rango plausible para el activo."""
    ref = {"XAUUSD": (200, 10000), "XAGUSD": (3, 150), "BRENT": (5, 300), "WTI": (-50, 300), "COCOA": (500, 30000),
           "US500": (800, 12000), "USTEC": (1500, 50000), "US30": (8000, 90000), "US2000": (400, 5000)}[name]
    med = float(df_raw["close"].median())
    for scale in (1, 10, 100, 1000, 10_000, 100_000):
        if ref[0] <= med / scale <= ref[1]:
            return float(scale)
    return 1000.0


def download_dukascopy(kind: str, only: tuple | None = None, first_year: int = FIRST_YEAR):
    now = datetime.now(timezone.utc)
    sides = ("BID", "ASK") if kind == "daily" else ("BID",)
    for name, code in DUKA.items():
        if only and name not in only:
            continue
        for side in sides:
            frames, scale = [], None
            raw_dir = OUT / "dukascopy" / "raw" / code / kind
            raw_dir.mkdir(parents=True, exist_ok=True)
            periods = ([(y, None) for y in range(first_year, now.year + 1)] if kind == "daily" else
                       [(y, m) for y in range(first_year, now.year + 1) for m in range(12) if (y, m + 1) <= (now.year, now.month)])
            for y, m in periods:
                fname = f"{side}_candles_day_1.bi5" if kind == "daily" else f"{side}_candles_hour_1.bi5"
                url = f"https://datafeed.dukascopy.com/datafeed/{code}/{y}/" + (f"{m:02d}/" if m is not None else "") + fname
                local = raw_dir / (f"{y}_{side}.bi5" if m is None else f"{y}_{m + 1:02d}_{side}.bi5")
                raw = local.read_bytes() if local.exists() and local.stat().st_size > 0 else fetch(url)
                if not raw:
                    continue
                local.write_bytes(raw)
                base = datetime(y, (m or 0) + 1, 1, tzinfo=timezone.utc)
                try:
                    df = decode_bi5(raw, base, 1.0)
                except Exception as exc:
                    print(f"  {code} {y}-{m}: no decodifica ({exc})", flush=True)
                    continue
                if scale is None and len(df):
                    scale = guess_scale(df, name)
                for c in ("open", "close", "low", "high"):
                    df[c] = df[c] / scale
                frames.append(df)
            if not frames:
                print(f"{kind} {name} {side}: sin datos", flush=True)
                continue
            out = pd.concat(frames).drop_duplicates("time").sort_values("time")
            out = out[out["volume"] > 0] if kind == "hourly" else out
            path = OUT / "dukascopy" / f"{name}_{kind}_{side.lower()}.csv"
            out.to_csv(path, index=False)
            print(f"{kind} {name} {side}: {len(out)} velas {out.time.min():%Y-%m-%d} → {out.time.max():%Y-%m-%d} "
                  f"escala {scale:g} -> {path.name}", flush=True)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    OUT.mkdir(parents=True, exist_ok=True)
    args = sys.argv[1:]
    only = None
    first_year = FIRST_YEAR
    if "--from-year" in args:
        k = args.index("--from-year")
        first_year = int(args[k + 1])
        args = args[:k] + args[k + 2:]
    if "--instruments" in args:
        k = args.index("--instruments")
        only = tuple(x.strip() for x in args[k + 1].split(",") if x.strip())
        args = args[:k] + args[k + 2:]
    jobs = args or ["cot", "fred", "daily"]
    for job in jobs:
        {"cot": download_cot, "fred": download_fred, "daily": lambda: download_dukascopy("daily", only, first_year),
         "hourly": lambda: download_dukascopy("hourly", only, first_year)}[job]()


if __name__ == "__main__":
    main()
