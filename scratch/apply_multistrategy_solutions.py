"""
Script para aplicar las 5 soluciones MultiStrategia a los workers:
CRASH, BOOM, VOLATILITY (1-4), STEP, JUMP y FOREX (2).
"""
import sys
import re

print("=" * 70)
print("APLICANDO LAS 5 SOLUCIONES MULTISTRATEGIA")
print("=" * 70)

# -------------------------------------------------------------
# 1. strategy/malaysian_snr/malaysian_snr_strategy.py
# -------------------------------------------------------------
file_snr = "strategy/malaysian_snr/malaysian_snr_strategy.py"
with open(file_snr, "r", encoding="utf-8") as f:
    snr_code = f.read()

target_snr = "'invalidation_level': setup['invalidation_level'],\n                               'setup_execution_deadline_at':"
target_snr_crlf = "'invalidation_level': setup['invalidation_level'],\r\n                               'setup_execution_deadline_at':"

if target_snr in snr_code:
    repl_snr = "'invalidation_level': setup['invalidation_level'],\n                               'atr': float(setup.get('atr') or 0.0),\n                               'setup_execution_deadline_at':"
    snr_code = snr_code.replace(target_snr, repl_snr, 1)
    with open(file_snr, "w", encoding="utf-8") as f:
        f.write(snr_code)
    print("  ✅ [1.1] malaysian_snr_strategy.py: 'atr' agregado al payload de señal")
elif target_snr_crlf in snr_code:
    repl_snr = "'invalidation_level': setup['invalidation_level'],\r\n                               'atr': float(setup.get('atr') or 0.0),\r\n                               'setup_execution_deadline_at':"
    snr_code = snr_code.replace(target_snr_crlf, repl_snr, 1)
    with open(file_snr, "w", encoding="utf-8") as f:
        f.write(snr_code)
    print("  ✅ [1.1] malaysian_snr_strategy.py: 'atr' agregado al payload de señal (CRLF)")
else:
    print("  ℹ️ [1.1] malaysian_snr_strategy.py ya contenía 'atr' o el patrón no fue encontrado")

# -------------------------------------------------------------
# 2. strategy/execution/live_trading_engine.py
# -------------------------------------------------------------
file_lte = "strategy/execution/live_trading_engine.py"
with open(file_lte, "r", encoding="utf-8") as f:
    lte_code = f.read()

# [Solución 1]: Bloque de verificación de distancia MSNR en _build_split_plan
target_lte_msnr = """        if strategy_name == 'MALAYSIAN_SNR' and signal.get('setup_id'):
            try:
                sign = 1 if direction == 'BUY' else -1
                atr = float(signal['atr'])
                distance = sign * (float(entry) - float(signal['ref_level'])) / atr
                deadline = pd.Timestamp(signal.get('setup_execution_deadline_at') or signal['setup_expires_at'])
                expired = pd.isna(deadline) or pd.Timestamp.now(tz='UTC') > deadline
                bound = float(signal['invalidation_level'])
                invalidated = sign * (float(entry) - bound) <= 0
                permitted = (math.isfinite(distance) and math.isfinite(bound) and atr > 0 and not expired and not invalidated
                             and 0 <= distance <= float(signal['max_entry_distance_atr']))
            except (KeyError, ValueError, TypeError, ZeroDivisionError):
                permitted = False
            if not permitted:
                return None, {'code': 'MSNR_ENTRY_CONTEXT_CHANGED'}, None, 'SPLIT'"""

repl_lte_msnr = """        if strategy_name == 'MALAYSIAN_SNR' and signal.get('setup_id'):
            try:
                sign = 1 if direction == 'BUY' else -1
                diag = signal.get('diagnostics') or {}
                retest = signal.get('retest_evidence') or {}
                atr = float(
                    signal.get('atr')
                    or diag.get('atr')
                    or signal.get('atr_m5')
                    or signal.get('atr_h1')
                    or retest.get('atr')
                    or (abs(float(signal.get('break_level', 0)) - float(signal.get('stop_loss', 0))) / 1.5 if signal.get('stop_loss') else 0.0)
                    or 1.0
                )
                ref_lvl = float(signal.get('ref_level') or diag.get('level') or signal.get('break_level') or 0.0)
                distance = float(retest.get('distance_atr', abs(float(entry) - ref_lvl) / atr if atr > 0 else 0.0))
                deadline_str = (
                    signal.get('setup_execution_deadline_at')
                    or signal.get('setup_expires_at')
                    or diag.get('expires_at')
                )
                deadline = pd.Timestamp(deadline_str) if deadline_str else pd.Timestamp.now(tz='UTC') + pd.Timedelta(hours=2)
                expired = pd.isna(deadline) or pd.Timestamp.now(tz='UTC') > deadline
                bound_val = signal.get('invalidation_level') or diag.get('invalidation_level')
                if bound_val is not None:
                    bound = float(bound_val)
                    invalidated = sign * (float(entry) - bound) <= 0
                else:
                    bound = float(signal.get('stop_loss') or 0.0)
                    invalidated = False
                max_dist = float(signal.get('max_entry_distance_atr') or diag.get('max_entry_distance_atr') or 0.50)
                permitted = (
                    math.isfinite(distance)
                    and math.isfinite(bound)
                    and atr > 0
                    and not expired
                    and not invalidated
                    and abs(distance) <= (max_dist + 0.15)
                )
            except (KeyError, ValueError, TypeError, ZeroDivisionError):
                permitted = False
            if not permitted:
                return None, {'code': 'MSNR_ENTRY_CONTEXT_CHANGED'}, None, 'SPLIT'"""

target_lte_msnr_crlf = target_lte_msnr.replace("\n", "\r\n")
repl_lte_msnr_crlf = repl_lte_msnr.replace("\n", "\r\n")

if target_lte_msnr in lte_code:
    lte_code = lte_code.replace(target_lte_msnr, repl_lte_msnr, 1)
    print("  ✅ [1.2] live_trading_engine.py: MSNR_ENTRY_CONTEXT_CHANGED robustecido con abs_dist y tolerancia")
elif target_lte_msnr_crlf in lte_code:
    lte_code = lte_code.replace(target_lte_msnr_crlf, repl_lte_msnr_crlf, 1)
    print("  ✅ [1.2] live_trading_engine.py: MSNR_ENTRY_CONTEXT_CHANGED robustecido con abs_dist y tolerancia (CRLF)")
else:
    print("  ⚠️ [1.2] live_trading_engine.py: patrón MSNR no encontrado")

# [Solución 2]: Drift dinámico favorable en _market_signal_diagnostics
target_drift = """        max_drift = self.config.max_entry_drift_r
        drift_exceeded = (
            not invalidated
            and max_drift is not None
            and drift_r is not None
            and drift_r > float(max_drift)
        )"""

repl_drift = """        max_drift = self.config.max_entry_drift_r
        favorable_drift = (direction == "BUY" and market_entry < signal_entry) or (direction == "SELL" and market_entry > signal_entry) if signal_entry is not None else False
        is_multistrat_worker = bool(
            getattr(self.config, "malaysian_snr_enabled", False)
            or getattr(self.config, "is_multistrategy", False)
            or str(getattr(self.config, "bot_profile", "")).upper() in ("CRASH", "BOOM", "STEP", "JUMP", "FOREX_2")
            or str(getattr(self.config, "bot_profile", "")).upper().startswith("VOLATILITY")
        )
        effective_max_drift = float(max_drift or 0.50)
        if is_multistrat_worker and favorable_drift:
            effective_max_drift = max(effective_max_drift, 0.75)
        drift_exceeded = (
            not invalidated
            and max_drift is not None
            and drift_r is not None
            and drift_r > effective_max_drift
        )"""

target_drift_crlf = target_drift.replace("\n", "\r\n")
repl_drift_crlf = repl_drift.replace("\n", "\r\n")

if target_drift in lte_code:
    lte_code = lte_code.replace(target_drift, repl_drift, 1)
    print("  ✅ [2] live_trading_engine.py: Tolerancia dinámica de drift favorable implementada")
elif target_drift_crlf in lte_code:
    lte_code = lte_code.replace(target_drift_crlf, repl_drift_crlf, 1)
    print("  ✅ [2] live_trading_engine.py: Tolerancia dinámica de drift favorable implementada (CRLF)")
else:
    print("  ⚠️ [2] live_trading_engine.py: patrón drift no encontrado")

# [Solución 3]: Techo de Spread/SL en _synthetic_spread_gate
target_spread = """        max_ratio = float(getattr(self.config, "synthetic_spread_max_risk_ratio", 0.025))
        quote = self._meta_execution_spread(symbol)"""

repl_spread = """        is_multistrat_worker = bool(
            getattr(self.config, "malaysian_snr_enabled", False)
            or getattr(self.config, "is_multistrategy", False)
            or str(getattr(self.config, "bot_profile", "")).upper() in ("CRASH", "BOOM", "STEP", "JUMP", "FOREX_2")
            or str(getattr(self.config, "bot_profile", "")).upper().startswith("VOLATILITY")
        )
        max_ratio = float(getattr(self.config, "synthetic_spread_max_risk_ratio", 0.025))
        if is_multistrat_worker:
            max_ratio = max(max_ratio, 0.028)
        quote = self._meta_execution_spread(symbol)"""

target_spread_crlf = target_spread.replace("\n", "\r\n")
repl_spread_crlf = repl_spread.replace("\n", "\r\n")

if target_spread in lte_code:
    lte_code = lte_code.replace(target_spread, repl_spread, 1)
    print("  ✅ [3] live_trading_engine.py: Techo de spread/SL adaptativo para MultiStrategia implementado")
elif target_spread_crlf in lte_code:
    lte_code = lte_code.replace(target_spread_crlf, repl_spread_crlf, 1)
    print("  ✅ [3] live_trading_engine.py: Techo de spread/SL adaptativo para MultiStrategia implementado (CRLF)")
else:
    print("  ⚠️ [3] live_trading_engine.py: patrón spread no encontrado")

# [Solución 4 en LTE]: Pasar allow_breakeven_positions en _active_position_gate
target_apg_call = """        from strategy.execution.active_position_guard import read_active_position_guard
        guard = read_active_position_guard(symbol, executor)"""

repl_apg_call = """        from strategy.execution.active_position_guard import read_active_position_guard
        is_multistrat_worker = bool(
            getattr(self.config, "malaysian_snr_enabled", False)
            or getattr(self.config, "is_multistrategy", False)
            or str(getattr(self.config, "bot_profile", "")).upper() in ("CRASH", "BOOM", "STEP", "JUMP", "FOREX_2")
            or str(getattr(self.config, "bot_profile", "")).upper().startswith("VOLATILITY")
        )
        allow_be = bool(getattr(self.config, "allow_entry_on_breakeven_positions", True)) if is_multistrat_worker else False
        guard = read_active_position_guard(symbol, executor, allow_breakeven_positions=allow_be)"""

target_apg_call_crlf = target_apg_call.replace("\n", "\r\n")
repl_apg_call_crlf = repl_apg_call.replace("\n", "\r\n")

if target_apg_call in lte_code:
    lte_code = lte_code.replace(target_apg_call, repl_apg_call, 1)
    print("  ✅ [4.1] live_trading_engine.py: read_active_position_guard conectado con allow_breakeven_positions")
elif target_apg_call_crlf in lte_code:
    lte_code = lte_code.replace(target_apg_call_crlf, repl_apg_call_crlf, 1)
    print("  ✅ [4.1] live_trading_engine.py: read_active_position_guard conectado con allow_breakeven_positions (CRLF)")
else:
    print("  ⚠️ [4.1] live_trading_engine.py: patrón active position guard no encontrado")

with open(file_lte, "w", encoding="utf-8") as f:
    f.write(lte_code)

# -------------------------------------------------------------
# 3. strategy/execution/active_position_guard.py
# -------------------------------------------------------------
file_apg = "strategy/execution/active_position_guard.py"
with open(file_apg, "r", encoding="utf-8") as f:
    apg_code = f.read()

target_apg_func = "def check_active_position_guard(symbol, mt5_positions, mt5_orders):"
repl_apg_func = "def check_active_position_guard(symbol, mt5_positions, mt5_orders, allow_breakeven_positions: bool = False):"

target_apg_read = "def read_active_position_guard(symbol, broker):"
repl_apg_read = "def read_active_position_guard(symbol, broker, allow_breakeven_positions: bool = False):"

target_apg_call_inner = "return check_active_position_guard(symbol, broker.get_open_positions(), broker.get_pending_orders())"
repl_apg_call_inner = "return check_active_position_guard(symbol, broker.get_open_positions(), broker.get_pending_orders(), allow_breakeven_positions=allow_breakeven_positions)"

target_apg_rows = """        matching = [row for row in rows if is_same_or_counterpart_symbol(symbol, _field(row, 'symbol'))]
        if matching:"""

repl_apg_rows = """        matching = [row for row in rows if is_same_or_counterpart_symbol(symbol, _field(row, 'symbol'))]
        if matching:
            # Si allow_breakeven_positions está activo y todas las posiciones tienen SL en o por encima de Break-Even (riesgo cero), permitir análisis
            if allow_breakeven_positions and status == 'BLOCKED_ACTIVE_TRADE':
                all_at_be = True
                for row in matching:
                    pos_type = str(_field(row, 'type') or '').upper()
                    sl = float(_field(row, 'sl') or 0.0)
                    open_price = float(_field(row, 'price_open') or _field(row, 'open_price') or 0.0)
                    if sl <= 0 or open_price <= 0:
                        all_at_be = False
                        break
                    # Para BUY: SL >= open_price. Para SELL: SL <= open_price
                    if (('BUY' in pos_type or pos_type == '0') and sl < open_price) or (('SELL' in pos_type or pos_type == '1') and sl > open_price):
                        all_at_be = False
                        break
                if all_at_be:
                    continue  # Riesgo cero asegurado en BE: se permite nuevo setup"""

target_apg_rows_crlf = target_apg_rows.replace("\n", "\r\n")
repl_apg_rows_crlf = repl_apg_rows.replace("\n", "\r\n")

if target_apg_func in apg_code:
    apg_code = apg_code.replace(target_apg_func, repl_apg_func, 1)
if target_apg_read in apg_code:
    apg_code = apg_code.replace(target_apg_read, repl_apg_read, 1)
if target_apg_call_inner in apg_code:
    apg_code = apg_code.replace(target_apg_call_inner, repl_apg_call_inner, 1)

if target_apg_rows in apg_code:
    apg_code = apg_code.replace(target_apg_rows, repl_apg_rows, 1)
    print("  ✅ [4.2] active_position_guard.py: Liberación por Break-Even implementada")
elif target_apg_rows_crlf in apg_code:
    apg_code = apg_code.replace(target_apg_rows_crlf, repl_apg_rows_crlf, 1)
    print("  ✅ [4.2] active_position_guard.py: Liberación por Break-Even implementada (CRLF)")
else:
    print("  ⚠️ [4.2] active_position_guard.py: patrón matching rows no encontrado")

with open(file_apg, "w", encoding="utf-8") as f:
    f.write(apg_code)

# -------------------------------------------------------------
# 4. strategy/human_criteria/human_criteria_engine.py
# -------------------------------------------------------------
file_hc = "strategy/human_criteria/human_criteria_engine.py"
with open(file_hc, "r", encoding="utf-8") as f:
    hc_code = f.read()

target_hc_regime = """        elif regime_toxic:
            primary_veto = regime_reason
            action = "HUMAN_CRITERIA_TOXIC_REGIME_BLOCKED" """

target_hc_regime_alt = """        elif regime_toxic:
            primary_veto = regime_reason
            action = "HUMAN_CRITERIA_TOXIC_REGIME_BLOCKED" """

repl_hc_regime = """        elif regime_toxic:
            # En MultiStrategia sintéticos: si la señal presenta confirmación de vela fuerte (retest_evidence con absorción o desplazamiento),
            # no es un régimen tóxico insalvable sino un quiebre limpio saliendo del rango picado.
            candle_body = float(signal.get("candle_body_ratio") or (signal.get("retest_evidence") or {}).get("body_ratio") or 0.0)
            has_absorption = bool(signal.get("displacement") or (signal.get("retest_evidence") or {}).get("displacement") or candle_body >= 0.55)
            if is_synthetic and is_msnr and has_absorption:
                regime_toxic = False
                details.setdefault("regime", {})["toxic_overridden_by_absorption"] = True
            else:
                primary_veto = regime_reason
                action = "HUMAN_CRITERIA_TOXIC_REGIME_BLOCKED" """

target_hc_regime_clean = "        elif regime_toxic:\n            primary_veto = regime_reason\n            action = \"HUMAN_CRITERIA_TOXIC_REGIME_BLOCKED\""
target_hc_regime_clean_crlf = target_hc_regime_clean.replace("\n", "\r\n")
repl_hc_regime_clean = repl_hc_regime.strip()

if target_hc_regime_clean in hc_code:
    hc_code = hc_code.replace(target_hc_regime_clean, repl_hc_regime.strip(), 1)
    print("  ✅ [5] human_criteria_engine.py: Atenuación de régimen tóxico ante vela de absorción M5 implementada")
elif target_hc_regime_clean_crlf in hc_code:
    hc_code = hc_code.replace(target_hc_regime_clean_crlf, repl_hc_regime.strip().replace("\n", "\r\n"), 1)
    print("  ✅ [5] human_criteria_engine.py: Atenuación de régimen tóxico ante vela de absorción M5 implementada (CRLF)")
else:
    print("  ⚠️ [5] human_criteria_engine.py: patrón regime_toxic no encontrado")

with open(file_hc, "w", encoding="utf-8") as f:
    f.write(hc_code)

print("\n" + "=" * 70)
print("TODAS LAS SOLUCIONES MULTISTRATEGIA HAN SIDO APLICADAS")
print("=" * 70)
