import os
import pytest
from strategy.execution.live_trading_engine import LiveTradingEngine, LiveTradingConfig


class MockRepo:
    def __init__(self, trades):
        self._trades = list(trades)

    def open_trades(self, source="DEMO"):
        return list(self._trades)


def test_anti_cannibalization_quotas_synthetics_and_real_markets():
    # 5 operaciones lógicas (10 físicas) en Sintéticos con riesgo activo
    synth_trades = []
    instruments = ["Step Index 200", "Crash 500 Index", "Boom 500 Index", "Jump 25 Index", "Volatility 10 Index"]
    for i, inst in enumerate(instruments):
        synth_trades.append({
            "id": 1000 + i * 2,
            "instrument": inst,
            "direction": "BUY",
            "entry_price": 100.0,
            "stop_loss": 90.0,
            "status": "OPEN",
            "trade_leg": "TP1",
        })
        synth_trades.append({
            "id": 1000 + i * 2 + 1,
            "instrument": inst,
            "direction": "BUY",
            "entry_price": 100.0,
            "stop_loss": 90.0,
            "status": "OPEN",
            "trade_leg": "RUNNER",
        })

    repo = MockRepo(synth_trades)
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(
        bot_profile="SYNTHETICS",
        source="DEMO",
        execution_enabled=True,
        max_open_positions=16,  # 8 operaciones = 16 posiciones
        max_open_positions_per_symbol=2,
        split_entries_enabled=True,
    )
    engine.repository = repo

    # 1. Un 6to sintético ("Jump 75 Index") intenta entrar:
    # Como ya hay 10 posiciones sintéticas de riesgo (tope 10), se veta para no canibalizar los slots de mercados reales
    res_synth = engine._position_limit_result("Jump 75 Index", "key_synth_6")
    assert res_synth is not None
    assert res_synth["action"] == "MAX_SYNTHETIC_QUOTA_REACHED"

    # 2. Sin embargo, un mercado real ("Wall Street 30" o "XAUUSD") TIENE SLOTS RESERVADOS y puede entrar!
    res_real = engine._position_limit_result("Wall Street 30", "key_real_1")
    assert res_real is None, "Mercados Reales deben poder entrar aprovechando su cuota garantizada"
