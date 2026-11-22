const fs = require('fs');
const mockState = JSON.parse(fs.readFileSync('scratch/mock_state.json', 'utf8'));

// Let's inspect visibleInstrumentGroups and groups from instruments_extracted.js
const jsCode = fs.readFileSync('scratch/instruments_extracted.js', 'utf8');

// Search for function visibleInstrumentGroups and function groups
const vStart = jsCode.indexOf('function visibleInstrumentGroups');
const gEnd = jsCode.indexOf('function selected()', vStart);
const fnCode = jsCode.substring(vStart, gEnd);

eval(fnCode);

let activeProfile = 'SYNTHETICS';
let res = groups(mockState);
console.log('SYNTHETICS groups count:', res.length);
for (const g of res) {
  console.log('  ', g.category, g.worker, g.label, (g.symbols || []).length);
}

activeProfile = 'MALAYSIAN_SNR';
res = groups(mockState);
console.log('\nMALAYSIAN_SNR groups count:', res.length);
for (const g of res) {
  console.log('  ', g.category, g.worker, g.label, (g.symbols || []).length);
}
