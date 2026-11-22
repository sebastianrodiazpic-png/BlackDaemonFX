# -*- coding: utf-8 -*-
import sys

sys.stdout.reconfigure(encoding='utf-8')

new_entry = """### 2026-11-09 · Actualización y Humanización de 'Fundamentos y Reglas de Ejecución' en /Strategy-bases · Estado: aplicado sin commit
- **Qué**:
  1. **Rediseño Completo a Formato Legendario (.daemon-card)**:
     - Reemplazo de las 3 antiguas tarjetas desactualizadas y de bajo contraste (`.strat-card`) por 4 cartas legendarias `.daemon-card` con marco dorado biselado, máscara oscura de alto contraste, acentos de color institucional y chapas metálicas 3D `BLACKDAEMON FX`.
  2. **Incorporación de las 4 Estrategias Implementadas en la Plataforma**:
     - **1. Malaysian SNR Institucional (Alchemist C2)**: 64 pares ganadores en Replay Fiel 5 Años (+3,093.36R netos / 63.8% WR). Reglas humanizadas: Niveles sin ruido en cierres H1, Regla de 2 Toques, Retesteo de quiebre (+4.4R) y Doble Orden 50%/50% a riesgo cero.
     - **2. ORB New York Sweep (Apertura Wall Street)**: 11 activos ganadores (+177.12R netos / 56.5% WR en sesión). Reglas humanizadas: Rango inicial de 15 minutos (09:30-09:45 NY), Barrido obligatorio de trampa (Sweep), Stop Loss al 50% Equilibrium y Poda de sintéticos 24/7.
     - **3. Estrategia ICT con IA (Smart Money Concepts)**: 59 activos ganadores (+8,038.81R netos / 60.5% WR). Reglas humanizadas: Entradas al 50% del Fair Value Gap (M15), Filtro predictivo de IA (83% precisión), Cierre intradía anti-swap y especialidad en sintéticos y metales.
     - **4. Trend Pullback H1/M15 (Continuación Tendencial)**: 30 sintéticos ganadores (+811.45R netos / 50.93% WR). Reglas humanizadas: Dirección obligatoria en H1 con EMA 20/50, Zona de valor con rechazo de mecha, Gatillo en M15 con quiebre estructural y Poda de mercados reales.
  3. **Humanización Total del Lenguaje**:
     - Eliminación de jerga ininteligible (`MSS Body Ratio >= 45%`, `Gating HTF_SWEEP`, `t = +7.51`, `PDH/PDL 0.25xATR`) y sustitución por conceptos comprensibles para cualquier trader: qué busca la estrategia, por qué funciona, cómo entra y cómo protege la cuenta.
  4. **Balance HTML Perfecto**:
     - 500 divs abiertos y 500 divs cerrados (diferencia exacta = 0).
- **Evidencia**:
  - `tests/test_strategy_bases_tab_and_msnr_cleanup.py` y `tests/test_strategy_bases_5y_all_records.py` pasando al 100% (11/11 tests green).
- **Ficheros modificados**:
  - `dashboard/strategy_bases_page.py`
  - `REGISTRO_CAMBIOS_ESTRATEGIA.md`
- **Interruptores**:
  - N/A (Sección de auditoría y documentación visual reactiva).

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
