from pathlib import Path

from database.repository import TradingRepository
from database.reporting import export_trading_report


def main():
    db = Path("database/test_trading_bot.sqlite3")
    if db.exists():
        db.unlink()

    repo = TradingRepository(db)
    trade_id = repo.create_trade({
        "external_ticket": "TEST-STORAGE-001",
        "source": "TEST",
        "broker": "SIMULATOR",
        "instrument": "Volatility 90 Index",
        "timeframe": "M5",
        "direction": "BUY",
        "status": "OPEN",
        "entry_time": "2026-08-24T12:00:00Z",
        "entry_price": 1000,
        "stop_loss": 990,
        "take_profit": 1020,
        "planned_rr": 2.0,
        "volume": 0.1,
        "balance_before": 1000,
        "risk_percent": 1,
        "risk_amount": 10,
        "setup_reason": "trend, swing, liquidity, sweep, structure_break, order_block, retest, premium_discount, confirmation",
        "details": {"test": True},
    })

    repo.close_trade(trade_id, {
        "status": "CLOSED",
        "result": "WIN",
        "exit_time": "2026-08-24T12:15:00Z",
        "exit_price": 1020,
        "realized_rr": 2.0,
        "bars_held": 3,
        "exit_reason": "Take Profit alcanzado.",
        "gross_pnl": 20,
        "net_pnl": 20,
        "balance_after": 1020,
        "equity": 1020,
        "peak_balance": 1020,
        "drawdown_amount": 0,
        "drawdown_percent": 0,
    })

    print(repo.summary(source="TEST"))
    print(export_trading_report(db, "storage/exports/test_report.xlsx", source="TEST"))


if __name__ == "__main__":
    main()


def test_repository_reset_database_preserves_schema_and_blocks_open_trades(tmp_path):
    from database.repository import TradingRepository
    db = tmp_path / "reset.sqlite3"
    repo = TradingRepository(db)
    repo.save_account_snapshot({"balance": 1000, "equity": 1000})
    repo.create_trade({"source": "DEMO", "instrument": "X", "direction": "BUY", "status": "OPEN"})

    try:
        repo.reset_database()
        assert False, "Debió bloquear trades OPEN"
    except RuntimeError as exc:
        assert "LIMPIEZA BLOQUEADA" in str(exc)

    result = repo.reset_database(allow_open_trades=True)
    assert result["trades"] == 1
    assert result["account_snapshots"] == 1
    assert repo.trades_dataframe().empty
    assert repo.account_snapshots_dataframe().empty

    new_id = repo.create_trade({"source": "DEMO", "instrument": "Y", "direction": "SELL", "status": "CLOSED"})
    assert new_id == 1


def test_import_open_mt5_positions_recovers_daemon_and_external(tmp_path):
    from datetime import datetime, timezone
    from database.repository import TradingRepository

    class FakeExecutor:
        def list_open_positions(self):
            return [
                {
                    "position_ticket": 7001, "symbol": "Volatility 75 Index", "direction": "BUY",
                    "magic": 26082026, "comment": "DBFX-RUNNER", "identifier": 7001,
                    "entry_time": datetime(2026, 8, 29, 12, 0, tzinfo=timezone.utc),
                    "entry_price": 100.0, "current_price": 101.0, "stop_loss": 99.0,
                    "take_profit": 102.0, "volume": 1.0, "floating_profit": 10.0, "swap": 0.0,
                },
                {
                    "position_ticket": 7002, "symbol": "Step Index 400", "direction": "SELL",
                    "magic": 999, "comment": "manual", "identifier": 7002,
                    "entry_time": datetime(2026, 8, 29, 12, 5, tzinfo=timezone.utc),
                    "entry_price": 200.0, "current_price": 199.0, "stop_loss": 202.0,
                    "take_profit": 196.0, "volume": 1.0, "floating_profit": 5.0, "swap": 0.0,
                },
            ]

        def account_info(self):
            return {"equity": 10000.0}

        def calculate_risk_amount(self, **kwargs):
            return {"actual_risk_amount": 100.0}

    repo = TradingRepository(db_path=tmp_path / "mt5_import.sqlite3")
    result = repo.import_open_mt5_positions(FakeExecutor(), source="DEMO", magic=26082026, include_external=True)

    assert result["seen"] == 2
    assert result["imported_daemon"] == 1
    assert result["imported_external"] == 1

    all_open = repo.open_trades()
    assert len(all_open) == 2
    daemon = next(t for t in all_open if t["broker_position_ticket"] == "7001")
    external = next(t for t in all_open if t["broker_position_ticket"] == "7002")
    assert daemon["source"] == "DEMO"
    assert daemon["risk_percent"] == 1.0
    assert daemon["planned_rr"] == 2.0
    assert daemon["details"]["metadata"]["managed_by_daemon"] is True
    assert external["source"] == "MT5_EXTERNAL"
    assert external["details"]["metadata"]["managed_by_daemon"] is False

    # Idempotencia: un segundo arranque no duplica posiciones.
    again = repo.import_open_mt5_positions(FakeExecutor(), source="DEMO", magic=26082026, include_external=True)
    assert again["imported_daemon"] == 0
    assert again["imported_external"] == 0
    assert again["existing"] == 2
    assert len(repo.open_trades()) == 2


def test_trade_journal_survives_operational_reset_and_account_reads_history(tmp_path):
    from dashboard.account_metrics import build_account_payload
    db = tmp_path / "journal.sqlite3"
    repo = TradingRepository(db)
    trade_id = repo.create_trade({
        "source": "DEMO", "instrument": "Volatility 75 Index", "direction": "BUY",
        "status": "OPEN", "external_ticket": "J-001", "entry_price": 100.0,
        "risk_percent": 1.0, "net_pnl": 0.0,
        "details": {"trade_leg": "RUNNER", "execution_mode": "SPLIT"},
    })
    repo.close_trade(trade_id, {"result": "WIN", "exit_price": 102.0, "realized_rr": 2.0, "net_pnl": 20.0})

    before = repo.trade_history_dataframe(source="DEMO")
    assert len(before) == 1
    assert before.iloc[0]["status"] == "CLOSED"
    assert float(before.iloc[0]["net_pnl"]) == 20.0

    result = repo.reset_database(allow_open_trades=True)
    assert result["trade_journal_preserved"] == 1
    assert repo.trades_dataframe(source="DEMO").empty

    after = repo.trade_history_dataframe(source="DEMO")
    assert len(after) == 1
    payload = build_account_payload(repo, source="DEMO")
    assert payload["stats"]["total"] == 1
    assert payload["stats"]["closed"] == 1
    assert payload["stats"]["net_pnl"] == 20.0
    assert len(payload["recent_trades"]) == 1


def test_import_mt5_trade_history_recovers_past_daemon_trades_and_is_idempotent(tmp_path):
    from datetime import datetime, timezone
    from dashboard.account_metrics import build_account_payload
    from database.repository import TradingRepository

    class FakeExecutor:
        def list_open_positions(self):
            return []

        def list_history_deals(self, from_time=None, to_time=None, magic=None):
            return [
                {
                    "deal_ticket": 101, "order_ticket": 11, "position_ticket": 9001,
                    "symbol": "Volatility 75 Index", "magic": 26082026,
                    "comment": "SMC-501-TP1", "time": datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc),
                    "entry_kind": "IN", "direction": "BUY", "reason_kind": "EXPERT",
                    "price": 100.0, "volume": 0.5, "profit": 0.0, "commission": -0.5, "swap": 0.0, "fee": 0.0,
                },
                {
                    "deal_ticket": 102, "order_ticket": 12, "position_ticket": 9001,
                    "symbol": "Volatility 75 Index", "magic": 26082026,
                    "comment": "SMC-501-TP1", "time": datetime(2026, 8, 20, 12, 15, tzinfo=timezone.utc),
                    "entry_kind": "OUT", "direction": "SELL", "reason_kind": "TP",
                    "price": 101.0, "volume": 0.5, "profit": 50.0, "commission": -0.5, "swap": 0.0, "fee": 0.0,
                },
                {
                    "deal_ticket": 201, "order_ticket": 21, "position_ticket": 9002,
                    "symbol": "Step Index 400", "magic": 26082026,
                    "comment": "SMC-502-RUNNER", "time": datetime(2026, 8, 21, 10, 0, tzinfo=timezone.utc),
                    "entry_kind": "IN", "direction": "SELL", "reason_kind": "EXPERT",
                    "price": 200.0, "volume": 0.2, "profit": 0.0, "commission": 0.0, "swap": 0.0, "fee": 0.0,
                },
                {
                    "deal_ticket": 202, "order_ticket": 22, "position_ticket": 9002,
                    "symbol": "Step Index 400", "magic": 26082026,
                    "comment": "SMC-502-RUNNER", "time": datetime(2026, 8, 21, 10, 30, tzinfo=timezone.utc),
                    "entry_kind": "OUT", "direction": "BUY", "reason_kind": "SL",
                    "price": 202.0, "volume": 0.2, "profit": -40.0, "commission": 0.0, "swap": 0.0, "fee": 0.0,
                },
                # Trade manual/externo: no debe contaminar Cuenta activa DEMO.
                {
                    "deal_ticket": 301, "order_ticket": 31, "position_ticket": 9999,
                    "symbol": "EURUSD", "magic": 0, "comment": "manual",
                    "time": datetime(2026, 8, 22, 10, 0, tzinfo=timezone.utc),
                    "entry_kind": "IN", "direction": "BUY", "reason_kind": "CLIENT",
                    "price": 1.1, "volume": 0.1, "profit": 0.0, "commission": 0.0, "swap": 0.0, "fee": 0.0,
                },
                {
                    "deal_ticket": 302, "order_ticket": 32, "position_ticket": 9999,
                    "symbol": "EURUSD", "magic": 0, "comment": "manual",
                    "time": datetime(2026, 8, 22, 11, 0, tzinfo=timezone.utc),
                    "entry_kind": "OUT", "direction": "SELL", "reason_kind": "CLIENT",
                    "price": 1.11, "volume": 0.1, "profit": 10.0, "commission": 0.0, "swap": 0.0, "fee": 0.0,
                },
            ]

    repo = TradingRepository(tmp_path / "history.sqlite3")
    result = repo.import_mt5_trade_history(FakeExecutor(), source="DEMO", magic=26082026)
    assert result["imported"] == 2
    assert result["skipped_external"] == 1

    history = repo.trade_history_dataframe(source="DEMO")
    assert len(history) == 2
    assert set(history["broker_position_ticket"].astype(str)) == {"9001", "9002"}
    assert round(float(history.loc[history["broker_position_ticket"] == "9001", "net_pnl"].iloc[0]), 2) == 49.0

    # v24: la importación histórica puede conservarse como herramienta de
    # auditoría, pero Cuenta activa no la mezcla con el historial DB operativo.
    payload = build_account_payload(repo, source="DEMO")
    assert payload["stats"]["total"] == 0
    assert payload["data_source"] == "SQLALCHEMY_LOCAL_ONLY"

    again = repo.import_mt5_trade_history(FakeExecutor(), source="DEMO", magic=26082026)
    assert again["imported"] == 0
    assert again["updated"] == 2
    assert len(repo.trade_history_dataframe(source="DEMO")) == 2


def test_import_mt5_trade_history_skips_positions_still_open(tmp_path):
    from datetime import datetime, timezone
    from database.repository import TradingRepository

    class FakeExecutor:
        def list_open_positions(self):
            return [{"position_ticket": 7001}]

        def list_history_deals(self, from_time=None, to_time=None, magic=None):
            return [
                {
                    "deal_ticket": 1, "position_ticket": 7001, "symbol": "X", "magic": 26082026,
                    "comment": "RUNNER", "time": datetime(2026, 8, 20, tzinfo=timezone.utc),
                    "entry_kind": "IN", "direction": "BUY", "reason_kind": "EXPERT",
                    "price": 10.0, "volume": 1.0, "profit": 0.0, "commission": 0.0, "swap": 0.0, "fee": 0.0,
                },
                {
                    "deal_ticket": 2, "position_ticket": 7001, "symbol": "X", "magic": 26082026,
                    "comment": "partial", "time": datetime(2026, 8, 21, tzinfo=timezone.utc),
                    "entry_kind": "OUT", "direction": "SELL", "reason_kind": "CLIENT",
                    "price": 11.0, "volume": 0.5, "profit": 5.0, "commission": 0.0, "swap": 0.0, "fee": 0.0,
                },
            ]

    repo = TradingRepository(tmp_path / "open_history.sqlite3")
    result = repo.import_mt5_trade_history(FakeExecutor(), source="DEMO", magic=26082026)
    assert result["skipped_open"] == 1
    assert repo.trade_history_dataframe(source="DEMO").empty


def test_account_history_excludes_direct_mt5_history_reconstruction(tmp_path):
    from datetime import datetime, timezone
    from dashboard.account_metrics import build_account_payload
    from database.repository import TradingRepository

    repo = TradingRepository(tmp_path / "db_only_account.sqlite3")
    local_id = repo.create_trade({
        "source": "DEMO", "instrument": "Volatility 75 Index", "direction": "BUY",
        "status": "OPEN", "external_ticket": "LOCAL-1", "entry_price": 100.0,
        "risk_percent": 1.0, "net_pnl": 0.0,
    })
    repo.close_trade(local_id, {"result": "WIN", "exit_price": 102.0, "realized_rr": 2.0, "net_pnl": 20.0})

    class FakeExecutor:
        def list_open_positions(self):
            return []
        def list_history_deals(self, from_time=None, to_time=None, magic=None):
            return [
                {"deal_ticket": 501, "position_ticket": 99001, "symbol": "Step Index 400", "magic": 26082026,
                 "comment": "SMC-900-RUNNER", "time": datetime(2026,8,1,10,0,tzinfo=timezone.utc),
                 "entry_kind": "IN", "direction": "SELL", "reason_kind": "EXPERT", "price": 200.0,
                 "volume": 0.2, "profit": 0.0, "commission": 0.0, "swap": 0.0, "fee": 0.0},
                {"deal_ticket": 502, "position_ticket": 99001, "symbol": "Step Index 400", "magic": 26082026,
                 "comment": "SMC-900-RUNNER", "time": datetime(2026,8,1,11,0,tzinfo=timezone.utc),
                 "entry_kind": "OUT", "direction": "BUY", "reason_kind": "TP", "price": 198.0,
                 "volume": 0.2, "profit": 40.0, "commission": 0.0, "swap": 0.0, "fee": 0.0},
            ]

    imported = repo.import_mt5_trade_history(FakeExecutor(), source="DEMO", magic=26082026)
    assert imported["imported"] == 1
    assert len(repo.trade_history_dataframe(source="DEMO")) == 2

    db_only = repo.account_trade_history_dataframe(source="DEMO")
    assert len(db_only) == 1
    assert db_only.iloc[0]["external_ticket"] == "LOCAL-1"

    payload = build_account_payload(repo, source="DEMO")
    assert payload["data_source"] == "SQLALCHEMY_LOCAL_ONLY"
    assert payload["stats"]["total"] == 1
    assert payload["stats"]["net_pnl"] == 20.0


def test_account_stats_reset_is_persistent_preserves_open_positions_and_hides_old_closed(tmp_path):
    from dashboard.account_metrics import build_account_payload
    from database.repository import TradingRepository

    db = tmp_path / "account_stats_reset.sqlite3"
    repo = TradingRepository(db)

    win_id = repo.create_trade({
        "source": "DEMO", "instrument": "XAUUSD", "direction": "BUY",
        "status": "OPEN", "execution_key": "old-win", "external_ticket": "old-win",
        "planned_rr": 1.0, "risk_percent": 0.5,
        "details": {"metadata": {"trade_leg": "TP1"}},
    })
    repo.close_trade(win_id, {
        "result": "WIN", "exit_price": 2500.0, "realized_rr": 1.0, "net_pnl": 50.0,
    })

    loss_id = repo.create_trade({
        "source": "DEMO", "instrument": "US500", "direction": "SELL",
        "status": "OPEN", "execution_key": "old-loss", "external_ticket": "old-loss",
        "planned_rr": 2.0, "risk_percent": 0.5,
        "details": {"metadata": {"trade_leg": "RUNNER"}},
    })
    repo.close_trade(loss_id, {
        "result": "LOSS", "exit_price": 5000.0, "realized_rr": -1.0, "net_pnl": -25.0,
    })

    open_id = repo.create_trade({
        "source": "DEMO", "instrument": "XAUUSDmicro", "direction": "BUY",
        "status": "OPEN", "execution_key": "still-open", "external_ticket": "still-open",
        "planned_rr": 2.0, "risk_percent": 0.5,
        "details": {"metadata": {"trade_leg": "RUNNER"}},
    })

    before = build_account_payload(repo, source="DEMO")
    assert before["stats"]["total"] == 3
    assert before["stats"]["open"] == 1
    assert before["stats"]["closed"] == 2
    assert before["stats"]["wins"] == 1
    assert before["stats"]["losses"] == 1
    assert before["stats"]["win_rate"] == 50.0
    assert before["stats"]["net_pnl"] == 25.0

    reset = repo.reset_account_statistics(source="DEMO")
    assert reset["ok"] is True
    assert reset["open_positions_preserved"] == 1
    assert reset["closed_rows_hidden_from_new_window"] == 2

    after = build_account_payload(repo, source="DEMO")
    assert after["stats"]["total"] == 1
    assert after["stats"]["open"] == 1
    assert after["stats"]["closed"] == 0
    assert after["stats"]["wins"] == 0
    assert after["stats"]["losses"] == 0
    assert after["stats"]["win_rate"] == 0.0
    assert after["stats"]["net_pnl"] == 0.0
    assert after["stats_reset"]["reset_time"] is not None

    # Un cierre posterior al reset sí pertenece a la nueva ventana.
    repo.close_trade(open_id, {
        "result": "WIN", "exit_price": 2510.0, "realized_rr": 2.0, "net_pnl": 30.0,
    })
    closed_after = build_account_payload(repo, source="DEMO")
    assert closed_after["stats"]["total"] == 1
    assert closed_after["stats"]["open"] == 0
    assert closed_after["stats"]["closed"] == 1
    assert closed_after["stats"]["wins"] == 1
    assert closed_after["stats"]["win_rate"] == 100.0
    assert closed_after["stats"]["net_pnl"] == 30.0

    # Reiniciar el repository no recupera los cierres antiguos.
    repo2 = TradingRepository(db)
    persisted = build_account_payload(repo2, source="DEMO")
    assert persisted["stats"]["total"] == 1
    assert persisted["stats"]["closed"] == 1
    assert persisted["stats"]["win_rate"] == 100.0
    assert persisted["stats_reset"]["reset_time"] is not None


def test_instrument_selection_preferences_persist_across_repository_restarts(tmp_path):
    from database.repository import TradingRepository

    db = tmp_path / "instrument_preferences.sqlite3"
    repo = TradingRepository(db)
    saved = repo.save_instrument_selection(
        ["Volatility 75 Index", "XAUUSD", "XAUUSDmicro"], source="DEMO"
    )
    assert saved["version"] == 1
    assert saved["selected_symbols"] == [
        "Volatility 75 Index", "XAUUSD", "XAUUSDmicro"
    ]

    repo2 = TradingRepository(db)
    loaded = repo2.latest_instrument_selection(source="DEMO")
    assert loaded["selected_symbols"] == [
        "Volatility 75 Index", "XAUUSD", "XAUUSDmicro"
    ]
    assert loaded["version"] == 1

    saved2 = repo2.save_instrument_selection(
        ["US500", "Wall Street 30"], source="DEMO"
    )
    assert saved2["version"] == 2

    repo3 = TradingRepository(db)
    loaded2 = repo3.latest_instrument_selection(source="DEMO")
    assert loaded2["selected_symbols"] == ["US500", "Wall Street 30"]
    assert loaded2["version"] == 2
