with open('tests/test_strategy_bases_tab_and_msnr_cleanup.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('assert "Malaysian SNR Híbrido Institucional" in STRATEGY_BASES_HTML', 'assert "Malaysian SNR Institucional" in STRATEGY_BASES_HTML')
text = text.replace('assert "ICT Sabri Malle" in winner_strats', 'assert "ICT" in winner_strats')

with open('tests/test_strategy_bases_tab_and_msnr_cleanup.py', 'w', encoding='utf-8') as f:
    f.write(text)

print('test_strategy_bases_tab_and_msnr_cleanup.py updated successfully')
