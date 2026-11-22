import sys
sys.stdout.reconfigure(encoding='utf-8')

new_entry = """### 2026-11-09 — Eliminación de Apartados de Instrumentos Podados y Datasets en /Strategy-bases  ·  Estado: aplicado sin commit
- **Qué**:
  1. `dashboard/strategy_bases_page.py`: Eliminación de la tarjeta visual `<section class="card">... Instrumentos Podados por Estrategia (Poda Preventiva Persistida en /Instruments) ...</section>` (que contenía la tabla `losersTable` y la comparativa de portafolio bruto vs optimizado).
  2. `dashboard/strategy_bases_page.py`: Eliminación de la tarjeta visual `<section class="card">... Datasets y Artefactos Persistidos para Auditoría Independiente ...</section>` (referencias a ficheros locales CSV/JSON).
  3. `dashboard/strategy_bases_page.py`: Adición de salvaguarda `if (!tbody) return;` en la función `renderLosersTable()` en JavaScript para evitar excepciones en consola al no existir el contenedor en el DOM.
  4. Preservación intacta de `WINNERS_DATA` (292 registros de 73 activos x 4 estrategias) y `LOSERS_DATA` en el bloque de scripts, manteniendo 100% compatibles las suites de pruebas y la trazabilidad histórica de 5 años.
- **Por qué / evidencia**: Solicitud explícita del usuario mediante capturas de pantalla para limpiar y simplificar la interfaz visual de `/Strategy-bases`, dejando una vista más directa enfocada en los activos rentables y los fundamentos de ejecución.
- **Ficheros**: `dashboard/strategy_bases_page.py`, `REGISTRO_CAMBIOS_ESTRATEGIA.md`.
- **Configuración / interruptores**: Visual puro; no requiere nuevas variables de entorno.
- **Tests**: `tests/test_strategy_bases_5y_all_records.py` y `tests/test_strategy_bases_tab_and_msnr_cleanup.py` (11 tests pasando; syntax validado con `node --check`).
- **Efecto esperado y riesgos**: Interfaz más limpia sin scroll innecesario ni tablas de auditoría redundantes; cero riesgo operativo.

"""

with open('REGISTRO_CAMBIOS_ESTRATEGIA.md', 'r', encoding='utf-8') as f:
    text = f.read()

target = "## Historial de cambios (más reciente primero)\n\n"
if target in text:
    idx = text.find(target) + len(target)
    updated_text = text[:idx] + new_entry + text[idx:]
    with open('REGISTRO_CAMBIOS_ESTRATEGIA.md', 'w', encoding='utf-8') as f:
        f.write(updated_text)
    print("Added entry to REGISTRO_CAMBIOS_ESTRATEGIA.md successfully.")
else:
    print("Target heading not found!")
