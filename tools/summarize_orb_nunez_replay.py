"""Comparable-period tables and static research figures for the audited replay."""
import json
import sys
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.replay_orb_nunez_2y import OUT, SYMBOLS, VARIANTS, metrics, portfolio, report


def main():
    results=json.loads((OUT/'results.json').read_text(encoding='utf-8'))
    frame=pd.read_csv(OUT/'trades.csv')
    starts=[pd.Timestamp(c['first']) for c in results['coverage'].values() if c.get('first')]
    ends=[pd.Timestamp(c['last']) for c in results['coverage'].values() if c.get('last')]
    # One full weekday beyond the last dataset's first day avoids partial sessions.
    start=(max(starts).tz_convert('America/New_York').normalize()+pd.offsets.BDay(1)).date()
    end=min(ends).tz_convert('America/New_York').date()
    common=frame[(frame.session_date>=str(start))&(frame.session_date<=str(end))]
    results['common_period']={'start_session':str(start),'end_session':str(end),'per_symbol':{}}
    rows=[]
    for variant in VARIANTS:
        for symbol in SYMBOLS:
            subset=common[(common.variant==variant)&(common.symbol==symbol)]
            stats=metrics(subset)
            stats['portfolio'],_=portfolio(subset)
            results['common_period']['per_symbol'][variant+'|'+symbol]=stats
            rows.append({'variant':variant,'symbol':symbol,**{k:v for k,v in stats.items() if k!='portfolio'},
                         **stats['portfolio']})
    pd.DataFrame(rows).to_csv(OUT/'common_period_metrics.csv',index=False)
    monthly=[]
    frame['month']=frame.session_date.str[:7]
    for (variant,symbol,month),subset in frame.groupby(['variant','symbol','month']):
        monthly.append({'variant':variant,'symbol':symbol,'month':month,**metrics(subset)})
    pd.DataFrame(monthly).to_csv(OUT/'monthly_metrics.csv',index=False)
    per_mode=[]
    for (variant,symbol,mode),subset in frame.groupby(['variant','symbol','entry_mode']):
        per_mode.append({'variant':variant,'symbol':symbol,'mode':mode,**metrics(subset)})
    pd.DataFrame(per_mode).to_csv(OUT/'entry_mode_metrics.csv',index=False)
    (OUT/'results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    report(results,frame)
    extra=['','## Período común entre los nueve instrumentos','',
           f'Sesiones {start} a {end}. EXPANDED; capital separado de 10.000 por instrumento. '
           'Retornos capitalizados, después del spread y antes de comisión/swap/deslizamiento.','',
           '| Instrumento | Cerradas | R neto | PF | Retorno | DD saldo |',
           '|---|---:|---:|---:|---:|---:|']
    for row in rows:
        if row['variant']!='EXPANDED':
            continue
        pf='—' if row['profit_factor'] is None else f"{row['profit_factor']:.2f}"
        extra.append(f"| {row['symbol']} | {row['closed']} | {row['net_r']:.2f} | {pf} | {row['return_pct']:.2f}% | {row['realized_drawdown_pct']:.2f}% |")
    extra+=['','El resumen aportado distingue proyecciones de amplitud del rango de ratios R. '
            'Este replay conserva los TP ya definidos en el bot: 1R y 2R desde el riesgo de entrada. '
            'No son equivalentes a proyectar 1x/2x la amplitud completa del ORB desde su borde. '
            'La afirmación del 70% no se utiliza como probabilidad garantizada ni como resultado de esta prueba.',
            'Las ventanas Asia/Londres son referencias en reloj NY; no reproducen los cambios de horario '
            'independientes de cada plaza. Los máximos/mínimos diarios corresponden al día NY observado, '
            'que puede tener historia parcial. El contexto HTF se agrega desde M5 completas.',
            'CURRENT significa la configuración predeterminada de ORBConfig y los perfiles presentes '
            'al ejecutar el replay. No reproduce todos los controles de ejecución del worker '
            '(IA, correlación, límite de margen, cuarentena o disponibilidad de lotes).','']
    with (OUT/'INFORME.md').open('a',encoding='utf-8') as f:
        f.write('\n'.join(extra))
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        selected=[r for r in rows if r['variant']=='EXPANDED']
        fig,axes=plt.subplots(2,1,figsize=(11,9),layout='constrained')
        axes[0].barh([r['symbol'] for r in selected],[r['net_r'] for r in selected],
                     color=['#15856e' if r['net_r']>=0 else '#d15555' for r in selected])
        axes[0].axvline(0,color='#444',linewidth=.7)
        axes[0].set_title(f'ORB ampliado: período común {start} a {end}')
        axes[0].set_xlabel('R neto (1R = riesgo total de la oportunidad)')
        for variant in ['CURRENT','EXPANDED','HTF','HTF_SWEEP']:
            events=pd.read_csv(OUT/(variant+'_equity_events.csv'))
            if len(events):
                axes[1].plot(pd.to_datetime(events.time,utc=True),events.balance,label=variant,linewidth=1.4)
        axes[1].set_title('Carteras ilustrativas sobre los datos disponibles; períodos distintos entre activos')
        axes[1].set_ylabel('Saldo realizado, capital inicial 10.000')
        axes[1].legend()
        axes[1].grid(alpha=.2)
        fig.suptitle('REPLAY PARCIAL — cobertura inferior a dos años',fontweight='bold')
        fig.savefig(OUT/'comparison.png',dpi=160)
        plt.close(fig)
    except ImportError:
        pass
    print(json.dumps({'common_period':results['common_period'],'variants':results['variants']},indent=2))


if __name__=='__main__':
    main()
