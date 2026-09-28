import re
from pathlib import Path

def test_account_table_uses_fixed_layout_and_vertical_scroll_only():
    root=Path(__file__).resolve().parents[1]
    text=(root/"dashboard"/"account_page.py").read_text(encoding="utf-8")
    assert re.sub(r'\s+', '', ".tbl{overflow-y:auto;overflow-x:hidden").replace(';}', '}') in re.sub(r'\s+', '', text).replace(';}', '}')
    assert re.sub(r'\s+', '', "table-layout:fixed").replace(';}', '}') in re.sub(r'\s+', '', text).replace(';}', '}')
    assert re.sub(r'\s+', '', "max-width:100%").replace(';}', '}') in re.sub(r'\s+', '', text).replace(';}', '}')

def test_account_audit_column_no_longer_forces_minimum_width():
    root=Path(__file__).resolve().parents[1]
    text=(root/"dashboard"/"account_page.py").read_text(encoding="utf-8")
    assert re.sub(r'\s+', '', ".auditCard{display:grid;gap:7px;min-width:0").replace(';}', '}') in re.sub(r'\s+', '', text).replace(';}', '}')
    assert re.sub(r'\s+', '', "min-width:360px").replace(';}', '}') not in re.sub(r'\s+', '', text).replace(';}', '}')

def test_account_audit_is_a_visible_card_without_disclosure_arrow():
    root=Path(__file__).resolve().parents[1]
    text=(root/"dashboard"/"account_page.py").read_text(encoding="utf-8")
    assert re.sub(r'\s+', '', "<div class=\"auditCard\">").replace(';}', '}') in re.sub(r'\s+', '', text).replace(';}', '}')
    assert re.sub(r'\s+', '', "<details><summary class=\"auditSummary\">").replace(';}', '}') not in re.sub(r'\s+', '', text).replace(';}', '}')
    assert re.sub(r'\s+', '', "Ver auditoría completa ↗").replace(';}', '}') in re.sub(r'\s+', '', text).replace(';}', '}')

def test_account_columns_fit_full_width():
    root=Path(__file__).resolve().parents[1]
    text=(root/"dashboard"/"account_page.py").read_text(encoding="utf-8")
    assert re.sub(r'\s+', '', "th:nth-child(7),td:nth-child(7){width:20%}").replace(';}', '}') in re.sub(r'\s+', '', text).replace(';}', '}')
    assert re.sub(r'\s+', '', "overflow-wrap:anywhere").replace(';}', '}') in re.sub(r'\s+', '', text).replace(';}', '}')
