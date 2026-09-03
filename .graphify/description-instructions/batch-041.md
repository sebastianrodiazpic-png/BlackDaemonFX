# Node Description Batch 42 of 56

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

- "reporting_trade_report_exporter_tradereportexporter_init": ".__init__()" | kind=code-symbol | source=reporting/trade_report_exporter.py:L60 | neighbors=[TradeReportExporter] | lang=en
- "risk_money_management_rationale_128": "Valida que trades sea un DataFrame." | kind=entity | source=strategy/risk/money_management.py:L128 | neighbors=[validate_dataframe()] | lang=fr
- "risk_money_management_rationale_155": "Calcula cuánto dinero se arriesgará.\r \r     Fórmula:\r \r         risk_amount =" | kind=entity | source=strategy/risk/money_management.py:L155 | neighbors=[calculate_risk_amount()] | lang=es
- "risk_money_management_rationale_18": "Valida que el balance sea un número válido y mayor que cero." | kind=entity | source=strategy/risk/money_management.py:L18 | neighbors=[validate_balance()] | lang=es
- "risk_money_management_rationale_199": "Actualiza el balance después de una operación.\r \r     Fórmula:\r \r         new_ba" | kind=entity | source=strategy/risk/money_management.py:L199 | neighbors=[update_balance()] | lang=en
- "risk_money_management_rationale_241": "Aplica Money Management a una sola operación.\r \r     Agrega:\r \r         balance_" | kind=entity | source=strategy/risk/money_management.py:L241 | neighbors=[apply_money_management_to_trade()] | lang=en
- "risk_money_management_rationale_347": "Aplica Money Management secuencialmente\r     a todas las operaciones.\r \r     El" | kind=entity | source=strategy/risk/money_management.py:L347 | neighbors=[apply_money_management()] | lang=es
- "risk_money_management_rationale_53": "Valida el porcentaje de riesgo." | kind=entity | source=strategy/risk/money_management.py:L53 | neighbors=[validate_risk_percent()] | lang=en
- "risk_money_management_rationale_570": "Obtiene el balance final.\r \r     Utiliza balance_after de la última operación." | kind=entity | source=strategy/risk/money_management.py:L570 | neighbors=[get_final_balance()] | lang=es
- "risk_money_management_rationale_641": "Calcula estadísticas de drawdown\r     a partir de una serie de balances." | kind=entity | source=strategy/risk/money_management.py:L641 | neighbors=[calculate_drawdown_statistics()] | lang=nl
- "risk_money_management_rationale_715": "Calcula estadísticas completas\r     de la evolución del capital.\r \r     Retorna:" | kind=entity | source=strategy/risk/money_management.py:L715 | neighbors=[calculate_money_management_statistics()] | lang=en
- "risk_money_management_rationale_943": "Ejecuta todo el proceso de Money Management.\r \r     Proceso:\r \r         1. Valid" | kind=entity | source=strategy/risk/money_management.py:L943 | neighbors=[run_money_management()] | lang=en
- "risk_money_management_rationale_97": "Valida el PnL de una operación." | kind=entity | source=strategy/risk/money_management.py:L97 | neighbors=[validate_pnl()] | lang=es
- "risk_money_manager_moneymanager_init": ".__init__()" | kind=code-symbol | source=risk/money_manager.py:L36 | neighbors=[MoneyManager] | lang=en
- "risk_money_manager_moneymanager_reset_balance": ".reset_balance()" | kind=code-symbol | source=risk/money_manager.py:L163 | neighbors=[MoneyManager] | lang=en
- "risk_money_manager_rationale_123": "Procesa una operación y actualiza\r         el balance de la cuenta." | kind=entity | source=risk/money_manager.py:L123 | neighbors=[.process_trade()] | lang=es
- "risk_money_manager_rationale_19": "Gestiona el riesgo y calcula el resultado monetario\r     de las operaciones." | kind=entity | source=risk/money_manager.py:L19 | neighbors=[MoneyManager] | lang=es
- "risk_money_manager_rationale_55": "Retorna el capital actual." | kind=entity | source=risk/money_manager.py:L55 | neighbors=[.get_current_balance()] | lang=es
- "risk_money_manager_rationale_6": "Resultado financiero de una operación." | kind=entity | source=risk/money_manager.py:L6 | neighbors=[TradeRiskResult] | lang=en
- "risk_money_manager_rationale_65": "Calcula cuánto dinero se arriesga\r         en una operación." | kind=entity | source=risk/money_manager.py:L65 | neighbors=[.calculate_risk_amount()] | lang=es
- "risk_money_manager_rationale_88": "Calcula el resultado monetario\r         utilizando el R realizado.\r \r         Ej" | kind=entity | source=risk/money_manager.py:L88 | neighbors=[.calculate_profit_loss()] | lang=es
- "risk_position_sizing_rationale_13": "Calcula el tamaño de posición basándose en el riesgo\r     permitido sobre el cap" | kind=entity | source=strategy/risk/position_sizing.py:L13 | neighbors=[calculate_position_size()] | lang=es
- "risk_position_sizing_rationale_181": "Agrega información de gestión de tamaño de posición\r     a un DataFrame de opera" | kind=entity | source=strategy/risk/position_sizing.py:L181 | neighbors=[add_position_sizing()] | lang=nl
- "risk_risk_manager_rationale_1109": "Verifica si se alcanzó el límite máximo\r     de pérdida diaria." | kind=entity | source=strategy/risk/risk_manager.py:L1109 | neighbors=[check_daily_loss_limit()] | lang=es
- "risk_risk_manager_rationale_1174": "Verifica si el drawdown actual supera\r     el límite permitido." | kind=entity | source=strategy/risk/risk_manager.py:L1174 | neighbors=[check_drawdown_limit()] | lang=es
- "risk_risk_manager_rationale_122": "Valida un número entero." | kind=entity | source=strategy/risk/risk_manager.py:L122 | neighbors=[validate_integer()] | lang=fr
- "risk_risk_manager_rationale_1246": "Evalúa completamente el riesgo de una operación.\r \r     Devuelve:\r \r         app" | kind=entity | source=strategy/risk/risk_manager.py:L1246 | neighbors=[evaluate_trade_risk()] | lang=es
- "risk_risk_manager_rationale_158": "Valida que trades sea un pandas DataFrame." | kind=entity | source=strategy/risk/risk_manager.py:L158 | neighbors=[validate_dataframe()] | lang=fr
- "risk_risk_manager_rationale_1701": "Alias simplificado de evaluate_trade_risk()." | kind=entity | source=strategy/risk/risk_manager.py:L1701 | neighbors=[evaluate_risk()] | lang=nl
- "risk_risk_manager_rationale_1717": "Genera un resumen simplificado del resultado\r     de una evaluación de riesgo." | kind=entity | source=strategy/risk/risk_manager.py:L1717 | neighbors=[get_risk_summary()] | lang=en
- "risk_risk_manager_rationale_187": "Valida la dirección de una operación.\r \r     Valores permitidos:\r \r         BUY" | kind=entity | source=strategy/risk/risk_manager.py:L187 | neighbors=[validate_direction()] | lang=en
- "risk_risk_manager_rationale_234": "Verifica que el Stop Loss esté correctamente\r     ubicado según la dirección." | kind=entity | source=strategy/risk/risk_manager.py:L234 | neighbors=[validate_stop_loss_direction()] | lang=en
- "risk_risk_manager_rationale_306": "Verifica que el Take Profit esté correctamente\r     ubicado según la dirección." | kind=entity | source=strategy/risk/risk_manager.py:L306 | neighbors=[validate_take_profit_direction()] | lang=en
- "risk_risk_manager_rationale_36": "Valida que un valor sea numérico, finito y mayor que cero." | kind=entity | source=strategy/risk/risk_manager.py:L36 | neighbors=[validate_positive_number()] | lang=fr
- "risk_risk_manager_rationale_378": "Calcula la relación Risk / Reward.\r \r     Fórmula:\r \r         riesgo = abs(entry" | kind=entity | source=strategy/risk/risk_manager.py:L378 | neighbors=[calculate_risk_reward()] | lang=en
- "risk_risk_manager_rationale_455": "Verifica si la operación cumple con el\r     Risk / Reward mínimo." | kind=entity | source=strategy/risk/risk_manager.py:L455 | neighbors=[validate_risk_reward()] | lang=es
- "risk_risk_manager_rationale_511": "Calcula el tamaño de posición y riesgo real\r     utilizando position_sizing.py." | kind=entity | source=strategy/risk/risk_manager.py:L511 | neighbors=[calculate_current_risk()] | lang=es
- "risk_risk_manager_rationale_558": "Calcula un monto máximo de pérdida basado\r     en un porcentaje del balance." | kind=entity | source=strategy/risk/risk_manager.py:L558 | neighbors=[calculate_max_loss_amount()] | lang=fr
- "risk_risk_manager_rationale_587": "Calcula el PnL y la pérdida acumulada\r     del día actual." | kind=entity | source=strategy/risk/risk_manager.py:L587 | neighbors=[calculate_daily_loss()] | lang=es
- "risk_risk_manager_rationale_716": "Cuenta las operaciones perdedoras consecutivas\r     al final del historial." | kind=entity | source=strategy/risk/risk_manager.py:L716 | neighbors=[count_consecutive_losses()] | lang=es

## Instructions

Write a single JSON object mapping each node id to a one-sentence description
to: c:\TradingBoot\smc_synthetic_bot\.graphify\description-instructions\batch-041.json

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
