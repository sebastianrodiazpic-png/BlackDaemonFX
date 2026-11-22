import os

p = 'strategy/human_criteria/human_criteria_engine.py'
tmp = 'strategy/human_criteria/human_criteria_engine.py.tmp'

with open(p, 'r', encoding='utf-8') as f:
    content = f.read()

target = """        regime = classification.regime
        sym_low = str(symbol or "").lower()
        is_step_jump = ("step" in sym_low or "jump" in sym_low)
        step_jump_exempt = is_step_jump and bool(getattr(self.config, "step_jump_adx_guard_exempt", True))

        is_toxic = classification.is_toxic or (
            category == "SYNTHETIC"
            and not step_jump_exempt
            and metrics.choppiness_index > self.config.synthetic_choppiness_threshold
            and metrics.adx < self.config.synthetic_adx_min_threshold
        )"""

replacement = """        regime = classification.regime
        sym_low = str(symbol or "").lower()
        is_step_jump = ("step" in sym_low or "jump" in sym_low)
        step_jump_exempt = is_step_jump and bool(getattr(self.config, "step_jump_adx_guard_exempt", True))

        if step_jump_exempt:
            is_toxic = False
        else:
            is_toxic = classification.is_toxic or (
                category == "SYNTHETIC"
                and metrics.choppiness_index > self.config.synthetic_choppiness_threshold
                and metrics.adx < self.config.synthetic_adx_min_threshold
            )"""

assert target in content, "Target not found"
content = content.replace(target, replacement)
with open(tmp, 'w', encoding='utf-8') as f:
    f.write(content)
os.replace(tmp, p)
print("Updated step_jump_exempt logic successfully!")
