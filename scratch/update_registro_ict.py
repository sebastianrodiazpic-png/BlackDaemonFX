# -*- coding: utf-8 -*-
with open("REGISTRO_CAMBIOS_ESTRATEGIA.md", "r", encoding="utf-8") as f:
    content = f.read()

target = "## Historial de cambios (más reciente primero)\n"
if target not in content:
    print("ERROR: Target no encontrado")
    exit(1)

new_entry = """## Historial de cambios (más reciente primero)

### 2026-11-09 — Corrección de fuga visual de ICT en ORB, humanización y rediseño .daemon-card en Estrategia ICT  ·  Estado: aplicado sin commit
- **Qué**:
  1. Corrección del anidamiento HTML entre `orbAuditPanel` e `ictAuditPanel` en `dashboard/strategy_bases_page.py`: se restauró el `</div>` de cierre de `orbAuditPanel` y se corrigió la etiqueta `<div id="ictAuditPanel" style="display: none; margin-bottom: 24px;">` (que antes carecía del prefijo `<div`, imprimiendo texto plano en pantalla y manteniéndose visible de forma espuria dentro de la vista de ORB).
  2. Rediseño completo de `ictAuditPanel` al formato de cartas coleccionables legendarias `.daemon-card` con doble marco dorado biselado, máscara obsidian de alto contraste y chapas metálicas 3D `BLACKDAEMON FX`.
  3. Humanización integral de textos de la estrategia ICT para cualquier perfil de trader: eliminación de jerga interna de desarrollo (\"consolidación de workers -4 procesos inactivos\", \"pestaña sintéticos\") por explicaciones claras sobre la confluencia entre vacíos de liquidez (FVG M15), Inteligencia Artificial predictiva (83% de precisión), sesión de Londres en Forex y rendimiento sobresaliente en US Tech 100 y Crash 300.
- **Por qué / evidencia**: El usuario reportó que al ver la vista rediseñada de ORB aparecía abajo el bloque antiguo de ICT con la etiqueta HTML rota visible. Al aislar correctamente los contenedores con `display: none` y un balance de divs exacto (0 desbalance), el panel viejo desaparece de la vista de ORB y se muestra únicamente al activar la pestaña de ICT con el nuevo diseño institucional.
- **Ficheros**:
  - `dashboard/strategy_bases_page.py`
  - `REGISTRO_CAMBIOS_ESTRATEGIA.md`
- **Interruptores**: No requiere nuevos interruptores. Sincronizado con `/instruments`.
- **Tests**:
  - `tests/test_strategy_bases_tab_and_msnr_cleanup.py` (6 passed).
  - `tests/test_strategy_bases_5y_all_records.py` (6 passed).
  - Verificación de balance de divs HTML (0 tags desbalanceados).
"""

content = content.replace(target, new_entry, 1)

with open("REGISTRO_CAMBIOS_ESTRATEGIA.md", "w", encoding="utf-8") as f:
    f.write(content)

print("REGISTRO_CAMBIOS_ESTRATEGIA.md actualizado con éxito.")
