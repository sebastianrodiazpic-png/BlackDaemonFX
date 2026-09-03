# Node Description Batch 53 of 56

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

- "tests_test_v69_forex_event_scheduler_candleprovider_get_candles": ".get_candles()" | kind=code-symbol | source=tests/test_v69_forex_event_scheduler.py:L38 | neighbors=[CandleProvider]
- "tests_test_v69_forex_event_scheduler_candleprovider_init": ".__init__()" | kind=code-symbol | source=tests/test_v69_forex_event_scheduler.py:L36 | neighbors=[CandleProvider]
- "tests_test_v69_forex_event_scheduler_exposurerepo_init": ".__init__()" | kind=code-symbol | source=tests/test_v69_forex_event_scheduler.py:L89 | neighbors=[ExposureRepo]
- "tests_test_v69_forex_event_scheduler_exposurerepo_open_trades": ".open_trades()" | kind=code-symbol | source=tests/test_v69_forex_event_scheduler.py:L91 | neighbors=[ExposureRepo]
- "tests_test_v69_forex_event_scheduler_test_forex_launcher_uses_split_scheduler": "test_forex_launcher_uses_split_scheduler()" | kind=code-symbol | source=tests/test_v69_forex_event_scheduler.py:L153 | neighbors=[test_v69_forex_event_scheduler.py]
- "tests_test_v69_forex_event_scheduler_test_forex_selection_profile_shared_by_all_shards": "test_forex_selection_profile_shared_by_all_shards()" | kind=code-symbol | source=tests/test_v69_forex_event_scheduler.py:L161 | neighbors=[test_v69_forex_event_scheduler.py]
- "tests_test_v69_forex_event_scheduler_test_forex_split_profiles_are_four_unique_workers": "test_forex_split_profiles_are_four_unique_workers()" | kind=code-symbol | source=tests/test_v69_forex_event_scheduler.py:L9 | neighbors=[test_v69_forex_event_scheduler.py]
- "tests_test_v69_forex_event_scheduler_test_stable_symbol_shards_are_disjoint_and_complete": "test_stable_symbol_shards_are_disjoint_and_complete()" | kind=code-symbol | source=tests/test_v69_forex_event_scheduler.py:L24 | neighbors=[test_v69_forex_event_scheduler.py]
- "tests_test_v70_recent_analysis_all_workers_test_dashboard_hides_superseded_but_keeps_db_history": "test_dashboard_hides_superseded_but_keeps_db_history()" | kind=code-symbol | source=tests/test_v70_recent_analysis_all_workers.py:L38 | neighbors=[test_v70_recent_analysis_all_workers.py]
- "tests_test_v70_recent_analysis_all_workers_test_recent_analysis_uses_sqlalchemy_as_authoritative_source": "test_recent_analysis_uses_sqlalchemy_as_authoritative_source()" | kind=code-symbol | source=tests/test_v70_recent_analysis_all_workers.py:L47 | neighbors=[test_v70_recent_analysis_all_workers.py]
- "tests_test_v70_recent_analysis_all_workers_test_recent_symbol_process_results_keeps_multiple_profiles": "test_recent_symbol_process_results_keeps_multiple_profiles()" | kind=code-symbol | source=tests/test_v70_recent_analysis_all_workers.py:L8 | neighbors=[test_v70_recent_analysis_all_workers.py]
- "tests_test_v71_balanced_recent_analysis_test_dashboard_calls_balanced_repository": "test_dashboard_calls_balanced_repository()" | kind=code-symbol | source=tests/test_v71_balanced_recent_analysis.py:L62 | neighbors=[test_v71_balanced_recent_analysis.py]
- "tests_test_v71_balanced_recent_analysis_test_profile_is_inferred_from_magic_when_payload_profile_missing": "test_profile_is_inferred_from_magic_when_payload_profile_missing()" | kind=code-symbol | source=tests/test_v71_balanced_recent_analysis.py:L38 | neighbors=[test_v71_balanced_recent_analysis.py]
- "tests_test_v71_balanced_recent_analysis_test_profile_is_inferred_from_symbol_for_old_synthetic_event": "test_profile_is_inferred_from_symbol_for_old_synthetic_event()" | kind=code-symbol | source=tests/test_v71_balanced_recent_analysis.py:L47 | neighbors=[test_v71_balanced_recent_analysis.py]
- "tests_test_v72_chart_conflict_explained_mixed_structure": "_mixed_structure()" | kind=code-symbol | source=tests/test_v72_chart_conflict_explained.py:L12 | neighbors=[test_v72_chart_conflict_explained.py]
- "tests_test_v72_chart_conflict_explained_test_account_keeps_conflict_explanation": "test_account_keeps_conflict_explanation()" | kind=code-symbol | source=tests/test_v72_chart_conflict_explained.py:L88 | neighbors=[test_v72_chart_conflict_explained.py]
- "tests_test_v72_chart_conflict_explained_test_conflict_explanation_compares_supporting_and_opposing_patterns": "test_conflict_explanation_compares_supporting_and_opposing_patterns()" | kind=code-symbol | source=tests/test_v72_chart_conflict_explained.py:L27 | neighbors=[test_v72_chart_conflict_explained.py]
- "tests_test_v72_chart_conflict_explained_test_dashboard_explains_both_sides_of_conflict": "test_dashboard_explains_both_sides_of_conflict()" | kind=code-symbol | source=tests/test_v72_chart_conflict_explained.py:L79 | neighbors=[test_v72_chart_conflict_explained.py]
- "tests_test_v72_chart_conflict_explained_test_live_current_view_preserves_conflict_explanation": "test_live_current_view_preserves_conflict_explanation()" | kind=code-symbol | source=tests/test_v72_chart_conflict_explained.py:L47 | neighbors=[test_v72_chart_conflict_explained.py]
- "tests_test_v72_chart_conflict_explained_test_stronger_opposing_pattern_is_identified": "test_stronger_opposing_pattern_is_identified()" | kind=code-symbol | source=tests/test_v72_chart_conflict_explained.py:L37 | neighbors=[test_v72_chart_conflict_explained.py]
- "tests_test_v73_forex_progressive_runner_positionexecutor_get_position": ".get_position()" | kind=code-symbol | source=tests/test_v73_forex_progressive_runner.py:L29 | neighbors=[PositionExecutor]
- "tests_test_v73_forex_progressive_runner_positionexecutor_get_symbol_constraints": ".get_symbol_constraints()" | kind=code-symbol | source=tests/test_v73_forex_progressive_runner.py:L31 | neighbors=[PositionExecutor]
- "tests_test_v73_forex_progressive_runner_positionexecutor_init": ".__init__()" | kind=code-symbol | source=tests/test_v73_forex_progressive_runner.py:L27 | neighbors=[PositionExecutor]
- "tests_test_v73_forex_progressive_runner_provider_get_candles": ".get_candles()" | kind=code-symbol | source=tests/test_v73_forex_progressive_runner.py:L16 | neighbors=[Provider]
- "tests_test_v73_forex_progressive_runner_repo_init": ".__init__()" | kind=code-symbol | source=tests/test_v73_forex_progressive_runner.py:L9 | neighbors=[Repo]
- "tests_test_v73_forex_progressive_runner_repo_update_trade": ".update_trade()" | kind=code-symbol | source=tests/test_v73_forex_progressive_runner.py:L11 | neighbors=[Repo]
- "tests_test_v73_forex_progressive_runner_test_forex_runner_config_starts_at_tp2_and_has_tp4_fail_safe": "test_forex_runner_config_starts_at_tp2_and_has_tp4_fail_safe()" | kind=code-symbol | source=tests/test_v73_forex_progressive_runner.py:L90 | neighbors=[test_v73_forex_progressive_runner.py]
- "tests_test_v73_forex_progressive_runner_test_source_builds_forex_runner_with_logical_tp2_and_broker_tp4": "test_source_builds_forex_runner_with_logical_tp2_and_broker_tp4()" | kind=code-symbol | source=tests/test_v73_forex_progressive_runner.py:L190 | neighbors=[test_v73_forex_progressive_runner.py]
- "tests_test_v73_forex_progressive_runner_tradeexecutor_close_position": ".close_position()" | kind=code-symbol | source=tests/test_v73_forex_progressive_runner.py:L45 | neighbors=[TradeExecutor]
- "tests_test_v73_forex_progressive_runner_tradeexecutor_init": ".__init__()" | kind=code-symbol | source=tests/test_v73_forex_progressive_runner.py:L36 | neighbors=[TradeExecutor]
- "tests_test_v73_forex_progressive_runner_tradeexecutor_move_stop_loss": ".move_stop_loss()" | kind=code-symbol | source=tests/test_v73_forex_progressive_runner.py:L40 | neighbors=[TradeExecutor]
- "tests_test_v74_fast_navigation_repo_init": ".__init__()" | kind=code-symbol | source=tests/test_v74_fast_navigation.py:L7 | neighbors=[Repo]
- "tests_test_v74_fast_navigation_repo_latest_instrument_selection": ".latest_instrument_selection()" | kind=code-symbol | source=tests/test_v74_fast_navigation.py:L17 | neighbors=[Repo]
- "tests_test_v74_fast_navigation_repo_latest_instrument_selection_profiles": ".latest_instrument_selection_profiles()" | kind=code-symbol | source=tests/test_v74_fast_navigation.py:L10 | neighbors=[Repo]
- "tests_test_v74_fast_navigation_repo_latest_worker_process_results": ".latest_worker_process_results()" | kind=code-symbol | source=tests/test_v74_fast_navigation.py:L25 | neighbors=[Repo]
- "tests_test_v74_fast_navigation_repo_open_trades": ".open_trades()" | kind=code-symbol | source=tests/test_v74_fast_navigation.py:L19 | neighbors=[Repo]
- "tests_test_v74_fast_navigation_repo_position_visual_audits": ".position_visual_audits()" | kind=code-symbol | source=tests/test_v74_fast_navigation.py:L23 | neighbors=[Repo]
- "tests_test_v74_fast_navigation_repo_recent_symbol_process_results": ".recent_symbol_process_results()" | kind=code-symbol | source=tests/test_v74_fast_navigation.py:L29 | neighbors=[Repo]
- "tests_test_v74_fast_navigation_repo_trade_visual_audits": ".trade_visual_audits()" | kind=code-symbol | source=tests/test_v74_fast_navigation.py:L21 | neighbors=[Repo]
- "tests_test_v74_fast_navigation_repo_worker_runtime_states": ".worker_runtime_states()" | kind=code-symbol | source=tests/test_v74_fast_navigation.py:L27 | neighbors=[Repo]

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-052.json

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
