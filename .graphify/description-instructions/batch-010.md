# Node Description Batch 11 of 56

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
Write every description in Portuguese (pt). Do not switch languages.
No marketing language.
Respond ONLY with a JSON object mapping each node id (as a string) to its
one-sentence description — no prose, no markdown fences.

- "trade_outcome_policy": "trade_outcome_policy.py" | kind=code-symbol | source=trade_outcome_policy.py:L1 | neighbors=[account_metrics.py, repository.py, trade_report_exporter.py, test_v48_break_even_winrate.py, decisive_outcome(), is_break_even_rr()]
- "backtesting_backtest_pipeline": "backtest_pipeline.py" | kind=code-symbol | source=backtesting/backtest_pipeline.py:L1 | neighbors=[main.py, backtest_money_management.py, run_full_backtest_pipeline(), backtest_storage.py, trade_simulator.py, test_full_backtest_pipeline.py]
- "backtesting_backtest_storage": "backtest_storage.py" | kind=code-symbol | source=backtesting/backtest_storage.py:L1 | neighbors=[backtest_pipeline.py, persist_money_management_results(), reporting.py, repository.py, test_backtest_money_management.py, test_backtest_storage.py]
- "brokers_mt5_connector": "mt5_connector.py" | kind=code-symbol | source=brokers/mt5_connector.py:L1 | neighbors=[mt5_connection.py, MT5Connector, mt5_data.py, test_deriv_symbols.py, test_live_demo.py, test_live_demo_origin.py]
- "brokers_mt5_data": "mt5_data.py" | kind=code-symbol | source=brokers/mt5_data.py:L1 | neighbors=[mt5_connector.py, MT5DataProvider, test_live_demo.py, test_live_demo_origin.py, test_mt5_connection.py, test_mt5_data.py]
- "brokers_mt5_execution_back_mt5executionprovider_normalize_market_stops": ".normalize_market_stops()" | kind=code-symbol | source=brokers/mt5_execution.back.py:L417 | neighbors=[MT5ExecutionProvider, ._ensure(), ._minimum_stop_distance(), ._normalize_price(), .symbol_spec(), Adapta SL/TP al precio actual y a la di…]
- "brokers_mt5_execution_back_mt5executionprovider_normalize_price": "._normalize_price()" | kind=code-symbol | source=brokers/mt5_execution.back.py:L231 | neighbors=[MT5ExecutionProvider, .check_market_order(), .normalize_market_stops(), ._price_decimals(), ._normalize_stops(), .place_market_order()]
- "brokers_mt5_execution_back_mt5executionprovider_normalize_stops": "._normalize_stops()" | kind=code-symbol | source=brokers/mt5_execution.back.py:L244 | neighbors=[MT5ExecutionProvider, .check_market_order(), MT5ExecutionError, ._minimum_stop_distance(), ._normalize_price(), .place_market_order()]
- "brokers_mt5_execution_mt5executionprovider_get_filling_diagnostics": ".get_filling_diagnostics()" | kind=code-symbol | source=brokers/mt5_execution.py:L396 | neighbors=[MT5ExecutionProvider, ._filling_name(), ._symbol_filling_candidates(), .symbol_spec(), ._run_order_check_with_fallback(), Expone cómo MT5 informa los filling mod…]
- "brokers_mt5_execution_mt5executionprovider_modify_position_stops": ".modify_position_stops()" | kind=code-symbol | source=brokers/mt5_execution.py:L1177 | neighbors=[MT5ExecutionProvider, ._ensure(), .get_position(), ._normalize_price(), .symbol_spec(), Modifica SL/TP de una posición abierta …]
- "brokers_mt5_execution_mt5executionprovider_order_check_safe": "._order_check_safe()" | kind=code-symbol | source=brokers/mt5_execution.py:L472 | neighbors=[MT5ExecutionProvider, ._last_error_is_invalid_comment(), ._sanitize_comment(), .place_market_order(), ._run_order_check_with_fallback(), Ejecuta order_check y, si el binding re…]
- "brokers_symbol_discovery": "symbol_discovery.py" | kind=code-symbol | source=brokers/symbol_discovery.py:L1 | neighbors=[DerivSymbolDiscovery, _looks_like_forex_name(), instruments.py, test_live_demo.py, test_live_demo_origin.py, test_v45_forex_instrument_catalog.py]
- "brokers_symbol_discovery_derivsymboldiscovery_ensure_connection": "._ensure_connection()" | kind=code-symbol | source=brokers/symbol_discovery.py:L48 | neighbors=[DerivSymbolDiscovery, .get_all_forex_symbols(), .get_all_symbols(), .get_symbol_info(), .get_tradeable_forex(), .is_forex_symbol()]
- "dashboard_realtime_dashboard_catalog_symbols_by_profile": "_catalog_symbols_by_profile()" | kind=code-symbol | source=dashboard/realtime_dashboard.py:L242 | neighbors=[realtime_dashboard.py, _normalize_symbol_list(), _selection_profile_for_category(), ._refresh_selection_profiles_from_db_lo…, .set_instrument_catalog(), .update_selected_symbols()]
- "dashboard_realtime_dashboard_normalize_symbol_list": "_normalize_symbol_list()" | kind=code-symbol | source=dashboard/realtime_dashboard.py:L249 | neighbors=[realtime_dashboard.py, _catalog_symbols_by_profile(), .get_selected_symbols(), ._refresh_selection_profiles_from_db_lo…, .set_instrument_catalog(), .update_selected_symbols()]
- "dashboard_realtime_dashboard_position_health": "_position_health()" | kind=code-symbol | source=dashboard/realtime_dashboard.py:L420 | neighbors=[realtime_dashboard.py, _confirmed_decision(), _divergence_direction(), _quality_grade(), Evalúa la salud de una posición abierta…, ._refresh_open_positions_locked()]
- "dashboard_realtime_dashboard_realtimedashboardservice_cycle_end": ".cycle_end()" | kind=code-symbol | source=dashboard/realtime_dashboard.py:L1352 | neighbors=[RealtimeDashboardService, _now_iso(), ._persist_state_locked(), ._refresh_account_locked(), ._refresh_open_positions_locked(), ._touch_live_locked()]
- "dashboard_realtime_dashboard_realtimedashboardservice_cycle_start": ".cycle_start()" | kind=code-symbol | source=dashboard/realtime_dashboard.py:L1296 | neighbors=[RealtimeDashboardService, _now_iso(), ._persist_state_locked(), ._refresh_account_locked(), ._refresh_open_positions_locked(), ._touch_live_locked()]
- "dashboard_realtime_dashboard_realtimedashboardservice_refresh_selection_profiles_from_db_locked": "._refresh_selection_profiles_from_db_locked()" | kind=code-symbol | source=dashboard/realtime_dashboard.py:L1676 | neighbors=[Recarga selecciones autoritativas desde…, RealtimeDashboardService, ._cached_instruments_payload(), _catalog_symbols_by_profile(), _normalize_symbol_list(), _now_iso()]
- "dashboard_realtime_dashboard_realtimedashboardservice_touch_live_locked": "._touch_live_locked()" | kind=code-symbol | source=dashboard/realtime_dashboard.py:L1289 | neighbors=[RealtimeDashboardService, .cycle_end(), .cycle_start(), .monitor_result(), .symbol_start(), _now_iso()]
- "dashboard_realtime_dashboard_realtimedashboardservice_update_selected_symbols": ".update_selected_symbols()" | kind=code-symbol | source=dashboard/realtime_dashboard.py:L1228 | neighbors=[RealtimeDashboardService, _catalog_symbols_by_profile(), _normalize_symbol_list(), _now_iso(), ._invalidate_navigation_caches(), ._persist_state_locked()]
- "database_database_bootstrap_stable_database": "_bootstrap_stable_database()" | kind=code-symbol | source=database/database.py:L105 | neighbors=[database.py, backup_sqlite_database(), _legacy_candidates(), _sqlite_activity_score(), Recupera automáticamente la DB históric…, resolve_db_path()]
- "database_repository_tradingrepository_float_or_none": "._float_or_none()" | kind=code-symbol | source=database/repository.py:L82 | neighbors=[Convierte un valor a float o devuelve N…, TradingRepository, ._trade_kwargs(), .update_trade(), ._upsert_trade_journal_session(), .upsert_worker_runtime_state()]
- "database_repository_tradingrepository_num": "._num()" | kind=code-symbol | source=database/repository.py:L132 | neighbors=[Convierte a float.         Si falla, de…, TradingRepository, .import_backtest_dataframe(), .import_mt5_trade_history(), .save_account_snapshot(), ._upsert_trade_journal_session()]
- "execution_live_trading_engine_livetradingengine_prepare_orb_gold_selection": "._prepare_orb_gold_selection()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L3276 | neighbors=[LiveTradingEngine, ._account_and_guard(), ._evaluate_orb_gold_contract(), ._orb_session_is_active(), .process_symbols(), Selecciona un solo contrato de Oro para…]
- "execution_live_trading_engine_livetradingengine_quarantine_symbol": "._quarantine_symbol()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L570 | neighbors=[LiveTradingEngine, .process_symbol(), ._load_quarantine_unlocked(), ._quarantine_storage_lock(), ._recoverable_quarantine_details(), ._save_quarantine_unlocked()]
- "execution_live_trading_engine_livetradingengine_refresh_current_strategy_views": "._refresh_current_strategy_views()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L5119 | neighbors=[LiveTradingEngine, ._current_strategy_view_from_analysis(), ._orb_higher_timeframe_context(), ._persist_audit_event(), ._trade_owned_by_current_bot(), Reanaliza posiciones abiertas y persist…]
- "execution_multi_timeframe_multitimeframeanalyzer_as_time": "._as_time()" | kind=code-symbol | source=strategy/execution/multi_timeframe.py:L289 | neighbors=[MultiTimeframeAnalyzer, .analyze_symbol(), ._get_h1_context(), ._pipeline_diagnostics(), ._select_ordered_pair(), ._signal_age_diagnostics()]
- "execution_multi_timeframe_multitimeframeanalyzer_get_stage_result": "._get_stage_result()" | kind=code-symbol | source=strategy/execution/multi_timeframe.py:L159 | neighbors=[MultiTimeframeAnalyzer, .analyze_symbol(), ._get_closed_candles(), ._next_refresh_at(), ._run_pipeline(), Obtiene una etapa H1/M15/M5 usando cach…]
- "execution_paper_trade_executor_rationale_22": "Ejecuta operaciones virtuales.      No envía órdenes al broker.      Característ" | kind=entity | source=strategy/execution/paper_trade_executor.py:L22 | neighbors=[PaperTradeExecutor, TradeExecutionRequest, TradeExecutionResult, TradeExecutor, PositionMonitoringService, PositionManager]
- "execution_trade_pipeline_run_trade_pipeline": "run_trade_pipeline()" | kind=code-symbol | source=strategy/execution/trade_pipeline.py:L198 | neighbors=[trade_pipeline.py, Ejecuta la cadena SMC completa. Si symb…, build_setups(), _filter_by_policy(), PipelineConfig, _validate_price_data()]
- "orb_new_york_orb_classify_orb_market": "classify_orb_market()" | kind=code-symbol | source=strategy/orb/new_york_orb.py:L19 | neighbors=[new_york_orb.py, _norm_symbol(), is_orb_eligible_symbol(), is_orb_gold_symbol(), .analyze_symbol(), Clasifica únicamente los contratos ORB …]
- "orb_new_york_orb_newyorkorbstrategy_analyze_symbol": ".analyze_symbol()" | kind=code-symbol | source=strategy/orb/new_york_orb.py:L265 | neighbors=[NewYorkORBStrategy, classify_orb_market(), ._prepare_candles(), ._session_bounds(), ._session_poc(), ._session_vwap()]
- "position_manager": "position_manager.py" | kind=code-symbol | source=position_manager.py:L1 | neighbors=[paper_trade_executor.py, position_monitoring_service.py, PositionManager, test_paper_trade_monitoring_integration…, test_position_manager.py, test_position_monitoring_service.py]
- "reporting_console_reporting_service_consolereportingservice_print_result": ".print_result()" | kind=code-symbol | source=reporting/console_reporting_service.py:L350 | neighbors=[ConsoleReportingService, ._label(), ._print_confirmation_diag(), .print_debug(), ._print_trade_fields(), ._reason()]
- "reporting_trade_reporting_service_tradereportingservice_build_open_data": "._build_open_data()" | kind=code-symbol | source=reporting/trade_reporting_service.py:L190 | neighbors=[TradeReportingService, ._broker(), ._build_details(), ._execution_key(), ._volume(), ._ensure_open_trade()]
- "reporting_trade_reporting_service_tradereportingservice_find_trade_id": "._find_trade_id()" | kind=code-symbol | source=reporting/trade_reporting_service.py:L280 | neighbors=[TradeReportingService, ._close_trade(), ._execution_key(), ._lookup_keys(), ._remember_trade(), ._sync_open_trade()]
- "reporting_trade_reporting_service_tradereportingservice_on_lifecycle_event": ".on_lifecycle_event()" | kind=code-symbol | source=reporting/trade_reporting_service.py:L62 | neighbors=[TradeReportingService, ._audit_lifecycle_event(), ._close_trade(), ._ensure_open_trade(), ._export_if_enabled(), ._sync_open_trade()]
- "reporting_trade_reporting_service_tradereportingservice_remember_trade": "._remember_trade()" | kind=code-symbol | source=reporting/trade_reporting_service.py:L303 | neighbors=[TradeReportingService, ._close_trade(), ._ensure_open_trade(), ._find_trade_id(), ._lookup_keys(), ._sync_open_trade()]
- "reporting_trade_reporting_service_tradereportingservice_sync_open_trade": "._sync_open_trade()" | kind=code-symbol | source=reporting/trade_reporting_service.py:L136 | neighbors=[TradeReportingService, .on_lifecycle_event(), ._build_open_update(), ._ensure_open_trade(), ._find_trade_id(), ._remember_trade()]

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-010.json

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
