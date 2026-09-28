# Compras Volatility en premium — auditoría y corrección

Se consultó SQLite en modo lectura y los gráficos congelados de entrada.
Operaciones del 14-09-2026 a las 18:25 UTC, segunda pierna:
- V15 (1s), trade 170: BUY 13855.396.
- V50 (1s), trade 171: BUY 235656.62.

Ambas guardaron H4/H1 BULLISH, M15 choch_bullish, zona histórica
del order block discount y confirmación STRICT_CONFIRMED (13/13).
El filtro anterior evaluaba la ubicación del OB cuando se formó;
no comprobaba el precio de ejecución contra el rango actual de H4/M15/M5.

Reproducción con las últimas 100 velas cerradas archivadas:

| Instrumento | Precio de entrada | Equilibrio H4 | Equilibrio M15 | Equilibrio M5 | Resultado nuevo |
| --- | ---: | ---: | ---: | ---: | --- |
| V15 (1s) | 13855.396 | 13501.3275 | 13820.7285 | 13841.088 | Compra bloqueada en los tres marcos |
| V50 (1s) | 235656.62 | 227058.825 | 236830.61 | 234098.35 | Compra bloqueada en H4 y M5 |

M15 de V50 queda discount según este rango: no se afirma equivalencia
con los rangos estructurales del indicador de las capturas.

Cambios:
- LiveTradingConfig.volatility_entry_location_enabled=True.
- Aplicable a símbolos Volatility, en el pipeline SMC.
- BUY requiere discount; SELL requiere premium en H4, M15 y M5.
- Rango: máximos/mínimos de las últimas 100 velas cerradas
  (PipelineConfig.premium_discount_lookback).
- Sin historial completo, sin rango válido, en equilibrio o fuera del rango:
  no se autoriza la entrada.
- Comprobación al validar la señal y nuevamente con ask/bid antes de ejecutar.
- Diagnóstico ENTRY_LOCATION_BLOCKED con marcos, límites, zona y razones;
  evidencia persistida en metadatos y auditoría de entrada.
- Tendencia compartida: último máximo y mínimo estructural, sin prioridad
  alcista por coexistencia de HH/HL antiguos con LH/LL recientes.
  Estructura mixta => NEUTRAL; un BOS interno no reemplaza ese estado.
  Esta corrección de tendencia beneficia a todos los consumidores SMC.

No se transforma una compra rechazada en venta: la venta necesita contexto
direccional y setup/confirmación propios. Exigir los tres marcos puede reducir
la frecuencia, especialmente cuando sus rangos no coinciden.

Validación: pruebas sintéticas de ambos lados, precio desplazado por spread,
historial insuficiente, estructura mixta y análisis multitemporal completo.
La reproducción archivada prueba el bloqueo por ubicación; no prueba que una
venta alternativa habría sido válida ni rentable. La reconstrucción de swings
con el fragmento archivado no equivale a recalcular las 500 velas originales.

El daemon no se reinició ni se enviaron órdenes durante esta tarea.
Debe recargar el código para aplicar los cambios.
