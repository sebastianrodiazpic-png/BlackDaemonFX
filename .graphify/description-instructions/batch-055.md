# Node Description Batch 56 of 56

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
Write every description in English (en). Do not switch languages.
No marketing language.
Respond ONLY with a JSON object mapping each node id (as a string) to its
one-sentence description — no prose, no markdown fences.

- "tests_test_v99_persistence_shards_adaptive_regime_test_adaptive_adx_is_bounded_and_keeps_structural_floor": "test_adaptive_adx_is_bounded_and_keeps_structural_floor()" | kind=code-symbol | source=tests/test_v99_persistence_shards_adaptive_regime.py:L97 | neighbors=[test_v99_persistence_shards_adaptive_re…]
- "tests_test_v99_persistence_shards_adaptive_regime_test_broker_position_ticket_promotes_recovered_row_without_duplicate": "test_broker_position_ticket_promotes_recovered_row_without_duplicate()" | kind=code-symbol | source=tests/test_v99_persistence_shards_adaptive_regime.py:L46 | neighbors=[test_v99_persistence_shards_adaptive_re…]
- "tests_test_v99_persistence_shards_adaptive_regime_test_dashboard_explains_regime_block_with_actual_adx_values": "test_dashboard_explains_regime_block_with_actual_adx_values()" | kind=code-symbol | source=tests/test_v99_persistence_shards_adaptive_regime.py:L118 | neighbors=[test_v99_persistence_shards_adaptive_re…]
- "tests_test_v99_persistence_shards_adaptive_regime_test_dashboard_translates_each_missing_arps_confirmation": "test_dashboard_translates_each_missing_arps_confirmation()" | kind=code-symbol | source=tests/test_v99_persistence_shards_adaptive_regime.py:L131 | neighbors=[test_v99_persistence_shards_adaptive_re…]
- "tests_test_v99_persistence_shards_adaptive_regime_test_recovery_skips_while_fill_persistence_is_in_progress": "test_recovery_skips_while_fill_persistence_is_in_progress()" | kind=code-symbol | source=tests/test_v99_persistence_shards_adaptive_regime.py:L21 | neighbors=[test_v99_persistence_shards_adaptive_re…]
- "tests_test_v99_persistence_shards_adaptive_regime_test_volatility_shards_are_disjoint_complete_and_have_unique_identity": "test_volatility_shards_are_disjoint_complete_and_have_unique_identity()" | kind=code-symbol | source=tests/test_v99_persistence_shards_adaptive_regime.py:L80 | neighbors=[test_v99_persistence_shards_adaptive_re…]
- "trade_lifecycle_manager_tradelifecycle_to_dict": ".to_dict()" | kind=code-symbol | source=trade_lifecycle_manager.py:L104 | neighbors=[TradeLifecycle]
- "trade_lifecycle_manager_tradelifecyclemanager_clear_history": ".clear_history()" | kind=code-symbol | source=trade_lifecycle_manager.py:L896 | neighbors=[TradeLifecycleManager]
- "trade_lifecycle_manager_tradelifecyclemanager_get_active_lifecycle": ".get_active_lifecycle()" | kind=code-symbol | source=trade_lifecycle_manager.py:L574 | neighbors=[TradeLifecycleManager]
- "trade_lifecycle_manager_tradelifecyclemanager_get_active_lifecycles": ".get_active_lifecycles()" | kind=code-symbol | source=trade_lifecycle_manager.py:L577 | neighbors=[TradeLifecycleManager]
- "trade_lifecycle_manager_tradelifecyclemanager_get_history": ".get_history()" | kind=code-symbol | source=trade_lifecycle_manager.py:L866 | neighbors=[TradeLifecycleManager]
- "trade_lifecycle_manager_tradelifecyclemanager_init": ".__init__()" | kind=code-symbol | source=trade_lifecycle_manager.py:L157 | neighbors=[TradeLifecycleManager]
- "trade_outcome_policy_rationale_31": "Devuelve WIN / LOSS / BREAK_EVEN / OPEN / None.      Prioridad:     1. OPEN nunc" | kind=entity | source=trade_outcome_policy.py:L31 | neighbors=[decisive_outcome()]
- "app_init": "__init__.py" | kind=code-symbol | source=app/__init__.py:L1
- "backtest_init": "__init__.py" | kind=code-symbol | source=strategy/backtest/__init__.py:L1
- "backtesting_init": "__init__.py" | kind=code-symbol | source=backtesting/__init__.py:L1
- "brokers_init": "__init__.py" | kind=code-symbol | source=brokers/__init__.py:L1
- "config_init": "__init__.py" | kind=code-symbol | source=config/__init__.py:L1
- "config_settings": "settings.py" | kind=code-symbol | source=config/settings.py:L1
- "dashboard_init": "__init__.py" | kind=code-symbol | source=dashboard/__init__.py:L1
- "data_instruments": "instruments.py" | kind=code-symbol | source=data/instruments.py:L1
- "database_init": "__init__.py" | kind=code-symbol | source=database/__init__.py:L1
- "orb_init": "__init__.py" | kind=code-symbol | source=strategy/orb/__init__.py:L1
- "risk_init": "__init__.py" | kind=code-symbol | source=strategy/risk/__init__.py:L1
- "services_init": "__init__.py" | kind=code-symbol | source=services/__init__.py:L1
- "smc_init": "__init__.py" | kind=code-symbol | source=strategy/smc/__init__.py:L1
- "strategy_init": "__init__.py" | kind=code-symbol | source=strategy/__init__.py:L1

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-055.json

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
