# Node Description Batch 52 of 56

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

- "tests_test_v63_account_db_continuity_test_account_page_displays_sqlite_path": "test_account_page_displays_sqlite_path()" | kind=code-symbol | source=tests/test_v63_account_db_continuity.py:L69 | neighbors=[test_v63_account_db_continuity.py]
- "tests_test_v63_account_db_continuity_test_account_payload_reports_database_diagnostics": "test_account_payload_reports_database_diagnostics()" | kind=code-symbol | source=tests/test_v63_account_db_continuity.py:L61 | neighbors=[test_v63_account_db_continuity.py]
- "tests_test_v63_account_db_continuity_test_repository_exposes_exact_database_path": "test_repository_exposes_exact_database_path()" | kind=code-symbol | source=tests/test_v63_account_db_continuity.py:L53 | neighbors=[test_v63_account_db_continuity.py]
- "tests_test_v64_account_ui_fix_test_account_page_fetch_checks_http_status": "test_account_page_fetch_checks_http_status()" | kind=code-symbol | source=tests/test_v64_account_ui_fix.py:L28 | neighbors=[test_v64_account_ui_fix.py]
- "tests_test_v64_account_ui_fix_test_account_page_javascript_is_valid": "test_account_page_javascript_is_valid()" | kind=code-symbol | source=tests/test_v64_account_ui_fix.py:L9 | neighbors=[test_v64_account_ui_fix.py]
- "tests_test_v64_account_ui_fix_test_account_page_keeps_persistent_confirmation_column": "test_account_page_keeps_persistent_confirmation_column()" | kind=code-symbol | source=tests/test_v64_account_ui_fix.py:L35 | neighbors=[test_v64_account_ui_fix.py]
- "tests_test_v64_account_ui_fix_test_account_payload_contains_db_diagnostics": "test_account_payload_contains_db_diagnostics()" | kind=code-symbol | source=tests/test_v64_account_ui_fix.py:L20 | neighbors=[test_v64_account_ui_fix.py]
- "tests_test_v65_smc_two_leg_tp3_protection_positionexecutor_get_position": ".get_position()" | kind=code-symbol | source=tests/test_v65_smc_two_leg_tp3_protection.py:L28 | neighbors=[PositionExecutor]
- "tests_test_v65_smc_two_leg_tp3_protection_positionexecutor_get_symbol_constraints": ".get_symbol_constraints()" | kind=code-symbol | source=tests/test_v65_smc_two_leg_tp3_protection.py:L30 | neighbors=[PositionExecutor]
- "tests_test_v65_smc_two_leg_tp3_protection_positionexecutor_init": ".__init__()" | kind=code-symbol | source=tests/test_v65_smc_two_leg_tp3_protection.py:L26 | neighbors=[PositionExecutor]
- "tests_test_v65_smc_two_leg_tp3_protection_provider_get_candles": ".get_candles()" | kind=code-symbol | source=tests/test_v65_smc_two_leg_tp3_protection.py:L17 | neighbors=[Provider]
- "tests_test_v65_smc_two_leg_tp3_protection_repo_init": ".__init__()" | kind=code-symbol | source=tests/test_v65_smc_two_leg_tp3_protection.py:L10 | neighbors=[Repo]
- "tests_test_v65_smc_two_leg_tp3_protection_repo_update_trade": ".update_trade()" | kind=code-symbol | source=tests/test_v65_smc_two_leg_tp3_protection.py:L12 | neighbors=[Repo]
- "tests_test_v65_smc_two_leg_tp3_protection_test_orb_keeps_tp4_cap": "test_orb_keeps_tp4_cap()" | kind=code-symbol | source=tests/test_v65_smc_two_leg_tp3_protection.py:L206 | neighbors=[test_v65_smc_two_leg_tp3_protection.py]
- "tests_test_v65_smc_two_leg_tp3_protection_test_smc_defaults_are_half_half_tp1_tp2_and_tp3_max": "test_smc_defaults_are_half_half_tp1_tp2_and_tp3_max()" | kind=code-symbol | source=tests/test_v65_smc_two_leg_tp3_protection.py:L86 | neighbors=[test_v65_smc_two_leg_tp3_protection.py]
- "tests_test_v65_smc_two_leg_tp3_protection_tradeexecutor_close_position": ".close_position()" | kind=code-symbol | source=tests/test_v65_smc_two_leg_tp3_protection.py:L44 | neighbors=[TradeExecutor]
- "tests_test_v65_smc_two_leg_tp3_protection_tradeexecutor_init": ".__init__()" | kind=code-symbol | source=tests/test_v65_smc_two_leg_tp3_protection.py:L35 | neighbors=[TradeExecutor]
- "tests_test_v65_smc_two_leg_tp3_protection_tradeexecutor_move_stop_loss": ".move_stop_loss()" | kind=code-symbol | source=tests/test_v65_smc_two_leg_tp3_protection.py:L39 | neighbors=[TradeExecutor]
- "tests_test_v66_smc_tp4_be_plus2_broker_get_symbol_constraints": ".get_symbol_constraints()" | kind=code-symbol | source=tests/test_v66_smc_tp4_be_plus2.py:L48 | neighbors=[Broker]
- "tests_test_v66_smc_tp4_be_plus2_broker_init": ".__init__()" | kind=code-symbol | source=tests/test_v66_smc_tp4_be_plus2.py:L44 | neighbors=[Broker]
- "tests_test_v66_smc_tp4_be_plus2_provider_get_candles": ".get_candles()" | kind=code-symbol | source=tests/test_v66_smc_tp4_be_plus2.py:L35 | neighbors=[Provider]
- "tests_test_v66_smc_tp4_be_plus2_repo_get_trade_by_execution_key": ".get_trade_by_execution_key()" | kind=code-symbol | source=tests/test_v66_smc_tp4_be_plus2.py:L24 | neighbors=[Repo]
- "tests_test_v66_smc_tp4_be_plus2_repo_init": ".__init__()" | kind=code-symbol | source=tests/test_v66_smc_tp4_be_plus2.py:L9 | neighbors=[Repo]
- "tests_test_v66_smc_tp4_be_plus2_repo_open_trades": ".open_trades()" | kind=code-symbol | source=tests/test_v66_smc_tp4_be_plus2.py:L23 | neighbors=[Repo]
- "tests_test_v66_smc_tp4_be_plus2_repo_update_trade": ".update_trade()" | kind=code-symbol | source=tests/test_v66_smc_tp4_be_plus2.py:L26 | neighbors=[Repo]
- "tests_test_v66_smc_tp4_be_plus2_test_smc_configuration_is_half_half_and_tp4_cap": "test_smc_configuration_is_half_half_and_tp4_cap()" | kind=code-symbol | source=tests/test_v66_smc_tp4_be_plus2.py:L95 | neighbors=[test_v66_smc_tp4_be_plus2.py]
- "tests_test_v66_smc_tp4_be_plus2_tradeexecutor_close_position": ".close_position()" | kind=code-symbol | source=tests/test_v66_smc_tp4_be_plus2.py:L62 | neighbors=[TradeExecutor]
- "tests_test_v66_smc_tp4_be_plus2_tradeexecutor_init": ".__init__()" | kind=code-symbol | source=tests/test_v66_smc_tp4_be_plus2.py:L55 | neighbors=[TradeExecutor]
- "tests_test_v66_smc_tp4_be_plus2_tradeexecutor_move_stop_loss": ".move_stop_loss()" | kind=code-symbol | source=tests/test_v66_smc_tp4_be_plus2.py:L57 | neighbors=[TradeExecutor]
- "tests_test_v67_live_entry_vs_now_analyzer_analyze_symbol": ".analyze_symbol()" | kind=code-symbol | source=tests/test_v67_live_entry_vs_now.py:L83 | neighbors=[Analyzer]
- "tests_test_v67_live_entry_vs_now_repo_init": ".__init__()" | kind=code-symbol | source=tests/test_v67_live_entry_vs_now.py:L56 | neighbors=[Repo]
- "tests_test_v67_live_entry_vs_now_repo_open_trades": ".open_trades()" | kind=code-symbol | source=tests/test_v67_live_entry_vs_now.py:L68 | neighbors=[Repo]
- "tests_test_v67_live_entry_vs_now_repo_save_audit_event": ".save_audit_event()" | kind=code-symbol | source=tests/test_v67_live_entry_vs_now.py:L78 | neighbors=[Repo]
- "tests_test_v67_live_entry_vs_now_repo_trade_visual_audits": ".trade_visual_audits()" | kind=code-symbol | source=tests/test_v67_live_entry_vs_now.py:L70 | neighbors=[Repo]
- "tests_test_v67_live_entry_vs_now_repo_upsert_trade_visual_audit": ".upsert_trade_visual_audit()" | kind=code-symbol | source=tests/test_v67_live_entry_vs_now.py:L76 | neighbors=[Repo]
- "tests_test_v67_live_entry_vs_now_test_current_strategy_view_extracts_live_signal_confirmations": "test_current_strategy_view_extracts_live_signal_confirmations()" | kind=code-symbol | source=tests/test_v67_live_entry_vs_now.py:L26 | neighbors=[test_v67_live_entry_vs_now.py]
- "tests_test_v67_live_entry_vs_now_test_current_strategy_view_normalizes_waiting_state": "test_current_strategy_view_normalizes_waiting_state()" | kind=code-symbol | source=tests/test_v67_live_entry_vs_now.py:L7 | neighbors=[test_v67_live_entry_vs_now.py]
- "tests_test_v67_live_entry_vs_now_test_dashboard_prioritizes_persisted_current_strategy_view": "test_dashboard_prioritizes_persisted_current_strategy_view()" | kind=code-symbol | source=tests/test_v67_live_entry_vs_now.py:L121 | neighbors=[test_v67_live_entry_vs_now.py]
- "tests_test_v67_live_entry_vs_now_test_live_refresh_is_independent_from_30_second_chart_persistence": "test_live_refresh_is_independent_from_30_second_chart_persistence()" | kind=code-symbol | source=tests/test_v67_live_entry_vs_now.py:L129 | neighbors=[test_v67_live_entry_vs_now.py]
- "tests_test_v68_persistent_entry_vs_now_dataset_test_account_page_has_entry_vs_now_timeline_ui": "test_account_page_has_entry_vs_now_timeline_ui()" | kind=code-symbol | source=tests/test_v68_persistent_entry_vs_now_dataset.py:L128 | neighbors=[test_v68_persistent_entry_vs_now_datase…]

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-051.json

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
