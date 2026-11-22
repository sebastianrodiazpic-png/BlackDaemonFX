# -*- coding: utf-8 -*-
with open('REGISTRO_CAMBIOS_ESTRATEGIA.md', 'r', encoding='utf-8') as f:
    content = f.read()

new_entry = """### 2026-11-07 — Eliminación del Panel 'Control de Workers en Paralelo' y Banner de Estrategia en /Instruments  ·  Estado: aplicado sin commit
- **Qué**:
  - Eliminación visual de la tarjeta de *Control de Workers en Paralelo* (`#tabWorkerPanel`) y del banner informativo de estrategia (`#strategyHighlightBanner`) en **todas las pestañas** de `/instruments` (`SYNTHETICS`, `FOREX`, `ICT`, `MALAYSIAN_SNR`, `ORB`, etc.) en [`dashboard/realtime_dashboard.py`](file:///c:/TradingBoot/smc_synthetic_bot/dashboard/realtime_dashboard.py).
  - Ambos contenedores se establecieron en `style="display:none;"` en la plantilla base HTML y la función JavaScript `renderTabWorkers(s)` fue configurada para mantenerlos ocultos de forma inmediata en cada actualización de ciclo o cambio de pestaña.
  - La interfaz de `/instruments` se mantiene 100% limpia y operativa, mostrando directamente los controles de acción (`Activar instrumentos ICT...`, `Seleccionar todos`, `Limpiar`, `Aplicar selección`), la barra de búsqueda `Buscar instrumento...`, y las tablas de instrumentos con sus categorías y checkboxes de selección.
- **Por qué**:
  - Solicitud expresa del trader mediante 5 capturas de pantalla de cada una de las pestañas de `/instruments` donde se mostraba dicho bloque redundante de tarjetas de workers en paralelo.
- **Evidencia**:
  - `tests/test_v121_instruments_tri_motor_worker_control.py`: 8/8 PASSED (incluye nuevo test `test_instruments_parallel_worker_panel_hidden_in_all_tabs`).
  - `tests/test_trend_pullback_instruments_tab.py`: 11/11 PASSED.
  - `tests/test_v119_malaysian_snr_sentinel_instruments_consistency.py`: 4/4 PASSED.
  - Total: 23 tests de dashboard e instrumentos pasando al 100%.
- **Ficheros tocados**:
  - `dashboard/realtime_dashboard.py`
  - `tests/test_v121_instruments_tri_motor_worker_control.py`
  - `REGISTRO_CAMBIOS_ESTRATEGIA.md`
- **Tests ejecutados**:
  - `pytest tests/test_v121_instruments_tri_motor_worker_control.py tests/test_trend_pullback_instruments_tab.py tests/test_v119_malaysian_snr_sentinel_instruments_consistency.py` -> 23/23 PASSED.

"""

import re
m = re.search(r'## Historial de cambios[^\n]*\n+', content)
if m:
    content = content[:m.end()] + new_entry + content[m.end():]

with open('REGISTRO_CAMBIOS_ESTRATEGIA.md', 'w', encoding='utf-8') as f:
    f.write(content)

print("Entrada añadida correctamente a REGISTRO_CAMBIOS_ESTRATEGIA.md")
