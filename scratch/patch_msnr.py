import re

path = 'strategy/malaysian_snr/malaysian_snr_strategy.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Normalize CRLF to LF
content = content.replace('\r\n', '\n')

old_d1 = """            raw_d1 = (self.provider.get_candles(symbol, self.config.macro_timeframe, count=15)
                      if self.config.enable_daily_storyline_filter else None)"""
new_d1 = """            raw_d1 = (self.provider.get_candles(symbol, self.config.macro_timeframe, count=40)
                      if (self.config.enable_daily_storyline_filter or getattr(self.config, 'enable_d1_storyline_levels', False)) else None)"""
assert old_d1 in content, "old_d1 not found"
content = content.replace(old_d1, new_d1)

old_d1_closed = """            d1 = closed_candles(raw_d1, self.config.macro_timeframe, now)"""
new_d1_closed = """            d1 = closed_candles(raw_d1, self.config.macro_timeframe, now) if raw_d1 is not None else pd.DataFrame()"""
assert old_d1_closed in content, "old_d1_closed not found"
content = content.replace(old_d1_closed, new_d1_closed)

old_levels = """        levels = av_levels(h1)

        def allowed_direction(direction):"""
new_levels = """        levels = av_levels(h1)
        d1_levels = av_levels(d1) if (getattr(self.config, 'enable_d1_storyline_levels', False) and d1 is not None and not d1.empty) else []
        use_crt = getattr(self.config, 'enable_crt_sweep_rejection', True)

        def allowed_direction(direction):"""
assert old_levels in content, "old_levels not found"
content = content.replace(old_levels, new_levels)

old_make_signal = """        def make_signal(direction, scenario, level, break_level, stop):
            sign = 1 if direction == "BUY" else -1
            candidates = [item["level"] for item in levels
                          if item["type"] == ("A_RESISTANCE" if direction == "BUY" else "V_SUPPORT")
                          and sign * (item["level"] - entry) > 0]
            obstacle = (min(candidates) if direction == "BUY" else max(candidates)) if candidates else 0.0"""

new_make_signal = """        def make_signal(direction, scenario, level, break_level, stop):
            sign = 1 if direction == "BUY" else -1
            risk_dist = sign * (entry - stop)
            if risk_dist <= 0:
                return {"valid": False, "strategy_name": self.config.strategy_name,
                        "strategy_version": self.config.strategy_version, "symbol": symbol,
                        "action": "WAITING_MALAYSIAN_SNR", "reason": "INVALID_STOP_OR_RISK_DISTANCE"}

            if getattr(self.config, 'enable_d1_storyline_levels', False) and d1_levels:
                d1_candidates = [item["level"] for item in d1_levels
                                 if item["type"] == ("A_RESISTANCE" if direction == "BUY" else "V_SUPPORT")
                                 and sign * (item["level"] - entry) > 0]
                if d1_candidates:
                    closest_d1 = min(d1_candidates) if direction == "BUY" else max(d1_candidates)
                    d1_clearance = sign * (closest_d1 - entry)
                    min_rr = getattr(self.config, 'min_obstacle_rr', 2.0)
                    if d1_clearance < min_rr * risk_dist:
                        return {"valid": False, "strategy_name": self.config.strategy_name,
                                "strategy_version": self.config.strategy_version, "symbol": symbol,
                                "action": "WAITING_MALAYSIAN_SNR", "reason": "OBSTACLE_D1_BEFORE_2R"}

            candidates = [item["level"] for item in levels
                          if item["type"] == ("A_RESISTANCE" if direction == "BUY" else "V_SUPPORT")
                          and sign * (item["level"] - entry) > 0]
            obstacle = (min(candidates) if direction == "BUY" else max(candidates)) if candidates else 0.0"""
assert old_make_signal in content, "old_make_signal not found"
content = content.replace(old_make_signal, new_make_signal)

old_entry_conf = """                    "entry_confirmation": "POST_BREAK_M15_RETEST_AND_DIRECTIONAL_CLOSE"})"""
new_entry_conf = """                    "entry_confirmation": "CRT_M15_SWEEP_AND_ABSORPTION_CLOSE" if use_crt else "POST_BREAK_M15_RETEST_AND_DIRECTIONAL_CLOSE"})"""
assert old_entry_conf in content, "old_entry_conf not found"
content = content.replace(old_entry_conf, new_entry_conf)

# Replace retest calls with use_crt_trigger=use_crt
content = content.replace(
    'self.config.retest_tolerance_atr, self.config.max_entry_distance_atr)',
    'self.config.retest_tolerance_atr, self.config.max_entry_distance_atr, use_crt_trigger=use_crt)'
)
content = content.replace(
    'self.config.retest_tolerance_atr, min(.40, self.config.max_entry_distance_atr))',
    'self.config.retest_tolerance_atr, min(.40, self.config.max_entry_distance_atr), use_crt_trigger=use_crt)'
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Patch applied successfully to", path)
