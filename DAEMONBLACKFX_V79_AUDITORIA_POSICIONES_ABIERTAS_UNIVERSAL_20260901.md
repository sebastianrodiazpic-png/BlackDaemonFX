# DaemonBlackFx v79 — Auditoría universal de posiciones abiertas

## Objetivo
Toda posición abierta gestionada por DaemonBlackFx mantiene telemetría reciente
sin depender de si fue abierta por SMC, Forex u ORB.

## Frecuencias
- Telemetría MT5 ligera: en cada pasada del monitor de posiciones
  (por defecto cada 2 s).
- Reanálisis de estrategia / Entrada vs. Ahora: conserva su refresco periódico
  independiente.
- Gráficos completos: permanecen en una frecuencia más baja para no sobrecargar
  MT5 ni SQLite.

## Persistencia
Cada pasada del monitor persiste en `trade_visual_audits.latest_market`:
- current_price
- current_rr
- current_stop_loss
- initial_stop_loss
- take_profit
- distance_to_sl_r
- distance_to_tp_r
- break_even_confirmed
- MFE / MAE
- runner_extension_stage
- runner_profit_lock_rr
- market_evaluated_at
- telemetry_mode
- current_strategy_view cuando esté disponible

## Dashboard
Para calcular la salud de una posición abierta, el dashboard prioriza:
1. `latest_market.current_strategy_view` persistido por el owner del trade.
2. último análisis general del símbolo.
3. memoria reciente del dashboard.

Esto evita que un análisis global viejo o de otra estrategia reemplace la
telemetría actual de una posición abierta.
