# Malaysian SNR: recuperación selectiva de oportunidades

Implementado el 12 de octubre de 2026. Motor: `msnr-v2.8-selective-recovery`. Preferencias aplicadas: versión 11.

El cambio permite recuperar y medir oportunidades por instrumento sin convertir la poda histórica de 23 activos en un bloqueo permanente. No acredita un aumento de WinRate. Los activos recuperados empiezan en observación porque la prueba reciente todavía no muestra rentabilidad positiva del conjunto.

## Controles disponibles

En `/strategy-bases`, pestaña **Malaysian SNR**, la sección **Recuperación selectiva por activo** contiene 60 instrumentos agrupados en sintéticos, Forex, criptos, metales, índices y materias primas.

Cada instrumento tiene tres controles independientes:

| Control | Efecto |
|---|---|
| Modo del activo | Heredar selección, Desactivado, Observación u Operar. Un modo explícito tiene prioridad sobre la selección y los antiguos candidatos adicionales. |
| Continuación | Heredar el modo general o asignar Desactivado, Observación u Operar a ese instrumento. |
| Confirmación M5 | Heredar el modo general o asignar Desactivado, Observación u Operar a ese instrumento. |

**Observación del activo impide sus órdenes**, aunque Continuación o M5 estén en Operar. Operar habilita la evaluación para ejecución: siguen siendo necesarias una señal válida y todas las comprobaciones de riesgo y ejecución. No fuerza una entrada. Desactivado retira el instrumento del escaneo y evita solicitar sus velas. El escaneo atiende primero los activos que pueden operar y después los de observación, conservando la prioridad de retests pendientes dentro de cada grupo.

Continuación tiene ahora distancia máxima y mecha máxima propias. Quasimodo tiene su distancia máxima propia. Cambiar estos controles no modifica la distancia del Fractal.

## Configuración aplicada y valores de referencia

| Parámetro | Aplicado | Por defecto al restaurar |
|---|---:|---:|
| Continuación general | Operar | Operar |
| Distancia Continuación/A/V | 0,50 ATR H1 | 0,50 ATR H1 |
| Mecha máxima de ruptura Continuación | 25% | 25% |
| Distancia Quasimodo | 0,50 ATR H1 | 0,50 ATR H1 |
| Cuerpo Fractal H1 | 45%, conservado | 50% |
| Distancia Fractal | 0,50 ATR H1 | 0,50 ATR H1 |
| Retest / recuperación | 90 / 45 minutos | 90 / 45 minutos |
| Cuerpo mínimo de recuperación | 35% | 35% |
| Exigir dirección D1 en sintéticos | Desactivado | Desactivado |
| Exigir Fresh en Continuación | Desactivado, conservado | Activado |
| M5 general / alternativa H4 | Observación / Observación | Observación / Observación |
| Frecuencia mínima para comparación | 80% | 80% |
| Muestra mínima resuelta por variante | 30 | 30 |

Se recuperaron en **Observación**: Crash 500 Index, Step Index 500, Volatility 10 Index, Volatility 25 Index, Volatility 75 Index, Boom 500 Index, Boom 600 Index y BTCUSD. Su M5 también quedó explícitamente en Observación y su Continuación hereda el modo general. El motor confirmó **31 instrumentos en el ciclo: 23 habituales y ocho recuperados**.

Se conservaron los ajustes previos de A/V ampliado, cambio de función, QM ampliado, Open–Close, dirección macro e IA. La política existente permite observar una IA incompatible solamente en DEMO; no se entrenó ni reemplazó el modelo.

**Volver a valores por defecto** carga referencias en el formulario. Hay que pulsar **Guardar ajustes** para aplicarlas. Restaurar vacía los modos propios por activo, vuelve a la selección habitual y recupera los dos candidatos adicionales históricos en observación; no conserva el conjunto de ocho recuperados como una nueva selección predeterminada. La nota de valores por defecto muestra también los demás controles.

## Registro y comparación

El panel muestra setups únicos, confirmados y ejecutados por activo y el primer motivo registrado de cada candidato. Esto evita explicar todos los rechazos únicamente por su estado final «vencido». El registro empezó recientemente: una consulta de siete días no significa que existan siete días completos de seguimiento.

El replay admite un archivo de ajustes congelado y compara frecuencia, expectativa y beneficio en R por activo, familia y escenario. Los criterios rechazan muestras pequeñas, resultados incompletos o ambiguos, períodos o feeds distintos, expectativa no positiva y variantes que no mejoran el resultado total. La frecuencia mínima evita aprobar una mejora aparente conseguida eliminando demasiadas entradas. Estos criterios son de investigación; **no activan activos, no promueven modelos y no garantizan rentabilidad**.

Siguen vigentes las velas cerradas, el retorno posterior a la ruptura, el primer retest, la invalidación, los obstáculos y el espacio mínimo de 2R, el riesgo con dirección correcta, la validación del precio efectivo y la prevención de entradas duplicadas.

## Prueba histórica de los activos recuperados

Ventana común: **4 de octubre de 2026, 00:00 UTC, a 11 de octubre de 2026, 00:00 UTC**. Los ocho instrumentos se procesaron sin errores. La ejecución es exclusivamente una hipótesis del replay; no usa el ejecutor de órdenes.

| Variante | Entradas simuladas | Resultados resueltos | Sin resultado completo | WinRate resuelto | Resultado resuelto |
|---|---:|---:|---:|---:|---:|
| M15 | 5 | 4 | 1 | 0% | −4,00R |
| M15 + M5 | 16 | 13 | 3 | 7,69% | −9,93R |
| M15 + alternativa H4 | 5 | 4 | 1 | 0% | −4,00R |

M5 aumentó la frecuencia y redujo la pérdida media por operación resuelta de −1,00R a −0,764R, pero aumentó la pérdida total. Ningún activo con entradas superó los criterios de investigación; Boom 600 no produjo entradas. La muestra por activo es inferior a 30 y algunos resultados están incompletos. Por ello los ocho activos permanecen en observación.

Esta semana no es una validación de dos años. El historial nativo M5 disponible no cubre dos años para los 60 activos. El replay usa precios OHLC y una aproximación del spread; no reproduce completamente comisiones, deslizamiento, swap, redondeo del bróker ni límites simultáneos de cartera. Los resultados simulados no son elegibles para entrenamiento. El siguiente análisis debe ampliar la ventana común disponible, incluir costes verificables y separar períodos de selección y validación antes de elegir qué combinaciones pasar a Operar.

## Verificación de implementación

- 327 pruebas de estrategia, persistencia, API, integración y replay aprobadas; después del último ajuste de prioridad, las 22 pruebas de recuperación selectiva también aprobaron.
- Sintaxis de JavaScript verificada. Navegador: 60 selectores de activos, BTCUSD y M5 en Observación, Continuación general en Operar y Guardar deshabilitado cuando no hay cambios. Un cambio temporal habilitó Guardar y Actualizar estado lo descartó sin modificar las preferencias.
- Motor en RUNNING, versión v2.8 y preferencias 11, ciclo de 31 instrumentos. Los logs muestran BTCUSD dentro del ciclo. Solo se recargó el motor SNR, tras comprobar cero posiciones y órdenes pendientes SNR; el coordinador y los otros motores se conservaron. Una comprobación adicional posterior de procesos fue rechazada por el límite de uso de la revisión automática; ya existían la comprobación de procesos y la evidencia de funcionamiento del motor.
- Modelo de IA sin cambios: SHA256 `7546b9ab6b859ef648d21622d7fe0e30f70ab5cc63e219f8d94ed39ddbc81d74`.

## Evidencia local

- Ajustes anteriores y aplicados: `storage/analysis/msnr_v28_recovery_20261012/settings_before.json` y `settings_after.json`.
- Estado del motor, configuración, registro y huella del modelo: `storage/analysis/msnr_v28_recovery_20261012/deployment_verification.json`.
- Recarga del motor: `storage/analysis/msnr_v28_recovery_20261012/worker_reload.json`.
- Replay, fuentes y parámetros congelados: `storage/analysis/msnr_v27_m5_reference_20261012/recovery_v28_7d/run.json`.
- Resultados y criterios: `storage/analysis/msnr_v27_m5_reference_20261012/recovery_v28_7d/summary.json` y `trades.csv`.
