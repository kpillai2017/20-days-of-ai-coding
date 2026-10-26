(function () {
"use strict";
/**
 * SortLab: Interactive Sorting Algorithms Visualizer
 * Provides 9 classic sorting algorithms with step-by-step execution tracking
 */

// ============================================================================
// ALGORITHM DEFINITIONS & METADATA
// ============================================================================

/**
 * Metadata for all sorting algorithms.
 * Each algorithm includes complexity analysis, stability info, and pseudocode.
 * @type {Object.<string, Object>}
 */
const ALGORITHMS = {
  bubble: {
    name: 'Bubble Sort',
    description: 'Simple comparison sort that repeatedly steps through list, comparing adjacent elements and swapping if in wrong order.',
    best: 'O(n)',
    average: 'O(n²)',
    worst: 'O(n²)',
    space: 'O(1)',
    stable: true,
    steps: [
      'for i = 0 to length - 1',
      '  for j = 0 to length - i - 2',
      '    if array[j] > array[j + 1]',
      '      swap(array[j], array[j + 1])'
    ],
    explanation: 'Bubble sort compares adjacent pairs and swaps them if they are in the wrong order. This "bubbles" larger elements toward the end with each pass. Though simple and stable, it is very slow for large datasets.'
  },
  selection: {
    name: 'Selection Sort',
    description: 'Divides array into sorted and unsorted regions, repeatedly selecting minimum from unsorted and moving to sorted region.',
    best: 'O(n²)',
    average: 'O(n²)',
    worst: 'O(n²)',
    space: 'O(1)',
    stable: false,
    steps: [
      'for i = 0 to length - 2',
      '  minIdx = i',
      '  for j = i + 1 to length - 1',
      '    if array[j] < array[minIdx]',
      '      minIdx = j',
      '  swap(array[i], array[minIdx])'
    ],
    explanation: 'Selection sort finds the smallest unsorted element and places it at the beginning of the unsorted region. Not stable because the swap may move equal elements out of order.'
  },
  insertion: {
    name: 'Insertion Sort',
    description: 'Builds sorted array one item at a time by inserting each element into its correct position in the sorted portion.',
    best: 'O(n)',
    average: 'O(n²)',
    worst: 'O(n²)',
    space: 'O(1)',
    stable: true,
    steps: [
      'for i = 1 to length - 1',
      '  key = array[i]',
      '  j = i - 1',
      '  while j >= 0 and array[j] > key',
      '    array[j + 1] = array[j]',
      '    j = j - 1',
      '  array[j + 1] = key'
    ],
    explanation: 'Insertion sort builds a sorted array by taking elements one at a time and inserting them into their correct position. Efficient for small datasets and nearly sorted data. Stable and adaptive.'
  },
  merge: {
    name: 'Merge Sort',
    description: 'Divide-and-conquer algorithm that recursively divides array in half, then merges sorted halves together.',
    best: 'O(n log n)',
    average: 'O(n log n)',
    worst: 'O(n log n)',
    space: 'O(n)',
    stable: true,
    steps: [
      'if range has fewer than 2 items: return',
      'split range at its midpoint',
      'recursively sort both halves',
      'copy halves into auxiliary buffers',
      'compare the two buffer heads (left wins ties)',
      'take the remaining head if one side is empty',
      'write the smaller head back into the array'
    ],
    explanation: 'Merge sort divides the array into halves recursively until single elements remain, then merges them back in sorted order. Guarantees O(n log n) but requires extra space. Stable due to careful merge.'
  },
  quick: {
    name: 'Quick Sort',
    description: 'Divide-and-conquer using Lomuto partition; selects pivot and partitions around it. Last element is pivot.',
    best: 'O(n log n)',
    average: 'O(n log n)',
    worst: 'O(n²)',
    space: 'O(log n) avg; O(n) worst',
    stable: false,
    steps: [
      'if low < high',
      '  pi = partition(low, high)',
      '  quickSort(low, pi - 1)',
      '  quickSort(pi + 1, high)',
      '// partition: move pivot, swap smaller left'
    ],
    explanation: 'Quick sort uses Lomuto partition with last element as pivot. Elements smaller than pivot move left, larger move right. Often fast on mixed input, but worst-case O(n²) on sorted data or many duplicates. In-place but not stable.'
  },
  heap: {
    name: 'Heap Sort',
    description: 'Builds max-heap from array, then repeatedly extracts max element and places at end, shrinking heap.',
    best: 'O(n log n)',
    average: 'O(n log n)',
    worst: 'O(n log n)',
    space: 'O(1)',
    stable: false,
    steps: [
      'buildMaxHeap(array)',
      'for i = length - 1 down to 1',
      '  swap(array[0], array[i])',
      '  heapify(array, 0, i)'
    ],
    explanation: 'Heap sort first builds a max-heap, then repeatedly removes the root (maximum) and restores heap property on the reduced array. Guarantees O(n log n) and uses constant extra space, but not stable.'
  },
  shell: {
    name: 'Shell Sort',
    description: 'Generalization of insertion sort that allows exchange of far-apart elements using decreasing gap sequence.',
    best: 'O(n log n)',
    average: 'Gap-dependent',
    worst: 'O(n²)',
    space: 'O(1)',
    stable: false,
    steps: [
      'gap = length / 2',
      'while gap > 0',
      '  for i = gap to length - 1',
      '    temp = array[i]',
      '    j = i - gap',
      '    while j >= 0 and array[j] > temp',
      '      array[j + gap] = array[j]',
      '      j = j - gap',
      '    array[j + gap] = temp',
      '  gap = gap / 2'
    ],
    explanation: 'Shell sort is an extension of insertion sort that uses a decreasing gap sequence. It starts by comparing far-apart elements, gradually reducing the gap. Not stable but works well in practice, especially for medium-sized arrays.'
  },
  counting: {
    name: 'Counting Sort',
    description: 'Non-comparative sort for integers; counts occurrences of each value and reconstructs sorted array.',
    best: 'O(n + k)',
    average: 'O(n + k)',
    worst: 'O(n + k)',
    space: 'O(n + k)',
    stable: true,
    steps: [
      'find maximum integer key',
      'initialise max + 1 counters to zero',
      'read each value',
      'increment its key counter',
      'prefix-sum counters into ending positions',
      'scan original values right to left',
      'place in output and decrement key position',
      'copy stable output back to array'
    ],
    explanation: 'Counting sort counts how many times each value appears, then uses this to place elements in correct positions. Linear time O(n+k) where k is range of values. Stable when implemented with reverse buffer. Only works for non-negative integers.'
  },
  radix: {
    name: 'Radix Sort',
    description: 'Non-comparative sort using counting sort on each digit position (LSD - least significant digit first).',
    best: 'O(d(n + b))',
    average: 'O(d(n + b))',
    worst: 'O(d(n + b))',
    space: 'O(n + b)',
    stable: true,
    steps: [
      'exp = 1',
      'while max / exp > 0',
      '  countingSort by digit at position exp',
      '  exp = exp * 10'
    ],
    explanation: 'Radix sort processes integers digit by digit using a stable counting sort (LSD approach). Each pass considers one decimal digit position. Time O(d(n+b)), where d is digit count and b=10 is the radix. Efficient for sorting integers with limited digit count.'
  }
};

/** Validate at the model boundary; a future caller can bypass the form. */
function validate(values) {
  if (!Array.isArray(values) || values.length > 128 ||
      Array.from(values).some(value => !Number.isInteger(value) || value < 1 || value > 999)) {
    throw new RangeError('Use up to 128 integers from 1 to 999.');
  }
}

/** One generator is a PAUSABLE function. Each next() resumes until yield.
 * The algorithm owns a private array; each event is a fresh snapshot. The UI
 * never edits this array, so a redraw cannot accidentally change the sort.
 */
function* run(id, input) {
  const a = input.slice();
  const n = a.length;
  let comparisons = 0, writes = 0, swaps = 0, auxWrites = 0;
  const fixed = new Set();

  /** Snapshot the state; line numbers are zero-based pseudocode indexes. */
  function event(note, line = 0, active = [], done = false) {
    return { values: a.slice(), active: [...new Set(active)], sorted: [...fixed],
      line, comparisons, writes, swaps, auxWrites, note, done };
  }
  /** Count VALUE comparisons, not loop/index tests. Yield before deciding. */
  function* compare(i, j, line, note = 'Compare the highlighted values.') {
    comparisons++;
    yield event(note, line, [i, j]);
    return a[i] - a[j];
  }
  /** A real swap writes two main-array cells. Self-swaps do no work. */
  function* swap(i, j, line) {
    if (i === j) return;
    [a[i], a[j]] = [a[j], a[i]];
    swaps++; writes += 2;
    yield event(`Swap positions ${i + 1} and ${j + 1}.`, line, [i, j]);
  }
  /** Assignment can temporarily duplicate a value during insertion/merge.
   * That is expected: a saved key or auxiliary buffer still owns the other one.
   */
  function* write(i, value, line, note) {
    a[i] = value; writes++;
    yield event(note || `Write ${value} into position ${i + 1}.`, line, [i]);
  }

  yield event('Ready. Values increase from left to right when finished.');
  if (id === 'bubble') {
    for (let end = n - 1; end > 0; end--) {
      let changed = false;
      for (let j = 0; j < end; j++) {
        if ((yield* compare(j, j + 1, 2)) > 0) {
          yield* swap(j, j + 1, 3); changed = true;
        }
      }
      fixed.add(end);
      yield event(`The largest remaining value is fixed at position ${end + 1}.`, 0);
      if (!changed) break; // Adaptive early exit gives the sorted O(n) best case.
    }
  } else if (id === 'selection') {
    for (let i = 0; i < n - 1; i++) {
      let min = i;
      for (let j = i + 1; j < n; j++) {
        if ((yield* compare(j, min, 3, 'Search for the smallest remaining value.')) < 0) min = j;
      }
      yield* swap(i, min, 5);
      fixed.add(i);
      yield event(`Position ${i + 1} now contains its final value.`, 0, [i]);
    }
  } else if (id === 'insertion' || id === 'shell') {
    // Insertion is the gap=1 special case of gapped insertion. Shell halves
    // the gap until every neighbour participates in the final insertion pass.
    for (let gap = id === 'insertion' ? 1 : Math.floor(n / 2); gap > 0;
         gap = id === 'insertion' ? 0 : Math.floor(gap / 2)) {
      yield event(`Insertion gap: ${gap}.`, 0);
      for (let i = gap; i < n; i++) {
        const key = a[i];
        let j = i;
        while (j >= gap) {
          comparisons++;
          yield event(`Compare ${a[j - gap]} with saved key ${key} (gap ${gap}).`, id === 'shell' ? 5 : 3, [j - gap, i]);
          if (a[j - gap] <= key) break;
          yield* write(j, a[j - gap], id === 'shell' ? 6 : 4, 'Shift a larger value to make room for the saved key.');
          j -= gap;
        }
        yield* write(j, key, id === 'shell' ? 8 : 6, `Insert saved key ${key} into its current gap sequence.`);
      }
    }
  } else if (id === 'merge') {
    /** Recursion divides ranges, then merges two independently sorted halves. */
    function* merge(lo, hi) {
      if (hi - lo < 2) return;
      const mid = Math.floor((lo + hi) / 2);
      yield event(`Divide positions ${lo + 1}–${hi} into two halves.`, 1, [lo, hi - 1]);
      yield* merge(lo, mid); yield* merge(mid, hi);
      const left = a.slice(lo, mid), right = a.slice(mid, hi);
      auxWrites += left.length + right.length; // Copying into buffers is work too.
      yield event('Copy the two sorted halves into temporary buffers.', 3, [lo, mid]);
      let i = 0, j = 0, k = lo;
      while (i < left.length || j < right.length) {
        let value;
        if (i === left.length) value = right[j++];
        else if (j === right.length) value = left[i++];
        else {
          comparisons++;
          yield event(`Compare buffer heads ${left[i]} and ${right[j]}.`, 4, [lo + i, mid + j]);
          value = left[i] <= right[j] ? left[i++] : right[j++]; // Left ties preserve stability.
        }
        yield* write(k++, value, 6, `Merge the next smallest buffer value (${value}).`);
      }
    }
    yield* merge(0, n);
  } else if (id === 'quick') {
    /** Lomuto partition: the last value is pivot, so ordered input is worst-case. */
    function* quick(lo, hi) {
      if (lo >= hi) { if (lo === hi) fixed.add(lo); return; }
      let boundary = lo;
      yield event(`Choose ${a[hi]} at position ${hi + 1} as pivot.`, 1, [hi]);
      for (let j = lo; j < hi; j++) {
        if ((yield* compare(j, hi, 4, `Compare with pivot ${a[hi]}.`)) < 0) {
          yield* swap(boundary++, j, 4);
        }
      }
      yield* swap(boundary, hi, 1);
      fixed.add(boundary);
      yield event('Pivot is now in its final position.', 1, [boundary]);
      yield* quick(lo, boundary - 1); yield* quick(boundary + 1, hi);
    }
    yield* quick(0, n - 1);
  } else if (id === 'heap') {
    /** Iterative sift-down restores the max-heap without recursive stack space. */
    function* sift(root, size) {
      while (root * 2 + 1 < size) {
        let child = root * 2 + 1;
        if (child + 1 < size && (yield* compare(child, child + 1, 3)) < 0) child++;
        if ((yield* compare(root, child, 3, 'Restore the max-heap: parent must be at least as large as its children.')) >= 0) break;
        yield* swap(root, child, 3); root = child;
      }
    }
    for (let root = Math.floor(n / 2) - 1; root >= 0; root--) yield* sift(root, n);
    yield event('Max-heap built. The root contains the largest value.', 0, n ? [0] : []);
    for (let end = n - 1; end > 0; end--) {
      yield* swap(0, end, 2); fixed.add(end);
      yield* sift(0, end);
    }
  } else if (id === 'counting' || id === 'radix') {
    // Non-comparison here means placement uses integer keys/digits. The max
    // scan uses Math.max and is NOT counted in the key-comparison metric.
    const max = n ? Math.max(...a) : 0;
    const passes = id === 'counting' ? [0] : Array.from({ length: String(max).length }, (_, i) => 10 ** i);
    for (const exp of passes) {
      const buckets = id === 'counting' ? max + 1 : 10;
      const count = new Array(buckets).fill(0);
      const output = new Array(n);
      auxWrites += buckets; // Explicit zero-initialisation of bucket cells.
      /** Extract a full key (counting) or one decimal digit (radix). */
      const digit = value => exp === 0 ? value : Math.floor(value / exp) % 10;
      yield event(exp ? `Stable pass for decimal place ${exp}.` : 'Allocate one counter per integer key.', id === 'counting' ? 1 : 1);
      for (let i = 0; i < n; i++) {
        count[digit(a[i])]++; auxWrites++;
        yield event(`Count key ${digit(a[i])} from value ${a[i]}.`, id === 'counting' ? 3 : 2, [i]);
      }
      for (let i = 1; i < buckets; i++) { count[i] += count[i - 1]; auxWrites++; }
      yield event('Prefix sums locate the end of each key group.', id === 'counting' ? 4 : 2);
      for (let i = n - 1; i >= 0; i--) {
        const key = digit(a[i]);
        output[--count[key]] = a[i]; auxWrites += 2;
        yield event(`Place ${a[i]} into its stable auxiliary position (scan right to left).`, id === 'counting' ? 6 : 2, [i]);
      }
      for (let i = 0; i < n; i++) yield* write(i, output[i], id === 'counting' ? 7 : 2, 'Copy the stable output back to the main array.');
      if (!n) break;
    }
  }
  for (let i = 0; i < n; i++) fixed.add(i);
  yield event(`${ALGORITHMS[id].name} complete.`, 0, [], true);
}

/** Return a fresh iterator; validation happens immediately, not at first next. */
function createStepper(id, values) {
  if (!Object.hasOwn(ALGORITHMS, id)) throw new RangeError('Choose a known algorithm.');
  validate(values);
  return run(id, values.slice());
}

/** Make an input distribution. An optional RNG makes tests reproducible.
 * Counts are UI-sized (8–128); the algorithms themselves also accept 0–7 items.
 */
function createData(count, pattern, rng = Math.random) {
  if (!Number.isInteger(count) || count < 8 || count > 128) throw new RangeError('Use 8–128 items.');
  if (!['random', 'reversed', 'nearly', 'sorted', 'few-unique'].includes(pattern)) throw new RangeError('Unknown pattern.');
  /** Keep generated values within the promised interval, even with a custom RNG. */
  function randomIndex(size) {
    const value = rng();
    if (!Number.isFinite(value) || value < 0 || value >= 1) throw new RangeError('RNG must return a number in [0, 1).');
    return Math.floor(value * size);
  }
  const ascending = Array.from({ length: count }, (_, i) => 1 + Math.floor(i * 99 / Math.max(1, count - 1)));
  if (pattern === 'sorted') return ascending;
  if (pattern === 'reversed') return ascending.reverse();
  if (pattern === 'nearly') {
    for (let i = 0; i < Math.max(1, Math.floor(count / 10)); i++) {
      const j = randomIndex(count - 1);
      [ascending[j], ascending[j + 1]] = [ascending[j + 1], ascending[j]];
    }
    return ascending;
  }
  return Array.from({ length: count }, () => pattern === 'few-unique' ? [10, 30, 50, 70, 90][randomIndex(5)] : randomIndex(100) + 1);
}

const api = Object.freeze({ ALGORITHMS, createStepper, createData });
if (typeof module !== 'undefined' && module.exports) module.exports = api;
else globalThis.SortLab = api;
})();
