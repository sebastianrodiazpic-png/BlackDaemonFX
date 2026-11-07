import os
import re
import subprocess
from pathlib import Path

from dashboard.account_metrics import build_account_payload
from dashboard.account_page import ACCOUNT_HTML
from database.repository import TradingRepository


def test_account_payload_hides_exact_db_path_by_default(tmp_path, monkeypatch):
    monkeypatch.delenv("DAEMONBLACKFX_SHOW_EXACT_DB_PATH", raising=False)
    repo = TradingRepository(db_path=tmp_path / "private_trading_bot.sqlite3")
    payload = build_account_payload(repo)

    # Diagnostic path is kept for backend/continuity tests
    assert payload["database"]["path"].endswith("private_trading_bot.sqlite3")
    # But display_path is masked to protect user privacy
    assert payload["database"]["display_path"] == "conectada"


def test_account_payload_reveals_exact_db_path_when_configured(tmp_path, monkeypatch):
    monkeypatch.setenv("DAEMONBLACKFX_SHOW_EXACT_DB_PATH", "1")
    repo = TradingRepository(db_path=tmp_path / "private_trading_bot.sqlite3")
    payload = build_account_payload(repo)

    assert payload["database"]["display_path"] == payload["database"]["path"]
    assert payload["database"]["display_path"].endswith("private_trading_bot.sqlite3")


def test_account_payload_ranking_toggle_default_false(tmp_path, monkeypatch):
    monkeypatch.delenv("DAEMONBLACKFX_SHOW_STRATEGY_RANKING", raising=False)
    repo = TradingRepository(db_path=tmp_path / "test.sqlite3")
    payload = build_account_payload(repo)
    assert payload["show_strategy_ranking"] is False


def test_account_payload_ranking_toggle_enabled(tmp_path, monkeypatch):
    monkeypatch.setenv("DAEMONBLACKFX_SHOW_STRATEGY_RANKING", "1")
    repo = TradingRepository(db_path=tmp_path / "test.sqlite3")
    payload = build_account_payload(repo)
    assert payload["show_strategy_ranking"] is True


def test_account_html_structure_hides_ranking_and_exact_path():
    # Card is hidden by default in initial DOM
    assert '<div id="strategyRankingCard" class="c full" style="display: none">' in ACCOUNT_HTML
    # Initial status does not expose checking path
    assert '<div id="dbpath" class="muted" style="margin-top: 3px; font-size: 11px">SQLite: conectando…</div>' in ACCOUNT_HTML
    # JavaScript correctly handles conditional ranking display and masked db path
    assert "strategyRankingCard" in ACCOUNT_HTML
    assert "show_strategy_ranking" in ACCOUNT_HTML
    assert "display_path" in ACCOUNT_HTML


def test_account_page_javascript_syntax_valid():
    root = Path(__file__).resolve().parents[1]
    text = (root / "dashboard" / "account_page.py").read_text(encoding="utf-8")
    script = re.search(r"<script>(.*)</script>", text, re.S).group(1)
    test_js = root / "storage" / "account_page_syntax_test.js"
    test_js.parent.mkdir(parents=True, exist_ok=True)
    test_js.write_text(script, encoding="utf-8")
    result = subprocess.run(["node", "--check", str(test_js)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
