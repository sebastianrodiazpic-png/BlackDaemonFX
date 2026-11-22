# -*- coding: utf-8 -*-
import sys

sys.stdout.reconfigure(encoding='utf-8')

new_entry = """### 2026-11-09 · Eliminación y Purga de los 38 Registros Incompatibles en /Strategy-bases · Estado: aplicado sin commit
- **Qué**:
  1. **Purga de los 38 Registros Incompatibles en Datasets Embebidos**:
     - Eliminados de `WINNERS_DATA` y `LOSERS_DATA` los 38 registros de ORB New York sobre índices sintéticos 24/7 de Deriv que tenían 0 trades y estado `"Incompatible (Sintético sin sesión)"`.
     - `WINNERS_DATA` pasa de 292 a **254 registros**, todos con histórico real de operaciones auditadas en el Replay Fiel de 5 Años (211 rentables con WR ≥ 50% y 43 podados con WR < 50%).
     - `LOSERS_DATA` pasa de 81 a **43 registros** (únicamente activos efectivamente evaluados pero con baja expectativa o spread adverso).
     - Ranks de la tabla reclasificados consecutivamente del 1 al 254.
  2. **Armonización de Badges, Textos y Contadores en el Frontend**:
     - Pestaña global actualizada a `🌐 Todas las Estrategias (177 Rentables / 254 Eval · Replay 5A)`.
     - Tarjeta KPI 1 actualizada a `71,962 trades evaluados (177 Activos Rentables / 254 Evaluados)`.
     - Paneles de Tri-Motor y ORB New York limpios de menciones a "38 incompatibles" o "115 podados / incompatibles" (actualizado a 35 activos con sesión física NY en ORB y 77 podados globales en Tri-Motor).
  3. **Actualización de Suite de Tests**:
     - `tests/test_strategy_bases_tab_and_msnr_cleanup.py`: conteos actualizados a 254 ganadores y 43 perdedores.
     - `tests/test_strategy_bases_5y_all_records.py`: adaptado a 254 registros (73 en MSNR, 73 en ICT, 73 en Trend Pullback, 35 en ORB) y nuevo test `test_no_incompatible_or_zero_trade_records` que valida que el 100% de los registros tienen operaciones reales (`trades > 0`) y cero registros incompatibles.
- **Evidencia**:
  - `tests/test_strategy_bases_tab_and_msnr_cleanup.py` y `tests/test_strategy_bases_5y_all_records.py` pasando al 100% (12/12 tests green).
- **Ficheros modificados**:
  - `dashboard/strategy_bases_page.py`
  - `tests/test_strategy_bases_tab_and_msnr_cleanup.py`
  - `tests/test_strategy_bases_5y_all_records.py`
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
