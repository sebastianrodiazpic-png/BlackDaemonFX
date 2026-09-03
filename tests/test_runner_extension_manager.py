
import pandas as pd

from strategy.execution.runner_extension_manager import evaluate_runner_continuation, rr_price


def _uptrend():
    rows = []
    base = 100.0
    for i in range(24):
        o = base + i * 0.45
        c = o + 0.32
        rows.append((
            pd.Timestamp("2026-08-30T12:00:00Z") + pd.Timedelta(minutes=5*i),
            o, c + 0.18, o - 0.15, c
        ))
    return pd.DataFrame(rows, columns=["time", "open", "high", "low", "close"])


def test_rr_price_buy_and_sell():
    assert rr_price(100, 90, "BUY", 1) == 110
    assert rr_price(100, 110, "SELL", 2) == 80


def test_clean_uptrend_can_continue_runner():
    decision = evaluate_runner_continuation(
        _uptrend(),
        direction="BUY",
        stage_rr=2.0,
    )
    assert decision.continue_runner is True


def test_insufficient_market_data_blocks_extension():
    decision = evaluate_runner_continuation(
        _uptrend().head(5),
        direction="BUY",
        stage_rr=2.0,
    )
    assert decision.continue_runner is False
    assert decision.reason == "DATOS_M5_INSUFICIENTES_PARA_EXTENSION"
