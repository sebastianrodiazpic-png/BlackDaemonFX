from datetime import datetime, timezone

import pandas as pd
import pytest

from strategy.orb.asset_rules import check_range_amplitude, audit_volume_confirmation, evaluate_retest_quality
from strategy.orb.new_york_orb import NewYorkORBStrategy, ORBConfig, classify_orb_market
from reporting.orb_metrics import summarize_orb_trades
from test_orb_new_york_strategy import FakeProvider, _session_candles


@pytest.mark.parametrize("ratio,momentum,valid", [(1.8, True, True), (1.81, False, True), (2.34, False, True), (2.35, False, False)])
def test_range_boundaries(ratio, momentum, valid):
    result = check_range_amplitude(ratio, 0, 1)
    assert result["allow_momentum"] == momentum
    assert result["isValid"] == valid


@pytest.mark.parametrize("atr", [None, 0, float("nan"), float("inf")])
def test_missing_atr_does_not_authorize(atr):
    assert not check_range_amplitude(105, 100, atr)["isValid"]


def volume_frame(current=100):
    return pd.DataFrame(dict(time=range(12), tick_volume=[100] * 10 + [current, 10000], real_volume=[0] * 12))


@pytest.mark.parametrize("mode,current,expected", [("MOMENTUM", 100, False), ("MOMENTUM", 101, True), ("RETEST", 70, True), ("RETEST", 69, False)])
def test_volume_thresholds_and_no_future_leak(mode, current, expected):
    evidence = audit_volume_confirmation(volume_frame(current), 10, mode, True)
    assert evidence["confirmed"] == expected
    assert evidence["average_volume"] == 100
    assert evidence["volume_source"] == "tick_volume"


def test_volume_real_priority_missing_neutral_and_disabled():
    frame = volume_frame(0)
    frame["real_volume"] = [50] * 10 + [60, 99999]
    assert audit_volume_confirmation(frame, 10, "MOMENTUM", True)["volume_source"] == "real_volume"
    frame[["real_volume", "tick_volume"]] = 0
    assert audit_volume_confirmation(frame, 10, "MOMENTUM", True)["confirmed"]
    assert audit_volume_confirmation(volume_frame(0), 10, "MOMENTUM", False)["confirmed"]


@pytest.mark.parametrize("index,tail,quality", [(1, .5, "HIGH_QUALITY"), (2, .5, "HIGH_QUALITY"), (3, 0, "STANDARD_QUALITY"), (1, .49, "LOW_QUALITY"), (4, 1, "LOW_QUALITY")])
def test_retest_quality(index, tail, quality):
    assert evaluate_retest_quality(index, tail) == quality


@pytest.mark.parametrize("direction", ["BUY", "SELL"])
def test_profiles_in_real_strategy(direction):
    now = datetime(2026, 8, 28, 13, 50, 1, tzinfo=timezone.utc)
    provider = FakeProvider(_session_candles(direction).iloc[:4], now)
    strategy = NewYorkORBStrategy(provider)
    assert not strategy.analyze_symbol("XAUUSD", now)["valid"]
    for symbol in ("US30", "NAS100", "BTCUSD"):
        result = strategy.analyze_symbol(symbol, now)
        assert result["valid"], result
        assert result["signal"]["orb_metrics_strategy"] == "ORB_NY_MOMENTUM"
    assert classify_orb_market("BTCUSD") == "BTCUSD"


def test_retest_metadata_and_asset_volume_bypass():
    now = datetime(2026, 8, 28, 13, 55, 1, tzinfo=timezone.utc)
    candles = _session_candles()
    candles.loc[3, "tick_volume"] = 0
    result = NewYorkORBStrategy(FakeProvider(candles, now)).analyze_symbol("XAUUSD", now)
    assert result["valid"], result
    assert result["signal"]["orb_metrics_strategy"] == "ORB_NY_RETEST"
    assert result["signal"]["retest_quality"] == "HIGH_QUALITY"
    assert result["signal"]["retest_candle_index"] == 1


def test_critical_session_stays_cancelled_after_atr_growth():
    now = datetime(2026, 8, 28, 13, 55, 1, tzinfo=timezone.utc)
    frame = FakeProvider(_session_candles(), now).get_candles("US30", "M5")
    frame.loc[:13, "high"] = 102.1
    frame.loc[:13, "low"] = 101.9
    frame.loc[18, "high"] = 200
    result = NewYorkORBStrategy(FakeProvider(frame, now)).analyze_symbol("US30", now)
    assert result["range_amplitude"]["isValid"]
    assert result["action"] == "ORB_SESSION_CANCELLED"


def test_missing_history_waits():
    now = datetime(2026, 8, 28, 13, 55, 1, tzinfo=timezone.utc)
    provider = FakeProvider(_session_candles(), now)
    provider.get_candles = lambda *a, **kw: _session_candles()
    assert NewYorkORBStrategy(provider).analyze_symbol("US30", now)["action"] == "WAITING_ORB_ATR"


def test_wide_range_disables_momentum_but_allows_retest():
    now = datetime(2026, 8, 28, 13, 55, 1, tzinfo=timezone.utc)
    config = ORBConfig()
    config.asset_profiles["US30"]["max_range_atr_ratio"] = 1.2
    result = NewYorkORBStrategy(FakeProvider(_session_candles(), now), config).analyze_symbol("US30", now)
    assert result["valid"], result
    assert result["allowed_modes"] == ["RETEST"]
    assert result["signal"]["orb_entry_mode"] == "ORB_BREAKOUT_RETEST"


@pytest.mark.parametrize("bars,valid,quality", [(2, True, "HIGH_QUALITY"), (3, True, "STANDARD_QUALITY"), (4, False, None)])
def test_retest_window_in_strategy(bars, valid, quality):
    frame = _session_candles()
    last = frame.iloc[-1].copy()
    frame = frame.iloc[:4].copy()
    for i in range(1, bars):
        frame.loc[len(frame)] = dict(time=pd.Timestamp("2026-08-28 13:45Z") + pd.Timedelta(minutes=5*i),
                                     open=106, close=106, high=106.4, low=105.8, tick_volume=100, real_volume=0)
    last["time"] = pd.Timestamp("2026-08-28 13:45Z") + pd.Timedelta(minutes=5*bars)
    frame.loc[len(frame)] = last
    now = (last["time"] + pd.Timedelta(minutes=5, seconds=1)).to_pydatetime()
    result = NewYorkORBStrategy(FakeProvider(frame, now)).analyze_symbol("US30", now)
    assert result["valid"] == valid, result
    if valid:
        assert result["signal"]["retest_quality"] == quality


def test_execution_labels_survive_lifecycle_and_repository_restart(tmp_path):
    from database.repository import TradingRepository
    from reporting.trade_reporting_service import TradeReportingConfig, TradeReportingService
    from strategy.execution.paper_trade_executor import PaperTradeExecutor
    from trade_lifecycle_manager import TradeLifecycleManager

    now = datetime(2026, 8, 28, 13, 55, 1, tzinfo=timezone.utc)
    signal = NewYorkORBStrategy(FakeProvider(_session_candles(), now)).analyze_symbol("US30", now)["signal"]
    signal["symbol"] = "US30"
    path = tmp_path / "orb.db"
    repository = TradingRepository(db_path=path)
    service = TradeReportingService(repository, TradeReportingConfig(auto_export=False))
    manager = TradeLifecycleManager(trade_executor=PaperTradeExecutor(), reporting_service=service)
    lifecycle = manager.process_signal_with_executor(signal=signal, volume=0.5)
    assert repository.orb_execution_metrics()[0]["closed"] == 0
    manager.monitor_execution(lifecycle=lifecycle, current_price=signal["stop_loss"] - 1)
    summary = TradingRepository(db_path=path).orb_execution_metrics()
    assert summary[0]["strategy"] == "ORB_NY_RETEST"
    assert summary[0]["closed"] == 1
    assert summary[0]["expectancy_net_pnl"] < 0


def test_metrics_separate_modes_sources_and_ignore_open_and_duplicates():
    def row(key, mode, pnl, status="CLOSED", source="DEMO"):
        return dict(execution_key=key, instrument="US30", source=source, broker="MT5", status=status,
                    net_pnl=pnl, details={"metadata": {"orb_entry_mode": "ORB_BREAKOUT_" + mode}})
    rows = [row("1", "RETEST", 100), row("2", "RETEST", -40), row("3", "RETEST", 500, "OPEN"),
            row("4", "MOMENTUM", -20), row("5", "RETEST", 20, source="PAPER")]
    result = summarize_orb_trades(rows + [rows[0]])
    assert len(result) == 3
    assert result[0]["expectancy_net_pnl"] == 30
    assert result[0]["closed"] == 2
    assert result[0]["executions"] == 3
    assert result[1]["expectancy_net_pnl"] == -20
