# A beginner's code tour: Koan Garden

You need only a browser to use the app. To learn the code, open these files in an editor and keep the browser alongside. No framework, bundler, package manager or API key hides the basic operations.

## 1. The whole journey

```text
textarea → submit event → validate → split into words
         → score themes → hash input for scene offset
         → select 3-scene pool (or fallback) → fetch next unused scene
         → compose three lines + scene interpretation → render safe text
                                                       ↓
                                         optional meaning disclosure
```

HTML describes the page's structure, CSS styles it, and JavaScript changes it in response to events. The browser already knows how to draw a textarea and operate a `<details>` disclosure. We do not have to rebuild them.

## 2. Model versus interface

`koan.js` is the **model**: data and writing rules. It never reads an HTML element. `app.js` is the **view/controller**: it reads the form, calls the model, and renders the result.

Why separate them? A test can ask the model for a passage without launching a browser. Changing the colours won't change generation. Replacing the interface need not rewrite the theme rules.

Both scripts use an immediately invoked function expression:

```js
(() => {
  "use strict";
  // Local variables do not spill into other scripts.
})();
```

The model exposes just a small frozen API. In a browser it becomes `globalThis.KoanGarden`; in Node it becomes `module.exports`. `app.js` is browser-only, not a CommonJS module. Script tags use `defer` so HTML exists before the code reads it, and the model loads before the app.

## 3. Data before algorithms

`THEMES` records contain English keywords, an original image and reflection ingredients. `EXTRA_SCENES` supplies two further scenes per abstract theme. `MOTIFS` contains six concrete vocabulary families, each with three scenes. These are original passages, not copied koans.

A `scene(...)` helper groups a title, opening, narrative turn and interpretation. Keeping them together prevents an unrelated interpretation from being attached to an image. `ENDINGS` contains eight shared final questions, not eight different interpretations. The opening and turn become the first two lines; a selected question becomes the third.

Arrays preserve order; objects group named fields. Theme and motif matching both use strict greater-than scoring, so the earlier record wins a tie. Motif imagery takes priority when present; otherwise a matched theme supplies imagery. With neither, all 18 motif scenes form a varied fallback. Exhaustion does not switch to another pool.

## 4. Validate and normalise

`normalizeInput(value)` requires a string, rejects more than 600 UTF-16 units, collapses whitespace and rejects an empty result. The HTML also sets `required` and `maxlength`, but a caller can bypass a form. Validation belongs at the model boundary too.

`/\s+/gu` is a regular expression matching runs of whitespace. `replace(..., " ")` turns them into one space; `trim()` removes leading/trailing whitespace. This prevents a pasted paragraph's line breaks from changing the story's layout.

JavaScript counts string **code units**, not visible symbols. A basic English letter usually takes one unit, many emoji take two, and combined emoji can take more. The counter deliberately follows the textarea's native limit rather than pretending to count all human-perceived characters.

## 5. Match words, not meaning

`selectTheme(context)` lowercases the text and extracts runs of Unicode letters/numbers. A `Set` keeps each token once. Theme scores count distinct vocabulary words present in that set.

Work through it:

```text
"Perfect plans need a perfect outcome."
→ perfect, plans, need, a, outcome
→ control: plans + outcome = 2
→ perfection: perfect = 1 (not 2)
→ choose control
```

A strict `score > bestScore` means ties do not replace the earlier winner. If every score is zero, everyday attention remains selected.

Whole words avoid `time` matching `sometimes`. They do not solve language understanding: `I do not want control` still matches control. Other languages are accepted as text but do not receive semantic translation. There is no hidden model, emotion analysis or emergency detection.

## 6. Compose the result

`generate(input, variant=0)` validates, scores themes, chooses an imagery pool and hashes the whole input into a starting offset. The offset selects a scene and one of eight ending questions. The result has three lines, that scene's interpretation, three reflection questions and a practice. Input is kept in the returned `context` field for the controller, but never quoted in the title, poem or interpretation.

The hash uses XOR, `Math.imul` and an unsigned shift to accumulate a 32-bit value. This is a compact deterministic selector, not encryption or language understanding. Different strings can collide, and punctuation-only changes need not produce different output.

`variantCount = pool.scenes.length * ENDINGS.length`. Modulo wraps within this finite pool. The scene index changes before the ending index, so successive variants visit all scenes before reusing one with another final question. Reduce the safe-integer variant before adding the offset, avoiding precision loss.

This composition function is pure: the same input and variant return equivalent results. The browser needs freshness, so state lives separately in `createSession()`:

```js
const session = KoanGarden.createSession();
const first = session.next("The cow jumped over the moon");
const next = session.next("The cow jumped over the moon");
// first and next have different rendered passages.
session.clear(); // Explicitly allow old results again.
```

A `Set` stores serialised title-and-lines signatures, not just numeric scene IDs. `next(input)` scans the input's entire candidate pool and returns the first signature not seen in this session. It marks the signature only when returning a result. This prevents exact repeats across different inputs too. Exhaustion throws a descriptive error rather than looping forever or quietly repeating. The finite pool cannot provide unlimited new imagery: later compositions reuse scenes with different ending questions.

## 7. Events and little bits of state

`app.js` creates ONE `session` for the page. Both form submission and **Another telling** call `session.next(input)`; submitting again does not reset history. `generatedContext` remembers the last successful submitted input separately from the editable draft. Editing a draft affects only the next submission, not Another telling.

`preventDefault()` stops form navigation. `try/catch` displays validation or exhaustion errors without replacing the previous valid passage. Example buttons fill but do not submit. Clear empties the visible text, calls `session.clear()` and forgets the current subject. Reload also resets memory; no `localStorage` is used.

## 8. Render safely and accessibly

`document.createElement("p")` makes an element. Assigning `p.textContent = line` inserts literal text. `replaceChildren(...paragraphs)` replaces the old output; `...` spreads an array into separate arguments.

Never put untrusted input into `innerHTML`. For example, `<img src=x onerror=alert(1)>` must remain inert in the textarea and must not become an executable image element. Keeping the generator offline does not make unsafe DOM operations harmless.

Native `<details>` and `<summary>` provide a disclosure control. Each new telling starts closed. The generated heading has `tabindex="-1"`, which allows JavaScript to focus it without adding it to normal tab order. A short live status announces completion without turning the whole passage into an overly long live region.

The CSS has visible keyboard outlines, wrapping layouts, system fonts, and only an optional colour transition. `prefers-reduced-motion` avoids that transition for users who request less motion. These choices help accessibility; they are not a substitute for real assistive-technology testing.

## 9. Test without a browser

Run from the repository root with Node.js 22+:

```sh
node --test day-08-koan-garden/tests/koan.test.cjs
```

Node's `test` defines cases; `assert` checks expectations. Tests cover valid/invalid inputs, every theme, fallback, tie-breaking, distinct matches, Unicode, variants, deterministic output and mutation isolation. Browser behaviour still needs browser tests: Node cannot tell whether focus is visible or mobile text is readable.

## 10. Experiments and novice walkthrough

**Understanding the system:**

1. Try `sometimes` and `time`. Explain why only one selects the time theme.
2. Try a sentence with negation. Find the limit of the matching rule.
3. Submit the same input twice. The session should show different passages even though the pure function is deterministic.
4. In Node, call `generate("moon", 0)` twice and compare the results. Explain the distinction between pure composition and session state.
5. Click Another telling until exhaustion. Some images return with new final questions, but no exact rendered passage should repeat.
6. Add a keyword and write a regression test for it.
7. Add a scene with its own interpretation; observe that `variantCount` increases automatically by eight for that pool.
8. Compare `My work must be perfect` with `Everything must be perfect`. Identify why the imagery pools differ.
9. Clear and resubmit an old input; explain why repeats are now permitted.
10. Inspect `createSession()` and trace how a Set prevents a collision across different prompts.

## References

See [README](README.md#7-references-and-licence) for MDN, Node and licensing links, and [About koans](ABOUT_KOANS.md) for historical context. Rule-based generation is a useful small programming exercise, not a substitute for cultural understanding or language comprehension.
