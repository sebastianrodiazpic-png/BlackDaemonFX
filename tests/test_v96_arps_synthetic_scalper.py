from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import numpy as np
import pandas as pd

from app.main import BOT_PROFILES, FULL_MULTI_BOT_PROFILES, SYNTHETIC_SCALPER_PROFILES
from reporting.trade_report_exporter import TradeReportExporter
from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
from strategy.scalping.adaptive_regime_pullback import (
    ARPS_STRATEGY_NAME,
    ARPS_STRATEGY_VERSION,
    AdaptiveRegimePullbackStrategy,
)


def test_parallel_arps_profiles_have_unique_modes_and_magics():
    assert len(SYNTHETIC_SCALPER_PROFILES) == 6
    specs = [BOT_PROFILES[name] for name in SYNTHETIC_SCALPER_PROFILES]
    assert len({item["mode"] for item in specs}) == 6
    assert len({item["magic"] for item in specs}) == 6
    assert all(item.get("strategy") == "ARPS" for item in specs)
    all_magics = [BOT_PROFILES[name]["magic"] for name in FULL_MULTI_BOT_PROFILES]
    assert len(all_magics) == len(set(all_magics))


def test_arps_execution_key_and_risk_config_are_distinguishable():
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(source="DEMO", bot_profile="SCALP_VOLATILITY", magic=26082303)
    key = engine._execution_key(
        "Volatility 50 Index", datetime(2026, 9, 2, tzinfo=timezone.utc), "BUY", ARPS_STRATEGY_NAME
    )
    assert ":ARPS:M15:M5:M1:" in key
    assert engine.config.arps_risk_percent == 0.25
    assert engine.config.arps_break_even_trigger_rr == 0.60


def test_family_direction_policy_is_preserved():
    assert AdaptiveRegimePullbackStrategy._family_direction_allowed("Boom 500 Index", "BUY")
    assert not AdaptiveRegimePullbackStrategy._family_direction_allowed("Boom 500 Index", "SELL")
    assert AdaptiveRegimePullbackStrategy._family_direction_allowed("Crash 500 Index", "SELL")
    assert not AdaptiveRegimePullbackStrategy._family_direction_allowed("Crash 500 Index", "BUY")
    assert AdaptiveRegimePullbackStrategy._family_direction_allowed("Crash Boom Flip 500 Index", "BUY")
    assert AdaptiveRegimePullbackStrategy._family_direction_allowed("Crash Boom Flip 500 Index", "SELL")


def test_report_exposes_strategy_identifier_version_profile_and_magic(tmp_path):
    exporter = TradeReportExporter(repository=SimpleNamespace(), output_path=tmp_path / "report.xlsx")
    row = pd.Series({"status": "OPEN", "strategy_version": ARPS_STRATEGY_VERSION, "net_pnl": 0.0})
    record = exporter._report_record(row, {
        "strategy_name": ARPS_STRATEGY_NAME,
        "strategy_version": ARPS_STRATEGY_VERSION,
        "bot_profile": "SCALP_VOLATILITY",
        "daemon_magic": 26082303,
        "confirmation_decision": "ARPS_STRICT_CONFIRMED",
    })
    assert record["estrategia_id"] == ARPS_STRATEGY_NAME
    assert record["version_estrategia"] == ARPS_STRATEGY_VERSION
    assert record["perfil_bot"] == "SCALP_VOLATILITY"
    assert record["magic_estrategia"] == 26082303
    assert "ARPS Synthetic Scalper" in record["motivo_entrada_es"]


def test_adx_math_returns_finite_values_for_directional_data():
    # Smoke test del módulo sin depender de MT5.
    count = 260
    close = np.linspace(100.0, 150.0, count)
    frame = pd.DataFrame({
        "time": pd.date_range("2026-01-01", periods=count, freq="15min", tz="UTC"),
        "open": close - 0.1, "high": close + 0.3, "low": close - 0.3, "close": close,
    })
    provider = SimpleNamespace(get_candles=lambda *args, **kwargs: frame)
    strategy = AdaptiveRegimePullbackStrategy(provider)
    result = strategy.analyze_symbol("Volatility 50 Index")
    assert result["strategy_name"] == ARPS_STRATEGY_NAME
    assert result["strategy_version"] == ARPS_STRATEGY_VERSION


def test_arps_three_minute_exit_closes_when_mfe_never_expands():
    class Repo:
        def update_trade(self, *args, **kwargs):
            return True

    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig()
    engine.repository = Repo()
    engine._current_strategy_view_cache = {}
    engine._persist_audit_event = lambda *args, **kwargs: None
    trade = {
        "id": 7, "instrument": "Volatility 30 Index",
        "entry_time": datetime.now(timezone.utc) - timedelta(minutes=3, seconds=5),
        "broker_position_ticket": "123", "details": {"metadata": {}},
    }
    closed = []
    result = engine._arps_time_stop_exit(
        trade=trade,
        metadata={"strategy_name": ARPS_STRATEGY_NAME, "max_favorable_excursion_rr": 0.0525},
        current_rr=-0.10,
        close_position=lambda **kwargs: closed.append(kwargs) or {"closed": True},
    )
    assert result["closed"] is True
    assert result["reason"] == "ARPS_3M_NO_EXPANSION_EXIT"
    assert closed
