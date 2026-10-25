"""Correcciones de la auditoría de código del 24-oct-2026 (ver REGISTRO_CAMBIOS_ESTRATEGIA.md)."""
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import brokers.mt5_execution as mt5_execution
from brokers.mt5_execution import MT5ExecutionError, MT5ExecutionProvider
from dashboard.request_guard import unsafe_request_reason
from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
from strategy.ict.ict_strategy import is_synthetic_asset
from strategy.malaysian_snr.malaysian_snr_strategy import is_synthetic_symbol
from tests.test_ict_virtual_limit_entry import BAR, make_engine, none_signal, signal_analysis


# --- 1. volume_limit del símbolo repartido entre las piernas -------------------------------------------------------

def engine_with_executor(executor, **cfg):
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(bot_profile="VOLATILITY_1", **cfg)
    engine.executor = executor
    return engine


def test_leg_volume_cap_splits_symbol_headroom_between_legs():
    executor = SimpleNamespace(symbol_volume_headroom=lambda s, d: {"volume_limit": 50.0, "used_volume": 0.0,
                                                                    "headroom": 50.0})
    assert engine_with_executor(executor)._leg_volume_cap("Volatility 250 (1s) Index", "BUY", 2) == 25.0


def test_leg_volume_cap_discounts_volume_already_open():
    executor = SimpleNamespace(symbol_volume_headroom=lambda s, d: {"headroom": 20.0})
    assert engine_with_executor(executor)._leg_volume_cap("X", "SELL", 2) == 10.0


@pytest.mark.parametrize("executor", [
    SimpleNamespace(),                                                       # ejecutor sin límite (paper)
    SimpleNamespace(symbol_volume_headroom=lambda s, d: {"headroom": None}),  # símbolo sin volume_limit
    SimpleNamespace(symbol_volume_headroom=MagicMock(side_effect=RuntimeError("mt5"))),
    MagicMock(),                                                             # dobles de test genéricos
])
def test_leg_volume_cap_is_none_when_unknown(executor):
    assert engine_with_executor(executor)._leg_volume_cap("X", "BUY", 2) is None


def test_leg_volume_cap_switch_off():
    executor = SimpleNamespace(symbol_volume_headroom=lambda s, d: {"headroom": 50.0})
    assert engine_with_executor(executor, leg_volume_limit_cap_enabled=False)._leg_volume_cap("X", "BUY", 2) is None


def test_new_switches_defaults():
    cfg = LiveTradingConfig()
    assert cfg.leg_volume_limit_cap_enabled is True
    assert cfg.ict_virtual_limit_one_shot is True


class FakeMT5:
    ORDER_TYPE_BUY, ORDER_TYPE_SELL, ORDER_TYPE_BUY_LIMIT, ORDER_TYPE_SELL_LIMIT = 0, 1, 2, 3
    ORDER_TYPE_BUY_STOP, ORDER_TYPE_SELL_STOP, ORDER_TYPE_BUY_STOP_LIMIT = 4, 5, 6
    POSITION_TYPE_BUY, POSITION_TYPE_SELL = 0, 1

    def __init__(self, positions=(), orders=()):
        self._positions, self._orders = positions, orders

    def positions_get(self, symbol=None):
        return self._positions

    def orders_get(self, symbol=None):
        return self._orders


def provider_with(info, monkeypatch, fake=None, risk_per_lot=1.0):
    provider = object.__new__(MT5ExecutionProvider)
    provider._ensure = lambda: None
    provider.symbol_spec = lambda symbol: info
    provider.calculate_risk_amount = lambda symbol, direction, volume, entry_price, stop_loss: {
        "actual_risk_amount": volume * risk_per_lot, "broker_profit_at_stop": -volume * risk_per_lot}
    if fake is not None:
        monkeypatch.setattr(mt5_execution, "mt5", fake)
    return provider


V250 = SimpleNamespace(volume_min=10.0, volume_max=30.0, volume_step=0.001, volume_limit=50.0)


def test_symbol_volume_headroom_counts_same_direction_positions_and_orders(monkeypatch):
    fake = FakeMT5(positions=(SimpleNamespace(type=0, volume=12.0), SimpleNamespace(type=1, volume=30.0)),
                   orders=(SimpleNamespace(type=2, volume_current=3.0), SimpleNamespace(type=3, volume_current=5.0)))
    provider = provider_with(V250, monkeypatch, fake)
    assert provider.symbol_volume_headroom("Volatility 250 (1s) Index", "BUY") == {
        "volume_limit": 50.0, "used_volume": 15.0, "headroom": 35.0}
    assert provider.symbol_volume_headroom("Volatility 250 (1s) Index", "SELL")["headroom"] == 15.0


def test_symbol_volume_headroom_without_limit(monkeypatch):
    info = SimpleNamespace(volume_min=0.01, volume_max=100.0, volume_step=0.01, volume_limit=0.0)
    assert provider_with(info, monkeypatch, FakeMT5()).symbol_volume_headroom("EURUSD", "BUY")["headroom"] is None


def test_calculate_volume_respects_leg_cap(monkeypatch):
    provider = provider_with(V250, monkeypatch)
    uncapped = provider.calculate_volume("Volatility 250 (1s) Index", "BUY", 100.0, 99.0, 40.0)
    assert uncapped["volume"] == 30.0  # volume_max por orden: dos piernas = 60 > volume_limit 50 -> 10034
    capped = provider.calculate_volume("Volatility 250 (1s) Index", "BUY", 100.0, 99.0, 40.0, max_volume_cap=25.0)
    assert capped["volume"] == 25.0 and capped["actual_risk_amount"] == 25.0


def test_calculate_volume_cap_below_minimum_is_rejected(monkeypatch):
    provider = provider_with(V250, monkeypatch)
    with pytest.raises(MT5ExecutionError, match="VOLUME_LIMIT_HEADROOM"):
        provider.calculate_volume("Volatility 250 (1s) Index", "BUY", 100.0, 99.0, 40.0, max_volume_cap=5.0)


# --- 2. Límite virtual ICT: un límite caducado o invalidado no se recrea con la misma señal -------------------------

def test_invalidated_limit_is_not_recreated_for_same_signal():
    engine, _ = make_engine([signal_analysis("BUY", 100.0, 98.0), signal_analysis("BUY", 100.0, 98.0),
                             signal_analysis("BUY", 100.0, 98.0)],
                            [(100.5, 100.6), (97.9, 98.0), (99.9, 100.0)], BAR + timedelta(minutes=16))
    engine._ict_analysis_with_virtual_limit("Jump 25 Index")
    assert engine._ict_analysis_with_virtual_limit("Jump 25 Index")["action"] == "ICT_VIRTUAL_LIMIT_INVALIDATED"
    # El precio vuelve al límite en la misma vela de señal: el replay ya habría perdido -1R; no se abre.
    again = engine._ict_analysis_with_virtual_limit("Jump 25 Index")
    assert again["valid"] is False and again["action"] == "ICT_VIRTUAL_LIMIT_CONSUMED"
    assert [a[0] for a in engine.audits].count("CREATED") == 1


def test_newer_signal_after_invalidation_creates_new_limit():
    newer = signal_analysis("BUY", 101.0, 99.0, bar=BAR + timedelta(minutes=15))
    engine, _ = make_engine([signal_analysis("BUY", 100.0, 98.0), none_signal(), newer],
                            [(100.5, 100.6), (97.9, 98.0), (101.5, 101.6)], BAR + timedelta(minutes=31))
    engine._ict_analysis_with_virtual_limit("Jump 25 Index")
    engine._ict_analysis_with_virtual_limit("Jump 25 Index")
    assert engine._ict_analysis_with_virtual_limit("Jump 25 Index")["action"] == "ICT_VIRTUAL_LIMIT_WAITING"
    assert engine._ict_virtual_limits["Jump 25 Index"]["limit"] == 101.0


def test_triggered_signal_can_retry_in_same_bar():
    """Disparada pero bloqueada por algo pasajero: se puede reintentar (la clave de ejecución evita duplicados)."""
    engine, _ = make_engine([signal_analysis(), signal_analysis()], [(99.9, 100.0), (99.9, 100.0)],
                            BAR + timedelta(minutes=16))
    assert engine._ict_analysis_with_virtual_limit("Volatility 75 Index")["valid"] is True
    assert engine._ict_analysis_with_virtual_limit("Volatility 75 Index")["valid"] is True


def test_one_shot_switch_off_restores_recreation():
    engine, _ = make_engine([signal_analysis("BUY", 100.0, 98.0), none_signal(), signal_analysis("BUY", 100.0, 98.0)],
                            [(100.5, 100.6), (97.9, 98.0), (100.5, 100.6)], BAR + timedelta(minutes=16),
                            ict_virtual_limit_one_shot=False)
    engine._ict_analysis_with_virtual_limit("Jump 25 Index")
    engine._ict_analysis_with_virtual_limit("Jump 25 Index")
    assert engine._ict_analysis_with_virtual_limit("Jump 25 Index")["action"] == "ICT_VIRTUAL_LIMIT_WAITING"


# --- 3. Dashboard: peticiones de otras webs -------------------------------------------------------------------------

OK_POST = {"Host": "127.0.0.1:8765", "Origin": "http://127.0.0.1:8765", "Content-Type": "application/json",
           "Content-Length": "20"}


def test_same_origin_json_post_is_accepted():
    assert unsafe_request_reason(OK_POST, "POST", "127.0.0.1") is None
    assert unsafe_request_reason({**OK_POST, "Host": "localhost:8765", "Origin": "http://localhost:8765"},
                                 "POST", "127.0.0.1") is None
    assert unsafe_request_reason({"Host": "127.0.0.1:8765", "Content-Type": "application/json; charset=utf-8",
                                  "Content-Length": "2"}, "POST", "127.0.0.1") is None  # sin Origin (urllib/tests)


@pytest.mark.parametrize("headers,reason", [
    ({**OK_POST, "Content-Type": "text/plain"}, "CONTENT_TYPE_MUST_BE_JSON"),
    ({**OK_POST, "Origin": "https://evil.example"}, "ORIGIN_NOT_ALLOWED"),
    ({**OK_POST, "Origin": "null"}, "ORIGIN_NOT_ALLOWED"),
    ({**OK_POST, "Sec-Fetch-Site": "cross-site"}, "CROSS_SITE_REQUEST"),
    ({**OK_POST, "Host": "rebind.evil.example:8765"}, "HOST_NOT_ALLOWED"),
    ({**OK_POST, "Content-Length": str(2 * 1024 * 1024)}, "PAYLOAD_TOO_LARGE"),
])
def test_cross_site_posts_are_rejected(headers, reason):
    assert unsafe_request_reason(headers, "POST", "127.0.0.1") == reason


def test_dns_rebinding_get_is_rejected_but_local_get_allowed():
    assert unsafe_request_reason({"Host": "rebind.evil.example:8765"}, "GET", "127.0.0.1") == "HOST_NOT_ALLOWED"
    assert unsafe_request_reason({"Host": "127.0.0.1:8765"}, "GET", "127.0.0.1") is None


def test_guard_switch_off(monkeypatch):
    monkeypatch.setenv("DAEMONBLACKFX_DASHBOARD_STRICT_REQUESTS", "0")
    assert unsafe_request_reason({**OK_POST, "Content-Type": "text/plain"}, "POST", "127.0.0.1") is None


def test_dashboard_rejects_text_plain_post_end_to_end(tmp_path):
    import json
    import urllib.error
    import urllib.request
    from dashboard.realtime_dashboard import RealtimeDashboardService
    dash = RealtimeDashboardService(repository=None, host="127.0.0.1", port=0, state_path=tmp_path / "s.json")
    dash.news_service.start = lambda: None
    dash.news_service.stop = lambda: None
    dash.start(live=False)
    try:
        request = urllib.request.Request(dash.url + "/api/workers/VOLATILITY_1/enabled",
                                         data=b'{"enabled": false}', headers={"Content-Type": "text/plain"})
        with pytest.raises(urllib.error.HTTPError) as err:
            urllib.request.urlopen(request, timeout=5)
        assert err.value.code == 403
        assert json.loads(err.value.read().decode("utf-8"))["error_code"] == "CONTENT_TYPE_MUST_BE_JSON"
    finally:
        dash.stop()


def test_dashboard_hot_sync_is_off_by_default(monkeypatch):
    from dashboard.strategy_bases_page import dashboard_hot_sync_enabled
    monkeypatch.delenv("DAEMONBLACKFX_DASHBOARD_HOT_SYNC", raising=False)
    assert dashboard_hot_sync_enabled() is False
    monkeypatch.setenv("DAEMONBLACKFX_DASHBOARD_HOT_SYNC", "1")
    assert dashboard_hot_sync_enabled() is True


# --- 4. Detección de sintéticos única ------------------------------------------------------------------------------

@pytest.mark.parametrize("symbol,expected", [
    ("DEX 1500 UP Index", True), ("Trek Up Index", True), ("Exponential Growth Index 1", True),
    ("Snap 50 Index", True), ("Vol over Boom 550", True), ("Volatility 250 (1s) Index", True),
    ("Germany 40 Index", False), ("US Dollar Index", False), ("EURUSD", False), ("US SP 500", False),
    ("XAUUSD", False),
])
def test_single_synthetic_detection(symbol, expected):
    assert is_synthetic_asset(symbol) is expected
    assert is_synthetic_symbol(symbol) is expected
