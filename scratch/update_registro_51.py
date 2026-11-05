from pathlib import Path

path = Path("REGISTRO_CAMBIOS_ESTRATEGIA.md")
content = path.read_text(encoding="utf-8")

# Update table rows
old_ict_synth = "| ICT sintéticos (28-oct) | Solo velas cerradas · entrada **limitada virtual** (8 velas M15) · tope spread/SL 2 % · IA en **sombra** · piso SL `sl_atr_h1 ≥ 1.0` · ADX H1 `≥ 20.0` · retroceso mitigado `≤ 0.45 R` (`DAEMONBLACKFX_ICT_MAX_PULLBACK_R=0.45`, +363 trades, +37.7 R netos) · asimetría direccional (Jump 50/75 BUY only, Step Index y Step Index 500 SELL only: +8.2 R salvados) · **30 activos con WR > 48%** (+450.8 R acumulados); podados únicamente `Crash 1000`, `Vol 90 1s` y `HF Vol 50` |"
new_ict_synth = "| ICT sintéticos (01-nov) | Solo velas cerradas · entrada **limitada virtual** (8 velas M15) · tope spread/SL 2 % · IA en **sombra** · piso SL `sl_atr_h1 ≥ 1.0` · ADX H1 `≥ 20.0` · retroceso mitigado `≤ 0.45 R` · **31 activos base activos (+ 2 alias broker = 33 símbolos) con WR > 51.0%** (+438.4 R acumulados); podados por WR <= 51.0%: `Crash 900`, `Boom 500`, `Volatility 100`, `Crash 1000`, `Vol 90 1s`, `HF Vol 50` |"

old_ict_forex = "| ICT Forex (26-oct) | Ventana Londres depurada 03:00–05:00 NY · Silver Bullet 03:00 NY · orden limitada virtual con tope spread/SL 2,5 % · **9 pares base activos con WR > 47%** (`GBPUSD`, `USDCHF`, `EURJPY`, `CADCHF`, `NZDUSD`, `EURGBP`, `GBPJPY`, `GBPCHF`, `AUDJPY` + `*micro` = 18 símbolos, `+17,47 R`) en `FOREX_1` (ON) y **12 pares base podados** (24 símbolos) en `FOREX_2` (OFF) |"
new_ict_forex = "| ICT Forex (01-nov) | Ventana Londres depurada 03:00–05:00 NY · Silver Bullet 03:00 NY · orden limitada virtual con tope spread/SL 2,5 % · **7 pares base activos con WR > 51.0%** (`GBPUSD`, `USDCHF`, `EURJPY`, `CADCHF`, `NZDUSD`, `EURGBP`, `GBPJPY` + `*micro` = 14 símbolos, `+14,87 R`) en `FOREX_1` (ON); `GBPCHF` (50.9%) y resto podados en `FOREX_2` (OFF) |"

old_msnr = "| Malaysian SNR (28-oct) | **Fórmula Híbrida Institucional v3.2** · 35 activos activos con WR ≥ 47 % (24 sintéticos + 11 mercados reales en sesión Londres+NY/Asia-NY) · **3 Mejoras Validadas (+113.13 R delta)**: Clearance obstáculo 1.2R (alineado a TP1 1:1), Buffer dinámico de retest H1 (+0.20 ATR) y Asimetría direccional Jump (BUY) / Step (SELL) · 6 activos en **PODA PREVENTIVA** (`Boom 600`, `Boom 900`, `Crash 1000`, `EURUSD`, `AUDUSD`, `CHFJPY`) · daemons reiniciados y activos |"
new_msnr = "| Malaysian SNR (01-nov) | **Fórmula Híbrida Institucional v3.2** · **27 activos activos con WR > 51.0%** (18 sintéticos + 9 mercados reales); podados por WR <= 51.0%: `Boom 300`, `Vol over Crash 550`, `Volatility 150 (1s)`, `CADJPY`, `Crash 900`, `GBPJPY`, etc. Sincronizado en todas las pestañas de /Instruments |"

content = content.replace(old_ict_synth, new_ict_synth)
content = content.replace(old_ict_forex, new_ict_forex)
content = content.replace(old_msnr, new_msnr)

# Insert new entry at top of Historial de cambios
marker = "## Historial de cambios (más reciente primero)\n"
new_entry = """## Historial de cambios (más reciente primero)

### 2026-11-01 — Filtro Estricto de Rentabilidad Cuantitativa (>51% Win Rate) y Sincronización Plena de /Instruments en Todas las Pestañas  ·  Estado: aplicado sin commit
- **Qué**:
  - Aplicación de política cuantitativa institucional estricta `Win Rate > 51.0%` en todas las estrategias y pestañas de `/Instruments`:
    * Pestaña `Sintéticos` (ICT y Workers: STEP, JUMP, VOLATILITY, BOOM, CRASH): Poda preventiva y deselección de activos con acierto <= 51.0% (`Boom 500 Index` 50.4%, `Crash 900 Index` 50.5% y `Volatility 100 Index` 49.7%). Quedan activos y persistentes **31 activos sintéticos base únicos** (+ 2 alias canónicos del broker = **33 símbolos**), con WR entre 51.2% y 64.3%.
    * Pestaña `Forex`: Poda preventiva de `GBPCHF` (50.9% WR). Quedan activos y persistentes los **7 pares base élite** (14 símbolos con `*micro`: `GBPUSD`, `USDCHF`, `EURJPY`, `CADCHF`, `NZDUSD`, `EURGBP`, `GBPJPY`), con acierto entre 52.1% y 58.3%.
    * Pestaña `ICT` (Índices, Metales, Commodities): Confirmación de los **4 activos base élite** (6 símbolos con micro: `US Tech 100` 79.7%, `Wall Street 30` 60.0%, `XAUUSD` 57.0%, `US Oil` 55.9%).
    * Pestaña `Malaysian SNR`: Poda preventiva de activos con acierto <= 51.0% (`Boom 300 Index` 51.0%, `Vol over Crash 550` 50.8%, `Volatility 150 (1s) Index` 50.8% y `CADJPY` 50.5%). Quedan activos y persistentes **27 activos** (18 sintéticos + 9 mercados reales), todos con WR entre 51.2% y 100.0%.
    * Pestaña `Trend Pullback`: Sincronización de los **17 sintéticos seleccionados** validados con WR > 51.0% (53.8% a 62.0%), manteniendo la estrategia en pausa preventiva en workers.
  - Sincronización y persistencia en caliente de las preferencias de selección en ambas bases de datos SQLite (`storage/database.sqlite` y `storage/trading_bot.sqlite3`) para `DEMO` y `LIVE`, y en el estado global `storage/dashboard/last_state.json`.
- **Por qué / evidencia**:
  - Requisito de usuario para erradicar instrumentos con expectativa neutra o subóptima (<= 51.0% WR), blindando las cuentas demo y real para que ningún worker abra órdenes en instrumentos sin ventaja estadística probada.
- **Ficheros**:
  - `config/ict_instrument_policy.py`
  - `strategy/malaysian_snr/config.py`
  - `tools/apply_ict_instrument_policy.py`
  - `storage/database.sqlite`
  - `storage/trading_bot.sqlite3`
  - `storage/dashboard/last_state.json`
  - `tests/test_ict_instrument_policy.py`
  - `tests/test_fixes_validation.py`
- **Configuración / interruptores**:
  - `DAEMONBLACKFX_ICT_5Y_AUDIT=1`, `DAEMONBLACKFX_ALLOW_SELECTIVE_ACTIVATION=1`, `DAEMONBLACKFX_MSNR_ACIERTO47=on`.
- **Tests**:
  - `tests/test_ict_instrument_policy.py`: 19/19 passed.
  - `tests/test_fixes_validation.py`: 6/6 passed.
  - Regresión completa (`test_human_criteria_engine.py`, `test_disabled_workers.py`, `test_performance_optimizations_20261026.py`, `test_adaptive_bidirectional_jump_step.py`): 29/29 passed. Total 54/54 passed.
"""

content = content.replace(marker, new_entry)
path.write_text(content, encoding="utf-8")
print("Updated REGISTRO_CAMBIOS_ESTRATEGIA.md successfully")
