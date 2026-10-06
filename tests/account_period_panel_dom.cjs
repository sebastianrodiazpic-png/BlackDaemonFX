const fs=require('fs'),vm=require('vm'),assert=require('assert');
class Element {
 constructor(){this.options=[];this.children=[];this.value='';this.style={};this.hidden=false;this.attributes={};}
 add(o){this.options.push(o)}
 replaceChildren(...xs){this.children=xs;this.options=xs.filter(x=>x.isOption)}
 append(...xs){this.children.push(...xs)}
 setAttribute(k,v){this.attributes[k]=v}
 addEventListener(){} focus(){}
}
const nodes=new Map();const get=id=>{if(!nodes.has(id))nodes.set(id,new Element());return nodes.get(id)};
const context={document:{getElementById:get,createElement:()=>new Element(),hidden:false},
 Option:function(t,v){return {text:t,value:String(v),isOption:true}},Intl,Date,Set,Map,Number,String,Error,
 setInterval:()=>{},fetch:async()=>({ok:true,json:async()=>({period_performance:{years:[2020],operations:[]}})})};
const source=fs.readFileSync('storage/analysis/account_calendar_check.js','utf8');vm.runInNewContext(source,context);
const parts=new Intl.DateTimeFormat('en-US',{timeZone:'America/Santiago',year:'numeric',month:'numeric'}).formatToParts(new Date());
const month=+parts.find(p=>p.type==='month').value,year=+parts.find(p=>p.type==='year').value;
assert.equal(get('perfMonth').value,month);assert.equal(get('perfYear').value,year);
setImmediate(()=>{assert.equal(get('perfMonth').value,month);assert.equal(get('perfYear').value,year);
get('perfHistoryTab').onclick();assert.equal(get('perfRankingView').hidden,true);
get('perfRankingTab').onclick();assert.equal(get('perfHistoryView').hidden,true);
console.log('Current month before/after API and tab navigation: OK')});
