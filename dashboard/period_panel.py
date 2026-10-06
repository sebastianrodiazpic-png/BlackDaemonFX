"""Shared calendar rankings for Account, dashboard and Instruments."""
PANEL = r'''<style>
#periodPerformance{box-sizing:border-box;margin:0 0 24px!important;padding:22px!important;border:1px solid #4a3c17!important;border-radius:14px!important;background:#0c1113!important;color:#e8ecec!important;font:14px system-ui!important}
#periodPerformance select,#periodPerformance button{background:#171d20;color:#e8ecec;border:1px solid #675321;border-radius:8px;padding:9px 12px;margin:3px;cursor:pointer;font-size:13px;transition:border-color 0.2s, background 0.2s}
#periodPerformance select:hover,#periodPerformance button:hover{border-color:#f4ce63;color:#f4ce63}
#periodPerformance h2{font-size:24px;margin:0 0 6px;color:#f4ce63}
#periodPerformance h3{font-size:16px;margin:12px 0 8px;color:#f5f5f2}
#periodPerformance p{color:#aeb9bc;line-height:1.5;margin:4px 0}
#periodPerformance .period-kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin:16px 0}
#periodPerformance .period-kpis div{padding:14px;border:1px solid #2a3337;border-radius:10px;background:#10161a}
#periodPerformance .period-kpis b{display:block;font-size:22px;color:#f4ce63;margin-top:6px}
#perfMonths button[aria-pressed=true]{border:2px solid #f4ce63;color:#f4ce63}
#perfMonths button{min-width:130px;text-align:left}
#periodPerformance .perf-tabs{display:flex;gap:6px;border-bottom:1px solid #2a3337;margin:14px 0 16px}
#periodPerformance button[aria-selected=true]{color:#f4ce63;border-color:#f4ce63;background:#1f282d}
#periodPerformance [hidden]{display:none!important}
#perfStatus{font-size:12px;margin:8px 0;color:#94a3b8}
#perfMonths{display:grid!important;grid-template-columns:repeat(auto-fit,minmax(145px,1fr));gap:6px!important}

/* Rankings & Assets */
#periodPerformance .rankings-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:20px}
#periodPerformance .rank-row{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:9px 12px;margin-bottom:6px;border:1px solid #1e262a;border-radius:8px;background:#11181c;transition:border-color 0.2s, background 0.2s}
#periodPerformance .rank-row:hover{border-color:#675321;background:#151e23}
#periodPerformance .rank-row small{display:block;color:#8e9da2;font-size:11px;margin-top:2px}
#periodPerformance .rank-row strong{white-space:nowrap;font-size:14px}

/* Asset Card Row with Modal trigger */
.asset-card{display:flex;justify-content:space-between;align-items:center;padding:10px 14px;margin-bottom:7px;border:1px solid #1f2a30;border-radius:9px;background:#10171b;cursor:pointer;transition:all 0.2s ease}
.asset-card:hover{border-color:#f4ce63;background:#162127;transform:translateX(3px)}
.asset-main{flex:1;min-width:0;margin-right:12px}
.asset-header-line{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:3px}
.asset-title{font-weight:700;font-size:14px;color:#f5f5f2}
.asset-badge-best{display:inline-flex;align-items:center;gap:4px;font-size:11px;font-weight:700;padding:2px 7px;border-radius:4px;background:rgba(244,206,99,0.15);color:#f4ce63;border:1px solid rgba(244,206,99,0.35);white-space:nowrap}
.asset-badge-untraded{font-size:10px;padding:2px 6px;border-radius:4px;background:#1c2429;color:#78888f;border:1px solid #2a343a}
.asset-subtitle{font-size:11px;color:#8e9da2}
.asset-metrics-box{text-align:right;white-space:nowrap}
.asset-pnl{font-size:14px;font-weight:800;display:block}
.asset-pnl.good{color:#34d399}
.asset-pnl.bad{color:#f87171}
.asset-pnl.zero{color:#94a3b8}
.asset-action-hint{font-size:10px;color:#f4ce63;margin-top:2px;display:inline-block}

/* Asset Filter Toolbar */
.assets-toolbar{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin:10px 0 12px}
.assets-search-input{flex:1;min-width:180px;background:#141b1f!important;border:1px solid #334147!important;color:#f5f5f2!important;padding:8px 12px!important;border-radius:8px!important;font-size:12px!important}
.assets-search-input:focus{outline:none;border-color:#f4ce63!important}
.filter-pills{display:flex;gap:4px}
.filter-pill{font-size:11px!important;padding:5px 9px!important;border-radius:6px!important;border:1px solid #2d383e!important;background:#131a1e!important;color:#94a3b8!important}
.filter-pill.active{background:#232e35!important;border-color:#f4ce63!important;color:#f4ce63!important;font-weight:700}
.assets-scrollbox{max-height:480px;overflow-y:auto;padding-right:4px}
.assets-scrollbox::-webkit-scrollbar{width:6px}
.assets-scrollbox::-webkit-scrollbar-thumb{background:#2e3a40;border-radius:4px}

/* Modal Overlay & Dialog */
.perf-modal-overlay{position:fixed;inset:0;background:rgba(4,7,9,0.85);backdrop-filter:blur(6px);z-index:99999;display:flex;align-items:center;justify-content:center;padding:16px;opacity:0;pointer-events:none;transition:opacity 0.22s ease}
.perf-modal-overlay.open{opacity:1;pointer-events:auto}
.perf-modal-card{background:#0e1418;border:1px solid #675321;border-radius:14px;max-width:760px;width:100%;max-height:90vh;display:flex;flex-direction:column;box-shadow:0 24px 60px rgba(0,0,0,0.85),0 0 25px rgba(244,206,99,0.18);transform:translateY(14px) scale(0.98);transition:transform 0.22s ease}
.perf-modal-overlay.open .perf-modal-card{transform:translateY(0) scale(1)}
.perf-modal-header{display:flex;justify-content:space-between;align-items:flex-start;padding:18px 20px 14px;border-bottom:1px solid #263238}
.perf-modal-header h2{font-size:20px;margin:0 0 4px;color:#f4ce63}
.perf-modal-header .sub{font-size:12px;color:#94a3b8}
.perf-modal-close{background:transparent!important;border:none!important;color:#8899a6!important;font-size:22px;line-height:1;cursor:pointer;padding:4px 8px!important;margin:0!important}
.perf-modal-close:hover{color:#f4ce63!important}
.perf-modal-body{padding:18px 20px;overflow-y:auto;flex:1}
.perf-modal-body::-webkit-scrollbar{width:6px}
.perf-modal-body::-webkit-scrollbar-thumb{background:#2a363d;border-radius:4px}

/* Winner Banner in Modal */
.best-strategy-banner{background:linear-gradient(135deg,rgba(244,206,99,0.12),rgba(14,20,24,0.7));border:1px solid #f4ce63;border-radius:10px;padding:16px;margin-bottom:18px}
.best-strategy-badge{display:inline-block;background:#f4ce63;color:#0b1013;font-size:10px;font-weight:800;padding:2px 8px;border-radius:4px;text-transform:uppercase;letter-spacing:0.04em;margin-bottom:8px}
.best-strategy-name{font-size:22px;font-weight:800;color:#f5f5f2;margin:2px 0 10px}
.best-strategy-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px}
.best-stat-item{background:rgba(0,0,0,0.35);padding:10px;border-radius:7px;border:1px solid rgba(244,206,99,0.2)}
.best-stat-item span{display:block;font-size:11px;color:#94a3b8}
.best-stat-item b{font-size:16px;color:#f5f5f2;margin-top:2px;display:block}
.best-strategy-verdict{margin-top:10px;font-size:12px;color:#d1d5db;font-style:italic}

/* Tables inside Modal */
.perf-modal-section{margin-bottom:18px}
.perf-modal-section h4{margin:0 0 4px;font-size:14px;color:#f4ce63}
.perf-table{width:100%;border-collapse:collapse;margin-top:8px;font-size:12px}
.perf-table th{text-align:left;padding:8px 10px;background:#141d22;color:#94a3b8;border-bottom:1px solid #263339;font-weight:600}
.perf-table td{padding:8px 10px;border-bottom:1px solid #1a2429;color:#e2e8f0}
.perf-table tr:hover td{background:#131c21}
.perf-modal-footer{padding:12px 20px;border-top:1px solid #263238;text-align:right}
</style>
<section id="periodPerformance">
<h2 id="periodHeading">Rendimiento mensual</h2>
<p style="font-size:12px;margin:4px 0 14px">Operaciones completas · PnL neto · Calendario de Santiago</p>
<div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap">
  <label>Año <select id="perfYear" aria-label="Año"></select></label>
  <label>Mes <select id="perfMonth" aria-label="Mes"><option value="">Todo el año</option></select></label>
  <label>Estrategia <select id="perfStrategy" aria-label="Estrategia"><option value="">Todas</option></select></label>
  <button id="perfCurrent" type="button">Volver al mes actual</button>
</div>
<div class="period-kpis">
  <div>PnL neto<b id="periodNet">—</b></div>
  <div>Operaciones completas<b id="periodCount">—</b></div>
  <div>Operaciones positivas<b id="periodWin">—</b></div>
  <div>Promedio por operación<b id="periodAvg">—</b></div>
</div>
<p id="perfStatus" role="status">Cargando historial…</p>
<div class="perf-tabs" role="tablist" aria-label="Vista de rendimiento">
  <button id="perfRankingTab" role="tab" aria-selected="true" aria-controls="perfRankingView">Rankings</button>
  <button id="perfHistoryTab" role="tab" aria-selected="false" aria-controls="perfHistoryView">Historial mensual</button>
</div>
<div id="perfRankingView" role="tabpanel" aria-labelledby="perfRankingTab" class="rankings-grid">
  <div>
    <h3>Estrategias por PnL neto</h3>
    <div id="perfStrategies"></div>
  </div>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap">
      <h3>Activos e instrumentos disponibles</h3>
      <span class="sub" style="font-size:11px;color:#94a3b8" id="assetsTotalCount">Todos los activos</span>
    </div>
    <div class="assets-toolbar">
      <input type="text" id="perfAssetSearch" placeholder="🔍 Filtrar instrumentos (ej: Crash, Step, Vol)..." class="assets-search-input" />
      <div class="filter-pills" id="assetFilterPills">
        <button type="button" class="filter-pill active" data-filter="all">Todos</button>
        <button type="button" class="filter-pill" data-filter="traded">Con trades</button>
        <button type="button" class="filter-pill" data-filter="untraded">Sin trades</button>
      </div>
    </div>
    <div class="assets-scrollbox" id="perfAssets"></div>
  </div>
</div>
<div id="perfHistoryView" role="tabpanel" aria-labelledby="perfHistoryTab" hidden>
  <h3>Meses transcurridos</h3>
  <div id="perfMonths"></div>
</div>

<!-- Modal de Diagnóstico por Instrumento -->
<div id="instrumentModal" class="perf-modal-overlay" aria-hidden="true" role="dialog" aria-modal="true">
  <div class="perf-modal-card">
    <div class="perf-modal-header">
      <div>
        <h2 id="modalInstrumentTitle">—</h2>
        <div class="sub" id="modalPeriodSubtitle">—</div>
      </div>
      <button id="modalCloseBtn" class="perf-modal-close" type="button" aria-label="Cerrar">&times;</button>
    </div>
    <div class="perf-modal-body">
      <div id="modalBestStrategyCard"></div>
      <div class="perf-modal-section">
        <h4>Estrategias evaluadas en este instrumento</h4>
        <p style="font-size:11px;color:#94a3b8;margin-bottom:6px">Expectativa y rentabilidad comparada de cada estrategia sobre este activo durante el mes.</p>
        <div id="modalStrategyComparison"></div>
      </div>
      <div class="perf-modal-section">
        <h4>Registro de operaciones del mes (<span id="modalOpsCount">0</span>)</h4>
        <p style="font-size:11px;color:#94a3b8;margin-bottom:6px">Detalle individual de setups cerrados en este activo para auditar el resultado.</p>
        <div id="modalOperationsList"></div>
      </div>
    </div>
    <div class="perf-modal-footer">
      <button id="modalDismissBtn" type="button" class="btn">Cerrar</button>
    </div>
  </div>
</div>
</section>
<script>
(()=>{
 const $=id=>document.getElementById(id),fmt=n=>Number(n).toLocaleString('es-CL',{maximumFractionDigits:2,minimumFractionDigits:2});
 let data=null, instCatalogData=null, followCurrent=true;
 const pages={perfStrategies:0};
 let activeAssetFilter='all', assetSearchQuery='';

 function currentPeriod(){
   const parts=new Intl.DateTimeFormat('en-US',{timeZone:'America/Santiago',year:'numeric',month:'numeric'}).formatToParts(new Date());
   return {year:+parts.find(p=>p.type==='year').value,month:+parts.find(p=>p.type==='month').value};
 }

 function selectCurrent(){
   const now=currentPeriod();
   if(![...$('perfYear').options].some(o=>+o.value===now.year)) $('perfYear').add(new Option(now.year,now.year));
   $('perfYear').value=now.year;
   $('perfMonth').value=now.month;
   $('periodHeading').textContent=months[now.month-1]+' '+now.year;
 }

 function switchView(history){
   $('perfRankingView').hidden=history;
   $('perfHistoryView').hidden=!history;
   $('perfRankingTab').setAttribute('aria-selected',String(!history));
   $('perfHistoryTab').setAttribute('aria-selected',String(history));
 }

 $('perfRankingTab').onclick=()=>switchView(false);
 $('perfHistoryTab').onclick=()=>switchView(true);
 [$('perfRankingTab'),$('perfHistoryTab')].forEach((tab,i)=>tab.addEventListener('keydown',e=>{
   if(['ArrowLeft','ArrowRight','Home','End'].includes(e.key)){
     e.preventDefault();
     const h=e.key==='Home'?false:e.key==='End'?true:!i;
     switchView(h);
     $(h?'perfHistoryTab':'perfRankingTab').focus();
   }
 }));

 const months=['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'];
 months.forEach((m,i)=>$('perfMonth').add(new Option(m,i+1)));
 selectCurrent();

 function getAllKnownInstruments(){
   const set=new Set();
   if(instCatalogData && Array.isArray(instCatalogData.instrument_catalog)){
     instCatalogData.instrument_catalog.forEach(g=>{(g.symbols||[]).forEach(s=>set.add(s));});
   }
   if(instCatalogData && Array.isArray(instCatalogData.selected_symbols)){
     instCatalogData.selected_symbols.forEach(s=>set.add(s));
   }
   if(data && Array.isArray(data.operations)){
     data.operations.forEach(op=>{
       if(op.asset && op.asset!=='SIN_ACTIVO') set.add(op.asset);
     });
   }
   return Array.from(set);
 }

 function aggregate(rows,key){
   const map=new Map();
   rows.forEach(r=>{
     let a=map.get(r[key])||{name:r[key],pnl:0,n:0,w:0};
     a.pnl+=Number(r.net_pnl)||0;
     a.n++;
     a.w+=(Number(r.net_pnl)||0)>0;
     map.set(r[key],a);
   });
   return [...map.values()].sort((a,b)=>b.pnl-a.pnl||a.name.localeCompare(b.name));
 }

 function showStrategies(id,rows){
   const host=$(id);
   host.replaceChildren();
   if(!rows.length){host.textContent='Sin operaciones cerradas.';return;}
   const max=Math.ceil(rows.length/5);
   pages[id]=Math.min(pages[id]||0,max-1);
   const start=(pages[id]||0)*5;
   rows.slice(start,start+5).forEach((r,i)=>{
     const line=document.createElement('div');
     line.className='rank-row';
     const label=document.createElement('span'),small=document.createElement('small'),value=document.createElement('strong');
     label.textContent=`${start+i+1}. ${r.name}`;
     small.textContent=`${r.n} operaciones · ${fmt(100*r.w/r.n)}% positivas`;
     label.append(small);
     value.textContent=fmt(r.pnl);
     value.style.color=r.pnl<0?'#ff9696':'#73e2bd';
     line.append(label,value);
     host.append(line);
   });
   if(max>1){
     const nav=document.createElement('div');
     nav.style.marginTop='8px';
     const back=document.createElement('button'),next=document.createElement('button'),count=document.createElement('span');
     back.textContent='Anterior';next.textContent='Siguiente';
     back.disabled=pages[id]===0;next.disabled=pages[id]===max-1;
     count.textContent=` ${pages[id]+1} / ${max} `;
     back.onclick=()=>{pages[id]--;render();};
     next.onclick=()=>{pages[id]++;render();};
     nav.append(back,count,next);
     host.append(nav);
   }
 }

 function openInstrumentModal(assetName, assetData, periodOps, monthName, year){
   const modal=$('instrumentModal');
   $('modalInstrumentTitle').textContent=`📊 ${assetName}`;
   $('modalPeriodSubtitle').textContent=`Período: ${monthName} ${year} · Expectativa matemática y registro del activo`;

   const bestBox=$('modalBestStrategyCard');
   const compBox=$('modalStrategyComparison');
   const opsBox=$('modalOperationsList');

   // 1. Tarjeta Estrategia Más Rentable
   if(assetData && assetData.bestStrategy && assetData.hasTrades){
     const bs=assetData.bestStrategy;
     const wr=bs.n ? (100*bs.w/bs.n).toFixed(1) : '0';
     const avg=bs.n ? fmt(bs.pnl/bs.n) : '0,00';
     bestBox.innerHTML=`
       <div class="best-strategy-banner">
         <span class="best-strategy-badge">🏆 Estrategia Más Rentable</span>
         <div class="best-strategy-name">${bs.name}</div>
         <div class="best-strategy-grid">
           <div class="best-stat-item"><span>PnL Neto</span><b style="color:${bs.pnl>=0?'#34d399':'#f87171'}">${fmt(bs.pnl)} USD</b></div>
           <div class="best-stat-item"><span>Setups cerrados</span><b>${bs.n}</b></div>
           <div class="best-stat-item"><span>Efectividad</span><b style="color:#f4ce63">${wr}%</b></div>
           <div class="best-stat-item"><span>Promedio / Trade</span><b>${avg} USD</b></div>
         </div>
         <div class="best-strategy-verdict">
           En ${monthName} ${year}, <b>${bs.name}</b> demostró ser la estrategia óptima para <b>${assetName}</b>, acumulando ${fmt(bs.pnl)} en beneficio neto a través de ${bs.n} setups con un ${wr}% de acierto.
         </div>
       </div>`;
   } else {
     bestBox.innerHTML=`
       <div class="best-strategy-banner" style="border-color:#334147;background:#11181c">
         <span class="best-strategy-badge" style="background:#2a343a;color:#94a3b8">Sin histórico cerrado</span>
         <div class="best-strategy-name" style="font-size:16px;color:#94a3b8">Sin operaciones completadas en este período</div>
         <div style="font-size:12px;color:#6b7280;margin-top:4px">
           ${assetName} está disponible en el catálogo operativo pero no cuenta con setups cerrados en ${monthName} ${year}. Las estrategias configuradas evaluarán oportunidades según sus condiciones de entrada.
         </div>
       </div>`;
   }

   // 2. Tabla Comparativa de Estrategias
   if(assetData && assetData.rankedStrategies && assetData.rankedStrategies.length){
     let rowsHtml=assetData.rankedStrategies.map((s,i)=>{
       const wr=s.n ? (100*s.w/s.n).toFixed(1)+'%' : '0%';
       const isTop=i===0 && s.pnl>0;
       const badge=isTop?'<span class="asset-badge-best">🏆 Ganadora</span>':(s.pnl>0?'<span style="color:#34d399;font-weight:700">✓ Rentable</span>':'<span style="color:#f87171">En pérdida</span>');
       return `<tr>
         <td style="font-weight:700">${i+1}</td>
         <td><b>${s.name}</b></td>
         <td style="font-weight:700;color:${s.pnl>=0?'#34d399':'#f87171'}">${fmt(s.pnl)}</td>
         <td>${s.n}</td>
         <td>${wr}</td>
         <td>${fmt(s.pnl/(s.n||1))}</td>
         <td>${badge}</td>
       </tr>`;
     }).join('');
     compBox.innerHTML=`<table class="perf-table"><thead><tr><th>#</th><th>Estrategia</th><th>PnL Neto</th><th>Setups</th><th>Win Rate</th><th>Promedio</th><th>Veredicto</th></tr></thead><tbody>${rowsHtml}</tbody></table>`;
   } else {
     compBox.innerHTML='<p style="font-size:12px;color:#78888f">No hay estrategias registradas con setups cerrados en este período.</p>';
   }

   // 3. Registro de Operaciones del Mes
   const assetOps=(periodOps||[]).filter(o=>o.asset===assetName);
   $('modalOpsCount').textContent=assetOps.length;
   if(assetOps.length){
     let opsRowsHtml=assetOps.map((op,i)=>{
       const pnl=Number(op.net_pnl)||0;
       return `<tr>
         <td>#${i+1}</td>
         <td><span style="background:#1b242a;padding:2px 6px;border-radius:4px;border:1px solid #2e3a41;font-size:11px">${op.strategy||'—'}</span></td>
         <td style="font-weight:700;color:${pnl>=0?'#34d399':'#f87171'}">${fmt(pnl)} USD</td>
         <td><span style="color:${pnl>0?'#34d399':pnl<0?'#f87171':'#94a3b8'}">${pnl>0?'GANADORA':'PERDEDORA'}</span></td>
       </tr>`;
     }).join('');
     opsBox.innerHTML=`<div style="max-height:220px;overflow-y:auto"><table class="perf-table"><thead><tr><th>Op.</th><th>Estrategia</th><th>Resultado PnL</th><th>Estado</th></tr></thead><tbody>${opsRowsHtml}</tbody></table></div>`;
   } else {
     opsBox.innerHTML='<p style="font-size:12px;color:#78888f">No hay operaciones para mostrar en el mes seleccionado.</p>';
   }

   modal.classList.add('open');
   modal.setAttribute('aria-hidden','false');
 }

 function closeModal(){
   const modal=$('instrumentModal');
   modal.classList.remove('open');
   modal.setAttribute('aria-hidden','true');
 }

 $('modalCloseBtn').onclick=closeModal;
 $('modalDismissBtn').onclick=closeModal;
 $('instrumentModal').onclick=(e)=>{if(e.target===$('instrumentModal')) closeModal();};
 document.addEventListener('keydown',(e)=>{if(e.key==='Escape') closeModal();});

 function render(){
   if(!data)return;
   const year=+$('perfYear').value,month=+$('perfMonth').value,strategy=$('perfStrategy').value;
   const annual=data.operations.filter(r=>r.year===year);
   const period=annual.filter(r=>!month||r.month===month);
   const ranked=aggregate(period,'strategy');
   const filtered=period.filter(r=>!strategy||r.strategy===strategy),net=filtered.reduce((s,r)=>s+(Number(r.net_pnl)||0),0);

   const monthLabel=month?months[month-1]:'Resumen anual';
   $('periodHeading').textContent=monthLabel+' '+year;
   $('periodNet').textContent=fmt(net);
   $('periodCount').textContent=filtered.length;
   $('periodWin').textContent=filtered.length?fmt(100*filtered.filter(r=>(Number(r.net_pnl)||0)>0).length/filtered.length)+'%':'—';
   $('periodAvg').textContent=filtered.length?fmt(net/filtered.length):'—';

   showStrategies('perfStrategies',ranked);

   // Construir directorio de TODOS los instrumentos disponibles
   const allSymbols=getAllKnownInstruments();
   $('assetsTotalCount').textContent=`${allSymbols.length} instrumentos disponibles`;

   const assetStats=allSymbols.map(sym=>{
     const symOps=period.filter(r=>r.asset===sym&&(!strategy||r.strategy===strategy));
     const pnl=symOps.reduce((s,r)=>s+(Number(r.net_pnl)||0),0);
     const n=symOps.length;
     const w=symOps.filter(r=>(Number(r.net_pnl)||0)>0).length;

     // Desglose por estrategia para este activo
     const stratMap=new Map();
     symOps.forEach(op=>{
       const stName=op.strategy||'SMC';
       let ent=stratMap.get(stName);
       if(!ent){ent={name:stName,pnl:0,n:0,w:0};stratMap.set(stName,ent);}
       ent.pnl+=Number(op.net_pnl)||0;
       ent.n++;
       ent.w+=(Number(op.net_pnl)||0)>0;
     });
     const rankedStrats=Array.from(stratMap.values()).sort((a,b)=>b.pnl-a.pnl);
     const bestStrat=rankedStrats.length?rankedStrats[0]:null;

     return {
       name:sym,
       pnl:pnl,
       n:n,
       w:w,
       hasTrades:n>0,
       rankedStrategies:rankedStrats,
       bestStrategy:bestStrat
     };
   });

   // Orden: primero los que tienen operaciones (por mayor ganancia), luego por orden alfabético
   assetStats.sort((a,b)=>{
     if(a.hasTrades && !b.hasTrades) return -1;
     if(!a.hasTrades && b.hasTrades) return 1;
     if(a.hasTrades && b.hasTrades) return b.pnl - a.pnl;
     return a.name.localeCompare(b.name);
   });

   // Filtrado de activos
   let visibleAssets=assetStats;
   if(activeAssetFilter==='traded') visibleAssets=visibleAssets.filter(x=>x.hasTrades);
   else if(activeAssetFilter==='untraded') visibleAssets=visibleAssets.filter(x=>!x.hasTrades);

   if(assetSearchQuery){
     const q=assetSearchQuery.toLocaleLowerCase('es');
     visibleAssets=visibleAssets.filter(x=>x.name.toLocaleLowerCase('es').includes(q));
   }

   const assetsContainer=$('perfAssets');
   assetsContainer.replaceChildren();

   if(!visibleAssets.length){
     const emptyDiv=document.createElement('div');
     emptyDiv.style.padding='20px';
     emptyDiv.style.textAlign='center';
     emptyDiv.style.color='#78888f';
     emptyDiv.textContent='No se encontraron instrumentos para el filtro actual.';
     assetsContainer.append(emptyDiv);
   } else {
     visibleAssets.forEach((ast,idx)=>{
       const card=document.createElement('div');
       card.className='asset-card';
       card.tabIndex=0;
       card.setAttribute('role','button');
       card.setAttribute('aria-label',`Ver análisis de ${ast.name}`);

       const mainDiv=document.createElement('div');
       mainDiv.className='asset-main';

       const headLine=document.createElement('div');
       headLine.className='asset-header-line';

       const title=document.createElement('span');
       title.className='asset-title';
       title.textContent=`${idx+1}. ${ast.name}`;
       headLine.append(title);

       if(ast.bestStrategy && ast.hasTrades){
         const badge=document.createElement('span');
         badge.className='asset-badge-best';
         badge.textContent=`🏆 Top: ${ast.bestStrategy.name} (${fmt(ast.bestStrategy.pnl)})`;
         headLine.append(badge);
       } else {
         const badge=document.createElement('span');
         badge.className='asset-badge-untraded';
         badge.textContent='Sin operaciones';
         headLine.append(badge);
       }
       mainDiv.append(headLine);

       const subtitle=document.createElement('div');
       subtitle.className='asset-subtitle';
       subtitle.textContent=ast.hasTrades
         ? `${ast.n} setups · ${fmt(100*ast.w/ast.n)}% efectividad`
         : 'Catálogo disponible';
       mainDiv.append(subtitle);

       const metricsBox=document.createElement('div');
       metricsBox.className='asset-metrics-box';

       const pnlEl=document.createElement('strong');
       pnlEl.className='asset-pnl '+(ast.pnl>0?'good':ast.pnl<0?'bad':'zero');
       pnlEl.textContent=ast.hasTrades?`${fmt(ast.pnl)}`:'0,00';
       metricsBox.append(pnlEl);

       const hint=document.createElement('span');
       hint.className='asset-action-hint';
       hint.textContent='Ver desglose ↗';
       metricsBox.append(hint);

       card.append(mainDiv,metricsBox);
       card.onclick=()=>openInstrumentModal(ast.name,ast,period,monthLabel,year);
       card.onkeydown=(e)=>{if(e.key==='Enter'||e.key===' ') {e.preventDefault(); openInstrumentModal(ast.name,ast,period,monthLabel,year);}};
       assetsContainer.append(card);
     });
   }

   $('perfStatus').textContent=ranked.length?`${ranked[0].pnl>0?'Estrategia más rentable':'Mejor resultado (sin beneficio positivo)'}: ${ranked[0].name} · ${fmt(ranked[0].pnl)}. Importes en moneda de cuenta; no son rentabilidad porcentual.`:'Sin resultados para el período seleccionado.';
   if(data.excluded_incomplete_data) $('perfStatus').textContent+=` ${data.excluded_incomplete_data} operaciones excluidas por datos incompletos.`;

   $('perfMonths').replaceChildren();
   months.forEach((m,i)=>{
     const rows=annual.filter(r=>r.month===i+1&&(!strategy||r.strategy===strategy));
     const now=currentPeriod();
     if(year===now.year&&i+1>now.month)return;
     const box=document.createElement('button');
     box.type='button';
     box.setAttribute('aria-pressed',String(month===i+1));
     box.onclick=()=>{
       followCurrent=false;
       $('perfMonth').value=i+1;
       pages.perfStrategies=0;
       switchView(false);
       render();
     };
     box.textContent=`${m}: ${rows.length?fmt(rows.reduce((s,r)=>s+(Number(r.net_pnl)||0),0)):'Sin cierres'}`;
     $('perfMonths').append(box);
   });
 }

 // Toolbar de búsqueda y filtros
 $('perfAssetSearch').addEventListener('input',(e)=>{
   assetSearchQuery=e.target.value.trim();
   render();
 });

 $('assetFilterPills').querySelectorAll('.filter-pill').forEach(btn=>{
   btn.addEventListener('click',()=>{
     $('assetFilterPills').querySelectorAll('.filter-pill').forEach(b=>b.classList.remove('active'));
     btn.classList.add('active');
     activeAssetFilter=btn.dataset.filter;
     render();
   });
 });

 ['perfYear','perfMonth','perfStrategy'].forEach(id=>$(id).addEventListener('change',()=>{
   if(id!=='perfStrategy') followCurrent=false;
   pages.perfStrategies=0;
   render();
 }));

 $('perfCurrent').onclick=()=>{
   followCurrent=true;
   selectCurrent();
   pages.perfStrategies=0;
   render();
 };

 async function load(){
   try{
     const [resAcc, resInst] = await Promise.all([
       fetch('/api/account'),
       fetch('/api/instruments').catch(()=>null)
     ]);
     if(!resAcc.ok) throw Error('HTTP '+resAcc.status);
     const payload=await resAcc.json();
     data=payload.period_performance;
     if(!data) throw Error('El servicio aún no publica el historial mensual; necesita cargar la versión actualizada.');
     if(data.error) throw Error(data.error);

     if(resInst && resInst.ok){
       try{ instCatalogData=await resInst.json(); }catch(_){}
     }

     const previous=$('perfYear').value;
     $('perfYear').replaceChildren();
     [...new Set([currentPeriod().year,...(data.years||[])])].sort((a,b)=>b-a).forEach(y=>$('perfYear').add(new Option(y,y)));
     if(followCurrent){selectCurrent();}else if(data.years.includes(+previous))$('perfYear').value=previous;

     const selected=$('perfStrategy').value;
     $('perfStrategy').replaceChildren(new Option('Todas',''));
     [...new Set(data.operations.map(r=>r.strategy))].sort().forEach(s=>$('perfStrategy').add(new Option(s,s)));
     $('perfStrategy').value=selected;

     render();
   }catch(e){
     $('perfStatus').textContent='No se pudo cargar el historial. '+e.message;
   }
 }

 load();
 setInterval(()=>{if(!document.hidden)load();},60000);
})();
</script>'''

def with_period_panel(html):
    return html.replace('</body>', PANEL+'\n</body>')
