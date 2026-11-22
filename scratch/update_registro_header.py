# -*- coding: utf-8 -*-
with open("REGISTRO_CAMBIOS_ESTRATEGIA.md", "r", encoding="utf-8") as f:
    content = f.read()

target = "## Historial de cambios (más reciente primero)\n"
if target not in content:
    print("ERROR: Target no encontrado")
    exit(1)

new_entry = """## Historial de cambios (más reciente primero)

### 2026-11-09 — Unificación de Header institucional en Dashboard principal (`/`)  ·  Estado: aplicado sin commit
- **Qué**:
  1. Rediseño del header principal (`.top`) en `dashboard/realtime_dashboard.py` para replicar con exactitud el patrón visual institucional de `/instruments`:
     - Título: `BLACKDAEMONFX · Control operativo` con `BLACKDAEMON` en blanco `#ffffff` (font-weight: 800), `FX` resaltado en dorado `#f6cb57`, separador centrado y nombre de sección en blanco.
     - Subtítulo: `ESTRATEGIA · DISCIPLINA · RESULTADOS · Control operativo en tiempo real · Conectado al motor` con tipografía limpia en 12px y espaciado institucional.
     - Divisoria dorada: `border-bottom: 1px solid rgba(91, 69, 20, 0.4)` con padding inferior calibrado a 12px.
     - Píldora de estado (`.badge`): Formato redondeado con borde dorado `#725116`, fondo obsidian `#0d1214`, texto dorado `#ffd465` en mayúsculas `DATOS EN VIVO` y resplandor perimetral dorado sutil.
  2. En Javascript, se optimizó la actualización dinámica de `$('status')` para preservar la píldora compacta `DATOS EN VIVO` / `CONECTADO` / `SIN CONEXIÓN`, desplazando los metadatos de versión y timestamp al tooltip `title` nativo.
- **Por qué / evidencia**: Solicitud del usuario para estandarizar la cabecera superior en todas las páginas, comenzando por el Dashboard principal.
- **Ficheros**:
  - `dashboard/realtime_dashboard.py`
  - `REGISTRO_CAMBIOS_ESTRATEGIA.md`
- **Interruptores**: No requiere interruptores.
- **Tests**:
  - `tests/test_dashboard_cleanup_retired_workers.py` (5 passed).
  - `tests/test_dashboard_front_performance.py` (8 passed).
  - `tests/test_strategy_bases_tab_and_msnr_cleanup.py` (6 passed).
"""

content = content.replace(target, new_entry, 1)

with open("REGISTRO_CAMBIOS_ESTRATEGIA.md", "w", encoding="utf-8") as f:
    f.write(content)

print("REGISTRO_CAMBIOS_ESTRATEGIA.md actualizado con éxito.")
