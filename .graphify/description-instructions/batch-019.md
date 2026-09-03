# Node Description Batch 20 of 56

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

- "tests_test_ready_to_stop_loss_transition_back_test_controlled_ready_to_enter_to_ambiguous": "test_controlled_ready_to_enter_to_ambiguous()" | kind=code-symbol | source=tests/test_ready_to_stop_loss_transition_back.py:L371 | neighbors=[test_ready_to_stop_loss_transition_back…, ControlledDataProvider, .get_candles(), ControlledMultiTimeframeAnalyzer]
- "tests_test_ready_to_stop_loss_transition_test_controlled_ready_to_enter_to_stop_loss": "test_controlled_ready_to_enter_to_stop_loss()" | kind=code-symbol | source=tests/test_ready_to_stop_loss_transition.py:L411 | neighbors=[test_ready_to_stop_loss_transition.py, ControlledDataProvider, .get_candles(), ControlledMultiTimeframeAnalyzer]
- "tests_test_risk_integration_test_risk_summary": "test_risk_summary()" | kind=code-symbol | source=tests/test_risk_integration.py:L465 | neighbors=[test_risk_integration.py, run_all_tests(), print_result(), print_section()]
- "tests_test_runner_extension_manager": "test_runner_extension_manager.py" | kind=code-symbol | source=tests/test_runner_extension_manager.py:L1 | neighbors=[test_clean_uptrend_can_continue_runner(), test_insufficient_market_data_blocks_ex…, test_rr_price_buy_and_sell(), _uptrend()]
- "tests_test_signal_freshness_engine": "_engine()" | kind=code-symbol | source=tests/test_signal_freshness.py:L63 | neighbors=[test_signal_freshness.py, test_market_signal_blocks_large_entry_d…, test_market_signal_buy_is_invalidated_a…, test_market_signal_sell_is_invalidated_…]
- "tests_test_trade_lifecycle_manager_test_unknown_simulation_result": "test_unknown_simulation_result()" | kind=code-symbol | source=tests/test_trade_lifecycle_manager.py:L816 | neighbors=[test_trade_lifecycle_manager.py, create_candles(), create_controlled_simulator(), create_signal()]
- "tests_test_v41_critical_gates_base": "_base()" | kind=code-symbol | source=tests/test_v41_critical_gates.py:L7 | neighbors=[test_v41_critical_gates.py, test_bos_cannot_be_saved_by_adaptive_sc…, test_choch_cannot_be_saved_by_adaptive_…, test_visible_trade_score_is_capped_at_1…]
- "tests_test_v41_critical_gates_setup": "_setup()" | kind=code-symbol | source=tests/test_v41_critical_gates.py:L19 | neighbors=[test_v41_critical_gates.py, test_bos_cannot_be_saved_by_adaptive_sc…, test_choch_cannot_be_saved_by_adaptive_…, test_visible_trade_score_is_capped_at_1…]
- "tests_test_v45_forex_instrument_catalog_connected": "Connected" | kind=code-symbol | source=tests/test_v45_forex_instrument_catalog.py:L9 | neighbors=[test_v45_forex_instrument_catalog.py, InstrumentManager, .is_connected(), test_tradeable_forex_is_discovered_from…]
- "tests_test_v48_break_even_winrate_recovered_trade": "recovered_trade()" | kind=code-symbol | source=tests/test_v48_break_even_winrate.py:L13 | neighbors=[test_v48_break_even_winrate.py, test_report_exporter_calls_small_positi…, test_screenshot_six_trade_example_becom…, test_small_positive_rr_is_break_even_no…]
- "tests_test_v49_split_synthetic_workers_engine": "_engine()" | kind=code-symbol | source=tests/test_v49_split_synthetic_workers.py:L11 | neighbors=[test_v49_split_synthetic_workers.py, test_legacy_synthetic_magic_is_adopted_…, test_new_magic_trade_is_owned_only_by_e…, test_profile_symbol_matching_is_exclusi…]
- "tests_test_v69_forex_event_scheduler_trade": "_trade()" | kind=code-symbol | source=tests/test_v69_forex_event_scheduler.py:L95 | neighbors=[test_v69_forex_event_scheduler.py, test_forex_currency_exposure_blocks_thi…, test_forex_exposure_does_not_double_cou…, test_forex_total_risk_limit_is_global_a…]
- "tests_test_v74_fast_navigation_service": "_service()" | kind=code-symbol | source=tests/test_v74_fast_navigation.py:L33 | neighbors=[test_v74_fast_navigation.py, Repo, test_instruments_cache_invalidates_afte…, test_instruments_payload_is_light_and_c…]
- "tests_test_v80_trade_audit_detail_tab": "test_v80_trade_audit_detail_tab.py" | kind=code-symbol | source=tests/test_v80_trade_audit_detail_tab.py:L1 | neighbors=[test_account_opens_trade_audit_in_new_t…, test_detail_api_loads_all_snapshots_and…, test_detail_page_exposes_timeline_and_e…, test_trade_audit_has_dedicated_page_and…]
- "tests_test_v84_entry_quality_and_audit_integrity": "test_v84_entry_quality_and_audit_integrity.py" | kind=code-symbol | source=tests/test_v84_entry_quality_and_audit_integrity.py:L1 | neighbors=[repository.py, test_orb_non_correlated_markets_do_not_…, test_orb_unknown_htf_context_is_blocked…, test_reused_trade_id_resets_frozen_iden…]
- "tests_test_v88_single_launch_multibot_gold": "test_v88_single_launch_multibot_gold.py" | kind=code-symbol | source=tests/test_v88_single_launch_multibot_gold.py:L1 | neighbors=[test_coordinator_forces_one_database_pa…, test_coordinator_remains_only_periodic_…, test_full_multibot_contains_gold_before…, test_gold_uses_fast_event_poll_inside_m…]
- "tests_test_v92_windows_launcher_guard": "test_v92_windows_launcher_guard.py" | kind=code-symbol | source=tests/test_v92_windows_launcher_guard.py:L1 | neighbors=[main.py, test_independent_coordinator_is_detecte…, test_python_launcher_parent_is_not_a_du…, test_workers_and_unrelated_python_are_n…]
- "tests_test_v93_latency_optimization_engine": "engine()" | kind=code-symbol | source=tests/test_v93_latency_optimization.py:L28 | neighbors=[test_v93_latency_optimization.py, test_coordinated_worker_sync_never_writ…, test_pre_execution_sync_skips_mt5_witho…, test_standalone_auto_export_remains_com…]
- "tests_test_v93_latency_optimization_test_coordinated_worker_sync_never_writes_xlsx": "test_coordinated_worker_sync_never_writes_xlsx()" | kind=code-symbol | source=tests/test_v93_latency_optimization.py:L40 | neighbors=[test_v93_latency_optimization.py, engine(), Repo, Reporting]
- "tests_test_v93_latency_optimization_test_pre_execution_sync_skips_mt5_without_owned_positions": "test_pre_execution_sync_skips_mt5_without_owned_positions()" | kind=code-symbol | source=tests/test_v93_latency_optimization.py:L57 | neighbors=[test_v93_latency_optimization.py, engine(), Repo, Reporting]
- "tests_test_v93_latency_optimization_test_standalone_auto_export_remains_compatible": "test_standalone_auto_export_remains_compatible()" | kind=code-symbol | source=tests/test_v93_latency_optimization.py:L49 | neighbors=[test_v93_latency_optimization.py, engine(), Repo, Reporting]
- "tests_test_v95_analysis_invalidation_exit_invalid_view": "invalid_view()" | kind=code-symbol | source=tests/test_v95_analysis_invalidation_exit.py:L38 | neighbors=[test_v95_analysis_invalidation_exit.py, test_recovery_protection_closes_after_p…, test_same_evaluation_does_not_inflate_c…, test_two_distinct_invalid_analyses_clos…]
- "tests_test_v95_analysis_invalidation_exit_test_recovery_protection_closes_after_positive_mfe_is_lost": "test_recovery_protection_closes_after_positive_mfe_is_lost()" | kind=code-symbol | source=tests/test_v95_analysis_invalidation_exit.py:L84 | neighbors=[test_v95_analysis_invalidation_exit.py, engine_with_view(), invalid_view(), old_trade()]
- "tests_test_v95_analysis_invalidation_exit_test_same_evaluation_does_not_inflate_confirmation_streak": "test_same_evaluation_does_not_inflate_confirmation_streak()" | kind=code-symbol | source=tests/test_v95_analysis_invalidation_exit.py:L48 | neighbors=[test_v95_analysis_invalidation_exit.py, engine_with_view(), invalid_view(), old_trade()]
- "tests_test_v95_analysis_invalidation_exit_test_two_distinct_invalid_analyses_close_at_loss_cap": "test_two_distinct_invalid_analyses_close_at_loss_cap()" | kind=code-symbol | source=tests/test_v95_analysis_invalidation_exit.py:L64 | neighbors=[test_v95_analysis_invalidation_exit.py, engine_with_view(), invalid_view(), old_trade()]
- "trade_lifecycle_manager_rationale_465": "Cierra una posición activa mediante el executor y finaliza el lifecycle." | kind=entity | source=trade_lifecycle_manager.py:L465 | neighbors=[TradeExecutionRequest, TradeExecutionResult, TradeExecutor, .close_execution()]
- "trade_lifecycle_manager_rationale_586": "Publica cambios relevantes del lifecycle hacia el servicio de reporting." | kind=entity | source=trade_lifecycle_manager.py:L586 | neighbors=[TradeExecutionRequest, TradeExecutionResult, TradeExecutor, ._notify_reporting()]
- "trade_lifecycle_manager_tradelifecyclemanager_execute_with_executor": ".execute_with_executor()" | kind=code-symbol | source=trade_lifecycle_manager.py:L370 | neighbors=[TradeLifecycleManager, .is_final(), ._notify_reporting(), .process_signal_with_executor()]
- "trade_outcome_policy_decisive_outcome": "decisive_outcome()" | kind=code-symbol | source=trade_outcome_policy.py:L23 | neighbors=[trade_outcome_policy.py, is_break_even_rr(), safe_float(), Devuelve WIN / LOSS / BREAK_EVEN / OPEN…]
- "app_main_assert_synthetic_split_architecture": "_assert_synthetic_split_architecture()" | kind=code-symbol | source=app/main.py:L952 | neighbors=[main.py, Falla temprano si se rompe la separació…, run_multi_bot_daemon()]
- "app_main_build_multi_bot_dashboard_catalog": "_build_multi_bot_dashboard_catalog()" | kind=code-symbol | source=app/main.py:L1063 | neighbors=[main.py, Descubre el catálogo completo que debe …, run_multi_bot_daemon()]
- "app_main_filter_external_multibot_coordinators": "_filter_external_multibot_coordinators()" | kind=code-symbol | source=app/main.py:L1771 | neighbors=[main.py, _find_other_multibot_coordinators_windo…, Separa coordinadores reales de los laun…]
- "app_main_multibotinstanceguard_acquire": ".acquire()" | kind=code-symbol | source=app/main.py:L1642 | neighbors=[_acquire_multibot_instance_guard(), _MultiBotInstanceGuard, ._already_running()]
- "app_main_multibotinstanceguard_already_running": "._already_running()" | kind=code-symbol | source=app/main.py:L1630 | neighbors=[_MultiBotInstanceGuard, .acquire(), ._owner()]
- "app_main_multibotinstanceguard_owner": "._owner()" | kind=code-symbol | source=app/main.py:L1623 | neighbors=[_MultiBotInstanceGuard, ._already_running(), .release()]
- "app_main_recover_empty_synthetic_selection": "_recover_empty_synthetic_selection()" | kind=code-symbol | source=app/main.py:L1103 | neighbors=[main.py, Restaura el catálogo sintético si su pr…, run_multi_bot_daemon()]
- "app_main_run_dashboard_only": "run_dashboard_only()" | kind=code-symbol | source=app/main.py:L2246 | neighbors=[main.py, main(), Levanta únicamente la interfaz web usan…]
- "app_main_run_report_daemon": "run_report_daemon()" | kind=code-symbol | source=app/main.py:L2206 | neighbors=[main.py, main(), Único escritor continuo del XLSX cuando…]
- "app_main_run_reset_account_stats": "run_reset_account_stats()" | kind=code-symbol | source=app/main.py:L2343 | neighbors=[main.py, main(), Reinicia la ventana estadística de Cuen…]
- "backtesting_backtest_money_management_calculate_risk_amount": "calculate_risk_amount()" | kind=code-symbol | source=backtesting/backtest_money_management.py:L8 | neighbors=[backtest_money_management.py, apply_money_management(), Calcula cuánto dinero se arriesga     …]

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-019.json

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
