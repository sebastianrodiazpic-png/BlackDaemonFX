# Node Description Batch 29 of 56

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
LANGUAGE: each entry has a `lang=` marker giving the language of its source.
Write that entry's description in EXACTLY that language. Do not translate to
a single common language — match each node's source language individually.
No marketing language.
Respond ONLY with a JSON object mapping each node id (as a string) to its
one-sentence description — no prose, no markdown fences.

- "brokers_mt5_data_mt5dataprovider_get_last_closed_candle": ".get_last_closed_candle()" | kind=code-symbol | source=brokers/mt5_data.py:L345 | neighbors=[MT5DataProvider, .get_candles()] | lang=en
- "brokers_mt5_data_mt5dataprovider_get_timeframe": ".get_timeframe()" | kind=code-symbol | source=brokers/mt5_data.py:L81 | neighbors=[MT5DataProvider, .get_candles()] | lang=en
- "brokers_mt5_data_mt5dataprovider_init": ".__init__()" | kind=code-symbol | source=brokers/mt5_data.py:L41 | neighbors=[MT5DataProvider, Inicializa el proveedor de datos.      …] | lang=en
- "brokers_mt5_data_mt5dataprovider_search_symbols": ".search_symbols()" | kind=code-symbol | source=brokers/mt5_data.py:L100 | neighbors=[MT5DataProvider, ._ensure_connection()] | lang=en
- "brokers_mt5_data_rationale_244": "Resuelve y activa una lista una sola vez antes del bucle del demonio." | kind=entity | source=brokers/mt5_data.py:L244 | neighbors=[MT5Connector, .prepare_symbols()] | lang=es
- "brokers_mt5_data_rationale_42": "Inicializa el proveedor de datos.          Si no se entrega un conector, se crea" | kind=entity | source=brokers/mt5_data.py:L42 | neighbors=[MT5Connector, .__init__()] | lang=es
- "brokers_mt5_data_rationale_9": "Proveedor de datos históricos y en tiempo real     desde MetaTrader 5." | kind=entity | source=brokers/mt5_data.py:L9 | neighbors=[MT5Connector, MT5DataProvider] | lang=en
- "brokers_mt5_execution_back": "mt5_execution.back.py" | kind=code-symbol | source=brokers/mt5_execution.back.py:L1 | neighbors=[MT5ExecutionError, MT5ExecutionProvider] | lang=en
- "brokers_mt5_execution_back_mt5executionprovider_find_position_ticket": ".find_position_ticket()" | kind=code-symbol | source=brokers/mt5_execution.back.py:L748 | neighbors=[MT5ExecutionProvider, ._ensure()] | lang=en
- "brokers_mt5_execution_back_mt5executionprovider_get_position": ".get_position()" | kind=code-symbol | source=brokers/mt5_execution.back.py:L794 | neighbors=[MT5ExecutionProvider, ._ensure()] | lang=en
- "brokers_mt5_execution_back_mt5executionprovider_history_for_position": ".history_for_position()" | kind=code-symbol | source=brokers/mt5_execution.back.py:L806 | neighbors=[MT5ExecutionProvider, ._ensure()] | lang=en
- "brokers_mt5_execution_back_mt5executionprovider_position_ticket_from_deal": ".position_ticket_from_deal()" | kind=code-symbol | source=brokers/mt5_execution.back.py:L775 | neighbors=[MT5ExecutionProvider, ._ensure()] | lang=en
- "brokers_mt5_execution_back_mt5executionprovider_price_decimals": "._price_decimals()" | kind=code-symbol | source=brokers/mt5_execution.back.py:L213 | neighbors=[MT5ExecutionProvider, ._normalize_price()] | lang=en
- "brokers_mt5_execution_mt5executionprovider_find_position_ticket": ".find_position_ticket()" | kind=code-symbol | source=brokers/mt5_execution.py:L1389 | neighbors=[MT5ExecutionProvider, ._ensure()] | lang=en
- "brokers_mt5_execution_mt5executionprovider_history_for_position": ".history_for_position()" | kind=code-symbol | source=brokers/mt5_execution.py:L1467 | neighbors=[MT5ExecutionProvider, ._ensure()] | lang=en
- "brokers_mt5_execution_mt5executionprovider_position_ticket_from_deal": ".position_ticket_from_deal()" | kind=code-symbol | source=brokers/mt5_execution.py:L1428 | neighbors=[MT5ExecutionProvider, ._ensure()] | lang=en
- "brokers_mt5_trade_executor": "mt5_trade_executor.py" | kind=code-symbol | source=brokers/mt5_trade_executor.py:L1 | neighbors=[MT5TradeExecutor, live_demo_smoke_test_service.py] | lang=en
- "brokers_mt5_trade_executor_mt5tradeexecutor_close_position": ".close_position()" | kind=code-symbol | source=brokers/mt5_trade_executor.py:L143 | neighbors=[MT5TradeExecutor, .get_position()] | lang=en
- "brokers_mt5_trade_executor_mt5tradeexecutor_comment_for": "._comment_for()" | kind=code-symbol | source=brokers/mt5_trade_executor.py:L212 | neighbors=[MT5TradeExecutor, .execute_trade()] | lang=en
- "brokers_mt5_trade_executor_mt5tradeexecutor_execute_trade": ".execute_trade()" | kind=code-symbol | source=brokers/mt5_trade_executor.py:L34 | neighbors=[MT5TradeExecutor, ._comment_for()] | lang=en
- "brokers_mt5_trade_executor_mt5tradeexecutor_get_position": ".get_position()" | kind=code-symbol | source=brokers/mt5_trade_executor.py:L121 | neighbors=[MT5TradeExecutor, .close_position()] | lang=en
- "brokers_mt5_trade_executor_mt5tradeexecutor_move_stop_loss": ".move_stop_loss()" | kind=code-symbol | source=brokers/mt5_trade_executor.py:L97 | neighbors=[MT5TradeExecutor, Modifica el Stop Loss de una posición r…] | lang=en
- "brokers_symbol_discovery_derivsymboldiscovery_classify_symbol": ".classify_symbol()" | kind=code-symbol | source=brokers/symbol_discovery.py:L78 | neighbors=[DerivSymbolDiscovery, .get_deriv_synthetics()] | lang=en
- "brokers_symbol_discovery_derivsymboldiscovery_get_symbol_info": ".get_symbol_info()" | kind=code-symbol | source=brokers/symbol_discovery.py:L143 | neighbors=[DerivSymbolDiscovery, ._ensure_connection()] | lang=en
- "brokers_symbol_discovery_derivsymboldiscovery_get_tradeable_synthetics": ".get_tradeable_synthetics()" | kind=code-symbol | source=brokers/symbol_discovery.py:L164 | neighbors=[DerivSymbolDiscovery, .get_all_synthetic_symbols()] | lang=en
- "brokers_symbol_discovery_derivsymboldiscovery_print_report": ".print_report()" | kind=code-symbol | source=brokers/symbol_discovery.py:L240 | neighbors=[DerivSymbolDiscovery, .get_deriv_synthetics()] | lang=en
- "config_instruments_instrumentmanager_get_active_symbols": ".get_active_symbols()" | kind=code-symbol | source=config/instruments.py:L48 | neighbors=[InstrumentManager, Devuelve símbolos sintéticos tradeables…] | lang=en
- "config_instruments_instrumentmanager_get_all_instruments": ".get_all_instruments()" | kind=code-symbol | source=config/instruments.py:L24 | neighbors=[InstrumentManager, Devuelve el universo tradeable soportad…] | lang=en
- "config_instruments_rationale_25": "Devuelve el universo tradeable soportado por DaemonBlackFx:         sintéticos +" | kind=entity | source=config/instruments.py:L25 | neighbors=[DerivSymbolDiscovery, .get_all_instruments()] | lang=es
- "config_instruments_rationale_52": "Devuelve símbolos sintéticos tradeables filtrados por categoría.          A dife" | kind=entity | source=config/instruments.py:L52 | neighbors=[DerivSymbolDiscovery, .get_active_symbols()] | lang=pt
- "config_strategy_config": "strategy_config.py" | kind=code-symbol | source=config/strategy_config.py:L1 | neighbors=[main.py, test_main_symbol_selection.py] | lang=en
- "config_symbol_policy_classify_synthetic_symbol": "classify_synthetic_symbol()" | kind=code-symbol | source=config/symbol_policy.py:L14 | neighbors=[symbol_policy.py, get_symbol_direction_policy()] | lang=en
- "config_symbol_policy_symboldirectionpolicy": "SymbolDirectionPolicy" | kind=code-symbol | source=config/symbol_policy.py:L7 | neighbors=[symbol_policy.py, get_symbol_direction_policy()] | lang=en
- "dashboard_realtime_dashboard_confirmed_decision": "_confirmed_decision()" | kind=code-symbol | source=dashboard/realtime_dashboard.py:L311 | neighbors=[realtime_dashboard.py, _position_health()] | lang=en
- "dashboard_realtime_dashboard_divergence_direction": "_divergence_direction()" | kind=code-symbol | source=dashboard/realtime_dashboard.py:L316 | neighbors=[realtime_dashboard.py, _position_health()] | lang=en
- "dashboard_realtime_dashboard_infer_symbol_profile": "_infer_symbol_profile()" | kind=code-symbol | source=dashboard/realtime_dashboard.py:L346 | neighbors=[realtime_dashboard.py, _position_owner()] | lang=en
- "dashboard_realtime_dashboard_operational_state": "_operational_state()" | kind=code-symbol | source=dashboard/realtime_dashboard.py:L167 | neighbors=[realtime_dashboard.py, _enrich_recent_row()] | lang=en
- "dashboard_realtime_dashboard_rationale_1677": "Recarga selecciones autoritativas desde SQLAlchemy.          v57: el estado JSON" | kind=entity | source=dashboard/realtime_dashboard.py:L1677 | neighbors=[._refresh_selection_profiles_from_db_lo…, TradeAuditExcelExporter] | lang=es
- "dashboard_realtime_dashboard_rationale_190": "Normaliza eventos persistidos para que el dashboard explique el bloqueo." | kind=entity | source=dashboard/realtime_dashboard.py:L190 | neighbors=[_enrich_recent_row(), TradeAuditExcelExporter] | lang=es
- "dashboard_realtime_dashboard_rationale_421": "Evalúa la salud de una posición abierta sin ejecutar cierres automáticos.      C" | kind=entity | source=dashboard/realtime_dashboard.py:L421 | neighbors=[_position_health(), TradeAuditExcelExporter] | lang=en

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-028.json

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
