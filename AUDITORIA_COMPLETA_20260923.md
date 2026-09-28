# Auditoría completa de aprendizaje y variantes — 23/09/2026

## Cambios implementados

1. Spread: MetaEtiquetado utiliza bid/ask del ejecutor MT5, fuente y fechas. Una cotización ausente, inválida o antigua queda desconocida. El adaptador MT5 tampoco inventa una fecha actual cuando el tick no contiene timestamp.
2. Persistencia posterior al fill: RR planificado/ejecutado, riesgo posterior y tiempos se fusionan con los detalles de SQLite después del callback de ejecución. Se preservan los datos del monitor. Se cubren callback habitual, recuperación defensiva y ruta sin lifecycle manager. Los fallos de persistencia generan auditoría; no autorizan repetir la orden.
3. Indicadores: ATR y ADX de 14 periodos con suavizado Wilder y semilla SMA. El calentamiento permanece ausente. El pipeline los añade después de sus decisiones; SMC captura los valores de la vela M5 confirmada. Para estrategias con indicadores incompletos se consulta un máximo de 100 velas del proveedor primario y se recorta hasta la confirmación cerrada. No usa velas posteriores. No se añaden requisitos de entrada.
4. Tiempos: la captura guarda apertura/cierre de confirmación y detección. Las features separan edad desde apertura, demora desde cierre a evaluación y procesamiento desde detección. El fill añade envío, retorno y fecha del broker cuando existe. round_trip_seconds mide la llamada de ejecución, que en la ruta lifecycle incluye el callback de persistencia; no se presenta como latencia pura de red.
5. Esquema meta-features-v3 / entry-learning-v3: el vector cambió para evitar interpretar edad de vela como latencia. Los modelos con nombres/dimensiones anteriores se descartan como incompatibles; las capturas anteriores permanecen en el historial pero no se mezclan automáticamente con las nuevas. No se fabrican features antiguas ni se promocionan modelos.
6. Setups únicos: identidad por instrumento, dirección, fecha de setup y límites de OB dentro del worker. Se conserva primera detección, formación, última evaluación, primera expiración, tiempos de etapas, edad de señal y secuencia de cambios. La primera condición favorable de cada variante congela plan, evidencia y cotización MT5. Los días se conservan en storage/runtime/smc_trial/history.
7. Resultados reales: el informe de aprendizaje compara cohortes de setups totalmente cerrados, agrupando los tramos por parent_execution_key. Usa PnL neto y riesgo monetario; prefiere riesgo posterior al fill cuando está disponible. No mezcla operaciones abiertas ni resultados ausentes. La evidencia de variantes debe haber sido capturada antes de entrar. Un subconjunto de trades ejecutados no demuestra el resultado de trades nunca ejecutados.
8. Replay automático en sombra: una vez por hora se comparan los planes congelados con velas M5 cerradas de MT5, mediante el proveedor de referencia, sin alterar el análisis primario Deriv. Mantiene SL/TP, utiliza la cotización ejecutable capturada para entrada y spread histórico por vela para aproximar ASK en ventas. Identifica falta de plan/cotización, historia incompleta, vela de entrada ambigua y toque de ambos objetivos. No convierte esos casos en ganancias o pérdidas. Los resultados terminales se conservan por huella del candidato aunque desaparezcan del historial reciente del broker.
9. Dashboard: muestra setups únicos y sus fechas, replays cerrados/pendientes/excluidos por variante, R bruto de simulaciones y comparación de R neto de operaciones reales. Los informes indican fecha, vigencia (más de dos horas = antiguo) y compatibilidad de esquema. La tarea de auditoría del worker puede actualizarse en el monitor aunque no esté analizando entradas; un worker detenido seguirá mostrándose con informe antiguo.

## Qué significa la comparación

El replay es condicional y exploratorio: superar una variante de confirmación no asegura superar todos los controles de ejecución. Requiere un plan causal completo; si el candidato rechazado no tenía TP/SL definidos, se muestra MISSING_CAUSAL_PLAN en lugar de inventarlos. Los planes históricos anteriores a esta captura no se reconstruyen retrospectivamente.

Los replays usan hasta 2.000 velas por instrumento y actualización, con caché durante esa actualización. Los saltos del historial se excluyen de conclusiones. La apertura parcial de la primera vela se trata conservadoramente: si una barrera pudo tocarse antes de la observación, el resultado es ambiguo. El spread por vela es una aproximación, no ticks ASK completos. No modela comisión, swap ni slippage de salida; por ello sus R son brutos, no expectativa neta demostrada.

Las comparaciones emparejadas solo utilizan setups con baseline y variante cerrados. Se conserva el resultado y número de pares; la promoción sigue deshabilitada. Los resultados en sombra no son etiquetas de entrenamiento ni órdenes reales.

## Contrato estratégico conservado

H1 define premium/discount; M15 aporta el setup/Order Block y M5 la confirmación favorable. Este cambio no flexibiliza esas condiciones ni modifica objetivos, SL/TP, horarios ni políticas de salida de ORB, Forex o GOLD. No garantiza más entradas: mejora la evidencia para decidir cambios posteriores.

## Validación y activación

115 pruebas aprobadas: persistencia SQLite tras fill, indicadores causales/calientamiento, tiempos separados, cotización MT5, modelos, agrupación de tramos, captura inmutable, resultados terminales, ambigüedad e historia incompleta, más regresiones SMC/ORB/Forex/GOLD. Sintaxis de JavaScript del dashboard validada con Node.

Los cambios están en código y requieren reiniciar los workers y el dashboard para quedar activos. Esta tarea no reinició procesos, no envió órdenes y no modificó registros históricos de la base operativa.
