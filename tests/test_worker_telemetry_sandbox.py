from datetime import datetime, timezone
import json
import pytest
from tools.test_worker_telemetry import run_test_suite, run_worker_cycle
from strategy.smc.telemetry_logger import SMCTelemetryTracker


@pytest.mark.parametrize('extended,cycles,scored',[(False,3,1),(True,5,3)])
def test_mock_worker_flow_and_persisted_telemetry(tmp_path,extended,cycles,scored):
    result=run_test_suite(tmp_path,extended=extended,emit=False,
        now=datetime(2026,9,27,12,tzinfo=timezone.utc))
    assert result['passed'] and result['scenarios']==cycles
    summary=result['telemetry']
    assert summary['total_evaluations']==scored
    assert summary['status_counts']['ADAPTIVE_APPROVED']==1
    assert summary['status_counts']['STRICT_APPROVED']==int(extended)
    assert summary['pipeline_funnel']['stage_counts']['POSITION_GUARD']==2
    assert summary['m5_diagnostic_tags']['M5_SWEEP_M1_CHOCH_EARLY_TRIGGER']==1+int(extended)
    assert all(not row['order_sent'] for row in result['results'])
    disk=json.loads((tmp_path/'report.json').read_text())
    assert disk['telemetry']['total_evaluations']==scored
    clean=result['results'][2]
    assert clean['broker_calls']==['positions','orders','price','H1','M15','M5','M1']
    assert clean['final_score']==75


def test_harness_refuses_real_broker():
    with pytest.raises(TypeError,match='only MockMT5BrokerAPI'):
        run_worker_cycle('X','BUY',object(),telemetry=SMCTelemetryTracker(),evaluation_id='test')


def test_dual_trigger_datetimes_are_persisted_as_iso_strings(tmp_path):
    from tools.test_worker_telemetry import MockMT5BrokerAPI, SYMBOL
    tracker=SMCTelemetryTracker(output_dir=tmp_path)
    now=datetime(2026,9,27,12,tzinfo=timezone.utc)
    run_worker_cycle(SYMBOL,'BUY',MockMT5BrokerAPI(now=now),telemetry=tracker,evaluation_id='clock')
    tracker.flush()
    snapshot=json.loads(next(tmp_path.glob('*.json')).read_text())
    detail=snapshot['last_evaluation']['m5_detail']
    assert detail['confirmation_timestamp']=='2026-09-27T11:59:00+00:00'
    assert detail['sweep_timestamp']=='2026-09-27T11:57:00+00:00'


def test_old_worker_snapshots_do_not_replace_current_run(tmp_path):
    (tmp_path/'snapshots').mkdir()
    (tmp_path/'snapshots'/'SANDBOX_DUAL_WORKER_999999.json').write_text('{"total_evaluations":999}')
    assert run_test_suite(tmp_path,extended=True,emit=False)['passed']
