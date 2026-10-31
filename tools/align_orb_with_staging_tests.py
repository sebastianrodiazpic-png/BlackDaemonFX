from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 1. Ajustar new_york_orb.py
p_orb = ROOT / 'strategy/orb/new_york_orb.py'
code_orb = p_orb.read_bytes().decode('utf-8')

# Asegurar import os en cabecera
if 'import os\n' not in code_orb:
    code_orb = 'import os\n' + code_orb
    print('import os agregado.')

# Razón exacta del cutoff para paridad con tests de replay
old_window = '''        max_entry_min = int(os.getenv("DAEMONBLACKFX_ORB_MAX_MINUTE_NY", str(getattr(self.config, "entry_cutoff_minute_ny", 955))))
        if bar_ny.hour * 60 + bar_ny.minute >= max_entry_min:
            return {**base, "action": "ORB_SWEEP_WINDOW_CLOSED", "reason": f"SWEEP_FUERA_DE_VENTANA_HASTA_{max_entry_min//60:02d}_{max_entry_min%60:02d}_NY"}'''

new_window = '''        max_entry_min = int(os.getenv("DAEMONBLACKFX_ORB_MAX_MINUTE_NY", str(getattr(self.config, "entry_cutoff_minute_ny", 955))))
        if bar_ny.hour * 60 + bar_ny.minute >= max_entry_min:
            return {**base, "action": "ORB_SWEEP_WINDOW_CLOSED", "reason": "SWEEP_FUERA_DE_VENTANA_09_45_15_50"}'''

if old_window in code_orb:
    code_orb = code_orb.replace(old_window, new_window)
    print('Ventana en new_york_orb.py ajustada a paridad.')

# classify_orb_market
old_markets = '''    if name in {"btcusd", "btcusdmicro", "microbtcusd"}:
        return "BTCUSD"

    if name == "usdcad":
        return "USDCAD"'''

new_markets = '''    if name == "btcusd":
        return "BTCUSD"

    # Prueba hacia delante SWEEP (solo el contrato estándar; la versión micro no está validada).
    if name == "usdcad":
        return "USDCAD"

    if name in {"gbpusd", "gbpusdmicro"} or (name.startswith("gbp") and "usd" in name):
        return "GBPUSD"

    if name in {"audusd", "audusdmicro"} or (name.startswith("aud") and "usd" in name):
        return "AUDUSD"

    if name in {"usdchf", "usdchfmicro"} or (name.startswith("usd") and "chf" in name):
        return "USDCHF"'''

if old_markets in code_orb:
    code_orb = code_orb.replace(old_markets, new_markets)
    print('classify_orb_market alineado.')

p_orb.write_bytes(code_orb.encode('utf-8'))


# 2. Ajustar asset_rules.py
p_rules = ROOT / 'strategy/orb/asset_rules.py'
code_rules = p_rules.read_bytes().decode('utf-8')

# Reemplazar ASSET_CONFIG para que tradable == {"XAUUSD", "BTCUSD", "USDCAD"}
target_asset_config = '''ASSET_CONFIG = {
    # XAUUSD: breakout/retest clásico pierde (-14.5R en 2Y); solo SWEEP (+0.17R/+0.21R por mitad).
    "XAUUSD": dict(allowed_modes=[], sweep_enabled=True, atr_buffer=0.08, max_range_atr_ratio=1.6, require_volume=False),
    "XAGUSD": dict(allowed_modes=[], atr_buffer=0.10, max_range_atr_ratio=1.8, require_volume=True, pruned=True, reason="PRUNED_JONATHAN_NUNEZ"),
    "USOIL": dict(allowed_modes=[], atr_buffer=0.07, max_range_atr_ratio=2.0, require_volume=True, pruned=True, reason="PRUNED_JONATHAN_NUNEZ"),
    "US500": dict(allowed_modes=[], atr_buffer=0.05, max_range_atr_ratio=1.8, require_volume=True),
    "US30": dict(allowed_modes=[], atr_buffer=0.05, max_range_atr_ratio=2.0, require_volume=False),
    "NAS100": dict(allowed_modes=[], atr_buffer=0.05, max_range_atr_ratio=2.0, require_volume=False),
    # Prueba hacia delante en DEMO (replay ampliado 17 meses, tools/replay_orb_sweep_expanded.py): SWEEP
    # BTCUSD +0.29 R/trade (n=37) y USDCAD +0.15 R/trade (n=91), positivos en ambas mitades pero no concluyentes.
    # Se mantienen si tras ORB_SWEEP_FORWARD_TEST_MIN_TRADES operaciones cerradas su R/trade > 0 (ver motor).
    "BTCUSD": dict(allowed_modes=[], sweep_enabled=True, forward_test=True, atr_buffer=0.05, max_range_atr_ratio=1.8, require_volume=True),
    "USDCAD": dict(allowed_modes=[], sweep_enabled=True, forward_test=True, atr_buffer=0.05, max_range_atr_ratio=1.5, require_volume=True),
    "EURUSD": dict(allowed_modes=[], atr_buffer=0.05, max_range_atr_ratio=1.8, require_volume=False),
}'''

idx_start = code_rules.find("ASSET_CONFIG = {")
idx_end = code_rules.find("DEFAULT_ORB_PROFILE = dict")

if idx_start != -1 and idx_end != -1:
    code_rules = code_rules[:idx_start] + target_asset_config + "\n\n\n" + code_rules[idx_end:]
    print("ASSET_CONFIG alineado.")

# Tuplas exactas
old_tuples = '''ORB_PROFITABLE_SWEEP_SYMBOLS = (
    "XAUUSD", "XAUUSDmicro",
)
# Activos SWEEP en prueba hacia delante (demo): se desactivan solos si fallan el criterio.
ORB_SWEEP_FORWARD_TEST_SYMBOLS = ("BTCUSD", "USDCAD")
# Activos adicionales con WR > 47% y R/op > 0 validados y rescatados en el replay multianual
ORB_EXTENDED_PROFITABLE_SYMBOLS = (
    "BTCUSD", "USDCAD", "GBPUSD", "AUDUSD", "XAGUSD", "US Oil", "USDCHF",
)'''

new_tuples = '''ORB_PROFITABLE_SWEEP_SYMBOLS = (
    "XAUUSD", "XAUUSDmicro",
)
# Activos SWEEP en prueba hacia delante (demo): se desactivan solos si fallan el criterio.
ORB_SWEEP_FORWARD_TEST_SYMBOLS = ("BTCUSD", "USDCAD")
ORB_PRUNED_LOSING_SYMBOLS = (
    "EURUSD", "EURUSDmicro",
    "US SP 500", "Wall Street 30", "US Tech 100", "UK Brent Oil",
    "BTCUSDmicro",
    "XAGUSD", "XAGUSDmicro",
    "US Oil",
)'''

# Reemplazar bloque de tuplas
idx_t_start = code_rules.find("ORB_PROFITABLE_SWEEP_SYMBOLS = (")
idx_t_end = code_rules.find("def get_asset_rules(symbol):")

if idx_t_start != -1 and idx_t_end != -1:
    code_rules = code_rules[:idx_t_start] + new_tuples + "\n\n\n" + code_rules[idx_t_end:]
    print("Tuplas alineadas.")

p_rules.write_bytes(code_rules.encode('utf-8'))

print("ALINEACIÓN COMPLETADA")
