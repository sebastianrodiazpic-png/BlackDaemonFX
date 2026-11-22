from types import SimpleNamespace
from unittest.mock import Mock
import pytest

from config.ict_instrument_policy import ICT_SYNTHETIC_FAMILIES, ICT_5Y_RESCUED_SYNTHETICS, ICT_5Y_SYNTH_PRUNED
from strategy.execution.live_trading_engine import LiveTradingEngine, LiveTradingConfig
from dashboard.strategy_bases_page import STRATEGY_BASES_HTML


def test_step_index_200_is_active_and_rescued():
    assert "Step Index 200" in ICT_5Y_RESCUED_SYNTHETICS
    assert "Step Index 200" not in ICT_5Y_SYNTH_PRUNED
    assert "Step Index 200" in ICT_SYNTHETIC_FAMILIES["STEP"]
    assert "Step Index 400" in ICT_SYNTHETIC_FAMILIES["STEP"]
    assert "Step Index 500" in ICT_SYNTHETIC_FAMILIES["STEP"]


def test_step_multi_strategy_rows_in_dashboard():
    html = STRATEGY_BASES_HTML
    assert "Step Index 200" in html
    assert "Step Index 400" in html
    assert "Step Index 500" in html
    assert "Worker STEP (MultiStrategia · Magic 26082104 · PID 17452)" in html


def test_step_adx_high_conviction_relaxation():
    engine = object.__new__(LiveTradingEngine)
    engine.config = SimpleNamespace(bot_profile="STEP", step_min_adx=25.0, step_prune_toxic_assets=False)
    engine.provider = Mock()
    engine.provider.get_candles.return_value = None

    # Signal with adx=21.0 and score=84.0 (high conviction >= 80.0) -> should pass ADX check!
    sig_high = {
        "strategy_name": "ICT",
        "adx": 21.0,
        "score": 84.0,
        "timeframe": "M15",
        "entry_timeframe": "M15",
        "structure_timeframe": "H1",
    }
    gate_res = engine._step_quality_gate("Step Index 400", sig_high)
    assert gate_res is None, f"Expected None but got {gate_res}"

    # Signal with adx=21.0 and score=60.0 (not high conviction) -> should reject with STEP_ADX_LOW (min_adx=25)
    sig_low = {
        "strategy_name": "ICT",
        "adx": 21.0,
        "score": 60.0,
        "timeframe": "M15",
        "entry_timeframe": "M15",
        "structure_timeframe": "H1",
    }
    gate_res_low = engine._step_quality_gate("Step Index 400", sig_low)
    assert gate_res_low is not None
    assert gate_res_low["action"] == "STEP_ADX_LOW"
    assert gate_res_low["min_adx"] == 25.0


def test_step_post_fill_risk_adaptive_tolerance():
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig()
    engine.executor = Mock()

    # Position with 5.0% excess over target risk (0.05 excess)
    # Standard tolerance is 0.035 -> would fail
    # Step adaptive tolerance is 0.065 -> should pass!
    target_risk = 50.0  # e.g. 0.5% of 10,000
    actual_risk = 52.5  # 5% excess (52.5 / 50.0 = 1.05)

    pos_mock = Mock()
    pos_mock.volume = 0.1
    pos_mock.price_open = 1000.0
    pos_mock.sl = 995.0
    engine.executor.get_position.return_value = pos_mock
    engine.executor.calculate_risk_amount.return_value = {
        "actual_risk_amount": actual_risk,
        "risk_engine": "MOCK",
    }

    res = engine._validate_post_fill_risk(
        symbol="Step Index 400",
        direction="BUY",
        position_ticket=12345,
        target_risk_amount=target_risk,
        risk_base_value=10000.0,
    )
    assert res["valid"] is True
    assert res["reason"] == "POST_FILL_RISK_OK"


def test_step_snr_m5_confirmation_allowed_with_h1_or_m15():
    engine = object.__new__(LiveTradingEngine)
    engine.config = SimpleNamespace(bot_profile="STEP", step_min_adx=25.0, step_prune_toxic_assets=False)
    engine.provider = Mock()
    engine.malaysian_snr_strategy = None

    sig_m5 = {
        "strategy_name": "MALAYSIAN_SNR",
        "adx": 26.0,
        "confirmation_timeframe": "M5",
        "entry_timeframe": "M5",
        "structure_timeframe": "M15",
    }
    res = engine._step_quality_gate("Step Index 200", sig_m5)
    assert res is None
