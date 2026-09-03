# Node Description Batch 4 of 56

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

- "database_repository_rationale_1757": "Devuelve el snapshot de cuenta más reciente como dict." | kind=entity | source=database/repository.py:L1757 | neighbors=[AccountSnapshot, AccountStatsReset, DaemonAuditEvent, InstrumentSelectionPreference, InstrumentSelectionProfilePreference, PositionVisualAudit] | lang=es
- "database_repository_rationale_1781": "Reinicia datos operativos conservando ``trade_journal``.          Cuenta activa" | kind=entity | source=database/repository.py:L1781 | neighbors=[AccountSnapshot, AccountStatsReset, DaemonAuditEvent, InstrumentSelectionPreference, InstrumentSelectionProfilePreference, PositionVisualAudit] | lang=en
- "database_repository_rationale_1935": "Crea una operación una sola vez usando:          1. execution_key         2. ext" | kind=entity | source=database/repository.py:L1935 | neighbors=[AccountSnapshot, AccountStatsReset, DaemonAuditEvent, InstrumentSelectionPreference, InstrumentSelectionProfilePreference, PositionVisualAudit] | lang=en
- "database_repository_rationale_206": "Convierte dict/list/etc. a JSON serializable." | kind=entity | source=database/repository.py:L206 | neighbors=[AccountSnapshot, AccountStatsReset, DaemonAuditEvent, InstrumentSelectionPreference, InstrumentSelectionProfilePreference, PositionVisualAudit] | lang=pt
- "database_repository_rationale_24": "Capa única de persistencia para:      - Señales SMC     - Operaciones     - Oper" | kind=entity | source=database/repository.py:L24 | neighbors=[AccountSnapshot, AccountStatsReset, DaemonAuditEvent, InstrumentSelectionPreference, InstrumentSelectionProfilePreference, PositionVisualAudit] | lang=es
- "database_repository_rationale_246": "Genera una clave única para evitar duplicar         operaciones importadas desde" | kind=entity | source=database/repository.py:L246 | neighbors=[AccountSnapshot, AccountStatsReset, DaemonAuditEvent, InstrumentSelectionPreference, InstrumentSelectionProfilePreference, PositionVisualAudit] | lang=es
- "database_repository_rationale_2753": "Sincroniza SQLite con MT5.          Solo marca una operación como CLOSED cuando:" | kind=entity | source=database/repository.py:L2753 | neighbors=[AccountSnapshot, AccountStatsReset, DaemonAuditEvent, InstrumentSelectionPreference, InstrumentSelectionProfilePreference, PositionVisualAudit] | lang=es
- "database_repository_rationale_281": "Construye una descripción del setup SMC." | kind=entity | source=database/repository.py:L281 | neighbors=[AccountSnapshot, AccountStatsReset, DaemonAuditEvent, InstrumentSelectionPreference, InstrumentSelectionProfilePreference, PositionVisualAudit] | lang=en
- "database_repository_rationale_2941": "Descubre posiciones abiertas en MT5 que todavía no existen en SQLite.          L" | kind=entity | source=database/repository.py:L2941 | neighbors=[AccountSnapshot, AccountStatsReset, DaemonAuditEvent, InstrumentSelectionPreference, InstrumentSelectionProfilePreference, PositionVisualAudit] | lang=es
- "database_repository_rationale_3104": "Reconstruye el historial permanente usando los deals de MT5.          Los deals" | kind=entity | source=database/repository.py:L3104 | neighbors=[AccountSnapshot, AccountStatsReset, DaemonAuditEvent, InstrumentSelectionPreference, InstrumentSelectionProfilePreference, PositionVisualAudit] | lang=es
- "database_repository_rationale_3338": "Diagnóstico entre SQLite y MT5." | kind=entity | source=database/repository.py:L3338 | neighbors=[AccountSnapshot, AccountStatsReset, DaemonAuditEvent, InstrumentSelectionPreference, InstrumentSelectionProfilePreference, PositionVisualAudit] | lang=es
- "database_repository_rationale_343": "Normaliza datos antes de crear un Trade." | kind=entity | source=database/repository.py:L343 | neighbors=[AccountSnapshot, AccountStatsReset, DaemonAuditEvent, InstrumentSelectionPreference, InstrumentSelectionProfilePreference, PositionVisualAudit] | lang=en
- "database_repository_rationale_431": "Convierte un objeto Trade de SQLAlchemy a dict." | kind=entity | source=database/repository.py:L431 | neighbors=[AccountSnapshot, AccountStatsReset, DaemonAuditEvent, InstrumentSelectionPreference, InstrumentSelectionProfilePreference, PositionVisualAudit] | lang=en
- "database_repository_rationale_477": "Persiste un evento sin sobrescribir eventos anteriores." | kind=entity | source=database/repository.py:L477 | neighbors=[AccountSnapshot, AccountStatsReset, DaemonAuditEvent, InstrumentSelectionPreference, InstrumentSelectionProfilePreference, PositionVisualAudit] | lang=fr
- "database_repository_rationale_517": "Retención incremental sin bloquear SQLite durante una eliminación masiva." | kind=entity | source=database/repository.py:L517 | neighbors=[AccountSnapshot, AccountStatsReset, DaemonAuditEvent, InstrumentSelectionPreference, InstrumentSelectionProfilePreference, PositionVisualAudit] | lang=en
- "database_repository_rationale_53": "Convierte distintos formatos de fecha a datetime UTC." | kind=entity | source=database/repository.py:L53 | neighbors=[AccountSnapshot, AccountStatsReset, DaemonAuditEvent, InstrumentSelectionPreference, InstrumentSelectionProfilePreference, PositionVisualAudit] | lang=en
- "database_repository_rationale_582": "Checkpoint WAL explícito; TRUNCATE se reserva para mantenimiento coordinado." | kind=entity | source=database/repository.py:L582 | neighbors=[AccountSnapshot, AccountStatsReset, DaemonAuditEvent, InstrumentSelectionPreference, InstrumentSelectionProfilePreference, PositionVisualAudit] | lang=es
- "database_repository_rationale_618": "Compactación explícita para ejecutar sólo con el daemon detenido." | kind=entity | source=database/repository.py:L618 | neighbors=[AccountSnapshot, AccountStatsReset, DaemonAuditEvent, InstrumentSelectionPreference, InstrumentSelectionProfilePreference, PositionVisualAudit] | lang=es
- "database_repository_rationale_660": "Datos compactos para evaluar ARPS/riesgo sin leer toda la auditoría." | kind=entity | source=database/repository.py:L660 | neighbors=[AccountSnapshot, AccountStatsReset, DaemonAuditEvent, InstrumentSelectionPreference, InstrumentSelectionProfilePreference, PositionVisualAudit] | lang=en
- "database_repository_rationale_83": "Convierte un valor a float o devuelve None." | kind=entity | source=database/repository.py:L83 | neighbors=[AccountSnapshot, AccountStatsReset, DaemonAuditEvent, InstrumentSelectionPreference, InstrumentSelectionProfilePreference, PositionVisualAudit] | lang=pt
- "database_repository_rationale_910": "Congela entry_* sólo una vez; latest_* puede actualizarse." | kind=entity | source=database/repository.py:L910 | neighbors=[AccountSnapshot, AccountStatsReset, DaemonAuditEvent, InstrumentSelectionPreference, InstrumentSelectionProfilePreference, PositionVisualAudit] | lang=it
- "database_repository_tradingrepository_upsert_trade_journal_session": "._upsert_trade_journal_session()" | kind=code-symbol | source=database/repository.py:L1348 | neighbors=[TradingRepository, .create_trade(), .create_trade_once(), .import_mt5_trade_history(), .sync_trade_journal(), .update_trade()] | lang=en
- "tests_test_demo_daemon_integration": "test_demo_daemon_integration.py" | kind=code-symbol | source=tests/test_demo_daemon_integration.py:L1 | neighbors=[trade_reporting_service.py, Analyzer, ExecutionRepo, Executor, FakeEngine, FakeLifecycleManager] | lang=en
- "tests_test_orb_new_york_strategy": "test_orb_new_york_strategy.py" | kind=code-symbol | source=tests/test_orb_new_york_strategy.py:L1 | neighbors=[FakeProvider, _session_candles(), _strategy(), test_gold_contract_score_prefers_more_p…, test_gold_contract_score_uses_spread_an…, test_orb_builds_15_minute_range_before_…] | lang=en
- "tests_test_paper_trade_executor": "test_paper_trade_executor.py" | kind=code-symbol | source=tests/test_paper_trade_executor.py:L1 | neighbors=[create_buy_request(), create_sell_request(), test_cannot_close_position_twice(), test_close_position(), test_duplicate_execution_is_blocked(), test_get_position()] | lang=en
- "tests_test_position_monitoring_service": "test_position_monitoring_service.py" | kind=code-symbol | source=tests/test_position_monitoring_service.py:L1 | neighbors=[position_monitoring_service.py, position_manager.py, create_buy_position(), create_sell_position(), test_closed_position_cannot_be_monitore…, test_monitor_buy_activates_break_even_a…] | lang=en
- "tests_test_v65_smc_two_leg_tp3_protection": "test_v65_smc_two_leg_tp3_protection.py" | kind=code-symbol | source=tests/test_v65_smc_two_leg_tp3_protection.py:L1 | neighbors=[_engine(), PositionExecutor, Provider, Repo, test_orb_keeps_tp4_cap(), test_smc_at_2r_locks_1r_then_extends_on…] | lang=en
- "base": "Base" | kind=code-symbol | neighbors=[AccountSnapshot, AccountStatsReset, DaemonAuditEvent, InstrumentSelectionPreference, InstrumentSelectionProfilePreference, PositionVisualAudit] | lang=en
- "dashboard_realtime_dashboard_realtimedashboardservice_persist_state_locked": "._persist_state_locked()" | kind=code-symbol | source=dashboard/realtime_dashboard.py:L712 | neighbors=[RealtimeDashboardService, .cycle_end(), .cycle_start(), .mark_live(), .mark_offline(), .monitor_result()] | lang=en
- "database_repository_tradingrepository_json_or_none": "._json_or_none()" | kind=code-symbol | source=database/repository.py:L205 | neighbors=[Convierte dict/list/etc. a JSON seriali…, TradingRepository, .import_mt5_trade_history(), .save_audit_event(), .save_signal(), .save_trade_audit_snapshot()] | lang=en
- "risk_money_management": "money_management.py" | kind=code-symbol | source=strategy/risk/money_management.py:L1 | neighbors=[apply_money_management(), apply_money_management_to_trade(), calculate_drawdown_statistics(), calculate_money_management_statistics(), calculate_risk_amount(), get_final_balance()] | lang=en
- "smc_confirmation_engine_m5confirmationconfig": "M5ConfirmationConfig" | kind=code-symbol | source=strategy/smc/confirmation_engine.py:L19 | neighbors=[PipelineConfig, Filtra una columna de dirección respeta…, Ejecuta la cadena SMC completa. Si symb…, confirmation_engine.py, evaluate_m5_confirmation(), ChartPatternConfig] | lang=en
- "tests_test_demo_daemon_integration_executionrepo": "ExecutionRepo" | kind=code-symbol | source=tests/test_demo_daemon_integration.py:L85 | neighbors=[test_demo_daemon_integration.py, LiveTradingConfig, LiveTradingEngine, TradeReportingService, .get_trade_by_execution_key(), .__init__()] | lang=en
- "tests_test_demo_daemon_integration_executor": "Executor" | kind=code-symbol | source=tests/test_demo_daemon_integration.py:L121 | neighbors=[test_demo_daemon_integration.py, LiveTradingConfig, LiveTradingEngine, TradeReportingService, .assert_demo_account(), .calculate_risk_amount()] | lang=en
- "tests_test_live_paper_trading_engine_fakeanalyzer": "FakeAnalyzer" | kind=code-symbol | source=tests/test_live_paper_trading_engine.py:L24 | neighbors=[test_live_paper_trading_engine.py, LivePaperTradingConfig, LivePaperTradingEngine, PaperTradeExecutor, .analyze_symbol(), .__init__()] | lang=en
- "tests_test_live_paper_trading_engine_fakeprovider": "FakeProvider" | kind=code-symbol | source=tests/test_live_paper_trading_engine.py:L11 | neighbors=[test_live_paper_trading_engine.py, LivePaperTradingConfig, LivePaperTradingEngine, PaperTradeExecutor, .get_current_tick(), .__init__()] | lang=en
- "tests_test_risk_integration_print_result": "print_result()" | kind=code-symbol | source=tests/test_risk_integration.py:L20 | neighbors=[test_risk_integration.py, test_consecutive_losses(), test_daily_loss_limit(), test_drawdown_limit(), test_invalid_buy_stop_loss(), test_invalid_risk_reward()] | lang=en
- "tests_test_risk_integration_print_section": "print_section()" | kind=code-symbol | source=tests/test_risk_integration.py:L13 | neighbors=[test_risk_integration.py, test_consecutive_losses(), test_daily_loss_limit(), test_drawdown_limit(), test_invalid_buy_stop_loss(), test_invalid_risk_reward()] | lang=en
- "tests_test_risk_integration_run_all_tests": "run_all_tests()" | kind=code-symbol | source=tests/test_risk_integration.py:L508 | neighbors=[test_risk_integration.py, test_consecutive_losses(), test_daily_loss_limit(), test_drawdown_limit(), test_invalid_buy_stop_loss(), test_invalid_risk_reward()] | lang=en
- "tests_test_v56_independent_instrument_profiles": "test_v56_independent_instrument_profiles.py" | kind=code-symbol | source=tests/test_v56_independent_instrument_profiles.py:L1 | neighbors=[main.py, realtime_dashboard.py, repository.py, _engine(), test_dashboard_defaults_each_profile_to…, test_dashboard_saves_only_target_profil…] | lang=en

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-003.json

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
