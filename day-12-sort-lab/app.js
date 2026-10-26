/* VIEW / CONTROLLER. Algorithms know nothing about DOM elements or clocks.
 * Playback consumes a lazy iterator, avoiding a huge precomputed event history.
 * A single requestAnimationFrame loop owns time; repeated Start cannot create
 * competing timers. Every function below explains its part of that contract. */
(() => {
  'use strict';
  const model = globalThis.SortLab;
  const $ = id => document.getElementById(id);
  const algorithm = $('algorithm');
  const chart = $('chart');
  let original = [];
  let iterator = null;
  let current = null;
  let running = false;
  let complete = false;
  let shown = 0;
  let budget = 0;
  let previousTime = null;
  let bars = [];

  /** A short status announces actions, not all 300 possible steps each second. */
  function announce(text) { $('status').textContent = text; }

  /** Populate the selector using safe DOM APIs, not string-built HTML. */
  function populateAlgorithms() {
    for (const [id, data] of Object.entries(model.ALGORITHMS)) {
      const option = document.createElement('option');
      option.value = id; option.textContent = data.name;
      algorithm.append(option);
    }
  }

  /** Present complexity alongside the exact variant this program implements. */
  function lesson() {
    const data = model.ALGORITHMS[algorithm.value];
    $('chart-title').textContent = data.name;
    $('lesson-title').textContent = data.name;
    $('description').textContent = data.description;
    $('explanation').textContent = data.explanation;
    $('complexity').replaceChildren();
    for (const [label, value] of [['Best', data.best], ['Average', data.average], ['Worst', data.worst], ['Extra algorithm space', data.space], ['Stable variant', data.stable ? 'Yes' : 'No']]) {
      const dt = document.createElement('dt'), dd = document.createElement('dd');
      dt.textContent = label; dd.textContent = value;
      $('complexity').append(dt, dd);
    }
    $('code').replaceChildren(...data.steps.map(text => {
      const li = document.createElement('li'); li.textContent = text; return li;
    }));
  }

  /** Create DOM bars once per input change; subsequent frames reuse them. */
  function buildBars() {
    bars = original.map(() => {
      const bar = document.createElement('div');
      bar.className = 'bar'; bar.setAttribute('aria-hidden', 'true');
      bar.append(document.createElement('span'));
      return bar;
    });
    chart.replaceChildren(...bars);
  }

  /** Draw one immutable snapshot. Scaling uses the ORIGINAL maximum: copying
   * values during insertion can temporarily hide a maximum in a saved key. */
  function render() {
    const active = new Set(current.active), sorted = new Set(current.sorted);
    const maximum = Math.max(...original, 1);
    current.values.forEach((value, i) => {
      bars[i].style.height = `${Math.max(1, value / maximum * 95)}%`;
      bars[i].className = `bar${sorted.has(i) ? ' sorted' : active.has(i) ? ' active' : ''}`;
      bars[i].firstChild.textContent = original.length <= 24 ? value : '';
      bars[i].title = `Position ${i + 1}: ${value}`;
    });
    for (const [id, field] of [['comparisons','comparisons'],['writes','writes'],['swaps','swaps'],['aux','auxWrites']]) $(id).textContent = current[field].toLocaleString();
    $('steps').textContent = shown.toLocaleString();
    $('note').textContent = current.note;
    $('values').textContent = current.values.join(', ');
    chart.setAttribute('aria-label', `${model.ALGORITHMS[algorithm.value].name}, ${original.length} values. ${current.note}`);
    [...$('code').children].forEach((li,i) => li.classList.toggle('current', !complete && i === current.line));
    $('state').textContent = complete ? 'Complete' : running ? 'Running' : shown ? 'Stopped' : 'Ready';
    $('start').textContent = complete ? 'Run again' : shown ? 'Resume' : 'Start';
    $('start').disabled = running;
    $('stop').disabled = !running;
    $('step').disabled = running || complete;
  }

  /** Reset abandons the old generator and restores the SAME starting array. */
  function reset() {
    running = false; complete = false; shown = 0; budget = 0;
    iterator = model.createStepper(algorithm.value, original);
    current = iterator.next().value; // Initial event is a ready snapshot.
    render();
  }

  /** Data changes are explicit and interrupt old playback without stale work. */
  function newData() {
    original = model.createData(Number($('count').value), $('pattern').value);
    $('count-label').value = String(original.length);
    buildBars(); reset(); announce('New input ready.');
  }

  /** Advance exactly one yielded action; finishing never creates an extra sort. */
  function advance() {
    if (complete) return;
    const next = iterator.next();
    if (next.done) {
      complete = true; running = false;
      return;
    }
    current = next.value; shown++;
    if (current.done) {
      complete = true; running = false; budget = 0;
      announce(`${model.ALGORITHMS[algorithm.value].name} finished.`);
    }
  }

  /** Accumulate fractions of an action. Bound dt and per-frame work so a tab
   * returning from sleep cannot fast-forward thousands of invisible steps. */
  function frame(time) {
    const dt = previousTime === null ? 0 : Math.min((time - previousTime) / 1000, .1);
    previousTime = time;
    if (running) {
      budget += dt * Number($('speed').value);
      let consumed = 0;
      while (budget >= 1 && running && consumed < 30) {
        advance(); budget = Math.max(0, budget - 1); consumed++;
      }
      if (consumed) render();
    }
    requestAnimationFrame(frame);
  }

  $('start').addEventListener('click', () => {
    if (complete) reset();
    running = true; budget = 0; previousTime = null;
    render(); announce('Playback started.');
  });
  $('stop').addEventListener('click', () => {
    running = false; budget = 0; render(); announce('Stopped. Resume or Step to continue.');
  });
  $('step').addEventListener('click', () => { advance(); render(); });
  $('reset').addEventListener('click', () => { reset(); announce('Restored the same original input.'); });
  $('shuffle').addEventListener('click', newData);
  algorithm.addEventListener('change', () => { lesson(); reset(); announce('Algorithm changed; original input preserved.'); });
  $('pattern').addEventListener('change', newData);
  $('count').addEventListener('input', newData);
  $('speed').addEventListener('input', () => { $('speed-label').value = `${$('speed').value} steps/s`; });
  document.addEventListener('visibilitychange', () => {
    if (document.hidden && running) {
      running = false; budget = 0; render(); announce('Paused while this tab was hidden.');
    }
    previousTime = null;
  });

  populateAlgorithms(); lesson(); newData();
  // Motion never starts automatically, including for reduced-motion readers.
  requestAnimationFrame(frame);
})();
