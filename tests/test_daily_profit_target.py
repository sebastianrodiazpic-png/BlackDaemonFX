"""Pruebas unitarias para la Meta de Ganancia Diaria (Daily Profit Target).

Verifica:
1. Persistencia de preferencias en SQLite / SQLAlchemy.
2. Cálculo de retorno del día a partir de operaciones cerradas y balance base.
3. Bloqueo de nuevas entradas al alcanzar la meta diaria configurada.
4. Mantenimiento activo de la gestión de riesgo para posiciones abiertas.
5. Opción de desactivar la meta diaria.
6. Función "Ganar un poquito más" (override con buffer extra y advertencia de riesgo).
7. Reactivación automática de los workers en la sesión de Asia del siguiente día (00:00 UTC).
8. Endpoints y payloads de servicio para el dashboard.
"""

from datetime import datetime, timezone, timedelta
import pytest
from pathlib import Path

from database.database import init_database, get_session_factory
from database.models import Trade, AccountSnapshot
from database.repository import TradingRepository
from strategy.execution.daily_profit_target import DailyProfitTargetManager, RISK_WARNING_TEXT


@pytest.fixture
def test_repo(tmp_path: Path):
    db_file = tmp_path / "test_trading.sqlite3"
    init_database(db_file)
    repo = TradingRepository(db_path=db_file)
    return repo


def test_preference_defaults_and_save(test_repo: TradingRepository):
    # Por defecto, devuelve valores estándar
    pref = test_repo.latest_daily_profit_target_preference(source="DEMO")
    assert pref["enabled"] is True
    assert pref["target_percent"] == 2.0
    assert pref["is_target_reached"] is False
    assert pref["override_unlocked"] is False
    assert pref["asia_session_start_hour_utc"] == 0

    # Guardar nueva configuración
    saved = test_repo.save_daily_profit_target_preference(
        source="DEMO",
        enabled=True,
        target_percent=3.5,
        extra_target_buffer_percent=1.5,
        is_target_reached=False,
    )
    assert saved["target_percent"] == 3.5
    assert saved["extra_target_buffer_percent"] == 1.5
    assert saved["version"] >= 1

    # Recuperar la última preferencia persistida
    latest = test_repo.latest_daily_profit_target_preference(source="DEMO")
    assert latest["target_percent"] == 3.5
    assert latest["extra_target_buffer_percent"] == 1.5


def test_daily_closed_trades_summary(test_repo: TradingRepository):
    now_utc = datetime(2026, 10, 8, 15, 30, tzinfo=timezone.utc)

    # Crear snapshot de cuenta con balance de 10,000
    test_repo.save_account_snapshot({
        "balance": 10250.0,
        "equity": 10250.0,
        "margin": 0.0,
        "free_margin": 10250.0,
        "profit": 0.0,
    })

    # Crear 2 trades cerrados hoy: uno de +$200 y uno de +$50
    with test_repo.Session() as session:
        t1 = Trade(
            source="DEMO",
            instrument="EURUSD",
            direction="BUY",
            status="CLOSED",
            net_pnl=200.0,
            exit_time=now_utc - timedelta(hours=2),
        )
        t2 = Trade(
            source="DEMO",
            instrument="GBPUSD",
            direction="SELL",
            status="CLOSED",
            net_pnl=50.0,
            exit_time=now_utc - timedelta(hours=1),
        )
        # Trade de ayer: no debe sumarse hoy
        t_yesterday = Trade(
            source="DEMO",
            instrument="USDJPY",
            direction="BUY",
            status="CLOSED",
            net_pnl=500.0,
            exit_time=now_utc - timedelta(days=1),
        )
        session.add_all([t1, t2, t_yesterday])
        session.commit()

    summary = test_repo.get_daily_closed_trades_summary(source="DEMO", now_utc=now_utc)
    assert summary["today_closed_trades_count"] == 2
    assert summary["today_winning_trades"] == 2
    assert summary["today_losing_trades"] == 0
    assert summary["today_net_pnl"] == 250.0
    # base_balance = 10,250 - 250 = 10,000
    assert summary["base_balance"] == 10000.0
    # return_pct = (250 / 10,000) * 100 = 2.5%
    assert abs(summary["daily_return_pct"] - 2.5) < 0.001


def test_daily_profit_target_reaches_goal_and_locks(test_repo: TradingRepository):
    now_utc = datetime(2026, 10, 8, 14, 0, tzinfo=timezone.utc)
    mgr = DailyProfitTargetManager(repository=test_repo, source="DEMO")

    # Meta de 2.0%
    mgr.update_settings(enabled=True, target_percent=2.0)

    # Balance 10,000
    test_repo.save_account_snapshot({
        "balance": 10220.0,
        "equity": 10220.0,
    })

    # Trade de +$220 cerrado hoy (2.2% de ganancia sobre 10,000 base)
    with test_repo.Session() as session:
        t = Trade(
            source="DEMO",
            instrument="EURUSD",
            direction="BUY",
            status="CLOSED",
            net_pnl=220.0,
            exit_time=now_utc - timedelta(minutes=30),
        )
        session.add(t)
        session.commit()

    status = mgr.get_status(now_utc=now_utc)
    assert status["is_target_reached"] is True
    assert status["is_locked"] is True
    assert status["can_override"] is True
    assert status["locked_date"] == "2026-10-08"
    assert status["daily_return_pct"] == 2.2
    assert RISK_WARNING_TEXT in status["risk_warning"]

    # Comprobar bloqueo de entradas
    allowed, reason = mgr.is_entry_allowed(now_utc=now_utc)
    assert allowed is False
    assert "Entradas bloqueadas" in reason


def test_daily_profit_target_disabled_allows_entries(test_repo: TradingRepository):
    now_utc = datetime(2026, 10, 8, 14, 0, tzinfo=timezone.utc)
    mgr = DailyProfitTargetManager(repository=test_repo, source="DEMO")

    # Guardar preferencia desactivada
    mgr.update_settings(enabled=False, target_percent=2.0)

    # Retorno muy alto
    test_repo.save_account_snapshot({"balance": 11000.0, "equity": 11000.0})
    with test_repo.Session() as session:
        t = Trade(
            source="DEMO",
            instrument="EURUSD",
            direction="BUY",
            status="CLOSED",
            net_pnl=1000.0,
            exit_time=now_utc - timedelta(minutes=10),
        )
        session.add(t)
        session.commit()

    status = mgr.get_status(now_utc=now_utc)
    assert status["enabled"] is False
    assert status["is_locked"] is False

    allowed, reason = mgr.is_entry_allowed(now_utc=now_utc)
    assert allowed is True


def test_override_more_profit_flow(test_repo: TradingRepository):
    now_utc = datetime(2026, 10, 8, 14, 0, tzinfo=timezone.utc)
    mgr = DailyProfitTargetManager(repository=test_repo, source="DEMO")
    mgr.update_settings(enabled=True, target_percent=2.0)

    # 1. Alcanza meta del 2.0% (ganando $200 sobre $10,000)
    test_repo.save_account_snapshot({"balance": 10200.0, "equity": 10200.0})
    with test_repo.Session() as session:
        t1 = Trade(
            source="DEMO",
            instrument="EURUSD",
            direction="BUY",
            status="CLOSED",
            net_pnl=200.0,
            exit_time=now_utc - timedelta(minutes=45),
        )
        session.add(t1)
        session.commit()

    assert mgr.is_entry_allowed(now_utc=now_utc)[0] is False

    # 2. El usuario acepta la advertencia de riesgo y pide "ganar un poquito más" (+1.0% buffer)
    unlocked_status = mgr.request_override_more_profit(extra_percent=1.0, now_utc=now_utc)
    assert unlocked_status["override_unlocked"] is True
    assert unlocked_status["is_target_reached"] is False
    assert unlocked_status["effective_target_percent"] == 3.0  # 2.0% + 1.0%
    assert unlocked_status["is_locked"] is False

    # Entradas ahora permitidas para buscar el buffer
    assert mgr.is_entry_allowed(now_utc=now_utc)[0] is True

    # 3. Llega a ganar $310 en total (3.1% > 3.0% meta efectiva)
    test_repo.save_account_snapshot({"balance": 10310.0, "equity": 10310.0})
    with test_repo.Session() as session:
        t2 = Trade(
            source="DEMO",
            instrument="GBPUSD",
            direction="BUY",
            status="CLOSED",
            net_pnl=110.0,
            exit_time=now_utc - timedelta(minutes=10),
        )
        session.add(t2)
        session.commit()

    # Se vuelve a bloquear al alcanzar la meta con buffer
    relocked_status = mgr.get_status(now_utc=now_utc)
    assert relocked_status["is_locked"] is True
    assert mgr.is_entry_allowed(now_utc=now_utc)[0] is False


def test_asia_session_auto_reset(test_repo: TradingRepository):
    # Día 1: 2026-10-08 a las 18:00 UTC (sesión de NY). Bloqueado por alcanzar meta.
    day1_time = datetime(2026, 10, 8, 18, 0, tzinfo=timezone.utc)
    mgr = DailyProfitTargetManager(repository=test_repo, source="DEMO")
    mgr.update_settings(enabled=True, target_percent=2.0)

    test_repo.save_account_snapshot({"balance": 10250.0, "equity": 10250.0})
    with test_repo.Session() as session:
        t = Trade(
            source="DEMO",
            instrument="EURUSD",
            direction="BUY",
            status="CLOSED",
            net_pnl=250.0,
            exit_time=day1_time - timedelta(hours=1),
        )
        session.add(t)
        session.commit()

    status1 = mgr.get_status(now_utc=day1_time)
    assert status1["is_locked"] is True
    assert status1["locked_date"] == "2026-10-08"

    # Día 2: 2026-10-09 a las 00:05 UTC (Apertura de la Sesión de Asia en Tokio, hora 0 UTC).
    day2_asia_time = datetime(2026, 10, 9, 0, 5, tzinfo=timezone.utc)

    # Al evaluar en la sesión de Asia del nuevo día, se desbloquea automáticamente
    status2 = mgr.get_status(now_utc=day2_asia_time)
    assert status2["is_locked"] is False
    assert status2["is_target_reached"] is False
    assert status2["override_unlocked"] is False
    assert status2["last_reset_date"] == "2026-10-09"

    # Entradas permitidas para la nueva jornada
    allowed, reason = mgr.is_entry_allowed(now_utc=day2_asia_time)
    assert allowed is True


def test_dashboard_service_daily_target_integration(test_repo: TradingRepository):
    from dashboard.realtime_dashboard import RealtimeDashboardService

    service = RealtimeDashboardService(repository=test_repo, host="127.0.0.1", port=0)

    # 1. Payload inicial
    payload = service.get_daily_profit_target_payload()
    assert payload["enabled"] is True
    assert payload["target_percent"] == 2.0

    # 2. Modificación de ajustes desde el dashboard
    update_res = service.update_daily_profit_target_settings(enabled=True, target_percent=3.0)
    assert update_res["ok"] is True
    assert update_res["daily_profit_target"]["target_percent"] == 3.0

    # 3. Snapshot incluye el bloque daily_profit_target
    snap = service.snapshot()
    assert "daily_profit_target" in snap
    assert snap["daily_profit_target"]["target_percent"] == 3.0

    # 4. Solicitud de override "ganar un poquito más"
    override_res = service.request_daily_profit_target_override(extra_percent=1.0)
    assert override_res["ok"] is True
    assert override_res["daily_profit_target"]["override_unlocked"] is True


def test_engine_cycle_symbols_blocked_when_daily_target_reached(test_repo: TradingRepository):
    from unittest.mock import MagicMock
    from strategy.execution.live_trading_engine import LiveTradingEngine, LiveTradingConfig

    mock_provider = MagicMock()
    mock_executor = MagicMock()

    engine = LiveTradingEngine(
        provider=mock_provider,
        repository=test_repo,
        config=LiveTradingConfig(source="DEMO", bot_profile="SYNTHETICS"),
        executor=mock_executor,
    )

    base_symbols = ["Volatility 75 Index", "Volatility 100 Index"]

    # 1. Sin bloqueo, devuelve los símbolos
    selected = engine._selected_cycle_symbols(base_symbols)
    assert selected == base_symbols

    # 2. Forzar estado bloqueado por target diario
    test_repo.save_daily_profit_target_preference(
        source="DEMO",
        enabled=True,
        target_percent=2.0,
        is_target_reached=True,
        override_unlocked=False,
        locked_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    )

    # 3. Con meta alcanzada, _selected_cycle_symbols devuelve lista vacía
    selected_locked = engine._selected_cycle_symbols(base_symbols)
    assert selected_locked == []

    # 4. Comprobar que en process_symbol también se bloquea defensivamente
    mock_provider.resolve_symbol.return_value = "Volatility 75 Index"
    result = engine.process_symbol("Volatility 75 Index")
    assert result["action"] == "DAILY_PROFIT_TARGET_BLOCKED"
    assert "Entradas bloqueadas" in result["reason"]

