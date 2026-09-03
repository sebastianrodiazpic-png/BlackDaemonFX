# Node Description Batch 32 of 56

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

- "monitoring_position_monitoring_service_rationale_69": "Procesa un único tick/precio para una posición abierta." | kind=entity | source=monitoring/position_monitoring_service.py:L69 | neighbors=[.monitor_position(), PositionManager]
- "orb_new_york_orb_newyorkorbstrategy_init": ".__init__()" | kind=code-symbol | source=strategy/orb/new_york_orb.py:L174 | neighbors=[NewYorkORBStrategy, ORBConfig]
- "orb_new_york_orb_newyorkorbstrategy_prepare_candles": "._prepare_candles()" | kind=code-symbol | source=strategy/orb/new_york_orb.py:L248 | neighbors=[NewYorkORBStrategy, .analyze_symbol()]
- "orb_new_york_orb_newyorkorbstrategy_session_bounds": "._session_bounds()" | kind=code-symbol | source=strategy/orb/new_york_orb.py:L179 | neighbors=[NewYorkORBStrategy, .analyze_symbol()]
- "orb_new_york_orb_norm_symbol": "_norm_symbol()" | kind=code-symbol | source=strategy/orb/new_york_orb.py:L15 | neighbors=[new_york_orb.py, classify_orb_market()]
- "orb_new_york_orb_score_orb_gold_contract_candidate": "score_orb_gold_contract_candidate()" | kind=code-symbol | source=strategy/orb/new_york_orb.py:L55 | neighbors=[new_york_orb.py, Puntúa la calidad de ejecución del cont…]
- "position_manager_positionmanager_apply_break_even": ".apply_break_even()" | kind=code-symbol | source=position_manager.py:L257 | neighbors=[PositionManager, Mueve el stop loss al precio de entrada…]
- "reporting_console_reporting_service_consolereportingservice_confirmation_label": "._confirmation_label()" | kind=code-symbol | source=reporting/console_reporting_service.py:L132 | neighbors=[ConsoleReportingService, ._print_confirmation_diag()]
- "reporting_console_reporting_service_consolereportingservice_extract_confirmation_diag": "._extract_confirmation_diag()" | kind=code-symbol | source=reporting/console_reporting_service.py:L207 | neighbors=[ConsoleReportingService, ._print_confirmation_diag()]
- "reporting_console_reporting_service_consolereportingservice_init": ".__init__()" | kind=code-symbol | source=reporting/console_reporting_service.py:L69 | neighbors=[ConsoleReportingService, ConsoleReportingConfig]
- "reporting_console_reporting_service_consolereportingservice_print_cycle_error": ".print_cycle_error()" | kind=code-symbol | source=reporting/console_reporting_service.py:L436 | neighbors=[ConsoleReportingService, ._line()]
- "reporting_console_reporting_service_consolereportingservice_print_cycle_start": ".print_cycle_start()" | kind=code-symbol | source=reporting/console_reporting_service.py:L167 | neighbors=[ConsoleReportingService, ._line()]
- "reporting_console_reporting_service_consolereportingservice_print_debug": ".print_debug()" | kind=code-symbol | source=reporting/console_reporting_service.py:L391 | neighbors=[ConsoleReportingService, .print_result()]
- "reporting_console_reporting_service_consolereportingservice_reason_label": "._reason_label()" | kind=code-symbol | source=reporting/console_reporting_service.py:L66 | neighbors=[ConsoleReportingService, ._print_confirmation_diag()]
- "reporting_console_reporting_service_consolereportingservice_summarize": ".summarize()" | kind=code-symbol | source=reporting/console_reporting_service.py:L395 | neighbors=[ConsoleReportingService, ._line()]
- "reporting_init": "__init__.py" | kind=code-symbol | source=reporting/__init__.py:L1 | neighbors=[console_reporting_service.py, trade_reporting_service.py]
- "reporting_strategy_evaluation_write_strategy_evaluation": "write_strategy_evaluation()" | kind=code-symbol | source=reporting/strategy_evaluation.py:L140 | neighbors=[strategy_evaluation.py, main()]
- "reporting_trade_audit_excel_exporter_tradeauditexcelexporter_format_workbook": "._format_workbook()" | kind=code-symbol | source=reporting/trade_audit_excel_exporter.py:L233 | neighbors=[TradeAuditExcelExporter, .export()]
- "reporting_trade_report_exporter_tradereportexporter_as_list": "._as_list()" | kind=code-symbol | source=reporting/trade_report_exporter.py:L532 | neighbors=[TradeReportExporter, ._report_record()]
- "reporting_trade_report_exporter_tradereportexporter_audit_payload_dict": "._audit_payload_dict()" | kind=code-symbol | source=reporting/trade_report_exporter.py:L149 | neighbors=[TradeReportExporter, ._audit_summary()]
- "reporting_trade_report_exporter_tradereportexporter_build_summary_dashboard": "._build_summary_dashboard()" | kind=code-symbol | source=reporting/trade_report_exporter.py:L681 | neighbors=[TradeReportExporter, ._format_workbook()]
- "reporting_trade_report_exporter_tradereportexporter_compact_audit_dataframe": "._compact_audit_dataframe()" | kind=code-symbol | source=reporting/trade_report_exporter.py:L214 | neighbors=[TradeReportExporter, .export()]
- "reporting_trade_report_exporter_tradereportexporter_format_chile_datetime": "._format_chile_datetime()" | kind=code-symbol | source=reporting/trade_report_exporter.py:L577 | neighbors=[TradeReportExporter, ._format_local()]
- "reporting_trade_report_exporter_tradereportexporter_get_account_snapshots": "._get_account_snapshots()" | kind=code-symbol | source=reporting/trade_report_exporter.py:L610 | neighbors=[TradeReportExporter, .export()]
- "reporting_trade_report_exporter_tradereportexporter_localize_dataframe_timestamps": "._localize_dataframe_timestamps()" | kind=code-symbol | source=reporting/trade_report_exporter.py:L597 | neighbors=[TradeReportExporter, .export()]
- "reporting_trade_report_exporter_tradereportexporter_parse_details": "._parse_details()" | kind=code-symbol | source=reporting/trade_report_exporter.py:L515 | neighbors=[TradeReportExporter, ._extract_metadata()]
- "reporting_trade_report_exporter_tradereportexporter_report_columns": "._report_columns()" | kind=code-symbol | source=reporting/trade_report_exporter.py:L290 | neighbors=[TradeReportExporter, ._enrich_trades_for_report()]
- "reporting_trade_reporting_service_rationale_12": "Configuración del servicio de reporting del ciclo de vida.      source:" | kind=entity | source=reporting/trade_reporting_service.py:L12 | neighbors=[TradeReportExporter, TradeReportingConfig]
- "reporting_trade_reporting_service_rationale_30": "Adaptador entre TradeLifecycleManager, TradingRepository y TradeReportExporter." | kind=entity | source=reporting/trade_reporting_service.py:L30 | neighbors=[TradeReportExporter, TradeReportingService]
- "reporting_trade_reporting_service_tradereportingservice_audit_lifecycle_event": "._audit_lifecycle_event()" | kind=code-symbol | source=reporting/trade_reporting_service.py:L371 | neighbors=[TradeReportingService, .on_lifecycle_event()]
- "reporting_trade_reporting_service_tradereportingservice_export_now": ".export_now()" | kind=code-symbol | source=reporting/trade_reporting_service.py:L346 | neighbors=[TradeReportingService, ._export_if_enabled()]
- "reporting_trade_reporting_service_tradereportingservice_init": ".__init__()" | kind=code-symbol | source=reporting/trade_reporting_service.py:L42 | neighbors=[TradeReportingService, TradeReportingConfig]
- "reporting_trade_reporting_service_tradereportingservice_safe_value": "._safe_value()" | kind=code-symbol | source=reporting/trade_reporting_service.py:L399 | neighbors=[TradeReportingService, ._build_details()]
- "risk_money_manager_moneymanager_get_current_balance": ".get_current_balance()" | kind=code-symbol | source=risk/money_manager.py:L54 | neighbors=[MoneyManager, Retorna el capital actual.]
- "risk_position_sizing": "position_sizing.py" | kind=code-symbol | source=strategy/risk/position_sizing.py:L1 | neighbors=[add_position_sizing(), calculate_position_size()]
- "risk_risk_manager_get_risk_summary": "get_risk_summary()" | kind=code-symbol | source=strategy/risk/risk_manager.py:L1714 | neighbors=[risk_manager.py, Genera un resumen simplificado del resu…]
- "risk_risk_manager_validate_non_negative_number": "validate_non_negative_number()" | kind=code-symbol | source=strategy/risk/risk_manager.py:L74 | neighbors=[risk_manager.py, Valida que un valor sea numérico, finit…]
- "runtimeerror": "RuntimeError" | kind=code-symbol | neighbors=[MT5ExecutionError, MT5ExecutionError]
- "scalping_adaptive_regime_pullback_adaptiveregimepullbackstrategy_family_direction_allowed": "._family_direction_allowed()" | kind=code-symbol | source=strategy/scalping/adaptive_regime_pullback.py:L92 | neighbors=[AdaptiveRegimePullbackStrategy, .analyze_symbol()]
- "scalping_adaptive_regime_pullback_adaptiveregimepullbackstrategy_init": ".__init__()" | kind=code-symbol | source=strategy/scalping/adaptive_regime_pullback.py:L87 | neighbors=[AdaptiveRegimePullbackStrategy, AdaptiveRegimePullbackConfig]

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-031.json

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
