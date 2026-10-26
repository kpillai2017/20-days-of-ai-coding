# Day 12 · Sort Lab

A visually guided tour of **nine familiar sorting algorithms**, made with only HTML, CSS and JavaScript. No framework, build step, account or API.

## Run

Open `index.html` directly in a current Chrome, Firefox, Safari or Edge browser. All scripts/styles are local. Alternatively, from the repository root:

```sh
cd day-12-sort-lab
python3 -m http.server 8000 --bind 127.0.0.1
```

Visit **http://127.0.0.1:8000**; Ctrl+C stops the server. Windows can use `py` instead of `python3`. Python is optional and only serves files. Markdown links may appear as raw text/downloads locally: read the guides on GitHub or in an editor for formatting.

## Controls

- **Algorithm:** bubble, selection, insertion, merge, quick, heap, Shell, counting or radix. Changes stop playback and restore the **same original input**.
- **Input pattern:** random, nearly sorted, reversed, already sorted or few unique values. Changing it makes new data.
- **Items:** 8–128; changing the slider creates new data and stops any old run.
- **Speed:** 1–300 yielded actions per second; adjusts during playback.
- **Start / Resume:** run from the current state. After completion, Run Again resets and sorts the same input.
- **Stop:** pause without losing progress. It does not reset.
- **Step:** perform one yielded action while stopped. A step may be a comparison, write, swap, buffer operation or explanatory milestone.
- **Reset:** restore the original input and clear counters without generating new numbers.
- **New data:** create another dataset using the current pattern and count.

Nothing starts automatically. Hidden tabs pause and require explicit resume. Buttons/selectors are native keyboard-accessible controls; Tab/Shift+Tab move focus, Enter/Space activate buttons, and arrow keys adjust sliders. The chart has a text description and expandable current-values list. It is not a full audio/screen-reader animation of every comparison.

Blue bars are not yet proven final; amber bars are active; green bars are **known final positions**, not merely a temporarily sorted prefix. During insertion/merge a main-array snapshot can temporarily contain duplicated values while a key/buffer holds the displaced value. The caption explains this; it is not a lost-data bug. Counting/radix display their original bars while auxiliary work happens, then visibly copy back.

## Understand the numbers

- **Key comparisons:** comparisons used to order values in comparison-based algorithms. Loop bounds, pivot/index checks and the maximum-key scan used by counting/radix are excluded. Counting/radix report zero here, not zero computational work.
- **Main writes:** assignments to the displayed array, including writing a saved key back into its original position. Swaps contribute two writes.
- **Swaps:** real exchanges of two distinct positions; self-swaps are skipped.
- **Aux writes:** explicit buffer/bucket writes, including bucket initialisation, counts, prefix sums and decrements. Scalar bookkeeping, returned event snapshots, copying the initial input and DOM work are excluded.
- **Steps shown:** yielded actions after the initial ready snapshot, including final completion. Faster playback may render several actions in one frame; Step reveals every event separately.

These are **teaching counters, not CPU instructions or wall-clock benchmarks**. The speed slider controls playback, not actual algorithm speed. The visualiser adds snapshot arrays, sets and DOM updates; listed space complexities describe the underlying algorithms, not the whole app. All algorithms sort ascending positive integers; public model input is 0–128 items valued 1–999. UI datasets use 1–100.

## Files and learning

| File | Responsibility |
| --- | --- |
| `algorithms.js` | Pure lazy generators, metadata, validation and data patterns; `SortLab` browser global/CommonJS export |
| `app.js` | DOM rendering, one animation clock, pause/reset state and event handling |
| `index.html` | Semantic controls, chart, metrics, teaching panel and text alternative |
| `style.css` | Responsive dark dashboard, visible focus and colour legend |
| `tests/algorithms.test.cjs` | Node's built-in model regression suite |

Read [nine algorithm explanations](ALGORITHMS.md) and the [beginner code walkthrough](LEARNING_GUIDE.md). Every algorithm/helper has explanatory comments; no native `Array.sort` implements the algorithms.

## Tests

Use Node.js **22+**, from the repository root:

```sh
node --check day-12-sort-lab/algorithms.js
node --check day-12-sort-lab/app.js
node --test day-12-sort-lab/tests/algorithms.test.cjs
```

Tests check sorted output, input nonmutation, event validity, final-position claims, counters, edge cases and seeded inputs for every algorithm. Manual/browser checks should exercise Start → Stop → Step → Resume, Reset, repeated Run Again, changing algorithm mid-run, changing size/pattern, hidden-tab pause, a narrow viewport and native keyboard focus.

## References and licence

- [OpenDSA sorting chapters](https://opendsa-server.cs.vt.edu/ODSA/Books/Everything/html/Sorting.html) — further learning.
- [Princeton Algorithms: sorting overview](https://algs4.cs.princeton.edu/20sorting/) — comparisons, stability and algorithm context.
- MDN: [generators](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/function*), [`yield*`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/yield*), [requestAnimationFrame](https://developer.mozilla.org/en-US/docs/Web/API/Window/requestAnimationFrame), [Page Visibility API](https://developer.mozilla.org/en-US/docs/Web/API/Page_Visibility_API), [textContent](https://developer.mozilla.org/en-US/docs/Web/API/Node/textContent).
- [Node test runner](https://nodejs.org/api/test.html).

Original AI-assisted source and educational prose use the repository [MIT licence](../LICENSE). No third-party libraries, fonts, images, article text or dataset files are bundled. Algorithms are standard techniques; implementations and explanations are written for this project rather than copied from the references. Linked publications retain their authors' rights; see [notices](../THIRD_PARTY_NOTICES.md). No entries are stored or uploaded; there are no external requests, analytics or runtime AI service.
