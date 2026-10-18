# Malaysian SNR: controles dinámicos y valores de referencia

Disponible en `/strategy-bases`, pestaña **Malaysian SNR (H1 / M15)**. Versión `msnr-v2.5-configurable-opportunities`.

## Valores por defecto

| Control | Referencia |
|---|---|
| Exigir dirección D1 en sintéticos | Desactivado |
| Cuerpo mínimo Fractal H1 | 50% |
| Distancia máxima Fractal | 0,50 ATR H1 |
| Ventana máxima de retest | 90 minutos |
| Activos adicionales seleccionados | Jump 50 Index y Jump 100 Index |
| Modo de activos adicionales | Observación, sin órdenes |
| Modo de continuación A/V | Observación, sin órdenes |
| Cuerpo mínimo H1 de continuación | 50% |
| ADX mínimo H1 de continuación | 20 |
| Exigir nivel realmente Fresh en continuación | Activado |
| Diagnóstico detallado H1 | Activado |
| Reutilización de estructura H1 | Activado |
| Priorizar setups vivos esperando retest | Activado |
| Separar análisis del bloqueo de envío | Activado |

Los valores de referencia también se muestran en **Consultar valores por defecto**. Se conservaron los ajustes previos guardados: cuerpo Fractal **45%**, distancia **0,50 ATR H1** y veto D1 desactivado. Restaurar no ocurre al abrir la página.

## Guardar o restaurar

1. Modificar los controles deseados. El panel indica cambios pendientes.
2. Pulsar **Guardar ajustes** para persistirlos. Se aplican al siguiente análisis; los nuevos activos y la prioridad se actualizan al siguiente ciclo.
3. Para restaurar, pulsar **Volver a valores por defecto**. Esto carga el preset en el formulario. Revisar y pulsar **Guardar ajustes** para aplicarlo.
4. **Actualizar estado** recupera lo guardado y descarta cambios pendientes del formulario.

Los cambios se conservan al reiniciar el bot. Los valores numéricos y los modos se validan antes del guardado completo. Un valor inválido no permite guardar parcialmente otros cambios de esa solicitud.

## Activos y continuación

Hay cuatro candidatos configurables: Jump 50, Jump 100, Jump 75 y Volatility 75 (1s). Los dos primeros se seleccionan por defecto. Su modo se elige entre **Desactivado**, **Observación — sin órdenes** y **Operar**; se añaden a la selección habitual de SNR.

La continuación A/V tiene un modo independiente y ajustes propios de cuerpo, ADX y frescura. Activar la continuación no modifica el cuerpo mínimo del Fractal. Los niveles consumidos permanecen bloqueados; si se desmarca exigir Fresh, las visitas previas siguen sujetas a la política existente de nivel probado y penetración.

En Observación se analizan y registran señales sin entrar al procesamiento de órdenes. Ese modo aplica a los activos adicionales o a la continuación según el control elegido; el Fractal de la selección habitual mantiene su funcionamiento anterior. Una continuación en observación no desplaza una entrada Fractal válida para operar.

El WinRate de estos candidatos y de la continuación con los ajustes actuales todavía requiere replay y evaluación posterior. Cambiar parámetros no recalcula las estadísticas históricas del panel.

## Diagnóstico y seguimiento

Cuando no hay setup, el diagnóstico H1 registra cuerpo observado, mínimo aplicado, ATR, ADX, barrido, ruptura, alineación geométrica y patrones Quasimodo confirmados. Se audita una vez por vela H1 cerrada y versión de parámetros.

La estructura H1 y sus diagnósticos se reutilizan mientras los datos y parámetros relevantes permanezcan iguales. Una revisión de precios o un cambio de parámetros invalida la entrada correspondiente de caché. El retest M15 se verifica de nuevo en cada análisis y la ejecución utiliza una cotización actual.

Los setups vivos esperando retest se procesan antes que los demás activos. Se puede desactivar esta prioridad desde el panel. El análisis previo puede realizarse fuera del bloqueo compartido del activo; una entrada válida conserva el bloqueo, las comprobaciones de posiciones, límites, deduplicación y validación del precio. Los parámetros y el cierre M15 se revalidan si cambian durante el procesamiento.

## Activación y verificación

Se recargó únicamente el worker SNR tras confirmar cero posiciones abiertas. La versión activa utiliza la preferencia guardada número 5 y evalúa 25 activos, incluidos Jump 50 y Jump 100. Los modos nuevos quedaron en Observación. Se verificó en ejecución el rechazo de un nivel probado en Jump 100 por la exigencia Fresh.

La verificación cubre persistencia, restauración, validación de solicitudes, modos de activos y continuación, separación de señales de observación, caché, prioridad, revalidación antes de envío y protecciones existentes de posiciones y riesgo.
