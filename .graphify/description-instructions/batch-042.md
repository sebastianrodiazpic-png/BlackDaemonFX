# Node Description Batch 43 of 56

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

- "risk_risk_manager_rationale_78": "Valida que un valor sea numérico, finito y mayor\r     o igual a cero." | kind=entity | source=strategy/risk/risk_manager.py:L78 | neighbors=[validate_non_negative_number()] | lang=en
- "risk_risk_manager_rationale_795": "Calcula el drawdown actual y máximo.\r \r     Si existe balance_after se utiliza d" | kind=entity | source=strategy/risk/risk_manager.py:L795 | neighbors=[calculate_current_drawdown()] | lang=es
- "risk_risk_manager_rationale_953": "Calcula el riesgo total de las posiciones\r     actualmente abiertas.\r \r     Cada" | kind=entity | source=strategy/risk/risk_manager.py:L953 | neighbors=[calculate_open_positions_risk()] | lang=es
- "scalping_adaptive_regime_pullback_rationale_104": "Umbral por instrumento, acotado por piso y techo configurados." | kind=entity | source=strategy/scalping/adaptive_regime_pullback.py:L104 | neighbors=[._effective_adx_threshold()] | lang=es
- "scalping_adaptive_regime_pullback_rationale_85": "Scalper 24/7 para sintéticos, aislado de la estrategia SMC existente." | kind=entity | source=strategy/scalping/adaptive_regime_pullback.py:L85 | neighbors=[AdaptiveRegimePullbackStrategy] | lang=en
- "scalping_init": "__init__.py" | kind=code-symbol | source=strategy/scalping/__init__.py:L1 | neighbors=[Estrategias de scalping independientes …] | lang=en
- "services_execution_preflight_service_rationale_19": "Valida que el entorno MT5 esté listo antes de permitir ejecución DEMO." | kind=entity | source=services/execution_preflight_service.py:L19 | neighbors=[ExecutionPreflightService] | lang=en
- "services_live_demo_smoke_test_service_livedemosmoketestservice_init": ".__init__()" | kind=code-symbol | source=services/live_demo_smoke_test_service.py:L31 | neighbors=[LiveDemoSmokeTestService] | lang=en
- "smc_chart_patterns_rationale_1": "Chart-pattern confluence detector for DaemonBlackFx SMC.  Patterns are deliberat" | kind=entity | source=strategy/smc/chart_patterns.py:L1 | neighbors=[chart_patterns.py] | lang=en
- "smc_chart_patterns_rationale_124": "Devuelve nivel, razón y delta sin alterar la decisión de trading." | kind=entity | source=strategy/smc/chart_patterns.py:L124 | neighbors=[_explain_chart_pattern_conflict()] | lang=es
- "smc_chart_patterns_rationale_83": "Tolera pivotes equivalentes en unidades comparables entre contratos.      ``pric" | kind=entity | source=strategy/smc/chart_patterns.py:L83 | neighbors=[_effective_price_tolerance()] | lang=en
- "smc_choch_bos": "choch_bos.py" | kind=code-symbol | source=strategy/smc/choch_bos.py:L1 | neighbors=[detect_choch_bos()] | lang=en
- "smc_choch_bos_rationale_5": "Detecta Change of Character (CHOCH) y Break of Structure (BOS).\r \r     CHOCH alc" | kind=entity | source=strategy/smc/choch_bos.py:L5 | neighbors=[detect_choch_bos()] | lang=en
- "smc_entry_confirmation": "entry_confirmation.py" | kind=code-symbol | source=strategy/smc/entry_confirmation.py:L1 | neighbors=[detect_entry_confirmations()] | lang=en
- "smc_h1_doji_extremes_rationale_51": "Detecta un Doji H1 reciente en un extremo compatible con la operación.      BUY" | kind=entity | source=strategy/smc/h1_doji_extremes.py:L51 | neighbors=[detect_h1_extreme_doji()] | lang=en
- "smc_harmonic_patterns_near": "_near()" | kind=code-symbol | source=strategy/smc/harmonic_patterns.py:L32 | neighbors=[harmonic_patterns.py] | lang=en
- "smc_harmonic_patterns_rationale_1": "Detección conservadora de patrones armónicos sobre swings confirmados.  No utili" | kind=entity | source=strategy/smc/harmonic_patterns.py:L1 | neighbors=[harmonic_patterns.py] | lang=nl
- "smc_harmonic_patterns_rationale_145": "Devuelve el mejor patrón armónico confirmado en los swings disponibles." | kind=entity | source=strategy/smc/harmonic_patterns.py:L145 | neighbors=[detect_harmonic_confirmation()] | lang=es
- "smc_harmonic_patterns_score": "_score()" | kind=code-symbol | source=strategy/smc/harmonic_patterns.py:L36 | neighbors=[harmonic_patterns.py] | lang=en
- "smc_liquidity": "liquidity.py" | kind=code-symbol | source=strategy/smc/liquidity.py:L1 | neighbors=[detect_liquidity_levels()] | lang=en
- "smc_liquidity_rationale_5": "Detecta zonas potenciales de liquidez.\r \r     Buy-side liquidity:\r         Swing" | kind=entity | source=strategy/smc/liquidity.py:L5 | neighbors=[detect_liquidity_levels()] | lang=nl
- "smc_liquidity_sweeps": "liquidity_sweeps.py" | kind=code-symbol | source=strategy/smc/liquidity_sweeps.py:L1 | neighbors=[detect_liquidity_sweeps()] | lang=en
- "smc_liquidity_sweeps_rationale_5": "Detecta barridos de liquidez.\r \r     Bearish Sweep:\r         - El precio supera" | kind=entity | source=strategy/smc/liquidity_sweeps.py:L5 | neighbors=[detect_liquidity_sweeps()] | lang=en
- "smc_market_structure_rationale_5": "Clasifica los Swing High y Swing Low detectados.\r \r     Swing High:\r         HH" | kind=entity | source=strategy/smc/market_structure.py:L5 | neighbors=[classify_market_structure()] | lang=es
- "smc_market_structure_rationale_67": "Intenta determinar la tendencia actual según\r     los últimos puntos de estructu" | kind=entity | source=strategy/smc/market_structure.py:L67 | neighbors=[get_current_trend()] | lang=es
- "smc_micro_confirmation": "micro_confirmation.py" | kind=code-symbol | source=strategy/smc/micro_confirmation.py:L1 | neighbors=[detect_micro_confirmation()] | lang=en
- "smc_micro_confirmation_detect_micro_confirmation": "detect_micro_confirmation()" | kind=code-symbol | source=strategy/smc/micro_confirmation.py:L4 | neighbors=[micro_confirmation.py] | lang=en
- "smc_ob_quality_calculate_average_range": "calculate_average_range()" | kind=code-symbol | source=strategy/smc/ob_quality.py:L79 | neighbors=[ob_quality.py] | lang=en
- "smc_ob_quality_calculate_ob_displacement": "calculate_ob_displacement()" | kind=code-symbol | source=strategy/smc/ob_quality.py:L4 | neighbors=[ob_quality.py] | lang=en
- "smc_order_blocks": "order_blocks.py" | kind=code-symbol | source=strategy/smc/order_blocks.py:L1 | neighbors=[detect_order_blocks()] | lang=en
- "smc_order_blocks_rationale_5": "Detecta Order Blocks y conserva el evento estructural que los valida.      Un Bu" | kind=entity | source=strategy/smc/order_blocks.py:L5 | neighbors=[detect_order_blocks()] | lang=es
- "smc_premium_discount_rationale_76": "Filtra Bullish Order Blocks ubicados en Discount." | kind=entity | source=strategy/smc/premium_discount.py:L76 | neighbors=[is_bullish_ob_in_discount()] | lang=en
- "smc_premium_discount_rationale_8": "Calcula las zonas Premium, Discount y Equilibrium.\r \r     Para cada vela:\r     -" | kind=entity | source=strategy/smc/premium_discount.py:L8 | neighbors=[calculate_premium_discount()] | lang=es
- "smc_premium_discount_rationale_94": "Filtra Bearish Order Blocks ubicados en Premium." | kind=entity | source=strategy/smc/premium_discount.py:L94 | neighbors=[is_bearish_ob_in_premium()] | lang=en
- "smc_risk_reward": "risk_reward.py" | kind=code-symbol | source=strategy/smc/risk_reward.py:L1 | neighbors=[calculate_risk_reward()] | lang=en
- "smc_risk_reward_rationale_8": "Calcula Stop Loss, Take Profit y Risk/Reward\r     para las confirmaciones de ent" | kind=entity | source=strategy/smc/risk_reward.py:L8 | neighbors=[calculate_risk_reward()] | lang=es
- "smc_setup_detector": "setup_detector.py" | kind=code-symbol | source=strategy/smc/setup_detector.py:L1 | neighbors=[detect_setups()] | lang=en
- "smc_setup_detector_rationale_9": "Detecta setups SMC utilizando una secuencia temporal.\r \r     Setup LONG:" | kind=entity | source=strategy/smc/setup_detector.py:L9 | neighbors=[detect_setups()] | lang=en
- "smc_swings": "swings.py" | kind=code-symbol | source=strategy/smc/swings.py:L1 | neighbors=[detect_swings()] | lang=en
- "smc_swings_rationale_5": "Detecta Swing High y Swing Low.\r \r     left: número de velas a comparar a la izq" | kind=entity | source=strategy/smc/swings.py:L5 | neighbors=[detect_swings()] | lang=en

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-042.json

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
