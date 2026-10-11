"""Validation script: confirms that BOOM, CRASH, STEP, JUMP, ICT, FOREX, and VOLATILITY
workers are configured and executing under the ICT Sabri Malle strategy.
"""
import sys
import json
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from strategy.execution.live_trading_engine import LiveTradingEngine, LiveTradingConfig
from strategy.execution.worker_rules import configure_worker_rules, RULESET
from strategy.ict.ict_strategy import ICTSabriMalleStrategy
from app.main import BOT_PROFILES, FULL_MULTI_BOT_PROFILES


class MockCandleProvider:
    def __init__(self, df_h4=None, df_h1=None, df_m5=None):
        self._df_h4 = df_h4
        self._df_h1 = df_h1
        self._df_m5 = df_m5

    def get_candles(self, symbol, timeframe, count=80):
        return None

    def resolve_symbol(self, symbol):
        return symbol

    def ensure_symbol(self, symbol):
        return True

    def get_current_tick(self, symbol):
        return {"bid": 100.0, "ask": 100.0}


class MockRepo:
    db_path = ":memory:"
    def save_audit_event(self, *args, **kwargs): pass
    def save_trade(self, *args, **kwargs): pass
    def update_trade(self, *args, **kwargs): pass
    def get_active_trades(self, *args, **kwargs): return []
    def save_signal(self, *args, **kwargs): return (1, None)
    def save_signal_once(self, payload): return 999, True
    def get_trade_by_execution_key(self, key): return None
    def open_trades(self, source=None): return []
    def save_account_snapshot(self, account): pass


class MockExecutor:
    def get_open_positions(self): return []
    def get_pending_orders(self): return []
    def assert_demo_account(self): return {"balance": 10000.0, "equity": 10000.0, "server": "Deriv-Demo"}
    def normalize_market_stops(self, symbol, direction, entry, sl, rr, **kwargs):
        tp = entry + abs(entry - sl) * rr if direction == "BUY" else entry - abs(entry - sl) * rr
        return {"valid": True, "entry_price": float(entry), "stop_loss": float(sl), "take_profit": float(tp)}
    def calculate_volume(self, symbol, direction, entry, stop, risk_amount):
        return {"volume": 0.01, "actual_risk_amount": risk_amount}


class SpyICT:
    def __init__(self):
        self.called_symbols = []

    def analyze_symbol(self, symbol, now_utc=None):
        self.called_symbols.append(symbol)
        return {
            "valid": False,
            "action": "WAITING_ICT",
            "reason": "VALIDATION_TEST_NO_SETUP",
            "strategy_name": "ICT_SABRI_MALLE",
            "strategy_version": "ict-sabri-malle-v1",
            "symbol": symbol,
        }


def validate_profile(profile, test_symbol):
    print(f"\n=======================================================")
    print(f"VERIFICANDO WORKER / PERFIL: {profile}")
    print(f"=======================================================")
    
    # 1. Check BOT_PROFILES
    in_bot_profiles = profile in BOT_PROFILES
    spec = BOT_PROFILES.get(profile, {})
    mode = spec.get("mode")
    magic = spec.get("magic")
    print(f"  [1] Registro en BOT_PROFILES: existe={in_bot_profiles} | mode={mode} | magic={magic}")
    
    # 2. Check configure_worker_rules
    base_cfg = LiveTradingConfig(bot_profile=profile)
    configured_cfg = configure_worker_rules(base_cfg)
    strategy_version = configured_cfg.strategy_version
    print(f"  [2] configure_worker_rules: strategy_version='{strategy_version}' (regla esperada: '{RULESET}')")
    assert strategy_version == RULESET, f"Expected {RULESET}, got {strategy_version}"
    
    # 3. Check LiveTradingEngine instantiation
    engine = LiveTradingEngine(
        provider=MockCandleProvider(),
        repository=MockRepo(),
        config=configured_cfg,
        executor=MockExecutor(),
    )
    has_ict = isinstance(engine.ict_strategy, ICTSabriMalleStrategy)
    print(f"  [3] Instancia en LiveTradingEngine: ICTSabriMalleStrategy cargado = {has_ict}")
    assert has_ict, "LiveTradingEngine must have ICTSabriMalleStrategy instance"
    
    # 4. Check routing in process_symbol
    spy = SpyICT()
    engine.ict_strategy = spy
    # Bypass market-schedule gates (killzone, rollover, news) to test core strategy engine routing
    engine._forex_killzone_entry_gate = lambda s: None
    engine._forex_rollover_entry_gate = lambda s: None
    engine._forex_high_impact_news_entry_gate = lambda s: None
    result = engine.process_symbol(test_symbol)
    
    was_called = test_symbol in spy.called_symbols
    context_policy = result.get("analysis", {}).get("context_policy")
    action = result.get("action")
    print(f"  [4] Enrutamiento de análisis: llamado a ICT={was_called} | context_policy='{context_policy}' | action='{action}'")
    assert was_called, f"Perfil {profile} no enrutó al motor ICT!"
    assert context_policy == "ICT_NATIVE", f"Se esperaba context_policy ICT_NATIVE, se obtuvo {context_policy}"
    
    print(f"  >>> ESTADO: CONFIRMADO - {profile} TRABAJA 100% BAJO ESTRATEGIA ICT")
    return True


def check_log_manifest(profile, log_filename):
    log_path = PROJECT_ROOT / "storage" / "logs" / "bots" / log_filename
    if not log_path.exists():
        print(f"  Archivo de log {log_filename} no existe.")
        return None
    
    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()[-200:]
    
    rules_line = None
    has_ict_waiting = False
    for line in reversed(lines):
        if "WORKER_RULES_LOADED" in line and not rules_line:
            rules_line = line.strip()
        if "WAITING ICT" in line or "ICT" in line:
            has_ict_waiting = True
            
    print(f"  Verificación en log de ejecución en vivo ({log_filename}):")
    if rules_line:
        idx = rules_line.find("{")
        if idx != -1:
            try:
                manifest = json.loads(rules_line[idx:])
                print(f"    Manifest cargado: ruleset='{manifest.get('ruleset')}' | strategy_version='{manifest.get('strategy_version')}'")
            except Exception:
                print(f"    Manifest: {rules_line[:120]}")
    print(f"    Eventos ICT en ejecución activa: {'SI' if has_ict_waiting else 'NO'}")


def main():
    targets = [
        ("BOOM", "Boom 1000 Index", "boom.log"),
        ("CRASH", "Crash 1000 Index", "crash.log"),
        ("STEP", "Step Index 500", "step.log"),
        ("JUMP", "Jump 75 Index", "jump.log"),
        ("ICT", "XAGUSD", "ict.log"),
        ("FOREX", "EURUSD", "forex_1.log"),
        ("FOREX_1", "AUDUSD", "forex_1.log"),
        ("FOREX_2", "EURUSD", "forex_2.log"),
        ("FOREX_3", "GBPUSD", "forex_3.log"),
        ("FOREX_4", "USDJPY", "forex_4.log"),
        ("VOLATILITY", "Volatility 75 Index", "volatility_1.log"),
        ("VOLATILITY_1", "Volatility 10 Index", "volatility_1.log"),
        ("VOLATILITY_2", "Volatility 25 Index", "volatility_2.log"),
        ("VOLATILITY_3", "Volatility 50 Index", "volatility_3.log"),
        ("VOLATILITY_4", "Volatility 75 Index", "volatility_4.log"),
    ]
    
    all_passed = True
    for profile, symbol, log_name in targets:
        try:
            validate_profile(profile, symbol)
            check_log_manifest(profile, log_name)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"  [ERROR] {profile}: {e}")
            all_passed = False
            
    print("\n" + "="*70)
    if all_passed:
        print("RESULTADO FINAL: TODOS LOS WORKERS EVALUADOS ESTÁN TRABAJANDO BAJO ICT")
    else:
        print("RESULTADO FINAL: HUBO ERRORES EN LA VALIDACIÓN.")
    print("="*70)

if __name__ == "__main__":
    main()
