# -*- coding: utf-8 -*-
with open('tests/test_v121_instruments_tri_motor_worker_control.py', 'r', encoding='utf-8') as f:
    text = f.read()

new_test = """

def test_instruments_parallel_worker_panel_hidden_in_all_tabs():
    \"\"\"Valida que el panel de control de workers y el banner de estrategia permanezcan ocultos en todas las pestañas de /instruments.\"\"\"
    assert '<div id="strategyHighlightBanner" style="display:none;"></div>' in _INSTRUMENTS_HTML
    assert '<section id="tabWorkerPanel" style="display:none;"></section>' in _INSTRUMENTS_HTML
    assert "banner.style.display = 'none'" in _INSTRUMENTS_HTML
    assert "panel.style.display = 'none'" in _INSTRUMENTS_HTML
"""

if "test_instruments_parallel_worker_panel_hidden_in_all_tabs" not in text:
    text += new_test
    with open('tests/test_v121_instruments_tri_motor_worker_control.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Added test to test_v121_instruments_tri_motor_worker_control.py")
else:
    print("Test already present")
