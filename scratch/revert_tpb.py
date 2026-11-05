import os
from pathlib import Path

target = Path('strategy/trend_pullback/config.py').resolve()
c = target.read_text(encoding='utf-8')

old_tpb = """    jump_buy_only_symbols: tuple = tuple(
        s.strip() for s in os.getenv("DAEMONBLACKFX_TPB_JUMP_BUY_ONLY", "").split(",") if s.strip()
    )
    step_sell_only_symbols: tuple = tuple(
        s.strip() for s in os.getenv("DAEMONBLACKFX_TPB_STEP_SELL_ONLY", "").split(",") if s.strip()
    )"""

new_tpb = """    jump_buy_only_symbols: tuple = tuple(
        s.strip() for s in os.getenv("DAEMONBLACKFX_TPB_JUMP_BUY_ONLY", "Jump 50 Index,Jump 75 Index").split(",") if s.strip()
    )
    step_sell_only_symbols: tuple = tuple(
        s.strip() for s in os.getenv("DAEMONBLACKFX_TPB_STEP_SELL_ONLY", "Step Index,Step Index 500").split(",") if s.strip()
    )"""

assert old_tpb in c, 'old_tpb not found'
c = c.replace(old_tpb, new_tpb)

temp = target.with_name('config_tpb_temp.py')
with open(temp, 'w', encoding='utf-8') as f:
    f.write(c)

os.replace(temp, target)
print('strategy/trend_pullback/config.py reverted cleanly!')
