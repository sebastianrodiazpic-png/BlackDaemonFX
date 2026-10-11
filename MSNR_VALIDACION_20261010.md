# Validación de Malaysia / Malaysian SNR — 10 de octubre de 2026

**Veredicto: se corrigieron fallos de causalidad y selección, pero no hay evidencia suficiente para certificar rentabilidad ni identificar entradas con una probabilidad de éxito validada.** Pasar las pruebas de software no demuestra una ventaja de mercado.

## Evidencia comprobada

El replay heredado de 180 días contiene 1.368 operaciones: 33,55% de resultados positivos, −9,915R, expectativa −0,0072R/trade y factor de beneficio 0,989. El intervalo descriptivo del 95% para la expectativa es [−0,0836; +0,0691]R. R representa el riesgo inicial total de la operación, con ambas piernas ponderadas. No hay una ventaja positiva demostrada.

Los mejores activos del informe previo tampoco tienen intervalos claramente positivos:

| Activo | Operaciones | R/trade | Intervalo aproximado 95% |
|---|---:|---:|---|
| Boom 1000 | 71 | +0,2963 | [−0,0466; +0,6391] |
| Crash 1000 | 84 | re+0,1712 | [−0,1578; +0,5002] |
| Volatility 25 | 138 | +0,1148 | [−0,1323; +0,3620] |
| Volatility 10 | 150 | +0,0946 | [−0,1438; +0,3329] |
| XAUUSD | 64 | +0,0888 | [−0,2553; +0,4329] |

Estos intervalos asumen independencia y son orientativos. La selección de activos ya utilizó el histórico completo; separar ahora el último 30% no lo convierte en una prueba independiente. En ese segmento reciente, Volatility 10 registra −0,401R/trade y Volatility 25 −0,1055R/trade. Una allowlist histórica no equivale a una lista de oportunidades actuales.

Los grandes resultados del replay de 207.520 trades no representan fielmente la ejecución actual. Ese detector utiliza el cierre H1 para generar una señal con la hora de apertura H1, y su simulador comienza a evaluar M15 desde esa misma apertura. También presupone entradas en un nivel previo sin comprobar un fill posterior al conocimiento de la ruptura. Esto introduce información que todavía no estaba disponible en el instante simulado.

El entrenamiento de IA calibra probabilidades sobre `X_test/y_test` y luego evalúa ese mismo conjunto. Además, construye varias características manualmente en lugar de reproducir las observaciones de entrada del motor actual. Los porcentajes filtrados próximos a 70% no acreditan éxito fuera de muestra para la versión corregida. No se entrenaron ni reemplazaron modelos durante esta auditoría.

## Correcciones realizadas

- H1, M15 y D1 deben estar cerradas según su hora de apertura y duración. Se normaliza UTC, se comprueba antigüedad y se rechazan datos corruptos o duplicados.
- La ausencia de D1 no se transforma en un sesgo comprador. Una D1 neutral bloquea la selección. El filtro sigue siendo un **proxy de dirección de la vela diaria**, no la narrativa completa de niveles D1/W1.
- Los niveles A/V se sitúan en el cierre del cuerpo. Las mechas conservan su papel de límite estructural. Fresh exige ausencia de contacto real entre formación y ruptura.
- El retest y el cierre direccional M15 deben ocurrir después del cierre de la ruptura H1. Se exige intersección con la zona y se rechazan entradas alejadas.
- Quasimodo utiliza swings alternados confirmados, barrido del extremo y un quiebre posterior por cierre. El patrón de tres velas continúa identificado separadamente como fractal.
- Se comprueba el lado correcto del stop, el riesgo firmado y espacio hasta el obstáculo para alcanzar al menos 2R. La corredora respeta el techo estructural también cuando cambia la cotización de ejecución.
- La hora de la señal queda fijada al cierre de confirmación M15; revisar la misma vela nuevamente no crea una nueva identidad temporal.
- Los valores de confirmación 85/90 se identifican como puntuaciones heurísticas. `success_probability` permanece sin validar; no se los presenta como porcentajes de éxito.
- El replay conserva el stop estructural, incorpora spread en la salida de ventas, respeta gaps adversos y prioriza el stop en velas ambiguas, incluido el break-even de la corredora.

## Cómo seleccionar las próximas oportunidades

Exigir conjuntamente activo permitido, dirección autorizada, datos recientes, sesgo D1 alineado, ruptura cerrada, retest posterior con recuperación M15, entrada cercana y espacio libre suficiente hasta el objetivo. En continuación, exigir un nivel fresh. Si falta una condición, esperar. El escenario de continuación conserva su desactivación por defecto.

Boom 1000 y Crash 1000 son candidatos para investigar en demo por sus resultados históricos relativos, **no operaciones recomendadas ni activos con ventaja probada**. Mantener BUY en Boom y SELL en Crash según la política existente. No aumentar el riesgo basándose en el score, en una tabla de ganadores ni en la IA heredada.

Para atribuir probabilidades a entradas futuras hace falta recoger señales de esta versión con sus características reales, costos y resultados; separar cronológicamente entrenamiento, calibración y prueba, purgar trades que atraviesen las fronteras y medir expectativa neta y calibración en datos nuevos. También falta contrastar el proxy D1 con velas diarias nativas y validar la gestión completa con ejecución demo.

## Alcance y resultados reproducibles

La auditoría offline de cinco activos y 30 días produjo **4 operaciones, 0 ganadoras y −4R**: dos en Boom 1000 y dos en Crash 1000. Step Index, XAUUSD y BTCUSD no generaron entradas admitidas. La muestra es demasiado pequeña para medir ventaja o mejora. No se ampliaron condiciones para forzar operaciones.

Los resultados están en [el reporte de replay](storage/analysis/msnr_causal_audit/report.md), con [métricas](storage/analysis/msnr_causal_audit/metrics.json) y [operaciones](storage/analysis/msnr_causal_audit/trades.csv). Se utilizaron archivos locales que terminan entre el 2 y el 4 de octubre; no son cotizaciones del día 10. El D1 se reconstruye con cortes UTC y el spread es estimado. No incluye comisiones ni swaps por defecto, ni límites conjuntos de cartera. La muestra reutiliza datos previos y no demuestra mejora fuera de muestra.

**61 pruebas pasaron**, incluyendo causalidad, entradas confirmadas reales con datos controlados, aislamiento de velas abiertas, obstáculos con cambios de cotización, riesgo compartido, break-even, spread y gestión de corredoras. Los archivos de integración contienen también comprobaciones de presencia del modelo y perfiles guardados; estas no certifican la calidad predictiva del modelo.

No se enviaron órdenes ni se reiniciaron procesos. Los cambios estarán disponibles al cargar nuevamente el código. Esta revisión no certifica el contenido de los 22 videos ni las citas del texto pegado: sus afirmaciones se contrastaron con el código y los datos disponibles.

Referencias oficiales: [MT5 documenta que el tiempo de las barras es su apertura en UTC](https://www.mql5.com/en/docs/python_metatrader5/mt5copyratesfrom_py); [Deriv explica que el rendimiento pasado no predice resultados futuros](https://deriv.com/terms-and-conditions/risk-disclosure).
