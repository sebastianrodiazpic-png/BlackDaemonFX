# Node Description Batch 23 of 56

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
Write every description in Italian (it). Do not switch languages.
No marketing language.
Respond ONLY with a JSON object mapping each node id (as a string) to its
one-sentence description — no prose, no markdown fences.

- "execution_live_trading_engine_livetradingengine_persist_live_position_market_snapshots": "._persist_live_position_market_snapshots()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L2469 | neighbors=[LiveTradingEngine, ._monitor_break_even_positions(), Persiste telemetría ligera de posicione…]
- "execution_live_trading_engine_livetradingengine_recover_unpersisted_open_positions": "._recover_unpersisted_open_positions()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L999 | neighbors=[LiveTradingEngine, ._persist_audit_event(), Auto-repara posiciones MT5 del daemon q…]
- "execution_live_trading_engine_livetradingengine_recoverable_quarantine_details": "._recoverable_quarantine_details()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L527 | neighbors=[LiveTradingEngine, ._quarantine_result(), ._quarantine_symbol()]
- "execution_live_trading_engine_livetradingengine_save_quarantine": "._save_quarantine()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L564 | neighbors=[LiveTradingEngine, ._quarantine_storage_lock(), ._save_quarantine_unlocked()]
- "execution_live_trading_engine_livetradingengine_selected_cycle_symbols": "._selected_cycle_symbols()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L5007 | neighbors=[LiveTradingEngine, .run_daemon(), ._selection_profile_for_bot()]
- "execution_live_trading_engine_livetradingengine_symbol_matches_split_profile": "._symbol_matches_split_profile()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L1054 | neighbors=[LiveTradingEngine, ._canonical_bot_profile(), ._trade_owned_by_current_bot()]
- "execution_live_trading_engine_livetradingengine_sync_closed_trades": ".sync_closed_trades()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L5795 | neighbors=[LiveTradingEngine, .run_once(), ._persist_audit_event()]
- "execution_live_trading_engine_livetradingengine_update_excursion_metrics": "._update_excursion_metrics()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L1689 | neighbors=[LiveTradingEngine, ._monitor_break_even_positions(), Actualiza MFE/MAE muestreados por el mo…]
- "execution_live_trading_engine_livetradingengine_validate_post_fill_risk": "._validate_post_fill_risk()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L624 | neighbors=[LiveTradingEngine, .process_symbol(), Lee la posición real y recalcula el rie…]
- "execution_multi_timeframe": "multi_timeframe.py" | kind=code-symbol | source=strategy/execution/multi_timeframe.py:L1 | neighbors=[symbol_policy.py, MultiTimeframeAnalyzer, MultiTimeframeConfig]
- "execution_multi_timeframe_multitimeframeanalyzer_pipeline_diagnostics": "._pipeline_diagnostics()" | kind=code-symbol | source=strategy/execution/multi_timeframe.py:L304 | neighbors=[MultiTimeframeAnalyzer, .analyze_symbol(), ._as_time()]
- "execution_multi_timeframe_multitimeframeanalyzer_select_ordered_pair": "._select_ordered_pair()" | kind=code-symbol | source=strategy/execution/multi_timeframe.py:L534 | neighbors=[MultiTimeframeAnalyzer, .analyze_symbol(), ._as_time()]
- "execution_multi_timeframe_multitimeframeanalyzer_signal_age_diagnostics": "._signal_age_diagnostics()" | kind=code-symbol | source=strategy/execution/multi_timeframe.py:L673 | neighbors=[MultiTimeframeAnalyzer, .analyze_symbol(), ._as_time()]
- "execution_multi_timeframe_rationale_126": "Invalida la caché completa o una etapa concreta." | kind=entity | source=strategy/execution/multi_timeframe.py:L126 | neighbors=[.clear_stage_cache(), PipelineConfig, H1ExtremeDojiConfig]
- "execution_multi_timeframe_rationale_142": "Devuelve un snapshot seguro de una etapa para auditoría visual." | kind=entity | source=strategy/execution/multi_timeframe.py:L142 | neighbors=[.cached_stage(), PipelineConfig, H1ExtremeDojiConfig]
- "execution_multi_timeframe_rationale_160": "Obtiene una etapa H1/M15/M5 usando caché hasta la próxima vela cerrada." | kind=entity | source=strategy/execution/multi_timeframe.py:L160 | neighbors=[._get_stage_result(), PipelineConfig, H1ExtremeDojiConfig]
- "execution_multi_timeframe_rationale_18": "Configuración del flujo:          H1  -> contexto / tendencia         M15 -> set" | kind=entity | source=strategy/execution/multi_timeframe.py:L18 | neighbors=[MultiTimeframeConfig, PipelineConfig, H1ExtremeDojiConfig]
- "execution_multi_timeframe_rationale_369": "Obtiene un contexto H1 direccional sin exigir que el proveedor         controlad" | kind=entity | source=strategy/execution/multi_timeframe.py:L369 | neighbors=[._get_h1_context(), PipelineConfig, H1ExtremeDojiConfig]
- "execution_multi_timeframe_rationale_52": "Analizador multi-temporal H1 -> M15 -> M5.      Estados principales:          ST" | kind=entity | source=strategy/execution/multi_timeframe.py:L52 | neighbors=[MultiTimeframeAnalyzer, PipelineConfig, H1ExtremeDojiConfig]
- "execution_paper_trade_executor": "paper_trade_executor.py" | kind=code-symbol | source=strategy/execution/paper_trade_executor.py:L1 | neighbors=[PaperTradeExecutor, position_monitoring_service.py, position_manager.py]
- "execution_paper_trade_executor_papertradeexecutor_close_position": ".close_position()" | kind=code-symbol | source=strategy/execution/paper_trade_executor.py:L357 | neighbors=[PaperTradeExecutor, .get_position(), ._sync_position_close_from_manager()]
- "execution_paper_trade_executor_papertradeexecutor_get_position": ".get_position()" | kind=code-symbol | source=strategy/execution/paper_trade_executor.py:L328 | neighbors=[PaperTradeExecutor, .close_position(), ._merge_paper_and_managed_position()]
- "execution_paper_trade_executor_papertradeexecutor_sync_position_close_from_manager": "._sync_position_close_from_manager()" | kind=code-symbol | source=strategy/execution/paper_trade_executor.py:L495 | neighbors=[PaperTradeExecutor, .close_position(), ._sync_position_update_from_manager()]
- "execution_runner_extension_manager": "runner_extension_manager.py" | kind=code-symbol | source=strategy/execution/runner_extension_manager.py:L1 | neighbors=[evaluate_runner_continuation(), rr_price(), RunnerExtensionDecision]
- "execution_runner_extension_manager_evaluate_runner_continuation": "evaluate_runner_continuation()" | kind=code-symbol | source=strategy/execution/runner_extension_manager.py:L28 | neighbors=[runner_extension_manager.py, RunnerExtensionDecision, Evalúa si un RUNNER que ya alcanzó 2R/3…]
- "execution_trade_outcome_policy": "trade_outcome_policy.py" | kind=code-symbol | source=strategy/execution/trade_outcome_policy.py:L1 | neighbors=[decisive_outcome(), is_break_even_rr(), safe_float()]
- "execution_trade_outcome_policy_is_break_even_rr": "is_break_even_rr()" | kind=code-symbol | source=strategy/execution/trade_outcome_policy.py:L16 | neighbors=[trade_outcome_policy.py, decisive_outcome(), safe_float()]
- "execution_trade_outcome_policy_safe_float": "safe_float()" | kind=code-symbol | source=strategy/execution/trade_outcome_policy.py:L9 | neighbors=[trade_outcome_policy.py, decisive_outcome(), is_break_even_rr()]
- "execution_trade_pipeline_filter_by_policy": "_filter_by_policy()" | kind=code-symbol | source=strategy/execution/trade_pipeline.py:L178 | neighbors=[trade_pipeline.py, Filtra una columna de dirección respeta…, run_trade_pipeline()]
- "livetradingengine": "LiveTradingEngine" | kind=code-symbol | neighbors=[Engine, FakeEngine, test_execution_path_uses_lifecycle_mana…]
- "monitoring_position_monitoring_service_positionmonitoringservice_monitor_open_positions": ".monitor_open_positions()" | kind=code-symbol | source=monitoring/position_monitoring_service.py:L153 | neighbors=[PositionMonitoringService, .monitor_position(), Procesa las posiciones abiertas que ten…]
- "monitoring_trade_monitor_trademonitor": "TradeMonitor" | kind=code-symbol | source=monitoring/trade_monitor.py:L1 | neighbors=[trade_monitor.py, .__init__(), .sync()]
- "orb_new_york_orb_discover_orb_symbols": "discover_orb_symbols()" | kind=code-symbol | source=strategy/orb/new_york_orb.py:L103 | neighbors=[new_york_orb.py, is_orb_eligible_symbol(), Descubre únicamente contratos ORB opera…]
- "orb_new_york_orb_is_orb_eligible_symbol": "is_orb_eligible_symbol()" | kind=code-symbol | source=strategy/orb/new_york_orb.py:L46 | neighbors=[new_york_orb.py, discover_orb_symbols(), classify_orb_market()]
- "orb_new_york_orb_is_orb_gold_symbol": "is_orb_gold_symbol()" | kind=code-symbol | source=strategy/orb/new_york_orb.py:L50 | neighbors=[new_york_orb.py, classify_orb_market(), True únicamente para las dos variantes …]
- "orb_new_york_orb_newyorkorbstrategy_session_poc": "._session_poc()" | kind=code-symbol | source=strategy/orb/new_york_orb.py:L221 | neighbors=[NewYorkORBStrategy, .analyze_symbol(), ._volume_column()]
- "orb_new_york_orb_newyorkorbstrategy_session_vwap": "._session_vwap()" | kind=code-symbol | source=strategy/orb/new_york_orb.py:L205 | neighbors=[NewYorkORBStrategy, .analyze_symbol(), ._volume_column()]
- "orb_new_york_orb_newyorkorbstrategy_volume_column": "._volume_column()" | kind=code-symbol | source=strategy/orb/new_york_orb.py:L193 | neighbors=[NewYorkORBStrategy, ._session_poc(), ._session_vwap()]
- "reporting_console_reporting_service_consolereportingservice_print_startup": ".print_startup()" | kind=code-symbol | source=reporting/console_reporting_service.py:L135 | neighbors=[ConsoleReportingService, ._fmt(), ._line()]
- "reporting_strategy_evaluation_distribution": "_distribution()" | kind=code-symbol | source=reporting/strategy_evaluation.py:L20 | neighbors=[strategy_evaluation.py, build_strategy_evaluation(), _number()]

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-022.json

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
