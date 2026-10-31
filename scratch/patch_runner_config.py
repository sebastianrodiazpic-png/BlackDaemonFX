import re

path = 'strategy/execution/live_trading_engine.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Config defaults
old_cfg = """    runner_extension_enabled: bool = True
    runner_extension_first_trigger_rr: float = 2.0
    runner_extension_first_lock_rr: float = 1.0
    runner_extension_second_trigger_rr: float = 3.0
    runner_extension_second_lock_rr: float = 2.5
    runner_extension_max_target_rr: float = 4.0
    smc_runner_max_target_rr: float = 4.0"""

new_cfg = """    runner_extension_enabled: bool = True
    runner_extension_first_trigger_rr: float = float(os.getenv("DAEMONBLACKFX_RUNNER_FIRST_TRIGGER_RR", "1.5"))
    runner_extension_first_lock_rr: float = float(os.getenv("DAEMONBLACKFX_RUNNER_FIRST_LOCK_RR", "1.5"))
    runner_extension_second_trigger_rr: float = float(os.getenv("DAEMONBLACKFX_RUNNER_SECOND_TRIGGER_RR", "2.5"))
    runner_extension_second_lock_rr: float = float(os.getenv("DAEMONBLACKFX_RUNNER_SECOND_LOCK_RR", "2.5"))
    runner_extension_max_target_rr: float = float(os.getenv("DAEMONBLACKFX_RUNNER_MAX_TARGET_RR", "4.0"))
    smc_runner_max_target_rr: float = float(os.getenv("DAEMONBLACKFX_SMC_RUNNER_MAX_TARGET_RR", "4.0"))"""

if old_cfg in content:
    content = content.replace(old_cfg, new_cfg, 1)
    print("1. Config replaced successfully.")
else:
    # Try normalizing CRLF
    old_cfg_crlf = old_cfg.replace('\n', '\r\n')
    new_cfg_crlf = new_cfg.replace('\n', '\r\n')
    if old_cfg_crlf in content:
        content = content.replace(old_cfg_crlf, new_cfg_crlf, 1)
        print("1. Config (CRLF) replaced successfully.")
    else:
        print("1. ERROR: Config snippet not found!")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
