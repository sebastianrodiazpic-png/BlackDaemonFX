"""Calendar performance of completed logical operations, in Santiago time."""
import math
from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo


def build_period_performance(records, strategy_name, metadata, now=None):
    current = now or datetime.now(ZoneInfo("America/Santiago"))
    current = current.astimezone(ZoneInfo("America/Santiago"))
    groups={};seen=set();excluded=0
    for row in records:
        identity=row.get('id')
        if identity is not None:
            if identity in seen:continue
            seen.add(identity)
        meta=metadata(row)
        key=(row.get('source'),row.get('broker'),row.get('instrument'),strategy_name(row),
             str(meta.get('parent_execution_key') or row.get('execution_key') or identity))
        groups.setdefault(key,[]).append(row)
    operations=[]
    for key,rows in groups.items():
        if any(str(r.get('status')).upper()!='CLOSED' for r in rows):continue
        try:
            pnl=[float(r['net_pnl']) for r in rows]
            if not all(math.isfinite(p) for p in pnl):raise ValueError()
            dates=[]
            for r in rows:
                t=datetime.fromisoformat(str(r['exit_time']).replace('Z','+00:00'))
                if t.tzinfo is None:t=t.replace(tzinfo=ZoneInfo('UTC'))
                dates.append(t.astimezone(ZoneInfo('America/Santiago')))
            end=max(dates)
            operations.append(dict(year=end.year,month=end.month,strategy=key[3],asset=key[2] or 'SIN_ACTIVO',net_pnl=sum(pnl)))
        except (KeyError,TypeError,ValueError):excluded+=1
    return dict(timezone='America/Santiago',basis='Cierre final de operación; TP1 y runner agrupados',
                current_year=current.year, current_month=current.month,
                years=list(range(max([current.year]+[o['year'] for o in operations]),
                                 min([current.year]+[o['year'] for o in operations])-1,-1)),operations=operations,
                excluded_incomplete_data=excluded)
