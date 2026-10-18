# Malaysian SNR: cantidad de entradas, calidad y WinRate

Revisión del 11 de octubre de 2026. Corte principal de auditoría: **22:03:32 UTC**. Se consultaron logs, auditoría y resultados históricos guardados, sin modificar parámetros ni ejecutar operaciones.

## Conclusión

La prioridad es ampliar las oportunidades mediante activos y escenarios que puedan validarse, conservando confirmación y ejecución exigentes. Los logs recientes no justifican reducir más el cuerpo Fractal ni ampliar otra vez la distancia de entrada. Tampoco acreditan que los cambios recientes hayan mejorado el WinRate: no hay operaciones de la versión actual en el historial consultado.

Configuración persistida: **D1 en sintéticos desactivado, cuerpo Fractal H1 45%, distancia Fractal 0,50 ATR H1**. Versión: `msnr-v2.4-dynamic-fractal-distance`.

## Qué dicen los logs

Se revisaron seis horas de auditoría muestreada: **1.679 eventos de resultado Malaysian SNR**, repartidos entre varias versiones. Para evitar mezclarlas, la versión actual se separó: **92 observaciones entre 21:46:08 y 22:01:06 UTC**, sin señales válidas, con cinco identificadores de setup distintos. La repetición de estados de espera se guarda por muestreo; esos eventos no equivalen al número de ciclos ni al número de oportunidades.

El tramo de texto posterior al cambio y al último reinicio contiene **25 ciclos completos entre 21:49:48 y 22:02:42 UTC**, 575 evaluaciones de los 23 instrumentos seleccionados, cero nuevas órdenes y cero errores. Los logs de texto no etiquetan cada ciclo con su versión; su ventana temporal se contrasta con la auditoría que sí la registra.

De esas evaluaciones, **300 corresponden a los 12 sintéticos**:

| Estado | Evaluaciones | Porcentaje |
|---|---:|---:|
| Sin setup confirmado | 221 | 73,7% |
| Setup vencido | 39 | 13,0% |
| Esperando primer retest o primera vela M15 posterior | 35 | 11,7% |
| Otro bot ocupa el ciclo del activo | 5 | 1,7% |

Estos porcentajes describen lecturas repetidas. **No hay 39 entradas perdidas por vencimiento**: la auditoría identifica dos setups vencidos, de Quasimodo en Boom 1000 y Step 400. Los otros tres identificadores actuales son Quasimodo en Volatility 90 esperando primer retest, y Fractal en Jump 25 y Step 400 esperando datos posteriores a la ruptura H1. En los dos últimos, la ruptura cerró a las 22:00 UTC: al momento de esos registros todavía no había cerrado la primera vela M15 posterior.

Las otras 275 evaluaciones pertenecen a instrumentos tradicionales: 273 están fuera de las ventanas de sesión configuradas y dos bloqueadas por otro bot. Es domingo y el tramo observado está fuera de Londres y Nueva York. Esto no demuestra que eliminar el filtro de sesión vaya a generar entradas rentables, y ese filtro ya se omite en sintéticos. Deriv confirma que sus índices sintéticos operan independientemente de los horarios tradicionales: [especificación del proveedor](https://deriv.com/markets/derived-indices/synthetic-indices).

No aparecen en la versión actual rechazos `ENTRY_TOO_FAR_FROM_LEVEL`, `RETEST_WEAK_RECOVERY`, conflictos D1 o bloqueos por obstáculos. Esto describe esta ventana corta; no permite concluir que esos filtros nunca limiten entradas. `NO_SETUP_CONFIRMED` tampoco distingue si falta un patrón o si una vela quedó debajo del cuerpo mínimo.

## Acciones priorizadas

### 1. Validar nuevos activos sin relajar las confirmaciones

Los siguientes candidatos no están en la lista permitida actual del módulo. El replay causal anterior v2.1, con dos años completos, ofrece una hipótesis para investigarlos:

| Candidato | Trades | WinRate | R por trade | R/trade año 1 / año 2 |
|---|---:|---:|---:|---:|
| Jump 50 Index | 30 | 46,67% | +0,4929 | +0,4060 / +0,5432 |
| Jump 100 Index | 34 | 41,18% | +0,1943 | +0,2228 / +0,1717 |
| Jump 75 Index | 31 | 38,71% | +0,1584 | +0,0012 / +0,2878 |
| Volatility 75 (1s) Index | 24 | 45,83% | +0,4725 | +0,2793 / +0,7944 |

Priorizar Jump 50 y Jump 100 para replay con los ajustes actuales y evaluación en demo. Jump 75 y Volatility 75 (1s) quedan como segunda tanda. Las muestras son pequeñas: por ejemplo, el intervalo Wilson 95% de Jump 50 es aproximadamente 30,2–63,9%. Su WinRate observado no es una predicción.

El replay anterior tenía D1 obligatorio, cuerpo Fractal 55% y distancia Fractal 0,40 ATR; además, sus objetivos del runner no coinciden completamente con el perfil del worker actual. **No valida la versión actual.** Elegir activos usando esta misma tabla también introduce sesgo de selección. Se requiere validación temporal adicional y una muestra nueva, controlando la cantidad de variantes probadas; [Bailey y colaboradores](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf) explican el riesgo de sobreajuste por múltiples pruebas.

No añadir todos los instrumentos por cantidad. Step 500 y Multi Step 2 tuvieron R/trade negativo en el segundo año, pese al agregado positivo. Volatility 75 convencional tampoco equivale a Volatility 75 (1s): el primero tuvo expectativa negativa en ambos años.

### 2. Diagnosticar los rechazos H1 y evaluar continuación Fresh

Desglosar `NO_SETUP_CONFIRMED` una vez por vela cerrada y versión de parámetros: ausencia de barrido estructural, ausencia de ruptura, cuerpo insuficiente, o ausencia de Quasimodo confirmado. Registrar cuerpo observado, mínimo aplicado, ATR, nivel, momento de ruptura y edad del setup. Esto permite descubrir qué ajuste recuperaría patrones completos y qué ajuste solo admitiría velas más débiles.

El escenario 1 de continuación A/V permanece desactivado. Probarlo primero en simulación o modo observación, exigiendo nivel realmente Fresh, vela H1 direccional con cuerpo mínimo 50%, ADX H1 ≥20, retest M15 fuerte, nivel no consumido y espacio al obstáculo opuesto ≥2R. Agrega otra familia de oportunidades, pero el replay anterior no midió este escenario: su efecto sobre WinRate sigue sin acreditarse.

### 3. Priorizar retests oportunos y recuperar eficiencia

La mediana del ciclo es 18,50 s; el percentil 95, 31,75 s; el máximo, 51,06 s. Tres de los 25 ciclos superaron el objetivo de 30 s. Una evaluación que terminó bloqueada en Volatility 90 tardó 22,87 s. **No significa que esperara todo ese tiempo por el candado**: el candado es no bloqueante y el tiempo registrado incluye otros pasos.

El código mantiene el bloqueo del activo durante el análisis y la ejecución. Evaluar separar cálculo de señales y envío: cachear estructura H1 por vela cerrada, revisar confirmación al cierre M15 y serializar la comprobación final de posiciones, deduplicación y órdenes. Invalidar cachés cuando cambian parámetros. Priorizar activos con setup vivo esperando retest. Estas mejoras pueden reducir omisiones técnicas y facilitar un universo mayor; no demuestran por sí mismas un aumento del WinRate. No retirar el bloqueo de posiciones ni la comprobación del precio real de entrada.

## Qué conservar y qué comparar

Conservar confirmación M15 cerrada, límites de penetración e invalidación, distancia sobre la cotización real, obstáculos antes de 2R, deduplicación y política Boom/Crash. No extender de nuevo el retest solo para rescatar setups vencidos: entre sintéticos de v2.1, las entradas de 15–45 minutos tuvieron 30,86% de WinRate y −0,0727 R/trade; las de 60–90 minutos, 28,72% y −0,1252 R/trade. Es evidencia descriptiva, no prueba causal ni recomendación de cambiar ya la ventana.

El rechazo de zona M15 ya está habilitado junto al barrido CRT. Desactivar CRT no agrega automáticamente un gatillo que hoy falte. El agregado sintético v2.1 tenía 30,67% de WinRate, −0,0774 R/trade y factor de beneficio 0,888: un aumento del WinRate aislado no basta para acreditar rentabilidad.

Para elegir el siguiente cambio, comparar pocas variantes predefinidas con la configuración actual. Medir por setup completo de dos piernas: trades ejecutables y cerrados, WinRate de R neto positivo, expectativa neta, factor de beneficio y drawdown, incluyendo costes y restricciones de cartera. Separar oportunidades nuevas y oportunidades sustituidas por ocupación de posiciones. Exigir mejora consistente por ventanas temporales, no solo un agregado favorable, y validación posterior con datos nuevos. Evitar contar cada pierna como una oportunidad distinta.

## Evidencia local

- `storage/analysis/msnr_log_review_20261011/telemetry.json`: auditoría, preferencias, diagnósticos y frecuencias.
- `storage/analysis/msnr_log_review_20261011/cycles.json`: los 25 ciclos de texto analizados.
- `storage/analysis/msnr_log_review_20261011/historical_evidence.json`: subgrupos y candidatos recalculados desde el CSV histórico.
- `MSNR_REPLAY_DOS_ANOS_20261011.md`: metodología y limitaciones del replay anterior.

Los scripts de esta revisión leen la base en modo solo lectura. No conectan con el broker ni alteran la estrategia.
