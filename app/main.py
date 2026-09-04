from __future__ import annotations

import argparse
import atexit
import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path
import subprocess
import sys
import threading
import time

# Windows puede usar cp1252 en procesos redirigidos. El daemon genera diagnósticos
# Unicode; forzamos UTF-8 para que un print nunca rompa el ciclo operativo.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from daemon_version import DAEMONBLACKFX_VERSION

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd

from config.instruments import InstrumentManager
from config.strategy_config import TIMEFRAMES
from data.collector import update_historical_csv
from database.repository import TradingRepository
from database.reporting import export_trading_report
from backtesting.backtest_pipeline import run_full_backtest_pipeline
from strategy.execution.trade_pipeline import run_trade_pipeline
from strategy.execution.live_trading_engine import LiveTradingEngine, LiveTradingConfig
from strategy.orb.new_york_orb import discover_orb_symbols, classify_orb_market


def _validate_timeframes():
    required = {"structure", "confirmation", "entry"}
    missing = required.difference(TIMEFRAMES)

    if missing:
        raise ValueError(
            "config.strategy_config.TIMEFRAMES no contiene las claves "
            f"requeridas: {sorted(missing)}"
        )


def _normalize_categories(categories):
    if categories is None:
        return None

    if isinstance(categories, str):
        categories = categories.split(",")

    normalized = [
        str(category).strip().lower()
        for category in categories
        if str(category).strip()
    ]

    return normalized or None


def _resolve_symbols(provider, symbol=None, categories=None):
    """
    Resuelve los símbolos después de conectar MT5.

    Prioridad:
      1. --symbol explícito.
      2. Instrumentos sintéticos y Forex tradeables descubiertos dinámicamente.
    """
    if symbol:
        return [provider.ensure_symbol(symbol)]

    manager = InstrumentManager(provider.connector)

    normalized_categories = _normalize_categories(categories)
    symbols = manager.get_active_symbols(categories=normalized_categories)

    # Sin filtro explícito de categorías, el daemon incorpora también los
    # cuatro mercados permitidos para ORB New York, si existen en este MT5.
    if normalized_categories is None:
        symbols = sorted(set(symbols).union(discover_orb_symbols(provider)))

    if not symbols:
        raise RuntimeError(
            "No se encontraron instrumentos tradeables "
            "(sintéticos/Forex/ORB) para las categorías solicitadas."
        )

    return symbols


def _require_symbol_for_offline_mode(symbol, mode):
    if not symbol:
        raise ValueError(
            f"El modo '{mode}' requiere --symbol porque no abre "
            "una conexión MT5 para descubrir instrumentos."
        )

    return str(symbol)


def collect_once(provider, repo, symbols):
    account = provider.connector.get_account_info()
    repo.save_account_snapshot(account)

    print(
        f"Balance actual: {account['balance']} | "
        f"Equity: {account['equity']}"
    )

    for requested_symbol in symbols:
        try:
            exact = provider.ensure_symbol(requested_symbol)

            path, rows = update_historical_csv(
                provider,
                exact,
                TIMEFRAMES["entry"],
                count=5000,
            )

            print(
                f"{exact}: {rows} velas guardadas en {path}"
            )

        except Exception as error:
            print(
                f"ERROR en {requested_symbol}: {error}"
            )


def run_collector(
    interval_seconds: int = 60,
    once: bool = False,
    symbol=None,
    categories=None,
):
    from brokers.mt5_connector import MT5Connector
    from brokers.mt5_data import MT5DataProvider

    connector = MT5Connector()
    provider = MT5DataProvider(connector)
    repo = TradingRepository()

    try:
        provider.connect()

        symbols = _resolve_symbols(
            provider,
            symbol=symbol,
            categories=categories,
        )

        print(
            f"Instrumentos seleccionados ({len(symbols)}): "
            f"{symbols}"
        )

        while True:
            print("\n=== CICLO DE RECOLECCIÓN ===")

            collect_once(
                provider,
                repo,
                symbols,
            )

            if once:
                break

            time.sleep(interval_seconds)

    except KeyboardInterrupt:
        print("Automatización detenida por el usuario.")

    finally:
        provider.disconnect()


def analyze_historical(
    symbol: str,
    timeframe: str,
    file_path: str,
):
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"No existe el histórico: {path}"
        )

    df = pd.read_csv(path)
    result = run_trade_pipeline(df)
    repo = TradingRepository()

    saved = 0

    for _, row in result["setups"].iterrows():
        data = {
            "instrument": symbol,
            "timeframe": timeframe,
            "signal_time": row["setup_time"],
            "direction": row["setup_type"].upper(),
            "valid": False,
            "trend_ok": row["trend_ok"],
            "swing_ok": row["swing_ok"],
            "liquidity_ok": row["liquidity_ok"],
            "sweep_ok": row["sweep_ok"],
            "structure_break_ok": row["structure_break_ok"],
            "order_block_ok": row["order_block_ok"],
            "retest_ok": False,
            "premium_discount_ok": row["premium_discount_ok"],
            "confirmation_ok": False,
            "details": row.to_dict(),
        }

        _, created = repo.save_signal_once(data)
        saved += int(created)

    for _, row in result["confirmations"].iterrows():
        data = {
            "instrument": symbol,
            "timeframe": timeframe,
            "signal_time": row["entry_time"],
            "direction": row["direction"],
            "valid": bool(row["valid"]),
            "trend_ok": True,
            "swing_ok": True,
            "liquidity_ok": True,
            "sweep_ok": True,
            "structure_break_ok": True,
            "order_block_ok": True,
            "retest_ok": True,
            "premium_discount_ok": True,
            "confirmation_ok": True,
            "details": row.to_dict(),
        }

        _, created = repo.save_signal_once(data)
        saved += int(created)

    output_dir = Path("storage/analysis")
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    result["setups"].to_csv(
        output_dir / (
            f"{symbol.replace(' ', '_')}_{timeframe}_setups.csv"
        ),
        index=False,
    )

    result["confirmations"].to_csv(
        output_dir / (
            f"{symbol.replace(' ', '_')}_"
            f"{timeframe}_confirmations.csv"
        ),
        index=False,
    )

    print("\n=== ANÁLISIS SMC COMPLETO ===")

    for key, value in result["summary"].items():
        print(f"{key}: {value}")

    print(
        f"Nuevos registros de señales guardados: {saved}"
    )
    print(
        f"Resultados CSV: {output_dir}"
    )


def run_demo_bot(
    symbols,
    timeframe: str,
    interval_seconds: int,
    once: bool,
    execute: bool,
    risk_percent: float,
    min_rr: float,
    verbose: bool = False,
    debug: bool = False,
    position_monitor_interval: int = 2,
    dashboard: bool = False,
    dashboard_port: int = 8765,
    bot_profile: str = "SYNTHETICS",
    magic: int = 26082026,
    auto_export: bool = True,
):
    from brokers.mt5_connector import MT5Connector
    from brokers.mt5_data import MT5DataProvider

    from brokers.mt5_execution import MT5ExecutionProvider
    from brokers.mt5_trade_executor import MT5TradeExecutor
    from reporting.trade_reporting_service import (
        TradeReportingConfig,
        TradeReportingService,
    )
    from trade_lifecycle_manager import TradeLifecycleManager
    from reporting.console_reporting_service import (
        ConsoleReportingConfig,
        ConsoleReportingService,
    )

    connector = MT5Connector()
    provider = MT5DataProvider(connector)
    repo = TradingRepository()

    execution_provider = MT5ExecutionProvider(connector)
    trade_executor = MT5TradeExecutor(
        execution_provider=execution_provider,
        magic=int(magic),
        deviation=20,
    )
    reporting_service = TradeReportingService(
        repository=repo,
        config=TradeReportingConfig(
            source="DEMO",
            output_path=(
                PROJECT_ROOT
                / "storage"
                / "exports"
                / "deriv_demo_trading_report.xlsx"
            ),
            auto_export=bool(auto_export),
            broker="Deriv-Demo",
        ),
    )
    lifecycle_manager = TradeLifecycleManager(
        trade_executor=trade_executor,
        reporting_service=reporting_service,
    )
    console_reporter = ConsoleReportingService(
        ConsoleReportingConfig(verbose=verbose, debug=debug)
    )

    dashboard_service = None
    if dashboard:
        from dashboard.realtime_dashboard import RealtimeDashboardService
        dashboard_service = RealtimeDashboardService(
            repository=repo,
            host="127.0.0.1",
            port=dashboard_port,
        )

    config = LiveTradingConfig(
        source="DEMO",
        entry_timeframe=timeframe,
        risk_percent=risk_percent,
        bot_profile=str(bot_profile).upper(),
        magic=int(magic),
        min_rr=min_rr,
        # v100: reserva de fill y banda inferior calibrada con los cuatro
        # incidentes reales de granularidad observados (exceso máximo 0.74%
        # sobre el hard cap). Reduce falsos cierres sin elevar el límite duro.
        pre_fill_risk_buffer=0.01,
        min_actual_risk_ratio=0.97,
        execution_enabled=execute,
        orb_enabled=(str(bot_profile).upper() == "ORB"),
        arps_scalper_enabled=(str(bot_profile).upper().startswith("SCALP_")),
        arps_risk_percent=0.25,
        forex_event_timeframe=(
            "M1" if str(bot_profile).upper().startswith("SCALP_") else "M5"
        ),
        first_target_rr=(0.8 if str(bot_profile).upper().startswith("SCALP_") else 1.0),
        second_target_rr=(1.5 if str(bot_profile).upper().startswith("SCALP_") else 2.0),
        single_entry_target_rr=(1.5 if str(bot_profile).upper().startswith("SCALP_") else 2.0),

        # v41 experimental: mantener riesgo inicial, pero permitir que el RUNNER
        # gestione 2R -> 3R -> 4R con profit lock estructural.
        runner_extension_enabled=(not str(bot_profile).upper().startswith("SCALP_")),
        runner_extension_first_trigger_rr=2.0,
        runner_extension_first_lock_rr=1.0,
        runner_extension_second_trigger_rr=3.0,
        runner_extension_second_lock_rr=2.0,
        runner_extension_max_target_rr=4.0,

        # Jump sigue operativo, pero necesita confirmaciones reforzadas.
        jump_strict_filter_enabled=True,
        jump_min_confirmation_ratio=0.90,
        jump_min_trade_score=90.0,
        jump_allow_single_fallback=False,
    )

    engine = LiveTradingEngine(
        provider,
        repo,
        config=config,
        executor=execution_provider,
        lifecycle_manager=lifecycle_manager,
        reporting_service=reporting_service,
        console_reporter=console_reporter,
        dashboard_service=dashboard_service,
    )

    try:
        provider.connect()

        symbols = (
            provider.prepare_symbols(symbols)
            if hasattr(provider, "prepare_symbols")
            else [provider.ensure_symbol(symbol) for symbol in symbols]
        )

        if dashboard_service is not None:
            manager = InstrumentManager(provider.connector)
            discovered = manager.get_all_instruments()
            categorized = {}
            forex_set = set(manager.discovery.get_tradeable_forex())
            for discovered_symbol in discovered:
                category = (
                    "forex"
                    if discovered_symbol in forex_set
                    else manager.discovery.classify_symbol(discovered_symbol)
                )
                categorized.setdefault(category, []).append(discovered_symbol)
            # Grupo separado para la estrategia ORB NY. Se descubre directamente
            # desde MT5 porque no forma parte del catálogo de sintéticos.
            for orb_symbol in discover_orb_symbols(provider):
                market = classify_orb_market(orb_symbol) or "ORB"
                categorized.setdefault(f"orb_ny_{market.lower()}", []).append(orb_symbol)
            # v56: no convertir el universo completo del worker en selección global.
            dashboard_service.set_instrument_catalog(categorized, selected_symbols=None)
            dashboard_url = dashboard_service.start(live=True)
            print(f"Dashboard de calidad en tiempo real: {dashboard_url}")
            print(f"Gestión modular de instrumentos: {dashboard_service.instruments_url}")
            print(f"Cuenta activa y estadísticas: {dashboard_service.account_url}")
            print("La selección de instrumentos se aplica desde el siguiente ciclo.")

        account = engine.executor.assert_demo_account()

        # Cuenta activa v24: NO reconstruye ni importa automáticamente el
        # historial completo de la cuenta MT5. La vista de Cuenta activa se
        # alimenta exclusivamente de registros que pasaron por la base
        # operativa local y fueron archivados en trade_journal.
        #
        # La reconciliación de posiciones ABIERTAS se mantiene abajo porque
        # permite recuperar el estado operativo actual del daemon sin poblar
        # el historial completo de la cuenta del broker.

        # Descubrimiento inverso MT5 -> SQLAlchemy. Esto recupera posiciones que
        # siguen abiertas en el terminal pero no existen todavía en la base local
        # (por ejemplo, si la DB fue limpiada, reemplazada o el daemon se cerró
        # antes de persistirlas). Las posiciones con el magic del daemon se
        # adoptan como DEMO; las demás se guardan sólo para visualización.
        try:
            imported = repo.import_open_mt5_positions(
                execution_provider,
                source="DEMO",
                magic=config.magic,
                include_external=True,
            )
            if imported.get("imported_daemon") or imported.get("imported_external"):
                print(
                    "Importación MT5/SQLAlchemy: "
                    f"{imported.get('imported_daemon', 0)} posición(es) del daemon recuperada(s), "
                    f"{imported.get('imported_external', 0)} posición(es) externa(s) guardada(s) sólo para visualización."
                )
        except Exception as exc:
            if debug:
                print(f"Advertencia al importar posiciones abiertas desde MT5: {exc}")

        # Reconciliación al reconectar: SQLite conserva las posiciones OPEN
        # durante una desconexión; al volver MT5 determina cuáles siguen vivas.
        try:
            reconciliation = repo.reconcile_open_trades(execution_provider, source="DEMO")
            if reconciliation.get("closed_synced"):
                print(
                    "Reconciliación MT5/SQLAlchemy: "
                    f"{reconciliation['closed_synced']} operación(es) cerrada(s) sincronizada(s)."
                )
            # También cerramos en SQLite las posiciones externas que se hubieran
            # importado anteriormente para visualización y ya no estén en MT5.
            try:
                repo.reconcile_open_trades(execution_provider, source="MT5_EXTERNAL")
            except Exception:
                pass
            if dashboard_service is not None:
                dashboard_service.mark_live()
        except Exception as exc:
            if debug:
                print(f"Advertencia de reconciliación MT5/SQLAlchemy: {exc}")

        print(f"DAEMONBLACKFX VERSION: {DAEMONBLACKFX_VERSION}")
        print(
            f"BOT ACTIVO: {str(bot_profile).upper()} | MAGIC={int(magic)} | "
            f"ESTRATEGIA={'ARPS_SYNTHETIC_SCALPER' if config.arps_scalper_enabled else 'SMC/ORB'} | "
            f"instrumentos={len(symbols)} | auto_export={bool(auto_export)}"
        )
        console_reporter.print_startup(
            account=account,
            execute=execute,
            symbols=symbols,
            interval=interval_seconds,
            risk_percent=(config.arps_risk_percent if config.arps_scalper_enabled else risk_percent),
            min_rr=min_rr,
            report_path=reporting_service.exporter.output_path,
        )

        if once:
            outcome = engine.run_once(symbols)
            results = outcome["results"]
            for index, row in enumerate(results, start=1):
                console_reporter.print_result(
                    row,
                    index=index,
                    total=len(results),
                )
            console_reporter.summarize(
                results,
                sync=outcome.get("sync", 0),
                cycle_number=1,
                interval=None,
            )

        else:
            engine.run_daemon(
                symbols,
                interval_seconds=interval_seconds,
                position_monitor_interval=position_monitor_interval,
                console_reporter=console_reporter,
            )

    except KeyboardInterrupt:
        print("Bot detenido por el usuario.")

    finally:
        if dashboard_service is not None:
            dashboard_service.mark_offline("DAEMON DESCONECTADO · ESTADO PERSISTIDO")
            dashboard_service.stop()
        provider.disconnect()


def run_live_paper(
    symbols,
    interval_seconds: int,
    once: bool,
    volume: float,
):
    from brokers.mt5_connector import MT5Connector
    from brokers.mt5_data import MT5DataProvider
    from strategy.execution.multi_timeframe import (
        MultiTimeframeAnalyzer,
        MultiTimeframeConfig,
    )
    from strategy.execution.paper_trade_executor import (
        PaperTradeExecutor,
    )
    from strategy.execution.live_paper_trading_engine import (
        LivePaperTradingConfig,
        LivePaperTradingEngine,
    )
    from trade_lifecycle_manager import (
        TradeLifecycleManager,
    )
    from reporting.trade_reporting_service import (
        TradeReportingConfig,
        TradeReportingService,
    )

    connector = MT5Connector()
    provider = MT5DataProvider(connector)

    multi_timeframe_config = MultiTimeframeConfig(
        structure_timeframe=TIMEFRAMES["structure"],
        confirmation_timeframe=TIMEFRAMES["confirmation"],
        entry_timeframe=TIMEFRAMES["entry"],
    )

    analyzer = MultiTimeframeAnalyzer(
        provider,
        config=multi_timeframe_config,
    )

    executor = PaperTradeExecutor()

    repository = TradingRepository()
    reporting_service = TradeReportingService(
        repository=repository,
        config=TradeReportingConfig(
            source="PAPER",
            output_path=(
                PROJECT_ROOT
                / "storage"
                / "exports"
                / "paper_trading_report.xlsx"
            ),
            auto_export=True,
            broker="PAPER",
        ),
    )

    lifecycle_manager = TradeLifecycleManager(
        trade_executor=executor,
        reporting_service=reporting_service,
    )

    engine = LivePaperTradingEngine(
        data_provider=provider,
        analyzer=analyzer,
        lifecycle_manager=lifecycle_manager,
        config=LivePaperTradingConfig(
            volume=volume,
            interval_seconds=interval_seconds,
        ),
    )

    try:
        provider.connect()

        symbols = (
            provider.prepare_symbols(symbols)
            if hasattr(provider, "prepare_symbols")
            else [provider.ensure_symbol(symbol) for symbol in symbols]
        )

        account = connector.get_account_info()
        repository.save_account_snapshot({
            **account,
            "broker": "MT5-DEMO-DATA",
        })

        print(
            "=== LIVE PAPER TRADING - MT5 DEMO DATA ==="
        )
        print(
            f"Cuenta: {account['login']} | "
            f"Servidor: {account['server']}"
        )
        print(
            "IMPORTANTE: no se enviarán órdenes al broker; "
            "las posiciones son PAPER."
        )
        print(
            f"Reporte XLSX: {reporting_service.exporter.output_path}"
        )
        print(
            f"Timeframes: H1={TIMEFRAMES['structure']} | "
            f"M15={TIMEFRAMES['confirmation']} | "
            f"Entrada={TIMEFRAMES['entry']}"
        )
        print(
            f"Instrumentos ({len(symbols)}): {symbols}"
        )

        if once:
            result = engine.run_once(symbols)
            print(result)

        else:
            engine.run_daemon(symbols)

    except KeyboardInterrupt:
        print(
            "Live Paper Trading detenido por el usuario."
        )

    finally:
        provider.disconnect()


def run_demo_preflight(symbols):
    from brokers.mt5_connector import MT5Connector
    from brokers.mt5_execution import MT5ExecutionProvider
    from services.execution_preflight_service import ExecutionPreflightService

    connector = MT5Connector()
    repository = TradingRepository()

    try:
        connector.connect()
        service = ExecutionPreflightService(
            execution_provider=MT5ExecutionProvider(connector),
            repository=repository,
        )
        result = service.run(symbols)

        print("=" * 72)
        print("DERIV DEMO EXECUTION PREFLIGHT")
        print("=" * 72)
        for item in result["checks"]:
            status = "OK" if item["ok"] else "FAIL"
            print(f"[{status}] {item['name']} {item['details']}")
        print("=" * 72)
        if result["ready"]:
            print("STATUS: READY FOR DEMO EXECUTION")
        else:
            print("STATUS: NOT READY")
            print("FAILED CHECKS:")
            for item in result["failed"]:
                details = item.get("details") or {}
                reason = details.get("reason") or details.get("error")
                if not reason:
                    if item["name"] == "MT5_AUTOTRADING_ALLOWED":
                        reason = "AUTO_TRADING_DISABLED_OR_TRADE_API_DISABLED"
                    elif item["name"] == "MT5_TERMINAL_CONNECTED":
                        reason = "MT5_TERMINAL_NOT_CONNECTED"
                    elif item["name"] == "DEMO_ACCOUNT":
                        reason = "CONNECTED_ACCOUNT_IS_NOT_DEMO"
                    else:
                        reason = "CHECK_FAILED"
                print(f" - {item['name']}: {reason} | details={details}")
        return result
    finally:
        connector.disconnect()


def run_live_demo_smoke(symbol, direction, volume, auto_close):
    from brokers.mt5_connector import MT5Connector
    from brokers.mt5_execution import MT5ExecutionProvider
    from services.live_demo_smoke_test_service import (
        LiveDemoSmokeTestConfig,
        LiveDemoSmokeTestService,
    )

    connector = MT5Connector()
    repository = TradingRepository()
    try:
        connector.connect()
        service = LiveDemoSmokeTestService(
            execution_provider=MT5ExecutionProvider(connector),
            repository=repository,
            config=LiveDemoSmokeTestConfig(
                symbol=symbol,
                direction=direction,
                volume=volume,
                auto_close=auto_close,
                output_path=(
                    PROJECT_ROOT / "storage" / "exports" / "deriv_demo_smoke_report.xlsx"
                ),
            ),
        )
        result = service.run()
        print("=" * 72)
        print("DERIV DEMO LIVE SMOKE TEST")
        print("=" * 72)
        print("POSITION TICKET:", result["position_ticket"])
        print("EXECUTION ID:", result["execution_id"])
        print("BROKER POSITION FOUND:", result["broker_position_found"])
        print("SQLITE TRADE FOUND:", result["sqlite_trade_found"])
        print("CLOSED:", result["closed"])
        print("XLSX:", result["xlsx"])
        return result
    finally:
        connector.disconnect()


def _resolve_live_symbols(args):
    """
    Descubre símbolos dinámicamente para modos que usan MT5.

    Se crea una conexión temporal solamente para resolver la lista.
    Los motores vuelven a abrir su propia conexión para ejecutar.
    """
    from brokers.mt5_connector import MT5Connector
    from brokers.mt5_data import MT5DataProvider

    connector = MT5Connector()
    provider = MT5DataProvider(connector)

    try:
        provider.connect()

        resolved = _resolve_symbols(
            provider,
            symbol=args.symbol,
            categories=args.categories,
        )

        # Las preferencias persistentes del módulo Instrumentos actúan como
        # selección predeterminada únicamente cuando el usuario no fuerza
        # --symbol ni --categories en la línea de comandos.
        if not args.symbol and not args.categories:
            try:
                repo = TradingRepository()
                pref = repo.latest_instrument_selection(source="DEMO")
            except Exception:
                pref = None

            if pref and pref.get("selected_symbols"):
                preferred = [str(s) for s in pref["selected_symbols"]]
                resolved_set = set(resolved)
                filtered = [s for s in preferred if s in resolved_set]

                # Si algún instrumento cambió de nombre/dejó de existir, no
                # bloqueamos el daemon. Se usan sólo los que siguen disponibles.
                if filtered:
                    print(
                        "Preferencias persistentes de instrumentos recuperadas "
                        f"desde SQLAlchemy ({len(filtered)}): {filtered}"
                    )
                    return filtered

        return resolved

    finally:
        provider.disconnect()





BOT_PROFILES = {
    # Perfil agregado conservado por compatibilidad. No se usa en el nuevo
    # coordinador dividido salvo que el usuario lo ejecute explícitamente.
    "SYNTHETICS": {
        "mode": "synthetic-daemon",
        "magic": 26082026,
        "categories": ["volatility", "boom", "crash", "step", "jump", "flip"],
    },
    "BOOM": {
        "mode": "boom-daemon",
        "magic": 26082101,
        "categories": ["boom"],
    },
    "CRASH": {
        "mode": "crash-daemon",
        "magic": 26082102,
        "categories": ["crash"],
    },
    "VOLATILITY": {
        "mode": "volatility-daemon",
        "magic": 26082103,
        "categories": ["volatility"],
    },
    # v99: el perfil anterior se conserva para compatibilidad/manual, pero el
    # multi-bot distribuye su universo entre cuatro procesos independientes.
    "VOLATILITY_1": {
        "mode": "volatility-1-daemon", "magic": 26082401,
        "categories": ["volatility"], "shard_index": 0, "shard_count": 4,
    },
    "VOLATILITY_2": {
        "mode": "volatility-2-daemon", "magic": 26082402,
        "categories": ["volatility"], "shard_index": 1, "shard_count": 4,
    },
    "VOLATILITY_3": {
        "mode": "volatility-3-daemon", "magic": 26082403,
        "categories": ["volatility"], "shard_index": 2, "shard_count": 4,
    },
    "VOLATILITY_4": {
        "mode": "volatility-4-daemon", "magic": 26082404,
        "categories": ["volatility"], "shard_index": 3, "shard_count": 4,
    },
    "STEP": {
        "mode": "step-daemon",
        "magic": 26082104,
        "categories": ["step"],
    },
    "JUMP": {
        "mode": "jump-daemon",
        "magic": 26082105,
        "categories": ["jump"],
    },
    "FLIP": {
        "mode": "flip-daemon",
        "magic": 26082106,
        "categories": ["flip"],
    },
    # v96: ARPS corre en paralelo a SMC. Cada familia conserva proceso y magic
    # independientes para impedir colisiones de ejecución, monitor y auditoría.
    "SCALP_BOOM": {"mode": "scalp-boom-daemon", "magic": 26082301, "categories": ["boom"], "strategy": "ARPS"},
    "SCALP_CRASH": {"mode": "scalp-crash-daemon", "magic": 26082302, "categories": ["crash"], "strategy": "ARPS"},
    "SCALP_VOLATILITY": {"mode": "scalp-volatility-daemon", "magic": 26082303, "categories": ["volatility"], "strategy": "ARPS"},
    "SCALP_STEP": {"mode": "scalp-step-daemon", "magic": 26082304, "categories": ["step"], "strategy": "ARPS"},
    "SCALP_JUMP": {"mode": "scalp-jump-daemon", "magic": 26082305, "categories": ["jump"], "strategy": "ARPS"},
    "SCALP_FLIP": {"mode": "scalp-flip-daemon", "magic": 26082306, "categories": ["flip"], "strategy": "ARPS"},
    "FOREX": {
        "mode": "forex-daemon",
        "magic": 26082027,
        "categories": ["forex"],
    },
    "FOREX_1": {
        "mode": "forex-1-daemon",
        "magic": 26082201,
        "categories": ["forex"],
        "shard_index": 0,
        "shard_count": 4,
    },
    "FOREX_2": {
        "mode": "forex-2-daemon",
        "magic": 26082202,
        "categories": ["forex"],
        "shard_index": 1,
        "shard_count": 4,
    },
    "FOREX_3": {
        "mode": "forex-3-daemon",
        "magic": 26082203,
        "categories": ["forex"],
        "shard_index": 2,
        "shard_count": 4,
    },
    "FOREX_4": {
        "mode": "forex-4-daemon",
        "magic": 26082204,
        "categories": ["forex"],
        "shard_index": 3,
        "shard_count": 4,
    },
    "ORB": {
        "mode": "orb-daemon",
        "magic": 26082028,
        "categories": [],
    },
    "GOLD": {
        "mode": "gold-session-daemon",
        "magic": 26082029,
        "categories": [],
    },
}

SYNTHETIC_SPLIT_PROFILES = (
    "BOOM",
    "CRASH",
    "VOLATILITY",
    "STEP",
    "JUMP",
    "FLIP",
)

SYNTHETIC_SCALPER_PROFILES = (
    "SCALP_BOOM", "SCALP_CRASH", "SCALP_VOLATILITY",
    "SCALP_STEP", "SCALP_JUMP", "SCALP_FLIP",
)

VOLATILITY_SHARD_PROFILES = (
    "VOLATILITY_1", "VOLATILITY_2", "VOLATILITY_3", "VOLATILITY_4",
)
MULTIBOT_SYNTHETIC_PROFILES = (
    "BOOM", "CRASH", *VOLATILITY_SHARD_PROFILES, "STEP", "JUMP", "FLIP",
)
FOREX_SPLIT_PROFILES = ("FOREX_1", "FOREX_2", "FOREX_3", "FOREX_4")
FULL_MULTI_BOT_PROFILES = (
    *MULTIBOT_SYNTHETIC_PROFILES,
    *SYNTHETIC_SCALPER_PROFILES,
    *FOREX_SPLIT_PROFILES,
    "GOLD", "ORB",
)


def _assert_synthetic_split_architecture():
    """Falla temprano si se rompe la separación 1 familia = 1 proceso."""
    expected = {
        "BOOM": ("boom-daemon", 26082101, ("boom",)),
        "CRASH": ("crash-daemon", 26082102, ("crash",)),
        "VOLATILITY": ("volatility-daemon", 26082103, ("volatility",)),
        "STEP": ("step-daemon", 26082104, ("step",)),
        "JUMP": ("jump-daemon", 26082105, ("jump",)),
        "FLIP": ("flip-daemon", 26082106, ("flip",)),
    }
    if tuple(SYNTHETIC_SPLIT_PROFILES) != tuple(expected):
        raise RuntimeError("SYNTHETIC_SPLIT_ARCHITECTURE_ERROR: perfiles alterados.")
    seen_modes, seen_magics = set(), set()
    for profile, (mode, magic, categories) in expected.items():
        spec = BOT_PROFILES.get(profile) or {}
        actual = (spec.get("mode"), spec.get("magic"), tuple(spec.get("categories") or ()))
        if actual != (mode, magic, categories):
            raise RuntimeError(f"SYNTHETIC_SPLIT_ARCHITECTURE_ERROR: {profile}={actual}.")
        if mode in seen_modes or magic in seen_magics:
            raise RuntimeError(f"SYNTHETIC_SPLIT_ARCHITECTURE_ERROR: duplicado en {profile}.")
        seen_modes.add(mode); seen_magics.add(magic)
    return True


def _assert_full_multibot_architecture(profiles):
    """Garantiza un solo coordinador con todos los workers esperados y únicos."""
    profiles = tuple(str(p).upper() for p in (profiles or ()))
    expected = tuple(FULL_MULTI_BOT_PROFILES)
    if profiles != expected:
        raise RuntimeError(
            f"FULL_MULTIBOT_ARCHITECTURE_ERROR: profiles={profiles}, expected={expected}"
        )
    modes = [str(BOT_PROFILES[p]["mode"]) for p in profiles]
    magics = [int(BOT_PROFILES[p]["magic"]) for p in profiles]
    if len(set(modes)) != len(modes) or len(set(magics)) != len(magics):
        raise RuntimeError("FULL_MULTIBOT_ARCHITECTURE_ERROR: mode o magic duplicado")
    if BOT_PROFILES["GOLD"] != {
        "mode": "gold-session-daemon", "magic": 26082029, "categories": []
    }:
        raise RuntimeError("FULL_MULTIBOT_ARCHITECTURE_ERROR: perfil GOLD alterado")
    return True


def _selection_profile_for_bot(profile: str) -> str:
    profile = str(profile or "").upper()
    if profile.startswith("FOREX"): return "FOREX"
    if profile in {"ORB", "GOLD"}: return "ORB"
    return "SYNTHETICS"



def _stable_symbol_shard(symbols, shard_index: int, shard_count: int):
    """Distribuye símbolos de forma determinista y estable entre workers."""
    shard_count = max(1, int(shard_count))
    shard_index = int(shard_index)
    ordered = sorted({str(s) for s in symbols if s}, key=lambda s: s.upper())
    return [s for i, s in enumerate(ordered) if i % shard_count == shard_index]


def _resolve_live_symbols_for_profile(args, profile: str):
    """Resuelve únicamente el universo perteneciente al bot solicitado."""
    from brokers.mt5_connector import MT5Connector
    from brokers.mt5_data import MT5DataProvider

    profile = str(profile).upper()
    if profile not in BOT_PROFILES:
        raise ValueError(f"Perfil de bot desconocido: {profile}")

    connector = MT5Connector()
    provider = MT5DataProvider(connector)
    try:
        provider.connect()
        manager = InstrumentManager(provider.connector)
        if profile == "ORB":
            universe = sorted(set(discover_orb_symbols(provider)))
        elif profile == "GOLD":
            universe = sorted({
                symbol for symbol in discover_orb_symbols(provider)
                if classify_orb_market(symbol) == "XAUUSD"
            })
        else:
            universe = manager.get_active_symbols(
                categories=BOT_PROFILES[profile]["categories"]
            )

        spec = BOT_PROFILES[profile]
        if spec.get("shard_count"):
            universe = _stable_symbol_shard(
                universe,
                int(spec.get("shard_index", 0)),
                int(spec.get("shard_count", 1)),
            )

        if args.symbol:
            exact = provider.ensure_symbol(args.symbol)
            if exact not in set(universe):
                raise ValueError(
                    f"El símbolo {exact} no pertenece al bot {profile}."
                )
            return [exact]

        if not universe:
            return []

        # v56: cada worker arranca con TODO su universo. La preferencia
        # persistente del perfil se relee en cada ciclo, sin reiniciar el bot.
        return universe
    finally:
        provider.disconnect()


def _build_multi_bot_dashboard_catalog(profiles):
    """Descubre el catálogo completo que debe mostrar el dashboard coordinador."""
    from brokers.mt5_connector import MT5Connector
    from brokers.mt5_data import MT5DataProvider

    connector = MT5Connector()
    provider = MT5DataProvider(connector)
    categorized = {}
    try:
        provider.connect()
        manager = InstrumentManager(provider.connector)

        for profile in profiles:
            spec = BOT_PROFILES[profile]
            if profile == "ORB":
                for symbol in discover_orb_symbols(provider):
                    market = classify_orb_market(symbol) or "ORB"
                    categorized.setdefault(
                        f"orb_ny_{str(market).lower()}",
                        [],
                    ).append(symbol)
                continue
            if profile == "GOLD":
                # XAUUSD ya aparece en la categoría visual ORB; el perfil GOLD
                # reutiliza esa selección sin duplicar el instrumento en UI.
                continue

            for category in spec.get("categories", []):
                symbols = manager.get_active_symbols(categories=[category])
                if symbols:
                    categorized.setdefault(category, []).extend(symbols)

        # Eliminar duplicados sin alterar el nombre real del broker.
        for category, symbols in list(categorized.items()):
            categorized[category] = sorted(set(str(s) for s in symbols if s))
        return categorized
    finally:
        provider.disconnect()


def _recover_empty_synthetic_selection(repo, catalog, profiles):
    """Restaura el catálogo sintético si su preferencia persistida quedó vacía."""
    active_profiles = {str(profile or "").upper() for profile in (profiles or [])}
    if not active_profiles.intersection(SYNTHETIC_SPLIT_PROFILES):
        return None
    reader = getattr(repo, "latest_instrument_selection_profile", None)
    writer = getattr(repo, "save_instrument_selection_profile", None)
    if not callable(reader) or not callable(writer):
        return None
    preference = reader("SYNTHETICS", source="DEMO")
    if preference is None or preference.get("selected_symbols"):
        return None
    synthetic_symbols = sorted(
        {
            str(symbol)
            for category, symbols in (catalog or {}).items()
            if str(category).lower() != "forex"
            and not str(category).lower().startswith("orb_ny_")
            for symbol in (symbols or [])
            if symbol
        },
        key=str.casefold,
    )
    if not synthetic_symbols:
        return None
    saved = writer(
        synthetic_symbols, selection_profile="SYNTHETICS", source="DEMO"
    )
    try:
        repo.save_audit_event(
            "EMPTY_SYNTHETIC_SELECTION_RECOVERED",
            source="DEMO",
            action="RESTORED_ALL_SYNTHETIC_SYMBOLS",
            reason="El coordinador no puede iniciar seis familias con SYNTHETICS vacío",
            payload={
                "symbols_restored": len(synthetic_symbols),
                "previous_version": preference.get("version"),
                "new_version": saved.get("version"),
                "version": DAEMONBLACKFX_VERSION,
            },
        )
    except Exception:
        pass
    print(
        "[RECUPERACIÓN] SYNTHETICS estaba vacío: "
        f"se habilitaron {len(synthetic_symbols)} instrumentos del catálogo."
    )
    return saved


def _assert_v53_runtime_compatibility(repo):
    """Falla temprano si la carpeta contiene módulos de versiones mezcladas."""
    missing = []
    if not hasattr(repo, "upsert_worker_runtime_state"):
        missing.append("TradingRepository.upsert_worker_runtime_state")
    if not hasattr(repo, "worker_runtime_states"):
        missing.append("TradingRepository.worker_runtime_states")

    try:
        from reporting.trade_report_exporter import TradeReportExporter
        if not hasattr(TradeReportExporter, "_compact_audit_dataframe"):
            missing.append("TradeReportExporter._compact_audit_dataframe")
    except Exception as exc:
        missing.append(f"TradeReportExporter import: {exc}")

    if missing:
        raise RuntimeError(
            "INSTALACION_INCONSISTENTE_V53: se detectaron archivos de versiones mezcladas. "
            "Extrae el ZIP v53 en una carpeta NUEVA y no sobre una instalación anterior. "
            "Faltan: " + ", ".join(missing)
        )

    # Verifica que la tabla nueva pueda escribirse/leerse realmente.
    probe_profile = "V53_PROBE"
    try:
        repo.upsert_worker_runtime_state(
            probe_profile,
            53000000,
            source="SYSTEM",
            status="PROBE",
            last_action="SCHEMA_CHECK",
            last_reason=DAEMONBLACKFX_VERSION,
            details={"version": DAEMONBLACKFX_VERSION},
        )
        rows = repo.worker_runtime_states(source="SYSTEM")
        if not any(row.get("bot_profile") == probe_profile for row in rows):
            raise RuntimeError("worker_runtime_states no devolvio el registro de prueba")
    except Exception as exc:
        raise RuntimeError(
            "RUNTIME_DB_SCHEMA_ERROR: no fue posible validar worker_runtime_states. "
            f"Detalle: {exc}"
        ) from exc


def _resolve_symbols_for_profile_shared(provider, repo, profile: str):
    """Resuelve el universo de un perfil usando una conexión MT5 ya abierta."""
    profile = str(profile or "").upper()
    spec = BOT_PROFILES[profile]
    manager = InstrumentManager(provider.connector)

    if profile == "ORB":
        universe = list(discover_orb_symbols(provider))
    elif profile == "GOLD":
        universe = [
            symbol for symbol in discover_orb_symbols(provider)
            if classify_orb_market(symbol) == "XAUUSD"
        ]
    elif profile.startswith("FOREX"):
        try:
            universe = list(manager.discovery.get_tradeable_forex())
        except Exception:
            universe = list(manager.get_active_symbols(categories=["forex"]))
    else:
        universe = []
        for category in spec.get("categories", []):
            universe.extend(manager.get_active_symbols(categories=[category]) or [])

    universe = sorted({str(s) for s in universe if s}, key=str.casefold)
    if spec.get("shard_count"):
        universe = _stable_symbol_shard(
            universe,
            int(spec.get("shard_index") or 0),
            int(spec.get("shard_count") or 1),
        )
    selection_profile = _selection_profile_for_bot(profile)
    reader = getattr(repo, "latest_instrument_selection_profile", None)
    pref = None
    if callable(reader):
        try:
            pref = reader(selection_profile, source="DEMO")
        except Exception:
            pref = None
    if pref is not None:
        selected = {str(s) for s in (pref.get("selected_symbols") or [])}
        universe = [s for s in universe if s in selected]
    return universe


def _run_startup_database_maintenance(repo, args):
    """Aplica retención antes de crear dashboard/workers del coordinador."""
    try:
        maintenance = repo.maintain_operational_audits(
            retention_days=getattr(args, "audit_retention_days", 14),
            max_rows=getattr(args, "audit_retention_max_rows", 250_000),
            checkpoint_mode="TRUNCATE",
        )
        print(
            "[DB MAINTENANCE] "
            f"deleted={maintenance['retention']['deleted_total']} "
            f"checkpoint={maintenance['checkpoint']['mode']} "
            f"db={maintenance['database']['path']}"
        )
        repo.save_audit_event(
            "DATABASE_MAINTENANCE",
            source="DEMO",
            action="AUDIT_RETENTION_APPLIED",
            payload=maintenance,
        )
        return maintenance
    except Exception as exc:
        # La retención es mantenimiento defensivo: nunca impide arrancar trading.
        print(f"[DB MAINTENANCE WARNING] {exc}", file=sys.stderr)
        return None


def run_unified_multibot_daemon(args, profiles=None):
    """v76: un solo proceso con workers lógicos independientes."""
    _warn_possible_parallel_daemon_instances()
    from brokers.mt5_connector import MT5Connector
    from brokers.mt5_data import MT5DataProvider
    from brokers.mt5_execution import MT5ExecutionProvider
    from brokers.mt5_trade_executor import MT5TradeExecutor
    from dashboard.realtime_dashboard import RealtimeDashboardService
    from reporting.console_reporting_service import ConsoleReportingConfig, ConsoleReportingService
    from reporting.trade_reporting_service import TradeReportingConfig, TradeReportingService
    from trade_lifecycle_manager import TradeLifecycleManager

    profiles = tuple(profiles or FULL_MULTI_BOT_PROFILES)
    if profiles == tuple(FULL_MULTI_BOT_PROFILES):
        _assert_full_multibot_architecture(profiles)
    repo = TradingRepository()
    _assert_v53_runtime_compatibility(repo)
    _run_startup_database_maintenance(repo, args)

    connector = MT5Connector()
    provider = MT5DataProvider(connector)
    execution_provider = MT5ExecutionProvider(connector)
    reporting = TradeReportingService(
        repository=repo,
        config=TradeReportingConfig(
            source="DEMO",
            output_path=PROJECT_ROOT / "storage" / "exports" / "deriv_demo_trading_report.xlsx",
            auto_export=False,
            broker="Deriv-Demo",
        ),
    )
    dashboard = RealtimeDashboardService(
        repository=repo,
        host="127.0.0.1",
        port=int(args.dashboard_port),
    )

    engines = {}
    symbols_by_profile = {}
    next_due = {}
    last_visual_by_profile = {}
    last_dashboard_heartbeat = 0.0
    pid = os.getpid()

    try:
        provider.connect()
        manager = InstrumentManager(provider.connector)

        categorized = {}
        for profile in profiles:
            spec = BOT_PROFILES[profile]
            if profile == "ORB":
                for symbol in discover_orb_symbols(provider):
                    market = classify_orb_market(symbol) or "ORB"
                    categorized.setdefault(f"orb_ny_{str(market).lower()}", []).append(symbol)
            elif profile.startswith("FOREX"):
                if "forex" not in categorized:
                    try:
                        categorized["forex"] = list(manager.discovery.get_tradeable_forex())
                    except Exception:
                        categorized["forex"] = list(manager.get_active_symbols(categories=["forex"]))
            else:
                for category in spec.get("categories", []):
                    categorized.setdefault(category, []).extend(
                        manager.get_active_symbols(categories=[category]) or []
                    )
        categorized = {
            k: sorted({str(x) for x in v if x}, key=str.casefold)
            for k, v in categorized.items()
        }
        dashboard.set_instrument_catalog(categorized, selected_symbols=None)
        dashboard_url = dashboard.start(live=True)
        dashboard.update_status("MULTIBOT UNIFICADO ACTIVO · 1 PROCESO")
        print(f"Dashboard central: {dashboard_url}")
        print(f"Instrumentos: {dashboard.instruments_url}")
        print(f"Cuenta activa: {dashboard.account_url}")

        for profile in profiles:
            spec = BOT_PROFILES[profile]
            symbols = _resolve_symbols_for_profile_shared(provider, repo, profile)
            if symbols and hasattr(provider, "prepare_symbols"):
                symbols = provider.prepare_symbols(symbols)
            symbols_by_profile[profile] = list(symbols)

            trade_executor = MT5TradeExecutor(
                execution_provider=execution_provider,
                magic=int(spec["magic"]),
                deviation=20,
            )
            lifecycle = TradeLifecycleManager(
                trade_executor=trade_executor,
                reporting_service=reporting,
            )
            console = ConsoleReportingService(
                ConsoleReportingConfig(verbose=args.verbose, debug=args.debug)
            )
            config = LiveTradingConfig(
                source="DEMO",
                entry_timeframe=args.timeframe,
                risk_percent=args.risk_percent,
                bot_profile=profile,
                magic=int(spec["magic"]),
                min_rr=args.min_rr,
                pre_fill_risk_buffer=0.01,
                min_actual_risk_ratio=0.97,
                execution_enabled=args.execute,
                orb_enabled=(profile == "ORB"),
                arps_scalper_enabled=bool(spec.get("strategy") == "ARPS"),
                arps_risk_percent=0.25,
                forex_event_timeframe=("M1" if spec.get("strategy") == "ARPS" else "M5"),
                first_target_rr=(0.8 if spec.get("strategy") == "ARPS" else 1.0),
                second_target_rr=(1.5 if spec.get("strategy") == "ARPS" else 2.0),
                single_entry_target_rr=(1.5 if spec.get("strategy") == "ARPS" else 2.0),
                runner_extension_enabled=bool(spec.get("strategy") != "ARPS"),
                runner_extension_first_trigger_rr=2.0,
                runner_extension_first_lock_rr=1.0,
                runner_extension_second_trigger_rr=3.0,
                runner_extension_second_lock_rr=2.0,
                runner_extension_max_target_rr=4.0,
                jump_strict_filter_enabled=True,
                jump_min_confirmation_ratio=0.90,
                jump_min_trade_score=90.0,
                jump_allow_single_fallback=False,
            )
            engines[profile] = LiveTradingEngine(
                provider,
                repo,
                config=config,
                executor=execution_provider,
                lifecycle_manager=lifecycle,
                reporting_service=reporting,
                console_reporter=console,
                dashboard_service=None,
            )
            next_due[profile] = time.monotonic() + (0.15 * len(next_due))
            last_visual_by_profile[profile] = 0.0
            repo.upsert_worker_runtime_state(
                profile,
                int(spec["magic"]),
                source="DEMO",
                status="RUNNING_UNIFIED",
                pid=pid,
                symbols_total=len(symbols),
                symbols_processed=0,
                current_symbol=None,
                last_action="UNIFIED_WORKER_READY",
                last_reason="v76: worker lógico dentro del proceso MultiBot",
                details={"version": DAEMONBLACKFX_VERSION, "runtime_mode": "UNIFIED_PROCESS"},
            )

        account = execution_provider.assert_demo_account()
        print(
            f"DAEMONBLACKFX VERSION: {DAEMONBLACKFX_VERSION} | "
            f"MULTIBOT UNIFICADO PID={pid} | perfiles={len(engines)}"
        )
        print(f"Cuenta DEMO: {account.get('login')} · {account.get('server')}")

        last_report = 0.0
        while True:
            now = time.monotonic()
            did_work = False

            # Las selecciones pueden cambiar desde /instruments sin reiniciar.
            for profile, engine in engines.items():
                if now < next_due.get(profile, 0.0):
                    continue
                did_work = True
                spec = BOT_PROFILES[profile]
                try:
                    symbols = _resolve_symbols_for_profile_shared(provider, repo, profile)
                    if symbols and hasattr(provider, "prepare_symbols"):
                        symbols = provider.prepare_symbols(symbols)
                    symbols_by_profile[profile] = list(symbols)

                    due_symbols = engine._selected_cycle_symbols(symbols)
                    due_symbols = engine._forex_due_symbols(due_symbols)
                    monitor = engine._monitor_break_even_positions()
                    current_audit = engine._refresh_current_strategy_views()

                    # Actualiza gráficos de auditoría sin crear otro servidor/front.
                    visual_updated = 0
                    if time.monotonic() - float(last_visual_by_profile.get(profile) or 0.0) >= 30.0:
                        try:
                            charts = engine._dashboard_chart_snapshots()
                            owned = [
                                t for t in (repo.open_trades(source="DEMO") or [])
                                if isinstance(t, dict) and engine._trade_owned_by_current_bot(t)
                            ]
                            for trade in owned:
                                trade_id = trade.get("id")
                                symbol = str(trade.get("instrument") or "")
                                chart = charts.get(symbol) or {}
                                if trade_id and chart:
                                    repo.upsert_trade_visual_audit(
                                        int(trade_id),
                                        instrument=symbol,
                                        bot_profile=profile,
                                        daemon_magic=int(spec["magic"]),
                                        broker_position_ticket=trade.get("broker_position_ticket"),
                                        latest_chart=chart,
                                        source="DEMO",
                                    )
                                    visual_updated += 1
                            last_visual_by_profile[profile] = time.monotonic()
                        except Exception as exc:
                            if args.debug:
                                print(f"[{profile}] VISUAL AUDIT ERROR: {exc}")

                    results = engine.process_symbols(
                        due_symbols,
                        sync_before_execution=True,
                    ) if due_symbols else []
                    engine._commit_forex_processed_symbols(results)

                    last_action = (
                        str((results[-1] or {}).get("action") or "WAITING")
                        if results else "WAITING_NEXT_EVENT"
                    )
                    repo.upsert_worker_runtime_state(
                        profile,
                        int(spec["magic"]),
                        source="DEMO",
                        status="RUNNING_UNIFIED",
                        pid=pid,
                        symbols_total=len(symbols),
                        symbols_processed=len(results),
                        current_symbol=None,
                        last_action=last_action,
                        last_reason="Proceso único MultiBot",
                        details={
                            "version": DAEMONBLACKFX_VERSION,
                            "runtime_mode": "UNIFIED_PROCESS",
                            "monitor": monitor,
                            "current_audit": current_audit,
                            "visual_updated": visual_updated,
                        },
                    )
                except Exception as exc:
                    repo.upsert_worker_runtime_state(
                        profile,
                        int(spec["magic"]),
                        source="DEMO",
                        status="ERROR",
                        pid=pid,
                        symbols_total=len(symbols_by_profile.get(profile) or []),
                        symbols_processed=0,
                        current_symbol=None,
                        last_action="UNIFIED_WORKER_ERROR",
                        last_reason=str(exc),
                        details={"version": DAEMONBLACKFX_VERSION, "runtime_mode": "UNIFIED_PROCESS"},
                    )
                    if args.debug:
                        print(f"[{profile}] ERROR: {exc}")

                if profile.startswith("FOREX") or profile == "GOLD":
                    delay = max(2.0, float(getattr(engine.config, "forex_event_poll_seconds", 10.0)))
                elif profile == "ORB":
                    delay = min(max(5.0, float(args.interval)), 10.0)
                else:
                    delay = max(1.0, float(args.interval))
                next_due[profile] = time.monotonic() + delay

            if time.monotonic() - last_report >= max(10.0, float(args.report_interval)):
                try:
                    reporting.export_now()
                except Exception as exc:
                    if args.debug:
                        print(f"[REPORT] {exc}")
                last_report = time.monotonic()

            if time.monotonic() - last_dashboard_heartbeat >= 2.0:
                dashboard.mark_live()
                last_dashboard_heartbeat = time.monotonic()
            if not did_work:
                time.sleep(0.25)

    except KeyboardInterrupt:
        print("MultiBot unificado detenido por el usuario.")
    finally:
        try:
            dashboard.mark_offline("MULTIBOT UNIFICADO DESCONECTADO · ESTADO PERSISTIDO")
            dashboard.stop()
        except Exception:
            pass
        try:
            provider.disconnect()
        except Exception:
            pass


def _warn_possible_parallel_daemon_instances():
    """Best-effort warning for stale DaemonBlackFx Python processes on Windows."""
    if os.name != "nt":
        return
    try:
        completed = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-CimInstance Win32_Process | "
                "Where-Object {$_.Name -eq 'python.exe' -and $_.CommandLine -match 'app.main'} | "
                "Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress"
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        raw = (completed.stdout or "").strip()
        if not raw:
            return
        import json as _json
        data = _json.loads(raw)
        rows = data if isinstance(data, list) else [data]
        rows = [r for r in rows if isinstance(r, dict)]
        current_pid = os.getpid()
        others = [r for r in rows if int(r.get("ProcessId") or -1) != current_pid]
        if others:
            print(
                "[ADVERTENCIA] Se detectaron otras instancias Python de DaemonBlackFx "
                "ejecutándose en paralelo. Esto puede aumentar CPU, lecturas MT5 y "
                "contención SQLite."
            )
            for row in others[:12]:
                print(
                    f"  PID={row.get('ProcessId')} | "
                    f"{str(row.get('CommandLine') or '')[:180]}"
                )
            print(
                "Recomendación: cerrar procesos antiguos antes de iniciar el MultiBot actual."
            )
    except Exception:
        return


class _MultiBotInstanceGuard:
    """Bloqueo atómico que permite un solo coordinador por proyecto.

    En Windows usa un mutex del sistema operativo, que desaparece incluso si el
    proceso termina abruptamente. En POSIX usa ``flock`` sobre un archivo
    persistente. El JSON es sólo diagnóstico; nunca decide por sí solo si una
    instancia está viva, por lo que un PID antiguo no bloquea el arranque.
    """

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()
        runtime_dir = self.project_root / "storage" / "runtime"
        runtime_dir.mkdir(parents=True, exist_ok=True)
        self.state_path = runtime_dir / "multi_bot_daemon.instance.json"
        identity = hashlib.sha256(str(self.project_root).lower().encode("utf-8")).hexdigest()[:20]
        self.mutex_name = f"Local\\DaemonBlackFxMultiBot_{identity}"
        self._handle = None
        self._file = None
        self._released = False

    def _owner(self):
        try:
            value = json.loads(self.state_path.read_text(encoding="utf-8"))
            return value if isinstance(value, dict) else {}
        except Exception:
            return {}

    def _already_running(self):
        owner = self._owner()
        pid = owner.get("pid") or "DESCONOCIDO"
        started_at = owner.get("started_at") or "DESCONOCIDO"
        command = owner.get("command") or ""
        raise SystemExit(
            "MULTIBOT_ALREADY_RUNNING: ya existe un coordinador activo "
            f"PID={pid} iniciado={started_at}.\n"
            f"Comando propietario: {command}\n"
            "La segunda instancia fue cancelada antes de crear workers."
        )

    def acquire(self):
        if os.name == "nt":
            import ctypes
            from ctypes import wintypes

            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel32.CreateMutexW.argtypes = (wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR)
            kernel32.CreateMutexW.restype = wintypes.HANDLE
            kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
            kernel32.CloseHandle.restype = wintypes.BOOL
            handle = kernel32.CreateMutexW(None, False, self.mutex_name)
            if not handle:
                raise OSError(ctypes.get_last_error(), "No fue posible crear el mutex MultiBot")
            if ctypes.get_last_error() == 183:  # ERROR_ALREADY_EXISTS
                kernel32.CloseHandle(handle)
                self._already_running()
            self._handle = (kernel32, handle)
        else:
            import fcntl

            lock_path = self.state_path.with_suffix(".lock")
            self._file = open(lock_path, "a+", encoding="utf-8")
            try:
                fcntl.flock(self._file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                self._file.close()
                self._file = None
                self._already_running()

        state = {
            "pid": os.getpid(),
            "started_at": datetime.now().astimezone().isoformat(),
            "project_root": str(self.project_root),
            "command": subprocess.list2cmdline(sys.argv),
            "version": DAEMONBLACKFX_VERSION,
            "active": True,
        }
        self.state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        atexit.register(self.release)
        return self

    def release(self):
        if self._released:
            return
        self._released = True
        try:
            state = self._owner()
            if int(state.get("pid") or -1) == os.getpid():
                state["active"] = False
                state["stopped_at"] = datetime.now().astimezone().isoformat()
                self.state_path.write_text(
                    json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
                )
        except Exception:
            pass
        if self._handle is not None:
            kernel32, handle = self._handle
            try:
                kernel32.CloseHandle(handle)
            except Exception:
                pass
            self._handle = None
        if self._file is not None:
            try:
                self._file.close()
            except Exception:
                pass
            self._file = None


def _acquire_multibot_instance_guard():
    guard = _MultiBotInstanceGuard(PROJECT_ROOT).acquire()
    legacy = _find_other_multibot_coordinators_windows()
    if legacy:
        # Un coordinador v89 (o anterior) no conoce el mutex de v90. El mutex
        # protege la carrera entre versiones nuevas y este segundo control
        # impide convivir con procesos heredados ya activos.
        guard.release()
        rows = "\n".join(
            f"  PID={row.get('ProcessId')} | {str(row.get('CommandLine') or '')[:220]}"
            for row in legacy
        )
        raise SystemExit(
            "MULTIBOT_LEGACY_INSTANCE_DETECTED: existe otro coordinador "
            "multi-bot-daemon que no posee el bloqueo actual.\n"
            f"{rows}\n"
            "El nuevo arranque fue cancelado antes de crear dashboard o workers. "
            "Detenga el PID anterior y vuelva a ejecutar el comando."
        )
    return guard


def _find_other_multibot_coordinators_windows():
    """Devuelve coordinadores externos, excluyendo todo el árbol lanzador actual."""
    if os.name != "nt":
        return []
    try:
        completed = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-CimInstance Win32_Process | "
                "Select-Object ProcessId,ParentProcessId,Name,CreationDate,CommandLine | "
                "ConvertTo-Json -Compress",
            ],
            capture_output=True,
            text=True,
            timeout=8,
        )
        raw = (completed.stdout or "").strip()
        if not raw:
            return []
        data = json.loads(raw)
        rows = data if isinstance(data, list) else [data]
        return _filter_external_multibot_coordinators(
            rows,
            current_pid=os.getpid(),
            parent_pid=os.getppid(),
        )
    except Exception as exc:
        # Fallar cerrado es preferible: sin esta validación podríamos volver a
        # duplicar órdenes. El mensaje permite corregir PowerShell/CIM.
        raise SystemExit(
            "MULTIBOT_INSTANCE_SCAN_FAILED: no fue posible validar procesos "
            f"multi-bot-daemon existentes ({exc}). Arranque cancelado por seguridad."
        ) from exc


def _filter_external_multibot_coordinators(rows, current_pid, parent_pid):
    """Separa coordinadores reales de los launchers del intérprete actual.

    En algunos virtualenv de Windows ``python.exe`` actúa como launcher y crea
    otro proceso Python con la misma línea de comando. Ese launcher es ancestro
    del intérprete actual, no una segunda instancia. Se reconstruye toda la
    cadena ParentProcessId antes de evaluar candidatos.
    """
    normalized = [row for row in rows if isinstance(row, dict)]
    parent_by_pid = {}
    for row in normalized:
        try:
            parent_by_pid[int(row.get("ProcessId"))] = int(row.get("ParentProcessId") or 0)
        except (TypeError, ValueError):
            continue

    own_tree = {int(current_pid), int(parent_pid)}
    pending = list(own_tree)
    while pending:
        pid = pending.pop()
        ancestor = int(parent_by_pid.get(pid) or 0)
        if ancestor > 0 and ancestor not in own_tree:
            own_tree.add(ancestor)
            pending.append(ancestor)

    external = []
    for row in normalized:
        try:
            pid = int(row.get("ProcessId") or -1)
        except (TypeError, ValueError):
            continue
        if pid in own_tree:
            continue
        name = str(row.get("Name") or "").lower()
        command = str(row.get("CommandLine") or "")
        if name not in {"python.exe", "pythonw.exe"}:
            continue
        if not re.search(r"(?:^|\s)(?:-m\s+)?app\.main(?:\s|$)", command, re.IGNORECASE):
            continue
        if not re.search(r"--mode(?:=|\s+)multi-bot-daemon(?:\s|$)", command, re.IGNORECASE):
            continue
        external.append(row)
    return external


def run_multi_bot_daemon(args, profiles=None):
    """Orquesta perfiles como procesos independientes.

    Los workers escriben sólo DB. Este coordinador es el único escritor periódico
    del XLSX consolidado para evitar colisiones entre procesos.
    """
    _warn_possible_parallel_daemon_instances()
    from reporting.trade_reporting_service import TradeReportingConfig, TradeReportingService

    logs_dir = PROJECT_ROOT / "storage" / "logs" / "bots"
    logs_dir.mkdir(parents=True, exist_ok=True)

    repo = TradingRepository()
    _assert_v53_runtime_compatibility(repo)
    _run_startup_database_maintenance(repo, args)
    reporting = TradeReportingService(
        repository=repo,
        config=TradeReportingConfig(
            source="DEMO",
            output_path=PROJECT_ROOT / "storage" / "exports" / "deriv_demo_trading_report.xlsx",
            auto_export=False,
            broker="Deriv-Demo",
        ),
    )

    profiles = tuple(profiles or FULL_MULTI_BOT_PROFILES)
    if profiles == tuple(FULL_MULTI_BOT_PROFILES):
        _assert_full_multibot_architecture(profiles)
    if profiles == tuple(SYNTHETIC_SPLIT_PROFILES):
        _assert_synthetic_split_architecture()
        # El dashboard no debe interpretar un estado persistido del antiguo
        # worker agregado como un séptimo worker activo.
        try:
            repo.upsert_worker_runtime_state(
                "SYNTHETICS",
                BOT_PROFILES["SYNTHETICS"]["magic"],
                source="DEMO",
                status="SUPERSEDED",
                pid=None,
                symbols_total=0,
                symbols_processed=0,
                current_symbol=None,
                last_action="REPLACED_BY_FAMILY_WORKERS",
                last_reason="v60: reemplazado por BOOM/CRASH/VOLATILITY/STEP/JUMP/FLIP",
                details={"version": DAEMONBLACKFX_VERSION, "legacy": True},
            )
        except Exception as exc:
            print(f"[LEGACY RUNTIME CLEANUP ERROR] SYNTHETICS: {exc}", file=sys.stderr)

    if profiles == tuple(FOREX_SPLIT_PROFILES) or all(p in profiles for p in FOREX_SPLIT_PROFILES):
        try:
            repo.upsert_worker_runtime_state(
                "FOREX",
                BOT_PROFILES["FOREX"]["magic"],
                source="DEMO",
                status="SUPERSEDED",
                pid=None,
                symbols_total=0,
                symbols_processed=0,
                current_symbol=None,
                last_action="REPLACED_BY_FOREX_SHARDS",
                last_reason="v69: reemplazado por FOREX_1/FOREX_2/FOREX_3/FOREX_4",
                details={"version": DAEMONBLACKFX_VERSION, "legacy": True},
            )
        except Exception as exc:
            print(f"[LEGACY RUNTIME CLEANUP ERROR] FOREX: {exc}", file=sys.stderr)

    if all(p in profiles for p in VOLATILITY_SHARD_PROFILES):
        try:
            repo.upsert_worker_runtime_state(
                "VOLATILITY",
                BOT_PROFILES["VOLATILITY"]["magic"],
                source="DEMO",
                status="SUPERSEDED",
                pid=None,
                symbols_total=0,
                symbols_processed=0,
                current_symbol=None,
                last_action="REPLACED_BY_VOLATILITY_SHARDS",
                last_reason="v99: reemplazado por VOLATILITY_1/2/3/4",
                details={"version": DAEMONBLACKFX_VERSION, "legacy": True},
            )
        except Exception as exc:
            print(f"[LEGACY RUNTIME CLEANUP ERROR] VOLATILITY: {exc}", file=sys.stderr)

    # v58: los coordinadores multi-bot siempre exponen un único dashboard central.
    # Los workers usan --coordinated-worker y no abren puertos propios.
    dashboard_service = None
    coordinator_dashboard_enabled = True
    if coordinator_dashboard_enabled:
        from dashboard.realtime_dashboard import RealtimeDashboardService

        dashboard_service = RealtimeDashboardService(
            repository=repo,
            host="127.0.0.1",
            port=int(args.dashboard_port),
        )
        try:
            catalog = _build_multi_bot_dashboard_catalog(profiles)
        except Exception as exc:
            catalog = {}
            repo.save_audit_event(
                "DASHBOARD_CATALOG_ERROR",
                source="DEMO",
                action="MULTI_BOT_CATALOG_FAILED",
                reason=str(exc),
            )

        # v82: evita workers sintéticos RUNNING con ciclos permanentes 0/0.
        _recover_empty_synthetic_selection(repo, catalog, profiles)

        # v56: el dashboard recupera SYNTHETICS / FOREX / ORB por separado.
        dashboard_service.set_instrument_catalog(catalog, selected_symbols=None)
        dashboard_url = dashboard_service.start(live=True)
        dashboard_service.update_status("COORDINADOR MULTI-BOT ACTIVO")
        print(f"Dashboard central: {dashboard_url}")
        print(f"Instrumentos: {dashboard_service.instruments_url}")
        print(f"Cuenta activa: {dashboard_service.account_url}")

    workers = {}
    log_handles = {}
    disabled_profiles = set()
    worker_lock = threading.RLock()
    shared_db_path = str(Path(repo.db_path).resolve())

    def start_worker(profile):
        with worker_lock:
            if profile in disabled_profiles:
                return False
            existing = workers.get(profile)
            if existing is not None and existing.poll() is None:
                return True
        spec = BOT_PROFILES[profile]
        worker_interval = (
            min(int(args.interval), 10)
            if str(profile).startswith("FOREX_") or str(profile) == "GOLD"
            else int(args.interval)
        )
        cmd = [
            sys.executable, "-m", "app.main",
            "--mode", spec["mode"],
            "--interval", str(worker_interval),
            "--position-monitor-interval", str(args.position_monitor_interval),
            "--risk-percent", str(args.risk_percent),
            "--min-rr", str(args.min_rr),
            "--coordinated-worker",
        ]
        if args.execute:
            cmd.append("--execute")
        if args.verbose:
            cmd.append("--verbose")
        if args.debug:
            cmd.append("--debug")

        log_path = logs_dir / f"{profile.lower()}.log"
        handle = open(log_path, "a", encoding="utf-8", buffering=1)
        worker_env = os.environ.copy()
        # v88: todos los procesos reciben la misma ruta resuelta. Así no pueden
        # crear DB distintas por cwd, usuario o una variable heredada ambigua.
        worker_env["DAEMONBLACKFX_DB_PATH"] = shared_db_path
        proc = subprocess.Popen(
            cmd,
            cwd=PROJECT_ROOT,
            stdout=handle,
            stderr=subprocess.STDOUT,
            env=worker_env,
        )
        with worker_lock:
            workers[profile] = proc
            log_handles[profile] = handle
        repo.save_audit_event(
            "BOT_WORKER_STARTED",
            source="DEMO",
            action="WORKER_STARTED",
            reason=profile,
            payload={
                "profile": profile, "pid": proc.pid, "magic": spec["magic"],
                "command": cmd, "shared_db_path": shared_db_path,
            },
        )
        try:
            repo.upsert_worker_runtime_state(
                profile,
                spec["magic"],
                source="DEMO",
                status="STARTING",
                pid=proc.pid,
                cycle_number=0,
                symbols_total=0,
                symbols_processed=0,
                last_action="WORKER_STARTED",
                last_reason=profile,
                details={
                    "command": cmd, "log_path": str(log_path),
                    "version": DAEMONBLACKFX_VERSION,
                    "shared_db_path": shared_db_path,
                    "persistence": {
                        "entry": "trade_visual_audits",
                        "timeline": "trade_audit_snapshots",
                        "runtime": "worker_runtime_states",
                    },
                },
            )
        except Exception as exc:
            print(f"[RUNTIME DB ERROR] {profile}: {exc}", file=sys.stderr)
            try:
                repo.save_audit_event(
                    "WORKER_RUNTIME_PERSIST_ERROR",
                    source="DEMO",
                    action="STARTUP_RUNTIME_FAILED",
                    reason=str(exc),
                    payload={"profile": profile, "pid": proc.pid, "magic": spec["magic"]},
                )
            except Exception:
                pass
        print(f"{profile:<10} PID={proc.pid} MAGIC={spec['magic']} LOG={log_path}")
        return True

    def set_worker_enabled(profile, enabled):
        if profile not in profiles:
            return {"ok": False, "error": f"Worker no administrado por este coordinador: {profile}"}
        with worker_lock:
            if enabled:
                disabled_profiles.discard(profile)
                started = start_worker(profile)
                action = "WORKER_REACTIVATED" if started else "WORKER_ALREADY_RUNNING"
                reason = "Reactivado desde el dashboard"
            else:
                open_positions = []
                for trade in repo.open_trades(source="DEMO") or []:
                    details = trade.get("details") if isinstance(trade, dict) else {}
                    metadata = details.get("metadata") if isinstance(details, dict) else {}
                    if str(metadata.get("bot_profile") or "").upper() == profile:
                        open_positions.append(trade)
                if open_positions:
                    return {
                        "ok": False,
                        "error": (
                            f"{profile} tiene {len(open_positions)} posición(es) abierta(s). "
                            "Ciérralas antes de detener su gestión."
                        ),
                    }
                disabled_profiles.add(profile)
                proc = workers.pop(profile, None)
                handle = log_handles.pop(profile, None)
                action = "STRATEGY_DISABLED_FROM_DASHBOARD"
                reason = "Desactivado manualmente desde el dashboard"

        if not enabled and proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
        if not enabled and handle is not None:
            handle.close()

        repo.upsert_worker_runtime_state(
            profile,
            BOT_PROFILES[profile]["magic"],
            source="DEMO",
            status="RUNNING" if enabled else "DISABLED",
            pid=(workers.get(profile).pid if enabled and workers.get(profile) is not None else None),
            last_action=action,
            last_reason=reason,
            details={"dashboard_controlled": True, "enabled": bool(enabled)},
        )
        repo.save_audit_event(
            "BOT_WORKER_CONTROL_CHANGED",
            source="DEMO",
            action=action,
            reason=profile,
            payload={"profile": profile, "enabled": bool(enabled)},
        )
        return {"ok": True, "profile": profile, "enabled": bool(enabled), "action": action}

    if dashboard_service is not None:
        dashboard_service.set_worker_controller(set_worker_enabled)

    for profile in profiles:
        start_worker(profile)

    print(f"\nDAEMONBLACKFX VERSION: {DAEMONBLACKFX_VERSION}")
    print("COORDINADOR MULTI-BOT ACTIVO")
    print("DB compartida: SQLAlchemy/SQLite WAL")
    print(f"DB persistente única: {shared_db_path}")
    print("XLSX: escritor único desde el coordinador")
    print(f"Workers: {', '.join(profiles)}")
    if profiles == tuple(SYNTHETIC_SPLIT_PROFILES):
        print("ARQUITECTURA SINTETICOS: 6 PROCESOS INDEPENDIENTES · 1 FAMILIA POR PID")
        print("PID por familia: " + " | ".join(
            f"{profile}={workers[profile].pid}" for profile in SYNTHETIC_SPLIT_PROFILES
        ))
    print("Ctrl+C detiene coordinador y todos los workers.\n")

    last_export = 0.0
    last_worker_console = 0.0
    last_audit_maintenance = time.monotonic()
    try:
        while True:
            now = time.monotonic()
            if now - last_export >= max(5, int(args.report_interval)):
                try:
                    result = reporting.export_now()
                    print(
                        f"[REPORT] trades={result.get('total_trades')} "
                        f"open={result.get('open_positions')} -> {result.get('path')}"
                    )
                except Exception as exc:
                    repo.save_audit_event(
                        "REPORT_EXPORT_ERROR",
                        source="DEMO",
                        action="MULTI_BOT_REPORT_FAILED",
                        reason=str(exc),
                    )
                last_export = now

            if now - last_audit_maintenance >= max(
                300,
                int(getattr(args, "audit_maintenance_interval", 3600)),
            ):
                try:
                    maintenance = repo.maintain_operational_audits(
                        retention_days=getattr(args, "audit_retention_days", 14),
                        max_rows=getattr(args, "audit_retention_max_rows", 250_000),
                        checkpoint_mode="PASSIVE",
                    )
                    deleted = maintenance["retention"]["deleted_total"]
                    if deleted:
                        print(f"[AUDIT RETENTION] filas operativas eliminadas={deleted}")
                except Exception as exc:
                    print(f"[AUDIT RETENTION WARNING] {exc}", file=sys.stderr)
                last_audit_maintenance = now

            if now - last_worker_console >= 10:
                try:
                    runtime_rows = {
                        row.get("bot_profile"): row
                        for row in repo.worker_runtime_states(source="DEMO")
                    }
                    print("[WORKERS] " + " | ".join(
                        (
                            f"{profile}:"
                            f"{runtime_rows.get(profile, {}).get('status', 'SIN_DB')} "
                            f"C{runtime_rows.get(profile, {}).get('cycle_number', 0)} "
                            f"{runtime_rows.get(profile, {}).get('symbols_processed', 0)}/"
                            f"{runtime_rows.get(profile, {}).get('symbols_total', 0)} "
                            f"{runtime_rows.get(profile, {}).get('current_symbol') or 'espera'}"
                        )
                        for profile in profiles
                    ))
                except Exception as exc:
                    print(f"[WORKERS DB ERROR] {exc}", file=sys.stderr)
                last_worker_console = now

            with worker_lock:
                active_workers = list(workers.items())
            for profile, proc in active_workers:
                code = proc.poll()
                if code is None:
                    try:
                        existing = {
                            row.get("bot_profile"): row
                            for row in repo.worker_runtime_states(source="DEMO")
                        }.get(profile, {})
                        repo.upsert_worker_runtime_state(
                            profile,
                            BOT_PROFILES[profile]["magic"],
                            source="DEMO",
                            status=(
                                existing.get("status")
                                if existing.get("status") in {
                                    "DEGRADED_NO_SYMBOLS",
                                    "WAITING_NEW_M5_BAR",
                                    "WAITING_NEW_M1_BAR",
                                    "WAITING_FOREX_DATA",
                                }
                                else "RUNNING"
                            ),
                            pid=proc.pid,
                            cycle_number=existing.get("cycle_number"),
                            symbols_total=existing.get("symbols_total"),
                            symbols_processed=existing.get("symbols_processed"),
                            current_symbol=existing.get("current_symbol"),
                            last_action=existing.get("last_action") or "HEARTBEAT",
                            last_reason=existing.get("last_reason") or "Proceso activo",
                            details=existing.get("details") or {"version": DAEMONBLACKFX_VERSION},
                        )
                    except Exception as exc:
                        print(f"[RUNTIME HEARTBEAT ERROR] {profile}: {exc}", file=sys.stderr)
                    continue
                if profile in disabled_profiles:
                    continue
                repo.save_audit_event(
                    "BOT_WORKER_STOPPED",
                    source="DEMO",
                    action="WORKER_EXITED",
                    reason=profile,
                    payload={"profile": profile, "exit_code": code},
                )
                try:
                    repo.upsert_worker_runtime_state(
                        profile,
                        BOT_PROFILES[profile]["magic"],
                        source="DEMO",
                        status="STOPPED",
                        last_action="WORKER_EXITED",
                        last_reason=f"exit_code={code}",
                        details={"exit_code": code},
                    )
                except Exception:
                    pass
                print(f"[WARN] {profile} terminó con código {code}. Reinicio en 5s.")
                try:
                    log_handles[profile].close()
                except Exception:
                    pass
                time.sleep(5)
                start_worker(profile)

            time.sleep(1)
    except KeyboardInterrupt:
        print("\nDeteniendo arquitectura multi-bot...")
    finally:
        for profile, proc in workers.items():
            if proc.poll() is None:
                proc.terminate()
            try:
                repo.upsert_worker_runtime_state(
                    profile,
                    BOT_PROFILES[profile]["magic"],
                    source="DEMO",
                    status="STOPPED",
                    last_action="COORDINATOR_SHUTDOWN",
                    last_reason="Detenido por coordinador",
                )
            except Exception:
                pass
        deadline = time.monotonic() + 10
        for proc in workers.values():
            remaining = max(0.1, deadline - time.monotonic())
            try:
                proc.wait(timeout=remaining)
            except Exception:
                proc.kill()
        for handle in log_handles.values():
            try:
                handle.close()
            except Exception:
                pass
        try:
            reporting.export_now()
        except Exception:
            pass
        if dashboard_service is not None:
            try:
                dashboard_service.mark_offline(
                    "COORDINADOR MULTI-BOT DETENIDO · ESTADO PERSISTIDO"
                )
                dashboard_service.stop()
            except Exception:
                pass
        print("Workers detenidos.")


def run_report_daemon(report_interval: int = 30):
    """Único escritor continuo del XLSX cuando los bots se ejecutan por separado."""
    from reporting.trade_reporting_service import TradeReportingConfig, TradeReportingService

    repo = TradingRepository()
    reporting = TradeReportingService(
        repository=repo,
        config=TradeReportingConfig(
            source="DEMO",
            output_path=PROJECT_ROOT / "storage" / "exports" / "deriv_demo_trading_report.xlsx",
            auto_export=False,
            broker="Deriv-Demo",
        ),
    )

    interval = max(5, int(report_interval))
    print("REPORTER DB -> XLSX ACTIVO")
    print(f"Intervalo: {interval}s")
    print(f"Archivo: {reporting.exporter.output_path}")
    try:
        while True:
            try:
                result = reporting.export_now()
                print(
                    f"[REPORT] trades={result.get('total_trades')} "
                    f"open={result.get('open_positions')}"
                )
            except Exception as exc:
                repo.save_audit_event(
                    "REPORT_EXPORT_ERROR",
                    source="DEMO",
                    action="REPORT_DAEMON_FAILED",
                    reason=str(exc),
                )
                print(f"[REPORT ERROR] {exc}")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("Reporter detenido por el usuario.")


def run_dashboard_only(dashboard_port: int = 8765):
    """
    Levanta únicamente la interfaz web usando SQLAlchemy + último snapshot
    persistido. No abre conexión con MetaTrader5 ni ejecuta operaciones.
    """
    from dashboard.realtime_dashboard import RealtimeDashboardService

    repo = TradingRepository()
    dashboard_service = RealtimeDashboardService(
        repository=repo,
        host="127.0.0.1",
        port=dashboard_port,
    )

    try:
        dashboard_url = dashboard_service.start(live=False)
        print("=== BLACKDAEMONFX · DASHBOARD OFFLINE ===")
        print(f"Dashboard: {dashboard_url}")
        print(f"Cuenta activa: {dashboard_service.account_url}")
        print(f"Instrumentos: {dashboard_service.instruments_url}")
        print("MT5 NO está conectado. Las posiciones OPEN provienen de SQLAlchemy.")
        print("Los precios, salud y gráficos son el último estado persistido y pueden estar desactualizados.")
        print("Presiona Ctrl+C para cerrar sólo la interfaz.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Dashboard offline detenido por el usuario.")
    finally:
        dashboard_service.mark_offline("DASHBOARD OFFLINE DETENIDO · ESTADO PERSISTIDO")
        dashboard_service.stop()


def run_reset_database(confirm: bool, force_open_trades: bool = False):
    if not confirm:
        raise SystemExit(
            "BLOQUEADO: reset-db requiere --confirm-reset-database. "
            "Detén el daemon antes de limpiar la base."
        )

    from database.database import DEFAULT_DB_PATH

    db_path = Path(DEFAULT_DB_PATH)
    backup_path = None
    repo = TradingRepository(db_path=db_path)
    if db_path.exists():
        backup_dir = PROJECT_ROOT / "database" / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"trading_bot_before_reset_{stamp}.sqlite3"
        repo.create_consistent_backup(backup_path)

    result = repo.reset_database(allow_open_trades=force_open_trades)

    print("BASE SQLALCHEMY LIMPIADA CORRECTAMENTE")
    print(f"Trades eliminados: {result['trades']}")
    print(f"Señales eliminadas: {result['signals']}")
    print(f"Snapshots de cuenta eliminados: {result['account_snapshots']}")
    print(f"Historial permanente conservado: {result.get('trade_journal_preserved', 0)} trade(s)")
    if backup_path is not None:
        print(f"Respaldo previo: {backup_path}")
    return {**result, "backup_path": str(backup_path) if backup_path else None}


def run_database_maintenance(
    *,
    confirm: bool,
    vacuum: bool,
    retention_days: int,
    max_rows: int,
):
    """Mantenimiento manual seguro para compactar una DB histórica grande."""
    if not confirm:
        raise SystemExit(
            "BLOQUEADO: db-maintenance requiere --confirm-db-maintenance y el daemon detenido."
        )
    guard = _acquire_multibot_instance_guard()
    try:
        repo = TradingRepository()
        backup = repo.create_consistent_backup()
        maintenance = repo.maintain_operational_audits(
            retention_days=retention_days,
            max_rows=max_rows,
            checkpoint_mode="TRUNCATE",
        )
        compact = repo.vacuum_database() if vacuum else None
        result = {
            "backup": backup,
            "maintenance": maintenance,
            "vacuum": compact,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        return result
    finally:
        guard.release()



def run_reset_account_stats(confirm: bool = False):
    """Reinicia la ventana estadística de Cuenta activa sin borrar el historial físico."""
    from database.database import DEFAULT_DB_PATH

    if not confirm:
        print("Se reiniciarán las estadísticas visibles de Cuenta activa.")
        print("Se conservarán las posiciones ABIERTAS, snapshots y el historial físico en SQLAlchemy.")
        print("Win Rate, cerrados, PnL, TP1/TP2, SL, BE y emergencias comenzarán desde cero.")
        try:
            answer = input("Escriba RESET para continuar: ").strip()
        except EOFError:
            raise SystemExit(
                "BLOQUEADO: no fue posible leer confirmación interactiva. "
                "Use --confirm-reset-account-stats para confirmar explícitamente."
            )
        if answer != "RESET":
            raise SystemExit("RESET CANCELADO: no se escribió RESET.")

    repo = TradingRepository(db_path=Path(DEFAULT_DB_PATH))
    result = repo.reset_account_statistics(source="DEMO", reason="CLI_MANUAL_RESET")

    print("ESTADÍSTICAS DE CUENTA ACTIVA REINICIADAS")
    print(f"Fecha de corte UTC: {result['reset_time']}")
    print(f"Posiciones abiertas conservadas: {result['open_positions_preserved']}")
    print(f"Cierres anteriores ocultos de la nueva ventana: {result['closed_rows_hidden_from_new_window']}")
    print(f"Filas históricas preservadas físicamente: {result['historical_rows_preserved']}")
    print("El historial no fue borrado; sólo se inició una nueva ventana estadística.")
    return result

def main():
    _validate_timeframes()

    parser = argparse.ArgumentParser(
        description="SMC Synthetic Bot"
    )

    parser.add_argument(
        "--mode",
        choices=[
            "collect",
            "daemon",
            "report",
            "analyze",
            "backtest",
            "demo",
            "demo-daemon",
            "live-paper",
            "live-paper-daemon",
            "demo-preflight",
            "live-demo-smoke",
            "reset-db",
            "db-maintenance",
            "reset-account-stats",
            "dashboard-only",
            "synthetic-daemon",
            "boom-daemon",
            "crash-daemon",
            "volatility-daemon",
            "volatility-1-daemon",
            "volatility-2-daemon",
            "volatility-3-daemon",
            "volatility-4-daemon",
            "step-daemon",
            "jump-daemon",
            "flip-daemon",
            "scalp-boom-daemon",
            "scalp-crash-daemon",
            "scalp-volatility-daemon",
            "scalp-step-daemon",
            "scalp-jump-daemon",
            "scalp-flip-daemon",
            "forex-daemon",
            "forex-split-daemon",
            "forex-1-daemon",
            "forex-2-daemon",
            "forex-3-daemon",
            "forex-4-daemon",
            "gold-session-daemon",
            "orb-daemon",
            "synthetics-split-daemon",
            "multi-bot-daemon",
            "unified-multibot-daemon",
            "report-daemon",
        ],
        default="collect",
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Segundos entre ciclos en modo daemon",
    )

    parser.add_argument(
        "--position-monitor-interval",
        type=int,
        default=2,
        help=(
            "Segundos entre revisiones de posiciones abiertas y Break Even "
            "en demo-daemon. Por defecto: 2."
        ),
    )

    parser.add_argument(
        "--symbol",
        default=None,
        help=(
            "Símbolo exacto o nombre resoluble por MT5. "
            "Si se omite en modos live/demo/collect, "
            "se descubren sintéticos dinámicamente."
        ),
    )

    parser.add_argument(
        "--categories",
        default=None,
        help=(
            "Categorías separadas por coma para descubrimiento dinámico. "
            "Ejemplo: boom,crash,volatility"
        ),
    )

    parser.add_argument(
        "--timeframe",
        default=TIMEFRAMES["entry"],
    )

    parser.add_argument(
        "--file",
        default=(
            "data/historical/"
            "Volatility_90_Index_M5_2026_08.csv"
        ),
    )

    parser.add_argument(
        "--confirm-live-demo",
        action="store_true",
        help="Confirmación explícita obligatoria para abrir una orden real en DEMO.",
    )

    parser.add_argument(
        "--direction",
        choices=["BUY", "SELL"],
        default="BUY",
        help="Dirección usada únicamente por live-demo-smoke.",
    )

    parser.add_argument(
        "--keep-open",
        action="store_true",
        help="En live-demo-smoke no cierra automáticamente la posición.",
    )

    parser.add_argument(
        "--execute",
        action="store_true",
        help=(
            "Permite enviar órdenes únicamente "
            "en modo DEMO."
        ),
    )

    parser.add_argument(
        "--paper-volume",
        type=float,
        default=1.0,
        help="Volumen virtual para live-paper",
    )

    parser.add_argument(
        "--live-volume",
        type=float,
        default=0.0,
        help=(
            "Volumen para live-demo-smoke. 0 = usar automáticamente "
            "el volumen mínimo permitido por el símbolo."
        ),
    )

    parser.add_argument(
        "--risk-percent",
        type=float,
        default=1.0,
    )

    parser.add_argument(
        "--min-rr",
        type=float,
        default=1.5,
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Muestra rechazos y detalles adicionales de cada símbolo.",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Muestra el diagnóstico técnico completo de cada resultado.",
    )

    parser.add_argument(
        "--dashboard",
        action="store_true",
        help="Activa interfaz web local de calidad de trades en tiempo real.",
    )

    parser.add_argument(
        "--dashboard-port",
        type=int,
        default=8765,
        help="Puerto local para --dashboard. Por defecto: 8765.",
    )

    parser.add_argument(
        "--reset-account-stats",
        action="store_true",
        help=(
            "Reinicia Win Rate y estadísticas persistentes de Cuenta activa "
            "sin borrar posiciones abiertas ni el historial físico."
        ),
    )

    parser.add_argument(
        "--confirm-reset-account-stats",
        action="store_true",
        help=(
            "Confirma reset-account-stats sin solicitar escribir RESET. "
            "Útil para scripts/automatizaciones."
        ),
    )

    parser.add_argument(
        "--confirm-reset-database",
        action="store_true",
        help="Confirmación explícita para vaciar trades, signals y account_snapshots.",
    )

    parser.add_argument(
        "--force-reset-open-trades",
        action="store_true",
        help="Permite reset-db aun si SQLite contiene trades OPEN. Usar sólo con MT5 sin posiciones activas.",
    )

    parser.add_argument(
        "--confirm-db-maintenance",
        action="store_true",
        help="Confirma retención/checkpoint y respaldo consistente con el daemon detenido.",
    )

    parser.add_argument(
        "--vacuum",
        action="store_true",
        help="En db-maintenance compacta físicamente SQLite después de crear respaldo.",
    )

    parser.add_argument(
        "--coordinated-worker",
        action="store_true",
        help=argparse.SUPPRESS,
    )

    parser.add_argument(
        "--report-interval",
        type=int,
        default=300,
        help="Segundos entre reconstrucciones del XLSX en multi-bot-daemon.",
    )

    parser.add_argument(
        "--audit-retention-days",
        type=int,
        default=14,
        help="Días de telemetría operacional a conservar; no afecta trades ni auditorías visuales.",
    )

    parser.add_argument(
        "--audit-retention-max-rows",
        type=int,
        default=250000,
        help="Máximo de eventos operacionales de alta frecuencia conservados.",
    )

    parser.add_argument(
        "--audit-maintenance-interval",
        type=int,
        default=3600,
        help="Segundos entre retención/checkpoint SQLite coordinados.",
    )

    args = parser.parse_args()

    if args.reset_account_stats or args.mode == "reset-account-stats":
        run_reset_account_stats(confirm=args.confirm_reset_account_stats)
        return

    if args.mode == "dashboard-only":
        run_dashboard_only(args.dashboard_port)
        return

    if args.mode == "reset-db":
        run_reset_database(args.confirm_reset_database, args.force_reset_open_trades)
        return

    if args.mode == "db-maintenance":
        run_database_maintenance(
            confirm=args.confirm_db_maintenance,
            vacuum=args.vacuum,
            retention_days=args.audit_retention_days,
            max_rows=args.audit_retention_max_rows,
        )
        return

    if args.mode == "report-daemon":
        run_report_daemon(args.report_interval)
        return

    # v60: cualquier entrada de daemon sintético agregado se redirige al
    # coordinador por familias. Evita volver accidentalmente al worker legacy
    # SYNTHETICS (magic 26082026) al usar comandos históricos.
    synthetic_split_modes = {
        "synthetics-split-daemon",
        "synthetic-daemon",
        "demo-daemon",
    }
    if args.mode == "multi-bot-daemon":
        if args.interval < 1 or args.position_monitor_interval < 1:
            raise SystemExit("Los intervalos deben ser >= 1 segundo.")
        # v90: el bloqueo se adquiere antes de crear dashboard, DB writer o
        # workers. Aunque Windows ejecute el comando dos veces casi al mismo
        # tiempo, sólo un coordinador puede continuar.
        instance_guard = _acquire_multibot_instance_guard()
        print(
            "[v77] MULTIBOT HÍBRIDO: workers de cálculo independientes + "
            "un único dashboard central liviano."
        )
        try:
            run_multi_bot_daemon(args, profiles=FULL_MULTI_BOT_PROFILES)
        finally:
            instance_guard.release()
        return

    if args.mode == "unified-multibot-daemon":
        if args.interval < 1 or args.position_monitor_interval < 1:
            raise SystemExit("Los intervalos deben ser >= 1 segundo.")
        print(
            "[EXPERIMENTAL] MultiBot unificado en un solo proceso. "
            "No recomendado para operación normal por latencia acumulativa."
        )
        run_unified_multibot_daemon(args, profiles=FULL_MULTI_BOT_PROFILES)
        return

    if args.mode in synthetic_split_modes:
        if args.interval < 1 or args.position_monitor_interval < 1:
            raise SystemExit("Los intervalos deben ser >= 1 segundo.")
        profiles = SYNTHETIC_SPLIT_PROFILES
        if args.mode in {"synthetic-daemon", "demo-daemon"}:
            print(
                f"[v60] {args.mode} es alias protegido de synthetics-split-daemon: "
                "se iniciarán 6 procesos por familia."
            )
        run_multi_bot_daemon(args, profiles=profiles)
        return

    if args.mode in {"forex-daemon", "forex-split-daemon"}:
        if args.interval < 1 or args.position_monitor_interval < 1:
            raise SystemExit("Los intervalos deben ser >= 1 segundo.")
        print("[v69] FOREX EVENT SCHEDULER: 4 workers independientes + caché H1/M15 + eventos M5.")
        run_multi_bot_daemon(args, profiles=FOREX_SPLIT_PROFILES)
        return

    strategy_worker_modes = {
        "boom-daemon": "BOOM",
        "crash-daemon": "CRASH",
        "volatility-daemon": "VOLATILITY",
        "volatility-1-daemon": "VOLATILITY_1",
        "volatility-2-daemon": "VOLATILITY_2",
        "volatility-3-daemon": "VOLATILITY_3",
        "volatility-4-daemon": "VOLATILITY_4",
        "step-daemon": "STEP",
        "jump-daemon": "JUMP",
        "flip-daemon": "FLIP",
        "scalp-boom-daemon": "SCALP_BOOM",
        "scalp-crash-daemon": "SCALP_CRASH",
        "scalp-volatility-daemon": "SCALP_VOLATILITY",
        "scalp-step-daemon": "SCALP_STEP",
        "scalp-jump-daemon": "SCALP_JUMP",
        "scalp-flip-daemon": "SCALP_FLIP",
        "forex-1-daemon": "FOREX_1",
        "forex-2-daemon": "FOREX_2",
        "forex-3-daemon": "FOREX_3",
        "forex-4-daemon": "FOREX_4",
        "gold-session-daemon": "GOLD",
        "orb-daemon": "ORB",
    }
    if args.mode in strategy_worker_modes:
        profile = strategy_worker_modes[args.mode]
        symbols = _resolve_live_symbols_for_profile(args, profile)
        if not symbols:
            print(f"{profile}: sin instrumentos seleccionados; worker queda activo sólo para monitor/auditoría.")
        if args.execute and symbols:
            preflight = run_demo_preflight(symbols)
            if not preflight["ready"]:
                raise SystemExit(2)
        run_demo_bot(
            symbols,
            args.timeframe,
            args.interval,
            once=False,
            execute=args.execute,
            risk_percent=args.risk_percent,
            min_rr=args.min_rr,
            verbose=args.verbose,
            debug=args.debug,
            position_monitor_interval=args.position_monitor_interval,
            dashboard=(args.dashboard and not args.coordinated_worker),
            dashboard_port=args.dashboard_port,
            bot_profile=profile,
            magic=BOT_PROFILES[profile]["magic"],
            auto_export=False,
        )
        return

    live_modes = {
        "live-paper",
        "live-paper-daemon",
        "demo",
        "demo-daemon",
        "demo-preflight",
        "live-demo-smoke",
    }

    if args.mode in live_modes:
        symbols = _resolve_live_symbols(args)

        if args.mode == "demo-preflight":
            result = run_demo_preflight(symbols)
            if not result["ready"]:
                raise SystemExit(2)

        elif args.mode == "live-demo-smoke":
            if not args.confirm_live_demo:
                raise SystemExit(
                    "BLOQUEADO: live-demo-smoke requiere --confirm-live-demo. "
                    "Esta acción abre una orden real en la cuenta DEMO."
                )
            if not args.symbol:
                raise SystemExit("live-demo-smoke requiere --symbol explícito")
            preflight = run_demo_preflight(symbols)
            if not preflight["ready"]:
                raise SystemExit(2)
            run_live_demo_smoke(
                symbol=symbols[0],
                direction=args.direction,
                volume=args.live_volume,
                auto_close=not args.keep_open,
            )

        elif args.mode == "live-paper":
            run_live_paper(
                symbols,
                args.interval,
                once=True,
                volume=args.paper_volume,
            )

        elif args.mode == "live-paper-daemon":
            run_live_paper(
                symbols,
                args.interval,
                once=False,
                volume=args.paper_volume,
            )

        elif args.mode == "demo":
            if args.execute:
                preflight = run_demo_preflight(symbols)
                if not preflight["ready"]:
                    raise SystemExit(2)
            run_demo_bot(
                symbols,
                args.timeframe,
                args.interval,
                once=True,
                execute=args.execute,
                risk_percent=args.risk_percent,
                min_rr=args.min_rr,
                verbose=args.verbose,
                debug=args.debug,
                position_monitor_interval=args.position_monitor_interval,
                dashboard=args.dashboard,
                dashboard_port=args.dashboard_port,
            )

        else:
            if args.interval < 1:
                raise SystemExit(
                    "demo-daemon requiere --interval mínimo de 1 segundo."
                )
            if args.position_monitor_interval < 1:
                raise SystemExit(
                    "--position-monitor-interval requiere un mínimo de 1 segundo."
                )
            if args.execute:
                preflight = run_demo_preflight(symbols)
                if not preflight["ready"]:
                    raise SystemExit(2)
            run_demo_bot(
                symbols,
                args.timeframe,
                args.interval,
                once=False,
                execute=args.execute,
                risk_percent=args.risk_percent,
                min_rr=args.min_rr,
                verbose=args.verbose,
                debug=args.debug,
                position_monitor_interval=args.position_monitor_interval,
                dashboard=args.dashboard,
                dashboard_port=args.dashboard_port,
            )

        return

    if args.mode == "collect":
        run_collector(
            once=True,
            symbol=args.symbol,
            categories=args.categories,
        )

    elif args.mode == "daemon":
        if args.interval < 30:
            raise ValueError(
                "El intervalo mínimo es 30 segundos."
            )

        run_collector(
            interval_seconds=args.interval,
            once=False,
            symbol=args.symbol,
            categories=args.categories,
        )

    elif args.mode == "report":
        path = export_trading_report()
        print(f"Reporte generado: {path}")

    elif args.mode == "backtest":
        symbol = _require_symbol_for_offline_mode(
            args.symbol,
            args.mode,
        )

        entries_file = Path(
            "storage/analysis"
        ) / (
            f"{symbol.replace(' ', '_')}_"
            f"{args.timeframe}_confirmations.csv"
        )

        result = run_full_backtest_pipeline(
            historical_file=args.file,
            entries_file=entries_file,
            instrument=symbol,
            timeframe=args.timeframe,
            initial_balance=1000.0,
            risk_percent=1.0,
            compound=True,
            strategy_version="smc-v1-backtest",
        )

        print("\n=== BACKTEST COMPLETO ===")
        print(f"Velas: {result['candles']}")
        print(f"Entradas: {result['entries']}")
        print(f"Operaciones: {result['trades']}")
        print(
            f"Backtest: {result['backtest_file']}"
        )
        print(
            "Money management: "
            f"{result['money_management_file']}"
        )
        print(
            "Nuevas operaciones SQLite: "
            f"{result['persistence']['import']['created']}"
        )
        print(
            f"Reporte Excel: "
            f"{result['persistence']['report']}"
        )

    else:
        symbol = _require_symbol_for_offline_mode(
            args.symbol,
            args.mode,
        )

        analyze_historical(
            symbol,
            args.timeframe,
            args.file,
        )


if __name__ == "__main__":
    main()
