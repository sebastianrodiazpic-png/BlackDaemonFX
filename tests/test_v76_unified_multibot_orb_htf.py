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


def test_orb_buy_is_blocked_against_bearish_h1_and_m15():
    e=_engine("BEARISH","bos_bearish")
    c=e._orb_higher_timeframe_context("XAUUSD","BUY")
    assert c["blocked"] is True
    assert c["h1_alignment"] is False
    assert c["m15_alignment"] is False
    assert c["reason"]=="ORB_BREAKOUT_CONTRA_H1_Y_M15"


def test_orb_sell_is_aligned_with_bearish_context():
    e=_engine("BEARISH","bos_bearish")
    c=e._orb_higher_timeframe_context("Wall Street 30","SELL")
    assert c["blocked"] is False
    assert c["h1_alignment"] is True
    assert c["m15_alignment"] is True


def test_neutral_h1_does_not_block_orb():
    e=_engine("RANGE",None)
    c=e._orb_higher_timeframe_context("XAUUSD","BUY")
    assert c["blocked"] is False
    assert c["h1_alignment"] is None


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


def test_orb_live_audit_includes_htf_context():
    root=Path(__file__).resolve().parents[1]
    text=(root/"strategy"/"execution"/"live_trading_engine.py").read_text(encoding="utf-8")
    assert 'view["higher_timeframe_context"] = htf_context' in text
    assert 'view["h1_trend"] = htf_context.get("h1_trend")' in text
    assert 'view["structure_break"] = htf_context.get("m15_structure")' in text
