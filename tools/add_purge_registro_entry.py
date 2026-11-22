# -*- coding: utf-8 -*-
with open('REGISTRO_CAMBIOS_ESTRATEGIA.md', 'r', encoding='utf-8') as f:
    content = f.read()

new_entry = """### 2026-11-07 — Purga Total de Instrumentos Podados en /Strategy-bases (Vista Exclusiva de Activos Rentables Operables)  ·  Estado: aplicado sin commit
- **Qué**:
  1. **Eliminación completa de instrumentos podados en todas las pestañas de `/Strategy-bases` (`dashboard/strategy_bases_page.py`)**:
     - `WINNERS_DATA` filtrado para contener exclusivamente los **177 instrumentos rentables operables** (`is_profitable: True`) bajo Confluencia Tripartita (Malaysian SNR: 63, ICT: 59, Trend Pullback: 38, ORB New York: 17).
     - Purgados los 115 registros que correspondían a podas preventivas o activos incompatibles.
  2. **Eliminación de la sección HTML de Pérdidas y Podas**:
     - Eliminada completamente la tarjeta `<section class="card">` con título *"⚠️ Instrumentos Podados por Estrategia (Poda Preventiva Persistida en /Instruments)"* y la tabla `#losersTable`.
     - `LOSERS_DATA` redefinido como arreglo vacío (`[]`) y `renderLosersTable` adaptado a no-op defensivo.
  3. **Simplificación de la interfaz y barra de filtros**:
     - Eliminados los selectores de "Solo Podados Preventivos" y "Ver todos los activos (Rentables + Podados)".
     - Incorporado indicador de estado directo: `✓ 177 Activos Operables Rentables (100% Sincronizados y Libres de Poda)`.
     - Métricas y badges en `STRATEGY_METRICS` actualizados para reflejar universo de 177 activos rentables operables.
- **Por qué**:
  - Requerimiento expreso del trader para limpiar la visualización en `/Strategy-bases` eliminando tablas y activos descartados innecesarios, asegurando que cada pestaña muestre únicamente los pares e índices que efectivamente se operan con expectativa matemática positiva probada en 5 años.
- **Evidencia**:
  - `tests/test_strategy_bases_5y_all_records.py`: 5/5 PASSED (valida 177 activos rentables, 0 podados en `WINNERS_DATA`, ausencia de `losersTable`).
  - `tests/test_strategy_bases_tab_and_msnr_cleanup.py`: 6/6 PASSED.
  - `tests/test_tripartite_confluence_gate.py`: 8/8 PASSED.
  - `tests/test_tripartite_confluence_replay.py`: 6/6 PASSED.
- **Ficheros tocados**:
  - `dashboard/strategy_bases_page.py`
  - `tests/test_strategy_bases_5y_all_records.py`
  - `tests/test_strategy_bases_tab_and_msnr_cleanup.py`
  - `REGISTRO_CAMBIOS_ESTRATEGIA.md`
- **Interruptores**:
  - Mantiene intactos los interruptores de motor y Confluencia Tripartita (`DAEMONBLACKFX_TRIPARTITE_CONFLUENCE_ENABLED`).
- **Tests ejecutados**:
  - `pytest tests/test_strategy_bases_tab_and_msnr_cleanup.py tests/test_strategy_bases_5y_all_records.py tests/test_tripartite_confluence_gate.py tests/test_tripartite_confluence_replay.py` -> 25/25 PASSED en 6.96s.
- **Plan de rollback**:
  - Restaurar `WINNERS_DATA` y la sección de podados con `git checkout -- dashboard/strategy_bases_page.py`.

"""

target = "## Historial de cambios (más reciente primero)\n\n"
if target in content:
    content = content.replace(target, target + new_entry)
else:
    # Si hay caracteres especiales o BOM
    import re
    m = re.search(r'## Historial de cambios[^\n]*\n+', content)
    if m:
        content = content[:m.end()] + new_entry + content[m.end():]

with open('REGISTRO_CAMBIOS_ESTRATEGIA.md', 'w', encoding='utf-8') as f:
    f.write(content)

print("Entrada añadida correctamente a REGISTRO_CAMBIOS_ESTRATEGIA.md")
