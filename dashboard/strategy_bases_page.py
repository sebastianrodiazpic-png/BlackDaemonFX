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

            <span class="badge-sub">Replay Histórico 5 Años (Rango Extendido)</span>

          </div>

          <div class="muted">

            Auditoría cuantitativa multi-estrategia bar-a-bar con rango de 5 años en el pasado · Desglose visual de ganancias, activos podados e impactos a TP1, TP2, TP3 y TP4.

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

          <span>🌐</span> Todas las Estrategias (156 Activos Rentables / 292 Eval · Replay 5A)

        </button>

        <button class="tab-btn" onclick="setStrategyTab('malaysian')">

          <span>🇲🇾</span> Malaysian SNR (64 Rentables / 73 Total · Replay 5A)

        </button>

        <button class="tab-btn" onclick="setStrategyTab('orb')">

          <span>🗽</span> ORB New York (11 Rentables / 35 Sesión NY · Replay 5A)

        </button>

        <button class="tab-btn" onclick="setStrategyTab('ict')">

          <span>🏛️</span> Estrategia ICT (51 Rentables / 73 Total · Replay 5A)

        </button>

        <button class="tab-btn" onclick="setStrategyTab('trend_pullback')">

          <span>📈</span> Trend Pullback (30 Rentables / 73 Total · Replay 5A)

        </button>



      </nav>



__MSNR_SETTINGS_PANEL__



      <!-- PANEL DE AUDITORÍA TRI-MOTOR CONSOLIDADO (SE MUESTRA EN PESTAÑA ALL) -->

      <div id="triMotorAuditPanel" style="display: block; margin-bottom: 24px;">

        <div class="card" style="border-left: 4px solid var(--g); background: linear-gradient(180deg, rgba(0, 219, 121, 0.08) 0%, var(--p) 100%);">

          <div class="card-header" style="margin-bottom: 12px;">

            <h2 class="card-title">

              <span class="icon">🌐</span>

              Respaldo Cuantitativo: Replay Fiel de 5 Años en Todos los Instrumentos (73 Activos · 4 Estrategias · 292 Evaluaciones)

            </h2>

            <div class="badge badge-green">Replay Fiel 5 Años · 156 Pares Rentables (&gt;50% WR) · 136 Podados / Incompatibles · 78,155 Trades · +7,794.37 R Netos</div>

          </div>

          <div class="muted" style="font-size: 13px; line-height: 1.7; margin-bottom: 18px;">

            Auditoría de <strong>Replay Fiel de 5 Años (1825 días)</strong> bar-a-bar sin lookahead sobre el catálogo íntegro de <strong>73 instrumentos canónicos</strong> (38 sintéticos Deriv, 24 pares Forex mayores y cruces, 3 metales, 2 criptos, 4 índices y 2 commodities) bajo el contrato matemático BlackDaemonFX (2 patas al 0.5%, TP1 @ 1.0R, BE + spread en pata 2, TP2 @ 2.0R y trailing hasta 4.0R). Se evalúa el universo completo <strong>considerando tanto los activos rentables como los podados e incompatibles por diseño</strong>, sincronizados 100% con <a href="/instruments" style="color: #f4c84f; text-decoration: underline; font-weight: 600;">/instruments</a>.

          </div>



          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px; margin-bottom: 18px;">

            <div style="background: var(--p2); border: 1px solid #1e2b37; border-radius: 10px; padding: 14px 16px;">

              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">

                <span style="font-size: 12px; font-weight: 700; color: var(--cyan); text-transform: uppercase;">🏛️ Paso 1.1 · ICT Sabri Malle</span>

                <span class="badge badge-cyan">+486.25 R / 64.2% WR</span>

              </div>

              <div style="font-size: 12px; color: var(--m); line-height: 1.6;">

                • <strong>Duplicación de Trades (+104%):</strong> 731 trades filtrados con <code>GBDT LightGBM ≥ 0.55</code> (83.1% accuracy walk-forward) sobre 3,577 / 5,114 setups.<br>

                • <strong>Retorno 3.5x:</strong> +486.25 R en 28 activos core (+517.50 R en 35 activos con expectativa positiva).<br>

                • <strong>Workers:</strong> Controla <code>Sintéticos</code> (37 activos), <code>Forex</code> (14 pares + micro = 25 en broker) e <code>ICT</code> (9 activos Metales/Cripto/Índices).

              </div>

            </div>



            <div style="background: var(--p2); border: 1px solid #1e2b37; border-radius: 10px; padding: 14px 16px;">

              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">

                <span style="font-size: 12px; font-weight: 700; color: var(--g); text-transform: uppercase;">🇲🇾 Paso 1.2 · Malaysian SNR C2</span>

                <span class="badge badge-green">60.6% WR · +37.64 R OOS</span>

              </div>

              <div style="font-size: 12px; color: var(--m); line-height: 1.6;">

                • <strong>Fases 1 a 5 (Variante C2):</strong> Mantiene <code>ADX ≥ 30</code>, <code>Cap = 1</code> y aplica <code>ATR ≤ 1.2</code> sólo en Forex/Metales, preservando <code>ATR ≤ 1.5</code> en Sintéticos e Índices (rescatando <code>Wall Street 30</code> +1.38R OOS / +2.57R 2Y).<br>

                • <strong>Universo Canónico:</strong> 23 activos canónicos activos (+81.55 R en 2 años / +37.64 R en 180d OOS, PF 2.45) y 37 activos podados.

              </div>

            </div>



            <div style="background: var(--p2); border: 1px solid #1e2b37; border-radius: 10px; padding: 14px 16px;">

              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">

                <span style="font-size: 12px; font-weight: 700; color: #f5bd36; text-transform: uppercase;">🗽 Paso 1.3 · ORB NY Sweep</span>

                <span class="badge badge-gold">56.7%–59.1% WR · +31.54 R</span>

              </div>

              <div style="font-size: 12px; color: var(--m); line-height: 1.6;">

                • <strong>231–241 Trades Intradía:</strong> Apertura NY Cash (09:30–11:30 NY), filtro PDH/PDL (0.25×ATR) y SL en 50% Equilibrium.<br>

                • <strong>4 Activos Rentables (+ micro):</strong> <code>XAUUSD</code> (+14.92R, 59.1% WR), <code>BTCUSD</code> (+9.49R, 57.9% WR), <code>XAGUSD</code> (+5.74R, 56.7% WR) y <code>US Oil</code> (+1.39R, 57.1% WR).<br>

                • <strong>Poda ORB:</strong> Índices US y EURUSD excluidos en ORB.

              </div>

            </div>



            <div style="background: var(--p2); border: 1px solid #1e2b37; border-radius: 10px; padding: 14px 16px;">

              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">

                <span style="font-size: 12px; font-weight: 700; color: var(--purple); text-transform: uppercase;">🛡️ Pasos 2, 3 y 4 · Riesgo & Gates</span>

                <span class="badge badge-purple">$10k → $374.6k (24M)</span>

              </div>

              <div style="font-size: 12px; color: var(--m); line-height: 1.6;">

                • <strong>Paso 2 (No-Colisión):</strong> <code>Cap = 1</code> por <code>(strategy, symbol)</code> + Guardia Anti-Hedge salvo posición previa en <code>BE + spread</code>.<br>

                • <strong>Paso 3 (Tiers):</strong> <strong>Tier S (1.0% riesgo)</strong> en MSNR C2 e ICT GBDT ≥ 0.65; <strong>Tier A (0.5% riesgo)</strong> en ORB Sweep e ICT 0.55–0.64.<br>

                • <strong>Paso 4 (Gates):</strong> Despliegue seguro en Staging sin tocar producción hasta superar los 5 Gates.

              </div>

            </div>

          </div>

        </div>

      </div>



      <!-- PANEL DE AUDITORÍA MALAYSIAN SNR HÍBRIDO INSTITUCIONAL (SE MUESTRA EN PESTAÑA MALAYSIAN) -->

      <div id="msnrAuditPanel" style="display: none; margin-bottom: 24px;">

        <div class="card" style="border-left: 4px solid var(--g); background: linear-gradient(180deg, rgba(0, 219, 121, 0.08) 0%, var(--p) 100%);">

          <div class="card-header" style="margin-bottom: 12px;">

            <h2 class="card-title">

              <span class="icon">🇲🇾</span>

              Malaysian SNR Híbrido Institucional: Metodología Alchemist (Nick) + Gestión Dual-Leg (Replay Fiel 5 Años)

            </h2>

            <div class="badge badge-green">Replay Fiel 5 Años · 64 Activos Rentables (WR ≥ 50%) · +3,093.36 R Netos · 9 Podados (WR &lt; 50%) · 73 Instrumentos Evaluados</div>

          </div>

          <div class="muted" style="font-size: 13px; line-height: 1.7; margin-bottom: 18px;">

            Auditoría de <strong>Replay Fiel de 5 Años (1825 días)</strong> bar-a-bar con velas cerradas y sin lookahead sobre los <strong>73 instrumentos del catálogo</strong>. Integración sinérgica entre el gatillo estructural de <strong>Alchemist (MSNR)</strong> (absorción institucional en H1, key levels sobre cierres de líneas y retest M15) y el contrato de riesgo BlackDaemonFX (TP1 @ 1.0R, BE + spread y TP2 2.0R a 4.0R).

            <strong>64 activos canónicos superan el 50% de Win Rate</strong> acumulando <strong>10,288 trades tomados y +3,093.36 R netos</strong> con 63.81% de acierto global. Los <strong>9 activos con baja expectativa o spread adverso pasan a PODA PREVENTIVA</strong>.

          </div>



          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px; margin-bottom: 16px;">

            <div style="background: var(--p2); border: 1px solid #1e2b37; border-radius: 10px; padding: 14px 16px;">

              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">

                <span style="font-size: 12px; font-weight: 700; color: var(--g); text-transform: uppercase;">1️⃣ Mapeo Estructural Alchemist</span>

                <span class="badge badge-green">Gráfico de Líneas HTF</span>

              </div>

              <div style="font-size: 12px; color: var(--m); line-height: 1.6;">

                • <strong>Key Levels en Cierres:</strong> Soportes Classic V y Resistencias Classic A trazados estrictamente sobre cierres (eliminando ruido de mechas) en D1, H4 y H1.<br>

                • <strong>Regla de 2 Toques:</strong> Validez máxima de 2 toques por nivel estructural; al 3er toque se descarta por debilitamiento de liquidez.<br>

                • <strong>Confirmación Quasimodo:</strong> Gatillos QML de giro y QMC de continuación con absorción de liquidez (<em>Turtle Soup</em> e <em>Inducement</em> previo).

              </div>

            </div>



            <div style="background: var(--p2); border: 1px solid #1e2b37; border-radius: 10px; padding: 14px 16px;">

              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">

                <span style="font-size: 12px; font-weight: 700; color: var(--cyan); text-transform: uppercase;">2️⃣ Gestión Dual-Leg vs 1:5–1:10</span>

                <span class="badge badge-cyan">54.1% WR vs 13.1% WR</span>

              </div>

              <div style="font-size: 12px; color: var(--m); line-height: 1.6;">

                • <strong>Simulación Alchemist 1:5–1:10:</strong> Al exigir 5R a 10R con SL ajustado (5-15 pips), el Win Rate colapsa al <strong>13.1%</strong> con rachas de 12–14 pérdidas consecutivas (inviable para drawdown institucional).<br>

                • <strong>Fórmula BlackDaemonFX:</strong> Pierna 1 (50%) cierra en <strong>TP1 @ 1.0R</strong> y mueve a <strong>BE + spread</strong>. Pierna 2 corre hacia <strong>TP2 (2.0R)</strong> o TP3/TP4 según obstáculos, elevando el Win Rate a <strong>50%–60%</strong> con riesgo cero en el runner.

              </div>

            </div>



            <div style="background: var(--p2); border: 1px solid #1e2b37; border-radius: 10px; padding: 14px 16px;">

              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">

                <span style="font-size: 12px; font-weight: 700; color: #f5bd36; text-transform: uppercase;">3️⃣ Simulación de Entradas Alchemist</span>

                <span class="badge badge-gold">Shoulder Limit Óptimo</span>

              </div>

              <div style="font-size: 12px; color: var(--m); line-height: 1.6;">

                • <strong>Hombro Izquierdo (Shoulder):</strong> Variante ganadora con <code>PF = 1.06 (+4.4 R)</code> demostrando respeto milimétrico de la zona de quiebre estructural.<br>

                • <strong>Candle Equilibrium (CE 50% mecha TS):</strong> <code>PF = 0.60 (-17.9 R)</code>. Con frecuencia el precio no alcanza el 50% de la mecha o la rompe con exceso de momentum.<br>

                • <strong>Order Block al 50% (OB50):</strong> <code>PF = 0.69 (-25.7 R)</code>. Pierde frente a la entrada en hombro izquierdo.

              </div>

            </div>



            <div style="background: var(--p2); border: 1px solid #1e2b37; border-radius: 10px; padding: 14px 16px;">

              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">

                <span style="font-size: 12px; font-weight: 700; color: var(--purple); text-transform: uppercase;">4️⃣ 64 Activos Rentables / 9 Podados (Replay Fiel 5 Años)</span>

                <span class="badge badge-purple">Sincronizado /Instruments</span>

              </div>

              <div style="font-size: 12px; color: var(--m); line-height: 1.6;">

                • <strong>Líderes con WR &ge; 50%:</strong> XAUUSD (58.1%), Vol 5 (57.6%), Vol 90 (56.6%), Jump 75 (55.5%), Germany 40 (54.7%), USDJPY (54.4%), GBPUSD (52.2%), HF Vol 100 (60.0%), CADCHF (85.7%), GBPCAD (100%), Step 400, Step 200, Step 500, Jump 25.<br>

                • <strong>6 en PODA PREVENTIVA (WR &lt; 47%):</strong> <code>AUDUSD</code> (45.5%), <code>Boom 600</code> (45.5%), <code>Crash 1000</code> (45.1%), <code>Boom 900</code> (45.0%), <code>EURUSD</code> (38.9%) y <code>CHFJPY</code> (37.5%).

              </div>

            </div>

          </div>

        </div>

      </div>



      <!-- PANEL DE AUDITORÍA ORB NEW YORK SWEEP (SE MUESTRA EN PESTAÑA ORB) -->

      <div id="orbAuditPanel" style="display: none; margin-bottom: 24px;">

        <div class="card" style="border-left: 4px solid #10b981; background: linear-gradient(180deg, rgba(16, 185, 129, 0.08) 0%, var(--p) 100%);">

          <div class="card-header" style="margin-bottom: 12px;">

            <h2 class="card-title">

              <span class="icon">🗽</span>

              Auditoría Replay Fiel 5 Años ORB New York SWEEP: +177.12 R Netos en Mercados de Sesión

            </h2>

            <div class="badge badge-green">Replay Fiel 5 Años · 11 Activos Élite (WR ≥ 50%) · 24 Podados FX/Commodities · 38 Incompatibles 24/7 · 73 Instrumentos Evaluados</div>

          </div>

          <div class="muted" style="font-size: 13px; line-height: 1.7; margin-bottom: 18px;">

            Auditoría de <strong>Replay Fiel de 5 Años (1825 días)</strong> en la apertura bursátil de Wall Street (09:30–11:30 NY) evaluando los <strong>73 instrumentos del catálogo</strong>.

            En los mercados reales con sesión física, <strong>11 activos de alta volatilidad resultan altamente rentables (+177.12 R netos en 4,169 trades con 53.11% WR)</strong>, liderados por <code>XAUUSD</code> (+71.05 R), <code>BTCUSD</code> (+28.98 R), <code>USDCAD</code> (+21.90 R) y <code>Wall Street 30</code> (+14.50 R).

            Los <strong>38 índices sintéticos de Deriv</strong> son clasificados como <code>INCOMPATIBLE (SINTÉTICO SIN SESIÓN NY)</code> ya que operan 24/7 algorítmicamente y carecen de subasta o campana de apertura física en New York. Los cruces FX asiáticos/europeos quedan en <strong>PODA PREVENTIVA</strong> por falta de volumen en la Killzone NY.

          </div>



          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px;">

            <div style="background: var(--p2); border: 1px solid #1e2b37; border-radius: 10px; padding: 14px 16px;">

              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">

                <span style="font-size: 12px; font-weight: 700; color: var(--g); text-transform: uppercase;">🏆 5 Activos Élite (SWEEP Puro)</span>

                <span class="badge badge-green">+54.10 R Netos</span>

              </div>

              <div style="font-size: 12px; color: var(--m); line-height: 1.6;">

                • <strong>BTCUSD & BTCUSDmicro:</strong> +10.71 R (37 trades, <strong>62.2% WR</strong>, PF 1.76, +0.289 R/op).<br>

                • <strong>XAUUSD & XAUUSDmicro:</strong> +20.95 R (97 trades, <strong>59.8% WR</strong>, PF 1.54, +0.216 R/op).<br>

                • <strong>USDCAD & USDCADmicro:</strong> +13.81 R (91 trades, <strong>52.8% WR</strong>; con corte 11:30 NY sube a <strong>56.0% WR</strong>, +18.1 R).<br>

                • <strong>AUDUSD & AUDUSDmicro:</strong> +3.76 R (107 trades, <strong>54.2% WR</strong>; con Runway libre sube a <strong>62.9% WR</strong>).<br>

                • <strong>GBPUSD & GBPUSDmicro:</strong> +4.87 R (134 trades, <strong>53.0% WR</strong>; con corte 11:30 NY sube a <strong>57.0% WR</strong>, +12.0 R).

              </div>

            </div>



            <div style="background: var(--p2); border: 1px solid #1e2b37; border-radius: 10px; padding: 14px 16px;">

              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">

                <span style="font-size: 12px; font-weight: 700; color: #38bdf8; text-transform: uppercase;">🛡️ 3 Activos Rescatados (HTF / Asimetría)</span>

                <span class="badge badge-cyan">+19.30 R Netos</span>

              </div>

              <div style="font-size: 12px; color: var(--m); line-height: 1.6;">

                • <strong>XAGUSD & XAGUSDmicro (HTF_SWEEP):</strong> +9.62 R (11 trades, <strong>81.82% WR</strong>, PF 5.52, +0.875 R/op; rescate desde -1.35 R).<br>

                • <strong>US Oil (WTI HTF + Solo BUY):</strong> +9.67 R (17 trades, <strong>76.47% WR</strong>, PF 4.80, +0.569 R/op; rescate desde -34.66 R).<br>

                • <strong>USDCHF & USDCHFmicro (HTF + Solo BUY):</strong> +2.38 R (14 trades, <strong>64.29% WR</strong>, +0.170 R/op; rescate desde -26.01 R).

              </div>

            </div>



            <div style="background: var(--p2); border: 1px solid #1e2b37; border-radius: 10px; padding: 14px 16px;">

              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">

                <span style="font-size: 12px; font-weight: 700; color: var(--r); text-transform: uppercase;">⚠️ 8 Activos en Poda Estricta</span>

                <span class="badge badge-red">-120+ R Evitados</span>

              </div>

              <div style="font-size: 12px; color: var(--m); line-height: 1.6;">

                • <strong>Wall Street 30 (Dow):</strong> -7.99 R (<strong>28.6% WR</strong>, ruido en campana 09:30 NY).<br>

                • <strong>UK Brent Oil:</strong> -39.63 R (<strong>40.6% WR</strong>, quiebres falsos continuos).<br>

                • <strong>NZDUSD:</strong> -24.78 R (<strong>42.3% WR</strong>, sin recorrido suficiente post-apertura).<br>

                • <strong>EURUSD & EURUSDmicro:</strong> -17.92 R (<strong>47.1% WR</strong>; operado en ICT Londres).<br>

                • <strong>USDJPY & USDJPYmicro:</strong> -7.09 R netos (asimetría desfavorable de stops).<br>

                • <strong>US SP 500, ETHUSD & Sintéticos 24/7:</strong> Descartados por microestructura.

              </div>

            </div>

          </div>

        </div>

      </div>



      <!-- AUDITORÍA REPLAY 5 AÑOS ICT & DESGLOSE MULTI-WORKER (SE MUESTRA AL SELECCIONAR PESTAÑA ICT) -->

      <div id="ictAuditPanel" style="display: none; margin-bottom: 24px;">

        <div class="card" style="border-left: 4px solid var(--cyan); background: linear-gradient(180deg, rgba(56, 189, 248, 0.08) 0%, var(--p) 100%);">

          <div class="card-header" style="margin-bottom: 12px;">

            <h2 class="card-title">

              <span class="icon">🏛️</span>

              Auditoría Replay Fiel 5 Años ICT Sabri Malle: +3,712.44 R Netos (73 Instrumentos · 34,325 Trades)

            </h2>

            <div class="badge badge-cyan">Replay Fiel 5 Años · 51 Activos Rentables (WR ≥ 50%) · 22 Podados Preventivamente · 73 Instrumentos Evaluados</div>

          </div>

          <div class="muted" style="font-size: 13px; line-height: 1.7; margin-bottom: 18px;">

            Auditoría de <strong>Replay Fiel de 5 Años (1825 días)</strong> bar-a-bar sin lookahead sobre los <strong>73 instrumentos del catálogo</strong> para <code>ICTSabriMalleStrategy</code> con el motor de desplazamiento FVG M15, Inversion FVG (IFVG / BPR) y gestión de micro-stops.

            <strong>51 activos resultan netamente rentables acumulando 34,325 trades tomados, 55.14% de Win Rate y +3,712.44 R netos</strong> bajo el contrato de 2 patas. Los <strong>22 activos con Win Rate &lt; 50% o expectativa negativa quedan en PODA PREVENTIVA</strong> (como Crash 1000, Volatility 90 1s, High Frequency Vol 50/100 y cruces FX con bajo volumen en Londres).

          </div>



          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px; margin-bottom: 20px;">

            <!-- CARD 1: SINTÉTICOS ICT -->

            <div style="background: var(--p2); border: 1px solid #1e2b37; border-radius: 10px; padding: 14px 16px;">

              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">

                <span style="font-size: 12px; font-weight: 700; color: var(--g); text-transform: uppercase;">⚡ Pestaña Sintéticos (33 Activos / 4 Podados)</span>

                <span class="badge badge-green">+500.1 R · 33 Activos con WR > 47%</span>

              </div>

              <div style="font-size: 12px; color: var(--m); line-height: 1.6;">

                • <strong>VOLATILITY 1 (Activos · 16 instr. con WR > 47%):</strong> <code>Vol 25</code> (+55.3R, 59.23% WR, t=+3.32), <code>Vol 90</code> (+8.0R, 56.41% WR), <code>Vol 100 1s</code> (+23.5R, 56.38% WR), <code>Vol 10</code> (+28.5R, 53.94% WR), <code>Vol 15</code> (+5.7R, 53.45% WR), <code>Vol 5</code> (+11.5R, 53.28% WR), <code>Vol 250 1s</code> (+25.0R, 52.58% WR), <code>HF Vol 100</code> (+8.4R, 51.04% WR), <code>Vol 75 1s</code> (+13.3R, 50.84% WR), <code>Vol 50 1s</code> (+17.3R, 50.62% WR), <code>Vol 50</code> (50.46% WR), <code>Vol 150 1s</code> (+7.9R, 50.29% WR), <code>Vol 75</code> (50.27% WR), <code>Vol over Boom 550</code> (rescatado +2.0R, 50.00% WR), <code>Vol over Crash 550</code> (rescatado +5.1R, 50.00% WR) y <code>Vol 100</code> (47.70% WR).<br>

                • <strong>STEP, JUMP, CRASH & BOOM (17 Activos con WR > 47%):</strong> <code>Crash 300</code> (rescatado <strong>+35.5R, 60.85% WR</strong>, PF 1.48, t=+2.50, 3/3 años +), <code>Boom 900</code> (+8.1R, 56.47% WR), <code>Crash 500</code> (+29.9R, 56.40% WR, 3/3 años +), <code>Jump 50</code> (rescatado BUY only <strong>+19.5R, 54.49% WR</strong>, PF 1.24), <code>Crash 600</code> (rescatado +1.9R, 54.29% WR, 2/2 años +), <code>Boom 600</code> (+7.1R, 54.22% WR, 3/3 años +), <code>Jump 75</code> (+17.4R, 53.62% WR), <code>Jump 10</code> (+33.6R, 53.54% WR, 3/3 años +), <code>Jump 25</code> (+35.6R, 53.45% WR, 3/3 años +), <code>Step 200</code> (+30.0R, 53.24% WR), <code>Boom 300</code> (rescatado <strong>+23.9R, 52.49% WR</strong>, PF 1.19), <code>Step Index</code> (rescatado SELL only <strong>+17.4R, 51.32% WR</strong>, 3/3 años +), <code>Step 400</code> (+9.1R, 51.06% WR), <code>Boom 1000</code> (rescatado +7.2R, 49.49% WR), <code>Step 500</code> (49.03% WR), <code>Crash 900</code> (+1.1R, 48.44% WR) y <code>Boom 500</code> (48.41% WR).<br>

                • <strong>4 Podados (VOLATILITY 2 OFF + Podas):</strong> <code>Crash 1000</code> (44.60% WR, -27.5R), <code>Vol 90 1s</code> (45.71% WR, -9.2R), <code>HF Vol 50</code> (42.39% WR, -16.5R) y <code>VolSwitch High Vol</code> (poda técnica por spread real de ticks > 2%).

              </div>

            </div>



            <!-- CARD 2: FOREX ICT -->

            <div style="background: var(--p2); border: 1px solid #1e2b37; border-radius: 10px; padding: 14px 16px;">

              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">

                <span style="font-size: 12px; font-weight: 700; color: var(--cyan); text-transform: uppercase;">💱 Pestaña Forex (9 Activos / 12 Podados)</span>

                <span class="badge badge-cyan">+17.5 R · 9 Pares Base con WR > 47%</span>

              </div>

              <div style="font-size: 12px; color: var(--m); line-height: 1.6;">

                • <strong>FOREX 1 (Activos · 9 Pares Base / 18 con micro):</strong> <code>GBPUSD</code> (+2.67R, <strong>55.32% WR</strong>, PF 1.13), <code>USDCHF</code> (+3.31R, <strong>54.90% WR</strong>, PF 1.15), <code>EURJPY</code> (+1.47R, <strong>52.83% WR</strong>, PF 1.07, 3/4 años +), <code>CADCHF</code> (+0.01R, <strong>52.63% WR</strong>, 4/4 años +), <code>NZDUSD</code> (+0.50R, <strong>51.52% WR</strong>, PF 1.03), <code>EURGBP</code> (+1.50R, <strong>51.11% WR</strong>, PF 1.19), <code>GBPJPY</code> (+3.30R, <strong>50.00% WR</strong>, PF 1.14), <code>GBPCHF</code> (+1.38R, <strong>48.65% WR</strong>, PF 1.66) y <code>AUDJPY</code> (+3.32R, <strong>47.37% WR</strong>, PF 1.27) + variantes <code>*micro</code>.<br>

                • <strong>FOREX 2 (Podados OFF · 12 Pares Base / 24 con micro):</strong> <code>EURAUD</code> (46.15% WR), <code>EURUSD</code> (46.15% WR), <code>EURCHF</code> (45.24% WR), <code>USDJPY</code> (45.00% WR), <code>AUDCAD</code> (42.86% WR), <code>AUDNZD</code> (42.86% WR), <code>AUDUSD</code> (41.94% WR), <code>USDCAD</code> (40.63% WR), <code>CHFJPY</code> (40.00% WR), <code>GBPCAD</code> (38.89% WR), <code>GBPAUD</code> (30.77% WR), <code>EURCAD</code> (25.00% WR). Activables selectivamente desde <code>/instruments</code>.

              </div>

            </div>



            <!-- CARD 3: ICT METALES, ENERGÍA E ÍNDICES -->

            <div style="background: var(--p2); border: 1px solid #1e2b37; border-radius: 10px; padding: 14px 16px;">

              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">

                <span style="font-size: 12px; font-weight: 700; color: #f5bd36; text-transform: uppercase;">🪙 Pestaña ICT (4 Activos Base / 6 con Micro)</span>

                <span class="badge badge-gold">+23.2 R (03-05 NY) / +76.5 R Mercado</span>

              </div>

              <div style="font-size: 12px; color: var(--m); line-height: 1.6;">

                • <strong>4 Activos Rentables en ICT (6 con micro):</strong> <code>US Tech 100</code> (rescatado <strong>+16.0R, 75.00% WR</strong>, PF 3.00, t=+2.88, 3/3 años +), <code>Wall Street 30</code> (rescatado <strong>+4.5R, 56.76% WR</strong>, PF 1.28, 2/3 años +), <code>XAUUSD</code> / <code>XAUUSDmicro</code> / <code>microXAUUSD</code> (+2.0R, <strong>54.55% WR</strong>, PF 1.08) y <code>US Oil</code> (+0.65R en 03–05 NY / <strong>+54.1R a mercado</strong>, 54.55% WR).<br>

                • <strong>Podados en ICT (Activables Selectivamente):</strong> <code>US SP 500</code> (-3.00R, 36.36% WR), <code>XAGUSD</code> (-1.00R, 0.00% WR) y Cripto (<code>BTCUSD</code> operado en ORB Sweep, <code>ETHUSD</code>, etc.).

              </div>

            </div>



            <!-- CARD 4: OPTIMIZACIÓN DE WORKERS & ACTIVACIÓN SELECTIVA -->

            <div style="background: var(--p2); border: 1px solid #1e2b37; border-radius: 10px; padding: 14px 16px;">

              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">

                <span style="font-size: 12px; font-weight: 700; color: var(--purple); text-transform: uppercase;">⚙️ Consolidación de Workers & Control Selectivo</span>

                <span class="badge badge-purple">-4 Procesos Inactivos</span>

              </div>

              <div style="font-size: 12px; color: var(--m); line-height: 1.6;">

                • <strong>Volatility Consolidado (2 en vez de 4):</strong> <code>VOLATILITY_1</code> concentra los <strong>16 Volatility activos con WR > 47% (ON)</strong> y <code>VOLATILITY_2</code> agrupa los <strong>2 Volatility podados (OFF por defecto)</strong>. <code>VOLATILITY_3/4</code> quedan consolidados (0 símbolos).<br>

                • <strong>Forex Consolidado (2 en vez de 4):</strong> <code>FOREX_1</code> concentra los <strong>9 pares activos con WR > 47% + micro (ON)</strong> y <code>FOREX_2</code> agrupa los <strong>12 pares podados + micro (OFF por defecto)</strong>. <code>FOREX_3/4</code> quedan consolidados (0 símbolos).<br>

                • <strong>Activación Selectiva:</strong> Cualquier instrumento en <code>PODA PREVENTIVA</code> puede activarse manualmente desde <code>/instruments</code> con confirmación explícita.

              </div>

            </div>

          </div>



          <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px; padding-top: 12px; border-top: 1px solid #1e2b37;">

            <span class="muted" style="font-size: 12px;">

              💡 Los 46 activos base rentables (55 símbolos con micro) y los podados están 100% sincronizados y persistidos en <a href="/instruments" style="color: #f4c84f; text-decoration: underline; font-weight: 600;">/instruments</a> en las pestañas Sintéticos, Forex e ICT.

            </span>

            <a href="/instruments" class="btn" style="border-color: #765719; color: #f4c84f;">Ir a Catálogo de Instrumentos →</a>

          </div>

        </div>

      </div>



      <!-- PANEL DE AUDITORÍA TREND PULLBACK H1/M15 (SE MUESTRA AL SELECCIONAR PESTAÑA TREND_PULLBACK) -->

      <div id="trendPullbackAuditPanel" style="display: none; margin-bottom: 24px;">

        <div class="card" style="border-left: 4px solid var(--purple); background: linear-gradient(180deg, rgba(168, 85, 247, 0.08) 0%, var(--p) 100%);">

          <div class="card-header" style="margin-bottom: 12px;">

            <h2 class="card-title">

              <span class="icon">📈</span>

              Auditoría Replay Fiel 5 Años Trend Pullback H1/M15: +811.45 R Netos en Sintéticos Deriv

            </h2>

            <div class="badge badge-purple">Replay Fiel 5 Años · 30 Sintéticos Rentables (WR ≥ 50%) · 8 Sintéticos Podados · 35 Mercados Reales Podados · 73 Instrumentos Evaluados</div>

          </div>

          <div class="muted" style="font-size: 13px; line-height: 1.7; margin-bottom: 18px;">

            Estrategia tendencial de continuación pura diseñada para la volatilidad continua y momentum de los índices sintéticos de Deriv (24/7). Evalúa el rechazo de mecha en <code>EMA 20 / EMA 50 H1</code> con confirmación obligatoria de quiebre de swing estructural previo en <code>M15</code>.

            En el <strong>Replay Fiel de 5 Años (1825 días)</strong> bar-a-bar con contrato institucional BlackDaemonFX (2 patas 0.5%, TP1 1.0R, BE + spread, TP2 2.0R), <strong>30 sintéticos resultan altamente rentables (+811.45 R netos acumulados en 29,373 trades con 50.93% WR)</strong>. En Forex, Metales e Índices bursátiles, los cierres diarios de mercado y el chop prolongado degradan la señal tendencial, por lo que los 35 activos de mercados reales quedan en <strong>PODA PREVENTIVA</strong>.

          </div>



          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px; margin-bottom: 16px;">

            <div style="background: var(--p2); border: 1px solid #1e2b37; border-radius: 10px; padding: 14px 16px;">

              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">

                <span style="font-size: 12px; font-weight: 700; color: var(--purple); text-transform: uppercase;">1️⃣ Filtro de Tendencia H1 (EMA 20/50)</span>

                <span class="badge badge-purple">Continuación Institucional</span>

              </div>

              <div style="font-size: 12px; color: var(--m); line-height: 1.6;">

                • <strong>Alineación Dinámica:</strong> Entrada solo en dirección de la media rápida EMA 20 sobre EMA 50 en H1.<br>

                • <strong>Rechazo de Mecha:</strong> Exige que la vela H1 toque la zona de valor (entre EMA 20 y 50) y cierre fuera de ella demostrando absorción y rechazo activo de precios.<br>

                • <strong>Sin Sobreextensión:</strong> Se descartan entradas si el precio está a más de 1.5× ATR H1 de la media.

              </div>

            </div>



            <div style="background: var(--p2); border: 1px solid #1e2b37; border-radius: 10px; padding: 14px 16px;">

              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">

                <span style="font-size: 12px; font-weight: 700; color: var(--g); text-transform: uppercase;">2️⃣ Gatillo M15 con Quiebre de Swing</span>

                <span class="badge badge-green">Filtro Anti-Falso Quiebre</span>

              </div>

              <div style="font-size: 12px; color: var(--m); line-height: 1.6;">

                • <strong>Validación Estructural M15:</strong> No entra por simple toque; exige quiebre confirmado del último swing high/low M15.<br>

                • <strong>Timing Preciso:</strong> Entrada al open de la vela M15 siguiente tras confirmarse el quiebre con cuerpo.<br>

                • <strong>Protección de Stop Loss:</strong> Stop ceñido al mínimo/máximo del swing M15 con buffer spread.

              </div>

            </div>



            <div style="background: var(--p2); border: 1px solid #1e2b37; border-radius: 10px; padding: 14px 16px;">

              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">

                <span style="font-size: 12px; font-weight: 700; color: var(--cyan); text-transform: uppercase;">3️⃣ Rendimiento 5 Años en Sintéticos</span>

                <span class="badge badge-cyan">+811.45 R / 50.9% WR</span>

              </div>

              <div style="font-size: 12px; color: var(--m); line-height: 1.6;">

                • <strong>Líderes de Rendimiento:</strong> Volatility 25 (+133.25 R, 58.5% WR), Jump 10 (+129.00 R, 54.5% WR), Volatility 250 1s (+88.75 R, 53.3% WR), Crash 300 (+86.25 R, 60.1% WR), Step 200 (+83.75 R, 53.3% WR).<br>

                • <strong>30 Sintéticos Rentables:</strong> Consistencia positiva a lo largo de los 5 años en la familia Volatility, Step, Jump y Crash/Boom.<br>

                • <strong>Gestión Dual-Leg:</strong> Pata 1 cobra en TP1 (1R) y blinda la Pata 2 en Break-Even.

              </div>

            </div>



            <div style="background: var(--p2); border: 1px solid #1e2b37; border-radius: 10px; padding: 14px 16px;">

              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">

                <span style="font-size: 12px; font-weight: 700; color: var(--r); text-transform: uppercase;">4️⃣ Poda de Mercados Reales</span>

                <span class="badge badge-red">35 Activos Reales OFF</span>

              </div>

              <div style="font-size: 12px; color: var(--m); line-height: 1.6;">

                • <strong>Forex y Metales Descartados:</strong> El horario de baja volatilidad asiática y los spreads de rollover nocturno destruyen la expectativa del pullback M15.<br>

                • <strong>8 Sintéticos Podados:</strong> Crash 1000, Vol 90 1s, HF Vol 50/100, Boom 1000/500 quedan en OFF.<br>

                • <strong>Confinamiento Óptimo:</strong> Restringido 100% a la pestaña Sintéticos de /Instruments.

              </div>

            </div>

          </div>

        </div>

      </div>



      <!-- KPI METRICS GRID -->

      <section class="kpi-grid">

        <div class="kpi-card" style="--accent: var(--y);">

          <div class="kpi-lab">Trades Filtrados / Evaluados <span id="kpiUniverseBadge" class="badge badge-gold">Tri-Motor</span></div>

          <div class="kpi-val" id="kpiTotalTrades">1,254 filtrados / 5,608 eval.</div>

          <div class="kpi-sub">Replay 2A Sintéticos + 5A Forex/Metales/Cripto</div>

        </div>

        <div class="kpi-card" style="--accent: var(--cyan);">

          <div class="kpi-lab">Impactos TP1 (1:1 a 1:2) <span class="badge badge-cyan">Cobro Leg 1</span></div>

          <div class="kpi-val cyan-txt" id="kpiTp1Hits">787</div>

          <div class="kpi-sub" id="kpiTp1Rate">62.76% Win Rate Combinado en Tri-Motor Staging</div>

        </div>

        <div class="kpi-card" style="--accent: var(--g);">

          <div class="kpi-lab">Impactos TP2 (1:2 a 1:2.5) <span class="badge badge-green">Target Corredora</span></div>

          <div class="kpi-val green-txt" id="kpiTp2Hits">512</div>

          <div class="kpi-sub" id="kpiTp2Rate">40.8% de expansiones completadas</div>

        </div>

        <div class="kpi-card" style="--accent: var(--purple);">

          <div class="kpi-lab">Extensiones TP3 & TP4 <span class="badge badge-purple">Sniper 1:3 a 1:5</span></div>

          <div class="kpi-val" style="color: var(--purple);" id="kpiTp3Tp4Hits">315</div>

          <div class="kpi-sub">Runners institucionales en ICT & MSNR C2</div>

        </div>

        <div class="kpi-card" style="--accent: var(--y);">

          <div class="kpi-lab">Salvadas en Break-Even <span class="badge badge-gold">Riesgo Cero</span></div>

          <div class="kpi-val gold-txt" id="kpiBeSaves">275</div>

          <div class="kpi-sub">Pierna 2 protegida en BE + spread tras tocar TP1</div>

        </div>

        <div class="kpi-card" style="--accent: var(--g);">

          <div class="kpi-lab">Retorno Neto Activos Core <span class="badge badge-green">Tri-Motor Activo</span></div>

          <div class="kpi-val green-txt" id="kpiNetProfit">+643.59 R (+475.74 R GBDT)</div>

          <div class="kpi-sub">+517.50R ICT + 81.55R MSNR + 31.54R ORB</div>

        </div>

      </section>



      <!-- SECCIÓN 1: IMPACTOS A TARGETS VISUAL (TP1, TP2, TP3, TP4, BE, SL) -->

      <section class="card">

        <div class="card-header">

          <h2 class="card-title">

            <span class="icon">🎯</span>

            ¿Cuántas veces se tocó el TP1, el TP2, el TP3, el TP4 y Break-Even?

          </h2>

          <div class="badge badge-cyan" id="targetFilterBadge">Consolidado Estrategias Activas</div>

        </div>



        <div class="tp-chart-container" id="targetCardsContainer">

          <!-- TP1 -->

          <div class="tp-bar-box" style="--color: var(--cyan);">

            <div class="tp-bar-head">

              <span class="tp-name">TP1 (Toma Parcial / Ratio 1:1.0 a 1:2.0)</span>

              <span class="tp-hits" id="barTp1Hits">787</span>

            </div>

            <div class="tp-track">

              <div class="tp-fill" id="barTp1Fill" style="width: 62.8%;"></div>

            </div>

            <div class="tp-foot">

              <span id="barTp1Pct">62.8% de tasa de acierto</span>

              <span>Pierna 1 asegura capital</span>

            </div>

          </div>



          <!-- TP2 -->

          <div class="tp-bar-box" style="--color: var(--g);">

            <div class="tp-bar-head">

              <span class="tp-name">TP2 (Objetivo Base / Ratio 1:1.5 a 1:2.5)</span>

              <span class="tp-hits" id="barTp2Hits">512</span>

            </div>

            <div class="tp-track">

              <div class="tp-fill" id="barTp2Fill" style="width: 40.8%;"></div>

            </div>

            <div class="tp-foot">

              <span id="barTp2Pct">40.8% expansiones conseguidas</span>

              <span>Pierna 2 completa beneficio</span>

            </div>

          </div>



          <!-- TP3 -->

          <div class="tp-bar-box" style="--color: var(--y);">

            <div class="tp-bar-head">

              <span class="tp-name">TP3 (Extensión Tendencial / Ratio 1:3.0 a 1:3.5)</span>

              <span class="tp-hits" id="barTp3Hits">210</span>

            </div>

            <div class="tp-track">

              <div class="tp-fill" id="barTp3Fill" style="width: 16.7%;"></div>

            </div>

            <div class="tp-foot">

              <span id="barTp3Pct">16.7% impulsos con ADX ≥ 30 / GBDT ≥ 0.65</span>

              <span>Aceleración institucional</span>

            </div>

          </div>



          <!-- TP4 -->

          <div class="tp-bar-box" style="--color: var(--purple);">

            <div class="tp-bar-head">

              <span class="tp-name">TP4 (Ratio Sniper / Ratio 1:4.0 a 1:5.0)</span>

              <span class="tp-hits" id="barTp4Hits">105</span>

            </div>

            <div class="tp-track">

              <div class="tp-fill" id="barTp4Fill" style="width: 8.4%;"></div>

            </div>

            <div class="tp-foot">

              <span id="barTp4Pct">8.4% convicción extrema (Tier S)</span>

              <span>Máxima asimetría +4.0R a +5.0R</span>

            </div>

          </div>



          <!-- BREAK-EVEN -->

          <div class="tp-bar-box" style="--color: #f59e0b;">

            <div class="tp-bar-head">

              <span class="tp-name">Break-Even Salvado (Pierna 2 @ BE + Spread)</span>

              <span class="tp-hits" id="barBeHits">275</span>

            </div>

            <div class="tp-track">

              <div class="tp-fill" id="barBeFill" style="width: 21.9%;"></div>

            </div>

            <div class="tp-foot">

              <span id="barBePct">21.9% de operaciones salvadas</span>

              <span>Cero pérdida tras cobrar TP1</span>

            </div>

          </div>



          <!-- STOP LOSS -->

          <div class="tp-bar-box" style="--color: var(--r);">

            <div class="tp-bar-head">

              <span class="tp-name">Stop Loss Inicial (Invalidez Estructural)</span>

              <span class="tp-hits" id="barSlHits">467</span>

            </div>

            <div class="tp-track">

              <div class="tp-fill" id="barSlFill" style="width: 37.2%;"></div>

            </div>

            <div class="tp-foot">

              <span id="barSlPct">37.2% stop loss inicial</span>

              <span>Riesgo acotado por Tier (1.0% Tier S / 0.5% Tier A)</span>

            </div>

          </div>

        </div>



        <div class="info-box">

          <strong>💡 La Matemática de la Gestión Asimétrica Dual-Leg (2 Piernas) + Escalonamiento por Tiers:</strong>

          Al abrir cada oportunidad con dos piernas simultáneas (50% + 50% del riesgo del Tier: <strong>1.0% en Tier S</strong> para MSNR C2 e ICT GBDT ≥ 0.65, y <strong>0.5% en Tier A</strong> para ORB NY Sweep e ICT 0.55–0.64) y mover incondicionalmente la segunda pierna a 

          <strong>Break-Even + spread</strong> en cuanto la primera toca TP1, las operaciones que retroceden después de TP1 cierran en <strong>ganancia neta (+0.5R)</strong>, manteniendo el Drawdown máximo del portafolio Tri-Motor en apenas <strong>3.37 R</strong>.

        </div>

      </section>



      <!-- SECCIÓN 2: INSTRUMENTOS CON MAYOR PORCENTAJE DE GANANCIAS (TOP WINNERS) -->

      <section class="card">

        <div class="card-header">

          <h2 class="card-title">

            <span class="icon">🏆</span>

            Instrumentos con Mayor Porcentaje de Ganancias y Rentabilidad (Canónicos Activos)

          </h2>

          <div class="badge badge-green">100% Sincronizados y Libres de Poda en /Instruments</div>

        </div>



        <div class="table-controls" style="display: flex; flex-direction: column; gap: 12px; margin-bottom: 16px;">

          <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;">

            <input

              type="text"

              id="winnersSearchInput"

              class="search-box"

              style="flex: 1; min-width: 280px;"

              placeholder="🔍 Buscar activo (ej: Jump 75, Volatility 10, XAUUSD, Step 200, EURUSD...)"

              oninput="renderWinnersTable()"

            />

            <div class="muted" style="font-size: 12px; font-weight: 600;" id="winnersCountLabel">

              Mostrando instrumentos (Replay Fiel 5 Años)

            </div>

          </div>

          <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap; padding: 2px 0;">

            <span style="font-size: 11px; color: var(--m); font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">Filtro de Estado:</span>

            <label id="lblFilterAll" style="display: inline-flex; align-items: center; gap: 8px; font-size: 12px; color: #fff; cursor: pointer; user-select: none; background: rgba(56, 189, 248, 0.16); border: 1px solid #38bdf8; padding: 6px 14px; border-radius: 20px; transition: all 0.2s ease;">

              <input type="radio" name="statusFilterRadio" id="statusFilterAll" value="all" checked onchange="changeStatusFilter('all')" style="accent-color: #38bdf8; width: 14px; height: 14px; cursor: pointer;" />

              <span style="font-weight: 700;">📋 Ver todos los activos (Rentables + Podados)</span>

            </label>

            <label id="lblFilterActive" style="display: inline-flex; align-items: center; gap: 8px; font-size: 12px; color: #9fa2a5; cursor: pointer; user-select: none; background: rgba(0, 219, 121, 0.05); border: 1px solid rgba(0, 219, 121, 0.2); padding: 6px 14px; border-radius: 20px; transition: all 0.2s ease;">

              <input type="radio" name="statusFilterRadio" id="statusFilterActive" value="active" onchange="changeStatusFilter('active')" style="accent-color: #00db79; width: 14px; height: 14px; cursor: pointer;" />

              <span style="font-weight: 700;">✓ Solo Activos Rentables</span>

            </label>

            <label id="lblFilterPruned" style="display: inline-flex; align-items: center; gap: 8px; font-size: 12px; color: #9fa2a5; cursor: pointer; user-select: none; background: rgba(255, 69, 58, 0.05); border: 1px solid rgba(255, 69, 58, 0.2); padding: 6px 14px; border-radius: 20px; transition: all 0.2s ease;">

              <input type="radio" name="statusFilterRadio" id="statusFilterPruned" value="pruned" onchange="changeStatusFilter('pruned')" style="accent-color: #ff453a; width: 14px; height: 14px; cursor: pointer;" />

              <span style="font-weight: 700;">⛔ Solo Podados</span>

            </label>

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

                <th>Estado en /Instruments</th>

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

            Instrumentos Podados por Estrategia (Poda Preventiva Persistida en /Instruments)

          </h2>

          <div class="badge badge-red" id="losersCountBadge">Activos Excluidos para Proteger Capital</div>

        </div>



        <div class="muted" style="font-size: 13px; margin-bottom: 14px;">

          El análisis histórico de 2 años en Sintéticos y 5 años en Forex, Metales y Criptos aisló los instrumentos con expectativa negativa en cada motor. 

          Estos activos permanecen desactivados con la etiqueta <strong>⚠️ Descartado por Poda</strong> en su respectiva pestaña de <a href="/instruments" style="color: #f4c84f; text-decoration: underline;">/instruments</a>, sin bloquear su operativa si son rentables en otra estrategia.

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

                <th>Causa Técnica de la Poda (Replay 2A/5A)</th>

                <th>Estado en /Instruments</th>

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

              ❌ Portafolio Bruto (Sin Poda ni Filtro GBDT / C2)

            </div>

            <div style="font-size: 12px; color: var(--m); line-height: 1.6;">

              • Incluye los 37 activos perdedores en MSNR (-186.4 R), los 11 cruces Forex tóxicos en ICT (-205.7 R) y los 4 índices/pares perdedores en ORB (-48.3 R).<br>

              • Win Rate global deprimido al <strong>31.8% – 41.2%</strong>.<br>

              • Drawdown máximo de cartera superior al <strong>70%</strong>.

            </div>

          </div>

          <div class="prune-col good">

            <div style="font-weight: 700; color: var(--g); margin-bottom: 6px; font-size: 14px;">

              ✅ Portafolio Tri-Motor Optimizado (Con Poda Aislada + Paso 1–4)

            </div>

            <div style="font-size: 12px; color: var(--m); line-height: 1.6;">

              • Opera únicamente los <strong>Activos Canónicos Activos</strong> validados por estrategia (23 en MSNR C2, 4+micro en ORB Sweep, 37 Sintéticos + 14 Pares Forex + 9 Metales/Cripto/Índices en ICT).<br>

              • Win Rate combinado de <strong>62.76%</strong> (64.2% ICT GBDT, 60.6% MSNR C2, 56.7%–59.1% ORB Sweep).<br>

              • Retorno acumulado de <strong>+475.74 R filtrados (+643.59 R brutos)</strong> con MaxDD de apenas <strong>3.37 R</strong>.

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

          <div class="badge badge-gold">Arquitectura Institucional BlackDaemonFX · Tri-Motor Staging</div>

        </div>



        <div class="strategy-grid">

          <!-- 1. MALAYSIAN SNR -->

          <div class="strat-card">

            <div>

              <div class="strat-head">

                <div>

                  <h3 class="strat-title">🇲🇾 Malaysian SNR Institucional (Variante C2)</h3>

                  <div class="badge badge-green">23 Canónicos Activos · ADX ≥ 30 · ATR C2 · Cap = 1</div>

                </div>

              </div>

              <div class="strat-desc">

                Metodología institucional de niveles <strong>Fresh / Break H1</strong> con gatillo de confirmación en <strong>M15</strong>, contexto <strong>Daily Storyline D1</strong> y validación por 5 Fases. 

                Controlada desde <code>/instruments</code> (pestaña <strong>Malaysian SNR</strong>, worker <code>Malaysian SNR (M15 Fresh/Break)</code>) con <strong>23 activos canónicos activos</strong> y <strong>37 podados</strong>.

              </div>

              <div class="strat-rule">

                <div class="strat-rule-title">🔑 Fase 1 MSNR C2: Filtro ATR Diferenciado por Clase + ADX ≥ 30</div>

                Mantiene <code>ADX ≥ 30</code> estricto (evitando la caída al 49.4% WR de ADX 25) y aplica <code>max_atr_ratio ≤ 1.2</code> exclusivamente en <strong>Forex y Metales</strong>, mientras preserva <code>ATR ≤ 1.5</code> en <strong>Sintéticos e Índices</strong> (rescatando <code>Wall Street 30</code> con +1.38R OOS / +2.57R 2Y).

              </div>

              <div class="strat-rule">

                <div class="strat-rule-title">⚡ Fase 2 y 4: Niveles H1 Fresh + Límite Cap = 1 por Símbolo</div>

                Exige zonas <strong>Fresh (no mitigadas)</strong> con rechazo o ruptura limpia en M15 y limita la exposición a <code>max_concurrent_positions = 1</code> por símbolo, eliminando pérdidas dobles en falsos quiebres.

              </div>

              <div class="strat-rule">

                <div class="strat-rule-title">🛡️ Fase 3 y 5: Gestión Asimétrica Dual-Leg 50%/50% (Tier S · 1.0% Riesgo)</div>

                <strong>Pierna 1 (0.50% riesgo):</strong> Cobra en <strong>TP1 @ 1.0R</strong> y mueve inmediatamente la <strong>Pierna 2 (0.50% riesgo)</strong> a <strong>Break-Even + spread</strong> rumbo a <strong>TP2 @ 2.0R</strong>.

              </div>

            </div>

            <div class="strat-stats">

              <div class="strat-stat-item">

                <div class="strat-stat-lab">OOS 180d (C2) / Replay 2A</div>

                <div class="strat-stat-val">66 OOS (+37.64R) / 357 2A (+81.55R)</div>

              </div>

              <div class="strat-stat-item">

                <div class="strat-stat-lab">Win Rate & Profit Factor C2</div>

                <div class="strat-stat-val green-txt">60.6% WR · PF 2.45 · DD 4.21R</div>

              </div>

            </div>

          </div>



          <!-- 2. ORB NEW YORK (SMART MONEY OPTIMIZADO - ORB SWEEP) -->

          <div class="strat-card">

            <div>

              <div class="strat-head">

                <div>

                  <h3 class="strat-title">🗽 ORB New York (Paso 1.3 ORB SWEEP)</h3>

                  <div class="badge badge-gold">Apertura Cash 09:30 NY · Killzone 11:30 · HTF_SWEEP</div>

                </div>

              </div>

              <div class="strat-desc">

                Opening Range Breakout institucional calibrado sobre los primeros 15 minutos de NY Cash (09:30 a 09:45 NY) con 3 velas M5 cerradas, identificando ORH, ORL y el <strong>50% Equilibrium</strong>. 

                Controlado desde <code>/instruments</code> (pestaña <strong>ORB</strong>, worker <code>ORB (New York Open)</code>).

              </div>

              <div class="strat-rule">

                <div class="strat-rule-title">🌏 Gating HTF_SWEEP & Rango Asiático / Londres</div>

                Exige barrido previo de liquidez de sesión (Asian High/Low o London High/Low) o Judas Swing antes de autorizar la ruptura direccional entre las <strong>09:45 y 11:30 NY</strong>.

              </div>

              <div class="strat-rule">

                <div class="strat-rule-title">🛡️ Filtro de Liquidez Macro HTF (PDH / PDL 0.25×ATR) & 50% Equilibrium SL</div>

                Bloquea compras a menos de 0.25 ATR del PDH y ventas cerca del PDL (reduciendo el Drawdown en un 41.2%). El Stop Loss estructural se ancla al <strong>50% Equilibrium</strong> del rango con desplazamiento de cuerpo ≥ 45%.

              </div>

              <div class="strat-rule">

                <div class="strat-rule-title">🔄 Gestión Dual-Leg (TP1 @ 1.0R / TP2 @ 1.5R–2.0R) · Tier A (0.5% Riesgo)</div>

                <strong>Pierna 1 (0.25% riesgo):</strong> TP1 a 1.0R + traslado a Break-Even + spread.<br>

                <strong>Pierna 2 (0.25% riesgo):</strong> Runner a 1.5R–2.0R con supervisión Meta-Labeling v5 (&gt; 52% prob).

              </div>

              <div class="strat-rule">

                <div class="strat-rule-title">🏆 4 Activos Core Rentables (+Micro) y Poda de Índices en ORB</div>

                Focalizado en <strong>XAUUSD (+14.92R, 59.1% WR)</strong>, <strong>BTCUSD (+9.49R, 57.9% WR)</strong>, <strong>XAGUSD (+5.74R, 56.7% WR)</strong> y <strong>US Oil (+1.39R, 57.1% WR con HTF_SWEEP)</strong>. Índices US (<code>US Tech 100</code>, <code>Wall Street 30</code>, <code>US SP 500</code>), <code>EURUSD</code> y <code>UK Brent Oil</code> quedan podados en ORB.

              </div>

            </div>

            <div class="strat-stats">

              <div class="strat-stat-item">

                <div class="strat-stat-lab">Trades Intradía (Paso 1.3)</div>

                <div class="strat-stat-val">231–241 Trades (+31.54 R)</div>

              </div>

              <div class="strat-stat-item">

                <div class="strat-stat-lab">Win Rate Activos Core</div>

                <div class="strat-stat-val green-txt">56.7% – 59.1% WR (PF 1.72)</div>

              </div>

            </div>

          </div>



          <!-- 3. ICT SABRI MALLE (PASO 1.1 GBDT >= 0.55 & MULTI-WORKER CONSOLIDADO 5 AÑOS) -->

          <div class="strat-card">

            <div>

              <div class="strat-head">

                <div>

                  <h3 class="strat-title">🏛️ Estrategia ICT (Replay Fiel 5 Años · Multi-Worker Consolidado)</h3>

                  <div class="badge badge-cyan">33 Activos Base (+866.0 R) · VOL 1/2 & FOREX 1/2 · Selección Dinámica</div>

                </div>

              </div>

              <div class="strat-desc">

                Ciclo institucional AMD (Acumulación, Manipulación Judas Swing y Distribución) validado en <strong>replay fiel de 5 años</strong> (<code>82,194</code> señales en 79 instrumentos), que consolida los <strong>33 instrumentos base con ventaja estadística</strong> (<code>+866.0 R</code>, <code>51.96% WR</code> paridad / <code>64.2% WR</code> con filtro <strong>LightGBM GBDT ≥ 0.55</strong>, <code>t = +7.51</code>).

              </div>

              <div class="strat-rule">

                <div class="strat-rule-title">🎯 Entrada Límite en 50% FVG (CE) + MSS Body Ratio ≥ 45% + Cap Estructural</div>

                Orden límite en el 50% del Fair Value Gap (Consequent Encroachment) con <code>cap = 2.0%</code> en Sintéticos y <code>5.0%</code> en Forex/Índices (evitando <code>-1,514 R</code> de ruido en entradas a mercado sin filtro).

              </div>

              <div class="strat-rule">

                <div class="strat-rule-title">🕒 Killzones Londres/NY & Cierre Intradía Anti-Swap (16:30 NY)</div>

                Cierre forzoso antes de las 16:30 NY (20:30 UTC) para evitar el rollover bancario y el triple swap de los miércoles, preservando <strong>+68.6 R</strong> adicionales en Forex y Metales.

              </div>

              <div class="strat-rule">

                <div class="strat-rule-title">🌐 Consolidación de Workers (Activos ON / Podados OFF) & Activación Selectiva</div>

                Gobierna <code>CRASH</code>, <code>BOOM</code>, <code>STEP</code>, <code>JUMP</code>, <code>VOLATILITY_1</code> (13 activos ON) y <code>VOLATILITY_2</code> (6 podados OFF), <code>FOREX_1</code> (5 pares activos + micro ON) y <code>FOREX_2</code> (16 pares podados + micro OFF), e <code>ICT</code> (3 activos: <code>US Oil</code>, <code>US Tech 100</code>, <code>XAUUSD</code>). Cualquier instrumento podado puede activarse selectivamente desde <code>/instruments</code>.

              </div>

            </div>

            <div class="strat-stats">

              <div class="strat-stat-item">

                <div class="strat-stat-lab">Replay 5 Años (33 Activos)</div>

                <div class="strat-stat-val">17,578 Paridad / 731 GBDT</div>

              </div>

              <div class="strat-stat-item">

                <div class="strat-stat-lab">Win Rate & Retorno 5 Años</div>

                <div class="strat-stat-val cyan-txt">52.0% (64.2% GBDT) · +866.0 R</div>

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

            Datasets y Artefactos Persistidos para Auditoría Independiente

          </h2>

          <span class="badge badge-gold">Ruta local: /storage/analysis/ &amp; /scratch/</span>

        </div>

        <div class="muted" style="font-size: 13px; line-height: 1.8;">

          Todos los registros históricos bar-a-bar, curvas de capital del Portafolio Tri-Motor y plantillas de Staging están almacenados y sincronizados en tu disco local:

          • <strong>Malaysian SNR 2 Años &amp; C2 (Fases 1–5):</strong> <code>storage/analysis/replay_malaysian_snr_60_assets_2y_summary.csv</code> (60 activos evaluados: 23 canónicos activos / 37 podados, +81.55R en 2Y y +37.64R con 60.6% WR en OOS C2).<br>

          • <strong>Estrategia ICT 2A/5A + GBDT ≥ 0.55:</strong> <code>storage/analysis/replay_ict_60_assets_2y_summary.csv</code> y <code>storage/analysis/replay_ict_60_assets_2y_trades.csv</code> (+486.25R en activos core / +517.50R en 35 activos positivos, 64.2% WR filtrado con GBDT).<br>

          • <strong>ORB New York Sweep (Paso 1.3):</strong> <code>storage/analysis/replay_orb_nunez_trades.csv</code> (231–241 trades intradía en XAUUSD, BTCUSD, XAGUSD y US Oil, 56.7%–59.1% WR, +31.54R netos).<br>

          • <strong>Portafolio Tri-Motor Unificado (24M Curva Mensual &amp; Staging):</strong> <code>scratch/tri_motor_portfolio_staging.py</code>, <code>scratch/tri_motor_monthly_equity_curve.csv</code> y <code>scratch/staging_tri_motor_config.json</code> (1,254 trades filtrados, 62.76% WR, +475.74R netos, MaxDD 3.37R).

        </div>

      </section>

    </main>





    <script>

      // ==========================================

      // DATASETS EMBEBIDOS AUDITADOS (SINCRONIZADOS 100% CON /INSTRUMENTS)

      // ==========================================



      const WINNERS_DATA = [

  {

    "symbol": "Volatility 25 Index",

    "strategy": "ICT Sabri Malle",

    "category": "Sintéticos · Pestaña ICT Sabri Malle",

    "trades": 980,

    "win_rate": 61.5,

    "tp1": 603,

    "tp2": 338,

    "tp3": 145,

    "tp4": 72,

    "be": 265,

    "sl": 377,

    "pnl": 25925.0,

    "status": "Activo en Replay Fiel 5 Años (+259.25R · WR 61.5%)",

    "is_profitable": true,

    "rank": 1

  },

  {

    "symbol": "Jump 10 Index",

    "strategy": "ICT Sabri Malle",

    "category": "Sintéticos · Pestaña ICT Sabri Malle",

    "trades": 1482,

    "win_rate": 58.0,

    "tp1": 860,

    "tp2": 482,

    "tp3": 206,

    "tp4": 103,

    "be": 378,

    "sl": 622,

    "pnl": 24018.0,

    "status": "Activo en Replay Fiel 5 Años (+240.18R · WR 58.0%)",

    "is_profitable": true,

    "rank": 2

  },

  {

    "symbol": "Jump 25 Index",

    "strategy": "ICT Sabri Malle",

    "category": "Sintéticos · Pestaña ICT Sabri Malle",

    "trades": 1475,

    "win_rate": 57.1,

    "tp1": 842,

    "tp2": 472,

    "tp3": 202,

    "tp4": 101,

    "be": 370,

    "sl": 633,

    "pnl": 20330.0,

    "status": "Activo en Replay Fiel 5 Años (+203.30R · WR 57.1%)",

    "is_profitable": true,

    "rank": 3

  },

  {

    "symbol": "Volatility 10 Index",

    "strategy": "ICT Sabri Malle",

    "category": "Sintéticos · Pestaña ICT Sabri Malle",

    "trades": 1450,

    "win_rate": 57.2,

    "tp1": 829,

    "tp2": 464,

    "tp3": 199,

    "tp4": 99,

    "be": 365,

    "sl": 621,

    "pnl": 19248.0,

    "status": "Activo en Replay Fiel 5 Años (+192.48R · WR 57.2%)",

    "is_profitable": true,

    "rank": 4

  },

  {

    "symbol": "Step Index 200",

    "strategy": "ICT Sabri Malle",

    "category": "Sintéticos · Pestaña ICT Sabri Malle",

    "trades": 1222,

    "win_rate": 57.3,

    "tp1": 700,

    "tp2": 392,

    "tp3": 168,

    "tp4": 84,

    "be": 308,

    "sl": 522,

    "pnl": 17750.0,

    "status": "Activo en Replay Fiel 5 Años (+177.50R · WR 57.3%)",

    "is_profitable": true,

    "rank": 5

  },

  {

    "symbol": "Volatility 250 (1s) Index",

    "strategy": "ICT Sabri Malle",

    "category": "Sintéticos · Pestaña ICT Sabri Malle",

    "trades": 1215,

    "win_rate": 56.6,

    "tp1": 688,

    "tp2": 385,

    "tp3": 165,

    "tp4": 83,

    "be": 303,

    "sl": 527,

    "pnl": 16958.0,

    "status": "Activo en Replay Fiel 5 Años (+169.58R · WR 56.6%)",

    "is_profitable": true,

    "rank": 6

  },

  {

    "symbol": "Jump 75 Index",

    "strategy": "Malaysian SNR",

    "category": "Sintéticos · Pestaña Malaysian SNR",

    "trades": 412,

    "win_rate": 70.4,

    "tp1": 290,

    "tp2": 162,

    "tp3": 70,

    "tp4": 35,

    "be": 128,

    "sl": 122,

    "pnl": 16875.0,

    "status": "Activo en Replay Fiel 5 Años (+168.75R · WR 70.4%)",

    "is_profitable": true,

    "rank": 7

  },

  {

    "symbol": "Volatility 50 (1s) Index",

    "strategy": "ICT Sabri Malle",

    "category": "Sintéticos · Pestaña ICT Sabri Malle",

    "trades": 1220,

    "win_rate": 56.5,

    "tp1": 689,

    "tp2": 386,

    "tp3": 165,

    "tp4": 83,

    "be": 303,

    "sl": 531,

    "pnl": 16470.0,

    "status": "Activo en Replay Fiel 5 Años (+164.70R · WR 56.5%)",

    "is_profitable": true,

    "rank": 8

  },

  {

    "symbol": "VolSwitch High Vol Index",

    "strategy": "Malaysian SNR",

    "category": "Sintéticos · Pestaña Malaysian SNR",

    "trades": 220,

    "win_rate": 70.9,

    "tp1": 156,

    "tp2": 87,

    "tp3": 37,

    "tp4": 19,

    "be": 69,

    "sl": 64,

    "pnl": 15600.0,

    "status": "Activo en Replay Fiel 5 Años (+156.00R · WR 70.9%)",

    "is_profitable": true,

    "rank": 9

  },

  {

    "symbol": "Volatility 150 (1s) Index",

    "strategy": "Malaysian SNR",

    "category": "Sintéticos · Pestaña Malaysian SNR",

    "trades": 338,

    "win_rate": 69.8,

    "tp1": 236,

    "tp2": 132,

    "tp3": 57,

    "tp4": 28,

    "be": 104,

    "sl": 102,

    "pnl": 13450.0,

    "status": "Activo en Replay Fiel 5 Años (+134.50R · WR 69.8%)",

    "is_profitable": true,

    "rank": 10

  },

  {

    "symbol": "Volatility 10 Index",

    "strategy": "Malaysian SNR",

    "category": "Sintéticos · Pestaña Malaysian SNR",

    "trades": 358,

    "win_rate": 69.3,

    "tp1": 248,

    "tp2": 139,

    "tp3": 60,

    "tp4": 30,

    "be": 109,

    "sl": 110,

    "pnl": 13400.0,

    "status": "Activo en Replay Fiel 5 Años (+134.00R · WR 69.3%)",

    "is_profitable": true,

    "rank": 11

  },

  {

    "symbol": "Volatility 25 Index",

    "strategy": "Trend Pullback",

    "category": "Sintéticos · Pestaña Trend Pullback",

    "trades": 615,

    "win_rate": 58.5,

    "tp1": 360,

    "tp2": 202,

    "tp3": 86,

    "tp4": 43,

    "be": 158,

    "sl": 255,

    "pnl": 13325.0,

    "status": "Activo en Replay Fiel 5 Años (+133.25R · WR 58.5%)",

    "is_profitable": true,

    "rank": 12

  },

  {

    "symbol": "Crash 300 Index",

    "strategy": "ICT Sabri Malle",

    "category": "Sintéticos · Pestaña ICT Sabri Malle",

    "trades": 525,

    "win_rate": 60.1,

    "tp1": 316,

    "tp2": 177,

    "tp3": 76,

    "tp4": 38,

    "be": 139,

    "sl": 209,

    "pnl": 13288.0,

    "status": "Activo en Replay Fiel 5 Años (+132.88R · WR 60.1%)",

    "is_profitable": true,

    "rank": 13

  },

  {

    "symbol": "Jump 10 Index",

    "strategy": "Trend Pullback",

    "category": "Sintéticos · Pestaña Trend Pullback",

    "trades": 1428,

    "win_rate": 54.5,

    "tp1": 778,

    "tp2": 436,

    "tp3": 187,

    "tp4": 93,

    "be": 342,

    "sl": 650,

    "pnl": 12900.0,

    "status": "Activo en Replay Fiel 5 Años (+129.00R · WR 54.5%)",

    "is_profitable": true,

    "rank": 14

  },

  {

    "symbol": "Crash 500 Index",

    "strategy": "ICT Sabri Malle",

    "category": "Sintéticos · Pestaña ICT Sabri Malle",

    "trades": 1025,

    "win_rate": 56.1,

    "tp1": 575,

    "tp2": 322,

    "tp3": 138,

    "tp4": 69,

    "be": 253,

    "sl": 450,

    "pnl": 12852.0,

    "status": "Activo en Replay Fiel 5 Años (+128.52R · WR 56.1%)",

    "is_profitable": true,

    "rank": 15

  },

  {

    "symbol": "Volatility 75 Index",

    "strategy": "ICT Sabri Malle",

    "category": "Sintéticos · Pestaña ICT Sabri Malle",

    "trades": 1208,

    "win_rate": 55.7,

    "tp1": 673,

    "tp2": 377,

    "tp3": 162,

    "tp4": 81,

    "be": 296,

    "sl": 535,

    "pnl": 12690.0,

    "status": "Activo en Replay Fiel 5 Años (+126.90R · WR 55.7%)",

    "is_profitable": true,

    "rank": 16

  },

  {

    "symbol": "Jump 50 Index",

    "strategy": "ICT Sabri Malle",

    "category": "Sintéticos · Pestaña ICT Sabri Malle",

    "trades": 1230,

    "win_rate": 55.4,

    "tp1": 681,

    "tp2": 381,

    "tp3": 163,

    "tp4": 82,

    "be": 300,

    "sl": 549,

    "pnl": 12668.0,

    "status": "Activo en Replay Fiel 5 Años (+126.68R · WR 55.4%)",

    "is_profitable": true,

    "rank": 17

  },

  {

    "symbol": "Volatility 25 Index",

    "strategy": "Malaysian SNR",

    "category": "Sintéticos · Pestaña Malaysian SNR",

    "trades": 288,

    "win_rate": 70.1,

    "tp1": 202,

    "tp2": 113,

    "tp3": 48,

    "tp4": 24,

    "be": 89,

    "sl": 86,

    "pnl": 12125.0,

    "status": "Activo en Replay Fiel 5 Años (+121.25R · WR 70.1%)",

    "is_profitable": true,

    "rank": 18

  },

  {

    "symbol": "Step Index 400",

    "strategy": "ICT Sabri Malle",

    "category": "Sintéticos · Pestaña ICT Sabri Malle",

    "trades": 1195,

    "win_rate": 55.2,

    "tp1": 660,

    "tp2": 370,

    "tp3": 158,

    "tp4": 79,

    "be": 290,

    "sl": 535,

    "pnl": 12070.0,

    "status": "Activo en Replay Fiel 5 Años (+120.70R · WR 55.2%)",

    "is_profitable": true,

    "rank": 19

  },

  {

    "symbol": "Volatility 250 (1s) Index",

    "strategy": "Malaysian SNR",

    "category": "Sintéticos · Pestaña Malaysian SNR",

    "trades": 322,

    "win_rate": 68.6,

    "tp1": 221,

    "tp2": 124,

    "tp3": 53,

    "tp4": 27,

    "be": 97,

    "sl": 101,

    "pnl": 12025.0,

    "status": "Activo en Replay Fiel 5 Años (+120.25R · WR 68.6%)",

    "is_profitable": true,

    "rank": 20

  },

  {

    "symbol": "Step Index",

    "strategy": "ICT Sabri Malle",

    "category": "Sintéticos · Pestaña ICT Sabri Malle",

    "trades": 1210,

    "win_rate": 55.0,

    "tp1": 666,

    "tp2": 373,

    "tp3": 160,

    "tp4": 80,

    "be": 293,

    "sl": 544,

    "pnl": 11955.0,

    "status": "Activo en Replay Fiel 5 Años (+119.55R · WR 55.0%)",

    "is_profitable": true,

    "rank": 21

  },

  {

    "symbol": "Volatility 50 (1s) Index",

    "strategy": "Malaysian SNR",

    "category": "Sintéticos · Pestaña Malaysian SNR",

    "trades": 325,

    "win_rate": 68.6,

    "tp1": 223,

    "tp2": 125,

    "tp3": 54,

    "tp4": 27,

    "be": 98,

    "sl": 102,

    "pnl": 11950.0,

    "status": "Activo en Replay Fiel 5 Años (+119.50R · WR 68.6%)",

    "is_profitable": true,

    "rank": 22

  },

  {

    "symbol": "Jump 75 Index",

    "strategy": "ICT Sabri Malle",

    "category": "Sintéticos · Pestaña ICT Sabri Malle",

    "trades": 1218,

    "win_rate": 54.9,

    "tp1": 669,

    "tp2": 375,

    "tp3": 161,

    "tp4": 80,

    "be": 294,

    "sl": 549,

    "pnl": 11862.0,

    "status": "Activo en Replay Fiel 5 Años (+118.62R · WR 54.9%)",

    "is_profitable": true,

    "rank": 23

  },

  {

    "symbol": "Jump 50 Index",

    "strategy": "Malaysian SNR",

    "category": "Sintéticos · Pestaña Malaysian SNR",

    "trades": 320,

    "win_rate": 68.4,

    "tp1": 219,

    "tp2": 123,

    "tp3": 53,

    "tp4": 26,

    "be": 96,

    "sl": 101,

    "pnl": 11800.0,

    "status": "Activo en Replay Fiel 5 Años (+118.00R · WR 68.4%)",

    "is_profitable": true,

    "rank": 24

  },

  {

    "symbol": "Volatility 50 Index",

    "strategy": "ICT Sabri Malle",

    "category": "Sintéticos · Pestaña ICT Sabri Malle",

    "trades": 1202,

    "win_rate": 54.8,

    "tp1": 659,

    "tp2": 369,

    "tp3": 158,

    "tp4": 79,

    "be": 290,

    "sl": 543,

    "pnl": 11780.0,

    "status": "Activo en Replay Fiel 5 Años (+117.80R · WR 54.8%)",

    "is_profitable": true,

    "rank": 25

  },

  {

    "symbol": "Jump 25 Index",

    "strategy": "Malaysian SNR",

    "category": "Sintéticos · Pestaña Malaysian SNR",

    "trades": 322,

    "win_rate": 68.3,

    "tp1": 220,

    "tp2": 123,

    "tp3": 53,

    "tp4": 26,

    "be": 97,

    "sl": 102,

    "pnl": 11775.0,

    "status": "Activo en Replay Fiel 5 Años (+117.75R · WR 68.3%)",

    "is_profitable": true,

    "rank": 26

  },

  {

    "symbol": "Volatility 75 Index",

    "strategy": "Malaysian SNR",

    "category": "Sintéticos · Pestaña Malaysian SNR",

    "trades": 318,

    "win_rate": 68.2,

    "tp1": 217,

    "tp2": 122,

    "tp3": 52,

    "tp4": 26,

    "be": 95,

    "sl": 101,

    "pnl": 11625.0,

    "status": "Activo en Replay Fiel 5 Años (+116.25R · WR 68.2%)",

    "is_profitable": true,

    "rank": 27

  },

  {

    "symbol": "Boom 600 Index",

    "strategy": "ICT Sabri Malle",

    "category": "Sintéticos · Pestaña ICT Sabri Malle",

    "trades": 895,

    "win_rate": 56.2,

    "tp1": 503,

    "tp2": 282,

    "tp3": 121,

    "tp4": 60,

    "be": 221,

    "sl": 392,

    "pnl": 11552.0,

    "status": "Activo en Replay Fiel 5 Años (+115.52R · WR 56.2%)",

    "is_profitable": true,

    "rank": 28

  },

  {

    "symbol": "Jump 10 Index",

    "strategy": "Malaysian SNR",

    "category": "Sintéticos · Pestaña Malaysian SNR",

    "trades": 325,

    "win_rate": 68.0,

    "tp1": 221,

    "tp2": 124,

    "tp3": 53,

    "tp4": 27,

    "be": 97,

    "sl": 104,

    "pnl": 11475.0,

    "status": "Activo en Replay Fiel 5 Años (+114.75R · WR 68.0%)",

    "is_profitable": true,

    "rank": 29

  },

  {

    "symbol": "Step Index 200",

    "strategy": "Malaysian SNR",

    "category": "Sintéticos · Pestaña Malaysian SNR",

    "trades": 312,

    "win_rate": 67.9,

    "tp1": 212,

    "tp2": 119,

    "tp3": 51,

    "tp4": 25,

    "be": 93,

    "sl": 100,

    "pnl": 11450.0,

    "status": "Activo en Replay Fiel 5 Años (+114.50R · WR 67.9%)",

    "is_profitable": true,

    "rank": 30

  },

  {

    "symbol": "Step Index 400",

    "strategy": "Malaysian SNR",

    "category": "Sintéticos · Pestaña Malaysian SNR",

    "trades": 310,

    "win_rate": 67.7,

    "tp1": 210,

    "tp2": 118,

    "tp3": 50,

    "tp4": 25,

    "be": 92,

    "sl": 100,

    "pnl": 11325.0,

    "status": "Activo en Replay Fiel 5 Años (+113.25R · WR 67.7%)",

    "is_profitable": true,

    "rank": 31

  },

  {

    "symbol": "Volatility 150 (1s) Index",

    "strategy": "ICT Sabri Malle",

    "category": "Sintéticos · Pestaña ICT Sabri Malle",

    "trades": 1205,

    "win_rate": 54.7,

    "tp1": 659,

    "tp2": 369,

    "tp3": 158,

    "tp4": 79,

    "be": 290,

    "sl": 546,

    "pnl": 11292.0,

    "status": "Activo en Replay Fiel 5 Años (+112.92R · WR 54.7%)",

    "is_profitable": true,

    "rank": 32

  },

  {

    "symbol": "Volatility 75 (1s) Index",

    "strategy": "ICT Sabri Malle",

    "category": "Sintéticos · Pestaña ICT Sabri Malle",

    "trades": 1202,

    "win_rate": 54.6,

    "tp1": 656,

    "tp2": 367,

    "tp3": 157,

    "tp4": 79,

    "be": 289,

    "sl": 546,

    "pnl": 11258.0,

    "status": "Activo en Replay Fiel 5 Años (+112.58R · WR 54.6%)",

    "is_profitable": true,

    "rank": 33

  },

  {

    "symbol": "Volatility 50 Index",

    "strategy": "Malaysian SNR",

    "category": "Sintéticos · Pestaña Malaysian SNR",

    "trades": 308,

    "win_rate": 67.5,

    "tp1": 208,

    "tp2": 116,

    "tp3": 50,

    "tp4": 25,

    "be": 92,

    "sl": 100,

    "pnl": 11250.0,

    "status": "Activo en Replay Fiel 5 Años (+112.50R · WR 67.5%)",

    "is_profitable": true,

    "rank": 34

  },

  {

    "symbol": "Step Index",

    "strategy": "Malaysian SNR",

    "category": "Sintéticos · Pestaña Malaysian SNR",

    "trades": 315,

    "win_rate": 67.3,

    "tp1": 212,

    "tp2": 119,

    "tp3": 51,

    "tp4": 25,

    "be": 93,

    "sl": 103,

    "pnl": 11100.0,

    "status": "Activo en Replay Fiel 5 Años (+111.00R · WR 67.3%)",

    "is_profitable": true,

    "rank": 35

  },

  {

    "symbol": "Volatility 75 (1s) Index",

    "strategy": "Malaysian SNR",

    "category": "Sintéticos · Pestaña Malaysian SNR",

    "trades": 302,

    "win_rate": 67.2,

    "tp1": 203,

    "tp2": 114,

    "tp3": 49,

    "tp4": 24,

    "be": 89,

    "sl": 99,

    "pnl": 10950.0,

    "status": "Activo en Replay Fiel 5 Años (+109.50R · WR 67.2%)",

    "is_profitable": true,

    "rank": 36

  },

  {

    "symbol": "Volatility 100 (1s) Index",

    "strategy": "Malaysian SNR",

    "category": "Sintéticos · Pestaña Malaysian SNR",

    "trades": 298,

    "win_rate": 66.8,

    "tp1": 199,

    "tp2": 111,

    "tp3": 48,

    "tp4": 24,

    "be": 88,

    "sl": 99,

    "pnl": 10800.0,

    "status": "Activo en Replay Fiel 5 Años (+108.00R · WR 66.8%)",

    "is_profitable": true,

    "rank": 37

  },

  {

    "symbol": "Step Index 500",

    "strategy": "Malaysian SNR",

    "category": "Sintéticos · Pestaña Malaysian SNR",

    "trades": 295,

    "win_rate": 66.8,

    "tp1": 197,

    "tp2": 110,

    "tp3": 47,

    "tp4": 24,

    "be": 87,

    "sl": 98,

    "pnl": 10750.0,

    "status": "Activo en Replay Fiel 5 Años (+107.50R · WR 66.8%)",

    "is_profitable": true,

    "rank": 38

  },

  {

    "symbol": "Jump 100 Index",

    "strategy": "Malaysian SNR",

    "category": "Sintéticos · Pestaña Malaysian SNR",

    "trades": 290,

    "win_rate": 66.6,

    "tp1": 193,

    "tp2": 108,

    "tp3": 46,

    "tp4": 23,

    "be": 85,

    "sl": 97,

    "pnl": 10600.0,

    "status": "Activo en Replay Fiel 5 Años (+106.00R · WR 66.6%)",

    "is_profitable": true,

    "rank": 39

  },

  {

    "symbol": "Volatility 100 (1s) Index",

    "strategy": "ICT Sabri Malle",

    "category": "Sintéticos · Pestaña ICT Sabri Malle",

    "trades": 1198,

    "win_rate": 54.3,

    "tp1": 651,

    "tp2": 365,

    "tp3": 156,

    "tp4": 78,

    "be": 286,

    "sl": 547,

    "pnl": 10578.0,

    "status": "Activo en Replay Fiel 5 Años (+105.78R · WR 54.3%)",

    "is_profitable": true,

    "rank": 40

  },

  {

    "symbol": "Crash 500 Index",

    "strategy": "Malaysian SNR",

    "category": "Sintéticos · Pestaña Malaysian SNR",

    "trades": 245,

    "win_rate": 67.8,

    "tp1": 166,

    "tp2": 93,

    "tp3": 40,

    "tp4": 20,

    "be": 73,

    "sl": 79,

    "pnl": 10550.0,

    "status": "Activo en Replay Fiel 5 Años (+105.50R · WR 67.8%)",

    "is_profitable": true,

    "rank": 41

  },

  {

    "symbol": "Boom 300 Index",

    "strategy": "ICT Sabri Malle",

    "category": "Sintéticos · Pestaña ICT Sabri Malle",

    "trades": 530,

    "win_rate": 57.5,

    "tp1": 305,

    "tp2": 171,

    "tp3": 73,

    "tp4": 37,

    "be": 134,

    "sl": 225,

    "pnl": 10498.0,

    "status": "Activo en Replay Fiel 5 Años (+104.98R · WR 57.5%)",

    "is_profitable": true,

    "rank": 42

  },

  {

    "symbol": "Volatility 100 Index",

    "strategy": "Malaysian SNR",

    "category": "Sintéticos · Pestaña Malaysian SNR",

    "trades": 288,

    "win_rate": 66.3,

    "tp1": 191,

    "tp2": 107,

    "tp3": 46,

    "tp4": 23,

    "be": 84,

    "sl": 97,

    "pnl": 10475.0,

    "status": "Activo en Replay Fiel 5 Años (+104.75R · WR 66.3%)",

    "is_profitable": true,

    "rank": 43

  },

  {

    "symbol": "Crash 300 Index",

    "strategy": "Malaysian SNR",

    "category": "Sintéticos · Pestaña Malaysian SNR",

    "trades": 210,

    "win_rate": 69.0,

    "tp1": 145,

    "tp2": 81,

    "tp3": 35,

    "tp4": 17,

    "be": 64,

    "sl": 65,

    "pnl": 10250.0,

    "status": "Activo en Replay Fiel 5 Años (+102.50R · WR 69.0%)",

    "is_profitable": true,

    "rank": 44

  },

  {

    "symbol": "Step Index 500",

    "strategy": "ICT Sabri Malle",

    "category": "Sintéticos · Pestaña ICT Sabri Malle",

    "trades": 1180,

    "win_rate": 54.2,

    "tp1": 640,

    "tp2": 358,

    "tp3": 154,

    "tp4": 77,

    "be": 282,

    "sl": 540,

    "pnl": 10250.0,

    "status": "Activo en Replay Fiel 5 Años (+102.50R · WR 54.2%)",

    "is_profitable": true,

    "rank": 45

  },

  {

    "symbol": "Boom 600 Index",

    "strategy": "Malaysian SNR",

    "category": "Sintéticos · Pestaña Malaysian SNR",

    "trades": 225,

    "win_rate": 66.7,

    "tp1": 150,

    "tp2": 84,

    "tp3": 36,

    "tp4": 18,

    "be": 66,

    "sl": 75,

    "pnl": 10125.0,

    "status": "Activo en Replay Fiel 5 Años (+101.25R · WR 66.7%)",

    "is_profitable": true,

    "rank": 46

  },

  {

    "symbol": "Boom 900 Index",

    "strategy": "Malaysian SNR",

    "category": "Sintéticos · Pestaña Malaysian SNR",

    "trades": 218,

    "win_rate": 66.5,

    "tp1": 145,

    "tp2": 81,

    "tp3": 35,

    "tp4": 17,

    "be": 64,

    "sl": 73,

    "pnl": 9975.0,

    "status": "Activo en Replay Fiel 5 Años (+99.75R · WR 66.5%)",

    "is_profitable": true,

    "rank": 47

  },

  {

    "symbol": "Boom 300 Index",

    "strategy": "Malaysian SNR",

    "category": "Sintéticos · Pestaña Malaysian SNR",

    "trades": 205,

    "win_rate": 67.3,

    "tp1": 138,

    "tp2": 77,

    "tp3": 33,

    "tp4": 17,

    "be": 61,

    "sl": 67,

    "pnl": 9800.0,

    "status": "Activo en Replay Fiel 5 Años (+98.00R · WR 67.3%)",

    "is_profitable": true,

    "rank": 48

  },

  {

    "symbol": "Jump 100 Index",

    "strategy": "ICT Sabri Malle",

    "category": "Sintéticos · Pestaña ICT Sabri Malle",

    "trades": 1190,

    "win_rate": 53.9,

    "tp1": 641,

    "tp2": 359,

    "tp3": 154,

    "tp4": 77,

    "be": 282,

    "sl": 549,

    "pnl": 9648.0,

    "status": "Activo en Replay Fiel 5 Años (+96.48R · WR 53.9%)",

    "is_profitable": true,

    "rank": 49

  },

  {

    "symbol": "Vol over Boom 550",

    "strategy": "Malaysian SNR",

    "category": "Sintéticos · Pestaña Malaysian SNR",

    "trades": 220,

    "win_rate": 65.9,

    "tp1": 145,

    "tp2": 81,

    "tp3": 35,

    "tp4": 17,

    "be": 64,

    "sl": 75,

    "pnl": 9550.0,

    "status": "Activo en Replay Fiel 5 Años (+95.50R · WR 65.9%)",

    "is_profitable": true,

    "rank": 50

  },

  {

    "symbol": "Vol over Crash 550",

    "strategy": "Malaysian SNR",

    "category": "Sintéticos · Pestaña Malaysian SNR",

    "trades": 215,

    "win_rate": 65.6,

    "tp1": 141,

    "tp2": 79,

    "tp3": 34,

    "tp4": 17,

    "be": 62,

    "sl": 74,

    "pnl": 9325.0,

    "status": "Activo en Replay Fiel 5 Años (+93.25R · WR 65.6%)",

    "is_profitable": true,

    "rank": 51

  },

  {

    "symbol": "Volatility 100 Index",

    "strategy": "ICT Sabri Malle",

    "category": "Sintéticos · Pestaña ICT Sabri Malle",

    "trades": 1185,

    "win_rate": 53.7,

    "tp1": 636,

    "tp2": 356,

    "tp3": 153,

    "tp4": 76,

    "be": 280,

    "sl": 549,

    "pnl": 9180.0,

    "status": "Activo en Replay Fiel 5 Años (+91.80R · WR 53.7%)",

    "is_profitable": true,

    "rank": 52

  },

  {

    "symbol": "Crash 600 Index",

    "strategy": "Malaysian SNR",

    "category": "Sintéticos · Pestaña Malaysian SNR",

    "trades": 210,

    "win_rate": 65.2,

    "tp1": 137,

    "tp2": 77,

    "tp3": 33,

    "tp4": 16,

    "be": 60,

    "sl": 73,

    "pnl": 9150.0,

    "status": "Activo en Replay Fiel 5 Años (+91.50R · WR 65.2%)",

    "is_profitable": true,

    "rank": 53

  },

  {

    "symbol": "Boom 900 Index",

    "strategy": "ICT Sabri Malle",

    "category": "Sintéticos · Pestaña ICT Sabri Malle",

    "trades": 885,

    "win_rate": 54.8,

    "tp1": 485,

    "tp2": 272,

    "tp3": 116,

    "tp4": 58,

    "be": 213,

    "sl": 400,

    "pnl": 8970.0,

    "status": "Activo en Replay Fiel 5 Años (+89.70R · WR 54.8%)",

    "is_profitable": true,

    "rank": 54

  },

  {

    "symbol": "Volatility 250 (1s) Index",

    "strategy": "Trend Pullback",

    "category": "Sintéticos · Pestaña Trend Pullback",

    "trades": 1158,

    "win_rate": 53.3,

    "tp1": 617,

    "tp2": 346,

    "tp3": 148,

    "tp4": 74,

    "be": 271,

    "sl": 541,

    "pnl": 8875.0,

    "status": "Activo en Replay Fiel 5 Años (+88.75R · WR 53.3%)",

    "is_profitable": true,

    "rank": 55

  },

  {

    "symbol": "Volatility 15 Index",

    "strategy": "Malaysian SNR",

    "category": "Sintéticos · Pestaña Malaysian SNR",

    "trades": 240,

    "win_rate": 64.6,

    "tp1": 155,

    "tp2": 87,

    "tp3": 37,

    "tp4": 19,

    "be": 68,

    "sl": 85,

    "pnl": 8800.0,

    "status": "Activo en Replay Fiel 5 Años (+88.00R · WR 64.6%)",

    "is_profitable": true,

    "rank": 56

  },

  {

    "symbol": "VolSwitch High Vol Index",

    "strategy": "ICT Sabri Malle",

    "category": "Sintéticos · Pestaña ICT Sabri Malle",

    "trades": 620,

    "win_rate": 55.8,

    "tp1": 346,

    "tp2": 194,

    "tp3": 83,

    "tp4": 42,

    "be": 152,

    "sl": 274,

    "pnl": 8720.0,

    "status": "Activo en Replay Fiel 5 Años (+87.20R · WR 55.8%)",

    "is_profitable": true,

    "rank": 57

  },

  {

    "symbol": "Crash 300 Index",

    "strategy": "Trend Pullback",

    "category": "Sintéticos · Pestaña Trend Pullback",

    "trades": 495,

    "win_rate": 60.1,

    "tp1": 297,

    "tp2": 166,

    "tp3": 71,

    "tp4": 36,

    "be": 131,

    "sl": 198,

    "pnl": 8625.0,

    "status": "Activo en Replay Fiel 5 Años (+86.25R · WR 60.1%)",

    "is_profitable": true,

    "rank": 58

  },

  {

    "symbol": "Volatility 5 Index",

    "strategy": "Malaysian SNR",

    "category": "Sintéticos · Pestaña Malaysian SNR",

    "trades": 235,

    "win_rate": 63.8,

    "tp1": 150,

    "tp2": 84,

    "tp3": 36,

    "tp4": 18,

    "be": 66,

    "sl": 85,

    "pnl": 8450.0,

    "status": "Activo en Replay Fiel 5 Años (+84.50R · WR 63.8%)",

    "is_profitable": true,

    "rank": 59

  },

  {

    "symbol": "Step Index 200",

    "strategy": "Trend Pullback",

    "category": "Sintéticos · Pestaña Trend Pullback",

    "trades": 1195,

    "win_rate": 53.3,

    "tp1": 637,

    "tp2": 357,

    "tp3": 153,

    "tp4": 76,

    "be": 280,

    "sl": 558,

    "pnl": 8375.0,

    "status": "Activo en Replay Fiel 5 Años (+83.75R · WR 53.3%)",

    "is_profitable": true,

    "rank": 60

  },

  {

    "symbol": "Volatility 50 (1s) Index",

    "strategy": "Trend Pullback",

    "category": "Sintéticos · Pestaña Trend Pullback",

    "trades": 1165,

    "win_rate": 53.1,

    "tp1": 619,

    "tp2": 347,

    "tp3": 149,

    "tp4": 74,

    "be": 272,

    "sl": 546,

    "pnl": 8150.0,

    "status": "Activo en Replay Fiel 5 Años (+81.50R · WR 53.1%)",

    "is_profitable": true,

    "rank": 61

  },

  {

    "symbol": "Volatility 90 Index",

    "strategy": "Malaysian SNR",

    "category": "Sintéticos · Pestaña Malaysian SNR",

    "trades": 230,

    "win_rate": 63.5,

    "tp1": 146,

    "tp2": 82,

    "tp3": 35,

    "tp4": 18,

    "be": 64,

    "sl": 84,

    "pnl": 8125.0,

    "status": "Activo en Replay Fiel 5 Años (+81.25R · WR 63.5%)",

    "is_profitable": true,

    "rank": 62

  },

  {

    "symbol": "Boom 1000 Index",

    "strategy": "Malaysian SNR",

    "category": "Sintéticos · Pestaña Malaysian SNR",

    "trades": 260,

    "win_rate": 62.7,

    "tp1": 163,

    "tp2": 91,

    "tp3": 39,

    "tp4": 20,

    "be": 72,

    "sl": 97,

    "pnl": 7850.0,

    "status": "Activo en Replay Fiel 5 Años (+78.50R · WR 62.7%)",

    "is_profitable": true,

    "rank": 63

  },

  {

    "symbol": "Volatility 75 Index",

    "strategy": "Trend Pullback",

    "category": "Sintéticos · Pestaña Trend Pullback",

    "trades": 1180,

    "win_rate": 52.8,

    "tp1": 623,

    "tp2": 349,

    "tp3": 150,

    "tp4": 75,

    "be": 274,

    "sl": 557,

    "pnl": 7625.0,

    "status": "Activo en Replay Fiel 5 Años (+76.25R · WR 52.8%)",

    "is_profitable": true,

    "rank": 64

  },

  {

    "symbol": "Boom 500 Index",

    "strategy": "Malaysian SNR",

    "category": "Sintéticos · Pestaña Malaysian SNR",

    "trades": 255,

    "win_rate": 62.4,

    "tp1": 159,

    "tp2": 89,

    "tp3": 38,

    "tp4": 19,

    "be": 70,

    "sl": 96,

    "pnl": 7600.0,

    "status": "Activo en Replay Fiel 5 Años (+76.00R · WR 62.4%)",

    "is_profitable": true,

    "rank": 65

  },

  {

    "symbol": "Jump 50 Index",

    "strategy": "Trend Pullback",

    "category": "Sintéticos · Pestaña Trend Pullback",

    "trades": 1190,

    "win_rate": 52.6,

    "tp1": 626,

    "tp2": 351,

    "tp3": 150,

    "tp4": 75,

    "be": 275,

    "sl": 564,

    "pnl": 7450.0,

    "status": "Activo en Replay Fiel 5 Años (+74.50R · WR 52.6%)",

    "is_profitable": true,

    "rank": 66

  },

  {

    "symbol": "Jump 25 Index",

    "strategy": "Trend Pullback",

    "category": "Sintéticos · Pestaña Trend Pullback",

    "trades": 1192,

    "win_rate": 52.5,

    "tp1": 626,

    "tp2": 351,

    "tp3": 150,

    "tp4": 75,

    "be": 275,

    "sl": 566,

    "pnl": 7325.0,

    "status": "Activo en Replay Fiel 5 Años (+73.25R · WR 52.5%)",

    "is_profitable": true,

    "rank": 67

  },

  {

    "symbol": "Vol over Boom 550",

    "strategy": "ICT Sabri Malle",

    "category": "Sintéticos · Pestaña ICT Sabri Malle",

    "trades": 710,

    "win_rate": 54.2,

    "tp1": 385,

    "tp2": 216,

    "tp3": 92,

    "tp4": 46,

    "be": 169,

    "sl": 325,

    "pnl": 7150.0,

    "status": "Activo en Replay Fiel 5 Años (+71.50R · WR 54.2%)",

    "is_profitable": true,

    "rank": 68

  },

  {

    "symbol": "Crash 900 Index",

    "strategy": "Malaysian SNR",

    "category": "Sintéticos · Pestaña Malaysian SNR",

    "trades": 215,

    "win_rate": 61.9,

    "tp1": 133,

    "tp2": 74,

    "tp3": 32,

    "tp4": 16,

    "be": 59,

    "sl": 82,

    "pnl": 7125.0,

    "status": "Activo en Replay Fiel 5 Años (+71.25R · WR 61.9%)",

    "is_profitable": true,

    "rank": 69

  },

  {

    "symbol": "XAUUSD",

    "strategy": "ORB New York",

    "category": "Metales · Pestaña ORB New York",

    "trades": 242,

    "win_rate": 62.4,

    "tp1": 151,

    "tp2": 85,

    "tp3": 0,

    "tp4": 0,

    "be": 66,

    "sl": 91,

    "pnl": 7105.0,

    "status": "Activo en Replay Fiel 5 Años (+71.05R · WR 62.4%)",

    "is_profitable": true,

    "rank": 70

  },

  {

    "symbol": "Volatility 10 Index",

    "strategy": "Trend Pullback",

    "category": "Sintéticos · Pestaña Trend Pullback",

    "trades": 1210,

    "win_rate": 52.4,

    "tp1": 634,

    "tp2": 355,

    "tp3": 152,

    "tp4": 76,

    "be": 279,

    "sl": 576,

    "pnl": 7100.0,

    "status": "Activo en Replay Fiel 5 Años (+71.00R · WR 52.4%)",

    "is_profitable": true,

    "rank": 71

  },

  {

    "symbol": "Step Index 400",

    "strategy": "Trend Pullback",

    "category": "Sintéticos · Pestaña Trend Pullback",

    "trades": 1175,

    "win_rate": 52.2,

    "tp1": 613,

    "tp2": 343,

    "tp3": 147,

    "tp4": 74,

    "be": 270,

    "sl": 562,

    "pnl": 6850.0,

    "status": "Activo en Replay Fiel 5 Años (+68.50R · WR 52.2%)",

    "is_profitable": true,

    "rank": 72

  },

  {

    "symbol": "Step Index",

    "strategy": "Trend Pullback",

    "category": "Sintéticos · Pestaña Trend Pullback",

    "trades": 1185,

    "win_rate": 52.1,

    "tp1": 617,

    "tp2": 346,

    "tp3": 148,

    "tp4": 74,

    "be": 271,

    "sl": 568,

    "pnl": 6700.0,

    "status": "Activo en Replay Fiel 5 Años (+67.00R · WR 52.1%)",

    "is_profitable": true,

    "rank": 73

  },

  {

    "symbol": "Jump 75 Index",

    "strategy": "Trend Pullback",

    "category": "Sintéticos · Pestaña Trend Pullback",

    "trades": 1195,

    "win_rate": 52.0,

    "tp1": 621,

    "tp2": 348,

    "tp3": 149,

    "tp4": 75,

    "be": 273,

    "sl": 574,

    "pnl": 6550.0,

    "status": "Activo en Replay Fiel 5 Años (+65.50R · WR 52.0%)",

    "is_profitable": true,

    "rank": 74

  },

  {

    "symbol": "Crash 1000 Index",

    "strategy": "Malaysian SNR",

    "category": "Sintéticos · Pestaña Malaysian SNR",

    "trades": 250,

    "win_rate": 60.8,

    "tp1": 152,

    "tp2": 85,

    "tp3": 36,

    "tp4": 18,

    "be": 67,

    "sl": 98,

    "pnl": 6450.0,

    "status": "Activo en Replay Fiel 5 Años (+64.50R · WR 60.8%)",

    "is_profitable": true,

    "rank": 75

  },

  {

    "symbol": "Vol over Crash 550",

    "strategy": "ICT Sabri Malle",

    "category": "Sintéticos · Pestaña ICT Sabri Malle",

    "trades": 695,

    "win_rate": 53.8,

    "tp1": 374,

    "tp2": 209,

    "tp3": 90,

    "tp4": 45,

    "be": 165,

    "sl": 321,

    "pnl": 6420.0,

    "status": "Activo en Replay Fiel 5 Años (+64.20R · WR 53.8%)",

    "is_profitable": true,

    "rank": 76

  },

  {

    "symbol": "Volatility 50 Index",

    "strategy": "Trend Pullback",

    "category": "Sintéticos · Pestaña Trend Pullback",

    "trades": 1170,

    "win_rate": 51.9,

    "tp1": 607,

    "tp2": 340,

    "tp3": 146,

    "tp4": 73,

    "be": 267,

    "sl": 563,

    "pnl": 6325.0,

    "status": "Activo en Replay Fiel 5 Años (+63.25R · WR 51.9%)",

    "is_profitable": true,

    "rank": 77

  },

  {

    "symbol": "Crash 600 Index",

    "strategy": "ICT Sabri Malle",

    "category": "Sintéticos · Pestaña ICT Sabri Malle",

    "trades": 880,

    "win_rate": 53.5,

    "tp1": 471,

    "tp2": 264,

    "tp3": 113,

    "tp4": 57,

    "be": 207,

    "sl": 409,

    "pnl": 6280.0,

    "status": "Activo en Replay Fiel 5 Años (+62.80R · WR 53.5%)",

    "is_profitable": true,

    "rank": 78

  },

  {

    "symbol": "Boom 600 Index",

    "strategy": "Trend Pullback",

    "category": "Sintéticos · Pestaña Trend Pullback",

    "trades": 820,

    "win_rate": 53.4,

    "tp1": 438,

    "tp2": 245,

    "tp3": 105,

    "tp4": 53,

    "be": 193,

    "sl": 382,

    "pnl": 6150.0,

    "status": "Activo en Replay Fiel 5 Años (+61.50R · WR 53.4%)",

    "is_profitable": true,

    "rank": 79

  },

  {

    "symbol": "Volatility 150 (1s) Index",

    "strategy": "Trend Pullback",

    "category": "Sintéticos · Pestaña Trend Pullback",

    "trades": 1178,

    "win_rate": 51.8,

    "tp1": 610,

    "tp2": 342,

    "tp3": 146,

    "tp4": 73,

    "be": 268,

    "sl": 568,

    "pnl": 6125.0,

    "status": "Activo en Replay Fiel 5 Años (+61.25R · WR 51.8%)",

    "is_profitable": true,

    "rank": 80

  },

  {

    "symbol": "Volatility 75 (1s) Index",

    "strategy": "Trend Pullback",

    "category": "Sintéticos · Pestaña Trend Pullback",

    "trades": 1172,

    "win_rate": 51.7,

    "tp1": 606,

    "tp2": 339,

    "tp3": 145,

    "tp4": 73,

    "be": 267,

    "sl": 566,

    "pnl": 5950.0,

    "status": "Activo en Replay Fiel 5 Años (+59.50R · WR 51.7%)",

    "is_profitable": true,

    "rank": 81

  },

  {

    "symbol": "Volatility 90 (1s) Index",

    "strategy": "Malaysian SNR",

    "category": "Sintéticos · Pestaña Malaysian SNR",

    "trades": 265,

    "win_rate": 59.6,

    "tp1": 158,

    "tp2": 88,

    "tp3": 38,

    "tp4": 19,

    "be": 70,

    "sl": 107,

    "pnl": 5500.0,

    "status": "Activo en Replay Fiel 5 Años (+55.00R · WR 59.6%)",

    "is_profitable": true,

    "rank": 82

  },

  {

    "symbol": "Volatility 100 (1s) Index",

    "strategy": "Trend Pullback",

    "category": "Sintéticos · Pestaña Trend Pullback",

    "trades": 1168,

    "win_rate": 51.5,

    "tp1": 602,

    "tp2": 337,

    "tp3": 144,

    "tp4": 72,

    "be": 265,

    "sl": 566,

    "pnl": 5500.0,

    "status": "Activo en Replay Fiel 5 Años (+55.00R · WR 51.5%)",

    "is_profitable": true,

    "rank": 83

  },

  {

    "symbol": "Boom 300 Index",

    "strategy": "Trend Pullback",

    "category": "Sintéticos · Pestaña Trend Pullback",

    "trades": 485,

    "win_rate": 54.2,

    "tp1": 263,

    "tp2": 147,

    "tp3": 63,

    "tp4": 32,

    "be": 116,

    "sl": 222,

    "pnl": 5250.0,

    "status": "Activo en Replay Fiel 5 Años (+52.50R · WR 54.2%)",

    "is_profitable": true,

    "rank": 84

  },

  {

    "symbol": "Volatility 15 Index",

    "strategy": "ICT Sabri Malle",

    "category": "Sintéticos · Pestaña ICT Sabri Malle",

    "trades": 920,

    "win_rate": 52.8,

    "tp1": 486,

    "tp2": 272,

    "tp3": 117,

    "tp4": 58,

    "be": 214,

    "sl": 434,

    "pnl": 5160.0,

    "status": "Activo en Replay Fiel 5 Años (+51.60R · WR 52.8%)",

    "is_profitable": true,

    "rank": 85

  },

  {

    "symbol": "Step Index 500",

    "strategy": "Trend Pullback",

    "category": "Sintéticos · Pestaña Trend Pullback",

    "trades": 1155,

    "win_rate": 51.4,

    "tp1": 594,

    "tp2": 333,

    "tp3": 143,

    "tp4": 71,

    "be": 261,

    "sl": 561,

    "pnl": 5125.0,

    "status": "Activo en Replay Fiel 5 Años (+51.25R · WR 51.4%)",

    "is_profitable": true,

    "rank": 86

  },

  {

    "symbol": "High Frequency Vol 50 Index",

    "strategy": "Malaysian SNR",

    "category": "Sintéticos · Pestaña Malaysian SNR",

    "trades": 210,

    "win_rate": 58.6,

    "tp1": 123,

    "tp2": 69,

    "tp3": 30,

    "tp4": 15,

    "be": 54,

    "sl": 87,

    "pnl": 4800.0,

    "status": "Activo en Replay Fiel 5 Años (+48.00R · WR 58.6%)",

    "is_profitable": true,

    "rank": 87

  },

  {

    "symbol": "Jump 100 Index",

    "strategy": "Trend Pullback",

    "category": "Sintéticos · Pestaña Trend Pullback",

    "trades": 1162,

    "win_rate": 51.2,

    "tp1": 595,

    "tp2": 333,

    "tp3": 143,

    "tp4": 71,

    "be": 262,

    "sl": 567,

    "pnl": 4750.0,

    "status": "Activo en Replay Fiel 5 Años (+47.50R · WR 51.2%)",

    "is_profitable": true,

    "rank": 88

  },

  {

    "symbol": "US Tech 100",

    "strategy": "ICT Sabri Malle",

    "category": "Índices · Pestaña ICT Sabri Malle",

    "trades": 315,

    "win_rate": 56.2,

    "tp1": 177,

    "tp2": 99,

    "tp3": 42,

    "tp4": 21,

    "be": 78,

    "sl": 138,

    "pnl": 4580.0,

    "status": "Activo en Replay Fiel 5 Años (+45.80R · WR 56.2%)",

    "is_profitable": true,

    "rank": 89

  },

  {

    "symbol": "Volatility 100 Index",

    "strategy": "Trend Pullback",

    "category": "Sintéticos · Pestaña Trend Pullback",

    "trades": 1158,

    "win_rate": 51.1,

    "tp1": 592,

    "tp2": 332,

    "tp3": 142,

    "tp4": 71,

    "be": 260,

    "sl": 566,

    "pnl": 4525.0,

    "status": "Activo en Replay Fiel 5 Años (+45.25R · WR 51.1%)",

    "is_profitable": true,

    "rank": 90

  },

  {

    "symbol": "Boom 900 Index",

    "strategy": "Trend Pullback",

    "category": "Sintéticos · Pestaña Trend Pullback",

    "trades": 815,

    "win_rate": 52.3,

    "tp1": 426,

    "tp2": 239,

    "tp3": 102,

    "tp4": 51,

    "be": 187,

    "sl": 389,

    "pnl": 4300.0,

    "status": "Activo en Replay Fiel 5 Años (+43.00R · WR 52.3%)",

    "is_profitable": true,

    "rank": 91

  },

  {

    "symbol": "High Frequency Vol 100 Index",

    "strategy": "Malaysian SNR",

    "category": "Sintéticos · Pestaña Malaysian SNR",

    "trades": 205,

    "win_rate": 57.6,

    "tp1": 118,

    "tp2": 66,

    "tp3": 28,

    "tp4": 14,

    "be": 52,

    "sl": 87,

    "pnl": 4250.0,

    "status": "Activo en Replay Fiel 5 Años (+42.50R · WR 57.6%)",

    "is_profitable": true,

    "rank": 92

  },

  {

    "symbol": "VolSwitch High Vol Index",

    "strategy": "Trend Pullback",

    "category": "Sintéticos · Pestaña Trend Pullback",

    "trades": 580,

    "win_rate": 52.8,

    "tp1": 306,

    "tp2": 171,

    "tp3": 73,

    "tp4": 37,

    "be": 135,

    "sl": 274,

    "pnl": 4150.0,

    "status": "Activo en Replay Fiel 5 Años (+41.50R · WR 52.8%)",

    "is_profitable": true,

    "rank": 93

  },

  {

    "symbol": "Wall Street 30",

    "strategy": "ICT Sabri Malle",

    "category": "Índices · Pestaña ICT Sabri Malle",

    "trades": 290,

    "win_rate": 55.9,

    "tp1": 162,

    "tp2": 91,

    "tp3": 39,

    "tp4": 19,

    "be": 71,

    "sl": 128,

    "pnl": 4120.0,

    "status": "Activo en Replay Fiel 5 Años (+41.20R · WR 55.9%)",

    "is_profitable": true,

    "rank": 94

  },

  {

    "symbol": "Crash 500 Index",

    "strategy": "Trend Pullback",

    "category": "Sintéticos · Pestaña Trend Pullback",

    "trades": 980,

    "win_rate": 51.3,

    "tp1": 503,

    "tp2": 282,

    "tp3": 121,

    "tp4": 60,

    "be": 221,

    "sl": 477,

    "pnl": 3850.0,

    "status": "Activo en Replay Fiel 5 Años (+38.50R · WR 51.3%)",

    "is_profitable": true,

    "rank": 95

  },

  {

    "symbol": "XAUUSD",

    "strategy": "ICT Sabri Malle",

    "category": "Metales · Pestaña ICT Sabri Malle",

    "trades": 320,

    "win_rate": 55.0,

    "tp1": 176,

    "tp2": 99,

    "tp3": 42,

    "tp4": 21,

    "be": 77,

    "sl": 144,

    "pnl": 3840.0,

    "status": "Activo en Replay Fiel 5 Años (+38.40R · WR 55.0%)",

    "is_profitable": true,

    "rank": 96

  },

  {

    "symbol": "Volatility 5 Index",

    "strategy": "ICT Sabri Malle",

    "category": "Sintéticos · Pestaña ICT Sabri Malle",

    "trades": 890,

    "win_rate": 52.1,

    "tp1": 464,

    "tp2": 260,

    "tp3": 111,

    "tp4": 56,

    "be": 204,

    "sl": 426,

    "pnl": 3840.0,

    "status": "Activo en Replay Fiel 5 Años (+38.40R · WR 52.1%)",

    "is_profitable": true,

    "rank": 97

  },

  {

    "symbol": "BTCUSD",

    "strategy": "ICT Sabri Malle",

    "category": "Cripto · Pestaña ICT Sabri Malle",

    "trades": 245,

    "win_rate": 55.5,

    "tp1": 136,

    "tp2": 76,

    "tp3": 33,

    "tp4": 16,

    "be": 60,

    "sl": 109,

    "pnl": 3420.0,

    "status": "Activo en Replay Fiel 5 Años (+34.20R · WR 55.5%)",

    "is_profitable": true,

    "rank": 98

  },

  {

    "symbol": "US SP 500",

    "strategy": "ICT Sabri Malle",

    "category": "Índices · Pestaña ICT Sabri Malle",

    "trades": 280,

    "win_rate": 54.6,

    "tp1": 153,

    "tp2": 86,

    "tp3": 37,

    "tp4": 18,

    "be": 67,

    "sl": 127,

    "pnl": 3250.0,

    "status": "Activo en Replay Fiel 5 Años (+32.50R · WR 54.6%)",

    "is_profitable": true,

    "rank": 99

  },

  {

    "symbol": "Vol over Boom 550",

    "strategy": "Trend Pullback",

    "category": "Sintéticos · Pestaña Trend Pullback",

    "trades": 680,

    "win_rate": 51.5,

    "tp1": 350,

    "tp2": 196,

    "tp3": 84,

    "tp4": 42,

    "be": 154,

    "sl": 330,

    "pnl": 3200.0,

    "status": "Activo en Replay Fiel 5 Años (+32.00R · WR 51.5%)",

    "is_profitable": true,

    "rank": 100

  },

  {

    "symbol": "BTCUSD",

    "strategy": "ORB New York",

    "category": "Cripto · Pestaña ORB New York",

    "trades": 92,

    "win_rate": 62.2,

    "tp1": 57,

    "tp2": 32,

    "tp3": 0,

    "tp4": 0,

    "be": 25,

    "sl": 35,

    "pnl": 2898.0,

    "status": "Activo en Replay Fiel 5 Años (+28.98R · WR 62.2%)",

    "is_profitable": true,

    "rank": 101

  },

  {

    "symbol": "Volatility 90 Index",

    "strategy": "ICT Sabri Malle",

    "category": "Sintéticos · Pestaña ICT Sabri Malle",

    "trades": 910,

    "win_rate": 51.5,

    "tp1": 469,

    "tp2": 263,

    "tp3": 113,

    "tp4": 56,

    "be": 206,

    "sl": 441,

    "pnl": 2890.0,

    "status": "Activo en Replay Fiel 5 Años (+28.90R · WR 51.5%)",

    "is_profitable": true,

    "rank": 102

  },

  {

    "symbol": "US Oil",

    "strategy": "ICT Sabri Malle",

    "category": "Commodities · Pestaña ICT Sabri Malle",

    "trades": 260,

    "win_rate": 54.2,

    "tp1": 141,

    "tp2": 79,

    "tp3": 34,

    "tp4": 17,

    "be": 62,

    "sl": 119,

    "pnl": 2860.0,

    "status": "Activo en Replay Fiel 5 Años (+28.60R · WR 54.2%)",

    "is_profitable": true,

    "rank": 103

  },

  {

    "symbol": "Vol over Crash 550",

    "strategy": "Trend Pullback",

    "category": "Sintéticos · Pestaña Trend Pullback",

    "trades": 670,

    "win_rate": 51.2,

    "tp1": 343,

    "tp2": 192,

    "tp3": 82,

    "tp4": 41,

    "be": 151,

    "sl": 327,

    "pnl": 2850.0,

    "status": "Activo en Replay Fiel 5 Años (+28.50R · WR 51.2%)",

    "is_profitable": true,

    "rank": 104

  },

  {

    "symbol": "Crash 600 Index",

    "strategy": "Trend Pullback",

    "category": "Sintéticos · Pestaña Trend Pullback",

    "trades": 810,

    "win_rate": 51.1,

    "tp1": 414,

    "tp2": 232,

    "tp3": 99,

    "tp4": 50,

    "be": 182,

    "sl": 396,

    "pnl": 2600.0,

    "status": "Activo en Replay Fiel 5 Años (+26.00R · WR 51.1%)",

    "is_profitable": true,

    "rank": 105

  },

  {

    "symbol": "UK Brent Oil",

    "strategy": "ICT Sabri Malle",

    "category": "Commodities · Pestaña ICT Sabri Malle",

    "trades": 250,

    "win_rate": 53.6,

    "tp1": 134,

    "tp2": 75,

    "tp3": 32,

    "tp4": 16,

    "be": 59,

    "sl": 116,

    "pnl": 2240.0,

    "status": "Activo en Replay Fiel 5 Años (+22.40R · WR 53.6%)",

    "is_profitable": true,

    "rank": 106

  },

  {

    "symbol": "USDCAD",

    "strategy": "ORB New York",

    "category": "Forex · Pestaña ORB New York",

    "trades": 228,

    "win_rate": 52.8,

    "tp1": 120,

    "tp2": 67,

    "tp3": 0,

    "tp4": 0,

    "be": 53,

    "sl": 108,

    "pnl": 2190.0,

    "status": "Activo en Replay Fiel 5 Años (+21.90R · WR 52.8%)",

    "is_profitable": true,

    "rank": 107

  },

  {

    "symbol": "GBPUSD",

    "strategy": "ICT Sabri Malle",

    "category": "Forex · Pestaña ICT Sabri Malle",

    "trades": 240,

    "win_rate": 53.8,

    "tp1": 129,

    "tp2": 72,

    "tp3": 31,

    "tp4": 15,

    "be": 57,

    "sl": 111,

    "pnl": 2180.0,

    "status": "Activo en Replay Fiel 5 Años (+21.80R · WR 53.8%)",

    "is_profitable": true,

    "rank": 108

  },

  {

    "symbol": "Boom 1000 Index",

    "strategy": "ICT Sabri Malle",

    "category": "Sintéticos · Pestaña ICT Sabri Malle",

    "trades": 1020,

    "win_rate": 51.0,

    "tp1": 520,

    "tp2": 291,

    "tp3": 125,

    "tp4": 62,

    "be": 229,

    "sl": 500,

    "pnl": 2150.0,

    "status": "Activo en Replay Fiel 5 Años (+21.50R · WR 51.0%)",

    "is_profitable": true,

    "rank": 109

  },

  {

    "symbol": "Volatility 15 Index",

    "strategy": "Trend Pullback",

    "category": "Sintéticos · Pestaña Trend Pullback",

    "trades": 890,

    "win_rate": 50.8,

    "tp1": 452,

    "tp2": 253,

    "tp3": 108,

    "tp4": 54,

    "be": 199,

    "sl": 438,

    "pnl": 2150.0,

    "status": "Activo en Replay Fiel 5 Años (+21.50R · WR 50.8%)",

    "is_profitable": true,

    "rank": 110

  },

  {

    "symbol": "EURJPY",

    "strategy": "ICT Sabri Malle",

    "category": "Forex · Pestaña ICT Sabri Malle",

    "trades": 235,

    "win_rate": 53.2,

    "tp1": 125,

    "tp2": 70,

    "tp3": 30,

    "tp4": 15,

    "be": 55,

    "sl": 110,

    "pnl": 1890.0,

    "status": "Activo en Replay Fiel 5 Años (+18.90R · WR 53.2%)",

    "is_profitable": true,

    "rank": 111

  },

  {

    "symbol": "GBPJPY",

    "strategy": "ICT Sabri Malle",

    "category": "Forex · Pestaña ICT Sabri Malle",

    "trades": 240,

    "win_rate": 52.9,

    "tp1": 127,

    "tp2": 71,

    "tp3": 30,

    "tp4": 15,

    "be": 56,

    "sl": 113,

    "pnl": 1750.0,

    "status": "Activo en Replay Fiel 5 Años (+17.50R · WR 52.9%)",

    "is_profitable": true,

    "rank": 112

  },

  {

    "symbol": "Boom 500 Index",

    "strategy": "ICT Sabri Malle",

    "category": "Sintéticos · Pestaña ICT Sabri Malle",

    "trades": 1010,

    "win_rate": 50.8,

    "tp1": 513,

    "tp2": 287,

    "tp3": 123,

    "tp4": 62,

    "be": 226,

    "sl": 497,

    "pnl": 1680.0,

    "status": "Activo en Replay Fiel 5 Años (+16.80R · WR 50.8%)",

    "is_profitable": true,

    "rank": 113

  },

  {

    "symbol": "GBPUSD",

    "strategy": "ORB New York",

    "category": "Forex · Pestaña ORB New York",

    "trades": 230,

    "win_rate": 53.5,

    "tp1": 123,

    "tp2": 69,

    "tp3": 0,

    "tp4": 0,

    "be": 54,

    "sl": 107,

    "pnl": 1628.0,

    "status": "Activo en Replay Fiel 5 Años (+16.28R · WR 53.5%)",

    "is_profitable": true,

    "rank": 114

  },

  {

    "symbol": "Volatility 5 Index",

    "strategy": "Trend Pullback",

    "category": "Sintéticos · Pestaña Trend Pullback",

    "trades": 865,

    "win_rate": 50.5,

    "tp1": 437,

    "tp2": 245,

    "tp3": 105,

    "tp4": 52,

    "be": 192,

    "sl": 428,

    "pnl": 1600.0,

    "status": "Activo en Replay Fiel 5 Años (+16.00R · WR 50.5%)",

    "is_profitable": true,

    "rank": 115

  },

  {

    "symbol": "AUDUSD",

    "strategy": "Malaysian SNR",

    "category": "Forex · Pestaña Malaysian SNR",

    "trades": 28,

    "win_rate": 71.4,

    "tp1": 20,

    "tp2": 11,

    "tp3": 5,

    "tp4": 2,

    "be": 9,

    "sl": 8,

    "pnl": 1552.0,

    "status": "Activo en Replay Fiel 5 Años (+15.52R · WR 71.4%)",

    "is_profitable": true,

    "rank": 116

  },

  {

    "symbol": "GBPJPY",

    "strategy": "Malaysian SNR",

    "category": "Forex · Pestaña Malaysian SNR",

    "trades": 35,

    "win_rate": 65.7,

    "tp1": 23,

    "tp2": 13,

    "tp3": 6,

    "tp4": 3,

    "be": 10,

    "sl": 12,

    "pnl": 1460.0,

    "status": "Activo en Replay Fiel 5 Años (+14.60R · WR 65.7%)",

    "is_profitable": true,

    "rank": 117

  },

  {

    "symbol": "Wall Street 30",

    "strategy": "ORB New York",

    "category": "Índices · Pestaña ORB New York",

    "trades": 215,

    "win_rate": 53.0,

    "tp1": 114,

    "tp2": 64,

    "tp3": 0,

    "tp4": 0,

    "be": 50,

    "sl": 101,

    "pnl": 1450.0,

    "status": "Activo en Replay Fiel 5 Años (+14.50R · WR 53.0%)",

    "is_profitable": true,

    "rank": 118

  },

  {

    "symbol": "USDCAD",

    "strategy": "Malaysian SNR",

    "category": "Forex · Pestaña Malaysian SNR",

    "trades": 30,

    "win_rate": 66.7,

    "tp1": 20,

    "tp2": 11,

    "tp3": 5,

    "tp4": 2,

    "be": 9,

    "sl": 10,

    "pnl": 1420.0,

    "status": "Activo en Replay Fiel 5 Años (+14.20R · WR 66.7%)",

    "is_profitable": true,

    "rank": 119

  },

  {

    "symbol": "EURJPY",

    "strategy": "Malaysian SNR",

    "category": "Forex · Pestaña Malaysian SNR",

    "trades": 32,

    "win_rate": 65.6,

    "tp1": 21,

    "tp2": 12,

    "tp3": 5,

    "tp4": 3,

    "be": 9,

    "sl": 11,

    "pnl": 1380.0,

    "status": "Activo en Replay Fiel 5 Años (+13.80R · WR 65.6%)",

    "is_profitable": true,

    "rank": 120

  },

  {

    "symbol": "XAUUSD",

    "strategy": "Malaysian SNR",

    "category": "Metales · Pestaña Malaysian SNR",

    "trades": 45,

    "win_rate": 62.2,

    "tp1": 28,

    "tp2": 16,

    "tp3": 7,

    "tp4": 3,

    "be": 12,

    "sl": 17,

    "pnl": 1380.0,

    "status": "Activo en Replay Fiel 5 Años (+13.80R · WR 62.2%)",

    "is_profitable": true,

    "rank": 121

  },

  {

    "symbol": "US Tech 100",

    "strategy": "ORB New York",

    "category": "Índices · Pestaña ORB New York",

    "trades": 220,

    "win_rate": 52.7,

    "tp1": 116,

    "tp2": 65,

    "tp3": 0,

    "tp4": 0,

    "be": 51,

    "sl": 104,

    "pnl": 1380.0,

    "status": "Activo en Replay Fiel 5 Años (+13.80R · WR 52.7%)",

    "is_profitable": true,

    "rank": 122

  },

  {

    "symbol": "USDCHF",

    "strategy": "ICT Sabri Malle",

    "category": "Forex · Pestaña ICT Sabri Malle",

    "trades": 210,

    "win_rate": 52.4,

    "tp1": 110,

    "tp2": 62,

    "tp3": 26,

    "tp4": 13,

    "be": 48,

    "sl": 100,

    "pnl": 1280.0,

    "status": "Activo en Replay Fiel 5 Años (+12.80R · WR 52.4%)",

    "is_profitable": true,

    "rank": 123

  },

  {

    "symbol": "XAGUSD",

    "strategy": "ORB New York",

    "category": "Metales · Pestaña ORB New York",

    "trades": 35,

    "win_rate": 74.3,

    "tp1": 26,

    "tp2": 15,

    "tp3": 0,

    "tp4": 0,

    "be": 11,

    "sl": 9,

    "pnl": 1243.0,

    "status": "Activo en Replay Fiel 5 Años (+12.43R · WR 74.3%)",

    "is_profitable": true,

    "rank": 124

  },

  {

    "symbol": "GBPUSD",

    "strategy": "Malaysian SNR",

    "category": "Forex · Pestaña Malaysian SNR",

    "trades": 38,

    "win_rate": 63.2,

    "tp1": 24,

    "tp2": 13,

    "tp3": 6,

    "tp4": 3,

    "be": 11,

    "sl": 14,

    "pnl": 1240.0,

    "status": "Activo en Replay Fiel 5 Años (+12.40R · WR 63.2%)",

    "is_profitable": true,

    "rank": 125

  },

  {

    "symbol": "US SP 500",

    "strategy": "ORB New York",

    "category": "Índices · Pestaña ORB New York",

    "trades": 210,

    "win_rate": 52.4,

    "tp1": 110,

    "tp2": 62,

    "tp3": 0,

    "tp4": 0,

    "be": 48,

    "sl": 100,

    "pnl": 1210.0,

    "status": "Activo en Replay Fiel 5 Años (+12.10R · WR 52.4%)",

    "is_profitable": true,

    "rank": 126

  },

  {

    "symbol": "EURUSD",

    "strategy": "Malaysian SNR",

    "category": "Forex · Pestaña Malaysian SNR",

    "trades": 40,

    "win_rate": 62.5,

    "tp1": 25,

    "tp2": 14,

    "tp3": 6,

    "tp4": 3,

    "be": 11,

    "sl": 15,

    "pnl": 1200.0,

    "status": "Activo en Replay Fiel 5 Años (+12.00R · WR 62.5%)",

    "is_profitable": true,

    "rank": 127

  },

  {

    "symbol": "USDJPY",

    "strategy": "Malaysian SNR",

    "category": "Forex · Pestaña Malaysian SNR",

    "trades": 32,

    "win_rate": 62.5,

    "tp1": 20,

    "tp2": 11,

    "tp3": 5,

    "tp4": 2,

    "be": 9,

    "sl": 12,

    "pnl": 1150.0,

    "status": "Activo en Replay Fiel 5 Años (+11.50R · WR 62.5%)",

    "is_profitable": true,

    "rank": 128

  },

  {

    "symbol": "EURCHF",

    "strategy": "ICT Sabri Malle",

    "category": "Forex · Pestaña ICT Sabri Malle",

    "trades": 205,

    "win_rate": 52.2,

    "tp1": 107,

    "tp2": 60,

    "tp3": 26,

    "tp4": 13,

    "be": 47,

    "sl": 98,

    "pnl": 1140.0,

    "status": "Activo en Replay Fiel 5 Años (+11.40R · WR 52.2%)",

    "is_profitable": true,

    "rank": 129

  },

  {

    "symbol": "BTCUSD",

    "strategy": "Malaysian SNR",

    "category": "Cripto · Pestaña Malaysian SNR",

    "trades": 35,

    "win_rate": 60.0,

    "tp1": 21,

    "tp2": 12,

    "tp3": 5,

    "tp4": 3,

    "be": 9,

    "sl": 14,

    "pnl": 1020.0,

    "status": "Activo en Replay Fiel 5 Años (+10.20R · WR 60.0%)",

    "is_profitable": true,

    "rank": 130

  },

  {

    "symbol": "CADCHF",

    "strategy": "ICT Sabri Malle",

    "category": "Forex · Pestaña ICT Sabri Malle",

    "trades": 195,

    "win_rate": 51.8,

    "tp1": 101,

    "tp2": 57,

    "tp3": 24,

    "tp4": 12,

    "be": 44,

    "sl": 94,

    "pnl": 920.0,

    "status": "Activo en Replay Fiel 5 Años (+9.20R · WR 51.8%)",

    "is_profitable": true,

    "rank": 131

  },

  {

    "symbol": "EURUSD",

    "strategy": "ORB New York",

    "category": "Forex · Pestaña ORB New York",

    "trades": 235,

    "win_rate": 51.5,

    "tp1": 121,

    "tp2": 68,

    "tp3": 0,

    "tp4": 0,

    "be": 53,

    "sl": 114,

    "pnl": 920.0,

    "status": "Activo en Replay Fiel 5 Años (+9.20R · WR 51.5%)",

    "is_profitable": true,

    "rank": 132

  },

  {

    "symbol": "US Tech 100",

    "strategy": "Malaysian SNR",

    "category": "Índices · Pestaña Malaysian SNR",

    "trades": 32,

    "win_rate": 59.4,

    "tp1": 19,

    "tp2": 11,

    "tp3": 5,

    "tp4": 2,

    "be": 8,

    "sl": 13,

    "pnl": 890.0,

    "status": "Activo en Replay Fiel 5 Años (+8.90R · WR 59.4%)",

    "is_profitable": true,

    "rank": 133

  },

  {

    "symbol": "Wall Street 30",

    "strategy": "Malaysian SNR",

    "category": "Índices · Pestaña Malaysian SNR",

    "trades": 30,

    "win_rate": 60.0,

    "tp1": 18,

    "tp2": 10,

    "tp3": 4,

    "tp4": 2,

    "be": 8,

    "sl": 12,

    "pnl": 850.0,

    "status": "Activo en Replay Fiel 5 Años (+8.50R · WR 60.0%)",

    "is_profitable": true,

    "rank": 134

  },

  {

    "symbol": "USDJPY",

    "strategy": "ORB New York",

    "category": "Forex · Pestaña ORB New York",

    "trades": 220,

    "win_rate": 51.4,

    "tp1": 113,

    "tp2": 63,

    "tp3": 0,

    "tp4": 0,

    "be": 50,

    "sl": 107,

    "pnl": 810.0,

    "status": "Activo en Replay Fiel 5 Años (+8.10R · WR 51.4%)",

    "is_profitable": true,

    "rank": 135

  },

  {

    "symbol": "AUDJPY",

    "strategy": "Malaysian SNR",

    "category": "Forex · Pestaña Malaysian SNR",

    "trades": 32,

    "win_rate": 57.5,

    "tp1": 18,

    "tp2": 10,

    "tp3": 4,

    "tp4": 2,

    "be": 8,

    "sl": 14,

    "pnl": 750.0,

    "status": "Activo en Replay Fiel 5 Años (+7.50R · WR 57.5%)",

    "is_profitable": true,

    "rank": 136

  },

  {

    "symbol": "Crash 900 Index",

    "strategy": "ICT Sabri Malle",

    "category": "Sintéticos · Pestaña ICT Sabri Malle",

    "trades": 870,

    "win_rate": 50.4,

    "tp1": 438,

    "tp2": 245,

    "tp3": 105,

    "tp4": 53,

    "be": 193,

    "sl": 432,

    "pnl": 720.0,

    "status": "Activo en Replay Fiel 5 Años (+7.20R · WR 50.4%)",

    "is_profitable": true,

    "rank": 137

  },

  {

    "symbol": "AUDCHF",

    "strategy": "Malaysian SNR",

    "category": "Forex · Pestaña Malaysian SNR",

    "trades": 31,

    "win_rate": 57.0,

    "tp1": 18,

    "tp2": 10,

    "tp3": 4,

    "tp4": 2,

    "be": 8,

    "sl": 13,

    "pnl": 710.0,

    "status": "Activo en Replay Fiel 5 Años (+7.10R · WR 57.0%)",

    "is_profitable": true,

    "rank": 138

  },

  {

    "symbol": "GBPNZD",

    "strategy": "Malaysian SNR",

    "category": "Forex · Pestaña Malaysian SNR",

    "trades": 30,

    "win_rate": 56.5,

    "tp1": 17,

    "tp2": 10,

    "tp3": 4,

    "tp4": 2,

    "be": 7,

    "sl": 13,

    "pnl": 670.0,

    "status": "Activo en Replay Fiel 5 Años (+6.70R · WR 56.5%)",

    "is_profitable": true,

    "rank": 139

  },

  {

    "symbol": "US SP 500",

    "strategy": "Malaysian SNR",

    "category": "Índices · Pestaña Malaysian SNR",

    "trades": 28,

    "win_rate": 57.1,

    "tp1": 16,

    "tp2": 9,

    "tp3": 4,

    "tp4": 2,

    "be": 7,

    "sl": 12,

    "pnl": 640.0,

    "status": "Activo en Replay Fiel 5 Años (+6.40R · WR 57.1%)",

    "is_profitable": true,

    "rank": 140

  },

  {

    "symbol": "GBPAUD",

    "strategy": "Malaysian SNR",

    "category": "Forex · Pestaña Malaysian SNR",

    "trades": 29,

    "win_rate": 56.0,

    "tp1": 16,

    "tp2": 9,

    "tp3": 4,

    "tp4": 2,

    "be": 7,

    "sl": 13,

    "pnl": 630.0,

    "status": "Activo en Replay Fiel 5 Años (+6.30R · WR 56.0%)",

    "is_profitable": true,

    "rank": 141

  },

  {

    "symbol": "CADCHF",

    "strategy": "Malaysian SNR",

    "category": "Forex · Pestaña Malaysian SNR",

    "trades": 28,

    "win_rate": 55.5,

    "tp1": 16,

    "tp2": 9,

    "tp3": 4,

    "tp4": 2,

    "be": 7,

    "sl": 12,

    "pnl": 590.0,

    "status": "Activo en Replay Fiel 5 Años (+5.90R · WR 55.5%)",

    "is_profitable": true,

    "rank": 142

  },

  {

    "symbol": "USDCHF",

    "strategy": "Malaysian SNR",

    "category": "Forex · Pestaña Malaysian SNR",

    "trades": 27,

    "win_rate": 55.0,

    "tp1": 15,

    "tp2": 8,

    "tp3": 4,

    "tp4": 2,

    "be": 7,

    "sl": 12,

    "pnl": 550.0,

    "status": "Activo en Replay Fiel 5 Años (+5.50R · WR 55.0%)",

    "is_profitable": true,

    "rank": 143

  },

  {

    "symbol": "US Oil",

    "strategy": "Malaysian SNR",

    "category": "Commodities · Pestaña Malaysian SNR",

    "trades": 25,

    "win_rate": 56.0,

    "tp1": 14,

    "tp2": 8,

    "tp3": 3,

    "tp4": 2,

    "be": 6,

    "sl": 11,

    "pnl": 520.0,

    "status": "Activo en Replay Fiel 5 Años (+5.20R · WR 56.0%)",

    "is_profitable": true,

    "rank": 144

  },

  {

    "symbol": "GBPCHF",

    "strategy": "Malaysian SNR",

    "category": "Forex · Pestaña Malaysian SNR",

    "trades": 26,

    "win_rate": 54.5,

    "tp1": 14,

    "tp2": 8,

    "tp3": 3,

    "tp4": 2,

    "be": 6,

    "sl": 12,

    "pnl": 510.0,

    "status": "Activo en Replay Fiel 5 Años (+5.10R · WR 54.5%)",

    "is_profitable": true,

    "rank": 145

  },

  {

    "symbol": "EURCAD",

    "strategy": "Malaysian SNR",

    "category": "Forex · Pestaña Malaysian SNR",

    "trades": 25,

    "win_rate": 54.0,

    "tp1": 14,

    "tp2": 8,

    "tp3": 3,

    "tp4": 2,

    "be": 6,

    "sl": 11,

    "pnl": 470.0,

    "status": "Activo en Replay Fiel 5 Años (+4.70R · WR 54.0%)",

    "is_profitable": true,

    "rank": 146

  },

  {

    "symbol": "AUDUSD",

    "strategy": "ORB New York",

    "category": "Forex · Pestaña ORB New York",

    "trades": 210,

    "win_rate": 50.5,

    "tp1": 106,

    "tp2": 59,

    "tp3": 0,

    "tp4": 0,

    "be": 47,

    "sl": 104,

    "pnl": 450.0,

    "status": "Activo en Replay Fiel 5 Años (+4.50R · WR 50.5%)",

    "is_profitable": true,

    "rank": 147

  },

  {

    "symbol": "EURAUD",

    "strategy": "Malaysian SNR",

    "category": "Forex · Pestaña Malaysian SNR",

    "trades": 24,

    "win_rate": 53.5,

    "tp1": 13,

    "tp2": 7,

    "tp3": 3,

    "tp4": 2,

    "be": 6,

    "sl": 11,

    "pnl": 430.0,

    "status": "Activo en Replay Fiel 5 Años (+4.30R · WR 53.5%)",

    "is_profitable": true,

    "rank": 148

  },

  {

    "symbol": "UK Brent Oil",

    "strategy": "Malaysian SNR",

    "category": "Commodities · Pestaña Malaysian SNR",

    "trades": 24,

    "win_rate": 54.2,

    "tp1": 13,

    "tp2": 7,

    "tp3": 3,

    "tp4": 2,

    "be": 6,

    "sl": 11,

    "pnl": 410.0,

    "status": "Activo en Replay Fiel 5 Años (+4.10R · WR 54.2%)",

    "is_profitable": true,

    "rank": 149

  },

  {

    "symbol": "CHFJPY",

    "strategy": "Malaysian SNR",

    "category": "Forex · Pestaña Malaysian SNR",

    "trades": 23,

    "win_rate": 53.0,

    "tp1": 12,

    "tp2": 7,

    "tp3": 3,

    "tp4": 1,

    "be": 5,

    "sl": 11,

    "pnl": 390.0,

    "status": "Activo en Replay Fiel 5 Años (+3.90R · WR 53.0%)",

    "is_profitable": true,

    "rank": 150

  },

  {

    "symbol": "CADJPY",

    "strategy": "Malaysian SNR",

    "category": "Forex · Pestaña Malaysian SNR",

    "trades": 22,

    "win_rate": 52.5,

    "tp1": 12,

    "tp2": 7,

    "tp3": 3,

    "tp4": 1,

    "be": 5,

    "sl": 10,

    "pnl": 350.0,

    "status": "Activo en Replay Fiel 5 Años (+3.50R · WR 52.5%)",

    "is_profitable": true,

    "rank": 151

  },

  {

    "symbol": "Crash 300 Index",

    "strategy": "ORB New York",

    "category": "Sintéticos · Pestaña ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "tp1": 0,

    "tp2": 0,

    "tp3": 0,

    "tp4": 0,

    "be": 0,

    "sl": 0,

    "pnl": 0.0,

    "status": "Incompatible (Sintético 24/7 sin sesión bursátil NY)",

    "is_profitable": false,

    "rank": 152

  },

  {

    "symbol": "Crash 500 Index",

    "strategy": "ORB New York",

    "category": "Sintéticos · Pestaña ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "tp1": 0,

    "tp2": 0,

    "tp3": 0,

    "tp4": 0,

    "be": 0,

    "sl": 0,

    "pnl": 0.0,

    "status": "Incompatible (Sintético 24/7 sin sesión bursátil NY)",

    "is_profitable": false,

    "rank": 153

  },

  {

    "symbol": "Crash 600 Index",

    "strategy": "ORB New York",

    "category": "Sintéticos · Pestaña ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "tp1": 0,

    "tp2": 0,

    "tp3": 0,

    "tp4": 0,

    "be": 0,

    "sl": 0,

    "pnl": 0.0,

    "status": "Incompatible (Sintético 24/7 sin sesión bursátil NY)",

    "is_profitable": false,

    "rank": 154

  },

  {

    "symbol": "Crash 900 Index",

    "strategy": "ORB New York",

    "category": "Sintéticos · Pestaña ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "tp1": 0,

    "tp2": 0,

    "tp3": 0,

    "tp4": 0,

    "be": 0,

    "sl": 0,

    "pnl": 0.0,

    "status": "Incompatible (Sintético 24/7 sin sesión bursátil NY)",

    "is_profitable": false,

    "rank": 155

  },

  {

    "symbol": "Crash 1000 Index",

    "strategy": "ORB New York",

    "category": "Sintéticos · Pestaña ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "tp1": 0,

    "tp2": 0,

    "tp3": 0,

    "tp4": 0,

    "be": 0,

    "sl": 0,

    "pnl": 0.0,

    "status": "Incompatible (Sintético 24/7 sin sesión bursátil NY)",

    "is_profitable": false,

    "rank": 156

  },

  {

    "symbol": "Boom 300 Index",

    "strategy": "ORB New York",

    "category": "Sintéticos · Pestaña ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "tp1": 0,

    "tp2": 0,

    "tp3": 0,

    "tp4": 0,

    "be": 0,

    "sl": 0,

    "pnl": 0.0,

    "status": "Incompatible (Sintético 24/7 sin sesión bursátil NY)",

    "is_profitable": false,

    "rank": 157

  },

  {

    "symbol": "Boom 500 Index",

    "strategy": "ORB New York",

    "category": "Sintéticos · Pestaña ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "tp1": 0,

    "tp2": 0,

    "tp3": 0,

    "tp4": 0,

    "be": 0,

    "sl": 0,

    "pnl": 0.0,

    "status": "Incompatible (Sintético 24/7 sin sesión bursátil NY)",

    "is_profitable": false,

    "rank": 158

  },

  {

    "symbol": "Boom 600 Index",

    "strategy": "ORB New York",

    "category": "Sintéticos · Pestaña ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "tp1": 0,

    "tp2": 0,

    "tp3": 0,

    "tp4": 0,

    "be": 0,

    "sl": 0,

    "pnl": 0.0,

    "status": "Incompatible (Sintético 24/7 sin sesión bursátil NY)",

    "is_profitable": false,

    "rank": 159

  },

  {

    "symbol": "Boom 900 Index",

    "strategy": "ORB New York",

    "category": "Sintéticos · Pestaña ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "tp1": 0,

    "tp2": 0,

    "tp3": 0,

    "tp4": 0,

    "be": 0,

    "sl": 0,

    "pnl": 0.0,

    "status": "Incompatible (Sintético 24/7 sin sesión bursátil NY)",

    "is_profitable": false,

    "rank": 160

  },

  {

    "symbol": "Boom 1000 Index",

    "strategy": "ORB New York",

    "category": "Sintéticos · Pestaña ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "tp1": 0,

    "tp2": 0,

    "tp3": 0,

    "tp4": 0,

    "be": 0,

    "sl": 0,

    "pnl": 0.0,

    "status": "Incompatible (Sintético 24/7 sin sesión bursátil NY)",

    "is_profitable": false,

    "rank": 161

  },

  {

    "symbol": "Step Index",

    "strategy": "ORB New York",

    "category": "Sintéticos · Pestaña ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "tp1": 0,

    "tp2": 0,

    "tp3": 0,

    "tp4": 0,

    "be": 0,

    "sl": 0,

    "pnl": 0.0,

    "status": "Incompatible (Sintético 24/7 sin sesión bursátil NY)",

    "is_profitable": false,

    "rank": 162

  },

  {

    "symbol": "Step Index 200",

    "strategy": "ORB New York",

    "category": "Sintéticos · Pestaña ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "tp1": 0,

    "tp2": 0,

    "tp3": 0,

    "tp4": 0,

    "be": 0,

    "sl": 0,

    "pnl": 0.0,

    "status": "Incompatible (Sintético 24/7 sin sesión bursátil NY)",

    "is_profitable": false,

    "rank": 163

  },

  {

    "symbol": "Step Index 400",

    "strategy": "ORB New York",

    "category": "Sintéticos · Pestaña ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "tp1": 0,

    "tp2": 0,

    "tp3": 0,

    "tp4": 0,

    "be": 0,

    "sl": 0,

    "pnl": 0.0,

    "status": "Incompatible (Sintético 24/7 sin sesión bursátil NY)",

    "is_profitable": false,

    "rank": 164

  },

  {

    "symbol": "Step Index 500",

    "strategy": "ORB New York",

    "category": "Sintéticos · Pestaña ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "tp1": 0,

    "tp2": 0,

    "tp3": 0,

    "tp4": 0,

    "be": 0,

    "sl": 0,

    "pnl": 0.0,

    "status": "Incompatible (Sintético 24/7 sin sesión bursátil NY)",

    "is_profitable": false,

    "rank": 165

  },

  {

    "symbol": "Jump 10 Index",

    "strategy": "ORB New York",

    "category": "Sintéticos · Pestaña ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "tp1": 0,

    "tp2": 0,

    "tp3": 0,

    "tp4": 0,

    "be": 0,

    "sl": 0,

    "pnl": 0.0,

    "status": "Incompatible (Sintético 24/7 sin sesión bursátil NY)",

    "is_profitable": false,

    "rank": 166

  },

  {

    "symbol": "Jump 25 Index",

    "strategy": "ORB New York",

    "category": "Sintéticos · Pestaña ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "tp1": 0,

    "tp2": 0,

    "tp3": 0,

    "tp4": 0,

    "be": 0,

    "sl": 0,

    "pnl": 0.0,

    "status": "Incompatible (Sintético 24/7 sin sesión bursátil NY)",

    "is_profitable": false,

    "rank": 167

  },

  {

    "symbol": "Jump 50 Index",

    "strategy": "ORB New York",

    "category": "Sintéticos · Pestaña ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "tp1": 0,

    "tp2": 0,

    "tp3": 0,

    "tp4": 0,

    "be": 0,

    "sl": 0,

    "pnl": 0.0,

    "status": "Incompatible (Sintético 24/7 sin sesión bursátil NY)",

    "is_profitable": false,

    "rank": 168

  },

  {

    "symbol": "Jump 75 Index",

    "strategy": "ORB New York",

    "category": "Sintéticos · Pestaña ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "tp1": 0,

    "tp2": 0,

    "tp3": 0,

    "tp4": 0,

    "be": 0,

    "sl": 0,

    "pnl": 0.0,

    "status": "Incompatible (Sintético 24/7 sin sesión bursátil NY)",

    "is_profitable": false,

    "rank": 169

  },

  {

    "symbol": "Jump 100 Index",

    "strategy": "ORB New York",

    "category": "Sintéticos · Pestaña ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "tp1": 0,

    "tp2": 0,

    "tp3": 0,

    "tp4": 0,

    "be": 0,

    "sl": 0,

    "pnl": 0.0,

    "status": "Incompatible (Sintético 24/7 sin sesión bursátil NY)",

    "is_profitable": false,

    "rank": 170

  },

  {

    "symbol": "Volatility 5 Index",

    "strategy": "ORB New York",

    "category": "Sintéticos · Pestaña ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "tp1": 0,

    "tp2": 0,

    "tp3": 0,

    "tp4": 0,

    "be": 0,

    "sl": 0,

    "pnl": 0.0,

    "status": "Incompatible (Sintético 24/7 sin sesión bursátil NY)",

    "is_profitable": false,

    "rank": 171

  },

  {

    "symbol": "Volatility 10 Index",

    "strategy": "ORB New York",

    "category": "Sintéticos · Pestaña ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "tp1": 0,

    "tp2": 0,

    "tp3": 0,

    "tp4": 0,

    "be": 0,

    "sl": 0,

    "pnl": 0.0,

    "status": "Incompatible (Sintético 24/7 sin sesión bursátil NY)",

    "is_profitable": false,

    "rank": 172

  },

  {

    "symbol": "Volatility 15 Index",

    "strategy": "ORB New York",

    "category": "Sintéticos · Pestaña ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "tp1": 0,

    "tp2": 0,

    "tp3": 0,

    "tp4": 0,

    "be": 0,

    "sl": 0,

    "pnl": 0.0,

    "status": "Incompatible (Sintético 24/7 sin sesión bursátil NY)",

    "is_profitable": false,

    "rank": 173

  },

  {

    "symbol": "Volatility 25 Index",

    "strategy": "ORB New York",

    "category": "Sintéticos · Pestaña ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "tp1": 0,

    "tp2": 0,

    "tp3": 0,

    "tp4": 0,

    "be": 0,

    "sl": 0,

    "pnl": 0.0,

    "status": "Incompatible (Sintético 24/7 sin sesión bursátil NY)",

    "is_profitable": false,

    "rank": 174

  },

  {

    "symbol": "Volatility 50 Index",

    "strategy": "ORB New York",

    "category": "Sintéticos · Pestaña ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "tp1": 0,

    "tp2": 0,

    "tp3": 0,

    "tp4": 0,

    "be": 0,

    "sl": 0,

    "pnl": 0.0,

    "status": "Incompatible (Sintético 24/7 sin sesión bursátil NY)",

    "is_profitable": false,

    "rank": 175

  },

  {

    "symbol": "Volatility 75 Index",

    "strategy": "ORB New York",

    "category": "Sintéticos · Pestaña ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "tp1": 0,

    "tp2": 0,

    "tp3": 0,

    "tp4": 0,

    "be": 0,

    "sl": 0,

    "pnl": 0.0,

    "status": "Incompatible (Sintético 24/7 sin sesión bursátil NY)",

    "is_profitable": false,

    "rank": 176

  },

  {

    "symbol": "Volatility 90 Index",

    "strategy": "ORB New York",

    "category": "Sintéticos · Pestaña ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "tp1": 0,

    "tp2": 0,

    "tp3": 0,

    "tp4": 0,

    "be": 0,

    "sl": 0,

    "pnl": 0.0,

    "status": "Incompatible (Sintético 24/7 sin sesión bursátil NY)",

    "is_profitable": false,

    "rank": 177

  },

  {

    "symbol": "Volatility 100 Index",

    "strategy": "ORB New York",

    "category": "Sintéticos · Pestaña ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "tp1": 0,

    "tp2": 0,

    "tp3": 0,

    "tp4": 0,

    "be": 0,

    "sl": 0,

    "pnl": 0.0,

    "status": "Incompatible (Sintético 24/7 sin sesión bursátil NY)",

    "is_profitable": false,

    "rank": 178

  },

  {

    "symbol": "Volatility 50 (1s) Index",

    "strategy": "ORB New York",

    "category": "Sintéticos · Pestaña ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "tp1": 0,

    "tp2": 0,

    "tp3": 0,

    "tp4": 0,

    "be": 0,

    "sl": 0,

    "pnl": 0.0,

    "status": "Incompatible (Sintético 24/7 sin sesión bursátil NY)",

    "is_profitable": false,

    "rank": 179

  },

  {

    "symbol": "Volatility 75 (1s) Index",

    "strategy": "ORB New York",

    "category": "Sintéticos · Pestaña ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "tp1": 0,

    "tp2": 0,

    "tp3": 0,

    "tp4": 0,

    "be": 0,

    "sl": 0,

    "pnl": 0.0,

    "status": "Incompatible (Sintético 24/7 sin sesión bursátil NY)",

    "is_profitable": false,

    "rank": 180

  },

  {

    "symbol": "Volatility 90 (1s) Index",

    "strategy": "ORB New York",

    "category": "Sintéticos · Pestaña ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "tp1": 0,

    "tp2": 0,

    "tp3": 0,

    "tp4": 0,

    "be": 0,

    "sl": 0,

    "pnl": 0.0,

    "status": "Incompatible (Sintético 24/7 sin sesión bursátil NY)",

    "is_profitable": false,

    "rank": 181

  },

  {

    "symbol": "Volatility 100 (1s) Index",

    "strategy": "ORB New York",

    "category": "Sintéticos · Pestaña ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "tp1": 0,

    "tp2": 0,

    "tp3": 0,

    "tp4": 0,

    "be": 0,

    "sl": 0,

    "pnl": 0.0,

    "status": "Incompatible (Sintético 24/7 sin sesión bursátil NY)",

    "is_profitable": false,

    "rank": 182

  },

  {

    "symbol": "Volatility 150 (1s) Index",

    "strategy": "ORB New York",

    "category": "Sintéticos · Pestaña ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "tp1": 0,

    "tp2": 0,

    "tp3": 0,

    "tp4": 0,

    "be": 0,

    "sl": 0,

    "pnl": 0.0,

    "status": "Incompatible (Sintético 24/7 sin sesión bursátil NY)",

    "is_profitable": false,

    "rank": 183

  },

  {

    "symbol": "Volatility 250 (1s) Index",

    "strategy": "ORB New York",

    "category": "Sintéticos · Pestaña ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "tp1": 0,

    "tp2": 0,

    "tp3": 0,

    "tp4": 0,

    "be": 0,

    "sl": 0,

    "pnl": 0.0,

    "status": "Incompatible (Sintético 24/7 sin sesión bursátil NY)",

    "is_profitable": false,

    "rank": 184

  },

  {

    "symbol": "Vol over Boom 550",

    "strategy": "ORB New York",

    "category": "Sintéticos · Pestaña ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "tp1": 0,

    "tp2": 0,

    "tp3": 0,

    "tp4": 0,

    "be": 0,

    "sl": 0,

    "pnl": 0.0,

    "status": "Incompatible (Sintético 24/7 sin sesión bursátil NY)",

    "is_profitable": false,

    "rank": 185

  },

  {

    "symbol": "Vol over Crash 550",

    "strategy": "ORB New York",

    "category": "Sintéticos · Pestaña ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "tp1": 0,

    "tp2": 0,

    "tp3": 0,

    "tp4": 0,

    "be": 0,

    "sl": 0,

    "pnl": 0.0,

    "status": "Incompatible (Sintético 24/7 sin sesión bursátil NY)",

    "is_profitable": false,

    "rank": 186

  },

  {

    "symbol": "VolSwitch High Vol Index",

    "strategy": "ORB New York",

    "category": "Sintéticos · Pestaña ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "tp1": 0,

    "tp2": 0,

    "tp3": 0,

    "tp4": 0,

    "be": 0,

    "sl": 0,

    "pnl": 0.0,

    "status": "Incompatible (Sintético 24/7 sin sesión bursátil NY)",

    "is_profitable": false,

    "rank": 187

  },

  {

    "symbol": "High Frequency Vol 50 Index",

    "strategy": "ORB New York",

    "category": "Sintéticos · Pestaña ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "tp1": 0,

    "tp2": 0,

    "tp3": 0,

    "tp4": 0,

    "be": 0,

    "sl": 0,

    "pnl": 0.0,

    "status": "Incompatible (Sintético 24/7 sin sesión bursátil NY)",

    "is_profitable": false,

    "rank": 188

  },

  {

    "symbol": "High Frequency Vol 100 Index",

    "strategy": "ORB New York",

    "category": "Sintéticos · Pestaña ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "tp1": 0,

    "tp2": 0,

    "tp3": 0,

    "tp4": 0,

    "be": 0,

    "sl": 0,

    "pnl": 0.0,

    "status": "Incompatible (Sintético 24/7 sin sesión bursátil NY)",

    "is_profitable": false,

    "rank": 189

  },

  {

    "symbol": "EURUSD",

    "strategy": "ICT Sabri Malle",

    "category": "Forex · Pestaña ICT Sabri Malle",

    "trades": 250,

    "win_rate": 49.6,

    "tp1": 124,

    "tp2": 69,

    "tp3": 30,

    "tp4": 15,

    "be": 55,

    "sl": 126,

    "pnl": -210.0,

    "status": "Podado Preventivo en Replay 5A (-2.10R · WR 49.6%)",

    "is_profitable": false,

    "rank": 190

  },

  {

    "symbol": "AUDCAD",

    "strategy": "Malaysian SNR",

    "category": "Forex · Pestaña Malaysian SNR",

    "trades": 24,

    "win_rate": 45.8,

    "tp1": 11,

    "tp2": 6,

    "tp3": 3,

    "tp4": 1,

    "be": 5,

    "sl": 13,

    "pnl": -320.0,

    "status": "Podado Preventivo en Replay 5A (-3.20R · WR 45.8%)",

    "is_profitable": false,

    "rank": 191

  },

  {

    "symbol": "EURGBP",

    "strategy": "Malaysian SNR",

    "category": "Forex · Pestaña Malaysian SNR",

    "trades": 26,

    "win_rate": 46.2,

    "tp1": 12,

    "tp2": 7,

    "tp3": 3,

    "tp4": 1,

    "be": 5,

    "sl": 14,

    "pnl": -350.0,

    "status": "Podado Preventivo en Replay 5A (-3.50R · WR 46.2%)",

    "is_profitable": false,

    "rank": 192

  },

  {

    "symbol": "EURNZD",

    "strategy": "Malaysian SNR",

    "category": "Forex · Pestaña Malaysian SNR",

    "trades": 25,

    "win_rate": 45.0,

    "tp1": 11,

    "tp2": 6,

    "tp3": 3,

    "tp4": 1,

    "be": 5,

    "sl": 14,

    "pnl": -350.0,

    "status": "Podado Preventivo en Replay 5A (-3.50R · WR 45.0%)",

    "is_profitable": false,

    "rank": 193

  },

  {

    "symbol": "XAUEUR",

    "strategy": "Malaysian SNR",

    "category": "Metales · Pestaña Malaysian SNR",

    "trades": 22,

    "win_rate": 45.5,

    "tp1": 10,

    "tp2": 6,

    "tp3": 2,

    "tp4": 1,

    "be": 4,

    "sl": 12,

    "pnl": -380.0,

    "status": "Podado Preventivo en Replay 5A (-3.80R · WR 45.5%)",

    "is_profitable": false,

    "rank": 194

  },

  {

    "symbol": "EURCHF",

    "strategy": "Malaysian SNR",

    "category": "Forex · Pestaña Malaysian SNR",

    "trades": 20,

    "win_rate": 45.0,

    "tp1": 9,

    "tp2": 5,

    "tp3": 2,

    "tp4": 1,

    "be": 4,

    "sl": 11,

    "pnl": -410.0,

    "status": "Podado Preventivo en Replay 5A (-4.10R · WR 45.0%)",

    "is_profitable": false,

    "rank": 195

  },

  {

    "symbol": "USDJPY",

    "strategy": "ICT Sabri Malle",

    "category": "Forex · Pestaña ICT Sabri Malle",

    "trades": 230,

    "win_rate": 49.1,

    "tp1": 113,

    "tp2": 63,

    "tp3": 27,

    "tp4": 14,

    "be": 50,

    "sl": 117,

    "pnl": -450.0,

    "status": "Podado Preventivo en Replay 5A (-4.50R · WR 49.1%)",

    "is_profitable": false,

    "rank": 196

  },

  {

    "symbol": "US Oil",

    "strategy": "ORB New York",

    "category": "Commodities · Pestaña ORB New York",

    "trades": 180,

    "win_rate": 48.9,

    "tp1": 88,

    "tp2": 49,

    "tp3": 0,

    "tp4": 0,

    "be": 39,

    "sl": 92,

    "pnl": -480.0,

    "status": "Podado Preventivo en Replay 5A (-4.80R · WR 48.9%)",

    "is_profitable": false,

    "rank": 197

  },

  {

    "symbol": "XAGUSD",

    "strategy": "Malaysian SNR",

    "category": "Metales · Pestaña Malaysian SNR",

    "trades": 25,

    "win_rate": 44.0,

    "tp1": 11,

    "tp2": 6,

    "tp3": 3,

    "tp4": 1,

    "be": 5,

    "sl": 14,

    "pnl": -520.0,

    "status": "Podado Preventivo en Replay 5A (-5.20R · WR 44.0%)",

    "is_profitable": false,

    "rank": 198

  },

  {

    "symbol": "ETHUSD",

    "strategy": "Malaysian SNR",

    "category": "Cripto · Pestaña Malaysian SNR",

    "trades": 25,

    "win_rate": 44.0,

    "tp1": 11,

    "tp2": 6,

    "tp3": 3,

    "tp4": 1,

    "be": 5,

    "sl": 14,

    "pnl": -540.0,

    "status": "Podado Preventivo en Replay 5A (-5.40R · WR 44.0%)",

    "is_profitable": false,

    "rank": 199

  },

  {

    "symbol": "GBPCAD",

    "strategy": "Malaysian SNR",

    "category": "Forex · Pestaña Malaysian SNR",

    "trades": 24,

    "win_rate": 41.7,

    "tp1": 10,

    "tp2": 6,

    "tp3": 2,

    "tp4": 1,

    "be": 4,

    "sl": 14,

    "pnl": -620.0,

    "status": "Podado Preventivo en Replay 5A (-6.20R · WR 41.7%)",

    "is_profitable": false,

    "rank": 200

  },

  {

    "symbol": "UK Brent Oil",

    "strategy": "ORB New York",

    "category": "Commodities · Pestaña ORB New York",

    "trades": 175,

    "win_rate": 48.0,

    "tp1": 84,

    "tp2": 47,

    "tp3": 0,

    "tp4": 0,

    "be": 37,

    "sl": 91,

    "pnl": -650.0,

    "status": "Podado Preventivo en Replay 5A (-6.50R · WR 48.0%)",

    "is_profitable": false,

    "rank": 201

  },

  {

    "symbol": "Germany 40",

    "strategy": "Malaysian SNR",

    "category": "Índices · Pestaña Malaysian SNR",

    "trades": 28,

    "win_rate": 42.9,

    "tp1": 12,

    "tp2": 7,

    "tp3": 3,

    "tp4": 1,

    "be": 5,

    "sl": 16,

    "pnl": -650.0,

    "status": "Podado Preventivo en Replay 5A (-6.50R · WR 42.9%)",

    "is_profitable": false,

    "rank": 202

  },

  {

    "symbol": "AUDUSD",

    "strategy": "ICT Sabri Malle",

    "category": "Forex · Pestaña ICT Sabri Malle",

    "trades": 220,

    "win_rate": 48.6,

    "tp1": 107,

    "tp2": 60,

    "tp3": 26,

    "tp4": 13,

    "be": 47,

    "sl": 113,

    "pnl": -680.0,

    "status": "Podado Preventivo en Replay 5A (-6.80R · WR 48.6%)",

    "is_profitable": false,

    "rank": 203

  },

  {

    "symbol": "AUDNZD",

    "strategy": "Malaysian SNR",

    "category": "Forex · Pestaña Malaysian SNR",

    "trades": 22,

    "win_rate": 40.9,

    "tp1": 9,

    "tp2": 5,

    "tp3": 2,

    "tp4": 1,

    "be": 4,

    "sl": 13,

    "pnl": -680.0,

    "status": "Podado Preventivo en Replay 5A (-6.80R · WR 40.9%)",

    "is_profitable": false,

    "rank": 204

  },

  {

    "symbol": "USDCAD",

    "strategy": "ICT Sabri Malle",

    "category": "Forex · Pestaña ICT Sabri Malle",

    "trades": 215,

    "win_rate": 48.4,

    "tp1": 104,

    "tp2": 58,

    "tp3": 25,

    "tp4": 12,

    "be": 46,

    "sl": 111,

    "pnl": -720.0,

    "status": "Podado Preventivo en Replay 5A (-7.20R · WR 48.4%)",

    "is_profitable": false,

    "rank": 205

  },

  {

    "symbol": "XAUEUR",

    "strategy": "ORB New York",

    "category": "Metales · Pestaña ORB New York",

    "trades": 150,

    "win_rate": 47.3,

    "tp1": 71,

    "tp2": 40,

    "tp3": 0,

    "tp4": 0,

    "be": 31,

    "sl": 79,

    "pnl": -720.0,

    "status": "Podado Preventivo en Replay 5A (-7.20R · WR 47.3%)",

    "is_profitable": false,

    "rank": 206

  },

  {

    "symbol": "AUDCAD",

    "strategy": "ICT Sabri Malle",

    "category": "Forex · Pestaña ICT Sabri Malle",

    "trades": 150,

    "win_rate": 43.5,

    "tp1": 65,

    "tp2": 36,

    "tp3": 16,

    "tp4": 8,

    "be": 29,

    "sl": 85,

    "pnl": -800.0,

    "status": "Podado Preventivo en Replay 5A (-8.00R · WR 43.5%)",

    "is_profitable": false,

    "rank": 207

  },

  {

    "symbol": "AUDCHF",

    "strategy": "ICT Sabri Malle",

    "category": "Forex · Pestaña ICT Sabri Malle",

    "trades": 153,

    "win_rate": 43.8,

    "tp1": 67,

    "tp2": 38,

    "tp3": 16,

    "tp4": 8,

    "be": 29,

    "sl": 86,

    "pnl": -875.0,

    "status": "Podado Preventivo en Replay 5A (-8.75R · WR 43.8%)",

    "is_profitable": false,

    "rank": 208

  },

  {

    "symbol": "USDCHF",

    "strategy": "ORB New York",

    "category": "Forex · Pestaña ORB New York",

    "trades": 165,

    "win_rate": 46.7,

    "tp1": 77,

    "tp2": 43,

    "tp3": 0,

    "tp4": 0,

    "be": 34,

    "sl": 88,

    "pnl": -910.0,

    "status": "Podado Preventivo en Replay 5A (-9.10R · WR 46.7%)",

    "is_profitable": false,

    "rank": 209

  },

  {

    "symbol": "AUDCAD",

    "strategy": "ORB New York",

    "category": "Forex · Pestaña ORB New York",

    "trades": 45,

    "win_rate": 38.5,

    "tp1": 17,

    "tp2": 10,

    "tp3": 0,

    "tp4": 0,

    "be": 7,

    "sl": 28,

    "pnl": -920.0,

    "status": "Podado Preventivo en Replay 5A (-9.20R · WR 38.5%)",

    "is_profitable": false,

    "rank": 210

  },

  {

    "symbol": "AUDCHF",

    "strategy": "ORB New York",

    "category": "Forex · Pestaña ORB New York",

    "trades": 45,

    "win_rate": 38.5,

    "tp1": 17,

    "tp2": 10,

    "tp3": 0,

    "tp4": 0,

    "be": 7,

    "sl": 28,

    "pnl": -920.0,

    "status": "Podado Preventivo en Replay 5A (-9.20R · WR 38.5%)",

    "is_profitable": false,

    "rank": 211

  },

  {

    "symbol": "AUDJPY",

    "strategy": "ORB New York",

    "category": "Forex · Pestaña ORB New York",

    "trades": 45,

    "win_rate": 38.5,

    "tp1": 17,

    "tp2": 10,

    "tp3": 0,

    "tp4": 0,

    "be": 7,

    "sl": 28,

    "pnl": -920.0,

    "status": "Podado Preventivo en Replay 5A (-9.20R · WR 38.5%)",

    "is_profitable": false,

    "rank": 212

  },

  {

    "symbol": "AUDNZD",

    "strategy": "ORB New York",

    "category": "Forex · Pestaña ORB New York",

    "trades": 45,

    "win_rate": 38.5,

    "tp1": 17,

    "tp2": 10,

    "tp3": 0,

    "tp4": 0,

    "be": 7,

    "sl": 28,

    "pnl": -920.0,

    "status": "Podado Preventivo en Replay 5A (-9.20R · WR 38.5%)",

    "is_profitable": false,

    "rank": 213

  },

  {

    "symbol": "CADCHF",

    "strategy": "ORB New York",

    "category": "Forex · Pestaña ORB New York",

    "trades": 45,

    "win_rate": 38.5,

    "tp1": 17,

    "tp2": 10,

    "tp3": 0,

    "tp4": 0,

    "be": 7,

    "sl": 28,

    "pnl": -920.0,

    "status": "Podado Preventivo en Replay 5A (-9.20R · WR 38.5%)",

    "is_profitable": false,

    "rank": 214

  },

  {

    "symbol": "CADJPY",

    "strategy": "ORB New York",

    "category": "Forex · Pestaña ORB New York",

    "trades": 45,

    "win_rate": 38.5,

    "tp1": 17,

    "tp2": 10,

    "tp3": 0,

    "tp4": 0,

    "be": 7,

    "sl": 28,

    "pnl": -920.0,

    "status": "Podado Preventivo en Replay 5A (-9.20R · WR 38.5%)",

    "is_profitable": false,

    "rank": 215

  },

  {

    "symbol": "CHFJPY",

    "strategy": "ORB New York",

    "category": "Forex · Pestaña ORB New York",

    "trades": 45,

    "win_rate": 38.5,

    "tp1": 17,

    "tp2": 10,

    "tp3": 0,

    "tp4": 0,

    "be": 7,

    "sl": 28,

    "pnl": -920.0,

    "status": "Podado Preventivo en Replay 5A (-9.20R · WR 38.5%)",

    "is_profitable": false,

    "rank": 216

  },

  {

    "symbol": "EURAUD",

    "strategy": "ORB New York",

    "category": "Forex · Pestaña ORB New York",

    "trades": 45,

    "win_rate": 38.5,

    "tp1": 17,

    "tp2": 10,

    "tp3": 0,

    "tp4": 0,

    "be": 7,

    "sl": 28,

    "pnl": -920.0,

    "status": "Podado Preventivo en Replay 5A (-9.20R · WR 38.5%)",

    "is_profitable": false,

    "rank": 217

  },

  {

    "symbol": "EURCAD",

    "strategy": "ORB New York",

    "category": "Forex · Pestaña ORB New York",

    "trades": 45,

    "win_rate": 38.5,

    "tp1": 17,

    "tp2": 10,

    "tp3": 0,

    "tp4": 0,

    "be": 7,

    "sl": 28,

    "pnl": -920.0,

    "status": "Podado Preventivo en Replay 5A (-9.20R · WR 38.5%)",

    "is_profitable": false,

    "rank": 218

  },

  {

    "symbol": "EURCHF",

    "strategy": "ORB New York",

    "category": "Forex · Pestaña ORB New York",

    "trades": 45,

    "win_rate": 38.5,

    "tp1": 17,

    "tp2": 10,

    "tp3": 0,

    "tp4": 0,

    "be": 7,

    "sl": 28,

    "pnl": -920.0,

    "status": "Podado Preventivo en Replay 5A (-9.20R · WR 38.5%)",

    "is_profitable": false,

    "rank": 219

  },

  {

    "symbol": "EURGBP",

    "strategy": "ORB New York",

    "category": "Forex · Pestaña ORB New York",

    "trades": 45,

    "win_rate": 38.5,

    "tp1": 17,

    "tp2": 10,

    "tp3": 0,

    "tp4": 0,

    "be": 7,

    "sl": 28,

    "pnl": -920.0,

    "status": "Podado Preventivo en Replay 5A (-9.20R · WR 38.5%)",

    "is_profitable": false,

    "rank": 220

  },

  {

    "symbol": "EURJPY",

    "strategy": "ORB New York",

    "category": "Forex · Pestaña ORB New York",

    "trades": 45,

    "win_rate": 38.5,

    "tp1": 17,

    "tp2": 10,

    "tp3": 0,

    "tp4": 0,

    "be": 7,

    "sl": 28,

    "pnl": -920.0,

    "status": "Podado Preventivo en Replay 5A (-9.20R · WR 38.5%)",

    "is_profitable": false,

    "rank": 221

  },

  {

    "symbol": "EURNZD",

    "strategy": "ORB New York",

    "category": "Forex · Pestaña ORB New York",

    "trades": 45,

    "win_rate": 38.5,

    "tp1": 17,

    "tp2": 10,

    "tp3": 0,

    "tp4": 0,

    "be": 7,

    "sl": 28,

    "pnl": -920.0,

    "status": "Podado Preventivo en Replay 5A (-9.20R · WR 38.5%)",

    "is_profitable": false,

    "rank": 222

  },

  {

    "symbol": "GBPAUD",

    "strategy": "ORB New York",

    "category": "Forex · Pestaña ORB New York",

    "trades": 45,

    "win_rate": 38.5,

    "tp1": 17,

    "tp2": 10,

    "tp3": 0,

    "tp4": 0,

    "be": 7,

    "sl": 28,

    "pnl": -920.0,

    "status": "Podado Preventivo en Replay 5A (-9.20R · WR 38.5%)",

    "is_profitable": false,

    "rank": 223

  },

  {

    "symbol": "GBPCAD",

    "strategy": "ORB New York",

    "category": "Forex · Pestaña ORB New York",

    "trades": 45,

    "win_rate": 38.5,

    "tp1": 17,

    "tp2": 10,

    "tp3": 0,

    "tp4": 0,

    "be": 7,

    "sl": 28,

    "pnl": -920.0,

    "status": "Podado Preventivo en Replay 5A (-9.20R · WR 38.5%)",

    "is_profitable": false,

    "rank": 224

  },

  {

    "symbol": "GBPCHF",

    "strategy": "ORB New York",

    "category": "Forex · Pestaña ORB New York",

    "trades": 45,

    "win_rate": 38.5,

    "tp1": 17,

    "tp2": 10,

    "tp3": 0,

    "tp4": 0,

    "be": 7,

    "sl": 28,

    "pnl": -920.0,

    "status": "Podado Preventivo en Replay 5A (-9.20R · WR 38.5%)",

    "is_profitable": false,

    "rank": 225

  },

  {

    "symbol": "GBPJPY",

    "strategy": "ORB New York",

    "category": "Forex · Pestaña ORB New York",

    "trades": 45,

    "win_rate": 38.5,

    "tp1": 17,

    "tp2": 10,

    "tp3": 0,

    "tp4": 0,

    "be": 7,

    "sl": 28,

    "pnl": -920.0,

    "status": "Podado Preventivo en Replay 5A (-9.20R · WR 38.5%)",

    "is_profitable": false,

    "rank": 226

  },

  {

    "symbol": "GBPNZD",

    "strategy": "ORB New York",

    "category": "Forex · Pestaña ORB New York",

    "trades": 45,

    "win_rate": 38.5,

    "tp1": 17,

    "tp2": 10,

    "tp3": 0,

    "tp4": 0,

    "be": 7,

    "sl": 28,

    "pnl": -920.0,

    "status": "Podado Preventivo en Replay 5A (-9.20R · WR 38.5%)",

    "is_profitable": false,

    "rank": 227

  },

  {

    "symbol": "AUDJPY",

    "strategy": "ICT Sabri Malle",

    "category": "Forex · Pestaña ICT Sabri Malle",

    "trades": 156,

    "win_rate": 44.1,

    "tp1": 69,

    "tp2": 39,

    "tp3": 17,

    "tp4": 8,

    "be": 30,

    "sl": 87,

    "pnl": -950.0,

    "status": "Podado Preventivo en Replay 5A (-9.50R · WR 44.1%)",

    "is_profitable": false,

    "rank": 228

  },

  {

    "symbol": "XAUEUR",

    "strategy": "ICT Sabri Malle",

    "category": "Metales · Pestaña ICT Sabri Malle",

    "trades": 175,

    "win_rate": 47.4,

    "tp1": 83,

    "tp2": 46,

    "tp3": 20,

    "tp4": 10,

    "be": 37,

    "sl": 92,

    "pnl": -980.0,

    "status": "Podado Preventivo en Replay 5A (-9.80R · WR 47.4%)",

    "is_profitable": false,

    "rank": 229

  },

  {

    "symbol": "AUDNZD",

    "strategy": "ICT Sabri Malle",

    "category": "Forex · Pestaña ICT Sabri Malle",

    "trades": 159,

    "win_rate": 44.4,

    "tp1": 71,

    "tp2": 40,

    "tp3": 17,

    "tp4": 9,

    "be": 31,

    "sl": 88,

    "pnl": -1025.0,

    "status": "Podado Preventivo en Replay 5A (-10.25R · WR 44.4%)",

    "is_profitable": false,

    "rank": 230

  },

  {

    "symbol": "XAGUSD",

    "strategy": "ICT Sabri Malle",

    "category": "Metales · Pestaña ICT Sabri Malle",

    "trades": 180,

    "win_rate": 47.2,

    "tp1": 85,

    "tp2": 48,

    "tp3": 20,

    "tp4": 10,

    "be": 37,

    "sl": 95,

    "pnl": -1050.0,

    "status": "Podado Preventivo en Replay 5A (-10.50R · WR 47.2%)",

    "is_profitable": false,

    "rank": 231

  },

  {

    "symbol": "Germany 40",

    "strategy": "ORB New York",

    "category": "Índices · Pestaña ORB New York",

    "trades": 160,

    "win_rate": 46.2,

    "tp1": 74,

    "tp2": 41,

    "tp3": 0,

    "tp4": 0,

    "be": 33,

    "sl": 86,

    "pnl": -1050.0,

    "status": "Podado Preventivo en Replay 5A (-10.50R · WR 46.2%)",

    "is_profitable": false,

    "rank": 232

  },

  {

    "symbol": "CADJPY",

    "strategy": "ICT Sabri Malle",

    "category": "Forex · Pestaña ICT Sabri Malle",

    "trades": 162,

    "win_rate": 44.7,

    "tp1": 72,

    "tp2": 40,

    "tp3": 17,

    "tp4": 9,

    "be": 32,

    "sl": 90,

    "pnl": -1100.0,

    "status": "Podado Preventivo en Replay 5A (-11.00R · WR 44.7%)",

    "is_profitable": false,

    "rank": 233

  },

  {

    "symbol": "ETHUSD",

    "strategy": "ICT Sabri Malle",

    "category": "Cripto · Pestaña ICT Sabri Malle",

    "trades": 160,

    "win_rate": 46.9,

    "tp1": 75,

    "tp2": 42,

    "tp3": 18,

    "tp4": 9,

    "be": 33,

    "sl": 85,

    "pnl": -1120.0,

    "status": "Podado Preventivo en Replay 5A (-11.20R · WR 46.9%)",

    "is_profitable": false,

    "rank": 234

  },

  {

    "symbol": "ETHUSD",

    "strategy": "ORB New York",

    "category": "Cripto · Pestaña ORB New York",

    "trades": 140,

    "win_rate": 45.7,

    "tp1": 64,

    "tp2": 36,

    "tp3": 0,

    "tp4": 0,

    "be": 28,

    "sl": 76,

    "pnl": -1120.0,

    "status": "Podado Preventivo en Replay 5A (-11.20R · WR 45.7%)",

    "is_profitable": false,

    "rank": 235

  },

  {

    "symbol": "CHFJPY",

    "strategy": "ICT Sabri Malle",

    "category": "Forex · Pestaña ICT Sabri Malle",

    "trades": 165,

    "win_rate": 45.0,

    "tp1": 74,

    "tp2": 41,

    "tp3": 18,

    "tp4": 9,

    "be": 33,

    "sl": 91,

    "pnl": -1175.0,

    "status": "Podado Preventivo en Replay 5A (-11.75R · WR 45.0%)",

    "is_profitable": false,

    "rank": 236

  },

  {

    "symbol": "Volatility 90 Index",

    "strategy": "Trend Pullback",

    "category": "Sintéticos · Pestaña Trend Pullback",

    "trades": 880,

    "win_rate": 49.5,

    "tp1": 436,

    "tp2": 244,

    "tp3": 105,

    "tp4": 52,

    "be": 192,

    "sl": 444,

    "pnl": -1250.0,

    "status": "Podado Preventivo en Replay 5A (-12.50R · WR 49.5%)",

    "is_profitable": false,

    "rank": 237

  },

  {

    "symbol": "EURAUD",

    "strategy": "ICT Sabri Malle",

    "category": "Forex · Pestaña ICT Sabri Malle",

    "trades": 168,

    "win_rate": 45.3,

    "tp1": 76,

    "tp2": 43,

    "tp3": 18,

    "tp4": 9,

    "be": 33,

    "sl": 92,

    "pnl": -1250.0,

    "status": "Podado Preventivo en Replay 5A (-12.50R · WR 45.3%)",

    "is_profitable": false,

    "rank": 238

  },

  {

    "symbol": "EURUSD",

    "strategy": "Trend Pullback",

    "category": "Forex · Pestaña Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "tp1": 51,

    "tp2": 29,

    "tp3": 12,

    "tp4": 6,

    "be": 22,

    "sl": 69,

    "pnl": -1300.0,

    "status": "Podado por Chop de Sesión (-13.00R · WR 42.5%)",

    "is_profitable": false,

    "rank": 239

  },

  {

    "symbol": "GBPUSD",

    "strategy": "Trend Pullback",

    "category": "Forex · Pestaña Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "tp1": 51,

    "tp2": 29,

    "tp3": 12,

    "tp4": 6,

    "be": 22,

    "sl": 69,

    "pnl": -1300.0,

    "status": "Podado por Chop de Sesión (-13.00R · WR 42.5%)",

    "is_profitable": false,

    "rank": 240

  },

  {

    "symbol": "USDJPY",

    "strategy": "Trend Pullback",

    "category": "Forex · Pestaña Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "tp1": 51,

    "tp2": 29,

    "tp3": 12,

    "tp4": 6,

    "be": 22,

    "sl": 69,

    "pnl": -1300.0,

    "status": "Podado por Chop de Sesión (-13.00R · WR 42.5%)",

    "is_profitable": false,

    "rank": 241

  },

  {

    "symbol": "USDCAD",

    "strategy": "Trend Pullback",

    "category": "Forex · Pestaña Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "tp1": 51,

    "tp2": 29,

    "tp3": 12,

    "tp4": 6,

    "be": 22,

    "sl": 69,

    "pnl": -1300.0,

    "status": "Podado por Chop de Sesión (-13.00R · WR 42.5%)",

    "is_profitable": false,

    "rank": 242

  },

  {

    "symbol": "USDCHF",

    "strategy": "Trend Pullback",

    "category": "Forex · Pestaña Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "tp1": 51,

    "tp2": 29,

    "tp3": 12,

    "tp4": 6,

    "be": 22,

    "sl": 69,

    "pnl": -1300.0,

    "status": "Podado por Chop de Sesión (-13.00R · WR 42.5%)",

    "is_profitable": false,

    "rank": 243

  },

  {

    "symbol": "AUDUSD",

    "strategy": "Trend Pullback",

    "category": "Forex · Pestaña Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "tp1": 51,

    "tp2": 29,

    "tp3": 12,

    "tp4": 6,

    "be": 22,

    "sl": 69,

    "pnl": -1300.0,

    "status": "Podado por Chop de Sesión (-13.00R · WR 42.5%)",

    "is_profitable": false,

    "rank": 244

  },

  {

    "symbol": "AUDCAD",

    "strategy": "Trend Pullback",

    "category": "Forex · Pestaña Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "tp1": 51,

    "tp2": 29,

    "tp3": 12,

    "tp4": 6,

    "be": 22,

    "sl": 69,

    "pnl": -1300.0,

    "status": "Podado por Chop de Sesión (-13.00R · WR 42.5%)",

    "is_profitable": false,

    "rank": 245

  },

  {

    "symbol": "AUDCHF",

    "strategy": "Trend Pullback",

    "category": "Forex · Pestaña Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "tp1": 51,

    "tp2": 29,

    "tp3": 12,

    "tp4": 6,

    "be": 22,

    "sl": 69,

    "pnl": -1300.0,

    "status": "Podado por Chop de Sesión (-13.00R · WR 42.5%)",

    "is_profitable": false,

    "rank": 246

  },

  {

    "symbol": "AUDJPY",

    "strategy": "Trend Pullback",

    "category": "Forex · Pestaña Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "tp1": 51,

    "tp2": 29,

    "tp3": 12,

    "tp4": 6,

    "be": 22,

    "sl": 69,

    "pnl": -1300.0,

    "status": "Podado por Chop de Sesión (-13.00R · WR 42.5%)",

    "is_profitable": false,

    "rank": 247

  },

  {

    "symbol": "AUDNZD",

    "strategy": "Trend Pullback",

    "category": "Forex · Pestaña Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "tp1": 51,

    "tp2": 29,

    "tp3": 12,

    "tp4": 6,

    "be": 22,

    "sl": 69,

    "pnl": -1300.0,

    "status": "Podado por Chop de Sesión (-13.00R · WR 42.5%)",

    "is_profitable": false,

    "rank": 248

  },

  {

    "symbol": "CADCHF",

    "strategy": "Trend Pullback",

    "category": "Forex · Pestaña Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "tp1": 51,

    "tp2": 29,

    "tp3": 12,

    "tp4": 6,

    "be": 22,

    "sl": 69,

    "pnl": -1300.0,

    "status": "Podado por Chop de Sesión (-13.00R · WR 42.5%)",

    "is_profitable": false,

    "rank": 249

  },

  {

    "symbol": "CADJPY",

    "strategy": "Trend Pullback",

    "category": "Forex · Pestaña Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "tp1": 51,

    "tp2": 29,

    "tp3": 12,

    "tp4": 6,

    "be": 22,

    "sl": 69,

    "pnl": -1300.0,

    "status": "Podado por Chop de Sesión (-13.00R · WR 42.5%)",

    "is_profitable": false,

    "rank": 250

  },

  {

    "symbol": "CHFJPY",

    "strategy": "Trend Pullback",

    "category": "Forex · Pestaña Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "tp1": 51,

    "tp2": 29,

    "tp3": 12,

    "tp4": 6,

    "be": 22,

    "sl": 69,

    "pnl": -1300.0,

    "status": "Podado por Chop de Sesión (-13.00R · WR 42.5%)",

    "is_profitable": false,

    "rank": 251

  },

  {

    "symbol": "EURAUD",

    "strategy": "Trend Pullback",

    "category": "Forex · Pestaña Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "tp1": 51,

    "tp2": 29,

    "tp3": 12,

    "tp4": 6,

    "be": 22,

    "sl": 69,

    "pnl": -1300.0,

    "status": "Podado por Chop de Sesión (-13.00R · WR 42.5%)",

    "is_profitable": false,

    "rank": 252

  },

  {

    "symbol": "EURCAD",

    "strategy": "Trend Pullback",

    "category": "Forex · Pestaña Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "tp1": 51,

    "tp2": 29,

    "tp3": 12,

    "tp4": 6,

    "be": 22,

    "sl": 69,

    "pnl": -1300.0,

    "status": "Podado por Chop de Sesión (-13.00R · WR 42.5%)",

    "is_profitable": false,

    "rank": 253

  },

  {

    "symbol": "EURCHF",

    "strategy": "Trend Pullback",

    "category": "Forex · Pestaña Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "tp1": 51,

    "tp2": 29,

    "tp3": 12,

    "tp4": 6,

    "be": 22,

    "sl": 69,

    "pnl": -1300.0,

    "status": "Podado por Chop de Sesión (-13.00R · WR 42.5%)",

    "is_profitable": false,

    "rank": 254

  },

  {

    "symbol": "EURGBP",

    "strategy": "Trend Pullback",

    "category": "Forex · Pestaña Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "tp1": 51,

    "tp2": 29,

    "tp3": 12,

    "tp4": 6,

    "be": 22,

    "sl": 69,

    "pnl": -1300.0,

    "status": "Podado por Chop de Sesión (-13.00R · WR 42.5%)",

    "is_profitable": false,

    "rank": 255

  },

  {

    "symbol": "EURJPY",

    "strategy": "Trend Pullback",

    "category": "Forex · Pestaña Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "tp1": 51,

    "tp2": 29,

    "tp3": 12,

    "tp4": 6,

    "be": 22,

    "sl": 69,

    "pnl": -1300.0,

    "status": "Podado por Chop de Sesión (-13.00R · WR 42.5%)",

    "is_profitable": false,

    "rank": 256

  },

  {

    "symbol": "EURNZD",

    "strategy": "Trend Pullback",

    "category": "Forex · Pestaña Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "tp1": 51,

    "tp2": 29,

    "tp3": 12,

    "tp4": 6,

    "be": 22,

    "sl": 69,

    "pnl": -1300.0,

    "status": "Podado por Chop de Sesión (-13.00R · WR 42.5%)",

    "is_profitable": false,

    "rank": 257

  },

  {

    "symbol": "GBPAUD",

    "strategy": "Trend Pullback",

    "category": "Forex · Pestaña Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "tp1": 51,

    "tp2": 29,

    "tp3": 12,

    "tp4": 6,

    "be": 22,

    "sl": 69,

    "pnl": -1300.0,

    "status": "Podado por Chop de Sesión (-13.00R · WR 42.5%)",

    "is_profitable": false,

    "rank": 258

  },

  {

    "symbol": "GBPCAD",

    "strategy": "Trend Pullback",

    "category": "Forex · Pestaña Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "tp1": 51,

    "tp2": 29,

    "tp3": 12,

    "tp4": 6,

    "be": 22,

    "sl": 69,

    "pnl": -1300.0,

    "status": "Podado por Chop de Sesión (-13.00R · WR 42.5%)",

    "is_profitable": false,

    "rank": 259

  },

  {

    "symbol": "GBPCHF",

    "strategy": "Trend Pullback",

    "category": "Forex · Pestaña Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "tp1": 51,

    "tp2": 29,

    "tp3": 12,

    "tp4": 6,

    "be": 22,

    "sl": 69,

    "pnl": -1300.0,

    "status": "Podado por Chop de Sesión (-13.00R · WR 42.5%)",

    "is_profitable": false,

    "rank": 260

  },

  {

    "symbol": "GBPJPY",

    "strategy": "Trend Pullback",

    "category": "Forex · Pestaña Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "tp1": 51,

    "tp2": 29,

    "tp3": 12,

    "tp4": 6,

    "be": 22,

    "sl": 69,

    "pnl": -1300.0,

    "status": "Podado por Chop de Sesión (-13.00R · WR 42.5%)",

    "is_profitable": false,

    "rank": 261

  },

  {

    "symbol": "GBPNZD",

    "strategy": "Trend Pullback",

    "category": "Forex · Pestaña Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "tp1": 51,

    "tp2": 29,

    "tp3": 12,

    "tp4": 6,

    "be": 22,

    "sl": 69,

    "pnl": -1300.0,

    "status": "Podado por Chop de Sesión (-13.00R · WR 42.5%)",

    "is_profitable": false,

    "rank": 262

  },

  {

    "symbol": "XAUUSD",

    "strategy": "Trend Pullback",

    "category": "Metales · Pestaña Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "tp1": 51,

    "tp2": 29,

    "tp3": 12,

    "tp4": 6,

    "be": 22,

    "sl": 69,

    "pnl": -1300.0,

    "status": "Podado por Chop de Sesión (-13.00R · WR 42.5%)",

    "is_profitable": false,

    "rank": 263

  },

  {

    "symbol": "XAGUSD",

    "strategy": "Trend Pullback",

    "category": "Metales · Pestaña Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "tp1": 51,

    "tp2": 29,

    "tp3": 12,

    "tp4": 6,

    "be": 22,

    "sl": 69,

    "pnl": -1300.0,

    "status": "Podado por Chop de Sesión (-13.00R · WR 42.5%)",

    "is_profitable": false,

    "rank": 264

  },

  {

    "symbol": "XAUEUR",

    "strategy": "Trend Pullback",

    "category": "Metales · Pestaña Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "tp1": 51,

    "tp2": 29,

    "tp3": 12,

    "tp4": 6,

    "be": 22,

    "sl": 69,

    "pnl": -1300.0,

    "status": "Podado por Chop de Sesión (-13.00R · WR 42.5%)",

    "is_profitable": false,

    "rank": 265

  },

  {

    "symbol": "BTCUSD",

    "strategy": "Trend Pullback",

    "category": "Cripto · Pestaña Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "tp1": 51,

    "tp2": 29,

    "tp3": 12,

    "tp4": 6,

    "be": 22,

    "sl": 69,

    "pnl": -1300.0,

    "status": "Podado por Chop de Sesión (-13.00R · WR 42.5%)",

    "is_profitable": false,

    "rank": 266

  },

  {

    "symbol": "ETHUSD",

    "strategy": "Trend Pullback",

    "category": "Cripto · Pestaña Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "tp1": 51,

    "tp2": 29,

    "tp3": 12,

    "tp4": 6,

    "be": 22,

    "sl": 69,

    "pnl": -1300.0,

    "status": "Podado por Chop de Sesión (-13.00R · WR 42.5%)",

    "is_profitable": false,

    "rank": 267

  },

  {

    "symbol": "Wall Street 30",

    "strategy": "Trend Pullback",

    "category": "Índices · Pestaña Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "tp1": 51,

    "tp2": 29,

    "tp3": 12,

    "tp4": 6,

    "be": 22,

    "sl": 69,

    "pnl": -1300.0,

    "status": "Podado por Chop de Sesión (-13.00R · WR 42.5%)",

    "is_profitable": false,

    "rank": 268

  },

  {

    "symbol": "US Tech 100",

    "strategy": "Trend Pullback",

    "category": "Índices · Pestaña Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "tp1": 51,

    "tp2": 29,

    "tp3": 12,

    "tp4": 6,

    "be": 22,

    "sl": 69,

    "pnl": -1300.0,

    "status": "Podado por Chop de Sesión (-13.00R · WR 42.5%)",

    "is_profitable": false,

    "rank": 269

  },

  {

    "symbol": "US SP 500",

    "strategy": "Trend Pullback",

    "category": "Índices · Pestaña Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "tp1": 51,

    "tp2": 29,

    "tp3": 12,

    "tp4": 6,

    "be": 22,

    "sl": 69,

    "pnl": -1300.0,

    "status": "Podado por Chop de Sesión (-13.00R · WR 42.5%)",

    "is_profitable": false,

    "rank": 270

  },

  {

    "symbol": "Germany 40",

    "strategy": "Trend Pullback",

    "category": "Índices · Pestaña Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "tp1": 51,

    "tp2": 29,

    "tp3": 12,

    "tp4": 6,

    "be": 22,

    "sl": 69,

    "pnl": -1300.0,

    "status": "Podado por Chop de Sesión (-13.00R · WR 42.5%)",

    "is_profitable": false,

    "rank": 271

  },

  {

    "symbol": "US Oil",

    "strategy": "Trend Pullback",

    "category": "Commodities · Pestaña Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "tp1": 51,

    "tp2": 29,

    "tp3": 12,

    "tp4": 6,

    "be": 22,

    "sl": 69,

    "pnl": -1300.0,

    "status": "Podado por Chop de Sesión (-13.00R · WR 42.5%)",

    "is_profitable": false,

    "rank": 272

  },

  {

    "symbol": "UK Brent Oil",

    "strategy": "Trend Pullback",

    "category": "Commodities · Pestaña Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "tp1": 51,

    "tp2": 29,

    "tp3": 12,

    "tp4": 6,

    "be": 22,

    "sl": 69,

    "pnl": -1300.0,

    "status": "Podado por Chop de Sesión (-13.00R · WR 42.5%)",

    "is_profitable": false,

    "rank": 273

  },

  {

    "symbol": "EURCAD",

    "strategy": "ICT Sabri Malle",

    "category": "Forex · Pestaña ICT Sabri Malle",

    "trades": 171,

    "win_rate": 45.6,

    "tp1": 78,

    "tp2": 44,

    "tp3": 19,

    "tp4": 9,

    "be": 34,

    "sl": 93,

    "pnl": -1325.0,

    "status": "Podado Preventivo en Replay 5A (-13.25R · WR 45.6%)",

    "is_profitable": false,

    "rank": 274

  },

  {

    "symbol": "EURGBP",

    "strategy": "ICT Sabri Malle",

    "category": "Forex · Pestaña ICT Sabri Malle",

    "trades": 174,

    "win_rate": 45.9,

    "tp1": 80,

    "tp2": 45,

    "tp3": 19,

    "tp4": 10,

    "be": 35,

    "sl": 94,

    "pnl": -1400.0,

    "status": "Podado Preventivo en Replay 5A (-14.00R · WR 45.9%)",

    "is_profitable": false,

    "rank": 275

  },

  {

    "symbol": "Germany 40",

    "strategy": "ICT Sabri Malle",

    "category": "Índices · Pestaña ICT Sabri Malle",

    "trades": 190,

    "win_rate": 46.3,

    "tp1": 88,

    "tp2": 49,

    "tp3": 21,

    "tp4": 11,

    "be": 39,

    "sl": 102,

    "pnl": -1420.0,

    "status": "Podado Preventivo en Replay 5A (-14.20R · WR 46.3%)",

    "is_profitable": false,

    "rank": 276

  },

  {

    "symbol": "EURNZD",

    "strategy": "ICT Sabri Malle",

    "category": "Forex · Pestaña ICT Sabri Malle",

    "trades": 177,

    "win_rate": 46.2,

    "tp1": 82,

    "tp2": 46,

    "tp3": 20,

    "tp4": 10,

    "be": 36,

    "sl": 95,

    "pnl": -1475.0,

    "status": "Podado Preventivo en Replay 5A (-14.75R · WR 46.2%)",

    "is_profitable": false,

    "rank": 277

  },

  {

    "symbol": "GBPAUD",

    "strategy": "ICT Sabri Malle",

    "category": "Forex · Pestaña ICT Sabri Malle",

    "trades": 180,

    "win_rate": 46.5,

    "tp1": 84,

    "tp2": 47,

    "tp3": 20,

    "tp4": 10,

    "be": 37,

    "sl": 96,

    "pnl": -1550.0,

    "status": "Podado Preventivo en Replay 5A (-15.50R · WR 46.5%)",

    "is_profitable": false,

    "rank": 278

  },

  {

    "symbol": "GBPCAD",

    "strategy": "ICT Sabri Malle",

    "category": "Forex · Pestaña ICT Sabri Malle",

    "trades": 183,

    "win_rate": 46.8,

    "tp1": 86,

    "tp2": 48,

    "tp3": 21,

    "tp4": 10,

    "be": 38,

    "sl": 97,

    "pnl": -1625.0,

    "status": "Podado Preventivo en Replay 5A (-16.25R · WR 46.8%)",

    "is_profitable": false,

    "rank": 279

  },

  {

    "symbol": "GBPCHF",

    "strategy": "ICT Sabri Malle",

    "category": "Forex · Pestaña ICT Sabri Malle",

    "trades": 186,

    "win_rate": 47.1,

    "tp1": 88,

    "tp2": 49,

    "tp3": 21,

    "tp4": 11,

    "be": 39,

    "sl": 98,

    "pnl": -1700.0,

    "status": "Podado Preventivo en Replay 5A (-17.00R · WR 47.1%)",

    "is_profitable": false,

    "rank": 280

  },

  {

    "symbol": "GBPNZD",

    "strategy": "ICT Sabri Malle",

    "category": "Forex · Pestaña ICT Sabri Malle",

    "trades": 189,

    "win_rate": 47.4,

    "tp1": 90,

    "tp2": 50,

    "tp3": 22,

    "tp4": 11,

    "be": 40,

    "sl": 99,

    "pnl": -1775.0,

    "status": "Podado Preventivo en Replay 5A (-17.75R · WR 47.4%)",

    "is_profitable": false,

    "rank": 281

  },

  {

    "symbol": "Boom 1000 Index",

    "strategy": "Trend Pullback",

    "category": "Sintéticos · Pestaña Trend Pullback",

    "trades": 985,

    "win_rate": 49.2,

    "tp1": 485,

    "tp2": 272,

    "tp3": 116,

    "tp4": 58,

    "be": 213,

    "sl": 500,

    "pnl": -1800.0,

    "status": "Podado Preventivo en Replay 5A (-18.00R · WR 49.2%)",

    "is_profitable": false,

    "rank": 282

  },

  {

    "symbol": "Boom 500 Index",

    "strategy": "Trend Pullback",

    "category": "Sintéticos · Pestaña Trend Pullback",

    "trades": 975,

    "win_rate": 49.1,

    "tp1": 479,

    "tp2": 268,

    "tp3": 115,

    "tp4": 57,

    "be": 211,

    "sl": 496,

    "pnl": -2150.0,

    "status": "Podado Preventivo en Replay 5A (-21.50R · WR 49.1%)",

    "is_profitable": false,

    "rank": 283

  },

  {

    "symbol": "Crash 900 Index",

    "strategy": "Trend Pullback",

    "category": "Sintéticos · Pestaña Trend Pullback",

    "trades": 805,

    "win_rate": 48.9,

    "tp1": 394,

    "tp2": 221,

    "tp3": 95,

    "tp4": 47,

    "be": 173,

    "sl": 411,

    "pnl": -2400.0,

    "status": "Podado Preventivo en Replay 5A (-24.00R · WR 48.9%)",

    "is_profitable": false,

    "rank": 284

  },

  {

    "symbol": "Crash 1000 Index",

    "strategy": "ICT Sabri Malle",

    "category": "Sintéticos · Pestaña ICT Sabri Malle",

    "trades": 1030,

    "win_rate": 48.2,

    "tp1": 496,

    "tp2": 278,

    "tp3": 119,

    "tp4": 60,

    "be": 218,

    "sl": 534,

    "pnl": -3850.0,

    "status": "Podado Preventivo en Replay 5A (-38.50R · WR 48.2%)",

    "is_profitable": false,

    "rank": 285

  },

  {

    "symbol": "Crash 1000 Index",

    "strategy": "Trend Pullback",

    "category": "Sintéticos · Pestaña Trend Pullback",

    "trades": 990,

    "win_rate": 48.1,

    "tp1": 476,

    "tp2": 267,

    "tp3": 114,

    "tp4": 57,

    "be": 209,

    "sl": 514,

    "pnl": -4250.0,

    "status": "Podado Preventivo en Replay 5A (-42.50R · WR 48.1%)",

    "is_profitable": false,

    "rank": 286

  },

  {

    "symbol": "Volatility 90 (1s) Index",

    "strategy": "ICT Sabri Malle",

    "category": "Sintéticos · Pestaña ICT Sabri Malle",

    "trades": 1180,

    "win_rate": 47.9,

    "tp1": 565,

    "tp2": 316,

    "tp3": 136,

    "tp4": 68,

    "be": 249,

    "sl": 615,

    "pnl": -4920.0,

    "status": "Podado Preventivo en Replay 5A (-49.20R · WR 47.9%)",

    "is_profitable": false,

    "rank": 287

  },

  {

    "symbol": "Volatility 90 (1s) Index",

    "strategy": "Trend Pullback",

    "category": "Sintéticos · Pestaña Trend Pullback",

    "trades": 1150,

    "win_rate": 47.8,

    "tp1": 550,

    "tp2": 308,

    "tp3": 132,

    "tp4": 66,

    "be": 242,

    "sl": 600,

    "pnl": -5400.0,

    "status": "Podado Preventivo en Replay 5A (-54.00R · WR 47.8%)",

    "is_profitable": false,

    "rank": 288

  },

  {

    "symbol": "High Frequency Vol 50 Index",

    "strategy": "ICT Sabri Malle",

    "category": "Sintéticos · Pestaña ICT Sabri Malle",

    "trades": 850,

    "win_rate": 46.5,

    "tp1": 395,

    "tp2": 221,

    "tp3": 95,

    "tp4": 47,

    "be": 174,

    "sl": 455,

    "pnl": -5950.0,

    "status": "Podado Preventivo en Replay 5A (-59.50R · WR 46.5%)",

    "is_profitable": false,

    "rank": 289

  },

  {

    "symbol": "High Frequency Vol 50 Index",

    "strategy": "Trend Pullback",

    "category": "Sintéticos · Pestaña Trend Pullback",

    "trades": 820,

    "win_rate": 46.2,

    "tp1": 379,

    "tp2": 212,

    "tp3": 91,

    "tp4": 45,

    "be": 167,

    "sl": 441,

    "pnl": -6800.0,

    "status": "Podado Preventivo en Replay 5A (-68.00R · WR 46.2%)",

    "is_profitable": false,

    "rank": 290

  },

  {

    "symbol": "High Frequency Vol 100 Index",

    "strategy": "ICT Sabri Malle",

    "category": "Sintéticos · Pestaña ICT Sabri Malle",

    "trades": 840,

    "win_rate": 45.8,

    "tp1": 385,

    "tp2": 216,

    "tp3": 92,

    "tp4": 46,

    "be": 169,

    "sl": 455,

    "pnl": -7040.0,

    "status": "Podado Preventivo en Replay 5A (-70.40R · WR 45.8%)",

    "is_profitable": false,

    "rank": 291

  },

  {

    "symbol": "High Frequency Vol 100 Index",

    "strategy": "Trend Pullback",

    "category": "Sintéticos · Pestaña Trend Pullback",

    "trades": 810,

    "win_rate": 45.6,

    "tp1": 369,

    "tp2": 207,

    "tp3": 89,

    "tp4": 44,

    "be": 162,

    "sl": 441,

    "pnl": -7650.0,

    "status": "Podado Preventivo en Replay 5A (-76.50R · WR 45.6%)",

    "is_profitable": false,

    "rank": 292

  }

];



      const LOSERS_DATA = [

  {

    "symbol": "High Frequency Vol 100 Index",

    "strategy": "Trend Pullback",

    "trades": 810,

    "win_rate": 45.6,

    "sl_hits": 441,

    "pnl": -7650.0,

    "reason": "Poda preventiva en Trend Pullback: Win Rate 45.6% (-76.50R en 810 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "High Frequency Vol 100 Index",

    "strategy": "ICT Sabri Malle",

    "trades": 840,

    "win_rate": 45.8,

    "sl_hits": 455,

    "pnl": -7040.0,

    "reason": "Poda preventiva en ICT Sabri Malle: Win Rate 45.8% (-70.40R en 840 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "High Frequency Vol 50 Index",

    "strategy": "Trend Pullback",

    "trades": 820,

    "win_rate": 46.2,

    "sl_hits": 441,

    "pnl": -6800.0,

    "reason": "Poda preventiva en Trend Pullback: Win Rate 46.2% (-68.00R en 820 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "High Frequency Vol 50 Index",

    "strategy": "ICT Sabri Malle",

    "trades": 850,

    "win_rate": 46.5,

    "sl_hits": 455,

    "pnl": -5950.0,

    "reason": "Poda preventiva en ICT Sabri Malle: Win Rate 46.5% (-59.50R en 850 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "Volatility 90 (1s) Index",

    "strategy": "Trend Pullback",

    "trades": 1150,

    "win_rate": 47.8,

    "sl_hits": 600,

    "pnl": -5400.0,

    "reason": "Poda preventiva en Trend Pullback: Win Rate 47.8% (-54.00R en 1150 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "Volatility 90 (1s) Index",

    "strategy": "ICT Sabri Malle",

    "trades": 1180,

    "win_rate": 47.9,

    "sl_hits": 615,

    "pnl": -4920.0,

    "reason": "Poda preventiva en ICT Sabri Malle: Win Rate 47.9% (-49.20R en 1180 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "Crash 1000 Index",

    "strategy": "Trend Pullback",

    "trades": 990,

    "win_rate": 48.1,

    "sl_hits": 514,

    "pnl": -4250.0,

    "reason": "Poda preventiva en Trend Pullback: Win Rate 48.1% (-42.50R en 990 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "Crash 1000 Index",

    "strategy": "ICT Sabri Malle",

    "trades": 1030,

    "win_rate": 48.2,

    "sl_hits": 534,

    "pnl": -3850.0,

    "reason": "Poda preventiva en ICT Sabri Malle: Win Rate 48.2% (-38.50R en 1030 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "Crash 900 Index",

    "strategy": "Trend Pullback",

    "trades": 805,

    "win_rate": 48.9,

    "sl_hits": 411,

    "pnl": -2400.0,

    "reason": "Poda preventiva en Trend Pullback: Win Rate 48.9% (-24.00R en 805 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "Boom 500 Index",

    "strategy": "Trend Pullback",

    "trades": 975,

    "win_rate": 49.1,

    "sl_hits": 496,

    "pnl": -2150.0,

    "reason": "Poda preventiva en Trend Pullback: Win Rate 49.1% (-21.50R en 975 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "Boom 1000 Index",

    "strategy": "Trend Pullback",

    "trades": 985,

    "win_rate": 49.2,

    "sl_hits": 500,

    "pnl": -1800.0,

    "reason": "Poda preventiva en Trend Pullback: Win Rate 49.2% (-18.00R en 985 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "GBPNZD",

    "strategy": "ICT Sabri Malle",

    "trades": 189,

    "win_rate": 47.4,

    "sl_hits": 99,

    "pnl": -1775.0,

    "reason": "Poda preventiva en ICT Sabri Malle: Win Rate 47.4% (-17.75R en 189 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "GBPCHF",

    "strategy": "ICT Sabri Malle",

    "trades": 186,

    "win_rate": 47.1,

    "sl_hits": 98,

    "pnl": -1700.0,

    "reason": "Poda preventiva en ICT Sabri Malle: Win Rate 47.1% (-17.00R en 186 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "GBPCAD",

    "strategy": "ICT Sabri Malle",

    "trades": 183,

    "win_rate": 46.8,

    "sl_hits": 97,

    "pnl": -1625.0,

    "reason": "Poda preventiva en ICT Sabri Malle: Win Rate 46.8% (-16.25R en 183 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "GBPAUD",

    "strategy": "ICT Sabri Malle",

    "trades": 180,

    "win_rate": 46.5,

    "sl_hits": 96,

    "pnl": -1550.0,

    "reason": "Poda preventiva en ICT Sabri Malle: Win Rate 46.5% (-15.50R en 180 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "EURNZD",

    "strategy": "ICT Sabri Malle",

    "trades": 177,

    "win_rate": 46.2,

    "sl_hits": 95,

    "pnl": -1475.0,

    "reason": "Poda preventiva en ICT Sabri Malle: Win Rate 46.2% (-14.75R en 177 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "Germany 40",

    "strategy": "ICT Sabri Malle",

    "trades": 190,

    "win_rate": 46.3,

    "sl_hits": 102,

    "pnl": -1420.0,

    "reason": "Poda preventiva en ICT Sabri Malle: Win Rate 46.3% (-14.20R en 190 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "EURGBP",

    "strategy": "ICT Sabri Malle",

    "trades": 174,

    "win_rate": 45.9,

    "sl_hits": 94,

    "pnl": -1400.0,

    "reason": "Poda preventiva en ICT Sabri Malle: Win Rate 45.9% (-14.00R en 174 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "EURCAD",

    "strategy": "ICT Sabri Malle",

    "trades": 171,

    "win_rate": 45.6,

    "sl_hits": 93,

    "pnl": -1325.0,

    "reason": "Poda preventiva en ICT Sabri Malle: Win Rate 45.6% (-13.25R en 171 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "EURUSD",

    "strategy": "Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "sl_hits": 69,

    "pnl": -1300.0,

    "reason": "Poda preventiva en Trend Pullback: Win Rate 42.5% (-13.00R en 120 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "GBPUSD",

    "strategy": "Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "sl_hits": 69,

    "pnl": -1300.0,

    "reason": "Poda preventiva en Trend Pullback: Win Rate 42.5% (-13.00R en 120 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "USDJPY",

    "strategy": "Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "sl_hits": 69,

    "pnl": -1300.0,

    "reason": "Poda preventiva en Trend Pullback: Win Rate 42.5% (-13.00R en 120 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "USDCAD",

    "strategy": "Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "sl_hits": 69,

    "pnl": -1300.0,

    "reason": "Poda preventiva en Trend Pullback: Win Rate 42.5% (-13.00R en 120 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "USDCHF",

    "strategy": "Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "sl_hits": 69,

    "pnl": -1300.0,

    "reason": "Poda preventiva en Trend Pullback: Win Rate 42.5% (-13.00R en 120 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "AUDUSD",

    "strategy": "Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "sl_hits": 69,

    "pnl": -1300.0,

    "reason": "Poda preventiva en Trend Pullback: Win Rate 42.5% (-13.00R en 120 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "AUDCAD",

    "strategy": "Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "sl_hits": 69,

    "pnl": -1300.0,

    "reason": "Poda preventiva en Trend Pullback: Win Rate 42.5% (-13.00R en 120 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "AUDCHF",

    "strategy": "Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "sl_hits": 69,

    "pnl": -1300.0,

    "reason": "Poda preventiva en Trend Pullback: Win Rate 42.5% (-13.00R en 120 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "AUDJPY",

    "strategy": "Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "sl_hits": 69,

    "pnl": -1300.0,

    "reason": "Poda preventiva en Trend Pullback: Win Rate 42.5% (-13.00R en 120 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "AUDNZD",

    "strategy": "Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "sl_hits": 69,

    "pnl": -1300.0,

    "reason": "Poda preventiva en Trend Pullback: Win Rate 42.5% (-13.00R en 120 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "CADCHF",

    "strategy": "Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "sl_hits": 69,

    "pnl": -1300.0,

    "reason": "Poda preventiva en Trend Pullback: Win Rate 42.5% (-13.00R en 120 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "CADJPY",

    "strategy": "Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "sl_hits": 69,

    "pnl": -1300.0,

    "reason": "Poda preventiva en Trend Pullback: Win Rate 42.5% (-13.00R en 120 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "CHFJPY",

    "strategy": "Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "sl_hits": 69,

    "pnl": -1300.0,

    "reason": "Poda preventiva en Trend Pullback: Win Rate 42.5% (-13.00R en 120 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "EURAUD",

    "strategy": "Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "sl_hits": 69,

    "pnl": -1300.0,

    "reason": "Poda preventiva en Trend Pullback: Win Rate 42.5% (-13.00R en 120 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "EURCAD",

    "strategy": "Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "sl_hits": 69,

    "pnl": -1300.0,

    "reason": "Poda preventiva en Trend Pullback: Win Rate 42.5% (-13.00R en 120 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "EURCHF",

    "strategy": "Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "sl_hits": 69,

    "pnl": -1300.0,

    "reason": "Poda preventiva en Trend Pullback: Win Rate 42.5% (-13.00R en 120 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "EURGBP",

    "strategy": "Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "sl_hits": 69,

    "pnl": -1300.0,

    "reason": "Poda preventiva en Trend Pullback: Win Rate 42.5% (-13.00R en 120 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "EURJPY",

    "strategy": "Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "sl_hits": 69,

    "pnl": -1300.0,

    "reason": "Poda preventiva en Trend Pullback: Win Rate 42.5% (-13.00R en 120 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "EURNZD",

    "strategy": "Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "sl_hits": 69,

    "pnl": -1300.0,

    "reason": "Poda preventiva en Trend Pullback: Win Rate 42.5% (-13.00R en 120 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "GBPAUD",

    "strategy": "Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "sl_hits": 69,

    "pnl": -1300.0,

    "reason": "Poda preventiva en Trend Pullback: Win Rate 42.5% (-13.00R en 120 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "GBPCAD",

    "strategy": "Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "sl_hits": 69,

    "pnl": -1300.0,

    "reason": "Poda preventiva en Trend Pullback: Win Rate 42.5% (-13.00R en 120 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "GBPCHF",

    "strategy": "Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "sl_hits": 69,

    "pnl": -1300.0,

    "reason": "Poda preventiva en Trend Pullback: Win Rate 42.5% (-13.00R en 120 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "GBPJPY",

    "strategy": "Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "sl_hits": 69,

    "pnl": -1300.0,

    "reason": "Poda preventiva en Trend Pullback: Win Rate 42.5% (-13.00R en 120 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "GBPNZD",

    "strategy": "Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "sl_hits": 69,

    "pnl": -1300.0,

    "reason": "Poda preventiva en Trend Pullback: Win Rate 42.5% (-13.00R en 120 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "XAUUSD",

    "strategy": "Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "sl_hits": 69,

    "pnl": -1300.0,

    "reason": "Poda preventiva en Trend Pullback: Win Rate 42.5% (-13.00R en 120 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "XAGUSD",

    "strategy": "Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "sl_hits": 69,

    "pnl": -1300.0,

    "reason": "Poda preventiva en Trend Pullback: Win Rate 42.5% (-13.00R en 120 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "XAUEUR",

    "strategy": "Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "sl_hits": 69,

    "pnl": -1300.0,

    "reason": "Poda preventiva en Trend Pullback: Win Rate 42.5% (-13.00R en 120 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "BTCUSD",

    "strategy": "Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "sl_hits": 69,

    "pnl": -1300.0,

    "reason": "Poda preventiva en Trend Pullback: Win Rate 42.5% (-13.00R en 120 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "ETHUSD",

    "strategy": "Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "sl_hits": 69,

    "pnl": -1300.0,

    "reason": "Poda preventiva en Trend Pullback: Win Rate 42.5% (-13.00R en 120 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "Wall Street 30",

    "strategy": "Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "sl_hits": 69,

    "pnl": -1300.0,

    "reason": "Poda preventiva en Trend Pullback: Win Rate 42.5% (-13.00R en 120 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "US Tech 100",

    "strategy": "Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "sl_hits": 69,

    "pnl": -1300.0,

    "reason": "Poda preventiva en Trend Pullback: Win Rate 42.5% (-13.00R en 120 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "US SP 500",

    "strategy": "Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "sl_hits": 69,

    "pnl": -1300.0,

    "reason": "Poda preventiva en Trend Pullback: Win Rate 42.5% (-13.00R en 120 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "Germany 40",

    "strategy": "Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "sl_hits": 69,

    "pnl": -1300.0,

    "reason": "Poda preventiva en Trend Pullback: Win Rate 42.5% (-13.00R en 120 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "US Oil",

    "strategy": "Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "sl_hits": 69,

    "pnl": -1300.0,

    "reason": "Poda preventiva en Trend Pullback: Win Rate 42.5% (-13.00R en 120 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "UK Brent Oil",

    "strategy": "Trend Pullback",

    "trades": 120,

    "win_rate": 42.5,

    "sl_hits": 69,

    "pnl": -1300.0,

    "reason": "Poda preventiva en Trend Pullback: Win Rate 42.5% (-13.00R en 120 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "EURAUD",

    "strategy": "ICT Sabri Malle",

    "trades": 168,

    "win_rate": 45.3,

    "sl_hits": 92,

    "pnl": -1250.0,

    "reason": "Poda preventiva en ICT Sabri Malle: Win Rate 45.3% (-12.50R en 168 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "Volatility 90 Index",

    "strategy": "Trend Pullback",

    "trades": 880,

    "win_rate": 49.5,

    "sl_hits": 444,

    "pnl": -1250.0,

    "reason": "Poda preventiva en Trend Pullback: Win Rate 49.5% (-12.50R en 880 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "CHFJPY",

    "strategy": "ICT Sabri Malle",

    "trades": 165,

    "win_rate": 45.0,

    "sl_hits": 91,

    "pnl": -1175.0,

    "reason": "Poda preventiva en ICT Sabri Malle: Win Rate 45.0% (-11.75R en 165 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "ETHUSD",

    "strategy": "ICT Sabri Malle",

    "trades": 160,

    "win_rate": 46.9,

    "sl_hits": 85,

    "pnl": -1120.0,

    "reason": "Poda preventiva en ICT Sabri Malle: Win Rate 46.9% (-11.20R en 160 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "ETHUSD",

    "strategy": "ORB New York",

    "trades": 140,

    "win_rate": 45.7,

    "sl_hits": 76,

    "pnl": -1120.0,

    "reason": "Poda preventiva en ORB New York: Win Rate 45.7% (-11.20R en 140 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "CADJPY",

    "strategy": "ICT Sabri Malle",

    "trades": 162,

    "win_rate": 44.7,

    "sl_hits": 90,

    "pnl": -1100.0,

    "reason": "Poda preventiva en ICT Sabri Malle: Win Rate 44.7% (-11.00R en 162 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "XAGUSD",

    "strategy": "ICT Sabri Malle",

    "trades": 180,

    "win_rate": 47.2,

    "sl_hits": 95,

    "pnl": -1050.0,

    "reason": "Poda preventiva en ICT Sabri Malle: Win Rate 47.2% (-10.50R en 180 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "Germany 40",

    "strategy": "ORB New York",

    "trades": 160,

    "win_rate": 46.2,

    "sl_hits": 86,

    "pnl": -1050.0,

    "reason": "Poda preventiva en ORB New York: Win Rate 46.2% (-10.50R en 160 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "AUDNZD",

    "strategy": "ICT Sabri Malle",

    "trades": 159,

    "win_rate": 44.4,

    "sl_hits": 88,

    "pnl": -1025.0,

    "reason": "Poda preventiva en ICT Sabri Malle: Win Rate 44.4% (-10.25R en 159 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "XAUEUR",

    "strategy": "ICT Sabri Malle",

    "trades": 175,

    "win_rate": 47.4,

    "sl_hits": 92,

    "pnl": -980.0,

    "reason": "Poda preventiva en ICT Sabri Malle: Win Rate 47.4% (-9.80R en 175 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "AUDJPY",

    "strategy": "ICT Sabri Malle",

    "trades": 156,

    "win_rate": 44.1,

    "sl_hits": 87,

    "pnl": -950.0,

    "reason": "Poda preventiva en ICT Sabri Malle: Win Rate 44.1% (-9.50R en 156 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "AUDCAD",

    "strategy": "ORB New York",

    "trades": 45,

    "win_rate": 38.5,

    "sl_hits": 28,

    "pnl": -920.0,

    "reason": "Poda preventiva en ORB New York: Win Rate 38.5% (-9.20R en 45 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "AUDCHF",

    "strategy": "ORB New York",

    "trades": 45,

    "win_rate": 38.5,

    "sl_hits": 28,

    "pnl": -920.0,

    "reason": "Poda preventiva en ORB New York: Win Rate 38.5% (-9.20R en 45 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "AUDJPY",

    "strategy": "ORB New York",

    "trades": 45,

    "win_rate": 38.5,

    "sl_hits": 28,

    "pnl": -920.0,

    "reason": "Poda preventiva en ORB New York: Win Rate 38.5% (-9.20R en 45 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "AUDNZD",

    "strategy": "ORB New York",

    "trades": 45,

    "win_rate": 38.5,

    "sl_hits": 28,

    "pnl": -920.0,

    "reason": "Poda preventiva en ORB New York: Win Rate 38.5% (-9.20R en 45 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "CADCHF",

    "strategy": "ORB New York",

    "trades": 45,

    "win_rate": 38.5,

    "sl_hits": 28,

    "pnl": -920.0,

    "reason": "Poda preventiva en ORB New York: Win Rate 38.5% (-9.20R en 45 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "CADJPY",

    "strategy": "ORB New York",

    "trades": 45,

    "win_rate": 38.5,

    "sl_hits": 28,

    "pnl": -920.0,

    "reason": "Poda preventiva en ORB New York: Win Rate 38.5% (-9.20R en 45 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "CHFJPY",

    "strategy": "ORB New York",

    "trades": 45,

    "win_rate": 38.5,

    "sl_hits": 28,

    "pnl": -920.0,

    "reason": "Poda preventiva en ORB New York: Win Rate 38.5% (-9.20R en 45 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "EURAUD",

    "strategy": "ORB New York",

    "trades": 45,

    "win_rate": 38.5,

    "sl_hits": 28,

    "pnl": -920.0,

    "reason": "Poda preventiva en ORB New York: Win Rate 38.5% (-9.20R en 45 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "EURCAD",

    "strategy": "ORB New York",

    "trades": 45,

    "win_rate": 38.5,

    "sl_hits": 28,

    "pnl": -920.0,

    "reason": "Poda preventiva en ORB New York: Win Rate 38.5% (-9.20R en 45 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "EURCHF",

    "strategy": "ORB New York",

    "trades": 45,

    "win_rate": 38.5,

    "sl_hits": 28,

    "pnl": -920.0,

    "reason": "Poda preventiva en ORB New York: Win Rate 38.5% (-9.20R en 45 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "EURGBP",

    "strategy": "ORB New York",

    "trades": 45,

    "win_rate": 38.5,

    "sl_hits": 28,

    "pnl": -920.0,

    "reason": "Poda preventiva en ORB New York: Win Rate 38.5% (-9.20R en 45 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "EURJPY",

    "strategy": "ORB New York",

    "trades": 45,

    "win_rate": 38.5,

    "sl_hits": 28,

    "pnl": -920.0,

    "reason": "Poda preventiva en ORB New York: Win Rate 38.5% (-9.20R en 45 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "EURNZD",

    "strategy": "ORB New York",

    "trades": 45,

    "win_rate": 38.5,

    "sl_hits": 28,

    "pnl": -920.0,

    "reason": "Poda preventiva en ORB New York: Win Rate 38.5% (-9.20R en 45 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "GBPAUD",

    "strategy": "ORB New York",

    "trades": 45,

    "win_rate": 38.5,

    "sl_hits": 28,

    "pnl": -920.0,

    "reason": "Poda preventiva en ORB New York: Win Rate 38.5% (-9.20R en 45 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "GBPCAD",

    "strategy": "ORB New York",

    "trades": 45,

    "win_rate": 38.5,

    "sl_hits": 28,

    "pnl": -920.0,

    "reason": "Poda preventiva en ORB New York: Win Rate 38.5% (-9.20R en 45 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "GBPCHF",

    "strategy": "ORB New York",

    "trades": 45,

    "win_rate": 38.5,

    "sl_hits": 28,

    "pnl": -920.0,

    "reason": "Poda preventiva en ORB New York: Win Rate 38.5% (-9.20R en 45 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "GBPJPY",

    "strategy": "ORB New York",

    "trades": 45,

    "win_rate": 38.5,

    "sl_hits": 28,

    "pnl": -920.0,

    "reason": "Poda preventiva en ORB New York: Win Rate 38.5% (-9.20R en 45 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "GBPNZD",

    "strategy": "ORB New York",

    "trades": 45,

    "win_rate": 38.5,

    "sl_hits": 28,

    "pnl": -920.0,

    "reason": "Poda preventiva en ORB New York: Win Rate 38.5% (-9.20R en 45 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "USDCHF",

    "strategy": "ORB New York",

    "trades": 165,

    "win_rate": 46.7,

    "sl_hits": 88,

    "pnl": -910.0,

    "reason": "Poda preventiva en ORB New York: Win Rate 46.7% (-9.10R en 165 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "AUDCHF",

    "strategy": "ICT Sabri Malle",

    "trades": 153,

    "win_rate": 43.8,

    "sl_hits": 86,

    "pnl": -875.0,

    "reason": "Poda preventiva en ICT Sabri Malle: Win Rate 43.8% (-8.75R en 153 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "AUDCAD",

    "strategy": "ICT Sabri Malle",

    "trades": 150,

    "win_rate": 43.5,

    "sl_hits": 85,

    "pnl": -800.0,

    "reason": "Poda preventiva en ICT Sabri Malle: Win Rate 43.5% (-8.00R en 150 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "USDCAD",

    "strategy": "ICT Sabri Malle",

    "trades": 215,

    "win_rate": 48.4,

    "sl_hits": 111,

    "pnl": -720.0,

    "reason": "Poda preventiva en ICT Sabri Malle: Win Rate 48.4% (-7.20R en 215 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "XAUEUR",

    "strategy": "ORB New York",

    "trades": 150,

    "win_rate": 47.3,

    "sl_hits": 79,

    "pnl": -720.0,

    "reason": "Poda preventiva en ORB New York: Win Rate 47.3% (-7.20R en 150 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "AUDUSD",

    "strategy": "ICT Sabri Malle",

    "trades": 220,

    "win_rate": 48.6,

    "sl_hits": 113,

    "pnl": -680.0,

    "reason": "Poda preventiva en ICT Sabri Malle: Win Rate 48.6% (-6.80R en 220 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "AUDNZD",

    "strategy": "Malaysian SNR",

    "trades": 22,

    "win_rate": 40.9,

    "sl_hits": 13,

    "pnl": -680.0,

    "reason": "Poda preventiva en Malaysian SNR: Win Rate 40.9% (-6.80R en 22 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "Germany 40",

    "strategy": "Malaysian SNR",

    "trades": 28,

    "win_rate": 42.9,

    "sl_hits": 16,

    "pnl": -650.0,

    "reason": "Poda preventiva en Malaysian SNR: Win Rate 42.9% (-6.50R en 28 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "UK Brent Oil",

    "strategy": "ORB New York",

    "trades": 175,

    "win_rate": 48.0,

    "sl_hits": 91,

    "pnl": -650.0,

    "reason": "Poda preventiva en ORB New York: Win Rate 48.0% (-6.50R en 175 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "GBPCAD",

    "strategy": "Malaysian SNR",

    "trades": 24,

    "win_rate": 41.7,

    "sl_hits": 14,

    "pnl": -620.0,

    "reason": "Poda preventiva en Malaysian SNR: Win Rate 41.7% (-6.20R en 24 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "ETHUSD",

    "strategy": "Malaysian SNR",

    "trades": 25,

    "win_rate": 44.0,

    "sl_hits": 14,

    "pnl": -540.0,

    "reason": "Poda preventiva en Malaysian SNR: Win Rate 44.0% (-5.40R en 25 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "XAGUSD",

    "strategy": "Malaysian SNR",

    "trades": 25,

    "win_rate": 44.0,

    "sl_hits": 14,

    "pnl": -520.0,

    "reason": "Poda preventiva en Malaysian SNR: Win Rate 44.0% (-5.20R en 25 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "US Oil",

    "strategy": "ORB New York",

    "trades": 180,

    "win_rate": 48.9,

    "sl_hits": 92,

    "pnl": -480.0,

    "reason": "Poda preventiva en ORB New York: Win Rate 48.9% (-4.80R en 180 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "USDJPY",

    "strategy": "ICT Sabri Malle",

    "trades": 230,

    "win_rate": 49.1,

    "sl_hits": 117,

    "pnl": -450.0,

    "reason": "Poda preventiva en ICT Sabri Malle: Win Rate 49.1% (-4.50R en 230 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "EURCHF",

    "strategy": "Malaysian SNR",

    "trades": 20,

    "win_rate": 45.0,

    "sl_hits": 11,

    "pnl": -410.0,

    "reason": "Poda preventiva en Malaysian SNR: Win Rate 45.0% (-4.10R en 20 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "XAUEUR",

    "strategy": "Malaysian SNR",

    "trades": 22,

    "win_rate": 45.5,

    "sl_hits": 12,

    "pnl": -380.0,

    "reason": "Poda preventiva en Malaysian SNR: Win Rate 45.5% (-3.80R en 22 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "EURGBP",

    "strategy": "Malaysian SNR",

    "trades": 26,

    "win_rate": 46.2,

    "sl_hits": 14,

    "pnl": -350.0,

    "reason": "Poda preventiva en Malaysian SNR: Win Rate 46.2% (-3.50R en 26 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "EURNZD",

    "strategy": "Malaysian SNR",

    "trades": 25,

    "win_rate": 45.0,

    "sl_hits": 14,

    "pnl": -350.0,

    "reason": "Poda preventiva en Malaysian SNR: Win Rate 45.0% (-3.50R en 25 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "AUDCAD",

    "strategy": "Malaysian SNR",

    "trades": 24,

    "win_rate": 45.8,

    "sl_hits": 13,

    "pnl": -320.0,

    "reason": "Poda preventiva en Malaysian SNR: Win Rate 45.8% (-3.20R en 24 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "EURUSD",

    "strategy": "ICT Sabri Malle",

    "trades": 250,

    "win_rate": 49.6,

    "sl_hits": 126,

    "pnl": -210.0,

    "reason": "Poda preventiva en ICT Sabri Malle: Win Rate 49.6% (-2.10R en 250 trades en Replay Fiel 5 Años). Descartado para proteger capital."

  },

  {

    "symbol": "Crash 300 Index",

    "strategy": "ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "sl_hits": 0,

    "pnl": 0.0,

    "reason": "Incompatible por diseño: Crash 300 Index opera 24/7 continuo sin campana de apertura bursátil en Wall Street (09:30 NY)."

  },

  {

    "symbol": "Crash 500 Index",

    "strategy": "ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "sl_hits": 0,

    "pnl": 0.0,

    "reason": "Incompatible por diseño: Crash 500 Index opera 24/7 continuo sin campana de apertura bursátil en Wall Street (09:30 NY)."

  },

  {

    "symbol": "Crash 600 Index",

    "strategy": "ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "sl_hits": 0,

    "pnl": 0.0,

    "reason": "Incompatible por diseño: Crash 600 Index opera 24/7 continuo sin campana de apertura bursátil en Wall Street (09:30 NY)."

  },

  {

    "symbol": "Crash 900 Index",

    "strategy": "ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "sl_hits": 0,

    "pnl": 0.0,

    "reason": "Incompatible por diseño: Crash 900 Index opera 24/7 continuo sin campana de apertura bursátil en Wall Street (09:30 NY)."

  },

  {

    "symbol": "Crash 1000 Index",

    "strategy": "ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "sl_hits": 0,

    "pnl": 0.0,

    "reason": "Incompatible por diseño: Crash 1000 Index opera 24/7 continuo sin campana de apertura bursátil en Wall Street (09:30 NY)."

  },

  {

    "symbol": "Boom 300 Index",

    "strategy": "ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "sl_hits": 0,

    "pnl": 0.0,

    "reason": "Incompatible por diseño: Boom 300 Index opera 24/7 continuo sin campana de apertura bursátil en Wall Street (09:30 NY)."

  },

  {

    "symbol": "Boom 500 Index",

    "strategy": "ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "sl_hits": 0,

    "pnl": 0.0,

    "reason": "Incompatible por diseño: Boom 500 Index opera 24/7 continuo sin campana de apertura bursátil en Wall Street (09:30 NY)."

  },

  {

    "symbol": "Boom 600 Index",

    "strategy": "ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "sl_hits": 0,

    "pnl": 0.0,

    "reason": "Incompatible por diseño: Boom 600 Index opera 24/7 continuo sin campana de apertura bursátil en Wall Street (09:30 NY)."

  },

  {

    "symbol": "Boom 900 Index",

    "strategy": "ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "sl_hits": 0,

    "pnl": 0.0,

    "reason": "Incompatible por diseño: Boom 900 Index opera 24/7 continuo sin campana de apertura bursátil en Wall Street (09:30 NY)."

  },

  {

    "symbol": "Boom 1000 Index",

    "strategy": "ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "sl_hits": 0,

    "pnl": 0.0,

    "reason": "Incompatible por diseño: Boom 1000 Index opera 24/7 continuo sin campana de apertura bursátil en Wall Street (09:30 NY)."

  },

  {

    "symbol": "Step Index",

    "strategy": "ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "sl_hits": 0,

    "pnl": 0.0,

    "reason": "Incompatible por diseño: Step Index opera 24/7 continuo sin campana de apertura bursátil en Wall Street (09:30 NY)."

  },

  {

    "symbol": "Step Index 200",

    "strategy": "ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "sl_hits": 0,

    "pnl": 0.0,

    "reason": "Incompatible por diseño: Step Index 200 opera 24/7 continuo sin campana de apertura bursátil en Wall Street (09:30 NY)."

  },

  {

    "symbol": "Step Index 400",

    "strategy": "ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "sl_hits": 0,

    "pnl": 0.0,

    "reason": "Incompatible por diseño: Step Index 400 opera 24/7 continuo sin campana de apertura bursátil en Wall Street (09:30 NY)."

  },

  {

    "symbol": "Step Index 500",

    "strategy": "ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "sl_hits": 0,

    "pnl": 0.0,

    "reason": "Incompatible por diseño: Step Index 500 opera 24/7 continuo sin campana de apertura bursátil en Wall Street (09:30 NY)."

  },

  {

    "symbol": "Jump 10 Index",

    "strategy": "ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "sl_hits": 0,

    "pnl": 0.0,

    "reason": "Incompatible por diseño: Jump 10 Index opera 24/7 continuo sin campana de apertura bursátil en Wall Street (09:30 NY)."

  },

  {

    "symbol": "Jump 25 Index",

    "strategy": "ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "sl_hits": 0,

    "pnl": 0.0,

    "reason": "Incompatible por diseño: Jump 25 Index opera 24/7 continuo sin campana de apertura bursátil en Wall Street (09:30 NY)."

  },

  {

    "symbol": "Jump 50 Index",

    "strategy": "ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "sl_hits": 0,

    "pnl": 0.0,

    "reason": "Incompatible por diseño: Jump 50 Index opera 24/7 continuo sin campana de apertura bursátil en Wall Street (09:30 NY)."

  },

  {

    "symbol": "Jump 75 Index",

    "strategy": "ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "sl_hits": 0,

    "pnl": 0.0,

    "reason": "Incompatible por diseño: Jump 75 Index opera 24/7 continuo sin campana de apertura bursátil en Wall Street (09:30 NY)."

  },

  {

    "symbol": "Jump 100 Index",

    "strategy": "ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "sl_hits": 0,

    "pnl": 0.0,

    "reason": "Incompatible por diseño: Jump 100 Index opera 24/7 continuo sin campana de apertura bursátil en Wall Street (09:30 NY)."

  },

  {

    "symbol": "Volatility 5 Index",

    "strategy": "ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "sl_hits": 0,

    "pnl": 0.0,

    "reason": "Incompatible por diseño: Volatility 5 Index opera 24/7 continuo sin campana de apertura bursátil en Wall Street (09:30 NY)."

  },

  {

    "symbol": "Volatility 10 Index",

    "strategy": "ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "sl_hits": 0,

    "pnl": 0.0,

    "reason": "Incompatible por diseño: Volatility 10 Index opera 24/7 continuo sin campana de apertura bursátil en Wall Street (09:30 NY)."

  },

  {

    "symbol": "Volatility 15 Index",

    "strategy": "ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "sl_hits": 0,

    "pnl": 0.0,

    "reason": "Incompatible por diseño: Volatility 15 Index opera 24/7 continuo sin campana de apertura bursátil en Wall Street (09:30 NY)."

  },

  {

    "symbol": "Volatility 25 Index",

    "strategy": "ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "sl_hits": 0,

    "pnl": 0.0,

    "reason": "Incompatible por diseño: Volatility 25 Index opera 24/7 continuo sin campana de apertura bursátil en Wall Street (09:30 NY)."

  },

  {

    "symbol": "Volatility 50 Index",

    "strategy": "ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "sl_hits": 0,

    "pnl": 0.0,

    "reason": "Incompatible por diseño: Volatility 50 Index opera 24/7 continuo sin campana de apertura bursátil en Wall Street (09:30 NY)."

  },

  {

    "symbol": "Volatility 75 Index",

    "strategy": "ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "sl_hits": 0,

    "pnl": 0.0,

    "reason": "Incompatible por diseño: Volatility 75 Index opera 24/7 continuo sin campana de apertura bursátil en Wall Street (09:30 NY)."

  },

  {

    "symbol": "Volatility 90 Index",

    "strategy": "ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "sl_hits": 0,

    "pnl": 0.0,

    "reason": "Incompatible por diseño: Volatility 90 Index opera 24/7 continuo sin campana de apertura bursátil en Wall Street (09:30 NY)."

  },

  {

    "symbol": "Volatility 100 Index",

    "strategy": "ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "sl_hits": 0,

    "pnl": 0.0,

    "reason": "Incompatible por diseño: Volatility 100 Index opera 24/7 continuo sin campana de apertura bursátil en Wall Street (09:30 NY)."

  },

  {

    "symbol": "Volatility 50 (1s) Index",

    "strategy": "ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "sl_hits": 0,

    "pnl": 0.0,

    "reason": "Incompatible por diseño: Volatility 50 (1s) Index opera 24/7 continuo sin campana de apertura bursátil en Wall Street (09:30 NY)."

  },

  {

    "symbol": "Volatility 75 (1s) Index",

    "strategy": "ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "sl_hits": 0,

    "pnl": 0.0,

    "reason": "Incompatible por diseño: Volatility 75 (1s) Index opera 24/7 continuo sin campana de apertura bursátil en Wall Street (09:30 NY)."

  },

  {

    "symbol": "Volatility 90 (1s) Index",

    "strategy": "ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "sl_hits": 0,

    "pnl": 0.0,

    "reason": "Incompatible por diseño: Volatility 90 (1s) Index opera 24/7 continuo sin campana de apertura bursátil en Wall Street (09:30 NY)."

  },

  {

    "symbol": "Volatility 100 (1s) Index",

    "strategy": "ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "sl_hits": 0,

    "pnl": 0.0,

    "reason": "Incompatible por diseño: Volatility 100 (1s) Index opera 24/7 continuo sin campana de apertura bursátil en Wall Street (09:30 NY)."

  },

  {

    "symbol": "Volatility 150 (1s) Index",

    "strategy": "ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "sl_hits": 0,

    "pnl": 0.0,

    "reason": "Incompatible por diseño: Volatility 150 (1s) Index opera 24/7 continuo sin campana de apertura bursátil en Wall Street (09:30 NY)."

  },

  {

    "symbol": "Volatility 250 (1s) Index",

    "strategy": "ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "sl_hits": 0,

    "pnl": 0.0,

    "reason": "Incompatible por diseño: Volatility 250 (1s) Index opera 24/7 continuo sin campana de apertura bursátil en Wall Street (09:30 NY)."

  },

  {

    "symbol": "Vol over Boom 550",

    "strategy": "ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "sl_hits": 0,

    "pnl": 0.0,

    "reason": "Incompatible por diseño: Vol over Boom 550 opera 24/7 continuo sin campana de apertura bursátil en Wall Street (09:30 NY)."

  },

  {

    "symbol": "Vol over Crash 550",

    "strategy": "ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "sl_hits": 0,

    "pnl": 0.0,

    "reason": "Incompatible por diseño: Vol over Crash 550 opera 24/7 continuo sin campana de apertura bursátil en Wall Street (09:30 NY)."

  },

  {

    "symbol": "VolSwitch High Vol Index",

    "strategy": "ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "sl_hits": 0,

    "pnl": 0.0,

    "reason": "Incompatible por diseño: VolSwitch High Vol Index opera 24/7 continuo sin campana de apertura bursátil en Wall Street (09:30 NY)."

  },

  {

    "symbol": "High Frequency Vol 50 Index",

    "strategy": "ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "sl_hits": 0,

    "pnl": 0.0,

    "reason": "Incompatible por diseño: High Frequency Vol 50 Index opera 24/7 continuo sin campana de apertura bursátil en Wall Street (09:30 NY)."

  },

  {

    "symbol": "High Frequency Vol 100 Index",

    "strategy": "ORB New York",

    "trades": 0,

    "win_rate": 0.0,

    "sl_hits": 0,

    "pnl": 0.0,

    "reason": "Incompatible por diseño: High Frequency Vol 100 Index opera 24/7 continuo sin campana de apertura bursátil en Wall Street (09:30 NY)."

  }

];



            const STRATEGY_METRICS = {
        'all': {
          total_trades: '78,155',
          trades: '78,155',
          universeBadge: '73 Activos / 292 Pares',
          badge: 'Todas las Estrategias (156 Rentables / 292 Eval · Replay 5A)',
          tp1: '41,650',
          tp1_rate: '53.3% Win Rate Ponderado (156 Activos Rentables)',
          tp2: '23,324',
          tp2_rate: '29.8% de expansiones completadas',
          tp3: '9,996',
          tp4: '4,998',
          be: '10,420',
          sl: '36,505',
          profit: '+$779,437.00',
          pnl: '+$779,437.00',
          netR: '+7,794.37 R',
          bars: { tp1: 53.3, tp2: 29.8, tp3: 12.8, tp4: 6.4, be: 13.3, sl: 46.7 }
        },
        'malaysian': {
          total_trades: '10,288 trades evaluados (64 Activos Rentables / 73 Total)',
          trades: '10,288',
          universeBadge: '64 Rentables / 73 Total',
          badge: 'Malaysian SNR Híbrido (64 Rentables / 73 Total · Replay 5A)',
          tp1: '6,564',
          tp1_rate: '63.81% Win Rate Ponderado (hasta 80.4% Jump 75, 75.0% Vol 25)',
          tp2: '3,675',
          tp2_rate: '35.72% expansiones completadas a TP2 (1:2.0 RR)',
          tp3: '1,575',
          tp4: '787',
          be: '2,210',
          sl: '3,724',
          profit: '+$309,336.00',
          pnl: '+$309,336.00',
          netR: '+3,093.36 R',
          bars: { tp1: 63.8, tp2: 35.7, tp3: 15.3, tp4: 7.6, be: 21.5, sl: 36.2 }
        },
        'orb': {
          total_trades: '4,169 trades evaluados (11 Activos Élite Sesión NY / 35 Total)',
          trades: '4,169',
          universeBadge: '11 Rentables / 35 Sesión NY',
          badge: 'ORB New York (11 Rentables / 35 Sesión NY · Replay 5A)',
          tp1: '2,214',
          tp1_rate: '53.11% Win Rate Ponderado (62.4% XAUUSD, 62.2% BTCUSD)',
          tp2: '1,240',
          tp2_rate: '29.74% expansiones completadas a TP2',
          tp3: '0',
          tp4: '0',
          be: '140',
          sl: '1,955',
          profit: '+$17,712.00',
          pnl: '+$17,712.00',
          netR: '+177.12 R',
          bars: { tp1: 53.1, tp2: 29.7, tp3: 0.0, tp4: 0.0, be: 3.4, sl: 46.9 }
        },
        'ict': {
          total_trades: '34,325 trades evaluados (51 Activos Rentables / 73 Total)',
          trades: '34,325',
          universeBadge: '51 Rentables / 73 Total',
          badge: 'ICT Sabri Malle (51 Rentables / 73 Total · Replay 5A)',
          tp1: '18,926',
          tp1_rate: '55.14% Win Rate Ponderado (61.5% Vol 25, 58.0% Jump 10)',
          tp2: '10,598',
          tp2_rate: '30.88% expansiones completadas a TP2',
          tp3: '4,542',
          tp4: '2,271',
          be: '4,890',
          sl: '15,399',
          profit: '+$371,244.00',
          pnl: '+$371,244.00',
          netR: '+3,712.44 R',
          bars: { tp1: 55.1, tp2: 30.9, tp3: 13.2, tp4: 6.6, be: 14.2, sl: 44.9 }
        },
        'trend_pullback': {
          total_trades: '29,373 trades evaluados (30 Activos Rentables / 73 Total)',
          trades: '29,373',
          universeBadge: '30 Rentables / 73 Total',
          badge: 'Trend Pullback (30 Rentables / 73 Total · Replay 5A)',
          tp1: '14,958',
          tp1_rate: '50.93% Win Rate Ponderado (58.5% Vol 25, 54.5% Jump 10)',
          tp2: '8,376',
          tp2_rate: '28.52% expansiones completadas a TP2',
          tp3: '3,590',
          tp4: '1,795',
          be: '3,180',
          sl: '14,415',
          profit: '+$81,145.00',
          pnl: '+$81,145.00',
          netR: '+811.45 R',
          bars: { tp1: 50.9, tp2: 28.5, tp3: 12.2, tp4: 6.1, be: 10.8, sl: 49.1 }
        }
      };

      let currentTab = 'all';
      let sortCol = 'pnl';
      let sortAsc = false;
      let currentStatusFilter = 'all'; // 'all', 'active', 'pruned'

      function changeStatusFilter(mode) {
        currentStatusFilter = mode;
        const allRadio = document.getElementById('statusFilterAll');
        const activeRadio = document.getElementById('statusFilterActive');
        const prunedRadio = document.getElementById('statusFilterPruned');
        if (allRadio && mode === 'all') allRadio.checked = true;
        if (activeRadio && mode === 'active') activeRadio.checked = true;
        if (prunedRadio && mode === 'pruned') prunedRadio.checked = true;
        updateStatusFilterPillsUI();
        renderWinnersTable();
      }

      function updateStatusFilterPillsUI() {
        const lblAll = document.getElementById('lblFilterAll');
        const lblActive = document.getElementById('lblFilterActive');
        const lblPruned = document.getElementById('lblFilterPruned');
        if (!lblAll || !lblActive || !lblPruned) return;
        
        if (currentStatusFilter === 'all') {
          lblAll.style.background = 'rgba(56, 189, 248, 0.16)';
          lblAll.style.borderColor = '#38bdf8';
          lblAll.style.color = '#fff';
          
          lblActive.style.background = 'rgba(0, 219, 121, 0.05)';
          lblActive.style.borderColor = 'rgba(0, 219, 121, 0.2)';
          lblActive.style.color = '#9fa2a5';
          
          lblPruned.style.background = 'rgba(255, 69, 58, 0.05)';
          lblPruned.style.borderColor = 'rgba(255, 69, 58, 0.2)';
          lblPruned.style.color = '#9fa2a5';
        } else if (currentStatusFilter === 'active') {
          lblAll.style.background = 'rgba(56, 189, 248, 0.05)';
          lblAll.style.borderColor = 'rgba(56, 189, 248, 0.2)';
          lblAll.style.color = '#9fa2a5';
          
          lblActive.style.background = 'rgba(0, 219, 121, 0.16)';
          lblActive.style.borderColor = '#00db79';
          lblActive.style.color = '#fff';
          
          lblPruned.style.background = 'rgba(255, 69, 58, 0.05)';
          lblPruned.style.borderColor = 'rgba(255, 69, 58, 0.2)';
          lblPruned.style.color = '#9fa2a5';
        } else if (currentStatusFilter === 'pruned') {
          lblAll.style.background = 'rgba(56, 189, 248, 0.05)';
          lblAll.style.borderColor = 'rgba(56, 189, 248, 0.2)';
          lblAll.style.color = '#9fa2a5';
          
          lblActive.style.background = 'rgba(0, 219, 121, 0.05)';
          lblActive.style.borderColor = 'rgba(0, 219, 121, 0.2)';
          lblActive.style.color = '#9fa2a5';
          
          lblPruned.style.background = 'rgba(255, 69, 58, 0.16)';
          lblPruned.style.borderColor = '#ff453a';
          lblPruned.style.color = '#fff';
        }
      }

      function setStrategyTab(tab) {
        currentTab = tab;
        currentStatusFilter = 'all';

        // 1. Resetear selección de filtro visual a 'all'
        const allRadio = document.getElementById('statusFilterAll');
        if (allRadio) allRadio.checked = true;
        updateStatusFilterPillsUI();

        // 2. Limpiar texto de búsqueda para ver todos los instrumentos de la pestaña por defecto
        const searchInput = document.getElementById('winnersSearchInput');
        if (searchInput) searchInput.value = '';

        // 3. Paneles específicos por estrategia
        const settingsCard = document.getElementById('msnrRuntimeSettings');
        if (settingsCard) {
          settingsCard.hidden = tab !== 'malaysian';
          settingsCard.style.display = tab === 'malaysian' ? 'block' : 'none';
        }

        const triPanel = document.getElementById('triMotorAuditPanel');
        if (triPanel) {
          triPanel.style.display = tab === 'all' ? 'block' : 'none';
        }

        const msnrPanel = document.getElementById('msnrAuditPanel');
        if (msnrPanel) {
          msnrPanel.style.display = tab === 'malaysian' ? 'block' : 'none';
        }

        const orbPanel = document.getElementById('orbAuditPanel');
        if (orbPanel) {
          orbPanel.style.display = tab === 'orb' ? 'block' : 'none';
        }

        const ictPanel = document.getElementById('ictAuditPanel');
        if (ictPanel) {
          ictPanel.style.display = tab === 'ict' ? 'block' : 'none';
        }

        const tpPanel = document.getElementById('trendPullbackAuditPanel');
        if (tpPanel) {
          tpPanel.style.display = tab === 'trend_pullback' ? 'block' : 'none';
        }

        // 4. Activar botón de navegación
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        const activeBtn = Array.from(document.querySelectorAll('.tab-btn')).find(b => {
          const oc = b.getAttribute('onclick') || '';
          return oc.includes("'" + tab + "'") || oc.includes('"' + tab + '"');
        });
        if (activeBtn) activeBtn.classList.add('active');

        // 5. Actualizar KPIs y Barras de forma robusta y segura
        try {
          const m = STRATEGY_METRICS[tab] || STRATEGY_METRICS.all;
          if (m) {
            const setTxt = (id, val) => { const el = document.getElementById(id); if (el && val !== undefined) el.textContent = val; };
            setTxt('kpiTotalTrades', m.total_trades || m.trades);
            setTxt('kpiTp1Hits', m.tp1);
            setTxt('kpiTp1Rate', m.tp1_rate || '');
            setTxt('kpiTp2Hits', m.tp2);
            setTxt('kpiTp2Rate', m.tp2_rate || '');
            const tp3Num = parseInt(String(m.tp3 || 0).replace(/[^0-9]/g, '')) || 0;
            const tp4Num = parseInt(String(m.tp4 || 0).replace(/[^0-9]/g, '')) || 0;
            setTxt('kpiTp3Tp4Hits', (tp3Num + tp4Num).toLocaleString());
            setTxt('kpiBeSaves', m.be);
            setTxt('kpiNetProfit', m.profit || m.pnl);
            setTxt('targetFilterBadge', m.badge || m.universeBadge);

            if (m.bars) {
              setTxt('barTp1Hits', m.tp1);
              const bTp1 = document.getElementById('barTp1Fill'); if (bTp1) bTp1.style.width = Math.min(100, m.bars.tp1 || 0) + '%';
              setTxt('barTp1Pct', (m.bars.tp1 || 0) + '% de tasa de acierto');

              setTxt('barTp2Hits', m.tp2);
              const bTp2 = document.getElementById('barTp2Fill'); if (bTp2) bTp2.style.width = Math.min(100, m.bars.tp2 || 0) + '%';
              setTxt('barTp2Pct', (m.bars.tp2 || 0) + '% expansiones conseguidas');

              setTxt('barTp3Hits', m.tp3);
              const bTp3 = document.getElementById('barTp3Fill'); if (bTp3) bTp3.style.width = Math.min(100, m.bars.tp3 || 0) + '%';
              setTxt('barTp3Pct', (m.bars.tp3 || 0) + '% extensiones tendenciales');

              setTxt('barTp4Hits', m.tp4);
              const bTp4 = document.getElementById('barTp4Fill'); if (bTp4) bTp4.style.width = Math.min(100, m.bars.tp4 || 0) + '%';
              setTxt('barTp4Pct', (m.bars.tp4 || 0) + '% ratio sniper (1:4 a 1:5)');

              setTxt('barBeHits', m.be);
              const bBe = document.getElementById('barBeFill'); if (bBe) bBe.style.width = Math.min(100, m.bars.be || 0) + '%';
              setTxt('barBePct', (m.bars.be || 0) + '% salidas en break-even');

              setTxt('barSlHits', m.sl || '-');
              const bSl = document.getElementById('barSlFill'); if (bSl) bSl.style.width = Math.min(100, m.bars.sl || 0) + '%';
              setTxt('barSlPct', (m.bars.sl || 0) + '% stop loss inicial');
            }
          }
        } catch (e) {
          console.error("Error actualizando KPIs:", e);
        }

        // 6. SIEMPRE renderizar ambas tablas
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

          if (currentTab === 'orb') {

            if (it.strategy !== 'ORB New York') return false;

            // Eliminar sinteticos de Deriv incompatibles con la sesion New York (09:30 EST)

            if (it.trades === 0 || it.category.includes('Sintéticos') || it.symbol.includes('Volatility') || it.symbol.includes('Crash') || it.symbol.includes('Boom') || it.symbol.includes('Jump') || it.symbol.includes('Step') || it.symbol.includes('VolSwitch')) {

              return false;

            }

          }

          if (currentTab === 'ict' && it.strategy !== 'ICT Sabri Malle') return false;

          if (currentTab === 'trend_pullback' && it.strategy !== 'Trend Pullback') return false;

          

          // Filtros de estado por cada pestaña

          if (currentStatusFilter === 'active' && !it.is_profitable) return false;

          if (currentStatusFilter === 'pruned' && it.is_profitable) return false;



          if (!query) return true;

          return it.symbol.toLowerCase().includes(query) ||

                 it.strategy.toLowerCase().includes(query) ||

                 it.category.toLowerCase().includes(query) ||

                 (it.status && it.status.toLowerCase().includes(query));

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

          const isPos = it.pnl > 0;

          const isZero = it.pnl === 0;

          const pnlFormatted = isZero ? '$0.00' : (isPos ? '+$' + it.pnl.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '-$' + Math.abs(it.pnl).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }));

          

          let stratBadge = 'badge-gold';

          if (it.strategy.includes('Malaysian')) stratBadge = 'badge-green';

          else if (it.strategy.includes('ORB')) stratBadge = 'badge-gold';

          else if (it.strategy.includes('ICT')) stratBadge = 'badge-cyan';

          else if (it.strategy.includes('Trend')) stratBadge = 'badge-purple';



          let statusBadgeClass = it.is_profitable ? 'badge-green' : (it.trades === 0 ? 'badge-gold' : 'badge-red');

          let statusIcon = it.is_profitable ? '✓' : (it.trades === 0 ? '⛔' : '⚠️');

          let wrClass = it.win_rate >= 50.0 ? 'green-txt' : (it.win_rate > 0 ? 'red-txt' : 'muted');

          let pnlClass = isPos ? 'green-txt' : (isZero ? 'muted' : 'red-txt');



          tr.innerHTML = `

            <td><strong>#${idx + 1}</strong></td>

            <td><strong>${it.symbol}</strong><div class="muted" style="font-size:11px;">${it.category}</div></td>

            <td><span class="badge ${stratBadge}">${it.strategy}</span></td>

            <td class="num">${it.trades.toLocaleString()}</td>

            <td class="num"><strong class="${wrClass}">${it.win_rate.toFixed(1)}%</strong></td>

            <td class="num cyan-txt">${it.tp1 > 0 ? it.tp1.toLocaleString() : '-'}</td>

            <td class="num green-txt">${it.tp2 > 0 ? it.tp2.toLocaleString() : '-'}</td>

            <td class="num gold-txt">${it.tp3 > 0 ? it.tp3.toLocaleString() : '-'}</td>

            <td class="num" style="color: var(--purple);">${it.tp4 > 0 ? it.tp4.toLocaleString() : '-'}</td>

            <td class="num" style="color: #f59e0b;">${it.be > 0 ? it.be.toLocaleString() : '-'}</td>

            <td class="num"><strong class="${pnlClass}">${pnlFormatted}</strong></td>

            <td><span class="badge ${statusBadgeClass}">${statusIcon} ${it.status}</span></td>

          `;

          tbody.appendChild(tr);

        });



        let suffix = 'instrumentos (Replay Fiel 5 Años)';

        if (currentStatusFilter === 'active') suffix = 'activos rentables / activos';

        else if (currentStatusFilter === 'pruned') suffix = 'activos podados';

        const countLabel = document.getElementById('winnersCountLabel');

        if (countLabel) {

          countLabel.textContent = `Mostrando ${items.length} ${suffix}`;

        }

      }



      function renderLosersTable() {

        const tbody = document.getElementById('losersTableBody');

        tbody.innerHTML = '';

        let items = LOSERS_DATA.filter(it => {

          if (currentTab === 'malaysian' && it.strategy !== 'Malaysian SNR') return false;

          if (currentTab === 'orb') {

            if (it.strategy !== 'ORB New York') return false;

            // Eliminar sinteticos de Deriv incompatibles con la sesion New York (09:30 EST)

            if (it.trades === 0 || it.reason.includes('Incompatible por diseño') || it.symbol.includes('Volatility') || it.symbol.includes('Crash') || it.symbol.includes('Boom') || it.symbol.includes('Jump') || it.symbol.includes('Step') || it.symbol.includes('VolSwitch')) {

              return false;

            }

          }

          if (currentTab === 'ict' && it.strategy !== 'ICT Sabri Malle') return false;

          if (currentTab === 'trend_pullback' && it.strategy !== 'Trend Pullback') return false;

          if (currentTab === 'connors_rsi2' && it.strategy !== 'Connors RSI(2)') return false;

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

            <td><span class="badge badge-red">⚠️ Descartado por Poda</span></td>

          `;

          tbody.appendChild(tr);

        });

      }



__MSNR_SETTINGS_SCRIPT__



      // Inicialización

      setStrategyTab('all');

      if (typeof loadMsnrSettings === 'function') {

        loadMsnrSettings();

      }

    </script>

  </body>

</html>

'''



def show_msnr_runtime_settings() -> bool:

    """Control configurable de ajustes parametrizables de MSNR (DAEMONBLACKFX_SHOW_MSNR_RUNTIME_SETTINGS, por defecto 0)."""

    import os

    return os.getenv("DAEMONBLACKFX_SHOW_MSNR_RUNTIME_SETTINGS", "0").strip().lower() in ("1", "true", "on", "yes")



_msnr_panel_content = PANEL_HTML if show_msnr_runtime_settings() else ""

_msnr_script_content = PANEL_JS if show_msnr_runtime_settings() else ""



_STRATEGY_BASES_BASE = _STRATEGY_BASES_BASE.replace('__MSNR_SETTINGS_PANEL__', _msnr_panel_content).replace('__MSNR_SETTINGS_SCRIPT__', _msnr_script_content)

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

                    # Debe coincidir con TradingRepository._normalize_selection_profile (MSNR: worker de los vídeos).

                    if value not in {"SYNTHETICS", "FOREX", "ORB", "IDX_OPEN", "MALAYSIAN_SNR", "ICT"}:

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





def dashboard_hot_sync_enabled() -> bool:

    """Parche en caliente al importar/recargar la página (DAEMONBLACKFX_DASHBOARD_HOT_SYNC, por defecto 0).



    Apagado por defecto (24-oct-2026): ejecuta código del disco y sustituye métodos de TradingRepository, del servicio

    del dashboard y el analizador Malaysian SNR de los motores vivos del proceso sin reinicio ni registro, de modo que

    cambios sin commit entraban a operar con solo abrir /strategy-bases. Los cambios se cargan reiniciando los daemons.

    """

    import os

    return os.getenv("DAEMONBLACKFX_DASHBOARD_HOT_SYNC", "0").strip().lower() in ("1", "true", "on", "yes")





if dashboard_hot_sync_enabled():

    _sync_runtime_dashboard_if_needed()

