"""Regresión: los workers SNR de mercados reales deben tener ajustes MSNR válidos.

Incidente 11-nov-2026: se pasó session_policy="asia_to_ny" a MalaysianSNRConfig en
FOREX_SNR / COMMODITIES_SNR / INDICESB_SNR. validate_msnr_patch sólo admite
legacy_utc/market_hours, así que config_settings_snapshot() lanzaba y TODOS los
símbolos reales terminaban en MSNR_SETTINGS_UNAVAILABLE (0 entradas).
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine


class _Repo:
    def save_signal_once(self, payload):
        return 1, True

    def get_trade_by_execution_key(self, key):
        return None


class _Provider:
    connector = SimpleNamespace()

    def resolve_symbol(self, symbol):
        return symbol

    def ensure_symbol(self, symbol):
        return True


@pytest.mark.parametrize(
    "profile,symbols",
    [
        ("FOREX_SNR", ["EURUSD", "GBPJPY", "USDJPYmicro"]),
        ("COMMODITIES_SNR", ["XAUUSD", "US Oil", "XAGUSD"]),
        ("INDICESB_SNR", ["US SP 500", "Germany 40", "Wall Street 30"]),
    ],
)
def test_real_market_snr_workers_have_valid_msnr_settings(profile, symbols):
    engine = LiveTradingEngine(
        provider=_Provider(),
        repository=_Repo(),
        config=LiveTradingConfig(bot_profile=profile, execution_enabled=False),
    )
    strategy = engine.malaysian_snr_strategy
    snapshot = strategy.config_settings_snapshot()  # no debe lanzar
    assert snapshot["session_policy"] in ("legacy_utc", "market_hours")
    for symbol in symbols:
        assert strategy.is_real_market_symbol(symbol), symbol
        assert strategy.real_market_session_policy(symbol) == "asia_to_ny"
        result = strategy.analyze_symbol(symbol)
        assert result.get("reason") != "MSNR_SETTINGS_UNAVAILABLE", (symbol, result)
