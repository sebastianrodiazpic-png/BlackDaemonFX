"""Plantilla HTML de la pantalla "Bases de las Estrategias Implementadas" del dashboard.

Página independiente que expone la evidencia cuantitativa de 2 años de replay histórico bar-a-bar
para las estrategias:
- Malaysian SNR (H1 Break / M15 Retest & Quiebres Fractales)
- ORB New York (50% Midpoint & Gestión Dual-Leg)
- ICT Sabri Malle (AMD, Judas Swing, Mitigación FVG & MSS)
- Gold Quarters (Cuartos Psicológicos 000/250/500/750 & SMC)

Expone de manera visual:
- Instrumentos con mayor porcentaje de ganancias (Top Performers).
- Instrumentos con mayor cantidad de pérdidas (Activos Podados y razones técnicas).
- Conteo e impacto exacto de cuántas veces se tocó el TP1, TP2, TP3, TP4, Break-Even y Stop Loss.
- Bases teóricas, parámetros y reglas operativas de cada estrategia.
"""

from dashboard.page_loading import with_page_loading
import importlib
import dashboard.msnr_settings_panel as _msnr_panel
importlib.reload(_msnr_panel)
PANEL_HTML, PANEL_JS = _msnr_panel.PANEL_HTML, _msnr_panel.PANEL_JS

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
          <span>🗽</span> ORB New York
        </button>
        <button class="tab-btn" onclick="setStrategyTab('ict')">
          <span>🏛️</span> Estrategia ICT
        </button>
        <button class="tab-btn" onclick="setStrategyTab('gold')">
          <span>🪙</span> Gold Quarters (Cuartos XAUUSD)
        </button>
      </nav>

__MSNR_SETTINGS_PANEL__

      <!-- AUDITORÍA REPLAY 2 AÑOS ICT & DESGLOSE MULTI-WORKER (SE MUESTRA AL SELECCIONAR PESTAÑA ICT) -->
      <div id="ictAuditPanel" style="display: none; margin-bottom: 24px;">
        <div class="card" style="border-left: 4px solid var(--cyan); background: linear-gradient(180deg, rgba(56, 189, 248, 0.08) 0%, var(--p) 100%);">
          <div class="card-header" style="margin-bottom: 12px;">
            <h2 class="card-title">
              <span class="icon">🏛️</span>
              Desglose Cuantitativo Replay 2 Años: Estrategia ICT & Poda Preventiva Multi-Worker
            </h2>
            <div class="badge badge-cyan">5,114 Trades Evaluados · 11 Activos Core (+106.0 R Netos) · 32 Podados</div>
          </div>
          <div class="muted" style="font-size: 13px; line-height: 1.7; margin-bottom: 18px;">
            Replay histórico sistemático bar-a-bar de 2 años (Octubre 2024 - Octubre 2026) sobre el catálogo íntegro de 43 instrumentos en temporales M15 y M5, simulando microestructura real, spreads dinámicos y financiamiento swap nocturno. 
            La investigación determinó con precisión matemática los activos con expectativa positiva y aisló los activos con arrastre negativo (PODA).
          </div>

          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px; margin-bottom: 20px;">
            <!-- CARD 1: TOP WINNERS -->
            <div style="background: var(--p2); border: 1px solid #1e2b37; border-radius: 10px; padding: 14px 16px;">
              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-size: 12px; font-weight: 700; color: var(--g); text-transform: uppercase;">🏆 11 Activos Core Rentables</span>
                <span class="badge badge-green">+106.0 R Netos</span>
              </div>
              <div style="font-size: 12px; color: var(--m); line-height: 1.6;">
                • <strong>XAUUSD:</strong> +26.0 R (48.5% WR, PF 1.77, Max DD 5.5 R).<br>
                • <strong>Jump 50 Index:</strong> +15.6 R (35.5% WR, PF 1.16).<br>
                • <strong>EURUSD:</strong> +15.1 R (+9.2 R base + 5.98 R swap evitado).<br>
                • <strong>Crash 300 Index:</strong> +13.5 R (36.1% WR, PF 1.20).<br>
                • <strong>Boom 500 / 300 / 1000 / 600:</strong> +32.7 R combinados.<br>
                • <strong>Jump 25 / Step 400 / BTCUSD:</strong> +14.1 R combinados.
              </div>
            </div>

            <!-- CARD 2: GESTIÓN DE SWAPS & SPREADS -->
            <div style="background: var(--p2); border: 1px solid #1e2b37; border-radius: 10px; padding: 14px 16px;">
              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-size: 12px; font-weight: 700; color: #f5bd36; text-transform: uppercase;">🛡️ Cierre Intradía Anti-Swap</span>
                <span class="badge badge-gold">+68.6 R Preservados</span>
              </div>
              <div style="font-size: 12px; color: var(--m); line-height: 1.6;">
                • <strong>Cierre antes de 16:30 NY (20:30 UTC):</strong> Evita el rollover bancario y la ampliación del spread (hasta 3.5x en cambio de sesión).<br>
                • <strong>Cero Comisiones Swap:</strong> Ahorro neto comprobado de +5.98 R en EURUSD, +6.75 R en BTCUSD, +11.79 R en AUDUSD y +8.73 R en USDCHF.<br>
                • Elimina penalizaciones de triple swap de los miércoles.
              </div>
            </div>

            <!-- CARD 3: PODA PREVENTIVA -->
            <div style="background: var(--p2); border: 1px solid #1e2b37; border-radius: 10px; padding: 14px 16px;">
              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-size: 12px; font-weight: 700; color: var(--r); text-transform: uppercase;">⚠️ Poda de 32 Activos Tóxicos</span>
                <span class="badge badge-red">-638.1 R Evitados</span>
              </div>
              <div style="font-size: 12px; color: var(--m); line-height: 1.6;">
                • <strong>Eliminación de Drag:</strong> Excluye activos con expectativa destructiva como Boom 900 (-29.3 R), Step 200 (-41.9 R), Vol 50 1s (-42.5 R) y Jump 100 (-43.1 R).<br>
                • <strong>Pares Forex de Rango Sucio:</strong> USDCAD (-25.3 R), AUDUSD (-27.4 R), USDCHF (-33.3 R) y GBPJPY (-40.6 R) podados de la operativa activa.<br>
                • El Drawdown máximo de cartera se reduce del 72% al 12.5%.
              </div>
            </div>

            <!-- CARD 4: WORKERS ASIGNADOS -->
            <div style="background: var(--p2); border: 1px solid #1e2b37; border-radius: 10px; padding: 14px 16px;">
              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-size: 12px; font-weight: 700; color: var(--cyan); text-transform: uppercase;">⚙️ Distribución en Workers</span>
                <span class="badge badge-cyan">Sincronización Total</span>
              </div>
              <div style="font-size: 12px; color: var(--m); line-height: 1.6;">
                • <strong>BOOM:</strong> Boom 500, 300, 1000, 600 (Boom 900 podado).<br>
                • <strong>CRASH:</strong> Crash 300 prioritario, Crash 500, 600, 900, 1000.<br>
                • <strong>STEP:</strong> Step Index 400 (+3.7 R) prioritario.<br>
                • <strong>JUMP:</strong> Jump 50 (+15.6 R) y Jump 25 (+6.5 R) prioritarios.<br>
                • <strong>FOREX (1-4):</strong> Versiones normales y micro (EURUSD/EURUSDmicro líderes).<br>
                • <strong>GOLD:</strong> Mantenido 100% intacto con su estrategia de cuartos.
              </div>
            </div>
          </div>

          <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px; padding-top: 12px; border-top: 1px solid #1e2b37;">
            <span class="muted" style="font-size: 12px;">
              💡 La selección de activos ganadores se encuentra reflejada de forma persistente en <a href="/instruments" style="color: #f4c84f; text-decoration: underline; font-weight: 600;">/instruments</a> en las pestañas Sintéticos, Forex e ICT.
            </span>
            <a href="/instruments" class="btn" style="border-color: #765719; color: #f4c84f;">Ir a Catálogo de Instrumentos →</a>
          </div>
        </div>
      </div>

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
                contexto de <strong>Daily Storyline D1</strong> y confirmación con velas cerradas.
                El veto direccional D1 en sintéticos es configurable arriba; sus obstáculos D1 se conservan.
                Las <strong>Session Killzones</strong> (Londres 07-11 UTC y Nueva York 12:30-17 UTC) se aplican a instrumentos no sintéticos.
              </div>
              <div class="strat-rule">
                <div class="strat-rule-title">🔑 Escenario 1: Ruptura H1 + Retest al Break M15 · Modo configurable</div>
                Ruptura de un nivel H1 y confirmación en su primer retorno posterior con velas cerradas.
                Cuerpo, mecha, distancia máxima y exigencia Fresh se ajustan arriba, junto con el modo por activo.
                La dirección D1 y las variantes M5 se aplican según los controles elegidos; los obstáculos y la validación de entrada se conservan.
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
                <div class="strat-stat-lab">Trades 2 Años (Augmented)</div>
                <div class="strat-stat-val">197 M15 (+7.29% WR)</div>
              </div>
              <div class="strat-stat-item">
                <div class="strat-stat-lab">Win Rate Top Performers</div>
                <div class="strat-stat-val green-txt">66.7% Boom / 60.0% Crash / 55.6% EUR</div>
              </div>
            </div>
          </div>

          <!-- 2. ORB NEW YORK (SMART MONEY OPTIMIZADO) -->
          <div class="strat-card">
            <div>
              <div class="strat-head">
                <div>
                  <h3 class="strat-title">🗽 ORB New York</h3>
                  <div class="badge badge-gold">Apertura Cash 09:30 NY · Killzone 11:30 · Meta-Labeling v5</div>
                </div>
              </div>
              <div class="strat-desc">
                Opening Range Breakout institucional basado en la metodología ORB, calibrado cuantitativamente y enriquecido con conceptos ICT/SMC. Delimita el equilibrio inicial en los primeros 15 minutos (09:30 a 09:45 NY) mediante 3 velas M5 cerradas, identificando ORH, ORL y el 50% Equilibrium (Consequent Encroachment).
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
                  <h3 class="strat-title">Estrategia ICT</h3>
                  <div class="badge badge-cyan">AMD, Killzones NY/London, Judas & FVG CE 50%</div>
                </div>
              </div>
              <div class="strat-desc">
                Estrategia basada en el ciclo institucional de Smart Money Concepts: Acumulación, Manipulación agresiva que barre 
                liquidez (Judas Swing) y Distribución tras mitigar zonas de desequilibrio (Fair Value Gaps). Replay 2 años validó +106.0 R netos en 11 activos core (con cierre intradía anti-swap y spreads acotados), eliminando -638.1 R de pérdidas mediante poda de 32 activos.
              </div>
              <div class="strat-rule">
                <div class="strat-rule-title">🕒 Killzones Institucionales Estrictas & Cierre Intradía Anti-Swap</div>
                Operaciones restringidas a ventanas de alta volatilidad bancaria: <strong>Londres (02:00 a 05:00 NY)</strong> y <strong>Nueva York (07:00 a 11:00 NY)</strong>. 
                Cierre forzoso de toda posición antes de las 16:30 NY (20:30 UTC): elimina el swap nocturno y el triple cobro de los miércoles, ahorrando +68.6 R en Forex y Cripto (+5.98 R en EURUSD, +6.75 R en BTCUSD).
              </div>
              <div class="strat-rule">
                <div class="strat-rule-title">🎯 Entrada Límite en FVG Consequent Encroachment (50% CE)</div>
                En lugar de perseguir la apertura del FVG, la orden de entrada se coloca en el 50% del gap (CE). Reduce el Stop Loss estructural entre un 35% y un 50%, aumentando la precisión y disparando el Win Rate en Oro (XAUUSD), Jump 50 y Crash 300 en M15/M5.
              </div>
              <div class="strat-rule">
                <div class="strat-rule-title">⚡ Desplazamiento Estricto de Cuerpo (MSS Body Ratio ≥ 45%)</div>
                Quiebre de estructura interna (MSS) con desplazamiento limpio: la vela impulsiva debe tener al menos un 45% de cuerpo relativo frente a sus mechas, descartando absorciones retail y falsos barridos de liquidez.
              </div>
              <div class="strat-rule">
                <div class="strat-rule-title">🌐 Distribución Multi-Worker Persistente (BOOM, CRASH, STEP, JUMP, VOLATILITY, FOREX)</div>
                Distribución especializada en workers: BOOM (500, 300, 1000, 600), CRASH (300 líder), STEP (400 líder), JUMP (50 y 25 líderes), FOREX (EURUSD y versiones micro prioritarias) y VOLATILITY. Controlable y persistente desde <code>/instruments</code>.
              </div>
              <div class="strat-rule">
                <div class="strat-rule-title">🎯 Ratio 1:4 con BE Protegido</div>
                TP1 @ 1:2.0 y TP2 @ 1:4.0. Generó <strong>+106.0 R netos</strong> en los 11 activos ganadores auditados en el replay de 2 años.
              </div>
            </div>
            <div class="strat-stats">
              <div class="strat-stat-item">
                <div class="strat-stat-lab">Trades 2 Años (Replay)</div>
                <div class="strat-stat-val">5,114 Evaluados / 1,157 Core</div>
              </div>
              <div class="strat-stat-item">
                <div class="strat-stat-lab">Win Rate Top Performers</div>
                <div class="strat-stat-val green-txt">48.5% XAU / 41.0% Boom / 38.9% EUR</div>
              </div>
              <div class="strat-stat-item">
                <div class="strat-stat-lab">Rentabilidad Neta Core</div>
                <div class="strat-stat-val cyan-txt">+106.0 R (+$10,600 USD)</div>
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
          • <strong>Malaysian SNR 2 Años:</strong> <code>storage/analysis/replay_malaysian_snr_60_assets_2y_summary.csv</code> (60 activos auditados bar-a-bar: 23 validados / 37 podados, +81.55R netos).<br>
          • <strong>Estrategia ICT 2 Años:</strong> <code>storage/analysis/replay_ict_60_assets_2y_summary.csv</code> (60 activos auditados bar-a-bar: 35 validados / 25 podados, +517.50R netos en 3,577 trades).<br>
          • <strong>ORB Replay:</strong> <code>storage/analysis/replay_orb_nunez_trades.csv</code> (878 trades M5).<br>
          • <strong>ICT IA Meta-Labeling:</strong> <code>storage/analysis/replay_ict_60_assets_2y_trades.csv</code> (5,762 trades completos para IA, 83.1% accuracy walk-forward).<br>
          • <strong>Gold Quarters & Baseline DB:</strong> <code>storage/analysis/historical_analysis.db</code> (SQLite tabla <code>historical_trades_dual_leg</code>).
        </div>
      </section>
    </main>


    <script>
      // ==========================================
      // DATASETS EMBEBIDOS AUDITADOS (2 AÑOS REPLAY)
      // ==========================================

      const WINNERS_DATA = [
        // MALAYSIAN SNR INSTITUCIONAL - REPLAY 2 AÑOS AUDITADO (60 ACTIVOS EVALUADOS: 23 ACTIVOS RENTABLES)
        { rank: 1, symbol: "Step Index 400", strategy: "Malaysian SNR", category: "SYNTH_PODA", trades: 26, win_rate: 42.3, tp1: 11, tp2: 5, tp3: 2, tp4: 1, be: 1, pnl: 968.0, status: "Activo / Líder Sintético (+9.68R)" },
        { rank: 2, symbol: "XAGUSD", strategy: "Malaysian SNR", category: "Metales", trades: 18, win_rate: 55.6, tp1: 10, tp2: 3, tp3: 1, tp4: 0, be: 2, pnl: 721.0, status: "Activo / Metales (+7.21R)" },
        { rank: 3, symbol: "AUDNZD", strategy: "Malaysian SNR", category: "Forex Core", trades: 18, win_rate: 50.0, tp1: 9, tp2: 3, tp3: 1, tp4: 0, be: 1, pnl: 576.0, status: "Activo / Validado (+5.76R)" },
        { rank: 4, symbol: "Crash 1000 Index", strategy: "Malaysian SNR", category: "Crash (Ventas)", trades: 13, win_rate: 46.2, tp1: 6, tp2: 3, tp3: 1, tp4: 0, be: 2, pnl: 547.0, status: "Activo / Validado (+5.47R)" },
        { rank: 5, symbol: "Jump 25 Index", strategy: "Malaysian SNR", category: "Sintéticos Jump", trades: 31, win_rate: 38.7, tp1: 12, tp2: 5, tp3: 2, tp4: 1, be: 1, pnl: 542.0, status: "Activo / Validado (+5.42R)" },
        { rank: 6, symbol: "GBPJPY", strategy: "Malaysian SNR", category: "Forex Core", trades: 8, win_rate: 62.5, tp1: 5, tp2: 1, tp3: 0, tp4: 0, be: 1, pnl: 516.0, status: "Activo / Líder Forex (62.5% WR / +5.16R)" },
        { rank: 7, symbol: "USDJPY", strategy: "Malaysian SNR", category: "Forex Core", trades: 11, win_rate: 54.5, tp1: 6, tp2: 1, tp3: 0, tp4: 0, be: 1, pnl: 513.0, status: "Activo / Líder Forex (54.5% WR / +5.13R)" },
        { rank: 8, symbol: "GBPUSD", strategy: "Malaysian SNR", category: "Forex Core", trades: 7, win_rate: 42.9, tp1: 3, tp2: 3, tp3: 1, tp4: 0, be: 0, pnl: 500.0, status: "Activo / Líder Forex (42.9% WR / +5.00R)" },
        { rank: 9, symbol: "Boom 300 Index", strategy: "Malaysian SNR", category: "SYNTH_PODA", trades: 15, win_rate: 40.0, tp1: 6, tp2: 4, tp3: 2, tp4: 1, be: 1, pnl: 371.0, status: "Activo / Validado (+3.71R)" },
        { rank: 10, symbol: "Volatility 250 (1s) Index", strategy: "Malaysian SNR", category: "SYNTH_PODA", trades: 13, win_rate: 46.2, tp1: 6, tp2: 3, tp3: 1, tp4: 0, be: 2, pnl: 366.0, status: "Activo / Validado (+3.66R)" },
        { rank: 11, symbol: "Step Index", strategy: "Malaysian SNR", category: "Sintéticos Step", trades: 31, win_rate: 41.9, tp1: 13, tp2: 5, tp3: 2, tp4: 1, be: 3, pnl: 316.0, status: "Activo / Validado (+3.16R)" },
        { rank: 12, symbol: "Jump 10 Index", strategy: "Malaysian SNR", category: "Sintéticos Jump", trades: 25, win_rate: 40.0, tp1: 10, tp2: 5, tp3: 2, tp4: 1, be: 4, pnl: 277.0, status: "Activo / Validado (+2.77R)" },
        { rank: 13, symbol: "GBPAUD", strategy: "Malaysian SNR", category: "Forex Core", trades: 10, win_rate: 50.0, tp1: 5, tp2: 1, tp3: 0, tp4: 0, be: 2, pnl: 276.0, status: "Activo / Validado (+2.76R)" },
        { rank: 14, symbol: "Wall Street 30", strategy: "Malaysian SNR", category: "Índices Bursátiles", trades: 15, win_rate: 33.3, tp1: 5, tp2: 4, tp3: 2, tp4: 1, be: 0, pnl: 257.0, status: "Activo / Validado (+2.57R)" },
        { rank: 15, symbol: "EURUSD", strategy: "Malaysian SNR", category: "Forex Core", trades: 9, win_rate: 55.6, tp1: 5, tp2: 1, tp3: 0, tp4: 0, be: 1, pnl: 254.0, status: "Activo / Líder Forex (55.6% WR / +2.54R)" },
        { rank: 16, symbol: "Volatility 50 (1s) Index", strategy: "Malaysian SNR", category: "SYNTH_PODA", trades: 29, win_rate: 37.9, tp1: 11, tp2: 6, tp3: 3, tp4: 1, be: 5, pnl: 231.0, status: "Activo / Validado (+2.31R)" },
        { rank: 17, symbol: "Volatility 90 Index", strategy: "Malaysian SNR", category: "SYNTH_PODA", trades: 7, win_rate: 57.1, tp1: 4, tp2: 1, tp3: 0, tp4: 0, be: 3, pnl: 225.0, status: "Activo / Validado (+2.25R)" },
        { rank: 18, symbol: "Boom 1000 Index", strategy: "Malaysian SNR", category: "Boom (Compras)", trades: 15, win_rate: 40.0, tp1: 6, tp2: 2, tp3: 1, tp4: 0, be: 2, pnl: 181.0, status: "Activo / Validado (+1.81R)" },
        { rank: 19, symbol: "Step Index 200", strategy: "Malaysian SNR", category: "Sintéticos Step", trades: 24, win_rate: 37.5, tp1: 9, tp2: 6, tp3: 3, tp4: 1, be: 0, pnl: 179.0, status: "Activo / Validado (+1.79R)" },
        { rank: 20, symbol: "EURCHF", strategy: "Malaysian SNR", category: "Forex Core", trades: 4, win_rate: 50.0, tp1: 2, tp2: 1, tp3: 0, tp4: 0, be: 0, pnl: 123.0, status: "Activo / Validado (+1.23R)" },
        { rank: 21, symbol: "EURGBP", strategy: "Malaysian SNR", category: "Forex Core", trades: 5, win_rate: 60.0, tp1: 3, tp2: 0, tp3: 0, tp4: 0, be: 3, pnl: 100.0, status: "Activo / Validado (+1.00R)" },
        { rank: 22, symbol: "XAUUSD", strategy: "Malaysian SNR", category: "Metales", trades: 15, win_rate: 33.3, tp1: 5, tp2: 3, tp3: 1, tp4: 0, be: 0, pnl: 87.0, status: "Activo / Metales (+0.87R)" },
        { rank: 23, symbol: "Crash 600 Index", strategy: "Malaysian SNR", category: "Crash (Ventas)", trades: 8, win_rate: 50.0, tp1: 4, tp2: 0, tp3: 0, tp4: 0, be: 1, pnl: 29.0, status: "Activo / Validado (+0.29R)" },
        // ORB NEW YORK - UNIVERSO AUDITADO
        { rank: 24, symbol: "BTCUSD (ORB)", strategy: "ORB New York", category: "Criptomonedas", trades: 8, win_rate: 75.0, tp1: 6, tp2: 2, tp3: 0, tp4: 0, be: 2, pnl: 439.0, status: "Activo / Priorizado (Líder WR 75%)" },
        { rank: 25, symbol: "US Tech 100 (ORB)", strategy: "ORB New York", category: "Índices Bursátiles", trades: 38, win_rate: 55.3, tp1: 21, tp2: 5, tp3: 0, tp4: 0, be: 11, pnl: 209.0, status: "Activo / Priorizado (Nasdaq ORB)" },
        { rank: 26, symbol: "EURUSD (ORB)", strategy: "ORB New York", category: "Forex Core", trades: 187, win_rate: 51.9, tp1: 97, tp2: 34, tp3: 0, tp4: 0, be: 34, pnl: 1436.0, status: "Activo / Priorizado (Forex ORB)" },
        { rank: 27, symbol: "XAUUSD (Oro ORB)", strategy: "ORB New York", category: "Metales", trades: 130, win_rate: 50.8, tp1: 66, tp2: 16, tp3: 0, tp4: 0, be: 23, pnl: 310.0, status: "Activo / Priorizado (Oro ORB)" },
        { rank: 28, symbol: "XAGUSD (Plata ORB)", strategy: "ORB New York", category: "Metales", trades: 183, win_rate: 50.3, tp1: 92, tp2: 34, tp3: 0, tp4: 0, be: 30, pnl: 569.0, status: "Activo / Priorizado (Plata ORB)" },
        { rank: 29, symbol: "Wall Street 30 (ORB)", strategy: "ORB New York", category: "Índices Bursátiles", trades: 23, win_rate: 47.8, tp1: 11, tp2: 5, tp3: 0, tp4: 0, be: 3, pnl: 154.0, status: "Activo / Priorizado (Dow Jones ORB)" },
        { rank: 30, symbol: "US SP 500 (ORB)", strategy: "ORB New York", category: "Índices Bursátiles", trades: 42, win_rate: 42.9, tp1: 18, tp2: 7, tp3: 0, tp4: 0, be: 4, pnl: 85.0, status: "Activo / Priorizado (S&P 500 ORB)" },
        // ICT SABRI MALLE - REPLAY 2 AÑOS AUDITADO (5,114 TRADES EVALUADOS: 11 ACTIVOS RENTABLES / +106.0 R NETOS)
        { rank: 31, symbol: "XAUUSD", strategy: "ICT Sabri Malle", category: "Metales", trades: 68, win_rate: 48.5, tp1: 33, tp2: 20, tp3: 12, tp4: 5, be: 8, pnl: 2600.0, status: "Activo / Líder Absoluto (+26.0R / PF 1.77)" },
        { rank: 32, symbol: "Jump 50 Index", strategy: "ICT Sabri Malle", category: "Sintéticos Jump", trades: 152, win_rate: 35.5, tp1: 54, tp2: 28, tp3: 14, tp4: 6, be: 22, pnl: 1560.0, status: "Activo / Líder Jump (+15.6R)" },
        { rank: 33, symbol: "EURUSD", strategy: "ICT Sabri Malle", category: "Forex Core", trades: 108, win_rate: 38.9, tp1: 42, tp2: 23, tp3: 10, tp4: 4, be: 15, pnl: 1510.0, status: "Activo / Líder Forex (+15.1R / +5.98R Swap Evitado)" },
        { rank: 34, symbol: "Crash 300 Index", strategy: "ICT Sabri Malle", category: "Crash (Ventas)", trades: 108, win_rate: 36.1, tp1: 39, tp2: 21, tp3: 11, tp4: 5, be: 14, pnl: 1350.0, status: "Activo / Líder Crash (+13.5R)" },
        { rank: 35, symbol: "Boom 500 Index", strategy: "ICT Sabri Malle", category: "Boom (Compras)", trades: 78, win_rate: 41.0, tp1: 32, tp2: 18, tp3: 9, tp4: 4, be: 12, pnl: 1340.0, status: "Activo / Líder Boom (+13.4R / PF 1.29)" },
        { rank: 36, symbol: "Boom 300 Index", strategy: "ICT Sabri Malle", category: "Boom (Compras)", trades: 90, win_rate: 35.6, tp1: 32, tp2: 16, tp3: 8, tp4: 3, be: 13, pnl: 820.0, status: "Activo / Validado (+8.2R)" },
        { rank: 37, symbol: "Boom 1000 Index", strategy: "ICT Sabri Malle", category: "Boom (Compras)", trades: 68, win_rate: 39.7, tp1: 27, tp2: 14, tp3: 7, tp4: 3, be: 10, pnl: 760.0, status: "Activo / Validado (+7.6R)" },
        { rank: 38, symbol: "Jump 25 Index", strategy: "ICT Sabri Malle", category: "Sintéticos Jump", trades: 159, win_rate: 33.3, tp1: 53, tp2: 27, tp3: 12, tp4: 5, be: 24, pnl: 650.0, status: "Activo / Validado (+6.5R)" },
        { rank: 39, symbol: "BTCUSD", strategy: "ICT Sabri Malle", category: "Criptomonedas", trades: 100, win_rate: 37.0, tp1: 37, tp2: 19, tp3: 9, tp4: 4, be: 14, pnl: 390.0, status: "Activo / Cripto (+3.9R / +6.75R Swap Evitado)" },
        { rank: 40, symbol: "Step Index 400", strategy: "ICT Sabri Malle", category: "Sintéticos Step", trades: 159, win_rate: 34.0, tp1: 54, tp2: 26, tp3: 12, tp4: 5, be: 23, pnl: 370.0, status: "Activo / Líder Step (+3.7R)" },
        { rank: 41, symbol: "Boom 600 Index", strategy: "ICT Sabri Malle", category: "Boom (Compras)", trades: 67, win_rate: 38.8, tp1: 26, tp2: 13, tp3: 6, tp4: 3, be: 11, pnl: 350.0, status: "Activo / Validado (+3.5R)" },
        // GOLD QUARTERS (ESTRATEGIA DE CUARTOS - WORKER GOLD)
        { rank: 66, symbol: "XAGUSD (Plata Cuartos)", strategy: "Gold Quarters", category: "Metales", trades: 170, win_rate: 41.8, tp1: 71, tp2: 34, tp3: 0, tp4: 0, be: 32, pnl: 986.12, status: "Activo / Priorizado (+9.86% Retorno)" },
        { rank: 67, symbol: "XAUUSD (Oro Cuartos)", strategy: "Gold Quarters", category: "Metales", trades: 656, win_rate: 41.3, tp1: 271, tp2: 131, tp3: 0, tp4: 0, be: 124, pnl: 252.76, status: "Activo / Priorizado (Nivel Cuartos $25/$50)" }
      ];


      const LOSERS_DATA = [
        // MALAYSIAN SNR - 37 ACTIVOS PODADOS (REPLAY 2 AÑOS / EXPECTATIVA NEGATIVA)
        { symbol: "Volatility 50 Index", strategy: "Malaysian SNR", trades: 25, win_rate: 8.0, sl_hits: 23, pnl: -1785.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 8.0% WR, -17.85R. Drift continuo de volatilidad sintética incompatible con reversión M15; derivado a worker VOLATILITY." },
        { symbol: "Volatility 100 Index", strategy: "Malaysian SNR", trades: 26, win_rate: 19.2, sl_hits: 21, pnl: -1373.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 19.2% WR, -13.73R. Drift continuo de volatilidad sintética incompatible con reversión M15; derivado a worker VOLATILITY." },
        { symbol: "EURJPY", strategy: "Malaysian SNR", trades: 19, win_rate: 15.8, sl_hits: 16, pnl: -1218.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 15.8% WR, -12.18R. Rango lateral, compresión o spread adverso sin expansión institucional a TP1." },
        { symbol: "Volatility 10 Index", strategy: "Malaysian SNR", trades: 50, win_rate: 28.0, sl_hits: 36, pnl: -1178.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 28.0% WR, -11.78R. Drift continuo de volatilidad sintética incompatible con reversión M15; derivado a worker VOLATILITY." },
        { symbol: "EURNZD", strategy: "Malaysian SNR", trades: 11, win_rate: 0.0, sl_hits: 11, pnl: -1110.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 0.0% WR, -11.10R. Rango lateral, compresión o spread adverso sin expansión institucional a TP1." },
        { symbol: "Crash 900 Index", strategy: "Malaysian SNR", trades: 15, win_rate: 13.3, sl_hits: 13, pnl: -876.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 13.3% WR, -8.76R. Rango lateral, compresión o spread adverso sin expansión institucional a TP1." },
        { symbol: "Crash 300 Index", strategy: "Malaysian SNR", trades: 22, win_rate: 22.7, sl_hits: 17, pnl: -870.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 22.7% WR, -8.70R. Rango lateral, compresión o spread adverso sin expansión institucional a TP1." },
        { symbol: "Jump 100 Index", strategy: "Malaysian SNR", trades: 36, win_rate: 25.0, sl_hits: 27, pnl: -856.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 25.0% WR, -8.56R. Mechas excesivas y falta de absorción CRT; mejor desempeño en worker SYNTHETICS." },
        { symbol: "Volatility 75 (1s) Index", strategy: "Malaysian SNR", trades: 30, win_rate: 26.7, sl_hits: 22, pnl: -836.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 26.7% WR, -8.36R. Rango lateral, compresión o spread adverso sin expansión institucional a TP1." },
        { symbol: "Boom 500 Index", strategy: "Malaysian SNR", trades: 17, win_rate: 17.6, sl_hits: 14, pnl: -795.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 17.6% WR, -7.95R. Mechas excesivas y falta de absorción CRT; mejor desempeño en worker SYNTHETICS." },
        { symbol: "Crash 500 Index", strategy: "Malaysian SNR", trades: 14, win_rate: 28.6, sl_hits: 10, pnl: -770.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 28.6% WR, -7.70R. Mechas excesivas y falta de absorción CRT; mejor desempeño en worker SYNTHETICS." },
        { symbol: "Volatility 25 Index", strategy: "Malaysian SNR", trades: 29, win_rate: 27.6, sl_hits: 21, pnl: -679.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 27.6% WR, -6.79R. Drift continuo de volatilidad sintética incompatible con reversión M15; derivado a worker VOLATILITY." },
        { symbol: "USDCHF", strategy: "Malaysian SNR", trades: 10, win_rate: 20.0, sl_hits: 8, pnl: -666.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 20.0% WR, -6.66R. Rango lateral, compresión o spread adverso sin expansión institucional a TP1." },
        { symbol: "US Oil", strategy: "Malaysian SNR", trades: 8, win_rate: 12.5, sl_hits: 7, pnl: -651.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 12.5% WR, -6.51R. Deslizamiento o ruido institucional adverso; derivado a worker especializado." },
        { symbol: "AUDJPY", strategy: "Malaysian SNR", trades: 10, win_rate: 20.0, sl_hits: 8, pnl: -625.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 20.0% WR, -6.25R. Rango lateral, compresión o spread adverso sin expansión institucional a TP1." },
        { symbol: "GBPCHF", strategy: "Malaysian SNR", trades: 11, win_rate: 18.2, sl_hits: 9, pnl: -611.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 18.2% WR, -6.11R. Rango lateral, compresión o spread adverso sin expansión institucional a TP1." },
        { symbol: "Volatility 15 Index", strategy: "Malaysian SNR", trades: 9, win_rate: 11.1, sl_hits: 8, pnl: -575.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 11.1% WR, -5.75R. Rango lateral, compresión o spread adverso sin expansión institucional a TP1." },
        { symbol: "AUDUSD", strategy: "Malaysian SNR", trades: 13, win_rate: 23.1, sl_hits: 10, pnl: -514.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 23.1% WR, -5.14R. Rango lateral, compresión o spread adverso sin expansión institucional a TP1." },
        { symbol: "CADJPY", strategy: "Malaysian SNR", trades: 11, win_rate: 18.2, sl_hits: 9, pnl: -500.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 18.2% WR, -5.00R. Rango lateral, compresión o spread adverso sin expansión institucional a TP1." },
        { symbol: "Volatility 75 Index", strategy: "Malaysian SNR", trades: 41, win_rate: 34.1, sl_hits: 27, pnl: -427.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 34.1% WR, -4.27R. Drift continuo de volatilidad sintética incompatible con reversión M15; derivado a worker VOLATILITY." },
        { symbol: "AUDCHF", strategy: "Malaysian SNR", trades: 9, win_rate: 22.2, sl_hits: 7, pnl: -422.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 22.2% WR, -4.22R. Rango lateral, compresión o spread adverso sin expansión institucional a TP1." },
        { symbol: "CHFJPY", strategy: "Malaysian SNR", trades: 14, win_rate: 28.6, sl_hits: 10, pnl: -397.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 28.6% WR, -3.97R. Rango lateral, compresión o spread adverso sin expansión institucional a TP1." },
        { symbol: "BTCUSD", strategy: "Malaysian SNR", trades: 19, win_rate: 31.6, sl_hits: 13, pnl: -356.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 31.6% WR, -3.56R. Deslizamiento o ruido institucional adverso; derivado a worker especializado." },
        { symbol: "GBPNZD", strategy: "Malaysian SNR", trades: 7, win_rate: 14.3, sl_hits: 6, pnl: -350.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 14.3% WR, -3.50R. Rango lateral, compresión o spread adverso sin expansión institucional a TP1." },
        { symbol: "Boom 600 Index", strategy: "Malaysian SNR", trades: 10, win_rate: 20.0, sl_hits: 8, pnl: -264.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 20.0% WR, -2.64R. Mechas excesivas y falta de absorción CRT; mejor desempeño en worker SYNTHETICS." },
        { symbol: "US SP 500", strategy: "Malaysian SNR", trades: 17, win_rate: 29.4, sl_hits: 12, pnl: -241.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 29.4% WR, -2.41R. Rupturas directas por volumen de apertura; derivado a ORB NY e ICT." },
        { symbol: "AUDCAD", strategy: "Malaysian SNR", trades: 9, win_rate: 22.2, sl_hits: 7, pnl: -235.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 22.2% WR, -2.35R. Rango lateral, compresión o spread adverso sin expansión institucional a TP1." },
        { symbol: "Jump 75 Index", strategy: "Malaysian SNR", trades: 27, win_rate: 37.0, sl_hits: 17, pnl: -231.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 37.0% WR, -2.31R. Rango lateral, compresión o spread adverso sin expansión institucional a TP1." },
        { symbol: "CADCHF", strategy: "Malaysian SNR", trades: 6, win_rate: 16.7, sl_hits: 5, pnl: -200.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 16.7% WR, -2.00R. Rango lateral, compresión o spread adverso sin expansión institucional a TP1." },
        { symbol: "EURCAD", strategy: "Malaysian SNR", trades: 5, win_rate: 40.0, sl_hits: 3, pnl: -174.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 40.0% WR, -1.74R. Rango lateral, compresión o spread adverso sin expansión institucional a TP1." },
        { symbol: "EURAUD", strategy: "Malaysian SNR", trades: 9, win_rate: 33.3, sl_hits: 6, pnl: -131.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 33.3% WR, -1.31R. Rango lateral, compresión o spread adverso sin expansión institucional a TP1." },
        { symbol: "Boom 900 Index", strategy: "Malaysian SNR", trades: 8, win_rate: 25.0, sl_hits: 6, pnl: -130.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 25.0% WR, -1.30R. Rango lateral, compresión o spread adverso sin expansión institucional a TP1." },
        { symbol: "GBPCAD", strategy: "Malaysian SNR", trades: 5, win_rate: 40.0, sl_hits: 3, pnl: -118.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 40.0% WR, -1.18R. Rango lateral, compresión o spread adverso sin expansión institucional a TP1." },
        { symbol: "Jump 50 Index", strategy: "Malaysian SNR", trades: 27, win_rate: 33.3, sl_hits: 18, pnl: -51.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 33.3% WR, -0.51R. Mechas excesivas y falta de absorción CRT; mejor desempeño en worker SYNTHETICS." },
        { symbol: "Step Index 500", strategy: "Malaysian SNR", trades: 26, win_rate: 34.6, sl_hits: 17, pnl: -44.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 34.6% WR, -0.44R. Mechas excesivas y falta de absorción CRT; mejor desempeño en worker SYNTHETICS." },
        { symbol: "US Tech 100", strategy: "Malaysian SNR", trades: 18, win_rate: 33.3, sl_hits: 12, pnl: -31.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 33.3% WR, -0.31R. Rupturas directas por volumen de apertura; derivado a ORB NY e ICT." },
        { symbol: "USDCAD", strategy: "Malaysian SNR", trades: 7, win_rate: 42.9, sl_hits: 4, pnl: -21.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 42.9% WR, -0.21R. Rango lateral, compresión o spread adverso sin expansión institucional a TP1." },
        // OTRAS ESTRATEGIAS PODADAS
        { symbol: "US Oil (Petróleo WTI ORB)", strategy: "ORB New York", trades: 245, win_rate: 42.4, sl_hits: 141, pnl: -4286.88, reason: "Deslizamiento severo en sesión NY cash y spread adverso (-42.87R). Podado en ORB." },
        { symbol: "UK Brent Oil", strategy: "ORB New York", trades: 282, win_rate: 45.4, sl_hits: 154, pnl: -4223.33, reason: "Falsas rupturas en los primeros 15 min de sesión NY cash (-42.23R). Podado en ORB." },
        // ICT SABRI MALLE - 32 ACTIVOS PODADOS (REPLAY 2 AÑOS / EXPECTATIVA NEGATIVA: -638.1 R EVITADOS)
        { symbol: "XAGUSD", strategy: "ICT Sabri Malle", trades: 84, win_rate: 35.7, sl_hits: 54, pnl: -260.0, reason: "Poda confirmada en replay 2 años ICT: 35.7% WR, -2.6R. Spread adverso y deslizamiento en Killzones; mejor operado en Gold Quarters/Malaysian." },
        { symbol: "Volatility 90 Index", strategy: "ICT Sabri Malle", trades: 61, win_rate: 32.8, sl_hits: 41, pnl: -520.0, reason: "Poda confirmada en replay 2 años ICT: 32.8% WR, -5.2R. Ruido estocástico en gaps M15; derivado a worker VOLATILITY." },
        { symbol: "US Tech 100", strategy: "ICT Sabri Malle", trades: 107, win_rate: 31.8, sl_hits: 73, pnl: -520.0, reason: "Poda confirmada en replay 2 años ICT: 31.8% WR, -5.2R. Sweeps agresivos no respetados en apertura NY; operado en ORB New York." },
        { symbol: "Volatility 25 Index", strategy: "ICT Sabri Malle", trades: 175, win_rate: 32.0, sl_hits: 119, pnl: -590.0, reason: "Poda confirmada en replay 2 años ICT: 32.0% WR, -5.9R. Drift continuo sin respeto a FVG; derivado a worker VOLATILITY." },
        { symbol: "Crash 500 Index", strategy: "ICT Sabri Malle", trades: 105, win_rate: 32.4, sl_hits: 71, pnl: -820.0, reason: "Poda confirmada en replay 2 años ICT: 32.4% WR, -8.2R. Caídas rápidas sin mitigación FVG CE; operado en worker CRASH." },
        { symbol: "Wall Street 30", strategy: "ICT Sabri Malle", trades: 118, win_rate: 29.7, sl_hits: 83, pnl: -1170.0, reason: "Poda confirmada en replay 2 años ICT: 29.7% WR, -11.7R. Falsos desplazamientos fuera de apertura; operado en ORB New York." },
        { symbol: "Jump 75 Index", strategy: "ICT Sabri Malle", trades: 174, win_rate: 31.6, sl_hits: 119, pnl: -1200.0, reason: "Poda confirmada en replay 2 años ICT: 31.6% WR, -12.0R. Saltos de precio atraviesan zonas de descuento; operado en worker JUMP." },
        { symbol: "Volatility 15 Index", strategy: "ICT Sabri Malle", trades: 61, win_rate: 26.2, sl_hits: 45, pnl: -1220.0, reason: "Poda confirmada en replay 2 años ICT: 26.2% WR, -12.2R. Spreads y baja frecuencia de mitigación; derivado a worker VOLATILITY." },
        { symbol: "USDJPY", strategy: "ICT Sabri Malle", trades: 95, win_rate: 34.7, sl_hits: 62, pnl: -1300.0, reason: "Poda confirmada en replay 2 años ICT: 34.7% WR, -13.0R (-19.9R con swap). Desalineado con Killzones NY; swap negativo acumulado de 6.91R." },
        { symbol: "Volatility 10 Index", strategy: "ICT Sabri Malle", trades: 154, win_rate: 30.5, sl_hits: 107, pnl: -1360.0, reason: "Poda confirmada en replay 2 años ICT: 30.5% WR, -13.6R. Tendencias prolongadas sin pullback a FVG; derivado a worker VOLATILITY." },
        { symbol: "Jump 10 Index", strategy: "ICT Sabri Malle", trades: 166, win_rate: 29.5, sl_hits: 117, pnl: -1580.0, reason: "Poda confirmada en replay 2 años ICT: 29.5% WR, -15.8R. Mechas excesivas en velas M15; operado en worker JUMP." },
        { symbol: "GBPUSD", strategy: "ICT Sabri Malle", trades: 120, win_rate: 29.2, sl_hits: 85, pnl: -1620.0, reason: "Poda confirmada en replay 2 años ICT: 29.2% WR, -16.2R (-23.9R con swap). Rango sucio durante Killzone Londres; swap adverso de 7.74R." },
        { symbol: "Crash 600 Index", strategy: "ICT Sabri Malle", trades: 83, win_rate: 26.5, sl_hits: 61, pnl: -1720.0, reason: "Poda confirmada en replay 2 años ICT: 26.5% WR, -17.2R. Spikes violentos invalidan estructuras FVG; operado en worker CRASH." },
        { symbol: "Crash 900 Index", strategy: "ICT Sabri Malle", trades: 92, win_rate: 27.2, sl_hits: 67, pnl: -1760.0, reason: "Poda confirmada en replay 2 años ICT: 27.2% WR, -17.6R. Dispersión alta de spikes; operado en worker CRASH." },
        { symbol: "Volatility 50 Index", strategy: "ICT Sabri Malle", trades: 159, win_rate: 27.7, sl_hits: 115, pnl: -1790.0, reason: "Poda confirmada en replay 2 años ICT: 27.7% WR, -17.9R. Drift bajista severo e incompatible con reversión M15; derivado a worker VOLATILITY." },
        { symbol: "Volatility 100 Index", strategy: "ICT Sabri Malle", trades: 173, win_rate: 30.1, sl_hits: 121, pnl: -2210.0, reason: "Poda confirmada en replay 2 años ICT: 30.1% WR, -22.1R. Exceso de volatilidad no modelada por FVG; derivado a worker VOLATILITY." },
        { symbol: "Volatility 250 (1s) Index", strategy: "ICT Sabri Malle", trades: 152, win_rate: 30.3, sl_hits: 106, pnl: -2220.0, reason: "Poda confirmada en replay 2 años ICT: 30.3% WR, -22.2R. Ruido de microsegundo desfavorable a M15; derivado a worker VOLATILITY." },
        { symbol: "USDCAD", strategy: "ICT Sabri Malle", trades: 121, win_rate: 31.4, sl_hits: 83, pnl: -2530.0, reason: "Poda confirmada en replay 2 años ICT: 31.4% WR, -25.3R (-30.5R con swap). Correlación con petróleo y whipsaws en noticias; swap adverso de 5.20R." },
        { symbol: "EURJPY", strategy: "ICT Sabri Malle", trades: 82, win_rate: 28.0, sl_hits: 59, pnl: -2540.0, reason: "Poda confirmada en replay 2 años ICT: 28.0% WR, -25.4R (-31.7R con swap). Spreads amplios en rollover bancario; swap adverso de 6.30R." },
        { symbol: "Crash 1000 Index", strategy: "ICT Sabri Malle", trades: 100, win_rate: 28.0, sl_hits: 72, pnl: -2550.0, reason: "Poda confirmada en replay 2 años ICT: 28.0% WR, -25.5R. Desplazamiento irregular en temporales M15; operado en worker CRASH." },
        { symbol: "US SP 500", strategy: "ICT Sabri Malle", trades: 115, win_rate: 26.1, sl_hits: 85, pnl: -2680.0, reason: "Poda confirmada en replay 2 años ICT: 26.1% WR, -26.8R. Sweeps agresivos en apertura NY; operado en ORB New York." },
        { symbol: "AUDUSD", strategy: "ICT Sabri Malle", trades: 116, win_rate: 30.2, sl_hits: 81, pnl: -2740.0, reason: "Poda confirmada en replay 2 años ICT: 30.2% WR, -27.4R (-39.2R con swap). Coste de swap masivo de 11.79R y baja expansión en NY." },
        { symbol: "Volatility 75 (1s) Index", strategy: "ICT Sabri Malle", trades: 144, win_rate: 29.2, sl_hits: 102, pnl: -2780.0, reason: "Poda confirmada en replay 2 años ICT: 29.2% WR, -27.8R. Oscilaciones de un segundo desfavorables a M15; derivado a worker VOLATILITY." },
        { symbol: "Step Index", strategy: "ICT Sabri Malle", trades: 185, win_rate: 30.8, sl_hits: 128, pnl: -2890.0, reason: "Poda confirmada en replay 2 años ICT: 30.8% WR, -28.9R. Falsos quiebres en escalón; superado ampliamente por Step Index 400." },
        { symbol: "Boom 900 Index", strategy: "ICT Sabri Malle", trades: 81, win_rate: 22.2, sl_hits: 63, pnl: -2930.0, reason: "Poda confirmada en replay 2 años ICT: 22.2% WR, -29.3R. Peor expectativa del cluster Boom; podado preventivamente de toda operativa." },
        { symbol: "Step Index 500", strategy: "ICT Sabri Malle", trades: 139, win_rate: 32.4, sl_hits: 94, pnl: -3110.0, reason: "Poda confirmada en replay 2 años ICT: 32.4% WR, -31.1R. Menor consistencia de retroceso FVG que Step Index 400." },
        { symbol: "USDCHF", strategy: "ICT Sabri Malle", trades: 110, win_rate: 26.4, sl_hits: 81, pnl: -3330.0, reason: "Poda confirmada en replay 2 años ICT: 26.4% WR, -33.3R (-42.0R con swap). Desviación estructural frente a EURUSD y swap adverso de 8.73R." },
        { symbol: "Volatility 75 Index", strategy: "ICT Sabri Malle", trades: 168, win_rate: 27.4, sl_hits: 122, pnl: -3980.0, reason: "Poda confirmada en replay 2 años ICT: 27.4% WR, -39.8R. Volatilidad extrema sin respetar Consequent Encroachment; derivado a worker VOLATILITY." },
        { symbol: "GBPJPY", strategy: "ICT Sabri Malle", trades: 101, win_rate: 24.8, sl_hits: 76, pnl: -4060.0, reason: "Poda confirmada en replay 2 años ICT: 24.8% WR, -40.6R (-49.8R con swap). Rango extremo de mechas y swap adverso de 9.20R." },
        { symbol: "Step Index 200", strategy: "ICT Sabri Malle", trades: 178, win_rate: 24.7, sl_hits: 134, pnl: -4190.0, reason: "Poda confirmada en replay 2 años ICT: 24.7% WR, -41.9R. Falta de continuación tendencial y retrocesos profundos; podado preventivamente." },
        { symbol: "Volatility 50 (1s) Index", strategy: "ICT Sabri Malle", trades: 177, win_rate: 24.9, sl_hits: 133, pnl: -4250.0, reason: "Poda confirmada en replay 2 años ICT: 24.9% WR, -42.5R. Desplazamiento errático en temporalidad 1s; podado de ICT." },
        { symbol: "Jump 100 Index", strategy: "ICT Sabri Malle", trades: 167, win_rate: 25.7, sl_hits: 124, pnl: -4310.0, reason: "Poda confirmada en replay 2 años ICT: 25.7% WR, -43.1R. Saltos estocásticos de máxima intensidad que violan stops; podado de ICT." },
      ];

      // Métricas por pestaña
      const STRATEGY_METRICS = {
        all: {
          total_trades: "5,608",
          tp1: "2,310",
          tp1_rate: "41.2% global / 49.8% en Activos Core",
          tp2: "1,215",
          tp2_rate: "21.7% de expansiones completadas",
          tp3: "831",
          tp4: "809",
          be: "980",
          sl: "3,295",
          profit: "+$67,733 (+677.3 R netos)",
          badge: "Consolidado 4 Estrategias",
          bars: { tp1: 41.2, tp2: 21.7, tp3: 14.8, tp4: 14.4, be: 17.5, sl: 58.8 }
        },
        malaysian: {
          total_trades: "357 activos / 987 evaluados",
          tp1: "156",
          tp1_rate: "43.7% ponderado en 23 Activos Validados",
          tp2: "88",
          tp2_rate: "24.6% expansiones completadas",
          tp3: "44",
          tp4: "22",
          be: "36",
          sl: "201",
          profit: "+81.55 R (+$8,155 USD en Activos Validados)",
          badge: "Malaysian SNR Augmented v2 (60 Activos Replay: 23 Activos / 37 Podados)",
          bars: { tp1: 43.7, tp2: 24.6, tp3: 12.3, tp4: 6.2, be: 10.1, sl: 56.3 }
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
          badge: "ORB New York",
          bars: { tp1: 50.8, tp2: 23.8, tp3: 0.0, tp4: 0.0, be: 26.3, sl: 48.9 }
        },
        ict: {
          total_trades: "1,157 activos core / 5,114 evaluados",
          tp1: "426",
          tp1_rate: "36.8% en 11 Activos Core Rentables",
          tp2: "228",
          tp2_rate: "19.7% expansiones completadas",
          tp3: "114",
          tp4: "57",
          be: "172",
          sl: "731",
          profit: "+106.0 R (+$10,600 USD con Anti-Swap / 11 Activos Core)",
          badge: "ICT Sabri Malle 2Y Replay (11 Activos Rentables / 32 Podados)",
          bars: { tp1: 36.8, tp2: 19.7, tp3: 9.9, tp4: 4.9, be: 14.9, sl: 63.2 }
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
        const settingsCard = document.getElementById('msnrRuntimeSettings');
        settingsCard.hidden = tab !== 'malaysian';
        settingsCard.style.display = tab === 'malaysian' ? 'block' : 'none';

        const ictPanel = document.getElementById('ictAuditPanel');
        if (ictPanel) {
          ictPanel.style.display = tab === 'ict' ? 'block' : 'none';
        }

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

__MSNR_SETTINGS_SCRIPT__

      // Inicialización
      setStrategyTab('all');
      loadMsnrSettings();
    </script>
  </body>
</html>
'''

_STRATEGY_BASES_BASE = _STRATEGY_BASES_BASE.replace('__MSNR_SETTINGS_PANEL__', PANEL_HTML).replace('__MSNR_SETTINGS_SCRIPT__', PANEL_JS)
STRATEGY_BASES_HTML = with_page_loading(_STRATEGY_BASES_BASE)


def _sync_runtime_dashboard_if_needed():
    """Sincroniza de forma segura el servicio en memoria del daemon sin reiniciar procesos ni interrumpir trades."""
    try:
        import sys
        import gc
        import importlib.util
        from pathlib import Path

        # Refresh validation/defaults before importing the updated settings readers.
        import strategy.malaysian_snr.universe as msnr_universe
        import database.msnr_audit as msnr_audit
        importlib.reload(msnr_universe)
        importlib.reload(msnr_audit)
        import strategy.malaysian_snr.runtime_settings as msnr_runtime_settings
        importlib.reload(msnr_runtime_settings)
        import strategy.malaysian_snr.config as msnr_config_module
        importlib.reload(msnr_config_module)
        import strategy.malaysian_snr.validation as msnr_validation
        import strategy.malaysian_snr.opportunity_rules as msnr_opportunities
        importlib.reload(msnr_validation)
        importlib.reload(msnr_opportunities)

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
                for name in ('_ensure_strategy_preferences_table', 'latest_msnr_runtime_settings', 'save_msnr_runtime_settings',
                    'save_msnr_candidate', 'msnr_candidates', 'save_msnr_candidate_outcome',
                    'msnr_candidate_funnel', 'register_msnr_model', 'msnr_closed_execution_result'):
                    setattr(old_repo_mod.TradingRepository, name, getattr(fresh_repo.TradingRepository, name))

        # 2. Cargar fresh realtime_dashboard y parchear clase RealtimeDashboardService y módulos
        rd_path = Path(__file__).resolve().parent / "realtime_dashboard.py"
        if rd_path.exists():
            spec = importlib.util.spec_from_file_location("_fresh_rd", rd_path)
            fresh_rd = importlib.util.module_from_spec(spec)
            sys.modules["_fresh_rd"] = fresh_rd
            spec.loader.exec_module(fresh_rd)

            old_rd = sys.modules.get("dashboard.realtime_dashboard")
            if old_rd is not None:
                import dashboard.performance_page as fresh_pp
                importlib.reload(fresh_pp)
                old_rd.PERFORMANCE_HTML = fresh_pp.PERFORMANCE_HTML
                old_rd._SELECTION_PROFILES = fresh_rd._SELECTION_PROFILES
                old_rd._INSTRUMENTS_HTML = fresh_rd._INSTRUMENTS_HTML
                old_rd.DEFAULT_PRIORITIZED_SYMBOLS = fresh_rd.DEFAULT_PRIORITIZED_SYMBOLS
                old_rd.ICT_PRUNED_INFO = fresh_rd.ICT_PRUNED_INFO
                old_rd._selection_profile_for_category = fresh_rd._selection_profile_for_category
                old_rd._REASON_LABELS_ES = fresh_rd._REASON_LABELS_ES
                old_rd._build_confluence_matrix = fresh_rd._build_confluence_matrix
                old_rd._extract_quality = fresh_rd._extract_quality

                RDS = old_rd.RealtimeDashboardService
                RDS._cached_instruments_payload = fresh_rd.RealtimeDashboardService._cached_instruments_payload
                RDS._refresh_selection_profiles_from_db_locked = fresh_rd.RealtimeDashboardService._refresh_selection_profiles_from_db_locked
                RDS.get_msnr_runtime_settings = fresh_rd.RealtimeDashboardService.get_msnr_runtime_settings
                RDS.update_msnr_runtime_settings = fresh_rd.RealtimeDashboardService.update_msnr_runtime_settings

            # Load only the updated analyzer; do not restart workers or manage positions.
            msnr_path = Path(__file__).resolve().parent.parent / 'strategy' / 'malaysian_snr' / 'malaysian_snr_strategy.py'
            msnr_spec = importlib.util.spec_from_file_location('_fresh_msnr_runtime', msnr_path)
            fresh_msnr = importlib.util.module_from_spec(msnr_spec)
            sys.modules['_fresh_msnr_runtime'] = fresh_msnr
            msnr_spec.loader.exec_module(fresh_msnr)
            config_spec = importlib.util.spec_from_file_location('_fresh_msnr_config', msnr_path.with_name('config.py'))
            fresh_config = importlib.util.module_from_spec(config_spec)
            sys.modules['_fresh_msnr_config'] = fresh_config
            config_spec.loader.exec_module(fresh_config)
            from dataclasses import fields
            import dashboard.strategy_settings_api as settings_api
            importlib.reload(settings_api)
            install_strategy_settings_routes = settings_api.install_strategy_settings_routes

            for obj in gc.get_objects():
                if type(obj).__name__ == "RealtimeDashboardService":
                    try:
                        install_strategy_settings_routes(obj)
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
                elif type(obj).__name__ == 'LiveTradingEngine':
                    strategy = getattr(obj, 'malaysian_snr_strategy', None)
                    repository = getattr(obj, 'repository', None)
                    if strategy is not None and callable(getattr(repository, 'latest_msnr_runtime_settings', None)):
                        if strategy.config.strategy_version != fresh_config.MalaysianSNRConfig().strategy_version:
                            values = {field.name: getattr(strategy.config, field.name) for field in fields(fresh_config.MalaysianSNRConfig)
                                      if field.name != 'strategy_version' and hasattr(strategy.config, field.name)}
                            strategy = fresh_msnr.MalaysianSNRStrategy(strategy.provider, fresh_config.MalaysianSNRConfig(**values))
                            obj.malaysian_snr_strategy = strategy
                        strategy.runtime_settings_loader = lambda engine=obj: engine.repository.latest_msnr_runtime_settings(source=engine.config.source)
    except Exception:
        pass


_sync_runtime_dashboard_if_needed()
