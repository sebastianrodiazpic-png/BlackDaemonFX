# Node Description Batch 33 of 56

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
Write every description in French (fr). Do not switch languages.
No marketing language.
Respond ONLY with a JSON object mapping each node id (as a string) to its
one-sentence description — no prose, no markdown fences.

- "scalping_adaptive_regime_pullback_closed_frame": "_closed_frame()" | kind=code-symbol | source=strategy/scalping/adaptive_regime_pullback.py:L44 | neighbors=[adaptive_regime_pullback.py, ._read()]
- "services_execution_preflight_service_executionpreflightconfig": "ExecutionPreflightConfig" | kind=code-symbol | source=services/execution_preflight_service.py:L13 | neighbors=[execution_preflight_service.py, .__init__()]
- "services_execution_preflight_service_executionpreflightservice_init": ".__init__()" | kind=code-symbol | source=services/execution_preflight_service.py:L21 | neighbors=[ExecutionPreflightService, ExecutionPreflightConfig]
- "services_execution_preflight_service_executionpreflightservice_result": "._result()" | kind=code-symbol | source=services/execution_preflight_service.py:L140 | neighbors=[ExecutionPreflightService, .run()]
- "services_execution_preflight_service_executionpreflightservice_run": ".run()" | kind=code-symbol | source=services/execution_preflight_service.py:L26 | neighbors=[ExecutionPreflightService, ._result()]
- "services_live_demo_smoke_test_service_livedemosmoketestservice_run": ".run()" | kind=code-symbol | source=services/live_demo_smoke_test_service.py:L54 | neighbors=[LiveDemoSmokeTestService, ._tick()]
- "services_live_demo_smoke_test_service_livedemosmoketestservice_tick": "._tick()" | kind=code-symbol | source=services/live_demo_smoke_test_service.py:L158 | neighbors=[LiveDemoSmokeTestService, .run()]
- "smc_chart_patterns_iso": "_iso()" | kind=code-symbol | source=strategy/smc/chart_patterns.py:L52 | neighbors=[chart_patterns.py, _evidence()]
- "smc_chart_patterns_lin_slope": "_lin_slope()" | kind=code-symbol | source=strategy/smc/chart_patterns.py:L59 | neighbors=[chart_patterns.py, detect_chart_pattern_confirmation()]
- "smc_chart_patterns_near": "_near()" | kind=code-symbol | source=strategy/smc/chart_patterns.py:L77 | neighbors=[chart_patterns.py, detect_chart_pattern_confirmation()]
- "smc_chart_patterns_pivots": "_pivots()" | kind=code-symbol | source=strategy/smc/chart_patterns.py:L67 | neighbors=[chart_patterns.py, detect_chart_pattern_confirmation()]
- "smc_choch_bos_detect_choch_bos": "detect_choch_bos()" | kind=code-symbol | source=strategy/smc/choch_bos.py:L4 | neighbors=[choch_bos.py, Detecta Change of Character (CHOCH) y B…]
- "smc_confirmation_engine_grade": "_grade()" | kind=code-symbol | source=strategy/smc/confirmation_engine.py:L107 | neighbors=[confirmation_engine.py, evaluate_m5_confirmation()]
- "smc_confirmation_engine_rsi": "_rsi()" | kind=code-symbol | source=strategy/smc/confirmation_engine.py:L119 | neighbors=[confirmation_engine.py, detect_rsi_divergence()]
- "smc_entry_confirmation_detect_entry_confirmations": "detect_entry_confirmations()" | kind=code-symbol | source=strategy/smc/entry_confirmation.py:L6 | neighbors=[entry_confirmation.py, Detecta confirmaciones de entrada despu…]
- "smc_entry_confirmation_rationale_13": "Detecta confirmaciones de entrada después de un setup SMC.      La lógica busca" | kind=entity | source=strategy/smc/entry_confirmation.py:L13 | neighbors=[M5ConfirmationConfig, detect_entry_confirmations()]
- "smc_h1_doji_extremes_empty": "_empty()" | kind=code-symbol | source=strategy/smc/h1_doji_extremes.py:L28 | neighbors=[h1_doji_extremes.py, detect_h1_extreme_doji()]
- "smc_h1_doji_extremes_safe_float": "_safe_float()" | kind=code-symbol | source=strategy/smc/h1_doji_extremes.py:L20 | neighbors=[h1_doji_extremes.py, detect_h1_extreme_doji()]
- "smc_harmonic_patterns_alternating_swings": "_alternating_swings()" | kind=code-symbol | source=strategy/smc/harmonic_patterns.py:L44 | neighbors=[harmonic_patterns.py, detect_harmonic_confirmation()]
- "smc_harmonic_patterns_ratio": "_ratio()" | kind=code-symbol | source=strategy/smc/harmonic_patterns.py:L26 | neighbors=[harmonic_patterns.py, _evaluate_pattern()]
- "smc_liquidity_detect_liquidity_levels": "detect_liquidity_levels()" | kind=code-symbol | source=strategy/smc/liquidity.py:L4 | neighbors=[liquidity.py, Detecta zonas potenciales de liquidez.…]
- "smc_liquidity_sweeps_detect_liquidity_sweeps": "detect_liquidity_sweeps()" | kind=code-symbol | source=strategy/smc/liquidity_sweeps.py:L4 | neighbors=[liquidity_sweeps.py, Detecta barridos de liquidez.      Be…]
- "smc_market_structure": "market_structure.py" | kind=code-symbol | source=strategy/smc/market_structure.py:L1 | neighbors=[classify_market_structure(), get_current_trend()]
- "smc_market_structure_classify_market_structure": "classify_market_structure()" | kind=code-symbol | source=strategy/smc/market_structure.py:L4 | neighbors=[market_structure.py, Clasifica los Swing High y Swing Low de…]
- "smc_market_structure_get_current_trend": "get_current_trend()" | kind=code-symbol | source=strategy/smc/market_structure.py:L66 | neighbors=[market_structure.py, Intenta determinar la tendencia actual …]
- "smc_ob_quality_calculate_ob_score": "calculate_ob_score()" | kind=code-symbol | source=strategy/smc/ob_quality.py:L107 | neighbors=[ob_quality.py, evaluate_order_block()]
- "smc_ob_quality_get_ob_grade": "get_ob_grade()" | kind=code-symbol | source=strategy/smc/ob_quality.py:L151 | neighbors=[ob_quality.py, evaluate_order_block()]
- "smc_order_blocks_detect_order_blocks": "detect_order_blocks()" | kind=code-symbol | source=strategy/smc/order_blocks.py:L4 | neighbors=[order_blocks.py, Detecta Order Blocks y conserva el even…]
- "smc_premium_discount_calculate_premium_discount": "calculate_premium_discount()" | kind=code-symbol | source=strategy/smc/premium_discount.py:L4 | neighbors=[premium_discount.py, Calcula las zonas Premium, Discount y E…]
- "smc_premium_discount_is_bearish_ob_in_premium": "is_bearish_ob_in_premium()" | kind=code-symbol | source=strategy/smc/premium_discount.py:L91 | neighbors=[premium_discount.py, Filtra Bearish Order Blocks ubicados en…]
- "smc_premium_discount_is_bullish_ob_in_discount": "is_bullish_ob_in_discount()" | kind=code-symbol | source=strategy/smc/premium_discount.py:L73 | neighbors=[premium_discount.py, Filtra Bullish Order Blocks ubicados en…]
- "smc_risk_reward_calculate_risk_reward": "calculate_risk_reward()" | kind=code-symbol | source=strategy/smc/risk_reward.py:L4 | neighbors=[risk_reward.py, Calcula Stop Loss, Take Profit y Risk/R…]
- "smc_setup_detector_detect_setups": "detect_setups()" | kind=code-symbol | source=strategy/smc/setup_detector.py:L4 | neighbors=[setup_detector.py, Detecta setups SMC utilizando una secue…]
- "smc_swings_detect_swings": "detect_swings()" | kind=code-symbol | source=strategy/smc/swings.py:L4 | neighbors=[swings.py, Detecta Swing High y Swing Low.      …]
- "smc_trade_simulator": "trade_simulator.py" | kind=code-symbol | source=strategy/smc/trade_simulator.py:L1 | neighbors=[simulate_trade(), simulate_trades()]
- "storage_account_page_syntax_test_go": "go()" | kind=code-symbol | source=storage/account_page_syntax_test.js:L56 | neighbors=[account_page_syntax_test.js, render()]
- "storage_account_page_syntax_test_money": "money()" | kind=code-symbol | source=storage/account_page_syntax_test.js:L1 | neighbors=[account_page_syntax_test.js, render()]
- "tests_test_backtest_format_number": "format_number()" | kind=code-symbol | source=tests/test_backtest.py:L34 | neighbors=[test_backtest.py, print_trades()]
- "tests_test_backtest_load_data": "load_data()" | kind=code-symbol | source=tests/test_backtest.py:L358 | neighbors=[test_backtest.py, run_backtest()]
- "tests_test_backtest_prepare_data": "prepare_data()" | kind=code-symbol | source=tests/test_backtest.py:L391 | neighbors=[test_backtest.py, run_backtest()]

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-032.json

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
