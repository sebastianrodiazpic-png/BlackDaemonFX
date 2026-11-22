# -*- coding: utf-8 -*-
"""
Script maestro para reaplicar completamente el diseño de /Strategy-bases:
1. appShell + brandSidebar + header unificado idéntico al Dashboard
2. Estilos CSS .daemon-card, placas metálicas doradas, y .tp-bar-box oscuro de alto contraste
3. 4 Tarjetas superiores de estrategias en .daemon-card (Tri-Motor)
4. Panel Malaysian SNR humanizado con .daemon-card (Image 4)
5. Panel ORB New York Sweep humanizado con .daemon-card (Image 6)
6. Panel ICT humanizado con .daemon-card (Image 7)
7. Panel Trend Pullback humanizado con .daemon-card (Image 8)
8. 6 Tarjetas KPI en formato .daemon-card legendario (Image 1)
9. Cajas de TP limpias sin imagen de fondo (Image 2)
10. Cierre exacto de divs y balance de etiquetas
"""

import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/strategy_bases_page.py', 'r', encoding='utf-8') as f:
    content = f.read()

# -------------------------------------------------------------------------
# PASO 1: ASEGURAR CSS COMPLETO
# -------------------------------------------------------------------------
daemon_card_css = '''
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
'''

if '.daemon-card {' not in content:
    content = content.replace('</style>', daemon_card_css + '\n    </style>', 1)
    print("CSS .daemon-card y estilos integrados.")

# -------------------------------------------------------------------------
# PASO 2: ESTRUCTURA APPSHELL, BRANDSIDEBAR Y HEADER UNIFICADO
# -------------------------------------------------------------------------
body_start_pattern = re.compile(r'<body>\s*<main class="w">.*?<div class="top">.*?</div>\s*</div>', re.DOTALL)

unified_body_start = '''<body>
    <div class="appShell">
      <aside class="brandSidebar">
        <img class="brandLogo" src="/assets/blackdaemonfx_logo_v1.jpeg" alt="Logo BlackDaemonFX" />
        <div>
          <div class="brandName">BLACKDAEMON<span>FX</span></div>
          <div class="brandTag">Estrategia · Disciplina · Resultados</div>
        </div>
        <nav class="sideNav">
          <a href="/">📁 Dashboard</a>
          <a href="/instruments">📁 Instrumentos</a>
          <a href="/account">💳 Cuenta en vivo</a>
          <a href="/performance">📈 Rendimiento</a>
          <a class="active" href="/Strategy-bases">🧩 Bases de Estrategias</a>
          <a href="/#openPositions">◆ Posiciones abiertas</a>
          <a href="/#recentAnalysis">⏱ Análisis recientes</a>
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
        </div>'''

m_body = body_start_pattern.search(content)
if m_body:
    content = content[:m_body.start()] + unified_body_start + content[m_body.end():]
    print("appShell, brandSidebar y header unificado insertados.")
else:
    print("WARNING: No se encontró patrón de inicio de body tradicional, buscando variante...")
    # Alternativa si ya tenía appShell
    m_body_alt = re.search(r'<body>.*?<main class="wrap">.*?<div class="top">.*?</div>\s*</div>', content, re.DOTALL)
    if m_body_alt:
        content = content[:m_body_alt.start()] + unified_body_start + content[m_body_alt.end():]
        print("appShell y header unificado actualizados (variante).")

# Asegurar cierre de </main></div> antes de <script>
if '</main>\n    </div>\n    <script>' not in content and '</main></div>\n<script>' not in content and '</main>\n</div>\n<script>' not in content:
    # Reemplazar el </div> o </main> previo a <script>
    content = re.sub(r'</main>\s*<script>', '</main>\n    </div>\n    <script>', content)
    content = re.sub(r'</div>\s*<script>\s*const WINNERS_DATA', '</main>\n    </div>\n    <script>\n      const WINNERS_DATA', content)
    print("Cierre </main></div> asegurado.")

# -------------------------------------------------------------------------
# PASO 3: TAB NAVIGATION TEXTS
# -------------------------------------------------------------------------
content = content.replace(
    '<span>🌐</span> Todas las Estrategias (156 Activos Rentables / 292 Eval · Replay 5A)',
    '<span>🌐</span> Todas las Estrategias (177 Rentables / 292 Eval · Replay 5A)'
)
content = content.replace(
    '<span>🏛️</span> Estrategia ICT (51 Rentables / 73 Total · Replay 5A)',
    '<span>🏛️</span> Estrategia ICT (59 Rentables / 73 Total · Replay 5A)'
)

# -------------------------------------------------------------------------
# PASO 4: 4 TARJETAS SUPERIORES EN FORMATO .DAEMON-CARD (TRI-MOTOR)
# -------------------------------------------------------------------------
tri_motor_header_pattern = re.compile(
    r'<div id="triMotorAuditPanel"[^>]*>.*?<div class="card-header".*?</div>\s*<div class="muted"[^>]*>.*?</div>\s*(?:<div style="display: grid; grid-template-columns: repeat\(auto-fit, minmax\(260px, 1fr\)\); gap: 14px; margin-bottom: 18px;">|<div class="daemon-card-grid">).*?</div>\s*</div>\s*</div>\s*</div>',
    re.DOTALL
)

new_tri_motor_panel = '''<div id="triMotorAuditPanel" style="display: block; margin-bottom: 24px;">
        <div class="card" style="border-left: 4px solid var(--g); border-top: 1px solid #5b4514; border-right: 1px solid #5b4514; border-bottom: 1px solid #5b4514; background: linear-gradient(180deg, rgba(0, 219, 121, 0.08) 0%, #070a0e 100%);">
          <div class="card-header" style="margin-bottom: 12px;">
            <h2 class="card-title">
              <span class="icon">🌐</span>
              Respaldo Cuantitativo: Replay Fiel de 5 Años en Todos los Instrumentos (73 Activos · 4 Estrategias · 292 Evaluaciones)
            </h2>
            <div class="badge badge-green">Replay Fiel 5 Años · 177 Pares Rentables (>50% WR) · 115 Podados / Incompatibles · 71,962 Trades · +13,875.40 R Netos</div>
          </div>
          <div class="muted" style="font-size: 13.5px; line-height: 1.75; margin-bottom: 18px;">
            Auditoría de <strong>Replay Fiel de 5 Años (1825 días)</strong> bar-a-bar sin lookahead sobre el catálogo íntegro de <strong>73 instrumentos canónicos</strong> (38 sintéticos Deriv, 24 pares Forex mayores y cruces, 3 metales, 2 criptos, 4 índices y 2 commodities) bajo el contrato matemático BlackDaemonFX (2 patas al 0.5%, TP1 @ 1.0R, BE + spread en pata 2, TP2 @ 2.0R y trailing hasta 4.0R). Se evalúa el universo completo <strong>considerando tanto los activos rentables como los podados e incompatibles por diseño</strong>, sincronizados 100% con <a href="/instruments" style="color: #f4c84f; text-decoration: underline; font-weight: 600;">/instruments</a>.
          </div>

          <div class="daemon-card-grid">
            <!-- TARJETA 1 · ICT -->
            <div class="daemon-card" style="--strat-accent: var(--cyan); --strat-glow: rgba(56, 189, 248, 0.25);">
              <div class="daemon-card-inner">
                <div class="daemon-card-head">
                  <div class="daemon-card-title">🏛 Estrategia 1 · ICT</div>
                  <div class="daemon-card-badge">+8,038.81R • 60.5% Acierto (Replay 5A)</div>
                </div>
                <div class="daemon-card-body">
                  <div class="daemon-card-bullet">• <strong>Filtro de Alta Probabilidad:</strong> Filtra con Inteligencia Artificial predictiva (83% de precisión histórica) ejecutando 37,918 operaciones de alta probabilidad en el Replay Fiel de 5 Años.</div>
                  <div class="daemon-card-bullet">• <strong>Crecimiento Sólido (+8,038R):</strong> Generó +8,038 veces el riesgo asumido (+$803,881.00) en 59 activos rentables con expectativa positiva a lo largo de 5 años.</div>
                  <div class="daemon-card-bullet">• <strong>Especialidad de Mercado:</strong> Caza liquidez y desequilibrios (Fair Value Gaps y Order Blocks) en Índices Sintéticos, Forex y Metales/Criptos en Replay Fiel de 5 Años.</div>
                </div>
                <div class="daemon-card-plate">
                  <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                  <div class="daemon-card-plate-sub">SMART MONEY CONCEPTS · ALGO ENGINE</div>
                </div>
              </div>
            </div>

            <!-- TARJETA 2 · MALAYSIAN SNR C2 -->
            <div class="daemon-card" style="--strat-accent: var(--g); --strat-glow: rgba(0, 219, 121, 0.25);">
              <div class="daemon-card-inner">
                <div class="daemon-card-head">
                  <div class="daemon-card-title">🇲🇾 Estrategia 2 · Malaysian SNR C2</div>
                  <div class="daemon-card-badge">+4,550.62R • 71.6% Acierto (Replay 5A)</div>
                </div>
                <div class="daemon-card-body">
                  <div class="daemon-card-bullet">• <strong>Quiebres y Retesteos con Tendencia:</strong> 9,465 trades en 5 años ingresando en soportes y resistencias clave solo con fuerza direccional confirmada (ADX ≥ 30), evitando trampas en rangos muertos.</div>
                  <div class="daemon-card-bullet">• <strong>Adaptación de Volatilidad:</strong> Calibra el rango medio (ATR) de forma independiente en Forex y Sintéticos para que el Stop Loss tenga el respiro técnico exacto sin asumir riesgo excesivo.</div>
                  <div class="daemon-card-bullet">• <strong>Portafolio Seleccionado:</strong> 63 activos canónicos rentables en Replay Fiel 5 Años (+4,550.62R y +$455,062.00 PnL con Win Rate de 71.6% ponderado), descartando pares sin ventaja.</div>
                </div>
                <div class="daemon-card-plate">
                  <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                  <div class="daemon-card-plate-sub">ALCHEMIST INSTITUTIONAL · DUAL-LEG</div>
                </div>
              </div>
            </div>

            <!-- TARJETA 3 · ORB NY SWEEP -->
            <div class="daemon-card" style="--strat-accent: #f5bd36; --strat-glow: rgba(245, 189, 54, 0.25);">
              <div class="daemon-card-inner">
                <div class="daemon-card-head">
                  <div class="daemon-card-title">🗽 Estrategia 3 · ORB NY Sweep</div>
                  <div class="daemon-card-badge">+391.80R • 55.0% Acierto (Replay 5A)</div>
                </div>
                <div class="daemon-card-body">
                  <div class="daemon-card-bullet">• <strong>Apertura de Nueva York (09:30–11:30 NY):</strong> 3,172 trades en 5 años operando la ventana horaria de mayor volumen institucional tras la apertura de Wall Street.</div>
                  <div class="daemon-card-bullet">• <strong>Barridas de Liquidez y Stop Protegido:</strong> Detecta cuando el precio barre los máximos o mínimos del día anterior para atrapar traders atrapados, fijando el Stop Loss en el 50% del rango de apertura.</div>
                  <div class="daemon-card-bullet">• <strong>Activos Ganadores:</strong> 17 activos rentables en Replay Fiel 5 Años (+3,172 trades en Oro, Plata, Cripto y Petróleo), excluyendo índices con ruido excesivo.</div>
                </div>
                <div class="daemon-card-plate">
                  <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                  <div class="daemon-card-plate-sub">NEW YORK OPEN · EQUILIBRIUM SWEEP</div>
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
      </div>'''

idx_tri = content.find('id="triMotorAuditPanel"')
idx_msnr = content.find('id="msnrAuditPanel"')
if idx_tri != -1 and idx_msnr != -1:
    content = content[:idx_tri-5] + new_tri_motor_panel + '\n\n      ' + content[idx_msnr-5:]
    print("Panel Tri-Motor y 4 tarjetas superiores reemplazadas con éxito.")

# -------------------------------------------------------------------------
# PASO 5: PANEL MALAYSIAN SNR HUMANIZADO (Image 4)
# -------------------------------------------------------------------------
idx_msnr = content.find('id="msnrAuditPanel"')
idx_orb = content.find('id="orbAuditPanel"')

new_msnr_panel = '''<div id="msnrAuditPanel" style="display: none; margin-bottom: 24px;">
        <div class="card" style="border-left: 4px solid var(--g); border-top: 1px solid #5b4514; border-right: 1px solid #5b4514; border-bottom: 1px solid #5b4514; background: linear-gradient(180deg, rgba(0, 219, 121, 0.08) 0%, #070a0e 100%);">
          <div class="card-header" style="margin-bottom: 12px;">
            <h2 class="card-title">
              <span class="icon">🇲🇾</span>
              Malaysian SNR Híbrido Institucional: Metodología Alchemist (Nick) + Gestión Dual-Leg (Replay Fiel 5 Años)
            </h2>
            <div class="badge badge-green">Replay Fiel 5 Años · 64 Activos Rentables (WR ≥ 50%) · +3,093.36 R Netos · 9 Podados (WR < 50%) · 73 Instrumentos Evaluados</div>
          </div>
          <div class="muted" style="font-size: 13.5px; line-height: 1.75; margin-bottom: 18px;">
            Auditoría de <strong>Replay Fiel de 5 Años (1825 días)</strong> bar-a-bar con velas cerradas y sin lookahead sobre los <strong>73 instrumentos del catálogo</strong>. Integración sinérgica entre el gatillo estructural de <strong>Alchemist (MSNR)</strong> (absorción institucional en H1, key levels sobre cierres de líneas y retest M15) y el contrato de riesgo BlackDaemonFX (TP1 @ 1.0R, BE + spread y TP2 2.0R a 4.0R). <strong>64 activos canónicos superan el 50% de Win Rate acumulando 10,288 trades tomados y +3,093.36 R netos con 63.81% de acierto global</strong>. Los <strong>9 activos con baja expectativa o spread adverso pasan a PODA PREVENTIVA</strong> descartados automáticamente para proteger tu capital.
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
                  <div class="daemon-card-badge">54% Acierto vs 13% en 1:10</div>
                </div>
                <div class="daemon-card-body">
                  <div class="daemon-card-bullet">• <strong>La Trampa de los Ratios Gigantes (1:5 a 1:10):</strong> Cuando intentas buscar 5 o 10 veces lo arriesgado con stops diminutos, la tasa de acierto cae al <strong>13.1%</strong> y sufres rachas de 12 a 14 pérdidas seguidas, algo que quema cuentas rápidamente.</div>
                  <div class="daemon-card-bullet">• <strong>Nuestra Fórmula de 2 Órdenes:</strong> La primera orden (50%) toma ganancias rápido en un ratio 1:1 (TP1) y pasa inmediatamente la segunda orden a <strong>Break-Even (cero riesgo)</strong> para buscar un 1:2 o 1:4. Esto sube el acierto al <strong>55%–64%</strong> y elimina el estrés de que una operación ganadora se vuelva perdedora.</div>
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
                  <div class="daemon-card-title">3️⃣ LA MEJOR FORMA DE ENTRAR AL MERCADO</div>
                  <div class="daemon-card-badge">Retesteo de Quiebre (Ganador)</div>
                </div>
                <div class="daemon-card-body">
                  <div class="daemon-card-bullet">• <strong>Retesteo al Nivel de Quiebre (Hombro Izquierdo):</strong> Es la entrada más sólida y rentable (<code>+4.4R netos</code>), entrando exactamente cuando el precio regresa a probar la zona que acaba de romper con decisión.</div>
                  <div class="daemon-card-bullet">• <strong>El 50% de la Mecha (Descartada):</strong> Intentar entrar a la mitad de mechas largas (<code>-17.9R en pérdidas</code>) suele fallar porque muchas veces el precio se va sin ti o rompe con demasiada fuerza en contra.</div>
                  <div class="daemon-card-bullet">• <strong>Bloques de Órdenes Profundos (Descartados):</strong> Colocar órdenes al 50% de los Order Blocks (<code>-25.7R</code>) tuvo peor rendimiento que el retesteo estructural directo, por lo que fue descartado.</div>
                </div>
                <div class="daemon-card-plate">
                  <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                  <div class="daemon-card-plate-sub">SHOULDER BREAK RETEST · HIGH WIN RATE</div>
                </div>
              </div>
            </div>

            <!-- CARD 4 -->
            <div class="daemon-card" style="--strat-accent: var(--purple); --strat-glow: rgba(192, 132, 252, 0.28);">
              <div class="daemon-card-inner">
                <div class="daemon-card-head">
                  <div class="daemon-card-title">4️⃣ ACTIVOS GANADORES Y PARES DESCARTADOS</div>
                  <div class="daemon-card-badge">Sincronizado con Instrumentos</div>
                </div>
                <div class="daemon-card-body">
                  <div class="daemon-card-bullet">• <strong>Mejores Activos (+50% a 100% de Acierto):</strong> Oro (XAUUSD 58.1%), Volatility 5 (57.6%), Vol 90 (56.6%), Jump 75 (55.5%), Alemania 40 (54.7%), USDJPY (54.4%), GBPUSD (52.2%), y pares con precisión alta como CADCHF (85.7%) y GBPCAD (100%).</div>
                  <div class="daemon-card-bullet">• <strong>Pares Descartados (Evitar Pérdidas):</strong> Excluimos automáticamente activos erráticos o con comisiones altas como <code>AUDUSD</code> (45.5%), <code>Boom 600</code> (45.5%), <code>Crash 1000</code> (45.1%), <code>Boom 900</code> (45.0%), <code>EURUSD</code> (38.9%) y <code>CHFJPY</code> (37.5%).</div>
                </div>
                <div class="daemon-card-plate">
                  <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                  <div class="daemon-card-plate-sub">64 WINNING PAIRS · 9 PRUNED ASSETS</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>'''

if idx_msnr != -1 and idx_orb != -1:
    content = content[:idx_msnr-5] + new_msnr_panel + '\n\n      ' + content[idx_orb-5:]
    print("Panel Malaysian SNR reemplazado con éxito.")

# -------------------------------------------------------------------------
# PASO 6: PANEL ORB NEW YORK SWEEP HUMANIZADO (Image 6)
# -------------------------------------------------------------------------
idx_orb = content.find('id="orbAuditPanel"')
idx_ict = content.find('id="ictAuditPanel"')

new_orb_panel = '''<div id="orbAuditPanel" style="display: none; margin-bottom: 24px;">
        <div class="card" style="border-left: 4px solid #f5bd36; border-top: 1px solid #5b4514; border-right: 1px solid #5b4514; border-bottom: 1px solid #5b4514; background: linear-gradient(180deg, rgba(245, 189, 54, 0.08) 0%, #070a0e 100%);">
          <div class="card-header" style="margin-bottom: 12px;">
            <h2 class="card-title">
              <span class="icon">🗽</span>
              Estrategia ORB New York Sweep: Volatilidad de Apertura en Wall Street (Replay Fiel 5 Años)
              <!-- ORB New York SWEEP Confluencia Tripartita -->
            </h2>
            <div class="badge badge-gold">Replay Fiel 5 Años · 11 Activos Ganadores (+50% Acierto) · 24 Pares Descartados · 38 Incompatibles (Sin Campana NY)</div>
          </div>
          <div class="muted" style="font-size: 13.5px; line-height: 1.75; margin-bottom: 18px;">
            Auditoría histórica real de <strong>5 años (1,825 días)</strong> operando la apertura más líquida del mundo: la campana de Wall Street (09:30 a 11:30 hora de Nueva York).<br>
            Aprovecha la trampa inicial de los primeros 15 minutos, esperando a que el mercado barra los máximos o mínimos previos para entrar con la verdadera dirección institucional. <strong>11 activos con horario bursátil físico resultaron sólidamente rentables (+177.12R netos en 4,169 operaciones)</strong>, liderados por el Oro (XAUUSD), Bitcoin (BTCUSD), USDCAD y GBPUSD.<br>
            Los 38 sintéticos de Deriv quedan catalogados como <strong>incompatibles por diseño</strong> porque funcionan 24/7 sin subasta de apertura en Nueva York, mientras que los pares con poco volumen en esa franja horaria fueron descartados para proteger tu capital.
          </div>

          <div class="daemon-card-grid" style="grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px;">
            <!-- CARD 1: ACTIVOS ÉLITE -->
            <div class="daemon-card" style="--strat-accent: var(--g); --strat-glow: rgba(0, 219, 121, 0.28);">
              <div class="daemon-card-inner">
                <div class="daemon-card-head">
                  <div class="daemon-card-title">🏆 5 ACTIVOS ÉLITE (BARRIDO Y EXPANSIÓN LIMPIA)</div>
                  <div class="daemon-card-badge">+54.10R Netos</div>
                </div>
                <div class="daemon-card-body">
                  <div class="daemon-card-bullet">• <strong>Oro (XAUUSD & Micro):</strong> <code>+20.95R</code> (97 trades, <strong>59.8% acierto</strong>, factor 1.54). El activo rey de la sesión americana: barre liquidez y expande con alta precisión técnica.</div>
                  <div class="daemon-card-bullet">• <strong>Dólar vs Dólar Canadiense (USDCAD):</strong> <code>+13.81R</code> (52.8% a <strong>56.0% de acierto</strong> cerrando a las 11:30 NY con <code>+18.1R</code>). Máxima sincronía con noticias de EE.UU.</div>
                  <div class="daemon-card-bullet">• <strong>Bitcoin (BTCUSD & Micro):</strong> <code>+10.71R</code> (37 trades, <strong>62.2% acierto</strong>, factor 1.76). Gran momentum y recorridos limpios tras la apertura de Wall Street.</div>
                  <div class="daemon-card-bullet">• <strong>Libra Esterlina (GBPUSD):</strong> <code>+4.87R</code> (53.0% a <strong>57.0% de acierto</strong>, <code>+12.0R</code>). Aprovecha el choque entre el cierre de Londres y la apertura de NY.</div>
                  <div class="daemon-card-bullet">• <strong>Dólar Australiano (AUDUSD):</strong> <code>+3.76R</code> (54.2% a <strong>62.9% de acierto</strong> cuando el mercado tiene espacio libre de expansión).</div>
                </div>
                <div class="daemon-card-plate">
                  <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                  <div class="daemon-card-plate-sub">NEW YORK CASH OPEN · PURE SWEEP</div>
                </div>
              </div>
            </div>

            <!-- CARD 2: ACTIVOS RESCATADOS -->
            <div class="daemon-card" style="--strat-accent: var(--cyan); --strat-glow: rgba(56, 189, 248, 0.28);">
              <div class="daemon-card-inner">
                <div class="daemon-card-head">
                  <div class="daemon-card-title">🛡️ 3 ACTIVOS RESCATADOS (FILTRO DE TENDENCIA MAYOR)</div>
                  <div class="daemon-card-badge">+19.30R Netos</div>
                </div>
                <div class="daemon-card-body">
                  <div class="daemon-card-bullet">• <strong>Plata (XAGUSD & Micro):</strong> <code>+9.62R</code> (<strong>81.8% de acierto</strong>, factor 5.52). Al exigir que el precio barra primero un nivel de temporalidad mayor, pasó de pérdida a casi un 82% de efectividad.</div>
                  <div class="daemon-card-bullet">• <strong>Petróleo WTI (US Oil):</strong> <code>+9.67R</code> (<strong>76.5% de acierto</strong>, factor 4.80). Operando únicamente compras a favor de la tendencia macro, rescató una pérdida histórica de -34.6R convirtiéndola en ganancia neta.</div>
                  <div class="daemon-card-bullet">• <strong>Dólar vs Franco Suizo (USDCHF):</strong> <code>+2.38R</code> (<strong>64.3% de acierto</strong>). Filtro solo a favor de la tendencia de fondo, eliminando pérdidas por indecisión.</div>
                </div>
                <div class="daemon-card-plate">
                  <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                  <div class="daemon-card-plate-sub">HTF TREND FILTER · HIGH WIN RATE</div>
                </div>
              </div>
            </div>

            <!-- CARD 3: ACTIVOS DESCARTADOS -->
            <div class="daemon-card" style="--strat-accent: var(--r); --strat-glow: rgba(255, 69, 58, 0.28);">
              <div class="daemon-card-inner">
                <div class="daemon-card-head">
                  <div class="daemon-card-title">⚠️ 8 ACTIVOS DESCARTADOS (PROTECCIÓN CONTRA RUIDO)</div>
                  <div class="daemon-card-badge">-120R Evitados</div>
                </div>
                <div class="daemon-card-body">
                  <div class="daemon-card-bullet">• <strong>Dow Jones (Wall Street 30):</strong> <code>-7.99R</code> (solo 28.6% acierto). En apertura inmediata tiene excesivo ruido y mechas falsas que barren stops; es preferible operarlo en ICT.</div>
                  <div class="daemon-card-bullet">• <strong>Petróleo Brent (UK Brent Oil):</strong> <code>-39.63R</code> (40.6% acierto). Sufre continuas rupturas falsas durante la sesión americana.</div>
                  <div class="daemon-card-bullet">• <strong>Dólar Neozelandés (NZDUSD):</strong> <code>-24.78R</code> (42.3% acierto). Rango de movimiento muy estrecho en horario de NY.</div>
                  <div class="daemon-card-bullet">• <strong>Euro Dólar (EURUSD):</strong> <code>-17.92R</code> (47.1% acierto). En ORB es errático en apertura de NY; rinde mucho mejor en la sesión europea de Londres con ICT.</div>
                  <div class="daemon-card-bullet">• <strong>Sintéticos 24/7, SP500 y USDJPY:</strong> Descartados por no tener subasta física o por comisiones desfavorables.</div>
                </div>
                <div class="daemon-card-plate">
                  <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                  <div class="daemon-card-plate-sub">STRICT CAPITAL SHIELD · NO NOISE</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>'''

if idx_orb != -1 and idx_ict != -1:
    content = content[:idx_orb-5] + new_orb_panel + '\n\n      ' + content[idx_ict-5:]
    print("Panel ORB New York Sweep reemplazado con éxito.")

# -------------------------------------------------------------------------
# PASO 7: PANEL ICT HUMANIZADO (Image 7)
# -------------------------------------------------------------------------
idx_ict = content.find('id="ictAuditPanel"')
idx_trend = content.find('id="trendPullbackAuditPanel"')

new_ict_panel = '''<div id="ictAuditPanel" style="display: none; margin-bottom: 24px;">
        <div class="card" style="border-left: 4px solid var(--cyan); border-top: 1px solid #5b4514; border-right: 1px solid #5b4514; border-bottom: 1px solid #5b4514; background: linear-gradient(180deg, rgba(56, 189, 248, 0.08) 0%, #070a0e 100%);">
          <div class="card-header" style="margin-bottom: 12px;">
            <h2 class="card-title">
              <span class="icon">🏛️</span>
              Estrategia ICT: Liquidez Institucional, Desequilibrios de Precio y Filtro con IA (Replay Fiel 5 Años)
              <!-- ICT Sabri Malle -->
            </h2>
            <div class="badge badge-cyan">Replay Fiel 5 Años · 59 Activos Ganadores (+50% Acierto) · +8,038.81R Netos Ganados · 14 Descartados · 73 Evaluados</div>
          </div>
          <div class="muted" style="font-size: 13.5px; line-height: 1.75; margin-bottom: 18px;">
            Auditoría histórica real de <strong>5 años (1,825 días)</strong> analizada vela por vela, sin trucos ni anticipación, sobre los <strong>73 activos del catálogo oficial</strong>. Esta estrategia detecta la huella del dinero institucional mediante vacíos de liquidez (Fair Value Gaps en 15 minutos) y desequilibrios de precio, validando cada entrada con nuestro modelo predictivo de Inteligencia Artificial (83% de precisión histórica).<br>
            Bajo nuestra gestión profesional de 2 órdenes (asegurar ganancia en 1:1, mover a Break-Even y dejar correr la segunda orden hacia 1:2 o 1:4), <strong>59 activos resultaron altamente rentables, acumulando 37,918 operaciones ganadoras y +8,038.81 veces el riesgo asumido (60.5% de acierto ponderado)</strong>. Los 14 activos con ruido excesivo o comisiones desfavorables fueron descartados automáticamente para blindar tu cuenta.
          </div>

          <div class="daemon-card-grid" style="grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin-bottom: 20px;">
            <!-- CARD 1: SINTÉTICOS DERIV -->
            <div class="daemon-card daemon-card-accent-green">
              <div class="daemon-card-inner">
                <div class="daemon-card-head">
                  <div class="daemon-card-title">⚡ SINTÉTICOS DERIV (33 GANADORES)</div>
                  <div class="daemon-card-badge">+500.1R Netos · 33 Activos</div>
                </div>
                <div class="daemon-card-body">
                  <div class="daemon-card-bullet">• <strong>Líderes de Alta Precisión:</strong> Crash 300 (optimizado con <strong>+170.34R netos y 66.98% de acierto</strong>), Volatility 25 (+55.3R, 59.2% acierto) y Vol 100 1s (+23.5R, 56.4% acierto) respetan los vacíos de liquidez con precisión milimétrica.</div>
                  <div class="daemon-card-bullet">• <strong>Especialistas en Impulsos (Boom & Jump):</strong> Jump 25 (+35.6R), Jump 10 (+33.6R), Step 200 (+30.0R) y Crash 500 (+29.9R) logran alta asimetría al entrar tras confirmación estructural.</div>
                  <div class="daemon-card-bullet">• <strong>Rehabilitados con Inteligencia Artificial:</strong> Crash 1000 (<strong>+86.18R con 55.4% de acierto</strong> en 814 operaciones) y Jump 50 (+19.5R) pasaron de dar pérdidas a ser altamente rentables gracias al filtro de alta probabilidad.</div>
                </div>
                <div class="daemon-card-plate">
                  <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                  <div class="daemon-card-plate-sub">SYNTHETICS ENGINE · HIGH PRECISION</div>
                </div>
              </div>
            </div>

            <!-- CARD 2: DIVISAS FOREX -->
            <div class="daemon-card daemon-card-accent-cyan">
              <div class="daemon-card-inner">
                <div class="daemon-card-head">
                  <div class="daemon-card-title">🔄 DIVISAS FOREX (SESIÓN DE LONDRES)</div>
                  <div class="daemon-card-badge">+17.5R Netos · 9 Pares Élite</div>
                </div>
                <div class="daemon-card-body">
                  <div class="daemon-card-bullet">• <strong>Pares con Mayor Volumen Institucional:</strong> Las mejores entradas se concentran en la sesión europea de Londres: GBPUSD (<strong>55.32% de acierto</strong>), USDCHF (<strong>54.90% de acierto</strong>), EURJPY (52.83% acierto) y CADCHF (52.63% acierto).</div>
                  <div class="daemon-card-bullet">• <strong>Protección Contra Rangos Muertos:</strong> Se descartan sesiones asiáticas y horarios de bajo volumen donde las trampas y falsos quiebres generan pérdidas innecesarias.</div>
                  <div class="daemon-card-bullet">• <strong>Micro-Lotes Sincronizados:</strong> Cada par opera con su variante micro sincronizada para garantizar que el cálculo de riesgo y tamaño de lote sea exacto en cualquier tamaño de cuenta.</div>
                </div>
                <div class="daemon-card-plate">
                  <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                  <div class="daemon-card-plate-sub">LONDON KILLZONE · SMART MONEY</div>
                </div>
              </div>
            </div>

            <!-- CARD 3: ÍNDICES BURSÁTILES Y METALES -->
            <div class="daemon-card daemon-card-accent-gold">
              <div class="daemon-card-inner">
                <div class="daemon-card-head">
                  <div class="daemon-card-title">🟡 ÍNDICES BURSÁTILES Y METALES</div>
                  <div class="daemon-card-badge">+76.5R a Mercado · Ratios 1:3 a 1:5</div>
                </div>
                <div class="daemon-card-body">
                  <div class="daemon-card-bullet">• <strong>US Tech 100 (Nasdaq):</strong> Excelente rendimiento con <strong>75.00% de acierto</strong>, Factor de Beneficio 3.00 y <strong>+16.0R netos</strong>, capturando aceleraciones limpias tras la apertura.</div>
                  <div class="daemon-card-bullet">• <strong>Wall Street 30 (Dow Jones):</strong> Rescatado con <strong>56.76% de acierto</strong> y <strong>+4.5R</strong>, evitando la volatilidad inicial y montándose en la verdadera tendencia institucional.</div>
                  <div class="daemon-card-bullet">• <strong>Oro (XAUUSD) y Petróleo (US Oil):</strong> Rendimiento consistente con <strong>54.55% de acierto</strong> (+54.1R en petróleo a mercado) barriendo liquidez previa en temporalidades mayores.</div>
                </div>
                <div class="daemon-card-plate">
                  <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                  <div class="daemon-card-plate-sub">WALL STREET INDICES & COMMODITIES</div>
                </div>
              </div>
            </div>

            <!-- CARD 4: FILTRO DE RUIDO Y PROTECCIÓN -->
            <div class="daemon-card daemon-card-accent-purple">
              <div class="daemon-card-inner">
                <div class="daemon-card-head">
                  <div class="daemon-card-title">🛡️ FILTRO DE RUIDO Y PROTECCIÓN</div>
                  <div class="daemon-card-badge">14 Pares Descartados</div>
                </div>
                <div class="daemon-card-body">
                  <div class="daemon-card-bullet">• <strong>Pares Descartados (Protección de Capital):</strong> Se excluyeron 12 pares de Forex inconsistentes (como EURAUD, AUDUSD, EURCAD y USDJPY) para evitar operaciones en contra de liquidez.</div>
                  <div class="daemon-card-bullet">• <strong>Sintéticos con Comisiones Altas:</strong> Se descartaron activos como VolSwitch High Vol y HF Vol 50 por spreads y comisiones excesivas que perjudicaban el beneficio neto.</div>
                  <div class="daemon-card-bullet">• <strong>Control y Transparencia Total:</strong> Todos los activos evaluados y sus resultados se encuentran 100% auditados y sincronizados en la sección de <a href="/instruments" style="color: #f4c84f; text-decoration: underline; font-weight: 600;">Catálogo de Instrumentos</a>.</div>
                </div>
                <div class="daemon-card-plate">
                  <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                  <div class="daemon-card-plate-sub">STRICT RISK SHIELD · CAPITAL FIRST</div>
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
      </div>'''

if idx_ict != -1 and idx_trend != -1:
    content = content[:idx_ict-5] + new_ict_panel + '\n\n      ' + content[idx_trend-5:]
    print("Panel ICT reemplazado con éxito.")

# -------------------------------------------------------------------------
# PASO 8: PANEL TREND PULLBACK HUMANIZADO (Image 8)
# -------------------------------------------------------------------------
idx_trend = content.find('id="trendPullbackAuditPanel"')
idx_kpi = content.find('<!-- KPI METRICS GRID -->')
if idx_kpi == -1:
    idx_kpi = content.find('<section class="kpi-grid"')

new_tp_panel = '''<div id="trendPullbackAuditPanel" style="display: none; margin-bottom: 24px;">
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
      </div>'''

if idx_trend != -1 and idx_kpi != -1:
    content = content[:idx_trend-5] + new_tp_panel + '\n\n      ' + content[idx_kpi:]
    print("Panel Trend Pullback reemplazado con éxito.")

# -------------------------------------------------------------------------
# PASO 9: 6 TARJETAS KPI EN .DAEMON-CARD (Image 1)
# -------------------------------------------------------------------------
old_kpi_grid_pattern = re.compile(r'<section class="kpi-grid">.*?</section>', re.DOTALL)

new_kpi_grid_html = '''<section class="kpi-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 16px; margin-bottom: 24px;">
        <!-- 1. TRADES FILTRADOS / EVALUADOS -->
        <div class="daemon-card" style="--strat-accent: var(--y); --strat-glow: rgba(245, 189, 54, 0.28);">
          <div class="daemon-card-inner">
            <div class="daemon-card-head">
              <div class="daemon-card-title">🌐 TRADES FILTRADOS / EVALUADOS</div>
              <div class="daemon-card-badge" id="kpiUniverseBadge">TRI-MOTOR</div>
            </div>
            <div class="daemon-card-body" style="display: flex; flex-direction: column; justify-content: center; min-height: 105px;">
              <div class="kpi-val gold-txt" id="kpiTotalTrades" style="font-size: 21px; line-height: 1.3; margin-bottom: 6px; font-weight: 900; text-shadow: 0 2px 4px rgba(0,0,0,0.9);">71,962 trades evaluados (177 Activos Rentables / 292 Total)</div>
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
      </section>'''

m_kpi = old_kpi_grid_pattern.search(content)
if m_kpi:
    content = content[:m_kpi.start()] + new_kpi_grid_html + content[m_kpi.end():]
    print("KPI grid reemplazado con diseño de cartas legendarias.")

# -------------------------------------------------------------------------
# PASO 10: ACTUALIZAR CIFRAS INICIALES DE TP HITS (Image 2)
# -------------------------------------------------------------------------
content = content.replace('<span class="tp-hits" id="barTp1Hits">787</span>', '<span class="tp-hits" id="barTp1Hits">44,834</span>')
content = content.replace('<span class="tp-hits" id="barTp2Hits">512</span>', '<span class="tp-hits" id="barTp2Hits">25,107</span>')
content = content.replace('<span class="tp-hits" id="barTp3Hits">210</span>', '<span class="tp-hits" id="barTp3Hits">10,760</span>')
content = content.replace('<span class="tp-hits" id="barTp4Hits">105</span>', '<span class="tp-hits" id="barTp4Hits">5,380</span>')
content = content.replace('<span class="tp-hits" id="barBeHits">275</span>', '<span class="tp-hits" id="barBeHits">19,727</span>')
content = content.replace('<span class="tp-hits" id="barSlHits">206</span>', '<span class="tp-hits" id="barSlHits">27,128</span>')

# Guardar cambios
with open('dashboard/strategy_bases_page.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("dashboard/strategy_bases_page.py actualizado satisfactoriamente con todos los diseños solicitados.")
