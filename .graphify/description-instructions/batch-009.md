# Node Description Batch 10 of 56

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

- "tests_test_daemon_break_even_live_splitrepo": "SplitRepo" | kind=code-symbol | source=tests/test_daemon_break_even_live.py:L142 | neighbors=[test_daemon_break_even_live.py, LiveTradingConfig, LiveTradingEngine, Repo, .get_trade_by_execution_key(), .__init__()] | lang=en
- "tests_test_daemon_risk_target_policy_executor": "Executor" | kind=code-symbol | source=tests/test_daemon_risk_target_policy.py:L33 | neighbors=[test_daemon_risk_target_policy.py, LiveTradingConfig, LiveTradingEngine, .assert_demo_account(), .calculate_volume(), .normalize_market_stops()] | lang=en
- "tests_test_daemon_risk_target_policy_provider": "Provider" | kind=code-symbol | source=tests/test_daemon_risk_target_policy.py:L20 | neighbors=[test_daemon_risk_target_policy.py, LiveTradingConfig, LiveTradingEngine, .ensure_symbol(), .get_current_tick(), .resolve_symbol()] | lang=en
- "tests_test_daemon_runner_extension_repo": "Repo" | kind=code-symbol | source=tests/test_daemon_runner_extension.py:L11 | neighbors=[test_daemon_runner_extension.py, _engine(), LiveTradingConfig, LiveTradingEngine, RunnerExtensionDecision, .__init__()] | lang=en
- "tests_test_daemon_single_entry_fallback": "test_daemon_single_entry_fallback.py" | kind=code-symbol | source=tests/test_daemon_single_entry_fallback.py:L1 | neighbors=[Analyzer, _engine(), FallbackExecutor, Provider, Repo, test_single_fallback_is_rejected_when_i…] | lang=en
- "tests_test_daemon_single_entry_fallback_provider": "Provider" | kind=code-symbol | source=tests/test_daemon_single_entry_fallback.py:L17 | neighbors=[test_daemon_single_entry_fallback.py, _engine(), LiveTradingConfig, LiveTradingEngine, .ensure_symbol(), .get_current_tick()] | lang=en
- "tests_test_daemon_split_risk_management": "test_daemon_split_risk_management.py" | kind=code-symbol | source=tests/test_daemon_split_risk_management.py:L1 | neighbors=[Analyzer, Executor, Provider, Repo, test_daemon_pipeline_uses_harmonic_as_b…, test_one_percent_operation_is_split_int…] | lang=en
- "tests_test_demo_daemon_integration_analyzer": "Analyzer" | kind=code-symbol | source=tests/test_demo_daemon_integration.py:L148 | neighbors=[test_demo_daemon_integration.py, LiveTradingConfig, LiveTradingEngine, TradeReportingService, .analyze_symbol(), TradeLifecycle] | lang=en
- "tests_test_demo_daemon_integration_test_execution_path_uses_lifecycle_manager_when_configured": "test_execution_path_uses_lifecycle_manager_when_configured()" | kind=code-symbol | source=tests/test_demo_daemon_integration.py:L162 | neighbors=[test_demo_daemon_integration.py, LiveTradingEngine, Analyzer, ExecutionRepo, Executor, FakeLifecycleManager] | lang=en
- "tests_test_live_demo_origin": "test_live_demo_origin.py" | kind=code-symbol | source=tests/test_live_demo_origin.py:L1 | neighbors=[mt5_connector.py, mt5_data.py, symbol_discovery.py, repository.py, main(), print_analysis_diagnostics()] | lang=en
- "tests_test_live_demo_rationale_1033": "Diagnóstico completo para resultados validados y rechazados.      Especialmente" | kind=entity | source=tests/test_live_demo.py:L1033 | neighbors=[MT5Connector, MT5DataProvider, DerivSymbolDiscovery, TradingRepository, LiveTradingConfig, LiveTradingEngine] | lang=es
- "tests_test_live_demo_rationale_1146": "Imprime los valores principales disponibles.      No depende de que action sea D" | kind=entity | source=tests/test_live_demo.py:L1146 | neighbors=[MT5Connector, MT5DataProvider, DerivSymbolDiscovery, TradingRepository, LiveTradingConfig, LiveTradingEngine] | lang=es
- "tests_test_live_demo_rationale_118": "Imprime una transición uniforme.      Ejemplo:        [PASS] H1_CONTEXT" | kind=entity | source=tests/test_live_demo.py:L118 | neighbors=[MT5Connector, MT5DataProvider, DerivSymbolDiscovery, TradingRepository, LiveTradingConfig, LiveTradingEngine] | lang=en
- "tests_test_live_demo_rationale_138": "Reconstruye visualmente el flujo completo:          START           ->         H" | kind=entity | source=tests/test_live_demo.py:L138 | neighbors=[MT5Connector, MT5DataProvider, DerivSymbolDiscovery, TradingRepository, LiveTradingConfig, LiveTradingEngine] | lang=es
- "tests_test_live_demo_rationale_16": "Imprime cualquier diccionario de diagnóstico sin depender de     nombres exactos" | kind=entity | source=tests/test_live_demo.py:L16 | neighbors=[MT5Connector, MT5DataProvider, DerivSymbolDiscovery, TradingRepository, LiveTradingConfig, LiveTradingEngine] | lang=nl
- "tests_test_live_demo_rationale_77": "Devuelve el bloque analysis cuando existe.      En resultados rechazados durante" | kind=entity | source=tests/test_live_demo.py:L77 | neighbors=[MT5Connector, MT5DataProvider, DerivSymbolDiscovery, TradingRepository, LiveTradingConfig, LiveTradingEngine] | lang=es
- "tests_test_live_demo_rationale_91": "Busca diagnostics en ambos formatos posibles:      1. result[\"diagnostics\"]" | kind=entity | source=tests/test_live_demo.py:L91 | neighbors=[MT5Connector, MT5DataProvider, DerivSymbolDiscovery, TradingRepository, LiveTradingConfig, LiveTradingEngine] | lang=en
- "tests_test_live_demo_smoke_stops_lifecyclemanager": "_LifecycleManager" | kind=code-symbol | source=tests/test_live_demo_smoke_stops.py:L59 | neighbors=[test_live_demo_smoke_stops.py, LiveDemoSmokeTestConfig, LiveDemoSmokeTestService, .close_execution(), .__init__(), .process_signal_with_executor()] | lang=en
- "tests_test_live_end_to_end_dry_run_fakeprovider": "FakeProvider" | kind=code-symbol | source=tests/test_live_end_to_end_dry_run.py:L6 | neighbors=[test_live_end_to_end_dry_run.py, LiveTradingConfig, LiveTradingEngine, .ensure_symbol(), .get_current_tick(), .resolve_symbol()] | lang=en
- "tests_test_multi_timeframe_cache_countingprovider": "CountingProvider" | kind=code-symbol | source=tests/test_multi_timeframe_cache.py:L6 | neighbors=[test_multi_timeframe_cache.py, MultiTimeframeAnalyzer, MultiTimeframeConfig, .get_candles(), .__init__(), test_clear_stage_cache_forces_new_fetch…] | lang=en
- "tests_test_orb_new_york_strategy_fakeprovider": "FakeProvider" | kind=code-symbol | source=tests/test_orb_new_york_strategy.py:L15 | neighbors=[test_orb_new_york_strategy.py, NewYorkORBStrategy, ORBConfig, .get_candles(), .get_current_tick(), .__init__()] | lang=en
- "tests_test_orb_new_york_strategy_session_candles": "_session_candles()" | kind=code-symbol | source=tests/test_orb_new_york_strategy.py:L28 | neighbors=[test_orb_new_york_strategy.py, test_orb_builds_15_minute_range_before_…, test_orb_buy_requires_m5_breakout_then_…, test_orb_does_not_run_on_weekends(), test_orb_is_disabled_after_new_york_ses…, test_orb_rejects_breakout_without_retes…] | lang=en
- "tests_test_position_monitoring_service_create_buy_position": "create_buy_position()" | kind=code-symbol | source=tests/test_position_monitoring_service.py:L18 | neighbors=[test_position_monitoring_service.py, test_closed_position_cannot_be_monitore…, test_monitor_buy_activates_break_even_a…, test_monitor_buy_closes_at_break_even_a…, test_monitor_buy_closes_at_take_profit(), test_monitor_buy_updates_price_without_…] | lang=en
- "tests_test_ready_to_enter_transition_controlledmultitimeframeanalyzer": "ControlledMultiTimeframeAnalyzer" | kind=code-symbol | source=tests/test_ready_to_enter_transition.py:L309 | neighbors=[test_ready_to_enter_transition.py, MultiTimeframeAnalyzer, MultiTimeframeConfig, MultiTimeframeAnalyzer, ._run_pipeline(), Analizador controlado.      La prueba…] | lang=en
- "tests_test_trade_lifecycle_full_integration_controlledmultitimeframeanalyzer": "ControlledMultiTimeframeAnalyzer" | kind=code-symbol | source=tests/test_trade_lifecycle_full_integration.py:L227 | neighbors=[test_trade_lifecycle_full_integration.py, MultiTimeframeAnalyzer, MultiTimeframeConfig, MultiTimeframeAnalyzer, ._run_pipeline(), TradeLifecycleManager] | lang=en
- "tests_test_trade_lifecycle_integration_controlledlifecycledataprovider": "ControlledLifecycleDataProvider" | kind=code-symbol | source=tests/test_trade_lifecycle_integration.py:L50 | neighbors=[test_trade_lifecycle_integration.py, MultiTimeframeAnalyzer, MultiTimeframeConfig, ._build_m5_candles(), .get_candles(), .__init__()] | lang=en
- "tests_test_trade_lifecycle_paper_integration_signal": "signal()" | kind=code-symbol | source=tests/test_trade_lifecycle_paper_integration.py:L14 | neighbors=[test_trade_lifecycle_paper_integration.…, test_full_paper_lifecycle_break_even_st…, test_full_paper_lifecycle_open_and_brea…, test_full_paper_lifecycle_stop_loss_to_…, test_full_paper_lifecycle_take_profit_t…, test_monitor_multiple_active_lifecycles…] | lang=en
- "tests_test_v100_entry_quarantine_winrate_analyzer": "_Analyzer" | kind=code-symbol | source=tests/test_v100_entry_quarantine_winrate.py:L121 | neighbors=[test_v100_entry_quarantine_winrate.py, LiveTradingConfig, LiveTradingEngine, ChartPatternConfig, M5ConfirmationConfig, .analyze_symbol()] | lang=en
- "tests_test_v59_synthetic_family_multiprocess": "test_v59_synthetic_family_multiprocess.py" | kind=code-symbol | source=tests/test_v59_synthetic_family_multiprocess.py:L1 | neighbors=[main.py, test_coordinator_spawns_per_profile(), test_exact_six(), test_launcher(), test_legacy_aggregate_not_in_split(), test_split_guard()] | lang=en
- "tests_test_v62_chart_pattern_confirmations": "test_v62_chart_pattern_confirmations.py" | kind=code-symbol | source=tests/test_v62_chart_pattern_confirmations.py:L1 | neighbors=[repository.py, _double_bottom(), test_account_page_exposes_persistent_co…, test_double_bottom_is_detected_and_alig…, test_entry_confirmation_audit_is_persis…, test_pattern_is_soft_confluence_by_defa…] | lang=en
- "tests_test_v65_smc_two_leg_tp3_protection_repo": "Repo" | kind=code-symbol | source=tests/test_v65_smc_two_leg_tp3_protection.py:L9 | neighbors=[test_v65_smc_two_leg_tp3_protection.py, _engine(), LiveTradingConfig, LiveTradingEngine, RunnerExtensionDecision, .__init__()] | lang=en
- "tests_test_v67_live_entry_vs_now": "test_v67_live_entry_vs_now.py" | kind=code-symbol | source=tests/test_v67_live_entry_vs_now.py:L1 | neighbors=[Analyzer, Repo, test_current_strategy_view_extracts_liv…, test_current_strategy_view_normalizes_w…, test_dashboard_prioritizes_persisted_cu…, test_live_refresh_is_independent_from_3…] | lang=en
- "tests_test_v73_forex_progressive_runner_repo": "Repo" | kind=code-symbol | source=tests/test_v73_forex_progressive_runner.py:L8 | neighbors=[test_v73_forex_progressive_runner.py, _engine(), LiveTradingConfig, LiveTradingEngine, RunnerExtensionDecision, .__init__()] | lang=en
- "tests_test_v79_universal_open_position_audit": "test_v79_universal_open_position_audit.py" | kind=code-symbol | source=tests/test_v79_universal_open_position_audit.py:L1 | neighbors=[_engine(), Repo, test_dashboard_prefers_current_strategy…, test_live_market_snapshot_persists_for_…, test_live_market_snapshot_persists_for_…, test_live_market_snapshot_persists_for_…] | lang=en
- "tests_test_v82_synthetic_selection_recovery": "test_v82_synthetic_selection_recovery.py" | kind=code-symbol | source=tests/test_v82_synthetic_selection_recovery.py:L1 | neighbors=[main.py, repository.py, test_empty_cycle_is_reported_as_degrade…, test_empty_synthetic_profile_is_recover…, test_forex_without_candles_reports_data…, test_forex_without_new_m5_bar_is_waitin…] | lang=en
- "tests_test_v87_gold_asia_new_york_session": "test_v87_gold_asia_new_york_session.py" | kind=code-symbol | source=tests/test_v87_gold_asia_new_york_session.py:L1 | neighbors=[main.py, _engine(), test_gold_entry_gate_does_not_affect_fo…, test_gold_profile_is_independent_and_us…, test_gold_window_opens_at_tokyo_0900_an…, test_gold_window_respects_new_york_wint…] | lang=en
- "trade_lifecycle_manager_tradelifecycle_is_final": ".is_final()" | kind=code-symbol | source=trade_lifecycle_manager.py:L100 | neighbors=[TradeLifecycle, .close_execution(), .execute(), .execute_with_executor(), .get_completed_trades(), .monitor_execution()] | lang=en
- "trade_lifecycle_manager_tradelifecyclemanager_close_execution": ".close_execution()" | kind=code-symbol | source=trade_lifecycle_manager.py:L459 | neighbors=[Cierra una posición activa mediante el …, TradeLifecycleManager, .is_final(), ._notify_reporting(), ._record_final_lifecycle(), ._result_from_exit_reason()] | lang=en
- "trade_lifecycle_manager_tradelifecyclemanager_execute": ".execute()" | kind=code-symbol | source=trade_lifecycle_manager.py:L239 | neighbors=[TradeLifecycleManager, .is_final(), ._apply_simulation_result(), ._notify_reporting(), ._record_final_lifecycle(), ._validate_candles()] | lang=en
- "trade_lifecycle_manager_tradelifecyclemanager_monitor_execution": ".monitor_execution()" | kind=code-symbol | source=trade_lifecycle_manager.py:L497 | neighbors=[TradeLifecycleManager, .is_final(), ._notify_reporting(), ._record_final_lifecycle(), ._result_from_exit_reason(), ._state_from_exit_reason()] | lang=en

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-009.json

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
