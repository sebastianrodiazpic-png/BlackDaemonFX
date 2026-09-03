# Node Description Batch 36 of 56

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

- "tests_test_position_monitoring_service_test_closed_position_cannot_be_monitored": "test_closed_position_cannot_be_monitored()" | kind=code-symbol | source=tests/test_position_monitoring_service.py:L288 | neighbors=[test_position_monitoring_service.py, create_buy_position()]
- "tests_test_position_monitoring_service_test_monitor_buy_activates_break_even_at_one_to_one": "test_monitor_buy_activates_break_even_at_one_to_one()" | kind=code-symbol | source=tests/test_position_monitoring_service.py:L82 | neighbors=[test_position_monitoring_service.py, create_buy_position()]
- "tests_test_position_monitoring_service_test_monitor_buy_closes_at_break_even_after_retrace": "test_monitor_buy_closes_at_break_even_after_retrace()" | kind=code-symbol | source=tests/test_position_monitoring_service.py:L145 | neighbors=[test_position_monitoring_service.py, create_buy_position()]
- "tests_test_position_monitoring_service_test_monitor_buy_closes_at_take_profit": "test_monitor_buy_closes_at_take_profit()" | kind=code-symbol | source=tests/test_position_monitoring_service.py:L176 | neighbors=[test_position_monitoring_service.py, create_buy_position()]
- "tests_test_position_monitoring_service_test_monitor_buy_updates_price_without_break_even": "test_monitor_buy_updates_price_without_break_even()" | kind=code-symbol | source=tests/test_position_monitoring_service.py:L49 | neighbors=[test_position_monitoring_service.py, create_buy_position()]
- "tests_test_position_monitoring_service_test_monitor_sell_activates_break_even_at_one_to_one": "test_monitor_sell_activates_break_even_at_one_to_one()" | kind=code-symbol | source=tests/test_position_monitoring_service.py:L114 | neighbors=[test_position_monitoring_service.py, create_sell_position()]
- "tests_test_position_monitoring_service_test_monitor_sell_closes_at_stop_loss": "test_monitor_sell_closes_at_stop_loss()" | kind=code-symbol | source=tests/test_position_monitoring_service.py:L206 | neighbors=[test_position_monitoring_service.py, create_sell_position()]
- "tests_test_ready_to_ambiguous_transition_controlleddataprovider_get_candles": ".get_candles()" | kind=code-symbol | source=tests/test_ready_to_ambiguous_transition.py:L22 | neighbors=[ControlledDataProvider, test_controlled_ready_to_enter_to_ambig…]
- "tests_test_ready_to_execution_transition_controlleddataprovider_get_candles": ".get_candles()" | kind=code-symbol | source=tests/test_ready_to_execution_transition.py:L22 | neighbors=[ControlledDataProvider, test_controlled_ready_to_enter_to_execu…]
- "tests_test_ready_to_no_exit_transition_controlleddataprovider_get_candles": ".get_candles()" | kind=code-symbol | source=tests/test_ready_to_no_exit_transition.py:L22 | neighbors=[ControlledDataProvider, test_controlled_ready_to_enter_to_no_ex…]
- "tests_test_ready_to_stop_loss_transition_back_controlleddataprovider_get_candles": ".get_candles()" | kind=code-symbol | source=tests/test_ready_to_stop_loss_transition_back.py:L22 | neighbors=[ControlledDataProvider, test_controlled_ready_to_enter_to_ambig…]
- "tests_test_ready_to_stop_loss_transition_controlleddataprovider_get_candles": ".get_candles()" | kind=code-symbol | source=tests/test_ready_to_stop_loss_transition.py:L22 | neighbors=[ControlledDataProvider, test_controlled_ready_to_enter_to_stop_…]
- "tests_test_realtime_dashboard_test_dashboard_attaches_m5_chart_and_nested_break_even_snapshot_to_open_position": "test_dashboard_attaches_m5_chart_and_nested_break_even_snapshot_to_open_positio…" | kind=code-symbol | source=tests/test_realtime_dashboard.py:L173 | neighbors=[test_realtime_dashboard.py, Repo]
- "tests_test_realtime_dashboard_test_dashboard_chart_controls_apply_only_to_graph_and_support_timeframes_navigation": "test_dashboard_chart_controls_apply_only_to_graph_and_support_timeframes_naviga…" | kind=code-symbol | source=tests/test_realtime_dashboard.py:L601 | neighbors=[test_realtime_dashboard.py, Repo]
- "tests_test_realtime_dashboard_test_dashboard_exposes_separate_instrument_management_route": "test_dashboard_exposes_separate_instrument_management_route()" | kind=code-symbol | source=tests/test_realtime_dashboard.py:L213 | neighbors=[test_realtime_dashboard.py, Repo]
- "tests_test_realtime_dashboard_test_dashboard_extracts_realtime_trade_quality": "test_dashboard_extracts_realtime_trade_quality()" | kind=code-symbol | source=tests/test_realtime_dashboard.py:L25 | neighbors=[test_realtime_dashboard.py, Repo]
- "tests_test_realtime_dashboard_test_dashboard_html_exposes_audit_layers_and_rsi_panel": "test_dashboard_html_exposes_audit_layers_and_rsi_panel()" | kind=code-symbol | source=tests/test_realtime_dashboard.py:L297 | neighbors=[test_realtime_dashboard.py, Repo]
- "tests_test_realtime_dashboard_test_dashboard_html_exposes_complete_smc_audit_layers": "test_dashboard_html_exposes_complete_smc_audit_layers()" | kind=code-symbol | source=tests/test_realtime_dashboard.py:L503 | neighbors=[test_realtime_dashboard.py, Repo]
- "tests_test_realtime_dashboard_test_dashboard_instrument_catalog_is_grouped_and_sorted_and_dynamic": "test_dashboard_instrument_catalog_is_grouped_and_sorted_and_dynamic()" | kind=code-symbol | source=tests/test_realtime_dashboard.py:L139 | neighbors=[test_realtime_dashboard.py, Repo]
- "tests_test_realtime_dashboard_test_dashboard_marks_no_signal_as_waiting_and_explains_reason": "test_dashboard_marks_no_signal_as_waiting_and_explains_reason()" | kind=code-symbol | source=tests/test_realtime_dashboard.py:L337 | neighbors=[test_realtime_dashboard.py, Repo]
- "tests_test_realtime_dashboard_test_dashboard_offline_http_marks_data_as_persisted": "test_dashboard_offline_http_marks_data_as_persisted()" | kind=code-symbol | source=tests/test_realtime_dashboard.py:L567 | neighbors=[test_realtime_dashboard.py, Repo]
- "tests_test_realtime_dashboard_test_dashboard_persists_open_positions_and_restores_offline_state": "test_dashboard_persists_open_positions_and_restores_offline_state()" | kind=code-symbol | source=tests/test_realtime_dashboard.py:L520 | neighbors=[test_realtime_dashboard.py, Repo]
- "tests_test_realtime_dashboard_test_dashboard_position_health_detects_opposite_confirmed_signal": "test_dashboard_position_health_detects_opposite_confirmed_signal()" | kind=code-symbol | source=tests/test_realtime_dashboard.py:L61 | neighbors=[test_realtime_dashboard.py, Repo]
- "tests_test_realtime_dashboard_test_dashboard_position_health_keeps_aligned_profitable_trade": "test_dashboard_position_health_keeps_aligned_profitable_trade()" | kind=code-symbol | source=tests/test_realtime_dashboard.py:L101 | neighbors=[test_realtime_dashboard.py, Repo]
- "tests_test_realtime_dashboard_test_dashboard_rejects_empty_or_unknown_instrument_selection": "test_dashboard_rejects_empty_or_unknown_instrument_selection()" | kind=code-symbol | source=tests/test_realtime_dashboard.py:L159 | neighbors=[test_realtime_dashboard.py, Repo]
- "tests_test_realtime_dashboard_test_dashboard_translates_recent_analysis_codes_to_trader_friendly_spanish": "test_dashboard_translates_recent_analysis_codes_to_trader_friendly_spanish()" | kind=code-symbol | source=tests/test_realtime_dashboard.py:L315 | neighbors=[test_realtime_dashboard.py, Repo]
- "tests_test_risk_manager_test_calculate_max_loss_amount": "test_calculate_max_loss_amount()" | kind=code-symbol | source=tests/test_risk_manager.py:L314 | neighbors=[test_risk_manager.py, print_section()]
- "tests_test_risk_manager_test_count_consecutive_losses": "test_count_consecutive_losses()" | kind=code-symbol | source=tests/test_risk_manager.py:L386 | neighbors=[test_risk_manager.py, print_section()]
- "tests_test_risk_manager_test_validate_direction": "test_validate_direction()" | kind=code-symbol | source=tests/test_risk_manager.py:L43 | neighbors=[test_risk_manager.py, print_section()]
- "tests_test_runner_extension_manager_test_clean_uptrend_can_continue_runner": "test_clean_uptrend_can_continue_runner()" | kind=code-symbol | source=tests/test_runner_extension_manager.py:L25 | neighbors=[test_runner_extension_manager.py, _uptrend()]
- "tests_test_runner_extension_manager_test_insufficient_market_data_blocks_extension": "test_insufficient_market_data_blocks_extension()" | kind=code-symbol | source=tests/test_runner_extension_manager.py:L34 | neighbors=[test_runner_extension_manager.py, _uptrend()]
- "tests_test_signal_freshness_test_m5_signal_age_becomes_stale_after_limit": "test_m5_signal_age_becomes_stale_after_limit()" | kind=code-symbol | source=tests/test_signal_freshness.py:L32 | neighbors=[test_signal_freshness.py, _analyzer()]
- "tests_test_signal_freshness_test_m5_signal_age_exact_index_is_fresh_at_limit": "test_m5_signal_age_exact_index_is_fresh_at_limit()" | kind=code-symbol | source=tests/test_signal_freshness.py:L17 | neighbors=[test_signal_freshness.py, _analyzer()]
- "tests_test_signal_freshness_test_m5_signal_age_minutes_can_block_even_when_candle_limit_allows": "test_m5_signal_age_minutes_can_block_even_when_candle_limit_allows()" | kind=code-symbol | source=tests/test_signal_freshness.py:L45 | neighbors=[test_signal_freshness.py, _analyzer()]
- "tests_test_signal_freshness_test_market_signal_blocks_large_entry_drift_in_r_units": "test_market_signal_blocks_large_entry_drift_in_r_units()" | kind=code-symbol | source=tests/test_signal_freshness.py:L89 | neighbors=[test_signal_freshness.py, _engine()]
- "tests_test_signal_freshness_test_market_signal_buy_is_invalidated_at_structural_stop": "test_market_signal_buy_is_invalidated_at_structural_stop()" | kind=code-symbol | source=tests/test_signal_freshness.py:L69 | neighbors=[test_signal_freshness.py, _engine()]
- "tests_test_signal_freshness_test_market_signal_sell_is_invalidated_at_structural_stop": "test_market_signal_sell_is_invalidated_at_structural_stop()" | kind=code-symbol | source=tests/test_signal_freshness.py:L79 | neighbors=[test_signal_freshness.py, _engine()]
- "tests_test_signal_freshness_test_signal_age_uses_temporal_fallback_when_timestamp_is_not_exact_candle": "test_signal_age_uses_temporal_fallback_when_timestamp_is_not_exact_candle()" | kind=code-symbol | source=tests/test_signal_freshness.py:L101 | neighbors=[test_signal_freshness.py, _analyzer()]
- "tests_test_trade_lifecycle_full_integration_controlleddataprovider_h1": "._h1()" | kind=code-symbol | source=tests/test_trade_lifecycle_full_integration.py:L70 | neighbors=[ControlledDataProvider, .get_candles()]
- "tests_test_trade_lifecycle_full_integration_controlleddataprovider_m15": "._m15()" | kind=code-symbol | source=tests/test_trade_lifecycle_full_integration.py:L116 | neighbors=[ControlledDataProvider, .get_candles()]

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-035.json

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
