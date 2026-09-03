# Node Description Batch 34 of 56

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

- "tests_test_backtest_print_rr_statistics": "print_rr_statistics()" | kind=code-symbol | source=tests/test_backtest.py:L182 | neighbors=[test_backtest.py, run_backtest()]
- "tests_test_backtest_print_summary": "print_summary()" | kind=code-symbol | source=tests/test_backtest.py:L52 | neighbors=[test_backtest.py, run_backtest()]
- "tests_test_backtest_storage": "test_backtest_storage.py" | kind=code-symbol | source=tests/test_backtest_storage.py:L1 | neighbors=[backtest_storage.py, main()]
- "tests_test_backtest_validate_files": "validate_files()" | kind=code-symbol | source=tests/test_backtest.py:L332 | neighbors=[test_backtest.py, run_backtest()]
- "tests_test_chile_timezone_reporting": "test_chile_timezone_reporting.py" | kind=code-symbol | source=tests/test_chile_timezone_reporting.py:L1 | neighbors=[trade_report_exporter.py, test_chile_timezone_conversion_winter_a…]
- "tests_test_daemon_explainable_report_test_report_enrichment_documents_entry_reason_and_outcome": "test_report_enrichment_documents_entry_reason_and_outcome()" | kind=code-symbol | source=tests/test_daemon_explainable_report.py:L11 | neighbors=[test_daemon_explainable_report.py, DummyRepository]
- "tests_test_deriv_symbols_print_symbols": "print_symbols()" | kind=code-symbol | source=tests/test_deriv_symbols.py:L6 | neighbors=[test_deriv_symbols.py, main()]
- "tests_test_deriv_symbols_rationale_22": "Busca instrumentos disponibles en MetaTrader 5\r     que contengan el texto indic" | kind=entity | source=tests/test_deriv_symbols.py:L22 | neighbors=[MT5Connector, search_symbols()]
- "tests_test_divergence_confirmation_frame": "_frame()" | kind=code-symbol | source=tests/test_divergence_confirmation.py:L6 | neighbors=[test_divergence_confirmation.py, test_bullish_regular_divergence_detecte…]
- "tests_test_divergence_confirmation_test_bullish_regular_divergence_detected_between_two_swing_lows": "test_bullish_regular_divergence_detected_between_two_swing_lows()" | kind=code-symbol | source=tests/test_divergence_confirmation.py:L19 | neighbors=[test_divergence_confirmation.py, _frame()]
- "tests_test_execution_preflight_service_test_preflight_accepts_dict_symbol_info": "test_preflight_accepts_dict_symbol_info()" | kind=code-symbol | source=tests/test_execution_preflight_service.py:L60 | neighbors=[test_execution_preflight_service.py, FakeRepository]
- "tests_test_forex_rollover_guard_test_asian_and_london_hours_are_enabled_after_tokyo_open": "test_asian_and_london_hours_are_enabled_after_tokyo_open()" | kind=code-symbol | source=tests/test_forex_rollover_guard.py:L36 | neighbors=[test_forex_rollover_guard.py, _engine()]
- "tests_test_forex_rollover_guard_test_cycle_restarts_exactly_at_tokyo_0900_summer": "test_cycle_restarts_exactly_at_tokyo_0900_summer()" | kind=code-symbol | source=tests/test_forex_rollover_guard.py:L40 | neighbors=[test_forex_rollover_guard.py, _engine()]
- "tests_test_forex_rollover_guard_test_cycle_restarts_exactly_at_tokyo_0900_winter": "test_cycle_restarts_exactly_at_tokyo_0900_winter()" | kind=code-symbol | source=tests/test_forex_rollover_guard.py:L46 | neighbors=[test_forex_rollover_guard.py, _engine()]
- "tests_test_forex_rollover_guard_test_dst_new_york_force_flat_still_works_in_winter": "test_dst_new_york_force_flat_still_works_in_winter()" | kind=code-symbol | source=tests/test_forex_rollover_guard.py:L52 | neighbors=[test_forex_rollover_guard.py, _engine()]
- "tests_test_forex_rollover_guard_test_force_flat_from_1645_new_york": "test_force_flat_from_1645_new_york()" | kind=code-symbol | source=tests/test_forex_rollover_guard.py:L31 | neighbors=[test_forex_rollover_guard.py, _engine()]
- "tests_test_forex_rollover_guard_test_forex_classifier_does_not_touch_synthetics_or_gold": "test_forex_classifier_does_not_touch_synthetics_or_gold()" | kind=code-symbol | source=tests/test_forex_rollover_guard.py:L19 | neighbors=[test_forex_rollover_guard.py, _engine()]
- "tests_test_forex_rollover_guard_test_friday_cutoff_stays_blocked_until_monday_tokyo": "test_friday_cutoff_stays_blocked_until_monday_tokyo()" | kind=code-symbol | source=tests/test_forex_rollover_guard.py:L63 | neighbors=[test_forex_rollover_guard.py, _engine()]
- "tests_test_forex_rollover_guard_test_monday_before_tokyo_is_blocked": "test_monday_before_tokyo_is_blocked()" | kind=code-symbol | source=tests/test_forex_rollover_guard.py:L58 | neighbors=[test_forex_rollover_guard.py, _engine()]
- "tests_test_forex_rollover_guard_test_new_entries_blocked_from_1630_new_york": "test_new_entries_blocked_from_1630_new_york()" | kind=code-symbol | source=tests/test_forex_rollover_guard.py:L26 | neighbors=[test_forex_rollover_guard.py, _engine()]
- "tests_test_full_backtest_pipeline": "test_full_backtest_pipeline.py" | kind=code-symbol | source=tests/test_full_backtest_pipeline.py:L1 | neighbors=[backtest_pipeline.py, main()]
- "tests_test_h1_extreme_doji_confirmation_test_bearish_h1_doji_at_upper_extreme_is_optional_confirmation": "test_bearish_h1_doji_at_upper_extreme_is_optional_confirmation()" | kind=code-symbol | source=tests/test_h1_extreme_doji_confirmation.py:L40 | neighbors=[test_h1_extreme_doji_confirmation.py, _base_frame()]
- "tests_test_h1_extreme_doji_confirmation_test_bullish_h1_doji_at_lower_extreme_is_optional_confirmation": "test_bullish_h1_doji_at_lower_extreme_is_optional_confirmation()" | kind=code-symbol | source=tests/test_h1_extreme_doji_confirmation.py:L21 | neighbors=[test_h1_extreme_doji_confirmation.py, _base_frame()]
- "tests_test_h1_extreme_doji_confirmation_test_disabled_doji_never_blocks_or_confirms": "test_disabled_doji_never_blocks_or_confirms()" | kind=code-symbol | source=tests/test_h1_extreme_doji_confirmation.py:L71 | neighbors=[test_h1_extreme_doji_confirmation.py, _base_frame()]
- "tests_test_h1_extreme_doji_confirmation_test_doji_in_middle_of_range_does_not_confirm": "test_doji_in_middle_of_range_does_not_confirm()" | kind=code-symbol | source=tests/test_h1_extreme_doji_confirmation.py:L57 | neighbors=[test_h1_extreme_doji_confirmation.py, _base_frame()]
- "tests_test_harmonic_patterns_test_harmonic_detector_returns_diagnostic_when_no_pattern": "test_harmonic_detector_returns_diagnostic_when_no_pattern()" | kind=code-symbol | source=tests/test_harmonic_patterns.py:L19 | neighbors=[test_harmonic_patterns.py, make_swings()]
- "tests_test_harmonic_patterns_test_harmonic_disabled_is_explicit": "test_harmonic_disabled_is_explicit()" | kind=code-symbol | source=tests/test_harmonic_patterns.py:L26 | neighbors=[test_harmonic_patterns.py, make_swings()]
- "tests_test_jump_strict_quality_gate_test_jump_passes_only_with_reinforced_confirmation": "test_jump_passes_only_with_reinforced_confirmation()" | kind=code-symbol | source=tests/test_jump_strict_quality_gate.py:L31 | neighbors=[test_jump_strict_quality_gate.py, _engine()]
- "tests_test_jump_strict_quality_gate_test_jump_rejects_signal_missing_rejection_even_with_high_score": "test_jump_rejects_signal_missing_rejection_even_with_high_score()" | kind=code-symbol | source=tests/test_jump_strict_quality_gate.py:L15 | neighbors=[test_jump_strict_quality_gate.py, _engine()]
- "tests_test_jump_strict_quality_gate_test_non_jump_is_not_affected": "test_non_jump_is_not_affected()" | kind=code-symbol | source=tests/test_jump_strict_quality_gate.py:L46 | neighbors=[test_jump_strict_quality_gate.py, _engine()]
- "tests_test_live_demo_origin_print_analysis_diagnostics": "print_analysis_diagnostics()" | kind=code-symbol | source=tests/test_live_demo_origin.py:L8 | neighbors=[test_live_demo_origin.py, main()]
- "tests_test_live_demo_origin_print_position_diagnostics": "print_position_diagnostics()" | kind=code-symbol | source=tests/test_live_demo_origin.py:L28 | neighbors=[test_live_demo_origin.py, main()]
- "tests_test_live_demo_print_position_diagnostics": "print_position_diagnostics()" | kind=code-symbol | source=tests/test_live_demo.py:L966 | neighbors=[test_live_demo.py, main()]
- "tests_test_live_demo_smoke_stops_lifecyclemanager_process_signal_with_executor": ".process_signal_with_executor()" | kind=code-symbol | source=tests/test_live_demo_smoke_stops.py:L63 | neighbors=[_LifecycleManager, _Lifecycle]
- "tests_test_live_demo_smoke_stops_provider_ensure_symbol": ".ensure_symbol()" | kind=code-symbol | source=tests/test_live_demo_smoke_stops.py:L17 | neighbors=[_Provider, _Info]
- "tests_test_live_demo_smoke_stops_provider_symbol_spec": ".symbol_spec()" | kind=code-symbol | source=tests/test_live_demo_smoke_stops.py:L20 | neighbors=[_Provider, _Info]
- "tests_test_main_symbol_selection_fakeconnector": "FakeConnector" | kind=code-symbol | source=tests/test_main_symbol_selection.py:L9 | neighbors=[test_main_symbol_selection.py, .__init__()]
- "tests_test_main_symbol_selection_fakeprovider_init": ".__init__()" | kind=code-symbol | source=tests/test_main_symbol_selection.py:L14 | neighbors=[FakeProvider, FakeConnector]
- "tests_test_main_symbol_selection_test_categories_are_normalized": "test_categories_are_normalized()" | kind=code-symbol | source=tests/test_main_symbol_selection.py:L83 | neighbors=[test_main_symbol_selection.py, FakeProvider]
- "tests_test_main_symbol_selection_test_dynamic_symbols_are_discovered": "test_dynamic_symbols_are_discovered()" | kind=code-symbol | source=tests/test_main_symbol_selection.py:L62 | neighbors=[test_main_symbol_selection.py, FakeProvider]

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-033.json

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
