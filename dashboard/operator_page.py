"""Página /operator: Suite Interactiva del Operador y Radar Macro en Tiempo Real.

Permite consultar visualmente desde el navegador el estado del bot,
chatear con el Copiloto Cuantitativo en lenguaje totalmente humanizado,
consultar el radar macroeconómico y la auditoría sin abrir consolas externas.
"""

from __future__ import annotations

from dashboard.page_loading import with_page_loading

_OPERATOR_BASE = r'''<!doctype html>
<html lang="es">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>DaemonBlackFx · Suite del Operador</title>
    <style>
      :root { color-scheme: dark; --bg:#050708; --p:#0a0e10; --p2:#10161a; --t:#f5f5f2; --m:#9fa2a5; --l:#5b4514;
              --g:#00db79; --r:#ff453a; --y:#f5bd36; --b:#d79b19; }
      * { box-sizing: border-box; }
      body { margin:0; background: radial-gradient(circle at 78% 0, rgba(215,155,25,.08), transparent 28%), #050708;
             color:var(--t); font:14px/1.45 system-ui,-apple-system,'Segoe UI',Roboto,sans-serif; }
      .appShell { display:grid; grid-template-columns:270px minmax(0,1fr); min-height:100vh; }
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
      .wrap { padding:22px 26px 60px; min-width:0; }
      h1 { margin:0 0 4px; font-size:22px; } h1 strong { color:var(--y); }
      h2 { font-size:16px; margin:26px 0 8px; color:var(--y); }
      .muted { color:var(--m); }
      .cards { display:grid; grid-template-columns:repeat(auto-fit,minmax(210px,1fr)); gap:12px; margin:16px 0; }
      .card { background:var(--p2); border:1px solid var(--l); border-radius:12px; padding:14px 16px; }
      .card .k { color:var(--m); font-size:12px; text-transform:uppercase; letter-spacing:.05em; }
      .card .v { font-size:22px; font-weight:700; margin-top:4px; }
      .card .sub { color:var(--m); font-size:12px; margin-top:2px; }
      .note { background:var(--p); border:1px solid var(--l); border-left:4px solid var(--b); border-radius:10px; padding:12px 14px; margin:14px 0; }
      .tableWrap { overflow-x:auto; margin:12px 0 24px; }
      table { width:100%; border-collapse:collapse; background:var(--p); border:1px solid var(--l); border-radius:10px; overflow:hidden; }
      th, td { padding:8px 12px; text-align:left; border-bottom:1px solid rgba(91,69,20,.35); vertical-align:middle; }
      th { color:var(--m); font-weight:600; font-size:12px; background:var(--p2); }
      .badge { display:inline-block; padding:2px 8px; border-radius:6px; font-size:11px; font-weight:700; text-transform:uppercase; }
      .badge-high { background:rgba(255,69,58,.2); color:var(--r); border:1px solid var(--r); }
      .badge-ok { background:rgba(0,219,121,.2); color:var(--g); border:1px solid var(--g); }
      .badge-warn { background:rgba(245,189,54,.2); color:var(--y); border:1px solid var(--y); }
      .top { display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:10px; }
      button, .btn { background:var(--p2); color:var(--y); border:1px solid var(--l); border-radius:8px; padding:7px 12px; cursor:pointer; font-weight:600; }
      button:hover { background:var(--b); color:#000; }
      .terminal { background:#030506; border:1px solid var(--l); border-radius:10px; padding:14px; font-family:Consolas,monospace; font-size:13px; color:#d9dde0; white-space:pre-wrap; max-height:280px; overflow-y:auto; line-height:1.5; }
      .cliBtns { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:10px; }

      /* ESTILOS DEL CHATBOT HUMANIZADO */
      .chatCard { background:var(--p2); border:1px solid var(--b); border-radius:14px; padding:18px 20px; margin:22px 0 28px; box-shadow:0 8px 24px rgba(0,0,0,.4); transition:all .2s ease; }
      .chatHeader { display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; flex-wrap:wrap; gap:8px; }
      .chatTitle { font-size:17px; font-weight:700; color:#fff; display:flex; align-items:center; gap:8px; }
      .chatTitle span { color:var(--y); }
      .chatHeaderActions { display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
      .chatStatusPill { font-size:11px; font-weight:700; color:var(--g); background:rgba(0,219,121,.12); border:1px solid var(--g); padding:3px 9px; border-radius:12px; }
      .btnSmall { background:#070a0d; border:1px solid var(--l); color:var(--t); border-radius:7px; padding:5px 11px; font-size:11.5px; font-weight:600; cursor:pointer; transition:all .15s; }
      .btnSmall:hover { color:var(--y); border-color:var(--y); background:rgba(215,155,25,.12); }
      .chatChips { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:12px; }
      .chipBtn { background:#070a0d; border:1px solid var(--l); border-radius:20px; color:var(--t); padding:5px 12px; font-size:12px; cursor:pointer; font-weight:500; transition:all .15s; }
      .chipBtn:hover { border-color:var(--y); color:var(--y); background:rgba(215,155,25,.1); }
      /* MODO FLUIDO SIN SCROLLBAR INTERNO POR DEFECTO */
      .chatWindow { min-height:360px; height:auto; max-height:none; overflow:visible; background:#040608; border:1px solid var(--l); border-radius:10px; padding:18px 20px; display:flex; flex-direction:column; gap:14px; }
      .chatWindow.scrollMode { height:580px; max-height:80vh; overflow-y:auto; scroll-behavior:smooth; }
      .chatWindow.scrollMode::-webkit-scrollbar { width:6px; }
      .chatWindow.scrollMode::-webkit-scrollbar-track { background:#040608; }
      .chatWindow.scrollMode::-webkit-scrollbar-thumb { background:#49380f; border-radius:3px; }
      .chatWindow.scrollMode::-webkit-scrollbar-thumb:hover { background:var(--b); }
      .msgBubble { max-width:92%; padding:14px 18px; border-radius:12px; line-height:1.55; font-size:13.5px; box-sizing:border-box; }
      .hasChartBubble { width:100% !important; max-width:100% !important; align-self:stretch !important; }
      .userBubble { align-self:flex-end; background:linear-gradient(135deg, rgba(215,155,25,.28), rgba(91,69,20,.5)); border:1px solid var(--b); color:#fff; border-bottom-right-radius:2px; }
      .botBubble { align-self:flex-start; background:#0c1114; border:1px solid rgba(91,69,20,.6); color:#f5f5f2; border-bottom-left-radius:2px; }
      .botBubble b, .botBubble strong { color:var(--y); }
      .botBubble ul { margin:6px 0; padding-left:20px; }
      .chatInputRow { display:flex; gap:10px; margin-top:12px; }
      .chatInput { flex:1; background:#05080a; border:1px solid var(--l); border-radius:9px; padding:10px 14px; color:#fff; font-size:14px; outline:none; }
      .chatInput:focus { border-color:var(--y); }
      .chatSendBtn { background:var(--b); color:#000; border:none; border-radius:9px; padding:0 22px; font-weight:700; cursor:pointer; transition:background .15s; }
      .chatSendBtn:hover { background:#ffc842; }

      /* ESTILOS DEL DIAGRAMA TÉCNICO INTERACTIVO A ANCHO COMPLETO */
      .chartCardWidget { margin-top:14px; width:100%; box-sizing:border-box; background:#030608; border:1px solid #7b5816; border-radius:12px; padding:12px 14px; box-shadow:0 6px 24px rgba(0,0,0,.6); }
      .chartWidgetHeader { display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; flex-wrap:wrap; gap:8px; border-bottom:1px solid rgba(91,69,20,.4); padding-bottom:8px; }
      .chartWidgetTitle { font-size:14.5px; font-weight:700; color:var(--y); display:flex; align-items:center; gap:8px; }
      .chartBadge { font-size:11.5px; font-weight:700; padding:3px 10px; border-radius:6px; letter-spacing:0.02em; }
      .chartBadgeBuy { background:rgba(0,219,121,.15); color:var(--g); border:1px solid var(--g); }
      .chartBadgeSell { background:rgba(255,69,58,.15); color:var(--r); border:1px solid var(--r); }
      .chartMetricsGrid { display:grid; grid-template-columns:repeat(auto-fit,minmax(120px,1fr)); gap:8px; margin-bottom:10px; }
      .chartMetric { background:#0a0e11; border:1px solid rgba(91,69,20,.35); border-radius:7px; padding:6px 10px; }
      .chartMetric .mlab { font-size:10px; color:var(--m); text-transform:uppercase; letter-spacing:.04em; }
      .chartMetric .mval { font-size:13px; font-weight:700; font-family:Consolas,monospace; margin-top:2px; }
      .chartSvgCanvas { width:100%; height:auto; min-height:270px; display:block; border-radius:8px; background:#020305; border:1px solid rgba(91,69,20,.3); }
      .chartLegend { display:flex; gap:14px; flex-wrap:wrap; font-size:11px; margin-top:10px; color:var(--m); align-items:center; }
      .chartLegendItem { display:flex; align-items:center; gap:6px; }
      .chartLegendDot { width:9px; height:9px; border-radius:50%; }

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
          padding: 10px;
        }
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
          <a href="/decisions">⚖ Decisiones de entrada</a>
          <a class="active" href="/operator">🛠 Suite Operador</a>
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
            <h1>BLACKDAEMON<strong>FX</strong> · Suite Interactiva del Operador</h1>
            <div class="muted">Panel centralizado de control, radar macroeconómico y copiloto conversacional en solo lectura estricta.</div>
          </div>
          <div>
            <button id="btnReload">🔄 Actualizar Datos</button>
          </div>
        </div>

        <div class="cards">
          <div class="card">
            <div class="k">Estado del Bot</div>
            <div class="v" id="cardStatus" style="color:var(--g)">--</div>
            <div class="sub" id="cardConnection">Conexión: --</div>
          </div>
          <div class="card">
            <div class="k">Radar Macroeconómico</div>
            <div class="v" id="cardMacroEvents" style="color:var(--y)">--</div>
            <div class="sub" id="cardMacroCurrencies">Divisas: --</div>
          </div>
          <div class="card">
            <div class="k">Posiciones Abiertas</div>
            <div class="v" id="cardPositions">--</div>
            <div class="sub">Máx. 8 concurrentes (16 físicas)</div>
          </div>
          <div class="card">
            <div class="k">Catálogo 212 Pares</div>
            <div class="v" id="cardCatalog" style="color:var(--g)">151 ON</div>
            <div class="sub">61 en poda preventiva (57.58% WR)</div>
          </div>
        </div>

        <!-- SECCIÓN CHATBOT INTERACTIVO HUMANIZADO -->
        <div class="chatCard">
          <div class="chatHeader">
            <div class="chatTitle">💬 Copiloto Cuantitativo <span>BlackDaemonFX</span></div>
            <div class="chatHeaderActions">
              <button id="btnClearChat" class="btnSmall" title="Reiniciar la conversación">🧹 Limpiar Chat</button>
              <button id="btnToggleScroll" class="btnSmall" title="Alternar entre vista fluida sin scroll y ventana con scroll">📦 Activar Scroll</button>
              <div class="chatStatusPill">● Asistente en vivo</div>
            </div>
          </div>
          <div class="muted" style="font-size:12.5px; margin-bottom:12px;">
            Pregunta en lenguaje natural sobre cualquier activo, qué instrumentos están por entrar a mercado, setups técnicos o noticias macro.
          </div>
          <div class="chatChips">
            <button class="chipBtn" style="border-color:var(--y);color:var(--y);background:rgba(215,155,25,.08);" onclick="sendQuickPrompt('¿Qué instrumento está por realizar un trade?')">🎯 ¿Qué activo está por entrar?</button>
            <button class="chipBtn" style="border-color:var(--g);color:var(--g);background:rgba(0,219,121,.08);" onclick="sendQuickPrompt('¿Cómo van los trades abiertos?')">📊 Operaciones vivas</button>
            <button class="chipBtn" style="border-color:#5bc0de;color:#5bc0de;background:rgba(91,192,222,.08);" onclick="sendQuickPrompt('¿Cuánto estamos arriesgando y cuál es el margen?')">🛡️ Riesgo & Margen</button>
            <button class="chipBtn" onclick="sendQuickPrompt('¿Qué se ve en Volatility 75?')">⚡ Volatility 75</button>
            <button class="chipBtn" onclick="sendQuickPrompt('Analízame Step Index 400')">⚡ Step Index 400</button>
            <button class="chipBtn" onclick="sendQuickPrompt('¿Cómo está Crash 1000?')">⚡ Crash 1000</button>
            <button class="chipBtn" onclick="sendQuickPrompt('¿Cuándo pasas a Break Even?')">🛡️ Break-Even</button>
            <button class="chipBtn" onclick="sendQuickPrompt('¿Hay noticias macro hoy?')">📡 Radar Macro</button>
            <button class="chipBtn" onclick="sendQuickPrompt('¿Cómo va la cuenta?')">📈 Estado cuenta</button>
          </div>
          <div class="chatWindow" id="chatBox">
            <div class="msgBubble botBubble">
              👋 <b>¡Hola, operador!</b> Soy tu Asistente Cuantitativo en vivo de <b>BlackDaemonFX</b>.<br><br>
              Monitoreo continuamente la microestructura de mercado, las confluencias de Smart Money y el Criterio Humano.
              ¿De qué instrumento te gustaría conocer el diagnóstico técnico ahora mismo o qué duda tienes sobre la sesión?
            </div>
          </div>
          <div class="chatInputRow">
            <input type="text" id="chatInput" class="chatInput" placeholder="Escribe tu consulta (ej. ¿Qué ves en Step Index o en el Oro?)..." />
            <button id="chatSendBtn" class="chatSendBtn">Enviar ➔</button>
          </div>
        </div>

        <div class="note">
          <b>Protección Inteligente ante Noticias Macro:</b> En mercados reales (Forex, Metales e Índices US), el bot activa una ventana de congelamiento pre y post noticia de alto impacto. Las posiciones que ya van en desarrollo favorable y con trailing stop o BE neto asegurado <b>preservan su stop favorable intacto</b> para continuar capturando la expansión de volatilidad sin degradar a BE plano.
          <br><b>Aislamiento Sintéticos:</b> Los 30 índices sintéticos de Deriv tienen <b>0% de afectación macro</b> y operan 24/7 sin bloqueos por noticias del mundo real.
        </div>

        <h2>📡 Radar Macroeconómico (Eventos de Alto Impacto)</h2>
        <div class="tableWrap">
          <table id="tblMacro">
            <thead>
              <tr>
                <th>FECHA / HORA (UTC)</th>
                <th>PAÍS</th>
                <th>EVENTO</th>
                <th>IMPACTO</th>
                <th>ANTERIOR</th>
                <th>PREVISIÓN</th>
              </tr>
            </thead>
            <tbody>
              <tr><td colspan="6" class="muted">Cargando agenda de eventos...</td></tr>
            </tbody>
          </table>
        </div>

        <h2>💻 Consola Rápida del Operador (CLI Integrada)</h2>
        <div class="cliBtns">
          <button onclick="loadCliView('status')">📊 Estado Global</button>
          <button onclick="loadCliView('macro')">📡 Radar Macro</button>
          <button onclick="loadCliView('audit')">⚖ Auditoría Reciente</button>
          <button onclick="loadCliView('catalog')">📚 Catálogo 212 Pares</button>
        </div>
        <div class="terminal" id="terminalOutput">Seleccione un comando o cargando estado inicial...</div>

        <h2>⚖ Últimas Decisiones de Auditoría y Vetos</h2>
        <div class="tableWrap">
          <table id="tblAudit">
            <thead>
              <tr>
                <th>HORA (UTC)</th>
                <th>ORIGEN</th>
                <th>SÍMBOLO</th>
                <th>ACCIÓN</th>
                <th>MOTIVO / DETALLE</th>
              </tr>
            </thead>
            <tbody>
              <tr><td colspan="5" class="muted">Cargando eventos de auditoría...</td></tr>
            </tbody>
          </table>
        </div>
      </main>
    </div>

    <script>
      let g_data = null;

      async function fetchOperatorData() {
        try {
          const res = await fetch('/api/operator?t=' + Date.now());
          if (!res.ok) throw new Error('HTTP ' + res.status);
          g_data = await res.json();
          renderCards(g_data);
          renderMacroTable(g_data.macro);
          renderAuditTable(g_data.audit);
          loadCliView('status');
        } catch (err) {
          console.error('Error fetching operator data:', err);
          document.getElementById('cardStatus').textContent = 'ERROR';
          document.getElementById('cardStatus').style.color = 'var(--r)';
        }
      }

      function renderCards(d) {
        if (!d) return;
        const st = d.status || {};
        const mc = d.macro || {};
        document.getElementById('cardStatus').textContent = st.bot_status || 'ACTIVO';
        document.getElementById('cardConnection').textContent = 'Modo: ' + (st.connection_mode || 'LIVE') + ' | Ciclo #' + (st.cycle || 0);

        const highCount = (mc.high_impact_events || []).length;
        document.getElementById('cardMacroEvents').textContent = highCount + ' Eventos';
        const currs = (mc.currencies_affected || []).join(', ') || 'Ninguna';
        document.getElementById('cardMacroCurrencies').textContent = 'Afecta: ' + currs;

        const posCount = (d.positions || []).length;
        document.getElementById('cardPositions').textContent = posCount + ' / 8';
      }

      function renderMacroTable(mc) {
        const tbody = document.querySelector('#tblMacro tbody');
        if (!mc || !mc.high_impact_events || mc.high_impact_events.length === 0) {
          tbody.innerHTML = '<tr><td colspan="6" class="muted">No hay eventos de alto impacto pendientes en la agenda para las próximas 24-48h.</td></tr>';
          return;
        }
        let html = '';
        for (const ev of mc.high_impact_events) {
          const dt = (ev.event_at || '').slice(0, 19).replace('T', ' ');
          const country = ev.country || 'GLOBAL';
          const title = ev.title || ev.title_original || 'Evento Macro';
          const prev = ev.previous || '-';
          const fc = ev.forecast || '-';
          html += `<tr>
            <td><b>${dt}</b></td>
            <td><span class="badge badge-warn">${country}</span></td>
            <td>${title}</td>
            <td><span class="badge badge-high">ALTO IMPACTO</span></td>
            <td>${prev}</td>
            <td>${fc}</td>
          </tr>`;
        }
        tbody.innerHTML = html;
      }

      function humanizeAuditAction(action, eventType) {
        const raw = String(action || eventType || '').trim().toUpperCase();
        if (!raw || raw === '--') return { label: 'Inicio de Ciclo', badge: 'badge-ok' };
        if (raw === 'CYCLE_START' || raw === 'DAEMON_CYCLE_START') return { label: 'Inicio de Ciclo', badge: 'badge-ok' };
        if (raw === 'REGIME_TOXIC_OBSERVED_NOT_BLOCKED' || raw === 'MARKET_REGIME_OBSERVED') return { label: 'Volatilidad Vigilada (Sin Veto)', badge: 'badge-warn' };
        if (raw === 'REGIME_FILTER_BLOCKED' || raw === 'MARKET_REGIME_BLOCKED') return { label: 'Veto por Régimen Tóxico', badge: 'badge-high' };
        if (raw.includes('STANDBY_ENTER')) return { label: 'Pausa Mercado Cerrado', badge: 'badge-warn' };
        if (raw.includes('STANDBY_EXIT')) return { label: 'Reapertura Mercado', badge: 'badge-ok' };
        if (raw === 'ANALYZING' || raw === 'SYMBOL_PROCESS_START') return { label: 'Evaluando Microestructura', badge: 'badge-ok' };
        if (raw.includes('COOLDOWN')) return { label: 'Pausa Preventiva Post-SL', badge: 'badge-high' };
        if (raw === 'VIRTUAL_TRADE_SPREAD_NORMALIZED') return { label: 'Spread Recuperado', badge: 'badge-ok' };
        if (raw === 'FOREX_NEWS_TRAILING_PRESERVED') return { label: 'Trailing Stop Preservado', badge: 'badge-ok' };
        if (raw === 'FOREX_NEWS_BREAK_EVEN_CONFIRMED') return { label: 'Break-Even por Noticia', badge: 'badge-warn' };
        if (raw === 'FOREX_NEWS_BREAK_EVEN_DEFERRED') return { label: 'BE Diferido (En Espera)', badge: 'badge-warn' };
        if (raw.includes('SELECTION') || raw.includes('PROFILE')) return { label: 'Catálogo Élite Sincronizado', badge: 'badge-ok' };
        if (raw.includes('TARGET_VALUES')) return { label: 'Niveles TP/SL Registrados', badge: 'badge-ok' };
        if (raw.includes('RECOVERED')) return { label: 'Posición MT5 Sincronizada', badge: 'badge-ok' };
        if (raw.includes('SGD_STEP')) return { label: 'Aprendizaje IA Actualizado', badge: 'badge-ok' };
        if (raw === 'ALLOW' || raw === 'PERMITIDO') return { label: 'Confluencia Confirmada', badge: 'badge-ok' };
        if (raw === 'VETO' || raw === 'REJECT' || raw === 'RECHAZADA') return { label: 'Veto Institucional', badge: 'badge-high' };

        const clean = raw.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, l => l.toUpperCase());
        return { label: clean, badge: 'badge-ok' };
      }

      function humanizeAuditReason(reason, action) {
        const r = String(reason || '').trim();
        const act = String(action || '').toUpperCase();
        if (!r || r === '--' || r === 'None' || r === 'null') {
          if (act.includes('CYCLE_START')) return 'Inicio del barrido periódico de escaneo sobre los 212 activos del catálogo institucional.';
          if (act.includes('STANDBY')) return 'Horario fuera de sesión bancaria/bolsa; respetando ventana de liquidez institucional.';
          if (act.includes('PROFILE') || act.includes('SELECTION')) return 'Sincronización del catálogo élite activo y activos en poda preventiva.';
          return 'Inspección periódica en segundo plano completada en condiciones normales.';
        }
        if (r.includes('ERRATIC_WHIPSAW_VOLATILITY') || r.includes('MARKET_REGIME_TOXIC')) {
          if (act.includes('NOT_BLOCKED') || act.includes('OBSERVED')) {
            return 'Volatilidad errática con sacudidas bruscas detectada; Centinela mantiene observación activa sin vetar el trade por absorción/desplazamiento institucional.';
          }
          return 'Volatilidad errática con sacudidas bruscas (Whipsaw); operación descartada preventivamente para proteger la cuenta.';
        }
        if (r === 'SYNTHETICS') return 'Perfil de 38 índices sintéticos de Deriv validado y activo 24/7.';
        if (r === 'FOREX') return 'Perfil de divisas Forex mayores y menores sincronizado con el calendario.';
        if (r === 'ICT') return 'Perfil especializado de estrategia ICT Institutional validado.';
        if (r === 'MALAYSIAN_SNR') return 'Perfil de niveles Malaysian SNR y microestructura validado.';
        if (r === 'TREND_PULLBACK') return 'Perfil de continuación tendencial validado.';
        if (r.includes('SPREAD_TOO_HIGH') || r.includes('SPREAD_SPIKE')) return 'Spread de mercado temporalmente elevado por encima del umbral institucional.';
        if (r.includes('MAX_POSITIONS')) return 'Cupo máximo de 8 posiciones concurrentes activas alcanzado para preservar margen.';
        if (r.includes('COOLDOWN')) return 'Período de enfriamiento post Stop Loss activo para evitar sobreoperativa en este par.';
        if (r.startsWith('LABEL_')) return 'Actualización del modelo de Criterio Humano / IA tras registrar el resultado de la operación.';
        return r.replace(/MARKET_REGIME_TOXIC_BLOCKED:/g, '').replace(/_/g, ' ').trim();
      }

      function renderAuditTable(auditList) {
        const tbody = document.querySelector('#tblAudit tbody');
        if (!auditList || auditList.length === 0) {
          tbody.innerHTML = '<tr><td colspan="5" class="muted">No se registran eventos de auditoría recientes.</td></tr>';
          return;
        }
        let html = '';
        for (const a of auditList) {
          const t = (a.event_time || a.created_at || '').slice(0, 19).replace('T', ' ');
          const src = a.source || 'LIVE';
          const sym = a.instrument || 'GLOBAL';

          const actObj = humanizeAuditAction(a.action_es || a.action, a.event_type);
          const actBadge = a.action_badge || actObj.badge;
          const actLabel = a.action_es || actObj.label;

          const reason = a.reason_es || humanizeAuditReason(a.reason, a.action_raw || a.action);

          html += `<tr>
            <td style="font-family:monospace;font-size:12px;white-space:nowrap;">${t}</td>
            <td><span class="badge badge-ok">${src}</span></td>
            <td><b>${sym}</b></td>
            <td><span class="badge ${actBadge}">${actLabel}</span></td>
            <td style="color:#d9dde0;line-height:1.45;">${reason}</td>
          </tr>`;
        }
        tbody.innerHTML = html;
      }

      function loadCliView(cmd) {
        if (!g_data) return;
        const box = document.getElementById('terminalOutput');
        if (cmd === 'status') {
          const st = g_data.status || {};
          const pos = g_data.positions || [];
          box.textContent = `=================================================================\n` +
            `      BLACKDAEMONFX — ESTADO OPERATIVO DEL SISTEMA (CLI VIEW)\n` +
            `=================================================================\n` +
            `  Estado del Bot:       ${st.bot_status}\n` +
            `  Modo de Conexión:     ${st.connection_mode}\n` +
            `  Frescura de Datos:    ${st.data_freshness}\n` +
            `  Ciclo Actual:         #${st.cycle}\n` +
            `  Símbolos Escaneados:  ${st.symbols_processed} / ${st.symbols_total}\n` +
            `  Posiciones Abiertas:  ${pos.length}\n` +
            `  Base de Datos (RO):   ${st.db_path}\n` +
            `-----------------------------------------------------------------\n` +
            (pos.length === 0 ? `  (No hay posiciones abiertas en este momento)\n` : JSON.stringify(pos, null, 2)) +
            `=================================================================`;
        } else if (cmd === 'macro') {
          const mc = g_data.macro || {};
          box.textContent = `===========================================================================\n` +
            `      BLACKDAEMONFX — RADAR MACROECONÓMICO Y NOTICIAS\n` +
            `===========================================================================\n` +
            `  Estado de la Agenda:   ${mc.calendar_status}\n` +
            `  Última Actualización:  ${mc.updated_at || 'N/A'}\n` +
            `  Divisas Afectadas:     ${(mc.currencies_affected || []).join(', ') || 'Ninguna'}\n` +
            `  Eventos de Alto Impacto: ${(mc.high_impact_events || []).length}\n` +
            `---------------------------------------------------------------------------\n` +
            (mc.high_impact_events || []).map(e => `  [${(e.event_at || '').slice(0, 19)}] ${e.country} -> ${e.title} (Prev: ${e.previous || '-'}, Est: ${e.forecast || '-'})`).join('\n') +
            `\n===========================================================================`;
        } else if (cmd === 'audit') {
          const aud = g_data.audit || [];
          box.textContent = `===========================================================================\n` +
            `      BLACKDAEMONFX — AUDITORÍA DE DECISIONES Y VETOS (HUMANIZADA)\n` +
            `===========================================================================\n` +
            aud.map(a => {
              const t = (a.event_time || '').slice(0, 19).replace('T', ' ');
              const act = a.action_es || humanizeAuditAction(a.action, a.event_type).label;
              const reas = a.reason_es || humanizeAuditReason(a.reason, a.action_raw || a.action);
              return `  [${t}] [${a.source || 'LIVE'}] ${a.instrument || 'GLOBAL'} -> ${act}\n      Motivo / Detalle: ${reas}`;
            }).join('\n---------------------------------------------------------------------------\n') +
            `\n===========================================================================`;
        } else if (cmd === 'catalog') {
          const cat = g_data.catalog || {};
          box.textContent = `=================================================================\n` +
            `      BLACKDAEMONFX — ESTADO DEL CATÁLOGO DE 212 PARES\n` +
            `=================================================================\n` +
            `  Auditoría Oficial:       ${cat.status}\n` +
            `  Total Pares Evaluados:   ${cat.total_pairs}\n` +
            `  Pares Activos (>50% WR): ${cat.active_pairs}  (71.2% del catálogo)\n` +
            `  Pares en Poda:           ${cat.pruned_pairs}  (28.8% del catálogo)\n` +
            `  Win Rate Global:         ${cat.global_winrate}\n` +
            `  Retorno Neto Acumulado:  ${cat.accumulated_r}\n` +
            `=================================================================`;
        }
      }

      /* FUNCIONES DEL CHATBOT CONVERSACIONAL */
      function escapeHtml(str) {
        return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
      }

      function formatMarkdown(text) {
        let t = escapeHtml(text);
        t = t.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
        t = t.replace(/\*(.*?)\*/g, '<i>$1</i>');
        t = t.replace(/`([^`]+)`/g, '<code style="background:#151c20;padding:2px 5px;border-radius:4px;color:var(--y)">$1</code>');
        t = t.replace(/\n\n/g, '<br><br>');
        t = t.replace(/\n• /g, '<br>• ');
        t = t.replace(/\n(\d+)\. /g, '<br>$1. ');
        t = t.replace(/\n/g, '<br>');
        return t;
      }

      function renderChartCard(cd) {
        if (!cd || !cd.candles || cd.candles.length === 0) return '';
        const dir = cd.direction || 'BUY';
        const isBuy = dir === 'BUY';
        const d = cd.digits != null ? cd.digits : 2;
        const num = (v) => Number(v).toFixed(d);

        // Lienzo ampliado a 1000px de resolución horizontal para nitidez absoluta a ancho completo
        const W = 1000;
        const H = 280;
        const p = { top: 28, right: 120, bottom: 28, left: 24 };
        const plotW = W - p.left - p.right;
        const priceH = H - p.top - p.bottom;

        const totalSteps = 34; // 26 velas pasadas + 8 pasos de proyección
        const candles = cd.candles;

        const rawPrices = [
          ...candles.map(c => c.high),
          ...candles.map(c => c.low),
          cd.current_price,
          cd.entry_price,
          cd.zone_low,
          cd.zone_high,
          cd.stop_loss,
          cd.take_profit_1,
          cd.take_profit_2
        ];
        // Filtrar estrictamente precios positivos válidos (> 0) para evitar que valores en 0 rompan la escala
        const validPrices = rawPrices.filter(v => typeof v === 'number' && Number.isFinite(v) && v > 0);
        if (validPrices.length === 0) validPrices.push(Number(cd.current_price) || 100.0);

        let minP = Math.min(...validPrices);
        let maxP = Math.max(...validPrices);
        let span = maxP - minP || (Math.abs(maxP) * 0.02) || 1.0;
        minP = Math.max(0.0001, minP - span * 0.08);
        maxP = maxP + span * 0.08;
        span = maxP - minP;

        const x = (step) => p.left + (step + 0.5) * (plotW / totalSteps);
        const y = (price) => p.top + ((maxP - Number(price)) / span) * priceH;
        const cw = Math.max(5, (plotW / totalSteps) * 0.65);

        let svg = `<svg viewBox="0 0 ${W} ${H}" class="chartSvgCanvas" preserveAspectRatio="none">`;
        svg += `<defs>
          <marker id="arrowHead" markerWidth="10" markerHeight="8" refX="8" refY="4" orient="auto">
            <polygon points="0 0, 10 4, 0 8" fill="#f5bd36"/>
          </marker>
        </defs>`;

        // Pre-calcular posiciones verticales de niveles clave para evitar colisiones
        const ySl = y(cd.stop_loss);
        const yTp1 = y(cd.take_profit_1);
        const yCur = y(cd.current_price);
        const yTp2 = cd.take_profit_2 ? y(cd.take_profit_2) : null;
        const badgePositions = [ySl, yTp1, yCur, yTp2].filter(v => v != null);

        // Grid horizontal de referencia y escala derecha (con prevención estricta de colisiones)
        for (let i = 0; i <= 5; i++) {
          const yy = p.top + (i * priceH) / 5;
          const val = maxP - (i * span) / 5;
          svg += `<line x1="${p.left}" y1="${yy}" x2="${W - p.right}" y2="${yy}" stroke="rgba(255,255,255,0.06)" stroke-dasharray="2,4"/>`;
          const collides = badgePositions.some(by => Math.abs(yy - by) < 13);
          if (!collides) {
            svg += `<text x="${W - p.right + 10}" y="${yy + 4}" fill="#7a8890" font-size="10" font-family="Consolas,monospace">${num(val)}</text>`;
          }
        }

        // Zona de Retest / Mitigación OTE (Rectángulo sombreado proyectado)
        const zTop = Math.min(y(cd.zone_high), y(cd.zone_low));
        const zHeight = Math.max(10, Math.abs(y(cd.zone_high) - y(cd.zone_low)));
        const zLeft = x(25.5);
        const zWidth = x(33.5) - zLeft;
        const zFill = isBuy ? 'rgba(0, 219, 121, 0.16)' : 'rgba(255, 69, 58, 0.16)';
        const zStroke = isBuy ? 'rgba(0, 219, 121, 0.7)' : 'rgba(255, 69, 58, 0.7)';
        svg += `<rect x="${zLeft}" y="${zTop}" width="${zWidth}" height="${zHeight}" fill="${zFill}" stroke="${zStroke}" stroke-dasharray="3,3" rx="4"/>`;
        const zoneTextY = zTop - 7 >= p.top ? zTop - 7 : zTop + 14;
        svg += `<rect x="${zLeft + 2}" y="${zoneTextY - 9}" width="138" height="15" fill="rgba(3,6,8,0.85)" rx="3"/>`;
        svg += `<text x="${zLeft + 6}" y="${zoneTextY + 2}" fill="${isBuy ? '#00db79' : '#ff453a'}" font-size="9" font-weight="700">ZONA DE RETEST / OTE</text>`;

        // Velas Japonesas con mechas y cuerpos de alta definición
        candles.forEach((c, i) => {
          const cx = x(i);
          const cyOpen = y(c.open);
          const cyClose = y(c.close);
          const cyHigh = y(c.high);
          const cyLow = y(c.low);
          const isBull = c.close >= c.open;
          const col = isBull ? '#00db79' : '#ff453a';

          svg += `<line x1="${cx}" y1="${cyHigh}" x2="${cx}" y2="${cyLow}" stroke="${col}" stroke-width="1.4"/>`;
          const bodyTop = Math.min(cyOpen, cyClose);
          const bodyH = Math.max(2.5, Math.abs(cyClose - cyOpen));
          svg += `<rect x="${cx - cw / 2}" y="${bodyTop}" width="${cw}" height="${bodyH}" fill="${col}" stroke="${col}" stroke-width="0.9" rx="0.8"/>`;
        });

        // Niveles clave proyectados: SL (Badge con fondo opaco y borde de color para nitidez absoluta)
        svg += `<line x1="${x(24)}" y1="${ySl}" x2="${W - p.right}" y2="${ySl}" stroke="#ff453a" stroke-dasharray="4,4" stroke-width="1.5"/>`;
        svg += `<rect x="${W - p.right + 4}" y="${ySl - 10}" width="102" height="20" fill="#180b0d" stroke="#ff453a" stroke-width="1.2" rx="3.5"/>`;
        svg += `<text x="${W - p.right + 9}" y="${ySl + 4}" fill="#ff453a" font-size="9.5" font-weight="700" font-family="Consolas,monospace">SL ${num(cd.stop_loss)}</text>`;

        // Niveles clave proyectados: TP1
        svg += `<line x1="${x(24)}" y1="${yTp1}" x2="${W - p.right}" y2="${yTp1}" stroke="#00db79" stroke-dasharray="4,4" stroke-width="1.5"/>`;
        svg += `<rect x="${W - p.right + 4}" y="${yTp1 - 10}" width="102" height="20" fill="#081810" stroke="#00db79" stroke-width="1.2" rx="3.5"/>`;
        svg += `<text x="${W - p.right + 9}" y="${yTp1 + 4}" fill="#00db79" font-size="9.5" font-weight="700" font-family="Consolas,monospace">TP1 ${num(cd.take_profit_1)}</text>`;

        // Niveles clave proyectados: TP2 (Runner)
        if (cd.take_profit_2 && yTp2) {
          if (yTp2 >= p.top - 5 && yTp2 <= H - p.bottom + 5) {
            svg += `<line x1="${x(24)}" y1="${yTp2}" x2="${W - p.right}" y2="${yTp2}" stroke="#00db79" stroke-dasharray="2,3" stroke-width="1.2"/>`;
            svg += `<rect x="${W - p.right + 4}" y="${yTp2 - 9}" width="102" height="18" fill="#081810" stroke="#00db79" stroke-width="1" rx="3"/>`;
            svg += `<text x="${W - p.right + 9}" y="${yTp2 + 4}" fill="#00db79" font-size="9" font-family="Consolas,monospace">TP2 ${num(cd.take_profit_2)}</text>`;
          }
        }

        // Precio Actual (Línea cian, punto indicador y badge opaco)
        const xCur = x(25);
        svg += `<line x1="${p.left}" y1="${yCur}" x2="${W - p.right}" y2="${yCur}" stroke="#38bdf8" stroke-dasharray="3,3" stroke-width="1.3"/>`;
        svg += `<circle cx="${xCur}" cy="${yCur}" r="5" fill="#38bdf8" stroke="#040709" stroke-width="1.5"/>`;
        svg += `<rect x="${W - p.right + 4}" y="${yCur - 10}" width="102" height="20" fill="#081420" stroke="#38bdf8" stroke-width="1.2" rx="3.5"/>`;
        svg += `<text x="${W - p.right + 9}" y="${yCur + 4}" fill="#38bdf8" font-size="9.5" font-weight="700" font-family="Consolas,monospace">NOW ${num(cd.current_price)}</text>`;

        // Trayectoria proyectada (Flecha dorada curvada: Precio Actual -> Retest OTE -> Expansión TP1)
        const xRetest = x(28.5);
        let yRetest = y(cd.entry_price);
        if (Math.abs(yRetest - yCur) < 6) {
          yRetest = isBuy ? yCur + (priceH * 0.09) : yCur - (priceH * 0.09);
        }
        const xTarget = x(33.0);
        const yTarget = y(cd.take_profit_1);

        const cp1x = (xCur + xRetest) / 2;
        const cp1y = isBuy ? Math.max(yCur, yRetest) + 6 : Math.min(yCur, yRetest) - 6;

        const pathD = `M ${xCur} ${yCur} Q ${cp1x} ${cp1y}, ${xRetest} ${yRetest} T ${xTarget} ${yTarget}`;

        svg += `<path d="${pathD}" fill="none" stroke="#f5bd36" stroke-width="2.8" stroke-dasharray="5,4" marker-end="url(#arrowHead)"/>`;
        svg += `<circle cx="${xRetest}" cy="${yRetest}" r="4" fill="#f5bd36"/>`;
        const textY = isBuy ? Math.max(yRetest, yCur) + 20 : Math.min(yRetest, yCur) - 14;
        const safeTextY = Math.max(p.top + 14, Math.min(H - p.bottom - 6, textY));
        svg += `<rect x="${xRetest - 32}" y="${safeTextY - 11}" width="176" height="17" fill="#140f04" stroke="#8a6715" stroke-width="0.9" rx="3"/>`;
        svg += `<text x="${xRetest - 27}" y="${safeTextY + 1}" fill="#f5bd36" font-size="9.5" font-weight="700">➔ TRAYECTORIA ESPERADA</text>`;

        svg += `</svg>`;

        const badgeClass = isBuy ? 'chartBadgeBuy' : 'chartBadgeSell';
        const badgeText = isBuy ? '🟢 SETUP ALCISTA (BUY)' : '🔴 SETUP BAJISTA (SELL)';

        return `
          <div class="chartCardWidget">
            <div class="chartWidgetHeader">
              <div class="chartWidgetTitle">
                <span>📊 ${escapeHtml(cd.symbol)}</span>
                <span style="color:var(--m);font-size:12px;">· ${cd.timeframe || 'M5'}</span>
              </div>
              <div class="chartBadge ${badgeClass}">${badgeText}</div>
            </div>
            <div class="chartMetricsGrid">
              <div class="chartMetric">
                <div class="mlab">Precio Actual</div>
                <div class="mval" style="color:#38bdf8">${num(cd.current_price)}</div>
              </div>
              <div class="chartMetric">
                <div class="mlab">Zona Retest (Entrada)</div>
                <div class="mval" style="color:var(--y)">${num(cd.entry_price)}</div>
              </div>
              <div class="chartMetric">
                <div class="mlab">Stop Loss</div>
                <div class="mval" style="color:var(--r)">${num(cd.stop_loss)}</div>
              </div>
              <div class="chartMetric">
                <div class="mlab">Take Profit 1 (1R)</div>
                <div class="mval" style="color:var(--g)">${num(cd.take_profit_1)}</div>
              </div>
            </div>
            ${svg}
            <div class="chartLegend">
              <div class="chartLegendItem"><span class="chartLegendDot" style="background:#38bdf8"></span> Precio Actual</div>
              <div class="chartLegendItem"><span class="chartLegendDot" style="background:${isBuy ? '#00db79' : '#ff453a'}"></span> Zona de Mitigación / OTE</div>
              <div class="chartLegendItem"><span class="chartLegendDot" style="background:#f5bd36"></span> Trayectoria Proyectada (Flecha)</div>
              <div class="chartLegendItem"><span class="chartLegendDot" style="background:var(--r)"></span> Stop Loss</div>
              <div class="chartLegendItem"><span class="chartLegendDot" style="background:var(--g)"></span> Take Profit</div>
            </div>
          </div>
        `;
      }

      function appendChatMessage(sender, text, chartData) {
        const box = document.getElementById('chatBox');
        const bubble = document.createElement('div');
        const hasChart = !!chartData;
        bubble.className = 'msgBubble ' + (sender === 'user' ? 'userBubble' : (hasChart ? 'botBubble hasChartBubble' : 'botBubble'));
        let content = sender === 'user' ? escapeHtml(text) : formatMarkdown(text);
        if (chartData) {
          content += renderChartCard(chartData);
        }
        bubble.innerHTML = content;
        box.appendChild(bubble);
        box.scrollTop = box.scrollHeight;
      }

      let currentConversationSymbol = null;

      async function sendUserMessage(msgText) {
        const text = msgText || document.getElementById('chatInput').value.trim();
        if (!text) return;
        document.getElementById('chatInput').value = '';
        appendChatMessage('user', text);

        // Indicador de tipeo
        const box = document.getElementById('chatBox');
        const typing = document.createElement('div');
        typing.id = 'typingIndicator';
        typing.className = 'msgBubble botBubble muted';
        typing.innerHTML = '<i>Analizando telemetría y estructura de mercado…</i>';
        box.appendChild(typing);
        box.scrollTop = box.scrollHeight;

        try {
          const res = await fetch('/api/operator/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              message: text,
              context_symbol: currentConversationSymbol
            })
          });
          if (!res.ok) throw new Error('HTTP ' + res.status);
          const data = await res.json();
          if (data && data.symbol) {
            currentConversationSymbol = data.symbol;
          }
          typing.remove();
          appendChatMessage('bot', data.reply || 'Sin respuesta del asistente.', data.chart_data);
        } catch (err) {
          typing.remove();
          appendChatMessage('bot', '⚠️ Hubo una dificultad al conectar con el motor de análisis: ' + err.message);
        }
      }

      function sendQuickPrompt(promptText) {
        sendUserMessage(promptText);
      }

      function clearChat() {
        currentConversationSymbol = null;
        fetch('/api/operator/chat/clear', { method: 'POST' }).catch(() => {});
        const box = document.getElementById('chatBox');
        box.innerHTML = `
          <div class="msgBubble botBubble">
            👋 <b>¡Hola, operador!</b> Conversación reiniciada.<br><br>
            Monitoreo continuamente la microestructura de mercado, las confluencias de Smart Money y el Criterio Humano.
            ¿De qué instrumento te gustaría conocer el diagnóstico técnico o deseas consultar <b>qué activo está más cerca de gatillar un trade</b>?
          </div>
        `;
      }

      function toggleChatScroll() {
        const chatWin = document.getElementById('chatBox');
        const btn = document.getElementById('btnToggleScroll');
        const isScroll = chatWin.classList.toggle('scrollMode');
        btn.textContent = isScroll ? '📜 Vista Fluida' : '📦 Scroll Fijo';
        btn.title = isScroll ? 'Restaurar vista fluida sin scroll' : 'Activar scroll interno fijo';
      }

      document.getElementById('btnClearChat').addEventListener('click', clearChat);
      document.getElementById('btnToggleScroll').addEventListener('click', toggleChatScroll);
      document.getElementById('chatSendBtn').addEventListener('click', () => sendUserMessage());
      document.getElementById('chatInput').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          sendUserMessage();
        }
      });

      document.getElementById('btnReload').addEventListener('click', fetchOperatorData);
      fetchOperatorData();
      setInterval(fetchOperatorData, 15000);
    </script>
  </body>
</html>
'''

OPERATOR_HTML = with_page_loading(_OPERATOR_BASE)
