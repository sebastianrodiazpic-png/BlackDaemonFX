"""Compare four declared DEMO profiles. Never apply settings or send orders."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.replay_msnr_confirmations import stats
from strategy.malaysian_snr.research_comparison import compare_samples

OUT=ROOT/'storage/analysis/msnr_configuracion_guiada_20261012'
STEP=('Step Index','Step Index 200','Step Index 400','Step Index 500')
CRASH=('Crash 600 Index','Crash 1000 Index')
PROFILES={
    'expansion_crash':{**{s:'live' for s in STEP},**{s:'live' for s in CRASH}},
    'selective_steps_and_crash':{**{s:'live' for s in STEP[:2]},**{s:'shadow' for s in STEP[2:]},**{s:'live' for s in CRASH}},
    'selective_steps_crash600':{**{s:'live' for s in STEP[:2]},**{s:'shadow' for s in STEP[2:]},CRASH[0]:'live',CRASH[1]:'shadow'},
    'selective_steps_crash1000':{**{s:'live' for s in STEP[:2]},**{s:'shadow' for s in STEP[2:]},CRASH[0]:'shadow',CRASH[1]:'live'},
}

def main():
    before=json.loads((OUT/'settings_before.json').read_text(encoding='utf-8-sig'))['settings']
    rows={}
    for symbol in (*STEP,*CRASH):
        run='steps_v28_30d_current' if symbol in STEP else 'crash_v28_30d_current'
        row=json.loads((ROOT/f'storage/analysis/msnr_v27_m5_reference_20261012/{run}/{symbol.replace(" ","_")}.json').read_text())
        if row.get('error'):raise ValueError(row['error'])
        rows[symbol]=row
    def records(modes):
        return [trade for symbol,row in rows.items() for trade in row['variants']['M15_M5' if modes.get(symbol,before['m5_confirmation_mode'])=='live' else 'M15']['trades']]
    baseline=records(before['m5_symbol_modes'])
    targets={**before,'research_min_frequency_ratio':1.05,'research_min_win_rate_improvement_pp':1.,'research_min_resolved_trades':50}
    result={'reference':'Actual version 12: four Step M5 live; Crash M15 live with M5 shadow',
        'period':'2026-09-11 / 2026-10-11 UTC','selection_is_in_sample':True,
        'independent_validation':False,'automatic_promotion':False,
        'baseline':stats(baseline),'baseline_entries':len(baseline),'profiles':{}}
    for name,modes in PROFILES.items():
        sample=records(modes)
        check=compare_samples(baseline,sample,targets,same_window_and_feed=True)
        arithmetic=(check['frequency_preserved'] is not None and check['frequency_preserved']>=1.05
            and check['win_rate_improvement_pp'] is not None and check['win_rate_improvement_pp']>=1.
            and check['candidate_total_r']>check['baseline_total_r']
            and check['candidate_expectancy_r'] is not None and check['candidate_expectancy_r']>0)
        result['profiles'][name]={'m5_modes':modes,'entries':len(sample),'metrics':stats(sample),
            'comparison':check,'arithmetic_objectives_met':arithmetic,'production_validated':False}
    (OUT/'configuration_candidates.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'baseline':result['baseline']['conservative_ohlc'],'baseline_entries':len(baseline),
        'profiles':{name:{'entries':row['entries'],'metrics':row['metrics']['conservative_ohlc'],
            'arithmetic_goals':row['arithmetic_objectives_met'],'reasons':row['comparison']['reasons']}
            for name,row in result['profiles'].items()}},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
