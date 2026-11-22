# -*- coding: utf-8 -*-
"""
Script para ajustar el ancho y diseño de winnersTable:
- Encabezados concisos y compactos
- Badge de estado optimizado (✓ ACTIVO / ⛔ PODADO) con tooltip completo en title
- Padding y fuentes balanceadas para eliminar el desborde horizontal
"""

import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/strategy_bases_page.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Actualizar el thead de winnersTable
old_thead_pattern = re.compile(r'<table id="winnersTable">\s*<thead>.*?</thead>', re.DOTALL)

new_thead = '''<table id="winnersTable">
            <thead>
              <tr>
                <th onclick="sortWinners('rank')" style="width: 32px; text-align: center;">#</th>
                <th onclick="sortWinners('symbol')">INSTRUMENTO</th>
                <th onclick="sortWinners('strategy')">ESTRATEGIA</th>
                <th onclick="sortWinners('trades')" class="num">TRADES</th>
                <th onclick="sortWinners('win_rate')" class="num">WIN RATE</th>
                <th onclick="sortWinners('tp1')" class="num" title="Impactos en Take Profit 1">TP1</th>
                <th onclick="sortWinners('tp2')" class="num" title="Impactos en Take Profit 2">TP2</th>
                <th onclick="sortWinners('tp3')" class="num" title="Extensiones Take Profit 3">TP3</th>
                <th onclick="sortWinners('tp4')" class="num" title="Extensiones Sniper Take Profit 4">TP4</th>
                <th onclick="sortWinners('be')" class="num" title="Salidas protegidas en Break-Even">BE</th>
                <th onclick="sortWinners('pnl')" class="num">PNL NETO ($)</th>
                <th onclick="sortWinners('status')" style="text-align: center;">ESTADO</th>
              </tr>
            </thead>'''

m_th = old_thead_pattern.search(content)
if not m_th:
    print("ERROR: old_thead_pattern not matched")
    sys.exit(1)

content = content[:m_th.start()] + new_thead + content[m_th.end():]
print("thead de winnersTable actualizado.")

# 2. Agregar CSS específico para #winnersTable si no existe
table_compact_css = '''
      #winnersTable {
        width: 100%;
        border-collapse: collapse;
      }
      #winnersTable th {
        background: #0f1720;
        padding: 8px 6px;
        color: #f5bd36;
        font-size: 10.5px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        border-bottom: 1px solid rgba(91, 69, 20, 0.4);
        white-space: nowrap;
        cursor: pointer;
        user-select: none;
      }
      #winnersTable th:hover {
        color: #ffd465;
      }
      #winnersTable td {
        padding: 6px 6px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        white-space: nowrap;
        font-size: 11.5px;
      }
'''

if '#winnersTable {' not in content:
    content = content.replace('</style>', table_compact_css + '\n    </style>', 1)
    print("CSS específico para #winnersTable insertado.")

# 3. Actualizar el row builder en renderWinnersTable
old_builder_pattern = re.compile(
    r'items\.forEach\(\(it, idx\) => \{.*?tbody\.appendChild\(tr\);\s*\}\);',
    re.DOTALL
)

new_builder = '''items.forEach((it, idx) => {
          const tr = document.createElement('tr');
          const isPos = it.pnl > 0;
          const isZero = it.pnl === 0;
          const pnlFormatted = isZero ? '$0.00' : (isPos ? '+$' + it.pnl.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '-$' + Math.abs(it.pnl).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }));
          
          let stratBadge = '';
          if (it.strategy.includes('Malaysian')) {
            stratBadge = 'border: 1px solid #00db79; color: #00db79; background: rgba(0, 219, 121, 0.08);';
          } else if (it.strategy.includes('ORB')) {
            stratBadge = 'border: 1px solid #f5bd36; color: #f5bd36; background: rgba(245, 189, 54, 0.08);';
          } else if (it.strategy.includes('ICT')) {
            stratBadge = 'border: 1px solid #38bdf8; color: #38bdf8; background: rgba(56, 189, 248, 0.08);';
          } else if (it.strategy.includes('Trend')) {
            stratBadge = 'border: 1px solid #c084fc; color: #c084fc; background: rgba(192, 132, 252, 0.08);';
          } else {
            stratBadge = 'border: 1px solid #f5bd36; color: #f5bd36; background: rgba(245, 189, 54, 0.08);';
          }

          let statusBadge = '';
          if (it.is_profitable) {
            statusBadge = `<span class="badge" title="${it.status}" style="border: 1px solid #00db79; color: #00db79; background: rgba(0, 219, 121, 0.1); border-radius: 6px; padding: 2px 7px; font-size: 10px; font-weight: 700; white-space: nowrap; display: inline-flex; align-items: center; gap: 4px;">✓ ACTIVO</span>`;
          } else {
            statusBadge = `<span class="badge" title="${it.status}" style="border: 1px solid #ff453a; color: #ff453a; background: rgba(255, 69, 58, 0.1); border-radius: 6px; padding: 2px 7px; font-size: 10px; font-weight: 700; white-space: nowrap; display: inline-flex; align-items: center; gap: 4px;">⛔ PODADO</span>`;
          }

          let wrColor = it.win_rate >= 50.0 ? '#00db79' : (it.win_rate > 0 ? '#ff453a' : 'var(--m)');
          let pnlColor = isPos ? '#00db79' : (isZero ? 'var(--m)' : '#ff453a');

          tr.innerHTML = `
            <td style="text-align: center;"><strong style="color: #94a3b8; font-size: 11px;">#${idx + 1}</strong></td>
            <td><strong style="color: #fff; font-size: 12.5px;">${it.symbol}</strong><div class="muted" style="font-size: 10px; margin-top: 1px; color: #64748b;">${it.category}</div></td>
            <td><span class="badge" style="${stratBadge} border-radius: 6px; padding: 2px 7px; font-size: 10px; font-weight: 600;">${it.strategy}</span></td>
            <td class="num" style="color: #fff; font-size: 11.5px;">${it.trades.toLocaleString()}</td>
            <td class="num"><strong style="color: ${wrColor}; font-size: 11.5px;">${it.win_rate.toFixed(1)}%</strong></td>
            <td class="num" style="color: #38bdf8; font-weight: 600; font-size: 11.5px;">${it.tp1 > 0 ? it.tp1.toLocaleString() : '-'}</td>
            <td class="num" style="color: #38bdf8; font-weight: 600; font-size: 11.5px;">${it.tp2 > 0 ? it.tp2.toLocaleString() : '-'}</td>
            <td class="num" style="color: #38bdf8; font-weight: 600; font-size: 11.5px;">${it.tp3 > 0 ? it.tp3.toLocaleString() : '-'}</td>
            <td class="num" style="color: #38bdf8; font-weight: 600; font-size: 11.5px;">${it.tp4 > 0 ? it.tp4.toLocaleString() : '-'}</td>
            <td class="num" style="color: #f5bd36; font-weight: 600; font-size: 11.5px;">${it.be > 0 ? it.be.toLocaleString() : '-'}</td>
            <td class="num"><strong style="color: ${pnlColor}; font-size: 11.5px;">${pnlFormatted}</strong></td>
            <td style="text-align: center;">${statusBadge}</td>
          `;
          tbody.appendChild(tr);
        });'''

m_builder = old_builder_pattern.search(content)
if not m_builder:
    print("ERROR: old_builder_pattern not matched")
    sys.exit(1)

content = content[:m_builder.start()] + new_builder + content[m_builder.end():]
print("Row builder de winnersTable actualizado.")

with open('dashboard/strategy_bases_page.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("strategy_bases_page.py actualizado con éxito.")
