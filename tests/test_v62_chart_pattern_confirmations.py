import pandas as pd
from pathlib import Path

from strategy.smc.chart_patterns import (
    ChartPatternConfig,
    detect_chart_pattern_confirmation,
)
from database.repository import TradingRepository


def _double_bottom():
    closes=[10,9,8,9,10,9,8,9,10,11]
    rows=[]
    for i,c in enumerate(closes):
        rows.append((pd.Timestamp("2026-01-01",tz="UTC")+pd.Timedelta(minutes=5*i),
                     c-.1,c+.35,c-.35,c))
    return pd.DataFrame(rows,columns=["time","open","high","low","close"])


def test_double_bottom_is_detected_and_aligned_for_buy():
    df=_double_bottom()
    r=detect_chart_pattern_confirmation(
        df,"long",len(df)-1,
        ChartPatternConfig(pivot_window=1,price_tolerance=.01,minimum_strength=.70)
    )
    assert r["chart_pattern_confirmed"] is True
    assert r["chart_pattern_name"] in {"DOUBLE_BOTTOM","TRIPLE_BOTTOM","CUP_AND_HANDLE","ROUNDING_BOTTOM"}
    assert r["chart_pattern_direction"] == "BUY"
    assert r["chart_pattern_strength"] >= .70
    assert r["chart_pattern_evidence"].get("anchors")


def test_pattern_is_soft_confluence_by_default():
    cfg=ChartPatternConfig()
    assert cfg.require_pattern is False
    assert cfg.bonus_points > 0


def test_entry_confirmation_audit_is_persistent_and_immutable(tmp_path):
    repo=TradingRepository(db_path=tmp_path/"v62.db")
    # trade visual audit is keyed by trade_id and entry context is write-once.
    repo.upsert_trade_visual_audit(
        77,instrument="Boom 1000 Index",source="DEMO",
        entry_context={
            "decision":"STRICT_CONFIRMED",
            "passed":["h1_trend","liquidity_sweep","m15_structure"],
            "confirmation_details":{"rejection":True,"micro_structure":True},
            "chart_pattern_confirmed":True,
            "chart_pattern_name":"DOUBLE_BOTTOM",
            "chart_pattern_strength":.82,
            "chart_pattern_evidence":{"anchors":[{"time":"2026-01-01T00:00:00+00:00","price":100.0}]},
        }
    )
    repo.upsert_trade_visual_audit(
        77,instrument="Boom 1000 Index",source="DEMO",
        entry_context={"chart_pattern_name":"SHOULD_NOT_OVERWRITE"}
    )
    rows=repo.trade_visual_audits(source="DEMO")
    row=next(x for x in rows if x["trade_id"]==77)
    ctx=row["entry_context"]
    assert ctx["chart_pattern_name"]=="DOUBLE_BOTTOM"
    assert ctx["confirmation_details"]["micro_structure"] is True


def test_visual_dashboard_has_chart_pattern_overlay():
    root=Path(__file__).resolve().parents[1]
    text=(root/"dashboard"/"realtime_dashboard.py").read_text(encoding="utf-8")
    assert "chart_pattern_evidence" in text
    assert "chart_pattern_name" in text
    assert "Patrón chartista" in text


def test_account_page_exposes_persistent_confirmations():
    root=Path(__file__).resolve().parents[1]
    text=(root/"dashboard"/"account_page.py").read_text(encoding="utf-8")
    assert "Confirmaciones persistentes" in text
    assert "auditHtml" in text
    assert "Detalle técnico persistido" in text
