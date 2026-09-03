from pathlib import Path
import zipfile

from reporting.trade_audit_excel_exporter import TradeAuditExcelExporter


def _payload():
    return {
        "ok": True,
        "trade": {
            "id": 6,
            "source_trade_id": 6,
            "instrument": "Wall Street 30",
            "direction": "BUY",
            "status": "CLOSED",
            "classification": "STOP LOSS",
            "entry_time": "2026-09-01T21:17:55+00:00",
            "exit_time": "2026-09-01T21:20:08+00:00",
            "planned_rr": 2.0,
            "realized_rr": -1.0,
            "net_pnl": -98.75,
            "risk_percent": 1.0,
        },
        "entry_view": {
            "decision": "ORB_NY_M5_BREAKOUT_RETEST_CONFIRMED",
            "score": 100,
            "confirmation_percentage": 100,
            "direction": "BUY",
        },
        "snapshots": [
            {
                "id": 1, "trade_id": 6, "snapshot_at": "2026-09-01T21:18:00+00:00",
                "bot_profile": "ORB", "daemon_magic": 26082028,
                "instrument": "Wall Street 30", "broker_position_ticket": "123",
                "entry_view": {"decision": "ORB_NY_M5_BREAKOUT_RETEST_CONFIRMED", "score": 100},
                "current_view": {"decision": "WAITING_M5_BREAKOUT_RETEST", "h1_trend": "BEARISH"},
                "market": {"current_rr": -0.2, "current_price": 53000.0},
                "visual_context": {"strategy": "ORB_NEW_YORK"},
            },
            {
                "id": 2, "trade_id": 6, "snapshot_at": "2026-09-01T21:20:00+00:00",
                "bot_profile": "ORB", "daemon_magic": 26082028,
                "instrument": "Wall Street 30", "broker_position_ticket": "123",
                "entry_view": {"decision": "ORB_NY_M5_BREAKOUT_RETEST_CONFIRMED", "score": 100},
                "current_view": {"decision": "WAITING_M5_BREAKOUT_RETEST", "h1_trend": "BEARISH"},
                "market": {"current_rr": -0.95, "current_price": 52920.0},
                "visual_context": {"strategy": "ORB_NEW_YORK"},
            },
        ],
        "latest": {
            "current_view": {"decision": "WAITING_M5_BREAKOUT_RETEST"},
            "market": {"current_rr": -0.95},
        },
    }


def test_exporter_creates_multisheet_xlsx(tmp_path):
    out=tmp_path/"audit.xlsx"
    result=TradeAuditExcelExporter(out).export(_payload())
    assert out.exists()
    assert result["snapshots"] == 2
    with zipfile.ZipFile(out) as z:
        assert z.testzip() is None
        workbook=z.read("xl/workbook.xml").decode("utf-8")
        for sheet in ("Resumen","Tesis Entrada","Ultimo Estado","Mercado Final","Timeline Completo"):
            assert sheet in workbook


def test_web_page_has_excel_button():
    root=Path(__file__).resolve().parents[1]
    page=(root/"dashboard"/"trade_audit_page.py").read_text(encoding="utf-8")
    assert "Exportar Excel" in page
    assert "'/api'+location.pathname+'/excel'" in page


def test_dashboard_exposes_excel_download_endpoint():
    root=Path(__file__).resolve().parents[1]
    dash=(root/"dashboard"/"realtime_dashboard.py").read_text(encoding="utf-8")
    assert 'audit/excel' in dash
    assert "TradeAuditExcelExporter" in dash
    assert "Content-Disposition" in dash
    assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in dash
