from types import SimpleNamespace

from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine


def _engine_with_open_trade(trade):
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(source="DEMO", bot_profile="ORB")
    engine.repository = SimpleNamespace(open_trades=lambda source: [trade])
    engine.executor = SimpleNamespace(get_position=lambda _: SimpleNamespace(sl=trade["stop_loss"]))
    return engine


def _orb_trade(
    symbol,
    *,
    stop_loss=19900.0,
    break_even_confirmed=False,
    break_even_offset_points=None,
):
    return {
        "id": 7,
        "instrument": symbol,
        "direction": "BUY",
        "entry_price": 20000.0,
        "stop_loss": stop_loss,
        "broker_position_ticket": "700",
        "execution_key": "ORB-NAS:RUNNER",
        "details": {"metadata": {
            "strategy_name": "ORB_NEW_YORK",
            "parent_execution_key": "ORB-NAS",
            "trade_leg": "RUNNER",
            "break_even_confirmed": break_even_confirmed,
            "break_even_price": stop_loss if break_even_confirmed else None,
            **(
                {"break_even_offset_points": break_even_offset_points}
                if break_even_offset_points is not None else {}
            ),
        }},
    }


def test_sp500_is_blocked_while_nasdaq_risk_is_not_protected():
    engine = _engine_with_open_trade(_orb_trade("US Tech 100"))
    result = engine._orb_exposure_guard("US500", "ORB-SP", "ORB_NEW_YORK")
    assert result["action"] == "ORB_CORRELATED_MARKET_BLOCKED"
    assert result["reason"] == "ORB_SP500_NASDAQ_REQUIRES_CONFIRMED_BREAK_EVEN"


def test_sp500_is_allowed_after_nasdaq_break_even_is_confirmed():
    engine = _engine_with_open_trade(
        _orb_trade(
            "NASDAQ 100",
            stop_loss=20000.2,
            break_even_confirmed=True,
            break_even_offset_points=2,
        )
    )
    assert engine._orb_exposure_guard("SP500", "ORB-SP", "ORB_NEW_YORK") is None


def test_persisted_protective_stop_also_proves_break_even():
    engine = _engine_with_open_trade(
        _orb_trade("NAS100", stop_loss=20000.0, break_even_offset_points=2)
    )
    assert engine._orb_exposure_guard("US500", "ORB-SP", "ORB_NEW_YORK")["action"] == "ORB_CORRELATED_MARKET_BLOCKED"


def test_sp500_remains_blocked_until_break_even_has_two_points():
    for offset in (0, 1):
        engine = _engine_with_open_trade(
            _orb_trade(
                "US Tech 100",
                stop_loss=20000.2,
                break_even_confirmed=True,
                break_even_offset_points=offset,
            )
        )
        assert engine._orb_exposure_guard("US500", "ORB-SP", "ORB_NEW_YORK")["action"] == "ORB_CORRELATED_MARKET_BLOCKED"


def test_gold_and_wall_street_are_not_part_of_sp500_nasdaq_guard():
    engine = _engine_with_open_trade(_orb_trade("US Tech 100"))
    assert engine._orb_exposure_guard("XAUUSDmicro", "ORB-GOLD", "ORB_NEW_YORK") is None
    assert engine._orb_exposure_guard("Wall Street 30", "ORB-DOW", "ORB_NEW_YORK") is None


def test_synthetics_share_forex_progressive_smc_management():
    for profile in ("SYNTHETICS", "BOOM", "CRASH", "VOLATILITY", "STEP", "JUMP", "FLIP"):
        assert LiveTradingEngine._uses_forex_style_smc_management(profile) is True
    assert LiveTradingEngine._uses_forex_style_smc_management("FOREX_3") is True
    assert LiveTradingEngine._uses_forex_style_smc_management("ORB") is False


def test_synthetics_inherit_m5_event_scheduler_without_forex_hours():
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(bot_profile="BOOM", forex_event_scheduler_enabled=True)
    assert engine.config.smc_event_scheduler_enabled is True


def test_correlation_rechecks_broker_stop_after_restart():
    engine = _engine_with_open_trade(_orb_trade('NAS100', stop_loss=20000.2,
        break_even_confirmed=True, break_even_offset_points=2))
    engine.executor.get_position = lambda _: SimpleNamespace(sl=19900)
    assert engine._orb_exposure_guard('US500', 'new', 'ORB_NEW_YORK') is not None
