const $=x=>document.getElementById(x),money=v=>v==null?'—':Number(v).toLocaleString('es-CL',{minimumFractionDigits:2,maximumFractionDigits:2}),num=(v,d=2)=>v==null?'—':Number(v).toFixed(d),e=v=>String(v??'—').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));function auditHtml(q){
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
function render(a){a=a||{};let x=a.snapshot||{},z=a.stats||{},r=a.recent_trades||[];$('balance').textContent=money(x.balance);$('equity').textContent=money(x.equity);$('free').textContent=money(x.free_margin);$('profit').textContent=money(x.profit);$('profit').className='val '+(Number(x.profit||0)>0?'good':Number(x.profit||0)<0?'bad':'');$('total').textContent=z.total||0;$('open').textContent=z.open||0;$('closed').textContent=z.closed||0;$('wr').textContent=num(z.win_rate,1)+'%';$('swr').textContent=num(z.setup_win_rate,1)+'%';$('strategyStats').innerHTML=(z.by_strategy||[]).map(q=>'<span><b>'+e(q.strategy)+'</b> · WR '+num(q.win_rate,1)+'% · PnL '+money(q.net_pnl)+' · emerg. '+e(q.emergency||0)+'</span>').join('');$('pnl').textContent=money(z.net_pnl);$('pnl').className=Number(z.net_pnl||0)>0?'good':Number(z.net_pnl||0)<0?'bad':'';$('stamp').textContent=x.snapshot_time?'Último snapshot DB: '+new Date(x.snapshot_time).toLocaleString('es-CL')+' · '+e(x.broker||'MT5'):'Todavía no hay snapshot guardado en la base de datos.';$('dbsource').textContent='Fuente: '+e(a.data_source||'SQLALCHEMY_LOCAL_ONLY')+(a.generated_at?' · leído '+new Date(a.generated_at).toLocaleTimeString('es-CL'):'');let db=a.database||{};$('dbpath').textContent='SQLite: '+e(db.path||'ruta no informada')+' · trades '+e(db.trade_rows??'—')+' · journal '+e(db.trade_journal_rows??'—')+' · snapshots '+e(db.account_snapshot_rows??'—')+(db.bootstrap&&db.bootstrap.recovered?' · RECUPERADA DESDE '+e(db.bootstrap.recovered_from):'');$('statswindow').textContent=a.stats_reset&&a.stats_reset.reset_time?'Estadísticas desde: '+new Date(a.stats_reset.reset_time).toLocaleString('es-CL'):'Ventana estadística: historial completo';$('tp1').textContent=z.tp1||0;$('tp2').textContent=z.tp2||0;$('tp3').textContent=z.tp3||0;$('tp4').textContent=z.tp4||0;$('tph').textContent=z.take_profit||0;$('sl').textContent=z.stop_loss||0;$('be').textContent=z.break_even||0;$('em').textContent=z.emergency||0;let c=[['#31c48d',z.tp1||0],['#53a7ff',z.tp2||0],['#8b7cff',z.tp3||0],['#d68cff',z.tp4||0],['#80d8a8',z.take_profit||0],['#ef6a6a',z.stop_loss||0],['#f5b942',z.break_even||0]],t=Math.max(1,c.reduce((n,q)=>n+q[1],0));$('bar').innerHTML=c.map(q=>q[1]?'<i style="display:block;background:'+q[0]+';width:'+(q[1]/t*100)+'%"></i>':'').join('');$('rows').innerHTML=r.map(q=>'<tr><td>'+e(q.id)+'</td><td><b>'+e(q.instrument)+'</b></td><td>'+e(q.direction)+'</td><td>'+e(q.status)+'</td><td>'+e(q.leg||q.execution_mode)+'</td><td>'+e(q.entry_time?new Date(q.entry_time).toLocaleString('es-CL'):'—')+'</td><td>'+e(q.exit_time?new Date(q.exit_time).toLocaleString('es-CL'):'—')+'</td><td>'+num(q.planned_rr)+'</td><td>'+num(q.realized_rr)+'</td><td class="'+(Number(q.net_pnl||0)>0?'good':Number(q.net_pnl||0)<0?'bad':'')+'">'+money(q.net_pnl)+'</td><td>'+(q.risk_percent==null?'—':num(q.risk_percent)+'%')+'</td><td>'+e(q.classification)+'</td><td class="auditDetail">'+auditHtml(q)+'</td></tr>').join('')||'<tr><td colspan="13" style="color:var(--m);padding:18px">No hay trades registrados.</td></tr>'}async function go(){try{let r=await fetch('/api/account?x='+Date.now(),{cache:'no-store'});if(!r.ok)throw new Error('HTTP '+r.status+' '+await r.text());let a=await r.json();render(a)}catch(err){$('stamp').textContent='Sin conexión: '+err.message;const d=$('dbpath');if(d)d.textContent='SQLite/API: '+err.message}}go();setInterval(go,2500)