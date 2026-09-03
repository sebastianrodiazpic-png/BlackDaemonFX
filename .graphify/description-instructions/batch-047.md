# Node Description Batch 48 of 56

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

- "tests_test_orb_new_york_strategy_test_gold_contract_score_uses_spread_and_margin_as_execution_quality_tiebreakers": "test_gold_contract_score_uses_spread_and_margin_as_execution_quality_tiebreaker…" | kind=code-symbol | source=tests/test_orb_new_york_strategy.py:L155 | neighbors=[test_orb_new_york_strategy.py]
- "tests_test_orb_new_york_strategy_test_orb_gold_scope_accepts_standard_and_micro_gold": "test_orb_gold_scope_accepts_standard_and_micro_gold()" | kind=code-symbol | source=tests/test_orb_new_york_strategy.py:L143 | neighbors=[test_orb_new_york_strategy.py]
- "tests_test_orb_new_york_strategy_test_orb_symbol_scope_is_limited_to_requested_markets": "test_orb_symbol_scope_is_limited_to_requested_markets()" | kind=code-symbol | source=tests/test_orb_new_york_strategy.py:L67 | neighbors=[test_orb_new_york_strategy.py]
- "tests_test_orb_symbol_discovery_fakeprovider_get_symbol_info": ".get_symbol_info()" | kind=code-symbol | source=tests/test_orb_symbol_discovery.py:L21 | neighbors=[FakeProvider]
- "tests_test_orb_symbol_discovery_fakeprovider_init": ".__init__()" | kind=code-symbol | source=tests/test_orb_symbol_discovery.py:L6 | neighbors=[FakeProvider]
- "tests_test_orb_symbol_discovery_fakeprovider_search_symbols": ".search_symbols()" | kind=code-symbol | source=tests/test_orb_symbol_discovery.py:L17 | neighbors=[FakeProvider]
- "tests_test_order_blocks": "test_order_blocks.py" | kind=code-symbol | source=tests/test_order_blocks.py:L1 | neighbors=[main()]
- "tests_test_order_blocks_main": "main()" | kind=code-symbol | source=tests/test_order_blocks.py:L14 | neighbors=[test_order_blocks.py]
- "tests_test_paper_trade_executor_test_invalid_buy_levels": "test_invalid_buy_levels()" | kind=code-symbol | source=tests/test_paper_trade_executor.py:L171 | neighbors=[test_paper_trade_executor.py]
- "tests_test_paper_trade_executor_test_invalid_direction": "test_invalid_direction()" | kind=code-symbol | source=tests/test_paper_trade_executor.py:L269 | neighbors=[test_paper_trade_executor.py]
- "tests_test_paper_trade_executor_test_invalid_sell_levels": "test_invalid_sell_levels()" | kind=code-symbol | source=tests/test_paper_trade_executor.py:L220 | neighbors=[test_paper_trade_executor.py]
- "tests_test_paper_trade_executor_test_invalid_volume": "test_invalid_volume()" | kind=code-symbol | source=tests/test_paper_trade_executor.py:L318 | neighbors=[test_paper_trade_executor.py]
- "tests_test_paper_trade_executor_test_unknown_position": "test_unknown_position()" | kind=code-symbol | source=tests/test_paper_trade_executor.py:L561 | neighbors=[test_paper_trade_executor.py]
- "tests_test_position_manager_test_unknown_position": "test_unknown_position()" | kind=code-symbol | source=tests/test_position_manager.py:L382 | neighbors=[test_position_manager.py]
- "tests_test_position_monitoring_service_test_monitor_unknown_position_is_blocked": "test_monitor_unknown_position_is_blocked()" | kind=code-symbol | source=tests/test_position_monitoring_service.py:L267 | neighbors=[test_position_monitoring_service.py]
- "tests_test_position_sizing": "test_position_sizing.py" | kind=code-symbol | source=tests/test_position_sizing.py:L1 | neighbors=[main()]
- "tests_test_position_sizing_main": "main()" | kind=code-symbol | source=tests/test_position_sizing.py:L53 | neighbors=[test_position_sizing.py]
- "tests_test_premiun_discount": "test_premiun_discount.py" | kind=code-symbol | source=tests/test_premiun_discount.py:L1 | neighbors=[main()]
- "tests_test_premiun_discount_main": "main()" | kind=code-symbol | source=tests/test_premiun_discount.py:L27 | neighbors=[test_premiun_discount.py]
- "tests_test_ready_to_ambiguous_transition_controlledmultitimeframeanalyzer_run_pipeline": "._run_pipeline()" | kind=code-symbol | source=tests/test_ready_to_ambiguous_transition.py:L242 | neighbors=[ControlledMultiTimeframeAnalyzer]
- "tests_test_ready_to_enter_transition_controlleddataprovider_get_candles": ".get_candles()" | kind=code-symbol | source=tests/test_ready_to_enter_transition.py:L32 | neighbors=[ControlledDataProvider]
- "tests_test_ready_to_enter_transition_controlledmultitimeframeanalyzer_run_pipeline": "._run_pipeline()" | kind=code-symbol | source=tests/test_ready_to_enter_transition.py:L333 | neighbors=[ControlledMultiTimeframeAnalyzer]
- "tests_test_ready_to_execution_transition_controlledmultitimeframeanalyzer_run_pipeline": "._run_pipeline()" | kind=code-symbol | source=tests/test_ready_to_execution_transition.py:L242 | neighbors=[ControlledMultiTimeframeAnalyzer]
- "tests_test_ready_to_no_exit_transition_controlledmultitimeframeanalyzer_run_pipeline": "._run_pipeline()" | kind=code-symbol | source=tests/test_ready_to_no_exit_transition.py:L416 | neighbors=[ControlledMultiTimeframeAnalyzer]
- "tests_test_ready_to_stop_loss_transition_back_controlledmultitimeframeanalyzer_run_pipeline": "._run_pipeline()" | kind=code-symbol | source=tests/test_ready_to_stop_loss_transition_back.py:L242 | neighbors=[ControlledMultiTimeframeAnalyzer]
- "tests_test_ready_to_stop_loss_transition_controlledmultitimeframeanalyzer_run_pipeline": "._run_pipeline()" | kind=code-symbol | source=tests/test_ready_to_stop_loss_transition.py:L282 | neighbors=[ControlledMultiTimeframeAnalyzer]
- "tests_test_realtime_dashboard_repo_open_trades": ".open_trades()" | kind=code-symbol | source=tests/test_realtime_dashboard.py:L5 | neighbors=[Repo]
- "tests_test_realtime_dashboard_test_account_api_reads_sqlalchemy_directly_and_survives_dashboard_state_loss": "test_account_api_reads_sqlalchemy_directly_and_survives_dashboard_state_loss()" | kind=code-symbol | source=tests/test_realtime_dashboard.py:L393 | neighbors=[test_realtime_dashboard.py]
- "tests_test_realtime_dashboard_test_dashboard_account_payload_and_route": "test_dashboard_account_payload_and_route()" | kind=code-symbol | source=tests/test_realtime_dashboard.py:L357 | neighbors=[test_realtime_dashboard.py]
- "tests_test_realtime_dashboard_test_dashboard_explicit_initial_selection_temporarily_overrides_persisted_preference": "test_dashboard_explicit_initial_selection_temporarily_overrides_persisted_prefe…" | kind=code-symbol | source=tests/test_realtime_dashboard.py:L682 | neighbors=[test_realtime_dashboard.py]
- "tests_test_realtime_dashboard_test_dashboard_instrument_selection_is_saved_to_sqlalchemy_and_restored": "test_dashboard_instrument_selection_is_saved_to_sqlalchemy_and_restored()" | kind=code-symbol | source=tests/test_realtime_dashboard.py:L649 | neighbors=[test_realtime_dashboard.py]
- "tests_test_realtime_dashboard_test_dashboard_preserves_entry_thesis_separately_from_latest_analysis": "test_dashboard_preserves_entry_thesis_separately_from_latest_analysis()" | kind=code-symbol | source=tests/test_realtime_dashboard.py:L234 | neighbors=[test_realtime_dashboard.py]
- "tests_test_realtime_dashboard_test_dashboard_shows_external_mt5_positions_without_managing_them": "test_dashboard_shows_external_mt5_positions_without_managing_them()" | kind=code-symbol | source=tests/test_realtime_dashboard.py:L582 | neighbors=[test_realtime_dashboard.py]
- "tests_test_realtime_dashboard_test_fvg_zone_labels_follow_chart_time_coordinates_without_viewport_clamp": "test_fvg_zone_labels_follow_chart_time_coordinates_without_viewport_clamp()" | kind=code-symbol | source=tests/test_realtime_dashboard.py:L639 | neighbors=[test_realtime_dashboard.py]
- "tests_test_realtime_dashboard_test_smc_visual_context_exposes_structure_liquidity_ob_fvg_and_pd": "test_smc_visual_context_exposes_structure_liquidity_ob_fvg_and_pd()" | kind=code-symbol | source=tests/test_realtime_dashboard.py:L459 | neighbors=[test_realtime_dashboard.py]
- "tests_test_risk_reward": "test_risk_reward.py" | kind=code-symbol | source=tests/test_risk_reward.py:L1 | neighbors=[main()]
- "tests_test_risk_reward_main": "main()" | kind=code-symbol | source=tests/test_risk_reward.py:L32 | neighbors=[test_risk_reward.py]
- "tests_test_runner_extension_manager_test_rr_price_buy_and_sell": "test_rr_price_buy_and_sell()" | kind=code-symbol | source=tests/test_runner_extension_manager.py:L20 | neighbors=[test_runner_extension_manager.py]
- "tests_test_setup_detector": "test_setup_detector.py" | kind=code-symbol | source=tests/test_setup_detector.py:L1 | neighbors=[main()]
- "tests_test_setup_detector_main": "main()" | kind=code-symbol | source=tests/test_setup_detector.py:L24 | neighbors=[test_setup_detector.py]

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-047.json

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
