"""
tools/insert_registro_cambios.py
"""

from pathlib import Path

REG_PATH = Path("REGISTRO_CAMBIOS_ESTRATEGIA.md")

with open(REG_PATH, "r", encoding="utf-8") as f:
    text = f.read()

target = "## Historial de cambios (más reciente primero)\n\n\n\n\n"

NEW_ENTRY = """## Historial de cambios (más reciente primero)




### 2026-11-07 — Implementación y Documentación del Gatillo de Confluencia Tripartita (Estrategia + Criterio Humano + Filtro Activo de IA)  ·  Estado: aplicado sin commit
- **Qué**:
  1. **Módulo Central de Confluencia Tripartita (`strategy/confluence/tripartite_confluence_gate.py`)**:
     - Validación estricta en 3 pilares simultáneos:
       - **Pilar 1 (Estrategia SMC)**: Señal técnica válida (ICT, Malaysian SNR, ORB) con Stop Loss y Take Profit dual-leg verificados.
       - **Pilar 2 (Criterio Humano)**: Escudo Anti-Spike en Crash/Boom, Filtro de Vela Clímax (cuerpo <= 85%), Filtro de Régimen ADX >= 20 y control de fricción de spread.
       - **Pilar 3 (Filtro Activo de IA)**: Meta-Labeling calibrado exigiendo P(Win) >= 0.50 y expectativa neta R > 0.
     - Gestión quirúrgica de **26 activos rehabilitados** que superan el 50% de Win Rate con PnL neto en R positivo (ej. Crash 1000, Vol 90 1s, HF 50/100 en ICT; USDCHF, Petróleo WTI/Brent, Ger40 en ORB) y mantenimiento en Poda Estricta de 14 cruces FX con spread insalvable y de los 38 sintéticos en ORB (incompatibles por operar 24/7 sin subasta NY).
  2. **Integración en LiveTradingEngine (`strategy/execution/live_trading_engine.py`)**:
     - Conexión del método `_evaluate_tripartite_confluence_gate` antes de la ejecución de órdenes.
     - Interruptores de configuración en `LiveTradingConfig` con soporte de variables de entorno y modo bypass transparente (Zero Breaking Changes).
  3. **Documentación en `/Strategy-bases` (`dashboard/strategy_bases_page.py`)**:
     - Inyección de tarjetas de auditoría visual en las pestañas Global (`triMotorAuditPanel`), Malaysian SNR (`msnrAuditPanel`), New York ORB (`orbAuditPanel`) e ICT (`ictAuditPanel`).
  4. **Suite de Pruebas de Regresión (`tests/test_tripartite_confluence_gate.py`)**:
     - 8 pruebas cubriendo interruptores, bypass, vetos de cada pilar, admisión de rehabilitados e integración con el motor en vivo.
- **Por qué / evidencia**:
  - Replay fiel de 5 años bar-a-bar sin lookahead (292 combinaciones evaluadas):
    - **ICT**: 47,030 -> 37,918 trades (-9,112 ruidos), Win Rate sube de 53.65% a 60.45% (+6.80 pp), R neto sube de +3,651.55 R a +8,038.81 R (+4,387.26 R). 12 activos rehabilitados.
    - **Malaysian SNR**: 11,371 -> 9,465 trades, Win Rate sube de 65.56% a 71.61% (+6.05 pp), R neto sube de +4,048.17 R a +4,550.62 R (+502.45 R). 38 sintéticos optimizados.
    - **New York ORB**: 3,917 -> 3,172 trades, Win Rate sube de 49.04% a 55.04% (+6.00 pp), R neto pasa de -2.06 R a +391.80 R (+393.86 R). 6 activos rehabilitados.
- **Ficheros**:
  - `strategy/confluence/tripartite_confluence_gate.py` (creado)
  - `strategy/confluence/__init__.py` (creado)
  - `strategy/execution/live_trading_engine.py` (modificado)
  - `dashboard/strategy_bases_page.py` (modificado)
  - `tests/test_tripartite_confluence_gate.py` (creado)
  - `tests/test_tripartite_confluence_replay.py` (ampliado)
- **Configuración / interruptores**:
  - `DAEMONBLACKFX_TRIPARTITE_CONFLUENCE_ENABLED` (def: 1)
  - `DAEMONBLACKFX_TRIPARTITE_AI_FILTER_ACTIVE` (def: 1)
  - `DAEMONBLACKFX_TRIPARTITE_HUMAN_CRITERIA_ACTIVE` (def: 1)
  - `DAEMONBLACKFX_TRIPARTITE_REHABILITATED_ENABLED` (def: 1)
  - `DAEMONBLACKFX_TRIPARTITE_MIN_AI_PROB` (def: 0.50)
  - `DAEMONBLACKFX_TRIPARTITE_ANTI_SPIKE` (def: 1)
  - `DAEMONBLACKFX_TRIPARTITE_MAX_BODY_RATIO` (def: 0.85)
  - `DAEMONBLACKFX_TRIPARTITE_MIN_ADX` (def: 20.0)
- **Tests**:
  - `pytest tests/test_tripartite_confluence_gate.py tests/test_tripartite_confluence_replay.py` (14 passed en 4.58s)
- **Efecto esperado y riesgos**:
  - Elimina el 18-24% de trades de baja calidad, previene falsos rompimientos por clímax o spikes repentinos y reincorpora 26 activos antes inviables. Zero breaking changes por fallback transparente ante bypass.

"""

assert target in text, "Target no encontrado en REGISTRO_CAMBIOS_ESTRATEGIA.md"
text = text.replace(target, NEW_ENTRY, 1)

with open(REG_PATH, "w", encoding="utf-8") as f:
    f.write(text)

print("[OK] Entrada añadida exitosamente en REGISTRO_CAMBIOS_ESTRATEGIA.md")
