# Node Description Batch 39 of 56

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

- "backtesting_trade_simulator_rationale_441": "Simula todas las entradas confirmadas." | kind=entity | source=backtesting/trade_simulator.py:L441 | neighbors=[simulate_all_trades()] | lang=es
- "backtesting_trade_simulator_rationale_520": "Alias de compatibilidad.\r \r     Permite utilizar:\r \r         simulate_trades(..." | kind=entity | source=backtesting/trade_simulator.py:L520 | neighbors=[simulate_trades()] | lang=nl
- "backtesting_trade_simulator_rationale_544": "Genera un resumen estadístico\r     de las operaciones simuladas." | kind=entity | source=backtesting/trade_simulator.py:L544 | neighbors=[get_backtest_summary()] | lang=en
- "backtesting_trade_simulator_rationale_88": "Calcula el Risk:Reward teórico de la operación.\r \r     Ejemplo:\r \r     Riesgo =" | kind=entity | source=backtesting/trade_simulator.py:L88 | neighbors=[calculate_planned_rr()] | lang=en
- "brokers_mt5_connector_mt5connector_init": ".__init__()" | kind=code-symbol | source=brokers/mt5_connector.py:L9 | neighbors=[MT5Connector] | lang=en
- "brokers_mt5_connector_rationale_13": "Inicializa la conexión con MetaTrader 5." | kind=entity | source=brokers/mt5_connector.py:L13 | neighbors=[.connect()] | lang=en
- "brokers_mt5_connector_rationale_47": "Cierra la conexión con MetaTrader 5." | kind=entity | source=brokers/mt5_connector.py:L47 | neighbors=[.disconnect()] | lang=en
- "brokers_mt5_connector_rationale_5": "Gestiona la conexión entre Python y MetaTrader 5." | kind=entity | source=brokers/mt5_connector.py:L5 | neighbors=[MT5Connector] | lang=es
- "brokers_mt5_connector_rationale_60": "Verifica si MetaTrader 5 continúa conectado." | kind=entity | source=brokers/mt5_connector.py:L60 | neighbors=[.is_connected()] | lang=pt
- "brokers_mt5_connector_rationale_78": "Obtiene la información de la cuenta actual." | kind=entity | source=brokers/mt5_connector.py:L78 | neighbors=[.get_account_info()] | lang=en
- "brokers_mt5_data_mt5dataprovider_disconnect": ".disconnect()" | kind=code-symbol | source=brokers/mt5_data.py:L67 | neighbors=[MT5DataProvider] | lang=en
- "brokers_mt5_execution_back_mt5executionprovider_init": ".__init__()" | kind=code-symbol | source=brokers/mt5_execution.back.py:L20 | neighbors=[MT5ExecutionProvider] | lang=en
- "brokers_mt5_execution_back_mt5executionprovider_is_order_send_success": "._is_order_send_success()" | kind=code-symbol | source=brokers/mt5_execution.back.py:L586 | neighbors=[MT5ExecutionProvider] | lang=en
- "brokers_mt5_execution_back_rationale_14": "Capa de ejecución para una cuenta MT5 ya conectada.      Esta clase no contiene" | kind=entity | source=brokers/mt5_execution.back.py:L14 | neighbors=[MT5ExecutionProvider] | lang=es
- "brokers_mt5_execution_back_rationale_326": "Convierte el bitmask SYMBOL_FILLING_* a ORDER_FILLING_*.          IMPORTANTE:" | kind=entity | source=brokers/mt5_execution.back.py:L326 | neighbors=[._allowed_fillings()] | lang=en
- "brokers_mt5_execution_back_rationale_395": "Devuelve las restricciones reales informadas por MT5 para el símbolo." | kind=entity | source=brokers/mt5_execution.back.py:L395 | neighbors=[.get_symbol_constraints()] | lang=es
- "brokers_mt5_execution_back_rationale_426": "Adapta SL/TP al precio actual y a la distancia mínima exigida por el broker." | kind=entity | source=brokers/mt5_execution.back.py:L426 | neighbors=[.normalize_market_stops()] | lang=es
- "brokers_mt5_execution_back_rationale_526": "Ejecuta order_check sin enviar la orden y prueba los filling compatibles." | kind=entity | source=brokers/mt5_execution.back.py:L526 | neighbors=[.check_market_order()] | lang=es
- "brokers_mt5_execution_mt5executionprovider_init": ".__init__()" | kind=code-symbol | source=brokers/mt5_execution.py:L31 | neighbors=[MT5ExecutionProvider] | lang=en
- "brokers_mt5_execution_rationale_1055": "Abre una orden de mercado.          Antes de order_send ejecuta order_check con" | kind=entity | source=brokers/mt5_execution.py:L1055 | neighbors=[.place_market_order()] | lang=en
- "brokers_mt5_execution_rationale_1183": "Modifica SL/TP de una posición abierta mediante TRADE_ACTION_SLTP.          Se u" | kind=entity | source=brokers/mt5_execution.py:L1183 | neighbors=[.modify_position_stops()] | lang=es
- "brokers_mt5_execution_rationale_123": "Devuelve restricciones reales informadas por MT5." | kind=entity | source=brokers/mt5_execution.py:L123 | neighbors=[.get_symbol_constraints()] | lang=en
- "brokers_mt5_execution_rationale_1246": "Devuelve un snapshot serializable de las posiciones abiertas de MT5.          Si" | kind=entity | source=brokers/mt5_execution.py:L1246 | neighbors=[.list_open_positions()] | lang=nl
- "brokers_mt5_execution_rationale_1304": "Devuelve el historial de deals disponible en MT5 en formato serializable." | kind=entity | source=brokers/mt5_execution.py:L1304 | neighbors=[.list_history_deals()] | lang=en
- "brokers_mt5_execution_rationale_14": "Capa de ejecución para una cuenta MT5 ya conectada.      MetaTrader 5 debe estar" | kind=entity | source=brokers/mt5_execution.py:L14 | neighbors=[MT5ExecutionProvider] | lang=es
- "brokers_mt5_execution_rationale_175": "Valida/adapta SL y TP y devuelve diagnóstico completo.          Regla importante" | kind=entity | source=brokers/mt5_execution.py:L175 | neighbors=[.normalize_market_stops()] | lang=es
- "brokers_mt5_execution_rationale_338": "Construye candidatos según las flags del símbolo.          MetaTrader expone inf" | kind=entity | source=brokers/mt5_execution.py:L338 | neighbors=[._symbol_filling_candidates()] | lang=es
- "brokers_mt5_execution_rationale_397": "Expone cómo MT5 informa los filling modes del símbolo." | kind=entity | source=brokers/mt5_execution.py:L397 | neighbors=[.get_filling_diagnostics()] | lang=es
- "brokers_mt5_execution_rationale_448": "Normaliza el comentario para el binding de MetaTrader5.          Algunos termina" | kind=entity | source=brokers/mt5_execution.py:L448 | neighbors=[._sanitize_comment()] | lang=es
- "brokers_mt5_execution_rationale_473": "Ejecuta order_check y, si el binding rechaza el comentario,         reintenta au" | kind=entity | source=brokers/mt5_execution.py:L473 | neighbors=[._order_check_safe()] | lang=es
- "brokers_mt5_execution_rationale_504": "Envía la orden y aplica el mismo fallback defensivo de comentario." | kind=entity | source=brokers/mt5_execution.py:L504 | neighbors=[._order_send_safe()] | lang=es
- "brokers_mt5_execution_rationale_632": "order_check() y order_send() no usan el mismo criterio de éxito.          En Met" | kind=entity | source=brokers/mt5_execution.py:L632 | neighbors=[._is_order_check_success()] | lang=en
- "brokers_mt5_execution_rationale_653": "Determina éxito después de order_send()." | kind=entity | source=brokers/mt5_execution.py:L653 | neighbors=[._is_order_send_success()] | lang=en
- "brokers_mt5_execution_rationale_679": "Prueba cada filling mode y conserva el diagnóstico completo." | kind=entity | source=brokers/mt5_execution.py:L679 | neighbors=[._run_order_check_with_fallback()] | lang=es
- "brokers_mt5_execution_rationale_787": "Ejecuta order_check sin abrir una operación.          Prueba automáticamente los" | kind=entity | source=brokers/mt5_execution.py:L787 | neighbors=[.check_market_order()] | lang=es
- "brokers_mt5_execution_rationale_816": "Calcula margen requerido con el motor nativo de MT5." | kind=entity | source=brokers/mt5_execution.py:L816 | neighbors=[.calculate_margin_amount()] | lang=es
- "brokers_mt5_execution_rationale_87": "Asegura que el símbolo exista y esté seleccionado en Market Watch." | kind=entity | source=brokers/mt5_execution.py:L87 | neighbors=[.ensure_symbol()] | lang=es
- "brokers_mt5_execution_rationale_908": "Calcula la pérdida monetaria teórica usando el propio motor del broker." | kind=entity | source=brokers/mt5_execution.py:L908 | neighbors=[.calculate_risk_amount()] | lang=en
- "brokers_mt5_execution_rationale_952": "Calcula volumen con MT5 como fuente de verdad del riesgo.          IMPORTANTE: s" | kind=entity | source=brokers/mt5_execution.py:L952 | neighbors=[.calculate_volume()] | lang=es
- "brokers_mt5_trade_executor_mt5tradeexecutor_init": ".__init__()" | kind=code-symbol | source=brokers/mt5_trade_executor.py:L29 | neighbors=[MT5TradeExecutor] | lang=en

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-038.json

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
