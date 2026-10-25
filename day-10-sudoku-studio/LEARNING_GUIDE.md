# Sudoku Studio: a beginner's guided tour

Read this with `sudoku.py` and `main.py` open. The model has no Pygame imports, so you can learn the puzzle rules before learning how a window works.

## 1. Represent a board with lists

```python
board = [[0 for col in range(9)] for row in range(9)]
board[0][3] = 7
```

Zero means blank. `board[row][column]` uses indexes 0–8 even though players usually say rows 1–9. The outer list contains nine separate row lists. Avoid `[[0]*9]*9`: that repeats references to the **same** row, so changing one row changes others too.

A 3×3 box starts at `((row // 3) * 3, (col // 3) * 3)`. Integer division groups indexes 0,1,2 into box 0, indexes 3,4,5 into box 1, and so on.

`validate_board` checks size and values, rejects booleans (Python otherwise treats True as integer 1) and makes an independent copy. Valid shape is not the same as a valid Sudoku state: duplicate detection is separate.

## 2. Local rules and candidates

A candidate is a digit absent from the cell's row, column and box:

```text
{1,2,3,4,5,6,7,8,9}
 minus digits in row
 minus digits in column
 minus digits in box
 = locally allowed values
```

A Python `set` naturally removes duplicates. `_candidates` is an internal fast path for an already validated board; public `candidates` validates the input first. Keeping repeated validation out of recursive search avoids needless copying.

`conflicts` returns every nonzero cell participating in a duplicate. That is what red highlighting shows. A digit can be wrong without any immediate duplicate: local permission is not global solvability.

## 3. Recursion and the search tree

To solve, choose an empty cell, try a candidate, then solve the smaller remaining problem. If a later cell has no candidates, undo the attempted value and try the next.

```text
choose cell
  ├─ try 2 → later contradiction → erase 2
  ├─ try 5 → continue → complete valid board!
  └─ try 8 → not needed after a solution is found
```

A function calling itself is **recursion**. Undoing a choice and exploring another branch is **backtracking**. A full valid board is the successful base case; a blank with zero candidates is a failed branch.

The solver scans for the cell with the **minimum remaining values (MRV)**, rather than always choosing the first blank. This is the “most constrained first” heuristic: try the place with the fewest options. Candidates are tried in sorted order for reproducibility. This is a search heuristic, not proof that the puzzle is easy for a person.

The solver edits a private working copy and returns either a complete grid or None. Your original board stays untouched. Conflicting/invalid inputs return no solution. A conflict-free board may also be unsatisfiable, requiring search to discover the problem.

## 4. Finding one solution is not proving uniqueness

A board with no clues has many solutions. Returning the first does not prove that a puzzle is well formed.

`count_solutions(board, limit=2)` explores until it finds two or exhausts all branches:

| Result | Meaning |
| --- | --- |
| 0 | No solution |
| 1 | Exactly one, after search is exhausted |
| 2 | At least two; no need to count further |

This early cutoff is valuable during generation. We need to know whether uniqueness survived, not count every arrangement.

## 5. Generate backwards

1. Fill an empty grid by randomized backtracking, choosing shuffled candidate values.
2. Copy that complete solution into a puzzle board.
3. Shuffle all 81 cell coordinates.
4. Temporarily erase one clue.
5. Count solutions up to two. Keep the erasure only if the count is one.
6. Continue until the target clue count is reached, or test another generated grid.

The full-grid constructor uses first-empty-cell randomized backtracking; the solution finder/counter uses MRV. Both use the same local Sudoku constraints. Generation retries at most twelve complete attempts and reports failure honestly if no grid meets the band.

A private `random.Random(seed)` means puzzle generation does not reseed every other random feature in the program. Given the same code and seed, the choices are repeatable. `App` increments the base seed for each New request, giving a reproducible series instead of repeatedly displaying the same grid.

More erasures tend to require more work, but clue count alone is **not a reliable human difficulty grade**. This project's Easy/Medium/Hard names mean 40–44 / 33–37 / 27–31 givens, respectively. It does not detect pairs, X-wings or other named human strategies, and does not promise symmetrical or minimal puzzles.

## 6. Session state and undo

`Puzzle` groups original clues, solution, label and clue count. `Session` protects its own copy, and its public puzzle property returns a snapshot so a caller cannot accidentally rewrite original givens.

Session keeps:

- a working `board`;
- `notes`, a dictionary mapping `(row, col)` to sets of pencil digits;
- `selected` and `note_mode` for editing;
- an `assisted` flag for hints/reveals;
- a stack of history snapshots.

Before any board/notes change, save independent copies of board, notes and assistance. Undo pops that old snapshot. Saving **after** mutation is a subtle bug: Undo would simply restore the change you wanted to undo. Selected cell and pencil-mode toggle are UI state and are not part of history.

Hints reveal a known solution value rather than explaining a deduction. Solve considers the current filled entries as constraints and fails rather than silently fixing them. `apply_solution` checks a returned board and preserves filled entries before applying the reveal undoably.

Custom-board mode creates an all-editable blank puzzle. Its typed entries are constraints when solving, not permanently locked givens. It may have zero, one or many solutions. Hints are disabled, and Solve gives one solution without certifying uniqueness. Reset returns it to blank.

## 7. Keep the window responsive

Pygame's main thread handles events and drawing. A slow recursive search on that thread would make the window appear frozen. `ThreadPoolExecutor(max_workers=1)` runs generation or solving in one worker:

```text
main thread:      events → poll → draw → events → poll → draw
worker:          [ search............................ ]
                                                     ↓ result
main thread:                              future.result() → apply
```

`poll()` checks `future.done()` before collecting the result; it does not wait every frame. A solver receives a **copy** of the current board. Editing is locked during a search, and the result is applied on the main thread. The worker never draws, calls Pygame or changes the session directly.

This is not parallel CPU speed-up in the usual CPython interpreter: the GIL still affects Python threads. It is a responsiveness and ownership design. A single worker avoids racing simultaneous jobs. Closing waits for the bounded job to finish; searches are not cancellable halfway through. Extremely underconstrained custom boards stop at the first solution, while pathological contradictory boards can still take time.

## 8. Drawing and mouse coordinates

The board lives at a fixed logical rectangle. A cell's screen origin is:

```text
x = grid_left + column × cell_size
y = grid_top  + row    × cell_size
```

Draw cell backgrounds, then digits/notes, then grid lines. Every third boundary is thicker to reveal the 3×3 boxes. Selected peers share a tint; matching digits and direct conflicts get distinct colours.

When resizing, draw the same logical Surface, scale it to fit, and letterbox the rest. Reverse that transformation for a mouse click:

```text
logical_x = (window_x - left_margin) / scale
logical_y = (window_y - top_margin)  / scale
column = int((logical_x - grid_left) // cell_size)
row    = int((logical_y - grid_top)  // cell_size)
```

The `int` matters: dividing scaled coordinates creates floats, but list indexes must be integers. Check that the point lies inside the grid before indexing.

## 9. Timer, completion and tests

Only active play adds elapsed time. Pause hides digits, and focus loss pauses without auto-resume. Completion means a full conflict-free board, not merely matching a stored string. Assisted completion is labelled separately. Reset intentionally clears all history and starts the timer over; it is not an undoable action.

Tests use known grids and generated seeds, not just random clicks. They check solver nonmutation, uniqueness, clue bands, notes/undo, protected givens, invalid input, custom solving and headless controls. The dummy SDL driver permits rendering without a real monitor; it does not prove human readability or make this a screen-reader-accessible app.

## Exercises

1. Print candidate sets for a blank in your puzzle. Explain which row/column/box removed each missing digit.
2. Compare first-empty search with MRV using a counter of attempted placements.
3. Remove another clue and count solutions. Why can a puzzle stay solvable but stop being unique?
4. Add a note, undo it, then undo an erase. Write a regression test before editing history code.
5. Try a wrong entry that causes no red duplicate. Ask Solve why it still cannot finish.
6. Add a symmetry option: remove paired cells only when uniqueness survives. Keep the existing clue-band contract.
7. Implement a naked-single explanation, distinct from a solution reveal. Do not label guesses as logical deductions.

Further reading and licensing links are in the [README](README.md#references-origins-and-licence).
