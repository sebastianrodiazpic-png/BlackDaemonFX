# Node Description Batch 31 of 56

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

- "execution_live_paper_trading_engine_livepapertradingengine_signal_key": "._signal_key()" | kind=code-symbol | source=strategy/execution/live_paper_trading_engine.py:L166 | neighbors=[LivePaperTradingEngine, .run_once()]
- "execution_live_trading_engine_livetradingengine_break_even_initial_stop": "._break_even_initial_stop()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L1587 | neighbors=[LiveTradingEngine, ._monitor_break_even_positions()]
- "execution_live_trading_engine_livetradingengine_execution_key": "._execution_key()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L690 | neighbors=[LiveTradingEngine, .process_symbol()]
- "execution_live_trading_engine_livetradingengine_forex_pair_currencies": "._forex_pair_currencies()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L1368 | neighbors=[LiveTradingEngine, ._forex_exposure_guard()]
- "execution_live_trading_engine_livetradingengine_init": ".__init__()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L343 | neighbors=[LiveTradingEngine, LiveTradingConfig]
- "execution_live_trading_engine_livetradingengine_parse_quarantine_time": "._parse_quarantine_time()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L551 | neighbors=[LiveTradingEngine, ._quarantine_result()]
- "execution_live_trading_engine_livetradingengine_run_loop": ".run_loop()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L5792 | neighbors=[LiveTradingEngine, .run_daemon()]
- "execution_live_trading_engine_livetradingengine_save_signal": "._save_signal()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L1218 | neighbors=[LiveTradingEngine, .process_symbol()]
- "execution_live_trading_engine_livetradingengine_selection_profile_for_bot": "._selection_profile_for_bot()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L5001 | neighbors=[LiveTradingEngine, ._selected_cycle_symbols()]
- "execution_live_trading_engine_livetradingengine_signal_entry_price": "._signal_entry_price()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L1306 | neighbors=[LiveTradingEngine, ._market_signal_diagnostics()]
- "execution_live_trading_engine_livetradingengine_total_position_limit": "._total_position_limit()" | kind=code-symbol | source=strategy/execution/live_trading_engine.py:L1238 | neighbors=[LiveTradingEngine, ._open_trade_diagnostics()]
- "execution_multi_timeframe_multitimeframeanalyzer_add_transition": "._add_transition()" | kind=code-symbol | source=strategy/execution/multi_timeframe.py:L224 | neighbors=[MultiTimeframeAnalyzer, .analyze_symbol()]
- "execution_multi_timeframe_multitimeframeanalyzer_build_result": "._build_result()" | kind=code-symbol | source=strategy/execution/multi_timeframe.py:L811 | neighbors=[MultiTimeframeAnalyzer, .analyze_symbol()]
- "execution_multi_timeframe_multitimeframeanalyzer_cached_stage": ".cached_stage()" | kind=code-symbol | source=strategy/execution/multi_timeframe.py:L141 | neighbors=[MultiTimeframeAnalyzer, Devuelve un snapshot seguro de una etap…]
- "execution_multi_timeframe_multitimeframeanalyzer_clear_stage_cache": ".clear_stage_cache()" | kind=code-symbol | source=strategy/execution/multi_timeframe.py:L125 | neighbors=[MultiTimeframeAnalyzer, Invalida la caché completa o una etapa …]
- "execution_multi_timeframe_multitimeframeanalyzer_get_closed_candles": "._get_closed_candles()" | kind=code-symbol | source=strategy/execution/multi_timeframe.py:L239 | neighbors=[MultiTimeframeAnalyzer, ._get_stage_result()]
- "execution_multi_timeframe_multitimeframeanalyzer_init": ".__init__()" | kind=code-symbol | source=strategy/execution/multi_timeframe.py:L85 | neighbors=[MultiTimeframeAnalyzer, MultiTimeframeConfig]
- "execution_multi_timeframe_multitimeframeanalyzer_m15_setups": "._m15_setups()" | kind=code-symbol | source=strategy/execution/multi_timeframe.py:L440 | neighbors=[MultiTimeframeAnalyzer, .analyze_symbol()]
- "execution_multi_timeframe_multitimeframeanalyzer_m5_confirmations": "._m5_confirmations()" | kind=code-symbol | source=strategy/execution/multi_timeframe.py:L488 | neighbors=[MultiTimeframeAnalyzer, .analyze_symbol()]
- "execution_multi_timeframe_multitimeframeanalyzer_new_transitions": "._new_transitions()" | kind=code-symbol | source=strategy/execution/multi_timeframe.py:L215 | neighbors=[MultiTimeframeAnalyzer, .analyze_symbol()]
- "execution_multi_timeframe_multitimeframeanalyzer_next_refresh_at": "._next_refresh_at()" | kind=code-symbol | source=strategy/execution/multi_timeframe.py:L148 | neighbors=[MultiTimeframeAnalyzer, ._get_stage_result()]
- "execution_multi_timeframe_multitimeframeanalyzer_run_pipeline": "._run_pipeline()" | kind=code-symbol | source=strategy/execution/multi_timeframe.py:L268 | neighbors=[MultiTimeframeAnalyzer, ._get_stage_result()]
- "execution_multi_timeframe_multitimeframeanalyzer_safe_float": "._safe_float()" | kind=code-symbol | source=strategy/execution/multi_timeframe.py:L1564 | neighbors=[MultiTimeframeAnalyzer, .analyze_symbol()]
- "execution_multi_timeframe_multitimeframeanalyzer_trend_direction": "._trend_direction()" | kind=code-symbol | source=strategy/execution/multi_timeframe.py:L355 | neighbors=[MultiTimeframeAnalyzer, .analyze_symbol()]
- "execution_paper_trade_executor_papertradeexecutor_build_execution_key": "._build_execution_key()" | kind=code-symbol | source=strategy/execution/paper_trade_executor.py:L666 | neighbors=[PaperTradeExecutor, .execute_trade()]
- "execution_paper_trade_executor_papertradeexecutor_merge_paper_and_managed_position": "._merge_paper_and_managed_position()" | kind=code-symbol | source=strategy/execution/paper_trade_executor.py:L515 | neighbors=[PaperTradeExecutor, .get_position()]
- "execution_paper_trade_executor_papertradeexecutor_sync_position_update_from_manager": "._sync_position_update_from_manager()" | kind=code-symbol | source=strategy/execution/paper_trade_executor.py:L473 | neighbors=[PaperTradeExecutor, ._sync_position_close_from_manager()]
- "execution_paper_trade_executor_papertradeexecutor_to_managed_position": "._to_managed_position()" | kind=code-symbol | source=strategy/execution/paper_trade_executor.py:L461 | neighbors=[PaperTradeExecutor, .execute_trade()]
- "execution_paper_trade_executor_papertradeexecutor_validate_request": "._validate_request()" | kind=code-symbol | source=strategy/execution/paper_trade_executor.py:L578 | neighbors=[PaperTradeExecutor, .execute_trade()]
- "execution_trade_executor_tradeexecutor_execute_trade": ".execute_trade()" | kind=code-symbol | source=strategy/execution/trade_executor.py:L210 | neighbors=[Ejecuta una operación.          Imple…, TradeExecutor]
- "execution_trade_executor_tradeexecutor_get_position": ".get_position()" | kind=code-symbol | source=strategy/execution/trade_executor.py:L228 | neighbors=[Obtiene el estado actual         de un…, TradeExecutor]
- "execution_trade_pipeline_empty_setups": "_empty_setups()" | kind=code-symbol | source=strategy/execution/trade_pipeline.py:L91 | neighbors=[trade_pipeline.py, build_setups()]
- "execution_trade_pipeline_latest_sweep": "_latest_sweep()" | kind=code-symbol | source=strategy/execution/trade_pipeline.py:L113 | neighbors=[trade_pipeline.py, build_setups()]
- "execution_trade_pipeline_rationale_179": "Filtra una columna de dirección respetando la política del símbolo.      La mism" | kind=entity | source=strategy/execution/trade_pipeline.py:L179 | neighbors=[_filter_by_policy(), M5ConfirmationConfig]
- "execution_trade_pipeline_rationale_203": "Ejecuta la cadena SMC completa. Si symbol es Boom/Crash, aplica la política de d" | kind=entity | source=strategy/execution/trade_pipeline.py:L203 | neighbors=[run_trade_pipeline(), M5ConfirmationConfig]
- "execution_trade_pipeline_trend_at": "_trend_at()" | kind=code-symbol | source=strategy/execution/trade_pipeline.py:L123 | neighbors=[trade_pipeline.py, build_setups()]
- "execution_trade_pipeline_validate_price_data": "_validate_price_data()" | kind=code-symbol | source=strategy/execution/trade_pipeline.py:L100 | neighbors=[trade_pipeline.py, run_trade_pipeline()]
- "monitoring_position_monitoring_service_positionmonitoringservice_resolve_exit_reason": "._resolve_exit_reason()" | kind=code-symbol | source=monitoring/position_monitoring_service.py:L187 | neighbors=[PositionMonitoringService, .monitor_position()]
- "monitoring_position_monitoring_service_rationale_157": "Procesa las posiciones abiertas que tengan un precio disponible.          No fal" | kind=entity | source=monitoring/position_monitoring_service.py:L157 | neighbors=[.monitor_open_positions(), PositionManager]
- "monitoring_position_monitoring_service_rationale_17": "Vigila las posiciones abiertas administradas por PositionManager.      Responsab" | kind=entity | source=monitoring/position_monitoring_service.py:L17 | neighbors=[PositionMonitoringService, PositionManager]

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-030.json

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
