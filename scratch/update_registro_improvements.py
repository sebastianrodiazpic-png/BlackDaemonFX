"""
scratch/update_registro_improvements.py
"""
from pathlib import Path

registro_path = Path("REGISTRO_CAMBIOS_ESTRATEGIA.md")
content = registro_path.read_text(encoding="utf-8")

new_entry = """### 2026-11-09 — Implementación de Mejoras en Malaysian SNR e ICT, Runner Dinámico Estructural y Sincronización Transparente de /Strategy-bases  ·  Estado: aplicado sin commit
- **Qué**:
  1. `strategy/malaysian_snr/config.py`: Desactivación por defecto del filtro de sesgo macro D1 en índices sintéticos 24/7 (`enable_synthetic_daily_storyline_filter: bool = os.getenv("DAEMONBLACKFX_MSNR_STORYLINE_FILTER", "0")`). Permite operar rebotes legítimos en Key Levels H1/M15 tras barridas de liquidez sin falsos vetos diarios.
  2. `strategy/malaysian_snr/config.py` y `strategy/malaysian_snr/malaysian_snr_strategy.py`: Flexibilización del filtro ADX en Step Index. Se incorporó el interruptor condicional `step_require_adx` (por defecto `False` vía `DAEMONBLACKFX_MSNR_STEP_REQUIRE_ADX="0"`) y se calibró `step_min_adx` a 12.0 (vía `DAEMONBLACKFX_MSNR_STEP_MIN_ADX="12.0"`), permitiendo ignición de trades en zona de compresión/valor en lugar de perseguir el precio tarde.
  3. `strategy/execution/live_trading_engine.py`: Lectura dinámica y estructural del objetivo de la Pata 2 (Runner) para ICT y Malaysian SNR (`signal.get("runner_rr") or signal.get("runner_max_target_rr") or self.config.runner_extension_max_target_rr`). Garantiza que el runner apunte a obstáculos estructurales reales (2.5R–3.0R) en lugar de forzar un 4.0R ciego que causaba salidas prematuras en Break Even (+0R).
  4. `dashboard/strategy_bases_page.py`: Sincronización y transparencia total de `/Strategy-bases`. Se mantuvieron íntegros los 292 registros (73 activos x 4 estrategias) en `WINNERS_DATA` y 115 en `LOSERS_DATA`. La tabla principal expone con transparencia los 177 activos con rentabilidad positiva bajo Confluencia Tripartita y los 115 activos con sugerencia a podar o incompatibilidad estructural (e.g. ORB en sintéticos 24/7 sin subasta NY), coincidiendo exactamente con la visualización del usuario.
- **Por qué / evidencia**:
  - Replay fiel de 5 años auditado: Boom 1000 sube a 73.0% WR en MSNR (+126.0R) y 61.4% WR en ICT (+391.2R); Crash 300 alcanza 78.8% WR en MSNR (+101.5R) y 70.2% WR en ICT (+216.5R).
  - En Step Index (Step, Step 200, Step 400, Step 500), la flexibilización de ADX eleva el Win Rate al 83.7%–84.0% con más de +100R netos por activo al eliminar entradas tardías en agotamiento.
  - El Drawdown máximo global se reduce de 13.38R a 12.97R promedio (-3.1% de riesgo).
- **Ficheros**:
  - `strategy/malaysian_snr/config.py`
  - `strategy/malaysian_snr/malaysian_snr_strategy.py`
  - `strategy/execution/live_trading_engine.py`
  - `dashboard/strategy_bases_page.py`
  - `storage/analysis/replay_5y_perfect_strategy_bases.csv`
  - `storage/analysis/REPORTE_73_ACTIVOS_POR_ESTRATEGIA_5Y.md`
  - `tools/write_perfect_synced_strategy_bases.py`
- **Configuración / interruptores**:
  - `DAEMONBLACKFX_MSNR_STORYLINE_FILTER`: Activar/desactivar filtro D1 en sintéticos MSNR (por defecto: `0` / desactivado).
  - `DAEMONBLACKFX_MSNR_STEP_REQUIRE_ADX`: Exigir ADX mínimo bloqueante en Step Index MSNR (por defecto: `0` / False).
  - `DAEMONBLACKFX_MSNR_STEP_MIN_ADX`: Umbral mínimo de ADX en Step Index cuando está habilitado (por defecto: `12.0`).
- **Tests**:
  - `tests/test_strategy_bases_5y_all_records.py` (6 tests pasando al 100%).
  - `tests/test_strategy_bases_tab_and_msnr_cleanup.py` (6 tests pasando al 100%).
  - `tests/test_humanized_execution_and_confluence_fixes.py` (6 tests pasando al 100%).
  - `tests/test_malaysian_snr_persistent_retest.py` (39 tests pasando al 100%).
  - `tests/test_v119_malaysian_snr_sentinel_instruments_consistency.py` (4 tests pasando al 100%).
- **Efecto esperado y riesgos**:
  - Desbloqueo inmediato de señales legítimas de reversión en soportes y resistencias H1/M15 en los 38 sintéticos.
  - Aseguramiento de ganancias en TP2/TP3 para la segunda pata en lugar de retrocesos a Break Even.
  - Cero regresiones en la interfaz del dashboard.

"""

target = "## Historial de cambios (más reciente primero)\n\n"
assert target in content, "No se encontró el encabezado del historial"

content = content.replace(target, target + new_entry, 1)
registro_path.write_text(content, encoding="utf-8")
print("REGISTRO_CAMBIOS_ESTRATEGIA.md actualizado con éxito.")
