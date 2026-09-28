# Filtros de entrada SMC — 2026-09-22

Alcance: toda señal SMC ejecutada por el motor compartido (Forex, Gold y
sintéticos). ORB y GOLD_QUARTERS conservan sus reglas propias. No se modifican
SL/TP ni gestión de posiciones abiertas.

## Espacio antes del primer obstáculo

Antes de enviar órdenes se compara cada TP planificado con los obstáculos M15
capturados por el análisis: OB contrario no invalidado por cierre y extremo del
rango M15. Se utiliza una cotización ejecutable nueva (ask en compra, bid en venta)
y el SL normalizado. Un obstáculo antes de 1R rechaza toda la entrada, incluidos
ambos tramos cuando el plan es dividido. El umbral es configurable mediante
`smc_obstacle_min_distance_r` (1.0). No se acorta el TP para aprobar una entrada.

GBPCAD: entrada planificada 1.87555, SL 1.878, demanda 1.87351–1.87378:
distancia al primer borde 0.72245R, rechazo `SMC_OBSTACLE_BEFORE_MIN_R`.
Obstáculos posteriores a 1R siguen registrados, pero no bloquean por esta regla.
El detector no replica todas las zonas de LuxAlgo ni todos los equilibrios M5.

## Vigencia M5 al ejecutar

Se descargan nuevamente 350 velas M5, se excluyen las abiertas y se recalcula el
pipeline de estructura sin reutilizar la caché del análisis. La confirmación debe
existir y no tener más de una vela cerrada posterior (configurable mediante
`smc_execution_max_later_m5_bars`). También se comprueba antigüedad por reloj,
para evitar aceptar huecos de datos como si fueran velas consecutivas.

Se rechaza un BOS/CHoCH contrario posterior a la confirmación, un cierre posterior
o precio ejecutable que atraviese su extremo adverso (mínimo para compras, máximo
para ventas), feed atrasado, datos faltantes, TP ya alcanzado o desplazamiento
de precio que incumpla el límite existente. No se exige otro patrón completo:
se comprueba que la confirmación previamente aprobada siga vigente.

## Auditoría y activación

Evento `SMC_ENTRY_PREFLIGHT`: motivo, decisión, cotización, vela confirmatoria,
última vela cerrada, obstáculo más cercano y distancias por tramo. Las entradas
aceptadas guardan `entry_preflight` en sus metadatos. Los rechazos usan
`SMC_ENTRY_PREFLIGHT_BLOCKED`. Estos datos no se incorporan automáticamente como
nuevas variables del modelo de metaetiquetado.

Se requiere reiniciar los workers SMC para cargar el cambio. No se reiniciaron
servicios ni se enviaron órdenes durante su implementación. Los controles reducen
entradas tardías o con poco espacio; no garantizan evitar SL.

Pruebas: tests/test_smc_entry_preflight.py y regresiones de obstáculos, política
ORB y riesgo/secuencia SMC. Se verifican ambos sentidos, caso GBPCAD, datos
faltantes, velas abiertas, señales antiguas y conservación de la auditoría.
