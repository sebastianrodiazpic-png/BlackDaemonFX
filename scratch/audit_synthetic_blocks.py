"""Auditoría profunda de bloqueos para sintéticos bajo ICT y Malaysian SNR."""
import sys
from pathlib import Path
sys.path.insert(0, '.')

import MetaTrader5 as mt5
from config.instruments import InstrumentManager
from brokers.mt5_connector import MT5Connector
from brokers.mt5_data import MT5DataProvider
from brokers.mt5_execution import MT5ExecutionProvider
from brokers.mt5_trade_executor import MT5TradeExecutor
from strategy.execution.live_trading_engine import LiveTradingEngine, LiveTradingConfig
from strategy.execution.worker_rules import configure_worker_rules
from database.repository import TradingRepository

if not mt5.initialize():
    print("MT5 no inicializado")
    sys.exit(1)

connector = MT5Connector()
connector.connect()
provider = MT5DataProvider(connector)
manager = InstrumentManager(connector)
repo = TradingRepository()
exec_provider = MT5ExecutionProvider(connector)
executor = MT5TradeExecutor(exec_provider, magic=26082026)

synthetic_cats = ["boom", "crash", "step", "jump", "volatility"]
active_by_cat = {}
for cat in synthetic_cats:
    active_by_cat[cat] = manager.get_active_symbols(categories=[cat]) or []
    print(f"Categoria {cat.upper()}: {active_by_cat[cat]}")

print("\n" + "="*80)
print("AUDITORIA 1: SINTETICOS BAJO ICT STRATEGY (MOTOR Y GATES)")
print("="*80)

# Revisamos perfiles sintéticos principales
profiles_to_test = [
    ("BOOM", active_by_cat["boom"][:2]),
    ("CRASH", active_by_cat["crash"][:2]),
    ("STEP", active_by_cat["step"][:2]),
    ("JUMP", active_by_cat["jump"][:2]),
    ("VOLATILITY_1", active_by_cat["volatility"][:3]),
]

for profile, syms in profiles_to_test:
    print(f"\n--- Probando Worker ICT Perfil: {profile} ---")
    base_cfg = LiveTradingConfig(bot_profile=profile)
    configured_cfg = configure_worker_rules(base_cfg)
    engine = LiveTradingEngine(provider, repo, config=configured_cfg, executor=executor)
    
    for sym in syms:
        # 1. Evaluar directo la estrategia ICT
        ict_res = engine.ict_strategy.analyze_symbol(sym)
        # 2. Evaluar por el pipeline completo del engine
        engine_res = engine._process_symbol_guarded(sym, sync_before_execution=False)
        
        print(f"Simbolo: {sym}")
        print(f"  ICT Directo: valid={ict_res.get('valid')} | action={ict_res.get('action')} | reason={ict_res.get('reason')}")
        print(f"  Engine Guarded: action={engine_res.get('action')} | reason={engine_res.get('reason')}")
        
        # Simular una señal sintética válida generada por ICT para probar los GATES del engine
        dummy_signal = {
            "symbol": sym,
            "direction": "BUY" if "CRASH" not in sym.upper() else "SELL",
            "entry_price": 1000.0,
            "stop_loss": 990.0 if "CRASH" not in sym.upper() else 1010.0,
            "take_profit": 1040.0 if "CRASH" not in sym.upper() else 960.0,
            "tp1_price": 1020.0,
            "tp2_price": 1040.0,
            "risk_amount": 10.0,
            "risk_reward_ratio": 4.0,
            "risk_reward": 4.0,
            "trade_score": 90.0,
            "confirmation_percentage": 95.0,
            "adx": 25.0,
            "structure_break": "MSS_BUY" if "CRASH" not in sym.upper() else "MSS_SELL",
            "entry_time": "2026-10-10T12:00:00Z",
            "scenario": "AMD_KILLZONE_FVG_REJECTION",
            "strategy_name": "ICT_SABRI_MALLE",
            "strategy_version": "ict-sabri-malle-v1",
        }
        dummy_analysis = {
            "valid": True,
            "strategy_name": "ICT_SABRI_MALLE",
            "strategy_version": "ict-sabri-malle-v1",
            "action": "ICT_SABRI_MALLE_CONFIRMED",
            "signal": dummy_signal,
            "context_policy": "ICT_NATIVE",
        }
        
        # Test gates individuales
        bg = engine._boom_crash_quality_gate(sym, dummy_signal["direction"], dummy_signal, dummy_analysis)
        sg = engine._step_quality_gate(sym, dummy_signal, dummy_analysis)
        vg = engine._volatility_quality_gate(sym, dummy_signal, dummy_analysis)
        jg = engine._jump_quality_gate(sym, dummy_signal)
        
        print(f"  Simulacion de Gates para {sym}:")
        if bg: print(f"    [!] BOOM/CRASH GATE BLOQUEA: {bg.get('action')} - {bg.get('reason')}")
        if sg: print(f"    [!] STEP GATE BLOQUEA: {sg.get('action')} - {sg.get('reason')}")
        if vg: print(f"    [!] VOLATILITY GATE BLOQUEA: {vg.get('action')} - {vg.get('reason')}")
        if jg: print(f"    [!] JUMP GATE BLOQUEA: {jg.get('action')} - {jg.get('reason')}")
        if not (bg or sg or vg or jg):
            print(f"    [OK] Ningun quality gate especifico bloquea la señal ficticia")

print("\n" + "="*80)
print("AUDITORIA 2: SINTETICOS BAJO MALAYSIAN SNR")
print("="*80)

msnr_cfg = configure_worker_rules(LiveTradingConfig(bot_profile="MALAYSIAN_SNR"))
msnr_engine = LiveTradingEngine(provider, repo, config=msnr_cfg, executor=executor)
from app.main import BOT_PROFILES
msnr_symbols = BOT_PROFILES.get("MALAYSIAN_SNR", {}).get("symbols", [])
print(f"Simbolos configurados en BOT_PROFILES['MALAYSIAN_SNR']: {len(msnr_symbols)}")
print(f"Allowed symbols en MalaysianSNRConfig: {msnr_engine.malaysian_snr_strategy.config.allowed_symbols}")

for sym in msnr_symbols:
    if any(k in sym.lower() for k in ["boom", "crash", "step", "jump", "volatility"]):
        res = msnr_engine.malaysian_snr_strategy.analyze_symbol(sym)
        guarded = msnr_engine._process_symbol_guarded(sym, sync_before_execution=False)
        print(f"MSNR [{sym}]: analyze={res.get('action')} ({res.get('reason')}) | engine={guarded.get('action')} ({guarded.get('reason')})")

mt5.shutdown()
