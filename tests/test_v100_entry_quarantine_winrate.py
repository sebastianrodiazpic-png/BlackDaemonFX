from datetime import datetime, timedelta, timezone
import json
from types import SimpleNamespace

import pandas as pd

import strategy.smc.confirmation_engine as confirmation_module
from dashboard.account_metrics import build_account_payload
from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
from strategy.smc.chart_patterns import ChartPatternConfig, _effective_price_tolerance
from strategy.smc.confirmation_engine import M5ConfirmationConfig, evaluate_m5_confirmation


def _m5_data():
    rows = [
        ("2026-01-01 00:00", 100, 101, 99, 100.5),
        ("2026-01-01 00:05", 100.5, 101, 99.5, 100),
        ("2026-01-01 00:10", 100, 100.4, 99.2, 99.8),
        ("2026-01-01 00:15", 99.8, 102.5, 99.7, 102.3),
    ]
    frame = pd.DataFrame(rows, columns=["time", "open", "high", "low", "close"])
    frame["time"] = pd.to_datetime(frame["time"], utc=True)
    return frame


def _setup(frame):
    return pd.Series({
        "setup_time": frame.iloc[1]["time"],
        "ob_low": 99.0,
        "ob_high": 101.0,
        "trend_ok": True,
        "sweep_ok": True,
        "structure_break_ok": True,
        "premium_discount_ok": True,
    })


def test_optional_harmonic_is_bonus_not_confirmation_denominator():
    frame = _m5_data()
    result = evaluate_m5_confirmation(
        data=frame,
        setup=_setup(frame),
        retest_index=2,
        confirmation_index=3,
        direction="long",
        config=M5ConfirmationConfig(
            minimum_trade_score=70,
            harmonic_enabled=True,
            require_harmonic=False,
            require_chart_pattern=False,
            require_fvg=False,
        ),
    )
    assert result["confirmations_total"] == 13
    assert "harmonic_confirmation" not in result["missing_confirmations"]


def test_similar_opposing_chart_patterns_penalize_but_do_not_block(monkeypatch):
    frame = _m5_data()

    def conflict(*_args, **_kwargs):
        return {
            "chart_pattern_confirmed": True,
            "chart_pattern_conflict": True,
            "chart_pattern_conflict_level": "FUERZAS_SIMILARES",
            "chart_pattern_strength": 0.78,
            "chart_pattern_bonus": 8.0,
        }

    monkeypatch.setattr(confirmation_module, "detect_chart_pattern_confirmation", conflict)
    result = evaluate_m5_confirmation(
        data=frame,
        setup=_setup(frame),
        retest_index=2,
        confirmation_index=3,
        direction="long",
        config=M5ConfirmationConfig(
            minimum_trade_score=70,
            require_fvg=False,
            # v106 endureció FUERZAS_SIMILARES a bloqueo por defecto
            # (`block_similar_chart_pattern_forces=True`); este test valida
            # el comportamiento previo (solo penaliza) desactivándolo.
            block_similar_chart_pattern_forces=False,
        ),
    )
    assert result["chart_pattern_conflict_blocked"] is False
    assert result["chart_pattern_conflict_penalty"] == 10.0
    assert "MATERIAL_CHART_PATTERN_CONFLICT" not in result["structural_gate_failures"]


def test_chart_pattern_tolerance_is_capped_by_recent_range():
    frame = pd.DataFrame({
        "high": [100.10, 100.15, 100.12, 100.18] * 10,
        "low": [100.00, 100.05, 100.02, 100.08] * 10,
        "close": [100.05, 100.10, 100.07, 100.13] * 10,
    })
    cfg = ChartPatternConfig(price_tolerance=0.006)
    effective = _effective_price_tolerance(frame, cfg)
    assert cfg.minimum_price_tolerance <= effective < cfg.price_tolerance
    assert effective <= 0.002


class _Repo:
    def save_signal_once(self, payload):
        return 11, True

    def get_trade_by_execution_key(self, key):
        return None

    def open_trades(self, source=None):
        return []

    def save_account_snapshot(self, account):
        return None


class _Provider:
    connector = SimpleNamespace()

    def resolve_symbol(self, symbol):
        return symbol

    def ensure_symbol(self, symbol):
        return True

    def get_current_tick(self, symbol):
        return {"bid": 100.0, "ask": 100.0}


class _Analyzer:
    def analyze_symbol(self, symbol):
        return {
            "valid": True,
            "signal": {
                "direction": "BUY",
                "entry_time": "2026-09-03T12:00:00+00:00",
                "entry_price": 100.0,
                "stop_loss": 90.0,
                "risk_reward_ratio": 2.0,
            },
        }


class _MinimumVolumeExecutor:
    def assert_demo_account(self):
        return {"balance": 10000.0, "equity": 10000.0, "server": "Deriv-Demo"}

    def normalize_market_stops(self, *args, **kwargs):
        return {
            "valid": True,
            "entry_price": 100.0,
            "stop_loss": 90.0,
            "take_profit": 120.0,
            "constraints": {"digits": 2},
        }

    def calculate_volume(self, symbol, direction, entry, stop, risk_amount):
        if risk_amount < 90.0:
            raise ValueError("minimum volume risks more than requested")
        return {"volume": 0.1, "actual_risk_amount": 98.0}


def test_minimum_volume_split_error_reaches_safe_single_fallback():
    engine = LiveTradingEngine(
        provider=_Provider(),
        repository=_Repo(),
        config=LiveTradingConfig(
            execution_enabled=False,
            validate_order_in_dry_run=False,
            max_entry_drift_r=None,
        ),
        executor=_MinimumVolumeExecutor(),
    )
    engine.multi_timeframe = _Analyzer()
    result = engine.process_symbol("Step Index 500")
    assert result["action"] == "DRY_RUN_VALIDATED"
    assert result["execution_mode"] == "SINGLE_FALLBACK"
    assert result["split_failure"]["code"] == "VOLUMEN_MINIMO_SUPERA_RIESGO_DE_LA_PIERNA"


def test_legacy_marginal_quarantine_expires_automatically(tmp_path):
    path = tmp_path / "risk_quarantine.json"
    path.write_text(json.dumps({
        "Volatility 25 Index": {
            "symbol": "Volatility 25 Index",
            "quarantined_at": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
            "reason": "POST_FILL_RISK_HARD_CAP_BREACH",
            "target_risk_amount": 12.28035,
            "actual_risk_amount": 12.54,
        }
    }), encoding="utf-8")
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(
        quarantine_path=str(path),
        recoverable_quarantine_minutes=60,
    )
    assert engine._quarantine_result("Volatility 25 Index") is None
    assert json.loads(path.read_text(encoding="utf-8")) == {}


def test_waiting_scheduler_reports_available_symbols_not_zero_of_zero():
    class Repo:
        def __init__(self):
            self.runtime = None

        def upsert_worker_runtime_state(self, profile, magic, **kwargs):
            self.runtime = kwargs

        def save_audit_event(self, *args, **kwargs):
            return 1

    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(bot_profile="GOLD")
    engine.repository = Repo()
    engine._persist_audit_event(
        "DAEMON_CYCLE_START",
        payload={
            "runtime_state": "WAITING_NEW_M5_BAR",
            "symbols_count": 0,
            "selected_symbols_count": 1,
        },
    )
    assert engine.repository.runtime["symbols_processed"] == 0
    assert engine.repository.runtime["symbols_total"] == 1
    assert engine.repository.runtime["status"] == "WAITING_NEW_M5_BAR"


def test_account_exposes_leg_and_logical_setup_win_rates():
    class Repo:
        def account_trade_history_dataframe(self, source="DEMO"):
            return pd.DataFrame([
                {
                    "id": 1, "status": "CLOSED", "net_pnl": 50.0,
                    "realized_rr": 1.0, "risk_amount": 50.0,
                    "details": {"metadata": {"strategy_name": "ORB_NEW_YORK", "parent_execution_key": "A"}},
                },
                {
                    "id": 2, "status": "CLOSED", "net_pnl": 0.0,
                    "realized_rr": 0.0, "risk_amount": 50.0,
                    "details": {"metadata": {"strategy_name": "ORB_NEW_YORK", "parent_execution_key": "A"}},
                },
                {
                    "id": 3, "status": "CLOSED", "net_pnl": -40.0,
                    "realized_rr": -0.8, "risk_amount": 50.0,
                    "details": {"metadata": {"strategy_name": "SMC", "parent_execution_key": "B"}},
                },
                {
                    "id": 4, "status": "CLOSED", "net_pnl": 0.0,
                    "realized_rr": None, "risk_amount": 50.0,
                    "result": "EMERGENCY_RISK_EXIT",
                    "details": {"metadata": {"strategy_name": "SMC", "parent_execution_key": "C"}},
                },
            ])

    stats = build_account_payload(Repo())["stats"]
    assert stats["decisive_legs"] == 2
    assert stats["win_rate"] == 50.0
    assert stats["logical_setups"] == 2
    assert stats["logical_wins"] == 1
    assert stats["logical_losses"] == 1
    assert stats["setup_win_rate"] == 50.0
    assert {row["strategy"] for row in stats["by_strategy"]} == {
        "ORB_NEW_YORK", "SMC"
    }
