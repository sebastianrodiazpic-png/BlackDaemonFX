"""Tests unitarios para la Fase 1 de optimización UI/UX:
Unificación de tokens visuales Black & Gold y aplicación de tabular-nums
para estabilizar números financieros y eliminar el jittering horizontal.
"""

import pytest


def test_realtime_dashboard_black_and_gold_tokens():
    from dashboard.realtime_dashboard import _HTML, _INSTRUMENTS_HTML

    # Comprobar tokens oficiales Black & Gold en _HTML
    assert "--bg: #050708;" in _HTML
    assert "--panel: #0a0e10;" in _HTML
    assert "--line: #5b4514;" in _HTML
    assert "--good: #00db79;" in _HTML
    assert "--bad: #ff453a;" in _HTML
    assert "--accent: #d79b19;" in _HTML

    # Comprobar degradado radial en body
    assert "radial-gradient(circle at 78% 0" in _HTML

    # Comprobar tabular-nums en clases numéricas y tablas
    assert "font-variant-numeric: tabular-nums" in _HTML
    assert "-webkit-font-feature-settings: \"tnum\" 1" in _HTML

    # Comprobar _INSTRUMENTS_HTML
    assert "font-variant-numeric: tabular-nums lining-nums;" in _INSTRUMENTS_HTML


def test_page_loading_ui_tokens():
    from dashboard.page_loading import LOADING_UI

    # Comprobar barra de carga dorada
    assert "linear-gradient(90deg, #d79b19, #ffd465)" in LOADING_UI
    assert "rgba(10, 14, 16, 0.96)" in LOADING_UI
    assert "border-top-color: #f5bd36" in LOADING_UI


def test_account_page_tabular_nums():
    import dashboard.account_page as ap

    assert "font-variant-numeric: tabular-nums lining-nums;" in ap.ACCOUNT_HTML
    assert "font-variant-numeric: tabular-nums;" in ap.ACCOUNT_HTML


def test_trade_audit_tabular_nums():
    import dashboard.trade_audit_page as tap

    assert "font-variant-numeric: tabular-nums lining-nums;" in tap.TRADE_AUDIT_HTML


def test_trade_audit_app_shell_and_breadcrumbs():
    import dashboard.trade_audit_page as tap

    html = tap.TRADE_AUDIT_HTML
    assert '<div class="appShell">' in html
    assert '<aside class="brandSidebar">' in html
    assert '<nav class="sideNav">' in html
    assert '<nav class="breadcrumbs"' in html
    assert 'href="/account"' in html
    assert 'id="breadcrumbTrade"' in html


def test_period_panel_tabular_nums():
    import dashboard.period_panel as pp

    assert "font-variant-numeric:tabular-nums lining-nums" in pp.PANEL


def test_dashboard_command_center_tabs():
    """Fase 3: Validar que el Command Center cuenta con la arquitectura de 4 pestañas
    ergonómicas (Radar, Posiciones, Workers y Recientes) sin scroll vertical infinito.
    """
    from dashboard.realtime_dashboard import _HTML

    # 1. Estilos CSS de las pestañas
    assert ".dashTabsBar" in _HTML
    assert ".dashTabs" in _HTML
    assert ".dashTabBtn" in _HTML
    assert ".tabPane {" in _HTML
    assert ".tabPane.active {" in _HTML
    assert "display: contents !important;" in _HTML

    # 2. Barra de pestañas y botones
    assert 'id="btnTabRadar"' in _HTML
    assert 'id="btnTabPositions"' in _HTML
    assert 'id="btnTabWorkers"' in _HTML
    assert 'id="btnTabRecent"' in _HTML
    assert 'id="tabOpenBadge"' in _HTML

    # 3. Paneles de pestañas
    assert 'id="tabPaneRadar"' in _HTML
    assert 'id="tabPanePositions"' in _HTML
    assert 'id="tabPaneWorkers"' in _HTML
    assert 'id="tabPaneRecent"' in _HTML

    # 4. Elementos operativos organizados en sus respectivos paneles
    assert 'id="confluenceMatrixCard"' in _HTML
    assert 'id="openPositions"' in _HTML
    assert 'id="positionChartCard"' in _HTML
    assert 'id="quarantinePanel"' in _HTML
    assert 'id="workerGrid"' in _HTML
    assert 'id="selectionSummary"' in _HTML
    assert 'id="financialNews"' in _HTML
    assert 'id="recentAnalysis"' in _HTML

    # 5. Funciones JavaScript de control y sincronización
    assert "function switchDashboardTab(" in _HTML
    assert "function initDashboardTabs(" in _HTML
    assert "tabOpenBadge" in _HTML
    assert "blackdaemon_active_dash_tab" in _HTML


def test_instruments_filter_chips_and_group_toggle():
    """Fase 4: Validar que /instruments cuenta con Chips de Filtrado Rápido (Todos,
    Solo Seleccionados, Solo Aprobados, Solo Podados) y botones de acción rápida por grupo.
    """
    from dashboard.realtime_dashboard import _INSTRUMENTS_HTML

    # 1. Estilos CSS de barra de filtro, chips y botones de grupo
    assert ".filterBarWrapper" in _INSTRUMENTS_HTML
    assert ".filterChips" in _INSTRUMENTS_HTML
    assert ".filterChip" in _INSTRUMENTS_HTML
    assert ".filterChip.active" in _INSTRUMENTS_HTML
    assert ".groupToggleBtn" in _INSTRUMENTS_HTML

    # 2. Marcado HTML de chips de filtro y contadores
    assert 'id="filterChips"' in _INSTRUMENTS_HTML
    assert 'id="chipCountAll"' in _INSTRUMENTS_HTML
    assert 'id="chipCountSelected"' in _INSTRUMENTS_HTML
    assert 'id="chipCountActive"' in _INSTRUMENTS_HTML
    assert 'id="chipCountPruned"' in _INSTRUMENTS_HTML

    # 3. Lógica JavaScript de filtrado y control por grupo
    assert "filterStatus = 'ALL'" in _INSTRUMENTS_HTML
    assert "function setFilterStatus(" in _INSTRUMENTS_HTML
    assert "function toggleGroupSymbols(" in _INSTRUMENTS_HTML
    assert "data-group-index=" in _INSTRUMENTS_HTML

    # 4. Cálculo de ratio de selección en updateCount
    assert "(${pct}%)" in _INSTRUMENTS_HTML


def test_live_telemetric_hud_and_toasts():
    """Fase 5: Validar que el Dashboard cuenta con el HUD de telemetría en vivo
    (latencia IPC, pulso esmeralda, reloj, flyout) y contenedor de toasts flotantes.
    """
    from dashboard.realtime_dashboard import _HTML

    # 1. Estilos CSS del HUD y Toasts
    assert ".liveTelemetricHUD" in _HTML
    assert ".hudPulseDot" in _HTML
    assert "@keyframes hudPulseAnim" in _HTML
    assert ".hudFlyout" in _HTML
    assert ".toastContainer" in _HTML
    assert ".bdToast" in _HTML
    assert ".bdToast.show" in _HTML

    # 2. Marcado HTML del HUD y contenedor de Toasts
    assert 'id="liveTelemetricHUD"' in _HTML
    assert 'id="hudPulseDot"' in _HTML
    assert 'id="hudLatency"' in _HTML
    assert 'id="hudClock"' in _HTML
    assert 'id="hudFlyout"' in _HTML
    assert 'id="toastContainer"' in _HTML

    # 3. Lógica JavaScript de medición de latencia y gestión de Toasts
    assert "function showToast(" in _HTML
    assert "function detectStateEvents(" in _HTML
    assert "hudLatency" in _HTML
    assert "performance.now()" in _HTML


def test_strategy_bases_and_decisions_sorting_and_filters():
    """Fase 6: Validar pulido visual, filtros ergonómicos y ordenamiento interactivo
    en las páginas /strategy-bases y /decisions.
    """
    from dashboard.strategy_bases_page import STRATEGY_BASES_HTML
    from dashboard.decisions_page import DECISIONS_HTML

    # --- 1. /strategy-bases: chips de estado, categoría, sticky header y tabular-nums ---
    assert 'id="chipStateAll"' in STRATEGY_BASES_HTML
    assert 'id="chipStateActive"' in STRATEGY_BASES_HTML
    assert 'id="chipStatePruned"' in STRATEGY_BASES_HTML
    assert 'id="chipCatAll"' in STRATEGY_BASES_HTML
    assert 'id="chipCatDeriv"' in STRATEGY_BASES_HTML
    assert 'id="chipCatForex"' in STRATEGY_BASES_HTML
    assert 'id="chipCatMetals"' in STRATEGY_BASES_HTML
    assert 'id="btnClearWinnersSearch"' in STRATEGY_BASES_HTML
    assert "filterChip" in STRATEGY_BASES_HTML
    assert "sortWinners('rank')" in STRATEGY_BASES_HTML
    assert "sortWinners('pnl')" in STRATEGY_BASES_HTML
    assert "function changeCategoryFilter(" in STRATEGY_BASES_HTML
    assert "font-variant-numeric: tabular-nums;" in STRATEGY_BASES_HTML
    assert "position: sticky;" in STRATEGY_BASES_HTML

    # --- 2. /decisions: chips de comités/acción, buscador, sortable headers y tabular-nums ---
    assert 'id="chipDecAll"' in DECISIONS_HTML
    assert 'id="chipDecAllow"' in DECISIONS_HTML
    assert 'id="chipDecVeto"' in DECISIONS_HTML
    assert 'id="chipDecTrades"' in DECISIONS_HTML
    assert 'id="btnClearFilter"' in DECISIONS_HTML
    assert "filterChip" in DECISIONS_HTML
    assert "th.sortable" in DECISIONS_HTML
    assert "sortVetoes('time')" in DECISIONS_HTML
    assert "sortRecent('entry_time')" in DECISIONS_HTML
    assert "function setDecisionFilter(" in DECISIONS_HTML
    assert "function renderVetoesTable(" in DECISIONS_HTML
    assert "function renderRecentTable(" in DECISIONS_HTML
    assert "font-variant-numeric: tabular-nums;" in DECISIONS_HTML




