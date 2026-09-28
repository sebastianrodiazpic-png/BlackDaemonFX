# Prueba SMC configurada — 17 septiembre 2026

LiveTradingConfig usa H1_PRIMARY y ATR_BOUNDED por defecto. H1 mantiene su
ubicación discount BUY / premium SELL tanto en análisis como en precio ejecutable.
ATR_BOUNDED mantiene rechazo y respeto del OB; ampliación limitada al75% del bloque.
Desplazamiento, caducidad, RR y límites de riesgo se conservan. ORB no usa este guard.
No hay evidencia todavía de mejora de rentabilidad.

Dashboard: panel Prueba SMC · H1 y retesteo ATR, con reglas efectivas, fecha de
arranque/actualización, rechazos, última evaluación por símbolo y comparación de
ubicación. Señales caducadas agrupadas por símbolo/hora, sin reutilizarlas para entrar.
Los contadores son evaluaciones desde arranque por día Santiago, no trades únicos.
Los snapshots antiguos conservan su fecha visible; no implican un worker activo.
Persistencia: storage/runtime/smc_trial, un archivo atómico por worker. Un fallo de
telemetría queda en trial_audit_error y no interrumpe ni reintenta una orden.

Reiniciar workers y dashboard para aplicar. No se reiniciaron durante el cambio.
Rollback: configurar smc_entry_location_policy=ALL_TIMEFRAMES y
retest_tolerance_mode=STRICT en LiveTradingConfig. No se cambió el porcentaje80%.
