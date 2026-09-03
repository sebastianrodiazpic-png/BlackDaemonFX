# Node Description Batch 38 of 56

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

- "tests_test_v68_persistent_entry_vs_now_dataset_test_xlsx_exports_entry_vs_now_sheet": "test_xlsx_exports_entry_vs_now_sheet()" | kind=code-symbol | source=tests/test_v68_persistent_entry_vs_now_dataset.py:L87 | neighbors=[test_v68_persistent_entry_vs_now_datase…, _repo_with_trade()] | lang=en
- "tests_test_v69_forex_event_scheduler_test_forex_event_scheduler_only_releases_new_closed_m5": "test_forex_event_scheduler_only_releases_new_closed_m5()" | kind=code-symbol | source=tests/test_v69_forex_event_scheduler.py:L58 | neighbors=[test_v69_forex_event_scheduler.py, _event_engine()] | lang=en
- "tests_test_v69_forex_event_scheduler_test_forex_scheduler_retries_same_bar_after_technical_error": "test_forex_scheduler_retries_same_bar_after_technical_error()" | kind=code-symbol | source=tests/test_v69_forex_event_scheduler.py:L71 | neighbors=[test_v69_forex_event_scheduler.py, _event_engine()] | lang=en
- "tests_test_v69_forex_event_scheduler_test_synthetic_is_event_filtered_since_v93": "test_synthetic_is_event_filtered_since_v93()" | kind=code-symbol | source=tests/test_v69_forex_event_scheduler.py:L78 | neighbors=[test_v69_forex_event_scheduler.py, _event_engine()] | lang=en
- "tests_test_v71_balanced_recent_analysis_test_orb_flood_does_not_hide_forex_or_synthetics": "test_orb_flood_does_not_hide_forex_or_synthetics()" | kind=code-symbol | source=tests/test_v71_balanced_recent_analysis.py:L20 | neighbors=[test_v71_balanced_recent_analysis.py, _event()] | lang=en
- "tests_test_v71_balanced_recent_analysis_test_recent_results_are_deduped_by_profile_symbol_action": "test_recent_results_are_deduped_by_profile_symbol_action()" | kind=code-symbol | source=tests/test_v71_balanced_recent_analysis.py:L51 | neighbors=[test_v71_balanced_recent_analysis.py, _event()] | lang=en
- "tests_test_v74_fast_navigation_test_instruments_cache_invalidates_after_catalog_change": "test_instruments_cache_invalidates_after_catalog_change()" | kind=code-symbol | source=tests/test_v74_fast_navigation.py:L58 | neighbors=[test_v74_fast_navigation.py, _service()] | lang=en
- "tests_test_v74_fast_navigation_test_instruments_payload_is_light_and_cached": "test_instruments_payload_is_light_and_cached()" | kind=code-symbol | source=tests/test_v74_fast_navigation.py:L44 | neighbors=[test_v74_fast_navigation.py, _service()] | lang=en
- "tests_test_v76_unified_multibot_orb_htf_test_neutral_h1_does_not_block_orb": "test_neutral_h1_does_not_block_orb()" | kind=code-symbol | source=tests/test_v76_unified_multibot_orb_htf.py:L50 | neighbors=[test_v76_unified_multibot_orb_htf.py, _engine()] | lang=en
- "tests_test_v76_unified_multibot_orb_htf_test_orb_buy_is_blocked_against_bearish_h1_and_m15": "test_orb_buy_is_blocked_against_bearish_h1_and_m15()" | kind=code-symbol | source=tests/test_v76_unified_multibot_orb_htf.py:L33 | neighbors=[test_v76_unified_multibot_orb_htf.py, _engine()] | lang=en
- "tests_test_v76_unified_multibot_orb_htf_test_orb_sell_is_aligned_with_bearish_context": "test_orb_sell_is_aligned_with_bearish_context()" | kind=code-symbol | source=tests/test_v76_unified_multibot_orb_htf.py:L42 | neighbors=[test_v76_unified_multibot_orb_htf.py, _engine()] | lang=en
- "tests_test_v79_universal_open_position_audit_test_live_market_snapshot_persists_for_forex": "test_live_market_snapshot_persists_for_forex()" | kind=code-symbol | source=tests/test_v79_universal_open_position_audit.py:L38 | neighbors=[test_v79_universal_open_position_audit.…, _engine()] | lang=en
- "tests_test_v79_universal_open_position_audit_test_live_market_snapshot_persists_for_orb": "test_live_market_snapshot_persists_for_orb()" | kind=code-symbol | source=tests/test_v79_universal_open_position_audit.py:L24 | neighbors=[test_v79_universal_open_position_audit.…, _engine()] | lang=en
- "tests_test_v79_universal_open_position_audit_test_live_market_snapshot_persists_for_synthetic": "test_live_market_snapshot_persists_for_synthetic()" | kind=code-symbol | source=tests/test_v79_universal_open_position_audit.py:L48 | neighbors=[test_v79_universal_open_position_audit.…, _engine()] | lang=en
- "tests_test_v81_trade_audit_excel_export_payload": "_payload()" | kind=code-symbol | source=tests/test_v81_trade_audit_excel_export.py:L7 | neighbors=[test_v81_trade_audit_excel_export.py, test_exporter_creates_multisheet_xlsx()] | lang=en
- "tests_test_v81_trade_audit_excel_export_test_exporter_creates_multisheet_xlsx": "test_exporter_creates_multisheet_xlsx()" | kind=code-symbol | source=tests/test_v81_trade_audit_excel_export.py:L57 | neighbors=[test_v81_trade_audit_excel_export.py, _payload()] | lang=en
- "tests_test_v86_durable_trade_audit_export_test_fill_persists_entry_context_and_initial_append_only_snapshot": "test_fill_persists_entry_context_and_initial_append_only_snapshot()" | kind=code-symbol | source=tests/test_v86_durable_trade_audit_export.py:L23 | neighbors=[test_v86_durable_trade_audit_export.py, EntryAuditRepo] | lang=en
- "tests_test_v86_durable_trade_audit_export_test_immediate_snapshot_is_idempotent_on_persistence_retry": "test_immediate_snapshot_is_idempotent_on_persistence_retry()" | kind=code-symbol | source=tests/test_v86_durable_trade_audit_export.py:L50 | neighbors=[test_v86_durable_trade_audit_export.py, EntryAuditRepo] | lang=en
- "tests_test_v87_gold_asia_new_york_session_test_gold_entry_gate_does_not_affect_forex_or_synthetics": "test_gold_entry_gate_does_not_affect_forex_or_synthetics()" | kind=code-symbol | source=tests/test_v87_gold_asia_new_york_session.py:L34 | neighbors=[test_v87_gold_asia_new_york_session.py, _engine()] | lang=en
- "tests_test_v87_gold_asia_new_york_session_test_gold_window_opens_at_tokyo_0900_and_closes_at_new_york_0930_summer": "test_gold_window_opens_at_tokyo_0900_and_closes_at_new_york_0930_summer()" | kind=code-symbol | source=tests/test_v87_gold_asia_new_york_session.py:L21 | neighbors=[test_v87_gold_asia_new_york_session.py, _engine()] | lang=en
- "tests_test_v87_gold_asia_new_york_session_test_gold_window_respects_new_york_winter_dst": "test_gold_window_respects_new_york_winter_dst()" | kind=code-symbol | source=tests/test_v87_gold_asia_new_york_session.py:L28 | neighbors=[test_v87_gold_asia_new_york_session.py, _engine()] | lang=en
- "tests_test_v87_gold_asia_new_york_session_test_orb_detects_open_gold_smc_exposure": "test_orb_detects_open_gold_smc_exposure()" | kind=code-symbol | source=tests/test_v87_gold_asia_new_york_session.py:L41 | neighbors=[test_v87_gold_asia_new_york_session.py, _engine()] | lang=en
- "trade_lifecycle_manager_tradelifecyclemanager_apply_simulation_result": "._apply_simulation_result()" | kind=code-symbol | source=trade_lifecycle_manager.py:L629 | neighbors=[TradeLifecycleManager, .execute()] | lang=en
- "trade_lifecycle_manager_tradelifecyclemanager_get_completed_trades": ".get_completed_trades()" | kind=code-symbol | source=trade_lifecycle_manager.py:L878 | neighbors=[TradeLifecycleManager, .is_final()] | lang=en
- "trade_lifecycle_manager_tradelifecyclemanager_get_timeframe": "._get_timeframe()" | kind=code-symbol | source=trade_lifecycle_manager.py:L779 | neighbors=[TradeLifecycleManager, .create_from_signal()] | lang=en
- "trade_lifecycle_manager_tradelifecyclemanager_monitor_open_executions": ".monitor_open_executions()" | kind=code-symbol | source=trade_lifecycle_manager.py:L556 | neighbors=[TradeLifecycleManager, .monitor_execution()] | lang=en
- "trade_lifecycle_manager_tradelifecyclemanager_validate_candles": "._validate_candles()" | kind=code-symbol | source=trade_lifecycle_manager.py:L808 | neighbors=[TradeLifecycleManager, .execute()] | lang=en
- "trade_lifecycle_manager_tradelifecyclemanager_validate_signal": "._validate_signal()" | kind=code-symbol | source=trade_lifecycle_manager.py:L712 | neighbors=[TradeLifecycleManager, .create_from_signal()] | lang=en
- "tradeexecutor": "TradeExecutor" | kind=code-symbol | neighbors=[MT5TradeExecutor, PaperTradeExecutor] | lang=en
- "app_main_multibotinstanceguard_init": ".__init__()" | kind=code-symbol | source=app/main.py:L1612 | neighbors=[_MultiBotInstanceGuard] | lang=en
- "backtest_backtest_metric": "backtest_metric.py" | kind=code-symbol | source=strategy/backtest/backtest_metric.py:L1 | neighbors=[calculate_backtest_metrics()] | lang=en
- "backtest_backtest_metric_rationale_17": "Calcula métricas completas de un backtest con\r     gestión de capital y riesgo." | kind=entity | source=strategy/backtest/backtest_metric.py:L17 | neighbors=[calculate_backtest_metrics()] | lang=en
- "backtesting_backtest_money_management_rationale_12": "Calcula cuánto dinero se arriesga\r     en una operación.\r \r     Ejemplo:" | kind=entity | source=backtesting/backtest_money_management.py:L12 | neighbors=[calculate_risk_amount()] | lang=es
- "backtesting_backtest_money_management_rationale_402": "Genera estadísticas financieras\r     después de aplicar money management." | kind=entity | source=backtesting/backtest_money_management.py:L402 | neighbors=[get_money_management_summary()] | lang=en
- "backtesting_backtest_money_management_rationale_52": "Calcula la ganancia o pérdida monetaria\r     utilizando el R:R realizado." | kind=entity | source=backtesting/backtest_money_management.py:L52 | neighbors=[calculate_trade_pnl()] | lang=en
- "backtesting_backtest_money_management_rationale_659": "Guarda los resultados financieros\r     en un archivo CSV." | kind=entity | source=backtesting/backtest_money_management.py:L659 | neighbors=[save_money_management_results()] | lang=es
- "backtesting_backtest_money_management_rationale_95": "Aplica gestión monetaria a los resultados\r     de un backtest.\r \r     Parámetros" | kind=entity | source=backtesting/backtest_money_management.py:L95 | neighbors=[apply_money_management()] | lang=fr
- "backtesting_backtest_pipeline_rationale_30": "Ejecuta el flujo completo histórico -> backtest -> gestión -> SQLite -> Excel." | kind=entity | source=backtesting/backtest_pipeline.py:L30 | neighbors=[run_full_backtest_pipeline()] | lang=es
- "backtesting_trade_simulator_rationale_134": "Simula una operación utilizando las velas\r     posteriores a la entrada." | kind=entity | source=backtesting/trade_simulator.py:L134 | neighbors=[simulate_trade()] | lang=es
- "backtesting_trade_simulator_rationale_14": "Calcula el resultado real de una operación\r     expresado en unidades de riesgo" | kind=entity | source=backtesting/trade_simulator.py:L14 | neighbors=[calculate_realized_rr()] | lang=en

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-037.json

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
