# Node Description Batch 3 of 56

Graphify is running in assistant/skill mode (no API key). You are the host
assistant (Claude Code / Codex / Gemini CLI). Read the prompt below and write
your JSON answer to the answer file.

## Prompt

You are documenting nodes in a knowledge graph.
For each entry below, write ONE concise factual plain-language sentence
describing what it is or does. Use only the provided context.
For a code symbol (kind=code-symbol — a function, class, or constant),
describe what the function/symbol does based on its name, source location
and neighbors — e.g. "Resolves the configured ontology profile from graphify.yaml.".
For an entity node (any other kind — e.g. a person, place, event, object),
describe what the entity is and its role, grounded in its type, its
relations (neighbors) and the provided citations/evidence — e.g.
"Lady Carfax, a wealthy heiress who disappears en route to Lausanne.".
Ground entity descriptions in the citations/evidence when present; do not
speculate beyond the context, so a node with no supporting context may be
left out of the reply.
LANGUAGE: each entry has a `lang=` marker giving the language of its source.
Write that entry's description in EXACTLY that language. Do not translate to
a single common language — match each node's source language individually.
No marketing language.
Respond ONLY with a JSON object mapping each node id (as a string) to its
one-sentence description — no prose, no markdown fences.

- "reporting_trade_audit_excel_exporter_tradeauditexcelexporter": "TradeAuditExcelExporter" | kind=code-symbol | source=reporting/trade_audit_excel_exporter.py:L11 | neighbors=[Recarga selecciones autoritativas desde…, Normaliza eventos persistidos para que …, Evalúa la salud de una posición abierta…, Publica un dashboard local de sólo lect…, Detalle completo de un trade y TODOS su…, RealtimeDashboardService] | lang=en
- "tests_test_realtime_dashboard_repo": "Repo" | kind=code-symbol | source=tests/test_realtime_dashboard.py:L4 | neighbors=[test_realtime_dashboard.py, RealtimeDashboardService, TradingRepository, .open_trades(), test_dashboard_attaches_m5_chart_and_ne…, test_dashboard_chart_controls_apply_onl…] | lang=en
- "tests_test_trade_lifecycle_manager": "test_trade_lifecycle_manager.py" | kind=code-symbol | source=tests/test_trade_lifecycle_manager.py:L1 | neighbors=[create_ambiguous_result(), create_candles(), create_controlled_simulator(), create_expired_result(), create_loss_result(), create_signal()] | lang=en
- "brokers_mt5_execution_mt5executionprovider_ensure": "._ensure()" | kind=code-symbol | source=brokers/mt5_execution.py:L38 | neighbors=[MT5ExecutionProvider, .account_info(), .calculate_margin_amount(), .calculate_risk_amount(), .calculate_volume(), .check_market_order()] | lang=en
- "dashboard_realtime_dashboard_now_iso": "_now_iso()" | kind=code-symbol | source=dashboard/realtime_dashboard.py:L262 | neighbors=[realtime_dashboard.py, .cycle_end(), .cycle_start(), .__init__(), ._load_persisted_state(), .mark_live()] | lang=en
- "database_repository_tradingrepository_dt": "._dt()" | kind=code-symbol | source=database/repository.py:L52 | neighbors=[Convierte distintos formatos de fecha a…, TradingRepository, .account_trade_history_dataframe(), .import_backtest_dataframe(), .import_mt5_trade_history(), .save_account_snapshot()] | lang=en
- "execution_live_trading_engine_livetradingengine_monitor_break_even_positions": "._monitor_break_even_positions()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L2637 | neighbors=[LiveTradingEngine, ._analysis_invalidation_exit(), ._arps_time_stop_exit(), ._break_even_initial_stop(), ._break_even_price_tolerance(), ._break_even_target_stop()] | lang=en
- "risk_risk_manager_evaluate_trade_risk": "evaluate_trade_risk()" | kind=code-symbol | source=strategy/risk/risk_manager.py:L1225 | neighbors=[risk_manager.py, evaluate_risk(), calculate_current_risk(), calculate_open_positions_risk(), check_daily_loss_limit(), check_drawdown_limit()] | lang=en
- "tests_test_risk_integration": "test_risk_integration.py" | kind=code-symbol | source=tests/test_risk_integration.py:L1 | neighbors=[assert_result(), print_result(), print_section(), run_all_tests(), test_consecutive_losses(), test_daily_loss_limit()] | lang=en
- "tests_test_v69_forex_event_scheduler": "test_v69_forex_event_scheduler.py" | kind=code-symbol | source=tests/test_v69_forex_event_scheduler.py:L1 | neighbors=[main.py, CandleProvider, _event_engine(), ExposureRepo, test_forex_currency_exposure_blocks_thi…, test_forex_event_scheduler_only_release…] | lang=en
- "trade_lifecycle_manager_tradelifecycle": "TradeLifecycle" | kind=code-symbol | source=trade_lifecycle_manager.py:L56 | neighbors=[Analyzer, ExecutionRepo, Executor, FakeEngine, FakeLifecycleManager, FakeReporting] | lang=en
- "execution_multi_timeframe_multitimeframeanalyzer_analyze_symbol": ".analyze_symbol()" | kind=code-symbol | source=strategy/execution/multi_timeframe.py:L860 | neighbors=[MultiTimeframeAnalyzer, ._add_transition(), ._as_time(), ._build_result(), ._get_h1_context(), ._get_stage_result()] | lang=en
- "execution_trade_executor_tradeexecutor": "TradeExecutor" | kind=code-symbol | source=strategy/execution/trade_executor.py:L207 | neighbors=[MT5TradeExecutor, Modifica el Stop Loss de una posición r…, Adaptador del proveedor MT5 al contrato…, PaperTradeExecutor, Ejecuta operaciones virtuales.      No …, trade_executor.py] | lang=en
- "tests_test_live_demo": "test_live_demo.py" | kind=code-symbol | source=tests/test_live_demo.py:L1 | neighbors=[mt5_connector.py, mt5_data.py, symbol_discovery.py, repository.py, get_analysis(), get_diagnostics()] | lang=en
- "tests_test_position_manager_create_buy_position": "create_buy_position()" | kind=code-symbol | source=tests/test_position_manager.py:L10 | neighbors=[test_position_manager.py, test_apply_break_even_buy_at_one_to_one…, test_break_even_cannot_be_applied_twice…, test_break_even_is_not_activated_before…, test_cannot_close_position_twice(), test_clear_all()] | lang=en
- "tests_test_v100_entry_quarantine_winrate": "test_v100_entry_quarantine_winrate.py" | kind=code-symbol | source=tests/test_v100_entry_quarantine_winrate.py:L1 | neighbors=[account_metrics.py, _Analyzer, _m5_data(), _MinimumVolumeExecutor, _Provider, _Repo] | lang=en
- "brokers_mt5_execution_back_mt5executionprovider_ensure": "._ensure()" | kind=code-symbol | source=brokers/mt5_execution.back.py:L23 | neighbors=[MT5ExecutionProvider, .account_info(), .calculate_volume(), .check_market_order(), .ensure_symbol(), .find_position_ticket()] | lang=en
- "brokers_mt5_execution_mt5executionprovider_place_market_order": ".place_market_order()" | kind=code-symbol | source=brokers/mt5_execution.py:L1044 | neighbors=[MT5ExecutionProvider, MT5ExecutionError, ._build_market_request_base(), ._current_market_price(), ._ensure(), ._filling_name()] | lang=en
- "database_database_rationale_106": "Recupera automáticamente la DB histórica sólo si la estable está vacía.      Ele" | kind=entity | source=database/database.py:L106 | neighbors=[_bootstrap_stable_database(), AccountSnapshot, AccountStatsReset, DaemonAuditEvent, InstrumentSelectionPreference, InstrumentSelectionProfilePreference] | lang=en
- "database_database_rationale_16": "Directorio persistente independiente de la carpeta de versión." | kind=entity | source=database/database.py:L16 | neighbors=[_stable_data_dir(), AccountSnapshot, AccountStatsReset, DaemonAuditEvent, InstrumentSelectionPreference, InstrumentSelectionProfilePreference] | lang=nl
- "database_database_rationale_261": "Índices compatibles con instalaciones existentes y alta concurrencia." | kind=entity | source=database/database.py:L261 | neighbors=[_ensure_performance_indexes(), AccountSnapshot, AccountStatsReset, DaemonAuditEvent, InstrumentSelectionPreference, InstrumentSelectionProfilePreference] | lang=es
- "database_database_rationale_33": "(trade_journal, trades, account_snapshots, total) sin modificar el archivo." | kind=entity | source=database/database.py:L33 | neighbors=[_sqlite_activity_score(), AccountSnapshot, AccountStatsReset, DaemonAuditEvent, InstrumentSelectionPreference, InstrumentSelectionProfilePreference] | lang=es
- "database_database_rationale_54": "Busca bases de versiones hermanas sin recorrer el disco completo." | kind=entity | source=database/database.py:L54 | neighbors=[_legacy_candidates(), AccountSnapshot, AccountStatsReset, DaemonAuditEvent, InstrumentSelectionPreference, InstrumentSelectionProfilePreference] | lang=en
- "database_database_rationale_70": "Crea una copia consistente que incorpora WAL mediante la API de SQLite." | kind=entity | source=database/database.py:L70 | neighbors=[backup_sqlite_database(), AccountSnapshot, AccountStatsReset, DaemonAuditEvent, InstrumentSelectionPreference, InstrumentSelectionProfilePreference] | lang=es
- "database_repository_rationale_1027": "Append-only: una fila por observación Entrada vs. Ahora." | kind=entity | source=database/repository.py:L1027 | neighbors=[AccountSnapshot, AccountStatsReset, DaemonAuditEvent, InstrumentSelectionPreference, InstrumentSelectionProfilePreference, PositionVisualAudit] | lang=es
- "database_repository_rationale_112": "Convierte un valor a entero o devuelve None." | kind=entity | source=database/repository.py:L112 | neighbors=[AccountSnapshot, AccountStatsReset, DaemonAuditEvent, InstrumentSelectionPreference, InstrumentSelectionProfilePreference, PositionVisualAudit] | lang=pt
- "database_repository_rationale_1132": "Último SYMBOL_PROCESS_RESULT por bot_profile desde auditoría append-only." | kind=entity | source=database/repository.py:L1132 | neighbors=[AccountSnapshot, AccountStatsReset, DaemonAuditEvent, InstrumentSelectionPreference, InstrumentSelectionProfilePreference, PositionVisualAudit] | lang=pt
- "database_repository_rationale_1227": "Panel equilibrado de análisis recientes de todos los workers.          Un ORB es" | kind=entity | source=database/repository.py:L1227 | neighbors=[AccountSnapshot, AccountStatsReset, DaemonAuditEvent, InstrumentSelectionPreference, InstrumentSelectionProfilePreference, PositionVisualAudit] | lang=en
- "database_repository_rationale_1296": "Último análisis persistido del símbolo, independiente del dashboard local." | kind=entity | source=database/repository.py:L1296 | neighbors=[AccountSnapshot, AccountStatsReset, DaemonAuditEvent, InstrumentSelectionPreference, InstrumentSelectionProfilePreference, PositionVisualAudit] | lang=en
- "database_repository_rationale_133": "Convierte a float.         Si falla, devuelve default." | kind=entity | source=database/repository.py:L133 | neighbors=[AccountSnapshot, AccountStatsReset, DaemonAuditEvent, InstrumentSelectionPreference, InstrumentSelectionProfilePreference, PositionVisualAudit] | lang=pt
- "database_repository_rationale_1334": "Clave estable para que un mismo trade no se duplique al reiniciar." | kind=entity | source=database/repository.py:L1334 | neighbors=[AccountSnapshot, AccountStatsReset, DaemonAuditEvent, InstrumentSelectionPreference, InstrumentSelectionProfilePreference, PositionVisualAudit] | lang=es
- "database_repository_rationale_1377": "Copia al journal cualquier trade operativo previo que aún no esté archivado." | kind=entity | source=database/repository.py:L1377 | neighbors=[AccountSnapshot, AccountStatsReset, DaemonAuditEvent, InstrumentSelectionPreference, InstrumentSelectionProfilePreference, PositionVisualAudit] | lang=en
- "database_repository_rationale_1402": "Devuelve la marca persistente más reciente para reiniciar estadísticas." | kind=entity | source=database/repository.py:L1402 | neighbors=[AccountSnapshot, AccountStatsReset, DaemonAuditEvent, InstrumentSelectionPreference, InstrumentSelectionProfilePreference, PositionVisualAudit] | lang=es
- "database_repository_rationale_1425": "Inicia una nueva ventana estadística sin borrar trades ni posiciones abiertas." | kind=entity | source=database/repository.py:L1425 | neighbors=[AccountSnapshot, AccountStatsReset, DaemonAuditEvent, InstrumentSelectionPreference, InstrumentSelectionProfilePreference, PositionVisualAudit] | lang=en
- "database_repository_rationale_1471": "Historial DB-only usado por Cuenta activa.          Conserva sólo filas originad" | kind=entity | source=database/repository.py:L1471 | neighbors=[AccountSnapshot, AccountStatsReset, DaemonAuditEvent, InstrumentSelectionPreference, InstrumentSelectionProfilePreference, PositionVisualAudit] | lang=en
- "database_repository_rationale_1524": "Persiste la selección completa de instrumentos como preferencia de usuario." | kind=entity | source=database/repository.py:L1524 | neighbors=[AccountSnapshot, AccountStatsReset, DaemonAuditEvent, InstrumentSelectionPreference, InstrumentSelectionProfilePreference, PositionVisualAudit] | lang=en
- "database_repository_rationale_157": "Convierte texto a MAYÚSCULAS." | kind=entity | source=database/repository.py:L157 | neighbors=[AccountSnapshot, AccountStatsReset, DaemonAuditEvent, InstrumentSelectionPreference, InstrumentSelectionProfilePreference, PositionVisualAudit] | lang=pt
- "database_repository_rationale_1587": "Guarda una única selección autoritativa por perfil.          v57 elimina ambigüe" | kind=entity | source=database/repository.py:L1587 | neighbors=[AccountSnapshot, AccountStatsReset, DaemonAuditEvent, InstrumentSelectionPreference, InstrumentSelectionProfilePreference, PositionVisualAudit] | lang=es
- "database_repository_rationale_1680": "Recupera la última selección persistida; None si nunca se guardó." | kind=entity | source=database/repository.py:L1680 | neighbors=[AccountSnapshot, AccountStatsReset, DaemonAuditEvent, InstrumentSelectionPreference, InstrumentSelectionProfilePreference, PositionVisualAudit] | lang=es
- "database_repository_rationale_173": "Limpia valores provenientes de pandas / numpy." | kind=entity | source=database/repository.py:L173 | neighbors=[AccountSnapshot, AccountStatsReset, DaemonAuditEvent, InstrumentSelectionPreference, InstrumentSelectionProfilePreference, PositionVisualAudit] | lang=nl

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-002.json

Keep each description factual and concise (one sentence). No markdown, no prose
outside the JSON object. It is acceptable to omit a node if context is
insufficient — but include every node you can ground confidently.

Example answer format:
```json
{
  "node_id_1": "Resolves the configured ontology profile from graphify.yaml.",
  "node_id_2": "Colonel James Barclay, an antagonist in The Crooked Man."
}
```
