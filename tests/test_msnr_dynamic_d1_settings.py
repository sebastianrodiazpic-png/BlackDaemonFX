"""Behavioral coverage for synthetic-only D1 veto and persistent live controls."""
import json
import urllib.error
import urllib.request
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import patch

import pandas as pd
import pytest

from database.repository import TradingRepository
from dashboard.realtime_dashboard import RealtimeDashboardService
from dashboard.strategy_settings_api import PATH, SETTING, BODY_SETTING, DISTANCE_SETTING, install_strategy_settings_routes
from strategy.malaysian_snr.config import MalaysianSNRConfig
from strategy.malaysian_snr.malaysian_snr_strategy import MalaysianSNRStrategy
from strategy.execution.live_trading_engine import LiveTradingEngine


def market(direction='BUY', daily='SELL'):
    h1 = pd.DataFrame({'time': pd.date_range('2026-10-08', periods=40, freq='h', tz='UTC'),
                       'open':100., 'high':102., 'low':98., 'close':101.})
    h1.loc[37, ['open','high','low','close']] = [100,103,99,101]
    h1.loc[38, ['open','high','low','close']] = [100,102,97,100.5]
    h1.loc[39, ['open','high','low','close']] = [99,105,98,104]
    break_close = h1.time.iloc[-1] + pd.Timedelta(hours=1)
    m15 = pd.DataFrame({'time': pd.date_range(break_close-pd.Timedelta(hours=15), periods=61, freq='15min'),
                        'open':100., 'high':102., 'low':98., 'close':101.})
    m15.loc[60, ['open','high','low','close']] = [102.9,103.8,102.8,103.3]
    if direction == 'SELL':
        for frame in (h1, m15):
            old = frame[['open','high','low','close']].copy()
            frame['open'], frame['close'] = 200-old.open, 200-old.close
            frame['high'], frame['low'] = 200-old.low, 200-old.high
    d1 = pd.DataFrame({'time':[pd.Timestamp('2026-10-08', tz='UTC')],
                       'open':[100.], 'high':[120.], 'low':[80.],
                       'close':[101. if daily == 'BUY' else 99. if daily == 'SELL' else 100.]})
    frames = {'H1':h1, 'M15':m15, 'D1':d1}
    class Provider:
        def get_candles(self, symbol, timeframe, count=100):
            return frames[timeframe].tail(count)
    return Provider(), frames, break_close+pd.Timedelta(minutes=15)


@pytest.mark.parametrize('symbol,direction,daily', [
    ('Step Index','BUY','SELL'), ('Jump 25 Index','SELL','BUY'),
    ('Volatility 50 (1s) Index','BUY','SELL'),
    ('Boom 300 Index','BUY','SELL'), ('Crash 600 Index','SELL','BUY'),
])
def test_synthetic_opposing_daily_bias_allowed_by_default_but_toggle_restores_veto(symbol, direction, daily):
    provider, _, now = market(direction, daily)
    cfg = MalaysianSNRConfig(allowed_symbols=())
    result = MalaysianSNRStrategy(provider, cfg).analyze_symbol(symbol, now)
    assert result['valid'], result
    assert result['signal']['direction'] == direction
    assert result['signal']['macro_bias'] == daily
    assert result['signal']['macro_bias_enforced'] is False
    enforced = MalaysianSNRStrategy(provider, replace(cfg, enable_synthetic_daily_storyline_filter=True))
    assert enforced.analyze_symbol(symbol, now)['reason'] == 'D1_BIAS_CONFLICT'


@pytest.mark.parametrize('symbol', ['EURUSD','XAUUSD','XAGUSD','Wall Street 30'])
def test_non_synthetic_daily_veto_remains_active(symbol):
    provider, _, now = market()
    result = MalaysianSNRStrategy(provider, MalaysianSNRConfig(allowed_symbols=())).analyze_symbol(symbol, now)
    assert result['reason'] == 'D1_BIAS_CONFLICT'
    assert result['macro_bias_enforced'] is True


def test_neutral_daily_candle_is_context_only_when_synthetic_veto_is_off():
    provider, _, now = market(daily='NEUTRAL')
    strategy = MalaysianSNRStrategy(provider, MalaysianSNRConfig(allowed_symbols=()))
    assert strategy.analyze_symbol('Step Index', now)['valid']
    strategy.config.enable_synthetic_daily_storyline_filter = True
    assert strategy.analyze_symbol('Step Index', now)['reason'] == 'NEUTRAL_D1_BIAS'


def test_daily_obstacle_still_blocks_opposing_synthetic_entry():
    provider, frames, now = market()
    frames['D1'] = pd.DataFrame({
        'time':pd.date_range('2026-10-06', periods=3, freq='D', tz='UTC'),
        'open':[102.,104.,100.], 'high':[106.,106.,101.],
        'low':[101.,99.,97.], 'close':[104.,100.,99.],
    })
    result = MalaysianSNRStrategy(provider, MalaysianSNRConfig(allowed_symbols=())).analyze_symbol('Step Index', now)
    assert result['reason'] == 'OBSTACLE_D1_BEFORE_2R', result


@pytest.mark.parametrize('issue', ['missing','stale'])
def test_daily_data_still_required_with_veto_off(issue):
    provider, frames, now = market()
    if issue == 'missing':
        frames['D1'] = pd.DataFrame()
    else:
        frames['D1']['time'] -= pd.Timedelta(days=7)
    result = MalaysianSNRStrategy(provider, MalaysianSNRConfig(allowed_symbols=())).analyze_symbol('Step Index', now)
    assert result['reason'] == ('MISSING_CLOSED_D1' if issue == 'missing' else 'STALE_CANDLES_D1')


@pytest.mark.parametrize('symbol,direction', [('Boom 300 Index','SELL'), ('Crash 600 Index','BUY')])
def test_boom_crash_direction_policy_is_preserved(symbol, direction):
    provider, _, now = market(direction, direction)
    result = MalaysianSNRStrategy(provider, MalaysianSNRConfig(allowed_symbols=())).analyze_symbol(symbol, now)
    assert result['reason'] == 'DIRECTION_POLICY_BLOCKED'


def test_persisted_changes_apply_to_existing_strategy_without_restart(tmp_path):
    path = tmp_path/'settings.sqlite3'
    repo = TradingRepository(path)
    provider, _, now = market()
    strategy = MalaysianSNRStrategy(provider, MalaysianSNRConfig(allowed_symbols=()),
                                    runtime_settings_loader=repo.latest_msnr_runtime_settings)
    assert strategy.analyze_symbol('Step Index', now)['valid']
    saved = repo.save_msnr_runtime_settings(True)
    blocked = strategy.analyze_symbol('Step Index', now)
    assert blocked['reason'] == 'D1_BIAS_CONFLICT'
    assert blocked['runtime_settings_version'] == saved['version']
    assert TradingRepository(path).latest_msnr_runtime_settings()[SETTING] is True
    assert repo.latest_msnr_runtime_settings(source='LIVE')[SETTING] is False
    repo.save_msnr_runtime_settings(False)
    assert strategy.analyze_symbol('Step Index', now)['valid']


def test_unreadable_settings_do_not_silently_disable_veto():
    provider, _, now = market()
    def broken():
        raise RuntimeError('DB unavailable')
    strategy = MalaysianSNRStrategy(provider, MalaysianSNRConfig(allowed_symbols=()), broken)
    assert strategy.analyze_symbol('Step Index', now)['reason'] == 'MSNR_SETTINGS_UNAVAILABLE'


@pytest.fixture
def dashboard(tmp_path):
    repo = TradingRepository(tmp_path/'dashboard.sqlite3')
    dash = RealtimeDashboardService(repository=repo, host='127.0.0.1', port=0, state_path=tmp_path/'state.json')
    with patch.object(dash.news_service, 'start'), patch.object(dash.news_service, 'stop'):
        dash.start(live=False)
        try:
            yield dash
        finally:
            dash.stop()


def api(dash, body=None):
    request = urllib.request.Request(dash.url+PATH,
        data=json.dumps(body).encode() if body is not None else None,
        headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.load(response)


def test_dashboard_http_round_trip_and_restart_persistence(dashboard):
    assert api(dashboard)['settings'][SETTING] is False
    assert api(dashboard, {SETTING:True})['settings'][SETTING] is True
    assert api(dashboard)['settings'][SETTING] is True
    assert api(dashboard, {SETTING:False})['settings'][SETTING] is False


@pytest.mark.parametrize('body', [{SETTING:'false'}, {SETTING:1}, {}, {SETTING:True,'enable_daily_storyline_filter':False}])
def test_dashboard_rejects_malformed_or_unrelated_settings(dashboard, body):
    with pytest.raises(urllib.error.HTTPError) as error:
        api(dashboard, body)
    assert error.value.code == 400
    assert api(dashboard)['settings'][SETTING] is False


def test_route_installation_on_existing_server_is_idempotent(dashboard):
    install_strategy_settings_routes(dashboard)
    installed = dashboard._server.RequestHandlerClass.do_GET
    install_strategy_settings_routes(dashboard)
    assert dashboard._server.RequestHandlerClass.do_GET is installed
    assert api(dashboard)['ok']


def test_runtime_telemetry_preserves_disabled_veto_and_preference_version():
    view = LiveTradingEngine._current_strategy_view_from_analysis({
        'action':'WAITING_MALAYSIAN_SNR', 'macro_bias':'SELL',
        'macro_bias_enforced':False, 'runtime_settings_version':7,
        'strategy_version':'msnr-v2.6-structural-opportunities', 'fractal_min_body_ratio':.50,
        'fractal_max_entry_distance_atr':.50,
    })
    assert view['macro_bias_enforced'] is False
    assert view['macro_bias'] == 'SELL'
    assert view['runtime_settings_version'] == 7
    assert view['fractal_min_body_ratio'] == .50
    assert view['fractal_max_entry_distance_atr'] == .50


def test_dashboard_reload_updates_legacy_in_process_analyzer_without_restarting(tmp_path):
    from dashboard.strategy_bases_page import _sync_runtime_dashboard_if_needed
    repo = TradingRepository(tmp_path/'legacy.sqlite3')
    provider, _, now = market()
    cfg = MalaysianSNRConfig(allowed_symbols=(), strategy_version='msnr-v2.1-persistent-retest', tp2_runner_rr=4.)
    previous = MalaysianSNRStrategy(provider, cfg)
    engine = LiveTradingEngine.__new__(LiveTradingEngine)
    engine.config = SimpleNamespace(source='DEMO')
    engine.repository = repo
    engine.malaysian_snr_strategy = previous
    _sync_runtime_dashboard_if_needed()
    current = engine.malaysian_snr_strategy
    assert current is not previous
    assert current.provider is provider
    assert current.config.tp2_runner_rr == 4.
    assert current.config.strategy_version == MalaysianSNRConfig().strategy_version
    assert current.analyze_symbol('Step Index', now)['valid']
    repo.save_msnr_runtime_settings(True)
    assert current.analyze_symbol('Step Index', now)['reason'] == 'D1_BIAS_CONFLICT'


@pytest.mark.parametrize('direction', ['BUY', 'SELL'])
@pytest.mark.parametrize('symbol', ['Step Index', 'EURUSD', 'XAUUSD'])
@pytest.mark.parametrize('body,accepted', [(.49, False), (.50, True), (.54, True), (.56, True)])
def test_fractal_body_50_percent_boundary_across_directions_and_assets(direction, symbol, body, accepted):
    provider, frames, now = market(direction, direction)
    sign = 1 if direction == 'BUY' else -1
    frames['H1'].loc[39, 'open'] = frames['H1'].loc[39, 'close'] - sign * 7 * body
    config = MalaysianSNRConfig(allowed_symbols=(), enable_quasimodo_pattern=False)
    result = MalaysianSNRStrategy(provider, config).analyze_symbol(symbol, now)
    assert result['valid'] is accepted, result
    assert result.get('signal', result)['fractal_min_body_ratio'] == .50
    if accepted:
        assert result['signal']['scenario'] == 'ESC_3_FRACTAL'
        assert result['signal'][BODY_SETTING] == .50


@pytest.mark.parametrize('direction', ['BUY', 'SELL'])
def test_config_and_persisted_fractal_threshold_change_existing_analyzer(tmp_path, direction):
    repo = TradingRepository(tmp_path/'fractal.sqlite3')
    provider, frames, now = market(direction, direction)
    frames['H1'].loc[39, 'open'] = 100.5 if direction == 'BUY' else 99.5
    cfg = MalaysianSNRConfig(allowed_symbols=(), enable_quasimodo_pattern=False, fractal_min_body_ratio=.55)
    assert not MalaysianSNRStrategy(provider, cfg).analyze_symbol('Step Index', now)['valid']
    strategy = MalaysianSNRStrategy(provider, cfg, repo.latest_msnr_runtime_settings)
    # The persisted default 50% overrides the isolated analyzer's 55%.
    assert strategy.analyze_symbol('Step Index', now)['valid']
    repo.save_msnr_runtime_settings(fractal_min_body_ratio=.55)
    assert not strategy.analyze_symbol('Step Index', now)['valid']
    saved = repo.save_msnr_runtime_settings(fractal_min_body_ratio=.50)
    result = strategy.analyze_symbol('Step Index', now)
    assert result['valid'], result
    assert result['signal']['runtime_settings_version'] == saved['version']
    assert result['signal']['macro_bias_enforced'] is False
    assert result['diagnostics'][BODY_SETTING] == .50


def test_joint_settings_and_partial_updates_preserve_peer_and_restart(dashboard):
    saved = api(dashboard, {SETTING: True, BODY_SETTING: .55})['settings']
    assert saved[SETTING] is True and saved[BODY_SETTING] == .55
    assert api(dashboard, {SETTING: False})['settings'][BODY_SETTING] == .55
    only_body = api(dashboard, {BODY_SETTING: .50})['settings']
    assert only_body[SETTING] is False
    assert only_body[BODY_SETTING] == .50
    reopened = TradingRepository(dashboard.repository.db_path).latest_msnr_runtime_settings()
    assert reopened == only_body
    assert dashboard.repository.latest_msnr_runtime_settings(source='LIVE')[BODY_SETTING] == .50


@pytest.mark.parametrize('value', [None, True, '50', -.01, 1.01, float('nan'), float('inf')])
def test_invalid_body_setting_rejects_entire_update(dashboard, value):
    before = api(dashboard)['settings']
    with pytest.raises(urllib.error.HTTPError) as error:
        api(dashboard, {SETTING: True, BODY_SETTING: value})
    assert error.value.code == 400
    assert api(dashboard)['settings'] == before


def test_legacy_persisted_d1_only_preference_receives_50_percent_default(tmp_path):
    from database.strategy_preferences import StrategyRuntimePreference
    repo = TradingRepository(tmp_path/'old.sqlite3')
    saved = repo.save_msnr_runtime_settings(True)
    with repo.Session() as session:
        row = session.get(StrategyRuntimePreference, saved['version'])
        row.settings_json = json.dumps({SETTING: True})
        session.commit()
    current = repo.latest_msnr_runtime_settings()
    assert current[SETTING] is True
    assert current[BODY_SETTING] == .50


def test_invalid_live_body_setting_blocks_analysis_without_silent_fallback():
    provider, _, now = market()
    strategy = MalaysianSNRStrategy(provider, MalaysianSNRConfig(allowed_symbols=()),
        lambda: {SETTING: False, BODY_SETTING: float('nan')})
    assert strategy.analyze_symbol('Step Index', now)['reason'] == 'MSNR_SETTINGS_UNAVAILABLE'


@pytest.mark.parametrize('daily,enforced,minimum,expected', [
    ('BUY', False, .50, 1), ('SELL', False, .50, 1), ('NEUTRAL', False, .50, 1),
    ('SELL', True, .50, 0), ('BUY', False, .55, 0),
])
def test_replay_screening_matches_new_fractal_threshold_and_optional_daily_veto(daily, enforced, minimum, expected):
    import strategy.malaysian_snr.malaysian_snr_strategy as module
    from tools.replay_msnr_two_year_comparison import replay, install_acceleration, restore
    _, frames, now = market(daily=daily)
    frames['H1'].loc[39, 'open'] = 100.5
    future = pd.DataFrame({'time':pd.date_range(now, periods=4, freq='15min'),
                          'open':103.3, 'high':104., 'low':96., 'close':100.})
    frames['M15'] = pd.concat([frames['M15'], future], ignore_index=True)
    cfg = MalaysianSNRConfig(allowed_symbols=(), enable_quasimodo_pattern=False,
        enable_synthetic_daily_storyline_filter=enforced, fractal_min_body_ratio=minimum)
    row = {'symbol':'Step Index', 'point':0., 'fallback_spread':0.}
    start, end = now-pd.Timedelta(minutes=15), now+pd.Timedelta(minutes=15)
    reference, _ = replay(row, frames, module, cfg, start, end, accelerated=False, screen=False)
    original = install_acceleration(module)
    try:
        optimized, _ = replay(row, frames, module, cfg, start, end)
    finally:
        restore(module, original)
    assert len(reference) == expected
    assert optimized == reference


def distant_market(direction, distance_atr):
    provider, frames, now = market(direction, direction)
    prices = [103.1, 103 + 2 * distance_atr + .1, 102.9, 103 + 2 * distance_atr]
    if direction == 'SELL':
        opening, high, low, close = prices
        prices = [200-opening, 200-low, 200-high, 200-close]
    frames['M15'].loc[60, ['open','high','low','close']] = prices
    return provider, frames, now


@pytest.mark.parametrize('direction', ['BUY', 'SELL'])
@pytest.mark.parametrize('distance,limit,expected', [
    (.39, .40, True), (.45, .40, False), (.45, .50, True),
    (.50, .50, True), (.51, .50, False), (.55, .60, True),
])
def test_fractal_distance_applies_to_m15_confirmation_without_global_clamp(direction, distance, limit, expected):
    provider, _, now = distant_market(direction, distance)
    cfg = MalaysianSNRConfig(allowed_symbols=(), enable_quasimodo_pattern=False,
        max_entry_distance_atr=.30, fractal_max_entry_distance_atr=limit)
    with patch('strategy.malaysian_snr.malaysian_snr_strategy.compute_atr', return_value=pd.Series([2.])):
        result = MalaysianSNRStrategy(provider, cfg).analyze_symbol('Step Index', now)
    assert result['valid'] is expected, result
    details = result['signal'] if expected else result['diagnostics']
    assert details['max_entry_distance_atr'] == limit
    assert details[DISTANCE_SETTING] == limit
    if not expected:
        assert result['reason'] == 'ENTRY_TOO_FAR_FROM_LEVEL'


def test_persisted_distance_applies_without_restart_and_preserves_other_controls(tmp_path):
    repo = TradingRepository(tmp_path/'distance.sqlite3')
    provider, _, now = distant_market('BUY', .45)
    strategy = MalaysianSNRStrategy(provider, MalaysianSNRConfig(allowed_symbols=(), enable_quasimodo_pattern=False),
                                    repo.latest_msnr_runtime_settings)
    with patch('strategy.malaysian_snr.malaysian_snr_strategy.compute_atr', return_value=pd.Series([2.])):
        assert strategy.analyze_symbol('Step Index', now)['valid']
        repo.save_msnr_runtime_settings(False, fractal_min_body_ratio=.55, fractal_max_entry_distance_atr=.40)
        assert strategy.analyze_symbol('Step Index', now)['reason'] == 'ENTRY_TOO_FAR_FROM_LEVEL'
        saved = repo.save_msnr_runtime_settings(fractal_max_entry_distance_atr=.50)
        signal = strategy.analyze_symbol('Step Index', now)['signal']
        assert signal['max_entry_distance_atr'] == .50
        assert signal['runtime_settings_version'] == saved['version']
        assert signal[BODY_SETTING] == .55
        assert signal['macro_bias_enforced'] is False
    assert TradingRepository(repo.db_path).latest_msnr_runtime_settings() == saved


def test_quasimodo_retains_general_distance_while_fractal_uses_its_own():
    provider, frames, _ = market()
    cfg = MalaysianSNRConfig(allowed_symbols=(), max_entry_distance_atr=.30, fractal_max_entry_distance_atr=.75)
    pattern = {'direction':'BUY', 'shoulder':103., 'neckline':103., 'head':97.}
    with patch('strategy.malaysian_snr.malaysian_snr_strategy.quasimodo_candidates', return_value=[pattern]):
        setups = MalaysianSNRStrategy(provider, cfg)._setups_at_break(frames['H1'])
    assert next(s for s in setups if s['scenario'] == 'ESC_3_QUASIMODO')['max_entry_distance_atr'] == .30
    assert next(s for s in setups if s['scenario'] == 'ESC_3_FRACTAL')['max_entry_distance_atr'] == .75


def test_three_controls_saved_together_and_partial_updates_preserve_other_values(dashboard):
    saved = api(dashboard, {SETTING: True, BODY_SETTING: .55, DISTANCE_SETTING: .75})['settings']
    assert saved[DISTANCE_SETTING] == .75
    updated = api(dashboard, {DISTANCE_SETTING: .50})['settings']
    assert updated[SETTING] is True and updated[BODY_SETTING] == .55
    assert api(dashboard, {SETTING: False})['settings'][DISTANCE_SETTING] == .50
    assert api(dashboard, {BODY_SETTING: .50})['settings'][DISTANCE_SETTING] == .50
    assert TradingRepository(dashboard.repository.db_path).latest_msnr_runtime_settings()[DISTANCE_SETTING] == .50
    assert dashboard.repository.latest_msnr_runtime_settings(source='LIVE')[DISTANCE_SETTING] == .50


@pytest.mark.parametrize('value', [None, False, '0.5', -.01, float('nan'), float('inf'), 10**400])
def test_invalid_distance_setting_rejects_entire_update(dashboard, value):
    before = api(dashboard)['settings']
    with pytest.raises(urllib.error.HTTPError) as error:
        api(dashboard, {SETTING: True, BODY_SETTING: .55, DISTANCE_SETTING: value})
    assert error.value.code == 400
    assert api(dashboard)['settings'] == before


def test_old_body_and_d1_preferences_receive_distance_default_without_resetting(tmp_path):
    from database.strategy_preferences import StrategyRuntimePreference
    repo = TradingRepository(tmp_path/'old_two_controls.sqlite3')
    saved = repo.save_msnr_runtime_settings(True, fractal_min_body_ratio=.55)
    with repo.Session() as session:
        session.get(StrategyRuntimePreference, saved['version']).settings_json = json.dumps({SETTING: True, BODY_SETTING: .55})
        session.commit()
    current = repo.latest_msnr_runtime_settings()
    assert current[SETTING] is True and current[BODY_SETTING] == .55
    assert current[DISTANCE_SETTING] == .50


@pytest.mark.parametrize('direction', ['BUY', 'SELL'])
@pytest.mark.parametrize('limit,distance,expected', [(.40,.45,False), (.50,.45,True), (.50,.50,True), (.50,.51,False), (.60,.55,True)])
def test_execution_quote_obeys_fractal_limit_before_planning_any_order(direction, limit, distance, expected):
    from strategy.execution.live_trading_engine import LiveTradingConfig
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(bot_profile='MALAYSIAN_SNR', split_entries_enabled=True, single_entry_fallback_enabled=True)
    sign = 1 if direction == 'BUY' else -1
    signal = {'setup_id':'distance', 'ref_level':100., 'atr':2., 'max_entry_distance_atr':limit,
              'invalidation_level':100-sign*3, 'tp1_rr':2., 'runner_rr':3.,
              'setup_expires_at':(pd.Timestamp.now(tz='UTC')+pd.Timedelta(minutes=1)).isoformat()}
    calls = []
    def build(specs, mode):
        calls.append(mode)
        return ([{'name':s[0], 'rr':s[2]} for s in specs], None)
    legs, failure, _, _ = engine._plan_execution_legs(exact_symbol='Step Index', direction=direction,
        entry=100+sign*2*distance, sl=100-sign*3, rr=3., strategy_name='MALAYSIAN_SNR', signal=signal,
        total_risk_amount=100., risk_fraction=.5, silver_risk_cap=False, build_plan=build)
    if expected:
        assert [leg['name'] for leg in legs] == ['TP1','RUNNER']
        assert len(calls) == 1
    else:
        assert legs is None and failure['code'] == 'MSNR_ENTRY_CONTEXT_CHANGED'
        assert not calls
