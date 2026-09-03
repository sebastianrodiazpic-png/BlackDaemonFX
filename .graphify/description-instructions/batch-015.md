# Node Description Batch 16 of 56

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

- "tests_test_signal_freshness_analyzer": "_analyzer()" | kind=code-symbol | source=tests/test_signal_freshness.py:L7 | neighbors=[test_signal_freshness.py, test_m5_signal_age_becomes_stale_after_…, test_m5_signal_age_exact_index_is_fresh…, test_m5_signal_age_minutes_can_block_ev…, test_signal_age_uses_temporal_fallback_…]
- "tests_test_trade_lifecycle_full_integration": "test_trade_lifecycle_full_integration.py" | kind=code-symbol | source=tests/test_trade_lifecycle_full_integration.py:L1 | neighbors=[ControlledDataProvider, ControlledMultiTimeframeAnalyzer, create_config(), test_trade_lifecycle_full_integration(), trade_lifecycle_manager.py]
- "tests_test_trade_lifecycle_full_integration_controlleddataprovider_get_candles": ".get_candles()" | kind=code-symbol | source=tests/test_trade_lifecycle_full_integration.py:L43 | neighbors=[ControlledDataProvider, ._h1(), ._m15(), ._m5(), test_trade_lifecycle_full_integration()]
- "tests_test_trade_lifecycle_full_integration_test_trade_lifecycle_full_integration": "test_trade_lifecycle_full_integration()" | kind=code-symbol | source=tests/test_trade_lifecycle_full_integration.py:L415 | neighbors=[test_trade_lifecycle_full_integration.py, ControlledDataProvider, .get_candles(), ControlledMultiTimeframeAnalyzer, create_config()]
- "tests_test_trade_lifecycle_manager_create_win_result": "create_win_result()" | kind=code-symbol | source=tests/test_trade_lifecycle_manager.py:L160 | neighbors=[test_trade_lifecycle_manager.py, test_cannot_execute_final_lifecycle_twi…, test_lifecycle_win(), test_manager_history(), test_process_signal()]
- "tests_test_trade_lifecycle_manager_test_cannot_execute_final_lifecycle_twice": "test_cannot_execute_final_lifecycle_twice()" | kind=code-symbol | source=tests/test_trade_lifecycle_manager.py:L761 | neighbors=[test_trade_lifecycle_manager.py, create_candles(), create_controlled_simulator(), create_signal(), create_win_result()]
- "tests_test_trade_lifecycle_manager_test_lifecycle_ambiguous": "test_lifecycle_ambiguous()" | kind=code-symbol | source=tests/test_trade_lifecycle_manager.py:L489 | neighbors=[test_trade_lifecycle_manager.py, create_ambiguous_result(), create_candles(), create_controlled_simulator(), create_signal()]
- "tests_test_trade_lifecycle_manager_test_lifecycle_expired": "test_lifecycle_expired()" | kind=code-symbol | source=tests/test_trade_lifecycle_manager.py:L560 | neighbors=[test_trade_lifecycle_manager.py, create_candles(), create_controlled_simulator(), create_expired_result(), create_signal()]
- "tests_test_trade_lifecycle_manager_test_lifecycle_loss": "test_lifecycle_loss()" | kind=code-symbol | source=tests/test_trade_lifecycle_manager.py:L416 | neighbors=[test_trade_lifecycle_manager.py, create_candles(), create_controlled_simulator(), create_loss_result(), create_signal()]
- "tests_test_trade_lifecycle_manager_test_lifecycle_win": "test_lifecycle_win()" | kind=code-symbol | source=tests/test_trade_lifecycle_manager.py:L339 | neighbors=[test_trade_lifecycle_manager.py, create_candles(), create_controlled_simulator(), create_signal(), create_win_result()]
- "tests_test_trade_lifecycle_manager_test_manager_history": "test_manager_history()" | kind=code-symbol | source=tests/test_trade_lifecycle_manager.py:L688 | neighbors=[test_trade_lifecycle_manager.py, create_candles(), create_controlled_simulator(), create_signal(), create_win_result()]
- "tests_test_trade_lifecycle_manager_test_process_signal": "test_process_signal()" | kind=code-symbol | source=tests/test_trade_lifecycle_manager.py:L633 | neighbors=[test_trade_lifecycle_manager.py, create_candles(), create_controlled_simulator(), create_signal(), create_win_result()]
- "tests_test_trade_reporting_service": "test_trade_reporting_service.py" | kind=code-symbol | source=tests/test_trade_reporting_service.py:L1 | neighbors=[repository.py, trade_reporting_service.py, create_signal(), test_paper_lifecycle_is_persisted_and_e…, trade_lifecycle_manager.py]
- "tests_test_v100_entry_quarantine_winrate_test_minimum_volume_split_error_reaches_safe_single_fallback": "test_minimum_volume_split_error_reaches_safe_single_fallback()" | kind=code-symbol | source=tests/test_v100_entry_quarantine_winrate.py:L154 | neighbors=[test_v100_entry_quarantine_winrate.py, _Analyzer, _MinimumVolumeExecutor, _Provider, _Repo]
- "tests_test_v41_critical_gates": "test_v41_critical_gates.py" | kind=code-symbol | source=tests/test_v41_critical_gates.py:L1 | neighbors=[_base(), _setup(), test_bos_cannot_be_saved_by_adaptive_sc…, test_choch_cannot_be_saved_by_adaptive_…, test_visible_trade_score_is_capped_at_1…]
- "tests_test_v51_multi_bot_dashboard": "test_v51_multi_bot_dashboard.py" | kind=code-symbol | source=tests/test_v51_multi_bot_dashboard.py:L1 | neighbors=[main.py, test_coordinator_source_contains_single…, test_dashboard_catalog_helper_exists(), test_multi_bot_daemon_accepts_dashboard…, test_split_profiles_remain_same()]
- "tests_test_v52_worker_family_dashboard": "test_v52_worker_family_dashboard.py" | kind=code-symbol | source=tests/test_v52_worker_family_dashboard.py:L1 | neighbors=[realtime_dashboard.py, repository.py, test_dashboard_html_contains_family_wor…, test_dashboard_snapshot_exposes_workers…, test_worker_runtime_state_roundtrip()]
- "tests_test_v55_persistent_entry_audit": "test_v55_persistent_entry_audit.py" | kind=code-symbol | source=tests/test_v55_persistent_entry_audit.py:L1 | neighbors=[repository.py, test_dashboard_source_exposes_entry_and…, test_database_model_has_unique_trade_vi…, test_trade_entry_visual_audit_is_immuta…, test_trade_visual_audit_survives_withou…]
- "tests_test_v61_orb_m5_retest_risk": "test_v61_orb_m5_retest_risk.py" | kind=code-symbol | source=tests/test_v61_orb_m5_retest_risk.py:L1 | neighbors=[test_execute_signal_uses_orb_specific_r…, test_live_orb_risk_is_fixed_to_one_perc…, test_orb_signal_source_requires_retest(), test_orb_v61_defaults_are_m5_midpoint_a…, test_runner_can_extend_2r_to_3r_and_4r_…]
- "tests_test_v67_live_entry_vs_now_analyzer": "Analyzer" | kind=code-symbol | source=tests/test_v67_live_entry_vs_now.py:L82 | neighbors=[test_v67_live_entry_vs_now.py, LiveTradingConfig, LiveTradingEngine, .analyze_symbol(), test_open_smc_position_is_reanalyzed_an…]
- "tests_test_v68_persistent_entry_vs_now_dataset_repo_with_trade": "_repo_with_trade()" | kind=code-symbol | source=tests/test_v68_persistent_entry_vs_now_dataset.py:L9 | neighbors=[test_v68_persistent_entry_vs_now_datase…, test_account_exposes_entry_vs_now_histo…, test_snapshot_dataframe_contains_resear…, test_snapshot_history_is_append_only_an…, test_xlsx_exports_entry_vs_now_sheet()]
- "tests_test_v69_forex_event_scheduler_event_engine": "_event_engine()" | kind=code-symbol | source=tests/test_v69_forex_event_scheduler.py:L46 | neighbors=[test_v69_forex_event_scheduler.py, CandleProvider, test_forex_event_scheduler_only_release…, test_forex_scheduler_retries_same_bar_a…, test_synthetic_is_event_filtered_since_…]
- "tests_test_v70_recent_analysis_all_workers": "test_v70_recent_analysis_all_workers.py" | kind=code-symbol | source=tests/test_v70_recent_analysis_all_workers.py:L1 | neighbors=[models.py, repository.py, test_dashboard_hides_superseded_but_kee…, test_recent_analysis_uses_sqlalchemy_as…, test_recent_symbol_process_results_keep…]
- "tests_test_v73_forex_progressive_runner_trade": "_trade()" | kind=code-symbol | source=tests/test_v73_forex_progressive_runner.py:L72 | neighbors=[test_v73_forex_progressive_runner.py, test_forex_at_tp2_protects_tp1_then_ext…, test_forex_at_tp2_without_continuation_…, test_forex_at_tp3_if_continuation_prote…, test_forex_at_tp3_without_continuation_…]
- "tests_test_v76_unified_multibot_orb_htf_engine": "_engine()" | kind=code-symbol | source=tests/test_v76_unified_multibot_orb_htf.py:L21 | neighbors=[test_v76_unified_multibot_orb_htf.py, FakeMTF, test_neutral_h1_does_not_block_orb(), test_orb_buy_is_blocked_against_bearish…, test_orb_sell_is_aligned_with_bearish_c…]
- "tests_test_v79_universal_open_position_audit_engine": "_engine()" | kind=code-symbol | source=tests/test_v79_universal_open_position_audit.py:L14 | neighbors=[test_v79_universal_open_position_audit.…, Repo, test_live_market_snapshot_persists_for_…, test_live_market_snapshot_persists_for_…, test_live_market_snapshot_persists_for_…]
- "tests_test_v81_trade_audit_excel_export": "test_v81_trade_audit_excel_export.py" | kind=code-symbol | source=tests/test_v81_trade_audit_excel_export.py:L1 | neighbors=[trade_audit_excel_exporter.py, _payload(), test_dashboard_exposes_excel_download_e…, test_exporter_creates_multisheet_xlsx(), test_web_page_has_excel_button()]
- "tests_test_v85_orb_correlation_synthetic_parity_engine_with_open_trade": "_engine_with_open_trade()" | kind=code-symbol | source=tests/test_v85_orb_correlation_synthetic_parity.py:L6 | neighbors=[test_v85_orb_correlation_synthetic_pari…, test_gold_and_wall_street_are_not_part_…, test_persisted_protective_stop_also_pro…, test_sp500_is_allowed_after_nasdaq_brea…, test_sp500_is_blocked_while_nasdaq_risk…]
- "tests_test_v85_orb_correlation_synthetic_parity_orb_trade": "_orb_trade()" | kind=code-symbol | source=tests/test_v85_orb_correlation_synthetic_parity.py:L13 | neighbors=[test_v85_orb_correlation_synthetic_pari…, test_gold_and_wall_street_are_not_part_…, test_persisted_protective_stop_also_pro…, test_sp500_is_allowed_after_nasdaq_brea…, test_sp500_is_blocked_while_nasdaq_risk…]
- "tests_test_v87_gold_asia_new_york_session_engine": "_engine()" | kind=code-symbol | source=tests/test_v87_gold_asia_new_york_session.py:L8 | neighbors=[test_v87_gold_asia_new_york_session.py, test_gold_entry_gate_does_not_affect_fo…, test_gold_window_opens_at_tokyo_0900_an…, test_gold_window_respects_new_york_wint…, test_orb_detects_open_gold_smc_exposure…]
- "tests_test_v95_analysis_invalidation_exit_old_trade": "old_trade()" | kind=code-symbol | source=tests/test_v95_analysis_invalidation_exit.py:L27 | neighbors=[test_v95_analysis_invalidation_exit.py, test_recovery_protection_closes_after_p…, test_same_evaluation_does_not_inflate_c…, test_two_distinct_invalid_analyses_clos…, test_valid_current_analysis_resets_stre…]
- "trade_lifecycle_manager_tradelifecyclemanager_record_final_lifecycle": "._record_final_lifecycle()" | kind=code-symbol | source=trade_lifecycle_manager.py:L601 | neighbors=[TradeLifecycleManager, .close_execution(), .execute(), .monitor_execution(), .is_final()]
- "app_main_assert_full_multibot_architecture": "_assert_full_multibot_architecture()" | kind=code-symbol | source=app/main.py:L976 | neighbors=[main.py, Garantiza un solo coordinador con todos…, run_multi_bot_daemon(), run_unified_multibot_daemon()]
- "app_main_assert_v53_runtime_compatibility": "_assert_v53_runtime_compatibility()" | kind=code-symbol | source=app/main.py:L1153 | neighbors=[main.py, Falla temprano si la carpeta contiene m…, run_multi_bot_daemon(), run_unified_multibot_daemon()]
- "app_main_find_other_multibot_coordinators_windows": "_find_other_multibot_coordinators_windows()" | kind=code-symbol | source=app/main.py:L1734 | neighbors=[main.py, _acquire_multibot_instance_guard(), _filter_external_multibot_coordinators(), Devuelve coordinadores externos, excluy…]
- "app_main_resolve_live_symbols": "_resolve_live_symbols()" | kind=code-symbol | source=app/main.py:L759 | neighbors=[main.py, main(), Descubre símbolos dinámicamente para mo…, _resolve_symbols()]
- "app_main_resolve_live_symbols_for_profile": "_resolve_live_symbols_for_profile()" | kind=code-symbol | source=app/main.py:L1011 | neighbors=[main.py, main(), Resuelve únicamente el universo pertene…, _stable_symbol_shard()]
- "app_main_run_collector": "run_collector()" | kind=code-symbol | source=app/main.py:L140 | neighbors=[main.py, main(), collect_once(), _resolve_symbols()]
- "app_main_run_startup_database_maintenance": "_run_startup_database_maintenance()" | kind=code-symbol | source=app/main.py:L1241 | neighbors=[main.py, Aplica retención antes de crear dashboa…, run_multi_bot_daemon(), run_unified_multibot_daemon()]
- "app_main_stable_symbol_shard": "_stable_symbol_shard()" | kind=code-symbol | source=app/main.py:L1003 | neighbors=[main.py, Distribuye símbolos de forma determinis…, _resolve_live_symbols_for_profile(), _resolve_symbols_for_profile_shared()]

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-015.json

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
