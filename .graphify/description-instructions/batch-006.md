# Node Description Batch 7 of 56

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

- "execution_live_trading_engine_rationale_3583": "Obtiene contexto H1/M15 sin convertir ORB en una estrategia SMC." | kind=entity | source=strategy/execution/live_trading_engine.py:L3583 | neighbors=[MT5ExecutionProvider, ._orb_higher_timeframe_context(), MultiTimeframeAnalyzer, MultiTimeframeConfig, PipelineConfig, NewYorkORBStrategy] | lang=es
- "execution_live_trading_engine_rationale_3649": "Confirma BE por metadata o por un SL persistido ya protector." | kind=entity | source=strategy/execution/live_trading_engine.py:L3649 | neighbors=[MT5ExecutionProvider, ._trade_has_confirmed_break_even(), MultiTimeframeAnalyzer, MultiTimeframeConfig, PipelineConfig, NewYorkORBStrategy] | lang=pt
- "execution_live_trading_engine_rationale_3670": "Evita S&P 500 + Nasdaq simultáneos hasta confirmar Break Even." | kind=entity | source=strategy/execution/live_trading_engine.py:L3670 | neighbors=[MT5ExecutionProvider, ._orb_exposure_guard(), MultiTimeframeAnalyzer, MultiTimeframeConfig, PipelineConfig, NewYorkORBStrategy] | lang=en
- "execution_live_trading_engine_rationale_468": "Serializa el read/modify/write entre engines, hilos y procesos.          El coor" | kind=entity | source=strategy/execution/live_trading_engine.py:L468 | neighbors=[MT5ExecutionProvider, ._quarantine_storage_lock(), MultiTimeframeAnalyzer, MultiTimeframeConfig, PipelineConfig, NewYorkORBStrategy] | lang=es
- "execution_live_trading_engine_rationale_4766": "Procesa símbolos uno a uno con puntos de control cooperativos.          ``progre" | kind=entity | source=strategy/execution/live_trading_engine.py:L4766 | neighbors=[MT5ExecutionProvider, .process_symbols(), MultiTimeframeAnalyzer, MultiTimeframeConfig, PipelineConfig, NewYorkORBStrategy] | lang=en
- "execution_live_trading_engine_rationale_4861": "Construye snapshots multi-timeframe para auditar posiciones abiertas.          E" | kind=entity | source=strategy/execution/live_trading_engine.py:L4861 | neighbors=[MT5ExecutionProvider, ._dashboard_chart_snapshots(), MultiTimeframeAnalyzer, MultiTimeframeConfig, PipelineConfig, NewYorkORBStrategy] | lang=en
- "execution_live_trading_engine_rationale_5034": "Normaliza cualquier resultado MTF a una vista auditable del estado actual." | kind=entity | source=strategy/execution/live_trading_engine.py:L5034 | neighbors=[MT5ExecutionProvider, ._current_strategy_view_from_analysis(), MultiTimeframeAnalyzer, MultiTimeframeConfig, PipelineConfig, NewYorkORBStrategy] | lang=en
- "execution_live_trading_engine_rationale_5120": "Reanaliza posiciones abiertas y persiste el bloque 'ahora'.          SMC usa el" | kind=entity | source=strategy/execution/live_trading_engine.py:L5120 | neighbors=[MT5ExecutionProvider, ._refresh_current_strategy_views(), MultiTimeframeAnalyzer, MultiTimeframeConfig, PipelineConfig, NewYorkORBStrategy] | lang=es
- "execution_live_trading_engine_rationale_5281": "Ejecuta scanner de señales y monitor de posiciones desacoplados.          En pro" | kind=entity | source=strategy/execution/live_trading_engine.py:L5281 | neighbors=[MT5ExecutionProvider, .run_daemon(), MultiTimeframeAnalyzer, MultiTimeframeConfig, PipelineConfig, NewYorkORBStrategy] | lang=en
- "execution_live_trading_engine_rationale_633": "Lee la posición real y recalcula el riesgo con volumen/precio/SL reales." | kind=entity | source=strategy/execution/live_trading_engine.py:L633 | neighbors=[MT5ExecutionProvider, ._validate_post_fill_risk(), MultiTimeframeAnalyzer, MultiTimeframeConfig, PipelineConfig, NewYorkORBStrategy] | lang=es
- "execution_live_trading_engine_rationale_711": "Telemetría runtime + auditoría persistente, ambas defensivas.          v53: el e" | kind=entity | source=strategy/execution/live_trading_engine.py:L711 | neighbors=[MT5ExecutionProvider, ._persist_audit_event(), MultiTimeframeAnalyzer, MultiTimeframeConfig, PipelineConfig, NewYorkORBStrategy] | lang=pt
- "execution_live_trading_engine_rationale_892": "Reduce telemetría por símbolo sin perder métricas de decisión.          Las audi" | kind=entity | source=strategy/execution/live_trading_engine.py:L892 | neighbors=[MT5ExecutionProvider, ._compact_symbol_result(), MultiTimeframeAnalyzer, MultiTimeframeConfig, PipelineConfig, NewYorkORBStrategy] | lang=en
- "execution_trade_pipeline": "trade_pipeline.py" | kind=code-symbol | source=strategy/execution/trade_pipeline.py:L1 | neighbors=[symbol_policy.py, build_setups(), _empty_setups(), _filter_by_policy(), _latest_sweep(), PipelineConfig] | lang=en
- "multitimeframeanalyzer": "MultiTimeframeAnalyzer" | kind=code-symbol | neighbors=[CountingAnalyzer, ControlledMultiTimeframeAnalyzer, ControlledMultiTimeframeAnalyzer, ControlledMultiTimeframeAnalyzer, ControlledMultiTimeframeAnalyzer, ControlledMultiTimeframeAnalyzer] | lang=en
- "smc_confirmation_engine": "confirmation_engine.py" | kind=code-symbol | source=strategy/smc/confirmation_engine.py:L1 | neighbors=[_average_range(), candle_metrics(), detect_rsi_divergence(), evaluate_m5_confirmation(), _grade(), M5ConfirmationConfig] | lang=en
- "tests_test_backtest": "test_backtest.py" | kind=code-symbol | source=tests/test_backtest.py:L1 | neighbors=[trade_simulator.py, format_number(), load_data(), prepare_data(), print_rr_statistics(), print_summary()] | lang=en
- "tests_test_daemon_break_even_live_lifecyclemanager": "LifecycleManager" | kind=code-symbol | source=tests/test_daemon_break_even_live.py:L68 | neighbors=[test_daemon_break_even_live.py, LiveTradingConfig, LiveTradingEngine, .__init__(), test_daemon_break_even_is_idempotent_wh…, test_daemon_does_not_persist_break_even…] | lang=en
- "tests_test_daemon_runner_extension": "test_daemon_runner_extension.py" | kind=code-symbol | source=tests/test_daemon_runner_extension.py:L1 | neighbors=[_engine(), PositionExecutor, Provider, Repo, test_at_2r_no_continuation_closes_runne…, test_at_2r_profit_is_locked_at_1r_befor…] | lang=en
- "tests_test_daemon_single_entry_fallback_fallbackexecutor": "FallbackExecutor" | kind=code-symbol | source=tests/test_daemon_single_entry_fallback.py:L43 | neighbors=[test_daemon_single_entry_fallback.py, LiveTradingConfig, LiveTradingEngine, .assert_demo_account(), .calculate_volume(), .__init__()] | lang=en
- "tests_test_daemon_split_risk_management_executor": "Executor" | kind=code-symbol | source=tests/test_daemon_split_risk_management.py:L33 | neighbors=[test_daemon_split_risk_management.py, LiveTradingConfig, LiveTradingEngine, .assert_demo_account(), .calculate_volume(), .normalize_market_stops()] | lang=en
- "tests_test_daemon_split_risk_management_provider": "Provider" | kind=code-symbol | source=tests/test_daemon_split_risk_management.py:L20 | neighbors=[test_daemon_split_risk_management.py, LiveTradingConfig, LiveTradingEngine, .ensure_symbol(), .get_current_tick(), .resolve_symbol()] | lang=en
- "tests_test_demo_daemon_integration_provider": "Provider" | kind=code-symbol | source=tests/test_demo_daemon_integration.py:L108 | neighbors=[test_demo_daemon_integration.py, LiveTradingConfig, LiveTradingEngine, TradeReportingService, .ensure_symbol(), .get_current_tick()] | lang=en
- "tests_test_live_end_to_end_dry_run_fakerepository": "FakeRepository" | kind=code-symbol | source=tests/test_live_end_to_end_dry_run.py:L19 | neighbors=[test_live_end_to_end_dry_run.py, LiveTradingConfig, LiveTradingEngine, .get_trade_by_execution_key(), .__init__(), .open_trades()] | lang=en
- "tests_test_paper_trade_monitoring_integration": "test_paper_trade_monitoring_integration.py" | kind=code-symbol | source=tests/test_paper_trade_monitoring_integration.py:L1 | neighbors=[position_manager.py, buy_request(), sell_request(), test_execute_registers_position_in_posi…, test_manual_close_syncs_position_manage…, test_monitor_multiple_open_positions_th…] | lang=en
- "tests_test_signal_freshness": "test_signal_freshness.py" | kind=code-symbol | source=tests/test_signal_freshness.py:L1 | neighbors=[_analyzer(), _engine(), test_m5_signal_age_becomes_stale_after_…, test_m5_signal_age_exact_index_is_fresh…, test_m5_signal_age_minutes_can_block_ev…, test_market_signal_blocks_large_entry_d…] | lang=en
- "tests_test_trade_lifecycle_manager_create_candles": "create_candles()" | kind=code-symbol | source=tests/test_trade_lifecycle_manager.py:L64 | neighbors=[test_trade_lifecycle_manager.py, test_cannot_execute_final_lifecycle_twi…, test_lifecycle_ambiguous(), test_lifecycle_expired(), test_lifecycle_loss(), test_lifecycle_win()] | lang=en
- "tests_test_trade_lifecycle_manager_create_controlled_simulator": "create_controlled_simulator()" | kind=code-symbol | source=tests/test_trade_lifecycle_manager.py:L141 | neighbors=[test_trade_lifecycle_manager.py, test_cannot_execute_final_lifecycle_twi…, test_lifecycle_ambiguous(), test_lifecycle_expired(), test_lifecycle_loss(), test_lifecycle_win()] | lang=en
- "tests_test_v100_entry_quarantine_winrate_minimumvolumeexecutor": "_MinimumVolumeExecutor" | kind=code-symbol | source=tests/test_v100_entry_quarantine_winrate.py:L135 | neighbors=[test_v100_entry_quarantine_winrate.py, LiveTradingConfig, LiveTradingEngine, ChartPatternConfig, M5ConfirmationConfig, .assert_demo_account()] | lang=en
- "tests_test_v100_entry_quarantine_winrate_provider": "_Provider" | kind=code-symbol | source=tests/test_v100_entry_quarantine_winrate.py:L108 | neighbors=[test_v100_entry_quarantine_winrate.py, LiveTradingConfig, LiveTradingEngine, ChartPatternConfig, M5ConfirmationConfig, .ensure_symbol()] | lang=en
- "tests_test_v45_forex_instrument_catalog": "test_v45_forex_instrument_catalog.py" | kind=code-symbol | source=tests/test_v45_forex_instrument_catalog.py:L1 | neighbors=[symbol_discovery.py, instruments.py, realtime_dashboard.py, Connected, _info(), test_forex_is_a_default_operational_cat…] | lang=en
- "tests_test_v47_multi_bot_architecture": "test_v47_multi_bot_architecture.py" | kind=code-symbol | source=tests/test_v47_multi_bot_architecture.py:L1 | neighbors=[main.py, database.py, _engine(), test_legacy_trade_is_only_owned_by_hist…, test_magic_numbers_are_unique(), test_run_demo_bot_supports_profile_magi…] | lang=en
- "tests_test_v48_break_even_winrate": "test_v48_break_even_winrate.py" | kind=code-symbol | source=tests/test_v48_break_even_winrate.py:L1 | neighbors=[account_metrics.py, trade_report_exporter.py, recovered_trade(), test_above_neutral_band_is_decisive_win…, test_report_exporter_calls_small_positi…, test_screenshot_six_trade_example_becom…] | lang=en
- "tests_test_v49_split_synthetic_workers": "test_v49_split_synthetic_workers.py" | kind=code-symbol | source=tests/test_v49_split_synthetic_workers.py:L1 | neighbors=[main.py, _engine(), test_each_profile_has_exact_single_cate…, test_full_multi_bot_uses_split_syntheti…, test_legacy_synthetic_magic_is_adopted_…, test_new_magic_trade_is_owned_only_by_e…] | lang=en
- "tests_test_v53_runtime_telemetry_utf8": "test_v53_runtime_telemetry_utf8.py" | kind=code-symbol | source=tests/test_v53_runtime_telemetry_utf8.py:L1 | neighbors=[main.py, daemon_version.py, realtime_dashboard.py, repository.py, test_console_reporter_no_problematic_wa…, test_coordinator_has_worker_console_sum…] | lang=en
- "tests_test_v54_context_health_visual_audit": "test_v54_context_health_visual_audit.py" | kind=code-symbol | source=tests/test_v54_context_health_visual_audit.py:L1 | neighbors=[realtime_dashboard.py, repository.py, test_dashboard_html_has_context_tabs_an…, test_dashboard_snapshot_exposes_worker_…, test_external_with_known_daemon_magic_i…, test_latest_worker_candidate_is_read_fr…] | lang=en
- "tests_test_v57_forex_persistence_hardening": "test_v57_forex_persistence_hardening.py" | kind=code-symbol | source=tests/test_v57_forex_persistence_hardening.py:L1 | neighbors=[realtime_dashboard.py, models.py, repository.py, catalog(), test_empty_forex_selection_is_persisten…, test_forex_and_orb_remain_independent_a…] | lang=en
- "tests_test_v63_account_db_continuity": "test_v63_account_db_continuity.py" | kind=code-symbol | source=tests/test_v63_account_db_continuity.py:L1 | neighbors=[account_metrics.py, database.py, repository.py, _make_legacy_db(), test_account_page_displays_sqlite_path(), test_account_payload_reports_database_d…] | lang=en
- "tests_test_v66_smc_tp4_be_plus2": "test_v66_smc_tp4_be_plus2.py" | kind=code-symbol | source=tests/test_v66_smc_tp4_be_plus2.py:L1 | neighbors=[Broker, _engine(), Provider, Repo, test_smc_3_5r_guard_locks_3r_while_targ…, test_smc_at_3r_evaluates_before_seeking…] | lang=en
- "tests_test_v66_smc_tp4_be_plus2_repo": "Repo" | kind=code-symbol | source=tests/test_v66_smc_tp4_be_plus2.py:L8 | neighbors=[test_v66_smc_tp4_be_plus2.py, _engine(), LiveTradingConfig, LiveTradingEngine, RunnerExtensionDecision, .get_trade_by_execution_key()] | lang=en
- "tests_test_v67_live_entry_vs_now_repo": "Repo" | kind=code-symbol | source=tests/test_v67_live_entry_vs_now.py:L55 | neighbors=[test_v67_live_entry_vs_now.py, LiveTradingConfig, LiveTradingEngine, .__init__(), .open_trades(), .save_audit_event()] | lang=en

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-006.json

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
