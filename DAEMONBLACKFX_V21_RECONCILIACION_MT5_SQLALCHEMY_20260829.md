# DaemonBlackFx v21 - Reconciliación bidireccional MT5 / SQLAlchemy

## Problema corregido
La v20 conservaba en SQLAlchemy las posiciones que el daemon ya conocía, pero al arrancar sólo reconciliaba SQLite -> MT5. Por eso una posición que seguía abierta en MetaTrader 5 pero no existía en la base local no aparecía en el dashboard.

## Nuevo flujo al arrancar
1. Conecta MT5 y valida la cuenta DEMO.
2. Lee todas las posiciones abiertas con `positions_get()`.
3. Compara cada `position_ticket` contra SQLAlchemy.
4. Si la posición tiene el `magic` de DaemonBlackFx (`26082026`), se recupera como `source=DEMO` y vuelve a ser administrada por el daemon.
5. Si pertenece a otro magic/manual, se persiste como `source=MT5_EXTERNAL` únicamente para visualización. El daemon no modifica su SL/TP ni la cierra.
6. Luego se ejecuta la reconciliación normal de cierres SQLite -> historial MT5.

## Datos recuperados
- ticket de posición
- símbolo
- BUY/SELL
- fecha/hora de apertura
- precio de entrada
- SL y TP actuales
- volumen
- precio actual al importar
- profit flotante al importar
- swap
- magic y comentario MT5
- riesgo monetario y porcentaje cuando pueden calcularse
- RR planificado cuando existen SL y TP

## TP1 / RUNNER / SINGLE
Cuando el comentario MT5 contiene `TP1`, `RUNNER` o `SINGLE`, la posición recuperada conserva ese rol en los metadatos. Esto protege la lógica de Break Even y de gestión de piernas.

## Dashboard
El panel de posiciones abiertas ahora incluye:
- posiciones `DEMO`: `GESTIONADA POR DAEMON`;
- posiciones `MT5_EXTERNAL`: `MT5 EXTERNA · SOLO VISUALIZACIÓN`.

Las externas se muestran para auditoría, pero nunca son adoptadas por la gestión automática.

## Idempotencia
La importación usa `broker_position_ticket` / `execution_key`, por lo que reiniciar el daemon no duplica una posición ya persistida.

## Validación
Suite ejecutable en Linux: 192 pruebas aprobadas.
Los 8 módulos omitidos requieren la librería nativa MetaTrader5 en Windows.
