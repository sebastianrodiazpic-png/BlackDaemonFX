# -*- coding: utf-8 -*-
import sys

sys.stdout.reconfigure(encoding='utf-8')

new_entry = """### 2026-11-09 · Optimización Compacta de Tabla en /Strategy-bases para Eliminar Scroll Horizontal · Estado: aplicado sin commit
- **Qué**:
  1. **Eliminación del Scroll Horizontal en la Tabla de Activos (`#winnersTable`)**:
     - Se redujo el ancho excesivo de la última columna `ESTADO`, reemplazando el badge sobredimensionado (`✓ ACTIVO CON CONFLUENCIA TRIPARTITA (+1013.81R · WR 68.13%)` que medía más de 400px de ancho) por un pill institucional compacto: `✓ ACTIVO` (verde) y `⛔ PODADO` (rojo). El detalle cuantitativo completo se preserva de forma accesible mediante el tooltip nativo `title="${it.status}"`.
     - Encabezados compactados y claros: `WIN RATE %` a `WIN RATE`, `TP1 HITS` a `TP1`, `TP2 HITS` a `TP2`, `TP3 HITS` a `TP3`, `TP4 HITS` a `TP4`, `BE SAVES` a `BE`, `PNL NETO ($ USD)` a `PNL NETO ($)`, y `ESTADO EN /INSTRUMENTS` a `ESTADO`.
     - Ajuste de paddings de celdas (`th`: 8px 6px, `td`: 6px 6px) y tipografía equilibrada (10.5px para encabezados y 11.5px para datos numéricos).
     - El ancho total de la tabla se redujo de más de 1,415px a ~780px, encajando de forma natural en cualquier resolución de pantalla y eliminando la necesidad de scroll horizontal.
- **Evidencia**:
  - `tests/test_strategy_bases_tab_and_msnr_cleanup.py` y `tests/test_strategy_bases_5y_all_records.py` pasando al 100% (12/12 tests green).
- **Ficheros modificados**:
  - `dashboard/strategy_bases_page.py`
  - `REGISTRO_CAMBIOS_ESTRATEGIA.md`
- **Interruptores**:
  - N/A.

"""

with open('REGISTRO_CAMBIOS_ESTRATEGIA.md', 'r', encoding='utf-8') as f:
    content = f.read()

target = '## Historial de cambios (más reciente primero)\n\n'
if target not in content:
    target = '## Historial de cambios (m\uFFFDs reciente primero)\n\n'
    if target not in content:
        idx = content.find('## Historial de cambios')
        end_line = content.find('\n\n', idx) + 2
        content = content[:end_line] + new_entry + content[end_line:]
    else:
        content = content.replace(target, target + new_entry, 1)
else:
    content = content.replace(target, target + new_entry, 1)

with open('REGISTRO_CAMBIOS_ESTRATEGIA.md', 'w', encoding='utf-8') as f:
    f.write(content)

print("REGISTRO_CAMBIOS_ESTRATEGIA.md actualizado con éxito.")
