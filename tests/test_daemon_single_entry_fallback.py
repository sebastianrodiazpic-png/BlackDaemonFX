from types import SimpleNamespace

from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine


class Repo:
    def save_signal_once(self, payload):
        return 11, True
    def get_trade_by_execution_key(self, key):
        return None
    def open_trades(self, source=None):
        return []
    def save_account_snapshot(self, account):
        pass


class Provider:
    connector = SimpleNamespace()
    def resolve_symbol(self, symbol):
        return symbol
    def ensure_symbol(self, symbol):
        return True
    def get_current_tick(self, symbol):
        return {"bid": 100.0, "ask": 100.0}


class Analyzer:
    def analyze_symbol(self, symbol):
        return {
            "valid": True,
            "signal": {
                "direction": "BUY",
                "entry_time": "2026-08-28T12:00:00+00:00",
                "entry_price": 100.0,
                "stop_loss": 90.0,
                "risk_reward_ratio": 2.0,
                "divergence_confirmation": True,
                "divergence_type": "DIVERGENCIA_ALCISTA_REGULAR",
            },
        }


class FallbackExecutor:
    def __init__(self, single_risk=98.0):
        self.single_risk = single_risk
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
        # Para 0.5% el lote mínimo fuerza $60 > $50 + tolerancia => split inviable.
        # Para 1% puede ajustarse a un riesgo seguro de $98.
        actual = 60.0 if risk_amount < 100.0 else self.single_risk
        return {"volume": 0.1, "actual_risk_amount": actual}


def _engine(executor):
    engine = LiveTradingEngine(
        provider=Provider(),
        repository=Repo(),
        config=LiveTradingConfig(
            execution_enabled=False,
            validate_order_in_dry_run=False,
            max_entry_drift_r=None,
            risk_percent=1.0,
            split_entries_enabled=True,
            single_entry_fallback_enabled=True,
            single_entry_target_rr=2.0,
        ),
        executor=executor,
    )
    engine.multi_timeframe = Analyzer()
    return engine


def test_split_risk_failure_falls_back_to_one_safe_entry():
    result = _engine(FallbackExecutor(single_risk=98.0)).process_symbol("Volatility 75 Index")
    assert result["action"] == "DRY_RUN_VALIDATED"
    assert result["execution_mode"] == "SINGLE_FALLBACK"
    assert len(result["legs"]) == 1
    leg = result["legs"][0]
    assert leg["name"] == "SINGLE"
    assert leg["risk_percent"] == 1.0
    assert leg["target_rr"] == 2.0
    assert leg["take_profit"] == 120.0
    assert result["actual_risk_amount"] == 98.0
    assert result["actual_risk_percent"] == 0.98
    assert result["split_failure"]["code"] == "RIESGO_REAL_SUPERA_LIMITE_DE_LA_ENTRADA"


def test_single_fallback_is_rejected_when_it_also_exceeds_one_percent():
    result = _engine(FallbackExecutor(single_risk=120.0)).process_symbol("Volatility 75 Index")
    assert result["action"] == "OPERACION_RECHAZADA_POR_RIESGO"
    assert result["reason"] == "NI_LA_DIVISION_NI_LA_ENTRADA_UNICA_RESPETAN_EL_RIESGO_MAXIMO"
    assert result["single_failure"]["code"] == "RIESGO_REAL_SUPERA_LIMITE_DE_LA_ENTRADA"
