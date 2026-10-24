# Day 08: Koan Garden

**Enter a statement or question; receive an original, koan-inspired passage and a possible reading to reflect on.**

A small, offline HTML/CSS/JavaScript project. It uses transparent English keyword rules and original writing templates, **not a language model**. AI assisted the coding; there is no runtime AI service. These invented passages are not traditional Zen koans, spiritual instruction, counselling or reliable decision advice.

## 1. Install and run

No packages, account, API key or build step. Use a current Chrome, Firefox, Safari or Edge browser.

- Open `index.html` in this folder by double-clicking it.
- Alternatively, from the repository root:

  ```sh
  cd day-08-koan-garden
  python3 -m http.server 8000 --bind 127.0.0.1
  ```

  Visit **http://127.0.0.1:8000**. On Windows use `py` instead of `python3`. Stop the server with Ctrl+C. Python is only needed for this optional server, not for generation.

The Markdown guide links may display as raw text or download when served by Python; read them in an editor or on GitHub for formatted documentation.

## 2. Use the garden

1. Type a question or statement, or choose an example to fill the form.
2. Select **Grow a koan**. Your words are hashed to select a scene from a finite, hand-written pool. The scene appears as an original three-line passage.
3. Read it before opening **Explore a possible meaning**.
4. Consider the suggested reading, three reflection questions, and a small practice. Disagreeing is allowed: there is no answer key.
5. **Another telling** asks the same input again within the same session. It returns the next unused composition from the selected motif, theme or fallback pool, until exhausted. Each submission or "another telling" uses the session's internal memory; it does not use an edited draft until you submit that draft.
6. **Clear** removes the input, output, and session memory from the page.

Tab/Shift+Tab move through controls; Enter/Space activate buttons or the reflection disclosure. Enter in the textarea creates a new line; use the submit button to generate. Focus moves to the passage heading after generation.

## 3. What "context" means here

The generator counts **distinct, whole-word English keyword matches** in seven themes: control, change, perfection, time, identity, relationships and uncertainty. The highest score wins; ties use their order in `koan.js`. With no match it chooses everyday attention.

**Scene selection:** A second set of whole-word rules looks for concrete imagery: sky/moon/stars (including a leaping cow), animals, water, paths/transport, work/craft and plants. If any motif matches, its three-scene pool takes priority over the abstract theme's imagery. Otherwise a matched theme supplies three scenes. If neither matches, the fallback pool contains all 18 motif scenes, rather than one repeated garden gate.

Each scene has its own interpretation, opening and narrative turn. Eight shared final reflection questions provide 24 compositions for a three-scene pool, or 144 for the fallback pool. The scenes and questions are finite: a new composition can reuse an image with a different ending. The meaning remains tied to the scene, not randomly mixed with an unrelated moral.

A stable 32-bit hash of the whole input selects a starting composition. Different inputs often start differently, but hashes and finite output pools can collide; hashing is variation, not understanding. A session-wide `Set` checks the actual rendered title and lines and skips anything already shown, even across different prompts. When that input's pool is exhausted, the app reports it rather than secretly repeating. It does not switch to unrelated imagery after exhaustion. Clear or reload starts a new session and permits repeats again.

**Your statement is not quoted in the title, passage or interpretation.** Input is retained in memory only to support another telling of the displayed subject; the seen-output history also lives only in memory.

Examples: `The cow jumped over the moon` selects sky imagery; `My bicycle` selects a journey scene. `Why must my work be perfect?` selects the perfection theme for reflection questions but work imagery for the passage. `Why must everything be perfect?` (without a concrete motif) uses perfection imagery such as a bowl, flute or unfinished circle.

Limitations matter:

- It does not understand grammar, intent, negation, metaphors, sarcasm or risk. "I do not need control" still matches control.
- No runtime language model. Variation comes from hash-based scene selection within a finite pool, not learned language patterns.
- Other languages and unlisted English synonyms can be entered, but usually receive the fallback scene.
- Each theme or motif pool holds three scenes; the fallback pool holds 18 scenes. Once a pool is exhausted for a session, a descriptive error appears asking you to start a new subject or clear the session.
- Maximum input: **600 UTF-16 code units** (JavaScript/HTML's counting convention). Some emoji use more than one unit. Whitespace-only input is rejected.
- Generated text can be awkward or inappropriate to your situation. Set it aside if it is not useful; the app does not assess your mental state or detect emergencies.

## 4. Privacy and safety

The app makes no API calls, loads no remote assets, uses no analytics and saves no entries persistently. It keeps the current input and seen-output history in memory until Clear or reload. Generation runs in memory in your browser. A local static server receives file requests, not the typed statement. Browser extensions, form restoration, shared devices and hosting-provider request logs are outside the app's control; avoid sensitive information on an untrusted device.

All rendered text uses `textContent`, never `innerHTML`. Pasted HTML remains inert in the textarea and is not echoed in the output. Clear removes displayed text, but is not a forensic erasure guarantee.

## 5. How the files fit together

| File | Job |
| --- | --- |
| `index.html` | Semantic form, result and native `<details>` disclosure |
| `style.css` | Responsive layout, reading typography, visible focus |
| `koan.js` | Pure model: validation, theme scoring and composition; browser global/CommonJS export |
| `app.js` | Browser-only events, safe rendering and small in-memory UI state |
| `tests/koan.test.cjs` | Node's built-in unit tests; no test packages |

Follow the [beginner code tour](LEARNING_GUIDE.md) and read [what koans are](ABOUT_KOANS.md).

## 6. Test

Install **Node.js 22+** for development tests, then from the repository root:

```sh
node --check day-08-koan-garden/koan.js
node --check day-08-koan-garden/app.js
node --test day-08-koan-garden/tests/koan.test.cjs
```

Manual checks: submit each example, open/close meaning with the keyboard, cycle through available tellings until the pool exhausts and an error appears, edit a draft without submitting, clear, submit spaces, paste `<img src=x onerror=alert(1)>` (it must not create an element or execute code), and try a narrow screen. Automated model tests do not prove accessibility across all browsers and assistive technologies.

## 7. References and licence

- [Britannica: koan](https://www.britannica.com/topic/koan) and [Stanford Encyclopedia of Philosophy: Japanese Zen](https://plato.stanford.edu/entries/japanese-zen/) — cultural context, not a template source.
- MDN: [forms](https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Forms), [`textContent`](https://developer.mozilla.org/en-US/docs/Web/API/Node/textContent), [`details`](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/details), [Unicode property escapes](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Regular_expressions/Unicode_character_class_escape).
- [Node test runner](https://nodejs.org/api/test.html).

Own code, writing ingredients and documentation are covered by the repository's [MIT licence](../LICENSE). No third-party text, traditional koan translations, libraries, fonts or images are bundled. Linked material retains its authors' rights. See [third-party notices](../THIRD_PARTY_NOTICES.md).
