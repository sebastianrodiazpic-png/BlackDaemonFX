from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
from strategy.execution.worker_rules import configure_worker_rules

cfg = LiveTradingConfig(bot_profile="BOOM", magic=26082101, execution_enabled=False)
cfg = configure_worker_rules(cfg)

print("Profile:", cfg.bot_profile)
print("malaysian_snr_enabled:", cfg.malaysian_snr_enabled)
is_pure_msnr = str(cfg.bot_profile).upper() == "MALAYSIAN_SNR"
print("Is pure MSNR worker:", is_pure_msnr)
