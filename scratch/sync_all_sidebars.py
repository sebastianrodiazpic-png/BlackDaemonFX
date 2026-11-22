import re

def get_sidebar_html(active_route):
    # Route can be: 'dashboard', 'instruments', 'account', 'performance', 'strategy_bases'
    is_dash = 'active' if active_route == 'dashboard' else ''
    is_inst = 'active' if active_route == 'instruments' else ''
    is_acct = 'active' if active_route == 'account' else ''
    is_perf = 'active' if active_route == 'performance' else ''
    is_sb = 'active' if active_route == 'strategy_bases' else ''

    # Clean class attribute helper
    cls = lambda a: f' class="{a}"' if a else ''

    return f"""<aside class="brandSidebar">
        <img class="brandLogo" src="/assets/blackdaemonfx_logo_v1.jpeg" alt="Logo BlackDaemonFX" />
        <div>
          <div class="brandName">BLACKDAEMON<span>FX</span></div>
          <div class="brandTag">Estrategia · Disciplina · Resultados</div>
        </div>
        <nav class="sideNav">
          <a{cls(is_dash)} href="/">▦ Dashboard</a>
          <a{cls(is_inst)} href="/instruments">▥ Instrumentos</a>
          <a{cls(is_acct)} href="/account">▣ Cuenta en vivo</a>
          <a{cls(is_perf)} href="/performance">📈 Rendimiento</a>
          <a{cls(is_sb)} href="/strategy-bases">📚 Bases de Estrategias</a>
          <a href="/#openPositions">◈ Posiciones abiertas</a>
          <a href="/#recentAnalysis">◷ Análisis recientes</a>
        </nav>
        <div class="sideStatus">
          <b>● Daemon Online</b>
          <div class="sub">Panel local conectado al motor</div>
        </div>
      </aside>"""

# 1. Update dashboard/realtime_dashboard.py
with open('dashboard/realtime_dashboard.py', 'r', encoding='utf-8') as f:
    rtd = f.read()

# Replace in _INSTRUMENTS_HTML
inst_start = rtd.find('_INSTRUMENTS_HTML =')
inst_aside_start = rtd.find('<aside class="brandSidebar">', inst_start)
inst_aside_end = rtd.find('</aside>', inst_aside_start) + len('</aside>')
assert inst_aside_start != -1 and inst_aside_end != -1
new_inst_aside = get_sidebar_html('instruments')
rtd = rtd[:inst_aside_start] + new_inst_aside + rtd[inst_aside_end:]

# Replace in _HTML (Dashboard)
dash_start = rtd.find('_HTML =')
dash_aside_start = rtd.find('<aside class="brandSidebar">', dash_start)
dash_aside_end = rtd.find('</aside>', dash_aside_start) + len('</aside>')
assert dash_aside_start != -1 and dash_aside_end != -1
new_dash_aside = get_sidebar_html('dashboard')
rtd = rtd[:dash_aside_start] + new_dash_aside + rtd[dash_aside_end:]

with open('dashboard/realtime_dashboard.py', 'w', encoding='utf-8') as f:
    f.write(rtd)
print("Updated dashboard/realtime_dashboard.py (_INSTRUMENTS_HTML and _HTML)")

# 2. Update dashboard/account_page.py
with open('dashboard/account_page.py', 'r', encoding='utf-8') as f:
    acct = f.read()

acct_aside_start = acct.find('<aside class="brandSidebar">')
acct_aside_end = acct.find('</aside>', acct_aside_start) + len('</aside>')
assert acct_aside_start != -1 and acct_aside_end != -1
new_acct_aside = get_sidebar_html('account')
acct = acct[:acct_aside_start] + new_acct_aside + acct[acct_aside_end:]

with open('dashboard/account_page.py', 'w', encoding='utf-8') as f:
    f.write(acct)
print("Updated dashboard/account_page.py")

# 3. Update dashboard/performance_page.py
with open('dashboard/performance_page.py', 'r', encoding='utf-8') as f:
    perf = f.read()

perf_aside_start = perf.find('<aside class="brandSidebar">')
perf_aside_end = perf.find('</aside>', perf_aside_start) + len('</aside>')
assert perf_aside_start != -1 and perf_aside_end != -1
new_perf_aside = get_sidebar_html('performance')
perf = perf[:perf_aside_start] + new_perf_aside + perf[perf_aside_end:]

with open('dashboard/performance_page.py', 'w', encoding='utf-8') as f:
    f.write(perf)
print("Updated dashboard/performance_page.py")

# 4. Update dashboard/strategy_bases_page.py
with open('dashboard/strategy_bases_page.py', 'r', encoding='utf-8') as f:
    sb = f.read()

sb_aside_start = sb.find('<aside class="brandSidebar">')
sb_aside_end = sb.find('</aside>', sb_aside_start) + len('</aside>')
assert sb_aside_start != -1 and sb_aside_end != -1
new_sb_aside = get_sidebar_html('strategy_bases')
sb = sb[:sb_aside_start] + new_sb_aside + sb[sb_aside_end:]

with open('dashboard/strategy_bases_page.py', 'w', encoding='utf-8') as f:
    f.write(sb)
print("Updated dashboard/strategy_bases_page.py")

print("All 5 sidebars updated successfully!")
