# Node Description Batch 24 of 56

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

- "reporting_strategy_evaluation_main": "main()" | kind=code-symbol | source=reporting/strategy_evaluation.py:L149 | neighbors=[strategy_evaluation.py, build_strategy_evaluation(), write_strategy_evaluation()]
- "reporting_strategy_evaluation_number": "_number()" | kind=code-symbol | source=reporting/strategy_evaluation.py:L13 | neighbors=[strategy_evaluation.py, build_strategy_evaluation(), _distribution()]
- "reporting_trade_audit_excel_exporter_tradeauditexcelexporter_first": "._first()" | kind=code-symbol | source=reporting/trade_audit_excel_exporter.py:L50 | neighbors=[TradeAuditExcelExporter, ._summary_frame(), ._timeline_frame()]
- "reporting_trade_audit_excel_exporter_tradeauditexcelexporter_local_time": "._local_time()" | kind=code-symbol | source=reporting/trade_audit_excel_exporter.py:L38 | neighbors=[TradeAuditExcelExporter, ._summary_frame(), ._timeline_frame()]
- "reporting_trade_audit_excel_exporter_tradeauditexcelexporter_view_frame": "._view_frame()" | kind=code-symbol | source=reporting/trade_audit_excel_exporter.py:L100 | neighbors=[TradeAuditExcelExporter, .export(), ._safe_text()]
- "reporting_trade_report_exporter_tradereportexporter_audit_summary": "._audit_summary()" | kind=code-symbol | source=reporting/trade_report_exporter.py:L163 | neighbors=[Construye un resumen útil sin exportar …, TradeReportExporter, ._audit_payload_dict()]
- "reporting_trade_report_exporter_tradereportexporter_extract_metadata": "._extract_metadata()" | kind=code-symbol | source=reporting/trade_report_exporter.py:L502 | neighbors=[TradeReportExporter, ._enrich_trades_for_report(), ._parse_details()]
- "reporting_trade_report_exporter_tradereportexporter_format_chile_now": "._format_chile_now()" | kind=code-symbol | source=reporting/trade_report_exporter.py:L564 | neighbors=[TradeReportExporter, .export(), ._format_local()]
- "reporting_trade_report_exporter_tradereportexporter_format_local": "._format_local()" | kind=code-symbol | source=reporting/trade_report_exporter.py:L569 | neighbors=[TradeReportExporter, ._format_chile_datetime(), ._format_chile_now()]
- "reporting_trade_report_exporter_tradereportexporter_format_workbook": "._format_workbook()" | kind=code-symbol | source=reporting/trade_report_exporter.py:L619 | neighbors=[TradeReportExporter, .export(), ._build_summary_dashboard()]
- "reporting_trade_report_exporter_tradereportexporter_labels": "._labels()" | kind=code-symbol | source=reporting/trade_report_exporter.py:L526 | neighbors=[TradeReportExporter, ._build_entry_reason(), ._report_record()]
- "reporting_trade_report_exporter_tradereportexporter_safe_number": "._safe_number()" | kind=code-symbol | source=reporting/trade_report_exporter.py:L550 | neighbors=[TradeReportExporter, ._classify_close(), ._report_record()]
- "reporting_trade_reporting_service_tradereportingservice_broker": "._broker()" | kind=code-symbol | source=reporting/trade_reporting_service.py:L256 | neighbors=[TradeReportingService, ._build_open_data(), ._build_open_update()]
- "reporting_trade_reporting_service_tradereportingservice_execution_key": "._execution_key()" | kind=code-symbol | source=reporting/trade_reporting_service.py:L320 | neighbors=[TradeReportingService, ._build_open_data(), ._find_trade_id()]
- "reporting_trade_reporting_service_tradereportingservice_export_if_enabled": "._export_if_enabled()" | kind=code-symbol | source=reporting/trade_reporting_service.py:L349 | neighbors=[TradeReportingService, .export_now(), .on_lifecycle_event()]
- "reporting_trade_reporting_service_tradereportingservice_lookup_keys": "._lookup_keys()" | kind=code-symbol | source=reporting/trade_reporting_service.py:L308 | neighbors=[TradeReportingService, ._find_trade_id(), ._remember_trade()]
- "reporting_trade_reporting_service_tradereportingservice_volume": "._volume()" | kind=code-symbol | source=reporting/trade_reporting_service.py:L268 | neighbors=[TradeReportingService, ._build_open_data(), ._build_open_update()]
- "risk_money_management_calculate_drawdown_statistics": "calculate_drawdown_statistics()" | kind=code-symbol | source=strategy/risk/money_management.py:L638 | neighbors=[money_management.py, calculate_money_management_statistics(), Calcula estadísticas de drawdown     a…]
- "risk_money_manager": "money_manager.py" | kind=code-symbol | source=risk/money_manager.py:L1 | neighbors=[MoneyManager, TradeRiskResult, test_money_manager.py]
- "risk_money_manager_traderiskresult": "TradeRiskResult" | kind=code-symbol | source=risk/money_manager.py:L5 | neighbors=[money_manager.py, .process_trade(), Resultado financiero de una operación.]
- "risk_position_sizing_add_position_sizing": "add_position_sizing()" | kind=code-symbol | source=strategy/risk/position_sizing.py:L173 | neighbors=[position_sizing.py, calculate_position_size(), Agrega información de gestión de tamaño…]
- "risk_position_sizing_calculate_position_size": "calculate_position_size()" | kind=code-symbol | source=strategy/risk/position_sizing.py:L4 | neighbors=[position_sizing.py, add_position_sizing(), Calcula el tamaño de posición basándose…]
- "risk_risk_manager_calculate_max_loss_amount": "calculate_max_loss_amount()" | kind=code-symbol | source=strategy/risk/risk_manager.py:L554 | neighbors=[risk_manager.py, check_daily_loss_limit(), Calcula un monto máximo de pérdida basa…]
- "risk_risk_manager_calculate_open_positions_risk": "calculate_open_positions_risk()" | kind=code-symbol | source=strategy/risk/risk_manager.py:L950 | neighbors=[risk_manager.py, evaluate_trade_risk(), Calcula el riesgo total de las posicion…]
- "risk_risk_manager_evaluate_risk": "evaluate_risk()" | kind=code-symbol | source=strategy/risk/risk_manager.py:L1698 | neighbors=[risk_manager.py, evaluate_trade_risk(), Alias simplificado de evaluate_trade_ri…]
- "risk_risk_manager_validate_integer": "validate_integer()" | kind=code-symbol | source=strategy/risk/risk_manager.py:L117 | neighbors=[risk_manager.py, evaluate_trade_risk(), Valida un número entero.]
- "scalping_adaptive_regime_pullback_adaptiveregimepullbackstrategy_effective_adx_threshold": "._effective_adx_threshold()" | kind=code-symbol | source=strategy/scalping/adaptive_regime_pullback.py:L103 | neighbors=[AdaptiveRegimePullbackStrategy, .analyze_symbol(), Umbral por instrumento, acotado por pis…]
- "scalping_adaptive_regime_pullback_adaptiveregimepullbackstrategy_read": "._read()" | kind=code-symbol | source=strategy/scalping/adaptive_regime_pullback.py:L100 | neighbors=[AdaptiveRegimePullbackStrategy, .analyze_symbol(), _closed_frame()]
- "scalping_adaptive_regime_pullback_adx": "_adx()" | kind=code-symbol | source=strategy/scalping/adaptive_regime_pullback.py:L72 | neighbors=[adaptive_regime_pullback.py, .analyze_symbol(), _atr()]
- "scalping_adaptive_regime_pullback_atr": "_atr()" | kind=code-symbol | source=strategy/scalping/adaptive_regime_pullback.py:L59 | neighbors=[adaptive_regime_pullback.py, .analyze_symbol(), _adx()]
- "scalping_init_rationale_1": "Estrategias de scalping independientes del pipeline SMC principal." | kind=entity | source=strategy/scalping/__init__.py:L1 | neighbors=[AdaptiveRegimePullbackConfig, AdaptiveRegimePullbackStrategy, __init__.py]
- "services_execution_preflight_service": "execution_preflight_service.py" | kind=code-symbol | source=services/execution_preflight_service.py:L1 | neighbors=[ExecutionPreflightConfig, ExecutionPreflightService, test_execution_preflight_service.py]
- "smc_chart_patterns_effective_price_tolerance": "_effective_price_tolerance()" | kind=code-symbol | source=strategy/smc/chart_patterns.py:L82 | neighbors=[chart_patterns.py, detect_chart_pattern_confirmation(), Tolera pivotes equivalentes en unidades…]
- "smc_chart_patterns_evidence": "_evidence()" | kind=code-symbol | source=strategy/smc/chart_patterns.py:L108 | neighbors=[chart_patterns.py, detect_chart_pattern_confirmation(), _iso()]
- "smc_chart_patterns_explain_chart_pattern_conflict": "_explain_chart_pattern_conflict()" | kind=code-symbol | source=strategy/smc/chart_patterns.py:L123 | neighbors=[chart_patterns.py, detect_chart_pattern_confirmation(), Devuelve nivel, razón y delta sin alter…]
- "smc_confirmation_engine_average_range": "_average_range()" | kind=code-symbol | source=strategy/smc/confirmation_engine.py:L98 | neighbors=[confirmation_engine.py, _safe_float(), evaluate_m5_confirmation()]
- "smc_confirmation_engine_candle_metrics": "candle_metrics()" | kind=code-symbol | source=strategy/smc/confirmation_engine.py:L78 | neighbors=[confirmation_engine.py, _safe_float(), evaluate_m5_confirmation()]
- "smc_confirmation_engine_rationale_1": "Motor de confirmación M5 para DaemonBlackFx.  El objetivo es evitar entradas por" | kind=entity | source=strategy/smc/confirmation_engine.py:L1 | neighbors=[ChartPatternConfig, confirmation_engine.py, HarmonicConfig]
- "smc_confirmation_engine_rationale_139": "Detecta divergencia regular entre precio y RSI usando pivotes SMC confirmados." | kind=entity | source=strategy/smc/confirmation_engine.py:L139 | neighbors=[ChartPatternConfig, detect_rsi_divergence(), HarmonicConfig]
- "smc_confirmation_engine_rationale_199": "Evalúa una vela candidata y devuelve un diagnóstico completamente explicable." | kind=entity | source=strategy/smc/confirmation_engine.py:L199 | neighbors=[ChartPatternConfig, evaluate_m5_confirmation(), HarmonicConfig]

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-023.json

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
