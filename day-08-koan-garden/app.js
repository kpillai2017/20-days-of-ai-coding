/* The VIEW/CONTROLLER: connect DOM events to the pure model in koan.js.
 * All user content goes through textContent, NEVER innerHTML. Text that looks
 * like HTML must remain text, not become executable markup. */
(() => {
  "use strict";
  const model = globalThis.KoanGarden;
  const byId = id => document.getElementById(id);
  const form = byId("koan-form");
  const input = byId("context");
  const result = byId("result");
  const error = byId("error");
  const status = byId("status");

  // Keep the generated input separate from the editable draft. 'Another telling'
  // belongs to the displayed story, even if someone has begun typing a new one.
  let generatedContext = null;
  const session = model.createSession(); // Shared by submit AND Another telling.

  function updateCounter() {
    byId("counter").textContent = `${input.value.length} / ${model.MAX_LENGTH}`;
    error.textContent = "";
    input.removeAttribute("aria-invalid");
  }

  function render(story) {
    byId("theme").textContent = story.themeName;
    byId("koan-title").textContent = story.title;
    // replaceChildren removes the PREVIOUS story rather than appending to it.
    const paragraphs = story.lines.map(line => {
      const p = document.createElement("p");
      p.textContent = line;
      return p;
    });
    byId("passage").replaceChildren(...paragraphs);
    byId("reading").textContent = story.reading;
    byId("practice").textContent = story.practice;
    byId("questions").replaceChildren(...story.questions.map(question => {
      const li = document.createElement("li");
      li.textContent = question;
      return li;
    }));
    byId("matching-note").textContent = story.motif
      ? `Imagery: ${story.motif}. Chosen by vocabulary rules—not language understanding.`
      : story.matched
        ? "Theme chosen using English keywords—not an assessment of you."
        : "No vocabulary rule matched; imagery is varied from the whole input, not interpreted semantically.";
    byId("variation").textContent = `A fresh telling from a finite pool of ${story.variantCount} compositions for this subject. Clear starts a new session.`;
    // Start each telling closed: let readers meet the image before the gloss.
    byId("reflection").open = false;
    result.hidden = false;
    status.textContent = "Your passage is ready. Reflect first, then explore a possible meaning.";
    byId("koan-title").focus();
  }

  form.addEventListener("submit", event => {
    event.preventDefault(); // Stay on this page; do not send the form anywhere.
    try {
      const story = session.next(input.value);
      generatedContext = story.context;
      error.textContent = "";
      input.removeAttribute("aria-invalid");
      render(story);
    } catch (problem) {
      error.textContent = problem.message;
      input.setAttribute("aria-invalid", "true");
      input.focus();
    }
  });

  byId("another").addEventListener("click", () => {
    if (generatedContext === null) return;
    try {
      render(session.next(generatedContext));
      error.textContent = "";
    } catch (problem) {
      // Keep the previous passage visible and report pool exhaustion honestly.
      error.textContent = problem.message;
      status.textContent = problem.message;
    }
  });

  document.querySelectorAll("[data-example]").forEach(button => {
    button.addEventListener("click", () => {
      input.value = button.dataset.example;
      updateCounter();
      input.focus(); // Filling an example doesn't submit without your choice.
    });
  });

  byId("clear").addEventListener("click", () => {
    input.value = "";
    generatedContext = null;
    session.clear();
    result.hidden = true;
    // Remove text from the DOM too, not merely from view. No localStorage or
    // history is used; the browser itself may still manage form restoration.
    ["passage", "reading", "practice", "questions", "koan-title", "theme", "matching-note", "variation"].forEach(id => byId(id).replaceChildren());
    byId("reflection").open = false;
    updateCounter();
    status.textContent = "Cleared. Nothing has been saved by this app.";
    input.focus();
  });

  input.addEventListener("input", updateCounter);
  updateCounter(); // Also handle a browser-restored form value on initial load.
})();
