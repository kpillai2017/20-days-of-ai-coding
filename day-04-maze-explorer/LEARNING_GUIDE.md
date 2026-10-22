# Maze Explorer: learn the algorithms by hand

Start with [installation and controls](README.md). This tour assumes no graph-algorithm knowledge. Spend five minutes playing, then follow one tiny example before reading the full source.

## 1. Reading route

1. Play a seeded maze and toggle the hint. Notice that moving and solving are different actions.
2. Read `DIRECTIONS`, `Maze.__init__()` and `_generate_maze()` in `maze.py`.
3. Draw the four-cell example below and trace the generation stack.
4. Read `solve()` and trace its queue and parent dictionary.
5. Read `MazeGame.move()`, then `handle_event()` and `draw_game()` in `main.py`.
6. Run the model tests and inspect a test that checks passages in both directions.

## 2. A maze is a graph

A **graph** is a collection of vertices and connections (edges). Here a vertex is a cell, and an edge is an open passage. We don't store a wall object for every wall. Instead, the absence of a passage between neighboring cells means they cannot be crossed.

A cell is a tuple `(row, col)`. Tuples are immutable and hashable, making them useful dictionary keys and set members. A set avoids duplicate connections; a dictionary locates a cell's set of neighbors.

This complete **2 × 2** example is connected and has three passages:

```text
A — B      A=(0,0)   B=(0,1)
    |      C=(1,0)   D=(1,1)
C — D
```

```python
passages = {
    (0, 0): {(0, 1)},
    (0, 1): {(0, 0), (1, 1)},
    (1, 0): {(1, 1)},
    (1, 1): {(0, 1), (1, 0)},
}
```

Check each connection: A lists B **and** B lists A. Storing a connection only once would allow walking one way but not returning. `neighbors(cell)` returns a tuple in up/right/down/left order, not the internal set. That fixed order makes search tie-breaking predictable.

Each passage appears twice in the dictionary. Add the set lengths and divide by two to count undirected edges: `(1 + 2 + 1 + 2) // 2 = 3`.

A **perfect maze** connects all V cells without cycles and has V−1 edges. It is a tree: exactly one simple route connects each pair of cells. A route that revisits cells is a walk, not a simple path.

## 3. DFS: build by exploring deeply

**Depth-first search** follows one branch as far as possible. When stuck, it returns to an earlier choice: **backtracking**.

A **stack** is last-in, first-out (LIFO). Python's list supplies `append()` to push and `pop()` to remove the latest entry. `stack[-1]` looks at the top without removing it.

For the example, assume the shuffled directions choose A→B, then B→D, then D→C. This is a possible random run, not a claim about a particular seed.

| Step | Action | Stack after action | Visited |
| --- | --- | --- | --- |
| 1 | Start at A | `[A]` | A |
| 2 | Carve A↔B; push B | `[A, B]` | A, B |
| 3 | Carve B↔D; push D | `[A, B, D]` | A, B, D |
| 4 | Carve D↔C; push C | `[A, B, D, C]` | A, B, C, D |
| 5 | C has no unvisited neighbor; pop | `[A, B, D]` | unchanged |
| 6 | D has no unvisited neighbor; pop | `[A, B]` | unchanged |
| 7 | B has no unvisited neighbor; pop | `[A]` | unchanged |
| 8 | A has no unvisited neighbor; pop | `[]` | unchanged |

Popping does **not** remove carved passages or visited marks. It only changes where the algorithm looks next. A wall A↔C remains because C was already visited when A was reconsidered.

### Why no cycles?

Every new passage joins the existing carved region to a cell it has never reached. Joining two already-visited cells could create a loop, so generation never does that. A connected grid lets the search eventually reach every cell.

### Why iterative rather than recursive?

Recursion can express DFS elegantly, but a long narrow path may exceed Python's recursion limit. An explicit list stack handles up to the supported 50 × 50 cells without using one Python call per depth.

### Where randomness lives

`rng = Random(self.seed)` creates a private generator. Its shuffle chooses which direction to try first. It does not reseed the global `random` module. The same seed, implementation and Python version reproduce a layout; different seeds need not always give different mazes. `None` requests unseeded generation, while integer `0` is a valid reproducible seed.

## 4. BFS: solve by exploring in layers

**Breadth-first search** considers all one-step destinations, then all two-step destinations, and so on. A **queue** is first-in, first-out (FIFO): the oldest waiting item is processed first.

The implementation uses `collections.deque`: `append()` adds at the back; `popleft()` removes from the front efficiently. A list's `pop(0)` would shift the remaining items.

Solve A→D on the same example:

| Step | Process | Queue after exploration | New parent entry |
| --- | --- | --- | --- |
| 1 | Initialise | `[A]` | `A: None` |
| 2 | Remove A; discover B | `[B]` | `B: A` |
| 3 | Remove B; skip visited A, discover D | `[D]` | `D: B` |
| 4 | Remove D; it is the goal | `[]` | stop |

`parent` records **how each cell was first reached**, not all its neighbors. Follow parents backward:

```text
D → B → A → None
```

Append those cells into a list and reverse it to get `[A, B, D]`. Both endpoints are included, so the number of moves is `len(path) - 1`, not `len(path)`.

A cell is marked visited when it is **enqueued**, not when removed. Otherwise several neighbors could queue it repeatedly before its first turn.

### Why BFS if a perfect maze has only one route?

It makes the shortest-path guarantee explicit and also works on an unweighted graph with cycles. Our tests include such a graph so the search is not merely relying on tree structure. In a generated perfect maze, shortest and unique simple path coincide. If you manually disconnect passages, a search can return `[]`; merely choosing different valid endpoints in a perfect maze does not disconnect them.

## 5. Separate kinds of “visited”

There are three independent tracking jobs:

- Generator visited set: prevents carving loops during DFS; discarded after generation.
- Solver visited set: prevents repeated queueing during BFS; local to one solve call.
- Game `visited`: records where the player has been; rendered as dots until restart.

A hint doesn't explore on the player's behalf. `game.solution` is computed from the current player cell to the goal without changing `position`, `moves` or the game's visited set.

## 6. From a keypress to pixels

Suppose Right is pressed at `(2, 3)`:

1. pygame delivers a `KEYDOWN` event.
2. `handle_event()` uses `MOVE_KEYS` to translate the key into `"right"`.
3. `game.move("right")` finds delta `(0, 1)` and candidate `(2, 4)`.
4. If the game is won or there is no passage, position and move count stay unchanged.
5. Otherwise position changes, moves increases, and the cell joins the visited set.
6. `draw_game()` draws the resulting state. If the hint is on, it asks for a route from the updated position.
7. `pygame.display.flip()` presents the frame.

Holding a key does not continually move: pygame key repeat is explicitly disabled. No velocity or frame-time multiplication is necessary for one-cell steps.

### Coordinates: rows aren't X

On the default board each cell is 40 pixels wide/high. The upper-left maze corner is `(60, 140)`:

```python
x = 60 + col * 40
y = 140 + row * 40
# Marker centre: add half a cell.
center_x = 60 + (col + 0.5) * 40
center_y = 140 + (row + 0.5) * 40
```

Cell `(1, 2)` has top-left `(140, 180)` and centre `(160, 200)`. Screen Y grows downward; model row also grows downward. Only rendering converts `(row, col)` into `(x, y)`. Custom model dimensions are scaled to fit the same drawing area.

## 7. Complexity without mystery

V means vertices/cells; E means edges/passages. Each cell has at most four neighbors. DFS and BFS take **O(V + E)** time and O(V) auxiliary space in this grid. A perfect maze has E=V−1, so time grows linearly with cell count.

This describes scaling, not a universal timing promise. Actual runtime depends on hardware, Python and rendering. Generation runs only on a new maze; visible hints currently rerun BFS during drawing, not just when position changes. Caching hints could be a later exercise, with invalidation on movement/new maze.

## 8. Run a tiny experiment

From `day-04-maze-explorer`, open Python with `python` (Windows: the environment's Python path) and enter:

```python
from maze import Maze
maze = Maze(2, 2, seed=42)
print(maze.passages)
path = maze.solve()
print(path)
print("moves:", len(path) - 1)
print("passages:", sum(len(v) for v in maze.passages.values()) // 2)
```

Expected: four cells, three undirected passages, and a valid inclusive route from `(0, 0)` to `(1, 1)`. Don't assume this seed reproduces the earlier hand-drawn example.

To debug, set an editor breakpoint inside `_generate_maze()` at `stack.append(neighbor_cell)`, then launch `main.py --seed 42` through the editor's Python debugger. Inspect `current_cell`, `neighbor_cell`, `visited` and `stack`. Merely starting Python in a separate terminal doesn't connect it to an editor breakpoint. Step and resume; remove the breakpoint afterward.

## 9. Tests: make properties observable

Run `python -m unittest discover -s tests -p test_maze.py -v` from the project folder. Arrange–Act–Assert means prepare input, execute an operation, compare the outcome.

Useful invariants:

- Every passage has a reverse and joins two orthogonally adjacent in-bounds cells.
- Every cell is reachable from the start.
- The undirected passage count is V−1.
- Every adjacent pair in a returned path is connected.
- Restart preserves the maze object; a new maze replaces it.

Do not test that two random results **must differ**. Random processes can repeat. Fixed seeds and structural invariants give reproducible checks without that false assumption.

## 10. Glossary

| Term | Meaning |
| --- | --- |
| Vertex / edge | Cell / open passage |
| Adjacency | Direct connection, not general reachability |
| Tree | Connected graph without cycles |
| Stack | Last item added is processed first |
| Queue | First item added is processed first |
| Backtracking | Return to an earlier search position to try other options |
| BFS parent | The cell from which a cell was first discovered |
| Seed | Input used to reproduce pseudorandom choices |
| Invariant | Property expected to remain true |
| `@property` | Method exposed using attribute syntax, e.g. `game.won` |
| `None` | Python's absence sentinel, distinct from integer zero |

## 11. Three small exercises

1. **Prove passage counting.** For a 3 × 3 maze, expect 9 cells and 8 undirected passages. Print the sum of neighbor-set lengths; expect 16. Explain the division by two.
2. **Trace BFS with a branch.** On paper attach a dead-end cell to B in the tiny example. Write queue and parent values as it is explored. The A→D route should still exclude the dead end.
3. **Design a hint cache.** Write down which actions invalidate it: movement, restart, new maze, and manual passage edits. Add tests before changing rendering; the cached route must start at the current position.

References: [DFS](https://en.wikipedia.org/wiki/Depth-first_search), [BFS](https://en.wikipedia.org/wiki/Breadth-first_search), [Python deque](https://docs.python.org/3/library/collections.html#collections.deque), [Python random](https://docs.python.org/3/library/random.html), [pygame events](https://www.pygame.org/docs/ref/event.html).

Own documentation and code: [MIT licence](../LICENSE). Reference material and pygame retain their own rights; see [third-party notices](../THIRD_PARTY_NOTICES.md).
