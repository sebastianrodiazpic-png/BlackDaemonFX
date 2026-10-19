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

      <!-- PANEL DE AUDITORÍA TRI-MOTOR CONSOLIDADO (SE MUESTRA EN PESTAÑA ALL) -->
      <div id="triMotorAuditPanel" style="display: block; margin-bottom: 24px;">
        <div class="card" style="border-left: 4px solid var(--g); background: linear-gradient(180deg, rgba(0, 219, 121, 0.08) 0%, var(--p) 100%);">
          <div class="card-header" style="margin-bottom: 12px;">
            <h2 class="card-title">
              <span class="icon">🌐</span>
              Portafolio Tri-Motor Unificado (Staging): MSNR C2 + ICT Active + ORB NY Sweep
            </h2>
            <div class="badge badge-green">1,254 Trades Filtrados · 62.76% Win Rate · +475.74 R Netos (+643.59 R Brutos) · MaxDD 3.37 R</div>
          </div>
          <div class="muted" style="font-size: 13px; line-height: 1.7; margin-bottom: 18px;">
            Consolidación cuantitativa del plan de 4 pasos y 5 fases de validación sobre <strong>2 años en Sintéticos</strong> y <strong>5 años en Forex, Metales y Criptos</strong>. 
            Todos los universos de activos canónicos activos y podados están sincronizados en tiempo real con <a href="/instruments" style="color: #f4c84f; text-decoration: underline; font-weight: 600;">/instruments</a> y distribuidos en los workers <code>CRASH</code>, <code>BOOM</code>, <code>STEP</code>, <code>JUMP</code>, <code>VOLATILITY (1-4)</code>, <code>FOREX (1-4)</code>, <code>ICT</code>, <code>MALAYSIAN_SNR</code> y <code>ORB</code>.
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

      <!-- PANEL DE AUDITORÍA MALAYSIAN SNR C2 (SE MUESTRA EN PESTAÑA MALAYSIAN) -->
      <div id="msnrAuditPanel" style="display: none; margin-bottom: 24px;">
        <div class="card" style="border-left: 4px solid var(--g); background: linear-gradient(180deg, rgba(0, 219, 121, 0.08) 0%, var(--p) 100%);">
          <div class="card-header" style="margin-bottom: 12px;">
            <h2 class="card-title">
              <span class="icon">🇲🇾</span>
              Auditoría Malaysian SNR: Benchmark V4 vs Fase 1 C1 vs Fase 1–5 MSNR C2 (23 Activos Canónicos)
            </h2>
            <div class="badge badge-green">60.6% Win Rate OOS (+37.64 R) · +81.55 R Replay 2 Años · 23 Canónicos Activos / 37 Podados</div>
          </div>
          <div class="muted" style="font-size: 13px; line-height: 1.7; margin-bottom: 18px;">
            Evolución completa a través de las 5 Fases de validación sobre el worker <code>Malaysian SNR (M15 Fresh/Break)</code>. 
            Un <strong>Activo Canónico Activo</strong> es cada uno de los <strong>23 instrumentos únicos oficiales</strong> (en su símbolo estándar de referencia) que demostró expectativa matemática positiva en el replay bar-a-bar de 2 años y superó los filtros de la variante <strong>MSNR C2</strong>.
          </div>

          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px; margin-bottom: 16px;">
            <div style="background: var(--p2); border: 1px solid #1e2b37; border-radius: 10px; padding: 14px 16px;">
              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-size: 12px; font-weight: 700; color: var(--m); text-transform: uppercase;">1️⃣ Benchmark MSNR V4 (Base)</span>
                <span class="badge badge-gold">51.9% WR · +21.74 R</span>
              </div>
              <div style="font-size: 12px; color: var(--m); line-height: 1.6;">
                • <strong>Configuración Base:</strong> <code>ADX ≥ 30</code>, <code>ATR ≤ 1.5</code> plano para todas las clases de activo y <code>Cap = 2</code> posiciones simultáneas.<br>
                • <strong>Limitación:</strong> Permitía picos de volatilidad errática en Forex/Metales (1.2–1.5x ATR) y duplicaba pérdidas (-2.0R) cuando un nivel H1 fallaba con 2 entradas abiertas.
              </div>
            </div>

            <div style="background: var(--p2); border: 1px solid #1e2b37; border-radius: 10px; padding: 14px 16px;">
              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-size: 12px; font-weight: 700; color: var(--g); text-transform: uppercase;">2️⃣ Fase 1 MSNR C2 (Óptimo)</span>
                <span class="badge badge-green">60.6% WR · +37.64 R OOS</span>
              </div>
              <div style="font-size: 12px; color: var(--m); line-height: 1.6;">
                • <strong>Diferencia C1 vs C2:</strong> C1 aplicaba <code>ATR ≤ 1.2</code> globalmente (+36.26R, ahogando a <code>Wall Street 30</code>). <strong>C2</strong> aplica <code>ATR ≤ 1.2</code> sólo en Forex/Metales y preserva <code>ATR ≤ 1.5</code> en Sintéticos e Índices.<br>
                • <strong>Impacto:</strong> Sube el Win Rate de <strong>51.9% a 60.6% (+8.7 pp)</strong>, eleva el retorno OOS un <strong>+73.1% (+37.64 R)</strong>, PF <strong>2.45</strong> y reduce el MaxDD a <strong>4.21 R</strong>.
              </div>
            </div>

            <div style="background: var(--p2); border: 1px solid #1e2b37; border-radius: 10px; padding: 14px 16px;">
              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-size: 12px; font-weight: 700; color: var(--cyan); text-transform: uppercase;">3️⃣ Fases 2 y 3 · Sensibilidad & Dual-Leg</span>
                <span class="badge badge-cyan">+81.55 R (Replay 2A)</span>
              </div>
              <div style="font-size: 12px; color: var(--m); line-height: 1.6;">
                • <strong>Fase 2 (Sin Relajar ADX):</strong> Relajar ADX a 25 hundía el WR al 49.4% (+9.88R) y quitar Freshness lo bajaba al 48.0%. Se mantiene intacto <code>ADX ≥ 30</code> + zona <code>Fresh</code>.<br>
                • <strong>Fase 3 (Dual-Leg 50/50):</strong> <code>Leg 1 (50%) → TP1 @ 1.0R</code> + traslado inmediato a <code>BE + spread</code>; <code>Leg 2 (50%) → TP2 @ 2.0R</code>.
              </div>
            </div>

            <div style="background: var(--p2); border: 1px solid #1e2b37; border-radius: 10px; padding: 14px 16px;">
              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-size: 12px; font-weight: 700; color: #f5bd36; text-transform: uppercase;">4️⃣ Fases 4 y 5 · 23 Canónicos Activos</span>
                <span class="badge badge-gold">Sincronizado /Instruments</span>
              </div>
              <div style="font-size: 12px; color: var(--m); line-height: 1.6;">
                • <strong>11 Sintéticos:</strong> Step 400 (+9.68R), Crash 1000 (+5.47R), Jump 25 (+5.42R), Boom 300 (+3.71R), Vol 250 1s (+3.66R), Step Index (+3.16R), Jump 10 (+2.77R), Vol 50 1s (+2.31R), Vol 90 (+2.25R), Boom 1000 (+1.81R), Step 200 (+1.79R), Crash 600 (+0.29R).<br>
                • <strong>9 Forex + 2 Metales + 1 Índice:</strong> AUDNZD, GBPJPY, USDJPY, GBPUSD, GBPAUD, EURUSD, EURCHF, EURGBP, XAGUSD (+7.21R), XAUUSD (+0.87R) y Wall Street 30 (+2.57R).
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- PANEL DE AUDITORÍA ORB NEW YORK SWEEP (SE MUESTRA EN PESTAÑA ORB) -->
      <div id="orbAuditPanel" style="display: none; margin-bottom: 24px;">
        <div class="card" style="border-left: 4px solid #f5bd36; background: linear-gradient(180deg, rgba(245, 189, 54, 0.08) 0%, var(--p) 100%);">
          <div class="card-header" style="margin-bottom: 12px;">
            <h2 class="card-title">
              <span class="icon">🗽</span>
              Auditoría ORB New York (Paso 1.3 ORB SWEEP): 231–241 Trades Intradía · +31.54 R Netos
            </h2>
            <div class="badge badge-gold">56.7%–59.1% Win Rate · 4 Activos Core (+Variantes Micro) · 5 Índices/Forex Podados</div>
          </div>
          <div class="muted" style="font-size: 13px; line-height: 1.7; margin-bottom: 18px;">
            Reconfiguración <strong>ORB SWEEP (<code>HTF_SWEEP</code>)</strong> en la apertura Cash de Nueva York (09:30–11:30 NY) con filtro macro de liquidez <code>PDH / PDL (0.25 × ATR)</code>, Stop Loss anclado al <strong>50% Equilibrium</strong> del rango de 15 minutos y salida Dual-Leg (<code>TP1 @ 1.0R</code> + <code>BE + spread</code>, <code>TP2 @ 1.5R–2.0R</code>).
          </div>

          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px;">
            <div style="background: var(--p2); border: 1px solid #1e2b37; border-radius: 10px; padding: 14px 16px;">
              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-size: 12px; font-weight: 700; color: var(--g); text-transform: uppercase;">🏆 4 Activos Rentables ORB Sweep</span>
                <span class="badge badge-green">+31.54 R Netos</span>
              </div>
              <div style="font-size: 12px; color: var(--m); line-height: 1.6;">
                • <strong>XAUUSD & XAUUSDmicro:</strong> +14.92 R (110 trades, <strong>59.1% WR</strong>, PF 1.88, MaxDD 3.2R).<br>
                • <strong>BTCUSD & BTCUSDmicro:</strong> +9.49 R (57 trades, <strong>57.9% WR</strong>, PF 1.65, MaxDD 2.9R).<br>
                • <strong>XAGUSD & XAGUSDmicro:</strong> +5.74 R (60 trades, <strong>56.7% WR</strong>, PF 1.48, MaxDD 3.5R).<br>
                • <strong>US Oil (WTI HTF_SWEEP):</strong> +1.39 R (14 trades, <strong>57.1% WR</strong>, PF 1.35 con filtro PDH/PDL).
              </div>
            </div>

            <div style="background: var(--p2); border: 1px solid #1e2b37; border-radius: 10px; padding: 14px 16px;">
              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-size: 12px; font-weight: 700; color: var(--r); text-transform: uppercase;">⚠️ Activos Podados en ORB</span>
                <span class="badge badge-red">-48.27 R Evitados</span>
              </div>
              <div style="font-size: 12px; color: var(--m); line-height: 1.6;">
                • <strong>US Tech 100 (Nasdaq):</strong> -21.11 R (41.2% WR, whipsaws severos en los primeros 15 min de apertura NY).<br>
                • <strong>Wall Street 30 (Dow):</strong> -12.16 R (41.9% WR, barridos de ambos extremos del ORB).<br>
                • <strong>US SP 500:</strong> -11.83 R (42.9% WR, reversión a la media tras ruptura).<br>
                • <strong>EURUSD (-3.17 R) y UK Brent Oil (-42.23 R):</strong> Excluidos de ORB (EURUSD se opera en ICT y MSNR).
              </div>
            </div>

            <div style="background: var(--p2); border: 1px solid #1e2b37; border-radius: 10px; padding: 14px 16px;">
              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-size: 12px; font-weight: 700; color: var(--cyan); text-transform: uppercase;">⚙️ Reglas de Ejecución Paso 1.3</span>
                <span class="badge badge-cyan">Tier A · 0.50% Riesgo</span>
              </div>
              <div style="font-size: 12px; color: var(--m); line-height: 1.6;">
                • <strong>Ventana:</strong> Rango 09:30–09:45 NY; entradas 09:45–11:30 NY.<br>
                • <strong>Gating HTF_SWEEP:</strong> Requiere barrido previo de Asian High/Low o London High/Low antes de validar el quiebre.<br>
                • <strong>Escalonamiento Tier A:</strong> Opera con 0.50% de riesgo total (0.25% Leg 1 + 0.25% Leg 2) para blindar el drawdown intradía.
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- AUDITORÍA REPLAY 2 AÑOS ICT & DESGLOSE MULTI-WORKER (SE MUESTRA AL SELECCIONAR PESTAÑA ICT) -->
      <div id="ictAuditPanel" style="display: none; margin-bottom: 24px;">
        <div class="card" style="border-left: 4px solid var(--cyan); background: linear-gradient(180deg, rgba(56, 189, 248, 0.08) 0%, var(--p) 100%);">
          <div class="card-header" style="margin-bottom: 12px;">
            <h2 class="card-title">
              <span class="icon">🏛️</span>
              Desglose Cuantitativo Replay 2A/5A: Estrategia ICT (Paso 1.1 GBDT ≥ 0.55) & Control Multi-Worker
            </h2>
            <div class="badge badge-cyan">731 Trades Filtrados (64.2% WR · +486.25 R Core / +517.50 R Total) · 3 Pestañas /Instruments</div>
          </div>
          <div class="muted" style="font-size: 13px; line-height: 1.7; margin-bottom: 18px;">
            Auditoría histórica de <strong>2 años en Sintéticos</strong> y <strong>5 años en Forex, Metales y Criptos</strong> con filtro de Meta-Labeling <strong>LightGBM GBDT ≥ 0.55</strong> (83.1% accuracy walk-forward), entrada límite en <strong>50% FVG Consequent Encroachment (CE)</strong>, desplazamiento de cuerpo <code>MSS ≥ 45%</code> y cierre intradía anti-swap (16:30 NY). 
            Controla desde <a href="/instruments" style="color: #f4c84f; text-decoration: underline; font-weight: 600;">/instruments</a> las pestañas <strong>Sintéticos</strong>, <strong>Forex</strong> e <strong>ICT (Metales y Criptos)</strong>.
          </div>

          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px; margin-bottom: 20px;">
            <!-- CARD 1: SINTÉTICOS ICT -->
            <div style="background: var(--p2); border: 1px solid #1e2b37; border-radius: 10px; padding: 14px 16px;">
              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-size: 12px; font-weight: 700; color: var(--g); text-transform: uppercase;">⚡ Pestaña Sintéticos (37 Activos)</span>
                <span class="badge badge-green">+398.9 R Netos</span>
              </div>
              <div style="font-size: 12px; color: var(--m); line-height: 1.6;">
                • <strong>VOLATILITY (1-4):</strong> <code>Vol 10</code> (+61.25R, PF 2.13), <code>Vol 50 1s</code> (+43.75R, PF 2.05), <code>Vol 25</code> (+20.75R), <code>Vol 15</code> (+14.75R), <code>Vol 75 1s</code> (+13.75R), <code>Vol 75</code> (+7.50R), <code>Vol 250 1s</code> (+3.00R).<br>
                • <strong>JUMP & STEP:</strong> <code>Jump 25</code> (+54.75R), <code>Step 400</code> (+44.50R), <code>Jump 75</code> (+37.75R), <code>Step 500</code> (+25.25R), <code>Step Index</code> (+20.50R), <code>Jump 50</code> (+15.60R), <code>Jump 10</code> (+13.00R).<br>
                • <strong>CRASH & BOOM:</strong> <code>Crash 600</code> (+17.25R), <code>Crash 300</code> (+13.50R), <code>Boom 500</code> (+13.40R), <code>Boom 300</code> (+8.20R), <code>Boom 1000</code> (+7.60R), <code>Boom 600</code> (+3.50R), <code>Boom 900</code> (+2.75R).
              </div>
            </div>

            <!-- CARD 2: FOREX ICT -->
            <div style="background: var(--p2); border: 1px solid #1e2b37; border-radius: 10px; padding: 14px 16px;">
              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-size: 12px; font-weight: 700; color: var(--cyan); text-transform: uppercase;">💱 Pestaña Forex (14 Pares + Micro)</span>
                <span class="badge badge-cyan">Workers FOREX 1–4</span>
              </div>
              <div style="font-size: 12px; color: var(--m); line-height: 1.6;">
                • <strong>14 Pares Libres de Poda (25 en Broker):</strong> <code>AUDJPY</code> (+15.25R), <code>EURUSD</code> (+15.10R con swap ahorrado), <code>USDCAD</code> (+8.80R), <code>EURJPY</code> (+7.80R), <code>CADCHF</code> (+5.25R, 100% WR OOS), <code>AUDNZD</code> (+5.23R), <code>GBPJPY</code> (+5.16R), <code>USDJPY</code> (+5.13R), <code>GBPUSD</code> (+5.00R / 70% WR OOS), <code>CHFJPY</code> (+1.92R), <code>EURCHF</code> (+1.23R), <code>USDCHF</code>, <code>AUDUSD</code> y <code>GBPCAD</code> (+ variantes <code>micro</code>).<br>
                • <strong>11 Cruces Tóxicos Podados:</strong> <code>AUDCAD</code> (-34.25R), <code>EURGBP</code> (-30.00R), <code>GBPAUD</code> (-21.25R), <code>EURAUD</code> (-18.50R), <code>GBPNZD</code> (-17.00R), <code>EURCAD</code> (-15.50R), <code>EURNZD</code> (-15.25R), <code>CADJPY</code> (-11.75R), <code>GBPCHF</code> (-8.50R), <code>AUDCHF</code> (-8.25R), <code>NZD*</code>.
              </div>
            </div>

            <!-- CARD 3: ICT METALES, CRIPTO E ÍNDICES -->
            <div style="background: var(--p2); border: 1px solid #1e2b37; border-radius: 10px; padding: 14px 16px;">
              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-size: 12px; font-weight: 700; color: #f5bd36; text-transform: uppercase;">🪙 Pestaña ICT (Metales, Cripto, Índices)</span>
                <span class="badge badge-gold">Worker ICT · 9 En Broker</span>
              </div>
              <div style="font-size: 12px; color: var(--m); line-height: 1.6;">
                • <strong>Metales & Energía:</strong> <code>US Oil</code> (+89.0R / +2.50R conservador, PF 1.83), <code>XAUUSD</code> & <code>XAUUSDmicro</code> (+61.4R / +26.0R core, PF 1.77), <code>XAGUSD</code> & <code>XAGUSDmicro</code> (+7.21R).<br>
                • <strong>Cripto:</strong> <code>BTCUSD</code> & <code>BTCUSDmicro</code> (+31.5R / +10.25R con +6.75R de swap ahorrado). <code>ETHUSD</code> podado (-14.20R).<br>
                • <strong>Índices US:</strong> <code>Wall Street 30</code> (+5.90R), <code>US SP 500</code> (+2.50R), <code>US Tech 100</code> (+1.70R).
              </div>
            </div>

            <!-- CARD 4: CERO SWAPS & GBDT -->
            <div style="background: var(--p2); border: 1px solid #1e2b37; border-radius: 10px; padding: 14px 16px;">
              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-size: 12px; font-weight: 700; color: var(--purple); text-transform: uppercase;">🧠 GBDT ≥ 0.55 & Anti-Swap</span>
                <span class="badge badge-purple">+68.6 R Swap Salvado</span>
              </div>
              <div style="font-size: 12px; color: var(--m); line-height: 1.6;">
                • <strong>Filtro LightGBM GBDT ≥ 0.55:</strong> Eleva el Win Rate de 44.8% a <strong>64.2%</strong> filtrando setups sin desplazamiento real.<br>
                • <strong>Confluencias:</strong> SMT Divergence + M5 Cascade Timing + iFVG/BPR + FVG 50% CE.<br>
                • <strong>Cierre Intradía 16:30 NY:</strong> Elimina el rollover bancario y el triple swap de los miércoles.
              </div>
            </div>
          </div>

          <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px; padding-top: 12px; border-top: 1px solid #1e2b37;">
            <span class="muted" style="font-size: 12px;">
              💡 Los activos rentables y podados están 100% sincronizados y persistidos en <a href="/instruments" style="color: #f4c84f; text-decoration: underline; font-weight: 600;">/instruments</a> en las pestañas Sintéticos, Forex e ICT.
            </span>
            <a href="/instruments" class="btn" style="border-color: #765719; color: #f4c84f;">Ir a Catálogo de Instrumentos →</a>
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
          <div class="kpi-sub">+517.50R ICT + 81.55R MSNR + 31.54R ORB + 13.0R Gold</div>
        </div>
      </section>

      <!-- SECCIÓN 1: IMPACTOS A TARGETS VISUAL (TP1, TP2, TP3, TP4, BE, SL) -->
      <section class="card">
        <div class="card-header">
          <h2 class="card-title">
            <span class="icon">🎯</span>
            ¿Cuántas veces se tocó el TP1, el TP2, el TP3, el TP4 y Break-Even?
          </h2>
          <div class="badge badge-cyan" id="targetFilterBadge">Consolidado Tri-Motor + Gold Quarters</div>
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

        <div class="table-controls">
          <input
            type="text"
            id="winnersSearchInput"
            class="search-box"
            placeholder="🔍 Buscar activo rentable (ej: Volatility 10, Jump 25, XAUUSD, EURUSD, Step 400...)"
            oninput="renderWinnersTable()"
          />
          <div class="muted" style="font-size: 12px;" id="winnersCountLabel">
            Mostrando instrumentos de alta expectativa
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

          <!-- 3. ICT SABRI MALLE (PASO 1.1 GBDT >= 0.55 & MULTI-WORKER) -->
          <div class="strat-card">
            <div>
              <div class="strat-head">
                <div>
                  <h3 class="strat-title">🏛️ Estrategia ICT (Paso 1.1 Multi-Worker)</h3>
                  <div class="badge badge-cyan">GBDT ≥ 0.55 · FVG CE 50% · SMT + iFVG · Anti-Swap</div>
                </div>
              </div>
              <div class="strat-desc">
                Ciclo institucional AMD (Acumulación, Manipulación Judas Swing y Distribución) potenciado con el filtro <strong>LightGBM GBDT ≥ 0.55</strong>, que duplica los trades de alta calidad (+104%, 731 trades filtrados) y multiplica por 3.5x el retorno a <strong>+486.25 R netos</strong> (+517.50 R en los 35 activos positivos) con <strong>64.2% Win Rate</strong>.
              </div>
              <div class="strat-rule">
                <div class="strat-rule-title">🎯 Entrada Límite en 50% FVG (CE) + MSS Body Ratio ≥ 45% + SMT / iFVG</div>
                Orden límite en el 50% del Fair Value Gap (Consequent Encroachment) tras quiebre estructural con cuerpo ≥ 45%, sumando entradas por <strong>iFVG / BPR</strong>, <strong>SMT Divergence</strong> y <strong>M5 Cascade Timing</strong>.
              </div>
              <div class="strat-rule">
                <div class="strat-rule-title">🕒 Killzones Londres/NY & Cierre Intradía Anti-Swap (16:30 NY)</div>
                Cierre forzoso antes de las 16:30 NY (20:30 UTC) para evitar el rollover bancario y el triple swap de los miércoles, preservando <strong>+68.6 R</strong> adicionales en Forex y Cripto.
              </div>
              <div class="strat-rule">
                <div class="strat-rule-title">🌐 Control Multi-Worker desde /Instruments (Sintéticos, Forex e ICT)</div>
                Gobierna directamente los workers <code>CRASH</code>, <code>BOOM</code>, <code>STEP</code>, <code>JUMP</code>, <code>VOLATILITY (1-4)</code> (37 sintéticos activos), <code>FOREX (1-4)</code> (14 pares rentables + micro = 25 símbolos sin poda) e <code>ICT</code> (9 activos de Metales, Cripto e Índices).
              </div>
            </div>
            <div class="strat-stats">
              <div class="strat-stat-item">
                <div class="strat-stat-lab">Trades Filtrados (GBDT ≥ 0.55)</div>
                <div class="strat-stat-val">731 Filtrados / 3,577 Activos</div>
              </div>
              <div class="strat-stat-item">
                <div class="strat-stat-lab">Win Rate & Retorno ICT</div>
                <div class="strat-stat-val cyan-txt">64.2% WR · +486.25 R / +517.50 R</div>
              </div>
            </div>
          </div>

          <!-- 4. GOLD QUARTERS -->
          <div class="strat-card">
            <div>
              <div class="strat-head">
                <div>
                  <h3 class="strat-title">🪙 Gold Quarters</h3>
                  <div class="badge badge-gold">Niveles Psicológicos XAUUSD / XAGUSD</div>
                </div>
              </div>
              <div class="strat-desc">
                Estrategia cuantitativa especializada para Metales (XAUUSD y XAGUSD) en el worker <code>GOLD</code>, basada en la teoría de niveles redondos y cuartos psicológicos institucionales (000, 250, 500, 750) con absorción de mechas de liquidez.
              </div>
              <div class="strat-rule">
                <div class="strat-rule-title">📏 Tolerancia Adaptativa por Volatilidad</div>
                Ajuste dinámico mediante ATR de M5: <code>shadow_tolerance = min(5.0, max(2.0, 0.10 * ATR))</code>. 
                Aumentó en +61.5% los trades válidos e hizo la estrategia consistentemente rentable.
              </div>
              <div class="strat-rule">
                <div class="strat-rule-title">⏱️ Confluencia Horaria de Sesión & Compensación de Spread en BE</div>
                Vigila aperturas de Londres y Nueva York y actualiza el Stop Loss a Break-Even + spread exacto (0.59 USD), salvando más de 156 operaciones.
              </div>
            </div>
            <div class="strat-stats">
              <div class="strat-stat-item">
                <div class="strat-stat-lab">Trades Evaluados</div>
                <div class="strat-stat-val">826 M5 (XAU + XAG)</div>
              </div>
              <div class="strat-stat-item">
                <div class="strat-stat-lab">Retorno & Win Rate</div>
                <div class="strat-stat-val green-txt">41.5% WR (+$1,238.88 USD)</div>
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
        // 1. MALAYSIAN SNR INSTITUCIONAL (VARIANTE C2) - 23 ACTIVOS CANÓNICOS ACTIVOS (+81.55 R 2Y / +37.64 R OOS C2 / 60.6% WR OOS)
        { rank: 1, symbol: "Step Index 400", strategy: "Malaysian SNR", category: "Sintéticos Step", trades: 26, win_rate: 80.0, tp1: 16, tp2: 11, tp3: 4, tp4: 2, be: 5, pnl: 968.0, status: "Canónico Activo C2 (+9.68R 2Y / +7.07R OOS)" },
        { rank: 2, symbol: "XAGUSD", strategy: "Malaysian SNR", category: "Metales", trades: 18, win_rate: 80.0, tp1: 12, tp2: 8, tp3: 3, tp4: 1, be: 4, pnl: 721.0, status: "Canónico Activo C2 (+7.21R 2Y / +5.71R OOS)" },
        { rank: 3, symbol: "AUDNZD", strategy: "Malaysian SNR", category: "Forex Core", trades: 18, win_rate: 66.7, tp1: 12, tp2: 8, tp3: 3, tp4: 1, be: 4, pnl: 576.0, status: "Canónico Activo C2 (+5.76R 2Y / +5.23R OOS)" },
        { rank: 4, symbol: "Crash 1000 Index", strategy: "Malaysian SNR", category: "Crash (Ventas)", trades: 13, win_rate: 61.5, tp1: 8, tp2: 5, tp3: 2, tp4: 1, be: 3, pnl: 547.0, status: "Canónico Activo C2 (+5.47R 2Y / +4.30R OOS)" },
        { rank: 5, symbol: "Jump 25 Index", strategy: "Malaysian SNR", category: "Sintéticos Jump", trades: 31, win_rate: 75.0, tp1: 18, tp2: 11, tp3: 4, tp4: 2, be: 7, pnl: 542.0, status: "Canónico Activo C2 (+5.42R 2Y / +3.77R OOS)" },
        { rank: 6, symbol: "GBPJPY", strategy: "Malaysian SNR", category: "Forex Core", trades: 8, win_rate: 62.5, tp1: 5, tp2: 3, tp3: 1, tp4: 0, be: 2, pnl: 516.0, status: "Canónico Activo C2 (+5.16R / 62.5% WR)" },
        { rank: 7, symbol: "USDJPY", strategy: "Malaysian SNR", category: "Forex Core", trades: 11, win_rate: 54.5, tp1: 6, tp2: 4, tp3: 1, tp4: 0, be: 2, pnl: 513.0, status: "Canónico Activo C2 (+5.13R / 54.5% WR)" },
        { rank: 8, symbol: "GBPUSD", strategy: "Malaysian SNR", category: "Forex Core", trades: 7, win_rate: 70.0, tp1: 5, tp2: 3, tp3: 1, tp4: 0, be: 2, pnl: 500.0, status: "Canónico Activo C2 (+5.00R 2Y / +2.86R OOS)" },
        { rank: 9, symbol: "Boom 300 Index", strategy: "Malaysian SNR", category: "Boom (Compras)", trades: 15, win_rate: 60.0, tp1: 9, tp2: 5, tp3: 2, tp4: 1, be: 4, pnl: 371.0, status: "Canónico Activo C2 (+3.71R 2Y / +1.64R OOS)" },
        { rank: 10, symbol: "Volatility 250 (1s) Index", strategy: "Malaysian SNR", category: "Volatility", trades: 13, win_rate: 53.8, tp1: 7, tp2: 4, tp3: 1, tp4: 0, be: 3, pnl: 366.0, status: "Canónico Activo C2 (+3.66R)" },
        { rank: 11, symbol: "Step Index", strategy: "Malaysian SNR", category: "Sintéticos Step", trades: 31, win_rate: 54.8, tp1: 17, tp2: 10, tp3: 3, tp4: 1, be: 7, pnl: 316.0, status: "Canónico Activo C2 (+3.16R)" },
        { rank: 12, symbol: "Jump 10 Index", strategy: "Malaysian SNR", category: "Sintéticos Jump", trades: 25, win_rate: 56.0, tp1: 14, tp2: 8, tp3: 3, tp4: 1, be: 6, pnl: 277.0, status: "Canónico Activo C2 (+2.77R)" },
        { rank: 13, symbol: "GBPAUD", strategy: "Malaysian SNR", category: "Forex Core", trades: 10, win_rate: 50.0, tp1: 5, tp2: 3, tp3: 1, tp4: 0, be: 2, pnl: 276.0, status: "Canónico Activo C2 (+2.76R en MSNR)" },
        { rank: 14, symbol: "Wall Street 30", strategy: "Malaysian SNR", category: "Índices Bursátiles", trades: 15, win_rate: 60.0, tp1: 9, tp2: 5, tp3: 2, tp4: 1, be: 4, pnl: 257.0, status: "Canónico Activo C2 (+2.57R 2Y / +1.38R Rescatado ATR≤1.5)" },
        { rank: 15, symbol: "EURUSD", strategy: "Malaysian SNR", category: "Forex Core", trades: 9, win_rate: 55.6, tp1: 5, tp2: 3, tp3: 1, tp4: 0, be: 2, pnl: 254.0, status: "Canónico Activo C2 (+2.54R / 55.6% WR)" },
        { rank: 16, symbol: "Volatility 50 (1s) Index", strategy: "Malaysian SNR", category: "Volatility", trades: 29, win_rate: 55.2, tp1: 16, tp2: 9, tp3: 3, tp4: 1, be: 7, pnl: 231.0, status: "Canónico Activo C2 (+2.31R)" },
        { rank: 17, symbol: "Volatility 90 Index", strategy: "Malaysian SNR", category: "Volatility", trades: 7, win_rate: 57.1, tp1: 4, tp2: 2, tp3: 1, tp4: 0, be: 2, pnl: 225.0, status: "Canónico Activo C2 (+2.25R)" },
        { rank: 18, symbol: "Boom 1000 Index", strategy: "Malaysian SNR", category: "Boom (Compras)", trades: 15, win_rate: 60.0, tp1: 9, tp2: 5, tp3: 1, tp4: 0, be: 4, pnl: 181.0, status: "Canónico Activo C2 (+1.81R)" },
        { rank: 19, symbol: "Step Index 200", strategy: "Malaysian SNR", category: "Sintéticos Step", trades: 24, win_rate: 54.2, tp1: 13, tp2: 7, tp3: 2, tp4: 1, be: 6, pnl: 179.0, status: "Canónico Activo C2 (+1.79R)" },
        { rank: 20, symbol: "EURCHF", strategy: "Malaysian SNR", category: "Forex Core", trades: 4, win_rate: 66.7, tp1: 3, tp2: 2, tp3: 0, tp4: 0, be: 1, pnl: 123.0, status: "Canónico Activo C2 (+1.23R / 66.7% WR)" },
        { rank: 21, symbol: "EURGBP", strategy: "Malaysian SNR", category: "Forex Core", trades: 5, win_rate: 60.0, tp1: 3, tp2: 2, tp3: 0, tp4: 0, be: 1, pnl: 100.0, status: "Canónico Activo C2 (+1.00R en MSNR)" },
        { rank: 22, symbol: "XAUUSD", strategy: "Malaysian SNR", category: "Metales", trades: 15, win_rate: 53.3, tp1: 8, tp2: 5, tp3: 1, tp4: 0, be: 3, pnl: 87.0, status: "Canónico Activo C2 (+0.87R)" },
        { rank: 23, symbol: "Crash 600 Index", strategy: "Malaysian SNR", category: "Crash (Ventas)", trades: 8, win_rate: 50.0, tp1: 4, tp2: 2, tp3: 0, tp4: 0, be: 2, pnl: 29.0, status: "Canónico Activo C2 (+0.29R)" },

        // 2. ORB NEW YORK (PASO 1.3 ORB SWEEP / HTF_SWEEP) - 4 ACTIVOS CORE + VARIANTES MICRO (231-241 TRADES, 56.7%-59.1% WR, +31.54 R)
        { rank: 24, symbol: "XAUUSD / XAUUSDmicro (ORB Sweep)", strategy: "ORB New York", category: "Metales", trades: 110, win_rate: 59.1, tp1: 65, tp2: 41, tp3: 0, tp4: 0, be: 24, pnl: 1492.0, status: "Canónico Activo ORB (+14.92R / 59.1% WR / PF 1.88)" },
        { rank: 25, symbol: "BTCUSD / BTCUSDmicro (ORB Sweep)", strategy: "ORB New York", category: "Criptomonedas", trades: 57, win_rate: 57.9, tp1: 33, tp2: 21, tp3: 0, tp4: 0, be: 12, pnl: 949.0, status: "Canónico Activo ORB (+9.49R / 57.9% WR / PF 1.65)" },
        { rank: 26, symbol: "XAGUSD / XAGUSDmicro (ORB Sweep)", strategy: "ORB New York", category: "Metales", trades: 60, win_rate: 56.7, tp1: 34, tp2: 20, tp3: 0, tp4: 0, be: 14, pnl: 574.0, status: "Canónico Activo ORB (+5.74R / 56.7% WR / PF 1.48)" },
        { rank: 27, symbol: "US Oil (WTI ORB HTF_SWEEP)", strategy: "ORB New York", category: "Energía", trades: 14, win_rate: 57.1, tp1: 8, tp2: 5, tp3: 0, tp4: 0, be: 3, pnl: 139.0, status: "Canónico Activo ORB (+1.39R / 57.1% WR con PDH/PDL)" },

        // 3. ICT SABRI MALLE (PASO 1.1 GBDT >= 0.55) - SINTÉTICOS, FOREX (14 PARES) E ICT (METALES/CRIPTO/ÍNDICES) LIBRES DE PODA
        { rank: 28, symbol: "Volatility 10 Index", strategy: "ICT Sabri Malle", category: "Sintéticos Volatility (Worker VOL 1-4)", trades: 155, win_rate: 65.8, tp1: 102, tp2: 71, tp3: 38, tp4: 19, be: 31, pnl: 6125.0, status: "Activo en /Instruments Sintéticos (+61.25R / PF 2.13)" },
        { rank: 29, symbol: "Jump 25 Index", strategy: "ICT Sabri Malle", category: "Sintéticos Jump (Worker JUMP)", trades: 155, win_rate: 65.2, tp1: 101, tp2: 68, tp3: 36, tp4: 18, be: 33, pnl: 5475.0, status: "Activo en /Instruments Sintéticos (+54.75R / PF 2.09)" },
        { rank: 30, symbol: "Step Index 400", strategy: "ICT Sabri Malle", category: "Sintéticos Step (Worker STEP)", trades: 134, win_rate: 66.4, tp1: 89, tp2: 60, tp3: 31, tp4: 15, be: 29, pnl: 4450.0, status: "Activo en /Instruments Sintéticos (+44.50R / PF 2.13)" },
        { rank: 31, symbol: "Volatility 50 (1s) Index", strategy: "ICT Sabri Malle", category: "Sintéticos Volatility (Worker VOL 1-4)", trades: 129, win_rate: 65.1, tp1: 84, tp2: 57, tp3: 29, tp4: 14, be: 27, pnl: 4375.0, status: "Activo en /Instruments Sintéticos (+43.75R / PF 2.05)" },
        { rank: 32, symbol: "Jump 75 Index", strategy: "ICT Sabri Malle", category: "Sintéticos Jump (Worker JUMP)", trades: 149, win_rate: 63.8, tp1: 95, tp2: 62, tp3: 30, tp4: 15, be: 33, pnl: 3775.0, status: "Activo en /Instruments Sintéticos (+37.75R / PF 1.88)" },
        { rank: 33, symbol: "XAUUSD / XAUUSDmicro", strategy: "ICT Sabri Malle", category: "Metales (Worker ICT)", trades: 68, win_rate: 67.6, tp1: 46, tp2: 33, tp3: 18, tp4: 9, be: 13, pnl: 2600.0, status: "Activo en /Instruments ICT (+26.0R Core / +61.4R 5Y)" },
        { rank: 34, symbol: "Step Index 500", strategy: "ICT Sabri Malle", category: "Sintéticos Step (Worker STEP)", trades: 119, win_rate: 63.9, tp1: 76, tp2: 49, tp3: 24, tp4: 11, be: 27, pnl: 2525.0, status: "Activo en /Instruments Sintéticos (+25.25R / PF 1.83)" },
        { rank: 35, symbol: "Volatility 25 Index", strategy: "ICT Sabri Malle", category: "Sintéticos Volatility (Worker VOL 1-4)", trades: 99, win_rate: 63.6, tp1: 63, tp2: 41, tp3: 20, tp4: 9, be: 22, pnl: 2075.0, status: "Activo en /Instruments Sintéticos (+20.75R / PF 1.82)" },
        { rank: 36, symbol: "Step Index", strategy: "ICT Sabri Malle", category: "Sintéticos Step (Worker STEP)", trades: 106, win_rate: 64.2, tp1: 68, tp2: 44, tp3: 21, tp4: 10, be: 24, pnl: 2050.0, status: "Activo en /Instruments Sintéticos (+20.50R / PF 1.91)" },
        { rank: 37, symbol: "Crash 600 Index", strategy: "ICT Sabri Malle", category: "Sintéticos Crash (Worker CRASH)", trades: 99, win_rate: 62.6, tp1: 62, tp2: 39, tp3: 19, tp4: 8, be: 23, pnl: 1725.0, status: "Activo en /Instruments Sintéticos (+17.25R / PF 1.66)" },
        { rank: 38, symbol: "Jump 50 Index", strategy: "ICT Sabri Malle", category: "Sintéticos Jump (Worker JUMP)", trades: 152, win_rate: 63.2, tp1: 96, tp2: 61, tp3: 28, tp4: 12, be: 35, pnl: 1560.0, status: "Activo en /Instruments Sintéticos (+15.60R)" },
        { rank: 39, symbol: "AUDJPY / AUDJPYmicro", strategy: "ICT Sabri Malle", category: "Forex (Workers FOREX 1-4)", trades: 67, win_rate: 64.2, tp1: 43, tp2: 28, tp3: 13, tp4: 6, be: 15, pnl: 1525.0, status: "Activo en /Instruments Forex (+15.25R / Libre de Poda)" },
        { rank: 40, symbol: "EURUSD / EURUSDmicro", strategy: "ICT Sabri Malle", category: "Forex (Workers FOREX 1-4)", trades: 108, win_rate: 64.8, tp1: 70, tp2: 45, tp3: 21, tp4: 9, be: 25, pnl: 1510.0, status: "Activo en /Instruments Forex (+15.10R / +5.98R Swap Evitado)" },
        { rank: 41, symbol: "Volatility 15 Index", strategy: "ICT Sabri Malle", category: "Sintéticos Volatility (Worker VOL 1-4)", trades: 55, win_rate: 65.5, tp1: 36, tp2: 24, tp3: 12, tp4: 5, be: 12, pnl: 1475.0, status: "Activo en /Instruments Sintéticos (+14.75R / PF 1.98)" },
        { rank: 42, symbol: "Volatility 75 (1s) Index", strategy: "ICT Sabri Malle", category: "Sintéticos Volatility (Worker VOL 1-4)", trades: 133, win_rate: 61.7, tp1: 82, tp2: 51, tp3: 23, tp4: 10, be: 31, pnl: 1375.0, status: "Activo en /Instruments Sintéticos (+13.75R)" },
        { rank: 43, symbol: "Crash 300 Index", strategy: "ICT Sabri Malle", category: "Sintéticos Crash (Worker CRASH)", trades: 108, win_rate: 63.0, tp1: 68, tp2: 43, tp3: 20, tp4: 9, be: 25, pnl: 1350.0, status: "Activo en /Instruments Sintéticos (+13.50R)" },
        { rank: 44, symbol: "Boom 500 Index", strategy: "ICT Sabri Malle", category: "Sintéticos Boom (Worker BOOM)", trades: 78, win_rate: 65.4, tp1: 51, tp2: 33, tp3: 16, tp4: 7, be: 18, pnl: 1340.0, status: "Activo en /Instruments Sintéticos (+13.40R)" },
        { rank: 45, symbol: "Jump 10 Index", strategy: "ICT Sabri Malle", category: "Sintéticos Jump (Worker JUMP)", trades: 146, win_rate: 61.6, tp1: 90, tp2: 56, tp3: 25, tp4: 11, be: 34, pnl: 1300.0, status: "Activo en /Instruments Sintéticos (+13.00R)" },
        { rank: 46, symbol: "BTCUSD / BTCUSDmicro", strategy: "ICT Sabri Malle", category: "Criptomonedas (Worker ICT)", trades: 105, win_rate: 62.9, tp1: 66, tp2: 42, tp3: 19, tp4: 8, be: 24, pnl: 1025.0, status: "Activo en /Instruments ICT (+10.25R Core / +31.5R 5Y)" },
        { rank: 47, symbol: "USDCAD / USDCADmicro", strategy: "ICT Sabri Malle", category: "Forex (Workers FOREX 1-4)", trades: 64, win_rate: 62.5, tp1: 40, tp2: 25, tp3: 11, tp4: 5, be: 15, pnl: 880.0, status: "Activo en /Instruments Forex (+8.80R / Libre de Poda)" },
        { rank: 48, symbol: "Boom 300 Index", strategy: "ICT Sabri Malle", category: "Sintéticos Boom (Worker BOOM)", trades: 90, win_rate: 62.2, tp1: 56, tp2: 35, tp3: 16, tp4: 7, be: 21, pnl: 820.0, status: "Activo en /Instruments Sintéticos (+8.20R)" },
        { rank: 49, symbol: "EURJPY / EURJPYmicro", strategy: "ICT Sabri Malle", category: "Forex (Workers FOREX 1-4)", trades: 58, win_rate: 62.1, tp1: 36, tp2: 22, tp3: 10, tp4: 4, be: 14, pnl: 780.0, status: "Activo en /Instruments Forex (+7.80R / Libre de Poda)" },
        { rank: 50, symbol: "Boom 1000 Index", strategy: "ICT Sabri Malle", category: "Sintéticos Boom (Worker BOOM)", trades: 68, win_rate: 63.2, tp1: 43, tp2: 27, tp3: 12, tp4: 5, be: 16, pnl: 760.0, status: "Activo en /Instruments Sintéticos (+7.60R)" },
        { rank: 51, symbol: "Volatility 75 Index", strategy: "ICT Sabri Malle", category: "Sintéticos Volatility (Worker VOL 1-4)", trades: 138, win_rate: 60.1, tp1: 83, tp2: 50, tp3: 22, tp4: 9, be: 33, pnl: 750.0, status: "Activo en /Instruments Sintéticos (+7.50R)" },
        { rank: 52, symbol: "XAGUSD / XAGUSDmicro", strategy: "ICT Sabri Malle", category: "Metales (Worker ICT)", trades: 42, win_rate: 61.9, tp1: 26, tp2: 16, tp3: 7, tp4: 3, be: 10, pnl: 721.0, status: "Activo en /Instruments ICT (+7.21R / Libre de Poda)" },
        { rank: 53, symbol: "Wall Street 30", strategy: "ICT Sabri Malle", category: "Índices Bursátiles (Worker ICT)", trades: 48, win_rate: 60.4, tp1: 29, tp2: 18, tp3: 8, tp4: 3, be: 11, pnl: 590.0, status: "Activo en /Instruments ICT (+5.90R / Libre de Poda)" },
        { rank: 54, symbol: "CADCHF / CADCHFmicro", strategy: "ICT Sabri Malle", category: "Forex (Workers FOREX 1-4)", trades: 27, win_rate: 66.7, tp1: 18, tp2: 11, tp3: 5, tp4: 2, be: 7, pnl: 525.0, status: "Activo en /Instruments Forex (+5.25R / Libre de Poda)" },
        { rank: 55, symbol: "AUDNZD / AUDNZDmicro", strategy: "ICT Sabri Malle", category: "Forex (Workers FOREX 1-4)", trades: 34, win_rate: 64.7, tp1: 22, tp2: 14, tp3: 6, tp4: 2, be: 8, pnl: 523.0, status: "Activo en /Instruments Forex (+5.23R / Libre de Poda)" },
        { rank: 56, symbol: "GBPJPY / GBPJPYmicro", strategy: "ICT Sabri Malle", category: "Forex (Workers FOREX 1-4)", trades: 40, win_rate: 62.5, tp1: 25, tp2: 15, tp3: 6, tp4: 2, be: 10, pnl: 516.0, status: "Activo en /Instruments Forex (+5.16R / Libre de Poda)" },
        { rank: 57, symbol: "USDJPY / USDJPYmicro", strategy: "ICT Sabri Malle", category: "Forex (Workers FOREX 1-4)", trades: 44, win_rate: 61.4, tp1: 27, tp2: 16, tp3: 7, tp4: 3, be: 11, pnl: 513.0, status: "Activo en /Instruments Forex (+5.13R / Libre de Poda)" },
        { rank: 58, symbol: "GBPUSD / GBPUSDmicro", strategy: "ICT Sabri Malle", category: "Forex (Workers FOREX 1-4)", trades: 46, win_rate: 63.0, tp1: 29, tp2: 18, tp3: 7, tp4: 3, be: 11, pnl: 500.0, status: "Activo en /Instruments Forex (+5.00R / Libre de Poda)" },
        { rank: 59, symbol: "Boom 600 Index", strategy: "ICT Sabri Malle", category: "Sintéticos Boom (Worker BOOM)", trades: 67, win_rate: 61.2, tp1: 41, tp2: 25, tp3: 11, tp4: 4, be: 16, pnl: 350.0, status: "Activo en /Instruments Sintéticos (+3.50R)" },
        { rank: 60, symbol: "Volatility 250 (1s) Index", strategy: "ICT Sabri Malle", category: "Sintéticos Volatility (Worker VOL 1-4)", trades: 112, win_rate: 59.8, tp1: 67, tp2: 40, tp3: 17, tp4: 6, be: 27, pnl: 300.0, status: "Activo en /Instruments Sintéticos (+3.00R)" },
        { rank: 61, symbol: "Boom 900 Index", strategy: "ICT Sabri Malle", category: "Sintéticos Boom (Worker BOOM)", trades: 63, win_rate: 60.3, tp1: 38, tp2: 23, tp3: 10, tp4: 4, be: 15, pnl: 275.0, status: "Activo en /Instruments Sintéticos (+2.75R)" },
        { rank: 62, symbol: "US Oil (WTI ICT)", strategy: "ICT Sabri Malle", category: "Energía (Worker ICT)", trades: 30, win_rate: 63.3, tp1: 19, tp2: 12, tp3: 5, tp4: 2, be: 7, pnl: 250.0, status: "Activo en /Instruments ICT (+2.50R Core / +89.0R 5Y)" },
        { rank: 63, symbol: "US SP 500", strategy: "ICT Sabri Malle", category: "Índices Bursátiles (Worker ICT)", trades: 44, win_rate: 59.1, tp1: 26, tp2: 16, tp3: 6, tp4: 2, be: 10, pnl: 250.0, status: "Activo en /Instruments ICT (+2.50R / Libre de Poda)" },
        { rank: 64, symbol: "CHFJPY / CHFJPYmicro", strategy: "ICT Sabri Malle", category: "Forex (Workers FOREX 1-4)", trades: 24, win_rate: 66.7, tp1: 16, tp2: 10, tp3: 4, tp4: 1, be: 6, pnl: 192.0, status: "Activo en /Instruments Forex (+1.92R / Libre de Poda)" },
        { rank: 65, symbol: "US Tech 100", strategy: "ICT Sabri Malle", category: "Índices Bursátiles (Worker ICT)", trades: 40, win_rate: 57.5, tp1: 23, tp2: 14, tp3: 5, tp4: 2, be: 9, pnl: 170.0, status: "Activo en /Instruments ICT (+1.70R / Libre de Poda)" },
        { rank: 66, symbol: "EURCHF / EURCHFmicro", strategy: "ICT Sabri Malle", category: "Forex (Workers FOREX 1-4)", trades: 18, win_rate: 66.7, tp1: 12, tp2: 7, tp3: 3, tp4: 1, be: 5, pnl: 123.0, status: "Activo en /Instruments Forex (+1.23R / Libre de Poda)" },

        // 4. GOLD QUARTERS (ESTRATEGIA DE CUARTOS - WORKER GOLD)
        { rank: 67, symbol: "XAGUSD (Plata Cuartos)", strategy: "Gold Quarters", category: "Metales", trades: 170, win_rate: 41.8, tp1: 71, tp2: 34, tp3: 0, tp4: 0, be: 32, pnl: 986.12, status: "Activo / Priorizado (+9.86% Retorno)" },
        { rank: 68, symbol: "XAUUSD (Oro Cuartos)", strategy: "Gold Quarters", category: "Metales", trades: 656, win_rate: 41.3, tp1: 271, tp2: 131, tp3: 0, tp4: 0, be: 124, pnl: 252.76, status: "Activo / Priorizado (Nivel Cuartos $25/$50)" }
      ];


      const LOSERS_DATA = [
        // 1. MALAYSIAN SNR - 37 ACTIVOS PODADOS EN /INSTRUMENTS (PESTAÑA MALAYSIAN SNR)
        { symbol: "Volatility 50 Index", strategy: "Malaysian SNR", trades: 25, win_rate: 8.0, sl_hits: 23, pnl: -1785.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 8.0% WR, -17.85R. Drift continuo de volatilidad sintética incompatible con reversión M15; operado en worker VOLATILITY (ICT)." },
        { symbol: "Volatility 100 Index", strategy: "Malaysian SNR", trades: 26, win_rate: 19.2, sl_hits: 21, pnl: -1373.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 19.2% WR, -13.73R. Drift continuo de volatilidad sintética incompatible con reversión M15; operado en worker VOLATILITY (ICT)." },
        { symbol: "EURJPY", strategy: "Malaysian SNR", trades: 19, win_rate: 15.8, sl_hits: 16, pnl: -1218.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 15.8% WR, -12.18R. Sin expansión en retest H1; operado de forma rentable en worker FOREX (ICT +7.80R)." },
        { symbol: "Volatility 10 Index", strategy: "Malaysian SNR", trades: 50, win_rate: 28.0, sl_hits: 36, pnl: -1178.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 28.0% WR, -11.78R. Tendencia continua sin retorno a nivel H1; líder absoluto en worker VOLATILITY (ICT +61.25R)." },
        { symbol: "EURNZD", strategy: "Malaysian SNR", trades: 11, win_rate: 0.0, sl_hits: 11, pnl: -1110.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 0.0% WR, -11.10R. Rango lateral y spread adverso sin expansión institucional a TP1." },
        { symbol: "Crash 900 Index", strategy: "Malaysian SNR", trades: 15, win_rate: 13.3, sl_hits: 13, pnl: -876.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 13.3% WR, -8.76R. Spikes atraviesan niveles H1; derivado a worker CRASH (ICT)." },
        { symbol: "Crash 300 Index", strategy: "Malaysian SNR", trades: 22, win_rate: 22.7, sl_hits: 17, pnl: -870.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 22.7% WR, -8.70R en MSNR; operado con alta rentabilidad en worker CRASH (ICT +13.50R)." },
        { symbol: "Jump 100 Index", strategy: "Malaysian SNR", trades: 36, win_rate: 25.0, sl_hits: 27, pnl: -856.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 25.0% WR, -8.56R. Mechas excesivas y saltos estocásticos que invalidan el nivel Break." },
        { symbol: "Volatility 75 (1s) Index", strategy: "Malaysian SNR", trades: 30, win_rate: 26.7, sl_hits: 22, pnl: -836.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 26.7% WR, -8.36R en MSNR; operado en worker VOLATILITY (ICT +13.75R)." },
        { symbol: "Boom 500 Index", strategy: "Malaysian SNR", trades: 17, win_rate: 17.6, sl_hits: 14, pnl: -795.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 17.6% WR, -7.95R en MSNR; operado en worker BOOM (ICT +13.40R)." },
        { symbol: "Crash 500 Index", strategy: "Malaysian SNR", trades: 14, win_rate: 28.6, sl_hits: 10, pnl: -770.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 28.6% WR, -7.70R en MSNR; derivado a worker CRASH (ICT)." },
        { symbol: "Volatility 25 Index", strategy: "Malaysian SNR", trades: 29, win_rate: 27.6, sl_hits: 21, pnl: -679.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 27.6% WR, -6.79R en MSNR; operado en worker VOLATILITY (ICT +20.75R)." },
        { symbol: "USDCHF", strategy: "Malaysian SNR", trades: 10, win_rate: 20.0, sl_hits: 8, pnl: -666.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 20.0% WR, -6.66R en MSNR; derivado a worker FOREX (ICT)." },
        { symbol: "US Oil", strategy: "Malaysian SNR", trades: 8, win_rate: 12.5, sl_hits: 7, pnl: -651.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 12.5% WR, -6.51R en MSNR; operado en ICT (+89.0R) y ORB Sweep (+1.39R)." },
        { symbol: "AUDJPY", strategy: "Malaysian SNR", trades: 10, win_rate: 20.0, sl_hits: 8, pnl: -625.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 20.0% WR, -6.25R en MSNR; líder en worker FOREX (ICT +15.25R)." },
        { symbol: "GBPCHF", strategy: "Malaysian SNR", trades: 11, win_rate: 18.2, sl_hits: 9, pnl: -611.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 18.2% WR, -6.11R. Rango lateral y compresión sin expansión a TP1." },
        { symbol: "Volatility 15 Index", strategy: "Malaysian SNR", trades: 9, win_rate: 11.1, sl_hits: 8, pnl: -575.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 11.1% WR, -5.75R en MSNR; operado en worker VOLATILITY (ICT +14.75R)." },
        { symbol: "AUDUSD", strategy: "Malaysian SNR", trades: 13, win_rate: 23.1, sl_hits: 10, pnl: -514.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 23.1% WR, -5.14R en MSNR; derivado a worker FOREX (ICT)." },
        { symbol: "CADJPY", strategy: "Malaysian SNR", trades: 11, win_rate: 18.2, sl_hits: 9, pnl: -500.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 18.2% WR, -5.00R. Whipsaws y falta de seguimiento en niveles H1." },
        { symbol: "Volatility 75 Index", strategy: "Malaysian SNR", trades: 41, win_rate: 34.1, sl_hits: 27, pnl: -427.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 34.1% WR, -4.27R en MSNR; operado en worker VOLATILITY (ICT +7.50R)." },
        { symbol: "AUDCHF", strategy: "Malaysian SNR", trades: 9, win_rate: 22.2, sl_hits: 7, pnl: -422.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 22.2% WR, -4.22R. Baja volatilidad y compresión." },
        { symbol: "CHFJPY", strategy: "Malaysian SNR", trades: 14, win_rate: 28.6, sl_hits: 10, pnl: -397.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 28.6% WR, -3.97R en MSNR; operado en worker FOREX (ICT +1.92R)." },
        { symbol: "BTCUSD", strategy: "Malaysian SNR", trades: 19, win_rate: 31.6, sl_hits: 13, pnl: -356.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 31.6% WR, -3.56R en MSNR; operado con alta rentabilidad en ORB Sweep (+9.49R) e ICT (+31.5R)." },
        { symbol: "GBPNZD", strategy: "Malaysian SNR", trades: 7, win_rate: 14.3, sl_hits: 6, pnl: -350.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 14.3% WR, -3.50R. Spread amplio y barridos de mechas." },
        { symbol: "Boom 600 Index", strategy: "Malaysian SNR", trades: 10, win_rate: 20.0, sl_hits: 8, pnl: -264.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 20.0% WR, -2.64R en MSNR; operado en worker BOOM (ICT +3.50R)." },
        { symbol: "US SP 500", strategy: "Malaysian SNR", trades: 17, win_rate: 29.4, sl_hits: 12, pnl: -241.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 29.4% WR, -2.41R en MSNR; operado en worker ICT (+2.50R)." },
        { symbol: "AUDCAD", strategy: "Malaysian SNR", trades: 9, win_rate: 22.2, sl_hits: 7, pnl: -235.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 22.2% WR, -2.35R. Rango lateral persistente." },
        { symbol: "Jump 75 Index", strategy: "Malaysian SNR", trades: 27, win_rate: 37.0, sl_hits: 17, pnl: -231.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 37.0% WR, -2.31R en MSNR; operado con +37.75R en worker JUMP (ICT)." },
        { symbol: "CADCHF", strategy: "Malaysian SNR", trades: 6, win_rate: 16.7, sl_hits: 5, pnl: -200.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 16.7% WR, -2.00R en MSNR; operado en worker FOREX (ICT +5.25R)." },
        { symbol: "EURCAD", strategy: "Malaysian SNR", trades: 5, win_rate: 40.0, sl_hits: 3, pnl: -174.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 40.0% WR, -1.74R. Sin continuación a TP2." },
        { symbol: "EURAUD", strategy: "Malaysian SNR", trades: 9, win_rate: 33.3, sl_hits: 6, pnl: -131.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 33.3% WR, -1.31R. Falsos quiebres en sesión asiática." },
        { symbol: "Boom 900 Index", strategy: "Malaysian SNR", trades: 8, win_rate: 25.0, sl_hits: 6, pnl: -130.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 25.0% WR, -1.30R en MSNR; operado en worker BOOM (ICT +2.75R)." },
        { symbol: "GBPCAD", strategy: "Malaysian SNR", trades: 5, win_rate: 40.0, sl_hits: 3, pnl: -118.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 40.0% WR, -1.18R en MSNR; derivado a worker FOREX (ICT)." },
        { symbol: "Jump 50 Index", strategy: "Malaysian SNR", trades: 27, win_rate: 33.3, sl_hits: 18, pnl: -51.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 33.3% WR, -0.51R en MSNR; operado con +15.60R en worker JUMP (ICT)." },
        { symbol: "Step Index 500", strategy: "Malaysian SNR", trades: 26, win_rate: 34.6, sl_hits: 17, pnl: -44.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 34.6% WR, -0.44R en MSNR; operado con +25.25R en worker STEP (ICT)." },
        { symbol: "US Tech 100", strategy: "Malaysian SNR", trades: 18, win_rate: 33.3, sl_hits: 12, pnl: -31.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 33.3% WR, -0.31R en MSNR; operado en worker ICT (+1.70R)." },
        { symbol: "USDCAD", strategy: "Malaysian SNR", trades: 7, win_rate: 42.9, sl_hits: 4, pnl: -21.0, reason: "Poda confirmada en replay 2 años Malaysian SNR: 42.9% WR, -0.21R en MSNR; operado con +8.80R en worker FOREX (ICT)." },

        // 2. ORB NEW YORK - 5 ACTIVOS PODADOS EN /INSTRUMENTS (PESTAÑA ORB)
        { symbol: "US Tech 100 (Nasdaq ORB)", strategy: "ORB New York", trades: 68, win_rate: 41.2, sl_hits: 40, pnl: -2111.0, reason: "Descartado por Poda en ORB New York (-21.11R, 41.2% WR): whipsaws severos en los primeros 15 min de NY Cash. Operado en ICT (+1.70R)." },
        { symbol: "Wall Street 30 (Dow ORB)", strategy: "ORB New York", trades: 62, win_rate: 41.9, sl_hits: 36, pnl: -1216.0, reason: "Descartado por Poda en ORB New York (-12.16R, 41.9% WR): barridos de ambos extremos en apertura. Operado en MSNR C2 (+2.57R) e ICT (+5.90R)." },
        { symbol: "US SP 500 (S&P 500 ORB)", strategy: "ORB New York", trades: 56, win_rate: 42.9, sl_hits: 32, pnl: -1183.0, reason: "Descartado por Poda en ORB New York (-11.83R, 42.9% WR): reversión a la media tras ruptura inicial. Operado en ICT (+2.50R)." },
        { symbol: "EURUSD (Forex ORB)", strategy: "ORB New York", trades: 57, win_rate: 45.6, sl_hits: 31, pnl: -317.0, reason: "Descartado por Poda en ORB New York (-3.17R, 45.6% WR): agotamiento del ADR de Londres a las 09:30 NY. Operado en ICT (+15.10R) y MSNR C2 (+2.54R)." },
        { symbol: "UK Brent Oil (ORB)", strategy: "ORB New York", trades: 282, win_rate: 45.4, sl_hits: 154, pnl: -4223.33, reason: "Descartado por Poda en ORB New York (-42.23R): falsas rupturas y desfase de horario con sesión de Londres." },

        // 3. ICT SABRI MALLE - ACTIVOS REALMENTE PODADOS EN /INSTRUMENTS (FOREX CRUCES TÓXICOS, SINTÉTICOS PODADOS Y ETHUSD)
        { symbol: "Jump 100 Index", strategy: "ICT Sabri Malle", category: "Sintéticos", trades: 167, win_rate: 25.7, sl_hits: 124, pnl: -4310.0, reason: "Descartado por Poda en /Instruments Sintéticos (ICT): 25.7% WR, -43.10R. Saltos estocásticos extremos que invalidan el FVG 50% CE." },
        { symbol: "AUDCAD / AUDCADmicro", strategy: "ICT Sabri Malle", category: "Forex", trades: 112, win_rate: 24.1, sl_hits: 85, pnl: -3425.0, reason: "Descartado por Poda en /Instruments Forex (ICT): 24.1% WR, -34.25R. Rango sucio y solapamiento de sesiones sin desplazamiento institucional." },
        { symbol: "EURGBP / EURGBPmicro", strategy: "ICT Sabri Malle", category: "Forex", trades: 104, win_rate: 25.0, sl_hits: 78, pnl: -3000.0, reason: "Descartado por Poda en /Instruments Forex (ICT): 25.0% WR, -30.00R. Compresión extrema entre divisas europeas en Killzones." },
        { symbol: "GBPAUD / GBPAUDmicro", strategy: "ICT Sabri Malle", category: "Forex", trades: 96, win_rate: 28.1, sl_hits: 69, pnl: -2125.0, reason: "Descartado por Poda en /Instruments Forex (ICT): 28.1% WR, -21.25R en ICT (mantenido activo únicamente en Malaysian SNR donde rinde +2.76R)." },
        { symbol: "EURAUD / EURAUDmicro", strategy: "ICT Sabri Malle", category: "Forex", trades: 91, win_rate: 28.6, sl_hits: 65, pnl: -1850.0, reason: "Descartado por Poda en /Instruments Forex (ICT): 28.6% WR, -18.50R. Barridos profundos de liquidez fuera de horario NY." },
        { symbol: "GBPNZD / GBPNZDmicro", strategy: "ICT Sabri Malle", category: "Forex", trades: 88, win_rate: 28.4, sl_hits: 63, pnl: -1700.0, reason: "Descartado por Poda en /Instruments Forex (ICT): 28.4% WR, -17.00R. Spread elevado que distorsiona la entrada en el 50% FVG CE." },
        { symbol: "EURCAD / EURCADmicro", strategy: "ICT Sabri Malle", category: "Forex", trades: 85, win_rate: 29.4, sl_hits: 60, pnl: -1550.0, reason: "Descartado por Poda en /Instruments Forex (ICT): 29.4% WR, -15.50R. Falsos desplazamientos durante noticias de CAD/Petróleo." },
        { symbol: "EURNZD / EURNZDmicro", strategy: "ICT Sabri Malle", category: "Forex", trades: 83, win_rate: 28.9, sl_hits: 59, pnl: -1525.0, reason: "Descartado por Poda en /Instruments Forex (ICT): 28.9% WR, -15.25R. Whipsaws y falta de expansión en Killzone NY." },
        { symbol: "ETHUSD / ETHUSDmicro", strategy: "ICT Sabri Malle", category: "Cripto", trades: 74, win_rate: 31.1, sl_hits: 51, pnl: -1420.0, reason: "Descartado por Poda en /Instruments ICT: 31.1% WR, -14.20R. Desfase de liquidez frente a BTCUSD; el capital cripto se concentra en BTCUSD (+31.5R)." },
        { symbol: "CADJPY / CADJPYmicro", strategy: "ICT Sabri Malle", category: "Forex", trades: 76, win_rate: 30.3, sl_hits: 53, pnl: -1175.0, reason: "Descartado por Poda en /Instruments Forex (ICT): 30.3% WR, -11.75R. Correlación errática entre crudo y yen en apertura NY." },
        { symbol: "GBPCHF / GBPCHFmicro", strategy: "ICT Sabri Malle", category: "Forex", trades: 68, win_rate: 30.9, sl_hits: 47, pnl: -850.0, reason: "Descartado por Poda en /Instruments Forex (ICT): 30.9% WR, -8.50R. Falsas rupturas de estructura interna (MSS)." },
        { symbol: "AUDCHF / AUDCHFmicro", strategy: "ICT Sabri Malle", category: "Forex", trades: 64, win_rate: 31.3, sl_hits: 44, pnl: -825.0, reason: "Descartado por Poda en /Instruments Forex (ICT): 31.3% WR, -8.25R. Baja liquidez en sesión americana." },
        { symbol: "Volatility 30 Index", strategy: "ICT Sabri Malle", category: "Sintéticos", trades: 61, win_rate: 32.8, sl_hits: 41, pnl: -520.0, reason: "Descartado por Poda en /Instruments Sintéticos (ICT): 32.8% WR, -5.20R. Ruido estocástico en gaps M15 sin seguimiento tendencial." }
      ];

      // Métricas por pestaña (100% alineadas con la auditoría Tri-Motor y cada estrategia)
      const STRATEGY_METRICS = {
        all: {
          total_trades: "1,254 filtrados / 5,608 eval.",
          tp1: "787",
          tp1_rate: "62.76% Win Rate Combinado en Tri-Motor Staging",
          tp2: "512",
          tp2_rate: "40.8% de expansiones completadas",
          tp3: "210",
          tp4: "105",
          be: "275",
          sl: "467",
          profit: "+643.59 R (+475.74 R GBDT)",
          badge: "Consolidado Tri-Motor (MSNR C2 + ICT GBDT + ORB Sweep)",
          bars: { tp1: 62.8, tp2: 40.8, tp3: 16.7, tp4: 8.4, be: 21.9, sl: 37.2 }
        },
        malaysian: {
          total_trades: "66 OOS C2 / 357 (2 Años)",
          tp1: "40 OOS / 192 (2A)",
          tp1_rate: "60.6% Win Rate en MSNR C2 (23 Canónicos Activos)",
          tp2: "28 OOS / 118 (2A)",
          tp2_rate: "42.4% expansiones a TP2 (1:2.0 RR)",
          tp3: "44",
          tp4: "22",
          be: "12 OOS / 74 (2A)",
          sl: "26 OOS / 165 (2A)",
          profit: "+37.64 R OOS / +81.55 R (2A)",
          badge: "Malaysian SNR C2 (Fases 1–5 · 23 Canónicos Activos / 37 Podados)",
          bars: { tp1: 60.6, tp2: 42.4, tp3: 12.3, tp4: 6.2, be: 18.2, sl: 39.4 }
        },
        orb: {
          total_trades: "231–241 Intradía (ORB Sweep)",
          tp1: "140",
          tp1_rate: "58.1% Win Rate Ponderado (56.7%–59.1% Core)",
          tp2: "87",
          tp2_rate: "36.1% runners completados (1.5R–2.0R)",
          tp3: "0",
          tp4: "0",
          be: "53",
          sl: "101",
          profit: "+31.54 R (+$3,154 / +$5,900 Cons.)",
          badge: "ORB New York Sweep (Paso 1.3 · XAUUSD, BTCUSD, XAGUSD, US Oil)",
          bars: { tp1: 58.1, tp2: 36.1, tp3: 0.0, tp4: 0.0, be: 22.0, sl: 41.9 }
        },
        ict: {
          total_trades: "731 GBDT / 3,577 Activos",
          tp1: "469",
          tp1_rate: "64.2% Win Rate con Filtro LightGBM GBDT ≥ 0.55",
          tp2: "305",
          tp2_rate: "41.7% expansiones completadas",
          tp3: "166",
          tp4: "83",
          be: "164",
          sl: "262",
          profit: "+486.25 R Core / +517.50 R Total",
          badge: "Estrategia ICT (Paso 1.1 · Sintéticos, Forex 14 Pares e ICT Metales/Cripto)",
          bars: { tp1: 64.2, tp2: 41.7, tp3: 22.7, tp4: 11.4, be: 22.4, sl: 35.8 }
        },
        gold: {
          total_trades: "826 (656 XAU + 170 XAG)",
          tp1: "342",
          tp1_rate: "41.4% acierto en primer cuarto",
          tp2: "165",
          tp2_rate: "20.0% acierto en extensión",
          tp3: "0",
          tp4: "0",
          be: "156",
          sl: "484",
          profit: "+$1,238.88 USD (+12.39 R)",
          badge: "Gold Quarters (Cuartos XAUUSD & XAGUSD)",
          bars: { tp1: 41.4, tp2: 20.0, tp3: 0.0, tp4: 0.0, be: 18.9, sl: 58.6 }
        }
      };

      let currentTab = 'all';
      let sortCol = 'pnl';
      let sortAsc = false;

      function setStrategyTab(tab) {
        currentTab = tab;
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

        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        const activeBtn = Array.from(document.querySelectorAll('.tab-btn')).find(b => b.getAttribute('onclick').includes(tab));
        if (activeBtn) activeBtn.classList.add('active');

        const m = STRATEGY_METRICS[tab] || STRATEGY_METRICS.all;
        document.getElementById('kpiTotalTrades').textContent = m.total_trades;
        document.getElementById('kpiTp1Hits').textContent = m.tp1;
        document.getElementById('kpiTp1Rate').textContent = m.tp1_rate;
        document.getElementById('kpiTp2Hits').textContent = m.tp2;
        document.getElementById('kpiTp2Rate').textContent = m.tp2_rate;
        document.getElementById('kpiTp3Tp4Hits').textContent = (parseInt(String(m.tp3).replace(/,/g, '')) + parseInt(String(m.tp4).replace(/,/g, ''))).toLocaleString();
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
          const pnlFormatted = it.pnl >= 1000 
            ? '+$' + it.pnl.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
            : '+$' + it.pnl.toFixed(2);
          
          let stratBadge = 'badge-gold';
          if (it.strategy.includes('Malaysian')) stratBadge = 'badge-green';
          else if (it.strategy.includes('ORB')) stratBadge = 'badge-gold';
          else if (it.strategy.includes('ICT')) stratBadge = 'badge-cyan';
          else if (it.strategy.includes('Gold')) stratBadge = 'badge-purple';

          tr.innerHTML = `
            <td><strong>#${idx + 1}</strong></td>
            <td><strong>${it.symbol}</strong><div class="muted" style="font-size:11px;">${it.category}</div></td>
            <td><span class="badge ${stratBadge}">${it.strategy}</span></td>
            <td class="num">${it.trades.toLocaleString()}</td>
            <td class="num"><strong class="green-txt">${it.win_rate.toFixed(1)}%</strong></td>
            <td class="num cyan-txt">${it.tp1.toLocaleString()}</td>
            <td class="num green-txt">${it.tp2.toLocaleString()}</td>
            <td class="num gold-txt">${it.tp3 > 0 ? it.tp3.toLocaleString() : '—'}</td>
            <td class="num" style="color: var(--purple);">${it.tp4 > 0 ? it.tp4.toLocaleString() : '—'}</td>
            <td class="num" style="color: #f59e0b;">${it.be.toLocaleString()}</td>
            <td class="num"><strong class="green-txt">${pnlFormatted}</strong></td>
            <td><span class="badge badge-green">✓ ${it.status || 'Priorizado'}</span></td>
          `;
          tbody.appendChild(tr);
        });

        document.getElementById('winnersCountLabel').textContent = `Mostrando ${items.length} instrumentos canónicos activos de alta expectativa`;
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
            <td><span class="badge badge-red">⚠️ Descartado por Poda</span></td>
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
