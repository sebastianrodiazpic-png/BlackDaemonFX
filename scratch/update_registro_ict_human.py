# -*- coding: utf-8 -*-
with open("REGISTRO_CAMBIOS_ESTRATEGIA.md", "r", encoding="utf-8") as f:
    content = f.read()

target = "## Historial de cambios (más reciente primero)\n"
if target not in content:
    print("ERROR: Target no encontrado")
    exit(1)

new_entry = """## Historial de cambios (más reciente primero)

### 2026-11-09 — Humanización pedagógica de textos en Estrategia ICT (SMC + FVG + Filtro IA)  ·  Estado: aplicado sin commit
- **Qué**:
  1. Transformación de los textos del panel `ictAuditPanel` en `dashboard/strategy_bases_page.py` hacia un enfoque pedagógico, amigable y comprensible para cualquier persona que realice trading.
  2. Sustitución de listas densas de números y métricas aisladas por explicaciones de mecánica de mercado real:
     - Cómo se forman los desequilibrios de precio (Fair Value Gaps) cuando los bancos compran/venden masivamente.
     - Por qué el bot espera con paciencia el retroceso en lugar de perseguir el precio por ansiedad o FOMO.
     - Cómo el modelo de Inteligencia Artificial predictiva (83% de precisión) filtra el 85% de las señales engañosas en rangos sucios.
     - Enfoque horario en sesiones líquidas (Londres para Forex, apertura de Nueva York para Nasdaq/Dow Jones/Oro).
     - La fórmula de 2 órdenes (cobro al 1:1 y paso a Break-Even) para operar con cero estrés y proteger el capital ante regresiones bruscas.
- **Por qué / evidencia**: Solicitud del usuario para hacer los textos totalmente accesibles y comprensibles para traders, manteniendo los datos probados del Replay Fiel de 5 Años (+8,038R y 60.5% acierto).
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
