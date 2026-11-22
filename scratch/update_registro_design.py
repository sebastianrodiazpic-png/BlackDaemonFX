import sys
sys.stdout.reconfigure(encoding='utf-8')

new_entry = """### 2026-11-09 — Unificación Visual de /Strategy-bases con el Diseño Global de /dashboard y Conversación a78072a2  ·  Estado: aplicado sin commit
- **Qué**:
  1. `dashboard/strategy_bases_page.py`: Integración del layout unificado `appShell` y barra lateral `brandSidebar` (idéntico a `/dashboard`, `/account` y `/performance` según lo diseñado en la conversación `a78072a2-83cd-4242-9935-27e1da602ecb`), proveyendo navegación sticky, logo institucional, marca `BLACKDAEMONFX`, tags y badge `Daemon Online`.
  2. Encabezado principal `.top` armonizado con título en dos tonos `BLACKDAEMONFX · Bases de las Estrategias Implementadas`, subtítulo descriptivo y badge `DATOS EN VIVO`.
  3. Contenedores de tarjeta (`.card`) con borde sutil dorado (`border: 1px solid rgba(215, 155, 25, 0.35)` y `box-shadow: inset 0 1px 0 rgba(255, 211, 102, 0.03)`).
  4. Rediseño fiel de la tabla canónica `#winnersTable` coincidiendo exactamente con las capturas provistas por el usuario:
     - Cabecera de columnas en mayúsculas doradas (`color: #f5bd36`, `font-weight: 800`, `letter-spacing: 0.05em`).
     - Badges de estrategia con contorno semántico píldora (`Malaysian SNR` en verde, `ICT Sabri Malle` en cyan, `Trend Pullback` en morado, `ORB New York` en ámbar).
     - Columnas de impactos TP1, TP2, TP3 y TP4 unificadas en color cyan (`#38bdf8`), columna `BE SAVES` en ámbar (`#f5bd36`) y PnL neto en verde positivo (`#00db79`).
     - Badges de estado en `/instruments` con diseño de píldora redondeada (`✓ Activo con Confluencia Tripartita` y `⛔ Incompatible (Sintético sin sesión)`).
     - Barra de filtro superior idéntica a las capturas: `FILTRO DE ESTADO: [🔘 📜 Ver todos los activos (Rentables + Podados)] [⚪ ✓ Solo Activos Rentables] [⚪ ⛔ Solo Podadas]`.
     - Cabecera de la sección de Fundamentos unificada con badge lateral `Arquitectura Institucional BlackDaemonFX - Tri-Motor Staging`.
  5. Limpieza de saltos de línea cuádruples redundantes, optimizando la legibilidad y peso del archivo.
- **Por qué / evidencia**: Requerimiento del usuario para preservar la identidad visual unificada del dashboard acordada previamente en la conversación `a78072a2-83cd-4242-9935-27e1da602ecb`, sin perder ni alterar los 292 registros de replay de 5 años ni los datos mejorados de Crash 300 / Boom 1000.
- **Ficheros**: `dashboard/strategy_bases_page.py`, `REGISTRO_CAMBIOS_ESTRATEGIA.md`.
- **Configuración / interruptores**: Visual puro; preserva compatibilidad con `DAEMONBLACKFX_SHOW_MSNR_RUNTIME_SETTINGS`.
- **Tests**: `tests/test_strategy_bases_5y_all_records.py` y `tests/test_strategy_bases_tab_and_msnr_cleanup.py` (11 tests pasando; syntax validado con `node --check`).
- **Efecto esperado y riesgos**: Experiencia de usuario consistente entre `/dashboard`, `/account`, `/instruments` y `/Strategy-bases`; cero riesgo de regresión operativa o de datos.

"""

with open('REGISTRO_CAMBIOS_ESTRATEGIA.md', 'r', encoding='utf-8') as f:
    text = f.read()

target = "## Historial de cambios (más reciente primero)\n\n"
if target in text:
    idx = text.find(target) + len(target)
    updated_text = text[:idx] + new_entry + text[idx:]
    with open('REGISTRO_CAMBIOS_ESTRATEGIA.md', 'w', encoding='utf-8') as f:
        f.write(updated_text)
    print("Pretended entry to REGISTRO_CAMBIOS_ESTRATEGIA.md successfully.")
else:
    print("Target heading not found!")
