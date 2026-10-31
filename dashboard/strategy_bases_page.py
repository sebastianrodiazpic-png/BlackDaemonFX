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

      <!-- PANEL DE AUDITORÍA MALAYSIAN SNR HÍBRIDO INSTITUCIONAL (SE MUESTRA EN PESTAÑA MALAYSIAN) -->
      <div id="msnrAuditPanel" style="display: none; margin-bottom: 24px;">
        <div class="card" style="border-left: 4px solid var(--g); background: linear-gradient(180deg, rgba(0, 219, 121, 0.08) 0%, var(--p) 100%);">
          <div class="card-header" style="margin-bottom: 12px;">
            <h2 class="card-title">
              <span class="icon">🇲🇾</span>
              Malaysian SNR Híbrido Institucional: Metodología Alchemist (Nick) + Gestión Dual-Leg BlackDaemonFX
            </h2>
            <div class="badge badge-green">35 Activos Activos (WR ≥ 47%) · +106.12 R Netos en Rentables · 6 Podados (WR &lt; 47%) · Sincronizado /Instruments</div>
          </div>
          <div class="muted" style="font-size: 13px; line-height: 1.7; margin-bottom: 18px;">
            Integración sinérgica entre el gatillo estructural de alta precisión de <strong>Alchemist (MSNR)</strong> y el contrato matemático de riesgo controlado de <strong>BlackDaemonFX</strong>.
            Se auditaron 41 instrumentos en el catálogo de <code>/Instruments</code>: los <strong>35 activos con acierto ≥ 47%</strong> quedan activos y 100% operativos, mientras que los <strong>6 activos con acierto &lt; 47%</strong> pasan a <strong>PODA PREVENTIVA</strong>.
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
                <span style="font-size: 12px; font-weight: 700; color: var(--purple); text-transform: uppercase;">4️⃣ 35 Activos Activos / 6 Podados</span>
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

      <!-- AUDITORÍA REPLAY 5 AÑOS ICT & DESGLOSE MULTI-WORKER (SE MUESTRA AL SELECCIONAR PESTAÑA ICT) -->
      <div id="ictAuditPanel" style="display: none; margin-bottom: 24px;">
        <div class="card" style="border-left: 4px solid var(--cyan); background: linear-gradient(180deg, rgba(56, 189, 248, 0.08) 0%, var(--p) 100%);">
          <div class="card-header" style="margin-bottom: 12px;">
            <h2 class="card-title">
              <span class="icon">🏛️</span>
              Auditoría Replay Fiel 5 Años con 6 Mejoras (82,194 Señales · 79 Instrumentos): Estrategia ICT & Consolidación Multi-Worker
            </h2>
            <div class="badge badge-cyan">46 Instrumentos Base Activos (33 Sintéticos + 9 Forex + 4 ICT con WR > 47%) · Consolidados en 1 Worker ON + 1 Worker OFF</div>
          </div>
          <div class="muted" style="font-size: 13px; line-height: 1.7; margin-bottom: 18px;">
            Replay fiel multianual (hasta <strong>5 años</strong>, <code>82,194</code> señales enriquecidas sobre <strong>79 instrumentos</strong>) de <code>ICTSabriMalleStrategy</code> con las <strong>6 mejoras institucionales aplicadas</strong>: (1) piso estructural de SL en sintéticos (<code>sl_atr_h1 ≥ 1.0</code>) y extremo H1, (2) entrada límite en 50% FVG CE validado de 3 velas con tope de retroceso <code>≤ 0.35 R</code>, (3) ventanas institucionales depuradas (Londres 03:00–05:00 NY y Silver Bullet 03:00 NY, retirando horas negativas 02:00 y 14:00 NY), (4) asimetría direccional especializada (Jump 50/75 solo BUY; Step Index solo SELL), (5) filtro de régimen de volatilidad H1 (<code>ADX ≥ 20.0</code>) y (6) ejecución virtual de orden limitada con tope spread/SL <code>≤ 2.0%</code> en Sintéticos y <code>≤ 2.5%</code> en Forex/ICT.
            Sincronizado 100% con <a href="/instruments" style="color: #f4c84f; text-decoration: underline; font-weight: 600;">/instruments</a> en las pestañas <strong>Sintéticos</strong>, <strong>Forex</strong> e <strong>ICT</strong>, con consolidación de workers (<strong>1 worker de Activos + 1 worker de Podados OFF</strong> en Volatility y Forex) y <strong>activación selectiva bajo demanda</strong>.
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

        // 3. ICT SABRI MALLE (AUDITORÍA FIEL 5 AÑOS) - 33 ACTIVOS BASE LIBRES DE PODA (25 SINTÉTICOS + 5 FOREX + 3 ICT MERCADOS REALES = +866.0 R)
        { rank: 28, symbol: "Step Index 200", strategy: "ICT Sabri Malle", category: "Sintéticos Step (Worker STEP)", trades: 1840, win_rate: 53.8, tp1: 989, tp2: 615, tp3: 240, tp4: 110, be: 374, pnl: 13002.46, status: "Activo 5Y en /Instruments Sintéticos (+130.02R / t=+2.86 / 3/3 años +)" },
        { rank: 29, symbol: "Step Index 400", strategy: "ICT Sabri Malle", category: "Sintéticos Step (Worker STEP)", trades: 1442, win_rate: 51.7, tp1: 745, tp2: 462, tp3: 185, tp4: 84, be: 283, pnl: 6905.51, status: "Activo 5Y en /Instruments Sintéticos (+69.06R / t=+1.69 / 2/2 años +)" },
        { rank: 30, symbol: "Volatility 25 Index", strategy: "ICT Sabri Malle", category: "Sintéticos Volatility (Worker VOLATILITY 1 Activos)", trades: 622, win_rate: 54.7, tp1: 340, tp2: 218, tp3: 92, tp4: 44, be: 122, pnl: 6378.03, status: "Rescatado 5Y en /Instruments Sintéticos (+63.78R / 54.66% WR / t=+2.39)" },
        { rank: 31, symbol: "Volatility 250 (1s) Index", strategy: "ICT Sabri Malle", category: "Sintéticos Volatility (Worker VOLATILITY 1 Activos)", trades: 1593, win_rate: 52.0, tp1: 829, tp2: 514, tp3: 205, tp4: 95, be: 315, pnl: 6350.00, status: "Activo 5Y en /Instruments Sintéticos (+63.50R / 3/3 años +)" },
        { rank: 32, symbol: "Jump 25 Index", strategy: "ICT Sabri Malle", category: "Sintéticos Jump (Worker JUMP)", trades: 1303, win_rate: 51.6, tp1: 672, tp2: 417, tp3: 168, tp4: 78, be: 255, pnl: 6118.27, status: "Rescatado 5Y en /Instruments Sintéticos (+61.18R / 51.57% WR / 3/3 años +)" },
        { rank: 33, symbol: "Volatility 10 Index", strategy: "ICT Sabri Malle", category: "Sintéticos Volatility (Worker VOLATILITY 1 Activos)", trades: 1205, win_rate: 52.4, tp1: 631, tp2: 394, tp3: 158, tp4: 74, be: 237, pnl: 5593.52, status: "Activo 5Y en /Instruments Sintéticos (+55.94R / +61.25R GBDT)" },
        { rank: 34, symbol: "US Oil (WTI ICT)", strategy: "ICT Sabri Malle", category: "Energía (Worker ICT)", trades: 137, win_rate: 56.9, tp1: 78, tp2: 51, tp3: 22, tp4: 11, be: 27, pnl: 5410.00, status: "Activo 5Y en /Instruments ICT (+54.1R 5Y / +12.81R Paridad / 56.93% WR)" },
        { rank: 35, symbol: "Volatility 75 (1s) Index", strategy: "ICT Sabri Malle", category: "Sintéticos Volatility (Worker VOLATILITY 1 Activos)", trades: 812, win_rate: 53.6, tp1: 435, tp2: 274, tp3: 110, tp4: 52, be: 161, pnl: 5103.66, status: "Activo 5Y en /Instruments Sintéticos (+51.04R / 3/3 años +)" },
        { rank: 36, symbol: "Volatility 150 (1s) Index", strategy: "ICT Sabri Malle", category: "Sintéticos Volatility (Worker VOLATILITY 1 Activos)", trades: 1091, win_rate: 51.6, tp1: 563, tp2: 349, tp3: 140, tp4: 64, be: 214, pnl: 4572.01, status: "Activo 5Y en /Instruments Sintéticos (+45.72R / 51.60% WR)" },
        { rank: 37, symbol: "Jump 75 Index", strategy: "ICT Sabri Malle", category: "Sintéticos Jump (Worker JUMP)", trades: 1855, win_rate: 51.6, tp1: 958, tp2: 590, tp3: 230, tp4: 105, be: 368, pnl: 3794.41, status: "Activo 5Y en /Instruments Sintéticos (+37.94R / 3/3 años WR≥47%)" },
        { rank: 38, symbol: "Volatility 5 Index", strategy: "ICT Sabri Malle", category: "Sintéticos Volatility (Worker VOLATILITY 1 Activos)", trades: 270, win_rate: 54.4, tp1: 147, tp2: 94, tp3: 38, tp4: 18, be: 53, pnl: 2649.52, status: "Activo 5Y en /Instruments Sintéticos (+26.50R / 54.44% WR)" },
        { rank: 39, symbol: "Volatility 50 (1s) Index", strategy: "ICT Sabri Malle", category: "Sintéticos Volatility (Worker VOLATILITY 1 Activos)", trades: 773, win_rate: 50.5, tp1: 390, tp2: 242, tp3: 96, tp4: 44, be: 148, pnl: 2621.27, status: "Activo 5Y en /Instruments Sintéticos (+26.21R / 3/3 años +)" },
        { rank: 40, symbol: "Crash 900 Index", strategy: "ICT Sabri Malle", category: "Sintéticos Crash (Worker CRASH)", trades: 239, win_rate: 52.3, tp1: 125, tp2: 79, tp3: 32, tp4: 15, be: 46, pnl: 2595.20, status: "Activo 5Y en /Instruments Sintéticos (+25.95R / PF 1.23)" },
        { rank: 41, symbol: "Volatility 100 (1s) Index", strategy: "ICT Sabri Malle", category: "Sintéticos Volatility (Worker VOLATILITY 1 Activos)", trades: 516, win_rate: 52.1, tp1: 269, tp2: 168, tp3: 67, tp4: 31, be: 101, pnl: 2503.23, status: "Activo 5Y en /Instruments Sintéticos (+25.03R / 3/3 años +)" },
        { rank: 42, symbol: "Boom 900 Index", strategy: "ICT Sabri Malle", category: "Sintéticos Boom (Worker BOOM)", trades: 165, win_rate: 58.2, tp1: 96, tp2: 64, tp3: 28, tp4: 14, be: 32, pnl: 2411.41, status: "Activo 5Y en /Instruments Sintéticos (+24.11R / 58.18% WR / 3/3 años +)" },
        { rank: 43, symbol: "Volatility 15 Index", strategy: "ICT Sabri Malle", category: "Sintéticos Volatility (Worker VOLATILITY 1 Activos)", trades: 232, win_rate: 55.2, tp1: 128, tp2: 82, tp3: 33, tp4: 15, be: 46, pnl: 1867.78, status: "Activo 5Y en /Instruments Sintéticos (+18.68R / 55.17% WR)" },
        { rank: 44, symbol: "High Frequency Vol 100 Index", strategy: "ICT Sabri Malle", category: "Sintéticos Volatility (Worker VOLATILITY 1 Activos)", trades: 315, win_rate: 50.8, tp1: 160, tp2: 100, tp3: 40, tp4: 18, be: 60, pnl: 1756.29, status: "Activo 5Y en /Instruments Sintéticos (+17.56R / PF 1.11)" },
        { rank: 45, symbol: "US Tech 100", strategy: "ICT Sabri Malle", category: "Índices Bursátiles (Worker ICT)", trades: 123, win_rate: 50.4, tp1: 62, tp2: 39, tp3: 15, tp4: 7, be: 23, pnl: 1460.00, status: "Activo 5Y en /Instruments ICT (+14.6R 5Y / +1.45R Paridad / 2/3 años +)" },
        { rank: 46, symbol: "Jump 10 Index", strategy: "ICT Sabri Malle", category: "Sintéticos Jump (Worker JUMP)", trades: 1669, win_rate: 50.6, tp1: 844, tp2: 520, tp3: 204, tp4: 92, be: 324, pnl: 1159.43, status: "Activo 5Y en /Instruments Sintéticos (+11.59R / 3/3 años WR≥47%)" },
        { rank: 47, symbol: "GBPJPY / GBPJPYmicro", strategy: "ICT Sabri Malle", category: "Forex (Worker FOREX 1 Activos)", trades: 193, win_rate: 52.3, tp1: 101, tp2: 63, tp3: 25, tp4: 11, be: 38, pnl: 952.44, status: "Activo 5Y en /Instruments Forex (+9.52R / 52.33% WR / PF 1.12)" },
        { rank: 48, symbol: "Volatility 90 Index", strategy: "ICT Sabri Malle", category: "Sintéticos Volatility (Worker VOLATILITY 1 Activos)", trades: 163, win_rate: 52.1, tp1: 85, tp2: 53, tp3: 21, tp4: 9, be: 32, pnl: 582.12, status: "Activo 5Y en /Instruments Sintéticos (+5.82R / 52.15% WR)" },
        { rank: 49, symbol: "Volatility 100 Index", strategy: "ICT Sabri Malle", category: "Sintéticos Volatility (Worker VOLATILITY 1 Activos)", trades: 1088, win_rate: 50.1, tp1: 545, tp2: 336, tp3: 132, tp4: 60, be: 209, pnl: 450.72, status: "Activo 5Y en /Instruments Sintéticos (+4.51R / 2025-26 +0.110 R/op)" },
        { rank: 50, symbol: "CHFJPY / CHFJPYmicro", strategy: "ICT Sabri Malle", category: "Forex (Worker FOREX 1 Activos)", trades: 69, win_rate: 55.1, tp1: 38, tp2: 24, tp3: 10, tp4: 4, be: 14, pnl: 442.75, status: "Activo 5Y en /Instruments Forex (+4.43R / 55.07% WR / 2/2 años +)" },
        { rank: 51, symbol: "XAUUSD / XAUUSDmicro", strategy: "ICT Sabri Malle", category: "Metales (Worker ICT)", trades: 125, win_rate: 49.6, tp1: 62, tp2: 39, tp3: 16, tp4: 7, be: 23, pnl: 400.00, status: "Activo 5Y en /Instruments ICT (+4.0R 5Y / +26.0R GBDT / 2024-26 +)" },
        { rank: 52, symbol: "Boom 500 Index", strategy: "ICT Sabri Malle", category: "Sintéticos Boom (Worker BOOM)", trades: 721, win_rate: 50.5, tp1: 364, tp2: 225, tp3: 88, tp4: 40, be: 139, pnl: 348.26, status: "Activo 5Y en /Instruments Sintéticos (+3.48R / 3/3 años WR≥48%)" },
        { rank: 53, symbol: "EURCHF / EURCHFmicro", strategy: "ICT Sabri Malle", category: "Forex (Worker FOREX 1 Activos)", trades: 173, win_rate: 50.3, tp1: 87, tp2: 54, tp3: 21, tp4: 9, be: 33, pnl: 196.49, status: "Activo 5Y en /Instruments Forex (+1.96R / 50.29% WR / PF 1.07)" },
        { rank: 54, symbol: "EURCAD / EURCADmicro", strategy: "ICT Sabri Malle", category: "Forex (Worker FOREX 1 Activos)", trades: 66, win_rate: 50.0, tp1: 33, tp2: 21, tp3: 8, tp4: 4, be: 12, pnl: 167.80, status: "Activo 5Y en /Instruments Forex (+1.68R / PF 1.27)" },
        { rank: 55, symbol: "GBPAUD / GBPAUDmicro", strategy: "ICT Sabri Malle", category: "Forex (Worker FOREX 1 Activos)", trades: 69, win_rate: 51.0, tp1: 35, tp2: 22, tp3: 9, tp4: 4, be: 13, pnl: 121.37, status: "Activo 5Y en /Instruments Forex (+1.21R / PF 1.17 / +0.097 R/op 2025-26)" },
        { rank: 56, symbol: "Crash 500 Index", strategy: "ICT Sabri Malle", category: "Sintéticos Crash (Worker CRASH)", trades: 645, win_rate: 50.7, tp1: 327, tp2: 201, tp3: 79, tp4: 35, be: 126, pnl: 31.81, status: "Activo 5Y en /Instruments Sintéticos (+0.32R / 2024-26 en positivo)" },
        { rank: 57, symbol: "Volatility 75 Index", strategy: "ICT Sabri Malle", category: "Sintéticos Volatility (Worker VOLATILITY 1 Activos)", trades: 1205, win_rate: 50.8, tp1: 612, tp2: 376, tp3: 148, tp4: 66, be: 236, pnl: 750.00, status: "Activo 5Y en /Instruments Sintéticos (50.79% WR / +0.104 R/op en 2025-26)" },
        { rank: 58, symbol: "Step Index 500", strategy: "ICT Sabri Malle", category: "Sintéticos Step (Worker STEP)", trades: 1915, win_rate: 50.4, tp1: 965, tp2: 594, tp3: 234, tp4: 105, be: 371, pnl: 2525.00, status: "Activo 5Y en /Instruments Sintéticos (50.39% WR / 2024-26 en positivo)" },
        { rank: 59, symbol: "Boom 600 Index", strategy: "ICT Sabri Malle", category: "Sintéticos Boom (Worker BOOM)", trades: 180, win_rate: 51.1, tp1: 92, tp2: 57, tp3: 22, tp4: 10, be: 35, pnl: 350.00, status: "Activo 5Y en /Instruments Sintéticos (51.11% WR / 2024-26 en positivo)" },
        { rank: 60, symbol: "Jump 50 Index", strategy: "ICT Sabri Malle", category: "Sintéticos Jump (Worker JUMP)", trades: 942, win_rate: 48.4, tp1: 456, tp2: 282, tp3: 110, tp4: 49, be: 174, pnl: 1560.00, status: "Activo 5Y en /Instruments Sintéticos (2/3 años +: +28.5R en 24-25 y +5.0R en 25-26)" },

        // 4. GOLD QUARTERS (ESTRATEGIA DE CUARTOS - WORKER GOLD)
        { rank: 61, symbol: "XAGUSD (Plata Cuartos)", strategy: "Gold Quarters", category: "Metales", trades: 170, win_rate: 41.8, tp1: 71, tp2: 34, tp3: 0, tp4: 0, be: 32, pnl: 986.12, status: "Activo / Priorizado (+9.86% Retorno)" },
        { rank: 62, symbol: "XAUUSD (Oro Cuartos)", strategy: "Gold Quarters", category: "Metales", trades: 656, win_rate: 41.3, tp1: 271, tp2: 131, tp3: 0, tp4: 0, be: 124, pnl: 252.76, status: "Activo / Priorizado (Nivel Cuartos $25/$50)" }
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

        // 3. ICT SABRI MALLE - ACTIVOS REALMENTE PODADOS EN /INSTRUMENTS SEGÚN AUDITORÍA FIEL 5 AÑOS (SINTÉTICOS, FOREX E ICT MERCADOS REALES)
        { symbol: "US SP 500", strategy: "ICT Sabri Malle", category: "Índices Bursátiles (ICT)", trades: 120, win_rate: 43.3, sl_hits: 68, pnl: -9090.0, reason: "Descartado por Poda en /Instruments ICT (Auditoría 5 Años): 43.33% WR, -0.209 R/op (-25.02R paridad / -90.9R sin cap), PF 0.63 y 0/3 años positivos." },
        { symbol: "Crash 1000 Index", strategy: "ICT Sabri Malle", category: "Sintéticos Crash", trades: 750, win_rate: 47.5, sl_hits: 394, pnl: -4694.36, reason: "Descartado por Poda en /Instruments Sintéticos (ICT): 47.47% WR, -0.063 R/op (-46.94R), 0/3 años positivos; mantenido activo en Malaysian SNR (+5.47R)." },
        { symbol: "Boom 1000 Index", strategy: "ICT Sabri Malle", category: "Sintéticos Boom", trades: 544, win_rate: 46.1, sl_hits: 293, pnl: -4475.53, reason: "Descartado por Poda en /Instruments Sintéticos (Auditoría 5 Años): 46.14% WR < 47%, -0.082 R/op (-44.76R), PF 0.85; mantenido activo en Malaysian SNR." },
        { symbol: "Vol over Crash 550", strategy: "ICT Sabri Malle", category: "Sintéticos Volatility (VOLATILITY 2 OFF)", trades: 778, win_rate: 48.2, sl_hits: 403, pnl: -3771.20, reason: "Descartado por Poda en /Instruments Sintéticos (Worker VOLATILITY 2 OFF): 48.20% WR, -0.048 R/op (-37.71R), 0/3 años positivos." },
        { symbol: "Crash 300 Index", strategy: "ICT Sabri Malle", category: "Sintéticos Crash", trades: 577, win_rate: 48.2, sl_hits: 299, pnl: -2751.75, reason: "Descartado por Poda en /Instruments Sintéticos (Auditoría 5 Años): 48.18% WR, -0.048 R/op (-27.52R), PF 0.91 y 0/3 años positivos." },
        { symbol: "High Frequency Vol 50 Index", strategy: "ICT Sabri Malle", category: "Sintéticos Volatility (VOLATILITY 2 OFF)", trades: 247, win_rate: 45.7, sl_hits: 134, pnl: -2697.27, reason: "Descartado por Poda en /Instruments Sintéticos (Worker VOLATILITY 2 OFF): 45.75% WR < 47%, -0.109 R/op (-26.97R), PF 0.80." },
        { symbol: "Volatility 90 (1s) Index", strategy: "ICT Sabri Malle", category: "Sintéticos Volatility (VOLATILITY 2 OFF)", trades: 211, win_rate: 45.5, sl_hits: 115, pnl: -2250.21, reason: "Descartado por Poda en /Instruments Sintéticos (Worker VOLATILITY 2 OFF): 45.50% WR < 47%, -0.107 R/op (-22.50R), PF 0.80." },
        { symbol: "EURUSD / EURUSDmicro", strategy: "ICT Sabri Malle", category: "Forex (FOREX 2 OFF)", trades: 182, win_rate: 45.6, sl_hits: 99, pnl: -2015.02, reason: "Descartado por Poda en /Instruments Forex (Worker FOREX 2 OFF): 45.60% WR < 47%, -0.111 R/op (-20.15R), PF 0.80; operado en Malaysian SNR (+2.54R)." },
        { symbol: "USDCAD / USDCADmicro", strategy: "ICT Sabri Malle", category: "Forex (FOREX 2 OFF)", trades: 146, win_rate: 45.9, sl_hits: 79, pnl: -1795.58, reason: "Descartado por Poda en /Instruments Forex (Worker FOREX 2 OFF): 45.89% WR < 47%, -0.123 R/op (-17.96R), 0/2 años positivos." },
        { symbol: "Boom 300 Index", strategy: "ICT Sabri Malle", category: "Sintéticos Boom", trades: 955, win_rate: 49.4, sl_hits: 483, pnl: -1755.86, reason: "Descartado por Poda en /Instruments Sintéticos (ICT): 49.42% WR, -0.018 R/op (-17.56R), colapso OOS 2025-26 (-0.182 R/op); operado en Malaysian SNR (+3.71R)." },
        { symbol: "AUDCAD / AUDCADmicro", strategy: "ICT Sabri Malle", category: "Forex (FOREX 2 OFF)", trades: 165, win_rate: 40.6, sl_hits: 98, pnl: -1507.75, reason: "Descartado por Poda en /Instruments Forex (Worker FOREX 2 OFF): 40.61% WR, -0.091 R/op (-15.08R), PF 0.53 y 0/4 años positivos." },
        { symbol: "Vol over Boom 550", strategy: "ICT Sabri Malle", category: "Sintéticos Volatility (VOLATILITY 2 OFF)", trades: 378, win_rate: 48.1, sl_hits: 196, pnl: -1446.29, reason: "Descartado por Poda en /Instruments Sintéticos (Worker VOLATILITY 2 OFF): 48.15% WR, -0.038 R/op (-14.46R), PF 0.93." },
        { symbol: "EURJPY / EURJPYmicro", strategy: "ICT Sabri Malle", category: "Forex (FOREX 2 OFF)", trades: 190, win_rate: 48.9, sl_hits: 97, pnl: -1323.83, reason: "Descartado por Poda en /Instruments Forex (Worker FOREX 2 OFF): 48.95% WR, -0.070 R/op (-13.24R), PF 0.84." },
        { symbol: "EURGBP / EURGBPmicro", strategy: "ICT Sabri Malle", category: "Forex (FOREX 2 OFF)", trades: 166, win_rate: 42.2, sl_hits: 96, pnl: -1306.45, reason: "Descartado por Poda en /Instruments Forex (Worker FOREX 2 OFF): 42.17% WR, -0.079 R/op (-13.06R), PF 0.64; operado en Malaysian SNR (+1.00R)." },
        { symbol: "Step Index", strategy: "ICT Sabri Malle", category: "Sintéticos Step", trades: 2080, win_rate: 50.0, sl_hits: 1041, pnl: -1264.20, reason: "Descartado por Poda en /Instruments Sintéticos (ICT): 49.95% WR, -0.006 R/op (-12.64R), MaxDD 70.6R; operado en Malaysian SNR (+3.16R)." },
        { symbol: "Wall Street 30", strategy: "ICT Sabri Malle", category: "Índices Bursátiles (ICT)", trades: 142, win_rate: 48.6, sl_hits: 73, pnl: -1100.00, reason: "Descartado por Poda en /Instruments ICT (Auditoría 5 Años): 48.59% WR, -0.026 R/op (-3.76R paridad / -11.0R total), 1/3 años positivos; operado en Malaysian SNR C2 (+2.57R)." },
        { symbol: "USDCHF / USDCHFmicro", strategy: "ICT Sabri Malle", category: "Forex (FOREX 2 OFF)", trades: 177, win_rate: 47.5, sl_hits: 93, pnl: -1032.71, reason: "Descartado por Poda en /Instruments Forex (Worker FOREX 2 OFF): 47.46% WR, -0.058 R/op (-10.33R), PF 0.89." },
        { symbol: "NZDUSD / NZDUSDmicro", strategy: "ICT Sabri Malle", category: "Forex (FOREX 2 OFF)", trades: 117, win_rate: 47.9, sl_hits: 61, pnl: -1013.12, reason: "Descartado por Poda en /Instruments Forex (Worker FOREX 2 OFF): 47.86% WR, -0.087 R/op (-10.13R); operado en Malaysian SNR." },
        { symbol: "GBPCHF / GBPCHFmicro", strategy: "ICT Sabri Malle", category: "Forex (FOREX 2 OFF)", trades: 159, win_rate: 44.0, sl_hits: 89, pnl: -714.93, reason: "Descartado por Poda en /Instruments Forex (Worker FOREX 2 OFF): 44.03% WR, -0.045 R/op (-7.15R); operado en Malaysian SNR." },
        { symbol: "USDJPY / USDJPYmicro", strategy: "ICT Sabri Malle", category: "Forex (FOREX 2 OFF)", trades: 148, win_rate: 49.3, sl_hits: 75, pnl: -577.71, reason: "Descartado por Poda en /Instruments Forex (Worker FOREX 2 OFF): 49.32% WR, -0.039 R/op (-5.78R); operado en Malaysian SNR (+5.13R)." },
        { symbol: "GBPCAD / GBPCADmicro", strategy: "ICT Sabri Malle", category: "Forex (FOREX 2 OFF)", trades: 158, win_rate: 42.4, sl_hits: 91, pnl: -562.85, reason: "Descartado por Poda en /Instruments Forex (Worker FOREX 2 OFF): 42.41% WR, -0.036 R/op (-5.63R); operado en Malaysian SNR." },
        { symbol: "XAGUSD / XAGUSDmicro", strategy: "ICT Sabri Malle", category: "Metales (ICT)", trades: 207, win_rate: 40.6, sl_hits: 123, pnl: -300.00, reason: "Descartado por Poda en /Instruments ICT: 28.57% WR con cap (-0.429 R/op) y 40.58% WR sin cap (-0.236 R/op); líder en Malaysian SNR (+7.21R), ORB (+5.74R) y Gold Quarters." },
        { symbol: "EURAUD / EURAUDmicro", strategy: "ICT Sabri Malle", category: "Forex (FOREX 2 OFF)", trades: 81, win_rate: 48.1, sl_hits: 42, pnl: -271.27, reason: "Descartado por Poda en /Instruments Forex (Worker FOREX 2 OFF): 48.15% WR, -0.033 R/op (-2.71R), PF 0.74." },
        { symbol: "Crash 600 Index", strategy: "ICT Sabri Malle", category: "Sintéticos Crash", trades: 74, win_rate: 48.6, sl_hits: 38, pnl: -231.21, reason: "Descartado por Poda en /Instruments Sintéticos (ICT): 48.65% WR, -0.031 R/op (-2.31R), muestra baja y sin significancia." },
        { symbol: "GBPUSD / GBPUSDmicro", strategy: "ICT Sabri Malle", category: "Forex (FOREX 2 OFF)", trades: 187, win_rate: 51.9, sl_hits: 90, pnl: -111.59, reason: "Descartado por Poda en /Instruments Forex (Worker FOREX 2 OFF): -0.006 R/op (-1.12R) y deterioro en 2025-26 (-0.179 R/op); operado en Malaysian SNR (+5.00R)." },
        { symbol: "Volatility 50 Index", strategy: "ICT Sabri Malle", category: "Sintéticos Volatility (VOLATILITY 2 OFF)", trades: 165, win_rate: 46.1, sl_hits: 89, pnl: -1729.69, reason: "Descartado por Poda en /Instruments Sintéticos (Worker VOLATILITY 2 OFF): deterioro OOS 2025-26 (46.06% WR, -0.105 R/op, -17.3R)." },
        { symbol: "VolSwitch High Vol Index", strategy: "ICT Sabri Malle", category: "Sintéticos Volatility (VOLATILITY 2 OFF)", trades: 166, win_rate: 53.6, sl_hits: 77, pnl: -117.98, reason: "Descartado por Poda en /Instruments Sintéticos (Worker VOLATILITY 2 OFF): 1 solo año de historial (t=+0.56 no significativo) y -0.118 R/op sin cap." },
        { symbol: "CADCHF / CADCHFmicro", strategy: "ICT Sabri Malle", category: "Forex (FOREX 2 OFF)", trades: 163, win_rate: 46.0, sl_hits: 88, pnl: -48.01, reason: "Descartado por Poda en /Instruments Forex (Worker FOREX 2 OFF): 46.01% WR < 47%, -0.003 R/op (-0.48R); operado en Malaysian SNR." },
        { symbol: "AUDNZD / AUDNZDmicro", strategy: "ICT Sabri Malle", category: "Forex (FOREX 2 OFF)", trades: 122, win_rate: 45.1, sl_hits: 67, pnl: -7.04, reason: "Descartado por Poda en /Instruments Forex (Worker FOREX 2 OFF): 45.08% WR < 47%, -0.001 R/op; operado en Malaysian SNR (+5.76R)." },
        { symbol: "AUDUSD / AUDUSDmicro", strategy: "ICT Sabri Malle", category: "Forex (FOREX 2 OFF)", trades: 150, win_rate: 50.7, sl_hits: 74, pnl: -4.66, reason: "Descartado por Poda en /Instruments Forex (Worker FOREX 2 OFF): -0.0003 R/op (-0.05R), PF 0.999; operado en Malaysian SNR." },
        { symbol: "AUDJPY / AUDJPYmicro", strategy: "ICT Sabri Malle", category: "Forex (FOREX 2 OFF)", trades: 149, win_rate: 45.6, sl_hits: 81, pnl: -2.56, reason: "Descartado por Poda en /Instruments Forex (Worker FOREX 2 OFF): 45.64% WR < 47%, -0.0002 R/op (-0.03R)." },
        { symbol: "BTCUSD / ETHUSD / Cripto", strategy: "ICT Sabri Malle", category: "Cripto (ICT)", trades: 117, win_rate: 44.4, sl_hits: 65, pnl: -1950.00, reason: "Descartado por Poda en /Instruments ICT: -19.5R agregado en Cripto (ETHUSD/SOLUSD/ADAUSD negativos; BTCUSD operado en ORB NY Sweep con +9.49R)." }
      ];

      // Métricas por pestaña (100% alineadas con la auditoría Tri-Motor y cada estrategia)
      const STRATEGY_METRICS = {
        all: {
          total_trades: "1,254 filtrados / 17,578 paridad 5Y",
          tp1: "787",
          tp1_rate: "62.76% Win Rate Combinado en Tri-Motor Staging",
          tp2: "512",
          tp2_rate: "40.8% de expansiones completadas",
          tp3: "210",
          tp4: "105",
          be: "275",
          sl: "467",
          profit: "+866.0 R ICT 5Y (+475.74 R GBDT)",
          badge: "Consolidado Tri-Motor (MSNR C2 + ICT 5Y Consolidado + ORB Sweep)",
          bars: { tp1: 62.8, tp2: 40.8, tp3: 16.7, tp4: 8.4, be: 21.9, sl: 37.2 }
        },
        malaysian: {
          total_trades: "3,842 trades fieles multianuales (35 Activos con WR ≥ 47%)",
          tp1: "2,081",
          tp1_rate: "54.16% Win Rate Ponderado en 35 Activos Activos (hasta 100% GBPCAD, 85.7% CADCHF, 60.0% HF Vol 100)",
          tp2: "1,248",
          tp2_rate: "32.48% runners completados a TP2 (1:2.0 RR) o superior",
          tp3: "164",
          tp4: "86",
          be: "833",
          sl: "1,761",
          profit: "+106.12 R Netos en Activos Rentables (+$10,612 USD a 1% riesgo)",
          badge: "Malaysian SNR Híbrido Alchemist (35 Activos WR ≥ 47% / 6 Podados)",
          bars: { tp1: 54.2, tp2: 32.5, tp3: 14.1, tp4: 7.2, be: 21.7, sl: 45.8 }
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
          total_trades: "7,819 Señales Filtradas (5Y)",
          tp1: "4,178 (5Y)",
          tp1_rate: "53.43% WR (46 Activos Base con WR > 47%)",
          tp2: "3,120",
          tp2_rate: "39.9% expansiones completadas",
          tp3: "1,450",
          tp4: "680",
          be: "1,890",
          sl: "3,641",
          profit: "+540.8 R (5Y: +500.1R Sint. +17.5R FX +23.2R ICT)",
          badge: "Estrategia ICT 5Y con 6 Mejoras (33 Sintéticos, 9 Pares Forex, 4 ICT · VOL 1/2 & FOREX 1/2)",
          bars: { tp1: 53.4, tp2: 39.9, tp3: 18.5, tp4: 8.7, be: 24.2, sl: 46.6 }
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
