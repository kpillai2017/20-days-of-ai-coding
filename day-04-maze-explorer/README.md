# Day 04 · Maze Explorer

Generate a maze, explore its passages, and find the exit. A **Python + pygame** project introducing depth-first search (DFS), backtracking and breadth-first search (BFS).

**New to algorithms?** Start with [the beginner learning guide](LEARNING_GUIDE.md) for tiny worked examples, a glossary and exercises. Comments in the source explain the decisions alongside the code.

## 1. Install and run

Use **Python 3.9–3.13**; Python 3.12 or 3.13 is recommended for convenient pygame wheels. Update your clone with `git pull` or download the latest repository ZIP. From the repository root:

### macOS / Linux

```sh
cd day-04-maze-explorer
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

### Windows (PowerShell)

```powershell
cd day-04-maze-explorer
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

A virtual environment keeps this day's packages separate. Windows commands use its Python directly, avoiding activation-policy issues. On macOS/Linux you can likewise use `.venv/bin/python` without activation. `deactivate` leaves an activated environment.

Optional reproducible initial maze:

```sh
python main.py --seed 42
```

Keep the same implementation and Python version when sharing seeded puzzles. Different seeds can produce the same layout; randomness does not guarantee uniqueness. N creates a fresh unseeded maze, even if you launched with a seed. R preserves the current maze.

## 2. Controls and behavior

| Key | Action |
| --- | --- |
| Arrows / W A S D | Move one cell per keypress if there is a passage |
| H | Show/hide a solution from your **current position** to the goal |
| R | Restart the same maze: reset position, visits, moves and hint |
| N | Generate a fresh random maze and reset play state |
| Esc / close window | Quit |

Key repeat is disabled; release and press again to move another cell. Clicking the window focuses keyboard input.

- **Mint circle:** player. Start has a mint ring; the gold outlined square is the goal.
- **Dots:** cells explored, including paths you later backtrack along.
- **Gold route:** optional solution. Hiding it doesn't remove visited markers.
- **Moves:** successful moves only. Bumping a wall does not count; walking back counts again.
- Reaching the goal shows a win message and blocks further movement. R/N still work; H can still toggle.

Default board: **15 × 15**, drawn in a 600 × 600 area at pixel `(60, 140)` in a fixed **720 × 820** window. The model supports dimensions 1–50 independently; the desktop entry point uses the default. A 1 × 1 model is already won.

No timer, score, audio, saved progress, cloud service or AI API. Everything runs locally after installation. A hint reveals a route but does not move the player.

## 3. Files and responsibilities

```text
day-04-maze-explorer/
├── maze.py               # Pure-Python maze algorithms and game state
├── main.py               # pygame events, drawing and frame loop
├── requirements.txt      # pygame 2.6.1
├── README.md
├── LEARNING_GUIDE.md
└── tests/
    ├── test_maze.py      # Algorithm and movement tests; no pygame needed
    └── test_window.py    # Real pygame headless rendering and controls
```

### `maze.py`: rules without a window

Cells are `(row, col)` tuples. `passages` is a dictionary mapping every cell to a **set** of directly connected cells. A connection is stored in both directions. Missing connections between neighboring grid cells mean walls.

`Maze(rows=15, cols=15, seed=None)` validates dimensions and generates a perfect maze with an iterative, randomized DFS:

1. Start at `(0, 0)`, mark visited, and push it onto a stack.
2. Shuffle possible directions with a private `Random(seed)` instance.
3. Carve a bidirectional passage to one unvisited in-bounds neighbor; push it.
4. If no unvisited neighbor exists, pop the stack to backtrack.
5. Stop when the stack is empty.

Connecting only unvisited cells creates no cycles. All cells become reachable. For `V` cells there are `V - 1` undirected passages, so there is exactly one simple route between any two cells: a **perfect maze**. The private RNG does not change Python's global random state.

`neighbors(cell)` validates the cell and returns connected cells as a **tuple**, in up/right/down/left order. `solve(start=None, goal=None)` uses a FIFO `deque` to explore breadth-first and a parent dictionary to reconstruct the path. Returns a list including both endpoints, or `[]` if disconnected. Both endpoints are validated. In an unweighted graph BFS finds a shortest path; in this generated tree that path is also the unique simple route.

`MazeGame` wraps a maze with `position`, `visited`, `moves` and `show_solution`:

| API | Purpose |
| --- | --- |
| `move(direction)` | Accept up/right/down/left; return whether a legal move happened |
| `won` | Property: position equals goal |
| `solution` | Property: calculate a route from current position to goal |
| `restart()` | Reset play state while keeping the same Maze object |
| `new_maze(seed=None)` | Replace the maze at the same dimensions, then reset |

The generator's visited set is temporary algorithm state; the game's visited set records player exploration. They are different sets for different jobs. Public `passages` is mutable for teaching experiments; changing it arbitrarily can break the generated-maze invariants.

### `main.py`: input and pixels

- `handle_event(event, game)` translates pygame keys into model actions and returns False to quit.
- `cell_center(cell, width, height)` converts row/column to pixel X/Y.
- `draw_game(screen, game, fonts)` draws floors, visited dots, hint, markers, walls and status. It doesn't change model state.
- `run(seed=None, max_frames=None)` runs **events → draw → present**, capped at 60 FPS to avoid unnecessary CPU use. Movement is discrete, so no delta-time physics is needed.

DFS runs only when constructing a maze, not on every frame. BFS runs during rendering only while the hint is visible. Both take **O(V + E)** work; a grid limits connections to four per cell, so that is linear in cell count. Avoid assuming any specific millisecond runtime on all machines.

Only pygame display/font modules are initialised; audio isn't needed. `finally` closes resources even on errors. The `__main__` guard prevents a window opening when tests import the file.

## 4. Tests and smoke check

From this project folder, model tests need Python alone:

```sh
python -m unittest discover -s tests -p test_maze.py -v
```

After installing pygame, run everything:

```sh
python -m unittest discover -s tests -v
```

Window tests use SDL's dummy driver and skip if pygame is absent. They test rendering and actual input handlers, not physical keyboard/monitor behavior. Run each day's Python suite in a separate process: different projects have their own `main.py` names.

A separate real-loop smoke check (macOS/Linux):

```sh
SDL_VIDEODRIVER=dummy python main.py --seed 42 --frames 5
```

`--frames` requires a positive integer. It limits frames; it does **not** select headless mode by itself. In PowerShell:

```powershell
$env:SDL_VIDEODRIVER = "dummy"
.\.venv\Scripts\python.exe main.py --seed 42 --frames 5
Remove-Item Env:SDL_VIDEODRIVER
```

CI runs model/window tests and the smoke check on Python 3.9, 3.12 and 3.13, alongside earlier projects.

### Manual acceptance checklist

1. Generate with `--seed 42` twice; compare layouts.
2. Try an outer wall and an internal wall: no motion or extra moves.
3. Move through a passage, backtrack, and check move/visited counters.
4. Toggle H, move, and verify the route starts from your new position.
5. R returns to the start without changing passages; N resets with fresh generation.
6. Reach the exit; movement stops and the message changes.
7. Close the window or press Esc; process exits cleanly.

## 5. Troubleshooting and small extensions

- **No pygame module:** install requirements with the same interpreter you use to launch. Activate your environment or use its Python path directly.
- **pygame builds from source:** update pip and try Python 3.12/3.13; newer Python versions may lack wheels for the pinned pygame release.
- **No video device:** normal play requires a graphical session. Dummy SDL checks intentionally show no window; unset that environment variable before playing.
- **Keys don't move:** focus the window, release/repress keys, and check for a wall or the won state.
- **Same maze after restart:** intentional—R restarts, N regenerates. A random regeneration can repeat, particularly on tiny boards.

Try changing colors, adding a timer (decide restart behavior first), or showing the BFS exploration order. Add tests for new model behavior before wiring controls. Never assume a seed is a saved player position: it reproduces only a layout under the same implementation.

## References and licence

Original educational implementation with AI coding assistance; no third-party game code, artwork or audio is bundled.

- [Python: random.Random](https://docs.python.org/3/library/random.html#random.Random)
- [Python: collections.deque](https://docs.python.org/3/library/collections.html#collections.deque)
- [Python: unittest](https://docs.python.org/3/library/unittest.html)
- [Depth-first search](https://en.wikipedia.org/wiki/Depth-first_search)
- [Breadth-first search](https://en.wikipedia.org/wiki/Breadth-first_search)
- [pygame documentation](https://www.pygame.org/docs/)

Own code/docs: [MIT licence](../LICENSE). pygame is installed separately and retains its [LGPL 2.1 licence](https://github.com/pygame/pygame/blob/2.6.1/docs/LGPL.txt). Its default font and native dependencies retain upstream notices; our MIT licence does not relicense them. See [third-party notices](../THIRD_PARTY_NOTICES.md) before redistributing a packaged application.
