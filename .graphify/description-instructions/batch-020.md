# Node Description Batch 21 of 56

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

- "backtesting_backtest_money_management_calculate_trade_pnl": "calculate_trade_pnl()" | kind=code-symbol | source=backtesting/backtest_money_management.py:L48 | neighbors=[backtest_money_management.py, apply_money_management(), Calcula la ganancia o pérdida monetaria…]
- "backtesting_trade_simulator_calculate_planned_rr": "calculate_planned_rr()" | kind=code-symbol | source=backtesting/trade_simulator.py:L83 | neighbors=[trade_simulator.py, Calcula el Risk:Reward teórico de la op…, simulate_trade()]
- "backtesting_trade_simulator_calculate_realized_rr": "calculate_realized_rr()" | kind=code-symbol | source=backtesting/trade_simulator.py:L8 | neighbors=[trade_simulator.py, Calcula el resultado real de una operac…, simulate_trade()]
- "backtesting_trade_simulator_simulate_trades": "simulate_trades()" | kind=code-symbol | source=backtesting/trade_simulator.py:L515 | neighbors=[trade_simulator.py, Alias de compatibilidad.      Permite…, simulate_all_trades()]
- "brokers_mt5_connection": "mt5_connection.py" | kind=code-symbol | source=brokers/mt5_connection.py:L1 | neighbors=[mt5_connector.py, Compatibilidad temporal. La implementac…, test_mt5_connection.py]
- "brokers_mt5_connector_mt5connector_get_account_info": ".get_account_info()" | kind=code-symbol | source=brokers/mt5_connector.py:L77 | neighbors=[MT5Connector, .is_connected(), Obtiene la información de la cuenta act…]
- "brokers_mt5_connector_mt5connector_is_connected": ".is_connected()" | kind=code-symbol | source=brokers/mt5_connector.py:L59 | neighbors=[MT5Connector, .get_account_info(), Verifica si MetaTrader 5 continúa conec…]
- "brokers_mt5_data_mt5dataprovider_get_current_tick": ".get_current_tick()" | kind=code-symbol | source=brokers/mt5_data.py:L370 | neighbors=[MT5DataProvider, ._ensure_connection(), .ensure_symbol()]
- "brokers_mt5_data_mt5dataprovider_get_symbol_info": ".get_symbol_info()" | kind=code-symbol | source=brokers/mt5_data.py:L251 | neighbors=[MT5DataProvider, ._ensure_connection(), .ensure_symbol()]
- "brokers_mt5_data_mt5dataprovider_prepare_symbols": ".prepare_symbols()" | kind=code-symbol | source=brokers/mt5_data.py:L243 | neighbors=[MT5DataProvider, .ensure_symbol(), Resuelve y activa una lista una sola ve…]
- "brokers_mt5_data_mt5dataprovider_resolve_symbol": ".resolve_symbol()" | kind=code-symbol | source=brokers/mt5_data.py:L133 | neighbors=[MT5DataProvider, .ensure_symbol(), ._ensure_connection()]
- "brokers_mt5_execution": "mt5_execution.py" | kind=code-symbol | source=brokers/mt5_execution.py:L1 | neighbors=[MT5ExecutionError, MT5ExecutionProvider, test_live_execution_helpers.py]
- "brokers_mt5_execution_back_mt5executionprovider_assert_demo_account": ".assert_demo_account()" | kind=code-symbol | source=brokers/mt5_execution.back.py:L50 | neighbors=[MT5ExecutionProvider, MT5ExecutionError, .account_info()]
- "brokers_mt5_execution_back_mt5executionprovider_check_result_dict": "._check_result_dict()" | kind=code-symbol | source=brokers/mt5_execution.back.py:L374 | neighbors=[MT5ExecutionProvider, .check_market_order(), .place_market_order()]
- "brokers_mt5_execution_back_mt5executionprovider_ensure_symbol": ".ensure_symbol()" | kind=code-symbol | source=brokers/mt5_execution.back.py:L826 | neighbors=[MT5ExecutionProvider, MT5ExecutionError, ._ensure()]
- "brokers_mt5_execution_back_mt5executionprovider_filling_name": "._filling_name()" | kind=code-symbol | source=brokers/mt5_execution.back.py:L740 | neighbors=[MT5ExecutionProvider, .check_market_order(), .place_market_order()]
- "brokers_mt5_execution_back_mt5executionprovider_symbol_filling_candidates": "._symbol_filling_candidates()" | kind=code-symbol | source=brokers/mt5_execution.back.py:L582 | neighbors=[MT5ExecutionProvider, ._allowed_fillings(), .symbol_spec()]
- "brokers_mt5_execution_mt5executionprovider_assert_demo_account": ".assert_demo_account()" | kind=code-symbol | source=brokers/mt5_execution.py:L66 | neighbors=[MT5ExecutionProvider, MT5ExecutionError, .account_info()]
- "brokers_mt5_execution_mt5executionprovider_get_position": ".get_position()" | kind=code-symbol | source=brokers/mt5_execution.py:L1452 | neighbors=[MT5ExecutionProvider, ._ensure(), .modify_position_stops()]
- "brokers_mt5_execution_mt5executionprovider_is_order_send_success": "._is_order_send_success()" | kind=code-symbol | source=brokers/mt5_execution.py:L652 | neighbors=[MT5ExecutionProvider, .place_market_order(), Determina éxito después de order_send().]
- "brokers_mt5_execution_mt5executionprovider_last_error_is_invalid_comment": "._last_error_is_invalid_comment()" | kind=code-symbol | source=brokers/mt5_execution.py:L464 | neighbors=[MT5ExecutionProvider, ._order_check_safe(), ._order_send_safe()]
- "brokers_mt5_execution_mt5executionprovider_list_history_deals": ".list_history_deals()" | kind=code-symbol | source=brokers/mt5_execution.py:L1298 | neighbors=[MT5ExecutionProvider, ._ensure(), Devuelve el historial de deals disponib…]
- "brokers_mt5_execution_mt5executionprovider_list_open_positions": ".list_open_positions()" | kind=code-symbol | source=brokers/mt5_execution.py:L1245 | neighbors=[MT5ExecutionProvider, ._ensure(), Devuelve un snapshot serializable de la…]
- "brokers_mt5_execution_mt5executionprovider_normalize_volume": ".normalize_volume()" | kind=code-symbol | source=brokers/mt5_execution.py:L847 | neighbors=[MT5ExecutionProvider, .calculate_volume(), MT5ExecutionError]
- "brokers_mt5_execution_mt5executionprovider_result_fields": "._result_fields()" | kind=code-symbol | source=brokers/mt5_execution.py:L589 | neighbors=[MT5ExecutionProvider, .place_market_order(), ._run_order_check_with_fallback()]
- "brokers_symbol_discovery_derivsymboldiscovery_get_all_synthetic_symbols": ".get_all_synthetic_symbols()" | kind=code-symbol | source=brokers/symbol_discovery.py:L120 | neighbors=[DerivSymbolDiscovery, .get_deriv_synthetics(), .get_tradeable_synthetics()]
- "brokers_symbol_discovery_looks_like_forex_name": "_looks_like_forex_name()" | kind=code-symbol | source=brokers/symbol_discovery.py:L33 | neighbors=[symbol_discovery.py, .is_forex_symbol(), Fallback para brokers con sufijos: EURU…]
- "config_symbol_policy_normalize_direction": "normalize_direction()" | kind=code-symbol | source=config/symbol_policy.py:L41 | neighbors=[symbol_policy.py, direction_policy_diagnostics(), is_direction_allowed()]
- "daemon_version": "daemon_version.py" | kind=code-symbol | source=daemon_version.py:L1 | neighbors=[main.py, realtime_dashboard.py, test_v53_runtime_telemetry_utf8.py]
- "dashboard_account_metrics_classify_close": "classify_close()" | kind=code-symbol | source=dashboard/account_metrics.py:L29 | neighbors=[account_metrics.py, build_account_payload(), _metadata()]
- "dashboard_account_metrics_strategy_name": "_strategy_name()" | kind=code-symbol | source=dashboard/account_metrics.py:L14 | neighbors=[account_metrics.py, build_account_payload(), _metadata()]
- "dashboard_realtime_dashboard_action_label_es": "_action_label_es()" | kind=code-symbol | source=dashboard/realtime_dashboard.py:L146 | neighbors=[realtime_dashboard.py, _humanize_code(), _enrich_recent_row()]
- "dashboard_realtime_dashboard_decision_label_es": "_decision_label_es()" | kind=code-symbol | source=dashboard/realtime_dashboard.py:L163 | neighbors=[realtime_dashboard.py, _humanize_code(), _enrich_recent_row()]
- "dashboard_realtime_dashboard_extract_signal": "_extract_signal()" | kind=code-symbol | source=dashboard/realtime_dashboard.py:L524 | neighbors=[realtime_dashboard.py, _extract_quality(), _first_dict()]
- "dashboard_realtime_dashboard_first_dict": "_first_dict()" | kind=code-symbol | source=dashboard/realtime_dashboard.py:L286 | neighbors=[realtime_dashboard.py, _extract_quality(), _extract_signal()]
- "dashboard_realtime_dashboard_position_owner": "_position_owner()" | kind=code-symbol | source=dashboard/realtime_dashboard.py:L375 | neighbors=[realtime_dashboard.py, _infer_symbol_profile(), ._refresh_open_positions_locked()]
- "dashboard_realtime_dashboard_quality_grade": "_quality_grade()" | kind=code-symbol | source=dashboard/realtime_dashboard.py:L293 | neighbors=[realtime_dashboard.py, _extract_quality(), _position_health()]
- "dashboard_realtime_dashboard_realtimedashboardservice_cached_account_payload": "._cached_account_payload()" | kind=code-symbol | source=dashboard/realtime_dashboard.py:L722 | neighbors=[RealtimeDashboardService, _json_safe(), ._refresh_account_locked()]
- "dashboard_realtime_dashboard_realtimedashboardservice_cached_instruments_payload": "._cached_instruments_payload()" | kind=code-symbol | source=dashboard/realtime_dashboard.py:L935 | neighbors=[RealtimeDashboardService, _json_safe(), ._refresh_selection_profiles_from_db_lo…]
- "dashboard_realtime_dashboard_realtimedashboardservice_invalidate_navigation_caches": "._invalidate_navigation_caches()" | kind=code-symbol | source=dashboard/realtime_dashboard.py:L963 | neighbors=[RealtimeDashboardService, .set_instrument_catalog(), .update_selected_symbols()]

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-020.json

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
