import sys
sys.path.insert(0, '.')
import os
import sqlite3
import json
from datetime import datetime, timezone

from config.strategy_config import PRUNED_ASSET_UNIVERSE
from config.ict_instrument_policy import POLICY_SELECTION_PROFILES, ict_active_symbols, sanitize_ict_selection
from database.repository import TradingRepository
from strategy.execution.live_trading_engine import LiveTradingEngine, LiveTradingConfig

repo = TradingRepository(db_path='storage/trading_bot.db')

print("=== 1. DAILY PROFIT TARGET PREFERENCES ===")
try:
    conn = sqlite3.connect('storage/trading_bot.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM daily_profit_target_preferences")
    rows = cur.fetchall()
    print("Daily profit target preferences rows:", rows)
    conn.close()
except Exception as e:
    print("Error:", e)

print("\n=== 2. DISABLED WORKERS IN ENV ===")
disabled = os.getenv("DAEMONBLACKFX_DISABLED_WORKERS", "FOREX_2,FOREX_3,FOREX_4,VOLATILITY_2,VOLATILITY_3,VOLATILITY_4,GOLD,IDX_OPEN")
print("DAEMONBLACKFX_DISABLED_WORKERS:", disabled)

print("\n=== 3. SYMBOL SELECTION BY PROFILE IN DB ===")
for prof in ['SYNTHETICS', 'VOLATILITY_1', 'BOOM', 'CRASH', 'STEP', 'JUMP', 'FOREX_1', 'MALAYSIAN_SNR', 'ICT', 'ORB']:
    try:
        pref = repo.latest_instrument_selection_profile(profile=prof, source='DEMO')
        if pref:
            syms = pref.get('selected_symbols', [])
            print(f"  Profile {prof} (DEMO): {len(syms)} symbols: {syms[:5]}...")
        else:
            print(f"  Profile {prof} (DEMO): None (no custom prefs)")
    except Exception as e:
        print(f"  Profile {prof}: {e}")

print("\n=== 4. TESTING LIVE TRADING ENGINE GATES (OFFLINE/LOCAL CHECK) ===")
# Let's check the gates for a sample of symbols across synthetic, forex, and real markets
symbols_to_test = [
    ("VOLATILITY_1", "Volatility 10 Index"),
    ("VOLATILITY_1", "Volatility 75 Index"),
    ("STEP", "Step Index 200"),
    ("BOOM", "Boom 500 Index"),
    ("JUMP", "Jump 25 Index"),
    ("FOREX_1", "GBPUSD"),
    ("MALAYSIAN_SNR", "Volatility 25 Index"),
    ("ICT", "US Tech 100"),
    ("ICT", "US Oil")
]

class MockConnector:
    pass

class MockProvider:
    connector = MockConnector()
    def resolve_symbol(self, s): return s
    def ensure_symbol(self, s): return s
    def get_symbol_info(self, s): return None

for bot_prof, sym in symbols_to_test:
    config = LiveTradingConfig(bot_profile=bot_prof, execution_enabled=False)
    engine = LiveTradingEngine(provider=MockProvider(), repository=repo, config=config)
    
    # Check individual gates
    pos_gate = engine._active_position_gate(sym)
    gold_gate = engine._gold_smc_entry_gate(sym)
    fkz_gate = engine._forex_killzone_entry_gate(sym)
    froll_gate = engine._forex_rollover_entry_gate(sym)
    news_gate = engine._forex_high_impact_news_entry_gate(sym)
    reg_gate = engine._market_regime_entry_gate(sym)
    cd_gate = engine._symbol_loss_cooldown_gate(sym)
    quar = engine._quarantine_result(sym)
    
    blocked_by = []
    if pos_gate: blocked_by.append(f"active_position: {pos_gate.get('reason')}")
    if gold_gate: blocked_by.append(f"gold_gate: {gold_gate.get('reason')}")
    if fkz_gate: blocked_by.append(f"forex_killzone: {fkz_gate.get('reason')}")
    if froll_gate: blocked_by.append(f"forex_rollover: {froll_gate.get('reason')}")
    if news_gate: blocked_by.append(f"forex_news: {news_gate.get('reason')}")
    if reg_gate: blocked_by.append(f"market_regime: {reg_gate.get('reason')}")
    if cd_gate: blocked_by.append(f"loss_cooldown: {cd_gate.get('reason')}")
    if quar: blocked_by.append(f"quarantine: {quar}")
    
    print(f"[{bot_prof}] {sym}: Gates: {'BLOCKED by ' + '; '.join(blocked_by) if blocked_by else 'CLEAR'}")
