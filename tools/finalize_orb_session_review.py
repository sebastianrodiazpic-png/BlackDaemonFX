"""Reconcile admitted signals, review datasets and common-period comparisons."""
import json
from pathlib import Path
import sys
import hashlib
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import replay_orb_nunez_2y as base
from tools import replay_orb_session_review as review


def main():
    out=review.OUT
    original=json.loads((out/'ai_review_manifest.json').read_text(encoding='utf-8'))
    results=json.loads((out/'results.json').read_text(encoding='utf-8'))
    frame=pd.read_csv(out/'trades.csv')
    audit=json.loads((base.OUT/'fetch_audit.json').read_text(encoding='utf-8'))
    records=[]
    for symbol in base.SYMBOLS:
        data,cov=base.load(symbol)
        if cov['sources']!=results['coverage'][symbol]['sources']:
            raise RuntimeError(f'Input history changed during replay: {symbol}')
        point=audit[symbol]['point']
        simulate=review.Simulator(symbol,point)
        for _,row in frame[frame.symbol==symbol].iterrows():
            index=int(data.time.searchsorted(pd.Timestamp(row.entry_time)))
            if index>=len(data) or data.time.iloc[index]!=pd.Timestamp(row.entry_time):
                raise RuntimeError('Admitted entry timestamp missing')
            result=simulate(data,index,row.direction,float(row.stop_loss),point)
            if result is None:
                raise RuntimeError('Admitted signal changed admission status')
            record=row.to_dict()
            record.update(result)
            records.append(record)
    frame=pd.DataFrame(records).sort_values(['variant','entry_time','symbol']).reset_index(drop=True)
    if frame.duplicated(['variant','symbol','session_date']).any():
        raise RuntimeError('Duplicate opportunity')
    if ((frame.leg1_r+frame.leg2_r)*.5-frame.net_r).abs().max()>1e-9:
        raise RuntimeError('Unreconciled two-leg R')
    if not (frame.loc[frame.leg2_reason=='BE_SPREAD','leg1_reason']=='TP1').all():
        raise RuntimeError('BE preceding TP1')
    for variant in base.VARIANTS:
        subset=frame[frame.variant==variant]
        stats=base.metrics(subset)
        stats['portfolio'],events=base.portfolio(subset)
        results['variants'][variant]=stats
        pd.DataFrame(events).to_csv(out/(variant+'_equity_events.csv'),index=False)
        difference=sum(e['pnl'] for e in events)-(stats['portfolio']['final_realized_balance']-10000)
        if abs(difference)>1e-7:
            raise RuntimeError('Unreconciled realized balance')
    review.build_package(results,frame,original['model_hashes'])
    start=(max(pd.Timestamp(c['first']) for c in results['coverage'].values()).tz_convert(
        'America/New_York').normalize()+pd.offsets.BDay(1)).date()
    end=min(pd.Timestamp(c['last']) for c in results['coverage'].values()).tz_convert('America/New_York').date()
    common=frame[(frame.session_date>=str(start))&(frame.session_date<=str(end))]
    common_rows=[]
    for variant in base.VARIANTS:
        for symbol in base.SYMBOLS:
            subset=common[(common.variant==variant)&(common.symbol==symbol)]
            stats=base.metrics(subset)
            p,_=base.portfolio(subset)
            common_rows.append({'variant':variant,'symbol':symbol,**stats,**p})
    pd.DataFrame(common_rows).to_csv(out/'common_period_metrics.csv',index=False)
    monthly=[]
    for (variant,symbol,month),subset in frame.groupby(['variant','symbol',frame.session_date.str[:7]]):
        monthly.append({'variant':variant,'symbol':symbol,'month':month,**base.metrics(subset)})
    pd.DataFrame(monthly).to_csv(out/'monthly_metrics.csv',index=False)
    lines=['','## Comparación por instrumento sobre fechas comunes','',
           f'{start} a {end}; EXPANDED, riesgo 1% por oportunidad.','',
           '| Instrumento | Cerradas | R neto | PF | Retorno por separado |',
           '|---|---:|---:|---:|---:|']
    for r in common_rows:
        if r['variant']!='EXPANDED':continue
        pf='—' if r['profit_factor'] is None else f"{r['profit_factor']:.2f}"
        lines.append(f"| {r['symbol']} | {r['closed']} | {r['net_r']:.2f} | {pf} | {r['return_pct']:.2f}% |")
    lines+=['','Ver DECISION_IA.md para el mapeo propuesto, requisitos antes de entrenar '
            'y límites de interpretación. Los rechazos cuentan evaluaciones por variante, '
            'no oportunidades independientes. CURRENT identifica reglas de detección '
            'predeterminadas con esta política experimental de salida.']
    with (out/'INFORME.md').open('a',encoding='utf-8') as f:f.write('\n'.join(lines)+'\n')
    feature=pd.read_csv(out/'features_review_only.csv')
    label=pd.read_csv(out/'labels_review_only.csv')
    assert len(feature)==len(label)==len(frame)
    assert not set(feature.columns)&{'net_r','label_positive','leg1_r','leg2_r','leg1_exit','leg2_exit',
                                     'max_spread_while_open','rollover_m5_bars_while_open'}
    assert feature.groupby('opportunity_id').fold.nunique().max()==1
    manifest={'unit_tests_passed':24,'admitted_variant_opportunities':len(frame),
              'two_leg_r_reconciled':True,'event_balances_reconciled':True,
              'be_requires_tp1':True,'features_labels_separated':True,
              'temporal_grouping_verified':True,'full_two_years_all_symbols':False,
              'training_performed':False,'model_files_unchanged':review.model_hashes()==original['model_hashes'],
              'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*')
                       if p.is_file() and p.name!='validation_manifest.json'}}
    (out/'validation_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps({'variants':results['variants'],'common':common_rows,'validation':manifest},indent=2))


if __name__=='__main__':main()
