# Typing Sprint: follow one character through the app

Start with [setup and controls](README.md). This guide explains the ideas without assuming knowledge of timers or state machines.

## 1. A short reading route

1. Play once, deliberately type a mistake, then correct it.
2. Find the textarea's `id="typing-input"` in HTML and its cached reference in `app.js`.
3. Read `analyzeText()` in `sprint.js`. Trace three letters by hand.
4. Read `calculateStats()`, then the Session constructor, `update()` and `tick()`.
5. Follow the browser's input listener into `acceptInput()` and `render()`.
6. Read a test with an exact deadline. Notice that no real clock or browser is needed.

## 2. Start with plain data

An array of passage objects holds `id`, `title` and `text`. The title is the label you see; text is what you type; ID is a stable identifier. `Object.freeze()` prevents accidental edits to those shared records. Freezing an outer array alone wouldn't freeze its objects, so both levels are frozen.

The Session contains the current text and timestamps, not DOM elements. The UI renders it; the UI is not the source of truth for scoring.

## 3. Compare `cat` with `car`

A loop visits each input index:

| Index | Target | Entered | Match? |
| --- | --- | --- | --- |
| 0 | c | c | yes |
| 1 | a | a | yes |
| 2 | t | r | no |

Correct = 2, incorrect = 1, accuracy = `2 / 3 × 100`, about 66.67%. Backspace the r and the buffer becomes `ca`: two correct out of two means 100%, though the passage isn't complete. Type t and exact equality finishes it.

This isn't a history of mistakes. Once a wrong character is deleted, it no longer contributes to the current-buffer accuracy. Inserting x near the start shifts later positions; the algorithm does not realign words.

### Try a separate model experiment

Open Developer Tools → Console on the app page:

```js
TypingSprint.analyzeText("cat", "car");
TypingSprint.analyzeText("cat", "ca");
TypingSprint.calculateStats("abcde abcde", "abcde", 30_000);
```

The final result has five correct characters in half a minute: `(5 / 5) / 0.5 = 2 WPM`. These calls do not change the real attempt.

JavaScript string indexing counts UTF-16 units. A single emoji can count as two. Original passages use ASCII so visible characters and units agree; copying in Unicode passages needs a new metric decision, not just a different string.

## 4. Time is a subtraction, not a tick count

Suppose the first input is accepted at timestamp 1,000ms. At timestamp 11,000ms:

```text
elapsed = 11,000 - 1,000 = 10,000ms = 10 seconds
remaining = 60,000 - 10,000 = 50,000ms
```

`setInterval(refresh, 100)` asks the browser to call back periodically. It doesn't promise exactly 100ms gaps. Incrementing a counter by 100 on each callback would undercount time when callbacks are late.

Instead, the browser supplies `performance.now()`. The model subtracts the start timestamp. This monotonic page clock is preferred over assuming a wall clock never changes. Real sleep/platform behavior still varies, so don't treat the game as a laboratory benchmark.

### The late-callback example

Start at 1,000ms, so the deadline is 61,000ms. A sleeping/background callback doesn't run until 90,000ms. The model must finish at **61,000ms**, not 90,000ms. Otherwise the WPM denominator would incorrectly be 89 seconds.

Likewise, input at exactly 61,000ms is too late. `update()` calls `tick()` before accepting text, so an interval delayed by the browser doesn't create extra time.

## 5. A state machine is a small set of allowed situations

```text
ready → running → finished
```

- **Ready:** empty input; focusing/waiting doesn't start time.
- **Running:** started on the first nonempty committed input. Deleting back to empty doesn't undo the start.
- **Finished:** exact full match or deadline. Input and result metrics no longer change.

Restart creates a new ready Session. The model also exposes `reset()` for explicit reuse/tests. The UI disables passage choice while running to avoid scoring text against a changing target.

`null` marks a missing timestamp. Checking `if (startedAt)` would be wrong: 0 is a valid timestamp but is falsy. The model compares to `null` explicitly.

## 6. One input event end to end

1. Browser editing changes the textarea value. The `input` event handles typing, deletion, selection replacement and paste—not just key presses.
2. `acceptInput()` passes the whole current string and `performance.now()` to `session.update()`.
3. The session resolves expiry and decides whether to accept that string.
4. It returns a snapshot of state and metrics.
5. If text arrived too late, the UI restores the previously accepted string.
6. `render()` updates numbers. `drawPassage()` creates text spans with visual classes.
7. On finish, a polite status announcement and results appear. The typing field becomes read-only.

Composition events matter for input methods that build a character in several steps. Provisional text isn't scored; `compositionend` accepts committed text. If time is already running, composing doesn't pause it. The passage still uses ASCII and doesn't claim a grapheme-aware Unicode score.

## 7. Keep the DOM safe and quiet

`textContent` inserts literal text. `createElement()` supplies the markup structure. Avoid interpolating typed text into `innerHTML`; arbitrary strings must never become executable markup.

Hundreds of character spans would be awkward to read with a screen reader, so the visual passage is hidden from accessibility APIs and a whole-text alternative describes the input. Live timer numbers are not continuously announced. Only start/finish state changes use a live region.

A cached `lastRenderedInput` avoids rebuilding the passage on every timer callback. Time affects metrics, but character highlighting changes only when input changes. This is a small, explainable optimisation, not a general-purpose rendering framework.

## 8. Tests use pretend times, not pretend correctness

From the repository root:

```sh
node --test day-05-typing-sprint/tests/sprint.test.cjs
```

A test arranges a session, acts at exact timestamps, then asserts results:

```js
const session = new TypingSprint.Session("cat", 1000);
session.update("c", 100);        // Deadline is 1100.
const result = session.update("cat", 1100);
console.log(result.reason);     // "timeout", NOT "completed"
console.log(result.input);      // "c": the late edit was rejected.
console.log(result.elapsedMs);  // 1000, regardless of callback lateness.
```

Node's built-in runner and `node:assert/strict` need no package installation. Unit tests protect the model; the README's browser checklist covers focus, composition, read-only fields and mobile layout.

## 9. Small syntax glossary

| Syntax | Role here |
| --- | --- |
| `class Session` / `new Session(...)` | Define behavior and construct an independent attempt |
| `this.input` | Data on this particular session, not shared global data |
| `{ ...analysis, elapsedMs }` | New object with copied analysis fields and elapsed time |
| `===` | Strict equality: completion requires the exact full string |
| `Math.ceil()` | Round remaining seconds upward for display |
| `toFixed(1)` | Format one decimal place; returns text, not a number |
| `return` | Exit a function; guard clauses stop invalid/finished updates early |
| `throw` | Report invalid API input instead of guessing a result |
| IIFE | Immediately called function: hides helpers and UI variables |
| Snapshot | A newly calculated view of state, not a second mutable session |

## 10. Exercises with expected outcomes

1. **Predict a correction.** For target `hello`, entered `hez` has 2/3 correct. Backspace z: expect 100% current accuracy, but not completion. Elapsed time must continue.
2. **Try a five-second model session.** Construct `new Session("hello", 5000)`, start at 0, tick at 8000. Expect timeout and 5,000ms elapsed, never 8,000ms.
3. **Add an original passage.** Give it a unique ID/title and keep ASCII initially. Verify it appears in the selector and restart clears every metric. Don't paste copyrighted text without permission.
4. **Plan duration selection.** Decide whether it can change during a running attempt (recommend no), add tests for remaining time, then wire the UI. Don't change only the visible countdown label.

References and rights: see [the README's references and licence](README.md#references-and-licence) and [MIT licence](../LICENSE).
