from pathlib import Path
from strategy.execution.live_trading_engine import LiveTradingEngine

def test_orb_current_view_normalizes_waiting_state():
    analysis={
        "valid":False,
        "strategy_name":"ORB_NEW_YORK",
        "action":"WAITING_M5_BREAKOUT_RETEST",
        "reason":"ESPERANDO_SECUENCIA_M5_BREAKOUT_MAS_RETEST",
        "orb_market":"GOLD",
    }
    view=LiveTradingEngine._current_strategy_view_from_analysis(analysis)
    assert view["decision"]=="WAITING_M5_BREAKOUT_RETEST"
    assert view["reason"]=="ESPERANDO_SECUENCIA_M5_BREAKOUT_MAS_RETEST"

def test_refresh_routes_open_orb_trade_to_orb_analyzer():
    root=Path(__file__).resolve().parents[1]
    text=(root/"strategy"/"execution"/"live_trading_engine.py").read_text(encoding="utf-8")
    assert 'if strategy_name == "ORB_NEW_YORK":' in text
    assert "analysis = self.orb_strategy.analyze_symbol(symbol)" in text
    assert 'view["opening_range_midpoint"] = analysis.get("opening_range_midpoint")' in text
    assert "for trade in auditable_trades:" in text

def test_orb_is_no_longer_skipped_from_current_audit():
    root=Path(__file__).resolve().parents[1]
    text=(root/"strategy"/"execution"/"live_trading_engine.py").read_text(encoding="utf-8")
    skipped = 'if strategy_name == "ORB_NEW_YORK":' + chr(10) + '                continue'
    assert skipped not in text
