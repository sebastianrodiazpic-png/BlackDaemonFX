# Node Description Batch 35 of 56

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

- "tests_test_main_symbol_selection_test_explicit_symbol_has_priority": "test_explicit_symbol_has_priority()" | kind=code-symbol | source=tests/test_main_symbol_selection.py:L44 | neighbors=[test_main_symbol_selection.py, FakeProvider]
- "tests_test_money_management": "test_money_management.py" | kind=code-symbol | source=tests/test_money_management.py:L1 | neighbors=[get_final_balance(), main()]
- "tests_test_money_management_main": "main()" | kind=code-symbol | source=tests/test_money_management.py:L123 | neighbors=[test_money_management.py, get_final_balance()]
- "tests_test_money_manager": "test_money_manager.py" | kind=code-symbol | source=tests/test_money_manager.py:L1 | neighbors=[money_manager.py, main()]
- "tests_test_mt5_data": "test_mt5_data.py" | kind=code-symbol | source=tests/test_mt5_data.py:L1 | neighbors=[mt5_data.py, main()]
- "tests_test_multi_timeframe_sequence_test_sequence_can_disable_m5_after_m15_requirement": "test_sequence_can_disable_m5_after_m15_requirement()" | kind=code-symbol | source=tests/test_multi_timeframe_sequence.py:L40 | neighbors=[test_multi_timeframe_sequence.py, _frame()]
- "tests_test_multi_timeframe_sequence_test_sequence_can_fall_back_to_previous_m15_when_config_allows_it": "test_sequence_can_fall_back_to_previous_m15_when_config_allows_it()" | kind=code-symbol | source=tests/test_multi_timeframe_sequence.py:L25 | neighbors=[test_multi_timeframe_sequence.py, _frame()]
- "tests_test_multi_timeframe_sequence_test_sequence_uses_latest_m15_when_required": "test_sequence_uses_latest_m15_when_required()" | kind=code-symbol | source=tests/test_multi_timeframe_sequence.py:L10 | neighbors=[test_multi_timeframe_sequence.py, _frame()]
- "tests_test_orb_gold_contract_selection_test_gold_selector_chooses_lower_execution_quality_score": "test_gold_selector_chooses_lower_execution_quality_score()" | kind=code-symbol | source=tests/test_orb_gold_contract_selection.py:L29 | neighbors=[test_orb_gold_contract_selection.py, _engine()]
- "tests_test_orb_gold_contract_selection_test_gold_selector_does_not_duplicate_gold_exposure": "test_gold_selector_does_not_duplicate_gold_exposure()" | kind=code-symbol | source=tests/test_orb_gold_contract_selection.py:L70 | neighbors=[test_orb_gold_contract_selection.py, _engine()]
- "tests_test_orb_gold_contract_selection_test_gold_selector_skips_expensive_comparison_outside_orb_session": "test_gold_selector_skips_expensive_comparison_outside_orb_session()" | kind=code-symbol | source=tests/test_orb_gold_contract_selection.py:L84 | neighbors=[test_orb_gold_contract_selection.py, _engine()]
- "tests_test_orb_gold_contract_selection_test_gold_selector_uses_xauusd_when_micro_is_not_viable": "test_gold_selector_uses_xauusd_when_micro_is_not_viable()" | kind=code-symbol | source=tests/test_orb_gold_contract_selection.py:L51 | neighbors=[test_orb_gold_contract_selection.py, _engine()]
- "tests_test_orb_symbol_discovery_test_discovery_excludes_disabled_orb_contracts": "test_discovery_excludes_disabled_orb_contracts()" | kind=code-symbol | source=tests/test_orb_symbol_discovery.py:L33 | neighbors=[test_orb_symbol_discovery.py, FakeProvider]
- "tests_test_orb_symbol_discovery_test_discovery_includes_both_real_gold_contracts_and_not_gold_derived_indices": "test_discovery_includes_both_real_gold_contracts_and_not_gold_derived_indices()" | kind=code-symbol | source=tests/test_orb_symbol_discovery.py:L25 | neighbors=[test_orb_symbol_discovery.py, FakeProvider]
- "tests_test_paper_trade_executor_create_sell_request": "create_sell_request()" | kind=code-symbol | source=tests/test_paper_trade_executor.py:L47 | neighbors=[test_paper_trade_executor.py, test_paper_execute_sell()]
- "tests_test_paper_trade_executor_test_cannot_close_position_twice": "test_cannot_close_position_twice()" | kind=code-symbol | source=tests/test_paper_trade_executor.py:L516 | neighbors=[test_paper_trade_executor.py, create_buy_request()]
- "tests_test_paper_trade_executor_test_close_position": "test_close_position()" | kind=code-symbol | source=tests/test_paper_trade_executor.py:L464 | neighbors=[test_paper_trade_executor.py, create_buy_request()]
- "tests_test_paper_trade_executor_test_duplicate_execution_is_blocked": "test_duplicate_execution_is_blocked()" | kind=code-symbol | source=tests/test_paper_trade_executor.py:L367 | neighbors=[test_paper_trade_executor.py, create_buy_request()]
- "tests_test_paper_trade_executor_test_get_position": "test_get_position()" | kind=code-symbol | source=tests/test_paper_trade_executor.py:L419 | neighbors=[test_paper_trade_executor.py, create_buy_request()]
- "tests_test_paper_trade_executor_test_paper_execute_buy": "test_paper_execute_buy()" | kind=code-symbol | source=tests/test_paper_trade_executor.py:L75 | neighbors=[test_paper_trade_executor.py, create_buy_request()]
- "tests_test_paper_trade_executor_test_paper_execute_sell": "test_paper_execute_sell()" | kind=code-symbol | source=tests/test_paper_trade_executor.py:L129 | neighbors=[test_paper_trade_executor.py, create_sell_request()]
- "tests_test_paper_trade_monitoring_integration_test_execute_registers_position_in_position_manager": "test_execute_registers_position_in_position_manager()" | kind=code-symbol | source=tests/test_paper_trade_monitoring_integration.py:L38 | neighbors=[test_paper_trade_monitoring_integration…, buy_request()]
- "tests_test_paper_trade_monitoring_integration_test_manual_close_syncs_position_manager": "test_manual_close_syncs_position_manager()" | kind=code-symbol | source=tests/test_paper_trade_monitoring_integration.py:L111 | neighbors=[test_paper_trade_monitoring_integration…, buy_request()]
- "tests_test_paper_trade_monitoring_integration_test_monitoring_break_even_stop_closes_paper_and_managed_position": "test_monitoring_break_even_stop_closes_paper_and_managed_position()" | kind=code-symbol | source=tests/test_paper_trade_monitoring_integration.py:L91 | neighbors=[test_paper_trade_monitoring_integration…, sell_request()]
- "tests_test_paper_trade_monitoring_integration_test_monitoring_break_even_syncs_stop_loss_to_paper_executor": "test_monitoring_break_even_syncs_stop_loss_to_paper_executor()" | kind=code-symbol | source=tests/test_paper_trade_monitoring_integration.py:L52 | neighbors=[test_paper_trade_monitoring_integration…, buy_request()]
- "tests_test_paper_trade_monitoring_integration_test_monitoring_take_profit_closes_paper_and_managed_position": "test_monitoring_take_profit_closes_paper_and_managed_position()" | kind=code-symbol | source=tests/test_paper_trade_monitoring_integration.py:L70 | neighbors=[test_paper_trade_monitoring_integration…, buy_request()]
- "tests_test_position_manager_test_apply_break_even_buy_at_one_to_one": "test_apply_break_even_buy_at_one_to_one()" | kind=code-symbol | source=tests/test_position_manager.py:L521 | neighbors=[test_position_manager.py, create_buy_position()]
- "tests_test_position_manager_test_apply_break_even_sell_at_one_to_one": "test_apply_break_even_sell_at_one_to_one()" | kind=code-symbol | source=tests/test_position_manager.py:L563 | neighbors=[test_position_manager.py, create_sell_position()]
- "tests_test_position_manager_test_break_even_cannot_be_applied_twice": "test_break_even_cannot_be_applied_twice()" | kind=code-symbol | source=tests/test_position_manager.py:L645 | neighbors=[test_position_manager.py, create_buy_position()]
- "tests_test_position_manager_test_break_even_is_not_activated_before_one_to_one": "test_break_even_is_not_activated_before_one_to_one()" | kind=code-symbol | source=tests/test_position_manager.py:L605 | neighbors=[test_position_manager.py, create_buy_position()]
- "tests_test_position_manager_test_cannot_close_position_twice": "test_cannot_close_position_twice()" | kind=code-symbol | source=tests/test_position_manager.py:L345 | neighbors=[test_position_manager.py, create_buy_position()]
- "tests_test_position_manager_test_clear_closed_positions": "test_clear_closed_positions()" | kind=code-symbol | source=tests/test_position_manager.py:L448 | neighbors=[test_position_manager.py, create_buy_position()]
- "tests_test_position_manager_test_close_buy_position": "test_close_buy_position()" | kind=code-symbol | source=tests/test_position_manager.py:L259 | neighbors=[test_position_manager.py, create_buy_position()]
- "tests_test_position_manager_test_close_sell_position": "test_close_sell_position()" | kind=code-symbol | source=tests/test_position_manager.py:L305 | neighbors=[test_position_manager.py, create_sell_position()]
- "tests_test_position_manager_test_closed_positions_history": "test_closed_positions_history()" | kind=code-symbol | source=tests/test_position_manager.py:L408 | neighbors=[test_position_manager.py, create_buy_position()]
- "tests_test_position_manager_test_duplicate_position_is_blocked": "test_duplicate_position_is_blocked()" | kind=code-symbol | source=tests/test_position_manager.py:L79 | neighbors=[test_position_manager.py, create_buy_position()]
- "tests_test_position_manager_test_get_position": "test_get_position()" | kind=code-symbol | source=tests/test_position_manager.py:L110 | neighbors=[test_position_manager.py, create_buy_position()]
- "tests_test_position_manager_test_register_position": "test_register_position()" | kind=code-symbol | source=tests/test_position_manager.py:L43 | neighbors=[test_position_manager.py, create_buy_position()]
- "tests_test_position_manager_test_update_price_buy": "test_update_price_buy()" | kind=code-symbol | source=tests/test_position_manager.py:L181 | neighbors=[test_position_manager.py, create_buy_position()]
- "tests_test_position_manager_test_update_price_sell": "test_update_price_sell()" | kind=code-symbol | source=tests/test_position_manager.py:L222 | neighbors=[test_position_manager.py, create_sell_position()]

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-034.json

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
