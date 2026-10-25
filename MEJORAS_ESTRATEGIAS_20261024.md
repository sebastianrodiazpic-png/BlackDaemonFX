# BlackDaemonFX — Auditoría completa de estrategias y mercados (24-oct-2026)

Todas las cifras son en **R por operación** (1R = el riesgo de la operación, el 1 % de la cuenta repartido en dos
entradas).

Fuentes:
- **Demo**: base viva leída en solo lectura, 1.211 operaciones del 4-sep al 23-oct-2026.
- **Replays fieles** del proyecto: velas cerradas, spread y swap reales, gestión del bot.
- **Logs** de los 22 workers.

Un resultado solo cuenta como evidencia si es positivo en todos los periodos, mejor que entrar al azar con la misma
gestión y significativo una vez agrupado por día.

---

## 1. Resumen ejecutivo

**La cuenta demo pierde** (−0,034 R/op en octubre). Las causas, por orden de peso:

1. **Hay workers operando mercados sin ventaja demostrada en ningún replay**: ICT en mercados reales, Forex, GOLD,
   ORB e IDX_OPEN. Desde septiembre suman ≈ −1.900 USD de las pérdidas en demo.
2. **Las señales que el bot genera en vivo y que el replay no genera** son las que pierden en ICT sintéticos: 23
   operaciones a −0,27 R/op. Cuando la señal coincide con la del replay, la demo gana +0,056 R/op.
3. **Fallos de datos y de coste que ya se corrigieron en esta sesión**: velas de Deriv distintas a las del broker en
   los índices US, spread de las velas 12 veces menor que el real en Drift Switch, filtro de IA bloqueando a NIGHT y
   RSI2, choque de límites entre NIGHT y RSI2, y señales de DRIFT perdidas sin reintento.
4. **Los cierres manuales desde el móvil** (14 % de las piernas de octubre, +0,24 R de media) maquillan la demo y
   rompen los criterios de las pruebas: con solo la gestión del bot, ICT v2 da −0,197 en vez de −0,062.

**Lo que sí funciona, con evidencia**:
- **RSI(2) diario de Connors**: positivo en 2021-26 en los índices US (+0,150) y confirmado ahora en **ETF**
  (+0,096, supera el criterio pre-registrado).
- **ICT en sintéticos en el replay** (+0,05 R/op en la cartera activa, con spread real).
- **Los workers VOLATILITY_3, BOOM y CRASH en vivo** (+0,4 a +0,66 R/op desde el 16-oct; muestras pequeñas).

**Mejora potencial estimada**:
- Desactivar lo que no tiene ventaja: ≈ +0,1 R/op en la cartera.
- Corregir la fidelidad de ICT: hasta +0,25 R/op en sus operaciones exclusivas de la demo.
- Añadir ETF a RSI2: unas 220 operaciones más al año a +0,10 R/op.

---

## 2. Problemas transversales (afectan a varias estrategias)

| # | Problema | Evidencia | Influencia | Estado |
|---|---|---|---|---|
| T1 | **Cierres manuales desde el móvil** | 165 piernas en octubre, +0,24 R de media. ICT v2: −0,062 total frente a −0,197 automático. MSNR vídeos: +0,041 frente a −0,221 | Las pruebas demo (60/120/200 ops) deciden con datos contaminados: pueden aprobar algo que pierde o al revés | **Pendiente**: no intervenir a mano durante las pruebas demo, o excluir esas piernas del criterio |
| T2 | **Velas de Deriv ≠ broker** en los índices US (modo shadow) | Deriv sirve otra serie: 56 % de velas H1 coincidentes, desfase del 24–40 % de una vela H1. RSI2 perdió la señal de US Tech 100 del 22-oct | Las estrategias validadas con MT5 operaban otra serie de precios | **Corregido** en RSI2, NIGHT, ICT y el centinela de régimen. Oro ≈ igual; US Oil ya usaba MT5; sintéticos ≈ iguales |
| T3 | **El spread de las velas MT5 es el mínimo del periodo** | En Drift Switch el real es ~12× mayor. El resto de sintéticos usa spread fijo (factor ≈ 1) | DRIFT pasaba de +0,083 a −0,030 | **Corregido**: DRIFT desactivado y VolSwitch High Vol podado. Todo replay futuro debe usar el spread de ticks |
| T4 | **La IA (meta-label) no predice en vivo** | ICT v2 por terciles de probabilidad: baja −0,205, media −0,091, alta −0,264. Rechazó a NIGHT con un modelo de otras estrategias | Usarla como filtro quitaría operaciones al azar o buenas | **Corregido**: en sombra para las estrategias nativas. Mantener en sombra hasta reentrenar por estrategia con ≥ 300 operaciones propias |
| T5 | **Señales vivas que el replay no genera (ICT)** | 23 operaciones en símbolos activos sin pareja en el replay de los mismos días: −0,272 R/op. Las 47 emparejadas: +0,056 (replay +0,023) | Es la principal fuga de ICT sintéticos. Sin ellas, ICT v2 estaría en positivo | **Pendiente**: auditoría de fidelidad señal a señal (estado del límite virtual, ventanas de vela, velas en formación) |
| T6 | **Workers evaluando instrumentos podados** | forex_3: el 99 % de sus evaluaciones son activos podados; MSNR evalúa mercados reales que rechaza (336); varios ICT evalúan excluidos | Ciclos perdidos y más bloqueos de ciclo por símbolo entre workers | **Pendiente**: limpiar las selecciones (aplicar la política en /Instruments) y apagar los workers sin instrumentos |
| T7 | **Concentración y correlación** | RSI2 dispara a la vez en 5 índices (y en ETF casi idénticos: SPY = IVV = VOO = VTI); NIGHT también compra US | Un mal día de EE. UU. golpea varias posiciones a la vez | **Pendiente**: tope de riesgo por "factor" (p. ej. ≤ 3 % en renta variable US al mismo tiempo) y no duplicar ETF equivalentes |

---

## 3. Estrategia por estrategia

### 3.1 ICT en sintéticos (STEP, JUMP, VOLATILITY 1-4, BOOM, CRASH)
- **Replay** (último año, spread real): cartera activa **+0,051 R/op** (7.149 ops).
  - Por activo siguen bien: Crash 900, Boom 900, Volatility 100/10/15, Boom 500, Crash 500, Step 200/400/500 y
    Volatility 50 (1s).
- **Demo desde el 16-oct (automático)**:

  | Worker | Piernas | R/op |
  |---|---:|---:|
  | VOLATILITY_3 | 25 | +0,65 |
  | CRASH | 10 | +0,44 |
  | BOOM | 18 | +0,05 |
  | STEP | 31 | −0,09 |
  | VOLATILITY_2 | 22 | −0,10 |
  | VOLATILITY_1 | 20 | −0,16 |
  | **JUMP** | 38 | **−0,53** |

- **Las perdedoras casi nunca estuvieron en ganancia** (MFE mediana 0,21 R; ninguna llegó a 0,8 R antes del stop). El
  problema es la **entrada**, no la gestión: ni el BE ni un TP más cercano lo arreglan.
- **Mejoras**:
  1. **T5, la principal**: hacer que en vivo solo se abran las señales que el replay reproduce. Hoy las
     operaciones exclusivas de la demo restan −0,27 R/op.
  2. **JUMP**: en el replay, Jump 10 (+0,006), Jump 50 (+0,035) y Jump 75 (+0,019) están casi a cero, y en vivo
     JUMP es el peor worker. Si tras la corrección de T5 sigue negativo, pasar Jump 10/50/75 a prueba demo con
     criterio (40 ops) o podarlos.
  3. Mantener la IA en sombra (T4) y el bloqueo fantasma por spread, que sigue siendo válido (+0,047 / +0,022).

### 3.2 ICT en mercados reales (worker ICT: oro, índices US, US Oil)
- **Replay**: sin ventaja demostrada (≈ 0).
- **Demo**: −0,197 R/op automático en 121 piernas desde el 16-oct. Ojo: hasta el 18-oct ese worker operaba también
  sintéticos excluidos (Jump 25, Boom 300, XAGUSDmicro). Ya está corregido, pero ensucia sus cifras.
- Los índices se analizaban con la serie de Deriv (T2, corregido el 23-oct).
- **Mejora**: **apagar el worker ICT en mercados reales**, o dejarlo en prueba demo con criterio fijado (40 ops,
  R/op > 0). No hay ningún replay que lo respalde y en vivo pierde. Liberaría huecos para las estrategias que sí
  tienen ventaja.

### 3.3 Forex (workers FOREX_1-4, ICT en Forex)
- **Investigado a fondo y sin ventaja**: ICT, Donchian diario, rupturas de sesión (S1–S4), momentum diario,
  reversión asiática, retroceso en tendencia, entrada limitada y MSNR. Todo pierde con costes reales.
- **Demo**: −0,37 / −0,31 / −0,12 / +0,12 R/op (muestras pequeñas). Las versiones antiguas, −0,64 / −0,71.
- **Mejora**: **desactivar los 4 workers Forex** (forex_3 ya no opera nada: el 99 % de sus activos están podados).
  La única vía seria pendiente es el **carry** con histórico de tipos de interés externo (sección 5).

### 3.4 Malaysian SNR
- **Replay** (sintéticos, spread real): **+0,023 R/op** sin filtro de régimen y +0,069 con el filtro (en prueba demo
  desde el 21-oct).
- **Demo**: −0,07 R/op automático en todo el periodo; −0,204 desde el 16-oct (33 piernas, poca muestra).
- **Activos con buen replay**: Volatility 50 (1s), Jump 75, Vol over Boom 550, Volatility 25, Volatility 250 (1s),
  Step 500 y Volatility 150 (1s).
- **Mejora**:
  - Dejar correr la prueba del filtro de régimen (60 ops) **sin cierres manuales** (T1).
  - Si no supera, restringir el universo a los 7 activos positivos (exploratorio) en nueva prueba demo.

### 3.5 MSNR vídeos (worker MSNR, escenario H4→H1)
- **Replay**: +0,017 R/op, una ventaja muy pequeña.
- **Demo**: **+0,041 total, pero −0,221 automático**. 15 de 36 piernas se cerraron a mano.
- **Mejora**:
  - Sin la mano del usuario pierde. Es la candidata natural a retirar si la prueba de 200 ops confirma R/op ≤ 0.
  - Mientras tanto, que no evalúe mercados reales (T6: 336 evaluaciones inútiles).

### 3.6 ORB (XAUUSD SWEEP; BTC y USDCAD en prueba)
- **Replay**: XAUUSD SWEEP ≈ +0,2 R/op con n ≈ 95, no concluyente.
- **Demo**: −0,352 R/op en 23 piernas.
- El 31 % de sus evaluaciones las bloquea el centinela de régimen y el 18 % el bloqueo de ciclo con GOLD e ICT por el
  oro.
- **Mejora**:
  - Mantener la prueba con criterio (40 ops).
  - Que el oro no se dispute entre tres workers (ORB, GOLD, ICT): asignarlo a uno.

### 3.7 GOLD (cuartos y niveles psicológicos)
- **Demo**: −0,466 R/op (22 piernas); en el replay de cuartos, TP2 no concluyente.
- **Mejora**: apagarlo o dejarlo en prueba con criterio, por el mismo motivo que ICT en mercados reales.

### 3.8 RSI2 (Connors diario) — la estrategia con más respaldo
- **Evidencia**:
  - Índices US 2021-26: **+0,150 R/op** (positivo en 2021-22, 2023-24 y 2025-hoy; p azar 0,001).
  - **ETF 2023-26: +0,096 R/op, SUPERA** el pre-registro (668 ops, t por día 2,05, p azar 0,022).
  - Mejores ETF (exploratorio): GLD +0,29, ARKK +0,23, DIA +0,18.
- **Corregido hoy**: velas del broker (T2), IA en sombra, límite por símbolo propio, reintento y huecos reservados.
- **Mejoras**:
  1. **Añadir ETF al worker RSI2** en prueba demo. Pasaría de unas 70 a unas 290 señales al año, con lo que la
     prueba de 60 ops llegaría en ≈ 3 meses en vez de 10.
  2. **No duplicar ETF equivalentes**: SPY, IVV, VOO y VTI son el mismo índice. Elegir uno, o tratarlos como un solo
     "factor" con tope de riesgo (T7).
  3. Acciones individuales: el broker solo tiene 14 meses. Validar con historia de Dukascopy antes de nada
     (sección 5).

### 3.9 NIGHT (sesgo nocturno)
- 5 años de Dukascopy: +0,022 / +0,030 R por noche, pero **no mejora a mantener comprado el índice a horas al azar**.
  Lo que gana es beta.
- **Corregido hoy**: velas del broker, IA en sombra y límites.
- **Mejora**: prueba de 120 noches (decisión del usuario). En la revisión, compararla con mantener el índice comprado
  sin más; si no lo supera, retirarla o sustituirla por RSI2, que sí es mejor que el azar.

### 3.10 DRIFT (ruptura en Drift Switch)
- **Desactivado**: con el spread real pierde (−0,030) y el tope del 2 % no le deja entrar. Nada más que hacer.

### 3.11 FLIP / IDX_OPEN / VOLATILITY_3
- FLIP: +0,85 R/op (9 piernas). VOLATILITY_3: +0,22 en todo el periodo y +0,65 desde el 16-oct. IDX_OPEN: −0,33
  (6). Muestras muy pequeñas.
- **Mejora**: nada sin evidencia. Vigilar VOLATILITY_3 y FLIP como posibles motores si siguen positivos con más
  operaciones.

---

## 4. Mercado por mercado

| Mercado | Qué se probó | Conclusión | Acción |
|---|---|---|---|
| Sintéticos Volatility/Step/Jump/Boom/Crash | ICT, MSNR, 7 estrategias de indicadores, diagnóstico de aleatoriedad | ICT con límite + tope de spread da una ventaja pequeña. Step = paseo aleatorio para los indicadores | Mantener ICT y corregir T5 |
| Drift Switch | Ruptura tras compresión | Ventaja falsa: spread real 12× | Desactivado |
| DEX / Crash-Boom / Hybrid / Trek / Range Break | Indicadores; MSNR en DEX 1500 UP | DEX 1500 UP en MSNR (+0,30 R/op en replay) | Prueba demo en curso (40 ops) |
| Forex (27 pares) | 9 enfoques | Sin ventaja | Desactivar workers Forex; estudiar carry |
| Índices US | RSI2, NIGHT, ORB, ICT, indicadores | **RSI2 sí**; NIGHT = beta; resto no | RSI2 en demo |
| Índices Europa / Asia | Indicadores diarios e intradía | Sin ventaja (RSI2 en Europa −0,09) | Nada |
| Metales (oro, plata) | ICT, ORB, GOLD, RSI2, Supertrend, ratio oro/plata, tipos reales | Nada supera; el oro sube por deriva (beta). RSI2 en el **ETF GLD** +0,29 (exploratorio) | Asignar el oro a un solo worker; GLD dentro de RSI2-ETF |
| Energía (WTI, Brent) | Indicadores, momentum, COT | Sin ventaja; la tendencia H4 pierde con fuerza | Nada |
| Softs / NGAS / platino / cobre | Coste prohibitivo (spread > 10 % del ATR) | No operables | Nada |
| **ETF (31)** | **RSI2 (nuevo)** | **SUPERA (+0,096)** | **Añadir a RSI2 en demo** |
| **Acciones (440)** | Historia del broker de 14 meses | No validable | Descargar historia de Dukascopy y probar RSI2 |
| **Cripto (37)** | **RSI2 y ruptura Donchian (nuevo)** | No superan (RSI2 −0,10; ruptura −0,08). BTC en ruptura +0,18, exploratorio. El swap del 15–20 % anual penaliza mantener posiciones | Nada; como mucho, ruptura solo en BTC en prueba futura |
| Cestas, VIX, DXY, Snap, Exponential | No analizados (pocos símbolos, sin tesis) | — | Baja prioridad |

---

## 5. Plan priorizado

| Prioridad | Acción | Efecto esperado | Riesgo | Coste |
|---|---|---|---|---|
| 1 | **No cerrar a mano durante las pruebas demo** (o excluir esas piernas del criterio) | Criterios fiables; se ve la verdad de cada estrategia | Ninguno | Disciplina |
| 2 | **Desactivar Forex 1-4, ICT en mercados reales, GOLD e IDX_OPEN** (o pasarlos a prueba con criterio) | Evita ≈ −0,2/−0,4 R/op en esos workers (≈ −1.900 USD desde septiembre) y libera huecos y bloqueos de ciclo | Perder una ventaja futura que hoy no está demostrada | Interruptores existentes |
| 3 | **Auditoría de fidelidad de ICT (T5)**: abrir solo las señales que reproduce el replay | Hasta +0,25 R/op en ≈ 30 % de las operaciones ICT → ICT sintéticos de negativo a positivo | Menos operaciones | Investigación y código |
| 4 | **RSI2 + ETF** en prueba demo, sin duplicar ETF equivalentes y con tope por factor | +0,10 R/op en ≈ 220 operaciones al año, y la prueba se acelera | Más exposición a renta variable US | Código pequeño |
| 5 | **Limpiar selecciones / workers vacíos (T6)** | Menos bloqueos de ciclo; ciclos más rápidos | Ninguno | Aplicar la política en /Instruments |
| 6 | **Asignar el oro a un solo worker** | Fin de la competencia ORB/GOLD/ICT por el símbolo | — | Configuración |
| 7 | **Acciones individuales**: descargar 5 años de Dukascopy (aprobación) y probar RSI2 | Ampliar la única ventaja demostrada | Correlación con los índices | Descarga + replay |
| 8 | **Carry en Forex** con histórico de tipos de bancos centrales | Única ventaja documentada en Forex sin indicadores | Crashes de carry; excepción al contrato | Datos externos + replay |
| 9 | Reentrenar la IA **por estrategia** cuando haya ≥ 300 operaciones propias, y solo activarla si el tercil alto gana y el bajo pierde en validación fuera de muestra | Filtro real en vez de ruido | Sobreajuste | Más adelante |

---

## 6. Herramientas y datos de esta auditoría
- Demo: `storage/analysis/demo_trades_audit.pkl`, con MFE/MAE, IA, escenario y worker de cada pierna.
- Fidelidad de ICT: replay de 12 días `storage/analysis/ict_limit_entry_signals_gap_v2.csv`, emparejado con la demo.
- ETF y cripto: `tools/research_etf_crypto.py` → `storage/analysis/etf_crypto_report.md`.
- Anteriores: `tools/research_real_spread_recheck.py`, `tools/research_us_index_longrun.py`,
  `tools/research_commodity_longrun.py`, `tools/research_forex_indicators.py`, `tools/research_index_indicators.py`,
  `tools/research_step_*`, `tools/research_synthetic_indicators.py` y `REGISTRO_CAMBIOS_ESTRATEGIA.md` (Hallazgos).

---

## 7. Estado tras aplicar y verificar el plan (24-oct-2026, continuación)

| Prioridad | Resultado |
|---|---|
| 2 · Apagar los workers sin ventaja | **Hecho**: `DAEMONBLACKFX_DISABLED_WORKERS` = Forex 1-4, ICT (mercados reales), GOLD e IDX_OPEN. Falta reiniciar |
| 3 · Fidelidad de ICT | **Verificada sin fallo** tras el reinicio del 22-oct: 23 de 27 operaciones emparejadas con el replay. La fuga de −0,27 era anterior a la Fase 1 |
| 4 · RSI2 + ETF | **Descartada por datos**: los ETF no duplicados aportan +0,057 y cuadruplican la caída máxima (−4,1 → −17,7 R) |
| 5 · Selecciones limpias | **Hecho**: `DAEMONBLACKFX_POLICY_CYCLE_FILTER`; ningún worker escanea instrumentos en PODA PREVENTIVA |
| 6 · Oro en un solo worker | **Resuelto**: con GOLD e ICT apagados, el oro solo lo opera ORB |
| Nueva · Cambio de mes en índices US | **Descartada**: no mejora al azar (+0,016 frente a +0,034) |
| Nueva · Poda de ICT por activo | **Descartada**: el R por activo no persiste entre años (correlación −0,25). La ventaja de ICT es de cartera: +0,024 / +0,032 R/op en dos años |
| Nueva · Validez de la orden límite de ICT | **Se mantiene en 8 velas** (la de mayor R total en ambos años) |
| 7 · Acciones (RSI2) | Pendiente: requiere aprobar la descarga de 5 años de Dukascopy |
| 8 · Carry en Forex | Pendiente: requiere histórico de tipos de interés externo |

**Cartera con evidencia de que es rentable**:
- **ICT sintéticos**: +0,02 a +0,05 R/op, robusto en dos años.
- **RSI2 en índices US**: +0,15 R/op en 5 años.
- **Malaysian SNR con filtro de régimen**: +0,069 en el replay, en prueba demo.
- **NIGHT**: en prueba; es beta.

El resto está apagado, desactivado o en prueba con criterio fijado. **Lo que falta para confirmarlo en demo**: reiniciar
los daemons y no cerrar posiciones a mano durante las pruebas.
