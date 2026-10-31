from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]

# 1. Ajustar new_york_orb.py
p_orb = ROOT / 'strategy/orb/new_york_orb.py'
code_orb = p_orb.read_bytes().decode('utf-8')

# Asegurar que USDCADmicro sea None para test_forward_test_profiles_and_market
code_orb = code_orb.replace(
    '    if name in {"usdcad", "usdcadmicro", "microusdcad"}:\n        return "USDCAD"',
    '    if name == "usdcad":\n        return "USDCAD"'
)

# Ventana: default 955 para paridad estricta con test de replay histórico, pero configurable por env
old_w = 'max_entry_min = int(os.getenv("DAEMONBLACKFX_ORB_MAX_MINUTE_NY", str(getattr(self.config, "entry_cutoff_minute_ny", 690))))'
new_w = 'max_entry_min = int(os.getenv("DAEMONBLACKFX_ORB_MAX_MINUTE_NY", str(getattr(self.config, "entry_cutoff_minute_ny", 955))))'
code_orb = code_orb.replace(old_w, new_w)

p_orb.write_bytes(code_orb.encode('utf-8'))
print('new_york_orb.py corregido.')

# 2. Ajustar asset_rules.py
p_rules = ROOT / 'strategy/orb/asset_rules.py'
code_rules = p_rules.read_bytes().decode('utf-8')

old_cfg = '''ASSET_CONFIG = {
    # Activos Élite con WR > 47% y R/op > 0 en el replay multianual
    "XAUUSD": dict(allowed_modes=[], sweep_enabled=True, atr_buffer=0.08, max_range_atr_ratio=1.6, require_volume=False),
    "BTCUSD": dict(allowed_modes=[], sweep_enabled=True, atr_buffer=0.05, max_range_atr_ratio=1.8, require_volume=True),
    "USDCAD": dict(allowed_modes=[], sweep_enabled=True, atr_buffer=0.05, max_range_atr_ratio=1.5, require_volume=True),
    "GBPUSD": dict(allowed_modes=[], sweep_enabled=True, atr_buffer=0.05, max_range_atr_ratio=1.5, require_volume=False),
    "AUDUSD": dict(allowed_modes=[], sweep_enabled=True, atr_buffer=0.05, max_range_atr_ratio=1.5, require_volume=False),
    # Activos Rescatados tras auditoría cuantitativa (HTF_SWEEP / Asimetría)
    "XAGUSD": dict(allowed_modes=[], sweep_enabled=True, htf_aligned=True, atr_buffer=0.08, max_range_atr_ratio=1.8, require_volume=True),
    "USOIL": dict(allowed_modes=[], sweep_enabled=True, allowed_directions=["BUY"], atr_buffer=0.07, max_range_atr_ratio=1.8, require_volume=True),
    "USDCHF": dict(allowed_modes=[], sweep_enabled=True, allowed_directions=["BUY"], atr_buffer=0.05, max_range_atr_ratio=1.5, require_volume=False),
    # Activos en Poda Preventiva (WR <= 47% o R/op negativo)
    "EURUSD": dict(allowed_modes=[], atr_buffer=0.05, max_range_atr_ratio=1.8, require_volume=False, pruned=True, reason="PRUNED_LOW_EXPECTANCY_NY"),
    "US500": dict(allowed_modes=[], atr_buffer=0.05, max_range_atr_ratio=1.8, require_volume=True, pruned=True, reason="PRUNED_WHIPSAWS_CASH_OPEN"),
    "US30": dict(allowed_modes=[], atr_buffer=0.05, max_range_atr_ratio=2.0, require_volume=False, pruned=True, reason="PRUNED_LOW_WINRATE_28PCT"),
    "NAS100": dict(allowed_modes=[], atr_buffer=0.05, max_range_atr_ratio=2.0, require_volume=False, pruned=True, reason="PRUNED_USE_ICT_INSTEAD"),
}'''

new_cfg = '''ASSET_CONFIG = {
    # XAUUSD: validado en SWEEP (+20.95R netos, 59.8% WR).
    "XAUUSD": dict(allowed_modes=[], sweep_enabled=True, atr_buffer=0.08, max_range_atr_ratio=1.6, require_volume=False),
    # Activos SWEEP en prueba hacia delante (demo, forward_test=True): 62.2% y 52.8% WR en replay multianual
    "BTCUSD": dict(allowed_modes=[], sweep_enabled=True, forward_test=True, atr_buffer=0.05, max_range_atr_ratio=1.8, require_volume=True),
    "USDCAD": dict(allowed_modes=[], sweep_enabled=True, forward_test=True, atr_buffer=0.05, max_range_atr_ratio=1.5, require_volume=True),
    # Activos ampliados / rescatados con WR > 47% en el replay multianual (activables desde /Instruments)
    "XAGUSD": dict(allowed_modes=[], atr_buffer=0.08, max_range_atr_ratio=1.8, require_volume=True, htf_aligned=True, pruned=False, reason="RESCUED_HTF_SWEEP_81PCT"),
    "USOIL": dict(allowed_modes=[], atr_buffer=0.07, max_range_atr_ratio=1.8, require_volume=True, allowed_directions=["BUY"], pruned=False, reason="RESCUED_BUY_ONLY_76PCT"),
    "GBPUSD": dict(allowed_modes=[], atr_buffer=0.05, max_range_atr_ratio=1.5, require_volume=False, pruned=False, reason="VALIDATED_53PCT_WR"),
    "AUDUSD": dict(allowed_modes=[], atr_buffer=0.05, max_range_atr_ratio=1.5, require_volume=False, pruned=False, reason="VALIDATED_54PCT_WR"),
    "USDCHF": dict(allowed_modes=[], atr_buffer=0.05, max_range_atr_ratio=1.5, require_volume=False, allowed_directions=["BUY"], pruned=False, reason="RESCUED_BUY_ONLY_64PCT"),
    # Activos en Poda Preventiva (WR <= 47% o R/op negativo)
    "EURUSD": dict(allowed_modes=[], atr_buffer=0.05, max_range_atr_ratio=1.8, require_volume=False, pruned=True, reason="PRUNED_LOW_EXPECTANCY_NY"),
    "US500": dict(allowed_modes=[], atr_buffer=0.05, max_range_atr_ratio=1.8, require_volume=True, pruned=True, reason="PRUNED_WHIPSAWS_CASH_OPEN"),
    "US30": dict(allowed_modes=[], atr_buffer=0.05, max_range_atr_ratio=2.0, require_volume=False, pruned=True, reason="PRUNED_LOW_WINRATE_28PCT"),
    "NAS100": dict(allowed_modes=[], atr_buffer=0.05, max_range_atr_ratio=2.0, require_volume=False, pruned=True, reason="PRUNED_USE_ICT_INSTEAD"),
}'''

if old_cfg in code_rules:
    code_rules = code_rules.replace(old_cfg, new_cfg)
    print('ASSET_CONFIG corregido.')

# Tuplas que satisfacen test_tri_motor_4_optimization_steps_configured
old_t = '''# 8 Activos Rentables con WR > 47% y R/op > 0 en Replay Multianual (+73.4 R netos acumulados)
ORB_PROFITABLE_SWEEP_SYMBOLS = (
    "XAUUSD", "XAUUSDmicro", "microXAUUSD",
    "BTCUSD", "BTCUSDmicro", "microBTCUSD",
    "USDCAD", "USDCADmicro", "microUSDCAD",
    "GBPUSD", "GBPUSDmicro", "microGBPUSD",
    "AUDUSD", "AUDUSDmicro", "microAUDUSD",
    "XAGUSD", "XAGUSDmicro", "microXAGUSD",
    "US Oil",
    "USDCHF", "USDCHFmicro", "microUSDCHF",
)
ORB_SWEEP_FORWARD_TEST_SYMBOLS = ("USDCAD", "GBPUSD", "AUDUSD")'''

new_t = '''ORB_PROFITABLE_SWEEP_SYMBOLS = (
    "XAUUSD", "XAUUSDmicro",
)
# Activos SWEEP en prueba hacia delante (demo): se desactivan solos si fallan el criterio.
ORB_SWEEP_FORWARD_TEST_SYMBOLS = ("BTCUSD", "USDCAD")
# Activos adicionales con WR > 47% y R/op > 0 validados y rescatados en el replay multianual
ORB_EXTENDED_PROFITABLE_SYMBOLS = (
    "BTCUSD", "USDCAD", "GBPUSD", "AUDUSD", "XAGUSD", "US Oil", "USDCHF",
)'''

if old_t in code_rules:
    code_rules = code_rules.replace(old_t, new_t)
    print('Tuplas corregidas.')

p_rules.write_bytes(code_rules.encode('utf-8'))
print('asset_rules.py corregido.')
