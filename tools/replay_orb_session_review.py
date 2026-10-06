"""Isolated research replay and review-only AI dataset. No model writes/orders."""
from __future__ import annotations
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from functools import partial
from pathlib import Path
import hashlib
import json
import sys

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import replay_orb_nunez_2y as base

OUT=ROOT/'storage/analysis/orb_session_review'
POLICY={'tp1_r':1.,'tp2_r':2.,'total_risk_pct':1.,'leg_risk_pct':.5,
        'forex_entry_cutoff_ny':'14:00','forex_flat_ny':'16:45',
        'thin_liquidity_ny':'16:00–18:00','spread_max_pips':5.,
        'spread_max_multiple':2.,'spread_max_risk_ratio':.15,
        'baseline_minimum_closed_m5':20,'stable_closed_m5':5,
        'enabled_in_live':False,'training_authorized':False}


def is_forex(symbol):
    return symbol=='EURUSD'


def fx_open(stamp):
    ny=pd.Timestamp(stamp).tz_convert('America/New_York')
    return ny.weekday()<4 or (ny.weekday()==4 and ny.hour<17) or (ny.weekday()==6 and ny.hour>=17)


def spread_context(df,point):
    """M5-only proxy: previous observations, excluding 16–18 NY, never future.

    Five stable M5 observations are deliberately not five 15-second live ticks.
    """
    minute=df.time_ny.dt.hour*60+df.time_ny.dt.minute
    spread=pd.to_numeric(df.spread,errors='coerce')*point
    valid=np.isfinite(spread)&(spread>=0)
    normal_hour=~((minute>=960)&(minute<1080))
    sample=spread.where(valid&normal_hour&(spread<=.0005))
    # Seven calendar days, at least 20 valid closed-M5 observations.
    baseline=sample.set_axis(pd.DatetimeIndex(df.time)).rolling('7D',min_periods=20).median().to_numpy()
    baseline=pd.Series(baseline,index=df.index).shift(1)
    stable=0
    counts=[]
    for i in range(len(df)):
        reset=i==0 or (df.time.iloc[i]-df.time.iloc[i-1])>pd.Timedelta(minutes=5)
        ny=df.time_ny.iloc[i]
        if i and (ny-pd.Timedelta(hours=17)).date()!=(df.time_ny.iloc[i-1]-pd.Timedelta(hours=17)).date():
            reset=True
        if reset:
            stable=0
        normal=bool(valid.iloc[i] and normal_hour.iloc[i] and pd.notna(baseline.iloc[i])
                    and spread.iloc[i]<=.0005 and spread.iloc[i]<=baseline.iloc[i]*2)
        stable=stable+1 if normal else 0
        counts.append(stable)
    return pd.DataFrame({'spread':spread,'baseline':baseline,'stable':counts})


class Simulator:
    def __init__(self,symbol,point):
        self.symbol,self.point=symbol,point
        self.context=None
        self.rejections=Counter()

    def __call__(self,df,first,direction,stop,point):
        if self.context is None:
            self.context=spread_context(df,point) if is_forex(self.symbol) else pd.DataFrame()
        side=1 if direction=='BUY' else -1
        bar=df.iloc[first]
        previous=df.iloc[first-1]
        # The previous CLOSED bar is the entry spread proxy. Entry bar aggregate
        # spread is not exposed as a known-at-entry feature or entry gate.
        spread=float(previous.spread)*point
        if not np.isfinite(spread) or spread<0:
            self.rejections['SPREAD_UNAVAILABLE']+=1
            return None
        entry=float(bar.open)+(spread if side==1 else 0.)
        risk=side*(entry-stop)
        if risk<=0:
            self.rejections['INVALID_EXECUTABLE_SL']+=1
            return None
        baseline=None
        stable=None
        flat_deadline=None
        if is_forex(self.symbol):
            c=self.context.iloc[first-1]
            baseline=float(c.baseline) if pd.notna(c.baseline) else None
            stable=int(c.stable)
            ny=bar.time.tz_convert('America/New_York')
            flat_deadline=pd.Timestamp(f'{ny.date()} 16:45',tz='America/New_York').tz_convert('UTC')
            reason=None
            if not fx_open(bar.time): reason='FOREX_MARKET_CLOSED'
            elif ny.hour>=14 and ny.hour<18: reason='FOREX_CUTOFF_OR_ROLLOVER'
            elif baseline is None: reason='SPREAD_BASELINE_WARMUP'
            elif spread>.0005 or spread>baseline*2: reason='SPREAD_SPIKE'
            elif stable<5: reason='SPREAD_NOT_STABLE_M5_PROXY'
            elif spread/risk>.15: reason='SPREAD_TO_RISK_ABOVE_15_PERCENT'
            if reason:
                self.rejections[reason]+=1
                return None
        tp1,tp2=entry+side*risk,entry+side*2*risk
        rr=[None,None]; exits=[None,None]; reasons=[None,None]
        closed=[False,False]; be=None; ambiguity=0; gaps=0; max_spread=spread
        transition_bars=0; last_time=bar.time
        for b in df.iloc[first:].itertuples():
            s=float(b.spread)*point
            if not np.isfinite(s) or s<0:
                gaps+=1
                continue
            max_spread=max(max_spread,s)
            if b.time-last_time>pd.Timedelta(minutes=5):
                gaps+=1
            last_time=b.time
            ny=b.time.tz_convert('America/New_York')
            transition_bars+=int(16<=ny.hour<18)
            stamp=str(b.time+pd.Timedelta(minutes=5))
            executable_open=float(b.open)+(s if side==-1 else 0.)
            if is_forex(self.symbol) and not fx_open(b.time):
                continue
            if flat_deadline is not None and b.time>=flat_deadline:
                for leg in range(2):
                    if not closed[leg]:
                        rr[leg]=side*(executable_open-entry)/risk
                        exits[leg],reasons[leg],closed[leg]=str(b.time),'FOREX_PRE_ROLLOVER_CLOSE',True
                break
            hi=float(b.high)+(s if side==-1 else 0.)
            lo=float(b.low)+(s if side==-1 else 0.)
            favorable,adverse=(hi,lo) if side==1 else (lo,hi)
            stop_price=be if be is not None else stop
            hit_stop=side*(adverse-stop_price)<=0
            hit1=side*(favorable-tp1)>=0
            hit2=side*(favorable-tp2)>=0
            if hit_stop:
                ambiguity+=int(hit2 if closed[0] else hit1)
                fill=executable_open if side*(executable_open-stop_price)<0 else stop_price
                for leg in range(2):
                    if not closed[leg]:
                        rr[leg]=side*(fill-entry)/risk
                        exits[leg],reasons[leg],closed[leg]=stamp,('BE_SPREAD' if be is not None else 'SL'),True
                break
            if not closed[0] and hit1:
                rr[0],exits[0],reasons[0],closed[0]=1.,stamp,'TP1',True
                pad=max(spread,s)
                desired=entry+side*pad
                if pad>=risk-point:
                    # Do not grant a fictional BE stop above the executable market.
                    if hit2:
                        rr[1],exits[1],reasons[1],closed[1]=2.,stamp,'TP2',True
                    else:
                        price=float(b.close)+(s if side==-1 else 0.)
                        rr[1],exits[1],reasons[1],closed[1]=side*(price-entry)/risk,stamp,'BE_UNPLACEABLE_SPREAD_EXIT',True
                        ambiguity+=1
                else:
                    be=desired
                    if side*(adverse-be)<=0:
                        ambiguity+=1
                        rr[1],exits[1],reasons[1],closed[1]=pad/risk,stamp,'BE_SPREAD',True
            if closed[0] and not closed[1] and hit2:
                rr[1],exits[1],reasons[1],closed[1]=2.,stamp,'TP2',True
            if all(closed): break
        return {'entry_time':str(bar.time),'entry_price':entry,'stop_loss':stop,
                'tp1_price':tp1,'tp2_price':tp2,'be_price':be,'risk_distance':risk,
                'spread_entry':spread,'spread_baseline':baseline,'spread_stable_m5':stable,
                'spread_to_risk_ratio':spread/risk,'spread_pips':spread/.0001 if is_forex(self.symbol) else None,
                'spread_points':spread/point,
                'max_spread_while_open':max_spread,'rollover_m5_bars_while_open':transition_bars,
                'ambiguity_bars':ambiguity,'data_gap_events':gaps,
                'leg1_r':rr[0],'leg2_r':rr[1],'leg1_exit':exits[0],'leg2_exit':exits[1],
                'leg1_reason':reasons[0],'leg2_reason':reasons[1],
                'closed':all(closed),'net_r':.5*sum(rr) if all(closed) else None,
                'planned_runner_rr':2.,'planned_weighted_max_rr':1.5,
                'exit_policy':'SESSION_SPREAD_RESEARCH','fees_status':'COMMISSION_SWAP_SLIPPAGE_UNKNOWN'}


def worker(symbol):
    audit=json.loads((base.OUT/'fetch_audit.json').read_text())
    simulator=Simulator(symbol,audit[symbol]['point'])
    result=base.run_symbol(symbol,simulator)
    result[3].update({'EXECUTION_'+k:v for k,v in simulator.rejections.items()})
    return result


def model_hashes():
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (ROOT/'storage/ai_models').glob('*') if p.is_file()}


def build_package(results,frame,original_models):
    audit=json.loads((base.OUT/'fetch_audit.json').read_text())
    # Explicit units even when rebuilding a completed checkpoint package.
    frame['spread_points']=frame.spread_entry/frame.symbol.map({s:audit[s]['point'] for s in base.SYMBOLS})
    frame['spread_pips']=np.where(frame.symbol=='EURUSD',frame.spread_entry/.0001,np.nan)
    features=['opportunity_id','variant','symbol','session_date','entry_time','direction','entry_mode',
              'h1_state','m15_state','orb_range_high','orb_range_low','entry_price','stop_loss',
              'risk_distance','spread_entry','spread_baseline','spread_stable_m5',
              'spread_to_risk_ratio','spread_pips','spread_points','nearest_liquidity_r',
              'planned_runner_rr','planned_weighted_max_rr']
    frame['opportunity_id']=[hashlib.sha256(f'{r.symbol}|{r.session_date}'.encode()).hexdigest()[:20]
                             for r in frame.itertuples()]
    frame['fold']=np.where(frame.session_date<'2025-10-03','TRAIN',
                         np.where(frame.session_date<'2026-04-03','VALIDATION','HOLDOUT'))
    exit_time=pd.concat([pd.to_datetime(frame.leg1_exit,utc=True),pd.to_datetime(frame.leg2_exit,utc=True)],axis=1).max(axis=1)
    boundary=pd.to_datetime(np.where(frame.fold=='TRAIN','2025-10-03',
                            np.where(frame.fold=='VALIDATION','2026-04-03','2026-10-03')),utc=True)
    eligible=(frame.closed & (frame.ambiguity_bars==0) & (frame.data_gap_events==0)
              & (exit_time<boundary) & frame.net_r.notna() & (frame.net_r.abs()>1e-9))
    frame['label_eligible_research']=eligible
    frame['label_positive']=np.where(eligible,(frame.net_r>0).astype(int),np.nan)
    frame[features+['fold']].to_csv(OUT/'features_review_only.csv',index=False)
    frame[['opportunity_id','variant','symbol','fold','label_eligible_research','label_positive','net_r',
           'leg1_reason','leg2_reason','leg1_r','leg2_r','leg1_exit','leg2_exit',
           'ambiguity_bars','data_gap_events','max_spread_while_open','rollover_m5_bars_while_open']].to_csv(
           OUT/'labels_review_only.csv',index=False)
    frame.to_csv(OUT/'trades.csv',index=False)
    manifest={'package_status':'REVIEW_ONLY_NOT_APPROVED_FOR_TRAINING','requested_start':str(base.START),
              'requested_end_exclusive':str(base.END),'full_two_years_all_symbols':False,
              'feature_schema':'orb-session-research-v1_NOT_meta-features-v5',
              'model_files_unchanged':original_models==model_hashes(),'model_hashes':original_models,
              'policy':POLICY,'sample_counts':frame.groupby(['variant','fold']).size().rename('count').reset_index().to_dict('records'),
              'eligible_labels':int(eligible.sum()),'approval_required_before_training_or_activation':True,
              'features':features,'no_lookahead':'Entry spread uses last closed M5; baseline excludes future observations.',
              'limitations':['M5 spread is an aggregate, not exact bid/ask ticks.','Incomplete two-year history.',
                            'Unknown fees; labels are research only.','Conservative same-bar order.',
                            'No historical broker holiday calendar; actual gaps flagged.',
                            'Forex protection applies to EURUSD, the Forex instrument in the nine-symbol universe.']}
    (OUT/'ai_review_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    results['labels_eligible_research']=int(eligible.sum())
    results['model_files_unchanged']=manifest['model_files_unchanged']
    (OUT/'results.json').write_text(json.dumps(results,indent=2,default=str),encoding='utf-8')
    lines=['# ORB: replay de sesiones y paquete de revisión de IA','',
      '**PARCIAL: faltan históricos desde el 03/10/2024. Paquete solo para revisión, sin entrenamiento ni activación.**','',
      'Universo: oro, plata, WTI, Brent, Nasdaq, Dow, S&P 500, BTCUSD y EURUSD. '
      'Las variantes conservan ruptura/retest, H1/M15 y barrido/MSS definidos en el informe anterior.','',
      'Dos entradas de 0,5% de riesgo cada una. TP1=1R; runner TP2=2R; BE después de TP1 '
      'con colchón del mayor spread entre entrada y vela de TP1. '
      'El máximo ponderado conjunto es 1,5R; el mínimo 1:2 se aplica al runner.','',
      '## Resultados sobre la historia disponible','',
      '| Variante | Cerradas | R neto | PF | Retorno saldo | DD saldo |',
      '|---|---:|---:|---:|---:|---:|']
    for name,stats in results['variants'].items():
        p=stats['portfolio']; pf='—' if stats['profit_factor'] is None else f"{stats['profit_factor']:.2f}"
        lines.append(f"| {name} | {stats['closed']} | {stats['net_r']:.2f} | {pf} | {p['return_pct']:.2f}% | {p['realized_drawdown_pct']:.2f}% |")
    lines+=['','## Spread, cierres y cambio de sesión','',
      '- EURUSD: entradas ORB NY hasta las 14:00; cierre preventivo de piernas abiertas a las 16:45 NY. '
      'Es una variante de investigación, no un cambio del worker actual que tiene rollover_guard desactivado.',
      '- Evita nuevas entradas de viernes 17:00 a domingo 17:00 NY. DST se aplica con America/New_York. '
      'La estrategia conserva su caja NY de 15 minutos; no añade entradas ORB Asia.',
      '- Spread máximo 5 pips, máximo 2 veces la mediana previa de siete días y máximo 15% del riesgo. '
      'El baseline excluye 16:00–18:00 NY. Requiere 20 M5 previas válidas y cinco M5 normales consecutivas. '
      'Esta estabilidad es una aproximación de 25 minutos, no cinco ticks de 15 segundos.',
      '- Las cotizaciones de salida cortas usan ask aproximado (bid OHLC + spread de vela). '
      'La entrada usa el spread de la última M5 cerrada para evitar usar el promedio futuro de la vela de entrada.',
      '- El cierre preventivo busca evitar la liquidez baja del cambio NY/Asia; no equivale a afirmar '
      'que Forex cierra mundialmente cada día. Sin vela ejecutable a la hora prevista se cierra en la '
      'primera cotización posterior disponible y se registra el hueco.',
      '- Si el spread impide colocar BE protegido después de TP1, se simula una salida defensiva del runner '
      'al cierre ejecutable de esa vela y se excluye ese caso del dataset estricto.',
      '- Índices/metales/petróleo conservan SL/TP durante sus cierres. Los saltos entre cotizaciones '
      'se registran y un gap puede provocar pérdida superior al 1% planificado.',
      '- No se inventan spreads históricos intrabar, calendario de festivos, comisiones, swaps ni slippage. '
      'El DD es del saldo realizado, no del equity flotante. El 1% es por oportunidad, no un techo de cartera.','',
      '## Material listo para decidir sobre IA','',
      '- features_review_only.csv: características conocidas al entrar, sin resultados futuros.',
      '- labels_review_only.csv: cierres separados de features; excluye abiertos, ambigüedad, '
      'huecos y salidas que cruzan el límite temporal del fold.',
      '- TRAIN: 03/10/2024–02/10/2025; VALIDATION: 03/10/2025–02/04/2026; '
      'HOLDOUT: 03/04/2026–02/10/2026. TRAIN tiene historia parcial. '
      'El mismo símbolo/día comparte opportunity_id entre variantes: no se debe contar como señales independientes.',
      '- Schema de investigación diferente del modelo activo: requiere mapeo explícito a meta-features-v5 '
      'y evaluación walk-forward antes de cualquier incorporación.',
      f"- Etiquetas elegibles para investigación: {int(eligible.sum())}. Archivos de modelos sin cambios: {manifest['model_files_unchanged']}.",
      '- La decisión de usar, entrenar o activar cambios queda pendiente de tu instrucción explícita. '
      'El paquete no se importa al journal ni a los entrenadores automáticos.','',
      '## Para completar la prueba de dos años','',
      'Faltan M5 reales desde el 03/10/2024 por el límite de 100000 barras observado en MT5. '
      'Solicitar al terminal al menos 500000 barras y exportar/descargar la historia del mismo broker '
      'antes de repetir esta prueba. La cobertura real por símbolo queda en results.json.']
    (OUT/'INFORME.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    before=model_hashes()
    results={'policy':POLICY,'coverage':{},'rejections':{},'variants':{}}
    all_trades=[]
    with ProcessPoolExecutor(max_workers=4) as pool:
        futures=[pool.submit(worker,s) for s in base.SYMBOLS]
        for future in as_completed(futures):
            symbol,cov,trades,rejected=future.result()
            results['coverage'][symbol]=cov
            results['rejections'][symbol]=rejected
            all_trades.extend(trades)
            (OUT/(symbol.replace(' ','_')+'_checkpoint.json')).write_text(
                json.dumps({'coverage':cov,'trades':trades,'rejections':rejected},default=str),encoding='utf-8')
    frame=pd.DataFrame(all_trades).sort_values(['variant','entry_time','symbol']).reset_index(drop=True)
    for variant in base.VARIANTS:
        subset=frame[frame.variant==variant]
        stats=base.metrics(subset)
        stats['portfolio'],events=base.portfolio(subset)
        results['variants'][variant]=stats
        pd.DataFrame(events).to_csv(OUT/(variant+'_equity_events.csv'),index=False)
    build_package(results,frame,before)
    print(json.dumps(results['variants'],indent=2))


if __name__=='__main__': main()
