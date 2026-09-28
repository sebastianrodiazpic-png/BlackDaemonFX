# DaemonBlackFx v113 · análisis externo y ejecución MT5

## Resultado

Las estrategias SMC de sintéticos, GOLD, FOREX y ORB pueden analizar velas y
ticks sin depender de MT5:

- Sintéticos: API WebSocket oficial de Deriv.
- FOREX, GOLD e índices tradicionales: API v20 de OANDA.
- MT5: descubrimiento/nombre del contrato, especificaciones del instrumento,
  cálculo pre-fill, envío de órdenes, posiciones abiertas, SL/TP y cierres.

No se cambiaron las reglas de entrada, H1→M15→M5, frescura M5, riesgo,
R:R, horarios, cuarentenas ni gestión de posiciones.

## Instalación

1. Detenga completamente todos los workers.
2. Copie el código de v113 conservando su `.env`, `storage` y `.venv`.
3. Active el entorno e instale dependencias:

```cmd
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.external.example .env
```

4. Edite `.env` y configure al menos:

```dotenv
DERIV_APP_ID=1089
OANDA_API_TOKEN=REEMPLAZAR
OANDA_ACCOUNT_ID=REEMPLAZAR
OANDA_ENVIRONMENT=practice
DAEMON_MARKET_DATA_MODE=shadow
```

`OANDA_API_TOKEN` es obligatorio para FOREX, GOLD y ORB. El `account_id` se
usa para obtener pricing; si se omite, el proveedor estima el tick con M1.
No incluya ni comparta el `.env` al enviar logs o respaldos.

## Preflight sin órdenes

Con MT5 abierto y conectado:

```cmd
python -m app.main --mode market-data-preflight --market-data-mode external
```

El comando sólo valida catálogo, mapeos, velas M5 cerradas, volumen y ticks.
No construye un ejecutor ni envía órdenes. Debe terminar con `ERROR=0`.

Un nombre de broker que no coincida con Deriv/OANDA debe mapearse en `.env`:

```dotenv
DAEMON_DERIV_SYMBOL_MAP_JSON={"Nombre broker":"R_100"}
DAEMON_OANDA_SYMBOL_MAP_JSON={"Nombre broker":"EUR_USD"}
```

## Despliegue recomendado

### Etapa 1 · sombra, sin ejecución

```cmd
python -m app.main --mode multi-bot-daemon --market-data-mode shadow --interval 30 --position-monitor-interval 2 --risk-percent 1.0 --min-rr 1.5 --dashboard --dashboard-port 8765
```

La fuente externa es la fuente primaria del análisis. MT5 sólo se consulta en
paralelo para comparar los datos; una falla de esa comparación no modifica la
decisión. El resultado se guarda en:

```text
storage/analysis/market_data_shadow.jsonl
```

Genere el resumen así:

```cmd
python -m tools.market_data_shadow_report --file storage/analysis/market_data_shadow.jsonl
```

Mantenga esta etapa al menos 7 sesiones completas e incluya Tokio/Londres,
Nueva York y la ventana ORB. Revise especialmente:

- `ERROR=0` en el preflight.
- Cobertura de velas cerradas comunes.
- Diferencia de cierre p95 igual o inferior a 0,10 del rango mediano.
- Horarios de las velas y señales iguales entre ambos feeds.
- Mapeo exacto del instrumento que finalmente ejecuta MT5.

### Etapa 2 · external en DEMO

Sólo después de aprobar la etapa sombra:

```cmd
python -m app.main --mode multi-bot-daemon --market-data-mode external --execute --interval 30 --position-monitor-interval 2 --risk-percent 1.0 --min-rr 1.5 --dashboard --dashboard-port 8765
```

En modo `external`, una fuente ausente, un mapeo ambiguo o datos OHLC inválidos
producen un error explícito y no provocan fallback silencioso a MT5.

## Caché y workers

- Cada proceso reutiliza ventanas OHLC mayores para solicitudes menores del
  mismo símbolo/timeframe.
- Las fuentes se conectan bajo demanda: un worker FOREX/GOLD no abre un
  WebSocket Deriv que no utiliza.
- `unified-multibot-daemon` comparte un router/caché en un solo proceso.
- `multi-bot-daemon` conserva el aislamiento entre procesos; por ello cada
  worker mantiene su propia caché local.

No se cambió automáticamente el daemon multiproceso por el unificado: esa
decisión afecta aislamiento y tolerancia a fallos y debe medirse en DEMO.

## Volumen y POC

OANDA entrega volumen de ticks y Deriv puede entregar conteo de ticks cuando
la API lo incluye. Esto permite construir filtros de actividad relativa y
aproximaciones de perfil/POC, pero no representa un libro de órdenes
centralizado. En v113 el volumen se normaliza y audita; no se convirtió en un
filtro obligatorio para evitar alterar las estrategias sin backtest.

## Qué falta validar en la instalación real

- Autenticación OANDA y disponibilidad de todos los instrumentos de la cuenta.
- Mapeos de los nombres exactos que entrega su broker MT5.
- Divergencia externa/MT5 durante 7 sesiones completas.
- Latencia y límites de API con todos los workers simultáneos.
- Resultado en DEMO antes de habilitar una cuenta real.

Estas comprobaciones no pueden simularse fielmente fuera de su terminal y no
deben omitirse antes de ejecutar órdenes.
