# -*- coding: utf-8 -*-
with open('REGISTRO_CAMBIOS_ESTRATEGIA.md', 'r', encoding='utf-8') as f:
    content = f.read()

new_entry = """### 2026-11-07 — Eliminación del Apartado 'Instrumentos Podados por Estrategia' en /Strategy-bases  ·  Estado: aplicado sin commit
- **Qué**:
  - Eliminación exclusiva de la tarjeta HTML inferior `<section class="card">` con título *"⚠️ Instrumentos Podados por Estrategia (Poda Preventiva Persistida en /Instruments)"* y su tabla `#losersTable` en [`dashboard/strategy_bases_page.py`](file:///c:/TradingBoot/smc_synthetic_bot/dashboard/strategy_bases_page.py).
  - Se incorporó un retorno defensivo `if (!tbody) return;` en la función JavaScript `renderLosersTable()` para garantizar ejecución limpia sin errores en consola cuando no existe dicho elemento en el DOM.
  - **Se preservaron íntegros al 100%**:
    - El dataset interactivo `WINNERS_DATA` con sus 292 registros auditados (73 instrumentos × 4 estrategias) y todas las métricas de Confluencia Tripartita (Crash 300 con 430 trades, 66.98% WR, etc.).
    - El dataset `LOSERS_DATA` en memoria (115 registros) y los controles de filtrado por pestaña y estado (`statusFilterAll`, `statusFilterActive`, `statusFilterPruned`).
- **Por qué**:
  - Solicitud precisa del usuario clarificando mediante captura de pantalla que deseaba remover únicamente ese bloque visual de podados que aparecía debajo de la tabla principal en cada pestaña.
- **Evidencia**:
  - `tests/test_strategy_bases_5y_all_records.py`: 6/6 PASSED (incluye nuevo test `test_losers_table_section_removed_from_html`).
  - `tests/test_strategy_bases_tab_and_msnr_cleanup.py`: 6/6 PASSED.
  - `tests/test_tripartite_confluence_gate.py`: 8/8 PASSED.
  - `tests/test_tripartite_confluence_replay.py`: 6/6 PASSED.
  - Total: 26/26 tests unitarios pasando.
- **Ficheros tocados**:
  - `dashboard/strategy_bases_page.py`
  - `tests/test_strategy_bases_5y_all_records.py`
  - `REGISTRO_CAMBIOS_ESTRATEGIA.md`
- **Tests ejecutados**:
  - `pytest tests/test_strategy_bases_tab_and_msnr_cleanup.py tests/test_strategy_bases_5y_all_records.py tests/test_tripartite_confluence_gate.py tests/test_tripartite_confluence_replay.py` -> 26/26 PASSED en 7.16s.

"""

import re
m = re.search(r'## Historial de cambios[^\n]*\n+', content)
if m:
    content = content[:m.end()] + new_entry + content[m.end():]

with open('REGISTRO_CAMBIOS_ESTRATEGIA.md', 'w', encoding='utf-8') as f:
    f.write(content)

print("Entrada añadida correctamente a REGISTRO_CAMBIOS_ESTRATEGIA.md")
