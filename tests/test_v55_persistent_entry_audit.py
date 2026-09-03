
from database.repository import TradingRepository


def test_trade_entry_visual_audit_is_immutable(tmp_path):
    repo=TradingRepository(db_path=tmp_path/"audit.db")

    first_chart={"timeframes":{"M5":{"candles":[{"time":"2026-08-31T12:00:00Z","close":100}]}}}
    first_context={"score":90,"confirmation_percentage":85.7,"passed":["BOS","REJECTION"]}
    second_chart={"timeframes":{"M5":{"candles":[{"time":"2026-08-31T12:05:00Z","close":110}]}}}
    second_context={"score":10,"passed":[]}

    repo.upsert_trade_visual_audit(
        7,instrument="Boom 500 Index",bot_profile="BOOM",daemon_magic=26082101,
        entry_chart=first_chart,entry_context=first_context,
        latest_chart=first_chart,latest_market={"current_rr":0.2},
    )
    repo.upsert_trade_visual_audit(
        7,instrument="Boom 500 Index",bot_profile="BOOM",daemon_magic=26082101,
        entry_chart=second_chart,entry_context=second_context,
        latest_chart=second_chart,latest_market={"current_rr":1.5},
    )

    row=repo.trade_visual_audits("DEMO")[0]
    assert row["entry_context"]["score"]==90
    assert row["entry_context"]["passed"]==["BOS","REJECTION"]
    assert row["entry_chart"]["timeframes"]["M5"]["candles"][0]["close"]==100
    assert row["latest_chart"]["timeframes"]["M5"]["candles"][0]["close"]==110
    assert row["latest_market"]["current_rr"]==1.5


def test_trade_visual_audit_survives_without_open_trade_row(tmp_path):
    repo=TradingRepository(db_path=tmp_path/"history.db")
    repo.upsert_trade_visual_audit(
        99,instrument="EURUSD",bot_profile="FOREX",daemon_magic=26082027,
        entry_chart={"timeframes":{"M15":{"candles":[]}}},
        entry_context={"score":88,"decision":"CONFIRMED"},
    )
    rows=repo.trade_visual_audits("DEMO")
    assert len(rows)==1
    assert rows[0]["trade_id"]==99
    assert rows[0]["entry_context"]["decision"]=="CONFIRMED"


def test_dashboard_source_exposes_entry_and_current_toggle():
    from dashboard import realtime_dashboard as rd
    assert 'data-audit-mode="ENTRY"' in rd._HTML
    assert 'data-audit-mode="CURRENT"' in rd._HTML
    assert "EVIDENCIA DE ENTRADA PERSISTIDA" in rd._HTML


def test_database_model_has_unique_trade_visual_audit():
    from database.models import TradeVisualAudit
    assert TradeVisualAudit.__tablename__=="trade_visual_audits"
