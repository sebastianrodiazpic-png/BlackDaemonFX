# Node Description Batch 15 of 56

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

- "smc_h1_doji_extremes_detect_h1_extreme_doji": "detect_h1_extreme_doji()" | kind=code-symbol | source=strategy/smc/h1_doji_extremes.py:L45 | neighbors=[h1_doji_extremes.py, _empty(), H1ExtremeDojiConfig, _safe_float(), Detecta un Doji H1 reciente en un extre…]
- "smc_harmonic_patterns_detect_harmonic_confirmation": "detect_harmonic_confirmation()" | kind=code-symbol | source=strategy/smc/harmonic_patterns.py:L137 | neighbors=[harmonic_patterns.py, _alternating_swings(), _evaluate_pattern(), HarmonicConfig, Devuelve el mejor patrón armónico confi…]
- "smc_ob_quality": "ob_quality.py" | kind=code-symbol | source=strategy/smc/ob_quality.py:L1 | neighbors=[calculate_average_range(), calculate_ob_displacement(), calculate_ob_score(), evaluate_order_block(), get_ob_grade()]
- "storage_account_page_syntax_test_render": "render()" | kind=code-symbol | source=storage/account_page_syntax_test.js:L56 | neighbors=[account_page_syntax_test.js, go(), e(), money(), num()]
- "tests_test_daemon_progress_repo": "Repo" | kind=code-symbol | source=tests/test_daemon_progress.py:L6 | neighbors=[test_daemon_progress.py, LiveTradingConfig, LiveTradingEngine, .sync_closed_mt5_trades(), test_process_symbols_reports_each_symbo…]
- "tests_test_daemon_risk_target_policy": "test_daemon_risk_target_policy.py" | kind=code-symbol | source=tests/test_daemon_risk_target_policy.py:L1 | neighbors=[Analyzer, Executor, Provider, Repo, test_rejects_trade_when_broker_max_volu…]
- "tests_test_daemon_risk_target_policy_analyzer": "Analyzer" | kind=code-symbol | source=tests/test_daemon_risk_target_policy.py:L54 | neighbors=[test_daemon_risk_target_policy.py, LiveTradingConfig, LiveTradingEngine, .analyze_symbol(), test_rejects_trade_when_broker_max_volu…]
- "tests_test_daemon_risk_target_policy_test_rejects_trade_when_broker_max_volume_cannot_reach_risk_target": "test_rejects_trade_when_broker_max_volume_cannot_reach_risk_target()" | kind=code-symbol | source=tests/test_daemon_risk_target_policy.py:L68 | neighbors=[test_daemon_risk_target_policy.py, Analyzer, Executor, Provider, Repo]
- "tests_test_daemon_single_entry_fallback_analyzer": "Analyzer" | kind=code-symbol | source=tests/test_daemon_single_entry_fallback.py:L27 | neighbors=[test_daemon_single_entry_fallback.py, LiveTradingConfig, LiveTradingEngine, .analyze_symbol(), _engine()]
- "tests_test_daemon_split_risk_management_test_one_percent_operation_is_split_into_two_half_percent_legs": "test_one_percent_operation_is_split_into_two_half_percent_legs()" | kind=code-symbol | source=tests/test_daemon_split_risk_management.py:L68 | neighbors=[test_daemon_split_risk_management.py, Analyzer, Executor, Provider, Repo]
- "tests_test_daemon_split_risk_management_test_smc_runner_extension_uses_4r_broker_target_without_increasing_risk": "test_smc_runner_extension_uses_4r_broker_target_without_increasing_risk()" | kind=code-symbol | source=tests/test_daemon_split_risk_management.py:L123 | neighbors=[test_daemon_split_risk_management.py, Analyzer, Executor, Provider, Repo]
- "tests_test_execution_preflight_service": "test_execution_preflight_service.py" | kind=code-symbol | source=tests/test_execution_preflight_service.py:L1 | neighbors=[execution_preflight_service.py, FakeProvider, FakeRepository, test_preflight_accepts_dict_symbol_info…, test_preflight_reports_ready()]
- "tests_test_h1_extreme_doji_confirmation": "test_h1_extreme_doji_confirmation.py" | kind=code-symbol | source=tests/test_h1_extreme_doji_confirmation.py:L1 | neighbors=[_base_frame(), test_bearish_h1_doji_at_upper_extreme_i…, test_bullish_h1_doji_at_lower_extreme_i…, test_disabled_doji_never_blocks_or_conf…, test_doji_in_middle_of_range_does_not_c…]
- "tests_test_h1_extreme_doji_confirmation_base_frame": "_base_frame()" | kind=code-symbol | source=tests/test_h1_extreme_doji_confirmation.py:L6 | neighbors=[test_h1_extreme_doji_confirmation.py, test_bearish_h1_doji_at_upper_extreme_i…, test_bullish_h1_doji_at_lower_extreme_i…, test_disabled_doji_never_blocks_or_conf…, test_doji_in_middle_of_range_does_not_c…]
- "tests_test_live_demo_smoke_stops_info": "_Info" | kind=code-symbol | source=tests/test_live_demo_smoke_stops.py:L7 | neighbors=[test_live_demo_smoke_stops.py, LiveDemoSmokeTestConfig, LiveDemoSmokeTestService, .ensure_symbol(), .symbol_spec()]
- "tests_test_live_demo_smoke_stops_repository": "_Repository" | kind=code-symbol | source=tests/test_live_demo_smoke_stops.py:L71 | neighbors=[test_live_demo_smoke_stops.py, LiveDemoSmokeTestConfig, LiveDemoSmokeTestService, .get_trade_by_execution_key(), test_smoke_uses_provider_stop_normaliza…]
- "tests_test_live_end_to_end_dry_run": "test_live_end_to_end_dry_run.py" | kind=code-symbol | source=tests/test_live_end_to_end_dry_run.py:L1 | neighbors=[FakeAnalyzer, FakeExecutor, FakeProvider, FakeRepository, test_live_engine_reaches_full_dry_run_v…]
- "tests_test_live_end_to_end_dry_run_fakeanalyzer": "FakeAnalyzer" | kind=code-symbol | source=tests/test_live_end_to_end_dry_run.py:L89 | neighbors=[test_live_end_to_end_dry_run.py, LiveTradingConfig, LiveTradingEngine, .analyze_symbol(), test_live_engine_reaches_full_dry_run_v…]
- "tests_test_live_end_to_end_dry_run_test_live_engine_reaches_full_dry_run_validated_path_without_sending_order": "test_live_engine_reaches_full_dry_run_validated_path_without_sending_order()" | kind=code-symbol | source=tests/test_live_end_to_end_dry_run.py:L124 | neighbors=[test_live_end_to_end_dry_run.py, FakeAnalyzer, FakeExecutor, FakeProvider, FakeRepository]
- "tests_test_live_paper_trading_engine_test_live_paper_monitor_uses_bid_for_buy_and_activates_break_even": "test_live_paper_monitor_uses_bid_for_buy_and_activates_break_even()" | kind=code-symbol | source=tests/test_live_paper_trading_engine.py:L73 | neighbors=[test_live_paper_trading_engine.py, build_engine(), FakeAnalyzer, FakeProvider, ready_signal()]
- "tests_test_live_paper_trading_engine_test_live_paper_opens_from_ready_signal": "test_live_paper_opens_from_ready_signal()" | kind=code-symbol | source=tests/test_live_paper_trading_engine.py:L61 | neighbors=[test_live_paper_trading_engine.py, build_engine(), FakeAnalyzer, FakeProvider, ready_signal()]
- "tests_test_live_paper_trading_engine_test_live_paper_take_profit_moves_lifecycle_to_win": "test_live_paper_take_profit_moves_lifecycle_to_win()" | kind=code-symbol | source=tests/test_live_paper_trading_engine.py:L86 | neighbors=[test_live_paper_trading_engine.py, build_engine(), FakeAnalyzer, FakeProvider, ready_signal()]
- "tests_test_live_paper_trading_engine_test_live_paper_uses_ask_for_sell_monitoring": "test_live_paper_uses_ask_for_sell_monitoring()" | kind=code-symbol | source=tests/test_live_paper_trading_engine.py:L110 | neighbors=[test_live_paper_trading_engine.py, build_engine(), FakeAnalyzer, FakeProvider, ready_signal()]
- "tests_test_live_paper_trading_engine_test_same_ready_signal_is_not_executed_twice": "test_same_ready_signal_is_not_executed_twice()" | kind=code-symbol | source=tests/test_live_paper_trading_engine.py:L98 | neighbors=[test_live_paper_trading_engine.py, build_engine(), FakeAnalyzer, FakeProvider, ready_signal()]
- "tests_test_orb_gold_contract_selection_repo": "Repo" | kind=code-symbol | source=tests/test_orb_gold_contract_selection.py:L7 | neighbors=[test_orb_gold_contract_selection.py, _engine(), LiveTradingConfig, LiveTradingEngine, .open_trades()]
- "tests_test_ready_to_ambiguous_transition_controlleddataprovider": "ControlledDataProvider" | kind=code-symbol | source=tests/test_ready_to_ambiguous_transition.py:L20 | neighbors=[test_ready_to_ambiguous_transition.py, MultiTimeframeAnalyzer, MultiTimeframeConfig, .get_candles(), test_controlled_ready_to_enter_to_ambig…]
- "tests_test_ready_to_execution_transition_controlleddataprovider": "ControlledDataProvider" | kind=code-symbol | source=tests/test_ready_to_execution_transition.py:L20 | neighbors=[test_ready_to_execution_transition.py, MultiTimeframeAnalyzer, MultiTimeframeConfig, .get_candles(), test_controlled_ready_to_enter_to_execu…]
- "tests_test_ready_to_no_exit_transition_controlleddataprovider": "ControlledDataProvider" | kind=code-symbol | source=tests/test_ready_to_no_exit_transition.py:L20 | neighbors=[test_ready_to_no_exit_transition.py, MultiTimeframeAnalyzer, MultiTimeframeConfig, .get_candles(), test_controlled_ready_to_enter_to_no_ex…]
- "tests_test_ready_to_stop_loss_transition_back_controlleddataprovider": "ControlledDataProvider" | kind=code-symbol | source=tests/test_ready_to_stop_loss_transition_back.py:L20 | neighbors=[test_ready_to_stop_loss_transition_back…, MultiTimeframeAnalyzer, MultiTimeframeConfig, .get_candles(), test_controlled_ready_to_enter_to_ambig…]
- "tests_test_ready_to_stop_loss_transition_controlleddataprovider": "ControlledDataProvider" | kind=code-symbol | source=tests/test_ready_to_stop_loss_transition.py:L20 | neighbors=[test_ready_to_stop_loss_transition.py, MultiTimeframeAnalyzer, MultiTimeframeConfig, .get_candles(), test_controlled_ready_to_enter_to_stop_…]
- "tests_test_risk_integration_test_consecutive_losses": "test_consecutive_losses()" | kind=code-symbol | source=tests/test_risk_integration.py:L337 | neighbors=[test_risk_integration.py, run_all_tests(), assert_result(), print_result(), print_section()]
- "tests_test_risk_integration_test_daily_loss_limit": "test_daily_loss_limit()" | kind=code-symbol | source=tests/test_risk_integration.py:L240 | neighbors=[test_risk_integration.py, run_all_tests(), assert_result(), print_result(), print_section()]
- "tests_test_risk_integration_test_drawdown_limit": "test_drawdown_limit()" | kind=code-symbol | source=tests/test_risk_integration.py:L285 | neighbors=[test_risk_integration.py, run_all_tests(), assert_result(), print_result(), print_section()]
- "tests_test_risk_integration_test_invalid_buy_stop_loss": "test_invalid_buy_stop_loss()" | kind=code-symbol | source=tests/test_risk_integration.py:L137 | neighbors=[test_risk_integration.py, run_all_tests(), assert_result(), print_result(), print_section()]
- "tests_test_risk_integration_test_invalid_risk_reward": "test_invalid_risk_reward()" | kind=code-symbol | source=tests/test_risk_integration.py:L205 | neighbors=[test_risk_integration.py, run_all_tests(), assert_result(), print_result(), print_section()]
- "tests_test_risk_integration_test_invalid_sell_take_profit": "test_invalid_sell_take_profit()" | kind=code-symbol | source=tests/test_risk_integration.py:L171 | neighbors=[test_risk_integration.py, run_all_tests(), assert_result(), print_result(), print_section()]
- "tests_test_risk_integration_test_open_positions_limit": "test_open_positions_limit()" | kind=code-symbol | source=tests/test_risk_integration.py:L380 | neighbors=[test_risk_integration.py, run_all_tests(), assert_result(), print_result(), print_section()]
- "tests_test_risk_integration_test_total_risk_limit": "test_total_risk_limit()" | kind=code-symbol | source=tests/test_risk_integration.py:L422 | neighbors=[test_risk_integration.py, run_all_tests(), assert_result(), print_result(), print_section()]
- "tests_test_risk_integration_test_valid_buy": "test_valid_buy()" | kind=code-symbol | source=tests/test_risk_integration.py:L67 | neighbors=[test_risk_integration.py, run_all_tests(), assert_result(), print_result(), print_section()]
- "tests_test_risk_integration_test_valid_sell": "test_valid_sell()" | kind=code-symbol | source=tests/test_risk_integration.py:L102 | neighbors=[test_risk_integration.py, run_all_tests(), assert_result(), print_result(), print_section()]

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-014.json

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
