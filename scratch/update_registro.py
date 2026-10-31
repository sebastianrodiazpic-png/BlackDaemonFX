entry = """### 2026-10-31 — Gestión Progresiva Dinámica en Vivo para Pata Corredora (1:2 Inicial -> Proteger 1.5R para 1:3 -> Proteger 2.5R para 1:4)  ·  Estado: aplicado sin commit
- **Qué**:
  - **Apertura de orden sin estimación preliminar fija**:
    * En `strategy/execution/live_trading_engine.py` (`_plan_split_orders`), la pata corredora (`RUNNER`) nace siempre configurada en el broker con su Take Profit inicial en **1:2 ($2.0\\text{ R}$)** (`eff_second_rr`), eliminando la colocación estática de $4.0\\text{ R}$ a ciegas al abrir la operación.
  - **Monitoreo dinámico en vivo en velas M5 (`_manage_runner_extension`)**:
    * **Hito 1 (+1.5 R)**: Al alcanzar $+1.5\\text{ R}$ de ganancia flotante en vivo, el monitor evalúa la estructura de mercado en M5 (`evaluate_runner_continuation`). Si se valida continuación hacia 1:3, **el stop loss se mueve a $+1.5\\text{ R}$ (bloqueando $+1.5\\text{ R}$ de beneficio garantizado)** y el Take Profit en el broker se amplía a **$3.0\\text{ R}$**. Si no hay continuación, el runner se cierra a mercado asegurando el beneficio.
    * **Hito 2 (+2.5 R)**: Al alcanzar $+2.5\\text{ R}$ flotantes buscando 1:4, el monitor vuelve a evaluar en M5 la continuación. Si se valida avance hacia 1:4, **el stop loss se mueve a $+2.5\\text{ R}$ (asegurando $+2.5\\text{ R}$ de ganancia)** y el Take Profit se amplía en el broker a **$4.0\\text{ R}$**. Si la estructura no muestra continuación, se cierra inmediatamente asegurando los $+2.5\\text{ R}$.
    * Si la posición toca el objetivo máximo ($4.0\\text{ R}$), se ejecuta el TP en el broker o el monitor ejecuta `MAX_TARGET_REACHED`.
  - **Parámetros y compatibilidad**:
    * Configuración por variables de entorno: `DAEMONBLACKFX_RUNNER_FIRST_TRIGGER_RR` (default 1.5), `DAEMONBLACKFX_RUNNER_FIRST_LOCK_RR` (default 1.5), `DAEMONBLACKFX_RUNNER_SECOND_TRIGGER_RR` (default 2.5), `DAEMONBLACKFX_RUNNER_SECOND_LOCK_RR` (default 2.5), `DAEMONBLACKFX_RUNNER_MAX_TARGET_RR` (default 4.0).
    * Nomenclatura dinámica de etapas (`1.5R_TO_3R`, `2.5R_TO_4R`) con total compatibilidad retrospectiva con etapas previas (`2R_TO_3R`, `3R_TO_4R`).
- **Por qué / evidencia**:
  - Evitar que una posición ganadora que alcanza $+1.5\\text{ R}$ o $+2.5\\text{ R}$ devuelva sus beneficios por mantener un TP preliminar lejano fijado a ciegas al nacer el trade.
  - El monitoreo en vivo en M5 permite surfear expansiones genuinas asegurando siempre el tramo ganado previo (bloqueo estricto de $+1.5\\text{ R}$ al buscar 3R y $+2.5\\text{ R}$ al buscar 4R).
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
