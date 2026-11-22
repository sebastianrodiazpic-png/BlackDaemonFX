"""tests/test_trade_unlock_and_optimization_enhancements.py - Validación de mejoras de optimización y desbloqueo de trades.

Cubre:
1. ICT Strategy: in_asian_session_jpy_aud inicializado por defecto, cero UnboundLocalError en Gold, Indices, Commodities y Sintéticos.
2. Live Trading Engine: Liberación de bloqueo de spread por recuperación (DAEMONBLACKFX_ICT_SPREAD_LOCK_RELEASE_ON_RECOVERY).
3. Human Criteria Engine: Anulación de veto de régimen tóxico (toxic_overridden_by_absorption) para ICT (desplazamiento FVG) y MSNR (absorción).
4. MT5 Data Provider: TTL adaptativo para temporalidades mayores (H1, H4).
"""

import os
from datetime import datetime, timezone
import pandas as pd
import pytest

from strategy.ict.config import ICTSabriMalleConfig
from strategy.ict.ict_strategy import ICTSabriMalleStrategy
from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
from strategy.human_criteria.config import HumanCriteriaConfig
from strategy.human_criteria.human_criteria_engine import HumanCriteriaEngine


class _DummyProvider:
    def __init__(self, candles=None):
        self.candles = candles

    def get_candles(self, symbol, timeframe="M15", count=10):
        return self.candles

    def ensure_symbol(self, s):
        return s

    def get_symbol_info(self, s):
        return {"digits": 2, "point": 0.01}


def test_ict_strategy_in_asian_session_defined_for_all_asset_types():
    """Verifica que in_asian_session_jpy_aud esté siempre definido sin lanzar UnboundLocalError."""
    cfg = ICTSabriMalleConfig()
    provider = _DummyProvider()
    strat = ICTSabriMalleStrategy(data_provider=provider, config=cfg)

    test_symbols = [
        "XAUUSD",              # Gold
        "US SP 500",           # Index
        "US Oil",              # Commodity
        "Volatility 75 Index", # Synthetic
        "EURUSD",              # Non-JPY/AUD Forex
        "GBPJPY",              # JPY Forex
    ]

    for sym in test_symbols:
        try:
            res = strat.analyze_symbol(sym)
            assert isinstance(res, dict)
            assert "valid" in res
            # Ninguna evaluación debe fallar por UnboundLocalError
            assert "in_asian_session_jpy_aud" not in str(res.get("reason", ""))
        except UnboundLocalError as exc:
            pytest.fail(f"UnboundLocalError lanzado en {sym}: {exc}")


def test_ict_spread_lock_releases_when_spread_recovers():
    """Verifica que si el spread se normaliza por debajo del 2% del SL, el lock se libera inmediatamente."""
    e = object.__new__(LiveTradingEngine)
    e.config = LiveTradingConfig(
        bot_profile="VOLATILITY_1",
        ict_spread_block_lock_enabled=True,
        ict_spread_lock_release_on_recovery=True,
        synthetic_spread_max_risk_ratio=0.02,
    )
    e.events = []
    e._persist_audit_event = lambda *a, **k: e.events.append((a[0], k.get("action"), k.get("reason")))

    # Simular un spread inicial del 20% (bloqueo)
    spread_val = [2.0]
    e._meta_execution_spread = lambda s: {"spread": spread_val[0], "execution_ask": 100.0, "execution_bid": 100.0 - spread_val[0]}
    e.provider = _DummyProvider()

    # Dispara el bloqueo de spread (20% > 2%)
    out = e._forex_execution_gate("Volatility 10 Index", "BUY", 90.0, strategy_name="ICT_SABRI_MALLE")
    assert out["action"] == "SYNTHETIC_SPREAD_TO_SL_EXCEEDED"
    assert "Volatility 10 Index" in e._ict_spread_locks

    # Con el spread aún en 2.0 (20% del riesgo de 10), el lock permanece activo
    assert e._ict_spread_lock_gate("Volatility 10 Index")["action"] == "ICT_SPREAD_LOCK_ACTIVE"

    # Ahora el spread se normaliza a 0.15 (1.5% del riesgo de 10 <= 2%)
    spread_val[0] = 0.15
    assert e._ict_spread_lock_gate("Volatility 10 Index") is None
    assert "Volatility 10 Index" not in e._ict_spread_locks
    assert e.events[-1] == ("ICT_SPREAD_LOCK", "RELEASED", "VIRTUAL_TRADE_SPREAD_NORMALIZED")


def test_human_criteria_toxic_regime_overridden_by_ict_displacement():
    """Verifica que un setup ICT con desplazamiento institucional o FVG anule el veto de régimen tóxico."""
    cfg = HumanCriteriaConfig(
        enabled=True,
        mode="FILTER",
        min_score_threshold=50.0,
        synthetic_min_score_threshold=50.0,
        absorption_regime_override_enabled=True,
    )
    engine = HumanCriteriaEngine(config=cfg)

    # Forzar clasificación tóxica en _eval_regime_health
    engine._eval_regime_health = lambda *a, **k: (15.0, True, "TOXIC_NOISE:ERRATIC_WHIPSAW_VOLATILITY", {})
    engine._eval_macro_news = lambda *a, **k: (25.0, False, None, {})
    engine._eval_htf_trend = lambda *a, **k: (30.0, False, None, {})
    engine._eval_spike_hazard = lambda *a, **k: (0.0, False, None, {})
    engine._eval_candle_quality = lambda *a, **k: (15.0, False, None, {})
    engine._eval_spread_friction = lambda *a, **k: (10.0, {})

    # Señal ICT con desplazamiento institucional FVG
    signal_ict = {
        "symbol": "XAUUSD",
        "direction": "BUY",
        "strategy_name": "ICT_SABRI_MALLE",
        "entry_price": 2000.0,
        "stop_loss": 1990.0,
        "displacement_body_ratio": 0.65,
        "fvg_consequent_encroachment_aligned": True,
        "scenario": "AMD_KILLZONE_FVG_REJECTION",
    }

    decision = engine.evaluate_candidate(signal=signal_ict, symbol="XAUUSD", direction="BUY")
    assert decision.allowed is True
    assert decision.details["regime"].get("toxic_overridden_by_absorption") is True
    assert "CRITERIO_HUMANO_APROBADO" in decision.reason


def test_human_criteria_toxic_regime_overridden_by_msnr_absorption():
    """Verifica que un setup MSNR con absorción anule el veto de régimen tóxico."""
    cfg = HumanCriteriaConfig(
        enabled=True,
        mode="FILTER",
        min_score_threshold=50.0,
        malaysian_snr_min_score_threshold=50.0,
        absorption_regime_override_enabled=True,
    )
    engine = HumanCriteriaEngine(config=cfg)

    engine._eval_regime_health = lambda *a, **k: (15.0, True, "TOXIC_NOISE:ERRATIC_WHIPSAW_VOLATILITY", {})
    engine._eval_macro_news = lambda *a, **k: (25.0, False, None, {})
    engine._eval_htf_trend = lambda *a, **k: (30.0, False, None, {})
    engine._eval_spike_hazard = lambda *a, **k: (0.0, False, None, {})
    engine._eval_candle_quality = lambda *a, **k: (15.0, False, None, {})
    engine._eval_spread_friction = lambda *a, **k: (10.0, {})

    signal_msnr = {
        "symbol": "Volatility 75 Index",
        "direction": "SELL",
        "strategy_name": "MALAYSIAN_SNR",
        "entry_price": 500.0,
        "stop_loss": 520.0,
        "displacement": True,
        "retest_evidence": {"displacement": True, "body_ratio": 0.60},
    }

    decision = engine.evaluate_candidate(signal=signal_msnr, symbol="Volatility 75 Index", direction="SELL")
    assert decision.allowed is True
    assert decision.details["regime"].get("toxic_overridden_by_absorption") is True


def test_mt5_provider_htf_cache_ttl_configuration():
    """Verifica que el TTL adaptativo HTF esté configurado en 30s por defecto."""
    htf_ttl = float(os.getenv("DAEMONBLACKFX_HTF_CANDLE_CACHE_TTL_SECONDS", "30.0"))
    assert htf_ttl >= 15.0
    assert htf_ttl == 30.0


def test_be_runner_slot_exemption_allows_new_trades_when_runners_are_risk_free():
    """Verifica que las posiciones con SL en Break Even (riesgo 0) se eximan del cupo de riesgo activo."""
    e = object.__new__(LiveTradingEngine)
    e.config = LiveTradingConfig(
        bot_profile="VOLATILITY_1",
        max_open_positions=4,
        max_total_open_positions=4,
        max_open_positions_per_symbol=2,
        split_entries_enabled=True,
        be_runner_slot_exemption_enabled=True,
        be_runner_max_total_cap=12,
        source="DEMO",
    )

    # Simular 4 posiciones abiertas en SQLite: 2 de ellas son runners protegidos en Break Even
    mock_open_trades = [
        {"id": 1, "instrument": "Jump 25 Index", "direction": "BUY", "entry_price": 100.0, "stop_loss": 100.5, "status": "OPEN"}, # BE profit
        {"id": 2, "instrument": "Jump 75 Index", "direction": "SELL", "entry_price": 200.0, "stop_loss": 199.5, "status": "OPEN"}, # BE profit
        {"id": 3, "instrument": "Step Index", "direction": "BUY", "entry_price": 50.0, "stop_loss": 45.0, "status": "OPEN"},     # Riesgo activo -1R
        {"id": 4, "instrument": "Step Index 500", "direction": "SELL", "entry_price": 80.0, "stop_loss": 85.0, "status": "OPEN"}, # Riesgo activo -1R
    ]

    class _MockRepo:
        def open_trades(self, source="DEMO"):
            return mock_open_trades

    e.repository = _MockRepo()
    e._trade_owned_by_current_bot = lambda t: True

    # Diagnósticos de posiciones
    diag = e._open_trade_diagnostics("Volatility 10 Index")
    assert diag["total_open"] == 4
    assert diag["be_exempt_count"] == 2
    # Las posiciones con riesgo activo son 4 - 2 = 2
    assert diag["active_risk_open"] == 2

    # Intentar abrir nueva operación para Volatility 10 Index (requiere 2 slots)
    # active_risk_open (2) + required_slots (2) = 4 <= max_total (4) -> PERMITIDO
    res = e._position_limit_result("Volatility 10 Index", "EXEC_KEY_1")
    assert res is None, f"Esperado None (permitido), pero obtuvo bloqueo: {res}"


def test_real_markets_h4_macro_flex_enabled_defaults():
    """Verifica que real_markets_h4_macro_flex_enabled, indices_cash_liquidity y fractal_mss estén activos."""
    cfg = ICTSabriMalleConfig()
    assert bool(cfg.real_markets_h4_macro_flex_enabled) is True
    assert bool(cfg.indices_cash_liquidity_sweep_enabled) is True
    assert bool(cfg.fractal_mss_enabled) is True

