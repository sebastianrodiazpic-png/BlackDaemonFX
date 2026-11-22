# -*- coding: utf-8 -*-
"""
Script para eliminar de la vista de /Instruments (en todas las pestañas) el banner de estrategia
y el panel de control de workers en paralelo (#strategyHighlightBanner y #tabWorkerPanel).
"""
import sys

def main():
    with open('dashboard/realtime_dashboard.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. En HTML, ocultar strategyHighlightBanner y tabWorkerPanel
    old_html_block = '''        <div id="strategyHighlightBanner" class="note" style="margin-top:12px;border-left:4px solid #38bdf8;background:rgba(14,29,45,0.85);">\n\n\n\n          <b>Estrategia ICT (Sabri Malle)</b> · Pestaña vinculada a workers en tiempo real.\n\n\n\n        </div>\n\n\n\n        <section id="tabWorkerPanel" class="card" style="margin-top:12px;padding:12px;background:var(--panel2);">\n\n\n\n          <div class="sub">Cargando estado de workers y progreso en paralelo…</div>\n\n\n\n        </section>'''
    
    new_html_block = '''        <div id="strategyHighlightBanner" style="display:none;"></div>\n        <section id="tabWorkerPanel" style="display:none;"></section>'''

    if old_html_block in content:
        content = content.replace(old_html_block, new_html_block)
        print("HTML block de strategyHighlightBanner y tabWorkerPanel ocultado exitosamente.")
    else:
        # Fallback con regex
        import re
        content = re.sub(
            r'<div id="strategyHighlightBanner"[\s\S]*?<\/section>',
            '<div id="strategyHighlightBanner" style="display:none;"></div>\n        <section id="tabWorkerPanel" style="display:none;"></section>',
            content,
            count=1
        )
        print("HTML block ocultado con regex.")

    # 2. En JS, hacer que renderTabWorkers mantenga ambos elementos ocultos en todas las pestañas
    old_js_start = "function renderTabWorkers(s) {\n\n\n\n        const banner = $('strategyHighlightBanner');\n\n\n\n        const info = PROFILE_STRATEGY_INFO[activeProfile] || PROFILE_STRATEGY_INFO.SYNTHETICS;"
    new_js_start = "function renderTabWorkers(s) {\n        const banner = $('strategyHighlightBanner');\n        if (banner) { banner.style.display = 'none'; banner.innerHTML = ''; }\n        const panel = $('tabWorkerPanel');\n        if (panel) { panel.style.display = 'none'; panel.innerHTML = ''; }\n        return;\n        const info = PROFILE_STRATEGY_INFO[activeProfile] || PROFILE_STRATEGY_INFO.SYNTHETICS;"

    if old_js_start in content:
        content = content.replace(old_js_start, new_js_start)
        print("renderTabWorkers actualizado para silenciar ambos paneles en todas las pestañas.")
    else:
        import re
        content = re.sub(
            r"function renderTabWorkers\(s\)\s*\{\s*const banner = \$\('strategyHighlightBanner'\);\s*const info = PROFILE_STRATEGY_INFO\[activeProfile\] \|\| PROFILE_STRATEGY_INFO\.SYNTHETICS;",
            "function renderTabWorkers(s) {\n        const banner = $('strategyHighlightBanner');\n        if (banner) { banner.style.display = 'none'; banner.innerHTML = ''; }\n        const panel = $('tabWorkerPanel');\n        if (panel) { panel.style.display = 'none'; panel.innerHTML = ''; }\n        return;\n        const info = PROFILE_STRATEGY_INFO[activeProfile] || PROFILE_STRATEGY_INFO.SYNTHETICS;",
            content,
            count=1
        )
        print("renderTabWorkers actualizado con regex.")

    with open('dashboard/realtime_dashboard.py', 'w', encoding='utf-8') as f:
        f.write(content)

    print("Actualización completada en dashboard/realtime_dashboard.py.")

if __name__ == '__main__':
    main()
