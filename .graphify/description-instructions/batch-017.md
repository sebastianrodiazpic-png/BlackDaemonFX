# Node Description Batch 18 of 56

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

- "database_repository_tradingrepository_import_open_mt5_positions": ".import_open_mt5_positions()" | kind=code-symbol | source=database/repository.py:L2932 | neighbors=[Descubre posiciones abiertas en MT5 que…, TradingRepository, .create_trade_once(), .get_trade_by_position_ticket()]
- "database_repository_tradingrepository_journal_key": "._journal_key()" | kind=code-symbol | source=database/repository.py:L1333 | neighbors=[Clave estable para que un mismo trade n…, TradingRepository, .import_mt5_trade_history(), ._upsert_trade_journal_session()]
- "database_repository_tradingrepository_latest_instrument_selection_profile": ".latest_instrument_selection_profile()" | kind=code-symbol | source=database/repository.py:L1654 | neighbors=[TradingRepository, ._normalize_selection_profile(), .latest_instrument_selection_profiles(), .save_instrument_selection_profile()]
- "database_repository_tradingrepository_maintain_operational_audits": ".maintain_operational_audits()" | kind=code-symbol | source=database/repository.py:L637 | neighbors=[TradingRepository, .checkpoint_database(), .database_diagnostics(), .prune_operational_audit_events()]
- "database_repository_tradingrepository_open_trades": ".open_trades()" | kind=code-symbol | source=database/repository.py:L2077 | neighbors=[TradingRepository, ._trade_dict(), .reconcile_open_trades(), .sync_closed_mt5_trades()]
- "database_repository_tradingrepository_reconcile_open_trades": ".reconcile_open_trades()" | kind=code-symbol | source=database/repository.py:L3333 | neighbors=[Diagnóstico entre SQLite y MT5., TradingRepository, .open_trades(), .sync_closed_mt5_trades()]
- "database_repository_tradingrepository_reset_account_statistics": ".reset_account_statistics()" | kind=code-symbol | source=database/repository.py:L1424 | neighbors=[Inicia una nueva ventana estadística si…, TradingRepository, .account_trade_history_dataframe(), .latest_account_stats_reset()]
- "database_repository_tradingrepository_save_signal_once": ".save_signal_once()" | kind=code-symbol | source=database/repository.py:L1875 | neighbors=[TradingRepository, ._dt(), ._none_or_upper(), .save_signal()]
- "database_repository_tradingrepository_save_trade_audit_snapshot": ".save_trade_audit_snapshot()" | kind=code-symbol | source=database/repository.py:L1012 | neighbors=[Append-only: una fila por observación E…, TradingRepository, ._dt(), ._json_or_none()]
- "database_repository_tradingrepository_sync_trade_journal": ".sync_trade_journal()" | kind=code-symbol | source=database/repository.py:L1376 | neighbors=[Copia al journal cualquier trade operat…, TradingRepository, .database_diagnostics(), ._upsert_trade_journal_session()]
- "database_repository_tradingrepository_upsert_trade_visual_audit": ".upsert_trade_visual_audit()" | kind=code-symbol | source=database/repository.py:L895 | neighbors=[Congela entry_* sólo una vez; latest_* …, TradingRepository, ._dt(), ._json_or_none()]
- "database_repository_tradingrepository_upsert_worker_runtime_state": ".upsert_worker_runtime_state()" | kind=code-symbol | source=database/repository.py:L714 | neighbors=[TradingRepository, ._dt(), ._float_or_none(), ._json_or_none()]
- "execution_live_trading_engine": "live_trading_engine.py" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L1 | neighbors=[symbol_policy.py, smc_visual_context.py, LiveTradingConfig, LiveTradingEngine]
- "execution_live_trading_engine_livetradingengine_analysis_invalidation_exit": "._analysis_invalidation_exit()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L1739 | neighbors=[LiveTradingEngine, ._persist_audit_event(), ._monitor_break_even_positions(), Cierra una pérdida controlada cuando la…]
- "execution_live_trading_engine_livetradingengine_arps_time_stop_exit": "._arps_time_stop_exit()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L1895 | neighbors=[LiveTradingEngine, ._persist_audit_event(), ._monitor_break_even_positions(), Invalidación M1 persistente + time stop…]
- "execution_live_trading_engine_livetradingengine_break_even_price_tolerance": "._break_even_price_tolerance()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L1673 | neighbors=[LiveTradingEngine, ._manage_runner_extension(), ._monitor_break_even_positions(), Tolerancia de confirmación alineada al …]
- "execution_live_trading_engine_livetradingengine_commit_forex_processed_symbols": "._commit_forex_processed_symbols()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L1516 | neighbors=[LiveTradingEngine, ._canonical_bot_profile(), .run_daemon(), Marca la vela M5 como procesada sólo tr…]
- "execution_live_trading_engine_livetradingengine_current_strategy_view_from_analysis": "._current_strategy_view_from_analysis()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L5033 | neighbors=[LiveTradingEngine, ._persist_entry_audit_immediately(), ._refresh_current_strategy_views(), Normaliza cualquier resultado MTF a una…]
- "execution_live_trading_engine_livetradingengine_forex_due_symbols": "._forex_due_symbols()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L1452 | neighbors=[LiveTradingEngine, ._canonical_bot_profile(), .run_daemon(), Analiza perfiles SMC una sola vez por c…]
- "execution_live_trading_engine_livetradingengine_forex_exposure_guard": "._forex_exposure_guard()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L1377 | neighbors=[LiveTradingEngine, ._forex_pair_currencies(), ._position_limit_result(), Bloqueo DB-global por exposición Forex,…]
- "execution_live_trading_engine_livetradingengine_forex_rollover_entry_gate": "._forex_rollover_entry_gate()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L3441 | neighbors=[LiveTradingEngine, ._forex_rollover_status(), ._is_forex_symbol(), .process_symbol()]
- "execution_live_trading_engine_livetradingengine_forex_rollover_status": "._forex_rollover_status()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L3360 | neighbors=[LiveTradingEngine, ._close_forex_positions_for_rollover(), ._forex_rollover_entry_gate(), Ventana Forex: Tokio 09:00 hasta cutoff…]
- "execution_live_trading_engine_livetradingengine_gold_smc_session_state": "._gold_smc_session_state()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L1084 | neighbors=[LiveTradingEngine, ._gold_smc_entry_gate(), ._monitor_break_even_positions(), Ventana DST-safe: Tokio 09:00 hasta la …]
- "execution_live_trading_engine_livetradingengine_is_forex_symbol": "._is_forex_symbol()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L3347 | neighbors=[LiveTradingEngine, ._close_forex_positions_for_rollover(), ._forex_rollover_entry_gate(), Reconoce pares FX estándar aun cuando e…]
- "execution_live_trading_engine_livetradingengine_jump_quality_gate": "._jump_quality_gate()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L3526 | neighbors=[LiveTradingEngine, ._is_jump_symbol(), .process_symbol(), Filtro extra para Jump basado en la mue…]
- "execution_live_trading_engine_livetradingengine_market_signal_diagnostics": "._market_signal_diagnostics()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L1313 | neighbors=[LiveTradingEngine, ._signal_entry_price(), .process_symbol(), Comprueba si el mercado actual invalida…]
- "execution_live_trading_engine_livetradingengine_orb_exposure_guard": "._orb_exposure_guard()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L3669 | neighbors=[LiveTradingEngine, ._trade_has_confirmed_break_even(), .process_symbol(), Evita S&P 500 + Nasdaq simultáneos hast…]
- "execution_live_trading_engine_livetradingengine_orb_higher_timeframe_context": "._orb_higher_timeframe_context()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L3582 | neighbors=[LiveTradingEngine, .process_symbol(), ._refresh_current_strategy_views(), Obtiene contexto H1/M15 sin convertir O…]
- "execution_live_trading_engine_livetradingengine_persist_entry_audit_immediately": "._persist_entry_audit_immediately()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L2524 | neighbors=[LiveTradingEngine, ._current_strategy_view_from_analysis(), .process_symbol(), Congela tesis y snapshot inicial apenas…]
- "execution_live_trading_engine_livetradingengine_quarantine_file": "._quarantine_file()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L459 | neighbors=[LiveTradingEngine, ._load_quarantine_unlocked(), ._quarantine_storage_lock(), ._save_quarantine_unlocked()]
- "execution_live_trading_engine_livetradingengine_run_once": ".run_once()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L4839 | neighbors=[LiveTradingEngine, ._monitor_break_even_positions(), .process_symbols(), .sync_closed_trades()]
- "execution_live_trading_engine_livetradingengine_trade_has_confirmed_break_even": "._trade_has_confirmed_break_even()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L3648 | neighbors=[LiveTradingEngine, ._gold_smc_exposure_open(), ._orb_exposure_guard(), Confirma BE por metadata o por un SL pe…]
- "execution_live_trading_engine_livetradingengine_trade_metadata": "._trade_metadata()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L1580 | neighbors=[LiveTradingEngine, ._gold_smc_exposure_open(), ._monitor_break_even_positions(), ._trade_owned_by_current_bot()]
- "execution_multi_timeframe_multitimeframeanalyzer_get_h1_context": "._get_h1_context()" | kind=code-symbol | source=strategy/execution/multi_timeframe.py:L368 | neighbors=[MultiTimeframeAnalyzer, .analyze_symbol(), ._as_time(), Obtiene un contexto H1 direccional sin …]
- "execution_paper_trade_executor_papertradeexecutor_execute_trade": ".execute_trade()" | kind=code-symbol | source=strategy/execution/paper_trade_executor.py:L78 | neighbors=[PaperTradeExecutor, ._build_execution_key(), ._to_managed_position(), ._validate_request()]
- "execution_trade_executor": "trade_executor.py" | kind=code-symbol | source=strategy/execution/trade_executor.py:L1 | neighbors=[ABC, TradeExecutionRequest, TradeExecutionResult, TradeExecutor]
- "execution_trade_outcome_policy_decisive_outcome": "decisive_outcome()" | kind=code-symbol | source=strategy/execution/trade_outcome_policy.py:L23 | neighbors=[trade_outcome_policy.py, is_break_even_rr(), safe_float(), Devuelve WIN / LOSS / BREAK_EVEN / OPEN…]
- "monitoring_position_monitoring_service_positionmonitoringservice_monitor_position": ".monitor_position()" | kind=code-symbol | source=monitoring/position_monitoring_service.py:L64 | neighbors=[PositionMonitoringService, .monitor_open_positions(), ._resolve_exit_reason(), Procesa un único tick/precio para una p…]
- "reporting_console_reporting_service": "console_reporting_service.py" | kind=code-symbol | source=reporting/console_reporting_service.py:L1 | neighbors=[ConsoleReportingConfig, ConsoleReportingService, __init__.py, test_console_reporting_service.py]
- "reporting_console_reporting_service_consolereportingservice_fmt": "._fmt()" | kind=code-symbol | source=reporting/console_reporting_service.py:L76 | neighbors=[ConsoleReportingService, ._print_confirmation_diag(), .print_startup(), ._print_trade_fields()]

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-017.json

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
