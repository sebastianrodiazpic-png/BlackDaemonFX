from dashboard.period_performance import build_period_performance

def test_grouped_closure_month_and_incomplete_operations():
    def row(i,parent,status,pnl,date):
        return dict(id=i,source='DEMO',broker='MT5',instrument='GOLD',strategy='ORB',parent=parent,status=status,net_pnl=pnl,exit_time=date)
    rows=[row(1,'a','CLOSED',10,'2026-08-31T20:00:00Z'),row(2,'a','CLOSED',-3,'2026-09-02T20:00:00Z'),
          row(3,'b','CLOSED',8,'2026-09-03T20:00:00Z'),row(4,'b','OPEN',None,None),
          row(5,'c','CLOSED',float('nan'),'2026-09-03T20:00:00Z')]
    r=build_period_performance(rows+[rows[0]],lambda r:r['strategy'],lambda r:{'parent_execution_key':r['parent']})
    assert r['operations']==[dict(year=2026,month=9,strategy='ORB',asset='GOLD',net_pnl=7)]
    assert r['excluded_incomplete_data']==1

def test_timezone_year_boundary_and_empty():
    rows=[dict(id=1,status='CLOSED',net_pnl=3,exit_time='2026-01-01T01:00:00Z',instrument='EURUSD')]
    r=build_period_performance(rows,lambda r:'SMC',lambda r:{})
    assert r['operations'][0]['year']==2025
    assert r['operations'][0]['month']==12
    assert build_period_performance([],lambda r:'SMC',lambda r:{})['years']

def test_panel_on_all_pages():
    from dashboard.account_page import ACCOUNT_HTML
    from dashboard.realtime_dashboard import _HTML, _INSTRUMENTS_HTML
    from dashboard.performance_page import PERFORMANCE_HTML

    # El panel vive en su propia página dedicada /performance
    assert PERFORMANCE_HTML.count('id="periodPerformance"') == 1
    assert 'perfYear' in PERFORMANCE_HTML and 'perfMonth' in PERFORMANCE_HTML and 'perfAssets' in PERFORMANCE_HTML
    # Y fue retirado del dashboard principal y de /account para mantener esas vistas enfocadas en la operativa en vivo
    assert 'id="periodPerformance"' not in _HTML
    assert 'id="periodPerformance"' not in ACCOUNT_HTML


def test_current_month_even_without_trades_and_year_rollover():
    from datetime import datetime, timezone
    r=build_period_performance([],lambda r:'SMC',lambda r:{},now=datetime(2027,1,1,1,tzinfo=timezone.utc))
    assert (r['current_year'],r['current_month'])==(2026,12)
    r=build_period_performance([],lambda r:'SMC',lambda r:{},now=datetime(2027,1,1,4,tzinfo=timezone.utc))
    assert (r['current_year'],r['current_month'])==(2027,1)


def test_account_api_includes_calendar_history():
    import pandas as pd
    from dashboard.account_metrics import build_account_payload
    class Repo:
        def account_trade_history_dataframe(self,source=None,apply_stats_reset=True):
            return pd.DataFrame()
    result=build_account_payload(Repo())
    assert result['period_performance']['current_year']
    assert result['period_performance']['current_month']


def test_calendar_is_primary_and_disclosure_is_balanced():
    from dashboard.account_page import ACCOUNT_HTML
    from dashboard.performance_page import PERFORMANCE_HTML

    # En /performance está el panel de rendimiento
    assert 'id="periodPerformance"' in PERFORMANCE_HTML
    # En /account la cuenta en vivo está visible directamente sin details ni acordeón
    assert 'Cuenta en vivo · Operaciones y auditorías' in ACCOUNT_HTML
    assert '<details class="accountOperational">' not in ACCOUNT_HTML
    assert '<section class="grid">' in ACCOUNT_HTML


def test_performance_page_instrument_modal_and_strategy_breakdown():
    from dashboard.performance_page import PERFORMANCE_HTML

    # Modal para diagnóstico de instrumento y mejor estrategia
    assert 'id="instrumentModal"' in PERFORMANCE_HTML
    assert 'id="modalBestStrategyCard"' in PERFORMANCE_HTML
    assert 'id="modalStrategyComparison"' in PERFORMANCE_HTML
    assert 'id="modalOperationsList"' in PERFORMANCE_HTML
    assert 'id="modalCloseBtn"' in PERFORMANCE_HTML
    assert 'closeModal' in PERFORMANCE_HTML

    # Barra de búsqueda y catálogo de todos los activos
    assert 'id="perfAssetSearch"' in PERFORMANCE_HTML
    assert 'openInstrumentModal' in PERFORMANCE_HTML


