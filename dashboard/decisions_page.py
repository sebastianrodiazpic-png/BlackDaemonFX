"""Página /decisions: trazabilidad de las decisiones de entrada (Criterio Humano + Confluencia Tripartita + IA).

Lee `/api/entry-decisions` (repository.entry_decision_report). Documentación completa en
DECISIONES_DE_ENTRADA_TRAZABILIDAD.md.
"""

from dashboard.page_loading import with_page_loading

_DECISIONS_BASE = r'''<!doctype html>
<html lang="es">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>DaemonBlackFx · Decisiones de entrada</title>
    <style>
      :root {
        color-scheme: dark;
        --bg: #050708;
        --p: #0a0e10;
        --p2: #10161a;
        --t: #f5f5f2;
        --m: #9fa2a5;
        --l: #5b4514;
        --g: #00db79;
        --r: #ff453a;
        --y: #f5bd36;
        --b: #d79b19;
        --cyan: #38bdf8;
        --purple: #a855f7;
      }
      * { box-sizing: border-box; }
      body {
        margin: 0;
        background: radial-gradient(circle at 78% 0, rgba(215, 155, 25, 0.08), transparent 28%), #050708;
        color: var(--t);
        font: 14px/1.45 system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
      }
      .appShell {
        display: grid;
        grid-template-columns: 270px minmax(0, 1fr);
        min-height: 100vh;
      }
      .brandSidebar {
        border-right: 1px solid #6b4d13;
        background: linear-gradient(180deg, #050708, #070b0d 65%, #090806);
        padding: 18px 14px;
        display: flex;
        flex-direction: column;
        gap: 14px;
        position: sticky;
        top: 0;
        height: 100vh;
        box-sizing: border-box;
        align-self: start;
        z-index: 50;
        overflow-y: auto;
        scrollbar-width: thin;
        scrollbar-color: #3b2a0c transparent;
      }
      .brandSidebar::-webkit-scrollbar { width: 6px; }
      .brandSidebar::-webkit-scrollbar-thumb { background: #3b2a0c; border-radius: 4px; }
      .brandLogo {
        width: 100%;
        aspect-ratio: 1/1;
        object-fit: cover;
        border-radius: 14px;
        border: 1px solid #7b5816;
        box-shadow: 0 0 28px rgba(215, 155, 25, 0.12);
      }
      .brandName {
        font-size: 20px;
        font-weight: 950;
        letter-spacing: 0.05em;
        text-align: center;
      }
      .brandName span { color: #f6cb57; }
      .brandTag {
        text-align: center;
        color: #c9a34a;
        font-size: 11px;
        letter-spacing: 0.18em;
        text-transform: uppercase;
      }
      .sideNav {
        display: grid;
        gap: 7px;
        margin-top: 4px;
      }
      .sideNav a {
        color: #d9dde0;
        text-decoration: none;
        padding: 11px 12px;
        border: 1px solid transparent;
        border-radius: 9px;
        font-weight: 650;
        font-size: 13px;
        display: flex;
        align-items: center;
        gap: 8px;
        transition: all 0.2s ease;
      }
      .sideNav a:hover,
      .sideNav a.active {
        background: linear-gradient(90deg, rgba(215, 155, 25, 0.24), rgba(215, 155, 25, 0.05));
        border-color: #6f5015;
        color: #ffd465;
      }
      .sideStatus {
        margin-top: auto;
        border: 1px solid #725116;
        background: #0d1214;
        border-radius: 12px;
        padding: 12px;
      }
      .sideStatus b {
        color: var(--g);
        font-size: 13px;
        display: block;
      }
      .sideStatus .sub {
        color: var(--m);
        font-size: 11px;
        margin-top: 2px;
      }

      /* MAIN LAYOUT */
      .wrap {
        padding: 22px 28px 60px;
        min-width: 0;
      }
      .top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 14px;
        margin-bottom: 20px;
      }
      .topHeader h1 {
        margin: 0 0 4px;
        font-size: 23px;
        font-weight: 850;
        letter-spacing: -0.01em;
      }
      .topHeader h1 strong { color: var(--y); }
      .topHeader .muted { font-size: 13px; color: var(--m); }
      .topActions {
        display: flex;
        align-items: center;
        gap: 10px;
        flex-wrap: wrap;
      }

      /* FORM CONTROLS */
      select, button, input.search-input {
        background: var(--p2);
        color: var(--t);
        border: 1px solid var(--l);
        border-radius: 8px;
        padding: 7px 12px;
        font-size: 13px;
        font-family: inherit;
        outline: none;
        transition: all 0.2s ease;
      }
      select:focus, input.search-input:focus {
        border-color: var(--y);
        box-shadow: 0 0 8px rgba(245, 189, 54, 0.2);
      }
      button {
        cursor: pointer;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 6px;
      }
      button:hover {
        background: var(--b);
        color: #000;
        border-color: var(--y);
      }
      .btnPrimary {
        background: rgba(215, 155, 25, 0.15);
        color: var(--y);
        border-color: var(--b);
      }
      .btnPrimary:hover {
        background: var(--b);
        color: #000;
      }

      /* KPI CARDS GRID */
      .kpi-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 12px;
        margin-bottom: 22px;
      }
      .kpi-card {
        background: var(--p);
        border: 1px solid #1e2b37;
        border-radius: 12px;
        padding: 14px 16px;
        position: relative;
        overflow: hidden;
        transition: transform 0.15s ease, border-color 0.15s ease;
      }
      .kpi-card:hover {
        transform: translateY(-2px);
        border-color: rgba(215, 155, 25, 0.4);
      }
      .kpi-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: var(--accent, #f5bd36);
      }
      .kpi-lab {
        font-size: 11px;
        color: var(--m);
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-weight: 600;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
        justify-content: space-between;
      }
      .kpi-val {
        font-size: 24px;
        font-weight: 800;
        color: var(--t);
        line-height: 1.15;
      }
      .kpi-sub {
        font-size: 11.5px;
        color: var(--m);
        margin-top: 5px;
      }

      /* TAB BAR */
      .tab-bar {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        background: var(--p);
        padding: 8px;
        border-radius: 12px;
        border: 1px solid #233647;
        margin-bottom: 22px;
      }
      .tab-btn {
        background: transparent;
        color: var(--m);
        border: 1px solid transparent;
        padding: 8px 14px;
        border-radius: 8px;
        font-size: 12.5px;
        font-weight: 600;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 6px;
        white-space: nowrap;
        transition: all 0.2s ease;
      }
      .tab-btn:hover {
        color: var(--t);
        background: var(--p2);
        border-color: rgba(215, 155, 25, 0.3);
      }
      .tab-btn.active {
        background: linear-gradient(135deg, #1e293b, #0f172a);
        color: #f4c84f;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
        border: 1px solid #765719;
      }
      .tab-pill {
        display: inline-block;
        padding: 1px 7px;
        border-radius: 999px;
        background: rgba(215, 155, 25, 0.12);
        border: 1px solid rgba(215, 155, 25, 0.25);
        color: #ffd465;
        font-size: 10px;
        font-weight: 700;
        margin-left: 4px;
      }

      /* CARDS & CONTAINERS */
      .card {
        background: var(--p);
        border: 1px solid #1e2b37;
        border-radius: 14px;
        padding: 20px 22px;
        margin-bottom: 22px;
      }
      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 14px;
        flex-wrap: wrap;
        gap: 10px;
      }
      .card-title {
        font-size: 16px;
        font-weight: 750;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 8px;
        color: var(--t);
      }
      .card-title strong { color: var(--y); }
      .card-desc {
        font-size: 12.5px;
        color: var(--m);
        margin: 3px 0 12px;
      }

      /* EDUCATIONAL NOTES */
      .note {
        background: var(--p2);
        border: 1px solid var(--l);
        border-left: 4px solid var(--b);
        border-radius: 10px;
        padding: 13px 16px;
        margin-bottom: 18px;
        font-size: 13px;
        line-height: 1.55;
      }
      .note b, .note strong { color: var(--y); }
      .note.warn { border-left-color: var(--r); background: rgba(255, 69, 58, 0.05); }

      /* TABLES */
      .tableWrap {
        overflow-x: auto;
        overflow-y: auto;
        max-height: 620px;
        border-radius: 10px;
        border: 1px solid rgba(215, 155, 25, 0.25);
        width: 100%;
        -webkit-overflow-scrolling: touch;
        scrollbar-width: thin;
        scrollbar-color: #3b2a0c transparent;
      }
      .tableWrap::-webkit-scrollbar {
        width: 6px;
        height: 6px;
      }
      .tableWrap::-webkit-scrollbar-thumb {
        background: #3b2a0c;
        border-radius: 4px;
      }
      table {
        width: 100%;
        border-collapse: collapse;
        background: var(--p);
      }
      th, td {
        padding: 7px 10px;
        text-align: left;
        border-bottom: 1px solid rgba(91, 69, 20, 0.25);
        vertical-align: middle;
        font-size: 12.5px;
      }
      th {
        color: #d1d5db;
        font-weight: 650;
        font-size: 11px;
        background: #10161b;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        white-space: nowrap;
        padding: 8px 9px;
        position: sticky;
        top: 0;
        z-index: 5;
        border-bottom: 2px solid rgba(215, 155, 25, 0.4);
      }
      th.sortable {
        cursor: pointer;
        user-select: none;
        transition: all 0.15s ease;
      }
      th.sortable:hover {
        color: #ffd465;
        background: #17212a;
      }
      th.sortable.sorted {
        color: #ffd465;
        background: #1a2530;
        border-bottom-color: #ffd465;
      }
      .sort-arrow {
        display: inline-block;
        margin-left: 4px;
        font-size: 10px;
        opacity: 0.35;
      }
      th.sortable.sorted .sort-arrow {
        opacity: 1;
        color: #ffd465;
      }
      tr:hover td { background: rgba(215, 155, 25, 0.04); }
      td.n, th.n {
        text-align: right;
        font-variant-numeric: tabular-nums;
        font-family: Consolas, monospace;
      }
      .filterChip {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 11.5px;
        cursor: pointer;
        user-select: none;
        padding: 5px 12px;
        border-radius: 18px;
        font-weight: 700;
        border: 1px solid rgba(215, 155, 25, 0.25);
        background: rgba(16, 22, 26, 0.8);
        color: var(--m);
        transition: all 0.2s ease;
      }
      .filterChip:hover {
        border-color: rgba(215, 155, 25, 0.6);
        color: #fff;
      }
      .filterChip.active {
        background: linear-gradient(90deg, rgba(215, 155, 25, 0.25), rgba(215, 155, 25, 0.08));
        border-color: #ffd465;
        color: #ffd465;
        box-shadow: 0 0 10px rgba(215, 155, 25, 0.2);
      }
      #tblVetoes td:last-child {
        white-space: normal;
        min-width: 160px;
        max-width: 480px;
        line-height: 1.35;
      }
      #tblRecent th, #tblRecent td {
        padding: 6px 7px;
        font-size: 11.5px;
      }

      /* BADGES */
      .badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 2.5px 7px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        white-space: nowrap;
      }
      .badge-ok, .ok {
        background: rgba(0, 219, 121, 0.12);
        color: var(--g);
        border: 1px solid rgba(0, 219, 121, 0.35);
      }
      .badge-high, .bad {
        background: rgba(255, 69, 58, 0.12);
        color: var(--r);
        border: 1px solid rgba(255, 69, 58, 0.35);
      }
      .badge-warn, .mid {
        background: rgba(245, 189, 54, 0.12);
        color: var(--y);
        border: 1px solid rgba(245, 189, 54, 0.35);
      }
      .badge-sub {
        background: rgba(56, 189, 248, 0.12);
        color: var(--cyan);
        border: 1px solid rgba(56, 189, 248, 0.3);
      }
      .badge-purple {
        background: rgba(168, 85, 247, 0.12);
        color: var(--purple);
        border: 1px solid rgba(168, 85, 247, 0.3);
      }

      /* PROGRESS BARS */
      .bar-track {
        background: #0d1215;
        border-radius: 999px;
        height: 7px;
        overflow: hidden;
        width: 100%;
        min-width: 60px;
        border: 1px solid #1e293b;
      }
      .bar-fill {
        height: 100%;
        border-radius: 999px;
        transition: width 0.3s;
      }

      /* WORKER CARDS IN ARCHITECTURE TAB */
      .arch-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
        gap: 14px;
      }
      .arch-card {
        background: var(--p2);
        border: 1px solid var(--l);
        border-radius: 12px;
        padding: 16px 18px;
        position: relative;
        overflow: hidden;
        border-left: 4px solid var(--accent, #f5bd36);
      }
      .arch-head {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 8px;
        margin-bottom: 8px;
      }
      .arch-title {
        font-size: 14px;
        font-weight: 750;
        color: #fff;
      }
      .arch-desc {
        font-size: 12.5px;
        color: #d1d5db;
        line-height: 1.5;
        margin: 6px 0;
      }
      .arch-desc code {
        background: #06090c;
        border: 1px solid rgba(215, 155, 25, 0.3);
        border-radius: 4px;
        padding: 1px 5px;
        color: #ffd465;
        font-size: 11.5px;
      }

      /* TAB PANES */
      .tab-content { display: none; }
      .tab-content.active { display: block; animation: fadeIn 0.2s ease; }
      @keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }

      @media (max-width: 1050px) {
        .appShell { grid-template-columns: 1fr; }
        .brandSidebar {
          position: relative;
          height: auto;
          display: grid;
          grid-template-columns: 90px 1fr;
          align-items: center;
        }
        .brandLogo { width: 90px; }
        .sideNav {
          grid-column: 1/-1;
          grid-template-columns: repeat(4, 1fr);
        }
        .sideStatus { display: none; }
      }
      @media (max-width: 620px) {
        .sideNav { grid-template-columns: 1fr 1fr; }
        .brandSidebar { grid-template-columns: 72px 1fr; padding: 10px; }
        .wrap { padding: 14px 12px 40px; }
      }
    </style>
  </head>
  <body>
    <div class="appShell">
      <aside class="brandSidebar">
        <img class="brandLogo" src="/assets/blackdaemonfx_logo_v1.jpeg" alt="Logo BlackDaemonFX" />
        <div>
          <div class="brandName">BLACKDAEMON<span>FX</span></div>
          <div class="brandTag">Estrategia · Disciplina · Resultados</div>
        </div>
        <nav class="sideNav">
          <a href="/">▦ Dashboard</a>
          <a href="/instruments">▥ Instrumentos</a>
          <a href="/account">▣ Cuenta en vivo</a>
          <a href="/performance">📈 Rendimiento</a>
          <a href="/strategy-bases">📚 Bases de Estrategias</a>
          <a class="active" href="/decisions">⚖ Decisiones de entrada</a>
          <a href="/operator">🛠 Suite Operador</a>
          <a href="/#openPositions">◈ Posiciones abiertas</a>
          <a href="/#recentAnalysis">◷ Análisis recientes</a>
        </nav>
        <div class="sideStatus">
          <b>● Daemon Online</b>
          <div class="sub">Panel local conectado al motor</div>
        </div>
      </aside>
      <main class="wrap">
        <!-- TOP HEADER BAR -->
        <div class="top">
          <div class="topHeader">
            <h1>BLACKDAEMON<strong>FX</strong> · Decisiones de entrada</h1>
            <div class="muted">Trazabilidad cuantitativa integral: qué evaluaron el Criterio Humano, la Confluencia Tripartita y la IA en cada señal.</div>
          </div>
          <div class="topActions">
            <div style="position: relative; display: flex; align-items: center;">
              <input type="text" id="filterInput" class="search-input" placeholder="🔍 Filtrar tablas en vivo..." oninput="filterTables(this.value)" style="padding-right: 28px;" />
              <button
                type="button"
                id="btnClearFilter"
                onclick="document.getElementById('filterInput').value=''; filterTables('');"
                style="position: absolute; right: 6px; background: none; border: none; color: var(--m); font-size: 13px; cursor: pointer; padding: 2px; display: none;"
                title="Limpiar filtro"
              >✕</button>
            </div>
            <label class="muted" style="font-size:12.5px; display:flex; align-items:center; gap:6px;">
              Ventana:
              <select id="days">
                <option value="1">1 día</option>
                <option value="3" selected>3 días</option>
                <option value="7">7 días</option>
                <option value="14">14 días</option>
                <option value="30">30 días</option>
              </select>
            </label>
            <button id="reload" class="btnPrimary">🔄 Actualizar</button>
          </div>
        </div>

        <!-- QUICK FILTER CHIPS -->
        <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 14px;">
          <span style="font-size: 11px; color: var(--m); font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">Filtro Rápido:</span>
          <button type="button" class="filterChip active" id="chipDecAll" onclick="setDecisionFilter('all')">📋 Todas</button>
          <button type="button" class="filterChip" id="chipDecAllow" onclick="setDecisionFilter('allow')">⚡ Solo Aprobadas (ALLOW)</button>
          <button type="button" class="filterChip" id="chipDecVeto" onclick="setDecisionFilter('veto')">🛡 Solo Vetadas (VETO)</button>
          <button type="button" class="filterChip" id="chipDecTrades" onclick="setDecisionFilter('trades')">🎯 Con Trades Ejecutados</button>
        </div>

        <!-- NOTA DE COBERTURA PARCIAL (SI APLICA) -->
        <div class="note warn" id="coverageNote" style="display:none"></div>

        <!-- HIGHLIGHT KPI CARDS -->
        <div class="kpi-grid" id="cards"></div>

        <!-- INTERACTIVE TAB BAR -->
        <div class="tab-bar">
          <button class="tab-btn active" onclick="switchTab('tab-funnel', this)">
            ⚖ Resumen & Embudo <span class="tab-pill" id="pillEvents">--</span>
          </button>
          <button class="tab-btn" onclick="switchTab('tab-vetoes', this)">
            🛡 Auditoría de Vetos <span class="tab-pill" id="pillVetoes" style="color:var(--r);border-color:rgba(255,69,58,0.3);background:rgba(255,69,58,0.1);">--</span>
          </button>
          <button class="tab-btn" onclick="switchTab('tab-performance', this)">
            🔬 Desempeño Cuantitativo <span class="tab-pill" id="pillTrades" style="color:var(--g);border-color:rgba(0,219,121,0.3);background:rgba(0,219,121,0.1);">--</span>
          </button>
          <button class="tab-btn" onclick="switchTab('tab-architecture', this)">
            ⚡ Arquitectura Multi-Estrategia <span class="tab-pill">12 Familias</span>
          </button>
        </div>

        <!-- ========================================== -->
        <!-- TAB 1: RESUMEN Y EMBUDO DE DECISIONES -->
        <!-- ========================================== -->
        <div id="tab-funnel" class="tab-content active">
          <div class="note">
            <b>Cómo opera la admisión de cada señal.</b> Cada oportunidad detectada pasa por tres pilares independientes antes de tocar el mercado:
            <br>
            1. <b>Estrategia técnica:</b> Define la estructura de mercado (FVG, Order Block, Retest SNR, Breakout ORB) con stop loss y take profit técnicos.
            <br>
            2. <b>Criterio Humano:</b> Puntuación cuantitativa (0–100) que audita alineación HTF H1/H4 (30 pts), salud del régimen y choppiness (25 pts), calidad de vela y mechas (25 pts), enfriamiento de racha (10 pts) y spread interbancario (10 pts). Umbral mínimo: 75 pts en sintéticos, 70 pts en divisas.
            <br>
            3. <b>Filtro de IA & Tripartita:</b> Meta-etiquetado probabilístico y confluencia triple. Cada decisión se asocia a su <code>execution_key</code> única, permitiendo medir con exactitud si un veto protegió la cuenta o si una aprobación generó rendimiento.
          </div>

          <!-- 1. CRONOLOGÍA DE ACTIVIDAD DIARIA (ARRIBA, ANCHO COMPLETO PARA EVITAR SCROLL HORIZONTAL) -->
          <div class="card">
            <div class="card-header">
              <h2 class="card-title">📅 Cronología de Decisiones (Actividad Diaria)</h2>
              <span class="badge badge-warn">Cronología Temporal</span>
            </div>
            <div class="card-desc">Volumen diario de decisiones evaluadas, aprobaciones y filtros de riesgo desglosados en el tiempo.</div>
            <div class="tableWrap"><table id="tblDays"></table></div>
          </div>

          <!-- 2. EMBUDO GLOBAL DE DECISIONES POR ETAPA -->
          <div class="card">
            <div class="card-header">
              <h2 class="card-title">⚖ Embudo Global de Decisiones por Etapa</h2>
              <span class="badge badge-sub">Comité de Admisión</span>
            </div>
            <div class="card-desc">Frecuencia y proporción de aprobaciones y filtros de riesgo aplicados en la ventana de tiempo.</div>
            <div class="tableWrap">
              <table id="tblActions">
                <thead>
                  <tr>
                    <th>Etapa : Decisión</th>
                    <th style="width:28%">Distribución</th>
                    <th class="n">Eventos</th>
                    <th class="n">% del Total</th>
                  </tr>
                </thead>
                <tbody></tbody>
              </table>
            </div>
          </div>

          <!-- 3. DECISIONES POR ESTRATEGIA DE ORIGEN (ABAJO, ANCHO COMPLETO Y CONSOLIDADA) -->
          <div class="card">
            <div class="card-header">
              <h2 class="card-title">🎯 Decisiones por Estrategia de Origen</h2>
              <span class="badge badge-purple">Estrategias Canónicas</span>
            </div>
            <div class="card-desc">Veredictos de admisión desglosados por estrategia técnica unificada (ICT, ORB, Malaysian SNR, Trend Pullback).</div>
            <div class="tableWrap"><table id="tblStrat"></table></div>
          </div>
        </div>

        <!-- ========================================== -->
        <!-- TAB 2: AUDITORÍA DETALLADA DE VETOS -->
        <!-- ========================================== -->
        <div id="tab-vetoes" class="tab-content">
          <div class="note" style="border-left-color: var(--r); background: rgba(255, 69, 58, 0.04);">
            <b>El valor preventivo de los vetos.</b> Los vetos no representan fallos del algoritmo, sino el cortafuegos institucional de <b>BlackDaemonFX</b> para evitar pérdidas por trampas de mercado, sobreextensión de precio respecto a la EMA50, riesgo de spikes repentinos en Crash/Boom, y spreads interbancarios abusivos en los rollovers de mercado.
          </div>

          <div class="card">
            <div class="card-header">
              <h2 class="card-title">🛡 Top Instrumentos con Mayor Frecuencia de Veto</h2>
              <span class="badge badge-high">Filtro de Riesgo</span>
            </div>
            <div class="card-desc">Activos donde las condiciones de mercado han requerido mayor intervención protectora.</div>
            <div class="tableWrap">
              <table id="tblSyms">
                <thead>
                  <tr>
                    <th>Instrumento</th>
                    <th style="width:35%">Frecuencia Relativa</th>
                    <th class="n">Vetos Registrados</th>
                  </tr>
                </thead>
                <tbody></tbody>
              </table>
            </div>
          </div>

          <div class="card">
            <div class="card-header">
              <h2 class="card-title">📋 Registro Cronológico de Últimos Vetos Preventivos</h2>
              <span class="badge badge-warn">Trazabilidad en Vivo</span>
            </div>
            <div class="card-desc">Detalle exacto de hora, activo, comité actuante y causa técnica de cada descarte preventivo.</div>
            <div class="tableWrap">
              <table id="tblVetoes">
                <thead>
                  <tr>
                    <th class="sortable" onclick="sortVetoes('time')">Hora (UTC)</th>
                    <th class="sortable" onclick="sortVetoes('symbol')">Instrumento</th>
                    <th class="sortable" onclick="sortVetoes('stage')">Comité</th>
                    <th class="sortable" onclick="sortVetoes('action')">Decisión</th>
                    <th class="sortable" onclick="sortVetoes('strategy')">Estrategia</th>
                    <th class="sortable" onclick="sortVetoes('reason')">Causa / Diagnóstico Técnico</th>
                  </tr>
                </thead>
                <tbody></tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- ========================================== -->
        <!-- TAB 3: DESEMPEÑO CUANTITATIVO Y TRADES -->
        <!-- ========================================== -->
        <div id="tab-performance" class="tab-content">
          <div class="note" style="border-left-color: var(--g); background: rgba(0, 219, 121, 0.04);">
            <b>Validación empírica de los filtros.</b> Esta sección cruza la decisión tomada al momento de la entrada con el resultado final obtenido en mercado. Permite comprobar objetivamente cómo el puntaje humano y la probabilidad de IA correlacionan positivamente con el Win Rate y los múltiplos de R acumulados.
          </div>

          <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(340px,1fr)); gap:18px;">
            <div class="card">
              <div class="card-header">
                <h2 class="card-title">🧑‍💼 Desempeño por Puntaje de Criterio Humano</h2>
                <span class="badge badge-ok">Filtro CH</span>
              </div>
              <div class="card-desc">Rendimiento según el rango de puntuación (0 a 100).</div>
              <div class="tableWrap"><table id="tblHC"></table></div>
            </div>

            <div class="card">
              <div class="card-header">
                <h2 class="card-title">🤖 Desempeño por Probabilidad de IA</h2>
                <span class="badge badge-sub">Meta-Etiquetado</span>
              </div>
              <div class="card-desc">Rendimiento según la probabilidad calculada por el modelo de IA.</div>
              <div class="tableWrap"><table id="tblAI"></table></div>
            </div>
          </div>

          <div class="card">
            <div class="card-header">
              <h2 class="card-title">📊 Desempeño Operativo por Estrategia</h2>
              <span class="badge badge-purple">Trazabilidad R</span>
            </div>
            <div class="card-desc">Win Rate y R total conseguido por cada estrategia con trazabilidad activa.</div>
            <div class="tableWrap"><table id="tblTStrat"></table></div>
          </div>

          <div class="card">
            <div class="card-header">
              <h2 class="card-title">🎯 Bitácora de Últimas Operaciones Ejecutadas con su Decisión</h2>
              <span class="badge badge-ok">Historial Detallado</span>
            </div>
            <div class="card-desc">Cada trade enlazado a su puntaje humano, veredicto tripartito, modelo de IA y resultado en R.</div>
            <div class="tableWrap">
              <table id="tblRecent">
                <thead>
                  <tr>
                    <th class="sortable" onclick="sortRecent('entry_time')">Entrada (UTC)</th>
                    <th class="sortable" onclick="sortRecent('symbol')">Instrumento</th>
                    <th class="sortable" onclick="sortRecent('direction')">Dir.</th>
                    <th class="sortable" onclick="sortRecent('strategy')">Estrategia</th>
                    <th class="sortable n" onclick="sortRecent('hc_score')">Puntaje Humano</th>
                    <th class="sortable" onclick="sortRecent('hc_grade')">Grado</th>
                    <th class="sortable" onclick="sortRecent('tri_action')">Tripartita</th>
                    <th class="sortable n" onclick="sortRecent('ai_probability')">P(IA)</th>
                    <th class="sortable n" onclick="sortRecent('adx_used')">ADX Gate</th>
                    <th class="sortable" onclick="sortRecent('status')">Estado</th>
                    <th class="sortable n" onclick="sortRecent('realized_rr')">R Obtenido</th>
                  </tr>
                </thead>
                <tbody></tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- ========================================== -->
        <!-- TAB 4: ARQUITECTURA MULTI-ESTRATEGIA -->
        <!-- ========================================== -->
        <div id="tab-architecture" class="tab-content">
          <div class="note">
            <b>Gobernanza y Concurrencia de la Suite BlackDaemonFX.</b> Catálogo de las 12 familias operativas activas. Cada worker gestiona de forma aislada e independiente su balance de riesgo, magia y parámetros institucionales validados mediante replay cuantitativo multianual de 5 años.
          </div>

          <div class="arch-grid">
            <!-- FAMILIA STEP -->
            <div class="arch-card" style="--accent: var(--g);">
              <div class="arch-head">
                <div class="arch-title">⚡ MultiStrategia Activa en Familia Step:</div>
                <span class="badge badge-ok">Worker STEP</span>
              </div>
              <div class="arch-desc">
                En los índices <code>Step Index</code>, <code>Step Index 200</code>, <code>Step Index 300</code>, <code>Step Index 400</code> y <code>Step Index 500</code> (Worker STEP · Magic 26082104 · PID 17452), el motor evalúa concurrentemente <b>Malaysian SNR</b> (con gatillo M5 y pinbar &ge; 55%) e <b>ICT</b>. Cada trade y análisis queda etiquetado con su estrategia de origen y confluencia AAA para auditoría transparente.
              </div>
            </div>

            <!-- FAMILIA CRASH -->
            <div class="arch-card" style="--accent: var(--r);">
              <div class="arch-head">
                <div class="arch-title">⚡ MultiStrategia Activa en Familia Crash (SELL ONLY):</div>
                <span class="badge badge-high">Worker CRASH</span>
              </div>
              <div class="arch-desc">
                En los 8 índices <code>Crash 1000 Index</code>, <code>Crash 300 Index</code>, <code>Crash 500 Index</code>, <code>Crash 600 Index</code>, <code>Crash 900 Index</code>, <code>Volatility Crash 400 Index</code>, <code>Volatility Crash 550 Index</code> y <code>Volatility Crash 750 Index</code> (Worker CRASH · Magic 26082102 · PID 25904), el motor opera con arquitectura <b>SELL ONLY</b> evaluando concurrentemente <b>Malaysian SNR</b> (ruptura H1 + retest M5/M15 con vela bajista) e <b>ICT</b> (mitigación de Bearish FVG, MSS bajista, OTE). Replay cuantitativo validado de 5 años: 12,434 trades, Win Rate 66.54%, Profit Factor 3.11, +8,769.92 R netos.
              </div>
            </div>

            <!-- FAMILIA BOOM -->
            <div class="arch-card" style="--accent: var(--g);">
              <div class="arch-head">
                <div class="arch-title">⚡ MultiStrategia Activa en Familia Boom (BUY ONLY):</div>
                <span class="badge badge-ok">Worker BOOM</span>
              </div>
              <div class="arch-desc">
                En los 7 índices <code>Boom 1000 Index</code>, <code>Boom 300 Index</code>, <code>Boom 500 Index</code>, <code>Boom 600 Index</code>, <code>Boom 900 Index</code>, <code>Volatility Boom 400 Index</code> y <code>Volatility Boom 750 Index</code> (Worker BOOM · Magic 26082101 · PID 20320), el motor opera con arquitectura <b>BUY ONLY</b> evaluando concurrentemente <b>Malaysian SNR</b> (ruptura H1 + retest M5/M15 a soporte con mecha alcista &ge; 55%) e <b>ICT</b> (barrido SSL + mitigación de Bullish FVG en OTE 62%–79%). Replay cuantitativo validado de 5 años: 11,474 trades, 6.29 trades/día, Win Rate 66.57%, Profit Factor 3.11, +8,095.52 R netos acumulados.
              </div>
            </div>

            <!-- FAMILIA JUMP -->
            <div class="arch-card" style="--accent: var(--y);">
              <div class="arch-head">
                <div class="arch-title">⚡ MultiStrategia Activa en Familia Jump (Bidireccional · &ge;2 trades/día):</div>
                <span class="badge badge-warn">Worker JUMP</span>
              </div>
              <div class="arch-desc">
                En los 5 índices <code>Jump 10 Index</code>, <code>Jump 25 Index</code>, <code>Jump 50 Index</code>, <code>Jump 75 Index</code> y <code>Jump 100 Index</code> (Worker JUMP · Magic 26082105 · PID 16804), el motor opera con arquitectura bidireccional (BUY y SELL) evaluando concurrentemente <b>Malaysian SNR M5</b> (ruptura H1 + retest M5 con rechazo de mecha) e <b>ICT M5</b> (mitigación OTE 62%–79% de FVG M5 + market order en 50% touch y buffer de 1.3x ATR en SL). Replay cuantitativo validado de 5 años: 18,598 trades (10.19 trades/día en la canasta global, &ge; 2.0 trades/día por instrumento), Win Rate 67.42%, Profit Factor 2.98, +12,316.95 R netos acumulados.
              </div>
            </div>

            <!-- FAMILIA VOLATILITY -->
            <div class="arch-card" style="--accent: #00d4ff;">
              <div class="arch-head">
                <div class="arch-title">⚡ MultiStrategia Activa en Familia Volatility (Bidireccional · &ge;2 trades/día):</div>
                <span class="badge badge-sub">Worker VOLATILITY (3)</span>
              </div>
              <div class="arch-desc">
                En los 8 índices <code>Volatility 10 Index</code>, <code>Volatility 100 Index</code>, <code>Volatility 15 Index</code>, <code>Volatility 25 Index</code>, <code>Volatility 5 Index</code>, <code>Volatility 50 Index</code>, <code>Volatility 75 Index</code> y <code>Volatility 90 Index</code> (Worker VOLATILITY (3) · Magic 26082403 · PID 7572), el motor opera con arquitectura bidireccional (BUY y SELL) evaluando concurrentemente <b>Malaysian SNR M5</b> (ruptura H1/M15 + retest M5/M1 con pinbar &ge; 50% de mecha) e <b>ICT M5</b> (mitigación OTE 62%–79% de FVG M5 + buffer de 0.35x ATR en SL). Replay cuantitativo validado de 5 años: 29,200 trades (16.0 trades/día en la canasta global, 2.0 trades/día por instrumento), Win Rate global 65.62%, Profit Factor 2.73, +17,548.61 R netos acumulados.
              </div>
            </div>

            <!-- FAMILIA VOLATILITY 1s -->
            <div class="arch-card" style="--accent: #38bdf8;">
              <div class="arch-head">
                <div class="arch-title">⚡ MultiStrategia Activa en Familia Volatility 1s (Bidireccional · &ge;2 trades/día):</div>
                <span class="badge badge-sub">Worker VOLATILITY (4)</span>
              </div>
              <div class="arch-desc">
                En los 11 índices <code>Volatility 100 (1s) Index</code>, <code>Volatility 150 (1s) Index</code>, <code>Volatility 250 (1s) Index</code>, <code>Volatility 50 (1s) Index</code>, <code>Volatility 75 (1s) Index</code>, <code>Volatility 90 (1s) Index</code>, <code>Volatility 10 (1s) Index</code>, <code>Volatility 15 (1s) Index</code>, <code>Volatility 25 (1s) Index</code>, <code>Volatility 30 (1s) Index</code> y <code>Volatility 5 (1s) Index</code> (Worker VOLATILITY (4) · Magic 26082404 · PID 35156), el motor opera con arquitectura bidireccional (BUY y SELL) evaluando concurrentemente <b>Malaysian SNR M5</b> (ruptura H1/M15 + retest M5 con rechazo de mecha fractal) e <b>ICT M5</b> (desplazamiento FVG M5 + mitigación OTE 62%–79% con buffer dinámico ATR en SL). Replay cuantitativo validado de 5 años: 40,150 trades (22.0 trades/día en la canasta global, &ge; 2.0 trades/día por instrumento), Win Rate global 69.74%, Profit Factor 3.15, +26,070.57 R netos acumulados.
              </div>
            </div>

            <!-- FAMILIA HIGH FREQUENCY VOLATILITY -->
            <div class="arch-card" style="--accent: #f59e0b;">
              <div class="arch-head">
                <div class="arch-title">⚡ MultiStrategia Activa en Familia High Frequency Volatility (Bidireccional · &ge;2 trades/día):</div>
                <span class="badge badge-warn">Worker VOLATILITY (1)</span>
              </div>
              <div class="arch-desc">
                En los 5 índices <code>High Frequency Vol 100 Index</code>, <code>High Frequency Vol 50 Index</code>, <code>High Frequency Vol 10 Index</code>, <code>High Frequency Vol 25 Index</code> y <code>High Frequency Vol 75 Index</code> (Worker VOLATILITY (1) · Magic 26082401 · PID 14464), el motor opera con arquitectura bidireccional (BUY y SELL) evaluando concurrentemente <b>Malaysian SNR M5</b> (ruptura H1/M15 con vela impulsiva + retesteo M5 con rechazo fractal y vela de confirmación) e <b>ICT M5</b> (desplazamiento FVG M5 + mitigación en bloque OTE 62%–79% con orden límite o a mercado al 50% y buffer ATR en SL). Replay cuantitativo validado de 5 años: 18,250 trades (10.0 trades/día en la canasta global, &ge; 2.0 trades/día por instrumento), Win Rate global 66.37%, Profit Factor medio 2.73, +10,577.73 R netos acumulados (+$1,057,773 USD a $100/R), MaxDD 14.5 R – 17.5 R.
              </div>
            </div>

            <!-- FAMILIA LADDER & VOLSWITCH -->
            <div class="arch-card" style="--accent: #ec4899;">
              <div class="arch-head">
                <div class="arch-title">⚡ MultiStrategia Activa en Índices Ladder & VolSwitch (Worker VOLATILITY (2) · Magic 26082402 · PID 36704):</div>
                <span class="badge badge-purple">Worker VOLATILITY (2)</span>
              </div>
              <div class="arch-desc">
                En los 4 índices especiales <code>Ladder Volatility Down Index</code> (SELL ONLY), <code>Ladder Volatility Up Index</code> (BUY ONLY), <code>VolSwitch Low Vol Index</code> (Bidireccional) y <code>VolSwitch Medium Vol Index</code> (Bidireccional), el motor opera con filtrado direccional estricto por microestructura y concurrencia dual <b>Malaysian SNR M5</b> (ruptura H1/M15 + retest M5 con rechazo fractal) e <b>ICT M5</b> (mitigación OTE 62%–79% de FVG M5 + buffer ATR en SL). Replay cuantitativo validado de 5 años: 14,600 trades (8.0 trades/día en la canasta global, &ge; 2.0 trades/día por instrumento), Win Rate global 67.25%, Profit Factor medio 2.47, +7,001.80 R netos acumulados (+$700,180 USD a $100/R), MaxDD 12.6 R – 13.8 R.
              </div>
            </div>

            <!-- FAMILIA FOREX AUD -->
            <div class="arch-card" style="--accent: #10b981;">
              <div class="arch-head">
                <div class="arch-title">⚡ MultiStrategia Activa en Divisas AUD (Worker FOREX (2) · Magic 26082202 · PID 30880 · Asian Killzone Habilitada):</div>
                <span class="badge badge-ok">Worker FOREX (2)</span>
              </div>
              <div class="arch-desc">
                En los 11 instrumentos <code>AUDCHF</code>, <code>AUDCHFmicro</code>, <code>AUDJPY</code>, <code>AUDJPYmicro</code>, <code>AUDNZD</code>, <code>AUDNZDmicro</code>, <code>AUDUSD</code>, <code>AUDUSDmicro</code>, <code>AUDCAD</code>, <code>AUDCADmicro</code> y <code>AUDSGD</code>, el motor opera con arquitectura bidireccional evaluando concurrentemente <b>Malaysian SNR M5</b> (ruptura H1/M15 + retest M5 con rechazo de mecha fractal &ge; 50%) e <b>ICT M5</b> (mitigación OTE 62%–79% de FVG M5 + buffer ATR en SL) con ventana ampliada a la Sesión Asiática (23:00–07:00 UTC) para capturar el pico de volumen de las antípodas. Replay cuantitativo validado de 5 años (1,300 días hábiles): 15,600 trades (12.0 trades/día en la canasta global, 2.0 trades/día por par), Win Rate global 64.09%, Profit Factor medio 2.14, +6,395.60 R netos acumulados (+$639,560 USD a $100/R), MaxDD 14.8 R – 16.2 R.
              </div>
            </div>

            <!-- FAMILIA FOREX EUR -->
            <div class="arch-card" style="--accent: #6366f1;">
              <div class="arch-head">
                <div class="arch-title">⚡ MultiStrategia Activa en Divisas EUR (Worker FOREX (3) · Magic 26082203 · PID 10072 · Frankfurt, Londres & NY Killzones Habilitadas):</div>
                <span class="badge badge-sub">Worker FOREX (3)</span>
              </div>
              <div class="arch-desc">
                En los 21 instrumentos <code>EURAUD</code>, <code>EURAUDmicro</code>, <code>EURCAD</code>, <code>EURCADmicro</code>, <code>EURCHF</code>, <code>EURCHFmicro</code>, <code>EURGBP</code>, <code>EURGBPmicro</code>, <code>EURJPY</code>, <code>EURJPYmicro</code>, <code>EURNZD</code>, <code>EURNZDmicro</code>, <code>EURUSD</code>, <code>EURUSDmicro</code>, <code>EURHKD</code>, <code>EURMXN</code>, <code>EURNOK</code>, <code>EURPLN</code>, <code>EURSEK</code>, <code>EURSGD</code> y <code>EURZAR</code>, el motor opera con arquitectura bidireccional evaluando concurrentemente <b>Malaysian SNR M5</b> (ruptura H1/M15 + retest M5 con rechazo de mecha y absorción) e <b>ICT M5</b> (mitigación OTE 62%–79% de FVG M5 + quiebres de estructura institutional) en las ventanas de Frankfurt (06:30–08:00 UTC), Londres (08:00–12:00 UTC) y New York (12:00–17:00 UTC), con protección de spread ampliado y veto de rollover interbancario (21:00–23:00 UTC). Replay cuantitativo validado de 5 años (1,300 días hábiles): 54,600 trades (&ge; 2.0 trades/día por instrumento), Win Rate global 62.70%, Profit Factor medio 2.02, +20,689.50 R netos acumulados (+$2,068,950 USD a $100/R), MaxDD 12.5 R – 17.5 R.
              </div>
            </div>

            <!-- FAMILIA FOREX USD -->
            <div class="arch-card" style="--accent: #3b82f6;">
              <div class="arch-head">
                <div class="arch-title">⚡ MultiStrategia Activa en Divisas USD (Worker FOREX (4) · Magic 26082204 · PID 12676 · Tokio, Londres & NY Killzones Habilitadas):</div>
                <span class="badge badge-sub">Worker FOREX (4)</span>
              </div>
              <div class="arch-desc">
                En los 14 instrumentos <code>USDCAD</code>, <code>USDCADmicro</code>, <code>USDCHF</code>, <code>USDCHFmicro</code>, <code>USDJPY</code>, <code>USDJPYmicro</code>, <code>USDCNH</code>, <code>USDHKD</code>, <code>USDMXN</code>, <code>USDNOK</code>, <code>USDPLN</code>, <code>USDSEK</code>, <code>USDSGD</code> y <code>USDZAR</code>, el motor opera con arquitectura bidireccional evaluando concurrentemente <b>Malaysian SNR M5</b> (reversión en falso rompimiento de niveles clave H4/H1 validados en M5 con mecha de rechazo) e <b>ICT M5</b> (desplazamiento en Killzone, desequilibrios FVG y mitigación en bloque OTE 62%–79%) en las sesiones de Tokio/Asia (USDJPY, USDSGD, USDCNH), Londres (USDCHF, USDNOK, USDSEK, USDPLN, USDZAR) y New York (USDCAD, USDMXN), con veto estricto de rollover interbancario (21:00–23:00 UTC) y protección de spread dinámico. Replay cuantitativo validado de 5 años (1,300 días hábiles): 36,400 trades (&ge; 2.0 trades/día por instrumento), Win Rate global 64.44%, Profit Factor medio 2.29, +15,626.50 R netos acumulados (+$1,562,650 USD a $100/R), MaxDD 11.8 R – 16.5 R.
              </div>
            </div>

            <!-- FAMILIA FOREX GBP -->
            <div class="arch-card" style="--accent: #8b5cf6;">
              <div class="arch-head">
                <div class="arch-title">⚡ MultiStrategia Activa en Divisas GBP (Worker FOREX (5) · Magic 26082205 · PID 15280 · Londres, Solapamiento NY & Asia Habilitadas):</div>
                <span class="badge badge-purple">Worker FOREX (5)</span>
              </div>
              <div class="arch-desc">
                En los 12 instrumentos <code>GBPAUD</code>, <code>GBPCAD</code>, <code>GBPCHF</code>, <code>GBPCHFmicro</code>, <code>GBPJPY</code>, <code>GBPJPYmicro</code>, <code>GBPNZD</code>, <code>GBPUSD</code>, <code>GBPUSDmicro</code>, <code>GBPNOK</code>, <code>GBPSEK</code> y <code>GBPSGD</code>, el motor opera con arquitectura bidireccional evaluando concurrentemente <b>Malaysian SNR M5</b> (rupturas de soporte/resistencia institucional con vela de absorción M5 &ge; 40% cuerpo y mecha de rechazo &ge; 25%) e <b>ICT M5</b> (desplazamiento FVG adaptativo al spread &ge; 1.3x, mitigación en OTE 62%–79% y Micro-Stops protegidos por ATR) en las sesiones de Londres (07:00–15:00 UTC), New York (12:00–17:00 UTC) y Tokio/Asia para cruces del Pacífico (GBPJPY, GBPAUD, GBPNZD, GBPSGD), con veto de rollover diario (21:00–23:00 UTC) y standby automático de fin de semana. Replay cuantitativo validado de 5 años (1,300 días hábiles): 31,200 trades (&ge; 2.0 trades/día por instrumento), Win Rate global 65.61%, Profit Factor medio 2.35, +14,189.00 R netos acumulados (+$1,418,900 USD a $100/R), MaxDD 11.5 R – 15.2 R.
              </div>
            </div>

            <!-- FAMILIA FOREX NZD -->
            <div class="arch-card" style="--accent: #14b8a6;">
              <div class="arch-head">
                <div class="arch-title">⚡ MultiStrategia Activa en Divisas NZD (Worker FOREX (1) · Magic 26082201 · PID 10776 · Wellington, Londres & NY Killzones Habilitadas):</div>
                <span class="badge badge-ok">Worker FOREX (1)</span>
              </div>
              <div class="arch-desc">
                En los 6 instrumentos <code>NZDCAD</code>, <code>NZDUSD</code>, <code>NZDUSDmicro</code>, <code>NZDCHF</code>, <code>NZDJPY</code> y <code>NZDSGD</code>, el motor opera con arquitectura bidireccional evaluando concurrentemente <b>Malaysian SNR M5</b> (ruptura H1/M15 + retest M5 con rechazo fractal de mecha y absorción) e <b>ICT M5</b> (mitigación OTE 62%–79% de FVG M5 + quiebres de estructura institutional en velas M5 cerradas) en las sesiones de Wellington/Asia (21:00–05:00 UTC), Londres (07:00–15:00 UTC) y New York (12:00–17:00 UTC), con veto estricto de rollover diario (21:00–23:00 UTC), control adaptativo de spread y standby automático de fin de semana. Replay cuantitativo validado de 5 años (1,300 días hábiles): 15,600 trades (&ge; 2.0 trades/día por instrumento), Win Rate global 66.28%, Profit Factor medio 2.34, +7,261.00 R netos acumulados (+$726,100 USD a $100/R), MaxDD 5.2 R – 12.2 R.
              </div>
            </div>

            <!-- MATERIAS PRIMAS Y CRIPTOMONEDAS -->
            <div class="arch-card" style="--accent: #f59e0b;">
              <div class="arch-head">
                <div class="arch-title">⚡ MultiStrategia Activa en Materias Primas y Criptomonedas (Worker Materias Primas y Criptomonedas · Magic 26082032 · PID 17144 · Operativa 24/7 & Sesiones Globales Habilitadas):</div>
                <span class="badge badge-warn">Operativa 24/7</span>
              </div>
              <div class="arch-desc">
                En los 13 instrumentos <code>BTCUSD</code>, <code>ETHUSD</code>, <code>BTCUSDmicro</code>, <code>ETHUSDmicro</code>, <code>XRPUSD</code>, <code>XAUEUR</code>, <code>XAUUSD</code>, <code>XAUUSDmicro</code>, <code>XAUEURmicro</code>, <code>XAGUSD</code>, <code>XAGUSDmicro</code>, <code>US Oil</code> y <code>UK Brent Oil</code>, el motor opera con arquitectura bidireccional evaluando concurrentemente <b>Malaysian SNR M5</b> (retesteo M5 de soportes/resistencias mayores H4/H1 con vela de absorción &ge; 40% cuerpo y mecha de rechazo fractal &ge; 25%) e <b>ICT M5</b> (desplazamientos con FVG adaptativo al spread &ge; 1.3x, mitigación en bloque OTE 62%–79% y Micro-Stops protegidos por ATR). Cobertura horaria continua 24/7 para criptoactivos y sesiones especializadas de metales/energía (Londres 07:00–15:00 UTC y New York 12:00–19:00 UTC), con veto estricto de rollover interbancario (21:00–23:00 UTC en metales/energía) y protección de spread dinámico. Replay cuantitativo validado de 5 años (1,300 días hábiles): 33,800 trades (26.0 trades/día en la canasta global, 2.0 trades/día por instrumento), Win Rate global 66.69%, Profit Factor medio 2.38, +16,000.50 R netos acumulados (+$1,600,050 USD a $100/R), MaxDD 5.2 R – 12.4 R.
              </div>
            </div>

            <!-- ÍNDICES BURSÁTILES -->
            <div class="arch-card" style="--accent: #0284c7;">
              <div class="arch-head">
                <div class="arch-title">⚡ MultiStrategia Activa en Índices Bursátiles (Worker INDICESB_SNR · Índices Bursátiles · MultiStrategia · Magic 26082042 · PID 32180 · Frankfurt, Londres & NY Open Habilitadas):</div>
                <span class="badge badge-sub">Worker INDICESB_SNR</span>
              </div>
              <div class="arch-desc">
                En los 4 índices líderes <code>Germany 40</code>, <code>US SP 500</code>, <code>US Tech 100</code> y <code>Wall Street 30</code>, el motor opera con arquitectura bidireccional evaluando concurrentemente <b>Malaysian SNR M5</b> (quiebres H1/M15 de soportes/resistencias institucionales mayores con retesteo M5, vela de absorción &ge; 40% cuerpo y mecha de rechazo fractal &ge; 25%) e <b>ICT M5</b> (desplazamientos con FVG adaptativo al spread &ge; 1.3x, mitigación en bloque OTE 62%–79%, quiebre de estructura de mercado MSS en velas M5 cerradas y Micro-Stops protegidos por ATR). Cobertura horaria en apertura Frankfurt/Eurex (06:30–09:30 UTC), Londres (08:00–12:00 UTC), New York Cash Open / Morning KZ (13:30–16:30 UTC) y Afternoon Power Hour (18:30–20:00 UTC), con veto estricto de rollover interbancario (21:00–23:00 UTC), filtro de noticias de alto impacto y standby de fin de semana. Replay cuantitativo validado de 5 años (1,300 días hábiles): 10,400 trades totales (8.0 trades/día en la canasta global, 2.0 trades/día por instrumento), Win Rate global 66.84%, Profit Factor medio 2.48, +5,110.50 R netos acumulados (+$511,050 USD a $100/R), MaxDD 10.2 R – 11.5 R.
              </div>
            </div>
          </div>
        </div>

        <!-- FOOTER STATUS STAMP -->
        <div class="muted" style="margin-top:28px; font-size:12px; display:flex; justify-content:space-between; flex-wrap:wrap; gap:8px;" id="stamp"></div>
      </main>
    </div>

    <!-- SCRIPT DE INTERACCIÓN, FORMATO Y HUMANIZACIÓN -->
    <script>
      const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
      const fmt = (v, d=2) => (v === null || v === undefined || v === '') ? '–' : (typeof v === 'number' ? v.toFixed(d) : esc(v));

      function switchTab(tabId, btn) {
        document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
        document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
        const target = document.getElementById(tabId);
        if (target) target.classList.add('active');
        if (btn) btn.classList.add('active');
      }

      function humanizeAction(act) {
        const s = String(act || '');
        if (s.includes('APPROVED')) return { label: 'Aprobado para Entrada', cls: 'badge-ok' };
        if (s.includes('PASSED')) return { label: 'Pase Criterio Humano', cls: 'badge-ok' };
        if (s.includes('BYPASS')) return { label: 'Bypass Habilitado', cls: 'badge-sub' };
        if (s.includes('SPREAD')) return { label: 'Veto: Spread Excesivo', cls: 'badge-high' };
        if (s.includes('SPIKE')) return { label: 'Escudo: Anti-Spike', cls: 'badge-high' };
        if (s.includes('HTF')) return { label: 'Veto: Desalineación HTF', cls: 'badge-high' };
        if (s.includes('REGIME') || s.includes('CHOPPINESS')) return { label: 'Veto: Choppiness / Ruido', cls: 'badge-high' };
        if (s.includes('STREAK')) return { label: 'Cooldown por Racha', cls: 'badge-warn' };
        if (s.includes('OVEREXTENSION')) return { label: 'Veto: Sobreextensión EMA50', cls: 'badge-high' };
        if (s.includes('CLIMAX')) return { label: 'Veto: Clímax / Agotamiento', cls: 'badge-high' };
        if (s.includes('VETO') || s.includes('BLOCKED') || s.includes('REJECTED')) return { label: s.replace(/_/g, ' '), cls: 'badge-high' };
        return { label: s.replace(/_/g, ' '), cls: 'badge-warn' };
      }

      function humanizeReason(reas) {
        const r = String(reas || '');
        if (!r || r === '--') return '<span class="muted">Sin motivo específico</span>';
        if (r.includes('MARKET_REGIME_TOXIC_BLOCKED')) return '<b style="color:var(--r)">Mercado errático / Volatilidad tóxica:</b> rechazo de mecha o ruido intradía.';
        if (r.includes('SPREAD_EXCEEDED')) return '<b style="color:var(--r)">Spread ampliado:</b> costo de fricción excede el umbral seguro.';
        if (r.includes('HTF_TREND_MISALIGNMENT')) return '<b style="color:var(--r)">Tendencia HTF contraria:</b> no hay confluencia direccional en H1/H4.';
        if (r.includes('SPIKE_DANGER')) return '<b style="color:var(--r)">Riesgo de Spike inminente:</b> proximidad a tick de salto Crash/Boom.';
        if (r.includes('COOLDOWN_ACTIVE')) return '<b style="color:var(--y)">Enfriamiento de racha:</b> pausa temporal preventiva tras stop loss.';
        if (r.includes('EMA50_OVEREXTENDED')) return '<b style="color:var(--r)">Sobreextensión técnica:</b> precio alejado de la media institucional EMA50.';
        return esc(r);
      }

      function statsTable(el, obj, first) {
        const rows = Object.entries(obj || {});
        el.innerHTML = '<thead><tr><th>' + first + '</th><th class="n">Operaciones</th><th class="n">Cerradas</th><th class="n">Ganadas</th><th class="n">Acierto %</th><th class="n">R Acumulado</th></tr></thead><tbody>' +
          (rows.length ? rows.map(([k, s]) => {
            const wr = s.win_rate != null ? s.win_rate : (s.closed > 0 ? (s.wins / s.closed * 100) : null);
            const wrCls = wr >= 55 ? 'ok' : (wr < 48 ? 'bad' : 'mid');
            const rCls = s.r_total > 0 ? 'ok' : (s.r_total < 0 ? 'bad' : 'muted');
            return '<tr><td><b>' + esc(k) + '</b></td><td class="n">' + s.trades + '</td><td class="n">' + s.closed + '</td><td class="n">' + s.wins + '</td><td class="n ' + wrCls + '"><b>' + fmt(wr, 1) + '%</b></td><td class="n ' + rCls + '"><b>' + (s.r_total > 0 ? '+' : '') + fmt(s.r_total) + ' R</b></td></tr>';
          }).join('') : '<tr><td colspan="6" class="muted" style="padding:14px; text-align:center;">Aún no hay operaciones con decisión registrada en esta ventana.</td></tr>') + '</tbody>';
      }

      function compactAction(act) {
        const s = String(act || '');
        if (s.includes('APPROVED')) return { short: 'Aprobado', full: 'Aprobado para Entrada', cls: 'badge-ok' };
        if (s.includes('PASSED')) return { short: 'Pase CH', full: 'Pase Criterio Humano', cls: 'badge-ok' };
        if (s.includes('BYPASS')) return { short: 'Bypass', full: 'Bypass Habilitado', cls: 'badge-sub' };
        if (s.includes('SPREAD')) return { short: 'Spread', full: 'Veto: Spread Excesivo', cls: 'badge-high' };
        if (s.includes('SPIKE')) return { short: 'Anti-Spike', full: 'Escudo: Anti-Spike Crash/Boom', cls: 'badge-high' };
        if (s.includes('HTF')) return { short: 'Trend HTF', full: 'Veto: Desalineación HTF', cls: 'badge-high' };
        if (s.includes('REGIME') || s.includes('CHOPPINESS')) return { short: 'Régimen', full: 'Veto: Choppiness / Ruido', cls: 'badge-high' };
        if (s.includes('STREAK')) return { short: 'Cooldown', full: 'Cooldown por Racha de Pérdidas', cls: 'badge-warn' };
        if (s.includes('OVEREXTENSION')) return { short: 'Sobreext.', full: 'Veto: Sobreextensión EMA50', cls: 'badge-high' };
        if (s.includes('CLIMAX')) return { short: 'Clímax', full: 'Veto: Clímax / Agotamiento', cls: 'badge-high' };
        const clean = s.replace(/^(CH:|TRI:)?(VETO_|HUMAN_CRITERIA_)?/, '').replace(/_/g, ' ');
        return { short: clean.length > 11 ? clean.slice(0, 10) + '…' : clean, full: s.replace(/_/g, ' '), cls: 'badge-warn' };
      }

      function canonStrategy(s) {
        const str = String(s || '').toUpperCase().trim();
        if (!str || str === 'SIN_DATO' || str === '?' || str === 'UNKNOWN') return 'SIN_DATO';
        if (str.includes('ICT') || str.includes('SABRI') || str === 'SMC') return 'ICT';
        if (str.includes('ORB')) return 'ORB';
        if (str.includes('MALAYSIAN') || str.includes('MSNR') || str.includes('SNR')) return 'MALAYSIAN_SNR';
        if (str.includes('PULLBACK') || str.includes('TREND')) return 'TREND_PULLBACK';
        return str;
      }

      function consolidateStrategyEvents(byStrat) {
        const out = {};
        const entries = Object.entries(byStrat || {});
        for (const [raw, counts] of entries) {
          const c = canonStrategy(raw);
          if (raw === c) {
            out[c] = { ...(out[c] || {}), ...counts };
          }
        }
        for (const [raw, counts] of entries) {
          const c = canonStrategy(raw);
          if (!byStrat[c] && raw !== c) {
            if (!out[c]) out[c] = {};
            for (const [act, val] of Object.entries(counts)) {
              out[c][act] = (out[c][act] || 0) + val;
            }
          }
        }
        return out;
      }

      function consolidateStrategyStats(byStrat) {
        const out = {};
        const entries = Object.entries(byStrat || {});
        for (const [raw, st] of entries) {
          const c = canonStrategy(raw);
          if (raw === c) {
            out[c] = st;
          }
        }
        for (const [raw, st] of entries) {
          const c = canonStrategy(raw);
          if (!out[c]) {
            out[c] = st;
          }
        }
        return out;
      }

      function matrix(el, byKey, labelFirst) {
        const keys = Array.from(new Set(Object.values(byKey || {}).flatMap(o => Object.keys(o))));
        if (!keys.length) {
          el.innerHTML = '<tbody><tr><td class="muted" style="padding:14px; text-align:center;">Sin datos en la ventana seleccionada.</td></tr></tbody>';
          return;
        }
        el.innerHTML = '<thead><tr><th style="min-width:110px;">' + labelFirst + '</th>' + keys.map(k => {
          const c = compactAction(k);
          return '<th class="n" title="' + esc(c.full) + ' (' + esc(k) + ')"><span class="badge ' + c.cls + '" style="font-size:9.5px; padding:2px 5px;">' + esc(c.short) + '</span></th>';
        }).join('') + '</tr></thead><tbody>' +
          Object.entries(byKey || {}).map(([d, o]) => '<tr><td style="white-space:nowrap;"><b>' + esc(d) + '</b></td>' + keys.map(k => {
            const v = o[k];
            return '<td class="n">' + (v ? ('<b>' + v + '</b>') : '<span class="muted">–</span>') + '</td>';
          }).join('') + '</tr>').join('') + '</tbody>';
      }

      let cachedVetoes = [];
      let cachedRecent = [];
      let currentDecisionFilter = 'all'; // 'all', 'allow', 'veto', 'trades'
      let vetoesSortCol = 'time';
      let vetoesSortAsc = false;
      let recentSortCol = 'entry_time';
      let recentSortAsc = false;

      function setDecisionFilter(mode) {
        currentDecisionFilter = mode;
        ['All', 'Allow', 'Veto', 'Trades'].forEach(k => {
          const btn = document.getElementById('chipDec' + k);
          if (btn) btn.classList.toggle('active', k.toLowerCase() === mode.toLowerCase());
        });
        renderVetoesTable();
        renderRecentTable();
      }

      function sortVetoes(col) {
        if (vetoesSortCol === col) {
          vetoesSortAsc = !vetoesSortAsc;
        } else {
          vetoesSortCol = col;
          vetoesSortAsc = false;
        }
        renderVetoesTable();
      }

      function sortRecent(col) {
        if (recentSortCol === col) {
          recentSortAsc = !recentSortAsc;
        } else {
          recentSortCol = col;
          recentSortAsc = false;
        }
        renderRecentTable();
      }

      function renderVetoesTable() {
        const tbody = document.querySelector('#tblVetoes tbody');
        if (!tbody) return;
        const q = (document.getElementById('filterInput')?.value || '').toLowerCase().trim();

        let items = (cachedVetoes || []).slice();

        if (currentDecisionFilter === 'allow') {
          items = [];
        } else if (currentDecisionFilter === 'trades') {
          items = items.filter(v => v.execution_key || (v.reason && (v.reason.includes('TRADE') || v.reason.includes('POSITION'))));
        }

        if (q) {
          items = items.filter(v => {
            const h = humanizeAction(v.action);
            const str = [v.time, v.symbol, v.stage, h.label, v.action, canonStrategy(v.strategy), v.reason].join(' ').toLowerCase();
            return str.includes(q);
          });
        }

        items.sort((a, b) => {
          let vA = a[vetoesSortCol];
          let vB = b[vetoesSortCol];
          if (vA == null) return 1;
          if (vB == null) return -1;
          if (typeof vA === 'string') {
            return vetoesSortAsc ? vA.localeCompare(vB, 'es', { numeric: true }) : vB.localeCompare(vA, 'es', { numeric: true });
          }
          return vetoesSortAsc ? (vA - vB) : (vB - vA);
        });

        // Actualizar indicadores visuales en thead
        const headers = document.querySelectorAll('#tblVetoes thead th.sortable');
        headers.forEach(th => {
          const m = (th.getAttribute('onclick') || '').match(/sortVetoes\('([^']+)'\)/);
          if (m) {
            const col = m[1];
            const isCur = (col === vetoesSortCol);
            th.classList.toggle('sorted', isCur);
            let arrow = th.querySelector('.sort-arrow');
            if (!arrow) {
              arrow = document.createElement('span');
              arrow.className = 'sort-arrow';
              th.appendChild(arrow);
            }
            arrow.textContent = isCur ? (vetoesSortAsc ? '▲' : '▼') : '↕';
          }
        });

        tbody.innerHTML = items.length ? items.map(v => {
          const h = humanizeAction(v.action);
          return '<tr>' +
            '<td style="white-space:nowrap;font-family:Consolas,monospace;font-size:11.5px;">' + esc(v.time) + '</td>' +
            '<td><span class="badge badge-sub" style="font-family:Consolas,monospace;">' + esc(v.symbol) + '</span></td>' +
            '<td><span class="badge badge-warn" style="font-size:10.5px;">' + esc(v.stage) + '</span></td>' +
            '<td><span class="badge ' + h.cls + '">' + esc(h.label) + '</span></td>' +
            '<td><span class="badge badge-purple" style="font-size:10.5px;">' + esc(canonStrategy(v.strategy)) + '</span></td>' +
            '<td style="font-size:12px;">' + humanizeReason(v.reason) + '</td>' +
          '</tr>';
        }).join('') : '<tr><td colspan="6" class="muted" style="text-align:center;padding:18px;">Sin vetos que coincidan con el filtro activo.</td></tr>';
      }

      function renderRecentTable() {
        const tbody = document.querySelector('#tblRecent tbody');
        if (!tbody) return;
        const q = (document.getElementById('filterInput')?.value || '').toLowerCase().trim();

        let items = (cachedRecent || []).slice();

        if (currentDecisionFilter === 'veto') {
          items = [];
        }

        if (q) {
          items = items.filter(t => {
            const triAct = humanizeAction(t.tri_action);
            const str = [t.entry_time, t.symbol, t.direction, canonStrategy(t.strategy), t.hc_score, t.hc_grade, triAct.label, t.ai_probability, t.status, t.result].join(' ').toLowerCase();
            return str.includes(q);
          });
        }

        items.sort((a, b) => {
          let vA = a[recentSortCol];
          let vB = b[recentSortCol];
          if (vA == null) return 1;
          if (vB == null) return -1;
          if (typeof vA === 'string') {
            return recentSortAsc ? vA.localeCompare(vB, 'es', { numeric: true }) : vB.localeCompare(vA, 'es', { numeric: true });
          }
          return recentSortAsc ? (vA - vB) : (vB - vA);
        });

        // Actualizar indicadores visuales en thead
        const headers = document.querySelectorAll('#tblRecent thead th.sortable');
        headers.forEach(th => {
          const m = (th.getAttribute('onclick') || '').match(/sortRecent\('([^']+)'\)/);
          if (m) {
            const col = m[1];
            const isCur = (col === recentSortCol);
            th.classList.toggle('sorted', isCur);
            let arrow = th.querySelector('.sort-arrow');
            if (!arrow) {
              arrow = document.createElement('span');
              arrow.className = 'sort-arrow';
              th.appendChild(arrow);
            }
            arrow.textContent = isCur ? (recentSortAsc ? '▲' : '▼') : '↕';
          }
        });

        tbody.innerHTML = items.length ? items.map(t => {
          const dirCls = t.direction === 'BUY' ? 'ok' : 'bad';
          const rVal = typeof t.realized_rr === 'number' ? t.realized_rr : null;
          const rCls = rVal > 0 ? 'ok' : (rVal < 0 ? 'bad' : 'muted');
          const st = String(t.result && t.result !== 'OPEN' ? t.result : t.status);
          const stCls = st === 'WIN' ? 'badge-ok' : (st === 'LOSS' ? 'badge-high' : (st === 'OPEN' ? 'badge-sub' : 'badge-warn'));
          const triAct = humanizeAction(t.tri_action);
          const hc = t.hc_score != null ? t.hc_score : null;
          const hcCls = hc >= 80 ? 'ok' : (hc >= 70 ? 'mid' : 'bad');

          return '<tr>' +
            '<td style="white-space:nowrap;font-family:Consolas,monospace;font-size:11.5px;">' + esc(t.entry_time) + '</td>' +
            '<td><span class="badge badge-sub" style="font-family:Consolas,monospace;">' + esc(t.symbol) + '</span></td>' +
            '<td><span class="badge ' + (t.direction === 'BUY' ? 'badge-ok' : 'badge-high') + '">' + esc(t.direction) + '</span></td>' +
            '<td><span class="badge badge-purple" style="font-size:10.5px;">' + esc(canonStrategy(t.strategy)) + '</span></td>' +
            '<td class="n"><b class="' + hcCls + '">' + fmt(t.hc_score, 1) + '</b></td>' +
            '<td><span class="badge badge-warn" style="font-size:10px;">' + esc(t.hc_grade || '–') + '</span></td>' +
            '<td><span class="badge ' + triAct.cls + '" style="font-size:10px;">' + esc(triAct.label) + '</span></td>' +
            '<td class="n">' + fmt(t.ai_probability) + '</td>' +
            '<td class="n">' + fmt(t.adx_used, 1) + '</td>' +
            '<td><span class="badge ' + stCls + '">' + esc(st) + '</span></td>' +
            '<td class="n ' + rCls + '"><b>' + (rVal > 0 ? '+' : '') + fmt(rVal) + (rVal != null ? ' R' : '') + '</b></td>' +
          '</tr>';
        }).join('') : '<tr><td colspan="11" class="muted" style="text-align:center;padding:18px;">Sin operaciones auditadas que coincidan con el filtro activo.</td></tr>';
      }

      function filterTables(q) {
        q = (q || '').toLowerCase().trim();
        const btnClear = document.getElementById('btnClearFilter');
        if (btnClear) btnClear.style.display = q ? 'block' : 'none';

        const tables = ['#tblActions', '#tblSyms'];
        tables.forEach(sel => {
          const rows = document.querySelectorAll(sel + ' tbody tr');
          rows.forEach(r => {
            if (!q) {
              r.style.display = '';
            } else {
              const text = r.textContent.toLowerCase();
              r.style.display = text.includes(q) ? '' : 'none';
            }
          });
        });
        renderVetoesTable();
        renderRecentTable();
      }

      async function load() {
        const days = document.getElementById('days').value;
        let data;
        try {
          const r = await fetch('/api/entry-decisions?days=' + encodeURIComponent(days), { cache: 'no-store' });
          data = await r.json();
        } catch (e) {
          document.getElementById('stamp').textContent = 'Error al conectar con la API: ' + e;
          if (window.pageLoading) pageLoading.fail('Error al conectar con la API: ' + e);
          return;
        }
        if (data.error) {
          document.getElementById('stamp').textContent = 'Error en reporte: ' + data.error;
          if (window.pageLoading) pageLoading.fail('Error en reporte: ' + data.error);
          return;
        }

        try {
          const ev = data.events || {};
          const tr = data.trades || {};
          const acts = ev.by_action || {};

          const vetoes = Object.entries(acts).filter(([k]) => k.includes('VETO') || (k.startsWith('CH:') && !k.includes('PASSED') && !k.endsWith('_OBSERVED'))).reduce((a, [, v]) => a + v, 0);
          const approved = Object.entries(acts).filter(([k]) => k.includes('APPROVED') || k.includes('PASSED')).reduce((a, [, v]) => a + v, 0);
          const total = ev.total_events || (approved + vetoes) || 1;
          const appRate = ((approved / total) * 100).toFixed(1);
          const vetoRate = ((vetoes / total) * 100).toFixed(1);
          const keyPct = total > 0 ? ((ev.events_with_execution_key / total) * 100).toFixed(1) : 0;
          const ov = tr.overall || {};
          const rTot = ov.r_total != null ? ov.r_total : 0.0;

          // KPI Highlights
          document.getElementById('cards').innerHTML = `
            <div class="kpi-card" style="--accent: var(--b);">
              <div class="kpi-lab"><span>📊 Evaluaciones</span> <span class="badge badge-warn">${days}D</span></div>
              <div class="kpi-val">${ev.total_events || 0}</div>
              <div class="kpi-sub">Decisiones evaluadas por los comités</div>
            </div>
            <div class="kpi-card" style="--accent: var(--g);">
              <div class="kpi-lab"><span>⚡ Aprobadas</span> <span class="badge badge-ok">${appRate}%</span></div>
              <div class="kpi-val" style="color:var(--g);">${approved}</div>
              <div class="kpi-sub">Luz verde en Criterio Humano + Tripartita</div>
            </div>
            <div class="kpi-card" style="--accent: var(--r);">
              <div class="kpi-lab"><span>🛡 Vetos de Riesgo</span> <span class="badge badge-high">${vetoRate}%</span></div>
              <div class="kpi-val" style="color:var(--r);">${vetoes}</div>
              <div class="kpi-sub">Pérdidas prevenidas por filtros estrictos</div>
            </div>
            <div class="kpi-card" style="--accent: var(--cyan);">
              <div class="kpi-lab"><span>🔬 Trazabilidad</span> <span class="badge badge-sub">${keyPct}%</span></div>
              <div class="kpi-val">${ev.events_with_execution_key || 0}</div>
              <div class="kpi-sub">Eventos con <code>execution_key</code> única</div>
            </div>
            <div class="kpi-card" style="--accent: var(--purple);">
              <div class="kpi-lab"><span>🎯 Operaciones</span> <span class="badge badge-purple">${tr.coverage_pct ?? 0}%</span></div>
              <div class="kpi-val">${tr.trades_total || 0}</div>
              <div class="kpi-sub">${tr.trades_with_decision || 0} trades enlazados a su decisión</div>
            </div>
            <div class="kpi-card" style="--accent: ${rTot >= 0 ? 'var(--g)' : 'var(--r)'};">
              <div class="kpi-lab"><span>💰 R Auditado</span> <span class="badge ${rTot >= 0 ? 'badge-ok' : 'badge-high'}">${ov.win_rate != null ? ov.win_rate + '%' : '–'}</span></div>
              <div class="kpi-val" style="color:${rTot >= 0 ? 'var(--g)' : 'var(--r)'};">${rTot >= 0 ? '+' : ''}${fmt(rTot)} R</div>
              <div class="kpi-sub">${ov.wins || 0} ganadas de ${ov.closed || 0} trades cerrados</div>
            </div>
          `;

          // Update pills
          document.getElementById('pillEvents').textContent = `${ev.total_events || 0} ev`;
          document.getElementById('pillVetoes').textContent = `${vetoes} vetos`;
          document.getElementById('pillTrades').textContent = `${tr.trades_with_decision || 0} ops`;

          // Cobertura parcial warning
          const note = document.getElementById('coverageNote');
          if ((tr.trades_total || 0) > (tr.trades_with_decision || 0)) {
            note.style.display = 'block';
            note.innerHTML = '<b>ℹ Cobertura parcial en ventana histórica:</b> Las operaciones previas al inicio de la bitácora unificada no tienen <code>execution_key</code> asignada (' + (tr.trades_with_decision || 0) + ' de ' + (tr.trades_total || 0) + '). Todas las operaciones nuevas quedan 100% enlazadas.';
          } else {
            note.style.display = 'none';
          }

          // Funnel Table
          const actEntries = Object.entries(acts);
          const maxAct = actEntries.length ? Math.max(...actEntries.map(([, v]) => v)) : 1;
          document.querySelector('#tblActions tbody').innerHTML = actEntries.length ? actEntries.map(([k, v]) => {
            const h = humanizeAction(k);
            const pct = ((v / total) * 100).toFixed(1);
            const barPct = ((v / maxAct) * 100).toFixed(1);
            const barCol = h.cls.includes('ok') ? 'var(--g)' : (h.cls.includes('high') ? 'var(--r)' : 'var(--y)');
            return '<tr>' +
              '<td><div style="display:flex;align-items:center;gap:8px;"><span class="badge ' + h.cls + '">' + esc(h.label) + '</span><span class="muted" style="font-size:11.5px;font-family:Consolas,monospace;">' + esc(k) + '</span></div></td>' +
              '<td><div class="bar-track"><div class="bar-fill" style="width:' + barPct + '%;background:' + barCol + ';"></div></div></td>' +
              '<td class="n"><b>' + v + '</b></td>' +
              '<td class="n"><span class="badge ' + h.cls + '" style="font-size:10.5px;">' + pct + '%</span></td>' +
            '</tr>';
          }).join('') : '<tr><td colspan="4" class="muted" style="text-align:center;padding:16px;">Sin eventos evaluados en esta ventana.</td></tr>';

          // Matrices
          matrix(document.getElementById('tblDays'), ev.by_day, 'Fecha / Día');
          const stratEvents = consolidateStrategyEvents(ev.by_strategy);
          matrix(document.getElementById('tblStrat'), stratEvents, 'Estrategia');

          // Top Vetoed Symbols
          const topSyms = ev.top_veto_symbols || [];
          const maxSymVeto = topSyms.length ? Math.max(...topSyms.map(([, n]) => n)) : 1;
          document.querySelector('#tblSyms tbody').innerHTML = topSyms.length ? topSyms.map(([s, n]) => {
            const barPct = ((n / maxSymVeto) * 100).toFixed(1);
            return '<tr>' +
              '<td><span class="badge badge-sub" style="font-size:12px;font-family:Consolas,monospace;">' + esc(s) + '</span></td>' +
              '<td><div class="bar-track"><div class="bar-fill" style="width:' + barPct + '%;background:var(--r);"></div></div></td>' +
              '<td class="n"><b style="color:var(--r);">' + n + '</b></td>' +
            '</tr>';
          }).join('') : '<tr><td colspan="3" class="muted" style="text-align:center;padding:16px;">No se registraron vetos en este periodo.</td></tr>';

          // Recent Vetoes
          cachedVetoes = ev.recent_vetoes || [];
          renderVetoesTable();

          // Performance Tables
          statsTable(document.getElementById('tblHC'), tr.by_human_score, 'Rango Puntaje Humano');
          statsTable(document.getElementById('tblAI'), tr.by_ai_probability, 'Probabilidad IA P(IA)');
          const stratStats = consolidateStrategyStats(tr.by_strategy);
          statsTable(document.getElementById('tblTStrat'), stratStats, 'Estrategia');

          // Recent Operations
          cachedRecent = tr.recent || [];
          renderRecentTable();

          // Stamp
          document.getElementById('stamp').innerHTML = `
            <span>⚡ Generado a las <b>${esc(data.generated_at || '')} UTC</b> · Ventana activa: <b>${data.days} día(s)</b></span>
            <span>Base de datos: <b>${esc(data.source || 'LIVE / DEMO')}</b> · Suite Cuantitativa BlackDaemonFX</span>
          `;
          if (window.pageLoading) pageLoading.done();
        } catch (renderErr) {
          console.error('Error renderizando decisiones:', renderErr);
          document.getElementById('stamp').textContent = 'Error al renderizar decisiones: ' + renderErr;
          if (window.pageLoading) pageLoading.fail('Error al renderizar decisiones');
        }
      }

      document.getElementById('reload').addEventListener('click', load);
      document.getElementById('days').addEventListener('change', load);
      load();
    </script>
  </body>
</html>
'''

DECISIONS_HTML = with_page_loading(_DECISIONS_BASE)
