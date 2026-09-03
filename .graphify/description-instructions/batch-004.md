# Node Description Batch 5 of 56

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
Write every description in English (en). Do not switch languages.
No marketing language.
Respond ONLY with a JSON object mapping each node id (as a string) to its
one-sentence description — no prose, no markdown fences.

- "tests_test_v73_forex_progressive_runner": "test_v73_forex_progressive_runner.py" | kind=code-symbol | source=tests/test_v73_forex_progressive_runner.py:L1 | neighbors=[_engine(), PositionExecutor, Provider, Repo, test_forex_at_tp2_protects_tp1_then_ext…, test_forex_at_tp2_without_continuation_…]
- "tests_test_v74_fast_navigation_repo": "Repo" | kind=code-symbol | source=tests/test_v74_fast_navigation.py:L6 | neighbors=[test_v74_fast_navigation.py, RealtimeDashboardService, .__init__(), .latest_instrument_selection(), .latest_instrument_selection_profiles(), .latest_worker_process_results()]
- "brokers_mt5_execution_mt5executionerror": "MT5ExecutionError" | kind=code-symbol | source=brokers/mt5_execution.py:L9 | neighbors=[mt5_execution.py, RuntimeError, .account_info(), .assert_demo_account(), .calculate_margin_amount(), .calculate_risk_amount()]
- "dashboard_account_metrics": "account_metrics.py" | kind=code-symbol | source=dashboard/account_metrics.py:L1 | neighbors=[build_account_payload(), classify_close(), _metadata(), _strategy_name(), trade_outcome_policy.py, realtime_dashboard.py]
- "execution_trade_executor_tradeexecutionrequest": "TradeExecutionRequest" | kind=code-symbol | source=strategy/execution/trade_executor.py:L23 | neighbors=[MT5TradeExecutor, Modifica el Stop Loss de una posición r…, Adaptador del proveedor MT5 al contrato…, PaperTradeExecutor, Ejecuta operaciones virtuales.      No …, trade_executor.py]
- "execution_trade_executor_tradeexecutionresult": "TradeExecutionResult" | kind=code-symbol | source=strategy/execution/trade_executor.py:L148 | neighbors=[MT5TradeExecutor, Modifica el Stop Loss de una posición r…, Adaptador del proveedor MT5 al contrato…, PaperTradeExecutor, Ejecuta operaciones virtuales.      No …, trade_executor.py]
- "reporting_trade_report_exporter": "trade_report_exporter.py" | kind=code-symbol | source=reporting/trade_report_exporter.py:L1 | neighbors=[__init__.py, TradeReportExporter, trade_outcome_policy.py, trade_reporting_service.py, test_chile_timezone_reporting.py, test_daemon_explainable_report.py]
- "tests_test_daemon_break_even_live": "test_daemon_break_even_live.py" | kind=code-symbol | source=tests/test_daemon_break_even_live.py:L1 | neighbors=[BrokerExecutor, LifecycleManager, Provider, Repo, SplitRepo, test_daemon_break_even_is_idempotent_wh…]
- "tests_test_daemon_break_even_live_brokerexecutor": "BrokerExecutor" | kind=code-symbol | source=tests/test_daemon_break_even_live.py:L38 | neighbors=[test_daemon_break_even_live.py, LiveTradingConfig, LiveTradingEngine, .get_position(), .get_symbol_constraints(), .__init__()]
- "tests_test_daemon_break_even_live_repo": "Repo" | kind=code-symbol | source=tests/test_daemon_break_even_live.py:L6 | neighbors=[test_daemon_break_even_live.py, LiveTradingConfig, LiveTradingEngine, .__init__(), .open_trades(), .update_trade()]
- "tests_test_risk_integration_assert_result": "assert_result()" | kind=code-symbol | source=tests/test_risk_integration.py:L27 | neighbors=[test_risk_integration.py, test_consecutive_losses(), test_daily_loss_limit(), test_drawdown_limit(), test_invalid_buy_stop_loss(), test_invalid_risk_reward()]
- "tests_test_storage": "test_storage.py" | kind=code-symbol | source=tests/test_storage.py:L1 | neighbors=[reporting.py, repository.py, main(), test_account_history_excludes_direct_mt…, test_account_stats_reset_is_persistent_…, test_import_mt5_trade_history_recovers_…]
- "tests_test_v86_durable_trade_audit_export_entryauditrepo": "EntryAuditRepo" | kind=code-symbol | source=tests/test_v86_durable_trade_audit_export.py:L8 | neighbors=[test_v86_durable_trade_audit_export.py, RealtimeDashboardService, LiveTradingConfig, LiveTradingEngine, TradeAuditExcelExporter, .__init__()]
- "trade_lifecycle_manager": "trade_lifecycle_manager.py" | kind=code-symbol | source=trade_lifecycle_manager.py:L1 | neighbors=[live_paper_trading_engine.py, live_demo_smoke_test_service.py, test_demo_daemon_integration.py, test_live_paper_trading_engine.py, test_trade_lifecycle_full_integration.py, test_trade_lifecycle_manager.py]
- "app_main_run_multi_bot_daemon": "run_multi_bot_daemon()" | kind=code-symbol | source=app/main.py:L1816 | neighbors=[main.py, main(), Orquesta perfiles como procesos indepen…, _assert_full_multibot_architecture(), _assert_synthetic_split_architecture(), _assert_v53_runtime_compatibility()]
- "brokers_mt5_execution_back_mt5executionerror": "MT5ExecutionError" | kind=code-symbol | source=brokers/mt5_execution.back.py:L9 | neighbors=[mt5_execution.back.py, RuntimeError, .account_info(), .assert_demo_account(), .calculate_volume(), .ensure_symbol()]
- "brokers_mt5_execution_back_mt5executionprovider_check_market_order": ".check_market_order()" | kind=code-symbol | source=brokers/mt5_execution.back.py:L515 | neighbors=[MT5ExecutionProvider, ._allowed_fillings(), ._check_result_dict(), ._ensure(), ._filling_name(), ._normalize_price()]
- "brokers_mt5_execution_back_mt5executionprovider_place_market_order": ".place_market_order()" | kind=code-symbol | source=brokers/mt5_execution.back.py:L596 | neighbors=[MT5ExecutionProvider, MT5ExecutionError, ._allowed_fillings(), ._check_result_dict(), ._ensure(), ._filling_name()]
- "brokers_mt5_execution_mt5executionprovider_run_order_check_with_fallback": "._run_order_check_with_fallback()" | kind=code-symbol | source=brokers/mt5_execution.py:L674 | neighbors=[MT5ExecutionProvider, .check_market_order(), .place_market_order(), ._filling_name(), .get_filling_diagnostics(), ._is_order_check_success()]
- "config_symbol_policy": "symbol_policy.py" | kind=code-symbol | source=config/symbol_policy.py:L1 | neighbors=[classify_synthetic_symbol(), direction_policy_diagnostics(), get_symbol_direction_policy(), is_direction_allowed(), normalize_direction(), SymbolDirectionPolicy]
- "dashboard_realtime_dashboard_realtimedashboardservice_refresh_open_positions_locked": "._refresh_open_positions_locked()" | kind=code-symbol | source=dashboard/realtime_dashboard.py:L1374 | neighbors=[RealtimeDashboardService, .cycle_end(), .cycle_start(), .__init__(), .monitor_result(), _json_safe()]
- "execution_live_trading_engine_livetradingengine_persist_audit_event": "._persist_audit_event()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L699 | neighbors=[LiveTradingEngine, ._analysis_invalidation_exit(), ._arps_time_stop_exit(), .process_symbol(), .process_symbols(), ._recover_unpersisted_open_positions()]
- "execution_live_trading_engine_livetradingengine_trade_owned_by_current_bot": "._trade_owned_by_current_bot()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L1155 | neighbors=[LiveTradingEngine, ._close_forex_positions_for_rollover(), ._dashboard_chart_snapshots(), ._monitor_break_even_positions(), ._refresh_current_strategy_views(), ._sync_open_trades_before_execution()]
- "monitoring_position_monitoring_service_positionmonitoringservice": "PositionMonitoringService" | kind=code-symbol | source=monitoring/position_monitoring_service.py:L16 | neighbors=[PaperTradeExecutor, Ejecuta operaciones virtuales.      No …, position_monitoring_service.py, .break_even_trigger_rr(), .__init__(), .monitor_open_positions()]
- "smc_chart_patterns": "chart_patterns.py" | kind=code-symbol | source=strategy/smc/chart_patterns.py:L1 | neighbors=[ChartPatternConfig, detect_chart_pattern_confirmation(), _effective_price_tolerance(), _evidence(), _explain_chart_pattern_conflict(), _iso()]
- "smc_chart_patterns_chartpatternconfig": "ChartPatternConfig" | kind=code-symbol | source=strategy/smc/chart_patterns.py:L21 | neighbors=[chart_patterns.py, detect_chart_pattern_confirmation(), M5ConfirmationConfig, Motor de confirmación M5 para DaemonBla…, Detecta divergencia regular entre preci…, Evalúa una vela candidata y devuelve un…]
- "smc_h1_doji_extremes_h1extremedojiconfig": "H1ExtremeDojiConfig" | kind=code-symbol | source=strategy/smc/h1_doji_extremes.py:L10 | neighbors=[MultiTimeframeAnalyzer, MultiTimeframeConfig, Invalida la caché completa o una etapa …, Devuelve un snapshot seguro de una etap…, Obtiene una etapa H1/M15/M5 usando cach…, Configuración del flujo:          H1  -…]
- "tests_test_daemon_break_even_live_tradeexecutor": "TradeExecutor" | kind=code-symbol | source=tests/test_daemon_break_even_live.py:L56 | neighbors=[test_daemon_break_even_live.py, test_daemon_break_even_is_idempotent_wh…, test_daemon_does_not_persist_break_even…, test_daemon_moves_live_position_to_brea…, test_runner_moves_to_break_even_when_tp…, test_runner_sell_break_even_uses_two_po…]
- "tests_test_daemon_split_risk_management_repo": "Repo" | kind=code-symbol | source=tests/test_daemon_split_risk_management.py:L6 | neighbors=[test_daemon_split_risk_management.py, LiveTradingConfig, LiveTradingEngine, .get_trade_by_execution_key(), .open_trades(), .save_account_snapshot()]
- "tests_test_forex_rollover_guard": "test_forex_rollover_guard.py" | kind=code-symbol | source=tests/test_forex_rollover_guard.py:L1 | neighbors=[_engine(), test_asian_and_london_hours_are_enabled…, test_cycle_restarts_exactly_at_tokyo_09…, test_cycle_restarts_exactly_at_tokyo_09…, test_dst_new_york_force_flat_still_work…, test_force_flat_from_1645_new_york()]
- "tests_test_forex_rollover_guard_engine": "_engine()" | kind=code-symbol | source=tests/test_forex_rollover_guard.py:L5 | neighbors=[test_forex_rollover_guard.py, test_asian_and_london_hours_are_enabled…, test_cycle_restarts_exactly_at_tokyo_09…, test_cycle_restarts_exactly_at_tokyo_09…, test_dst_new_york_force_flat_still_work…, test_force_flat_from_1645_new_york()]
- "tests_test_live_demo_smoke_stops": "test_live_demo_smoke_stops.py" | kind=code-symbol | source=tests/test_live_demo_smoke_stops.py:L1 | neighbors=[live_demo_smoke_test_service.py, _Executor, _Exporter, _Info, _Lifecycle, _LifecycleManager]
- "tests_test_live_demo_smoke_stops_provider": "_Provider" | kind=code-symbol | source=tests/test_live_demo_smoke_stops.py:L13 | neighbors=[test_live_demo_smoke_stops.py, LiveDemoSmokeTestConfig, LiveDemoSmokeTestService, .assert_demo_account(), .ensure_symbol(), .get_symbol_constraints()]
- "tests_test_live_end_to_end_dry_run_fakeexecutor": "FakeExecutor" | kind=code-symbol | source=tests/test_live_end_to_end_dry_run.py:L38 | neighbors=[test_live_end_to_end_dry_run.py, LiveTradingConfig, LiveTradingEngine, .assert_demo_account(), .calculate_volume(), .check_market_order()]
- "tests_test_live_paper_trading_engine": "test_live_paper_trading_engine.py" | kind=code-symbol | source=tests/test_live_paper_trading_engine.py:L1 | neighbors=[build_engine(), FakeAnalyzer, FakeProvider, ready_signal(), test_live_paper_monitor_uses_bid_for_bu…, test_live_paper_opens_from_ready_signal…]
- "tests_test_main_symbol_selection": "test_main_symbol_selection.py" | kind=code-symbol | source=tests/test_main_symbol_selection.py:L1 | neighbors=[main.py, strategy_config.py, FakeConnector, FakeInstrumentManager, FakeProvider, test_categories_are_normalized()]
- "tests_test_trade_lifecycle_full_integration_controlleddataprovider": "ControlledDataProvider" | kind=code-symbol | source=tests/test_trade_lifecycle_full_integration.py:L37 | neighbors=[test_trade_lifecycle_full_integration.py, MultiTimeframeAnalyzer, MultiTimeframeConfig, .get_candles(), ._h1(), .__init__()]
- "tests_test_trade_lifecycle_manager_create_signal": "create_signal()" | kind=code-symbol | source=tests/test_trade_lifecycle_manager.py:L36 | neighbors=[test_trade_lifecycle_manager.py, test_cannot_execute_final_lifecycle_twi…, test_create_lifecycle_from_signal(), test_lifecycle_ambiguous(), test_lifecycle_expired(), test_lifecycle_loss()]
- "tests_test_v100_entry_quarantine_winrate_repo": "_Repo" | kind=code-symbol | source=tests/test_v100_entry_quarantine_winrate.py:L94 | neighbors=[test_v100_entry_quarantine_winrate.py, LiveTradingConfig, LiveTradingEngine, ChartPatternConfig, M5ConfirmationConfig, .get_trade_by_execution_key()]
- "tests_test_v65_smc_two_leg_tp3_protection_engine": "_engine()" | kind=code-symbol | source=tests/test_v65_smc_two_leg_tp3_protection.py:L49 | neighbors=[test_v65_smc_two_leg_tp3_protection.py, PositionExecutor, Provider, Repo, TradeExecutor, test_smc_at_2r_locks_1r_then_extends_on…]

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-004.json

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
