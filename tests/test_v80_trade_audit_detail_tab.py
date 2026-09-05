from pathlib import Path
import re
import subprocess

def test_account_opens_trade_audit_in_new_tab():
    root=Path(__file__).resolve().parents[1]
    text=(root/"dashboard"/"account_page.py").read_text(encoding="utf-8")
    assert 'target="_blank"' in text
    assert '/account/trade/' in text
    assert 'Abrir auditoría visual completa' in text
    assert 'Historial Entrada vs. Ahora (últimos ' not in text

def test_trade_audit_has_dedicated_page_and_api():
    root=Path(__file__).resolve().parents[1]
    dash=(root/"dashboard"/"realtime_dashboard.py").read_text(encoding="utf-8")
    assert 'TRADE_AUDIT_HTML' in dash
    assert 're.fullmatch(r"/account/trade/' in dash
    assert 're.fullmatch(r"/api/account/trade/' in dash
    assert 'def _trade_audit_detail_payload' in dash

def test_detail_api_loads_all_snapshots_and_orders_chronologically():
    root=Path(__file__).resolve().parents[1]
    dash=(root/"dashboard"/"realtime_dashboard.py").read_text(encoding="utf-8")
    assert 'trade_audit_snapshots(' in dash
    assert 'limit=None' in dash
    assert 'snapshots = list(reversed(snapshots))' in dash

def test_detail_page_exposes_timeline_and_evolution_metrics():
    root=Path(__file__).resolve().parents[1]
    page=(root/"dashboard"/"trade_audit_page.py").read_text(encoding="utf-8")
    assert 'Línea temporal completa' in page
    assert 'MFE observado' in page
    assert 'MAE observado' in page
    assert 'LO QUE VEÍA EN ESE MOMENTO' in page
    assert 'Contexto técnico persistido' in page


def test_trade_audit_page_javascript_is_valid(tmp_path):
    root=Path(__file__).resolve().parents[1]
    page=(root/"dashboard"/"trade_audit_page.py").read_text(encoding="utf-8")
    script=re.search(r"<script>(.*)</script>", page, re.S).group(1)
    js=tmp_path/"trade_audit_page.js"
    js.write_text(script, encoding="utf-8")

    result=subprocess.run(["node", "--check", str(js)], capture_output=True, text=True)

    assert result.returncode == 0, result.stderr
