from types import SimpleNamespace
from database.repository import TradingRepository
from dashboard.realtime_dashboard import RealtimeDashboardService
from strategy.execution.live_trading_engine import LiveTradingEngine
from app.main import _selection_profile_for_bot


def test_repository_profiles_are_independent(tmp_path):
    repo=TradingRepository(db_path=tmp_path/'profiles.db')
    repo.save_instrument_selection_profile(['EURUSD','GBPUSD'],selection_profile='FOREX')
    repo.save_instrument_selection_profile(['XAUUSDmicro','US500'],selection_profile='ORB')
    assert repo.latest_instrument_selection_profile('FOREX')['selected_symbols']==['EURUSD','GBPUSD']
    assert repo.latest_instrument_selection_profile('ORB')['selected_symbols']==['XAUUSDmicro','US500']


def test_forex_update_does_not_change_orb(tmp_path):
    repo=TradingRepository(db_path=tmp_path/'profiles.db')
    orb=repo.save_instrument_selection_profile(['XAUUSDmicro','US500'],selection_profile='ORB')
    repo.save_instrument_selection_profile(['EURUSD'],selection_profile='FOREX')
    after=repo.latest_instrument_selection_profile('ORB')
    assert after['version']==orb['version']
    assert after['selected_symbols']==orb['selected_symbols']


def test_dashboard_defaults_each_profile_to_its_own_universe(tmp_path):
    repo=TradingRepository(db_path=tmp_path/'dash.db')
    svc=RealtimeDashboardService(repository=repo,port=0,state_path=tmp_path/'state.json')
    svc.set_instrument_catalog({'volatility':['Volatility 75 Index'],'forex':['EURUSD','GBPUSD'],
                                'orb_ny_gold':['XAUUSDmicro'],'orb_ny_us500':['US500']})
    p=svc.snapshot()['selection_profiles']
    assert set(p['FOREX'])=={'EURUSD','GBPUSD'}
    assert set(p['ORB'])=={'XAUUSDmicro','US500'}
    assert p['SYNTHETICS']==['Volatility 75 Index']


def test_dashboard_saves_only_target_profile(tmp_path):
    repo=TradingRepository(db_path=tmp_path/'dash.db')
    svc=RealtimeDashboardService(repository=repo,port=0,state_path=tmp_path/'state.json')
    svc.set_instrument_catalog({'forex':['EURUSD','GBPUSD'],'orb_ny_gold':['XAUUSDmicro'],'orb_ny_us500':['US500']})
    before=list(svc.snapshot()['selection_profiles']['ORB'])
    result=svc.update_selected_symbols(['EURUSD'],selection_profile='FOREX')
    assert result['ok'] is True
    state=svc.snapshot()['selection_profiles']
    assert state['FOREX']==['EURUSD']
    assert state['ORB']==before


def test_empty_forex_selection_is_persistent_and_means_no_new_entries(tmp_path):
    repo=TradingRepository(db_path=tmp_path/'empty.db')
    repo.save_instrument_selection_profile([],selection_profile='FOREX')
    assert repo.latest_instrument_selection_profile('FOREX')['selected_symbols']==[]


def _engine(profile,repo):
    e=object.__new__(LiveTradingEngine); e.repository=repo; e.dashboard_service=None
    e.config=SimpleNamespace(bot_profile=profile,source='DEMO')
    return e


def test_workers_read_profile_selection_each_cycle(tmp_path):
    repo=TradingRepository(db_path=tmp_path/'cycle.db')
    repo.save_instrument_selection_profile(['EURUSD'],selection_profile='FOREX')
    repo.save_instrument_selection_profile(['US500'],selection_profile='ORB')
    fx=_engine('FOREX',repo); orb=_engine('ORB',repo)
    assert fx._selected_cycle_symbols(['EURUSD','GBPUSD'])==['EURUSD']
    assert orb._selected_cycle_symbols(['XAUUSDmicro','US500'])==['US500']
    repo.save_instrument_selection_profile(['GBPUSD'],selection_profile='FOREX')
    assert fx._selected_cycle_symbols(['EURUSD','GBPUSD'])==['GBPUSD']


def test_profile_mapping():
    assert _selection_profile_for_bot('FOREX')=='FOREX'
    assert _selection_profile_for_bot('ORB')=='ORB'
    assert _selection_profile_for_bot('BOOM')=='SYNTHETICS'


def test_instrument_page_has_three_profile_tabs():
    from dashboard import realtime_dashboard as rd
    assert 'data-profile="SYNTHETICS"' in rd._INSTRUMENTS_HTML
    assert 'data-profile="FOREX"' in rd._INSTRUMENTS_HTML
    assert 'data-profile="ORB"' in rd._INSTRUMENTS_HTML
    assert 'selection_profile:activeProfile' in rd._INSTRUMENTS_HTML
