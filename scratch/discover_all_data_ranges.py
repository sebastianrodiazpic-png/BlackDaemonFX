"""
scratch/discover_all_data_ranges.py
===================================
Inventario exhaustivo de solo lectura de todos los archivos de velas históricas
en data/ y storage/analysis/ escrito en UTF-8.
"""
from pathlib import Path
import pandas as pd
import pickle

PROJECT_ROOT = Path(__file__).resolve().parent.parent

dirs_to_scan = [
    PROJECT_ROOT / "data" / "historical",
    PROJECT_ROOT / "data" / "forex_historical",
    PROJECT_ROOT / "data" / "cache_msnr",
    PROJECT_ROOT / "data" / "cache",
    PROJECT_ROOT / "data" / "research",
    PROJECT_ROOT / "storage" / "analysis",
]

lines = []
for d in dirs_to_scan:
    lines.append(f"\n==================== {d.relative_to(PROJECT_ROOT)} (exists={d.exists()}) ====================")
    if not d.exists():
        continue
    for f in sorted(d.rglob("*")):
        if not f.is_file():
            continue
        if f.suffix.lower() not in (".csv", ".pkl", ".parquet"):
            continue
        rel = f.relative_to(d)
        if "daily_gold_quarters_2026" in f.name:
            continue
        if any(tf in f.name.upper() for tf in ["M15", "M5", "H1", "H4", "D1", "TRADES", "SUMMARY", "2Y", "5Y", "10Y", "FAITHFUL", "AUDIT"]):
            try:
                if f.suffix.lower() == ".csv":
                    df = pd.read_csv(f, nrows=5)
                    tcols = [c for c in df.columns if c.lower() in ("time", "datetime", "date", "timestamp", "open_time", "entry_time")]
                    if tcols:
                        tc = tcols[0]
                        s_col = pd.read_csv(f, usecols=[tc])[tc]
                        ts = pd.to_datetime(s_col, utc=True, errors="coerce").dropna()
                        if len(ts) > 0:
                            yrs = (ts.max() - ts.min()).total_seconds() / (86400 * 365.25)
                            lines.append(f"  {str(rel):56s} | rows={len(s_col):8,d} | {str(ts.min())[:10]} -> {str(ts.max())[:10]} ({yrs:4.2f}y)")
                        else:
                            lines.append(f"  {str(rel):56s} | rows={len(s_col):8,d}")
                    else:
                        s_all = pd.read_csv(f)
                        lines.append(f"  {str(rel):56s} | rows={len(s_all):8,d} | cols={list(df.columns)[:6]}")
                elif f.suffix.lower() == ".pkl":
                    with open(f, "rb") as fp:
                        obj = pickle.load(fp)
                    if isinstance(obj, pd.DataFrame):
                        tcols = [c for c in obj.columns if c.lower() in ("time", "datetime", "date", "timestamp")]
                        ts = pd.to_datetime(obj[tcols[0]], utc=True) if tcols else pd.to_datetime(obj.index, utc=True)
                        yrs = (ts.max() - ts.min()).total_seconds() / (86400 * 365.25)
                        lines.append(f"  {str(rel):56s} | rows={len(obj):8,d} | {str(ts.min())[:10]} -> {str(ts.max())[:10]} ({yrs:4.2f}y)")
                elif f.suffix.lower() == ".parquet":
                    df = pd.read_parquet(f)
                    tcols = [c for c in df.columns if c.lower() in ("time", "datetime", "date", "timestamp")]
                    ts = pd.to_datetime(df[tcols[0]], utc=True) if tcols else pd.to_datetime(df.index, utc=True)
                    yrs = (ts.max() - ts.min()).total_seconds() / (86400 * 365.25)
                    lines.append(f"  {str(rel):56s} | rows={len(df):8,d} | {str(ts.min())[:10]} -> {str(ts.max())[:10]} ({yrs:4.2f}y)")
            except Exception as e:
                lines.append(f"  {str(rel):56s} | err={e}")

out = PROJECT_ROOT / "scratch" / "discover_all_data_ranges_utf8.txt"
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"Saved {out} ({len(lines)} lines)")
