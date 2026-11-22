from dashboard.realtime_dashboard import _INSTRUMENTS_HTML
from dashboard.strategy_bases_page import STRATEGY_BASES_HTML


def test_instruments_page_sorts_items_by_status():
    # Verificar que el template HTML de /Instruments contenga la lógica de ordenamiento por estado
    assert "isPrunedA !== isPrunedB" in _INSTRUMENTS_HTML
    assert "return isPrunedA ? 1 : -1" in _INSTRUMENTS_HTML
    assert "const sortedGs" in _INSTRUMENTS_HTML


def test_strategy_bases_page_sorts_items_by_status():
    html = STRATEGY_BASES_HTML
    # Verificar que renderWinnersTable priorice is_profitable: true (Activo) sobre is_profitable: false (Podado)
    assert "a.is_profitable !== b.is_profitable" in html
    assert "return a.is_profitable ? -1 : 1" in html
    assert "sortCol === 'status'" in html


def test_design_elements_preserved():
    html_inst = _INSTRUMENTS_HTML
    html_bases = STRATEGY_BASES_HTML
    
    # Preservación de clases y diseño en /Instruments
    assert "activeBadge" in html_inst
    assert "pruneBadge" in html_inst
    assert "groupItems" in html_inst
    assert "groupHeader" in html_inst
    
    # Preservación de badges y diseño en /Strategy-bases
    assert "winnersTable" in html_bases
    assert "✓ ACTIVO" in html_bases
    assert "⛔ PODADO" in html_bases
