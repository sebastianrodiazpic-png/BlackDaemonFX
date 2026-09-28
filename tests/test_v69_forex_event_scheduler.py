from types import SimpleNamespace
from pathlib import Path
import pandas as pd

import app.main as main
from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine


def test_forex_split_profiles_are_four_unique_workers():
    assert main.FOREX_SPLIT_PROFILES == ("FOREX_1","FOREX_2","FOREX_3","FOREX_4")
    magics=[]
    modes=[]
    for idx,profile in enumerate(main.FOREX_SPLIT_PROFILES):
        spec=main.BOT_PROFILES[profile]
        assert spec["categories"] == ["forex"]
        assert spec["shard_index"] == idx
        assert spec["shard_count"] == 4
        magics.append(spec["magic"])
        modes.append(spec["mode"])
    assert len(set(magics)) == 4
    assert len(set(modes)) == 4


def test_stable_symbol_shards_are_disjoint_and_complete():
    symbols=["EURUSD","GBPUSD","USDJPY","AUDUSD","NZDUSD","USDCAD","USDCHF","EURJPY","GBPJPY"]
    shards=[main._stable_symbol_shard(symbols,i,4) for i in range(4)]
    flat=[s for group in shards for s in group]
    assert sorted(flat)==sorted(symbols)
    assert sum(len(set(group)) for group in shards)==len(symbols)
    for i in range(4):
        for j in range(i+1,4):
            assert set(shards[i]).isdisjoint(shards[j])


class CandleProvider:
    def __init__(self):
        self.ts="2026-09-01T10:00:00Z"
    def get_candles(self, symbol, timeframe, count=3):
        return pd.DataFrame([
            {"time":"2026-09-01T09:55:00Z","open":1,"high":2,"low":.5,"close":1.1},
            {"time":self.ts,"open":1.1,"high":2,"low":.5,"close":1.2},
            {"time":"2026-09-01T10:05:00Z","open":1.2,"high":2,"low":.5,"close":1.3},
        ])


def _event_engine():
    e=object.__new__(LiveTradingEngine)
    e.config=LiveTradingConfig(
        bot_profile="FOREX_1",
        forex_event_scheduler_enabled=True,
        forex_event_timeframe="M5",
    )
    # Isolate candle scheduling from the real wall-clock trading session.
    e._analysis_session_status=lambda: {"state":"ACTIVE", "active":True, "next_activation":None}
    e._available_market_symbols=lambda symbols: (symbols, [])
    e.provider=CandleProvider()
    e._forex_last_closed_bar={}
    return e


def test_forex_event_scheduler_only_releases_new_closed_m5():
    e=_event_engine()
    symbols=["EURUSD","GBPUSD"]
    assert e._forex_due_symbols(symbols)==symbols
    e._commit_forex_processed_symbols([
        {"symbol":"EURUSD","action":"WAITING_M5_CONFIRMATION"},
        {"symbol":"GBPUSD","action":"NO_M15_SETUP"},
    ])
    assert e._forex_due_symbols(symbols)==[]
    e.provider.ts="2026-09-01T10:05:00Z"
    assert e._forex_due_symbols(symbols)==symbols


def test_forex_scheduler_retries_same_bar_after_technical_error():
    e=_event_engine()
    assert e._forex_due_symbols(["EURUSD"])==["EURUSD"]
    e._commit_forex_processed_symbols([{"symbol":"EURUSD","action":"DATA_ERROR"}])
    assert e._forex_due_symbols(["EURUSD"])==["EURUSD"]


def test_synthetic_is_event_filtered_since_v93():
    e=_event_engine()
    e.config.bot_profile="BOOM"
    assert e._forex_due_symbols(["Boom 1000 Index"])==["Boom 1000 Index"]
    e._commit_forex_processed_symbols([
        {"symbol":"Boom 1000 Index","action":"NO_M15_SETUP"},
    ])
    assert e._forex_due_symbols(["Boom 1000 Index"])==[]


class ExposureRepo:
    def __init__(self,trades):
        self.trades=trades
    def open_trades(self,source=None):
        return self.trades


def _trade(id_,symbol,parent,risk=1.0):
    return {
        "id":id_,"instrument":symbol,"risk_percent":.5,
        "details":{"metadata":{
            "parent_execution_key":parent,
            "operation_risk_percent":risk,
        }}
    }


def test_forex_exposure_does_not_double_count_split_legs():
    e=object.__new__(LiveTradingEngine)
    e.config=LiveTradingConfig(
        bot_profile="FOREX_2",risk_percent=1.0,
        forex_max_currency_exposure_percent=2.0,
        forex_max_total_risk_percent=4.0,
    )
    e.repository=ExposureRepo([
        _trade(1,"EURUSD","A",1.0),
        _trade(2,"EURUSD","A",1.0),
    ])
    # Existing EURUSD setup = 1% logical, not 2%. A second EUR pair reaches 2%, allowed.
    assert e._forex_exposure_guard("EURJPY","B") is None


def test_forex_currency_exposure_blocks_third_percent_on_same_currency():
    e=object.__new__(LiveTradingEngine)
    e.config=LiveTradingConfig(
        bot_profile="FOREX_3",risk_percent=1.0,
        forex_max_currency_exposure_percent=2.0,
        forex_max_total_risk_percent=4.0,
    )
    e.repository=ExposureRepo([
        _trade(1,"EURUSD","A",1.0),
        _trade(2,"EURJPY","B",1.0),
    ])
    result=e._forex_exposure_guard("EURGBP","C")
    assert result["action"]=="FOREX_CURRENCY_EXPOSURE_LIMIT"
    assert result["forex_exposure"]["violations"]["EUR"]==3.0


def test_forex_total_risk_limit_is_global_across_pairs():
    e=object.__new__(LiveTradingEngine)
    e.config=LiveTradingConfig(
        bot_profile="FOREX_4",risk_percent=1.0,
        forex_max_currency_exposure_percent=10.0,
        forex_max_total_risk_percent=4.0,
    )
    e.repository=ExposureRepo([
        _trade(1,"EURUSD","A",1.0),
        _trade(2,"GBPJPY","B",1.0),
        _trade(3,"AUDCAD","C",1.0),
        _trade(4,"NZDCHF","D",1.0),
    ])
    result=e._forex_exposure_guard("USDJPY","E")
    assert result["action"]=="FOREX_TOTAL_RISK_LIMIT"


def test_forex_launcher_uses_split_scheduler():
    root=Path(__file__).resolve().parents[1]
    text=(root/"run_forex_bot.bat").read_text(encoding="utf-8")
    assert "--mode forex-split-daemon" in text
    assert "--interval 10" in text
    assert "--position-monitor-interval 2" in text


def test_forex_selection_profile_shared_by_all_shards():
    for profile in main.FOREX_SPLIT_PROFILES:
        assert main._selection_profile_for_bot(profile)=="FOREX"
