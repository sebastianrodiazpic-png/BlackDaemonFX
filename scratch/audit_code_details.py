import inspect
import sys
from pathlib import Path

ROOT = Path("c:/TradingBoot/smc_synthetic_bot")
sys.path.insert(0, str(ROOT))

print("=== 1. ORB IMPLEMENTATION AUDIT ===")
import strategy.orb.new_york_orb as orb_mod
print("ORB module functions/classes:", [a for a in dir(orb_mod) if not a.startswith('_')])

print("\n=== 2. GOLD QUARTERS IMPLEMENTATION AUDIT ===")
import strategy.gold_quarters as gq_mod
print("Gold Quarters code length:", len(Path("strategy/gold_quarters.py").read_text().splitlines()))
print(Path("strategy/gold_quarters.py").read_text()[:1200])

print("\n=== 3. ICT SABRI MALLE AUDIT ===")
import strategy.ict.ict_strategy as ict_mod
print("ICT module classes:", [a for a in dir(ict_mod) if not a.startswith('_')])

print("\n=== 4. MALAYSIAN SNR AUDIT ===")
import strategy.malaysian_snr.malaysian_snr_strategy as msnr_mod
print("MSNR Strategy methods:", [m for m in dir(msnr_mod.MalaysianSNRStrategy) if not m.startswith('_')])

print("\n=== 5. LIVE TRADING ENGINE RISK & TWO-LEG AUDIT ===")
import strategy.execution.live_trading_engine as lte_mod
print("LiveTradingEngine risk methods:", [m for m in dir(lte_mod.LiveTradingEngine) if 'risk' in m or 'leg' in m or 'target' in m or 'be' in m or 'exit' in m])
