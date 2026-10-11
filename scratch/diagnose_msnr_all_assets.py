import sys
import os
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, '.')

from app.main import BOT_PROFILES
from strategy.malaysian_snr.config import MalaysianSNRConfig
from strategy.malaysian_snr.malaysian_snr_strategy import MalaysianSNRStrategy, is_synthetic_symbol
from config.symbol_policy import is_direction_allowed, get_symbol_direction_policy
from strategy.execution.worker_rules import configure_worker_rules
from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
from database.repository import TradingRepository

print("="*90)
print("DIAGNÓSTICO INTEGRAL DE BLOQUEOS EN ACTIVOS DISPONIBLES DEL WORK DE MALAYSIAN SNR")
print("="*90)

msnr_spec = BOT_PROFILES.get("MALAYSIAN_SNR", {})
active_symbols = msnr_spec.get("symbols", [])
pruned_symbols = msnr_spec.get("pruned_symbols", [])

print(f"Total activos configurados en el perfil MALAYSIAN_SNR: {len(active_symbols)}")
print(f"Activos podados configurados: {len(pruned_symbols)}")

config = MalaysianSNRConfig()
allowed = set(a.strip().lower() for a in config.allowed_symbols)

now_utc = datetime.now(timezone.utc)
print(f"Hora actual UTC para test de sesión: {now_utc.strftime('%Y-%m-%d %H:%M:%S UTC')} (Día: {now_utc.strftime('%A')})")

print("\n" + "-"*90)
print(f"{'SÍMBOLO':<25} | {'ALLOWLIST':<12} | {'TIPO':<10} | {'DIRECCIÓN':<15} | {'KILLZONE / SESIÓN':<20}")
print("-"*90)

blocked_allowlist = []
blocked_session = []

for sym in active_symbols:
    norm = sym.strip().lower().removesuffix("micro")
    in_allow = norm in allowed
    is_synth = is_synthetic_symbol(sym)
    
    # Dirección
    pol = get_symbol_direction_policy(sym)
    dir_str = pol.allowed_direction or "BIDIRECCIONAL"
    
    # Killzone
    hour = now_utc.hour + now_utc.minute / 60.0 + now_utc.second / 3600.0
    in_kz = (7 <= hour < 11 or 12.5 <= hour < 17)
    
    if not in_allow:
        blocked_allowlist.append(sym)
        allow_str = "BLOQUEADO"
    else:
        allow_str = "PERMITIDO"
        
    if not is_synth and not in_kz:
        blocked_session.append(sym)
        kz_str = f"FUERA_KZ ({hour:.1f}h)"
    else:
        kz_str = "OK (24/7)" if is_synth else "EN_KZ"
        
    print(f"{sym:<25} | {allow_str:<12} | {'SYNTH' if is_synth else 'MKT':<10} | {dir_str:<15} | {kz_str:<20}")

print("\n" + "="*90)
print("RESUMEN DE BLOQUEOS IDENTIFICADOS:")
print("="*90)

print(f"\n1. BLOQUEO POR ALLOWLIST (SYMBOL_NOT_IN_MSNR_ALLOWLIST):")
if blocked_allowlist:
    print(f"   [ALERTA CRÍTICA] {len(blocked_allowlist)} activos activos del worker están bloqueados en MalaysianSNRConfig.allowed_symbols:")
    for s in blocked_allowlist:
        print(f"     - {s}")
else:
    print("   [OK] Todos los activos activos están incluidos en la allowlist.")

print(f"\n2. BLOQUEO POR HORARIO / SESIÓN (SESSION_FILTER_OUTSIDE_KILLZONE):")
if blocked_session:
    print(f"   [INFO SESIÓN] {len(blocked_session)} activos no sintéticos están fuera de Killzones bancarias a esta hora:")
    for s in blocked_session:
        print(f"     - {s} (Solo opera Londres 07-11 UTC y NY 12:30-17 UTC)")
else:
    print("   [OK] Todos los activos están dentro de horario de sesión.")

print(f"\n3. POLÍTICA ASIMÉTRICA DE BOOM Y CRASH (SymbolDirectionPolicy):")
for s in active_symbols:
    if "boom" in s.lower():
        print(f"   - {s}: Solo COMPRAS (BUY) permitidas por protección de spike.")
    elif "crash" in s.lower():
        print(f"   - {s}: Solo VENTAS (SELL) permitidas por protección de spike.")
