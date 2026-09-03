# Node Description Batch 17 of 56

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
Write every description in Spanish (es). Do not switch languages.
No marketing language.
Respond ONLY with a JSON object mapping each node id (as a string) to its
one-sentence description — no prose, no markdown fences.

- "app_main_warn_possible_parallel_daemon_instances": "_warn_possible_parallel_daemon_instances()" | kind=code-symbol | source=app/main.py:L1558 | neighbors=[main.py, Best-effort warning for stale DaemonBla…, run_multi_bot_daemon(), run_unified_multibot_daemon()]
- "backtesting_backtest_money_management_apply_money_management": "apply_money_management()" | kind=code-symbol | source=backtesting/backtest_money_management.py:L89 | neighbors=[backtest_money_management.py, calculate_risk_amount(), calculate_trade_pnl(), Aplica gestión monetaria a los resultad…]
- "backtesting_trade_simulator_simulate_all_trades": "simulate_all_trades()" | kind=code-symbol | source=backtesting/trade_simulator.py:L436 | neighbors=[trade_simulator.py, Simula todas las entradas confirmadas., simulate_trade(), simulate_trades()]
- "brokers_mt5_execution_back_mt5executionprovider_account_info": ".account_info()" | kind=code-symbol | source=brokers/mt5_execution.back.py:L27 | neighbors=[MT5ExecutionProvider, MT5ExecutionError, ._ensure(), .assert_demo_account()]
- "brokers_mt5_execution_back_mt5executionprovider_minimum_stop_distance": "._minimum_stop_distance()" | kind=code-symbol | source=brokers/mt5_execution.back.py:L235 | neighbors=[MT5ExecutionProvider, .get_symbol_constraints(), .normalize_market_stops(), ._normalize_stops()]
- "brokers_mt5_execution_mt5executionprovider_account_info": ".account_info()" | kind=code-symbol | source=brokers/mt5_execution.py:L42 | neighbors=[MT5ExecutionProvider, MT5ExecutionError, ._ensure(), .assert_demo_account()]
- "brokers_mt5_execution_mt5executionprovider_calculate_margin_amount": ".calculate_margin_amount()" | kind=code-symbol | source=brokers/mt5_execution.py:L809 | neighbors=[MT5ExecutionProvider, MT5ExecutionError, ._ensure(), Calcula margen requerido con el motor n…]
- "brokers_mt5_execution_mt5executionprovider_current_market_price": "._current_market_price()" | kind=code-symbol | source=brokers/mt5_execution.py:L422 | neighbors=[MT5ExecutionProvider, ._build_market_request_base(), MT5ExecutionError, .place_market_order()]
- "brokers_mt5_execution_mt5executionprovider_filling_name": "._filling_name()" | kind=code-symbol | source=brokers/mt5_execution.py:L329 | neighbors=[MT5ExecutionProvider, .get_filling_diagnostics(), .place_market_order(), ._run_order_check_with_fallback()]
- "brokers_mt5_execution_mt5executionprovider_get_symbol_constraints": ".get_symbol_constraints()" | kind=code-symbol | source=brokers/mt5_execution.py:L122 | neighbors=[MT5ExecutionProvider, .symbol_spec(), .normalize_market_stops(), Devuelve restricciones reales informada…]
- "brokers_mt5_execution_mt5executionprovider_is_order_check_success": "._is_order_check_success()" | kind=code-symbol | source=brokers/mt5_execution.py:L631 | neighbors=[MT5ExecutionProvider, .place_market_order(), ._run_order_check_with_fallback(), order_check() y order_send() no usan el…]
- "brokers_mt5_execution_mt5executionprovider_normalize_price": "._normalize_price()" | kind=code-symbol | source=brokers/mt5_execution.py:L159 | neighbors=[MT5ExecutionProvider, ._build_market_request_base(), .modify_position_stops(), .normalize_market_stops()]
- "brokers_mt5_trade_executor_rationale_104": "Modifica el Stop Loss de una posición real sin cerrarla.          El método se u" | kind=entity | source=brokers/mt5_trade_executor.py:L104 | neighbors=[.move_stop_loss(), TradeExecutionRequest, TradeExecutionResult, TradeExecutor]
- "brokers_mt5_trade_executor_rationale_21": "Adaptador del proveedor MT5 al contrato TradeExecutor.      Esta clase no contie" | kind=entity | source=brokers/mt5_trade_executor.py:L21 | neighbors=[MT5TradeExecutor, TradeExecutionRequest, TradeExecutionResult, TradeExecutor]
- "brokers_symbol_discovery_derivsymboldiscovery_get_all_symbols": ".get_all_symbols()" | kind=code-symbol | source=brokers/symbol_discovery.py:L56 | neighbors=[DerivSymbolDiscovery, .get_all_forex_symbols(), ._ensure_connection(), .get_deriv_synthetics()]
- "brokers_symbol_discovery_derivsymboldiscovery_get_tradeable_forex": ".get_tradeable_forex()" | kind=code-symbol | source=brokers/symbol_discovery.py:L221 | neighbors=[DerivSymbolDiscovery, ._ensure_connection(), .get_all_forex_symbols(), Devuelve únicamente pares FX habilitado…]
- "config_instruments": "instruments.py" | kind=code-symbol | source=config/instruments.py:L1 | neighbors=[main.py, symbol_discovery.py, InstrumentManager, test_v45_forex_instrument_catalog.py]
- "config_symbol_policy_direction_policy_diagnostics": "direction_policy_diagnostics()" | kind=code-symbol | source=config/symbol_policy.py:L56 | neighbors=[symbol_policy.py, get_symbol_direction_policy(), is_direction_allowed(), normalize_direction()]
- "config_symbol_policy_is_direction_allowed": "is_direction_allowed()" | kind=code-symbol | source=config/symbol_policy.py:L48 | neighbors=[symbol_policy.py, direction_policy_diagnostics(), get_symbol_direction_policy(), normalize_direction()]
- "dashboard_account_metrics_build_account_payload": "build_account_payload()" | kind=code-symbol | source=dashboard/account_metrics.py:L100 | neighbors=[account_metrics.py, classify_close(), _metadata(), _strategy_name()]
- "dashboard_account_metrics_metadata": "_metadata()" | kind=code-symbol | source=dashboard/account_metrics.py:L9 | neighbors=[account_metrics.py, build_account_payload(), classify_close(), _strategy_name()]
- "dashboard_realtime_dashboard_humanize_code": "_humanize_code()" | kind=code-symbol | source=dashboard/realtime_dashboard.py:L138 | neighbors=[realtime_dashboard.py, _action_label_es(), _decision_label_es(), _reason_label_es()]
- "dashboard_realtime_dashboard_realtimedashboardservice_mark_live": ".mark_live()" | kind=code-symbol | source=dashboard/realtime_dashboard.py:L969 | neighbors=[RealtimeDashboardService, _now_iso(), ._persist_state_locked(), .start()]
- "dashboard_realtime_dashboard_realtimedashboardservice_mark_offline": ".mark_offline()" | kind=code-symbol | source=dashboard/realtime_dashboard.py:L978 | neighbors=[RealtimeDashboardService, _now_iso(), ._persist_state_locked(), .start()]
- "dashboard_realtime_dashboard_realtimedashboardservice_start": ".start()" | kind=code-symbol | source=dashboard/realtime_dashboard.py:L998 | neighbors=[RealtimeDashboardService, .mark_live(), .mark_offline(), .update_status()]
- "dashboard_realtime_dashboard_realtimedashboardservice_symbol_start": ".symbol_start()" | kind=code-symbol | source=dashboard/realtime_dashboard.py:L1313 | neighbors=[RealtimeDashboardService, _now_iso(), ._persist_state_locked(), ._touch_live_locked()]
- "dashboard_realtime_dashboard_realtimedashboardservice_trade_audit_detail_payload": "._trade_audit_detail_payload()" | kind=code-symbol | source=dashboard/realtime_dashboard.py:L735 | neighbors=[Detalle completo de un trade y TODOS su…, RealtimeDashboardService, _json_safe(), _now_iso()]
- "dashboard_realtime_dashboard_realtimedashboardservice_update_status": ".update_status()" | kind=code-symbol | source=dashboard/realtime_dashboard.py:L1179 | neighbors=[RealtimeDashboardService, .start(), _now_iso(), ._persist_state_locked()]
- "dashboard_smc_visual_context_float": "_float()" | kind=code-symbol | source=dashboard/smc_visual_context.py:L8 | neighbors=[smc_visual_context.py, build_smc_visual_context(), _fvg_status(), _zone_status()]
- "dashboard_smc_visual_context_zone_status": "_zone_status()" | kind=code-symbol | source=dashboard/smc_visual_context.py:L31 | neighbors=[smc_visual_context.py, build_smc_visual_context(), Estado visual de una zona; no altera la…, _float()]
- "data_market_data": "market_data.py" | kind=code-symbol | source=data/market_data.py:L1 | neighbors=[get_historical_data(), initialize_mt5(), main(), save_historical_data()]
- "data_market_data_main": "main()" | kind=code-symbol | source=data/market_data.py:L73 | neighbors=[market_data.py, get_historical_data(), initialize_mt5(), save_historical_data()]
- "database_database_database_diagnostics": "database_diagnostics()" | kind=code-symbol | source=database/database.py:L179 | neighbors=[database.py, resolve_db_path(), _sqlite_activity_score(), _stable_data_dir()]
- "database_database_get_engine": "get_engine()" | kind=code-symbol | source=database/database.py:L196 | neighbors=[database.py, resolve_db_path(), get_session_factory(), init_database()]
- "database_database_init_database": "init_database()" | kind=code-symbol | source=database/database.py:L278 | neighbors=[database.py, _ensure_performance_indexes(), _ensure_trade_columns(), get_engine()]
- "database_database_resolve_db_path": "resolve_db_path()" | kind=code-symbol | source=database/database.py:L170 | neighbors=[database.py, database_diagnostics(), get_engine(), _bootstrap_stable_database()]
- "database_database_sqlite_activity_score": "_sqlite_activity_score()" | kind=code-symbol | source=database/database.py:L32 | neighbors=[database.py, _bootstrap_stable_database(), database_diagnostics(), (trade_journal, trades, account_snapsho…]
- "database_reporting_export_trading_report": "export_trading_report()" | kind=code-symbol | source=database/reporting.py:L28 | neighbors=[reporting.py, _numeric(), _write_sheet(), Exporta un reporte completo desde SQLit…]
- "database_repository_tradingrepository_account_trade_history_dataframe": ".account_trade_history_dataframe()" | kind=code-symbol | source=database/repository.py:L1466 | neighbors=[Historial DB-only usado por Cuenta acti…, TradingRepository, ._dt(), .reset_account_statistics()]
- "database_repository_tradingrepository_create_trade": ".create_trade()" | kind=code-symbol | source=database/repository.py:L1918 | neighbors=[TradingRepository, ._trade_kwargs(), ._upsert_trade_journal_session(), .create_trade_once()]

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-016.json

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
