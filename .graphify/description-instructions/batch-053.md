# Node Description Batch 54 of 56

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

- "tests_test_v74_fast_navigation_test_dashboard_main_still_uses_state_endpoint": "test_dashboard_main_still_uses_state_endpoint()" | kind=code-symbol | source=tests/test_v74_fast_navigation.py:L74 | neighbors=[test_v74_fast_navigation.py]
- "tests_test_v74_fast_navigation_test_dashboard_source_has_dedicated_instruments_endpoint": "test_dashboard_source_has_dedicated_instruments_endpoint()" | kind=code-symbol | source=tests/test_v74_fast_navigation.py:L67 | neighbors=[test_v74_fast_navigation.py]
- "tests_test_v74_fast_navigation_test_short_ttls_are_configured": "test_short_ttls_are_configured()" | kind=code-symbol | source=tests/test_v74_fast_navigation.py:L80 | neighbors=[test_v74_fast_navigation.py]
- "tests_test_v75_orb_entry_vs_now_test_orb_current_view_normalizes_waiting_state": "test_orb_current_view_normalizes_waiting_state()" | kind=code-symbol | source=tests/test_v75_orb_entry_vs_now.py:L4 | neighbors=[test_v75_orb_entry_vs_now.py]
- "tests_test_v75_orb_entry_vs_now_test_orb_is_no_longer_skipped_from_current_audit": "test_orb_is_no_longer_skipped_from_current_audit()" | kind=code-symbol | source=tests/test_v75_orb_entry_vs_now.py:L24 | neighbors=[test_v75_orb_entry_vs_now.py]
- "tests_test_v75_orb_entry_vs_now_test_refresh_routes_open_orb_trade_to_orb_analyzer": "test_refresh_routes_open_orb_trade_to_orb_analyzer()" | kind=code-symbol | source=tests/test_v75_orb_entry_vs_now.py:L16 | neighbors=[test_v75_orb_entry_vs_now.py]
- "tests_test_v76_unified_multibot_orb_htf_fakemtf_analyze_symbol": ".analyze_symbol()" | kind=code-symbol | source=tests/test_v76_unified_multibot_orb_htf.py:L11 | neighbors=[FakeMTF]
- "tests_test_v76_unified_multibot_orb_htf_fakemtf_init": ".__init__()" | kind=code-symbol | source=tests/test_v76_unified_multibot_orb_htf.py:L8 | neighbors=[FakeMTF]
- "tests_test_v76_unified_multibot_orb_htf_test_orb_live_audit_includes_htf_context": "test_orb_live_audit_includes_htf_context()" | kind=code-symbol | source=tests/test_v76_unified_multibot_orb_htf.py:L85 | neighbors=[test_v76_unified_multibot_orb_htf.py]
- "tests_test_v76_unified_multibot_orb_htf_test_unified_runtime_has_single_dashboard_and_shared_provider": "test_unified_runtime_has_single_dashboard_and_shared_provider()" | kind=code-symbol | source=tests/test_v76_unified_multibot_orb_htf.py:L74 | neighbors=[test_v76_unified_multibot_orb_htf.py]
- "tests_test_v76_unified_multibot_orb_htf_test_unified_runtime_keeps_independent_profile_magics": "test_unified_runtime_keeps_independent_profile_magics()" | kind=code-symbol | source=tests/test_v76_unified_multibot_orb_htf.py:L65 | neighbors=[test_v76_unified_multibot_orb_htf.py]
- "tests_test_v76_unified_multibot_orb_htf_test_unified_runtime_remains_available_explicitly": "test_unified_runtime_remains_available_explicitly()" | kind=code-symbol | source=tests/test_v76_unified_multibot_orb_htf.py:L57 | neighbors=[test_v76_unified_multibot_orb_htf.py]
- "tests_test_v77_hybrid_multibot_fast_front_test_browser_polling_is_reduced": "test_browser_polling_is_reduced()" | kind=code-symbol | source=tests/test_v77_hybrid_multibot_fast_front.py:L21 | neighbors=[test_v77_hybrid_multibot_fast_front.py]
- "tests_test_v77_hybrid_multibot_fast_front_test_dashboard_has_short_full_snapshot_cache": "test_dashboard_has_short_full_snapshot_cache()" | kind=code-symbol | source=tests/test_v77_hybrid_multibot_fast_front.py:L15 | neighbors=[test_v77_hybrid_multibot_fast_front.py]
- "tests_test_v77_hybrid_multibot_fast_front_test_multi_bot_default_returns_to_multiprocess_coordinator": "test_multi_bot_default_returns_to_multiprocess_coordinator()" | kind=code-symbol | source=tests/test_v77_hybrid_multibot_fast_front.py:L3 | neighbors=[test_v77_hybrid_multibot_fast_front.py]
- "tests_test_v77_hybrid_multibot_fast_front_test_orb_htf_context_is_preserved_after_rollback": "test_orb_htf_context_is_preserved_after_rollback()" | kind=code-symbol | source=tests/test_v77_hybrid_multibot_fast_front.py:L29 | neighbors=[test_v77_hybrid_multibot_fast_front.py]
- "tests_test_v77_hybrid_multibot_fast_front_test_startup_warns_about_parallel_daemon_instances": "test_startup_warns_about_parallel_daemon_instances()" | kind=code-symbol | source=tests/test_v77_hybrid_multibot_fast_front.py:L36 | neighbors=[test_v77_hybrid_multibot_fast_front.py]
- "tests_test_v77_hybrid_multibot_fast_front_test_unified_multibot_is_explicit_experimental_mode_only": "test_unified_multibot_is_explicit_experimental_mode_only()" | kind=code-symbol | source=tests/test_v77_hybrid_multibot_fast_front.py:L9 | neighbors=[test_v77_hybrid_multibot_fast_front.py]
- "tests_test_v78_account_no_horizontal_scroll_test_account_audit_column_no_longer_forces_minimum_width": "test_account_audit_column_no_longer_forces_minimum_width()" | kind=code-symbol | source=tests/test_v78_account_no_horizontal_scroll.py:L10 | neighbors=[test_v78_account_no_horizontal_scroll.py]
- "tests_test_v78_account_no_horizontal_scroll_test_account_columns_fit_full_width": "test_account_columns_fit_full_width()" | kind=code-symbol | source=tests/test_v78_account_no_horizontal_scroll.py:L16 | neighbors=[test_v78_account_no_horizontal_scroll.py]
- "tests_test_v78_account_no_horizontal_scroll_test_account_table_uses_fixed_layout_and_vertical_scroll_only": "test_account_table_uses_fixed_layout_and_vertical_scroll_only()" | kind=code-symbol | source=tests/test_v78_account_no_horizontal_scroll.py:L3 | neighbors=[test_v78_account_no_horizontal_scroll.py]
- "tests_test_v79_universal_open_position_audit_repo_init": ".__init__()" | kind=code-symbol | source=tests/test_v79_universal_open_position_audit.py:L8 | neighbors=[Repo]
- "tests_test_v79_universal_open_position_audit_repo_upsert_trade_visual_audit": ".upsert_trade_visual_audit()" | kind=code-symbol | source=tests/test_v79_universal_open_position_audit.py:L10 | neighbors=[Repo]
- "tests_test_v79_universal_open_position_audit_test_dashboard_prefers_current_strategy_view_from_trade_market": "test_dashboard_prefers_current_strategy_view_from_trade_market()" | kind=code-symbol | source=tests/test_v79_universal_open_position_audit.py:L58 | neighbors=[test_v79_universal_open_position_audit.…]
- "tests_test_v79_universal_open_position_audit_test_monitor_persists_live_position_telemetry_each_pass": "test_monitor_persists_live_position_telemetry_each_pass()" | kind=code-symbol | source=tests/test_v79_universal_open_position_audit.py:L66 | neighbors=[test_v79_universal_open_position_audit.…]
- "tests_test_v80_trade_audit_detail_tab_test_account_opens_trade_audit_in_new_tab": "test_account_opens_trade_audit_in_new_tab()" | kind=code-symbol | source=tests/test_v80_trade_audit_detail_tab.py:L3 | neighbors=[test_v80_trade_audit_detail_tab.py]
- "tests_test_v80_trade_audit_detail_tab_test_detail_api_loads_all_snapshots_and_orders_chronologically": "test_detail_api_loads_all_snapshots_and_orders_chronologically()" | kind=code-symbol | source=tests/test_v80_trade_audit_detail_tab.py:L19 | neighbors=[test_v80_trade_audit_detail_tab.py]
- "tests_test_v80_trade_audit_detail_tab_test_detail_page_exposes_timeline_and_evolution_metrics": "test_detail_page_exposes_timeline_and_evolution_metrics()" | kind=code-symbol | source=tests/test_v80_trade_audit_detail_tab.py:L26 | neighbors=[test_v80_trade_audit_detail_tab.py]
- "tests_test_v80_trade_audit_detail_tab_test_trade_audit_has_dedicated_page_and_api": "test_trade_audit_has_dedicated_page_and_api()" | kind=code-symbol | source=tests/test_v80_trade_audit_detail_tab.py:L11 | neighbors=[test_v80_trade_audit_detail_tab.py]
- "tests_test_v81_trade_audit_excel_export_test_dashboard_exposes_excel_download_endpoint": "test_dashboard_exposes_excel_download_endpoint()" | kind=code-symbol | source=tests/test_v81_trade_audit_excel_export.py:L76 | neighbors=[test_v81_trade_audit_excel_export.py]
- "tests_test_v81_trade_audit_excel_export_test_web_page_has_excel_button": "test_web_page_has_excel_button()" | kind=code-symbol | source=tests/test_v81_trade_audit_excel_export.py:L69 | neighbors=[test_v81_trade_audit_excel_export.py]
- "tests_test_v82_synthetic_selection_recovery_test_empty_cycle_is_reported_as_degraded": "test_empty_cycle_is_reported_as_degraded()" | kind=code-symbol | source=tests/test_v82_synthetic_selection_recovery.py:L38 | neighbors=[test_v82_synthetic_selection_recovery.py]
- "tests_test_v82_synthetic_selection_recovery_test_empty_synthetic_profile_is_recovered_for_synthetic_coordinator": "test_empty_synthetic_profile_is_recovered_for_synthetic_coordinator()" | kind=code-symbol | source=tests/test_v82_synthetic_selection_recovery.py:L8 | neighbors=[test_v82_synthetic_selection_recovery.py]
- "tests_test_v82_synthetic_selection_recovery_test_forex_without_candles_reports_data_wait": "test_forex_without_candles_reports_data_wait()" | kind=code-symbol | source=tests/test_v82_synthetic_selection_recovery.py:L76 | neighbors=[test_v82_synthetic_selection_recovery.py]
- "tests_test_v82_synthetic_selection_recovery_test_forex_without_new_m5_bar_is_waiting_not_degraded": "test_forex_without_new_m5_bar_is_waiting_not_degraded()" | kind=code-symbol | source=tests/test_v82_synthetic_selection_recovery.py:L54 | neighbors=[test_v82_synthetic_selection_recovery.py]
- "tests_test_v82_synthetic_selection_recovery_test_nonempty_synthetic_profile_is_preserved": "test_nonempty_synthetic_profile_is_preserved()" | kind=code-symbol | source=tests/test_v82_synthetic_selection_recovery.py:L24 | neighbors=[test_v82_synthetic_selection_recovery.py]
- "tests_test_v84_entry_quality_and_audit_integrity_test_orb_non_correlated_markets_do_not_share_a_global_one_percent_cap": "test_orb_non_correlated_markets_do_not_share_a_global_one_percent_cap()" | kind=code-symbol | source=tests/test_v84_entry_quality_and_audit_integrity.py:L21 | neighbors=[test_v84_entry_quality_and_audit_integr…]
- "tests_test_v84_entry_quality_and_audit_integrity_test_orb_unknown_htf_context_is_blocked": "test_orb_unknown_htf_context_is_blocked()" | kind=code-symbol | source=tests/test_v84_entry_quality_and_audit_integrity.py:L7 | neighbors=[test_v84_entry_quality_and_audit_integr…]
- "tests_test_v84_entry_quality_and_audit_integrity_test_reused_trade_id_resets_frozen_identity": "test_reused_trade_id_resets_frozen_identity()" | kind=code-symbol | source=tests/test_v84_entry_quality_and_audit_integrity.py:L36 | neighbors=[test_v84_entry_quality_and_audit_integr…]
- "tests_test_v85_orb_correlation_synthetic_parity_test_synthetics_inherit_m5_event_scheduler_without_forex_hours": "test_synthetics_inherit_m5_event_scheduler_without_forex_hours()" | kind=code-symbol | source=tests/test_v85_orb_correlation_synthetic_parity.py:L63 | neighbors=[test_v85_orb_correlation_synthetic_pari…]

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-053.json

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
