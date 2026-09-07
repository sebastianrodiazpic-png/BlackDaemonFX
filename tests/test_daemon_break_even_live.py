from types import SimpleNamespace

from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine


class Repo:
    def __init__(self):
        self.trade = {
            "id": 1,
            "broker_position_ticket": "123",
            "instrument": "TEST",
            "direction": "BUY",
            "stop_loss": 90.0,
            "take_profit": 120.0,
            "details": {
                "metadata": {
                    "initial_stop_loss": 90.0,
                    "break_even_activated": False,
                }
            },
        }
        self.updates = []

    def open_trades(self, source=None):
        return [self.trade]

    def update_trade(self, trade_id, data):
        self.updates.append((trade_id, data))
        self.trade.update({k: v for k, v in data.items() if k != "details"})
        if "details" in data:
            self.trade["details"] = data["details"]


class Provider:
    connector = SimpleNamespace()


class BrokerExecutor:
    def __init__(self):
        self.sl = 90.0
        self.confirm_changes = True

    def get_symbol_constraints(self, symbol):
        return {"point": 0.01, "digits": 2}

    def get_position(self, ticket):
        return SimpleNamespace(
            ticket=ticket,
            price_open=100.0,
            price_current=110.0,
            sl=self.sl,
            tp=120.0,
        )


class TradeExecutor:
    def __init__(self, broker):
        self.calls = []
        self.broker = broker

    def move_stop_loss(self, position_ticket, stop_loss, take_profit=None, reason=""):
        self.calls.append((position_ticket, stop_loss, take_profit, reason))
        if self.broker.confirm_changes:
            self.broker.sl = float(stop_loss)
        return {"modified": True, "retcode": 10009}


class LifecycleManager:
    def __init__(self, trade_executor):
        self.trade_executor = trade_executor


def test_daemon_moves_live_position_to_break_even_at_one_r():
    repo = Repo()
    broker = BrokerExecutor()
    trade_executor = TradeExecutor(broker)
    engine = LiveTradingEngine(
        provider=Provider(),
        repository=repo,
        config=LiveTradingConfig(
            execution_enabled=True,
            break_even_enabled=True,
            break_even_trigger_rr=1.0,
        ),
        executor=broker,
        lifecycle_manager=LifecycleManager(trade_executor),
    )

    result = engine._monitor_break_even_positions()

    assert result["activated"] == 1
    assert trade_executor.calls[0][0] == "123"
    # v105: el BE ya no solo cubre spread/offset (100.02): bloquea además una
    # fracción del riesgo inicial como ganancia real. Riesgo=10 (entry 100,
    # stop inicial 90) x break_even_profit_lock_rr_fraction=0.3 -> +3.0.
    assert trade_executor.calls[0][1] == 103.02
    assert repo.trade["stop_loss"] == 103.02
    assert repo.trade["details"]["metadata"]["break_even_activated"] is True


def test_daemon_break_even_is_idempotent_when_broker_already_at_entry():
    repo = Repo()
    repo.trade["details"]["metadata"]["break_even_activated"] = True
    broker = BrokerExecutor()
    broker.sl = 100.02
    trade_executor = TradeExecutor(broker)
    engine = LiveTradingEngine(
        provider=Provider(),
        repository=repo,
        config=LiveTradingConfig(execution_enabled=True),
        executor=broker,
        lifecycle_manager=LifecycleManager(trade_executor),
    )

    result = engine._monitor_break_even_positions()

    assert result["activated"] == 0
    assert trade_executor.calls == []


def test_daemon_does_not_persist_break_even_when_broker_does_not_confirm():
    repo = Repo()
    broker = BrokerExecutor()
    broker.confirm_changes = False
    trade_executor = TradeExecutor(broker)
    engine = LiveTradingEngine(
        provider=Provider(),
        repository=repo,
        config=LiveTradingConfig(
            execution_enabled=True,
            break_even_confirmation_retries=1,
            break_even_confirmation_delay_seconds=0.0,
        ),
        executor=broker,
        lifecycle_manager=LifecycleManager(trade_executor),
    )

    result = engine._monitor_break_even_positions()

    assert result["activated"] == 0
    assert trade_executor.calls
    assert repo.trade["details"]["metadata"]["break_even_activated"] is False
    assert result["errors"][0]["error"] == "BREAK_EVEN_NOT_CONFIRMED_BY_BROKER"

class SplitRepo(Repo):
    def __init__(self):
        super().__init__()
        self.trade["details"]["metadata"].update({
            "trade_leg": "RUNNER",
            "parent_execution_key": "TEST:SETUP:BUY",
        })
        self.tp1 = {
            "id": 2,
            "status": "CLOSED",
            "result": "WIN",
            "realized_rr": 0.98,
            "exit_price": 110.0,
        }

    def get_trade_by_execution_key(self, execution_key):
        if execution_key == "TEST:SETUP:BUY:TP1":
            return self.tp1
        return None


def test_runner_moves_to_break_even_when_tp1_closed_even_after_price_retrace():
    repo = SplitRepo()
    broker = BrokerExecutor()
    # El precio ya retrocedió por debajo de 1R (110), pero TP1 demuestra que 1R fue tocado.
    original_get_position = broker.get_position

    def retraced_position(ticket):
        position = original_get_position(ticket)
        position.price_current = 106.0
        return position

    broker.get_position = retraced_position
    trade_executor = TradeExecutor(broker)
    engine = LiveTradingEngine(
        provider=Provider(),
        repository=repo,
        config=LiveTradingConfig(
            execution_enabled=True,
            split_entries_enabled=True,
            break_even_enabled=True,
            break_even_trigger_rr=1.0,
            break_even_offset_points=2,
        ),
        executor=broker,
        lifecycle_manager=LifecycleManager(trade_executor),
    )

    result = engine._monitor_break_even_positions()

    assert result["activated"] == 1
    # v105: riesgo=10 (entry 100, stop inicial 90) x fracción 0.3 -> +3.0 de
    # ganancia real bloqueada, además del offset de 2 points (0.02).
    assert trade_executor.calls[0][1] == 103.02
    metadata = repo.trade["details"]["metadata"]
    assert metadata["break_even_activated"] is True
    assert metadata["break_even_activation_reason"] == "TP1_CLOSED_IN_PROFIT"
    assert result["updates"][0]["activation_reason"] == "TP1_CLOSED_IN_PROFIT"


def test_runner_sell_break_even_uses_two_points_in_favorable_direction():
    repo = Repo()
    repo.trade["direction"] = "SELL"
    repo.trade["stop_loss"] = 110.0
    repo.trade["details"]["metadata"]["initial_stop_loss"] = 110.0
    broker = BrokerExecutor()

    def sell_position(ticket):
        return SimpleNamespace(
            ticket=ticket,
            price_open=100.0,
            price_current=90.0,
            sl=broker.sl if broker.sl != 90.0 else 110.0,
            tp=80.0,
        )

    broker.sl = 110.0
    broker.get_position = sell_position
    trade_executor = TradeExecutor(broker)
    engine = LiveTradingEngine(
        provider=Provider(),
        repository=repo,
        config=LiveTradingConfig(
            execution_enabled=True,
            break_even_offset_points=2,
        ),
        executor=broker,
        lifecycle_manager=LifecycleManager(trade_executor),
    )

    result = engine._monitor_break_even_positions()

    assert result["activated"] == 1
    # v105: riesgo=10 (entry 100, stop inicial 110 en SELL) x fracción 0.3
    # -> -3.0 de ganancia real bloqueada, restando el offset de 2 points.
    assert trade_executor.calls[0][1] == 96.98
