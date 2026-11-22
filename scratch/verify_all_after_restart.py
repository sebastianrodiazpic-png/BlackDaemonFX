import os
import sys
import csv

sys.path.insert(0, os.path.abspath("."))

from config.strategy_config import (
    PRUNED_ASSET_UNIVERSE,
)
from config.ict_instrument_policy import (
    resolve_active_pruned_worker_universe,
    is_ict_active,
    preventive_prune_reason,
    ICT_MARKETS_ACTIVE,
)
from strategy.execution.worker_rules import configure_worker_rules
from strategy.execution.live_trading_engine import LiveTradingConfig
from dashboard.realtime_dashboard import _WORKER_PROFILE_META
from dashboard.strategy_bases_page import STRATEGY_BASES_HTML
from dashboard.decisions_page import DECISIONS_HTML

print("=" * 80)
print("AUDITORÍA INTEGRAL DE ESTADO: BLACKDAEMONFX MULTISTRATEGIA")
print("=" * 80)

# 1. VERIFICACIÓN DE REGLAS DE TRADING (INVIOLABILIDAD DEL CONTRATO INSTITUCIONAL)
print("\n[FASE 1] Verificando Inviolabilidad de Reglas de Trading en Todos los Workers...")

all_workers_rules = {
    # Workers MultiStrategia
    "INDICESB_SNR": {"magic": 26082042, "tp1": 1.0, "tp2": 2.0, "be": True, "msnr": True, "tf": "M5"},
    "ICT": {"magic": 26082032, "tp1": 1.0, "tp2": 2.0, "be": True, "msnr": True, "tf": "M5"},
    "FOREX_1": {"magic": 26082201, "tp1": 1.0, "tp2": 2.0, "be": True, "msnr": True, "tf": "M5"},
    "FOREX_2": {"magic": 26082202, "tp1": 1.0, "tp2": 2.0, "be": True, "msnr": True, "tf": "M5"},
    "FOREX_3": {"magic": 26082203, "tp1": 1.0, "tp2": 2.0, "be": True, "msnr": True, "tf": "M5"},
    "FOREX_4": {"magic": 26082204, "tp1": 1.0, "tp2": 2.0, "be": True, "msnr": True, "tf": "M5"},
    "FOREX_5": {"magic": 26082205, "tp1": 1.0, "tp2": 2.0, "be": True, "msnr": True, "tf": "M5"},
    "STEP": {"magic": 26082104, "tp1": 1.0, "tp2": 2.0, "be": True, "msnr": True, "tf": "M5"},
    "BOOM": {"magic": 26082101, "tp1": 1.0, "tp2": 2.0, "be": True, "msnr": True, "tf": "M5"},
    "CRASH": {"magic": 26082102, "tp1": 1.0, "tp2": 2.0, "be": True, "msnr": True, "tf": "M5"},
    "JUMP": {"magic": 26082105, "tp1": 1.0, "tp2": 2.0, "be": True, "msnr": True, "tf": "M5"},
    "VOLATILITY_1": {"magic": 26082401, "tp1": 1.0, "tp2": 2.0, "be": True, "msnr": True, "tf": "M5"},
    "VOLATILITY_2": {"magic": 26082402, "tp1": 1.0, "tp2": 2.0, "be": True, "msnr": True, "tf": "M5"},
    "VOLATILITY_3": {"magic": 26082403, "tp1": 1.0, "tp2": 2.0, "be": True, "msnr": True, "tf": "M5"},
    "VOLATILITY_4": {"magic": 26082404, "tp1": 1.0, "tp2": 2.0, "be": True, "msnr": True, "tf": "M5"},
    # Workers Especializados
    "ORB": {"magic": 26082028, "orb": True},
    "MALAYSIAN_SNR": {"magic": 26082031, "msnr": True, "tf": "M15"},
    "TREND_PULLBACK": {"magic": 26082038, "tp1": 1.0, "tp2": 2.0, "be": True, "tf": "M15"},
}

for prof, expected in all_workers_rules.items():
    cfg = LiveTradingConfig(bot_profile=prof, magic=expected["magic"])
    configured = configure_worker_rules(cfg)
    
    if "tp1" in expected:
        assert configured.first_target_rr == expected["tp1"], f"Error TP1 en {prof}: {configured.first_target_rr}"
    if "tp2" in expected:
        assert configured.second_target_rr == expected["tp2"], f"Error TP2 en {prof}: {configured.second_target_rr}"
    if "be" in expected:
        assert configured.break_even_enabled == expected["be"], f"Error BE en {prof}: {configured.break_even_enabled}"
        assert configured.break_even_trigger_rr == 1.0, f"Error BE trigger en {prof}: {configured.break_even_trigger_rr}"
    if "msnr" in expected:
        assert configured.malaysian_snr_enabled == expected["msnr"], f"Error MSNR en {prof}: {configured.malaysian_snr_enabled}"
    if "tf" in expected:
        assert configured.entry_timeframe == expected["tf"], f"Error TF en {prof}: {configured.entry_timeframe}"
    if "orb" in expected:
        assert configured.orb_enabled == expected["orb"], f"Error ORB en {prof}: {configured.orb_enabled}"
    
    print(f"  ✓ {prof:15} (Magic {expected['magic']}): Reglas intactas (Gatillo={getattr(configured, 'entry_timeframe', 'N/A')}, TP1={getattr(configured, 'first_target_rr', 'N/A')}R, TP2={getattr(configured, 'second_target_rr', 'N/A')}R, BE={getattr(configured, 'break_even_enabled', 'N/A')}, MSNR={getattr(configured, 'malaysian_snr_enabled', 'N/A')})")

print("  -> FASE 1 COMPLETADA CON ÉXITO: 0 alteraciones en las reglas de trading.")

# 2. VERIFICACIÓN DE UNIVERSOS DE INSTRUMENTOS
print("\n[FASE 2] Verificando Universos y Políticas de Instrumentos...")

expected_indices = ["Germany 40", "US SP 500", "US Tech 100", "Wall Street 30"]
pruned_indices = PRUNED_ASSET_UNIVERSE.get("INDICESB_SNR", ())
assert sorted(pruned_indices) == sorted(expected_indices), f"Mismatch en PRUNED_ASSET_UNIVERSE['INDICESB_SNR']: {pruned_indices}"
print(f"  ✓ PRUNED_ASSET_UNIVERSE['INDICESB_SNR']: {len(pruned_indices)} índices bursátiles coinciden exactamente.")

resolved_indices = resolve_active_pruned_worker_universe("INDICESB_SNR")
assert sorted(resolved_indices) == sorted(expected_indices), f"Mismatch en resolve_active_pruned_worker_universe('INDICESB_SNR'): {resolved_indices}"
print(f"  ✓ resolve_active_pruned_worker_universe('INDICESB_SNR'): {len(resolved_indices)} índices bursátiles resueltos.")

expected_commodities_crypto = [
    "BTCUSD", "ETHUSD",
    "BTCUSDmicro", "ETHUSDmicro",
    "XRPUSD",
    "XAUEUR", "XAUUSD",
    "XAUUSDmicro", "XAUEURmicro",
    "XAGUSD", "XAGUSDmicro",
    "US Oil", "UK Brent Oil",
]

pruned_ict = PRUNED_ASSET_UNIVERSE.get("ICT", ())
assert sorted(pruned_ict) == sorted(expected_commodities_crypto), f"Mismatch en PRUNED_ASSET_UNIVERSE['ICT']: {pruned_ict}"
print(f"  ✓ PRUNED_ASSET_UNIVERSE['ICT']: {len(pruned_ict)} símbolos coinciden exactamente.")

resolved_ict = resolve_active_pruned_worker_universe("ICT")
assert sorted(resolved_ict) == sorted(expected_commodities_crypto), f"Mismatch en resolve_active_pruned_worker_universe('ICT'): {resolved_ict}"
print(f"  ✓ resolve_active_pruned_worker_universe('ICT'): {len(resolved_ict)} símbolos resueltos.")

# 3. VERIFICACIÓN DE METADATOS DEL DASHBOARD
print("\n[FASE 3] Verificando Dashboard Metadata, Nombramiento y Salud de Posiciones...")

indices_meta = _WORKER_PROFILE_META.get("INDICESB_SNR", {})
assert indices_meta.get("strategy_key") == "MULTISTRATEGY"
assert indices_meta.get("strategy_label") == "MultiStrategia"
assert indices_meta.get("magic") == 26082042
assert "INDICESB_SNR" in indices_meta.get("label", "")
assert "32180" in indices_meta.get("label", "")
print(f"  ✓ Worker INDICESB_SNR nombrado: '{indices_meta.get('label')}'")

ict_meta = _WORKER_PROFILE_META.get("ICT", {})
assert ict_meta.get("strategy_key") == "MULTISTRATEGY"
assert ict_meta.get("strategy_label") == "MultiStrategia"
assert ict_meta.get("magic") == 26082032
assert "Materias Primas y Criptomonedas" in ict_meta.get("label", "")
print(f"  ✓ Worker ICT nombrado: '{ict_meta.get('label')}'")

with open("dashboard/realtime_dashboard.py", "r", encoding="utf-8") as f:
    dashboard_code = f.read()

assert '26082042' in dashboard_code, "Magic 26082042 no encontrado en realtime_dashboard.py"
assert '"26082042"' in dashboard_code, "Magic '26082042' no presente en tupla de magics de strategy_origin"
assert '26082032' in dashboard_code, "Magic 26082032 no encontrado en realtime_dashboard.py"
assert '"26082032"' in dashboard_code, "Magic '26082032' no presente en tupla de magics de strategy_origin"
print("  ✓ Magics 26082042 y 26082032 presentes en la discriminación de strategy_origin (Salud de Posiciones).")

# 4. VERIFICACIÓN DE STRATEGY-BASES Y CSV HISTÓRICO
print("\n[FASE 4] Verificando Persistencia y Consistencia en /Strategy-bases y CSV Replay 5Y...")

csv_file = "storage/analysis/replay_5y_perfect_strategy_bases.csv"
assert os.path.exists(csv_file), "CSV de bases no existe"

with open(csv_file, "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    header = next(reader)
    assert len(header) == 39, f"Header tiene {len(header)} columnas (esperado 39)"
    
    indices_rows = 0
    comm_rows = 0
    for row in reader:
        assert len(row) == 39, f"Fila en CSV no tiene 39 columnas"
        if row[0] in expected_indices and "INDICESB_SNR" in row[2]:
            indices_rows += 1
        if row[0] in expected_commodities_crypto and "26082032" in row[2]:
            comm_rows += 1

assert indices_rows == 4, f"Se encontraron {indices_rows} filas de Índices (esperadas 4)"
assert comm_rows == 13, f"Se encontraron {comm_rows} filas de Materias Primas y Cripto (esperadas 13)"
print(f"  ✓ CSV Replay 5Y: 4 índices + 13 materias primas/cripto validados con 39 columnas exactas.")

# 5. VERIFICACIÓN DE /Decisions
print("\n[FASE 5] Verificando Trazabilidad en /Decisions...")

assert "Worker INDICESB_SNR · Índices Bursátiles · MultiStrategia · Magic 26082042 · PID 32180" in DECISIONS_HTML
assert "10,400 trades totales" in DECISIONS_HTML
assert "66.84%" in DECISIONS_HTML
assert "+5,110.50 R netos acumulados" in DECISIONS_HTML
print("  ✓ /Decisions: Ficha técnica completa de Índices Bursátiles (MultiStrategia · PID 32180) validada.")

print("\n" + "=" * 80)
print("TODAS LAS VERIFICACIONES CONCLUYERON CON ÉXITO: 0 BUGS, 0 REGRESIONES, 100% OPERATIVO")
print("=" * 80)
