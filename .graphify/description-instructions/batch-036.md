# Node Description Batch 37 of 56

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

- "tests_test_trade_lifecycle_full_integration_controlleddataprovider_m5": "._m5()" | kind=code-symbol | source=tests/test_trade_lifecycle_full_integration.py:L153 | neighbors=[ControlledDataProvider, .get_candles()]
- "tests_test_trade_lifecycle_full_integration_create_config": "create_config()" | kind=code-symbol | source=tests/test_trade_lifecycle_full_integration.py:L322 | neighbors=[test_trade_lifecycle_full_integration.py, test_trade_lifecycle_full_integration()]
- "tests_test_trade_lifecycle_integration_controlledlifecycledataprovider_build_m5_candles": "._build_m5_candles()" | kind=code-symbol | source=tests/test_trade_lifecycle_integration.py:L338 | neighbors=[ControlledLifecycleDataProvider, .get_candles()]
- "tests_test_trade_lifecycle_integration_create_config": "create_config()" | kind=code-symbol | source=tests/test_trade_lifecycle_integration.py:L695 | neighbors=[test_trade_lifecycle_integration.py, run_lifecycle()]
- "tests_test_trade_lifecycle_integration_print_case_result": "print_case_result()" | kind=code-symbol | source=tests/test_trade_lifecycle_integration.py:L974 | neighbors=[test_trade_lifecycle_integration.py, test_trade_lifecycle_integration()]
- "tests_test_trade_lifecycle_manager_create_ambiguous_result": "create_ambiguous_result()" | kind=code-symbol | source=tests/test_trade_lifecycle_manager.py:L208 | neighbors=[test_trade_lifecycle_manager.py, test_lifecycle_ambiguous()]
- "tests_test_trade_lifecycle_manager_create_expired_result": "create_expired_result()" | kind=code-symbol | source=tests/test_trade_lifecycle_manager.py:L232 | neighbors=[test_trade_lifecycle_manager.py, test_lifecycle_expired()]
- "tests_test_trade_lifecycle_manager_create_loss_result": "create_loss_result()" | kind=code-symbol | source=tests/test_trade_lifecycle_manager.py:L184 | neighbors=[test_trade_lifecycle_manager.py, test_lifecycle_loss()]
- "tests_test_trade_lifecycle_manager_test_create_lifecycle_from_signal": "test_create_lifecycle_from_signal()" | kind=code-symbol | source=tests/test_trade_lifecycle_manager.py:L258 | neighbors=[test_trade_lifecycle_manager.py, create_signal()]
- "tests_test_trade_lifecycle_paper_integration_test_full_paper_lifecycle_break_even_stop_is_final": "test_full_paper_lifecycle_break_even_stop_is_final()" | kind=code-symbol | source=tests/test_trade_lifecycle_paper_integration.py:L97 | neighbors=[test_trade_lifecycle_paper_integration.…, signal()]
- "tests_test_trade_lifecycle_paper_integration_test_full_paper_lifecycle_open_and_break_even": "test_full_paper_lifecycle_open_and_break_even()" | kind=code-symbol | source=tests/test_trade_lifecycle_paper_integration.py:L40 | neighbors=[test_trade_lifecycle_paper_integration.…, signal()]
- "tests_test_trade_lifecycle_paper_integration_test_full_paper_lifecycle_stop_loss_to_loss": "test_full_paper_lifecycle_stop_loss_to_loss()" | kind=code-symbol | source=tests/test_trade_lifecycle_paper_integration.py:L80 | neighbors=[test_trade_lifecycle_paper_integration.…, signal()]
- "tests_test_trade_lifecycle_paper_integration_test_full_paper_lifecycle_take_profit_to_win_and_history": "test_full_paper_lifecycle_take_profit_to_win_and_history()" | kind=code-symbol | source=tests/test_trade_lifecycle_paper_integration.py:L61 | neighbors=[test_trade_lifecycle_paper_integration.…, signal()]
- "tests_test_trade_lifecycle_paper_integration_test_monitor_multiple_active_lifecycles": "test_monitor_multiple_active_lifecycles()" | kind=code-symbol | source=tests/test_trade_lifecycle_paper_integration.py:L116 | neighbors=[test_trade_lifecycle_paper_integration.…, signal()]
- "tests_test_trade_lifecycle_paper_integration_test_rejected_executor_result_does_not_create_active_lifecycle": "test_rejected_executor_result_does_not_create_active_lifecycle()" | kind=code-symbol | source=tests/test_trade_lifecycle_paper_integration.py:L137 | neighbors=[test_trade_lifecycle_paper_integration.…, signal()]
- "tests_test_trade_reporting_service_create_signal": "create_signal()" | kind=code-symbol | source=tests/test_trade_reporting_service.py:L18 | neighbors=[test_trade_reporting_service.py, test_paper_lifecycle_is_persisted_and_e…]
- "tests_test_trade_reporting_service_test_paper_lifecycle_is_persisted_and_exported": "test_paper_lifecycle_is_persisted_and_exported()" | kind=code-symbol | source=tests/test_trade_reporting_service.py:L32 | neighbors=[test_trade_reporting_service.py, create_signal()]
- "tests_test_v45_forex_instrument_catalog_info": "_info()" | kind=code-symbol | source=tests/test_v45_forex_instrument_catalog.py:L14 | neighbors=[test_v45_forex_instrument_catalog.py, test_tradeable_forex_is_discovered_from…]
- "tests_test_v46_total_persistence_test_filled_lifecycle_persists_trade_journal_and_audit": "test_filled_lifecycle_persists_trade_journal_and_audit()" | kind=code-symbol | source=tests/test_v46_total_persistence.py:L47 | neighbors=[test_v46_total_persistence.py, signal()]
- "tests_test_v46_total_persistence_test_xlsx_contains_permanent_trades_and_audit_log": "test_xlsx_contains_permanent_trades_and_audit_log()" | kind=code-symbol | source=tests/test_v46_total_persistence.py:L82 | neighbors=[test_v46_total_persistence.py, signal()]
- "tests_test_v47_multi_bot_architecture_test_legacy_trade_is_only_owned_by_historical_synthetics_bot": "test_legacy_trade_is_only_owned_by_historical_synthetics_bot()" | kind=code-symbol | source=tests/test_v47_multi_bot_architecture.py:L40 | neighbors=[test_v47_multi_bot_architecture.py, _engine()]
- "tests_test_v47_multi_bot_architecture_test_trade_ownership_by_magic": "test_trade_ownership_by_magic()" | kind=code-symbol | source=tests/test_v47_multi_bot_architecture.py:L29 | neighbors=[test_v47_multi_bot_architecture.py, _engine()]
- "tests_test_v48_break_even_winrate_test_report_exporter_calls_small_positive_rr_break_even": "test_report_exporter_calls_small_positive_rr_break_even()" | kind=code-symbol | source=tests/test_v48_break_even_winrate.py:L101 | neighbors=[test_v48_break_even_winrate.py, recovered_trade()]
- "tests_test_v48_break_even_winrate_test_screenshot_six_trade_example_becomes_40_percent_winrate": "test_screenshot_six_trade_example_becomes_40_percent_winrate()" | kind=code-symbol | source=tests/test_v48_break_even_winrate.py:L43 | neighbors=[test_v48_break_even_winrate.py, recovered_trade()]
- "tests_test_v48_break_even_winrate_test_small_positive_rr_is_break_even_not_win": "test_small_positive_rr_is_break_even_not_win()" | kind=code-symbol | source=tests/test_v48_break_even_winrate.py:L30 | neighbors=[test_v48_break_even_winrate.py, recovered_trade()]
- "tests_test_v49_split_synthetic_workers_test_legacy_synthetic_magic_is_adopted_only_by_matching_family": "test_legacy_synthetic_magic_is_adopted_only_by_matching_family()" | kind=code-symbol | source=tests/test_v49_split_synthetic_workers.py:L61 | neighbors=[test_v49_split_synthetic_workers.py, _engine()]
- "tests_test_v49_split_synthetic_workers_test_new_magic_trade_is_owned_only_by_exact_worker": "test_new_magic_trade_is_owned_only_by_exact_worker()" | kind=code-symbol | source=tests/test_v49_split_synthetic_workers.py:L72 | neighbors=[test_v49_split_synthetic_workers.py, _engine()]
- "tests_test_v49_split_synthetic_workers_test_profile_symbol_matching_is_exclusive_for_main_families": "test_profile_symbol_matching_is_exclusive_for_main_families()" | kind=code-symbol | source=tests/test_v49_split_synthetic_workers.py:L51 | neighbors=[test_v49_split_synthetic_workers.py, _engine()]
- "tests_test_v56_independent_instrument_profiles_engine": "_engine()" | kind=code-symbol | source=tests/test_v56_independent_instrument_profiles.py:L54 | neighbors=[test_v56_independent_instrument_profile…, test_workers_read_profile_selection_eac…]
- "tests_test_v56_independent_instrument_profiles_test_workers_read_profile_selection_each_cycle": "test_workers_read_profile_selection_each_cycle()" | kind=code-symbol | source=tests/test_v56_independent_instrument_profiles.py:L60 | neighbors=[test_v56_independent_instrument_profile…, _engine()]
- "tests_test_v57_forex_persistence_hardening_test_empty_forex_selection_is_persistent_and_not_replaced_by_full_catalog": "test_empty_forex_selection_is_persistent_and_not_replaced_by_full_catalog()" | kind=code-symbol | source=tests/test_v57_forex_persistence_hardening.py:L81 | neighbors=[test_v57_forex_persistence_hardening.py, catalog()]
- "tests_test_v57_forex_persistence_hardening_test_forex_survives_dashboard_restart_and_stale_state_file": "test_forex_survives_dashboard_restart_and_stale_state_file()" | kind=code-symbol | source=tests/test_v57_forex_persistence_hardening.py:L30 | neighbors=[test_v57_forex_persistence_hardening.py, catalog()]
- "tests_test_v62_chart_pattern_confirmations_double_bottom": "_double_bottom()" | kind=code-symbol | source=tests/test_v62_chart_pattern_confirmations.py:L11 | neighbors=[test_v62_chart_pattern_confirmations.py, test_double_bottom_is_detected_and_alig…]
- "tests_test_v62_chart_pattern_confirmations_test_double_bottom_is_detected_and_aligned_for_buy": "test_double_bottom_is_detected_and_aligned_for_buy()" | kind=code-symbol | source=tests/test_v62_chart_pattern_confirmations.py:L20 | neighbors=[test_v62_chart_pattern_confirmations.py, _double_bottom()]
- "tests_test_v63_account_db_continuity_test_nonempty_stable_db_is_never_overwritten": "test_nonempty_stable_db_is_never_overwritten()" | kind=code-symbol | source=tests/test_v63_account_db_continuity.py:L40 | neighbors=[test_v63_account_db_continuity.py, _make_legacy_db()]
- "tests_test_v63_account_db_continuity_test_stable_db_recovers_nonempty_sibling_legacy_db": "test_stable_db_recovers_nonempty_sibling_legacy_db()" | kind=code-symbol | source=tests/test_v63_account_db_continuity.py:L24 | neighbors=[test_v63_account_db_continuity.py, _make_legacy_db()]
- "tests_test_v66_smc_tp4_be_plus2_test_tp1_close_immediately_protects_runner_at_be_plus_two_points": "test_tp1_close_immediately_protects_runner_at_be_plus_two_points()" | kind=code-symbol | source=tests/test_v66_smc_tp4_be_plus2.py:L105 | neighbors=[test_v66_smc_tp4_be_plus2.py, _engine()]
- "tests_test_v68_persistent_entry_vs_now_dataset_test_account_exposes_entry_vs_now_history_using_source_trade_id": "test_account_exposes_entry_vs_now_history_using_source_trade_id()" | kind=code-symbol | source=tests/test_v68_persistent_entry_vs_now_dataset.py:L70 | neighbors=[test_v68_persistent_entry_vs_now_datase…, _repo_with_trade()]
- "tests_test_v68_persistent_entry_vs_now_dataset_test_snapshot_dataframe_contains_research_columns": "test_snapshot_dataframe_contains_research_columns()" | kind=code-symbol | source=tests/test_v68_persistent_entry_vs_now_dataset.py:L109 | neighbors=[test_v68_persistent_entry_vs_now_datase…, _repo_with_trade()]
- "tests_test_v68_persistent_entry_vs_now_dataset_test_snapshot_history_is_append_only_and_persistent": "test_snapshot_history_is_append_only_and_persistent()" | kind=code-symbol | source=tests/test_v68_persistent_entry_vs_now_dataset.py:L46 | neighbors=[test_v68_persistent_entry_vs_now_datase…, _repo_with_trade()]

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-036.json

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
