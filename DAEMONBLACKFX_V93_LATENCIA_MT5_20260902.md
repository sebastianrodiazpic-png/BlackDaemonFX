# DaemonBlackFx v93 — optimización de latencia MT5

## Causa confirmada

Los workers coordinados tenían `auto_export=False`, pero `sync_closed_trades()`
invocaba `export_now()` manualmente en cada pasada del monitor. Con 12 workers y
un intervalo de dos segundos, se reconstruía el mismo XLSX reiteradamente. Esto
produjo ciclos de 10 a 40 minutos y `PermissionError` temporales de openpyxl.

## Correcciones

- Los workers respetan `auto_export=False`; sólo el coordinador escribe el XLSX.
- Sin posiciones abiertas del perfil, el monitor usa una ruta rápida SQLite y
  no consulta MT5 cada dos segundos.
- La autorreparación de posiciones no persistidas se conserva cada 30 segundos.
- Con una posición abierta, break-even, runner, rollover, telemetría y auditoría
  continúan con el intervalo configurado de dos segundos entre símbolos.
- La reconciliación previa al análisis se omite si el perfil no tiene posiciones.
- Sintéticos, Forex y GOLD analizan una sola vez cada vela M5 cerrada. Los
  sintéticos no heredan restricciones horarias de Forex.
- Las lecturas de velas MT5 reintentan hasta tres veces ante fallos transitorios.
- ORB mantiene su scheduler por sesión de Nueva York.

## Persistencia

No se eliminó ninguna escritura SQLite. Se mantienen auditoría de entrada,
snapshots en tiempo real, estado de workers y exportación consolidada desde el
coordinador.
