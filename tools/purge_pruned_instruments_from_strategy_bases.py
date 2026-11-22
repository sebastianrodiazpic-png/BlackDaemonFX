# -*- coding: utf-8 -*-
"""
Script para eliminar de /Strategy-bases todos los instrumentos podados:
1. Filtra WINNERS_DATA para conservar exclusivamente los 177 instrumentos rentables (is_profitable == True).
   Elimina los 115 instrumentos podados de todas las pestañas.
2. Elimina la sección HTML de "Instrumentos Podados por Estrategia" (<section class="card">...losersTable...</section>).
3. Establece LOSERS_DATA = [] y simplifica renderLosersTable a no-op.
4. Actualiza los filtros de estado de la interfaz eliminando la opción de podados.
5. Actualiza los badges y KPIs de STRATEGY_METRICS.
"""
import json
import re

def main():
    with open('dashboard/strategy_bases_page.py', 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Extraer WINNERS_DATA actual
    m_winners = re.search(r'const WINNERS_DATA = (\[.*?\]);', html, re.DOTALL)
    if not m_winners:
        raise ValueError("No se pudo encontrar WINNERS_DATA en dashboard/strategy_bases_page.py")

    winners = json.loads(m_winners.group(1))
    print(f"Total registros originales en WINNERS_DATA: {len(winners)}")

    # Filtrar solo rentables
    profitable_winners = [w for w in winners if w.get("is_profitable") is True]
    print(f"Total registros rentables conservados: {len(profitable_winners)}")

    # Re-indexar rangos
    profitable_winners.sort(key=lambda x: x.get("pnl", 0), reverse=True)
    for idx, item in enumerate(profitable_winners):
        item["rank"] = idx + 1

    # Formatear JSON limpio con indentación 2
    new_winners_json = json.dumps(profitable_winners, indent=2, ensure_ascii=False)
    html = html[:m_winners.start(1)] + new_winners_json + html[m_winners.end(1):]

    # 2. Vaciar LOSERS_DATA = []
    m_losers = re.search(r'const LOSERS_DATA = (\[.*?\]);', html, re.DOTALL)
    if m_losers:
        html = html[:m_losers.start(1)] + "[]" + html[m_losers.end(1):]
        print("LOSERS_DATA establecido a []")

    # 3. Eliminar sección HTML de losersTable
    # Buscar <section class="card"> que contenga losersTable
    idx_losers_tbl = html.find('id="losersTable"')
    if idx_losers_tbl != -1:
        # Encontrar inicio de la sección antes de losersTable
        sec_start = html.rfind('<section class="card">', 0, idx_losers_tbl)
        # Encontrar fin de la sección después de losersTable
        sec_end = html.find('</section>', idx_losers_tbl) + len('</section>')
        # También buscar comentarios previos
        comment_start = html.rfind('<!-- SECCIÓN 3: PÉRDIDAS DETALLADAS', 0, sec_start)
        actual_start = comment_start if comment_start != -1 and (sec_start - comment_start) < 200 else sec_start
        print(f"Eliminando sección HTML de losersTable desde {actual_start} hasta {sec_end}")
        html = html[:actual_start] + html[sec_end:]

    # 4. Actualizar barra de filtros en el HTML para reflejar que solo hay activos rentables
    old_filter_block = re.search(r'<div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap; padding: 2px 0;">[\s\S]*?</div>\s*</div>\s*</div>', html)
    if old_filter_block:
        clean_filter_html = '''<div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap; padding: 2px 0;">
            <div style="display: inline-flex; align-items: center; gap: 8px; font-size: 12px; color: var(--g); background: rgba(0, 219, 121, 0.08); border: 1px solid rgba(0, 219, 121, 0.3); padding: 6px 14px; border-radius: 20px;">
              <span style="font-weight: 700;">✓ 177 Activos Operables Rentables (100% Sincronizados y Libres de Poda)</span>
            </div>
            <input type="hidden" id="statusFilterAll" value="all" checked />
          </div>
        </div>
      </div>'''
        html = html[:old_filter_block.start(0)] + clean_filter_html + html[old_filter_block.end(0):]
        print("Barra de filtros actualizada a vista exclusiva de activos rentables.")

    # 5. Asegurar que renderLosersTable sea seguro (no-op si no existe tbody)
    old_render_losers = re.search(r'function renderLosersTable\(\)\s*\{[\s\S]*?const tbody = document\.getElementById\(\x27losersTableBody\x27\);[\s\S]*?badge\.textContent = `\$\{items\.length\} Activos Excluidos`;\s*\}\s*\}', html)
    if old_render_losers:
        new_render_losers = '''function renderLosersTable() {
        const tbody = document.getElementById('losersTableBody');
        if (tbody) tbody.innerHTML = '';
        const badge = document.getElementById('losersCountBadge');
        if (badge) badge.textContent = '0 Activos Excluidos';
      }'''
        html = html[:old_render_losers.start(0)] + new_render_losers + html[old_render_losers.end(0):]
        print("renderLosersTable simplificada.")

    # 6. Actualizar badges en STRATEGY_METRICS para reflejar Activos Rentables Operables
    html = html.replace('"177 Rentables / 292 Pares"', '"177 Activos Rentables Operables"')
    html = html.replace('"Todas las Estrategias (177 Rentables / 292 Eval · Confluencia Tripartita)"', '"Todas las Estrategias (177 Activos Rentables Operables · Confluencia Tripartita)"')
    html = html.replace('"59 Rentables / 73 Total"', '"59 Activos Rentables Operables"')
    html = html.replace('"ICT (59 Rentables / 73 Total · Confluencia Tripartita)"', '"ICT (59 Activos Rentables Operables · Confluencia Tripartita)"')
    html = html.replace('"63 Rentables / 73 Total"', '"63 Activos Rentables Operables"')
    html = html.replace('"Malaysian SNR Híbrido (63 Rentables / 73 Total · Confluencia Tripartita)"', '"Malaysian SNR Híbrido (63 Activos Rentables Operables · Confluencia Tripartita)"')
    html = html.replace('"17 Rentables / 73 Total"', '"17 Activos Rentables Operables"')
    html = html.replace('"ORB New York (17 Rentables / 73 Total · Confluencia Tripartita)"', '"ORB New York (17 Activos Rentables Operables · Confluencia Tripartita)"')
    html = html.replace('"38 Rentables / 73 Total"', '"38 Activos Rentables Operables"')
    html = html.replace('"Trend Pullback (38 Rentables / 73 Total · Confluencia Tripartita)"', '"Trend Pullback (38 Activos Rentables Operables · Confluencia Tripartita)"')

    with open('dashboard/strategy_bases_page.py', 'w', encoding='utf-8') as f:
        f.write(html)

    print("Actualización completada exitosamente.")

if __name__ == '__main__':
    main()
