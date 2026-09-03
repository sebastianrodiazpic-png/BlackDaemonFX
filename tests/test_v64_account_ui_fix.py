import re
import subprocess
from pathlib import Path

from dashboard.account_metrics import build_account_payload
from database.repository import TradingRepository


def test_account_page_javascript_is_valid():
    root=Path(__file__).resolve().parents[1]
    text=(root/"dashboard"/"account_page.py").read_text(encoding="utf-8")
    script=re.search(r"<script>(.*)</script>",text,re.S).group(1)
    js=root/"storage"/"account_page_syntax_test.js"
    js.parent.mkdir(parents=True,exist_ok=True)
    js.write_text(script,encoding="utf-8")
    result=subprocess.run(["node","--check",str(js)],capture_output=True,text=True)
    assert result.returncode==0, result.stderr


def test_account_payload_contains_db_diagnostics(tmp_path):
    repo=TradingRepository(db_path=tmp_path/"account.db")
    payload=build_account_payload(repo)
    assert payload["database"]["path"].endswith("account.db")
    assert "trade_rows" in payload["database"]
    assert "trade_journal_rows" in payload["database"]


def test_account_page_fetch_checks_http_status():
    root=Path(__file__).resolve().parents[1]
    text=(root/"dashboard"/"account_page.py").read_text(encoding="utf-8")
    assert "if(!r.ok)throw new Error" in text
    assert "SQLite/API:" in text


def test_account_page_keeps_persistent_confirmation_column():
    root=Path(__file__).resolve().parents[1]
    text=(root/"dashboard"/"account_page.py").read_text(encoding="utf-8")
    assert "Confirmaciones persistentes" in text
    assert "Detalle técnico persistido" in text
