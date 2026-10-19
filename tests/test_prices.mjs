import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const ctx = vm.createContext({});
vm.runInContext(fs.readFileSync(new URL('../qml/logic/Omatinta.js', import.meta.url), 'utf8'), ctx);
const prices = {checked: '2026-10-12', upscale: {precision: {unitMP: 24, usd: 0.08}}};
const spec = {price: {'2K': 0.135}, dimensions: {'2K': [2048, 1152]}, priceChecked: '2026-10-12'};
const config = {res: '2K', upscaler: 'precision', upscaleFactor: 4};
const text = ctx.priceText(config, 'generate', prices, 0, 0, 4, spec, 3);
// Actual 2048×1152×4 output needs two 24MP blocks, not three guessed blocks.
assert.match(text, /upscale ~ \$0.16/);
assert.match(text, /Remaining batch ~ \$0.885/);
const tokens = {rates: [{billable: 'output_image', usd: 0.00003, unit: 'token'}]};
assert.match(ctx.priceText({...config, upscaler: 'none'}, 'generate', prices, 0, 0, 2, tokens, 6), /Batch total varies with usage; 6 outputs remain/);
assert.match(ctx.reportedCost({complete: false, edit: 0.05, upscale: null, upscaleRequested: true}), /upscale not reported/);
assert.doesNotMatch(ctx.reportedCost({complete: false, edit: 0.05, upscale: null, upscaleRequested: true}), /Final cost/);
assert.match(ctx.editingOptions([{...tokens, value:'test', label:'Test', available:false}], '1K')[0].label, /unavailable/);
console.log('Price checks passed: model dimensions, batch estimates, variable rates and partial accounting.');

assert.ok(!ctx.priceText({upscaler: 'none'}, 'upscale', prices, 0, 0, 2, {}, 1).startsWith('\n'));

assert.match(ctx.providerRate([{billable:'output_image', unit:'token', usd:.00003}]), /\$30\/output_image\/M tokens/);
assert.notEqual(ctx.dollars(.000001), '$0');
