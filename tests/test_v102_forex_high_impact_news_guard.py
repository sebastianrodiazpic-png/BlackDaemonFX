from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import json

from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine


def _calendar(path, *, country="USD", minutes_until=10):
    event_at = datetime.now(timezone.utc) + timedelta(minutes=minutes_until)
    path.write_text(json.dumps({
        "calendar_status": "ACTUALIZADA",
        "calendar_events": [{
            "title": "Nóminas no agrícolas",
            "title_original": "Non-Farm Employment Change",
            "country": country,
            "impact": "ALTO",
            "event_at": event_at.isoformat(),
        }],
    }), encoding="utf-8")


def _engine(path):
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(
        bot_profile="FOREX_1",
        forex_high_impact_news_calendar_path=str(path),
        break_even_confirmation_retries=1,
    )
    return engine


def test_high_impact_event_blocks_only_affected_forex_pair(tmp_path):
    path = tmp_path / "financial_news.json"
    _calendar(path, country="USD")
    engine = _engine(path)

    assert engine._forex_high_impact_news_entry_gate("EURUSD")["action"] == (
        "FOREX_HIGH_IMPACT_NEWS_ENTRY_BLOCKED"
    )
    assert engine._forex_high_impact_news_entry_gate("EURJPY") is None


def test_pre_news_break_even_covers_live_spread_and_extra_points(tmp_path):
    path = tmp_path / "financial_news.json"
    _calendar(path, country="USD")
    engine = _engine(path)
    position = SimpleNamespace(price_open=1.10000, sl=1.09000, tp=1.12000)

    class Provider:
        @staticmethod
        def get_current_tick(_symbol):
            return {"bid": 1.10030, "ask": 1.10050}

    class Executor:
        @staticmethod
        def get_symbol_constraints(_symbol):
            return {"point": 0.00001, "digits": 5}

        @staticmethod
        def get_position(_ticket):
            return position

    class Repository:
        updates = []

        @classmethod
        def update_trade(cls, trade_id, payload):
            cls.updates.append((trade_id, payload))

    engine.provider = Provider()
    engine.executor = Executor()
    engine.repository = Repository()
    trade = {
        "id": 1,
        "broker_position_ticket": "123",
        "instrument": "EURUSD",
        "direction": "BUY",
        "details": {"metadata": {}},
    }
    metadata = {}

    def move_stop(**kwargs):
        position.sl = kwargs["stop_loss"]
        return {"modified": True}

    result = engine._protect_forex_position_for_high_impact_news(
        trade=trade,
        metadata=metadata,
        position=position,
        entry_price=position.price_open,
        current_sl=position.sl,
        direction="BUY",
        move_stop=move_stop,
    )

    assert result["action"] == "FOREX_NEWS_BREAK_EVEN_CONFIRMED"
    assert result["break_even_price"] == 1.10022
    assert metadata["break_even_confirmed"] is True
    assert Repository.updates[0][1]["stop_loss"] == 1.10022
