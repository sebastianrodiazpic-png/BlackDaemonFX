# DaemonBlackFx v67 — Entrada vs. ahora en tiempo real

## Problema
La auditoría mostraba correctamente la tesis de entrada persistida, pero
"Lo que ve ahora" dependía del último `SYMBOL_PROCESS_RESULT`. En workers con
muchos instrumentos ese símbolo podía tardar varios minutos en volver a ser
analizado, por lo que el panel quedaba en "Sin registro" o con datos obsoletos.

## Solución
- Cada worker SMC reevaluará exclusivamente los símbolos que mantienen posiciones
  abiertas cada ~10 segundos.
- Se usa `multi_timeframe.analyze_symbol()` directamente: NO ejecuta nuevas órdenes.
- El resultado actual se normaliza y se persiste en
  `trade_visual_audits.latest_market_json.current_strategy_view`.
- La tesis de entrada (`entry_context_json`) continúa inmutable.
- El dashboard prioriza el estado actual persistido del trade y luego usa el
  último análisis general como fallback.
- "Lo que ve ahora" muestra hora de última evaluación.
- Incluso estados NO_H1_CONTEXT / NO_M15_SETUP / WAITING_M5 / STALE quedan visibles,
  evitando "Sin registro".
