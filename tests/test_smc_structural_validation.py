import pandas as pd
import pytest
from strategy.smc.structural_validation import get_h1_structural_range, validate_m15_ob_structure
from strategy.smc.fair_value_gap import detect_fvg_confirmation
from strategy.smc.confirmation_engine import evaluate_m5_confirmation, M5ConfirmationConfig
from strategy.smc.m15_setup import build_m15_setups
from strategy.execution.trade_pipeline import PipelineConfig


def test_h1_waits_for_all_right_candles_and_rejects_flat_range():
    d = pd.DataFrame({'high': [10.,11,15,11,10,11,12,11,10],
                      'low': [8.,8,9,8,4,8,9,8,8]})
    assert get_h1_structural_range(d.iloc[:6], 2) is None
    result = get_h1_structural_range(d.iloc[:7], 2)
    assert result['high'] == 15 and result['low'] == 4
    assert result['equilibrium'] == 9.5
    assert get_h1_structural_range(pd.DataFrame({'high':[10.]*15,'low':[8.]*15})) is None


@pytest.mark.parametrize('sell', [False, True])
def test_m15_requires_close_not_wick_and_preconfirmed_pivot(sell):
    from test_m15_responsibilities import candles
    d = candles()
    if sell:
        old=d.copy()
        for a,b in [('open','open'),('close','close'),('high','low'),('low','high')]:
            d[a]=200-old[b]
    direction = 'short' if sell else 'long'
    assert validate_m15_ob_structure(d,21,direction)['has_structure_break']
    d.loc[22,'close']=98 if sell else 102
    d.loc[23,'close']=98 if sell else 102
    assert not validate_m15_ob_structure(d,21,direction)['has_structure_break']
    d.loc[10,'high' if not sell else 'low']=101 if not sell else 99
    assert not validate_m15_ob_structure(d,21,direction)['has_structure_break']


def test_m15_rejects_displacement_without_pivot():
    from test_m15_responsibilities import candles
    d=candles(); d.loc[10,'high']=101
    setups,audit=build_m15_setups(d,PipelineConfig(m15_flexible_structure=False))
    assert setups.empty
    assert any('M15_OB_STRUCTURE_BREAK_REQUIRED' in row['reasons'] for row in audit)


@pytest.mark.parametrize('sell', [False, True])
def test_fvg_cannot_use_future_or_unrelated_choch(sell):
    d=pd.DataFrame({'high':[10.,13,15], 'low':[8.,9,12]})
    if sell:
        d=pd.DataFrame({'high':30-d.low,'low':30-d.high})
    direction='short' if sell else 'long'
    assert not detect_fvg_confirmation(d,direction,1,choch_indices=[1])['fvg_confirmed']
    assert detect_fvg_confirmation(d,direction,2,choch_indices=[1])['fvg_confirmed']
    assert not detect_fvg_confirmation(d,direction,2,choch_indices=[0])['fvg_confirmed']


def test_adaptive_score_cannot_replace_choch_fvg():
    from test_confirmation_engine import _data, _setup
    d=_data(); d['choch_bullish']=False; d.loc[3,'choch_bullish']=True
    result=evaluate_m5_confirmation(data=d,setup=_setup(d),retest_index=2,
        confirmation_index=3,direction='long',config=M5ConfirmationConfig(
        require_choch_fvg=True,minimum_viable_trade_score=0,minimum_confirmation_ratio=0))
    assert not result['confirmation_valid']
    assert 'M5_CHOCH_FVG_REQUIRED' in result['critical_confirmation_failures']
