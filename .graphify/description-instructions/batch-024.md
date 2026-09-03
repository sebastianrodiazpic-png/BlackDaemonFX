# Node Description Batch 25 of 56

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

- "smc_harmonic_patterns_evaluate_pattern": "_evaluate_pattern()" | kind=code-symbol | source=strategy/smc/harmonic_patterns.py:L72 | neighbors=[harmonic_patterns.py, detect_harmonic_confirmation(), _ratio()]
- "smc_ob_quality_evaluate_order_block": "evaluate_order_block()" | kind=code-symbol | source=strategy/smc/ob_quality.py:L170 | neighbors=[ob_quality.py, calculate_ob_score(), get_ob_grade()]
- "smc_premium_discount": "premium_discount.py" | kind=code-symbol | source=strategy/smc/premium_discount.py:L1 | neighbors=[calculate_premium_discount(), is_bearish_ob_in_premium(), is_bullish_ob_in_discount()]
- "smc_trade_simulator_simulate_trade": "simulate_trade()" | kind=code-symbol | source=strategy/smc/trade_simulator.py:L4 | neighbors=[trade_simulator.py, Simula una operación utilizando las vel…, simulate_trades()]
- "smc_trade_simulator_simulate_trades": "simulate_trades()" | kind=code-symbol | source=strategy/smc/trade_simulator.py:L296 | neighbors=[trade_simulator.py, Simula múltiples operaciones y agrega e…, simulate_trade()]
- "storage_account_page_syntax_test_audithtml": "auditHtml()" | kind=code-symbol | source=storage/account_page_syntax_test.js:L1 | neighbors=[account_page_syntax_test.js, e(), num()]
- "storage_account_page_syntax_test_e": "e()" | kind=code-symbol | source=storage/account_page_syntax_test.js:L1 | neighbors=[account_page_syntax_test.js, auditHtml(), render()]
- "storage_account_page_syntax_test_num": "num()" | kind=code-symbol | source=storage/account_page_syntax_test.js:L1 | neighbors=[account_page_syntax_test.js, auditHtml(), render()]
- "tests_test_backtest_money_management": "test_backtest_money_management.py" | kind=code-symbol | source=tests/test_backtest_money_management.py:L1 | neighbors=[backtest_money_management.py, backtest_storage.py, main()]
- "tests_test_backtest_print_trades": "print_trades()" | kind=code-symbol | source=tests/test_backtest.py:L84 | neighbors=[test_backtest.py, format_number(), run_backtest()]
- "tests_test_confirmation_engine_test_adaptive_75_mode_accepts_when_only_secondary_confirmation_is_missing": "test_adaptive_75_mode_accepts_when_only_secondary_confirmation_is_missing()" | kind=code-symbol | source=tests/test_confirmation_engine.py:L48 | neighbors=[test_confirmation_engine.py, _data(), _setup()]
- "tests_test_confirmation_engine_test_adaptive_75_mode_never_overrides_a_critical_smc_failure": "test_adaptive_75_mode_never_overrides_a_critical_smc_failure()" | kind=code-symbol | source=tests/test_confirmation_engine.py:L73 | neighbors=[test_confirmation_engine.py, _data(), _setup()]
- "tests_test_confirmation_engine_test_adaptive_80_decision_code_reflects_current_threshold": "test_adaptive_80_decision_code_reflects_current_threshold()" | kind=code-symbol | source=tests/test_confirmation_engine.py:L103 | neighbors=[test_confirmation_engine.py, _data(), _setup()]
- "tests_test_confirmation_engine_test_high_quality_long_confirmation_is_accepted": "test_high_quality_long_confirmation_is_accepted()" | kind=code-symbol | source=tests/test_confirmation_engine.py:L24 | neighbors=[test_confirmation_engine.py, _data(), _setup()]
- "tests_test_confirmation_engine_test_repeated_order_block_touch_is_rejected": "test_repeated_order_block_touch_is_rejected()" | kind=code-symbol | source=tests/test_confirmation_engine.py:L37 | neighbors=[test_confirmation_engine.py, _data(), _setup()]
- "tests_test_daemon_explainable_report": "test_daemon_explainable_report.py" | kind=code-symbol | source=tests/test_daemon_explainable_report.py:L1 | neighbors=[trade_report_exporter.py, DummyRepository, test_report_enrichment_documents_entry_…]
- "tests_test_daemon_explainable_report_dummyrepository": "DummyRepository" | kind=code-symbol | source=tests/test_daemon_explainable_report.py:L7 | neighbors=[test_daemon_explainable_report.py, TradeReportExporter, test_report_enrichment_documents_entry_…]
- "tests_test_daemon_progress": "test_daemon_progress.py" | kind=code-symbol | source=tests/test_daemon_progress.py:L1 | neighbors=[Engine, Repo, test_process_symbols_reports_each_symbo…]
- "tests_test_daemon_progress_test_process_symbols_reports_each_symbol_immediately": "test_process_symbols_reports_each_symbol_immediately()" | kind=code-symbol | source=tests/test_daemon_progress.py:L16 | neighbors=[test_daemon_progress.py, Engine, Repo]
- "tests_test_daemon_runner_extension_test_at_2r_no_continuation_closes_runner_after_locking_profit": "test_at_2r_no_continuation_closes_runner_after_locking_profit()" | kind=code-symbol | source=tests/test_daemon_runner_extension.py:L127 | neighbors=[test_daemon_runner_extension.py, _engine(), _trade()]
- "tests_test_daemon_runner_extension_test_at_2r_profit_is_locked_at_1r_before_extending": "test_at_2r_profit_is_locked_at_1r_before_extending()" | kind=code-symbol | source=tests/test_daemon_runner_extension.py:L99 | neighbors=[test_daemon_runner_extension.py, _engine(), _trade()]
- "tests_test_daemon_runner_extension_test_at_3r_profit_lock_advances_to_2r": "test_at_3r_profit_lock_advances_to_2r()" | kind=code-symbol | source=tests/test_daemon_runner_extension.py:L153 | neighbors=[test_daemon_runner_extension.py, _engine(), _trade()]
- "tests_test_daemon_single_entry_fallback_test_single_fallback_is_rejected_when_it_also_exceeds_one_percent": "test_single_fallback_is_rejected_when_it_also_exceeds_one_percent()" | kind=code-symbol | source=tests/test_daemon_single_entry_fallback.py:L97 | neighbors=[test_daemon_single_entry_fallback.py, _engine(), FallbackExecutor]
- "tests_test_daemon_single_entry_fallback_test_split_risk_failure_falls_back_to_one_safe_entry": "test_split_risk_failure_falls_back_to_one_safe_entry()" | kind=code-symbol | source=tests/test_daemon_single_entry_fallback.py:L82 | neighbors=[test_daemon_single_entry_fallback.py, _engine(), FallbackExecutor]
- "tests_test_deriv_symbols_main": "main()" | kind=code-symbol | source=tests/test_deriv_symbols.py:L51 | neighbors=[test_deriv_symbols.py, print_symbols(), search_symbols()]
- "tests_test_deriv_symbols_search_symbols": "search_symbols()" | kind=code-symbol | source=tests/test_deriv_symbols.py:L21 | neighbors=[test_deriv_symbols.py, main(), Busca instrumentos disponibles en MetaT…]
- "tests_test_divergence_confirmation": "test_divergence_confirmation.py" | kind=code-symbol | source=tests/test_divergence_confirmation.py:L1 | neighbors=[_frame(), test_bullish_regular_divergence_detecte…, test_divergence_is_optional_confluence_…]
- "tests_test_execution_preflight_service_test_preflight_reports_ready": "test_preflight_reports_ready()" | kind=code-symbol | source=tests/test_execution_preflight_service.py:L38 | neighbors=[test_execution_preflight_service.py, FakeProvider, FakeRepository]
- "tests_test_harmonic_patterns": "test_harmonic_patterns.py" | kind=code-symbol | source=tests/test_harmonic_patterns.py:L1 | neighbors=[make_swings(), test_harmonic_detector_returns_diagnost…, test_harmonic_disabled_is_explicit()]
- "tests_test_harmonic_patterns_make_swings": "make_swings()" | kind=code-symbol | source=tests/test_harmonic_patterns.py:L6 | neighbors=[test_harmonic_patterns.py, test_harmonic_detector_returns_diagnost…, test_harmonic_disabled_is_explicit()]
- "tests_test_live_demo_origin_main": "main()" | kind=code-symbol | source=tests/test_live_demo_origin.py:L55 | neighbors=[test_live_demo_origin.py, print_analysis_diagnostics(), print_position_diagnostics()]
- "tests_test_live_demo_print_mapping": "print_mapping()" | kind=code-symbol | source=tests/test_live_demo.py:L15 | neighbors=[test_live_demo.py, print_execution_diagnostics(), Imprime cualquier diccionario de diagnó…]
- "tests_test_live_demo_print_trade_values": "print_trade_values()" | kind=code-symbol | source=tests/test_live_demo.py:L1145 | neighbors=[test_live_demo.py, main(), Imprime los valores principales disponi…]
- "tests_test_live_demo_print_transition": "print_transition()" | kind=code-symbol | source=tests/test_live_demo.py:L117 | neighbors=[test_live_demo.py, print_transition_trace(), Imprime una transición uniforme.      E…]
- "tests_test_live_demo_smoke_stops_exporter": "_Exporter" | kind=code-symbol | source=tests/test_live_demo_smoke_stops.py:L76 | neighbors=[test_live_demo_smoke_stops.py, LiveDemoSmokeTestConfig, LiveDemoSmokeTestService]
- "tests_test_live_execution_helpers": "test_live_execution_helpers.py" | kind=code-symbol | source=tests/test_live_execution_helpers.py:L1 | neighbors=[mt5_execution.py, test_min_volume_does_not_force_excess_r…, test_normalize_volume_rounds_down_to_st…]
- "tests_test_main_symbol_selection_fakeinstrumentmanager": "FakeInstrumentManager" | kind=code-symbol | source=tests/test_main_symbol_selection.py:L23 | neighbors=[test_main_symbol_selection.py, .get_active_symbols(), .__init__()]
- "tests_test_money_management_get_final_balance": "get_final_balance()" | kind=code-symbol | source=tests/test_money_management.py:L81 | neighbors=[test_money_management.py, main(), Obtiene el balance final de manera segu…]
- "tests_test_mt5_connection": "test_mt5_connection.py" | kind=code-symbol | source=tests/test_mt5_connection.py:L1 | neighbors=[mt5_connection.py, mt5_data.py, main()]
- "tests_test_multi_timeframe_cache_test_clear_stage_cache_forces_new_fetch_and_pipeline": "test_clear_stage_cache_forces_new_fetch_and_pipeline()" | kind=code-symbol | source=tests/test_multi_timeframe_cache.py:L54 | neighbors=[test_multi_timeframe_cache.py, CountingAnalyzer, CountingProvider]

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-024.json

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
