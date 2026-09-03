from types import SimpleNamespace

from services.execution_preflight_service import ExecutionPreflightService


class FakeRepository:
    def __init__(self):
        self.snapshots = []

    def save_account_snapshot(self, account):
        self.snapshots.append(account)


class FakeProvider:
    def account_info(self):
        return {
            "login": 1,
            "server": "Deriv-Demo",
            "currency": "USD",
            "balance": 1000.0,
            "equity": 1000.0,
            "margin": 0.0,
            "free_margin": 1000.0,
            "profit": 0.0,
            "leverage": 100,
            "trade_mode": 0,
            "snapshot_time": None,
            "broker": "MT5",
        }

    def ensure_symbol(self, symbol):
        return SimpleNamespace(visible=True, trade_mode=1)

    def get_symbol_constraints(self, symbol):
        return {"volume_min": 0.01, "volume_step": 0.01, "point": 0.1, "stops_level_points": 0}


def test_preflight_reports_ready(monkeypatch):
    import services.execution_preflight_service as module

    fake_mt5 = SimpleNamespace(
        ACCOUNT_TRADE_MODE_DEMO=0,
        SYMBOL_TRADE_MODE_DISABLED=0,
        terminal_info=lambda: SimpleNamespace(
            connected=True,
            trade_allowed=True,
            tradeapi_disabled=False,
        ),
    )
    monkeypatch.setattr(module, "mt5", fake_mt5)

    service = ExecutionPreflightService(FakeProvider(), FakeRepository())
    result = service.run(["Boom 100 Index"])

    assert result["ready"] is True
    assert result["failed"] == []
    assert any(item["name"] == "SYMBOL:Boom 100 Index" for item in result["checks"])


def test_preflight_accepts_dict_symbol_info(monkeypatch):
    import services.execution_preflight_service as module

    fake_mt5 = SimpleNamespace(
        ACCOUNT_TRADE_MODE_DEMO=0,
        SYMBOL_TRADE_MODE_DISABLED=0,
        terminal_info=lambda: SimpleNamespace(
            connected=True,
            trade_allowed=True,
            tradeapi_disabled=False,
        ),
    )
    monkeypatch.setattr(module, "mt5", fake_mt5)

    class DictProvider(FakeProvider):
        def ensure_symbol(self, symbol):
            return {
                "symbol": symbol,
                "visible": True,
                "trade_mode": 1,
                "volume_min": 0.1,
                "volume_step": 0.01,
                "point": 0.001,
            }

    result = ExecutionPreflightService(
        DictProvider(),
        FakeRepository(),
    ).run(["Boom 100 Index"])

    assert result["ready"] is True
    symbol_check = next(
        item
        for item in result["checks"]
        if item["name"] == "SYMBOL:Boom 100 Index"
    )
    assert symbol_check["details"]["trade_mode"] == 1
