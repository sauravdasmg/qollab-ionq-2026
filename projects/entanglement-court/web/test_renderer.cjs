const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

// Small DOM harness: exercises the shipped renderer and rollback without adding
// browser libraries to the Qollab submission. No quantum experiments are run.
class Element {
  constructor(tag = 'div') {
    this.tagName = tag;
    this.childNodes = [];
    this.attrs = {};
    this.hidden = false;
    this.textContent = '';
    this.classList = { remove() {}, toggle() {} };
  }
  setAttribute(key, value) { this.attrs[key] = String(value); }
  appendChild(node) {
    if (node.tagName === '#fragment') this.childNodes.push(...node.childNodes);
    else this.childNodes.push(node);
    return node;
  }
  replaceChildren(...nodes) {
    this.childNodes = [];
    nodes.forEach(node => this.appendChild(node));
  }
  cloneNode() {
    const node = new Element(this.tagName);
    node.attrs = { ...this.attrs };
    node.hidden = this.hidden;
    node.textContent = this.textContent;
    node.html = this.html;
    node.childNodes = this.childNodes.map(child => child.cloneNode(true));
    return node;
  }
  querySelector(selector) {
    if (selector === 'tbody') return this.childNodes.find(node => node.tagName === 'tbody');
    if (selector === '#loading-text') return this.childNodes[0];
    return null;
  }
  querySelectorAll() { return []; }
  addEventListener() {}
  set innerHTML(html) { this.html = html; this.childNodes = []; }
  get innerHTML() { return this.html || ''; }
}
const ids = ['docket', 'evidence-docket', 'loading', 'error-display', 'error-text', 'status-region',
  'verdict-options', 'verdict-note-text', 'evidence-tabs', 'case-select', 'challenge-select',
  'trust-toggle', 'remeasure-btn', 'case-id', 'evidence-case-id', 'meaning-text', 'circuit-text',
  'live-values', 'recorded-values', 'comparison-meta', 'bars-target', 'table-target',
  'bars-impostor', 'table-impostor', 'parity-Z', 'table-parity-Z', 'parity-A', 'table-parity-A',
  'parity-B', 'table-parity-B', 'stamp-content', 'table-stamp'];
const elements = Object.fromEntries(ids.map(id => [id, new Element()]));
for (const id of ids.filter(id => id.startsWith('table-'))) elements[id].appendChild(new Element('tbody'));
elements.loading.appendChild(new Element());
elements['evidence-docket'].hidden = true;
let handlers = {};
let failMeasurement = false;
const data = {
  marginals: { target_Z: { '0000': 2, '0011': 2 }, impostor_Z: { '0101': 4 } },
  analysis: { parity_intervals_95: {
    target_A: [{ generator: 0, estimate: 0.8, interval: [0.3, 1], shots: 4 }],
    impostor_A: [{ generator: 0, estimate: 0.2, interval: [-0.3, 0.8], shots: 4 }]
  }, simultaneous_witness: { F_lower: 0.4, threshold: 0.5 } },
  source: 'Live built-in ideal', shots: 4
};
const context = vm.createContext({
  console, Map, Object, Array, Number, String, Set, Math,
  setTimeout() { return 1; }, clearTimeout() {},
  requestAnimationFrame(fn) { fn(); return 1; }, cancelAnimationFrame() {},
  backend: { name: 'basic_simulator' },
  court: {
    run_demo: { async callPromising() { if (failMeasurement) throw new Error('private traceback'); return data; } },
    load_recorded: { async callPromising() { return { records: [] }; } },
    get_circuit_text: { async callPromising() { return 'circuit'; } }
  },
  window: { addEventListener(name, handler) { handlers[name] = handler; } },
  document: {
    readyState: 'loading', addEventListener() {}, querySelectorAll() { return []; },
    getElementById(id) { return elements[id]; },
    createElement(tag) { return new Element(tag); },
    createElementNS(ns, tag) { return new Element(tag); },
    createDocumentFragment() { return new Element('#fragment'); }
  }
});
const source = fs.readFileSync(__dirname + '/main.js', 'utf8').replace(/^import .*;$/m, '');
vm.runInContext(source, context);
context.data = data;
vm.runInContext('renderResults(data, { records: [] })', context);
let svg = elements['bars-target'].childNodes[0];
assert.equal(svg.attrs.viewBox, '0 0 720 310');
assert.equal(svg.attrs.width, '720');
assert.equal(svg.attrs.height, '310');
const bars = svg.childNodes.filter(node => node.tagName === 'rect' && node.attrs.fill === '#2B3A8C');
assert.equal(bars.length, 16);
assert.equal(bars.filter(node => Number(node.attrs.height) > 0).length, 2);
assert.equal(elements['table-target'].querySelector('tbody').childNodes.length, 16);
assert.match(elements['table-target'].querySelector('tbody').childNodes[0].innerHTML, /0.500000/);
assert.equal(elements['parity-A'].childNodes.length, 2); // both preparations retained

// Missing/zero measurements must fail before altering either chart or table.
const previous = elements['bars-target'].childNodes[0];
context.invalid = { ...data, marginals: { target_Z: { '0000': 4 } } };
assert.throws(() => vm.runInContext('renderResults(invalid, { records: [] })', context));
assert.equal(elements['bars-target'].childNodes[0], previous);
context.invalid = { ...data, analysis: { parity_intervals_95: {}, simultaneous_witness: { threshold: 'bad' } } };
assert.throws(() => vm.runInContext('renderResults(invalid, { records: [] })', context));
assert.equal(elements['bars-target'].childNodes[0], previous); // late renderer failure

// A failure during commit itself rolls all panels back to the previous nodes.
const replace = elements['table-target'].replaceChildren;
let once = true;
elements['table-target'].replaceChildren = function (...nodes) {
  if (once) { once = false; throw new Error('commit failed'); }
  return replace.apply(this, nodes);
};
assert.throws(() => vm.runInContext('renderResults(data, { records: [] })', context));
assert.equal(elements['bars-target'].childNodes[0], previous);
elements['table-target'].replaceChildren = replace;
vm.runInContext('showLoading()', context);
assert.equal(elements.docket.hidden, false);
vm.runInContext('showError("Retry")', context);
assert.equal(elements.docket.hidden, false);
assert.equal(elements.loading.hidden, true);
assert.equal(elements['status-region'].attrs['aria-live'], 'assertive');

(async () => {
  await vm.runInContext('runDemo()', context);
  const measured = elements['bars-target'].childNodes[0];
  failMeasurement = true;
  await vm.runInContext('runDemo()', context);
  assert.equal(elements['bars-target'].childNodes[0], measured);
  assert.equal(elements.docket.hidden, false);
  assert.doesNotMatch(elements['error-text'].textContent, /private traceback/);
  vm.runInContext('setupEventListeners()', context);
  handlers.resize();
  assert.equal(elements['bars-target'].childNodes[0].attrs.viewBox, '0 0 720 310');
  console.log('Renderer checks passed');
})().catch(error => { console.error(error); process.exitCode = 1; });
