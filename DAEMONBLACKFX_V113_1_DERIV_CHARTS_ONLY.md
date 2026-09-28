# DaemonBlackFx v113.1 · Deriv Charts/API + MT5 DEMO

## Arquitectura

- Deriv WebSocket público: velas y ticks de análisis para SMC sintéticos,
  FOREX, GOLD, ORB e IDX Open.
- MT5: catálogo del broker, especificaciones, cuenta DEMO, precio pre-fill,
  volumen, envío de órdenes, posiciones, SL/TP, break-even y cierres.
- OANDA fue retirado del flujo. No se solicitan token ni account ID de OANDA.

No se modificaron confirmaciones, horarios, score, estructura H1→M15→M5,
frescura M5, riesgo de 1%, R:R ni políticas de cada familia.

## ¿Necesito registrarme?

Para los datos públicos de mercado no necesita token, PAT ni una aplicación
Deriv registrada. Se utiliza:

```text
wss://api.derivws.com/trading/v1/options/ws/public
```

Sí necesita conservar:

1. Su cuenta Deriv MT5 DEMO.
2. El terminal MT5 abierto y conectado a esa cuenta.
3. `websocket-client`, instalado mediante `requirements.txt`.

Si en el futuro se agregan endpoints de cuenta o trading de Options, entonces
sí correspondería autenticación; v113.1 no usa esos endpoints y Deriv API nunca
envía órdenes.

## Instalación

Detenga el coordinador y todos los workers. Descomprima v113.1 conservando su
`.env`, `storage` y `.venv`. Después:

```cmd
cd /d C:\TradingBoot\smc_synthetic_bot
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

Si no existe `.env`:

```cmd
if not exist .env copy .env.deriv.example .env
```

Configuración mínima:

```dotenv
DAEMON_MARKET_DATA_PROVIDER=deriv
DAEMON_MARKET_DATA_MODE=shadow
DERIV_WEBSOCKET_ENDPOINT=wss://api.derivws.com/trading/v1/options/ws/public
DAEMON_DERIV_SYMBOL_MAP_JSON={}
```

## Preflight obligatorio

Con MT5 conectado a DEMO:

```cmd
python -m app.main --mode market-data-preflight --market-data-mode external
```

Comprueba para cada instrumento:

- equivalencia MT5↔Deriv única;
- histórico H1, M15, M5 y M1;
- existencia de velas cerradas;
- tick Deriv y tick MT5;
- diferencia relativa de precio inferior al 5% por defecto.

El preflight no construye ni utiliza un ejecutor de órdenes. Si un símbolo no
es resoluble, agregue únicamente su equivalencia confirmada:

```dotenv
DAEMON_DERIV_SYMBOL_MAP_JSON={"Nombre exacto MT5":"codigo_active_symbols"}
```

Nunca adivine un código. Debe provenir del inventario `active_symbols`.

## Ejecución solicitada en DEMO

Una vez que el preflight termine con `ERROR=0`:

```cmd
python -m app.main --mode multi-bot-daemon --market-data-mode shadow --execute --interval 30 --position-monitor-interval 2 --risk-percent 1.0 --min-rr 1.5 --dashboard --dashboard-port 8765
```

Cada worker vuelve a comprobar antes de operar:

1. que MT5 esté conectado a una cuenta DEMO;
2. que sus instrumentos tengan datos Deriv válidos;
3. que Deriv y MT5 no representen precios materialmente incompatibles.

Además, antes de cada entrada, el motor vuelve a leer el precio ejecutable de
MT5 y mantiene la protección existente por drift respecto de la señal.

`shadow --execute` significa que Deriv decide el análisis y MT5 se usa como
comparación y ejecutor. No significa que MT5 vuelva a aportar las velas de la
estrategia.

## Auditoría

Las comparaciones se guardan en:

```text
storage/analysis/market_data_shadow.jsonl
```

El reporte puede ejecutarse mientras el daemon está activo:

```cmd
python -m tools.market_data_shadow_report --file storage/analysis/market_data_shadow.jsonl
```

Si aún no existe el archivo, v113.1 informa que no hay comparaciones en vez de
producir `FileNotFoundError`.

## Límites conocidos

- Deriv Charts/API y Deriv MT5 pueden tener catálogos o precios diferentes.
- Un instrumento presente en MT5 pero ausente de `active_symbols` queda
  bloqueado; no existe fallback silencioso.
- El volumen disponible es actividad/ticks, no volumen bursátil centralizado.
- El modo multiproceso conserva una caché por worker. El modo unificado puede
  compartir caché, pero continúa siendo experimental por aislamiento de fallos.
