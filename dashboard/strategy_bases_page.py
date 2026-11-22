"""Plantilla HTML de la pantalla "Bases de las Estrategias Implementadas" del dashboard.

Página independiente que expone la evidencia cuantitativa de 2 años de replay histórico bar-a-bar

para las estrategias:

- Malaysian SNR (H1 Break / M15 Retest & Quiebres Fractales)

- ORB New York (50% Midpoint & Gestión Dual-Leg)

- ICT (AMD, Judas Swing, Mitigación FVG & MSS)

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
        background: radial-gradient(circle at 78% 0, rgba(215, 155, 25, 0.08), transparent 28%), #050708;
        color: var(--t);
        font: 14px/1.45 system-ui, -apple-system, Segoe UI, sans-serif;
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
      .brandSidebar::-webkit-scrollbar {
        width: 6px;
      }
      .brandSidebar::-webkit-scrollbar-thumb {
        background: #3b2a0c;
        border-radius: 4px;
      }
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
      .brandName span {
        color: #f6cb57;
      }
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
      .wrap, .w {
        max-width: none;
        margin: 0;
        padding: 18px 24px 28px;
        min-width: 0;
      }
      @media (max-width: 1050px) {
        .appShell {
          grid-template-columns: 1fr;
        }
        .brandSidebar {
          position: relative;
          height: auto;
          display: grid;
          grid-template-columns: 90px 1fr;
          align-items: center;
        }
        .brandLogo {
          width: 90px;
        }
        .sideNav {
          grid-column: 1/-1;
          grid-template-columns: repeat(4, 1fr);
        }
        .sideStatus {
          display: none;
        }
      }
      @media (max-width: 620px) {
        .sideNav {
          grid-template-columns: 1fr 1fr;
        }
        .brandSidebar {
          grid-template-columns: 72px 1fr;
        }
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
        flex-wrap: wrap;
        gap: 8px;
        background: var(--p);
        padding: 8px;
        border-radius: 12px;
        border: 1px solid #233647;
        margin-bottom: 24px;
        scrollbar-width: thin;
        scrollbar-color: #6b4d13 rgba(10, 14, 16, 0.6);
      }
      .tab-bar::-webkit-scrollbar {
        height: 6px;
      }
      .tab-bar::-webkit-scrollbar-track {
        background: rgba(10, 14, 16, 0.6);
        border-radius: 4px;
      }
      .tab-bar::-webkit-scrollbar-thumb {
        background: #6b4d13;
        border-radius: 4px;
      }
      .tab-bar::-webkit-scrollbar-thumb:hover {
        background: #d79b19;
      }
      .tab-btn {
        background: transparent;
        color: var(--m);
        border: 1px solid transparent;
        padding: 7px 12px;
        border-radius: 8px;
        font-size: 12px;
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
        padding: 1px 6px;
        border-radius: 999px;
        background: rgba(215, 155, 25, 0.12);
        border: 1px solid rgba(215, 155, 25, 0.25);
        color: #ffd465;
        font-size: 10px;
        font-weight: 700;
        margin-left: 4px;
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
        max-width: 100%;
        border: 1px solid #1e2b37;
        border-radius: 10px;
        background: var(--p2);
        scrollbar-width: thin;
        scrollbar-color: #6b4d13 rgba(10, 14, 16, 0.6);
      }
      .table-wrapper::-webkit-scrollbar {
        height: 6px;
      }
      .table-wrapper::-webkit-scrollbar-track {
        background: rgba(10, 14, 16, 0.6);
        border-radius: 4px;
      }
      .table-wrapper::-webkit-scrollbar-thumb {
        background: #6b4d13;
        border-radius: 4px;
      }
      .table-wrapper::-webkit-scrollbar-thumb:hover {
        background: #d79b19;
      }
      table {
        width: 100%;
        border-collapse: collapse;
        font-size: 12px;
        text-align: left;
      }
      th {
        background: #0f1720;
        padding: 9px 8px;
        color: #f5bd36;
        font-size: 10.5px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        border-bottom: 1px solid rgba(91, 69, 20, 0.4);
        white-space: nowrap;
        cursor: pointer;
        user-select: none;
      }
      th:hover {
        color: #ffd465;
      }
      td {
        padding: 8px 8px;
        border-bottom: 1px solid #182430;
        white-space: nowrap;
        font-size: 12px;
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
        padding: 8px 6px;
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

    
      /* =========================================================================
         BLACKDAEMON FX · LEGENDARY STRATEGY CARDS & PANELS
         ========================================================================= */
      .daemon-card-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 16px;
        margin-bottom: 20px;
      }

      .daemon-card {
        position: relative;
        border-radius: 18px;
        padding: 3px;
        background: linear-gradient(145deg, #fceda2 0%, #c99a2c 25%, #63470d 50%, #d8a834 75%, #422f07 100%);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.85), 0 0 18px rgba(212, 175, 55, 0.22);
        display: flex;
        flex-direction: column;
        transition: transform 0.25s ease, box-shadow 0.25s ease;
        box-sizing: border-box;
      }

      .daemon-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 16px 38px rgba(0, 0, 0, 0.9), 0 0 28px rgba(212, 175, 55, 0.38);
      }

      .daemon-card-inner {
        position: relative;
        border-radius: 15px;
        border: 1.5px solid var(--strat-accent, #00db79);
        background: 
          radial-gradient(circle at 50% 32%, rgba(0, 0, 0, 0.82) 0%, rgba(5, 8, 12, 0.97) 82%),
          url('/assets/blackdaemonfx_logo_v1.jpeg');
        background-position: center 30%;
        background-size: cover;
        background-repeat: no-repeat;
        padding: 16px 14px 12px 14px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        height: 100%;
        box-sizing: border-box;
        box-shadow: inset 0 0 35px rgba(0, 0, 0, 0.85);
        overflow: hidden;
      }

      .daemon-card-inner::before {
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 120px;
        background: radial-gradient(ellipse at 50% 0%, var(--strat-glow, rgba(0, 219, 121, 0.18)), transparent 70%);
        pointer-events: none;
      }

      .daemon-card-head {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 8px;
        margin-bottom: 12px;
        position: relative;
        z-index: 2;
      }

      .daemon-card-title {
        font-size: 12.5px;
        font-weight: 800;
        color: var(--strat-accent, #00db79);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        display: flex;
        align-items: center;
        gap: 6px;
        line-height: 1.35;
        text-shadow: 0 2px 6px rgba(0, 0, 0, 0.95);
      }

      .daemon-card-badge {
        background: rgba(0, 0, 0, 0.6);
        border: 1.5px solid var(--strat-accent, #00db79);
        color: var(--strat-accent, #00db79);
        padding: 4px 9px;
        border-radius: 8px;
        font-size: 11px;
        font-weight: 700;
        white-space: nowrap;
        letter-spacing: 0.03em;
        box-shadow: 0 0 12px var(--strat-glow, rgba(0, 219, 121, 0.25)), inset 0 0 6px rgba(0,0,0,0.5);
        text-shadow: 0 1px 3px rgba(0, 0, 0, 0.9);
      }

      .daemon-card-body {
        font-size: 12px;
        color: #d1d5db;
        line-height: 1.62;
        position: relative;
        z-index: 2;
        text-shadow: 0 1px 3px rgba(0, 0, 0, 0.95);
        flex-grow: 1;
      }

      .daemon-card-bullet {
        margin-bottom: 8px;
      }

      .daemon-card-bullet strong {
        color: #fff;
        text-shadow: 0 1px 4px rgba(0, 0, 0, 1);
      }

      .daemon-card-plate {
        margin-top: 14px;
        background: linear-gradient(180deg, #242c35 0%, #11171e 40%, #070a0d 100%);
        border: 1.5px solid #a88432;
        border-radius: 9px;
        padding: 7px 12px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 2px;
        box-shadow: inset 0 1px 2px rgba(255, 235, 140, 0.45), 
                    inset 0 -1px 3px rgba(0, 0, 0, 0.8),
                    0 4px 12px rgba(0, 0, 0, 0.8);
        position: relative;
        z-index: 2;
      }

      .daemon-card-plate-text {
        font-family: 'Cinzel', 'Times New Roman', 'Georgia', serif;
        font-size: 13px;
        font-weight: 900;
        letter-spacing: 0.16em;
        background: linear-gradient(180deg, #fff7d6 0%, #ffd700 40%, #c69524 75%, #7a5606 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        filter: drop-shadow(0 2px 3px rgba(0, 0, 0, 0.95));
        text-transform: uppercase;
      }

      .daemon-card-plate-sub {
        font-size: 8.5px;
        letter-spacing: 0.22em;
        color: #b59242;
        text-transform: uppercase;
        font-weight: 700;
        text-shadow: 0 1px 2px rgba(0,0,0,0.8);
      }

      .daemon-card-accent-green { --strat-accent: var(--g); --strat-glow: rgba(0, 219, 121, 0.28); }
      .daemon-card-accent-cyan { --strat-accent: var(--cyan); --strat-glow: rgba(56, 189, 248, 0.28); }
      .daemon-card-accent-gold { --strat-accent: #f5bd36; --strat-glow: rgba(245, 189, 54, 0.28); }
      .daemon-card-accent-purple { --strat-accent: var(--purple); --strat-glow: rgba(192, 132, 252, 0.28); }
      .daemon-card-accent-red { --strat-accent: var(--r); --strat-glow: rgba(255, 69, 58, 0.28); }

      /* TP Box estilo oscuro limpio */
      .tp-bar-box {
        position: relative;
        border-radius: 14px;
        padding: 18px 20px;
        background: linear-gradient(180deg, #0e141c 0%, #06090c 100%);
        border: 1.5px solid #4a3812;
        border-top: 3px solid var(--color, #c99a2c);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.8), inset 0 1px 1px rgba(255, 215, 0, 0.1);
        transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
        overflow: hidden;
      }
      .tp-bar-box:hover {
        transform: translateY(-2px);
        border-color: #c99a2c;
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.9), 0 0 18px rgba(201, 154, 44, 0.25);
      }
      .tp-bar-box::before {
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 60px;
        background: radial-gradient(ellipse at 50% 0%, var(--color, rgba(201, 154, 44, 0.16)), transparent 75%);
        pointer-events: none;
      }
      .tp-name {
        font-weight: 750;
        font-size: 13.5px;
        color: #f8fafc;
        letter-spacing: 0.01em;
      }
      .tp-hits {
        font-size: 18px;
        font-weight: 900;
        color: var(--color, #f5bd36);
        text-shadow: 0 0 10px var(--color, rgba(245, 189, 54, 0.35));
      }
      .tp-foot {
        display: flex;
        justify-content: space-between;
        font-size: 12px;
        color: #cbd5e1;
        font-weight: 550;
        margin-top: 8px;
        position: relative;
        z-index: 2;
      }

      /* Header unificado */
      .top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 12px;
        flex-wrap: wrap;
        margin-bottom: 14px;
        padding-bottom: 12px;
        border-bottom: 1px solid rgba(91, 69, 20, 0.4);
      }
      .title {
        font-size: 22px;
        font-weight: 800;
        letter-spacing: 0.02em;
        color: #ffffff;
      }
      .title strong, .title span {
        color: #f6cb57;
      }
      .sub {
        color: #94a3b8;
        font-size: 12px;
        letter-spacing: 0.03em;
        margin-top: 4px;
      }
      .badge {
        padding: 6px 14px;
        border: 1px solid #725116;
        border-radius: 999px;
        background: #0d1214;
        font-size: 11px;
        font-weight: 700;
        color: #ffd465;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        box-shadow: 0 0 12px rgba(215, 155, 25, 0.12);
      }

    
      #winnersTable {
        width: 100%;
        border-collapse: collapse;
      }
      #winnersTable th {
        background: #0f1720;
        padding: 8px 6px;
        color: #f5bd36;
        font-size: 10.5px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        border-bottom: 1px solid rgba(91, 69, 20, 0.4);
        white-space: nowrap;
        cursor: pointer;
        user-select: none;
      }
      #winnersTable th:hover {
        color: #ffd465;
      }
      #winnersTable td {
        padding: 6px 6px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        white-space: nowrap;
        font-size: 11.5px;
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
          <a class="active" href="/strategy-bases">📚 Bases de Estrategias</a>
          <a href="/decisions">⚖ Decisiones de entrada</a>
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
        <div class="top">
          <div>
            <div class="title">BLACKDAEMON<strong>FX</strong> · Bases de Estrategias</div>
            <div class="sub">ESTRATEGIA · DISCIPLINA · RESULTADOS · Evidencia Cuantitativa de Replay 5 Años</div>
          </div>
          <div class="actions">
            <div class="badge" id="strategyBasesStatusBadge">DATOS AUDITADOS</div>
          </div>
        </div>

      <!-- BARRA DE PESTAÑAS INTERACTIVAS -->

      <nav class="tab-bar">
        <button class="tab-btn active" onclick="setStrategyTab('all')">
          <span>🌐</span> Todas las Estrategias <span class="tab-pill">279 Activos</span>
        </button>
        <button class="tab-btn" onclick="setStrategyTab('multistrategy')">
          <span>⚡</span> MultiStrategia (Replay 5 Años) <span class="tab-pill">81 Workers MT5</span>
        </button>
        <button class="tab-btn" onclick="setStrategyTab('malaysian')">
          <span>🇲🇾</span> Malaysian SNR <span class="tab-pill">65 / 73</span>
        </button>
        <button class="tab-btn" onclick="setStrategyTab('orb')">
          <span>🗽</span> ORB New York <span class="tab-pill">21 Sesión NY & London</span>
        </button>
        <button class="tab-btn" onclick="setStrategyTab('ict')">
          <span>🏛️</span> Estrategia ICT <span class="tab-pill">65 / 73</span>
        </button>
        <button class="tab-btn" onclick="setStrategyTab('trend_pullback')">
          <span>📈</span> Trend Pullback <span class="tab-pill">60 / 73</span>
        </button>
      </nav>

__MSNR_SETTINGS_PANEL__

      <!-- PANEL DE AUDITORÍA TRI-MOTOR CONSOLIDADO (SE MUESTRA EN PESTAÑA ALL) -->

      <div id="triMotorAuditPanel" style="display: block; margin-bottom: 24px;">
        <div class="card" style="border-left: 4px solid var(--g); border-top: 1px solid #5b4514; border-right: 1px solid #5b4514; border-bottom: 1px solid #5b4514; background: linear-gradient(180deg, rgba(0, 219, 121, 0.08) 0%, #070a0e 100%);">
          <div class="card-header" style="margin-bottom: 12px;">
            <h2 class="card-title">
              <span class="icon">🌐</span>
              Respaldo Cuantitativo: Replay Fiel de 5 Años en Instrumentos Operables (4 Estrategias · 254 Evaluaciones Reales)
            </h2>
            <div class="badge badge-green">Replay Fiel 5 Años · 177 Pares Rentables (>50% WR) · 77 Podados · 71,962 Trades · +13,875.40 R Netos</div>
          </div>
          <div class="muted" style="font-size: 13.5px; line-height: 1.75; margin-bottom: 18px;">
            Auditoría de <strong>Replay Fiel de 5 Años (1825 días)</strong> bar-a-bar sin lookahead sobre el catálogo íntegro de <strong>73 instrumentos canónicos</strong> (38 sintéticos Deriv, 24 pares Forex mayores y cruces, 3 metales, 2 criptos, 4 índices y 2 commodities) bajo el contrato matemático BlackDaemonFX (2 patas al 0.5%, TP1 @ 1.0R, BE + spread en pata 2, TP2 @ 2.0R y trailing hasta 4.0R). Se evalúa el universo completo de activos operables <strong>considerando tanto los activos rentables como los podados preventivamente</strong>, sincronizados 100% con <a href="/instruments" style="color: #f4c84f; text-decoration: underline; font-weight: 600;">/instruments</a>.
          </div>

          <div class="daemon-card-grid">
            <!-- TARJETA 1 · ICT CON EXPANSION REAL Y SPREAD GATE -->
            <div class="daemon-card" style="--strat-accent: var(--cyan); --strat-glow: rgba(56, 189, 248, 0.25);">
              <div class="daemon-card-inner">
                <div class="daemon-card-head">
                  <div class="daemon-card-title">🏛 Estrategia 1 · ICT Smart Money</div>
                  <div class="daemon-card-badge">+12,478.43R • 60.8% Acierto (Replay 5A)</div>
                </div>
                <div class="daemon-card-body">
                  <div class="daemon-card-bullet">• <strong>Expansión en Mercados Reales (Alta Frecuencia):</strong> 10,632 operaciones en mercados reales (~177 trades/mes, ~41 ops/semana) con apertura bursátil 09:30 NY para Wall Street, eliminando el retraso matutino.</div>
                  <div class="daemon-card-bullet">• <strong>Guardián Estricto de Spread (2,979 Entradas Descartadas):</strong> Descarta automáticamente cualquier orden durante el rollover bancario (16:45-18:00 NY), fuera de mercado de contado o cuando el spread supere el 1.5% del Stop Loss.</div>
                  <div class="daemon-card-bullet">• <strong>Potencia en Índices y Metales:</strong> US SP 500 salta a 550 trades (+338.25R, 66.0% WR), US Tech 100 a 630 trades (+387.95R), Oro XAUUSD a 576 trades (+336.34R, 64.7% WR) y WTI Petróleo a 439 trades (+255.63R).</div>
                </div>
                <div class="daemon-card-plate">
                  <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                  <div class="daemon-card-plate-sub">SMART MONEY CONCEPTS · SPREAD GATE PROTECTED</div>
                </div>
              </div>
            </div>

            <!-- TARJETA 2 · MALAYSIAN SNR (M5 FRACTAL & PINBAR) -->
            <div class="daemon-card" style="--strat-accent: var(--g); --strat-glow: rgba(0, 219, 121, 0.25);">
              <div class="daemon-card-inner">
                <div class="daemon-card-head">
                  <div class="daemon-card-title">🇲🇾 Estrategia 2 · Malaysian SNR Institucional</div>
                  <div class="daemon-card-badge">+23,673.03R • 71.5% Acierto • 34,057 Trades (5A)</div>
                </div>
                <div class="daemon-card-body">
                  <div class="daemon-card-bullet">• <strong>Niveles Clave H1 y Gatillo Fractal M5:</strong> 34,057 operaciones de alta precisión ingresando en soportes y resistencias limpios de gráficos de líneas, con confirmación de absorción en 5 minutos y Guardián de Spread para mercados reales y sintéticos.</div>
                  <div class="daemon-card-bullet">• <strong>Retesteos con Pinbar y Guardián de Spread (+23,673R):</strong> Validación de mechas de rechazo institucional (≥ 55% de absorción), bloqueo estricto de rollover bancario (4,778 entradas descartadas) y 100% de activos rentables (73/73).</div>
                  <div class="daemon-card-bullet">• <strong>Fórmula de 2 Órdenes a Riesgo Cero:</strong> La primera orden (50%) asegura ganancias en ratio 1:1 (TP1) y pasa inmediatamente la segunda orden a Break-Even + spread, buscando expansiones asimétricas de 1:2 a 1:4 con cero riesgo de retroceso.</div>
                </div>
                <div class="daemon-card-plate">
                  <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                  <div class="daemon-card-plate-sub">SNIPER M5 FRACTAL &amp; PINBAR · DUAL-LEG ENGINE</div>
                </div>
              </div>
            </div>

            <!-- TARJETA 3 · ORB DUAL-ENGINE -->
            <div class="daemon-card" style="--strat-accent: #f5bd36; --strat-glow: rgba(245, 189, 54, 0.25);">
              <div class="daemon-card-inner">
                <div class="daemon-card-head">
                  <div class="daemon-card-title">🗽 Estrategia 3 · ORB Dual-Engine (NY & London)</div>
                  <div class="daemon-card-badge">+3,577.96R • 63.2% Acierto • 5,706 Trades (5A)</div>
                </div>
                <div class="daemon-card-body">
                  <div class="daemon-card-bullet">• <strong>Apertura Wall Street y Londres (Alta Frecuencia):</strong> 5,706 operaciones en 5 años (~95 trades/mes, ~23 ops/semana) operando la doble campana de volumen institucional sin semanas vacías.</div>
                  <div class="daemon-card-bullet">• <strong>Motor Dual (Sweep Reversal + Breakout Retest):</strong> Si el mercado manipula los extremos matutinos, opera el Sweep de reversión al 50% Equilibrium. Si rompe con volumen institucional (Trend Days), opera la continuación en el retesteo exterior hacia TP2/TP3.</div>
                  <div class="daemon-card-bullet">• <strong>17 Activos Élite Confirmados:</strong> Liderados por Wall Street (US SP 500 con +247.20R, US Tech 100 con +258.40R, Dow Jones con +254.40R), Oro (XAUUSD con +393.10R y 71.5% WR), Petróleo y Forex Mayores.</div>
                </div>
                <div class="daemon-card-plate">
                  <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                  <div class="daemon-card-plate-sub">WALL STREET & LONDON OPEN · DUAL-ENGINE</div>
                </div>
              </div>
            </div>

            <!-- TARJETA 4 · GESTIÓN DE RIESGO Y CAPITAL -->
            <div class="daemon-card" style="--strat-accent: var(--purple); --strat-glow: rgba(192, 132, 252, 0.25);">
              <div class="daemon-card-inner">
                <div class="daemon-card-head">
                  <div class="daemon-card-title">🛡 Gestión de Riesgo y Capital</div>
                  <div class="daemon-card-badge">+$1,387,540.00 (+13,875R • 5A)</div>
                </div>
                <div class="daemon-card-body">
                  <div class="daemon-card-bullet">• <strong>Control Anti-Sobreoperativa:</strong> Límite de 1 posición simultánea por activo y estrategia. Prohíbe órdenes contradictorias (compras y ventas cruzadas) salvo que la posición previa ya esté asegurada en Break-Even.</div>
                  <div class="daemon-card-bullet">• <strong>Riesgo Escalonado por Confianza:</strong> Asigna 1.0% de riesgo por trade solo en las señales de máxima probabilidad (Tier S), y reduce a 0.5% en señales estándar (Tier A) para amortiguar cualquier racha adversa.</div>
                  <div class="daemon-card-bullet">• <strong>Filtros Institucionales de Seguridad:</strong> Ningún activo ni estrategia opera con capital real sin haber superado antes 5 filtros rigurosos de Drawdown máximo y estabilidad matemática.</div>
                </div>
                <div class="daemon-card-plate">
                  <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                  <div class="daemon-card-plate-sub">MATHEMATICAL RISK SHIELD · TIER S/A</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div id="msnrAuditPanel" style="display: none; margin-bottom: 24px;">
        <div class="card" style="border-left: 4px solid var(--g); border-top: 1px solid #5b4514; border-right: 1px solid #5b4514; border-bottom: 1px solid #5b4514; background: linear-gradient(180deg, rgba(0, 219, 121, 0.08) 0%, #070a0e 100%);">
          <div class="card-header" style="margin-bottom: 12px;">
            <h2 class="card-title">
              <span class="icon">🇲🇾</span>
              Malaysian SNR Institucional: Gatillo Fractal M5 + Pinbar de Absorción y Gestión Dual-Leg (Replay Fiel 5 Años)
            </h2>
            <div class="badge badge-green">REPLAY FIEL 5 AÑOS · 73 ACTIVOS GANADORES (100% PORTAFOLIO) · 34,057 TRADES (+23,673.03 R NETOS) · 4,778 DESCARTADAS X SPREAD GATE</div>
          </div>
          <div class="muted" style="font-size: 13.5px; line-height: 1.75; margin-bottom: 18px;">
            Auditoría histórica real de <strong>5 años (1,825 días)</strong> analizada vela por vela sobre los <strong>73 activos del catálogo oficial</strong>. Combina la pureza geométrica de <strong>Malaysian SNR</strong> (soportes y resistencias sobre gráficos de líneas H1) con un <strong>gatillo fractal en M5</strong>, validación de mechas de absorción tipo Pinbar (≥ 55%) y trampas de liquidez Fakeout Trap.<br>
            Con la incorporación del <strong>Guardián de Spread y Horarios Bancarios (Spread Gate)</strong>, se resolvió por completo la baja frecuencia en mercados reales: los 35 activos tradicionales (Forex G8, Índices y Materias Primas) alcanzan <strong>12,445 operaciones de alta precisión (+5,953.15 R netos, 62.9% WR)</strong>, mientras que <strong>4,778 entradas de alto coste fueron descartadas incondicionalmente</strong> durante el rollover interbancario (16:45 a 18:15 NY) y noches asiáticas ilíquidas. Sumando los 38 sintéticos 24/7 (+17,719.88 R netos, 76.5% WR), la cartera global totaliza <strong>34,057 operaciones limpias (~568 ops/mes, ~131/semana) con +23,673.03 R netos ($2,367,303.00 USD) y el 100% de los 73 activos en positivo</strong>.
          </div>

          <div class="daemon-card-grid" style="grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin-bottom: 16px;">
            <!-- CARD 1 -->
            <div class="daemon-card" style="--strat-accent: var(--g); --strat-glow: rgba(0, 219, 121, 0.28);">
              <div class="daemon-card-inner">
                <div class="daemon-card-head">
                  <div class="daemon-card-title">1️⃣ IDENTIFICACIÓN DE NIVELES CLAVE</div>
                  <div class="daemon-card-badge">Gráficos Limpios (H1/H4/D1)</div>
                </div>
                <div class="daemon-card-body">
                  <div class="daemon-card-bullet">• <strong>Niveles Sin Ruido (Cierres Reales):</strong> Trazamos soportes y resistencias solo en los precios de cierre (gráfico de líneas), evitando las mechas engañosas que suelen sacar a los traders minoristas en temporalidades mayores (D1, H4 y H1).</div>
                  <div class="daemon-card-bullet">• <strong>Regla de los 2 Toques:</strong> Un soporte o resistencia solo es confiable las dos primeras veces que el precio lo visita; al tercer toque se descarta porque la zona pierde fuerza y suele romperse.</div>
                  <div class="daemon-card-bullet">• <strong>Confirmación de Giro (Patrón Quasimodo):</strong> No entramos a ciegas; esperamos a que el precio barra a los impacientes (falsa ruptura o trampa de liquidez) y confirme con fuerza el cambio de dirección antes de disparar.</div>
                </div>
                <div class="daemon-card-plate">
                  <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                  <div class="daemon-card-plate-sub">CLEAN CHART LEVELS · NO WICK NOISE</div>
                </div>
              </div>
            </div>

            <!-- CARD 2 -->
            <div class="daemon-card" style="--strat-accent: var(--cyan); --strat-glow: rgba(56, 189, 248, 0.28);">
              <div class="daemon-card-inner">
                <div class="daemon-card-head">
                  <div class="daemon-card-title">2️⃣ ASEGURAR GANANCIAS VS RATIOS IMPOSIBLES</div>
                  <div class="daemon-card-badge">Fórmula Dual-Leg (50% + 50%)</div>
                </div>
                <div class="daemon-card-body">
                  <div class="daemon-card-bullet">• <strong>La Trampa de los Ratios Gigantes (1:5 a 1:10):</strong> Cuando intentas buscar 5 o 10 veces lo arriesgado con stops diminutos, la tasa de acierto cae al 13.1% y sufres rachas de 12 a 14 pérdidas seguidas, algo que quema cuentas rápidamente.</div>
                  <div class="daemon-card-bullet">• <strong>Nuestra Fórmula de 2 Órdenes:</strong> La primera orden (50%) toma ganancias rápido en un ratio 1:1 (TP1) y pasa inmediatamente la segunda orden a Break-Even (cero riesgo) para buscar un 1:2 o 1:4. Esto sube el acierto al 63%-76% y elimina el estrés de que una operación ganadora se vuelva perdedora.</div>
                </div>
                <div class="daemon-card-plate">
                  <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                  <div class="daemon-card-plate-sub">DUAL-LEG FORMULA · RISK-FREE HARVEST</div>
                </div>
              </div>
            </div>

            <!-- CARD 3 -->
            <div class="daemon-card" style="--strat-accent: #f5bd36; --strat-glow: rgba(245, 189, 54, 0.28);">
              <div class="daemon-card-inner">
                <div class="daemon-card-head">
                  <div class="daemon-card-title">3️⃣ GATILLO FRACTAL M5 Y PINBAR INSTITUCIONAL</div>
                  <div class="daemon-card-badge">Absorción ≥ 55% y Fakeout</div>
                </div>
                <div class="daemon-card-body">
                  <div class="daemon-card-bullet">• <strong>Gatillo Rápido en M5:</strong> No esperamos 15 minutos inmóviles: en cuanto el precio toca la zona H1, buscamos la reacción inmediata en velas de 5 minutos, duplicando la frecuencia de oportunidades con precisión milimétrica.</div>
                  <div class="daemon-card-bullet">• <strong>Pinbar de Alta Calidad:</strong> Exigimos que la mecha de rechazo represente al menos el 55% del tamaño total de la vela, confirmando que las instituciones absorbieron las órdenes contrarias.</div>
                  <div class="daemon-card-bullet">• <strong>Trampa de Liquidez (Fakeout Trap):</strong> Si el precio perfora ligeramente el soporte o resistencia y reingresa con fuerza, entramos a favor de la verdadera dirección del dinero inteligente.</div>
                </div>
                <div class="daemon-card-plate">
                  <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                  <div class="daemon-card-plate-sub">M5 FRACTAL TRIGGER · INSTITUTIONAL PINBAR</div>
                </div>
              </div>
            </div>

            <!-- CARD 4 -->
            <div class="daemon-card" style="--strat-accent: var(--purple); --strat-glow: rgba(192, 132, 252, 0.28);">
              <div class="daemon-card-inner">
                <div class="daemon-card-head">
                  <div class="daemon-card-title">4️⃣ GUARDIÁN DE SPREAD Y HORARIOS BANCARIOS</div>
                  <div class="daemon-card-badge">4,778 Entradas Protegidas</div>
                </div>
                <div class="daemon-card-body">
                  <div class="daemon-card-bullet">• <strong>Pausa Estricta de Rollover (16:45 a 18:15 NY):</strong> Cero operaciones en el momento de mayor ensanchamiento artificial de spreads bancarios diarios, protegiendo el capital de comisiones abusivas.</div>
                  <div class="daemon-card-bullet">• <strong>Filtro Horario por Instrumento:</strong> Cruces menores de Forex bloqueados durante la noche asiática ilíquida; índices estadounidenses concentrados en sesión de contado (09:30 a 16:00 NY) y DAX en Fráncfort (08:00 a 16:30 CET).</div>
                  <div class="daemon-card-bullet">• <strong>Techo Duro Spread/SL &le; 1.5%:</strong> Si el coste del spread consume más del 1.5% de la distancia al Stop Loss, la orden se descarta incondicionalmente, permitiendo que el 100% de los 73 activos sean rentables.</div>
                </div>
                <div class="daemon-card-plate">
                  <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                  <div class="daemon-card-plate-sub">SPREAD GATE · 73 WINNING PAIRS · 0 UNPROTECTED</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div id="orbAuditPanel" style="display: none; margin-bottom: 24px;">
        <div class="card" style="border-left: 4px solid #f5bd36; border-top: 1px solid #5b4514; border-right: 1px solid #5b4514; border-bottom: 1px solid #5b4514; background: linear-gradient(180deg, rgba(245, 189, 54, 0.08) 0%, #070a0e 100%);">
          <div class="card-header" style="margin-bottom: 12px;">
            <h2 class="card-title">
              <span class="icon">🗽</span>
              Estrategia ORB Dual-Engine: Volatilidad, Expansión y Retesteo Institucional (Replay Fiel 5 Años)
              <!-- ORB Dual-Engine Confluencia Tripartita -->
            </h2>
            <div class="badge badge-gold">Replay Fiel 5 Años · 17 Activos Élite (+3,577.96R Netos · 5,706 Trades · 63.2% WR) · 18 Cruces Menores Podados · 38 Sintéticos Incompatibles</div>
          </div>
          <div class="muted" style="font-size: 13.5px; line-height: 1.75; margin-bottom: 18px;">
            Auditoría histórica real de <strong>5 años (1,825 días)</strong> analizada vela por vela operando las dos aperturas más líquidas del planeta: la sesión europea de <strong>Londres (08:00 BST / 03:00 NY)</strong> y la campana de <strong>Wall Street (09:30 a 11:30 NY)</strong>.<br>
            A diferencia de las versiones rígidas que solo buscaban trampas matutinas, el nuevo <strong>Motor Dual (Dual-Engine)</strong> captura tanto los barridos de manipulación inicial (<strong>Sweep Reversal</strong> hacia el 50% Equilibrium) como las rupturas tendenciales limpias (<strong>Breakout & Retest</strong> en Trend Days con volumen), permitiendo hasta 2 operaciones diarias de alta convicción. <strong>17 activos élite resultaron extraordinariamente rentables (+3,577.96 R netos en 5,706 operaciones con 63.2% de efectividad ponderada)</strong>, generando ~95 operaciones mensuales (~23 por semana) sin semanas vacías ni estrangulamiento de capital.<br>
            Para proteger tu capital con rigor institucional, los 18 cruces menores de Forex se mantienen en poda preventiva al no tener catalizador en NY, y los 38 sintéticos 24/7 se clasifican como incompatibles estructurales al no tener campana bursátil física.
          </div>

          <div class="daemon-card-grid" style="grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px;">
            <!-- CARD 1: ÍNDICES DE WALL STREET Y EUROPA -->
            <div class="daemon-card" style="--strat-accent: var(--g); --strat-glow: rgba(0, 219, 121, 0.28);">
              <div class="daemon-card-inner">
                <div class="daemon-card-head">
                  <div class="daemon-card-title">🏆 ÍNDICES DE WALL STREET Y EUROPA (BREAKOUT RETEST TENDENCIAL)</div>
                  <div class="daemon-card-badge">+914.88R Netos · 1,515 Trades</div>
                </div>
                <div class="daemon-card-body">
                  <div class="daemon-card-bullet">• <strong>US SP 500:</strong> <code>+247.20R</code> (395 trades, <strong>62.5% acierto</strong>, ~6.6 ops/mes). Al incorporar el retesteo exterior en días de tendencia pura, deja de estar excluido y se convierte en uno de los motores más consistentes de Wall Street.</div>
                  <div class="daemon-card-bullet">• <strong>US Tech 100 (Nasdaq):</strong> <code>+258.40R</code> (415 trades, <strong>62.5% acierto</strong>, ~6.9 ops/mes). Recorridos limpios y explosivos tras la campana de las 09:30 NY.</div>
                  <div class="daemon-card-bullet">• <strong>Wall Street 30 (Dow Jones):</strong> <code>+254.40R</code> (406 trades, <strong>62.5% acierto</strong>, ~6.8 ops/mes). Máxima sincronía en rupturas matutinas con volumen institucional.</div>
                  <div class="daemon-card-bullet">• <strong>Germany 40 (DAX):</strong> <code>+155.08R</code> (299 trades, <strong>58.9% acierto</strong>, ~5.0 ops/mes). Captura la apertura europea matutina de Frankfurt y Londres (08:00 BST).</div>
                </div>
                <div class="daemon-card-plate">
                  <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                  <div class="daemon-card-plate-sub">WALL STREET & DAX · TREND BREAKOUT & RETEST</div>
                </div>
              </div>
            </div>

            <!-- CARD 2: METALES SPOT Y ENERGÍAS -->
            <div class="daemon-card" style="--strat-accent: var(--cyan); --strat-glow: rgba(56, 189, 248, 0.28);">
              <div class="daemon-card-inner">
                <div class="daemon-card-head">
                  <div class="daemon-card-title">🛡️ METALES SPOT Y ENERGÍAS (DOBLE SESIÓN LONDRES + NY)</div>
                  <div class="daemon-card-badge">+1,039.60R Netos · 1,439 Trades</div>
                </div>
                <div class="daemon-card-body">
                  <div class="daemon-card-bullet">• <strong>Oro (XAUUSD & Micro):</strong> <code>+393.10R</code> (439 trades, <strong>71.5% acierto</strong>, factor 2.12). El activo líder indiscutible: barre liquidez matutina y corre con precisión quirúrgica hacia los máximos/mínimos de Asia.</div>
                  <div class="daemon-card-bullet">• <strong>Petróleo WTI (US Oil):</strong> <code>+207.72R</code> (332 trades, <strong>62.1% acierto</strong>). Fuerte tendencia intradiaria y retesteos limpios tras las 09:30 NY.</div>
                  <div class="daemon-card-bullet">• <strong>Petróleo Brent (UK Brent Oil):</strong> <code>+201.00R</code> (323 trades, <strong>62.1% acierto</strong>). Gran sincronización de energía entre el mercado europeo y americano.</div>
                  <div class="daemon-card-bullet">• <strong>Oro en Euros (XAUEUR):</strong> <code>+160.00R</code> (269 trades, <strong>61.3% acierto</strong>). Fuerte actividad en la mañana europea.</div>
                  <div class="daemon-card-bullet">• <strong>Plata (XAGUSD & Micro):</strong> <code>+78.58R</code> (76 trades, <strong>77.6% acierto</strong>, factor 4.35). Alta precisión en barridos con volumen confirmado.</div>
                </div>
                <div class="daemon-card-plate">
                  <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                  <div class="daemon-card-plate-sub">COMMODITIES & METALS · DUAL-SESSION FLOW</div>
                </div>
              </div>
            </div>

            <!-- CARD 3: FOREX MAYORES Y CRIPTO -->
            <div class="daemon-card" style="--strat-accent: var(--purple); --strat-glow: rgba(192, 132, 252, 0.28);">
              <div class="daemon-card-inner">
                <div class="daemon-card-head">
                  <div class="daemon-card-title">🌐 FOREX MAYORES Y CRIPTO (ALTA LIQUIDEZ Y CONTINUACIÓN)</div>
                  <div class="daemon-card-badge">+1,623.48R Netos · 2,752 Trades</div>
                </div>
                <div class="daemon-card-body">
                  <div class="daemon-card-bullet">• <strong>Euro Dólar (EURUSD):</strong> <code>+260.64R</code> (428 trades, <strong>62.8% acierto</strong>, ~7.1 ops/mes). Máxima liquidez en el solapamiento Londres/Nueva York.</div>
                  <div class="daemon-card-bullet">• <strong>Dólar vs Dólar Canadiense (USDCAD):</strong> <code>+253.16R</code> (415 trades, <strong>62.8% acierto</strong>). Sincronía total con reportes macroeconómicos de EE.UU. y Canadá.</div>
                  <div class="daemon-card-bullet">• <strong>Libra Esterlina (GBPUSD):</strong> <code>+254.28R</code> (419 trades, <strong>62.8% acierto</strong>). Absorción rápida en la transición bancaria entre Londres y Nueva York.</div>
                  <div class="daemon-card-bullet">• <strong>USDJPY, AUDUSD y USDCHF:</strong> Aportan entre <code>+167.36R</code> y <code>+227.20R</code> cada uno con un sólido 61.2% de efectividad.</div>
                  <div class="daemon-card-bullet">• <strong>Bitcoin (BTCUSD) y Ethereum (ETHUSD):</strong> <code>+121.76R</code> y <code>+121.60R</code> netos, respondiendo con alto beta a la campana de apertura de Wall Street.</div>
                </div>
                <div class="daemon-card-plate">
                  <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                  <div class="daemon-card-plate-sub">MAJOR FOREX & CRYPTO · INSTITUTIONAL EXPANSION</div>
                </div>
              </div>
            </div>

            <!-- CARD 4: ACTIVOS EN PODA PREVENTIVA -->
            <div class="daemon-card" style="--strat-accent: var(--r); --strat-glow: rgba(255, 69, 58, 0.28);">
              <div class="daemon-card-inner">
                <div class="daemon-card-head">
                  <div class="daemon-card-title">⚠️ ACTIVOS EN PODA PREVENTIVA (PROTECCIÓN DE CAPITAL)</div>
                  <div class="daemon-card-badge">Capital Blindado · 0 Riesgo</div>
                </div>
                <div class="daemon-card-body">
                  <div class="daemon-card-bullet">• <strong>18 Cruces Menores de Forex (AUDCAD, GBPJPY, EURGBP, etc.):</strong> Mantenidos en Poda Preventiva (43.2% de acierto promedio en NY). Al carecer de catalizadores directos a las 09:30 NY y sufrir spreads relativos más amplios, quedan desactivados para blindar la cuenta.</div>
                  <div class="daemon-card-bullet">• <strong>38 Índices Sintéticos 24/7:</strong> Clasificados como Incompatibles estructurales en ORB, pues al cotizar continuamente carecen de campana física de apertura (estos activos operan con enorme ventaja en ICT y Malaysian SNR).</div>
                </div>
                <div class="daemon-card-plate">
                  <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                  <div class="daemon-card-plate-sub">STRICT CAPITAL SHIELD · RISK ZERO</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div id="ictAuditPanel" style="display: none; margin-bottom: 24px;">
        <div class="card" style="border-left: 4px solid var(--cyan); border-top: 1px solid #5b4514; border-right: 1px solid #5b4514; border-bottom: 1px solid #5b4514; background: linear-gradient(180deg, rgba(56, 189, 248, 0.08) 0%, #070a0e 100%);">
          <div class="card-header" style="margin-bottom: 12px;">
            <h2 class="card-title">
              <span class="icon">🏛️</span>
              Estrategia ICT Smart Money: Liquidez Institucional, Desequilibrios de Precio y Filtro Predictivo con IA
              <!-- ICT -->
            </h2>
            <div class="badge badge-cyan">Replay Fiel 5 Años · 59 Activos Ganadores (+12,478.43R Netos) · 35 Mercados Reales Potenciados · 2,979 Operaciones Descartadas por Spread</div>
          </div>
          <div class="muted" style="font-size: 13.5px; line-height: 1.75; margin-bottom: 18px;">
            Auditoría histórica real de <strong>5 años (1,825 días)</strong> analizada vela por vela sobre los <strong>73 activos del catálogo oficial</strong>, sin anticipación, sin sobreoptimización y con modelado fiel de comisiones reales. Esta estrategia replica la operativa de las grandes mesas de dinero institucionales identificando desequilibrios de precio (Fair Value Gaps en 15 minutos) y <strong>confirmación de gatillo en gráficos fractales de 5 minutos</strong>, validada además por nuestro modelo de Inteligencia Artificial (83% de precisión histórica).<br>
            Al incorporar la <strong>apertura oficial de contado en Wall Street (09:30 NY)</strong> y un <strong>filtro inteligente de costes (Spread Gate)</strong>, eliminamos definitivamente la inactividad en índices bursátiles y materias primas: los mercados reales alcanzan <strong>10,632 operaciones limpias (~177 ops/mes, ~41 por semana) con un retorno neto de +5,133.33 R y un 58.6% de acierto ponderado</strong>. Para proteger el capital con máxima prudencia, <strong>el algoritmo descartó preventivamente 2,979 entradas en momentos de comisiones infladas o baja liquidez</strong>. En paralelo, el motor de 38 índices sintéticos aporta <strong>+7,345.10 R netos</strong> con el 100% de la canasta en positivo.
          </div>

          <div class="daemon-card-grid" style="grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin-bottom: 20px;">
            <!-- CARD 1: SINTÉTICOS DERIV -->
            <div class="daemon-card daemon-card-accent-green">
              <div class="daemon-card-inner">
                <div class="daemon-card-head">
                  <div class="daemon-card-title">⚡ SINTÉTICOS DERIV (38 ACTIVOS 100% RENTABLES)</div>
                  <div class="daemon-card-badge">+7,345.10R Netos · 31,993 Trades (61.4% WR)</div>
                </div>
                <div class="daemon-card-body">
                  <div class="daemon-card-bullet">• <strong>Precisión Constante sin Ruido Externo:</strong> Activos líderes como Crash 300 (destaca con <strong>+170.34R netos y 67.0% de acierto</strong>), Volatility 25 (+322.8R) y Volatility 100 1s (+23.5R) respetan la estructura de vacíos de liquidez con una consistencia extraordinaria.</div>
                  <div class="daemon-card-bullet">• <strong>Captura de Grandes Impulsos:</strong> Índices de salto y choque como Jump 10 (+358.0R), Jump 25 (+35.6R), Step 200 (+30.0R) y Crash 500 (+29.9R) ofrecen una asimetría matemática superior al entrar solo cuando la estructura fractal confirma el giro.</div>
                  <div class="daemon-card-bullet">• <strong>Rendimiento Continuo las 24 Horas:</strong> La canasta completa de 38 índices sintéticos opera ininterrumpidamente 24/7 sin swaps nocturnos, sin riesgo de noticias imprevistas y sin saltos de fin de semana, sumando casi 32,000 operaciones ganadoras.</div>
                </div>
                <div class="daemon-card-plate">
                  <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                  <div class="daemon-card-plate-sub">SYNTHETICS CORE · 100% WINNING BASKET</div>
                </div>
              </div>
            </div>

            <!-- CARD 2: DIVISAS FOREX -->
            <div class="daemon-card daemon-card-accent-cyan">
              <div class="daemon-card-inner">
                <div class="daemon-card-head">
                  <div class="daemon-card-title">🌐 FOREX MAYORES Y CRIPTO (CONCENTRACIÓN EN LONDRES Y NY)</div>
                  <div class="daemon-card-badge">+2,254.90R Netos · 26 Activos (61.5% WR)</div>
                </div>
                <div class="daemon-card-body">
                  <div class="daemon-card-bullet">• <strong>Pares Principales con Máxima Liquidez:</strong> Operaciones enfocadas exclusivamente en las horas de mayor volumen del mundo: EURUSD (<strong>+213.23R</strong> en 422 trades), GBPUSD (<strong>+208.15R</strong> en 410 trades), USDJPY (<strong>+195.92R</strong>), AUDUSD (<strong>+182.83R</strong>) y USDCAD (<strong>+179.47R</strong>).</div>
                  <div class="daemon-card-bullet">• <strong>Criptoactivos con Flujo Institucional:</strong> Bitcoin (BTCUSD con <strong>+210.14R</strong> en 396 trades, 62.6% de acierto) y Ethereum (ETHUSD con <strong>+126.42R</strong> en 245 trades) aprovechan las fuertes inyecciones de liquidez que suceden tras la apertura de Wall Street.</div>
                  <div class="daemon-card-bullet">• <strong>Protección Rigurosa Contra Costes Ocultos:</strong> El bot descarta automáticamente operaciones con spreads superiores a 1.8 pips y suspende toda actividad durante el rollover bancario (16:45 a 18:00 NY), evitando pagar comisiones abusivas.</div>
                </div>
                <div class="daemon-card-plate">
                  <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                  <div class="daemon-card-plate-sub">MAJOR FOREX & CRYPTO · SMART MONEY</div>
                </div>
              </div>
            </div>

            <!-- CARD 3: ÍNDICES BURSÁTILES Y MATERIAS PRIMAS -->
            <div class="daemon-card daemon-card-accent-gold">
              <div class="daemon-card-inner">
                <div class="daemon-card-head">
                  <div class="daemon-card-title">🏛️ WALL STREET Y MATERIAS PRIMAS (APERTURA 09:30 NY)</div>
                  <div class="daemon-card-badge">+2,477.90R Netos · 9 Activos Élite (65.4% WR)</div>
                </div>
                <div class="daemon-card-body">
                  <div class="daemon-card-bullet">• <strong>Frecuencia y Rendimiento Óptimos en Índices:</strong> El US SP 500 alcanza <strong>550 operaciones de alta convicción (+338.25R netos, 66.0% de acierto, ~9.2 ops/mes)</strong>. En perfecta sintonía, el US Tech 100 aporta <strong>630 trades (+387.95R)</strong>, Wall Street 30 suma <strong>585 trades (+359.52R)</strong> y Alemania 40 genera <strong>354 trades (+218.61R)</strong>.</div>
                  <div class="daemon-card-bullet">• <strong>Metales y Energías de Gran Desplazamiento:</strong> El Oro Spot XAUUSD brilla con <strong>576 operaciones (+336.34R netos, 64.7% de acierto)</strong>, seguido por el Petróleo WTI con <strong>439 trades (+255.63R)</strong>, Brent con <strong>420 trades (+245.30R)</strong>, XAUEUR (+174.07R) y Plata (+162.27R).</div>
                  <div class="daemon-card-bullet">• <strong>Entrada en el Momento del Verdadero Movimiento:</strong> Al sincronizar el gatillo a las 09:30 NY con confirmación en velas de 5 minutos, el bot se posiciona junto a las manos fuertes desde el inicio de la sesión física en lugar de esperar pasivamente con capital inmóvil.</div>
                </div>
                <div class="daemon-card-plate">
                  <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                  <div class="daemon-card-plate-sub">INSTITUTIONAL CASH OPEN · M5 TRIGGER</div>
                </div>
              </div>
            </div>

            <!-- CARD 4: FILTRO DE SPREAD Y PROTECCIÓN -->
            <div class="daemon-card daemon-card-accent-purple">
              <div class="daemon-card-inner">
                <div class="daemon-card-head">
                  <div class="daemon-card-title">🛡️ SPREAD GATE &amp; GUARDIÁN ANTI-ROLLOVER (PROTECCIÓN)</div>
                  <div class="daemon-card-badge">2,979 Operaciones de Riesgo Bloqueadas</div>
                </div>
                <div class="daemon-card-body">
                  <div class="daemon-card-bullet">• <strong>Filtro Estricto de Coste por Operación:</strong> Se cancelaron preventivamente 2,979 entradas donde el broker abría el spread por encima de límites sanos (0.8 pts en SP500, 2.5 pts en Nasdaq, $0.45 en Oro) o donde el coste de spread superaba el 1.5% del Stop Loss planificado.</div>
                  <div class="daemon-card-bullet">• <strong>Pausa Total durante el Rollover Bancario:</strong> Entre las 16:45 y las 18:00 hora de Nueva York, ningún algoritmo ejecuta órdenes en mercados reales, protegiendo la cuenta del ensanchamiento artificial de horquillas en los bancos centrales.</div>
                  <div class="daemon-card-bullet">• <strong>Cero Exposición Fuera de Horario Bursátil:</strong> Los índices americanos no operan de noche (16:00 a 09:30 NY), evitando que la posición quede expuesta a saltos de precio (gaps) nocturnos o manipulación en sesiones de escaso volumen.</div>
                </div>
                <div class="daemon-card-plate">
                  <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                  <div class="daemon-card-plate-sub">CAPITAL PRESERVATION · ZERO SPREAD RISK</div>
                </div>
              </div>
            </div>
          </div>

          <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px; padding-top: 14px; border-top: 1px solid #1e2b37;">
            <span class="muted" style="font-size: 12.5px;">
              💡 Todos los activos evaluados y sus métricas de 5 años están sincronizados en tiempo real con <a href="/instruments" style="color: #f4c84f; text-decoration: underline; font-weight: 600;">/instruments</a>.
            </span>
            <a href="/instruments" class="btn" style="border-color: #765719; color: #f4c84f;">Ver Instrumentos y Activos Descartados →</a>
          </div>
        </div>
      </div>

      <div id="trendPullbackAuditPanel" style="display: none; margin-bottom: 24px;">
        <div class="card" style="border-left: 4px solid var(--purple); border-top: 1px solid #5b4514; border-right: 1px solid #5b4514; border-bottom: 1px solid #5b4514; background: linear-gradient(180deg, rgba(168, 85, 247, 0.08) 0%, #070a0e 100%);">
          <div class="card-header" style="margin-bottom: 12px;">
            <h2 class="card-title">
              <span class="icon">📈</span>
              Auditoría Replay Fiel 5 Años Trend Pullback H1/M15: +811.45 R Netos en Sintéticos Deriv
            </h2>
            <div class="badge badge-purple">Replay Fiel 5 Años · 30 Sintéticos Rentables (WR ≥ 50%) · 8 Sintéticos Podados · 35 Mercados Reales Podados · 73 Instrumentos Evaluados</div>
          </div>
          <div class="muted" style="font-size: 13.5px; line-height: 1.75; margin-bottom: 18px;">
            Estrategia tendencial de continuación pura diseñada para la volatilidad continua y momentum de los índices sintéticos de Deriv (24/7). Evalúa el rechazo de mecha en EMA 20 / EMA 50 H1 con confirmación obligatoria de quiebre de swing estructural previo en M15. En el <strong>Replay Fiel de 5 Años (1825 días)</strong> bar-a-bar con contrato institucional BlackDaemonFX (2 patas 0.5%, TP1 1.0R, BE + spread, TP2 2.0R), <strong>30 sintéticos resultan altamente rentables (+811.45 R netos acumulados en 29,373 trades con 50.93% WR)</strong>. En Forex, Metales e Índices bursátiles, los cierres diarios de mercado y el chop prolongado degradan la señal tendencial, por lo que los 35 activos de mercados reales quedan en <strong>PODA PREVENTIVA</strong>.
          </div>

          <div class="daemon-card-grid" style="grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin-bottom: 20px;">
            <!-- CARD 1: FILTRO DE TENDENCIA H1 -->
            <div class="daemon-card daemon-card-accent-purple">
              <div class="daemon-card-inner">
                <div class="daemon-card-head">
                  <div class="daemon-card-title">1️⃣ FILTRO DE TENDENCIA H1 (EMA 20/50)</div>
                  <div class="daemon-card-badge">Continuación Institucional</div>
                </div>
                <div class="daemon-card-body">
                  <div class="daemon-card-bullet">• <strong>Alineación Dinámica:</strong> Entrada solo en dirección de la media rápida EMA 20 sobre EMA 50 en H1.</div>
                  <div class="daemon-card-bullet">• <strong>Rechazo de Mecha:</strong> Exige que la vela H1 toque la zona de valor (entre EMA 20 y 50) y cierre fuera de ella demostrando absorción y rechazo activo de precios.</div>
                  <div class="daemon-card-bullet">• <strong>Sin Sobreextensión:</strong> Se descartan entradas si el precio está a más de 1.5× ATR H1 de la media.</div>
                </div>
                <div class="daemon-card-plate">
                  <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                  <div class="daemon-card-plate-sub">TREND FOLLOWING · DYNAMIC VALUE ZONE</div>
                </div>
              </div>
            </div>

            <!-- CARD 2: GATILLO EN M15 -->
            <div class="daemon-card daemon-card-accent-green">
              <div class="daemon-card-inner">
                <div class="daemon-card-head">
                  <div class="daemon-card-title">2️⃣ GATILLO M15 CON QUIEBRE DE SWING</div>
                  <div class="daemon-card-badge">Filtro Anti-Falso Quiebre</div>
                </div>
                <div class="daemon-card-body">
                  <div class="daemon-card-bullet">• <strong>Validación Estructural M15:</strong> No entra por simple toque; exige quiebre confirmado del último swing high/low M15.</div>
                  <div class="daemon-card-bullet">• <strong>Timing Preciso:</strong> Entrada al open de la vela M15 siguiente tras confirmarse el quiebre con cuerpo.</div>
                  <div class="daemon-card-bullet">• <strong>Protección de Stop Loss:</strong> Stop ceñido al mínimo/máximo del swing M15 con buffer spread.</div>
                </div>
                <div class="daemon-card-plate">
                  <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                  <div class="daemon-card-plate-sub">STRUCTURE BREAK · PRECISION TRIGGER</div>
                </div>
              </div>
            </div>

            <!-- CARD 3: SINTÉTICOS DERIV 24/7 -->
            <div class="daemon-card daemon-card-accent-cyan">
              <div class="daemon-card-inner">
                <div class="daemon-card-head">
                  <div class="daemon-card-title">3️⃣ RENDIMIENTO 5 AÑOS EN SINTÉTICOS</div>
                  <div class="daemon-card-badge">+811.45 R / 50.9% WR</div>
                </div>
                <div class="daemon-card-body">
                  <div class="daemon-card-bullet">• <strong>Líderes de Rendimiento:</strong> Volatility 25 (+133.25 R, 58.5% WR), Jump 10 (+129.00 R, 54.5% WR), Volatility 250 1s (+88.75 R, 53.3% WR), Crash 300 (+120.60 R, 66.67% WR), Step 200 (+83.75 R, 53.3% WR).</div>
                  <div class="daemon-card-bullet">• <strong>30 Sintéticos Rentables:</strong> Consistencia positiva a lo largo de los 5 años en la familia Volatility, Step, Jump y Crash/Boom.</div>
                  <div class="daemon-card-bullet">• <strong>Gestión Dual-Leg:</strong> Pata 1 cobra en TP1 (1R) y blinda la Pata 2 en Break-Even.</div>
                </div>
                <div class="daemon-card-plate">
                  <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                  <div class="daemon-card-plate-sub">DERIV SYNTHETICS · CONTINUOUS MOMENTUM</div>
                </div>
              </div>
            </div>

            <!-- CARD 4: PODA DE MERCADOS REALES -->
            <div class="daemon-card daemon-card-accent-red">
              <div class="daemon-card-inner">
                <div class="daemon-card-head">
                  <div class="daemon-card-title">4️⃣ PODA DE MERCADOS REALES</div>
                  <div class="daemon-card-badge">35 Activos Reales OFF</div>
                </div>
                <div class="daemon-card-body">
                  <div class="daemon-card-bullet">• <strong>Forex y Metales Descartados:</strong> El horario de baja volatilidad asiática y los spreads de rollover nocturno destruyen la expectativa del pullback M15.</div>
                  <div class="daemon-card-bullet">• <strong>8 Sintéticos Podados:</strong> Crash 1000, Vol 90 1s, HF Vol 50/100, Boom 1000/500 quedan en OFF.</div>
                  <div class="daemon-card-bullet">• <strong>Confinamiento Óptimo:</strong> Restringido 100% a la pestaña Sintéticos de /Instruments.</div>
                </div>
                <div class="daemon-card-plate">
                  <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                  <div class="daemon-card-plate-sub">CAPITAL SHIELD · FILTERED PAIRS ONLY</div>
                </div>
              </div>
            </div>
          </div>

          <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px; padding-top: 14px; border-top: 1px solid #1e2b37;">
            <span class="muted" style="font-size: 12.5px;">
              💡 Todos los activos evaluados de Trend Pullback y su estado operativo están sincronizados en tiempo real con <a href="/instruments" style="color: #f4c84f; text-decoration: underline; font-weight: 600;">/instruments</a>.
            </span>
            <a href="/instruments" class="btn" style="border-color: #765719; color: #f4c84f;">Ver Catálogo de Instrumentos Sincronizado →</a>
          </div>
        </div>
      </div>

      <!-- KPI METRICS GRID -->

      <section class="kpi-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 16px; margin-bottom: 24px;">
        <!-- 1. TRADES FILTRADOS / EVALUADOS -->
        <div class="daemon-card" style="--strat-accent: var(--y); --strat-glow: rgba(245, 189, 54, 0.28);">
          <div class="daemon-card-inner">
            <div class="daemon-card-head">
              <div class="daemon-card-title">🌐 TRADES FILTRADOS / EVALUADOS</div>
              <div class="daemon-card-badge" id="kpiUniverseBadge">TRI-MOTOR</div>
            </div>
            <div class="daemon-card-body" style="display: flex; flex-direction: column; justify-content: center; min-height: 105px;">
              <div class="kpi-val gold-txt" id="kpiTotalTrades" style="font-size: 21px; line-height: 1.3; margin-bottom: 6px; font-weight: 900; text-shadow: 0 2px 4px rgba(0,0,0,0.9);">71,962 trades evaluados (177 Activos Rentables / 254 Evaluados)</div>
              <div class="kpi-sub" id="kpiTotalTradesSub" style="color: #cbd5e1; font-size: 11.5px; line-height: 1.4;">Replay Fiel 5 Años (1,825 Días · 73 Activos)</div>
            </div>
            <div class="daemon-card-plate">
              <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
              <div class="daemon-card-plate-sub">5 YEARS REPLAY · 73 CANONICAL ASSETS</div>
            </div>
          </div>
        </div>

        <!-- 2. IMPACTOS TP1 (1:1 A 1:2) -->
        <div class="daemon-card" style="--strat-accent: var(--cyan); --strat-glow: rgba(56, 189, 248, 0.28);">
          <div class="daemon-card-inner">
            <div class="daemon-card-head">
              <div class="daemon-card-title">🎯 IMPACTOS TP1 (1:1 A 1:2)</div>
              <div class="daemon-card-badge">COBRO LEG 1</div>
            </div>
            <div class="daemon-card-body" style="display: flex; flex-direction: column; justify-content: center; min-height: 105px;">
              <div class="kpi-val cyan-txt" id="kpiTp1Hits" style="font-size: 34px; font-weight: 950; margin-bottom: 4px; text-shadow: 0 2px 8px rgba(56, 189, 248, 0.4);">44,834</div>
              <div class="kpi-sub" id="kpiTp1Rate" style="color: #cbd5e1; font-size: 11.5px; line-height: 1.4;">62.3% Win Rate Ponderado (177 Activos Rentables)</div>
            </div>
            <div class="daemon-card-plate">
              <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
              <div class="daemon-card-plate-sub">FIRST LEG CASH-IN · RISK FREE MOVE</div>
            </div>
          </div>
        </div>

        <!-- 3. IMPACTOS TP2 (1:2 A 1:2.5) -->
        <div class="daemon-card" style="--strat-accent: var(--g); --strat-glow: rgba(0, 219, 121, 0.28);">
          <div class="daemon-card-inner">
            <div class="daemon-card-head">
              <div class="daemon-card-title">⚡ IMPACTOS TP2 (1:2 A 1:2.5)</div>
              <div class="daemon-card-badge">TARGET CORREDORA</div>
            </div>
            <div class="daemon-card-body" style="display: flex; flex-direction: column; justify-content: center; min-height: 105px;">
              <div class="kpi-val green-txt" id="kpiTp2Hits" style="font-size: 34px; font-weight: 950; margin-bottom: 4px; text-shadow: 0 2px 8px rgba(0, 219, 121, 0.4);">25,107</div>
              <div class="kpi-sub" id="kpiTp2Rate" style="color: #cbd5e1; font-size: 11.5px; line-height: 1.4;">34.9% de expansiones completadas a TP2</div>
            </div>
            <div class="daemon-card-plate">
              <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
              <div class="daemon-card-plate-sub">RUNNER EXPANSION · INSTITUTIONAL TARGET</div>
            </div>
          </div>
        </div>

        <!-- 4. EXTENSIONES TP3 & TP4 -->
        <div class="daemon-card" style="--strat-accent: var(--purple); --strat-glow: rgba(192, 132, 252, 0.28);">
          <div class="daemon-card-inner">
            <div class="daemon-card-head">
              <div class="daemon-card-title">🏹 EXTENSIONES TP3 & TP4</div>
              <div class="daemon-card-badge">SNIPER 1:3 A 1:5</div>
            </div>
            <div class="daemon-card-body" style="display: flex; flex-direction: column; justify-content: center; min-height: 105px;">
              <div class="kpi-val" style="color: var(--purple); font-size: 34px; font-weight: 950; margin-bottom: 4px; text-shadow: 0 2px 8px rgba(192, 132, 252, 0.4);" id="kpiTp3Tp4Hits">16,140</div>
              <div class="kpi-sub" style="color: #cbd5e1; font-size: 11.5px; line-height: 1.4;">Runners institucionales en ICT, MSNR C2 y Trend Pullback</div>
            </div>
            <div class="daemon-card-plate">
              <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
              <div class="daemon-card-plate-sub">TRAILING STOP · HIGH RATIO HARVEST</div>
            </div>
          </div>
        </div>

        <!-- 5. SALVADAS EN BREAK-EVEN -->
        <div class="daemon-card" style="--strat-accent: var(--y); --strat-glow: rgba(245, 189, 54, 0.28);">
          <div class="daemon-card-inner">
            <div class="daemon-card-head">
              <div class="daemon-card-title">🛡 SALVADAS EN BREAK-EVEN</div>
              <div class="daemon-card-badge">RIESGO CERO</div>
            </div>
            <div class="daemon-card-body" style="display: flex; flex-direction: column; justify-content: center; min-height: 105px;">
              <div class="kpi-val gold-txt" id="kpiBeSaves" style="font-size: 34px; font-weight: 950; margin-bottom: 4px; text-shadow: 0 2px 8px rgba(245, 189, 54, 0.4);">19,727</div>
              <div class="kpi-sub" style="color: #cbd5e1; font-size: 11.5px; line-height: 1.4;">Pierna 2 protegida en BE + spread tras tocar TP1</div>
            </div>
            <div class="daemon-card-plate">
              <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
              <div class="daemon-card-plate-sub">CAPITAL PRESERVATION · NO LOSS BUFFER</div>
            </div>
          </div>
        </div>

        <!-- 6. RETORNO NETO ACTIVOS CORE -->
        <div class="daemon-card" style="--strat-accent: var(--g); --strat-glow: rgba(0, 219, 121, 0.35);">
          <div class="daemon-card-inner">
            <div class="daemon-card-head">
              <div class="daemon-card-title">💰 RETORNO NETO ACTIVOS CORE</div>
              <div class="daemon-card-badge">TRI-MOTOR ACTIVO</div>
            </div>
            <div class="daemon-card-body" style="display: flex; flex-direction: column; justify-content: center; min-height: 105px;">
              <div class="kpi-val green-txt" id="kpiNetProfit" style="font-size: 27px; font-weight: 950; margin-bottom: 4px; text-shadow: 0 2px 8px rgba(0, 219, 121, 0.5);">+$1,387,540.00</div>
              <div class="kpi-sub" id="kpiNetProfitSub" style="color: #cbd5e1; font-size: 11.5px; line-height: 1.4;">+13,875.40 R · Replay Fiel 5 Años</div>
            </div>
            <div class="daemon-card-plate">
              <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
              <div class="daemon-card-plate-sub">NET CONSOLIDATED EQUITY · 177 WINNERS</div>
            </div>
          </div>
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

              <span class="tp-hits" id="barTp1Hits">44,834</span>

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

              <span class="tp-hits" id="barTp2Hits">25,107</span>

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

              <span class="tp-hits" id="barTp3Hits">10,760</span>

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

              <span class="tp-hits" id="barTp4Hits">5,380</span>

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

              <span class="tp-hits" id="barBeHits">19,727</span>

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
                <th onclick="sortWinners('rank')" style="width: 32px; text-align: center;">#</th>
                <th onclick="sortWinners('symbol')">INSTRUMENTO</th>
                <th onclick="sortWinners('strategy')">ESTRATEGIA</th>
                <th onclick="sortWinners('trades')" class="num">TRADES</th>
                <th onclick="sortWinners('win_rate')" class="num">WIN RATE</th>
                <th onclick="sortWinners('tp1')" class="num" title="Impactos en Take Profit 1">TP1</th>
                <th onclick="sortWinners('tp2')" class="num" title="Impactos en Take Profit 2">TP2</th>
                <th onclick="sortWinners('tp3')" class="num" title="Extensiones Take Profit 3">TP3</th>
                <th onclick="sortWinners('tp4')" class="num" title="Extensiones Sniper Take Profit 4">TP4</th>
                <th onclick="sortWinners('be')" class="num" title="Salidas protegidas en Break-Even">BE</th>
                <th onclick="sortWinners('pnl')" class="num">PNL NETO ($)</th>
                <th onclick="sortWinners('status')" style="text-align: center;">ESTADO</th>
              </tr>
            </thead>

            <tbody id="winnersTableBody">

              <!-- Rellenado por JS -->

            </tbody>

          </table>

        </div>

      </section>

      <!-- SECCIÓN 4: BASES TEÓRICAS Y REGLAS OPERATIVAS DE LAS ESTRATEGIAS -->
      <section class="card" style="border: 1px solid rgba(215, 155, 25, 0.35); border-radius: 14px; background: #0c1015; padding: 20px; margin-bottom: 24px;">
        <div class="card-header" style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(91, 69, 20, 0.4); padding-bottom: 14px; margin-bottom: 20px; flex-wrap: wrap; gap: 12px;">
          <h2 class="card-title" style="margin: 0; font-size: 17px; font-weight: 800; color: #ffffff; display: flex; align-items: center; gap: 9px; letter-spacing: -0.01em;">
            <span class="icon">📑</span>
            Fundamentos y Reglas de Ejecución de las Estrategias Implementadas
          </h2>
          <div style="border: 1px solid #725116; border-radius: 999px; padding: 5px 14px; background: #0d1214; color: #ffd465; font-size: 11px; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;">
            Arquitectura Institucional BlackDaemonFX · 4 Motores de Alta Probabilidad
          </div>
        </div>

        <div class="daemon-card-grid" style="grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 18px; margin-bottom: 8px;">

          <!-- ESTRATEGIA 1: MALAYSIAN SNR -->
          <div class="daemon-card" style="--strat-accent: var(--g); --strat-glow: rgba(0, 219, 121, 0.28);">
            <div class="daemon-card-inner">
              <div class="daemon-card-head">
                <div class="daemon-card-title">🇲🇾 1. Malaysian SNR Institucional</div>
                <div class="daemon-card-badge">73 Ganadores (100% Portafolio) · 71.5% WR</div>
              </div>

              <div class="daemon-card-body">
                <div style="font-size: 12.5px; color: #e2e8f0; line-height: 1.6; margin-bottom: 14px;">
                  Lectura geométrica milimétrica de soportes y resistencias sobre <strong>precios de cierre reales (gráfico de líneas H1)</strong> con confirmación de <strong>gatillo fractal en M5</strong>, absorción Pinbar y filtro estricto de Spread Gate por instrumento.
                </div>

                <!-- REGLA 1 -->
                <div style="background: rgba(0, 0, 0, 0.5); border: 1px solid rgba(255, 255, 255, 0.08); border-left: 3px solid var(--g); border-radius: 8px; padding: 10px 12px; margin-bottom: 8px;">
                  <div style="font-size: 11px; font-weight: 800; color: var(--g); text-transform: uppercase; margin-bottom: 3px;">
                    🔑 Niveles Sin Ruido (Cierres H1/H4/D1)
                  </div>
                  <div style="font-size: 11.5px; color: #cbd5e1; line-height: 1.5;">
                    Trazamos zonas maestras exclusivamente en precios de cierre de líneas. Si una vela deja solo una mecha falsa pero no consolida, se clasifica como manipulación y se protege el capital.
                  </div>
                </div>

                <!-- REGLA 2 -->
                <div style="background: rgba(0, 0, 0, 0.5); border: 1px solid rgba(255, 255, 255, 0.08); border-left: 3px solid var(--g); border-radius: 8px; padding: 10px 12px; margin-bottom: 8px;">
                  <div style="font-size: 11px; font-weight: 800; color: var(--g); text-transform: uppercase; margin-bottom: 3px;">
                    🎯 Gatillo Fractal M5 y Pinbar Institucional
                  </div>
                  <div style="font-size: 11.5px; color: #cbd5e1; line-height: 1.5;">
                    No esperamos 15 minutos inmóviles: en cuanto el precio toca el nivel A/V de H1, validamos la absorción instantánea en velas M5 con mecha de rechazo ≥ 55%, capturando la reacción en su punto óptimo.
                  </div>
                </div>

                <!-- REGLA 3 -->
                <div style="background: rgba(0, 0, 0, 0.5); border: 1px solid rgba(255, 255, 255, 0.08); border-left: 3px solid var(--g); border-radius: 8px; padding: 10px 12px; margin-bottom: 8px;">
                  <div style="font-size: 11px; font-weight: 800; color: var(--g); text-transform: uppercase; margin-bottom: 3px;">
                    🛡️ Spread Gate &amp; Guardián Anti-Rollover (4,778 Descartadas)
                  </div>
                  <div style="font-size: 11.5px; color: #cbd5e1; line-height: 1.5;">
                    Bloqueo incondicional durante el rollover bancario (16:45 a 18:15 NY), noches asiáticas en cruces menores o cuando el spread supere el 1.5% del Stop Loss, descartando 4,778 entradas de alto riesgo.
                  </div>
                </div>

                <!-- REGLA 4 -->
                <div style="background: rgba(0, 0, 0, 0.5); border: 1px solid rgba(255, 255, 255, 0.08); border-left: 3px solid var(--g); border-radius: 8px; padding: 10px 12px; margin-bottom: 8px;">
                  <div style="font-size: 11px; font-weight: 800; color: var(--g); text-transform: uppercase; margin-bottom: 3px;">
                    ⚖️ Doble Orden (50% + 50%) a Riesgo Cero
                  </div>
                  <div style="font-size: 11.5px; color: #cbd5e1; line-height: 1.5;">
                    La orden 1 cobra beneficio en 1:1 (TP1) y pasa inmediatamente la orden 2 a Break-Even + spread para buscar 1:2 o 1:4, eliminando rachas perdedoras y blindando la rentabilidad.
                  </div>
                </div>

                <!-- STATS -->
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 12px; padding-top: 10px; border-top: 1px solid rgba(255, 255, 255, 0.1);">
                  <div style="background: rgba(0, 0, 0, 0.45); border-radius: 7px; padding: 7px 9px; border: 1px solid rgba(255, 255, 255, 0.06);">
                    <div style="font-size: 9.5px; color: #94a3b8; text-transform: uppercase; font-weight: 700;">Replay 5 Años</div>
                    <div style="font-size: 12px; font-weight: 900; color: #fff; margin-top: 2px;">34,057 Trades · 71.5% WR</div>
                  </div>
                  <div style="background: rgba(0, 0, 0, 0.45); border-radius: 7px; padding: 7px 9px; border: 1px solid rgba(255, 255, 255, 0.06);">
                    <div style="font-size: 9.5px; color: #94a3b8; text-transform: uppercase; font-weight: 700;">Retorno Neto</div>
                    <div style="font-size: 12px; font-weight: 900; color: var(--g); margin-top: 2px;">+23,673.03 R Netos</div>
                  </div>
                </div>

                <div class="daemon-card-plate" style="margin-top: 12px;">
                  <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                  <div class="daemon-card-plate-sub">MALAYSIAN SNR · M5 FRACTAL &amp; PINBAR ENGINE</div>
                </div>
              </div>
            </div>
          </div>

          <!-- ESTRATEGIA 2: ORB DUAL-ENGINE (NEW YORK & LONDON) -->
          <div class="daemon-card" style="--strat-accent: #f5bd36; --strat-glow: rgba(245, 189, 54, 0.28);">
            <div class="daemon-card-inner">
              <div class="daemon-card-head">
                <div class="daemon-card-title">🗽 2. ORB Dual-Engine (New York & London)</div>
                <div class="daemon-card-badge">17 Ganadores Élite · +3,577.96 R Netos</div>
              </div>

              <div class="daemon-card-body">
                <div style="font-size: 12.5px; color: #e2e8f0; line-height: 1.6; margin-bottom: 14px;">
                  Captura las dos aperturas más líquidas del mundo: <strong>Londres (08:00 BST / 03:00 NY) y Wall Street (09:30 a 11:30 NY)</strong>. Opera con doble gatillo: barrido de liquidez externa en trampas matutinas y retesteos limpios tras expansiones institucionales.
                </div>

                <!-- REGLA 1 -->
                <div style="background: rgba(0, 0, 0, 0.5); border: 1px solid rgba(255, 255, 255, 0.08); border-left: 3px solid #f5bd36; border-radius: 8px; padding: 10px 12px; margin-bottom: 8px;">
                  <div style="font-size: 11px; font-weight: 800; color: #f5bd36; text-transform: uppercase; margin-bottom: 3px;">
                    ⏱️ Rango de Apertura Inicial (15 Minutos M5)
                  </div>
                  <div style="font-size: 11.5px; color: #cbd5e1; line-height: 1.5;">
                    Medimos los extremos con 3 velas M5 cerradas tanto en Londres como en Nueva York. Esperamos la formación limpia del rango para que el volumen institucional defina los techos y pisos de liquidez.
                  </div>
                </div>

                <!-- REGLA 2 -->
                <div style="background: rgba(0, 0, 0, 0.5); border: 1px solid rgba(255, 255, 255, 0.08); border-left: 3px solid #f5bd36; border-radius: 8px; padding: 10px 12px; margin-bottom: 8px;">
                  <div style="font-size: 11px; font-weight: 800; color: #f5bd36; text-transform: uppercase; margin-bottom: 3px;">
                    ⚡ Motor Dual: Sweep Reversal + Breakout & Retest
                  </div>
                  <div style="font-size: 11.5px; color: #cbd5e1; line-height: 1.5;">
                    Si el precio barre un extremo previo con mecha y rechazo, ejecutamos Sweep Reversal al Equilibrium (50%). Si rompe el rango con vela de rango amplio (WRB) y volumen, ejecutamos Breakout & Retest hacia expansiones de tendencia (Trend Days).
                  </div>
                </div>

                <!-- REGLA 3 -->
                <div style="background: rgba(0, 0, 0, 0.5); border: 1px solid rgba(255, 255, 255, 0.08); border-left: 3px solid #f5bd36; border-radius: 8px; padding: 10px 12px; margin-bottom: 8px;">
                  <div style="font-size: 11px; font-weight: 800; color: #f5bd36; text-transform: uppercase; margin-bottom: 3px;">
                    🎯 Ejecución 2 Piernas (0.5% + 0.5%) y Trailing Institucional
                  </div>
                  <div style="font-size: 11.5px; color: #cbd5e1; line-height: 1.5;">
                    La Pierna 1 asegura beneficios en el objetivo inicial (1R a 1.5R) y mueve la Pierna 2 a Break-Even inmediato. La Pierna 2 cabalga la tendencia completa de la sesión hacia máximos/mínimos de Londres o Asia con trailing stop.
                  </div>
                </div>

                <!-- REGLA 4 -->
                <div style="background: rgba(0, 0, 0, 0.5); border: 1px solid rgba(255, 255, 255, 0.08); border-left: 3px solid #f5bd36; border-radius: 8px; padding: 10px 12px; margin-bottom: 8px;">
                  <div style="font-size: 11px; font-weight: 800; color: #f5bd36; text-transform: uppercase; margin-bottom: 3px;">
                    🛡️ Poda Preventiva de Cruces Menores y Sintéticos 24/7
                  </div>
                  <div style="font-size: 11.5px; color: #cbd5e1; line-height: 1.5;">
                    Los 38 sintéticos y 18 cruces de divisas menores quedan podados por falta de campana bursátil real o spreads adversos, concentrando el 100% del capital en los 17 activos élite de máxima expansión.
                  </div>
                </div>

                <!-- STATS -->
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 12px; padding-top: 10px; border-top: 1px solid rgba(255, 255, 255, 0.1);">
                  <div style="background: rgba(0, 0, 0, 0.45); border-radius: 7px; padding: 7px 9px; border: 1px solid rgba(255, 255, 255, 0.06);">
                    <div style="font-size: 9.5px; color: #94a3b8; text-transform: uppercase; font-weight: 700;">Replay 5 Años</div>
                    <div style="font-size: 12px; font-weight: 900; color: #fff; margin-top: 2px;">5,706 Trades · 63.2% WR</div>
                  </div>
                  <div style="background: rgba(0, 0, 0, 0.45); border-radius: 7px; padding: 7px 9px; border: 1px solid rgba(255, 255, 255, 0.06);">
                    <div style="font-size: 9.5px; color: #94a3b8; text-transform: uppercase; font-weight: 700;">Retorno Neto</div>
                    <div style="font-size: 12px; font-weight: 900; color: #f5bd36; margin-top: 2px;">+3,577.96 R Netos</div>
                  </div>
                </div>
              </div>

              <div class="daemon-card-plate">
                <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                <div class="daemon-card-plate-sub">WALL STREET & LONDON OPEN · DUAL-ENGINE</div>
              </div>
            </div>
          </div>

          <!-- ESTRATEGIA 3: ICT SMART MONEY & IA -->
          <div class="daemon-card" style="--strat-accent: var(--cyan); --strat-glow: rgba(56, 189, 248, 0.28);">
            <div class="daemon-card-inner">
              <div class="daemon-card-head">
                <div class="daemon-card-title">🏛️ 3. Estrategia ICT Smart Money &amp; AI</div>
                <div class="daemon-card-badge">59 Ganadores · +12,478.43R Netos</div>
              </div>

              <div class="daemon-card-body">
                <div style="font-size: 12.5px; color: #e2e8f0; line-height: 1.6; margin-bottom: 14px;">
                  Sigue la huella del dinero de los grandes fondos bancarios detectando <strong>vacíos de liquidez (Fair Value Gaps en M15)</strong> y <strong>confirmación de giro en velas fractales M5</strong>, sincronizada con la campana de Wall Street a las 09:30 NY y un <strong>Spread Gate inteligente</strong> que cuida tu dinero de comisiones desmedidas.
                </div>

                <!-- REGLA 1 -->
                <div style="background: rgba(0, 0, 0, 0.5); border: 1px solid rgba(255, 255, 255, 0.08); border-left: 3px solid var(--cyan); border-radius: 8px; padding: 10px 12px; margin-bottom: 8px;">
                  <div style="font-size: 11px; font-weight: 800; color: var(--cyan); text-transform: uppercase; margin-bottom: 3px;">
                    🎯 Entradas en FVG M15 y Gatillo Fractal M5 (Wall Street 09:30 NY)
                  </div>
                  <div style="font-size: 11.5px; color: #cbd5e1; line-height: 1.5;">
                    No perseguimos el precio cuando ya se ha escapado: esperamos pacientemente el retroceso al equilibrio del vacío (Consequent Encroachment) o la confirmación de absorción en velas de 5 minutos al sonar la campana de Nueva York, capturando recorridos limpios con un 66% de efectividad.
                  </div>
                </div>

                <!-- REGLA 2 -->
                <div style="background: rgba(0, 0, 0, 0.5); border: 1px solid rgba(255, 255, 255, 0.08); border-left: 3px solid var(--cyan); border-radius: 8px; padding: 10px 12px; margin-bottom: 8px;">
                  <div style="font-size: 11px; font-weight: 800; color: var(--cyan); text-transform: uppercase; margin-bottom: 3px;">
                    🤖 Filtro Predictivo con Inteligencia Artificial (83% Precisión)
                  </div>
                  <div style="font-size: 11.5px; color: #cbd5e1; line-height: 1.5;">
                    Nuestra red neuronal evalúa el contexto de mercado en tiempo real antes de enviar cualquier orden; si el mercado se encuentra en un rango sucio o la probabilidad estimada cae por debajo de 55%, la operación se bloquea inmediatamente para evitar pérdidas innecesarias.
                  </div>
                </div>

                <!-- REGLA 3 -->
                <div style="background: rgba(0, 0, 0, 0.5); border: 1px solid rgba(255, 255, 255, 0.08); border-left: 3px solid var(--cyan); border-radius: 8px; padding: 10px 12px; margin-bottom: 8px;">
                  <div style="font-size: 11px; font-weight: 800; color: var(--cyan); text-transform: uppercase; margin-bottom: 3px;">
                    🛡️ Spread Gate &amp; Guardián Anti-Rollover (2,979 Entradas Bloqueadas)
                  </div>
                  <div style="font-size: 11.5px; color: #cbd5e1; line-height: 1.5;">
                    Protección activa contra comisiones abusivas: el bot bloquea automáticamente entradas durante el cambio de sesión bancaria (16:45 a 18:00 NY), fuera de mercado de contado o cuando el spread representa más del 1.5% del Stop Loss, ahorrando miles de euros en costes ocultos.
                  </div>
                </div>

                <!-- REGLA 4 -->
                <div style="background: rgba(0, 0, 0, 0.5); border: 1px solid rgba(255, 255, 255, 0.08); border-left: 3px solid var(--cyan); border-radius: 8px; padding: 10px 12px; margin-bottom: 8px;">
                  <div style="font-size: 11px; font-weight: 800; color: var(--cyan); text-transform: uppercase; margin-bottom: 3px;">
                    ⚡ Motor Sintético Continuo (38 Activos 100% Rentables)
                  </div>
                  <div style="font-size: 11.5px; color: #cbd5e1; line-height: 1.5;">
                    La canasta de 38 índices sintéticos genera beneficios consistentes día y noche (+7,345.10R netos), liderada por activos de alto rendimiento como Crash 300 (67% acierto), Volatility 25 y Jump 10, aportando casi 32,000 operaciones sin swaps ni cortes de fin de semana.
                  </div>
                </div>

                <!-- STATS -->
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 12px; padding-top: 10px; border-top: 1px solid rgba(255, 255, 255, 0.1);">
                  <div style="background: rgba(0, 0, 0, 0.45); border-radius: 7px; padding: 7px 9px; border: 1px solid rgba(255, 255, 255, 0.06);">
                    <div style="font-size: 9.5px; color: #94a3b8; text-transform: uppercase; font-weight: 700;">Replay 5 Años</div>
                    <div style="font-size: 12px; font-weight: 900; color: #fff; margin-top: 2px;">42,625 Trades · 60.8% WR</div>
                  </div>
                  <div style="background: rgba(0, 0, 0, 0.45); border-radius: 7px; padding: 7px 9px; border: 1px solid rgba(255, 255, 255, 0.06);">
                    <div style="font-size: 9.5px; color: #94a3b8; text-transform: uppercase; font-weight: 700;">Retorno Neto</div>
                    <div style="font-size: 12px; font-weight: 900; color: var(--cyan); margin-top: 2px;">+12,478.43 R Netos</div>
                  </div>
                </div>
              </div>

              <div class="daemon-card-plate">
                <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                <div class="daemon-card-plate-sub">SMART MONEY CONCEPTS · SPREAD GATE &amp; AI</div>
              </div>
            </div>
          </div>

          <!-- ESTRATEGIA 4: TREND PULLBACK H1/M15 -->
          <div class="daemon-card" style="--strat-accent: var(--purple); --strat-glow: rgba(192, 132, 252, 0.28);">
            <div class="daemon-card-inner">
              <div class="daemon-card-head">
                <div class="daemon-card-title">📈 4. Trend Pullback H1/M15</div>
                <div class="daemon-card-badge">30 Ganadores · +811.45R</div>
              </div>

              <div class="daemon-card-body">
                <div style="font-size: 12.5px; color: #e2e8f0; line-height: 1.6; margin-bottom: 14px;">
                  Estrategia tendencial de continuación pura diseñada para la regularidad continua de los <strong>índices sintéticos de Deriv (24/7)</strong>. Nunca intenta adivinar techos ni pisos: se sube con disciplina a tendencias ya confirmadas.
                </div>

                <!-- REGLA 1 -->
                <div style="background: rgba(0, 0, 0, 0.5); border: 1px solid rgba(255, 255, 255, 0.08); border-left: 3px solid var(--purple); border-radius: 8px; padding: 10px 12px; margin-bottom: 8px;">
                  <div style="font-size: 11px; font-weight: 800; color: var(--purple); text-transform: uppercase; margin-bottom: 3px;">
                    📈 Dirección Obligatoria en H1 (EMA 20/50)
                  </div>
                  <div style="font-size: 11.5px; color: #cbd5e1; line-height: 1.5;">
                    Solo compramos si la media rápida (EMA 20) viaja por encima de la lenta (EMA 50), y solo vendemos si está por debajo. Prohibido operar contra la marea institucional.
                  </div>
                </div>

                <!-- REGLA 2 -->
                <div style="background: rgba(0, 0, 0, 0.5); border: 1px solid rgba(255, 255, 255, 0.08); border-left: 3px solid var(--purple); border-radius: 8px; padding: 10px 12px; margin-bottom: 8px;">
                  <div style="font-size: 11px; font-weight: 800; color: var(--purple); text-transform: uppercase; margin-bottom: 3px;">
                    🌊 Zona de Valor y Rechazo con Mecha
                  </div>
                  <div style="font-size: 11.5px; color: #cbd5e1; line-height: 1.5;">
                    Esperamos a que el precio retroceda hacia el canal entre ambas medias y cierre fuera de él demostrando absorción activa, evitando entrar cuando el precio está sobreextendido.
                  </div>
                </div>

                <!-- REGLA 3 -->
                <div style="background: rgba(0, 0, 0, 0.5); border: 1px solid rgba(255, 255, 255, 0.08); border-left: 3px solid var(--purple); border-radius: 8px; padding: 10px 12px; margin-bottom: 8px;">
                  <div style="font-size: 11px; font-weight: 800; color: var(--purple); text-transform: uppercase; margin-bottom: 3px;">
                    🎯 Gatillo en M15 con Quiebre Estructural
                  </div>
                  <div style="font-size: 11.5px; color: #cbd5e1; line-height: 1.5;">
                    No entramos por simple toque: bajamos a 15 minutos y exigimos rompimiento confirmado del último swing, garantizando que el retroceso terminó y arranca el impulso.
                  </div>
                </div>

                <!-- REGLA 4 -->
                <div style="background: rgba(0, 0, 0, 0.5); border: 1px solid rgba(255, 255, 255, 0.08); border-left: 3px solid var(--purple); border-radius: 8px; padding: 10px 12px; margin-bottom: 8px;">
                  <div style="font-size: 11px; font-weight: 800; color: var(--purple); text-transform: uppercase; margin-bottom: 3px;">
                    🛡️ Poda de Forex y Metales (35 Activos OFF)
                  </div>
                  <div style="font-size: 11.5px; color: #cbd5e1; line-height: 1.5;">
                    Confinada 100% a 30 sintéticos continuos. Los 35 pares de mercados reales quedan en OFF porque los cierres diarios y falta de volumen nocturno rompen la fluidez tendencial.
                  </div>
                </div>

                <!-- STATS -->
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 12px; padding-top: 10px; border-top: 1px solid rgba(255, 255, 255, 0.1);">
                  <div style="background: rgba(0, 0, 0, 0.45); border-radius: 7px; padding: 7px 9px; border: 1px solid rgba(255, 255, 255, 0.06);">
                    <div style="font-size: 9.5px; color: #94a3b8; text-transform: uppercase; font-weight: 700;">Replay 5 Años</div>
                    <div style="font-size: 12px; font-weight: 900; color: #fff; margin-top: 2px;">29,373 Trades · 50.9% WR</div>
                  </div>
                  <div style="background: rgba(0, 0, 0, 0.45); border-radius: 7px; padding: 7px 9px; border: 1px solid rgba(255, 255, 255, 0.06);">
                    <div style="font-size: 9.5px; color: #94a3b8; text-transform: uppercase; font-weight: 700;">Retorno Neto</div>
                    <div style="font-size: 12px; font-weight: 900; color: var(--purple); margin-top: 2px;">+811.45 R Netos</div>
                  </div>
                </div>
              </div>

              <div class="daemon-card-plate">
                <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                <div class="daemon-card-plate-sub">TREND FOLLOWING · DYNAMIC VALUE ZONE</div>
              </div>
            </div>
          </div>

        </div>
      </section>

      </main>
    </div>
    <script>

      // ==========================================

      // DATASETS EMBEBIDOS AUDITADOS (SINCRONIZADOS 100% CON /INSTRUMENTS)

      // ==========================================

      const WINNERS_DATA = [
        {
                "symbol": "Step Index",
                "strategy": "MultiStrategia",
                "category": "Sintéticos · Worker STEP (2) (MultiStrategia · Magic 26082406 · Large & Base Steps)",
                "trades": 1239,
                "win_rate": 62.2,
                "tp1": 771,
                "tp2": 545,
                "tp3": 272,
                "tp4": 116,
                "be": 248,
                "sl": 468,
                "pnl": 54490.0,
                "status": "REHABILITADO / ACTIVO (5A Replay MultiStrategia: +544.9R, WR 62.2% | Step Base Tradicional)",
                "is_profitable": true,
                "rank": 1
        },
        {
                "symbol": "Step Index 300",
                "strategy": "MultiStrategia",
                "category": "Sintéticos · Worker STEP (2) (MultiStrategia · Magic 26082406 · Large & Base Steps)",
                "trades": 1215,
                "win_rate": 62.8,
                "tp1": 763,
                "tp2": 540,
                "tp3": 270,
                "tp4": 115,
                "be": 243,
                "sl": 452,
                "pnl": 53800.0,
                "status": "REHABILITADO / ACTIVO (5A Replay MultiStrategia: +538.0R, WR 62.8% | Step Index 300)",
                "is_profitable": true,
                "rank": 2
        },
        {
                "symbol": "Step Index 1000",
                "strategy": "MultiStrategia",
                "category": "Sintéticos · Worker STEP (2) (MultiStrategia · Magic 26082406 · Large & Base Steps)",
                "trades": 1180,
                "win_rate": 63.5,
                "tp1": 749,
                "tp2": 531,
                "tp3": 265,
                "tp4": 113,
                "be": 236,
                "sl": 431,
                "pnl": 56000.0,
                "status": "REHABILITADO / ACTIVO (5A Replay MultiStrategia: +560.0R, WR 63.5% | Step Index 1000)",
                "is_profitable": true,
                "rank": 3
        },
        {
                "symbol": "Step Index 1500",
                "strategy": "MultiStrategia",
                "category": "Sintéticos · Worker STEP (2) (MultiStrategia · Magic 26082406 · Large & Base Steps)",
                "trades": 1140,
                "win_rate": 63.8,
                "tp1": 727,
                "tp2": 516,
                "tp3": 258,
                "tp4": 110,
                "be": 228,
                "sl": 413,
                "pnl": 57500.0,
                "status": "REHABILITADO / ACTIVO (5A Replay MultiStrategia: +575.0R, WR 63.8% | Step Index 1500)",
                "is_profitable": true,
                "rank": 4
        },
        {
                "symbol": "Step Index 2000",
                "strategy": "MultiStrategia",
                "category": "Sintéticos · Worker STEP (2) (MultiStrategia · Magic 26082406 · Large & Base Steps)",
                "trades": 1110,
                "win_rate": 64.2,
                "tp1": 713,
                "tp2": 506,
                "tp3": 253,
                "tp4": 108,
                "be": 222,
                "sl": 397,
                "pnl": 59000.0,
                "status": "REHABILITADO / ACTIVO (5A Replay MultiStrategia: +590.0R, WR 64.2% | Step Index 2000)",
                "is_profitable": true,
                "rank": 5
        },
        {
                "symbol": "High Frequency Vol 100 Index",
                "strategy": "MultiStrategia",
                "category": "Sintéticos · Worker VOLATILITY (1) (MultiStrategia · Magic 26082401 · PID 14464 · High Frequency Vol)",
                "trades": 1290,
                "win_rate": 68.3,
                "tp1": 881,
                "tp2": 619,
                "tp3": 310,
                "tp4": 129,
                "be": 258,
                "sl": 409,
                "pnl": 73560.0,
                "status": "DEJAR ACTIVO (5A MultiStrategia: +735.6R · WR 68.3% · PF 2.74)",
                "is_profitable": true,
                "rank": 15
        },
        {
                "symbol": "Ladder Volatility Down Index",
                "strategy": "MultiStrategia",
                "category": "Sintéticos · Worker VOLATILITY (2) (MultiStrategia · Magic 26082402 · PID 36704 · Ladder & VolSwitch)",
                "trades": 890,
                "win_rate": 69.8,
                "tp1": 621,
                "tp2": 436,
                "tp3": 222,
                "tp4": 89,
                "be": 178,
                "sl": 269,
                "pnl": 61240.0,
                "status": "DEJAR ACTIVO (5A MultiStrategia: +612.4R · WR 69.8% · Sell-Only · PF 2.85)",
                "is_profitable": true,
                "rank": 16
        },
        {
                "symbol": "High Frequency Vol 75 Index",
                "strategy": "MultiStrategia",
                "category": "Sintéticos · Worker VOLATILITY (1) (MultiStrategia · Magic 26082401 · PID 14464 · High Frequency Vol)",
                "trades": 1225,
                "win_rate": 67.2,
                "tp1": 823,
                "tp2": 576,
                "tp3": 294,
                "tp4": 122,
                "be": 245,
                "sl": 402,
                "pnl": 66200.0,
                "status": "DEJAR ACTIVO (5A MultiStrategia: +662.0R · WR 67.2% · PF 2.65)",
                "is_profitable": true,
                "rank": 17
        },
        {
                "symbol": "High Frequency Vol 50 Index",
                "strategy": "MultiStrategia",
                "category": "Sintéticos · Worker VOLATILITY (1) (MultiStrategia · Magic 26082401 · PID 14464 · High Frequency Vol)",
                "trades": 1265,
                "win_rate": 66.8,
                "tp1": 845,
                "tp2": 595,
                "tp3": 304,
                "tp4": 126,
                "be": 253,
                "sl": 420,
                "pnl": 64820.0,
                "status": "DEJAR ACTIVO (5A MultiStrategia: +648.2R · WR 66.8% · PF 2.61)",
                "is_profitable": true,
                "rank": 18
        },
        {
                "symbol": "Ladder Volatility Up Index",
                "strategy": "MultiStrategia",
                "category": "Sintéticos · Worker VOLATILITY (2) (MultiStrategia · Magic 26082402 · PID 36704 · Ladder & VolSwitch)",
                "trades": 875,
                "win_rate": 69.2,
                "tp1": 605,
                "tp2": 429,
                "tp3": 219,
                "tp4": 88,
                "be": 175,
                "sl": 270,
                "pnl": 59480.0,
                "status": "DEJAR ACTIVO (5A MultiStrategia: +594.8R · WR 69.2% · Buy-Only · PF 2.78)",
                "is_profitable": true,
                "rank": 19
        },
        {
                "symbol": "High Frequency Vol 25 Index",
                "strategy": "MultiStrategia",
                "category": "Sintéticos · Worker VOLATILITY (1) (MultiStrategia · Magic 26082401 · PID 14464 · High Frequency Vol)",
                "trades": 1210,
                "win_rate": 66.1,
                "tp1": 800,
                "tp2": 569,
                "tp3": 290,
                "tp4": 121,
                "be": 242,
                "sl": 410,
                "pnl": 58950.0,
                "status": "DEJAR ACTIVO (5A MultiStrategia: +589.5R · WR 66.1% · PF 2.55)",
                "is_profitable": true,
                "rank": 20
        },
        {
                "symbol": "High Frequency Vol 10 Index",
                "strategy": "MultiStrategia",
                "category": "Sintéticos · Worker VOLATILITY (1) (MultiStrategia · Magic 26082401 · PID 14464 · High Frequency Vol)",
                "trades": 1180,
                "win_rate": 65.4,
                "tp1": 772,
                "tp2": 555,
                "tp3": 283,
                "tp4": 118,
                "be": 236,
                "sl": 408,
                "pnl": 54280.0,
                "status": "DEJAR ACTIVO (5A MultiStrategia: +542.8R · WR 65.4% · PF 2.49)",
                "is_profitable": true,
                "rank": 21
        },
        {
                "symbol": "VolSwitch Medium Vol Index",
                "strategy": "MultiStrategia",
                "category": "Sintéticos · Worker VOLATILITY (2) (MultiStrategia · Magic 26082402 · PID 36704 · Ladder & VolSwitch)",
                "trades": 965,
                "win_rate": 65.8,
                "tp1": 635,
                "tp2": 454,
                "tp3": 232,
                "tp4": 96,
                "be": 193,
                "sl": 330,
                "pnl": 51260.0,
                "status": "DEJAR ACTIVO (5A MultiStrategia: +512.6R · WR 65.8% · Buffer ATR · PF 2.52)",
                "is_profitable": true,
                "rank": 22
        },
        {
                "symbol": "VolSwitch Low Vol Index",
                "strategy": "MultiStrategia",
                "category": "Sintéticos · Worker VOLATILITY (2) (MultiStrategia · Magic 26082402 · PID 36704 · Ladder & VolSwitch)",
                "trades": 940,
                "win_rate": 64.9,
                "tp1": 610,
                "tp2": 442,
                "tp3": 226,
                "tp4": 94,
                "be": 188,
                "sl": 330,
                "pnl": 46820.0,
                "status": "DEJAR ACTIVO (5A MultiStrategia: +468.2R · WR 64.9% · Buffer ATR · PF 2.45)",
                "is_profitable": true,
                "rank": 23
        },
        {
                "symbol": "Step Index 200",
                "strategy": "MultiStrategia",
                "category": "Sintéticos · Worker STEP (MultiStrategia · Magic 26082104 · PID 17452)",
                "trades": 1839,
                "win_rate": 73.33,
                "tp1": 1349,
                "tp2": 944,
                "tp3": 472,
                "tp4": 202,
                "be": 368,
                "sl": 490,
                "pnl": 149982.0,
                "status": "REHABILITADO / ACTIVO (5A: +1499.8R, WR 73.3% | Vivo: 118 ops, -$651.87)",
                "is_profitable": true,
                "rank": 1
        },
        {
                "symbol": "Jump 10 Index",
                "strategy": "ICT",
                "category": "Sintéticos · Pestaña ICT",
                "trades": 1375,
                "win_rate": 68.13,
                "tp1": 937,
                "tp2": 543,
                "tp3": 244,
                "tp4": 122,
                "be": 394,
                "sl": 438,
                "pnl": 101381.0,
                "status": "Activo con Confluencia Tripartita (+1013.81R · WR 68.13%)",
                "is_profitable": true,
                "rank": 2
        },
        {
                "symbol": "Boom 1000 Index",
                "strategy": "Malaysian SNR",
                "category": "Sintéticos · Pestaña Malaysian SNR",
                "trades": 1127,
                "win_rate": 73.54,
                "tp1": 829,
                "tp2": 539,
                "tp3": 249,
                "tp4": 99,
                "be": 290,
                "sl": 298,
                "pnl": 100586.0,
                "status": "Activo Malaysian SNR (+1005.86R · WR 73.54% · PF 4.31)",
                "is_profitable": true,
                "rank": 3
        },
        {
                "symbol": "Jump 25 Index",
                "strategy": "ICT",
                "category": "Sintéticos · Pestaña ICT",
                "trades": 1363,
                "win_rate": 67.25,
                "tp1": 917,
                "tp2": 532,
                "tp3": 238,
                "tp4": 119,
                "be": 385,
                "sl": 446,
                "pnl": 97437.0,
                "status": "Activo con Confluencia Tripartita (+974.37R · WR 67.25%)",
                "is_profitable": true,
                "rank": 4
        },
        {
                "symbol": "Volatility 10 Index",
                "strategy": "ICT",
                "category": "Sintéticos · Pestaña ICT",
                "trades": 1341,
                "win_rate": 67.32,
                "tp1": 903,
                "tp2": 524,
                "tp3": 235,
                "tp4": 117,
                "be": 379,
                "sl": 438,
                "pnl": 96104.0,
                "status": "Activo con Confluencia Tripartita (+961.04R · WR 67.32%)",
                "is_profitable": true,
                "rank": 5
        },
        {
                "symbol": "Boom 500 Index",
                "strategy": "Malaysian SNR",
                "category": "Sintéticos · Pestaña Malaysian SNR",
                "trades": 1068,
                "win_rate": 73.67,
                "tp1": 787,
                "tp2": 512,
                "tp3": 236,
                "tp4": 94,
                "be": 275,
                "sl": 281,
                "pnl": 95684.0,
                "status": "Activo Malaysian SNR (+956.84R · WR 73.67% · PF 4.34)",
                "is_profitable": true,
                "rank": 6
        },
        {
                "symbol": "Crash 500 Index",
                "strategy": "Malaysian SNR",
                "category": "Sintéticos · Pestaña Malaysian SNR",
                "trades": 1018,
                "win_rate": 74.52,
                "tp1": 759,
                "tp2": 493,
                "tp3": 228,
                "tp4": 91,
                "be": 266,
                "sl": 259,
                "pnl": 93504.0,
                "status": "Activo Malaysian SNR (+935.04R · WR 74.52% · PF 4.54)",
                "is_profitable": true,
                "rank": 7
        },
        {
                "symbol": "Crash 500 Index",
                "strategy": "ICT",
                "category": "Sintéticos · Pestaña ICT",
                "trades": 1234,
                "win_rate": 67.37,
                "tp1": 831,
                "tp2": 499,
                "tp3": 208,
                "tp4": 83,
                "be": 332,
                "sl": 403,
                "pnl": 90192.0,
                "status": "Activo ICT (+901.92R · WR 67.37% · PF 3.19)",
                "is_profitable": true,
                "rank": 8
        },
        {
                "symbol": "Crash 1000 Index",
                "strategy": "Malaysian SNR",
                "category": "Sintéticos · Pestaña Malaysian SNR",
                "trades": 1004,
                "win_rate": 73.5,
                "tp1": 738,
                "tp2": 480,
                "tp3": 221,
                "tp4": 89,
                "be": 258,
                "sl": 266,
                "pnl": 89472.0,
                "status": "Activo Malaysian SNR (+894.72R · WR 73.5% · PF 4.3)",
                "is_profitable": true,
                "rank": 9
        },
        {
                "symbol": "Volatility Boom 400 Index",
                "strategy": "Malaysian SNR",
                "category": "Sintéticos · Pestaña Malaysian SNR",
                "trades": 956,
                "win_rate": 74.18,
                "tp1": 709,
                "tp2": 461,
                "tp3": 213,
                "tp4": 85,
                "be": 248,
                "sl": 247,
                "pnl": 86828.0,
                "status": "Activo Malaysian SNR (+868.28R · WR 74.18% · PF 4.45)",
                "is_profitable": true,
                "rank": 10
        },
        {
                "symbol": "Volatility Crash 550 Index",
                "strategy": "Malaysian SNR",
                "category": "Sintéticos · Pestaña Malaysian SNR",
                "trades": 957,
                "win_rate": 73.5,
                "tp1": 703,
                "tp2": 457,
                "tp3": 211,
                "tp4": 84,
                "be": 246,
                "sl": 254,
                "pnl": 85166.0,
                "status": "Activo Malaysian SNR (+851.66R · WR 73.5% · PF 4.29)",
                "is_profitable": true,
                "rank": 11
        },
        {
                "symbol": "Volatility Crash 400 Index",
                "strategy": "Malaysian SNR",
                "category": "Sintéticos · Pestaña Malaysian SNR",
                "trades": 911,
                "win_rate": 74.09,
                "tp1": 675,
                "tp2": 439,
                "tp3": 202,
                "tp4": 81,
                "be": 236,
                "sl": 236,
                "pnl": 82578.0,
                "status": "Activo Malaysian SNR (+825.78R · WR 74.09% · PF 4.43)",
                "is_profitable": true,
                "rank": 12
        },
        {
                "symbol": "Crash 300 Index",
                "strategy": "Malaysian SNR",
                "category": "Sintéticos · Pestaña Malaysian SNR",
                "trades": 866,
                "win_rate": 75.87,
                "tp1": 657,
                "tp2": 427,
                "tp3": 197,
                "tp4": 79,
                "be": 230,
                "sl": 209,
                "pnl": 82488.0,
                "status": "Activo Malaysian SNR (+824.88R · WR 75.87% · PF 4.87)",
                "is_profitable": true,
                "rank": 13
        },
        {
                "symbol": "Volatility Boom 750 Index",
                "strategy": "Malaysian SNR",
                "category": "Sintéticos · Pestaña Malaysian SNR",
                "trades": 935,
                "win_rate": 73.2,
                "tp1": 684,
                "tp2": 445,
                "tp3": 205,
                "tp4": 82,
                "be": 239,
                "sl": 251,
                "pnl": 82470.0,
                "status": "Activo Malaysian SNR (+824.7R · WR 73.2% · PF 4.22)",
                "is_profitable": true,
                "rank": 14
        },
        {
                "symbol": "Boom 900 Index",
                "strategy": "Malaysian SNR",
                "category": "Sintéticos · Pestaña Malaysian SNR",
                "trades": 919,
                "win_rate": 73.66,
                "tp1": 677,
                "tp2": 440,
                "tp3": 203,
                "tp4": 81,
                "be": 237,
                "sl": 242,
                "pnl": 82282.0,
                "status": "Activo Malaysian SNR (+822.82R · WR 73.66% · PF 4.33)",
                "is_profitable": true,
                "rank": 15
        },
        {
                "symbol": "Crash 600 Index",
                "strategy": "Malaysian SNR",
                "category": "Sintéticos · Pestaña Malaysian SNR",
                "trades": 920,
                "win_rate": 73.5,
                "tp1": 676,
                "tp2": 439,
                "tp3": 203,
                "tp4": 81,
                "be": 237,
                "sl": 244,
                "pnl": 81920.0,
                "status": "Activo Malaysian SNR (+819.2R · WR 73.5% · PF 4.29)",
                "is_profitable": true,
                "rank": 16
        },
        {
                "symbol": "Boom 600 Index",
                "strategy": "Malaysian SNR",
                "category": "Sintéticos · Pestaña Malaysian SNR",
                "trades": 910,
                "win_rate": 73.75,
                "tp1": 671,
                "tp2": 436,
                "tp3": 201,
                "tp4": 81,
                "be": 235,
                "sl": 239,
                "pnl": 81640.0,
                "status": "Activo Malaysian SNR (+816.4R · WR 73.75% · PF 4.35)",
                "is_profitable": true,
                "rank": 17
        },
        {
                "symbol": "Step Index 200",
                "strategy": "ICT",
                "category": "Sintéticos · Pestaña ICT",
                "trades": 1131,
                "win_rate": 67.41,
                "tp1": 762,
                "tp2": 442,
                "tp3": 198,
                "tp4": 99,
                "be": 320,
                "sl": 369,
                "pnl": 81314.0,
                "status": "Activo con Confluencia Tripartita (+813.14R · WR 67.41%)",
                "is_profitable": true,
                "rank": 18
        },
        {
                "symbol": "Boom 300 Index",
                "strategy": "Malaysian SNR",
                "category": "Sintéticos · Pestaña Malaysian SNR",
                "trades": 883,
                "win_rate": 74.29,
                "tp1": 656,
                "tp2": 426,
                "tp3": 197,
                "tp4": 79,
                "be": 230,
                "sl": 227,
                "pnl": 80494.0,
                "status": "Activo Malaysian SNR (+804.94R · WR 74.29% · PF 4.48)",
                "is_profitable": true,
                "rank": 19
        },
        {
                "symbol": "Jump 10 Index",
                "strategy": "Trend Pullback",
                "category": "Sintéticos · Pestaña Trend Pullback",
                "trades": 1288,
                "win_rate": 63.37,
                "tp1": 816,
                "tp2": 473,
                "tp3": 212,
                "tp4": 106,
                "be": 343,
                "sl": 472,
                "pnl": 79332.0,
                "status": "Activo con Confluencia Tripartita (+793.32R · WR 63.37%)",
                "is_profitable": true,
                "rank": 20
        },
        {
                "symbol": "Volatility Crash 750 Index",
                "strategy": "Malaysian SNR",
                "category": "Sintéticos · Pestaña Malaysian SNR",
                "trades": 888,
                "win_rate": 73.5,
                "tp1": 653,
                "tp2": 424,
                "tp3": 196,
                "tp4": 78,
                "be": 229,
                "sl": 235,
                "pnl": 79204.0,
                "status": "Activo Malaysian SNR (+792.04R · WR 73.5% · PF 4.3)",
                "is_profitable": true,
                "rank": 21
        },
        {
                "symbol": "Volatility 250 (1s) Index",
                "strategy": "ICT",
                "category": "Sintéticos · Pestaña ICT",
                "trades": 1122,
                "win_rate": 66.82,
                "tp1": 750,
                "tp2": 435,
                "tp3": 195,
                "tp4": 98,
                "be": 315,
                "sl": 372,
                "pnl": 78979.0,
                "status": "Activo con Confluencia Tripartita (+789.79R · WR 66.82%)",
                "is_profitable": true,
                "rank": 22
        },
        {
                "symbol": "Volatility 50 (1s) Index",
                "strategy": "ICT",
                "category": "Sintéticos · Pestaña ICT",
                "trades": 1126,
                "win_rate": 66.66,
                "tp1": 751,
                "tp2": 436,
                "tp3": 195,
                "tp4": 98,
                "be": 315,
                "sl": 375,
                "pnl": 78801.0,
                "status": "Activo con Confluencia Tripartita (+788.01R · WR 66.66%)",
                "is_profitable": true,
                "rank": 23
        },
        {
                "symbol": "Crash 900 Index",
                "strategy": "Malaysian SNR",
                "category": "Sintéticos · Pestaña Malaysian SNR",
                "trades": 862,
                "win_rate": 73.5,
                "tp1": 634,
                "tp2": 412,
                "tp3": 190,
                "tp4": 76,
                "be": 222,
                "sl": 228,
                "pnl": 76916.0,
                "status": "Activo Malaysian SNR (+769.16R · WR 73.5% · PF 4.31)",
                "is_profitable": true,
                "rank": 24
        },
        {
                "symbol": "Jump 50 Index",
                "strategy": "ICT",
                "category": "Sintéticos · Pestaña ICT",
                "trades": 1132,
                "win_rate": 65.64,
                "tp1": 743,
                "tp2": 431,
                "tp3": 193,
                "tp4": 97,
                "be": 312,
                "sl": 389,
                "pnl": 76276.0,
                "status": "Activo con Confluencia Tripartita (+762.76R · WR 65.64%)",
                "is_profitable": true,
                "rank": 25
        },
        {
                "symbol": "Volatility 75 Index",
                "strategy": "ICT",
                "category": "Sintéticos · Pestaña ICT",
                "trades": 1113,
                "win_rate": 65.9,
                "tp1": 733,
                "tp2": 425,
                "tp3": 191,
                "tp4": 95,
                "be": 308,
                "sl": 380,
                "pnl": 75734.0,
                "status": "Activo con Confluencia Tripartita (+757.34R · WR 65.90%)",
                "is_profitable": true,
                "rank": 26
        },
        {
                "symbol": "Boom 600 Index",
                "strategy": "ICT",
                "category": "Sintéticos · Pestaña ICT",
                "trades": 1037,
                "win_rate": 67.3,
                "tp1": 698,
                "tp2": 419,
                "tp3": 174,
                "tp4": 70,
                "be": 279,
                "sl": 339,
                "pnl": 75706.0,
                "status": "Activo ICT (+757.06R · WR 67.3% · PF 3.19)",
                "is_profitable": true,
                "rank": 27
        },
        {
                "symbol": "Volatility 25 Index",
                "strategy": "ICT",
                "category": "Sintéticos · Pestaña ICT",
                "trades": 918,
                "win_rate": 71.4,
                "tp1": 655,
                "tp2": 380,
                "tp3": 170,
                "tp4": 85,
                "be": 275,
                "sl": 263,
                "pnl": 75340.0,
                "status": "Activo con Confluencia Tripartita (+753.40R · WR 71.40%)",
                "is_profitable": true,
                "rank": 28
        },
        {
                "symbol": "Jump 10 Index",
                "strategy": "MultiStrategia",
                "category": "Sintéticos · Worker JUMP (Magic 26082105 · PID 16804)",
                "trades": 1478,
                "win_rate": 64.4,
                "tp1": 952,
                "tp2": 666,
                "tp3": 333,
                "tp4": 143,
                "be": 296,
                "sl": 526,
                "pnl": 74800.0,
                "status": "DEJAR ACTIVO (5A: +748.0R, WR 64.4% | Vivo: 63 ops, -$279.21)",
                "is_profitable": true,
                "rank": 29
        },
        {
                "symbol": "Jump 75 Index",
                "strategy": "ICT",
                "category": "Sintéticos · Pestaña ICT",
                "trades": 1119,
                "win_rate": 65.22,
                "tp1": 730,
                "tp2": 423,
                "tp3": 190,
                "tp4": 95,
                "be": 307,
                "sl": 389,
                "pnl": 74202.0,
                "status": "Activo con Confluencia Tripartita (+742.02R · WR 65.22%)",
                "is_profitable": true,
                "rank": 30
        },
        {
                "symbol": "Step Index",
                "strategy": "ICT",
                "category": "Sintéticos · Pestaña ICT",
                "trades": 1113,
                "win_rate": 65.29,
                "tp1": 727,
                "tp2": 422,
                "tp3": 189,
                "tp4": 95,
                "be": 305,
                "sl": 386,
                "pnl": 74003.0,
                "status": "Activo con Confluencia Tripartita (+740.03R · WR 65.29%)",
                "is_profitable": true,
                "rank": 31
        },
        {
                "symbol": "Step Index 400",
                "strategy": "ICT",
                "category": "Sintéticos · Pestaña ICT",
                "trades": 1100,
                "win_rate": 65.48,
                "tp1": 720,
                "tp2": 418,
                "tp3": 187,
                "tp4": 94,
                "be": 302,
                "sl": 380,
                "pnl": 73671.0,
                "status": "Activo con Confluencia Tripartita (+736.71R · WR 65.48%)",
                "is_profitable": true,
                "rank": 32
        },
        {
                "symbol": "Boom 900 Index",
                "strategy": "ICT",
                "category": "Sintéticos · Pestaña ICT",
                "trades": 1058,
                "win_rate": 65.89,
                "tp1": 697,
                "tp2": 418,
                "tp3": 174,
                "tp4": 70,
                "be": 279,
                "sl": 361,
                "pnl": 73304.0,
                "status": "Activo ICT (+733.04R · WR 65.89% · PF 2.99)",
                "is_profitable": true,
                "rank": 33
        },
        {
                "symbol": "Crash 1000 Index",
                "strategy": "ICT",
                "category": "Sintéticos · Pestaña ICT",
                "trades": 1235,
                "win_rate": 62.0,
                "tp1": 766,
                "tp2": 460,
                "tp3": 192,
                "tp4": 77,
                "be": 306,
                "sl": 469,
                "pnl": 73190.0,
                "status": "Activo ICT (+731.9R · WR 62.0% · PF 2.53)",
                "is_profitable": true,
                "rank": 34
        },
        {
                "symbol": "Volatility 50 Index",
                "strategy": "ICT",
                "category": "Sintéticos · Pestaña ICT",
                "trades": 1105,
                "win_rate": 65.12,
                "tp1": 720,
                "tp2": 418,
                "tp3": 187,
                "tp4": 94,
                "be": 302,
                "sl": 385,
                "pnl": 72992.0,
                "status": "Activo con Confluencia Tripartita (+729.92R · WR 65.12%)",
                "is_profitable": true,
                "rank": 35
        },
        {
                "symbol": "Jump 75 Index",
                "strategy": "Malaysian SNR",
                "category": "Sintéticos · Pestaña Malaysian SNR",
                "trades": 854,
                "win_rate": 77.87,
                "tp1": 532,
                "tp2": 306,
                "tp3": 140,
                "tp4": 66,
                "be": 226,
                "sl": 189,
                "pnl": 72870.0,
                "status": "Activo con Confluencia Tripartita (+728.70R · WR 77.87%)",
                "is_profitable": true,
                "rank": 36
        },
        {
                "symbol": "Volatility 150 (1s) Index",
                "strategy": "ICT",
                "category": "Sintéticos · Pestaña ICT",
                "trades": 1107,
                "win_rate": 64.99,
                "tp1": 719,
                "tp2": 417,
                "tp3": 187,
                "tp4": 93,
                "be": 302,
                "sl": 388,
                "pnl": 72757.0,
                "status": "Activo con Confluencia Tripartita (+727.57R · WR 64.99%)",
                "is_profitable": true,
                "rank": 37
        },
        {
                "symbol": "Volatility 75 (1s) Index",
                "strategy": "ICT",
                "category": "Sintéticos · Pestaña ICT",
                "trades": 1104,
                "win_rate": 64.87,
                "tp1": 716,
                "tp2": 415,
                "tp3": 186,
                "tp4": 93,
                "be": 301,
                "sl": 388,
                "pnl": 72222.0,
                "status": "Activo con Confluencia Tripartita (+722.22R · WR 64.87%)",
                "is_profitable": true,
                "rank": 38
        },
        {
                "symbol": "Boom 500 Index",
                "strategy": "ICT",
                "category": "Sintéticos · Pestaña ICT",
                "trades": 1215,
                "win_rate": 62.08,
                "tp1": 754,
                "tp2": 452,
                "tp3": 188,
                "tp4": 75,
                "be": 302,
                "sl": 461,
                "pnl": 72110.0,
                "status": "Activo ICT (+721.1R · WR 62.08% · PF 2.53)",
                "is_profitable": true,
                "rank": 39
        },
        {
                "symbol": "Step Index 300",
                "strategy": "ICT",
                "category": "Sintéticos · Pestaña ICT",
                "trades": 1090,
                "win_rate": 65.0,
                "tp1": 708,
                "tp2": 411,
                "tp3": 184,
                "tp4": 92,
                "be": 297,
                "sl": 382,
                "pnl": 72000.0,
                "status": "Activo con Confluencia Tripartita (+720.00R · WR 65.00%)",
                "is_profitable": true,
                "rank": 40
        },
        {
                "symbol": "Crash 600 Index",
                "strategy": "ICT",
                "category": "Sintéticos · Pestaña ICT",
                "trades": 1056,
                "win_rate": 65.26,
                "tp1": 689,
                "tp2": 413,
                "tp3": 172,
                "tp4": 69,
                "be": 276,
                "sl": 367,
                "pnl": 71428.0,
                "status": "Activo ICT (+714.28R · WR 65.26% · PF 2.91)",
                "is_profitable": true,
                "rank": 41
        },
        {
                "symbol": "Volatility 100 (1s) Index",
                "strategy": "ICT",
                "category": "Sintéticos · Pestaña ICT",
                "trades": 1099,
                "win_rate": 64.61,
                "tp1": 710,
                "tp2": 412,
                "tp3": 185,
                "tp4": 92,
                "be": 298,
                "sl": 389,
                "pnl": 71166.0,
                "status": "Activo con Confluencia Tripartita (+711.66R · WR 64.61%)",
                "is_profitable": true,
                "rank": 42
        },
        {
                "symbol": "Boom 1000 Index",
                "strategy": "ICT",
                "category": "Sintéticos · Pestaña ICT",
                "trades": 1190,
                "win_rate": 62.18,
                "tp1": 740,
                "tp2": 444,
                "tp3": 185,
                "tp4": 74,
                "be": 296,
                "sl": 450,
                "pnl": 71020.0,
                "status": "Activo ICT (+710.2R · WR 62.18% · PF 2.55)",
                "is_profitable": true,
                "rank": 43
        },
        {
                "symbol": "Step Index",
                "strategy": "Malaysian SNR",
                "category": "Sintéticos · Pestaña Malaysian SNR",
                "trades": 729,
                "win_rate": 82.58,
                "tp1": 482,
                "tp2": 277,
                "tp3": 126,
                "tp4": 60,
                "be": 205,
                "sl": 127,
                "pnl": 70376.0,
                "status": "Activo con Confluencia Tripartita (+703.76R · WR 82.58%)",
                "is_profitable": true,
                "rank": 44
        },
        {
                "symbol": "Step Index 500",
                "strategy": "ICT",
                "category": "Sintéticos · Pestaña ICT",
                "trades": 1082,
                "win_rate": 64.53,
                "tp1": 698,
                "tp2": 405,
                "tp3": 181,
                "tp4": 91,
                "be": 293,
                "sl": 384,
                "pnl": 69845.0,
                "status": "Activo con Confluencia Tripartita (+698.45R · WR 64.53%)",
                "is_profitable": true,
                "rank": 45
        },
        {
                "symbol": "Jump 100 Index",
                "strategy": "ICT",
                "category": "Sintéticos · Pestaña ICT",
                "trades": 1090,
                "win_rate": 64.18,
                "tp1": 700,
                "tp2": 406,
                "tp3": 182,
                "tp4": 91,
                "be": 294,
                "sl": 390,
                "pnl": 69388.0,
                "status": "Activo con Confluencia Tripartita (+693.88R · WR 64.18%)",
                "is_profitable": true,
                "rank": 46
        },
        {
                "symbol": "Step Index 200",
                "strategy": "Malaysian SNR",
                "category": "Sintéticos · Pestaña Malaysian SNR",
                "trades": 708,
                "win_rate": 82.77,
                "tp1": 469,
                "tp2": 270,
                "tp3": 123,
                "tp4": 59,
                "be": 199,
                "sl": 122,
                "pnl": 68668.0,
                "status": "Activo con Confluencia Tripartita (+686.68R · WR 82.77%)",
                "is_profitable": true,
                "rank": 47
        },
        {
                "symbol": "Volatility 100 Index",
                "strategy": "ICT",
                "category": "Sintéticos · Pestaña ICT",
                "trades": 1085,
                "win_rate": 64.02,
                "tp1": 695,
                "tp2": 403,
                "tp3": 181,
                "tp4": 90,
                "be": 292,
                "sl": 390,
                "pnl": 68627.0,
                "status": "Activo con Confluencia Tripartita (+686.27R · WR 64.02%)",
                "is_profitable": true,
                "rank": 48
        },
        {
                "symbol": "Step Index 400",
                "strategy": "Malaysian SNR",
                "category": "Sintéticos · Pestaña Malaysian SNR",
                "trades": 711,
                "win_rate": 82.42,
                "tp1": 469,
                "tp2": 270,
                "tp3": 123,
                "tp4": 59,
                "be": 199,
                "sl": 125,
                "pnl": 68368.0,
                "status": "Activo con Confluencia Tripartita (+683.68R · WR 82.42%)",
                "is_profitable": true,
                "rank": 49
        },
        {
                "symbol": "Step Index 500",
                "strategy": "Malaysian SNR",
                "category": "Sintéticos · Pestaña Malaysian SNR",
                "trades": 702,
                "win_rate": 81.48,
                "tp1": 458,
                "tp2": 263,
                "tp3": 120,
                "tp4": 57,
                "be": 194,
                "sl": 130,
                "pnl": 65936.0,
                "status": "Activo con Confluencia Tripartita (+659.36R · WR 81.48%)",
                "is_profitable": true,
                "rank": 50
        },
        {
                "symbol": "Volatility 10 Index",
                "strategy": "MultiStrategia",
                "category": "Sintéticos · Worker VOLATILITY (1) (Magic 26082401 · PID 14464)",
                "trades": 1477,
                "win_rate": 63.7,
                "tp1": 941,
                "tp2": 659,
                "tp3": 329,
                "tp4": 141,
                "be": 295,
                "sl": 536,
                "pnl": 65350.0,
                "status": "DEJAR ACTIVO (LÍDER) (5A: +653.5R, WR 63.7% | Vivo: 78 ops, +$123.73)",
                "is_profitable": true,
                "rank": 51
        },
        {
                "symbol": "Jump 25 Index",
                "strategy": "MultiStrategia",
                "category": "Sintéticos · Worker JUMP (Magic 26082105 · PID 16804)",
                "trades": 1465,
                "win_rate": 63.5,
                "tp1": 930,
                "tp2": 651,
                "tp3": 326,
                "tp4": 140,
                "be": 293,
                "sl": 535,
                "pnl": 65140.0,
                "status": "DEJAR ACTIVO (5A: +651.4R, WR 63.5% | Vivo: 67 ops, +$71.31)",
                "is_profitable": true,
                "rank": 52
        },
        {
                "symbol": "Step Index 300",
                "strategy": "Malaysian SNR",
                "category": "Sintéticos · Pestaña Malaysian SNR",
                "trades": 695,
                "win_rate": 81.8,
                "tp1": 454,
                "tp2": 261,
                "tp3": 118,
                "tp4": 56,
                "be": 193,
                "sl": 126,
                "pnl": 65050.0,
                "status": "Activo con Confluencia Tripartita (+650.50R · WR 81.80%)",
                "is_profitable": true,
                "rank": 53
        },
        {
                "symbol": "Volatility Crash 400 Index",
                "strategy": "ICT",
                "category": "Sintéticos · Pestaña ICT",
                "trades": 887,
                "win_rate": 67.04,
                "tp1": 595,
                "tp2": 357,
                "tp3": 149,
                "tp4": 60,
                "be": 238,
                "sl": 292,
                "pnl": 64226.0,
                "status": "Activo ICT (+642.26R · WR 67.04% · PF 3.16)",
                "is_profitable": true,
                "rank": 54
        },
        {
                "symbol": "Volatility Boom 400 Index",
                "strategy": "ICT",
                "category": "Sintéticos · Pestaña ICT",
                "trades": 932,
                "win_rate": 65.65,
                "tp1": 612,
                "tp2": 367,
                "tp3": 153,
                "tp4": 61,
                "be": 245,
                "sl": 320,
                "pnl": 64056.0,
                "status": "Activo ICT (+640.56R · WR 65.65% · PF 2.96)",
                "is_profitable": true,
                "rank": 55
        },
        {
                "symbol": "Step Index 200",
                "strategy": "Trend Pullback",
                "category": "Sintéticos · Pestaña Trend Pullback",
                "trades": 1074,
                "win_rate": 62.28,
                "tp1": 669,
                "tp2": 388,
                "tp3": 174,
                "tp4": 87,
                "be": 281,
                "sl": 405,
                "pnl": 63166.0,
                "status": "Activo con Confluencia Tripartita (+631.66R · WR 62.28%)",
                "is_profitable": true,
                "rank": 56
        },
        {
                "symbol": "Volatility 10 Index",
                "strategy": "Malaysian SNR",
                "category": "Sintéticos · Pestaña Malaysian SNR",
                "trades": 745,
                "win_rate": 77.32,
                "tp1": 461,
                "tp2": 265,
                "tp3": 121,
                "tp4": 58,
                "be": 196,
                "sl": 169,
                "pnl": 62588.0,
                "status": "Activo con Confluencia Tripartita (+625.88R · WR 77.32%)",
                "is_profitable": true,
                "rank": 57
        },
        {
                "symbol": "Volatility Boom 750 Index",
                "strategy": "ICT",
                "category": "Sintéticos · Pestaña ICT",
                "trades": 957,
                "win_rate": 64.24,
                "tp1": 615,
                "tp2": 369,
                "tp3": 154,
                "tp4": 62,
                "be": 246,
                "sl": 342,
                "pnl": 62286.0,
                "status": "Activo ICT (+622.86R · WR 64.24% · PF 2.79)",
                "is_profitable": true,
                "rank": 58
        },
        {
                "symbol": "Volatility 10 Index",
                "strategy": "Trend Pullback",
                "category": "Sintéticos · Pestaña Trend Pullback",
                "trades": 1085,
                "win_rate": 61.35,
                "tp1": 666,
                "tp2": 386,
                "tp3": 173,
                "tp4": 87,
                "be": 280,
                "sl": 419,
                "pnl": 61240.0,
                "status": "Activo con Confluencia Tripartita (+612.40R · WR 61.35%)",
                "is_profitable": true,
                "rank": 59
        },
        {
                "symbol": "Volatility 50 (1s) Index",
                "strategy": "Trend Pullback",
                "category": "Sintéticos · Pestaña Trend Pullback",
                "trades": 1046,
                "win_rate": 62.08,
                "tp1": 649,
                "tp2": 376,
                "tp3": 169,
                "tp4": 84,
                "be": 273,
                "sl": 397,
                "pnl": 60986.0,
                "status": "Activo con Confluencia Tripartita (+609.86R · WR 62.08%)",
                "is_profitable": true,
                "rank": 60
        },
        {
                "symbol": "Volatility 250 (1s) Index",
                "strategy": "Trend Pullback",
                "category": "Sintéticos · Pestaña Trend Pullback",
                "trades": 1040,
                "win_rate": 62.19,
                "tp1": 647,
                "tp2": 375,
                "tp3": 168,
                "tp4": 84,
                "be": 272,
                "sl": 393,
                "pnl": 60928.0,
                "status": "Activo con Confluencia Tripartita (+609.28R · WR 62.19%)",
                "is_profitable": true,
                "rank": 61
        },
        {
                "symbol": "Volatility 75 Index",
                "strategy": "Trend Pullback",
                "category": "Sintéticos · Pestaña Trend Pullback",
                "trades": 1060,
                "win_rate": 61.74,
                "tp1": 654,
                "tp2": 379,
                "tp3": 170,
                "tp4": 85,
                "be": 275,
                "sl": 406,
                "pnl": 60883.0,
                "status": "Activo con Confluencia Tripartita (+608.83R · WR 61.74%)",
                "is_profitable": true,
                "rank": 62
        },
        {
                "symbol": "Jump 50 Index",
                "strategy": "Trend Pullback",
                "category": "Sintéticos · Pestaña Trend Pullback",
                "trades": 1068,
                "win_rate": 61.55,
                "tp1": 657,
                "tp2": 381,
                "tp3": 171,
                "tp4": 85,
                "be": 276,
                "sl": 411,
                "pnl": 60825.0,
                "status": "Activo con Confluencia Tripartita (+608.25R · WR 61.55%)",
                "is_profitable": true,
                "rank": 63
        },
        {
                "symbol": "Jump 25 Index",
                "strategy": "Trend Pullback",
                "category": "Sintéticos · Pestaña Trend Pullback",
                "trades": 1070,
                "win_rate": 61.49,
                "tp1": 658,
                "tp2": 382,
                "tp3": 171,
                "tp4": 86,
                "be": 276,
                "sl": 412,
                "pnl": 60775.0,
                "status": "Activo con Confluencia Tripartita (+607.75R · WR 61.49%)",
                "is_profitable": true,
                "rank": 64
        },
        {
                "symbol": "Volatility 250 (1s) Index",
                "strategy": "MultiStrategia",
                "category": "Sintéticos · Worker VOLATILITY (4) (Magic 26082404 · PID 35156)",
                "trades": 1254,
                "win_rate": 63.6,
                "tp1": 798,
                "tp2": 559,
                "tp3": 279,
                "tp4": 120,
                "be": 251,
                "sl": 456,
                "pnl": 60720.0,
                "status": "DEJAR ACTIVO (5A: +607.2R, WR 63.6% | Vivo: 5 ops, +$0.05)",
                "is_profitable": true,
                "rank": 65
        },
        {
                "symbol": "Crash 900 Index",
                "strategy": "ICT",
                "category": "Sintéticos · Pestaña ICT",
                "trades": 1002,
                "win_rate": 62.38,
                "tp1": 625,
                "tp2": 375,
                "tp3": 156,
                "tp4": 62,
                "be": 250,
                "sl": 377,
                "pnl": 60296.0,
                "status": "Activo ICT (+602.96R · WR 62.38% · PF 2.57)",
                "is_profitable": true,
                "rank": 66
        },
        {
                "symbol": "Jump 75 Index",
                "strategy": "MultiStrategia",
                "category": "Sintéticos · Worker JUMP (Magic 26082105 · PID 16804)",
                "trades": 1329,
                "win_rate": 63.0,
                "tp1": 837,
                "tp2": 586,
                "tp3": 293,
                "tp4": 126,
                "be": 266,
                "sl": 492,
                "pnl": 60280.0,
                "status": "DEJAR ACTIVO (5A: +602.8R, WR 63.0% | Vivo: 35 ops, +$148.75)",
                "is_profitable": true,
                "rank": 67
        },
        {
                "symbol": "Volatility 50 (1s) Index",
                "strategy": "MultiStrategia",
                "category": "Sintéticos · Worker VOLATILITY (2) (Magic 26082402 · PID 36704)",
                "trades": 1260,
                "win_rate": 63.5,
                "tp1": 800,
                "tp2": 560,
                "tp3": 280,
                "tp4": 120,
                "be": 252,
                "sl": 460,
                "pnl": 59840.0,
                "status": "CANDIDATO A PODAR (5A: +598.4R, WR 63.5% | Vivo: 36 ops, -$242.73)",
                "is_profitable": false,
                "rank": 68
        },
        {
                "symbol": "Jump 75 Index",
                "strategy": "Trend Pullback",
                "category": "Sintéticos · Pestaña Trend Pullback",
                "trades": 1070,
                "win_rate": 60.96,
                "tp1": 652,
                "tp2": 378,
                "tp3": 170,
                "tp4": 85,
                "be": 274,
                "sl": 418,
                "pnl": 59329.0,
                "status": "Activo con Confluencia Tripartita (+593.29R · WR 60.96%)",
                "is_profitable": true,
                "rank": 69
        },
        {
                "symbol": "Step Index",
                "strategy": "Trend Pullback",
                "category": "Sintéticos · Pestaña Trend Pullback",
                "trades": 1061,
                "win_rate": 61.04,
                "tp1": 648,
                "tp2": 376,
                "tp3": 168,
                "tp4": 84,
                "be": 272,
                "sl": 413,
                "pnl": 59047.0,
                "status": "Activo con Confluencia Tripartita (+590.47R · WR 61.04%)",
                "is_profitable": true,
                "rank": 70
        },
        {
                "symbol": "Step Index 400",
                "strategy": "Trend Pullback",
                "category": "Sintéticos · Pestaña Trend Pullback",
                "trades": 1053,
                "win_rate": 61.16,
                "tp1": 644,
                "tp2": 374,
                "tp3": 167,
                "tp4": 84,
                "be": 270,
                "sl": 409,
                "pnl": 58924.0,
                "status": "Activo con Confluencia Tripartita (+589.24R · WR 61.16%)",
                "is_profitable": true,
                "rank": 71
        },
        {
                "symbol": "Volatility 150 (1s) Index",
                "strategy": "Malaysian SNR",
                "category": "Sintéticos · Pestaña Malaysian SNR",
                "trades": 697,
                "win_rate": 77.47,
                "tp1": 432,
                "tp2": 248,
                "tp3": 113,
                "tp4": 54,
                "be": 184,
                "sl": 157,
                "pnl": 58820.0,
                "status": "Activo con Confluencia Tripartita (+588.20R · WR 77.47%)",
                "is_profitable": true,
                "rank": 72
        },
        {
                "symbol": "Volatility 150 (1s) Index",
                "strategy": "Trend Pullback",
                "category": "Sintéticos · Pestaña Trend Pullback",
                "trades": 1054,
                "win_rate": 60.78,
                "tp1": 641,
                "tp2": 372,
                "tp3": 167,
                "tp4": 83,
                "be": 269,
                "sl": 413,
                "pnl": 57958.0,
                "status": "Activo con Confluencia Tripartita (+579.58R · WR 60.78%)",
                "is_profitable": true,
                "rank": 73
        },
        {
                "symbol": "Volatility 50 (1s) Index",
                "strategy": "Malaysian SNR",
                "category": "Sintéticos · Pestaña Malaysian SNR",
                "trades": 703,
                "win_rate": 76.53,
                "tp1": 430,
                "tp2": 247,
                "tp3": 113,
                "tp4": 54,
                "be": 183,
                "sl": 165,
                "pnl": 57744.0,
                "status": "Activo con Confluencia Tripartita (+577.44R · WR 76.53%)",
                "is_profitable": true,
                "rank": 74
        },
        {
                "symbol": "Volatility 50 Index",
                "strategy": "Trend Pullback",
                "category": "Sintéticos · Pestaña Trend Pullback",
                "trades": 1047,
                "win_rate": 60.84,
                "tp1": 637,
                "tp2": 369,
                "tp3": 166,
                "tp4": 83,
                "be": 268,
                "sl": 410,
                "pnl": 57734.0,
                "status": "Activo con Confluencia Tripartita (+577.34R · WR 60.84%)",
                "is_profitable": true,
                "rank": 75
        },
        {
                "symbol": "Volatility 75 (1s) Index",
                "strategy": "Trend Pullback",
                "category": "Sintéticos · Pestaña Trend Pullback",
                "trades": 1048,
                "win_rate": 60.67,
                "tp1": 636,
                "tp2": 369,
                "tp3": 165,
                "tp4": 83,
                "be": 267,
                "sl": 412,
                "pnl": 57335.0,
                "status": "Activo con Confluencia Tripartita (+573.35R · WR 60.67%)",
                "is_profitable": true,
                "rank": 76
        },
        {
                "symbol": "Step Index 300",
                "strategy": "Trend Pullback",
                "category": "Sintéticos · Pestaña Trend Pullback",
                "trades": 1040,
                "win_rate": 60.8,
                "tp1": 632,
                "tp2": 366,
                "tp3": 164,
                "tp4": 82,
                "be": 266,
                "sl": 408,
                "pnl": 57200.0,
                "status": "Activo con Confluencia Tripartita (+572.00R · WR 60.80%)",
                "is_profitable": true,
                "rank": 77
        },
        {
                "symbol": "Volatility Crash 750 Index",
                "strategy": "ICT",
                "category": "Sintéticos · Pestaña ICT",
                "trades": 891,
                "win_rate": 63.88,
                "tp1": 569,
                "tp2": 341,
                "tp3": 142,
                "tp4": 57,
                "be": 228,
                "sl": 322,
                "pnl": 57058.0,
                "status": "Activo ICT (+570.58R · WR 63.88% · PF 2.74)",
                "is_profitable": true,
                "rank": 78
        },
        {
                "symbol": "Volatility 100 (1s) Index",
                "strategy": "Trend Pullback",
                "category": "Sintéticos · Pestaña Trend Pullback",
                "trades": 1045,
                "win_rate": 60.54,
                "tp1": 633,
                "tp2": 367,
                "tp3": 165,
                "tp4": 82,
                "be": 266,
                "sl": 412,
                "pnl": 56824.0,
                "status": "Activo con Confluencia Tripartita (+568.24R · WR 60.54%)",
                "is_profitable": true,
                "rank": 79
        },
        {
                "symbol": "Jump 50 Index",
                "strategy": "MultiStrategia",
                "category": "Sintéticos · Worker JUMP (Magic 26082105 · PID 16804)",
                "trades": 1261,
                "win_rate": 62.7,
                "tp1": 791,
                "tp2": 554,
                "tp3": 277,
                "tp4": 119,
                "be": 252,
                "sl": 470,
                "pnl": 56360.0,
                "status": "DEJAR ACTIVO (5A: +563.6R, WR 62.7% | Vivo: 69 ops, -$240.55)",
                "is_profitable": true,
                "rank": 80
        },
        {
                "symbol": "Step Index 500",
                "strategy": "Trend Pullback",
                "category": "Sintéticos · Pestaña Trend Pullback",
                "trades": 1033,
                "win_rate": 60.48,
                "tp1": 625,
                "tp2": 362,
                "tp3": 162,
                "tp4": 81,
                "be": 262,
                "sl": 408,
                "pnl": 56013.0,
                "status": "Activo con Confluencia Tripartita (+560.13R · WR 60.48%)",
                "is_profitable": true,
                "rank": 81
        },
        {
                "symbol": "Jump 10 Index",
                "strategy": "Malaysian SNR",
                "category": "Sintéticos · Pestaña Malaysian SNR",
                "trades": 684,
                "win_rate": 76.32,
                "tp1": 418,
                "tp2": 240,
                "tp3": 110,
                "tp4": 52,
                "be": 177,
                "sl": 162,
                "pnl": 55836.0,
                "status": "Activo con Confluencia Tripartita (+558.36R · WR 76.32%)",
                "is_profitable": true,
                "rank": 82
        },
        {
                "symbol": "Volatility 150 (1s) Index",
                "strategy": "MultiStrategia",
                "category": "Sintéticos · Worker VOLATILITY (4) (Magic 26082404 · PID 35156)",
                "trades": 1255,
                "win_rate": 62.4,
                "tp1": 783,
                "tp2": 548,
                "tp3": 274,
                "tp4": 117,
                "be": 251,
                "sl": 472,
                "pnl": 55720.0,
                "status": "DESBLOQUEAR (ALTA CONVICCIÓN) (5A: +557.2R, WR 62.4% | Vivo: 0 ops, $0.00)",
                "is_profitable": true,
                "rank": 83
        },
        {
                "symbol": "Volatility 75 Index",
                "strategy": "MultiStrategia",
                "category": "Sintéticos · Worker VOLATILITY (3) (Magic 26082403 · PID 7572)",
                "trades": 1242,
                "win_rate": 62.9,
                "tp1": 781,
                "tp2": 547,
                "tp3": 273,
                "tp4": 117,
                "be": 248,
                "sl": 461,
                "pnl": 55630.0,
                "status": "DEJAR ACTIVO (5A: +556.3R, WR 62.9% | Vivo: 70 ops, -$281.30)",
                "is_profitable": true,
                "rank": 84
        },
        {
                "symbol": "Jump 100 Index",
                "strategy": "Trend Pullback",
                "category": "Sintéticos · Pestaña Trend Pullback",
                "trades": 1038,
                "win_rate": 60.16,
                "tp1": 624,
                "tp2": 362,
                "tp3": 162,
                "tp4": 81,
                "be": 262,
                "sl": 414,
                "pnl": 55438.0,
                "status": "Activo con Confluencia Tripartita (+554.38R · WR 60.16%)",
                "is_profitable": true,
                "rank": 85
        },
        {
                "symbol": "Volatility Crash 550 Index",
                "strategy": "ICT",
                "category": "Sintéticos · Pestaña ICT",
                "trades": 813,
                "win_rate": 65.47,
                "tp1": 532,
                "tp2": 319,
                "tp3": 133,
                "tp4": 53,
                "be": 213,
                "sl": 281,
                "pnl": 55394.0,
                "status": "Activo ICT (+553.94R · WR 65.47% · PF 2.93)",
                "is_profitable": true,
                "rank": 86
        },
        {
                "symbol": "Volatility 100 Index",
                "strategy": "Trend Pullback",
                "category": "Sintéticos · Pestaña Trend Pullback",
                "trades": 1035,
                "win_rate": 60.13,
                "tp1": 622,
                "tp2": 361,
                "tp3": 162,
                "tp4": 81,
                "be": 261,
                "sl": 413,
                "pnl": 55198.0,
                "status": "Activo con Confluencia Tripartita (+551.98R · WR 60.13%)",
                "is_profitable": true,
                "rank": 87
        },
        {
                "symbol": "Volatility 75 Index",
                "strategy": "Malaysian SNR",
                "category": "Sintéticos · Pestaña Malaysian SNR",
                "trades": 677,
                "win_rate": 76.22,
                "tp1": 413,
                "tp2": 237,
                "tp3": 108,
                "tp4": 52,
                "be": 175,
                "sl": 161,
                "pnl": 55108.0,
                "status": "Activo con Confluencia Tripartita (+551.08R · WR 76.22%)",
                "is_profitable": true,
                "rank": 88
        },
        {
                "symbol": "Volatility 25 Index",
                "strategy": "Malaysian SNR",
                "category": "Sintéticos · Pestaña Malaysian SNR",
                "trades": 638,
                "win_rate": 78.21,
                "tp1": 399,
                "tp2": 230,
                "tp3": 105,
                "tp4": 50,
                "be": 170,
                "sl": 139,
                "pnl": 54962.0,
                "status": "Activo con Confluencia Tripartita (+549.62R · WR 78.21%)",
                "is_profitable": true,
                "rank": 89
        },
        {
                "symbol": "Step Index 400",
                "strategy": "MultiStrategia",
                "category": "Sintéticos · Worker STEP (MultiStrategia · Magic 26082104 · PID 17452)",
                "trades": 1224,
                "win_rate": 62.4,
                "tp1": 764,
                "tp2": 535,
                "tp3": 267,
                "tp4": 115,
                "be": 245,
                "sl": 460,
                "pnl": 54620.0,
                "status": "DEJAR ACTIVO (5A: +546.2R, WR 62.4% | Vivo: 55 ops, -$306.00)",
                "is_profitable": true,
                "rank": 90
        },
        {
                "symbol": "Volatility 50 Index",
                "strategy": "MultiStrategia",
                "category": "Sintéticos · Worker VOLATILITY (2) (Magic 26082402 · PID 36704)",
                "trades": 1226,
                "win_rate": 62.1,
                "tp1": 761,
                "tp2": 533,
                "tp3": 266,
                "tp4": 114,
                "be": 245,
                "sl": 465,
                "pnl": 54010.0,
                "status": "DEJAR ACTIVO (5A: +540.1R, WR 62.1% | Vivo: 9 ops, +$108.82)",
                "is_profitable": true,
                "rank": 92
        },
        {
                "symbol": "Jump 25 Index",
                "strategy": "Malaysian SNR",
                "category": "Sintéticos · Pestaña Malaysian SNR",
                "trades": 650,
                "win_rate": 76.77,
                "tp1": 399,
                "tp2": 230,
                "tp3": 105,
                "tp4": 50,
                "be": 170,
                "sl": 151,
                "pnl": 53762.0,
                "status": "Activo con Confluencia Tripartita (+537.62R · WR 76.77%)",
                "is_profitable": true,
                "rank": 93
        },
        {
                "symbol": "Jump 50 Index",
                "strategy": "Malaysian SNR",
                "category": "Sintéticos · Pestaña Malaysian SNR",
                "trades": 655,
                "win_rate": 76.49,
                "tp1": 401,
                "tp2": 230,
                "tp3": 105,
                "tp4": 50,
                "be": 170,
                "sl": 154,
                "pnl": 53738.0,
                "status": "Activo con Confluencia Tripartita (+537.38R · WR 76.49%)",
                "is_profitable": true,
                "rank": 94
        },
        {
                "symbol": "Volatility 250 (1s) Index",
                "strategy": "Malaysian SNR",
                "category": "Sintéticos · Pestaña Malaysian SNR",
                "trades": 659,
                "win_rate": 76.02,
                "tp1": 401,
                "tp2": 230,
                "tp3": 105,
                "tp4": 50,
                "be": 170,
                "sl": 158,
                "pnl": 53338.0,
                "status": "Activo con Confluencia Tripartita (+533.38R · WR 76.02%)",
                "is_profitable": true,
                "rank": 95
        },
        {
                "symbol": "Volatility 75 (1s) Index",
                "strategy": "MultiStrategia",
                "category": "Sintéticos · Worker VOLATILITY (3) (Magic 26082403 · PID 7572)",
                "trades": 1220,
                "win_rate": 61.8,
                "tp1": 754,
                "tp2": 528,
                "tp3": 264,
                "tp4": 113,
                "be": 244,
                "sl": 466,
                "pnl": 53130.0,
                "status": "DEJAR ACTIVO (5A: +531.3R, WR 61.8% | Vivo: 26 ops, +$21.35)",
                "is_profitable": true,
                "rank": 96
        },
        {
                "symbol": "Volatility 75 (1s) Index",
                "strategy": "Malaysian SNR",
                "category": "Sintéticos · Pestaña Malaysian SNR",
                "trades": 651,
                "win_rate": 75.73,
                "tp1": 394,
                "tp2": 227,
                "tp3": 104,
                "tp4": 49,
                "be": 168,
                "sl": 158,
                "pnl": 52234.0,
                "status": "Activo con Confluencia Tripartita (+522.34R · WR 75.73%)",
                "is_profitable": true,
                "rank": 97
        },
        {
                "symbol": "Crash 300 Index",
                "strategy": "ICT",
                "category": "Sintéticos · Pestaña ICT",
                "trades": 621,
                "win_rate": 71.53,
                "tp1": 444,
                "tp2": 266,
                "tp3": 111,
                "tp4": 44,
                "be": 178,
                "sl": 177,
                "pnl": 52098.0,
                "status": "Activo ICT (+520.98R · WR 71.53% · PF 3.89)",
                "is_profitable": true,
                "rank": 98
        },
        {
                "symbol": "Volatility 100 (1s) Index",
                "strategy": "MultiStrategia",
                "category": "Sintéticos · Worker VOLATILITY (4) (Magic 26082404 · PID 35156)",
                "trades": 1212,
                "win_rate": 61.6,
                "tp1": 747,
                "tp2": 523,
                "tp3": 261,
                "tp4": 112,
                "be": 242,
                "sl": 465,
                "pnl": 51960.0,
                "status": "DEJAR ACTIVO (5A: +519.6R, WR 61.6% | Vivo: 29 ops, -$208.67)",
                "is_profitable": true,
                "rank": 99
        },
        {
                "symbol": "Volatility 90 (1s) Index",
                "strategy": "ICT",
                "category": "Sintéticos · Pestaña ICT",
                "trades": 1062,
                "win_rate": 58.35,
                "tp1": 620,
                "tp2": 360,
                "tp3": 161,
                "tp4": 81,
                "be": 260,
                "sl": 442,
                "pnl": 51818.0,
                "status": "Activo con Confluencia Tripartita (+518.18R · WR 58.35%)",
                "is_profitable": true,
                "rank": 100
        },
        {
                "symbol": "Volatility 15 Index",
                "strategy": "ICT",
                "category": "Sintéticos · Pestaña ICT",
                "trades": 840,
                "win_rate": 63.17,
                "tp1": 531,
                "tp2": 308,
                "tp3": 138,
                "tp4": 69,
                "be": 223,
                "sl": 309,
                "pnl": 51310.0,
                "status": "Activo con Confluencia Tripartita (+513.10R · WR 63.17%)",
                "is_profitable": true,
                "rank": 101
        },
        {
                "symbol": "Step Index 500",
                "strategy": "MultiStrategia",
                "category": "Sintéticos · Worker STEP (MultiStrategia · Magic 26082104 · PID 17452)",
                "trades": 1195,
                "win_rate": 61.5,
                "tp1": 735,
                "tp2": 514,
                "tp3": 257,
                "tp4": 110,
                "be": 239,
                "sl": 460,
                "pnl": 51020.0,
                "status": "DEJAR ACTIVO (5A: +510.2R, WR 61.5% | Vivo: 119 ops, -$76.48)",
                "is_profitable": true,
                "rank": 102
        },
        {
                "symbol": "Volatility 50 Index",
                "strategy": "Malaysian SNR",
                "category": "Sintéticos · Pestaña Malaysian SNR",
                "trades": 640,
                "win_rate": 75.47,
                "tp1": 386,
                "tp2": 222,
                "tp3": 101,
                "tp4": 48,
                "be": 164,
                "sl": 157,
                "pnl": 50954.0,
                "status": "Activo con Confluencia Tripartita (+509.54R · WR 75.47%)",
                "is_profitable": true,
                "rank": 103
        },
        {
                "symbol": "Jump 100 Index",
                "strategy": "MultiStrategia",
                "category": "Sintéticos · Worker JUMP (Magic 26082105 · PID 16804)",
                "trades": 1198,
                "win_rate": 61.2,
                "tp1": 733,
                "tp2": 513,
                "tp3": 257,
                "tp4": 110,
                "be": 240,
                "sl": 465,
                "pnl": 50300.0,
                "status": "DESBLOQUEAR (ALTA CONVICCIÓN) (5A: +503.0R, WR 61.2% | Vivo: 2 ops, +$52.92)",
                "is_profitable": true,
                "rank": 104
        },
        {
                "symbol": "Volatility 100 Index",
                "strategy": "MultiStrategia",
                "category": "Sintéticos · Worker VOLATILITY (3) (Magic 26082403 · PID 7572)",
                "trades": 1192,
                "win_rate": 61.1,
                "tp1": 728,
                "tp2": 510,
                "tp3": 255,
                "tp4": 109,
                "be": 238,
                "sl": 464,
                "pnl": 49740.0,
                "status": "DEJAR ACTIVO (5A: +497.4R, WR 61.1% | Vivo: 22 ops, -$50.78)",
                "is_profitable": true,
                "rank": 105
        },
        {
                "symbol": "Boom 300 Index",
                "strategy": "ICT",
                "category": "Sintéticos · Pestaña ICT",
                "trades": 638,
                "win_rate": 68.52,
                "tp1": 437,
                "tp2": 262,
                "tp3": 109,
                "tp4": 44,
                "be": 175,
                "sl": 201,
                "pnl": 48544.0,
                "status": "Activo ICT (+485.44R · WR 68.52% · PF 3.37)",
                "is_profitable": true,
                "rank": 106
        },
        {
                "symbol": "Volatility 100 Index",
                "strategy": "Malaysian SNR",
                "category": "Sintéticos · Pestaña Malaysian SNR",
                "trades": 625,
                "win_rate": 74.56,
                "tp1": 373,
                "tp2": 214,
                "tp3": 98,
                "tp4": 47,
                "be": 158,
                "sl": 159,
                "pnl": 48408.0,
                "status": "Activo con Confluencia Tripartita (+484.08R · WR 74.56%)",
                "is_profitable": true,
                "rank": 107
        },
        {
                "symbol": "Volatility 5 Index",
                "strategy": "ICT",
                "category": "Sintéticos · Pestaña ICT",
                "trades": 812,
                "win_rate": 62.47,
                "tp1": 507,
                "tp2": 294,
                "tp3": 132,
                "tp4": 66,
                "be": 213,
                "sl": 305,
                "pnl": 48150.0,
                "status": "Activo con Confluencia Tripartita (+481.50R · WR 62.47%)",
                "is_profitable": true,
                "rank": 108
        },
        {
                "symbol": "Volatility 90 Index",
                "strategy": "ICT",
                "category": "Sintéticos · Pestaña ICT",
                "trades": 829,
                "win_rate": 61.93,
                "tp1": 513,
                "tp2": 298,
                "tp3": 133,
                "tp4": 67,
                "be": 215,
                "sl": 316,
                "pnl": 48017.0,
                "status": "Activo con Confluencia Tripartita (+480.17R · WR 61.93%)",
                "is_profitable": true,
                "rank": 109
        },
        {
                "symbol": "Crash 500 Index",
                "strategy": "MultiStrategia",
                "category": "Sintéticos · Worker CRASH (Magic 26082102 · PID 25904)",
                "trades": 1034,
                "win_rate": 62.3,
                "tp1": 644,
                "tp2": 451,
                "tp3": 225,
                "tp4": 97,
                "be": 207,
                "sl": 390,
                "pnl": 47710.0,
                "status": "DEJAR ACTIVO (LÍDER) (5A: +477.1R, WR 62.3% | Vivo: 80 ops, +$1,330.81)",
                "is_profitable": true,
                "rank": 110
        },
        {
                "symbol": "Crash 500 Index",
                "strategy": "Trend Pullback",
                "category": "Sintéticos · Pestaña Trend Pullback",
                "trades": 876,
                "win_rate": 60.37,
                "tp1": 529,
                "tp2": 307,
                "tp3": 138,
                "tp4": 69,
                "be": 222,
                "sl": 347,
                "pnl": 47255.0,
                "status": "Activo con Confluencia Tripartita (+472.55R · WR 60.37%)",
                "is_profitable": true,
                "rank": 111
        },
        {
                "symbol": "Jump 100 Index",
                "strategy": "Malaysian SNR",
                "category": "Sintéticos · Pestaña Malaysian SNR",
                "trades": 592,
                "win_rate": 75.51,
                "tp1": 358,
                "tp2": 206,
                "tp3": 94,
                "tp4": 45,
                "be": 152,
                "sl": 145,
                "pnl": 47186.0,
                "status": "Activo con Confluencia Tripartita (+471.86R · WR 75.51%)",
                "is_profitable": true,
                "rank": 112
        },
        {
                "symbol": "Volatility 100 (1s) Index",
                "strategy": "Malaysian SNR",
                "category": "Sintéticos · Pestaña Malaysian SNR",
                "trades": 609,
                "win_rate": 74.55,
                "tp1": 363,
                "tp2": 209,
                "tp3": 95,
                "tp4": 45,
                "be": 154,
                "sl": 155,
                "pnl": 47152.0,
                "status": "Activo con Confluencia Tripartita (+471.52R · WR 74.55%)",
                "is_profitable": true,
                "rank": 113
        },
        {
                "symbol": "Volatility 90 (1s) Index",
                "strategy": "Trend Pullback",
                "category": "Sintéticos · Pestaña Trend Pullback",
                "trades": 1017,
                "win_rate": 56.87,
                "tp1": 578,
                "tp2": 335,
                "tp3": 150,
                "tp4": 75,
                "be": 243,
                "sl": 439,
                "pnl": 45784.0,
                "status": "Activo con Confluencia Tripartita (+457.84R · WR 56.87%)",
                "is_profitable": true,
                "rank": 114
        },
        {
                "symbol": "Boom 600 Index",
                "strategy": "MultiStrategia",
                "category": "Sintéticos · Worker BOOM (Magic 26082101 · PID 20320)",
                "trades": 912,
                "win_rate": 63.2,
                "tp1": 576,
                "tp2": 403,
                "tp3": 202,
                "tp4": 86,
                "be": 182,
                "sl": 336,
                "pnl": 44640.0,
                "status": "DEJAR ACTIVO (5A: +446.4R, WR 63.2% | Vivo: 54 ops, -$171.98)",
                "is_profitable": true,
                "rank": 115
        },
        {
                "symbol": "Volatility 90 (1s) Index",
                "strategy": "Malaysian SNR",
                "category": "Sintéticos · Pestaña Malaysian SNR",
                "trades": 569,
                "win_rate": 74.52,
                "tp1": 339,
                "tp2": 195,
                "tp3": 89,
                "tp4": 42,
                "be": 144,
                "sl": 145,
                "pnl": 44012.0,
                "status": "Activo con Confluencia Tripartita (+440.12R · WR 74.52%)",
                "is_profitable": true,
                "rank": 116
        },
        {
                "symbol": "Boom 600 Index",
                "strategy": "Trend Pullback",
                "category": "Sintéticos · Pestaña Trend Pullback",
                "trades": 738,
                "win_rate": 62.35,
                "tp1": 460,
                "tp2": 267,
                "tp3": 120,
                "tp4": 60,
                "be": 193,
                "sl": 278,
                "pnl": 43536.0,
                "status": "Activo con Confluencia Tripartita (+435.36R · WR 62.35%)",
                "is_profitable": true,
                "rank": 117
        },
        {
                "symbol": "Boom 1000 Index",
                "strategy": "Trend Pullback",
                "category": "Sintéticos · Pestaña Trend Pullback",
                "trades": 875,
                "win_rate": 58.27,
                "tp1": 510,
                "tp2": 296,
                "tp3": 133,
                "tp4": 66,
                "be": 214,
                "sl": 365,
                "pnl": 42515.0,
                "status": "Activo con Confluencia Tripartita (+425.15R · WR 58.27%)",
                "is_profitable": true,
                "rank": 118
        },
        {
                "symbol": "Vol over Boom 550",
                "strategy": "ICT",
                "category": "Sintéticos · Pestaña ICT",
                "trades": 651,
                "win_rate": 64.5,
                "tp1": 420,
                "tp2": 244,
                "tp3": 109,
                "tp4": 55,
                "be": 176,
                "sl": 231,
                "pnl": 41973.0,
                "status": "Activo con Confluencia Tripartita (+419.73R · WR 64.50%)",
                "is_profitable": true,
                "rank": 119
        },
        {
                "symbol": "VolSwitch High Vol Index",
                "strategy": "Malaysian SNR",
                "category": "Sintéticos · Pestaña Malaysian SNR",
                "trades": 485,
                "win_rate": 78.35,
                "tp1": 304,
                "tp2": 175,
                "tp3": 80,
                "tp4": 38,
                "be": 129,
                "sl": 105,
                "pnl": 41940.0,
                "status": "Activo con Confluencia Tripartita (+419.40R · WR 78.35%)",
                "is_profitable": true,
                "rank": 120
        },
        {
                "symbol": "Boom 500 Index",
                "strategy": "Trend Pullback",
                "category": "Sintéticos · Pestaña Trend Pullback",
                "trades": 866,
                "win_rate": 58.2,
                "tp1": 504,
                "tp2": 292,
                "tp3": 131,
                "tp4": 66,
                "be": 212,
                "sl": 362,
                "pnl": 41923.0,
                "status": "Activo con Confluencia Tripartita (+419.23R · WR 58.20%)",
                "is_profitable": true,
                "rank": 121
        },
        {
                "symbol": "Volatility 15 Index",
                "strategy": "Trend Pullback",
                "category": "Sintéticos · Pestaña Trend Pullback",
                "trades": 794,
                "win_rate": 59.77,
                "tp1": 475,
                "tp2": 276,
                "tp3": 124,
                "tp4": 62,
                "be": 200,
                "sl": 319,
                "pnl": 41616.0,
                "status": "Activo con Confluencia Tripartita (+416.16R · WR 59.77%)",
                "is_profitable": true,
                "rank": 122
        },
        {
                "symbol": "Boom 900 Index",
                "strategy": "Trend Pullback",
                "category": "Sintéticos · Pestaña Trend Pullback",
                "trades": 731,
                "win_rate": 61.22,
                "tp1": 448,
                "tp2": 260,
                "tp3": 116,
                "tp4": 58,
                "be": 188,
                "sl": 283,
                "pnl": 41017.0,
                "status": "Activo con Confluencia Tripartita (+410.17R · WR 61.22%)",
                "is_profitable": true,
                "rank": 123
        },
        {
                "symbol": "Boom 900 Index",
                "strategy": "MultiStrategia",
                "category": "Sintéticos · Worker BOOM (Magic 26082101 · PID 20320)",
                "trades": 895,
                "win_rate": 62.1,
                "tp1": 556,
                "tp2": 389,
                "tp3": 195,
                "tp4": 83,
                "be": 179,
                "sl": 339,
                "pnl": 40800.0,
                "status": "DEJAR ACTIVO (5A: +408.0R, WR 62.1% | Vivo: 27 ops, -$199.40)",
                "is_profitable": true,
                "rank": 124
        },
        {
                "symbol": "Vol over Crash 550",
                "strategy": "ICT",
                "category": "Sintéticos · Pestaña ICT",
                "trades": 636,
                "win_rate": 64.13,
                "tp1": 408,
                "tp2": 237,
                "tp3": 106,
                "tp4": 53,
                "be": 171,
                "sl": 228,
                "pnl": 40406.0,
                "status": "Activo con Confluencia Tripartita (+404.06R · WR 64.13%)",
                "is_profitable": true,
                "rank": 125
        },
        {
                "symbol": "Volatility 25 Index",
                "strategy": "Trend Pullback",
                "category": "Sintéticos · Pestaña Trend Pullback",
                "trades": 561,
                "win_rate": 67.27,
                "tp1": 377,
                "tp2": 219,
                "tp3": 98,
                "tp4": 49,
                "be": 158,
                "sl": 184,
                "pnl": 40133.0,
                "status": "Activo con Confluencia Tripartita (+401.33R · WR 67.27%)",
                "is_profitable": true,
                "rank": 126
        },
        {
                "symbol": "Volatility 5 Index",
                "strategy": "Trend Pullback",
                "category": "Sintéticos · Pestaña Trend Pullback",
                "trades": 772,
                "win_rate": 59.56,
                "tp1": 460,
                "tp2": 267,
                "tp3": 120,
                "tp4": 60,
                "be": 193,
                "sl": 312,
                "pnl": 40050.0,
                "status": "Activo con Confluencia Tripartita (+400.50R · WR 59.56%)",
                "is_profitable": true,
                "rank": 127
        },
        {
                "symbol": "Crash 300 Index",
                "strategy": "MultiStrategia",
                "category": "Sintéticos · Worker CRASH (Magic 26082102 · PID 25904)",
                "trades": 606,
                "win_rate": 68.2,
                "tp1": 413,
                "tp2": 289,
                "tp3": 145,
                "tp4": 62,
                "be": 121,
                "sl": 193,
                "pnl": 40040.0,
                "status": "CANDIDATO A PODAR (5A: +400.4R, WR 68.2% | Vivo: 34 ops, -$434.70)",
                "is_profitable": false,
                "rank": 128
        },
        {
                "symbol": "Crash 1000 Index",
                "strategy": "Trend Pullback",
                "category": "Sintéticos · Pestaña Trend Pullback",
                "trades": 877,
                "win_rate": 57.1,
                "tp1": 501,
                "tp2": 291,
                "tp3": 130,
                "tp4": 65,
                "be": 210,
                "sl": 376,
                "pnl": 39996.0,
                "status": "Activo con Confluencia Tripartita (+399.96R · WR 57.10%)",
                "is_profitable": true,
                "rank": 129
        },
        {
                "symbol": "XAUUSD",
                "strategy": "ORB New York",
                "category": "Mercados Tradicionales · Pestaña ORB New York",
                "trades": 439,
                "win_rate": 71.46,
                "tp1": 314,
                "tp2": 182,
                "tp3": 80,
                "tp4": 40,
                "be": 132,
                "sl": 125,
                "pnl": 39310.0,
                "status": "Activo Dual-Engine (+393.10R · WR 71.46%)",
                "is_profitable": true,
                "rank": 130
        },
        {
                "symbol": "VolSwitch High Vol Index",
                "strategy": "ICT",
                "category": "Sintéticos · Pestaña ICT",
                "trades": 571,
                "win_rate": 66.07,
                "tp1": 377,
                "tp2": 219,
                "tp3": 98,
                "tp4": 49,
                "be": 158,
                "sl": 194,
                "pnl": 39101.0,
                "status": "Activo con Confluencia Tripartita (+391.01R · WR 66.07%)",
                "is_profitable": true,
                "rank": 131
        },
        {
                "symbol": "Volatility 90 Index",
                "strategy": "Trend Pullback",
                "category": "Sintéticos · Pestaña Trend Pullback",
                "trades": 783,
                "win_rate": 58.6,
                "tp1": 459,
                "tp2": 266,
                "tp3": 119,
                "tp4": 60,
                "be": 193,
                "sl": 324,
                "pnl": 38704.0,
                "status": "Activo con Confluencia Tripartita (+387.04R · WR 58.60%)",
                "is_profitable": true,
                "rank": 132
        },
        {
                "symbol": "Crash 600 Index",
                "strategy": "Trend Pullback",
                "category": "Sintéticos · Pestaña Trend Pullback",
                "trades": 724,
                "win_rate": 60.16,
                "tp1": 436,
                "tp2": 253,
                "tp3": 113,
                "tp4": 57,
                "be": 183,
                "sl": 288,
                "pnl": 38667.0,
                "status": "Activo con Confluencia Tripartita (+386.67R · WR 60.16%)",
                "is_profitable": true,
                "rank": 133
        },
        {
                "symbol": "Volatility 15 (1s) Index",
                "strategy": "MultiStrategia",
                "category": "Sintéticos · Worker VOLATILITY (1) (Magic 26082401 · PID 14464)",
                "trades": 1220,
                "win_rate": 68.8,
                "tp1": 839,
                "tp2": 587,
                "tp3": 294,
                "tp4": 126,
                "be": 244,
                "sl": 381,
                "pnl": 38000.0,
                "status": "DEJAR ACTIVO (5A: +380.0R, WR 68.8% | Vivo: 8 ops, +$113.53)",
                "is_profitable": true,
                "rank": 134
        },
        {
                "symbol": "Volatility 15 Index",
                "strategy": "Malaysian SNR",
                "category": "Sintéticos · Pestaña Malaysian SNR",
                "trades": 490,
                "win_rate": 74.49,
                "tp1": 292,
                "tp2": 168,
                "tp3": 77,
                "tp4": 36,
                "be": 124,
                "sl": 125,
                "pnl": 37870.0,
                "status": "Activo con Confluencia Tripartita (+378.70R · WR 74.49%)",
                "is_profitable": true,
                "rank": 135
        },
        {
                "symbol": "Volatility 90 Index",
                "strategy": "Malaysian SNR",
                "category": "Sintéticos · Pestaña Malaysian SNR",
                "trades": 481,
                "win_rate": 74.43,
                "tp1": 286,
                "tp2": 165,
                "tp3": 75,
                "tp4": 36,
                "be": 122,
                "sl": 123,
                "pnl": 37104.0,
                "status": "Activo con Confluencia Tripartita (+371.04R · WR 74.43%)",
                "is_profitable": true,
                "rank": 136
        },
        {
                "symbol": "Volatility 5 Index",
                "strategy": "Malaysian SNR",
                "category": "Sintéticos · Pestaña Malaysian SNR",
                "trades": 476,
                "win_rate": 74.58,
                "tp1": 284,
                "tp2": 163,
                "tp3": 75,
                "tp4": 36,
                "be": 121,
                "sl": 121,
                "pnl": 36890.0,
                "status": "Activo con Confluencia Tripartita (+368.90R · WR 74.58%)",
                "is_profitable": true,
                "rank": 137
        },
        {
                "symbol": "Crash 600 Index",
                "strategy": "MultiStrategia",
                "category": "Sintéticos · Worker CRASH (Magic 26082102 · PID 25904)",
                "trades": 882,
                "win_rate": 60.9,
                "tp1": 537,
                "tp2": 376,
                "tp3": 188,
                "tp4": 81,
                "be": 176,
                "sl": 345,
                "pnl": 36670.0,
                "status": "CANDIDATO A PODAR (5A: +366.7R, WR 60.9% | Vivo: 30 ops, -$395.67)",
                "is_profitable": false,
                "rank": 138
        },
        {
                "symbol": "Volatility 10 (1s) Index",
                "strategy": "MultiStrategia",
                "category": "Sintéticos · Worker VOLATILITY (1) (Magic 26082401 · PID 14464)",
                "trades": 1215,
                "win_rate": 68.6,
                "tp1": 833,
                "tp2": 583,
                "tp3": 292,
                "tp4": 125,
                "be": 243,
                "sl": 382,
                "pnl": 36500.0,
                "status": "DEJAR ACTIVO (5A: +365.0R, WR 68.6% | Vivo: 7 ops, +$44.91)",
                "is_profitable": true,
                "rank": 139
        },
        {
                "symbol": "Volatility 15 Index",
                "strategy": "MultiStrategia",
                "category": "Sintéticos · Worker VOLATILITY (1) (Magic 26082401 · PID 14464)",
                "trades": 936,
                "win_rate": 60.4,
                "tp1": 565,
                "tp2": 396,
                "tp3": 198,
                "tp4": 85,
                "be": 187,
                "sl": 371,
                "pnl": 36360.0,
                "status": "CANDIDATO A PODAR (5A: +363.6R, WR 60.4% | Vivo: 33 ops, -$305.51)",
                "is_profitable": false,
                "rank": 140
        },
        {
                "symbol": "Boom 300 Index",
                "strategy": "MultiStrategia",
                "category": "Sintéticos · Worker BOOM (Magic 26082101 · PID 20320)",
                "trades": 603,
                "win_rate": 64.8,
                "tp1": 391,
                "tp2": 274,
                "tp3": 137,
                "tp4": 59,
                "be": 121,
                "sl": 212,
                "pnl": 35320.0,
                "status": "DEJAR ACTIVO (5A: +353.2R, WR 64.8% | Vivo: 10 ops, -$76.98)",
                "is_profitable": true,
                "rank": 141
        },
        {
                "symbol": "Vol over Boom 550",
                "strategy": "Malaysian SNR",
                "category": "Sintéticos · Pestaña Malaysian SNR",
                "trades": 461,
                "win_rate": 73.97,
                "tp1": 273,
                "tp2": 157,
                "tp3": 72,
                "tp4": 34,
                "be": 116,
                "sl": 120,
                "pnl": 35058.0,
                "status": "Activo con Confluencia Tripartita (+350.58R · WR 73.97%)",
                "is_profitable": true,
                "rank": 142
        },
        {
                "symbol": "High Frequency Vol 50 Index",
                "strategy": "ICT",
                "category": "Sintéticos · Pestaña ICT",
                "trades": 762,
                "win_rate": 56.94,
                "tp1": 434,
                "tp2": 252,
                "tp3": 113,
                "tp4": 56,
                "be": 182,
                "sl": 328,
                "pnl": 34440.0,
                "status": "Activo con Confluencia Tripartita (+344.40R · WR 56.94%)",
                "is_profitable": true,
                "rank": 143
        },
        {
                "symbol": "Crash 900 Index",
                "strategy": "Trend Pullback",
                "category": "Sintéticos · Pestaña Trend Pullback",
                "trades": 715,
                "win_rate": 58.07,
                "tp1": 415,
                "tp2": 241,
                "tp3": 108,
                "tp4": 54,
                "be": 174,
                "sl": 300,
                "pnl": 34376.0,
                "status": "Activo con Confluencia Tripartita (+343.76R · WR 58.07%)",
                "is_profitable": true,
                "rank": 144
        },
        {
                "symbol": "Vol over Crash 550",
                "strategy": "Malaysian SNR",
                "category": "Sintéticos · Pestaña Malaysian SNR",
                "trades": 447,
                "win_rate": 74.05,
                "tp1": 265,
                "tp2": 152,
                "tp3": 70,
                "tp4": 33,
                "be": 113,
                "sl": 116,
                "pnl": 34078.0,
                "status": "Activo con Confluencia Tripartita (+340.78R · WR 74.05%)",
                "is_profitable": true,
                "rank": 145
        },
        {
                "symbol": "Volatility 5 Index",
                "strategy": "MultiStrategia",
                "category": "Sintéticos · Worker VOLATILITY (1) (Magic 26082401 · PID 14464)",
                "trades": 906,
                "win_rate": 59.9,
                "tp1": 543,
                "tp2": 380,
                "tp3": 190,
                "tp4": 81,
                "be": 181,
                "sl": 363,
                "pnl": 33990.0,
                "status": "DEJAR ACTIVO (5A: +339.9R, WR 59.9% | Vivo: 52 ops, -$59.99)",
                "is_profitable": true,
                "rank": 146
        },
        {
                "symbol": "Crash 300 Index",
                "strategy": "Trend Pullback",
                "category": "Sintéticos · Pestaña Trend Pullback",
                "trades": 454,
                "win_rate": 68.47,
                "tp1": 311,
                "tp2": 180,
                "tp3": 81,
                "tp4": 40,
                "be": 131,
                "sl": 143,
                "pnl": 33868.0,
                "status": "Activo con Confluencia Tripartita (+338.68R · WR 68.47%)",
                "is_profitable": true,
                "rank": 147
        },
        {
                "symbol": "XAUUSD",
                "strategy": "ICT",
                "category": "Mercados Tradicionales · Pestaña ICT",
                "trades": 576,
                "win_rate": 64.7,
                "tp1": 373,
                "tp2": 216,
                "tp3": 95,
                "tp4": 48,
                "be": 157,
                "sl": 203,
                "pnl": 33634.0,
                "status": "Activo con Confluencia Tripartita (+336.34R · WR 64.70%)",
                "is_profitable": true,
                "rank": 148
        },
        {
                "symbol": "Vol over Boom 550",
                "strategy": "Trend Pullback",
                "category": "Sintéticos · Pestaña Trend Pullback",
                "trades": 607,
                "win_rate": 60.47,
                "tp1": 367,
                "tp2": 213,
                "tp3": 95,
                "tp4": 48,
                "be": 154,
                "sl": 240,
                "pnl": 32898.0,
                "status": "Activo con Confluencia Tripartita (+328.98R · WR 60.47%)",
                "is_profitable": true,
                "rank": 149
        },
        {
                "symbol": "High Frequency Vol 100 Index",
                "strategy": "ICT",
                "category": "Sintéticos · Pestaña ICT",
                "trades": 751,
                "win_rate": 56.31,
                "tp1": 423,
                "tp2": 245,
                "tp3": 110,
                "tp4": 55,
                "be": 178,
                "sl": 328,
                "pnl": 32736.0,
                "status": "Activo con Confluencia Tripartita (+327.36R · WR 56.31%)",
                "is_profitable": true,
                "rank": 150
        },
        {
                "symbol": "Volatility 25 Index",
                "strategy": "MultiStrategia",
                "category": "Sintéticos · Worker VOLATILITY (2) (Magic 26082402 · PID 36704)",
                "trades": 1047,
                "win_rate": 68.2,
                "tp1": 714,
                "tp2": 500,
                "tp3": 250,
                "tp4": 107,
                "be": 209,
                "sl": 333,
                "pnl": 32280.0,
                "status": "CANDIDATO A PODAR (5A: +322.8R, WR 68.2% | Vivo: 94 ops, -$916.61)",
                "is_profitable": false,
                "rank": 151
        },
        {
                "symbol": "Vol over Crash 550",
                "strategy": "Trend Pullback",
                "category": "Sintéticos · Pestaña Trend Pullback",
                "trades": 598,
                "win_rate": 60.23,
                "tp1": 360,
                "tp2": 209,
                "tp3": 94,
                "tp4": 47,
                "be": 151,
                "sl": 238,
                "pnl": 32045.0,
                "status": "Activo con Confluencia Tripartita (+320.45R · WR 60.23%)",
                "is_profitable": true,
                "rank": 152
        },
        {
                "symbol": "XAUUSD",
                "strategy": "Malaysian SNR",
                "category": "Mercados Tradicionales · Pestaña Malaysian SNR",
                "trades": 530,
                "win_rate": 67.5,
                "tp1": 358,
                "tp2": 186,
                "tp3": 79,
                "tp4": 39,
                "be": 125,
                "sl": 172,
                "pnl": 31130.0,
                "status": "Activo con Confluencia Tripartita (+311.30R · WR 67.50%)",
                "is_profitable": true,
                "rank": 153
        },
        {
                "symbol": "Volatility 90 Index",
                "strategy": "MultiStrategia",
                "category": "Sintéticos · Worker VOLATILITY (3) (Magic 26082403 · PID 7572)",
                "trades": 917,
                "win_rate": 59.2,
                "tp1": 543,
                "tp2": 380,
                "tp3": 190,
                "tp4": 81,
                "be": 183,
                "sl": 374,
                "pnl": 31020.0,
                "status": "DESBLOQUEAR (ALTA CONVICCIÓN) (5A: +310.2R, WR 59.2% | Vivo: 1 ops, +$169.78)",
                "is_profitable": true,
                "rank": 154
        },
        {
                "symbol": "High Frequency Vol 100 Index",
                "strategy": "Malaysian SNR",
                "category": "Sintéticos · Pestaña Malaysian SNR",
                "trades": 414,
                "win_rate": 73.43,
                "tp1": 243,
                "tp2": 140,
                "tp3": 64,
                "tp4": 30,
                "be": 103,
                "sl": 110,
                "pnl": 30952.0,
                "status": "Activo con Confluencia Tripartita (+309.52R · WR 73.43%)",
                "is_profitable": true,
                "rank": 155
        },
        {
                "symbol": "VolSwitch High Vol Index",
                "strategy": "Trend Pullback",
                "category": "Sintéticos · Pestaña Trend Pullback",
                "trades": 520,
                "win_rate": 61.71,
                "tp1": 321,
                "tp2": 186,
                "tp3": 83,
                "tp4": 42,
                "be": 135,
                "sl": 199,
                "pnl": 29827.0,
                "status": "Activo con Confluencia Tripartita (+298.27R · WR 61.71%)",
                "is_profitable": true,
                "rank": 156
        },
        {
                "symbol": "High Frequency Vol 50 Index",
                "strategy": "Malaysian SNR",
                "category": "Sintéticos · Pestaña Malaysian SNR",
                "trades": 396,
                "win_rate": 73.48,
                "tp1": 233,
                "tp2": 134,
                "tp3": 61,
                "tp4": 29,
                "be": 99,
                "sl": 105,
                "pnl": 29658.0,
                "status": "Activo con Confluencia Tripartita (+296.58R · WR 73.48%)",
                "is_profitable": true,
                "rank": 157
        },
        {
                "symbol": "High Frequency Vol 50 Index",
                "strategy": "Trend Pullback",
                "category": "Sintéticos · Pestaña Trend Pullback",
                "trades": 722,
                "win_rate": 55.29,
                "tp1": 399,
                "tp2": 231,
                "tp3": 104,
                "tp4": 52,
                "be": 168,
                "sl": 323,
                "pnl": 29594.0,
                "status": "Activo con Confluencia Tripartita (+295.94R · WR 55.29%)",
                "is_profitable": true,
                "rank": 158
        },
        {
                "symbol": "Boom 500 Index",
                "strategy": "MultiStrategia",
                "category": "Sintéticos · Worker BOOM (Magic 26082101 · PID 20320)",
                "trades": 1015,
                "win_rate": 61.0,
                "tp1": 619,
                "tp2": 433,
                "tp3": 217,
                "tp4": 93,
                "be": 203,
                "sl": 396,
                "pnl": 28740.0,
                "status": "DEJAR ACTIVO (LÍDER) (5A: +287.4R, WR 61.0% | Vivo: 55 ops, +$552.42)",
                "is_profitable": true,
                "rank": 159
        },
        {
                "symbol": "High Frequency Vol 100 Index",
                "strategy": "Trend Pullback",
                "category": "Sintéticos · Pestaña Trend Pullback",
                "trades": 712,
                "win_rate": 54.63,
                "tp1": 389,
                "tp2": 226,
                "tp3": 101,
                "tp4": 51,
                "be": 163,
                "sl": 323,
                "pnl": 27986.0,
                "status": "Activo con Confluencia Tripartita (+279.86R · WR 54.63%)",
                "is_profitable": true,
                "rank": 160
        },
        {
                "symbol": "Boom 300 Index",
                "strategy": "Trend Pullback",
                "category": "Sintéticos · Pestaña Trend Pullback",
                "trades": 437,
                "win_rate": 63.08,
                "tp1": 276,
                "tp2": 160,
                "tp3": 72,
                "tp4": 36,
                "be": 116,
                "sl": 161,
                "pnl": 26593.0,
                "status": "Activo con Confluencia Tripartita (+265.93R · WR 63.08%)",
                "is_profitable": true,
                "rank": 161
        },
        {
                "symbol": "US Oil",
                "strategy": "ICT",
                "category": "Mercados Tradicionales · Pestaña ICT",
                "trades": 439,
                "win_rate": 64.7,
                "tp1": 284,
                "tp2": 165,
                "tp3": 73,
                "tp4": 36,
                "be": 119,
                "sl": 155,
                "pnl": 25563.0,
                "status": "Activo con Confluencia Tripartita (+255.63R · WR 64.70%)",
                "is_profitable": true,
                "rank": 162
        },
        {
                "symbol": "GBPUSD",
                "strategy": "ORB New York",
                "category": "Mercados Tradicionales · Pestaña ORB New York",
                "trades": 419,
                "win_rate": 62.8,
                "tp1": 263,
                "tp2": 153,
                "tp3": 67,
                "tp4": 34,
                "be": 110,
                "sl": 156,
                "pnl": 25428.0,
                "status": "Activo Dual-Engine (+254.28R · WR 62.80%)",
                "is_profitable": true,
                "rank": 163
        },
        {
                "symbol": "UK Brent Oil",
                "strategy": "ICT",
                "category": "Mercados Tradicionales · Pestaña ICT",
                "trades": 420,
                "win_rate": 64.7,
                "tp1": 272,
                "tp2": 158,
                "tp3": 70,
                "tp4": 35,
                "be": 114,
                "sl": 148,
                "pnl": 24530.0,
                "status": "Activo con Confluencia Tripartita (+245.30R · WR 64.70%)",
                "is_profitable": true,
                "rank": 164
        },
        {
                "symbol": "Boom 1000 Index",
                "strategy": "MultiStrategia",
                "category": "Sintéticos · Worker BOOM (Magic 26082101 · PID 20320)",
                "trades": 1027,
                "win_rate": 60.5,
                "tp1": 621,
                "tp2": 435,
                "tp3": 217,
                "tp4": 93,
                "be": 205,
                "sl": 406,
                "pnl": 24100.0,
                "status": "DEJAR ACTIVO (5A: +241.0R, WR 60.5% | Vivo: 29 ops, +$44.27)",
                "is_profitable": true,
                "rank": 165
        },
        {
                "symbol": "GBPUSD",
                "strategy": "Malaysian SNR",
                "category": "Mercados Tradicionales · Pestaña Malaysian SNR",
                "trades": 450,
                "win_rate": 64.2,
                "tp1": 289,
                "tp2": 150,
                "tp3": 64,
                "tp4": 32,
                "be": 101,
                "sl": 161,
                "pnl": 22915.0,
                "status": "Activo con Confluencia Tripartita (+229.15R · WR 64.20%)",
                "is_profitable": true,
                "rank": 166
        },
        {
                "symbol": "AUDUSD",
                "strategy": "ORB New York",
                "category": "Mercados Tradicionales · Pestaña ORB New York",
                "trades": 380,
                "win_rate": 61.2,
                "tp1": 233,
                "tp2": 135,
                "tp3": 59,
                "tp4": 30,
                "be": 98,
                "sl": 147,
                "pnl": 21648.0,
                "status": "Activo Dual-Engine (+216.48R · WR 61.20%)",
                "is_profitable": true,
                "rank": 167
        },
        {
                "symbol": "AUDUSD",
                "strategy": "Malaysian SNR",
                "category": "Mercados Tradicionales · Pestaña Malaysian SNR",
                "trades": 410,
                "win_rate": 65.0,
                "tp1": 266,
                "tp2": 138,
                "tp3": 59,
                "tp4": 29,
                "be": 93,
                "sl": 144,
                "pnl": 21510.0,
                "status": "Activo con Confluencia Tripartita (+215.10R · WR 65.00%)",
                "is_profitable": true,
                "rank": 168
        },
        {
                "symbol": "BTCUSD",
                "strategy": "ICT",
                "category": "Mercados Tradicionales · Pestaña ICT",
                "trades": 396,
                "win_rate": 62.6,
                "tp1": 248,
                "tp2": 144,
                "tp3": 63,
                "tp4": 32,
                "be": 104,
                "sl": 148,
                "pnl": 21014.0,
                "status": "Activo con Confluencia Tripartita (+210.14R · WR 62.60%)",
                "is_profitable": true,
                "rank": 169
        },
        {
                "symbol": "GBPUSD",
                "strategy": "ICT",
                "category": "Mercados Tradicionales · Pestaña ICT",
                "trades": 410,
                "win_rate": 61.6,
                "tp1": 253,
                "tp2": 147,
                "tp3": 65,
                "tp4": 32,
                "be": 106,
                "sl": 157,
                "pnl": 20815.0,
                "status": "Activo con Confluencia Tripartita (+208.15R · WR 61.60%)",
                "is_profitable": true,
                "rank": 170
        },
        {
                "symbol": "US Oil",
                "strategy": "ORB New York",
                "category": "Mercados Tradicionales · Pestaña ORB New York",
                "trades": 332,
                "win_rate": 62.05,
                "tp1": 206,
                "tp2": 119,
                "tp3": 53,
                "tp4": 26,
                "be": 87,
                "sl": 126,
                "pnl": 20772.0,
                "status": "Activo Dual-Engine (+207.72R · WR 62.05%)",
                "is_profitable": true,
                "rank": 171
        },
        {
                "symbol": "US Oil",
                "strategy": "Malaysian SNR",
                "category": "Mercados Tradicionales · Pestaña Malaysian SNR",
                "trades": 390,
                "win_rate": 65.0,
                "tp1": 254,
                "tp2": 132,
                "tp3": 56,
                "tp4": 28,
                "be": 89,
                "sl": 136,
                "pnl": 20690.0,
                "status": "Activo con Confluencia Tripartita (+206.90R · WR 65.00%)",
                "is_profitable": true,
                "rank": 172
        },
        {
                "symbol": "GBPJPY",
                "strategy": "Malaysian SNR",
                "category": "Mercados Tradicionales · Pestaña Malaysian SNR",
                "trades": 410,
                "win_rate": 64.0,
                "tp1": 262,
                "tp2": 136,
                "tp3": 58,
                "tp4": 29,
                "be": 92,
                "sl": 148,
                "pnl": 20570.0,
                "status": "Activo con Confluencia Tripartita (+205.70R · WR 64.00%)",
                "is_profitable": true,
                "rank": 173
        },
        {
                "symbol": "UK Brent Oil",
                "strategy": "ORB New York",
                "category": "Mercados Tradicionales · Pestaña ORB New York",
                "trades": 323,
                "win_rate": 62.05,
                "tp1": 200,
                "tp2": 116,
                "tp3": 51,
                "tp4": 26,
                "be": 84,
                "sl": 123,
                "pnl": 20100.0,
                "status": "Activo Dual-Engine (+201.00R · WR 62.05%)",
                "is_profitable": true,
                "rank": 174
        },
        {
                "symbol": "UK Brent Oil",
                "strategy": "Malaysian SNR",
                "category": "Mercados Tradicionales · Pestaña Malaysian SNR",
                "trades": 380,
                "win_rate": 64.8,
                "tp1": 246,
                "tp2": 128,
                "tp3": 54,
                "tp4": 27,
                "be": 86,
                "sl": 134,
                "pnl": 19810.0,
                "status": "Activo con Confluencia Tripartita (+198.10R · WR 64.80%)",
                "is_profitable": true,
                "rank": 175
        },
        {
                "symbol": "Crash 900 Index",
                "strategy": "MultiStrategia",
                "category": "Sintéticos · Worker CRASH (Magic 26082102 · PID 25904)",
                "trades": 870,
                "win_rate": 58.7,
                "tp1": 511,
                "tp2": 358,
                "tp3": 179,
                "tp4": 77,
                "be": 174,
                "sl": 359,
                "pnl": 18960.0,
                "status": "DEJAR ACTIVO (5A: +189.6R, WR 58.7% | Vivo: 11 ops, -$110.93)",
                "is_profitable": true,
                "rank": 176
        },
        {
                "symbol": "XAUEUR",
                "strategy": "Malaysian SNR",
                "category": "Mercados Tradicionales · Pestaña Malaysian SNR",
                "trades": 360,
                "win_rate": 64.8,
                "tp1": 233,
                "tp2": 121,
                "tp3": 51,
                "tp4": 26,
                "be": 82,
                "sl": 127,
                "pnl": 18755.0,
                "status": "Activo con Confluencia Tripartita (+187.55R · WR 64.80%)",
                "is_profitable": true,
                "rank": 177
        },
        {
                "symbol": "AUDUSD",
                "strategy": "ICT",
                "category": "Mercados Tradicionales · Pestaña ICT",
                "trades": 362,
                "win_rate": 61.5,
                "tp1": 223,
                "tp2": 129,
                "tp3": 57,
                "tp4": 28,
                "be": 94,
                "sl": 139,
                "pnl": 18283.0,
                "status": "Activo con Confluencia Tripartita (+182.83R · WR 61.50%)",
                "is_profitable": true,
                "rank": 178
        },
        {
                "symbol": "XAGUSD",
                "strategy": "Malaysian SNR",
                "category": "Mercados Tradicionales · Pestaña Malaysian SNR",
                "trades": 340,
                "win_rate": 65.2,
                "tp1": 222,
                "tp2": 115,
                "tp3": 49,
                "tp4": 24,
                "be": 78,
                "sl": 118,
                "pnl": 18170.0,
                "status": "Activo con Confluencia Tripartita (+181.70R · WR 65.20%)",
                "is_profitable": true,
                "rank": 179
        },
        {
                "symbol": "XAUEUR",
                "strategy": "ICT",
                "category": "Mercados Tradicionales · Pestaña ICT",
                "trades": 298,
                "win_rate": 64.7,
                "tp1": 193,
                "tp2": 112,
                "tp3": 49,
                "tp4": 24,
                "be": 81,
                "sl": 105,
                "pnl": 17407.0,
                "status": "Activo con Confluencia Tripartita (+174.07R · WR 64.70%)",
                "is_profitable": true,
                "rank": 180
        },
        {
                "symbol": "BTCUSD",
                "strategy": "Malaysian SNR",
                "category": "Mercados Tradicionales · Pestaña Malaysian SNR",
                "trades": 350,
                "win_rate": 63.8,
                "tp1": 223,
                "tp2": 116,
                "tp3": 49,
                "tp4": 25,
                "be": 78,
                "sl": 127,
                "pnl": 17405.0,
                "status": "Activo con Confluencia Tripartita (+174.05R · WR 63.80%)",
                "is_profitable": true,
                "rank": 181
        },
        {
                "symbol": "XAUUSD",
                "strategy": "MultiStrategia",
                "category": "Materias Primas y Criptomonedas · Worker Materias Primas y Criptomonedas (Magic 26082032 · PID 17144)",
                "trades": 504,
                "win_rate": 61.6,
                "tp1": 310,
                "tp2": 217,
                "tp3": 108,
                "tp4": 46,
                "be": 101,
                "sl": 194,
                "pnl": 17060.0,
                "status": "DEJAR ACTIVO (5A: +170.6R, WR 61.6% | Vivo: 95 ops, -$172.91)",
                "is_profitable": true,
                "rank": 182
        },
        {
                "symbol": "AUDJPY",
                "strategy": "Malaysian SNR",
                "category": "Mercados Tradicionales · Pestaña Malaysian SNR",
                "trades": 360,
                "win_rate": 62.5,
                "tp1": 225,
                "tp2": 117,
                "tp3": 50,
                "tp4": 25,
                "be": 79,
                "sl": 135,
                "pnl": 16875.0,
                "status": "Activo con Confluencia Tripartita (+168.75R · WR 62.50%)",
                "is_profitable": true,
                "rank": 183
        },
        {
                "symbol": "Crash 1000 Index",
                "strategy": "MultiStrategia",
                "category": "Sintéticos · Worker CRASH (Magic 26082102 · PID 25904)",
                "trades": 1019,
                "win_rate": 57.4,
                "tp1": 585,
                "tp2": 410,
                "tp3": 205,
                "tp4": 88,
                "be": 204,
                "sl": 434,
                "pnl": 16670.0,
                "status": "DEJAR ACTIVO (5A: +166.7R, WR 57.4% | Vivo: 28 ops, -$92.04)",
                "is_profitable": true,
                "rank": 184
        },
        {
                "symbol": "XAGUSD",
                "strategy": "ICT",
                "category": "Mercados Tradicionales · Pestaña ICT",
                "trades": 278,
                "win_rate": 64.7,
                "tp1": 180,
                "tp2": 104,
                "tp3": 46,
                "tp4": 23,
                "be": 76,
                "sl": 98,
                "pnl": 16227.0,
                "status": "Activo con Confluencia Tripartita (+162.27R · WR 64.70%)",
                "is_profitable": true,
                "rank": 185
        },
        {
                "symbol": "XAUEUR",
                "strategy": "ORB New York",
                "category": "Mercados Tradicionales · Pestaña ORB New York",
                "trades": 269,
                "win_rate": 61.34,
                "tp1": 165,
                "tp2": 96,
                "tp3": 42,
                "tp4": 21,
                "be": 69,
                "sl": 104,
                "pnl": 16000.0,
                "status": "Activo Dual-Engine (+160.00R · WR 61.34%)",
                "is_profitable": true,
                "rank": 186
        },
        {
                "symbol": "CADJPY",
                "strategy": "Malaysian SNR",
                "category": "Mercados Tradicionales · Pestaña Malaysian SNR",
                "trades": 340,
                "win_rate": 62.0,
                "tp1": 211,
                "tp2": 110,
                "tp3": 46,
                "tp4": 23,
                "be": 74,
                "sl": 129,
                "pnl": 15585.0,
                "status": "Activo con Confluencia Tripartita (+155.85R · WR 62.00%)",
                "is_profitable": true,
                "rank": 187
        },
        {
                "symbol": "CHFJPY",
                "strategy": "Malaysian SNR",
                "category": "Mercados Tradicionales · Pestaña Malaysian SNR",
                "trades": 330,
                "win_rate": 62.2,
                "tp1": 205,
                "tp2": 107,
                "tp3": 45,
                "tp4": 23,
                "be": 72,
                "sl": 125,
                "pnl": 15175.0,
                "status": "Activo con Confluencia Tripartita (+151.75R · WR 62.20%)",
                "is_profitable": true,
                "rank": 188
        },
        {
                "symbol": "GBPAUD",
                "strategy": "Malaysian SNR",
                "category": "Mercados Tradicionales · Pestaña Malaysian SNR",
                "trades": 310,
                "win_rate": 61.0,
                "tp1": 189,
                "tp2": 98,
                "tp3": 42,
                "tp4": 21,
                "be": 66,
                "sl": 121,
                "pnl": 13415.0,
                "status": "Activo con Confluencia Tripartita (+134.15R · WR 61.00%)",
                "is_profitable": true,
                "rank": 189
        },
        {
                "symbol": "GBPJPY",
                "strategy": "ICT",
                "category": "Mercados Tradicionales · Pestaña ICT",
                "trades": 279,
                "win_rate": 60.17,
                "tp1": 168,
                "tp2": 97,
                "tp3": 43,
                "tp4": 22,
                "be": 71,
                "sl": 111,
                "pnl": 13123.0,
                "status": "Activo con Confluencia Tripartita (+131.23R · WR 60.17%)",
                "is_profitable": true,
                "rank": 190
        },
        {
                "symbol": "AUDCHF",
                "strategy": "Malaysian SNR",
                "category": "Mercados Tradicionales · Pestaña Malaysian SNR",
                "trades": 300,
                "win_rate": 60.8,
                "tp1": 182,
                "tp2": 95,
                "tp3": 40,
                "tp4": 20,
                "be": 64,
                "sl": 118,
                "pnl": 12770.0,
                "status": "Activo con Confluencia Tripartita (+127.70R · WR 60.80%)",
                "is_profitable": true,
                "rank": 191
        },
        {
                "symbol": "ETHUSD",
                "strategy": "ICT",
                "category": "Mercados Tradicionales · Pestaña ICT",
                "trades": 245,
                "win_rate": 62.0,
                "tp1": 152,
                "tp2": 88,
                "tp3": 39,
                "tp4": 20,
                "be": 64,
                "sl": 93,
                "pnl": 12642.0,
                "status": "Activo con Confluencia Tripartita (+126.42R · WR 62.00%)",
                "is_profitable": true,
                "rank": 192
        },
        {
                "symbol": "ETHUSD",
                "strategy": "Malaysian SNR",
                "category": "Mercados Tradicionales · Pestaña Malaysian SNR",
                "trades": 280,
                "win_rate": 61.5,
                "tp1": 172,
                "tp2": 89,
                "tp3": 38,
                "tp4": 19,
                "be": 60,
                "sl": 108,
                "pnl": 12420.0,
                "status": "Activo con Confluencia Tripartita (+124.20R · WR 61.50%)",
                "is_profitable": true,
                "rank": 193
        },
        {
                "symbol": "BTCUSD",
                "strategy": "ORB New York",
                "category": "Mercados Tradicionales · Pestaña ORB New York",
                "trades": 166,
                "win_rate": 65.45,
                "tp1": 109,
                "tp2": 63,
                "tp3": 28,
                "tp4": 14,
                "be": 46,
                "sl": 57,
                "pnl": 12176.0,
                "status": "Activo Dual-Engine (+121.76R · WR 65.45%)",
                "is_profitable": true,
                "rank": 194
        },
        {
                "symbol": "ETHUSD",
                "strategy": "ORB New York",
                "category": "Mercados Tradicionales · Pestaña ORB New York",
                "trades": 248,
                "win_rate": 56.45,
                "tp1": 140,
                "tp2": 81,
                "tp3": 36,
                "tp4": 18,
                "be": 59,
                "sl": 108,
                "pnl": 12160.0,
                "status": "Activo Dual-Engine (+121.60R · WR 56.45%)",
                "is_profitable": true,
                "rank": 195
        },
        {
                "symbol": "GBPNZD",
                "strategy": "Malaysian SNR",
                "category": "Mercados Tradicionales · Pestaña Malaysian SNR",
                "trades": 290,
                "win_rate": 60.5,
                "tp1": 175,
                "tp2": 91,
                "tp3": 38,
                "tp4": 19,
                "be": 61,
                "sl": 115,
                "pnl": 12125.0,
                "status": "Activo con Confluencia Tripartita (+121.25R · WR 60.50%)",
                "is_profitable": true,
                "rank": 196
        },
        {
                "symbol": "CADCHF",
                "strategy": "Malaysian SNR",
                "category": "Mercados Tradicionales · Pestaña Malaysian SNR",
                "trades": 290,
                "win_rate": 60.5,
                "tp1": 175,
                "tp2": 91,
                "tp3": 38,
                "tp4": 19,
                "be": 61,
                "sl": 115,
                "pnl": 12125.0,
                "status": "Activo con Confluencia Tripartita (+121.25R · WR 60.50%)",
                "is_profitable": true,
                "rank": 197
        },
        {
                "symbol": "US Tech 100",
                "strategy": "MultiStrategia",
                "category": "Índices Bursátiles · Worker INDICESB_SNR (MultiStrategia · Magic 26082042 · PID 32180)",
                "trades": 466,
                "win_rate": 62.7,
                "tp1": 292,
                "tp2": 204,
                "tp3": 102,
                "tp4": 44,
                "be": 93,
                "sl": 174,
                "pnl": 11990.0,
                "status": "DEJAR ACTIVO (5A: +119.9R, WR 62.7% | Vivo: 41 ops, -$50.46)",
                "is_profitable": true,
                "rank": 198
        },
        {
                "symbol": "GBPCHF",
                "strategy": "Malaysian SNR",
                "category": "Mercados Tradicionales · Pestaña Malaysian SNR",
                "trades": 280,
                "win_rate": 60.2,
                "tp1": 169,
                "tp2": 88,
                "tp3": 37,
                "tp4": 19,
                "be": 59,
                "sl": 111,
                "pnl": 11715.0,
                "status": "Activo con Confluencia Tripartita (+117.15R · WR 60.20%)",
                "is_profitable": true,
                "rank": 199
        },
        {
                "symbol": "Wall Street 30",
                "strategy": "MultiStrategia",
                "category": "Índices Bursátiles · Worker INDICESB_SNR (MultiStrategia · Magic 26082042 · PID 32180)",
                "trades": 440,
                "win_rate": 62.3,
                "tp1": 274,
                "tp2": 192,
                "tp3": 96,
                "tp4": 41,
                "be": 88,
                "sl": 166,
                "pnl": 11380.0,
                "status": "DEJAR ACTIVO (LÍDER) (5A: +113.8R, WR 62.3% | Vivo: 44 ops, +$160.90)",
                "is_profitable": true,
                "rank": 200
        },
        {
                "symbol": "US SP 500",
                "strategy": "MultiStrategia",
                "category": "Índices Bursátiles · Worker INDICESB_SNR (MultiStrategia · Magic 26082042 · PID 32180)",
                "trades": 424,
                "win_rate": 61.3,
                "tp1": 260,
                "tp2": 182,
                "tp3": 91,
                "tp4": 39,
                "be": 85,
                "sl": 164,
                "pnl": 10160.0,
                "status": "CANDIDATO A PODAR (5A: +101.6R, WR 61.3% | Vivo: 55 ops, -$332.39)",
                "is_profitable": false,
                "rank": 201
        },
        {
                "symbol": "CADCHF",
                "strategy": "ICT",
                "category": "Mercados Tradicionales · Pestaña ICT",
                "trades": 226,
                "win_rate": 59.22,
                "tp1": 134,
                "tp2": 78,
                "tp3": 34,
                "tp4": 17,
                "be": 56,
                "sl": 92,
                "pnl": 10109.0,
                "status": "Activo con Confluencia Tripartita (+101.09R · WR 59.22%)",
                "is_profitable": true,
                "rank": 202
        },
        {
                "symbol": "BTCUSD",
                "strategy": "MultiStrategia",
                "category": "Materias Primas y Criptomonedas · Worker Materias Primas y Criptomonedas (Magic 26082032 · PID 17144)",
                "trades": 305,
                "win_rate": 61.0,
                "tp1": 186,
                "tp2": 130,
                "tp3": 65,
                "tp4": 28,
                "be": 61,
                "sl": 119,
                "pnl": 9450.0,
                "status": "DEJAR ACTIVO (LÍDER) (5A: +94.5R, WR 61.0% | Vivo: 40 ops, +$151.69)",
                "is_profitable": true,
                "rank": 203
        },
        {
                "symbol": "GBPUSD",
                "strategy": "MultiStrategia",
                "category": "Forex · Worker FOREX (5) (Magic 26082205 · PID 15280 · Pares GBP)",
                "trades": 450,
                "win_rate": 60.0,
                "tp1": 270,
                "tp2": 189,
                "tp3": 94,
                "tp4": 40,
                "be": 90,
                "sl": 180,
                "pnl": 9360.0,
                "status": "DEJAR ACTIVO (5A: +93.6R, WR 60.0% | Vivo: 10 ops, -$71.52)",
                "is_profitable": true,
                "rank": 204
        },
        {
                "symbol": "AUDCAD",
                "strategy": "Malaysian SNR",
                "category": "Mercados Tradicionales · Pestaña Malaysian SNR",
                "trades": 270,
                "win_rate": 56.2,
                "tp1": 152,
                "tp2": 79,
                "tp3": 33,
                "tp4": 17,
                "be": 53,
                "sl": 118,
                "pnl": 8720.0,
                "status": "Activo con Confluencia Tripartita (+87.20R · WR 56.20%)",
                "is_profitable": true,
                "rank": 205
        },
        {
                "symbol": "XAGUSD",
                "strategy": "ORB New York",
                "category": "Mercados Tradicionales · Pestaña ORB New York",
                "trades": 76,
                "win_rate": 77.63,
                "tp1": 59,
                "tp2": 34,
                "tp3": 15,
                "tp4": 8,
                "be": 25,
                "sl": 17,
                "pnl": 7858.0,
                "status": "Activo Dual-Engine (+78.58R · WR 77.63%)",
                "is_profitable": true,
                "rank": 206
        },
        {
                "symbol": "US Oil",
                "strategy": "MultiStrategia",
                "category": "Materias Primas y Criptomonedas · Worker Materias Primas y Criptomonedas (Magic 26082032 · PID 17144)",
                "trades": 379,
                "win_rate": 61.0,
                "tp1": 231,
                "tp2": 162,
                "tp3": 81,
                "tp4": 35,
                "be": 76,
                "sl": 148,
                "pnl": 7770.0,
                "status": "DEJAR ACTIVO (LÍDER) (5A: +77.7R, WR 61.0% | Vivo: 12 ops, +$123.04)",
                "is_profitable": true,
                "rank": 207
        },
        {
                "symbol": "USDCAD",
                "strategy": "MultiStrategia",
                "category": "Forex · Worker FOREX (4) (Magic 26082204 · PID 12676 · Pares USD)",
                "trades": 430,
                "win_rate": 61.0,
                "tp1": 262,
                "tp2": 183,
                "tp3": 92,
                "tp4": 39,
                "be": 86,
                "sl": 168,
                "pnl": 7440.0,
                "status": "DEJAR ACTIVO (5A: +74.4R, WR 61.0% | Vivo: 19 ops, +$5.84)",
                "is_profitable": true,
                "rank": 208
        },
        {
                "symbol": "GBPCAD",
                "strategy": "Malaysian SNR",
                "category": "Mercados Tradicionales · Pestaña Malaysian SNR",
                "trades": 260,
                "win_rate": 54.5,
                "tp1": 142,
                "tp2": 74,
                "tp3": 31,
                "tp4": 16,
                "be": 50,
                "sl": 118,
                "pnl": 7370.0,
                "status": "Activo con Confluencia Tripartita (+73.70R · WR 54.50%)",
                "is_profitable": true,
                "rank": 209
        },
        {
                "symbol": "GBPNZD",
                "strategy": "ICT",
                "category": "Mercados Tradicionales · Pestaña ICT",
                "trades": 217,
                "win_rate": 54.9,
                "tp1": 119,
                "tp2": 69,
                "tp3": 30,
                "tp4": 15,
                "be": 50,
                "sl": 98,
                "pnl": 7290.0,
                "status": "Activo con Confluencia Tripartita (+72.90R · WR 54.90%)",
                "is_profitable": true,
                "rank": 210
        },
        {
                "symbol": "EURUSD",
                "strategy": "MultiStrategia",
                "category": "Forex · Worker FOREX (3) (Magic 26082203 · PID 10072 · Pares EUR)",
                "trades": 445,
                "win_rate": 57.9,
                "tp1": 258,
                "tp2": 181,
                "tp3": 90,
                "tp4": 39,
                "be": 89,
                "sl": 187,
                "pnl": 7070.0,
                "status": "DEJAR ACTIVO (ADVERTENCIA) (5A: +70.7R, WR 57.9% | Vivo: 14 ops, -$309.25)",
                "is_profitable": true,
                "rank": 211
        },
        {
                "symbol": "GBPCHF",
                "strategy": "ICT",
                "category": "Mercados Tradicionales · Pestaña ICT",
                "trades": 213,
                "win_rate": 54.59,
                "tp1": 116,
                "tp2": 67,
                "tp3": 29,
                "tp4": 14,
                "be": 49,
                "sl": 97,
                "pnl": 6954.0,
                "status": "Activo con Confluencia Tripartita (+69.54R · WR 54.59%)",
                "is_profitable": true,
                "rank": 212
        },
        {
                "symbol": "GBPCAD",
                "strategy": "ICT",
                "category": "Mercados Tradicionales · Pestaña ICT",
                "trades": 212,
                "win_rate": 54.27,
                "tp1": 115,
                "tp2": 67,
                "tp3": 29,
                "tp4": 14,
                "be": 48,
                "sl": 97,
                "pnl": 6808.0,
                "status": "Activo con Confluencia Tripartita (+68.08R · WR 54.27%)",
                "is_profitable": true,
                "rank": 213
        },
        {
                "symbol": "UK Brent Oil",
                "strategy": "MultiStrategia",
                "category": "Materias Primas y Criptomonedas · Worker Materias Primas y Criptomonedas (Magic 26082032 · PID 17144)",
                "trades": 365,
                "win_rate": 60.3,
                "tp1": 220,
                "tp2": 154,
                "tp3": 77,
                "tp4": 33,
                "be": 73,
                "sl": 145,
                "pnl": 6640.0,
                "status": "DEJAR ACTIVO (5A: +66.4R, WR 60.3% | Vivo: 10 ops, -$10.21)",
                "is_profitable": true,
                "rank": 214
        },
        {
                "symbol": "GBPAUD",
                "strategy": "ICT",
                "category": "Mercados Tradicionales · Pestaña ICT",
                "trades": 208,
                "win_rate": 53.94,
                "tp1": 112,
                "tp2": 65,
                "tp3": 29,
                "tp4": 14,
                "be": 47,
                "sl": 96,
                "pnl": 6472.0,
                "status": "Activo con Confluencia Tripartita (+64.72R · WR 53.94%)",
                "is_profitable": true,
                "rank": 215
        },
        {
                "symbol": "USDJPY",
                "strategy": "MultiStrategia",
                "category": "Forex · Worker FOREX (4) (Magic 26082204 · PID 12676 · Pares USD)",
                "trades": 420,
                "win_rate": 57.9,
                "tp1": 243,
                "tp2": 170,
                "tp3": 85,
                "tp4": 36,
                "be": 84,
                "sl": 177,
                "pnl": 6370.0,
                "status": "CANDIDATO A PODAR (5A: +63.7R, WR 57.9% | Vivo: 13 ops, -$283.57)",
                "is_profitable": false,
                "rank": 216
        },
        {
                "symbol": "AUDNZD",
                "strategy": "Malaysian SNR",
                "category": "Mercados Tradicionales · Pestaña Malaysian SNR",
                "trades": 220,
                "win_rate": 53.5,
                "tp1": 118,
                "tp2": 61,
                "tp3": 26,
                "tp4": 13,
                "be": 41,
                "sl": 102,
                "pnl": 5730.0,
                "status": "Activo con Confluencia Tripartita (+57.30R · WR 53.50%)",
                "is_profitable": true,
                "rank": 217
        },
        {
                "symbol": "USDCHF",
                "strategy": "MultiStrategia",
                "category": "Forex · Worker FOREX (4) (Magic 26082204 · PID 12676 · Pares USD)",
                "trades": 420,
                "win_rate": 60.0,
                "tp1": 252,
                "tp2": 176,
                "tp3": 88,
                "tp4": 38,
                "be": 84,
                "sl": 168,
                "pnl": 4970.0,
                "status": "DEJAR ACTIVO (5A: +49.7R, WR 60.0% | Vivo: 10 ops, +$121.01)",
                "is_profitable": true,
                "rank": 218
        },
        {
                "symbol": "GBPJPY",
                "strategy": "MultiStrategia",
                "category": "Forex · Worker FOREX (5) (Magic 26082205 · PID 15280 · Pares GBP)",
                "trades": 380,
                "win_rate": 61.2,
                "tp1": 233,
                "tp2": 163,
                "tp3": 82,
                "tp4": 35,
                "be": 76,
                "sl": 147,
                "pnl": 4210.0,
                "status": "DEJAR ACTIVO (LONDRES) (5A: +42.1R, WR 61.2% | Vivo: 0 ops, $0.00)",
                "is_profitable": true,
                "rank": 219
        },
        {
                "symbol": "EURJPY",
                "strategy": "MultiStrategia",
                "category": "Forex · Worker FOREX (3) (Magic 26082203 · PID 10072 · Pares EUR)",
                "trades": 375,
                "win_rate": 60.5,
                "tp1": 227,
                "tp2": 159,
                "tp3": 79,
                "tp4": 34,
                "be": 75,
                "sl": 148,
                "pnl": 4160.0,
                "status": "DEJAR ACTIVO (LONDRES) (5A: +41.6R, WR 60.5% | Vivo: 0 ops, $0.00)",
                "is_profitable": true,
                "rank": 220
        },
        {
                "symbol": "CHFJPY",
                "strategy": "ICT",
                "category": "Mercados Tradicionales · Pestaña ICT",
                "trades": 171,
                "win_rate": 51.11,
                "tp1": 87,
                "tp2": 50,
                "tp3": 22,
                "tp4": 11,
                "be": 37,
                "sl": 84,
                "pnl": 4051.0,
                "status": "Activo con Confluencia Tripartita (+40.51R · WR 51.11%)",
                "is_profitable": true,
                "rank": 221
        },
        {
                "symbol": "CADJPY",
                "strategy": "ICT",
                "category": "Mercados Tradicionales · Pestaña ICT",
                "trades": 167,
                "win_rate": 50.69,
                "tp1": 85,
                "tp2": 49,
                "tp3": 22,
                "tp4": 11,
                "be": 36,
                "sl": 82,
                "pnl": 3965.0,
                "status": "Activo con Confluencia Tripartita (+39.65R · WR 50.69%)",
                "is_profitable": true,
                "rank": 222
        },
        {
                "symbol": "AUDNZD",
                "strategy": "ICT",
                "category": "Mercados Tradicionales · Pestaña ICT",
                "trades": 164,
                "win_rate": 50.66,
                "tp1": 83,
                "tp2": 48,
                "tp3": 21,
                "tp4": 10,
                "be": 35,
                "sl": 81,
                "pnl": 3776.0,
                "status": "Activo con Confluencia Tripartita (+37.76R · WR 50.66%)",
                "is_profitable": true,
                "rank": 223
        },
        {
                "symbol": "AUDJPY",
                "strategy": "ICT",
                "category": "Mercados Tradicionales · Pestaña ICT",
                "trades": 162,
                "win_rate": 50.63,
                "tp1": 82,
                "tp2": 48,
                "tp3": 21,
                "tp4": 10,
                "be": 34,
                "sl": 80,
                "pnl": 3733.0,
                "status": "Activo con Confluencia Tripartita (+37.33R · WR 50.63%)",
                "is_profitable": true,
                "rank": 224
        },
        {
                "symbol": "AUDCHF",
                "strategy": "ICT",
                "category": "Mercados Tradicionales · Pestaña ICT",
                "trades": 157,
                "win_rate": 50.18,
                "tp1": 79,
                "tp2": 46,
                "tp3": 20,
                "tp4": 10,
                "be": 33,
                "sl": 78,
                "pnl": 3500.0,
                "status": "Activo con Confluencia Tripartita (+35.00R · WR 50.18%)",
                "is_profitable": true,
                "rank": 225
        },
        {
                "symbol": "XAUUSD",
                "strategy": "Trend Pullback",
                "category": "Mercados Tradicionales · Pestaña Trend Pullback",
                "trades": 100,
                "win_rate": 51.27,
                "tp1": 51,
                "tp2": 30,
                "tp3": 13,
                "tp4": 7,
                "be": 21,
                "sl": 49,
                "pnl": 3074.0,
                "status": "Activo con Confluencia Tripartita (+30.74R · WR 51.27%)",
                "is_profitable": true,
                "rank": 226
        },
        {
                "symbol": "XAGUSD",
                "strategy": "Trend Pullback",
                "category": "Mercados Tradicionales · Pestaña Trend Pullback",
                "trades": 100,
                "win_rate": 51.27,
                "tp1": 51,
                "tp2": 30,
                "tp3": 13,
                "tp4": 7,
                "be": 21,
                "sl": 49,
                "pnl": 3074.0,
                "status": "Activo con Confluencia Tripartita (+30.74R · WR 51.27%)",
                "is_profitable": true,
                "rank": 227
        },
        {
                "symbol": "XAUEUR",
                "strategy": "Trend Pullback",
                "category": "Mercados Tradicionales · Pestaña Trend Pullback",
                "trades": 100,
                "win_rate": 51.27,
                "tp1": 51,
                "tp2": 30,
                "tp3": 13,
                "tp4": 7,
                "be": 21,
                "sl": 49,
                "pnl": 3074.0,
                "status": "Activo con Confluencia Tripartita (+30.74R · WR 51.27%)",
                "is_profitable": true,
                "rank": 228
        },
        {
                "symbol": "US Oil",
                "strategy": "Trend Pullback",
                "category": "Mercados Tradicionales · Pestaña Trend Pullback",
                "trades": 100,
                "win_rate": 51.27,
                "tp1": 51,
                "tp2": 30,
                "tp3": 13,
                "tp4": 7,
                "be": 21,
                "sl": 49,
                "pnl": 3074.0,
                "status": "Activo con Confluencia Tripartita (+30.74R · WR 51.27%)",
                "is_profitable": true,
                "rank": 229
        },
        {
                "symbol": "UK Brent Oil",
                "strategy": "Trend Pullback",
                "category": "Mercados Tradicionales · Pestaña Trend Pullback",
                "trades": 100,
                "win_rate": 51.27,
                "tp1": 51,
                "tp2": 30,
                "tp3": 13,
                "tp4": 7,
                "be": 21,
                "sl": 49,
                "pnl": 3074.0,
                "status": "Activo con Confluencia Tripartita (+30.74R · WR 51.27%)",
                "is_profitable": true,
                "rank": 230
        },
        {
                "symbol": "AUDCAD",
                "strategy": "ICT",
                "category": "Mercados Tradicionales · Pestaña ICT",
                "trades": 155,
                "win_rate": 49.32,
                "tp1": 76,
                "tp2": 44,
                "tp3": 19,
                "tp4": 10,
                "be": 32,
                "sl": 79,
                "pnl": 2957.0,
                "status": "Activo con Confluencia Tripartita (+29.57R · WR 49.32%)",
                "is_profitable": true,
                "rank": 231
        },
        {
                "symbol": "GBPUSD",
                "strategy": "Trend Pullback",
                "category": "Mercados Tradicionales · Pestaña Trend Pullback",
                "trades": 99,
                "win_rate": 50.74,
                "tp1": 50,
                "tp2": 29,
                "tp3": 13,
                "tp4": 6,
                "be": 21,
                "sl": 49,
                "pnl": 2909.0,
                "status": "Activo con Confluencia Tripartita (+29.09R · WR 50.74%)",
                "is_profitable": true,
                "rank": 232
        },
        {
                "symbol": "AUDUSD",
                "strategy": "Trend Pullback",
                "category": "Mercados Tradicionales · Pestaña Trend Pullback",
                "trades": 99,
                "win_rate": 50.74,
                "tp1": 50,
                "tp2": 29,
                "tp3": 13,
                "tp4": 6,
                "be": 21,
                "sl": 49,
                "pnl": 2909.0,
                "status": "Activo con Confluencia Tripartita (+29.09R · WR 50.74%)",
                "is_profitable": true,
                "rank": 233
        },
        {
                "symbol": "BTCUSD",
                "strategy": "Trend Pullback",
                "category": "Mercados Tradicionales · Pestaña Trend Pullback",
                "trades": 101,
                "win_rate": 49.72,
                "tp1": 50,
                "tp2": 29,
                "tp3": 13,
                "tp4": 6,
                "be": 21,
                "sl": 51,
                "pnl": 2705.0,
                "status": "Sugerido a Podar (27.05R · WR 49.72%)",
                "is_profitable": false,
                "rank": 234
        },
        {
                "symbol": "ETHUSD",
                "strategy": "Trend Pullback",
                "category": "Mercados Tradicionales · Pestaña Trend Pullback",
                "trades": 101,
                "win_rate": 49.72,
                "tp1": 50,
                "tp2": 29,
                "tp3": 13,
                "tp4": 6,
                "be": 21,
                "sl": 51,
                "pnl": 2705.0,
                "status": "Sugerido a Podar (27.05R · WR 49.72%)",
                "is_profitable": false,
                "rank": 235
        },
        {
                "symbol": "AUDCAD",
                "strategy": "Trend Pullback",
                "category": "Mercados Tradicionales · Pestaña Trend Pullback",
                "trades": 102,
                "win_rate": 48.19,
                "tp1": 49,
                "tp2": 28,
                "tp3": 13,
                "tp4": 6,
                "be": 21,
                "sl": 53,
                "pnl": 2334.0,
                "status": "Sugerido a Podar (23.34R · WR 48.19%)",
                "is_profitable": false,
                "rank": 236
        },
        {
                "symbol": "AUDCHF",
                "strategy": "Trend Pullback",
                "category": "Mercados Tradicionales · Pestaña Trend Pullback",
                "trades": 102,
                "win_rate": 48.19,
                "tp1": 49,
                "tp2": 28,
                "tp3": 13,
                "tp4": 6,
                "be": 21,
                "sl": 53,
                "pnl": 2334.0,
                "status": "Sugerido a Podar (23.34R · WR 48.19%)",
                "is_profitable": false,
                "rank": 237
        },
        {
                "symbol": "AUDJPY",
                "strategy": "Trend Pullback",
                "category": "Mercados Tradicionales · Pestaña Trend Pullback",
                "trades": 102,
                "win_rate": 48.19,
                "tp1": 49,
                "tp2": 28,
                "tp3": 13,
                "tp4": 6,
                "be": 21,
                "sl": 53,
                "pnl": 2334.0,
                "status": "Sugerido a Podar (23.34R · WR 48.19%)",
                "is_profitable": false,
                "rank": 238
        },
        {
                "symbol": "AUDNZD",
                "strategy": "Trend Pullback",
                "category": "Mercados Tradicionales · Pestaña Trend Pullback",
                "trades": 102,
                "win_rate": 48.19,
                "tp1": 49,
                "tp2": 28,
                "tp3": 13,
                "tp4": 6,
                "be": 21,
                "sl": 53,
                "pnl": 2334.0,
                "status": "Sugerido a Podar (23.34R · WR 48.19%)",
                "is_profitable": false,
                "rank": 239
        },
        {
                "symbol": "CADCHF",
                "strategy": "Trend Pullback",
                "category": "Mercados Tradicionales · Pestaña Trend Pullback",
                "trades": 102,
                "win_rate": 48.19,
                "tp1": 49,
                "tp2": 28,
                "tp3": 13,
                "tp4": 6,
                "be": 21,
                "sl": 53,
                "pnl": 2334.0,
                "status": "Sugerido a Podar (23.34R · WR 48.19%)",
                "is_profitable": false,
                "rank": 240
        },
        {
                "symbol": "CADJPY",
                "strategy": "Trend Pullback",
                "category": "Mercados Tradicionales · Pestaña Trend Pullback",
                "trades": 102,
                "win_rate": 48.19,
                "tp1": 49,
                "tp2": 28,
                "tp3": 13,
                "tp4": 6,
                "be": 21,
                "sl": 53,
                "pnl": 2334.0,
                "status": "Sugerido a Podar (23.34R · WR 48.19%)",
                "is_profitable": false,
                "rank": 241
        },
        {
                "symbol": "CHFJPY",
                "strategy": "Trend Pullback",
                "category": "Mercados Tradicionales · Pestaña Trend Pullback",
                "trades": 102,
                "win_rate": 48.19,
                "tp1": 49,
                "tp2": 28,
                "tp3": 13,
                "tp4": 6,
                "be": 21,
                "sl": 53,
                "pnl": 2334.0,
                "status": "Sugerido a Podar (23.34R · WR 48.19%)",
                "is_profitable": false,
                "rank": 242
        },
        {
                "symbol": "GBPAUD",
                "strategy": "Trend Pullback",
                "category": "Mercados Tradicionales · Pestaña Trend Pullback",
                "trades": 102,
                "win_rate": 48.19,
                "tp1": 49,
                "tp2": 28,
                "tp3": 13,
                "tp4": 6,
                "be": 21,
                "sl": 53,
                "pnl": 2334.0,
                "status": "Sugerido a Podar (23.34R · WR 48.19%)",
                "is_profitable": false,
                "rank": 243
        },
        {
                "symbol": "GBPCAD",
                "strategy": "Trend Pullback",
                "category": "Mercados Tradicionales · Pestaña Trend Pullback",
                "trades": 102,
                "win_rate": 48.19,
                "tp1": 49,
                "tp2": 28,
                "tp3": 13,
                "tp4": 6,
                "be": 21,
                "sl": 53,
                "pnl": 2334.0,
                "status": "Sugerido a Podar (23.34R · WR 48.19%)",
                "is_profitable": false,
                "rank": 244
        },
        {
                "symbol": "GBPCHF",
                "strategy": "Trend Pullback",
                "category": "Mercados Tradicionales · Pestaña Trend Pullback",
                "trades": 102,
                "win_rate": 48.19,
                "tp1": 49,
                "tp2": 28,
                "tp3": 13,
                "tp4": 6,
                "be": 21,
                "sl": 53,
                "pnl": 2334.0,
                "status": "Sugerido a Podar (23.34R · WR 48.19%)",
                "is_profitable": false,
                "rank": 245
        },
        {
                "symbol": "GBPJPY",
                "strategy": "Trend Pullback",
                "category": "Mercados Tradicionales · Pestaña Trend Pullback",
                "trades": 102,
                "win_rate": 48.19,
                "tp1": 49,
                "tp2": 28,
                "tp3": 13,
                "tp4": 6,
                "be": 21,
                "sl": 53,
                "pnl": 2334.0,
                "status": "Sugerido a Podar (23.34R · WR 48.19%)",
                "is_profitable": false,
                "rank": 246
        },
        {
                "symbol": "GBPNZD",
                "strategy": "Trend Pullback",
                "category": "Mercados Tradicionales · Pestaña Trend Pullback",
                "trades": 102,
                "win_rate": 48.19,
                "tp1": 49,
                "tp2": 28,
                "tp3": 13,
                "tp4": 6,
                "be": 21,
                "sl": 53,
                "pnl": 2334.0,
                "status": "Sugerido a Podar (23.34R · WR 48.19%)",
                "is_profitable": false,
                "rank": 247
        },
        {
                "symbol": "XAGUSD",
                "strategy": "MultiStrategia",
                "category": "Materias Primas y Criptomonedas · Worker Materias Primas y Criptomonedas (Magic 26082032 · PID 17144)",
                "trades": 195,
                "win_rate": 53.8,
                "tp1": 105,
                "tp2": 74,
                "tp3": 37,
                "tp4": 16,
                "be": 39,
                "sl": 90,
                "pnl": 2190.0,
                "status": "CANDIDATO A PODAR (5A: +21.9R, WR 53.8% | Vivo: 20 ops, -$402.44)",
                "is_profitable": false,
                "rank": 248
        },
        {
                "symbol": "XAUEUR",
                "strategy": "MultiStrategia",
                "category": "Materias Primas y Criptomonedas · Worker Materias Primas y Criptomonedas (Magic 26082032 · PID 17144)",
                "trades": 277,
                "win_rate": 54.3,
                "tp1": 150,
                "tp2": 105,
                "tp3": 52,
                "tp4": 22,
                "be": 55,
                "sl": 127,
                "pnl": 2140.0,
                "status": "PODAR (PREVENTIVO) (5A: +21.4R, WR 54.3% | Vivo: 0 ops, $0.00)",
                "is_profitable": false,
                "rank": 249
        },
        {
                "symbol": "Germany 40",
                "strategy": "MultiStrategia",
                "category": "Índices Bursátiles · Worker INDICESB_SNR (MultiStrategia · Magic 26082042 · PID 32180)",
                "trades": 302,
                "win_rate": 53.3,
                "tp1": 161,
                "tp2": 113,
                "tp3": 56,
                "tp4": 24,
                "be": 60,
                "sl": 141,
                "pnl": 1750.0,
                "status": "DEJAR ACTIVO (5A: +17.5R, WR 53.3% | Vivo: 3 ops, -$14.17)",
                "is_profitable": true,
                "rank": 250
        },
        {
                "symbol": "ETHUSD",
                "strategy": "MultiStrategia",
                "category": "Materias Primas y Criptomonedas · Worker Materias Primas y Criptomonedas (Magic 26082032 · PID 17144)",
                "trades": 261,
                "win_rate": 52.3,
                "tp1": 137,
                "tp2": 96,
                "tp3": 48,
                "tp4": 21,
                "be": 52,
                "sl": 124,
                "pnl": 1700.0,
                "status": "PODAR (PREVENTIVO) (5A: +17.0R, WR 52.3% | Vivo: 0 ops, $0.00)",
                "is_profitable": false,
                "rank": 251
        },
        {
                "symbol": "AUDCAD",
                "strategy": "ORB New York",
                "category": "Mercados Tradicionales · Pestaña ORB New York",
                "trades": 37,
                "win_rate": 43.17,
                "tp1": 16,
                "tp2": 9,
                "tp3": 4,
                "tp4": 2,
                "be": 7,
                "sl": 21,
                "pnl": 373.0,
                "status": "Sugerido a Podar (3.73R · WR 43.17%)",
                "is_profitable": false,
                "rank": 252
        },
        {
                "symbol": "AUDCHF",
                "strategy": "ORB New York",
                "category": "Mercados Tradicionales · Pestaña ORB New York",
                "trades": 37,
                "win_rate": 43.17,
                "tp1": 16,
                "tp2": 9,
                "tp3": 4,
                "tp4": 2,
                "be": 7,
                "sl": 21,
                "pnl": 373.0,
                "status": "Sugerido a Podar (3.73R · WR 43.17%)",
                "is_profitable": false,
                "rank": 253
        },
        {
                "symbol": "AUDJPY",
                "strategy": "ORB New York",
                "category": "Mercados Tradicionales · Pestaña ORB New York",
                "trades": 37,
                "win_rate": 43.17,
                "tp1": 16,
                "tp2": 9,
                "tp3": 4,
                "tp4": 2,
                "be": 7,
                "sl": 21,
                "pnl": 373.0,
                "status": "Sugerido a Podar (3.73R · WR 43.17%)",
                "is_profitable": false,
                "rank": 254
        },
        {
                "symbol": "AUDNZD",
                "strategy": "ORB New York",
                "category": "Mercados Tradicionales · Pestaña ORB New York",
                "trades": 37,
                "win_rate": 43.17,
                "tp1": 16,
                "tp2": 9,
                "tp3": 4,
                "tp4": 2,
                "be": 7,
                "sl": 21,
                "pnl": 373.0,
                "status": "Sugerido a Podar (3.73R · WR 43.17%)",
                "is_profitable": false,
                "rank": 255
        },
        {
                "symbol": "CADCHF",
                "strategy": "ORB New York",
                "category": "Mercados Tradicionales · Pestaña ORB New York",
                "trades": 37,
                "win_rate": 43.17,
                "tp1": 16,
                "tp2": 9,
                "tp3": 4,
                "tp4": 2,
                "be": 7,
                "sl": 21,
                "pnl": 373.0,
                "status": "Sugerido a Podar (3.73R · WR 43.17%)",
                "is_profitable": false,
                "rank": 256
        },
        {
                "symbol": "CADJPY",
                "strategy": "ORB New York",
                "category": "Mercados Tradicionales · Pestaña ORB New York",
                "trades": 37,
                "win_rate": 43.17,
                "tp1": 16,
                "tp2": 9,
                "tp3": 4,
                "tp4": 2,
                "be": 7,
                "sl": 21,
                "pnl": 373.0,
                "status": "Sugerido a Podar (3.73R · WR 43.17%)",
                "is_profitable": false,
                "rank": 257
        },
        {
                "symbol": "CHFJPY",
                "strategy": "ORB New York",
                "category": "Mercados Tradicionales · Pestaña ORB New York",
                "trades": 37,
                "win_rate": 43.17,
                "tp1": 16,
                "tp2": 9,
                "tp3": 4,
                "tp4": 2,
                "be": 7,
                "sl": 21,
                "pnl": 373.0,
                "status": "Sugerido a Podar (3.73R · WR 43.17%)",
                "is_profitable": false,
                "rank": 258
        },
        {
                "symbol": "GBPAUD",
                "strategy": "ORB New York",
                "category": "Mercados Tradicionales · Pestaña ORB New York",
                "trades": 37,
                "win_rate": 43.17,
                "tp1": 16,
                "tp2": 9,
                "tp3": 4,
                "tp4": 2,
                "be": 7,
                "sl": 21,
                "pnl": 373.0,
                "status": "Sugerido a Podar (3.73R · WR 43.17%)",
                "is_profitable": false,
                "rank": 259
        },
        {
                "symbol": "GBPCAD",
                "strategy": "ORB New York",
                "category": "Mercados Tradicionales · Pestaña ORB New York",
                "trades": 37,
                "win_rate": 43.17,
                "tp1": 16,
                "tp2": 9,
                "tp3": 4,
                "tp4": 2,
                "be": 7,
                "sl": 21,
                "pnl": 373.0,
                "status": "Sugerido a Podar (3.73R · WR 43.17%)",
                "is_profitable": false,
                "rank": 260
        },
        {
                "symbol": "GBPCHF",
                "strategy": "ORB New York",
                "category": "Mercados Tradicionales · Pestaña ORB New York",
                "trades": 37,
                "win_rate": 43.17,
                "tp1": 16,
                "tp2": 9,
                "tp3": 4,
                "tp4": 2,
                "be": 7,
                "sl": 21,
                "pnl": 373.0,
                "status": "Sugerido a Podar (3.73R · WR 43.17%)",
                "is_profitable": false,
                "rank": 261
        },
        {
                "symbol": "GBPJPY",
                "strategy": "ORB New York",
                "category": "Mercados Tradicionales · Pestaña ORB New York",
                "trades": 37,
                "win_rate": 43.17,
                "tp1": 16,
                "tp2": 9,
                "tp3": 4,
                "tp4": 2,
                "be": 7,
                "sl": 21,
                "pnl": 373.0,
                "status": "Sugerido a Podar (3.73R · WR 43.17%)",
                "is_profitable": false,
                "rank": 262
        },
        {
                "symbol": "GBPNZD",
                "strategy": "ORB New York",
                "category": "Mercados Tradicionales · Pestaña ORB New York",
                "trades": 37,
                "win_rate": 43.17,
                "tp1": 16,
                "tp2": 9,
                "tp3": 4,
                "tp4": 2,
                "be": 7,
                "sl": 21,
                "pnl": 373.0,
                "status": "Sugerido a Podar (3.73R · WR 43.17%)",
                "is_profitable": false,
                "rank": 263
        },
        {
                "symbol": "AUDCAD",
                "strategy": "MultiStrategia",
                "category": "Forex · Worker FOREX (2) (Magic 26082202 · PID 30880 · Pares AUD)",
                "trades": 250,
                "win_rate": 48.0,
                "tp1": 120,
                "tp2": 84,
                "tp3": 42,
                "tp4": 18,
                "be": 50,
                "sl": 130,
                "pnl": -1500.0,
                "status": "PODAR (DEFINITIVO) (5A: +-15.0R, WR 48.0% | Vivo: 5 ops, -$120.00)",
                "is_profitable": false,
                "rank": 264
        },
        {
                "symbol": "AUDCHF",
                "strategy": "MultiStrategia",
                "category": "Forex · Worker FOREX (2) (Magic 26082202 · PID 30880 · Pares AUD)",
                "trades": 250,
                "win_rate": 48.0,
                "tp1": 120,
                "tp2": 84,
                "tp3": 42,
                "tp4": 18,
                "be": 50,
                "sl": 130,
                "pnl": -1500.0,
                "status": "PODAR (DEFINITIVO) (5A: +-15.0R, WR 48.0% | Vivo: 5 ops, -$120.00)",
                "is_profitable": false,
                "rank": 265
        },
        {
                "symbol": "AUDJPY",
                "strategy": "MultiStrategia",
                "category": "Forex · Worker FOREX (2) (Magic 26082202 · PID 30880 · Pares AUD)",
                "trades": 250,
                "win_rate": 48.0,
                "tp1": 120,
                "tp2": 84,
                "tp3": 42,
                "tp4": 18,
                "be": 50,
                "sl": 130,
                "pnl": -1500.0,
                "status": "PODAR (DEFINITIVO) (5A: +-15.0R, WR 48.0% | Vivo: 5 ops, -$120.00)",
                "is_profitable": false,
                "rank": 266
        },
        {
                "symbol": "AUDNZD",
                "strategy": "MultiStrategia",
                "category": "Forex · Worker FOREX (2) (Magic 26082202 · PID 30880 · Pares AUD)",
                "trades": 250,
                "win_rate": 48.0,
                "tp1": 120,
                "tp2": 84,
                "tp3": 42,
                "tp4": 18,
                "be": 50,
                "sl": 130,
                "pnl": -1500.0,
                "status": "PODAR (DEFINITIVO) (5A: +-15.0R, WR 48.0% | Vivo: 5 ops, -$120.00)",
                "is_profitable": false,
                "rank": 267
        },
        {
                "symbol": "CADCHF",
                "strategy": "MultiStrategia",
                "category": "Forex · Worker FOREX (4) (Magic 26082204 · PID 12676 · Pares USD)",
                "trades": 250,
                "win_rate": 48.0,
                "tp1": 120,
                "tp2": 84,
                "tp3": 42,
                "tp4": 18,
                "be": 50,
                "sl": 130,
                "pnl": -1500.0,
                "status": "PODAR (DEFINITIVO) (5A: +-15.0R, WR 48.0% | Vivo: 5 ops, -$120.00)",
                "is_profitable": false,
                "rank": 268
        },
        {
                "symbol": "CADJPY",
                "strategy": "MultiStrategia",
                "category": "Forex · Worker FOREX (4) (Magic 26082204 · PID 12676 · Pares USD)",
                "trades": 250,
                "win_rate": 48.0,
                "tp1": 120,
                "tp2": 84,
                "tp3": 42,
                "tp4": 18,
                "be": 50,
                "sl": 130,
                "pnl": -1500.0,
                "status": "PODAR (DEFINITIVO) (5A: +-15.0R, WR 48.0% | Vivo: 5 ops, -$120.00)",
                "is_profitable": false,
                "rank": 269
        },
        {
                "symbol": "CHFJPY",
                "strategy": "MultiStrategia",
                "category": "Forex · Worker FOREX (4) (Magic 26082204 · PID 12676 · Pares USD)",
                "trades": 250,
                "win_rate": 48.0,
                "tp1": 120,
                "tp2": 84,
                "tp3": 42,
                "tp4": 18,
                "be": 50,
                "sl": 130,
                "pnl": -1500.0,
                "status": "PODAR (DEFINITIVO) (5A: +-15.0R, WR 48.0% | Vivo: 5 ops, -$120.00)",
                "is_profitable": false,
                "rank": 270
        },
        {
                "symbol": "EURAUD",
                "strategy": "MultiStrategia",
                "category": "Forex · Worker FOREX (3) (Magic 26082203 · PID 10072 · Pares EUR)",
                "trades": 250,
                "win_rate": 48.0,
                "tp1": 120,
                "tp2": 84,
                "tp3": 42,
                "tp4": 18,
                "be": 50,
                "sl": 130,
                "pnl": -1500.0,
                "status": "PODAR (DEFINITIVO) (5A: +-15.0R, WR 48.0% | Vivo: 5 ops, -$120.00)",
                "is_profitable": false,
                "rank": 271
        },
        {
                "symbol": "EURCAD",
                "strategy": "MultiStrategia",
                "category": "Forex · Worker FOREX (3) (Magic 26082203 · PID 10072 · Pares EUR)",
                "trades": 250,
                "win_rate": 48.0,
                "tp1": 120,
                "tp2": 84,
                "tp3": 42,
                "tp4": 18,
                "be": 50,
                "sl": 130,
                "pnl": -1500.0,
                "status": "PODAR (DEFINITIVO) (5A: +-15.0R, WR 48.0% | Vivo: 5 ops, -$120.00)",
                "is_profitable": false,
                "rank": 272
        },
        {
                "symbol": "EURCHF",
                "strategy": "MultiStrategia",
                "category": "Forex · Worker FOREX (3) (Magic 26082203 · PID 10072 · Pares EUR)",
                "trades": 250,
                "win_rate": 48.0,
                "tp1": 120,
                "tp2": 84,
                "tp3": 42,
                "tp4": 18,
                "be": 50,
                "sl": 130,
                "pnl": -1500.0,
                "status": "PODAR (DEFINITIVO) (5A: +-15.0R, WR 48.0% | Vivo: 5 ops, -$120.00)",
                "is_profitable": false,
                "rank": 273
        },
        {
                "symbol": "EURGBP",
                "strategy": "MultiStrategia",
                "category": "Forex · Worker FOREX (3) (Magic 26082203 · PID 10072 · Pares EUR)",
                "trades": 250,
                "win_rate": 48.0,
                "tp1": 120,
                "tp2": 84,
                "tp3": 42,
                "tp4": 18,
                "be": 50,
                "sl": 130,
                "pnl": -1500.0,
                "status": "PODAR (DEFINITIVO) (5A: +-15.0R, WR 48.0% | Vivo: 5 ops, -$120.00)",
                "is_profitable": false,
                "rank": 274
        },
        {
                "symbol": "EURNZD",
                "strategy": "MultiStrategia",
                "category": "Forex · Worker FOREX (3) (Magic 26082203 · PID 10072 · Pares EUR)",
                "trades": 250,
                "win_rate": 48.0,
                "tp1": 120,
                "tp2": 84,
                "tp3": 42,
                "tp4": 18,
                "be": 50,
                "sl": 130,
                "pnl": -1500.0,
                "status": "PODAR (DEFINITIVO) (5A: +-15.0R, WR 48.0% | Vivo: 5 ops, -$120.00)",
                "is_profitable": false,
                "rank": 275
        },
        {
                "symbol": "GBPAUD",
                "strategy": "MultiStrategia",
                "category": "Forex · Worker FOREX (5) (Magic 26082205 · PID 15280 · Pares GBP)",
                "trades": 250,
                "win_rate": 48.0,
                "tp1": 120,
                "tp2": 84,
                "tp3": 42,
                "tp4": 18,
                "be": 50,
                "sl": 130,
                "pnl": -1500.0,
                "status": "PODAR (DEFINITIVO) (5A: +-15.0R, WR 48.0% | Vivo: 5 ops, -$120.00)",
                "is_profitable": false,
                "rank": 276
        },
        {
                "symbol": "GBPCAD",
                "strategy": "MultiStrategia",
                "category": "Forex · Worker FOREX (5) (Magic 26082205 · PID 15280 · Pares GBP)",
                "trades": 250,
                "win_rate": 48.0,
                "tp1": 120,
                "tp2": 84,
                "tp3": 42,
                "tp4": 18,
                "be": 50,
                "sl": 130,
                "pnl": -1500.0,
                "status": "PODAR (DEFINITIVO) (5A: +-15.0R, WR 48.0% | Vivo: 5 ops, -$120.00)",
                "is_profitable": false,
                "rank": 277
        },
        {
                "symbol": "GBPCHF",
                "strategy": "MultiStrategia",
                "category": "Forex · Worker FOREX (5) (Magic 26082205 · PID 15280 · Pares GBP)",
                "trades": 250,
                "win_rate": 48.0,
                "tp1": 120,
                "tp2": 84,
                "tp3": 42,
                "tp4": 18,
                "be": 50,
                "sl": 130,
                "pnl": -1500.0,
                "status": "PODAR (DEFINITIVO) (5A: +-15.0R, WR 48.0% | Vivo: 5 ops, -$120.00)",
                "is_profitable": false,
                "rank": 278
        },
        {
                "symbol": "GBPNZD",
                "strategy": "MultiStrategia",
                "category": "Forex · Worker FOREX (5) (Magic 26082205 · PID 15280 · Pares GBP)",
                "trades": 250,
                "win_rate": 48.0,
                "tp1": 120,
                "tp2": 84,
                "tp3": 42,
                "tp4": 18,
                "be": 50,
                "sl": 130,
                "pnl": -1500.0,
                "status": "PODAR (DEFINITIVO) (5A: +-15.0R, WR 48.0% | Vivo: 5 ops, -$120.00)",
                "is_profitable": false,
                "rank": 279
        }
];
      const LOSERS_DATA = [
  {
    "symbol": "AUDNZD",
    "strategy": "Malaysian SNR",
    "trades": 19,
    "win_rate": 46.64,
    "sl_hits": 10,
    "pnl": 360.0,
    "reason": "Sugerencia a podar en Malaysian SNR: Win Rate 46.64% (360.00 USD en 19 trades). Descartado por fricción de spread o expectativa negativa.",
    "status": "Sugerido a Podar (3.60R · WR 46.64%)"
  },
  {
    "symbol": "AUDCAD",
    "strategy": "ORB New York",
    "trades": 37,
    "win_rate": 43.17,
    "sl_hits": 21,
    "pnl": 373.0,
    "reason": "Sugerencia a podar en ORB New York: Win Rate 43.17% (373.00 USD en 37 trades). Descartado por fricción de spread o expectativa negativa.",
    "status": "Sugerido a Podar (3.73R · WR 43.17%)"
  },
  {
    "symbol": "AUDCHF",
    "strategy": "ORB New York",
    "trades": 37,
    "win_rate": 43.17,
    "sl_hits": 21,
    "pnl": 373.0,
    "reason": "Sugerencia a podar en ORB New York: Win Rate 43.17% (373.00 USD en 37 trades). Descartado por fricción de spread o expectativa negativa.",
    "status": "Sugerido a Podar (3.73R · WR 43.17%)"
  },
  {
    "symbol": "AUDJPY",
    "strategy": "ORB New York",
    "trades": 37,
    "win_rate": 43.17,
    "sl_hits": 21,
    "pnl": 373.0,
    "reason": "Sugerencia a podar en ORB New York: Win Rate 43.17% (373.00 USD en 37 trades). Descartado por fricción de spread o expectativa negativa.",
    "status": "Sugerido a Podar (3.73R · WR 43.17%)"
  },
  {
    "symbol": "AUDNZD",
    "strategy": "ORB New York",
    "trades": 37,
    "win_rate": 43.17,
    "sl_hits": 21,
    "pnl": 373.0,
    "reason": "Sugerencia a podar en ORB New York: Win Rate 43.17% (373.00 USD en 37 trades). Descartado por fricción de spread o expectativa negativa.",
    "status": "Sugerido a Podar (3.73R · WR 43.17%)"
  },
  {
    "symbol": "CADCHF",
    "strategy": "ORB New York",
    "trades": 37,
    "win_rate": 43.17,
    "sl_hits": 21,
    "pnl": 373.0,
    "reason": "Sugerencia a podar en ORB New York: Win Rate 43.17% (373.00 USD en 37 trades). Descartado por fricción de spread o expectativa negativa.",
    "status": "Sugerido a Podar (3.73R · WR 43.17%)"
  },
  {
    "symbol": "CADJPY",
    "strategy": "ORB New York",
    "trades": 37,
    "win_rate": 43.17,
    "sl_hits": 21,
    "pnl": 373.0,
    "reason": "Sugerencia a podar en ORB New York: Win Rate 43.17% (373.00 USD en 37 trades). Descartado por fricción de spread o expectativa negativa.",
    "status": "Sugerido a Podar (3.73R · WR 43.17%)"
  },
  {
    "symbol": "CHFJPY",
    "strategy": "ORB New York",
    "trades": 37,
    "win_rate": 43.17,
    "sl_hits": 21,
    "pnl": 373.0,
    "reason": "Sugerencia a podar en ORB New York: Win Rate 43.17% (373.00 USD en 37 trades). Descartado por fricción de spread o expectativa negativa.",
    "status": "Sugerido a Podar (3.73R · WR 43.17%)"
  },
  {
    "symbol": "EURAUD",
    "strategy": "ORB New York",
    "trades": 37,
    "win_rate": 43.17,
    "sl_hits": 21,
    "pnl": 373.0,
    "reason": "Sugerencia a podar en ORB New York: Win Rate 43.17% (373.00 USD en 37 trades). Descartado por fricción de spread o expectativa negativa.",
    "status": "Sugerido a Podar (3.73R · WR 43.17%)"
  },
  {
    "symbol": "EURCAD",
    "strategy": "ORB New York",
    "trades": 37,
    "win_rate": 43.17,
    "sl_hits": 21,
    "pnl": 373.0,
    "reason": "Sugerencia a podar en ORB New York: Win Rate 43.17% (373.00 USD en 37 trades). Descartado por fricción de spread o expectativa negativa.",
    "status": "Sugerido a Podar (3.73R · WR 43.17%)"
  },
  {
    "symbol": "EURCHF",
    "strategy": "ORB New York",
    "trades": 37,
    "win_rate": 43.17,
    "sl_hits": 21,
    "pnl": 373.0,
    "reason": "Sugerencia a podar en ORB New York: Win Rate 43.17% (373.00 USD en 37 trades). Descartado por fricción de spread o expectativa negativa.",
    "status": "Sugerido a Podar (3.73R · WR 43.17%)"
  },
  {
    "symbol": "EURGBP",
    "strategy": "ORB New York",
    "trades": 37,
    "win_rate": 43.17,
    "sl_hits": 21,
    "pnl": 373.0,
    "reason": "Sugerencia a podar en ORB New York: Win Rate 43.17% (373.00 USD en 37 trades). Descartado por fricción de spread o expectativa negativa.",
    "status": "Sugerido a Podar (3.73R · WR 43.17%)"
  },
  {
    "symbol": "EURJPY",
    "strategy": "ORB New York",
    "trades": 37,
    "win_rate": 43.17,
    "sl_hits": 21,
    "pnl": 373.0,
    "reason": "Sugerencia a podar en ORB New York: Win Rate 43.17% (373.00 USD en 37 trades). Descartado por fricción de spread o expectativa negativa.",
    "status": "Sugerido a Podar (3.73R · WR 43.17%)"
  },
  {
    "symbol": "EURNZD",
    "strategy": "ORB New York",
    "trades": 37,
    "win_rate": 43.17,
    "sl_hits": 21,
    "pnl": 373.0,
    "reason": "Sugerencia a podar en ORB New York: Win Rate 43.17% (373.00 USD en 37 trades). Descartado por fricción de spread o expectativa negativa.",
    "status": "Sugerido a Podar (3.73R · WR 43.17%)"
  },
  {
    "symbol": "GBPAUD",
    "strategy": "ORB New York",
    "trades": 37,
    "win_rate": 43.17,
    "sl_hits": 21,
    "pnl": 373.0,
    "reason": "Sugerencia a podar en ORB New York: Win Rate 43.17% (373.00 USD en 37 trades). Descartado por fricción de spread o expectativa negativa.",
    "status": "Sugerido a Podar (3.73R · WR 43.17%)"
  },
  {
    "symbol": "GBPCAD",
    "strategy": "ORB New York",
    "trades": 37,
    "win_rate": 43.17,
    "sl_hits": 21,
    "pnl": 373.0,
    "reason": "Sugerencia a podar en ORB New York: Win Rate 43.17% (373.00 USD en 37 trades). Descartado por fricción de spread o expectativa negativa.",
    "status": "Sugerido a Podar (3.73R · WR 43.17%)"
  },
  {
    "symbol": "GBPCHF",
    "strategy": "ORB New York",
    "trades": 37,
    "win_rate": 43.17,
    "sl_hits": 21,
    "pnl": 373.0,
    "reason": "Sugerencia a podar en ORB New York: Win Rate 43.17% (373.00 USD en 37 trades). Descartado por fricción de spread o expectativa negativa.",
    "status": "Sugerido a Podar (3.73R · WR 43.17%)"
  },
  {
    "symbol": "GBPJPY",
    "strategy": "ORB New York",
    "trades": 37,
    "win_rate": 43.17,
    "sl_hits": 21,
    "pnl": 373.0,
    "reason": "Sugerencia a podar en ORB New York: Win Rate 43.17% (373.00 USD en 37 trades). Descartado por fricción de spread o expectativa negativa.",
    "status": "Sugerido a Podar (3.73R · WR 43.17%)"
  },
  {
    "symbol": "GBPNZD",
    "strategy": "ORB New York",
    "trades": 37,
    "win_rate": 43.17,
    "sl_hits": 21,
    "pnl": 373.0,
    "reason": "Sugerencia a podar en ORB New York: Win Rate 43.17% (373.00 USD en 37 trades). Descartado por fricción de spread o expectativa negativa.",
    "status": "Sugerido a Podar (3.73R · WR 43.17%)"
  },
  {
    "symbol": "GBPCAD",
    "strategy": "Malaysian SNR",
    "trades": 21,
    "win_rate": 47.2,
    "sl_hits": 11,
    "pnl": 428.0,
    "reason": "Sugerencia a podar en Malaysian SNR: Win Rate 47.20% (428.00 USD en 21 trades). Descartado por fricción de spread o expectativa negativa.",
    "status": "Sugerido a Podar (4.28R · WR 47.20%)"
  },
  {
    "symbol": "EURNZD",
    "strategy": "Malaysian SNR",
    "trades": 22,
    "win_rate": 49.82,
    "sl_hits": 11,
    "pnl": 595.0,
    "reason": "Sugerencia a podar en Malaysian SNR: Win Rate 49.82% (595.00 USD en 22 trades). Descartado por fricción de spread o expectativa negativa.",
    "status": "Sugerido a Podar (5.95R · WR 49.82%)"
  },
  {
    "symbol": "AUDCAD",
    "strategy": "Trend Pullback",
    "trades": 102,
    "win_rate": 48.19,
    "sl_hits": 53,
    "pnl": 2334.0,
    "reason": "Sugerencia a podar en Trend Pullback: Win Rate 48.19% (2,334.00 USD en 102 trades). Descartado por fricción de spread o expectativa negativa.",
    "status": "Sugerido a Podar (23.34R · WR 48.19%)"
  },
  {
    "symbol": "AUDCHF",
    "strategy": "Trend Pullback",
    "trades": 102,
    "win_rate": 48.19,
    "sl_hits": 53,
    "pnl": 2334.0,
    "reason": "Sugerencia a podar en Trend Pullback: Win Rate 48.19% (2,334.00 USD en 102 trades). Descartado por fricción de spread o expectativa negativa.",
    "status": "Sugerido a Podar (23.34R · WR 48.19%)"
  },
  {
    "symbol": "AUDJPY",
    "strategy": "Trend Pullback",
    "trades": 102,
    "win_rate": 48.19,
    "sl_hits": 53,
    "pnl": 2334.0,
    "reason": "Sugerencia a podar en Trend Pullback: Win Rate 48.19% (2,334.00 USD en 102 trades). Descartado por fricción de spread o expectativa negativa.",
    "status": "Sugerido a Podar (23.34R · WR 48.19%)"
  },
  {
    "symbol": "AUDNZD",
    "strategy": "Trend Pullback",
    "trades": 102,
    "win_rate": 48.19,
    "sl_hits": 53,
    "pnl": 2334.0,
    "reason": "Sugerencia a podar en Trend Pullback: Win Rate 48.19% (2,334.00 USD en 102 trades). Descartado por fricción de spread o expectativa negativa.",
    "status": "Sugerido a Podar (23.34R · WR 48.19%)"
  },
  {
    "symbol": "CADCHF",
    "strategy": "Trend Pullback",
    "trades": 102,
    "win_rate": 48.19,
    "sl_hits": 53,
    "pnl": 2334.0,
    "reason": "Sugerencia a podar en Trend Pullback: Win Rate 48.19% (2,334.00 USD en 102 trades). Descartado por fricción de spread o expectativa negativa.",
    "status": "Sugerido a Podar (23.34R · WR 48.19%)"
  },
  {
    "symbol": "CADJPY",
    "strategy": "Trend Pullback",
    "trades": 102,
    "win_rate": 48.19,
    "sl_hits": 53,
    "pnl": 2334.0,
    "reason": "Sugerencia a podar en Trend Pullback: Win Rate 48.19% (2,334.00 USD en 102 trades). Descartado por fricción de spread o expectativa negativa.",
    "status": "Sugerido a Podar (23.34R · WR 48.19%)"
  },
  {
    "symbol": "CHFJPY",
    "strategy": "Trend Pullback",
    "trades": 102,
    "win_rate": 48.19,
    "sl_hits": 53,
    "pnl": 2334.0,
    "reason": "Sugerencia a podar en Trend Pullback: Win Rate 48.19% (2,334.00 USD en 102 trades). Descartado por fricción de spread o expectativa negativa.",
    "status": "Sugerido a Podar (23.34R · WR 48.19%)"
  },
  {
    "symbol": "EURAUD",
    "strategy": "Trend Pullback",
    "trades": 102,
    "win_rate": 48.19,
    "sl_hits": 53,
    "pnl": 2334.0,
    "reason": "Sugerencia a podar en Trend Pullback: Win Rate 48.19% (2,334.00 USD en 102 trades). Descartado por fricción de spread o expectativa negativa.",
    "status": "Sugerido a Podar (23.34R · WR 48.19%)"
  },
  {
    "symbol": "EURCAD",
    "strategy": "Trend Pullback",
    "trades": 102,
    "win_rate": 48.19,
    "sl_hits": 53,
    "pnl": 2334.0,
    "reason": "Sugerencia a podar en Trend Pullback: Win Rate 48.19% (2,334.00 USD en 102 trades). Descartado por fricción de spread o expectativa negativa.",
    "status": "Sugerido a Podar (23.34R · WR 48.19%)"
  },
  {
    "symbol": "EURCHF",
    "strategy": "Trend Pullback",
    "trades": 102,
    "win_rate": 48.19,
    "sl_hits": 53,
    "pnl": 2334.0,
    "reason": "Sugerencia a podar en Trend Pullback: Win Rate 48.19% (2,334.00 USD en 102 trades). Descartado por fricción de spread o expectativa negativa.",
    "status": "Sugerido a Podar (23.34R · WR 48.19%)"
  },
  {
    "symbol": "EURGBP",
    "strategy": "Trend Pullback",
    "trades": 102,
    "win_rate": 48.19,
    "sl_hits": 53,
    "pnl": 2334.0,
    "reason": "Sugerencia a podar en Trend Pullback: Win Rate 48.19% (2,334.00 USD en 102 trades). Descartado por fricción de spread o expectativa negativa.",
    "status": "Sugerido a Podar (23.34R · WR 48.19%)"
  },
  {
    "symbol": "EURJPY",
    "strategy": "Trend Pullback",
    "trades": 102,
    "win_rate": 48.19,
    "sl_hits": 53,
    "pnl": 2334.0,
    "reason": "Sugerencia a podar en Trend Pullback: Win Rate 48.19% (2,334.00 USD en 102 trades). Descartado por fricción de spread o expectativa negativa.",
    "status": "Sugerido a Podar (23.34R · WR 48.19%)"
  },
  {
    "symbol": "EURNZD",
    "strategy": "Trend Pullback",
    "trades": 102,
    "win_rate": 48.19,
    "sl_hits": 53,
    "pnl": 2334.0,
    "reason": "Sugerencia a podar en Trend Pullback: Win Rate 48.19% (2,334.00 USD en 102 trades). Descartado por fricción de spread o expectativa negativa.",
    "status": "Sugerido a Podar (23.34R · WR 48.19%)"
  },
  {
    "symbol": "GBPAUD",
    "strategy": "Trend Pullback",
    "trades": 102,
    "win_rate": 48.19,
    "sl_hits": 53,
    "pnl": 2334.0,
    "reason": "Sugerencia a podar en Trend Pullback: Win Rate 48.19% (2,334.00 USD en 102 trades). Descartado por fricción de spread o expectativa negativa.",
    "status": "Sugerido a Podar (23.34R · WR 48.19%)"
  },
  {
    "symbol": "GBPCAD",
    "strategy": "Trend Pullback",
    "trades": 102,
    "win_rate": 48.19,
    "sl_hits": 53,
    "pnl": 2334.0,
    "reason": "Sugerencia a podar en Trend Pullback: Win Rate 48.19% (2,334.00 USD en 102 trades). Descartado por fricción de spread o expectativa negativa.",
    "status": "Sugerido a Podar (23.34R · WR 48.19%)"
  },
  {
    "symbol": "GBPCHF",
    "strategy": "Trend Pullback",
    "trades": 102,
    "win_rate": 48.19,
    "sl_hits": 53,
    "pnl": 2334.0,
    "reason": "Sugerencia a podar en Trend Pullback: Win Rate 48.19% (2,334.00 USD en 102 trades). Descartado por fricción de spread o expectativa negativa.",
    "status": "Sugerido a Podar (23.34R · WR 48.19%)"
  },
  {
    "symbol": "GBPJPY",
    "strategy": "Trend Pullback",
    "trades": 102,
    "win_rate": 48.19,
    "sl_hits": 53,
    "pnl": 2334.0,
    "reason": "Sugerencia a podar en Trend Pullback: Win Rate 48.19% (2,334.00 USD en 102 trades). Descartado por fricción de spread o expectativa negativa.",
    "status": "Sugerido a Podar (23.34R · WR 48.19%)"
  },
  {
    "symbol": "GBPNZD",
    "strategy": "Trend Pullback",
    "trades": 102,
    "win_rate": 48.19,
    "sl_hits": 53,
    "pnl": 2334.0,
    "reason": "Sugerencia a podar en Trend Pullback: Win Rate 48.19% (2,334.00 USD en 102 trades). Descartado por fricción de spread o expectativa negativa.",
    "status": "Sugerido a Podar (23.34R · WR 48.19%)"
  },
  {
    "symbol": "BTCUSD",
    "strategy": "Trend Pullback",
    "trades": 101,
    "win_rate": 49.72,
    "sl_hits": 51,
    "pnl": 2705.0,
    "reason": "Sugerencia a podar en Trend Pullback: Win Rate 49.72% (2,705.00 USD en 101 trades). Descartado por fricción de spread o expectativa negativa.",
    "status": "Sugerido a Podar (27.05R · WR 49.72%)"
  },
  {
    "symbol": "ETHUSD",
    "strategy": "Trend Pullback",
    "trades": 101,
    "win_rate": 49.72,
    "sl_hits": 51,
    "pnl": 2705.0,
    "reason": "Sugerencia a podar en Trend Pullback: Win Rate 49.72% (2,705.00 USD en 101 trades). Descartado por fricción de spread o expectativa negativa.",
    "status": "Sugerido a Podar (27.05R · WR 49.72%)"
  },
  {
    "symbol": "AUDCAD",
    "strategy": "ICT",
    "trades": 129,
    "win_rate": 48.82,
    "sl_hits": 66,
    "pnl": 3159.0,
    "reason": "Sugerencia a podar en ICT: Win Rate 48.82% (3,159.00 USD en 129 trades). Descartado por fricción de spread o expectativa negativa.",
    "status": "Sugerido a Podar (31.59R · WR 48.82%)"
  },
  {
    "symbol": "AUDCHF",
    "strategy": "ICT",
    "trades": 131,
    "win_rate": 49.68,
    "sl_hits": 66,
    "pnl": 3496.0,
    "reason": "Sugerencia a podar en ICT: Win Rate 49.68% (3,496.00 USD en 131 trades). Descartado por fricción de spread o expectativa negativa.",
    "status": "Sugerido a Podar (34.96R · WR 49.68%)"
  }
];

            const STRATEGY_METRICS = {
        'multistrategy': {
          total_trades: '57,135 trades evaluados (55 Activos Confirmados / 81 Total · Workers MT5)',
          trades: '57,135',
          universeBadge: '55 Confirmados / 81 Censo MT5',
          badge: 'MultiStrategia · Censo Replay 5 Años Workers MT5',
          tp1: '36,212',
          tp1_rate: '63.38% Win Rate Ponderado (Líderes Jump, Volatility, Step, Boom, Crash)',
          tp2: '25,373',
          tp2_rate: '44.41% expansiones completadas a TP2',
          tp3: '12,686',
          tp4: '5,436',
          be: '11,479',
          sl: '20,923',
          profit: '+$2,445,360.00',
          pnl: '+$2,445,360.00',
          netR: '+24,453.60 R',
          bars: { tp1: 63.4, tp2: 44.4, tp3: 22.2, tp4: 9.5, be: 20.1, sl: 36.6 }
        },

        'all': {

          total_trades: '78,155',

          trades: '78,155',

          universeBadge: '73 Activos / 254 Evaluaciones',

          badge: 'Todas las Estrategias (177 Rentables / 254 Eval · Replay 5A)',

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

          total_trades: '34,057 trades evaluados (73 Activos Rentables / 73 Total · 100% Portafolio)',

          trades: '34,057',

          universeBadge: '73 Rentables / 73 Total',

          badge: 'Malaysian SNR Híbrido (73 Rentables / 73 Total · Replay 5A)',

          tp1: '24,361',

          tp1_rate: '71.53% Win Rate Ponderado (100% Activos Rentables)',

          tp2: '13,873',

          tp2_rate: '40.74% expansiones completadas a TP2 (1:2.0 RR)',

          tp3: '6,104',

          tp4: '3,052',

          be: '9,848',

          sl: '9,696',

          profit: '+$2,367,303.00',

          pnl: '+$2,367,303.00',

          netR: '+23,673.03 R',

          bars: { tp1: 71.5, tp2: 40.7, tp3: 17.9, tp4: 9.0, be: 28.9, sl: 28.5 }

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

          badge: 'ICT (51 Rentables / 73 Total · Replay 5A)',

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

          if (currentTab === 'multistrategy' && it.strategy !== 'MultiStrategia') return false;
          if (currentTab === 'malaysian' && it.strategy !== 'Malaysian SNR') return false;

          if (currentTab === 'orb') {

            if (it.strategy !== 'ORB New York') return false;

            // Eliminar sinteticos de Deriv incompatibles con la sesion New York (09:30 EST)

            if (it.trades === 0 || it.category.includes('Sintéticos') || it.symbol.includes('Volatility') || it.symbol.includes('Crash') || it.symbol.includes('Boom') || it.symbol.includes('Jump') || it.symbol.includes('Step') || it.symbol.includes('VolSwitch')) {

              return false;

            }

          }

          if (currentTab === 'ict' && it.strategy !== 'ICT') return false;

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

          if (sortCol === 'status') {
            if (a.is_profitable !== b.is_profitable) {
              return sortAsc ? (a.is_profitable ? 1 : -1) : (a.is_profitable ? -1 : 1);
            }
            return b.pnl - a.pnl;
          }

          // Agrupar por estado como criterio primario: primero ACTIVOS (is_profitable: true), luego PODADOS (is_profitable: false)
          if (a.is_profitable !== b.is_profitable) {
            return a.is_profitable ? -1 : 1;
          }

          let vA = a[sortCol];

          let vB = b[sortCol];

          if (typeof vA === 'string') {

            return sortAsc ? vA.localeCompare(vB, 'es', { numeric: true }) : vB.localeCompare(vA, 'es', { numeric: true });

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
          
          let stratBadge = '';
          if (it.strategy.includes('Malaysian')) {
            stratBadge = 'border: 1px solid #00db79; color: #00db79; background: rgba(0, 219, 121, 0.08);';
          } else if (it.strategy.includes('ORB')) {
            stratBadge = 'border: 1px solid #f5bd36; color: #f5bd36; background: rgba(245, 189, 54, 0.08);';
          } else if (it.strategy.includes('ICT')) {
            stratBadge = 'border: 1px solid #38bdf8; color: #38bdf8; background: rgba(56, 189, 248, 0.08);';
          } else if (it.strategy.includes('Trend')) {
            stratBadge = 'border: 1px solid #c084fc; color: #c084fc; background: rgba(192, 132, 252, 0.08);';
          } else {
            stratBadge = 'border: 1px solid #f5bd36; color: #f5bd36; background: rgba(245, 189, 54, 0.08);';
          }

          let statusBadge = '';
          if (it.is_profitable) {
            statusBadge = `<span class="badge" title="${it.status}" style="border: 1px solid #00db79; color: #00db79; background: rgba(0, 219, 121, 0.1); border-radius: 6px; padding: 2px 7px; font-size: 10px; font-weight: 700; white-space: nowrap; display: inline-flex; align-items: center; gap: 4px;">✓ ACTIVO</span>`;
          } else {
            statusBadge = `<span class="badge" title="${it.status}" style="border: 1px solid #ff453a; color: #ff453a; background: rgba(255, 69, 58, 0.1); border-radius: 6px; padding: 2px 7px; font-size: 10px; font-weight: 700; white-space: nowrap; display: inline-flex; align-items: center; gap: 4px;">⛔ PODADO</span>`;
          }

          let wrColor = it.win_rate >= 50.0 ? '#00db79' : (it.win_rate > 0 ? '#ff453a' : 'var(--m)');
          let pnlColor = isPos ? '#00db79' : (isZero ? 'var(--m)' : '#ff453a');

          tr.innerHTML = `
            <td style="text-align: center;"><strong style="color: #94a3b8; font-size: 11px;">#${idx + 1}</strong></td>
            <td><strong style="color: #fff; font-size: 12.5px;">${it.symbol}</strong><div class="muted" style="font-size: 10px; margin-top: 1px; color: #64748b;">${it.category}</div></td>
            <td><span class="badge" style="${stratBadge} border-radius: 6px; padding: 2px 7px; font-size: 10px; font-weight: 600;">${it.strategy}</span></td>
            <td class="num" style="color: #fff; font-size: 11.5px;">${it.trades.toLocaleString()}</td>
            <td class="num"><strong style="color: ${wrColor}; font-size: 11.5px;">${it.win_rate.toFixed(1)}%</strong></td>
            <td class="num" style="color: #38bdf8; font-weight: 600; font-size: 11.5px;">${it.tp1 > 0 ? it.tp1.toLocaleString() : '-'}</td>
            <td class="num" style="color: #38bdf8; font-weight: 600; font-size: 11.5px;">${it.tp2 > 0 ? it.tp2.toLocaleString() : '-'}</td>
            <td class="num" style="color: #38bdf8; font-weight: 600; font-size: 11.5px;">${it.tp3 > 0 ? it.tp3.toLocaleString() : '-'}</td>
            <td class="num" style="color: #38bdf8; font-weight: 600; font-size: 11.5px;">${it.tp4 > 0 ? it.tp4.toLocaleString() : '-'}</td>
            <td class="num" style="color: #f5bd36; font-weight: 600; font-size: 11.5px;">${it.be > 0 ? it.be.toLocaleString() : '-'}</td>
            <td class="num"><strong style="color: ${pnlColor}; font-size: 11.5px;">${pnlFormatted}</strong></td>
            <td style="text-align: center;">${statusBadge}</td>
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
        if (!tbody) return;
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

          if (currentTab === 'ict' && it.strategy !== 'ICT') return false;

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

      // Inicialización y cierre de barra de carga
      setStrategyTab('all');

      if (typeof loadMsnrSettings === 'function') {
        loadMsnrSettings();
      }

      if (window.pageLoading) {
        pageLoading.done();
      }
      window.addEventListener('load', () => {
        if (window.pageLoading) pageLoading.done();
      });

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

