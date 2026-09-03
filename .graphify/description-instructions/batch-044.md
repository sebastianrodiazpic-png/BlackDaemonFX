# Node Description Batch 45 of 56

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

- "tests_test_daemon_runner_extension_provider_get_candles": ".get_candles()" | kind=code-symbol | source=tests/test_daemon_runner_extension.py:L20 | neighbors=[Provider]
- "tests_test_daemon_runner_extension_repo_init": ".__init__()" | kind=code-symbol | source=tests/test_daemon_runner_extension.py:L12 | neighbors=[Repo]
- "tests_test_daemon_runner_extension_repo_update_trade": ".update_trade()" | kind=code-symbol | source=tests/test_daemon_runner_extension.py:L15 | neighbors=[Repo]
- "tests_test_daemon_runner_extension_tradeexecutor_close_position": ".close_position()" | kind=code-symbol | source=tests/test_daemon_runner_extension.py:L53 | neighbors=[TradeExecutor]
- "tests_test_daemon_runner_extension_tradeexecutor_init": ".__init__()" | kind=code-symbol | source=tests/test_daemon_runner_extension.py:L42 | neighbors=[TradeExecutor]
- "tests_test_daemon_runner_extension_tradeexecutor_move_stop_loss": ".move_stop_loss()" | kind=code-symbol | source=tests/test_daemon_runner_extension.py:L47 | neighbors=[TradeExecutor]
- "tests_test_daemon_single_entry_fallback_analyzer_analyze_symbol": ".analyze_symbol()" | kind=code-symbol | source=tests/test_daemon_single_entry_fallback.py:L28 | neighbors=[Analyzer]
- "tests_test_daemon_single_entry_fallback_fallbackexecutor_assert_demo_account": ".assert_demo_account()" | kind=code-symbol | source=tests/test_daemon_single_entry_fallback.py:L46 | neighbors=[FallbackExecutor]
- "tests_test_daemon_single_entry_fallback_fallbackexecutor_calculate_volume": ".calculate_volume()" | kind=code-symbol | source=tests/test_daemon_single_entry_fallback.py:L56 | neighbors=[FallbackExecutor]
- "tests_test_daemon_single_entry_fallback_fallbackexecutor_init": ".__init__()" | kind=code-symbol | source=tests/test_daemon_single_entry_fallback.py:L44 | neighbors=[FallbackExecutor]
- "tests_test_daemon_single_entry_fallback_fallbackexecutor_normalize_market_stops": ".normalize_market_stops()" | kind=code-symbol | source=tests/test_daemon_single_entry_fallback.py:L48 | neighbors=[FallbackExecutor]
- "tests_test_daemon_single_entry_fallback_provider_ensure_symbol": ".ensure_symbol()" | kind=code-symbol | source=tests/test_daemon_single_entry_fallback.py:L21 | neighbors=[Provider]
- "tests_test_daemon_single_entry_fallback_provider_get_current_tick": ".get_current_tick()" | kind=code-symbol | source=tests/test_daemon_single_entry_fallback.py:L23 | neighbors=[Provider]
- "tests_test_daemon_single_entry_fallback_provider_resolve_symbol": ".resolve_symbol()" | kind=code-symbol | source=tests/test_daemon_single_entry_fallback.py:L19 | neighbors=[Provider]
- "tests_test_daemon_single_entry_fallback_repo_get_trade_by_execution_key": ".get_trade_by_execution_key()" | kind=code-symbol | source=tests/test_daemon_single_entry_fallback.py:L9 | neighbors=[Repo]
- "tests_test_daemon_single_entry_fallback_repo_open_trades": ".open_trades()" | kind=code-symbol | source=tests/test_daemon_single_entry_fallback.py:L11 | neighbors=[Repo]
- "tests_test_daemon_single_entry_fallback_repo_save_account_snapshot": ".save_account_snapshot()" | kind=code-symbol | source=tests/test_daemon_single_entry_fallback.py:L13 | neighbors=[Repo]
- "tests_test_daemon_single_entry_fallback_repo_save_signal_once": ".save_signal_once()" | kind=code-symbol | source=tests/test_daemon_single_entry_fallback.py:L7 | neighbors=[Repo]
- "tests_test_daemon_split_risk_management_analyzer_analyze_symbol": ".analyze_symbol()" | kind=code-symbol | source=tests/test_daemon_split_risk_management.py:L52 | neighbors=[Analyzer]
- "tests_test_daemon_split_risk_management_executor_assert_demo_account": ".assert_demo_account()" | kind=code-symbol | source=tests/test_daemon_split_risk_management.py:L34 | neighbors=[Executor]
- "tests_test_daemon_split_risk_management_executor_calculate_volume": ".calculate_volume()" | kind=code-symbol | source=tests/test_daemon_split_risk_management.py:L46 | neighbors=[Executor]
- "tests_test_daemon_split_risk_management_executor_normalize_market_stops": ".normalize_market_stops()" | kind=code-symbol | source=tests/test_daemon_split_risk_management.py:L37 | neighbors=[Executor]
- "tests_test_daemon_split_risk_management_provider_ensure_symbol": ".ensure_symbol()" | kind=code-symbol | source=tests/test_daemon_split_risk_management.py:L26 | neighbors=[Provider]
- "tests_test_daemon_split_risk_management_provider_get_current_tick": ".get_current_tick()" | kind=code-symbol | source=tests/test_daemon_split_risk_management.py:L29 | neighbors=[Provider]
- "tests_test_daemon_split_risk_management_provider_resolve_symbol": ".resolve_symbol()" | kind=code-symbol | source=tests/test_daemon_split_risk_management.py:L23 | neighbors=[Provider]
- "tests_test_daemon_split_risk_management_repo_get_trade_by_execution_key": ".get_trade_by_execution_key()" | kind=code-symbol | source=tests/test_daemon_split_risk_management.py:L10 | neighbors=[Repo]
- "tests_test_daemon_split_risk_management_repo_open_trades": ".open_trades()" | kind=code-symbol | source=tests/test_daemon_split_risk_management.py:L13 | neighbors=[Repo]
- "tests_test_daemon_split_risk_management_repo_save_account_snapshot": ".save_account_snapshot()" | kind=code-symbol | source=tests/test_daemon_split_risk_management.py:L16 | neighbors=[Repo]
- "tests_test_daemon_split_risk_management_repo_save_signal_once": ".save_signal_once()" | kind=code-symbol | source=tests/test_daemon_split_risk_management.py:L7 | neighbors=[Repo]
- "tests_test_demo_daemon_integration_analyzer_analyze_symbol": ".analyze_symbol()" | kind=code-symbol | source=tests/test_demo_daemon_integration.py:L149 | neighbors=[Analyzer]
- "tests_test_demo_daemon_integration_executionrepo_get_trade_by_execution_key": ".get_trade_by_execution_key()" | kind=code-symbol | source=tests/test_demo_daemon_integration.py:L95 | neighbors=[ExecutionRepo]
- "tests_test_demo_daemon_integration_executionrepo_init": ".__init__()" | kind=code-symbol | source=tests/test_demo_daemon_integration.py:L86 | neighbors=[ExecutionRepo]
- "tests_test_demo_daemon_integration_executionrepo_open_trades": ".open_trades()" | kind=code-symbol | source=tests/test_demo_daemon_integration.py:L98 | neighbors=[ExecutionRepo]
- "tests_test_demo_daemon_integration_executionrepo_save_account_snapshot": ".save_account_snapshot()" | kind=code-symbol | source=tests/test_demo_daemon_integration.py:L101 | neighbors=[ExecutionRepo]
- "tests_test_demo_daemon_integration_executionrepo_save_signal_once": ".save_signal_once()" | kind=code-symbol | source=tests/test_demo_daemon_integration.py:L91 | neighbors=[ExecutionRepo]
- "tests_test_demo_daemon_integration_executionrepo_sync_closed_mt5_trades": ".sync_closed_mt5_trades()" | kind=code-symbol | source=tests/test_demo_daemon_integration.py:L104 | neighbors=[ExecutionRepo]
- "tests_test_demo_daemon_integration_executor_assert_demo_account": ".assert_demo_account()" | kind=code-symbol | source=tests/test_demo_daemon_integration.py:L122 | neighbors=[Executor]
- "tests_test_demo_daemon_integration_executor_calculate_risk_amount": ".calculate_risk_amount()" | kind=code-symbol | source=tests/test_demo_daemon_integration.py:L144 | neighbors=[Executor]
- "tests_test_demo_daemon_integration_executor_calculate_volume": ".calculate_volume()" | kind=code-symbol | source=tests/test_demo_daemon_integration.py:L133 | neighbors=[Executor]
- "tests_test_demo_daemon_integration_executor_check_market_order": ".check_market_order()" | kind=code-symbol | source=tests/test_demo_daemon_integration.py:L136 | neighbors=[Executor]

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-044.json

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
