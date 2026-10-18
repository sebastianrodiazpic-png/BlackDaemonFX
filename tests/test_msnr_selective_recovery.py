from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from strategy.malaysian_snr.config import MalaysianSNRConfig
from strategy.malaysian_snr.malaysian_snr_strategy import MalaysianSNRStrategy
from strategy.malaysian_snr.runtime_settings import msnr_default_settings, validate_msnr_patch
from strategy.malaysian_snr.runtime_engine import cycle_symbols
from strategy.malaysian_snr.universe import catalogue, resolve_symbol_settings, RECOVERY_SYMBOLS
from strategy.malaysian_snr.research_comparison import compare_samples
from test_msnr_dynamic_d1_settings import market, dashboard, api


def controls(**patch):
    return {**msnr_default_settings(), 'additional_symbols': [], **patch}


@pytest.mark.parametrize('bad', [
    {'asset_modes':{'BTCUSD':'OPERAR'}}, {'asset_modes':{'ETHUSD':'live'}},
    {'asset_modes':['BTCUSD']}, {'m5_symbol_modes':{'BTCUSD':True}},
    {'continuation_symbol_modes':{'../BTCUSD':'live'}},
    {'continuation_max_entry_distance_atr':float('nan')},
    {'qm_max_entry_distance_atr':6}, {'continuation_maximum_breakout_wick_ratio':1.1},
    {'research_min_frequency_ratio':True}, {'research_min_resolved_trades':True},
])
def test_invalid_controls_fail_atomically(dashboard,bad):
    import urllib.error
    before=api(dashboard)['settings']
    with pytest.raises(urllib.error.HTTPError): api(dashboard,{'fractal_min_body_ratio':.4,**bad})
    assert api(dashboard)['settings']==before


def test_catalogue_has_crypto_and_preserves_the_current_core(dashboard):
    state=api(dashboard)
    assert len(state['asset_catalog'])==60
    bitcoin=next(r for r in state['asset_catalog'] if r['symbol']=='BTCUSD')
    assert bitcoin['family']=='crypto' and bitcoin['base_mode']=='off'
    assert sum(r['base_mode']=='live' for r in state['asset_catalog'])==23


def test_recovery_modes_persist_without_resetting_geometry(dashboard):
    before=api(dashboard)['settings']
    saved=api(dashboard,{'asset_modes':{'BTCUSD':'shadow','Step Index':'off'},
        'm5_symbol_modes':{'BTCUSD':'live'},'continuation_symbol_modes':{'EURUSD':'off'},
        'continuation_max_entry_distance_atr':.6})['settings']
    assert saved['asset_modes']['BTCUSD']=='shadow'
    assert saved['fractal_min_body_ratio']==before['fractal_min_body_ratio']
    assert saved['qm_max_entry_distance_atr']==.5
    from database.repository import TradingRepository
    assert TradingRepository(dashboard.repository.db_path).latest_msnr_runtime_settings()==saved


def test_excluded_bitcoin_can_be_observed_without_authorizing_orders():
    provider,_,now=market()
    cfg=MalaysianSNRConfig(enable_daily_storyline_filter=False)
    settings=controls(asset_modes={'BTCUSD':'shadow'},m5_symbol_modes={'BTCUSD':'live'},
        continuation_mode='off',av_entry_mode='off',role_flip_mode='off',gap_mode='off')
    reading=MalaysianSNRStrategy(provider,cfg,lambda:settings).analyze_symbol('BTCUSD',now)
    assert reading['valid'] and reading['shadow_only'],reading
    assert reading['signal']['execution_mode']=='SHADOW'
    assert reading['runtime_controls']['m5_confirmation_mode']=='live'


def test_explicit_disabled_core_never_fetches_or_creates_candidates():
    provider=Mock()
    reading=MalaysianSNRStrategy(provider, runtime_settings_loader=lambda:controls(
        asset_modes={'Step Index':'off'})).analyze_symbol('Step Index')
    assert reading['reason']=='MSNR_SYMBOL_DISABLED'
    provider.get_candles.assert_not_called()


def test_asset_mode_has_precedence_over_legacy_additional_mode():
    provider,_,now=market()
    cfg=MalaysianSNRConfig(enable_daily_storyline_filter=False)
    settings=controls(additional_symbols=['Jump 50 Index'],additional_symbols_mode='shadow',
        asset_modes={'Jump 50 Index':'live'},m5_confirmation_mode='off',continuation_mode='off',
        av_entry_mode='off',role_flip_mode='off',gap_mode='off')
    reading=MalaysianSNRStrategy(provider,cfg,lambda:settings).analyze_symbol('Jump 50 Index',now)
    assert reading['valid'] and not reading['shadow_only'],reading


def test_symbol_modes_are_isolated_and_dont_mutate_global_modes():
    settings=controls(m5_confirmation_mode='off', m5_symbol_modes={'BTCUSD':'shadow'},
        continuation_symbol_modes={'EURUSD':'off'})
    assert resolve_symbol_settings(settings,'BTCUSDmicro')['m5_confirmation_mode']=='shadow'
    assert resolve_symbol_settings(settings,'EURUSD')['m5_confirmation_mode']=='off'
    assert resolve_symbol_settings(settings,'EURUSD')['continuation_mode']=='off'
    assert settings['continuation_mode']=='live' and settings['m5_confirmation_mode']=='off'


def test_worker_cycle_recovers_observation_symbols_and_honors_disabled_core():
    settings=controls(asset_modes={**{s:'shadow' for s in RECOVERY_SYMBOLS},'Step Index':'off'})
    engine=SimpleNamespace(malaysian_snr_strategy=SimpleNamespace(settings_snapshot=lambda:settings))
    result=cycle_symbols(engine,['Step Index','EURUSD'])
    assert 'Step Index' not in result
    assert set(result)=={'EURUSD',*RECOVERY_SYMBOLS}
    assert len(result)==len(set(result))
    assert result[0]=='EURUSD'


def test_continuation_distance_is_separate_from_fractal_and_qm():
    provider,frames,_=market()
    cfg=MalaysianSNRConfig(enable_scenario_1_continuation=True,continuation_fresh_only=False,
        continuation_max_entry_distance_atr=.7,fractal_max_entry_distance_atr=.3,max_entry_distance_atr=.4,
        minimum_body_ratio=0,continuation_min_adx=0,maximum_breakout_wick_ratio=1)
    frame=frames['H1']
    strategy=MalaysianSNRStrategy(provider,cfg)
    setups=strategy._compute_setups_at_break(frame)
    # Fractal geometry is unchanged by adjusting Continuation distance.
    fractals=[s for s in setups if s['scenario']=='ESC_3_FRACTAL']
    assert fractals and all(s['max_entry_distance_atr']==.3 for s in fractals)
    settings=strategy.settings_snapshot()
    assert settings['continuation_max_entry_distance_atr']==.7
    assert settings['qm_max_entry_distance_atr']==.4
    assert settings['continuation_maximum_breakout_wick_ratio']==1


def test_more_wins_with_excessive_frequency_loss_cannot_pass_research_check():
    settings=controls(research_min_resolved_trades=30,research_min_frequency_ratio=.8)
    result=compare_samples([{'rr':.1}]*100,[{'rr':2.}]*30,settings,same_window_and_feed=True)
    assert 'FREQUENCY_LOSS_EXCEEDS_LIMIT' in result['reasons']
    assert not result['research_checks_passed'] and not result['automatic_promotion']


def test_more_trades_with_negative_expectancy_cannot_pass_research_check():
    result=compare_samples([{'rr':-.5}]*30,[{'rr':-.1}]*90,controls(),same_window_and_feed=True)
    assert 'NON_POSITIVE_EXPECTANCY' in result['reasons']
    assert not result['research_checks_passed']


def test_incomplete_different_feed_or_small_sample_never_approves_promotion():
    result=compare_samples([{'rr':.1}]*30,[{'rr':None}]*30,controls(),same_window_and_feed=False)
    assert set(result['reasons'])>={'DIFFERENT_WINDOW_OR_FEED','INSUFFICIENT_RESOLVED_SAMPLE','INCOMPLETE_OR_AMBIGUOUS_OUTCOMES'}
    assert not result['automatic_promotion']


def test_positive_comparable_sample_still_never_automatically_promotes():
    result=compare_samples([{'rr':1.}]*30+[{'rr':-1.}]*20,
        [{'rr':1.}]*40+[{'rr':-1.}]*20,controls(),same_window_and_feed=True)
    assert result['research_checks_passed'] and not result['automatic_promotion']
