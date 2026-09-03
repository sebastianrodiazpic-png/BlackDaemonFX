# Node Description Batch 6 of 56

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

- "tests_test_v98_persistence_latency_retention": "test_v98_persistence_latency_retention.py" | kind=code-symbol | source=tests/test_v98_persistence_latency_retention.py:L1 | neighbors=[database.py, repository.py, strategy_evaluation.py, test_background_monitor_is_enabled_with…, test_repeated_waiting_evaluation_is_sam…, test_retention_deletes_only_old_operati…] | lang=en
- "brokers_mt5_execution_back_mt5executionprovider_symbol_spec": ".symbol_spec()" | kind=code-symbol | source=brokers/mt5_execution.back.py:L62 | neighbors=[MT5ExecutionProvider, .calculate_volume(), .check_market_order(), .get_symbol_constraints(), .normalize_market_stops(), .place_market_order()] | lang=en
- "brokers_mt5_execution_mt5executionprovider_symbol_spec": ".symbol_spec()" | kind=code-symbol | source=brokers/mt5_execution.py:L114 | neighbors=[MT5ExecutionProvider, ._build_market_request_base(), .calculate_volume(), .get_filling_diagnostics(), .get_symbol_constraints(), .modify_position_stops()] | lang=en
- "dashboard_realtime_dashboard_json_safe": "_json_safe()" | kind=code-symbol | source=dashboard/realtime_dashboard.py:L266 | neighbors=[realtime_dashboard.py, ._cached_account_payload(), ._cached_instruments_payload(), .monitor_result(), ._persist_state_locked(), ._refresh_open_positions_locked()] | lang=en
- "database_repository_tradingrepository_trade_kwargs": "._trade_kwargs()" | kind=code-symbol | source=database/repository.py:L342 | neighbors=[Normaliza datos antes de crear un Trade., TradingRepository, .create_trade(), .create_trade_once(), ._dt(), ._float_or_none()] | lang=en
- "database_repository_tradingrepository_update_trade": ".update_trade()" | kind=code-symbol | source=database/repository.py:L2112 | neighbors=[TradingRepository, .close_trade(), .sync_closed_mt5_trades(), ._dt(), ._float_or_none(), ._int_or_none()] | lang=en
- "execution_live_trading_engine_livetradingengine_process_symbols": ".process_symbols()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L4758 | neighbors=[LiveTradingEngine, ._compact_symbol_result(), ._persist_audit_event(), ._prepare_orb_gold_selection(), .process_symbol(), ._sync_open_trades_before_execution()] | lang=en
- "execution_live_trading_engine_livetradingengine_run_daemon": ".run_daemon()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L5273 | neighbors=[LiveTradingEngine, ._canonical_bot_profile(), ._commit_forex_processed_symbols(), ._forex_due_symbols(), ._persist_audit_event(), .process_symbols()] | lang=en
- "execution_live_trading_engine_rationale_1000": "Auto-repara posiciones MT5 del daemon que aún no estén en SQLite." | kind=entity | source=strategy/execution/live_trading_engine.py:L1000 | neighbors=[MT5ExecutionProvider, ._recover_unpersisted_open_positions(), MultiTimeframeAnalyzer, MultiTimeframeConfig, PipelineConfig, NewYorkORBStrategy] | lang=es
- "execution_live_trading_engine_rationale_1047": "Devuelve la familia estratégica de un worker físicamente dividido." | kind=entity | source=strategy/execution/live_trading_engine.py:L1047 | neighbors=[MT5ExecutionProvider, ._canonical_bot_profile(), MultiTimeframeAnalyzer, MultiTimeframeConfig, PipelineConfig, NewYorkORBStrategy] | lang=fr
- "execution_live_trading_engine_rationale_1073": "Perfiles SMC con la misma gestión progresiva de Forex.          Esto no habilita" | kind=entity | source=strategy/execution/live_trading_engine.py:L1073 | neighbors=[MT5ExecutionProvider, ._uses_forex_style_smc_management(), MultiTimeframeAnalyzer, MultiTimeframeConfig, PipelineConfig, NewYorkORBStrategy] | lang=en
- "execution_live_trading_engine_rationale_1085": "Ventana DST-safe: Tokio 09:00 hasta la siguiente NY 09:30 hábil." | kind=entity | source=strategy/execution/live_trading_engine.py:L1085 | neighbors=[MT5ExecutionProvider, ._gold_smc_session_state(), MultiTimeframeAnalyzer, MultiTimeframeConfig, PipelineConfig, NewYorkORBStrategy] | lang=en
- "execution_live_trading_engine_rationale_1156": "Evita que un proceso administre posiciones de otro bot.          v49 permite que" | kind=entity | source=strategy/execution/live_trading_engine.py:L1156 | neighbors=[MT5ExecutionProvider, ._trade_owned_by_current_bot(), MultiTimeframeAnalyzer, MultiTimeframeConfig, PipelineConfig, NewYorkORBStrategy] | lang=fr
- "execution_live_trading_engine_rationale_1245": "Obtiene únicamente operaciones OPEN del propio bot registradas en SQLite." | kind=entity | source=strategy/execution/live_trading_engine.py:L1245 | neighbors=[MT5ExecutionProvider, ._open_trade_diagnostics(), MultiTimeframeAnalyzer, MultiTimeframeConfig, PipelineConfig, NewYorkORBStrategy] | lang=es
- "execution_live_trading_engine_rationale_1276": "Evita que SQLite mantenga OPEN una operación ya cerrada en MT5." | kind=entity | source=strategy/execution/live_trading_engine.py:L1276 | neighbors=[MT5ExecutionProvider, ._sync_open_trades_before_execution(), MultiTimeframeAnalyzer, MultiTimeframeConfig, PipelineConfig, NewYorkORBStrategy] | lang=es
- "execution_live_trading_engine_rationale_1314": "Comprueba si el mercado actual invalida o degrada la señal original." | kind=entity | source=strategy/execution/live_trading_engine.py:L1314 | neighbors=[MT5ExecutionProvider, ._market_signal_diagnostics(), MultiTimeframeAnalyzer, MultiTimeframeConfig, PipelineConfig, NewYorkORBStrategy] | lang=es
- "execution_live_trading_engine_rationale_1378": "Bloqueo DB-global por exposición Forex, independiente del shard." | kind=entity | source=strategy/execution/live_trading_engine.py:L1378 | neighbors=[MT5ExecutionProvider, ._forex_exposure_guard(), MultiTimeframeAnalyzer, MultiTimeframeConfig, PipelineConfig, NewYorkORBStrategy] | lang=es
- "execution_live_trading_engine_rationale_1453": "Analiza perfiles SMC una sola vez por cada vela M5 cerrada.          El nombre s" | kind=entity | source=strategy/execution/live_trading_engine.py:L1453 | neighbors=[MT5ExecutionProvider, ._forex_due_symbols(), MultiTimeframeAnalyzer, MultiTimeframeConfig, PipelineConfig, NewYorkORBStrategy] | lang=es
- "execution_live_trading_engine_rationale_1517": "Marca la vela M5 como procesada sólo tras terminar su análisis." | kind=entity | source=strategy/execution/live_trading_engine.py:L1517 | neighbors=[MT5ExecutionProvider, ._commit_forex_processed_symbols(), MultiTimeframeAnalyzer, MultiTimeframeConfig, PipelineConfig, NewYorkORBStrategy] | lang=es
- "execution_live_trading_engine_rationale_1543": "Devuelve None si se puede continuar o un resultado de bloqueo detallado." | kind=entity | source=strategy/execution/live_trading_engine.py:L1543 | neighbors=[MT5ExecutionProvider, ._position_limit_result(), MultiTimeframeAnalyzer, MultiTimeframeConfig, PipelineConfig, NewYorkORBStrategy] | lang=en
- "execution_live_trading_engine_rationale_1605": "Calcula BE+offset en puntos, siempre hacia el lado favorable del trade." | kind=entity | source=strategy/execution/live_trading_engine.py:L1605 | neighbors=[MT5ExecutionProvider, ._break_even_target_stop(), MultiTimeframeAnalyzer, MultiTimeframeConfig, PipelineConfig, NewYorkORBStrategy] | lang=es
- "execution_live_trading_engine_rationale_1626": "Detecta si la pierna TP1 hermana ya cerró con beneficio.          Esto hace pers" | kind=entity | source=strategy/execution/live_trading_engine.py:L1626 | neighbors=[MT5ExecutionProvider, ._break_even_tp1_completion(), MultiTimeframeAnalyzer, MultiTimeframeConfig, PipelineConfig, NewYorkORBStrategy] | lang=en
- "execution_live_trading_engine_rationale_1674": "Tolerancia de confirmación alineada al tick/point real del broker." | kind=entity | source=strategy/execution/live_trading_engine.py:L1674 | neighbors=[MT5ExecutionProvider, ._break_even_price_tolerance(), MultiTimeframeAnalyzer, MultiTimeframeConfig, PipelineConfig, NewYorkORBStrategy] | lang=en
- "execution_live_trading_engine_rationale_1696": "Actualiza MFE/MAE muestreados por el monitor de posiciones.          MFE = máxim" | kind=entity | source=strategy/execution/live_trading_engine.py:L1696 | neighbors=[MT5ExecutionProvider, ._update_excursion_metrics(), MultiTimeframeAnalyzer, MultiTimeframeConfig, PipelineConfig, NewYorkORBStrategy] | lang=es
- "execution_live_trading_engine_rationale_1747": "Cierra una pérdida controlada cuando la tesis ACTUAL ya no es válida.          C" | kind=entity | source=strategy/execution/live_trading_engine.py:L1747 | neighbors=[MT5ExecutionProvider, ._analysis_invalidation_exit(), MultiTimeframeAnalyzer, MultiTimeframeConfig, PipelineConfig, NewYorkORBStrategy] | lang=en
- "execution_live_trading_engine_rationale_1896": "Invalidación M1 persistente + time stop escalonado 1/3/5 minutos." | kind=entity | source=strategy/execution/live_trading_engine.py:L1896 | neighbors=[MT5ExecutionProvider, ._arps_time_stop_exit(), MultiTimeframeAnalyzer, MultiTimeframeConfig, PipelineConfig, NewYorkORBStrategy] | lang=en
- "execution_live_trading_engine_rationale_2009": "Gestiona extensión dinámica del RUNNER con profit-lock estructural.          SMC" | kind=entity | source=strategy/execution/live_trading_engine.py:L2009 | neighbors=[MT5ExecutionProvider, ._manage_runner_extension(), MultiTimeframeAnalyzer, MultiTimeframeConfig, PipelineConfig, NewYorkORBStrategy] | lang=en
- "execution_live_trading_engine_rationale_2470": "Persiste telemetría ligera de posiciones abiertas en cada monitor.          Es d" | kind=entity | source=strategy/execution/live_trading_engine.py:L2470 | neighbors=[MT5ExecutionProvider, ._persist_live_position_market_snapshot…, MultiTimeframeAnalyzer, MultiTimeframeConfig, PipelineConfig, NewYorkORBStrategy] | lang=en
- "execution_live_trading_engine_rationale_2525": "Congela tesis y snapshot inicial apenas MT5 confirma la entrada." | kind=entity | source=strategy/execution/live_trading_engine.py:L2525 | neighbors=[MT5ExecutionProvider, ._persist_entry_audit_immediately(), MultiTimeframeAnalyzer, MultiTimeframeConfig, PipelineConfig, NewYorkORBStrategy] | lang=es
- "execution_live_trading_engine_rationale_2638": "Monitorea posiciones OPEN del daemon y mueve el SL real en MT5 a Break Even" | kind=entity | source=strategy/execution/live_trading_engine.py:L2638 | neighbors=[MT5ExecutionProvider, ._monitor_break_even_positions(), MultiTimeframeAnalyzer, MultiTimeframeConfig, PipelineConfig, NewYorkORBStrategy] | lang=es
- "execution_live_trading_engine_rationale_3102": "Evita duplicar la misma tesis de Oro entre XAUUSD y microXAUUSD." | kind=entity | source=strategy/execution/live_trading_engine.py:L3102 | neighbors=[MT5ExecutionProvider, ._orb_gold_counterpart_open(), MultiTimeframeAnalyzer, MultiTimeframeConfig, PipelineConfig, NewYorkORBStrategy] | lang=es
- "execution_live_trading_engine_rationale_3116": "Detecta Oro SMC aún abierto para impedir una segunda tesis ORB." | kind=entity | source=strategy/execution/live_trading_engine.py:L3116 | neighbors=[MT5ExecutionProvider, ._gold_smc_exposure_open(), MultiTimeframeAnalyzer, MultiTimeframeConfig, PipelineConfig, NewYorkORBStrategy] | lang=en
- "execution_live_trading_engine_rationale_3136": "Evalúa si un contrato de Oro puede ejecutar correctamente una señal ORB." | kind=entity | source=strategy/execution/live_trading_engine.py:L3136 | neighbors=[MT5ExecutionProvider, ._evaluate_orb_gold_contract(), MultiTimeframeAnalyzer, MultiTimeframeConfig, PipelineConfig, NewYorkORBStrategy] | lang=es
- "execution_live_trading_engine_rationale_3259": "True sólo mientras la sesión ORB NY está activa (09:30 <= NY < 16:00)." | kind=entity | source=strategy/execution/live_trading_engine.py:L3259 | neighbors=[MT5ExecutionProvider, ._orb_session_is_active(), MultiTimeframeAnalyzer, MultiTimeframeConfig, PipelineConfig, NewYorkORBStrategy] | lang=en
- "execution_live_trading_engine_rationale_3277": "Selecciona un solo contrato de Oro para la oportunidad ORB del ciclo." | kind=entity | source=strategy/execution/live_trading_engine.py:L3277 | neighbors=[MT5ExecutionProvider, ._prepare_orb_gold_selection(), MultiTimeframeAnalyzer, MultiTimeframeConfig, PipelineConfig, NewYorkORBStrategy] | lang=es
- "execution_live_trading_engine_rationale_3348": "Reconoce pares FX estándar aun cuando el broker agregue un sufijo." | kind=entity | source=strategy/execution/live_trading_engine.py:L3348 | neighbors=[MT5ExecutionProvider, ._is_forex_symbol(), MultiTimeframeAnalyzer, MultiTimeframeConfig, PipelineConfig, NewYorkORBStrategy] | lang=fr
- "execution_live_trading_engine_rationale_3361": "Ventana Forex: Tokio 09:00 hasta cutoff NY 16:30, DST-safe." | kind=entity | source=strategy/execution/live_trading_engine.py:L3361 | neighbors=[MT5ExecutionProvider, ._forex_rollover_status(), MultiTimeframeAnalyzer, MultiTimeframeConfig, PipelineConfig, NewYorkORBStrategy] | lang=en
- "execution_live_trading_engine_rationale_337": "Motor DEMO: H1 contexto -> M15 setup -> M5 entrada -> MT5 -> SQLite.      execut" | kind=entity | source=strategy/execution/live_trading_engine.py:L337 | neighbors=[MT5ExecutionProvider, LiveTradingEngine, MultiTimeframeAnalyzer, MultiTimeframeConfig, PipelineConfig, NewYorkORBStrategy] | lang=en
- "execution_live_trading_engine_rationale_3455": "Cierra posiciones Forex administradas por el daemon antes del rollover." | kind=entity | source=strategy/execution/live_trading_engine.py:L3455 | neighbors=[MT5ExecutionProvider, ._close_forex_positions_for_rollover(), MultiTimeframeAnalyzer, MultiTimeframeConfig, PipelineConfig, NewYorkORBStrategy] | lang=es
- "execution_live_trading_engine_rationale_3527": "Filtro extra para Jump basado en la muestra DEMO observada.          Jump no se" | kind=entity | source=strategy/execution/live_trading_engine.py:L3527 | neighbors=[MT5ExecutionProvider, ._jump_quality_gate(), MultiTimeframeAnalyzer, MultiTimeframeConfig, PipelineConfig, NewYorkORBStrategy] | lang=es

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-005.json

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
