"""Unit tests for ICT Sabri Malle strategy and full engine replacement of SMC."""
import math
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace
import pandas as pd
import pytest

from strategy.ict.config import ICTSabriMalleConfig
from strategy.ict.ict_strategy import ICTSabriMalleStrategy
from strategy.execution.worker_rules import configure_worker_rules, RULESET
from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine


class MockCandleProvider:
    def __init__(self, df_h4=None, df_h1=None, df_m5=None):
        self._df_h4 = df_h4
        self._df_h1 = df_h1
        self._df_m5 = df_m5

    def get_candles(self, symbol, timeframe, count=80):
        if timeframe == "H4":
            return self._df_h4
        elif timeframe == "H1":
            return self._df_h1
        elif timeframe == "M5":
            return self._df_m5
        return None

    def resolve_symbol(self, symbol):
        return symbol

    def ensure_symbol(self, symbol):
        return True

    def get_current_tick(self, symbol):
        return {"bid": 100.0, "ask": 100.0}


class MockRepo:
    def save_signal_once(self, payload):
        return 999, True

    def get_trade_by_execution_key(self, key):
        return None

    def open_trades(self, source=None):
        return []

    def save_account_snapshot(self, account):
        pass


class MockExecutor:
    def get_open_positions(self):
        return []

    def get_pending_orders(self):
        return []

    def assert_demo_account(self):
        return {"balance": 10000.0, "equity": 10000.0, "server": "Deriv-Demo"}

    def normalize_market_stops(self, symbol, direction, entry, sl, rr, **kwargs):
        tp = entry + abs(entry - sl) * rr if direction == "BUY" else entry - abs(entry - sl) * rr
        return {
            "valid": True,
            "entry_price": float(entry),
            "stop_loss": float(sl),
            "take_profit": float(tp),
            "constraints": {"digits": 2},
        }

    def calculate_volume(self, symbol, direction, entry, stop, risk_amount):
        return {"volume": risk_amount / 100.0, "actual_risk_amount": risk_amount}


def test_ict_config_defaults():
    config = ICTSabriMalleConfig()
    assert config.strategy_name == "ICT_SABRI_MALLE"
    assert config.strategy_version == "ict-sabri-malle-v1"
    assert config.tp1_rr == 2.0
    assert config.runner_rr == 4.0
    assert config.be_trigger_rr == 2.0
    assert config.leg1_risk_ratio == 0.5
    assert config.leg2_risk_ratio == 0.5
    assert config.range_lookback == 24


def test_worker_rules_ict_ruleset():
    assert RULESET == "ict-sabri-malle-v1"
    for profile in ["VOLATILITY_1", "STEP", "JUMP", "FOREX_1", "ICT"]:
        cfg = configure_worker_rules(LiveTradingConfig(bot_profile=profile))
        assert cfg.strategy_version == "ict-sabri-malle-v1"
        assert cfg.first_target_rr == 2.0
        assert cfg.second_target_rr == 4.0
        assert cfg.break_even_trigger_rr == 2.0
        assert cfg.min_rr == 2.0


def test_ict_strategy_insufficient_candles():
    provider = MockCandleProvider(df_h1=pd.DataFrame({"time": [datetime.now(timezone.utc)], "close": [100.0]}))
    strategy = ICTSabriMalleStrategy(data_provider=provider)
    result = strategy.analyze_symbol("EURUSD")
    assert result["valid"] is False
    assert "INSUFFICIENT" in result["reason"]


def test_ict_live_engine_dual_leg_execution():
    """Verify LiveTradingEngine plans 2 asymmetric legs for ICT (TP1 2.0 RR, Runner 4.0 RR) at 0.5% risk each."""
    engine = LiveTradingEngine(
        provider=MockCandleProvider(),
        repository=MockRepo(),
        config=LiveTradingConfig(
            execution_enabled=False,
            validate_order_in_dry_run=False,
            max_entry_drift_r=None,
            risk_percent=1.0,
            bot_profile="ICT",
            split_entries_enabled=True,
            split_entry_risk_fraction=0.50,
            meta_labeling_mode="SHADOW",
        ),
        executor=MockExecutor(),
    )

    class MockICTStrategy:
        def analyze_symbol(self, symbol, now_utc=None):
            return {
                "valid": True,
                "strategy_name": "ICT_SABRI_MALLE",
                "strategy_version": "ict-sabri-malle-v1",
                "action": "ICT_SABRI_MALLE_CONFIRMED",
                "symbol": symbol,
                "signal": {
                    "direction": "BUY",
                    "entry_price": 100.0,
                    "stop_loss": 90.0,
                    "tp1_price": 120.0,
                    "runner_price": 140.0,
                    "tp1_rr": 2.0,
                    "runner_rr": 4.0,
                    "risk_reward_ratio": 2.0,
                    "entry_time": "2026-10-08T12:00:00+00:00",
                    "strategy_name": "ICT_SABRI_MALLE",
                    "strategy_version": "ict-sabri-malle-v1",
                    "timeframe": "M5",
                    "split_execution": True,
                    "leg1_risk_ratio": 0.5,
                    "leg2_risk_ratio": 0.5,
                },
            }

    engine.ict_strategy = MockICTStrategy()
    engine._smc_entry_preflight = lambda *args: {"valid": True}

    result = engine.process_symbol("XAGUSD")
    assert result["action"] == "DRY_RUN_VALIDATED"
    assert result["actual_risk_percent"] == 1.0
    assert len(result["legs"]) == 2

    tp1, runner = result["legs"]
    assert tp1["name"] == "TP1"
    assert tp1["risk_percent"] == 0.5
    assert tp1["target_rr"] == 2.0
    assert tp1["take_profit"] == 120.0

    assert runner["name"] == "RUNNER"
    assert runner["risk_percent"] == 0.5
    assert runner["target_rr"] == 4.0
    assert runner["take_profit"] == 140.0


def test_ict_and_malaysian_snr_strict_independence():
    """Verify complete independence and isolation between ICT and Malaysian SnR strategies."""
    # 1. Configuración de Worker Rules
    msnr_cfg = configure_worker_rules(LiveTradingConfig(bot_profile="MALAYSIAN_SNR"))
    ict_cfg = configure_worker_rules(LiveTradingConfig(bot_profile="ICT"))

    # Malaysian SnR preserva sus reglas nativas
    assert msnr_cfg.malaysian_snr_enabled is True
    assert msnr_cfg.first_target_rr in (1.0, 2.0)
    assert msnr_cfg.second_target_rr in (2.0, 4.0)
    assert msnr_cfg.malaysian_snr_tp1_rr in (1.0, 2.0)
    assert msnr_cfg.malaysian_snr_runner_rr in (2.0, 4.0)
    assert msnr_cfg.break_even_trigger_rr in (1.0, 2.0)
    assert msnr_cfg.min_rr in (1.0, 2.0)

    # ICT tiene sus reglas exclusivas (1:2.0 TP1, 1:4.0 Runner, BE 2.0, orb_enabled=False)
    assert ict_cfg.malaysian_snr_enabled is False
    assert ict_cfg.first_target_rr == 2.0
    assert ict_cfg.second_target_rr == 4.0
    assert ict_cfg.break_even_trigger_rr == 2.0
    assert ict_cfg.min_rr == 2.0
    assert ict_cfg.strategy_version == "ict-sabri-malle-v1"
    assert ict_cfg.orb_enabled is False

    # 2. Aislamiento de Routing en LiveTradingEngine
    called_msnr = False
    called_ict = False

    class SpyMSNR:
        def analyze_symbol(self, symbol, now_utc=None):
            nonlocal called_msnr
            called_msnr = True
            return {"valid": False, "action": "WAITING_MALAYSIAN_SNR", "reason": "TEST"}

    class SpyICT:
        def analyze_symbol(self, symbol, now_utc=None):
            nonlocal called_ict
            called_ict = True
            return {"valid": False, "action": "WAITING_ICT", "reason": "TEST"}

    # Worker Malaysian SNR NUNCA invoca el motor ICT
    engine_msnr = LiveTradingEngine(
        provider=MockCandleProvider(),
        repository=MockRepo(),
        config=msnr_cfg,
        executor=MockExecutor(),
    )
    engine_msnr.malaysian_snr_strategy = SpyMSNR()
    engine_msnr.ict_strategy = SpyICT()

    res_msnr = engine_msnr.process_symbol("Volatility 75 Index")
    assert called_msnr is True
    assert called_ict is False
    assert res_msnr["analysis"]["context_policy"] == "MALAYSIAN_SNR_NATIVE"

    # Worker ICT NUNCA invoca el motor Malaysian SNR
    called_msnr = False
    called_ict = False

    engine_ict = LiveTradingEngine(
        provider=MockCandleProvider(),
        repository=MockRepo(),
        config=ict_cfg,
        executor=MockExecutor(),
    )
    engine_ict.malaysian_snr_strategy = SpyMSNR()
    engine_ict.ict_strategy = SpyICT()

    res_ict = engine_ict.process_symbol("XAGUSD")
    assert called_msnr is False
    assert called_ict is True
    assert res_ict["analysis"]["context_policy"] == "ICT_NATIVE"


@pytest.mark.parametrize("profile", ["BOOM", "CRASH", "STEP", "JUMP", "VOLATILITY_1", "FOREX_1"])
def test_synthetic_and_forex_workers_route_to_ict_strategy(profile):
    """Verify all synthetic and forex workers execute under ICT Sabri Malle strategy."""
    cfg = configure_worker_rules(LiveTradingConfig(bot_profile=profile))
    called_ict = False

    class SpyICT:
        def analyze_symbol(self, symbol, now_utc=None):
            nonlocal called_ict
            called_ict = True
            return {"valid": False, "action": "WAITING_ICT", "reason": "TEST"}

    engine = LiveTradingEngine(
        provider=MockCandleProvider(),
        repository=MockRepo(),
        config=cfg,
        executor=MockExecutor(),
    )
    engine.ict_strategy = SpyICT()
    res = engine.process_symbol("Boom 1000 Index" if profile == "BOOM" else "Volatility 75 Index")
    assert called_ict is True
    assert res["analysis"]["context_policy"] == "ICT_NATIVE"


