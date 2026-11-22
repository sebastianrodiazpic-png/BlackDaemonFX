from datetime import datetime, timezone
import pandas as pd
import pytest
from types import SimpleNamespace

from brokers.mt5_trade_executor import MT5TradeExecutor, TradeExecutionRequest
from strategy.orb.new_york_orb import NewYorkORBStrategy, ORBConfig
from database.repository import TradingRepository


def test_comment_preserves_runner_and_tp1_suffix():
    req_runner = TradeExecutionRequest(
        symbol="UK Brent Oil",
        timeframe="M5",
        direction="BUY",
        entry_time=datetime.now(timezone.utc),
        entry_price=95.8,
        stop_loss=95.3,
        take_profit=98.0,
        volume=1.0,
        metadata={
            "execution_key": "DEMO:UK Brent Oil:ORB:NY:M1:2026-11-09T09:25:00+00:00:BUY:RUNNER",
            "trade_leg": "RUNNER",
        },
    )
    c_runner = MT5TradeExecutor._comment_for(req_runner)
    assert len(c_runner) <= 31
    assert c_runner.endswith(":RUNNER")

    req_tp1 = TradeExecutionRequest(
        symbol="USDJPY",
        timeframe="M5",
        direction="BUY",
        entry_time=datetime.now(timezone.utc),
        entry_price=158.0,
        stop_loss=157.8,
        take_profit=158.2,
        volume=0.17,
        metadata={
            "execution_key": "DEMO:USDJPY:ORB:NY:M1:2026-11-09T08:40:00+00:00:BUY:TP1",
            "trade_leg": "TP1",
        },
    )
    c_tp1 = MT5TradeExecutor._comment_for(req_tp1)
    assert len(c_tp1) <= 31
    assert c_tp1.endswith(":TP1")


def test_orb_london_session_name():
    class DummyProvider:
        def get_current_tick(self, symbol):
            return {"bid": 95.0, "ask": 95.02, "time": "2026-11-09T08:40:00Z"}
        def get_candles(self, *args, **kwargs):
            return pd.DataFrame({
                "time": [pd.Timestamp("2026-11-09T08:30:00Z")],
                "open": [95.0], "high": [95.5], "low": [94.8], "close": [95.2], "volume": [100]
            })

    strat = NewYorkORBStrategy(DummyProvider(), ORBConfig())
    # 08:40 UTC es 03:40 NY (sesión de Londres)
    now_utc = datetime(2026, 11, 9, 8, 40, tzinfo=timezone.utc)
    now_ny, open_ny, range_end_ny, close_ny = strat._session_bounds(now_utc, "USDJPY")
    assert open_ny.hour == 3  # London open in NY timezone
    res = strat.analyze_symbol("USDJPY", now_utc=now_utc)
    assert res.get("session_name") == "LONDON"
    assert res.get("strategy_name") == "ORB_LONDON"


def test_break_even_enabled_for_orb_signals():
    from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
    from unittest.mock import MagicMock
    mock_provider = MagicMock()
    mock_executor = MagicMock()
    mock_repo = MagicMock()
    engine = LiveTradingEngine(provider=mock_provider, repository=mock_repo, executor=mock_executor, config=LiveTradingConfig(execution_enabled=False, break_even_enabled=True))
    assert engine.config.break_even_enabled is True


def test_reconcile_infers_runner_leg(tmp_path):
    db_file = tmp_path / "test.db"
    repo = TradingRepository(db_path=str(db_file))

    # Crear primero el trade hermano TP1
    tp1_payload = {
        "external_ticket": "11111",
        "execution_key": "DEMO:UK Brent Oil:ORB:NY:M1:2026-11-09T09:25:00:BUY:TP1",
        "broker_position_ticket": "11111",
        "source": "DEMO",
        "broker": "MT5",
        "instrument": "UK Brent Oil",
        "timeframe": "M5",
        "direction": "BUY",
        "status": "OPEN",
        "result": "OPEN",
        "entry_price": 95.8,
        "stop_loss": 95.3,
        "take_profit": 96.3,
        "planned_rr": 1.0,
        "details": {
            "metadata": {
                "trade_leg": "TP1",
                "strategy_name": "ORB_NEW_YORK",
                "parent_execution_key": "DEMO:UK Brent Oil:ORB:NY:M1:2026-11-09T09:25:00:BUY",
            }
        },
        "strategy_version": "orb-ny-v5-sweep",
    }
    repo.create_trade_once(tp1_payload)

    # Ahora simular posición en MT5 descubierta que solo tiene comentario genérico "BlackDaemonFx"
    # pero es del daemon (magic 26082028)
    mt5_positions = [{
        "position_ticket": 22222,
        "symbol": "UK Brent Oil",
        "direction": "BUY",
        "entry_price": 95.8,
        "stop_loss": 95.3,
        "take_profit": 98.0,
        "volume": 1.0,
        "magic": 26082028,
        "comment": "BlackDaemonFx",
        "identifier": 22222,
        "current_price": 95.8,
        "floating_profit": 0.0,
        "swap": 0.0,
    }]

    mock_executor = SimpleNamespace(
        list_open_positions=lambda: mt5_positions,
        account_info=lambda: {"equity": 5000.0},
    )

    res = repo.import_open_mt5_positions(
        mock_executor,
        source="DEMO",
        magic=26082028,
    )
    assert res["imported_daemon"] == 1
    ids = res["ids"]
    assert len(ids) == 1

    recovered_trade = repo.get_trade(ids[0])
    rec_meta = (recovered_trade.get("details") or {}).get("metadata") or {}

    # Debe inferirse como RUNNER y vincular parent_execution_key y estrategia
    assert rec_meta.get("trade_leg") == "RUNNER"
    assert rec_meta.get("execution_mode") == "SPLIT"
    assert rec_meta.get("parent_execution_key") == "DEMO:UK Brent Oil:ORB:NY:M1:2026-11-09T09:25:00:BUY"
    assert rec_meta.get("strategy_name") == "ORB_NEW_YORK"
    eng = getattr(repo, "_engine", None) or getattr(repo, "engine", None)
    if eng:
        eng.dispose()
