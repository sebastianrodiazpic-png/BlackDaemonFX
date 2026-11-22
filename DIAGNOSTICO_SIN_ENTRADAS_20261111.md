# Diagnóstico: por qué no hay entradas desde el 10-nov-2026 14:01 (-03)

Fecha: 2026-11-11 08:15 (-03) · Solo análisis: no se tocó código, configuración, base de datos ni daemons.

Fuentes: `graphify-out/graph.json` (10.687 nodos, generado 11-nov 03:15), `storage/logs/bots/*.log(.old)`,
`storage/exports/deriv_demo_trading_report.xlsx` (export de la base viva de las 08:01: 1.707 patas, 2.000 eventos
de auditoría), `storage/analysis/*`, `REGISTRO_CAMBIOS_ESTRATEGIA.md` y el código. La base viva de
`%LOCALAPPDATA%\BlackDaemonFx` no se pudo abrir (carpeta fuera de la sesión); se usó su export.

## 1. Hechos

| Dato | Valor |
|---|---|
| Última orden abierta | 10-nov 17:01 UTC (Step, worker STEP) |
| Órdenes por día (logs) | 20–25/oct ≈ 25 · 9-nov: 9 · 10-nov: 8 · 11-nov: 0 |
| Reinicios del daemon desde la última orden | al menos 10 (el último 11-nov 07:44 -03) |
| Resultado demo acumulado | −4.970 USD en 1.707 patas · saldo 4.757 USD |
| Por mes (R por pata) | sep −0,27 · oct −0,05 · nov +0,07 (184 patas, 55 % aciertos) |

## 2. Embudo desde la última orden (señales válidas que no se abrieron)

ICT en sintéticos (VOLATILITY_1, BOOM, CRASH, JUMP, STEP), 9→11-nov: 118 señales llegaron a tocar su límite
virtual y solo 10 se abrieron (8,5 %). Las otras:

| Motivo | Nº | Naturaleza |
|---|---|---|
| `SYNTHETIC_SPREAD_RISK_RATIO_EXCEEDED` (spread 3–13 % del SL, tope 2,5 %) | 31 | Stops demasiado ajustados (micro-stops) |
| `HUMAN_CRITERIA_FILTER_REJECTED` (régimen tóxico, contratendencia H1, score) | 26 | Filtro discrecional |
| `BLOCKED_SYMBOL_CYCLE` | 12 | Ciclo bloqueado antes de evaluar: el límite sigue pendiente (no es un rechazo; ver corrección al final) |
| `TRIPARTITE_CONFLUENCE_FILTER_REJECTED` (IA no disponible + score < umbral) | 11 | Filtro discrecional |
| `NI_LA_DIVISION_NI_LA_ENTRADA_UNICA_RESPETAN_EL_RIESGO_MAXIMO` | 9 | Lote mínimo vs. 0,5 % de un saldo de 4.757 |
| `JUMP_REQUIERE_EJECUCION_DIVIDIDA_TP1_RUNNER` | 3 | Ídem (no se puede partir en 2 patas) |

Además, cada señal no abierta deja el símbolo ocupado con una operación virtual (`ICT_TRIGGER_LOCK`,
107 bloqueos, mediana 28 min, 70 horas-símbolo).

MALAYSIAN_SNR sintéticos (10-nov 17:01 → 11-nov 08:00):

| Motivo | Nº ciclos | Símbolos |
|---|---|---|
| `MSNR_OBSERVATION_ONLY` (variantes en modo sombra) | 781 | 23 |
| `JUMP_REQUIERE_EJECUCION_DIVIDIDA` / confirmaciones reforzadas Jump | 295 | Jump 50/75 |
| `CRITERIO_HUMANO_VETO` (contratendencia H1, régimen tóxico) | 145 | 6 |
| `MSNR_STEP_EXECUTION_ADX_BELOW_MINIMUM` | 84 | Step 200/400 |
| `MSNR_REGIME_BLOCKS_ADX_25_40` | 67 | Jump 50, Step 200, Vol 100 (1s) |
| `ENTRY_PRICE_DRIFT_TOO_LARGE` (> 0,5 R) | 65 | 3 |

Mercados reales: FOREX_SNR / COMMODITIES_SNR / INDICESB_SNR estuvieron en error hasta el hotfix de las 00:13
(`ImportError`, luego `MSNR_SETTINGS_UNAVAILABLE`); ahora analizan pero sin ninguna señal válida todavía
(esperas normales: `D1_BIAS_CONFLICT`, `LEVEL_CONSUMED`, `WAITING_FIRST_RETEST`). ICT y FOREX_1 perdieron
9.494 y 2.494 ciclos por `BLOCKED_SYMBOL_CYCLE` hasta las 02:38 UTC y 1.991 por el error
`in_asian_session_jpy_aud` (10-nov 19:44–20:59 UTC); ambos ya no aparecen. Hoy están fuera de killzone.

## 3. Causas

1. **Contradicción de filtros en Step (MSNR)**: la ejecución exige ADX ≥ 25 (`step_min_adx` por defecto 25 en
   `runtime_settings.py`; en `config.py` es 12) y el filtro de régimen bloquea 25 < ADX ≤ 40
   (`live_trading_engine.py` L7574–7607 y L8715–8735). Solo pasa ADX > 40. Hoy Step Index 200 fue aprobado por
   Criterio Humano (80–100) y Confluencia Tripartita y bloqueado 20 veces por esto.
2. **Filtros apilados sin validar con replay real**: Criterio Humano, Centinela de régimen y Confluencia
   Tripartita rechazan ~1/3 de las señales ICT ya disparadas. El pilar de IA no aporta: P(Win) = 55,0 % fijo
   (modelo MSNR sin entrenar: `MSNR_REQUIRES_CANONICAL_PURGED_TRAINING`).
3. **Stops ajustados contra spread**: el 26 % de las señales ICT disparadas tienen spread de 3–13 % del SL.
   El tope es correcto (ese coste se come el margen); el problema está en la construcción del stop.
4. **Saldo demo en 4.757 USD**: con 0,5 % por pata (≈ 24 USD) el lote mínimo ya no cabe en varios símbolos.
5. **Inestabilidad operativa**: al menos 10 reinicios en 18 h y tres bugs introducidos el 10-nov (ya corregidos).
6. **Variantes MSNR en sombra** (`breaker_pair`, `av_entry`, `role_flip`, `qm_extended`, `gap`,
   `macro_structure`, `h4_neutral_fallback`): por diseño no operan; son el mayor caudal de señales sin usar.
7. **TREND_PULLBACK** está en `DAEMONBLACKFX_DISABLED_WORKERS` por defecto (último log 1-nov) aunque
   `/Strategy-bases` lo muestra activo. En demo: −19 R, 37 % aciertos en octubre.

## 4. La base de evidencia de /Strategy-bases no es un replay

Los ficheros que alimentan `/Strategy-bases` y el "Estado actual" del registro no ejecutan la estrategia sobre
velas; calculan cifras con fórmulas:

- `scratch/build_perfect_strategy_bases_replay.py` L98–130: `wr_boost` fijo (+2,1/+1,1/+6,5…), `trades_boost_pct`
  fijo, ganador medio 1,55 R. En el CSV, +3,2 pp exactos en 38 filas y +1,8 pp en 73.
- `tools/replay_msnr_5y_real_markets_audit.py` L80–128: `target_5y` y `target_wr` escritos a mano por activo y
  `np.random.RandomState(42)` para las "entradas descartadas por spread". De ahí salen los 12.445 trades y
  +5.953 R con los que se crearon FOREX_SNR, COMMODITIES_SNR e INDICESB_SNR.
- `tools/replay_msnr_5y_synthetics_audit.py` L39–83: multiplicadores aleatorios de trades (×1,9–2,25).
- `tools/run_multistrategy_5y_replay.py` L237–330: copia `n_proyectado` / `wr_proyectado` de CSV de simulación.
- `tools/replay_tripartite_confluence_5y.py` L262–268: `trades × 0,75`, `R × 1,3`.

Solo hay velas locales de 11 símbolos (`data/historical`, `data/forex_historical`). El único replay que sí
instancia la estrategia es `tools/replay_ict_5y_audit.py` (26-oct), y los comentarios del propio motor citan su
resultado real: +0,02 a +0,05 R por trade en ICT sintéticos, no +0,3 R.

Consecuencia: la demo (−0,05 R/pata en octubre, +0,07 en noviembre) es coherente con los replays reales y no
con las tablas de `/Strategy-bases` (57,6 % aciertos, +2.884 R).

## 5. Acciones propuestas (ninguna aplicada)

Sin coste de expectativa:
1. Step en MSNR: unificar el mínimo de ADX y eximir a Step de la banda 25–40, o fijar una sola regla.
2. Que `BLOCKED_SYMBOL_CYCLE` no deje operación virtual (no es una operación que el replay tome).
3. Congelar reinicios y cambios de código durante la sesión; cambios solo con tests y fuera de killzones.
4. Reponer el saldo demo o subir el riesgo mínimo viable para que el lote mínimo quepa en 2 patas.

Requieren replay real antes de activarse:
5. Criterio Humano, Centinela y Tripartita a modo observación con registro contrafactual 2 semanas, o medirlos
   con `tools/replay_ict_5y_audit.py`; conservar solo los que mejoren R/trade en ambas mitades.
6. Suelo de SL ligado al spread (SL ≥ 40 × spread) en lugar de descartar la señal.
7. Promover variantes MSNR en sombra una a una según su resultado a 24 h ya registrado en la base.
8. Rehacer `/Strategy-bases` solo con replays que ejecuten la clase real; marcar el resto como proyección.

## Corrección (11-nov 08:50)

- Los 12 casos de `BLOCKED_SYMBOL_CYCLE` del embudo ICT no son señales rechazadas: `symbol_cycle_lock` corta antes
  de analizar, el límite virtual sigue pendiente y se reintenta en el ciclo siguiente. Tampoco crean bloqueos
  virtuales nuevos; lo que se veía en los logs era el mismo bloqueo intercalado con ciclos bloqueados. La acción 2
  de la sección 5 tiene por tanto un efecto pequeño.
- Step en MSNR: la demo confirma que el tramo ADX (25, 40] es el perdedor (26 patas, −12,2 R), así que la
  contradicción se resolvió bajando el mínimo de Step y manteniendo ese tramo cerrado.
- Cambios aplicados: ver la entrada del 11-nov en `REGISTRO_CAMBIOS_ESTRATEGIA.md`.
