# Malaysian SNR: variantes estructurales configurables

Versión `msnr-v2.6-structural-opportunities`. Los controles están en `/strategy-bases`, pestaña **Malaysian SNR (H1 / M15)**. Se incorporan las cinco mejoras de la revisión web; la confirmación sigue siendo M15. El experimento M5 quedó propuesto para una investigación posterior y no forma parte de esta versión.

## Modos y valores de referencia

| Grupo | Modo inicial | Parámetros por defecto |
|---|---|---|
| A/V ampliado | Observación | Giro de cuerpos sin envolvente |
| Cambio de función SBR/RBS | Observación | Máximo 1 cambio; desplazamiento cerrado ≥0,20 ATR H1 |
| Quasimodo ampliado | Observación | Últimos 8 swings confirmados; profundidad de cabeza ≥0,20 ATR H1 |
| Dirección macro estructural | Observación | Estructura D1; pivotes con 2 velas de confirmación por lado |
| Open–Close / Decision Levels | Observación | Formación H1; separación ≥0,05 ATR, 2 ticks y 2 veces el spread |

Estos valores son hipótesis iniciales, no parámetros optimizados ni una estimación de WinRate. Cada modo se puede cambiar independientemente a **Desactivado**, **Observación** u **Operar**.

Se conservaron los ajustes previos: cuerpo Fractal 45%, distancia 0,50 ATR H1, veto D1 sintético desactivado, activos adicionales vacíos y desactivados, continuación en observación con Fresh obligatorio desmarcado y ventana de retest de 90 minutos.

## Qué hace cada grupo

**A/V ampliado** agrega niveles que cumplen cambio de color pero no la condición envolvente de la definición original. No modifica la continuación original ni el mapa H1/D1 de obstáculos. Comparte los mínimos de cuerpo, ADX y mecha de continuación y sus restricciones de frescura. Seleccionar Envolvente deja sin niveles adicionales a esta variante. La definición elegida también se utiliza en el grupo SBR/RBS.

**SBR/RBS** conserva los cambios de función de cada nivel en un prefijo de velas cerradas. Un nuevo episodio requiere un cierre que cambie de lado, desplazamiento suficiente y un primer retest posterior. No convierte cualquier nivel consumido en Fresh: mantiene su estado anterior en el diagnóstico. La primera ruptura de un nivel Fresh elegible pertenece a continuación y no se vuelve a generar aquí. La opción permite 1–3 cambios por nivel dentro del historial de análisis de la estrategia; no representa un historial ilimitado del instrumento.

**Quasimodo ampliado** busca triples dentro de una ventana acotada de swings confirmados, permitiendo oscilaciones intermedias. Exige cabeza más profunda, confirmación del pivote antes de la primera ruptura posterior y retest del hombro. La cabeza sigue siendo la invalidación. Los patrones que ya detecta el QM original no se agregan otra vez.

**Dirección macro** ofrece estructura D1, H4 o acuerdo D1/H4. Usa pivotes confirmados de cierres, progresión de swings y rupturas posteriores. En Observación conserva el filtro por color de la última vela D1 para las entradas normales; si la estructura recupera una entrada rechazada, esa entrada se registra sin órdenes. En Operar sustituye el método anterior y espera si no hay dirección suficiente. El grupo solo interviene cuando el filtro macro es obligatorio: no reactiva el veto D1 en sintéticos. Los obstáculos D1 se mantienen.

**Open–Close** exige dos velas cerradas consecutivas del mismo color, separación direccional y ausencia de penetración en la banda durante la vela de formación. Usa el mayor umbral entre ATR, tamaño real de tick y spread actual verificable. Comparte cuerpo y ADX mínimos con continuación. Se puede formar en H1 o H4, siempre con confirmación de retorno en M15. No es un FVG de tres velas. Si falta información de mercado o H4, no genera esa variante; las demás pueden seguir analizándose. Las consultas adicionales de precio se realizan solo cuando hay una separación potencialmente material.

## Guardar, restaurar y operar

1. Elegir los modos y modificar los parámetros deseados.
2. Pulsar **Guardar ajustes**. Se validan todos los campos antes de guardar; un valor inválido no aplica cambios parciales.
3. Los valores quedan persistidos y se aplican al siguiente análisis. No es necesario reiniciar por cambios de parámetros.
4. **Consultar valores por defecto** muestra las referencias de todos los grupos.
5. **Volver a valores por defecto** carga el preset completo en el formulario. Solo se aplica al pulsar Guardar ajustes. Incluye los controles anteriores: revisar también cuerpo Fractal, extras y Fresh.
6. **Actualizar estado** descarta cambios pendientes y recupera lo guardado.

Observación nunca entra al procesamiento de órdenes. Una variante nueva en Operar queda sujeta al resto de restricciones de la estrategia, a la cotización real, obstáculos, posiciones, deduplicación y riesgo. El modo de activos adicionales sigue prevaleciendo sobre sus señales: si un activo está en Observación, cambiar un escenario a Operar no habilita órdenes para ese activo.

La señal normal elegida conserva su prioridad; se recogen además las variantes en observación para auditoría. Cuando dos detectores producen una oportunidad equivalente en el mismo nivel y dirección, se evita que una candidata en observación sustituya a una habilitada para operar. La auditoría registra la familia, marco de estructura, contexto macro, identidad y plan de las observaciones junto a las entradas normales.

## Verificación y límites

Las pruebas cubren migración de preferencias, validación y restauración por API, niveles no envolventes con retest cerrado, renovación de episodios, límites de cambios, QM con swings intermedios, ausencia de anticipación de pivotes, sesgo estructural, confluencia D1/H4, gaps H1/H4 con retest M15 y separación entre observación y órdenes. Se verificaron también las protecciones existentes de posiciones, deduplicación y gestión dual.

Se aprobaron 303 pruebas distintas: una revisión amplia de 301 y verificaciones posteriores de los detectores y dos casos adicionales de telemetría/eficiencia. Se recargó únicamente SNR tras verificar cero posiciones abiertas en base y broker. La ejecución confirma la versión v2.6 con la preferencia 8, un universo de 23 activos y los cinco modos nuevos en Observación. El panel se verificó visualmente y se comprobó que restaurar referencias no modifica lo guardado hasta confirmar con Guardar ajustes.

No se realizó un nuevo replay de rendimiento de dos años para esta versión. Las estadísticas históricas visibles no se recalculan al guardar ni validan las nuevas variantes. Para acreditar más trades y mejor calidad deben compararse contra la configuración previa, por setup de dos piernas, incluyendo costes, expectativa, factor de beneficio, drawdown y una muestra posterior nueva.
