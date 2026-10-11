import time
import pytest
from strategy.execution.event_dispatcher import (
    AsyncEventDispatcher,
    EventType,
    Event,
    TickEvent,
    BarClosedEvent,
    RiskAlertEvent,
)


def test_event_dispatcher_priority_ordering():
    dispatcher = AsyncEventDispatcher()
    collected = []

    dispatcher.subscribe(EventType.TICK, lambda e: collected.append("TICK"))
    dispatcher.subscribe(EventType.RISK_ALERT, lambda e: collected.append("RISK"))
    dispatcher.start()

    # Publish TICK first, RISK second
    dispatcher.publish(TickEvent("EURUSD", 1.0500, 1.0502))
    dispatcher.publish(RiskAlertEvent("EURUSD", "STOP_LOSS_HIT"))

    time.sleep(0.15)
    dispatcher.stop()

    # RISK (priority 0) must execute before TICK (priority 5)
    assert collected == ["RISK", "TICK"]


def test_event_dispatcher_stats():
    dispatcher = AsyncEventDispatcher()
    dispatcher.start()
    dispatcher.publish(TickEvent("BOOM1000", 1000.0, 1001.0))
    time.sleep(0.1)
    dispatcher.stop()

    stats = dispatcher.stats()
    assert stats["total_events_dispatched"] >= 1
    assert "avg_dispatch_latency_ms" in stats
