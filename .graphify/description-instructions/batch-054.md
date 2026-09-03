# Node Description Batch 55 of 56

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

- "tests_test_v85_orb_correlation_synthetic_parity_test_synthetics_share_forex_progressive_smc_management": "test_synthetics_share_forex_progressive_smc_management()" | kind=code-symbol | source=tests/test_v85_orb_correlation_synthetic_parity.py:L56 | neighbors=[test_v85_orb_correlation_synthetic_pari…]
- "tests_test_v86_durable_trade_audit_export_entryauditrepo_init": ".__init__()" | kind=code-symbol | source=tests/test_v86_durable_trade_audit_export.py:L9 | neighbors=[EntryAuditRepo]
- "tests_test_v86_durable_trade_audit_export_entryauditrepo_save_trade_audit_snapshot": ".save_trade_audit_snapshot()" | kind=code-symbol | source=tests/test_v86_durable_trade_audit_export.py:L19 | neighbors=[EntryAuditRepo]
- "tests_test_v86_durable_trade_audit_export_entryauditrepo_trade_audit_snapshots": ".trade_audit_snapshots()" | kind=code-symbol | source=tests/test_v86_durable_trade_audit_export.py:L16 | neighbors=[EntryAuditRepo]
- "tests_test_v86_durable_trade_audit_export_entryauditrepo_upsert_trade_visual_audit": ".upsert_trade_visual_audit()" | kind=code-symbol | source=tests/test_v86_durable_trade_audit_export.py:L13 | neighbors=[EntryAuditRepo]
- "tests_test_v86_durable_trade_audit_export_test_audit_page_excludes_snapshot_from_another_ticket_and_remains_exportable": "test_audit_page_excludes_snapshot_from_another_ticket_and_remains_exportable()" | kind=code-symbol | source=tests/test_v86_durable_trade_audit_export.py:L90 | neighbors=[test_v86_durable_trade_audit_export.py]
- "tests_test_v86_durable_trade_audit_export_test_audit_page_falls_back_to_immutable_visual_entry_when_history_is_empty": "test_audit_page_falls_back_to_immutable_visual_entry_when_history_is_empty()" | kind=code-symbol | source=tests/test_v86_durable_trade_audit_export.py:L61 | neighbors=[test_v86_durable_trade_audit_export.py]
- "tests_test_v86_durable_trade_audit_export_test_audit_page_recovers_entry_thesis_from_canonical_trade": "test_audit_page_recovers_entry_thesis_from_canonical_trade()" | kind=code-symbol | source=tests/test_v86_durable_trade_audit_export.py:L121 | neighbors=[test_v86_durable_trade_audit_export.py]
- "tests_test_v87_gold_asia_new_york_session_test_gold_profile_is_independent_and_uses_orb_gold_selection": "test_gold_profile_is_independent_and_uses_orb_gold_selection()" | kind=code-symbol | source=tests/test_v87_gold_asia_new_york_session.py:L14 | neighbors=[test_v87_gold_asia_new_york_session.py]
- "tests_test_v88_single_launch_multibot_gold_test_coordinator_forces_one_database_path_for_every_worker": "test_coordinator_forces_one_database_path_for_every_worker()" | kind=code-symbol | source=tests/test_v88_single_launch_multibot_gold.py:L12 | neighbors=[test_v88_single_launch_multibot_gold.py]
- "tests_test_v88_single_launch_multibot_gold_test_coordinator_remains_only_periodic_xlsx_writer": "test_coordinator_remains_only_periodic_xlsx_writer()" | kind=code-symbol | source=tests/test_v88_single_launch_multibot_gold.py:L21 | neighbors=[test_v88_single_launch_multibot_gold.py]
- "tests_test_v88_single_launch_multibot_gold_test_full_multibot_contains_gold_before_orb_and_unique_workers": "test_full_multibot_contains_gold_before_orb_and_unique_workers()" | kind=code-symbol | source=tests/test_v88_single_launch_multibot_gold.py:L4 | neighbors=[test_v88_single_launch_multibot_gold.py]
- "tests_test_v88_single_launch_multibot_gold_test_gold_uses_fast_event_poll_inside_multibot": "test_gold_uses_fast_event_poll_inside_multibot()" | kind=code-symbol | source=tests/test_v88_single_launch_multibot_gold.py:L27 | neighbors=[test_v88_single_launch_multibot_gold.py]
- "tests_test_v90_multibot_single_instance_test_lock_can_be_acquired_after_clean_release": "test_lock_can_be_acquired_after_clean_release()" | kind=code-symbol | source=tests/test_v90_multibot_single_instance.py:L21 | neighbors=[test_v90_multibot_single_instance.py]
- "tests_test_v90_multibot_single_instance_test_second_coordinator_is_rejected_before_workers": "test_second_coordinator_is_rejected_before_workers()" | kind=code-symbol | source=tests/test_v90_multibot_single_instance.py:L8 | neighbors=[test_v90_multibot_single_instance.py]
- "tests_test_v91_legacy_multibot_guard_test_legacy_coordinator_aborts_after_releasing_new_guard": "test_legacy_coordinator_aborts_after_releasing_new_guard()" | kind=code-symbol | source=tests/test_v91_legacy_multibot_guard.py:L4 | neighbors=[test_v91_legacy_multibot_guard.py]
- "tests_test_v91_legacy_multibot_guard_test_without_legacy_coordinator_guard_remains_active": "test_without_legacy_coordinator_guard_remains_active()" | kind=code-symbol | source=tests/test_v91_legacy_multibot_guard.py:L35 | neighbors=[test_v91_legacy_multibot_guard.py]
- "tests_test_v92_windows_launcher_guard_test_independent_coordinator_is_detected_but_own_launcher_is_excluded": "test_independent_coordinator_is_detected_but_own_launcher_is_excluded()" | kind=code-symbol | source=tests/test_v92_windows_launcher_guard.py:L16 | neighbors=[test_v92_windows_launcher_guard.py]
- "tests_test_v92_windows_launcher_guard_test_python_launcher_parent_is_not_a_duplicate": "test_python_launcher_parent_is_not_a_duplicate()" | kind=code-symbol | source=tests/test_v92_windows_launcher_guard.py:L7 | neighbors=[test_v92_windows_launcher_guard.py]
- "tests_test_v92_windows_launcher_guard_test_workers_and_unrelated_python_are_not_coordinators": "test_workers_and_unrelated_python_are_not_coordinators()" | kind=code-symbol | source=tests/test_v92_windows_launcher_guard.py:L26 | neighbors=[test_v92_windows_launcher_guard.py]
- "tests_test_v93_latency_optimization_repo_init": ".__init__()" | kind=code-symbol | source=tests/test_v93_latency_optimization.py:L7 | neighbors=[Repo]
- "tests_test_v93_latency_optimization_repo_open_trades": ".open_trades()" | kind=code-symbol | source=tests/test_v93_latency_optimization.py:L11 | neighbors=[Repo]
- "tests_test_v93_latency_optimization_repo_sync_closed_mt5_trades": ".sync_closed_mt5_trades()" | kind=code-symbol | source=tests/test_v93_latency_optimization.py:L14 | neighbors=[Repo]
- "tests_test_v93_latency_optimization_reporting_export_now": ".export_now()" | kind=code-symbol | source=tests/test_v93_latency_optimization.py:L24 | neighbors=[Reporting]
- "tests_test_v93_latency_optimization_reporting_init": ".__init__()" | kind=code-symbol | source=tests/test_v93_latency_optimization.py:L20 | neighbors=[Reporting]
- "tests_test_v95_analysis_invalidation_exit_repo_init": ".__init__()" | kind=code-symbol | source=tests/test_v95_analysis_invalidation_exit.py:L8 | neighbors=[Repo]
- "tests_test_v95_analysis_invalidation_exit_repo_update_trade": ".update_trade()" | kind=code-symbol | source=tests/test_v95_analysis_invalidation_exit.py:L11 | neighbors=[Repo]
- "tests_test_v96_arps_synthetic_scalper_test_adx_math_returns_finite_values_for_directional_data": "test_adx_math_returns_finite_values_for_directional_data()" | kind=code-symbol | source=tests/test_v96_arps_synthetic_scalper.py:L64 | neighbors=[test_v96_arps_synthetic_scalper.py]
- "tests_test_v96_arps_synthetic_scalper_test_arps_execution_key_and_risk_config_are_distinguishable": "test_arps_execution_key_and_risk_config_are_distinguishable()" | kind=code-symbol | source=tests/test_v96_arps_synthetic_scalper.py:L27 | neighbors=[test_v96_arps_synthetic_scalper.py]
- "tests_test_v96_arps_synthetic_scalper_test_arps_three_minute_exit_closes_when_mfe_never_expands": "test_arps_three_minute_exit_closes_when_mfe_never_expands()" | kind=code-symbol | source=tests/test_v96_arps_synthetic_scalper.py:L79 | neighbors=[test_v96_arps_synthetic_scalper.py]
- "tests_test_v96_arps_synthetic_scalper_test_family_direction_policy_is_preserved": "test_family_direction_policy_is_preserved()" | kind=code-symbol | source=tests/test_v96_arps_synthetic_scalper.py:L38 | neighbors=[test_v96_arps_synthetic_scalper.py]
- "tests_test_v96_arps_synthetic_scalper_test_parallel_arps_profiles_have_unique_modes_and_magics": "test_parallel_arps_profiles_have_unique_modes_and_magics()" | kind=code-symbol | source=tests/test_v96_arps_synthetic_scalper.py:L17 | neighbors=[test_v96_arps_synthetic_scalper.py]
- "tests_test_v96_arps_synthetic_scalper_test_report_exposes_strategy_identifier_version_profile_and_magic": "test_report_exposes_strategy_identifier_version_profile_and_magic()" | kind=code-symbol | source=tests/test_v96_arps_synthetic_scalper.py:L47 | neighbors=[test_v96_arps_synthetic_scalper.py]
- "tests_test_v98_persistence_latency_retention_test_background_monitor_is_enabled_without_changing_strategy_thresholds": "test_background_monitor_is_enabled_without_changing_strategy_thresholds()" | kind=code-symbol | source=tests/test_v98_persistence_latency_retention.py:L233 | neighbors=[test_v98_persistence_latency_retention.…]
- "tests_test_v98_persistence_latency_retention_test_repeated_waiting_evaluation_is_sampled_but_runtime_keeps_updating": "test_repeated_waiting_evaluation_is_sampled_but_runtime_keeps_updating()" | kind=code-symbol | source=tests/test_v98_persistence_latency_retention.py:L178 | neighbors=[test_v98_persistence_latency_retention.…]
- "tests_test_v98_persistence_latency_retention_test_retention_deletes_only_old_operational_events": "test_retention_deletes_only_old_operational_events()" | kind=code-symbol | source=tests/test_v98_persistence_latency_retention.py:L70 | neighbors=[test_v98_persistence_latency_retention.…]
- "tests_test_v98_persistence_latency_retention_test_sqlite_backup_closes_both_handles_before_windows_replace": "test_sqlite_backup_closes_both_handles_before_windows_replace()" | kind=code-symbol | source=tests/test_v98_persistence_latency_retention.py:L35 | neighbors=[test_v98_persistence_latency_retention.…]
- "tests_test_v98_persistence_latency_retention_test_sqlite_backup_includes_committed_wal_and_is_integral": "test_sqlite_backup_includes_committed_wal_and_is_integral()" | kind=code-symbol | source=tests/test_v98_persistence_latency_retention.py:L13 | neighbors=[test_v98_persistence_latency_retention.…]
- "tests_test_v98_persistence_latency_retention_test_strategy_evaluation_summarizes_arps_and_risk_without_changing_thresholds": "test_strategy_evaluation_summarizes_arps_and_risk_without_changing_thresholds()" | kind=code-symbol | source=tests/test_v98_persistence_latency_retention.py:L134 | neighbors=[test_v98_persistence_latency_retention.…]
- "tests_test_v98_persistence_latency_retention_test_symbol_audit_payload_is_compact_and_keeps_arps_metrics": "test_symbol_audit_payload_is_compact_and_keeps_arps_metrics()" | kind=code-symbol | source=tests/test_v98_persistence_latency_retention.py:L101 | neighbors=[test_v98_persistence_latency_retention.…]

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-054.json

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
