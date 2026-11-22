import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from datetime import datetime

from database.repository import TradingRepository
from config.strategy_config import PRUNED_ASSET_UNIVERSE
from config.ict_instrument_policy import resolve_active_pruned_worker_universe
from strategy.execution.worker_rules import configure_worker_rules
from strategy.execution.live_trading_engine import LiveTradingConfig
from dashboard.realtime_dashboard import _WORKER_PROFILE_META

print("=== 1. VERIFICANDO TRADING REPOSITORY Y BASE DE DATOS ACTIVA ===")
repo = TradingRepository()
print(f"Ruta de base de datos activa: {repo.db_path}")

# Verificar últimos eventos de auditoría del daemon
try:
    recent_events = repo.get_recent_audit_events(limit=10)
    print(f"Eventos de auditoría recientes ({len(recent_events)}):")
    for ev in recent_events[:5]:
        print(f"  [{ev.get('timestamp') or ev.get('created_at')}] {ev.get('event_type')} | {ev.get('action')}")
except Exception as e:
    print(f"Error consultando audit_events: {e}")

# Verificar estados de runtime de los workers
try:
    worker_states = repo.get_all_worker_runtime_states()
    print(f"\nEstados de runtime de workers registrados ({len(worker_states)}):")
    for ws in worker_states:
        prof = ws.get("bot_profile") or ws.get("profile")
        magic = ws.get("magic")
        state = ws.get("state")
        cycle = ws.get("cycle_count")
        updated = ws.get("updated_at")
        active_syms = ws.get("active_symbols") or []
        print(f"  Worker {prof} (Magic {magic}): state={state}, cycle={cycle}, syms={len(active_syms)}, updated={updated}")
except Exception as e:
    print(f"Error consultando worker_runtime_states: {e}")

# Verificar posiciones abiertas en la BD
try:
    open_positions = repo.get_open_trades()
    print(f"\nPosiciones abiertas en DB ({len(open_positions)}):")
    for p in open_positions:
        print(f"  Ticket {p.get('ticket')} | {p.get('symbol')} {p.get('trade_type')} | Magic {p.get('magic')} | Entry {p.get('entry_price')} | SL {p.get('stop_loss')} | TP {p.get('take_profit')}")
except Exception as e:
    print(f"Error consultando open_trades: {e}")

print("\n=== 2. VERIFICANDO REGLAS DE TRADING (INTEGRIDAD DE REGLAS) ===")
# Validar reglas de VOLATILITY_1, VOLATILITY_3, VOLATILITY_4, BOOM, CRASH, STEP, JUMP
profiles_to_test = [
    ("VOLATILITY_1", 26082401, 5),
    ("VOLATILITY_3", 26082403, 8),
    ("VOLATILITY_4", 26082404, 11),
    ("STEP", 26082104, 5),
    ("BOOM", 26082101, 7),
    ("CRASH", 26082102, 8),
    ("JUMP", 26082105, 5),
]

all_rules_ok = True
for prof, magic, exp_sym_count in profiles_to_test:
    cfg = LiveTradingConfig(bot_profile=prof, magic=magic, execution_enabled=False)
    rules = configure_worker_rules(cfg)
    
    # 1. Contrato 1.0R / 2.0R
    tp1 = getattr(rules, "first_target_rr", None)
    tp2 = getattr(rules, "second_target_rr", None)
    be = getattr(rules, "break_even_enabled", None)
    tf = getattr(rules, "entry_timeframe", None)
    msnr = getattr(rules, "malaysian_snr_enabled", None)
    
    # 2. Universo
    univ = resolve_active_pruned_worker_universe(prof)
    
    # 3. Metadata dashboard
    meta = _WORKER_PROFILE_META.get(prof, {})
    strat_key = meta.get("strategy_key")
    strat_label = meta.get("strategy_label")
    
    tp1_ok = (tp1 == 1.0)
    tp2_ok = (tp2 == 2.0)
    be_ok = (be is True)
    tf_ok = (tf == "M5")
    msnr_ok = (msnr is True)
    count_ok = (len(univ) == exp_sym_count)
    strat_ok = (strat_key == "MULTISTRATEGY" and strat_label == "MultiStrategia")
    
    status = "OK" if (tp1_ok and tp2_ok and be_ok and tf_ok and msnr_ok and count_ok and strat_ok) else "FALLO"
    if status == "FALLO":
        all_rules_ok = False
        
    print(f"[{status}] {prof} (Magic {magic}):")
    print(f"     TP1={tp1}R (exp 1.0R), TP2={tp2}R (exp 2.0R), BE={be}, TF={tf}, MSNR={msnr}")
    print(f"     Símbolos resueltos={len(univ)} (exp {exp_sym_count}), Estrategia={strat_label} ({strat_key})")

print(f"\nResultado global de reglas de trades: {'TODAS LAS REGLAS ÍNTEGRAS Y CORRECTAS' if all_rules_ok else 'HAY DESVIACIONES EN LAS REGLAS'}")
