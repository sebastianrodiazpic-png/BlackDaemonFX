# Node Description Batch 46 of 56

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

- "tests_test_demo_daemon_integration_executor_get_position": ".get_position()" | kind=code-symbol | source=tests/test_demo_daemon_integration.py:L139 | neighbors=[Executor]
- "tests_test_demo_daemon_integration_executor_normalize_market_stops": ".normalize_market_stops()" | kind=code-symbol | source=tests/test_demo_daemon_integration.py:L125 | neighbors=[Executor]
- "tests_test_demo_daemon_integration_fakeengine_process_symbols": ".process_symbols()" | kind=code-symbol | source=tests/test_demo_daemon_integration.py:L40 | neighbors=[FakeEngine]
- "tests_test_demo_daemon_integration_fakelifecyclemanager_create_from_signal": ".create_from_signal()" | kind=code-symbol | source=tests/test_demo_daemon_integration.py:L64 | neighbors=[FakeLifecycleManager]
- "tests_test_demo_daemon_integration_fakelifecyclemanager_execute_with_executor": ".execute_with_executor()" | kind=code-symbol | source=tests/test_demo_daemon_integration.py:L76 | neighbors=[FakeLifecycleManager]
- "tests_test_demo_daemon_integration_fakereporting_export_now": ".export_now()" | kind=code-symbol | source=tests/test_demo_daemon_integration.py:L35 | neighbors=[FakeReporting]
- "tests_test_demo_daemon_integration_fakereporting_init": ".__init__()" | kind=code-symbol | source=tests/test_demo_daemon_integration.py:L32 | neighbors=[FakeReporting]
- "tests_test_demo_daemon_integration_fakerepository_init": ".__init__()" | kind=code-symbol | source=tests/test_demo_daemon_integration.py:L23 | neighbors=[FakeRepository]
- "tests_test_demo_daemon_integration_fakerepository_sync_closed_mt5_trades": ".sync_closed_mt5_trades()" | kind=code-symbol | source=tests/test_demo_daemon_integration.py:L26 | neighbors=[FakeRepository]
- "tests_test_demo_daemon_integration_provider_ensure_symbol": ".ensure_symbol()" | kind=code-symbol | source=tests/test_demo_daemon_integration.py:L114 | neighbors=[Provider]
- "tests_test_demo_daemon_integration_provider_get_current_tick": ".get_current_tick()" | kind=code-symbol | source=tests/test_demo_daemon_integration.py:L117 | neighbors=[Provider]
- "tests_test_demo_daemon_integration_provider_resolve_symbol": ".resolve_symbol()" | kind=code-symbol | source=tests/test_demo_daemon_integration.py:L111 | neighbors=[Provider]
- "tests_test_demo_daemon_integration_test_reporting_prefers_explicit_execution_key": "test_reporting_prefers_explicit_execution_key()" | kind=code-symbol | source=tests/test_demo_daemon_integration.py:L9 | neighbors=[test_demo_daemon_integration.py]
- "tests_test_divergence_confirmation_test_divergence_is_optional_confluence_not_a_mandatory_confirmation": "test_divergence_is_optional_confluence_not_a_mandatory_confirmation()" | kind=code-symbol | source=tests/test_divergence_confirmation.py:L36 | neighbors=[test_divergence_confirmation.py]
- "tests_test_entry_confirmation": "test_entry_confirmation.py" | kind=code-symbol | source=tests/test_entry_confirmation.py:L1 | neighbors=[main()]
- "tests_test_entry_confirmation_main": "main()" | kind=code-symbol | source=tests/test_entry_confirmation.py:L27 | neighbors=[test_entry_confirmation.py]
- "tests_test_execution_preflight_service_fakeprovider_account_info": ".account_info()" | kind=code-symbol | source=tests/test_execution_preflight_service.py:L15 | neighbors=[FakeProvider]
- "tests_test_execution_preflight_service_fakeprovider_ensure_symbol": ".ensure_symbol()" | kind=code-symbol | source=tests/test_execution_preflight_service.py:L31 | neighbors=[FakeProvider]
- "tests_test_execution_preflight_service_fakeprovider_get_symbol_constraints": ".get_symbol_constraints()" | kind=code-symbol | source=tests/test_execution_preflight_service.py:L34 | neighbors=[FakeProvider]
- "tests_test_execution_preflight_service_fakerepository_init": ".__init__()" | kind=code-symbol | source=tests/test_execution_preflight_service.py:L7 | neighbors=[FakeRepository]
- "tests_test_execution_preflight_service_fakerepository_save_account_snapshot": ".save_account_snapshot()" | kind=code-symbol | source=tests/test_execution_preflight_service.py:L10 | neighbors=[FakeRepository]
- "tests_test_full_backtest_pipeline_main": "main()" | kind=code-symbol | source=tests/test_full_backtest_pipeline.py:L4 | neighbors=[test_full_backtest_pipeline.py]
- "tests_test_liquidity": "test_liquidity.py" | kind=code-symbol | source=tests/test_liquidity.py:L1 | neighbors=[main()]
- "tests_test_liquidity_main": "main()" | kind=code-symbol | source=tests/test_liquidity.py:L13 | neighbors=[test_liquidity.py]
- "tests_test_liquidity_sweeps": "test_liquidity_sweeps.py" | kind=code-symbol | source=tests/test_liquidity_sweeps.py:L1 | neighbors=[main()]
- "tests_test_liquidity_sweeps_main": "main()" | kind=code-symbol | source=tests/test_liquidity_sweeps.py:L14 | neighbors=[test_liquidity_sweeps.py]
- "tests_test_live_demo_smoke_stops_executor_get_position": ".get_position()" | kind=code-symbol | source=tests/test_live_demo_smoke_stops.py:L50 | neighbors=[_Executor]
- "tests_test_live_demo_smoke_stops_executor_init": ".__init__()" | kind=code-symbol | source=tests/test_live_demo_smoke_stops.py:L47 | neighbors=[_Executor]
- "tests_test_live_demo_smoke_stops_lifecyclemanager_close_execution": ".close_execution()" | kind=code-symbol | source=tests/test_live_demo_smoke_stops.py:L67 | neighbors=[_LifecycleManager]
- "tests_test_live_demo_smoke_stops_lifecyclemanager_init": ".__init__()" | kind=code-symbol | source=tests/test_live_demo_smoke_stops.py:L60 | neighbors=[_LifecycleManager]
- "tests_test_live_demo_smoke_stops_provider_assert_demo_account": ".assert_demo_account()" | kind=code-symbol | source=tests/test_live_demo_smoke_stops.py:L14 | neighbors=[_Provider]
- "tests_test_live_demo_smoke_stops_provider_get_symbol_constraints": ".get_symbol_constraints()" | kind=code-symbol | source=tests/test_live_demo_smoke_stops.py:L23 | neighbors=[_Provider]
- "tests_test_live_demo_smoke_stops_provider_normalize_market_stops": ".normalize_market_stops()" | kind=code-symbol | source=tests/test_live_demo_smoke_stops.py:L33 | neighbors=[_Provider]
- "tests_test_live_demo_smoke_stops_provider_normalize_volume": ".normalize_volume()" | kind=code-symbol | source=tests/test_live_demo_smoke_stops.py:L30 | neighbors=[_Provider]
- "tests_test_live_demo_smoke_stops_repository_get_trade_by_execution_key": ".get_trade_by_execution_key()" | kind=code-symbol | source=tests/test_live_demo_smoke_stops.py:L72 | neighbors=[_Repository]
- "tests_test_live_end_to_end_dry_run_fakeanalyzer_analyze_symbol": ".analyze_symbol()" | kind=code-symbol | source=tests/test_live_end_to_end_dry_run.py:L90 | neighbors=[FakeAnalyzer]
- "tests_test_live_end_to_end_dry_run_fakeexecutor_assert_demo_account": ".assert_demo_account()" | kind=code-symbol | source=tests/test_live_end_to_end_dry_run.py:L43 | neighbors=[FakeExecutor]
- "tests_test_live_end_to_end_dry_run_fakeexecutor_calculate_volume": ".calculate_volume()" | kind=code-symbol | source=tests/test_live_end_to_end_dry_run.py:L57 | neighbors=[FakeExecutor]
- "tests_test_live_end_to_end_dry_run_fakeexecutor_check_market_order": ".check_market_order()" | kind=code-symbol | source=tests/test_live_end_to_end_dry_run.py:L71 | neighbors=[FakeExecutor]
- "tests_test_live_end_to_end_dry_run_fakeexecutor_init": ".__init__()" | kind=code-symbol | source=tests/test_live_end_to_end_dry_run.py:L39 | neighbors=[FakeExecutor]

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-045.json

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
