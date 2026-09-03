# Node Description Batch 27 of 56

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

- "tests_test_risk_manager_test_stop_loss_buy_invalid": "test_stop_loss_buy_invalid()" | kind=code-symbol | source=tests/test_risk_manager.py:L98 | neighbors=[test_risk_manager.py, print_result(), print_section()]
- "tests_test_risk_manager_test_stop_loss_buy_valid": "test_stop_loss_buy_valid()" | kind=code-symbol | source=tests/test_risk_manager.py:L74 | neighbors=[test_risk_manager.py, print_result(), print_section()]
- "tests_test_risk_manager_test_stop_loss_sell_valid": "test_stop_loss_sell_valid()" | kind=code-symbol | source=tests/test_risk_manager.py:L122 | neighbors=[test_risk_manager.py, print_result(), print_section()]
- "tests_test_risk_manager_test_take_profit_buy_valid": "test_take_profit_buy_valid()" | kind=code-symbol | source=tests/test_risk_manager.py:L146 | neighbors=[test_risk_manager.py, print_result(), print_section()]
- "tests_test_risk_manager_test_take_profit_sell_valid": "test_take_profit_sell_valid()" | kind=code-symbol | source=tests/test_risk_manager.py:L170 | neighbors=[test_risk_manager.py, print_result(), print_section()]
- "tests_test_risk_manager_test_validate_risk_reward": "test_validate_risk_reward()" | kind=code-symbol | source=tests/test_risk_manager.py:L228 | neighbors=[test_risk_manager.py, print_result(), print_section()]
- "tests_test_risk_manager_test_validate_risk_reward_invalid": "test_validate_risk_reward_invalid()" | kind=code-symbol | source=tests/test_risk_manager.py:L257 | neighbors=[test_risk_manager.py, print_result(), print_section()]
- "tests_test_runner_extension_manager_uptrend": "_uptrend()" | kind=code-symbol | source=tests/test_runner_extension_manager.py:L7 | neighbors=[test_runner_extension_manager.py, test_clean_uptrend_can_continue_runner(), test_insufficient_market_data_blocks_ex…]
- "tests_test_trade_executor": "test_trade_executor.py" | kind=code-symbol | source=tests/test_trade_executor.py:L1 | neighbors=[test_execution_request_from_signal(), test_execution_request_invalid_signal(), test_trade_executor_is_abstract()]
- "tests_test_trade_lifecycle_integration_controlledlifecycledataprovider_get_candles": ".get_candles()" | kind=code-symbol | source=tests/test_trade_lifecycle_integration.py:L55 | neighbors=[ControlledLifecycleDataProvider, ._build_m5_candles(), run_lifecycle()]
- "tests_test_trade_lifecycle_integration_test_trade_lifecycle_integration": "test_trade_lifecycle_integration()" | kind=code-symbol | source=tests/test_trade_lifecycle_integration.py:L1055 | neighbors=[test_trade_lifecycle_integration.py, print_case_result(), run_lifecycle()]
- "tests_test_trade_report_exporter": "test_trade_report_exporter.py" | kind=code-symbol | source=tests/test_trade_report_exporter.py:L1 | neighbors=[repository.py, trade_report_exporter.py, test_export_trade_report()]
- "tests_test_v100_entry_quarantine_winrate_m5_data": "_m5_data()" | kind=code-symbol | source=tests/test_v100_entry_quarantine_winrate.py:L14 | neighbors=[test_v100_entry_quarantine_winrate.py, test_optional_harmonic_is_bonus_not_con…, test_similar_opposing_chart_patterns_pe…]
- "tests_test_v100_entry_quarantine_winrate_setup": "_setup()" | kind=code-symbol | source=tests/test_v100_entry_quarantine_winrate.py:L26 | neighbors=[test_v100_entry_quarantine_winrate.py, test_optional_harmonic_is_bonus_not_con…, test_similar_opposing_chart_patterns_pe…]
- "tests_test_v100_entry_quarantine_winrate_test_optional_harmonic_is_bonus_not_confirmation_denominator": "test_optional_harmonic_is_bonus_not_confirmation_denominator()" | kind=code-symbol | source=tests/test_v100_entry_quarantine_winrate.py:L38 | neighbors=[test_v100_entry_quarantine_winrate.py, _m5_data(), _setup()]
- "tests_test_v100_entry_quarantine_winrate_test_similar_opposing_chart_patterns_penalize_but_do_not_block": "test_similar_opposing_chart_patterns_penalize_but_do_not_block()" | kind=code-symbol | source=tests/test_v100_entry_quarantine_winrate.py:L56 | neighbors=[test_v100_entry_quarantine_winrate.py, _m5_data(), _setup()]
- "tests_test_v41_critical_gates_test_bos_cannot_be_saved_by_adaptive_score_without_rejection": "test_bos_cannot_be_saved_by_adaptive_score_without_rejection()" | kind=code-symbol | source=tests/test_v41_critical_gates.py:L32 | neighbors=[test_v41_critical_gates.py, _base(), _setup()]
- "tests_test_v41_critical_gates_test_choch_cannot_be_saved_by_adaptive_score_without_microstructure": "test_choch_cannot_be_saved_by_adaptive_score_without_microstructure()" | kind=code-symbol | source=tests/test_v41_critical_gates.py:L54 | neighbors=[test_v41_critical_gates.py, _base(), _setup()]
- "tests_test_v41_critical_gates_test_visible_trade_score_is_capped_at_100_but_raw_score_is_preserved": "test_visible_trade_score_is_capped_at_100_but_raw_score_is_preserved()" | kind=code-symbol | source=tests/test_v41_critical_gates.py:L82 | neighbors=[test_v41_critical_gates.py, _base(), _setup()]
- "tests_test_v45_forex_instrument_catalog_test_tradeable_forex_is_discovered_from_mt5_metadata": "test_tradeable_forex_is_discovered_from_mt5_metadata()" | kind=code-symbol | source=tests/test_v45_forex_instrument_catalog.py:L44 | neighbors=[test_v45_forex_instrument_catalog.py, Connected, _info()]
- "tests_test_v46_total_persistence_signal": "signal()" | kind=code-symbol | source=tests/test_v46_total_persistence.py:L10 | neighbors=[test_v46_total_persistence.py, test_filled_lifecycle_persists_trade_jo…, test_xlsx_contains_permanent_trades_and…]
- "tests_test_v47_multi_bot_architecture_engine": "_engine()" | kind=code-symbol | source=tests/test_v47_multi_bot_architecture.py:L11 | neighbors=[test_v47_multi_bot_architecture.py, test_legacy_trade_is_only_owned_by_hist…, test_trade_ownership_by_magic()]
- "tests_test_v50_compact_audit_log": "test_v50_compact_audit_log.py" | kind=code-symbol | source=tests/test_v50_compact_audit_log.py:L1 | neighbors=[trade_report_exporter.py, test_compact_audit_log_extracts_key_fie…, test_export_does_not_emit_excel_cell_to…]
- "tests_test_v57_forex_persistence_hardening_catalog": "catalog()" | kind=code-symbol | source=tests/test_v57_forex_persistence_hardening.py:L9 | neighbors=[test_v57_forex_persistence_hardening.py, test_empty_forex_selection_is_persisten…, test_forex_survives_dashboard_restart_a…]
- "tests_test_v63_account_db_continuity_make_legacy_db": "_make_legacy_db()" | kind=code-symbol | source=tests/test_v63_account_db_continuity.py:L9 | neighbors=[test_v63_account_db_continuity.py, test_nonempty_stable_db_is_never_overwr…, test_stable_db_recovers_nonempty_siblin…]
- "tests_test_v65_smc_two_leg_tp3_protection_test_smc_at_2r_locks_1r_then_extends_only_to_tp3": "test_smc_at_2r_locks_1r_then_extends_only_to_tp3()" | kind=code-symbol | source=tests/test_v65_smc_two_leg_tp3_protection.py:L97 | neighbors=[test_v65_smc_two_leg_tp3_protection.py, _engine(), _trade()]
- "tests_test_v65_smc_two_leg_tp3_protection_test_smc_at_2r_without_continuation_closes_runner_after_profit_lock": "test_smc_at_2r_without_continuation_closes_runner_after_profit_lock()" | kind=code-symbol | source=tests/test_v65_smc_two_leg_tp3_protection.py:L119 | neighbors=[test_v65_smc_two_leg_tp3_protection.py, _engine(), _trade()]
- "tests_test_v65_smc_two_leg_tp3_protection_test_smc_at_3r_can_extend_to_tp4_with_2r_locked": "test_smc_at_3r_can_extend_to_tp4_with_2r_locked()" | kind=code-symbol | source=tests/test_v65_smc_two_leg_tp3_protection.py:L158 | neighbors=[test_v65_smc_two_leg_tp3_protection.py, _engine(), _trade()]
- "tests_test_v65_smc_two_leg_tp3_protection_test_smc_at_3r_without_continuation_closes_after_2r_lock": "test_smc_at_3r_without_continuation_closes_after_2r_lock()" | kind=code-symbol | source=tests/test_v65_smc_two_leg_tp3_protection.py:L183 | neighbors=[test_v65_smc_two_leg_tp3_protection.py, _engine(), _trade()]
- "tests_test_v65_smc_two_leg_tp3_protection_test_smc_between_tp2_and_tp3_advances_profit_lock_to_2r": "test_smc_between_tp2_and_tp3_advances_profit_lock_to_2r()" | kind=code-symbol | source=tests/test_v65_smc_two_leg_tp3_protection.py:L138 | neighbors=[test_v65_smc_two_leg_tp3_protection.py, _engine(), _trade()]
- "tests_test_v66_smc_tp4_be_plus2_broker_get_position": ".get_position()" | kind=code-symbol | source=tests/test_v66_smc_tp4_be_plus2.py:L50 | neighbors=[Broker, test_smc_3_5r_guard_locks_3r_while_targ…, test_smc_at_3r_evaluates_before_seeking…]
- "tests_test_v66_smc_tp4_be_plus2_test_smc_3_5r_guard_locks_3r_while_targeting_4r": "test_smc_3_5r_guard_locks_3r_while_targeting_4r()" | kind=code-symbol | source=tests/test_v66_smc_tp4_be_plus2.py:L116 | neighbors=[test_v66_smc_tp4_be_plus2.py, .get_position(), _engine()]
- "tests_test_v66_smc_tp4_be_plus2_test_smc_at_3r_evaluates_before_seeking_tp4": "test_smc_at_3r_evaluates_before_seeking_tp4()" | kind=code-symbol | source=tests/test_v66_smc_tp4_be_plus2.py:L139 | neighbors=[test_v66_smc_tp4_be_plus2.py, .get_position(), _engine()]
- "tests_test_v67_live_entry_vs_now_test_open_smc_position_is_reanalyzed_and_persisted_without_touching_entry": "test_open_smc_position_is_reanalyzed_and_persisted_without_touching_entry()" | kind=code-symbol | source=tests/test_v67_live_entry_vs_now.py:L96 | neighbors=[test_v67_live_entry_vs_now.py, Analyzer, Repo]
- "tests_test_v69_forex_event_scheduler_test_forex_currency_exposure_blocks_third_percent_on_same_currency": "test_forex_currency_exposure_blocks_third_percent_on_same_currency()" | kind=code-symbol | source=tests/test_v69_forex_event_scheduler.py:L120 | neighbors=[test_v69_forex_event_scheduler.py, ExposureRepo, _trade()]
- "tests_test_v69_forex_event_scheduler_test_forex_exposure_does_not_double_count_split_legs": "test_forex_exposure_does_not_double_count_split_legs()" | kind=code-symbol | source=tests/test_v69_forex_event_scheduler.py:L105 | neighbors=[test_v69_forex_event_scheduler.py, ExposureRepo, _trade()]
- "tests_test_v69_forex_event_scheduler_test_forex_total_risk_limit_is_global_across_pairs": "test_forex_total_risk_limit_is_global_across_pairs()" | kind=code-symbol | source=tests/test_v69_forex_event_scheduler.py:L136 | neighbors=[test_v69_forex_event_scheduler.py, ExposureRepo, _trade()]
- "tests_test_v71_balanced_recent_analysis_event": "_event()" | kind=code-symbol | source=tests/test_v71_balanced_recent_analysis.py:L8 | neighbors=[test_v71_balanced_recent_analysis.py, test_orb_flood_does_not_hide_forex_or_s…, test_recent_results_are_deduped_by_prof…]
- "tests_test_v73_forex_progressive_runner_test_forex_at_tp2_protects_tp1_then_extends_logically_to_tp3": "test_forex_at_tp2_protects_tp1_then_extends_logically_to_tp3()" | kind=code-symbol | source=tests/test_v73_forex_progressive_runner.py:L99 | neighbors=[test_v73_forex_progressive_runner.py, _engine(), _trade()]
- "tests_test_v73_forex_progressive_runner_test_forex_at_tp2_without_continuation_closes_runner_after_tp1_lock": "test_forex_at_tp2_without_continuation_closes_runner_after_tp1_lock()" | kind=code-symbol | source=tests/test_v73_forex_progressive_runner.py:L122 | neighbors=[test_v73_forex_progressive_runner.py, _engine(), _trade()]

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-026.json

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
