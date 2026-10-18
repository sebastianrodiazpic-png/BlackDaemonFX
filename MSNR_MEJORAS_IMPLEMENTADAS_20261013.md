# Implementación de Mejoras Clave: Malaysian SNR (Maximización de Trades y WinRate)

**Fecha:** 13 de Octubre de 2026  
**Estrategia:** Malaysian SNR Institucional (`msnr-v2.9-video-evidence`)  
**Estado:** ✅ Implementado, Validado con Suite de Pruebas (66/66 Tests Aprobados) y Sincronizado en SQLite.

---

## 1. Resumen de Mejoras Implementadas

Se han codificado e integrado fielmente en el motor causal del bot los 5 puntos clave identificados en la auditoría técnica y lecciones institucionales de Malaysian SNR (Cikgu Mansor, RTM y videos de referencia):

| # | Mejora Implementada | Módulos Modificados | Beneficio Cuantitativo Directo |
|---|---------------------|---------------------|--------------------------------|
| **1** | **Módulo "Fakeout Trap" / Liquidity Sweep** | [`strategy/malaysian_snr/video_rules.py`](file:///c:/TradingBoot/smc_synthetic_bot/strategy/malaysian_snr/video_rules.py)<br>[`strategy/malaysian_snr/validation.py`](file:///c:/TradingBoot/smc_synthetic_bot/strategy/malaysian_snr/validation.py) | **+Trades & +WinRate:** Permite capturar entradas cuando una mecha en M15 barre liquidez minorista más allá del nivel (hasta 0.60 ATR) y absorbe con cierre interno ($\ge 50\%$ mecha de rechazo). Deja de descartar estas trampas de alta probabilidad. |
| **2** | **Quasimodo de Continuación (QMC)** | [`strategy/malaysian_snr/validation.py`](file:///c:/TradingBoot/smc_synthetic_bot/strategy/malaysian_snr/validation.py)<br>[`strategy/malaysian_snr/malaysian_snr_strategy.py`](file:///c:/TradingBoot/smc_synthetic_bot/strategy/malaysian_snr/malaysian_snr_strategy.py) | **+Trades:** Genera candidatos de continuación de tendencia (`ESC_3_QMC`) aprovechando el retest del Hombro Izquierdo (Left Shoulder) tras una ruptura de estructura (BOS) con causalidad estricta. |
| **3** | **Stop Loss Micro-Estructural M15** | [`strategy/malaysian_snr/malaysian_snr_strategy.py`](file:///c:/TradingBoot/smc_synthetic_bot/strategy/malaysian_snr/malaysian_snr_strategy.py)<br>[`strategy/malaysian_snr/config.py`](file:///c:/TradingBoot/smc_synthetic_bot/strategy/malaysian_snr/config.py) | **+WinRate & +RR:** En lugar de fijar un SL estático holgado en el extremo H1, se ancla al extremo de la mecha de rechazo en M15 (+ buffer 0.10 ATR). Al reducir el riesgo por punto, TP1 (+2.0R) se alcanza en menos pips y con mayor rapidez. |
| **4** | **Trailing Stop Escalonado Mecánico para Runner** | [`strategy/execution/live_trading_engine.py`](file:///c:/TradingBoot/smc_synthetic_bot/strategy/execution/live_trading_engine.py) | **+Rentabilidad Neta:** Protege el profit flotante de la corredora en 3 fases mecánicas:<br>• Al tocar **+2.0R** (TP1): SL a Break-Even + spread buffer.<br>• Al tocar **+2.5R**: SL asegura automáticamente **+1.5R**.<br>• Al tocar **+3.5R**: SL asegura automáticamente **+2.5R**. |
| **5** | **Confluencia Dinámica con EMA 50 en H1** | [`strategy/malaysian_snr/video_rules.py`](file:///c:/TradingBoot/smc_synthetic_bot/strategy/malaysian_snr/video_rules.py)<br>[`strategy/malaysian_snr/malaysian_snr_strategy.py`](file:///c:/TradingBoot/smc_synthetic_bot/strategy/malaysian_snr/malaysian_snr_strategy.py) | **+Calidad de Trade:** Identifica la alineación del nivel horizontal SNR con la EMA 50 en H1 ($\le 0.40$ ATR). Etiqueta `dynamic_ema_50 = True` y otorga +10 puntos al `trade_score`. |

---

## 2. Detalle Técnico de la Implementación

### 2.1. Módulo "Fakeout Trap"
- **Función:** [`fakeout_trap_candidate`](file:///c:/TradingBoot/smc_synthetic_bot/strategy/malaysian_snr/video_rules.py#L209-L253)
- **Lógica de rechazo:**
  - Si la vela penetra hasta `0.60 ATR` más allá del nivel (antiguamente fallaba por `RETEST_PENETRATION_TOO_DEEP` al superar 0.35 ATR).
  - La mecha de absorción absorbe al menos el 50% del rango de la vela (`wick_ratio >= 0.50`).
  - El cuerpo de la vela cierra de vuelta sobre el nivel (dentro del rango permitido).
  - Emite el disparador oficial: `trigger = 'SNR_FAKEOUT_TRAP_SWEEP'`.

### 2.2. Quasimodo de Continuación (QMC)
- **Función:** [`quasimodo_continuation_candidates`](file:///c:/TradingBoot/smc_synthetic_bot/strategy/malaysian_snr/validation.py#L288-L338)
- **Geometría Causal de 3 Swings en Tendencia:**
  - **QMC Alcista:** Swing A (High / Hombro Izquierdo) $\to$ Swing B (Low de retroceso) $\to$ Swing Head (High más alto que A). La primera vela cerrada que rompe el Head confirma el setup. Nivel de retest para entrar en compra: Hombro Izquierdo (A).
  - **QMC Bajista:** Swing A (Low / Hombro Izquierdo) $\to$ Swing B (High de retroceso) $\to$ Swing Head (Low más bajo que A). La primera vela cerrada que rompe el Head confirma el setup. Nivel de retest para entrar en venta: Hombro Izquierdo (A).

### 2.3. Stop Loss Micro-Estructural en M15
- **Ubicación:** [`strategy/malaysian_snr/malaysian_snr_strategy.py`](file:///c:/TradingBoot/smc_synthetic_bot/strategy/malaysian_snr/malaysian_snr_strategy.py#L413-L440)
- **Cálculo:**
  - Extrae el extremo real alcanzado por la vela de retest y confirmación en M15 (`low.min()` para compras, `high.max()` para ventas).
  - Calcula `micro_stop = extremo ± (0.10 * ATR)`.
  - Si `micro_stop` es más ajustado que el SL estructural de H1 y cumple con el piso mínimo de seguridad (`min_risk_floor = 0.20 * ATR` para tolerancia a spreads), se utiliza como el Stop Loss real de la orden.
  - La orden se ejecuta con un riesgo ajustado, acercando físicamente la distancia al TP1 (1:2.0 RR).

### 2.4. Trailing Stop Escalonado Mecánico
- **Ubicación:** [`strategy/execution/live_trading_engine.py`](file:///c:/TradingBoot/smc_synthetic_bot/strategy/execution/live_trading_engine.py#L3825-L3845) y [`_manage_runner_extension`](file:///c:/TradingBoot/smc_synthetic_bot/strategy/execution/live_trading_engine.py#L4140-L4160)
- **Etapas activas para `MALAYSIAN_SNR`:**
  - `MSNR_LOCK_1_5R`: Al alcanzar `+2.5R`, mueve el SL en MT5 a `+1.5R`.
  - `MSNR_LOCK_2_5R`: Al alcanzar `+3.5R`, mueve el SL en MT5 a `+2.5R`.
  - Al alcanzar `max_target_rr` (TP4 o 4.0R): Cierre completo a mercado con motivo `MAX_TARGET_REACHED`.

### 2.5. Confluencia Dinámica con EMA 50
- **Función:** [`h1_ema_dynamic_confluence`](file:///c:/TradingBoot/smc_synthetic_bot/strategy/malaysian_snr/video_rules.py#L256-L293)
- Calcula la EMA exponencial de 50 periodos en velas H1 cerradas.
- Si el nivel SNR está a $\le 0.40 \times \text{ATR}$ de la EMA 50, se confirma la confluencia dinámica y se suma bonificación al `trade_score`.

---

## 3. Validación y Pruebas Unitarias

Se ejecutó la suite completa de pruebas unitarias y de regresión:
```bash
pytest tests/test_msnr_video_improvements.py tests/test_msnr_two_year_replay.py tests/test_v119_malaysian_snr_sentinel_instruments_consistency.py tests/test_v119_multistrategy_thesis_audit.py
```
**Resultado:** **66 passed in 6.56s (100% de éxito, 0 fallos)**.

Tests añadidos específicamente para estas 5 mejoras:
- `test_fakeout_trap_candidate_and_retest_confirmation`: Valida el sweep de liquidez y absorción $\ge 50\%$.
- `test_quasimodo_continuation_candidates`: Valida la detección causal de QMC alcista y bajista.
- `test_h1_ema_dynamic_confluence`: Valida la cercanía a la EMA 50 en H1.
- `test_m15_micro_structural_stop_loss`: Valida que el SL micro M15 reduce el riesgo y acerca TP1.
- `test_msnr_runner_tiered_trailing_lock`: Valida los candados de +1.5R y +2.5R en el broker.

---

## 4. Estado de Base de Datos y Knowledge Graph
- **SQLite:** 19 registros de preferencias de runtime de `MALAYSIAN_SNR` sincronizados con los nuevos parámetros activados (`enable_fakeout_trap=True`, `enable_qmc_pattern=True`, `enable_m15_micro_stop=True`, `enable_runner_trailing_lock=True`, `enable_h1_ema_confluence=True`).
- **Graphify:** Ejecutado `graphify update .` (6,565 nodos, 18,246 aristas, 233 comunidades actualizadas sin errores).
