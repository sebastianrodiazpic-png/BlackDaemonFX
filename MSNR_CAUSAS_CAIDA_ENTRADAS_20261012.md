# Malaysian SNR: por qué cayó la frecuencia de entradas

Corte del análisis de logs y journal: 12 de octubre de 2026, 20:43 UTC. Consultas en modo solo lectura; no se modificó la estrategia ni se enviaron órdenes.

La evidencia apunta a cambios acumulados de selección y confirmación. Todavía no se demostró que la reducción de actividad esté compensada por mayor beneficio neto.

## La caída existe en los logs operativos

| Día UTC | Resultados de apertura reportados por el worker |
|---|---:|
| 5 de octubre | 34 |
| 6 de octubre | 39 |
| 7 de octubre | 49 |
| 8 de octubre | 58 |
| 9 de octubre | 36 |
| 10 de octubre | 4 |
| 11 de octubre | 0 |
| 12 de octubre, hasta el corte | 0 |

Los 220 resultados de apertura del 5 al 10 proceden del log dedicado a SNR. Una apertura de dos piernas se cuenta una vez en este log. No se compara directamente ese número con las filas del journal: el journal tiene piernas, sincronizaciones y registros cuyo agrupamiento no coincide exactamente con el contador del log.

## 1. Se restringió el escenario que producía casi todas las operaciones

Entre el 5 y el 10, el journal identifica 416 piernas del worker Malaysian SNR:

- 384 de Continuación: 92,3%.
- 31 de Fractal: 7,5%.
- 1 de Quasimodo: 0,2%.

La versión anterior msnr-v1.0 tenía Continuación habilitada. La configuración de msnr-v2.0-augmented la dejó deshabilitada. Las preferencias 5–8 del 11 de octubre la pusieron en Observación. La preferencia 9 la devolvió a Operar el 12 a las 00:52:22 UTC.

Por eso reducir el cuerpo mínimo Fractal de 55% a 45% no recuperaba el motor principal de volumen. Esa reducción actúa sobre un escenario diferente. Aunque Continuación ya está en Operar, ahora debe completar las nuevas reglas de retest y ejecución.

Para identificar la versión histórica se contrastó la metadata: 356 piernas antiguas tienen la columna genérica smc-v1, pero su metadata identifica msnr-v1.0, estrategia MALAYSIAN_SNR y escenarios SNR. No se las atribuyó a otro worker por esa etiqueta genérica.

## 2. La lista permitida excluye varios instrumentos muy activos

SNR admite actualmente 23 activos: 12 sintéticos, 8 forex, 2 metales y 1 índice tradicional. No admite criptomonedas. La lista adicional está vacía, aunque su modo figura como Operar.

Entre los instrumentos que operaron antes y hoy no están permitidos se encuentran Crash 500, Step 500, Volatility 10, Volatility 25, Volatility 75, Boom 500, Boom 600 y BTCUSD. US SP 500 y US Tech 100 también quedaron fuera.

Al agrupar el journal por parent_execution_key, o por la base de execution_key cuando falta ese campo, aparecen 234 grupos para esa ventana. De ellos, 144 pertenecen a instrumentos hoy excluidos. Es una medida de exposición histórica a la poda, no una atribución causal de un 61,5% de caída ni un contador exacto de oportunidades independientes.

En sintéticos, 90 de 135 grupos consultados pertenecen a instrumentos excluidos. Los 18 grupos de cripto son BTCUSD, también excluido. En forex, los 10 grupos consultados son EURUSD, GBPUSD y USDJPY: estos tres siguen permitidos.

La cartera del replay tenía 60 instrumentos; los logs operativos de la semana no muestran que el worker escaneara los 60 simultáneamente. Sus ciclos variaron entre 7 y 22 instrumentos antes de la selección actual. El efecto de la poda viene de qué instrumentos se retiraron, no de afirmar que el escáner bajó de 60 a 23.

## 3. Cambió la secuencia exigida para entrar

El código anterior seleccionaba velas por hora de apertura menor o igual al momento de análisis. Eso podía incluir H1 y M15 todavía en formación. El Fractal inicial podía construir una señal directamente desde esa geometría; otros escenarios buscaban contacto en las últimas velas M15 sin la reconstrucción temporal actual.

Ahora se exige:

1. Ruptura H1 completamente cerrada.
2. Retest posterior al cierre de esa ruptura.
3. Primera visita controlada, sin invalidación de estructura.
4. Recuperación direccional en un máximo de 45 minutos, con cuerpo mínimo de recuperación de 35%.
5. Confirmación dentro de una ventana total de 90 minutos.
6. Distancia permitida al nivel y espacio suficiente antes del obstáculo para alcanzar al menos 2R.
7. Cotización ejecutable y deduplicación del episodio H1.

Esto modifica mucho más que el porcentaje del cuerpo Fractal. Una secuencia puede tener patrón H1 y, aun así, no producir una entrada.

La nueva auditoría de candidatos registra 32 episodios sintéticos en este corte: cero confirmados y cero ejecutados. 28 tienen como estado final Vencido. Sus primeros motivos incluían espera de retest, dirección no permitida y nivel consumido: Vencido no acredita que fueran 28 operaciones rentables perdidas. La auditoría es nueva y no representa siete días completos de cobertura efectiva.

La corrección temporal conserva información disponible en cada momento. MT5 documenta que el tiempo de una barra es su apertura, no su cierre: [documentación oficial](https://www.mql5.com/en/docs/python_metatrader5/mt5copyratesrange_py).

## 4. Forex tiene una selección macro más exigente

La dirección D1 obligatoria en sintéticos está desactivada. Forex conserva el filtro macro y ahora usa estructura D1: pivotes y ruptura confirmada, no solo el color de la vela diaria.

Una estructura D1 neutral bloquea la entrada incluso si existe una dirección intradía. El apoyo H4 está en Observación y no abre esa alternativa. Forex también conserva las ventanas de 07:00–11:00 y 12:30–17:00 UTC, además de controles de rollover y spread.

El log del 12 contiene 1.306 lecturas de estructura macro neutral/no disponible y 775 de conflicto D1. Son revisiones repetidas, no 2.081 trades independientes descartados. Las 15.457 lecturas fuera de sesión también incluyen los otros instrumentos tradicionales; no son exclusivamente forex.

## 5. La expansión M5 todavía no aporta órdenes

M5 y H4 permanecen en Observación. Su implementación permite evaluarlas, pero no las convierte en rutas operativas nuevas.

En el piloto offline del 4 al 11 de octubre, M15 produjo 10 operaciones cerradas para los 23 activos y M15+M5 produjo 29. El WinRate estimado subió de 10% a 24,1%, pero la expectativa de M15+M5 fue −0,303 R por operación. La muestra es corta, usa spread aproximado y no valida activar M5 de forma general.

## 6. Hubo señales hoy que no se ejecutaron por modo o IA

- Step Index 200: 28 lecturas MSNR_SHADOW_SIGNAL desde las 00:00 UTC, antes de poner Continuación en Operar a las 00:52. No son 28 señales independientes.
- Boom 300: 29 lecturas rechazadas por PROBABILITY_BELOW_THRESHOLD, con últimos registros a las 04:44 UTC.
- A las 18:33 UTC, la preferencia 10 permitió observar el modelo incompatible sin su veto solo en DEMO.

No se atribuyen esas lecturas de madrugada a las variantes M5/H4 introducidas más tarde. Cambiar un modo después no permite ejecutar retrospectivamente una confirmación ya vencida.

## Qué implica para el objetivo de ganar más preservando actividad

Se restringieron activos, escenarios y confirmaciones en cambios acumulados. Relajar después el cuerpo Fractal o retirar el veto D1 sintético no revierte todas esas restricciones. Las correcciones de temporalidad eran necesarias para medir y ejecutar coherentemente, pero una poda o un filtro adicional necesita evidencia de beneficio frente al volumen que sacrifica.

El CSV que respaldó la selección de 23 reutiliza el histórico para elegir la cartera y presenta limitaciones metodológicas ya documentadas. No certifica que excluir los otros 37 aumente el beneficio operativo. Seleccionar usando el resultado del mismo backtest puede sobreajustar la cartera: [Bailey y colaboradores](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf).

La suma de net_pnl de las piernas SNR abiertas del 5 al 9 en el journal es +142,26; al incluir las del 10, el agregado es −66,47. Son cohortes por fecha de apertura, no el cambio diario del saldo ni una auditoría de todos los costes del broker. Tener más aperturas tampoco acredita por sí mismo una expectativa positiva.

El siguiente ajuste debe comparar escenarios y familias por separado: conservar Continuación como fuente de oportunidades; revisar selectivamente los activos excluidos, incluyendo cripto; evaluar M5 temprano dentro del mismo episodio; y contrastar qué bloqueos evitan pérdidas y cuáles quitan ganancias. La decisión debe medir beneficio neto por período, expectativa, pérdidas y frecuencia preservada. No se propone restaurar velas abiertas ni reactivar toda la cartera usando solo una semana favorable.

## Evidencia reproducible

Directorio: storage/analysis/msnr_trade_drop_20261012.

- evidence.json: comparación de log, journal, preferencias y candidatos.
- episodes.json: grupos del journal, metadata y exposición a activos excluidos.
- ai_timeline.json: fechas y activos de lecturas en observación o rechazadas por IA.

Los scripts de esta revisión no construyen ejecutores, no conectan al broker y no actualizan preferencias.
