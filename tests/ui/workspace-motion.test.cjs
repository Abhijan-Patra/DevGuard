// Real motion-controller lifecycle with a minimal canvas/observer environment.
// No model, privacy, clipboard or repair results are simulated here.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { resolve } = require('node:path');
const { runInNewContext } = require('node:vm');
const source = readFileSync(resolve(__dirname, '../../devguard/web/workspace-motion.js'), 'utf8');

function harness({ reduced = false, context = true } = {}) {
  const frames = new Map(), documentEvents = {}, mediaEvents = {};
  const observers = { resize: [], intersection: [], mutation: [] };
  let nextFrame = 0, now = 0, arcs = 0;
  const ctx = { setTransform() {}, clearRect() {}, beginPath() {}, fill() {},
    arc(x, y, radius) { assert.ok(Number.isFinite(x) && Number.isFinite(y) && radius > 0); arcs++; } };
  const buttons = [{ dataset: { action: 'motion' }, attributes: {},
    setAttribute(key, value) { this.attributes[key] = value; } }];
  const doc = { hidden: false, documentElement: { dataset: {} }, canvases: [],
    querySelectorAll(selector) { return selector.startsWith('canvas') ? this.canvases : buttons; },
    addEventListener(name, handler) { documentEvents[name] = handler; } };
  const canvas = (key = 'test') => ({
    dataset: { shieldField: key }, events: {},
    getContext() { return context ? ctx : null; },
    getBoundingClientRect() { return { width: 300, height: 260, left: 10, top: 20 }; },
    addEventListener(name, fn) { this.events[name] = fn; },
    removeEventListener(name) { delete this.events[name]; },
    removeAttribute(name) { if (name === 'data-ready') delete this.dataset.ready; },
    replaceWith(other) { doc.canvases[doc.canvases.indexOf(this)] = other; },
  });
  const media = { matches: reduced, addEventListener(name, handler) { mediaEvents[name] = handler; } };
  const win = { devicePixelRatio: 2,
    matchMedia(query) { return query.includes('reduced-motion') ? media : { matches: true }; } };
  const observer = (kind) => class {
    constructor(callback) { this.callback = callback; observers[kind].push(this); }
    observe() {} disconnect() { this.disconnected = true; }
  };
  runInNewContext(source, { window: win, document: doc,
    getComputedStyle: () => ({ getPropertyValue: () => '#8ce8c1' }),
    requestAnimationFrame(fn) { const id = ++nextFrame; frames.set(id, fn); return id; },
    cancelAnimationFrame(id) { frames.delete(id); },
    ResizeObserver: observer('resize'), IntersectionObserver: observer('intersection'), MutationObserver: observer('mutation'),
  });
  function flush(limit = 240) {
    let count = 0;
    while (frames.size && count++ < limit) {
      const batch = [...frames.values()]; frames.clear(); now += 16.667;
      for (const draw of batch) draw(now);
    }
    assert.equal(frames.size, 0, 'Decorative animation must settle instead of polling forever');
  }
  return { win, doc, canvas, frames, observers, buttons, documentEvents, media, mediaEvents, flush,
    get arcs() { return arcs; } };
}

test('shield draws finite geometry, settles, reacts to input and reuses its canvas across polling renders', () => {
  const h = harness(), first = h.canvas(); h.doc.canvases = [first];
  h.win.DevGuardMotion.sync(); h.flush();
  assert.equal(first.width, 600); assert.equal(first.dataset.ready, 'true'); assert.ok(h.arcs > 0);
  first.events.pointermove({ clientX: 150, clientY: 110 });
  first.events.pointerdown({ clientX: 150, clientY: 110 });
  first.events.pointerleave(); h.flush();
  h.doc.canvases = [h.canvas()]; h.win.DevGuardMotion.sync();
  assert.equal(h.doc.canvases[0], first);
  assert.equal(h.observers.resize.length, 1, 'Polling must not accumulate observers');
});

test('pause and OS reduced-motion changes stop movement and update controls', () => {
  const h = harness({ reduced: true }), first = h.canvas(); h.doc.canvases = [first];
  h.win.DevGuardMotion.sync(); h.flush(2);
  assert.equal(h.doc.documentElement.dataset.motion, 'off');
  assert.equal(h.buttons[0].disabled, true);
  first.events.pointermove({ clientX: 150, clientY: 110 }); assert.equal(h.frames.size, 0);
  h.media.matches = false; h.mediaEvents.change(); h.flush();
  assert.equal(h.doc.documentElement.dataset.motion, 'on');
  h.win.DevGuardMotion.toggle(); h.flush(2);
  assert.equal(h.doc.documentElement.dataset.motion, 'off');
  assert.equal(h.buttons[0].textContent, 'Enable motion');
});

test('hidden/offscreen fields stop frames; leaving the view removes listeners and observers', () => {
  const h = harness(), first = h.canvas(); h.doc.canvases = [first]; h.win.DevGuardMotion.sync();
  h.doc.hidden = true; h.documentEvents.visibilitychange(); assert.equal(h.frames.size, 0);
  h.doc.hidden = false; h.documentEvents.visibilitychange(); h.flush();
  first.events.pointerdown({ clientX: 150, clientY: 110 });
  h.observers.intersection[0].callback([{ isIntersecting: false }]); assert.equal(h.frames.size, 0);
  h.doc.canvases = []; h.win.DevGuardMotion.sync();
  assert.equal(Object.keys(first.events).length, 0);
  assert.equal(h.observers.resize[0].disconnected, true);
  assert.equal(h.observers.intersection[0].disconnected, true);
});

test('unavailable canvas retains static fallback without starting animation', () => {
  const h = harness({ context: false }), first = h.canvas(); h.doc.canvases = [first];
  assert.doesNotThrow(() => h.win.DevGuardMotion.sync());
  assert.equal(first.dataset.ready, undefined); assert.equal(h.frames.size, 0);
});
