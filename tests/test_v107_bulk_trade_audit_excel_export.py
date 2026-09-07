from pathlib import Path


def test_dashboard_exposes_bulk_excel_download_endpoint():
    root = Path(__file__).resolve().parents[1]
    dash = (root / "dashboard" / "realtime_dashboard.py").read_text(encoding="utf-8")
    assert "/api/account/trades/audit/excel/bulk" in dash
    assert "zipfile" in dash
    assert "application/zip" in dash
    assert "trade_ids" in dash


def test_account_page_has_bulk_selection_ui():
    root = Path(__file__).resolve().parents[1]
    page = (root / "dashboard" / "account_page.py").read_text(encoding="utf-8")
    assert "selectAllRows" in page
    assert "bulkDownloadBtn" in page
    assert "downloadSelectedAudits" in page
    assert "/api/account/trades/audit/excel/bulk" in page
