from unittest.mock import Mock, patch
from types import SimpleNamespace
from datetime import datetime, timezone
import pytest

from brokers.mt5_trade_executor import MT5TradeExecutor
from brokers.mt5_execution import MT5ExecutionProvider
from strategy.execution.trade_executor import TradeExecutionRequest, EXECUTION_STATUS_FILLED


def test_execute_trade_prioritizes_deal_ticket_resolution():
    """Verifica que execute_trade use position_ticket_from_deal prioritariamente."""
    mock_provider = Mock()
    mock_provider.assert_demo_account = Mock()
    mock_provider.place_market_order = Mock(return_value={
        "order_ticket": 1001,
        "deal_ticket": 5001,
        "entry_price": 100.0,
        "filled_volume": 0.5,
    })
    mock_provider.position_ticket_from_deal = Mock(return_value=9001)
    mock_provider.find_position_ticket = Mock(return_value=8888)  # No debería llamarse

    executor = MT5TradeExecutor(
        execution_provider=mock_provider,
        magic=26082403,
        deviation=10,
    )

    request = TradeExecutionRequest(
        symbol="Volatility 100 Index",
        timeframe="M15",
        direction="SELL",
        entry_time=datetime.now(timezone.utc),
        entry_price=100.0,
        stop_loss=110.0,
        take_profit=90.0,
        volume=0.5,
        metadata={"execution_key": "DEMO:Vol100:SELL:RUNNER", "trade_leg": "RUNNER"},
    )

    result = executor.execute_trade(request)

    assert result.status == EXECUTION_STATUS_FILLED
    assert result.position_ticket == "9001"
    mock_provider.position_ticket_from_deal.assert_called_once_with(5001)
    mock_provider.find_position_ticket.assert_not_called()


def test_execute_trade_falls_back_to_find_position_ticket_when_deal_returns_none():
    """Verifica que execute_trade recurra a find_position_ticket si position_ticket_from_deal retorna None."""
    mock_provider = Mock()
    mock_provider.assert_demo_account = Mock()
    mock_provider.place_market_order = Mock(return_value={
        "order_ticket": 1002,
        "deal_ticket": 5002,
        "entry_price": 100.0,
        "filled_volume": 0.5,
    })
    mock_provider.position_ticket_from_deal = Mock(return_value=None)
    mock_provider.find_position_ticket = Mock(return_value=9002)

    executor = MT5TradeExecutor(
        execution_provider=mock_provider,
        magic=26082403,
        deviation=10,
    )

    request = TradeExecutionRequest(
        symbol="Volatility 100 Index",
        timeframe="M15",
        direction="SELL",
        entry_time=datetime.now(timezone.utc),
        entry_price=100.0,
        stop_loss=110.0,
        take_profit=90.0,
        volume=0.5,
        metadata={"execution_key": "DEMO:Vol100:SELL:TP1", "trade_leg": "TP1"},
    )

    result = executor.execute_trade(request)

    assert result.status == EXECUTION_STATUS_FILLED
    assert result.position_ticket == "9002"
    mock_provider.position_ticket_from_deal.assert_called_once_with(5002)
    mock_provider.find_position_ticket.assert_called_once()


def test_find_position_ticket_distinguishes_tp1_and_runner_comments():
    """Verifica que find_position_ticket distinga correctamente entre TP1 y RUNNER aunque compartan magic y segundo."""
    provider = MT5ExecutionProvider.__new__(MT5ExecutionProvider)
    provider._ensure = Mock()

    # Simular dos posiciones abiertas en el mismo segundo con el mismo magic pero distintos comentarios
    pos_tp1 = SimpleNamespace(
        ticket=11111,
        magic=26082403,
        comment="DEMO:Vol100:SELL:TP1",
        time=1763782298,
        time_msc=1763782298100,
    )
    pos_runner = SimpleNamespace(
        ticket=22222,
        magic=26082403,
        comment="DEMO:Vol100:SELL:RUNNER",
        time=1763782298,
        time_msc=1763782298900,
    )

    with patch("brokers.mt5_execution.mt5") as mock_mt5:
        # positions_get devuelve ambas posiciones (TP1 primero)
        mock_mt5.positions_get.return_value = [pos_tp1, pos_runner]

        # Al buscar RUNNER, debe devolver el ticket de pos_runner (22222), NO el de pos_tp1
        ticket_runner = provider.find_position_ticket(
            symbol="Volatility 100 Index",
            magic=26082403,
            comment="DEMO:Vol100:SELL:RUNNER",
        )
        assert ticket_runner == 22222

        # Al buscar TP1, debe devolver el ticket de pos_tp1 (11111)
        ticket_tp1 = provider.find_position_ticket(
            symbol="Volatility 100 Index",
            magic=26082403,
            comment="DEMO:Vol100:SELL:TP1",
        )
        assert ticket_tp1 == 11111


def test_find_position_ticket_leg_suffix_partial_match():
    """Verifica que el filtrado por sufijo (:RUNNER vs :TP1) resuelva el ticket aun con truncamiento de comentario."""
    provider = MT5ExecutionProvider.__new__(MT5ExecutionProvider)
    provider._ensure = Mock()

    pos_tp1 = SimpleNamespace(
        ticket=33333,
        magic=26082403,
        comment="truncated_base_prefix:TP1",
        time=1763782298,
        time_msc=1763782298000,
    )
    pos_runner = SimpleNamespace(
        ticket=44444,
        magic=26082403,
        comment="truncated_base_prefix:RUNNER",
        time=1763782298,
        time_msc=1763782298800,
    )

    with patch("brokers.mt5_execution.mt5") as mock_mt5:
        mock_mt5.positions_get.return_value = [pos_tp1, pos_runner]

        ticket = provider.find_position_ticket(
            symbol="Volatility 5 Index",
            magic=26082403,
            comment="full_original_long_key:RUNNER",
        )
        assert ticket == 44444


def test_find_position_ticket_disambiguates_by_time_msc_and_ticket():
    """Verifica que cuando los comentarios son ambiguos, se use time_msc y ticket numérico más reciente."""
    provider = MT5ExecutionProvider.__new__(MT5ExecutionProvider)
    provider._ensure = Mock()

    older_pos = SimpleNamespace(
        ticket=55555,
        magic=26082403,
        comment="generic_comment",
        time=1763782298,
        time_msc=1763782298100,
    )
    newer_pos = SimpleNamespace(
        ticket=66666,
        magic=26082403,
        comment="generic_comment",
        time=1763782298,
        time_msc=1763782298950,
    )

    with patch("brokers.mt5_execution.mt5") as mock_mt5:
        # Aunque older_pos venga primero en la lista
        mock_mt5.positions_get.return_value = [older_pos, newer_pos]

        ticket = provider.find_position_ticket(
            symbol="Volatility 75 Index",
            magic=26082403,
            comment="generic_comment",
        )
        assert ticket == 66666


def test_position_ticket_from_deal_direct_and_range_fallback():
    """Verifica que position_ticket_from_deal funcione directo y con fallback a rango de fechas."""
    provider = MT5ExecutionProvider.__new__(MT5ExecutionProvider)
    provider._ensure = Mock()

    deal_obj = SimpleNamespace(ticket=77777, position_id=88888)

    with patch("brokers.mt5_execution.mt5") as mock_mt5:
        # Caso 1: Directo por ticket
        mock_mt5.history_deals_get.return_value = [deal_obj]
        res1 = provider.position_ticket_from_deal(77777)
        assert res1 == 88888

        # Caso 2: Directo devuelve vacío, pero fallback por rango temporal encuentra el deal
        def fake_history(*args, **kwargs):
            if "ticket" in kwargs:
                return []
            return [deal_obj]

        mock_mt5.history_deals_get.side_effect = fake_history
        res2 = provider.position_ticket_from_deal(77777)
        assert res2 == 88888
