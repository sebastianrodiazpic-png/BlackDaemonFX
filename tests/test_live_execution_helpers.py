from types import SimpleNamespace
import pytest

from brokers.mt5_execution import MT5ExecutionProvider, MT5ExecutionError


def test_normalize_volume_rounds_down_to_step():
    info = SimpleNamespace(volume_min=0.01, volume_max=10.0, volume_step=0.01)
    assert MT5ExecutionProvider.normalize_volume(0.037, info) == 0.03


def test_min_volume_does_not_force_excess_risk(monkeypatch):
    import brokers.mt5_execution as module

    class DummyConnector:
        def is_connected(self): return True
        def connect(self): return True

    provider = MT5ExecutionProvider(DummyConnector())
    info = SimpleNamespace(
        volume_min=1.0, volume_max=100.0, volume_step=1.0,
        trade_tick_size=1.0, trade_tick_value_loss=10.0, trade_tick_value=10.0,
    )
    monkeypatch.setattr(provider, 'symbol_spec', lambda symbol: info)
    with pytest.raises(MT5ExecutionError):
        provider.calculate_volume('X', 'BUY', 100.0, 99.0, 5.0)
