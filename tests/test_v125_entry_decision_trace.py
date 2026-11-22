"""11-nov-2026: trazabilidad de decisiones de entrada (Criterio Humano + Tripartita + IA)."""
import os
import tempfile
from pathlib import Path

from strategy.confluence.entry_decision import (
    HC_EVENT,
    TRI_EVENT,
    aggregate_decision_events,
    aggregate_trade_decisions,
    attach_to_trade_details,
    build_entry_decision_record,
    trace_enabled,
)

HC = {
    "action": "HUMAN_CRITERIA_PASSED", "allowed": True, "mode": "FILTER", "score": 82.5, "grade": "GRADE_B_CAUTIOUS",
    "reason": "CRITERIO_HUMANO_APROBADO", "primary_veto_factor": None,
    "breakdown": {"htf_trend": 25.0, "regime_health": 20.0, "total_score": 82.5},
}
TRI = {
    "action": "APPROVED", "allowed": True, "reason": "ok", "strategy_pillar_ok": True, "human_criteria_pillar_ok": True,
    "ai_filter_pillar_ok": True, "ai_probability": 0.55, "human_criteria_score": 82.5, "is_rehabilitated_asset": False,
}
ML = {"mode": "SHADOW", "probability": 0.61, "net_expectancy_r": 0.09, "allowed": True, "shadow": True, "trained": True}


def _signal(**extra):
    sig = {"human_criteria": dict(HC), "tripartite_confluence": dict(TRI), "meta_label": dict(ML), "adx": 27.3,
           "candle_body_ratio": 0.42, "spike_danger": False}
    sig.update(extra)
    return sig


def test_record_contains_the_three_pillars_and_context():
    rec = build_entry_decision_record(symbol="GBPNZD", direction="sell", strategy_name="ict_sabri_malle",
                                      signal=_signal(), execution_key="K1", bot_profile="forex_1", adx_used=27.3)
    assert rec["schema"] == 1 and rec["direction"] == "SELL" and rec["strategy_key"] == "ICT_SABRI_MALLE"
    assert rec["execution_key"] == "K1" and rec["bot_profile"] == "FOREX_1"
    assert rec["human_criteria"]["score"] == 82.5 and rec["human_criteria"]["breakdown"]["htf_trend"] == 25.0
    assert rec["tripartite"]["action"] == "APPROVED" and rec["tripartite"]["ai_probability"] == 0.55
    assert rec["ai"]["available"] is True and rec["ai"]["probability"] == 0.61 and rec["ai"]["shadow"] is True
    assert rec["context"]["adx_used_by_gate"] == 27.3 and rec["context"]["candle_body_ratio"] == 0.42


def test_record_without_ai_or_human_criteria_marks_unavailable():
    rec = build_entry_decision_record(symbol="EURAUD", direction="BUY", strategy_name="ICT_SABRI_MALLE", signal={})
    assert rec["ai"] == {"available": False}
    assert "human_criteria" not in rec and "tripartite" not in rec


def test_attach_keeps_existing_metadata():
    details = {"metadata": {"strategy_name": "ICT", "trade_leg": "TP1"}, "sizing": {"volume": 0.02}}
    out = attach_to_trade_details(details, {"schema": 1})
    assert out["metadata"]["trade_leg"] == "TP1" and out["metadata"]["entry_decision"] == {"schema": 1}
    assert out["sizing"] == {"volume": 0.02} and "entry_decision" not in details["metadata"]  # no muta el original
    assert attach_to_trade_details(None, {"schema": 1})["metadata"]["entry_decision"] == {"schema": 1}


def test_trace_switch_off():
    old = os.environ.get("DAEMONBLACKFX_ENTRY_DECISION_TRACE")
    try:
        os.environ["DAEMONBLACKFX_ENTRY_DECISION_TRACE"] = "0"
        assert trace_enabled() is False
        os.environ["DAEMONBLACKFX_ENTRY_DECISION_TRACE"] = "1"
        assert trace_enabled() is True
    finally:
        if old is None:
            os.environ.pop("DAEMONBLACKFX_ENTRY_DECISION_TRACE", None)
        else:
            os.environ["DAEMONBLACKFX_ENTRY_DECISION_TRACE"] = old


def _ev(day, et, action, sym="X", key=None, strat=None, reason="r"):
    payload = {"strategy_key": strat} if strat else {}
    return {"event_time": f"{day}T10:00:00", "event_type": et, "action": action, "instrument": sym,
            "reason": reason, "execution_key": key, "payload": payload}


def test_aggregate_events_counts_vetoes_coverage_and_strategy():
    rows = [
        _ev("2026-11-10", TRI_EVENT, "APPROVED", key="K1", strat="ICT_SABRI_MALLE"),
        _ev("2026-11-10", TRI_EVENT, "VETO_HUMAN_CRITERIA_ADX", sym="Jump 25 Index", key="K2", strat="ICT_SABRI_MALLE"),
        _ev("2026-11-10", TRI_EVENT, "VETO_INSUFFICIENT_CONFLUENCE_WITHOUT_AI", sym="EURAUD"),
        _ev("2026-11-11", HC_EVENT, "HUMAN_CRITERIA_PASSED"),
        _ev("2026-11-11", HC_EVENT, "HUMAN_CRITERIA_COUNTERTREND_BLOCKED", sym="Step Index", key="K3"),
        _ev("2026-11-11", HC_EVENT, "HUMAN_CRITERIA_CLIMAX_BLOCKED_OBSERVED", sym="Y"),  # observado: no es veto
        _ev("2026-11-11", "OTRO_EVENTO", "VETO_X"),  # ignorado
    ]
    agg = aggregate_decision_events(rows)
    assert agg["total_events"] == 6 and agg["events_with_execution_key"] == 3
    assert agg["by_action"]["TRI:APPROVED"] == 1 and agg["by_action"]["CH:HUMAN_CRITERIA_PASSED"] == 1
    assert agg["by_day"]["2026-11-10"]["TRI:VETO_HUMAN_CRITERIA_ADX"] == 1
    assert agg["by_strategy"]["ICT_SABRI_MALLE"]["TRI:APPROVED"] == 1 and "SIN_DATO" in agg["by_strategy"]
    symbols = dict(agg["top_veto_symbols"])
    assert symbols == {"Jump 25 Index": 1, "EURAUD": 1, "Step Index": 1}
    assert len(agg["recent_vetoes"]) == 3 and agg["recent_vetoes"][0]["stage"] in ("Tripartita", "Criterio Humano")


def _trade(sym, result, rr, score=None, ai=None, with_decision=True, status="CLOSED"):
    md = {}
    if with_decision:
        md["entry_decision"] = {"strategy_key": "ICT_SABRI_MALLE", "human_criteria": {"score": score, "grade": "B"},
                                "tripartite": {"action": "APPROVED"}, "ai": {"probability": ai},
                                "context": {"adx_used_by_gate": 25.0}}
    return {"instrument": sym, "direction": "BUY", "status": status, "result": result, "realized_rr": rr,
            "entry_time": "2026-11-11T10:00:00", "details": {"metadata": md}}


def test_aggregate_trades_buckets_coverage_and_results():
    trades = [
        _trade("A", "WIN", 1.5, score=92, ai=0.9),
        _trade("B", "LOSS", -1.0, score=76, ai=0.55),
        _trade("C", "LOSS", -1.0, score=76, ai=0.55),
        _trade("D", "OPEN", 0.0, score=82, ai=0.7, status="OPEN", ),
        _trade("E", "WIN", 1.0, with_decision=False),
    ]
    agg = aggregate_trade_decisions(trades)
    assert agg["trades_total"] == 5 and agg["trades_with_decision"] == 4 and agg["coverage_pct"] == 80.0
    assert agg["overall"]["closed"] == 3 and agg["overall"]["wins"] == 1 and agg["overall"]["r_total"] == -0.5
    assert agg["by_human_score"][">=90"]["wins"] == 1
    assert agg["by_human_score"]["75-80"]["closed"] == 2 and agg["by_human_score"]["75-80"]["r_total"] == -2.0
    assert agg["by_ai_probability"]["0.50-0.60"]["trades"] == 2
    assert len(agg["recent"]) == 4


def test_repository_report_joins_events_and_trades():
    try:
        from database.repository import TradingRepository
    except Exception:
        return  # entorno sin SQLAlchemy/dependencias: se valida en Windows
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        repo = TradingRepository(db_path=Path(tmp) / "t.sqlite3")
        repo.record_audit_event(event_type=TRI_EVENT, instrument="GBPNZD", action="APPROVED", reason="ok",
                                execution_key="K9", payload={"strategy_key": "ICT_SABRI_MALLE"}) \
            if hasattr(repo, "record_audit_event") else None
        report = repo.entry_decision_report(days=3, source="DEMO")
        assert set(report) >= {"events", "trades", "days", "generated_at"}
        assert report["trades"]["trades_total"] == 0
        if hasattr(repo, "engine"):
            repo.engine.dispose()


def test_engine_attach_entry_decision_updates_trade_details():
    try:
        from strategy.execution.live_trading_engine import LiveTradingEngine
    except Exception:
        return  # requiere MetaTrader5 (solo Windows)

    class Repo:
        def __init__(self):
            self.updated = None
            self.row = {"id": 7, "instrument": "GBPNZD", "direction": "SELL", "execution_key": "K1",
                        "details": {"metadata": {"trade_leg": "TP1"}}}

        def get_trade(self, trade_id):
            return self.row

        def update_trade(self, trade_id, data):
            self.updated = (trade_id, data)

    class Cfg:
        bot_profile = "FOREX_1"

    class Fake:
        config = Cfg()
        repository = Repo()

        def _persist_audit_event(self, *a, **k):
            raise AssertionError("no debe fallar")

    fake = Fake()
    assert LiveTradingEngine._attach_entry_decision(fake, dict(fake.repository.row), _signal(strategy_name="ICT_SABRI_MALLE")) is True
    trade_id, data = fake.repository.updated
    meta = data["details"]["metadata"]
    assert trade_id == 7 and meta["trade_leg"] == "TP1"
    assert meta["entry_decision"]["entered"] is True and meta["entry_decision"]["execution_key"] == "K1"
    assert meta["entry_decision"]["human_criteria"]["score"] == 82.5
