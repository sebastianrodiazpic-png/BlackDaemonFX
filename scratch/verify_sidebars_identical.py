files = [
    ('dashboard/realtime_dashboard.py (Dashboard)', 'dashboard/realtime_dashboard.py', '_HTML ='),
    ('dashboard/realtime_dashboard.py (Instruments)', 'dashboard/realtime_dashboard.py', '_INSTRUMENTS_HTML ='),
    ('dashboard/account_page.py', 'dashboard/account_page.py', None),
    ('dashboard/performance_page.py', 'dashboard/performance_page.py', None),
    ('dashboard/strategy_bases_page.py', 'dashboard/strategy_bases_page.py', None),
]

for label, path, marker in files:
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    start_search = 0
    if marker:
        start_search = text.find(marker)
    aside_start = text.find('<aside class="brandSidebar">', start_search)
    aside_end = text.find('</aside>', aside_start) + len('</aside>')
    snippet = text[aside_start:aside_end]
    assert '▦ Dashboard' in snippet, f"Dashboard icon missing in {label}"
    assert '▥ Instrumentos' in snippet, f"Instruments icon missing in {label}"
    assert '▣ Cuenta en vivo' in snippet, f"Account icon missing in {label}"
    assert '📈 Rendimiento' in snippet, f"Performance icon missing in {label}"
    assert '📚 Bases de Estrategias' in snippet, f"Strategy bases icon missing in {label}"
    assert '◈ Posiciones abiertas' in snippet, f"Open positions icon missing in {label}"
    assert '◷ Análisis recientes' in snippet, f"Recent analysis icon missing in {label}"
    print(f"Verified {label}: OK!")

print("ALL SIDEBARS VERIFIED AND IDENTICAL!")
