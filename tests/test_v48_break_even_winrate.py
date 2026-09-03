
import pandas as pd

from dashboard.account_metrics import classify_close, build_account_payload
from reporting.trade_report_exporter import TradeReportExporter
from trade_outcome_policy import (
    BREAK_EVEN_RR_TOLERANCE,
    decisive_outcome,
    is_break_even_rr,
)


def recovered_trade(rr=0.01, pnl=0.33):
    return {
        "id": 3,
        "instrument": "Jump 100 Index",
        "direction": "BUY",
        "status": "CLOSED",
        "result": "WIN",
        "entry_time": pd.Timestamp("2026-08-31T15:06:19Z"),
        "exit_time": pd.Timestamp("2026-08-31T16:50:47Z"),
        "planned_rr": 3.95,
        "realized_rr": rr,
        "net_pnl": pnl,
        "risk_percent": 0.5,
        "details": {"metadata": {"trade_leg": "RECOVERED_MT5"}},
    }


def test_small_positive_rr_is_break_even_not_win():
    trade = recovered_trade()
    assert BREAK_EVEN_RR_TOLERANCE == 0.25
    assert is_break_even_rr(trade["realized_rr"])
    assert classify_close(trade) == "BREAK EVEN / OTRO"
    assert decisive_outcome(
        realized_rr=trade["realized_rr"],
        net_pnl=trade["net_pnl"],
        status=trade["status"],
        classification=classify_close(trade),
    ) == "BREAK_EVEN"


def test_screenshot_six_trade_example_becomes_40_percent_winrate():
    rows = [
        {
            "id": 1, "instrument": "Multi Step 4 Index", "direction": "BUY",
            "status": "CLOSED", "result": "WIN", "entry_time": "2026-08-31T12:11:02Z",
            "exit_time": "2026-08-31T16:28:17Z", "planned_rr": 203.57,
            "realized_rr": 202.73, "net_pnl": 196.65, "risk_percent": 0.01,
            "details": {"metadata": {"trade_leg": "RECOVERED_MT5"}},
        },
        {
            "id": 2, "instrument": "Jump 100 Index", "direction": "BUY",
            "status": "CLOSED", "result": "WIN", "entry_time": "2026-08-31T15:06:18Z",
            "exit_time": "2026-08-31T16:09:38Z", "planned_rr": 0.97,
            "realized_rr": 0.98, "net_pnl": 48.30, "risk_percent": 0.5,
            "details": {"metadata": {"trade_leg": "RECOVERED_MT5"}},
        },
        recovered_trade(),
        {
            "id": 4, "instrument": "Volatility 25 (1s) Index", "direction": "SELL",
            "status": "CLOSED", "result": "LOSS", "entry_time": "2026-08-31T15:55:11Z",
            "exit_time": "2026-08-31T16:31:42Z", "planned_rr": 2.0,
            "realized_rr": -1.02, "net_pnl": -99.02, "risk_percent": 1.0,
            "details": {"metadata": {"trade_leg": "SINGLE"}},
        },
        {
            "id": 5, "instrument": "Boom 99 Index", "direction": "BUY",
            "status": "CLOSED", "result": "LOSS", "entry_time": "2026-08-31T15:57:05Z",
            "exit_time": "2026-08-31T16:11:03Z", "planned_rr": 1.0,
            "realized_rr": -1.0, "net_pnl": -48.95, "risk_percent": 0.5,
            "details": {"metadata": {"trade_leg": "TP1"}},
        },
        {
            "id": 6, "instrument": "Boom 99 Index", "direction": "BUY",
            "status": "CLOSED", "result": "LOSS", "entry_time": "2026-08-31T15:57:08Z",
            "exit_time": "2026-08-31T16:11:03Z", "planned_rr": 4.0,
            "realized_rr": -0.99, "net_pnl": -48.67, "risk_percent": 0.5,
            "details": {"metadata": {"trade_leg": "RUNNER"}},
        },
    ]

    class Repo:
        def latest_account_snapshot(self):
            return None
        def latest_account_stats_reset(self, source="DEMO"):
            return None
        def account_trade_history_dataframe(self, source="DEMO"):
            return pd.DataFrame(rows)

    payload = build_account_payload(Repo(), source="DEMO")
    stats = payload["stats"]

    assert stats["closed"] == 6
    assert stats["wins"] == 2
    assert stats["losses"] == 3
    assert stats["break_even"] == 1
    assert stats["win_rate"] == 40.0


def test_report_exporter_calls_small_positive_rr_break_even():
    exporter = object.__new__(TradeReportExporter)
    row = recovered_trade()
    row["pierna_operacion"] = "RECOVERED_MT5"
    assert exporter._classify_close(row) == "PUNTO DE EQUILIBRIO / OTRO"


def test_above_neutral_band_is_decisive_win():
    assert decisive_outcome(
        realized_rr=0.30,
        net_pnl=10.0,
        status="CLOSED",
    ) == "WIN"


def test_small_negative_rr_is_also_break_even():
    assert decisive_outcome(
        realized_rr=-0.10,
        net_pnl=-2.0,
        status="CLOSED",
    ) == "BREAK_EVEN"
