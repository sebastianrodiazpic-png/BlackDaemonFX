# Node Description Batch 22 of 56

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

- "dashboard_realtime_dashboard_realtimedashboardservice_load_persisted_state": "._load_persisted_state()" | kind=code-symbol | source=dashboard/realtime_dashboard.py:L681 | neighbors=[RealtimeDashboardService, .__init__(), _now_iso()]
- "dashboard_realtime_dashboard_reason_label_es": "_reason_label_es()" | kind=code-symbol | source=dashboard/realtime_dashboard.py:L150 | neighbors=[realtime_dashboard.py, _enrich_recent_row(), _humanize_code()]
- "dashboard_realtime_dashboard_selection_profile_for_category": "_selection_profile_for_category()" | kind=code-symbol | source=dashboard/realtime_dashboard.py:L236 | neighbors=[realtime_dashboard.py, _catalog_symbols_by_profile(), .set_instrument_catalog()]
- "dashboard_smc_visual_context_fvg_status": "_fvg_status()" | kind=code-symbol | source=dashboard/smc_visual_context.py:L52 | neighbors=[smc_visual_context.py, build_smc_visual_context(), _float()]
- "data_market_data_get_historical_data": "get_historical_data()" | kind=code-symbol | source=data/market_data.py:L23 | neighbors=[market_data.py, main(), Descarga velas históricas entre dos fec…]
- "data_market_data_initialize_mt5": "initialize_mt5()" | kind=code-symbol | source=data/market_data.py:L11 | neighbors=[market_data.py, main(), Inicializa la conexión con MetaTrader 5.]
- "data_market_data_save_historical_data": "save_historical_data()" | kind=code-symbol | source=data/market_data.py:L53 | neighbors=[market_data.py, main(), Guarda los datos en CSV.]
- "database_database_backup_sqlite_database": "backup_sqlite_database()" | kind=code-symbol | source=database/database.py:L69 | neighbors=[database.py, _bootstrap_stable_database(), Crea una copia consistente que incorpor…]
- "database_database_ensure_performance_indexes": "_ensure_performance_indexes()" | kind=code-symbol | source=database/database.py:L260 | neighbors=[database.py, init_database(), Índices compatibles con instalaciones e…]
- "database_database_legacy_candidates": "_legacy_candidates()" | kind=code-symbol | source=database/database.py:L53 | neighbors=[database.py, _bootstrap_stable_database(), Busca bases de versiones hermanas sin r…]
- "database_database_stable_data_dir": "_stable_data_dir()" | kind=code-symbol | source=database/database.py:L15 | neighbors=[database.py, database_diagnostics(), Directorio persistente independiente de…]
- "database_repository_tradingrepository_backtest_ticket": "._backtest_ticket()" | kind=code-symbol | source=database/repository.py:L237 | neighbors=[Genera una clave única para evitar dupl…, TradingRepository, .import_backtest_dataframe()]
- "database_repository_tradingrepository_build_setup_reason": "._build_setup_reason()" | kind=code-symbol | source=database/repository.py:L280 | neighbors=[Construye una descripción del setup SMC., TradingRepository, .import_backtest_dataframe()]
- "database_repository_tradingrepository_checkpoint_database": ".checkpoint_database()" | kind=code-symbol | source=database/repository.py:L581 | neighbors=[Checkpoint WAL explícito; TRUNCATE se r…, TradingRepository, .maintain_operational_audits()]
- "database_repository_tradingrepository_clean_value": "._clean_value()" | kind=code-symbol | source=database/repository.py:L172 | neighbors=[Limpia valores provenientes de pandas /…, TradingRepository, .import_backtest_dataframe()]
- "database_repository_tradingrepository_database_diagnostics": ".database_diagnostics()" | kind=code-symbol | source=database/repository.py:L41 | neighbors=[TradingRepository, .sync_trade_journal(), .maintain_operational_audits()]
- "database_repository_tradingrepository_get_trade_by_position_ticket": ".get_trade_by_position_ticket()" | kind=code-symbol | source=database/repository.py:L2049 | neighbors=[TradingRepository, ._trade_dict(), .import_open_mt5_positions()]
- "database_repository_tradingrepository_latest_account_stats_reset": ".latest_account_stats_reset()" | kind=code-symbol | source=database/repository.py:L1401 | neighbors=[Devuelve la marca persistente más recie…, TradingRepository, .reset_account_statistics()]
- "database_repository_tradingrepository_normalize_selection_profile": "._normalize_selection_profile()" | kind=code-symbol | source=database/repository.py:L1580 | neighbors=[TradingRepository, .latest_instrument_selection_profile(), .save_instrument_selection_profile()]
- "database_repository_tradingrepository_prune_operational_audit_events": ".prune_operational_audit_events()" | kind=code-symbol | source=database/repository.py:L510 | neighbors=[Retención incremental sin bloquear SQLi…, TradingRepository, .maintain_operational_audits()]
- "database_repository_tradingrepository_recent_symbol_process_results": ".recent_symbol_process_results()" | kind=code-symbol | source=database/repository.py:L1220 | neighbors=[Panel equilibrado de análisis recientes…, TradingRepository, ._infer_audit_profile()]
- "database_repository_tradingrepository_save_account_snapshot": ".save_account_snapshot()" | kind=code-symbol | source=database/repository.py:L1716 | neighbors=[TradingRepository, ._dt(), ._num()]
- "database_repository_tradingrepository_save_instrument_selection": ".save_instrument_selection()" | kind=code-symbol | source=database/repository.py:L1523 | neighbors=[Persiste la selección completa de instr…, TradingRepository, .save_audit_event()]
- "database_repository_tradingrepository_trades_dataframe": ".trades_dataframe()" | kind=code-symbol | source=database/repository.py:L2508 | neighbors=[TradingRepository, .summary(), ._trade_dict()]
- "database_repository_tradingrepository_upsert_position_visual_audit": ".upsert_position_visual_audit()" | kind=code-symbol | source=database/repository.py:L811 | neighbors=[TradingRepository, ._dt(), ._json_or_none()]
- "execution_live_paper_trading_engine": "live_paper_trading_engine.py" | kind=code-symbol | source=strategy/execution/live_paper_trading_engine.py:L1 | neighbors=[LivePaperTradingConfig, LivePaperTradingEngine, trade_lifecycle_manager.py]
- "execution_live_paper_trading_engine_livepapertradingengine_monitor_active_positions": ".monitor_active_positions()" | kind=code-symbol | source=strategy/execution/live_paper_trading_engine.py:L116 | neighbors=[LivePaperTradingEngine, ._monitor_price(), .run_once()]
- "execution_live_paper_trading_engine_rationale_13": "Configuración del ciclo Paper Trading alimentado con precios reales." | kind=entity | source=strategy/execution/live_paper_trading_engine.py:L13 | neighbors=[LivePaperTradingConfig, PaperTradeExecutor, TradeLifecycleManager]
- "execution_live_paper_trading_engine_rationale_21": "Orquestador funcional para validar la estrategia con datos/ticks reales     sin" | kind=entity | source=strategy/execution/live_paper_trading_engine.py:L21 | neighbors=[LivePaperTradingEngine, PaperTradeExecutor, TradeLifecycleManager]
- "execution_live_trading_engine_livetradingengine_account_and_guard": "._account_and_guard()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L1211 | neighbors=[LiveTradingEngine, ._prepare_orb_gold_selection(), .process_symbol()]
- "execution_live_trading_engine_livetradingengine_break_even_target_stop": "._break_even_target_stop()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L1604 | neighbors=[LiveTradingEngine, ._monitor_break_even_positions(), Calcula BE+offset en puntos, siempre ha…]
- "execution_live_trading_engine_livetradingengine_break_even_tp1_completion": "._break_even_tp1_completion()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L1625 | neighbors=[LiveTradingEngine, ._monitor_break_even_positions(), Detecta si la pierna TP1 hermana ya cer…]
- "execution_live_trading_engine_livetradingengine_compact_symbol_result": "._compact_symbol_result()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L891 | neighbors=[LiveTradingEngine, .process_symbols(), Reduce telemetría por símbolo sin perde…]
- "execution_live_trading_engine_livetradingengine_dashboard_chart_snapshots": "._dashboard_chart_snapshots()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L4860 | neighbors=[LiveTradingEngine, ._trade_owned_by_current_bot(), Construye snapshots multi-timeframe par…]
- "execution_live_trading_engine_livetradingengine_evaluate_orb_gold_contract": "._evaluate_orb_gold_contract()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L3135 | neighbors=[LiveTradingEngine, ._prepare_orb_gold_selection(), Evalúa si un contrato de Oro puede ejec…]
- "execution_live_trading_engine_livetradingengine_gold_smc_entry_gate": "._gold_smc_entry_gate()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L1140 | neighbors=[LiveTradingEngine, ._gold_smc_session_state(), .process_symbol()]
- "execution_live_trading_engine_livetradingengine_is_jump_symbol": "._is_jump_symbol()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L3523 | neighbors=[LiveTradingEngine, ._jump_quality_gate(), .process_symbol()]
- "execution_live_trading_engine_livetradingengine_load_quarantine": "._load_quarantine()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L558 | neighbors=[LiveTradingEngine, ._load_quarantine_unlocked(), ._quarantine_storage_lock()]
- "execution_live_trading_engine_livetradingengine_orb_gold_counterpart_open": "._orb_gold_counterpart_open()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L3101 | neighbors=[LiveTradingEngine, .process_symbol(), Evita duplicar la misma tesis de Oro en…]
- "execution_live_trading_engine_livetradingengine_orb_session_is_active": "._orb_session_is_active()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L3258 | neighbors=[LiveTradingEngine, ._prepare_orb_gold_selection(), True sólo mientras la sesión ORB NY est…]

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-021.json

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
