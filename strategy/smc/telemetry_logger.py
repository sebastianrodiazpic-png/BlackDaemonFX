"""Thread-safe, bounded, per-worker telemetry for adaptive SMC candidates."""
from collections import Counter, OrderedDict, deque
from datetime import datetime, timezone
import atexit
import json
import logging
import math
import os
from pathlib import Path
import re
import threading
import time

logger = logging.getLogger("SMC_Telemetry")
logger.setLevel(logging.INFO)


class SMCTelemetryTracker:
    def __init__(self, bot_name="Synthetic_SMC_Bot", output_dir=None,
                 report_every=100, dedup_capacity=50000, history_capacity=1000):
        if report_every < 1 or dedup_capacity < 1 or history_capacity < 1:
            raise ValueError("Telemetry capacities must be positive")
        self.bot_name = bot_name
        self.output_dir = Path(output_dir) if output_dir is not None else None
        self.report_every = report_every
        self.dedup_capacity = dedup_capacity
        self.history_capacity = history_capacity
        self._lock = threading.RLock()
        self.reset_counters()

    def reset_counters(self):
        """Explicit session reset; no implicit daily reset or trading side effects."""
        with self._lock:
            self.start_time = datetime.now(timezone.utc)
            self.total_evaluations = 0
            self.status_counts = Counter({k: 0 for k in (
                "STRICT_APPROVED", "ADAPTIVE_APPROVED", "REJECTED_CRITICAL_VETO", "REJECTED_LOW_SCORE", "REJECTED_OTHER")})
            self.rejection_stages = Counter({k: 0 for k in (
                "H1_LOCATION", "M15_STRUCTURE", "M5_CONFIRMATION", "RISK_EXECUTION")})
            self.veto_reasons_counter = Counter()
            self.m5_rejection_codes = Counter()
            self.h1_context_counts = Counter()
            self.symbol_counts = Counter()
            self.scores_history = deque(maxlen=self.history_capacity)
            self._score_sum = 0.0
            self._score_count = 0
            self._seen = OrderedDict()
            self._last_flush = 0.0
            self.last_evaluation = None
            self.funnel_total = 0
            self.funnel_stages = Counter()
            self.funnel_actions = Counter()
            self.funnel_reasons = Counter()
            self.funnel_symbols = {}
            self._funnel_seen = OrderedDict()
            self.last_funnel_result = None

    def log_evaluation(self, evaluation_result, symbol, evaluation_id=None):
        """Return False for duplicate IDs in the bounded session cache."""
        with self._lock:
            key = (symbol, evaluation_id) if evaluation_id is not None else None
            if key is not None and key in self._seen:
                self._seen.move_to_end(key)
                return False
            if key is not None:
                self._seen[key] = None
                if len(self._seen) > self.dedup_capacity:
                    self._seen.popitem(last=False)
            status = evaluation_result.get("status", "REJECTED")
            approved = bool(evaluation_result.get("approved", False))
            if status == "REJECTED":
                status = "REJECTED_CRITICAL_VETO"
            if status not in self.status_counts or (status.endswith("APPROVED") != approved):
                status = "REJECTED_OTHER"
            score = evaluation_result.get("final_score")
            try:
                score = float(score)
                if not math.isfinite(score): score = None
            except (ValueError, TypeError):
                score = None
            self.total_evaluations += 1
            self.status_counts[status] += 1
            self.symbol_counts[symbol] += 1
            context = (evaluation_result.get("h1_context") or {}).get("context_type")
            if context:
                self.h1_context_counts[context] += 1
            if score is not None:
                self.scores_history.append(score)
                self._score_sum += score
                self._score_count += 1
            reasons = list(dict.fromkeys(evaluation_result.get("reasons") or []))
            if not approved:
                self.veto_reasons_counter.update(reasons)
                self.m5_rejection_codes.update({code for code in evaluation_result.get("veto_codes", []) if code.startswith("M5_")})
                stages = set()
                for reason in reasons + list(evaluation_result.get("veto_codes") or []):
                    for prefix, stage in (("H1", "H1_LOCATION"), ("M15", "M15_STRUCTURE"),
                                          ("M5", "M5_CONFIRMATION"), ("RISK", "RISK_EXECUTION")):
                        if str(reason).startswith((prefix+":", prefix+"_")):
                            stages.add(stage)
                self.rejection_stages.update(stages)
            self.last_evaluation = dict(symbol=symbol, status=status, score=score,
                                        reasons=reasons, evaluation_id=evaluation_id,
                                        h1_context=evaluation_result.get("h1_context"),
                                        m5_detail=evaluation_result.get("m5_detail"))
            now = time.monotonic()
            if self.total_evaluations == 1 or now-self._last_flush >= 30 or self.total_evaluations % self.report_every == 0:
                self.flush()
                self._last_flush = now
            if self.total_evaluations % self.report_every == 0:
                self.print_telemetry_dashboard()
            return True

    def log_pipeline_result(self, result, evaluation_id=None):
        """Terminal analyzer outcomes, separate from scored candidate statistics."""
        action = str(result.get('action') or 'UNKNOWN')
        stage = {'NO_H1_CONTEXT':'H1', 'NO_M15_SETUP':'M15',
                 'NO_M5_CONFIRMATION':'M5', 'WAITING_M5_AFTER_M15':'M5',
                 'STALE_M5_SIGNAL':'M5', 'ENTRY_LOCATION_BLOCKED':'LOCATION',
                 'DIRECTION_POLICY_BLOCKED':'INSTRUMENT_POLICY'}.get(action)
        if result.get('valid'):
            stage = 'SIGNAL_READY'
        stage = stage or 'OTHER'
        symbol = str(result.get('symbol') or 'UNKNOWN')
        reason = str(result.get('reason') or action)
        if stage == 'H1':
            context = (result.get('h1') or {}).get('context') or {}
            reason = context.get('location_detail') or reason
        # One outcome per symbol/action/setup and five-minute observation bucket.
        # This is an analysis snapshot, not an independent trade opportunity.
        if evaluation_id is None:
            setup = ((result.get('m15') or {}).get('setup') or {})
            evaluation_id = json.dumps([int(time.time()//300), action, result.get('direction'),
                                       str(setup.get('setup_time')), reason])
        key = (symbol, evaluation_id)
        with self._lock:
            if key in self._funnel_seen:
                return False
            self._funnel_seen[key] = None
            if len(self._funnel_seen) > self.dedup_capacity:
                self._funnel_seen.popitem(last=False)
            self.funnel_total += 1
            self.funnel_stages[stage] += 1
            self.funnel_actions[action] += 1
            if stage != 'SIGNAL_READY':
                self.funnel_reasons[reason] += 1
            counts = self.funnel_symbols.setdefault(symbol, Counter())
            counts[stage] += 1
            self.last_funnel_result = dict(symbol=symbol, stage=stage, action=action, reason=reason,
                                          observed_at=datetime.now(timezone.utc).isoformat())
            now = time.monotonic()
            if self.funnel_total == 1 or now-self._last_flush >= 30 or self.funnel_total % self.report_every == 0:
                self.flush()
                self._last_flush = now
            if self.funnel_total % self.report_every == 0:
                self.print_telemetry_dashboard()
            return True

    def get_summary_report(self):
        with self._lock:
            total = max(1, self.total_evaluations)
            strict, adaptive = self.status_counts['STRICT_APPROVED'], self.status_counts['ADAPTIVE_APPROVED']
            return dict(bot_name=self.bot_name, pid=os.getpid(),
                start_time=self.start_time.isoformat(), timestamp=datetime.now(timezone.utc).isoformat(),
                scope="ADAPTIVE_SCORE_CANDIDATES_NOT_EXECUTED_ORDERS",
                pipeline_funnel=dict(scope="TERMINAL_ANALYSIS_SNAPSHOTS_NOT_TRADES",
                    total=self.funnel_total, stage_counts=dict(self.funnel_stages),
                    stage_pct={k:round(100*v/max(1,self.funnel_total),2) for k,v in self.funnel_stages.items()},
                    action_counts=dict(self.funnel_actions),
                    top_3_rejection_reasons=self.funnel_reasons.most_common(3),
                    symbol_stage_counts={k:dict(v) for k,v in self.funnel_symbols.items()},
                    last_result=self.last_funnel_result),
                total_evaluations=self.total_evaluations, status_counts=dict(self.status_counts),
                approval_rate_pct=round(100*(strict+adaptive)/total, 2),
                approval_breakdown=dict(strict_approved=strict, strict_pct=round(100*strict/total,2),
                                       adaptive_approved=adaptive, adaptive_pct=round(100*adaptive/total,2)),
                stage_rejection_counts=dict(self.rejection_stages),
                stage_rejection_pct={key:round(100*self.rejection_stages[stage]/total,2)
                    for key,stage in [('H1_location','H1_LOCATION'),('M15_structure','M15_STRUCTURE'),
                                      ('M5_confirmation','M5_CONFIRMATION'),('risk_execution','RISK_EXECUTION')]},
                average_score=round(self._score_sum/max(1,self._score_count),2),
                scored_evaluations=self._score_count,
                m5_rejection_codes=dict(self.m5_rejection_codes),
                h1_context_counts=dict(self.h1_context_counts),
                top_3_rejection_reasons=self.veto_reasons_counter.most_common(3),
                symbol_counts=dict(self.symbol_counts), last_evaluation=self.last_evaluation)

    def print_telemetry_dashboard(self):
        # ASCII-safe console output through the worker's existing logging handlers.
        logger.info("SMC TELEMETRY | %s", json.dumps(self.get_summary_report(), ensure_ascii=True))

    def flush(self):
        if self.output_dir is None:
            return
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            name = re.sub(r'[^A-Za-z0-9_-]', '_', self.bot_name)[:80] or 'SMC'
            target = self.output_dir / f'{name}_{os.getpid()}.json'
            temporary = target.with_suffix('.tmp')
            with self._lock:
                temporary.write_text(json.dumps(self.get_summary_report(), ensure_ascii=True, indent=2), encoding='utf-8')
                temporary.replace(target)
        except OSError:
            logger.warning("SMC telemetry snapshot unavailable", exc_info=True)


_trackers = {}
_registry_lock = threading.Lock()


def get_telemetry_tracker(bot_name):
    with _registry_lock:
        if bot_name not in _trackers:
            _trackers[bot_name] = SMCTelemetryTracker(bot_name,
                output_dir=Path(__file__).resolve().parents[2] / 'storage' / 'runtime' / 'smc_telemetry')
        return _trackers[bot_name]


def _flush_on_exit():
    for tracker in list(_trackers.values()):
        tracker.flush()


atexit.register(_flush_on_exit)
