"""
scratch/inspect_multiyear_trade_files.py
========================================
Inspección rápida de columnas y métricas por símbolo en los archivos de replay de 2+ años.
"""
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent

files = [
    "storage/analysis/msnr_2year_audit/trades_augmented.csv",
    "storage/analysis/msnr_v21_two_years_20261011/trades.csv",
    "storage/analysis/replay_ict_60_assets_2y_trades.csv",
    "storage/analysis/step_jump_workers_2y_smc_trades.csv",
    "storage/analysis/volatility_workers_2y_smc_trades.csv",
    "storage/analysis/orb_nunez_2y/trades.csv",
    "storage/analysis/orb_improvements_audit/all_variants_trades.csv",
    "storage/analysis/replay_msnr_exp_fase1_sinteticos_all29_2y.csv",
    "storage/analysis/replay_msnr_exp_fase2_tradicionales_all31_2y.csv",
]

for rel in files:
    p = PROJECT_ROOT / rel
    if p.exists():
        df = pd.read_csv(p, nrows=5)
        full = pd.read_csv(p)
        print(f"=== {rel} (rows={len(full)}) ===")
        print("  Columns:", list(df.columns))
        print("  Sample row:", df.iloc[0].to_dict() if len(df) > 0 else {})
