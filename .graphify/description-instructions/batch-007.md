# Node Description Batch 8 of 56

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

- "tests_test_v68_persistent_entry_vs_now_dataset": "test_v68_persistent_entry_vs_now_dataset.py" | kind=code-symbol | source=tests/test_v68_persistent_entry_vs_now_dataset.py:L1 | neighbors=[account_metrics.py, repository.py, trade_report_exporter.py, _repo_with_trade(), test_account_exposes_entry_vs_now_histo…, test_account_page_has_entry_vs_now_time…]
- "tests_test_v73_forex_progressive_runner_engine": "_engine()" | kind=code-symbol | source=tests/test_v73_forex_progressive_runner.py:L50 | neighbors=[test_v73_forex_progressive_runner.py, PositionExecutor, Provider, Repo, TradeExecutor, test_forex_at_tp2_protects_tp1_then_ext…]
- "tests_test_v76_unified_multibot_orb_htf": "test_v76_unified_multibot_orb_htf.py" | kind=code-symbol | source=tests/test_v76_unified_multibot_orb_htf.py:L1 | neighbors=[_engine(), FakeMTF, test_neutral_h1_does_not_block_orb(), test_orb_buy_is_blocked_against_bearish…, test_orb_live_audit_includes_htf_contex…, test_orb_sell_is_aligned_with_bearish_c…]
- "tests_test_v93_latency_optimization_repo": "Repo" | kind=code-symbol | source=tests/test_v93_latency_optimization.py:L6 | neighbors=[test_v93_latency_optimization.py, LiveTradingConfig, LiveTradingEngine, .__init__(), .open_trades(), .sync_closed_mt5_trades()]
- "tests_test_v99_persistence_shards_adaptive_regime": "test_v99_persistence_shards_adaptive_regime.py" | kind=code-symbol | source=tests/test_v99_persistence_shards_adaptive_regime.py:L1 | neighbors=[main.py, realtime_dashboard.py, repository.py, test_adaptive_adx_is_bounded_and_keeps_…, test_broker_position_ticket_promotes_re…, test_dashboard_explains_regime_block_wi…]
- "app_main_run_unified_multibot_daemon": "run_unified_multibot_daemon()" | kind=code-symbol | source=app/main.py:L1268 | neighbors=[main.py, main(), v76: un solo proceso con workers lógico…, _assert_full_multibot_architecture(), _assert_v53_runtime_compatibility(), _resolve_symbols_for_profile_shared()]
- "backtesting_trade_simulator": "trade_simulator.py" | kind=code-symbol | source=backtesting/trade_simulator.py:L1 | neighbors=[backtest_pipeline.py, calculate_planned_rr(), calculate_realized_rr(), get_backtest_summary(), simulate_all_trades(), simulate_trade()]
- "brokers_mt5_data_mt5dataprovider_ensure_connection": "._ensure_connection()" | kind=code-symbol | source=brokers/mt5_data.py:L71 | neighbors=[MT5DataProvider, .connect(), .ensure_symbol(), .get_candles(), .get_current_tick(), .get_symbol_info()]
- "dashboard_realtime_dashboard_enrich_recent_row": "_enrich_recent_row()" | kind=code-symbol | source=dashboard/realtime_dashboard.py:L189 | neighbors=[realtime_dashboard.py, _action_label_es(), _decision_label_es(), _operational_state(), _reason_label_es(), Normaliza eventos persistidos para que …]
- "dashboard_realtime_dashboard_realtimedashboardservice_refresh_account_locked": "._refresh_account_locked()" | kind=code-symbol | source=dashboard/realtime_dashboard.py:L1673 | neighbors=[RealtimeDashboardService, .cycle_end(), .cycle_start(), .__init__(), .monitor_result(), ._cached_account_payload()]
- "dashboard_realtime_dashboard_realtimedashboardservice_symbol_result": ".symbol_result()" | kind=code-symbol | source=dashboard/realtime_dashboard.py:L1324 | neighbors=[RealtimeDashboardService, _enrich_recent_row(), _extract_quality(), _json_safe(), _now_iso(), ._persist_state_locked()]
- "database_reporting": "reporting.py" | kind=code-symbol | source=database/reporting.py:L1 | neighbors=[main.py, backtest_storage.py, export_trading_report(), _numeric(), _pretty_json(), _write_sheet()]
- "database_repository_tradingrepository_import_backtest_dataframe": ".import_backtest_dataframe()" | kind=code-symbol | source=database/repository.py:L2247 | neighbors=[TradingRepository, ._backtest_ticket(), ._build_setup_reason(), ._clean_value(), .create_trade_once(), ._dt()]
- "database_repository_tradingrepository_none_or_upper": "._none_or_upper()" | kind=code-symbol | source=database/repository.py:L156 | neighbors=[Convierte texto a MAYÚSCULAS., TradingRepository, .import_backtest_dataframe(), .save_signal(), .save_signal_once(), ._trade_kwargs()]
- "database_repository_tradingrepository_trade_dict": "._trade_dict()" | kind=code-symbol | source=database/repository.py:L430 | neighbors=[Convierte un objeto Trade de SQLAlchemy…, TradingRepository, .get_trade(), .get_trade_by_execution_key(), .get_trade_by_position_ticket(), .open_trades()]
- "execution_live_trading_engine_livetradingengine_canonical_bot_profile": "._canonical_bot_profile()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L1046 | neighbors=[LiveTradingEngine, ._commit_forex_processed_symbols(), ._forex_due_symbols(), .run_daemon(), ._symbol_matches_split_profile(), ._trade_owned_by_current_bot()]
- "orb_new_york_orb": "new_york_orb.py" | kind=code-symbol | source=strategy/orb/new_york_orb.py:L1 | neighbors=[classify_orb_market(), discover_orb_symbols(), is_orb_eligible_symbol(), is_orb_gold_symbol(), NewYorkORBStrategy, _norm_symbol()]
- "reporting_trade_report_exporter_tradereportexporter_report_record": "._report_record()" | kind=code-symbol | source=reporting/trade_report_exporter.py:L320 | neighbors=[TradeReportExporter, ._enrich_trades_for_report(), ._as_list(), ._build_entry_reason(), ._classify_close(), ._clean()]
- "reporting_trade_reporting_service": "trade_reporting_service.py" | kind=code-symbol | source=reporting/trade_reporting_service.py:L1 | neighbors=[__init__.py, trade_report_exporter.py, TradeReportingConfig, TradeReportingService, live_demo_smoke_test_service.py, test_demo_daemon_integration.py]
- "risk_money_management_apply_money_management_to_trade": "apply_money_management_to_trade()" | kind=code-symbol | source=strategy/risk/money_management.py:L236 | neighbors=[money_management.py, apply_money_management(), calculate_risk_amount(), update_balance(), validate_balance(), validate_pnl()]
- "risk_money_management_validate_balance": "validate_balance()" | kind=code-symbol | source=strategy/risk/money_management.py:L17 | neighbors=[money_management.py, apply_money_management(), apply_money_management_to_trade(), calculate_money_management_statistics(), calculate_risk_amount(), get_final_balance()]
- "risk_money_manager_moneymanager": "MoneyManager" | kind=code-symbol | source=risk/money_manager.py:L18 | neighbors=[money_manager.py, .calculate_profit_loss(), .calculate_risk_amount(), .get_current_balance(), .__init__(), .process_trade()]
- "risk_risk_manager_validate_positive_number": "validate_positive_number()" | kind=code-symbol | source=strategy/risk/risk_manager.py:L32 | neighbors=[risk_manager.py, calculate_current_risk(), calculate_risk_reward(), evaluate_trade_risk(), Valida que un valor sea numérico, finit…, validate_risk_reward()]
- "smc_chart_patterns_detect_chart_pattern_confirmation": "detect_chart_pattern_confirmation()" | kind=code-symbol | source=strategy/smc/chart_patterns.py:L165 | neighbors=[chart_patterns.py, ChartPatternConfig, _effective_price_tolerance(), _evidence(), _explain_chart_pattern_conflict(), _lin_slope()]
- "smc_confirmation_engine_evaluate_m5_confirmation": "evaluate_m5_confirmation()" | kind=code-symbol | source=strategy/smc/confirmation_engine.py:L190 | neighbors=[confirmation_engine.py, _average_range(), candle_metrics(), detect_rsi_divergence(), _grade(), M5ConfirmationConfig]
- "smc_harmonic_patterns": "harmonic_patterns.py" | kind=code-symbol | source=strategy/smc/harmonic_patterns.py:L1 | neighbors=[_alternating_swings(), detect_harmonic_confirmation(), _evaluate_pattern(), HarmonicConfig, _near(), _ratio()]
- "storage_account_page_syntax_test": "account_page_syntax_test.js" | kind=code-symbol | source=storage/account_page_syntax_test.js:L1 | neighbors=[account_page_syntax_test.js, auditHtml(), e(), go(), money(), num()]
- "tests_test_confirmation_engine": "test_confirmation_engine.py" | kind=code-symbol | source=tests/test_confirmation_engine.py:L1 | neighbors=[_data(), _setup(), test_adaptive_75_mode_accepts_when_only…, test_adaptive_75_mode_never_overrides_a…, test_adaptive_80_decision_code_reflects…, test_default_adaptive_confirmation_thre…]
- "tests_test_daemon_break_even_live_provider": "Provider" | kind=code-symbol | source=tests/test_daemon_break_even_live.py:L34 | neighbors=[test_daemon_break_even_live.py, LiveTradingConfig, LiveTradingEngine, test_daemon_break_even_is_idempotent_wh…, test_daemon_does_not_persist_break_even…, test_daemon_moves_live_position_to_brea…]
- "tests_test_daemon_risk_target_policy_repo": "Repo" | kind=code-symbol | source=tests/test_daemon_risk_target_policy.py:L6 | neighbors=[test_daemon_risk_target_policy.py, LiveTradingConfig, LiveTradingEngine, .get_trade_by_execution_key(), .open_trades(), .save_account_snapshot()]
- "tests_test_daemon_runner_extension_engine": "_engine()" | kind=code-symbol | source=tests/test_daemon_runner_extension.py:L58 | neighbors=[test_daemon_runner_extension.py, PositionExecutor, Provider, Repo, TradeExecutor, test_at_2r_no_continuation_closes_runne…]
- "tests_test_daemon_runner_extension_positionexecutor": "PositionExecutor" | kind=code-symbol | source=tests/test_daemon_runner_extension.py:L30 | neighbors=[test_daemon_runner_extension.py, _engine(), LiveTradingConfig, LiveTradingEngine, RunnerExtensionDecision, .get_position()]
- "tests_test_daemon_runner_extension_tradeexecutor": "TradeExecutor" | kind=code-symbol | source=tests/test_daemon_runner_extension.py:L41 | neighbors=[test_daemon_runner_extension.py, _engine(), LiveTradingConfig, LiveTradingEngine, RunnerExtensionDecision, .close_position()]
- "tests_test_daemon_single_entry_fallback_repo": "Repo" | kind=code-symbol | source=tests/test_daemon_single_entry_fallback.py:L6 | neighbors=[test_daemon_single_entry_fallback.py, _engine(), LiveTradingConfig, LiveTradingEngine, .get_trade_by_execution_key(), .open_trades()]
- "tests_test_demo_daemon_integration_fakeengine": "FakeEngine" | kind=code-symbol | source=tests/test_demo_daemon_integration.py:L39 | neighbors=[test_demo_daemon_integration.py, LiveTradingConfig, LiveTradingEngine, LiveTradingEngine, TradeReportingService, .process_symbols()]
- "tests_test_demo_daemon_integration_fakelifecyclemanager": "FakeLifecycleManager" | kind=code-symbol | source=tests/test_demo_daemon_integration.py:L63 | neighbors=[test_demo_daemon_integration.py, LiveTradingConfig, LiveTradingEngine, TradeReportingService, .create_from_signal(), .execute_with_executor()]
- "tests_test_demo_daemon_integration_fakereporting": "FakeReporting" | kind=code-symbol | source=tests/test_demo_daemon_integration.py:L31 | neighbors=[test_demo_daemon_integration.py, LiveTradingConfig, LiveTradingEngine, TradeReportingService, .export_now(), .__init__()]
- "tests_test_demo_daemon_integration_fakerepository": "FakeRepository" | kind=code-symbol | source=tests/test_demo_daemon_integration.py:L22 | neighbors=[test_demo_daemon_integration.py, LiveTradingConfig, LiveTradingEngine, TradeReportingService, .__init__(), .sync_closed_mt5_trades()]
- "tests_test_live_demo_main": "main()" | kind=code-symbol | source=tests/test_live_demo.py:L1188 | neighbors=[test_live_demo.py, get_analysis(), get_diagnostics(), print_analysis_diagnostics(), print_execution_diagnostics(), print_position_diagnostics()]
- "tests_test_multi_timeframe_cache_countinganalyzer": "CountingAnalyzer" | kind=code-symbol | source=tests/test_multi_timeframe_cache.py:L22 | neighbors=[test_multi_timeframe_cache.py, MultiTimeframeAnalyzer, MultiTimeframeConfig, MultiTimeframeAnalyzer, .__init__(), ._run_pipeline()]

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-007.json

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
