# Node Description Batch 30 of 56

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

- "dashboard_realtime_dashboard_rationale_630": "Publica un dashboard local de sólo lectura sin bloquear el hilo de MT5." | kind=entity | source=dashboard/realtime_dashboard.py:L630 | neighbors=[RealtimeDashboardService, TradeAuditExcelExporter] | lang=nl
- "dashboard_realtime_dashboard_rationale_736": "Detalle completo de un trade y TODOS sus snapshots Entrada vs. Ahora." | kind=entity | source=dashboard/realtime_dashboard.py:L736 | neighbors=[._trade_audit_detail_payload(), TradeAuditExcelExporter] | lang=es
- "dashboard_realtime_dashboard_realtimedashboardservice_get_selected_symbols": ".get_selected_symbols()" | kind=code-symbol | source=dashboard/realtime_dashboard.py:L1282 | neighbors=[RealtimeDashboardService, _normalize_symbol_list()] | lang=en
- "dashboard_smc_visual_context_bool": "_bool()" | kind=code-symbol | source=dashboard/smc_visual_context.py:L23 | neighbors=[smc_visual_context.py, build_smc_visual_context()] | lang=en
- "dashboard_smc_visual_context_iso": "_iso()" | kind=code-symbol | source=dashboard/smc_visual_context.py:L16 | neighbors=[smc_visual_context.py, build_smc_visual_context()] | lang=en
- "data_collector": "collector.py" | kind=code-symbol | source=data/collector.py:L1 | neighbors=[main.py, update_historical_csv()] | lang=en
- "database_database_ensure_trade_columns": "_ensure_trade_columns()" | kind=code-symbol | source=database/database.py:L231 | neighbors=[database.py, init_database()] | lang=en
- "database_database_get_session_factory": "get_session_factory()" | kind=code-symbol | source=database/database.py:L226 | neighbors=[database.py, get_engine()] | lang=en
- "database_models_rationale_101": "Historial permanente de operaciones para Cuenta activa.      Esta tabla es delib" | kind=entity | source=database/models.py:L101 | neighbors=[Base, TradeJournal] | lang=es
- "database_models_rationale_140": "Marca persistente del inicio de una nueva ventana estadística de Cuenta activa." | kind=entity | source=database/models.py:L140 | neighbors=[Base, AccountStatsReset] | lang=en
- "database_models_rationale_152": "Última selección de instrumentos elegida por el usuario para nuevas entradas." | kind=entity | source=database/models.py:L152 | neighbors=[Base, InstrumentSelectionPreference] | lang=es
- "database_models_rationale_164": "Selección persistente independiente por universo operativo." | kind=entity | source=database/models.py:L164 | neighbors=[Base, InstrumentSelectionProfilePreference] | lang=en
- "database_models_rationale_177": "Bitácora append-only de todo evento operativo relevante de DaemonBlackFx." | kind=entity | source=database/models.py:L177 | neighbors=[Base, DaemonAuditEvent] | lang=nl
- "database_models_rationale_195": "Estado operacional consolidado por worker multi-bot." | kind=entity | source=database/models.py:L195 | neighbors=[Base, WorkerRuntimeState] | lang=en
- "database_models_rationale_217": "Último snapshot visual multi-timeframe por símbolo/worker." | kind=entity | source=database/models.py:L217 | neighbors=[Base, PositionVisualAudit] | lang=en
- "database_models_rationale_230": "Auditoría visual persistente por trade: entrada inmutable + estado actual." | kind=entity | source=database/models.py:L230 | neighbors=[Base, TradeVisualAudit] | lang=pt
- "database_models_rationale_250": "Serie histórica append-only de Entrada vs. Ahora por trade.      Guarda datos es" | kind=entity | source=database/models.py:L250 | neighbors=[Base, TradeAuditSnapshot] | lang=es
- "database_reporting_numeric": "_numeric()" | kind=code-symbol | source=database/reporting.py:L10 | neighbors=[reporting.py, export_trading_report()] | lang=en
- "database_reporting_rationale_29": "Exporta un reporte completo desde SQLite a Excel." | kind=entity | source=database/reporting.py:L29 | neighbors=[export_trading_report(), TradingRepository] | lang=en
- "database_reporting_write_sheet": "_write_sheet()" | kind=code-symbol | source=database/reporting.py:L16 | neighbors=[reporting.py, export_trading_report()] | lang=en
- "database_repository_tradingrepository_close_trade": ".close_trade()" | kind=code-symbol | source=database/repository.py:L2221 | neighbors=[TradingRepository, .update_trade()] | lang=en
- "database_repository_tradingrepository_get_trade": ".get_trade()" | kind=code-symbol | source=database/repository.py:L2019 | neighbors=[TradingRepository, ._trade_dict()] | lang=en
- "database_repository_tradingrepository_get_trade_by_execution_key": ".get_trade_by_execution_key()" | kind=code-symbol | source=database/repository.py:L2030 | neighbors=[TradingRepository, ._trade_dict()] | lang=en
- "database_repository_tradingrepository_infer_audit_profile": "._infer_audit_profile()" | kind=code-symbol | source=database/repository.py:L1173 | neighbors=[TradingRepository, .recent_symbol_process_results()] | lang=en
- "database_repository_tradingrepository_latest_account_snapshot": ".latest_account_snapshot()" | kind=code-symbol | source=database/repository.py:L1756 | neighbors=[Devuelve el snapshot de cuenta más reci…, TradingRepository] | lang=en
- "database_repository_tradingrepository_latest_instrument_selection": ".latest_instrument_selection()" | kind=code-symbol | source=database/repository.py:L1679 | neighbors=[Recupera la última selección persistida…, TradingRepository] | lang=en
- "database_repository_tradingrepository_latest_instrument_selection_profiles": ".latest_instrument_selection_profiles()" | kind=code-symbol | source=database/repository.py:L1672 | neighbors=[TradingRepository, .latest_instrument_selection_profile()] | lang=en
- "database_repository_tradingrepository_latest_symbol_process_result": ".latest_symbol_process_result()" | kind=code-symbol | source=database/repository.py:L1295 | neighbors=[Último análisis persistido del símbolo,…, TradingRepository] | lang=en
- "database_repository_tradingrepository_latest_worker_process_results": ".latest_worker_process_results()" | kind=code-symbol | source=database/repository.py:L1131 | neighbors=[Último SYMBOL_PROCESS_RESULT por bot_pr…, TradingRepository] | lang=en
- "database_repository_tradingrepository_recent_symbol_evaluation_events": ".recent_symbol_evaluation_events()" | kind=code-symbol | source=database/repository.py:L654 | neighbors=[Datos compactos para evaluar ARPS/riesg…, TradingRepository] | lang=en
- "database_repository_tradingrepository_reset_database": ".reset_database()" | kind=code-symbol | source=database/repository.py:L1780 | neighbors=[Reinicia datos operativos conservando `…, TradingRepository] | lang=en
- "database_repository_tradingrepository_summary": ".summary()" | kind=code-symbol | source=database/repository.py:L2542 | neighbors=[TradingRepository, .trades_dataframe()] | lang=en
- "database_repository_tradingrepository_trade_audit_snapshots": ".trade_audit_snapshots()" | kind=code-symbol | source=database/repository.py:L1048 | neighbors=[TradingRepository, .trade_audit_snapshots_dataframe()] | lang=en
- "database_repository_tradingrepository_trade_audit_snapshots_dataframe": ".trade_audit_snapshots_dataframe()" | kind=code-symbol | source=database/repository.py:L1083 | neighbors=[TradingRepository, .trade_audit_snapshots()] | lang=en
- "database_repository_tradingrepository_vacuum_database": ".vacuum_database()" | kind=code-symbol | source=database/repository.py:L617 | neighbors=[Compactación explícita para ejecutar só…, TradingRepository] | lang=en
- "execution_init": "__init__.py" | kind=code-symbol | source=strategy/execution/__init__.py:L1 | neighbors=[__getattr__(), trade_report_exporter.py] | lang=en
- "execution_live_paper_trading_engine_livepapertradingengine_init": ".__init__()" | kind=code-symbol | source=strategy/execution/live_paper_trading_engine.py:L34 | neighbors=[LivePaperTradingEngine, LivePaperTradingConfig] | lang=en
- "execution_live_paper_trading_engine_livepapertradingengine_is_ready_signal": "._is_ready_signal()" | kind=code-symbol | source=strategy/execution/live_paper_trading_engine.py:L158 | neighbors=[LivePaperTradingEngine, .run_once()] | lang=en
- "execution_live_paper_trading_engine_livepapertradingengine_monitor_price": "._monitor_price()" | kind=code-symbol | source=strategy/execution/live_paper_trading_engine.py:L149 | neighbors=[LivePaperTradingEngine, .monitor_active_positions()] | lang=en
- "execution_live_paper_trading_engine_livepapertradingengine_run_daemon": ".run_daemon()" | kind=code-symbol | source=strategy/execution/live_paper_trading_engine.py:L139 | neighbors=[LivePaperTradingEngine, .run_once()] | lang=en

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-029.json

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
