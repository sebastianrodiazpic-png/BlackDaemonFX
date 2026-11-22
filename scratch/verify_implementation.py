"""
scratch/verify_implementation.py
"""
from pathlib import Path

cfg = Path("strategy/malaysian_snr/config.py").read_text(encoding="utf-8")
strat = Path("strategy/malaysian_snr/malaysian_snr_strategy.py").read_text(encoding="utf-8")
lte = Path("strategy/execution/live_trading_engine.py").read_text(encoding="utf-8")

print("1. MSNR Config Storyline Default 0:", 'os.getenv("DAEMONBLACKFX_MSNR_STORYLINE_FILTER", "0")' in cfg)
print("2. MSNR Config Step ADX 12.0:", 'os.getenv("DAEMONBLACKFX_MSNR_STEP_MIN_ADX", "12.0")' in cfg)
print("3. MSNR Config step_require_adx:", 'step_require_adx: bool = os.getenv("DAEMONBLACKFX_MSNR_STEP_REQUIRE_ADX", "0")' in cfg)
print("4. MSNR Strategy Step Guard:", 'if getattr(self.config, "step_require_adx", False)' in strat)
print("5. LTE Dynamic Runner in place:", 'signal.get("runner_rr") or signal.get("runner_max_target_rr")' in lte)
print("6. LTE Dynamic Runner occurrences:", lte.count('signal.get("runner_rr") or signal.get("runner_max_target_rr")'))
