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


def test_build_monthly_daily_performance_best_worst_day_and_strategy_breakdown():
    from datetime import datetime, timezone
    from dashboard.period_performance import build_monthly_daily_performance

    fixed_now = datetime(2026, 10, 15, 15, 0, tzinfo=timezone.utc)

    records = [
        {"id": 1, "status": "CLOSED", "net_pnl": 100.0, "exit_time": "2026-10-03T14:00:00Z", "strategy": "SMC", "instrument": "EURUSD"},
        {"id": 2, "status": "CLOSED", "net_pnl": 50.0, "exit_time": "2026-10-03T16:00:00Z", "strategy": "ORB", "instrument": "US_500"},
        {"id": 3, "status": "CLOSED", "net_pnl": -70.0, "exit_time": "2026-10-07T11:00:00Z", "strategy": "MALAYSIAN_SNR", "instrument": "BTCUSD"},
        {"id": 4, "status": "CLOSED", "net_pnl": -30.0, "exit_time": "2026-10-07T13:00:00Z", "strategy": "SMC", "instrument": "EURUSD"},
        {"id": 5, "status": "CLOSED", "net_pnl": 40.0, "exit_time": "2026-10-10T15:00:00Z", "strategy": "GOLD_QUARTERS", "instrument": "XAUUSD"},
        {"id": 6, "status": "CLOSED", "net_pnl": 0.0, "exit_time": "2026-10-12T10:00:00Z", "strategy": "SMC", "instrument": "GBPUSD"},
    ]

    res = build_monthly_daily_performance(
        records=records,
        strategy_name=lambda r: r.get("strategy"),
        metadata=lambda r: {},
        now=fixed_now,
    )

    assert res["year"] == 2026
    assert res["month"] == 10
    assert res["month_name"] == "Octubre"
    assert res["days_elapsed"] == 15
    assert len(res["days"]) == 15

    # Check best day (Day 3, +150, Top strategy: SMC)
    assert res["best_day"] is not None
    assert res["best_day"]["day"] == 3
    assert res["best_day"]["net_pnl"] == 150.0
    assert res["best_day"]["trades"] == 2
    assert res["best_day"]["top_strategy"] == "SMC"

    # Check worst day (Day 7, -100, Worst strategy: MALAYSIAN_SNR)
    assert res["worst_day"] is not None
    assert res["worst_day"]["day"] == 7
    assert res["worst_day"]["net_pnl"] == -100.0
    assert res["worst_day"]["trades"] == 2
    assert res["worst_day"]["worst_strategy"] == "MALAYSIAN_SNR"

    # Check overall monthly counts
    assert res["active_days_count"] == 4
    assert res["winning_days_count"] == 2
    assert res["losing_days_count"] == 1
    assert res["neutral_days_count"] == 1
    assert res["daily_winrate"] == 50.0
    assert res["total_month_pnl"] == 90.0

    # Verify day 3 breakdown
    day3 = next(d for d in res["days"] if d["day"] == 3)
    assert day3["is_best_day"] is True
    assert day3["is_worst_day"] is False
    assert day3["wins"] == 2
    assert day3["losses"] == 0
    assert day3["winrate"] == 100.0
    assert "SMC" in day3["strategies"] and day3["strategies"]["SMC"]["pnl"] == 100.0
    assert "ORB" in day3["strategies"] and day3["strategies"]["ORB"]["pnl"] == 50.0

    # Verify day 7 breakdown
    day7 = next(d for d in res["days"] if d["day"] == 7)
    assert day7["is_best_day"] is False
    assert day7["is_worst_day"] is True
    assert day7["wins"] == 0
    assert day7["losses"] == 2
    assert day7["winrate"] == 0.0

    # Verify strategy summary ranking
    strats = res["strategy_summary"]
    assert len(strats) == 4
    assert strats[0]["strategy"] in {"SMC", "ORB"}
    assert strats[-1]["strategy"] == "MALAYSIAN_SNR"
    assert strats[-1]["pnl"] == -70.0


def test_monthly_daily_performance_in_account_page():
    from dashboard.account_page import ACCOUNT_HTML

    assert 'id="monthlyDailyPerformanceSection"' in ACCOUNT_HTML
    assert 'id="calDaysGrid"' in ACCOUNT_HTML
    assert 'renderMonthlyDailyPerformance' in ACCOUNT_HTML
    assert 'showCalDayDetail' in ACCOUNT_HTML
    assert 'calBestDayPnl' in ACCOUNT_HTML
    assert 'calWorstDayPnl' in ACCOUNT_HTML
    assert 'calStrategyTable' in ACCOUNT_HTML


def test_break_even_target_stop_swap_and_spread_protection():
    from types import SimpleNamespace
    from strategy.execution.live_trading_engine import LiveTradingEngine, LiveTradingConfig

    e = object.__new__(LiveTradingEngine)
    e.config = LiveTradingConfig(break_even_offset_points=2)
    e.executor = SimpleNamespace(
        get_symbol_constraints=lambda sym: {
            "point": 0.0001,
            "digits": 5,
            "trade_contract_size": 100000.0,
        }
    )
    # Mock live tick: Bid 1.1000, Ask 1.1002 -> Spread = 0.0002 (2 pips)
    e.provider = SimpleNamespace(
        get_current_tick=lambda sym: {"bid": 1.1000, "ask": 1.1002}
    )

    entry = 1.1000
    # Case 1: Base offset = point * 2 (0.0002) + spread (0.0002) = 0.0004
    be_buy, off_buy = e._break_even_target_stop("EURUSD", "BUY", entry)
    assert round(off_buy, 5) == 0.0004
    assert round(be_buy, 5) == 1.1004

    be_sell, off_sell = e._break_even_target_stop("EURUSD", "SELL", entry)
    assert round(off_sell, 5) == 0.0004
    assert round(be_sell, 5) == 1.0996

    # Case 2: Negative Swap (-$10 USD accrued swap on 0.50 lots)
    # volume = 0.50, contract_size = 100000 -> denom = 50,000
    # swap_points = 10 / 50000 = 0.0002
    # Total offset = 0.0004 (base) + 0.0002 (swap) = 0.0006
    pos_dict = {"swap": -10.0, "volume": 0.50}
    be_swap_buy, off_swap_buy = e._break_even_target_stop("EURUSD", "BUY", entry, position=pos_dict)
    assert round(off_swap_buy, 5) == 0.0006
    assert round(be_swap_buy, 5) == 1.1006

    # Case 3: MT5 position object with attributes
    pos_obj = SimpleNamespace(swap=-10.0, volume=0.50)
    be_obj_sell, off_obj_sell = e._break_even_target_stop("EURUSD", "SELL", entry, position=pos_obj)
    assert round(off_obj_sell, 5) == 0.0006
    assert round(be_obj_sell, 5) == 1.0994


def test_calendar_view_and_day_inspector_html_structure():
    from dashboard.account_page import ACCOUNT_HTML

    # Controles de navegación mensual
    assert 'id="calPrevMonthBtn"' in ACCOUNT_HTML
    assert 'id="calNextMonthBtn"' in ACCOUNT_HTML
    assert 'id="calMonthSelect"' in ACCOUNT_HTML
    assert 'id="calTodayBtn"' in ACCOUNT_HTML
    assert 'navigateMonth' in ACCOUNT_HTML
    assert 'goToToday' in ACCOUNT_HTML

    # Encabezado de 7 columnas estilo calendario (LUN .. DOM)
    assert 'calWeekdaysHeader' in ACCOUNT_HTML
    assert 'LUN' in ACCOUNT_HTML
    assert 'DOM' in ACCOUNT_HTML

    # Grid de calendario y celdas
    assert 'calMonthGrid' in ACCOUNT_HTML
    assert 'calEmptyCell' in ACCOUNT_HTML
    assert 'calDayCell' in ACCOUNT_HTML

    # Inspector permanente del día
    assert 'id="calDayInspector"' in ACCOUNT_HTML
    assert 'id="inspDayTitle"' in ACCOUNT_HTML
    assert 'id="inspDayBadge"' in ACCOUNT_HTML
    assert 'id="inspDayPnl"' in ACCOUNT_HTML
    assert 'id="inspDayReturnPct"' in ACCOUNT_HTML
    assert 'id="inspDayTradesCount"' in ACCOUNT_HTML
    assert 'id="inspDayPosPct"' in ACCOUNT_HTML
    assert 'id="inspDayNegPct"' in ACCOUNT_HTML
    assert 'id="inspDayStrategies"' in ACCOUNT_HTML
    assert 'id="inspDayOperationsTable"' in ACCOUNT_HTML


def test_backend_calendar_metrics_and_month_history():
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from dashboard.period_performance import build_monthly_daily_performance

    # Simular operaciones en septiembre y octubre de 2026
    fake_records = [
        # Octubre día 1 (2 ganadas)
        {"id": 1, "source": "L", "broker": "M", "instrument": "EURUSD", "strategy": "SMC", "status": "CLOSED", "net_pnl": 50.0, "exit_time": "2026-10-01T14:00:00Z", "leg": "TP1"},
        {"id": 2, "source": "L", "broker": "M", "instrument": "EURUSD", "strategy": "SMC", "status": "CLOSED", "net_pnl": 70.0, "exit_time": "2026-10-01T15:00:00Z", "leg": "TP2"},
        # Octubre día 2 (1 perdida, 1 be)
        {"id": 3, "source": "L", "broker": "M", "instrument": "GBPUSD", "strategy": "ORB", "status": "CLOSED", "net_pnl": -40.0, "exit_time": "2026-10-02T10:00:00Z", "leg": "SL"},
        {"id": 4, "source": "L", "broker": "M", "instrument": "GBPUSD", "strategy": "ORB", "status": "CLOSED", "net_pnl": 0.0, "exit_time": "2026-10-02T11:00:00Z", "leg": "BE"},
        # Septiembre día 15
        {"id": 5, "source": "L", "broker": "M", "instrument": "USDJPY", "strategy": "ICT", "status": "CLOSED", "net_pnl": 120.0, "exit_time": "2026-09-15T12:00:00Z", "leg": "TP1"},
    ]

    now_oct = datetime(2026, 10, 7, 12, 0, tzinfo=ZoneInfo("America/Santiago"))
    res = build_monthly_daily_performance(
        fake_records,
        lambda r: r.get("strategy"),
        lambda r: {},
        now=now_oct,
        account_balance=10000.0,
    )

    # 1. Validación de navegación de meses disponibles
    assert "available_months" in res
    assert "all_months" in res
    month_keys = [m["key"] for m in res["available_months"]]
    assert "2026-10" in month_keys
    assert "2026-09" in month_keys

    # 2. Validación del mes actual (Octubre)
    assert res["year"] == 2026
    assert res["month"] == 10
    assert res["total_days_in_month"] == 31
    assert res["first_weekday_idx"] == 3  # 1 de Octubre de 2026 es Jueves (idx 3)
    assert res["today_day"] == 7

    # 3. Validación de la cuadrícula completa del calendario (31 días)
    assert len(res["calendar_days"]) == 31
    day1 = next(d for d in res["calendar_days"] if d["day"] == 1)
    assert day1["trades_count"] == 2
    assert day1["wins"] == 2
    assert day1["losses"] == 0
    assert day1["pos_trades_pct"] == 100.0
    assert day1["neg_trades_pct"] == 0.0
    assert day1["net_pnl"] == 120.0
    assert day1["return_pct"] == 1.2  # 120 / 10000 * 100

    day2 = next(d for d in res["calendar_days"] if d["day"] == 2)
    assert day2["trades_count"] == 2
    assert day2["wins"] == 0
    assert day2["losses"] == 1
    assert day2["break_even"] == 1
    assert day2["pos_trades_pct"] == 0.0
    assert day2["neg_trades_pct"] == 50.0
    assert day2["be_trades_pct"] == 50.0
    assert day2["net_pnl"] == -40.0
    assert day2["return_pct"] == -0.4

    # 4. Verificación de operaciones con datos detallados de ticket, pierna y porcentaje
    assert len(day1["operations"]) == 2
    op = day1["operations"][0]
    assert "ticket" in op
    assert "leg" in op
    assert "pnl_percent" in op
    assert "realized_rr" in op

    # 5. Verificación de orden descendente por hora (más reciente primero)
    assert day1["operations"][0]["datetime"] > day1["operations"][1]["datetime"]
    assert day1["operations"][0]["leg"] == "TP2"
    assert day1["operations"][1]["leg"] == "TP1"


def test_day_operations_table_has_expanded_height():
    from dashboard.account_page import ACCOUNT_HTML
    assert 'id="inspDayOperationsTable"' in ACCOUNT_HTML
    assert 'max-height: 1100px' in ACCOUNT_HTML




