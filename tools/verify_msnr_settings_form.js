// Execute the real settings serialization without using the user's browser.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const path = require('node:path');
const folder = process.argv[2];
const defaults = JSON.parse(fs.readFileSync(path.join(folder, 'final_defaults.json'), 'utf8'));
const nodes = new Map();
const context = vm.createContext({document: {
  getElementById: id => nodes.get(id),
  querySelectorAll: () => [],
}, fixtureDefaults: defaults});
vm.runInContext(fs.readFileSync(path.join(folder, 'panel.js'), 'utf8'), context);
const fields = vm.runInContext('Object.entries(msnrFields)', context);
for (const [key, [id, type]] of fields) {
  const value = defaults[key];
  const raw = type === 'percent' ? String(value * 100) : String(value);
  nodes.set(id, {value: raw, valueAsNumber: Number(raw), checked: value,
    checkValidity: () => true});
}
defaults.additional_symbols.forEach((name, i) => nodes.set('msnrExtra'+i, {checked: true}));
vm.runInContext('msnrCatalog=fixtureDefaults.additional_symbols; msnrSavedSettings=fixtureDefaults;', context);
const values = vm.runInContext('msnrFormValues()', context);
for (const [key, value] of Object.entries(defaults)) {
  assert.deepEqual(JSON.parse(JSON.stringify(values[key])), value, 'Default serialization: '+key);
}
assert.equal(vm.runInContext('msnrFormValid(msnrFormValues())', context), true);
assert.equal(vm.runInContext('msnrDirty(msnrFormValues())', context), false);
nodes.get('msnrPinbarMode').value = 'live';
assert.equal(vm.runInContext('msnrFormValues().retest_pinbar_mode', context), 'live');
assert.equal(vm.runInContext('msnrFormValid(msnrFormValues())', context), true);
assert.equal(vm.runInContext('msnrDirty(msnrFormValues())', context), true);
console.log('Verified all '+Object.keys(defaults).length+' defaults and editable Pinbar mode.');
