import json

from tools.market_data_shadow_report import summarize


def test_shadow_report_groups_and_calculates_pass_rate(tmp_path):
    output = tmp_path / "shadow.jsonl"
    rows = [
        {"kind": "CANDLES", "symbol": "EURUSD", "timeframe": "M5",
         "comparison_available": True, "within_tolerance": True,
         "matched_closed_candles": 20, "maximum_close_divergence_range_ratio": 0.02},
        {"kind": "CANDLES", "symbol": "EURUSD", "timeframe": "M5",
         "comparison_available": True, "within_tolerance": False,
         "matched_closed_candles": 18, "maximum_close_divergence_range_ratio": 0.20},
    ]
    output.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
    result = summarize(output)
    assert result[0]["records"] == 2
    assert result[0]["matched_candles"] == 38
    assert result[0]["tolerance_pass_rate"] == 0.5
    assert result[0]["divergence_ratio_p95"] == 0.2
