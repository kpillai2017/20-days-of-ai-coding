# Day 05 · Typing Sprint

A 60-second typing practice in **HTML, CSS and JavaScript**. Choose an original passage, type it, correct mistakes, and see speed, accuracy and matching-character count.

No accounts, saved results, network requests, AI API, runtime libraries or build step. For a slower introduction, read [the beginner learning guide](LEARNING_GUIDE.md). Source comments explain the decisions next to the implementation.

## 1. Run

Open `day-05-typing-sprint/index.html` directly in a modern browser, keeping its CSS and JavaScript files beside it. Or, from the repository root:

```sh
cd day-05-typing-sprint
python3 -m http.server 8000 --bind 127.0.0.1
```

Windows: use `py` instead of `python3`. Visit **http://localhost:8000**. Ctrl+C stops the server. Python serves files; the browser runs the app. If 8000 is occupied, choose another port and change the URL accordingly.

Get the latest files using `git pull` in an existing clone or download/extract the repository ZIP. No `npm install` is needed. Node.js 20+ is optional for tests, not for playing.

## 2. Practice

1. Select one of three passages while ready.
2. Click or Tab to the labelled text field. Focus alone does not start the clock.
3. Your first nonempty **committed input** starts 60 seconds. Spaces count as input.
4. Green/underlined characters match; struck-through highlighted characters are wrong. The next character has a gold underline.
5. Backspace, selection and normal text editing remain available. Correcting a mistake improves current-text accuracy.
6. Finish by matching the whole passage exactly, or when time expires. A wrong full-length entry stays editable until timeout.
7. Read the result, then choose **Restart attempt** or another passage. Passage choice is disabled during an attempt.

The field is limited to the passage length. Pasting is intentionally allowed: this is a learning/practice tool, **not a verified typing benchmark**. Autocorrect/spelling hints are requested off, but browser/keyboard behavior can vary. Native input events are used rather than blocking keyboard keys. IME provisional text is not scored until committed; an already-running timer continues during composition.

No pause. Switching tabs does not stop time. Reload or Restart discards the attempt without confirmation. Nothing is stored or uploaded.

## 3. Exact scoring rules

Comparison is **position by position**, case-sensitive, including spaces and punctuation. With target `cat` and entered `car`, two characters match and one doesn't. Inserting a character shifts later positions; this is not edit-distance alignment.

- **Correct:** currently entered characters equal to the target at the same indexes.
- **Incorrect:** entered count minus correct count.
- **Accuracy:** `correct / entered × 100`. Empty input displays 100% by convention.
- **WPM:** `(correct / 5) / elapsedMinutes`. A typing word is five characters, not a dictionary word.
- **Zero elapsed:** display 0 WPM, not infinity. Pasting a complete passage as the first input can finish with zero elapsed time.

Example: 25 correct out of 30 entered in 30 seconds means **10 WPM**, about **83.33% accuracy**. Backspacing changes current entered/correct counts but does not reset elapsed time. We do not count historical keystrokes or corrected errors. Early live WPM may fluctuate strongly because elapsed time is tiny.

The supplied text is ASCII. JavaScript string length and indexing count UTF-16 code units; custom emoji/combined Unicode text would require a deliberate grapheme-aware redesign. Results are rounded for display only, not during calculation.

## 4. Files and architecture

```text
day-05-typing-sprint/
├── index.html            # Labelled controls, text field, metrics and results
├── style.css             # Responsive desk and character states
├── sprint.js             # Comparison, scoring and deterministic session model
├── app.js                # DOM, input events, browser clock and rendering
├── README.md
├── LEARNING_GUIDE.md
└── tests/
    └── sprint.test.cjs    # Node's built-in runner; no test dependencies
```

### `sprint.js`: rules without a browser

Exports `TypingSprint` globally for a classic browser script and through CommonJS for Node. The IIFE keeps internal helpers private.

| API | Purpose |
| --- | --- |
| `DURATION_MS` | Default 60,000 milliseconds |
| `PASSAGES` | Frozen array of three original `{id, title, text}` records |
| `analyzeText(target, input)` | Positional counts, accuracy and exact-match flag |
| `calculateStats(target, input, elapsedMs)` | Analysis plus WPM, elapsed and default-duration remaining time |
| `new Session(target, durationMs=60000)` | Ready/running/finished state machine |
| `session.update(input, now)` | Check deadline, then accept input if still active |
| `session.tick(now)` | Check expiry without a text edit |
| `session.snapshot(now)` | Read metrics without resolving expiry or mutating state |
| `session.reset()` | Clear text, timestamps, status and clock history |

`Session` adjusts remaining time to its own duration; standalone `calculateStats` uses the default. Timestamps must be finite nonnegative milliseconds and must not move backward relative to the last update/tick. Model fields are public for learning: the UI treats them as read-only and changes state through methods.

```text
ready --first nonempty input--> running --exact match--> finished/completed
                                  |
                                  +--deadline reached--> finished/timeout

Restart creates a new ready Session for the selected passage.
```

The deadline is checked **before** accepting a text edit. Input arriving at or after it is ignored. Timeout finish time is exactly `startedAt + durationMs`, even if a delayed callback arrives much later. Finished results stay unchanged on later ticks/edits. `snapshot()` can report a clamped elapsed time while state still says running; callers must use `tick()` to resolve expiry.

### `app.js`: connect input, time and view

- `restart()` creates a model, clears input/results, and restores the passage.
- `acceptInput()` passes the textarea value and `performance.now()` to the model. It restores the last accepted text if a late edit was rejected.
- `drawPassage()` safely builds text spans, with correct/wrong/current classes. It only rebuilds when input changes.
- `render()` updates rounded metrics and accessible start/finish announcements.
- `refresh()` resolves elapsed time through `tick()` every 100ms and on visibility changes.

The 100ms interval is **not the clock**. Browsers delay callbacks, especially in background tabs. `performance.now()` is monotonic within this page; subtracting the recorded start measures elapsed time without assuming each callback arrived punctually. Processing input also checks the deadline, so a delayed interval cannot grant extra typing time. Browser/platform sleep behavior can vary; this isn't a certified timing instrument.

The passage uses safe `textContent`, not interpreted HTML. A plain-text accessible passage accompanies the visual per-character spans. Timer metrics are not a noisy live region; state changes are announced politely. At finish, results receive focus only if the input was focused and the page is visible. No global keyboard shortcuts steal normal editing keys.

## 5. Tests

From the repository root:

```sh
node --check day-05-typing-sprint/sprint.js
node --check day-05-typing-sprint/app.js
node --test day-05-typing-sprint/tests/sprint.test.cjs
```

From this project folder: `node --test tests/sprint.test.cjs`. Tests use supplied timestamps, not real 60-second waits. They cover correction, punctuation/spacing, validation, exact deadline, delayed callbacks, zero-time completion, custom durations, reset and immutable final results. CI runs them alongside earlier projects.

### Browser checklist

1. Focus the input and wait: ready stays at 60 seconds.
2. Type a wrong character then correct it with Backspace; accuracy recovers and time keeps running.
3. Match a full passage exactly; results appear and further edits are blocked.
4. Wait for timeout; results show 60 seconds and accepted text stops changing.
5. Restart; metrics, input, highlights, results and passage-choice state reset.
6. Select another passage while ready/finished and verify the displayed text changes.
7. Switch tabs during an active attempt, return after a minute: the session expires, not resumes.
8. Use keyboard-only navigation and a narrow/mobile viewport. Results should fit and the typing field should remain usable.

## 6. Troubleshooting and exercises

- **Nothing happens:** enable JavaScript, keep files together, inspect Developer Tools → Console.
- **Cannot edit:** a finished attempt is read-only; click Restart.
- **WPM seems high at first:** the first few milliseconds form a tiny denominator. Final results are more meaningful; pasting is allowed and not a valid speed measurement.
- **Accuracy differs from another typing site:** metric definitions differ. Ours measures the current buffer, not all historical errors.
- **Timer jumps after switching tabs:** expected; elapsed time continued while callbacks were throttled.

Try adding another original passage, a configurable practice duration, or a history of results. Decide scoring/storage behavior and add tests before changing the interface. If adding Unicode passages, first decide whether a “character” means code unit, code point or grapheme cluster.

## References and licence

Original implementation and practice passages created with AI coding assistance. No third-party text excerpts, libraries, assets, fonts or analytics are bundled.

- [MDN: input event](https://developer.mozilla.org/en-US/docs/Web/API/Element/input_event)
- [MDN: performance.now](https://developer.mozilla.org/en-US/docs/Web/API/Performance/now)
- [MDN: setInterval](https://developer.mozilla.org/en-US/docs/Web/API/Window/setInterval)
- [MDN: composition events](https://developer.mozilla.org/en-US/docs/Web/API/Element/compositionend_event)
- [MDN: textContent](https://developer.mozilla.org/en-US/docs/Web/API/Node/textContent)
- [Node.js test runner](https://nodejs.org/api/test.html)

Own code, passages and documentation: [MIT licence](../LICENSE). Linked material retains its authors' rights; see [third-party notices](../THIRD_PARTY_NOTICES.md).
