# DaemonBlackFx v65 — SMC 0,5% + 0,5% con TP3 protegido

## Smart Money Concepts
Riesgo total por setup lógico: 1%.

- Pierna TP1: 0,5% de riesgo, objetivo 1R. Se cierra completamente en TP1.
- Pierna RUNNER: 0,5% de riesgo.
  - Objetivo lógico inicial: TP2 = 2R.
  - A 1R: Break Even protector (mecanismo existente).
  - A 2R: primero mueve SL a +1R; después evalúa continuación M5.
  - Si no hay continuación: cierre automático del RUNNER y materialización de ganancia.
  - Si hay continuación: mantiene objetivo TP3 = 3R.
  - A ~2,5R: mueve SL a +2R automáticamente.
  - TP3 = 3R es el objetivo máximo para SMC.
  - SMC ya no intenta TP4.

## ORB
No se modifica. ORB conserva su gestión independiente y capacidad de extensión hasta TP4.

## Riesgo
El 1% continúa siendo el riesgo TOTAL del setup:
0,5% TP1 + 0,5% RUNNER = 1%.
La extensión de objetivos nunca aumenta el riesgo inicial.
