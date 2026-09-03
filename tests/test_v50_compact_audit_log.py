
import json
import warnings

import pandas as pd

from reporting.trade_report_exporter import TradeReportExporter


def test_compact_audit_log_extracts_key_fields_and_limits_summary():
    huge_text = "X" * 38095
    payload = {
        "bot_profile": "VOLATILITY",
        "daemon_magic": 26082103,
        "elapsed_seconds": 4.65,
        "result": {
            "action": "WAITING M5 AFTER M15",
            "reason": "M5_CONFIRMATIONS_EXIST_BUT_ALL_PRECEDE_LATEST_M15_SETUP",
            "analysis_dump": huge_text,
        },
    }
    frame = pd.DataFrame([{
        "id": 1,
        "event_time": pd.Timestamp("2026-08-31T12:00:00Z"),
        "source": "DEMO",
        "event_type": "SYMBOL_PROCESS_RESULT",
        "instrument": "Volatility 75 Index",
        "action": "WAITING M5 AFTER M15",
        "reason": "M5_CONFIRMATIONS_EXIST_BUT_ALL_PRECEDE_LATEST_M15_SETUP",
        "execution_key": None,
        "broker_position_ticket": None,
        "cycle_number": 10,
        "payload": payload,
        "payload_json": json.dumps(payload),
    }])

    compact = TradeReportExporter._compact_audit_dataframe(frame)

    assert "payload" not in compact.columns
    assert "payload_json" not in compact.columns
    assert compact.iloc[0]["bot_profile"] == "VOLATILITY"
    assert int(compact.iloc[0]["daemon_magic"]) == 26082103
    assert compact.iloc[0]["payload_completo_en_db"] == "SÍ"
    assert len(compact.iloc[0]["resumen"]) <= TradeReportExporter.AUDIT_EXCEL_SUMMARY_LIMIT


def test_export_does_not_emit_excel_cell_too_long_warning(tmp_path):
    huge_text = "Y" * 38095

    class Repo:
        def trade_history_dataframe(self, source="DEMO"):
            return pd.DataFrame()
        def trades_dataframe(self, source="DEMO"):
            return pd.DataFrame()
        def summary(self, source="DEMO"):
            return {
                "total_trades": 0, "closed_trades": 0, "open_trades": 0,
                "winning_trades": 0, "losing_trades": 0, "ambiguous_trades": 0,
                "breakeven_trades": 0, "win_rate": 0.0, "gross_profit": 0.0,
                "gross_loss": 0.0, "total_net_pnl": 0.0, "invested_amount": 0.0,
                "average_planned_rr": 0.0, "average_realized_rr": 0.0,
                "max_drawdown_amount": 0.0, "max_drawdown_percent": 0.0,
                "instruments": [],
            }
        def account_snapshots_dataframe(self):
            return pd.DataFrame()
        def audit_events_dataframe(self, source="DEMO"):
            return pd.DataFrame([{
                "id": 1,
                "event_time": pd.Timestamp("2026-08-31T12:00:00Z"),
                "source": "DEMO",
                "event_type": "SYMBOL_PROCESS_RESULT",
                "instrument": "Boom 500 Index",
                "action": "NO_SIGNAL",
                "reason": "WAITING",
                "execution_key": None,
                "broker_position_ticket": None,
                "cycle_number": 1,
                "payload": {
                    "bot_profile": "BOOM",
                    "daemon_magic": 26082101,
                    "result": {"action": "NO_SIGNAL", "blob": huge_text},
                },
                "payload_json": json.dumps({"blob": huge_text}),
            }])

    exporter = TradeReportExporter(
        repository=Repo(),
        output_path=tmp_path / "report.xlsx",
    )

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        exporter.export(source="DEMO")

    messages = [str(item.message) for item in caught]
    assert not any("Cell contents too long" in message for message in messages)

    audit = pd.read_excel(tmp_path / "report.xlsx", sheet_name="Audit Log")
    assert "resumen" in audit.columns
    assert "payload_completo_en_db" in audit.columns
    assert "payload" not in audit.columns
    assert "payload_json" not in audit.columns
