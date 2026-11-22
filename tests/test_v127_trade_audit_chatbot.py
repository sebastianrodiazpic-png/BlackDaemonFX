from pathlib import Path
from dashboard.trade_audit_chatbot import answer_trade_audit_inquiry


def _mock_win_audit():
    return {
        "ok": True,
        "trade": {
            "id": 101,
            "source_trade_id": 101,
            "instrument": "Boom 1000 Index",
            "direction": "BUY",
            "entry_time": "2026-11-20T10:00:00Z",
            "exit_time": "2026-11-20T10:45:00Z",
            "entry_price": 12500.0,
            "exit_price": 12625.0,
            "stop_loss": 12450.0,
            "take_profit": 12625.0,
            "planned_rr": 2.5,
            "realized_rr": 2.5,
            "net_pnl": 75.50,
            "status": "CLOSED",
            "classification": "PROFIT",
            "result": "TAKE PROFIT",
        },
        "entry_view": {
            "strategy_name": "ICT",
            "decision": "ICT_CONFIRMED",
            "score": 95,
            "confirmation_percentage": 100,
            "h4_trend": "BULLISH",
            "h1_trend": "BULLISH",
            "structure_break": "BOS_BULLISH",
            "zone": "M15_OB_BULLISH",
            "passed": ["FVG_FORMED", "LIQUIDITY_SWEEP", "DISPLACEMENT_DETECTED"],
            "missing": [],
        },
        "snapshots": [
            {"market": {"current_rr": 0.5, "current_price": 12525.0}},
            {"market": {"current_rr": 1.5, "current_price": 12575.0}},
            {"market": {"current_rr": 2.5, "current_price": 12625.0}},
        ],
        "learning_eligibility": {
            "evidence_type": "ENTRY_CAPTURE",
            "reason": "ELEGIBLE_ENTRADA",
        },
    }


def _mock_loss_audit():
    return {
        "ok": True,
        "trade": {
            "id": 2021,
            "source_trade_id": 2021,
            "instrument": "Volatility 100 Index",
            "direction": "SELL",
            "entry_time": "2026-11-21T02:31:39Z",
            "exit_time": "2026-11-21T03:15:20Z",
            "entry_price": 565.02,
            "exit_price": 574.91,
            "stop_loss": 574.91,
            "take_profit": 555.13,
            "planned_rr": 2.5,
            "realized_rr": -0.98,
            "net_pnl": -25.77,
            "status": "CLOSED",
            "classification": "LOSS",
            "result": "STOP LOSS",
        },
        "entry_view": {
            "strategy_name": "ICT",
            "decision": "ICT_CONFIRMED",
            "score": 90,
            "confirmation_percentage": 95,
            "h4_trend": "BEARISH",
            "h1_trend": "BEARISH",
            "structure_break": "BOS_BEARISH",
            "zone": "M15_OB_BEARISH",
            "passed": ["FVG_FORMED", "LIQUIDITY_SWEEP", "DISPLACEMENT_DETECTED"],
            "missing": ["SPREAD_PENALTY"],
        },
        "snapshots": [
            {"market": {"current_rr": 0.15, "current_price": 563.50}},
            {"market": {"current_rr": -0.50, "current_price": 570.00}},
            {"market": {"current_rr": -0.98, "current_price": 574.91}},
        ],
        "learning_eligibility": {
            "evidence_type": "ENTRY_CAPTURE",
            "reason": "VALIDAR_CIERRE_COMPLETO_DEL_SETUP",
        },
    }


def test_chatbot_explains_why_trade_won():
    audit = _mock_win_audit()
    resp = answer_trade_audit_inquiry(audit, "¿Por qué se ganó la operación?")
    assert resp["ok"] is True
    reply = resp["reply"]
    assert "Victoria" in reply
    assert "+2.50R" in reply
    assert "Take Profit" in reply
    assert "Score técnico" in reply


def test_chatbot_explains_why_trade_lost():
    audit = _mock_loss_audit()
    resp = answer_trade_audit_inquiry(audit, "¿Por qué se perdió la entrada?")
    assert resp["ok"] is True
    reply = resp["reply"]
    assert "Análisis de Pérdida" in reply
    assert "-0.98R" in reply
    assert "Stop Loss" in reply
    assert "MFE vs MAE" in reply
    assert "Penalización por spread elevado" in reply


def test_chatbot_explains_slippage_and_sl():
    audit = _mock_loss_audit()
    resp = answer_trade_audit_inquiry(audit, "¿Hubo deslizamiento o se respetó el Stop Loss?")
    assert resp["ok"] is True
    reply = resp["reply"]
    assert "Slippage" in reply or "Deslizamiento" in reply
    assert "574.91000" in reply
    assert "Cierre milimétrico exacto" in reply


def test_chatbot_explains_mfe_and_trajectory():
    audit = _mock_loss_audit()
    resp = answer_trade_audit_inquiry(audit, "¿Llegó a estar en ganancia o cuál fue el MFE?")
    assert resp["ok"] is True
    reply = resp["reply"]
    assert "MFE" in reply
    assert "+0.15R" in reply


def test_chatbot_explains_ai_learning():
    audit = _mock_loss_audit()
    resp = answer_trade_audit_inquiry(audit, "¿Qué aprendió la IA de este trade?")
    assert resp["ok"] is True
    reply = resp["reply"]
    assert "Aprendizaje" in reply or "Machine Learning" in reply
    assert "En espera de cierre de todo el setup para aprendizaje IA" in reply


def test_page_has_chat_ui_and_endpoints():
    root = Path(__file__).resolve().parents[1]
    page = (root / "dashboard" / "trade_audit_page.py").read_text(encoding="utf-8")
    dash = (root / "dashboard" / "realtime_dashboard.py").read_text(encoding="utf-8")

    assert "chatCard" in page
    assert "chatMessages" in page
    assert "askAuditChat" in page
    assert "submitAuditChat" in page
    assert "initAuditChat" in page
    assert "/audit/chat" in page

    assert "api_trade_audit_chat_match" in dash
    assert "api_trade_audit_chat_post" in dash
    assert "answer_trade_audit_inquiry" in dash
