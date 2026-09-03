# Node Description Batch 41 of 56

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

- "execution_runner_extension_manager_rationale_34": "Evalúa si un RUNNER que ya alcanzó 2R/3R conserva estructura suficiente.      Ga" | kind=entity | source=strategy/execution/runner_extension_manager.py:L34 | neighbors=[evaluate_runner_continuation()]
- "execution_runner_extension_manager_rr_price": "rr_price()" | kind=code-symbol | source=strategy/execution/runner_extension_manager.py:L19 | neighbors=[runner_extension_manager.py]
- "execution_trade_executor_rationale_215": "Ejecuta una operación.\r \r         Implementaciones posibles:\r \r         - PaperT" | kind=entity | source=strategy/execution/trade_executor.py:L215 | neighbors=[.execute_trade()]
- "execution_trade_executor_rationale_233": "Obtiene el estado actual\r         de una posición." | kind=entity | source=strategy/execution/trade_executor.py:L233 | neighbors=[.get_position()]
- "execution_trade_executor_tradeexecutionrequest_from_signal": ".from_signal()" | kind=code-symbol | source=strategy/execution/trade_executor.py:L46 | neighbors=[TradeExecutionRequest]
- "execution_trade_executor_tradeexecutionresult_is_filled": ".is_filled()" | kind=code-symbol | source=strategy/execution/trade_executor.py:L192 | neighbors=[TradeExecutionResult]
- "execution_trade_executor_tradeexecutor_close_position": ".close_position()" | kind=code-symbol | source=strategy/execution/trade_executor.py:L241 | neighbors=[TradeExecutor]
- "execution_trade_outcome_policy_rationale_31": "Devuelve WIN / LOSS / BREAK_EVEN / OPEN / None.      Prioridad:     1. OPEN nunc" | kind=entity | source=strategy/execution/trade_outcome_policy.py:L31 | neighbors=[decisive_outcome()]
- "monitoring_init": "__init__.py" | kind=code-symbol | source=monitoring/__init__.py:L1 | neighbors=[position_monitoring_service.py]
- "monitoring_position_monitoring_service_positionmonitoringservice_break_even_trigger_rr": ".break_even_trigger_rr()" | kind=code-symbol | source=monitoring/position_monitoring_service.py:L61 | neighbors=[PositionMonitoringService]
- "monitoring_position_monitoring_service_positionmonitoringservice_init": ".__init__()" | kind=code-symbol | source=monitoring/position_monitoring_service.py:L30 | neighbors=[PositionMonitoringService]
- "monitoring_trade_monitor": "trade_monitor.py" | kind=code-symbol | source=monitoring/trade_monitor.py:L1 | neighbors=[TradeMonitor]
- "monitoring_trade_monitor_trademonitor_init": ".__init__()" | kind=code-symbol | source=monitoring/trade_monitor.py:L2 | neighbors=[TradeMonitor]
- "monitoring_trade_monitor_trademonitor_sync": ".sync()" | kind=code-symbol | source=monitoring/trade_monitor.py:L5 | neighbors=[TradeMonitor]
- "orb_new_york_orb_rationale_104": "Descubre únicamente contratos ORB operables en la cuenta MT5 actual.      Los sí" | kind=entity | source=strategy/orb/new_york_orb.py:L104 | neighbors=[discover_orb_symbols()]
- "orb_new_york_orb_rationale_165": "Opening Range Breakout para la sesión cash de Nueva York.      - Rango: 09:30 <=" | kind=entity | source=strategy/orb/new_york_orb.py:L165 | neighbors=[NewYorkORBStrategy]
- "orb_new_york_orb_rationale_20": "Clasifica únicamente los contratos ORB autorizados.      Importante: no usamos e" | kind=entity | source=strategy/orb/new_york_orb.py:L20 | neighbors=[classify_orb_market()]
- "orb_new_york_orb_rationale_51": "True únicamente para las dos variantes de Oro autorizadas por ORB." | kind=entity | source=strategy/orb/new_york_orb.py:L51 | neighbors=[is_orb_gold_symbol()]
- "orb_new_york_orb_rationale_63": "Puntúa la calidad de ejecución del contrato de Oro.      Menor score = mejor con" | kind=entity | source=strategy/orb/new_york_orb.py:L63 | neighbors=[score_orb_gold_contract_candidate()]
- "position_manager_positionmanager_clear_all": ".clear_all()" | kind=code-symbol | source=position_manager.py:L518 | neighbors=[PositionManager]
- "position_manager_positionmanager_clear_closed_positions": ".clear_closed_positions()" | kind=code-symbol | source=position_manager.py:L510 | neighbors=[PositionManager]
- "position_manager_positionmanager_close_position": ".close_position()" | kind=code-symbol | source=position_manager.py:L417 | neighbors=[PositionManager]
- "position_manager_positionmanager_closed_positions_count": ".closed_positions_count()" | kind=code-symbol | source=position_manager.py:L171 | neighbors=[PositionManager]
- "position_manager_positionmanager_get_closed_positions": ".get_closed_positions()" | kind=code-symbol | source=position_manager.py:L150 | neighbors=[PositionManager]
- "position_manager_positionmanager_get_open_positions": ".get_open_positions()" | kind=code-symbol | source=position_manager.py:L139 | neighbors=[PositionManager]
- "position_manager_positionmanager_get_position": ".get_position()" | kind=code-symbol | source=position_manager.py:L119 | neighbors=[PositionManager]
- "position_manager_positionmanager_init": ".__init__()" | kind=code-symbol | source=position_manager.py:L10 | neighbors=[PositionManager]
- "position_manager_positionmanager_is_open": ".is_open()" | kind=code-symbol | source=position_manager.py:L181 | neighbors=[PositionManager]
- "position_manager_positionmanager_open_positions_count": ".open_positions_count()" | kind=code-symbol | source=position_manager.py:L161 | neighbors=[PositionManager]
- "position_manager_positionmanager_register_position": ".register_position()" | kind=code-symbol | source=position_manager.py:L19 | neighbors=[PositionManager]
- "position_manager_positionmanager_update_price": ".update_price()" | kind=code-symbol | source=position_manager.py:L192 | neighbors=[PositionManager]
- "position_manager_rationale_263": "Mueve el stop loss al precio de entrada cuando la posición         alcanza la re" | kind=entity | source=position_manager.py:L263 | neighbors=[.apply_break_even()]
- "reporting_console_reporting_service_consolereportingservice_print_daemon_started": ".print_daemon_started()" | kind=code-symbol | source=reporting/console_reporting_service.py:L154 | neighbors=[ConsoleReportingService]
- "reporting_console_reporting_service_consolereportingservice_print_position_monitor": ".print_position_monitor()" | kind=code-symbol | source=reporting/console_reporting_service.py:L278 | neighbors=[ConsoleReportingService]
- "reporting_console_reporting_service_consolereportingservice_print_symbol_start": ".print_symbol_start()" | kind=code-symbol | source=reporting/console_reporting_service.py:L180 | neighbors=[ConsoleReportingService]
- "reporting_console_reporting_service_rationale_20": "Presenta resultados del motor de trading sin volcar diccionarios completos." | kind=entity | source=reporting/console_reporting_service.py:L20 | neighbors=[ConsoleReportingService]
- "reporting_trade_audit_excel_exporter_rationale_12": "Exporta la auditoría completa Entrada vs. Ahora de un trade a XLSX.      El payl" | kind=entity | source=reporting/trade_audit_excel_exporter.py:L12 | neighbors=[TradeAuditExcelExporter]
- "reporting_trade_audit_excel_exporter_tradeauditexcelexporter_init": ".__init__()" | kind=code-symbol | source=reporting/trade_audit_excel_exporter.py:L22 | neighbors=[TradeAuditExcelExporter]
- "reporting_trade_report_exporter_rationale_15": "Exporta el estado del daemon a XLSX con auditoría explicable.      Además de las" | kind=entity | source=reporting/trade_report_exporter.py:L15 | neighbors=[TradeReportExporter]
- "reporting_trade_report_exporter_rationale_164": "Construye un resumen útil sin exportar el JSON completo a una celda." | kind=entity | source=reporting/trade_report_exporter.py:L164 | neighbors=[._audit_summary()]

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-040.json

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
