# Node Description Batch 12 of 56

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

- "risk_money_management_calculate_money_management_statistics": "calculate_money_management_statistics()" | kind=code-symbol | source=strategy/risk/money_management.py:L711 | neighbors=[money_management.py, calculate_drawdown_statistics(), validate_balance(), validate_dataframe(), Calcula estadísticas completas     de …, run_money_management()]
- "risk_risk_manager_validate_dataframe": "validate_dataframe()" | kind=code-symbol | source=strategy/risk/risk_manager.py:L155 | neighbors=[risk_manager.py, calculate_current_drawdown(), calculate_daily_loss(), count_consecutive_losses(), evaluate_trade_risk(), Valida que trades sea un pandas DataFra…]
- "scalping_adaptive_regime_pullback_adaptiveregimepullbackstrategy_analyze_symbol": ".analyze_symbol()" | kind=code-symbol | source=strategy/scalping/adaptive_regime_pullback.py:L117 | neighbors=[AdaptiveRegimePullbackStrategy, ._effective_adx_threshold(), ._family_direction_allowed(), ._read(), _adx(), _atr()]
- "services_live_demo_smoke_test_service": "live_demo_smoke_test_service.py" | kind=code-symbol | source=services/live_demo_smoke_test_service.py:L1 | neighbors=[mt5_trade_executor.py, trade_reporting_service.py, LiveDemoSmokeTestConfig, LiveDemoSmokeTestService, trade_lifecycle_manager.py, test_live_demo_smoke_stops.py]
- "smc_harmonic_patterns_harmonicconfig": "HarmonicConfig" | kind=code-symbol | source=strategy/smc/harmonic_patterns.py:L16 | neighbors=[M5ConfirmationConfig, Motor de confirmación M5 para DaemonBla…, Detecta divergencia regular entre preci…, Evalúa una vela candidata y devuelve un…, harmonic_patterns.py, detect_harmonic_confirmation()]
- "tests_test_confirmation_engine_data": "_data()" | kind=code-symbol | source=tests/test_confirmation_engine.py:L6 | neighbors=[test_confirmation_engine.py, test_adaptive_75_mode_accepts_when_only…, test_adaptive_75_mode_never_overrides_a…, test_adaptive_80_decision_code_reflects…, test_high_quality_long_confirmation_is_…, test_repeated_order_block_touch_is_reje…]
- "tests_test_confirmation_engine_setup": "_setup()" | kind=code-symbol | source=tests/test_confirmation_engine.py:L16 | neighbors=[test_confirmation_engine.py, test_adaptive_75_mode_accepts_when_only…, test_adaptive_75_mode_never_overrides_a…, test_adaptive_80_decision_code_reflects…, test_high_quality_long_confirmation_is_…, test_repeated_order_block_touch_is_reje…]
- "tests_test_daemon_break_even_live_test_daemon_break_even_is_idempotent_when_broker_already_at_entry": "test_daemon_break_even_is_idempotent_when_broker_already_at_entry()" | kind=code-symbol | source=tests/test_daemon_break_even_live.py:L98 | neighbors=[test_daemon_break_even_live.py, BrokerExecutor, LifecycleManager, Provider, Repo, TradeExecutor]
- "tests_test_daemon_break_even_live_test_daemon_does_not_persist_break_even_when_broker_does_not_confirm": "test_daemon_does_not_persist_break_even_when_broker_does_not_confirm()" | kind=code-symbol | source=tests/test_daemon_break_even_live.py:L118 | neighbors=[test_daemon_break_even_live.py, BrokerExecutor, LifecycleManager, Provider, Repo, TradeExecutor]
- "tests_test_daemon_break_even_live_test_daemon_moves_live_position_to_break_even_at_one_r": "test_daemon_moves_live_position_to_break_even_at_one_r()" | kind=code-symbol | source=tests/test_daemon_break_even_live.py:L73 | neighbors=[test_daemon_break_even_live.py, BrokerExecutor, LifecycleManager, Provider, Repo, TradeExecutor]
- "tests_test_daemon_break_even_live_test_runner_moves_to_break_even_when_tp1_closed_even_after_price_retrace": "test_runner_moves_to_break_even_when_tp1_closed_even_after_price_retrace()" | kind=code-symbol | source=tests/test_daemon_break_even_live.py:L163 | neighbors=[test_daemon_break_even_live.py, BrokerExecutor, LifecycleManager, Provider, SplitRepo, TradeExecutor]
- "tests_test_daemon_break_even_live_test_runner_sell_break_even_uses_two_points_in_favorable_direction": "test_runner_sell_break_even_uses_two_points_in_favorable_direction()" | kind=code-symbol | source=tests/test_daemon_break_even_live.py:L200 | neighbors=[test_daemon_break_even_live.py, BrokerExecutor, LifecycleManager, Provider, Repo, TradeExecutor]
- "tests_test_daemon_progress_engine": "Engine" | kind=code-symbol | source=tests/test_daemon_progress.py:L11 | neighbors=[test_daemon_progress.py, LiveTradingConfig, LiveTradingEngine, LiveTradingEngine, .process_symbol(), test_process_symbols_reports_each_symbo…]
- "tests_test_daemon_runner_extension_provider": "Provider" | kind=code-symbol | source=tests/test_daemon_runner_extension.py:L19 | neighbors=[test_daemon_runner_extension.py, _engine(), LiveTradingConfig, LiveTradingEngine, RunnerExtensionDecision, .get_candles()]
- "tests_test_daemon_single_entry_fallback_engine": "_engine()" | kind=code-symbol | source=tests/test_daemon_single_entry_fallback.py:L63 | neighbors=[test_daemon_single_entry_fallback.py, Analyzer, Provider, Repo, test_single_fallback_is_rejected_when_i…, test_split_risk_failure_falls_back_to_o…]
- "tests_test_daemon_split_risk_management_analyzer": "Analyzer" | kind=code-symbol | source=tests/test_daemon_split_risk_management.py:L51 | neighbors=[test_daemon_split_risk_management.py, LiveTradingConfig, LiveTradingEngine, .analyze_symbol(), test_one_percent_operation_is_split_int…, test_smc_runner_extension_uses_4r_broke…]
- "tests_test_execution_preflight_service_fakeprovider": "FakeProvider" | kind=code-symbol | source=tests/test_execution_preflight_service.py:L14 | neighbors=[test_execution_preflight_service.py, ExecutionPreflightService, .account_info(), .ensure_symbol(), .get_symbol_constraints(), test_preflight_reports_ready()]
- "tests_test_execution_preflight_service_fakerepository": "FakeRepository" | kind=code-symbol | source=tests/test_execution_preflight_service.py:L6 | neighbors=[test_execution_preflight_service.py, ExecutionPreflightService, .__init__(), .save_account_snapshot(), test_preflight_accepts_dict_symbol_info…, test_preflight_reports_ready()]
- "tests_test_live_demo_get_analysis": "get_analysis()" | kind=code-symbol | source=tests/test_live_demo.py:L76 | neighbors=[test_live_demo.py, get_diagnostics(), main(), print_analysis_diagnostics(), print_transition_trace(), Devuelve el bloque analysis cuando exis…]
- "tests_test_live_demo_get_diagnostics": "get_diagnostics()" | kind=code-symbol | source=tests/test_live_demo.py:L90 | neighbors=[test_live_demo.py, get_analysis(), main(), print_analysis_diagnostics(), print_transition_trace(), Busca diagnostics en ambos formatos pos…]
- "tests_test_live_demo_print_transition_trace": "print_transition_trace()" | kind=code-symbol | source=tests/test_live_demo.py:L137 | neighbors=[test_live_demo.py, main(), get_analysis(), get_diagnostics(), print_transition(), Reconstruye visualmente el flujo comple…]
- "tests_test_live_demo_smoke_stops_executor": "_Executor" | kind=code-symbol | source=tests/test_live_demo_smoke_stops.py:L46 | neighbors=[test_live_demo_smoke_stops.py, LiveDemoSmokeTestConfig, LiveDemoSmokeTestService, .get_position(), .__init__(), test_smoke_uses_provider_stop_normaliza…]
- "tests_test_live_demo_smoke_stops_test_smoke_uses_provider_stop_normalization": "test_smoke_uses_provider_stop_normalization()" | kind=code-symbol | source=tests/test_live_demo_smoke_stops.py:L84 | neighbors=[test_live_demo_smoke_stops.py, _Executor, _LifecycleManager, _Provider, _Reporting, _Repository]
- "tests_test_live_paper_trading_engine_build_engine": "build_engine()" | kind=code-symbol | source=tests/test_live_paper_trading_engine.py:L52 | neighbors=[test_live_paper_trading_engine.py, test_live_paper_monitor_uses_bid_for_bu…, test_live_paper_opens_from_ready_signal…, test_live_paper_take_profit_moves_lifec…, test_live_paper_uses_ask_for_sell_monit…, test_same_ready_signal_is_not_executed_…]
- "tests_test_live_paper_trading_engine_ready_signal": "ready_signal()" | kind=code-symbol | source=tests/test_live_paper_trading_engine.py:L36 | neighbors=[test_live_paper_trading_engine.py, test_live_paper_monitor_uses_bid_for_bu…, test_live_paper_opens_from_ready_signal…, test_live_paper_take_profit_moves_lifec…, test_live_paper_uses_ask_for_sell_monit…, test_same_ready_signal_is_not_executed_…]
- "tests_test_main_symbol_selection_fakeprovider": "FakeProvider" | kind=code-symbol | source=tests/test_main_symbol_selection.py:L13 | neighbors=[test_main_symbol_selection.py, .ensure_symbol(), .__init__(), test_categories_are_normalized(), test_dynamic_symbols_are_discovered(), test_explicit_symbol_has_priority()]
- "tests_test_orb_gold_contract_selection": "test_orb_gold_contract_selection.py" | kind=code-symbol | source=tests/test_orb_gold_contract_selection.py:L1 | neighbors=[_engine(), Repo, test_gold_selector_chooses_lower_execut…, test_gold_selector_does_not_duplicate_g…, test_gold_selector_skips_expensive_comp…, test_gold_selector_uses_xauusd_when_mic…]
- "tests_test_orb_gold_contract_selection_engine": "_engine()" | kind=code-symbol | source=tests/test_orb_gold_contract_selection.py:L12 | neighbors=[test_orb_gold_contract_selection.py, Repo, test_gold_selector_chooses_lower_execut…, test_gold_selector_does_not_duplicate_g…, test_gold_selector_skips_expensive_comp…, test_gold_selector_uses_xauusd_when_mic…]
- "tests_test_orb_symbol_discovery_fakeprovider": "FakeProvider" | kind=code-symbol | source=tests/test_orb_symbol_discovery.py:L5 | neighbors=[test_orb_symbol_discovery.py, .get_symbol_info(), .__init__(), .search_symbols(), test_discovery_excludes_disabled_orb_co…, test_discovery_includes_both_real_gold_…]
- "tests_test_paper_trade_executor_create_buy_request": "create_buy_request()" | kind=code-symbol | source=tests/test_paper_trade_executor.py:L25 | neighbors=[test_paper_trade_executor.py, test_cannot_close_position_twice(), test_close_position(), test_duplicate_execution_is_blocked(), test_get_position(), test_paper_execute_buy()]
- "tests_test_paper_trade_monitoring_integration_buy_request": "buy_request()" | kind=code-symbol | source=tests/test_paper_trade_monitoring_integration.py:L12 | neighbors=[test_paper_trade_monitoring_integration…, test_execute_registers_position_in_posi…, test_manual_close_syncs_position_manage…, test_monitor_multiple_open_positions_th…, test_monitoring_break_even_syncs_stop_l…, test_monitoring_take_profit_closes_pape…]
- "tests_test_position_manager_create_sell_position": "create_sell_position()" | kind=code-symbol | source=tests/test_position_manager.py:L24 | neighbors=[test_position_manager.py, test_apply_break_even_sell_at_one_to_on…, test_clear_all(), test_close_sell_position(), test_get_open_positions(), test_update_price_sell()]
- "tests_test_ready_to_ambiguous_transition_controlledmultitimeframeanalyzer": "ControlledMultiTimeframeAnalyzer" | kind=code-symbol | source=tests/test_ready_to_ambiguous_transition.py:L238 | neighbors=[test_ready_to_ambiguous_transition.py, MultiTimeframeAnalyzer, MultiTimeframeConfig, MultiTimeframeAnalyzer, ._run_pipeline(), test_controlled_ready_to_enter_to_ambig…]
- "tests_test_ready_to_enter_transition_controlleddataprovider": "ControlledDataProvider" | kind=code-symbol | source=tests/test_ready_to_enter_transition.py:L12 | neighbors=[test_ready_to_enter_transition.py, MultiTimeframeAnalyzer, MultiTimeframeConfig, .get_candles(), Proveedor artificial para una prueba co…, test_controlled_transition_to_ready_to_…]
- "tests_test_ready_to_execution_transition_controlledmultitimeframeanalyzer": "ControlledMultiTimeframeAnalyzer" | kind=code-symbol | source=tests/test_ready_to_execution_transition.py:L238 | neighbors=[test_ready_to_execution_transition.py, MultiTimeframeAnalyzer, MultiTimeframeConfig, MultiTimeframeAnalyzer, ._run_pipeline(), test_controlled_ready_to_enter_to_execu…]
- "tests_test_ready_to_no_exit_transition_controlledmultitimeframeanalyzer": "ControlledMultiTimeframeAnalyzer" | kind=code-symbol | source=tests/test_ready_to_no_exit_transition.py:L412 | neighbors=[test_ready_to_no_exit_transition.py, MultiTimeframeAnalyzer, MultiTimeframeConfig, MultiTimeframeAnalyzer, ._run_pipeline(), test_controlled_ready_to_enter_to_no_ex…]
- "tests_test_ready_to_stop_loss_transition_back_controlledmultitimeframeanalyzer": "ControlledMultiTimeframeAnalyzer" | kind=code-symbol | source=tests/test_ready_to_stop_loss_transition_back.py:L238 | neighbors=[test_ready_to_stop_loss_transition_back…, MultiTimeframeAnalyzer, MultiTimeframeConfig, MultiTimeframeAnalyzer, ._run_pipeline(), test_controlled_ready_to_enter_to_ambig…]
- "tests_test_ready_to_stop_loss_transition_controlledmultitimeframeanalyzer": "ControlledMultiTimeframeAnalyzer" | kind=code-symbol | source=tests/test_ready_to_stop_loss_transition.py:L278 | neighbors=[test_ready_to_stop_loss_transition.py, MultiTimeframeAnalyzer, MultiTimeframeConfig, MultiTimeframeAnalyzer, ._run_pipeline(), test_controlled_ready_to_enter_to_stop_…]
- "tests_test_symbol_direction_policy": "test_symbol_direction_policy.py" | kind=code-symbol | source=tests/test_symbol_direction_policy.py:L1 | neighbors=[symbol_policy.py, test_boom_confirmation_policy_does_not_…, test_boom_is_buy_only(), test_crash_is_sell_only(), test_other_symbols_keep_neutral_policy(), test_pipeline_policy_filter_accepts_lon…]
- "tests_test_trade_lifecycle_integration": "test_trade_lifecycle_integration.py" | kind=code-symbol | source=tests/test_trade_lifecycle_integration.py:L1 | neighbors=[ControlledLifecycleAnalyzer, ControlledLifecycleDataProvider, create_config(), print_case_result(), run_lifecycle(), test_trade_lifecycle_integration()]

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-011.json

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
