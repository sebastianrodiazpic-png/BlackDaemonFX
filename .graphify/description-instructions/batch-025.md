# Node Description Batch 26 of 56

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

- "tests_test_multi_timeframe_cache_test_stage_cache_reuses_data_and_pipeline_before_next_candle": "test_stage_cache_reuses_data_and_pipeline_before_next_candle()" | kind=code-symbol | source=tests/test_multi_timeframe_cache.py:L38 | neighbors=[test_multi_timeframe_cache.py, CountingAnalyzer, CountingProvider]
- "tests_test_orb_new_york_strategy_test_orb_builds_15_minute_range_before_allowing_breakout": "test_orb_builds_15_minute_range_before_allowing_breakout()" | kind=code-symbol | source=tests/test_orb_new_york_strategy.py:L78 | neighbors=[test_orb_new_york_strategy.py, _session_candles(), _strategy()]
- "tests_test_orb_new_york_strategy_test_orb_buy_requires_m5_breakout_then_retest_and_midpoint_stop": "test_orb_buy_requires_m5_breakout_then_retest_and_midpoint_stop()" | kind=code-symbol | source=tests/test_orb_new_york_strategy.py:L86 | neighbors=[test_orb_new_york_strategy.py, _session_candles(), _strategy()]
- "tests_test_orb_new_york_strategy_test_orb_does_not_run_on_weekends": "test_orb_does_not_run_on_weekends()" | kind=code-symbol | source=tests/test_orb_new_york_strategy.py:L135 | neighbors=[test_orb_new_york_strategy.py, _session_candles(), _strategy()]
- "tests_test_orb_new_york_strategy_test_orb_is_disabled_after_new_york_session_close": "test_orb_is_disabled_after_new_york_session_close()" | kind=code-symbol | source=tests/test_orb_new_york_strategy.py:L127 | neighbors=[test_orb_new_york_strategy.py, _session_candles(), _strategy()]
- "tests_test_orb_new_york_strategy_test_orb_rejects_breakout_without_retest": "test_orb_rejects_breakout_without_retest()" | kind=code-symbol | source=tests/test_orb_new_york_strategy.py:L106 | neighbors=[test_orb_new_york_strategy.py, _session_candles(), _strategy()]
- "tests_test_orb_new_york_strategy_test_orb_sell_requires_m5_breakout_then_retest_and_midpoint_stop": "test_orb_sell_requires_m5_breakout_then_retest_and_midpoint_stop()" | kind=code-symbol | source=tests/test_orb_new_york_strategy.py:L115 | neighbors=[test_orb_new_york_strategy.py, _session_candles(), _strategy()]
- "tests_test_orb_symbol_discovery": "test_orb_symbol_discovery.py" | kind=code-symbol | source=tests/test_orb_symbol_discovery.py:L1 | neighbors=[FakeProvider, test_discovery_excludes_disabled_orb_co…, test_discovery_includes_both_real_gold_…]
- "tests_test_paper_trade_monitoring_integration_sell_request": "sell_request()" | kind=code-symbol | source=tests/test_paper_trade_monitoring_integration.py:L25 | neighbors=[test_paper_trade_monitoring_integration…, test_monitor_multiple_open_positions_th…, test_monitoring_break_even_stop_closes_…]
- "tests_test_paper_trade_monitoring_integration_test_monitor_multiple_open_positions_through_executor": "test_monitor_multiple_open_positions_through_executor()" | kind=code-symbol | source=tests/test_paper_trade_monitoring_integration.py:L131 | neighbors=[test_paper_trade_monitoring_integration…, buy_request(), sell_request()]
- "tests_test_position_manager_test_clear_all": "test_clear_all()" | kind=code-symbol | source=tests/test_position_manager.py:L483 | neighbors=[test_position_manager.py, create_buy_position(), create_sell_position()]
- "tests_test_position_manager_test_get_open_positions": "test_get_open_positions()" | kind=code-symbol | source=tests/test_position_manager.py:L145 | neighbors=[test_position_manager.py, create_buy_position(), create_sell_position()]
- "tests_test_position_monitoring_service_test_monitor_open_positions_processes_available_prices_only": "test_monitor_open_positions_processes_available_prices_only()" | kind=code-symbol | source=tests/test_position_monitoring_service.py:L236 | neighbors=[test_position_monitoring_service.py, create_buy_position(), create_sell_position()]
- "tests_test_ready_to_ambiguous_transition": "test_ready_to_ambiguous_transition.py" | kind=code-symbol | source=tests/test_ready_to_ambiguous_transition.py:L1 | neighbors=[ControlledDataProvider, ControlledMultiTimeframeAnalyzer, test_controlled_ready_to_enter_to_ambig…]
- "tests_test_ready_to_enter_transition": "test_ready_to_enter_transition.py" | kind=code-symbol | source=tests/test_ready_to_enter_transition.py:L1 | neighbors=[ControlledDataProvider, ControlledMultiTimeframeAnalyzer, test_controlled_transition_to_ready_to_…]
- "tests_test_ready_to_enter_transition_rationale_13": "Proveedor artificial para una prueba completamente controlada.\r \r     No conecta" | kind=entity | source=tests/test_ready_to_enter_transition.py:L13 | neighbors=[MultiTimeframeAnalyzer, MultiTimeframeConfig, ControlledDataProvider]
- "tests_test_ready_to_enter_transition_rationale_310": "Analizador controlado.\r \r     La prueba NO ejecuta el pipeline SMC real." | kind=entity | source=tests/test_ready_to_enter_transition.py:L310 | neighbors=[MultiTimeframeAnalyzer, MultiTimeframeConfig, ControlledMultiTimeframeAnalyzer]
- "tests_test_ready_to_enter_transition_rationale_478": "Prueba completa:\r \r         H1 válido\r             ->\r         M15 setup válido" | kind=entity | source=tests/test_ready_to_enter_transition.py:L478 | neighbors=[MultiTimeframeAnalyzer, MultiTimeframeConfig, test_controlled_transition_to_ready_to_…]
- "tests_test_ready_to_execution_transition": "test_ready_to_execution_transition.py" | kind=code-symbol | source=tests/test_ready_to_execution_transition.py:L1 | neighbors=[ControlledDataProvider, ControlledMultiTimeframeAnalyzer, test_controlled_ready_to_enter_to_execu…]
- "tests_test_ready_to_no_exit_transition": "test_ready_to_no_exit_transition.py" | kind=code-symbol | source=tests/test_ready_to_no_exit_transition.py:L1 | neighbors=[ControlledDataProvider, ControlledMultiTimeframeAnalyzer, test_controlled_ready_to_enter_to_no_ex…]
- "tests_test_ready_to_stop_loss_transition": "test_ready_to_stop_loss_transition.py" | kind=code-symbol | source=tests/test_ready_to_stop_loss_transition.py:L1 | neighbors=[ControlledDataProvider, ControlledMultiTimeframeAnalyzer, test_controlled_ready_to_enter_to_stop_…]
- "tests_test_ready_to_stop_loss_transition_back": "test_ready_to_stop_loss_transition_back.py" | kind=code-symbol | source=tests/test_ready_to_stop_loss_transition_back.py:L1 | neighbors=[ControlledDataProvider, ControlledMultiTimeframeAnalyzer, test_controlled_ready_to_enter_to_ambig…]
- "tests_test_risk_manager_test_calculate_current_drawdown": "test_calculate_current_drawdown()" | kind=code-symbol | source=tests/test_risk_manager.py:L419 | neighbors=[test_risk_manager.py, print_result(), print_section()]
- "tests_test_risk_manager_test_calculate_current_risk": "test_calculate_current_risk()" | kind=code-symbol | source=tests/test_risk_manager.py:L282 | neighbors=[test_risk_manager.py, print_result(), print_section()]
- "tests_test_risk_manager_test_calculate_daily_loss": "test_calculate_daily_loss()" | kind=code-symbol | source=tests/test_risk_manager.py:L337 | neighbors=[test_risk_manager.py, print_result(), print_section()]
- "tests_test_risk_manager_test_calculate_open_positions_risk": "test_calculate_open_positions_risk()" | kind=code-symbol | source=tests/test_risk_manager.py:L463 | neighbors=[test_risk_manager.py, print_result(), print_section()]
- "tests_test_risk_manager_test_calculate_risk_reward": "test_calculate_risk_reward()" | kind=code-symbol | source=tests/test_risk_manager.py:L194 | neighbors=[test_risk_manager.py, print_result(), print_section()]
- "tests_test_risk_manager_test_check_daily_loss_limit": "test_check_daily_loss_limit()" | kind=code-symbol | source=tests/test_risk_manager.py:L500 | neighbors=[test_risk_manager.py, print_result(), print_section()]
- "tests_test_risk_manager_test_check_daily_loss_limit_blocked": "test_check_daily_loss_limit_blocked()" | kind=code-symbol | source=tests/test_risk_manager.py:L543 | neighbors=[test_risk_manager.py, print_result(), print_section()]
- "tests_test_risk_manager_test_check_drawdown_limit": "test_check_drawdown_limit()" | kind=code-symbol | source=tests/test_risk_manager.py:L582 | neighbors=[test_risk_manager.py, print_result(), print_section()]
- "tests_test_risk_manager_test_evaluate_risk_alias": "test_evaluate_risk_alias()" | kind=code-symbol | source=tests/test_risk_manager.py:L899 | neighbors=[test_risk_manager.py, print_result(), print_section()]
- "tests_test_risk_manager_test_evaluate_trade_risk_buy_approved": "test_evaluate_trade_risk_buy_approved()" | kind=code-symbol | source=tests/test_risk_manager.py:L616 | neighbors=[test_risk_manager.py, print_result(), print_section()]
- "tests_test_risk_manager_test_evaluate_trade_risk_consecutive_losses": "test_evaluate_trade_risk_consecutive_losses()" | kind=code-symbol | source=tests/test_risk_manager.py:L777 | neighbors=[test_risk_manager.py, print_result(), print_section()]
- "tests_test_risk_manager_test_evaluate_trade_risk_invalid_stop_loss": "test_evaluate_trade_risk_invalid_stop_loss()" | kind=code-symbol | source=tests/test_risk_manager.py:L692 | neighbors=[test_risk_manager.py, print_result(), print_section()]
- "tests_test_risk_manager_test_evaluate_trade_risk_invalid_take_profit": "test_evaluate_trade_risk_invalid_take_profit()" | kind=code-symbol | source=tests/test_risk_manager.py:L720 | neighbors=[test_risk_manager.py, print_result(), print_section()]
- "tests_test_risk_manager_test_evaluate_trade_risk_low_rr": "test_evaluate_trade_risk_low_rr()" | kind=code-symbol | source=tests/test_risk_manager.py:L748 | neighbors=[test_risk_manager.py, print_result(), print_section()]
- "tests_test_risk_manager_test_evaluate_trade_risk_max_positions": "test_evaluate_trade_risk_max_positions()" | kind=code-symbol | source=tests/test_risk_manager.py:L820 | neighbors=[test_risk_manager.py, print_result(), print_section()]
- "tests_test_risk_manager_test_evaluate_trade_risk_sell_approved": "test_evaluate_trade_risk_sell_approved()" | kind=code-symbol | source=tests/test_risk_manager.py:L656 | neighbors=[test_risk_manager.py, print_result(), print_section()]
- "tests_test_risk_manager_test_evaluate_trade_risk_total_risk": "test_evaluate_trade_risk_total_risk()" | kind=code-symbol | source=tests/test_risk_manager.py:L856 | neighbors=[test_risk_manager.py, print_result(), print_section()]
- "tests_test_risk_manager_test_get_risk_summary": "test_get_risk_summary()" | kind=code-symbol | source=tests/test_risk_manager.py:L927 | neighbors=[test_risk_manager.py, print_result(), print_section()]

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-025.json

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
