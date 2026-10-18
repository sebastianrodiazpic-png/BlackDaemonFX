from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from strategy.execution.live_trading_engine import LiveTradingEngine
from strategy.malaysian_snr.runtime_settings import msnr_default_settings, validate_msnr_patch
from strategy.malaysian_snr.universe import resolve_symbol_settings


def engine(profile='MALAYSIAN_SNR',**patch):
    value=object.__new__(LiveTradingEngine)
    settings={**msnr_default_settings(),**patch}
    value.config=SimpleNamespace(bot_profile=profile,step_min_adx=25.,step_prune_toxic_assets=False)
    value.provider=Mock()
    value.malaysian_snr_strategy=SimpleNamespace(settings_snapshot=lambda:settings)
    return value


def signal(adx=24):
    return {'strategy_name':'MALAYSIAN_SNR','adx':adx,'timeframe':'M15',
        'entry_timeframe':'M15','structure_timeframe':'H1'}


def test_only_standard_step_snr_uses_its_own_threshold():
    value=engine(step_symbol_min_adx={'Step Index':23.})
    assert value._step_quality_gate('Step Index',signal()) is None
    reading=value._step_quality_gate('Step Index 200',signal())
    assert reading['min_adx']==25. and reading['reason']=='MSNR_STEP_EXECUTION_ADX_BELOW_MINIMUM'


@pytest.mark.parametrize('profile',['STEP','SYNTHETICS'])
def test_other_workers_keep_the_legacy_threshold(profile):
    value=engine(profile,step_min_adx=15.,step_symbol_min_adx={'Step Index':10.})
    assert value._step_quality_gate('Step Index',signal())['min_adx']==25.


def test_missing_snr_adx_cannot_authorize_an_entry():
    value=engine()
    value.provider.get_candles.return_value=None
    assert value._step_quality_gate('Step Index',signal(None))['reason']=='MSNR_STEP_EXECUTION_ADX_BELOW_MINIMUM'


def test_frozen_controls_and_provenance_match_the_execution_threshold():
    value=engine()
    controls={**msnr_default_settings(),'step_symbol_min_adx':{'Step Index':23.},'version':13}
    payload=signal()
    assert value._step_quality_gate('Step Index',payload,{'runtime_controls':controls}) is None
    assert payload['step_execution_quality']=={'minimum_adx':23.,'captured_adx':24.,'runtime_settings_version':13}
    assert resolve_symbol_settings(controls,'Step Indexmicro')['step_min_adx']==23.


@pytest.mark.parametrize('patch',[{'step_min_adx':True},{'step_min_adx':float('nan')},
    {'step_min_adx':10**400},{'step_symbol_min_adx':{'BTCUSD':23}},
    {'step_symbol_min_adx':{'Step Index':float('inf')}},{'step_symbol_min_adx':{'Step Index':True}}])
def test_invalid_step_thresholds_are_rejected(patch):
    with pytest.raises(ValueError):validate_msnr_patch(patch)
