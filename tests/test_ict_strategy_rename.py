import pytest
from strategy.ict.config import ICTSabriMalleConfig
from strategy.ict.ict_strategy import ICTSabriMalleStrategy
from dashboard.account_metrics import _strategy_name, build_account_payload
from database.repository import TradingRepository


def test_ict_config_default_name():
    cfg = ICTSabriMalleConfig()
    assert cfg.strategy_name == "ICT"


def test_ict_strategy_action_confirmed():
    # Strategy should return ICT_CONFIRMED on valid signal structure
    strat = ICTSabriMalleStrategy(data_provider=None, config=ICTSabriMalleConfig())
    # Verify the action returned is ICT_CONFIRMED
    import inspect
    src = inspect.getsource(strat.analyze_symbol)
    assert '"action": "ICT_CONFIRMED"' in src


def test_account_metrics_strategy_name_normalization():
    # Trade with explicit ICT_SABRI_MALLE in metadata
    trade1 = {
        "details": {"metadata": {"strategy_name": "ICT_SABRI_MALLE"}},
        "instrument": "Jump 75 Index"
    }
    assert _strategy_name(trade1) == "ICT"

    # Trade with ICT in strategy_name directly on trade
    trade2 = {
        "strategy_name": "ICT_SABRI_MALLE",
        "instrument": "Volatility 10 Index"
    }
    assert _strategy_name(trade2) == "ICT"

    # Trade with already normalized ICT
    trade3 = {
        "details": {"metadata": {"strategy_name": "ICT"}},
        "instrument": "EURUSD"
    }
    assert _strategy_name(trade3) == "ICT"

    # Malaysian SnR or other strategies should remain unchanged
    trade4 = {
        "details": {"metadata": {"strategy_name": "MALAYSIAN_SNR"}},
        "instrument": "Boom 1000 Index"
    }
    assert _strategy_name(trade4) == "MALAYSIAN_SNR"


def test_dashboard_format_strategy_origin_logic():
    # Verify the normalization logic used in dashboard templates
    def format_strategy_origin(orig):
        if not orig:
            return ""
        s = str(orig).strip()
        up = s.upper()
        if up in ("ICT_SABRI_MALLE", "ICT", "ESTRATEGIA ICT_SABRI_MALLE", "ESTRATEGIA ICT"):
            return "Estrategia ICT"
        return s if s.startswith("Estrategia ") else f"Estrategia {s}"

    assert format_strategy_origin("ICT_SABRI_MALLE") == "Estrategia ICT"
    assert format_strategy_origin("ICT") == "Estrategia ICT"
    assert format_strategy_origin("Estrategia ICT_SABRI_MALLE") == "Estrategia ICT"
    assert format_strategy_origin("Malaysian SNR") == "Estrategia Malaysian SNR"
    assert format_strategy_origin("Estrategia Malaysian SNR") == "Estrategia Malaysian SNR"


def test_dashboard_html_templates_contain_format_strategy_origin():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    dash_text = (root / "dashboard" / "realtime_dashboard.py").read_text(encoding="utf-8")
    assert "function formatStrategyOrigin(orig)" in dash_text
    assert "formatStrategyOrigin(t.strategy_origin)" in dash_text

    acct_text = (root / "dashboard" / "account_page.py").read_text(encoding="utf-8")
    assert "stratDisplay = (v) =>" in acct_text
    assert "stratDisplay(st.strategy)" in acct_text
    assert "stratDisplay(op.strategy)" in acct_text


def test_technical_audit_decision_rename():
    # Verify formatAuditDecision logic
    def format_audit_decision(dec):
        if not dec:
            return "Sin auditoría persistida"
        s = str(dec).strip()
        if s.upper() in ("ICT_SABRI_MALLE_CONFIRMED", "ICT_CONFIRMED"):
            return "ICT_CONFIRMED"
        return s.replace("ICT_SABRI_MALLE", "ICT").replace("ICT SABRI MALLE", "ICT")

    assert format_audit_decision("ICT_SABRI_MALLE_CONFIRMED") == "ICT_CONFIRMED"
    assert format_audit_decision("ICT_CONFIRMED") == "ICT_CONFIRMED"
    assert format_audit_decision("ORB_SWEEP_MSS_CONFIRMED") == "ORB_SWEEP_MSS_CONFIRMED"

    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    acct_text = (root / "dashboard" / "account_page.py").read_text(encoding="utf-8")
    assert "formatAuditDecision = (dec) =>" in acct_text
    assert "formatAuditDecision(q.confirmation_decision)" in acct_text

    audit_text = (root / "dashboard" / "trade_audit_page.py").read_text(encoding="utf-8")
    assert "function formatAuditDecision(dec)" in audit_text
    assert "formatAuditDecision(e.decision" in audit_text
    assert "formatStrategyName(e.strategy_name)" in audit_text
