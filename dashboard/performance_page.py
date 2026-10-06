"""Plantilla HTML de la pantalla "Historial y Rendimiento" del dashboard.

Página dedicada para el análisis mensual de rendimiento, rankings de estrategias
por PnL neto y calendario de operaciones completas.
"""

from dashboard.page_loading import with_page_loading
from dashboard.period_panel import PANEL

_PERFORMANCE_BASE = r'''<!doctype html>
<html lang="es">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>DaemonBlackFx · Historial y Rendimiento</title>
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
      }
      * {
        box-sizing: border-box;
      }
      body {
        margin: 0;
        background: var(--bg);
        color: var(--t);
        font: 14px system-ui;
      }
      .w {
        max-width: 1380px;
        margin: auto;
        padding: 18px;
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
        width: 54px;
        height: 54px;
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
        gap: 14px;
        align-items: start;
        flex-wrap: wrap;
        margin-bottom: 18px;
      }
      .top h1 {
        margin: 0;
      }
      .muted {
        color: var(--m);
      }
      .nav {
        display: flex;
        gap: 8px;
      }
      .btn {
        color: var(--t);
        background: var(--p2);
        border: 1px solid var(--l);
        padding: 8px 11px;
        border-radius: 8px;
        text-decoration: none;
        font-size: 12px;
        transition: border-color 0.2s, color 0.2s;
      }
      .btn:hover, .btn.active {
        border-color: #f4ce63;
        color: #f4ce63;
      }
      #periodPerformance {
        margin: 0 !important;
      }
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
          <h1>Historial y rendimiento</h1>
          <div class="muted">
            La rentabilidad se calcula por setup completo, no por piernas TP individuales · Calendario de Santiago.
          </div>
        </div>
        <div class="nav">
          <a class="btn" href="/">Dashboard</a>
          <a class="btn" href="/account">Cuenta en vivo</a>
          <a class="btn active" href="/performance">Rendimiento</a>
          <a class="btn" href="/instruments">Instrumentos</a>
        </div>
      </div>
      <!-- PERIOD_PANEL_PLACEHOLDER -->
    </main>
  </body>
</html>
'''

PERFORMANCE_HTML = with_page_loading(_PERFORMANCE_BASE.replace("<!-- PERIOD_PANEL_PLACEHOLDER -->", PANEL))
