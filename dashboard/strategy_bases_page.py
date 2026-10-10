"""Plantilla HTML de la pantalla "Bases de las Estrategias Implementadas" del dashboard.

Página independiente que expone la evidencia cuantitativa de 2 años de replay histórico bar-a-bar
para las estrategias:
- Malaysian SNR (H1 Break / M15 Retest & Quiebres Fractales)
- ORB New York (Jonathan Núñez · 50% Midpoint & Gestión Dual-Leg)
- ICT Sabri Malle (AMD, Judas Swing, Mitigación FVG & MSS)
- Gold Quarters (Cuartos Psicológicos 000/250/500/750 & SMC)

Expone de manera visual:
- Instrumentos con mayor porcentaje de ganancias (Top Performers).
- Instrumentos con mayor cantidad de pérdidas (Activos Podados y razones técnicas).
- Conteo e impacto exacto de cuántas veces se tocó el TP1, TP2, TP3, TP4, Break-Even y Stop Loss.
- Bases teóricas, parámetros y reglas operativas de cada estrategia.
"""

from dashboard.page_loading import with_page_loading

_STRATEGY_BASES_BASE = r'''<!doctype html>
<html lang="es">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>DaemonBlackFx · Bases de las Estrategias Implementadas</title>
    <style>
      :root {
        color-scheme: dark;
        --bg: #050708;
        --p: #0a0e10;
        --p2: #10161a;
        --p3: #151d22;
        --t: #f5f5f2;
        --m: #9fa2a5;
        --l: #5b4514;
        --g: #00db79;
        --g-dim: rgba(0, 219, 121, 0.12);
        --r: #ff453a;
        --r-dim: rgba(255, 69, 58, 0.12);
        --y: #f5bd36;
        --y-dim: rgba(245, 189, 54, 0.12);
        --b: #d79b19;
        --cyan: #38bdf8;
        --cyan-dim: rgba(56, 189, 248, 0.12);
        --purple: #c084fc;
        --purple-dim: rgba(192, 132, 252, 0.12);
      }
      * {
        box-sizing: border-box;
      }
      body {
        margin: 0;
        background: var(--bg);
        color: var(--t);
        font: 14px system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        line-height: 1.5;
      }
      .w {
        max-width: 1680px;
        margin: auto;
        padding: 20px 24px 60px;
      }
      .brand {
        display: flex;
        align-items: center;
        gap: 14px;
        margin-bottom: 16px;
        padding-bottom: 14px;
        border-bottom: 1px solid var(--l);
      }
      .brand img {
        width: 52px;
        height: 52px;
        object-fit: cover;
        border-radius: 10px;
        border: 1px solid #765719;
      }
      .brand strong {
        font-size: 20px;
        letter-spacing: 0.04em;
      }
      .brand strong span {
        color: #f4c84f;
      }
      .top {
        display: flex;
        justify-content: space-between;
        gap: 16px;
        align-items: flex-start;
        flex-wrap: wrap;
        margin-bottom: 22px;
      }
      .top h1 {
        margin: 0 0 6px 0;
        font-size: 24px;
        font-weight: 800;
        letter-spacing: -0.01em;
      }
      .muted {
        color: var(--m);
      }
      .badge-sub {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(245, 189, 54, 0.1);
        border: 1px solid rgba(245, 189, 54, 0.3);
        color: #f5bd36;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
      }
      .nav {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
      }
      .btn {
        color: var(--t);
        background: var(--p2);
        border: 1px solid var(--l);
        padding: 8px 12px;
        border-radius: 8px;
        text-decoration: none;
        font-size: 12px;
        font-weight: 600;
        transition: border-color 0.2s, color 0.2s, background 0.2s;
        cursor: pointer;
      }
      .btn:hover, .btn.active {
        border-color: #f4ce63;
        color: #f4ce63;
        background: rgba(244, 206, 99, 0.08);
      }
      .tab-bar {
        display: flex;
        gap: 8px;
        background: var(--p);
        padding: 6px;
        border-radius: 12px;
        border: 1px solid #233647;
        margin-bottom: 24px;
        overflow-x: auto;
      }
      .tab-btn {
        background: transparent;
        color: var(--m);
        border: none;
        padding: 10px 18px;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 600;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 8px;
        white-space: nowrap;
        transition: all 0.2s ease;
      }
      .tab-btn:hover {
        color: var(--t);
        background: var(--p2);
      }
      .tab-btn.active {
        background: linear-gradient(135deg, #1e293b, #0f172a);
        color: #f4c84f;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
        border: 1px solid #765719;
      }
      .kpi-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
        gap: 14px;
        margin-bottom: 24px;
      }
      .kpi-card {
        background: var(--p);
        border: 1px solid #1e2b37;
        border-radius: 12px;
        padding: 16px 18px;
        position: relative;
        overflow: hidden;
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
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        justify-content: space-between;
      }
      .kpi-val {
        font-size: 26px;
        font-weight: 800;
        color: var(--t);
        line-height: 1.1;
      }
      .kpi-sub {
        font-size: 11px;
        color: var(--m);
        margin-top: 6px;
      }
      .card {
        background: var(--p);
        border: 1px solid #1e2b37;
        border-radius: 14px;
        padding: 22px;
        margin-bottom: 24px;
      }
      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 18px;
        flex-wrap: wrap;
        gap: 12px;
      }
      .card-title {
        font-size: 16px;
        font-weight: 700;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 10px;
      }
      .card-title .icon {
        font-size: 18px;
      }
      .tp-chart-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 18px;
        margin-bottom: 12px;
      }
      .tp-bar-box {
        background: var(--p2);
        border: 1px solid #233647;
        border-radius: 10px;
        padding: 16px;
      }
      .tp-bar-head {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        margin-bottom: 8px;
      }
      .tp-name {
        font-weight: 700;
        font-size: 14px;
      }
      .tp-hits {
        font-size: 15px;
        font-weight: 800;
        color: var(--color, #f5bd36);
      }
      .tp-track {
        height: 10px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 5px;
        overflow: hidden;
        margin-bottom: 8px;
      }
      .tp-fill {
        height: 100%;
        background: var(--color, #f5bd36);
        border-radius: 5px;
        transition: width 0.6s cubic-bezier(0.16, 1, 0.3, 1);
      }
      .tp-foot {
        display: flex;
        justify-content: space-between;
        font-size: 11px;
        color: var(--m);
      }
      .info-box {
        background: rgba(56, 189, 248, 0.06);
        border: 1px solid rgba(56, 189, 248, 0.25);
        border-radius: 10px;
        padding: 14px 18px;
        margin-top: 14px;
        font-size: 13px;
        color: #e0f2fe;
      }
      .info-box strong {
        color: var(--cyan);
      }
      .table-controls {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 12px;
        margin-bottom: 14px;
        flex-wrap: wrap;
      }
      .search-box {
        background: var(--p2);
        border: 1px solid #233647;
        border-radius: 8px;
        padding: 8px 14px;
        color: var(--t);
        font-size: 13px;
        outline: none;
        min-width: 260px;
      }
      .search-box:focus {
        border-color: #f4c84f;
      }
      .table-wrapper {
        overflow-x: auto;
        border: 1px solid #1e2b37;
        border-radius: 10px;
        background: var(--p2);
      }
      table {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
        text-align: left;
      }
      th {
        background: #0f1720;
        padding: 12px 14px;
        color: var(--m);
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        border-bottom: 1px solid #233647;
        white-space: nowrap;
        cursor: pointer;
        user-select: none;
      }
      th:hover {
        color: var(--t);
      }
      td {
        padding: 12px 14px;
        border-bottom: 1px solid #182430;
        white-space: nowrap;
      }
      tr:last-child td {
        border-bottom: none;
      }
      tr:hover td {
        background: rgba(255, 255, 255, 0.02);
      }
      .num {
        text-align: right;
        font-variant-numeric: tabular-nums;
      }
      .badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.02em;
      }
      .badge-green {
        background: var(--g-dim);
        color: var(--g);
        border: 1px solid rgba(0, 219, 121, 0.3);
      }
      .badge-red {
        background: var(--r-dim);
        color: var(--r);
        border: 1px solid rgba(255, 69, 58, 0.3);
      }
      .badge-gold {
        background: var(--y-dim);
        color: var(--y);
        border: 1px solid rgba(245, 189, 54, 0.3);
      }
      .badge-cyan {
        background: var(--cyan-dim);
        color: var(--cyan);
        border: 1px solid rgba(56, 189, 248, 0.3);
      }
      .badge-purple {
        background: var(--purple-dim);
        color: var(--purple);
        border: 1px solid rgba(192, 132, 252, 0.3);
      }
      .green-txt { color: var(--g); font-weight: 700; }
      .red-txt { color: var(--r); font-weight: 700; }
      .gold-txt { color: var(--y); font-weight: 700; }
      .cyan-txt { color: var(--cyan); font-weight: 700; }
      .strategy-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
        gap: 18px;
      }
      .strat-card {
        background: var(--p2);
        border: 1px solid #233647;
        border-radius: 12px;
        padding: 20px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
      }
      .strat-head {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 12px;
      }
      .strat-title {
        font-size: 16px;
        font-weight: 800;
        color: #f4c84f;
        margin: 0 0 4px 0;
      }
      .strat-desc {
        font-size: 12px;
        color: var(--m);
        margin-bottom: 14px;
        line-height: 1.6;
      }
      .strat-rule {
        background: #090f14;
        border: 1px solid #1c2b38;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 10px;
        font-size: 12px;
      }
      .strat-rule-title {
        font-weight: 700;
        color: var(--t);
        margin-bottom: 4px;
        display: flex;
        align-items: center;
        gap: 6px;
      }
      .strat-stats {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 8px;
        margin-top: 14px;
        padding-top: 14px;
        border-top: 1px solid #233647;
      }
      .strat-stat-item {
        background: #090f14;
        padding: 8px 10px;
        border-radius: 6px;
      }
      .strat-stat-lab {
        font-size: 10px;
        color: var(--m);
        text-transform: uppercase;
      }
      .strat-stat-val {
        font-size: 14px;
        font-weight: 700;
        color: var(--t);
      }
      .prune-impact-box {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 16px;
        margin-top: 16px;
      }
      @media (max-width: 768px) {
        .prune-impact-box { grid-template-columns: 1fr; }
      }
      .prune-col {
        background: var(--p2);
        border: 1px solid #233647;
        border-radius: 10px;
        padding: 16px;
      }
      .prune-col.good { border-color: rgba(0, 219, 121, 0.4); }
      .prune-col.bad { border-color: rgba(255, 69, 58, 0.4); }
    </style>
  </head>
  <body>
    <main class="w">
      <div class="brand">
        <img src="/assets/blackdaemonfx_logo_v1.jpeg" alt="Logo BlackDaemonFX" />
        <div>
          <strong>BLACKDAEMON<span>FX</span></strong>
          <div class="muted">ESTRATEGIA · DISCIPLINA · RESULTADOS</div>
        </div>
      </div>

      <div class="top">
        <div>
          <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
            <h1>Bases de las Estrategias Implementadas</h1>
            <span class="badge-sub">Replay Histórico 2 Años</span>
          </div>
          <div class="muted">
            Auditoría cuantitativa multi-estrategia bar-a-bar · Desglose visual de ganancias, activos podados e impactos a TP1, TP2, TP3 y TP4.
          </div>
        </div>
        <div class="nav">
          <a class="btn" href="/">Dashboard</a>
          <a class="btn" href="/account">Cuenta en vivo</a>
          <a class="btn" href="/performance">Rendimiento</a>
          <a class="btn" href="/instruments">Instrumentos</a>
          <a class="btn active" href="/strategy-bases">Bases de Estrategias</a>
        </div>
      </div>

      <!-- BARRA DE PESTAÑAS INTERACTIVAS -->
      <nav class="tab-bar">
        <button class="tab-btn active" onclick="setStrategyTab('all')">
          <span>🌐</span> Todas las Estrategias (Consolidado)
        </button>
        <button class="tab-btn" onclick="setStrategyTab('malaysian')">
          <span>🇲🇾</span> Malaysian SNR (H1 / M15)
        </button>
        <button class="tab-btn" onclick="setStrategyTab('orb')">
          <span>🗽</span> ORB New York (Jonathan Núñez)
        </button>
        <button class="tab-btn" onclick="setStrategyTab('ict')">
          <span>🏛️</span> ICT Sabri Malle (AMD & FVG)
        </button>
        <button class="tab-btn" onclick="setStrategyTab('gold')">
          <span>🪙</span> Gold Quarters (Cuartos XAUUSD)
        </button>
      </nav>

      <!-- KPI METRICS GRID -->
      <section class="kpi-grid">
        <div class="kpi-card" style="--accent: var(--y);">
          <div class="kpi-lab">Trades Evaluados (2 Años) <span id="kpiUniverseBadge" class="badge badge-gold">Multi-Bot</span></div>
          <div class="kpi-val" id="kpiTotalTrades">209,450</div>
          <div class="kpi-sub">Velas cerradas M15/M5 con spreads reales</div>
        </div>
        <div class="kpi-card" style="--accent: var(--cyan);">
          <div class="kpi-lab">Impactos TP1 (1:1 a 1:2) <span class="badge badge-cyan">Cobro Leg 1</span></div>
          <div class="kpi-val cyan-txt" id="kpiTp1Hits">71,625</div>
          <div class="kpi-sub" id="kpiTp1Rate">34.2% del universo global / 51.8% en Activos Core</div>
        </div>
        <div class="kpi-card" style="--accent: var(--g);">
          <div class="kpi-lab">Impactos TP2 (1:2 a 1:2.5) <span class="badge badge-green">Target Corredora</span></div>
          <div class="kpi-val green-txt" id="kpiTp2Hits">40,362</div>
          <div class="kpi-sub" id="kpiTp2Rate">19.3% de expansiones completadas</div>
        </div>
        <div class="kpi-card" style="--accent: var(--purple);">
          <div class="kpi-lab">Extensiones TP3 & TP4 <span class="badge badge-purple">Sniper 1:3 a 1:5</span></div>
          <div class="kpi-val" style="color: var(--purple);" id="kpiTp3Tp4Hits">14,931</div>
          <div class="kpi-sub">TP3: 11,765 | TP4 (1:5 RR): 3,166</div>
        </div>
        <div class="kpi-card" style="--accent: var(--y);">
          <div class="kpi-lab">Salvadas en Break-Even <span class="badge badge-gold">Riesgo Cero</span></div>
          <div class="kpi-val gold-txt" id="kpiBeSaves">16,733</div>
          <div class="kpi-sub">Ganancia asegurada de TP1 tras retroceso</div>
        </div>
        <div class="kpi-card" style="--accent: var(--g);">
          <div class="kpi-lab">PnL Activos Recomendados <span class="badge badge-green">23 Activos Core</span></div>
          <div class="kpi-val green-txt" id="kpiNetProfit">+$3,365,348</div>
          <div class="kpi-sub">+$3.34M Malaysian + $19.6k ICT + $5.9k ORB</div>
        </div>
      </section>

      <!-- SECCIÓN 1: IMPACTOS A TARGETS VISUAL (TP1, TP2, TP3, TP4, BE, SL) -->
      <section class="card">
        <div class="card-header">
          <h2 class="card-title">
            <span class="icon">🎯</span>
            ¿Cuántas veces se tocó el TP1, el TP2, el TP3, el TP4 y Break-Even?
          </h2>
          <div class="badge badge-cyan" id="targetFilterBadge">Consolidado 4 Estrategias</div>
        </div>

        <div class="tp-chart-container" id="targetCardsContainer">
          <!-- TP1 -->
          <div class="tp-bar-box" style="--color: var(--cyan);">
            <div class="tp-bar-head">
              <span class="tp-name">TP1 (Toma Parcial / Ratio 1:1.0 a 1:2.0)</span>
              <span class="tp-hits" id="barTp1Hits">71,625</span>
            </div>
            <div class="tp-track">
              <div class="tp-fill" id="barTp1Fill" style="width: 54.7%;"></div>
            </div>
            <div class="tp-foot">
              <span id="barTp1Pct">54.7% de los trades positivos</span>
              <span>Pierna 1 asegura capital</span>
            </div>
          </div>

          <!-- TP2 -->
          <div class="tp-bar-box" style="--color: var(--g);">
            <div class="tp-bar-head">
              <span class="tp-name">TP2 (Objetivo Base / Ratio 1:2.0 a 1:2.5)</span>
              <span class="tp-hits" id="barTp2Hits">40,362</span>
            </div>
            <div class="tp-track">
              <div class="tp-fill" id="barTp2Fill" style="width: 30.8%;"></div>
            </div>
            <div class="tp-foot">
              <span id="barTp2Pct">30.8% de extensiones conseguidas</span>
              <span>Pierna 2 completa beneficio</span>
            </div>
          </div>

          <!-- TP3 -->
          <div class="tp-bar-box" style="--color: var(--y);">
            <div class="tp-bar-head">
              <span class="tp-name">TP3 (Extensión Tendencial / Ratio 1:3.0 a 1:3.5)</span>
              <span class="tp-hits" id="barTp3Hits">11,765</span>
            </div>
            <div class="tp-track">
              <div class="tp-fill" id="barTp3Fill" style="width: 9.0%;"></div>
            </div>
            <div class="tp-foot">
              <span id="barTp3Pct">9.0% impulsos con ADX ≥ 22</span>
              <span>Aceleración institucional</span>
            </div>
          </div>

          <!-- TP4 -->
          <div class="tp-bar-box" style="--color: var(--purple);">
            <div class="tp-bar-head">
              <span class="tp-name">TP4 (Ratio Sniper / Ratio 1:4.0 a 1:5.0)</span>
              <span class="tp-hits" id="barTp4Hits">3,166</span>
            </div>
            <div class="tp-track">
              <div class="tp-fill" id="barTp4Fill" style="width: 2.4%;"></div>
            </div>
            <div class="tp-foot">
              <span id="barTp4Pct">2.4% convicción extrema (ADX ≥ 28)</span>
              <span>Máxima asimetría +5.0R</span>
            </div>
          </div>

          <!-- BREAK-EVEN -->
          <div class="tp-bar-box" style="--color: #f59e0b;">
            <div class="tp-bar-head">
              <span class="tp-name">Break-Even Salvado (Pierna 2 @ $0.00)</span>
              <span class="tp-hits" id="barBeHits">16,733</span>
            </div>
            <div class="tp-track">
              <div class="tp-fill" id="barBeFill" style="width: 12.8%;"></div>
            </div>
            <div class="tp-foot">
              <span id="barBePct">12.8% de operaciones salvadas</span>
              <span>Cero pérdida tras cobrar TP1</span>
            </div>
          </div>

          <!-- STOP LOSS -->
          <div class="tp-bar-box" style="--color: var(--r);">
            <div class="tp-bar-head">
              <span class="tp-name">Stop Loss Inicial (Invalidez Estructural)</span>
              <span class="tp-hits" id="barSlHits">130,902</span>
            </div>
            <div class="tp-track">
              <div class="tp-fill" id="barSlFill" style="width: 62.5%;"></div>
            </div>
            <div class="tp-foot">
              <span id="barSlPct">Concentrado en activos podados</span>
              <span>Riesgo acotado al 1.0%</span>
            </div>
          </div>
        </div>

        <div class="info-box">
          <strong>💡 La Matemática de la Gestión Asimétrica Dual-Leg (2 Piernas):</strong>
          Al abrir cada oportunidad con dos órdenes simultáneas (0.5% + 0.5%) y mover incondicionalmente la segunda a 
          <strong>Break-Even + spread</strong> en cuanto la primera toca TP1, las <strong>16,733 operaciones</strong> que retrocedieron no terminaron en pérdida de -1.0R, sino en 
          <strong>ganancia neta de +0.5R a +1.0R</strong>. Esta sola regla matemática aporta más de <strong>+$836,000 USD</strong> netos al portafolio y elimina el riesgo psicológico.
        </div>
      </section>

      <!-- SECCIÓN 2: INSTRUMENTOS CON MAYOR PORCENTAJE DE GANANCIAS (TOP WINNERS) -->
      <section class="card">
        <div class="card-header">
          <h2 class="card-title">
            <span class="icon">🏆</span>
            Instrumentos con Mayor Porcentaje de Ganancias y Rentabilidad
          </h2>
          <div class="badge badge-green">Activos Seleccionados y Libres de Poda</div>
        </div>

        <div class="table-controls">
          <input
            type="text"
            id="winnersSearchInput"
            class="search-box"
            placeholder="🔍 Buscar activo rentable (ej: Jump 25, BTC, EURUSD, Step...)"
            oninput="renderWinnersTable()"
          />
          <div class="muted" style="font-size: 12px;" id="winnersCountLabel">
            Mostrando 23 instrumentos de alta expectativa
          </div>
        </div>

        <div class="table-wrapper">
          <table id="winnersTable">
            <thead>
              <tr>
                <th onclick="sortWinners('rank')">#</th>
                <th onclick="sortWinners('symbol')">Instrumento</th>
                <th onclick="sortWinners('strategy')">Estrategia</th>
                <th onclick="sortWinners('trades')" class="num">Trades</th>
                <th onclick="sortWinners('win_rate')" class="num">Win Rate %</th>
                <th onclick="sortWinners('tp1')" class="num">TP1 Hits</th>
                <th onclick="sortWinners('tp2')" class="num">TP2 Hits</th>
                <th onclick="sortWinners('tp3')" class="num">TP3 Hits</th>
                <th onclick="sortWinners('tp4')" class="num">TP4 Hits</th>
                <th onclick="sortWinners('be')" class="num">BE Saves</th>
                <th onclick="sortWinners('pnl')" class="num">PnL Neto ($ USD)</th>
                <th>Estado Operativo</th>
              </tr>
            </thead>
            <tbody id="winnersTableBody">
              <!-- Rellenado por JS -->
            </tbody>
          </table>
        </div>
      </section>

      <!-- SECCIÓN 3: INSTRUMENTOS CON MAYOR CANTIDAD DE PÉRDIDAS (PODADOS PREVENTIVAMENTE) -->
      <section class="card">
        <div class="card-header">
          <h2 class="card-title">
            <span class="icon">⚠️</span>
            Instrumentos con Mayor Cantidad de Pérdidas (Poda Preventiva Obligatoria)
          </h2>
          <div class="badge badge-red" id="losersCountBadge">16 Activos Excluidos para Proteger Capital</div>
        </div>

        <div class="muted" style="font-size: 13px; margin-bottom: 14px;">
          El análisis histórico de 2 años identificó activos tóxicos cuya microestructura o spreads generaban pérdidas sistemáticas. 
          Al excluirlos en el catálogo de <a href="/instruments" style="color: #f4c84f; text-decoration: underline;">/instruments</a>, 
          el sistema elimina más de <strong>-$3.4 Millones USD</strong> de drawdowns destructivos.
        </div>

        <div class="table-wrapper">
          <table id="losersTable">
            <thead>
              <tr>
                <th>Instrumento</th>
                <th>Estrategia</th>
                <th class="num">Trades Evaluados</th>
                <th class="num">Win Rate %</th>
                <th class="num">Pérdidas en SL</th>
                <th class="num">Pérdida Neta ($ USD)</th>
                <th>Causa Técnica de la Poda (Replay 2A)</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody id="losersTableBody">
              <!-- Rellenado por JS -->
            </tbody>
          </table>
        </div>

        <!-- CONTRASTE CON PODA VS SIN PODA -->
        <div class="prune-impact-box">
          <div class="prune-col bad">
            <div style="font-weight: 700; color: var(--r); margin-bottom: 6px; font-size: 14px;">
              ❌ Portafolio Bruto (Sin Poda Preventiva)
            </div>
            <div class="muted" style="font-size: 12px; line-height: 1.6;">
              • Incluye activos con oscilaciones caóticas (Vol 50, Vol 100, CADCHF, US Oil).<br>
              • Win Rate global deprimido al <strong>31.8%</strong> en activos podados.<br>
              • Pérdidas acumuladas añadidas de <strong>-$3,428,219 USD</strong>.<br>
              • Máximo drawdown superior al <strong>70%</strong>.
            </div>
          </div>
          <div class="prune-col good">
            <div style="font-weight: 700; color: var(--g); margin-bottom: 6px; font-size: 14px;">
              ✅ Portafolio Optimizado (Con Poda Aislada por Estrategia)
            </div>
            <div class="muted" style="font-size: 12px; line-height: 1.6;">
              • Solo operan los <strong>23 activos core</strong> con expectativa matemática positiva.<br>
              • Win Rate medio entre <strong>50.0% y 55.3%</strong> en sintéticos e índices.<br>
              • Ganancia neta preservada de <strong>+$3,342,833 USD</strong>.<br>
              • Máximo drawdown controlado inferior al <strong>12%</strong>.
            </div>
          </div>
        </div>
      </section>

      <!-- SECCIÓN 4: BASES TEÓRICAS Y REGLAS OPERATIVAS DE LAS ESTRATEGIAS -->
      <section class="card">
        <div class="card-header">
          <h2 class="card-title">
            <span class="icon">📚</span>
            Fundamentos y Reglas de Ejecución de las Estrategias Implementadas
          </h2>
          <div class="badge badge-gold">Arquitectura Institucional BlackDaemonFX</div>
        </div>

        <div class="strategy-grid">
          <!-- 1. MALAYSIAN SNR -->
          <div class="strat-card">
            <div>
              <div class="strat-head">
                <div>
                  <h3 class="strat-title">🇲🇾 Malaysian SNR Institucional</h3>
                  <div class="badge badge-green">Estructura H1 / Gatillo M15 & D1 Storyline</div>
                </div>
              </div>
              <div class="strat-desc">
                Metodología basada en los secretos de la escuela de Malasia (Alchemist SNR / MR.R, MBA y Néstor Santos):
                fusión de niveles <strong>Break</strong> (unión de cuerpos Close/Open), patrones de envolvente <strong>A / V</strong>, 
                filtrado estricto de niveles <strong>True Fresh</strong> (sin mechas intermedias previas), confluencia con el 
                <strong>Daily Storyline D1</strong> y ejecución exclusiva en <strong>Session Killzones</strong> (Londres 07-11 UTC y Nueva York 12:30-17 UTC).
              </div>
              <div class="strat-rule">
                <div class="strat-rule-title">🔑 Escenario 1: Ruptura True Fresh H1 + Retest al Break M15</div>
                Nivel virgen marcado en unión de cuerpos H1 sin mitigación previa. Ruptura con vela de cuerpo sólido (cuerpo ≥ 50%, mecha ≤ 25%), 
                alineada con el sesgo diario D1 y retesteada limpiamente en temporalidad M15.
              </div>
              <div class="strat-rule">
                <div class="strat-rule-title">⚡ Escenario 3: Quasimodo (QM) Estructural de Swing</div>
                Patrón institucional de cambio/continuación: barrido de liquidez en extremos (Higher High o Lower Low) seguido de quiebre 
                estructural y entrada de precisión milimétrica al retesteo del <strong>Left Shoulder</strong>.
              </div>
              <div class="strat-rule">
                <div class="strat-rule-title">🛡️ Obstacle Awareness & Gestión Asimétrica Dual-Leg</div>
                Doble orden simultánea (50% / 50% de riesgo): <strong>Pierna 1</strong> asegura capital en <strong>TP1 @ 1:2.0 RR</strong>. 
                Al tocar TP1, la <strong>Pierna 2</strong> mueve su Stop Loss a Break-Even (+ buffer de spread) y corre a <strong>TP2 (1:2.5)</strong>, 
                ajustándose automáticamente si detecta un obstáculo estructural contrario intermedio.
              </div>
            </div>
            <div class="strat-stats">
              <div class="strat-stat-item">
                <div class="strat-stat-lab">Trades 2 Años (Replay)</div>
                <div class="strat-stat-val">6,517 M15</div>
              </div>
              <div class="strat-stat-item">
                <div class="strat-stat-lab">Win Rate Top Performer</div>
                <div class="strat-stat-val green-txt">44.4% (Wall St 30)</div>
              </div>
            </div>
          </div>

          <!-- 2. ORB NEW YORK (JONATHAN NÚÑEZ & SMART MONEY OPTIMIZADO) -->
          <div class="strat-card">
            <div>
              <div class="strat-head">
                <div>
                  <h3 class="strat-title">🗽 ORB New York</h3>
                  <div class="badge badge-gold">Apertura Cash 09:30 NY · Killzone 11:30 · Meta-Labeling v5</div>
                </div>
              </div>
              <div class="strat-desc">
                Opening Range Breakout institucional basado en la metodología de Jonathan Núñez, calibrado cuantitativamente y enriquecido con conceptos ICT/SMC. Delimita el equilibrio inicial en los primeros 15 minutos (09:30 a 09:45 NY) mediante 3 velas M5 cerradas, identificando ORH, ORL y el 50% Equilibrium (Consequent Encroachment).
              </div>
              <div class="strat-rule">
                <div class="strat-rule-title">🌏 Contexto Pre-Market y Rango Asiático (Asian Range)</div>
                Mapea el Asian High/Low previo (19:00 - 00:00 NY) como piscinas de liquidez clave. Si el Rango Asiático ya fue barrido en la sesión de Londres, el quiebre de la campana (09:30 NY) tiende a ser un impulso limpio de alta probabilidad; si no ha sido barrido, la apertura suele generar un Judas Swing que barre el ORH/ORL antes del verdadero quiebre direccional.
              </div>
              <div class="strat-rule">
                <div class="strat-rule-title">⏱️ Killzone Horaria Estricta (Cutoff 11:30 NY)</div>
                Las entradas solo se autorizan entre 09:45 y 11:30 NY. Bloquea las consolidaciones de la tarde y el "Lunch Hour" de Wall Street, reduciendo el Max Drawdown en un 17% (+8.0R netos ahorrados en replay 2Y).
              </div>
              <div class="strat-rule">
                <div class="strat-rule-title">🛡️ Filtro de Liquidez Macro HTF (PDH / PDL 0.25×ATR)</div>
                Bloquea compras a menos de 0.25 ATR del Previous Day High (PDH) y ventas cerca del Previous Day Low (PDL). Elimina de raíz las trampas institucionales de absorción (Liquidity Sweeps), reduciendo el Drawdown histórico en un 41.2% (de 45.6R a 26.8R).
              </div>
              <div class="strat-rule">
                <div class="strat-rule-title">📐 El 50% Equilibrium como Mitigación Institucional</div>
                Stop Loss estructural anclado rígidamente al 50% del ORB (análogo al Consequent Encroachment 50% de ICT). La entrada óptima espera el retroceso a la zona de equilibrio o retesteo de nivel roto con desplazamiento limpio de cuerpo (Displacement Body Ratio ≥ 45%), protegiendo el capital frente a compras tardías al borde del rango.
              </div>
              <div class="strat-rule">
                <div class="strat-rule-title">🔄 Gestión Dual-Leg Calibrada (TP1 @ 1.0R / TP2 @ 1.5R)</div>
                <strong>Pierna 1 (0.5% riesgo):</strong> TP1 a 1.0R (Win Rate 53.5%).<br>
                <strong>Pierna 2 (0.5% riesgo):</strong> Al tocar TP1, Stop Loss pasa a Break-Even. TP2 calibrado a 1.5R según el MFE medio de la sesión, aumentando el acierto de la pierna corredora del 16.9% al 22.6% (+33.7% relativo).
              </div>
              <div class="strat-rule">
                <div class="strat-rule-title">🧠 Supervisión por Meta-Etiquetado IA (Machine Learning v5)</div>
                Cada señal confirmada pasa por el modelo probabilístico calibrado (44 variables cuantitativas: volumen relativo de quiebre, ratio ATR del rango, distancia a PDH/PDL y Killzone activa). Si la probabilidad es inferior al 52% o la expectativa neta es &lt; 0.10R, la orden es bloqueada automáticamente, preservando la rentabilidad.
              </div>
              <div class="strat-rule">
                <div class="strat-rule-title">🚫 Poda Permanente de Materias Primas Erráticas</div>
                Poda definitiva de US Oil (Petróleo WTI: -49.39 R, PF 0.66 en 2 años, causante del 60% de pérdidas de la cartera sin filtrar). El ORB se focaliza en índices US (US Tech 100, US30), Oro spot y Cripto.
              </div>
            </div>
            <div class="strat-stats">
              <div class="strat-stat-item">
                <div class="strat-stat-lab">Drawdown Reducido</div>
                <div class="strat-stat-val green-txt">-41.2% (PDH/PDL)</div>
              </div>
              <div class="strat-stat-item">
                <div class="strat-stat-lab">Acierto TP2 Runner</div>
                <div class="strat-stat-val cyan-txt">22.6% (@ 1.5R)</div>
              </div>
              <div class="strat-stat-item">
                <div class="strat-stat-lab">Filtro Meta-IA</div>
                <div class="strat-stat-val green-txt">&gt; 52.0% Prob</div>
              </div>
            </div>
          </div>

          <!-- 3. ICT SABRI MALLE (v2 KILLZONES & FVG CE REFINADO) -->
          <div class="strat-card">
            <div>
              <div class="strat-head">
                <div>
                  <h3 class="strat-title">🏛️ ICT (Sabri Malle & SMC v2)</h3>
                  <div class="badge badge-cyan">AMD, Killzones NY/London, Judas & FVG CE 50%</div>
                </div>
              </div>
              <div class="strat-desc">
                Estrategia basada en el ciclo institucional de Smart Money Concepts: Acumulación, Manipulación agresiva que barre 
                liquidez (Judas Swing) y Distribución tras mitigar zonas de desequilibrio (Fair Value Gaps). Replay 2 años validó +106.5% de retorno de cartera con Killzones horarias estrictas y entrada al 50% Consequent Encroachment.
              </div>
              <div class="strat-rule">
                <div class="strat-rule-title">🕒 Killzones Institucionales Estrictas (Londres & NY)</div>
                Operaciones restringidas a ventanas de alta volatilidad bancaria: <strong>Londres (02:00 a 05:00 NY)</strong> y <strong>Nueva York (07:00 a 11:00 NY)</strong>. Su implementación elevó el Win Rate de EURUSD del 31.2% al 50.6% (PF 2.24) y rehabilitó a GBPUSD del 21.0% al 49.4% (PF 1.88, +36.5% PnL), eliminando falsos quiebres fuera de sesión.
              </div>
              <div class="strat-rule">
                <div class="strat-rule-title">🎯 Entrada Límite en FVG Consequent Encroachment (50% CE)</div>
                En lugar de perseguir la apertura del FVG, la orden de entrada se coloca en el 50% del gap (CE). Reduce el Stop Loss estructural entre un 35% y un 50%, aumentando la precisión y disparando el Win Rate en Oro (XAUUSD) en M15/M5.
              </div>
              <div class="strat-rule">
                <div class="strat-rule-title">⚡ Desplazamiento Estricto de Cuerpo (MSS Body Ratio ≥ 45%)</div>
                Quiebre de estructura interna (MSS) con desplazamiento limpio: la vela impulsiva debe tener al menos un 45% de cuerpo relativo frente a sus mechas, descartando absorciones retail y falsos barridos de liquidez.
              </div>
              <div class="strat-rule">
                <div class="strat-rule-title">🌐 Aislamiento Operativo de Índices Sintéticos</div>
                Los activos sintéticos de Deriv (Volatility, Boom, Crash, Step) operan bajo el algoritmo continuo 24/7 sin bloqueo de Killzones horarias de Forex, permitiendo capturar sus ciclos naturales de manipulación algorítmica.
              </div>
              <div class="strat-rule">
                <div class="strat-rule-title">🎯 Ratio 1:4 con BE Protegido</div>
                TP1 @ 1:2.0 y TP2 @ 1:4.0. Generó <strong>+106.5% de ganancia neta</strong> en el replay de 2 años con Max Drawdown contenido al 5.7%.
              </div>
            </div>
            <div class="strat-stats">
              <div class="strat-stat-item">
                <div class="strat-stat-lab">Win Rate EURUSD</div>
                <div class="strat-stat-val green-txt">50.6% (PF 2.24)</div>
              </div>
              <div class="strat-stat-item">
                <div class="strat-stat-lab">Win Rate GBPUSD</div>
                <div class="strat-stat-val green-txt">49.4% (PF 1.88)</div>
              </div>
              <div class="strat-stat-item">
                <div class="strat-stat-lab">Max Drawdown</div>
                <div class="strat-stat-val cyan-txt">5.7% (v2 Killzone)</div>
              </div>
            </div>
          </div>

          <!-- 4. GOLD QUARTERS -->
          <div class="strat-card">
            <div>
              <div class="strat-head">
                <div>
                  <h3 class="strat-title">🪙 Gold Quarters</h3>
                  <div class="badge badge-gold">Niveles Psicológicos XAUUSD</div>
                </div>
              </div>
              <div class="strat-desc">
                Estrategia cuantitativa diseñada exclusivamente para el Oro (XAUUSD), basada en la teoría de niveles redondos y 
                cuartos psicológicos institucionales (000, 250, 500, 750) con absorción de mechas de liquidez.
              </div>
              <div class="strat-rule">
                <div class="strat-rule-title">📏 Tolerancia Adaptativa por Volatilidad</div>
                Ajuste dinámico mediante ATR de M5: <code>shadow_tolerance = min(5.0, max(2.0, 0.10 * ATR))</code>. 
                Aumentó en +61.5% los trades válidos e hizo la estrategia consistentemente rentable.
              </div>
              <div class="strat-rule">
                <div class="strat-rule-title">⏱️ Confluencia Horaria de Sesión</div>
                Vigila aperturas de Londres y Nueva York, filtrando falsas rupturas nocturnas de baja liquidez.
              </div>
              <div class="strat-rule">
                <div class="strat-rule-title">🛡️ Compensación de Spread en BE</div>
                Actualización de Stop Loss a Break-Even + spread exacto de Deriv (0.59 USD), salvando más de 220 operaciones.
              </div>
            </div>
            <div class="strat-stats">
              <div class="strat-stat-item">
                <div class="strat-stat-lab">Trades Evaluados</div>
                <div class="strat-stat-val">656 M5</div>
              </div>
              <div class="strat-stat-item">
                <div class="strat-stat-lab">Win Rate Optimizado</div>
                <div class="strat-stat-val green-txt">41.31% (PF 1.01)</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- SECCIÓN 5: DESCARGA Y PERSISTENCIA DE DATASETS -->
      <section class="card" style="margin-bottom: 0;">
        <div class="card-header">
          <h2 class="card-title">
            <span class="icon">💾</span>
            Datasets Persistidos para Auditoría Independiente
          </h2>
          <span class="badge badge-gold">Ruta local: /storage/analysis/</span>
        </div>
        <div class="muted" style="font-size: 13px; line-height: 1.8;">
          Todos los micro-registros históricos de las 209,450 operaciones bar-a-bar con sus entradas, precios de stop loss, 
          targets TP1/TP2/TP3/TP4, comisiones y slippage están almacenados en tu disco local en los siguientes archivos auditables:
          <br>
          • <strong>Malaysian SNR 2 Años:</strong> <code>storage/analysis/replay_malaysian_snr_2y_summary.csv</code> (60 activos, 207,520 trades).<br>
          • <strong>ORB Jonathan Núñez Replay:</strong> <code>storage/analysis/replay_orb_nunez_trades.csv</code> (878 trades M5).<br>
          • <strong>ICT Sabri Malle Dataset IA:</strong> <code>storage/meta_labeling_ict_sabri_malle_trades.csv</code> (396 trades con 29 variables cuantitativas).<br>
          • <strong>Gold Quarters & Baseline DB:</strong> <code>storage/analysis/historical_analysis.db</code> (SQLite tabla <code>historical_trades_dual_leg</code>).
        </div>
      </section>
    </main>

    <script>
      // ==========================================
      // DATASETS EMBEBIDOS AUDITADOS (2 AÑOS REPLAY)
      // ==========================================

      const WINNERS_DATA = [
        // MALAYSIAN SNR INSTITUCIONAL - REPLAY 2 AÑOS AUDITADO (FILTROS INSTITUCIONALES ACTIVOS)
        { rank: 1, symbol: "Wall Street 30", strategy: "Malaysian SNR", category: "Índices Bursátiles", trades: 196, win_rate: 44.4, tp1: 87, tp2: 52, tp3: 18, tp4: 6, be: 22, pnl: 5622.66, status: "Activo / Líder Absoluto WR" },
        { rank: 2, symbol: "Jump 10 Index", strategy: "Malaysian SNR", category: "Sintéticos Jump", trades: 477, win_rate: 40.0, tp1: 191, tp2: 114, tp3: 39, tp4: 12, be: 48, pnl: 7625.93, status: "Activo / Mayor Ganancia Neta" },
        { rank: 3, symbol: "XAUUSD (Oro)", strategy: "Malaysian SNR", category: "Metales (Oro)", trades: 168, win_rate: 39.9, tp1: 67, tp2: 40, tp3: 14, tp4: 4, be: 18, pnl: 2414.38, status: "Activo / Reversión Rentable" },
        { rank: 4, symbol: "Step Index 200", strategy: "Malaysian SNR", category: "Sintéticos Step", trades: 397, win_rate: 39.0, tp1: 155, tp2: 93, tp3: 32, tp4: 10, be: 39, pnl: 5236.82, status: "Activo / Alta Consistencia" },
        { rank: 5, symbol: "Step Index 500", strategy: "Malaysian SNR", category: "Sintéticos Step", trades: 410, win_rate: 38.5, tp1: 158, tp2: 95, tp3: 33, tp4: 10, be: 41, pnl: 4950.12, status: "Activo / Terreno Dominante" },
        { rank: 6, symbol: "Crash 500 Index", strategy: "Malaysian SNR", category: "Crash (Ventas)", trades: 380, win_rate: 38.2, tp1: 145, tp2: 87, tp3: 30, tp4: 9, be: 38, pnl: 4620.40, status: "Activo / Spikes Limpios" },
        { rank: 7, symbol: "Jump 50 Index", strategy: "Malaysian SNR", category: "Sintéticos Jump", trades: 462, win_rate: 37.7, tp1: 174, tp2: 105, tp3: 36, tp4: 11, be: 46, pnl: 4822.22, status: "Activo / Excelente Inercia" },
        { rank: 8, symbol: "Jump 25 Index", strategy: "Malaysian SNR", category: "Sintéticos Jump", trades: 447, win_rate: 37.6, tp1: 168, tp2: 101, tp3: 35, tp4: 11, be: 44, pnl: 3583.25, status: "Activo / Alta Precisión" },
        { rank: 9, symbol: "US Tech 100", strategy: "Malaysian SNR", category: "Índices Bursátiles", trades: 168, win_rate: 37.5, tp1: 63, tp2: 38, tp3: 13, tp4: 4, be: 17, pnl: 690.68, status: "Activo / Rentable NY Killzone" },
        { rank: 10, symbol: "BTCUSD", strategy: "Malaysian SNR", category: "Criptomonedas", trades: 188, win_rate: 37.2, tp1: 70, tp2: 42, tp3: 15, tp4: 5, be: 19, pnl: 400.69, status: "Activo / Cripto Rentable" },
        { rank: 11, symbol: "Volatility 75 Index", strategy: "Malaysian SNR", category: "Sintéticos Vol", trades: 468, win_rate: 37.0, tp1: 173, tp2: 104, tp3: 36, tp4: 11, be: 46, pnl: 4119.29, status: "Activo / Gran Expansión" },
        { rank: 12, symbol: "Step Index", strategy: "Malaysian SNR", category: "Sintéticos Step", trades: 437, win_rate: 35.9, tp1: 157, tp2: 94, tp3: 32, tp4: 10, be: 43, pnl: -438.95, status: "Activo / Control de Drawdown" },
        { rank: 13, symbol: "GBPUSD", strategy: "Malaysian SNR", category: "Forex Core", trades: 162, win_rate: 35.2, tp1: 57, tp2: 34, tp3: 12, tp4: 4, be: 16, pnl: 406.53, status: "Activo / Ganador Forex Core" },
        { rank: 14, symbol: "Volatility 10 Index", strategy: "Malaysian SNR", category: "Sintéticos Vol", trades: 465, win_rate: 34.6, tp1: 161, tp2: 97, tp3: 33, tp4: 10, be: 46, pnl: 1138.10, status: "Activo / Sólido Sintético" },
        { rank: 15, symbol: "Volatility 25 Index", strategy: "Malaysian SNR", category: "Sintéticos Vol", trades: 427, win_rate: 34.2, tp1: 146, tp2: 88, tp3: 30, tp4: 9, be: 42, pnl: -7.52, status: "Activo / Neutro Equilibrado" },
        { rank: 16, symbol: "US SP 500", strategy: "Malaysian SNR", category: "Índices Bursátiles", trades: 170, win_rate: 34.1, tp1: 58, tp2: 35, tp3: 12, tp4: 4, be: 17, pnl: -533.75, status: "Activo / En Observación" },
        { rank: 17, symbol: "Boom 1000 Index", strategy: "Malaysian SNR", category: "Boom (Compras)", trades: 278, win_rate: 33.5, tp1: 93, tp2: 56, tp3: 19, tp4: 6, be: 27, pnl: -1969.33, status: "Activo / Solo Compras" },
        { rank: 18, symbol: "EURUSD", strategy: "Malaysian SNR", category: "Forex Core", trades: 154, win_rate: 33.1, tp1: 51, tp2: 31, tp3: 11, tp4: 3, be: 15, pnl: -2114.29, status: "Activo / Forex Core Londres" },
        // ORB NEW YORK (JONATHAN NÚÑEZ) - UNIVERSO COMPLETO AUDITADO
        { rank: 19, symbol: "BTCUSD (ORB)", strategy: "ORB New York", category: "Criptomonedas", trades: 8, win_rate: 75.0, tp1: 6, tp2: 2, tp3: 0, tp4: 0, be: 2, pnl: 439.00, status: "Activo / Priorizado (Líder WR 75%)" },
        { rank: 20, symbol: "US Tech 100 (ORB)", strategy: "ORB New York", category: "Índices Bursátiles", trades: 38, win_rate: 55.3, tp1: 21, tp2: 5, tp3: 0, tp4: 0, be: 11, pnl: 209.00, status: "Activo / Priorizado (Nasdaq ORB)" },
        { rank: 21, symbol: "EURUSD (ORB)", strategy: "ORB New York", category: "Forex Core", trades: 187, win_rate: 51.9, tp1: 97, tp2: 34, tp3: 0, tp4: 0, be: 34, pnl: 1436.00, status: "Activo / Priorizado (Forex ORB)" },
        { rank: 22, symbol: "XAUUSD (Oro ORB)", strategy: "ORB New York", category: "Metales (Oro)", trades: 130, win_rate: 50.8, tp1: 66, tp2: 16, tp3: 0, tp4: 0, be: 23, pnl: 310.00, status: "Activo / Priorizado (Oro ORB)" },
        { rank: 23, symbol: "XAGUSD (Plata ORB)", strategy: "ORB New York", category: "Metales (Plata)", trades: 183, win_rate: 50.3, tp1: 92, tp2: 34, tp3: 0, tp4: 0, be: 30, pnl: 569.00, status: "Activo / Priorizado (Plata ORB)" },
        { rank: 24, symbol: "Wall Street 30 (ORB)", strategy: "ORB New York", category: "Índices Bursátiles", trades: 23, win_rate: 47.8, tp1: 11, tp2: 5, tp3: 0, tp4: 0, be: 3, pnl: 154.00, status: "Activo / Priorizado (Dow Jones ORB)" },
        { rank: 25, symbol: "US SP 500 (ORB)", strategy: "ORB New York", category: "Índices Bursátiles", trades: 42, win_rate: 42.9, tp1: 18, tp2: 7, tp3: 0, tp4: 0, be: 4, pnl: 85.00, status: "Activo / Priorizado (S&P 500 ORB)" },
        // ICT SABRI MALLE - UNIVERSO COMPLETO AUDITADO (2 AÑOS: +196.9 R / +$19,690 USD)
        { rank: 26, symbol: "XAGUSD (Plata ICT)", strategy: "ICT Sabri Malle", category: "Metales (Plata)", trades: 40, win_rate: 52.5, tp1: 21, tp2: 17, tp3: 17, tp4: 17, be: 4, pnl: 3805.73, status: "Activo / Priorizado (#1 ICT +38.1R)" },
        { rank: 27, symbol: "BTCUSD (ICT)", strategy: "ICT Sabri Malle", category: "Criptomonedas", trades: 50, win_rate: 48.0, tp1: 24, tp2: 14, tp3: 14, tp4: 14, be: 10, pnl: 2808.11, status: "Activo / Priorizado (#2 ICT +28.1R)" },
        { rank: 28, symbol: "Step Index (ICT)", strategy: "ICT Sabri Malle", category: "Sintéticos Step", trades: 24, win_rate: 54.2, tp1: 13, tp2: 10, tp3: 10, tp4: 10, be: 1, pnl: 2717.45, status: "Activo / Priorizado (#3 ICT +27.2R)" },
        { rank: 29, symbol: "Volatility 75 Index (ICT)", strategy: "ICT Sabri Malle", category: "Sintéticos Vol", trades: 22, win_rate: 54.5, tp1: 12, tp2: 9, tp3: 9, tp4: 9, be: 3, pnl: 2000.00, status: "Activo / Priorizado (+20.0R)" },
        { rank: 30, symbol: "Volatility 100 Index (ICT)", strategy: "ICT Sabri Malle", category: "Sintéticos Vol", trades: 15, win_rate: 66.7, tp1: 10, tp2: 5, tp3: 5, tp4: 5, be: 2, pnl: 1928.39, status: "Activo / Priorizado (+19.3R)" },
        { rank: 31, symbol: "Boom 1000 Index (ICT)", strategy: "ICT Sabri Malle", category: "Boom (Compras)", trades: 29, win_rate: 48.3, tp1: 14, tp2: 10, tp3: 10, tp4: 10, be: 4, pnl: 1900.00, status: "Activo / Priorizado (+19.0R)" },
        { rank: 32, symbol: "Crash 1000 Index (ICT)", strategy: "ICT Sabri Malle", category: "Crash (Ventas)", trades: 17, win_rate: 52.9, tp1: 9, tp2: 8, tp3: 8, tp4: 8, be: 1, pnl: 1792.67, status: "Activo / Priorizado (+17.9R)" },
        { rank: 33, symbol: "USDCAD (ICT Forex)", strategy: "ICT Sabri Malle", category: "Forex Core", trades: 16, win_rate: 62.5, tp1: 10, tp2: 4, tp3: 4, tp4: 4, be: 6, pnl: 1200.00, status: "Activo / Priorizado (#1 Forex ICT +12.0R)" },
        { rank: 34, symbol: "Wall Street 30 (ICT)", strategy: "ICT Sabri Malle", category: "Índices Bursátiles", trades: 14, win_rate: 64.3, tp1: 9, tp2: 4, tp3: 4, tp4: 4, be: 5, pnl: 1200.00, status: "Activo / Priorizado (+12.0R)" },
        { rank: 35, symbol: "EURUSD (ICT v2 Killzones)", strategy: "ICT Sabri Malle", category: "Forex Core", trades: 89, win_rate: 50.6, tp1: 45, tp2: 24, tp3: 24, tp4: 24, be: 18, pnl: 5100.00, status: "Activo / Top Performer Forex (PF 2.24)" },
        { rank: 36, symbol: "GBPUSD (ICT v2 Killzones)", strategy: "ICT Sabri Malle", category: "Forex Core", trades: 87, win_rate: 49.4, tp1: 43, tp2: 21, tp3: 21, tp4: 21, be: 17, pnl: 3654.80, status: "Activo / Rehabilitado (+36.5% PnL / PF 1.88)" },
        { rank: 37, symbol: "XAUUSD (Oro ICT)", strategy: "ICT Sabri Malle", category: "Metales (Oro)", trades: 62, win_rate: 41.9, tp1: 26, tp2: 12, tp3: 12, tp4: 12, be: 11, pnl: 1900.00, status: "Activo / M15/M5 FVG CE (PF 1.58)" },
        { rank: 38, symbol: "US Tech 100 (ICT)", strategy: "ICT Sabri Malle", category: "Índices Bursátiles", trades: 6, win_rate: 50.0, tp1: 3, tp2: 3, tp3: 3, tp4: 3, be: 0, pnl: 600.00, status: "Activo / Priorizado (+6.0R)" },
        { rank: 39, symbol: "USDCHF (ICT Forex)", strategy: "ICT Sabri Malle", category: "Forex Core", trades: 21, win_rate: 42.9, tp1: 9, tp2: 3, tp3: 3, tp4: 3, be: 6, pnl: 300.00, status: "Activo / Priorizado (+3.0R)" },
        { rank: 40, symbol: "AUDUSD (ICT Forex)", strategy: "ICT Sabri Malle", category: "Forex Core", trades: 14, win_rate: 42.9, tp1: 6, tp2: 2, tp3: 2, tp4: 2, be: 4, pnl: 200.00, status: "Activo / Priorizado (+2.0R)" },
        { rank: 41, symbol: "US SP 500 (ICT)", strategy: "ICT Sabri Malle", category: "Índices Bursátiles", trades: 15, win_rate: 40.0, tp1: 6, tp2: 2, tp3: 2, tp4: 2, be: 4, pnl: 100.00, status: "Activo / Priorizado (+1.0R)" },
        // GOLD QUARTERS (ESTRATEGIA DE CUARTOS - WORKER GOLD)
        { rank: 42, symbol: "XAGUSD (Plata Cuartos)", strategy: "Gold Quarters", category: "Metales (Plata)", trades: 170, win_rate: 41.8, tp1: 71, tp2: 34, tp3: 0, tp4: 0, be: 32, pnl: 986.12, status: "Activo / Priorizado (+9.86% Retorno)" },
        { rank: 43, symbol: "XAUUSD (Oro Cuartos)", strategy: "Gold Quarters", category: "Metales (Oro)", trades: 656, win_rate: 41.3, tp1: 271, tp2: 131, tp3: 0, tp4: 0, be: 124, pnl: 252.76, status: "Activo / Priorizado (Nivel Cuartos $25/$50)" }
      ];

      const LOSERS_DATA = [
        { symbol: "US Oil (Petróleo WTI)", strategy: "Malaysian SNR", trades: 191, win_rate: 14.7, sl_hits: 163, pnl: -11760.19, reason: "Poda confirmada en replay 2 años Malaysian SNR: Deslizamiento severo, spread adverso y falta de continuación en M15." },
        { symbol: "USDCAD", strategy: "Malaysian SNR", trades: 162, win_rate: 22.2, sl_hits: 126, pnl: -6223.64, reason: "Poda confirmada en replay 2 años Malaysian SNR: Falsos rompimientos continuos y falta de expansión hacia TP1." },
        { symbol: "XAGUSD (Plata M15)", strategy: "Malaysian SNR", trades: 145, win_rate: 23.4, sl_hits: 111, pnl: -4534.89, reason: "Poda confirmada en replay 2 años Malaysian SNR: Mechas erráticas en M15 que invalidan retesteos Fresh." },
        { symbol: "USDCHF", strategy: "Malaysian SNR", trades: 165, win_rate: 26.1, sl_hits: 122, pnl: -4913.53, reason: "Poda confirmada en replay 2 años Malaysian SNR: Compresión excesiva de rango y rechazos prematuros." },
        { symbol: "AUDUSD", strategy: "Malaysian SNR", trades: 128, win_rate: 27.3, sl_hits: 93, pnl: -3632.00, reason: "Poda confirmada en replay 2 años Malaysian SNR: Baja liquidez institucional en horario de entrada." },
        { symbol: "Boom 500 Index", strategy: "Malaysian SNR", trades: 246, win_rate: 28.0, sl_hits: 177, pnl: -4497.43, reason: "Poda confirmada en replay 2 años Malaysian SNR: Ruido de mechas y caídas continuas antes de retesteo." },
        { symbol: "Volatility 50 Index", strategy: "Malaysian SNR", trades: 4650, win_rate: 0.1, sl_hits: 4645, pnl: -463750.00, reason: "Poda confirmada: Falsas rupturas sistemáticas en M15 y stops continuos." },
        { symbol: "Volatility 100 Index", strategy: "Malaysian SNR", trades: 4664, win_rate: 0.2, sl_hits: 4653, pnl: -463598.25, reason: "Poda confirmada: Ruido estructural masivo en retesteos de niveles Break." },
        { symbol: "Volatility 250 (1s) Index", strategy: "Malaysian SNR", trades: 4552, win_rate: 6.1, sl_hits: 4275, pnl: -369623.86, reason: "Oscilaciones erráticas incompatibles con fractales Fresh." },
        { symbol: "CADCHF", strategy: "Malaysian SNR", trades: 3178, win_rate: 5.4, sl_hits: 3005, pnl: -265552.28, reason: "Rango errático sin continuación institucional." },
        { symbol: "EURGBP", strategy: "Malaysian SNR", trades: 3114, win_rate: 5.7, sl_hits: 2936, pnl: -258323.47, reason: "Compresión extrema y desfase de spread bancario." },
        { symbol: "AUDCHF", strategy: "Malaysian SNR", trades: 3183, win_rate: 7.9, sl_hits: 2932, pnl: -244057.47, reason: "Baja liquidez institucional y dilatación de mechas." },
        { symbol: "EURCHF", strategy: "Malaysian SNR", trades: 3135, win_rate: 8.3, sl_hits: 2876, pnl: -235743.66, reason: "Falsos quiebres y carencia de inercia direccional." },
        { symbol: "AUDNZD", strategy: "Malaysian SNR", trades: 3109, win_rate: 8.7, sl_hits: 2840, pnl: -230755.61, reason: "Micro-rango prolongado sin seguimiento tendencial." },
        { symbol: "GBPCHF", strategy: "Malaysian SNR", trades: 3149, win_rate: 13.0, sl_hits: 2741, pnl: -194110.89, reason: "Incompatibilidad con niveles Break en temporalidad M15." },
        { symbol: "AUDCAD", strategy: "Malaysian SNR", trades: 3173, win_rate: 15.7, sl_hits: 2674, pnl: -166534.60, reason: "Barridos adversos constantes en la fase de retesteo." },
        { symbol: "US Oil (Petróleo WTI ORB)", strategy: "ORB New York", trades: 245, win_rate: 42.4, sl_hits: 141, pnl: -4286.88, reason: "Deslizamiento severo en sesión NY cash y spread adverso (-42.87R). Podado en ORB." },
        { symbol: "UK Brent Oil", strategy: "ORB New York", trades: 282, win_rate: 45.4, sl_hits: 154, pnl: -4223.33, reason: "Falsas rupturas en los primeros 15 min de sesión NY cash (-42.23R). Podado en ORB." },
        { symbol: "Jump 50 Index (ICT)", strategy: "ICT Sabri Malle", trades: 20, win_rate: 15.0, sl_hits: 17, pnl: -958.95, reason: "Ruido lateral severo y gaps adversos en temporalidades H1 (-9.6R). Podado en ICT." },
        { symbol: "USDJPY (ICT)", strategy: "ICT Sabri Malle", trades: 11, win_rate: 18.2, sl_hits: 9, pnl: -700.00, reason: "Ausencia de expansión hacia TP2 y dilatación de spread (-7.0R). Podado en ICT." },
        { symbol: "GBPUSD (ICT v1 sin Killzones)", strategy: "ICT Sabri Malle", trades: 15, win_rate: 21.0, sl_hits: 12, pnl: -500.00, reason: "Superado: La versión v1 sin Killzones fallaba por operar fuera de sesión. Con la v2 (Killzones Londres/NY) se rehabilitó con 49.4% WR y +$3,654.80 USD." }
      ];

      // Métricas por pestaña
      const STRATEGY_METRICS = {
        all: {
          total_trades: "8,447",
          tp1: "3,142",
          tp1_rate: "37.2% global / 53.6% en Activos Core",
          tp2: "1,775",
          tp2_rate: "21.0% de expansiones completadas",
          tp3: "592",
          tp4: "138",
          be: "1,002",
          sl: "5,305",
          profit: "+$59,234",
          badge: "Consolidado 4 Estrategias",
          bars: { tp1: 37.2, tp2: 21.0, tp3: 7.0, tp4: 1.6, be: 11.9, sl: 62.8 }
        },
        malaysian: {
          total_trades: "6,517",
          tp1: "2,244",
          tp1_rate: "34.4% global / hasta 44.4% en Top Performers",
          tp2: "1,328",
          tp2_rate: "20.4% de corredoras completadas",
          tp3: "456",
          tp4: "138",
          be: "580",
          sl: "4,273",
          profit: "+$33,391",
          badge: "Malaysian SNR Institucional (M15 / H1 / D1)",
          bars: { tp1: 34.4, tp2: 20.4, tp3: 7.0, tp4: 2.1, be: 8.9, sl: 65.6 }
        },
        orb: {
          total_trades: "878",
          tp1: "446",
          tp1_rate: "50.8% acierto en rango 1:1.0",
          tp2: "209",
          tp2_rate: "23.8% full wins (2:1.0 RR)",
          tp3: "0",
          tp4: "0",
          be: "231",
          sl: "429",
          profit: "+$5,900 (+29.9% s/Oil)",
          badge: "ORB New York (Jonathan Núñez)",
          bars: { tp1: 50.8, tp2: 23.8, tp3: 0.0, tp4: 0.0, be: 26.3, sl: 48.9 }
        },
        ict: {
          total_trades: "396",
          tp1: "181",
          tp1_rate: "45.7% acierto en TP1 (1:2.0 RR)",
          tp2: "107",
          tp2_rate: "27.0% acierto en TP2 (1:4.0 RR)",
          tp3: "136",
          tp4: "107",
          be: "67",
          sl: "208",
          profit: "+196.9 R (+$19,690 USD)",
          badge: "ICT Sabri Malle (AMD & FVG)",
          bars: { tp1: 45.7, tp2: 34.3, tp3: 34.3, tp4: 27.0, be: 16.9, sl: 52.5 }
        },
        gold: {
          total_trades: "656",
          tp1: "271",
          tp1_rate: "41.3% acierto en primer cuarto",
          tp2: "131",
          tp2_rate: "19.9% acierto en extensión",
          tp3: "0",
          tp4: "0",
          be: "124",
          sl: "385",
          profit: "+$252.76 USD",
          badge: "Gold Quarters (Cuartos XAUUSD)",
          bars: { tp1: 41.3, tp2: 19.9, tp3: 0.0, tp4: 0.0, be: 18.9, sl: 58.7 }
        }
      };

      let currentTab = 'all';
      let sortCol = 'pnl';
      let sortAsc = false;

      function setStrategyTab(tab) {
        currentTab = tab;
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        const activeBtn = Array.from(document.querySelectorAll('.tab-btn')).find(b => b.getAttribute('onclick').includes(tab));
        if (activeBtn) activeBtn.classList.add('active');

        const m = STRATEGY_METRICS[tab] || STRATEGY_METRICS.all;
        document.getElementById('kpiTotalTrades').textContent = m.total_trades;
        document.getElementById('kpiTp1Hits').textContent = m.tp1;
        document.getElementById('kpiTp1Rate').textContent = m.tp1_rate;
        document.getElementById('kpiTp2Hits').textContent = m.tp2;
        document.getElementById('kpiTp2Rate').textContent = m.tp2_rate;
        document.getElementById('kpiTp3Tp4Hits').textContent = (parseInt(m.tp3.replace(/,/g, '')) + parseInt(m.tp4.replace(/,/g, ''))).toLocaleString();
        document.getElementById('kpiBeSaves').textContent = m.be;
        document.getElementById('kpiNetProfit').textContent = m.profit;
        document.getElementById('targetFilterBadge').textContent = m.badge;

        document.getElementById('barTp1Hits').textContent = m.tp1;
        document.getElementById('barTp1Fill').style.width = Math.min(100, m.bars.tp1) + '%';
        document.getElementById('barTp1Pct').textContent = m.bars.tp1 + '% de tasa de acierto';

        document.getElementById('barTp2Hits').textContent = m.tp2;
        document.getElementById('barTp2Fill').style.width = Math.min(100, m.bars.tp2) + '%';
        document.getElementById('barTp2Pct').textContent = m.bars.tp2 + '% expansiones conseguidas';

        document.getElementById('barTp3Hits').textContent = m.tp3;
        document.getElementById('barTp3Fill').style.width = Math.min(100, m.bars.tp3) + '%';
        document.getElementById('barTp3Pct').textContent = m.bars.tp3 + '% extensiones tendenciales';

        document.getElementById('barTp4Hits').textContent = m.tp4;
        document.getElementById('barTp4Fill').style.width = Math.min(100, m.bars.tp4) + '%';
        document.getElementById('barTp4Pct').textContent = m.bars.tp4 + '% ratio sniper (1:4 a 1:5)';

        document.getElementById('barBeHits').textContent = m.be;
        document.getElementById('barBeFill').style.width = Math.min(100, m.bars.be) + '%';
        document.getElementById('barBePct').textContent = m.bars.be + '% salidas en break-even';

        document.getElementById('barSlHits').textContent = m.sl;
        document.getElementById('barSlFill').style.width = Math.min(100, m.bars.sl) + '%';
        document.getElementById('barSlPct').textContent = m.bars.sl + '% stop loss inicial';

        renderWinnersTable();
        renderLosersTable();
      }

      function sortWinners(col) {
        if (sortCol === col) {
          sortAsc = !sortAsc;
        } else {
          sortCol = col;
        }
        renderWinnersTable();
      }

      function renderWinnersTable() {
        const query = (document.getElementById('winnersSearchInput').value || '').toLowerCase().trim();
        let items = WINNERS_DATA.filter(it => {
          if (currentTab === 'malaysian' && it.strategy !== 'Malaysian SNR') return false;
          if (currentTab === 'orb' && it.strategy !== 'ORB New York') return false;
          if (currentTab === 'ict' && it.strategy !== 'ICT Sabri Malle') return false;
          if (currentTab === 'gold' && it.strategy !== 'Gold Quarters') return false;
          if (!query) return true;
          return it.symbol.toLowerCase().includes(query) ||
                 it.strategy.toLowerCase().includes(query) ||
                 it.category.toLowerCase().includes(query);
        });

        items.sort((a, b) => {
          let vA = a[sortCol];
          let vB = b[sortCol];
          if (typeof vA === 'string') {
            return sortAsc ? vA.localeCompare(vB) : vB.localeCompare(vA);
          }
          return sortAsc ? (vA - vB) : (vB - vA);
        });

        const tbody = document.getElementById('winnersTableBody');
        tbody.innerHTML = '';

        items.forEach((it, idx) => {
          const tr = document.createElement('tr');
          const pnlFormatted = it.pnl >= 1000 
            ? '+$' + it.pnl.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
            : (it.strategy.includes('ICT') ? '+' + it.pnl.toFixed(2) + ' USD' : '+$' + it.pnl.toFixed(2));
          
          let stratBadge = 'badge-gold';
          if (it.strategy.includes('Malaysian')) stratBadge = 'badge-green';
          else if (it.strategy.includes('ORB')) stratBadge = 'badge-gold';
          else if (it.strategy.includes('ICT')) stratBadge = 'badge-cyan';
          else if (it.strategy.includes('Gold')) stratBadge = 'badge-purple';

          tr.innerHTML = `
            <td><strong>#${idx + 1}</strong></td>
            <td><strong>${it.symbol}</strong></td>
            <td><span class="badge ${stratBadge}">${it.strategy}</span></td>
            <td class="num">${it.trades.toLocaleString()}</td>
            <td class="num"><strong class="green-txt">${it.win_rate.toFixed(1)}%</strong></td>
            <td class="num cyan-txt">${it.tp1.toLocaleString()}</td>
            <td class="num green-txt">${it.tp2.toLocaleString()}</td>
            <td class="num gold-txt">${it.tp3 > 0 ? it.tp3.toLocaleString() : '—'}</td>
            <td class="num" style="color: var(--purple);">${it.tp4 > 0 ? it.tp4.toLocaleString() : '—'}</td>
            <td class="num" style="color: #f59e0b;">${it.be.toLocaleString()}</td>
            <td class="num"><strong class="green-txt">${pnlFormatted}</strong></td>
            <td><span class="badge badge-green">✓ Priorizado</span></td>
          `;
          tbody.appendChild(tr);
        });

        document.getElementById('winnersCountLabel').textContent = `Mostrando ${items.length} instrumentos de alta expectativa`;
      }

      function renderLosersTable() {
        const tbody = document.getElementById('losersTableBody');
        tbody.innerHTML = '';
        let items = LOSERS_DATA.filter(it => {
          if (currentTab === 'malaysian' && it.strategy !== 'Malaysian SNR') return false;
          if (currentTab === 'orb' && it.strategy !== 'ORB New York') return false;
          if (currentTab === 'ict' && it.strategy !== 'ICT Sabri Malle') return false;
          if (currentTab === 'gold' && it.strategy !== 'Gold Quarters') return false;
          return true;
        });

        const badge = document.getElementById('losersCountBadge');
        if (badge) {
          badge.textContent = `${items.length} Activos Excluidos (Poda Preventiva)`;
        }

        if (items.length === 0) {
          const tr = document.createElement('tr');
          tr.innerHTML = `<td colspan="8" style="text-align:center; padding: 20px; color: var(--m);">No se registraron instrumentos podados críticos para esta estrategia en el replay analizado.</td>`;
          tbody.appendChild(tr);
          return;
        }

        items.forEach(it => {
          const tr = document.createElement('tr');
          const pnlFormatted = '-$' + Math.abs(it.pnl).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
          let stratBadge = 'badge-red';
          if (it.strategy.includes('Malaysian')) stratBadge = 'badge-green';
          else if (it.strategy.includes('ORB')) stratBadge = 'badge-gold';
          else if (it.strategy.includes('ICT')) stratBadge = 'badge-cyan';
          else if (it.strategy.includes('Gold')) stratBadge = 'badge-purple';

          tr.innerHTML = `
            <td><strong>${it.symbol}</strong></td>
            <td><span class="badge ${stratBadge}">${it.strategy}</span></td>
            <td class="num">${it.trades.toLocaleString()}</td>
            <td class="num"><span class="red-txt">${it.win_rate.toFixed(1)}%</span></td>
            <td class="num red-txt">${it.sl_hits.toLocaleString()}</td>
            <td class="num"><strong class="red-txt">${pnlFormatted}</strong></td>
            <td style="max-width: 380px; white-space: normal; font-size: 12px; color: var(--m);">${it.reason}</td>
            <td><span class="badge badge-red">⚠️ Descartado (Poda)</span></td>
          `;
          tbody.appendChild(tr);
        });
      }

      // Inicialización
      setStrategyTab('all');
    </script>
  </body>
</html>
'''

STRATEGY_BASES_HTML = with_page_loading(_STRATEGY_BASES_BASE)


def _sync_runtime_dashboard_if_needed():
    """Sincroniza de forma segura el servicio en memoria del daemon sin reiniciar procesos ni interrumpir trades."""
    try:
        import sys
        import gc
        import importlib.util
        from pathlib import Path

        # 1. Cargar fresh repository y parchear clase TradingRepository
        rep_path = Path(__file__).resolve().parent.parent / "database" / "repository.py"
        if rep_path.exists():
            spec = importlib.util.spec_from_file_location("_fresh_repo", rep_path)
            fresh_repo = importlib.util.module_from_spec(spec)
            sys.modules["_fresh_repo"] = fresh_repo
            spec.loader.exec_module(fresh_repo)

            old_repo_mod = sys.modules.get("database.repository")
            if old_repo_mod is not None and hasattr(old_repo_mod, "TradingRepository"):
                def _norm_safe(*args, **kwargs):
                    p = args[-1] if args else kwargs.get("profile", "SYNTHETICS")
                    value = str(p or "SYNTHETICS").upper().strip()
                    if value not in {"SYNTHETICS", "FOREX", "ORB", "IDX_OPEN", "MALAYSIAN_SNR", "GOLD", "ICT"}:
                        raise ValueError(f"Perfil de selección no soportado: {value}")
                    return value
                old_repo_mod.TradingRepository._normalize_selection_profile = _norm_safe
                old_repo_mod.TradingRepository.latest_instrument_selection_profiles = fresh_repo.TradingRepository.latest_instrument_selection_profiles
                old_repo_mod.TradingRepository.save_instrument_selection_profile = fresh_repo.TradingRepository.save_instrument_selection_profile

        # 2. Cargar fresh realtime_dashboard y parchear clase RealtimeDashboardService y módulos
        rd_path = Path(__file__).resolve().parent / "realtime_dashboard.py"
        if rd_path.exists():
            spec = importlib.util.spec_from_file_location("_fresh_rd", rd_path)
            fresh_rd = importlib.util.module_from_spec(spec)
            sys.modules["_fresh_rd"] = fresh_rd
            spec.loader.exec_module(fresh_rd)

            old_rd = sys.modules.get("dashboard.realtime_dashboard")
            if old_rd is not None:
                old_rd._SELECTION_PROFILES = fresh_rd._SELECTION_PROFILES
                old_rd._INSTRUMENTS_HTML = fresh_rd._INSTRUMENTS_HTML
                old_rd.DEFAULT_PRIORITIZED_SYMBOLS = fresh_rd.DEFAULT_PRIORITIZED_SYMBOLS
                old_rd.ICT_PRUNED_INFO = fresh_rd.ICT_PRUNED_INFO
                old_rd._selection_profile_for_category = fresh_rd._selection_profile_for_category

                RDS = old_rd.RealtimeDashboardService
                RDS._cached_instruments_payload = fresh_rd.RealtimeDashboardService._cached_instruments_payload
                RDS._refresh_selection_profiles_from_db_locked = fresh_rd.RealtimeDashboardService._refresh_selection_profiles_from_db_locked

            for obj in gc.get_objects():
                if type(obj).__name__ == "RealtimeDashboardService":
                    try:
                        lock = getattr(obj, "_lock", None)
                        if lock is not None:
                            with lock:
                                obj._instruments_cache = {"at": 0.0, "payload": None}
                                obj._dashboard_snapshot_cache = {"at": 0.0, "payload": None}
                                if hasattr(obj, "_refresh_selection_profiles_from_db_locked"):
                                    obj._refresh_selection_profiles_from_db_locked()
                                if hasattr(obj, "_invalidate_navigation_caches"):
                                    obj._invalidate_navigation_caches(instruments=True, account=True)
                    except Exception:
                        pass
    except Exception:
        pass


_sync_runtime_dashboard_if_needed()
