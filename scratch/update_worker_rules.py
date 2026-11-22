with open('strategy/execution/worker_rules.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add import os if not present
if 'import os' not in content:
    content = content.replace(
        'from dataclasses import replace',
        'import os\nfrom dataclasses import replace'
    )

old_step_jump = """    if profile in {"STEP", "JUMP"}:
        return replace(
            config,
            h1_location_only=True,
            smc_entry_location_policy='H1_PRIMARY',
            dual_m5_m1_trigger_enabled=True,
            entry_timeframe='M5',
            strategy_version=RULESET,
            first_target_rr=1.0,
            second_target_rr=2.0,
            smc_runner_max_target_rr=4.0,
            runner_extension_enabled=True,
            runner_extension_first_trigger_rr=2.0,
            runner_extension_first_lock_rr=1.0,
            runner_extension_second_trigger_rr=3.0,
            runner_extension_second_lock_rr=2.5,
            runner_extension_max_target_rr=4.0,
            break_even_enabled=True,
            break_even_trigger_rr=1.0,
            min_rr=1.0,
        )"""

new_step_jump = """    if profile == "STEP":
        step_multistrat = os.getenv("DAEMONBLACKFX_STEP_MULTISTRATEGY", "1").strip().lower() not in ("0", "false", "off")
        return replace(
            config,
            h1_location_only=True,
            smc_entry_location_policy='H1_PRIMARY',
            dual_m5_m1_trigger_enabled=True,
            entry_timeframe='M5',
            strategy_version=RULESET,
            malaysian_snr_enabled=step_multistrat,
            first_target_rr=1.0,
            second_target_rr=2.0,
            smc_runner_max_target_rr=4.0,
            runner_extension_enabled=True,
            runner_extension_first_trigger_rr=2.0,
            runner_extension_first_lock_rr=1.0,
            runner_extension_second_trigger_rr=3.0,
            runner_extension_second_lock_rr=2.5,
            runner_extension_max_target_rr=4.0,
            break_even_enabled=True,
            break_even_trigger_rr=1.0,
            min_rr=1.0,
        )
    if profile == "JUMP":
        return replace(
            config,
            h1_location_only=True,
            smc_entry_location_policy='H1_PRIMARY',
            dual_m5_m1_trigger_enabled=True,
            entry_timeframe='M5',
            strategy_version=RULESET,
            first_target_rr=1.0,
            second_target_rr=2.0,
            smc_runner_max_target_rr=4.0,
            runner_extension_enabled=True,
            runner_extension_first_trigger_rr=2.0,
            runner_extension_first_lock_rr=1.0,
            runner_extension_second_trigger_rr=3.0,
            runner_extension_second_lock_rr=2.5,
            runner_extension_max_target_rr=4.0,
            break_even_enabled=True,
            break_even_trigger_rr=1.0,
            min_rr=1.0,
        )"""

norm = content.replace('\r\n', '\n')
if old_step_jump in norm:
    norm = norm.replace(old_step_jump, new_step_jump)
    with open('strategy/execution/worker_rules.py', 'w', encoding='utf-8', newline='\r\n') as f:
        f.write(norm)
    print("SUCCESS: worker_rules.py updated")
else:
    print("ERROR: old_step_jump not found")
