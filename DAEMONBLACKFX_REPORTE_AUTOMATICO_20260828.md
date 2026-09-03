# DaemonBlackFx - Reporte automático explicable

## Objetivo
El daemon genera y actualiza automáticamente `storage/exports/deriv_demo_trading_report.xlsx` mediante `TradeReportingService(auto_export=True)` después de los eventos relevantes del ciclo de vida de las operaciones.

## Hoja Trades
Cada trade incorpora columnas legibles en español:
- motivo_entrada_es
- decision_entrada_es
- porcentaje_confirmaciones
- confirmaciones_aprobadas / confirmaciones_totales
- score_calidad / grado_calidad
- confirmaciones_cumplidas_es
- confirmaciones_faltantes_es
- condiciones_criticas_faltantes_es
- modalidad_ejecucion_es
- pierna_operacion
- confirmacion_armonica_es
- divergencia_es
- clasificacion_cierre_es
- resultado_monetario_es

El LiveTradingEngine persiste en los metadatos del lifecycle la evidencia de la decisión: score, porcentaje de confirmación, confirmaciones aprobadas/faltantes, fallos críticos, divergencia, patrón armónico, tendencia H1, estructura M15 y zona Premium/Discount.

## Clasificación de cierres
- TP1: primera pierna/objetivo cercano a 1R.
- TP2: runner o entrada única que alcanza aproximadamente 2R.
- STOP LOSS: cierre cercano a -1R.
- PUNTO DE EQUILIBRIO / OTRO: cierre cercano a 0R.
- EMERGENCIA / NO CONTABILIZAR: cierres provocados por protecciones de riesgo.

## Hoja Summary
Se genera automáticamente un dashboard con:
- número de trades ganadores;
- número de trades perdedores;
- porcentaje ganador;
- porcentaje perdedor;
- ganancia neta total;
- pérdida neta total;
- gráfico circular de TP1, TP2, Stop Loss y Punto de equilibrio/Otros.

Las métricas son calculadas por el propio daemon durante cada exportación; no dependen de recálculo de fórmulas por Excel.

## Ruta DEMO
`storage/exports/deriv_demo_trading_report.xlsx`

No se requiere cambiar el comando normal de ejecución del daemon.
