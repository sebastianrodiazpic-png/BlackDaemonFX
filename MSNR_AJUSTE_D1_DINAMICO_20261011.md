# Malaysian SNR: ajuste dinámico del veto D1 en sintéticos

Implementado el 11 de octubre de 2026, versión `msnr-v2.2-dynamic-synthetic-d1`.

## Uso

1. Abrir `/strategy-bases`.
2. En «Ajustes de Malaysian SNR», marcar o desmarcar «Exigir dirección D1 en sintéticos».
3. Pulsar «Guardar ajuste» y esperar la confirmación de guardado.
4. El ajuste se aplica al próximo análisis Malaysian SNR, incluso si el worker ya estaba ejecutándose. «Actualizar estado» consulta la preferencia persistida.

El estado solicitado y guardado es **desactivado**, versión de preferencia 1. El control conserva la preferencia al reiniciar. Cambiar la casilla sin guardar no modifica la estrategia.

## Alcance

- Desactivado: el sesgo de la última D1 cerrada es contexto; no veta una entrada sintética por ser contrario o neutral.
- Activado: los sintéticos vuelven a exigir alineación con esa vela D1; una vela neutral bloquea.
- Forex, metales e índices tradicionales conservan su filtro D1.
- Se siguen exigiendo datos diarios válidos y recientes y se conservan los obstáculos diarios, la estructura H1, el retest M15, las invalidaciones y las reglas de riesgo.
- Boom conserva compras y Crash ventas según la política existente.
- La configuración se guarda en `strategy_runtime_preferences`, separada por fuente. El panel actual controla DEMO.
- Si la preferencia no puede leerse, el análisis queda bloqueado con `MSNR_SETTINGS_UNAVAILABLE`; no se interpreta el fallo como permiso para operar.
- Los resultados del analizador incluyen si el veto se aplica y la versión de la preferencia utilizada.

## Activación y comprobación

Se comprobó ausencia de posiciones Malaysian SNR en SQLite y en el terminal antes de recargar únicamente ese worker mediante el controlador del coordinador. El proceso reanudó sus ciclos y publicó la versión v2.2. Los demás workers siguieron activos.

131 pruebas pasaron: entradas sintéticas contrarias al sesgo diario, restauración del veto, neutralidad, obstáculos D1, datos faltantes/antiguos, política Boom/Crash, persistencia entre procesos, validación HTTP, recarga de analizador, telemetría, panel y regresiones del retest/replay.

El nuevo control se comprobó en el navegador: carga el estado apagado, habilita guardar un cambio pendiente y conserva el estado apagado al deshacerlo. Captura: `storage/analysis/msnr_dynamic_d1_control_20261011.jpg`.

Este cambio no recalcula estadísticas históricas. El replay previo evaluó el veto D1 activado; no valida el WinRate de esta nueva configuración.
