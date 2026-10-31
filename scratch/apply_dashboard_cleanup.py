import os
import tempfile

target_file = r'dashboard\realtime_dashboard.py'

with open(target_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Definir _RETIRED_WORKER_PROFILES y expandir _is_retired_worker_profile
old_retired = '''def _is_retired_worker_profile(profile):
   """Identifica perfiles cuya estrategia ya no forma parte del daemon."""
   return str(profile or "").upper().startswith("SCALP_")'''

new_retired = '''_RETIRED_WORKER_PROFILES = {
    "CARRY",
    "DRIFT",
    "GOLD",
    "GOLD_QUARTERS",
    "MSNR",
    "NIGHT",
    "RSI2",
    "FLIP",
    "IDX_OPEN",
    "V53_PROBE",
}


def _is_retired_worker_profile(profile: str | None) -> bool:
    """Identifica perfiles cuya estrategia ya no forma parte del daemon o fue retirada."""
    if os.getenv("DAEMONBLACKFX_RETIRED_WORKERS_FILTER", "1").lower() in ("0", "false", "no"):
        return False
    prof = str(profile or "").strip().upper()
    if not prof:
        return False
    if prof.startswith("SCALP_"):
        return True
    return prof in _RETIRED_WORKER_PROFILES'''

assert old_retired in content, "old_retired snippet not found!"
content = content.replace(old_retired, new_retired)

# 2. Eliminar gold_cuartos del catálogo de instrumentos
old_gold_cat = '''        if "gold_cuartos_xauusd" not in cat_keys:
            catalog.append({"category": "gold_cuartos_xauusd", "selection_profile": "GOLD", "label": "Oro Cuartos (XAUUSD)", "symbols": ["XAUUSD", "XAUUSDmicro"]})
        if "gold_cuartos_xagusd" not in cat_keys:
            catalog.append({"category": "gold_cuartos_xagusd", "selection_profile": "GOLD", "label": "Plata Cuartos (XAGUSD)", "symbols": ["XAGUSD", "XAGUSDmicro"]})'''

new_gold_cat = '''        # Workers retirados: gold_cuartos eliminado del catálogo dinámico (cubierto activamente por ICT y ORB).'''

assert old_gold_cat in content, "old_gold_cat snippet not found!"
content = content.replace(old_gold_cat, new_gold_cat)

# 3. Limpiar Matriz Centinela: cambiar título y reemplazar botón GOLD_QUARTERS por TREND_PULLBACK
old_matrix_header = '''                <div class="label" style="color: var(--gold2); font-weight: 800; font-size: 13px;">Matriz Centinela Multiestrategia (ICT · Malaysian SNR · ORB · Gold Quarters)</div>
                <div class="sub">
                  Monitoreo centinela unificado en tiempo real: Estrategia ICT · Malaysian SNR (Break/Retest/ADX) · ORB (Apertura NY) · Gold Quarters
                </div>'''

new_matrix_header = '''                <div class="label" style="color: var(--gold2); font-weight: 800; font-size: 13px;">Matriz Centinela Multiestrategia (ICT · Malaysian SNR · ORB · Trend Pullback)</div>
                <div class="sub">
                  Monitoreo centinela unificado en tiempo real: Estrategia ICT · Malaysian SNR (Break/Retest/ADX) · ORB (Apertura NY) · Trend Pullback (>51% WR)
                </div>'''

assert old_matrix_header in content, "old_matrix_header snippet not found!"
content = content.replace(old_matrix_header, new_matrix_header)

old_matrix_btn = '''              <button class="matrixTabBtn" data-filter="ORB" onclick="setMatrixFilter('ORB')">ORB NY</button>
              <button class="matrixTabBtn" data-filter="GOLD_QUARTERS" onclick="setMatrixFilter('GOLD_QUARTERS')">GOLD QUARTERS</button>
              <button class="matrixTabBtn" data-filter="ACTIVE" onclick="setMatrixFilter('ACTIVE')" style="color: #60a5fa;">🔵 ACTIVAS</button>'''

new_matrix_btn = '''              <button class="matrixTabBtn" data-filter="ORB" onclick="setMatrixFilter('ORB')">ORB NY</button>
              <button class="matrixTabBtn" data-filter="TREND_PULLBACK" onclick="setMatrixFilter('TREND_PULLBACK')" style="color: #c084fc;">TREND PULLBACK</button>
              <button class="matrixTabBtn" data-filter="ACTIVE" onclick="setMatrixFilter('ACTIVE')" style="color: #60a5fa;">🔵 ACTIVAS</button>'''

assert old_matrix_btn in content, "old_matrix_btn snippet not found!"
content = content.replace(old_matrix_btn, new_matrix_btn)

# 4. Frontend JS visibleWorkers: filtrar trabajadores retirados
old_visible_workers = '''          function visibleWorkers(s) {
            return (s.worker_states || []).filter(
              (w) => !['FLIP', 'IDX_OPEN'].includes(String(w.bot_profile || '').toUpperCase()),
            );
          }'''

new_visible_workers = '''          const RETIRED_WORKER_PROFILES = new Set([
            'FLIP', 'IDX_OPEN', 'CARRY', 'DRIFT', 'GOLD', 'GOLD_QUARTERS', 'MSNR', 'NIGHT', 'RSI2', 'V53_PROBE'
          ]);
          function visibleWorkers(s) {
            return (s.worker_states || []).filter(
              (w) => !RETIRED_WORKER_PROFILES.has(String(w.bot_profile || '').toUpperCase()),
            );
          }'''

assert old_visible_workers in content, "old_visible_workers snippet not found!"
content = content.replace(old_visible_workers, new_visible_workers)

# 5. Orden de workers en front
old_order = '''            const order = [
              'BOOM', 'CRASH', 'STEP', 'JUMP',
              'VOLATILITY', 'VOLATILITY_1', 'VOLATILITY_2', 'VOLATILITY_3', 'VOLATILITY_4',
              'FOREX', 'FOREX_1', 'FOREX_2', 'FOREX_3', 'FOREX_4',
              'ICT', 'MALAYSIAN_SNR', 'ORB'
            ];'''

new_order = '''            const order = [
              'BOOM', 'CRASH', 'STEP', 'JUMP',
              'VOLATILITY', 'VOLATILITY_1', 'VOLATILITY_2', 'VOLATILITY_3', 'VOLATILITY_4',
              'FOREX', 'FOREX_1', 'FOREX_2', 'FOREX_3', 'FOREX_4',
              'ICT', 'MALAYSIAN_SNR', 'ORB', 'TREND_PULLBACK'
            ];'''

assert old_order in content, "old_order snippet not found!"
content = content.replace(old_order, new_order)

# 6. DEFAULT_PRIORITIZED_SYMBOLS: no agregar workers retirados
old_prioritized_retired = '''# Worker NIGHT (sesgo nocturno, 21-oct-2026): activos validados y podados.
DEFAULT_PRIORITIZED_SYMBOLS["NIGHT"] = ["US SP 500", "US Tech 100"]
# Worker DRIFT (ruptura tras compresión, 21-oct-2026): los tres Drift Switch validados en el replay.
# Worker RSI2 (RSI(2) diario de Connors, 21-oct-2026): los 5 índices US validados en el replay.
# Worker CARRY (carry Forex G10, 24-oct-2026): los 28 pares G10; la estrategia elige cada mes los 3 de mayor carry.
DEFAULT_PRIORITIZED_SYMBOLS["CARRY"] = list(__import__("strategy.fx_carry.carry_strategy", fromlist=["x"]).CARRY_DEFAULT_SYMBOLS)
DEFAULT_PRIORITIZED_SYMBOLS["RSI2"] = ["US SP 500", "US Tech 100", "Wall Street 30", "US Small Cap 2000", "US Mid Cap 400"]
DEFAULT_PRIORITIZED_SYMBOLS["DRIFT"] = ["Drift Switch Index 10", "Drift Switch Index 20", "Drift Switch Index 30"]
NIGHT_PRUNED_INFO = {
    "Wall Street 30": "PODA PREVENTIVA: sesgo nocturno neto ≈ 0 en el replay (spread y swap se lo comen).",
}'''

new_prioritized_retired = '''# Workers retirados (NIGHT, DRIFT, RSI2, CARRY): removidos de DEFAULT_PRIORITIZED_SYMBOLS activos.
NIGHT_PRUNED_INFO = {
    "Wall Street 30": "PODA PREVENTIVA: sesgo nocturno neto ≈ 0 en el replay (spread y swap se lo comen).",
}'''

assert old_prioritized_retired in content, "old_prioritized_retired snippet not found!"
content = content.replace(old_prioritized_retired, new_prioritized_retired)

# Guardar atómicamente
dir_name = os.path.dirname(os.path.abspath(target_file))
with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, encoding="utf-8") as tf:
    tf.write(content)
    tmp_path = tf.name

os.replace(tmp_path, target_file)
print("SUCCESS: dashboard/realtime_dashboard.py updated cleanly!")
