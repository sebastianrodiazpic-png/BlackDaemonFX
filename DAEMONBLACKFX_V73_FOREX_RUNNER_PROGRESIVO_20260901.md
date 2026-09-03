# DaemonBlackFx v73 — Forex Runner progresivo TP2 → TP3 → TP4

## Riesgo
Cada setup Forex mantiene 1% total:
- TP1: 0,5% -> 1R.
- RUNNER: 0,5%.

## Objetivo lógico
El RUNNER nace con objetivo lógico TP2 = 2R.
El broker conserva TP4 = 4R como `broker_safety_target_rr`; esto es un fail-safe
técnico, no autorización lógica para saltarse evaluaciones.

## Evaluación
1. TP1 cerrado -> Break Even +2 puntos (mecanismo existente).
2. Al alcanzar 2R:
   - primero SL a +1R;
   - evaluar continuación M5;
   - si falla -> cerrar runner;
   - si confirma -> objetivo lógico cambia a TP3 = 3R.
3. Al alcanzar 3R:
   - antes de evaluar se protege al menos +2R;
   - si falla continuidad -> cerrar;
   - si confirma -> elevar SL a +2,5R y objetivo lógico TP4 = 4R.
4. TP4 es el objetivo final.

## Auditoría
Se persisten:
- runner_initial_target_rr
- runner_logical_target_rr
- runner_candidate_target_rr
- runner_broker_safety_target_rr
- runner_profit_lock_rr
- runner_extension_decisions
- runner_extension_stage

Así `/account`, SQLAlchemy y reportes pueden reconstruir cuándo un runner ganó
derecho a TP3/TP4.
