# -*- coding: utf-8 -*-
import sys

sys.stdout.reconfigure(encoding='utf-8')

new_entry = """### 2026-11-09 · Restauración y Reaplicación Integral del Rediseño Legendario en /Strategy-bases · Estado: aplicado sin commit
- **Qué**:
  1. **Header Institucional Unificado y Sidebar Persistente**:
     - Estructura `appShell` con `brandSidebar` fija en 270px (logo oficial, navegación y estado `● Daemon Online`).
     - Encabezado unificado idéntico al Dashboard: `BLACKDAEMONFX · Bases de Estrategias` con `FX` en dorado `#f6cb57`, texto en blanco `#ffffff`, subtítulo institucional en mayúsculas `ESTRATEGIA · DISCIPLINA · RESULTADOS · Evidencia Cuantitativa de Replay 5 Años`, píldora `.badge` dorada `DATOS AUDITADOS` y divisoria dorada `border-bottom: 1px solid rgba(91, 69, 20, 0.4)`.
  2. **Tarjetas Legendarias (.daemon-card)**:
     - 4 Tarjetas superiores de Tri-Motor (ICT, Malaysian SNR C2, ORB NY Sweep, Risk & Capital Shield) con marco dorado biselado, máscara oscura de alto contraste y chapas metálicas 3D `BLACKDAEMON FX`.
     - 6 Tarjetas KPI inferiores rediseñadas con estilo legendario (.daemon-card) y valores auditados del Replay Fiel 5 Años (71,962 trades, 44,834 TP1, 25,107 TP2, 16,140 TP3/TP4, 19,727 BE, +$1,387,540.00 retorno neto).
  3. **Humanización Integral de los 4 Paneles de Auditoría**:
     - **Malaysian SNR**: 4 subtarjetas humanizadas (Identificación de Niveles Clave, Asegurar Ganancias vs Ratios Imposibles, Mejor Forma de Entrar, Activos Ganadores y Pares Descartados).
     - **ORB New York Sweep**: 3 subtarjetas humanizadas (5 Activos Élite, 3 Activos Rescatados, 8 Activos Descartados) con badges y chapas doradas.
     - **ICT**: 4 subtarjetas humanizadas (Sintéticos Deriv 33 Ganadores, Divisas Forex Sesión Londres, Índices Bursátiles y Metales, Filtro de Ruido y Protección).
     - **Trend Pullback**: 4 subtarjetas humanizadas (Filtro Tendencia H1 EMA 20/50, Gatillo M15 Quiebre Swing, Rendimiento 5 Años en Sintéticos, Poda de Mercados Reales).
  4. **Cajas de Objetivos TP (.tp-bar-box)**:
     - Fondo obsidian limpio de alto contraste sin gráfico de fuego para garantizar 100% de legibilidad.
  5. **Integridad Estructural HTML**:
     - Balance perfecto de etiquetas: 456 divs abiertos y 456 cerrados (diferencia exacta = 0).
- **Evidencia**:
  - `tests/test_strategy_bases_tab_and_msnr_cleanup.py` y `tests/test_strategy_bases_5y_all_records.py` pasando al 100% (11/11 tests green).
- **Ficheros modificados**:
  - `dashboard/strategy_bases_page.py`
  - `REGISTRO_CAMBIOS_ESTRATEGIA.md`
- **Interruptores**:
  - `DAEMONBLACKFX_SHOW_MSNR_RUNTIME_SETTINGS=0` (panel runtime deshabilitado por defecto pero restaurable vía env var).

"""

with open('REGISTRO_CAMBIOS_ESTRATEGIA.md', 'r', encoding='utf-8') as f:
    content = f.read()

target = '## Historial de cambios (más reciente primero)\n\n'
if target not in content:
    target = '## Historial de cambios (m\uFFFDs reciente primero)\n\n'
    if target not in content:
        # Fallback to search
        idx = content.find('## Historial de cambios')
        end_line = content.find('\n\n', idx) + 2
        content = content[:end_line] + new_entry + content[end_line:]
    else:
        content = content.replace(target, target + new_entry, 1)
else:
    content = content.replace(target, target + new_entry, 1)

with open('REGISTRO_CAMBIOS_ESTRATEGIA.md', 'w', encoding='utf-8') as f:
    f.write(content)

print("Registro actualizado con éxito.")
