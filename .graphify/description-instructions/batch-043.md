# Node Description Batch 44 of 56

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

- "smc_trade_simulator_rationale_301": "Simula múltiples operaciones y agrega el resultado\r     de cada una al DataFrame" | kind=entity | source=strategy/smc/trade_simulator.py:L301 | neighbors=[simulate_trades()]
- "smc_trade_simulator_rationale_9": "Simula una operación utilizando las velas posteriores\r     al momento de entrada" | kind=entity | source=strategy/smc/trade_simulator.py:L9 | neighbors=[simulate_trade()]
- "tests_test_backtest_metric": "test_backtest_metric.py" | kind=code-symbol | source=tests/test_backtest_metric.py:L1 | neighbors=[main()]
- "tests_test_backtest_metric_main": "main()" | kind=code-symbol | source=tests/test_backtest_metric.py:L42 | neighbors=[test_backtest_metric.py]
- "tests_test_backtest_money_management_main": "main()" | kind=code-symbol | source=tests/test_backtest_money_management.py:L47 | neighbors=[test_backtest_money_management.py]
- "tests_test_backtest_storage_main": "main()" | kind=code-symbol | source=tests/test_backtest_storage.py:L15 | neighbors=[test_backtest_storage.py]
- "tests_test_chile_timezone_reporting_test_chile_timezone_conversion_winter_and_summer": "test_chile_timezone_conversion_winter_and_summer()" | kind=code-symbol | source=tests/test_chile_timezone_reporting.py:L6 | neighbors=[test_chile_timezone_reporting.py]
- "tests_test_choch_bos": "test_choch_bos.py" | kind=code-symbol | source=tests/test_choch_bos.py:L1 | neighbors=[main()]
- "tests_test_choch_bos_main": "main()" | kind=code-symbol | source=tests/test_choch_bos.py:L13 | neighbors=[test_choch_bos.py]
- "tests_test_confirmation_engine_test_default_adaptive_confirmation_threshold_is_80_percent": "test_default_adaptive_confirmation_threshold_is_80_percent()" | kind=code-symbol | source=tests/test_confirmation_engine.py:L98 | neighbors=[test_confirmation_engine.py]
- "tests_test_console_reporting_service_test_normal_mode_hides_no_signal": "test_normal_mode_hides_no_signal()" | kind=code-symbol | source=tests/test_console_reporting_service.py:L4 | neighbors=[test_console_reporting_service.py]
- "tests_test_console_reporting_service_test_summary_counts_actions": "test_summary_counts_actions()" | kind=code-symbol | source=tests/test_console_reporting_service.py:L19 | neighbors=[test_console_reporting_service.py]
- "tests_test_console_reporting_service_test_verbose_mode_prints_reason": "test_verbose_mode_prints_reason()" | kind=code-symbol | source=tests/test_console_reporting_service.py:L10 | neighbors=[test_console_reporting_service.py]
- "tests_test_daemon_break_even_live_brokerexecutor_get_position": ".get_position()" | kind=code-symbol | source=tests/test_daemon_break_even_live.py:L46 | neighbors=[BrokerExecutor]
- "tests_test_daemon_break_even_live_brokerexecutor_get_symbol_constraints": ".get_symbol_constraints()" | kind=code-symbol | source=tests/test_daemon_break_even_live.py:L43 | neighbors=[BrokerExecutor]
- "tests_test_daemon_break_even_live_brokerexecutor_init": ".__init__()" | kind=code-symbol | source=tests/test_daemon_break_even_live.py:L39 | neighbors=[BrokerExecutor]
- "tests_test_daemon_break_even_live_lifecyclemanager_init": ".__init__()" | kind=code-symbol | source=tests/test_daemon_break_even_live.py:L69 | neighbors=[LifecycleManager]
- "tests_test_daemon_break_even_live_repo_init": ".__init__()" | kind=code-symbol | source=tests/test_daemon_break_even_live.py:L7 | neighbors=[Repo]
- "tests_test_daemon_break_even_live_repo_open_trades": ".open_trades()" | kind=code-symbol | source=tests/test_daemon_break_even_live.py:L24 | neighbors=[Repo]
- "tests_test_daemon_break_even_live_repo_update_trade": ".update_trade()" | kind=code-symbol | source=tests/test_daemon_break_even_live.py:L27 | neighbors=[Repo]
- "tests_test_daemon_break_even_live_splitrepo_get_trade_by_execution_key": ".get_trade_by_execution_key()" | kind=code-symbol | source=tests/test_daemon_break_even_live.py:L157 | neighbors=[SplitRepo]
- "tests_test_daemon_break_even_live_splitrepo_init": ".__init__()" | kind=code-symbol | source=tests/test_daemon_break_even_live.py:L143 | neighbors=[SplitRepo]
- "tests_test_daemon_break_even_live_tradeexecutor_init": ".__init__()" | kind=code-symbol | source=tests/test_daemon_break_even_live.py:L57 | neighbors=[TradeExecutor]
- "tests_test_daemon_break_even_live_tradeexecutor_move_stop_loss": ".move_stop_loss()" | kind=code-symbol | source=tests/test_daemon_break_even_live.py:L61 | neighbors=[TradeExecutor]
- "tests_test_daemon_progress_engine_process_symbol": ".process_symbol()" | kind=code-symbol | source=tests/test_daemon_progress.py:L12 | neighbors=[Engine]
- "tests_test_daemon_progress_repo_sync_closed_mt5_trades": ".sync_closed_mt5_trades()" | kind=code-symbol | source=tests/test_daemon_progress.py:L7 | neighbors=[Repo]
- "tests_test_daemon_risk_target_policy_analyzer_analyze_symbol": ".analyze_symbol()" | kind=code-symbol | source=tests/test_daemon_risk_target_policy.py:L55 | neighbors=[Analyzer]
- "tests_test_daemon_risk_target_policy_executor_assert_demo_account": ".assert_demo_account()" | kind=code-symbol | source=tests/test_daemon_risk_target_policy.py:L34 | neighbors=[Executor]
- "tests_test_daemon_risk_target_policy_executor_calculate_volume": ".calculate_volume()" | kind=code-symbol | source=tests/test_daemon_risk_target_policy.py:L45 | neighbors=[Executor]
- "tests_test_daemon_risk_target_policy_executor_normalize_market_stops": ".normalize_market_stops()" | kind=code-symbol | source=tests/test_daemon_risk_target_policy.py:L37 | neighbors=[Executor]
- "tests_test_daemon_risk_target_policy_provider_ensure_symbol": ".ensure_symbol()" | kind=code-symbol | source=tests/test_daemon_risk_target_policy.py:L26 | neighbors=[Provider]
- "tests_test_daemon_risk_target_policy_provider_get_current_tick": ".get_current_tick()" | kind=code-symbol | source=tests/test_daemon_risk_target_policy.py:L29 | neighbors=[Provider]
- "tests_test_daemon_risk_target_policy_provider_resolve_symbol": ".resolve_symbol()" | kind=code-symbol | source=tests/test_daemon_risk_target_policy.py:L23 | neighbors=[Provider]
- "tests_test_daemon_risk_target_policy_repo_get_trade_by_execution_key": ".get_trade_by_execution_key()" | kind=code-symbol | source=tests/test_daemon_risk_target_policy.py:L10 | neighbors=[Repo]
- "tests_test_daemon_risk_target_policy_repo_open_trades": ".open_trades()" | kind=code-symbol | source=tests/test_daemon_risk_target_policy.py:L13 | neighbors=[Repo]
- "tests_test_daemon_risk_target_policy_repo_save_account_snapshot": ".save_account_snapshot()" | kind=code-symbol | source=tests/test_daemon_risk_target_policy.py:L16 | neighbors=[Repo]
- "tests_test_daemon_risk_target_policy_repo_save_signal_once": ".save_signal_once()" | kind=code-symbol | source=tests/test_daemon_risk_target_policy.py:L7 | neighbors=[Repo]
- "tests_test_daemon_runner_extension_positionexecutor_get_position": ".get_position()" | kind=code-symbol | source=tests/test_daemon_runner_extension.py:L34 | neighbors=[PositionExecutor]
- "tests_test_daemon_runner_extension_positionexecutor_get_symbol_constraints": ".get_symbol_constraints()" | kind=code-symbol | source=tests/test_daemon_runner_extension.py:L37 | neighbors=[PositionExecutor]
- "tests_test_daemon_runner_extension_positionexecutor_init": ".__init__()" | kind=code-symbol | source=tests/test_daemon_runner_extension.py:L31 | neighbors=[PositionExecutor]

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-043.json

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
