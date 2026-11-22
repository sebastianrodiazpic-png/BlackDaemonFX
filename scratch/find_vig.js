const fs = require('fs');
const jsCode = fs.readFileSync('scratch/instruments_extracted.js', 'utf8');

let pos = 0;
while (true) {
  pos = jsCode.indexOf('visibleInstrumentGroups', pos);
  if (pos === -1) break;
  console.log('Found visibleInstrumentGroups at:', pos);
  console.log(jsCode.substring(pos, pos + 200));
  pos += 23;
}
