# Node Description Batch 28 of 56

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

- "tests_test_v73_forex_progressive_runner_test_forex_at_tp3_if_continuation_protects_2_5r_and_runs_to_tp4": "test_forex_at_tp3_if_continuation_protects_2_5r_and_runs_to_tp4()" | kind=code-symbol | source=tests/test_v73_forex_progressive_runner.py:L141 | neighbors=[test_v73_forex_progressive_runner.py, _engine(), _trade()]
- "tests_test_v73_forex_progressive_runner_test_forex_at_tp3_without_continuation_closes_after_profit_protection": "test_forex_at_tp3_without_continuation_closes_after_profit_protection()" | kind=code-symbol | source=tests/test_v73_forex_progressive_runner.py:L167 | neighbors=[test_v73_forex_progressive_runner.py, _engine(), _trade()]
- "tests_test_v75_orb_entry_vs_now": "test_v75_orb_entry_vs_now.py" | kind=code-symbol | source=tests/test_v75_orb_entry_vs_now.py:L1 | neighbors=[test_orb_current_view_normalizes_waitin…, test_orb_is_no_longer_skipped_from_curr…, test_refresh_routes_open_orb_trade_to_o…]
- "tests_test_v78_account_no_horizontal_scroll": "test_v78_account_no_horizontal_scroll.py" | kind=code-symbol | source=tests/test_v78_account_no_horizontal_scroll.py:L1 | neighbors=[test_account_audit_column_no_longer_for…, test_account_columns_fit_full_width(), test_account_table_uses_fixed_layout_an…]
- "tests_test_v85_orb_correlation_synthetic_parity_test_gold_and_wall_street_are_not_part_of_sp500_nasdaq_guard": "test_gold_and_wall_street_are_not_part_of_sp500_nasdaq_guard()" | kind=code-symbol | source=tests/test_v85_orb_correlation_synthetic_parity.py:L50 | neighbors=[test_v85_orb_correlation_synthetic_pari…, _engine_with_open_trade(), _orb_trade()]
- "tests_test_v85_orb_correlation_synthetic_parity_test_persisted_protective_stop_also_proves_break_even": "test_persisted_protective_stop_also_proves_break_even()" | kind=code-symbol | source=tests/test_v85_orb_correlation_synthetic_parity.py:L45 | neighbors=[test_v85_orb_correlation_synthetic_pari…, _engine_with_open_trade(), _orb_trade()]
- "tests_test_v85_orb_correlation_synthetic_parity_test_sp500_is_allowed_after_nasdaq_break_even_is_confirmed": "test_sp500_is_allowed_after_nasdaq_break_even_is_confirmed()" | kind=code-symbol | source=tests/test_v85_orb_correlation_synthetic_parity.py:L38 | neighbors=[test_v85_orb_correlation_synthetic_pari…, _engine_with_open_trade(), _orb_trade()]
- "tests_test_v85_orb_correlation_synthetic_parity_test_sp500_is_blocked_while_nasdaq_risk_is_not_protected": "test_sp500_is_blocked_while_nasdaq_risk_is_not_protected()" | kind=code-symbol | source=tests/test_v85_orb_correlation_synthetic_parity.py:L31 | neighbors=[test_v85_orb_correlation_synthetic_pari…, _engine_with_open_trade(), _orb_trade()]
- "tests_test_v90_multibot_single_instance": "test_v90_multibot_single_instance.py" | kind=code-symbol | source=tests/test_v90_multibot_single_instance.py:L1 | neighbors=[main.py, test_lock_can_be_acquired_after_clean_r…, test_second_coordinator_is_rejected_bef…]
- "tests_test_v91_legacy_multibot_guard": "test_v91_legacy_multibot_guard.py" | kind=code-symbol | source=tests/test_v91_legacy_multibot_guard.py:L1 | neighbors=[main.py, test_legacy_coordinator_aborts_after_re…, test_without_legacy_coordinator_guard_r…]
- "tests_test_v95_analysis_invalidation_exit_test_valid_current_analysis_resets_streak_and_never_closes": "test_valid_current_analysis_resets_streak_and_never_closes()" | kind=code-symbol | source=tests/test_v95_analysis_invalidation_exit.py:L102 | neighbors=[test_v95_analysis_invalidation_exit.py, engine_with_view(), old_trade()]
- "trade_lifecycle_manager_tradelifecyclemanager_process_signal": ".process_signal()" | kind=code-symbol | source=trade_lifecycle_manager.py:L346 | neighbors=[TradeLifecycleManager, .create_from_signal(), .execute()]
- "trade_lifecycle_manager_tradelifecyclemanager_process_signal_with_executor": ".process_signal_with_executor()" | kind=code-symbol | source=trade_lifecycle_manager.py:L442 | neighbors=[TradeLifecycleManager, .create_from_signal(), .execute_with_executor()]
- "trade_lifecycle_manager_tradelifecyclemanager_result_from_exit_reason": "._result_from_exit_reason()" | kind=code-symbol | source=trade_lifecycle_manager.py:L606 | neighbors=[TradeLifecycleManager, .close_execution(), .monitor_execution()]
- "trade_lifecycle_manager_tradelifecyclemanager_state_from_exit_reason": "._state_from_exit_reason()" | kind=code-symbol | source=trade_lifecycle_manager.py:L616 | neighbors=[TradeLifecycleManager, .close_execution(), .monitor_execution()]
- "trade_outcome_policy_is_break_even_rr": "is_break_even_rr()" | kind=code-symbol | source=trade_outcome_policy.py:L16 | neighbors=[trade_outcome_policy.py, decisive_outcome(), safe_float()]
- "trade_outcome_policy_safe_float": "safe_float()" | kind=code-symbol | source=trade_outcome_policy.py:L9 | neighbors=[trade_outcome_policy.py, decisive_outcome(), is_break_even_rr()]
- "abc": "ABC" | kind=code-symbol | neighbors=[trade_executor.py, TradeExecutor]
- "app_main_analyze_historical": "analyze_historical()" | kind=code-symbol | source=app/main.py:L188 | neighbors=[main.py, main()]
- "app_main_collect_once": "collect_once()" | kind=code-symbol | source=app/main.py:L110 | neighbors=[main.py, run_collector()]
- "app_main_normalize_categories": "_normalize_categories()" | kind=code-symbol | source=app/main.py:L54 | neighbors=[main.py, _resolve_symbols()]
- "app_main_require_symbol_for_offline_mode": "_require_symbol_for_offline_mode()" | kind=code-symbol | source=app/main.py:L100 | neighbors=[main.py, main()]
- "app_main_run_demo_bot": "run_demo_bot()" | kind=code-symbol | source=app/main.py:L284 | neighbors=[main.py, main()]
- "app_main_run_demo_preflight": "run_demo_preflight()" | kind=code-symbol | source=app/main.py:L673 | neighbors=[main.py, main()]
- "app_main_run_live_demo_smoke": "run_live_demo_smoke()" | kind=code-symbol | source=app/main.py:L719 | neighbors=[main.py, main()]
- "app_main_run_live_paper": "run_live_paper()" | kind=code-symbol | source=app/main.py:L545 | neighbors=[main.py, main()]
- "app_main_run_reset_database": "run_reset_database()" | kind=code-symbol | source=app/main.py:L2278 | neighbors=[main.py, main()]
- "app_main_selection_profile_for_bot": "_selection_profile_for_bot()" | kind=code-symbol | source=app/main.py:L995 | neighbors=[main.py, _resolve_symbols_for_profile_shared()]
- "app_main_validate_timeframes": "_validate_timeframes()" | kind=code-symbol | source=app/main.py:L43 | neighbors=[main.py, main()]
- "backtest_backtest_metric_calculate_backtest_metrics": "calculate_backtest_metrics()" | kind=code-symbol | source=strategy/backtest/backtest_metric.py:L9 | neighbors=[backtest_metric.py, Calcula métricas completas de un backte…]
- "backtesting_backtest_money_management_get_money_management_summary": "get_money_management_summary()" | kind=code-symbol | source=backtesting/backtest_money_management.py:L398 | neighbors=[backtest_money_management.py, Genera estadísticas financieras     de…]
- "backtesting_backtest_money_management_save_money_management_results": "save_money_management_results()" | kind=code-symbol | source=backtesting/backtest_money_management.py:L655 | neighbors=[backtest_money_management.py, Guarda los resultados financieros     …]
- "backtesting_backtest_pipeline_run_full_backtest_pipeline": "run_full_backtest_pipeline()" | kind=code-symbol | source=backtesting/backtest_pipeline.py:L15 | neighbors=[backtest_pipeline.py, Ejecuta el flujo completo histórico -> …]
- "backtesting_backtest_storage_persist_money_management_results": "persist_money_management_results()" | kind=code-symbol | source=backtesting/backtest_storage.py:L10 | neighbors=[backtest_storage.py, Importa el CSV financiero a SQLite y ge…]
- "backtesting_backtest_storage_rationale_18": "Importa el CSV financiero a SQLite y genera/actualiza el Excel." | kind=entity | source=backtesting/backtest_storage.py:L18 | neighbors=[persist_money_management_results(), TradingRepository]
- "backtesting_trade_simulator_get_backtest_summary": "get_backtest_summary()" | kind=code-symbol | source=backtesting/trade_simulator.py:L541 | neighbors=[trade_simulator.py, Genera un resumen estadístico     de l…]
- "brokers_mt5_connection_rationale_1": "Compatibilidad temporal. La implementación oficial del conector vive en brokers." | kind=entity | source=brokers/mt5_connection.py:L1 | neighbors=[mt5_connection.py, MT5Connector]
- "brokers_mt5_connector_mt5connector_connect": ".connect()" | kind=code-symbol | source=brokers/mt5_connector.py:L12 | neighbors=[MT5Connector, Inicializa la conexión con MetaTrader 5.]
- "brokers_mt5_connector_mt5connector_disconnect": ".disconnect()" | kind=code-symbol | source=brokers/mt5_connector.py:L46 | neighbors=[MT5Connector, Cierra la conexión con MetaTrader 5.]
- "brokers_mt5_data_mt5dataprovider_connect": ".connect()" | kind=code-symbol | source=brokers/mt5_data.py:L63 | neighbors=[MT5DataProvider, ._ensure_connection()]

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-027.json

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
