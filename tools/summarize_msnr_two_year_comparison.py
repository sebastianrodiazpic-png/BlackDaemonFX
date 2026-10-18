"""Build reproducible paired metrics and a Spanish report from completed checkpoints."""
from __future__ import annotations
import json, hashlib, sys
from dataclasses import asdict
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from strategy.malaysian_snr.config import MalaysianSNRConfig
from tools.replay_msnr_two_year_comparison import OUT,metrics,read_manifest

def subset_metrics(frame):
    return metrics(frame.to_dict('records'))

def bootstrap_delta(baseline,v21,start,end,replications=2000):
    """Paired weekly blocks of calendar days, preserving simultaneous assets."""
    dates=pd.date_range(start.normalize(),end.normalize(),freq='D',inclusive='left')
    values=[]
    for frame in (baseline,v21):
        if len(frame):
            copy=frame[frame.outcome!='RIGHT_CENSORED'].copy()
            copy['date']=pd.to_datetime(copy.time,utc=True).dt.normalize()
            copy['wins']=(copy.rr>0).astype(int)
            daily=copy.groupby('date').agg(n=('rr','size'),wins=('wins','sum')).reindex(dates,fill_value=0)
            values.append(daily[['n','wins']].to_numpy(float))
        else:
            values.append(np.zeros((len(dates),2)))
    if not all(x[:,0].sum()>0 for x in values):
        return {'delta_ci95_pp':None,'reason':'NO_TRADES_IN_ONE_VERSION'}
    rng=np.random.default_rng(20261011)
    block=7
    starts=rng.integers(0,len(dates)-block+1,size=(replications,int(np.ceil(len(dates)/block))))
    picks=(starts[:,:,None]+np.arange(block)).reshape(replications,-1)[:,:len(dates)]
    sums=[x[picks].sum(axis=1) for x in values]
    ok=(sums[0][:,0]>0)&(sums[1][:,0]>0)
    delta=100*(sums[1][ok,1]/sums[1][ok,0]-sums[0][ok,1]/sums[0][ok,0])
    return {'delta_ci95_pp':np.quantile(delta,[.025,.975]).round(3).tolist(),
            'replications':replications,'block_days':block,'seed':20261011,
            'interpretation':'Descriptive resampling of reused history; no independent future-performance guarantee.'}

def fmt(value,digits=2,suffix=''):
    return '—' if value is None else f'{value:.{digits}f}{suffix}'

def main():
    manifest=read_manifest()
    requested=manifest['requested_symbols']
    checkpoints={}
    for path in (OUT/'results').glob('*.json'):
        if path.name.endswith('.superseded.json'):
            continue
        row=json.loads(path.read_text(encoding='utf-8'))
        checkpoints[row['symbol']]=row
    missing=set(requested)-set(checkpoints)
    if missing:
        raise SystemExit(f'Incomplete replay: {len(missing)} instruments remain')
    meta={r['symbol']:r for r in manifest['symbols']}
    guard_path=OUT/'initial_quote_guard_audit.json'
    quote_guard_audit=json.loads(guard_path.read_text()) if guard_path.exists() else {}
    quote_guard_count=len(quote_guard_audit.get('affected_instruments',[]))
    for name,row in checkpoints.items():
        if row.get('error'):
            continue
        for tf,frame_meta in row['frames'].items():
            if frame_meta['sha256']!=meta[name]['frames'][tf]['sha256']:
                raise SystemExit(f'Checkpoint uses superseded snapshot: {name} {tf}')
    final_manifest=dict(manifest)
    final_manifest.pop('shard',None)
    final_manifest['integrity_check']='All completed checkpoints match the final frozen snapshot hashes.'
    (OUT/'history_manifest.json').write_text(json.dumps(final_manifest,indent=2),encoding='utf-8')
    all_trades=[]
    per_symbol=[]
    errors=[]
    coincident_target_corrections=0
    cfg=MalaysianSNRConfig()
    allowed={s.lower().removesuffix('micro') for s in cfg.allowed_symbols}
    for name in requested:
        row=checkpoints[name]
        if row.get('error'):
            errors.append({'symbol':name,'error':row['error']})
            per_symbol.append({'symbol':name,'error':row['error']})
            continue
        corrected=False
        for variant in row['versions'].values():
            for trade in variant['trades']:
                if trade.get('simulation_correction'):
                    coincident_target_corrections+=1
                if trade['outcome']=='TP1+BE_AMBIGUOUS' and trade['tp1']==trade['tp2']:
                    sign=1 if trade['direction']=='BUY' else -1
                    risk=abs(trade['entry']-trade['stop'])
                    trade['original_simulation_rr']=trade['rr']
                    trade['original_simulation_outcome']=trade['outcome']
                    trade['rr']=.5*(sign*(trade['tp1']-trade['entry'])/risk+sign*(trade['tp2']-trade['entry'])/risk)
                    trade['outcome']='TP2'
                    trade['simulation_correction']='COINCIDENT_TARGETS_FILL_TOGETHER; exit bar and entry decisions unchanged'
                    coincident_target_corrections+=1
                    corrected=True
            variant['metrics']=metrics(variant['trades'])
        if corrected:
            checkpoint=OUT/'results'/f'{name.replace(" ","_")}.json'
            checkpoint.write_text(json.dumps(row,indent=2),encoding='utf-8')
        item={'symbol':name,'full_two_years':row['full_two_year_start'],'available_start':row['available_start'],
              'live_allowlist':name.lower().removesuffix('micro') in allowed,'is_micro':name.endswith('micro'),
              'synthetic':any(word in name.upper() for word in ('BOOM','CRASH','STEP','JUMP','VOL','SPOT')),
              'path':meta[name].get('path')}
        for label,value in row['versions'].items():
            item.update({f'{label}_{k}':v for k,v in value['metrics'].items() if k not in ('expectancy_ci95','win_ci95_wilson')})
            item[f'{label}_win_ci95']=value['metrics']['win_ci95_wilson']
            for trade in value['trades']:
                all_trades.append({**trade,'variant':label,**{k:item[k] for k in ('full_two_years','live_allowlist','is_micro','synthetic')}})
        item['win_delta_pp']=(item['v21_win_pct']-item['baseline_win_pct']) if item['v21_win_pct'] is not None and item['baseline_win_pct'] is not None else None
        item['expectancy_delta_r']=(item['v21_expectancy_r']-item['baseline_expectancy_r']) if item['v21_expectancy_r'] is not None and item['baseline_expectancy_r'] is not None else None
        per_symbol.append(item)
    df=pd.DataFrame(all_trades)
    if df.empty:
        df=pd.DataFrame(columns=['symbol','time','exit_time','rr','outcome','variant','full_two_years','live_allowlist','is_micro','synthetic'])
    df.to_csv(OUT/'trades.csv',index=False)
    pd.DataFrame(per_symbol).to_csv(OUT/'per_symbol.csv',index=False)
    start,end=pd.Timestamp(manifest['audit_start']),pd.Timestamp(manifest['audit_end'])
    scopes={
        'all_available_history':pd.Series(True,index=df.index),
        'full_two_years':df.full_two_years.astype(bool),
        'full_two_years_unique_contracts':df.full_two_years.astype(bool)&~df.is_micro.astype(bool),
        'full_two_years_unique_contracts_no_timeout':df.full_two_years.astype(bool)&~df.is_micro.astype(bool)&~df.outcome.isin(['TIMEOUT','RIGHT_CENSORED','NO_DATA']),
        'partial_history':~df.full_two_years.astype(bool),
        'live_allowlist_all_history':df.live_allowlist.astype(bool),
        'live_allowlist_full_two_years':df.live_allowlist.astype(bool)&df.full_two_years.astype(bool),
        'live_allowlist_full_two_years_unique_contracts':df.live_allowlist.astype(bool)&df.full_two_years.astype(bool)&~df.is_micro.astype(bool),
        'live_allowlist_unique_contracts_all_history':df.live_allowlist.astype(bool)&~df.is_micro.astype(bool),
        'synthetics_full_two_years':df.synthetic.astype(bool)&df.full_two_years.astype(bool),
        'other_full_two_years':~df.synthetic.astype(bool)&df.full_two_years.astype(bool),
    }
    scope_results={}
    for name,mask in scopes.items():
        group=df[mask]
        a,b=(group[group.variant==label] for label in ('baseline','v21'))
        ma,mb=subset_metrics(a),subset_metrics(b)
        scope_results[name]={'baseline':ma,'v21':mb,
                             'win_delta_pp':round(mb['win_pct']-ma['win_pct'],3) if ma['win_pct'] is not None and mb['win_pct'] is not None else None,
                             'paired_weekly_bootstrap':bootstrap_delta(a,b,start,end)}
    periods=[]
    for lower,upper,label in ((start,start+pd.DateOffset(years=1),'Primer año'),(start+pd.DateOffset(years=1),end,'Segundo año')):
        for scope in ('full_two_years_unique_contracts','live_allowlist_full_two_years_unique_contracts'):
            group=df[scopes[scope]]
            timestamps=pd.to_datetime(group.time,utc=True)
            group=group[(timestamps>=lower)&(timestamps<upper)]
            for variant in ('baseline','v21'):
                periods.append({'period':label,'scope':scope,'variant':variant,**subset_metrics(group[group.variant==variant])})
    quarterly=[]
    if len(df):
        calendar=pd.to_datetime(df.time,utc=True).dt.tz_localize(None).dt.to_period('Q').astype(str)
        for (variant,quarter),group in df.assign(quarter=calendar).groupby(['variant','quarter']):
            quarterly.append({'variant':variant,'quarter':quarter,**subset_metrics(group)})
    pd.DataFrame(quarterly).to_csv(OUT/'quarterly.csv',index=False)
    current_df=df[df.variant=='v21'].copy()
    detail={}
    if len(current_df):
        lag=(pd.to_datetime(current_df.time,utc=True)-pd.to_datetime(current_df.structure_closed_at,utc=True)).dt.total_seconds()/60
        detail['retention_late_60_to_90_minutes']=subset_metrics(current_df[lag>45])
        detail['early_15_to_45_minutes']=subset_metrics(current_df[lag<=45])
        detail['by_trigger']={str(trigger):subset_metrics(group) for trigger,group in current_df.groupby('trigger')}
        detail['by_scenario']={str(scenario):subset_metrics(group) for scenario,group in current_df.groupby('scenario')}
        detail['outcomes']=current_df.outcome.value_counts().to_dict()
        resolved=current_df[~current_df.outcome.isin(['TIMEOUT','RIGHT_CENSORED','NO_DATA'])]
        detail['resolved_without_timeout_marking']=subset_metrics(resolved)
        detail['cost_sensitivity']={str(cost):subset_metrics(current_df.assign(rr=current_df.rr-cost)) for cost in (0.05,0.10)}
    files=('strategy/malaysian_snr/config.py','strategy/malaysian_snr/validation.py','strategy/malaysian_snr/malaysian_snr_strategy.py','tools/replay_msnr_two_year_comparison.py')
    hashes={path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in files}
    legacy_refs=[]
    for filename in ('replay_malaysian_snr_2y_metrics.json','comparison_malaysian_snr_metrics.json','msnr_2year_audit/audit_metrics.json'):
        path=ROOT/'storage/analysis'/filename
        if path.exists():
            legacy_refs.append({'file':filename,'metrics':json.loads(path.read_text(encoding='utf-8-sig')),'comparable':False})
    result={'start':str(start),'end':str(end),'days':(end-start).days,'requested_instruments':len(requested),
            'evaluated_instruments':len(requested)-len(errors),'full_two_year_instruments':sum(r.get('full_two_years',False) for r in per_symbol),
            'partial_history_instruments':sum('error' not in r and not r.get('full_two_years') for r in per_symbol),
            'full_two_year_unique_contracts':sum(r.get('full_two_years',False) and not r.get('is_micro',False) for r in per_symbol),
            'live_allowlist_full_two_year_unique_contracts':sum(r.get('full_two_years',False) and r.get('live_allowlist',False) and not r.get('is_micro',False) for r in per_symbol),
            'errors':errors,'configuration':asdict(cfg),'audit_allowlist_override':[],
            'source_hashes':hashes,'scopes':scope_results,'periods':periods,'v21_details':detail,'legacy_references':legacy_refs,
            'coincident_target_corrections':coincident_target_corrections,
            'initial_quote_guard_audit':quote_guard_audit,
            'limitations':['Same historical data used in previous analyses; not an untouched forward test.',
                           'Visible/configured terminal universe, not all unmonitored broker listings.',
                           'Bid OHLC and historical spread, conservative same-bar stop priority; no ticks, slippage, commission, swaps, lot rounding, broker minimum stop-distance validation or portfolio limits.',
                           'Both versions use a common 200-M15-bar holding cap; TIMEOUT is marked to market. Right-censored trades excluded from win rate.',
                           'Common replay reevaluation starts at the M15 close following an exit, potentially later than the live worker.',
                           'Native broker D1 used. Current live defaults keep continuation disabled, so graded freshness of scenario 1 is not independently tested.',
                           'Micro contracts are separate tested instruments; a second aggregate excludes them to avoid duplicate exposure.',
                           'Wilson intervals assume independent outcomes; weekly bootstrap is descriptive and does not correct previous selection or parameter reuse.']}
    (OUT/'metrics.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    titles={'all_available_history':'Todos los históricos, incluidos parciales','full_two_years':'Dos años completos',
            'full_two_years_unique_contracts':'Dos años, excluyendo contratos micro','partial_history':'Sólo históricos parciales',
            'full_two_years_unique_contracts_no_timeout':'Dos años sin micro: sólo salidas SL/TP del mismo replay',
            'live_allowlist_all_history':'Selección actual, incluidos parciales','live_allowlist_full_two_years':'Selección actual con dos años',
            'live_allowlist_full_two_years_unique_contracts':'Selección actual con dos años, sin contratos micro',
            'live_allowlist_unique_contracts_all_history':'Selección actual sin micro, incluidos parciales',
            'synthetics_full_two_years':'Sintéticos con dos años','other_full_two_years':'Otros instrumentos con dos años'}
    principal=scope_results['full_two_years_unique_contracts']
    delta=principal['win_delta_pp']
    verdict=('supera' if delta>0 else 'mantiene' if delta==0 else 'no mantiene') if delta is not None else 'no permite comparar'
    delta_interval=principal['paired_weekly_bootstrap'].get('delta_ci95_pp')
    uncertainty=('El intervalo descriptivo de la diferencia incluye cero: no se acredita una mejora estable del WinRate.'
                 if delta_interval and delta_interval[0]<=0<=delta_interval[1]
                 else 'El resultado reutiliza histórico previamente analizado y no sustituye una validación independiente.')
    lines=['# Malaysian SNR: replay comparativo de dos años','',
           f'Periodo de señales: **{start.date()} a {end.date()}**, {result["days"]} días. Datos nativos del terminal, con calentamiento desde agosto de 2024.',
           f'Universo: {len(requested)} instrumentos visibles/configurados y del replay anterior; {result["evaluated_instruments"]} evaluados, {result["full_two_year_instruments"]} con historia desde el inicio y {result["partial_history_instruments"]} parciales. {len(errors)} no disponibles.',
           '',f'**En este replay, v2.1 {verdict} el WinRate de v2.0 en el grupo con dos años completos, excluyendo contratos micro.** Diferencia: {fmt(delta,2," puntos porcentuales")}. Este resultado histórico no acredita un WinRate futuro.',
           uncertainty,
           f'La selección actual sin contratos micro pasa de {fmt(scope_results["live_allowlist_full_two_years_unique_contracts"]["baseline"]["win_pct"],2,"%")} a {fmt(scope_results["live_allowlist_full_two_years_unique_contracts"]["v21"]["win_pct"],2,"%")} en los activos con dos años. El agregado principal todavía tiene expectativa {fmt(principal["v21"]["expectancy_r"],4)} R/trade y factor de beneficio {fmt(principal["v21"]["profit_factor"],3)}.',
           '', '| Universo | Operaciones anterior / v2.1 | WinRate anterior | WinRate v2.1 | Diferencia pp | R/trade v2.1 | Factor beneficio v2.1 |',
           '|---|---:|---:|---:|---:|---:|---:|']
    for name,value in scope_results.items():
        a,b=value['baseline'],value['v21']
        lines.append(f'| {titles[name]} | {a["trades"]} / {b["trades"]} | {fmt(a["win_pct"],2,"%")} | {fmt(b["win_pct"],2,"%")} | {fmt(value["win_delta_pp"])} | {fmt(b["expectancy_r"],4)} | {fmt(b["profit_factor"],3)} |')
    lines += ['', '## Interpretación y referencia histórica', '',
              f'Intervalo Wilson 95% del WinRate v2.1, grupo con dos años: {principal["v21"]["win_ci95_wilson"]}. Intervalo descriptivo de la diferencia con bloques semanales: {principal["paired_weekly_bootstrap"].get("delta_ci95_pp")} pp.',
              f'R total v2.1: {principal["v21"]["total_r"]}; drawdown máximo agregado: {principal["v21"]["max_drawdown_r"]} R. El agregado suma riesgos unitarios de pruebas por símbolo: no representa una cuenta con límites de cartera ni rentabilidad en dólares.',
              'Los estimados anteriores de 42,1% para activos ACTIVE, 34,43% o 31,91% proceden de otros detectores, universos o simulaciones. El replay de 207.520 trades fue señalado por anticipar información futura. Se conservan como referencias, pero no sirven como comparación controlada de estos cambios.',
              'El escenario 1 de continuación sigue deshabilitado en los parámetros actuales. Este experimento evalúa el retest persistente, los dos gatillos, obstáculos vigentes, invalidación y deduplicación para QM/fractal; no demuestra el efecto aislado de admitir un nivel probado una vez.',
              '', '## Estabilidad por año', '', '| Periodo | Universo | Versión | Operaciones | WinRate | R/trade |', '|---|---|---|---:|---:|---:|']
    for p in periods:
        lines.append(f'| {p["period"]} | {titles[p["scope"]]} | {p["variant"]} | {p["trades"]} | {fmt(p["win_pct"],2,"%")} | {fmt(p["expectancy_r"],4)} |')
    lines += ['', '## Desglose de entradas v2.1', '', 'Estos subgrupos describen operaciones realizadas; no aíslan el efecto causal de cada cambio.']
    for key,title in (('retention_late_60_to_90_minutes','Entradas recuperadas entre 60 y 90 minutos'),('early_15_to_45_minutes','Entradas entre 15 y 45 minutos')):
        value=detail.get(key,{})
        lines.append(f'- {title}: {value.get("trades",0)} operaciones, WinRate {fmt(value.get("win_pct"),2,"%")}, expectativa {fmt(value.get("expectancy_r"),4)} R/trade.')
    for trigger,value in detail.get('by_trigger',{}).items():
        lines.append(f'- {trigger}: {value["trades"]} operaciones, WinRate {fmt(value["win_pct"],2,"%")}, expectativa {fmt(value["expectancy_r"],4)} R/trade.')
    lines += ['', '## Resultado por instrumento', '', '| Instrumento | Cobertura | Trades anterior / v2.1 | WR anterior | WR v2.1 | R/trade v2.1 | R total v2.1 |', '|---|---|---:|---:|---:|---:|---:|']
    for row in per_symbol:
        if 'error' in row:
            lines.append(f'| {row["symbol"]} | No disponible | — | — | — | — | — |')
        else:
            coverage='Dos años' if row['full_two_years'] else f'Parcial desde {row["available_start"][:10]}'
            lines.append(f'| {row["symbol"]} | {coverage} | {row["baseline_trades"]} / {row["v21_trades"]} | {fmt(row["baseline_win_pct"],2,"%")} | {fmt(row["v21_win_pct"],2,"%")} | {fmt(row["v21_expectancy_r"],4)} | {fmt(row["v21_total_r"],3)} |')
    lines += ['', '## Método y límites', '',
              'Se comparan el código previo conservado desde HEAD y la versión msnr-v2.1-persistent-retest. Ambos observan exclusivamente velas cerradas. La aceleración memoriza prefijos inmutables y descarta horarios sin patrones posibles; se verifica contra el detector sin acelerar.',
              'Se abre en la siguiente vela M15 con spread histórico cuando existe; BUY entra a ask, SELL sale a ask. Se mantiene el SL estructural, se recalculan los objetivos desde el precio de entrada y se verifica el contexto de ejecución de v2.1. TP1=2R y distribución 50/50; la corredora pasa a BE con 1,5 spreads de buffer. En ambigüedad intravela se prioriza el stop. Una operación activa por instrumento.',
              'Se aplica a ambas versiones el límite común del simulador de 200 velas M15 (50 horas de cotización). Las salidas TIMEOUT se valoran a mercado; las abiertas al final del histórico quedan censuradas y no cuentan en WinRate. metrics.json incluye el resultado sólo de las operaciones resueltas sin TIMEOUT.',
              'El simulador vuelve a evaluar en el cierre M15 posterior al cierre de una posición; el worker en vivo puede reevaluar antes. Es una comparación controlada bajo un modelo común de ejecución, no una reproducción de cada decisión del broker.',
              f'Antes de abrir, se rechaza un stop ya cruzado por Bid en BUY o Ask en SELL. Esta validación utiliza el lado de cotización correspondiente al cierre de la posición, conforme a las [reglas de MetaTrader](https://www.mql5.com/en/articles/2555). Se reejecutaron {quote_guard_count} instrumentos afectados; sus resultados anteriores quedan archivados para trazabilidad.',
              'No se simulan ticks, latencia, slippage, comisión, swaps, lote mínimo, redondeo, validación de distancia mínima de stops del broker ni restricciones de cartera. La sensibilidad de costos en metrics.json resta 0,05R/0,10R a las operaciones realizadas; no es una reoptimización ni un replay de decisiones diferente.',
              f'Corrección común del simulador: {coincident_target_corrections} operaciones con TP1 y TP2 exactamente iguales se cierran juntas en TP2, antes de mover BE. Sólo corrige R/etiqueta, sin alterar entradas, fecha de salida, WinRate ni disponibilidad para otra operación.',
              'El grupo que excluye TIMEOUT describe un subconjunto de las operaciones del mismo replay: no es un nuevo replay con posiciones mantenidas indefinidamente, y no recalcula las entradas posteriores a esas salidas.',
              'No se modificaron parámetros del bot en vivo, su selección de activos ni modelos IA; no se enviaron órdenes. Los históricos parciales no se extrapolan a dos años. La selección de mejores activos después de ver este resultado requeriría una validación posterior independiente.',
              '', 'Archivos: `per_symbol.csv`, `trades.csv`, `quarterly.csv`, `metrics.json`, `history_manifest.json` y snapshots de velas con hash SHA-256.']
    report=OUT/'report.md'
    report.write_text('\n'.join(lines),encoding='utf-8')
    (ROOT/'MSNR_REPLAY_DOS_ANOS_20261011.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('requested_instruments','evaluated_instruments','full_two_year_instruments','partial_history_instruments','errors','scopes','v21_details')},ensure_ascii=True),flush=True)

if __name__=='__main__':
    main()
