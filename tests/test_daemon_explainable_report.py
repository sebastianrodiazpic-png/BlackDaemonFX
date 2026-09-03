import json
import pandas as pd

from reporting.trade_report_exporter import TradeReportExporter


class DummyRepository:
    pass


def test_report_enrichment_documents_entry_reason_and_outcome():
    exporter = TradeReportExporter(DummyRepository(), output_path="unused.xlsx")
    details = {
        "metadata": {
            "execution_mode": "SPLIT",
            "trade_leg": "TP1",
            "trade_score": 88,
            "trade_grade": "A",
            "confirmation_decision": "ADAPTIVE_75_CONFIRMED",
            "confirmation_percentage": 80,
            "confirmations_passed": 12,
            "confirmations_total": 15,
            "passed_confirmations": ["h1_trend", "liquidity_sweep", "m15_structure", "fresh_order_block"],
            "missing_confirmations": ["strong_close"],
            "critical_confirmation_failures": [],
            "divergence_confirmation": True,
            "divergence_type": "DIVERGENCIA_ALCISTA_REGULAR",
            "harmonic_confirmed": False,
            "m15_structure_break_type": "CHOCH",
            "h1_trend": "BULLISH",
            "m15_zone": "DISCOUNT",
        }
    }
    df = pd.DataFrame([{
        "status": "CLOSED",
        "result": "WIN",
        "planned_rr": 1.0,
        "realized_rr": 1.01,
        "net_pnl": 50.0,
        "details_json": json.dumps(details),
    }])

    out = exporter._enrich_trades_for_report(df)
    row = out.iloc[0]
    assert row["decision_entrada_es"] == "CONFIRMADA POR REGLA ADAPTATIVA >=75%"
    assert row["porcentaje_confirmaciones"] == 80.0
    assert "Barrido de liquidez" in row["confirmaciones_cumplidas_es"]
    assert "Cierre fuerte" in row["confirmaciones_faltantes_es"]
    assert "divergencia confirmada" in row["motivo_entrada_es"]
    assert row["clasificacion_cierre_es"] == "TP1"
    assert row["resultado_monetario_es"] == "GANADOR"
