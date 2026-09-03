# DaemonBlackFx v20 - Posiciones persistentes y dashboard offline

## Objetivo
Permitir que las operaciones registradas como `OPEN` sigan visibles aunque el daemon de trading se haya desconectado de MT5.

## Fuente de verdad
- SQLAlchemy conserva las operaciones abiertas.
- `storage/dashboard/last_state.json` conserva el último snapshot visual del dashboard: monitor, precio conocido, auditoría SMC, gráfico y análisis recientes.
- El snapshot visual es informativo y puede quedar desactualizado mientras MT5 esté desconectado.

## Modo normal

```bash
python -m app.main --mode demo-daemon --execute --interval 30 --risk-percent 1.0 --min-rr 1.5 --dashboard
```

Mientras MT5 está conectado, las posiciones se marcan `EN VIVO`.

## Dashboard sin MT5

Después de detener el daemon puedes levantar sólo la interfaz:

```bash
python -m app.main --mode dashboard-only --dashboard-port 8765
```

Rutas:
- Dashboard: http://127.0.0.1:8765/
- Instrumentos: http://127.0.0.1:8765/instruments
- Cuenta: http://127.0.0.1:8765/account

En este modo:
- No se conecta a MT5.
- No analiza instrumentos.
- No abre ni cierra trades.
- Lee las operaciones `OPEN` de SQLAlchemy.
- Muestra el último precio/gráfico conocido si existe un snapshot previo.
- Cada posición muestra `PERSISTIDA · SIN CONEXIÓN`.
- La validación de salud cambia a `SIN VALIDACIÓN EN VIVO`.

## Reconciliación al volver a conectar
Al iniciar de nuevo `demo-daemon`, DaemonBlackFx reconcilia SQLAlchemy con MT5:
1. Comprueba las posiciones persistidas como `OPEN`.
2. Si una posición ya no existe en MT5 y existe historial de deals, la sincroniza como cerrada.
3. Las posiciones que continúan abiertas vuelven a mostrarse `EN VIVO`.

## Seguridad
Nunca interpretar el precio, R, salud o estructura mostrados en modo offline como información de mercado actual. Son el último estado persistido antes de la desconexión.
