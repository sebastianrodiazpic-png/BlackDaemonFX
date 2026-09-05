from pathlib import Path

def test_account_table_uses_fixed_layout_and_vertical_scroll_only():
    root=Path(__file__).resolve().parents[1]
    text=(root/"dashboard"/"account_page.py").read_text(encoding="utf-8")
    assert ".tbl{overflow-y:auto;overflow-x:hidden" in text
    assert "table-layout:fixed" in text
    assert "max-width:100%" in text

def test_account_audit_column_no_longer_forces_minimum_width():
    root=Path(__file__).resolve().parents[1]
    text=(root/"dashboard"/"account_page.py").read_text(encoding="utf-8")
    assert ".auditCard{display:grid;gap:7px;min-width:0" in text
    assert "min-width:360px" not in text

def test_account_audit_is_a_visible_card_without_disclosure_arrow():
    root=Path(__file__).resolve().parents[1]
    text=(root/"dashboard"/"account_page.py").read_text(encoding="utf-8")
    assert "<div class=\"auditCard\">" in text
    assert "<details><summary class=\"auditSummary\">" not in text
    assert "Ver auditoría completa ↗" in text

def test_account_columns_fit_full_width():
    root=Path(__file__).resolve().parents[1]
    text=(root/"dashboard"/"account_page.py").read_text(encoding="utf-8")
    assert "th:nth-child(7),td:nth-child(7){width:20%}" in text
    assert "overflow-wrap:anywhere" in text
