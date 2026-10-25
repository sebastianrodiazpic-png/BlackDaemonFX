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

## Estado actual (19-oct-2026, tras los cambios de esta sesión — pendiente de reiniciar daemons)

| Área | Configuración vigente en código |
|---|---|
| Riesgo | 1 % por operación en 2 patas (sintéticos y MSNR también al 1 %) |
| Operaciones simultáneas | 8 (16 posiciones físicas), común a todos los workers |
| ICT sintéticos | Solo velas cerradas · entrada **limitada virtual** (8 velas M15) · tope spread/SL 2 % · IA en **sombra** · 28 activos (podados: excluidos Fase 1 + acierto ≤ 45 %) |
| ICT Forex | Tope spread/SL 5 % · entrada a mercado · sin ventaja demostrada |
| ICT metales | Tope spread/SL 2 % (solo ICT) |
| ICT cripto | **Desactivado** |
| ORB | SWEEP en XAUUSD (validado) + BTCUSD y USDCAD en **prueba demo** (corte automático tras 40 ops si R/op ≤ 0) · runner TP3/TP4 |
| MSNR | Solo sintéticos (30 activos), sin C2 ni lista de 23, runner TP3/TP4. **Ojo**: los ajustes de MSNR en la base (`asset_modes`) tienen activos en `off` que mandan sobre el código |
| Forex workers | Tope spread/SL 5 % (antes 15 %) |
| Workers desactivados (24-oct) | Forex 1-4, ICT (mercados reales), GOLD e IDX_OPEN sin entradas nuevas (`DAEMONBLACKFX_DISABLED_WORKERS`); el monitor gestiona lo abierto |
| RSI2 (22-oct) | RSI(2) diario de Connors en los 5 índices US · **prueba demo** (60 ops, R/op > 0) · 1 % en dos entradas (TP1 1R + runner 2R con BE), stop 2 ATR D1, la regla cierre > SMA5 o 10 días cierra lo que quede · replay +0,177 R/op (no concluyente) |
| CARRY (24-oct) | Carry Forex G10 con swap real de MT5 · top 3 pares, rebalanceo mensual, stop 3 ATR D1 · 1 % en dos entradas (TP1 1R + runner TP2 2R con BE y extensión TP3/TP4) · **prueba demo** (36 ops, R/op > 0) · exento del cierre forzado de Forex · falta reiniciar |
| Ejecución y dashboard (24-oct, auditoría de código) | `volume_limit` repartido entre piernas · límite ICT de un solo uso · dashboard rechaza peticiones de otras webs · sin parche en caliente · falta reiniciar |
| DRIFT (21-oct) | **DESACTIVADO** (23-oct): sin ventaja con el spread real de ticks (−0,030 R/op); `DAEMONBLACKFX_DRIFT=off` por defecto |

Rendimiento esperado (replay fiel, no garantizado): ICT sintéticos con límite + tope 2 % ≈ **+0,03/+0,04 R/trade**, acierto ~52 %.
MSNR sintéticos ≈ 0 R/trade. ORB XAUUSD SWEEP ≈ +0,2 R/trade (n≈95, no concluyente). Demo real hasta el 18-oct: −0,088 R/trade.

---

## Historial de cambios (más reciente primero)

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

## Pendientes

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
- [ ] Opcional: podar también los activos con acierto > 45 % pero R/trade negativo.
- [x] Dashboard: servir `recent_trades` y rendimiento fuera de `/api/state` (20-oct, ver historial).
- [x] Ajustar volumen al límite del símbolo (Volatility 250 (1s), `retcode 10034`): hecho el 24-oct; tras reiniciar,
  comprobar que su próxima entrada abre TP1 y RUNNER.
- [x] Parche en caliente del dashboard apagado por defecto (`DAEMONBLACKFX_DASHBOARD_HOT_SYNC=0`); queda el código por si
  se quiere borrar del todo más adelante.
- [ ] Replay antes de decidir: EMA200 H4 de ICT con ≥ 400 velas; ADX real como feature de IA de ICT (prioridad 9).
- [ ] Decidir si se borra `enable_runner_trailing_lock` de Malaysian SNR (bandera sin efecto) o se diseña y valida en
  replay un trailing propio.
- [ ] Commit de los cambios del 19-oct y PR (`gh` no está instalado; descripción en `PR_BlackDaemon2_fase1.md`).
