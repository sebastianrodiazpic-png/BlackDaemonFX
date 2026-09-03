# Node Description Batch 2 of 56

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

- "config_instruments_instrumentmanager": "InstrumentManager" | kind=code-symbol | source=config/instruments.py:L17 | neighbors=[_MultiBotInstanceGuard, Distribuye símbolos de forma determinis…, Resuelve únicamente el universo pertene…, Descubre el catálogo completo que debe …, Restaura el catálogo sintético si su pr…, Falla temprano si la carpeta contiene m…] | lang=en
- "execution_live_paper_trading_engine_livepapertradingconfig": "LivePaperTradingConfig" | kind=code-symbol | source=strategy/execution/live_paper_trading_engine.py:L12 | neighbors=[_MultiBotInstanceGuard, Distribuye símbolos de forma determinis…, Resuelve únicamente el universo pertene…, Descubre el catálogo completo que debe …, Restaura el catálogo sintético si su pr…, Falla temprano si la carpeta contiene m…] | lang=en
- "reporting_trade_reporting_service_tradereportingconfig": "TradeReportingConfig" | kind=code-symbol | source=reporting/trade_reporting_service.py:L11 | neighbors=[_MultiBotInstanceGuard, Distribuye símbolos de forma determinis…, Resuelve únicamente el universo pertene…, Descubre el catálogo completo que debe …, Restaura el catálogo sintético si su pr…, Falla temprano si la carpeta contiene m…] | lang=en
- "services_execution_preflight_service_executionpreflightservice": "ExecutionPreflightService" | kind=code-symbol | source=services/execution_preflight_service.py:L18 | neighbors=[_MultiBotInstanceGuard, Distribuye símbolos de forma determinis…, Resuelve únicamente el universo pertene…, Descubre el catálogo completo que debe …, Restaura el catálogo sintético si su pr…, Falla temprano si la carpeta contiene m…] | lang=en
- "tests_test_risk_manager_print_section": "print_section()" | kind=code-symbol | source=tests/test_risk_manager.py:L27 | neighbors=[test_risk_manager.py, test_calculate_current_drawdown(), test_calculate_current_risk(), test_calculate_daily_loss(), test_calculate_max_loss_amount(), test_calculate_open_positions_risk()] | lang=en
- "brokers_mt5_execution_back_mt5executionprovider": "MT5ExecutionProvider" | kind=code-symbol | source=brokers/mt5_execution.back.py:L13 | neighbors=[mt5_execution.back.py, .account_info(), ._allowed_fillings(), .assert_demo_account(), .calculate_volume(), .check_market_order()] | lang=en
- "tests_test_risk_manager_print_result": "print_result()" | kind=code-symbol | source=tests/test_risk_manager.py:L33 | neighbors=[test_risk_manager.py, test_calculate_current_drawdown(), test_calculate_current_risk(), test_calculate_daily_loss(), test_calculate_open_positions_risk(), test_calculate_risk_reward()] | lang=en
- "app_main_rationale_1004": "Distribuye símbolos de forma determinista y estable entre workers." | kind=entity | source=app/main.py:L1004 | neighbors=[_stable_symbol_shard(), MT5Connector, MT5DataProvider, MT5ExecutionProvider, MT5TradeExecutor, InstrumentManager] | lang=en
- "app_main_rationale_1012": "Resuelve únicamente el universo perteneciente al bot solicitado." | kind=entity | source=app/main.py:L1012 | neighbors=[_resolve_live_symbols_for_profile(), MT5Connector, MT5DataProvider, MT5ExecutionProvider, MT5TradeExecutor, InstrumentManager] | lang=es
- "app_main_rationale_1064": "Descubre el catálogo completo que debe mostrar el dashboard coordinador." | kind=entity | source=app/main.py:L1064 | neighbors=[_build_multi_bot_dashboard_catalog(), MT5Connector, MT5DataProvider, MT5ExecutionProvider, MT5TradeExecutor, InstrumentManager] | lang=es
- "app_main_rationale_1104": "Restaura el catálogo sintético si su preferencia persistida quedó vacía." | kind=entity | source=app/main.py:L1104 | neighbors=[_recover_empty_synthetic_selection(), MT5Connector, MT5DataProvider, MT5ExecutionProvider, MT5TradeExecutor, InstrumentManager] | lang=es
- "app_main_rationale_1154": "Falla temprano si la carpeta contiene módulos de versiones mezcladas." | kind=entity | source=app/main.py:L1154 | neighbors=[_assert_v53_runtime_compatibility(), MT5Connector, MT5DataProvider, MT5ExecutionProvider, MT5TradeExecutor, InstrumentManager] | lang=en
- "app_main_rationale_1198": "Resuelve el universo de un perfil usando una conexión MT5 ya abierta." | kind=entity | source=app/main.py:L1198 | neighbors=[_resolve_symbols_for_profile_shared(), MT5Connector, MT5DataProvider, MT5ExecutionProvider, MT5TradeExecutor, InstrumentManager] | lang=es
- "app_main_rationale_1242": "Aplica retención antes de crear dashboard/workers del coordinador." | kind=entity | source=app/main.py:L1242 | neighbors=[_run_startup_database_maintenance(), MT5Connector, MT5DataProvider, MT5ExecutionProvider, MT5TradeExecutor, InstrumentManager] | lang=en
- "app_main_rationale_1269": "v76: un solo proceso con workers lógicos independientes." | kind=entity | source=app/main.py:L1269 | neighbors=[run_unified_multibot_daemon(), MT5Connector, MT5DataProvider, MT5ExecutionProvider, MT5TradeExecutor, InstrumentManager] | lang=en
- "app_main_rationale_1559": "Best-effort warning for stale DaemonBlackFx Python processes on Windows." | kind=entity | source=app/main.py:L1559 | neighbors=[_warn_possible_parallel_daemon_instance…, MT5Connector, MT5DataProvider, MT5ExecutionProvider, MT5TradeExecutor, InstrumentManager] | lang=en
- "app_main_rationale_1604": "Bloqueo atómico que permite un solo coordinador por proyecto.      En Windows us" | kind=entity | source=app/main.py:L1604 | neighbors=[_MultiBotInstanceGuard, MT5Connector, MT5DataProvider, MT5ExecutionProvider, MT5TradeExecutor, InstrumentManager] | lang=es
- "app_main_rationale_1735": "Devuelve coordinadores externos, excluyendo todo el árbol lanzador actual." | kind=entity | source=app/main.py:L1735 | neighbors=[_find_other_multibot_coordinators_windo…, MT5Connector, MT5DataProvider, MT5ExecutionProvider, MT5TradeExecutor, InstrumentManager] | lang=es
- "app_main_rationale_1772": "Separa coordinadores reales de los launchers del intérprete actual.      En algu" | kind=entity | source=app/main.py:L1772 | neighbors=[_filter_external_multibot_coordinators(), MT5Connector, MT5DataProvider, MT5ExecutionProvider, MT5TradeExecutor, InstrumentManager] | lang=es
- "app_main_rationale_1817": "Orquesta perfiles como procesos independientes.      Los workers escriben sólo D" | kind=entity | source=app/main.py:L1817 | neighbors=[run_multi_bot_daemon(), MT5Connector, MT5DataProvider, MT5ExecutionProvider, MT5TradeExecutor, InstrumentManager] | lang=es
- "app_main_rationale_2207": "Único escritor continuo del XLSX cuando los bots se ejecutan por separado." | kind=entity | source=app/main.py:L2207 | neighbors=[run_report_daemon(), MT5Connector, MT5DataProvider, MT5ExecutionProvider, MT5TradeExecutor, InstrumentManager] | lang=es
- "app_main_rationale_2247": "Levanta únicamente la interfaz web usando SQLAlchemy + último snapshot     persi" | kind=entity | source=app/main.py:L2247 | neighbors=[run_dashboard_only(), MT5Connector, MT5DataProvider, MT5ExecutionProvider, MT5TradeExecutor, InstrumentManager] | lang=en
- "app_main_rationale_2316": "Mantenimiento manual seguro para compactar una DB histórica grande." | kind=entity | source=app/main.py:L2316 | neighbors=[run_database_maintenance(), MT5Connector, MT5DataProvider, MT5ExecutionProvider, MT5TradeExecutor, InstrumentManager] | lang=es
- "app_main_rationale_2344": "Reinicia la ventana estadística de Cuenta activa sin borrar el historial físico." | kind=entity | source=app/main.py:L2344 | neighbors=[run_reset_account_stats(), MT5Connector, MT5DataProvider, MT5ExecutionProvider, MT5TradeExecutor, InstrumentManager] | lang=es
- "app_main_rationale_71": "Resuelve los símbolos después de conectar MT5.      Prioridad:       1. --symbol" | kind=entity | source=app/main.py:L71 | neighbors=[_resolve_symbols(), MT5Connector, MT5DataProvider, MT5ExecutionProvider, MT5TradeExecutor, InstrumentManager] | lang=en
- "app_main_rationale_760": "Descubre símbolos dinámicamente para modos que usan MT5.      Se crea una conexi" | kind=entity | source=app/main.py:L760 | neighbors=[_resolve_live_symbols(), MT5Connector, MT5DataProvider, MT5ExecutionProvider, MT5TradeExecutor, InstrumentManager] | lang=es
- "app_main_rationale_953": "Falla temprano si se rompe la separación 1 familia = 1 proceso." | kind=entity | source=app/main.py:L953 | neighbors=[_assert_synthetic_split_architecture(), MT5Connector, MT5DataProvider, MT5ExecutionProvider, MT5TradeExecutor, InstrumentManager] | lang=es
- "app_main_rationale_977": "Garantiza un solo coordinador con todos los workers esperados y únicos." | kind=entity | source=app/main.py:L977 | neighbors=[_assert_full_multibot_architecture(), MT5Connector, MT5DataProvider, MT5ExecutionProvider, MT5TradeExecutor, InstrumentManager] | lang=es
- "reporting_console_reporting_service_consolereportingconfig": "ConsoleReportingConfig" | kind=code-symbol | source=reporting/console_reporting_service.py:L11 | neighbors=[_MultiBotInstanceGuard, Distribuye símbolos de forma determinis…, Resuelve únicamente el universo pertene…, Descubre el catálogo completo que debe …, Restaura el catálogo sintético si su pr…, Falla temprano si la carpeta contiene m…] | lang=en
- "tests_test_realtime_dashboard": "test_realtime_dashboard.py" | kind=code-symbol | source=tests/test_realtime_dashboard.py:L1 | neighbors=[realtime_dashboard.py, Repo, test_account_api_reads_sqlalchemy_direc…, test_dashboard_account_payload_and_rout…, test_dashboard_attaches_m5_chart_and_ne…, test_dashboard_chart_controls_apply_onl…] | lang=en
- "brokers_symbol_discovery_derivsymboldiscovery": "DerivSymbolDiscovery" | kind=code-symbol | source=brokers/symbol_discovery.py:L43 | neighbors=[symbol_discovery.py, .classify_symbol(), ._ensure_connection(), .get_all_forex_symbols(), .get_all_symbols(), .get_all_synthetic_symbols()] | lang=en
- "database_database_base": "Base" | kind=code-symbol | source=database/database.py:L166 | neighbors=[database.py, AccountSnapshot, AccountStatsReset, DaemonAuditEvent, InstrumentSelectionPreference, InstrumentSelectionProfilePreference] | lang=en
- "execution_live_trading_engine_livetradingengine_process_symbol": ".process_symbol()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L3725 | neighbors=[LiveTradingEngine, ._account_and_guard(), ._execution_key(), ._forex_rollover_entry_gate(), ._gold_smc_entry_gate(), ._gold_smc_exposure_open()] | lang=en
- "app_main_main": "main()" | kind=code-symbol | source=app/main.py:L2372 | neighbors=[main.py, _acquire_multibot_instance_guard(), analyze_historical(), .release(), _require_symbol_for_offline_mode(), _resolve_live_symbols()] | lang=en
- "position_manager_positionmanager": "PositionManager" | kind=code-symbol | source=position_manager.py:L8 | neighbors=[PaperTradeExecutor, Ejecuta operaciones virtuales.      No …, PositionMonitoringService, Procesa las posiciones abiertas que ten…, Vigila las posiciones abiertas administ…, Procesa un único tick/precio para una p…] | lang=en
- "risk_risk_manager": "risk_manager.py" | kind=code-symbol | source=strategy/risk/risk_manager.py:L1 | neighbors=[calculate_current_drawdown(), calculate_current_risk(), calculate_daily_loss(), calculate_max_loss_amount(), calculate_open_positions_risk(), calculate_risk_reward()] | lang=en
- "tests_test_position_manager": "test_position_manager.py" | kind=code-symbol | source=tests/test_position_manager.py:L1 | neighbors=[position_manager.py, create_buy_position(), create_sell_position(), test_apply_break_even_buy_at_one_to_one…, test_apply_break_even_sell_at_one_to_on…, test_break_even_cannot_be_applied_twice…] | lang=en
- "database_database": "database.py" | kind=code-symbol | source=database/database.py:L1 | neighbors=[backup_sqlite_database(), Base, _bootstrap_stable_database(), database_diagnostics(), _ensure_performance_indexes(), _ensure_trade_columns()] | lang=en
- "database_models": "models.py" | kind=code-symbol | source=database/models.py:L1 | neighbors=[database.py, AccountSnapshot, AccountStatsReset, DaemonAuditEvent, InstrumentSelectionPreference, InstrumentSelectionProfilePreference] | lang=en
- "execution_runner_extension_manager_runnerextensiondecision": "RunnerExtensionDecision" | kind=code-symbol | source=strategy/execution/runner_extension_manager.py:L13 | neighbors=[runner_extension_manager.py, evaluate_runner_continuation(), PositionExecutor, Provider, Repo, TradeExecutor] | lang=en

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-001.json

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
