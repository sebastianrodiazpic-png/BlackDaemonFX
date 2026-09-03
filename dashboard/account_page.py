ACCOUNT_HTML = r'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>DaemonBlackFx · Cuenta activa</title>
<style>:root{color-scheme:dark;--bg:#050708;--p:#0a0e10;--p2:#10161a;--t:#f5f5f2;--m:#9fa2a5;--l:#5b4514;--g:#00db79;--r:#ff453a;--y:#f5bd36;--b:#d79b19}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--t);font:14px system-ui}.w{max-width:1380px;margin:auto;padding:18px}.top{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}.nav{display:flex;gap:8px}.btn{color:var(--t);background:var(--p2);border:1px solid var(--l);padding:9px 12px;border-radius:9px;text-decoration:none}.grid{display:grid;grid-template-columns:repeat(12,1fr);gap:12px;margin-top:15px}.c{background:var(--p);border:1px solid var(--l);border-radius:14px;padding:14px}.k{grid-column:span 3}.half{grid-column:span 6}.full{grid-column:1/-1}.lab{color:var(--m);font-size:11px;text-transform:uppercase}.val{font-size:25px;font-weight:800;margin-top:5px}.stats{display:grid;grid-template-columns:repeat(6,1fr);gap:8px}.s{background:var(--p2);padding:10px;border-radius:9px}.s b{display:block;font-size:19px}.bar{height:18px;background:#192a37;border-radius:99px;overflow:hidden;display:flex;margin:12px 0}.leg{display:flex;gap:13px;flex-wrap:wrap;color:var(--m)}.strategyStats{display:flex;gap:7px;flex-wrap:wrap;margin-top:8px}.strategyStats span{background:var(--p2);border-radius:7px;padding:6px 8px;color:var(--m);font-size:11px}.tbl{overflow-y:auto;overflow-x:hidden;max-height:620px;width:100%}
table{width:100%;max-width:100%;border-collapse:collapse;table-layout:fixed}
th,td{padding:9px 5px;border-bottom:1px solid var(--l);text-align:left;white-space:normal;overflow-wrap:anywhere;word-break:normal;vertical-align:top;font-size:12px}
th{color:var(--m);font-size:10px;text-transform:uppercase;position:sticky;top:0;background:var(--p);z-index:2}
th:nth-child(1),td:nth-child(1){width:3%}
th:nth-child(2),td:nth-child(2){width:8%}
th:nth-child(3),td:nth-child(3){width:4%}
th:nth-child(4),td:nth-child(4){width:5%}
th:nth-child(5),td:nth-child(5){width:6%}
th:nth-child(6),td:nth-child(6){width:9%}
th:nth-child(7),td:nth-child(7){width:9%}
th:nth-child(8),td:nth-child(8){width:5%}
th:nth-child(9),td:nth-child(9){width:5%}
th:nth-child(10),td:nth-child(10){width:6%}
th:nth-child(11),td:nth-child(11){width:5%}
th:nth-child(12),td:nth-child(12){width:7%}
th:nth-child(13),td:nth-child(13){width:28%}
.good{color:var(--g)}.bad{color:var(--r)}.warn{color:var(--y)}
.auditDetail{white-space:normal;min-width:0;max-width:none;line-height:1.45;overflow-wrap:anywhere}
.auditDetail details{max-width:100%}
.auditDetail .pill{white-space:normal;overflow-wrap:anywhere}.auditOpen{display:inline-block;margin-top:2px;font-size:11px}
.pill{display:inline-block;border:1px solid var(--l);border-radius:99px;padding:2px 7px;margin:2px;font-size:11px}.auditBlock{margin-top:6px;padding:7px;background:var(--p2);border-radius:7px}@media(max-width:900px){.k,.half{grid-column:span 6}.stats{grid-template-columns:repeat(2,1fr)}th,td{font-size:10px;padding:7px 3px}.auditDetail{font-size:10px}.pill{font-size:9px;padding:2px 4px}}@media(max-width:560px){.k,.half{grid-column:1/-1}.stats{grid-template-columns:1fr}.w{padding:10px}} .brandStrip{display:flex;align-items:center;gap:14px;margin-bottom:16px;padding-bottom:14px;border-bottom:1px solid var(--l)}.brandStrip img{width:78px;height:78px;object-fit:cover;border-radius:12px;border:1px solid #765719}.brandStrip strong{font-size:24px;letter-spacing:.04em}.brandStrip strong span{color:#f4c84f}.c{box-shadow:inset 0 1px 0 rgba(255,211,102,.03)}
</style></head>
<body><main class="w"><div class="brandStrip"><img src="/assets/blackdaemonfx_logo.jpeg" alt="Logo BlackDaemonFX"><div><strong>BLACKDAEMON<span>FX</span></strong><div style="color:var(--m);letter-spacing:.13em">ESTRATEGIA · DISCIPLINA · RESULTADOS</div></div></div><div class="top"><div><h1 style="margin:0">Cuenta activa</h1><div style="color:var(--m)">Todos los indicadores de esta página se reconstruyen desde SQLAlchemy. Trades, abiertos, cerrados, Win rate, PnL, cierres y snapshot de cuenta no dependen del estado temporal del dashboard.</div></div><div class="nav"><a class="btn" href="/">Dashboard</a><a class="btn" href="/instruments">Instrumentos</a></div></div><section class="grid">
<div class="c k"><div class="lab">Balance</div><div class="val" id="balance">—</div></div><div class="c k"><div class="lab">Equity</div><div class="val" id="equity">—</div></div><div class="c k"><div class="lab">Margen libre</div><div class="val" id="free">—</div></div><div class="c k"><div class="lab">Profit flotante</div><div class="val" id="profit">—</div></div>
<div class="c half"><div class="lab">Actividad</div><div class="stats"><div class="s">Trades<b id="total">0</b></div><div class="s">Abiertos<b id="open">0</b></div><div class="s">Cerrados<b id="closed">0</b></div><div class="s">WR piernas<b id="wr">0%</b></div><div class="s">WR setups<b id="swr">0%</b></div><div class="s">PnL neto<b id="pnl">0</b></div></div><div id="strategyStats" class="strategyStats"></div><div id="stamp" style="color:var(--m);margin-top:10px">Sin snapshot.</div><div id="dbsource" style="color:var(--m);margin-top:5px;font-size:11px">Fuente: SQLAlchemy local</div><div id="dbpath" style="color:var(--m);margin-top:3px;font-size:11px;word-break:break-all">SQLite: verificando ruta…</div><div id="statswindow" style="color:var(--m);margin-top:3px;font-size:11px">Ventana estadística: historial completo</div></div>
<div class="c half"><div class="lab">Cierres</div><div class="bar" id="bar"></div><div class="leg"><span>TP1 <b id="tp1">0</b></span><span>TP2 <b id="tp2">0</b></span><span>TP3 <b id="tp3">0</b></span><span>TP4 <b id="tp4">0</b></span><span>TP histórico <b id="tph">0</b></span><span>Stop Loss <b id="sl">0</b></span><span>BE/Otro <b id="be">0</b></span><span>Emergencia <b id="em">0</b></span></div></div>
<div class="c full"><div class="lab">Historial DB · SQLAlchemy únicamente</div><div class="tbl"><table><thead><tr><th>ID</th><th>Instrumento</th><th>Dir.</th><th>Estado</th><th>Pierna</th><th>Entrada</th><th>Salida</th><th>RR plan</th><th>RR real</th><th>PnL</th><th>Riesgo</th><th>Cierre</th><th>Confirmaciones persistentes</th></tr></thead><tbody id="rows"></tbody></table></div></div></section></main>
<script>const $=x=>document.getElementById(x),money=v=>v==null?'—':Number(v).toLocaleString('es-CL',{minimumFractionDigits:2,maximumFractionDigits:2}),num=(v,d=2)=>v==null?'—':Number(v).toFixed(d),e=v=>String(v??'—').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));function auditHtml(q){
  const passed=q.passed_confirmations||[];
  const missing=q.missing_confirmations||[];
  const critical=q.critical_confirmation_failures||[];
  const details=q.confirmation_details||{};
  let out='<div><b>'+e(q.confirmation_decision||'Sin auditoría')+'</b>';
  out+=' · score '+(q.confirmation_score==null?'—':num(q.confirmation_score,0));
  out+=' · confirmación '+(q.confirmation_percentage==null?'—':num(q.confirmation_percentage,0)+'%')+'</div>';
  if(q.chart_pattern_confirmed){
    out+='<div class="auditBlock"><b>Patrón chartista:</b> <span class="good">'+
      e(String(q.chart_pattern_name||'confirmado').replaceAll('_',' '))+
      '</span> · fuerza '+(q.chart_pattern_strength==null?'—':num(Number(q.chart_pattern_strength)*100,0)+'%')+
      '</div>';
  }
  if(q.chart_pattern_conflict){
    out+='<div class="auditBlock warn"><b>Conflicto chartista:</b> '+e(q.chart_pattern_conflict_reason||'patrones opuestos detectados')+'</div>';
    if(q.chart_pattern_supporting_pattern){
      out+='<div class="auditBlock good"><b>A favor:</b> '+e(String(q.chart_pattern_supporting_pattern).replaceAll('_',' '))+
        ' · '+e(q.chart_pattern_supporting_direction||'—')+' · '+(q.chart_pattern_supporting_strength==null?'—':num(Number(q.chart_pattern_supporting_strength)*100,0)+'%')+'</div>';
    }
    if(q.chart_pattern_conflicting_pattern){
      out+='<div class="auditBlock bad"><b>En contra:</b> '+e(String(q.chart_pattern_conflicting_pattern).replaceAll('_',' '))+
        ' · '+e(q.chart_pattern_conflicting_direction||'—')+' · '+(q.chart_pattern_conflicting_strength==null?'—':num(Number(q.chart_pattern_conflicting_strength)*100,0)+'%')+'</div>';
    }
  }
  if(passed.length){
    out+='<div class="auditBlock good"><b>Aprobadas:</b> '+
      passed.map(x=>'<span class="pill">'+e(x)+'</span>').join('')+'</div>';
  }
  if(missing.length){
    out+='<div class="auditBlock warn"><b>Faltantes:</b> '+
      missing.map(x=>'<span class="pill">'+e(x)+'</span>').join('')+'</div>';
  }
  if(critical.length){
    out+='<div class="auditBlock bad"><b>Críticas:</b> '+
      critical.map(x=>'<span class="pill">'+e(x)+'</span>').join('')+'</div>';
  }
  if(Object.keys(details).length){
    out+='<details class="auditBlock"><summary>Detalle técnico persistido</summary>'+
      Object.entries(details).map(([k,v])=>'<div><b>'+e(k)+':</b> '+
      e(typeof v==='object'?JSON.stringify(v):v)+'</div>').join('')+'</details>';
  }
  const timeline=q.entry_vs_now_history||[];
  const total=q.entry_vs_now_snapshot_count||0;
  if(total){
    const latest=q.entry_vs_now_latest||timeline[0]||{};
    const cv=latest.current_view||{}, ev=latest.entry_view||{}, mk=latest.market||{};
    out+='<div class="auditBlock"><b>Historial Entrada vs. Ahora:</b> '+e(total)+' snapshots persistentes'+
      (latest.snapshot_at?' · último '+e(new Date(latest.snapshot_at).toLocaleString('es-CL')):'')+
      '<div>Entrada: '+e(ev.decision||'—')+' · score '+e(ev.score??'—')+' · conf. '+e(ev.confirmation_percentage??'—')+'%</div>'+
      '<div>Ahora: '+e(cv.decision||cv.state||'—')+' · score '+e(cv.score??'—')+' · conf. '+e(cv.confirmation_percentage??'—')+'% · R '+e(mk.current_rr??'—')+'</div></div>';
  }else{
    out+='<div class="auditBlock warn"><b>Historial Entrada vs. Ahora:</b> sin snapshots periódicos. La auditoría reconstruirá el contrato persistente de este trade sin mezclar identidades.</div>';
  }
  if(q.source_trade_id||q.id){out+='<div class="auditBlock"><a class="btn auditOpen" target="_blank" rel="noopener" href="/account/trade/'+e(q.source_trade_id||q.id)+'/audit">Abrir auditoría visual completa ↗</a></div>';}
  return out;
}
function render(a){a=a||{};let x=a.snapshot||{},z=a.stats||{},r=a.recent_trades||[];$('balance').textContent=money(x.balance);$('equity').textContent=money(x.equity);$('free').textContent=money(x.free_margin);$('profit').textContent=money(x.profit);$('profit').className='val '+(Number(x.profit||0)>0?'good':Number(x.profit||0)<0?'bad':'');$('total').textContent=z.total||0;$('open').textContent=z.open||0;$('closed').textContent=z.closed||0;$('wr').textContent=num(z.win_rate,1)+'%';$('swr').textContent=num(z.setup_win_rate,1)+'%';$('strategyStats').innerHTML=(z.by_strategy||[]).map(q=>'<span><b>'+e(q.strategy)+'</b> · WR '+num(q.win_rate,1)+'% · PnL '+money(q.net_pnl)+' · emerg. '+e(q.emergency||0)+'</span>').join('');$('pnl').textContent=money(z.net_pnl);$('pnl').className=Number(z.net_pnl||0)>0?'good':Number(z.net_pnl||0)<0?'bad':'';$('stamp').textContent=x.snapshot_time?'Último snapshot DB: '+new Date(x.snapshot_time).toLocaleString('es-CL')+' · '+e(x.broker||'MT5'):'Todavía no hay snapshot guardado en la base de datos.';$('dbsource').textContent='Fuente: '+e(a.data_source||'SQLALCHEMY_LOCAL_ONLY')+(a.generated_at?' · leído '+new Date(a.generated_at).toLocaleTimeString('es-CL'):'');let db=a.database||{};$('dbpath').textContent='SQLite: '+e(db.path||'ruta no informada')+' · trades '+e(db.trade_rows??'—')+' · journal '+e(db.trade_journal_rows??'—')+' · snapshots '+e(db.account_snapshot_rows??'—')+(db.bootstrap&&db.bootstrap.recovered?' · RECUPERADA DESDE '+e(db.bootstrap.recovered_from):'');$('statswindow').textContent=a.stats_reset&&a.stats_reset.reset_time?'Estadísticas desde: '+new Date(a.stats_reset.reset_time).toLocaleString('es-CL'):'Ventana estadística: historial completo';$('tp1').textContent=z.tp1||0;$('tp2').textContent=z.tp2||0;$('tp3').textContent=z.tp3||0;$('tp4').textContent=z.tp4||0;$('tph').textContent=z.take_profit||0;$('sl').textContent=z.stop_loss||0;$('be').textContent=z.break_even||0;$('em').textContent=z.emergency||0;let c=[['#31c48d',z.tp1||0],['#53a7ff',z.tp2||0],['#8b7cff',z.tp3||0],['#d68cff',z.tp4||0],['#80d8a8',z.take_profit||0],['#ef6a6a',z.stop_loss||0],['#f5b942',z.break_even||0]],t=Math.max(1,c.reduce((n,q)=>n+q[1],0));$('bar').innerHTML=c.map(q=>q[1]?'<i style="display:block;background:'+q[0]+';width:'+(q[1]/t*100)+'%"></i>':'').join('');$('rows').innerHTML=r.map(q=>'<tr><td>'+e(q.id)+'</td><td><b>'+e(q.instrument)+'</b></td><td>'+e(q.direction)+'</td><td>'+e(q.status)+'</td><td>'+e(q.leg||q.execution_mode)+'</td><td>'+e(q.entry_time?new Date(q.entry_time).toLocaleString('es-CL'):'—')+'</td><td>'+e(q.exit_time?new Date(q.exit_time).toLocaleString('es-CL'):'—')+'</td><td>'+num(q.planned_rr)+'</td><td>'+num(q.realized_rr)+'</td><td class="'+(Number(q.net_pnl||0)>0?'good':Number(q.net_pnl||0)<0?'bad':'')+'">'+money(q.net_pnl)+'</td><td>'+(q.risk_percent==null?'—':num(q.risk_percent)+'%')+'</td><td>'+e(q.classification)+'</td><td class="auditDetail">'+auditHtml(q)+'</td></tr>').join('')||'<tr><td colspan="13" style="color:var(--m);padding:18px">No hay trades registrados.</td></tr>'}async function go(){try{let r=await fetch('/api/account?x='+Date.now(),{cache:'no-store'});if(!r.ok)throw new Error('HTTP '+r.status+' '+await r.text());let a=await r.json();render(a)}catch(err){$('stamp').textContent='Sin conexión: '+err.message;const d=$('dbpath');if(d)d.textContent='SQLite/API: '+err.message}}go();setInterval(go,2500)</script></body></html>'''
