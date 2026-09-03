# Node Description Batch 50 of 56

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

- "tests_test_v100_entry_quarantine_winrate_test_account_exposes_leg_and_logical_setup_win_rates": "test_account_exposes_leg_and_logical_setup_win_rates()" | kind=code-symbol | source=tests/test_v100_entry_quarantine_winrate.py:L219 | neighbors=[test_v100_entry_quarantine_winrate.py]
- "tests_test_v100_entry_quarantine_winrate_test_chart_pattern_tolerance_is_capped_by_recent_range": "test_chart_pattern_tolerance_is_capped_by_recent_range()" | kind=code-symbol | source=tests/test_v100_entry_quarantine_winrate.py:L82 | neighbors=[test_v100_entry_quarantine_winrate.py]
- "tests_test_v100_entry_quarantine_winrate_test_legacy_marginal_quarantine_expires_automatically": "test_legacy_marginal_quarantine_expires_automatically()" | kind=code-symbol | source=tests/test_v100_entry_quarantine_winrate.py:L172 | neighbors=[test_v100_entry_quarantine_winrate.py]
- "tests_test_v100_entry_quarantine_winrate_test_waiting_scheduler_reports_available_symbols_not_zero_of_zero": "test_waiting_scheduler_reports_available_symbols_not_zero_of_zero()" | kind=code-symbol | source=tests/test_v100_entry_quarantine_winrate.py:L192 | neighbors=[test_v100_entry_quarantine_winrate.py]
- "tests_test_v45_forex_instrument_catalog_connected_is_connected": ".is_connected()" | kind=code-symbol | source=tests/test_v45_forex_instrument_catalog.py:L10 | neighbors=[Connected]
- "tests_test_v45_forex_instrument_catalog_test_forex_is_a_default_operational_category": "test_forex_is_a_default_operational_category()" | kind=code-symbol | source=tests/test_v45_forex_instrument_catalog.py:L29 | neighbors=[test_v45_forex_instrument_catalog.py]
- "tests_test_v45_forex_instrument_catalog_test_forex_name_fallback_supports_broker_suffixes": "test_forex_name_fallback_supports_broker_suffixes()" | kind=code-symbol | source=tests/test_v45_forex_instrument_catalog.py:L34 | neighbors=[test_v45_forex_instrument_catalog.py]
- "tests_test_v45_forex_instrument_catalog_test_instrument_manager_unifies_synthetics_and_forex": "test_instrument_manager_unifies_synthetics_and_forex()" | kind=code-symbol | source=tests/test_v45_forex_instrument_catalog.py:L65 | neighbors=[test_v45_forex_instrument_catalog.py]
- "tests_test_v46_total_persistence_test_audit_event_is_append_only_and_queryable": "test_audit_event_is_append_only_and_queryable()" | kind=code-symbol | source=tests/test_v46_total_persistence.py:L24 | neighbors=[test_v46_total_persistence.py]
- "tests_test_v46_total_persistence_test_instrument_selection_also_generates_audit_event": "test_instrument_selection_also_generates_audit_event()" | kind=code-symbol | source=tests/test_v46_total_persistence.py:L75 | neighbors=[test_v46_total_persistence.py]
- "tests_test_v47_multi_bot_architecture_test_magic_numbers_are_unique": "test_magic_numbers_are_unique()" | kind=code-symbol | source=tests/test_v47_multi_bot_architecture.py:L21 | neighbors=[test_v47_multi_bot_architecture.py]
- "tests_test_v47_multi_bot_architecture_test_run_demo_bot_supports_profile_magic_and_centralized_export_flag": "test_run_demo_bot_supports_profile_magic_and_centralized_export_flag()" | kind=code-symbol | source=tests/test_v47_multi_bot_architecture.py:L47 | neighbors=[test_v47_multi_bot_architecture.py]
- "tests_test_v47_multi_bot_architecture_test_sqlite_uses_wal_and_busy_timeout": "test_sqlite_uses_wal_and_busy_timeout()" | kind=code-symbol | source=tests/test_v47_multi_bot_architecture.py:L54 | neighbors=[test_v47_multi_bot_architecture.py]
- "tests_test_v47_multi_bot_architecture_test_windows_launchers_exist": "test_windows_launchers_exist()" | kind=code-symbol | source=tests/test_v47_multi_bot_architecture.py:L63 | neighbors=[test_v47_multi_bot_architecture.py]
- "tests_test_v48_break_even_winrate_test_above_neutral_band_is_decisive_win": "test_above_neutral_band_is_decisive_win()" | kind=code-symbol | source=tests/test_v48_break_even_winrate.py:L108 | neighbors=[test_v48_break_even_winrate.py]
- "tests_test_v48_break_even_winrate_test_small_negative_rr_is_also_break_even": "test_small_negative_rr_is_also_break_even()" | kind=code-symbol | source=tests/test_v48_break_even_winrate.py:L116 | neighbors=[test_v48_break_even_winrate.py]
- "tests_test_v49_split_synthetic_workers_test_each_profile_has_exact_single_category": "test_each_profile_has_exact_single_category()" | kind=code-symbol | source=tests/test_v49_split_synthetic_workers.py:L28 | neighbors=[test_v49_split_synthetic_workers.py]
- "tests_test_v49_split_synthetic_workers_test_full_multi_bot_uses_split_synthetics_plus_forex_orb": "test_full_multi_bot_uses_split_synthetics_plus_forex_orb()" | kind=code-symbol | source=tests/test_v49_split_synthetic_workers.py:L41 | neighbors=[test_v49_split_synthetic_workers.py]
- "tests_test_v49_split_synthetic_workers_test_synthetic_split_profiles_exist_and_have_unique_magic": "test_synthetic_split_profiles_exist_and_have_unique_magic()" | kind=code-symbol | source=tests/test_v49_split_synthetic_workers.py:L21 | neighbors=[test_v49_split_synthetic_workers.py]
- "tests_test_v49_split_synthetic_workers_test_windows_launchers_exist": "test_windows_launchers_exist()" | kind=code-symbol | source=tests/test_v49_split_synthetic_workers.py:L83 | neighbors=[test_v49_split_synthetic_workers.py]
- "tests_test_v50_compact_audit_log_test_compact_audit_log_extracts_key_fields_and_limits_summary": "test_compact_audit_log_extracts_key_fields_and_limits_summary()" | kind=code-symbol | source=tests/test_v50_compact_audit_log.py:L10 | neighbors=[test_v50_compact_audit_log.py]
- "tests_test_v50_compact_audit_log_test_export_does_not_emit_excel_cell_too_long_warning": "test_export_does_not_emit_excel_cell_too_long_warning()" | kind=code-symbol | source=tests/test_v50_compact_audit_log.py:L47 | neighbors=[test_v50_compact_audit_log.py]
- "tests_test_v51_multi_bot_dashboard_test_coordinator_source_contains_single_dashboard_start": "test_coordinator_source_contains_single_dashboard_start()" | kind=code-symbol | source=tests/test_v51_multi_bot_dashboard.py:L24 | neighbors=[test_v51_multi_bot_dashboard.py]
- "tests_test_v51_multi_bot_dashboard_test_dashboard_catalog_helper_exists": "test_dashboard_catalog_helper_exists()" | kind=code-symbol | source=tests/test_v51_multi_bot_dashboard.py:L14 | neighbors=[test_v51_multi_bot_dashboard.py]
- "tests_test_v51_multi_bot_dashboard_test_multi_bot_daemon_accepts_dashboard_flags_via_args": "test_multi_bot_daemon_accepts_dashboard_flags_via_args()" | kind=code-symbol | source=tests/test_v51_multi_bot_dashboard.py:L8 | neighbors=[test_v51_multi_bot_dashboard.py]
- "tests_test_v51_multi_bot_dashboard_test_split_profiles_remain_same": "test_split_profiles_remain_same()" | kind=code-symbol | source=tests/test_v51_multi_bot_dashboard.py:L18 | neighbors=[test_v51_multi_bot_dashboard.py]
- "tests_test_v52_worker_family_dashboard_test_dashboard_html_contains_family_worker_grid": "test_dashboard_html_contains_family_worker_grid()" | kind=code-symbol | source=tests/test_v52_worker_family_dashboard.py:L38 | neighbors=[test_v52_worker_family_dashboard.py]
- "tests_test_v52_worker_family_dashboard_test_dashboard_snapshot_exposes_workers": "test_dashboard_snapshot_exposes_workers()" | kind=code-symbol | source=tests/test_v52_worker_family_dashboard.py:L25 | neighbors=[test_v52_worker_family_dashboard.py]
- "tests_test_v52_worker_family_dashboard_test_worker_runtime_state_roundtrip": "test_worker_runtime_state_roundtrip()" | kind=code-symbol | source=tests/test_v52_worker_family_dashboard.py:L6 | neighbors=[test_v52_worker_family_dashboard.py]
- "tests_test_v53_runtime_telemetry_utf8_test_console_reporter_no_problematic_warning_symbols": "test_console_reporter_no_problematic_warning_symbols()" | kind=code-symbol | source=tests/test_v53_runtime_telemetry_utf8.py:L31 | neighbors=[test_v53_runtime_telemetry_utf8.py]
- "tests_test_v53_runtime_telemetry_utf8_test_coordinator_has_worker_console_summary": "test_coordinator_has_worker_console_summary()" | kind=code-symbol | source=tests/test_v53_runtime_telemetry_utf8.py:L44 | neighbors=[test_v53_runtime_telemetry_utf8.py]
- "tests_test_v53_runtime_telemetry_utf8_test_runtime_compatibility_guard_passes_on_clean_v53": "test_runtime_compatibility_guard_passes_on_clean_v53()" | kind=code-symbol | source=tests/test_v53_runtime_telemetry_utf8.py:L11 | neighbors=[test_v53_runtime_telemetry_utf8.py]
- "tests_test_v53_runtime_telemetry_utf8_test_runtime_persistence_happens_before_audit_save_in_source": "test_runtime_persistence_happens_before_audit_save_in_source()" | kind=code-symbol | source=tests/test_v53_runtime_telemetry_utf8.py:L38 | neighbors=[test_v53_runtime_telemetry_utf8.py]
- "tests_test_v53_runtime_telemetry_utf8_test_worker_state_survives_and_dashboard_exposes_version": "test_worker_state_survives_and_dashboard_exposes_version()" | kind=code-symbol | source=tests/test_v53_runtime_telemetry_utf8.py:L16 | neighbors=[test_v53_runtime_telemetry_utf8.py]
- "tests_test_v54_context_health_visual_audit_test_dashboard_html_has_context_tabs_and_owner_column": "test_dashboard_html_has_context_tabs_and_owner_column()" | kind=code-symbol | source=tests/test_v54_context_health_visual_audit.py:L104 | neighbors=[test_v54_context_health_visual_audit.py]
- "tests_test_v54_context_health_visual_audit_test_dashboard_snapshot_exposes_worker_candidates_and_visual_health": "test_dashboard_snapshot_exposes_worker_candidates_and_visual_health()" | kind=code-symbol | source=tests/test_v54_context_health_visual_audit.py:L82 | neighbors=[test_v54_context_health_visual_audit.py]
- "tests_test_v54_context_health_visual_audit_test_external_with_known_daemon_magic_is_flagged_for_reconciliation": "test_external_with_known_daemon_magic_is_flagged_for_reconciliation()" | kind=code-symbol | source=tests/test_v54_context_health_visual_audit.py:L30 | neighbors=[test_v54_context_health_visual_audit.py]
- "tests_test_v54_context_health_visual_audit_test_latest_worker_candidate_is_read_from_append_only_audit": "test_latest_worker_candidate_is_read_from_append_only_audit()" | kind=code-symbol | source=tests/test_v54_context_health_visual_audit.py:L56 | neighbors=[test_v54_context_health_visual_audit.py]
- "tests_test_v54_context_health_visual_audit_test_legacy_daemon_magic_infers_correct_owner": "test_legacy_daemon_magic_infers_correct_owner()" | kind=code-symbol | source=tests/test_v54_context_health_visual_audit.py:L21 | neighbors=[test_v54_context_health_visual_audit.py]
- "tests_test_v54_context_health_visual_audit_test_symbol_owner_inference_by_family": "test_symbol_owner_inference_by_family()" | kind=code-symbol | source=tests/test_v54_context_health_visual_audit.py:L10 | neighbors=[test_v54_context_health_visual_audit.py]

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-049.json

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
