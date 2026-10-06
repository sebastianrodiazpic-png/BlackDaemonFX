import pandas as pd
import pytest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock

from strategy.gold_quarters import GoldQuarterStrategy
from strategy.execution.live_trading_engine import LiveTradingEngine, LiveTradingConfig


NOW = pd.Timestamp('2026-09-22T12:00:00Z')


class MockQuarterProvider:
    def __init__(self, buy=True):
        self.buy = buy

    def get_candles(self, symbol, tf, count):
        if tf == 'H1':
            return pd.DataFrame({
                'time': pd.date_range(end=NOW - pd.Timedelta(hours=1), periods=100, freq='h'),
                'open': 100., 'close': 100.,
                'high': 180. if self.buy else 110.,
                'low': 90. if self.buy else 20.
            })
        data = pd.DataFrame({
            'time': pd.date_range(end=NOW - pd.Timedelta(minutes=5), periods=40, freq='5min'),
            'open': 101., 'close': 101., 'high': 102., 'low': 98.
        })
        data.loc[38, ['open', 'close', 'high', 'low']] = [102, 102, 103, 99.8] if self.buy else [98, 98, 100.2, 97]
        data.loc[39, ['open', 'close', 'high', 'low']] = [102, 104, 104.5, 102] if self.buy else [98, 96, 98, 95.5]
        return data


def test_gold_quarters_targets_tp2_and_sets_tp1_milestone():
    strategy = GoldQuarterStrategy(MockQuarterProvider(buy=True))
    result = strategy.analyze_symbol('XAUUSD', NOW)
    
    assert result['valid'] is True
    sig = result['signal']
    assert sig['direction'] == 'BUY'
    # TP1 milestone is 100 + 25 = 125
    assert sig['quarter_target'] == 125.0
    # TP2 milestone is 100 + 50 = 150
    assert sig['quarter_target_2'] == 150.0
    # Executable take_profit targets TP2 (+50 pts)
    assert sig['take_profit'] == 150.0
    assert sig['risk_reward_ratio_tp2'] > sig['risk_reward_ratio_tp1']
    assert sig['risk_reward_ratio'] == sig['risk_reward_ratio_tp2']


def test_live_trading_engine_executes_tp2_with_tp1_be_milestone():
    from test_demo_daemon_integration import Provider, ExecutionRepo, Executor, FakeLifecycleManager

    executor = Executor()
    executor.normalize_market_stops = lambda sym, d, entry, sl, tp, **kwargs: {
        "valid": True, "entry_price": entry, "stop_loss": sl, "take_profit": tp
    }
    engine = LiveTradingEngine(
        provider=Provider(),
        repository=ExecutionRepo(),
        executor=executor,
        lifecycle_manager=FakeLifecycleManager(),
        config=LiveTradingConfig(
            bot_profile='GOLD',
            orb_enabled=False,
            execution_enabled=True,
            max_entry_drift_r=None,
            meta_labeling_enabled=False,
            split_entries_enabled=False,
        )
    )
    engine.multi_timeframe = SimpleNamespace(analyze_symbol=lambda s: {'valid': False, 'reason': 'NO_SMC_SETUP'})
    engine._attach_exhaustion_reversal_shadow = lambda s, a: a
    engine._gold_smc_entry_gate = lambda s: None

    # Signal targeting TP2 (150.0) with TP1 milestone at (125.0)
    engine._gold_quarters_analysis = lambda s: {
        'valid': True,
        'strategy_name': 'GOLD_QUARTERS',
        'signal': {
            'strategy_name': 'GOLD_QUARTERS',
            'direction': 'BUY',
            'entry_time': pd.Timestamp.now(tz='UTC').isoformat(),
            'entry_price': 100.,
            'stop_loss': 95.,
            'quarter_target': 125.,
            'quarter_target_2': 150.,
            'take_profit': 150.,
            'risk_reward_ratio': 10.,
            'entry_location_ranges': {'H1': {'low': 90., 'high': 180.}}
        }
    }

    engine._gold_quarters_entry_preflight = Mock(return_value={'valid': True, 'reason': 'GOLD_QUARTERS_PREFLIGHT_PASSED'})

    res = engine.process_symbol('XAUUSD')
    assert res['action'] in ('ORDER_OPENED', 'SPLIT_ORDER_OPENED'), res
    assert len(engine.repository.rows) in (1, 2)
    
    trade_row = list(engine.repository.rows.values())[-1]
    # Executable Take Profit must be TP2 (150.0)
    assert trade_row['take_profit'] == 150.0
    
    metadata = trade_row['details']['metadata']
    # TP1 milestone stored for Break-Even guard
    assert metadata['gold_tp1_target_price'] == 125.0
    assert metadata['quarter_target'] == 125.0
    assert metadata['quarter_target_2'] == 150.0
