# DaemonBlackFx v66 — SMC hasta TP4 con protección progresiva

Riesgo total del setup SMC: 1%.
- TP1: 0,5% de riesgo, objetivo 1R y cierre total.
- RUNNER: 0,5% de riesgo.

Protección:
1. Cuando TP1 cierra en beneficio, RUNNER pasa a Break Even +2 puntos favorables,
   incluso si el precio retrocedió antes del siguiente ciclo de monitor.
2. En 2R: SL se bloquea en +1R antes de evaluar continuación hacia TP3.
3. En ~2,5R: SL avanza a +2R.
4. En 3R: se evalúa continuación; sin continuación se cierra, con continuación busca TP4.
5. En ~3,5R: SL avanza a +3R.
6. TP4 = 4R es el máximo SMC.

La extensión no aumenta el riesgo inicial. ORB permanece independiente.
