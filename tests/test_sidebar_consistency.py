"""Test para verificar la consistencia del diseño y navegación en la barra lateral (brandSidebar).

Verifica que en todas las páginas (/instruments, /decisions, /operator, /account, /performance, /strategy-bases):
1. Estén presentes todos los enlaces de navegación, incluyendo 'Suite Operador', 'Posiciones abiertas' y 'Análisis recientes'.
2. Se mantenga la estructura y diseño homogéneo con /dashboard (.brandSidebar, .brandLogo, .brandName, .sideNav, .sideStatus).
"""

import pytest
from dashboard.decisions_page import DECISIONS_HTML
from dashboard.operator_page import OPERATOR_HTML
from dashboard.account_page import ACCOUNT_HTML
from dashboard.performance_page import PERFORMANCE_HTML
from dashboard.strategy_bases_page import STRATEGY_BASES_HTML


REQUIRED_NAV_LINKS = [
    'href="/"',
    'href="/instruments"',
    'href="/account"',
    'href="/performance"',
    'href="/strategy-bases"',
    'href="/decisions"',
    'href="/operator"',
    'href="/#openPositions"',
    'href="/#recentAnalysis"',
]


def test_decisions_page_sidebar_consistency():
    for link in REQUIRED_NAV_LINKS:
        assert link in DECISIONS_HTML, f"Falta el enlace {link} en DECISIONS_HTML"
    assert 'class="sideStatus"' in DECISIONS_HTML
    assert "scrollbar-color: #3b2a0c transparent" in DECISIONS_HTML
    assert '<a class="active" href="/decisions">⚖ Decisiones de entrada</a>' in DECISIONS_HTML


def test_operator_page_sidebar_consistency():
    for link in REQUIRED_NAV_LINKS:
        assert link in OPERATOR_HTML, f"Falta el enlace {link} en OPERATOR_HTML"
    assert 'class="sideStatus"' in OPERATOR_HTML
    assert "scrollbar-color: #3b2a0c transparent" in OPERATOR_HTML
    assert '<a class="active" href="/operator">🛠 Suite Operador</a>' in OPERATOR_HTML


def test_instruments_sidebar_consistency():
    with open("dashboard/realtime_dashboard.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    idx_inst = content.find("BLACKDAEMON<strong>FX</strong> · Instrumentos para nuevas entradas")
    assert idx_inst != -1, "No se encontró el bloque de /instruments en realtime_dashboard.py"
    inst_section = content[idx_inst - 2000 : idx_inst + 200]
    
    for link in REQUIRED_NAV_LINKS:
        assert link in inst_section, f"Falta el enlace {link} en la barra lateral de /instruments"
    assert 'class="sideStatus"' in inst_section
    assert '<a class="active" href="/instruments">▥ Instrumentos</a>' in inst_section


def test_decisions_page_humanized_ui():
    """Valida que /decisions incluya tabs, kpi-grid, cronología arriba, estrategias abajo y normalización canónica."""
    assert 'class="tab-bar"' in DECISIONS_HTML
    assert 'class="kpi-grid"' in DECISIONS_HTML
    assert 'filterTables' in DECISIONS_HTML
    assert 'humanizeAction' in DECISIONS_HTML
    assert 'humanizeReason' in DECISIONS_HTML
    assert 'compactAction' in DECISIONS_HTML
    assert 'canonStrategy' in DECISIONS_HTML
    assert 'tab-funnel' in DECISIONS_HTML
    assert 'tab-vetoes' in DECISIONS_HTML
    assert 'tab-performance' in DECISIONS_HTML
    assert 'tab-architecture' in DECISIONS_HTML

    # Validar que la cronología diaria (#tblDays) esté ubicada arriba de decisiones por estrategia (#tblStrat)
    pos_days = DECISIONS_HTML.find('id="tblDays"')
    pos_strat = DECISIONS_HTML.find('id="tblStrat"')
    assert pos_days != -1 and pos_strat != -1, "Deben existir #tblDays y #tblStrat en DECISIONS_HTML"
    assert pos_days < pos_strat, "La Cronología (#tblDays) debe estar arriba de Estrategias (#tblStrat) para evitar scroll horizontal"

