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
        <div class="card" style="border-left: 4px solid #10b981; background: linear-gradient(180deg, rgba(16, 185, 129, 0.08) 0%, var(--p) 100%);">
          <div class="card-header" style="margin-bottom: 12px;">
            <h2 class="card-title">
              <span class="icon">🗽</span>
              Auditoría Replay Multianual ORB New York SWEEP: +73.4 R Netos Acumulados
            </h2>
            <div class="badge badge-green">8 Activos con WR > 47% y R > 0 · Contrato 2 Patas 0.5% (TP1 @ 1R -> BE, Runner TP2/TP4) · 8 Podados OFF</div>
          </div>
          <div class="muted" style="font-size: 13px; line-height: 1.7; margin-bottom: 18px;">
            Metodología <strong>ORB SWEEP Institucional</strong> en la apertura Cash de Wall Street (09:30–11:30 NY) con filtro de absorción de liquidez (*Turtle Soup* del rango 15 min), confirmación de quiebre de estructura menor (*MSS*), alineación con <code>VWAP / POC</code> y contrato institucional de 2 patas (1% total: <code>TP1 @ 1.0R</code> con traslado automático de Stop a <code>Break Even + spread buffer</code>, y <code>TP2 @ 2.0R</code> con extensión progresiva hacia <code>3.0R–4.0R</code>).
            Sincronizado 100% con <a href="/instruments" style="color: #34d399; text-decoration: underline; font-weight: 600;">/instruments</a> en la pestaña <strong>ORB NEW YORK</strong>.
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
        // ICT SABRI MALLE - UNIVERSO COMPLETO AUDITADO (2 AÑOS: +196.9 R / +$19,690 USD)
        { rank: 31, symbol: "XAGUSD (Plata ICT)", strategy: "ICT Sabri Malle", category: "Metales", trades: 40, win_rate: 52.5, tp1: 21, tp2: 17, tp3: 17, tp4: 17, be: 4, pnl: 3805.73, status: "Activo / Priorizado (#1 ICT +38.1R)" },
        { rank: 32, symbol: "BTCUSD (ICT)", strategy: "ICT Sabri Malle", category: "Criptomonedas", trades: 50, win_rate: 48.0, tp1: 24, tp2: 14, tp3: 14, tp4: 14, be: 10, pnl: 2808.11, status: "Activo / Priorizado (#2 ICT +28.1R)" },
        { rank: 33, symbol: "Step Index (ICT)", strategy: "ICT Sabri Malle", category: "Sintéticos Step", trades: 24, win_rate: 54.2, tp1: 13, tp2: 10, tp3: 10, tp4: 10, be: 1, pnl: 2717.45, status: "Activo / Priorizado (#3 ICT +27.2R)" },
        { rank: 34, symbol: "Volatility 75 Index (ICT)", strategy: "ICT Sabri Malle", category: "Sintéticos Vol", trades: 22, win_rate: 54.5, tp1: 12, tp2: 9, tp3: 9, tp4: 9, be: 3, pnl: 2000.0, status: "Activo / Priorizado (+20.0R)" },
        { rank: 35, symbol: "Volatility 100 Index (ICT)", strategy: "ICT Sabri Malle", category: "Sintéticos Vol", trades: 15, win_rate: 66.7, tp1: 10, tp2: 5, tp3: 5, tp4: 5, be: 2, pnl: 1928.39, status: "Activo / Priorizado (+19.3R)" },
        { rank: 36, symbol: "Boom 1000 Index (ICT)", strategy: "ICT Sabri Malle", category: "Boom (Compras)", trades: 29, win_rate: 48.3, tp1: 14, tp2: 10, tp3: 10, tp4: 10, be: 4, pnl: 1900.0, status: "Activo / Priorizado (+19.0R)" },
        { rank: 37, symbol: "Crash 1000 Index (ICT)", strategy: "ICT Sabri Malle", category: "Crash (Ventas)", trades: 17, win_rate: 52.9, tp1: 9, tp2: 8, tp3: 8, tp4: 8, be: 1, pnl: 1792.67, status: "Activo / Priorizado (+17.9R)" },
        { rank: 38, symbol: "USDCAD (ICT Forex)", strategy: "ICT Sabri Malle", category: "Forex Core", trades: 16, win_rate: 62.5, tp1: 10, tp2: 4, tp3: 4, tp4: 4, be: 6, pnl: 1200.0, status: "Activo / Priorizado (#1 Forex ICT +12.0R)" },
        { rank: 39, symbol: "Wall Street 30 (ICT)", strategy: "ICT Sabri Malle", category: "Índices Bursátiles", trades: 14, win_rate: 64.3, tp1: 9, tp2: 4, tp3: 4, tp4: 4, be: 5, pnl: 1200.0, status: "Activo / Priorizado (+12.0R)" },
        { rank: 40, symbol: "EURUSD (ICT v2 Killzones)", strategy: "ICT Sabri Malle", category: "Forex Core", trades: 89, win_rate: 50.6, tp1: 45, tp2: 24, tp3: 24, tp4: 24, be: 18, pnl: 5100.0, status: "Activo / Top Performer Forex (PF 2.24)" },
        { rank: 41, symbol: "GBPUSD (ICT v2 Killzones)", strategy: "ICT Sabri Malle", category: "Forex Core", trades: 87, win_rate: 49.4, tp1: 43, tp2: 21, tp3: 21, tp4: 21, be: 17, pnl: 3654.8, status: "Activo / Rehabilitado (+36.5% PnL / PF 1.88)" },
        { rank: 42, symbol: "XAUUSD (Oro ICT)", strategy: "ICT Sabri Malle", category: "Metales", trades: 62, win_rate: 41.9, tp1: 26, tp2: 12, tp3: 12, tp4: 12, be: 11, pnl: 1900.0, status: "Activo / M15/M5 FVG CE (PF 1.58)" },
        { rank: 43, symbol: "US Tech 100 (ICT)", strategy: "ICT Sabri Malle", category: "Índices Bursátiles", trades: 6, win_rate: 50.0, tp1: 3, tp2: 3, tp3: 3, tp4: 3, be: 0, pnl: 600.0, status: "Activo / Priorizado (+6.0R)" },
        { rank: 44, symbol: "USDCHF (ICT Forex)", strategy: "ICT Sabri Malle", category: "Forex Core", trades: 21, win_rate: 42.9, tp1: 9, tp2: 3, tp3: 3, tp4: 3, be: 6, pnl: 300.0, status: "Activo / Priorizado (+3.0R)" },
        { rank: 45, symbol: "AUDUSD (ICT Forex)", strategy: "ICT Sabri Malle", category: "Forex Core", trades: 14, win_rate: 42.9, tp1: 6, tp2: 2, tp3: 2, tp4: 2, be: 4, pnl: 200.0, status: "Activo / Priorizado (+2.0R)" },
        { rank: 46, symbol: "US SP 500 (ICT)", strategy: "ICT Sabri Malle", category: "Índices Bursátiles", trades: 15, win_rate: 40.0, tp1: 6, tp2: 2, tp3: 2, tp4: 2, be: 4, pnl: 100.0, status: "Activo / Priorizado (+1.0R)" },
        // GOLD QUARTERS (ESTRATEGIA DE CUARTOS - WORKER GOLD)
        { rank: 47, symbol: "XAGUSD (Plata Cuartos)", strategy: "Gold Quarters", category: "Metales", trades: 170, win_rate: 41.8, tp1: 71, tp2: 34, tp3: 0, tp4: 0, be: 32, pnl: 986.12, status: "Activo / Priorizado (+9.86% Retorno)" },
        { rank: 48, symbol: "XAUUSD (Oro Cuartos)", strategy: "Gold Quarters", category: "Metales", trades: 656, win_rate: 41.3, tp1: 271, tp2: 131, tp3: 0, tp4: 0, be: 124, pnl: 252.76, status: "Activo / Priorizado (Nivel Cuartos $25/$50)" }
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
        { symbol: "Jump 50 Index (ICT)", strategy: "ICT Sabri Malle", trades: 20, win_rate: 15.0, sl_hits: 17, pnl: -958.95, reason: "Ruido lateral severo y gaps adversos en temporalidades H1 (-9.6R). Podado en ICT." },
        { symbol: "USDJPY (ICT)", strategy: "ICT Sabri Malle", trades: 11, win_rate: 18.2, sl_hits: 9, pnl: -700.0, reason: "Ausencia de expansión hacia TP2 y dilatación de spread (-7.0R). Podado en ICT." },
        { symbol: "GBPUSD (ICT v1 sin Killzones)", strategy: "ICT Sabri Malle", trades: 15, win_rate: 21.0, sl_hits: 12, pnl: -500.0, reason: "Superado: La versión v1 sin Killzones fallaba por operar fuera de sesión. Con la v2 (Killzones Londres/NY) se rehabilitó con 49.4% WR y +$3,654.80 USD." }
      ];

      // Métricas por pestaña
      const STRATEGY_METRICS = {
        all: {
          total_trades: "2,287",
          tp1: "1,054",
          tp1_rate: "46.1% global / 53.6% en Activos Core",
          tp2: "535",
          tp2_rate: "23.4% de expansiones completadas",
          tp3: "180",
          tp4: "129",
          be: "458",
          sl: "1,223",
          profit: "+$33,998",
          badge: "Consolidado 4 Estrategias",
          bars: { tp1: 46.1, tp2: 23.4, tp3: 7.9, tp4: 5.6, be: 20.0, sl: 53.5 }
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
