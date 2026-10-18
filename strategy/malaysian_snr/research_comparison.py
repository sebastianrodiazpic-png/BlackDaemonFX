"""Research acceptance checks. Never authorize orders or model promotion."""
import math


def compare_samples(baseline, candidate, settings, *, same_window_and_feed):
    minimum = settings['research_min_resolved_trades']
    reasons = []
    if not same_window_and_feed:
        reasons.append('DIFFERENT_WINDOW_OR_FEED')
    eligible = lambda rows: [r for r in rows if r.get('rr') is not None
        and not r.get('ambiguous') and math.isfinite(float(r['rr']))]
    base, trial = eligible(baseline), eligible(candidate)
    frequency = len(candidate)/len(baseline) if baseline else None
    if frequency is None:
        reasons.append('MISSING_BASELINE_FREQUENCY')
    elif frequency<settings['research_min_frequency_ratio']:
        reasons.append('FREQUENCY_LOSS_EXCEEDS_LIMIT')
    if len(base)<minimum or len(trial)<minimum:
        reasons.append('INSUFFICIENT_RESOLVED_SAMPLE')
    if len(base)!=len(baseline) or len(trial)!=len(candidate):
        reasons.append('INCOMPLETE_OR_AMBIGUOUS_OUTCOMES')
    base_win_rate=100*sum(float(r['rr'])>0 for r in base)/len(base) if base else None
    trial_win_rate=100*sum(float(r['rr'])>0 for r in trial)/len(trial) if trial else None
    win_rate_delta=trial_win_rate-base_win_rate if base_win_rate is not None and trial_win_rate is not None else None
    if win_rate_delta is None:
        reasons.append('MISSING_COMPARABLE_WIN_RATE')
    elif win_rate_delta+1e-10<settings.get('research_min_win_rate_improvement_pp',0.):
        reasons.append('WIN_RATE_IMPROVEMENT_BELOW_TARGET')
    base_total=sum(float(r['rr']) for r in base)
    trial_total=sum(float(r['rr']) for r in trial)
    if not trial or trial_total/len(trial)<=0:
        reasons.append('NON_POSITIVE_EXPECTANCY')
    if trial_total<=base_total:
        reasons.append('NO_NET_REWARD_IMPROVEMENT')
    return {'baseline_entries':len(baseline), 'candidate_entries':len(candidate),
        'baseline_resolved':len(base),'candidate_resolved':len(trial),
        'baseline_win_rate_pct':base_win_rate,'candidate_win_rate_pct':trial_win_rate,
        'win_rate_improvement_pp':win_rate_delta,'required_win_rate_improvement_pp':settings.get('research_min_win_rate_improvement_pp',0.),
        'frequency_preserved':frequency,'baseline_total_r':base_total,'candidate_total_r':trial_total,
        'candidate_expectancy_r':trial_total/len(trial) if trial else None,
        'research_checks_passed':not reasons,'reasons':reasons,
        'automatic_promotion':False, 'note':'Comparación de investigación; requiere costes y validación temporal independiente.'}
