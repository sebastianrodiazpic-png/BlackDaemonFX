from types import SimpleNamespace

from dashboard.realtime_dashboard import RealtimeDashboardService
from reporting.trade_audit_excel_exporter import TradeAuditExcelExporter
from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine


class EntryAuditRepo:
    def __init__(self):
        self.visual = []
        self.snapshots = []

    def upsert_trade_visual_audit(self, trade_id, **kwargs):
        self.visual.append((trade_id, kwargs))

    def trade_audit_snapshots(self, **kwargs):
        return list(reversed(self.snapshots))

    def save_trade_audit_snapshot(self, trade_id, **kwargs):
        self.snapshots.append({"id": len(self.snapshots) + 1, "trade_id": trade_id, **kwargs})


def test_fill_persists_entry_context_and_initial_append_only_snapshot():
    repo = EntryAuditRepo()
    engine = object.__new__(LiveTradingEngine)
    engine.repository = repo
    engine.config = LiveTradingConfig(bot_profile="FOREX_1", magic=26082031)
    engine._current_strategy_view_from_analysis = lambda analysis: {
        "decision": "WAITING_M5_CONFIRMATION", "evaluated_at": "2026-09-02T12:00:00Z"
    }
    trade = {
        "id": 10, "instrument": "EURUSD", "direction": "BUY",
        "entry_time": "2026-09-02T12:00:00Z", "entry_price": 1.10,
        "stop_loss": 1.09, "take_profit": 1.12, "planned_rr": 2.0,
        "risk_percent": 0.5, "broker_position_ticket": "9001",
    }
    assert engine._persist_entry_audit_immediately(
        trade,
        {"confirmation_decision": "ADAPTIVE_80_CONFIRMED", "trade_score": 92},
        {"action": "ENTRY_CONFIRMED"},
        ticket="9001",
    ) is True
    assert len(repo.visual) == 1
    assert repo.visual[0][1]["entry_context"]["captured_immediately_after_fill"] is True
    assert len(repo.snapshots) == 1
    assert repo.snapshots[0]["market"]["telemetry_mode"] == "ENTRY_FILL_CONFIRMED"
    assert repo.snapshots[0]["broker_position_ticket"] == "9001"


def test_immediate_snapshot_is_idempotent_on_persistence_retry():
    repo = EntryAuditRepo()
    repo.snapshots.append({"id": 1, "trade_id": 10})
    engine = object.__new__(LiveTradingEngine)
    engine.repository = repo
    engine.config = LiveTradingConfig(bot_profile="BOOM", magic=26082101)
    trade = {"id": 10, "instrument": "Boom 500 Index", "direction": "SELL"}
    engine._persist_entry_audit_immediately(trade, {}, {}, ticket="99")
    assert len(repo.snapshots) == 1


def test_audit_page_falls_back_to_immutable_visual_entry_when_history_is_empty(monkeypatch):
    trade = {
        "id": 3, "source_trade_id": 3, "instrument": "US500",
        "direction": "BUY", "broker_position_ticket": "300",
    }
    monkeypatch.setattr(
        "dashboard.realtime_dashboard.build_account_payload",
        lambda repository, source, recent_limit: {"recent_trades": [trade]},
    )
    repo = SimpleNamespace(
        trade_audit_snapshots=lambda **kwargs: [],
        trade_visual_audits=lambda source: [{
            "trade_id": 3, "instrument": "US500", "broker_position_ticket": "300",
            "bot_profile": "ORB", "daemon_magic": 26082028,
            "entry_context": {"decision": "ORB_ENTRY_CONFIRMED", "score": 100},
            "latest_market": {"current_rr": -0.2},
            "entry_captured_at": "2026-09-02T12:00:00Z",
        }],
    )
    service = object.__new__(RealtimeDashboardService)
    service.repository = repo
    payload = service._trade_audit_detail_payload(3)
    assert payload["ok"] is True
    assert payload["audit_integrity"]["valid"] is True
    assert payload["audit_integrity"]["fallback_from_trade_visual_audit"] is True
    assert payload["entry_view"]["decision"] == "ORB_ENTRY_CONFIRMED"
    assert len(payload["snapshots"]) == 1


def test_audit_page_excludes_snapshot_from_another_ticket_and_remains_exportable(monkeypatch, tmp_path):
    trade = {
        "id": 3, "source_trade_id": 3, "instrument": "US500",
        "direction": "BUY", "broker_position_ticket": "300",
    }
    monkeypatch.setattr(
        "dashboard.realtime_dashboard.build_account_payload",
        lambda repository, source, recent_limit: {"recent_trades": [trade]},
    )
    repo = SimpleNamespace(
        trade_audit_snapshots=lambda **kwargs: [{
            "id": 8, "trade_id": 3, "instrument": "US500",
            "broker_position_ticket": "WRONG", "entry_view": {"decision": "WRONG"},
        }],
        trade_visual_audits=lambda source: [],
    )
    service = object.__new__(RealtimeDashboardService)
    service.repository = repo
    payload = service._trade_audit_detail_payload(3)
    assert payload["audit_integrity"]["valid"] is True
    assert payload["audit_integrity"]["sanitized"] is True
    assert payload["audit_integrity"]["excluded_snapshot_ids"] == [8]
    assert payload["entry_view"]["decision"] == "HISTORICAL_ENTRY_CONTEXT_UNAVAILABLE"
    assert all(snap.get("broker_position_ticket") != "WRONG" for snap in payload["snapshots"])

    output = tmp_path / "audit.xlsx"
    result = TradeAuditExcelExporter(output).export(payload)
    assert output.exists()
    assert result["snapshots"] == 1


def test_audit_page_recovers_entry_thesis_from_canonical_trade(monkeypatch):
    account_trade = {
        "id": 4, "source_trade_id": 4, "instrument": "XAUUSD",
        "direction": "SELL", "broker_position_ticket": "400",
    }
    monkeypatch.setattr(
        "dashboard.realtime_dashboard.build_account_payload",
        lambda repository, source, recent_limit: {"recent_trades": [account_trade]},
    )
    repo = SimpleNamespace(
        get_trade=lambda trade_id: {
            **account_trade,
            "confirmation_audit": {"decision": "ADAPTIVE_80_CONFIRMED", "score": 88},
        },
        trade_audit_snapshots=lambda **kwargs: [],
        trade_visual_audits=lambda source: [],
    )
    service = object.__new__(RealtimeDashboardService)
    service.repository = repo
    payload = service._trade_audit_detail_payload(4)
    assert payload["audit_integrity"]["valid"] is True
    assert payload["audit_integrity"]["entry_view_origin"] == "TRADE_CONFIRMATION_AUDIT"
    assert payload["entry_view"]["decision"] == "ADAPTIVE_80_CONFIRMED"
