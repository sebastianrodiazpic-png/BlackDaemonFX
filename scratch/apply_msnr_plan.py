# 1. Update config/ict_instrument_policy.py
policy_path = 'config/ict_instrument_policy.py'
with open(policy_path, 'r', encoding='utf-8') as f:
    pol_content = f.read()

old_msnr_synthetics = """MSNR_ACIERTO47_SYNTHETICS = (
    "High Frequency Vol 100 Index", "VolSwitch High Vol Index", "Volatility 5 Index",
    "Volatility 50 (1s) Index", "Volatility 90 Index", "Boom 300 Index",
    "Volatility 150 (1s) Index", "Jump 25 Index",
    "Volatility 25 Index", "Volatility 75 Index", "Volatility 250 (1s) Index", "Crash 900 Index",
    "High Frequency Vol 50 Index", "Volatility 10 Index", "Jump 10 Index", "Boom 500 Index",
    "Volatility 15 Index", "Volatility 75 (1s) Index",
)"""

new_msnr_synthetics = """MSNR_ACIERTO47_SYNTHETICS = (
    # Canasta Élite Cuantitativa Malaysian SNR (Replay fiel 1.368 ops, alta expectativa y win rate positivo):
    # Ganadores top: Boom 1000 (+21.0 R), Crash 1000 (+14.4 R), Vol 25 (+15.8 R), Vol 10 (+14.2 R), Step Index (+5.5 R)
    "Boom 1000 Index", "Crash 1000 Index", "Step Index", "Volatility 25 Index", "Volatility 10 Index",
    "Volatility 90 Index", "Volatility 50 (1s) Index", "Boom 500 Index", "Crash 900 Index",
    "Boom 300 Index", "Crash 600 Index", "VolSwitch High Vol Index", "High Frequency Vol 100 Index",
    "High Frequency Vol 50 Index", "Volatility 15 Index", "Volatility 75 (1s) Index",
    "Volatility 150 (1s) Index", "Volatility 250 (1s) Index", "Volatility 5 Index", "Jump 10 Index",
    # NOTA: Jump 25 Index (-43.0 R) y Volatility 75 Index (-27.4 R) excluidos estrictamente por sangría recurrente.
)"""

if old_msnr_synthetics in pol_content:
    pol_content = pol_content.replace(old_msnr_synthetics, new_msnr_synthetics, 1)
    print("1. config/ict_instrument_policy.py updated successfully.")
else:
    old_crlf = old_msnr_synthetics.replace('\n', '\r\n')
    new_crlf = new_msnr_synthetics.replace('\n', '\r\n')
    if old_crlf in pol_content:
        pol_content = pol_content.replace(old_crlf, new_crlf, 1)
        print("1. config/ict_instrument_policy.py (CRLF) updated successfully.")
    else:
        print("1. ERROR: old_msnr_synthetics not found!")

with open(policy_path, 'w', encoding='utf-8') as f:
    f.write(pol_content)

# 2. Update strategy/malaysian_snr/config.py
cfg_path = 'strategy/malaysian_snr/config.py'
with open(cfg_path, 'r', encoding='utf-8') as f:
    cfg_content = f.read()

# retest_window_minutes & recovery defaults
old_retest = """    retest_window_minutes: int = int(os.getenv("DAEMONBLACKFX_MSNR_RETEST_WINDOW_MINUTES", "90"))
    entry_execution_grace_seconds: int = 60
    retest_recovery_bars: int = 3
    confirmation_tolerance_bars: int = 0
    confirmation_tolerance_max_atr: float = 0.35
    enable_zone_rejection_trigger: bool = True
    max_retest_penetration_atr: float = 0.35
    retest_min_body_ratio: float = 0.35"""

new_retest = """    retest_window_minutes: int = int(os.getenv("DAEMONBLACKFX_MSNR_RETEST_WINDOW_MINUTES", "180"))
    entry_execution_grace_seconds: int = 60
    retest_recovery_bars: int = int(os.getenv("DAEMONBLACKFX_MSNR_RECOVERY_BARS", "4"))
    confirmation_tolerance_bars: int = int(os.getenv("DAEMONBLACKFX_MSNR_CONFIRMATION_TOLERANCE_BARS", "2"))
    confirmation_tolerance_max_atr: float = 0.35
    enable_zone_rejection_trigger: bool = True
    max_retest_penetration_atr: float = 0.35
    retest_min_body_ratio: float = float(os.getenv("DAEMONBLACKFX_MSNR_RETEST_MIN_BODY_RATIO", "0.25"))"""

old_cont = """    # Escenarios habilitados
    enable_scenario_1_continuation: bool = False"""

new_cont = """    # Escenarios habilitados
    enable_scenario_1_continuation: bool = os.getenv("DAEMONBLACKFX_MSNR_ENABLE_CONTINUATION", "1").strip().lower() in ("1", "true", "on")"""

old_story = """    enable_daily_storyline_filter: bool = True     # Confluencia con sesgo macro D1
    enable_synthetic_daily_storyline_filter: bool = False  # Veto D1 opcional para sintéticos; obstáculos D1 se conservan"""

new_story = """    enable_daily_storyline_filter: bool = True     # Confluencia con sesgo macro D1
    enable_synthetic_daily_storyline_filter: bool = os.getenv("DAEMONBLACKFX_MSNR_STORYLINE_FILTER", "1").strip().lower() in ("1", "true", "on")  # Sesgo macro D1/H4 Alchemist"""

old_recovery = """    recovery_window_minutes: int = 45
    recovery_min_body_ratio: float = 0.35"""

new_recovery = """    recovery_window_minutes: int = int(os.getenv("DAEMONBLACKFX_MSNR_RECOVERY_WINDOW_MINUTES", "60"))
    recovery_min_body_ratio: float = float(os.getenv("DAEMONBLACKFX_MSNR_RECOVERY_MIN_BODY_RATIO", "0.25"))"""

def replace_in_cfg(text, old_s, new_s, lbl):
    if old_s in text:
        print(f"2. {lbl} OK")
        return text.replace(old_s, new_s, 1)
    old_c = old_s.replace('\n', '\r\n')
    new_c = new_s.replace('\n', '\r\n')
    if old_c in text:
        print(f"2. {lbl} (CRLF) OK")
        return text.replace(old_c, new_c, 1)
    print(f"2. {lbl} ERROR: not found")
    return text

cfg_content = replace_in_cfg(cfg_content, old_retest, new_retest, "retest")
cfg_content = replace_in_cfg(cfg_content, old_cont, new_cont, "continuation")
cfg_content = replace_in_cfg(cfg_content, old_story, new_story, "storyline")
cfg_content = replace_in_cfg(cfg_content, old_recovery, new_recovery, "recovery")

with open(cfg_path, 'w', encoding='utf-8') as f:
    f.write(cfg_content)

# 3. Update strategy/execution/live_trading_engine.py
eng_path = 'strategy/execution/live_trading_engine.py'
with open(eng_path, 'r', encoding='utf-8') as f:
    eng_content = f.read()

old_msnr_runner = """            if is_msnr_runner:
                completed_stages.add(stage_name)
                metadata["runner_extension_completed_stages"] = sorted(completed_stages)
                # Misma etiqueta que el resto de estrategias (informes y dashboard): MSNR no evalúa continuación,
                # solo sube el stop de forma progresiva hacia su objetivo máximo.
                metadata["runner_extension_stage"] = "EXTENDED_TO_3R" if stage_name == "2R_TO_3R" else "EXTENDED_TO_4R"
                result.update({
                    "managed": True,
                    "extended": True,
                    "stage": stage_name,
                    "profit_lock_rr": float(lock_rr),
                    "profit_lock_price": float(protected_sl),
                    "target_rr": max_target_rr,
                    "target_price": float(target_price),
                })
                return result"""

new_msnr_runner = """            if is_msnr_runner:
                completed_stages.add(stage_name)
                metadata["runner_extension_completed_stages"] = sorted(completed_stages)
                # Gestión progresiva de 2 patas para MSNR: etapa 1 asegura 1.5R y busca 3.0R; etapa 2 asegura 2.5R y busca 4.0R
                metadata["runner_extension_stage"] = "EXTENDED_TO_3R" if is_stage1 else "EXTENDED_TO_4R"
                metadata["runner_logical_target_rr"] = float(next_target_rr)
                metadata["runner_candidate_target_rr"] = None
                metadata["runner_profit_lock_rr"] = float(lock_rr)
                metadata["runner_profit_lock_price"] = float(protected_sl)
                details = dict(trade.get("details") or {})
                details["metadata"] = metadata
                self.repository.update_trade(
                    int(trade["id"]),
                    {
                        "stop_loss": float(protected_sl),
                        "take_profit": float(target_price),
                        "planned_rr": float(next_target_rr),
                        "details": details,
                    },
                )
                result.update({
                    "managed": True,
                    "extended": True,
                    "stage": stage_name,
                    "profit_lock_rr": float(lock_rr),
                    "profit_lock_price": float(protected_sl),
                    "target_rr": float(next_target_rr),
                    "target_price": float(target_price),
                    "next_target_rr": next_target_rr,
                })
                return result"""

eng_content = replace_in_cfg(eng_content, old_msnr_runner, new_msnr_runner, "msnr_runner_engine")

with open(eng_path, 'w', encoding='utf-8') as f:
    f.write(eng_content)

print("All patches completed.")
