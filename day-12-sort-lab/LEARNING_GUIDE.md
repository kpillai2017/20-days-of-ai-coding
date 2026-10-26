# Beginner code tour: pause a sorting algorithm

No framework is necessary to connect data, a few controls and a picture. Read this alongside the copiously commented source. The model is separate from the browser so tests can run without drawing a single bar.

## 1. The three layers

```text
algorithms.js: input → lazy action snapshots
app.js:        user controls + one clock → consume snapshots → update DOM
HTML/CSS:      semantic controls + readable bars/panels
```

A **pure model** does not query elements, create timers or decide animation speed. A **controller** decides when to ask for another step. The **view** displays the latest state. Separating them keeps a Reset button from needing to know how heap sort works.

`algorithms.js` uses a function wrapper to keep helper names private. Browser code sees `globalThis.SortLab`; Node tests use `module.exports`. `defer` script tags preserve loading order and wait until the HTML has been parsed. There is no module server or build requirement, so a file URL works.

## 2. Arrays, indexes and immutable snapshots

An array is an ordered collection. Indexes start at zero, while captions say “position 1” for the first value. `.slice()` copies an array. It does not give the caller permission to modify the algorithm's private working state.

The event factory returns fresh `values`, `active` and `sorted` arrays plus counters and a caption. If all events shared the same array reference, reading an older event later would show the final array instead of its original state. Copying is necessary for honest snapshots, but adds real memory/time overhead not included in textbook sort complexity.

`fixed` is a Set of indexes proven final. A quick-sort pivot and extracted heap suffix are final; an insertion prefix is only internally sorted and might still move. Green must mean the same thing across algorithms.

## 3. A generator is a function you can pause

```js
function* count() {
  yield 1;
  yield 2;
}
const iterator = count();
iterator.next(); // { value: 1, done: false }
iterator.next(); // { value: 2, done: false }
iterator.next(); // { value: undefined, done: true }
```

The star makes a generator. Calling it returns an iterator without running its body immediately. `next()` resumes until the next `yield`. Local variables and loop positions survive the pause.

`yield*` delegates to another generator. Sorting uses `yield* compare(...)`, `yield* swap(...)` and `yield* write(...)`, sharing the event/counter helpers without duplicate code. `compare` yields its snapshot, then returns a numeric difference when resumed. The sorting loop can use that returned difference in an `if`.

There are **two done flags**: the iterator's `next().done` means it has no more yields; the final **event's** `done=true` is a visible completion snapshot. The controller receives and renders that event before the iterator would finish.

## 4. Counters need a written definition

The model counts ordering comparisons, actual main-array assignments, swaps and explicit auxiliary writes. Index tests and scalar bookkeeping are excluded. A real swap adds two writes, but a skipped self-swap adds none. Insertion's final key assignment counts even if the key stays where it began.

Counting/radix use a key-digit function and buffers. Bucket zero-fills, increments, prefix-sum assignments, decrements and output placements count as auxiliary writes. `Math.max` finds the key range, but the educational key-comparison counter excludes that scan. Zero comparisons therefore does not mean zero work.

Event snapshots and the initial input copy are excluded from counters. The README defines this precisely so numbers cannot be mistaken for instructions, benchmark results or fair CPU timing comparisons.

## 5. Validate before starting

`createStepper` validates the algorithm ID and input immediately, then returns `run(id, copiedInput)`. This wrapper matters because validation inside a generator would not execute until its first `next()`.

Inputs must be arrays of up to 128 positive integer values from 1 through 999. Zero, booleans, fractions and nonfinite values are rejected. UI generation permits 8–128 items and values 1–100. Test-only empty/single inputs still exercise base cases correctly.

Data patterns are simple constructions, not imported datasets. Nearly-sorted starts ascending and swaps some neighbours; repeated swaps can cancel. Few-unique samples from five fixed keys. A custom RNG must return a finite number in `[0,1)`, giving deterministic tests without hidden global random state.

## 6. One clock, no competing timers

`requestAnimationFrame(frame)` requests a callback before a browser repaint. One callback schedules the next one. Start changes `running`, not the number of timers; repeatedly starting cannot create multiple simultaneous sorts.

```text
budget += elapsed_seconds × requested_steps_per_second
while budget >= 1:
    consume one event
    budget -= 1
```

Fractions accumulate, so a low speed does not round down to zero progress. Each frame's accepted time is capped at 0.1 second and work at 30 actions. Returning from a sleeping tab therefore does not fast-forward through thousands of missed operations. The Page Visibility handler pauses playback explicitly. At high speeds several actions may occur between repaints; Step is how to inspect every event.

Start after completion resets to the same original input. Stop preserves the iterator. Reset abandons it and creates a fresh iterator from the original. New data changes that original. Algorithm changes preserve it for comparisons. Count/pattern changes create new data and cancel old progress. There is no stored playback history, rewind or import feature.

## 7. Draw bars safely

Each bar is a div created once per input change. Its height is `value / originalMaximum * 95%`. Use the original maximum: intermediate insertion/merge states can hide the largest value in a saved key/buffer, and recalculating from the visible array would make every bar rescale unexpectedly.

Classes `.active` and `.sorted` change colour. Final-state green takes priority over active amber. Small datasets show labels; larger ones rely on tooltips and the expandable text values. Caption/metrics use `textContent`, never parsed HTML. CSS flex layout divides available width among up to 128 bars.

The chart is not an essential-canvas-only image: native form controls, a short live status and a current-values text alternative provide other ways to inspect it. Do not send every step to a live region at 300 per second; that would overwhelm assistive technology. Colour is supported by the legend, operation caption and text data, but this still does not provide a complete spoken sorting lesson.

## 8. Read one algorithm before nine

Start with bubble's nested loops and early-exit flag. Then selection's minimum index. Read insertion's saved key before merge's two auxiliary buffers. Quick sort introduces a partition boundary and recursion; heap uses index arithmetic for a tree; Shell generalises insertion with a gap. Counting/radix replace pairwise ordering with integer key locations.

See [ALGORITHMS.md](ALGORITHMS.md) for complete examples and variant-specific complexity. Metadata/pseudocode are teaching sketches, not a literal listing of every yielded event or JavaScript line.

## 9. Test the model, then test the browser

From the repository root with Node.js 22+:

```sh
node --test day-12-sort-lab/tests/algorithms.test.cjs
```

Node's test module gives named cases. A numerical `Array.sort((a,b)=>a-b)` is used only as the **test oracle**, never to implement a sorting algorithm. For each algorithm tests compare the final values, input nonmutation, event indexes, monotonic counters and the truth of every final-green claim. Seeded random inputs make failures reproducible.

Browser testing is separate: model correctness cannot prove Stop pauses, Reset restores the right dataset, keyboard focus works or a phone layout avoids horizontal overflow. Do both before publishing.

## Exercises

1. Step through insertion until you see a duplicate. Where is the displaced key stored?
2. Remove bubble's early exit; write a test showing comparisons increase for sorted input.
3. Try quick sort on all-equal data; explain the strict less-than partition and unbalanced recursion.
4. Add a new data pattern without touching any sort implementation.
5. Add a tagged-record model to demonstrate stability. Updating only bar colours does not prove it.
6. Add a maximum-value slider; document how it changes counting's key range and radix's digits.
7. Add a statistics export only after deciding whether it exports algorithm counters or animation time.

Background API links, licences and privacy details are in the [README](README.md#references-and-licence).
