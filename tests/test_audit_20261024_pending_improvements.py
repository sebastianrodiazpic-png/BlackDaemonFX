"""Mejoras pendientes sin riesgo de la auditoría del 24-oct-2026 (ver REGISTRO_CAMBIOS_ESTRATEGIA.md)."""
import importlib
from types import SimpleNamespace

import pandas as pd
import pytest

from strategy.ict.config import ICTSabriMalleConfig
from strategy.ict.ict_strategy import ICTSabriMalleStrategy, build_h4_candles_from_h1
from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
from tests.test_ict_closed_candles_only import LiveLikeProvider, _random_walk_m15


# --- IA de Malaysian SNR con modelo incompatible: observar (solo DEMO) por defecto -----------------------------------

def test_msnr_incompatible_ai_defaults_to_observe(monkeypatch):
    import strategy.malaysian_snr.runtime_settings as rs
    monkeypatch.delenv("DAEMONBLACKFX_MSNR_AI_INCOMPATIBLE_DEFAULT", raising=False)
    rs = importlib.reload(rs)
    assert rs.msnr_default_settings()["ai_incompatible_policy"] == "observe"
    from strategy.malaysian_snr.config import MalaysianSNRConfig
    assert MalaysianSNRConfig().ai_incompatible_policy == "observe"


@pytest.mark.parametrize("raw,expected", [("block", "block"), ("BLOCK", "block"), ("nonsense", "observe")])
def test_msnr_incompatible_ai_default_switch(monkeypatch, raw, expected):
    import strategy.malaysian_snr.runtime_settings as rs
    monkeypatch.setenv("DAEMONBLACKFX_MSNR_AI_INCOMPATIBLE_DEFAULT", raw)
    try:
        assert importlib.reload(rs).msnr_default_settings()["ai_incompatible_policy"] == expected
    finally:
        monkeypatch.delenv("DAEMONBLACKFX_MSNR_AI_INCOMPATIBLE_DEFAULT", raising=False)
        importlib.reload(rs)


def test_msnr_observe_exception_is_demo_only():
    from strategy.malaysian_snr import ai_policy
    source = open(ai_policy.__file__, encoding="utf-8").read()
    assert "settings['ai_incompatible_policy']=='observe' and str(source).upper()=='DEMO'" in source


# --- ICT: datos reales para la IA sin tocar los campos que usa la operativa ----------------------------------------

def _first_valid_ict_signal(cfg=None):
    m15 = _random_walk_m15()
    provider = LiveLikeProvider(m15, include_forming=False)
    strategy = ICTSabriMalleStrategy(provider, cfg or ICTSabriMalleConfig())
    for i in range(1500, len(m15) - 1, 3):
        provider.now = m15["time"].iloc[i] + pd.Timedelta(minutes=15)
        result = strategy.analyze_symbol("Volatility 75 Index", provider.now.to_pydatetime())
        if result.get("valid"):
            return result["signal"]
    pytest.skip("la serie sintética no produjo señal ICT")


def test_ict_signal_carries_real_features_and_keeps_legacy_fields():
    signal = _first_valid_ict_signal()
    features = signal["ict_real_features"]
    assert signal["adx"] == 28.0 and signal["confirmation_percentage"] == 95.0  # operativa validada, sin cambios
    assert features["adx_h1"] is not None and 0 <= features["adx_h1"] <= 100
    assert features["atr_h1"] > 0 and features["sl_atr_h1"] > 0 and features["range_atr_h1"] > 0
    assert features["spread_sl"] is not None and features["spread_sl"] >= 0


def test_ict_h4_candle_count_is_configurable(monkeypatch):
    assert ICTSabriMalleConfig().macro_h4_candles == 300

    calls = []

    class Recorder(LiveLikeProvider):
        def get_candles(self, symbol, timeframe, count=100):
            calls.append((timeframe, count))
            return super().get_candles(symbol, timeframe, count)

    m15 = _random_walk_m15()
    provider = Recorder(m15, include_forming=False)
    provider.now = m15["time"].iloc[2500] + pd.Timedelta(minutes=15)
    ICTSabriMalleStrategy(provider, ICTSabriMalleConfig(macro_h4_candles=401)).analyze_symbol(
        "Volatility 75 Index", provider.now.to_pydatetime())
    assert ("H4", 401) in calls or not any(tf == "H4" for tf, _ in calls)


def test_h4_from_h1_drops_forming_bucket(monkeypatch):
    times = pd.date_range("2026-10-20 00:00", periods=6, freq="1h", tz="UTC")  # 00-03 completo, 04-05 a medias
    h1 = pd.DataFrame({"time": times, "open": range(6), "high": range(1, 7), "low": range(6), "close": range(6)})
    monkeypatch.delenv("DAEMONBLACKFX_ICT_H4_COMPLETE_ONLY", raising=False)
    h4 = build_h4_candles_from_h1(h1)
    assert list(h4["time"]) == [pd.Timestamp("2026-10-20 00:00", tz="UTC")]
    full = pd.DataFrame({"time": pd.date_range("2026-10-20 00:00", periods=8, freq="1h", tz="UTC"),
                         "open": range(8), "high": range(1, 9), "low": range(8), "close": range(8)})
    assert len(build_h4_candles_from_h1(full)) == 2
    monkeypatch.setenv("DAEMONBLACKFX_ICT_H4_COMPLETE_ONLY", "0")
    assert len(build_h4_candles_from_h1(h1)) == 2


def test_shared_adx_matches_msnr_and_engine_import_works():
    from strategy.indicators import calculate_adx
    from strategy.malaysian_snr.malaysian_snr_strategy import compute_adx
    m15 = _random_walk_m15(400)
    pd.testing.assert_series_equal(calculate_adx(m15), compute_adx(m15))
    assert calculate_adx(m15).dropna().between(0, 100).all()


# --- Criterios de las pruebas demo sin cierres manuales ------------------------------------------------------------

def _repo_with_ops(tmp_path):
    from database.repository import TradingRepository
    repo = TradingRepository(db_path=tmp_path / "demo.sqlite3")
    ops = {"A": ("mt5_tp", "mt5_tp", 50.0, 100.0), "B": ("mt5_tp", "mt5_mobile", 50.0, 60.0),
           "C": ("mt5_sl", "mt5_sl", -50.0, -50.0)}
    for name, (r1, r2, p1, p2) in ops.items():
        for leg, reason, pnl in (("TP1", r1, p1), ("RUNNER", r2, p2)):
            trade_id, _ = repo.create_trade_once({
                "execution_key": f"DEMO:X:{name}:{leg}", "source": "DEMO", "broker": "MT5", "instrument": "X",
                "timeframe": "M15", "direction": "BUY", "status": "OPEN", "entry_time": "2026-10-21T10:00:00+00:00",
                "entry_price": 100.0, "stop_loss": 99.0, "take_profit": 102.0, "volume": 1.0, "planned_rr": 2.0,
                "risk_percent": 0.5, "risk_amount": 50.0, "strategy_version": "v-test", "details": {}})
            repo.close_trade(trade_id, {"status": "CLOSED", "exit_time": "2026-10-21T12:00:00+00:00",
                                        "exit_price": 101.0, "net_pnl": pnl, "exit_reason": reason})
    return repo


def test_demo_criteria_exclude_operations_with_manual_legs(tmp_path, monkeypatch):
    monkeypatch.delenv("DAEMONBLACKFX_DEMO_TEST_EXCLUDE_MANUAL", raising=False)
    repo = _repo_with_ops(tmp_path)
    everything = sorted(repo.closed_operations_r(None, strategy_version="v-test", exclude_manual=False))
    if not everything:
        pytest.skip("el repositorio de prueba no replica el diario de operaciones")
    assert everything == sorted([1.5, 1.1, -1.0])
    assert sorted(repo.closed_operations_r(None, strategy_version="v-test")) == sorted([1.5, -1.0])
    monkeypatch.setenv("DAEMONBLACKFX_DEMO_TEST_EXCLUDE_MANUAL", "0")
    assert len(repo.closed_operations_r(None, strategy_version="v-test")) == 3


# --- Tope de riesgo por factor (renta variable US) ------------------------------------------------------------------

def factor_engine(open_trades, **cfg):
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(bot_profile="RSI2", risk_percent=1.0, **cfg)
    engine.repository = SimpleNamespace(open_trades=lambda source=None: list(open_trades))
    return engine


def leg(symbol, risk=0.5, be=False):
    return {"instrument": symbol, "risk_percent": risk, "details": {"metadata": {"break_even_confirmed": be}}}


def test_factor_cap_is_off_by_default():
    engine = factor_engine([leg("US SP 500")] * 10)
    assert engine.config.us_equity_risk_cap_percent == 0.0
    assert engine._factor_risk_guard("US Tech 100", "k") is None


def test_factor_cap_blocks_fourth_us_operation_but_not_other_markets():
    open_legs = [leg(s) for s in ("US SP 500", "US Tech 100", "Wall Street 30") for _ in range(2)]  # 3 % abierto
    engine = factor_engine(open_legs, us_equity_risk_cap_percent=3.0)
    blocked = engine._factor_risk_guard("US Small Cap 2000", "k")
    assert blocked["action"] == "FACTOR_RISK_CAP_REACHED" and blocked["open_risk_percent"] == 3.0
    assert engine._factor_risk_guard("Volatility 75 Index", "k") is None


def test_factor_cap_ignores_legs_already_at_break_even():
    open_legs = [leg("US SP 500", be=True)] * 4 + [leg("US Tech 100")] * 2  # solo 1 % en riesgo real
    engine = factor_engine(open_legs, us_equity_risk_cap_percent=3.0)
    assert engine._factor_risk_guard("Wall Street 30", "k") is None


# --- Centinela de régimen en ORB: observa sin vetar (prueba demo) ---------------------------------------------------

def orb_engine(**cfg):
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(bot_profile="ORB", **cfg)
    return engine


def test_orb_regime_sentinel_observes_by_default():
    engine = orb_engine()
    assert engine.config.market_regime_orb_mode == "OBSERVE"
    assert engine._market_regime_observe_only("XAUUSD") is True


def test_orb_regime_sentinel_filter_switch_and_other_workers_unchanged():
    assert orb_engine(market_regime_orb_mode="FILTER")._market_regime_observe_only("XAUUSD") is False
    gold = object.__new__(LiveTradingEngine)
    gold.config = LiveTradingConfig(bot_profile="GOLD")
    assert gold._market_regime_observe_only("XAUUSD") is False


# --- Dashboard: gráficos de posiciones bajo demanda ------------------------------------------------------------------

def _state_with_positions():
    chart = {"timeframes": {"M15": {"candles": [{"time": 1, "open": 1, "high": 2, "low": 0, "close": 1}] * 50}}}
    return {"open_positions": [{"id": 7, "symbol": "Volatility 75 Index", "chart": chart, "entry_chart": chart},
                               {"id": 8, "symbol": "Boom 500 Index", "chart": {}, "entry_chart": {}}],
            "account": {"snapshot": {"balance": 1}, "recent_trades": [1] * 10}}


def test_light_state_drops_position_charts_but_flags_them(monkeypatch):
    from dashboard.realtime_dashboard import _light_state_payload
    monkeypatch.delenv("DAEMONBLACKFX_DASHBOARD_LAZY_CHARTS", raising=False)
    state = _state_with_positions()
    light = _light_state_payload(state)
    first, second = light["open_positions"]
    assert first["chart"] == {} and first["entry_chart"] == {} and first["charts_lazy"] is True
    assert first["chart_available"] is True and second["chart_available"] is False
    assert state["open_positions"][0]["chart"]  # el estado original no se toca
    monkeypatch.setenv("DAEMONBLACKFX_DASHBOARD_LAZY_CHARTS", "0")
    assert _light_state_payload(_state_with_positions())["open_positions"][0]["chart"]


def test_position_charts_endpoint(tmp_path):
    import json
    import urllib.error
    import urllib.request
    from dashboard.realtime_dashboard import RealtimeDashboardService
    dash = RealtimeDashboardService(repository=None, host="127.0.0.1", port=0, state_path=tmp_path / "s.json")
    dash.news_service.start = lambda: None
    dash.news_service.stop = lambda: None
    dash.snapshot = lambda force=False: _state_with_positions()
    dash.start(live=False)
    try:
        with urllib.request.urlopen(dash.url + "/api/open-positions/7/charts", timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
        assert data["ok"] is True and data["chart"]["timeframes"]["M15"]["candles"]
        with urllib.request.urlopen(dash.url + "/api/state", timeout=5) as response:
            state = json.loads(response.read().decode("utf-8"))
        assert state["open_positions"][0]["chart"] == {} and state["open_positions"][0]["chart_available"] is True
        with pytest.raises(urllib.error.HTTPError) as err:
            urllib.request.urlopen(dash.url + "/api/open-positions/999/charts", timeout=5)
        assert err.value.code == 404
    finally:
        dash.stop()


# --- ICT: una señal disparada que no se abre ocupa el símbolo (como en el replay) -----------------------------------

def _triggered_engine(**cfg):
    from datetime import timedelta as _td
    from tests.test_ict_virtual_limit_entry import BAR, make_engine, signal_analysis
    engine, _ = make_engine([signal_analysis()], [(99.9, 100.0)], BAR + _td(minutes=16), **cfg)
    assert engine._ict_analysis_with_virtual_limit("Volatility 75 Index")["valid"] is True
    return engine


@pytest.mark.parametrize("action", ["MAX_TOTAL_OPEN_POSITIONS", "OPERACION_RECHAZADA_POR_RIESGO",
                                    "EXECUTABLE_RR_BLOCKED", "BLOCKED_SYMBOL_CYCLE"])
def test_triggered_but_not_opened_signal_occupies_symbol(action):
    engine = _triggered_engine()
    lock = engine._register_ict_trigger_block_lock("Volatility 75 Index", {"action": action})
    assert lock is not None and lock["entry"] == 100.0 and lock["stop"] == 98.0
    assert lock["reason"] == f"ICT_SIGNAL_TRIGGERED_NOT_OPENED:{action}"
    assert "Volatility 75 Index" in engine._ict_spread_locks


@pytest.mark.parametrize("action", ["SPLIT_ORDER_OPENED", "ORDER_OPENED", "ALREADY_EXECUTED", "DRY_RUN_VALIDATED"])
def test_opened_signal_does_not_create_virtual_lock(action):
    engine = _triggered_engine()
    assert engine._register_ict_trigger_block_lock("Volatility 75 Index", {"action": action}) is None
    assert "Volatility 75 Index" not in engine.__dict__.get("_ict_spread_locks", {})


def test_trigger_lock_switch_off_and_consumed_once():
    engine = _triggered_engine(ict_trigger_block_lock_enabled=False)
    assert engine._register_ict_trigger_block_lock("Volatility 75 Index", {"action": "MAX_TOTAL_OPEN_POSITIONS"}) is None
    engine = _triggered_engine()
    engine._register_ict_trigger_block_lock("Volatility 75 Index", {"action": "SPLIT_ORDER_OPENED"})
    # el disparo se consume: un resultado posterior sin nuevo disparo no ocupa el símbolo
    assert engine._register_ict_trigger_block_lock("Volatility 75 Index", {"action": "MAX_TOTAL_OPEN_POSITIONS"}) is None


def test_process_symbol_registers_lock_when_triggered_signal_is_blocked():
    engine = _triggered_engine()
    engine._process_symbol_impl = lambda symbol, sync: {"symbol": symbol, "action": "MAX_TOTAL_OPEN_POSITIONS"}
    engine.process_symbol("Volatility 75 Index")
    assert "Volatility 75 Index" in engine._ict_spread_locks


# --- Malaysian SNR: filtro de régimen con tramos de ADX que SÍ operan (pre-registrado) -------------------------------

def msnr_regime_engine(**cfg):
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(bot_profile="MALAYSIAN_SNR", msnr_regime_filter_mode="live", **cfg)
    engine._msnr_regime_filter_status = lambda force=False: {"verdict": "EN_PRUEBA"}
    engine._persist_audit_event = lambda *a, **k: None
    return engine


@pytest.mark.parametrize("adx,blocked", [(10, False), (24, False), (26, True), (40, True), (41, False)])
def test_msnr_regime_default_band_unchanged(adx, blocked):
    engine = msnr_regime_engine()
    assert engine.config.msnr_regime_adx_keep_bands == ""
    result = engine._msnr_regime_filter_gate("Step Index 500", {"adx": adx, "entry_confirmation": "M15_ZONE_REJECTION_CLOSE"},
                                             "MALAYSIAN_SNR")
    assert (result is not None) is blocked


@pytest.mark.parametrize("adx,blocked", [(10, False), (15, False), (16, True), (30, True), (45, False), (50, False), (55, True)])
def test_msnr_regime_keep_bands_mode(adx, blocked):
    engine = msnr_regime_engine(msnr_regime_adx_keep_bands="0-15,40-50")
    result = engine._msnr_regime_filter_gate("Step Index 500", {"adx": adx, "entry_confirmation": "M15_ZONE_REJECTION_CLOSE"},
                                             "MALAYSIAN_SNR")
    assert (result is not None) is blocked
    if blocked:
        assert result["reason"] == "MSNR_REGIME_KEEPS_ONLY_ADX_0-15,40-50"


def test_msnr_regime_keep_bands_ignores_malformed_text():
    engine = msnr_regime_engine(msnr_regime_adx_keep_bands="abc,30-20")
    assert engine._msnr_regime_keep_bands() == []


def test_h4h1_scenario_stays_synthetics_only_by_default():
    from strategy.malaysian_snr.config import MalaysianSNRConfig
    from strategy.malaysian_snr.malaysian_snr_strategy import MalaysianSNRStrategy
    from strategy.malaysian_snr.video_strategy import MSNRVideoConfig, MSNRVideoStrategy
    assert MalaysianSNRConfig().h4h1_synthetics_only is True
    assert MSNRVideoStrategy(None)._engine.config.h4h1_synthetics_only is True
    assert MSNRVideoStrategy(None, MSNRVideoConfig(synthetics_only=False))._engine.config.h4h1_synthetics_only is False
    strategy = MalaysianSNRStrategy(None, MalaysianSNRConfig(enable_h4h1_confirmation=True))
    assert strategy._h4h1_signal("EURUSD") is None  # mercado real: no se evalúa con la configuración por defecto


# --- Malaysian SNR en mercados reales (prueba demo, sesión Asia → NY) ------------------------------------------------

def test_asia_to_ny_window():
    from strategy.malaysian_snr.video_rules import asia_to_ny_allowed
    ts = lambda s: pd.Timestamp(s, tz="America/New_York").tz_convert("UTC")
    assert asia_to_ny_allowed(ts("2026-10-26 19:30")) is True    # lunes, apertura de Tokio
    assert asia_to_ny_allowed(ts("2026-10-27 08:00")) is True    # martes, Londres/NY
    assert asia_to_ny_allowed(ts("2026-10-27 13:59")) is True
    assert asia_to_ny_allowed(ts("2026-10-27 14:00")) is False   # 3 h antes del rollover de las 17:00
    assert asia_to_ny_allowed(ts("2026-10-27 18:30")) is False   # tras el rollover, antes de Tokio
    assert asia_to_ny_allowed(ts("2026-10-30 14:30")) is False   # viernes por la tarde
    assert asia_to_ny_allowed(ts("2026-10-31 11:00")) is False   # sábado
    assert asia_to_ny_allowed(ts("2026-11-01 18:30")) is False   # domingo antes de Tokio
    assert asia_to_ny_allowed(ts("2026-11-01 19:30")) is True    # domingo, apertura de Tokio


def test_msnr_real_market_symbols_use_default_settings_and_own_version():
    from strategy.malaysian_snr.config import MSNR_REAL_STRATEGY_VERSION, MalaysianSNRConfig
    from strategy.malaysian_snr.malaysian_snr_strategy import MalaysianSNRStrategy
    calls = []
    strategy = MalaysianSNRStrategy(SimpleNamespace(get_candles=lambda *a, **k: None),
                                    MalaysianSNRConfig(synthetics_only=True, allowed_symbols=()),
                                    runtime_settings_loader=lambda: calls.append("db") or {})
    assert strategy.is_real_market_symbol("EURUSD") and not strategy.is_real_market_symbol("AUDJPY")
    result = strategy.analyze_symbol("EURUSD")
    assert calls == []  # no lee los ajustes de la base (Breaker Pair / Pinbar en live)
    assert result["strategy_version"] == MSNR_REAL_STRATEGY_VERSION and result["real_market_demo_test"] is True


def msnr_real_engine(results=None, **cfg):
    from strategy.malaysian_snr.config import MalaysianSNRConfig
    from strategy.malaysian_snr.malaysian_snr_strategy import MalaysianSNRStrategy
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(bot_profile="MALAYSIAN_SNR", **cfg)
    engine.malaysian_snr_strategy = MalaysianSNRStrategy(None, MalaysianSNRConfig(synthetics_only=True))
    engine.repository = SimpleNamespace(closed_operations_r=lambda inst, strategy_version, source, since=None: list(results or []))
    engine._persist_audit_event = lambda *a, **k: None
    engine._meta_execution_spread = lambda symbol: {"spread": 0.0001, "execution_ask": 1.1000, "execution_bid": 1.0999}
    return engine


def test_msnr_real_markets_gate_modes_and_verdict():
    assert LiveTradingConfig().msnr_real_markets_mode == "demo_test"
    engine = msnr_real_engine()
    assert engine._msnr_real_markets_gate("EURUSD", "BUY", 1.0950, "MALAYSIAN_SNR") is None   # spread 2 % < 5 %
    assert engine._msnr_real_markets_gate("Volatility 75 Index", "BUY", 1.0, "MALAYSIAN_SNR") is None
    assert msnr_real_engine(msnr_real_markets_mode="off")._msnr_real_markets_gate(
        "EURUSD", "BUY", 1.0950, "MALAYSIAN_SNR")["action"] == "MSNR_REAL_MARKETS_DISABLED"
    failed = msnr_real_engine(results=[-0.2] * 40)
    assert failed._msnr_real_markets_gate("EURUSD", "BUY", 1.0950, "MALAYSIAN_SNR")["action"] == "MSNR_REAL_DEMO_TEST_FAILED"
    passed = msnr_real_engine(results=[0.1] * 40)
    assert passed._msnr_real_markets_status()["verdict"] == "SUPERA"


def test_msnr_real_markets_spread_cap():
    engine = msnr_real_engine()
    blocked = engine._msnr_real_markets_gate("EURUSD", "BUY", 1.0998, "MALAYSIAN_SNR")  # spread 50 % del stop
    assert blocked["action"] == "MSNR_REAL_SPREAD_TO_SL_EXCEEDED"


def test_msnr_real_markets_skip_filters_not_in_their_replay():
    engine = msnr_real_engine(msnr_regime_filter_mode="live")
    engine._msnr_regime_filter_status = lambda force=False: {}
    assert engine._msnr_regime_filter_gate("EURUSD", {"adx": 30, "entry_confirmation": "X"}, "MALAYSIAN_SNR") is None
    assert engine._market_regime_observe_only("EURUSD") is True
    assert engine._market_regime_observe_only("AUDJPY") is False


def test_msnr_universe_includes_real_market_demo_symbols():
    from config.ict_instrument_policy import MALAYSIAN_SNR_ACTIVE, sanitize_ict_selection
    assert {"EURUSD", "XAUUSD", "Germany 40"} <= set(MALAYSIAN_SNR_ACTIVE)
    assert sanitize_ict_selection("MALAYSIAN_SNR", ["EURUSD", "AUDJPY"]) == ["EURUSD"]


def test_msnr_real_markets_user_selection_and_per_symbol_session():
    from strategy.malaysian_snr.config import MalaysianSNRConfig
    from strategy.malaysian_snr.malaysian_snr_strategy import MalaysianSNRStrategy
    strategy = MalaysianSNRStrategy(None)
    # Decisión del usuario (25-oct-2026): acierto > 47 % en el replay con el cierre de las 16:45 NY.
    # Más los forex con acierto > 47 % en el replay fiel de 3 años, medidos en Londres + NY (legacy_utc).
    added_fx = {"NZDUSD", "GBPCAD", "AUDUSD", "CADCHF", "EURGBP", "GBPCHF", "CADJPY", "GBPJPY", "CHFJPY"}
    assert set(MalaysianSNRConfig().real_market_symbols) == {"Germany 40", "XAUUSD", "USDJPY", "GBPUSD", "EURUSD", *added_fx}
    for symbol in ("Germany 40", "XAUUSD", "USDJPY", "GBPUSD"):
        assert strategy.real_market_session_policy(symbol) == "asia_to_ny"
    for symbol in ("EURUSD", *added_fx):
        assert strategy.real_market_session_policy(symbol) == "legacy_utc"
    for symbol in ("US SP 500", "US Tech 100", "EURJPY", "USDCAD", "Wall Street 30"):
        assert not strategy.is_real_market_symbol(symbol)
    custom = MalaysianSNRStrategy(None, MalaysianSNRConfig(real_market_session_overrides="XAUUSD:legacy_utc"))
    assert custom.real_market_session_policy("XAUUSD") == "legacy_utc"
    assert custom.real_market_session_policy("EURUSD") == "asia_to_ny"


def _msnr_with_db_settings(asset_modes, **config):
    from strategy.malaysian_snr.config import MalaysianSNRConfig
    from strategy.malaysian_snr.malaysian_snr_strategy import MalaysianSNRStrategy
    from strategy.malaysian_snr.runtime_settings import msnr_default_settings
    raw = {**msnr_default_settings(), "asset_modes": asset_modes, "additional_symbols": ["Jump 50 Index"],
           "additional_symbols_mode": "live", "version": 7}
    return MalaysianSNRStrategy(None, MalaysianSNRConfig(allowed_symbols=(), **config), lambda: dict(raw))


def test_msnr_instruments_tab_is_the_only_control_by_default(monkeypatch):
    """25-oct-2026: un «off» en los ajustes de la base ya no quita un instrumento marcado en /Instruments."""
    from types import SimpleNamespace
    from strategy.malaysian_snr.runtime_engine import cycle_symbols
    monkeypatch.delenv("DAEMONBLACKFX_MSNR_INSTRUMENTS_CONTROL", raising=False)
    strategy = _msnr_with_db_settings({"Boom 900 Index": "off", "Jump 75 Index": "shadow", "Crash 300 Index": "live"})
    snap = strategy.settings_snapshot()
    assert snap["asset_modes"] == {} and snap["additional_symbols_mode"] == "off" and snap["version"] == 7
    engine = SimpleNamespace(malaysian_snr_strategy=strategy)
    selected = ["Boom 900 Index", "Jump 75 Index", "XAUUSD"]
    # Solo lo seleccionado, en su orden: ni los «off» salen ni los «live»/adicionales no seleccionados entran.
    assert cycle_symbols(engine, selected) == selected
    assert strategy.analyze_symbol("Boom 900 Index").get("reason") != "MSNR_SYMBOL_DISABLED"


def test_msnr_instruments_control_switch_restores_asset_modes(monkeypatch):
    from types import SimpleNamespace
    from strategy.malaysian_snr.runtime_engine import cycle_symbols
    modes = {"Boom 900 Index": "off", "Crash 300 Index": "live"}
    monkeypatch.setenv("DAEMONBLACKFX_MSNR_INSTRUMENTS_CONTROL", "off")
    strategy = _msnr_with_db_settings(modes)
    assert strategy.settings_snapshot()["asset_modes"] == modes
    symbols = cycle_symbols(SimpleNamespace(malaysian_snr_strategy=strategy), ["Boom 900 Index", "XAUUSD"])
    assert "Boom 900 Index" not in symbols and {"Crash 300 Index", "Jump 50 Index"} <= set(symbols)
    assert strategy.analyze_symbol("Boom 900 Index")["reason"] == "MSNR_SYMBOL_DISABLED"
    # El campo de la config manda sobre la variable.
    monkeypatch.setenv("DAEMONBLACKFX_MSNR_INSTRUMENTS_CONTROL", "on")
    assert _msnr_with_db_settings(modes, instruments_tab_control=False).settings_snapshot()["asset_modes"] == modes
