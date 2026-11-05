"""Test suite for ICT Sabri Malle improvements:
1. Doble gatillo de entrada en FVG (Mitigation / Threshold vs Consequent Encroachment 50%).
2. Activación del Silver Bullet de Nueva York (10:00 - 11:00 AM NY) y Londres (03:00 - 05:00 NY).
3. Mitigación de Order Blocks (OB 5 Estrellas como soporte alternativo de entrada).
"""
import os
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from zoneinfo import ZoneInfo
import pandas as pd
import pytest

from strategy.ict.config import ICTSabriMalleConfig
from strategy.ict.ict_strategy import ICTSabriMalleStrategy, check_order_block_five_stars
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


def test_silver_bullet_hours_default_includes_london_and_ny_am():
    cfg = ICTSabriMalleConfig()
    assert 3 in cfg.silver_bullet_hours_ny  # 03:00 AM NY (London)
    assert 10 in cfg.silver_bullet_hours_ny  # 10:00 AM NY (New York AM)


def test_silver_bullet_env_override(monkeypatch):
    monkeypatch.setenv("DAEMONBLACKFX_ICT_SB_HOURS_NY", "3,10,14")
    cfg = ICTSabriMalleConfig()
    assert cfg.silver_bullet_hours_ny == (3, 10, 14)


def test_silver_bullet_activation_in_ny_am_window():
    ny_tz = ZoneInfo("America/New_York")
    now_ny = datetime(2026, 10, 15, 10, 30, tzinfo=ny_tz).astimezone(timezone.utc)
    dates = [now_ny - timedelta(hours=i) for i in range(40, 0, -1)]
    df_h1 = pd.DataFrame({
        "time": dates,
        "open": [1.10] * 40,
        "high": [1.11] * 40,
        "low": [1.09] * 40,
        "close": [1.10] * 40,
    })
    strat = ICTSabriMalleStrategy(data_provider=MockCandleProvider(df_h1=df_h1), config=ICTSabriMalleConfig())
    res = strat.analyze_symbol("EURUSD", now_utc=now_ny)
    # 10:30 AM NY está dentro de la ventana Silver Bullet, por lo que pasa el filtro de sesiones
    assert "OUTSIDE_INSTITUTIONAL_KILLZONE" not in res.get("reason", "")


def test_order_block_five_stars_mitigation_detection():
    df = pd.DataFrame({
        "open": [100.0, 98.0, 95.0, 96.0, 102.0, 105.0],
        "high": [101.0, 99.0, 96.0, 98.0, 104.0, 107.0],
        "low": [97.0, 94.0, 91.0, 95.0, 101.0, 104.0],
        "close": [98.0, 95.0, 92.0, 101.0, 105.0, 106.0],
    })
    ob_buy = check_order_block_five_stars(df, "BUY")
    assert ob_buy["valid"] is True
    assert ob_buy["stars"] >= 3
    assert ob_buy["top"] == 96.0
    assert ob_buy["mean_threshold"] == 93.5

    ob_sell = check_order_block_five_stars(df, "SELL")
    # For SELL, the candles don't form a bearish OB with displacement down, valid is False
    assert ob_sell["valid"] is False


def test_dual_entry_mitigation_config_switches(monkeypatch):
    monkeypatch.setenv("DAEMONBLACKFX_ICT_DUAL_ENTRY_MITIGATION", "0")
    monkeypatch.setenv("DAEMONBLACKFX_ICT_OB_MITIGATION", "0")
    monkeypatch.setenv("DAEMONBLACKFX_ICT_MITIGATION_FVG_RATIO", "0.20")
    cfg = ICTSabriMalleConfig()
    assert cfg.dual_entry_mitigation_enabled is False
    assert cfg.ob_mitigation_entry_enabled is False
    assert cfg.mitigation_fvg_ratio == 0.20

    live_cfg = LiveTradingConfig()
    assert live_cfg.ict_dual_entry_mitigation_enabled is False


def test_virtual_limit_triggers_on_mitigation_limit():
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(bot_profile="VOLATILITY_1", ict_virtual_limit_enabled=True)
    engine.ict_strategy = SimpleNamespace(analyze_symbol=lambda s: {"valid": False})
    engine._is_crypto_symbol = lambda s: False
    engine._is_synthetic_symbol = lambda s: True
    engine._virtual_limit_now = lambda: datetime(2026, 10, 19, 12, 16, tzinfo=timezone.utc)
    engine._meta_execution_spread = lambda s: {"execution_bid": 99.5, "execution_ask": 99.6}
    engine.audits = []
    engine._persist_audit_event = lambda event, **kw: engine.audits.append((kw.get("action"), kw.get("reason")))

    # Pending order with deep limit at 99.0 and mitigation limit at 99.6
    engine._ict_virtual_limits = {
        "Step Index 200": {
            "identity": ("BUY", "2026-10-19T12:00:00+00:00", 99.0),
            "analysis": {
                "valid": True,
                "strategy_name": "ICT_SABRI_MALLE",
                "strategy_version": "test",
                "signal": {
                    "direction": "BUY",
                    "entry_price": 99.0,
                    "mitigation_entry_price": 99.6,
                    "stop_loss": 98.0,
                    "tp1_rr": 1.0,
                    "runner_rr": 2.0,
                }
            },
            "direction": "BUY",
            "limit": 99.0,
            "mitigation_limit": 99.6,
            "stop_loss": 98.0,
            "created_at": "2026-10-19T12:00:00+00:00",
            "expires_at": datetime(2026, 10, 19, 15, 0, tzinfo=timezone.utc),
        }
    }
    engine._ict_virtual_limits_consumed = {}

    res = engine._ict_analysis_with_virtual_limit("Step Index 200")
    # Ask is 99.6 <= mitigation_limit (99.6), so it triggers!
    assert res["valid"] is True
    assert res["signal"]["entry_price"] == 99.6
    assert res["signal"]["risk_amount"] == pytest.approx(1.6)
    assert res["signal"]["tp1_price"] == pytest.approx(99.6 + 1.6)
    assert res["signal"]["tp2_price"] == pytest.approx(99.6 + 3.2)
    assert engine.audits[-1][0] == "TRIGGERED"
