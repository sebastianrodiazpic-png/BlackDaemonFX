"""Recheck captured offline signals against Step and Boom/Crash quality gates.

This is a diagnostic subset, not a new replay: rejecting a captured position
would free time for other signals, which cannot be inferred by filtering rows.
"""
import json
import sys
from pathlib import Path
from types import SimpleNamespace
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.replay_msnr_confirmations import Provider, config_for, load_frames, VARIANTS, stats
from strategy.malaysian_snr.malaysian_snr_strategy import MalaysianSNRStrategy
from strategy.execution.live_trading_engine import LiveTradingEngine

OUT=ROOT/'storage/analysis/msnr_configuracion_guiada_20261012'
HISTORY=ROOT/'storage/analysis/msnr_v27_m5_reference_20261012'

def main():
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--settings-file',default=str(OUT/'settings_before.json'))
    parser.add_argument('--output-name',default='shared_quality_gates.json')
    args=parser.parse_args()
    if Path(args.output_name).name!=args.output_name:raise ValueError('Output must be one filename')
    manifest=json.loads((HISTORY/'confirmation_history_manifest.json').read_text())
    settings=json.loads(Path(args.settings_file).read_text(encoding='utf-8-sig'))['settings']
    result={'subset_diagnostic_only':True,'not_a_full_execution_replay':True,
        'step_min_adx':25.,'automatic_promotion':False,'symbols':{}}
    for symbol in ('Step Index','Step Index 200','Step Index 400','Step Index 500','Crash 600 Index','Crash 1000 Index'):
        run='steps_v28_30d_current' if symbol.startswith('Step') else 'crash_v28_30d_current'
        path=HISTORY/run/(symbol.replace(' ','_')+'.json')
        if not path.exists():continue
        captured=json.loads(path.read_text())
        row=next(row for row in manifest['symbols'] if row['symbol']==symbol)
        provider=Provider(load_frames(row),row)
        variants={}
        for variant in ('M15','M15_M5'):
            controls={**settings,'m5_confirmation_mode':VARIANTS[variant][0],
                'h4_neutral_fallback_mode':VARIANTS[variant][1], 'additional_symbols':[],
                'asset_modes':{**settings['asset_modes'],symbol:'live'},
                'm5_symbol_modes':({s:('live' if mode=='shadow' else mode) for s,mode in settings['m5_symbol_modes'].items()}
                    if variant=='M15_M5' else {symbol:'off'}),
                'continuation_symbol_modes':{s:('live' if mode=='shadow' else mode) for s,mode in settings['continuation_symbol_modes'].items()}}
            analyzer=MalaysianSNRStrategy(provider,config_for(settings,variant),lambda c=controls:c)
            # No __init__, executor, broker connection, or order method is used.
            engine=object.__new__(LiveTradingEngine)
            engine.config=SimpleNamespace(bot_profile='MALAYSIAN_SNR',step_min_adx=25.)
            engine.provider=provider;engine.malaysian_snr_strategy=analyzer
            checked=[];passing=[]
            for trade in captured['variants'][variant]['trades']:
                provider.now=pd.Timestamp(trade['time'])
                reading=analyzer.analyze_symbol(symbol,provider.now.to_pydatetime())
                signal=reading.get('signal') or {}
                if not reading.get('valid') or signal.get('setup_id')!=trade['setup_id']:
                    gate={'reason':'CAPTURE_RECONSTRUCTION_MISMATCH'}
                else:
                    gate=engine._boom_crash_quality_gate(symbol,signal['direction'],signal,reading)
                    if gate is None:gate=engine._step_quality_gate(symbol,signal,reading)
                checked.append({'time':trade['time'],'setup_id':trade['setup_id'],
                    'signal_adx':signal.get('adx'),'reason':gate.get('reason') if gate else None})
                if gate is None:passing.append(trade)
            variants[variant]={'captured':len(checked),'passing_subset':len(passing),
                'checks':checked,'subset_stats':stats(passing),'passing_records':passing}
        result['symbols'][symbol]=variants
    (OUT/args.output_name).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({s:{v:{'captured':r['captured'],'pass_subset':r['passing_subset'],
        'blocked_reasons':sorted(set(c['reason'] for c in r['checks'] if c['reason']))}
        for v,r in variants.items()} for s,variants in result['symbols'].items()},ensure_ascii=False))

if __name__=='__main__':main()
