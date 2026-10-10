"""Plantilla HTML de la pantalla "Cuenta activa" del dashboard.

Modulo de un solo dato: `ACCOUNT_HTML`, una cadena cruda con la pagina completa
(HTML + CSS + JS). Se mantiene aparte para que el servidor no cargue con
cientos de lineas de markup.

La pagina consume por fetch el payload de `dashboard.account_metrics` e incluye
el bloque "Meta-etiquetado con IA" (senales analizadas, modo sombra, filtradas,
probabilidad media y mejoras aplicadas).

Vinculaciones:
    - `dashboard.realtime_dashboard`: sirve esta cadena en la ruta `/account`.
    - `dashboard.account_metrics.build_account_payload`: datos que rellenan los
      identificadores del DOM referenciados aqui.
"""

ACCOUNT_HTML = r'''
<!doctype html>
<html lang="es">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>DaemonBlackFx · Cuenta activa</title>
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
        max-width: 1720px;
        margin: auto;
        padding: 18px 24px;
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
      }
      .grid {
        display: grid;
        grid-template-columns: repeat(12, 1fr);
        gap: 12px;
        margin-top: 15px;
      }
      .c {
        background: var(--p);
        border: 1px solid var(--l);
        border-radius: 14px;
        padding: 14px;
        min-width: 0;
        box-shadow: inset 0 1px 0 rgba(255, 211, 102, 0.03);
      }
      .k {
        grid-column: span 3;
      }
      .half {
        grid-column: span 6;
      }
      .full {
        grid-column: 1/-1;
      }
      .lab {
        color: var(--m);
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.06em;
      }
      .val {
        font-size: 25px;
        font-weight: 800;
        margin-top: 5px;
      }
      .stats {
        display: grid;
        grid-template-columns: repeat(6, 1fr);
        gap: 8px;
        margin-top: 10px;
      }
      .s {
        background: var(--p2);
        padding: 10px;
        border-radius: 9px;
        min-width: 0;
      }
      .s b {
        display: block;
        font-size: 19px;
      }
      .bar {
        height: 14px;
        background: #192a37;
        border-radius: 99px;
        overflow: hidden;
        display: flex;
        margin: 12px 0;
      }
      .leg {
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
        color: var(--m);
        font-size: 12px;
      }
      .ranking {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 9px;
        margin-top: 10px;
      }
      .strategy {
        padding: 11px;
        background: var(--p2);
        border: 1px solid #263139;
        border-radius: 10px;
      }
      .strategyHead {
        display: flex;
        justify-content: space-between;
        gap: 8px;
        font-weight: 800;
      }
      .strategyMeta {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        color: var(--m);
        font-size: 11px;
        margin-top: 7px;
      }
      .strategy .profit {
        font-size: 16px;
      }
      .good {
        color: var(--g);
      }
      .bad {
        color: var(--r);
      }
      .warn {
        color: var(--y);
      }
      .historyHead {
        display: flex;
        justify-content: space-between;
        gap: 12px;
        align-items: end;
        flex-wrap: wrap;
      }
      .tbl {
        overflow-y: auto;
        overflow-x: hidden;
        max-height: 620px;
        margin-top: 10px;
        border: 1px solid var(--l);
        border-radius: 9px;
      }
      table {
        width: 100%;
        max-width: 100%;
        border-collapse: collapse;
        table-layout: fixed;
      }
      th,
      td {
        padding: 10px 8px;
        border-bottom: 1px solid #302914;
        text-align: left;
        vertical-align: top;
        font-size: 12px;
        overflow-wrap: anywhere;
      }
      th {
        color: var(--m);
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        position: sticky;
        top: 0;
        background: var(--p);
        z-index: 2;
      }
      th:nth-child(1),
      td:nth-child(1) {
        width: 34px;
        text-align: center;
        padding-left: 6px;
        padding-right: 6px;
      }
      th:nth-child(2),
      td:nth-child(2) {
        width: 6%;
      }
      th:nth-child(3),
      td:nth-child(3) {
        width: 16%;
      }
      th:nth-child(4),
      td:nth-child(4) {
        width: 12%;
      }
      th:nth-child(5),
      td:nth-child(5) {
        width: 16%;
      }
      th:nth-child(6),
      td:nth-child(6) {
        width: 14%;
      }
      th:nth-child(7),
      td:nth-child(7) {
        width: 20%;
      }
      th:nth-child(8),
      td:nth-child(8) {
        width: auto;
      }
      .dayOpsTable th,
      .dayOpsTable td {
        vertical-align: middle;
      }
      .dayOpsTable th:nth-child(1),
      .dayOpsTable td:nth-child(1) { width: 36px; text-align: center; }
      .dayOpsTable th:nth-child(2),
      .dayOpsTable td:nth-child(2) { width: 95px; }
      .dayOpsTable th:nth-child(3),
      .dayOpsTable td:nth-child(3) { width: 75px; }
      .dayOpsTable th:nth-child(4),
      .dayOpsTable td:nth-child(4) { width: 110px; }
      .dayOpsTable th:nth-child(5),
      .dayOpsTable td:nth-child(5) { width: 135px; }
      .dayOpsTable th:nth-child(6),
      .dayOpsTable td:nth-child(6) { width: 70px; }
      .dayOpsTable th:nth-child(7),
      .dayOpsTable td:nth-child(7) { width: 80px; }
      .dayOpsTable th:nth-child(8),
      .dayOpsTable td:nth-child(8) { width: 120px; }
      .dayOpsTable th:nth-child(9),
      .dayOpsTable td:nth-child(9) { width: 125px; }
      .dayOpsTable th:nth-child(10),
      .dayOpsTable td:nth-child(10) { width: 70px; }
      .dayOpsTable th:nth-child(11),
      .dayOpsTable td:nth-child(11) { width: auto; min-width: 290px; }
      .tradeMeta {
        color: var(--m);
        font-size: 11px;
        margin-top: 3px;
      }
      .auditCard {
        display: grid;
        gap: 7px;
        min-width: 0;
        padding: 9px;
        border: 1px solid #4a3b18;
        border-radius: 10px;
        background: linear-gradient(180deg, #111710, #0b0f11);
        box-shadow: inset 3px 0 0 var(--b);
      }
      .auditDecision {
        color: var(--y);
        font-weight: 850;
        font-size: 11px;
        line-height: 1.3;
        overflow-wrap: anywhere;
      }
      .auditMeta {
        display: flex;
        gap: 5px;
        flex-wrap: wrap;
      }
      .auditStat {
        display: inline-flex;
        align-items: center;
        padding: 3px 6px;
        border: 1px solid #3d351d;
        border-radius: 6px;
        background: #151a1c;
        color: var(--m);
        font-size: 10px;
      }
      .auditStat b {
        color: var(--t);
        margin-left: 3px;
      }
      .auditPattern {
        font-size: 10px;
        color: var(--m);
        line-height: 1.35;
      }
      .auditPattern b {
        color: var(--g);
      }
      .auditOpen {
        display: flex;
        align-items: center;
        justify-content: center;
        margin-top: 1px;
        padding: 6px 7px;
        border-color: #765719;
        color: #ffd465;
        font-size: 10px;
        font-weight: 750;
        text-align: center;
      }
      .pill {
        display: inline-block;
        border: 1px solid var(--l);
        border-radius: 99px;
        padding: 2px 7px;
        margin: 2px;
        font-size: 10px;
      }
      .empty {
        color: var(--m);
        padding: 18px;
      }
      input.rowSelect,
      #selectAllRows {
        width: 15px;
        height: 15px;
        accent-color: var(--b);
        cursor: pointer;
      }
      .btn:disabled {
        opacity: 0.45;
        cursor: not-allowed;
      }
      @media (max-width: 900px) {
        .k,
        .half {
          grid-column: span 6;
        }
        .stats {
          grid-template-columns: repeat(3, 1fr);
        }
      }
      @media (max-width: 560px) {
        .w {
          padding: 10px;
        }
        .k,
        .half {
          grid-column: 1/-1;
        }
        .stats {
          grid-template-columns: repeat(2, 1fr);
        }
        .brand {
          margin-bottom: 10px;
        }
      }
      .nav .btn:hover {
        border-color: #f4ce63;
        color: #f4ce63;
      }

      /* ========================================================
         CALENDARIO MENSUAL DE RENDIMIENTO & INSPECTOR DIARIO
         ======================================================== */
      .calHeaderBar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 10px;
        margin-top: 10px;
        padding-bottom: 12px;
        border-bottom: 1px solid #1c262e;
      }
      .calNavGroup {
        display: flex;
        align-items: center;
        gap: 8px;
      }
      .calMonthSelect {
        background: #0f171d;
        border: 1px solid #d79b19;
        color: #f4c84f;
        font-weight: 700;
        font-size: 13px;
        padding: 6px 12px;
        border-radius: 6px;
        cursor: pointer;
        outline: none;
      }
      .calMonthSelect option {
        background: #0b1115;
        color: #e2e8f0;
      }
      .calBtn {
        background: #141c22;
        border: 1px solid #23313a;
        color: #cbd5e1;
        padding: 6px 12px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.15s ease;
      }
      .calBtn:hover {
        background: #1e293b;
        border-color: #d79b19;
        color: #f4c84f;
      }
      .calBtn:disabled {
        opacity: 0.35;
        cursor: not-allowed;
        border-color: #23313a;
        color: #64748b;
      }

      /* Grid de 7 columnas estilo calendario real */
      .calWeekdaysHeader {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 6px;
        margin-top: 14px;
        text-align: center;
      }
      .calWeekdayCol {
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 0.08em;
        color: #8b9bb4;
        padding: 6px 0;
        background: #0c1318;
        border-radius: 4px;
        text-transform: uppercase;
      }
      .calWeekdayCol.weekend {
        color: #64748b;
      }

      .calMonthGrid {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 6px;
        margin-top: 6px;
      }
      .calEmptyCell {
        min-height: 86px;
        background: rgba(13, 19, 24, 0.25);
        border: 1px dashed rgba(35, 46, 53, 0.4);
        border-radius: 8px;
      }
      .calDayCell {
        background: #0d1318;
        border: 1px solid #222d36;
        border-radius: 8px;
        padding: 8px;
        cursor: pointer;
        transition: transform 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease, background 0.15s ease;
        position: relative;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-height: 88px;
      }
      .calDayCell:hover {
        transform: translateY(-2px);
        border-color: #f4c84f;
        box-shadow: 0 4px 14px rgba(0,0,0,0.5);
        z-index: 2;
      }
      .calDayCell.win {
        background: linear-gradient(180deg, #091a13 0%, #0a1216 100%);
        border-color: rgba(0, 219, 121, 0.35);
      }
      .calDayCell.win:hover {
        border-color: #00db79;
        box-shadow: 0 0 14px rgba(0, 219, 121, 0.25);
      }
      .calDayCell.loss {
        background: linear-gradient(180deg, #1d0f11 0%, #0a1216 100%);
        border-color: rgba(255, 69, 58, 0.35);
      }
      .calDayCell.loss:hover {
        border-color: #ff453a;
        box-shadow: 0 0 14px rgba(255, 69, 58, 0.25);
      }
      .calDayCell.neutral {
        background: #0d1318;
        border-color: #2a3842;
      }
      .calDayCell.today {
        border: 2px solid #f4c84f !important;
        box-shadow: 0 0 14px rgba(244, 200, 79, 0.35) !important;
      }
      .calDayCell.selected {
        outline: 2px solid #38bdf8;
        outline-offset: 1px;
      }
      .calDayCell.future {
        opacity: 0.35;
        cursor: not-allowed;
        background: #090e11;
        border-color: #172127;
      }
      .calDayCell.future:hover {
        transform: none;
        box-shadow: none;
        border-color: #172127;
      }

      .calCellTop {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      .calDayNum {
        font-size: 13px;
        font-weight: 800;
        color: #e2e8f0;
      }
      .calDayBadges {
        display: flex;
        gap: 3px;
        align-items: center;
      }
      .calBadge {
        font-size: 8.5px;
        padding: 1px 4px;
        border-radius: 3px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.04em;
      }
      .calBadge.today {
        background: #f4c84f;
        color: #000;
      }
      .calBadge.top {
        background: rgba(0, 219, 121, 0.2);
        color: #00db79;
        border: 1px solid rgba(0, 219, 121, 0.4);
      }
      .calBadge.low {
        background: rgba(255, 69, 58, 0.2);
        color: #ff453a;
        border: 1px solid rgba(255, 69, 58, 0.4);
      }
      .calCellPnl {
        font-size: 14px;
        font-weight: 800;
        margin: 3px 0 1px;
        letter-spacing: -0.01em;
      }
      .calCellRet {
        font-size: 10px;
        font-weight: 700;
        margin-left: 2px;
      }
      .calCellTrades {
        font-size: 10px;
        color: #94a3b8;
        margin-top: 2px;
      }
      .calWinLossMiniBar {
        height: 3px;
        background: #1e293b;
        border-radius: 2px;
        overflow: hidden;
        display: flex;
        margin-top: 4px;
      }
      .calWinLossMiniBar .barW {
        background: #00db79;
        height: 100%;
      }
      .calWinLossMiniBar .barL {
        background: #ff453a;
        height: 100%;
      }

      /* Inspector del Día Permanente */
      .calDayInspector {
        margin-top: 16px;
        padding: 16px;
        border: 1px solid #23313a;
        border-radius: 10px;
        background: #0c1217;
      }
      .inspectorHead {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 10px;
        padding-bottom: 12px;
        border-bottom: 1px solid #1a242c;
      }
      .inspectorTitle {
        font-size: 16px;
        font-weight: 800;
        color: #f4c84f;
      }
      .inspectorSubtitle {
        font-size: 12px;
        color: #94a3b8;
        margin-top: 2px;
      }
      .inspectorKpis {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 10px;
        margin-top: 14px;
      }
      .inspKpiCard {
        background: #111a21;
        border: 1px solid #202d37;
        border-radius: 8px;
        padding: 10px 12px;
      }
      .inspKpiCard .lab {
        font-size: 10.5px;
        color: #8b9bb4;
        text-transform: uppercase;
        font-weight: 700;
      }
      .inspKpiCard .val {
        font-size: 18px;
        font-weight: 800;
        margin-top: 3px;
      }
      .inspKpiCard .sub {
        font-size: 11px;
        color: #94a3b8;
        margin-top: 2px;
      }
      .inspStratsRow {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin-top: 14px;
      }
      .inspStratCard {
        background: #141d24;
        border: 1px solid #23323c;
        border-radius: 6px;
        padding: 8px 12px;
        flex: 1 1 150px;
      }

      @media (max-width: 768px) {
        .calWeekdaysHeader,
        .calMonthGrid {
          gap: 3px;
        }
        .calDayCell {
          min-height: 70px;
          padding: 5px;
        }
        .calCellPnl {
          font-size: 12px;
        }
        .inspectorKpis {
          grid-template-columns: repeat(2, 1fr);
        }
      }

      /* ========================================================
         META DE GANANCIA DIARIA (DAILY PROFIT TARGET)
         ======================================================== */
      .dptCard {
        background: linear-gradient(180deg, #10161a 0%, #0a0e10 100%);
        border: 1px solid #765719;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
      }
      .dptHeader {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
        border-bottom: 1px solid #23313a;
        padding-bottom: 12px;
        margin-bottom: 12px;
      }
      .dptTitle {
        font-size: 14px;
        font-weight: 800;
        color: #f4c84f;
        letter-spacing: 0.04em;
        display: flex;
        align-items: center;
        gap: 8px;
      }
      .dptSub {
        font-size: 11.5px;
        color: #94a3b8;
        margin-top: 3px;
      }
      .dptControlBar {
        display: flex;
        align-items: center;
        gap: 14px;
        flex-wrap: wrap;
        background: #090e12;
        border: 1px solid #1c2730;
        border-radius: 8px;
        padding: 10px 14px;
        margin-top: 10px;
      }
      .dptControlGroup {
        display: flex;
        align-items: center;
        gap: 8px;
      }
      .dptInput {
        background: #141c22;
        border: 1px solid #d79b19;
        color: #f4c84f;
        font-weight: 700;
        font-size: 13px;
        padding: 5px 10px;
        border-radius: 6px;
        width: 75px;
        text-align: right;
        outline: none;
      }
      .dptBtn {
        background: #1a252f;
        border: 1px solid #d79b19;
        color: #f4c84f;
        font-size: 12px;
        font-weight: 700;
        padding: 6px 14px;
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.15s ease;
      }
      .dptBtn:hover {
        background: #d79b19;
        color: #000;
      }
      .dptGrid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 10px;
        margin-top: 12px;
      }
      .dptKpi {
        background: #0d1419;
        border: 1px solid #1c2730;
        border-radius: 8px;
        padding: 10px 12px;
      }
      .dptKpi .lab {
        font-size: 11px;
        color: #8fa2b3;
      }
      .dptKpi .val {
        font-size: 17px;
        font-weight: 800;
        margin-top: 2px;
      }
      .dptKpi .sub {
        font-size: 10.5px;
        color: #64748b;
        margin-top: 2px;
      }
      .dptProgressTrack {
        width: 100%;
        height: 8px;
        background: #151e25;
        border-radius: 4px;
        overflow: hidden;
        margin-top: 6px;
      }
      .dptProgressBar {
        height: 100%;
        width: 0%;
        background: #d79b19;
        transition: width 0.3s ease;
      }
      .dptLockedBanner {
        background: linear-gradient(135deg, rgba(215, 155, 25, 0.18), rgba(245, 189, 54, 0.06));
        border: 1.5px solid #f5bd36;
        border-radius: 10px;
        padding: 14px 18px;
        margin-top: 14px;
        display: none;
      }
      .dptModalOverlay {
        position: fixed;
        inset: 0;
        background: rgba(0,0,0,0.85);
        backdrop-filter: blur(5px);
        display: none;
        align-items: center;
        justify-content: center;
        z-index: 99999;
      }
      .dptModalBox {
        background: #0e151b;
        border: 2px solid #ef6a6a;
        border-radius: 14px;
        max-width: 550px;
        width: 90%;
        padding: 24px;
        box-shadow: 0 10px 40px rgba(239, 106, 106, 0.3);
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
          <h1>Cuenta en vivo · Operaciones y auditorías</h1>
          <div class="muted">
            Métricas en tiempo real, balance de cuenta, historial de operaciones y auditorías técnicas.
          </div>
        </div>
        <div class="nav">
          <a class="btn" href="/">Dashboard</a>
          <a class="btn" href="/performance">Rendimiento</a>
          <a class="btn" href="/instruments">Instrumentos</a>
          <a class="btn" href="/strategy-bases">Bases de Estrategias</a>
        </div>
      </div>
      <section class="grid">
        <div class="c k">
          <div class="lab">Balance</div>
          <div class="val" id="balance">—</div>
        </div>
        <div class="c k">
          <div class="lab">Equity</div>
          <div class="val" id="equity">—</div>
        </div>
        <div class="c k">
          <div class="lab">Margen libre</div>
          <div class="val" id="free">—</div>
        </div>
        <div class="c k">
          <div class="lab">Profit flotante</div>
          <div class="val" id="profit">—</div>
        </div>
        <div class="c half">
          <div class="lab">Actividad</div>
          <div class="stats">
            <div class="s">Trades<b id="total">0</b></div>
            <div class="s">Abiertos<b id="open">0</b></div>
            <div class="s">Cerrados<b id="closed">0</b></div>
            <div class="s">WR piernas<b id="wr">0%</b></div>
            <div class="s">WR setups<b id="swr">0%</b></div>
            <div class="s">PnL neto<b id="pnl">0</b></div>
          </div>
          <div id="stamp" class="muted" style="margin-top: 10px">Sin snapshot.</div>
          <div id="dbsource" class="muted" style="margin-top: 5px; font-size: 11px">
            Última actualización: —
          </div>
          <div id="dbpath" class="muted" style="margin-top: 3px; font-size: 11px; word-break: break-all">SQLite: verificando ruta…</div>
          <div id="statswindow" class="muted" style="margin-top: 3px; font-size: 11px">
            Ventana estadística: historial completo
          </div>
        </div>
        <div class="c half">
          <div class="lab">Cierres</div>
          <div class="bar" id="bar"></div>
          <div class="leg">
            <span>TP1 <b id="tp1">0</b></span
            ><span>TP2 <b id="tp2">0</b></span
            ><span>TP histórico <b id="tph">0</b></span
            ><span>Stop Loss <b id="sl">0</b></span
            ><span>BE/Otro <b id="be">0</b></span
            ><span>Emergencia <b id="em">0</b></span>
          </div>
        </div>
        <div class="c full">
          <div class="lab">Ranking de estrategias</div>
          <div class="muted" style="font-size: 12px; margin-top: 5px">
            Ordenado por PnL neto de setups cerrados. El factor de beneficio se muestra sólo cuando
            hay pérdidas registradas.
          </div>
          <div id="strategyStats" class="ranking"></div>
        </div>

        <!-- META DE GANANCIA DIARIA (DAILY PROFIT TARGET) -->
        <div class="c full dptCard" id="dailyProfitTargetCard">
          <div class="dptHeader">
            <div>
              <div class="dptTitle">🎯 Meta de Ganancia Diaria (Daily Profit Target)</div>
              <div class="dptSub">
                Fija un objetivo diario en % sobre el balance. Al cumplirse, se bloquean todas las nuevas entradas para proteger ganancias. Reactivación automática en la sesión de Asia (00:00 UTC).
              </div>
            </div>
            <div id="dptStatusBadge" class="statusPill good">Cargando...</div>
          </div>

          <div class="dptControlBar">
            <label class="dptControlGroup" style="cursor: pointer; user-select: none;">
              <input type="checkbox" id="dptEnabledCheckbox" style="accent-color: #d79b19; width: 16px; height: 16px;" onchange="saveDailyTargetSettings()" checked />
              <span style="font-weight: 700; font-size: 12.5px;">Habilitar meta diaria de beneficio</span>
            </label>

            <div class="dptControlGroup" style="margin-left: auto;">
              <span style="font-size: 12px; color: #94a3b8;">Meta Diaria:</span>
              <input type="number" id="dptTargetPercentInput" class="dptInput" step="0.1" min="0.1" max="100" value="2.0" onchange="saveDailyTargetSettings()" onkeydown="if(event.key==='Enter'){event.preventDefault();saveDailyTargetSettings();}" />
              <span style="font-weight: 700; color: #f4c84f;">%</span>
              <button type="button" id="dptSaveSettingsBtn" class="dptBtn" onclick="saveDailyTargetSettings()">Guardar Meta</button>
            </div>
          </div>

          <div class="dptGrid">
            <div class="dptKpi">
              <div class="lab">Retorno Diario Cerrado</div>
              <div class="val" id="dptReturnDisplay">+0.00%</div>
              <div class="sub" id="dptTodayPnlDisplay">+$0.00 hoy</div>
            </div>
            <div class="dptKpi">
              <div class="lab">Meta Objetivo</div>
              <div class="val" id="dptTargetDisplay" style="color: #f4c84f;">2.00%</div>
              <div class="sub">Límite diario establecido</div>
            </div>
            <div class="dptKpi">
              <div class="lab">Progreso Hacia la Meta</div>
              <div class="dptProgressTrack"><div class="dptProgressBar" id="dptProgressBar"></div></div>
              <div class="sub" id="dptTradesSummary">0 cerrados hoy</div>
            </div>
            <div class="dptKpi">
              <div class="lab">Próxima Reactivación</div>
              <div class="val" style="font-size: 14px; color: #60a5fa;">Sesión de Asia</div>
              <div class="sub">00:00 UTC / 09:00 Tokio (Automática)</div>
            </div>
          </div>

          <div class="dptLockedBanner" id="dptLockedBanner">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 14px;">
              <div id="dptBannerText" style="flex: 1 1 320px; line-height: 1.5;">
                <b>🎯 ¡META DIARIA CUMPLIDA!</b> Entradas bloqueadas para proteger tus ganancias.
              </div>
              <div>
                <button type="button" id="dptOverrideBtn" onclick="openDptOverrideModal()" style="background: linear-gradient(135deg, #d79b19, #f5bd36); color: #000; font-weight: 800; border: none; padding: 10px 18px; border-radius: 8px; cursor: pointer; box-shadow: 0 2px 10px rgba(215, 155, 25, 0.4); font-size: 12.5px;">
                  🚀 ¿Deseas ganar un poquito más?
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- MODAL DE ADVERTENCIA DE RIESGO DE OVERTRADING -->
        <div class="dptModalOverlay" id="dptRiskModal">
          <div class="dptModalBox">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 14px;">
              <span style="font-size: 24px;">⚠️</span>
              <b style="font-size: 16px; color: #ff6b6b; letter-spacing: 0.03em;">ADVERTENCIA DE RIESGO: PELIGRO DE OVERTRADING</b>
            </div>
            <p style="font-size: 13px; line-height: 1.55; color: #e2e8f0; margin-bottom: 12px;">
              ¡Felicidades! Has cumplido la meta de rentabilidad diaria prevista en tu plan de trading.
            </p>
            <div style="background: rgba(255, 69, 58, 0.12); border-left: 3px solid #ff453a; padding: 10px 14px; border-radius: 6px; font-size: 12px; line-height: 1.5; color: #fca5a5; margin-bottom: 16px;">
              <b>ALERTA DE DISCIPLINA:</b> Continuar operando desafía las reglas de gestión de riesgo y expone tus ganancias a reversiones inesperadas del mercado, incremento de spreads y deslizamientos. <b>Corres el riesgo real de perder parte o la totalidad de los beneficios acumulados en la sesión.</b>
            </div>
            <p style="font-size: 12.5px; color: #cbd5e1; margin-bottom: 20px;">
              ¿Deseas desbloquear temporalmente el escaneo de nuevas entradas para buscar un objetivo adicional (+1.0% de margen) asumiendo este riesgo?
            </p>
            <div style="display: flex; justify-content: flex-end; gap: 10px; flex-wrap: wrap;">
              <button type="button" onclick="closeDptOverrideModal()" style="background: #1e293b; border: 1px solid #475569; color: #f1f5f9; padding: 8px 16px; border-radius: 6px; font-size: 12px; font-weight: 700; cursor: pointer;">
                🛡️ Mantener Ganancias Protegidas (Recomendado)
              </button>
              <button type="button" id="dptConfirmOverrideBtn" onclick="confirmDptOverride()" style="background: #dc2626; border: 1px solid #ef4444; color: #fff; padding: 8px 16px; border-radius: 6px; font-size: 12px; font-weight: 800; cursor: pointer;">
                ⚠️ Asumo el Riesgo, Desbloquear (+1.0%)
              </button>
            </div>
          </div>
        </div>

        <!-- RENDIMIENTO DIARIO DEL MES (CALENDARIO Y COMPORTAMIENTO DE ESTRATEGIAS) -->
        <div class="c full" id="monthlyDailyPerformanceSection">
          <div class="calHeaderBar">
            <div>
              <div class="lab" style="color: #f4c84f; font-size: 13.5px; font-weight: 800; letter-spacing: 0.05em">
                🗓️ Calendario de Rendimiento Diario y Estrategias
              </div>
              <div class="muted" style="font-size: 11.5px; margin-top: 3px">
                Auditoría estilo calendario día a día. Selecciona cualquier día del mes para inspeccionar trades tomados, rentabilidad %, porcentaje de acierto/pérdida y el historial detallado de operaciones.
              </div>
            </div>
            <div class="calNavGroup">
              <button type="button" class="calBtn" id="calPrevMonthBtn" onclick="navigateMonth(1)" title="Ver mes anterior">◀ Mes anterior</button>
              <select id="calMonthSelect" class="calMonthSelect" onchange="onCalMonthSelectChange(this.value)"></select>
              <button type="button" class="calBtn" id="calNextMonthBtn" onclick="navigateMonth(-1)" title="Ver mes siguiente">Mes siguiente ▶</button>
              <button type="button" class="calBtn" id="calTodayBtn" onclick="goToToday()" style="border-color:#f4c84f; color:#f4c84f">📅 Ir a Hoy</button>
            </div>
          </div>

          <!-- HIGHLIGHT KPIS (MEJOR DÍA, PEOR DÍA, BALANCE DÍAS, PNL TOTAL) -->
          <div class="stats" style="grid-template-columns: repeat(4, 1fr); margin-top: 14px">
            <div class="s" style="border-left: 3px solid #00db79; background: #0b1610">
              <span class="lab" style="color: #00db79; font-size: 10px">🏆 Mejor Día (Mayor Ganancia)</span>
              <b id="calBestDayPnl" style="color: #00db79; font-size: 18px">—</b>
              <div class="muted" style="font-size: 11px; margin-top: 2px" id="calBestDaySub">—</div>
            </div>
            <div class="s" style="border-left: 3px solid #ff453a; background: #160c0d">
              <span class="lab" style="color: #ff453a; font-size: 10px">⚠️ Día Más Adverso (Mayor Pérdida)</span>
              <b id="calWorstDayPnl" style="color: #ff453a; font-size: 18px">—</b>
              <div class="muted" style="font-size: 11px; margin-top: 2px" id="calWorstDaySub">—</div>
            </div>
            <div class="s" style="border-left: 3px solid #f5bd36; background: #15130b">
              <span class="lab" style="color: #f5bd36; font-size: 10px">📊 Días Ganadores vs Perdedores</span>
              <b id="calDaysRatio" style="color: #f5bd36; font-size: 18px">—</b>
              <div class="muted" style="font-size: 11px; margin-top: 2px" id="calDaysWinrate">—</div>
            </div>
            <div class="s" style="border-left: 3px solid #d79b19; background: #12181d">
              <span class="lab" style="color: #d79b19; font-size: 10px">💰 PnL y Rentabilidad Mensual</span>
              <b id="calTotalPnl" style="font-size: 18px">—</b>
              <div class="muted" style="font-size: 11px; margin-top: 2px" id="calDaysElapsed">—</div>
            </div>
          </div>

          <!-- CALENDARIO DE 7 COLUMNAS -->
          <div style="margin-top: 16px">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px">
              <span class="lab" id="calCalendarGridTitle">Calendario Mensual</span>
              <span class="muted" style="font-size: 11px">Haz clic en cualquier día para cargar instantáneamente su inspector</span>
            </div>
            <div class="calWeekdaysHeader">
              <div class="calWeekdayCol">LUN</div>
              <div class="calWeekdayCol">MAR</div>
              <div class="calWeekdayCol">MIÉ</div>
              <div class="calWeekdayCol">JUE</div>
              <div class="calWeekdayCol">VIE</div>
              <div class="calWeekdayCol weekend">SÁB</div>
              <div class="calWeekdayCol weekend">DOM</div>
            </div>
            <div class="calMonthGrid" id="calDaysGrid"></div>
          </div>

          <!-- INSPECTOR PERMANENTE DEL DÍA SELECCIONADO (AL MOMENTO Y SIEMPRE SE MUESTRA EL DÍA ACTUAL) -->
          <div class="calDayInspector" id="calDayInspector">
            <div class="inspectorHead">
              <div>
                <div style="display: flex; align-items: center; gap: 8px">
                  <span class="inspectorTitle" id="inspDayTitle">Día Actual</span>
                  <span class="pill" id="inspDayBadge" style="font-size: 10px">HOY</span>
                </div>
                <div class="inspectorSubtitle" id="inspDaySubtitle">Detalle de operaciones y rentabilidad del día</div>
              </div>
              <div id="inspDayStatusPill" class="pill" style="font-size: 11px">—</div>
            </div>

            <!-- 4 KPIS ESPECÍFICOS DEL DÍA PEDIDOS POR EL USUARIO -->
            <div class="inspectorKpis">
              <div class="inspKpiCard" style="border-left: 3px solid #f4c84f">
                <div class="lab">Rentabilidad y PnL</div>
                <div class="val" id="inspDayPnl">—</div>
                <div class="sub" id="inspDayReturnPct">—</div>
              </div>
              <div class="inspKpiCard" style="border-left: 3px solid #38bdf8">
                <div class="lab">Trades Tomados</div>
                <div class="val" id="inspDayTradesCount">0</div>
                <div class="sub" id="inspDayTradesSub">Operaciones cerradas</div>
              </div>
              <div class="inspKpiCard" style="border-left: 3px solid #00db79">
                <div class="lab">Trades Positivos</div>
                <div class="val" id="inspDayPosPct" style="color: #00db79">—</div>
                <div class="sub" id="inspDayPosCount">0 ganadas</div>
              </div>
              <div class="inspKpiCard" style="border-left: 3px solid #ff453a">
                <div class="lab">Trades Negativos / BE</div>
                <div class="val" id="inspDayNegPct" style="color: #ff453a">—</div>
                <div class="sub" id="inspDayNegCount">0 pérdidas · 0 BE</div>
              </div>
            </div>

            <!-- DESGLOSE DE ESTRATEGIAS DEL DÍA -->
            <div style="margin-top: 14px">
              <div class="lab" style="font-size: 11px">Estrategias Activas en el Día</div>
              <div class="inspStratsRow" id="inspDayStrategies"></div>
            </div>

            <!-- HISTORIAL DE OPERACIONES DEL DÍA CON AUDITORÍA INTEGRADA Y DESCARGA POR LOTE -->
            <div style="margin-top: 18px">
              <div class="historyHead" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; flex-wrap: wrap; gap: 10px">
                <div>
                  <div class="lab" style="font-size: 12.5px; color: #f4c84f">Historial de Operaciones del Día · Auditoría Técnica Completa</div>
                  <div class="muted" style="font-size: 11px; margin-top: 2px">
                    Cada auditoría muestra su resumen directamente; abre la vista completa para revisar toda la evidencia técnica.
                    <!-- Confirmaciones persistentes · Detalle técnico persistido · snapshots persistentes · Historial Entrada vs. Ahora · Conflicto chartista: -->
                  </div>
                </div>
                <div style="display: flex; align-items: center; gap: 10px">
                  <span class="muted" style="font-size: 11px" id="inspDayOpsCount">—</span>
                  <button id="bulkDownloadBtn" class="btn" disabled onclick="downloadSelectedAudits()">
                    Descargar seleccionados (.xlsx)
                  </button>
                </div>
              </div>
              <div class="tbl" style="max-height: 1100px" id="inspDayOperationsTable"></div>
            </div>
          </div>

          <!-- TABLA RESUMEN DE ESTRATEGIAS EN EL MES -->
          <div style="margin-top: 18px">
            <div class="lab" style="margin-bottom: 8px">Comportamiento Mensual Global por Estrategia</div>
            <div id="calStrategyTable"></div>
          </div>
        </div>
        <div class="c full">
          <div class="historyHead">
            <div>
              <div class="lab">Comparativa Pre/Post mejoras (v107)</div>
              <div class="muted" style="font-size: 12px; margin-top: 4px">
                Win Rate por señal antes vs. después de las mejoras aplicadas (v106: Break-Even con
                bloqueo real, filtro de horas de bajo edge en Sintéticos, salida por invalidación
                estructural M15; v107: retest limpio validado con overshoot real, patrón chartista y
                FVG obligatorios, sin killzones/filtro horario forzado, niveles de cuarto en
                Gold/ORB solo XAUUSD).
              </div>
            </div>
          </div>
          <div class="stats" style="grid-template-columns: repeat(3, 1fr)">
            <div class="s">
              WR Pre<b id="ppPreWr">—</b>
              <div class="muted" style="font-size: 10px; margin-top: 2px" id="ppPreN">n=0</div>
            </div>
            <div class="s">
              WR Post<b id="ppPostWr">—</b>
              <div class="muted" style="font-size: 10px; margin-top: 2px" id="ppPostN">n=0</div>
            </div>
            <div class="s">Delta<b id="ppDelta">—</b></div>
          </div>
          <div id="ppNotice" class="muted" style="margin-top: 10px; font-size: 12px"></div>
          <div id="ppByFamily" class="ranking" style="margin-top: 10px"></div>
        </div>
        <div class="c full">
          <div class="historyHead">
            <div>
              <div class="lab">Meta-etiquetado con IA</div>
              <div class="muted" style="font-size: 12px; margin-top: 4px">
                Señales puntuadas por el motor de IA antes de ejecutarse. En modo sombra la IA
                observa y aprende sin bloquear ninguna entrada.
              </div>
            </div>
            <div id="aiMode" class="pill">—</div>
          </div>
          <div class="stats" style="grid-template-columns: repeat(5, 1fr)">
            <div class="s">Analizadas por IA<b id="aiTotal">0</b></div>
            <div class="s">En sombra<b id="aiShadow">0</b></div>
            <div class="s">Filtradas (rechazadas)<b id="aiRejected">0</b></div>
            <div class="s">Prob. media<b id="aiProb">—</b></div>
            <div class="s">Expectativa neta<b id="aiExp">—</b></div>
          </div>
          <div id="aiState" class="muted" style="margin-top: 10px; font-size: 12px"></div>
          <div style="display: grid; grid-template-columns: 1fr 1.25fr; gap: 14px; margin-top: 12px">
            <div>
              <div class="lab">Mejoras aplicadas para futuras entradas</div>
              <div id="aiImprovements" class="ranking" style="grid-template-columns: 1fr"></div>
            </div>
            <div>
              <div style="display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:8px">
                <div class="lab">Catálogo de Modelos de IA y Cobertura</div>
                <span id="aiModelsCount" style="font-size:11px;color:#94a3b8">Cargando modelos…</span>
              </div>
              <div style="margin:8px 0 6px 0">
                <input type="text" id="aiWorkerSearch" placeholder="🔍 Filtrar modelos (ej: Boom, Crash, Forex, Gold, Vol, Step)..." style="width:100%;box-sizing:border-box;padding:7px 10px;font-size:12px;background:#0d1317;border:1px solid #263139;border-radius:6px;color:#f5f5f2;margin-bottom:6px" oninput="filterAIWorkers()" />
                <div style="display:flex;gap:6px;flex-wrap:wrap">
                  <button type="button" class="ai-filter-pill active" onclick="setAIFilter('all', this)" style="background:#162026;border:1px solid #d79b19;color:#fff;padding:3px 10px;border-radius:12px;font-size:11px;cursor:pointer">Todos (<span id="aiFilterCountAll">0</span>)</button>
                  <button type="button" class="ai-filter-pill" onclick="setAIFilter('active', this)" style="background:#162026;border:1px solid #2b3942;color:#d1d5db;padding:3px 10px;border-radius:12px;font-size:11px;cursor:pointer">Con señales en vivo</button>
                  <button type="button" class="ai-filter-pill" onclick="setAIFilter('synthetics', this)" style="background:#162026;border:1px solid #2b3942;color:#d1d5db;padding:3px 10px;border-radius:12px;font-size:11px;cursor:pointer">Sintéticos</button>
                  <button type="button" class="ai-filter-pill" onclick="setAIFilter('forex_gold', this)" style="background:#162026;border:1px solid #2b3942;color:#d1d5db;padding:3px 10px;border-radius:12px;font-size:11px;cursor:pointer">Forex / Oro</button>
                  <button type="button" class="ai-filter-pill" onclick="setAIFilter('indices', this)" style="background:#162026;border:1px solid #2b3942;color:#d1d5db;padding:3px 10px;border-radius:12px;font-size:11px;cursor:pointer">Índices / Global</button>
                </div>
              </div>
              <div id="aiWorkers" class="ranking" style="grid-template-columns: 1fr; max-height: 580px; overflow-y: auto; padding-right: 4px;"></div>
            </div>
          </div>
        </div>

      </section>
    </main>
    <script>
      const $ = (x) => document.getElementById(x),
        money = (v) =>
          v == null
            ? '—'
            : Number(v).toLocaleString('es-CL', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              }),
        num = (v, d = 2) => (v == null ? '—' : Number(v).toFixed(d)),
        e = (v) =>
          String(v ?? '—').replace(
            /[&<>"']/g,
            (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c],
          );
      function auditHtml(q) {
        const passed = q.passed_confirmations || [],
          missing = q.missing_confirmations || [],
          critical = q.critical_confirmation_failures || [],
          total = q.entry_vs_now_snapshot_count || 0,
          id = q.source_trade_id || q.trade_id || q.id,
          score = q.confirmation_score == null ? '—' : num(q.confirmation_score, 0);
        let pattern = q.chart_pattern_confirmed
          ? '<div class="auditPattern">Patrón confirmado · <b>' +
            e(String(q.chart_pattern_name || 'confirmado').replaceAll('_', ' ')) +
            '</b></div>'
          : '';
        let link = id
          ? '<a class="btn auditOpen" target="_blank" rel="noopener" href="/account/trade/' +
            e(id) +
            '/audit" title="Abrir auditoría visual completa">Ver auditoría completa ↗</a>'
          : '';
        return (
          '<div class="auditCard"><div class="auditDecision">' +
          e(q.confirmation_decision || 'Sin auditoría persistida') +
          '</div><div class="auditMeta"><span class="auditStat">Score <b>' +
          score +
          '</b></span><span class="auditStat">Snapshots <b>' +
          e(total) +
          '</b></span><span class="auditStat good">Aprobadas <b>' +
          e(passed.length) +
          '</b></span><span class="auditStat warn">Faltantes <b>' +
          e(missing.length) +
          '</b></span><span class="auditStat bad">Críticas <b>' +
          e(critical.length) +
          '</b></span></div>' +
          pattern +
          link +
          '</div>'
        );
      }
      function strategyHtml(q, index) {
        const pnl = Number(q.net_pnl || 0),
          pf = q.profit_factor == null ? '—' : num(q.profit_factor, 2),
          cls = pnl > 0 ? 'good' : pnl < 0 ? 'bad' : '';
        return (
          '<article class="strategy"><div class="strategyHead"><span>#' +
          (index + 1) +
          ' · ' +
          e(q.strategy) +
          '</span><span class="profit ' +
          cls +
          '">' +
          money(pnl) +
          '</span></div><div class="strategyMeta"><span>' +
          e(q.setups || 0) +
          ' setups</span><span>WR ' +
          num(q.win_rate, 1) +
          '%</span><span>PF ' +
          pf +
          '</span><span>Prom. ' +
          money(q.average_pnl) +
          '</span></div></article>'
        );
      }
      function familyHtml(f) {
        const wr = f.win_rate == null ? '—' : num(f.win_rate, 1) + '%';
        return (
          '<article class="strategy"><div class="strategyHead"><span>' +
          e(f.family) +
          '</span><span>' +
          wr +
          '</span></div><div class="strategyMeta"><span>n=' +
          e(f.decisive || 0) +
          '</span></div></article>'
        );
      }
      function renderPrePost(pp) {
        pp = pp || {};
        const pre = pp.pre || {},
          post = pp.post || {};
        const preWr = pre.win_rate,
          postWr = post.win_rate;
        $('ppPreWr').textContent = preWr == null ? '—' : num(preWr, 1) + '%';
        $('ppPreN').textContent =
          'n=' + (pre.decisive || 0) + ' (' + (pre.signal_count || 0) + ' señales)';
        $('ppPostWr').textContent = postWr == null ? '—' : num(postWr, 1) + '%';
        $('ppPostN').textContent =
          'n=' + (post.decisive || 0) + ' (' + (post.signal_count || 0) + ' señales)';
        const delta = pp.delta_win_rate_pp;
        if (delta == null) {
          $('ppDelta').textContent = '—';
          $('ppDelta').className = 'val';
        } else {
          $('ppDelta').textContent = (delta >= 0 ? '+' : '') + num(delta, 1) + ' pp';
          $('ppDelta').className = 'val ' + (delta > 0 ? 'good' : delta < 0 ? 'bad' : '');
        }
        let notice = '';
        if (!post.decisive) {
          notice =
            'Aún no hay operaciones POST-mejoras cerradas; esta comparación se activa apenas se acumulen nuevas señales con la versión v107+.';
        } else if (pp.post_sample_small) {
          notice =
            'Muestra POST todavía pequeña (n=' +
            post.decisive +
            '). Con menos de ~20-30 señales decisivas el WR puede variar mucho por azar.';
        }
        $('ppNotice').textContent = notice;
        const families = (post.decisive ? post.by_family : pre.by_family) || [];
        $('ppByFamily').innerHTML = families.map(familyHtml).join('') || '';
      }
      let aiWorkersList = [];
      let aiActiveFilter = 'all';
      let aiSearchQuery = '';

      function filterAIWorkers() {
        const input = $('aiWorkerSearch');
        aiSearchQuery = input ? input.value.trim().toLowerCase() : '';
        renderAIWorkersFiltered();
      }

      function setAIFilter(filterName, btn) {
        aiActiveFilter = filterName;
        document.querySelectorAll('.ai-filter-pill').forEach((b) => {
          b.style.borderColor = '#2b3942';
          b.style.color = '#d1d5db';
        });
        if (btn) {
          btn.style.borderColor = '#d79b19';
          btn.style.color = '#fff';
        }
        renderAIWorkersFiltered();
      }

      function renderAIWorkersFiltered() {
        const host = $('aiWorkers');
        if (!host) return;
        const filtered = (aiWorkersList || []).filter((w) => {
          const text = (
            (w.worker || '') + ' ' + (w.model_strategy || '') + ' ' + (w.family || '')
          ).toLowerCase();
          if (aiSearchQuery && !text.includes(aiSearchQuery)) return false;
          if (aiActiveFilter === 'active') return Number(w.analyzed || 0) > 0;
          if (aiActiveFilter === 'synthetics') {
            return ['SINTETICOS', 'BOOM', 'CRASH', 'VOLATILITY', 'STEP', 'JUMP', 'FLIP', 'SYNTHETICS'].some(
              (k) => (w.family || '').toUpperCase().includes(k) || (w.worker || '').toUpperCase().includes(k)
            );
          }
          if (aiActiveFilter === 'forex_gold') {
            return ['FOREX', 'GOLD', 'COMMODITIES'].some(
              (k) => (w.family || '').toUpperCase().includes(k) || (w.worker || '').toUpperCase().includes(k)
            );
          }
          if (aiActiveFilter === 'indices') {
            return ['INDICES', 'ORB', 'GLOBAL'].some(
              (k) => (w.family || '').toUpperCase().includes(k) || (w.worker || '').toUpperCase().includes(k)
            );
          }
          return true;
        });

        if (!filtered.length) {
          host.innerHTML = '<div class="empty">No se encontraron modelos con los filtros seleccionados.</div>';
          return;
        }
        host.innerHTML = filtered.map(aiWorkerHtml).join('');
      }

      function aiWorkerHtml(w) {
        const rej = Number(w.rejected || 0),
          analyzed = Number(w.analyzed || 0),
          trained = Boolean(w.trained),
          cls = trained ? 'good' : 'warn';

        let badgeText = '';
        if (analyzed > 0) {
          badgeText = '⚡ MODELO USADO EN EVALUACIONES (' + analyzed + ')';
        } else if (trained) {
          badgeText = '🟢 MODELO ENTRENADO Y ACTIVO';
        } else {
          badgeText = 'SIN MODELO EN EVALUACIONES';
        }

        const strat = w.model_strategy ? ' · ' + e(w.model_strategy) : '';
        const fam = w.family ? ' <small style="color:#94a3b8;font-weight:normal">[' + e(w.family) + ']</small>' : '';

        let modelStatsHtml = '';
        if (w.model_samples) {
          const wrStr = w.model_positive_rate ? (w.model_positive_rate * 100).toFixed(1) + '% acierto base' : '';
          const rrStr = (w.model_win_rr && w.model_loss_rr) ? ' · R: +' + num(w.model_win_rr, 2) + 'R / -' + num(w.model_loss_rr, 2) + 'R' : '';
          modelStatsHtml = '<div class="strategyMeta" style="color:#73e2bd;font-size:11px"><span>📦 ' +
            Number(w.model_samples).toLocaleString('es-CL') + ' muestras entrenadas</span><span>' +
            wrStr + rrStr + '</span><span>Isotónico calibrado</span></div>';
        }

        let liveActivityHtml = '';
        if (analyzed > 0) {
          liveActivityHtml = '<div class="strategyMeta"><span>' +
            analyzed + ' evaluaciones de señales</span><span>En sombra ' +
            e(w.shadow || 0) + '</span><span>Permitidas ' +
            e(w.allowed || 0) + '</span><span class="' + (rej ? 'bad' : '') + '">Rechazadas ' + rej + '</span></div>';
        } else {
          liveActivityHtml = '<div class="strategyMeta" style="color:#94a3b8"><span>0 evaluaciones en sesión (en espera de setup según condiciones de mercado)</span></div>';
        }

        const learningEntries = Object.entries(w.learning_strategies || {});
        let learningHtml = '';
        if (learningEntries.length) {
          learningHtml = '<div class="strategyMeta">' +
            learningEntries.map(([k, v]) =>
              e(k) + ': ' + e(v.eligible_closed_setups || 0) + ' setups cerrados elegibles / ' +
              e(v.minimum || 30) + ' · Candidato ' + (v.trained ? 'entrenado' : 'pendiente')
            ).join('<br>') + '</div>';
        } else if (trained) {
          learningHtml = '<div class="strategyMeta" style="color:#94a3b8">Modelo entrenado con histórico unificado y disponible en storage/ai_models</div>';
        } else {
          learningHtml = '<div class="strategyMeta">Sin setups con captura válida en el último informe</div>';
        }

        const dateStr = w.model_trained_at || w.learning_audit_updated_at;
        const formattedDate = dateStr ? new Date(dateStr).toLocaleString('es-CL') : 'sin informe';

        return (
          '<article class="strategy"><div class="strategyHead"><span>' +
          e(w.worker) + strat + fam +
          '</span><span class="' + cls + '" style="font-size:11px">' +
          badgeText +
          '</span></div>' +
          modelStatsHtml +
          liveActivityHtml +
          learningHtml +
          '<div class="strategyMeta">Actualizado / entrenado: ' +
          e(formattedDate) +
          ' · Las evaluaciones en sombra no son trades cerrados.</div></article>'
        );
      }
      function aiImprovementHtml(it) {
        return (
          '<article class="strategy"><div class="strategyHead"><span>' +
          e(it.title) +
          '</span><span class="' +
          e(it.cls || '') +
          '" style="font-size:11px">' +
          e(it.badge) +
          '</span></div><div class="strategyMeta" style="display:block;line-height:1.5">' +
          e(it.detail) +
          '</div></article>'
        );
      }
      function aiImprovements(m) {
        const out = [],
          total = Number(m.analyzed_total || 0),
          trained = Number(m.trained_decisions || 0),
          rejected = Number(m.filter_rejected || 0),
          reasons = m.rejection_reasons || [];
        if (rejected > 0) {
          out.push({
            title: 'Entradas evitadas por el filtro',
            badge: rejected + ' bloqueadas',
            cls: 'good',
            detail:
              'La IA rechazó ' +
              rejected +
              ' señales que las estrategias habrían ejecutado. Motivo principal: ' +
              e((reasons[0] || {}).reason || '—') +
              '.',
          });
        }
        if (trained > 0) {
          out.push({
            title: 'Probabilidad calibrada en uso',
            badge: 'activa',
            cls: 'good',
            detail:
              'Cada señal recibe una probabilidad de acierto calibrada y una expectativa neta en R, calculadas con el historial propio del worker.',
          });
        }
        (reasons || []).slice(0, 3).forEach((r) =>
          out.push({
            title: 'Patrón de rechazo detectado',
            badge: r.count + '×',
            cls: 'warn',
            detail:
              'La IA descartó señales por "' +
              e(r.reason) +
              '". Revisa si la estrategia origen debería filtrar esa condición antes.',
          }),
        );
        if (!out.length) {
          out.push({
            title: 'Aún no hay mejoras aplicadas',
            badge: 'aprendiendo',
            cls: 'warn',
            detail: total
              ? 'La IA lleva ' +
                total +
                ' señales observadas en modo sombra. Todavía no bloquea ni prioriza entradas: primero necesita historial suficiente para entrenar un modelo fiable por worker.'
              : 'La IA aún no ha puntuado señales. El panel se poblará cuando los workers evalúen nuevas entradas.',
          });
        }
        return out;
      }
      function renderAI(m) {
        m = m || {};
        const total = Number(m.analyzed_total || 0),
          trained = Number(m.trained_decisions || 0);
        $('aiTotal').textContent = total;
        $('aiShadow').textContent = m.shadow_scored || 0;
        $('aiRejected').textContent = m.filter_rejected || 0;
        $('aiProb').textContent =
          m.average_probability == null ? '—' : num(m.average_probability * 100, 1) + '%';
        $('aiExp').textContent =
          m.average_net_expectancy_r == null ? '—' : num(m.average_net_expectancy_r, 2) + 'R';
        const mode = $('aiMode');
        if (m.error) {
          mode.textContent = 'ERROR';
          mode.className = 'pill bad';
        } else if (trained > 0) {
          mode.textContent = 'MODELO ACTIVO';
          mode.className = 'pill good';
        } else if (total > 0) {
          mode.textContent = 'MODO SOMBRA';
          mode.className = 'pill warn';
        } else {
          mode.textContent = 'SIN DATOS';
          mode.className = 'pill';
        }
        let state;
        if (m.error) {
          state = 'No fue posible leer las decisiones de IA: ' + e(m.error);
        } else if (!total) {
          state =
            'Ningún worker ha puntuado señales todavía. La IA no interfiere con la operativa.';
        } else if (!trained) {
          state =
            'Las ' +
            total +
            ' señales se puntuaron sin modelo entrenado, por lo que la IA no bloqueó ninguna entrada. Ejecuta el entrenamiento cuando cada worker acumule historial cerrado suficiente.';
        } else {
          state =
            trained +
            ' de ' +
            total +
            ' decisiones usaron un modelo entrenado' +
            (m.last_trained_at
              ? ' · último entrenamiento ' + new Date(m.last_trained_at).toLocaleString('es-CL')
              : '') +
            '.';
        }
        $('aiState').textContent = state;
        $('aiImprovements').innerHTML = aiImprovements(m).map(aiImprovementHtml).join('');
        aiWorkersList = m.by_worker || [];
        if ($('aiFilterCountAll')) {
          $('aiFilterCountAll').textContent = aiWorkersList.length;
        }
        if ($('aiModelsCount')) {
          const totalModels = m.models_count || (m.models_catalog || []).length || aiWorkersList.length;
          const activeCount = aiWorkersList.filter((w) => Number(w.analyzed || 0) > 0).length;
          $('aiModelsCount').textContent =
            totalModels + ' modelos de IA entrenados · ' + activeCount + ' con señales en sesión activa';
        }
        renderAIWorkersFiltered();
      }
      let currentMdpPayload = null;
      let activeMonthKey = null;
      let activeDayNum = null;

      function onCalMonthSelectChange(monthKey) {
        if (!currentMdpPayload || !currentMdpPayload.all_months) return;
        selectMonthKey(monthKey, false);
      }

      function navigateMonth(direction) {
        if (!currentMdpPayload || !currentMdpPayload.available_months) return;
        const months = currentMdpPayload.available_months;
        const idx = months.findIndex((m) => m.key === activeMonthKey);
        if (idx === -1) return;
        const targetIdx = idx + direction;
        if (targetIdx >= 0 && targetIdx < months.length) {
          selectMonthKey(months[targetIdx].key, false);
        }
      }

      function goToToday() {
        if (!currentMdpPayload) return;
        const months = currentMdpPayload.available_months || [];
        const todayMonth = months.find((m) => m.is_current) || months[0];
        if (todayMonth) {
          selectMonthKey(todayMonth.key, true);
        }
      }

      function selectMonthKey(monthKey, forceSelectToday) {
        if (!currentMdpPayload) return;
        activeMonthKey = monthKey;
        const monthData = (currentMdpPayload.all_months && currentMdpPayload.all_months[monthKey])
          ? currentMdpPayload.all_months[monthKey]
          : currentMdpPayload;

        const sel = $('calMonthSelect');
        if (sel) sel.value = monthKey;

        // Actualizar estado de botones prev/next
        const months = currentMdpPayload.available_months || [];
        const idx = months.findIndex((m) => m.key === activeMonthKey);
        if ($('calPrevMonthBtn')) $('calPrevMonthBtn').disabled = (idx >= months.length - 1);
        if ($('calNextMonthBtn')) $('calNextMonthBtn').disabled = (idx <= 0);

        // Determinar qué día seleccionar
        if (forceSelectToday || monthData.today_day) {
          activeDayNum = monthData.today_day || (new Date()).getDate();
        } else {
          // Mes anterior: seleccionar el día con mejor PnL o el último día con trades
          if (monthData.best_day) {
            activeDayNum = monthData.best_day.day;
          } else if (monthData.days && monthData.days.length) {
            const activeDays = monthData.days.filter((x) => x.has_trades);
            activeDayNum = activeDays.length ? activeDays[activeDays.length - 1].day : monthData.days[0].day;
          } else {
            activeDayNum = 1;
          }
        }

        renderMonthCalendar(monthData);
        selectCalDay(activeDayNum);
      }

      function renderMonthlyDailyPerformance(mdp) {
        if (!mdp || (!mdp.days && !mdp.calendar_days)) {
          if ($('calDaysGrid')) $('calDaysGrid').innerHTML = '<div class="empty">Sin datos de días transcurridos.</div>';
          return;
        }
        currentMdpPayload = mdp;

        // Poblar selector de meses si está disponible
        const sel = $('calMonthSelect');
        if (sel && mdp.available_months) {
          const currentOptions = Array.from(sel.options).map((o) => o.value).join(',');
          const newOptions = mdp.available_months.map((m) => m.key).join(',');
          if (currentOptions !== newOptions) {
            sel.innerHTML = mdp.available_months.map((m) =>
              '<option value="' + m.key + '">' + e(m.label) + (m.is_current ? ' (Actual)' : '') + '</option>'
            ).join('');
          }
        }

        // Si no hay mes activo seleccionado, fijar el del payload
        if (!activeMonthKey || !mdp.all_months || !mdp.all_months[activeMonthKey]) {
          activeMonthKey = mdp.month_key || (mdp.year + '-' + (mdp.month < 10 ? '0' : '') + mdp.month);
        }

        const monthData = (mdp.all_months && mdp.all_months[activeMonthKey]) ? mdp.all_months[activeMonthKey] : mdp;

        // Mantener el día seleccionado o inicializar con hoy
        if (!activeDayNum) {
          activeDayNum = monthData.today_day || (new Date()).getDate();
        }

        const months = mdp.available_months || [];
        const idx = months.findIndex((m) => m.key === activeMonthKey);
        if ($('calPrevMonthBtn')) $('calPrevMonthBtn').disabled = (idx >= months.length - 1);
        if ($('calNextMonthBtn')) $('calNextMonthBtn').disabled = (idx <= 0);
        if (sel) sel.value = activeMonthKey;

        renderMonthCalendar(monthData);
        selectCalDay(activeDayNum);
      }

      function renderMonthCalendar(monthData) {
        if (!monthData) return;

        // 1. Título y KPIs globales del mes
        if ($('calCalendarGridTitle')) {
          $('calCalendarGridTitle').textContent = 'Calendario de ' + (monthData.month_name || '') + ' ' + (monthData.year || '');
        }

        if (monthData.best_day) {
          $('calBestDayPnl').textContent = '+' + money(monthData.best_day.net_pnl);
          $('calBestDaySub').textContent = 'Día ' + monthData.best_day.day + ' (' + monthData.best_day.weekday + ') · Líder: ' + e(monthData.best_day.top_strategy);
        } else {
          $('calBestDayPnl').textContent = '—';
          $('calBestDaySub').textContent = 'Sin días con ganancia aún';
        }

        if (monthData.worst_day) {
          $('calWorstDayPnl').textContent = money(monthData.worst_day.net_pnl);
          $('calWorstDaySub').textContent = 'Día ' + monthData.worst_day.day + ' (' + monthData.worst_day.weekday + ') · Mayor drawdown: ' + e(monthData.worst_day.worst_strategy || '—');
        } else {
          $('calWorstDayPnl').textContent = '—';
          $('calWorstDaySub').textContent = 'Sin días en pérdida registrados';
        }

        $('calDaysRatio').textContent = (monthData.winning_days_count || 0) + ' Verdes / ' + (monthData.losing_days_count || 0) + ' Rojos';
        $('calDaysWinrate').textContent = (monthData.daily_winrate || 0).toFixed(1) + '% días ganadores · ' + (monthData.neutral_days_count || 0) + ' neutros';

        const totalPnl = Number(monthData.total_month_pnl || 0);
        const retPct = Number(monthData.total_month_return_pct || 0);
        $('calTotalPnl').textContent = (totalPnl >= 0 ? '+' : '') + money(totalPnl) + ' (' + (retPct >= 0 ? '+' : '') + num(retPct, 2) + '%)';
        $('calTotalPnl').className = 'val ' + (totalPnl > 0 ? 'good' : (totalPnl < 0 ? 'bad' : ''));
        $('calDaysElapsed').textContent = (monthData.days_elapsed || 0) + ' de ' + (monthData.total_days_in_month || 30) + ' días transcurridos';

        // 2. Grid de 7 columnas estilo calendario real
        const grid = $('calDaysGrid');
        if (grid) {
          const cells = [];
          // Preceder con celdas vacías según first_weekday_idx (0=Lun..6=Dom)
          const offset = monthData.first_weekday_idx || 0;
          for (let i = 0; i < offset; i++) {
            cells.push('<div class="calEmptyCell"></div>');
          }

          const calDays = monthData.calendar_days || monthData.days || [];
          for (const d of calDays) {
            const isSelected = (d.day === activeDayNum);
            const isFuture = Boolean(d.is_future);
            const isToday = Boolean(d.is_today);

            if (isFuture) {
              cells.push(
                '<div class="calDayCell future" data-day="' + d.day + '">' +
                  '<div class="calCellTop">' +
                    '<span class="calDayNum">' + (d.day < 10 ? '0' : '') + d.day + '</span>' +
                  '</div>' +
                  '<div class="muted" style="font-size: 10px; margin-top: 14px">Próximo</div>' +
                '</div>'
              );
              continue;
            }

            const pnlNum = Number(d.net_pnl || 0);
            const cellClasses = ['calDayCell'];
            if (isToday) cellClasses.push('today');
            if (isSelected) cellClasses.push('selected');

            if (d.has_trades) {
              if (pnlNum > 0.001) cellClasses.push('win');
              else if (pnlNum < -0.001) cellClasses.push('loss');
              else cellClasses.push('neutral');
            } else {
              cellClasses.push('neutral');
            }

            if (d.is_best_day) cellClasses.push('bestDay');
            if (d.is_worst_day) cellClasses.push('worstDay');

            // Badges
            let badgesHtml = '<div class="calDayBadges">';
            if (isToday) badgesHtml += '<span class="calBadge today">HOY</span>';
            if (d.is_best_day) badgesHtml += '<span class="calBadge top">TOP</span>';
            if (d.is_worst_day) badgesHtml += '<span class="calBadge low">DRAW</span>';
            badgesHtml += '</div>';

            const pnlColor = pnlNum > 0 ? 'good' : (pnlNum < 0 ? 'bad' : '');
            const pnlDisplay = d.has_trades
              ? (pnlNum >= 0 ? '+' : '') + money(d.net_pnl)
              : '<span class="muted" style="font-weight: normal; font-size: 12px">0.00</span>';

            const retDisplay = d.has_trades && d.return_pct != null
              ? '<span class="calCellRet ' + pnlColor + '">' + (d.return_pct >= 0 ? '+' : '') + num(d.return_pct, 1) + '%</span>'
              : '';

            const tradesSub = d.has_trades
              ? d.trades_count + ' trades · ' + num(d.pos_trades_pct, 0) + '% W'
              : 'Sin trades';

            // Mini bar de distribución de aciertos/pérdidas
            let miniBarHtml = '';
            if (d.has_trades && d.trades_count > 0) {
              miniBarHtml =
                '<div class="calWinLossMiniBar">' +
                  '<div class="barW" style="width:' + (d.pos_trades_pct || 0) + '%"></div>' +
                  '<div class="barL" style="width:' + (d.neg_trades_pct || 0) + '%"></div>' +
                '</div>';
            }

            cells.push(
              '<div class="' + cellClasses.join(' ') + '" data-day="' + d.day + '" onclick="selectCalDay(' + d.day + ')">' +
                '<div class="calCellTop">' +
                  '<span class="calDayNum">' + (d.day < 10 ? '0' : '') + d.day + '</span>' +
                  badgesHtml +
                '</div>' +
                '<div>' +
                  '<div class="calCellPnl ' + pnlColor + '">' + pnlDisplay + retDisplay + '</div>' +
                  '<div class="calCellTrades">' + tradesSub + '</div>' +
                  miniBarHtml +
                '</div>' +
              '</div>'
            );
          }
          grid.innerHTML = cells.join('');
        }

        // 3. Tabla Resumen Global de Estrategias
        const stratTable = $('calStrategyTable');
        if (stratTable) {
          if (!monthData.strategy_summary || !monthData.strategy_summary.length) {
            stratTable.innerHTML = '<div class="empty">Sin actividad de estrategias en este mes.</div>';
          } else {
            stratTable.innerHTML =
              '<div class="tbl" style="max-height: 280px">' +
                '<table>' +
                  '<thead>' +
                    '<tr>' +
                      '<th style="width: 25%">Estrategia</th>' +
                      '<th style="width: 15%">PnL Neto</th>' +
                      '<th style="width: 12%">Setups</th>' +
                      '<th style="width: 12%">Ganadas</th>' +
                      '<th style="width: 12%">Perdidas</th>' +
                      '<th style="width: 12%">Win Rate</th>' +
                      '<th style="width: 12%">Mejor Día</th>' +
                    '</tr>' +
                  '</thead>' +
                  '<tbody>' +
                    monthData.strategy_summary.map((st) => {
                      const pnlNum = Number(st.pnl || 0);
                      const pnlColor = pnlNum > 0 ? 'good' : (pnlNum < 0 ? 'bad' : '');
                      return (
                        '<tr>' +
                          '<td><b>' + e(st.strategy) + '</b></td>' +
                          '<td><b class="' + pnlColor + '">' + (pnlNum >= 0 ? '+' : '') + money(st.pnl) + '</b></td>' +
                          '<td>' + st.trades + '</td>' +
                          '<td><span class="good">' + st.wins + '</span></td>' +
                          '<td><span class="bad">' + st.losses + '</span></td>' +
                          '<td><b>' + num(st.winrate, 1) + '%</b></td>' +
                          '<td>' + (st.best_day ? 'Día ' + st.best_day : '—') + '</td>' +
                        '</tr>'
                      );
                    }).join('') +
                  '</tbody>' +
                '</table>' +
              '</div>';
          }
        }
      }

      function showCalDayDetail(dayNum) {
        selectCalDay(dayNum);
      }

      function selectCalDay(dayNum) {
        activeDayNum = dayNum;

        // Actualizar clase selected en todas las celdas
        document.querySelectorAll('.calDayCell').forEach((el) => {
          if (Number(el.dataset.day) === dayNum) el.classList.add('selected');
          else el.classList.remove('selected');
        });

        // Actualizar inspector
        const monthData = (currentMdpPayload && currentMdpPayload.all_months && currentMdpPayload.all_months[activeMonthKey])
          ? currentMdpPayload.all_months[activeMonthKey]
          : currentMdpPayload;

        if (monthData) {
          updateDayInspector(dayNum, monthData);
        }
      }

      function updateDayInspector(dayNum, monthData) {
        if (!monthData) return;
        const allDays = monthData.calendar_days || monthData.days || [];
        const d = allDays.find((x) => x.day === dayNum);
        if (!d) return;

        // Header del Inspector
        $('inspDayTitle').textContent = 'Día ' + (d.day < 10 ? '0' : '') + d.day + ' · ' + e(d.weekday) + ' (' + d.date + ')';

        const badgeEl = $('inspDayBadge');
        if (badgeEl) {
          if (d.is_today) {
            badgeEl.textContent = 'HOY (ACTUAL)';
            badgeEl.className = 'pill warn';
          } else if (d.is_future) {
            badgeEl.textContent = 'PRÓXIMO DÍA';
            badgeEl.className = 'pill';
          } else if (d.has_trades) {
            if (Number(d.net_pnl) > 0.001) {
              badgeEl.textContent = 'DÍA GANADOR';
              badgeEl.className = 'pill good';
            } else if (Number(d.net_pnl) < -0.001) {
              badgeEl.textContent = 'DÍA PERDEDOR';
              badgeEl.className = 'pill bad';
            } else {
              badgeEl.textContent = 'BREAK-EVEN';
              badgeEl.className = 'pill warn';
            }
          } else {
            badgeEl.textContent = 'SIN ACTIVIDAD';
            badgeEl.className = 'pill';
          }
        }

        const pnlNum = Number(d.net_pnl || 0);
        const retNum = Number(d.return_pct || 0);
        const pnlClass = pnlNum > 0 ? 'good' : (pnlNum < 0 ? 'bad' : '');

        if ($('inspDayStatusPill')) {
          if (d.has_trades) {
            $('inspDayStatusPill').textContent = d.trades_count + ' trades cerrados · ' + (pnlNum >= 0 ? '+' : '') + money(d.net_pnl);
            $('inspDayStatusPill').className = 'pill ' + (pnlNum > 0 ? 'good' : (pnlNum < 0 ? 'bad' : 'warn'));
          } else {
            $('inspDayStatusPill').textContent = 'Sin trades cerrados';
            $('inspDayStatusPill').className = 'pill';
          }
        }

        // 4 KPIs Específicos del Día
        $('inspDayPnl').textContent = (pnlNum >= 0 ? '+' : '') + money(pnlNum);
        $('inspDayPnl').className = 'val ' + pnlClass;
        $('inspDayReturnPct').textContent = 'Rentabilidad: ' + (retNum >= 0 ? '+' : '') + num(retNum, 2) + '% sobre balance';

        $('inspDayTradesCount').textContent = d.trades_count + ' trades';
        $('inspDayTradesSub').textContent = d.has_trades ? 'Operaciones completadas en la jornada' : 'Sin trades tomados este día';

        $('inspDayPosPct').textContent = num(d.pos_trades_pct, 1) + '% WIN';
        $('inspDayPosCount').textContent = d.wins + ' de ' + d.trades_count + ' ganadoras (acierto)';

        $('inspDayNegPct').textContent = num(d.neg_trades_pct, 1) + '% LOSS';
        $('inspDayNegCount').textContent = d.losses + ' pérdidas (' + num(d.neg_trades_pct, 1) + '%) · ' + d.break_even + ' BE (' + num(d.be_trades_pct, 1) + '%)';

        // Desglose de Estrategias
        const stratsRow = $('inspDayStrategies');
        if (stratsRow) {
          const strats = Object.entries(d.strategies || {});
          if (!strats.length) {
            stratsRow.innerHTML = '<span class="muted" style="font-size: 11px">Sin estrategias operadas en este día.</span>';
          } else {
            stratsRow.innerHTML = strats.map(([sName, sData]) => {
              const sPnl = Number(sData.pnl || 0);
              const sCls = sPnl > 0 ? 'good' : (sPnl < 0 ? 'bad' : '');
              const sWr = sData.trades > 0 ? ((sData.wins / sData.trades) * 100).toFixed(1) : '0.0';
              return (
                '<div class="inspStratCard">' +
                  '<div style="display: flex; justify-content: space-between; align-items: center">' +
                    '<b style="font-size: 11.5px; color: #f4c84f">' + e(sName) + '</b>' +
                    '<b class="' + sCls + '" style="font-size: 12.5px">' + (sPnl >= 0 ? '+' : '') + money(sPnl) + '</b>' +
                  '</div>' +
                  '<div class="muted" style="font-size: 10px; margin-top: 4px">' +
                    sData.trades + ' trades · ' + sWr + '% WR (' + sData.wins + 'W / ' + sData.losses + 'L)' +
                  '</div>' +
                '</div>'
              );
            }).join('');
          }
        }

        // Historial Detallado de Operaciones del Día
        const opsTable = $('inspDayOperationsTable');
        if (opsTable) {
          const ops = (d.operations || []).slice();
          // Ordenar siempre desde la hora más reciente a la más antigua
          ops.sort((a, b) => {
            const timeA = String(a.datetime || a.time_str || '');
            const timeB = String(b.datetime || b.time_str || '');
            if (timeA < timeB) return 1;
            if (timeA > timeB) return -1;
            const tA = Number(a.ticket || a.trade_id || 0);
            const tB = Number(b.ticket || b.trade_id || 0);
            return tB - tA;
          });
          if ($('inspDayOpsCount')) $('inspDayOpsCount').textContent = ops.length + ' operaciones';

          if (!ops.length) {
            opsTable.innerHTML = '<div class="empty" style="padding: 16px">No se registraron operaciones cerradas en esta fecha.</div>';
          } else {
            opsTable.innerHTML =
              '<table class="dayOpsTable">' +
                '<thead>' +
                  '<tr>' +
                    '<th style="width: 38px; text-align: center">' +
                      '<input type="checkbox" id="selectAllRows" onchange="toggleAllRows(this)" />' +
                    '</th>' +
                    '<th style="width: 85px">Ticket / ID</th>' +
                    '<th style="width: 75px">Hora</th>' +
                    '<th style="width: 105px">Activo</th>' +
                    '<th style="width: 135px">Estrategia</th>' +
                    '<th style="width: 65px">Dirección</th>' +
                    '<th style="width: 75px">Pierna</th>' +
                    '<th style="width: 110px">Resultado</th>' +
                    '<th style="width: 110px">PnL Neto</th>' +
                    '<th style="width: 65px">R:R</th>' +
                    '<th style="min-width: 280px">Auditoría Técnica</th>' +
                  '</tr>' +
                '</thead>' +
                '<tbody>' +
                  ops.map((op) => {
                    const opPnl = Number(op.net_pnl || 0);
                    const opPnlClass = opPnl > 0 ? 'good' : (opPnl < 0 ? 'bad' : '');
                    const resPill = op.is_win
                      ? '<span class="pill good">GANADA (WIN)</span>'
                      : (op.is_loss ? '<span class="pill bad">PERDIDA (LOSS)</span>' : '<span class="pill warn">BREAK-EVEN</span>');
                    const dirPill = op.direction === 'BUY'
                      ? '<span style="color: #00db79; font-weight: 700">BUY</span>'
                      : (op.direction === 'SELL' ? '<span style="color: #ff453a; font-weight: 700">SELL</span>' : e(op.direction || '—'));
                    const retStr = op.pnl_percent != null
                      ? ' (' + (op.pnl_percent >= 0 ? '+' : '') + num(op.pnl_percent, 2) + '%)'
                      : '';
                    const timeDisplay = op.time_str || (op.datetime ? new Date(op.datetime).toLocaleTimeString('es-CL') : '—');
                    const tradeIdVal = String(op.source_trade_id || op.trade_id || op.id || '');
                    const isChecked = selectedTradeIds.has(tradeIdVal);
                    return (
                      '<tr>' +
                        '<td style="text-align: center">' +
                          '<input type="checkbox" class="rowSelect" value="' + e(tradeIdVal) + '"' + (isChecked ? ' checked' : '') + ' onchange="onRowSelectChange()">' +
                        '</td>' +
                        '<td><b>#' + e(op.ticket || op.trade_id || '—') + '</b></td>' +
                        '<td class="muted">' + e(timeDisplay) + '</td>' +
                        '<td><b>' + e(op.asset || op.instrument || '—') + '</b></td>' +
                        '<td><b>' + e(op.strategy || '—') + '</b></td>' +
                        '<td>' + dirPill + '</td>' +
                        '<td><span class="muted">' + e(op.leg || '—') + '</span></td>' +
                        '<td>' + resPill + '</td>' +
                        '<td><b class="' + opPnlClass + '">' + (opPnl >= 0 ? '+' : '') + money(opPnl) + '</b><span class="muted" style="font-size: 10px">' + retStr + '</span></td>' +
                        '<td><b>' + (op.realized_rr != null ? num(op.realized_rr, 2) + 'R' : '—') + '</b></td>' +
                        '<td>' + auditHtml(op) + '</td>' +
                      '</tr>'
                    );
                  }).join('') +
                '</tbody>' +
              '</table>';
            onRowSelectChange();
          }
        }
      }

      function showDptNotification(msg, isError) {
        let toast = $('dptToast');
        if (!toast) {
          toast = document.createElement('div');
          toast.id = 'dptToast';
          toast.style.cssText = 'position:fixed;bottom:24px;right:24px;padding:12px 20px;border-radius:8px;font-weight:700;font-size:13px;z-index:99999;box-shadow:0 6px 18px rgba(0,0,0,0.5);transition:all 0.3s ease;pointer-events:none;';
          document.body.appendChild(toast);
        }
        toast.textContent = msg;
        toast.style.background = isError ? '#ff453a' : '#00db79';
        toast.style.color = '#000000';
        toast.style.opacity = '1';
        toast.style.transform = 'translateY(0)';
        setTimeout(() => {
          if (toast) {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(10px)';
          }
        }, 3500);
      }

      function renderDailyProfitTarget(s) {
        const d = (s && s.daily_profit_target) ? s.daily_profit_target : (s || {});
        const card = $('dailyProfitTargetCard');
        if (!card) return;
        const enabled = Boolean(d.enabled);
        const isLocked = Boolean(d.is_locked);
        const overrideUnlocked = Boolean(d.override_unlocked);
        const targetPct = Number(d.target_percent != null ? d.target_percent : 2.0).toFixed(2);
        const extraBuffer = Number(d.extra_target_buffer_percent != null ? d.extra_target_buffer_percent : 1.0).toFixed(2);
        const effectiveTarget = Number(d.effective_target_percent != null ? d.effective_target_percent : targetPct).toFixed(2);
        const dailyReturn = Number(d.daily_return_pct || 0.0);
        const todayPnl = Number(d.today_net_pnl || 0.0);
        const tradesCount = Number(d.today_trades_count || 0);
        const wins = Number(d.today_winning_trades || 0);
        const losses = Number(d.today_losing_trades || 0);

        const badge = $('dptStatusBadge');
        if (badge) {
          if (!enabled) {
            badge.className = 'pill';
            badge.textContent = '⚪ Desactivado';
          } else if (isLocked) {
            badge.className = 'pill bad';
            badge.textContent = '🔒 Meta Alcanzada · Entradas Bloqueadas';
          } else if (overrideUnlocked) {
            badge.className = 'pill warn';
            badge.textContent = `⚡ Desbloqueo Activo (+${extraBuffer}% extra)`;
          } else {
            badge.className = 'pill good';
            badge.textContent = '🟢 Operando Normal';
          }
        }

        const chk = $('dptEnabledCheckbox');
        if (chk && document.activeElement !== chk) chk.checked = enabled;
        const inp = $('dptTargetPercentInput');
        if (inp && document.activeElement !== inp) inp.value = targetPct;

        if ($('dptReturnDisplay')) {
          $('dptReturnDisplay').textContent = (dailyReturn >= 0 ? '+' : '') + dailyReturn.toFixed(2) + '%';
          $('dptReturnDisplay').style.color = dailyReturn > 0 ? '#00db79' : dailyReturn < 0 ? '#ff453a' : 'inherit';
        }
        if ($('dptTodayPnlDisplay')) {
          $('dptTodayPnlDisplay').textContent = (todayPnl >= 0 ? '+$' : '-$') + Math.abs(todayPnl).toFixed(2) + ' hoy';
          $('dptTodayPnlDisplay').style.color = todayPnl > 0 ? '#00db79' : todayPnl < 0 ? '#ff453a' : '#94a3b8';
        }
        if ($('dptTargetDisplay')) {
          $('dptTargetDisplay').textContent = effectiveTarget + '%' + (overrideUnlocked ? ` (base ${targetPct}% + ${extraBuffer}% buffer)` : '');
        }
        if ($('dptTradesSummary')) {
          $('dptTradesSummary').textContent = `${tradesCount} cerrados · ${wins} ganados / ${losses} perdidos`;
        }

        const prog = $('dptProgressBar');
        if (prog) {
          const eff = parseFloat(effectiveTarget) || 2.0;
          const ratio = eff > 0 ? Math.min(100, Math.max(0, (dailyReturn / eff) * 100)) : 0;
          prog.style.width = ratio.toFixed(1) + '%';
          prog.style.background = isLocked ? '#00db79' : dailyReturn < 0 ? '#ff453a' : '#d79b19';
        }

        const banner = $('dptLockedBanner');
        if (banner) {
          banner.style.display = isLocked ? 'block' : 'none';
          if (isLocked && $('dptBannerText')) {
            $('dptBannerText').innerHTML = `<b>🎯 ¡META DIARIA CUMPLIDA!</b> Se ha alcanzado un retorno de <b>+${dailyReturn.toFixed(2)}%</b> (meta: ${effectiveTarget}%). Las nuevas entradas se encuentran bloqueadas en todos los workers para proteger tus ganancias.<br><span style="font-size:11px; color:#cbd5e1;">🛡️ Las posiciones abiertas continúan activas con gestión de riesgo (SL, TP, BE con protección de swap y spread).<br>🌏 Reactivación automática de todos los workers en la próxima <b>sesión de Asia (00:00 UTC / 09:00 JST)</b>.</span>`;
          }
        }
      }

      window.saveDailyTargetSettings = async function() {
        const chk = $('dptEnabledCheckbox');
        const inp = $('dptTargetPercentInput');
        const btn = $('dptSaveSettingsBtn');
        if (!inp) return;
        const enabled = chk ? chk.checked : true;
        const target_percent = parseFloat(inp.value) || 2.0;
        if (btn) { btn.disabled = true; btn.textContent = 'Guardando...'; }
        try {
          const res = await fetch('/api/daily-target/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ enabled, target_percent })
          });
          const data = await res.json();
          if (!res.ok || !data.ok) throw new Error(data.error || 'No se pudo guardar la meta');
          if (data.daily_profit_target) {
            renderDailyProfitTarget(data.daily_profit_target);
          }
          showDptNotification(`✓ Meta diaria (${enabled ? target_percent.toFixed(2) + '%' : 'Desactivada'}) guardada exitosamente y persistida.`);
          if (typeof go === 'function') await go();
          else if (typeof window.go === 'function') await window.go();
        } catch (err) {
          showDptNotification('❌ Error al guardar meta diaria: ' + err.message, true);
        } finally {
          if (btn) { btn.disabled = false; btn.textContent = 'Guardar Meta'; }
        }
      };

      window.openDptOverrideModal = function() {
        const modal = $('dptRiskModal');
        if (modal) modal.style.display = 'flex';
      };

      window.closeDptOverrideModal = function() {
        const modal = $('dptRiskModal');
        if (modal) modal.style.display = 'none';
      };

      window.confirmDptOverride = async function() {
        const btn = $('dptConfirmOverrideBtn');
        if (btn) btn.disabled = true;
        try {
          const res = await fetch('/api/daily-target/override', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ confirm: true, extra_percent: 1.0 })
          });
          const data = await res.json();
          if (!res.ok || !data.ok) throw new Error(data.error || 'No se pudo desbloquear');
          closeDptOverrideModal();
          if (data.daily_profit_target) {
            renderDailyProfitTarget(data.daily_profit_target);
          }
          showDptNotification('⚡ Nuevas entradas desbloqueadas con buffer adicional asumido.');
          if (typeof go === 'function') await go();
          else if (typeof window.go === 'function') await window.go();
        } catch (err) {
          showDptNotification('❌ Error al desbloquear: ' + err.message, true);
        } finally {
          if (btn) btn.disabled = false;
        }
      };

      let selectedTradeIds = new Set();
      function render(a) {
        a = a || {};
        renderDailyProfitTarget(a.daily_profit_target);
        let x = a.snapshot || {},
          z = a.stats || {},
          r = a.recent_trades || [];
        $('balance').textContent = money(x.balance);
        $('equity').textContent = money(x.equity);
        $('free').textContent = money(x.free_margin);
        $('profit').textContent = money(x.profit);
        $('profit').className =
          'val ' + (Number(x.profit || 0) > 0 ? 'good' : Number(x.profit || 0) < 0 ? 'bad' : '');
        $('total').textContent = z.total || 0;
        $('open').textContent = z.open || 0;
        $('closed').textContent = z.closed || 0;
        $('wr').textContent = num(z.win_rate, 1) + '%';
        $('swr').textContent = num(z.setup_win_rate, 1) + '%';
        $('pnl').textContent = money(z.net_pnl);
        $('pnl').className =
          Number(z.net_pnl || 0) > 0 ? 'good' : Number(z.net_pnl || 0) < 0 ? 'bad' : '';
        renderAI(a.meta_labeling);
        renderPrePost(a.winrate_pre_post);
        renderMonthlyDailyPerformance(a.monthly_daily_performance || (a.period_performance || {}).monthly_daily_performance);
        $('strategyStats').innerHTML =
          (z.by_strategy || []).map(strategyHtml).join('') ||
          '<div class="empty">Aún no hay setups cerrados para comparar.</div>';
        $('stamp').textContent = x.snapshot_time
          ? 'Último snapshot DB: ' +
            new Date(x.snapshot_time).toLocaleString('es-CL') +
            ' · ' +
            e(x.broker || 'MT5')
          : 'Todavía no hay snapshot guardado en la base de datos.';
        $('dbsource').textContent =
          'Última actualización: ' +
          (a.generated_at ? new Date(a.generated_at).toLocaleString('es-CL') : '—');
        let db = a.database || {};
        if ($('dbpath')) $('dbpath').textContent = 'SQLite: ' + e(db.path || 'ruta no informada') + ' · trades ' + e(db.trade_rows ?? '—') + ' · journal ' + e(db.trade_journal_rows ?? '—') + ' · snapshots ' + e(db.account_snapshot_rows ?? '—') + (db.bootstrap && db.bootstrap.recovered ? ' · RECUPERADA DESDE ' + e(db.bootstrap.recovered_from) : '');
        $('statswindow').textContent =
          a.stats_reset && a.stats_reset.reset_time
            ? 'Estadísticas desde: ' + new Date(a.stats_reset.reset_time).toLocaleString('es-CL')
            : 'Ventana estadística: historial completo';
        [
          ['tp1', z.tp1],
          ['tp2', z.tp2],
          ['tph', z.take_profit],
          ['sl', z.stop_loss],
          ['be', z.break_even],
          ['em', z.emergency],
        ].forEach(([id, v]) => ($(id).textContent = v || 0));
        let c = [
            ['#31c48d', z.tp1 || 0],
            ['#53a7ff', z.tp2 || 0],
            ['#80d8a8', z.take_profit || 0],
            ['#ef6a6a', z.stop_loss || 0],
            ['#f5b942', z.break_even || 0],
          ],
          t = Math.max(
            1,
            c.reduce((n, q) => n + q[1], 0),
          );
        $('bar').innerHTML = c
          .map((q) =>
            q[1]
              ? '<i style="display:block;background:' +
                q[0] +
                ';width:' +
                (q[1] / t) * 100 +
                '%"></i>'
              : '',
          )
          .join('');
        const liveIds = new Set(r.map((q) => String(q.id)));
        for (const id of Array.from(selectedTradeIds)) {
          if (!liveIds.has(id)) selectedTradeIds.delete(id);
        }
        if ($('rows')) {
          $('rows').innerHTML =
            r
              .map(
                (q) =>
                  '<tr><td><input type="checkbox" class="rowSelect" value="' +
                  e(q.id) +
                  '"' +
                  (selectedTradeIds.has(String(q.id)) ? ' checked' : '') +
                  ' onchange="onRowSelectChange()"></td><td>' +
                  e(q.id) +
                  '</td><td><b>' +
                  e(q.strategy) +
                  '</b><div class="tradeMeta">' +
                  e(q.instrument) +
                  '</div></td><td>' +
                  e(q.direction) +
                  '<div class="tradeMeta">' +
                  e(q.status) +
                  ' · ' +
                  e(q.leg || q.execution_mode) +
                  '</div></td><td>' +
                  e(q.entry_time ? new Date(q.entry_time).toLocaleString('es-CL') : '—') +
                  '</td><td><b class="' +
                  (Number(q.net_pnl || 0) > 0 ? 'good' : Number(q.net_pnl || 0) < 0 ? 'bad' : '') +
                  '">' +
                  money(q.net_pnl) +
                  '</b><div class="tradeMeta">RR ' +
                  num(q.realized_rr) +
                  ' / plan ' +
                  num(q.planned_rr) +
                  '</div></td><td>' +
                  e(q.classification) +
                  '</td><td>' +
                  auditHtml(q) +
                  '</td></tr>',
              )
              .join('') || '<tr><td colspan="8" class="empty">No hay trades registrados.</td></tr>';
        }
        onRowSelectChange();
      }
      function toggleAllRows(cb) {
        document.querySelectorAll('.rowSelect').forEach((el) => {
          el.checked = cb.checked;
          if (cb.checked) selectedTradeIds.add(el.value);
          else selectedTradeIds.delete(el.value);
        });
        onRowSelectChange();
      }
      function onRowSelectChange() {
        document.querySelectorAll('.rowSelect').forEach((el) => {
          if (el.checked) selectedTradeIds.add(el.value);
          else selectedTradeIds.delete(el.value);
        });
        const count = selectedTradeIds.size;
        if ($('bulkDownloadBtn')) {
          $('bulkDownloadBtn').disabled = count === 0;
          $('bulkDownloadBtn').textContent =
            'Descargar seleccionados (.xlsx)' + (count ? ' (' + count + ')' : '');
        }
        if ($('selectAllRows')) {
          const all = document.querySelectorAll('.rowSelect');
          $('selectAllRows').checked = all.length > 0 && Array.from(all).every((el) => el.checked);
        }
      }
      async function downloadSelectedAudits() {
        const ids = Array.from(selectedTradeIds)
          .map(Number)
          .filter((n) => !isNaN(n));
        if (!ids.length) return;
        const btn = $('bulkDownloadBtn');
        btn.disabled = true;
        btn.textContent = 'Generando...';
        try {
          const resp = await fetch('/api/account/trades/audit/excel/bulk', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ trade_ids: ids }),
          });
          if (!resp.ok) {
            let msg = 'HTTP ' + resp.status;
            try {
              const j = await resp.json();
              msg = j.error || msg;
            } catch (_) {}
            throw new Error(msg);
          }
          const blob = await resp.blob();
          const disposition = resp.headers.get('Content-Disposition') || '';
          const match = /filename="?([^"]+)"?/.exec(disposition);
          const filename = match ? match[1] : 'DaemonBlackFx_Auditorias_Lote.zip';
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = filename;
          document.body.appendChild(a);
          a.click();
          a.remove();
          URL.revokeObjectURL(url);
          selectedTradeIds.clear();
        } catch (err) {
          alert('No fue posible descargar las auditorías: ' + err.message);
        } finally {
          onRowSelectChange();
        }
      }
      let accountBusy = false;
      async function go() {
        if (document.hidden || accountBusy) return;
        accountBusy = true;
        const controller = new AbortController(),
          timeout = setTimeout(() => controller.abort(), 30000);
        try {
          let r = await fetch('/api/account?x=' + Date.now(), {
            cache: 'no-store',
            signal: controller.signal,
          });
          if (!r.ok) throw new Error('HTTP ' + r.status + ' ' + (await r.text()));
          render(await r.json());
          pageLoading.done();
        } catch (err) {
          $('stamp').textContent = 'Sin conexión: ' + err.message;
          if ($('dbpath')) $('dbpath').textContent = 'SQLite/API: ' + err.message;
          pageLoading.fail('No se pudieron cargar los datos de cuenta. Intenta nuevamente.');
        } finally {
          clearTimeout(timeout);
          accountBusy = false;
        }
      }
      window.go = go;
      go();
      setInterval(go,6000);
      document.addEventListener('visibilitychange', () => {
        if (!document.hidden) go();
      });
    </script>
  </body>
</html>
'''

from dashboard.page_loading import with_page_loading

ACCOUNT_HTML = with_page_loading(ACCOUNT_HTML)
