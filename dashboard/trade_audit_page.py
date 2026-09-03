TRADE_AUDIT_HTML = r"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>BlackDaemonFX · Auditoría del trade</title>
<style>
:root{color-scheme:dark;--bg:#050708;--p:#0a0e10;--p2:#10161a;--t:#f5f5f2;--m:#9fa2a5;--l:#5b4514;--g:#00db79;--r:#ff453a;--y:#f5bd36;--b:#d79b19}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--t);font:14px system-ui}.w{max-width:1500px;margin:auto;padding:18px}.brand{display:flex;align-items:center;gap:12px;border-bottom:1px solid var(--l);padding-bottom:12px}.brand img{width:62px;height:62px;border-radius:10px}.brand b{font-size:22px}.brand span{color:#f4c84f}.top{display:flex;justify-content:space-between;gap:12px;align-items:end;flex-wrap:wrap;margin:18px 0}.muted{color:var(--m)}.btn{display:inline-block;color:var(--t);background:var(--p2);border:1px solid var(--l);padding:9px 12px;border-radius:9px;text-decoration:none}.grid{display:grid;grid-template-columns:repeat(12,1fr);gap:12px}.card{background:var(--p);border:1px solid var(--l);border-radius:13px;padding:13px}.k{grid-column:span 3}.half{grid-column:span 6}.full{grid-column:1/-1}.lab{font-size:10px;color:var(--m);text-transform:uppercase}.val{font-size:18px;font-weight:800;margin-top:4px}.good{color:var(--g)}.bad{color:var(--r)}.warn{color:var(--y)}.timeline{margin-top:16px}.snap{display:grid;grid-template-columns:170px 1fr 1fr;gap:12px;padding:12px 0;border-bottom:1px solid #263036}.snapTime{color:var(--m);font-size:12px}.view{background:var(--p2);border-radius:9px;padding:10px;min-width:0}.view b{display:block;margin-bottom:5px}.chips{margin-top:6px}.pill{display:inline-block;border:1px solid var(--l);border-radius:99px;padding:2px 6px;margin:2px;font-size:10px;overflow-wrap:anywhere}.json{white-space:pre-wrap;overflow-wrap:anywhere;color:#b8c0c5;font:11px ui-monospace,monospace;max-height:260px;overflow-y:auto}.rr{font-size:20px;font-weight:900}.toolbar{display:flex;gap:8px;flex-wrap:wrap}.summary{display:grid;grid-template-columns:repeat(5,1fr);gap:8px}.mini{background:var(--p2);padding:9px;border-radius:8px}.mini b{display:block;font-size:16px}@media(max-width:900px){.k,.half{grid-column:span 6}.snap{grid-template-columns:1fr}.summary{grid-template-columns:repeat(2,1fr)}}@media(max-width:560px){.k,.half{grid-column:1/-1}.summary{grid-template-columns:1fr}.w{padding:10px}}
</style></head><body><main class="w">
<div class="brand"><img src="/assets/blackdaemonfx_logo.jpeg"><div><b>BLACKDAEMON<span>FX</span></b><div class="muted">AUDITORÍA VISUAL · ENTRADA VS. AHORA</div></div></div>
<div class="top"><div><h1 id="title" style="margin:0">Cargando trade…</h1><div id="subtitle" class="muted"></div></div><div class="toolbar"><a class="btn" id="excelBtn" href="#">Exportar Excel ↓</a><a class="btn" href="/account">← Cuenta</a><a class="btn" href="/">Dashboard</a></div></div>
<section class="grid">
<div class="card k"><div class="lab">Dirección</div><div class="val" id="direction">—</div></div>
<div class="card k"><div class="lab">Estado / cierre</div><div class="val" id="status">—</div></div>
<div class="card k"><div class="lab">RR real</div><div class="val" id="rr">—</div></div>
<div class="card k"><div class="lab">PnL</div><div class="val" id="pnl">—</div></div>
<div class="card half"><div class="lab">Tesis al abrir</div><div id="entry">—</div></div>
<div class="card half"><div class="lab">Último estado observado</div><div id="current">—</div></div>
<div class="card full"><div class="lab">Resumen de evolución</div><div class="summary" id="summary"></div></div>
<div class="card full"><div class="lab">Línea temporal completa · SQLAlchemy</div><div id="timeline" class="timeline"></div></div>
</section></main>
<script>
const $=x=>document.getElementById(x),e=v=>String(v??'—').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const n=(v,d=2)=>v==null?'—':Number(v).toFixed(d), money=v=>v==null?'—':Number(v).toLocaleString('es-CL',{minimumFractionDigits:2,maximumFractionDigits:2});
function pills(a){return (a||[]).map(x=>'<span class="pill">'+e(x)+'</span>').join('')}
function view(v,m,isEntry){v=v||{};m=m||{};let decision=v.decision||v.state||v.action||'—';return '<b>'+e(decision)+'</b>'+
'<div>Score: '+e(v.score??v.trade_score??'—')+' · Confirmación: '+e(v.confirmation_percentage??'—')+'%</div>'+
(isEntry?'':'<div class="rr">R actual: '+e(m.current_rr??'—')+'</div>')+
(v.h1_trend?'<div>H1: '+e(v.h1_trend)+'</div>':'')+
(v.structure_break?'<div>Estructura: '+e(v.structure_break)+'</div>':'')+
(v.chart_pattern_name?'<div>Chartista: '+e(String(v.chart_pattern_name).replaceAll('_',' '))+(v.chart_pattern_conflict?' · <span class="warn">conflicto</span>':'')+'</div>':'')+
'<div class="chips">'+pills(v.passed_confirmations||v.confirmations_passed)+'</div>'}
function render(a){let t=a.trade||{},s=a.snapshots||[],entry=a.entry_view||{},last=a.latest||{},cv=last.current_view||{},mk=last.market||{};const eb=$('excelBtn');if(eb)eb.href='/api'+location.pathname+'/excel';
$('title').textContent=(t.instrument||'Trade')+' · Trade #'+(t.id??t.source_trade_id??'—');
$('subtitle').textContent='Entrada '+(t.entry_time?new Date(t.entry_time).toLocaleString('es-CL'):'—')+' · '+s.length+' snapshots históricos';
$('direction').textContent=t.direction||'—';$('status').textContent=(t.status||'—')+' · '+(t.classification||t.result||'—');
$('rr').textContent=n(t.realized_rr);$('pnl').textContent=money(t.net_pnl);$('pnl').className='val '+(Number(t.net_pnl||0)>0?'good':Number(t.net_pnl||0)<0?'bad':'');
$('entry').innerHTML=view(entry,{},true);$('current').innerHTML=view(cv,mk,false);
let rrs=s.map(x=>Number((x.market||{}).current_rr)).filter(Number.isFinite), max=rrs.length?Math.max(...rrs):null,min=rrs.length?Math.min(...rrs):null;
$('summary').innerHTML='<div class="mini">Snapshots<b>'+e(s.length)+'</b></div><div class="mini">MFE observado<b>'+e(max==null?'—':max.toFixed(2)+'R')+'</b></div><div class="mini">MAE observado<b>'+e(min==null?'—':min.toFixed(2)+'R')+'</b></div><div class="mini">Inicio<b>'+e(s.length?new Date(s[0].snapshot_at).toLocaleTimeString('es-CL'):'—')+'</b></div><div class="mini">Último<b>'+e(s.length?new Date(s[s.length-1].snapshot_at).toLocaleTimeString('es-CL'):'—')+'</b></div>';
$('timeline').innerHTML=s.map((x,i)=>{let c=x.current_view||{},m=x.market||{},v=x.visual_context||{};return '<article class="snap"><div class="snapTime"><b>#'+(i+1)+'</b><br>'+e(x.snapshot_at?new Date(x.snapshot_at).toLocaleString('es-CL'):'—')+'<br>R '+e(m.current_rr??'—')+'</div><div class="view"><b>LO QUE VEÍA EN ESE MOMENTO</b>'+view(c,m,false)+'</div><details class="view"><summary>Contexto técnico persistido</summary><pre class="json">'+e(JSON.stringify({market:m,visual_context:v},null,2))+'</pre></details></article>'}).join('')||'<div class="muted">Este trade todavía no tiene snapshots históricos.</div>'}
async function go(){try{let r=await fetch('/api'+location.pathname+'?x='+Date.now(),{cache:'no-store'});if(!r.ok)throw new Error(await r.text());render(await r.json())}catch(err){$('title').textContent='No se pudo cargar la auditoría';$('subtitle').textContent=err.message}}go();
</script></body></html>"""
