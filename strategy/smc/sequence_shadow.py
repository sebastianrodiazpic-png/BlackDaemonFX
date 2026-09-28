"""Bounded same-setup comparisons. No live decision is modified."""
import pandas as pd


def compare(data, setup, direction, index, critical, displacement=False):
    start=pd.to_datetime(setup.get('setup_time',setup.get('time')),utc=True,errors='coerce')
    ob_low=float(setup.get('ob_low',0));ob_high=float(setup.get('ob_high',0))
    time=pd.to_datetime(data.iloc[index]['time'],utc=True)
    report={'mode':'SHADOW_ONLY','setup_time':None if pd.isna(start) else start.isoformat(),
            'confirmation_time':time.isoformat(),'ob_low':ob_low,'ob_high':ob_high,
            'direction':direction,'max_window_bars':3,'baseline_critical_failures':list(critical),'variants':{}}
    if pd.isna(start) or ob_high<=ob_low:return report
    window=data.iloc[max(0,index-2):index+1].copy()
    stamps=pd.to_datetime(window.time,utc=True)
    window=window[(stamps>=start)&(stamps>=time-pd.Timedelta(minutes=10))]
    keys=('bos_bullish','choch_bullish') if direction=='long' else ('bos_bearish','choch_bearish')
    respected=bool((window.close>=ob_low).all() if direction=='long' else (window.close<=ob_high).all())
    events=[str(row['time']) for _,row in window.iterrows() if any(pd.notna(row.get(k)) and bool(row.get(k)) for k in keys)]
    for name,remove in [('STRUCTURE_WITHIN_3_BARS',{'M5_BOS_CHOCH_REQUIRED'}),
                        ('STRUCTURE_AND_DISPLACEMENT_WITHIN_3_BARS',{'M5_BOS_CHOCH_REQUIRED','DISPLACEMENT_REQUIRED_FOR_LIVE_ENTRY'})]:
        can_structure=bool(events and respected)
        # Only evaluated displacement evidence supplied by the caller, never an invented score.
        resolved=set()
        if can_structure: resolved.add('M5_BOS_CHOCH_REQUIRED')
        if displacement and respected:resolved.add('DISPLACEMENT_REQUIRED_FOR_LIVE_ENTRY')
        resolved &= remove
        report['variants'][name]={'resolved_failures':sorted(set(critical)&resolved),
            'remaining_critical_failures':[f for f in critical if f not in resolved],
            'structure_event_times':events,'ob_respected':respected,
            'entry_authorized':False}
    return report
