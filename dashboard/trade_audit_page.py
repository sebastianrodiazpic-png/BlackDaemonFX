"""Auditoría visual forense de una operación con velas de Deriv Charts."""

TRADE_AUDIT_HTML = r'''
<!doctype html>
<html lang="es">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>BlackDaemonFX · Auditoría visual</title>
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
        font: 14px system-ui;
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
      }
      .muted {
        color: var(--m);
      }
      .btn,
      .tab {
        color: var(--t);
        background: var(--p2);
        border: 1px solid var(--line);
        padding: 8px 11px;
        border-radius: 8px;
        text-decoration: none;
        font-size: 12px;
        cursor: pointer;
      }
      .tab.active {
        background: #49380f;
        color: #ffd965;
        border-color: #9c751e;
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
        padding: 14px;
        min-width: 0;
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
        font-size: 10px;
        color: var(--m);
        text-transform: uppercase;
        letter-spacing: 0.07em;
      }
      .val {
        font-size: 19px;
        font-weight: 850;
        margin-top: 5px;
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
        margin-bottom: 10px;
      }
      .chartWrap {
        height: 590px;
        background: #070b0d;
        border: 1px solid #263137;
        border-radius: 10px;
        overflow: hidden;
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
      }
      .source {
        display: inline-block;
        border: 1px solid #26654b;
        background: #0c251c;
        color: #64e6ac;
        border-radius: 99px;
        padding: 4px 8px;
        font-size: 10px;
        font-weight: 800;
      }
      .whyGrid {
        display: grid;
        gap: 8px;
        margin-top: 10px;
      }
      .datum {
        padding: 9px;
        background: var(--p2);
        border-radius: 8px;
        color: var(--m);
        font-size: 11px;
      }
      .datum b {
        display: block;
        color: var(--t);
        font-size: 13px;
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
        margin: 0 0 8px;
      }
      .pill {
        display: inline-block;
        border: 1px solid #3c432f;
        border-radius: 99px;
        padding: 4px 7px;
        margin: 2px;
        font-size: 10px;
        background: #151d22;
        overflow-wrap: anywhere;
      }
      .pill.ok {
        border-color: #236345;
        color: #72e5b0;
      }
      .pill.no {
        border-color: #703a36;
        color: #ff8b85;
      }
      .pill.opt {
        border-color: #645522;
        color: #f5cf67;
      }
      .summary {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 8px;
        margin-top: 9px;
      }
      .mini {
        background: var(--p2);
        padding: 10px;
        border-radius: 8px;
      }
      .mini b {
        display: block;
        font-size: 16px;
        margin-top: 3px;
      }
      .timeline {
        margin-top: 12px;
      }
      .snap {
        display: grid;
        grid-template-columns: 180px 1fr;
        gap: 12px;
        padding: 0 0 13px;
        margin-bottom: 13px;
        border-bottom: 1px solid #263137;
      }
      .snapTime,
      .snapBody {
        background: var(--p2);
        border-radius: 9px;
        padding: 10px;
      }
      .json {
        white-space: pre-wrap;
        overflow-wrap: anywhere;
        color: #b8c0c5;
        font:
          11px ui-monospace,
          monospace;
        max-height: 230px;
        overflow: auto;
      }
      .integrity {
        margin-top: 8px;
        font-size: 11px;
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
        <img src="/assets/blackdaemonfx_logo.jpeg" alt="Logo" />
        <div>
          <b>BLACKDAEMON<span>FX</span></b>
          <div class="muted">AUDITORÍA DERIV · DECISIÓN Y EVOLUCIÓN</div>
        </div>
      </div>
      <div class="top">
        <div>
          <h1 id="title">Cargando trade…</h1>
          <div id="subtitle" class="muted"></div>
        </div>
        <div class="toolbar">
          <a class="btn" id="excelBtn" href="#">Exportar Excel ↓</a
          ><a class="btn" href="/account">← Cuenta</a><a class="btn" href="/">Dashboard</a>
        </div>
      </div>
      <section class="grid">
        <div class="card kpi">
          <div class="lab">Dirección</div>
          <div class="val" id="direction">—</div>
        </div>
        <div class="card kpi">
          <div class="lab">Estado / cierre</div>
          <div class="val" id="status">—</div>
        </div>
        <div class="card kpi">
          <div class="lab">RR real</div>
          <div class="val" id="rr">—</div>
        </div>
        <div class="card kpi">
          <div class="lab">PnL</div>
          <div class="val" id="pnl">—</div>
        </div>
        <div class="card chartCard">
          <div class="chartHead">
            <div>
              <div class="lab">Gráfico de evidencia</div>
              <div id="chartSub" class="muted">—</div>
            </div>
            <div>
              <div class="tabs">
                <button class="tab active" data-mode="ENTRY">Momento de entrada</button
                ><button class="tab" data-mode="LATEST">Evolución posterior</button>
              </div>
              <div class="tabs" style="margin-top: 7px">
                <button class="tab active" data-tf="M5">M5</button
                ><button class="tab" data-tf="M15">M15</button
                ><button class="tab" data-tf="H1">H1</button
                ><button class="tab" data-tf="H4">H4</button>
              </div>
            </div>
          </div>
          <div class="layers">
            <label><input type="checkbox" data-layer="structure" checked /> Estructura</label
            ><label><input type="checkbox" data-layer="zones" checked /> OB/FVG</label
            ><label><input type="checkbox" data-layer="levels" checked /> Liquidez</label
            ><label><input type="checkbox" data-layer="trade" checked /> Entrada/SL/TP</label
            ><label><input type="checkbox" data-layer="volume" checked /> Volumen</label>
          </div>
          <div id="chart" class="chartWrap"><div class="empty">Cargando velas…</div></div>
          <div id="chartIntegrity" class="integrity"></div>
        </div>
        <aside class="card why">
          <div class="lab">Por qué se tomó</div>
          <div id="decision" class="val gold">—</div>
          <div id="why" class="whyGrid"></div>
          <div class="section">
            <h3>Confirmaciones aprobadas</h3>
            <div id="passed"></div>
          </div>
          <div class="section">
            <h3>Faltantes / penalizaciones</h3>
            <div id="missing"></div>
          </div>
          <div class="section">
            <h3>Confluencias opcionales</h3>
            <div id="optional"></div>
          </div>
        </aside>
        <div class="card full">
          <div class="lab">Resumen de evolución</div>
          <div class="summary" id="summary"></div>
        </div>
        <div class="card full">
          <div class="lab">Línea temporal persistente</div>
          <div class="muted" style="font-size: 12px; margin-top: 5px">
            La vista de entrada es inmutable. La evolución añade únicamente información conocida
            después de ejecutar.
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
      let audit = null,
        mode = 'ENTRY',
        tf = 'M5',
        layers = { structure: true, zones: true, levels: true, trade: true, volume: true };
      function pills(a, cls) {
        return (
          (a || [])
            .map(
              (x) =>
                '<span class="pill ' +
                cls +
                '">' +
                esc(typeof x === 'string' ? x : x.label || x.name || JSON.stringify(x)) +
                '</span>',
            )
            .join('') || '<span class="muted">Ninguna</span>'
        );
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
              ? 'Este trade no posee un gráfico inmutable de entrada. No se sustituye con datos posteriores para evitar sesgo futuro.'
              : 'Todavía no existe un refresco gráfico posterior.') +
            '</div>';
          return;
        }
        let frame = (root.timeframes || {})[tf] || {},
          c = (frame.candles || []).slice(-120);
        if (!c.length) {
          box.innerHTML =
            '<div class="empty">No existen velas ' +
            esc(tf) +
            ' persistidas para esta vista.</div>';
          return;
        }
        const W = 1120,
          H = 570,
          p = { l: 58, r: 112, t: 24, b: 32 },
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
              '" opacity=".16"><title>' +
              esc(z.label) +
              ' · ' +
              esc(z.status) +
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
              esc(l.label) +
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
            ' · O ' +
            q.open +
            ' H ' +
            q.high +
            ' L ' +
            q.low +
            ' C ' +
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
              esc(ev.label) +
              '</title></circle><text x="' +
              x(i) +
              '" y="' +
              (yy + (bull ? 15 : -8)) +
              '" text-anchor="middle" fill="' +
              col +
              '" font-size="8">' +
              esc(ev.label) +
              '</text>';
          });
        if (layers.trade) {
          [
            ['Entrada', trade.entry_price, '#53a7ff'],
            ['SL', trade.stop_loss, '#ff5b55'],
            ['TP', trade.take_profit, '#21d789'],
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
            '" fill="#91a0a8" font-size="10">TICK VOLUME DERIV</text>';
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
          esc(ci.data_source || root.data_source || 'DERIV_CHARTS') +
          '</span> · ' +
          esc(
            mode === 'ENTRY' ? 'Evidencia congelada al entrar' : 'Mercado observado posteriormente',
          ) +
          ' · ' +
          esc(tf) +
          ' · ' +
          c.length +
          ' velas';
        $('chartIntegrity').textContent =
          (mode === 'ENTRY' ? 'No se recalcula con información futura. ' : '') +
          'Captura: ' +
          (stamp ? new Date(stamp).toLocaleString('es-CL') : 'no disponible');
      }
      function why(e) {
        e = e || {};
        $('decision').textContent = e.decision || e.state || '—';
        let f = [
          ['Estrategia', e.strategy_name],
          ['H4', e.h4_trend],
          ['H1', e.h1_trend],
          [
            'Convergencia H4/H1',
            e.h4_h1_convergence === true
              ? 'CONFIRMADA'
              : e.h4_h1_convergence === false
                ? 'NO CONFIRMADA'
                : '—',
          ],
          ['Estructura M15', e.structure_break],
          ['Zona', e.zone],
          ['Score', e.score],
          [
            'Confirmación',
            e.confirmation_percentage == null ? '—' : e.confirmation_percentage + '%',
          ],
          ['RR previsto', e.planned_rr],
          ['Riesgo', e.risk_percent == null ? '—' : e.risk_percent + '%'],
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
            ? 'Armónico: ' + (e.harmonic_pattern || 'confirmado')
            : 'Armónico: no detectado · opcional',
        );
        o.push(
          e.chart_pattern_confirmed
            ? 'Chartista: ' + (e.chart_pattern_name || 'confirmado')
            : 'Chartista: no detectado · opcional',
        );
        if (e.divergence_confirmed) o.push('Divergencia confirmada');
        $('optional').innerHTML = pills(o, 'opt');
      }
      function timelineItem(x, i) {
        let c = x.current_view || {},
          m = x.market || {};
        return (
          '<article class="snap"><div class="snapTime"><b>Snapshot #' +
          (i + 1) +
          '</b><br><span class="muted">' +
          esc(x.snapshot_at ? new Date(x.snapshot_at).toLocaleString('es-CL') : '—') +
          '</span><div class="val ' +
          (Number(m.current_rr || 0) >= 0 ? 'good' : 'bad') +
          '">' +
          esc(m.current_rr == null ? 'R —' : num(m.current_rr) + 'R') +
          '</div></div><div class="snapBody"><b>' +
          esc(c.decision || c.state || c.action || '—') +
          '</b><div class="muted">' +
          esc(c.reason || 'Sin motivo adicional') +
          '</div><div style="margin-top:7px">Precio ' +
          esc(num(m.current_price, 5)) +
          ' · SL ' +
          esc(num(m.current_stop_loss, 5)) +
          ' · TP ' +
          esc(num(m.take_profit, 5)) +
          '</div><details><summary class="muted">Contexto técnico</summary><pre class="json">' +
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
      function render(a) {
        audit = a;
        let t = a.trade || {},
          s = a.snapshots || [],
          e = a.entry_view || {},
          rrs = s.map((x) => Number((x.market || {}).current_rr)).filter(Number.isFinite);
        $('excelBtn').href = '/api' + location.pathname + '/excel';
        $('title').textContent =
          (t.instrument || 'Trade') + ' · Trade #' + (t.id ?? t.source_trade_id ?? '—');
        $('subtitle').textContent =
          'Entrada ' +
          (t.entry_time ? new Date(t.entry_time).toLocaleString('es-CL') : '—') +
          ' · ' +
          s.length +
          ' snapshots · ' +
          ((a.chart_integrity || {}).data_source || 'DERIV_CHARTS');
        $('direction').textContent = t.direction || '—';
        $('status').textContent = (t.status || '—') + ' · ' + (t.classification || t.result || '—');
        $('rr').textContent = num(t.realized_rr);
        $('pnl').textContent = money(t.net_pnl);
        $('pnl').className =
          'val ' + (Number(t.net_pnl || 0) > 0 ? 'good' : Number(t.net_pnl || 0) < 0 ? 'bad' : '');
        why(e);
        $('subtitle').textContent +=
          ' · Evidencia: ' +
          ((a.learning_eligibility || {}).evidence_type || 'NO_ENTRY_EVIDENCE') +
          ' · MetaEtiquetado: ' +
          ((a.learning_eligibility || {}).reason || 'pendiente');
        const metadata = (t.details || {}).metadata || {};
        const corridor = (metadata.entry_preflight || {}).path || {};
        if (typeof corridor.full_path_clear === 'boolean') {
          $('subtitle').textContent += ' · Recorrido al TP: ' +
            (corridor.full_path_clear ? 'sin obstáculos detectados' : 'con obstáculos') +
            ' · Primer obstáculo: ' + (corridor.free_r_to_first_obstacle == null ? '—' : num(corridor.free_r_to_first_obstacle) + 'R') +
            ' · Objetivos: ' + Object.entries(corridor.target_r || {}).map(([name, r]) => name + ' ' + num(r) + 'R').join(', ');
        }
        $('summary').innerHTML =
          '<div class="mini">Snapshots<b>' +
          s.length +
          '</b></div><div class="mini">MFE observado<b>' +
          (rrs.length ? num(Math.max(...rrs)) + 'R' : '—') +
          '</b></div><div class="mini">MAE observado<b>' +
          (rrs.length ? num(Math.min(...rrs)) + 'R' : '—') +
          '</b></div><div class="mini">Entrada visual<b>' +
          ((a.chart_integrity || {}).entry_chart_present ? 'ÍNTEGRA' : 'NO DISPONIBLE') +
          '</b></div><div class="mini">Conflictos excluidos<b>' +
          esc((a.audit_integrity || {}).identity_conflicts_removed || 0) +
          '</b></div>';
        $('timeline').innerHTML =
          s.map(timelineItem).join('') ||
          '<div class="empty">Este trade todavía no tiene snapshots históricos.</div>';
        draw();
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
