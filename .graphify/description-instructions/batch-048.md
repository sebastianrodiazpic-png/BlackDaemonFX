# Node Description Batch 49 of 56

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

- "tests_test_storage_main": "main()" | kind=code-symbol | source=tests/test_storage.py:L7 | neighbors=[test_storage.py]
- "tests_test_storage_test_account_history_excludes_direct_mt5_history_reconstruction": "test_account_history_excludes_direct_mt5_history_reconstruction()" | kind=code-symbol | source=tests/test_storage.py:L275 | neighbors=[test_storage.py]
- "tests_test_storage_test_account_stats_reset_is_persistent_preserves_open_positions_and_hides_old_closed": "test_account_stats_reset_is_persistent_preserves_open_positions_and_hides_old_c…" | kind=code-symbol | source=tests/test_storage.py:L317 | neighbors=[test_storage.py]
- "tests_test_storage_test_import_mt5_trade_history_recovers_past_daemon_trades_and_is_idempotent": "test_import_mt5_trade_history_recovers_past_daemon_trades_and_is_idempotent()" | kind=code-symbol | source=tests/test_storage.py:L167 | neighbors=[test_storage.py]
- "tests_test_storage_test_import_mt5_trade_history_skips_positions_still_open": "test_import_mt5_trade_history_skips_positions_still_open()" | kind=code-symbol | source=tests/test_storage.py:L245 | neighbors=[test_storage.py]
- "tests_test_storage_test_import_open_mt5_positions_recovers_daemon_and_external": "test_import_open_mt5_positions_recovers_daemon_and_external()" | kind=code-symbol | source=tests/test_storage.py:L82 | neighbors=[test_storage.py]
- "tests_test_storage_test_instrument_selection_preferences_persist_across_repository_restarts": "test_instrument_selection_preferences_persist_across_repository_restarts()" | kind=code-symbol | source=tests/test_storage.py:L396 | neighbors=[test_storage.py]
- "tests_test_storage_test_repository_reset_database_preserves_schema_and_blocks_open_trades": "test_repository_reset_database_preserves_schema_and_blocks_open_trades()" | kind=code-symbol | source=tests/test_storage.py:L59 | neighbors=[test_storage.py]
- "tests_test_storage_test_trade_journal_survives_operational_reset_and_account_reads_history": "test_trade_journal_survives_operational_reset_and_account_reads_history()" | kind=code-symbol | source=tests/test_storage.py:L137 | neighbors=[test_storage.py]
- "tests_test_swings": "test_swings.py" | kind=code-symbol | source=tests/test_swings.py:L1 | neighbors=[main()]
- "tests_test_swings_main": "main()" | kind=code-symbol | source=tests/test_swings.py:L12 | neighbors=[test_swings.py]
- "tests_test_symbol_direction_policy_test_boom_confirmation_policy_does_not_drop_buy_confirmation_after_direction_conversion": "test_boom_confirmation_policy_does_not_drop_buy_confirmation_after_direction_co…" | kind=code-symbol | source=tests/test_symbol_direction_policy.py:L46 | neighbors=[test_symbol_direction_policy.py]
- "tests_test_symbol_direction_policy_test_boom_is_buy_only": "test_boom_is_buy_only()" | kind=code-symbol | source=tests/test_symbol_direction_policy.py:L8 | neighbors=[test_symbol_direction_policy.py]
- "tests_test_symbol_direction_policy_test_crash_is_sell_only": "test_crash_is_sell_only()" | kind=code-symbol | source=tests/test_symbol_direction_policy.py:L15 | neighbors=[test_symbol_direction_policy.py]
- "tests_test_symbol_direction_policy_test_other_symbols_keep_neutral_policy": "test_other_symbols_keep_neutral_policy()" | kind=code-symbol | source=tests/test_symbol_direction_policy.py:L22 | neighbors=[test_symbol_direction_policy.py]
- "tests_test_symbol_direction_policy_test_pipeline_policy_filter_accepts_long_short_and_buy_sell_representations": "test_pipeline_policy_filter_accepts_long_short_and_buy_sell_representations()" | kind=code-symbol | source=tests/test_symbol_direction_policy.py:L27 | neighbors=[test_symbol_direction_policy.py]
- "tests_test_trade_executor_test_execution_request_from_signal": "test_execution_request_from_signal()" | kind=code-symbol | source=tests/test_trade_executor.py:L38 | neighbors=[test_trade_executor.py]
- "tests_test_trade_executor_test_execution_request_invalid_signal": "test_execution_request_invalid_signal()" | kind=code-symbol | source=tests/test_trade_executor.py:L107 | neighbors=[test_trade_executor.py]
- "tests_test_trade_executor_test_trade_executor_is_abstract": "test_trade_executor_is_abstract()" | kind=code-symbol | source=tests/test_trade_executor.py:L15 | neighbors=[test_trade_executor.py]
- "tests_test_trade_lifecycle_full_integration_controlleddataprovider_init": ".__init__()" | kind=code-symbol | source=tests/test_trade_lifecycle_full_integration.py:L39 | neighbors=[ControlledDataProvider]
- "tests_test_trade_lifecycle_full_integration_controlledmultitimeframeanalyzer_run_pipeline": "._run_pipeline()" | kind=code-symbol | source=tests/test_trade_lifecycle_full_integration.py:L231 | neighbors=[ControlledMultiTimeframeAnalyzer]
- "tests_test_trade_lifecycle_integration_controlledlifecycleanalyzer_run_pipeline": "._run_pipeline()" | kind=code-symbol | source=tests/test_trade_lifecycle_integration.py:L545 | neighbors=[ControlledLifecycleAnalyzer]
- "tests_test_trade_lifecycle_integration_controlledlifecycledataprovider_init": ".__init__()" | kind=code-symbol | source=tests/test_trade_lifecycle_integration.py:L52 | neighbors=[ControlledLifecycleDataProvider]
- "tests_test_trade_lifecycle_manager_test_invalid_signal": "test_invalid_signal()" | kind=code-symbol | source=tests/test_trade_lifecycle_manager.py:L879 | neighbors=[test_trade_lifecycle_manager.py]
- "tests_test_trade_pipeline": "test_trade_pipeline.py" | kind=code-symbol | source=tests/test_trade_pipeline.py:L1 | neighbors=[main()]
- "tests_test_trade_pipeline_main": "main()" | kind=code-symbol | source=tests/test_trade_pipeline.py:L9 | neighbors=[test_trade_pipeline.py]
- "tests_test_trade_report_exporter_test_export_trade_report": "test_export_trade_report()" | kind=code-symbol | source=tests/test_trade_report_exporter.py:L9 | neighbors=[test_trade_report_exporter.py]
- "tests_test_trade_simulator": "test_trade_simulator.py" | kind=code-symbol | source=tests/test_trade_simulator.py:L1 | neighbors=[main()]
- "tests_test_trade_simulator_main": "main()" | kind=code-symbol | source=tests/test_trade_simulator.py:L35 | neighbors=[test_trade_simulator.py]
- "tests_test_v100_entry_quarantine_winrate_analyzer_analyze_symbol": ".analyze_symbol()" | kind=code-symbol | source=tests/test_v100_entry_quarantine_winrate.py:L122 | neighbors=[_Analyzer]
- "tests_test_v100_entry_quarantine_winrate_minimumvolumeexecutor_assert_demo_account": ".assert_demo_account()" | kind=code-symbol | source=tests/test_v100_entry_quarantine_winrate.py:L136 | neighbors=[_MinimumVolumeExecutor]
- "tests_test_v100_entry_quarantine_winrate_minimumvolumeexecutor_calculate_volume": ".calculate_volume()" | kind=code-symbol | source=tests/test_v100_entry_quarantine_winrate.py:L148 | neighbors=[_MinimumVolumeExecutor]
- "tests_test_v100_entry_quarantine_winrate_minimumvolumeexecutor_normalize_market_stops": ".normalize_market_stops()" | kind=code-symbol | source=tests/test_v100_entry_quarantine_winrate.py:L139 | neighbors=[_MinimumVolumeExecutor]
- "tests_test_v100_entry_quarantine_winrate_provider_ensure_symbol": ".ensure_symbol()" | kind=code-symbol | source=tests/test_v100_entry_quarantine_winrate.py:L114 | neighbors=[_Provider]
- "tests_test_v100_entry_quarantine_winrate_provider_get_current_tick": ".get_current_tick()" | kind=code-symbol | source=tests/test_v100_entry_quarantine_winrate.py:L117 | neighbors=[_Provider]
- "tests_test_v100_entry_quarantine_winrate_provider_resolve_symbol": ".resolve_symbol()" | kind=code-symbol | source=tests/test_v100_entry_quarantine_winrate.py:L111 | neighbors=[_Provider]
- "tests_test_v100_entry_quarantine_winrate_repo_get_trade_by_execution_key": ".get_trade_by_execution_key()" | kind=code-symbol | source=tests/test_v100_entry_quarantine_winrate.py:L98 | neighbors=[_Repo]
- "tests_test_v100_entry_quarantine_winrate_repo_open_trades": ".open_trades()" | kind=code-symbol | source=tests/test_v100_entry_quarantine_winrate.py:L101 | neighbors=[_Repo]
- "tests_test_v100_entry_quarantine_winrate_repo_save_account_snapshot": ".save_account_snapshot()" | kind=code-symbol | source=tests/test_v100_entry_quarantine_winrate.py:L104 | neighbors=[_Repo]
- "tests_test_v100_entry_quarantine_winrate_repo_save_signal_once": ".save_signal_once()" | kind=code-symbol | source=tests/test_v100_entry_quarantine_winrate.py:L95 | neighbors=[_Repo]

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-048.json

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
