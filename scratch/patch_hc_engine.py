import os

p = 'strategy/human_criteria/human_criteria_engine.py'
tmp = 'strategy/human_criteria/human_criteria_engine.py.tmp'

with open(p, 'r', encoding='utf-8') as f:
    content = f.read()

target1 = """        regime = classification.regime
        is_toxic = classification.is_toxic or (
            category == "SYNTHETIC"
            and metrics.choppiness_index > self.config.synthetic_choppiness_threshold
            and metrics.adx < self.config.synthetic_adx_min_threshold
        )

        details = {
            "regime": regime,
            "choppiness": metrics.choppiness_index,
            "adx": metrics.adx,
            "is_toxic": is_toxic,
        }"""

replacement1 = """        regime = classification.regime
        sym_low = str(symbol or "").lower()
        is_step_jump = ("step" in sym_low or "jump" in sym_low)
        step_jump_exempt = is_step_jump and bool(getattr(self.config, "step_jump_adx_guard_exempt", True))

        is_toxic = classification.is_toxic or (
            category == "SYNTHETIC"
            and not step_jump_exempt
            and metrics.choppiness_index > self.config.synthetic_choppiness_threshold
            and metrics.adx < self.config.synthetic_adx_min_threshold
        )

        details = {
            "regime": regime,
            "choppiness": metrics.choppiness_index,
            "adx": metrics.adx,
            "is_toxic": is_toxic,
            "step_jump_exempt": step_jump_exempt,
        }"""

target2 = """        # 1. Filtro Anti-Agotamiento Clímax (no comprar en la cúspide de una vela parabólica)
        is_climax = False
        if bool(self.config.synthetic_climax_filter_enabled) and category == "SYNTHETIC" and atr_val > 0:
            if rng > (self.config.synthetic_climax_atr_multiplier * atr_val):
                # Si una sola vela mide más de 2.75x ATR y su cuerpo domina la vela (≥65% cuerpo) en la dirección del trade
                if (direction == "BUY" and c > o and (body / rng) >= 0.65 and (upper_wick / rng) < 0.20) or (
                    direction == "SELL" and c < o and (body / rng) >= 0.65 and (lower_wick / rng) < 0.20
                ):
                    is_climax = True"""

replacement2 = """        # 1. Filtro Anti-Agotamiento Clímax (no comprar en la cúspide de una vela parabólica)
        is_climax = False
        climax_body_ratio = float(getattr(self.config, "synthetic_climax_body_ratio", 0.80))
        if bool(self.config.synthetic_climax_filter_enabled) and category == "SYNTHETIC" and atr_val > 0:
            body_ratio_val = body / rng
            is_oversized = rng > (self.config.synthetic_climax_atr_multiplier * atr_val)
            if is_oversized:
                # Si una sola vela mide más de 2.75x ATR y su cuerpo domina la vela en la dirección del trade
                if (direction == "BUY" and c > o and body_ratio_val >= 0.65 and (upper_wick / rng) < 0.20) or (
                    direction == "SELL" and c < o and body_ratio_val >= 0.65 and (lower_wick / rng) < 0.20
                ):
                    is_climax = True
            elif body_ratio_val >= climax_body_ratio:
                # Agotamiento por marubozu parabólico extremo sin mecha de rechazo
                if (direction == "BUY" and c > o and (upper_wick / rng) < 0.15) or (
                    direction == "SELL" and c < o and (lower_wick / rng) < 0.15
                ):
                    is_climax = True"""

target3 = """        ratio = spread / sl_dist
        details = {"spread": spread, "sl_dist": sl_dist, "spread_sl_ratio": round(ratio, 4)}

        if ratio <= 0.03:
            return max_pts, details
        elif ratio <= 0.08:
            return max_pts * 0.75, details
        elif ratio <= 0.15:
            return max_pts * 0.50, details
        else:
            return max_pts * 0.20, details"""

replacement3 = """        ratio = spread / sl_dist
        max_ratio = float(getattr(self.config, "max_spread_to_sl_ratio", 0.12))
        is_excessive = ratio > max_ratio
        details = {
            "spread": spread,
            "sl_dist": sl_dist,
            "spread_sl_ratio": round(ratio, 4),
            "max_spread_to_sl_ratio": max_ratio,
            "is_excessive": is_excessive,
        }

        if ratio <= 0.03:
            return max_pts, details
        elif ratio <= 0.08:
            return max_pts * 0.75, details
        elif ratio <= max_ratio:
            return max_pts * 0.50, details
        else:
            return 0.0, details"""

assert target1 in content, "Target 1 not found"
assert target2 in content, "Target 2 not found"
assert target3 in content, "Target 3 not found"

content = content.replace(target1, replacement1)
content = content.replace(target2, replacement2)
content = content.replace(target3, replacement3)

with open(tmp, 'w', encoding='utf-8') as f:
    f.write(content)

os.replace(tmp, p)
print("Successfully applied all 3 optimizations to human_criteria_engine.py via atomic replace")
