import os
import tempfile

target_file = r'dashboard\realtime_dashboard.py'

with open(target_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Limpiar etiquetas viejas en _CATEGORY_LABELS
old_labels = '''    "night_indices": "Sesgo nocturno · Índices US (cierre → apertura NY)",
    "drift_switch": "Ruptura Drift · Drift Switch Indices (compresión + Donchian)",
    "rsi2_us_indices": "RSI(2) diario · Índices US (Connors)",
    "carry_fx_g10": "Carry Forex G10 · swap real del broker (rebalanceo mensual)",
    "msnr_jump": "MSNR · Jump Index",
    "msnr_step": "MSNR · Step Index",
    "msnr_volatility": "MSNR · Volatility Index",
    "msnr_indices": "MSNR · Índices & Commodities",
    "msnr_boom": "MSNR · Boom Index (BUY Only)",
    "msnr_crash": "MSNR · Crash Index (SELL Only)",
    "msnr_forex": "MSNR · Forex & Cripto",
    "msnr_metals": "MSNR · Metales",
    "msnr_pruned": "MSNR · Activos Podados (PODA PREVENTIVA)",
    "gold_cuartos_xauusd": "Oro Cuartos (XAUUSD)",
    "gold_cuartos_micro_xauusd": "Oro Micro Cuartos (XAUUSDmicro)",
    "gold_cuartos_xagusd": "Plata Cuartos (XAGUSD)",
    "gold_cuartos_micro_xagusd": "Plata Micro Cuartos (XAGUSDmicro)",'''

new_labels = '''    # Categorías de workers retirados (NIGHT, DRIFT, RSI2, CARRY, MSNR viejo, GOLD CUARTOS) removidas.'''

assert old_labels in content, "old_labels snippet not found!"
content = content.replace(old_labels, new_labels)

# 2. Limpiar perfiles retirados de _WORKER_PROFILE_META
old_meta = '''    "CARRY": {
        "selection_profile": "CARRY",
        "category": "carry",
        "label": "Carry Forex G10",
        "strategy_key": "FX_CARRY",
        "strategy_label": "Carry · top 3 pares por swap real, rebalanceo mensual",
        "magic": 26082037,
    },
    "RSI2": {
        "selection_profile": "RSI2",
        "category": "rsi2",
        "label": "RSI(2) diario · Índices US",
        "strategy_key": "CONNORS_RSI2",
        "strategy_label": "RSI(2) de Connors · D1 sobre SMA200, salida cierre > SMA5",
        "magic": 26082036,
    },
    "ORB": {
        "selection_profile": "ORB",
        "category": "orb",
        "label": "ORB · Apertura New York (Sweep/HTF)",
        "strategy_key": "ORB",
        "strategy_label": "ORB New York (Sweep / HTF_Sweep)",
        "magic": 26082028,
    },
    "GOLD": {
        "selection_profile": "GOLD",
        "category": "gold",
        "label": "Cuartos · Oro/Plata (XAUUSD / XAGUSD)",
        "strategy_key": "GOLD_QUARTERS",
        "strategy_label": "Gold Quarters (Cuartos Psicológicos)",
        "magic": 26082029,
    },'''

new_meta = '''    "ORB": {
        "selection_profile": "ORB",
        "category": "orb",
        "label": "ORB · Apertura New York (Sweep/HTF)",
        "strategy_key": "ORB",
        "strategy_label": "ORB New York (Sweep / HTF_Sweep)",
        "magic": 26082028,
    },'''

assert old_meta in content, "old_meta snippet not found!"
content = content.replace(old_meta, new_meta)

# Guardar atómicamente
dir_name = os.path.dirname(os.path.abspath(target_file))
with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, encoding="utf-8") as tf:
    tf.write(content)
    tmp_path = tf.name

os.replace(tmp_path, target_file)
print("SUCCESS: _CATEGORY_LABELS and _WORKER_PROFILE_META cleaned!")
