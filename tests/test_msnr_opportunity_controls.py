from copy import deepcopy
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import Mock, patch
import urllib.error
import pandas as pd
import pytest

from test_msnr_dynamic_d1_settings import market, dashboard, api
from database.repository import TradingRepository
from strategy.malaysian_snr.config import MalaysianSNRConfig
from strategy.malaysian_snr.malaysian_snr_strategy import MalaysianSNRStrategy
from strategy.malaysian_snr.runtime_settings import msnr_default_settings
from strategy.malaysian_snr.runtime_engine import cycle_symbols, track_pending
from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
from strategy.execution.active_position_guard import symbol_cycle_lock


def strategy_with_preferences(tmp_path, **changes):
    repo = TradingRepository(tmp_path/'controls.sqlite3')
    if changes:
        repo.save_msnr_runtime_settings(**changes)
    provider, frames, now = market()
    strategy = MalaysianSNRStrategy(provider, MalaysianSNRConfig(), repo.latest_msnr_runtime_settings)
    return strategy, repo, frames, now


def test_defaults_and_restore_are_complete_and_persistent(dashboard):
    defaults = api(dashboard)['defaults']
    assert defaults == msnr_default_settings()
    assert defaults['additional_symbols'] == ['Jump 50 Index','Jump 100 Index']
    assert defaults['continuation_mode'] == 'live'
    changed = {**defaults, 'fractal_min_body_ratio':.45, 'additional_symbols_mode':'off',
               'continuation_min_adx':25., 'prioritize_pending_retests':False}
    api(dashboard, changed)
    restored = api(dashboard, defaults)['settings']
    assert {k:restored[k] for k in defaults} == defaults
    assert TradingRepository(dashboard.repository.db_path).latest_msnr_runtime_settings() == restored
    defaults['additional_symbols'].clear()
    assert msnr_default_settings()['additional_symbols'] == ['Jump 50 Index','Jump 100 Index']


@pytest.mark.parametrize('change', [
    {'continuation_mode':'enabled'}, {'additional_symbols_mode':True},
    {'additional_symbols':['EURUSD']}, {'additional_symbols':'Jump 50 Index'},
    {'continuation_min_body_ratio':1.01}, {'continuation_min_adx':101},
    {'continuation_min_adx':float('nan')}, {'retest_window_minutes':14},
    {'retest_window_minutes':90.5}, {'retest_window_minutes':True},
    {'continuation_fresh_only':1}, {'enable_setup_diagnostics':'true'},
    {'analysis_outside_entry_lock':None}, {'enable_structure_cache':1},
    {'prioritize_pending_retests':'false'},
])
def test_invalid_new_control_cannot_partially_save_existing_controls(dashboard, change):
    before = api(dashboard)['settings']
    with pytest.raises(urllib.error.HTTPError) as exc:
        api(dashboard, {'fractal_min_body_ratio':.40, **change})
    assert exc.value.code == 400
    assert api(dashboard)['settings'] == before


@pytest.mark.parametrize('mode,valid,shadow', [('off',False,False),('shadow',True,True),('live',True,False)])
def test_new_asset_modes_apply_dynamically_and_do_not_mutate_base_config(tmp_path, mode, valid, shadow):
    strategy, repo, _, now = strategy_with_preferences(tmp_path, additional_symbols_mode=mode)
    result = strategy.analyze_symbol('Jump 50 Index', now)
    assert result['valid'] is valid, result
    if valid:
        assert result['shadow_only'] is shadow
        assert result['signal']['execution_mode'] == ('SHADOW' if shadow else 'LIVE')
    else:
        assert result['reason'] == 'SYMBOL_NOT_IN_MSNR_ALLOWLIST'
    assert 'Jump 50 Index' not in strategy.config.allowed_symbols
    repo.save_msnr_runtime_settings(additional_symbols_mode='live')
    assert strategy.analyze_symbol('Jump 50 Index', now)['shadow_only'] is False


def test_continuation_fresh_gate_and_adx_remain_independent_from_fractal():
    _, frames, _ = market()
    h1 = frames['H1'].copy()
    h1.loc[39,['open','high','low','close']] = [101,108,101,107]
    cfg = MalaysianSNRConfig(enable_scenario_1_continuation=True)
    strategy = MalaysianSNRStrategy(None,cfg)
    level = {'type':'A_RESISTANCE','level':106.,'break_level':106.,'idx':30}
    with patch('strategy.malaysian_snr.malaysian_snr_strategy.compute_adx',return_value=pd.Series([25.])), \
         patch('strategy.malaysian_snr.malaysian_snr_strategy.av_levels',return_value=[level]):
        fresh = next(s for s in strategy._setups_at_break(h1) if s['scenario']=='ESC_1_CONTINUATION')
        assert fresh['freshness']['state']=='FRESH' and fresh['blocked_reason'] is None
        h1.loc[34,'high']=106.1
        tested = next(s for s in strategy._setups_at_break(h1) if s['scenario']=='ESC_1_CONTINUATION')
        assert tested['blocked_reason']=='CONTINUATION_REQUIRES_FRESH'
        strategy.config.continuation_fresh_only=False
        assert next(s for s in strategy._setups_at_break(h1) if s['scenario']=='ESC_1_CONTINUATION')['blocked_reason'] is None
        strategy.config.continuation_min_adx=26.
        assert all(s['scenario']!='ESC_1_CONTINUATION' for s in strategy._setups_at_break(h1))


def test_shadow_continuation_does_not_steal_a_valid_live_fractal(tmp_path):
    strategy, repo, frames, now = strategy_with_preferences(tmp_path, continuation_mode='shadow')
    setup = next(s for s in strategy._setups_at_break(frames['H1']) if s['scenario']=='ESC_3_FRACTAL')
    continuation = {**deepcopy(setup),'scenario':'ESC_1_CONTINUATION','freshness':{'state':'FRESH'}}
    with patch.object(MalaysianSNRStrategy,'_compute_setups_at_break',return_value=[continuation, setup]):
        strategy._structure_cache.clear()
        result = strategy.analyze_symbol('Step Index',now)
    assert result['valid'] and result['signal']['scenario']=='ESC_3_FRACTAL'
    assert result['shadow_only'] is False
    assert result['shadow_candidates'][0]['shadow_only'] is True


def test_cache_reuses_structure_but_revalidates_m15_and_settings(tmp_path):
    strategy, repo, frames, now = strategy_with_preferences(tmp_path, continuation_mode='off')
    with patch.object(MalaysianSNRStrategy,'_compute_setups_at_break',autospec=True,
                      side_effect=MalaysianSNRStrategy._compute_setups_at_break) as compute:
        assert strategy.analyze_symbol('Step Index',now)['valid']
        count = compute.call_count
        assert strategy.analyze_symbol('Step Index',now)['valid']
        assert compute.call_count==count
        frames['M15'].loc[60,'low']=97.
        assert not strategy.analyze_symbol('Step Index',now)['valid']
        # A rejected retest explores older anchors for the first time. The
        # original current-H1 structure must still come from its cache.
        assert all(len(call.args[1])<len(frames['H1']) for call in compute.call_args_list[count:])
        count = compute.call_count
        assert not strategy.analyze_symbol('Step Index',now)['valid']
        assert compute.call_count==count
        repo.save_msnr_runtime_settings(fractal_min_body_ratio=.55)
        strategy.analyze_symbol('Step Index',now)
        assert compute.call_count>count
        count = compute.call_count
        frames['H1'].loc[39,'high'] += .1
        strategy.analyze_symbol('Step Index',now)
        assert compute.call_count>count


def test_diagnostics_explain_no_pattern_and_can_be_disabled(tmp_path):
    strategy, repo, frames, now = strategy_with_preferences(tmp_path, continuation_mode='off')
    frames['H1'][['open','high','low','close']] = [100.,102.,98.,101.]
    result = strategy.analyze_symbol('Step Index',now)
    assert result['reason']=='NO_SETUP_CONFIRMED'
    snapshot = result['diagnostics']['h1_snapshot']
    assert snapshot['body_ratio']==.25
    assert 'FRACTAL_BODY_BELOW_MINIMUM' in snapshot['rejections']
    assert 'FRACTAL_NO_STRUCTURAL_SWEEP' in snapshot['rejections']
    assert snapshot['atr']>0
    repo.save_msnr_runtime_settings(enable_setup_diagnostics=False)
    assert strategy.analyze_symbol('Step Index',now)['diagnostics']['h1_snapshot']=={}


def test_new_assets_and_pending_retests_are_scheduled_dynamically(tmp_path):
    strategy, repo, _, _ = strategy_with_preferences(tmp_path)
    engine = SimpleNamespace(malaysian_snr_strategy=strategy)
    expiry = (datetime.now(timezone.utc)+timedelta(minutes=10)).isoformat()
    track_pending(engine,'Step Index',{'reason':'WAITING_FIRST_RETEST','diagnostics':{'expires_at':expiry}})
    assert cycle_symbols(engine,['EURUSD','Step Index']) == ['Step Index','EURUSD','Jump 50 Index','Jump 100 Index']
    repo.save_msnr_runtime_settings(prioritize_pending_retests=False,additional_symbols_mode='off')
    assert cycle_symbols(engine,['EURUSD','Step Index'])==['EURUSD','Step Index']
    track_pending(engine,'Step Index',{'reason':'SETUP_EXPIRED'})
    assert not engine._msnr_pending_retests


def manual_engine(strategy, now, symbol):
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(bot_profile='MALAYSIAN_SNR',malaysian_snr_enabled=True,execution_enabled=True,orb_enabled=False)
    engine.provider = SimpleNamespace(resolve_symbol=lambda s:s,ensure_symbol=Mock())
    engine.malaysian_snr_strategy = SimpleNamespace(settings_snapshot=strategy.settings_snapshot,
        analyze_symbol=lambda s:strategy.analyze_symbol(s,now))
    engine._persist_audit_event=Mock()
    engine._process_symbol_guarded=Mock(side_effect=AssertionError('An observation must never reach order processing'))
    return engine


def test_shadow_asset_does_not_enter_order_processing_even_with_execution_enabled(tmp_path):
    strategy, _, _, now = strategy_with_preferences(tmp_path)
    engine = manual_engine(strategy,now,'Jump 50 Index')
    result = engine.process_symbol('Jump 50 Index')
    assert result['action']=='MSNR_SHADOW_SIGNAL'
    assert result['valid'] is False
    assert result['analysis']['signal']['execution_mode']=='SHADOW'
    engine._process_symbol_guarded.assert_not_called()


def test_preanalysis_can_run_with_competing_lock_but_live_entry_cannot(tmp_path, monkeypatch):
    import strategy.execution.active_position_guard as module
    strategy, _, _, now = strategy_with_preferences(tmp_path)
    engine = manual_engine(strategy,now,'Step Index')
    original = module.symbol_cycle_lock
    monkeypatch.setattr(module,'symbol_cycle_lock',lambda s:original(s,tmp_path/'locks'))
    with original('Step Index',tmp_path/'locks'):
        result = engine.process_symbol('Step Index')
    assert result['action']=='BLOCKED_SYMBOL_CYCLE'
    engine._process_symbol_guarded.assert_not_called()


def test_h1_diagnostics_audit_once_per_closed_bar_and_preference_version():
    engine = object.__new__(LiveTradingEngine)
    engine.config=LiveTradingConfig(bot_profile='MALAYSIAN_SNR')
    engine.repository=SimpleNamespace(save_audit_event=Mock(return_value=1))
    result={'action':'WAITING_MALAYSIAN_SNR','reason':'NO_SETUP_CONFIRMED','runtime_settings_version':1,
            'diagnostics':{'h1_snapshot':{'closed_at':'2026-10-11T22:00:00+00:00'}}}
    def emit():
        engine._persist_audit_event('SYMBOL_PROCESS_RESULT',instrument='Step Index',payload={'result':result})
    emit();emit()
    assert engine.repository.save_audit_event.call_count==1
    result['runtime_settings_version']=2
    emit()
    assert engine.repository.save_audit_event.call_count==2
    result['diagnostics']['h1_snapshot']['closed_at']='2026-10-11T23:00:00+00:00'
    emit()
    assert engine.repository.save_audit_event.call_count==3


def guarded_manual_engine(strategy, now):
    engine = manual_engine(strategy,now,'Jump 50 Index')
    engine._process_symbol_guarded=LiveTradingEngine._process_symbol_guarded.__get__(engine)
    for name in ('_active_position_gate','_gold_smc_entry_gate','_forex_killzone_entry_gate',
                 '_forex_rollover_entry_gate','_crypto_rollover_entry_gate','_forex_high_impact_news_entry_gate','_quarantine_result'):
        setattr(engine,name,Mock(return_value=None))
    engine._sync_open_trades_before_execution=Mock(return_value={'synced':0})
    return engine


def test_shadow_is_safe_also_when_analysis_outside_lock_is_disabled(tmp_path,monkeypatch):
    import strategy.execution.active_position_guard as module
    original = module.symbol_cycle_lock
    monkeypatch.setattr(module,'symbol_cycle_lock',lambda s:original(s,tmp_path/'locks'))
    strategy, _, _, now = strategy_with_preferences(tmp_path,analysis_outside_entry_lock=False)
    engine = guarded_manual_engine(strategy,now)
    result = engine.process_symbol('Jump 50 Index')
    assert result['action']=='MSNR_SHADOW_SIGNAL'
    assert result['valid'] is False


def test_parameter_change_invalidates_preanalysis_before_order_processing(tmp_path,monkeypatch):
    import strategy.execution.active_position_guard as module
    original = module.symbol_cycle_lock
    monkeypatch.setattr(module,'symbol_cycle_lock',lambda s:original(s,tmp_path/'locks'))
    strategy, _, _, now = strategy_with_preferences(tmp_path)
    engine = guarded_manual_engine(strategy,now)
    snapshots = [dict(analysis_outside_entry_lock=True,version=1), dict(version=2)]
    analyzer = Mock(side_effect=[
        {'valid':True,'signal':{'evaluated_at':datetime.now(timezone.utc).isoformat(),'runtime_settings_version':1}},
        {'valid':False,'action':'WAITING_MALAYSIAN_SNR','reason':'NO_SETUP_CONFIRMED','strategy_name':'MALAYSIAN_SNR'}])
    engine.malaysian_snr_strategy=SimpleNamespace(settings_snapshot=Mock(side_effect=snapshots),analyze_symbol=analyzer)
    result = engine.process_symbol('Step Index')
    assert analyzer.call_count==2, result
    assert result['action']=='WAITING_MALAYSIAN_SNR'


def test_structure_cache_can_be_disabled_dynamically(tmp_path):
    strategy, _, _, now = strategy_with_preferences(tmp_path,enable_structure_cache=False,continuation_mode='off')
    with patch.object(MalaysianSNRStrategy,'_compute_setups_at_break',autospec=True,
                      side_effect=MalaysianSNRStrategy._compute_setups_at_break) as compute:
        strategy.analyze_symbol('Step Index',now)
        count=compute.call_count
        strategy.analyze_symbol('Step Index',now)
        assert compute.call_count>count


def test_dashboard_distinguishes_shadow_signal_from_live_entry():
    from dashboard.realtime_dashboard import _build_confluence_matrix
    matrix = _build_confluence_matrix({'recent':[{
        'symbol':'Jump 50 Index','strategy_name':'MALAYSIAN_SNR',
        'bot_profile':'MALAYSIAN_SNR',
        'action':'MSNR_SHADOW_SIGNAL','reason':'MSNR_OBSERVATION_ONLY','scenario':'ESC_3_FRACTAL'}]})
    row = next(item for item in matrix if item['symbol']=='Jump 50 Index')
    assert row['final_state']=='🔵 OBSERVACIÓN · SIN ÓRDENES'
