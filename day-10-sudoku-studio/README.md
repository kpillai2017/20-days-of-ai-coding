# Day 10 · Sudoku Studio

A Python/Pygame **Sudoku generator, player and solver**, with easy, medium and hard puzzles, pencil notes, hints, undo and a custom-board mode.

## Install and run

Use **Python 3.9–3.13**; 3.12/3.13 are recommended for convenient dependency wheels.

macOS/Linux, from the repository root:

```sh
cd day-10-sudoku-studio
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

Windows PowerShell:

```powershell
cd day-10-sudoku-studio
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

The environment isolates dependencies. No account, API, server or network access is needed. Optional: `python main.py --seed 42` makes a repeatable series of puzzles: New uses seed 43, then 44, etc. Seeds reproduce results for the same implementation. `python main.py --seed 42 --frames 30` runs a short window-loop smoke test.

## Sudoku rules

Fill the 9×9 grid using 1–9 so **each row, column and 3×3 box contains each digit exactly once**. Dark given clues are fixed; your entries are blue. Red cells indicate direct duplicates, not necessarily every wrong entry. A locally legal digit may still lead to no solution.

## Controls

Buttons provide mouse equivalents for these keys:

| Key | Action |
| --- | --- |
| Click cell / arrows | Select / move, wrapping at edges |
| 1–9 / keypad / digit buttons | Enter digit |
| Delete, Backspace or 0 | Erase value; in pencil mode, clear that cell's notes |
| M | Toggle pencil mode; digits toggle small manual marks on blank cells |
| C | Show/hide automatically allowed candidates where no manual notes exist |
| Z | Undo last board edit, note change, hint or solution reveal |
| H | Reveal one value from the generated solution |
| S | Solve using current entries as constraints |
| R | Reset to original clues, clear notes/history/assistance and timer |
| N | New puzzle at selected difficulty |
| E / Custom board | Blank board for entering your own puzzle |
| P / Space | Pause/resume; paused grid digits are hidden |
| Esc | Quit |

Selecting Easy/Medium/Hard immediately generates a **new** puzzle. New/difficulty/custom/reset actions discard progress without confirmation; no work is saved to disk. Editing is disabled during background generation/solving. Losing window focus pauses; resume explicitly. Resize preserves the board's aspect ratio.

### Difficulty, honestly defined

| Label | Allowed givens | Usual target |
| --- | --- | --- |
| Easy | 40–44 | 42 |
| Medium | 33–37 | 35 |
| Hard | 27–31 | 29 |

These are **clue-count bands, not a human-technique rating**. Fewer clues do not always mean a harder puzzle, and a hard-labelled grid may still yield to simple logic. The generator does not claim expert grading, rotational symmetry or minimality.

Every generated puzzle is checked to have **exactly one solution**. Starting from a randomly filled valid board, remove a clue only when a solver counting up to two solutions still finds one. Generation retries at most 12 times to hit the requested band; failure is reported rather than returning a wrong-band or nonunique puzzle. A single worker handles generation so the window remains responsive; the main thread alone edits/draws the session.

### Solver, hints and custom puzzles

Solve preserves all entered numbers as constraints. If those entries contradict Sudoku or cannot extend to a solution, it reports failure without replacing your board. Undo/erase/reset mistaken entries and try again. A successful reveal can be undone.

Hint is a **value reveal**, not a human logical explanation. It fixes the selected editable blank/wrong cell, or the first other editable blank/wrong cell. Hint and Solve mark the result **assisted**; undo restores the previous assistance flag. Candidate display is a local rule check, not a proof that a value belongs in the solution. Manual notes are not automatically pruned from peers.

Custom board starts blank; enter the puzzle's clues as editable numbers and select Solve. It returns **one solution if any exists**, without claiming uniqueness. Hints are disabled because no authoritative generated solution exists. Reset returns a custom board to blank, not to the values you typed. There is no import/export, save file or printing feature.

The timer counts active, unpaused play time, excludes background searches, and stops on completion. Long frames are capped at 0.1 seconds, so it is a convenience timer, not a competition clock.

## Learn and test

- [Beginner code guide](LEARNING_GUIDE.md): grid indexing, candidates, recursion, backtracking, generation and UI concurrency.
- `sudoku.py`: Pygame-free rules, solver, generator and undoable session.
- `main.py`: drawing, events, scaled mouse coordinates and worker hand-off.
- `tests/test_sudoku.py`: model tests; `tests/test_ui.py`: headless UI and regression tests.

From this folder:

```sh
python -m unittest discover -s tests -v
```

Model-only checks need no Pygame:

```sh
python -m unittest discover -s tests -p test_sudoku.py -v
```

Headless macOS/Linux:

```sh
SDL_VIDEODRIVER=dummy PYGAME_HIDE_SUPPORT_PROMPT=1 python -m unittest discover -s tests -v
SDL_VIDEODRIVER=dummy python main.py --seed 42 --frames 30
```

PowerShell: set `$env:SDL_VIDEODRIVER='dummy'` before those Python commands. Tests exercise model invariants and event handlers but cannot guarantee readability on every monitor or accessibility for every player.

## References, origins and licence

Sudoku's modern history includes Howard Garns's *Number Place* puzzle, published in 1979, and subsequent popularisation in Japan. The arithmetic value of a digit is irrelevant: this is a constraint puzzle using nine distinct symbols.

- [Britannica: Sudoku](https://www.britannica.com/topic/sudoku) — rules and historical background.
- [Peter Norvig: Solving Every Sudoku Puzzle](https://norvig.com/sudoku.html) — further reading on constraint propagation and search. Our implementation is independently written, not copied from this article, and does not implement all its propagation techniques.
- [Python dataclasses](https://docs.python.org/3/library/dataclasses.html), [random.Random](https://docs.python.org/3/library/random.html), [ThreadPoolExecutor](https://docs.python.org/3/library/concurrent.futures.html), [unittest](https://docs.python.org/3/library/unittest.html).
- [Pygame documentation](https://www.pygame.org/docs/) — Surface, Rect, drawing and events.

Own source and prose are original AI-assisted educational work under the repository's [MIT licence](../LICENSE). No puzzle collection, images, sounds, external font files or third-party solver code are bundled. Pygame is separately installed under its own LGPL terms; its bundled default font and native dependencies have their own terms. Linked publications retain their authors' rights; see [notices](../THIRD_PARTY_NOTICES.md). Generated puzzles are made locally, not downloaded from a provider.
