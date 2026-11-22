"""Auditoría visual forense de una operación con velas de Deriv Charts."""

TRADE_AUDIT_HTML = r'''
<!doctype html>
<html lang="es">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>BlackDaemonFX · Auditoría Técnica y Visual del Trade</title>
    <!-- Línea temporal completa · LO QUE VEÍA EN ESE MOMENTO · Contexto técnico persistido -->
    <style>
      :root {
        color-scheme: dark;
        --bg: #050708;
        --p: #0a0e10;
        --p2: #10161a;
        --t: #f5f5f2;
        --m: #9fa8ae;
        --line: #5b4514;
        --gold: #f5bd36;
        --gold-light: #ffd965;
        --green: #21d789;
        --red: #ff5b55;
        --blue: #53a7ff;
      }
      * {
        box-sizing: border-box;
      }
      body {
        margin: 0;
        background: var(--bg);
        color: var(--t);
        font: 14px system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
      }
      .w {
        max-width: 1600px;
        margin: auto;
        padding: 18px;
      }
      .brand,
      .top,
      .toolbar,
      .tabs,
      .layers {
        display: flex;
        align-items: center;
        gap: 9px;
        flex-wrap: wrap;
      }
      .brand {
        border-bottom: 1px solid var(--line);
        padding-bottom: 12px;
      }
      .brand img {
        width: 52px;
        height: 52px;
        border-radius: 10px;
        border: 1px solid #765719;
      }
      .brand b {
        font-size: 20px;
        letter-spacing: 0.05em;
      }
      .brand span,
      .gold {
        color: var(--gold);
      }
      .top {
        justify-content: space-between;
        margin: 17px 0;
      }
      .top h1 {
        margin: 0;
        font-size: 24px;
        font-weight: 800;
        color: #fff;
      }
      .muted {
        color: var(--m);
      }
      .subtags {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 6px;
        align-items: center;
      }
      .subtag {
        display: inline-flex;
        align-items: center;
        background: #141c22;
        border: 1px solid #283742;
        padding: 3px 9px;
        border-radius: 6px;
        font-size: 11.5px;
        color: #c8d4dc;
      }
      .subtag b {
        color: #fff;
        margin-left: 4px;
      }
      .btn,
      .tab {
        color: var(--t);
        background: var(--p2);
        border: 1px solid var(--line);
        padding: 8px 13px;
        border-radius: 8px;
        text-decoration: none;
        font-size: 12px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.15s ease-in-out;
      }
      .btn:hover,
      .tab:hover {
        border-color: var(--gold);
        color: #fff;
      }
      .tab.active {
        background: #49380f;
        color: #ffd965;
        border-color: #9c751e;
        box-shadow: 0 0 10px rgba(245, 189, 54, 0.2);
      }
      .grid {
        display: grid;
        grid-template-columns: repeat(12, minmax(0, 1fr));
        gap: 12px;
      }
      .card {
        background: var(--p);
        border: 1px solid var(--line);
        border-radius: 13px;
        padding: 15px;
        min-width: 0;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.4);
      }
      .kpi {
        grid-column: span 3;
      }
      .full {
        grid-column: 1/-1;
      }
      .chartCard {
        grid-column: span 9;
      }
      .why {
        grid-column: span 3;
      }
      .lab {
        font-size: 11px;
        color: var(--m);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 700;
      }
      .val {
        font-size: 21px;
        font-weight: 850;
        margin-top: 6px;
        letter-spacing: -0.02em;
      }
      .good {
        color: var(--green);
      }
      .bad {
        color: var(--red);
      }
      .chartHead {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 10px;
        flex-wrap: wrap;
        margin-bottom: 12px;
      }
      .chartWrap {
        height: 590px;
        background: #070b0d;
        border: 1px solid #263137;
        border-radius: 10px;
        overflow: hidden;
        position: relative;
      }
      .chartWrap svg {
        width: 100%;
        height: 100%;
        display: block;
      }
      .empty {
        display: grid;
        place-items: center;
        height: 100%;
        padding: 25px;
        text-align: center;
        color: var(--m);
        font-size: 13.5px;
      }
      .source {
        display: inline-block;
        border: 1px solid #26654b;
        background: #0c251c;
        color: #64e6ac;
        border-radius: 99px;
        padding: 4px 10px;
        font-size: 11px;
        font-weight: 800;
      }
      .whyGrid {
        display: grid;
        gap: 8px;
        margin-top: 12px;
      }
      .datum {
        padding: 10px 12px;
        background: var(--p2);
        border-radius: 8px;
        color: var(--m);
        font-size: 11.5px;
        border: 1px solid rgba(255, 255, 255, 0.03);
      }
      .datum b {
        display: block;
        color: var(--t);
        font-size: 13.5px;
        margin-top: 3px;
        overflow-wrap: anywhere;
      }
      .section {
        margin-top: 14px;
        border-top: 1px solid #263137;
        padding-top: 12px;
      }
      .section h3 {
        font-size: 11px;
        color: var(--gold);
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin: 0 0 8px;
      }
      .pill {
        display: inline-block;
        border: 1px solid #3c432f;
        border-radius: 99px;
        padding: 5px 10px;
        margin: 3px;
        font-size: 11px;
        background: #151d22;
        overflow-wrap: anywhere;
        line-height: 1.35;
      }
      .pill.ok {
        border-color: #236345;
        color: #72e5b0;
        background: #0d2319;
      }
      .pill.no {
        border-color: #703a36;
        color: #ff8b85;
        background: #251010;
      }
      .pill.opt {
        border-color: #645522;
        color: #f5cf67;
        background: #221a08;
      }

      /* Estilos del Chatbot Forense */
      .chatCard {
        border-color: #765719;
        background: linear-gradient(180deg, #0e1418 0%, #070a0c 100%);
      }
      .chatHeadRow {
        display: flex;
        align-items: center;
        gap: 12px;
        border-bottom: 1px solid #263137;
        padding-bottom: 12px;
        margin-bottom: 12px;
      }
      .chatAvatar {
        width: 42px;
        height: 42px;
        border-radius: 10px;
        background: #231b08;
        border: 1px solid var(--gold);
        display: grid;
        place-items: center;
        font-size: 22px;
      }
      .quickPills {
        display: flex;
        gap: 7px;
        flex-wrap: wrap;
        margin-bottom: 12px;
      }
      .quickPill {
        background: #141c22;
        border: 1px solid #3c432f;
        color: #f5cf67;
        border-radius: 99px;
        padding: 5px 12px;
        font-size: 11px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.15s ease-in-out;
      }
      .quickPill:hover {
        background: #49380f;
        color: #ffd965;
        border-color: var(--gold);
        box-shadow: 0 0 8px rgba(245, 189, 54, 0.25);
      }
      .chatLogs {
        height: 320px;
        max-height: 420px;
        overflow-y: auto;
        background: #05080a;
        border: 1px solid #1c272e;
        border-radius: 10px;
        padding: 14px;
        display: flex;
        flex-direction: column;
        gap: 12px;
      }
      .chatBubble {
        max-width: 88%;
        padding: 11px 15px;
        border-radius: 10px;
        font-size: 13px;
        line-height: 1.5;
        word-break: break-word;
      }
      .chatBubble.user {
        align-self: flex-end;
        background: #2a200a;
        border: 1px solid #85611c;
        color: #fff;
        border-bottom-right-radius: 2px;
      }
      .chatBubble.bot {
        align-self: flex-start;
        background: #10161b;
        border: 1px solid #283742;
        color: #d8e2e8;
        border-bottom-left-radius: 2px;
      }
      .chatBubble.bot b {
        color: #fff;
      }
      .chatBubble.bot code {
        background: #070b0d;
        border: 1px solid #28353d;
        padding: 1px 5px;
        border-radius: 4px;
        color: #64e6ac;
        font-size: 11.5px;
      }
      .chatBubble.bot ul {
        margin: 6px 0 6px 18px;
        padding: 0;
      }
      .chatBubble.bot li {
        margin-bottom: 4px;
      }
      .chatTime {
        font-size: 10px;
        color: var(--m);
        margin-top: 4px;
        text-align: right;
      }
      .chatForm {
        display: flex;
        gap: 9px;
        margin-top: 12px;
      }
      .chatInput {
        flex: 1;
        background: #0d1317;
        border: 1px solid #2b3942;
        color: #fff;
        padding: 10px 14px;
        border-radius: 8px;
        font-size: 13px;
        outline: none;
      }
      .chatInput:focus {
        border-color: var(--gold);
        box-shadow: 0 0 10px rgba(245, 189, 54, 0.2);
      }
      .chatSendBtn {
        background: #49380f;
        color: #ffd965;
        border: 1px solid #9c751e;
        padding: 0 20px;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 700;
        cursor: pointer;
        transition: all 0.15s ease-in-out;
      }
      .chatSendBtn:hover {
        background: #644d15;
        color: #fff;
        border-color: var(--gold);
      }

      .summary {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 10px;
        margin-top: 10px;
      }
      .mini {
        background: var(--p2);
        padding: 12px;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.04);
      }
      .mini span {
        font-size: 11px;
        color: var(--m);
        text-transform: uppercase;
      }
      .mini b {
        display: block;
        font-size: 16px;
        margin-top: 4px;
        color: #fff;
      }
      .timeline {
        margin-top: 14px;
      }
      .snap {
        display: grid;
        grid-template-columns: 210px 1fr;
        gap: 14px;
        padding: 0 0 14px;
        margin-bottom: 14px;
        border-bottom: 1px solid #263137;
      }
      .snapTime,
      .snapBody {
        background: var(--p2);
        border-radius: 9px;
        padding: 12px;
        border: 1px solid rgba(255, 255, 255, 0.03);
      }
      .json {
        white-space: pre-wrap;
        overflow-wrap: anywhere;
        color: #b8c0c5;
        font: 11px ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        max-height: 230px;
        overflow: auto;
        background: #080d10;
        padding: 10px;
        border-radius: 6px;
        margin-top: 8px;
      }
      .integrity {
        margin-top: 8px;
        font-size: 11.5px;
        color: var(--m);
      }
      @media (max-width: 1050px) {
        .chartCard,
        .why {
          grid-column: 1/-1;
        }
        .whyGrid {
          grid-template-columns: repeat(3, 1fr);
        }
      }
      @media (max-width: 720px) {
        .kpi {
          grid-column: span 6;
        }
        .summary {
          grid-template-columns: repeat(2, 1fr);
        }
        .snap {
          grid-template-columns: 1fr;
        }
        .whyGrid {
          grid-template-columns: 1fr;
        }
        .chartWrap {
          height: 470px;
        }
      }
      @media (max-width: 480px) {
        .kpi {
          grid-column: 1/-1;
        }
        .w {
          padding: 10px;
        }
      }
    </style>
  </head>
  <body>
    <main class="w">
      <div class="brand">
        <img src="/assets/blackdaemonfx_logo_v1.jpeg" alt="Logo" />
        <div>
          <b>BLACKDAEMON<span>FX</span></b>
          <div class="muted">AUDITORÍA FORENSE · EVOLUCIÓN Y DECISIÓN TÉCNICA</div>
        </div>
      </div>
      <div class="top">
        <div>
          <h1 id="title">Cargando trade…</h1>
          <div id="subtitle" class="subtags"></div>
        </div>
        <div class="toolbar">
          <a class="btn" id="excelBtn" href="#">Exportar Excel ↓</a>
          <a class="btn" href="/account">← Volver a Cuenta</a>
          <a class="btn" href="/">Panel Principal</a>
        </div>
      </div>
      <section class="grid">
        <div class="card kpi">
          <div class="lab">Dirección operativa</div>
          <div class="val" id="direction">—</div>
        </div>
        <div class="card kpi">
          <div class="lab">Estado y resultado</div>
          <div class="val" id="status">—</div>
        </div>
        <div class="card kpi">
          <div class="lab">Ratio R:R obtenido</div>
          <div class="val" id="rr">—</div>
        </div>
        <div class="card kpi">
          <div class="lab">PnL neto</div>
          <div class="val" id="pnl">—</div>
        </div>
        <div class="card chartCard">
          <div class="chartHead">
            <div>
              <div class="lab">Gráfico de evidencia técnica</div>
              <div id="chartSub" class="muted">—</div>
            </div>
            <div>
              <div class="tabs">
                <button class="tab active" data-mode="ENTRY">Momento de entrada (Congelado)</button
                ><button class="tab" data-mode="LATEST">Evolución posterior (En vivo)</button>
              </div>
              <div class="tabs" style="margin-top: 7px">
                <button class="tab active" data-tf="M5">M5 (5 min)</button
                ><button class="tab" data-tf="M15">M15 (15 min)</button
                ><button class="tab" data-tf="H1">H1 (1 hora)</button
                ><button class="tab" data-tf="H4">H4 (4 horas)</button>
              </div>
            </div>
          </div>
          <div class="layers">
            <label><input type="checkbox" data-layer="structure" checked /> Estructura (BOS/CHoCH)</label
            ><label><input type="checkbox" data-layer="zones" checked /> Zonas (OB / FVG)</label
            ><label><input type="checkbox" data-layer="levels" checked /> Liquidez y niveles</label
            ><label><input type="checkbox" data-layer="trade" checked /> Niveles Trade (Entrada/SL/TP)</label
            ><label><input type="checkbox" data-layer="volume" checked /> Volumen de ticks</label>
          </div>
          <div id="chart" class="chartWrap"><div class="empty">Cargando velas del gráfico…</div></div>
          <div id="chartIntegrity" class="integrity"></div>
        </div>
        <aside class="card why">
          <div class="lab">Por qué se tomó la operación</div>
          <div id="decision" class="val gold">—</div>
          <div id="why" class="whyGrid"></div>
          <div class="section">
            <h3>Confirmaciones técnicas aprobadas</h3>
            <div id="passed"></div>
          </div>
          <div class="section">
            <h3>Faltantes / Penalizaciones</h3>
            <div id="missing"></div>
          </div>
          <div class="section">
            <h3>Confluencias opcionales</h3>
            <div id="optional"></div>
          </div>
        </aside>

        <!-- SECCIÓN DEL CHATBOT FORENSE INTERACTIVO -->
        <div class="card full chatCard">
          <div class="chatHeadRow">
            <div class="chatAvatar">🤖</div>
            <div>
              <div class="lab" style="color:var(--gold);font-size:12px;">Asistente de Auditoría Forense · Análisis de Resultado y Aprendizaje IA</div>
              <div class="muted" style="font-size:12px;margin-top:2px;">Pregúntale al auditor sobre los motivos de entrada, por qué se ganó o perdió, recorrido MFE/MAE, desvío de Stop Loss y lecciones aprendidas.</div>
            </div>
          </div>
          <div class="quickPills">
            <button class="quickPill" onclick="askAuditChat('¿Por qué se perdió o ganó esta operación?')">🔍 ¿Por qué se ganó o perdió?</button>
            <button class="quickPill" onclick="askAuditChat('¿Por qué se tomó esta entrada y qué confluencias tuvo?')">🎯 Tesis de apertura</button>
            <button class="quickPill" onclick="askAuditChat('¿Llegó a estar en ganancia (MFE) antes del desenlace?')">📈 Recorrido MFE / MAE</button>
            <button class="quickPill" onclick="askAuditChat('¿Se respetó el Stop Loss o hubo deslizamiento?')">🛡️ Deslizamiento y SL</button>
            <button class="quickPill" onclick="askAuditChat('¿Qué confluencias se cumplieron y cuáles faltaron?')">📋 Checklist de confluencias</button>
            <button class="quickPill" onclick="askAuditChat('¿Qué aprendió el modelo de IA de este trade?')">🧠 Aprendizaje IA</button>
          </div>
          <div id="chatMessages" class="chatLogs">
            <!-- Mensajes inyectados dinámicamente -->
          </div>
          <form class="chatForm" onsubmit="submitAuditChat(event)">
            <input type="text" id="chatInput" class="chatInput" placeholder="Escribe tu consulta sobre este trade (ej. ¿Por qué se perdió?, ¿hubo slippage en el SL?)..." autocomplete="off" />
            <button type="submit" class="chatSendBtn">Preguntar ↗</button>
          </form>
        </div>

        <div class="card full">
          <div class="lab">Resumen de evolución del trade</div>
          <div class="summary" id="summary"></div>
        </div>
        <div class="card full">
          <div class="lab">Línea temporal completa y persistente</div>
          <div class="muted" style="font-size: 12px; margin-top: 5px">
            LO QUE VEÍA EN ESE MOMENTO · La vista de entrada es inmutable y congelada. La evolución posterior añade cronológicamente la información real observada en mercado.
          </div>
          <div id="timeline" class="timeline"></div>
        </div>
      </section>
    </main>
    <script>
      const $ = (x) => document.getElementById(x),
        esc = (v) =>
          String(v ?? '—').replace(
            /[&<>"']/g,
            (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c],
          ),
        num = (v, d = 2) => (v == null || !Number.isFinite(Number(v)) ? '—' : Number(v).toFixed(d)),
        money = (v) =>
          v == null
            ? '—'
            : Number(v).toLocaleString('es-CL', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              });

      const CONFIRMATION_LABELS = {
        'FVG_FORMED': 'Fair Value Gap (FVG) formado',
        'fvg_formed': 'Fair Value Gap (FVG) formado',
        'LIQUIDITY_SWEEP': 'Barrido de liquidez previo',
        'liquidity_sweep': 'Barrido de liquidez previo',
        'DISPLACEMENT_DETECTED': 'Desplazamiento fuerte con volumen',
        'displacement_detected': 'Desplazamiento fuerte con volumen',
        'HTF_ALIGNED': 'Marco temporal mayor alineado (H1/H4)',
        'htf_aligned': 'Marco temporal mayor alineado (H1/H4)',
        'OTE_ZONE': 'Entrada en zona óptima OTE (62%-79%)',
        'ote_zone': 'Entrada en zona óptima OTE (62%-79%)',
        'CHOCH_M5': 'Cambio de carácter CHoCH en M5',
        'choch_m5': 'Cambio de carácter CHoCH en M5',
        'ORDER_BLOCK_MITIGATED': 'Mitigación en Order Block clave',
        'order_block_mitigated': 'Mitigación en Order Block clave',
        'GBDT_PROB_GT_0_55': 'Modelo IA favorable (>55% prob.)',
        'gbdt_prob_gt_0_55': 'Modelo IA favorable (>55% prob.)',
        'CLEAN_CORRIDOR_TO_TP': 'Camino despejado hacia Take Profit',
        'clean_corridor_to_tp': 'Camino despejado hacia Take Profit',
        'SESSION_KILLZONE_ACTIVE': 'Dentro de Killzone institucional',
        'session_killzone_active': 'Dentro de Killzone institucional',
        'ENGULFING_CONFIRMED': 'Vela envolvente de rechazo',
        'PINBAR_REJECTION': 'Rechazo claro por mecha (Pinbar)',
        'RESONANCE_ZONE': 'Zona de confluencia técnica',
        'M15_STRUCTURE_CONFIRMED': 'Estructura M15 confirmada',
        'SESSION_OPEN_SWEEP': 'Barrido en apertura de sesión',
        'ADAPTIVE_MOMENTUM_OK': 'Momento técnico favorable',
        'MARKET_STRUCTURE_BREAK': 'Rompimiento estructural válido',
        'SPREAD_PENALTY': 'Penalización por spread elevado',
        'HTF_COUNTER_TREND': 'Contra tendencia en marco mayor (H1/H4)',
        'NO_SWEEP': 'Sin barrido previo de liquidez',
        'SESSION_OUT_OF_KILLZONE': 'Operación fuera de Killzone óptima',
        'LOW_CONFIRMATION_SCORE': 'Puntaje técnico inferior al umbral',
        'CHOPPY_REGIME': 'Mercado lateral o régimen errático',
        'OBSTACLE_BEFORE_TP1': 'Obstáculo estructural antes de TP1',
        'ADVERSE_WICK_DETECTED': 'Mecha de rechazo adversa detectada',
        'HIGH_VOLATILITY_NOISE': 'Ruido excesivo de volatilidad',
        'ENTRY_CAPTURE': 'Captura exacta al momento de entrada (Inmutable)',
        'FIRST_OBSERVATION': 'Primera observación del trade',
        'FIRST_VALID_RISK_OBSERVATION': 'Primera observación con riesgo válido',
        'NO_ENTRY_EVIDENCE': 'Sin evidencia visual previa'
      };

      const META_LABELS = {
        'VALIDAR_CIERRE_COMPLETO_DEL_SETUP': 'En espera de cierre de todo el setup para aprendizaje IA',
        'ELEGIBLE_ENTRADA': 'Apto para reentrenamiento IA (Tesis de entrada completa)',
        'ELEGIBLE_OBSERVACION': 'Apto para reentrenamiento IA (Por observación MT5)',
        'SL_TP_PENDIENTE_RECONCILIACION': 'Pendiente de reconciliación de niveles SL/TP',
        'ESPERANDO_CIERRE_DEL_SETUP': 'Operación activa · Esperando cierre de todas las patas',
        'ESPERANDO_CIERRE': 'Operación en curso · Esperando cierre',
        'CIERRE_MANUAL_EXCLUIDO_DEL_MODELO_DE_ESTRATEGIA': 'Cierre manual por usuario (Excluido de modelos IA)',
        'SIN_CONTEXTO_DE_ENTRADA_NI_OBSERVACION': 'Sin contexto técnico previo registrado',
        'ESQUEMA_DE_FEATURES_ANTIGUO_REQUIERE_MIGRACION': 'Esquema de datos anterior (Requiere migración)',
        'EVIDENCIA_INCOMPLETA_O_RESULTADO_NO_ETIQUETABLE': 'Evidencia incompleta para etiquetado',
        'ENTRY_CAPTURE': 'Captura exacta al entrar (Inmutable)',
        'FIRST_OBSERVATION': 'Primera observación del trade',
        'FIRST_VALID_RISK_OBSERVATION': 'Primera observación con riesgo válido',
        'NO_ENTRY_EVIDENCE': 'Sin captura previa de entrada'
      };

      function humanizeTag(x) {
        if (!x) return '—';
        let raw = typeof x === 'string' ? x : x.label || x.name || JSON.stringify(x);
        let trimmed = String(raw).trim();
        if (CONFIRMATION_LABELS[trimmed]) return CONFIRMATION_LABELS[trimmed];
        let upper = trimmed.toUpperCase();
        if (CONFIRMATION_LABELS[upper]) return CONFIRMATION_LABELS[upper];
        return trimmed
          .replaceAll('ICT_SABRI_MALLE', 'ICT')
          .replaceAll('ICT Sabri Malle', 'ICT')
          .replaceAll('_', ' ')
          .toLowerCase()
          .replace(/^./, (c) => c.toUpperCase());
      }

      function humanizeMetaReason(val) {
        if (!val) return 'Pendiente';
        let s = String(val).trim();
        if (META_LABELS[s]) return META_LABELS[s];
        return s.replaceAll('_', ' ').toLowerCase().replace(/^./, (c) => c.toUpperCase());
      }

      function humanizeEvidence(val) {
        if (!val) return 'Sin captura previa';
        let s = String(val).trim();
        if (META_LABELS[s]) return META_LABELS[s];
        return s.replaceAll('_', ' ').toLowerCase().replace(/^./, (c) => c.toUpperCase());
      }

      function formatDirection(dir) {
        if (!dir) return '—';
        let d = String(dir).toUpperCase();
        if (d === 'BUY') return 'COMPRA (Largo)';
        if (d === 'SELL') return 'VENTA (Corto)';
        return d;
      }

      function formatStatus(status, classification, result) {
        let s = String(status || '').toUpperCase();
        let c = String(classification || result || '').toUpperCase();
        if (s === 'OPEN') return 'Operación Abierta (En curso)';
        if (s === 'CLOSED' || s.includes('CLOSE')) {
          if (c.includes('LOSS') || c.includes('SL') || c.includes('STOP')) return 'Cerrada · Pérdida (Stop Loss)';
          if (c.includes('PROFIT') || c.includes('WIN') || c.includes('TP')) return 'Cerrada · Ganancia (Take Profit)';
          if (c.includes('BE') || c.includes('BREAKEVEN')) return 'Cerrada · Breakeven (Sin riesgo)';
          if (c.includes('EXPIR')) return 'Cerrada · Expirada por tiempo';
          return 'Cerrada' + (c ? ' · ' + humanizeTag(c) : '');
        }
        return (s || '—') + (c ? ' · ' + humanizeTag(c) : '');
      }

      function formatRR(rr) {
        if (rr == null || !Number.isFinite(Number(rr))) return '—';
        let n = Number(rr);
        return (n >= 0 ? '+' : '') + n.toFixed(2) + 'R';
      }

      function formatPnL(pnl) {
        if (pnl == null || !Number.isFinite(Number(pnl))) return '—';
        let n = Number(pnl);
        let sign = n > 0 ? '+$' : n < 0 ? '-$' : '$';
        let formatted = Math.abs(n).toLocaleString('es-CL', {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        });
        return sign + formatted + ' USD';
      }

      function formatAuditDecision(dec) {
        if (!dec) return '—';
        let s = String(dec).trim();
        let up = s.toUpperCase();
        if (up === 'ICT_SABRI_MALLE_CONFIRMED' || up === 'ICT_CONFIRMED') {
          return 'Configuración ICT Confirmada';
        }
        if (up === 'MSNR_CONFIRMED') return 'Configuración Malaysian SNR Confirmada';
        if (up.includes('ORB_NY') || up === 'ORB_CONFIRMED') return 'Configuración New York ORB Confirmada';
        if (up === 'TREND_PULLBACK_CONFIRMED') return 'Configuración Trend Pullback Confirmada';
        if (up === 'WAITING_M5_BREAKOUT_RETEST') return 'En espera de breakout y retesteo M5';
        if (up === 'IN_TRADE') return 'Operación en seguimiento activo';
        if (up === 'TRAILING_ACTIVE') return 'Trailing Stop dinámico activo';
        return s.replaceAll('ICT_SABRI_MALLE', 'ICT').replaceAll('ICT Sabri Malle', 'ICT').replaceAll('_', ' ');
      }

      function formatStrategyName(strat) {
        if (!strat) return '—';
        let s = String(strat).trim();
        let up = s.toUpperCase();
        if (up === 'ICT_SABRI_MALLE' || up === 'ICT') return 'ICT Institucional';
        if (up === 'MSNR' || up === 'MALAYSIAN_SNR') return 'Malaysian SNR';
        if (up === 'ORB' || up === 'ORB_NEW_YORK') return 'New York ORB';
        if (up === 'TREND_PULLBACK') return 'Trend Pullback (H1+M15)';
        if (up === 'SMC') return 'Smart Money Concepts';
        return s.replaceAll('_', ' ');
      }

      function formatTrend(t) {
        if (!t || t === '—') return 'Sin tendencia definida';
        let s = String(t).toUpperCase();
        if (s.includes('BULL') || s.includes('UP') || s.includes('ALCISTA')) return 'Alcista ↗';
        if (s.includes('BEAR') || s.includes('DOWN') || s.includes('BAJISTA')) return 'Bajista ↘';
        if (s.includes('NEUT') || s.includes('SIDE') || s.includes('RANGE')) return 'Lateral / Rango ↔';
        return s.replaceAll('_', ' ');
      }

      function formatConvergence(c) {
        if (c === true || String(c).toUpperCase() === 'CONFIRMADA' || String(c).toUpperCase() === 'TRUE') {
          return 'Confirmada (Alineada ↗↘)';
        }
        if (c === false || String(c).toUpperCase() === 'NO CONFIRMADA' || String(c).toUpperCase() === 'FALSE') {
          return 'No confirmada (Divergente)';
        }
        return 'No evaluada';
      }

      function formatStructure(s) {
        if (!s || s === '—') return 'Sin rompimiento mayor';
        let v = String(s).toUpperCase();
        if (v.includes('BOS_BULL') || v === 'BOS_BUY') return 'Rompimiento alcista (BOS)';
        if (v.includes('BOS_BEAR') || v === 'BOS_SELL') return 'Rompimiento bajista (BOS)';
        if (v.includes('CHOCH_BULL') || v === 'CHOCH_BUY') return 'Cambio de carácter alcista (CHoCH)';
        if (v.includes('CHOCH_BEAR') || v === 'CHOCH_SELL') return 'Cambio de carácter bajista (CHoCH)';
        if (v.includes('BOS')) return 'Rompimiento de estructura (BOS)';
        if (v.includes('CHOCH')) return 'Cambio de carácter (CHoCH)';
        if (v.includes('SWEEP')) return 'Barrido de liquidez';
        if (v.includes('INDUCEMENT')) return 'Inducción de liquidez';
        if (v === 'BULLISH') return 'Estructura alcista';
        if (v === 'BEARISH') return 'Estructura bajista';
        return v.replaceAll('_', ' ');
      }

      function formatZone(z) {
        if (!z || z === '—') return 'Zona no clasificada';
        let v = String(z).toUpperCase();
        if (v.includes('OB_BEAR') || v.includes('ORDER_BLOCK_BEAR')) return 'Order Block bajista M15';
        if (v.includes('OB_BULL') || v.includes('ORDER_BLOCK_BULL')) return 'Order Block alcista M15';
        if (v.includes('FVG_UNMITIGATED')) return 'Fair Value Gap sin mitigar';
        if (v.includes('FVG')) return 'Fair Value Gap (FVG)';
        if (v.includes('PREMIUM')) return 'Zona Premium (Venta en zona cara)';
        if (v.includes('DISCOUNT')) return 'Zona Discount (Compra en zona barata)';
        if (v.includes('EQUILIBRIUM')) return 'Zona de equilibrio (50%)';
        if (v.includes('BREAKER')) return 'Breaker Block institucional';
        if (v.includes('MITIGATION')) return 'Bloque de mitigación';
        return v.replaceAll('_', ' ');
      }

      function formatScore(score) {
        if (score == null || score === '' || isNaN(Number(score))) return '—';
        let n = Number(score);
        if (n >= 85) return n + ' / 100 · Alta convicción';
        if (n >= 75) return n + ' / 100 · Aprobado';
        return n + ' / 100 · Condicional';
      }

      function formatPlannedRR(rr) {
        if (rr == null || !Number.isFinite(Number(rr))) return '—';
        let n = Number(rr);
        return '1 : ' + n.toFixed(2) + ' (+' + n.toFixed(2) + 'R)';
      }

      function formatRiskPercent(r) {
        if (r == null || !Number.isFinite(Number(r))) return '—';
        return Number(r).toFixed(2) + '% del balance';
      }

      let audit = null,
        mode = 'ENTRY',
        tf = 'M5',
        layers = { structure: true, zones: true, levels: true, trade: true, volume: true };

      function pills(a, cls) {
        let arr = a || [];
        if (!arr.length) {
          if (cls === 'ok') return '<span class="muted">Ninguna confirmación registrada</span>';
          if (cls === 'no') return '<span class="good" style="font-size:11.5px">✓ Sin penalizaciones ni filtros faltantes</span>';
          return '<span class="muted">Ninguna</span>';
        }
        return arr
          .map(
            (x) =>
              '<span class="pill ' +
              cls +
              '">' +
              esc(humanizeTag(x)) +
              '</span>',
          )
          .join('');
      }

      function nearest(c, time) {
        if (!time || !c.length) return null;
        let t = new Date(time).getTime(),
          best = null,
          dist = Infinity;
        c.forEach((q, i) => {
          let d = Math.abs(new Date(q.time).getTime() - t);
          if (d < dist) {
            dist = d;
            best = i;
          }
        });
        return best;
      }

      function draw() {
        if (!audit) return;
        let charts = audit.charts || {},
          root = mode === 'ENTRY' ? charts.entry : charts.latest,
          ci = audit.chart_integrity || {},
          box = $('chart');
        if (!root || !Object.keys(root).length) {
          box.innerHTML =
            '<div class="empty">' +
            (mode === 'ENTRY'
              ? 'Este trade no posee un gráfico inmutable de entrada. No se proyecta con datos posteriores para preservar el rigor forense.'
              : 'Todavía no existe un refresco gráfico posterior.') +
            '</div>';
          return;
        }
        let frame = (root.timeframes || {})[tf] || {},
          c = (frame.candles || []).slice(-120);
        if (!c.length) {
          box.innerHTML =
            '<div class="empty">No existen velas persistidas en temporalidad ' +
            esc(tf) +
            ' para esta captura.</div>';
          return;
        }
        const W = 1120,
          H = 570,
          p = { l: 58, r: 125, t: 24, b: 32 },
          volH = layers.volume ? 100 : 0,
          gap = layers.volume ? 25 : 0,
          priceBottom = H - p.b - volH - gap,
          priceH = priceBottom - p.t,
          plotW = W - p.l - p.r;
        let vals = c.flatMap((q) => [Number(q.low), Number(q.high)]).filter(Number.isFinite),
          trade = audit.trade || {};
        if (layers.trade)
          [trade.entry_price, trade.stop_loss, trade.take_profit]
            .map(Number)
            .filter(Number.isFinite)
            .forEach((v) => vals.push(v));
        let lo = Math.min(...vals),
          hi = Math.max(...vals),
          span = hi - lo || Math.max(1, Math.abs(hi) * 0.01);
        lo -= span * 0.08;
        hi += span * 0.08;
        const x = (i) => p.l + ((i + 0.5) * plotW) / c.length,
          y = (v) => p.t + ((hi - Number(v)) / (hi - lo)) * priceH,
          cw = Math.max(2, (plotW / c.length) * 0.58),
          timeMap = new Map(c.map((q, i) => [String(q.time).slice(0, 16), i]));
        let out = '<svg viewBox="0 0 ' + W + ' ' + H + '" preserveAspectRatio="none">';
        for (let i = 0; i < 6; i++) {
          let yy = p.t + (i * priceH) / 5,
            val = hi - (i * (hi - lo)) / 5;
          out +=
            '<line x1="' +
            p.l +
            '" y1="' +
            yy +
            '" x2="' +
            (W - p.r) +
            '" y2="' +
            yy +
            '" stroke="#1d2a30"/><text x="' +
            (W - p.r + 8) +
            '" y="' +
            (yy + 4) +
            '" fill="#91a0a8" font-size="11">' +
            num(val, 4) +
            '</text>';
        }
        if (layers.zones)
          (frame.zones || []).forEach((z) => {
            let zl = Number(z.low),
              zh = Number(z.high),
              i = nearest(c, z.time);
            if (!Number.isFinite(zl) || !Number.isFinite(zh) || i == null) return;
            let col = z.direction === 'BUY' ? '#1a835d' : '#9b403c';
            out +=
              '<rect x="' +
              x(i) +
              '" y="' +
              y(zh) +
              '" width="' +
              Math.max(2, W - p.r - x(i)) +
              '" height="' +
              Math.max(2, y(zl) - y(zh)) +
              '" fill="' +
              col +
              '" opacity=".18"><title>' +
              esc(humanizeTag(z.label)) +
              ' · ' +
              esc(humanizeTag(z.status)) +
              '</title></rect>';
          });
        if (layers.levels)
          (frame.levels || []).forEach((l) => {
            let v = Number(l.price);
            if (!Number.isFinite(v)) return;
            out +=
              '<line x1="' +
              p.l +
              '" y1="' +
              y(v) +
              '" x2="' +
              (W - p.r) +
              '" y2="' +
              y(v) +
              '" stroke="#9d78d5" stroke-dasharray="3 5" opacity=".7"><title>' +
              esc(humanizeTag(l.label)) +
              '</title></line>';
          });
        c.forEach((q, i) => {
          let xx = x(i),
            yo = y(q.open),
            yc = y(q.close),
            up = Number(q.close) >= Number(q.open),
            col = up ? '#31c48d' : '#ef6a6a';
          out +=
            '<g><title>' +
            new Date(q.time).toLocaleString('es-CL') +
            ' · Apertura ' +
            q.open +
            ' · Máx ' +
            q.high +
            ' · Mín ' +
            q.low +
            ' · Cierre ' +
            q.close +
            '</title><line x1="' +
            xx +
            '" y1="' +
            y(q.high) +
            '" x2="' +
            xx +
            '" y2="' +
            y(q.low) +
            '" stroke="' +
            col +
            '"/><rect x="' +
            (xx - cw / 2) +
            '" y="' +
            Math.min(yo, yc) +
            '" width="' +
            cw +
            '" height="' +
            Math.max(1, Math.abs(yc - yo)) +
            '" fill="' +
            col +
            '"/></g>';
        });
        if (layers.structure)
          (frame.events || []).forEach((ev) => {
            let i = timeMap.get(String(ev.time).slice(0, 16));
            if (i == null) return;
            let v = Number(ev.price);
            if (!Number.isFinite(v)) v = ev.direction === 'BUY' ? c[i].low : c[i].high;
            let bull = ev.direction === 'BUY',
              yy = y(v),
              col = bull ? '#53a7ff' : '#f5bd36';
            out +=
              '<circle cx="' +
              x(i) +
              '" cy="' +
              yy +
              '" r="4" fill="' +
              col +
              '"><title>' +
              esc(humanizeTag(ev.label)) +
              '</title></circle><text x="' +
              x(i) +
              '" y="' +
              (yy + (bull ? 15 : -8)) +
              '" text-anchor="middle" fill="' +
              col +
              '" font-size="8.5" font-weight="700">' +
              esc(humanizeTag(ev.label)) +
              '</text>';
          });
        if (layers.trade) {
          [
            ['Entrada', trade.entry_price, '#53a7ff'],
            ['Stop Loss', trade.stop_loss, '#ff5b55'],
            ['Take Profit', trade.take_profit, '#21d789'],
          ].forEach(([lab, v, col]) => {
            v = Number(v);
            if (!Number.isFinite(v)) return;
            out +=
              '<line x1="' +
              p.l +
              '" y1="' +
              y(v) +
              '" x2="' +
              (W - p.r) +
              '" y2="' +
              y(v) +
              '" stroke="' +
              col +
              '" stroke-width="1.6" stroke-dasharray="7 5"/><text x="' +
              (p.l + 5) +
              '" y="' +
              (y(v) - 4) +
              '" fill="' +
              col +
              '" font-size="10" font-weight="700">' +
              lab +
              ' ' +
              num(v, 5) +
              '</text>';
          });
          let ei = nearest(c, trade.entry_time);
          if (ei != null)
            out +=
              '<line x1="' +
              x(ei) +
              '" y1="' +
              p.t +
              '" x2="' +
              x(ei) +
              '" y2="' +
              priceBottom +
              '" stroke="#53a7ff" stroke-width="1.4" stroke-dasharray="3 4"/><text x="' +
              (x(ei) + 5) +
              '" y="' +
              (p.t + 14) +
              '" fill="#53a7ff" font-size="10" font-weight="800">ENTRADA</text>';
        }
        if (layers.volume) {
          let vols = c.map((q) => Number(q.volume) || 0),
            vm = Math.max(...vols, 1),
            top = priceBottom + gap;
          out +=
            '<text x="' +
            p.l +
            '" y="' +
            (top + 10) +
            '" fill="#91a0a8" font-size="10">VOLUMEN DE TICKS DERIV</text>';
          c.forEach((q, i) => {
            let h = ((Number(q.volume) || 0) / vm) * (volH - 15),
              col = Number(q.close) >= Number(q.open) ? '#23795c' : '#8b3f3d';
            out +=
              '<rect x="' +
              (x(i) - cw / 2) +
              '" y="' +
              (top + volH - h) +
              '" width="' +
              cw +
              '" height="' +
              h +
              '" fill="' +
              col +
              '" opacity=".7"/>';
          });
        }
        [0, Math.floor((c.length - 1) / 2), c.length - 1].forEach((i) => {
          out +=
            '<text x="' +
            x(i) +
            '" y="' +
            (H - 8) +
            '" text-anchor="middle" fill="#91a0a8" font-size="10">' +
            new Date(c[i].time).toLocaleString('es-CL', {
              day: '2-digit',
              month: '2-digit',
              hour: '2-digit',
              minute: '2-digit',
            }) +
            '</text>';
        });
        out += '</svg>';
        box.innerHTML = out;
        let stamp =
          mode === 'ENTRY'
            ? ci.entry_captured_at || root.captured_at
            : ci.latest_updated_at || root.updated_at;
        $('chartSub').innerHTML =
          '<span class="source">' +
          esc(ci.data_source || root.data_source || 'DERIV CHARTS') +
          '</span> · ' +
          esc(
            mode === 'ENTRY' ? 'Evidencia congelada al entrar (Inmutable)' : 'Mercado observado posteriormente (Evolución)',
          ) +
          ' · ' +
          esc(tf) +
          ' · ' +
          c.length +
          ' velas';
        $('chartIntegrity').textContent =
          (mode === 'ENTRY' ? 'No se recalcula con información futura (rigor forense). ' : '') +
          'Captura registrada: ' +
          (stamp ? new Date(stamp).toLocaleString('es-CL') : 'no disponible');
      }

      function why(e) {
        e = e || {};
        $('decision').textContent = formatAuditDecision(e.decision || e.state || '—');
        let f = [
          ['Estrategia', formatStrategyName(e.strategy_name)],
          ['Tendencia H4', formatTrend(e.h4_trend)],
          ['Tendencia H1', formatTrend(e.h1_trend)],
          ['Convergencia H4/H1', formatConvergence(e.h4_h1_convergence)],
          ['Estructura M15', formatStructure(e.structure_break)],
          ['Zona operativa', formatZone(e.zone)],
          ['Puntuación técnica', formatScore(e.score)],
          [
            'Nivel de confirmación',
            e.confirmation_percentage == null ? '—' : e.confirmation_percentage + '% de confluencias',
          ],
          ['R:R proyectado', formatPlannedRR(e.planned_rr)],
          ['Riesgo asumido', formatRiskPercent(e.risk_percent)],
        ];
        $('why').innerHTML = f
          .map((q) => '<div class="datum">' + esc(q[0]) + '<b>' + esc(q[1] ?? '—') + '</b></div>')
          .join('');
        $('passed').innerHTML = pills(
          e.passed || e.passed_confirmations || e.confirmations_passed,
          'ok',
        );
        $('missing').innerHTML = pills(
          [...(e.missing || e.missing_confirmations || []), ...(e.critical_failures || [])],
          'no',
        );
        let o = [];
        o.push(
          e.harmonic_confirmed
            ? 'Patrón armónico: ' + humanizeTag(e.harmonic_pattern || 'confirmado')
            : 'Patrón armónico: no detectado (opcional)',
        );
        o.push(
          e.chart_pattern_confirmed
            ? 'Patrón chartista: ' + humanizeTag(e.chart_pattern_name || 'confirmado')
            : 'Patrón chartista: no detectado (opcional)',
        );
        if (e.divergence_confirmed) o.push('Divergencia confirmada en oscilador');
        $('optional').innerHTML = pills(o, 'opt');
      }

      function timelineItem(x, i) {
        let c = x.current_view || {},
          m = x.market || {},
          total = (audit && audit.snapshots) ? audit.snapshots.length : 0,
          tagLabel = i === 0 ? ' · Entrada al mercado' : (i === total - 1 ? ' · Último estado observado' : '');
        let rrVal = Number(m.current_rr);
        let rrText = Number.isFinite(rrVal) ? (rrVal >= 0 ? '+' : '') + rrVal.toFixed(2) + 'R' : '0.00R';
        let dec = formatAuditDecision(c.decision || c.state || c.action || '—');
        let reason = c.reason ? humanizeTag(c.reason) : 'Seguimiento normal en mercado';
        let priceText = 'Cotización: ' + (m.current_price != null ? num(m.current_price, 5) : '—') +
          ' · Stop Loss: ' + (m.current_stop_loss != null ? num(m.current_stop_loss, 5) : '—') +
          ' · Take Profit: ' + (m.take_profit != null ? num(m.take_profit, 5) : '—');
        return (
          '<article class="snap"><div class="snapTime"><b>Punto de control #' +
          (i + 1) + tagLabel +
          '</b><br><span class="muted">' +
          esc(x.snapshot_at ? new Date(x.snapshot_at).toLocaleString('es-CL') : '—') +
          '</span><div class="val ' +
          (rrVal >= 0 ? 'good' : 'bad') +
          '">' +
          esc(rrText) +
          '</div></div><div class="snapBody"><b style="font-size:14px;color:var(--gold)">' +
          esc(dec) +
          '</b><div class="muted" style="margin-top:3px">' +
          esc(reason) +
          '</div><div style="margin-top:8px;font-size:12px;background:rgba(255,255,255,0.03);padding:6px 10px;border-radius:6px">' +
          priceText +
          '</div><details style="margin-top:8px"><summary class="muted" style="cursor:pointer;font-size:11px">Contexto técnico persistido (Ver telemetría detallada)</summary><pre class="json">' +
          esc(
            JSON.stringify(
              { current_view: c, market: m, visual_context: x.visual_context || {} },
              null,
              2,
            ),
          ) +
          '</pre></details></div></article>'
        );
      }

      function formatChatMarkdown(text) {
        if (!text) return '';
        let s = String(text);
        s = s.replace(/```([\s\S]*?)```/g, (m, c) => '<pre class="json">' + esc(c.trim()) + '</pre>');
        s = s.replace(/`([^`]+)`/g, (m, c) => '<code>' + esc(c) + '</code>');
        s = s.replace(/\*\*([^*]+)\*\*/g, (m, c) => '<b>' + c + '</b>');
        s = s.replace(/\*([^*]+)\*/g, (m, c) => '<i>' + c + '</i>');
        s = s.replace(/^[•\-]\s+(.*)$/gm, '<li>$1</li>');
        s = s.replace(/(<li>.*<\/li>)/g, '<ul>$1</ul>');
        s = s.replace(/<\/ul>\s*<ul>/g, '');
        s = s.replace(/\n\n/g, '<br><br>').replace(/\n/g, '<br>');
        return s;
      }

      function appendChatMessage(role, text) {
        const box = $('chatMessages');
        if (!box) return;
        const timeStr = new Date().toLocaleTimeString('es-CL', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        const bubble = document.createElement('div');
        bubble.className = 'chatBubble ' + (role === 'user' ? 'user' : 'bot');
        bubble.innerHTML = formatChatMarkdown(text) + '<div class="chatTime">' + timeStr + '</div>';
        box.appendChild(bubble);
        box.scrollTop = box.scrollHeight;
      }

      async function askAuditChat(promptText) {
        if (!promptText || !audit) return;
        appendChatMessage('user', promptText);
        const t = audit.trade || {};
        const tid = t.id ?? t.source_trade_id;

        // Bubble de espera
        const waitId = 'wait_' + Date.now();
        const waitBubble = document.createElement('div');
        waitBubble.id = waitId;
        waitBubble.className = 'chatBubble bot';
        waitBubble.innerHTML = '<span class="muted">⏳ Analizando expediente forense...</span>';
        $('chatMessages').appendChild(waitBubble);
        $('chatMessages').scrollTop = $('chatMessages').scrollHeight;

        try {
          const endpoint = '/api/account/trade/' + tid + '/audit/chat';
          const res = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: promptText }),
          });
          const waitEl = $(waitId);
          if (waitEl) waitEl.remove();

          if (res.ok) {
            const data = await res.json();
            appendChatMessage('bot', data.reply || 'Sin respuesta del auditor.');
          } else {
            // Fallback en cliente
            appendChatMessage('bot', 'No se pudo conectar con el endpoint de chat (' + res.status + ').');
          }
        } catch (err) {
          const waitEl = $(waitId);
          if (waitEl) waitEl.remove();
          appendChatMessage('bot', 'Error de comunicación: ' + err.message);
        }
      }

      function submitAuditChat(e) {
        e.preventDefault();
        const inp = $('chatInput');
        if (!inp) return;
        const val = inp.value.trim();
        if (!val) return;
        inp.value = '';
        askAuditChat(val);
      }

      function initAuditChat(a) {
        const box = $('chatMessages');
        if (!box || box.children.length > 0) return;
        const t = a.trade || {};
        const tid = t.id ?? t.source_trade_id ?? '—';
        const inst = t.instrument || 'Operación';
        const dir = formatDirection(t.direction);
        const st = formatStatus(t.status, t.classification, t.result);
        const rr = formatRR(t.realized_rr);
        const pnl = formatPnL(t.net_pnl);

        const welcome = '👋 **Hola. Soy el Asistente Forense de BlackDaemonFX.**\n\n' +
          'He cargado el expediente completo del **Trade #' + tid + '** en **' + inst + '** (' + dir + ' · ' + st + ' · ' + rr + ' · ' + pnl + ').\n\n' +
          'Puedes consultarme sobre:\n' +
          '• **¿Por qué se ganó o se perdió la entrada?**\n' +
          '• **¿Qué confluencias se cumplieron al entrar y cuáles faltaron?**\n' +
          '• **¿Llegó a estar en ganancia (MFE) antes del desenlace?**\n' +
          '• **¿Se respetó el Stop Loss o hubo deslizamiento?**\n' +
          '• **¿Qué aprendió la IA o el modelo GBDT de este trade?**\n\n' +
          'Haz clic en una de las consultas rápidas arriba o escribe tu pregunta abajo.';
        appendChatMessage('bot', welcome);
      }

      function render(a) {
        audit = a;
        let t = a.trade || {},
          s = a.snapshots || [],
          e = a.entry_view || {},
          rrs = s.map((x) => Number((x.market || {}).current_rr)).filter(Number.isFinite);
        $('excelBtn').href = '/api'+location.pathname+'/excel';
        $('title').textContent =
          (t.instrument || 'Operación') + ' · Trade #' + (t.id ?? t.source_trade_id ?? '—');

        const entryDateStr = t.entry_time ? new Date(t.entry_time).toLocaleString('es-CL') : '—';
        const snapshotCount = s.length;
        const dataSource = (a.chart_integrity || {}).data_source === 'DERIV_CHARTS' ? 'Velas Deriv Charts' : ((a.chart_integrity || {}).data_source || 'Deriv Charts');
        const rawEv = (a.learning_eligibility || {}).evidence_type || 'NO_ENTRY_EVIDENCE';
        const rawReason = (a.learning_eligibility || {}).reason || 'pendiente';
        const humanEv = humanizeEvidence(rawEv);
        const humanReason = humanizeMetaReason(rawReason);

        let subHtml = '<div class="subtag">Entrada: <b>' + esc(entryDateStr) + '</b></div>' +
          '<div class="subtag">' + snapshotCount + ' <b>' + (snapshotCount === 1 ? 'snapshot de seguimiento' : 'snapshots de seguimiento') + '</b></div>' +
          '<div class="subtag">Fuente: <b>' + esc(dataSource) + '</b></div>' +
          '<div class="subtag">Evidencia: <b>' + esc(humanEv) + '</b></div>' +
          '<div class="subtag">Meta-etiquetado IA: <b>' + esc(humanReason) + '</b></div>';

        const metadata = (t.details || {}).metadata || {};
        const corridor = (metadata.entry_preflight || {}).path || {};
        if (typeof corridor.full_path_clear === 'boolean') {
          let cDesc = corridor.full_path_clear ? 'Despejado sin obstáculos' : 'Con obstáculos';
          if (corridor.free_r_to_first_obstacle != null) {
            cDesc += ' (1º obstáculo a ' + num(corridor.free_r_to_first_obstacle) + 'R)';
          }
          subHtml += '<div class="subtag">Recorrido al TP: <b>' + esc(cDesc) + '</b></div>';
        }
        $('subtitle').innerHTML = subHtml;

        $('direction').textContent = formatDirection(t.direction);
        if (String(t.direction || '').toUpperCase() === 'BUY') {
          $('direction').className = 'val good';
        } else if (String(t.direction || '').toUpperCase() === 'SELL') {
          $('direction').className = 'val bad';
        }

        $('status').textContent = formatStatus(t.status, t.classification, t.result);
        $('rr').textContent = formatRR(t.realized_rr);
        let rrNum = Number(t.realized_rr || 0);
        $('rr').className = 'val ' + (rrNum > 0 ? 'good' : rrNum < 0 ? 'bad' : '');

        $('pnl').textContent = formatPnL(t.net_pnl);
        let pnlNum = Number(t.net_pnl || 0);
        $('pnl').className = 'val ' + (pnlNum > 0 ? 'good' : pnlNum < 0 ? 'bad' : '');

        why(e);

        let maxR = rrs.length ? Math.max(...rrs) : null;
        let minR = rrs.length ? Math.min(...rrs) : null;
        let maxRText = maxR != null ? (maxR >= 0 ? '+' : '') + num(maxR) + 'R' : '—';
        let minRText = minR != null ? (minR >= 0 ? '+' : '') + num(minR) + 'R' : '—';

        $('summary').innerHTML =
          '<div class="mini"><span>Puntos de seguimiento</span><b>' +
          s.length + ' snapshots' +
          '</b></div><div class="mini"><span>Máx. ganancia (MFE observado)</span><b class="good">' +
          maxRText +
          '</b></div><div class="mini"><span>Máx. retroceso (MAE observado)</span><b class="bad">' +
          minRText +
          '</b></div><div class="mini"><span>Auditoría visual al entrar</span><b>' +
          ((a.chart_integrity || {}).entry_chart_present ? 'Íntegra (Inmutable)' : 'No disponible') +
          '</b></div><div class="mini"><span>Conflictos excluidos</span><b>' +
          esc((a.audit_integrity || {}).identity_conflicts_removed || 0) + ' anomalías' +
          '</b></div>';

        $('timeline').innerHTML =
          s.map(timelineItem).join('') ||
          '<div class="empty">Este trade todavía no tiene snapshots históricos registrados.</div>';
        draw();
        initAuditChat(a);
      }

      document.querySelectorAll('[data-mode]').forEach(
        (b) =>
          (b.onclick = () => {
            mode = b.dataset.mode;
            document
              .querySelectorAll('[data-mode]')
              .forEach((x) => x.classList.toggle('active', x === b));
            draw();
          }),
      );
      document.querySelectorAll('[data-tf]').forEach(
        (b) =>
          (b.onclick = () => {
            tf = b.dataset.tf;
            document
              .querySelectorAll('[data-tf]')
              .forEach((x) => x.classList.toggle('active', x === b));
            draw();
          }),
      );
      document.querySelectorAll('[data-layer]').forEach(
        (c) =>
          (c.onchange = () => {
            layers[c.dataset.layer] = c.checked;
            draw();
          }),
      );

      async function go() {
        try {
          let r = await fetch('/api' + location.pathname + '?x=' + Date.now(), {
            cache: 'no-store',
          });
          if (!r.ok) throw new Error(await r.text());
          render(await r.json());
        } catch (err) {
          $('title').textContent = 'No se pudo cargar la auditoría';
          $('subtitle').textContent = err.message;
        }
      }
      go();
    </script>
  </body>
</html>
'''
