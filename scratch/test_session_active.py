import sys
sys.path.insert(0, ".")
from datetime import datetime, timezone
import zoneinfo
from strategy.ict.config import ICTConfig
from strategy.ict.ict_strategy import ICTStrategy, is_index_cash_session

config = ICTConfig()
print("ICTConfig:")
print("  killzone_filter_enabled:", config.killzone_filter_enabled)
print("  ny_killzone_enabled:", config.ny_killzone_enabled)
print("  forex_ny_killzone_enabled:", config.forex_ny_killzone_enabled)
print("  real_markets_expansion_enabled:", config.real_markets_expansion_enabled)
print("  indices_cash_open_enabled:", config.indices_cash_open_enabled)
print("  silver_bullet_enabled:", config.silver_bullet_enabled)
print("  silver_bullet_hours_ny:", config.silver_bullet_hours_ny)
print("  ny_kz_start_ny:", config.ny_kz_start_ny)
print("  ny_kz_end_ny:", config.ny_kz_end_ny)

now_utc = datetime.now(timezone.utc)
ny_tz = zoneinfo.ZoneInfo("America/New_York")
now_ny = now_utc.astimezone(ny_tz)
print(f"Current UTC: {now_utc}")
print(f"Current NY: {now_ny} (hour: {now_ny.hour}, minute: {now_ny.minute})")

for sym in ["US Tech 100", "Wall Street 30", "Germany 40", "NZDUSD", "XAUUSD"]:
    is_cash = is_index_cash_session(sym, now_ny)
    print(f"Symbol: {sym} -> is_index_cash_session: {is_cash}")
