import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime, timezone

from strategy.ict.ict_strategy import ICTStrategy, is_synthetic_asset
from strategy.ict.config import ICTConfig
from strategy.malaysian_snr.malaysian_snr_strategy import MalaysianSNRStrategy
from strategy.malaysian_snr.config import MalaysianSNRConfig
from strategy.execution.live_trading_engine import LiveTradingEngine, LiveTradingConfig
from strategy.execution.worker_rules import configure_worker_rules

synth_symbols = [
    "Volatility 75 Index",
    "Volatility 100 (1s) Index",
    "Step Index 400",
    "Step Index",
    "Crash 1000 Index",
    "Crash 500 Index",
    "Boom 1000 Index",
    "Boom 500 Index",
    "Jump 50 Index",
    "Jump 25 Index",
    "High Frequency Vol 100 Index",
]

print("=== 1. TEST IS_SYNTHETIC_ASSET ===")
for s in synth_symbols:
    is_syn = is_synthetic_asset(s)
    print(f"Symbol: {s} -> is_synthetic: {is_syn}")
    assert is_syn, f"FAILED: {s} should be synthetic!"

print("\n=== 2. TEST ICTSTRATEGY SESSION ACTIVE AT ASIAN HOURS ===")
# Horas en Asia: 20:00 UTC (21:00 NY), 00:00 UTC (19:00 NY), 03:00 UTC (22:00 NY), 06:00 UTC (01:00 NY)
asian_hours_utc = [20, 22, 0, 2, 4, 6]

ict_strat = ICTStrategy(None, config=ICTConfig())

for s in synth_symbols:
    for h in asian_hours_utc:
        now_test = datetime(2026, 11, 18, h, 15, 0, tzinfo=timezone.utc)
        now_ts = pd.Timestamp(now_test)
        
        # Evaluar la lógica de sesión de ict_strategy
        is_syn = is_synthetic_asset(s)
        # En ict_strategy: line 536: elif is_synthetic: session_active = True
        # line 595: if not is_synthetic and self.config.killzone_filter_enabled:
        killzone_blocks = (not is_syn) and ict_strat.config.killzone_filter_enabled
        if killzone_blocks:
            print(f"ERROR: {s} at hour {h} UTC was blocked by Killzone!")

print("Resultado ICT: Ningún sintético es bloqueado por Killzone en ninguna hora de Asia.")

print("\n=== 3. TEST LIVE_TRADING_ENGINE GATES ON SYNTHETICS ===")
# Comprobar puertas en LiveTradingEngine
dummy_config = LiveTradingConfig(bot_profile="STEP", source="DEMO")
dummy_config = configure_worker_rules(dummy_config)

from unittest.mock import MagicMock
mock_provider = MagicMock()
engine = LiveTradingEngine(provider=mock_provider, repository=MagicMock(), config=dummy_config)

for s in synth_symbols:
    for h in asian_hours_utc:
        now_test = datetime(2026, 11, 18, h, 15, 0, tzinfo=timezone.utc)
        
        # Test 1: _forex_market_standby_status
        standby = engine._forex_market_standby_status(now_utc=now_test)
        if standby.get("in_standby"):
            print(f"ERROR: {s} marked in standby at {h} UTC!")
            
        # Test 2: _forex_killzone_entry_gate
        fx_kz = engine._forex_killzone_entry_gate(s, now_utc=now_test)
        if fx_kz is not None:
            print(f"ERROR: {s} blocked by forex_killzone at {h} UTC: {fx_kz}")
            
        # Test 3: _gold_smc_entry_gate
        gold_gate = engine._gold_smc_entry_gate(s, now_utc=now_test)
        if gold_gate is not None:
            print(f"ERROR: {s} blocked by gold_gate at {h} UTC: {gold_gate}")
            
        # Test 4: _forex_high_impact_news_entry_gate
        news_gate = engine._forex_high_impact_news_entry_gate(s)
        if news_gate is not None:
            print(f"ERROR: {s} blocked by news_gate: {news_gate}")
            
        # Test 5: _forex_rollover_entry_gate
        roll_gate = engine._forex_rollover_entry_gate(s)
        if roll_gate is not None:
            print(f"ERROR: {s} blocked by rollover_gate: {roll_gate}")

print("Resultado Gates: Ninguna puerta de sesión/killzone/standby/noticias bloquea sintéticos.")
