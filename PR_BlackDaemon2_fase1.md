# Fase 1: ICT sin vela en formación, ORB solo XAUUSD SWEEP y selección alineada

## Qué cambia

- **ICT evalúa solo velas cerradas (bug de paridad live/replay).** `closed_candles_only()` en `strategy/ict/ict_strategy.py` exige apertura + duración ≤ now en M15/H1/H4. Antes el filtro era apertura ≤ now, así que la vela en formación de MT5 se usaba como `last_candle`. Se pide una vela extra y se recorta tras filtrar, para que la ventana de indicadores sea la misma que en el replay.
- **Fase 1 ICT** (`strategy/ict/config.py`, v2): sin NY Killzone ni London Close, Silver Bullet sin la ventana 10-11 NY y exclusión de Step Index, Jump 25, Volatility 25 y XAGUSD. Motivo: expectativa negativa en ambas mitades del replay fiel 365d.
- **ORB SWEEP** (`orb-ny-v5-sweep`): barrido fuera del rango más MSS M5, réplica de `tools/replay_orb_nunez_2y.py`. Solo XAUUSD opera; el resto queda con `allowed_modes=[]`.
- **MSNR C2**: ADX ≥ 30 y tope SL/ATR (1,2 en FX/metales, 1,5 en el resto), activa por defecto (`DAEMONBLACKFX_MSNR_C2`), a 0,5× de riesgo (`DAEMONBLACKFX_MSNR_RISK_MULT`).
- **Selección alineada con la Fase 1**: `DEFAULT_PRIORITIZED_SYMBOLS`, `PRUNED_ASSET_UNIVERSE`, tiers Tri-Motor, listas ORB y los `*_PRUNED_INFO` del dashboard.

## Por qué

Comparación señal a señal de la demo (15-18 oct, 105 operaciones ICT) con el replay fiel del mismo código y ventana:
- Solo 12 de 105 operaciones coincidían con una señal del replay; las entradas en vivo se repartían uniformemente dentro de cada vela M15.
- 35 de 105 salieron de velas que al cerrar no confirmaban la señal: −0,39 R/op (−13,5 R). El resto dio +0,08 R/op.
- MSNR ya filtraba velas cerradas (`strategy/malaysian_snr/validation.py::closed_candles`).

## Tests

- Nuevos:
  - `tests/test_ict_closed_candles_only.py`: una vela en formación extrema no cambia la decisión, la dirección ni el SL (600 evaluaciones, 13 señales). Falla con el código anterior.
  - `tests/test_orb_sweep_mode.py`: paridad SWEEP con el replay 2Y.
  - `tests/test_v121_*`: selección alineada con la Fase 1.
- `tests/conftest.py`: fixture `orb_classic_modes`, para que los tests de mecánica breakout/retest sigan probándola con perfiles explícitos.
- Suite: 1756 pasan, 24 fallan. 23 ya fallaban en `f1a87d2`. El restante (`test_meta_execution_spread::...[timestamp2]`) es inestable porque fija `now + 2 min` al recolectarse; aislado pasa.

## A revisar con cuidado

- `dashboard/performance_page.py::_hot_sync_realtime_dashboard`: re-ejecuta `realtime_dashboard.py` en cada import, parchea en caliente clases, objetos vivos (vía `gc`) y `do_GET`, y silencia cualquier error. Recomiendo quitarlo.
- `tools/persist_instruments_pruning.py` ahora escribe `DEFAULT_PRIORITIZED_SYMBOLS` en la SQLite persistente al ejecutarse.
- `app/main.py` aún incluye Step Index, Jump 25 y XAGUSD en el universo ICT (ICT los rechaza igualmente).
- Fuera del commit: `graphify-out/` (generado) y `database/trading_bot.sqlite3-shm/-wal`.
- La demo de esta semana también es negativa en el replay (−0,057 R/trade en 282 señales): este PR alinea el comportamiento en vivo con el replay, pero no garantiza rentabilidad por sí solo.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
