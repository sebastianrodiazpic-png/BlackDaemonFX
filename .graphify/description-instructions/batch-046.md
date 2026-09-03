# Node Description Batch 47 of 56

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

- "tests_test_live_end_to_end_dry_run_fakeexecutor_normalize_market_stops": ".normalize_market_stops()" | kind=code-symbol | source=tests/test_live_end_to_end_dry_run.py:L46 | neighbors=[FakeExecutor]
- "tests_test_live_end_to_end_dry_run_fakeexecutor_place_market_order": ".place_market_order()" | kind=code-symbol | source=tests/test_live_end_to_end_dry_run.py:L84 | neighbors=[FakeExecutor]
- "tests_test_live_end_to_end_dry_run_fakeprovider_ensure_symbol": ".ensure_symbol()" | kind=code-symbol | source=tests/test_live_end_to_end_dry_run.py:L12 | neighbors=[FakeProvider]
- "tests_test_live_end_to_end_dry_run_fakeprovider_get_current_tick": ".get_current_tick()" | kind=code-symbol | source=tests/test_live_end_to_end_dry_run.py:L15 | neighbors=[FakeProvider]
- "tests_test_live_end_to_end_dry_run_fakeprovider_resolve_symbol": ".resolve_symbol()" | kind=code-symbol | source=tests/test_live_end_to_end_dry_run.py:L9 | neighbors=[FakeProvider]
- "tests_test_live_end_to_end_dry_run_fakerepository_get_trade_by_execution_key": ".get_trade_by_execution_key()" | kind=code-symbol | source=tests/test_live_end_to_end_dry_run.py:L28 | neighbors=[FakeRepository]
- "tests_test_live_end_to_end_dry_run_fakerepository_init": ".__init__()" | kind=code-symbol | source=tests/test_live_end_to_end_dry_run.py:L20 | neighbors=[FakeRepository]
- "tests_test_live_end_to_end_dry_run_fakerepository_open_trades": ".open_trades()" | kind=code-symbol | source=tests/test_live_end_to_end_dry_run.py:L31 | neighbors=[FakeRepository]
- "tests_test_live_end_to_end_dry_run_fakerepository_save_account_snapshot": ".save_account_snapshot()" | kind=code-symbol | source=tests/test_live_end_to_end_dry_run.py:L34 | neighbors=[FakeRepository]
- "tests_test_live_end_to_end_dry_run_fakerepository_save_signal_once": ".save_signal_once()" | kind=code-symbol | source=tests/test_live_end_to_end_dry_run.py:L24 | neighbors=[FakeRepository]
- "tests_test_live_execution_helpers_test_min_volume_does_not_force_excess_risk": "test_min_volume_does_not_force_excess_risk()" | kind=code-symbol | source=tests/test_live_execution_helpers.py:L12 | neighbors=[test_live_execution_helpers.py]
- "tests_test_live_execution_helpers_test_normalize_volume_rounds_down_to_step": "test_normalize_volume_rounds_down_to_step()" | kind=code-symbol | source=tests/test_live_execution_helpers.py:L7 | neighbors=[test_live_execution_helpers.py]
- "tests_test_live_paper_trading_engine_fakeanalyzer_analyze_symbol": ".analyze_symbol()" | kind=code-symbol | source=tests/test_live_paper_trading_engine.py:L29 | neighbors=[FakeAnalyzer]
- "tests_test_live_paper_trading_engine_fakeanalyzer_init": ".__init__()" | kind=code-symbol | source=tests/test_live_paper_trading_engine.py:L25 | neighbors=[FakeAnalyzer]
- "tests_test_live_paper_trading_engine_fakeprovider_get_current_tick": ".get_current_tick()" | kind=code-symbol | source=tests/test_live_paper_trading_engine.py:L16 | neighbors=[FakeProvider]
- "tests_test_live_paper_trading_engine_fakeprovider_init": ".__init__()" | kind=code-symbol | source=tests/test_live_paper_trading_engine.py:L12 | neighbors=[FakeProvider]
- "tests_test_main_account_stats_reset_cli": "test_main_account_stats_reset_cli.py" | kind=code-symbol | source=tests/test_main_account_stats_reset_cli.py:L1 | neighbors=[test_main_exposes_account_stats_reset_c…]
- "tests_test_main_account_stats_reset_cli_test_main_exposes_account_stats_reset_command_and_confirmation": "test_main_exposes_account_stats_reset_command_and_confirmation()" | kind=code-symbol | source=tests/test_main_account_stats_reset_cli.py:L5 | neighbors=[test_main_account_stats_reset_cli.py]
- "tests_test_main_symbol_selection_fakeinstrumentmanager_get_active_symbols": ".get_active_symbols()" | kind=code-symbol | source=tests/test_main_symbol_selection.py:L28 | neighbors=[FakeInstrumentManager]
- "tests_test_main_symbol_selection_fakeinstrumentmanager_init": ".__init__()" | kind=code-symbol | source=tests/test_main_symbol_selection.py:L24 | neighbors=[FakeInstrumentManager]
- "tests_test_main_symbol_selection_fakeprovider_ensure_symbol": ".ensure_symbol()" | kind=code-symbol | source=tests/test_main_symbol_selection.py:L18 | neighbors=[FakeProvider]
- "tests_test_main_symbol_selection_test_offline_modes_require_symbol": "test_offline_modes_require_symbol()" | kind=code-symbol | source=tests/test_main_symbol_selection.py:L115 | neighbors=[test_main_symbol_selection.py]
- "tests_test_main_symbol_selection_test_strategy_timeframes_are_used_outside_instruments": "test_strategy_timeframes_are_used_outside_instruments()" | kind=code-symbol | source=tests/test_main_symbol_selection.py:L133 | neighbors=[test_main_symbol_selection.py]
- "tests_test_market_structure": "test_market_structure.py" | kind=code-symbol | source=tests/test_market_structure.py:L1 | neighbors=[main()]
- "tests_test_market_structure_main": "main()" | kind=code-symbol | source=tests/test_market_structure.py:L16 | neighbors=[test_market_structure.py]
- "tests_test_money_management_rationale_85": "Obtiene el balance final de manera segura.\r \r     Si existe la columna balance_a" | kind=entity | source=tests/test_money_management.py:L85 | neighbors=[get_final_balance()]
- "tests_test_money_manager_main": "main()" | kind=code-symbol | source=tests/test_money_manager.py:L4 | neighbors=[test_money_manager.py]
- "tests_test_mt5_connection_main": "main()" | kind=code-symbol | source=tests/test_mt5_connection.py:L5 | neighbors=[test_mt5_connection.py]
- "tests_test_mt5_data_main": "main()" | kind=code-symbol | source=tests/test_mt5_data.py:L4 | neighbors=[test_mt5_data.py]
- "tests_test_mt5_symbol": "test_mt5_symbol.py" | kind=code-symbol | source=tests/test_mt5_symbol.py:L1 | neighbors=[test_symbol()]
- "tests_test_mt5_symbol_test_symbol": "test_symbol()" | kind=code-symbol | source=tests/test_mt5_symbol.py:L7 | neighbors=[test_mt5_symbol.py]
- "tests_test_multi_timeframe_cache_countinganalyzer_init": ".__init__()" | kind=code-symbol | source=tests/test_multi_timeframe_cache.py:L23 | neighbors=[CountingAnalyzer]
- "tests_test_multi_timeframe_cache_countinganalyzer_run_pipeline": "._run_pipeline()" | kind=code-symbol | source=tests/test_multi_timeframe_cache.py:L27 | neighbors=[CountingAnalyzer]
- "tests_test_multi_timeframe_cache_countingprovider_get_candles": ".get_candles()" | kind=code-symbol | source=tests/test_multi_timeframe_cache.py:L10 | neighbors=[CountingProvider]
- "tests_test_multi_timeframe_cache_countingprovider_init": ".__init__()" | kind=code-symbol | source=tests/test_multi_timeframe_cache.py:L7 | neighbors=[CountingProvider]
- "tests_test_orb_gold_contract_selection_repo_open_trades": ".open_trades()" | kind=code-symbol | source=tests/test_orb_gold_contract_selection.py:L8 | neighbors=[Repo]
- "tests_test_orb_new_york_strategy_fakeprovider_get_candles": ".get_candles()" | kind=code-symbol | source=tests/test_orb_new_york_strategy.py:L20 | neighbors=[FakeProvider]
- "tests_test_orb_new_york_strategy_fakeprovider_get_current_tick": ".get_current_tick()" | kind=code-symbol | source=tests/test_orb_new_york_strategy.py:L24 | neighbors=[FakeProvider]
- "tests_test_orb_new_york_strategy_fakeprovider_init": ".__init__()" | kind=code-symbol | source=tests/test_orb_new_york_strategy.py:L16 | neighbors=[FakeProvider]
- "tests_test_orb_new_york_strategy_test_gold_contract_score_prefers_more_precise_half_percent_risk": "test_gold_contract_score_prefers_more_precise_half_percent_risk()" | kind=code-symbol | source=tests/test_orb_new_york_strategy.py:L149 | neighbors=[test_orb_new_york_strategy.py]

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-046.json

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
