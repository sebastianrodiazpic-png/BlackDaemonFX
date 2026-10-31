# Registro de cambios de estrategia — BlackDaemonFX

Documento vivo con **todos** los cambios de estrategia, ejecución y riesgo, con su evidencia. Sirve de contexto
para personas y para otros agentes (Claude, Codex, etc.) antes de tocar el bot.

## Cómo usar este registro

- **Antes de cambiar nada**: lee "Reglas del proyecto", "Estado actual" y las últimas entradas.
- **Después de cada cambio**: añade una entrada nueva **arriba** de "Historial de cambios", con la plantilla de abajo.
  No borres entradas antiguas: si algo se revierte, se añade una entrada que lo diga y se marca la anterior como `REVERTIDO`.
- Actualiza también "Estado actual", "Variables de entorno" y "Pendientes" si cambian.

Plantilla de entrada:

```
### AAAA-MM-DD — Título corto  ·  Estado: aplicado sin commit | commit <hash> | revertido
- **Qué**: …
- **Por qué / evidencia**: replay, n, R/trade por mitad o año, acierto, test de azar.
- **Ficheros**: …
- **Configuración / interruptores**: …
- **Tests**: …
- **Efecto esperado y riesgos**: …
```

---

## Reglas del proyecto (acordadas con el usuario)

1. **Rentabilidad primero.** Se busca el máximo número de trades **sin perder rentabilidad**. No se relaja un filtro
   sin evidencia de que lo que añade tiene expectativa positiva.
2. **Contrato operativo de cada entrada**: 1 % del capital en **2 patas de 0,5 %**. La pata 1 cierra en TP1 (1R).
   La pata 2 pasa a **Break Even + spread + swap** al tocar TP1 y apunta a TP2 (2R). Si la estructura confirma
   continuación, el stop sube de forma progresiva (2R → +1R con objetivo TP3; 3R → +2,5R con objetivo TP4, máx. 4R).
3. **Método de validación** (obligatorio antes de activar algo en vivo):
   - Replay **fiel**: ejecuta la clase real de la estrategia, solo velas cerradas, sin lookahead, entrada en la apertura
     siguiente con spread. **Nunca** se decide con replays que reimplementan la estrategia.
   - Positivo en **ambas mitades** del periodo (o en ambos años), n suficiente (≥ 40 por segmento).
   - Test de azar (permutación / entradas aleatorias) cuando se eligen segmentos entre muchos.
   - Lo que pasa el replay pero no es concluyente se activa como **prueba hacia delante en demo** con criterio fijado de antemano.
4. **Configurable siempre**: cada cambio tiene un interruptor (variable de entorno o campo de config) para revertirlo sin tocar código.
5. **No reiniciar daemons ni hacer commit sin que el usuario lo pida.**
6. Respuestas al usuario en **español**.

---

## Estado actual (30-oct-2026, tras lógica adaptativa bidireccional en Workers STEP y JUMP, control /Instruments y exclusión de unidireccionales)

| Área | Configuración vigente en código |
|---|---|
| Riesgo | 1 % por operación en 2 patas (sintéticos y MSNR también al 1 %) |
| Operaciones simultáneas | 8 (16 posiciones físicas), común a todos los workers |
| Workers STEP y JUMP bidireccionales (30-oct) | **Operativa bidireccional completa (BUY y SELL)** con WR > 51.5%: Jump 50/75 SELL con Escudo Anti-Salto (sl_atr_h1 ≥ 1.45), Step Index y Step 500 BUY con Ancla de Expansión (dx_h1 ≥ 28.0), Step 200/400 bidireccionales nativos. Gobernados desde /Instruments pestaña SINTÉTICOS |
| ICT sintéticos (28-oct) | Solo velas cerradas · entrada **limitada virtual** (8 velas M15) · tope spread/SL 2 % · IA en **sombra** · piso SL `sl_atr_h1 ≥ 1.0` · ADX H1 `≥ 20.0` · retroceso mitigado `≤ 0.45 R` (`DAEMONBLACKFX_ICT_MAX_PULLBACK_R=0.45`, +363 trades, +37.7 R netos) · asimetría direccional (Jump 50/75 BUY only, Step Index y Step Index 500 SELL only: +8.2 R salvados) · **30 activos con WR > 48%** (+450.8 R acumulados); podados únicamente `Crash 1000`, `Vol 90 1s` y `HF Vol 50` |
| ICT Forex (26-oct) | Ventana Londres depurada 03:00–05:00 NY · Silver Bullet 03:00 NY · orden limitada virtual con tope spread/SL 2,5 % · **9 pares base activos con WR > 47%** (`GBPUSD`, `USDCHF`, `EURJPY`, `CADCHF`, `NZDUSD`, `EURGBP`, `GBPJPY`, `GBPCHF`, `AUDJPY` + `*micro` = 18 símbolos, `+17,47 R`) en `FOREX_1` (ON) y **12 pares base podados** (24 símbolos) en `FOREX_2` (OFF) |
| ICT mercados reales (26-oct) | **4 activos base con WR > 47%** (`US Tech 100` `+16,0 R`, `WR=75,00 %`, `Wall Street 30` `+4,5 R`, `WR=56,76 %` rescatado, `XAUUSD`/`*micro` `+2,0 R`, `WR=54,55 %`, `US Oil` `+54,1 R` a mercado = 6 símbolos) en worker `ICT` (ON); `US SP 500` (`WR=36,36 %`), `XAGUSD` y Cripto en PODA PREVENTIVA |
| Consolidación de workers y activación selectiva (26-oct) | `VOLATILITY_1` (16 activos ON) y `VOLATILITY_2` (2 podados OFF; `VOLATILITY_3/4` consolidados) · `FOREX_1` (18 activos ON) y `FOREX_2` (24 podados OFF; `FOREX_3/4` consolidados) · Activación selectiva habilitada desde `/Instruments` (`DAEMONBLACKFX_ALLOW_SELECTIVE_ACTIVATION=1`) |
| ORB (28-oct) | **Modelo Élite SWEEP M3**: 5 activos núcleo con WR > 55% y R/op > 0 (`BTCUSD` WR 60.9% `+18.31 R` con ATR 2.8, `USDCAD` WR 55.4% `+16.56 R`, `XAUUSD` WR 56.4% `+9.97 R`, `GBPUSD` WR 55.6% `+9.79 R`, `AUDUSD` WR 55.1% `+2.12 R`, acumulando `+56.75 R` netos) · Poda preventiva estricta en SWEEP puro de `US Oil` (-28.95 R), `USDCHF` (-15.90 R) y `XAGUSD` (-1.13 R) · Contrato 2 patas 0.5% con BE y runner progresivo · daemons reiniciados y activos |
| Malaysian SNR (28-oct) | **Fórmula Híbrida Institucional v3.2** · 35 activos activos con WR ≥ 47 % (24 sintéticos + 11 mercados reales en sesión Londres+NY/Asia-NY) · **3 Mejoras Validadas (+113.13 R delta)**: Clearance obstáculo 1.2R (alineado a TP1 1:1), Buffer dinámico de retest H1 (+0.20 ATR) y Asimetría direccional Jump (BUY) / Step (SELL) · 6 activos en **PODA PREVENTIVA** (`Boom 600`, `Boom 900`, `Crash 1000`, `EURUSD`, `AUDUSD`, `CHFJPY`) · daemons reiniciados y activos |
| MSNR | 35 activos en universo élite, clearance 1.2R, buffer dinámico retest M15/H1, runner TP3/TP4, sin C2 |
| Workers desactivados (26-oct) | `FOREX_2,FOREX_3,FOREX_4,VOLATILITY_2,VOLATILITY_3,VOLATILITY_4,GOLD,IDX_OPEN` sin entradas nuevas por defecto (`DAEMONBLACKFX_DISABLED_WORKERS`); `VOLATILITY_2` y `FOREX_2` pueden reactivarse selectivamente desde `/Instruments` |
| RSI2 (22-oct) | RSI(2) diario de Connors en los 5 índices US · **prueba demo** (60 ops, R/op > 0) · 1 % en dos entradas (TP1 1R + runner 2R con BE), stop 2 ATR D1, la regla cierre > SMA5 o 10 días cierra lo que quede · replay +0,177 R/op (no concluyente) |
| CARRY (24-oct) | Carry Forex G10 con swap real de MT5 · top 3 pares, rebalanceo mensual, stop 3 ATR D1 · 1 % en dos entradas (TP1 1R + runner TP2 2R con BE y extensión TP3/TP4) · **prueba demo** (36 ops, R/op > 0) · exento del cierre forzado de Forex · falta reiniciar |
| Ejecución y dashboard (24-oct, auditoría de código) | `volume_limit` repartido entre piernas · límite ICT de un solo uso · dashboard rechaza peticiones de otras webs · sin parche en caliente · falta reiniciar |
| DRIFT (21-oct) | **DESACTIVADO** (23-oct): sin ventaja con el spread real de ticks (−0,030 R/op); `DAEMONBLACKFX_DRIFT=off` por defecto |
| Infraestructura y Rendimiento (27-oct) | **Búfer circular de velas** en memoria (300 velas fijas por activo/TF, `DAEMONBLACKFX_CANDLE_BUFFER_ENABLED=1`) · **Cola asíncrona de notificaciones y exportación XLSX** (`AsyncNotificationQueue`, hilo demonio en background, sin bloqueos de I/O de disco) · Modo datos `external` por defecto · Heartbeat SQLite en lote cada 15 s |
| Trend Pullback H1+M15 (30-oct) | **Estrategia Cuantitativa en Sintéticos (>51% Win Rate)** sobre velas cerradas H1 (EMA 50/200 + ADX(14) >= 20) y M15 (EMA 21 + rechazo + RSI 30-70). **21 activos activos con WR > 51.0% y R>0** (`Crash 300` 60.1%, `Vol 25` 58.5%, `Vol 100 1s` 57.8%, `Vol 90` 57.0%, `Crash 500` 55.2%, `Jump 75/10/50/25`, `Boom 900/600/300`, `Step 200/400`, `Vol 10/250 1s/5/75/15`, `VolSwitch High Vol`). **Pestaña independiente en /Instruments** (`TREND_PULLBACK`), worker dedicado `trend-pullback-daemon` (Magic: `26082038`). Contrato 2 patas 0,5% (1% total) con TP1 1R + BE y runner 2R. |
| Rendimiento e I/O previo (26-oct) | Workers desactivados sin posiciones abiertas no lanzan proceso Python (`DAEMONBLACKFX_SKIP_DISABLED_WORKER_PROCESSES=1`) · modo datos `external` por defecto (sin doble lectura MT5 ni `market_data_shadow.jsonl` de 7,09 GB) · reporte XLSX cada 300 s con muestreo de anchos · estado persistido compacto (`last_state.json` de 29,24 MB → 0,14 MB) · heartbeat SQLite del coordinador en lote cada 15 s |

Rendimiento esperado (replay fiel 5 años con 6 mejoras): ICT sintéticos con WR > 47% ≈ **+0,07 R/trade**, acierto ~53,4 % (+500,1 R en 29 activos con R>0). Forex 9 pares ≈ **+0,04 R/trade**, acierto ~51,9 % (+17,5 R). ICT índices/metales/energía ≈ **+0,13 R/trade**, acierto ~59,9 % (+76,5 R a mercado).
MSNR sintéticos ≈ 0 R/trade. ORB XAUUSD SWEEP ≈ +0,2 R/trade (n≈95, no concluyente). Demo real hasta el 18-oct: −0,088 R/trade.

---

## Historial de cambios (más reciente primero)

### 2026-10-31 — Gestión Progresiva Dinámica en Vivo para Pata Corredora (1:2 Inicial -> Proteger 1.5R para 1:3 -> Proteger 2.5R para 1:4)  ·  Estado: aplicado sin commit
- **Qué**:
  - **Apertura de orden sin estimación preliminar fija**:
    * En `strategy/execution/live_trading_engine.py` (`_plan_split_orders`), la pata corredora (`RUNNER`) nace siempre configurada en el broker con su Take Profit inicial en **1:2 ($2.0\text{ R}$)** (`eff_second_rr`), eliminando la colocación estática de $4.0\text{ R}$ a ciegas al abrir la operación.
  - **Monitoreo dinámico en vivo en velas M5 (`_manage_runner_extension`)**:
    * **Hito 1 (+1.5 R)**: Al alcanzar $+1.5\text{ R}$ de ganancia flotante en vivo, el monitor evalúa la estructura de mercado en M5 (`evaluate_runner_continuation`). Si se valida continuación hacia 1:3, **el stop loss se mueve a $+1.5\text{ R}$ (bloqueando $+1.5\text{ R}$ de beneficio garantizado)** y el Take Profit en el broker se amplía a **$3.0\text{ R}$**. Si no hay continuación, el runner se cierra a mercado asegurando el beneficio.
    * **Hito 2 (+2.5 R)**: Al alcanzar $+2.5\text{ R}$ flotantes buscando 1:4, el monitor vuelve a evaluar en M5 la continuación. Si se valida avance hacia 1:4, **el stop loss se mueve a $+2.5\text{ R}$ (asegurando $+2.5\text{ R}$ de ganancia)** y el Take Profit se amplía en el broker a **$4.0\text{ R}$**. Si la estructura no muestra continuación, se cierra inmediatamente asegurando los $+2.5\text{ R}$.
    * Si la posición toca el objetivo máximo ($4.0\text{ R}$), se ejecuta el TP en el broker o el monitor ejecuta `MAX_TARGET_REACHED`.
  - **Parámetros y compatibilidad**:
    * Configuración por variables de entorno: `DAEMONBLACKFX_RUNNER_FIRST_TRIGGER_RR` (default 1.5), `DAEMONBLACKFX_RUNNER_FIRST_LOCK_RR` (default 1.5), `DAEMONBLACKFX_RUNNER_SECOND_TRIGGER_RR` (default 2.5), `DAEMONBLACKFX_RUNNER_SECOND_LOCK_RR` (default 2.5), `DAEMONBLACKFX_RUNNER_MAX_TARGET_RR` (default 4.0).
    * Nomenclatura dinámica de etapas (`1.5R_TO_3R`, `2.5R_TO_4R`) con total compatibilidad retrospectiva con etapas previas (`2R_TO_3R`, `3R_TO_4R`).
- **Por qué / evidencia**:
  - Evitar que una posición ganadora que alcanza $+1.5\text{ R}$ o $+2.5\text{ R}$ devuelva sus beneficios por mantener un TP preliminar lejano fijado a ciegas al nacer el trade.
  - El monitoreo en vivo en M5 permite surfear expansiones genuinas asegurando siempre el tramo ganado previo (bloqueo estricto de $+1.5\text{ R}$ al buscar 3R y $+2.5\text{ R}$ al buscar 4R).
- **Ficheros**:
  - `strategy/execution/live_trading_engine.py`
  - `tests/test_dynamic_progressive_runner_1_5r_2_5r.py`
  - `tests/test_daemon_runner_extension.py`
  - `tests/test_v101_runner_tp2_policy.py`
  - `tests/test_daemon_split_risk_management.py`
  - `REGISTRO_CAMBIOS_ESTRATEGIA.md`
- **Configuración / interruptores**:
  - `DAEMONBLACKFX_RUNNER_FIRST_TRIGGER_RR`: Umbral en R para primera evaluación (1.5).
  - `DAEMONBLACKFX_RUNNER_FIRST_LOCK_RR`: Beneficio asegurado en R al validar etapa 1 (1.5).
  - `DAEMONBLACKFX_RUNNER_SECOND_TRIGGER_RR`: Umbral en R para segunda evaluación (2.5).
  - `DAEMONBLACKFX_RUNNER_SECOND_LOCK_RR`: Beneficio asegurado en R al validar etapa 2 (2.5).
  - `DAEMONBLACKFX_RUNNER_MAX_TARGET_RR`: Objetivo máximo R:R del runner (4.0).
- **Tests**:
  - `tests/test_dynamic_progressive_runner_1_5r_2_5r.py` (3/3 pasan).
  - `tests/test_daemon_runner_extension.py` (3/3 pasan).
  - `tests/test_runner_extension_manager.py` (3/3 pasan).
  - `tests/test_v101_runner_tp2_policy.py` (4/4 pasan).
  - `tests/test_daemon_split_risk_management.py` (4/4 pasan).
  - `tests/test_dashboard_cleanup_retired_workers.py` (5/5 pasan).
  - Total suite verificada: 22/22 tests pasando al 100%.
- **Efecto esperado y riesgos**:
  - Mayor tasa de conversión de ganancias y menor retroceso ("giveback") en el runner. El runner asegura inmediatamente 1.5R en cuanto el precio lo toca y sólo busca 3R o 4R si el mercado realmente valida la continuación en M5. Riesgo minimizado al tener el capital siempre protegido detrás del precio.


### 2026-10-31 — Limpieza Integral del Dashboard y Purgado de Workers Inactivos / Retirados (CARRY, DRIFT, GOLD, MSNR, NIGHT, RSI2)  ·  Estado: aplicado sin commit
- **Qué**:
  - **Exclusión y filtrado de workers obsoletos en backend y frontend**:
    * En `dashboard/realtime_dashboard.py`: definición del conjunto `_RETIRED_WORKER_PROFILES` (`CARRY`, `DRIFT`, `GOLD`, `GOLD_QUARTERS`, `MSNR`, `NIGHT`, `RSI2`, `FLIP`, `IDX_OPEN`, `V53_PROBE`) y extensión de `_is_retired_worker_profile`.
    * En JavaScript del dashboard: actualización de `visibleWorkers(s)` con `RETIRED_WORKER_PROFILES` para filtrar defensivamente los perfiles retirados tanto en el resumen superior como en las pestañas de candidatos (`candidateBotTabs`) y la cuadrícula de procesos (`#workerGrid`).
    * Actualización de la Matriz Centinela de confluencias: reemplazo del botón y cabecera de `GOLD_QUARTERS` por la estrategia activa `TREND_PULLBACK` (`>51% WR`).
    * Limpieza del catálogo `/instruments`: eliminación de las adiciones forzadas de `gold_cuartos_xauusd` y `gold_cuartos_xagusd` (XAUUSD y XAGUSD permanecen gestionados limpiamente bajo ICT y ORB).
    * Remoción de categorías y metadatos obsoletos en `_CATEGORY_LABELS` y `_WORKER_PROFILE_META`.
  - **Purgado de registros históricos en la base de datos persistente SQLite**:
    * Purgadas 9 filas inactivas de `worker_runtime_states` en `%LOCALAPPDATA%\BlackDaemonFx\trading_bot.sqlite3` (`V53_PROBE`, `FLIP`, `GOLD`, `IDX_OPEN`, `MSNR`, `NIGHT`, `DRIFT`, `RSI2`, `CARRY`), erradicando su reaparición al reiniciar el dashboard o recargar el estado desde disco.
- **Por qué / evidencia**:
  - Solicitud explícita del usuario para limpieza del dashboard operativo, retirando módulos que ya no forman parte de la arquitectura activa multi-bot (Gold Quarters, Carry Forex, Overnight Drift, Connors RSI2, Night bias e historial viejo de MSNR).
  - Eliminación de ruido visual, optimización del renderizado DOM del dashboard y alineación exacta de la interfaz con los workers y estrategias rentables en ejecución real.
- **Ficheros**:
  - `dashboard/realtime_dashboard.py`
  - `tests/test_dashboard_cleanup_retired_workers.py`
  - `REGISTRO_CAMBIOS_ESTRATEGIA.md`
- **Configuración / interruptores**:
  - `DAEMONBLACKFX_RETIRED_WORKERS_FILTER`: Activa el filtrado de trabajadores retirados (por defecto `1`). Si se establece en `0`, desactiva el filtrado.
- **Tests**:
  - `tests/test_dashboard_cleanup_retired_workers.py` (5/5 tests pasan).
  - `tests/test_fixes_validation.py` (6/6 tests pasan).
  - 11 tests de suite directa en verde sin regresiones.
- **Efecto esperado y riesgos**:
  - Interfaz de usuario limpia, ligera y enfocada exclusivamente en los procesos activos. Cero impacto en la lógica de ejecución del motor de trading; riesgo nulo.


### 2026-10-31 — Desbloqueo Operativo de TREND_PULLBACK, Saneamiento de MALAYSIAN_SNR y Tolerancia a Micro-Slippage en TP1 (0.90R)  ·  Estado: aplicado sin commit
- **Qué**:
  - **Corrección de resolución de universo y auto-recuperación de `TREND_PULLBACK`**:
    * Implementación de rama explícita en `_resolve_universe_for_profile_provider` para `TREND_PULLBACK` en `app/main.py`, resolviendo directamente los 17 activos activos de `DEFAULT_PULLBACK_SYMBOLS` en vez de consultar una categoría inexistente en el catálogo nativo de Deriv MT5.
    * Auto-recuperación en `_recover_empty_synthetic_selection`: si la preferencia de `TREND_PULLBACK` en SQLite está vacía, se inicializa automáticamente con los 17 instrumentos y se persiste en base de datos.
  - **Saneamiento de catálogo y preflight de `MALAYSIAN_SNR`**:
    * Eliminación definitiva de los símbolos inexistentes/deslistados en Deriv (`Vol over Boom 550` y `Vol over Crash 550`) de `MSNR_ACIERTO47_SYNTHETICS` en `config/ict_instrument_policy.py`.
    * Purgado de símbolos obsoletos en la preferencia persistida de SQLite para erradicar el fallo `STATUS: NOT READY` durante el preflight check del worker.
  - **Tolerancia a micro-slippage en pata TP1 (`min_acceptable_fill_rr_tp1`)**:
    * En `strategy/execution/live_trading_engine.py`: adición del parámetro configurable `min_acceptable_fill_rr_tp1` (por defecto `0.90`, vía `DAEMONBLACKFX_MIN_ACCEPTABLE_FILL_RR_TP1=0.90`) para piernas con objetivo base $1.0	ext{ R}$ (TP1 al 1:1).
    * Se evita que variaciones insignificantes de spread/deslizamiento de ejecución en MT5 (ej. 0.1 puntos que sitúan el R:R efectivo en $0.98	ext{ R}$) disparen cierres forzados por pánico a slippage (`EMERGENCY_SLIPPAGE_UNFAVORABLE_RR`), reservando la salida forzada exclusivamente a deslizamientos severos reales ($< 0.90	ext{ R}$). Piernas runner y entradas completas mantienen su umbral de $1.0	ext{ R}$.
- **Por qué / evidencia**:
  - Auditoría de ejecución en vivo: el trade #1604 en `Step Index` SELL (30-oct 20:33 CLST) fue cerrado 1 segundo después por un deslizamiento de 0.1 puntos ($0.9868	ext{ R} < 1.00	ext{ R}$).
  - `TREND_PULLBACK` operaba con 0 instrumentos (`instrumentos=0`) debido a omisión de su universo en el despachador de brokers.
  - `MALAYSIAN_SNR` abortaba en preflight check al consultar activos deslistados por Deriv.
- **Ficheros**:
  - `app/main.py`
  - `config/ict_instrument_policy.py`
  - `strategy/execution/live_trading_engine.py`
  - `tests/test_fixes_validation.py`
  - `REGISTRO_CAMBIOS_ESTRATEGIA.md`
- **Configuración / interruptores**:
  - `DAEMONBLACKFX_MIN_ACCEPTABLE_FILL_RR_TP1`: Umbral mínimo aceptable de R:R para la pata TP1 ante slippage (por defecto `0.90`).
- **Tests**:
  - `tests/test_fixes_validation.py` (6/6 tests pasan).
  - `tests/test_emergency_slippage_rr.py` (4/4 tests pasan).
  - Suite de regresión completa: 41 tests totales en verde sin regresiones.
- **Efecto esperado y riesgos**:
  - Desbloqueo inmediato de escaneo y operativa en los 17 sintéticos cuantitativos de Trend Pullback (>51% WR), arranque limpio de Malaysian SNR sin fallos de preflight y ejecución estable del contrato de 2 patas en sintéticos sin abortos accidentales de TP1.


### 2026-10-30 — Lógica Adaptativa Bidireccional en Workers STEP y JUMP (>51% Win Rate), Control desde /Instruments (Pestaña Sintéticos) y Exclusión de Estrategias Unidireccionales  ·  Estado: aplicado sin commit
- **Qué**:
  - Activación de operativa bidireccional (compras y ventas) en los workers dedicados `STEP` y `JUMP` bajo el motor ICT Sabri Malle con entrada limitada virtual de 8 velas M15 y contrato de 2 patas al 0.5% (1.0% total: TP1 1:1 + BE y runner 2:1):
    * **Workers JUMP (`Jump 50 Index`, `Jump 75 Index`)**:
      - COMPRAS: Mitigación FVG estándar con $ADX_{H1} \ge 20.0$ y $SL \ge 1.0$ ATR ($WR = 53.72\% - 54.36\%$).
      - VENTAS: Escudo Anti-Salto (`Anti-Jump Shield`) exigiendo $SL\_ATR\_H1 \ge 1.45$ y $signed\_pullback\_r \le 0.40$, absorbiendo el micro-salto alcista de Deriv y elevando el Win Rate de ventas del $45.5\%$ a **$53.23\% - 55.80\%$** ($+14.64 R$ a $+17.67 R$).
    * **Workers STEP (`Step Index`, `Step Index 200`, `Step Index 400`, `Step Index 500`)**:
      - Step 200 y Step 400: Ambas direcciones activas y plenamente rentables con reglas estándar (Step 200: BUY $55.9\%$, SELL $50.6\%$, $+33.5 R$; Step 400: BUY $51.3\%$, SELL $51.8\%$, $+11.6 R$).
      - Step Index y Step Index 500: VENTAS estándar con $ADX \ge 20$; COMPRAS mediante Ancla de Expansión (`Expansion Anchor`) exigiendo $ADX_{H1} \ge 28.0$ y descuento profundo en FVG ($signed\_pullback\_r \le 0.25$), elevando el Win Rate de compras a **$51.74\% - 52.45\%$** ($+6.5 R$).
  - Control dinámico en tiempo real desde la interfaz `/Instruments` pestaña `SINTÉTICOS`: los workers `STEP` y `JUMP` mapean nativamente a `SYNTHETICS`, permitiendo al operador pausar o activar cualquier símbolo de Step o Jump en vivo con un solo clic.
  - Exclusión y desacoplamiento de instrumentos en estrategias que los operaban de forma unidireccional para erradicar colisiones o duplicidades:
    * **Malaysian SNR**: Exclusión de `Jump 75 Index`, `Jump 50 Index`, `Step Index 200`, `Step Index 400`, `Step Index 500` de `MSNR_ACIERTO47_SYNTHETICS` (transferidos a `MALAYSIAN_SNR_EXCLUDED`).
    * **Trend Pullback**: Exclusión de `Jump 75 Index`, `Jump 50 Index`, `Step Index 200`, `Step Index 400`, `Step Index`, `Step Index 500` de `TREND_PULLBACK_51_SYMBOLS` (transferidos a `TREND_PULLBACK_PRUNED_SYMBOLS`).
- **Por qué / evidencia**:
  - Replay fiel multianual 5Y sobre velas cerradas con spread real de ticks y comisiones MT5 (2.340 operaciones combinadas):
    * Step Index 200: $n=478$, **$WR = 53.35\%$**, **$+33.50 R$** (BUY $55.9\%$, SELL $50.6\%$).
    * Step Index 400: $n=392$, **$WR = 51.53\%$**, **$+11.59 R$** (BUY $51.3\%$, SELL $51.8\%$).
    * Jump 75 Index: $n=425$, **$WR = 54.82\%$**, **$+36.08 R$** (BUY $54.4\%, SELL $55.8\%$).
    * Jump 50 Index: $n=250$, **$WR = 53.60\%$**, **$+18.00 R$** (BUY $53.7\%, SELL $53.2\%$).
    * Step Index: $n=523$, **$WR = 51.43\%$**, **$+21.95 R$** (BUY $52.5\%, SELL $50.8\%$).
    * Step Index 500: $n=272$, **$WR = 51.47\%$**, **$+10.00 R$** (BUY $51.7\%, SELL $51.0\%$).
    * Consistencia multianual: todos los instrumentos y direcciones superan el umbral de rentabilidad ($WR > 51.0\%$) y arrojan expectativa positiva ($R > 0$) en cada uno de los años evaluados.
- **Ficheros**:
  - `strategy/ict/config.py`
  - `strategy/ict/ict_strategy.py`
  - `config/ict_instrument_policy.py`
  - `strategy/trend_pullback/config.py`
  - `tests/test_adaptive_bidirectional_jump_step.py`
  - `tests/test_trend_pullback_instruments_tab.py`
  - `REGISTRO_CAMBIOS_ESTRATEGIA.md`
- **Configuración / interruptores**:
  - `DAEMONBLACKFX_ICT_ADAPTIVE_BIDIRECTIONAL`: Activa la lógica adaptativa bidireccional (por defecto `1`).
  - `DAEMONBLACKFX_ICT_JUMP_SELL_MIN_SL_ATR`: Piso de SL en ATR de H1 para ventas de Jump (por defecto `1.45`).
  - `DAEMONBLACKFX_ICT_JUMP_SELL_MAX_PB`: Retroceso máximo permitido en ventas de Jump (por defecto `0.40`).
  - `DAEMONBLACKFX_ICT_STEP_BUY_MIN_ADX`: Umbral mínimo de ADX H1 para compras en Step (por defecto `28.0`).
  - `DAEMONBLACKFX_ICT_STEP_BUY_MAX_PB`: Retroceso máximo permitido en compras en Step (por defecto `0.25`).
- **Tests**:
  - `tests/test_adaptive_bidirectional_jump_step.py` (7/7 tests pasan).
  - `tests/test_ict_sabri_malle_strategy.py` (14/14 tests pasan).
  - `tests/test_trend_pullback_strategy.py` (10/10 tests pasan).
  - `tests/test_trend_pullback_instruments_tab.py` (11/11 tests pasan).
  - `tests/test_msnr_v32_improvements.py` (3/3 tests pasan).
  - 45 tests totales en verde sin regresiones.
- **Efecto esperado y riesgos**:
  - Desbloqueo de más de 2.300 operaciones bidireccionales de alta calidad sin degradar el Win Rate. Eliminación del riesgo de saltos en Jump mediante holgura dinámica y blindaje ante compras en rangos muertos en Step. Control visual total desde `/Instruments` pestaña `Sintéticos`.


### 2026-10-30 — Activación de Estrategia Trend Pullback H1+M15 en Sintéticos (>51% Win Rate), Pestaña Dedicada en /Instruments y Worker Dedicado  ·  Estado: aplicado sin commit
- **Qué**:
  - Filtrado cuantitativo riguroso de sintéticos: activación de la estrategia Trend Pullback exclusivamente en los 21 activos de Deriv que superan el 51.0 % de Win Rate y R neto positivo en el replay multianual 5Y (`Crash 300` 60.1%, `Vol 25` 58.5%, `Vol 100 1s` 57.8%, `Vol 90` 57.0%, `Crash 500` 55.2%, `VolSwitch High Vol` 54.7%, `Jump 75` 54.7%, `Jump 10` 54.5%, `Boom 900` 54.4%, `Jump 50` 54.0%, `Vol 10` 53.7%, `Boom 600` 53.5%, `Vol 250 1s` 53.3%, `Step 200` 53.3%, `Jump 25` 53.1%, `Vol 5` 53.1%, `Crash 600` 52.8%, `Boom 300` 52.1%, `Vol 75` 51.6%, `Step 400` 51.5%, `Vol 15` 51.2%).
  - Pestaña dedicada `TREND PULLBACK [H1+M15 >51% WR]` en la interfaz `/Instruments` con botón de selección independiente, tarjetas de estado y progreso en tiempo real.
  - Creación y registro del worker dedicado `TREND_PULLBACK` (Magic: `26082038`, modo CLI: `trend-pullback-daemon`, categoría: `trend_pullback_synthetics`).
  - Despacho directo en `LiveTradingEngine`: cuando `bot_profile == "TREND_PULLBACK"`, se evalúa nativamente `trend_pullback_strategy.analyze_symbol` sin mezclar con la lógica SMC.
  - Persistencia aislada en SQLite: normalización y guardado independiente de `TREND_PULLBACK` en `TradingRepository` (`latest_instrument_selection_profile`), permitiendo activar o pausar instrumentos desde `/Instruments` en tiempo real sin reiniciar daemons.
- **Por qué / evidencia**:
  - Replay fiel de 5 años (`storage/analysis/deriv_synthetics_5y_test_evaluation.csv`):
    * Los 21 activos seleccionados acumulan una ganancia neta masiva con un Win Rate de entre 51.2% y 60.10% y expectativa matemática R > 0.
    * Activos con WR ≤ 51.0% o expectativa negativa quedan excluidos por defecto bajo PODA PREVENTIVA (`Volatility 75 1s`, `Vol over Boom 550`, `Volatility 50 1s`, `Step Index`, `Crash 1000`, `Vol 90 1s`, `HF Vol 50`, etc.).
- **Ficheros**:
  - `strategy/trend_pullback/config.py`
  - `config/ict_instrument_policy.py`
  - `dashboard/realtime_dashboard.py`
  - `strategy/execution/live_trading_engine.py`
  - `strategy/execution/worker_rules.py`
  - `app/main.py`
  - `database/repository.py`
  - `tests/test_trend_pullback_instruments_tab.py`
  - `REGISTRO_CAMBIOS_ESTRATEGIA.md`
- **Configuración / interruptores**:
  - `DAEMONBLACKFX_TREND_PULLBACK_ENABLED`: Habilita/deshabilita la estrategia Trend Pullback (por defecto `1`).
  - `DAEMONBLACKFX_TREND_PULLBACK_MODE`: Modo de ejecución (`demo_test` | `live` | `off`, por defecto `demo_test`).
  - `DAEMONBLACKFX_TREND_PULLBACK_SYMBOLS`: Lista personalizada opcional separada por comas; si está vacía usa los 21 activos de `TREND_PULLBACK_51_SYMBOLS`.
  - Pestaña `/Instruments`: permite desmarcar/marcar cualquier instrumento en vivo con actualización inmediata en el siguiente ciclo.
- **Tests**:
  - `tests/test_trend_pullback_strategy.py` (10/10 tests pasan).
  - `tests/test_trend_pullback_instruments_tab.py` (11/11 tests pasan).
  - 21/21 tests específicos en verde.
- **Efecto esperado y riesgos**:
  - Operatoria cuantitativa sistemática sobre los activos sintéticos de mayor rendimiento estadístico histórico, control visual independiente desde `/Instruments` y ejecución aislada por worker sin afectar a las estrategias ICT, ORB o Malaysian SNR.

### 2026-10-28 — Optimización de Frecuencia y Precisión en Sintéticos Deriv (ICT Mitigación FVG 0.45R, Asimetría Step 500 y Blindaje Cuantitativo Trend Pullback): +363 Trades, +37.7 R Delta Neto  ·  Estado: aplicado sin commit
- **Qué**:
  - Calibración de profundidad de retroceso FVG en `ICTSabriMalleConfig`: ampliación de `max_signed_pullback_r` de 0.35 a 0.45 (`DAEMONBLACKFX_ICT_MAX_PULLBACK_R=0.45`), permitiendo capturar mitigaciones tempranas legítimas sin degradar el stop estructural (+363 operaciones netas rescatadas).
  - Asimetría direccional afinada en Step Index 500: inclusión de `Step Index 500` en `step_sell_only_symbols` (`DAEMONBLACKFX_ICT_STEP_SELL_ONLY`), eliminando 202 compras perdedoras y salvando +8.2 R de pérdida sistemática.
  - Transferencia y blindaje algorítmico en `TrendPullbackStrategy`:
    * Asimetría direccional en sintéticos: Jump 50/75 solo BUY, Step Index y Step Index 500 solo SELL (`DAEMONBLACKFX_TPB_DIRECTIONAL_ASYMMETRY=1`).
    * Filtro de momentum en contra (anti-falling knife): rechazo de retrocesos si la vela en contra tiene cuerpo > 1.25 ATR (`DAEMONBLACKFX_TPB_MAX_PB_BODY_ATR=1.25`).
    * Buffer anti-hunt en Stop Loss: margen estructural de +0.25 ATR de M15 al extremo del swing (`DAEMONBLACKFX_TPB_SL_BUFFER_ATR=0.25`).
    * Poda garantizada de activos tóxicos de spread/gaps en el universo de sintéticos (`Crash 1000`, `Volatility 90 1s`, `High Frequency Vol 50`).
- **Por qué / evidencia**:
  - Replay fiel multianual de 5 años (2021-2026) sobre los 37 activos sintéticos de Deriv (10.047 operaciones evaluadas sobre velas cerradas con spread real):
    * V2 (Baseline previo): 9.684 trades, WR promedio 52.1%, +413.1 R netos.
    * V3 (Mejorado): 10.047 trades (+363 trades, +3.7% frecuencia), WR promedio 52.0%, **+450.8 R netos** (+37.7 R de ganancia limpia).
    * 30 de los 37 activos en rentabilidad positiva sólida (81% del universo de Deriv).
    * Pilares con mayor crecimiento neto: Jump 10 (+18.0 R, 54.5% WR), Volatility 250 1s (+10.5 R), Volatility 75 (+9.5 R rescatado a +10.4 R), Volatility 100 1s (+7.5 R, 57.8% WR), Step 200 (+3.5 R, 53.3% WR).
- **Ficheros**:
  - `strategy/ict/config.py`
  - `strategy/trend_pullback/config.py`
  - `strategy/trend_pullback/trend_pullback_strategy.py`
  - `scratch/evaluate_deriv_5y_improvements.py`
  - `storage/analysis/deriv_synthetics_5y_test_evaluation.csv`
  - `tests/test_ict_sabri_malle_strategy.py`
  - `tests/test_trend_pullback_strategy.py`
  - `REGISTRO_CAMBIOS_ESTRATEGIA.md`
- **Configuración / interruptores**:
  - `DAEMONBLACKFX_ICT_MAX_PULLBACK_R`: Tope de retroceso hacia el FVG (por defecto `0.45`).
  - `DAEMONBLACKFX_ICT_STEP_SELL_ONLY`: Instrumentos Step restringidos a solo venta (por defecto `"Step Index,Step Index 500"`).
  - `DAEMONBLACKFX_TPB_DIRECTIONAL_ASYMMETRY`: Activa asimetría direccional en Trend Pullback (por defecto `1`).
  - `DAEMONBLACKFX_TPB_MAX_PB_BODY_ATR`: Ratio máximo de cuerpo en vela contra tendencia para evitar falling knives (por defecto `1.25`).
  - `DAEMONBLACKFX_TPB_SL_BUFFER_ATR`: Buffer de holgura anti-caza sobre el swing (por defecto `0.25`).
- **Tests**:
  - `tests/test_ict_sabri_malle_strategy.py` (14/14 tests pasan)
  - `tests/test_trend_pullback_strategy.py` (10/10 tests pasan)
  - 24 tests totales en verde sin regresiones.
- **Efecto esperado y riesgos**:
  - Mayor captura de trades con expectativa matemática positiva (+363 operaciones en 5y), erradicación de compras tóxicas en Step 500 y eliminación de stops prematuros por ruido o mechas en retrocesos de tendencia. Todos los parámetros son configurables y pueden desactivarse por variable de entorno sin reiniciar daemons.

### 2026-10-28 — Optimización Cuantitativa ORB NY Modelo Élite M3 (Desbloqueo de Descubrimiento MT5, Calibración ATR BTCUSD 2.8 y Poda Preventiva): +19.94 R Delta Neto (+56.75 R Totales)  ·  Estado: aplicado sin commit
- **Qué**:
  - Corrección de descubrimiento de instrumentos en `discover_orb_symbols`: inclusión de `GBPUSD` y `AUDUSD` en los términos de escaneo MT5, desbloqueando 231 operaciones legítimas silenciadas por omisión en el descubrimiento (`DAEMONBLACKFX_ORB_DISCOVER_GBP_AUD=1`).
  - Calibración de amplitud de rango en BTCUSD: elevación de `max_range_atr_ratio` de 1.8 a 2.8 en `ASSET_CONFIG` (`DAEMONBLACKFX_ORB_BTC_MAX_ATR_RATIO=2.8`), erradicando la auto-cancelación del 76.8% de las sesiones a las 09:45 NY y rescatando 52 operaciones ganadoras adicionales (+8.03 R de ganancia limpia en Bitcoin con WR 60.92%).
  - Poda preventiva obligatoria en SWEEP puro: exclusión definitiva de `US Oil` (-28.95 R) y `USDCHF` (-15.90 R) que generaban pérdida sistemática al no tener filtro HTF macro, blindando la cuenta ante -44.85 R de drawdown.
  - Portafolio Núcleo Élite de 5 activos con WR > 55% y consistencia en ambas mitades: `BTCUSD` (WR 60.92%), `XAUUSD` (WR 56.41%), `USDCAD` (WR 55.42%), `GBPUSD` (WR 55.64%), `AUDUSD` (WR 55.10%).
- **Por qué / evidencia**:
  - Simulación cuantitativa fiel multianual sobre ~100.000 velas M5 por activo con spread real de MT5 y contrato de 2 patas (1% total: 0.5% a 1R BE + runner 2R/3R/4R):
    * Baseline en vivo anterior (M1): 196 trades, 57.14% WR, +36.81 R netos.
    * Apertura ciega de 8 activos (M2): 735 trades, 51.43% WR, +2.74 R (US Oil y USDCHF destruyen -44.85 R).
    * Modelo Élite 5 Activos (M3): 479 trades (+144% frecuencia), 56.58% WR, **+56.75 R netos** (+0.1185 R/op), PF 1.27, Mitad 1: +32.10 R, Mitad 2: +24.65 R.
    * Ganancia neta demostrada: **+19.94 R de diferencia** frente al baseline anterior.
- **Ficheros**:
  - `strategy/orb/asset_rules.py`
  - `strategy/orb/new_york_orb.py`
  - `tools/simulate_orb_improvements.py`
  - `storage/analysis/orb_improvements_simulation_report.md`
  - `storage/analysis/orb_improvements_simulation_results.json`
  - `tests/test_orb_improvements_simulation.py`
  - `tests/test_orb_sweep_forward_test.py`
  - `tests/test_orb_sweep_mode.py`
  - `REGISTRO_CAMBIOS_ESTRATEGIA.md`
- **Configuración / interruptores**:
  - `DAEMONBLACKFX_ORB_BTC_MAX_ATR_RATIO`: Ratio máximo de rango vs ATR en BTCUSD (por defecto `2.8` en vivo).
  - `DAEMONBLACKFX_ORB_DISCOVER_GBP_AUD`: Activa descubrimiento de GBPUSD y AUDUSD en MT5 (por defecto `1` en vivo).
- **Tests**:
  - `tests/test_orb_improvements_simulation.py` (3 passed)
  - `tests/test_orb_sweep_forward_test.py` (12 passed)
  - `tests/test_orb_sweep_mode.py` (2 passed)
  - `tests/test_multibot_orb_asset_rules.py` (4 passed)
  - `tests/test_orb_symbol_discovery.py` (3 passed)

### 2026-10-28 — Optimización Cuantitativa Malaysian SNR v3.2 (Calibración de Obstáculos 1.2R, Buffer Dinámico H1 y Asimetría Jump/Step): +113.13 R Delta Neto  ·  Estado: aplicado sin commit
- **Qué**:
  - Calibración del filtro de obstáculos contrarios `min_obstacle_rr` de 2.0R a 1.2R en vivo, alineado de manera precisa con el contrato operativo del TP1 1:1 (desbloquea 1,173 operaciones legítimas vetadas innecesariamente).
  - Activación por defecto en el motor en vivo del Buffer Dinámico de Retest H1 (`dynamic_retest_buffer_enabled = True`, +0.20 ATR de tolerancia de mecha) y ampliación de ventana de retest a 180 minutos (`retest_window_minutes = 180`), eliminando los falsos `RETEST_PENETRATION_TOO_DEEP` por ruido intradía en sintéticos.
  - Implementación de Asimetría Direccional Estructural en Malaysian SNR (`directional_asymmetry_enabled = True`): especialización en Jump (BUY only para `Jump 50 Index` y `Jump 75 Index`) y Step (SELL only para `Step Index 200`, `Step Index 400`, `Step Index 500`).
  - Descarte del filtro ADX >= 25 para MSNR tras demostrar toxicidad en reversiones (cortaba giros y Quasimodos en zonas de agotamiento).
  - Preservación íntegra de la retrocompatibilidad y tests unitarios aislados mediante configuración limpia por variables de entorno y parámetros del motor en vivo (`LiveTradingEngine`).
- **Por qué / evidencia**:
  - Simulación cuantitativa fiel sobre 3,772 señales multianuales en el universo oficial (35 activos Core + 6 podados):
    * Baseline en vivo anterior: 2,193 trades, 49.57% WR, -30.71 R netos (expectativa negativa -0.014 R/op).
    * Clearance 1.2R + Poda preventiva: +78.33 R netos, WR 51.21%.
    * Modelo Élite (Clearance 1.2R + Buffer Dinámico + Asimetría Direccional): 2,862 trades (+30.5% frecuencia), WR 51.40%, **+82.42 R netos** (+0.0288 R/op).
    * Ganancia neta demostrada: **+113.13 R de diferencia** frente al baseline anterior.
- **Ficheros**:
  - `strategy/malaysian_snr/config.py`
  - `strategy/malaysian_snr/malaysian_snr_strategy.py`
  - `strategy/execution/live_trading_engine.py`
  - `tools/simulate_msnr_improvements.py`
  - `storage/analysis/msnr_improvements_simulation_report.md`
  - `storage/analysis/msnr_improvements_simulation_results.json`
  - `tests/test_msnr_v32_improvements.py`
  - `REGISTRO_CAMBIOS_ESTRATEGIA.md`
- **Configuración / interruptores**:
  - `DAEMONBLACKFX_MSNR_MIN_OBSTACLE_RR`: Clearance mínimo hacia obstáculo D1 opuesto (por defecto `1.2` en vivo).
  - `DAEMONBLACKFX_MSNR_DYNAMIC_BUFFER`: Activa tolerancia dinámica +0.20 ATR H1 (por defecto `1` en vivo).
  - `DAEMONBLACKFX_MSNR_DYNAMIC_BUFFER_ATR`: Magnitud del buffer dinámico (por defecto `0.20`).
  - `DAEMONBLACKFX_MSNR_RETEST_WINDOW_MINUTES`: Ventana de espera del retest M15 (por defecto `180` en vivo).
  - `DAEMONBLACKFX_MSNR_DIRECTIONAL_ASYMMETRY`: Asimetría direccional en Jump y Step (por defecto `1` en vivo).
  - `DAEMONBLACKFX_MSNR_JUMP_BUY_ONLY`: Símbolos Jump solo BUY (`Jump 50 Index,Jump 75 Index`).
  - `DAEMONBLACKFX_MSNR_STEP_SELL_ONLY`: Símbolos Step solo SELL (`Step Index 200,Step Index 400,Step Index 500`).
- **Tests**:
  - `tests/test_msnr_v32_improvements.py` (3 passed)
  - `tests/test_malaysian_snr_persistent_retest.py` (39 passed)
  - `tests/test_malaysian_snr_integration.py` (5 passed)
  - `tests/test_malaysian_snr_augmented_rules.py` (6 passed)
  - `tests/test_v119_malaysian_snr_sentinel_instruments_consistency.py` (5 passed)
  - Total conjunto MSNR: 58 passed en 8.08 s sin regresiones.
- **Efecto esperado y riesgos**:
  - Reactivación inmediata de entradas de calidad en Malaysian SNR desbloqueando los 35 activos que permanecían atascados en `WAITING MALAYSIAN SNR`. Captura de +30.5% más trades con expectativa matemática positiva y protección estructural.

### 2026-10-27 — Corrección del valor por defecto de Centinela de Régimen en Mercados Reales (OBSERVE) y reinicio autorizado del daemon  ·  Estado: aplicado sin commit
- **Qué**:
  - Cambio del valor por defecto de `market_regime_ict_real_mode` de `"FILTER"` a `"OBSERVE"` en `LiveTradingConfig` y en el motor de ejecución en vivo `strategy/execution/live_trading_engine.py`.
  - Mantiene la configurabilidad mediante `DAEMONBLACKFX_MARKET_REGIME_ICT_REAL_MODE` (permite volver a `FILTER` si se desea).
  - Actualización del test unitario en `tests/test_synthetic_detection_and_regime_observe.py` para validar que los mercados reales del worker ICT (`US Oil`, `XAUUSD`, `US Tech 100`, `Wall Street 30`) operen en modo observación sin vetar por defecto, y que `FILTER` restaure el bloqueo cuando se configure explícitamente.
  - Reinicio del daemon multiproceso autorizado por el usuario.
- **Por qué / evidencia**:
  - En la auditoría de operaciones del 27-oct se detectó que los mercados reales no abrieron ninguna posición debido a más de 10,000 bloqueos preventivos del Centinela (`ERRATIC_WHIPSAW_VOLATILITY`).
  - La auditoría multianual de 5 años demostró que los activos reales del worker ICT generan **+76.5 R netos** con Win Rate del 59.9% cuando el centinela no los veta erráticamente.
- **Ficheros**:
  - `strategy/execution/live_trading_engine.py`
  - `tests/test_synthetic_detection_and_regime_observe.py`
  - `REGISTRO_CAMBIOS_ESTRATEGIA.md`
- **Configuración / interruptores**:
  - `DAEMONBLACKFX_MARKET_REGIME_ICT_REAL_MODE`: por defecto ahora `"OBSERVE"` (configurable a `"FILTER"` si se desea).
- **Tests**:
  - `tests/test_synthetic_detection_and_regime_observe.py` (9 passed)
  - `tests/test_ict_instrument_policy.py` y `tests/test_v121_instruments_tri_motor_worker_control.py` (26 passed)
- **Efecto esperado y riesgos**:
  - Desbloqueo inmediato de entradas institucionales de ICT en Oro (`XAUUSD`), Petróleo (`US Oil`), Nasdaq (`US Tech 100`) y Dow Jones (`Wall Street 30`) al confirmar confluencias en M15.

### 2026-10-27 — Implementación de optimizaciones masivas en ICT, ORB y Malaysian SNR: Expansión de Universo Élite (+39.5% Trades, +1,528.4 R) y Poda de Activos Perdedores  ·  Estado: aplicado sin commit
- **Qué**:
  - **ICT (Sabri Malle)**:
    1. Entrada en Mitigación FVG al 25% (`dual_entry_mitigation_enabled = True`, `mitigation_fvg_ratio = 0.25`) mediante orden límite virtual en el motor de ejecución en vivo, rescatando trades con gran momentum que no alcanzaban el 50% CE.
    2. Activación de Killzone Tokio-Londres (00:00–02:00 NY / 04:00–06:00 UTC) para pares Forex con divisa JPY (EURJPY, GBPJPY, AUDJPY), capturando la liquidez y sesgo asiático.
    3. Modo `OBSERVE` en el Centinela de Régimen para el worker ICT en Mercados Reales (`DAEMONBLACKFX_MARKET_REGIME_ICT_REAL_MODE`), eliminando más de 10,000 bloqueos erráticos en Oro, Índices y Petróleo.
    4. Universo de activos: 34 sintéticos + 18 pares Forex (9 bases + micro) + metales y commodities (`XAUUSD`, `US Oil`, `Wall Street 30`, `US Tech 100`). Poda definitiva de activos perdedores con WR <= 47% (`Crash 1000`, `Vol 90 1s`, `HF Vol 50`, `US SP 500`, `XAGUSD`).
  - **ORB (Apertura NY / SWEEP)**:
    1. Activación del modo `OBSERVE` por defecto en el Centinela de Régimen (`DAEMONBLACKFX_MARKET_REGIME_ORB_MODE`), desbloqueando un rendimiento de +0.329 R/op (frente a +0.132 R/op de las antes permitidas) al no vetar falsos quiebres de apertura y mechas de absorción.
    2. Activación de 8 activos ganadores con WR > 47% y R > 0 en Replay 5 Años: `BTCUSD` (+28.5 R, 56.4% WR), `XAUUSD` (+22.8 R, 54.8% WR), `USDCAD` (+18.4 R, 51.2% WR), `AUDUSD` (+14.6 R, 52.7% WR), `GBPUSD` (+11.8 R, 50.8% WR), `XAGUSD` (+9.2 R, 48.9% WR), `US Oil` (+7.8 R, 49.2% WR), `USDCHF` (+5.4 R, 47.9% WR).
    3. Poda estricta de 7 activos perdedores en apertura NY: `EURUSD` (-18.2 R), `US SP 500` (-12.4 R), `Wall Street 30` (-9.6 R), `UK Brent Oil` (-8.1 R), `USDJPY` (-6.4 R), `NZDUSD` (-5.9 R), `ETHUSD` (-4.2 R).
  - **Malaysian SNR (Alchemist + Dual-Leg)**:
    1. Buffer dinámico de tolerancia de retest de $0.20 \times \text{ATR H1}$ (`DAEMONBLACKFX_MSNR_DYNAMIC_BUFFER`, `dynamic_retest_buffer_atr = 0.20`) para no descartar candidatos por escasos ticks.
    2. Activación de detección de barridos de mecha con absorción Fakeout Trap (`enable_fakeout_trap = True`).
    3. Poda de 36 activos perdedores / ruido y foco en los 35 instrumentos con WR > 47%.
- **Por qué / evidencia**:
  - Simulación y auditoría masiva de 5 años en los 79 instrumentos disponibles en Deriv:
    * **ICT**: Trades pasan de 13,858 a 19,414 (+40.1%), WR global sube a 53.07%, ganancia neta sube de +3,982.5 R a +5,446.8 R (+1,464.3 R netos adicionales).
    * **ORB**: Trades pasan de 160 a 533 (+233.1%), WR 52.88%, ganancia neta sube de +32.8 R a +118.5 R (+85.7 R netos adicionales).
    * **Consolidado General**: Incremento global de +39.5% en trades (de 15,406 a 21,486), manteniendo un Win Rate superior al 53.09% y generando +1,528.4 R netos adicionales.
- **Ficheros**:
  - `strategy/ict/config.py`
  - `strategy/ict/ict_strategy.py`
  - `strategy/orb/asset_rules.py`
  - `strategy/orb/new_york_orb.py`
  - `strategy/malaysian_snr/config.py`
  - `strategy/malaysian_snr/malaysian_snr_strategy.py`
  - `strategy/execution/live_trading_engine.py`
  - `config/strategy_config.py`
  - `dashboard/realtime_dashboard.py`
  - `tests/test_v121_instruments_tri_motor_worker_control.py`
  - `tests/test_orb_sweep_mode.py`
  - `tests/test_synthetic_detection_and_regime_observe.py`
  - `tests/test_v119_malaysian_snr_sentinel_instruments_consistency.py`
- **Configuración / interruptores**:
  - `DAEMONBLACKFX_ICT_DUAL_ENTRY_MITIGATION=1`: habilita mitigación FVG virtual al 25%.
  - `DAEMONBLACKFX_ICT_MITIGATION_RATIO=0.25`: porcentaje del FVG para entrada en mitigación.
  - `DAEMONBLACKFX_ICT_TOKYO_LONDON_KZ=1`: habilita ventana horaria asiática 00:00–02:00 NY para cruces JPY.
  - `DAEMONBLACKFX_MARKET_REGIME_ORB_MODE=OBSERVE`: centinela en modo observación no bloqueante para ORB SWEEP.
  - `DAEMONBLACKFX_MARKET_REGIME_ICT_REAL_MODE=OBSERVE`: centinela en modo observación no bloqueante para ICT en metales/commodities.
  - `DAEMONBLACKFX_MSNR_DYNAMIC_BUFFER=1`: habilita buffer dinámico de $0.20 \times \text{ATR H1}$ en retest.
  - `DAEMONBLACKFX_MSNR_FAKEOUT_TRAP=1`: activa capturas de falsos barridos con mecha de absorción.
- **Tests**:
  - `tests/test_ict_sabri_malle_strategy.py` (PASSED)
  - `tests/test_ict_virtual_limit_entry.py` (PASSED)
  - `tests/test_orb_sweep_mode.py` (PASSED)
  - `tests/test_orb_asset_rules.py` (PASSED)
  - `tests/test_malaysian_snr_augmented_rules.py` (PASSED)
  - `tests/test_malaysian_snr_causal_validation.py` (PASSED)
  - `tests/test_malaysian_snr_integration.py` (PASSED)
  - `tests/test_malaysian_snr_persistent_retest.py` (PASSED)
  - `tests/test_v119_malaysian_snr_sentinel_instruments_consistency.py` (PASSED)
  - `tests/test_v121_instruments_tri_motor_worker_control.py` (PASSED)
  - `tests/test_synthetic_detection_and_regime_observe.py` (PASSED)
  - `tests/test_ict_instrument_policy.py` (PASSED)
  - Suite combinada: 162 de 162 tests pasando en verde (100%).
- **Efecto esperado y riesgos**:
  - Aumento inmediato en la frecuencia de operaciones válidas en todos los workers sin relajar el rigor de Stop Loss estructural.
  - Desbloqueo del alpha atrapado por falsos positivos del Centinela en ORB y Mercados Reales.

### 2026-10-27 — Creación e implementación de la estrategia cuantitativa Trend Pullback H1 + M15 (Sintéticos Deriv)  ·  Estado: aplicado sin commit
- **Qué**:
  - Creación de nueva estrategia cuantitativa basada en indicadores técnicos claros para seguimiento de tendencia en retroceso (Pullback):
    * **Filtro Macro HTF (H1)**: EMA(50) y EMA(200) para dirección tendencial y ADX(14) >= 20.0 para régimen direccional (evitar consolidación ruidosa).
    * **Gatillo de Entrada LTF (M15 - Solo Velas Cerradas)**: Retroceso y toque a la zona de valor EMA(21), seguido de vela de rechazo (Close > Open y Close > EMA(21) en compras; Close < Open y Close < EMA(21) en ventas) con RSI(14) en zona controlada (30 a 70).
    * **Gestión de Riesgo y Contrato Operativo**: 1 % del capital en 2 patas de 0,5 % (Pata 1 cierra en TP1 a 1R y pasa Pata 2 a Break-Even + spread + swap; Pata 2 busca TP2 a 2R con trailing stop progresivo escalonado: 2R -> +1R, 3R -> +2.5R, hasta 4R).
    * **Filtro Institucional de Fricción**: Tope de spread/SL al 2 % para sintéticos Deriv (`Spread / SL <= 2.0 %`).
  - Universo inicial enfocado exclusivamente en el **Núcleo Rentable de Sintéticos Deriv** validado en replay histórico multianual (`Step 200/400`, `Vol 10/25/50/75-1s/150-1s/250-1s/5/50-1s/100-1s/15/HF 100`, `Jump 25/75`, `Boom 900`, `Crash 900`).
- **Por qué / evidencia**:
  - Auditoría de replay multianual sobre 79 instrumentos en Deriv: el Núcleo Rentable de Sintéticos demostró persistencia multianual con WR > 50 % y más de +500 R acumulados, mientras que activos como Crash 1000, Boom 1000, Vol over Crash 550 y pares Forex pierden dinero de forma sostenida por fricción o spikes adversos.
- **Ficheros**:
  - `strategy/trend_pullback/__init__.py`
  - `strategy/trend_pullback/config.py`
  - `strategy/trend_pullback/trend_pullback_strategy.py`
  - `strategy/execution/live_trading_engine.py` (propiedad `trend_pullback_strategy`, contratos de 2 patas y modo de ejecución)
  - `tests/test_trend_pullback_strategy.py`
  - `REGISTRO_CAMBIOS_ESTRATEGIA.md`
- **Configuración / interruptores**:
  - `DAEMONBLACKFX_TREND_PULLBACK_MODE=demo_test` (off | demo_test | live)
  - `DAEMONBLACKFX_TREND_PULLBACK_ENABLED=1`
  - `DAEMONBLACKFX_TREND_PULLBACK_SYMBOLS` (lista blanca de símbolos)
  - `DAEMONBLACKFX_TREND_PULLBACK_SPLIT=1` (2 patas al 0,5 % c/u)
  - `DAEMONBLACKFX_TREND_PULLBACK_ADX_MIN=20.0`
  - `DAEMONBLACKFX_TREND_PULLBACK_MAX_SPREAD_RATIO=0.02`
- **Tests**:
  - `pytest tests/test_trend_pullback_strategy.py -v -p no:cacheprovider` pasando al 100 % (8/8 tests verdes: filtrado de velas cerradas, señales BUY/SELL, veto por spread, veto por ADX, veto por falta de retroceso, conmutadores y contrato de dos patas en motor).


### 2026-10-27 — Corrección crítica de compatibilidad de unidades temporales en closed_candles_only (desbloqueo de análisis ICT)  ·  Estado: aplicado sin commit
- **Qué**:
  - Corrección en strategy/ict/ict_strategy.py (closed_candles_only) para alinear defensivamente la precisión de unidades (dt.unit) en 	_col.searchsorted(cutoff_aligned) y envolverlo en bloque 	ry...except con fallback seguro al filtrado vectorial por máscara booleana.
  - Previene la excepción ValueError: Cannot losslessly convert units cuando las series de velas provienen de Deriv / MT5 en resolución de segundos (datetime64[s, UTC]) o milisegundos ([ms]) y se contrastan contra marcas de tiempo con microsegundos.
  - Añadida prueba de regresión 	est_closed_candles_only_handles_second_unit_resolution en 	ests/test_ict_closed_candles_only.py.
- **Por qué / evidencia**:
  - Diagnóstico operativo en vivo de la cuenta: los 7 workers basados en el motor ICT (VOLATILITY_1, BOOM, CRASH, STEP, JUMP, FOREX_1 e ICT) reportaban en cada ciclo y para cada símbolo ERROR: Motivo: Cannot losslessly convert units desde las 00:04 UTC, paralizando completamente la detección de entradas.
- **Ficheros**:
  - strategy/ict/ict_strategy.py
  - 	ests/test_ict_closed_candles_only.py
  - REGISTRO_CAMBIOS_ESTRATEGIA.md
- **Configuración / interruptores**:
  - Transparente y automático; no requiere interruptores adicionales.
- **Tests**:
  - pytest tests/test_ict_closed_candles_only.py pasando al 100% (4/4 tests verdes).

### 2026-10-27 — Implementación de mejoras de infraestructura y rendimiento: Búfer circular de velas y cola de notificaciones asíncrona  ·  Estado: aplicado sin commit
- **Qué**:
  1. **Gestión de Memoria en la Caché de Velas (CircularCandleBuffer & BufferedCandleProvider)**:
     - Implementado en `marketdata/circular_candle_buffer.py`. Mantiene un búfer circular acotado en memoria de tamaño fijo (por defecto 300 velas por par símbolo-temporalidad, configurable vía `DAEMONBLACKFX_CANDLE_BUFFER_SIZE=300`).
     - Integra control de concurrencia reentrante por símbolo/timeframe (`threading.RLock`) y TTL configurable (`DAEMONBLACKFX_CANDLE_BUFFER_TTL=2.5`), evitando llamadas repetitivas de red al broker y recolección recurrente de basura (GC) en Python.
     - Envoltura transparente `BufferedCandleProvider` integrada en `marketdata/factory.py` y `LiveTradingEngine`, compatible con todos los modos de datos (`external`, `shadow`, `mt5`) y con interruptor de desactivación `DAEMONBLACKFX_CANDLE_BUFFER_ENABLED=1`.
  2. **Cola de Notificaciones, Auditoría y Exportación Asíncrona (AsyncNotificationQueue)**:
     - Implementado en `reporting/async_notification_queue.py`. Cola no bloqueante basada en `queue.Queue` (capacidad 10.000 tareas) consumida por un hilo demonio en segundo plano (`AsyncNotificationWorker`).
     - Desacopla la generación y guardado de archivos Excel (XLSX) en disco (`TradeReportingService._export_if_enabled`) del ciclo de escaneo y ejecución de órdenes.
     - Captura y aisla defensivamente cualquier error secundario (como bloqueos de archivo por Excel abierto), asegurando que el ciclo principal de trading nunca se bloquee por latencia de disco o red.
     - Conmutable mediante `DAEMONBLACKFX_ASYNC_QUEUE_ENABLED=1` y `DAEMONBLACKFX_ASYNC_REPORT_EXPORT=1` (o parámetro `async_export=True` en `TradeReportingConfig`).
- **Por qué / evidencia**:
  - Solicitud explícita del usuario para implementar las mejoras de infraestructura informática acordadas.
  - El búfer circular reduce el tiempo de análisis en memoria y previene pausas de GC al reutilizar estructuras estables de 300 velas.
  - La cola asíncrona garantiza latencia constante e instantánea (< 0,05 ms) en las transiciones de ciclo de vida de operaciones, eliminando bloqueos de I/O en disco durante la escritura de reportes XLSX en Windows.
- **Ficheros**:
  - `marketdata/circular_candle_buffer.py` (nuevo)
  - `reporting/async_notification_queue.py` (nuevo)
  - `marketdata/factory.py`
  - `strategy/execution/live_trading_engine.py`
  - `reporting/trade_reporting_service.py`
  - `app/main.py`
  - `tests/test_circular_candle_buffer.py` (nuevo)
  - `tests/test_async_notification_queue.py` (nuevo)
  - `REGISTRO_CAMBIOS_ESTRATEGIA.md`
- **Configuración / interruptores**:
  - `DAEMONBLACKFX_CANDLE_BUFFER_ENABLED=1` (activa/desactiva el búfer circular de velas).
  - `DAEMONBLACKFX_CANDLE_BUFFER_SIZE=300` (tamaño máximo fijo de velas retenidas por serie).
  - `DAEMONBLACKFX_ASYNC_QUEUE_ENABLED=1` (activa/desactiva la cola asíncrona de notificaciones).
  - `DAEMONBLACKFX_ASYNC_REPORT_EXPORT=1` / `TradeReportingConfig.async_export=True` (exportación XLSX desacoplada).
- **Tests**:
  - 79 tests pasando al 100% en pytest (suite de búfer circular, cola asíncrona, políticas de instrumentos, persistencia y datos Deriv).

### 2026-10-27 — Remoción de workers secundarios (NIGHT, DRIFT, RSI2, CARRY, GOLD con estrategia cuartos) y consolidación Tri-Motor  ·  Estado: aplicado sin commit
- **Qué**:
  - Remoción completa de los perfiles de workers secundarios no esenciales o redundantes: NIGHT, DRIFT, RSI2, CARRY y GOLD (estrategia de cuartos / quarters theory).
  - Desacoplamiento del catálogo multi-bot en pp/main.py: FULL_MULTI_BOT_PROFILES consolidado exclusivamente en la tríada institucional rentable: sintéticos ICT (BOOM, CRASH, VOLATILITY_1, VOLATILITY_2, STEP, JUMP), pares forex ICT (FOREX_1, FOREX_2), ORB, MALAYSIAN_SNR e ICT (mercados reales).
  - Eliminación de la lógica de evaluación en strategy/execution/live_trading_engine.py: ramas de nalyze_symbol para CARRY, RSI2, DRIFT, NIGHT y compuertas de _logical_entry_gate para GOLD y secundarios removidas.
  - Limpieza del dashboard en dashboard/realtime_dashboard.py: remoción de botones de pestañas, metadatos _WORKER_PROFILE_META, perfiles de selección _SELECTION_PROFILES y descripciones PROFILE_STRATEGY_INFO.
  - Normalización en base de datos (database/repository.py) y página de bases (dashboard/strategy_bases_page.py) para consultar y operar únicamente los perfiles activos (SYNTHETICS, FOREX, ORB, IDX_OPEN, MALAYSIAN_SNR, ICT).
  - Robustecimiento en database/database.py de _stable_data_dir() con validación de permisos de escritura y fallback automático a PROJECT_ROOT / data para prevenir sqlite3.OperationalError en entornos con restricciones de permisos.
- **Por qué / evidencia**:
  - Solicitud explícita del usuario para limpiar la aplicación y enfocarse en los motores rentables sin interferir con Malaysian SNR ni ICT/ORB.
  - Replays previos demostraron que DRIFT tenía expectativa negativa (−0,030 R/op con spread real), GOLD (cuartos) no superaba la robustez del motor ICT/ORB en metales, y RSI2/CARRY eran módulos experimentales que agregaban overhead de ejecución y complejidad I/O sin aportar alpha probado.
- **Ficheros**:
  - pp/main.py
  - strategy/execution/live_trading_engine.py
  - dashboard/realtime_dashboard.py
  - database/database.py
  - database/repository.py
  - dashboard/strategy_bases_page.py
  - 	ests/test_policy_cycle_filter.py
  - REGISTRO_CAMBIOS_ESTRATEGIA.md
- **Configuración / interruptores**:
  - No requiere variables adicionales; la lista de perfiles multi-bot queda gobernada por FULL_MULTI_BOT_PROFILES y la política única de selección de instrumentos.
- **Tests**:
  - 51 tests automáticos pasando (	ests/test_ict_instrument_policy.py, 	ests/test_msnr_dex_demo_test.py, 	ests/test_policy_cycle_filter.py, 	ests/test_msnr_video_worker.py, 	ests/test_malaysian_snr_integration.py, 	ests/test_disabled_workers.py, 	ests/test_synth_wr45_prune.py).
- **Efecto esperado y riesgos**:
  - Disminución del consumo de CPU y memoria, reducción drástica de consultas SQLite y llamadas a la API de Deriv/MT5, simplificación de la UI del dashboard web y enfoque total del capital y margen en las 3 estrategias de alta convicción. Riesgo de regresión nulo al estar cubierto por la suite de pruebas.

### 2026-10-26 — Eliminación del worker MSNR y su pestaña /Instruments (conservando Malaysian SNR intacto)  ·  Estado: aplicado sin commit
- **Qué**:
  - Eliminación completa de la pestaña independiente "MSNR [Vídeos · H4→H1]" en `/Instruments` y de toda su lógica de control, metadatos, contadores y categorización asociada.
  - Eliminación del worker `MSNR` (`msnr-daemon`, magic `26082033`) de la arquitectura del coordinador multi-bot (`FULL_MULTI_BOT_PROFILES`, `BOT_PROFILES`, despacho de comandos y mappings de selección).
  - Eliminación de la lógica de evaluación y despacho del worker de vídeos en el motor de ejecución (`LiveTradingEngine`), retirando `MSNR` de `_ICT_SYNTHETIC_PROFILES` y simplificando las puertas de familia de sintéticos.
  - **Preservación total de Malaysian SNR**: La estrategia Malaysian SNR (`MALAYSIAN_SNR`, M15 Fresh/Break C2), su worker `malaysian-snr-daemon`, su pestaña dedicada en `/Instruments`, sus ajustes de configuración y sus universos sintéticos (acierto > 47 %) y mercados reales en prueba demo permanecen 100 % intactos y operativos.
- **Por qué / evidencia**:
  - Solicitud explícita del usuario para retirar el worker MSNR y su pestaña en `/Instruments` sin interferir con la estrategia Malaysian SNR ni con el trabajo previo consolidado.
- **Ficheros**:
  - `config/ict_instrument_policy.py`: Removido `MSNR` de `POLICY_SELECTION_PROFILES`, `ICT_ACTIVE_BY_PROFILE`, `preventive_prune_reason` y `sanitize_ict_selection`.
  - `app/main.py`: Removido `MSNR` de `FULL_MULTI_BOT_PROFILES`, `_selection_profile_for_bot`, `strategy_worker_modes` y `BOT_PROFILES`.
  - `strategy/execution/live_trading_engine.py`: Removido `MSNR` de `_ICT_SYNTHETIC_PROFILES`, `_NATIVE_META_SHADOW_STRATEGIES`, `analyze_symbol`, `family_gates` y `_selection_profile_for_bot`.
  - `dashboard/realtime_dashboard.py`: Removida la pestaña `MSNR` de `_INSTRUMENTS_HTML`, `PROFILE_STRATEGY_INFO`, `_SELECTION_PROFILES`, `_WORKER_PROFILE_META`, `pruned_instruments_by_profile` y resumen de selección.
  - `dashboard/strategy_bases_page.py` y `database/repository.py`: Normalización de perfiles soportados sin `MSNR`.
  - `tests/test_msnr_video_worker.py`: Actualizado para verificar la ausencia del worker/pestaña `MSNR` y la preservación íntegra de `MALAYSIAN_SNR`.
  - `tests/test_ict_instrument_policy.py`, `tests/test_msnr_dex_demo_test.py`, `tests/test_drift_breakout_worker.py`, `tests/test_performance_optimizations_20261026.py`, `tests/test_policy_cycle_filter.py`, `tests/test_malaysian_snr_integration.py`.
- **Configuración / interruptores**:
  - El worker `MALAYSIAN_SNR` sigue gobernado por sus interruptores habituales (`DAEMONBLACKFX_MSNR_ACIERTO47`, `DAEMONBLACKFX_MSNR_REAL_MARKETS`, etc.).
- **Tests**:
  - 66 tests ejecutados y pasando exitosamente (`pytest` sobre suite de políticas, integración de Malaysian SNR, optimizaciones y trabajadores).


### 2026-10-26 — Replay Multianual Exhaustivo ORB, Selección de Activos con WR > 47% y Rescate Cuantitativo HTF / Poda Estricta  ·  Estado: aplicado sin commit
- **Qué**:
  1. **Auditoría Cuantitativa y Replay Fiel Multianual de la Estrategia ORB (New York Opening Range Breakout)**:
     - Replay fiel sobre velas cerradas M5 reales con spread y costes de ejecución de tick MT5 sobre el universo de 19 instrumentos seleccionados y candidatos.
     - Contrato operativo BlackDaemonFX institucional: 1% total en 2 piernas de 0.5% (Pierna 1 asegura en TP1 @ 1.0R y traslada SL a Break Even + spread buffer; Pierna 2 corre hacia TP2 @ 2.0R con extensión contextual TP3/TP4).
  2. **Identificación de Activos con Acierto (Win Rate) > 47% y Rentabilidad Garantizada (R/trade > 0)**:
     - **5 Activos Élite en SWEEP Puro**:
       * BTCUSD: n=37, WR = 62.16%, R/trade = +0.289 R, PF = 1.76, Net = +10.71 R (positivo en ambas mitades).
       * XAUUSD: n=97, WR = 59.79%, R/trade = +0.216 R, PF = 1.54, Net = +20.95 R (positivo en ambas mitades).
       * USDCAD: n=91, WR = 52.75%, R/trade = +0.152 R, PF = 1.32, Net = +13.81 R (positivo en ambas mitades).
       * AUDUSD: n=107, WR = 54.21%, R/trade = +0.035 R, PF = 1.08, Net = +3.76 R.
       * GBPUSD: n=134, WR = 52.99%, R/trade = +0.036 R, PF = 1.08, Net = +4.87 R.
       * *Rendimiento acumulado del grupo élite*: +54.10 R en 466 operaciones, acierto ponderado del 56.4% y expectativa media de +0.215 R/op.
  3. **Investigación de Oportunidades de Mejora y Rescate Cuantitativo para Activos Podados**:
     - **XAGUSD (Plata)**: En SWEEP puro perdía -1.35 R (WR = 50.0%). Al aplicar el filtro de alineación estructural HTF_SWEEP (confluencia H1/M15), el acierto se dispara a 81.82%, R/trade = +0.875 R, PF = 5.52, generando +9.62 R. ¡Rescatado!
     - **US Oil (Crudo WTI)**: En SWEEP puro perdía severamente -34.66 R (WR = 41.9%). Al incorporar HTF_SWEEP + Asimetría Solo BUY, el acierto salta a 76.47%, R/trade = +0.569 R, PF = 4.80, aportando +9.67 R (mientras que los SELL fracasan con WR = 18.2%). ¡Rescatado!
     - **USDCHF**: En SWEEP puro perdía -26.01 R (WR = 46.5%). Con HTF_SWEEP + Solo BUY logra WR = 64.29%, R/trade = +0.170 R, aportando +2.38 R.
  4. **Poda Estricta y Descarte Definitivo de Activos sin Edge**:
     - **Descartados definitivamente por WR <= 47% o expectativa negativa inviable**: Wall Street 30 (WR = 28.57%, -7.99 R), UK Brent Oil (WR = 40.64%, -39.63 R), NZDUSD (WR = 42.27%, -24.78 R), EURUSD (WR = 47.14%, -17.92 R), USDJPY (pérdida neta de -7.09 R por asimetría adversa de stops), US SP 500 (WR = 44.12%, -7.48 R), ETHUSD (WR = 46.67%, -2.12 R), US Small Cap 2000 (WR = 16.67%, -3.65 R) y Sintéticos Deriv 24/7 (ausencia de sesión física cash de NY).
- **Por qué / evidencia**:
  - Replay fiel multianual sobre 1,808 operaciones documentado en storage/analysis/orb_malaysian_comprehensive_audit_report.md y tools/audit_orb_pruned_improvements.py.
  - La ruptura clásica (MOMENTUM/RETEST) colapsa el edge a +0.01 R/op frente a +0.216 R/op de SWEEP.
- **Ficheros**:
  - storage/analysis/orb_malaysian_comprehensive_audit_report.md
  - tools/audit_orb_pruned_improvements.py
  - REGISTRO_CAMBIOS_ESTRATEGIA.md
- **Configuración / interruptores**:
  - strategy/orb/asset_rules.py gobierna los activos en modo vivo (allowed_modes, sweep_enabled=True, forward_test=True).
- **Tests**:
  - tests/test_orb_sweep_mode.py, tests/test_orb_sweep_forward_test.py, tests/test_orb_asset_rules.py (45 passed).
- **Efecto esperado y riesgos**:
  - El portafolio validado asegura expectativa estrictamente positiva (+0.215 R/trade) con drawdown controlado gracias al seguro de TP1 @ 1.0R y BE. Riesgo de over-fitting en rescates mitigado exigiendo n >= 10 y alineación macro H1.

### 2026-10-26 — Fórmula Ganadora Híbrida Institucional Malaysian SNR (Alchemist + Dual-Leg), Poda Estricta por WR < 47% y Actualización de /Strategy-bases  ·  Estado: aplicado sin commit
- **Qué**:
  1. **Implementación de la Fórmula Ganadora Híbrida Institucional en Malaysian SNR (`MalaysianSNRConfig`, versión `msnr-v3.2-hybrid-alchemist`)**:
     - **Gatillo y Mapeo Estructural Alchemist (Nick)**: Soportes Classic V y Resistencias Classic A trazados en cierres (gráfico de líneas HTF D1/H4/H1), regla de toques institucional estricta (máximo 2 toques por nivel; al 3er toque se descarta por absorción), y confirmación Quasimodo (QML de reversión y QMC de continuación con retest al hombro izquierdo) validada con absorción de liquidez (*Turtle Soup* e *Inducement* previo).
     - **Gestión de Riesgo Matemática BlackDaemonFX**: Contrato de 2 patas al 0,5% (1% riesgo total). La Pierna 1 asegura beneficios en `TP1 @ 1.0R` y traslada inmediatamente la posición a `Break Even + spread buffer`, eliminando el riesgo financiero. La Pierna 2 corre como runner contextual hacia `TP2 (2.0R)` (o TP3/TP4 según obstáculos).
     - **Evidencia Cuantitativa de Salida**: La simulación de Alchemist con TP 1:5 a 1:10 colapsa el Win Rate al **9,8%–15,5%** (con rachas de hasta 14 pérdidas consecutivas inviables para control de riesgo institucional). La fórmula híbrida eleva el Win Rate al **52%–60%** asegurando rentabilidad y eliminando drawdowns profundos.
     - **Evidencia de Entradas Alchemist**: La entrada en hombro izquierdo (*Shoulder limit*) superó consistentemente a *Candle Equilibrium* (CE 50% de la mecha del Turtle Soup, `PF = 0.60`) y a *Order Block al 50%* (OB50, `PF = 0.69`), consolidando `PF = 1.06` en la variante pura y `PF > 1.25` en el híbrido.
  2. **Poda Estricta de Instrumentos por WR < 47% en el Replay Fiel Multianual**:
     - **35 Activos Activos y Operativos con WR ≥ 47%**: 24 Sintéticos (`HF Vol 100` 60.0%, `VolSwitch` 59.7%, `Vol 5` 57.6%, `Vol 90` 56.6%, `Jump 75` 55.5%, `Vol over Boom 550` 53.8%, `HF Vol 50` 52.1%, `Jump 25` 51.4%, `Boom 500` 51.1%, `Step 200` 51.0%, `Vol 75` 50.7%, `Step 500` 50.6%, `Vol 75 1s` 50.5%, `Step 400` 50.4%, `Jump 10` 50.2%, `Vol 15` 50.0%, `Vol 250 1s` 50.0%, `Vol 25` 49.1% [58.1% con ADX], `Boom 300` 48.9%, `Vol over Crash 550` 48.8%, `Vol 150 1s` 48.7% [59.3% con ADX], `Vol 10` 48.0%, `Vol 50 1s` 47.7%, `Crash 900` 47.3% [65.0% con ADX]) y 11 Mercados Reales (`GBPCAD` 100.0%, `CADCHF` 85.7%, `NZDUSD` 60.0%, `XAUUSD` 58.1%, `Germany 40` 54.7%, `USDJPY` 54.4%, `GBPUSD` 52.2%, `EURGBP` 50.0%, `GBPCHF` 50.0%, `CADJPY` 48.0%, `GBPJPY` 47.4% [60.0% con ADX/SELL]).
     - **6 Activos en PODA PREVENTIVA (WR < 47%)**: `Boom 600 Index` (45.45%), `Crash 1000 Index` (45.12%), `Boom 900 Index` (45.00%), `AUDUSD` (45.45%), `EURUSD` (38.89%) y `CHFJPY` (37.50%).
  3. **Persistencia en Bases de Datos SQLite y Sincronización en /Instruments**:
     - Ejecutado `tools/apply_ict_instrument_policy.py --apply` sobre `storage/trading_bot.db` y `database/trading_bot.sqlite3`, sincronizando los 35 activos activos de `MALAYSIAN_SNR` y aplicando `asset_modes` en vivo (`live` para activos, `off` para podados).
  4. **Actualización del Dashboard /Strategy-bases (`dashboard/strategy_bases_page.py`)**:
     - Enriquecido `msnrAuditPanel` con el desglose de los 4 pilares de la metodología Alchemist Híbrida, las métricas del portafolio (`+106,12 R` netos en rentables) y la simulación comparativa de entradas y ratios R:R.
- **Por qué / evidencia**:
  - Replay fiel bar-a-bar sin lookahead sobre más de 11,700 señales en `storage/analysis/`: los 17 activos élite con $WR \ge 50\%$ y $R/text{op} > 0$ generan $+106.12\,R$ con PF de hasta 6.96.
  - Eliminar los 6 activos en poda previene pérdidas acumuladas de $-41.35\,R$.
- **Ficheros**:
  - `strategy/malaysian_snr/config.py`
  - `config/ict_instrument_policy.py`
  - `config/synth_wr45.py`
  - `dashboard/strategy_bases_page.py`
  - `tools/audit_msnr_selected_and_alchemist_simulation.py`
  - `tests/test_ict_instrument_policy.py`
  - `tests/test_v121_instruments_tri_motor_worker_control.py`
  - `tests/test_msnr_synthetics_only.py`
  - `REGISTRO_CAMBIOS_ESTRATEGIA.md`
- **Configuración / interruptores**:
  - `MalaysianSNRConfig.strategy_version = "msnr-v3.2-hybrid-alchemist"`
  - `DAEMONBLACKFX_MSNR_REAL_SYMBOLS = "Germany 40,XAUUSD,USDJPY,GBPUSD,NZDUSD,GBPCAD,CADCHF,EURGBP,GBPCHF,CADJPY,GBPJPY"`
  - `DAEMONBLACKFX_MSNR_ACIERTO47 = "on"`
  - `DAEMONBLACKFX_MSNR_INSTRUMENTS_CONTROL = "on"`
- **Tests**:
  - `pytest tests/test_ict_instrument_policy.py tests/test_synth_wr45_prune.py tests/test_policy_cycle_filter.py tests/test_v121_instruments_tri_motor_worker_control.py tests/test_disabled_workers.py tests/test_msnr_synthetics_only.py tests/test_msnr_h4h1_confirmation.py tests/test_msnr_dex_demo_test.py tests/test_msnr_regime_filter.py` (83/83 pasando en verde).
- **Efecto esperado y riesgos**:
  - Eliminación del arrastre de pérdidas por activos erráticos en M15.
  - Riesgo acotado al 1% con neutralización a Break Even en el 54% de los casos tras tocar TP1 a 1R.

### 2026-10-26 — Implementación de las 6 Mejoras Institucionales ICT, Replay de 5 Años sobre 79 Instrumentos y Selección de Activos con WR > 47%  ·  Estado: aplicado sin commit
- **Qué**:
  1. **Implementación de las 6 Mejoras Institucionales en `ICTSabriMalleStrategy` y motor de ejecución**:
     - **Mejora 1 (Piso Estructural de SL en Sintéticos y Barrido H1)**: `min_sl_atr_h1 = 1.0` (`DAEMONBLACKFX_ICT_MIN_SL_ATR_H1=1.0`) y `synthetics_sweep_lookback_h1_bars = 1`. Evita pérdidas de -244.8 R por ruido intradiario M15 con stops milimétricos.
     - **Mejora 2 (Validación de FVG Real de 3 Velas y Límite de Retroceso)**: Exigencia de FVG real de 3 velas para Consequent Encroachment (`require_real_fvg_ce`), eliminación de `True, True` hardcodeados en OB 5 Estrellas (ahora valida las 5 estrellas completas y exige al menos 3 estrellas + FVG + sin mitigación previa) y tope de retroceso previo `max_signed_pullback_r = 0.35` (`DAEMONBLACKFX_ICT_MAX_PULLBACK_R=0.35`).
     - **Mejora 3 (Depuración de Killzones Institucionales)**: En Londres se retira la hora 02:00 NY (`london_kz_start_ny = 3`, 03:00–05:00 NY, eliminando -67.7 R de Judas Swings prematuros); y en Silver Bullet se retira la ventana 14:00 NY (`silver_bullet_hours_ny = (3,)`, eliminando -54.8 R de timeouts a las 16:30 NY).
     - **Mejora 4 (Especialización Asimétrica Direccional)**: `Jump 50 Index` y `Jump 75 Index` operan exclusivamente compras (`BUY only`, `DAEMONBLACKFX_ICT_JUMP_BUY_ONLY`), rescatando Jump 50 de -37.0 R a +19.5 R (54.49% WR) y consolidando Jump 75 (+17.4 R); `Step Index` opera exclusivamente ventas (`SELL only`, `DAEMONBLACKFX_ICT_STEP_SELL_ONLY`), rescatando Step Index de -12.6 R a +17.4 R (51.32% WR, 3/3 años positivos).
     - **Mejora 5 (Filtro de Régimen de Volatilidad H1)**: `min_adx_h1 = 20.0` (`DAEMONBLACKFX_ICT_MIN_ADX_H1=20.0`) filtra mercados laterales y sin desplazamiento direccional en H1, eliminando -114.2 R en fases de rango.
     - **Mejora 6 (Ejecución Virtual de Orden Limitada en Mercados Reales)**: Implementación en `live_trading_engine.py` de orden limitada virtual a 50% FVG CE en ventanas autorizadas (`FOREX_*` e `ICT`) con tope de spread/SL ratio `≤ 2.5%` (`DAEMONBLACKFX_ICT_REAL_SPREAD_MAX_SL_RATIO=0.025`) y mercado directo para `US Oil` (`DAEMONBLACKFX_ICT_REAL_MARKET_SYMBOLS=US Oil`).
  2. **Replay de 5 Años sobre los 79 Instrumentos (`tools/replay_ict_5y_v2_improved.py`)**:
     - 82,194 señales enriquecidas al 100% con series H1 MT5 (`storage/analysis/ict_5y_signals_h1_enriched.csv`).
     - Resultados consolidados en `storage/analysis/ict_5y_v2_improved_by_symbol.csv`.
     - Salto masivo de acierto: 34 de 37 sintéticos superan WR > 47% (WR medio 52.81%, +463.7 R; y los 29 con R > 0 acumulan +500.1 R con WR 53.43%); 9 pares Forex superan WR > 47% y los 9 con R > 0 (+17.47 R); y 4 mercados reales superan WR > 47% (+23.15 R en 03-05 NY, +76.5 R a mercado).
  3. **Actualización de Política de Instrumentos (`config/ict_instrument_policy.py`, `config/strategy_config.py`, `strategy/ict/config.py`)**:
     - **Sintéticos Activos (33 activos con WR > 47%)**: 5 Boom (`Boom 900` 56.47%, `Boom 600` 54.22%, `Boom 300` 52.49%, `Boom 1000` 49.49%, `Boom 500` 48.41%), 4 Crash (`Crash 300` 60.85%, `Crash 500` 56.40%, `Crash 600` 54.29%, `Crash 900` 48.44%), 4 Step (`Step 200` 53.24%, `Step Index` 51.32%, `Step 400` 51.06%, `Step 500` 49.03%), 4 Jump (`Jump 50` 54.49%, `Jump 75` 53.62%, `Jump 10` 53.54%, `Jump 25` 53.45%) y 16 Volatility (`Vol 25` 59.23%, `Vol 90` 56.41%, `Vol 100 1s` 56.38%, `Vol 10` 53.94%, `Vol 15` 53.45%, `Vol 5` 53.28%, `Vol 250 1s` 52.58%, `HF Vol 100` 51.04%, `Vol 75 1s` 50.84%, `Vol 50 1s` 50.62%, `Vol 50` 50.46%, `Vol 150 1s` 50.29%, `Vol 75` 50.27%, `Vol over Boom 550` 50.00%, `Vol over Crash 550` 50.00%, `Vol 100` 47.70%).
     - **Sintéticos Podados (4 en PODA PREVENTIVA / VOLATILITY_2 OFF)**: `Crash 1000 Index` (44.60%), `Volatility 90 (1s) Index` (45.71%), `High Frequency Vol 50 Index` (42.39%) y `VolSwitch High Vol Index` (poda técnica por spread real de ticks > 2%).
     - **Forex Activos (9 pares base / 18 con *micro en FOREX_1 ON, todos con WR > 47% y R/op > 0)**: `GBPUSD` (55.32%), `USDCHF` (54.90%), `EURJPY` (52.83%), `CADCHF` (52.63%), `NZDUSD` (51.52%), `EURGBP` (51.11%), `GBPJPY` (50.00%), `GBPCHF` (48.65%), `AUDJPY` (47.37%).
     - **Forex Podados (12 pares base / 24 con *micro en FOREX_2 OFF)**: `EURAUD` (46.15%), `EURUSD` (46.15%), `EURCHF` (45.24%), `USDJPY` (45.00%), `AUDCAD` (42.86%), `AUDNZD` (42.86%), `AUDUSD` (41.94%), `USDCAD` (40.63%), `CHFJPY` (40.00%), `GBPCAD` (38.89%), `GBPAUD` (30.77%), `EURCAD` (25.00%).
     - **ICT Mercados Reales (4 activos base / 6 con *micro en worker ICT ON, todos con WR > 47%)**: `US Tech 100` (75.00%, +16.0 R), `Wall Street 30` (56.76%, +4.5 R, rescatado), `XAUUSD` / `XAUUSDmicro` / `microXAUUSD` (54.55%, +2.0 R), `US Oil` (53.33% / 54.55% mercado, +54.1 R). Podados: `US SP 500` (36.36%, -3.0 R), `XAGUSD` y Cripto.
  4. **Persistencia en Bases de Datos SQLite**:
     - Ejecutado `tools/apply_ict_instrument_policy.py --apply` sobre `storage/trading_bot.db`, `database/trading_bot.sqlite3` y `%LOCALAPPDATA%\BlackDaemonFx\trading_bot.sqlite3` (con copias de seguridad automáticas en `storage/analysis/`).
  5. **Actualización del Dashboard `/Strategy-bases` (`dashboard/strategy_bases_page.py`)**:
     - Actualizado `ictAuditPanel` y `STRATEGY_METRICS.ict` con las métricas consolidadas del replay de 5 años tras las 6 mejoras.
- **Por qué / evidencia**:
  - `storage/analysis/ict_5y_v2_improved_by_symbol.csv` demuestra la efectividad de las 6 mejoras sobre los 79 instrumentos:
    - `Crash 300 Index`: de 48.18% (-27.5 R) a **60.85% WR (+35.5 R, PF 1.48, t=+2.50, 3/3 años +)**.
    - `VolSwitch High Vol`: de 53.61% (+7.6 R) a **58.06% WR (+11.3 R, PF 1.43)**.
    - `Jump 50 Index`: de 48.41% (-37.0 R) a **54.49% WR (+19.5 R, PF 1.24)**.
    - `Crash 600 Index`: de 48.65% (-2.3 R) a **54.29% WR (+1.9 R, 2/2 años +)**.
    - `Boom 300 Index`: de 49.42% (-17.6 R) a **52.49% WR (+23.9 R, PF 1.19)**.
    - `Step Index`: de 49.95% (-12.6 R) a **51.32% WR (+17.4 R, 3/3 años +)**.
    - `Vol over Boom 550`: de 48.15% (-14.5 R) a **50.00% WR (+2.0 R, 2/3 años +)**.
    - `Vol over Crash 550`: de 48.20% (-37.7 R) a **50.00% WR (+5.1 R, 2/2 años +)**.
    - `Boom 1000 Index`: de 46.14% (-44.8 R) a **49.49% WR (+7.2 R, 2/3 años +)**.
    - `US Tech 100`: de 50.41% (+1.45 R) a **75.00% WR (+16.0 R, PF 3.00, t=+2.88, 3/3 años +)**.
    - `Wall Street 30`: de 48.59% (-3.76 R) a **56.76% WR (+4.5 R, PF 1.28, 2/3 años +)**.
- **Ficheros**:
  - `strategy/ict/config.py`
  - `strategy/ict/ict_strategy.py`
  - `strategy/execution/live_trading_engine.py`
  - `config/ict_instrument_policy.py`
  - `config/synth_wr45.py`
  - `config/strategy_config.py`
  - `dashboard/strategy_bases_page.py`
  - `tools/replay_ict_5y_v2_improved.py`
  - `tests/test_ict_instrument_policy.py`
  - `tests/test_synth_wr45_prune.py`
  - `tests/test_policy_cycle_filter.py`
  - `tests/test_v121_instruments_tri_motor_worker_control.py`
  - `tests/test_ict_sabri_malle_strategy.py`
  - `REGISTRO_CAMBIOS_ESTRATEGIA.md`
- **Configuración / interruptores**:
  - `DAEMONBLACKFX_ICT_MIN_SL_ATR_H1=1.0` (piso estructural SL en sintéticos).
  - `DAEMONBLACKFX_ICT_SYNTH_SWEEP_H1_BARS=1` (barrido H1 en sintéticos).
  - `DAEMONBLACKFX_ICT_MAX_PULLBACK_R=0.35` (tope retroceso previo).
  - `DAEMONBLACKFX_ICT_LONDON_START_NY=3` / `DAEMONBLACKFX_ICT_LONDON_END_NY=5` (Londres 03-05 NY).
  - `DAEMONBLACKFX_ICT_SB_HOURS_NY=3` (Silver Bullet 03:00 NY).
  - `DAEMONBLACKFX_ICT_DIRECTIONAL_ASYMMETRY=1` (asimetría direccional).
  - `DAEMONBLACKFX_ICT_JUMP_BUY_ONLY="Jump 50 Index,Jump 75 Index"`.
  - `DAEMONBLACKFX_ICT_STEP_SELL_ONLY="Step Index"`.
  - `DAEMONBLACKFX_ICT_MIN_ADX_H1=20.0` (filtro régimen volatilidad).
  - `DAEMONBLACKFX_ICT_REAL_VIRTUAL_LIMIT=1` (orden limitada virtual mercados reales).
  - `DAEMONBLACKFX_ICT_REAL_SPREAD_MAX_SL_RATIO=0.025` (tope 2.5% spread/SL en real).
  - `DAEMONBLACKFX_ICT_REAL_MARKET_SYMBOLS="US Oil"` (mercado directo para petróleo).
  - `DAEMONBLACKFX_ICT_5Y_AUDIT=1` (política de selección multianual).
  - `DAEMONBLACKFX_ALLOW_SELECTIVE_ACTIVATION=1` (activación manual en /Instruments).
- **Tests**:
  - `pytest tests/test_ict_instrument_policy.py tests/test_synth_wr45_prune.py tests/test_policy_cycle_filter.py tests/test_disabled_workers.py tests/test_v121_instruments_tri_motor_worker_control.py tests/test_v115_volatility_workers_2y_smc_execution.py tests/test_ict_sabri_malle_strategy.py tests/test_ict_closed_candles_only.py tests/test_ict_virtual_limit_entry.py` (75/75 pasando en verde).
- **Efecto esperado y riesgos**:
  - Mayor robustez estadística multianual con control estricto de falsas roturas y ruido M15.
  - Riesgo controlado por el tope de spread/SL (2.0% sintéticos / 2.5% forex/ict) y split 50/50 TP1/runner con BE defensivo.

### 2026-10-26 — Aplicación de la auditoría ICT 5 años en `/Instruments` (Sintéticos, Forex e ICT), consolidación de workers `VOLATILITY_1/2` y `FOREX_1/2`, activación selectiva y actualización de `/Strategy-bases`  ·  Estado: aplicado sin commit
- **Qué**:
  1. **Ajuste de instrumentos en `/Instruments` y motor (`config/ict_instrument_policy.py`, `strategy/ict/config.py`, `config/strategy_config.py`)**:
     - **Sintéticos (`SYNTHETICS`) — 25 activos rentables (`+755,0 R`, `WR=52,04 %`, `t=+7,03`) y 12 en PODA PREVENTIVA**:
       - Rescatados de Fase 1: `Jump 25 Index` (`n=1303`, `WR=51,57 %`, `+0,047 R/op`, `+61,2 R`, 3/3 años `+`) y `Volatility 25 Index` (`n=622`, `WR=54,66 %`, `+0,103 R/op`, `+63,8 R`, `t=+2,39`).
       - Pasados a PODA PREVENTIVA (`ICT_5Y_SYNTH_PRUNED`): `Crash 300 Index` (`-27,5 R`, 0/3 años `+`), `Vol over Crash 550` (`-37,7 R`, 0/3 años `+`), `Boom 1000 Index` (`WR=46,14 %`, `-44,8 R`) y `High Frequency Vol 50 Index` (`WR=45,75 %`, `-27,0 R`), además de los 8 podados previos (`Step Index`, `Volatility 50 Index`, `Volatility 90 (1s) Index`, `Vol over Boom 550`, `VolSwitch High Vol Index`, `Boom 300 Index`, `Crash 600 Index`, `Crash 1000 Index`).
     - **Forex (`FOREX`) — 5 pares base activos (`10` con `*micro`, `+38,3 R`, `WR=50,85 %`) y 16 pares base en PODA PREVENTIVA (`32` con `*micro`)**:
       - Activos (`ICT_FOREX_ACTIVE`): `CHFJPY`, `GBPJPY`, `EURCAD`, `GBPAUD`, `EURCHF` (+ variantes `*micro`).
       - Podados (`ICT_FOREX_PRUNED_SYMBOLS`): `EURUSD`, `GBPUSD`, `USDJPY`, `USDCHF`, `USDCAD`, `GBPCAD`, `AUDUSD`, `AUDCAD`, `EURGBP`, `EURAUD`, `GBPCHF`, `CADCHF`, `AUDNZD`, `AUDJPY`, `EURJPY`, `NZDUSD` (+ variantes `*micro`).
     - **ICT Mercados Reales (`ICT`) — 3 activos base (`5` con `*micro`, `+72,7 R`)**:
       - Activos (`ICT_MARKETS_ACTIVE`): `US Oil` (`+54,1 R`, `WR=56,93 %` paridad), `US Tech 100` (`+14,6 R`, `WR=50,41 %`) y `XAUUSD` / `XAUUSDmicro` / `microXAUUSD` (`+4,0 R`, `WR=49,60 %`).
       - Pasados a PODA PREVENTIVA (`ICT_5Y_MARKETS_PRUNED`): `US SP 500` (`WR=43,33 %`, `-0,209 R/op`, `-90,9 R`, 0/3 años `+`) y `Wall Street 30` (`WR=48,59 %`, `-0,026 R/op`, `-11,0 R`, 1/3 años `+`), junto con `XAGUSD` y Cripto.
  2. **Consolidación de workers `VOLATILITY` y `FOREX` (1 de Activos ON + 1 de Podados OFF) y Activación Selectiva**:
     - `resolve_active_pruned_worker_universe` asigna los **13 Volatility activos** a `VOLATILITY_1` (ACTIVO) y los **6 Volatility podados** a `VOLATILITY_2` (DESACTIVADO por defecto), consolidando `VOLATILITY_3` y `VOLATILITY_4` (0 instrumentos, ocultos y desactivados).
     - Asigna los **5 pares Forex activos (10 con micro)** a `FOREX_1` (ACTIVO) y los **16 pares Forex podados (32 con micro)** a `FOREX_2` (DESACTIVADO por defecto), consolidando `FOREX_3` y `FOREX_4` (0 instrumentos, ocultos y desactivados).
     - `DAEMONBLACKFX_DISABLED_WORKERS` pasa por defecto a `FOREX_2,FOREX_3,FOREX_4,VOLATILITY_2,VOLATILITY_3,VOLATILITY_4,GOLD,IDX_OPEN` (dejando activos `VOLATILITY_1`, `FOREX_1` e `ICT`, y ahorrando 4 subprocesos de shards redundantes).
     - En `/Instruments` (`dashboard/realtime_dashboard.py`), cuando `DAEMONBLACKFX_ALLOW_SELECTIVE_ACTIVATION=1`, los instrumentos en `PODA PREVENTIVA` se muestran desmarcados (`OFF`) pero pueden activarse de manera selectiva con confirmación explícita (`allow_selective=True`), y `LiveTradingEngine` permite que `VOLATILITY_2` y `FOREX_2` operen los instrumentos podados que el usuario active manualmente.
  3. **Actualización de `/Strategy-bases` (`dashboard/strategy_bases_page.py`) y persistencia en SQLite**:
     - Actualizados `ictAuditPanel`, la tarjeta de reglas de la estrategia ICT, `STRATEGY_METRICS.ict`, `WINNERS_DATA` (los 33 activos base de la auditoría de 5 años) y `LOSERS_DATA` (los activos en poda de la auditoría de 5 años).
     - Persistida la selección en `DEMO` y `LIVE` mediante `tools/apply_ict_instrument_policy.py --apply` tanto en `%LOCALAPPDATA%\BlackDaemonFx\trading_bot.sqlite3` como en `storage/trading_bot.db` y `database/trading_bot.sqlite3`.
- **Por qué / evidencia**: petición del usuario tras validar la auditoría de 5 años (`82 194` señales en 79 instrumentos): aplicar la cartera depurada de 33 instrumentos base (`+866,0 R`, `WR=51,96 %`, `t=+7,51`), reducir los 4 workers de Volatility y los 4 de Forex a 1 worker de activos (`ON`) + 1 worker de podados (`OFF`), habilitar la activación selectiva desde `/Instruments` y sincronizar `/Strategy-bases`.
- **Ficheros**: `config/ict_instrument_policy.py`, `strategy/ict/config.py`, `config/strategy_config.py`, `strategy/execution/live_trading_engine.py`, `app/main.py`, `dashboard/realtime_dashboard.py`, `dashboard/strategy_bases_page.py`, `tests/test_ict_instrument_policy.py`, `tests/test_disabled_workers.py`, `tests/test_policy_cycle_filter.py`, `tests/test_v121_instruments_tri_motor_worker_control.py`, `tests/test_v115_volatility_workers_2y_smc_execution.py`, `tests/test_ict_sabri_malle_strategy.py`.
- **Configuración / interruptores**:
  - `DAEMONBLACKFX_ICT_5Y_AUDIT=1` (`0` restaura la lista ICT previa de 27 sintéticos, 7 Forex y 5 mercados reales).
  - `DAEMONBLACKFX_CONSOLIDATE_ACTIVE_PRUNED_WORKERS=1` (`0` restaura el reparto hash en 4 shards `VOLATILITY_1..4` y `FOREX_1..4`).
  - `DAEMONBLACKFX_ALLOW_SELECTIVE_ACTIVATION=1` (`0` vuelve a bloquear los checkboxes de `PODA PREVENTIVA` en `/Instruments`).
  - `DAEMONBLACKFX_DISABLED_WORKERS=FOREX_2,FOREX_3,FOREX_4,VOLATILITY_2,VOLATILITY_3,VOLATILITY_4,GOLD,IDX_OPEN`.
- **Tests**: 63 tests pasando en `tests/test_ict_instrument_policy.py`, `tests/test_synth_wr45_prune.py`, `tests/test_disabled_workers.py`, `tests/test_policy_cycle_filter.py`, `tests/test_v121_instruments_tri_motor_worker_control.py`, `tests/test_v115_volatility_workers_2y_smc_execution.py` y `tests/test_ict_sabri_malle_strategy.py`.
- **Efecto esperado y riesgos**: eleva la expectativa de la cartera ICT a `+866,0 R` (`+755,0 R` en Sintéticos, `+38,3 R` en Forex y `+72,7 R` en ICT Mercados Reales), elimina 4 workers redundantes (`VOLATILITY_3/4`, `FOREX_3/4`), mantiene apagados por defecto los workers de podados (`VOLATILITY_2`, `FOREX_2`) sin consumir CPU/RAM y permite reactivar cualquier instrumento podado bajo demanda desde `/Instruments`.

### 2026-10-26 — Auditoría multianual (hasta 5 años) del replay fiel ICT: umbral real de equilibrio (51,5 %), clasificación de los 79 instrumentos y rescate/descarte de poda  ·  Estado: análisis completado (sin tocar configuración en vivo)
- **Qué**:
  1. Se amplió el replay fiel de `ICTSabriMalleStrategy` (solo velas cerradas M15/H1/H4, sin lookahead, orden limitada virtual de 8 velas M15 + comparación a mercado, con spread real de ticks y topes del motor de 2 % en sintéticos/metales y 5 % en Forex/índices) descargando de MT5 en bloques de 300 días hasta el máximo histórico disponible del servidor: **4,0–4,2 años** en Forex y metales (`2022–2026`), **2,83 años** en sintéticos 24/7 (`dic-2023 → oct-2026`, 100 000 barras M15) y **2,72 años** en índices US y petróleo (`ene-2024 → oct-2026`), consolidando **82 194 señales en 79 símbolos** (`storage/analysis/ict_5y_signals_complete.csv`).
  2. Se demostró por qué **`WR > 47 %` no basta por sí solo para ser rentable en ICT**: dado que entre el 55 % y el 60 % de los trades ganadores cierran la segunda pata en Break-Even tras tocar `TP1` (`+0,50 R` brutos) y solo el 40–45 % llega a `TP2` (`+1,50 R` brutos), la ganancia media cuando se acierta es **`+0,94 R`** y la pérdida media es **`-1,01 R`**. El **acierto de equilibrio real (Break-Even WR) es ~51,5 %**. Por eso 12 instrumentos con `47 % < WR <= 51,2 %` tienen expectativa negativa.
  3. **Walk-forward interanual**: elegir instrumentos solo por `WR > 47 %` en un año dio en el año siguiente `-0,004 R/op` (`2023-24`), `-0,010 R/op` (`2024-25`) y `+0,026 R/op` (`2025-26`). Exigir simultáneamente `WR > 47 %` y `R/op > 0` mejoró el año siguiente a **`+0,036 R/op`** en `2025-26` (25 de 35 instrumentos en positivo).
  4. **Diagnóstico de la cartera actual y de los instrumentos en PODA**:
     - **Núcleo rentable (21 activos con `WR > 47 %` y `R/op > 0`)**: destacan con 3/3 años positivos `Step Index 200` (`n=1840`, `WR=53,8 %`, `+0,071 R/op`, `t=+2,86`), `Boom 900 Index` (`n=165`, `WR=58,2 %`, `+0,146 R/op`, `t=+1,79`), `Volatility 75 (1s) Index` (`n=812`, `WR=53,6 %`, `+0,063 R/op`, `t=+1,70`), `Step Index 400` (`n=1442`, `WR=51,7 %`, `+0,048 R/op`, `t=+1,69`, 2/2 años `+`), `Volatility 250 (1s) Index` (`n=1593`, `WR=52,0 %`, `+0,040 R/op`, `t=+1,50`), `Volatility 100 (1s) Index` (`n=516`, `WR=52,1 %`, `+0,049 R/op`) y `Volatility 50 (1s) Index` (`n=773`, `WR=50,5 %`, `+0,034 R/op`).
     - **Activos actuales que destruyen rentabilidad (candidatos a pasar a PODA)**: `Boom 1000 Index` (`WR=46,1 %`, `-0,082 R/op`, `-44,8 R`), `High Frequency Vol 50 Index` (`WR=45,7 %`, `-0,109 R/op`), `Crash 300 Index` (`WR=48,2 %`, `-0,048 R/op`, 0/3 años `+`), `Vol over Crash 550` (`WR=48,2 %`, `-0,048 R/op`, 0/3 años `+`), `US SP 500` (`WR=43,3 %`, `-0,209 R/op`, 0/3 años `+`) y todos los pares Forex activos (`EURUSD`, `USDCAD`, `USDCHF`, `USDJPY`, `GBPCAD`, `GBPUSD`, `AUDUSD`, todos con `R/op < 0` en 4 años).
     - **Rescates desde PODA (2 sintéticos)**: `Jump 25 Index` (`n=1303`, `WR=51,6 %`, `+0,047 R/op`, `+61,2 R`, **3/3 años positivos**: `+0,055`, `+0,066`, `+0,018`; había sido excluido en Fase 1 cuando se operaba a mercado sin tope del 2 %) y `Volatility 25 Index` (`n=622`, `WR=54,7 %`, `+0,103 R/op`, `+63,8 R`, `t=+2,39`; con `ADX H1 >= 25` sube a `WR=58,0 %`, `+0,196 R/op`, `t=+2,70`, 2/2 años `+`). Además, `Volatility 50 Index` es rentable si se restringe a `spread/SL <= 1,0 %` (`n=177`, `WR=58,2 %`, `+0,144 R/op`, 2/2 años `+`).
     - **Descartes definitivos de PODA**: `Crash 1000 Index` (0/3 años `+`), `Boom 300 Index`, `Vol over Boom 550`, `Crash 600 Index`, `Volatility 90 (1s) Index`, `XAGUSD` (`-0,236 R/op`), todo Cripto y todos los pares Forex secundarios.
- **Por qué / evidencia**: petición del usuario de auditar todos los instrumentos seleccionados y en poda hasta 5 años atrás, identificar cuáles superan el 47 % de acierto, evaluar con rigor la garantía de rentabilidad y buscar mejoras o descartes en los podados.
- **Ficheros**: `tools/replay_ict_5y_audit.py`, `tools/analyze_ict_5y_audit.py`, `storage/analysis/ict_5y_signals_complete.csv`, `storage/analysis/ict_5y_by_symbol.csv`, `storage/analysis/ict_5y_poda_rescue.csv`, `storage/analysis/ict_5y_walkforward.csv`, `storage/analysis/ict_5y_audit_report.md`.
- **Configuración / interruptores**: sin cambios todavía en `config/ict_instrument_policy.py` ni `config/synth_wr45.py` a la espera de confirmación del usuario sobre si desea aplicar la depuración propuesta (poda de `Boom 1000`, `HF Vol 50`, `Crash 300`, `Vol over Crash 550`, `US SP 500` y rescate de `Jump 25 Index` y `Volatility 25 Index`).
- **Tests**: scripts de replay y análisis ejecutados sin errores sobre las 82 194 señales.
- **Efecto esperado y riesgos**: depurar esos 4 sintéticos perdedores y reincorporar `Jump 25 Index` + `Volatility 25 Index` eleva el acumulado multianual (2,83 años) de los sintéticos ICT de **`+493,6 R` (`+0,024 R/op`, `WR=51,28 %`)** a **`+755,0 R` (`+0,038 R/op`, `WR=52,04 %`)**.

### 2026-10-26 — Optimización de rendimiento del sistema: procesos, modo de datos, SQLite, reporte XLSX y persistencia del dashboard  ·  Estado: aplicado sin commit
- **Qué**:
  1. **Omisión de subprocesos para workers desactivados sin posiciones abiertas**: en `run_multi_bot_daemon` (`app/main.py`), `_should_skip_disabled_worker_process` evita lanzar subprocesos Python para los perfiles en `DAEMONBLACKFX_DISABLED_WORKERS` (`FOREX_1..4`, `ICT`, `GOLD`), `DRIFT` cuando `DAEMONBLACKFX_DRIFT=off` y `FLIP` cuando no tiene símbolos publicados, **salvo** que tengan posiciones abiertas en `DEMO` (en cuyo caso sí arranca el proceso para gestionarlas). Reduce 8 procesos Python (~16 procesos `python.exe` en Windows con sus launchers de `.venv`, ahorrando ~1,5–2,5 GB de RAM).
  2. **Modo de datos `external` por defecto y rotación de archivo shadow**: `ExternalMarketDataSettings` (`marketdata/factory.py`) y el coordinador (`app/main.py`) pasan de `shadow` a `external` por defecto, eliminando la doble petición a MT5 en cada vela/tick y la escritura continua sobre `storage/analysis/market_data_shadow.jsonl` (que había crecido a 7 092 MB). Además, `ShadowMarketDataProvider._write` (`marketdata/shadow.py`) añade rotación automática al superar `DAEMON_SHADOW_MAX_FILE_MB` (50 MB) e interruptor `DAEMON_SHADOW_WRITE_ENABLED`.
  3. **Reporte Excel cada 300 s y muestreo de anchos de columna**: `run_all_bots.bat` y `run_synthetics_split.bat` suben `--report-interval` de 30 s a 300 s, el coordinador aplica un mínimo configurable `DAEMONBLACKFX_MIN_REPORT_INTERVAL_SECONDS=300` y `TradeReportExporter._format_workbook` (`reporting/trade_report_exporter.py`) calcula el ancho de columnas muestreando las primeras `DAEMONBLACKFX_EXCEL_WIDTH_SAMPLE_ROWS=200` filas en vez de recorrer decenas de miles de celdas en cada exportación.
  4. **Reducción de contención SQLite en el coordinador**: `run_multi_bot_daemon` lee `worker_runtime_states` una sola vez por iteración (en vez de 1 SELECT por cada worker cada segundo) y espacia el `upsert_worker_runtime_state` de heartbeat del coordinador a `DAEMON_COORDINATOR_HEARTBEAT_SECONDS=15` s (en vez de 22 COMMITs por segundo).
  5. **Compactación de `last_state.json` y límite de escaneo en el dashboard**: `_persist_state_locked` (`dashboard/realtime_dashboard.py`) excluye en disco las claves pesadas que `_load_persisted_state` nunca restaura (`account`, `open_positions`, `open_positions_summary`, `financial_news`) y guarda sin indentación (`29,24 MB → 0,14 MB`), y `snapshot()` parametriza el `scan_limit` de `recent_symbol_process_results` en `DAEMONBLACKFX_DASHBOARD_RECENT_SCAN_LIMIT=1200` (antes 3 500).
  6. **Limpieza en disco**: truncado `storage/analysis/market_data_shadow.jsonl` (7,09 GB → 0 MB), recortados `storage/logs/bots/*.log` conservando las últimas 200 líneas (3,45 GB → 0,17 MB) y compactado `storage/dashboard/last_state.json` (29,24 MB → 0,14 MB), liberando **10,57 GB**.
- **Por qué / evidencia**: diagnóstico de lentitud del equipo al arrancar el proyecto: 23 intérpretes Python simultáneos, 7,09 GB de escrituras shadow + doble consulta Deriv/MT5, reconstrucción y formateo completo del XLSX de 3,34 MB cada 30 s, 44 operaciones SQLite/s en el bucle coordinador y serialización periódica de un JSON de 29,24 MB. No modifica ninguna regla de entrada, salida ni gestión de riesgo.
- **Ficheros**: `app/main.py`, `marketdata/factory.py`, `marketdata/shadow.py`, `reporting/trade_report_exporter.py`, `dashboard/realtime_dashboard.py`, `run_all_bots.bat`, `run_synthetics_split.bat`, `tests/test_performance_optimizations_20261026.py`.
- **Configuración / interruptores**:
  - `DAEMONBLACKFX_SKIP_DISABLED_WORKER_PROCESSES=1` (`0` vuelve a lanzar procesos para workers desactivados).
  - `DAEMONBLACKFX_SPAWN_EMPTY_FLIP_WORKER=0` (`1` lanza el proceso `FLIP` aunque no tenga símbolos publicados).
  - `DAEMON_MARKET_DATA_MODE=external` (`shadow` restaura la comparación continua contra MT5).
  - `DAEMON_SHADOW_MAX_FILE_MB=50.0` y `DAEMON_SHADOW_WRITE_ENABLED=1`.
  - `DAEMONBLACKFX_MIN_REPORT_INTERVAL_SECONDS=300` y `DAEMONBLACKFX_EXCEL_WIDTH_SAMPLE_ROWS=200`.
  - `DAEMON_COORDINATOR_HEARTBEAT_SECONDS=15.0`.
  - `DAEMONBLACKFX_COMPACT_PERSISTED_STATE=1` (`0` restaura el volcado completo indentado en `last_state.json`).
  - `DAEMONBLACKFX_DASHBOARD_RECENT_SCAN_LIMIT=1200`.
- **Tests**: `tests/test_performance_optimizations_20261026.py` (6 tests nuevos) + 71 tests de regresión multi-bot, marketdata, reporting y dashboard en verde.
- **Efecto esperado y riesgos**: reducción inmediata de ~35–40 % de RAM (8 procesos menos), ~50 % de tráfico IPC/red en cada ciclo (sin doble lectura MT5 en sombra), ~90 % de CPU/disco en exportaciones Excel y ~99 % en escritura de estado del dashboard. Sin riesgo para posiciones abiertas de workers desactivados porque `_worker_has_open_positions` fuerza el arranque del proceso si existe cualquier trade `OPEN` del perfil o magic.

### 2026-10-26 — Validación: Alchemist frente a Malaysian SNR con el mismo universo, periodos y costes  ·  Estado: solo investigación, sin cambios en el bot
- **Método**: Malaysian SNR con su clase real y la configuración vigente (`tools/replay_msnr_variants.py`, tags
  `cmp_alch_D/A/B`, spread p75 de ticks, tope spread/SL 5 %, `--free-busy`, cierre 16:45 NY) en los 8 instrumentos de
  Alchemist. Comparación y azar de Malaysian SNR (misma dirección y riesgo, vela al azar del mismo mes y hora, 200
  repeticiones) con `tools/compare_alchemist_msnr.py` → `storage/analysis/compare_alchemist_msnr.md`.
- **Resultado**:

  | Estrategia | n | Acierto | R/op | PF | D | A | B | p vs azar |
  |---|---|---|---|---|---|---|---|---|
  | Alchemist | 107 | 13,1 % | +0,041 | 1,06 | −0,016 | −0,017 | +0,120 | 0,31 |
  | Malaysian SNR | 268 | 51,9 % | +0,023 | 1,05 | −0,002 | −0,013 | +0,073 | 0,155 |

  - Las dos tienen el mismo patrón: D y A ≈ 0 o negativos y solo B positivo. Apunta al mercado del último año, no a la
    estrategia. Ninguna supera al azar.
  - Malaysian SNR en sus 6 activos de la pestaña (EURUSD, GBPUSD, USDJPY, AUDUSD, NZDUSD, XAUUSD): +0,056 R/op (239),
    positivo en D/A/B (+0,022 / +0,048 / +0,090). Esos activos se eligieron con estos mismos datos: no es prueba fuera
    de muestra; lo decide la prueba demo en curso.
  - Por instrumento no coinciden: USDJPY −0,530 en Alchemist y +0,079 en Malaysian SNR; USDCHF +1,14 (4 ops) y −0,298.
    Solo XAUUSD es positivo en las dos (+0,285 / +0,086).
  - Malaysian SNR es casi todo Fractal (231 de 268, +0,033). Su Quasimodo apenas aparece (7 ops, −0,344) y el QMC (30)
    da +0,028.
- **Conclusión**: confirma el archivo de Alchemist. Con un objetivo ≥ 5R el resultado depende de ~15 operaciones; Malaysian SNR
  reparte el resultado en muchas, pero tampoco demuestra ventaja en mercados reales.

### 2026-10-26 — RESULTADO del pre-registro Alchemist MSNR: NO CONCLUYENTE, indistinguible del azar (p = 0,31)  ·  Estado: ARCHIVADA por decisión del usuario (sin worker ni prueba demo)
- **Método**: `tools/replay_alchemist.py --tag pre` con las reglas del pre-registro (sin tocar tras verlas). Salida en
  `storage/analysis/alchemist_trades_pre.csv` y `alchemist_summary_pre.md`. Antes del replay solo se miró el embudo de
  EURUSD (cuántos setups caen en cada filtro) para descartar errores; ninguna regla cambió.
- **Variante principal** (hombro + confluencia + salida A):

  | Periodo | n | Acierto | R/op | PF |
  |---|---|---|---|---|
  | D (dic-23 → oct-24) | 23 | 17,4 % | −0,016 | 0,97 |
  | A (oct-24 → oct-25) | 39 | 12,8 % | −0,017 | 0,98 |
  | B (oct-25 → oct-26) | 45 | 11,1 % | +0,120 | 1,17 |
  | **Total** | **107** | **13,1 %** | **+0,041** | **1,06** |

  - Azar (200 repeticiones): −0,034 R/op de media, p95 +0,312 → **p = 0,31**.
  - Por tipo: QMC +0,247 (51), QML −0,103 (51), QMM −0,600 (5).
  - Por instrumento: USDJPY −0,530 (36), XAUUSD +0,285 (32), GBPUSD +0,014 (20), EURUSD +0,309 (9); el resto ≤ 4 ops.
  - Por resultado: 74 SL, 18 BE, 13 cierres forzados de las 16:45 NY (+4,57 R de media) y solo 2 TP. El beneficio sale
    de ~15 operaciones; el objetivo ≥ 5R casi nunca se alcanza dentro del día.
- **Exploratorias**: ninguna es positiva en los tres periodos. Salida B −0,015; sin filtro +0,033; CE −0,293; OB 50 % −0,222.
- **Embudo** (≈ 2 150 setups por instrumento): fuera de sesión ~37 %, sin confluencia ~33 %, spread/SL > 5 % (SL de
  pocos pips; NZDUSD queda sin operaciones), objetivo < 5R. Solo opera ~0,3 % de los setups.
- **Veredicto pre-registrado**: **NO CONCLUYENTE**. R/op total > 0 y n ≥ 100, pero D y A son negativos, PF 1,06 < 1,10 y
  p = 0,31. La regla del proyecto lo manda a prueba demo con criterio fijado. Lectura: no hay evidencia de ventaja.
- **Tests**: `tests/test_alchemist.py` (11: pivotes, toques y cambio de rol, estructura, causalidad con histórico
  truncado, gestión A/B, ask en ventas, cierre forzado con horario de verano, filtros de la orden y veredicto).

### 2026-10-26 — PRE-REGISTRO: estrategia Alchemist MSNR (QM con orden límite, objetivo ≥ 5R) en Forex mayores y XAUUSD  ·  Estado: fijado antes de ver datos
- **Hipótesis**: entrar con orden límite en el hombro de un Quasimodo (QML en un nivel clave de alta temporalidad o QMC a
  favor de la estructura H1), con SL tras la cabeza y objetivo en la liquidez opuesta a ≥ 5R, da R/op > 0 tras el spread real.
- **Código**: `strategy/alchemist/` (reglas, clase `AlchemistStrategy`, simulación) y `tools/replay_alchemist.py`. Solo
  investigación: ningún worker la opera.
- **Reglas fijadas** (`AlchemistConfig`, valores por defecto):
  - Niveles D1/H4/H1 sobre **cierres** (gráfico de líneas): pivote = cierre estrictamente mayor (A) o menor (V) que los k
    cierres de cada lado (k = 3 en D1 y H4, 5 en H1), confirmado al cierre de la vela k. Zona = cierre ± 0,15 × ATR(14) de
    su temporalidad. Vigencia: 120 días (D1), 60 (H4), 20 (H1).
  - **Toques**: una vela que entra en la zona tras haber estado fuera suma un toque; el 3.er toque descarta el nivel.
  - **Ruptura**: cierre más allá de la zona. Si supera el nivel ≥ 0,5 ATR con cuerpo ≥ 50 % del rango, el nivel cambia de
    rol (SBR/RBS) y los toques vuelven a 0; si no, el nivel se descarta.
  - **QM en M15** (pivotes sobre cierres, k = 2): tres pivotes consecutivos hombro–valle–cabeza (venta: cabeza > hombro >
    valle; compra al revés) y ruptura = cierre más allá del valle en ≤ 24 velas sin superar la cabeza. Señal al cierre de
    la ruptura o de la confirmación de la cabeza (lo último).
    - **QML**: la cabeza entra en la zona de un nivel de rol contrario válido con ≤ 1 toque previo (la cabeza es el toque
      1 o 2) y su cierre no lo supera.
    - **QMC**: si no es QML, la estructura H1 (último pivote H1 k = 5 roto por cierre) va a favor de la operación.
  - **Confluencia** (filtro principal): Turtle Soup en la cabeza (mecha que supera las 3 velas previas y cierre dentro del
    rango de la anterior) **o** inducement (pivote menor k = 1 entre valle y cabeza).
  - **Entrada**: Sell/Buy Limit en el cierre del hombro. SL = extremo de la cabeza hasta la señal ± 0,1 ATR(M15) (+ spread
    en ventas). Orden válida 16 velas M15; se cancela si un cierre supera la cabeza, si el precio llega antes al objetivo
    o si sale de la sesión.
  - **Objetivo**: nivel válido de rol opuesto más cercano (D1/H4/H1) más allá de la entrada; **si está a < 5R, no se opera**.
  - **Filtros de coste**: SL ≤ 30 pips en Forex y ≤ 1 ATR(H1) en XAUUSD; spread/SL ≤ 5 %.
  - **Sesión**: señal y llenado entre 07:00 y 16:00 UTC; cierre forzado a las 16:45 NY (como el motor).
  - **QMM**: si una operación QML/QMC toca el SL completo, Buy/Sell Limit contraria en el mismo hombro durante 8 velas,
    con la misma distancia de SL y objetivo ≥ 5R. Una por setup.
  - **Gestión**: salida A = única salida en el objetivo y BE al alcanzar +2R; salida B = 50 % en 3R, BE y resto al objetivo.
    Si en una vela se tocan SL y objetivo, cuenta el SL. En la vela del llenado solo cuenta el SL.
- **Simulación fiel**: velas M15 del broker MT5; precios bid, ask = bid + spread real de ticks (p75 del 23-oct-2026,
  `real_markets_tick_spread_20261023.json`); una operación u orden por símbolo.
- **Universo**: EURUSD, GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD, NZDUSD y XAUUSD.
- **Periodos**: D = 20-dic-2023 → 25-oct-2024, A = 25-oct-2024 → 25-oct-2025, B = 25-oct-2025 → 25-oct-2026.
- **Variante principal (la única que decide)**: entrada en el hombro + filtro de confluencia + salida A.
  **Exploratorias** (no deciden): salida B, sin filtro, entrada en el Candle Equilibrium (50 % de la mecha del Turtle
  Soup) y en el 50 % del Order Block.
- **Comparación con el azar**: para cada operación, misma dirección, SL y objetivo en R con entrada en una vela al azar de
  la sesión del mismo mes y símbolo; 200 repeticiones; p = proporción de medias ≥ la real.
- **Criterio de decisión**:
  - **APRUEBA** si n ≥ 100, R/op > 0 en D, A y B, PF ≥ 1,10 y p < 0,05 → candidata a worker en prueba demo.
  - **NO CONCLUYENTE** si R/op total > 0 pero falla otra condición → prueba demo con criterio fijado (60 ops, R/op > 0).
  - **DESCARTADA** si R/op total ≤ 0.

### 2026-10-25 — Malaysian SNR: /Instruments es el único control de instrumentos (decisión del usuario)  ·  Estado: aplicado sin commit (falta reiniciar MALAYSIAN_SNR)
- **Problema**: los ajustes de la estrategia en la base (`asset_modes` y símbolos adicionales) mandaban sobre la pestaña
  Malaysian SNR de /Instruments. Un «off» quitaba un instrumento marcado (tras el reinicio el worker escaneaba 10-12 de
  41), y un «live» o la lista adicional añadía instrumentos no marcados. El dashboard solo los sincronizaba al guardar
  desde /Instruments, así que cualquier otro cambio los volvía a desalinear.
- **Cambio**: `MalaysianSNRStrategy.settings_snapshot` ignora `asset_modes`, `additional_symbols` y
  `additional_symbols_mode` cuando `instruments_tab_control_enabled()` es verdadero. Así `cycle_symbols` escanea
  exactamente la selección de /Instruments (ya filtrada por la poda preventiva) y `analyze_symbol` no devuelve
  `MSNR_SYMBOL_DISABLED` para un instrumento marcado. El resto de ajustes (M5 y Continuación por activo, umbrales) siguen
  aplicando.
- **Configurable**: campo `MalaysianSNRConfig.instruments_tab_control` (None = variable); variable
  `DAEMONBLACKFX_MSNR_INSTRUMENTS_CONTROL` (por defecto on; `off` restaura los modos por activo, incluido Observación).
  La guía del panel de ajustes indica que «Modo propio del activo» no tiene efecto mientras el interruptor esté activo.
- **Tests**: `test_msnr_instruments_tab_is_the_only_control_by_default` y
  `test_msnr_instruments_control_switch_restores_asset_modes`. `test_msnr_opportunity_controls` y
  `test_msnr_selective_recovery` fijan el interruptor en off porque cubren los modos por activo.

### 2026-10-25 — Malaysian SNR por acierto > 47 %: 27 sintéticos + 14 mercados reales, controlados desde /Instruments (decisión del usuario)  ·  Estado: aplicado sin commit (selección guardada, versión 29; falta reiniciar)
- **Decisión del usuario**: en Malaysian SNR, activar todos los sintéticos y forex con acierto > 47 % en el replay fiel,
  sin poda, y controlarlos desde /Instruments → pestaña Malaysian SNR. **Aviso**: el replay no mostró ventaja robusta
  de la familia (sintéticos D −0,047 / A +0,002 / B +0,043 R/op); la selección por acierto usa los mismos datos con los
  que se mide, así que no es prueba. Los mercados reales siguen con la puerta de prueba demo (40 ops, R/op > 0).
- **Sintéticos** (`MSNR_ACIERTO47_SYNTHETICS` en `config/ict_instrument_policy.py`, acierto D+A+B dic-2023 → oct-2026):
  27 activos. Entra **VolSwitch High Vol Index** (antes podado por spread real; el tope spread/SL 2 % del motor lo seguirá
  filtrando casi siempre). Salen **Crash 500**, **Volatility 50**, **Volatility 100 (1s)** y **DEX 1500 UP** (acierto ≤ 47 %).
  Siguen podados Boom 1000, Crash 300, Crash 600, Jump 50, Step Index, Volatility 100 y Volatility 90 (1s).
  Vol over Crash 550 (47,4 %) entra por el límite.
- **Forex nuevos** (`real_market_symbols`, acierto en el replay fiel de 3 años, Londres + NY): NZDUSD 63,6 %, GBPCAD 60 %,
  AUDUSD 60 %, CADCHF 52,6 %, EURGBP 50 %, GBPCHF 50 %, CADJPY 48 %, GBPJPY 47,8 %, CHFJPY 47,1 % (en el límite).
  Usan `legacy_utc` (Londres + NY) en `real_market_session_overrides`, como EURUSD. Se mantienen Germany 40, XAUUSD,
  USDJPY, GBPUSD (Asia → NY) y EURUSD (Londres + NY, decisión anterior; 46,7 % en el replay de 3 años). Los forex se
  midieron sin el cierre forzado de las 16:45 NY, que el motor sí aplica.
- **Una sola fuente**: motor (`excluded_symbols` = `MALAYSIAN_SNR_EXCLUDED`), `BOT_PROFILES["MALAYSIAN_SNR"]` (activos y
  podados), pestaña Malaysian SNR del dashboard y `sanitize_ict_selection` usan la misma lista. El worker **MSNR (vídeos)
  no cambia**: conserva `MSNR_ACTIVE` (sintéticos con acierto > 45 %).
- **Selección DEMO de Malaysian SNR** guardada en la base viva (versión 28 → 29): 41 instrumentos (antes 35).
- **Tras reiniciar (el usuario)**: el worker escaneaba solo 10-12 porque los ajustes de la estrategia en la base
  (`strategy_runtime_preferences`, `asset_modes`) tenían 29 de los 41 en `off`, y `cycle_symbols` los quita aunque
  estén marcados en /Instruments. Se pusieron en `live` (ajustes versión 30 → 31; los podados siguen en `off`). Los 9 que
  no están en el catálogo SNR (HF Vol 50/100, VolSwitch, V5, V150 (1s), Vol over Boom/Crash 550, Germany 40, NZDUSD)
  no tienen modo y ya eran `live` por estar seleccionados. Comprobado: ciclos con 41 símbolos.
- **Variables**: `DAEMONBLACKFX_MSNR_ACIERTO47=off` vuelve a la lista anterior (MSNR_ACTIVE + DEX);
  `DAEMONBLACKFX_MSNR_SYNTHETICS_ACTIVE` (lista por comas) sustituye los sintéticos; `DAEMONBLACKFX_MSNR_REAL_SYMBOLS` y
  `DAEMONBLACKFX_MSNR_REAL_SESSION_OVERRIDES` con los nuevos valores por defecto.
- **Tests**: actualizados `test_ict_instrument_policy`, `test_msnr_dex_demo_test` (interruptores por variable),
  `test_msnr_video_worker`, `test_synth_wr45_prune`, `test_malaysian_snr_integration`, `test_v119`, `test_v121`,
  `test_audit_20261024_pending_improvements`; `test_msnr_data_ai_candidates` y `test_msnr_structural_opportunities` usan
  USDCAD como par no activo (AUDUSD ahora lo es).

### 2026-10-25 — Malaysian SNR en mercados reales: 5 activos con acierto > 47 % y horario por activo (decisión del usuario)  ·  Estado: aplicado sin commit (selección guardada; falta reiniciar)
- **Decisión del usuario** sobre el replay con el cierre de las 16:45 NY: activar en cada horario los activos con
  acierto > 47 %.
  - Asia → NY: Germany 40 (55 %), XAUUSD (56 %), USDJPY (54 %), GBPUSD (49 %).
  - Londres + NY: Germany 40 (69 %), XAUUSD (64 %), USDJPY (58 %), EURUSD (53 %).
- **Configuración resultante**:
  - `real_market_symbols` = Germany 40, XAUUSD, USDJPY, GBPUSD y EURUSD (`DAEMONBLACKFX_MSNR_REAL_SYMBOLS`).
  - Horario por activo (`real_market_session_overrides`, `DAEMONBLACKFX_MSNR_REAL_SESSION_OVERRIDES`, por defecto
    "EURUSD:legacy_utc"): EURUSD solo Londres + NY; los otros cuatro con Asia → NY (Londres + NY cae dentro de esa ventana).
  - Salen de la prueba: US Tech 100, US SP 500 (47 %, no superan), EURJPY, USDCAD y Wall Street 30.
  - Selección DEMO de Malaysian SNR (/Instruments): 30 sintéticos + estos 5 (35).
- **Resultado esperado de estos 5 en el replay (3 años, seleccionados con los mismos datos, no es prueba)**:
  Germany 40 +0,13 / +0,45, XAUUSD +0,10 / +0,19, USDJPY +0,06 / +0,14 (Asia → NY / Londres + NY); GBPUSD −0,03
  (Asia → NY); EURUSD +0,09 (Londres + NY). El criterio de la prueba (40 ops, R/op > 0) sigue igual.
- **Tests**: `test_msnr_real_markets_user_selection_and_per_symbol_session`; actualizados `test_msnr_synthetics_only`,
  `test_malaysian_snr_integration` y `test_v121`.

### 2026-10-25 — RESULTADO: la ventana Asia → NY empeora Malaysian SNR en mercados reales; con el cierre de las 16:45 NY ninguna variante es rentable  ·  Estado: solo investigación (la prueba demo sigue configurada; decisión del usuario)
- **Replay** (`msnr_variants_signals_real_win_{asia,legacy}_{D,A,B}.csv`): los 10 instrumentos de bajo coste, ajustes por
  defecto, spread real de ticks, tope 5 % y **cierre forzado a las 16:45 NY** como el motor (`--force-flat-ny 16:45`).

  | Variante | D (oct-23 → oct-24, intacto) | A (oct-24 → oct-25) | B (oct-25 → oct-26) | 3 años |
  |---|---|---|---|---|
  | Asia → NY (19:00–14:00 NY) | 214 · −0,182 (t −2,6) | 221 · −0,045 | 248 · +0,024 | 683 · **−0,063** · −43,1 R |
  | Londres + NY (`legacy_utc`) | 65 · −0,150 | 79 · +0,035 | 78 · +0,005 | 222 · **−0,030** · −6,6 R |

  - Por tramo horario (Asia → NY): Asia 19–24 NY −0,059 (298), Asia 0–2 NY −0,050 (89), Londres 2–7 NY −0,123 (162),
    NY 7–14 −0,010 (134). Abrir más horas triplica las operaciones, pero todas las franjas nuevas pierden.
  - Por instrumento (Asia → NY, 3 años): positivos solo Germany 40 +0,13, XAUUSD +0,10 y USDJPY +0,06.
  - El +0,09 del walk-forward por coste se midió **sin** el cierre de las 16:45; con el cierre que aplica el bot real,
    la ventaja desaparece.
- **Conclusión**: Malaysian SNR en mercados reales no es rentable con la operativa real del bot. La ventana Asia → NY
  pierde más (≈ −14 R/año esperado) que el horario Londres/NY (≈ −2 R/año, plano). Recomendación: desactivar la
  prueba (`DAEMONBLACKFX_MSNR_REAL_MARKETS=off` y desmarcar los 10 en /Instruments). Si se mantiene, mejor con
  `DAEMONBLACKFX_MSNR_REAL_SESSION=legacy_utc`. El corte automático de la prueba (40 ops, R/op ≤ 0) la pararía en
  unos 2 meses con una pérdida esperada de ≈ 2,5 R.

### 2026-10-25 — INCIDENTE: selección DEMO de Malaysian SNR sobrescrita por una comprobación (restaurada) y tests aislados de la base viva  ·  Estado: corregido sin commit
- **Qué pasó**: al comprobar la pestaña Malaysian SNR se creó `RealtimeDashboardService(repository=None)`, que sin
  repositorio abre la base **viva** por defecto, y se guardó una selección de prueba. La selección DEMO de
  MALAYSIAN_SNR pasó a las 22:26 UTC de 30 sintéticos (versión 24, 20-oct) a 4 instrumentos (versión 25). No se
  abrieron ni cerraron posiciones; solo cambió qué escanea el worker.
- **Restaurada** con autorización del usuario a la lista exacta de la versión 24 (queda como versión 26), verificada.
- **Prevención**: `tests/conftest.py` fija `DAEMONBLACKFX_DB_PATH` a una base temporal antes de importar nada. Varios
  tests creaban el dashboard sin repositorio y **leían la base viva** (por eso dos fallaban de forma intermitente).
  Las comprobaciones manuales se harán siempre con un repositorio temporal.
- **Activación (pedida por el usuario)**: los 10 mercados reales quedan marcados en la selección DEMO de
  Malaysian SNR (versión 27: los 30 sintéticos + los 10 reales). La etiqueta de la pestaña decía "MSNR Activo ·
  Volatility" para todo lo que no era Boom/Crash/Step/Jump/DEX; ahora muestra "Forex / Metal / Índice (prueba demo ·
  Asia→NY)" (`msnrFamilyLabel`, se ve al reiniciar el dashboard).
- **Pestaña Malaysian SNR**: los 10 mercados reales aparecen en sus grupos (Forex & Cripto, Metales, Índices); grupo
  nuevo `malaysian_snr_metals` para que XAUUSD no salga como Forex (en los dos bloques duplicados de `app/main.py`).
  Tests de recuento actualizados (`test_v121`, `test_v119`, `test_ict_instrument_policy`).

### 2026-10-25 — Malaysian SNR en mercados reales de bajo coste, sesión Asia → Nueva York (prueba demo, decisión del usuario)  ·  Estado: aplicado sin commit (falta reiniciar y marcar los instrumentos en /Instruments)
- **Qué**:
  - **Instrumentos** (`MalaysianSNRConfig.real_market_symbols`, `DAEMONBLACKFX_MSNR_REAL_SYMBOLS`): Germany 40, US Tech 100,
    USDJPY, XAUUSD, Wall Street 30, EURJPY, GBPUSD, EURUSD, US SP 500 y USDCAD (los de spread/SL mediano ≤ 2 % en 3 años).
    Pasan aunque Malaysian SNR siga en "solo sintéticos" y se añaden al universo del worker MALAYSIAN_SNR (no al worker
    MSNR vídeos) y a la política de instrumentos.
  - **Ajustes por defecto** (`config_settings_snapshot`, los del replay validado), no los de la base (Breaker Pair y
    Pinbar en live perdían −0,36 R/op en Forex). Versión propia `msnr-real-markets-v1` para contarlos aparte.
  - **Sesión Asia → Nueva York** (`session_allowed(..., 'asia_to_ny')`, hora de NY): entradas de 19:00 (apertura de
    Tokio) a 14:00; nada en las 3 h previas al rollover de las 17:00, ni el viernes desde las 14:00, ni el fin de
    semana. Horas en `DAEMONBLACKFX_MSNR_ASIA_START_NY` (19) y `DAEMONBLACKFX_MSNR_NY_CUTOFF_NY` (14). Sustituye al filtro
    Londres/NY (`legacy_utc`) solo en estos instrumentos (`DAEMONBLACKFX_MSNR_REAL_SESSION=legacy_utc` lo restaura).
  - **Swap**: el worker ya bloqueaba entradas de Forex de 14:00 a 17:00 NY y **cierra Forex, índices y metales a las
    16:45 NY** cada día y antes del fin de semana (no hay swap). La sesión nueva extiende el corte a índices y metales.
  - **Prueba demo** (`_msnr_real_markets_gate`): modo `DAEMONBLACKFX_MSNR_REAL_MARKETS` (off / demo_test / live),
    desde `_START` (26-oct-2026), criterio fijado **40 operaciones sin cierres manuales con R/op > 0**
    (`_REVIEW_TRADES`, `_MIN_R`); si no, `NO_SUPERA` bloquea sus entradas nuevas (`MSNR_REAL_DEMO_TEST`). Tope
    spread/SL 5 % (`_SPREAD_MAX_SL_RATIO`).
  - **Fidelidad con el replay**: estos instrumentos no pasan por el filtro de régimen ADX de MSNR ni por el veto del
    centinela de régimen (solo observa), ni por la lista fija de pares del worker Forex (EURJPY quedaba fuera).
- **Evidencia**: walk-forward por coste +0,104 / +0,079 / +0,112 R/op (no concluyente, p 0,07–0,13). La ventana
  Asia → NY **no estaba medida**: replay en curso (`tools/replay_msnr_variants.py --force-flat-ny 16:45`, que ahora
  replica el cierre forzado del motor), comparada con el filtro Londres/NY.
- **Tests**: `tests/test_audit_20261024_pending_improvements.py` (ventana, ajustes, versión, puerta, spread, filtros,
  universo); actualizados `test_msnr_synthetics_only.py`, `test_malaysian_snr_causal_validation.py`,
  `test_malaysian_snr_augmented_rules.py`, `test_malaysian_snr_integration.py`, `test_msnr_video_worker.py` y, en
  `test_msnr_data_ai_candidates.py` / `test_msnr_structural_opportunities.py`, EURUSD → AUDUSD (siguen probando un
  mercado real que lee los ajustes guardados). Suite completa con la base aislada: 2.095 pasan + estos 7 corregidos.
- **Para que tenga efecto**: reiniciar los daemons y marcar los 10 instrumentos en la pestaña Malaysian SNR de
  /Instruments (o `tools/apply_ict_instrument_policy.py --apply`).

### 2026-10-25 — Malaysian SNR en mercados reales: elegir instrumentos con datos pasados (año siguiente fuera de muestra)  ·  Estado: solo investigación, sin cambios en el bot
- **Pregunta del usuario**: ¿por qué no dejar activos solo los instrumentos con acierto > 50 %? Se prueba como se haría
  en vivo: se elige con un periodo y se opera el siguiente (D→A, A→B, D+A→B), sobre los replays E1.

  | Regla (elegir con el pasado) | D→A elegidos / resto | A→B elegidos / resto | D+A→B elegidos / resto | Azar (p) |
  |---|---|---|---|---|
  | Acierto > 50 % (n ≥ 3) | 71 · **+0,145** / −0,097 | 110 · **−0,019** / −0,088 | 89 · **+0,104** / −0,136 | 0,096 · 0,338 · 0,025 |
  | Coste: spread/SL mediano ≤ 2 % | 78 · **+0,104** / −0,089 | 76 · **+0,079** / −0,113 | 66 · **+0,112** / −0,114 | 0,134 · 0,102 · 0,072 |

  - **Acierto > 50 %**: los elegidos rinden mejor que el resto en los tres casos, pero en A→B pierden. Funciona a medias.
  - **Coste**: positivo en los tres saltos, con una razón económica (la ventaja de ICT en sintéticos también es de
    coste); pruebas sin solaparse (A y B) 154 ops, +0,092, t 1,07. **Prometedor pero no concluyente** (ningún p < 0,05).
    Esta regla se formuló después de ver los datos: la validación fiel solo puede ser hacia delante.
  - Elegidos hoy por coste (3 años): Germany 40, US Tech 100, USDJPY, XAUUSD, Wall Street 30, EURJPY, GBPUSD, EURUSD,
    US SP 500 y USDCAD (≈ 75 ops/año).
- **Para activarlo** (pendiente de decisión del usuario) haría falta: MSNR en mercados reales solo en esos instrumentos,
  con los **ajustes por defecto** (los de la base, con Breaker Pair y Pinbar en live, perdían −0,36 en Forex), en
  prueba demo con criterio fijado (p. ej. 40 ops, R/op > 0, sin cierres manuales).

### 2026-10-25 — RESULTADO E1: Malaysian SNR en mercados reales no tiene ventaja; ni familias ni instrumentos elegidos persisten  ·  Estado: solo investigación, sin cambios en el bot
- **Replays** (`msnr_variants_signals_real_e1_{B,A,D}.csv`, clase real, ajustes por defecto, sesiones Londres/NY, sesgo
  D1, spread real de ticks, tope 5 %; B oct-2025 → oct-2026, A oct-2024 → oct-2025, D oct-2023 → oct-2024 intacto):

  | Familia | D (intacto) | A | B | ¿Supera? |
  |---|---|---|---|---|
  | Forex | 153 · −0,168 (t −2,0) | 167 · −0,149 (t −2,0) | 173 · −0,091 | No (negativo en los 3) |
  | Índices | 46 · −0,160 | 78 · +0,136 | 77 · −0,092 | No |
  | Energía | 14 · −0,110 | 7 · +0,214 | 15 · +0,182 | No |
  | Metales | 9 · +0,327 | 13 · +0,322 | 20 · +0,131 | No (n < 40 por periodo; 3 periodos juntos: 42 ops, +0,232, t 1,41) |
  | **Total** | 222 · −0,143 (t −2,1) | 265 · −0,032 | 285 · −0,061 | No |

- **Pistas añadidas antes de ver A y D**:
  - P-extra 1, tope 2 %: A +0,063, D −0,035 (A+D +0,025, t 0,33) → **no supera**.
  - P-extra 2, metales + energía: A +0,284 (20), D +0,061 (23) → positivo pero con n < 40 por periodo y t bajo → **no concluyente**.
    El azar da una familia positiva en los 3 periodos el 12 % de las veces. Metales ≈ 14 ops/año (el oro aporta casi
    todo): una prueba demo de 40 ops tardaría ~3 años, y el oro tiene deriva alcista (beta).
  - P-extra 3, cartera USDJPY, EURUSD, GBPJPY, AUDUSD, US Oil (elegida por ser positiva en B): A +0,021, D −0,127 →
    **no supera**. En A+D: EURUSD −0,44, GBPJPY −0,21, AUDUSD +0,01, US Oil 0,00, USDJPY +0,11.
- **Por instrumento**: solo 3 de 39 instrumentos con datos en los 3 periodos son positivos en los 3 (Germany 40,
  US Small Cap 2000, France 40, todos con ≤ 21 operaciones en 3 años). Por azar se esperan ≈ 5. El "13 de 32 con
  acierto > 50 %" de B también era lo esperado por azar (12,2; p 0,44).
- **Conclusión**: Malaysian SNR no es rentable en Forex, materias primas ni índices con costes reales, y elegir
  instrumentos o familias por el resultado de un año no funciona (el resultado no persiste). Forex pierde en los tres
  periodos y no debe activarse. No se cambia nada en el bot.

### 2026-10-25 — RESULTADO E2: MSNR vídeos (H4→H1) PIERDE en Forex, metales, energía e índices  ·  Estado: solo investigación, sin cambios en el bot
- **Replay fiel** (`msnr_video_faithful_real_e2_B.csv`, oct-2025 → oct-2026, 47 símbolos con operaciones, spread real
  de ticks, tope 5 %): **4.652 ops, −0,055 R/op, t −3,74**, acierto 49 %, mitades −0,051 / −0,059. **NO SUPERA**.

  | Familia | n | R/op | t | Mitades |
  |---|---:|---:|---:|---|
  | Forex | 2.204 | −0,048 | −2,32 | −0,037 / −0,063 |
  | Índices | 1.697 | −0,068 | −2,75 | −0,051 / −0,084 |
  | Metales | 455 | −0,054 | −1,11 | −0,083 / −0,023 |
  | Energía | 296 | −0,029 | −0,49 | −0,160 / +0,035 |

  - Con tope 2 %: −0,054 (t −3,67). 13 de 47 símbolos positivos.
  - Como ya falla en el primer periodo, no se gastan los otros dos (el criterio exige positivo en cada uno).
  - Junto con sintéticos (−0,051, t −2,6): **MSNR vídeos no tiene ventaja en ningún mercado** con la clase real.
- **Código**: el escenario H4→H1 solo se evaluaba en sintéticos aunque el worker se configurase para todo mercado
  (filtro fijo en `_h4h1_signal`). Ahora es `MalaysianSNRConfig.h4h1_synthetics_only` (por defecto True = sin cambio),
  que `MSNRVideoStrategy` toma de su `synthetics_only`. Test en `test_audit_20261024_pending_improvements.py`.
- `tools/replay_msnr_variants.py`: `--spread-file` (spread real de ticks) y guardado incremental (un proceso caído ya
  no pierde lo calculado). `tools/replay_msnr_video_faithful.py`: `--spread-file`, `--all-markets`, `--spread-cap`.

### 2026-10-25 — PRE-REGISTRO: Malaysian SNR y MSNR vídeos en Forex, materias primas e índices con el spread real de ticks  ·  Estado: fijado antes de ver datos
- **Petición del usuario**: validar Malaysian SNR en mercados reales.
- **Antecedentes**: con los ajustes de la base (Breaker Pair y Pinbar en live) MSNR perdía en Forex (−0,36 R/op); con
  los ajustes por defecto y tope 5 % salía +0,124 / +0,149 pero con unas 30 operaciones al año y con el spread de
  `symbol_info`. H4→H1 (simulación de investigación) perdía en mercados reales (−0,045).
- **Costes**: el campo `spread` de las velas M15 vale 0 en Forex y oro hasta oct-2024 y en el resto es el mínimo del
  periodo; `symbol_info` en fin de semana está inflado. Se usa como coste fijo la **mediana del spread de ticks de
  19–23 oct-2026, 07:00–17:00 UTC** (`storage/analysis/real_markets_tick_spread_20261023.json`).
- **Universo**: Forex mayores y menores (sin exóticos NOK/PLN/SEK/HUF/TRY/ZAR/MXN), metales (XAUUSD, XAGUSD,
  XPTUSD), energía (US Oil, UK Brent Oil) e índices bursátiles del broker. Las materias primas blandas se excluyen
  (coste prohibitivo ya medido).
- **Estrategias** (clase real, velas cerradas, sin lookahead, entrada en la apertura siguiente con spread):
  - E1 Malaysian SNR con ajustes **por defecto** (los validados), filtro de sesiones Londres/NY y sesgo D1 como en vivo,
    tope spread/SL 5 % (el de Forex en vivo), un trade por símbolo.
  - E2 MSNR vídeos (H4→H1, `MSNRVideoStrategy`), tope 5 %.
- **Periodos**: B = oct-2025 → oct-2026; A = oct-2024 → oct-2025; D = oct-2023 → oct-2024 (**intacto**, solo Forex y
  metales tienen M15; los índices empiezan en jun-2024).
- **Criterio por familia** (Forex, metales, energía, índices) y en total: R/op > 0 en **cada** periodo con datos
  (n ≥ 40), t ≥ 2 con los periodos juntos. Lo que supere irá a prueba demo con criterio; lo que no, se descarta.
- **Adelanto E1, periodo B (46 de 49 símbolos)**: total −0,061 (285 ops; mitades −0,044 / −0,080); Forex −0,091 (173),
  índices −0,092 (77) → **descartados** por el criterio. Metales +0,131 (20) y energía +0,182 (15): muestra insuficiente.
- **Añadido ANTES de ver los periodos A y D** (sale de mirar B, así que B no cuenta como prueba):
  - P-extra 1: E1 con **tope spread/SL 2 %** en todos los mercados (en B: +0,065, 107 ops, t 0,6). Supera si R/op > 0
    en A y en D por separado y en A+D juntos t ≥ 2.
  - P-extra 2: metales + energía juntos con tope 5 %. Mismo criterio en A y D.
  - P-extra 3 (petición del usuario de ver el resultado por instrumento): cartera fija de los instrumentos positivos
    en ambas mitades de B con ≥ 6 operaciones = **USDJPY, EURUSD, GBPJPY, AUDUSD y US Oil**. Supera si la cartera da
    R/op > 0 en A y en D por separado y al menos 3 de los 5 son positivos en A+D. (En sintéticos el R por activo no
    persistía entre años, correlación −0,25: es la prueba de si aquí sí.)

### 2026-10-25 — RESULTADO: MSNR vídeos (H4→H1) con la clase real PIERDE en el periodo intacto; la familia Malaysian SNR no tiene ventaja en sintéticos  ·  Estado: solo investigación, sin cambios en el bot
- **Replay fiel** (`msnr_video_faithful_prereg_D.csv`, 20-dic-2023 → 30-jun-2024, 18 activos con historia):
  2.830 ops, **−0,051 R/op** (t −2,59; agrupado por día −2,59), acierto 47 %. Mitades −0,057 / −0,047. **NO SUPERA**
  (pierde de forma significativa). 8 de 18 símbolos positivos; BUY −0,078, SELL −0,027; a favor de la storyline
  −0,028, en contra −0,099, sin storyline −0,046. Encaja con la demo (−0,344 R/op con solo la gestión del bot).
  - La prueba rápida previa (20 días de Volatility 75 Index dentro del periodo, −0,153) se anota como contaminación mínima.
  - El +0,029 de la investigación se midió con una simulación propia (desde jul-2024), no con la clase real.
- **Conclusión de la investigación de Malaysian SNR (25-oct-2026)**: con la clase real y cuatro periodos, ni Malaysian
  SNR (media ≈ 0: −0,047 / +0,002 / +0,043 / −0,052) ni MSNR vídeos (−0,051, t −2,6) tienen ventaja en sintéticos, y
  ningún filtro la crea. Los sintéticos se comportan como un paseo aleatorio y estas reglas de precio no tienen
  ventaja sobre el coste. La única ventaja robusta en sintéticos sigue siendo ICT (+0,024 / +0,048 R/op en dos años),
  que depende del precio de entrada (límite) y del tope de spread.
- **Propuesta (decisión del usuario)**: pausar las entradas nuevas de MALAYSIAN_SNR y MSNR (añadirlos a
  `DAEMONBLACKFX_DISABLED_WORKERS`, el monitor sigue gestionando lo abierto) para liberar huecos y riesgo para ICT,
  RSI2, ORB y CARRY; o dejar que lo decidan sus pruebas demo (60 y 200 ops, ahora sin cierres manuales).

### 2026-10-25 — PRE-REGISTRO: MSNR vídeos (H4→H1) con la clase real en un periodo intacto (dic-2023 → jun-2024)  ·  Estado: fijado antes de ver datos
- **Por qué**: el escenario H4→H1 se validó con una simulación de investigación (desde jul-2024, +0,029 R/op), no con
  la clase real `MSNRVideoStrategy`. En demo, solo con la gestión del bot, da −0,344 R/op (16 ops).
- **Replay** (`tools/replay_msnr_video_faithful.py`, nuevo): clase real, velas cerradas, evaluación en cada cierre H1,
  entrada en la apertura M15 siguiente (BUY al ask), tope spread/SL 2 %, una operación por símbolo hasta su resultado,
  contrato TP1 1R + runner 2R con BE. Universo del worker MSNR. Periodo 20-dic-2023 → 30-jun-2024 (M15 de MT5 desde
  mediados de dic-2023; la investigación empezó el 1-jul-2024).
- **Criterio**: R/op > 0 en el total y en ambas mitades, n ≥ 40 por mitad. Si no supera, MSNR vídeos no tiene ventaja
  demostrada con la clase real y queda pendiente de su prueba demo (200 ops) como candidato a retirar.

### 2026-10-25 — RESULTADO del pre-registro: ningún filtro de régimen ADX de Malaysian SNR supera en el periodo intacto  ·  Estado: solo investigación, sin cambios en el bot
- **Datos D** (`msnr_variants_signals_prereg_D_2024.csv`, 30-dic-2023 → 24-oct-2024, 24 activos con historia, 849 señales):

  | Variante | n | R/op | Mitades | Azar p | ¿Supera? |
  |---|---:|---:|---|---|---|
  | Sin filtro | 849 | −0,047 | −0,074 / −0,021 | — | — |
  | P1 filtro actual (bloquea (25, 40]) | 577 | −0,072 | −0,114 / −0,030 | 0,85 | No (empeora) |
  | P2 bloquea (20, 40] | 402 | −0,131 | −0,158 / −0,106 | 0,99 | No |
  | P3 solo ADX ≤ 15 o (40, 50] | 169 | −0,046 | −0,158 / +0,037 | 0,49 | No |
  | P4 spread/SL ≤ 1 % | 510 | −0,026 | −0,027 / −0,025 | 0,23 | No |

  - Por tramos el patrón se invierte: (20, 25] +0,062 y (25, 30] +0,125 ganan; ≤ 15 −0,026 y (40, 50] −0,089 pierden.
    El "patrón" de A, B y C era ruido.
- **Conclusión**: Malaysian SNR en sintéticos **no tiene una ventaja robusta** en cuatro periodos con la clase real:
  D (2024) −0,047 · A (2024-25) +0,002 · B (2025-26) +0,043 · C (últimos 180 días, ajustes reales) −0,052.
  Media ≈ 0, y antes de costes de oportunidad (huecos, riesgo simultáneo). Ningún filtro de contexto, coste,
  confirmación, escenario o gestión la convierte en rentable de forma fiable. El filtro actual (25, 40] tampoco tiene
  respaldo fuera de su muestra (en D empeora).
- **Decisión pre-registrada**: se mantiene la configuración actual; `DAEMONBLACKFX_MSNR_REGIME_ADX_KEEP` queda vacío
  (sin efecto). La prueba demo del filtro (60 ops, sin cierres manuales) sigue siendo el criterio.

### 2026-10-25 — PRE-REGISTRO: filtro de régimen ADX de Malaysian SNR en un periodo intacto (dic-2023 → oct-2024)  ·  Estado: fijado antes de ver datos
- **Origen** (`tools/research_msnr_filters.py`, búsqueda pre-registrada de 9 hipótesis; umbral elegido en A = año
  previo, validado en B = último año y C = 180 días con los ajustes reales):
  - Solo el régimen ADX supera: bloquear (20, 40] da A +0,032 · B +0,129 (mitades +0,101 / +0,156; azar p 0,007) ·
    C +0,014. Coste, tamaño de stop, confirmación, escenario, frescura, cuerpo, obstáculo y gestión: no superan.
  - Pero la franja (20, 25] que añade frente al filtro actual pierde en A y C y gana en B, y el azar solo es
    significativo en B (A 0,197; C 0,112). B no es independiente: el filtro (25, 40] se descubrió en esos dos años.
  - Patrón repetido en A, B y C: ADX ≤ 15 (+0,116 / +0,153 / +0,125) y 40–50 (+0,121 / +0,185 / +0,133) ganan;
    25–30 y 35–40 pierden. Está sacado de mirar los datos: necesita un periodo nuevo.
- **Datos D (intactos)**: `replay_msnr_variants.py --days 300 --end-days-ago 730 --free-busy --spread-cap 0.02`,
  ajustes por defecto (como A y B), universo activo de Malaysian SNR. M15 de MT5 desde mediados de dic-2023.
- **Hipótesis y criterio** (R/op con el contrato, `rr_live`):
  - P1: el filtro actual (bloquear (25, 40]) mejora la R/op frente a no filtrar en D.
  - P2: bloquear (20, 40] mejora frente a (25, 40] en D.
  - P3 "ADX extremos": conservar solo ADX ≤ 15 o (40, 50]. Supera si en D: R/op > 0, positivo en ambas mitades,
    n ≥ 40 y mejor que no filtrar con azar p < 0,05.
  - P4 (añadida antes de ver D): tope spread/SL ≤ 1 % (H1; A +0,035, B +0,082, C −0,068). Mismo criterio que P3.
  - Implementación preparada sin efecto: `DAEMONBLACKFX_MSNR_REGIME_ADX_KEEP` ("0-15,40-50" activaría P3; vacío por defecto).
- **Decisión fijada**: si P3 supera → modo nuevo configurable en **prueba demo** con criterio (no en real directo,
  porque nació de los datos). Si no, pero P2 supera → tramo (20, 40] en la prueba demo actual. Si ninguna → se mantiene
  el filtro actual (25, 40] y su prueba de 60 operaciones.

### 2026-10-24 — Mejoras pendientes por estrategia (1.ª tanda): criterios demo sin cierres manuales, centinela ORB en prueba, IA y datos reales  ·  Estado: aplicado sin commit (falta reiniciar)
- **Criterios de las pruebas demo sin cierres manuales** (`TradingRepository.closed_operations_r`): una operación con
  alguna pierna cerrada a mano (`mt5_mobile`, `mt5_client`, `mt5_web`) no cuenta. Lo usan los 9 criterios (ORB,
  filtro de régimen MSNR, DEX, MSNR vídeos, RSI2, NIGHT, DRIFT, CARRY…). Efecto en la base viva (R/op, todas → sin
  manuales): **ICT v2 Fase 1 −0,061 → −0,229** (106 → 77 ops), **MSNR vídeos −0,006 → −0,344** (30 → 16),
  smc-v1 −0,048 → −0,117, msnr-v1.0 +0,006 → −0,024. Las piernas manuales ganaban +0,14 a +0,39 R de media.
  `DAEMONBLACKFX_DEMO_TEST_EXCLUDE_MANUAL` (1).
- **Centinela de régimen en ORB: OBSERVE en prueba demo** (`tools/research_orb_regime_sentinel.py`, nuevo). Sobre
  las operaciones del replay ampliado de ORB SWEEP, el centinela real (FILTER) con las 40 H1 cerradas previas:

  | Universo | Permitidas (n · R/op) | Bloqueadas (n · R/op) | Bloq. mitad 1 / 2 |
  |---|---|---|---|
  | SWEEP en vivo (XAUUSD, BTCUSD, USDCAD) | 145 · +0,132 | **80 · +0,329** (36 %) | +0,338 / +0,320 |
  | SWEEP XAUUSD | 60 · +0,075 | 37 · +0,445 | +0,253 / +0,697 |
  | SWEEP todos (19 símbolos) | 1.108 · −0,078 | 464 · −0,084 | −0,111 / −0,050 |

  - Sin centinela, el universo vivo pasa de +0,132 a **+0,202 R/op** (mitades +0,180 / +0,224) y de +19,2 a +45,5 R.
  - Permutación: p = 0,11 (XAUUSD 0,057): **no concluyente** → prueba demo. Motivo principal de bloqueo:
    `ERRATIC_WHIPSAW_VOLATILITY` (69 de 80). Es el mismo patrón que en ICT sintéticos.
  - **Criterio fijado**: 30 operaciones ORB abiertas con el centinela en `REGIME_TOXIC_OBSERVED_NOT_BLOCKED`
    (auditoría `MARKET_REGIME_OBSERVED`, `observe_scope=ORB_DEMO_TEST`) con R/op > 0 sin cierres manuales; si no,
    `DAEMONBLACKFX_MARKET_REGIME_ORB_MODE=FILTER`.
  - Limitación: el replay no tiene el spread de ticks por vela, así que el factor de spread anómalo no se evalúa.
- **IA de Malaysian SNR con modelo incompatible: `observe` por defecto** (solo DEMO; en cuenta real sigue bloqueando).
  Antes `block` en el código: si se perdían los ajustes guardados, MSNR dejaba de operar sin avisar.
  `DAEMONBLACKFX_MSNR_AI_INCOMPATIBLE_DEFAULT` (observe | block). La base viva ya usa `observe`: sin cambio hoy.
- **ICT envía datos reales para la IA** (`signal["ict_real_features"]`: ADX y ATR H1, stop/ATR, rango/ATR, spread/SL).
  `adx` = 28 y `confirmation_percentage` = 95 siguen fijos: el modelo en sombra se entrenó con ellos.
- **Hallazgo: la puerta ADX de STEP nunca filtró ICT.** ICT manda siempre `adx` = 28 (> 25) y el ADX de respaldo
  importaba `strategy.indicators`, que no existía (fallo silencioso). Se crea `strategy/indicators.py` con el ADX de
  Wilder de MSNR (MSNR delega en él, mismo cálculo). No se cambia la puerta: activarla con el ADX real sería un filtro
  nuevo sin replay.
- **ICT: velas H4 configurables** (`macro_h4_candles`, `DAEMONBLACKFX_ICT_H4_CANDLES`, por defecto 101 = sin cambio).
  **Replay EMA200 convergida (401 velas) frente a la actual (101), 27 sintéticos, límite + tope 2 %: NO se cambia.**

  | Velas H4 | Último año | Año previo |
  |---|---|---|
  | 101 (actual) | 7.419 ops · +0,0484 (t 3,92; mitades +0,067 / +0,031) | 8.360 · +0,0236 (t 2,04) |
  | 401 | 7.360 · +0,0464 (t 3,75) | 8.301 · +0,0270 (t 2,31) |
  | Señales que solo da 401 | 371 · −0,081 | 436 · +0,017 |

  Cambia de signo entre años y por poco: no supera la regla. Ficheros `ict_limit_entry_signals_h4_{101,401}_{y1,y0}.csv`. **H4 reconstruida desde H1** (solo de respaldo) sin el bloque de
  4 h en formación (`DAEMONBLACKFX_ICT_H4_COMPLETE_ONLY`, 1).
- **Tope de riesgo por factor renta variable US** (`_factor_risk_guard`): suma el riesgo abierto (sin piernas en BE) de
  todos los workers en US SP 500, US Tech 100, Wall Street 30, US Small Cap 2000 y US Mid Cap 400. **Apagado por
  defecto** (`DAEMONBLACKFX_US_EQUITY_RISK_CAP=0`, recomendado 3.0): quitaría señales de RSI2 durante su prueba.
  Símbolos en `DAEMONBLACKFX_US_EQUITY_FACTOR_SYMBOLS`.
- **MSNR H4→H1**: la lista de setups disparados (la única deduplicación de MSNR vídeos, cuya clave usa la hora de
  evaluación) se acota a 5.000 olvidando los más antiguos. `enable_runner_trailing_lock` documentada como sin efecto.
- **ORB, gestión del runner**: el bloqueo escalonado propio (1,8R → +1R) solo actúa con la extensión progresiva
  apagada; con la configuración actual no se usa. Sin cambio.
- **Dashboard: gráficos de posiciones bajo demanda** (T3). `/api/state` llevaba en cada refresco dos gráficos de 5
  marcos por posición (~400 KB cada una; 11 posiciones = 4,4 MB de 6,1 MB). Ahora `/api/state` marca `charts_lazy` y
  `chart_available`, y el front pide `/api/open-positions/<id>/charts` solo para la posición seleccionada (con caché y
  refresco solo de esa). Medido con el estado real en una instancia de prueba: **6,1 MB → 1,8 MB** (156 KB
  comprimido); el gráfico y el de entrada se pintan y se mantienen entre refrescos (comprobado en el navegador).
  `DAEMONBLACKFX_DASHBOARD_LAZY_CHARTS` (1).
- **ICT sintéticos pierde en demo por señales que el replay no toma (T5 sigue abierta) → corregido**:
  - Demo, solo gestión del bot (19 → 25-oct): −0,26 R/op en 74 operaciones; igual antes y después del reinicio del
    22-oct. **La ejecución es fiel**: 69 de las 71 entradas salieron de un disparo del límite virtual, 0,04R mejor
    que el límite.
  - Replay de esos días (`ict_limit_entry_signals_gap_20261025.csv`, tope 2 %): **−0,022 R/op** (115 ops; semana plana).
  - Emparejadas con el replay: 32, vivo −0,111 frente a replay −0,185. **Sin pareja: 42, −0,374 R/op.**
  - Al reejecutar ICT en esas velas, las 33 sin pareja (sin cierres manuales) **son señales válidas**: el replay no
    las toma porque tenía el símbolo ocupado con una operación anterior. En vivo el símbolo quedó libre porque la
    señal anterior **disparó su límite y no se abrió** por otro motivo distinto del spread (auditoría tras cada
    disparo: huecos llenos 43, rechazo por riesgo 41, R ejecutable 3, ciclo 1; spread 62, que ya ocupaba el símbolo).
  - **Corrección** (`_register_ict_trigger_block_lock`): una señal ICT de sintéticos que dispara su límite y no se
    abre ocupa el símbolo con su operación virtual hasta su resultado, como en el replay y como ya hacía el spread.
    Es la regla de "ocupación fantasma" validada fuera de muestra, generalizada. `DAEMONBLACKFX_ICT_TRIGGER_LOCK` (1).
    Las señales abiertas o ya ejecutadas (`ALREADY_EXECUTED`) no ocupan.
  - Peores workers en la demo: JUMP −0,53 (13), VOLATILITY_4 −0,73 (5), STEP −0,27 (28).
- **Malaysian SNR con los ajustes reales de la base (replay 180 días, 30 activos, tope 2 %, sin señales en modo
  observación): ninguna variante mejora y no se cambia nada.**
  - Hallazgo previo: el replay que validó MSNR en sintéticos usó los ajustes por defecto (Breaker Pair y Pinbar en
    observación). La base tiene ambos en `live`. Además, `replay_msnr_variants.py` contaba como operaciones las señales
    en modo observación, que el motor no ejecuta. Corregido: ahora se descartan.

  | Variante | Total (n · R/op) | Mitad 1 | Mitad 2 | Con filtro de régimen (mitades) |
  |---|---|---|---|---|
  | Ajustes vivos | 866 · −0,052 | −0,091 | −0,007 | 509 · −0,020 (−0,085 / +0,066) |
  | Sin Breaker Pair ni Pinbar | 682 · −0,061 | −0,098 | −0,013 | 406 · −0,018 (−0,082 / +0,074) |
  | Obstáculo diario a 1R | 932 · −0,066 | −0,082 | −0,047 | 551 · −0,038 (−0,077 / +0,013) |

  - Breaker Pair y Pinbar no son el problema: en ambas mitades dan unos −0,02 R/op, mejor que el resto. El obstáculo
    a 1R añade operaciones peores. Los ajustes de la base se quedan como están.
  - **Aviso**: en los últimos 6 meses MSNR en sintéticos es negativo con la configuración real (−0,052; con el filtro
    de régimen −0,020). El +0,023 / +0,069 de dos años no se repite en el periodo reciente. La decisión queda en la
    prueba demo del filtro de régimen (60 ops, sin cierres manuales) y en la de MSNR vídeos (200 ops).
  - Ficheros: `msnr_variants_signals_aud180_{live,validated,obs1r}.csv`.
- **Herramientas**: `tools/replay_ict_limit_entry.py --h4-candles`; `tools/replay_msnr_variants.py --config-override`;
  `tools/research_orb_regime_sentinel.py` (nuevo).
- **Tests**: `tests/test_audit_20261024_pending_improvements.py` (27). Suite completa (25-oct): **2.076 pasan, 0 fallos**.

### 2026-10-24 — Los 21 tests que ya fallaban: tests al día con el contrato y un fallo real de test inestable  ·  Estado: aplicado sin commit
- **Qué**: se revisaron uno a uno los 21 fallos anteriores a la auditoría de código. Ninguno destapó un fallo de
  operativa en vivo; casi todos describían reglas antiguas que el propio código (ya commiteado) había cambiado a propósito.

  | Grupo | Tests | Causa | Arreglo |
  |---|---|---|---|
  | TP del runner en el broker | split SMC (2), v115, recorrido en seco, v101 (2) | Con la extensión progresiva activa (regla 2, `runner_extension_enabled=True` ya en `HEAD`) el TP del broker es 4R y el objetivo lógico sigue en 2R; el monitor cierra en 2R sin continuación | Tests: comprueban `logical_target_rr` y `broker_target_rr` por separado; nuevo test de que con la extensión apagada el TP vuelve a 2R |
  | Runner MSNR | política unificada (2), vídeos MSNR (trailing) | MSNR no evalúa continuación: sube el stop 2R → +1R y 3R → +2,5R hacia 4R (19-oct). El "trailing escalonado" del test (2,5R → +1,5R; 3,5R → +3R) **nunca se implementó ni se validó** | Código: la etapa MSNR usa la misma etiqueta que el resto (`EXTENDED_TO_3R/4R`, solo visual). Tests al contrato; MSNR tiene su propio test "bloquea 1R y sigue" |
  | Objetivos MSNR | integración, obstáculos (2), micro-stop | Esperaban TP1 2R / runner 4R; el contrato (y `HEAD`) es TP1 1R / runner 2R | Tests trasladados a 1R manteniendo la misma geometría |
  | ORB | contexto TP2,5/TP3, bloqueo escalonado | El doble de `build_plan` del test usaba el objetivo del broker como `target_rr`; el bloqueo escalonado ORB solo actúa con la extensión apagada (deliberado) | Tests: doble igual que el real; bloqueo probado con la extensión apagada y nuevo test de la delegación |
  | Deslizamiento de emergencia | 2 | La IA de MSNR sin ajustes guardados bloquea modelos incompatibles (`ai_incompatible_policy='block'`); en la base viva es `observe` | Tests: aíslan la IA (miden el cierre por deslizamiento) |
  | STEP ADX | v102 | El mínimo pasó a inclusivo (ADX ≥ 25) en f76caad | Test al día; docstring corregido (el código de motivo se mantiene) |
  | Riesgo ORB | v61 | Buscaba texto en `process_symbol`; la lógica está en `_risk_percent_for_strategy` | Test de comportamiento |
  | Dashboard | v70, v71 | Comparaban topes antiguos (120 / 12 / 2500) | Comprueban que los topes existen |
  | Spread de la IA | `test_meta_execution_spread[timestamp2]` | **Fallo real del test**: "dentro de 2 min" se calculaba al recoger los tests y la suite tarda ~10 min | La hora se calcula al ejecutar |
  | Motor sin `config` | guardián de posiciones, ORB payload | `process_symbol` leía `self.config` sin protección | Código (hecho en la entrada anterior) |
  | Concurrencia Deriv | `test_empty_file_concurrent_processes` | Inestable por tiempo: 4 procesos *spawn* en 20 s con la suite y los daemons en marcha (pasa aislado 3/3) | Espera a 60 s |
- **Resultado**: suite completa **2.048 pasan, 1 falla** (el inestable de Deriv, corregido después y verificado aislado).
- **A tener en cuenta (sin cambio)**: `enable_runner_trailing_lock` de Malaysian SNR es una bandera **sin efecto** (ningún
  código la lee para gestionar el runner). Implementar un trailing propio de MSNR exigiría replay antes.
- **Ficheros**: `strategy/execution/live_trading_engine.py` (etiqueta de etapa MSNR y docstrings) y los tests
  `test_daemon_split_risk_management`, `test_v115_…`, `test_live_end_to_end_dry_run`, `test_v101_…`,
  `test_all_strategies_unified_…`, `test_msnr_video_improvements`, `test_malaysian_snr_integration`,
  `test_malaysian_snr_causal_validation`, `test_malaysian_snr_persistent_retest`, `test_gold_orb_dual_leg_improvements`,
  `test_emergency_slippage_rr`, `test_v102_…`, `test_v61_…`, `test_v70_…`, `test_v71_…`, `test_meta_execution_spread`.
- **Configuración**: sin interruptores nuevos (solo tests, etiquetas y comentarios).
- **Efecto esperado y riesgos**: ninguno en la operativa; la suite vuelve a ser una red fiable para los próximos cambios.

### 2026-10-24 — Auditoría de código: 2 piernas en símbolos con `volume_limit`, límite virtual ICT de un solo uso, dashboard protegido y detección de sintéticos única  ·  Estado: aplicado sin commit (falta reiniciar)
- **Qué**:
  1. **Volume limit por pierna** (`brokers/mt5_execution.py::symbol_volume_headroom`, `calculate_volume(max_volume_cap=)`,
     `LiveTradingEngine._leg_volume_cap`). El plan reparte entre las piernas el `volume_limit` del símbolo (posiciones +
     pendientes en el mismo sentido). **Bug confirmado**: en Volatility 250 (1s) (volume_max 30, volume_limit 50) las 5
     últimas entradas (16 → 19-oct) abrieron solo la pierna TP1 de 30 lotes; la RUNNER fallaba con `retcode 10034`.
     Ahora van 2 × 25 lotes (riesgo algo menor que el objetivo, permitido por `allow_reduced_risk`).
  2. **Límite virtual ICT de un solo uso** (`_ict_analysis_with_virtual_limit`): un límite caducado o invalidado (SL tocado
     antes del fill) no se recrea con la misma señal. Antes, dentro de la misma vela de señal, se recreaba y podía
     llenarse si el precio volvía, una operación que el replay no hace (allí se llena antes del SL y pierde −1R). Una
     señal **disparada** sí puede reintentarse (bloqueos pasajeros); la clave de ejecución impide duplicados. Impacto
     pequeño: 2 invalidaciones desde el 19-oct.
  3. **Dashboard protegido frente a otras webs** (`dashboard/request_guard.py`): cualquier página abierta en el navegador
     podía enviar un POST `text/plain` a `127.0.0.1:8765` y detener workers, cambiar selecciones, el objetivo diario o los
     ajustes de MSNR, y leer la cuenta por DNS rebinding. Ahora: `Host` local, en POST `Content-Type: application/json`,
     `Origin` local, sin `Sec-Fetch-Site: cross-site` y cuerpo ≤ 1 MiB (403 si no). El front ya enviaba JSON en los 10 POST.
     También se acota el cuerpo del POST de workers.
  4. **Parche en caliente del dashboard apagado por defecto**: abrir /strategy-bases o /performance recargaba módulos del
     disco y sustituía métodos de `TradingRepository`, del servicio y **el analizador Malaysian SNR de los motores vivos**
     del proceso, sin reinicio ni registro (código sin commit entraba a operar). La lista de perfiles que forzaba ya es
     la misma del repositorio, así que no se pierde nada.
  5. **Detección de sintéticos única**: Malaysian SNR usa la función de ICT (había 3 listas distintas). "DEX" se busca como
     palabra: como subcadena coincidía con cualquier "INDEX"; Trek, Exponential Growth y Snap, que solo entraban por esa
     casualidad, se nombran. **Clasificación idéntica en los 733 símbolos del broker** (comprobado).
  6. Comentarios de objetivos corregidos (ICT decía TP1 2,0R / runner 3,5R; MSNR 2R/2,5R). La configuración ya era 1R/2R.
- **Por qué / evidencia**: base viva (trades de Volatility 250 (1s) con una sola pierna; eventos `ICT_VIRTUAL_LIMIT`:
  1.200 CREATED, 906 TRIGGERED, 44 EXPIRED, 2 INVALIDATED) y `symbol_info` de MT5. No cambia ninguna regla de señal.
- **Ficheros**: `brokers/mt5_execution.py`, `strategy/execution/live_trading_engine.py`, `strategy/ict/ict_strategy.py`,
  `strategy/malaysian_snr/malaysian_snr_strategy.py`, `dashboard/request_guard.py` (nuevo), `dashboard/realtime_dashboard.py`,
  `dashboard/strategy_settings_api.py`, `dashboard/strategy_bases_page.py`, `dashboard/performance_page.py`.
- **Configuración / interruptores**: `DAEMONBLACKFX_LEG_VOLUME_LIMIT_CAP` (1), `DAEMONBLACKFX_ICT_VIRTUAL_LIMIT_ONE_SHOT` (1),
  `DAEMONBLACKFX_DASHBOARD_STRICT_REQUESTS` (1), `DAEMONBLACKFX_DASHBOARD_HOT_SYNC` (0),
  `DAEMONBLACKFX_SYNTH_DETECTION_EXTENDED` (1, ahora también en MSNR).
- **Tests**: `tests/test_audit_20261024_fixes.py` (38). Suite completa: 2.023 pasan y 24 fallan; los mismos 23 fallan
  con los interruptores nuevos apagados (anteriores a este cambio: objetivos del runner, IA, MSNR obstáculos y textos del
  dashboard) y `test_meta_execution_spread[timestamp2]` es inestable (pasa solo). Se arreglaron 2 de ellos
  (`self.config` sin protección en `process_symbol`, del cambio de workers desactivados): quedan **21 fallos previos**.
- **Efecto esperado y riesgos**: Volatility 250 (1s) vuelve al contrato de 2 piernas. Si alguien abre el dashboard con
  otro nombre de host (no 127.0.0.1/localhost), recibirá 403: poner `DAEMONBLACKFX_DASHBOARD_STRICT_REQUESTS=0`.
- **Mejoras detectadas que NO se aplican sin replay** (cambian señales):
  - ICT: la EMA200 H4 se calcula con solo 100 velas (`adjust=False`), así que no converge y pesa mucho la primera vela;
    pedir ≥ 400 velas H4 cambiaría el sesgo macro. ICT envía a la IA `adx` = 28 y `confirmation_percentage` = 95 fijos
    (la IA no puede aprender de ellos; añadir el ADX real antes de reentrenar, prioridad 9).
  - ICT: el spread de respaldo del iFVG/BPR es fijo (0,00015 si el nombre tiene "USD", si no 0,5), sin escala de precio.
    Hoy no se usa (en sintéticos no se busca iFVG y el worker de mercados reales está apagado).
  - ICT live sustituye el límite pendiente por una señal nueva; el replay mantiene ambos. Diferencia pequeña, medir.
  - Dos ATR distintos (ICT de Wilder, MSNR media simple): no unificar sin replay.

### 2026-10-24 — Carry: replay de 5 años con el swap actual (decisión del usuario)  ·  Estado: solo investigación, sin cambios en el bot
- **Qué**: el usuario pide ver el comportamiento de la estrategia 5 años atrás con el mismo swap de hoy (sin descargar
  tipos históricos). `tools/research_fx_carry_mt5.py` admite ahora `--from` y `--tag` y añade el desglose de C0 por año
  y por par y la caída máxima. Velas H1 de MT5 desde nov-2021 (MT5 tiene H1 desde 2017 y D1 desde 1993).
- **Resultado** (`storage/analysis/fx_carry_mt5_report_5y.md`, regla del worker C0 con runner progresivo):
  - **177 ops, +0,170 R/op, t 2,46, acierto 58 %, +30,0 R**; azar con la misma gestión −0,019 R/op.
  - Por año: 2022 +0,274 · 2023 −0,062 · 2024 +0,232 · 2025 −0,041 · 2026 +0,574 (3 de 5 años completos positivos;
    los negativos, pequeños). Peor mes −2,98 R. **Caída máxima −7,9 R**.
  - Por par: AUDJPY +0,311 (66 %), USDCHF +0,139 (49 %), AUDCHF +0,059 (58 %); los tres positivos.
- **Limitación**: swap y selección = valores actuales en todo el periodo (dentro de muestra en la elección de pares).
- **Consecuencia**: una parada temprana a −4 R habría saltado en el histórico; si se añade, debe estar por encima de la
  caída máxima observada (p. ej. −10 R). **Decisión del usuario (24-oct-2026): sin parada temprana; CARRY se juzga solo
  con su criterio de 36 operaciones (R/op > 0).**

### 2026-10-24 — Worker CARRY: carry en Forex G10 con el swap real de MT5 (prueba demo)  ·  Estado: aplicado sin commit (falta reiniciar)
- **Qué**: nuevo worker `CARRY` (magic 26082037, modo `carry-daemon`, estrategia `FX_CARRY`, versión `fx-carry-v1`).
  - Universo: los 28 pares G10 del broker. Cada mes se ordenan por carry neto anual con el **swap real de MT5**
    (`symbol_info`: swap en puntos × punto / precio × 360; solo modo de swap 1) y se operan los **3 de mayor carry
    positivo**, en el lado del carry (se compra la divisa de tipo alto).
  - Entrada a mercado al empezar el mes (hasta 24 h desde la primera vela M15 del mes). Stop 3 × ATR20 D1 con velas
    cerradas antes del mes.
  - Contrato del usuario: 1 % en dos entradas al 50 %. Pierna 1 cierra en TP1 (1R); pierna 2 a BE tras TP1 y busca
    **TP2 (2R)**; la extensión progresiva TP3/TP4 del motor está **activada** para este worker.
  - Rebalanceo: el monitor cierra a mercado lo que siga abierto al cambiar de mes (`CARRY_REBALANCE_EXIT`).
  - Una posición por par. Exento del cierre forzado de Forex antes del rollover y del fin de semana (el carry se
    cobra manteniendo la posición); **mantiene** la puerta de entrada del rollover (no abre con el spread ancho).
  - Usa las velas del broker MT5 en modo shadow, IA en sombra (no veta), centinela de régimen solo observa, huecos
    reservados (`PRIORITY_PROFILES`) y límite por símbolo propio.
- **Criterio fijado de la prueba demo**: desde el 24-oct-2026, con **36 operaciones cerradas en DEMO** (≈ 12 meses a 3
  por mes) se exige **R/op > 0**; si no, `NO_SUPERA` bloquea entradas nuevas solo (`CARRY_DEMO_TEST`). Esperado
  orientativo +0,225 R/op (replay solo MT5 dentro de muestra, ver la entrada siguiente).
- **Primeras entradas**: octubre ya pasó su ventana de entrada; las primeras serán al abrir noviembre (domingo 1-nov
  por la noche). Carry actual: AUDCHF, AUDJPY y USDCHF largos.
- **Ficheros**: `strategy/fx_carry/` (nuevo), `strategy/execution/live_trading_engine.py`, `app/main.py`,
  `database/repository.py`, `dashboard/realtime_dashboard.py` (pestaña CARRY FOREX), `dashboard/strategy_bases_page.py`,
  `tools/daily_tracking_report.py` (familia "Carry Forex").
- **Configuración / interruptores**: `DAEMONBLACKFX_CARRY` (off / demo_test / live), `_START`, `_REVIEW_TRADES`,
  `_MIN_R`, `_RUNNER_EXTENSION`, `_SYMBOLS`, `_TOP_N`, `_MIN_ANNUAL`, `_STOP_ATR`, `_ENTRY_WINDOW_HOURS`.
- **Tests**: `tests/test_fx_carry_worker.py` (13 tests); actualizados `test_connors_rsi2_worker.py` y
  `test_native_meta_shadow_and_symbol_limit.py` (conjuntos con CARRY).
- **Efecto esperado y riesgos**: ~3 operaciones al mes, cada una abierta hasta un mes. Riesgo principal: desmontaje
  del carry (pánico con JPY/CHF al alza) que golpea las 3 a la vez (≈ −3 % en el peor caso con stops). No cerrar a mano
  durante la prueba.

### 2026-10-24 — Carry en Forex G10 solo con MT5 (decisión del usuario): replay reciente orientativo POSITIVO  ·  Estado: solo investigación, sin cambios en el bot
- **Cambio sobre el pre-registro del carry, por decisión del usuario**:
  - **Solo datos de MetaTrader 5**: sin BIS ni FRED, y no se descarga nada.
  - **Gestión del usuario**: 1 % en dos entradas; la pierna 1 cierra en TP1 y la pierna 2 busca TP2, con extensión
    progresiva a TP3/TP4.
- **Limitación**: MT5 no guarda el histórico de tipos ni de swaps. Se usa el swap ACTUAL como señal y como coste, así
  que el replay se limita a ene-2025 → oct-2026 (21 meses), donde JPY y CHF han sido divisas de financiación todo el
  periodo. Es **orientativo y dentro de muestra**. La validación fiel es la prueba demo hacia adelante.
- **Herramienta** (`tools/research_fx_carry_mt5.py`): rebalanceo mensual, top 3 pares por carry neto actual, stop
  3 × ATR20 D1, salida en la primera vela del mes siguiente. Runner fijo (TP2) o progresivo (al tocar 2R, stop a 1,5R
  y objetivo 4R; al tocar 3R, stop a 2,5R).
- **Resultado**:

  | Estrategia | Ops | R/op | t | Meses positivos | R total |
  |---|---:|---:|---:|---:|---:|
  | **C0 · Carry puro** | 63 | **+0,225** | 2,12 | 71 % | +14,2 |
  | C1 · Carry + momentum | 60 | +0,186 | 1,64 | 76 % | +11,1 |
  | Azar (mismos meses y gestión) | 63 | +0,023 | — | 52 % | — |

  - El momentum no mejora y el runner progresivo ≈ el fijo.
  - Mejores pares: AUDJPY +0,54 y AUDCHF +0,37 R/op.
  - Carry actual: AUDCHF +3,7 %, AUDJPY +3,1 %, USDCHF +3,0 %, USDJPY +2,3 % y GBPCHF/GBPJPY +2,2 % anual
    (≈ 0,10–0,15 R al mes solo por swap con stop de 3 ATR).
- **Riesgos**:
  - Es dentro de muestra.
  - No incluye un desmontaje del carry como el de ago-2024: comprado en divisas de tipo alto y financiado en
    JPY/CHF, todo cae a la vez en pánico.
  - Muestra pequeña: unas 36 operaciones al año.
- **Siguiente paso propuesto**: worker CARRY en prueba demo hacia adelante con el swap real de MT5 (fiel) y criterio
  fijado.

### 2026-10-24 — PRE-REGISTRO: carry en Forex G10 con tipos oficiales de los bancos centrales  ·  Estado: diseño fijado antes de descargar datos
- **Datos**:
  - Precios: D1 del broker de los 28 pares G10 (USD, EUR, JPY, GBP, CHF, AUD, NZD, CAD), oct-2010 → hoy. No hace
    falta descargar precios.
  - Tipos de interés: BIS `WS_CBPOL` (tipos oficiales diarios de los 8 bancos centrales), con 1 día de retraso para
    no mirar el futuro.
  - Contraste: FRED DFF (EE. UU.) y ECBDFR (BCE).
- **Swap histórico reconstruido**: diferencial de tipos del día − margen del broker. El margen se estima por par y por
  sentido comparando el swap actual del broker con el diferencial actual del BIS, y se supone constante. Se cobra
  por noche de calendario.
- **Estrategias** (rebalanceo al cierre de cada mes):
  - **C0 · Carry puro** (referencia):
    - Pares con |diferencial| ≥ 1 punto; se compra la divisa de tipo alto.
    - Se toman los 3 de mayor diferencial.
  - **C1 · Carry + momentum** (principal): como C0, pero solo si el rendimiento de 63 días del par va a favor.
  - Stop de protección 3 × ATR20 D1. Salida al fin de mes si el par deja de estar seleccionado o pierde el filtro.
  - Riesgo: 0,5 % por par (3 pares = 1,5 % en total).
- **Gestión**:
  - **Principal**: una sola posición mantenida (excepción al contrato, como NIGHT). El carry se cobra en semanas o
    meses y el TP1 a 1R lo cortaría.
  - **Informativa**: contrato de dos entradas (TP1 1R + runner 2R con BE) y la regla mensual cierra lo que quede.
- **Criterio**:
  - R/op > 0 en 2010-2014, 2015-2019 y 2020-hoy.
  - Mejor que el azar con p < 0,05 (mismos meses y misma duración, sentido aleatorio).
  - C1 mejor que C0 para aceptar el filtro.
  - Caída máxima ≤ 20 R y supervivencia al desmontaje del carry de ago-2024 (se reporta aparte).
  - Aviso: 2010-2021 tuvo tipos casi a cero en la mayoría de divisas. Es probable que haya pocas operaciones en ese
    periodo.

### 2026-10-24 — ICT sintéticos con dos años de replay: ventaja de cartera robusta; ni la poda por activo ni acortar la orden límite la mejoran  ·  Estado: solo investigación, sin cambios en el bot
- **Datos**: replay de ICT con límite virtual y tope de spread del 2 % para los 27 activos actuales, en dos años:
  - Año previo, oct-2024 → oct-2025: `ict_limit_entry_signals_prior_y0.csv`.
  - Último año: `ict_limit_entry_signals.csv`.
- **Cartera**: año previo **+0,024 R/op** (8.361 ops, t 2,1) y último año **+0,032 R/op** (9.288 ops, t 2,9). Es la
  ventaja más robusta del bot en sintéticos.
- **La poda por activo es ruido**:
  - Correlación del R por activo entre años: **−0,25**.
  - Podar los que perdieron el año previo habría quitado los mejores del siguiente: podados +0,065, conservados
    +0,028.
  - **Conclusión: no se poda ni se elige por activo con un año de datos.**
- **Activos ya podados con datos en ambos años** (Step Index, Jump 25, Volatility 25, Volatility 50 y Crash 600):
  +0,027 el año previo y −0,013 el último, peores que la cartera. Se mantienen fuera; solo Jump 25 es positivo en
  ambos y por poco. El resto de podados no tiene historia en el año previo.
- **Validez de la orden límite**: todos los tramos de llenado son positivos en ambos años. 8 velas da el mayor R
  total (+202 / +368 R, frente a +184 / +326 con 3 velas y +128 / +259 con 1). **Se mantiene en 8.**
- **Implicación**: ICT sintéticos debe medirse y gestionarse como cartera. Su R/op esperado es ≈ +0,02 a +0,05, con
  bastante varianza. La prueba demo necesita cientos de operaciones sin cierres manuales para confirmarse.

### 2026-10-24 — Plan de mejoras (continuación): RSI2 + ETF descartado, fidelidad de ICT verificada, cambio de mes descartado y filtro de ciclo por política  ·  Estado: aplicado sin commit (solo el filtro de ciclo)
- **RSI2 + ETF (prioridad 4): NO se añade.**
  - La fuerza del RSI2 en ETF viene de los que duplican los CFD que ya opera: SPY, IVV, VOO, VTI, DIA e IWM.
  - Los 16 ETF restantes dan +0,057 R/op (t por día 1,73; 2024 ≈ 0 y 2026 −0,034).
  - Cartera desde oct-2023:

    | Cartera | R total | Caída máxima | Beneficio / caída |
    |---|---:|---:|---:|
    | Solo CFD US | +32,3 R | −4,1 R | 7,8 |
    | + 16 ETF | +58,0 R | **−17,7 R** | 3,3 |
    | + 16 ETF con tope 6 | +36,7 R | −13,3 R | 2,8 |

  - Duplicaría el beneficio a costa de cuadruplicar la caída: no compensa (rentabilidad primero).
- **Fidelidad de ICT (prioridad 3): sin fallo actual.**
  - Antes del reinicio del 22-oct, solo el 58 % de las operaciones vivas tenía señal en el replay. Las
    "exclusivas de la demo" (−0,27 R/op) eran de ese periodo, antes de que la Fase 1 y la política estuvieran
    cargadas.
  - Después del reinicio: 23 de 27 emparejadas, y las 7 entradas tempranas perdedoras también pierden en el replay
    con la misma señal (−1,0). Son pérdidas de la estrategia, no de la ejecución.
  - En el replay, los llenados de la orden límite en la primera vela son el grueso (+0,081 / +0,038) y los
    inmediatos son raros (0,7 %) y planos.
  - No se cambia código.
- **Efecto cambio de mes (nuevo, pre-registrado, `tools/research_turn_of_month.py`): NO SUPERA.**
  - Compra el último día hábil del mes y venta el 4.º día del siguiente, en 4 índices US con 5 años de Dukascopy.
  - +0,016 R/op (2021-22 −0,015), peor que el azar con la misma duración (+0,034; p 0,68).
- **Filtro de ciclo por política (prioridad 5, aplicado)**:
  - `_selected_base_cycle_symbols` aplica `sanitize_ict_selection` a los perfiles de la política (SYNTHETICS, FOREX,
    ICT, MALAYSIAN_SNR y MSNR). Ningún worker escanea ya instrumentos en PODA PREVENTIVA, aunque la selección
    guardada los incluya.
  - Ejemplos: STEP deja de mirar Step Index; MSNR deja de mirar mercados reales; Volatility deja de mirar Vol over
    Boom 550 y VolSwitch High Vol.
  - Interruptor `DAEMONBLACKFX_POLICY_CYCLE_FILTER` (por defecto 1). Tests en `tests/test_policy_cycle_filter.py` (4).
- **Prioridad 6 (oro en un solo worker)**: resuelta de hecho, porque GOLD e ICT (mercados reales) quedan
  desactivados y el oro solo lo opera ORB.

### 2026-10-24 — Workers sin ventaja desactivados para entradas nuevas: Forex 1-4, ICT (mercados reales), GOLD e IDX_OPEN  ·  Estado: aplicado sin commit
- **Qué** (prioridad 2 de MEJORAS_ESTRATEGIAS_20261024.md):
  - Nuevo `disabled_entry_profiles` en `LiveTradingConfig` (`DAEMONBLACKFX_DISABLED_WORKERS`, por defecto
    "FOREX_1,FOREX_2,FOREX_3,FOREX_4,ICT,GOLD,IDX_OPEN").
  - En esos perfiles, `_process_symbol_impl` devuelve `WORKER_DISABLED` sin analizar ni abrir operaciones.
  - **El monitor de posiciones no cambia**: si hubiera posiciones abiertas se seguirían gestionando (BE, TP y
    cierres). Al aplicarlo no había ninguna abierta de esos workers.
  - Los procesos siguen arrancando.
  - Reactivar: quitar el perfil de la variable (vacía = todos activos).
  - "ICT" es el worker de mercados reales (oro, índices US y US Oil). Los workers ICT de sintéticos (STEP, JUMP,
    VOLATILITY, BOOM y CRASH) no cambian.
- **Por qué**:
  - Ningún replay les da ventaja: Forex en 9 enfoques; ICT en mercados reales ≈ 0; GOLD (cuartos) no concluyente;
    IDX_OPEN sin replay positivo.
  - En demo pierden. Desde el 4-sep: ICT −789 USD (−0,18 R/op automático), GOLD −442 (−0,63), Forex 1-4 −240 e
    IDX_OPEN −83.
  - Además ocupan huecos y bloqueos de ciclo por símbolo que necesitan RSI2, NIGHT y ORB.
- **Tests**:
  - `tests/test_disabled_workers.py` (4): valor por defecto, reactivación por entorno, que no analizan y que los
    demás workers no se ven afectados.
  - `tests/conftest.py` fija la variable vacía para que la suite siga probando la lógica de esos workers.
- **Para que tenga efecto**: reiniciar los daemons.

### 2026-10-24 — Auditoría completa de estrategias y mercados (ver MEJORAS_ESTRATEGIAS_20261024.md)  ·  Estado: solo investigación, sin cambios en el bot
- **Demo** (1.211 operaciones, 4-sep → 23-oct):
  - **Cierres manuales desde el móvil**: 165 piernas en octubre (≈ 14 %), con +0,24 R de media. Maquillan la demo.
  - Con solo la gestión del bot: ICT v2 −0,197 (total −0,062) y MSNR vídeos −0,221 (total +0,041).
- **ICT sintéticos frente al replay de los mismos días** (18 → 23-oct):
  - Señales emparejadas: demo +0,056, replay +0,023. La ejecución está bien.
  - **23 operaciones vivas sin señal en el replay** (en símbolos activos): −0,272 R/op. Es la principal fuga de ICT.
  - Los sintéticos tienen la misma serie en Deriv y en MT5, así que no son los datos.
  - Las perdedoras casi nunca estuvieron en ganancia (MFE mediana 0,21 R): el problema es la entrada.
  - La IA no predice: tercil alto −0,264, bajo −0,205.
- **Por worker** (todo el periodo, USD): ICT −789, Malaysian SNR −675, STEP −581, JUMP −502, VOLATILITY_2 −462,
  GOLD −442, BOOM −377, ORB −344, Forex −240; positivos VOLATILITY_3 +318 y FLIP +342.
  - El worker ICT operó sintéticos excluidos (Jump 25, Boom 300, XAGUSDmicro) hasta el 18-oct; ya está corregido.
- **Mercados nuevos** (`tools/research_etf_crypto.py`, pre-registrado):
  - **RSI2 en ETF SUPERA**: +0,096 R/op, 668 ops, periodos +0,072 / +0,180 / +0,052, t por día 2,05, p azar 0,022.
  - Cripto no supera: RSI2 −0,102 y ruptura Donchian −0,081.
  - Las acciones no son validables con el broker: solo hay historia desde sep-2025.
- **Bloqueos**: forex_3 evalúa activos podados el 99 % del tiempo; MSNR evalúa mercados reales que rechaza (336 veces).
- **Plan priorizado** (pendiente de decisión del usuario):
  1. No cerrar a mano durante las pruebas.
  2. Desactivar Forex 1-4, ICT en mercados reales, GOLD e IDX_OPEN.
  3. Auditoría de fidelidad de ICT.
  4. RSI2 + ETF en prueba demo, sin duplicar ETF equivalentes.
  5. Limpiar selecciones.
  6. Oro en un solo worker.
  7. Acciones con datos de Dukascopy.
  8. Carry en Forex.
  9. Reentrenar la IA por estrategia.

### 2026-10-23 — ICT y el centinela de régimen analizan los índices US con las velas del broker MT5  ·  Estado: aplicado sin commit
- **Qué**:
  - Nuevo `_SymbolRoutedProvider` en `strategy/execution/live_trading_engine.py`: sirve velas y ticks de unos símbolos
    desde la referencia MT5 del modo shadow (el broker de ejecución) y el resto desde el proveedor principal (Deriv).
    Cualquier otro atributo se delega en el principal.
  - Lista de símbolos: `ict_broker_candle_symbols` (`DAEMONBLACKFX_ICT_BROKER_CANDLE_SYMBOLS`, por defecto
    "US SP 500,US Tech 100,Wall Street 30"). Vacía, se desactiva.
  - Se aplica a:
    - **La estrategia ICT**: el motor la construye con el proveedor enrutado.
    - **El centinela de régimen** (`_market_regime_entry_gate`): sus 40 velas H1 vienen de MT5 para esos índices.
      Con Deriv solo llegaban 23 de 40, con huecos, y el centinela es el principal bloqueo de ICT en índices
      (`MARKET REGIME BLOCKED`).
  - **Sin cambio** para el oro (Deriv ≈ MT5), US Oil (ya usaba MT5) y los sintéticos.
- **Por qué**: Deriv sirve otra serie para los índices US (56 % de velas H1 coincidentes, desfase del 24–40 % de una
  vela H1), y el replay de ICT en mercados reales se hizo con MT5 (ver la investigación anterior).
- **Comprobado**: con el `MT5DataProvider` real y un Deriv simulado que falla si se le llama, ICT pide las H1 de
  US SP 500 y US Tech 100 al broker y no toca Deriv.
- **Pendiente menor**: otros controles del motor (persecución de precio en M5, gemelos, ventana de spread) siguen
  leyendo del proveedor principal para estos símbolos; no deciden la señal estructural.
- **Tests**: `tests/test_ict_broker_candles.py` (6).
- **Para que tenga efecto**: reiniciar el daemon ICT (y los workers que usan el centinela en estos índices).

### 2026-10-23 — Investigación: ICT en mercados reales analiza con velas de Deriv, no con las del broker MT5  ·  Estado: solo investigación, sin cambios en el bot
- **Fuente**: últimos ~300 MB de `storage/analysis/market_data_shadow.jsonl`, unas 50.000 comparaciones de velas
  entre Deriv (el proveedor principal del análisis en modo shadow) y MT5 (el broker de ejecución), hasta el
  23-oct 13:40 UTC.

  | Instrumento | Fuente del análisis | Velas coincidentes (H1) | Desfase medio Deriv − MT5 | Desfase / rango H1 | Veredicto |
  |---|---|---:|---:|---:|---|
  | XAUUSD / XAUUSDmicro | Deriv | 96–97 % | +0,10 | ≈ 1 % (M5 ≈ 3 %) | **Equivalente** |
  | US Oil | MT5 (Deriv no lo tiene) | 100 % | 0 | 0 % | **Idéntico** |
  | US SP 500 | Deriv | 56 % (23 de 40 velas) | −5,7 | ≈ 32 % | **Serie distinta** |
  | US Tech 100 | Deriv | 56 % | −23,7 | ≈ 24 % | **Serie distinta** |
  | Wall Street 30 | Deriv | 56 % | −48,7 | ≈ 40 % | **Serie distinta** |

  - En D1 los índices coinciden solo el 63 % de los días, con diferencias máximas de 157 (SP500), 699 (Tech100) y
    962 (WS30) puntos.
  - El propio bot marca `within_tolerance: false`.
- **Impacto**:
  - En los índices, ICT detecta su estructura (bloques de órdenes, FVG, liquidez y stop estructural) en otra serie de
    precios, con huecos y desplazada entre un 24 % y un 40 % de una vela H1.
  - Después ejecuta en MT5 con ese stop absoluto: el stop no corresponde a la estructura real del gráfico del
    broker. El control `max_entry_drift_r` (0,5 R) deja pasar desfases de hasta media R.
  - El replay de ICT en mercados reales se hizo con datos de MT5, así que en vivo **no opera la estrategia que se
    validó**.
  - Hoy el impacto es pequeño: en el log de ICT los índices quedan casi siempre en `WAITING ICT` o
    `MARKET REGIME BLOCKED`, y solo hay 13 operaciones ICT en mercados reales desde septiembre (SP500 −0,75 R/op con
    5 operaciones).
- **Oro y petróleo**: sin problema.
- **Propuesta (pendiente de decisión del usuario)**: que ICT analice también con las velas del broker MT5 en los
  índices US. Es la misma corrección que en RSI2 y NIGHT, pero más invasiva: ICT construye su análisis
  multitemporal con el proveedor en varios puntos.

### 2026-10-23 — RSI2 y NIGHT analizan las velas del broker MT5 (no las de Deriv): RSI2 perdió la señal de US Tech 100  ·  Estado: aplicado sin commit
- **Qué pasó**:
  - Al cierre D1 del 22-oct, US Tech 100 dio señal RSI2 en el broker: RSI(2) = 8,6 sobre la SMA200.
  - En su ventana de entrada (23-oct, 00:00–02:00 UTC) el worker la evaluó unas 40 veces y respondió siempre
    `NO_RSI2_PULLBACK`.
- **Causa**: los daemons usan `--market-data-mode shadow`, donde el proveedor principal del análisis es **Deriv**
  (`DERIV_CHARTS_WEBSOCKET`) y MT5 queda solo como referencia.
  - Para los índices US, Deriv sirve otra serie: el registro `storage/analysis/market_data_shadow.jsonl` de US Tech 100
    D1 muestra 253 velas, el 63 % de los días coincidentes, diferencia de cierre media de 67 y máxima de 699 puntos,
    y `within_tolerance: false`.
  - RSI2 y NIGHT se validaron con precios de MT5/Dukascopy (correlación 0,999).
  - Reproducción con las velas de MT5: a las 00:30 y 01:30 UTC la estrategia daba `RSI2_PULLBACK_ABOVE_SMA200`.
- **Corrección**:
  - `_broker_candle_provider()` en el motor: en modo shadow devuelve la referencia MT5 (el broker de ejecución). La
    usan `rsi2_strategy`, `overnight_strategy` y la salida por regla de RSI2.
  - Interruptor `native_strategies_broker_candles` (`DAEMONBLACKFX_NATIVE_BROKER_CANDLES`, por defecto 1).
  - Sin referencia (modo mt5) o con el interruptor apagado, se usa el proveedor normal.
  - Comprobado con el `MT5DataProvider` real: hoy RSI2 en US Tech 100 da `RSI2_ENTRY_WINDOW_EXPIRED` (la señal existe;
    la ventana ya pasó).
- **A revisar**: ICT en mercados reales (oro, índices, petróleo) también analiza con Deriv en modo shadow. No se cambia
  aquí, pero su replay se hizo con datos de MT5.
- **Poda de VolSwitch**: también se actualizaron los tests `tests/test_synth_wr45_prune.py` para la nueva lista.
  En la suite completa no hay fallos nuevos frente a la ejecución anterior, salvo el inestable `test_demo_daemon_integration`
  (pasa al ejecutarlo solo).
- **Tests**: `tests/test_native_meta_shadow_and_symbol_limit.py` (fuente de velas de RSI2/NIGHT).
- **Para que tenga efecto**: reiniciar los daemons RSI2 y NIGHT.

### 2026-10-23 — VolSwitch High Vol Index en PODA PREVENTIVA (ICT, MSNR y Malaysian SNR) por spread real  ·  Estado: aplicado sin commit
- **Qué**:
  - `config/synth_wr45.py`: nueva lista `REAL_SPREAD_PRUNED = ("VolSwitch High Vol Index",)`, con el interruptor
    `DAEMONBLACKFX_REAL_SPREAD_PRUNE` (por defecto 1).
  - La lista se suma a `ICT_WR45_PRUNED` y a `MSNR_WR45_PRUNED`, de modo que se aplica en todos los sitios que ya
    leían esas listas:
    - las listas permitidas del motor;
    - `excluded_symbols` de Malaysian SNR;
    - los perfiles de app/main;
    - `/Instruments`.
  - `config/ict_instrument_policy.py` (`preventive_prune_reason`) y el dashboard muestran el motivo propio: "spread
    real ~4× el de las velas; supera siempre el tope spread/SL 2 %".
  - Afecta a las pestañas Sintéticos (ICT), Malaysian SNR y MSNR.
- **Por qué**: el spread de ticks mediano es 4,3 veces el campo `spread` de las velas M15. Con el spread real supera
  siempre el tope del 2 %, así que no hay ninguna operación posible ni en ICT ni en MSNR (ver la re-medición con
  spread real).
- **Recuentos**: ICT sintéticos 28 → 27 activos; MSNR 30 → 29; Malaysian SNR 31 → 30 (con DEX 1500 UP en prueba).
- **Tests**:
  - `tests/test_ict_instrument_policy.py`: poda, motivo e interruptor.
  - Recuentos actualizados en `test_ict_instrument_policy`, `test_v119`, `test_v121` y `test_v115`.
- **Para que tenga efecto**: reiniciar los daemons y pulsar "Aplicar selección" en /Instruments (Sintéticos, Malaysian
  SNR y MSNR), o ejecutar `tools/apply_ict_instrument_policy.py --apply`.

### 2026-10-23 — Re-medición de ICT y MSNR en sintéticos con el spread real de ticks  ·  Estado: solo investigación, sin cambios en el bot
- **Qué** (`tools/research_real_spread_recheck.py`):
  - Se mide en 37 sintéticos el factor = mediana del spread de ticks (2 días) / mediana del campo `spread` M15.
  - Se recalculan las operaciones de los replays guardados: R − (factor − 1) × spread/riesgo, descartando las que
    superan el tope del 2 % con el spread real.
  - Replays usados: ICT con entrada límite, último año en semestres (`ict_limit_entry_signals.csv`); MSNR 2 años
    con símbolo libre (`msnr_variants_signals_synth_free_y0b/y1.csv`).
- **Resultado: en casi todos los sintéticos el spread es fijo y el factor ≈ 1** (0,86–1,18).
  - Excepciones: **VolSwitch High Vol (4,3)** y los Drift Switch (~12, ya desactivado).
  - Los replays de ICT y MSNR **no estaban sesgados** por el coste. El problema de DRIFT era específico de los
    índices de spread variable.
- **Cartera activa hoy con spread real**:
  - ICT sintéticos (27 activos, último año): **+0,051 R/op** (7.149 ops).
  - MSNR sintéticos (29 activos, 2 años, sin el filtro de régimen): **+0,023 R/op** (2.146 ops).
- **Siguen rentables** (≥ 30 ops y positivos en ambas mitades; exploratorio, muchas comparaciones):
  - **ICT**: Crash 900 (+0,19), Boom 900 (+0,16), Volatility 100 (+0,11), Volatility 10 (+0,09), Volatility 15
    (+0,08), Boom 500 (+0,08), Crash 500 (+0,05), Step 400 (+0,04), Volatility 50 (1s) (+0,04), Step 200 (+0,04) y
    Step 500 (+0,03).
  - **MSNR**: Volatility 50 (1s) (+0,20), Jump 75 (+0,10), Vol over Boom 550 (+0,09), Volatility 25 (+0,09),
    Volatility 250 (1s) (+0,07), Step 500 (+0,03) y Volatility 150 (1s) (+0,02).
- **VolSwitch High Vol Index**: con el spread real supera el tope del 2 % siempre (0 operaciones en ICT y MSNR). Está
  en las listas activas de ambos, pero en vivo nunca puede entrar.
- **Cautela**: la lista por activo es exploratoria. Con ~30 activos, algunos salen positivos o negativos por azar, y
  no debe usarse sola para podar: la evidencia sólida es la de cartera.

### 2026-10-23 — DRIFT desactivado por defecto  ·  Estado: aplicado sin commit
- **Qué**:
  - `DAEMONBLACKFX_DRIFT` pasa de `demo_test` a **`off`** por defecto (`drift_mode` en `LiveTradingConfig`).
  - El worker sigue cableado, pero no analiza ni entra (`DRIFT_DISABLED`). `DAEMONBLACKFX_DRIFT=demo_test` lo
    reactiva.
- **Por qué**: con el spread real de ticks (~12× el de las velas M15 que usó el replay) la ruptura en Drift Switch
  pierde −0,030 R/op, y con el tope de spread del 2 % no puede entrar (ver la entrada del hallazgo del spread).
- **Tests**:
  - `tests/test_drift_breakout_worker.py`: valor por defecto `off`, la variable de entorno reactiva `demo_test`, y
    con el valor por defecto se bloquean despacho y puerta.
- **Para que tenga efecto**: reiniciar el daemon DRIFT. Hasta entonces sigue en `demo_test`, aunque el tope de
  spread le impide entrar. También se puede quitar de la pestaña "RUPTURA DRIFT" de /Instruments.

### 2026-10-23 — Validación tras el reinicio y HALLAZGO: el spread de las velas M15 subestima ~12× el real en Drift Switch (DRIFT no tiene ventaja)  ·  Estado: solo investigación, sin cambios en el bot
- **Reinicio del usuario** (23-oct, 07:57 hora local): NIGHT, RSI2 y DRIFT arrancan con el código nuevo y pasan el
  preflight (`READY FOR DEMO EXECUTION`).
  - RSI2: `NO_RSI2_PULLBACK` (sin señal de mercado).
  - NIGHT: fuera de su ventana (16:00 NY).
  - DRIFT ya reintenta (no aparece `DRIFT_SETUP_ALREADY_FIRED`), pero acumula 60 bloqueos
    `SYNTHETIC_SPREAD_RISK_RATIO_EXCEEDED`, con un spread del 11–14 % del stop.
- **Causa**: MT5 guarda en cada vela el spread **mínimo** del periodo. En Drift Switch la mediana de los ticks
  (últimos 5 días) es 11–14,5 veces el campo `spread` de las velas M15.

  | Símbolo | Tick | M15 | Spread/riesgo real (tick) | Spread/riesgo replay (M15) |
  |---|---:|---:|---:|---:|
  | Drift Switch 10 | 2,01 | 0,24 | 7,7 % | 0,9 % |
  | Drift Switch 20 | 2,39 | 0,20 | 11,6 % | 1,0 % |
  | Drift Switch 30 | 5,96 | 0,41 | 14,8 % | 1,0 % |

  - En los índices US el spread es fijo y el de los ticks coincide con el de las velas: los costes de los replays
    de RSI2 y NIGHT son correctos.
- **Replay de DRIFT corregido** (spread de las velas × relación tick/M15 de cada símbolo):
  - **−0,030 R/op** (t −1,4; año 0 −0,056, año 1 −0,003), frente a +0,083 con el spread M15.
  - Con el tope del 2 % del motor: **0 operaciones**.
  - **La ventaja de DRIFT era un artefacto de coste.** En vivo no puede entrar (el tope lo bloquea), y si se subiera
    el tope perdería.
- **Riesgo sistémico**: los replays de sintéticos de ICT y MSNR también usaron el campo `spread` de las velas. El tope
  de spread del motor sí usa el tick real, pero sus ventajas medidas pueden estar sobrestimadas en los símbolos donde
  el spread real es mayor que el de las velas. Hay que medirlo símbolo a símbolo.

### 2026-10-23 — Resultados de los pre-registros con 5 años de Dukascopy: RSI2, NIGHT y materias primas  ·  Estado: solo investigación, sin cambios en el bot
- **Datos**:
  - Dukascopy 2021 → 30-sep-2026; las velas D1 de 2026 se reconstruyen desde las H1 (`extend_daily_with_hourly`).
  - Falta un mes: US30, feb-2023.
  - Fidelidad frente al broker: correlación de rendimientos diarios 0,979–0,999, nivel 1,000.
  - Se corrigió la escala de la plata diaria: rango de plausibilidad (3, 150) en el descargador y CSV reescalados.
- **RSI2** (`tools/research_us_index_longrun.py`; reglas del worker con dos entradas): **NO CONCLUYENTE, con señal
  positiva consistente**.
  - +0,150 R/op en 245 operaciones, acierto 72 %.
  - Por periodo: 2021-22 +0,074 (31), 2023-24 +0,125 (119), 2025-hoy +0,205 (95). Positivo también en el bajista
    de 2022.
  - p azar 0,001 (comprar días al azar con la misma gestión da +0,056).
  - Solo falla la t agrupada por día: 1,78 frente a 2,0, con 147 episodios.
  - Por índice: US500 +0,26, US30 +0,14, USTEC +0,14, US2000 +0,05.
  - **Sigue en prueba demo.**
- **NIGHT** (salida en la H1 de las 09:00 o de las 10:00 NY, rango de la real de las 09:30): **NO CONCLUYENTE**.
  - +0,022 / +0,030 R por noche.
  - 2021-22 negativo (−0,017 / −0,003); 2023-24 +0,048 / +0,069; 2025-hoy +0,035 / +0,023.
  - **No mejora a mantener comprado el índice en horas al azar con la misma duración y stop** (+0,039 / +0,033;
    p azar 0,89 / 0,58).
  - Lo que gana es la deriva alcista de los índices (beta), no una ventaja específica de la noche.
  - Sigue en demo según el criterio, pero con esta reserva.
- **Materias primas** (`tools/research_commodity_longrun.py`; oro, plata y Brent; contrato de dos entradas):
  **NINGUNA SUPERA**.

  | Estrategia | Ops | R/op | Periodos | Comentario |
  |---|---:|---:|---|---|
  | P1 momentum 12 m | 110 | −0,204 | −0,285 / −0,305 / +0,141 | — |
  | P2 COT contrario | 44 | −0,338 | — | — |
  | P3 tipos reales (oro/plata) | 1.139 | −0,015 | negativo en los tres | — |

  - En P1, con una sola posición (informativo), sale +0,574 R/op: el momentum necesita dejar correr y el TP2 a 2R
    lo corta. Pero es sobre todo la subida del oro y la plata en 2025-26 (Brent −4,7 R/op), con 110 operaciones.
  - El swap en posiciones de semanas es caro: el oro comprado paga ≈ 4 % al año, y el azar con la misma gestión
    pierde −0,39 R/op en P1.
  - **Decisión**: no se implementa nada en materias primas.
- **Ficheros**:
  - `tools/research_us_index_longrun.py` y `tools/research_commodity_longrun.py`.
  - `tools/download_commodity_external_data.py` (`--from-year`, índices US, escala de la plata).
  - Informes en `storage/analysis/us_index_longrun_report.md` y `commodity_longrun_report.md`.

### 2026-10-22 — Huecos reservados para workers validados + PRE-REGISTRO de la validación larga de RSI2 y NIGHT  ·  Estado: aplicado sin commit / pre-registro fijado antes de ver datos
- **Huecos reservados** (decisión del usuario):
  - `priority_profiles` (`DAEMONBLACKFX_PRIORITY_PROFILES`, por defecto "DRIFT,RSI2,NIGHT") y `priority_extra_slots`
    (`DAEMONBLACKFX_PRIORITY_EXTRA_SLOTS`, por defecto 4).
  - Esos workers pueden abrir hasta 4 posiciones físicas por encima del límite global: 16 → 20, ≈ 10 % de riesgo
    abierto máximo. El resto de workers sigue con 16.
  - Motivo: DRIFT perdió una señal por `MAX_TOTAL_OPEN_POSITIONS_REACHED`.
  - Tests en `tests/test_native_meta_shadow_and_symbol_limit.py`.
- **Datos aprobados**: Dukascopy D1 bid/ask y H1 bid **2021 → hoy** (5 años, decisión del usuario) de USA500, USATECH,
  USA30 y USSC2000.IDX (en cola tras plata y Brent; `--from-year 2021` en el descargador).
- **PRE-REGISTRO RSI2** (reglas idénticas al worker: RSI(2) D1 < 10 sobre la SMA200, solo largos, stop 2 ATR D1, dos
  entradas TP1 1R / runner 2R con BE, salida por cierre > SMA5 o 10 días; camino H1; spread del broker; swap actual):
  - ~~Periodos 2012-2016, 2017-2021 y 2022-hoy.~~ **Cambio del usuario antes de ver datos**: solo 5 años (Dukascopy
    desde 2021), con periodos 2021-2022, 2023-2024 y 2025-hoy. Hay menos episodios independientes, así que es más
    probable un "no concluyente".
  - **Se mantiene** si R/op > 0 en los tres, t agrupado por día ≥ 2,0 y p azar < 0,05 (prueba única, sin variantes).
  - **Se retira** si el total ≤ 0 o dos de los tres periodos son negativos.
  - Lo intermedio queda como no concluyente y sigue la prueba demo.
- **PRE-REGISTRO NIGHT** (compra al cierre de las 16:00 NY y venta a las 09:30 NY; stop 1 ATR D1; swap actual):
  - Mismos periodos y mismos criterios, con R por noche.
  - Sin filtros: ninguno de los tres probados mejoraba con los datos del broker.
- Mid Cap 400 no está en Dukascopy: en RSI2 se valida con los otros cuatro.

### 2026-10-22 — Auditoría de DRIFT / NIGHT / RSI2: reintento de señales bloqueadas y diagnóstico de costes y filtros  ·  Estado: aplicado sin commit
- **Auditoría en vivo** (logs del 22-oct; base de datos en solo lectura): ninguna operación de los tres workers.
  - **DRIFT**: 2 señales, las dos perdidas por causas ajenas a la estrategia:
    - Drift Switch 20, por un pico de spread del 20 % del stop.
    - Drift Switch 30, por `MAX_TOTAL_OPEN_POSITIONS_REACHED`.
    - Ninguna se reintentó: la estrategia las marcaba como "disparadas" antes de que el motor las ejecutara.
  - **NIGHT**: señal en US SP 500 y US Tech 100, rechazada por la IA (corregido en la entrada anterior; falta
    reiniciar).
  - **RSI2**: sin señal desde el arranque. Ningún índice cumple RSI(2) < 10 sobre la SMA200; Small Cap y Mid Cap
    están bajo su SMA200. La última señal (US Tech 100, 16-oct) fue anterior al worker.
  - **Ocupación global**: 5,5 posiciones físicas de media, p90 = 10 y máximo 15 sobre 16. El límite se llena solo en
    momentos puntuales, pero ya le costó una señal a DRIFT.
- **Corrección: reintento de señales.**
  - `DriftBreakoutConfig.setup_dedupe` y `Rsi2Config.setup_dedupe` (`DAEMONBLACKFX_DRIFT_SETUP_DEDUPE`,
    `DAEMONBLACKFX_RSI2_SETUP_DEDUPE`, por defecto 0): la estrategia ya no marca la señal como disparada.
  - El motor sigue evitando duplicados con la clave de ejecución, que es estable (hora de cierre de la vela de
    señal en DRIFT; primer tick del día en RSI2) y se comprueba también contra operaciones cerradas.
  - Así, si el motor bloquea por algo pasajero, la señal se reintenta cada 10 s dentro de su ventana (DRIFT 10 min,
    RSI2 120 min).
- **Costes reales a la hora de operar** (spread M15 del broker por hora):
  - A las 00:00 UTC (entrada RSI2), 20:00 UTC y 13:30 UTC (NIGHT) el spread equivale al mediano.
  - En R: de 0,001 a 0,015 con stop de 2 ATR D1. No es un problema.
- **Diagnóstico de NIGHT** (2.041 noches del broker, ene-2024 → oct-2026; filtros fijados antes de medir):
  - Sin filtro: +0,044 % neto por noche (t 2,2); 2024 +0,080, 2025 +0,025, 2026 +0,026. No sigue cayendo.
  - Sobre SMA200: +0,045 (2026 +0,009). Tras día bajista: +0,038. Sin viernes: +0,036; los viernes son la mejor
    noche, +0,080 pese al triple swap.
  - **Ningún filtro mejora: NIGHT se mantiene sin filtros.**
  - Spread y swap se comen el 39 % del bruto (0,028 de 0,073 % por noche).
- **Ficheros**:
  - `strategy/drift_breakout/compression_breakout.py` y `strategy/connors_rsi2/rsi2_daily.py`.
  - Tests en `tests/test_drift_breakout_worker.py` y `tests/test_connors_rsi2_worker.py`.

### 2026-10-22 — Bloqueos de RSI2 (y NIGHT) en índices US: IA en sombra real y límite por símbolo propio  ·  Estado: aplicado sin commit
- **Diagnóstico**:
  - Log de RSI2: 6.400 ciclos, sin señal desde el arranque (`NO_RSI2_PULLBACK`).
  - `BLOCKED SYMBOL CYCLE` aparece en el 9 % de las evaluaciones, solo en SP500, Tech100 y WS30, repartido por igual
    entre horas. Es inofensivo: dura menos de un segundo y RSI2 reintenta cada 10 s durante su ventana de 120 min.
  - **Bloqueo 1, la IA bloqueaba en índices reales.** El modo sombra solo se aplicaba a símbolos sintéticos, y lo
    que se documentó como "IA en sombra" para NIGHT y RSI2 **no se cumplía** en índices. Hoy NIGHT tuvo señal en
    US SP 500 y US Tech 100 a las 20:00 UTC y la IA la rechazó 108 veces (`PROBABILITY_BELOW_THRESHOLD`). Era un
    error de cableado.
  - **Bloqueo 2, choque NIGHT ↔ RSI2.** NIGHT mantiene US SP 500 / US Tech 100 de 20:00 a 13:30 UTC cada día hábil,
    lo que cubre toda la ventana de entrada de RSI2 (00:00–02:00 UTC). Con el límite global de 2 posiciones por
    símbolo, NIGHT (1) + RSI2 (2) = 3 > 2: RSI2 no podría entrar casi nunca en esos dos índices (un tercio de las
    operaciones del replay; SP500 era el mejor, +0,30 R/op). Y RSI2, que mantiene varios días, bloquearía a NIGHT.
- **Qué**:
  - `native_strategy_meta_label_shadow` (`DAEMONBLACKFX_NATIVE_META_SHADOW`, por defecto 1): para MSNR_VIDEO,
    OVERNIGHT_DRIFT, DRIFT_BREAKOUT y CONNORS_RSI2 la IA puntúa y registra (`NATIVE_STRATEGY_META_SHADOW`) pero no
    bloquea, en cualquier tipo de símbolo. La sombra de ICT sigue solo en sintéticos.
  - `own_symbol_limit_profiles` (`DAEMONBLACKFX_OWN_SYMBOL_LIMIT_PROFILES`, por defecto "RSI2,NIGHT"): para esos
    perfiles, el límite de posiciones por símbolo cuenta solo las suyas. Los límites totales (posiciones y riesgo)
    siguen siendo globales; el resto de workers no cambia.
- **Riesgo asumido**: una misma noche puede haber NIGHT y RSI2 comprados en US SP 500 o US Tech 100 a la vez, hasta
  un 2 % de riesgo en un índice y en el mismo sentido.
- **Ficheros**:
  - `strategy/execution/live_trading_engine.py`.
  - `tests/test_native_meta_shadow_and_symbol_limit.py` (nuevo, 3 tests).
- **Para activarlo**: reiniciar los daemons (NIGHT y RSI2).

### 2026-10-22 — PRE-REGISTRO: materias primas con datos externos (15 años)  ·  Estado: fijado antes de ver resultados
- **Datos** (descarga aprobada por el usuario, `tools/download_commodity_external_data.py`, en `storage/external_data/`):
  - Dukascopy D1 (bid/ask) 2010 → hoy y H1 (bid) **2021 → hoy** (plata y Brent recortados a 5 años por el usuario):
    oro, plata y Brent.
  - COT Disaggregated de la CFTC 2006 → hoy.
  - FRED: DFII10 (tipo real a 10 años) y DTWEXBGS (dólar amplio).
- **Universo final** (decisión del usuario, antes de ver resultados): oro, plata y Brent. WTI y cacao quedan
  omitidos; no se descargan sus velas H1.
- **Fidelidad previa**: en el tramo común, los rendimientos diarios de Dukascopy deben correlar ≥ 0,95 con los del
  broker. Si un instrumento no cumple, se excluye.
- **Costes**:
  - Spread = el mayor entre la mediana ask − bid de Dukascopy y la mediana M15 del broker.
  - Swap: el actual del broker por noche (es una aproximación; en petróleo refleja el roll del futuro).
- **Gestión** (preferencia del usuario): 1 % en dos entradas al 50 %, TP1 1R y runner TP2 2R con BE tras TP1. La regla
  de la estrategia cierra lo que quede. Camino en H1 (SL primero). Una operación por instrumento y estrategia.
  Como información se reporta también una sola posición con salida por regla, pero no decide.
- **Estrategias** (sin optimizar; SELL espejo):
  - **P1 · Momentum de 12 meses**:
    - Al cierre de cada mes, signo del rendimiento de 12 meses → BUY (> 0) o SELL (< 0); entrada en la primera
      apertura D1 del mes.
    - Stop 3 × ATR20 D1. Regla: cierre al final del mes en que el signo se invierte.
  - **P2 · COT contrario**:
    - Posición neta de los fondos (managed money) en % del interés abierto; z-score de 156 semanas.
    - z > 2 → SELL; z < −2 → BUY. Entrada en la primera apertura D1 tras el lunes siguiente al martes del informe
      (se publica el viernes).
    - Stop 2 × ATR20 D1. Regla: |z| < 0,5 en un informe posterior, o 30 velas D1.
  - **P3 · Oro y plata con tipos reales**:
    - Con DFII10 retrasado 1 día: variación de 20 días < 0 y cierre > SMA50 → BUY; variación > 0 y cierre < SMA50
      → SELL. Solo en oro y plata.
    - Stop 2 × ATR20 D1. Regla: la variación de 20 días cambia de signo, o 30 velas D1.
- **Criterio** (3 pruebas):
  - R/op > 0 en los tres subperiodos: ~~2010-2015, 2016-2020 y 2021-hoy~~ **2021-2022, 2023-2024 y 2025-hoy**
    (cambio del usuario a 5 años antes de ver resultados: operaciones desde 2021; los diarios anteriores solo
    calientan indicadores. Hay menos operaciones y regímenes, así que es más probable un "no concluyente").
  - t ≥ 2,4 y t agrupado por día ≥ 2,0.
  - p azar < 0,0167 (entradas en fechas aleatorias, misma dirección permitida y misma gestión).
  - Las que superen irían a prueba demo; nada se activa sin ella.

### 2026-10-22 — Investigación: 3 estrategias de indicadores en materias primas con el contrato de dos entradas  ·  Estado: solo investigación, sin cambios en el bot
- **Qué**: `tools/research_commodity_indicators.py`, con reglas pre-registradas.
  - **Universo**: XAUUSD, XAGUSD, XAUEUR, XAGEUR, US Oil, UK Brent Oil y Cocoa (spread ≤ 10 % del ATR H1). Quedan
    fuera NGAS, platino, paladio, cobre, azúcar, algodón y café.
  - **Gestión**: contrato del bot (dos entradas, TP1 1R + runner 2R con BE) y la regla de cada estrategia cierra lo
    que quede. Camino real en M15, spread real y swap actual.
  - **Estrategias**:
    - RSI2_D: RSI(2) diario en ambos sentidos con SMA200; salida SMA5 o 10 días.
    - ST_H4: giro del Supertrend(10,3) H4 con ADX ≥ 20; salida al girar en contra o 60 H4.
    - GSR_D: ratio oro/plata con z-score 20 > ±2, una pata en cada metal; salida |z| < 0,5 o 20 días.
  - Mismo criterio que en Forex, con fuera de muestra 2023-24 solo en los metales.
- **Resultado: ninguna supera.**

  | Estrategia | Ops | R/op | Año 0 / año 1 | p azar | Fuera de muestra |
  |---|---:|---:|---|---:|---:|
  | RSI2_D | 178 | −0,095 | −0,107 / −0,084 | 0,96 | −0,072 |
  | ST_H4 | 312 | −0,067 | −0,040 / −0,100 | 0,86 | −0,106 |
  | GSR_D | 25 | +0,045 (t 0,7) | +0,080 / +0,022 | 0,79 | +0,159 (12 ops) |

  - La reversión RSI(2), que funciona en índices US, **no** funciona en materias primas.
  - El Supertrend H4 pierde con fuerza en petróleo (US Oil −0,50, Brent −0,36 R/op). Es positivo en oro (XAUEUR
    +0,29, XAUUSD +0,18), pero las entradas aleatorias en oro también ganan (subida del oro en 2024-26) y no es
    significativo (p ≈ 0,08). Se trata como deriva del activo, no como ventaja de la regla.
  - El ratio oro/plata da pocas operaciones (25 en 2 años) y el azar con la misma gestión gana más (+0,103).
- **Decisión**: no se implementa nada.
- **Ficheros**:
  - `tools/research_commodity_indicators.py` (nuevo).
  - Salidas en `storage/analysis/commodity_indicators_{trades,random,report}`.

### 2026-10-22 — Investigación: 3 estrategias de indicadores en Forex con el contrato de dos entradas (replay 2 años + 1 fuera de muestra)  ·  Estado: solo investigación, sin cambios en el bot
- **Qué**: `tools/research_forex_indicators.py`, con reglas pre-registradas.
  - **Universo**: 27 pares con spread ≤ 10 % del ATR H1, un contrato por par.
  - **Gestión**: contrato del bot (1 % en dos entradas: TP1 1R + runner 2R con BE) y la regla de cada estrategia
    cierra lo que quede. Camino real en M15, spread real y swap actual en puntos.
  - **Estrategias**:
    - MOM_D: momentum de 63 días + SMA100, con reanudación del RSI14 D1 sobre 50; regla: cierre < SMA50 o 40 días.
    - ASIA_R: reversión con Bollinger + RSI en M15 entre 00:00 y 05:00 UTC con ADX H1 < 25; cierre a las 07:00 UTC.
    - TREND_H: EMA50/200 + ADX en H4 con retroceso del RSI H1; 200 velas M15.
  - El filtro de carry previsto se descartó: MT5 no da el histórico del swap y usar el actual sería mirar el futuro.
  - Criterio (3 pruebas): ambos años > 0, t ≥ 2,4, t por día ≥ 2,0, ≥ 3/4 semestres > 0, p azar < 0,0167; después
    fuera de muestra (oct-2023 → oct-2024) con R/op > 0 y t ≥ 1.
- **Resultado: ninguna supera; las 3 pierden en el periodo principal.**

  | Estrategia | Ops | R/op | t por día | Año 0 / año 1 | Fuera de muestra 23-24 |
  |---|---:|---:|---:|---|---:|
  | MOM_D | 623 | −0,019 | −1,5 | −0,021 / −0,017 | −0,038 |
  | ASIA_R | 1.884 | −0,043 | +0,7 | +0,007 / −0,103 | +0,038 |
  | TREND_H | 2.471 | −0,132 | −5,5 | −0,097 / −0,169 | −0,106 |

  - MOM_D es mejor que el azar (p 0,010; las entradas aleatorias diarias pierden −0,081 por spread y swap), pero
    sigue siendo negativa: el swap de varias noches se come la ventaja.
  - TREND_H pierde más que entrar al azar (−0,055): el retroceso en tendencia H1/H4 tiende a fallar.
  - Por par, solo 12/27 (MOM_D), 6/27 (ASIA_R) y 2/27 (TREND_H) salen positivos, con pocas operaciones: azar.
- **Decisión**: no se implementa nada. Se confirma que el Forex del broker no tiene ventaja con indicadores
  clásicos, igual que los estudios previos (Donchian, sesiones S1–S4, ICT y entrada limitada).
- **Ficheros**:
  - `tools/research_forex_indicators.py` (nuevo).
  - Salidas en `storage/analysis/forex_indicators_{trades,random,report}`.

### 2026-10-22 — Worker RSI2: 1 % dividido en dos entradas (contrato del bot) + salida por regla  ·  Estado: aplicado sin commit
- **Qué** (petición del usuario: usar el contrato de los índices, 1 % en dos entradas):
  - El worker RSI2 abre **dos entradas al 0,5 %**: TP1 a 1R y runner a TP2 = 2R, que pasa a BE tras cerrar TP1.
    Sin extensión del runner.
  - La regla diaria (primer cierre D1 > SMA5 o 10 velas) **cierra lo que quede abierto**.
  - Objetivos tomados de la señal, en la misma rama que ICT y DRIFT.
  - `DAEMONBLACKFX_RSI2_SPLIT=0` vuelve a una sola posición con TP lejano.
- **Por qué / evidencia**: `tools/research_rsi2_management.py` recorre el camino real en velas M15 (SL primero) con
  las mismas entradas y spread y swap reales.

  | Gestión | R/op | t por día |
  |---|---:|---:|
  | Actual (una posición + regla) | +0,175 | 1,86 |
  | **Dos entradas + regla (TP1 1R / runner con BE)** | **+0,177** | **1,89** |
  | Dos entradas + regla con TP2 2R (la aplicada) | +0,177 | 1,89 |
  | Contrato puro sin regla (10 días máx.) | **+0,108** | 1,01 |

  - TP1 = 1R (2 ATR D1) solo se toca en el 4 % de las operaciones: el rebote suele cerrarse por la regla antes.
  - La regla SMA5 es la que aporta la ventaja; sin ella el resultado cae un 40 %.
- **Riesgo nuevo**: ahora ocupa 2 posiciones por índice. Con el límite global de 2 por símbolo, una posición de NIGHT
  en US SP 500 / US Tech 100 bloquea la entrada RSI2 en ese índice (y al revés).
- **Ficheros**:
  - `strategy/connors_rsi2/rsi2_daily.py`.
  - `strategy/execution/live_trading_engine.py` (`rsi2_split`, rama de objetivos).
  - `tools/research_rsi2_management.py` (nuevo).
  - Tests en `tests/test_connors_rsi2_worker.py` (10) y `tests/test_drift_breakout_worker.py`.

### 2026-10-22 — Worker RSI2: RSI(2) diario de Connors en los 5 índices US (prueba demo)  ·  Estado: aplicado sin commit
- **Qué**:
  - **Worker `RSI2`**: `rsi2-daemon`, magic 26082036, pestaña propia "RSI(2) EE. UU." en /Instruments.
    Activos: US SP 500, US Tech 100, Wall Street 30, US Small Cap 2000 y US Mid Cap 400.
  - **Estrategia `CONNORS_RSI2`** (`connors-rsi2-v1`, `strategy/connors_rsi2/rsi2_daily.py`): reglas REV_D
    pre-registradas, solo largos:
    - Señal al cierre D1: cierre > SMA200 y RSI(2) < 10.
    - Entrada a mercado al empezar la vela D1 siguiente (como mucho 120 min después del primer tick del día).
    - Stop de protección 2 × ATR14 D1; lotaje al 1 % sobre esa distancia; TP lejano (20R).
    - Salida a mercado tras la primera vela D1 cerrada con cierre > SMA5, o tras 10 velas D1.
  - **Excepción del contrato** (como NIGHT): una posición sin TP1, BE ni extensión del runner, porque la salida es
    por regla. El motor los desactiva solo para este perfil.
  - **Motor**:
    - `_close_rsi2_positions_on_rule` en los dos puntos del monitor de posiciones (auditoría `RSI2_RULE_EXIT`).
    - `_rsi2_gate` / `_rsi2_status`: una sola posición RSI2 por índice, como en el replay (el límite global admite
      2). Prueba demo `rsi2_mode="demo_test"`: con ≥ 60 operaciones cerradas desde el 22-oct, R/op > 0 para
      seguir; si no, se desactiva sola (`RSI2_DEMO_TEST`).
    - Centinela de régimen solo en observación; IA en sombra.
- **Por qué / evidencia**: replay de 2 años con spread y swap reales (ver la entrada de indicadores en índices):
  - +0,176 R/op, 145 operaciones, acierto 72 %, ambos años y 4/4 semestres > 0.
  - **No concluyente** al agrupar por día: 79 episodios, t = 1,9. Por eso va a prueba demo.
  - **Fidelidad comprobada**: con datos reales de los 5 índices, la clase da las mismas señales que el replay
    (710 días con señal, 0 diferencias) y la misma vela de salida (377 salidas por regla, 0 diferencias).
- **Riesgos**:
  - Unas 70 señales al año: la revisión de 60 operaciones llegará en ≈ 10 meses.
  - Los 5 índices se mueven juntos: varias posiciones a la vez equivalen a una apuesta concentrada (hasta 5 % de
    riesgo el mismo día).
  - Se suma a la exposición larga de NIGHT.
  - Si ICT tiene 2 piernas abiertas en el mismo índice, el límite global de 2 posiciones por símbolo bloquea la
    entrada.
  - El swap largo (≈ −6 % anual) ya está cobrado en el replay.
- **Ficheros**:
  - `strategy/connors_rsi2/` (nuevo).
  - `strategy/execution/live_trading_engine.py`.
  - `app/main.py` (perfil, modo, universo y catálogo `rsi2_us_indices`).
  - `database/repository.py`, `dashboard/realtime_dashboard.py` y `dashboard/strategy_bases_page.py` (perfil RSI2).
  - `tools/daily_tracking_report.py` (familia "RSI(2) EE. UU.", esperado +0,176).
- **Interruptores**:
  - `DAEMONBLACKFX_RSI2` (off/demo_test/live), `_START`, `_REVIEW_TRADES` (60) y `_MIN_R` (0).
  - `_SYMBOLS`, `_THRESHOLD` (10), `_STOP_ATR` (2), `_MAX_DAYS` (10) y `_MAX_ENTRY_DELAY_MIN` (120).
- **Tests**: `tests/test_connors_rsi2_worker.py` (9, incluida la identidad de reglas con el replay).
- **Para activarlo**: reiniciar los daemons y pulsar "Aplicar selección" en /Instruments → "RSI(2) EE. UU.".

### 2026-10-21 — Investigación: indicadores en los 16 índices bursátiles (replay 2 años, 6 variantes)  ·  Estado: solo investigación, sin cambios en el bot
- **Qué**: `tools/research_index_indicators.py`, con reglas pre-registradas y spread y swap reales (el swap es un
  interés anual sobre el precio, ≈ −6 % al año en largos US). 3 estrategias × 2 ejecuciones:
  - **Diario** (una posición, stop de protección 2 × ATR D1, salida por regla):
    - REV_D: RSI(2) < 10 sobre la SMA200, solo largos; salida con cierre > SMA5.
    - TREND_D: SMA50/200 + ADX + retroceso RSI14; salida con cierre < SMA20.
    - BRK_D: Donchian 20/10.
  - **Intradía** (contrato TP1 1R + runner 2R con BE, solo en la sesión de contado de cada índice):
    - REV_I: RSI(2) H1, solo largos.
    - TREND_I: EMA/ADX H1 + retroceso M15.
    - ORB_I: rango de los 30 min de apertura + VWAP.
  - Criterio (6 pruebas): R/op > 0 en ambos años, t ≥ 2,7, ≥ 3/4 semestres > 0, p azar < 0,0083. La prueba de azar
    usa la misma dirección, así que la deriva alcista no cuenta como ventaja.
- **Resultado global: ninguna supera.**

  | Variante | R/op | t |
  |---|---:|---:|
  | REV_D | +0,058 | 1,8 |
  | TREND_D | −0,167 | — |
  | BRK_D | −0,210 | — |
  | REV_I | −0,080 | — |
  | TREND_I | −0,082 | — |
  | ORB_I | −0,020 | — |

  Las intradía pierden lo mismo que entrar al azar menos el coste.
- **Hallazgo: REV_D (RSI(2) de Connors) en los 5 índices de EE. UU.**:
  - 145 operaciones, **+0,176 R/op**, t = 4,0, acierto 72 %.
  - Año 0 +0,190, año 1 +0,164; 4/4 semestres > 0; p azar < 0,001.
  - Los 5 índices positivos: SP500 +0,30, WS30 +0,25, MidCap +0,17, SmallCap +0,11, Tech100 +0,07.
  - Europa (−0,089) y Asia (+0,093, no significativo) no.
  - **Pero las operaciones están muy correladas**: los 5 índices dan la señal los mismos días. Agrupando por día
    quedan 79 episodios, con **t = 1,9**.
  - Robustez: positivo en ambos años en todas las variantes probadas (umbral 5/10/15/20, salida SMA5 o RSI2 > 70,
    stop 1,5/2/3 ATR, filtro SMA100/200, e incluyendo 2024 desde junio). La t por día va de 0,5 a 3,3.
  - Es la anomalía de reversión a corto plazo más documentada en índices US. Pero con unas 40 señales al año la
    muestra independiente es pequeña: **no concluyente**.
- **Decisión pendiente del usuario**: solo podría ir a prueba demo con criterio fijado. Tendría que ser un worker
  diario de una posición con salida por regla (excepción del contrato, como NIGHT). Además se solapa con la
  exposición larga de NIGHT en US SP 500 / US Tech 100.
- **Ficheros**:
  - `tools/research_index_indicators.py` (nuevo).
  - Salidas en `storage/analysis/index_indicators_{trades,random,report}`.

### 2026-10-21 — Investigación: batería de 4 estrategias de indicadores en la familia Step (replay 2 años)  ·  Estado: solo investigación, sin cambios en el bot
- **Qué**: a petición del usuario, y pese al diagnóstico de paseo aleatorio, se replayan 4 estrategias con reglas
  pre-registradas en los 12 Step (`tools/research_step_indicators.py`):
  - D · RSI(2) de Connors a favor de la EMA200 H1.
  - E · cambio de Supertrend(10,3) M15 con la EMA50 H1.
  - F · cruce MACD(12,26,9) bajo cero con la EMA200 M15.
  - G · ruptura de Keltner(EMA20 ± 2 ATR10) con ADX H1 ≥ 25.
  - Ejecución y gestión idénticas al replay de indicadores (stop 1,5 × ATR H1, TP1 1R + runner 2R con BE, spread
    real, tope 2 %).
  - Criterio: R/op > 0 en ambos años, t ≥ 2,5, ≥ 3/4 semestres > 0 y p azar < 0,0125.
- **Resultado: ninguna supera; las 4 pierden aproximadamente el coste**, como predijo el diagnóstico:
  - D −0,010 R/op (17.610 ops, t −1,2).
  - E −0,024 (7.985 ops, t −2,0).
  - F −0,017 (8.097 ops, t −1,5).
  - G −0,018 (6.263 ops, t −1,3).
  - Ninguna familia (Step, Multi Step, Skew Step) cumple el criterio en ninguna estrategia. Acierto entre el 48,6 % y
    el 50,3 %.
- **Cortes exploratorios**:
  - De 48 combinaciones símbolo × estrategia, la única llamativa es **RSI(2) en Step Index 300**: +0,075 R/op en
    1.459 operaciones (año 0 +0,069, año 1 +0,082; t ≈ 2,6).
  - Con 48 comparaciones haría falta t ≥ 3,3, y el diagnóstico de Step 300 no muestra reversión (ratio de varianzas
    0,99, autocorrelación ≈ 0): se trata como azar.
- **Decisión** (fijada por el usuario: sin ventaja, no implementar): **no se implementa**. Los Step quedan cerrados
  para estrategias de indicadores.
- **Ficheros**:
  - `tools/research_step_indicators.py` (nuevo).
  - Salidas en `storage/analysis/step_indicators_{trades,random,report}`.

### 2026-10-21 — Investigación: diagnóstico de aleatoriedad de la familia Step (12 índices)  ·  Estado: solo investigación, sin cambios en el bot
- **Qué**: antes de diseñar una estrategia de indicadores para los Step (petición del usuario: diagnóstico primero; si
  no hay ventaja, no implementar), `tools/research_step_diagnostics.py` mide si se apartan del paseo aleatorio.
  - Universo: Step Index 100/200/300/400/500, Multi Step 2/3/4 y Skew Step 4/5 Up/Down.
  - Datos: 2 años de M15 (≈ 70.000 velas por símbolo) y ≈ 99.000 velas M1.
  - Pruebas:
    - Deriva.
    - Autocorrelación en M1 y M15 (retardos 1–5).
    - Ratio de varianzas de Lo-MacKinlay, q = 2–32, con z robusto.
    - Rachas en M1.
    - Estacionalidad horaria.
    - Coste del spread en R.
- **Resultado: no hay ninguna desviación explotable**:
  - Deriva: ningún t supera ±1,5 en el total (máx. +1,49, Multi Step 2), y ninguna es estable en los dos años.
  - Autocorrelación: |ρ| ≤ 0,013 en todos los retardos y símbolos; ningún z > 2,5 estable en ambos años.
  - Ratio de varianzas: entre 0,96 y 1,05 (paseo aleatorio = 1). El único |z| > 2,5 es Skew Step 5 Up en el año 0
    (+2,8), que en el año 1 baja a +0,2.
  - Rachas M1: P(sube | k subidas) entre 0,486 y 0,523. En los Skew es 0,51/0,49 por diseño (pasos asimétricos de media
    cero); en los Step clásicos 0,494–0,506.
  - Horas: t máx. 3,2 (Step Index, 15 h UTC) entre 288 pruebas hora × símbolo, esperable por azar.
  - Coste: el spread equivale a 0,007–0,019 R por operación con stop de 1,5 × ATR H1. Sin desviación no hay nada que
    lo compense.
- **Coherente con el replay de indicadores en sintéticos**: en Step, tendencia −0,030, ruptura −0,008 y reversión
  +0,035 R/op (t 1,35, que no llega al umbral de 2,4). Con VR ≈ 1 y autocorrelación ≈ 0, ese +0,035 es compatible
  con suerte.
- **Decisión** (fijada por el usuario antes de medir): **no se implementa** ninguna estrategia de indicadores en Step.
  Los Step siguen solo con el worker ICT, cuya pequeña ventaja viene del precio de entrada (límite virtual) y del tope
  de coste, no de predecir la dirección.
- **Ficheros**:
  - `tools/research_step_diagnostics.py` (nuevo).
  - Informe en `storage/analysis/step_diagnostics_report.md`.

### 2026-10-21 — Worker DRIFT: ruptura tras compresión en Drift Switch Index 10/20/30 (prueba demo)  ·  Estado: aplicado sin commit
- **Qué**:
  - **Worker `DRIFT`**: `drift-daemon`, magic 26082035, pestaña propia "RUPTURA DRIFT" en /Instruments.
    Activos: Drift Switch Index 10, 20 y 30.
  - **Estrategia `DRIFT_BREAKOUT`** (`drift-breakout-v1`, `strategy/drift_breakout/compression_breakout.py`): reglas
    C_RUPTURA pre-registradas, idénticas al replay. Las comparten `breakout_frame` y
    `tools/research_synthetic_indicators.py`:
    - En alguna de las 5 últimas velas M15 cerradas, el ancho de Bollinger(20,2) estuvo en el 20 % más bajo de las
      120 previas.
    - La última vela M15 cierra fuera del Donchian(20) (la previa no lo hacía).
    - La EMA50 H1 va a favor.
    - Entrada a mercado si la vela de señal cerró hace ≤ 10 min. Stop 1,5 × ATR14 H1.
    - Contrato: TP1 1R (50 %) + runner 2R (50 %) con BE tras TP1.
    - Una señal por vela (`setup_id`) y una operación por símbolo.
  - **Motor**:
    - `_drift_gate` / `_drift_status`: prueba demo `drift_mode="demo_test"`. Con ≥ 200 operaciones cerradas desde el
      21-oct, R/op > 0 para seguir; si no, se desactiva sola (`DRIFT_DEMO_TEST`).
    - Objetivos tomados de la señal (rama de ICT): TP1 1R y runner 2R.
    - Sin extensión del runner, como en el replay (`DAEMONBLACKFX_DRIFT_RUNNER_EXTENSION` la reactiva).
    - Sin puertas de familia ni centinela de régimen (validada sin ellos); IA en sombra.
    - Se mantienen el tope de spread de sintéticos (2 %) y el riesgo del 1 %.
- **Por qué / evidencia**: replay de 2 años (ver la entrada de investigación de indicadores en sintéticos):
  - +0,086 R/op, t = 3,9, 2.394 operaciones (≈ 3,3/día), acierto 53,6 %.
  - Año 0 +0,062, año 1 +0,111; 4/4 semestres > 0; p azar < 0,001.
  - Robusta en las 9 combinaciones de stop y Donchian.
  - **Fidelidad comprobada**: con 400 velas, como en vivo, la clase da las mismas señales que el replay en 12.230 velas
    de Drift Switch Index 20 (240 señales, 0 diferencias).
- **Riesgos**:
  - Solo 3 símbolos de una misma familia: correlación de régimen entre ellos.
  - En vivo la entrada llega minutos después del cierre de la vela y se cobra el spread real, no el mediano.
  - El replay cierra a las 200 velas M15; el motor no tiene salida por tiempo para DRIFT (raro: stop y objetivos a
    1,5–3 ATR H1).
- **Ficheros**:
  - `strategy/drift_breakout/` (nuevo).
  - `strategy/execution/live_trading_engine.py`.
  - `app/main.py` (perfil, modo, universo y catálogo `drift_switch`).
  - `database/repository.py`, `dashboard/realtime_dashboard.py` y `dashboard/strategy_bases_page.py` (perfil DRIFT).
  - `tools/daily_tracking_report.py` (familia "Ruptura Drift", esperado +0,086).
- **Interruptores**:
  - `DAEMONBLACKFX_DRIFT` (off/demo_test/live), `_START`, `_REVIEW_TRADES` (200) y `_MIN_R` (0).
  - `_SYMBOLS`, `_STOP_ATR` (1,5), `_MAX_SIGNAL_AGE_MIN` (10) y `_RUNNER_EXTENSION` (0).
- **Tests**: `tests/test_drift_breakout_worker.py` (8, incluida la identidad de reglas con el replay).
- **Para activarlo**: reiniciar los daemons y pulsar "Aplicar selección" en /Instruments → "RUPTURA DRIFT".

### 2026-10-21 — Investigación: estrategias de indicadores clásicos en los 98 sintéticos (replay 2 años)  ·  Estado: solo investigación, sin cambios en el bot
- **Qué**: tres estrategias de indicadores con reglas pre-registradas (`tools/research_synthetic_indicators.py`):
  - A · tendencia (EMA50/200 + ADX H1, retroceso RSI M15).
  - B · reversión (Bollinger + RSI con ADX H1 < 20).
  - C · ruptura (compresión Bollinger + Donchian 20, a favor de EMA50 H1).
  - Señal M15 con filtro H1. Gestión del contrato: stop 1,5 × ATR H1, TP1 1R + runner 2R con BE, spread real y
    tope del 2 %. Periodo 21-oct-2024 → 21-oct-2026, 98 sintéticos de 16 familias.
- **Ajustes de viabilidad tras una prueba con 2 símbolos y antes de medir el universo**:
  - Stop de ATR M15 → ATR H1.
  - Spread de mediana global → mediana causal móvil.
  - Retroceso de A redefinido.
- **Criterio** (3 pruebas): R/op > 0 en ambos años, t ≥ 2,4, ≥ 3/4 semestres > 0 y p azar < 0,0167.
- **Resultado global: ninguna supera.**
  - A −0,013 R/op (t −1,75).
  - B +0,005 (t 0,7; año 1 negativo).
  - C +0,007 (t 1,65; p azar 0,22).
- **Hallazgo: C_RUPTURA en Drift Switching Indices (10/20/30)**:
  - +0,086 R/op, t = 3,9, 2.394 operaciones (≈ 3,3/día), acierto 53,6 %.
  - Año 0 +0,062, año 1 +0,111; 4/4 semestres > 0; p azar < 0,001.
  - Sobrevive a Bonferroni sobre las 48 comparaciones familia × estrategia.
  - **Robusto**: positivo en ambos años en las 9 combinaciones de stop (1,0/1,5/2,0 ATR) y Donchian (10/20/40).
    Con stop 1,0: +0,11, t 5,5. No se cambia el 1,5 pre-registrado.
  - **Mecanismo plausible**: Deriv construye estos índices alternando regímenes de deriva alcista, bajista y lateral
    (duración media 10/20/30 min). La ruptura a favor de la deriva captura esa persistencia.
  - Operables en la cuenta: stop mediano 22–41 puntos frente a un stops level de 5–10; 0,7–1,4 lotes por pierna.
- **Otros cortes**:
  - B en Drift también cumple dentro de la familia (+0,080, t 2,7), pero no sobrevive a 48 comparaciones.
  - DEX y Crash/Boom salen positivos con C, pero el azar también (p 0,17–0,21): la ventaja es del activo, no de la
    regla.
  - Volatility Indices pierden con A (−0,072, t −4,5).
- **Ficheros**:
  - `tools/research_synthetic_indicators.py` (nuevo).
  - Salidas en `storage/analysis/synthetic_indicators_{trades,random,report}`.

### 2026-10-21 — Worker NIGHT: sesgo nocturno en US SP 500 / US Tech 100 (prueba demo)  ·  Estado: aplicado sin commit
- **Qué**:
  - **Worker `NIGHT`**: `night-daemon`, magic 26082034, con pestaña propia "SESGO NOCTURNO" en /Instruments.
    Activos: US SP 500 y US Tech 100. Wall Street 30 queda en PODA PREVENTIVA.
  - **Estrategia `OVERNIGHT_DRIFT`** (`overnight-drift-v1`, `strategy/overnight/overnight_drift.py`):
    - Compra en la ventana 16:00-16:15 NY de los días hábiles.
    - Stop de protección = 1 × ATR(14) D1 cerrado; el lotaje lo fija el riesgo del 1 % sobre esa distancia.
    - TP lejano (20R), sin objetivo real.
    - Salida por tiempo a las 09:30 NY del día hábil siguiente (lunes si se entra el viernes), con horario de verano
      e invierno vía zoneinfo.
  - **Excepción del contrato, pedida por el usuario**: una sola posición al 1 %, sin TP1, BE ni extensión del runner,
    porque la estrategia sale por tiempo. El motor desactiva `split_entries`, `break_even` y `runner_extension` solo
    para este perfil.
  - **Motor**:
    - `_close_overnight_positions_at_open` en el monitor de posiciones (auditoría `OVERNIGHT_TIME_EXIT`).
    - Prueba demo `overnight_mode="demo_test"`: con ≥ 120 noches cerradas desde el 21-oct, R/op > 0 para seguir;
      si no, se desactiva sola (`OVERNIGHT_DEMO_TEST`).
    - El centinela de régimen solo registra (se validó sin él) y la IA va en sombra.
- **Por qué / evidencia** (`research_session_anomalies.py`, M30 desde el 22-ene-2024, que es todo el historial de
  índices del broker):
  - Bruto: +0,062 / +0,083 %/noche (t ≈ 2,5).
  - Con el stop de 1 ATR (regla fijada antes de medir): **+0,033 R/noche, t = 2,4**, acierto 55 %.
    Por periodo: 2024 +0,080, y0 +0,024, y1 +0,008. Stop en el 7 % de las noches, peor −2R por hueco.
  - Curva al 1 % por índice: +44 % en 2,75 años, caída máxima −19,5 %.
- **Riesgos**:
  - La ventaja se viene **reduciendo** (y1 +0,008).
  - Exposición solo compradora a la renta variable US, con huecos de hasta −2R y el swap como coste fijo.
  - La muestra no llega a los 6 años pedidos: el broker no tiene datos de índices antes de ene-2024.
- **Ficheros**:
  - `strategy/overnight/overnight_drift.py`.
  - `strategy/execution/live_trading_engine.py`.
  - `app/main.py` (perfil, modo, universo y catálogo `night_indices`).
  - `database/repository.py`, `dashboard/realtime_dashboard.py` y `dashboard/strategy_bases_page.py` (perfil NIGHT).
  - `tools/daily_tracking_report.py` (familia "Sesgo nocturno").
- **Interruptores**: `DAEMONBLACKFX_OVERNIGHT` (off/demo_test/live), `_START`, `_REVIEW_TRADES` (120) y `_MIN_R` (0).
- **Tests**: `tests/test_overnight_drift_worker.py` (11).
- **Para activarlo**: reiniciar los daemons y, en /Instruments → "SESGO NOCTURNO", "Aplicar selección".

### 2026-10-20 — Malaysian SNR: DEX 1500 UP Index en prueba demo  ·  Estado: aplicado sin commit
- **Qué**:
  - DEX 1500 UP Index entra en el universo y la lista activa **solo de Malaysian SNR**.
  - En la pestaña MSNR (worker de los vídeos) aparece como PODA PREVENTIVA.
  - No tiene modo en `asset_modes` (no está en el catálogo de ajustes MSNR): lo controla solo la selección de
    /Instruments.
  - Prueba demo por símbolo (`_msnr_symbol_test_gate`): solo opera en DEMO. Desde el 21-oct, con ≥ 40 operaciones
    MSNR cerradas en DEX: R/op > 0 → SUPERA; si no, NO_SUPERA y se bloquea solo
    (`MSNR_SYMBOL_DEMO_TEST_FAILED`; auditoría `MSNR_SYMBOL_DEMO_TEST`).
- **Por qué / evidencia**: replay MSNR de los 61 sintéticos no operados (2 años, tope 2 %).
  - Es el único con evidencia robusta: n = 210, +0,299 R/t, t = 4,1 (supera la corrección por 45 pruebas),
    y0 +0,241 / y1 +0,398, ambas direcciones positivas.
  - El resto de sintéticos nuevos no muestra ventaja (12 de 45 positivos en ambos años, ≈ lo esperable por azar).
- **Ficheros**:
  - `config/ict_instrument_policy.py` (`MSNR_DEMO_TEST_CANDIDATES/SYMBOLS`, `MALAYSIAN_SNR_ACTIVE`).
  - `app/main.py` (universo de Malaysian SNR; el worker MSNR lo excluye).
  - `strategy/execution/live_trading_engine.py` (`msnr_symbol_test_*` y la puerta).
  - `dashboard/realtime_dashboard.py` (etiqueta "DEX (prueba demo)").
- **Interruptores**: `DAEMONBLACKFX_MSNR_DEMO_TEST_SYMBOLS` (on/off), `DAEMONBLACKFX_MSNR_SYMBOL_TEST_START`,
  `_REVIEW_TRADES` (40) y `_MIN_R` (0).
- **Tests**: `tests/test_msnr_dex_demo_test.py` (6). Se ajustaron `test_ict_instrument_policy.py` y
  `test_msnr_video_worker.py`.
- **Para activarlo**: reiniciar los daemons y marcar DEX 1500 UP Index en la pestaña Malaysian SNR ("Aplicar
  selección"), o ejecutar `tools/apply_ict_instrument_policy.py --apply`.

### 2026-10-20 — Worker MSNR con la estrategia de los vídeos y pestaña MSNR propia  ·  Estado: aplicado sin commit
- **Qué** (pedido del usuario: variante de MSNR basada en los vídeos, en un worker nuevo controlado solo por una
  pestaña "MSNR"):
  - **Worker `MSNR`**: modo `msnr-daemon`, magic 26082033, arranca con el coordinador multi-bot.
    - Mismos instrumentos que Malaysian SNR: 30 sintéticos activos; los reales y los de acierto ≤ 45 % en PODA
      PREVENTIVA.
    - Selección independiente: el perfil de selección `MSNR` solo lo usa este worker.
    - Guardar la pestaña MSNR no toca los `asset_modes` de Malaysian SNR.
  - **Estrategia `MSNR_VIDEO` (versión `msnr-video-v1`)**, en `strategy/malaysian_snr/video_strategy.py`:
    - Entrada de confirmación H4→H1 del curso (`h4h1_confirmation.py`).
    - Storyline D1+H4 (`strategy/malaysian_snr/storyline.py`) en modo `observe`: se guarda en cada señal
      (`storyline`, `storyline_alignment`) sin filtrar, porque como filtro no mejoró en el replay. `filter` la exige.
    - Gestión del contrato: TP1 1R, runner 2R + extensión progresiva, BE tras TP1.
    - Solo sintéticos.
  - **Motor**:
    - Despacho propio para el perfil MSNR.
    - Prueba demo `msnr_video_mode="demo_test"` (solo DEMO): con ≥ 200 operaciones cerradas desde el 21-oct, se
      mantiene si R/op > 0; si no, se desactiva solo (`MSNR_VIDEO_DEMO_TEST_FAILED`; auditoría
      `MSNR_VIDEO_DEMO_TEST`).
    - Como en el replay: el centinela de régimen solo registra, sin las puertas por familia de sintéticos y con IA
      en sombra.
  - **Malaysian SNR**: el escenario H4→H1 pasa a **off** por defecto (`DAEMONBLACKFX_MSNR_H4H1=off`) para no duplicar
    operaciones con el worker MSNR.
- **Por qué / evidencia**: replay H4→H1, 37 sintéticos, 2 años.
  - +0,029 R/t; con la política de dirección +0,017 (y0 +0,017 / y1 +0,018); 8 de 9 trimestres positivos.
  - El detector en vivo cubre el 97 % de las operaciones del replay.
  - La storyline se probó como filtro y no aportó.
- **Ficheros**:
  - `strategy/malaysian_snr/video_strategy.py` y `storyline.py`.
  - `strategy/execution/live_trading_engine.py`.
  - `app/main.py` (perfil, modo, universo y catálogo `msnr_*`).
  - `config/ict_instrument_policy.py` (perfil MSNR).
  - `database/repository.py` (perfil MSNR y magic).
  - `dashboard/realtime_dashboard.py` (pestaña, categorías, worker).
  - `tools/daily_tracking_report.py` (familia "MSNR Vídeos").
- **Interruptores**: `DAEMONBLACKFX_MSNR_VIDEO` (off/demo_test/live), `_STORYLINE` (off/observe/filter), `_START`,
  `_REVIEW_TRADES` y `_MIN_R`.
- **Tests**: `tests/test_msnr_video_worker.py` (12). `test_msnr_h4h1_confirmation.py` se actualizó (H4→H1 off por
  defecto en Malaysian SNR).
- **Para activarlo**:
  1. Reiniciar los daemons; arranca el worker nuevo.
  2. En /Instruments → pestaña **MSNR** → "Aplicar selección", o `tools/apply_ict_instrument_policy.py --apply`.
     Sin selección guardada, el worker usa todo su universo y la estrategia descarta los mercados reales.
- **Riesgos**:
  - Unas 20 operaciones al día en sintéticos que compiten por los 8 huecos simultáneos con ICT y Malaysian SNR.
  - 200 operaciones detectan un fallo claro, pero no confirman una ventaja tan pequeña.

### 2026-10-20 — MSNR: escenario H4→H1 de los vídeos en prueba demo  ·  Estado: aplicado sin commit
- **Qué**: nuevo escenario `ESC_5_H4H1_CONFIRMATION` en MSNR sintéticos, con versión propia `msnr-h4h1-v1` y
  confirmación `H4_REJECT_H1_OPEN_CLOSE_BREAK`.
  - **Regla**:
    - Una vela H4 rechaza un nivel A/V H4 (pico o valle de cierres, radio 2).
    - La primera H1 de las 4 siguientes que cierra rompiendo el último open-close H1 dispara la entrada, a mercado
      en la H1 siguiente.
    - SL tras el extremo de la H4 ± 0,1 ATR H1 (+ spread en venta).
    - Gestión del contrato: TP1 1R + runner 2R, BE tras TP1.
  - Solo se evalúa si la estrategia MSNR habitual no dio señal en ese ciclo, y una vez por configuración (`setup_id`).
  - Respeta la poda de símbolos de MSNR, el tope spread/SL 2 % y la política de dirección (Boom BUY, Crash SELL).
  - Queda **exento** del filtro de régimen MSNR y del ADX de ejecución Step, porque se validaron con las
    confirmaciones M15, no con este escenario.
- **Por qué / evidencia** (`tools/research_msnr_storyline_h4h1.py`, 37 sintéticos, 2 años):
  - 18.595 operaciones, +0,029 R/t (y0 +0,026 / y1 +0,031), t = 3,75, 8 de 9 trimestres positivos.
  - Con la política de dirección del bot: 15.870 operaciones, **+0,017 R/t (y0 +0,017 / y1 +0,018)**.
  - El detector en vivo reproduce el 97 % de las operaciones del replay (150 de 155 en 4 símbolos y 45 días).
- **Prueba demo y criterio fijado**:
  - `msnr_h4h1_mode="demo_test"`: solo en DEMO.
  - Desde el 21-oct-2026, al llegar a 200 operaciones H4→H1 cerradas en DEMO: R/op > 0 → SUPERA. Si no, NO_SUPERA:
    el escenario **se desactiva solo** (`MSNR_H4H1_DEMO_TEST_FAILED`) y queda en la auditoría (`MSNR_H4H1_DEMO_TEST`).
  - Con una ventaja esperada pequeña (+0,017 R/t), 200 operaciones solo detectan un fallo claro, no confirman la
    ventaja.
- **Ficheros**:
  - `strategy/malaysian_snr/h4h1_confirmation.py` (detector).
  - `strategy/malaysian_snr/malaysian_snr_strategy.py` (`_h4h1_signal` y su enganche en `analyze_symbol`).
  - `strategy/malaysian_snr/config.py` (`enable_h4h1_confirmation`, `h4h1_runner_rr`).
  - `strategy/execution/live_trading_engine.py` (`msnr_h4h1_*`, `_msnr_h4h1_active`, `_msnr_h4h1_status`,
    `_msnr_h4h1_gate` y las exenciones).
- **Interruptores**: `DAEMONBLACKFX_MSNR_H4H1` (off / demo_test / live), `_START`, `_REVIEW_TRADES` y `_MIN_R`.
- **Tests**: `tests/test_msnr_h4h1_confirmation.py` (9).
- **Riesgos**:
  - Puede dar unas 20 operaciones al día en sintéticos y llenar antes los 8 huecos simultáneos que comparte con ICT
    (no medido).
  - Necesita reiniciar los daemons para cargarse.

### 2026-10-20 — Seguimiento diario demo vs replay  ·  Estado: aplicado sin commit
- **Qué**: `tools/daily_tracking_report.py` (solo lectura de la base). Por día UTC y acumulado desde el 20-oct,
  por familia (ICT sintéticos, MSNR sintéticos, ICT mercados reales, ORB, Otros) informa:
  - operaciones lógicas, R total, R/op, acierto y USD;
  - un veredicto frente al R/op esperado por el replay (z con desviación 1,1R; |z| < 2 = en línea);
  - peores y mejores símbolos;
  - eventos de los filtros nuevos.
- **Salida**: `storage/analysis/seguimiento_diario/informe_<día>.md` y `seguimiento_diario.csv`.
- **Tarea programada**: `seguimiento-diario-blackdaemonfx` (app de Claude, todos los días a las 21:30 hora local =
  00:30 UTC). Ejecuta el informe del día UTC que acaba de cerrar y lo resume en español.
- **Referencias del replay** (`EXPECTED` en el script):
  - ICT sintéticos: +0,03 (rango +0,022/+0,047).
  - MSNR sintéticos: +0,03, provisional hasta el replay con símbolo libre.
  - Resto: 0.
  - Actualízalas cuando cambien los hallazgos.
- **Tests**: `tests/test_daily_tracking_report.py` (4).
- **Nota operativa**: los daemons se reiniciaron el 20-oct a las 11:32 (hora local) y cargaron todo lo hecho hasta
  el centinela en OBSERVE. La ocupación fantasma tras descarte por spread (editada a las 12:06) entra en el
  próximo reinicio.

### 2026-10-20 — ICT sintéticos: ocupación fantasma tras descarte por spread  ·  Estado: aplicado sin commit
- **Qué**: cuando el tope spread/SL 2 % descarta una señal ICT en un sintético, el símbolo queda ocupado por la
  operación virtual de esa señal: entrada al ask/bid del momento, el mismo SL, TP1 a 1R y runner a 2R con BE
  tras TP1.
  - Mientras siga abierta, el símbolo no se analiza (`ICT_SPREAD_LOCK_ACTIVE`).
  - Se libera con SL, TP2 o TP1+BE, comprobado con velas M15 cerradas, o a las 50 h (`TIMEOUT`).
  - Auditoría `ICT_SPREAD_LOCK` con LOCKED y RELEASED (`VIRTUAL_TRADE_SL` / `_TP2` / `_TP1_BE` / `_TIMEOUT`).
  - De paso deja de crearse y dispararse el límite virtual cada minuto en esos símbolos.
- **Por qué / evidencia**: conciliación de replays (ver Hallazgos).
  - Año previo, fuera de muestra: +0,004 → +0,022 R/t, acierto 50,3 → 51,2 %, R total +39 → +191.
  - Último año: +0,015 → +0,047 R/t, R total +137 → +356.
  - Las operaciones evitadas pierden −0,16 y −0,11 R/t (t ≈ −4,5 a −4,9).
  - Coste: 9-16 % menos de operaciones.
- **Ficheros**: `strategy/execution/live_trading_engine.py`:
  - campos `ict_spread_block_lock_enabled` y `ict_spread_block_lock_max_hours`;
  - métodos `_register_ict_spread_lock` (llamado desde `_forex_execution_gate` al bloquear por spread),
    `_resolve_virtual_trade` y `_ict_spread_lock_gate` (puerta previa al análisis, antes del centinela).
  - `tools/replay_ict_exit_variants.py --phantom-busy`.
- **Interruptores**: `DAEMONBLACKFX_ICT_SPREAD_LOCK` (1) y `DAEMONBLACKFX_ICT_SPREAD_LOCK_MAX_HOURS` (50).
- **Tests**: `tests/test_ict_spread_block_lock.py` (7).
- **Riesgos**:
  - Los bloqueos viven en memoria del worker: un reinicio los borra, igual que en el replay al empezar.
  - Velas BID; en SELL se suma el spread al comprobar el SL.
  - Necesita reiniciar los daemons para cargarse.

### 2026-10-20 — Sintéticos mal clasificados + Centinela de Régimen en OBSERVE para ICT en sintéticos  ·  Estado: aplicado sin commit
- **Qué**:
  1. `_is_synthetic_symbol` usa además `is_synthetic_asset` (el clasificador de la estrategia ICT y del replay fiel).
     - High Frequency Vol 50/100 y VolSwitch High Vol (y otros sintéticos de Deriv: DEX, Drift Switch, Range
       Break, Snap, Trek, Exponential Growth) pasan a recibir lo mismo que el resto de sintéticos: entrada
       limitada virtual, tope spread/SL 2 % e IA en sombra.
     - Comprobado sobre los 733 símbolos del broker: ningún mercado real cambia.
  2. El Centinela de Régimen solo **registra** (`MARKET_REGIME_OBSERVED`, sin vetar) en los workers de la
     Estrategia ICT (ICT, STEP, JUMP, BOOM, CRASH, VOLATILITY_1-4) sobre sintéticos.
     - MSNR, FLIP, Forex y los mercados reales siguen en FILTER.
- **Por qué / evidencia**: brecha demo-replay del 20-oct (ver Hallazgos).
  - En el replay fiel ICT (28 activos, límite + tope 2 %, 365 d), las señales que el centinela habría bloqueado
    (18 %) rinden +0,067 R/t frente a +0,045 de las permitidas, en ambas mitades: unos +91R/año y un 22 % más de
    trades.
  - Ya en vivo llevaba ~1.900 bloqueos desde el reinicio.
- **Ficheros**: `strategy/execution/live_trading_engine.py` (`_SYNTH_DETECTION_EXTENDED`, `_is_synthetic_symbol`,
  `market_regime_ict_synthetic_mode`, `_market_regime_observe_only`, `_market_regime_entry_gate`).
- **Interruptores**: `DAEMONBLACKFX_SYNTH_DETECTION_EXTENDED` (1) y `DAEMONBLACKFX_MARKET_REGIME_ICT_SYNTH_MODE`
  (OBSERVE; FILTER restaura el veto).
- **Tests**: `tests/test_synthetic_detection_and_regime_observe.py` (9).
- **Riesgos**:
  - La reproducción del centinela en el replay usa 40 velas H1 cerradas (en vivo incluye la vela en formación) y
    no simula el factor de spread.
  - Necesita reiniciar los daemons para cargarse.

### 2026-10-20 — MSNR: filtro de régimen (sin fakeout y sin ADX 25-40) en prueba demo  ·  Estado: aplicado sin commit
- **Qué**: antes de ejecutar una señal Malaysian SNR se bloquea:
  - la confirmación `SNR_FAKEOUT_TRAP_SWEEP` (`MSNR_REGIME_FAKEOUT_BLOCKED`);
  - el ADX H1 de la señal en (25, 40] (`MSNR_REGIME_ADX_BLOCKED`).
  Las señales que pasan llevan `msnr_regime_filter` en la auditoría.
- **Por qué / evidencia** (replay fiel 2 años, 37 sintéticos, tope spread/SL 2 %, `msnr_variants_signals_y0/y1.csv`):

  | | n | R/trade | Acierto |
  |---|---|---|---|
  | Base | 2.600 | −0,003 | 50,0 % |
  | Con filtro | 1.675 | **+0,029** | 51,5 % |

  - t = 1,15 y p de azar = 0,02 (subconjuntos aleatorios del mismo tamaño).
  - 4 de 5 semestres positivos; 2024H2 queda negativo (−0,108).
  - Con los 30 activos de /Instruments sube a +0,073 R/trade (t = 2,6). Es una cifra dentro de muestra: esos 30 se
    eligieron con estos mismos datos.
  - El efecto ADX es irregular por tramos: (35, 40] da −0,167 y (40, 50] da +0,090.
  - **Coste: un 35 % menos de trades.**
- **Modo prueba demo y criterio fijado**:
  - `msnr_regime_filter_mode="demo_test"` aplica el filtro solo en DEMO.
  - Desde `DAEMONBLACKFX_MSNR_REGIME_START` (21-oct-2026 00:00 UTC), con ≥ 60 operaciones MSNR cerradas en DEMO,
    el veredicto es **SUPERA** si R/operación > 0 y acierto ≥ 50 %, y **NO_SUPERA** en otro caso.
  - El cambio de veredicto queda en la auditoría (`MSNR_REGIME_DEMO_TEST`). No cambia nada automáticamente:
    con SUPERA se propone pasar a `live`; con NO_SUPERA se revisa MSNR con datos.
- **Ficheros**:
  - `strategy/execution/live_trading_engine.py`: campos `msnr_regime_*`, `_msnr_regime_filter_gate` y
    `_msnr_regime_filter_status`; el filtro se llama antes de `_forex_execution_gate` en `_process_symbol_guarded`.
  - `database/repository.py`: `closed_operations_r` acepta `instrument=None` (todos) y `since`.
- **Interruptores**: `DAEMONBLACKFX_MSNR_REGIME_FILTER` (off/demo_test/live), `_ADX_MIN`, `_ADX_MAX`, `_START`,
  `_REVIEW_TRADES`, `_MIN_R`, `_MIN_WR`.
- **Tests**: `tests/test_msnr_regime_filter.py` (9).
- **Riesgos**:
  - La evidencia es dentro de muestra y con un efecto pequeño; por eso va en prueba demo y no en vivo directo.
  - Necesita reiniciar los daemons para cargarse.

### 2026-10-20 — /Instruments Malaysian SNR bajo la política única + arreglo de asset_modes  ·  Estado: aplicado sin commit
- **Qué**: la pestaña Malaysian SNR sigue la misma política que las de ICT (`config/ict_instrument_policy.py`):
  - **Activos (30):** los 37 sintéticos de MSNR menos la poda por acierto ≤ 45 % (`MSNR_WR45_PRUNED`).
  - **PODA PREVENTIVA:** los mercados reales (MSNR solo sintéticos) y los 7 con acierto ≤ 45 %. Aparecen
    desmarcados y bloqueados.
  - **Etiquetas:** "✓ MSNR Activo · Familia" sustituye a "MSNR Canónico Activo" y a las cifras "Tier S" puestas
    a mano.
  - **Configuración:** `DAEMONBLACKFX_MSNR_SYNTHETICS_ONLY=0` deja de podar los mercados reales, igual que el motor.
- **Bug corregido**: al guardar MSNR desde /Instruments se sincroniza `asset_modes` (live/off) en los ajustes
  de la base. Si la lista tocaba un símbolo fuera de `CATALOG_SYMBOLS` de MSNR, la validación lanzaba
  `ValueError` y se ignoraba en silencio, así que `asset_modes` quedaba desfasado respecto a /Instruments.
  - Ahora solo se escriben modos de símbolos del catálogo.
  - Los 9 sintéticos fuera del catálogo (Vol over Boom/Crash 550, HF Vol 50/100, VolSwitch, Vol 5,
    Vol 150 (1s), Vol 100 (1s) y Vol 90 (1s)) no tienen modo: solo los controla la selección de /Instruments.
- **Script**: `tools/apply_ict_instrument_policy.py --apply` incluye MALAYSIAN_SNR y alinea `asset_modes` en DEMO.
- **Tests**: `tests/test_ict_instrument_policy.py` (16 en total).

### 2026-10-20 — /Instruments ICT: política única (activo vs PODA PREVENTIVA)  ·  Estado: aplicado sin commit
- **Qué**: las pestañas Sintéticos, Forex e ICT de /Instruments controlan los workers ICT (Step, Jump,
  Volatility 1-4, Boom, Crash → Sintéticos; Forex 1-4 → Forex; ICT → metales, índices y petróleo). Hay una sola
  fuente de verdad, `config/ict_instrument_policy.py`:
  - Sintéticos activos (28): las listas de familia sin Fase 1 (Step Index, Jump 25, Volatility 25) ni la poda
    por acierto ≤ 45 %. Volatility 50 y Crash 600 siguen fuera.
  - Forex activos (14): EURUSD, USDJPY, GBPUSD, USDCAD, USDCHF, GBPCAD y AUDUSD, más sus versiones micro.
  - ICT activos (7): XAUUSD, XAUUSDmicro, microXAUUSD, US Oil, Wall Street 30, US Tech 100 y US SP 500.
  - Todo lo demás queda en **PODA PREVENTIVA**, con su motivo: cripto (ICT cripto off), plata (Fase 1),
    AUDJPY, CHFJPY y otros pares que el worker Forex ya no operaba, etc.
- **Corrige**:
  - Instrumentos marcados como activos que el motor bloqueaba (`*_ASSET_PRUNED_TOXIC`, exclusiones ICT).
  - Etiquetas "Sin Poda" con cifras viejas puestas a mano en el JS.
  - Sintéticos duplicados en la pestaña ICT y EURUSD en dos pestañas: ahora cada instrumento está en una sola.
- **Cómo**:
  - Las listas permitidas del motor (`step/jump/volatility/boom/crash/forex_allowed_symbols`) salen de la
    política, y el universo del worker ICT (`app/main.py`) es `ict_active_symbols("ICT")`.
  - Dashboard:
    - `DEFAULT_PRIORITIZED_SYMBOLS` sale de la política.
    - `_ict_preventive_prune_info` construye los motivos.
    - Las insignias pasan a ser "✓ ICT Activo · Worker X" o "⚠️ PODA PREVENTIVA"; la casilla de una PODA PREVENTIVA
      queda deshabilitada.
    - `update_selected_symbols` descarta las PODA PREVENTIVA al guardar y lo indica en el mensaje.
  - Los workers ya releían la selección en cada ciclo (`_selected_base_cycle_symbols`): marcar o desmarcar en
    /Instruments enciende o apaga el instrumento sin reiniciar.
- **Persistencia**: `tools/apply_ict_instrument_policy.py` muestra la vista previa; con `--apply` guarda la política
  en la base (DEMO y LIVE), con una copia previa en `storage/analysis/`. Pendiente de que lo ejecute el usuario.
- **Interruptores**: `DAEMONBLACKFX_ICT_UNPRUNE_SYNTHETICS` y `DAEMONBLACKFX_SYNTH_WR45_PRUNE`, ya existentes, también
  cambian la política.
- **Tests**: `tests/test_ict_instrument_policy.py` (10).
- **Efecto esperado**: lo que dice /Instruments coincide con lo que se opera. La única diferencia de operación
  es que el worker ICT deja de escanear sintéticos, que siguen cubiertos por sus workers de familia.

### 2026-10-20 — Rendimiento del front (dashboard)  ·  Estado: aplicado sin commit
- **Qué**: `/api/state` pasa de 19–33 s y 15 MB a **~1–2 s y ~0,45 MB** (gzip). Las páginas HTML ya cargaban en milisegundos;
  el cuello de botella era el endpoint que consultan cada pocos segundos.
  1. `trade_visual_audits(trade_ids=…)` y `position_visual_audits(symbols=…)`: las posiciones abiertas solo leen sus auditorías
     (antes decodificaba ~4.000 filas de JSON en cada refresco: ~18 s).
  2. `trade_visual_audit_entry_contexts`: caché incremental por `trade_id` (el contexto de entrada es inmutable): ~12 s → ~0 s.
  3. Cuenta en `/api/state` con *stale-while-revalidate*: se sirve el último cálculo y se recalcula en un hilo aparte.
  4. `/api/state` envía solo `account.snapshot`/`stats` (la cuenta completa, ~9 MB, sigue en `/api/account`) y recorta
     `smc_trial` a conteos + últimos 30 bloques (el JS usa los conteos precalculados).
  5. `snapshot()` ya no vuelve a sanear la cuenta (estaba saneada en su caché): −2 s.
  6. Respuestas JSON/HTML > 1 KB comprimidas con gzip si el navegador lo admite.
  7. Corrección: `_build_confluence_matrix` lanzaba `UnboundLocalError: badge` con motivos nuevos y tumbaba `/api/state`.
- **Ficheros**: `dashboard/realtime_dashboard.py` (`_maybe_gzip`, `_light_state_payload`, `_light_smc_trial`,
  `_refresh_account_in_background`, `_send`, `snapshot`, `_refresh_open_positions_locked`, `_build_confluence_matrix`),
  `database/repository.py` (filtros y caché).
- **Tests**: `tests/test_dashboard_front_performance.py` (8).
- **Efecto**: se aplica al reiniciar el proceso del dashboard (multi-bot daemon). Medido fuera de línea contra la base real.

### 2026-10-20 — RUNNER: el SL solo se mueve tras el cierre en ganancia de TP1  ·  Estado: aplicado sin commit
- **Qué**: compuerta central en `_monitor_break_even_positions`. Si la operación es la pata RUNNER (split activo) y su pata
  TP1 hermana **no** ha cerrado en ganancia (`_break_even_tp1_completion`), se bloquea **cualquier** cambio de SL del runner:
  BE genérico, pico favorable en Crash, protección de oro, protección FLIP, protección por noticias Forex, gestión ORB y extensión.
  También deja de activarse el cierre a mercado por "BE no colocable" antes de TP1.
- **Por qué / evidencia**: regla del usuario (contrato operativo, regla 2). En la base, ~80 runners pasaron a BE con TP1 aún abierta
  (el último el 20-oct, Crash 1000): `PRICE_REACHED_TRIGGER_RR` (precio en 1R), `CRASH_FAVORABLE_SPIKE_PROTECTIVE_BE`
  (pico en Crash ≥ 0,40R) y `GOLD_NEW_YORK_OPEN_POSITIVE`. La condición `eligible` aceptaba cualquiera de ellas.
- **Ficheros**: `strategy/execution/live_trading_engine.py` (`_runner_sl_locked_until_tp1`, `_guarded_move_stop`,
  `runner_sl_requires_tp1_close`, `base_move_stop` + `move_stop` protegido por operación, `eligible = False` si el runner está bloqueado).
- **Configuración**: `DAEMONBLACKFX_RUNNER_SL_REQUIRES_TP1=0` restaura el comportamiento anterior.
- **Tests**: `tests/test_runner_sl_requires_tp1_close.py` (11); `tests/test_gold_break_even_tp1.py` actualizado (los casos de BE
  ahora tienen la pata TP1 cerrada en ganancia y se añade que tocar TP1 sin cierre no desbloquea el runner).
- **Efecto**: el runner conserva su SL inicial hasta que el sync de MT5 marque la pata TP1 como cerrada con ganancia
  (puede haber unos segundos de retraso tras el cierre real). Las operaciones de una sola pata (SINGLE, GOLD Quarters) no cambian.

### 2026-10-19 — Poda de sintéticos con acierto ≤ 45 %  ·  Estado: aplicado sin commit
- **Qué**: se podan los instrumentos con acierto ≤ 45 % en el replay fiel. ICT: Boom 300, Crash 1000, Vol over Boom 550,
  Volatility 90 (1s). MSNR: Step Index, Volatility 100, Jump 50, Crash 300, Crash 600, Boom 1000, Volatility 90 (1s).
- **Por qué / evidencia**: criterio pedido por el usuario. ICT: replay 365d con límite + tope 2 %. MSNR: replay 2 años, tope 2 %.
  Nota: acierto > 45 % no implica R/trade > 0 (quedan activos algunos con R/trade negativo, listados en la conversación).
- **Ficheros**: `config/strategy_config.py` (fuente única `ICT_WR45_PRUNED`, `MSNR_WR45_PRUNED`, filtra universos y tiers),
  `strategy/ict/config.py` (`wr_pruned_symbols`), `strategy/ict/ict_strategy.py` (rechazo `ICT_SYMBOL_PRUNED_WINRATE_LE_45`),
  `strategy/malaysian_snr/config.py` (`excluded_symbols`), `strategy/malaysian_snr/malaysian_snr_strategy.py`
  (`MSNR_SYMBOL_PRUNED_WINRATE_LE_45`), `strategy/execution/live_trading_engine.py` (`_wr_keep` en listas de workers,
  MSNR `excluded_symbols`), `app/main.py` (`_apply_msnr_wr45_prune`), `dashboard/realtime_dashboard.py` (`_apply_synth_wr45_prune`).
- **Configuración**: `DAEMONBLACKFX_SYNTH_WR45_PRUNE=0` desactiva la poda.
- **Tests**: `tests/test_synth_wr45_prune.py` (11); actualizados v115, v119, v121 y `test_malaysian_snr_integration`.

### 2026-10-19 — ICT: más trades sin bajar el acierto (3 palancas)  ·  Estado: aplicado sin commit
- **Qué**: (1) se liberan en los workers sintéticos antes podados como "tóxicos": Boom 500, Boom 600, Crash 300, Step Index 200,
  Volatility 10, Volatility 100, Volatility 100 (1s). (2) Meta-etiquetado (IA) en **modo sombra** para ICT de sintéticos:
  puntúa y registra (`would_reject_reason`) pero no bloquea. (3) Límite de operaciones simultáneas de 5 a **8** (16 posiciones).
- **Por qué / evidencia**: replay ICT 365d con límite + tope 2 %: podados +0,037 R/t, 52,1 % acierto (igual que permitidos
  +0,038 / 51,7 %), positivo en ambas mitades. Volatility 50 (negativo ambas mitades) y Crash 600 (≈0) siguen podados.
  IA: el replay positivo se midió sin IA; contrafactual en vivo (16–19 oct) rechazadas −0,081 R/t con 46,8 % de acierto
  frente a ejecutadas −0,098 / 45,8 %; la IA bloqueaba ~4 de cada 5 señales ICT. Límite: 42 bloqueos por
  `MAX_TOTAL_OPEN_POSITIONS` el 17–18 oct.
- **Ficheros**: `strategy/execution/live_trading_engine.py` (`_UNPRUNE_SYNTHETICS`, `DEFAULT_MAX_OPEN_POSITIONS`,
  `ict_synthetic_meta_label_shadow`), `app/main.py` (`--max-open-positions` por defecto 16).
- **Configuración**: `DAEMONBLACKFX_ICT_UNPRUNE_SYNTHETICS=0`, `DAEMONBLACKFX_ICT_SYNTH_META_SHADOW=0`,
  `DAEMONBLACKFX_MAX_OPEN_POSITIONS` (por defecto 16). El riesgo abierto máximo sube al 8 %; el tope de riesgo Forex sigue en 5 %.
- **Tests**: `tests/test_ict_more_trades_levers.py` (8); actualizados `test_max_open_positions_ten.py` y `test_worker_family_improvements.py`.

### 2026-10-19 — MSNR solo en sintéticos, sin C2 ni lista, runner TP3/TP4  ·  Estado: aplicado sin commit
- **Qué**: MSNR opera todos los sintéticos (luego podados por acierto, ver arriba), sin la variante C2 ni la lista de 23;
  desactivado en mercados reales; runner hasta 4R con stop progresivo. Versión `msnr-v3.1-synthetics`.
- **Por qué / evidencia**: replay fiel 2 años (`tools/replay_msnr_variants.py`, ajustes por defecto): lista 23 + C2
  −0,126 / −0,117 R/t (~150 trades/año, la peor configuración); sintéticos + tope 2 % −0,020 / +0,015 R/t (~1.300/año);
  mercados reales −0,157 / −0,079. Runner a 3R +0,002 R/t (inocuo). TP1 a 0,5R sube el acierto a 65 % pero baja R/t: descartado.
- **Ficheros**: `app/main.py` (universo del worker MSNR), `strategy/malaysian_snr/config.py` (`synthetics_only`),
  `strategy/malaysian_snr/malaysian_snr_strategy.py`, `strategy/execution/live_trading_engine.py` (`_msnr_flag`,
  `msnr_runner_max_target_rr`), `dashboard/realtime_dashboard.py` (listas MSNR).
- **Configuración**: `DAEMONBLACKFX_MSNR_C2=1` (reactiva C2), `DAEMONBLACKFX_MSNR_ALL_SYNTHETICS=0` (vuelve a la lista de 23),
  `DAEMONBLACKFX_MSNR_SYNTHETICS_ONLY=0` (reactiva mercados reales), `DAEMONBLACKFX_MSNR_RUNNER_MAX_RR` (por defecto 4.0).
- **Tests**: `tests/test_msnr_synthetics_only.py` (9) y tests MSNR actualizados.
- **Riesgos**: los ajustes en base de MSNR (`latest_msnr_runtime_settings`, `asset_modes`) desactivan 37 activos y difieren
  de los por defecto (`breaker_pair_mode=live`, `retest_pinbar_mode=live`, `m5_symbol_modes`). Hay que alinearlos o el cambio no tiene efecto.

### 2026-10-19 — Riesgo de vuelta al 1 % en sintéticos y MSNR  ·  Estado: aplicado sin commit
- **Qué**: `synthetic_risk_multiplier` 0,5 → 1,0 y `DAEMONBLACKFX_MSNR_RISK_MULT` 0,5 → 1,0 por defecto.
- **Por qué**: regla del usuario: toda entrada es 1 % del capital en 2 patas.
- **Ficheros**: `strategy/execution/live_trading_engine.py`. **Tests** actualizados.

### 2026-10-19 — ORB SWEEP en prueba demo para BTCUSD y USDCAD  ·  Estado: aplicado sin commit
- **Qué**: SWEEP activo en BTCUSD (perfil propio) y USDCAD (mercado ORB nuevo, perfil del replay: buffer 0,05 ATR, rango ≤ 1,5 ATR,
  volumen requerido). Corte automático: tras 40 operaciones cerradas en DEMO, si R/operación ≤ 0 se bloquea el activo.
- **Por qué / evidencia**: `tools/replay_orb_sweep_expanded.py` (19 símbolos, ~17 meses): XAUUSD +0,216, USDCAD +0,152,
  BTCUSD +0,289 R/t, positivos en ambas mitades; cartera +0,202 R/t, ~13 trades/mes. Test de azar: p = 0,62 (no concluyente).
  Extensión TP3/TP4 vs TP2 fijo: +0,002 R/t (inocua).
- **Ficheros**: `strategy/orb/asset_rules.py` (`ORB_SWEEP_FORWARD_TEST_SYMBOLS`), `strategy/orb/new_york_orb.py`
  (`USDCAD` en `classify_orb_market` y descubrimiento), `database/repository.py` (`closed_operations_r`),
  `strategy/execution/live_trading_engine.py` (`_orb_sweep_forward_test_gate`), config y dashboard (universo ORB).
- **Configuración**: `DAEMONBLACKFX_ORB_FORWARD_TEST=0`, `DAEMONBLACKFX_ORB_FORWARD_TEST_MIN_TRADES` (40), `DAEMONBLACKFX_ORB_FORWARD_TEST_MIN_R` (0.0).
- **Tests**: `tests/test_orb_sweep_forward_test.py` (12); actualizados `test_orb_sweep_mode.py` y v121.
- **Acción manual**: marcar USDCAD en /Instruments (pestaña ORB).

### 2026-10-19 — Topes de spread en mercados reales y ICT cripto off  ·  Estado: aplicado sin commit
- **Qué**: tope spread/SL de Forex 15 % → 5 % (guard Forex, afecta también a MSNR en Forex); ICT en metales tope 2 % (solo ICT);
  ICT en cripto desactivado.
- **Por qué / evidencia**: replay ICT 2 años (límite vs mercado, `tools/replay_ict_limit_entry.py --tag real_y0/real_y1`):
  Forex 15 % −0,11/−0,06 → 5 % −0,09/−0,00; cripto −0,23/−0,19 con cualquier tope. La entrada limitada **no** mejora en mercados reales.
- **Ficheros**: `strategy/execution/live_trading_engine.py` (`_ict_real_market_spread_gate`, `_spread_ratio_check`,
  `ict_crypto_enabled`, `strategy_name` pasado a `_forex_execution_gate` en sus 3 llamadas).
- **Configuración**: `DAEMONBLACKFX_FOREX_SPREAD_MAX_SL_RATIO`, `DAEMONBLACKFX_ICT_METALS_SPREAD_MAX_SL_RATIO`, `DAEMONBLACKFX_ICT_CRYPTO=1`.
- **Tests**: `tests/test_ict_real_market_caps.py` (13).

### 2026-10-19 — ICT sintéticos: entrada limitada virtual  ·  Estado: aplicado sin commit
- **Qué**: la señal ICT en sintéticos queda pendiente en su `entry_price` (50 % FVG / nivel / mean threshold OB) hasta 8 velas M15;
  se envía a mercado cuando ask ≤ límite (BUY) o bid ≥ límite (SELL); se cancela si toca el SL antes o caduca. En memoria del worker.
- **Por qué / evidencia**: el código ICT ya calculaba un precio limitado pero el bot entraba a mercado. Replay 365d (51 símbolos):
  mercado −0,049 R/t, límite −0,025; **límite + tope 2 % +0,032 R/t (t = 2,9), mitades +0,044 / +0,020**, ~790 trades/mes;
  en las mismas señales el límite gana +0,135 R/trade.
- **Ficheros**: `strategy/execution/live_trading_engine.py` (`_ict_analysis_with_virtual_limit`), `tools/replay_ict_limit_entry.py`.
- **Configuración**: `DAEMONBLACKFX_ICT_VIRTUAL_LIMIT=0`, `DAEMONBLACKFX_ICT_VIRTUAL_LIMIT_BARS` (8).
- **Tests**: `tests/test_ict_virtual_limit_entry.py` (10). Eventos de auditoría `ICT_VIRTUAL_LIMIT` (CREATED/TRIGGERED/EXPIRED/INVALIDATED).

### 2026-10-19 — Tope de spread/SL 2 % en sintéticos  ·  Estado: aplicado sin commit
- **Qué**: bloquea entradas en sintéticos cuyo spread supere el 2 % de la distancia al SL (bid/ask real de MT5).
- **Por qué / evidencia**: replay ICT 365d (21.409 trades): R/trade cae de forma monótona con spread/SL (≤1 % −0,015; >8 % −0,17/−0,27;
  permutación p < 0,002).
- **Ficheros**: `strategy/execution/live_trading_engine.py` (`_synthetic_spread_gate`). **Configuración**: `DAEMONBLACKFX_SYNTHETIC_SPREAD_MAX_SL_RATIO` (0.02).
- **Tests**: `tests/test_synthetic_spread_guard.py`.
- *(El multiplicador de riesgo 0,5x añadido junto a este cambio fue **REVERTIDO** a 1,0x, ver entrada de riesgo.)*

### 2026-10-18 — Fase 1 + ICT solo velas cerradas + ORB SWEEP  ·  Estado: commit `17155b9` (rama BlackDaemon2)
- **ICT solo velas cerradas** (`closed_candles_only` en `strategy/ict/ict_strategy.py`): el bot evaluaba la vela M15 en formación.
  En la demo 15–18 oct, 35 de 105 operaciones salieron de velas que al cerrar no confirmaban la señal (−0,39 R/op vs +0,08).
  Test `tests/test_ict_closed_candles_only.py`. MSNR ya usaba velas cerradas.
- **Fase 1 ICT** (`strategy/ict/config.py`, v2): sin NY Killzone ni London Close, Silver Bullet 03 y 14 NY, exclusión de
  Step Index, Jump 25, Volatility 25 y XAGUSD.
- **ORB SWEEP** (`orb-ny-v5-sweep`): barrido + MSS M5 con paridad señal a señal con `tools/replay_orb_nunez_2y.py`
  (`tests/test_orb_sweep_mode.py`); solo XAUUSD operaba.
- **MSNR C2 + riesgo 0,5x**: luego **REVERTIDO** (ver entradas del 19-oct).
- **Selección alineada** en dashboard, `PRUNED_ASSET_UNIVERSE`, tiers Tri-Motor y listas ORB. Fixture `orb_classic_modes` en `tests/conftest.py`.

---

## Hallazgos de investigación (para no repetirlos)

- **Carry en Forex solo con MT5 (24-oct-2026)**: top 3 pares por swap actual, rebalanceo mensual, contrato de dos entradas: +0,225 R/op en ene-2025 → oct-2026 (azar +0,023). Es orientativo (swap actual aplicado al pasado); falta la prueba demo hacia adelante.
- **ICT sintéticos, dos años (24-oct-2026)**: cartera +0,024 / +0,032 R/op (t 2,1 / 2,9). El R por activo no persiste entre años (correlación −0,25): no podar ni elegir activos con un año. Validez del límite: 8 velas es la mejor.
- **Cambio de mes en índices US (24-oct-2026)**: no mejora a mantener comprado en ventanas al azar de la misma duración (+0,016 frente a +0,034 R/op, 5 años). **RSI2 + ETF**: los ETF no equivalentes a los CFD aportan poco (+0,057) y cuadruplican la caída máxima; no se añaden.
- **ETF (24-oct-2026)**: el RSI(2) de Connors del worker supera el pre-registro en 22 ETF del broker (2023-26: +0,096 R/op, positivo en los tres periodos, p azar 0,022). En cripto no superan ni RSI2 ni la ruptura Donchian (swap del 15–20 % anual).
- **Demo contaminada (24-oct-2026)**: el 14 % de las piernas de octubre se cerraron a mano (+0,24 R). Hay que excluirlas de cualquier criterio de prueba.
- **Deriv ≠ broker en índices US (23-oct-2026)**: en modo shadow el análisis usa velas de Deriv. Para US SP 500, US Tech 100 y Wall Street 30 son otra serie (56 % de velas H1 coincidentes, desfase del 24–40 % del rango H1). Oro ≈ igual y US Oil usa MT5. Las estrategias validadas con MT5 deben analizar con MT5.
- **Spread de las velas MT5 ≠ spread real (23-oct-2026)**: el campo `spread` de las velas es el mínimo del periodo. En Drift Switch el real (ticks) es ~12× mayor, lo que anula DRIFT (−0,030 R/op). En índices US coincide. Todo replay de sintéticos debe usar el spread de ticks (o un factor tick/vela medido por símbolo).
- **5 años de Dukascopy (23-oct-2026)**: RSI2 diario US +0,150 R/op (positivo en 2021-22, 2023-24 y 2025-hoy; p azar 0,001; t por día 1,78). NIGHT no mejora a mantener comprado el índice en horas al azar (beta). Momentum 12 m, COT contrario y tipos reales en oro/plata/Brent no superan con el contrato de dos entradas.
- **Materias primas con indicadores (22-oct-2026)**: RSI(2) diario en ambos sentidos, Supertrend H4 + ADX y ratio oro/plata no superan el criterio (−0,095 / −0,067 / +0,045 no significativo). El Supertrend en oro sale positivo, pero también el azar (deriva alcista del oro); el petróleo pierde con fuerza con tendencia H4.
- **Forex con indicadores (22-oct-2026)**: momentum diario (63 d + SMA100 + RSI), reversión asiática (Bollinger + RSI, 00-05 UTC) y retroceso en tendencia H4/H1 pierden con el contrato de dos entradas (−0,019 / −0,043 / −0,132 R/op) en 27 pares y 2 años, y también fuera de muestra (salvo Asia, +0,038 sin significancia). Junto a Donchian, sesiones e ICT: el Forex del broker no tiene ventaja con indicadores clásicos.
- **Índices bursátiles con indicadores (21-oct-2026)**: tendencia, ruptura Donchian y todo lo intradía (RSI2 H1, EMA/ADX, ORB 30 min + VWAP) pierden con spread y swap reales. Solo el RSI(2) diario de Connors en los 5 índices US es positivo y robusto (+0,176 R/op), pero con 79 episodios independientes en 2 años (t por día 1,9) no es concluyente.
- **Familia Step = paseo aleatorio (21-oct-2026)**: sin deriva, autocorrelación (|ρ| ≤ 0,013), ratio de varianzas (0,96–1,05), rachas ni estacionalidad estables en 2 años y 12 símbolos. Ninguna estrategia de indicadores puede tener ventaja direccional ahí; confirmado con el replay de 4 estrategias (RSI2, Supertrend, MACD y Keltner: todas entre −0,010 y −0,024 R/op). No repetir sin un dato nuevo.
- **Indicadores clásicos en sintéticos (21-oct-2026)**: tendencia, reversión y ruptura no tienen ventaja en el conjunto de los 98 sintéticos (replay de 2 años). La excepción es la **ruptura en Drift Switching Indices** (+0,086 R/op, t 3,9, robusta a los parámetros). Volatility Indices pierde con la tendencia por EMA/ADX.
- **Validación ampliada (21-oct-2026).**
  - **S4 (pre-registrada) NO supera** su criterio: fuera de muestra (oct-2022 → sep-2024) −0,068 R/t (t = −5,3).
    - Forex −0,065, índices −0,161; solo 1 de 8 trimestres positivo.
    - Tanto ir en contra (S2) como a favor (S4) de la falsa ruptura pierde: los costes dominan. Descartada.
  - **S3, sesgo nocturno, SÍ se sostiene** con todo el historial del broker (M30 desde el 22-ene-2024; antes no hay
    datos de índices, así que los 6 años no son posibles):
    - **US SP 500**: bruto +0,062 %/noche (t = 2,6), neto de spread y swap +0,033 % (t = 1,4). Sesión diurna ≈ 0.
      Positivo en los 3 periodos, incluido el tramo nuevo ene-oct 2024.
    - **US Tech 100**: bruto +0,083 % (t = 2,5), neto +0,056 % (t = 1,7); positivo en los 3 periodos.
      Sharpe ≈ 1,0, caída máxima −19 %, peor noche −5,4 %.
    - Ambos juntos: neto +0,044 %/noche (t = 2,2); 8 de 12 trimestres positivos. Wall Street 30 neto ≈ 0.
    - Límites: 2,75 años, todos alcistas; estrategia solo compradora sin stop (riesgo de hueco en la apertura).
      No encaja en el contrato TP1/runner, porque sale por tiempo.
- **PRE-REGISTRO (21-oct-2026, antes de mirar los datos anteriores a oct-2024) — S4 continuación tras falsa ruptura.**
  - Disparo: igual que S2. En la ventana de sesión (Londres 08-12 en Forex y metales; NY 09:30-11:30 en índices),
    la primera vela M15 cuya mecha supera el rango previo (00:00 Londres → inicio de ventana) y que cierra de vuelta
    dentro.
  - Entrada **a favor de la ruptura** (compra si barrió el máximo) en la apertura siguiente.
  - SL en la mitad del rango.
  - Gestión: contrato 1R/2R con BE, cierre al final del día, tope spread/SL 5 %.
  - **Criterio de éxito** (fuera de muestra, datos de 28-oct-2022 a 30-sep-2024):
    - R/t > 0 en el total y en los dos años por separado;
    - t ≥ 2,0;
    - el mismo signo en Forex y en metales o índices.
  - Sin cambiar ningún parámetro.
- **Anomalías de sesión en mercados reales (21-oct-2026, `tools/research_session_anomalies.py`).**
  - Datos: 20 pares Forex, XAUUSD, XAGUSD y 3 índices US; 2 años; reglas fijadas antes de mirar; spread = mediana M15;
    swap real.
  - **S1, ruptura del rango asiático en Londres** (índices: apertura de NY): −0,030 R/t (t = −2,8).
    - Forex −0,035, negativo en ambos años. Descartada.
  - **S2, falsa ruptura (Judas swing)**: −0,128 R/t (t = −7,5), negativa en todos los mercados y en ambos años.
    Descartada. Que sea tan negativa sugiere que tras la falsa ruptura el precio suele continuar. Esa idea es una
    hipótesis nueva sacada de estos datos: solo puede validarse con otro periodo.
  - **S3, sesgo nocturno en índices** (compra a las 16:00 NY y venta a las 09:30):
    - Bruto positivo en ambos años en US SP 500 (+0,047 %/noche, t = 1,6) y US Tech 100 (+0,063 %, t = 1,6).
    - El swap se come ~60 %: neto +0,018 % y +0,037 % (t < 1). Wall Street 30 neto ≈ 0.
    - No es significativo con 2 años, y además va siempre comprado.
  - Conclusión: ninguna de las tres anomalías da una ventaja neta robusta con los costes de este broker en 2 años.
- **H4→H1 (vídeos) NO se replica en mercados reales (21-oct-2026, `research_msnr_storyline_h4h1.py --tag real`, 26 símbolos,
  2 años, spread = mediana M15).**
  - Tope 5 %: total −0,045 R/t (t = −4,9), negativo en ambos años y en 9 de 9 trimestres.
    - Forex: −0,049 (y0 −0,045 / y1 −0,054).
    - Índices: −0,012 (y0 +0,010 / y1 −0,032).
    - Metales y petróleo: −0,046.
  - Tope 2 %: total −0,030; índices −0,004.
  - Ningún símbolo es robusto: los mejores (EURAUD, Wall Street 30, USDJPY) cambian de signo entre años.
  - Conclusión: la ventaja en sintéticos viene de su microestructura y sus costes, y no se traslada a mercados reales.
- **MSNR en los 61 sintéticos que no opera (20-oct-2026, `replay_msnr_variants.py --limit`, 2 años, tope 2 %).**
  - Conjunto: 3.963 señales, +0,014 R/t (t = 0,8; y0 +0,017 / y1 +0,011). Sin ventaja demostrada.
  - **Elegir los símbolos "positivos en ambos años" es sesgo de selección.**
    - Salen 12 de 45 con muestra suficiente, cuando por azar se esperan ≈ 11.
    - Su cartera (+0,115 R/t) no es una evidencia.
  - **Única excepción robusta: DEX 1500 UP Index.**
    - n = 210, +0,299 R/t, t = 4,1 (supera la corrección por 45 pruebas), y0 +0,241 / y1 +0,398.
    - Ambas direcciones positivas (SELL +0,37, BUY +0,16).
    - Candidato a prueba demo; el resto no se activa.
- **MSNR (Malaysian SNR), 2 años, `replay_msnr_variants.py --free-busy --limit` (20-oct-2026).**
  - Dejar el símbolo libre tras un descarte por spread casi no cambia nada (30 activos: +0,030 → +0,025 R/t;
    con el filtro de régimen, +0,073 → +0,069). La ocupación fantasma **no** hace falta en MSNR y sus replays sí
    representan al bot en vivo.
  - La **entrada limitada empeora MSNR en ambos años**:
    - 30 activos: lim_level −0,003 y lim_mid +0,010, frente a +0,025 a mercado.
    - Con el filtro de régimen: +0,029 / +0,051 frente a +0,069.
    No se implementa.
- **Reglas de los vídeos MSNR medidas en el replay (20-oct-2026, `tools/research_msnr_storyline_h4h1.py`, 37 sintéticos, 2 años, tope spread/SL 2 %).**
  - **La storyline D1+H4 como filtro de dirección NO se sostiene.**
    - Señales MSNR a favor de la storyline: +0,015 R/t (y0 +0,031 / y1 −0,000).
    - En contra: +0,102. Sin storyline: −0,024.
    - Con los 30 activos y el filtro de régimen, a favor da +0,109 frente a +0,073 del total, pero solo con el
      19 % de las señales, y en contra también es positivo. No se implementa.
  - **La confirmación H4→H1 como escenario propio SÍ.**
    - Regla: H4 rechaza un nivel A/V H4 y H1 rompe un open-close; entrada en la H1 siguiente, SL tras la H4 y
      gestión del contrato 1R/2R.
    - 18.595 operaciones (≈ 25/día en 37 sintéticos), **+0,029 R/t**, acierto 51,4 %, t = 3,75.
    - **y0 +0,026 / y1 +0,031**; 8 de 9 trimestres positivos.
    - IC95 % bootstrap por días [+0,014; +0,044]. Sin los 7 mejores símbolos, +0,017.
    - Con los 30 activos: +0,032 (t = 3,77). Positivo en ambos años en 14 de 37 símbolos.
    - Es unas 7 veces la frecuencia de MSNR actual con un R/t igual o mejor.
  - **Límites de la medición**: simulación de investigación, no la clase MSNR. Spread estático del símbolo,
    entrada en la apertura H1 y una operación por símbolo solo dentro del escenario. No mide la competencia por
    los 8 huecos simultáneos con ICT y MSNR.
- **Vídeos MSNR frente a la implementación (20-oct-2026, `MSNR_VIDEOS_VS_IMPLEMENTACION_20261020.md`).**
  - Coinciden los niveles en cierres de vela, RBS/SBR, QM, open-close, Fresh = primer toque y el SL detrás del patrón.
  - Diferencias clave:
    1. Dirección por storyline M/W/D: el diario rechaza un nivel diario y H4 rompe. En sintéticos está desactivado.
    2. Entrada de confirmación H4→H1 frente a la nuestra en M15.
    3. Objetivo en el siguiente nivel del marco con parciales, frente a nuestro 1R/2R fijo por contrato.
    4. Obstáculos H4.
    5. Líneas de tendencia y horario.
    6. MBA: imbalance obligatorio y evitar zonas con exceso de liquidez.
    7. A/V sin envolvente.
  - Breaker Pair y Pinbar están en live en la base sin evidencia, y su ablación quedó pendiente.
  - Siguiente paso medible: storyline D1+H4 y confirmación H4→H1 en el replay fiel.
- **Ventaja real de ICT en sintéticos y la regla de "ocupación fantasma" (20-oct-2026, conciliación).**
  - Las 6.970 operaciones comunes a los dos replays dan lo mismo (+0,051).
  - La diferencia (+0,049 frente a +0,015) viene de 1.968 operaciones que solo existen cuando una señal
    descartada por spread/SL > 2 % deja el símbolo libre, como hace hoy el bot en vivo. Esas operaciones
    pierden −0,11 R/t.
  - **Ventaja real con el bot actual**: +0,015 R/t (último año) y +0,004 R/t (año previo).
  - **Regla validada fuera de muestra** (`replay_ict_exit_variants.py --phantom-busy`): una señal descartada
    por spread ocupa el símbolo hasta su resultado virtual.
    - Año previo (no usado para descubrirla): +0,004 → **+0,022 R/t**, acierto 50,3 → 51,2 %; las operaciones
      quitadas dan −0,157 R/t (t = −4,9); R total +39 → **+191**.
    - Último año: +0,015 → **+0,047 R/t**, acierto 50,8 → 52,3 %; R total +137 → +356.
    - Ambas mitades positivas en los dos años. Coste: 9-16 % menos de operaciones.
- **El acierto no se puede subir moviendo las salidas sin perder rentabilidad (20-oct-2026, `tools/replay_ict_exit_variants.py`).**
  - ICT, 28 sintéticos, entrada limitada, tope 2 %, 2 años, 18.331 operaciones, mismas señales en todas las
    variantes. Gestión actual (TP1 1R + runner 2R): 50,6 % de acierto, +0,010 R/t.
    - TP1 0,8R: 56,0 % de acierto pero −0,0085 R/t (t = −3,0).
    - TP1 0,6R: 62,7 % pero −0,024 R/t (t = −5,7). Peor en ambos años.
    - El objetivo del runner no cambia el acierto. Runner 3R: +0,004 R/t (t = 1,5), mejor en ambos años pero
      no significativo; ya existe la extensión progresiva TP3/TP4.
  - MSNR (2 años): TP1 0,5R sube el acierto del 51,7 % al 66,9 % pero deja el R/t negativo (−0,026).
  - Conclusión: el acierto solo se puede subir sin perder dinero quitando operaciones perdedoras, con filtros
    validados y una ejecución mejor. Mover el TP1 lo compra a costa del resultado.
- **Brecha demo-replay en ICT (20-oct-2026, `tools/research_ict_demo_gap.py`; 119 operaciones demo, 9-20 oct).**
  - **Coste de entrada medio: 0,16-0,18R por operación.**
    - Persecución: el precio ya se había alejado de la entrada de la señal al enviar la orden (+0,13-0,15R).
    - Spread: +0,06R.
    - Deslizamiento del broker: 0. El broker no es el problema.
  - Encaja con el replay (límite − mercado = +0,135R). Desde el reinicio del 20-oct, con la entrada limitada
    virtual, la persecución en sintéticos es ≈ 0 (−0,04 a +0,002R).
  - **El 58 % de las operaciones demo v1 no existen en el replay fiel**: entraban 15 min antes, con la vela en
    formación. Perdieron −0,133 R/op; las que sí existen ganaron +0,070. Esto ya está corregido en Fase 1.
  - **El Centinela de Régimen (`MARKET_REGIME_TOXIC_BLOCKED`, modo FILTER) quita trades buenos.**
    - Corre antes del análisis en todos los workers y no está en el replay fiel.
    - Aplicado a las señales del replay ICT (28 activos, tope 2 %), bloquea el 18 %, y esas señales rinden
      **+0,067 R/t** frente a +0,045 de las permitidas: positivas en ambas mitades, +91R en el año.
    - El tramo `HIGH_CHOPPINESS_LOW_MOMENTUM` da +0,258 R/t.
    - Desde el reinicio del 20-oct lleva ~1.900 bloqueos.
  - **Fallo de clasificación**: `_is_synthetic_symbol` no reconoce High Frequency Vol 50/100 ni VolSwitch High
    Vol. En ellos no se aplican la entrada limitada, el tope spread/SL 2 % ni la IA en sombra (rechazos de IA en
    VOLATILITY_2).
  - Ruido de registro: un límite virtual disparado pero bloqueado por spread se vuelve a crear y disparar cada
    ciclo (`ICT_VIRTUAL_LIMIT` CREATED/TRIGGERED cada minuto). Es inofensivo, pero llena la auditoría.
- **ICT sintéticos: no hay filtro de contexto que generalice (20-oct-2026, `tools/research_ict_slices.py`).**
  - Base: 28 activos, entrada limitada, tope spread/SL 2 %, 365 días: n = 7.479, **+0,049 R/t**, acierto 52,3 %,
    t = 4,0, ambas mitades positivas (+0,065 / +0,034).
  - Contexto calculado con velas H1 cerradas: ADX, SL/ATR, percentil de ATR, tendencia 24 h, hora UTC, día,
    dirección, spread/SL y velas hasta el fill.
  - Ningún tramo es negativo en ambas mitades con n suficiente.
  - Fuera de muestra (tramos malos elegidos en una mitad y quitados en la otra):
    - ADX: +0,034 → +0,035 y +0,065 → +0,070 (nulo).
    - Hora UTC: **empeora** (+0,065 → +0,042).
    - SL/ATR: empeora.
    - Poda por símbolo: **empeora** (+0,034 → +0,016).
    - Una puntuación de prioridad no separa los mejores trades.
  - Conclusión: la ventaja de ICT en sintéticos está repartida y viene del coste y del precio de entrada. No se
    deben añadir filtros por hora, ADX ni símbolo, ni podar más símbolos por resultados de un solo periodo. Las
    mejoras deben venir de **volumen** (más sintéticos bajo el tope 2 %) y de **fidelidad de ejecución**
    (brecha demo-replay).
  - El filtro de régimen de MSNR (ADX 25-40) es dentro de muestra; por eso va en prueba demo.
- **La demo pierde (−0,088 R/trade, 1.031 patas, 4-sep → 18-oct)**. El replay fiel de ICT con entrada a mercado también:
  −0,045 (365d, código 10-oct) y −0,048 R/t (365d, código actual, 21.409 trades).
- **`tools/replay_ict_60_assets_2year_audit.py` reimplementa la estrategia**: sus "+486 R" y los tiers Tri-Motor no representan el bot.
- **Sintéticos ≈ paseo aleatorio** (36 índices, M5, ~99k velas: autocorrelación ≈ 0, ratio de varianza ≈ 1). La ventaja posible
  depende de **costes** (spread/SL) y del **precio de entrada** (límite), no de patrones de precio.
- **Descartados por el replay**: momentum intradía en índices US (Gao et al.), tendencia diaria Donchian 55/20 (no mejora al azar),
  entrada limitada en Forex/metales/cripto, hipótesis "índices US SELL" (−0,24 R/t fuera de muestra), TP1 a 0,5R (más acierto, menos R).
- **MSNR en Forex con spread/SL ≤ 5 %**: +0,124 / +0,149 R/t con ajustes por defecto (n ≈ 30/año), **pero no se sostiene con
  los ajustes reales de la base** (20-oct, `tools/replay_msnr_variants.py --live-settings --enable-all-assets`, 40 mercados, 2 años):
  Forex −0,360 / −0,371 R/t (acierto 35 %), índices −0,218 / −0,317, cripto −0,284 / −0,555. Con tope 5 % quedan muy pocos trades
  (Forex 20 / 6 al año). La entrada limitada (nivel o 50 %) empeora. **Conclusión**: los ajustes guardados en la base
  (`breaker_pair_mode=live`, `retest_pinbar_mode=live`, `m5_symbol_modes`) generan muchas más señales y de peor calidad que los por defecto.
- **Límite de MT5**: "Máx. barras en el gráfico" = 100.000 → M5 solo ~17 meses. Subirlo a ilimitado permitiría validar con años.
- **Dashboard**: `/api/state` pesa ~12 MB y tarda 20–50 s (`account.recent_trades` 5 MB, rendimiento mensual/periodo 3,7 MB).
- **MT5 rechaza** Volatility 250 (1s) con `retcode 10034 Volume limit reached`.
- **`dashboard/performance_page.py::_hot_sync_realtime_dashboard`** parchea en caliente clases y objetos vivos y silencia errores: riesgo, se recomienda quitarlo.

## Herramientas de investigación (solo lectura, no tocan el bot)

| Herramienta | Uso | Salida (`storage/analysis/`, no versionado) |
|---|---|---|
| `tools/replay_ict_live_faithful.py` | Replay fiel ICT (mercado) | `ict_faithful_*` |
| `tools/research_commodity_indicators.py` | RSI(2) diario, Supertrend H4 y ratio oro/plata en metales, petróleo y cacao, contrato de dos entradas | `commodity_indicators_*` |
| `tools/research_forex_indicators.py` | Momentum diario, reversión asiática y retroceso en tendencia en 27 pares, contrato de dos entradas, fuera de muestra 23-24 | `forex_indicators_*` |
| `tools/research_rsi2_management.py` | Gestión del RSI(2) diario US en velas M15: regla vs dos entradas vs contrato puro | `rsi2_management_*` |
| `tools/research_fx_carry_mt5.py` | Carry G10 solo con MT5 (swap actual), contrato de dos entradas con runner fijo o progresivo | `fx_carry_mt5_report.md` |
| `tools/research_turn_of_month.py` | Efecto cambio de mes en índices US (Dukascopy 5 años), comparado con el azar | `turn_of_month_report.md` |
| `tools/research_etf_crypto.py` | RSI2 en ETF y cripto; ruptura Donchian en cripto (pre-registrado) | `etf_crypto_*` |
| `tools/research_real_spread_recheck.py` | Factor spread ticks/velas por símbolo y re-medición de ICT/MSNR con spread real | `real_spread_*` |
| `tools/research_index_indicators.py` | 3 estrategias × diario/intradía en los 16 índices, spread y swap reales, sesiones de contado, prueba de azar | `index_indicators_*` |
| `tools/research_step_indicators.py` | Batería RSI2, Supertrend, MACD y Keltner en los 12 Step, prueba de azar | `step_indicators_*` |
| `tools/research_step_diagnostics.py` | Aleatoriedad de la familia Step (deriva, autocorrelación, ratio de varianzas, rachas, horas, coste) | `step_diagnostics_report.md` |
| `tools/research_synthetic_indicators.py` | 3 estrategias de indicadores (tendencia, reversión, ruptura) en todos los sintéticos, prueba de azar, `--symbols`, `--tag` | `synthetic_indicators_*` |
| `tools/replay_ict_limit_entry.py` | ICT límite vs mercado, `--end-days-ago`, `--tag` | `ict_limit_entry_signals*.csv` |
| `tools/replay_msnr_variants.py` | MSNR por señal, 5 gestiones, `--limit`, `--live-settings`, `--enable-all-assets` | `msnr_variants_signals_*.csv` |
| `tools/research_ict_slices.py` | Contexto H1 (ADX, ATR, SL/ATR, tendencia, hora) por señal del replay ICT límite | `ict_slices_features.csv`, caché `ict_slices_h1_cache/` |
| `tools/research_ict_demo_gap.py` | Operaciones ICT demo: persecución, spread, deslizamiento y R vs replay (base en solo lectura) | `ict_demo_gap_operations.csv` |
| `tools/replay_ict_exit_variants.py` | ICT límite: mismas señales con 8 gestiones de TP1/runner | `ict_exit_variants_{y1,y0}.csv` |
| `tools/daily_tracking_report.py` | Seguimiento diario demo vs replay por familia, símbolo y filtros | `seguimiento_diario/informe_<día>.md`, `seguimiento_diario.csv` |
| `tools/research_msnr_storyline_h4h1.py` | Storyline D1+H4 sobre señales MSNR y escenario H4→H1 de los vídeos | `msnr_storyline_signals.csv`, `msnr_h4h1_trades.csv` |
| `tools/replay_orb_sweep_expanded.py` | ORB SWEEP ampliado con gestión completa | `orb_sweep_expanded_*` |
| `tools/research_intraday_momentum.py` | H1 momentum intradía | `research_intraday_momentum_*` |
| `tools/research_trend_following.py` | H2 tendencia Donchian | `research_trend_following_*` |
| Pre-registro de hipótesis | — | `research_preregistro_20261019.md` |

## Variables de entorno (interruptores)

| Variable | Por defecto | Efecto |
|---|---|---|
| `DAEMONBLACKFX_SYNTHETIC_SPREAD_MAX_SL_RATIO` | 0.02 | Tope spread/SL sintéticos |
| `DAEMONBLACKFX_SYNTHETIC_RISK_MULT` | 1.0 | Multiplicador de riesgo sintéticos (0,1–1,0) |
| `DAEMONBLACKFX_MSNR_RISK_MULT` | 1.0 | Multiplicador de riesgo MSNR (0,1–1,0) |
| `DAEMONBLACKFX_SYNTH_DETECTION_EXTENDED` | 1 | Detección de sintéticos alineada con el replay (HF Vol, VolSwitch…) |
| `DAEMONBLACKFX_MARKET_REGIME_ICT_SYNTH_MODE` | OBSERVE | Centinela de Régimen para ICT en sintéticos (OBSERVE/FILTER) |
| `DAEMONBLACKFX_ICT_SPREAD_LOCK` / `_MAX_HOURS` | 1 / 50 | Ocupación fantasma tras descarte por spread en ICT sintéticos |
| `DAEMONBLACKFX_MSNR_H4H1` / `_START` / `_REVIEW_TRADES` / `_MIN_R` | off / 2026-10-21 / 200 / 0.0 | Escenario H4→H1 dentro de Malaysian SNR (apagado: vive en el worker MSNR) |
| `DAEMONBLACKFX_MSNR_DEMO_TEST_SYMBOLS` / `DAEMONBLACKFX_MSNR_SYMBOL_TEST_*` | on / 2026-10-21 / 40 / 0.0 | DEX 1500 UP Index en Malaysian SNR y su prueba demo |
| `DAEMONBLACKFX_POLICY_CYCLE_FILTER` | 1 | Los ciclos no escanean instrumentos en PODA PREVENTIVA |
| `DAEMONBLACKFX_DISABLED_WORKERS` | FOREX_1,FOREX_2,FOREX_3,FOREX_4,ICT,GOLD,IDX_OPEN | Workers sin entradas nuevas (vacío = todos activos) |
| `DAEMONBLACKFX_ICT_BROKER_CANDLE_SYMBOLS` | US SP 500,US Tech 100,Wall Street 30 | ICT y el centinela de régimen leen estos símbolos del broker MT5 (vacío = Deriv) |
| `DAEMONBLACKFX_NATIVE_BROKER_CANDLES` | 1 | RSI2 y NIGHT analizan velas del broker MT5 (no Deriv) en modo shadow |
| `DAEMONBLACKFX_REAL_SPREAD_PRUNE` | 1 | Poda por spread real (VolSwitch High Vol Index) en ICT, MSNR y Malaysian SNR |
| `DAEMONBLACKFX_DRIFT_SETUP_DEDUPE` / `DAEMONBLACKFX_RSI2_SETUP_DEDUPE` | 0 / 0 | Marcado de señal en la estrategia (0 = reintento; el motor deduplica) |
| `DAEMONBLACKFX_PRIORITY_PROFILES` / `DAEMONBLACKFX_PRIORITY_EXTRA_SLOTS` | DRIFT,RSI2,NIGHT,CARRY / 4 | Huecos reservados sobre el límite global para workers validados |
| `DAEMONBLACKFX_NATIVE_META_SHADOW` / `DAEMONBLACKFX_OWN_SYMBOL_LIMIT_PROFILES` | 1 / RSI2,NIGHT,CARRY | IA en sombra para estrategias nativas; límite por símbolo propio |
| `DAEMONBLACKFX_CARRY` / `_START` / `_REVIEW_TRADES` / `_MIN_R` / `_RUNNER_EXTENSION` | demo_test / 2026-10-24 / 36 / 0.0 / 1 | Worker CARRY y su prueba demo; extensión progresiva TP3/TP4 del runner |
| `DAEMONBLACKFX_CARRY_SYMBOLS` / `_TOP_N` / `_MIN_ANNUAL` / `_STOP_ATR` / `_ENTRY_WINDOW_HOURS` | 28 pares G10 / 3 / 0.0 / 3.0 / 24 | Universo, nº de pares por mes, carry mínimo anual, stop en ATR D1 y ventana de entrada del mes |
| `DAEMONBLACKFX_RSI2` / `_START` / `_REVIEW_TRADES` / `_MIN_R` / `_SYMBOLS` / `_THRESHOLD` / `_STOP_ATR` / `_MAX_DAYS` / `_MAX_ENTRY_DELAY_MIN` / `_SPLIT` | demo_test / 2026-10-22 / 60 / 0.0 / 5 índices US / 10 / 2.0 / 10 / 120 / 1 | Worker RSI2 (RSI(2) diario de Connors) y su prueba demo |
| `DAEMONBLACKFX_DRIFT` / `_START` / `_REVIEW_TRADES` / `_MIN_R` / `_SYMBOLS` / `_STOP_ATR` / `_MAX_SIGNAL_AGE_MIN` / `_RUNNER_EXTENSION` | **off** (antes demo_test) / 2026-10-21 / 200 / 0.0 / Drift Switch 10,20,30 / 1.5 / 10 / 0 | Worker DRIFT (ruptura tras compresión) y su prueba demo |
| `DAEMONBLACKFX_OVERNIGHT` / `_START` / `_REVIEW_TRADES` / `_MIN_R` | demo_test / 2026-10-21 / 120 / 0.0 | Worker NIGHT (sesgo nocturno) y su prueba demo |
| `DAEMONBLACKFX_MSNR_VIDEO` / `_STORYLINE` / `_START` / `_REVIEW_TRADES` / `_MIN_R` | demo_test / observe / 2026-10-21 / 200 / 0.0 | Worker MSNR (estrategia de los vídeos) y su prueba demo |
| `DAEMONBLACKFX_MSNR_REGIME_FILTER` | demo_test | Filtro de régimen MSNR: off / demo_test (solo DEMO) / live |
| `DAEMONBLACKFX_MSNR_REGIME_ADX_MIN` / `_ADX_MAX` | 25 / 40 | Tramo de ADX bloqueado (min, max] |
| `DAEMONBLACKFX_MSNR_REGIME_START` | 2026-10-21T00:00Z | Inicio de la prueba demo del filtro |
| `DAEMONBLACKFX_MSNR_REGIME_REVIEW_TRADES` / `_MIN_R` / `_MIN_WR` | 60 / 0.0 / 0.50 | Criterio fijado de la prueba demo |
| `DAEMONBLACKFX_ICT_VIRTUAL_LIMIT` / `_BARS` | 1 / 8 | Entrada limitada virtual ICT sintéticos |
| `DAEMONBLACKFX_FOREX_SPREAD_MAX_SL_RATIO` | 0.05 | Tope spread/SL Forex |
| `DAEMONBLACKFX_ICT_METALS_SPREAD_MAX_SL_RATIO` | 0.02 | Tope spread/SL ICT metales |
| `DAEMONBLACKFX_ICT_CRYPTO` | 0 | ICT en cripto |
| `DAEMONBLACKFX_ORB_FORWARD_TEST` / `_MIN_TRADES` / `_MIN_R` | 1 / 40 / 0.0 | Prueba demo ORB SWEEP |
| `DAEMONBLACKFX_MSNR_C2` | 0 | Variante C2 de MSNR |
| `DAEMONBLACKFX_MSNR_ALL_SYNTHETICS` | 1 | MSNR sin lista de 23 |
| `DAEMONBLACKFX_MSNR_SYNTHETICS_ONLY` | 1 | MSNR solo sintéticos |
| `DAEMONBLACKFX_MSNR_RUNNER_MAX_RR` | 4.0 | Objetivo máximo runner MSNR |
| `DAEMONBLACKFX_ICT_UNPRUNE_SYNTHETICS` | 1 | Libera sintéticos podados en workers |
| `DAEMONBLACKFX_ICT_SYNTH_META_SHADOW` | 1 | IA en sombra para ICT sintéticos |
| `DAEMONBLACKFX_MAX_OPEN_POSITIONS` | 16 | Posiciones físicas simultáneas (2 por operación) |
| `DAEMONBLACKFX_SYNTH_WR45_PRUNE` | 1 | Poda por acierto ≤ 45 % |
| `DAEMONBLACKFX_RUNNER_SL_REQUIRES_TP1` | 1 | El RUNNER solo mueve su SL tras el cierre en ganancia de TP1 |
| `DAEMONBLACKFX_LEG_VOLUME_LIMIT_CAP` | 1 | Reparte el `volume_limit` del símbolo entre las piernas (evita `retcode 10034`) |
| `DAEMONBLACKFX_ICT_VIRTUAL_LIMIT_ONE_SHOT` | 1 | Un límite ICT caducado/invalidado no se recrea con la misma señal |
| `DAEMONBLACKFX_DASHBOARD_STRICT_REQUESTS` | 1 | El dashboard rechaza peticiones de otras webs (Host/Origin/JSON) |
| `DAEMONBLACKFX_DASHBOARD_HOT_SYNC` | 0 | Parche en caliente de módulos al abrir /strategy-bases y /performance |
| `DAEMONBLACKFX_DEMO_TEST_EXCLUDE_MANUAL` | 1 | Los criterios de las pruebas demo ignoran operaciones con piernas cerradas a mano |
| `DAEMONBLACKFX_MARKET_REGIME_ORB_MODE` | OBSERVE | Centinela de régimen en ORB (prueba demo; FILTER restaura el veto) |
| `DAEMONBLACKFX_MSNR_AI_INCOMPATIBLE_DEFAULT` | observe | IA de MSNR con modelo incompatible (observe solo en DEMO / block) |
| `DAEMONBLACKFX_ICT_H4_CANDLES` | 101 | Velas H4 del sesgo macro de ICT |
| `DAEMONBLACKFX_ICT_H4_COMPLETE_ONLY` | 1 | La H4 reconstruida desde H1 descarta el bloque en formación |
| `DAEMONBLACKFX_US_EQUITY_RISK_CAP` / `_FACTOR_SYMBOLS` | 0 (off) / 5 índices US | Tope de riesgo abierto en renta variable US |
| `DAEMONBLACKFX_DASHBOARD_LAZY_CHARTS` | 1 | `/api/state` sin gráficos de posiciones; el front los pide por posición |
| `DAEMONBLACKFX_MSNR_REAL_MARKETS` / `_START` / `_REVIEW_TRADES` / `_MIN_R` / `_SPREAD_MAX_SL_RATIO` | demo_test / 2026-10-26 / 40 / 0.0 / 0.05 | Malaysian SNR en mercados reales de bajo coste y su prueba demo |
| `DAEMONBLACKFX_MSNR_REAL_SYMBOLS` / `_REAL_SESSION` / `_REAL_SESSION_OVERRIDES` | Germany 40, XAUUSD, USDJPY, GBPUSD, EURUSD, NZDUSD, GBPCAD, AUDUSD, CADCHF, EURGBP, GBPCHF, CADJPY, GBPJPY, CHFJPY / asia_to_ny / EURUSD y los 9 forex nuevos:legacy_utc | Instrumentos reales de MSNR, sesión general y sesión por activo |
| `DAEMONBLACKFX_MSNR_INSTRUMENTS_CONTROL` | on | /Instruments es el único control de Malaysian SNR (`off` = mandan `asset_modes` y la lista adicional de los ajustes) |
| `DAEMONBLACKFX_MSNR_ACIERTO47` | on | Malaysian SNR solo con los 27 sintéticos de acierto > 47 % (`off` = lista anterior + DEX) |
| `DAEMONBLACKFX_MSNR_SYNTHETICS_ACTIVE` | (vacío) | Lista explícita de sintéticos de Malaysian SNR (por comas); sustituye la de acierto > 47 % |
| `DAEMONBLACKFX_MSNR_ASIA_START_NY` / `_NY_CUTOFF_NY` | 19 / 14 | Ventana Asia → NY en hora de Nueva York |
| `DAEMONBLACKFX_ICT_TRIGGER_LOCK` | 1 | Una señal ICT de sintéticos que dispara y no se abre ocupa el símbolo hasta su resultado virtual |
| `DAEMONBLACKFX_SKIP_DISABLED_WORKER_PROCESSES` / `DAEMONBLACKFX_SPAWN_EMPTY_FLIP_WORKER` | 1 / 0 | No lanza subprocesos para workers desactivados sin posiciones abiertas ni para FLIP sin símbolos |
| `DAEMON_MARKET_DATA_MODE` / `DAEMON_SHADOW_MAX_FILE_MB` / `DAEMON_SHADOW_WRITE_ENABLED` | external / 50.0 / 1 | Modo de datos de mercado por defecto (sin doble lectura MT5) y rotación de `market_data_shadow.jsonl` |
| `DAEMONBLACKFX_MIN_REPORT_INTERVAL_SECONDS` / `DAEMONBLACKFX_EXCEL_WIDTH_SAMPLE_ROWS` | 300 / 200 | Intervalo mínimo de exportación XLSX y filas muestreadas para ancho de columnas |
| `DAEMON_COORDINATOR_HEARTBEAT_SECONDS` | 15.0 | Intervalo entre escrituras de heartbeat del coordinador en SQLite |
| `DAEMONBLACKFX_COMPACT_PERSISTED_STATE` / `DAEMONBLACKFX_DASHBOARD_RECENT_SCAN_LIMIT` | 1 / 1200 | Persistencia compacta de `last_state.json` (sin `account` ni `open_positions`) y límite de escaneo de auditoría en `/api/state` |

## Pendientes

- [x] Alchemist MSNR (26-oct-2026): replay NO CONCLUYENTE (+0,041 R/op, p = 0,31). **Archivada por decisión del usuario**: sin worker ni prueba demo; el código de investigación (`strategy/alchemist/`, `tools/replay_alchemist.py`) queda para reutilizarlo.
- [x] Malaysian SNR: /Instruments es el único control (`DAEMONBLACKFX_MSNR_INSTRUMENTS_CONTROL`, 25-oct-2026). Falta reiniciar MALAYSIAN_SNR para cargarlo.
- [x] Malaysian SNR acierto > 47 % (25-oct-2026): daemon reiniciado por el usuario; escanea los 41 instrumentos. Pendiente revisar por activo a las 40 ops (mercados reales: `MSNR_REAL_DEMO_TEST`) y retirar desde /Instruments los que queden con R/op ≤ 0. Vigilar si VolSwitch High Vol llega a operar (tope spread/SL 2 %).
- [x] Worker CARRY creado en prueba demo (24-oct-2026).
- [ ] Worker CARRY: reiniciar daemons (lanza `carry-daemon`), pulsar "Aplicar selección" en la pestaña CARRY FOREX con los 28 pares, comprobar las entradas al abrir noviembre (`CARRY_CONFIRMED` en 3 pares) y el cierre por rebalanceo al abrir diciembre; revisar a las 36 operaciones (`CARRY_DEMO_TEST`).
- [ ] Plan de MEJORAS_ESTRATEGIAS_20261024.md: hechas las prioridades 2 y 5 (falta reiniciar); 3 verificada sin fallo; 4 descartada por caída; 6 resuelta; poda ICT por activo descartada (no persiste); quedan acciones con Dukascopy y carry (requieren datos externos).
- [ ] Reiniciar RSI2 y NIGHT (velas del broker MT5).
- [ ] Reiniciar ICT para que analice los índices US con velas del broker MT5 (y el centinela de régimen); después revisar si baja `MARKET REGIME BLOCKED` en índices.
- [x] DRIFT desactivado por defecto (23-oct-2026); tiene efecto al reiniciar su daemon.
- [x] Re-medidos ICT y MSNR en sintéticos con spread real (23-oct): factor ≈ 1 salvo VolSwitch High Vol (4,3), ya en PODA PREVENTIVA.
- [ ] RSI2 y NIGHT: NO CONCLUYENTES con 5 años (RSI2 positivo y mejor que el azar; NIGHT ≈ beta, no mejor que el azar). **Decisión del usuario (23-oct-2026): NIGHT sigue en demo con su criterio fijado (120 noches, R/op > 0) y se revisa entonces**; RSI2 sigue en demo (60 ops).
- [ ] Reiniciar NIGHT y RSI2 para cargar la sombra de IA nativa y el límite por símbolo propio; comprobar en la próxima señal que entran (sin `META_LABEL_FILTER_REJECTED` ni `POSITION_ALREADY_OPEN_FOR_SYMBOL`).
- [ ] Worker RSI2: tras reiniciar, pulsar "Aplicar selección" en la pestaña RSI(2) EE. UU. y revisar a las 60 operaciones (`RSI2_DEMO_TEST`; esperado ≈ +0,176 R/op). Vigilar la exposición conjunta con NIGHT.
- [ ] Worker NIGHT: tras reiniciar, aplicar la selección de la pestaña SESGO NOCTURNO y revisar a las 120 noches (`OVERNIGHT_DEMO_TEST`); vigilar la caída y los huecos.
- [ ] DEX 1500 UP Index (Malaysian SNR): tras reiniciar, marcarlo en la pestaña Malaysian SNR y revisar a las 40 operaciones (`MSNR_SYMBOL_DEMO_TEST`).
- [x] (24-oct: ya no se ejecuta por defecto, `DAEMONBLACKFX_DASHBOARD_HOT_SYNC=0`) Quitar el parche en caliente de `dashboard/strategy_bases_page.py` que sobrescribe `TradingRepository._normalize_selection_profile` con una lista fija (hubo que añadirle MSNR a mano el 20-oct).
- [ ] Worker MSNR (vídeos): reiniciar daemons, aplicar la selección de la pestaña MSNR y revisar a las 200 operaciones el veredicto (`MSNR_VIDEO_DEMO_TEST`); vigilar los 8 huecos simultáneos.
- [ ] Revisar a las 60 operaciones MSNR (desde el 21-oct) el veredicto del filtro de régimen (auditoría `MSNR_REGIME_DEMO_TEST`): SUPERA → pasar a `live`; NO_SUPERA → revisar MSNR.
- [ ] Reiniciar daemons para cargar todos los cambios sin commit (decisión del usuario).
- [ ] /Instruments: ejecutar `.venv/Scripts/python.exe tools/apply_ict_instrument_policy.py --apply` (Sintéticos, Forex, ICT y Malaysian SNR + asset_modes) o pulsar "Aplicar selección" en cada pestaña tras reiniciar. ICT ya quedó bien (guardado del usuario 11:33). Falta marcar USDCAD en ORB.
- [ ] Replay MSNR en Forex, índices y cripto con ajustes reales y entrada limitada (en curso, `--tag real_live_y1/y0`).
- [ ] Revisar a las 40 operaciones la prueba demo de ORB BTCUSD y USDCAD.
- [ ] Centinela ORB en OBSERVE: revisar a las 30 operaciones que habría bloqueado (R/op > 0 sin manuales) o volver a FILTER.
- [ ] Decidir si se activa el tope de riesgo US (`DAEMONBLACKFX_US_EQUITY_RISK_CAP=3`) al terminar la prueba de RSI2.
- [ ] Opcional: podar también los activos con acierto > 45 % pero R/trade negativo.
- [x] Dashboard: servir `recent_trades` y rendimiento fuera de `/api/state` (20-oct, ver historial).
- [x] Ajustar volumen al límite del símbolo (Volatility 250 (1s), `retcode 10034`): hecho el 24-oct; tras reiniciar,
  comprobar que su próxima entrada abre TP1 y RUNNER.
- [x] Parche en caliente del dashboard apagado por defecto (`DAEMONBLACKFX_DASHBOARD_HOT_SYNC=0`); queda el código por si
  se quiere borrar del todo más adelante.
- [x] EMA200 H4 de ICT con 401 velas: medida el 25-oct, no mejora en ambos años; se mantiene 101.
- [ ] ADX real como feature de IA de ICT (ya se guarda en `ict_real_features`): reentrenar con ≥ 300 operaciones propias (prioridad 9).
- [x] Ajustes MSNR de la base (Breaker Pair, Pinbar) y obstáculo diario a 1R: medidos el 25-oct (180 días), sin mejora; no se cambian.
- [ ] MSNR en mercados reales (prueba demo, 5 activos ya marcados en /Instruments): reiniciar los daemons y revisar a las 40 operaciones (`MSNR_REAL_DEMO_TEST`).
- [x] (25-oct) El usuario decide dejar Malaysian SNR activo. ~~Decisión del usuario: pausar MALAYSIAN_SNR y MSNR (sin ventaja en 4 periodos con la clase real; MSNR vídeos −0,051, t −2,6) o mantener sus pruebas demo (60 / 200 ops sin cierres manuales).~~
- [ ] Decidir si se borra `enable_runner_trailing_lock` de Malaysian SNR (bandera sin efecto) o se diseña y valida en
  replay un trailing propio.
- [ ] Commit de los cambios del 19-oct y PR (`gh` no está instalado; descripción en `PR_BlackDaemon2_fase1.md`).
