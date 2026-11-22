# -*- coding: utf-8 -*-
with open('tests/test_strategy_bases_tab_and_msnr_cleanup.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
old_block = re.search(r'# Total counts match expectations[\s\S]*?assert len\(losers\) == 141', text)
if old_block:
    new_block = '''# Total counts match expectations: exclusivamente 177 activos rentables, 0 podados
    assert len(winners) == 177
    assert all(w.get("is_profitable") for w in winners)
    assert len(losers) == 0'''
    text = text[:old_block.start(0)] + new_block + text[old_block.end(0):]
    with open('tests/test_strategy_bases_tab_and_msnr_cleanup.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Updated test_strategy_bases_tab_and_msnr_cleanup successfully")
else:
    print("Pattern not found")
