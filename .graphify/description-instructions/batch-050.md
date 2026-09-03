# Node Description Batch 51 of 56

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

- "tests_test_v54_context_health_visual_audit_test_visual_audit_roundtrip": "test_visual_audit_roundtrip()" | kind=code-symbol | source=tests/test_v54_context_health_visual_audit.py:L39 | neighbors=[test_v54_context_health_visual_audit.py]
- "tests_test_v55_persistent_entry_audit_test_dashboard_source_exposes_entry_and_current_toggle": "test_dashboard_source_exposes_entry_and_current_toggle()" | kind=code-symbol | source=tests/test_v55_persistent_entry_audit.py:L45 | neighbors=[test_v55_persistent_entry_audit.py]
- "tests_test_v55_persistent_entry_audit_test_database_model_has_unique_trade_visual_audit": "test_database_model_has_unique_trade_visual_audit()" | kind=code-symbol | source=tests/test_v55_persistent_entry_audit.py:L52 | neighbors=[test_v55_persistent_entry_audit.py]
- "tests_test_v55_persistent_entry_audit_test_trade_entry_visual_audit_is_immutable": "test_trade_entry_visual_audit_is_immutable()" | kind=code-symbol | source=tests/test_v55_persistent_entry_audit.py:L5 | neighbors=[test_v55_persistent_entry_audit.py]
- "tests_test_v55_persistent_entry_audit_test_trade_visual_audit_survives_without_open_trade_row": "test_trade_visual_audit_survives_without_open_trade_row()" | kind=code-symbol | source=tests/test_v55_persistent_entry_audit.py:L32 | neighbors=[test_v55_persistent_entry_audit.py]
- "tests_test_v56_independent_instrument_profiles_test_dashboard_defaults_each_profile_to_its_own_universe": "test_dashboard_defaults_each_profile_to_its_own_universe()" | kind=code-symbol | source=tests/test_v56_independent_instrument_profiles.py:L25 | neighbors=[test_v56_independent_instrument_profile…]
- "tests_test_v56_independent_instrument_profiles_test_dashboard_saves_only_target_profile": "test_dashboard_saves_only_target_profile()" | kind=code-symbol | source=tests/test_v56_independent_instrument_profiles.py:L36 | neighbors=[test_v56_independent_instrument_profile…]
- "tests_test_v56_independent_instrument_profiles_test_empty_forex_selection_is_persistent_and_means_no_new_entries": "test_empty_forex_selection_is_persistent_and_means_no_new_entries()" | kind=code-symbol | source=tests/test_v56_independent_instrument_profiles.py:L48 | neighbors=[test_v56_independent_instrument_profile…]
- "tests_test_v56_independent_instrument_profiles_test_forex_update_does_not_change_orb": "test_forex_update_does_not_change_orb()" | kind=code-symbol | source=tests/test_v56_independent_instrument_profiles.py:L16 | neighbors=[test_v56_independent_instrument_profile…]
- "tests_test_v56_independent_instrument_profiles_test_instrument_page_has_three_profile_tabs": "test_instrument_page_has_three_profile_tabs()" | kind=code-symbol | source=tests/test_v56_independent_instrument_profiles.py:L77 | neighbors=[test_v56_independent_instrument_profile…]
- "tests_test_v56_independent_instrument_profiles_test_profile_mapping": "test_profile_mapping()" | kind=code-symbol | source=tests/test_v56_independent_instrument_profiles.py:L71 | neighbors=[test_v56_independent_instrument_profile…]
- "tests_test_v56_independent_instrument_profiles_test_repository_profiles_are_independent": "test_repository_profiles_are_independent()" | kind=code-symbol | source=tests/test_v56_independent_instrument_profiles.py:L8 | neighbors=[test_v56_independent_instrument_profile…]
- "tests_test_v57_forex_persistence_hardening_test_forex_and_orb_remain_independent_after_restart": "test_forex_and_orb_remain_independent_after_restart()" | kind=code-symbol | source=tests/test_v57_forex_persistence_hardening.py:L51 | neighbors=[test_v57_forex_persistence_hardening.py]
- "tests_test_v57_forex_persistence_hardening_test_forex_survives_repository_restart": "test_forex_survives_repository_restart()" | kind=code-symbol | source=tests/test_v57_forex_persistence_hardening.py:L20 | neighbors=[test_v57_forex_persistence_hardening.py]
- "tests_test_v57_forex_persistence_hardening_test_only_one_authoritative_row_per_profile_after_multiple_saves": "test_only_one_authoritative_row_per_profile_after_multiple_saves()" | kind=code-symbol | source=tests/test_v57_forex_persistence_hardening.py:L62 | neighbors=[test_v57_forex_persistence_hardening.py]
- "tests_test_v58_synthetics_split_dashboard_test_coordinator_dashboard_is_not_conditional_on_dashboard_flag": "test_coordinator_dashboard_is_not_conditional_on_dashboard_flag()" | kind=code-symbol | source=tests/test_v58_synthetics_split_dashboard.py:L13 | neighbors=[test_v58_synthetics_split_dashboard.py]
- "tests_test_v58_synthetics_split_dashboard_test_coordinator_starts_and_stops_one_central_dashboard": "test_coordinator_starts_and_stops_one_central_dashboard()" | kind=code-symbol | source=tests/test_v58_synthetics_split_dashboard.py:L29 | neighbors=[test_v58_synthetics_split_dashboard.py]
- "tests_test_v58_synthetics_split_dashboard_test_split_profiles_are_exactly_six": "test_split_profiles_are_exactly_six()" | kind=code-symbol | source=tests/test_v58_synthetics_split_dashboard.py:L24 | neighbors=[test_v58_synthetics_split_dashboard.py]
- "tests_test_v58_synthetics_split_dashboard_test_synthetics_split_launcher_enables_dashboard": "test_synthetics_split_launcher_enables_dashboard()" | kind=code-symbol | source=tests/test_v58_synthetics_split_dashboard.py:L6 | neighbors=[test_v58_synthetics_split_dashboard.py]
- "tests_test_v58_synthetics_split_dashboard_test_workers_still_do_not_start_individual_dashboards": "test_workers_still_do_not_start_individual_dashboards()" | kind=code-symbol | source=tests/test_v58_synthetics_split_dashboard.py:L18 | neighbors=[test_v58_synthetics_split_dashboard.py]
- "tests_test_v59_synthetic_family_multiprocess_test_coordinator_spawns_per_profile": "test_coordinator_spawns_per_profile()" | kind=code-symbol | source=tests/test_v59_synthetic_family_multiprocess.py:L12 | neighbors=[test_v59_synthetic_family_multiprocess.…]
- "tests_test_v59_synthetic_family_multiprocess_test_exact_six": "test_exact_six()" | kind=code-symbol | source=tests/test_v59_synthetic_family_multiprocess.py:L6 | neighbors=[test_v59_synthetic_family_multiprocess.…]
- "tests_test_v59_synthetic_family_multiprocess_test_launcher": "test_launcher()" | kind=code-symbol | source=tests/test_v59_synthetic_family_multiprocess.py:L15 | neighbors=[test_v59_synthetic_family_multiprocess.…]
- "tests_test_v59_synthetic_family_multiprocess_test_legacy_aggregate_not_in_split": "test_legacy_aggregate_not_in_split()" | kind=code-symbol | source=tests/test_v59_synthetic_family_multiprocess.py:L14 | neighbors=[test_v59_synthetic_family_multiprocess.…]
- "tests_test_v59_synthetic_family_multiprocess_test_split_guard": "test_split_guard()" | kind=code-symbol | source=tests/test_v59_synthetic_family_multiprocess.py:L5 | neighbors=[test_v59_synthetic_family_multiprocess.…]
- "tests_test_v59_synthetic_family_multiprocess_test_unique_family_contracts": "test_unique_family_contracts()" | kind=code-symbol | source=tests/test_v59_synthetic_family_multiprocess.py:L7 | neighbors=[test_v59_synthetic_family_multiprocess.…]
- "tests_test_v60_split_enforced_test_family_architecture_guard_still_passes": "test_family_architecture_guard_still_passes()" | kind=code-symbol | source=tests/test_v60_split_enforced.py:L27 | neighbors=[test_v60_split_enforced.py]
- "tests_test_v60_split_enforced_test_historical_daemon_aliases_route_to_split": "test_historical_daemon_aliases_route_to_split()" | kind=code-symbol | source=tests/test_v60_split_enforced.py:L9 | neighbors=[test_v60_split_enforced.py]
- "tests_test_v60_split_enforced_test_legacy_runtime_is_superseded_by_coordinator": "test_legacy_runtime_is_superseded_by_coordinator()" | kind=code-symbol | source=tests/test_v60_split_enforced.py:L21 | neighbors=[test_v60_split_enforced.py]
- "tests_test_v60_split_enforced_test_legacy_synthetic_daemon_is_not_individual_worker": "test_legacy_synthetic_daemon_is_not_individual_worker()" | kind=code-symbol | source=tests/test_v60_split_enforced.py:L4 | neighbors=[test_v60_split_enforced.py]
- "tests_test_v60_split_enforced_test_split_still_exact_six": "test_split_still_exact_six()" | kind=code-symbol | source=tests/test_v60_split_enforced.py:L16 | neighbors=[test_v60_split_enforced.py]
- "tests_test_v61_orb_m5_retest_risk_test_execute_signal_uses_orb_specific_risk_percent": "test_execute_signal_uses_orb_specific_risk_percent()" | kind=code-symbol | source=tests/test_v61_orb_m5_retest_risk.py:L39 | neighbors=[test_v61_orb_m5_retest_risk.py]
- "tests_test_v61_orb_m5_retest_risk_test_live_orb_risk_is_fixed_to_one_percent_total": "test_live_orb_risk_is_fixed_to_one_percent_total()" | kind=code-symbol | source=tests/test_v61_orb_m5_retest_risk.py:L14 | neighbors=[test_v61_orb_m5_retest_risk.py]
- "tests_test_v61_orb_m5_retest_risk_test_orb_signal_source_requires_retest": "test_orb_signal_source_requires_retest()" | kind=code-symbol | source=tests/test_v61_orb_m5_retest_risk.py:L45 | neighbors=[test_v61_orb_m5_retest_risk.py]
- "tests_test_v61_orb_m5_retest_risk_test_orb_v61_defaults_are_m5_midpoint_and_2r": "test_orb_v61_defaults_are_m5_midpoint_and_2r()" | kind=code-symbol | source=tests/test_v61_orb_m5_retest_risk.py:L6 | neighbors=[test_v61_orb_m5_retest_risk.py]
- "tests_test_v61_orb_m5_retest_risk_test_runner_can_extend_2r_to_3r_and_4r_with_profit_locks": "test_runner_can_extend_2r_to_3r_and_4r_with_profit_locks()" | kind=code-symbol | source=tests/test_v61_orb_m5_retest_risk.py:L23 | neighbors=[test_v61_orb_m5_retest_risk.py]
- "tests_test_v62_chart_pattern_confirmations_test_account_page_exposes_persistent_confirmations": "test_account_page_exposes_persistent_confirmations()" | kind=code-symbol | source=tests/test_v62_chart_pattern_confirmations.py:L73 | neighbors=[test_v62_chart_pattern_confirmations.py]
- "tests_test_v62_chart_pattern_confirmations_test_entry_confirmation_audit_is_persistent_and_immutable": "test_entry_confirmation_audit_is_persistent_and_immutable()" | kind=code-symbol | source=tests/test_v62_chart_pattern_confirmations.py:L39 | neighbors=[test_v62_chart_pattern_confirmations.py]
- "tests_test_v62_chart_pattern_confirmations_test_pattern_is_soft_confluence_by_default": "test_pattern_is_soft_confluence_by_default()" | kind=code-symbol | source=tests/test_v62_chart_pattern_confirmations.py:L33 | neighbors=[test_v62_chart_pattern_confirmations.py]
- "tests_test_v62_chart_pattern_confirmations_test_visual_dashboard_has_chart_pattern_overlay": "test_visual_dashboard_has_chart_pattern_overlay()" | kind=code-symbol | source=tests/test_v62_chart_pattern_confirmations.py:L65 | neighbors=[test_v62_chart_pattern_confirmations.py]

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-050.json

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
