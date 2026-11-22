# -*- coding: utf-8 -*-
with open('tests/test_strategy_bases_tab_and_msnr_cleanup.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
old_block = re.search(r'# Total counts match expectations[\s\S]*?assert len\(losers\) == 141', text)
if old_block:
    new_block = '''# Total counts match expectations: 292 registros, 177 rentables con Confluencia Tripartita, 115 podados
    assert len(winners) == 292
    assert len([w for w in winners if w.get("is_profitable")]) == 177
    assert len(losers) == 115'''
    text = text[:old_block.start(0)] + new_block + text[old_block.end(0):]
    with open('tests/test_strategy_bases_tab_and_msnr_cleanup.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Updated test_strategy_bases_tab_and_msnr_cleanup.py for Tripartite counts")
else:
    print("Pattern not found in test_strategy_bases_tab_and_msnr_cleanup.py")
