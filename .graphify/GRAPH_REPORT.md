# Graph Report - .  (2026-09-03)

## Corpus Check
- 223 files · ~147.896 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2227 nodes · 5338 edges · 125 communities detected
- Extraction: 66% EXTRACTED · 34% INFERRED · 0% AMBIGUOUS · INFERRED: 1816 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output
- Edge kinds: uses: 1816 · calls: 1337 · contains: 1016 · method: 686 · rationale_for: 297 · imports_from: 148 · inherits: 30 · imports: 8


## Input Scope
- Requested: all
- Resolved: all (source: configured-default)
- Included files: 223 · Candidates: recursive
- Excluded: 0 untracked · 0 ignored · 0 sensitive · 0 missing committed
## God Nodes (most connected - your core abstractions)
1. `LiveTradingEngine` - 173 edges
2. `TradingRepository` - 114 edges
3. `MultiTimeframeAnalyzer` - 113 edges
4. `MT5ExecutionProvider` - 105 edges
5. `LiveTradingConfig` - 102 edges
6. `MultiTimeframeConfig` - 94 edges
7. `TradeLifecycleManager` - 59 edges
8. `PipelineConfig` - 57 edges
9. `RealtimeDashboardService` - 56 edges
10. `NewYorkORBStrategy` - 56 edges

## Surprising Connections (you probably didn't know these)
- `Importa el CSV financiero a SQLite y genera/actualiza el Excel.` --uses--> `TradingRepository`  [INFERRED]
  backtesting/backtest_storage.py → database/repository.py
- `Recarga selecciones autoritativas desde SQLAlchemy.          v57: el estado JSON` --uses--> `TradeAuditExcelExporter`  [INFERRED]
  dashboard/realtime_dashboard.py → reporting/trade_audit_excel_exporter.py
- `Normaliza eventos persistidos para que el dashboard explique el bloqueo.` --uses--> `TradeAuditExcelExporter`  [INFERRED]
  dashboard/realtime_dashboard.py → reporting/trade_audit_excel_exporter.py
- `Evalúa la salud de una posición abierta sin ejecutar cierres automáticos.      C` --uses--> `TradeAuditExcelExporter`  [INFERRED]
  dashboard/realtime_dashboard.py → reporting/trade_audit_excel_exporter.py
- `Publica un dashboard local de sólo lectura sin bloquear el hilo de MT5.` --uses--> `TradeAuditExcelExporter`  [INFERRED]
  dashboard/realtime_dashboard.py → reporting/trade_audit_excel_exporter.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.08
Nodes (68): Base, Base, Recupera automáticamente la DB histórica sólo si la estable está vacía.      Ele, Directorio persistente independiente de la carpeta de versión., Índices compatibles con instalaciones existentes y alta concurrencia., (trade_journal, trades, account_snapshots, total) sin modificar el archivo., Busca bases de versiones hermanas sin recorrer el disco completo., Crea una copia consistente que incorpora WAL mediante la API de SQLite. (+60 more)

### Community 1 - "Community 1"
Cohesion: 0.07
Nodes (1): LiveTradingEngine

### Community 2 - "Community 2"
Cohesion: 0.13
Nodes (52): _assert_full_multibot_architecture(), _assert_synthetic_split_architecture(), _assert_v53_runtime_compatibility(), _build_multi_bot_dashboard_catalog(), Distribuye símbolos de forma determinista y estable entre workers., Resuelve únicamente el universo perteneciente al bot solicitado., Descubre el catálogo completo que debe mostrar el dashboard coordinador., Restaura el catálogo sintético si su preferencia persistida quedó vacía. (+44 more)

### Community 3 - "Community 3"
Cohesion: 0.18
Nodes (56): MT5ExecutionProvider, Capa de ejecución para una cuenta MT5 ya conectada.      MetaTrader 5 debe estar, Auto-repara posiciones MT5 del daemon que aún no estén en SQLite., Devuelve la familia estratégica de un worker físicamente dividido., Perfiles SMC con la misma gestión progresiva de Forex.          Esto no habilita, Ventana DST-safe: Tokio 09:00 hasta la siguiente NY 09:30 hábil., Evita que un proceso administre posiciones de otro bot.          v49 permite que, Obtiene únicamente operaciones OPEN del propio bot registradas en SQLite. (+48 more)

### Community 4 - "Community 4"
Cohesion: 0.06
Nodes (28): Compatibilidad temporal. La implementación oficial del conector vive en brokers., DerivSymbolDiscovery, _looks_like_forex_name(), Identifica FX usando metadata MT5 y, si falta, el nombre del símbolo., Devuelve únicamente pares FX habilitados/seleccionables en el MT5 actual., Fallback para brokers con sufijos: EURUSDm, GBPUSD.a, USDJPYm, etc., Devuelve el universo tradeable soportado por DaemonBlackFx:         sintéticos +, Devuelve símbolos sintéticos tradeables filtrados por categoría.          A dife (+20 more)

### Community 5 - "Community 5"
Cohesion: 0.05
Nodes (21): MT5ExecutionError, Abre una orden de mercado.          Antes de order_send ejecuta order_check con, Modifica SL/TP de una posición abierta mediante TRADE_ACTION_SLTP.          Se u, Devuelve restricciones reales informadas por MT5., Devuelve un snapshot serializable de las posiciones abiertas de MT5.          Si, Devuelve el historial de deals disponible en MT5 en formato serializable., Valida/adapta SL y TP y devuelve diagnóstico completo.          Regla importante, Construye candidatos según las flags del símbolo.          MetaTrader expone inf (+13 more)

### Community 6 - "Community 6"
Cohesion: 0.06
Nodes (24): PositionMonitoringService, Procesa las posiciones abiertas que tengan un precio disponible.          No fal, Vigila las posiciones abiertas administradas por PositionManager.      Responsab, Procesa un único tick/precio para una posición abierta., PositionManager, Mueve el stop loss al precio de entrada cuando la posición         alcanza la re, buy_request(), sell_request() (+16 more)

### Community 7 - "Community 7"
Cohesion: 0.06
Nodes (19): build_account_payload(), classify_close(), _metadata(), _strategy_name(), DummyRepository, test_report_enrichment_documents_entry_reason_and_outcome(), recovered_trade(), test_report_exporter_calls_small_positive_rr_break_even() (+11 more)

### Community 8 - "Community 8"
Cohesion: 0.08
Nodes (40): calculate_current_drawdown(), calculate_current_risk(), calculate_daily_loss(), calculate_max_loss_amount(), calculate_open_positions_risk(), calculate_risk_reward(), check_daily_loss_limit(), check_drawdown_limit() (+32 more)

### Community 9 - "Community 9"
Cohesion: 0.07
Nodes (32): apply_money_management(), calculate_risk_amount(), calculate_trade_pnl(), get_money_management_summary(), Calcula cuánto dinero se arriesga     en una operación.      Ejemplo:, Genera estadísticas financieras     después de aplicar money management., Calcula la ganancia o pérdida monetaria     utilizando el R:R realizado., Guarda los resultados financieros     en un archivo CSV. (+24 more)

### Community 10 - "Community 10"
Cohesion: 0.06
Nodes (13): LiveTradingEngine, Engine, Repo, test_process_symbols_reports_each_symbol_immediately(), ExecutionRepo, Executor, FakeEngine, FakeLifecycleManager (+5 more)

### Community 11 - "Community 11"
Cohesion: 0.10
Nodes (13): MultiTimeframeAnalyzer, Invalida la caché completa o una etapa concreta., Devuelve un snapshot seguro de una etapa para auditoría visual., Obtiene una etapa H1/M15/M5 usando caché hasta la próxima vela cerrada., Obtiene un contexto H1 direccional sin exigir que el proveedor         controlad, Analizador multi-temporal H1 -> M15 -> M5.      Estados principales:          ST, H1ExtremeDojiConfig, ControlledDataProvider (+5 more)

### Community 12 - "Community 12"
Cohesion: 0.15
Nodes (7): MT5ExecutionError, MT5ExecutionProvider, Capa de ejecución para una cuenta MT5 ya conectada.      Esta clase no contiene, Convierte el bitmask SYMBOL_FILLING_* a ORDER_FILLING_*.          IMPORTANTE:, Devuelve las restricciones reales informadas por MT5 para el símbolo., Adapta SL/TP al precio actual y a la distancia mínima exigida por el broker., Ejecuta order_check sin enviar la orden y prueba los filling compatibles.

### Community 13 - "Community 13"
Cohesion: 0.18
Nodes (30): print_result(), print_section(), test_calculate_current_drawdown(), test_calculate_current_risk(), test_calculate_daily_loss(), test_calculate_max_loss_amount(), test_calculate_open_positions_risk(), test_calculate_risk_reward() (+22 more)

### Community 14 - "Community 14"
Cohesion: 0.12
Nodes (15): ABC, MT5TradeExecutor, Modifica el Stop Loss de una posición real sin cerrarla.          El método se u, Adaptador del proveedor MT5 al contrato TradeExecutor.      Esta clase no contie, Ejecuta operaciones virtuales.      No envía órdenes al broker.      Característ, Ejecuta una operación.          Implementaciones posibles:          - PaperT, Obtiene el estado actual         de una posición., TradeExecutionRequest (+7 more)

### Community 15 - "Community 15"
Cohesion: 0.12
Nodes (11): LiveDemoSmokeTestService, Prueba controlada de una única orden real en una cuenta MT5 DEMO.      Requiere, _Executor, _Exporter, _Info, _Lifecycle, _LifecycleManager, _Provider (+3 more)

### Community 16 - "Community 16"
Cohesion: 0.15
Nodes (3): Exporta el estado del daemon a XLSX con auditoría explicable.      Además de las, Construye un resumen útil sin exportar el JSON completo a una celda., TradeReportExporter

### Community 17 - "Community 17"
Cohesion: 0.16
Nodes (2): Configuración del ciclo Paper Trading alimentado con precios reales., TradeLifecycleManager

### Community 18 - "Community 18"
Cohesion: 0.15
Nodes (24): apply_money_management(), apply_money_management_to_trade(), calculate_drawdown_statistics(), calculate_money_management_statistics(), calculate_risk_amount(), get_final_balance(), Valida que trades sea un DataFrame., Calcula cuánto dinero se arriesgará.      Fórmula:          risk_amount = (+16 more)

### Community 19 - "Community 19"
Cohesion: 0.13
Nodes (15): Repo, test_dashboard_attaches_m5_chart_and_nested_break_even_snapshot_to_open_position(), test_dashboard_chart_controls_apply_only_to_graph_and_support_timeframes_navigation(), test_dashboard_exposes_separate_instrument_management_route(), test_dashboard_extracts_realtime_trade_quality(), test_dashboard_html_exposes_audit_layers_and_rsi_panel(), test_dashboard_html_exposes_complete_smc_audit_layers(), test_dashboard_instrument_catalog_is_grouped_and_sorted_and_dynamic() (+7 more)

### Community 20 - "Community 20"
Cohesion: 0.12
Nodes (12): MultiTimeframeAnalyzer, CountingAnalyzer, CountingProvider, test_clear_stage_cache_forces_new_fetch_and_pipeline(), test_stage_cache_reuses_data_and_pipeline_before_next_candle(), ControlledDataProvider, ControlledMultiTimeframeAnalyzer, test_controlled_ready_to_enter_to_ambiguous() (+4 more)

### Community 21 - "Community 21"
Cohesion: 0.14
Nodes (14): classify_synthetic_symbol(), direction_policy_diagnostics(), get_symbol_direction_policy(), is_direction_allowed(), normalize_direction(), SymbolDirectionPolicy, _bool(), build_smc_visual_context() (+6 more)

### Community 22 - "Community 22"
Cohesion: 0.19
Nodes (11): BrokerExecutor, LifecycleManager, Provider, Repo, SplitRepo, test_daemon_break_even_is_idempotent_when_broker_already_at_entry(), test_daemon_does_not_persist_break_even_when_broker_does_not_confirm(), test_daemon_moves_live_position_to_break_even_at_one_r() (+3 more)

### Community 23 - "Community 23"
Cohesion: 0.18
Nodes (21): analyze_historical(), collect_once(), main(), _normalize_categories(), _require_symbol_for_offline_mode(), _resolve_live_symbols(), _resolve_live_symbols_for_profile(), _resolve_symbols() (+13 more)

### Community 24 - "Community 24"
Cohesion: 0.18
Nodes (2): ConsoleReportingService, Presenta resultados del motor de trading sin volcar diccionarios completos.

### Community 25 - "Community 25"
Cohesion: 0.14
Nodes (10): _engine(), PositionExecutor, Provider, Repo, test_forex_at_tp2_protects_tp1_then_extends_logically_to_tp3(), test_forex_at_tp2_without_continuation_closes_runner_after_tp1_lock(), test_forex_at_tp3_if_continuation_protects_2_5r_and_runs_to_tp4(), test_forex_at_tp3_without_continuation_closes_after_profit_protection() (+2 more)

### Community 26 - "Community 26"
Cohesion: 0.23
Nodes (3): _json_safe(), _now_iso(), Detalle completo de un trade y TODOS sus snapshots Entrada vs. Ahora.

### Community 27 - "Community 27"
Cohesion: 0.11
Nodes (5): FakeAnalyzer, FakeExecutor, FakeProvider, FakeRepository, test_live_engine_reaches_full_dry_run_validated_path_without_sending_order()

### Community 28 - "Community 28"
Cohesion: 0.14
Nodes (8): Broker, _engine(), Provider, Repo, test_smc_3_5r_guard_locks_3r_while_targeting_4r(), test_smc_at_3r_evaluates_before_seeking_tp4(), test_tp1_close_immediately_protects_runner_at_be_plus_two_points(), TradeExecutor

### Community 29 - "Community 29"
Cohesion: 0.14
Nodes (3): _MultiBotInstanceGuard, Bloqueo atómico que permite un solo coordinador por proyecto.      En Windows us, PaperTradeExecutor

### Community 30 - "Community 30"
Cohesion: 0.18
Nodes (17): _action_label_es(), _confirmed_decision(), _decision_label_es(), _divergence_direction(), _enrich_recent_row(), _extract_quality(), _extract_signal(), _first_dict() (+9 more)

### Community 31 - "Community 31"
Cohesion: 0.26
Nodes (2): Adaptador entre TradeLifecycleManager, TradingRepository y TradeReportExporter., TradeReportingService

### Community 32 - "Community 32"
Cohesion: 0.14
Nodes (7): Analyzer, _engine(), FallbackExecutor, Provider, Repo, test_single_fallback_is_rejected_when_it_also_exceeds_one_percent(), test_split_risk_failure_falls_back_to_one_safe_entry()

### Community 33 - "Community 33"
Cohesion: 0.19
Nodes (18): create_buy_position(), create_sell_position(), test_apply_break_even_buy_at_one_to_one(), test_apply_break_even_sell_at_one_to_one(), test_break_even_cannot_be_applied_twice(), test_break_even_is_not_activated_before_one_to_one(), test_cannot_close_position_twice(), test_clear_all() (+10 more)

### Community 34 - "Community 34"
Cohesion: 0.14
Nodes (8): _Analyzer, _m5_data(), _MinimumVolumeExecutor, _Provider, _setup(), test_minimum_volume_split_error_reaches_safe_single_fallback(), test_optional_harmonic_is_bonus_not_confirmation_denominator(), test_similar_opposing_chart_patterns_penalize_but_do_not_block()

### Community 35 - "Community 35"
Cohesion: 0.16
Nodes (9): _engine(), PositionExecutor, Provider, Repo, test_at_2r_no_continuation_closes_runner_after_locking_profit(), test_at_2r_profit_is_locked_at_1r_before_extending(), test_at_3r_profit_lock_advances_to_2r(), _trade() (+1 more)

### Community 36 - "Community 36"
Cohesion: 0.17
Nodes (7): Analyzer, Executor, Provider, Repo, test_daemon_pipeline_uses_harmonic_as_bonus_with_adaptive_75_gate_by_default(), test_one_percent_operation_is_split_into_two_half_percent_legs(), test_smc_runner_extension_uses_4r_broker_target_without_increasing_risk()

### Community 37 - "Community 37"
Cohesion: 0.18
Nodes (10): _engine(), PositionExecutor, Provider, Repo, test_smc_at_2r_locks_1r_then_extends_only_to_tp3(), test_smc_at_2r_without_continuation_closes_runner_after_profit_lock(), test_smc_at_3r_can_extend_to_tp4_with_2r_locked(), test_smc_at_3r_without_continuation_closes_after_2r_lock() (+2 more)

### Community 38 - "Community 38"
Cohesion: 0.16
Nodes (10): CandleProvider, _event_engine(), ExposureRepo, test_forex_currency_exposure_blocks_third_percent_on_same_currency(), test_forex_event_scheduler_only_releases_new_closed_m5(), test_forex_exposure_does_not_double_count_split_legs(), test_forex_scheduler_retries_same_bar_after_technical_error(), test_forex_total_risk_limit_is_global_across_pairs() (+2 more)

### Community 39 - "Community 39"
Cohesion: 0.12
Nodes (2): create_signal(), test_paper_lifecycle_is_persisted_and_exported()

### Community 40 - "Community 40"
Cohesion: 0.32
Nodes (16): create_ambiguous_result(), create_candles(), create_controlled_simulator(), create_expired_result(), create_loss_result(), create_signal(), create_win_result(), test_cannot_execute_final_lifecycle_twice() (+8 more)

### Community 41 - "Community 41"
Cohesion: 0.15
Nodes (8): MoneyManager, Procesa una operación y actualiza         el balance de la cuenta., Gestiona el riesgo y calcula el resultado monetario     de las operaciones., Retorna el capital actual., Resultado financiero de una operación., Calcula cuánto dinero se arriesga         en una operación., Calcula el resultado monetario         utilizando el R realizado.          Ej, TradeRiskResult

### Community 42 - "Community 42"
Cohesion: 0.15
Nodes (5): Analyzer, Executor, Provider, Repo, test_rejects_trade_when_broker_max_volume_cannot_reach_risk_target()

### Community 43 - "Community 43"
Cohesion: 0.14
Nodes (4): Repo, _service(), test_instruments_cache_invalidates_after_catalog_change(), test_instruments_payload_is_light_and_cached()

### Community 44 - "Community 44"
Cohesion: 0.17
Nodes (2): LivePaperTradingEngine, Orquestador funcional para validar la estrategia con datos/ticks reales     sin

### Community 45 - "Community 45"
Cohesion: 0.48
Nodes (15): assert_result(), print_result(), print_section(), run_all_tests(), test_consecutive_losses(), test_daily_loss_limit(), test_drawdown_limit(), test_invalid_buy_stop_loss() (+7 more)

### Community 46 - "Community 46"
Cohesion: 0.19
Nodes (6): FakeConnector, FakeInstrumentManager, FakeProvider, test_categories_are_normalized(), test_dynamic_symbols_are_discovered(), test_explicit_symbol_has_priority()

### Community 47 - "Community 47"
Cohesion: 0.27
Nodes (12): backup_sqlite_database(), _bootstrap_stable_database(), database_diagnostics(), _ensure_performance_indexes(), _ensure_trade_columns(), get_engine(), get_session_factory(), init_database() (+4 more)

### Community 48 - "Community 48"
Cohesion: 0.32
Nodes (13): ChartPatternConfig, _average_range(), candle_metrics(), detect_rsi_divergence(), evaluate_m5_confirmation(), _grade(), M5ConfirmationConfig, Motor de confirmación M5 para DaemonBlackFx.  El objetivo es evitar entradas por (+5 more)

### Community 49 - "Community 49"
Cohesion: 0.36
Nodes (9): build_engine(), FakeAnalyzer, FakeProvider, ready_signal(), test_live_paper_monitor_uses_bid_for_buy_and_activates_break_even(), test_live_paper_opens_from_ready_signal(), test_live_paper_take_profit_moves_lifecycle_to_win(), test_live_paper_uses_ask_for_sell_monitoring() (+1 more)

### Community 50 - "Community 50"
Cohesion: 0.21
Nodes (8): create_buy_request(), create_sell_request(), test_cannot_close_position_twice(), test_close_position(), test_duplicate_execution_is_blocked(), test_get_position(), test_paper_execute_buy(), test_paper_execute_sell()

### Community 51 - "Community 51"
Cohesion: 0.16
Nodes (3): Analyzer, Repo, test_open_smc_position_is_reanalyzed_and_persisted_without_touching_entry()

### Community 52 - "Community 52"
Cohesion: 0.19
Nodes (5): ExecutionPreflightConfig, FakeProvider, FakeRepository, test_preflight_accepts_dict_symbol_info(), test_preflight_reports_ready()

### Community 53 - "Community 53"
Cohesion: 0.31
Nodes (8): _session_candles(), _strategy(), test_orb_builds_15_minute_range_before_allowing_breakout(), test_orb_buy_requires_m5_breakout_then_retest_and_midpoint_stop(), test_orb_does_not_run_on_weekends(), test_orb_is_disabled_after_new_york_session_close(), test_orb_rejects_breakout_without_retest(), test_orb_sell_requires_m5_breakout_then_retest_and_midpoint_stop()

### Community 54 - "Community 54"
Cohesion: 0.23
Nodes (1): Resuelve y activa una lista una sola vez antes del bucle del demonio.

### Community 55 - "Community 55"
Cohesion: 0.27
Nodes (11): detect_chart_pattern_confirmation(), _effective_price_tolerance(), _evidence(), _explain_chart_pattern_conflict(), _iso(), _lin_slope(), _near(), _pivots() (+3 more)

### Community 56 - "Community 56"
Cohesion: 0.23
Nodes (5): _engine(), FakeMTF, test_neutral_h1_does_not_block_orb(), test_orb_buy_is_blocked_against_bearish_h1_and_m15(), test_orb_sell_is_aligned_with_bearish_context()

### Community 57 - "Community 57"
Cohesion: 0.30
Nodes (6): engine(), Repo, Reporting, test_coordinated_worker_sync_never_writes_xlsx(), test_pre_execution_sync_skips_mt5_without_owned_positions(), test_standalone_auto_export_remains_compatible()

### Community 58 - "Community 58"
Cohesion: 0.22
Nodes (6): persist_money_management_results(), Importa el CSV financiero a SQLite y genera/actualiza el Excel., export_trading_report(), _numeric(), Exporta un reporte completo desde SQLite a Excel., _write_sheet()

### Community 59 - "Community 59"
Cohesion: 0.25
Nodes (10): classify_orb_market(), discover_orb_symbols(), is_orb_eligible_symbol(), is_orb_gold_symbol(), _norm_symbol(), Descubre únicamente contratos ORB operables en la cuenta MT5 actual.      Los sí, Clasifica únicamente los contratos ORB autorizados.      Importante: no usamos e, True únicamente para las dos variantes de Oro autorizadas por ORB. (+2 more)

### Community 60 - "Community 60"
Cohesion: 0.38
Nodes (2): Exporta la auditoría completa Entrada vs. Ahora de un trade a XLSX.      El payl, TradeAuditExcelExporter

### Community 61 - "Community 61"
Cohesion: 0.35
Nodes (10): _engine(), test_asian_and_london_hours_are_enabled_after_tokyo_open(), test_cycle_restarts_exactly_at_tokyo_0900_summer(), test_cycle_restarts_exactly_at_tokyo_0900_winter(), test_dst_new_york_force_flat_still_works_in_winter(), test_force_flat_from_1645_new_york(), test_forex_classifier_does_not_touch_synthetics_or_gold(), test_friday_cutoff_stays_blocked_until_monday_tokyo() (+2 more)

### Community 62 - "Community 62"
Cohesion: 0.31
Nodes (6): ControlledLifecycleAnalyzer, ControlledLifecycleDataProvider, create_config(), print_case_result(), run_lifecycle(), test_trade_lifecycle_integration()

### Community 63 - "Community 63"
Cohesion: 0.22
Nodes (3): EntryAuditRepo, test_fill_persists_entry_context_and_initial_append_only_snapshot(), test_immediate_snapshot_is_idempotent_on_persistence_retry()

### Community 64 - "Community 64"
Cohesion: 0.40
Nodes (8): engine_with_view(), invalid_view(), old_trade(), Repo, test_recovery_protection_closes_after_positive_mfe_is_lost(), test_same_evaluation_does_not_inflate_confirmation_streak(), test_two_distinct_invalid_analyses_close_at_loss_cap(), test_valid_current_analysis_resets_streak_and_never_closes()

### Community 65 - "Community 65"
Cohesion: 0.31
Nodes (4): _catalog_symbols_by_profile(), _normalize_symbol_list(), Recarga selecciones autoritativas desde SQLAlchemy.          v57: el estado JSON, _selection_profile_for_category()

### Community 66 - "Community 66"
Cohesion: 0.33
Nodes (9): build_setups(), _empty_setups(), _filter_by_policy(), _latest_sweep(), Filtra una columna de dirección respetando la política del símbolo.      La mism, Ejecuta la cadena SMC completa. Si symbol es Boom/Crash, aplica la política de d, run_trade_pipeline(), _trend_at() (+1 more)

### Community 67 - "Community 67"
Cohesion: 0.36
Nodes (9): _analyzer(), _engine(), test_m5_signal_age_becomes_stale_after_limit(), test_m5_signal_age_exact_index_is_fresh_at_limit(), test_m5_signal_age_minutes_can_block_even_when_candle_limit_allows(), test_market_signal_blocks_large_entry_drift_in_r_units(), test_market_signal_buy_is_invalidated_at_structural_stop(), test_market_signal_sell_is_invalidated_at_structural_stop() (+1 more)

### Community 69 - "Community 69"
Cohesion: 0.22
Nodes (2): _engine(), test_workers_read_profile_selection_each_cycle()

### Community 70 - "Community 70"
Cohesion: 0.29
Nodes (5): _engine(), Repo, test_live_market_snapshot_persists_for_forex(), test_live_market_snapshot_persists_for_orb(), test_live_market_snapshot_persists_for_synthetic()

### Community 71 - "Community 71"
Cohesion: 0.25
Nodes (4): evaluate_runner_continuation(), Evalúa si un RUNNER que ya alcanzó 2R/3R conserva estructura suficiente.      Ga, RunnerExtensionDecision, TradeExecutor

### Community 72 - "Community 72"
Cohesion: 0.31
Nodes (4): _adx(), _atr(), _closed_frame(), Umbral por instrumento, acotado por piso y techo configurados.

### Community 73 - "Community 73"
Cohesion: 0.31
Nodes (6): _alternating_swings(), detect_harmonic_confirmation(), _evaluate_pattern(), _ratio(), Detección conservadora de patrones armónicos sobre swings confirmados.  No utili, Devuelve el mejor patrón armónico confirmado en los swings disponibles.

### Community 74 - "Community 74"
Cohesion: 0.50
Nodes (7): _data(), _setup(), test_adaptive_75_mode_accepts_when_only_secondary_confirmation_is_missing(), test_adaptive_75_mode_never_overrides_a_critical_smc_failure(), test_adaptive_80_decision_code_reflects_current_threshold(), test_high_quality_long_confirmation_is_accepted(), test_repeated_order_block_touch_is_rejected()

### Community 75 - "Community 75"
Cohesion: 0.39
Nodes (3): ControlledDataProvider, create_config(), test_trade_lifecycle_full_integration()

### Community 76 - "Community 76"
Cohesion: 0.31
Nodes (4): _engine(), test_legacy_synthetic_magic_is_adopted_only_by_matching_family(), test_new_magic_trade_is_owned_only_by_exact_worker(), test_profile_symbol_matching_is_exclusive_for_main_families()

### Community 77 - "Community 77"
Cohesion: 0.44
Nodes (6): _engine_with_open_trade(), _orb_trade(), test_gold_and_wall_street_are_not_part_of_sp500_nasdaq_guard(), test_persisted_protective_stop_also_proves_break_even(), test_sp500_is_allowed_after_nasdaq_break_even_is_confirmed(), test_sp500_is_blocked_while_nasdaq_risk_is_not_protected()

### Community 78 - "Community 78"
Cohesion: 0.32
Nodes (4): _acquire_multibot_instance_guard(), _filter_external_multibot_coordinators(), _find_other_multibot_coordinators_windows(), run_database_maintenance()

### Community 79 - "Community 79"
Cohesion: 0.36
Nodes (7): get_historical_data(), initialize_mt5(), main(), Inicializa la conexión con MetaTrader 5., Descarga velas históricas entre dos fechas., Guarda los datos en CSV., save_historical_data()

### Community 80 - "Community 80"
Cohesion: 0.43
Nodes (6): _engine(), Repo, test_gold_selector_chooses_lower_execution_quality_score(), test_gold_selector_does_not_duplicate_gold_exposure(), test_gold_selector_skips_expensive_comparison_outside_orb_session(), test_gold_selector_uses_xauusd_when_micro_is_not_viable()

### Community 81 - "Community 81"
Cohesion: 0.46
Nodes (7): signal(), test_full_paper_lifecycle_break_even_stop_is_final(), test_full_paper_lifecycle_open_and_break_even(), test_full_paper_lifecycle_stop_loss_to_loss(), test_full_paper_lifecycle_take_profit_to_win_and_history(), test_monitor_multiple_active_lifecycles(), test_rejected_executor_result_does_not_create_active_lifecycle()

### Community 82 - "Community 82"
Cohesion: 0.32
Nodes (3): _engine(), test_legacy_trade_is_only_owned_by_historical_synthetics_bot(), test_trade_ownership_by_magic()

### Community 86 - "Community 86"
Cohesion: 0.29
Nodes (6): calculate_premium_discount(), is_bearish_ob_in_premium(), is_bullish_ob_in_discount(), Filtra Bullish Order Blocks ubicados en Discount., Calcula las zonas Premium, Discount y Equilibrium.      Para cada vela:     -, Filtra Bearish Order Blocks ubicados en Premium.

### Community 87 - "Community 87"
Cohesion: 0.62
Nodes (6): auditHtml(), e(), go(), money(), num(), render()

### Community 88 - "Community 88"
Cohesion: 0.38
Nodes (3): FakeProvider, test_discovery_excludes_disabled_orb_contracts(), test_discovery_includes_both_real_gold_contracts_and_not_gold_derived_indices()

### Community 89 - "Community 89"
Cohesion: 0.38
Nodes (3): catalog(), test_empty_forex_selection_is_persistent_and_not_replaced_by_full_catalog(), test_forex_survives_dashboard_restart_and_stale_state_file()

### Community 91 - "Community 91"
Cohesion: 0.33
Nodes (2): _double_bottom(), test_double_bottom_is_detected_and_aligned_for_buy()

### Community 92 - "Community 92"
Cohesion: 0.38
Nodes (3): _make_legacy_db(), test_nonempty_stable_db_is_never_overwritten(), test_stable_db_recovers_nonempty_sibling_legacy_db()

### Community 93 - "Community 93"
Cohesion: 0.38
Nodes (3): _event(), test_orb_flood_does_not_hide_forex_or_synthetics(), test_recent_results_are_deduped_by_profile_symbol_action()

### Community 96 - "Community 96"
Cohesion: 0.48
Nodes (5): _engine(), test_gold_entry_gate_does_not_affect_forex_or_synthetics(), test_gold_window_opens_at_tokyo_0900_and_closes_at_new_york_0930_summer(), test_gold_window_respects_new_york_winter_dst(), test_orb_detects_open_gold_smc_exposure()

### Community 99 - "Community 99"
Cohesion: 0.67
Nodes (5): build_strategy_evaluation(), _distribution(), main(), _number(), write_strategy_evaluation()

### Community 100 - "Community 100"
Cohesion: 0.40
Nodes (2): _payload(), test_exporter_creates_multisheet_xlsx()

### Community 101 - "Community 101"
Cohesion: 0.47
Nodes (3): calculate_ob_score(), evaluate_order_block(), get_ob_grade()

### Community 102 - "Community 102"
Cohesion: 0.60
Nodes (5): _base_frame(), test_bearish_h1_doji_at_upper_extreme_is_optional_confirmation(), test_bullish_h1_doji_at_lower_extreme_is_optional_confirmation(), test_disabled_doji_never_blocks_or_confirms(), test_doji_in_middle_of_range_does_not_confirm()

### Community 103 - "Community 103"
Cohesion: 0.53
Nodes (3): ControlledDataProvider, ControlledMultiTimeframeAnalyzer, test_controlled_ready_to_enter_to_execution()

### Community 104 - "Community 104"
Cohesion: 0.53
Nodes (3): ControlledDataProvider, ControlledMultiTimeframeAnalyzer, test_controlled_ready_to_enter_to_no_exit()

### Community 105 - "Community 105"
Cohesion: 0.53
Nodes (3): ControlledDataProvider, ControlledMultiTimeframeAnalyzer, test_controlled_ready_to_enter_to_stop_loss()

### Community 106 - "Community 106"
Cohesion: 0.73
Nodes (5): _base(), _setup(), test_bos_cannot_be_saved_by_adaptive_score_without_rejection(), test_choch_cannot_be_saved_by_adaptive_score_without_microstructure(), test_visible_trade_score_is_capped_at_100_but_raw_score_is_preserved()

### Community 107 - "Community 107"
Cohesion: 0.47
Nodes (3): signal(), test_filled_lifecycle_persists_trade_journal_and_audit(), test_xlsx_contains_permanent_trades_and_audit_log()

### Community 112 - "Community 112"
Cohesion: 0.70
Nodes (4): decisive_outcome(), is_break_even_rr(), Devuelve WIN / LOSS / BREAK_EVEN / OPEN / None.      Prioridad:     1. OPEN nunc, safe_float()

### Community 113 - "Community 113"
Cohesion: 0.50
Nodes (4): add_position_sizing(), calculate_position_size(), Calcula el tamaño de posición basándose en el riesgo     permitido sobre el cap, Agrega información de gestión de tamaño de posición     a un DataFrame de opera

### Community 114 - "Community 114"
Cohesion: 0.60
Nodes (4): detect_h1_extreme_doji(), _empty(), Detecta un Doji H1 reciente en un extremo compatible con la operación.      BUY, _safe_float()

### Community 115 - "Community 115"
Cohesion: 0.40
Nodes (4): classify_market_structure(), get_current_trend(), Clasifica los Swing High y Swing Low detectados.      Swing High:         HH, Intenta determinar la tendencia actual según     los últimos puntos de estructu

### Community 116 - "Community 116"
Cohesion: 0.50
Nodes (4): Simula múltiples operaciones y agrega el resultado     de cada una al DataFrame, Simula una operación utilizando las velas posteriores     al momento de entrada, simulate_trade(), simulate_trades()

### Community 117 - "Community 117"
Cohesion: 0.70
Nodes (4): _engine(), test_jump_passes_only_with_reinforced_confirmation(), test_jump_rejects_signal_missing_rejection_even_with_high_score(), test_non_jump_is_not_affected()

### Community 118 - "Community 118"
Cohesion: 0.70
Nodes (4): _frame(), test_sequence_can_disable_m5_after_m15_requirement(), test_sequence_can_fall_back_to_previous_m15_when_config_allows_it(), test_sequence_uses_latest_m15_when_required()

### Community 119 - "Community 119"
Cohesion: 0.60
Nodes (3): test_clean_uptrend_can_continue_runner(), test_insufficient_market_data_blocks_extension(), _uptrend()

### Community 120 - "Community 120"
Cohesion: 0.40
Nodes (1): _Repo

### Community 125 - "Community 125"
Cohesion: 0.50
Nodes (2): Verifica si MetaTrader 5 continúa conectado., Obtiene la información de la cuenta actual.

### Community 126 - "Community 126"
Cohesion: 0.50
Nodes (1): TradeMonitor

### Community 128 - "Community 128"
Cohesion: 0.67
Nodes (2): _frame(), test_bullish_regular_divergence_detected_between_two_swing_lows()

### Community 129 - "Community 129"
Cohesion: 0.83
Nodes (3): make_swings(), test_harmonic_detector_returns_diagnostic_when_no_pattern(), test_harmonic_disabled_is_explicit()

### Community 130 - "Community 130"
Cohesion: 0.67
Nodes (3): get_final_balance(), main(), Obtiene el balance final de manera segura.      Si existe la columna balance_a

### Community 131 - "Community 131"
Cohesion: 0.50
Nodes (1): FakeProvider

### Community 136 - "Community 136"
Cohesion: 0.67
Nodes (2): calculate_backtest_metrics(), Calcula métricas completas de un backtest con     gestión de capital y riesgo.

### Community 137 - "Community 137"
Cohesion: 0.67
Nodes (2): detect_choch_bos(), Detecta Change of Character (CHOCH) y Break of Structure (BOS).      CHOCH alc

### Community 138 - "Community 138"
Cohesion: 0.67
Nodes (2): detect_entry_confirmations(), Detecta confirmaciones de entrada después de un setup SMC.      La lógica busca

### Community 139 - "Community 139"
Cohesion: 0.67
Nodes (2): detect_liquidity_sweeps(), Detecta barridos de liquidez.      Bearish Sweep:         - El precio supera

### Community 140 - "Community 140"
Cohesion: 0.67
Nodes (2): detect_liquidity_levels(), Detecta zonas potenciales de liquidez.      Buy-side liquidity:         Swing

### Community 141 - "Community 141"
Cohesion: 0.67
Nodes (2): detect_order_blocks(), Detecta Order Blocks y conserva el evento estructural que los valida.      Un Bu

### Community 142 - "Community 142"
Cohesion: 0.67
Nodes (2): calculate_risk_reward(), Calcula Stop Loss, Take Profit y Risk/Reward     para las confirmaciones de ent

### Community 143 - "Community 143"
Cohesion: 0.67
Nodes (2): detect_setups(), Detecta setups SMC utilizando una secuencia temporal.      Setup LONG:

### Community 144 - "Community 144"
Cohesion: 0.67
Nodes (2): detect_swings(), Detecta Swing High y Swing Low.      left: número de velas a comparar a la izq

### Community 147 - "Community 147"
Cohesion: 1.00
Nodes (1): Inicializa la conexión con MetaTrader 5.

### Community 148 - "Community 148"
Cohesion: 1.00
Nodes (1): Cierra la conexión con MetaTrader 5.

## Knowledge Gaps
- **130 isolated node(s):** `Calcula cuánto dinero se arriesga     en una operación.      Ejemplo:`, `Calcula la ganancia o pérdida monetaria     utilizando el R:R realizado.`, `Aplica gestión monetaria a los resultados     de un backtest.      Parámetros`, `Genera estadísticas financieras     después de aplicar money management.`, `Guarda los resultados financieros     en un archivo CSV.` (+125 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 1`** (1 nodes): `LiveTradingEngine`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 17`** (2 nodes): `Configuración del ciclo Paper Trading alimentado con precios reales.`, `TradeLifecycleManager`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 24`** (2 nodes): `ConsoleReportingService`, `Presenta resultados del motor de trading sin volcar diccionarios completos.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 31`** (2 nodes): `Adaptador entre TradeLifecycleManager, TradingRepository y TradeReportExporter.`, `TradeReportingService`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 39`** (2 nodes): `create_signal()`, `test_paper_lifecycle_is_persisted_and_exported()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 44`** (2 nodes): `LivePaperTradingEngine`, `Orquestador funcional para validar la estrategia con datos/ticks reales     sin`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 54`** (1 nodes): `Resuelve y activa una lista una sola vez antes del bucle del demonio.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 60`** (2 nodes): `Exporta la auditoría completa Entrada vs. Ahora de un trade a XLSX.      El payl`, `TradeAuditExcelExporter`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 69`** (2 nodes): `_engine()`, `test_workers_read_profile_selection_each_cycle()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 91`** (2 nodes): `_double_bottom()`, `test_double_bottom_is_detected_and_aligned_for_buy()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 100`** (2 nodes): `_payload()`, `test_exporter_creates_multisheet_xlsx()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 120`** (1 nodes): `_Repo`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 125`** (2 nodes): `Verifica si MetaTrader 5 continúa conectado.`, `Obtiene la información de la cuenta actual.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 126`** (1 nodes): `TradeMonitor`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 128`** (2 nodes): `_frame()`, `test_bullish_regular_divergence_detected_between_two_swing_lows()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 131`** (1 nodes): `FakeProvider`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 136`** (2 nodes): `calculate_backtest_metrics()`, `Calcula métricas completas de un backtest con     gestión de capital y riesgo.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 137`** (2 nodes): `detect_choch_bos()`, `Detecta Change of Character (CHOCH) y Break of Structure (BOS).      CHOCH alc`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 138`** (2 nodes): `detect_entry_confirmations()`, `Detecta confirmaciones de entrada después de un setup SMC.      La lógica busca`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 139`** (2 nodes): `detect_liquidity_sweeps()`, `Detecta barridos de liquidez.      Bearish Sweep:         - El precio supera`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 140`** (2 nodes): `detect_liquidity_levels()`, `Detecta zonas potenciales de liquidez.      Buy-side liquidity:         Swing`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 141`** (2 nodes): `detect_order_blocks()`, `Detecta Order Blocks y conserva el evento estructural que los valida.      Un Bu`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 142`** (2 nodes): `calculate_risk_reward()`, `Calcula Stop Loss, Take Profit y Risk/Reward     para las confirmaciones de ent`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 143`** (2 nodes): `detect_setups()`, `Detecta setups SMC utilizando una secuencia temporal.      Setup LONG:`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 144`** (2 nodes): `detect_swings()`, `Detecta Swing High y Swing Low.      left: número de velas a comparar a la izq`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 147`** (1 nodes): `Inicializa la conexión con MetaTrader 5.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 148`** (1 nodes): `Cierra la conexión con MetaTrader 5.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `LiveTradingEngine` connect `Community 1` to `Community 29`, `Community 2`, `Community 21`, `Community 3`, `Community 11`, `Community 22`, `Community 10`, `Community 42`, `Community 35`, `Community 32`, `Community 36`, `Community 14`, `Community 27`, `Community 80`, `Community 34`, `Community 120`, `Community 37`, `Community 71`, `Community 28`, `Community 51`, `Community 38`, `Community 25`, `Community 56`, `Community 70`, `Community 63`, `Community 57`, `Community 64`?**
  _High betweenness centrality (0.180) - this node is a cross-community bridge._
- **Why does `TradingRepository` connect `Community 0` to `Community 29`, `Community 2`, `Community 58`, `Community 39`, `Community 19`?**
  _High betweenness centrality (0.151) - this node is a cross-community bridge._
- **Why does `LiveTradingConfig` connect `Community 2` to `Community 29`, `Community 21`, `Community 3`, `Community 11`, `Community 1`, `Community 22`, `Community 10`, `Community 42`, `Community 35`, `Community 32`, `Community 36`, `Community 14`, `Community 27`, `Community 80`, `Community 34`, `Community 120`, `Community 37`, `Community 71`, `Community 28`, `Community 51`, `Community 38`, `Community 25`, `Community 56`, `Community 70`, `Community 63`, `Community 57`, `Community 64`?**
  _High betweenness centrality (0.132) - this node is a cross-community bridge._
- **Are the 100 inferred relationships involving `LiveTradingEngine` (e.g. with `_MultiBotInstanceGuard` and `Distribuye símbolos de forma determinista y estable entre workers.`) actually correct?**
  _`LiveTradingEngine` has 100 INFERRED edges - model-reasoned connections that need verification._
- **Are the 44 inferred relationships involving `TradingRepository` (e.g. with `_MultiBotInstanceGuard` and `Distribuye símbolos de forma determinista y estable entre workers.`) actually correct?**
  _`TradingRepository` has 44 INFERRED edges - model-reasoned connections that need verification._
- **Are the 91 inferred relationships involving `MultiTimeframeAnalyzer` (e.g. with `_MultiBotInstanceGuard` and `Distribuye símbolos de forma determinista y estable entre workers.`) actually correct?**
  _`MultiTimeframeAnalyzer` has 91 INFERRED edges - model-reasoned connections that need verification._
- **Are the 68 inferred relationships involving `MT5ExecutionProvider` (e.g. with `_MultiBotInstanceGuard` and `Distribuye símbolos de forma determinista y estable entre workers.`) actually correct?**
  _`MT5ExecutionProvider` has 68 INFERRED edges - model-reasoned connections that need verification._