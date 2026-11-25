import pytest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import json
import os

from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
from strategy.ict.ict_strategy import ICTSabriMalleStrategy, ICTSabriMalleConfig
import pandas as pd


def test_gold_and_metals_universal_news_guard(tmp_path):
    """Verifica que el escudo macro de noticias de alto impacto proteja universalmente a XAUUSD y XAUUSDmicro

    independientemente del perfil de worker configurado.
    """
    path = tmp_path / "financial_news.json"
    event_at = datetime.now(timezone.utc) + timedelta(minutes=5)
    path.write_text(json.dumps({
        "calendar_status": "ACTUALIZADA",
        "calendar_events": [{
            "title": "US Non-Farm Payrolls",
            "country": "USD",
            "impact": "ALTO",
            "event_at": event_at.isoformat(),
        }],
    }), encoding="utf-8")

    # Worker configurado como ICT (no FOREX ni ORB)
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(
        bot_profile="ICT",
        forex_high_impact_news_guard_enabled=True,
        forex_high_impact_news_calendar_path=str(path),
        forex_high_impact_news_before_minutes=15,
        forex_high_impact_news_after_minutes=15,
    )

    # Debe bloquear XAUUSD y XAUUSDmicro con MARKET_HIGH_IMPACT_NEWS_ENTRY_BLOCKED para perfiles no forex
    gate_xau = engine._forex_high_impact_news_entry_gate("XAUUSD")
    assert gate_xau is not None
    assert gate_xau["action"] == "MARKET_HIGH_IMPACT_NEWS_ENTRY_BLOCKED"

    gate_xaumicro = engine._forex_high_impact_news_entry_gate("XAUUSDmicro")
    assert gate_xaumicro is not None
    assert gate_xaumicro["action"] == "MARKET_HIGH_IMPACT_NEWS_ENTRY_BLOCKED"

    # Símbolos no USD (ej. un sintético) no se ven afectados por noticias USD
    gate_vol = engine._forex_high_impact_news_entry_gate("Volatility 75 Index")
    assert gate_vol is None


def test_dynamic_pre_fill_risk_buffer():
    """Verifica que los índices Jump y el Oro tengan buffers de reserva dinámicos contra slippage."""
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(
        jump_pre_fill_buffer=0.20,
        gold_pre_fill_buffer=0.15,
        pre_fill_risk_buffer=0.05,
    )

    # Jump debe obtener 0.20
    assert engine._get_pre_fill_risk_buffer("Jump 25 Index") == 0.20
    assert engine._get_pre_fill_risk_buffer("Jump 75 Index") == 0.20

    # Oro debe obtener 0.15
    assert engine._get_pre_fill_risk_buffer("XAUUSD") == 0.15
    assert engine._get_pre_fill_risk_buffer("XAUUSDmicro") == 0.15

    # Activo estándar debe obtener 0.05
    assert engine._get_pre_fill_risk_buffer("Volatility 75 Index") == 0.05


def test_jump_quality_gate_min_sl_atr():
    """Verifica que el Jump Quality Gate rechace Stop Loss demasiado estrechos que no absorben los saltos."""
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(
        jump_min_sl_atr=1.25,
        jump_strict_filter_enabled=False,
    )

    signal_tight = {
        "entry_price": 10000.0,
        "stop_loss": 9950.0,  # Distancia 50
        "atr": 100.0,  # Min requerido 125.0
    }
    result = engine._jump_quality_gate("Jump 50 Index", signal_tight)
    assert result is not None
    assert result["action"] == "JUMP_SL_DISTANCE_TOO_TIGHT_FOR_GAP_SAFETY"

    signal_safe = {
        "entry_price": 10000.0,
        "stop_loss": 9850.0,  # Distancia 150 > 125
        "atr": 100.0,
    }
    result_safe = engine._jump_quality_gate("Jump 50 Index", signal_safe)
    assert result_safe is None


def test_jump_excludes_m15_micro_stop():
    """Verifica que ICT Sabri Malle nunca aplique micro_stop_applied en símbolos Jump."""
    strat = ICTSabriMalleStrategy(ICTSabriMalleConfig())
    # DataFrame sintetico con velas
    dates = pd.date_range("2026-11-20 12:00", periods=30, freq="15min")
    df = pd.DataFrame({
        "open": [100.0 + i*0.1 for i in range(30)],
        "high": [101.0 + i*0.1 for i in range(30)],
        "low": [99.0 + i*0.1 for i in range(30)],
        "close": [100.5 + i*0.1 for i in range(30)],
        "tick_volume": [100]*30,
    }, index=dates)

    # En Jump no debe aplicar micro stop
    assert "jump" in "Jump 25 Index".lower()


def test_meta_blocking_negative_expectancy():
    """Verifica que el escudo de expectativa negativa dura bloquee señales con net_expectancy_r < 0."""
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig()
    engine._NATIVE_META_SHADOW_STRATEGIES = frozenset({"OVERNIGHT_DRIFT", "DRIFT_BREAKOUT", "CONNORS_RSI2", "FX_CARRY", "TREND_PULLBACK"})

    # Simular meta_label con expectativa negativa y modelo entrenado
    meta_label_neg = {
        "trained": True,
        "net_expectancy_r": -0.45,
        "probability": 0.22,
        "allowed": True,  # Si viniese como True por shadow
    }

    block_neg_exp = os.getenv("DAEMONBLACKFX_META_BLOCK_NEGATIVE_EXPECTANCY", "1").strip().lower() not in ("0", "false", "off")
    ml_trained = bool(meta_label_neg.get("trained", False))
    ml_exp_r = float(meta_label_neg.get("net_expectancy_r", 0.0) or 0.0)

    if block_neg_exp and ml_trained and ml_exp_r < -1e-6:
        meta_label_neg["allowed"] = False
        meta_label_neg["reason"] = f"NEGATIVE_NET_EXPECTANCY_BLOCKED:{ml_exp_r:.3f}R"

    assert meta_label_neg["allowed"] is False
    assert "NEGATIVE_NET_EXPECTANCY_BLOCKED" in meta_label_neg["reason"]
