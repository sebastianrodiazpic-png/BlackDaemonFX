# -*- coding: utf-8 -*-
with open('REGISTRO_CAMBIOS_ESTRATEGIA.md', 'r', encoding='utf-8') as f:
    content = f.read()

new_entry = """### 2026-11-07 — Corrección de Sintaxis JS en renderTabWorkers y Restauración de Carga en /Instruments  ·  Estado: aplicado sin commit
- **Diagnóstico del problema**:
  - Al silenciar la función `renderTabWorkers` en [`dashboard/realtime_dashboard.py`](file:///c:/TradingBoot/smc_synthetic_bot/dashboard/realtime_dashboard.py), se introdujo una declaración duplicada del identificador `const panel` dentro del mismo bloque de ámbito de la función.
  - En JavaScript estricto (ES6+), esto provocaba un `SyntaxError: Identifier 'panel' has already been declared` en tiempo de compilación/parseo del script en el navegador.
  - Al fallar el parseo de todo el `<script>`, la rutina de inicialización de la página quedaba bloqueada, impidiendo la invocación de `window.pageLoading.dismiss()`, lo que mantenía permanentemente la cortina/overlay de carga ("Cargando pantalla...") en pantalla.
- **Solución implementada**:
  - Se reescribió `renderTabWorkers` de forma limpia y concisa:
    ```javascript
    function renderTabWorkers(s) {
      const banner = $('strategyHighlightBanner');
      if (banner) { banner.style.display = 'none'; banner.innerHTML = ''; }
      const panel = $('tabWorkerPanel');
      if (panel) { panel.style.display = 'none'; panel.innerHTML = ''; }
    }
    ```
  - Se añadió la prueba permanente `test_instruments_javascript_syntax_valid` en `tests/test_v121_instruments_tri_motor_worker_control.py` que ejecuta `node --check` sobre todos los scripts embebidos de `/instruments` para blindar la sintaxis de forma automatizada.
- **Evidencia**:
  - Verificación `node --check` en Node.js sobre los scripts de `/instruments`: 0 errores de sintaxis.
  - `tests/test_v121_instruments_tri_motor_worker_control.py`: 9/9 PASSED.
  - Suite de regresión completa: 51/51 PASSED.
- **Ficheros tocados**:
  - `dashboard/realtime_dashboard.py`
  - `tests/test_v121_instruments_tri_motor_worker_control.py`
  - `REGISTRO_CAMBIOS_ESTRATEGIA.md`
- **Tests ejecutados**:
  - `pytest tests/test_v121_instruments_tri_motor_worker_control.py tests/test_trend_pullback_instruments_tab.py tests/test_v119_malaysian_snr_sentinel_instruments_consistency.py tests/test_strategy_bases_tab_and_msnr_cleanup.py tests/test_strategy_bases_5y_all_records.py tests/test_tripartite_confluence_gate.py tests/test_tripartite_confluence_replay.py` -> 51/51 PASSED en 13.29s.

"""

import re
m = re.search(r'## Historial de cambios[^\n]*\n+', content)
if m:
    content = content[:m.end()] + new_entry + content[m.end():]

with open('REGISTRO_CAMBIOS_ESTRATEGIA.md', 'w', encoding='utf-8') as f:
    f.write(content)

print("Entrada añadida correctamente a REGISTRO_CAMBIOS_ESTRATEGIA.md")
