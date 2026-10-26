# Nine ways to sort: a guided field notebook

All variants here sort ascending integers. `n` means item count; `k` means the range of integer keys; `d` is decimal digit count; `b=10` is the radix. Big-O describes growth, not measured milliseconds. Extra space below excludes the visualiser's snapshots and copied input. A stable sort preserves the relative order of equal-key **records**; equal-height numeric bars alone cannot prove stability.

## 1. Bubble sort — let the largest rise

Compare neighbours and swap only when the left one is larger. After a full pass the largest remaining item is at the end. Repeat on the shorter prefix. If no swaps occurred, stop early.

```text
[4, 2, 3] → compare 4/2 → [2, 4, 3]
          → compare 4/3 → [2, 3, 4]  (4 is final)
```

**Watch:** amber pairs move along the row; final green suffix grows. **Best O(n)** with early exit; average/worst **O(n²)**; **O(1)** algorithm space. Stable because equal neighbours never swap. Good for learning; rarely a practical general-purpose choice. Try already sorted data to see the early exit.

## 2. Selection sort — find the next minimum

Scan the unsorted region for its smallest value, then swap that into the region's first position. Grow the fixed prefix one item per pass.

```text
[3, 1, 2] → locate 1 → [1, 3, 2] → locate 2 → [1, 2, 3]
```

**Watch:** many comparisons, relatively few swaps. Best/average/worst **O(n²)**; **O(1)** space. Not stable: swapping the first element with a distant minimum can reverse two equal records. Useful when limiting writes matters more than comparisons, but not automatically fastest in real hardware.

## 3. Insertion sort — make room for a saved card

Take the next value as a saved key. Shift larger preceding values one slot right, then insert the saved key. This resembles arranging cards in your hand.

```text
[2, 4, 3] → save 3 → [2, 4, 4] → insert key → [2, 3, 4]
```

The temporary duplicate is intentional: 3 is held outside the displayed array. The sorted prefix is not necessarily at its **final** indexes, so it is not coloured final-green yet. Best **O(n)**; average/worst **O(n²)**; **O(1)** space. Stable: only strictly larger values shift. Often useful for small/nearly sorted inputs. Compare reversed and nearly sorted patterns.

## 4. Merge sort — divide, then weave

Recursively split ranges into halves until each contains fewer than two items. Merge two sorted halves by repeatedly choosing their smaller front value, copying from temporary buffers back into the array. Left wins ties to preserve stability.

```text
[4,1,3,2] → [4,1] [3,2] → [1,4] [2,3] → [1,2,3,4]
```

**Watch:** buffer-head comparisons, then a sequence of main writes. A copied-back region can look sorted while a later merge still moves it. Best/average/worst **O(n log n)**; peak auxiliary **O(n)** plus logarithmic recursion. Stable; pays for buffers. A useful comparison baseline when predictable complexity and stability matter.

## 5. Quick sort — put a pivot in its final home

This implementation uses **Lomuto partitioning with the last item as pivot**. Scan the other items, move strictly smaller values toward the left boundary, and swap the pivot into that boundary. Then recursively sort each side.

```text
[4,1,3,2] pivot 2 → [1,2,3,4] (2 is fixed)
```

The other values need not already be sorted after partitioning. Best/average **O(n log n)** for suitably balanced partitions; worst **O(n²)**. Stack space averages **O(log n)** but can reach **O(n)**. Unstable. Already sorted/reversed and many equal values are deliberately bad examples for this naive pivot rule; production variants improve pivot choice/partitioning. It is not always the fastest algorithm.

## 6. Heap sort — repeatedly remove the champion

A binary max-heap stores a tree in an array. Children of index `i` are `2i+1` and `2i+2`. Build a heap so every parent is at least as large as its children. Swap the largest root to the end, shrink the heap, and sift the new root down.

```text
       max                 root → final suffix
      /   \                restore heap → repeat
```

The visualiser stays in array view, not a tree diagram. Best/average/worst **O(n log n)** for the conventional bound; this iterative sift implementation uses **O(1)** algorithm space. Unstable. Guarantees an upper bound without merge buffers, but constant factors/cache behaviour still matter.

## 7. Shell sort — insertion with shrinking gaps

Perform insertion sort on values separated by a gap. Start at `floor(n/2)`, halve repeatedly, and finish at gap 1. Early wide moves reduce the distance later local shifts need to cover.

```text
indices with gap 4: (0,4,8...), (1,5,9...), ...
then gap 2, then gap 1
```

**Watch:** active positions can be far apart. **O(1)** space; not stable. For this simple halving sequence, worst **O(n²)**; already sorted behaviour is **O(n log n)**. Average performance is **gap/distribution dependent**, not a universal O(n log² n) guarantee. Shell sort's name does not identify one exact gap sequence, so compare claims carefully.

## 8. Counting sort — turn keys into addresses

For bounded integer keys, allocate a count for each value. Count occurrences, prefix-sum the counts into ending positions, scan the original right-to-left into an output buffer, then copy output back.

```text
values: [3,1,3,2]
counts: value 1 → 1, 2 → 1, 3 → 2
output: [1,2,3,3]
```

Reverse placement makes this variant stable. It uses **O(n+k)** time and **O(n+k)** space. Here keys are positive; no signed-number offset handling is implemented. No pairwise ordering comparisons are counted, but maximum scan, bucket initialisation, prefix sums and writes still take work. Poor choice for a huge sparse key range. Counting only frequencies and reconstructing bare numbers can be simpler, but would not demonstrate stable record placement.

## 9. LSD radix sort — stable digit passes

Use a stable counting pass on units, then tens, then hundreds, continuing through the largest value's digits. After processing a more significant digit, earlier lower-digit order is preserved within each new group.

```text
[21, 13, 12] → units: [21,12,13] → tens: [12,13,21]
```

Each digit pass uses ten buckets. Time **O(d(n+b))**, space **O(n+b)** with `b=10`; stable. Not a comparison sort, but not magical O(n) independent of the representation size. This variant handles positive decimal integers only, not negative numbers, arbitrary text, floating point or other bases.

## Experiments that teach more than a race

1. Keep the same input and switch bubble → insertion. Compare counters, not animation duration.
2. Try sorted data with quick sort. Explain why last-pivot partitioning becomes unbalanced.
3. Try few unique values with counting/radix. Which operations disappear, and which still happen?
4. Step insertion to a temporary duplicate. Locate the saved key in the source.
5. Explain why a sorted merge prefix is not final yet, while a quick-sort pivot is.
6. Imagine records `(key=2, name=A)` and `(key=2, name=B)`. Trace whether their order can reverse; numeric bars alone hide the distinction.

Further reading: [Princeton sorting](https://algs4.cs.princeton.edu/20sorting/), [OpenDSA sorting](https://opendsa-server.cs.vt.edu/ODSA/Books/Everything/html/Sorting.html). These are background links, not copied lesson text. See the [README](README.md) for setup, limits and licence.
