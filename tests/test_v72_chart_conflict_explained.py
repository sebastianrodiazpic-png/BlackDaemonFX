import pandas as pd
from pathlib import Path

from strategy.smc.chart_patterns import (
    ChartPatternConfig,
    detect_chart_pattern_confirmation,
    _explain_chart_pattern_conflict,
)
from strategy.execution.live_trading_engine import LiveTradingEngine


def _mixed_structure():
    # Pivots deliberately create a bullish triple-bottom family and a bearish
    # double/triple-top family in the same recent window.
    closes=[10,12,8,12,10,12,8,12,10,12,8,11,10]
    rows=[]
    for i,c in enumerate(closes):
        high=c+0.35
        low=c-0.35
        rows.append({
            "time":pd.Timestamp("2026-09-01T10:00:00Z")+pd.Timedelta(minutes=5*i),
            "open":c-0.1,"high":high,"low":low,"close":c,
        })
    return pd.DataFrame(rows)


def test_conflict_explanation_compares_supporting_and_opposing_patterns():
    # v102: un patrón contrario más fuerte es CONTRA_MAS_FUERTE aunque el
    # margen sea estrecho. Antes caía en FUERZAS_SIMILARES y no bloqueaba.
    supporting={"pattern":"TRIPLE_BOTTOM","direction":"BUY","strength":.78}
    conflicting={"pattern":"HEAD_AND_SHOULDERS","direction":"SELL","strength":.82}
    level,reason,delta=_explain_chart_pattern_conflict(supporting,conflicting,"BUY")
    assert level=="CONTRA_MAS_FUERTE"
    assert "TRIPLE_BOTTOM BUY 78%" in reason
    assert "HEAD_AND_SHOULDERS SELL 82%" in reason
    assert delta==.04


def test_similar_forces_require_aligned_pattern_to_hold_its_ground():
    # FUERZAS_SIMILARES queda para el empate o una ventaja alineada estrecha.
    supporting={"pattern":"TRIPLE_BOTTOM","direction":"BUY","strength":.82}
    conflicting={"pattern":"HEAD_AND_SHOULDERS","direction":"SELL","strength":.78}
    level,reason,delta=_explain_chart_pattern_conflict(supporting,conflicting,"BUY")
    assert level=="FUERZAS_SIMILARES"
    assert "fuerza similar" in reason
    assert delta==-.04


def test_stronger_opposing_pattern_is_identified():
    supporting={"pattern":"DOUBLE_BOTTOM","direction":"BUY","strength":.74}
    conflicting={"pattern":"HEAD_AND_SHOULDERS","direction":"SELL","strength":.86}
    level,reason,delta=_explain_chart_pattern_conflict(supporting,conflicting,"BUY")
    assert level=="CONTRA_MAS_FUERTE"
    assert "es más fuerte" in reason
    assert delta==.12



def test_live_current_view_preserves_conflict_explanation():
    analysis={
        "valid":True,
        "action":"READY_TO_ENTER",
        "direction":"BUY",
        "h1":{"context":{"trend":"BULLISH"}},
        "m15":{"setup":{"zone":"DISCOUNT","structure_break_type":"BOS"}},
        "signal":{
            "direction":"BUY",
            "confirmation_decision":"ADAPTIVE_80_CONFIRMED",
            "trade_score":100,
            "confirmation_percentage":85.7,
            "chart_pattern_confirmed":True,
            "chart_pattern_name":"TRIPLE_BOTTOM",
            "chart_pattern_strength":.78,
            "chart_pattern_conflict":True,
            "chart_pattern_supporting_pattern":"TRIPLE_BOTTOM",
            "chart_pattern_supporting_direction":"BUY",
            "chart_pattern_supporting_strength":.78,
            "chart_pattern_conflicting_pattern":"HEAD_AND_SHOULDERS",
            "chart_pattern_conflicting_direction":"SELL",
            "chart_pattern_conflicting_strength":.82,
            "chart_pattern_conflict_level":"FUERZAS_SIMILARES",
            "chart_pattern_conflict_reason":"Patrones opuestos con fuerza similar.",
        },
    }
    view=LiveTradingEngine._current_strategy_view_from_analysis(analysis)
    assert view["chart_pattern_supporting_pattern"]=="TRIPLE_BOTTOM"
    assert view["chart_pattern_conflicting_pattern"]=="HEAD_AND_SHOULDERS"
    assert view["chart_pattern_conflict_reason"]=="Patrones opuestos con fuerza similar."


def test_dashboard_explains_both_sides_of_conflict():
    root=Path(__file__).resolve().parents[1]
    text=(root/"dashboard"/"realtime_dashboard.py").read_text(encoding="utf-8")
    assert "A favor:" in text
    assert "En contra:" in text
    assert "Nivel conflicto:" in text
    assert "chart_pattern_conflict_reason" in text


def test_account_keeps_conflict_explanation():
    root=Path(__file__).resolve().parents[1]
    page=(root/"dashboard"/"account_page.py").read_text(encoding="utf-8")
    metrics=(root/"dashboard"/"account_metrics.py").read_text(encoding="utf-8")
    assert "Conflicto chartista:" in page
    assert "chart_pattern_conflicting_pattern" in metrics
    assert "chart_pattern_supporting_pattern" in metrics
