# Node Description Batch 40 of 56

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

- "brokers_symbol_discovery_derivsymboldiscovery_init": ".__init__()" | kind=code-symbol | source=brokers/symbol_discovery.py:L45 | neighbors=[DerivSymbolDiscovery] | lang=en
- "brokers_symbol_discovery_rationale_200": "Identifica FX usando metadata MT5 y, si falta, el nombre del símbolo." | kind=entity | source=brokers/symbol_discovery.py:L200 | neighbors=[.is_forex_symbol()] | lang=es
- "brokers_symbol_discovery_rationale_222": "Devuelve únicamente pares FX habilitados/seleccionables en el MT5 actual." | kind=entity | source=brokers/symbol_discovery.py:L222 | neighbors=[.get_tradeable_forex()] | lang=es
- "brokers_symbol_discovery_rationale_34": "Fallback para brokers con sufijos: EURUSDm, GBPUSD.a, USDJPYm, etc." | kind=entity | source=brokers/symbol_discovery.py:L34 | neighbors=[_looks_like_forex_name()] | lang=en
- "brokers_symbols": "symbols.py" | kind=code-symbol | source=brokers/symbols.py:L1 | neighbors=[list_symbols()] | lang=en
- "brokers_symbols_list_symbols": "list_symbols()" | kind=code-symbol | source=brokers/symbols.py:L4 | neighbors=[symbols.py] | lang=en
- "config_instruments_instrumentmanager_get_instruments_by_category": ".get_instruments_by_category()" | kind=code-symbol | source=config/instruments.py:L33 | neighbors=[InstrumentManager] | lang=en
- "config_instruments_instrumentmanager_init": ".__init__()" | kind=code-symbol | source=config/instruments.py:L19 | neighbors=[InstrumentManager] | lang=en
- "dashboard_account_page": "account_page.py" | kind=code-symbol | source=dashboard/account_page.py:L1 | neighbors=[realtime_dashboard.py] | lang=en
- "dashboard_realtime_dashboard_realtimedashboardservice_account_url": ".account_url()" | kind=code-symbol | source=dashboard/realtime_dashboard.py:L995 | neighbors=[RealtimeDashboardService] | lang=en
- "dashboard_realtime_dashboard_realtimedashboardservice_instruments_url": ".instruments_url()" | kind=code-symbol | source=dashboard/realtime_dashboard.py:L991 | neighbors=[RealtimeDashboardService] | lang=en
- "dashboard_realtime_dashboard_realtimedashboardservice_stop": ".stop()" | kind=code-symbol | source=dashboard/realtime_dashboard.py:L1172 | neighbors=[RealtimeDashboardService] | lang=en
- "dashboard_realtime_dashboard_realtimedashboardservice_url": ".url()" | kind=code-symbol | source=dashboard/realtime_dashboard.py:L987 | neighbors=[RealtimeDashboardService] | lang=en
- "dashboard_smc_visual_context_rationale_32": "Estado visual de una zona; no altera la estrategia." | kind=entity | source=dashboard/smc_visual_context.py:L32 | neighbors=[_zone_status()] | lang=en
- "dashboard_smc_visual_context_rationale_76": "Construye evidencia visual SMC a partir del DataFrame ya analizado.      No calc" | kind=entity | source=dashboard/smc_visual_context.py:L76 | neighbors=[build_smc_visual_context()] | lang=en
- "dashboard_trade_audit_page": "trade_audit_page.py" | kind=code-symbol | source=dashboard/trade_audit_page.py:L1 | neighbors=[realtime_dashboard.py] | lang=en
- "data_collector_update_historical_csv": "update_historical_csv()" | kind=code-symbol | source=data/collector.py:L6 | neighbors=[collector.py] | lang=en
- "data_market_data_rationale_12": "Inicializa la conexión con MetaTrader 5." | kind=entity | source=data/market_data.py:L12 | neighbors=[initialize_mt5()] | lang=en
- "data_market_data_rationale_24": "Descarga velas históricas entre dos fechas." | kind=entity | source=data/market_data.py:L24 | neighbors=[get_historical_data()] | lang=pt
- "data_market_data_rationale_54": "Guarda los datos en CSV." | kind=entity | source=data/market_data.py:L54 | neighbors=[save_historical_data()] | lang=es
- "database_database_explicit_db_path": "_explicit_db_path()" | kind=code-symbol | source=database/database.py:L27 | neighbors=[database.py] | lang=en
- "database_models_utcnow": "utcnow()" | kind=code-symbol | source=database/models.py:L9 | neighbors=[models.py] | lang=en
- "database_reporting_pretty_json": "_pretty_json()" | kind=code-symbol | source=database/reporting.py:L102 | neighbors=[reporting.py] | lang=en
- "database_repository_tradingrepository_account_snapshots_dataframe": ".account_snapshots_dataframe()" | kind=code-symbol | source=database/repository.py:L3373 | neighbors=[TradingRepository] | lang=en
- "database_repository_tradingrepository_audit_events_dataframe": ".audit_events_dataframe()" | kind=code-symbol | source=database/repository.py:L690 | neighbors=[TradingRepository] | lang=en
- "database_repository_tradingrepository_create_consistent_backup": ".create_consistent_backup()" | kind=code-symbol | source=database/repository.py:L600 | neighbors=[TradingRepository] | lang=en
- "database_repository_tradingrepository_init": ".__init__()" | kind=code-symbol | source=database/repository.py:L36 | neighbors=[TradingRepository] | lang=en
- "database_repository_tradingrepository_position_visual_audits": ".position_visual_audits()" | kind=code-symbol | source=database/repository.py:L859 | neighbors=[TradingRepository] | lang=en
- "database_repository_tradingrepository_trade_history_dataframe": ".trade_history_dataframe()" | kind=code-symbol | source=database/repository.py:L1385 | neighbors=[TradingRepository] | lang=en
- "database_repository_tradingrepository_trade_visual_audits": ".trade_visual_audits()" | kind=code-symbol | source=database/repository.py:L977 | neighbors=[TradingRepository] | lang=en
- "database_repository_tradingrepository_worker_runtime_states": ".worker_runtime_states()" | kind=code-symbol | source=database/repository.py:L784 | neighbors=[TradingRepository] | lang=en
- "declarativebase": "DeclarativeBase" | kind=code-symbol | neighbors=[Base] | lang=en
- "execution_init_getattr": "__getattr__()" | kind=code-symbol | source=strategy/execution/__init__.py:L16 | neighbors=[__init__.py] | lang=en
- "execution_paper_trade_executor_papertradeexecutor_get_open_positions": ".get_open_positions()" | kind=code-symbol | source=strategy/execution/paper_trade_executor.py:L558 | neighbors=[PaperTradeExecutor] | lang=en
- "execution_paper_trade_executor_papertradeexecutor_get_positions": ".get_positions()" | kind=code-symbol | source=strategy/execution/paper_trade_executor.py:L542 | neighbors=[PaperTradeExecutor] | lang=en
- "execution_paper_trade_executor_papertradeexecutor_init": ".__init__()" | kind=code-symbol | source=strategy/execution/paper_trade_executor.py:L40 | neighbors=[PaperTradeExecutor] | lang=en
- "execution_paper_trade_executor_papertradeexecutor_monitor_open_positions": ".monitor_open_positions()" | kind=code-symbol | source=strategy/execution/paper_trade_executor.py:L448 | neighbors=[PaperTradeExecutor] | lang=en
- "execution_paper_trade_executor_papertradeexecutor_monitor_position": ".monitor_position()" | kind=code-symbol | source=strategy/execution/paper_trade_executor.py:L438 | neighbors=[PaperTradeExecutor] | lang=en
- "execution_paper_trade_executor_papertradeexecutor_position_manager": ".position_manager()" | kind=code-symbol | source=strategy/execution/paper_trade_executor.py:L431 | neighbors=[PaperTradeExecutor] | lang=en
- "execution_paper_trade_executor_papertradeexecutor_position_monitoring_service": ".position_monitoring_service()" | kind=code-symbol | source=strategy/execution/paper_trade_executor.py:L435 | neighbors=[PaperTradeExecutor] | lang=en

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-039.json

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
