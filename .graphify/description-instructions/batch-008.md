# Node Description Batch 9 of 56

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

- "tests_test_orb_new_york_strategy_strategy": "_strategy()" | kind=code-symbol | source=tests/test_orb_new_york_strategy.py:L63 | neighbors=[test_orb_new_york_strategy.py, FakeProvider, test_orb_builds_15_minute_range_before_…, test_orb_buy_requires_m5_breakout_then_…, test_orb_does_not_run_on_weekends(), test_orb_is_disabled_after_new_york_ses…]
- "tests_test_trade_lifecycle_paper_integration": "test_trade_lifecycle_paper_integration.py" | kind=code-symbol | source=tests/test_trade_lifecycle_paper_integration.py:L1 | neighbors=[signal(), test_full_paper_lifecycle_break_even_st…, test_full_paper_lifecycle_open_and_brea…, test_full_paper_lifecycle_stop_loss_to_…, test_full_paper_lifecycle_take_profit_t…, test_monitor_multiple_active_lifecycles…]
- "tests_test_v46_total_persistence": "test_v46_total_persistence.py" | kind=code-symbol | source=tests/test_v46_total_persistence.py:L1 | neighbors=[repository.py, trade_reporting_service.py, signal(), test_audit_event_is_append_only_and_que…, test_filled_lifecycle_persists_trade_jo…, test_instrument_selection_also_generate…]
- "tests_test_v65_smc_two_leg_tp3_protection_positionexecutor": "PositionExecutor" | kind=code-symbol | source=tests/test_v65_smc_two_leg_tp3_protection.py:L25 | neighbors=[test_v65_smc_two_leg_tp3_protection.py, _engine(), LiveTradingConfig, LiveTradingEngine, RunnerExtensionDecision, .get_position()]
- "tests_test_v65_smc_two_leg_tp3_protection_tradeexecutor": "TradeExecutor" | kind=code-symbol | source=tests/test_v65_smc_two_leg_tp3_protection.py:L34 | neighbors=[test_v65_smc_two_leg_tp3_protection.py, _engine(), LiveTradingConfig, LiveTradingEngine, RunnerExtensionDecision, .close_position()]
- "tests_test_v66_smc_tp4_be_plus2_broker": "Broker" | kind=code-symbol | source=tests/test_v66_smc_tp4_be_plus2.py:L43 | neighbors=[test_v66_smc_tp4_be_plus2.py, LiveTradingConfig, LiveTradingEngine, RunnerExtensionDecision, .get_position(), .get_symbol_constraints()]
- "tests_test_v66_smc_tp4_be_plus2_engine": "_engine()" | kind=code-symbol | source=tests/test_v66_smc_tp4_be_plus2.py:L67 | neighbors=[test_v66_smc_tp4_be_plus2.py, Broker, Provider, Repo, TradeExecutor, test_smc_3_5r_guard_locks_3r_while_targ…]
- "tests_test_v66_smc_tp4_be_plus2_tradeexecutor": "TradeExecutor" | kind=code-symbol | source=tests/test_v66_smc_tp4_be_plus2.py:L54 | neighbors=[test_v66_smc_tp4_be_plus2.py, _engine(), LiveTradingConfig, LiveTradingEngine, RunnerExtensionDecision, .close_position()]
- "tests_test_v69_forex_event_scheduler_exposurerepo": "ExposureRepo" | kind=code-symbol | source=tests/test_v69_forex_event_scheduler.py:L88 | neighbors=[test_v69_forex_event_scheduler.py, LiveTradingConfig, LiveTradingEngine, .__init__(), .open_trades(), test_forex_currency_exposure_blocks_thi…]
- "tests_test_v71_balanced_recent_analysis": "test_v71_balanced_recent_analysis.py" | kind=code-symbol | source=tests/test_v71_balanced_recent_analysis.py:L1 | neighbors=[models.py, repository.py, _event(), test_dashboard_calls_balanced_repositor…, test_orb_flood_does_not_hide_forex_or_s…, test_profile_is_inferred_from_magic_whe…]
- "tests_test_v73_forex_progressive_runner_positionexecutor": "PositionExecutor" | kind=code-symbol | source=tests/test_v73_forex_progressive_runner.py:L26 | neighbors=[test_v73_forex_progressive_runner.py, _engine(), LiveTradingConfig, LiveTradingEngine, RunnerExtensionDecision, .get_position()]
- "tests_test_v73_forex_progressive_runner_tradeexecutor": "TradeExecutor" | kind=code-symbol | source=tests/test_v73_forex_progressive_runner.py:L35 | neighbors=[test_v73_forex_progressive_runner.py, _engine(), LiveTradingConfig, LiveTradingEngine, RunnerExtensionDecision, .close_position()]
- "tests_test_v74_fast_navigation": "test_v74_fast_navigation.py" | kind=code-symbol | source=tests/test_v74_fast_navigation.py:L1 | neighbors=[realtime_dashboard.py, Repo, _service(), test_dashboard_main_still_uses_state_en…, test_dashboard_source_has_dedicated_ins…, test_instruments_cache_invalidates_afte…]
- "tests_test_v85_orb_correlation_synthetic_parity": "test_v85_orb_correlation_synthetic_parity.py" | kind=code-symbol | source=tests/test_v85_orb_correlation_synthetic_parity.py:L1 | neighbors=[_engine_with_open_trade(), _orb_trade(), test_gold_and_wall_street_are_not_part_…, test_persisted_protective_stop_also_pro…, test_sp500_is_allowed_after_nasdaq_brea…, test_sp500_is_blocked_while_nasdaq_risk…]
- "tests_test_v86_durable_trade_audit_export": "test_v86_durable_trade_audit_export.py" | kind=code-symbol | source=tests/test_v86_durable_trade_audit_export.py:L1 | neighbors=[realtime_dashboard.py, trade_audit_excel_exporter.py, EntryAuditRepo, test_audit_page_excludes_snapshot_from_…, test_audit_page_falls_back_to_immutable…, test_audit_page_recovers_entry_thesis_f…]
- "tests_test_v93_latency_optimization_reporting": "Reporting" | kind=code-symbol | source=tests/test_v93_latency_optimization.py:L19 | neighbors=[test_v93_latency_optimization.py, LiveTradingConfig, LiveTradingEngine, .export_now(), .__init__(), test_coordinated_worker_sync_never_writ…]
- "tests_test_v95_analysis_invalidation_exit": "test_v95_analysis_invalidation_exit.py" | kind=code-symbol | source=tests/test_v95_analysis_invalidation_exit.py:L1 | neighbors=[engine_with_view(), invalid_view(), old_trade(), Repo, test_recovery_protection_closes_after_p…, test_same_evaluation_does_not_inflate_c…]
- "tests_test_v96_arps_synthetic_scalper": "test_v96_arps_synthetic_scalper.py" | kind=code-symbol | source=tests/test_v96_arps_synthetic_scalper.py:L1 | neighbors=[main.py, trade_report_exporter.py, test_adx_math_returns_finite_values_for…, test_arps_execution_key_and_risk_config…, test_arps_three_minute_exit_closes_when…, test_family_direction_policy_is_preserv…]
- "app_main_acquire_multibot_instance_guard": "_acquire_multibot_instance_guard()" | kind=code-symbol | source=app/main.py:L1712 | neighbors=[main.py, _find_other_multibot_coordinators_windo…, _MultiBotInstanceGuard, .acquire(), .release(), main()]
- "backtesting_backtest_money_management": "backtest_money_management.py" | kind=code-symbol | source=backtesting/backtest_money_management.py:L1 | neighbors=[apply_money_management(), calculate_risk_amount(), calculate_trade_pnl(), get_money_management_summary(), save_money_management_results(), backtest_pipeline.py]
- "brokers_mt5_data_mt5dataprovider_ensure_symbol": ".ensure_symbol()" | kind=code-symbol | source=brokers/mt5_data.py:L195 | neighbors=[MT5DataProvider, ._ensure_connection(), .resolve_symbol(), .get_candles(), .get_current_tick(), .get_symbol_info()]
- "brokers_mt5_execution_mt5executionprovider_build_market_request_base": "._build_market_request_base()" | kind=code-symbol | source=brokers/mt5_execution.py:L532 | neighbors=[MT5ExecutionProvider, ._current_market_price(), ._normalize_price(), ._sanitize_comment(), .symbol_spec(), .check_market_order()]
- "brokers_mt5_execution_mt5executionprovider_calculate_volume": ".calculate_volume()" | kind=code-symbol | source=brokers/mt5_execution.py:L944 | neighbors=[MT5ExecutionProvider, MT5ExecutionError, .calculate_risk_amount(), ._ensure(), .normalize_volume(), .symbol_spec()]
- "dashboard_realtime_dashboard_realtimedashboardservice_monitor_result": ".monitor_result()" | kind=code-symbol | source=dashboard/realtime_dashboard.py:L1365 | neighbors=[RealtimeDashboardService, _json_safe(), _now_iso(), ._persist_state_locked(), ._refresh_account_locked(), ._refresh_open_positions_locked()]
- "dashboard_realtime_dashboard_realtimedashboardservice_set_instrument_catalog": ".set_instrument_catalog()" | kind=code-symbol | source=dashboard/realtime_dashboard.py:L1189 | neighbors=[RealtimeDashboardService, _catalog_symbols_by_profile(), _normalize_symbol_list(), _now_iso(), ._invalidate_navigation_caches(), ._persist_state_locked()]
- "dashboard_smc_visual_context": "smc_visual_context.py" | kind=code-symbol | source=dashboard/smc_visual_context.py:L1 | neighbors=[_bool(), build_smc_visual_context(), _float(), _fvg_status(), _iso(), _zone_status()]
- "dashboard_smc_visual_context_build_smc_visual_context": "build_smc_visual_context()" | kind=code-symbol | source=dashboard/smc_visual_context.py:L75 | neighbors=[smc_visual_context.py, _bool(), _float(), _fvg_status(), _iso(), _zone_status()]
- "database_repository_tradingrepository_create_trade_once": ".create_trade_once()" | kind=code-symbol | source=database/repository.py:L1934 | neighbors=[Crea una operación una sola vez usando:…, TradingRepository, .create_trade(), ._trade_kwargs(), ._upsert_trade_journal_session(), .import_backtest_dataframe()]
- "database_repository_tradingrepository_import_mt5_trade_history": ".import_mt5_trade_history()" | kind=code-symbol | source=database/repository.py:L3094 | neighbors=[Reconstruye el historial permanente usa…, TradingRepository, ._dt(), ._journal_key(), ._json_or_none(), ._num()]
- "database_repository_tradingrepository_save_audit_event": ".save_audit_event()" | kind=code-symbol | source=database/repository.py:L463 | neighbors=[Persiste un evento sin sobrescribir eve…, TradingRepository, ._dt(), ._int_or_none(), ._json_or_none(), .save_instrument_selection()]
- "execution_live_trading_engine_livetradingengine_quarantine_result": "._quarantine_result()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L594 | neighbors=[LiveTradingEngine, .process_symbol(), ._load_quarantine_unlocked(), ._parse_quarantine_time(), ._quarantine_storage_lock(), ._recoverable_quarantine_details()]
- "execution_live_trading_engine_livetradingengine_quarantine_storage_lock": "._quarantine_storage_lock()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L467 | neighbors=[LiveTradingEngine, ._load_quarantine(), ._quarantine_result(), ._quarantine_file(), ._quarantine_symbol(), ._save_quarantine()]
- "reporting_console_reporting_service_consolereportingservice_print_confirmation_diag": "._print_confirmation_diag()" | kind=code-symbol | source=reporting/console_reporting_service.py:L246 | neighbors=[ConsoleReportingService, ._confirmation_label(), ._extract_confirmation_diag(), ._fmt(), ._reason_label(), .print_result()]
- "reporting_strategy_evaluation": "strategy_evaluation.py" | kind=code-symbol | source=reporting/strategy_evaluation.py:L1 | neighbors=[repository.py, build_strategy_evaluation(), _distribution(), main(), _number(), write_strategy_evaluation()]
- "reporting_trade_report_exporter_tradereportexporter_export": ".export()" | kind=code-symbol | source=reporting/trade_report_exporter.py:L66 | neighbors=[TradeReportExporter, ._compact_audit_dataframe(), ._enrich_trades_for_report(), ._format_chile_now(), ._format_workbook(), ._get_account_snapshots()]
- "reporting_trade_reporting_service_tradereportingservice_build_open_update": "._build_open_update()" | kind=code-symbol | source=reporting/trade_reporting_service.py:L220 | neighbors=[TradeReportingService, ._broker(), ._build_details(), ._volume(), ._close_trade(), ._ensure_open_trade()]
- "reporting_trade_reporting_service_tradereportingservice_close_trade": "._close_trade()" | kind=code-symbol | source=reporting/trade_reporting_service.py:L156 | neighbors=[TradeReportingService, ._build_details(), ._build_open_update(), ._ensure_open_trade(), ._find_trade_id(), ._remember_trade()]
- "reporting_trade_reporting_service_tradereportingservice_ensure_open_trade": "._ensure_open_trade()" | kind=code-symbol | source=reporting/trade_reporting_service.py:L121 | neighbors=[TradeReportingService, ._close_trade(), ._build_open_data(), ._build_open_update(), ._remember_trade(), .on_lifecycle_event()]
- "risk_money_management_apply_money_management": "apply_money_management()" | kind=code-symbol | source=strategy/risk/money_management.py:L342 | neighbors=[money_management.py, apply_money_management_to_trade(), validate_balance(), validate_dataframe(), validate_risk_percent(), Aplica Money Management secuencialmente…]
- "tests_test_backtest_run_backtest": "run_backtest()" | kind=code-symbol | source=tests/test_backtest.py:L444 | neighbors=[test_backtest.py, load_data(), prepare_data(), print_rr_statistics(), print_summary(), print_trades()]

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-008.json

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
