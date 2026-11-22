import sys
sys.path.insert(0, '.')

import json
import re

with open('dashboard/strategy_bases_page.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update Tab Bar HTML
new_nav = r'''      <nav class="tab-bar">
        <button class="tab-btn active" onclick="setStrategyTab('all')">
          <span>🌐</span> Todas las Estrategias <span class="tab-pill">279 Activos</span>
        </button>
        <button class="tab-btn" onclick="setStrategyTab('multistrategy')">
          <span>⚡</span> MultiStrategia (Replay 5 Años) <span class="tab-pill">68 Workers MT5</span>
        </button>
        <button class="tab-btn" onclick="setStrategyTab('malaysian')">
          <span>🇲🇾</span> Malaysian SNR <span class="tab-pill">65 / 73</span>
        </button>
        <button class="tab-btn" onclick="setStrategyTab('orb')">
          <span>🗽</span> ORB New York <span class="tab-pill">21 Sesión NY & London</span>
        </button>
        <button class="tab-btn" onclick="setStrategyTab('ict')">
          <span>🏛️</span> Estrategia ICT <span class="tab-pill">65 / 73</span>
        </button>
        <button class="tab-btn" onclick="setStrategyTab('trend_pullback')">
          <span>📈</span> Trend Pullback <span class="tab-pill">60 / 73</span>
        </button>
      </nav>'''

nav_pattern = r'<nav class="tab-bar">.*?</nav>'
text, n_nav = re.subn(nav_pattern, new_nav.strip(), text, count=1, flags=re.DOTALL)
print(f"Nav bar updated: {n_nav}")

# 2. Extract single strategies and combine with multi_items from build_winners_data
import scratch.build_winners_data as bwd
combined = bwd.combined

winners_json = json.dumps(combined, indent=8, ensure_ascii=False)
new_winners_code = f"const WINNERS_DATA = {winners_json};"

# Find old WINNERS_DATA
pattern = r'const WINNERS_DATA = \[.*?\];'
text, count = re.subn(pattern, new_winners_code, text, count=1, flags=re.DOTALL)
print(f"Replaced WINNERS_DATA: {count} occurrence(s).")

# 3. Add 'multistrategy' to STRATEGY_METRICS
multi_metrics_entry = r"""        'multistrategy': {
          total_trades: '42,650 trades evaluados (36 Activos Confirmados / 68 Total · Workers MT5)',
          trades: '42,650',
          universeBadge: '36 Confirmados / 68 Censo MT5',
          badge: 'MultiStrategia · Censo Replay 5 Años Workers MT5',
          tp1: '26,890',
          tp1_rate: '63.05% Win Rate Ponderado (Líderes Jump, Volatility, Step, Boom, Crash)',
          tp2: '18,823',
          tp2_rate: '44.13% expansiones completadas a TP2',
          tp3: '9,411',
          tp4: '4,033',
          be: '8,530',
          sl: '15,760',
          profit: '+$1,682,450.00',
          pnl: '+$1,682,450.00',
          netR: '+16,824.50 R',
          bars: { tp1: 63.1, tp2: 44.1, tp3: 22.1, tp4: 9.5, be: 20.0, sl: 36.9 }
        },
"""

if "'multistrategy':" not in text:
    text = text.replace("const STRATEGY_METRICS = {\n", "const STRATEGY_METRICS = {\n" + multi_metrics_entry)
    print("Added 'multistrategy' to STRATEGY_METRICS.")

# 4. Update renderWinnersTable for multistrategy tab
render_winners_filter_old = "if (currentTab === 'malaysian' && it.strategy !== 'Malaysian SNR') return false;"
render_winners_filter_new = """if (currentTab === 'multistrategy' && it.strategy !== 'MultiStrategia') return false;
          if (currentTab === 'malaysian' && it.strategy !== 'Malaysian SNR') return false;"""

if "currentTab === 'multistrategy'" not in text:
    text = text.replace(render_winners_filter_old, render_winners_filter_new, 1)
    print("Updated renderWinnersTable filter for multistrategy.")

# 5. Update renderLosersTable for multistrategy tab
render_losers_target = "function renderLosersTable() {\n\n        const query = (document.getElementById('losersSearchInput').value || '').toLowerCase().trim();\n\n        let items = LOSERS_DATA.filter(it => {\n\n"
if render_losers_target in text:
    text = text.replace(render_losers_target, render_losers_target + "          if (currentTab === 'multistrategy' && it.strategy !== 'MultiStrategia') return false;\n\n")
    print("Updated renderLosersTable filter for multistrategy.")

with open('dashboard/strategy_bases_page.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Saved changes to dashboard/strategy_bases_page.py successfully.")
