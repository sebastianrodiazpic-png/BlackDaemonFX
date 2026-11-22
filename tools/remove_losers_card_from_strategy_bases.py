# -*- coding: utf-8 -*-
"""
Script para eliminar únicamente el apartado de "Instrumentos Podados por Estrategia"
(<section class="card">...losersTable...</section>) de /Strategy-bases, manteniendo
intactos WINNERS_DATA (292 registros), LOSERS_DATA (115 registros) y todas las funcionalidades.
"""
import sys

def main():
    with open('dashboard/strategy_bases_page.py', 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Encontrar la sección de losersTable
    idx_tbl = html.find('id="losersTable"')
    if idx_tbl == -1:
        print("id='losersTable' ya no está presente.")
        return

    start_sec = html.rfind('<section class="card">', 0, idx_tbl)
    comment_start = html.rfind('<!-- SECCIÓN 3: INSTRUMENTOS CON MAYOR CANTIDAD DE PÉRDIDAS', 0, start_sec)
    actual_start = comment_start if comment_start != -1 and (start_sec - comment_start) < 200 else start_sec
    end_sec = html.find('</section>', idx_tbl) + len('</section>')

    print(f"Eliminando sección de losersTable desde índice {actual_start} hasta {end_sec}")
    html = html[:actual_start] + html[end_sec:]

    # 2. Agregar guard if (!tbody) return; en renderLosersTable()
    old_render = "function renderLosersTable() {\n\n\n\n        const tbody = document.getElementById('losersTableBody');\n\n\n\n        tbody.innerHTML = '';"
    new_render = "function renderLosersTable() {\n\n\n\n        const tbody = document.getElementById('losersTableBody');\n\n\n\n        if (!tbody) return;\n\n\n\n        tbody.innerHTML = '';"
    
    if old_render in html:
        html = html.replace(old_render, new_render)
        print("Guard if (!tbody) return; añadido a renderLosersTable.")
    else:
        # Fallback con regex si el espaciado varía
        import re
        html = re.sub(
            r"function renderLosersTable\(\)\s*\{\s*const tbody = document\.getElementById\('losersTableBody'\);\s*tbody\.innerHTML = '';",
            "function renderLosersTable() {\n        const tbody = document.getElementById('losersTableBody');\n        if (!tbody) return;\n        tbody.innerHTML = '';",
            html
        )
        print("Guard añadido con regex a renderLosersTable.")

    with open('dashboard/strategy_bases_page.py', 'w', encoding='utf-8') as f:
        f.write(html)

    print("Apartado eliminado exitosamente de /Strategy-bases.")

if __name__ == '__main__':
    main()
