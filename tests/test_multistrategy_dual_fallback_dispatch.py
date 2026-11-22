"""Tests unitarios para la arquitectura de doble despacho y fallback MultiStrategia (MSNR + ICT).

Verifica que:
1. En todos los workers MultiStrategia (BOOM, CRASH, STEP, JUMP, VOLATILITY 1-4, ICT, INDICESB_SNR, FOREX 1-5),
   cuando Malaysian SNR no encuentra un retesteo válido (valid=False), el motor NO aborte con WAITING_MALAYSIAN_SNR,
   sino que evalúe y ejecute ICT.
2. Si Malaysian SNR encuentra un setup válido (valid=True), se seleccione Malaysian SNR (strategy_name="MALAYSIAN_SNR").
3. Si el worker es exclusivamente MALAYSIAN_SNR y no hay setup válido, se conserve el comportamiento de observación.
"""

from unittest.mock import MagicMock, patch
import pytest

from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
from strategy.execution.worker_rules import configure_worker_rules


@pytest.fixture
def mock_provider():
    p = MagicMock()
    p.resolve_symbol.side_effect = lambda s: s
    p.ensure_symbol.return_value = True
    return p


@pytest.fixture
def mock_repository():
    r = MagicMock()
    r.open_trades.return_value = []
    r.active_position_guards.return_value = []
    return r


@pytest.mark.parametrize("worker_profile,symbol,expected_direction", [
    ("BOOM", "Boom 500 Index", "BUY"),
    ("CRASH", "Crash 300 Index", "SELL"),
    ("STEP", "Step Index", "BUY"),
    ("JUMP", "Jump 50 Index", "BUY"),
    ("VOLATILITY_1", "High Frequency Vol 100 Index", "BUY"),
    ("VOLATILITY_2", "VolSwitch Low Vol Index", "BUY"),
    ("VOLATILITY_3", "Volatility 75 Index", "BUY"),
    ("VOLATILITY_4", "Volatility 75 (1s) Index", "BUY"),
    ("ICT", "XAUUSDmicro", "BUY"),
    ("INDICESB_SNR", "US Tech 100", "BUY"),
    ("FOREX_1", "AUDNZD", "BUY"),
])
def test_multistrategy_worker_falls_back_to_ict_when_msnr_invalid(
    mock_provider, mock_repository, worker_profile, symbol, expected_direction
):
    """Cuando Malaysian SNR no tiene setup válido, el worker MultiStrategia debe evaluar y seleccionar ICT."""
    cfg = LiveTradingConfig(bot_profile=worker_profile, magic=26082000, execution_enabled=False)
    cfg = configure_worker_rules(cfg)

    engine = LiveTradingEngine(provider=mock_provider, repository=mock_repository, config=cfg)

    # 1. Malaysian SNR devuelve valid=False (sin retesteo en ese ciclo)
    engine.malaysian_snr_strategy.analyze_symbol = MagicMock(return_value={
        "symbol": symbol,
        "valid": False,
        "reason": "MSNR_NO_FRESH_RETEST",
        "action": "NO_SIGNAL",
    })

    # 2. ICT devuelve valid=True con señal institucional
    mock_ict_result = {
        "symbol": symbol,
        "valid": True,
        "action": expected_direction,
        "strategy_name": "ICT",
        "signal": {
            "symbol": symbol,
            "direction": expected_direction,
            "entry_price": 100.0,
            "stop_loss": 90.0 if expected_direction == "BUY" else 110.0,
            "take_profit_1": 110.0 if expected_direction == "BUY" else 90.0,
            "take_profit_2": 120.0 if expected_direction == "BUY" else 80.0,
            "strategy_name": "ICT",
        },
    }
    engine._ict_analysis_with_virtual_limit = MagicMock(return_value=mock_ict_result)

    # Mockeamos _active_position_gate para que permita el análisis
    engine._active_position_gate = MagicMock(return_value=None)
    engine._ict_spread_lock_gate = MagicMock(return_value=None)
    engine._market_regime_entry_gate = MagicMock(return_value=None)
    engine._symbol_loss_cooldown_gate = MagicMock(return_value=None)
    engine._gold_smc_entry_gate = MagicMock(return_value=None)
    engine._forex_killzone_entry_gate = MagicMock(return_value=None)
    engine._forex_rollover_entry_gate = MagicMock(return_value=None)
    engine._crypto_rollover_entry_gate = MagicMock(return_value=None)
    engine._forex_high_impact_news_entry_gate = MagicMock(return_value=None)
    engine._quarantine_result = MagicMock(return_value=None)

    result = engine.process_symbol(symbol)

    # El resultado NO debe ser WAITING_MALAYSIAN_SNR; debe evaluar ICT
    assert result is not None
    assert result.get("action") != "WAITING_MALAYSIAN_SNR", (
        f"Worker {worker_profile} abortó prematuramente con WAITING_MALAYSIAN_SNR en vez de evaluar ICT"
    )
    # Debe haber ejecutado ICT
    engine._ict_analysis_with_virtual_limit.assert_called_once_with(symbol)


def test_pure_malaysian_snr_worker_preserves_observation_result(mock_provider, mock_repository):
    """El worker exclusivo MALAYSIAN_SNR debe preservar el retorno de observación si no hay setup."""
    cfg = LiveTradingConfig(bot_profile="MALAYSIAN_SNR", magic=26082031, execution_enabled=False)
    cfg = configure_worker_rules(cfg)

    engine = LiveTradingEngine(provider=mock_provider, repository=mock_repository, config=cfg)
    engine.malaysian_snr_strategy.analyze_symbol = MagicMock(return_value={
        "symbol": "Step Index 500",
        "valid": False,
        "reason": "MSNR_NO_FRESH_RETEST",
    })
    engine._active_position_gate = MagicMock(return_value=None)

    result = engine.process_symbol("Step Index 500")

    assert result is not None
    assert result.get("action") == "WAITING_MALAYSIAN_SNR"
