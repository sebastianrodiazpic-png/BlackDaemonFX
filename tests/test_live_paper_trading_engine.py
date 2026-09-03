import pandas as pd

from strategy.execution.live_paper_trading_engine import (
    LivePaperTradingConfig,
    LivePaperTradingEngine,
)
from strategy.execution.paper_trade_executor import PaperTradeExecutor
from trade_lifecycle_manager import STATE_BREAK_EVEN, STATE_EXECUTION, STATE_WIN, TradeLifecycleManager


class FakeProvider:
    def __init__(self, ticks=None):
        self.ticks = list(ticks or [])
        self.calls = []

    def get_current_tick(self, symbol):
        self.calls.append(symbol)
        if not self.ticks:
            return {"symbol": symbol, "time": pd.Timestamp("2026-08-26T00:00:00Z"), "bid": 111.0, "ask": 111.0}
        item = self.ticks.pop(0)
        return {"symbol": symbol, "time": item.get("time", pd.Timestamp("2026-08-26T00:00:00Z")), "bid": item["bid"], "ask": item["ask"]}


class FakeAnalyzer:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def analyze_symbol(self, symbol):
        self.calls.append(symbol)
        if self.responses:
            return dict(self.responses.pop(0))
        return {"symbol": symbol, "valid": False, "state": "NO_SIGNAL", "action": "NO_SIGNAL"}


def ready_signal(symbol="TEST_SYMBOL", direction="BUY"):
    if direction == "SELL":
        return {
            "action": "MULTI_TIMEFRAME_SIGNAL", "valid": True, "state": "READY_TO_ENTER",
            "symbol": symbol, "m5_timeframe": "M5", "direction": "SELL",
            "entry_time": pd.Timestamp("2026-08-26 10:00:00+00:00"), "entry_price": 111.0,
            "stop_loss": 113.0, "take_profit": 107.0, "risk_reward_ratio": 2.0,
        }
    return {
        "action": "MULTI_TIMEFRAME_SIGNAL", "valid": True, "state": "READY_TO_ENTER",
        "symbol": symbol, "m5_timeframe": "M5", "direction": "BUY",
        "entry_time": pd.Timestamp("2026-08-26 10:00:00+00:00"), "entry_price": 111.0,
        "stop_loss": 109.0, "take_profit": 115.0, "risk_reward_ratio": 2.0,
    }


def build_engine(provider, analyzer, **config):
    executor = PaperTradeExecutor()
    manager = TradeLifecycleManager(trade_executor=executor)
    engine = LivePaperTradingEngine(
        provider, analyzer, manager, LivePaperTradingConfig(**config)
    )
    return engine, manager


def test_live_paper_opens_from_ready_signal():
    print("\nTEST 1 - PRECIO REAL -> ANALISIS -> PAPER EXECUTION")
    engine, manager = build_engine(FakeProvider(), FakeAnalyzer([ready_signal()]))
    result = engine.run_once(["TEST_SYMBOL"])
    row = result["signals"][0]
    assert row["action"] == "PAPER_EXECUTED"
    assert row["lifecycle"].state == STATE_EXECUTION
    assert row["position_ticket"] == "PAPER-000001"
    assert len(manager.get_active_lifecycles()) == 1
    print("PAPER EXECUTION: OK")


def test_live_paper_monitor_uses_bid_for_buy_and_activates_break_even():
    print("\nTEST 2 - TICK REAL -> BUY BID -> BREAK EVEN")
    provider = FakeProvider([{"bid": 113.0, "ask": 113.2}])
    engine, manager = build_engine(provider, FakeAnalyzer([]))
    lifecycle = manager.process_signal_with_executor(ready_signal())
    results = engine.monitor_active_positions()
    assert results[0]["market_price"] == 113.0
    assert results[0]["action"] == "break_even_activated"
    assert lifecycle.stop_loss == 111.0
    assert lifecycle.state == STATE_EXECUTION
    print("BREAK EVEN: OK")


def test_live_paper_take_profit_moves_lifecycle_to_win():
    print("\nTEST 3 - TICK REAL -> TAKE PROFIT -> WIN")
    provider = FakeProvider([{"bid": 115.0, "ask": 115.2}])
    engine, manager = build_engine(provider, FakeAnalyzer([]))
    lifecycle = manager.process_signal_with_executor(ready_signal())
    result = engine.monitor_active_positions()[0]
    assert result["closed"] is True
    assert lifecycle.state == STATE_WIN
    assert lifecycle in manager.get_completed_trades()
    print("WIN: OK")


def test_same_ready_signal_is_not_executed_twice():
    print("\nTEST 4 - NO DUPLICAR MISMA SEÑAL LIVE")
    signal = ready_signal()
    engine, manager = build_engine(FakeProvider(), FakeAnalyzer([signal, signal]))
    first = engine.run_once(["TEST_SYMBOL"])
    second = engine.run_once(["TEST_SYMBOL"])
    assert first["signals"][0]["action"] == "PAPER_EXECUTED"
    assert second["signals"][0]["action"] == "DUPLICATE_SIGNAL_SKIPPED"
    assert len(manager.get_active_lifecycles()) == 1
    print("DUPLICADO BLOQUEADO: OK")


def test_live_paper_uses_ask_for_sell_monitoring():
    print("\nTEST 5 - SELL MONITOREA CON ASK")
    provider = FakeProvider([{"bid": 108.8, "ask": 109.0}])
    engine, manager = build_engine(provider, FakeAnalyzer([]))
    lifecycle = manager.process_signal_with_executor(ready_signal(direction="SELL"))
    result = engine.monitor_active_positions()[0]
    assert result["market_price"] == 109.0
    assert lifecycle.state == STATE_EXECUTION
    print("ASK PARA SELL: OK")
