import pytest
from dashboard.msnr_action_guide import ACTION_GUIDE
from strategy.malaysian_snr.runtime_settings import msnr_default_settings, validate_msnr_patch
from strategy.malaysian_snr.research_comparison import compare_samples
from strategy.malaysian_snr.ai_policy import settings_signature
from test_msnr_dynamic_d1_settings import dashboard, api


def rows(wins,losses,reward=1.,loss=-1.):
    return [{'rr':reward}]*wins+[{'rr':loss}]*losses


def targets(**patch):
    return {**msnr_default_settings(),'research_min_frequency_ratio':1.05,
        'research_min_resolved_trades':50,'research_min_win_rate_improvement_pp':1.,**patch}


def test_action_guide_explains_every_control_exactly_once():
    keys=[row[0] for row in ACTION_GUIDE]
    assert len(keys)==len(set(keys))
    assert set(keys)==set(msnr_default_settings())
    assert all(all(isinstance(value,str) and value.strip() for value in row) for row in ACTION_GUIDE)


def test_more_entries_and_more_total_reward_cannot_mask_a_lower_win_rate():
    base=rows(60,40,.2,-.1)
    candidate=rows(50,70,2.,-.1)
    result=compare_samples(base,candidate,targets(),same_window_and_feed=True)
    assert result['candidate_total_r']>result['baseline_total_r']
    assert result['frequency_preserved']>1.05
    assert result['win_rate_improvement_pp']<0
    assert 'WIN_RATE_IMPROVEMENT_BELOW_TARGET' in result['reasons']
    assert not result['research_checks_passed']


def test_better_win_rate_cannot_mask_lower_total_reward():
    result=compare_samples(rows(60,40,3.),rows(80,40,1.),targets(),same_window_and_feed=True)
    assert result['win_rate_improvement_pp']>1
    assert 'NO_NET_REWARD_IMPROVEMENT' in result['reasons']


def test_all_three_objectives_and_sample_required_without_auto_promotion():
    result=compare_samples(rows(60,40),rows(80,40),targets(),same_window_and_feed=True)
    assert result['research_checks_passed']
    assert result['baseline_win_rate_pct']==60
    assert result['candidate_win_rate_pct']==pytest.approx(100*2/3)
    assert not result['automatic_promotion']


def test_one_percentage_point_is_not_one_percent_relative():
    result=compare_samples(rows(40,60,2.),rows(41,59,2.),targets(research_min_frequency_ratio=1.),same_window_and_feed=True)
    assert result['win_rate_improvement_pp']==pytest.approx(1.)
    assert result['research_checks_passed']


@pytest.mark.parametrize('patch',[
    {'research_min_win_rate_improvement_pp':True},
    {'research_min_win_rate_improvement_pp':float('nan')},
    {'research_min_win_rate_improvement_pp':-1},
    {'research_min_win_rate_improvement_pp':101},
    {'research_min_frequency_ratio':5.01},
    {'research_min_frequency_ratio':float('inf')},
])
def test_research_targets_reject_invalid_values(patch):
    with pytest.raises(ValueError):validate_msnr_patch(patch)


def test_growth_target_can_exceed_one_hundred_percent_and_does_not_change_ai_geometry():
    patch={'research_min_frequency_ratio':1.05,'research_min_win_rate_improvement_pp':1.,'research_min_resolved_trades':50}
    assert validate_msnr_patch(patch)==patch
    settings=msnr_default_settings()
    assert settings_signature(settings)==settings_signature({**settings,**patch})


def test_research_targets_persist_without_changing_execution_controls(dashboard):
    before=api(dashboard)['settings']
    patch={'research_min_frequency_ratio':1.05,'research_min_win_rate_improvement_pp':1.,'research_min_resolved_trades':50}
    after=api(dashboard,patch)['settings']
    assert api(dashboard)['settings']==after
    from database.repository import TradingRepository
    assert TradingRepository(dashboard.repository.db_path).latest_msnr_runtime_settings()==after
    for key,value in before.items():
        if key not in {*patch,'version','updated_at'}:assert after[key]==value
