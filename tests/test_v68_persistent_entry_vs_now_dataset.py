from pathlib import Path
from zipfile import ZipFile

from database.repository import TradingRepository
from dashboard.account_metrics import build_account_payload
from reporting.trade_report_exporter import TradeReportExporter


def _repo_with_trade(tmp_path):
    repo = TradingRepository(db_path=tmp_path / 'v68.db')
    trade_id = repo.create_trade({
        'source': 'DEMO',
        'broker': 'Deriv-Demo',
        'instrument': 'Volatility 75 Index',
        'timeframe': 'M5',
        'direction': 'BUY',
        'status': 'OPEN',
        'entry_time': '2026-09-01T09:00:00Z',
        'entry_price': 100.0,
        'stop_loss': 90.0,
        'take_profit': 140.0,
        'planned_rr': 4.0,
        'risk_percent': 0.5,
        'risk_amount': 50.0,
        'execution_key': 'V68:TEST:RUNNER',
        'broker_position_ticket': '88001',
        'details': {'metadata': {'trade_leg': 'RUNNER', 'strategy_name': 'SMC'}},
    })
    repo.upsert_trade_visual_audit(
        trade_id,
        instrument='Volatility 75 Index',
        source='DEMO',
        entry_context={
            'decision': 'ADAPTIVE_80_CONFIRMED',
            'direction': 'BUY',
            'score': 100,
            'confirmation_percentage': 85.7,
            'h1_trend': 'BULLISH',
            'structure_break': 'BOS_BULLISH',
            'zone': 'DISCOUNT',
        },
    )
    return repo, trade_id


def test_snapshot_history_is_append_only_and_persistent(tmp_path):
    repo, trade_id = _repo_with_trade(tmp_path)
    for rr, decision in [(0.4, 'ADAPTIVE_80_CONFIRMED'), (1.1, 'WAITING_M5_CONFIRMATION')]:
        repo.save_trade_audit_snapshot(
            trade_id,
            instrument='Volatility 75 Index',
            source='DEMO',
            bot_profile='VOLATILITY',
            daemon_magic=26082103,
            broker_position_ticket='88001',
            entry_view={'decision': 'ADAPTIVE_80_CONFIRMED', 'score': 100, 'confirmation_percentage': 85.7},
            current_view={'decision': decision, 'score': 88, 'confirmation_percentage': 80.0},
            market={'current_rr': rr, 'current_price': 104.0 + rr},
            visual_context={'available_timeframes': ['H1', 'M15', 'M5']},
        )
    rows = repo.trade_audit_snapshots(trade_id=trade_id, source='DEMO')
    assert len(rows) == 2
    assert rows[0]['market']['current_rr'] == 1.1
    assert rows[1]['market']['current_rr'] == 0.4
    # Reinicio del repositorio sobre el mismo SQLite.
    repo2 = TradingRepository(db_path=tmp_path / 'v68.db')
    assert len(repo2.trade_audit_snapshots(trade_id=trade_id, source='DEMO')) == 2


def test_account_exposes_entry_vs_now_history_using_source_trade_id(tmp_path):
    repo, trade_id = _repo_with_trade(tmp_path)
    repo.save_trade_audit_snapshot(
        trade_id,
        instrument='Volatility 75 Index',
        source='DEMO',
        entry_view={'decision': 'ENTRY_OK', 'score': 100},
        current_view={'decision': 'PROTECT', 'score': 82, 'chart_pattern_name': 'DOUBLE_BOTTOM'},
        market={'current_rr': 1.75},
    )
    payload = build_account_payload(repo, source='DEMO')
    row = next(r for r in payload['recent_trades'] if r.get('source_trade_id') == trade_id)
    assert row['entry_vs_now_snapshot_count'] == 1
    assert row['entry_vs_now_latest']['current_view']['decision'] == 'PROTECT'
    assert payload['persistence']['entry_vs_now_history'] == 'trade_audit_snapshots'


def test_xlsx_exports_entry_vs_now_sheet(tmp_path):
    repo, trade_id = _repo_with_trade(tmp_path)
    repo.save_trade_audit_snapshot(
        trade_id,
        instrument='Volatility 75 Index',
        source='DEMO',
        entry_view={'decision': 'ENTRY_OK', 'score': 100, 'confirmation_percentage': 85.7},
        current_view={'decision': 'PROTECT', 'score': 82, 'confirmation_percentage': 78.0},
        market={'current_rr': 1.75, 'current_price': 117.5},
        visual_context={'available_timeframes': ['H1', 'M15', 'M5']},
    )
    out = tmp_path / 'report.xlsx'
    result = TradeReportExporter(repo, output_path=out).export(source='DEMO')
    assert result['entry_vs_now_snapshots'] == 1
    assert out.exists()
    # XLSX es ZIP: validar que el workbook contiene la nueva hoja sin depender
    # del render del dashboard.
    with ZipFile(out) as z:
        workbook_xml = z.read('xl/workbook.xml').decode('utf-8')
        assert 'Entrada vs Ahora' in workbook_xml


def test_snapshot_dataframe_contains_research_columns(tmp_path):
    repo, trade_id = _repo_with_trade(tmp_path)
    repo.save_trade_audit_snapshot(
        trade_id,
        instrument='Volatility 75 Index',
        source='DEMO',
        entry_view={'decision': 'ENTRY_OK', 'score': 100, 'zone': 'DISCOUNT'},
        current_view={'decision': 'PROTECT', 'score': 80, 'chart_pattern_conflict': True},
        market={'current_rr': 2.2},
    )
    df = repo.trade_audit_snapshots_dataframe(source='DEMO')
    assert len(df) == 1
    assert df.iloc[0]['trade_id'] == trade_id
    assert df.iloc[0]['entry_decision'] == 'ENTRY_OK'
    assert df.iloc[0]['current_decision'] == 'PROTECT'
    assert bool(df.iloc[0]['current_chart_pattern_conflict']) is True
    assert float(df.iloc[0]['current_rr']) == 2.2


def test_account_page_has_entry_vs_now_timeline_ui():
    root = Path(__file__).resolve().parents[1]
    text = (root / 'dashboard' / 'account_page.py').read_text(encoding='utf-8')
    assert 'snapshots persistentes' in text
    assert 'Historial Entrada vs. Ahora' in text
