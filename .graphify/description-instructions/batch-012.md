# Node Description Batch 13 of 56

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

- "tests_test_trade_lifecycle_integration_controlledlifecycleanalyzer": "ControlledLifecycleAnalyzer" | kind=code-symbol | source=tests/test_trade_lifecycle_integration.py:L541 | neighbors=[test_trade_lifecycle_integration.py, MultiTimeframeAnalyzer, MultiTimeframeConfig, MultiTimeframeAnalyzer, ._run_pipeline(), run_lifecycle()]
- "tests_test_trade_lifecycle_integration_run_lifecycle": "run_lifecycle()" | kind=code-symbol | source=tests/test_trade_lifecycle_integration.py:L735 | neighbors=[test_trade_lifecycle_integration.py, ControlledLifecycleAnalyzer, ControlledLifecycleDataProvider, .get_candles(), create_config(), test_trade_lifecycle_integration()]
- "tests_test_v58_synthetics_split_dashboard": "test_v58_synthetics_split_dashboard.py" | kind=code-symbol | source=tests/test_v58_synthetics_split_dashboard.py:L1 | neighbors=[main.py, test_coordinator_dashboard_is_not_condi…, test_coordinator_starts_and_stops_one_c…, test_split_profiles_are_exactly_six(), test_synthetics_split_launcher_enables_…, test_workers_still_do_not_start_individ…]
- "tests_test_v60_split_enforced": "test_v60_split_enforced.py" | kind=code-symbol | source=tests/test_v60_split_enforced.py:L1 | neighbors=[main.py, test_family_architecture_guard_still_pa…, test_historical_daemon_aliases_route_to…, test_legacy_runtime_is_superseded_by_co…, test_legacy_synthetic_daemon_is_not_ind…, test_split_still_exact_six()]
- "tests_test_v64_account_ui_fix": "test_v64_account_ui_fix.py" | kind=code-symbol | source=tests/test_v64_account_ui_fix.py:L1 | neighbors=[account_metrics.py, repository.py, test_account_page_fetch_checks_http_sta…, test_account_page_javascript_is_valid(), test_account_page_keeps_persistent_conf…, test_account_payload_contains_db_diagno…]
- "tests_test_v65_smc_two_leg_tp3_protection_provider": "Provider" | kind=code-symbol | source=tests/test_v65_smc_two_leg_tp3_protection.py:L16 | neighbors=[test_v65_smc_two_leg_tp3_protection.py, _engine(), LiveTradingConfig, LiveTradingEngine, RunnerExtensionDecision, .get_candles()]
- "tests_test_v65_smc_two_leg_tp3_protection_trade": "_trade()" | kind=code-symbol | source=tests/test_v65_smc_two_leg_tp3_protection.py:L72 | neighbors=[test_v65_smc_two_leg_tp3_protection.py, test_smc_at_2r_locks_1r_then_extends_on…, test_smc_at_2r_without_continuation_clo…, test_smc_at_3r_can_extend_to_tp4_with_2…, test_smc_at_3r_without_continuation_clo…, test_smc_between_tp2_and_tp3_advances_p…]
- "tests_test_v66_smc_tp4_be_plus2_provider": "Provider" | kind=code-symbol | source=tests/test_v66_smc_tp4_be_plus2.py:L33 | neighbors=[test_v66_smc_tp4_be_plus2.py, _engine(), LiveTradingConfig, LiveTradingEngine, RunnerExtensionDecision, .get_candles()]
- "tests_test_v69_forex_event_scheduler_candleprovider": "CandleProvider" | kind=code-symbol | source=tests/test_v69_forex_event_scheduler.py:L35 | neighbors=[test_v69_forex_event_scheduler.py, LiveTradingConfig, LiveTradingEngine, .get_candles(), .__init__(), _event_engine()]
- "tests_test_v72_chart_conflict_explained": "test_v72_chart_conflict_explained.py" | kind=code-symbol | source=tests/test_v72_chart_conflict_explained.py:L1 | neighbors=[_mixed_structure(), test_account_keeps_conflict_explanation…, test_conflict_explanation_compares_supp…, test_dashboard_explains_both_sides_of_c…, test_live_current_view_preserves_confli…, test_stronger_opposing_pattern_is_ident…]
- "tests_test_v73_forex_progressive_runner_provider": "Provider" | kind=code-symbol | source=tests/test_v73_forex_progressive_runner.py:L15 | neighbors=[test_v73_forex_progressive_runner.py, _engine(), LiveTradingConfig, LiveTradingEngine, RunnerExtensionDecision, .get_candles()]
- "tests_test_v76_unified_multibot_orb_htf_fakemtf": "FakeMTF" | kind=code-symbol | source=tests/test_v76_unified_multibot_orb_htf.py:L7 | neighbors=[test_v76_unified_multibot_orb_htf.py, _engine(), LiveTradingConfig, LiveTradingEngine, .analyze_symbol(), .__init__()]
- "tests_test_v77_hybrid_multibot_fast_front": "test_v77_hybrid_multibot_fast_front.py" | kind=code-symbol | source=tests/test_v77_hybrid_multibot_fast_front.py:L1 | neighbors=[test_browser_polling_is_reduced(), test_dashboard_has_short_full_snapshot_…, test_multi_bot_default_returns_to_multi…, test_orb_htf_context_is_preserved_after…, test_startup_warns_about_parallel_daemo…, test_unified_multibot_is_explicit_exper…]
- "tests_test_v79_universal_open_position_audit_repo": "Repo" | kind=code-symbol | source=tests/test_v79_universal_open_position_audit.py:L7 | neighbors=[test_v79_universal_open_position_audit.…, _engine(), LiveTradingConfig, LiveTradingEngine, .__init__(), .upsert_trade_visual_audit()]
- "tests_test_v93_latency_optimization": "test_v93_latency_optimization.py" | kind=code-symbol | source=tests/test_v93_latency_optimization.py:L1 | neighbors=[engine(), Repo, Reporting, test_coordinated_worker_sync_never_writ…, test_pre_execution_sync_skips_mt5_witho…, test_standalone_auto_export_remains_com…]
- "tests_test_v95_analysis_invalidation_exit_engine_with_view": "engine_with_view()" | kind=code-symbol | source=tests/test_v95_analysis_invalidation_exit.py:L15 | neighbors=[test_v95_analysis_invalidation_exit.py, Repo, test_recovery_protection_closes_after_p…, test_same_evaluation_does_not_inflate_c…, test_two_distinct_invalid_analyses_clos…, test_valid_current_analysis_resets_stre…]
- "tests_test_v95_analysis_invalidation_exit_repo": "Repo" | kind=code-symbol | source=tests/test_v95_analysis_invalidation_exit.py:L7 | neighbors=[test_v95_analysis_invalidation_exit.py, engine_with_view(), LiveTradingConfig, LiveTradingEngine, .__init__(), .update_trade()]
- "trade_lifecycle_manager_tradelifecyclemanager_create_from_signal": ".create_from_signal()" | kind=code-symbol | source=trade_lifecycle_manager.py:L191 | neighbors=[TradeLifecycleManager, TradeLifecycle, ._get_timeframe(), ._validate_signal(), .process_signal(), .process_signal_with_executor()]
- "trade_lifecycle_manager_tradelifecyclemanager_notify_reporting": "._notify_reporting()" | kind=code-symbol | source=trade_lifecycle_manager.py:L580 | neighbors=[Publica cambios relevantes del lifecycl…, TradeLifecycleManager, .close_execution(), .execute(), .execute_with_executor(), .monitor_execution()]
- "app_main_multibotinstanceguard_release": ".release()" | kind=code-symbol | source=app/main.py:L1683 | neighbors=[_acquire_multibot_instance_guard(), main(), _MultiBotInstanceGuard, ._owner(), run_database_maintenance()]
- "app_main_resolve_symbols": "_resolve_symbols()" | kind=code-symbol | source=app/main.py:L70 | neighbors=[main.py, Resuelve los símbolos después de conect…, _resolve_live_symbols(), _normalize_categories(), run_collector()]
- "app_main_resolve_symbols_for_profile_shared": "_resolve_symbols_for_profile_shared()" | kind=code-symbol | source=app/main.py:L1197 | neighbors=[main.py, Resuelve el universo de un perfil usand…, _selection_profile_for_bot(), _stable_symbol_shard(), run_unified_multibot_daemon()]
- "app_main_run_database_maintenance": "run_database_maintenance()" | kind=code-symbol | source=app/main.py:L2309 | neighbors=[main.py, main(), Mantenimiento manual seguro para compac…, _acquire_multibot_instance_guard(), .release()]
- "backtesting_trade_simulator_simulate_trade": "simulate_trade()" | kind=code-symbol | source=backtesting/trade_simulator.py:L125 | neighbors=[trade_simulator.py, Simula una operación utilizando las vel…, simulate_all_trades(), calculate_planned_rr(), calculate_realized_rr()]
- "brokers_mt5_data_mt5dataprovider_get_candles": ".get_candles()" | kind=code-symbol | source=brokers/mt5_data.py:L280 | neighbors=[MT5DataProvider, ._ensure_connection(), .ensure_symbol(), .get_timeframe(), .get_last_closed_candle()]
- "brokers_mt5_execution_back_mt5executionprovider_allowed_fillings": "._allowed_fillings()" | kind=code-symbol | source=brokers/mt5_execution.back.py:L325 | neighbors=[MT5ExecutionProvider, .check_market_order(), .place_market_order(), ._symbol_filling_candidates(), Convierte el bitmask SYMBOL_FILLING_* a…]
- "brokers_mt5_execution_back_mt5executionprovider_calculate_volume": ".calculate_volume()" | kind=code-symbol | source=brokers/mt5_execution.back.py:L101 | neighbors=[MT5ExecutionProvider, MT5ExecutionError, ._ensure(), .normalize_volume(), .symbol_spec()]
- "brokers_mt5_execution_back_mt5executionprovider_get_symbol_constraints": ".get_symbol_constraints()" | kind=code-symbol | source=brokers/mt5_execution.back.py:L394 | neighbors=[MT5ExecutionProvider, ._ensure(), ._minimum_stop_distance(), .symbol_spec(), Devuelve las restricciones reales infor…]
- "brokers_mt5_execution_back_mt5executionprovider_normalize_volume": ".normalize_volume()" | kind=code-symbol | source=brokers/mt5_execution.back.py:L74 | neighbors=[MT5ExecutionProvider, .calculate_volume(), .check_market_order(), MT5ExecutionError, .place_market_order()]
- "brokers_mt5_execution_mt5executionprovider_calculate_risk_amount": ".calculate_risk_amount()" | kind=code-symbol | source=brokers/mt5_execution.py:L900 | neighbors=[MT5ExecutionProvider, MT5ExecutionError, ._ensure(), .calculate_volume(), Calcula la pérdida monetaria teórica us…]
- "brokers_mt5_execution_mt5executionprovider_check_market_order": ".check_market_order()" | kind=code-symbol | source=brokers/mt5_execution.py:L776 | neighbors=[MT5ExecutionProvider, ._build_market_request_base(), ._ensure(), ._run_order_check_with_fallback(), Ejecuta order_check sin abrir una opera…]
- "brokers_mt5_execution_mt5executionprovider_ensure_symbol": ".ensure_symbol()" | kind=code-symbol | source=brokers/mt5_execution.py:L86 | neighbors=[MT5ExecutionProvider, MT5ExecutionError, ._ensure(), .symbol_spec(), Asegura que el símbolo exista y esté se…]
- "brokers_mt5_execution_mt5executionprovider_normalize_market_stops": ".normalize_market_stops()" | kind=code-symbol | source=brokers/mt5_execution.py:L166 | neighbors=[MT5ExecutionProvider, ._ensure(), .get_symbol_constraints(), ._normalize_price(), Valida/adapta SL y TP y devuelve diagnó…]
- "brokers_mt5_execution_mt5executionprovider_order_send_safe": "._order_send_safe()" | kind=code-symbol | source=brokers/mt5_execution.py:L503 | neighbors=[MT5ExecutionProvider, ._last_error_is_invalid_comment(), ._sanitize_comment(), .place_market_order(), Envía la orden y aplica el mismo fallba…]
- "brokers_mt5_execution_mt5executionprovider_sanitize_comment": "._sanitize_comment()" | kind=code-symbol | source=brokers/mt5_execution.py:L447 | neighbors=[MT5ExecutionProvider, ._build_market_request_base(), ._order_check_safe(), ._order_send_safe(), Normaliza el comentario para el binding…]
- "brokers_mt5_execution_mt5executionprovider_symbol_filling_candidates": "._symbol_filling_candidates()" | kind=code-symbol | source=brokers/mt5_execution.py:L337 | neighbors=[MT5ExecutionProvider, .get_filling_diagnostics(), ._run_order_check_with_fallback(), .symbol_spec(), Construye candidatos según las flags de…]
- "brokers_symbol_discovery_derivsymboldiscovery_get_all_forex_symbols": ".get_all_forex_symbols()" | kind=code-symbol | source=brokers/symbol_discovery.py:L210 | neighbors=[DerivSymbolDiscovery, ._ensure_connection(), .get_all_symbols(), .is_forex_symbol(), .get_tradeable_forex()]
- "brokers_symbol_discovery_derivsymboldiscovery_get_deriv_synthetics": ".get_deriv_synthetics()" | kind=code-symbol | source=brokers/symbol_discovery.py:L96 | neighbors=[DerivSymbolDiscovery, .get_all_synthetic_symbols(), .classify_symbol(), .get_all_symbols(), .print_report()]
- "brokers_symbol_discovery_derivsymboldiscovery_is_forex_symbol": ".is_forex_symbol()" | kind=code-symbol | source=brokers/symbol_discovery.py:L199 | neighbors=[DerivSymbolDiscovery, .get_all_forex_symbols(), ._ensure_connection(), _looks_like_forex_name(), Identifica FX usando metadata MT5 y, si…]
- "config_symbol_policy_get_symbol_direction_policy": "get_symbol_direction_policy()" | kind=code-symbol | source=config/symbol_policy.py:L23 | neighbors=[symbol_policy.py, direction_policy_diagnostics(), classify_synthetic_symbol(), SymbolDirectionPolicy, is_direction_allowed()]

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-012.json

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
