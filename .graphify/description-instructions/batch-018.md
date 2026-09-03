# Node Description Batch 19 of 56

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

- "reporting_console_reporting_service_consolereportingservice_label": "._label()" | kind=code-symbol | source=reporting/console_reporting_service.py:L127 | neighbors=[ConsoleReportingService, .print_result(), .print_symbol_result(), ._reason()]
- "reporting_console_reporting_service_consolereportingservice_print_trade_fields": "._print_trade_fields()" | kind=code-symbol | source=reporting/console_reporting_service.py:L329 | neighbors=[ConsoleReportingService, .print_result(), .print_symbol_result(), ._fmt()]
- "reporting_console_reporting_service_consolereportingservice_reason": "._reason()" | kind=code-symbol | source=reporting/console_reporting_service.py:L322 | neighbors=[ConsoleReportingService, .print_result(), .print_symbol_result(), ._label()]
- "reporting_strategy_evaluation_build_strategy_evaluation": "build_strategy_evaluation()" | kind=code-symbol | source=reporting/strategy_evaluation.py:L33 | neighbors=[strategy_evaluation.py, _distribution(), _number(), main()]
- "reporting_trade_audit_excel_exporter": "trade_audit_excel_exporter.py" | kind=code-symbol | source=reporting/trade_audit_excel_exporter.py:L1 | neighbors=[realtime_dashboard.py, TradeAuditExcelExporter, test_v81_trade_audit_excel_export.py, test_v86_durable_trade_audit_export.py]
- "reporting_trade_audit_excel_exporter_tradeauditexcelexporter_safe_text": "._safe_text()" | kind=code-symbol | source=reporting/trade_audit_excel_exporter.py:L26 | neighbors=[TradeAuditExcelExporter, ._summary_frame(), ._timeline_frame(), ._view_frame()]
- "reporting_trade_report_exporter_tradereportexporter_build_entry_reason": "._build_entry_reason()" | kind=code-symbol | source=reporting/trade_report_exporter.py:L423 | neighbors=[TradeReportExporter, ._clean(), ._labels(), ._report_record()]
- "reporting_trade_report_exporter_tradereportexporter_classify_close": "._classify_close()" | kind=code-symbol | source=reporting/trade_report_exporter.py:L456 | neighbors=[TradeReportExporter, ._clean(), ._safe_number(), ._report_record()]
- "reporting_trade_report_exporter_tradereportexporter_clean": "._clean()" | kind=code-symbol | source=reporting/trade_report_exporter.py:L542 | neighbors=[TradeReportExporter, ._build_entry_reason(), ._classify_close(), ._report_record()]
- "risk_money_management_get_final_balance": "get_final_balance()" | kind=code-symbol | source=strategy/risk/money_management.py:L566 | neighbors=[money_management.py, validate_balance(), validate_dataframe(), Obtiene el balance final.      Utiliz…]
- "risk_money_management_run_money_management": "run_money_management()" | kind=code-symbol | source=strategy/risk/money_management.py:L938 | neighbors=[money_management.py, Ejecuta todo el proceso de Money Manage…, apply_money_management(), calculate_money_management_statistics()]
- "risk_money_management_validate_pnl": "validate_pnl()" | kind=code-symbol | source=strategy/risk/money_management.py:L96 | neighbors=[money_management.py, apply_money_management_to_trade(), Valida el PnL de una operación., update_balance()]
- "risk_money_manager_moneymanager_calculate_profit_loss": ".calculate_profit_loss()" | kind=code-symbol | source=risk/money_manager.py:L83 | neighbors=[MoneyManager, .calculate_risk_amount(), .process_trade(), Calcula el resultado monetario        …]
- "risk_money_manager_moneymanager_calculate_risk_amount": ".calculate_risk_amount()" | kind=code-symbol | source=risk/money_manager.py:L61 | neighbors=[MoneyManager, .calculate_profit_loss(), .process_trade(), Calcula cuánto dinero se arriesga     …]
- "risk_risk_manager_calculate_current_drawdown": "calculate_current_drawdown()" | kind=code-symbol | source=strategy/risk/risk_manager.py:L791 | neighbors=[risk_manager.py, validate_dataframe(), check_drawdown_limit(), Calcula el drawdown actual y máximo. …]
- "risk_risk_manager_calculate_current_risk": "calculate_current_risk()" | kind=code-symbol | source=strategy/risk/risk_manager.py:L502 | neighbors=[risk_manager.py, validate_positive_number(), evaluate_trade_risk(), Calcula el tamaño de posición y riesgo …]
- "risk_risk_manager_calculate_daily_loss": "calculate_daily_loss()" | kind=code-symbol | source=strategy/risk/risk_manager.py:L583 | neighbors=[risk_manager.py, validate_dataframe(), check_daily_loss_limit(), Calcula el PnL y la pérdida acumulada …]
- "risk_risk_manager_calculate_risk_reward": "calculate_risk_reward()" | kind=code-symbol | source=strategy/risk/risk_manager.py:L373 | neighbors=[risk_manager.py, validate_positive_number(), Calcula la relación Risk / Reward.   …, validate_risk_reward()]
- "risk_risk_manager_check_drawdown_limit": "check_drawdown_limit()" | kind=code-symbol | source=strategy/risk/risk_manager.py:L1169 | neighbors=[risk_manager.py, calculate_current_drawdown(), evaluate_trade_risk(), Verifica si el drawdown actual supera …]
- "risk_risk_manager_count_consecutive_losses": "count_consecutive_losses()" | kind=code-symbol | source=strategy/risk/risk_manager.py:L713 | neighbors=[risk_manager.py, validate_dataframe(), evaluate_trade_risk(), Cuenta las operaciones perdedoras conse…]
- "smc_h1_doji_extremes": "h1_doji_extremes.py" | kind=code-symbol | source=strategy/smc/h1_doji_extremes.py:L1 | neighbors=[detect_h1_extreme_doji(), _empty(), H1ExtremeDojiConfig, _safe_float()]
- "tests_test_console_reporting_service": "test_console_reporting_service.py" | kind=code-symbol | source=tests/test_console_reporting_service.py:L1 | neighbors=[console_reporting_service.py, test_normal_mode_hides_no_signal(), test_summary_counts_actions(), test_verbose_mode_prints_reason()]
- "tests_test_daemon_runner_extension_trade": "_trade()" | kind=code-symbol | source=tests/test_daemon_runner_extension.py:L83 | neighbors=[test_daemon_runner_extension.py, test_at_2r_no_continuation_closes_runne…, test_at_2r_profit_is_locked_at_1r_befor…, test_at_3r_profit_lock_advances_to_2r()]
- "tests_test_daemon_split_risk_management_test_daemon_pipeline_uses_harmonic_as_bonus_with_adaptive_75_gate_by_default": "test_daemon_pipeline_uses_harmonic_as_bonus_with_adaptive_75_gate_by_default()" | kind=code-symbol | source=tests/test_daemon_split_risk_management.py:L108 | neighbors=[test_daemon_split_risk_management.py, Executor, Provider, Repo]
- "tests_test_demo_daemon_integration_test_run_once_processes_and_syncs_and_exports": "test_run_once_processes_and_syncs_and_exports()" | kind=code-symbol | source=tests/test_demo_daemon_integration.py:L44 | neighbors=[test_demo_daemon_integration.py, FakeEngine, FakeReporting, FakeRepository]
- "tests_test_deriv_symbols": "test_deriv_symbols.py" | kind=code-symbol | source=tests/test_deriv_symbols.py:L1 | neighbors=[mt5_connector.py, main(), print_symbols(), search_symbols()]
- "tests_test_jump_strict_quality_gate": "test_jump_strict_quality_gate.py" | kind=code-symbol | source=tests/test_jump_strict_quality_gate.py:L1 | neighbors=[_engine(), test_jump_passes_only_with_reinforced_c…, test_jump_rejects_signal_missing_reject…, test_non_jump_is_not_affected()]
- "tests_test_jump_strict_quality_gate_engine": "_engine()" | kind=code-symbol | source=tests/test_jump_strict_quality_gate.py:L5 | neighbors=[test_jump_strict_quality_gate.py, test_jump_passes_only_with_reinforced_c…, test_jump_rejects_signal_missing_reject…, test_non_jump_is_not_affected()]
- "tests_test_live_demo_print_analysis_diagnostics": "print_analysis_diagnostics()" | kind=code-symbol | source=tests/test_live_demo.py:L832 | neighbors=[test_live_demo.py, main(), get_analysis(), get_diagnostics()]
- "tests_test_live_demo_print_execution_diagnostics": "print_execution_diagnostics()" | kind=code-symbol | source=tests/test_live_demo.py:L1032 | neighbors=[test_live_demo.py, main(), print_mapping(), Diagnóstico completo para resultados va…]
- "tests_test_live_demo_smoke_stops_lifecycle": "_Lifecycle" | kind=code-symbol | source=tests/test_live_demo_smoke_stops.py:L54 | neighbors=[test_live_demo_smoke_stops.py, LiveDemoSmokeTestConfig, LiveDemoSmokeTestService, .process_signal_with_executor()]
- "tests_test_live_demo_smoke_stops_reporting": "_Reporting" | kind=code-symbol | source=tests/test_live_demo_smoke_stops.py:L80 | neighbors=[test_live_demo_smoke_stops.py, LiveDemoSmokeTestConfig, LiveDemoSmokeTestService, test_smoke_uses_provider_stop_normaliza…]
- "tests_test_multi_timeframe_cache": "test_multi_timeframe_cache.py" | kind=code-symbol | source=tests/test_multi_timeframe_cache.py:L1 | neighbors=[CountingAnalyzer, CountingProvider, test_clear_stage_cache_forces_new_fetch…, test_stage_cache_reuses_data_and_pipeli…]
- "tests_test_multi_timeframe_sequence": "test_multi_timeframe_sequence.py" | kind=code-symbol | source=tests/test_multi_timeframe_sequence.py:L1 | neighbors=[_frame(), test_sequence_can_disable_m5_after_m15_…, test_sequence_can_fall_back_to_previous…, test_sequence_uses_latest_m15_when_requ…]
- "tests_test_multi_timeframe_sequence_frame": "_frame()" | kind=code-symbol | source=tests/test_multi_timeframe_sequence.py:L6 | neighbors=[test_multi_timeframe_sequence.py, test_sequence_can_disable_m5_after_m15_…, test_sequence_can_fall_back_to_previous…, test_sequence_uses_latest_m15_when_requ…]
- "tests_test_position_monitoring_service_create_sell_position": "create_sell_position()" | kind=code-symbol | source=tests/test_position_monitoring_service.py:L31 | neighbors=[test_position_monitoring_service.py, test_monitor_open_positions_processes_a…, test_monitor_sell_activates_break_even_…, test_monitor_sell_closes_at_stop_loss()]
- "tests_test_ready_to_ambiguous_transition_test_controlled_ready_to_enter_to_ambiguous": "test_controlled_ready_to_enter_to_ambiguous()" | kind=code-symbol | source=tests/test_ready_to_ambiguous_transition.py:L371 | neighbors=[test_ready_to_ambiguous_transition.py, ControlledDataProvider, .get_candles(), ControlledMultiTimeframeAnalyzer]
- "tests_test_ready_to_enter_transition_test_controlled_transition_to_ready_to_enter": "test_controlled_transition_to_ready_to_enter()" | kind=code-symbol | source=tests/test_ready_to_enter_transition.py:L476 | neighbors=[test_ready_to_enter_transition.py, Prueba completa:          H1 válido …, ControlledDataProvider, ControlledMultiTimeframeAnalyzer]
- "tests_test_ready_to_execution_transition_test_controlled_ready_to_enter_to_execution": "test_controlled_ready_to_enter_to_execution()" | kind=code-symbol | source=tests/test_ready_to_execution_transition.py:L371 | neighbors=[test_ready_to_execution_transition.py, ControlledDataProvider, .get_candles(), ControlledMultiTimeframeAnalyzer]
- "tests_test_ready_to_no_exit_transition_test_controlled_ready_to_enter_to_no_exit": "test_controlled_ready_to_enter_to_no_exit()" | kind=code-symbol | source=tests/test_ready_to_no_exit_transition.py:L552 | neighbors=[test_ready_to_no_exit_transition.py, ControlledDataProvider, .get_candles(), ControlledMultiTimeframeAnalyzer]

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-018.json

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
