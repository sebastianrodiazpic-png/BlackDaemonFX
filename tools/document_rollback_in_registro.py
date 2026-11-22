# -*- coding: utf-8 -*-
with open('REGISTRO_CAMBIOS_ESTRATEGIA.md', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Marcar la entrada anterior como REVERTIDO
old_header = "### 2026-11-07 — Purga Total de Instrumentos Podados en /Strategy-bases (Vista Exclusiva de Activos Rentables Operables)  ·  Estado: aplicado sin commit"
reverted_header = "### 2026-11-07 — [REVERTIDO] Purga Total de Instrumentos Podados en /Strategy-bases  ·  Estado: REVERTIDO"

if old_header in content:
    content = content.replace(old_header, reverted_header)
else:
    # Buscar con regex flexible por caracteres especiales
    import re
    content = re.sub(
        r'### 2026-11-07 [^\n]* Purga Total de Instrumentos Podados[^\n]*',
        reverted_header,
        content
    )

# 2. Agregar entrada de reversión arriba
new_entry = """### 2026-11-07 — Reversión de Purga de Podados en /Strategy-bases (Restauración de los 292 Registros Completos)  ·  Estado: aplicado sin commit
- **Qué**:
  - Reversión total a solicitud del usuario de la purga de instrumentos podados.
  - Se restaura `dashboard/strategy_bases_page.py` con el catálogo completo de **292 evaluaciones** (73 instrumentos × 4 estrategias) en `WINNERS_DATA`, la tabla y sección HTML de `LOSERS_DATA` (115 podados preventivos / incompatibles), y los controles de filtro de 3 vías (`statusFilterAll`, `statusFilterActive`, `statusFilterPruned`).
  - Se mantienen plenamente vigentes y actualizados los números de **Confluencia Tripartita** para todos los instrumentos (incluyendo `Crash 300 Index` en ICT con 430 trades y 66.98% WR, +170.34 R).
- **Por qué**:
  - Solicitud expresa del usuario ("ete cambio no era el que habia solicitado vuelve atras por favor").
- **Evidencia**:
  - `tests/test_strategy_bases_5y_all_records.py`: 5/5 PASSED (valida 292 registros totales, 73 por estrategia, Jump 75, Crash 300, y filtros intactos).
  - `tests/test_strategy_bases_tab_and_msnr_cleanup.py`: 6/6 PASSED (292 winners, 177 rentables, 115 podados en losers).
  - `tests/test_tripartite_confluence_gate.py`: 8/8 PASSED.
  - `tests/test_tripartite_confluence_replay.py`: 6/6 PASSED.
- **Ficheros tocados**:
  - `dashboard/strategy_bases_page.py`
  - `tests/test_strategy_bases_5y_all_records.py`
  - `tests/test_strategy_bases_tab_and_msnr_cleanup.py`
  - `REGISTRO_CAMBIOS_ESTRATEGIA.md`
- **Tests ejecutados**:
  - `pytest tests/test_strategy_bases_tab_and_msnr_cleanup.py tests/test_strategy_bases_5y_all_records.py tests/test_tripartite_confluence_gate.py tests/test_tripartite_confluence_replay.py` -> 25/25 PASSED en 7.07s.

"""

import re
m = re.search(r'## Historial de cambios[^\n]*\n+', content)
if m:
    content = content[:m.end()] + new_entry + content[m.end():]

with open('REGISTRO_CAMBIOS_ESTRATEGIA.md', 'w', encoding='utf-8') as f:
    f.write(content)

print("Entrada de reversión documentada correctamente en REGISTRO_CAMBIOS_ESTRATEGIA.md")
