import pandas as pd
import numpy as np
import json
from pathlib import Path

# Cargar bases existentes
perfect_bases_path = Path("storage/analysis/replay_5y_perfect_strategy_bases.csv")
df_bases = pd.read_csv(perfect_bases_path) if perfect_bases_path.exists() else None

# Cargar comparación de sintéticos 5y MSNR
msnr_comp_path = Path("storage/analysis/replay_5y_msnr_synthetics_comparison.csv")
df_msnr_comp = pd.read_csv(msnr_comp_path) if msnr_comp_path.exists() else None

# Cargar ict 5y
ict_5y_path = Path("storage/analysis/ict_5y_by_symbol.csv")
df_ict_5y = pd.read_csv(ict_5y_path) if ict_5y_path.exists() else None

ict_v2_path = Path("storage/analysis/ict_5y_v2_improved_by_symbol.csv")
df_ict_v2 = pd.read_csv(ict_v2_path) if ict_v2_path.exists() else None

# Cargar Step 300 específico
step300_json_path = Path("storage/analysis/msnr_v21_two_years_20261011/results/Step_Index_300.json")
step300_data = json.load(open(step300_json_path)) if step300_json_path.exists() else None

print("Analisis cargado correctamente.")
