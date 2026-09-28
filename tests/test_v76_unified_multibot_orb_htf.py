from pathlib import Path
from types import SimpleNamespace

from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine


class FakeMTF:
    def __init__(self, trend="BEARISH", structure="bos_bearish"):
        self.trend=trend
        self.structure=structure
    def analyze_symbol(self, symbol):
        return {
            "action":"NO_M5_SETUP",
            "h1":{"context":{"trend":self.trend,"valid":True}},
            "m15":{"setup":{"structure_break_type":self.structure}},
            "h1_trend":self.trend,
            "m15_structure_break_type":self.structure,
        }


def _engine(trend="BEARISH", structure="bos_bearish"):
    e=object.__new__(LiveTradingEngine)
    e.config=LiveTradingConfig(
        bot_profile="ORB",
        orb_htf_context_enabled=True,
        orb_require_h1_alignment=True,
        orb_use_m15_context=True,
    )
    e.multi_timeframe=FakeMTF(trend,structure)
    return e


def test_orb_context_does_not_call_smc_even_with_legacy_flags():
    for direction in ("BUY", "SELL"):
        for momentum in (False, True):
            e = _engine()
            def forbidden(symbol):
                raise AssertionError("ORB must not query SMC")
            e.multi_timeframe.analyze_symbol = forbidden
            c = e._orb_higher_timeframe_context("XAUUSD", direction, momentum=momentum)
            assert c["blocked"] is False
            assert c["enabled"] is False
            assert c["h1_alignment"] is None
            assert c["m15_alignment"] is None
            assert c["policy"] == "ORB_NATIVE_ONLY"


def test_unified_runtime_remains_available_explicitly():
    root=Path(__file__).resolve().parents[1]
    text=(root/"app"/"main.py").read_text(encoding="utf-8")
    assert 'def run_unified_multibot_daemon' in text
    assert 'if args.mode == "unified-multibot-daemon":' in text
    assert 'run_unified_multibot_daemon(args, profiles=FULL_MULTI_BOT_PROFILES)' in text


def test_unified_runtime_keeps_independent_profile_magics():
    root=Path(__file__).resolve().parents[1]
    text=(root/"app"/"main.py").read_text(encoding="utf-8")
    for magic in ("26082101","26082102","26082103","26082104","26082105","26082106",
                  "26082201","26082202","26082203","26082204","26082028"):
        assert magic in text
    assert '"runtime_mode": "UNIFIED_PROCESS"' in text


def test_unified_runtime_has_single_dashboard_and_shared_provider():
    root=Path(__file__).resolve().parents[1]
    text=(root/"app"/"main.py").read_text(encoding="utf-8")
    start=text.index("def run_unified_multibot_daemon")
    end=text.index("def run_multi_bot_daemon", start)
    block=text[start:end]
    assert block.count("RealtimeDashboardService(")==1
    assert block.count("MT5Connector()")==1
    assert "subprocess.Popen" not in block


def test_orb_open_position_audit_pauses_entry_analysis():
    from types import SimpleNamespace
    from unittest.mock import Mock
    engine=object.__new__(LiveTradingEngine)
    engine.config=LiveTradingConfig(bot_profile='ORB')
    engine.repository=SimpleNamespace(open_trades=lambda **kw:[dict(instrument='US SP 500',
        direction='BUY',details={'metadata':{'strategy_name':'ORB_NEW_YORK'}})])
    engine._trade_auditable_by_current_bot=lambda trade:True
    engine._persist_audit_event=Mock()
    engine.orb_strategy=SimpleNamespace(analyze_symbol=Mock(side_effect=AssertionError('Entry analysis while open')))
    engine._refresh_current_strategy_views()
    engine.orb_strategy.analyze_symbol.assert_not_called()
    assert engine._current_strategy_view_cache['US SP 500']['entry_analysis_paused']


def test_orb_entry_uses_native_signal_without_smc_or_score_inflation():
    from types import SimpleNamespace
    from test_demo_daemon_integration import Provider, ExecutionRepo, Executor
    engine = LiveTradingEngine(
        provider=Provider(), repository=ExecutionRepo(), executor=Executor(),
        config=LiveTradingConfig(bot_profile="ORB", execution_enabled=False),
    )
    engine.executor.get_open_positions = lambda: []
    engine.executor.get_pending_orders = lambda: []
    def forbidden(symbol):
        raise AssertionError("ORB entry queried SMC")
    engine.multi_timeframe = SimpleNamespace(analyze_symbol=forbidden)
    signal = {"direction":"BUY", "strategy_name":"ORB_NEW_YORK",
              "risk_reward_ratio":0, "confirmations":{"orb_retest_confirmed":True},
              "confirmation_percentage":80, "trade_score":80}
    engine.orb_strategy = SimpleNamespace(analyze_symbol=lambda symbol: {
        "valid":True, "strategy_name":"ORB_NEW_YORK", "signal":signal})
    result = engine.process_symbol("US SP 500")
    assert result["action"] == "RR_TOO_LOW"
    assert signal["confirmations"] == {"orb_retest_confirmed":True}
    assert signal["trade_score"] == 80
