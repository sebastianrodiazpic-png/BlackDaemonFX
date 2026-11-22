entry = """### 2026-11-09 — Corrección de Tipado Polimórfico en Gatillo de Confluencia Tripartita (Desbloqueo de Trades con Criterio Humano)  ·  Estado: aplicado sin commit
- **Qué**:
  1. `strategy/confluence/tripartite_confluence_gate.py`: Soporte polimórfico robusto para `human_criteria_decision` tanto si se recibe como objeto de clase como si se recibe como diccionario serializado (`isinstance(human_criteria_decision, dict)`). Se extraen limpiamente `allowed`, `score` y `reason`.
  2. `strategy/confluence/tripartite_confluence_gate.py`: Soporte polimórfico en `ai_evaluation` para leer `probability` y `net_expectancy_r` tanto de diccionarios como de objetos.
  3. `tests/test_tripartite_confluence_gate.py`: Incorporación de pruebas unitarias `test_polymorphic_human_criteria_dict_and_ai_compensation` que validan la aprobación por compensación con score humano >= 80.0 pts (caso real auditado de 82.0 pts en Volatility 250 (1s) Index), el veto estricto cuando el score es inferior al umbral, y el veto inmediato ante `allowed=False`.
- **Por qué / evidencia**: Auditoría forense de la base de datos viva (`AppData/Local/BlackDaemonFx/trading_bot.sqlite3`) identificó que en `live_trading_engine.py` la decisión se almacena en la señal como diccionario (`signal["human_criteria"] = decision.to_dict()`). Al evaluar `hasattr(dict, "score")`, devolvía `False`, dejando el score en el fallback estático de 75.0 pts y provocando falsos vetos sistemáticos con `VETO_INSUFFICIENT_CONFLUENCE_WITHOUT_AI` a señales con Criterio Humano de alta convicción (82.0 pts GRADE_A_ELITE).
- **Ficheros**: `strategy/confluence/tripartite_confluence_gate.py`, `tests/test_tripartite_confluence_gate.py`, `REGISTRO_CAMBIOS_ESTRATEGIA.md`.
- **Configuración / interruptores**: Mantiene 100% compatibles los interruptores existentes (`DAEMONBLACKFX_TRIPARTITE_CONFLUENCE_ENABLED`, `DAEMONBLACKFX_TRIPARTITE_HUMAN_CRITERIA_ACTIVE`, etc.).
- **Tests**: `tests/test_tripartite_confluence_gate.py` (10 tests pasando al 100%), `tests/test_tripartite_confluence_replay.py` (7 tests), `tests/test_humanized_execution_and_confluence_fixes.py` (6 tests).
- **Efecto esperado y riesgos**: Desbloqueo inmediato de entradas de trading algorítmico cuando el Criterio Humano califica con alta convicción (>= 80.0 pts) sin depender de inferencia IA; cero regresiones.

"""

with open('REGISTRO_CAMBIOS_ESTRATEGIA.md', 'r', encoding='utf-8') as f:
    text = f.read()

target = '## Historial de cambios (más reciente primero)'
idx = text.find(target)
if idx != -1:
    pos = idx + len(target)
    # look for next newline
    while pos < len(text) and text[pos] in ('\r', '\n'):
        pos += 1
    new_text = text[:pos] + entry + text[pos:]
    with open('REGISTRO_CAMBIOS_ESTRATEGIA.md', 'w', encoding='utf-8') as f:
        f.write(new_text)
    print("Updated successfully")
else:
    print("Target not found")
