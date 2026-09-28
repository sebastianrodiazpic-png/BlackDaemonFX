"""Offline worker telemetry harness using the production guard, evaluator and tracker.

No MT5 imports, candle detector, execution adapter or order submission.
Run: python -m tools.test_worker_telemetry --extended
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
import argparse
import json
import os
import sys
from uuid import uuid4

if __package__ in {None, ''}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from strategy.execution.active_position_guard import read_active_position_guard
from strategy.smc.candidate_evaluator import evaluate_candidate_signal_v4
from strategy.smc.telemetry_logger import SMCTelemetryTracker

SYMBOL = 'Volatility 100 Index'


class MockMT5BrokerAPI:
    def __init__(self, scenario='CLEAN', now=None):
        if scenario not in {'CLEAN', 'ACTIVE_TRADE', 'PENDING_ORDER', 'STRICT', 'EXPIRED'}:
            raise ValueError('Unknown sandbox scenario: ' + scenario)
        self.scenario = scenario
        self.now = now or datetime.now(timezone.utc)
        self.calls = []

    def get_open_positions(self):
        self.calls.append('positions')
        return [SimpleNamespace(symbol=SYMBOL, ticket=987654321)] if self.scenario == 'ACTIVE_TRADE' else []

    def get_pending_orders(self):
        self.calls.append('orders')
        return [SimpleNamespace(symbol=SYMBOL, ticket=123456789)] if self.scenario == 'PENDING_ORDER' else []

    def get_current_price(self, symbol):
        self.calls.append('price')
        return 1250.50

    def get_structure_data(self, symbol, timeframe):
        self.calls.append(timeframe)
        if timeframe == 'H1':
            # Real evaluator requires range evidence, not only a DISCOUNT label.
            return dict(low=1200., high=1400., source='PIVOT', adaptive_context_enabled=True)
        if timeframe == 'M15':
            return dict(break_quality='BOS', is_invalidated=False)
        if timeframe == 'M5':
            return dict(has_sweep=True, has_choch=False,
                        sweep_timestamp=self.now-timedelta(minutes=15 if self.scenario == 'EXPIRED' else 3))
        if timeframe == 'M1':
            return dict(has_choch=True, has_fvg=self.scenario == 'STRICT',
                        choch_timestamp=self.now-timedelta(minutes=11 if self.scenario == 'EXPIRED' else 1))
        raise ValueError('Unexpected timeframe: ' + timeframe)


def run_worker_cycle(symbol, signal_type, broker_api, *, telemetry, evaluation_id):
    """Sandbox orchestration over production functions; approved means score only."""
    if not isinstance(broker_api, MockMT5BrokerAPI):
        raise TypeError('This harness accepts only MockMT5BrokerAPI')
    guard = read_active_position_guard(symbol, broker_api)
    common = dict(symbol=symbol, timestamp=broker_api.now.isoformat(), sandbox=True,
                  order_sent=False, execution_status='NOT_EXECUTED_SANDBOX')
    if not guard['can_analyze']:
        result = dict(guard, **common, approved=False, valid=False, action=guard['status'],
                      reasons=[guard['reason']])
        telemetry.log_pipeline_result(result, evaluation_id=evaluation_id)
        return result

    price = broker_api.get_current_price(symbol)
    raw = {tf: broker_api.get_structure_data(symbol, tf) for tf in ('H1','M15','M5','M1')}
    result = evaluate_candidate_signal_v4(signal_type, price, raw['H1'], raw['M15'],
        raw['M5'], raw['M1'], current_time=broker_api.now)
    result.update(common)
    result['diagnostic_tag'] = result['m5_detail']['diagnostic_tag']
    telemetry.log_evaluation(result, symbol, evaluation_id=evaluation_id)
    telemetry.log_pipeline_result(dict(result, valid=result['approved'],
        action='SIGNAL_READY' if result['approved'] else 'NO_M5_CONFIRMATION',
        reason='SANDBOX_SCORE_APPROVED' if result['approved'] else '; '.join(result['reasons'])),
        evaluation_id=evaluation_id)
    return result


def run_test_suite(output_dir=None, extended=False, emit=True, now=None):
    now = now or datetime.now(timezone.utc)
    root = Path(output_dir) if output_dir else (Path(__file__).resolve().parents[1]/
        'storage/sandbox/worker_telemetry'/f"{now:%Y%m%dT%H%M%S}_{uuid4().hex[:8]}")
    root.mkdir(parents=True, exist_ok=True)
    tracker = SMCTelemetryTracker(bot_name='SANDBOX_DUAL_WORKER', output_dir=root/'snapshots')
    scenarios = ['ACTIVE_TRADE','PENDING_ORDER','CLEAN'] + (['STRICT','EXPIRED'] if extended else [])
    expected = dict(ACTIVE_TRADE='BLOCKED_ACTIVE_TRADE', PENDING_ORDER='BLOCKED_PENDING_ORDER',
                    CLEAN='ADAPTIVE_APPROVED', STRICT='STRICT_APPROVED', EXPIRED='REJECTED')
    results = []
    for scenario in scenarios:
        broker = MockMT5BrokerAPI(scenario, now)
        result = run_worker_cycle(SYMBOL,'BUY',broker,telemetry=tracker,evaluation_id=scenario)
        result.update(scenario=scenario, broker_calls=list(broker.calls))
        if result['status'] != expected[scenario]:
            raise AssertionError(f"{scenario}: expected {expected[scenario]}, got {result['status']}")
        if scenario in {'ACTIVE_TRADE','PENDING_ORDER'} and broker.calls != ['positions','orders']:
            raise AssertionError('Blocked worker requested market data')
        if scenario == 'CLEAN' and (result['final_score'] != 75 or
                result['diagnostic_tag'] != 'M5_SWEEP_M1_CHOCH_EARLY_TRIGGER'):
            raise AssertionError('Unexpected M1 score or diagnostic')
        if scenario == 'EXPIRED' and result['diagnostic_tag'] != 'EXPIRED_SIGNAL':
            raise AssertionError('Expired signal did not receive the latency diagnostic')
        results.append(result)
        if emit:
            print(json.dumps(result, indent=2, default=str, ensure_ascii=True))
    tracker.flush()
    summary = tracker.get_summary_report()
    scored = 3 if extended else 1
    if summary['total_evaluations'] != scored or summary['pipeline_funnel']['total'] != len(scenarios):
        raise AssertionError('Telemetry mixed blocked cycles with scored candidates')
    if summary['pipeline_funnel']['stage_counts'].get('POSITION_GUARD') != 2:
        raise AssertionError('Missing position/order guard telemetry')
    snapshot = root/'snapshots'/f'SANDBOX_DUAL_WORKER_{os.getpid()}.json'
    if not snapshot.exists():
        raise AssertionError('Telemetry snapshot was not persisted')
    persisted = json.loads(snapshot.read_text(encoding='utf-8'))
    if persisted['total_evaluations'] != scored:
        raise AssertionError('Persisted telemetry does not match memory')
    report = dict(passed=True, sandbox=True, scope='MOCK_EVIDENCE_GUARD_SCORE_TELEMETRY_NO_ORDERS',
                  scenarios=len(scenarios), results=results, telemetry=summary)
    path = root/'report.json'
    path.write_text(json.dumps(report, indent=2, default=str, ensure_ascii=True), encoding='utf-8')
    if emit:
        print(f"PASS: {len(scenarios)} scenarios; {scored} scored candidates; 2 position guards")
        print(f"Report: {path.resolve()}")
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--extended', action='store_true', help='Also verify strict approval and expired M1')
    parser.add_argument('--output-dir', type=Path)
    args = parser.parse_args()
    run_test_suite(args.output_dir, extended=args.extended)
