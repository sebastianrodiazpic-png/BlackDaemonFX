# Node Description Batch 14 of 56

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

- "dashboard_realtime_dashboard_extract_quality": "_extract_quality()" | kind=code-symbol | source=dashboard/realtime_dashboard.py:L541 | neighbors=[realtime_dashboard.py, _extract_signal(), _first_dict(), _quality_grade(), .symbol_result()]
- "dashboard_realtime_dashboard_realtimedashboardservice_init": ".__init__()" | kind=code-symbol | source=dashboard/realtime_dashboard.py:L632 | neighbors=[RealtimeDashboardService, _now_iso(), ._load_persisted_state(), ._refresh_account_locked(), ._refresh_open_positions_locked()]
- "dashboard_realtime_dashboard_realtimedashboardservice_snapshot": ".snapshot()" | kind=code-symbol | source=dashboard/realtime_dashboard.py:L1719 | neighbors=[RealtimeDashboardService, _enrich_recent_row(), _json_safe(), ._refresh_account_locked(), ._refresh_open_positions_locked()]
- "database_repository_tradingrepository_int_or_none": "._int_or_none()" | kind=code-symbol | source=database/repository.py:L111 | neighbors=[Convierte un valor a entero o devuelve …, TradingRepository, .save_audit_event(), ._trade_kwargs(), .update_trade()]
- "database_repository_tradingrepository_save_instrument_selection_profile": ".save_instrument_selection_profile()" | kind=code-symbol | source=database/repository.py:L1586 | neighbors=[Guarda una única selección autoritativa…, TradingRepository, .latest_instrument_selection_profile(), ._normalize_selection_profile(), .save_audit_event()]
- "database_repository_tradingrepository_save_signal": ".save_signal()" | kind=code-symbol | source=database/repository.py:L1819 | neighbors=[TradingRepository, ._dt(), ._json_or_none(), ._none_or_upper(), .save_signal_once()]
- "database_repository_tradingrepository_sync_closed_mt5_trades": ".sync_closed_mt5_trades()" | kind=code-symbol | source=database/repository.py:L2748 | neighbors=[Sincroniza SQLite con MT5.          Sol…, TradingRepository, .reconcile_open_trades(), .open_trades(), .update_trade()]
- "execution_live_paper_trading_engine_livepapertradingengine_run_once": ".run_once()" | kind=code-symbol | source=strategy/execution/live_paper_trading_engine.py:L63 | neighbors=[LivePaperTradingEngine, .run_daemon(), ._is_ready_signal(), .monitor_active_positions(), ._signal_key()]
- "execution_live_trading_engine_livetradingengine_close_forex_positions_for_rollover": "._close_forex_positions_for_rollover()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L3454 | neighbors=[LiveTradingEngine, ._forex_rollover_status(), ._is_forex_symbol(), ._trade_owned_by_current_bot(), Cierra posiciones Forex administradas p…]
- "execution_live_trading_engine_livetradingengine_gold_smc_exposure_open": "._gold_smc_exposure_open()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L3115 | neighbors=[LiveTradingEngine, ._trade_has_confirmed_break_even(), ._trade_metadata(), .process_symbol(), Detecta Oro SMC aún abierto para impedi…]
- "execution_live_trading_engine_livetradingengine_load_quarantine_unlocked": "._load_quarantine_unlocked()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L499 | neighbors=[LiveTradingEngine, ._load_quarantine(), ._quarantine_file(), ._quarantine_result(), ._quarantine_symbol()]
- "execution_live_trading_engine_livetradingengine_manage_runner_extension": "._manage_runner_extension()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L1999 | neighbors=[LiveTradingEngine, ._break_even_price_tolerance(), ._uses_forex_style_smc_management(), ._monitor_break_even_positions(), Gestiona extensión dinámica del RUNNER …]
- "execution_live_trading_engine_livetradingengine_open_trade_diagnostics": "._open_trade_diagnostics()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L1244 | neighbors=[LiveTradingEngine, ._total_position_limit(), ._position_limit_result(), .process_symbol(), Obtiene únicamente operaciones OPEN del…]
- "execution_live_trading_engine_livetradingengine_position_limit_result": "._position_limit_result()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L1542 | neighbors=[LiveTradingEngine, ._forex_exposure_guard(), ._open_trade_diagnostics(), .process_symbol(), Devuelve None si se puede continuar o u…]
- "execution_live_trading_engine_livetradingengine_save_quarantine_unlocked": "._save_quarantine_unlocked()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L509 | neighbors=[LiveTradingEngine, ._quarantine_result(), ._quarantine_symbol(), ._save_quarantine(), ._quarantine_file()]
- "execution_live_trading_engine_livetradingengine_sync_open_trades_before_execution": "._sync_open_trades_before_execution()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L1275 | neighbors=[LiveTradingEngine, .process_symbol(), .process_symbols(), ._trade_owned_by_current_bot(), Evita que SQLite mantenga OPEN una oper…]
- "execution_live_trading_engine_livetradingengine_uses_forex_style_smc_management": "._uses_forex_style_smc_management()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L1072 | neighbors=[LiveTradingEngine, ._manage_runner_extension(), .process_symbol(), ._canonical_bot_profile(), Perfiles SMC con la misma gestión progr…]
- "execution_trade_pipeline_build_setups": "build_setups()" | kind=code-symbol | source=strategy/execution/trade_pipeline.py:L127 | neighbors=[trade_pipeline.py, _empty_setups(), _latest_sweep(), _trend_at(), run_trade_pipeline()]
- "monitoring_position_monitoring_service": "position_monitoring_service.py" | kind=code-symbol | source=monitoring/position_monitoring_service.py:L1 | neighbors=[paper_trade_executor.py, __init__.py, PositionMonitoringService, position_manager.py, test_position_monitoring_service.py]
- "reporting_console_reporting_service_consolereportingservice_line": "._line()" | kind=code-symbol | source=reporting/console_reporting_service.py:L72 | neighbors=[ConsoleReportingService, .print_cycle_error(), .print_cycle_start(), .print_startup(), .summarize()]
- "reporting_console_reporting_service_consolereportingservice_print_symbol_result": ".print_symbol_result()" | kind=code-symbol | source=reporting/console_reporting_service.py:L183 | neighbors=[ConsoleReportingService, ._label(), ._print_confirmation_diag(), ._print_trade_fields(), ._reason()]
- "reporting_trade_audit_excel_exporter_tradeauditexcelexporter_export": ".export()" | kind=code-symbol | source=reporting/trade_audit_excel_exporter.py:L190 | neighbors=[TradeAuditExcelExporter, ._format_workbook(), ._summary_frame(), ._timeline_frame(), ._view_frame()]
- "reporting_trade_audit_excel_exporter_tradeauditexcelexporter_summary_frame": "._summary_frame()" | kind=code-symbol | source=reporting/trade_audit_excel_exporter.py:L56 | neighbors=[TradeAuditExcelExporter, .export(), ._first(), ._local_time(), ._safe_text()]
- "reporting_trade_audit_excel_exporter_tradeauditexcelexporter_timeline_frame": "._timeline_frame()" | kind=code-symbol | source=reporting/trade_audit_excel_exporter.py:L124 | neighbors=[TradeAuditExcelExporter, .export(), ._first(), ._local_time(), ._safe_text()]
- "reporting_trade_report_exporter_tradereportexporter_enrich_trades_for_report": "._enrich_trades_for_report()" | kind=code-symbol | source=reporting/trade_report_exporter.py:L269 | neighbors=[TradeReportExporter, ._extract_metadata(), ._report_columns(), ._report_record(), .export()]
- "reporting_trade_reporting_service_tradereportingservice_build_details": "._build_details()" | kind=code-symbol | source=reporting/trade_reporting_service.py:L246 | neighbors=[TradeReportingService, ._safe_value(), ._build_open_data(), ._build_open_update(), ._close_trade()]
- "risk_money_management_calculate_risk_amount": "calculate_risk_amount()" | kind=code-symbol | source=strategy/risk/money_management.py:L151 | neighbors=[money_management.py, apply_money_management_to_trade(), validate_balance(), validate_risk_percent(), Calcula cuánto dinero se arriesgará. …]
- "risk_money_management_update_balance": "update_balance()" | kind=code-symbol | source=strategy/risk/money_management.py:L195 | neighbors=[money_management.py, apply_money_management_to_trade(), Actualiza el balance después de una ope…, validate_balance(), validate_pnl()]
- "risk_money_management_validate_dataframe": "validate_dataframe()" | kind=code-symbol | source=strategy/risk/money_management.py:L127 | neighbors=[money_management.py, apply_money_management(), calculate_money_management_statistics(), get_final_balance(), Valida que trades sea un DataFrame.]
- "risk_money_management_validate_risk_percent": "validate_risk_percent()" | kind=code-symbol | source=strategy/risk/money_management.py:L52 | neighbors=[money_management.py, apply_money_management(), apply_money_management_to_trade(), calculate_risk_amount(), Valida el porcentaje de riesgo.]
- "risk_money_manager_moneymanager_process_trade": ".process_trade()" | kind=code-symbol | source=risk/money_manager.py:L119 | neighbors=[MoneyManager, .calculate_profit_loss(), .calculate_risk_amount(), TradeRiskResult, Procesa una operación y actualiza     …]
- "risk_risk_manager_check_daily_loss_limit": "check_daily_loss_limit()" | kind=code-symbol | source=strategy/risk/risk_manager.py:L1103 | neighbors=[risk_manager.py, calculate_daily_loss(), calculate_max_loss_amount(), evaluate_trade_risk(), Verifica si se alcanzó el límite máximo…]
- "risk_risk_manager_validate_direction": "validate_direction()" | kind=code-symbol | source=strategy/risk/risk_manager.py:L184 | neighbors=[risk_manager.py, evaluate_trade_risk(), Valida la dirección de una operación. …, validate_stop_loss_direction(), validate_take_profit_direction()]
- "risk_risk_manager_validate_risk_reward": "validate_risk_reward()" | kind=code-symbol | source=strategy/risk/risk_manager.py:L449 | neighbors=[risk_manager.py, evaluate_trade_risk(), Verifica si la operación cumple con el…, calculate_risk_reward(), validate_positive_number()]
- "risk_risk_manager_validate_stop_loss_direction": "validate_stop_loss_direction()" | kind=code-symbol | source=strategy/risk/risk_manager.py:L229 | neighbors=[risk_manager.py, evaluate_trade_risk(), Verifica que el Stop Loss esté correcta…, validate_direction(), validate_positive_number()]
- "risk_risk_manager_validate_take_profit_direction": "validate_take_profit_direction()" | kind=code-symbol | source=strategy/risk/risk_manager.py:L301 | neighbors=[risk_manager.py, evaluate_trade_risk(), Verifica que el Take Profit esté correc…, validate_direction(), validate_positive_number()]
- "scalping_adaptive_regime_pullback": "adaptive_regime_pullback.py" | kind=code-symbol | source=strategy/scalping/adaptive_regime_pullback.py:L1 | neighbors=[AdaptiveRegimePullbackConfig, AdaptiveRegimePullbackStrategy, _adx(), _atr(), _closed_frame()]
- "services_live_demo_smoke_test_service_rationale_25": "Prueba controlada de una única orden real en una cuenta MT5 DEMO.      Requiere" | kind=entity | source=services/live_demo_smoke_test_service.py:L25 | neighbors=[MT5TradeExecutor, TradeReportingConfig, TradeReportingService, LiveDemoSmokeTestService, TradeLifecycleManager]
- "smc_confirmation_engine_detect_rsi_divergence": "detect_rsi_divergence()" | kind=code-symbol | source=strategy/smc/confirmation_engine.py:L131 | neighbors=[confirmation_engine.py, _rsi(), _safe_float(), evaluate_m5_confirmation(), Detecta divergencia regular entre preci…]
- "smc_confirmation_engine_safe_float": "_safe_float()" | kind=code-symbol | source=strategy/smc/confirmation_engine.py:L70 | neighbors=[confirmation_engine.py, _average_range(), candle_metrics(), detect_rsi_divergence(), evaluate_m5_confirmation()]

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-013.json

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
