from services.live_demo_smoke_test_service import (
    LiveDemoSmokeTestConfig,
    LiveDemoSmokeTestService,
)


class _Info:
    volume_min = 0.1
    volume_step = 0.01
    volume_max = 10.0


class _Provider:
    def assert_demo_account(self):
        return None

    def ensure_symbol(self, symbol):
        return _Info()

    def symbol_spec(self, symbol):
        return _Info()

    def get_symbol_constraints(self, symbol):
        return {
            "point": 0.001,
            "stops_level_points": 22451,
            "volume_min": 0.1,
        }

    def normalize_volume(self, volume, info):
        return float(volume)

    def normalize_market_stops(self, **kwargs):
        assert kwargs["risk_reward"] == 2.0
        return {
            "valid": True,
            "reason": "STOPS_NORMALIZED",
            "entry_price": kwargs["entry_price"],
            "stop_loss": 9222.742,
            "take_profit": 9293.245,
            "minimum_stop_distance": 23.451,
            "used_stop_distance": 23.501,
        }


class _Executor:
    def __init__(self, provider):
        self.execution_provider = provider

    def get_position(self, ticket):
        return {"position_ticket": ticket}


class _Lifecycle:
    execution_id = "deal-1"
    position_ticket = "position-1"


class _LifecycleManager:
    def __init__(self):
        self.signal = None

    def process_signal_with_executor(self, signal, volume):
        self.signal = signal
        return _Lifecycle()

    def close_execution(self, lifecycle, reason):
        return {"closed": True}


class _Repository:
    def get_trade_by_execution_key(self, execution_id):
        return {"execution_id": execution_id}


class _Exporter:
    output_path = "smoke.xlsx"


class _Reporting:
    exporter = _Exporter()


def test_smoke_uses_provider_stop_normalization(monkeypatch):
    provider = _Provider()
    service = LiveDemoSmokeTestService(
        execution_provider=provider,
        repository=_Repository(),
        config=LiveDemoSmokeTestConfig(
            symbol="Boom 100 Index",
            auto_close=False,
        ),
    )
    service.executor = _Executor(provider)
    service.lifecycle_manager = _LifecycleManager()
    service.reporting_service = _Reporting()
    monkeypatch.setattr(
        service,
        "_tick",
        lambda symbol: {"bid": 9246.200, "ask": 9246.243, "time": 1},
    )

    result = service.run()

    assert service.lifecycle_manager.signal["stop_loss"] == 9222.742
    assert service.lifecycle_manager.signal["take_profit"] == 9293.245
    assert result["stops"]["reason"] == "STOPS_NORMALIZED"
    assert result["closed"] is False
