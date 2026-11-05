"""Tests unitarios para el Motor de Criterio Humano (Human Criteria Decision Engine).

Valida:
1. Clasificación correcta de activos (Sintéticos, Forex, Materias Primas, Índices).
2. Escudo Macro/Noticias para Forex, Oro y Petróleo.
3. Cazador de Tendencia HTF (H1) en Sintéticos y filtro anti-contratendencia.
4. Filtro Anti-Agotamiento Clímax y Recompensa por Mechas de Rechazo.
5. Inmutabilidad estricta de Stop Loss y Take Profit de la estrategia original.
6. Modos FILTER, OBSERVE y OFF.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pandas as pd
import pytest

from strategy.human_criteria.config import (
    HumanCriteriaConfig,
    MODE_FILTER,
    MODE_OBSERVE,
    MODE_OFF,
)
from strategy.human_criteria.human_criteria_engine import (
    HumanCriteriaEngine,
    classify_symbol_category,
)
from strategy.execution.live_trading_engine import (
    LiveTradingConfig,
    LiveTradingEngine,
)


def _build_candles(
    n: int = 50,
    base: float = 100.0,
    trend: float = 0.5,
    noise: float = 0.2,
    freq: str = "1h",
) -> pd.DataFrame:
    """Genera DataFrame OHLCV sintético determinista para pruebas."""
    times = pd.date_range("2026-01-01 00:00", periods=n, freq=freq, tz="UTC")
    data = []
    current = base
    for i in range(n):
        o = current
        current += trend + (noise * ((i % 3) - 1))
        c = current
        h = max(o, c) + abs(noise) * 1.5
        l = min(o, c) - abs(noise) * 1.5
        data.append((times[i], o, h, l, c, 1000.0))
    return pd.DataFrame(data, columns=["time", "open", "high", "low", "close", "volume"])


def _write_calendar(path: Path, events: list[dict]) -> None:
    payload = {
        "calendar_status": "ACTUALIZADA",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "calendar_events": events,
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


# -----------------------------------------------------------------------------
# 1. Clasificación de Símbolos
# -----------------------------------------------------------------------------

def test_classify_symbol_category():
    assert classify_symbol_category("Crash 300 Index") == "SYNTHETIC"
    assert classify_symbol_category("Boom 1000 Index") == "SYNTHETIC"
    assert classify_symbol_category("Step Index 500") == "SYNTHETIC"
    assert classify_symbol_category("Jump 75 Index") == "SYNTHETIC"
    assert classify_symbol_category("Volatility 75 (1s) Index") == "SYNTHETIC"
    assert classify_symbol_category("XAUUSD") == "COMMODITY"
    assert classify_symbol_category("microXAUUSD") == "COMMODITY"
    assert classify_symbol_category("US Oil") == "COMMODITY"
    assert classify_symbol_category("US Tech 100") == "INDEX"
    assert classify_symbol_category("Wall Street 30") == "INDEX"
    assert classify_symbol_category("BTCUSD") == "CRYPTO"
    assert classify_symbol_category("EURUSD") == "FOREX"
    assert classify_symbol_category("GBPUSD.pro") == "FOREX"


# -----------------------------------------------------------------------------
# 2. Escudo Macro y Noticias (Forex y Materias Primas)
# -----------------------------------------------------------------------------

def test_forex_news_blackout_blocks_trade(tmp_path):
    cal_file = tmp_path / "financial_news.json"
    now = datetime.now(timezone.utc)
    # Evento de alto impacto en USD a ocurrir en 10 minutos
    events = [{
        "title": "Decisión de tasas de interés",
        "country": "USD",
        "impact": "ALTO",
        "event_at": (now + timedelta(minutes=10)).isoformat(),
    }]
    _write_calendar(cal_file, events)

    cfg = HumanCriteriaConfig(
        enabled=True,
        mode=MODE_FILTER,
        news_calendar_path=str(cal_file),
    )
    engine = HumanCriteriaEngine(cfg)

    signal = {
        "entry_price": 1.0850,
        "stop_loss": 1.0820,
        "take_profit": 1.0910,
        "tp1_price": 1.0880,
        "tp2_price": 1.0910,
        "spread": 0.0001,
    }

    # EURUSD afectado por USD -> VETO
    decision_eurusd = engine.evaluate_candidate(
        symbol="EURUSD",
        direction="BUY",
        signal=signal,
        current_time=now,
    )
    assert decision_eurusd.allowed is False
    assert "HIGH_IMPACT_NEWS_WINDOW" in decision_eurusd.reason

    # EURJPY no tiene USD -> No afectado por esa noticia
    decision_eurjpy = engine.evaluate_candidate(
        symbol="EURJPY",
        direction="BUY",
        signal=signal,
        current_time=now,
    )
    assert decision_eurjpy.breakdown.macro_news == cfg.weight_macro_news


def test_commodity_gold_and_oil_news_sensitivity(tmp_path):
    cal_file = tmp_path / "financial_news.json"
    now = datetime.now(timezone.utc)
    events = [
        {
            "title": "US CPI Inflation YoY",
            "country": "USD",
            "impact": "ALTO",
            "event_at": (now + timedelta(minutes=15)).isoformat(),
        },
        {
            "title": "Inventarios semanales de petróleo de la AIE",
            "country": "USD",
            "impact": "ALTO",
            "event_at": (now + timedelta(minutes=10)).isoformat(),
        },
    ]
    _write_calendar(cal_file, events)

    cfg = HumanCriteriaConfig(
        enabled=True,
        mode=MODE_FILTER,
        news_calendar_path=str(cal_file),
    )
    engine = HumanCriteriaEngine(cfg)

    # Oro (XAUUSD) afectado por USD
    signal_gold = {"entry_price": 2700.0, "stop_loss": 2690.0, "take_profit": 2720.0, "spread": 0.20}
    dec_gold = engine.evaluate_candidate("XAUUSD", "BUY", signal_gold, current_time=now)
    assert dec_gold.allowed is False
    assert "HIGH_IMPACT_NEWS_WINDOW:USD" in dec_gold.reason

    # Petróleo (US Oil) afectado por inventarios/petróleo
    signal_oil = {"entry_price": 75.0, "stop_loss": 74.0, "take_profit": 77.0, "spread": 0.05}
    dec_oil = engine.evaluate_candidate("US Oil", "SELL", signal_oil, current_time=now)
    assert dec_oil.allowed is False
    assert "HIGH_IMPACT_NEWS_WINDOW" in dec_oil.reason


# -----------------------------------------------------------------------------
# 3. Índices Sintéticos: Tendencia H1 y Filtros de Régimen
# -----------------------------------------------------------------------------

def test_synthetic_strong_trend_alignment_gets_grade_a():
    cfg = HumanCriteriaConfig(enabled=True, mode=MODE_FILTER)
    engine = HumanCriteriaEngine(cfg)

    # H1 alcista sano con retroceso ordenado a EMA50
    df_h1 = _build_candles(n=50, base=1000.0, trend=0.5, noise=0.2)
    ema_val = float(df_h1["close"].ewm(span=50, adjust=False).mean().iloc[-1])
    # Ajustar últimas velas para simular un pullback saludable sobre la EMA50 sin sobreextensión
    df_h1.loc[len(df_h1)-1, "close"] = ema_val + 0.5
    df_h1.loc[len(df_h1)-1, "high"] = ema_val + 1.2
    df_h1.loc[len(df_h1)-1, "low"] = ema_val - 0.2

    # M15 con retroceso sano y mecha de rechazo inferior
    df_ltf = _build_candles(n=30, base=1020.0, trend=0.2, noise=0.2, freq="15min")
    # Asegurar mecha inferior en la última vela
    df_ltf.loc[len(df_ltf)-1, "open"] = 1025.0
    df_ltf.loc[len(df_ltf)-1, "close"] = 1028.0
    df_ltf.loc[len(df_ltf)-1, "low"] = 1020.0   # Mecha de 5 puntos
    df_ltf.loc[len(df_ltf)-1, "high"] = 1028.5

    signal = {
        "entry_price": 1028.0,
        "stop_loss": 1018.0,
        "take_profit": 1048.0,
        "tp1_price": 1038.0,
        "tp2_price": 1048.0,
        "spread": 0.10,
    }

    decision = engine.evaluate_candidate(
        symbol="Volatility 75 Index",
        direction="BUY",
        signal=signal,
        df_h1=df_h1,
        df_ltf=df_ltf,
        current_spread=0.10,
    )

    assert decision.allowed is True
    assert decision.grade == "GRADE_A_ELITE"
    assert decision.score >= 80.0
    assert decision.breakdown.htf_trend == cfg.synthetic_weight_htf_trend


def test_synthetic_spike_hazard_guard():
    """Verifica penalización por asimetría de spikes en Crash (BUY) y Boom (SELL)."""
    cfg = HumanCriteriaConfig(enabled=True, mode=MODE_FILTER)
    engine = HumanCriteriaEngine(cfg)

    df_h1 = _build_candles(n=50, base=1000.0, trend=0.5, noise=0.2)
    df_ltf = _build_candles(n=30, base=1020.0, trend=0.2, noise=0.2, freq="15min")
    signal = {"entry_price": 1000.0, "stop_loss": 990.0, "take_profit": 1020.0, "spread": 0.1}

    # BUY en Crash 500 Index: penalización de spike hazard
    dec_crash = engine.evaluate_candidate(
        symbol="Crash 500 Index",
        direction="BUY",
        signal=signal,
        df_h1=df_h1,
        df_ltf=df_ltf,
    )
    assert dec_crash.breakdown.spike_penalty == 20.0
    assert dec_crash.details["spike_hazard"]["is_crash_hazard"] is True

    # SELL en Boom 600 Index: penalización de spike hazard
    dec_boom = engine.evaluate_candidate(
        symbol="Boom 600 Index",
        direction="SELL",
        signal=signal,
        df_h1=df_h1,
        df_ltf=df_ltf,
    )
    assert dec_boom.breakdown.spike_penalty == 20.0
    assert dec_boom.details["spike_hazard"]["is_boom_hazard"] is True


def test_synthetic_streak_penalty_with_repository():
    """Verifica descuento de salud por racha perdedora reciente."""
    cfg = HumanCriteriaConfig(enabled=True, mode=MODE_FILTER)
    engine = HumanCriteriaEngine(cfg)

    mock_repo_losing = SimpleNamespace(
        get_symbol_loss_status=lambda symbol, source, cooldown_minutes, now_utc: {
            "cooldown_active": True,
            "cooldown_remaining_minutes": 45.0,
            "daily_losses_count": 2,
        }
    )

    df_h1 = _build_candles(n=50, base=1000.0, trend=0.5, noise=0.2)
    df_ltf = _build_candles(n=30, base=1020.0, trend=0.2, noise=0.2, freq="15min")
    signal = {"entry_price": 1000.0, "stop_loss": 990.0, "take_profit": 1020.0, "spread": 0.1}

    dec = engine.evaluate_candidate(
        symbol="Volatility 5 Index",
        direction="BUY",
        signal=signal,
        df_h1=df_h1,
        df_ltf=df_ltf,
        repository=mock_repo_losing,
    )
    # Cooldown activo -> 0 puntos de racha
    assert dec.breakdown.streak_health == 0.0
    assert dec.details["streak"]["cooldown_active"] is True


def test_synthetic_counter_trend_is_vetoed():
    cfg = HumanCriteriaConfig(enabled=True, mode=MODE_FILTER)
    engine = HumanCriteriaEngine(cfg)

    # H1 bajista fuerte (caída continua)
    df_h1 = _build_candles(n=50, base=1500.0, trend=-3.0, noise=0.2)
    signal = {"entry_price": 1350.0, "stop_loss": 1340.0, "take_profit": 1370.0, "spread": 0.10}

    # Intentar comprar contra la caída en sintéticos
    decision = engine.evaluate_candidate(
        symbol="Crash 500 Index",
        direction="BUY",
        signal=signal,
        df_h1=df_h1,
    )

    assert decision.allowed is False
    assert "COUNTER_TREND_BUY_IN_BEARISH_H1" in decision.reason


def test_synthetic_parabolic_climax_overextension_vetoed():
    cfg = HumanCriteriaConfig(
        enabled=True,
        mode=MODE_FILTER,
        synthetic_climax_filter_enabled=True,
        synthetic_climax_atr_multiplier=2.5,
    )
    engine = HumanCriteriaEngine(cfg)

    df_h1 = _build_candles(n=50, base=1000.0, trend=1.0, noise=0.2)
    # M15 normal con velas de ~1.0 punto de rango (ATR ~ 1.0)
    df_ltf = _build_candles(n=30, base=1050.0, trend=0.1, noise=0.2, freq="15min")
    # Última vela clímax gigantesca: 10 puntos de rango (> 5x ATR)
    last_idx = len(df_ltf) - 1
    df_ltf.loc[last_idx, "open"] = 1052.0
    df_ltf.loc[last_idx, "close"] = 1062.0
    df_ltf.loc[last_idx, "low"] = 1051.8
    df_ltf.loc[last_idx, "high"] = 1062.1  # Cerró casi en el máximo

    signal = {"entry_price": 1062.0, "stop_loss": 1050.0, "take_profit": 1080.0, "spread": 0.10}
    decision = engine.evaluate_candidate(
        symbol="Boom 500 Index",
        direction="BUY",
        signal=signal,
        df_h1=df_h1,
        df_ltf=df_ltf,
    )

    assert decision.allowed is False
    assert "PARABOLIC_CLIMAX_OVEREXTENSION" in decision.reason


# -----------------------------------------------------------------------------
# 4. Inmutabilidad Estricta de Stop Loss y Take Profit
# -----------------------------------------------------------------------------

def test_sl_and_tp_are_never_altered_by_human_criteria_engine():
    cfg = HumanCriteriaConfig(enabled=True, mode=MODE_FILTER)
    engine = HumanCriteriaEngine(cfg)

    df_h1 = _build_candles(n=50, base=500.0, trend=1.5, noise=0.2)
    df_ltf = _build_candles(n=30, base=550.0, trend=0.3, noise=0.2, freq="15min")

    initial_sl = 538.12345
    initial_tp = 575.98765
    initial_tp1 = 555.55555
    initial_tp2 = 575.98765

    signal = {
        "entry_price": 546.0,
        "stop_loss": initial_sl,
        "take_profit": initial_tp,
        "tp1_price": initial_tp1,
        "tp2_price": initial_tp2,
        "spread": 0.10,
    }

    decision = engine.evaluate_candidate(
        symbol="Jump 50 Index",
        direction="BUY",
        signal=signal,
        df_h1=df_h1,
        df_ltf=df_ltf,
    )

    # Verificar que el motor NO modificó en absoluto los niveles originales
    assert signal["stop_loss"] == initial_sl
    assert signal["take_profit"] == initial_tp
    assert signal["tp1_price"] == initial_tp1
    assert signal["tp2_price"] == initial_tp2


# -----------------------------------------------------------------------------
# 5. Modos FILTER, OBSERVE y OFF
# -----------------------------------------------------------------------------

def test_observe_mode_does_not_block():
    cfg = HumanCriteriaConfig(enabled=True, mode=MODE_OBSERVE)
    engine = HumanCriteriaEngine(cfg)

    # H1 bajista intentando comprar (fallaría en FILTER)
    df_h1 = _build_candles(n=50, base=1000.0, trend=-2.0, noise=0.2)
    signal = {"entry_price": 900.0, "stop_loss": 890.0, "take_profit": 920.0, "spread": 0.10}

    decision = engine.evaluate_candidate(
        symbol="Step Index",
        direction="BUY",
        signal=signal,
        df_h1=df_h1,
    )

    # En modo OBSERVE no debe bloquearse la orden
    assert decision.allowed is True
    assert "OBSERVADO" in decision.reason
    assert decision.primary_veto_factor is not None


def test_off_mode_bypasses_all_checks():
    cfg = HumanCriteriaConfig(enabled=False, mode=MODE_OFF)
    engine = HumanCriteriaEngine(cfg)

    signal = {"entry_price": 100.0, "stop_loss": 90.0, "take_profit": 120.0}
    decision = engine.evaluate_candidate("EURUSD", "BUY", signal)

    assert decision.allowed is True
    assert decision.action == "HUMAN_CRITERIA_OFF"
    assert decision.score == 100.0


# -----------------------------------------------------------------------------
# 6. Integración en LiveTradingEngine (_human_criteria_entry_gate)
# -----------------------------------------------------------------------------

def test_live_trading_engine_human_criteria_gate_veto(tmp_path):
    cal_file = tmp_path / "financial_news.json"
    now = datetime.now(timezone.utc)
    events = [{
        "title": "Decisión de tasas de interés de la FED",
        "country": "USD",
        "impact": "ALTO",
        "event_at": (now + timedelta(minutes=5)).isoformat(),
    }]
    _write_calendar(cal_file, events)

    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(
        bot_profile="FOREX_1",
        forex_high_impact_news_calendar_path=str(cal_file),
        human_criteria_enabled=True,
        human_criteria_mode="FILTER",
    )
    from strategy.human_criteria import HumanCriteriaEngine, HumanCriteriaConfig
    engine.human_criteria_engine = HumanCriteriaEngine(
        HumanCriteriaConfig(
            enabled=True,
            mode="FILTER",
            news_calendar_path=str(cal_file),
        )
    )

    signal = {
        "entry_price": 1.2500,
        "stop_loss": 1.2450,
        "take_profit": 1.2600,
        "spread": 0.0001,
        "timeframe": "M15",
    }

    result = engine._human_criteria_entry_gate(
        symbol="GBPUSD",
        direction="BUY",
        signal=signal,
        analysis=None,
        key="test_key",
    )

    assert result is not None
    assert result["action"] == "HUMAN_CRITERIA_FILTER_REJECTED"
    assert "HIGH_IMPACT_NEWS_WINDOW" in result["reason"]
    # Comprobar que signal["human_criteria"] quedó sellada para auditoría
    assert "human_criteria" in signal
    assert signal["human_criteria"]["allowed"] is False


def test_malaysian_snr_threshold_calibration():
    # En sintéticos el umbral ICT estándar es 75.0 pts, pero para Malaysian SNR es 60.0 pts.
    cfg = HumanCriteriaConfig(
        enabled=True,
        mode=MODE_FILTER,
        synthetic_min_score_threshold=75.0,
        malaysian_snr_min_score_threshold=60.0,
    )
    engine = HumanCriteriaEngine(cfg)

    df_h1 = _build_candles(n=60, base=100.0, trend=0.8, noise=0.1)
    df_ltf = _build_candles(n=40, base=140.0, trend=0.1, noise=0.1, freq="15min")

    msnr_signal = {
        "strategy_name": "MALAYSIAN_SNR",
        "entry_price": 145.0,
        "stop_loss": 140.0,
        "take_profit": 155.0,
        "spread": 0.05,
    }

    decision_msnr = engine.evaluate_candidate(
        symbol="Volatility 75 Index",
        direction="BUY",
        signal=msnr_signal,
        df_h1=df_h1,
        df_ltf=df_ltf,
        current_spread=0.05,
    )

    ict_signal = {
        "strategy_name": "ICT_SABRI_MALLE",
        "entry_price": 145.0,
        "stop_loss": 140.0,
        "take_profit": 155.0,
        "spread": 0.05,
    }

    decision_ict = engine.evaluate_candidate(
        symbol="Volatility 75 Index",
        direction="BUY",
        signal=ict_signal,
        df_h1=df_h1,
        df_ltf=df_ltf,
        current_spread=0.05,
    )

    assert decision_msnr.score == decision_ict.score
    if 60.0 <= decision_msnr.score < 75.0:
        assert decision_msnr.allowed is True
        assert decision_ict.allowed is False
    assert cfg.malaysian_snr_min_score_threshold == 60.0

