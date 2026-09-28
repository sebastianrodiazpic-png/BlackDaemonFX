import copy
from pathlib import Path
from unittest.mock import patch
import pytest
from dashboard.smc_trial import _atomic_write
from strategy.ai.training import _trade_label, _logical_setup_records
from strategy.ai.trade_observation import capture_observation, learning_rows, eligibility
from strategy.ai.feature_extraction import FEATURE_NAMES
from strategy.smc.entry_preflight import obstacle_guard


def test_atomic_retry_preserves_and_replaces(tmp_path):
    target = tmp_path / 'state.json'
    target.write_text('old')
    original = Path.replace
    calls = []
    def replace(self, dest):
        calls.append(self)
        if len(calls) < 3:
            assert target.read_text() == 'old'
            raise PermissionError('sharing violation')
        return original(self, dest)
    with patch.object(Path, 'replace', replace), patch('dashboard.smc_trial.time.sleep'):
        _atomic_write(target, 'new')
    assert target.read_text() == 'new'
    assert len(calls) == 3
    assert not list(tmp_path.glob('*.tmp'))


def test_atomic_permanent_failure_preserves_last_good(tmp_path):
    target = tmp_path / 'state.json'
    target.write_text('old')
    with patch.object(Path, 'replace', side_effect=PermissionError('locked')), patch('dashboard.smc_trial.time.sleep'):
        with pytest.raises(PermissionError):
            _atomic_write(target, 'new')
    assert target.read_text() == 'old'
    assert not list(tmp_path.glob('*.tmp'))


@pytest.mark.parametrize('reason', ['mt5_mobile', 'mt5_client', 'mt5_web'])
def test_manual_exit_does_not_label_strategy_or_sibling(reason):
    row = {'status':'CLOSED', 'realized_rr':2, 'net_pnl':100, 'exit_reason':reason,
           'details':{'metadata':{'parent_execution_key':'setup', 'strategy_name':'SMC'}}}
    sibling = copy.deepcopy(row)
    sibling['exit_reason'] = 'mt5_tp'
    assert _trade_label(row) is None
    assert _trade_label(sibling) == 1
    assert _logical_setup_records([sibling, row], exclude_manual=True) == []
    assert eligibility(row)['reason'] == 'CIERRE_MANUAL_EXCLUIDO_DEL_MODELO_DE_ESTRATEGIA'


def test_broker_reason_alone_excludes_manual_label():
    row = {'status':'CLOSED', 'net_pnl':10, 'details':{'metadata':{'broker_exit':{'reason':'MOBILE'}}}}
    assert _trade_label(row) is None


def test_later_valid_risk_is_causal_immutable_and_single_sample():
    meta = {}
    first = {'evaluated_at':'2026-09-25T01:00:00Z', 'risk_distance':None,
             'observed_price':100, 'direction':'BUY', 'feature_names':list(FEATURE_NAMES),
             'features':{k:0 for k in FEATURE_NAMES}}
    assert capture_observation(meta, first)
    later = dict(first, evaluated_at='2026-09-25T01:01:00Z', observed_price=102, risk_distance=2)
    assert capture_observation(meta, later)
    assert not capture_observation(meta, dict(later, observed_price=110, risk_distance=10))
    assert meta['mt5_observation'] == first
    assert meta['mt5_risk_observation']['observed_price'] == 102
    row = {'status':'CLOSED', 'entry_time':'2026-09-25T00:59:00Z',
           'exit_time':'2026-09-25T02:00:00Z', 'exit_price':101,
           'exit_reason':'mt5_mobile', 'net_pnl':100, 'details':{'metadata':meta}}
    projected = learning_rows([row])
    assert len(projected) == 1
    assert projected[0]['entry_time'] == later['evaluated_at']
    assert projected[0]['realized_rr'] == -.5
    assert eligibility(row)['reason'] == 'ELEGIBLE_OBSERVACION'


def test_obstacles_after_minimum_are_not_full_clearance():
    result = obstacle_guard(100, 90, {'FULL':150}, 'BUY', [{'low':112, 'high':114}])
    assert result['valid']
    assert not result['full_path_clear']
    assert result['free_r_to_first_obstacle'] == 1.2
    assert result['target_r']['FULL'] == 5
    assert result['reason'] == 'SMC_MINIMUM_CORRIDOR_PASSED_WITH_OBSTACLES'


def test_manual_profit_reported_separately_from_comparable_strategy():
    from strategy.ai.closed_comparison import closed_comparison
    row = {'id':1, 'status':'CLOSED', 'exit_reason':'mt5_mobile', 'net_pnl':229.22,
           'details':{'metadata':{'bot_profile':'GOLD', 'strategy_name':'GOLD_QUARTERS'}}}
    result = closed_comparison([row], 'GOLD')
    assert result['closed_setups'] == 0
    assert result['manual_exit_setups'] == 1
    assert result['manual_exit_net_pnl'] == 229.22
    assert result['cohorts'] == {}
