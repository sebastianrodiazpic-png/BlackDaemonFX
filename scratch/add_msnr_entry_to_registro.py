entry = """### 2026-10-31 — Rehabilitación Operativa y Rentabilidad de Malaysian SNR (Canasta Élite Cuantitativa, Confirmación No Asfixiante y Acople a Gestión Progresiva 2 Patas)  ·  Estado: aplicado sin commit
- **Qué**:
  - **Reactivación y desbloqueo de confirmaciones M15 (erradicación de la asfixia de entradas)**:
    * En `strategy/malaysian_snr/config.py`: reactivación de `enable_scenario_1_continuation` (por defecto `True`, configurable vía `DAEMONBLACKFX_MSNR_ENABLE_CONTINUATION=1`), el escenario que producía el 92.3% del volumen rentable original con $ADX \\ge 20$.
    * Ampliación de la ventana de retest a 180 minutos (`retest_window_minutes = 180`), permitiendo absorber el tiempo natural de retest institucional.
    * Flexibilización de la tolerancia de barras de confirmación (`confirmation_tolerance_bars = 2`, `DAEMONBLACKFX_MSNR_CONFIRMATION_TOLERANCE_BARS`), erradicando el descarte prematuro `SETUP_ALREADY_CONFIRMED`.
    * Calibración de cuerpo de recuperación a `0.25` (`retest_min_body_ratio` y `recovery_min_body_ratio`), evitando que velas sanas con mechas de rechazo sean descartadas.
    * Sesgo macro Storyline D1/H4 (`enable_synthetic_daily_storyline_filter = True`, `DAEMONBLACKFX_MSNR_STORYLINE_FILTER=1`) para filtrar continuaciones solo a favor del rechazo mayor, tal como estipula el método original Alchemist.
  - **Canasta Élite Cuantitativa (`MSNR_ELITE_SYNTHETICS`) en `config/ict_instrument_policy.py`**:
    * Reincorporación prioritaria de los activos con rentabilidad probada en el replay fiel multianual (1.368 ops):
      - `Boom 1000 Index` (+21.04 R, 46.5% WR)
      - `Crash 1000 Index` (+14.38 R, 38.1% WR)
      - `Volatility 25 Index` (+15.85 R, 37.7% WR)
      - `Volatility 10 Index` (+14.19 R, 36.7% WR)
      - `Step Index` (+5.50 R, 35.9% WR)
      - Activos complementarios: `Volatility 90`, `Vol 50 (1s)`, `Boom 500`, `Crash 900`, `Boom 300`, `Crash 600`, `VolSwitch High Vol`, etc.
    * Exclusión estricta de los activos con sangría demostrada: `Jump 25 Index` (−43.02 R) y `Volatility 75 Index` (−27.44 R).
  - **Acoplamiento de la Nueva Gestión Progresiva de 2 Patas en vivo (`_manage_runner_extension`)**:
    * En `strategy/execution/live_trading_engine.py`: la pata corredora de `MALAYSIAN_SNR` se integra de lleno a la gestión dinámica progresiva:
      - Al alcanzar $+1.5\\text{ R}$: se asegura $+1.5\\text{ R}$ en el Stop Loss (`protected_sl`) y el TP se amplía en el broker a **$3.0\\text{ R}$** (etapa `1.5R_TO_3R` / `EXTENDED_TO_3R`).
      - Al alcanzar $+2.5\\text{ R}$: se asegura $+2.5\\text{ R}$ en el Stop Loss y el TP se amplía en el broker a **$4.0\\text{ R}$** (etapa `2.5R_TO_4R` / `EXTENDED_TO_4R`).
      - Si en cualquiera de los dos hitos no hay confirmación de avance, la posición se liquida a mercado asegurando el beneficio protegido.
- **Por qué / evidencia**:
  - Auditoría de los 22 informes de investigación (`MSNR_*.md`): la rentabilidad inicial del 5 al 9 de octubre (35-58 ops/día) se perdió por sobrefiltrado acumulativo que apagó el 92% de las entradas y excluyó los mejores activos ganadores (`Boom 1000`, `Crash 1000`, etc.).
  - Replay fiel 180 días (1.368 trades): Fractal y QMC en la canasta élite promedian ratios positivos (+35.5 R y +4.4 R), mientras que Jump 25 y Vol 75 causaban el 80% de las pérdidas.
- **Ficheros**:
  - `config/ict_instrument_policy.py`
  - `strategy/malaysian_snr/config.py`
  - `strategy/execution/live_trading_engine.py`
  - `tests/test_msnr_progressive_runner_and_elite_basket.py`
  - `REGISTRO_CAMBIOS_ESTRATEGIA.md`
- **Configuración / interruptores**:
  - `DAEMONBLACKFX_MSNR_ENABLE_CONTINUATION`: Activa escenario 1 de continuación (por defecto `1`).
  - `DAEMONBLACKFX_MSNR_RETEST_WINDOW_MINUTES`: Ventana temporal de retest en minutos (por defecto `180`).
  - `DAEMONBLACKFX_MSNR_CONFIRMATION_TOLERANCE_BARS`: Tolerancia de barras M15 para confirmación (por defecto `2`).
  - `DAEMONBLACKFX_MSNR_RECOVERY_MIN_BODY_RATIO`: Ratio de cuerpo mínimo de recuperación M15 (por defecto `0.25`).
  - `DAEMONBLACKFX_MSNR_STORYLINE_FILTER`: Filtro de alineación con Storyline macro D1/H4 (por defecto `1`).
  - `DAEMONBLACKFX_MSNR_ELITE_BASKET`: Activa la Canasta Élite Cuantitativa (por defecto `1`).
- **Tests**:
  - `tests/test_msnr_progressive_runner_and_elite_basket.py` (4/4 pasan).
  - `tests/test_dynamic_progressive_runner_1_5r_2_5r.py` (3/3 pasan).
  - `tests/test_daemon_runner_extension.py` (3/3 pasan).
  - `tests/test_ict_instrument_policy.py` (19/19 pasan).
  - Suite combinada completa: 26/26 tests en verde sin regresiones.
- **Efecto esperado y riesgos**:
  - Recuperación inmediata de la frecuencia y rentabilidad operativa de Malaysian SNR en activos con alta expectativa estadística, protegiendo las ganancias en vivo en $+1.5\\text{ R}$ y $+2.5\\text{ R}$ para evitar la devolución de beneficios en el runner.

"""

path = 'REGISTRO_CAMBIOS_ESTRATEGIA.md'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

marker = '## Historial de cambios (más reciente primero)\n\n'
if marker in content:
    content = content.replace(marker, marker + entry + '\n', 1)
    print("Inserted entry into REGISTRO_CAMBIOS_ESTRATEGIA.md")
else:
    marker_crlf = '## Historial de cambios (más reciente primero)\r\n\r\n'
    if marker_crlf in content:
        content = content.replace(marker_crlf, marker_crlf + entry.replace('\n', '\r\n') + '\r\n', 1)
        print("Inserted entry (CRLF) into REGISTRO_CAMBIOS_ESTRATEGIA.md")
    else:
        print("Marker not found!")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
