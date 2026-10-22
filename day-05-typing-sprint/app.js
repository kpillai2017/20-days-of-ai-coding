/* The UI translates browser events into model updates. It never invents its
   own scoring formula: every displayed metric comes from the same Session. */
(() => {
  "use strict";
  const { PASSAGES, Session } = globalThis.TypingSprint;
  // Cache stable DOM nodes. Only passage children are rebuilt during typing.
  const choice = document.getElementById("passage-choice");
  const input = document.getElementById("typing-input");
  const passage = document.getElementById("passage");
  const readable = document.getElementById("passage-readable");
  const time = document.getElementById("time");
  const wpm = document.getElementById("wpm");
  const accuracy = document.getElementById("accuracy");
  const correct = document.getElementById("correct");
  const status = document.getElementById("status");
  const results = document.getElementById("results");
  const resultsTitle = document.getElementById("results-title");
  let session;
  let composing = false;
  let lastRenderedInput = null;
  let finishAnnounced = false;

  PASSAGES.forEach(item => {
    const option = document.createElement("option");
    option.value = item.id;
    option.textContent = item.title;
    choice.append(option);
  });

  function drawPassage(snapshot) {
    // Avoid rebuilding hundreds of spans every timer tick. A new input value
    // changes highlighting; time passing by itself does not.
    if (lastRenderedInput === snapshot.input) return;
    lastRenderedInput = snapshot.input;
    const fragment = document.createDocumentFragment();
    for (let index = 0; index < session.target.length; index++) {
      const span = document.createElement("span");
      span.textContent = session.target[index]; // Text, never interpreted HTML.
      if (index < snapshot.input.length) {
        span.className = snapshot.input[index] === session.target[index] ? "correct" : "incorrect";
      } else if (index === snapshot.input.length) {
        span.className = "current";
      }
      fragment.append(span);
    }
    passage.replaceChildren(fragment);
  }

  function render(snapshot) {
    drawPassage(snapshot);
    // ceil means 59.9 seconds remaining is still displayed as 60, not 59.
    // Only display rounding occurs here; all calculations retain precision.
    time.textContent = `${Math.ceil(snapshot.remainingMs / 1000)}s`;
    wpm.textContent = snapshot.wpm.toFixed(1);
    accuracy.textContent = `${snapshot.accuracy.toFixed(1)}%`;
    correct.textContent = `${snapshot.correct}/${session.target.length}`;
    choice.disabled = snapshot.state === "running";
    input.readOnly = snapshot.state === "finished";
    if (snapshot.state === "ready") {
      status.textContent = "Ready. Type your first character to begin.";
    } else if (snapshot.state === "running" && status.textContent !== "Running. Keep a steady rhythm.") {
      // Don't announce the timer every 100ms: live regions would be unusable.
      status.textContent = "Running. Keep a steady rhythm.";
    }
    if (snapshot.state === "finished") {
      results.hidden = false;
      resultsTitle.textContent = snapshot.reason === "timeout" ? "Time is up" : "Passage complete";
      document.getElementById("result-summary").textContent = `${snapshot.wpm.toFixed(1)} WPM · ${snapshot.accuracy.toFixed(1)}% accuracy · ${snapshot.correct} correct characters`;
      document.getElementById("result-detail").textContent = `${(snapshot.elapsedMs / 1000).toFixed(2)} seconds elapsed. ${snapshot.incorrect} currently incorrect characters out of ${snapshot.typed} entered. Restart to try again.`;
      if (!finishAnnounced) {
        finishAnnounced = true;
        status.textContent = `${resultsTitle.textContent}. Results are below. Restart to practice again.`;
        // Do not steal focus if the user switched tabs or is using a control.
        if (document.activeElement === input && !document.hidden) resultsTitle.focus();
      }
    }
  }

  function restart(focus = true) {
    const selected = PASSAGES.find(item => item.id === choice.value) || PASSAGES[0];
    session = new Session(selected.text);
    composing = false;
    lastRenderedInput = null;
    finishAnnounced = false;
    input.value = "";
    input.readOnly = false;
    // UI limit matches the ASCII passage length; wrong full-length text remains
    // editable. The pure model also handles extra input for defensive testing.
    input.maxLength = selected.text.length;
    readable.textContent = `Practice passage: ${selected.text}`;
    results.hidden = true;
    render(session.snapshot(performance.now()));
    if (focus) input.focus();
  }

  function acceptInput() {
    const snapshot = session.update(input.value, performance.now());
    // An input event can arrive after the deadline before the timer callback.
    // The model rejects that late edit, so restore its accepted text to the UI.
    if (snapshot.state === "finished") input.value = snapshot.input;
    render(snapshot);
  }
  input.addEventListener("input", event => {
    // IME composition creates provisional text. Don't score incomplete syllables
    // or reset the clock. The committed value is handled on compositionend.
    if (!composing && !event.isComposing) acceptInput();
  });
  input.addEventListener("compositionstart", () => { composing = true; });
  input.addEventListener("compositionend", () => { composing = false; acceptInput(); });
  document.getElementById("restart").addEventListener("click", () => restart());
  choice.addEventListener("change", () => restart());

  function refresh() {
    const snapshot = session.tick(performance.now());
    if (snapshot.state === "finished") input.value = snapshot.input;
    render(snapshot);
  }
  // Intervals are repaint opportunities, NOT a clock. Background tabs throttle
  // callbacks; elapsed time is always now - startedAt, never 'ticks counted'.
  window.setInterval(refresh, 100);
  document.addEventListener("visibilitychange", refresh);
  restart(false);
})();
