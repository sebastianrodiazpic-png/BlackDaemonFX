"""v126 (12-nov-2026): spread de referencia de ICT en cruces FX sin USD y guardado del order_check de MT5."""
from __future__ import annotations

import importlib
from pathlib import Path

import pandas as pd
import pytest

from strategy.ict.ict_strategy import find_inversion_fvg_and_bpr_setups, ict_reference_spread
from strategy.execution.order_check_summary import (
    format_order_check_line,
    order_check_failures,
    summarize_order_check,
)

ROOT = Path(__file__).resolve().parents[1]


# --------------------------------------------------------------------------- ICT: spread de referencia

@pytest.mark.parametrize("symbol, expected", [
    ("AUDNZD", 0.00015),
    ("AUDNZDmicro", 0.00015),
    ("EURCAD", 0.00015),
    ("GBPNZD", 0.00015),
    ("EURJPY", 0.015),
    ("CHFJPYmicro", 0.015),
])
def test_fx_crosses_without_usd_use_pip_reference(monkeypatch, symbol, expected):
    monkeypatch.delenv("DAEMONBLACKFX_ICT_FX_CROSS_SPREAD_FIX", raising=False)
    assert ict_reference_spread(symbol) == pytest.approx(expected)


@pytest.mark.parametrize("symbol, expected", [
    ("EURUSD", 0.00015), ("USDJPY", 0.00015), ("XAUUSD", 0.00015), ("BTCUSD", 0.00015),
    ("Volatility 75 Index", 0.5), ("Step Index 500", 0.5), ("Germany 40", 0.5), ("UK Brent Oil", 0.5),
    ("XAUEUR", 0.5),
])
def test_other_symbols_keep_previous_reference(monkeypatch, symbol, expected):
    monkeypatch.delenv("DAEMONBLACKFX_ICT_FX_CROSS_SPREAD_FIX", raising=False)
    assert ict_reference_spread(symbol) == pytest.approx(expected)


def test_switch_off_restores_legacy_value(monkeypatch):
    monkeypatch.setenv("DAEMONBLACKFX_ICT_FX_CROSS_SPREAD_FIX", "0")
    assert ict_reference_spread("AUDNZD") == pytest.approx(0.5)
    assert ict_reference_spread("EURJPY") == pytest.approx(0.5)


def _bpr_sell_frame(base: float, step: float) -> pd.DataFrame:
    # c_m2 alto, c_m1 por debajo con hueco (c_m1.high < c_m2.low), c_m0 cierra bajo c_m1.low.
    rows = [
        (base, base + 2 * step, base - step, base + step),
        (base, base + 2 * step, base - step, base + step),
        (base + 5 * step, base + 6 * step, base + 4 * step, base + 4.5 * step),   # c_m2
        (base + 3 * step, base + 3.5 * step, base + 2 * step, base + 2.2 * step),  # c_m1
        (base + 2 * step, base + 2.1 * step, base + 1 * step, base + 1.2 * step),  # c_m0
    ]
    return pd.DataFrame(rows, columns=["open", "high", "low", "close"])


def test_audnzd_bpr_stop_is_a_few_pips_not_one_unit(monkeypatch):
    """Caso real 12-nov: AUDNZD SELL entrada 1.22805 con SL 2.22862 (10.000 pips)."""
    monkeypatch.delenv("DAEMONBLACKFX_ICT_FX_CROSS_SPREAD_FIX", raising=False)
    df = _bpr_sell_frame(1.2280, 0.0002)
    setup = find_inversion_fvg_and_bpr_setups(
        df, curr_idx=len(df) - 1, intended_direction="SELL", spread=ict_reference_spread("AUDNZD"))
    assert setup and setup["valid"]
    distance = setup["stop_loss"] - setup["entry_price"]
    assert 0 < distance < 0.0050  # menos de 50 pips



def _ifvg_sell_frame() -> pd.DataFrame:
    # FVG alcista 1.2280-1.2290, perforado con cierre bajo 1.2280 y retesteado por la vela actual.
    rows = [
        (1.2270, 1.2275, 1.2265, 1.2272),
        (1.2272, 1.2280, 1.2268, 1.2278),  # c0 (high 1.2280)
        (1.2278, 1.2296, 1.2277, 1.2294),  # c1 alcista
        (1.2294, 1.2300, 1.2290, 1.2292),  # c2 (low 1.2290) -> FVG 1.2280-1.2290
        (1.2292, 1.2293, 1.2270, 1.2272),  # perfora: cierre < 1.2280
        (1.2272, 1.2284, 1.2268, 1.2276),  # retesteo actual (high >= 1.2280)
    ]
    return pd.DataFrame(rows, columns=["open", "high", "low", "close"])


def test_audnzd_ifvg_reproduces_bug_and_fix(monkeypatch):
    """Caso real 12-nov: AUDNZD SELL entrada 1.22805, SL 2.22862 (gap_top + 2 x 0.5)."""
    monkeypatch.delenv("DAEMONBLACKFX_ICT_FX_CROSS_SPREAD_FIX", raising=False)
    df = _ifvg_sell_frame()
    legacy = find_inversion_fvg_and_bpr_setups(df, curr_idx=len(df) - 1, intended_direction="SELL", spread=0.5)
    assert legacy and legacy["stop_loss"] == pytest.approx(1.2290 + 1.0)
    fixed = find_inversion_fvg_and_bpr_setups(
        df, curr_idx=len(df) - 1, intended_direction="SELL", spread=ict_reference_spread("AUDNZD"))
    assert fixed and fixed["stop_loss"] == pytest.approx(1.2290 + 0.0003)
    assert fixed["stop_loss"] - fixed["entry_price"] < 0.0050


def test_strategy_no_longer_inlines_legacy_spread():
    source = (ROOT / "strategy" / "ict" / "ict_strategy.py").read_text(encoding="utf-8")
    body = source.split("def ict_reference_spread", 1)[1].split("\ndef ", 1)[1]
    assert '0.00015 if "USD" in symbol else 0.5' not in body
    assert body.count("ict_reference_spread(symbol)") >= 2


# --------------------------------------------------------------------------- MT5 order_check

REJECTED = {
    "valid": False,
    "reason": "Invalid stops",
    "retcode": 10016,
    "comment": "Invalid stops",
    "request": {"action": 1, "symbol": "EURAUD", "volume": 0.31, "price": 1.61806, "sl": 1.61844,
                "tp": 1.61768, "deviation": 20, "type_filling": 1, "magic": 26082201},
    "attempts": [
        {"filling": 1, "filling_name": "IOC", "retcode": 10016, "comment": "Invalid stops",
         "result": {"retcode": 10016, "comment": "Invalid stops", "margin": 0.0}, "request": {"big": "x" * 500}},
        {"filling": 2, "filling_name": "RETURN", "retcode": 10016, "comment": "Invalid stops"},
    ],
    "filling_diagnostics": {"huge": list(range(100))},
}


def test_summary_keeps_retcode_comment_and_request():
    summary = summarize_order_check(REJECTED)
    assert summary["retcode"] == 10016
    assert summary["retcode_description"] == "stops inválidos"
    assert summary["comment"] == "Invalid stops"
    assert summary["request"]["sl"] == pytest.approx(1.61844)
    assert "magic" not in summary["request"]
    assert [a["retcode"] for a in summary["attempts"]] == [10016, 10016]
    assert "filling_diagnostics" not in summary
    assert "request" not in summary["attempts"][0]


def test_summary_handles_empty_and_none():
    assert summarize_order_check(None) is None
    assert summarize_order_check({}) is None
    assert summarize_order_check({"valid": False, "retcode": None, "comment": "ORDER_CHECK_NONE"})["comment"] == "ORDER_CHECK_NONE"


def test_failures_and_console_line(monkeypatch):
    monkeypatch.delenv("DAEMONBLACKFX_PERSIST_ORDER_CHECK_DETAIL", raising=False)
    row = {
        "action": "OPERACION_RECHAZADA_POR_RIESGO",
        "split_failure": {"code": "ORDEN_RECHAZADA_EN_VALIDACION_MT5", "leg": "TP1", "order_check": REJECTED},
        "single_failure": {"code": "VOLUMEN_MINIMO_SUPERA_RIESGO_DE_LA_PIERNA", "leg": "SINGLE"},
    }
    failures = order_check_failures(row)
    assert list(failures) == ["split_failure"]
    line = format_order_check_line(row)
    assert line.startswith("MT5 order_check: TP1 retcode=10016 (stops inválidos)")
    monkeypatch.setenv("DAEMONBLACKFX_PERSIST_ORDER_CHECK_DETAIL", "0")
    assert format_order_check_line(row) is None


def test_engine_compaction_persists_order_check(monkeypatch):
    try:
        engine_mod = importlib.import_module("strategy.execution.live_trading_engine")
    except Exception as exc:  # pragma: no cover - entorno sin dependencias del motor
        pytest.skip(f"motor no importable aquí: {exc}")
    monkeypatch.delenv("DAEMONBLACKFX_PERSIST_ORDER_CHECK_DETAIL", raising=False)
    row = {
        "symbol": "EURAUD", "action": "OPERACION_RECHAZADA_POR_RIESGO",
        "reason": "NI_LA_DIVISION_NI_LA_ENTRADA_UNICA_RESPETAN_EL_RIESGO_MAXIMO",
        "split_failure": {"code": "ORDEN_RECHAZADA_EN_VALIDACION_MT5", "leg": "TP1", "order_check": REJECTED},
        "single_failure": {"code": "ORDEN_RECHAZADA_EN_VALIDACION_MT5", "leg": "SINGLE", "order_check": REJECTED},
        "analysis": {},
    }
    out = engine_mod.LiveTradingEngine._compact_symbol_result(row)
    metrics = out.get("risk_metrics") or (out.get("result") or {}).get("risk_metrics")
    assert metrics["split_failure"]["code"] == "ORDEN_RECHAZADA_EN_VALIDACION_MT5"
    assert metrics["split_failure"]["order_check"]["retcode"] == 10016
    assert metrics["single_failure"]["order_check"]["comment"] == "Invalid stops"

    monkeypatch.setenv("DAEMONBLACKFX_PERSIST_ORDER_CHECK_DETAIL", "0")
    out = engine_mod.LiveTradingEngine._compact_symbol_result(row)
    metrics = out.get("risk_metrics") or (out.get("result") or {}).get("risk_metrics")
    assert "order_check" not in metrics["split_failure"]
