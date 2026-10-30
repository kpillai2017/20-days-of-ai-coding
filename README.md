# 20 Days of AI Coding

**One small project a day. Learn by building, reading and experimenting.**

A beginner-friendly series of AI-assisted coding projects: games, utilities and small experiments written in **Python** (with pygame where relevant) or **HTML + CSS + JavaScript**. AI helps with the coding; projects do not necessarily use AI themselves.

Each day should include runnable code, explanatory comments, installation and usage instructions, a walkthrough of how it works, tests where practical, and references for further learning.

## Project index

| Day | Project | Stack | Learn |
| --- | --- | --- | --- |
| 01 | [Pixel Life](day-01-pixel-life/) | HTML / CSS / JavaScript | Conway’s Game of Life, arrays, canvas, events and simulation loops |
| 02 | [Breakout](day-02-breakout/) | Python / pygame | Game loops, delta time, collision detection and game state |
| 03 | [Pocket Tasks](day-03-pocket-tasks/) | HTML / CSS / JavaScript | Forms, immutable state, safe DOM rendering and browser persistence |
| 04 | [Maze Explorer](day-04-maze-explorer/) | Python / pygame | DFS generation, backtracking, BFS pathfinding and graph invariants |
| 05 | [Typing Sprint](day-05-typing-sprint/) | HTML / CSS / JavaScript | Text input, elapsed-time deadlines, state machines and scoring |
| 06 | [Enigma Lab](day-06-enigma-lab/) | Python / pygame | Permutations, modular arithmetic, stateful ciphers and historical Enigma |
| 07 | [Engine Explorer](day-07-engine-explorer/) | HTML / CSS / JavaScript | 3D projection, slider-crank kinematics and two-/four-stroke cycles |
| 08 | [Koan Garden](day-08-koan-garden/) | HTML / CSS / JavaScript | Rule-based writing, keyword matching, safe DOM rendering and reflective interpretation |
| 09 | [Vector Tanks](day-09-vector-tanks/) | Python / pygame | First-person wireframes, 3D projection, swept collisions, tank controls and enemy AI |
| 10 | [Sudoku Studio](day-10-sudoku-studio/) | Python / pygame | Backtracking, MRV search, unique generation, pencil notes and undo |
| 11 | [Clockwork Chess](day-11-clockwork-chess/) | Python / pygame | VICE-inspired legal moves, alpha–beta search, 2D/3D views, character capture animation and sound |
| 12 | [Sort Lab](day-12-sort-lab/) | HTML / CSS / JavaScript | Nine sorting algorithms, lazy generators, visual playback and honest operation counters |
| 13 | [Horologium](day-13-clockwork/) | HTML / CSS / JavaScript | Local-time analog clock, procedural brass/walnut artwork, pendulum and synthesised chimes |
| 14 | [Monopoly](day-14-monopoly/) | Python / pygame | Classic British Monopoly (London), rule state machines, auctions, trading, finite resources and local human/computer seats |
| 15 | [Scrabble](day-15-scrabble/) | Python / pygame | Classic-English tile scoring, private racks, trie-based computer moves, hints and 2–4 local human/computer seats |

**Days 16–20:** not built yet. Each will be a separate small project in this repository.

## Run Day 15

See [Scrabble installation and controls](day-15-scrabble/README.md). From `day-15-scrabble`, install `requirements.txt` in a virtual environment and run `python main.py`. Configure 2–4 human/computer seats, or use `--demo` for four computers. Includes previewed scoring, blanks, exchanges, passes, hints and final rack adjustments.

Read [rules and compatibility limits](day-15-scrabble/RULES.md): the bundled CC0 Letterpress dictionary is not an official Scrabble lexicon, words are automatically adjudicated without challenges, and six scoreless turns end play. The project does not claim perfect compatibility with every official edition. See the [beginner code tour](day-15-scrabble/LEARNING_GUIDE.md) and [word-list provenance](day-15-scrabble/words/NOTICE.md).

## Run Day 14

See [Monopoly setup and controls](day-14-monopoly/README.md). Install pygame in a virtual environment, then run `python main.py` from `day-14-monopoly`. Configure 2–6 local human/computer seats, or use `--demo` for four computer players. Includes property auctions, trades with consent, mortgages, buildings, jail, cards, debt and bankruptcy. Implements the British London edition with classic property names, stations and pound sterling. Read [rules and explicit fidelity limits](day-14-monopoly/RULES.md): this educational implementation is not certified rules-perfect or an official licensed product.

Follow the [beginner code tour](day-14-monopoly/LEARNING_GUIDE.md) and [references/rights notes](day-14-monopoly/REFERENCES.md).

## Run Day 13

Open `day-13-clockwork/index.html` directly. Enjoy an original walnut-cased clock illustration with ivory dial, exposed brass gears, weights and pendulum, synchronised to your device's local time. The original 2D view is labelled v0.1; toggle to the separate v0.2 solid 3D view, left-drag to rotate freely and reset its default camera. Enable sound for tick/tock, quarter phrases and hourly 1–12 strikes. Preview controls, volume, glass/labels, sweep seconds and reduced-motion support are included. This is a visual model, not a physics-accurate mechanism.

See [setup/audio behaviour](day-13-clockwork/README.md), [mechanism explanation](day-13-clockwork/MECHANISM.md) and [beginner code tour](day-13-clockwork/LEARNING_GUIDE.md). The requested Clock3D reference is inspiration only; no source/assets were reused.

## Run Day 12

Open `day-12-sort-lab/index.html` directly, or see the [setup and controls](day-12-sort-lab/README.md). Explore bubble, selection, insertion, merge, quick, heap, Shell, counting and radix sort with Start/Stop/Step/Reset, speed and item sliders, and input patterns. Changing algorithm preserves the original dataset for comparison. The dashboard shows operation captions, pseudocode, counters and variant-specific complexity.

Read the [algorithm field guide](day-12-sort-lab/ALGORITHMS.md) and [beginner code tour](day-12-sort-lab/LEARNING_GUIDE.md). Tests: `node --test day-12-sort-lab/tests/algorithms.test.cjs` (Node.js 22+).

## Run Day 11

See [Clockwork Chess setup and controls](day-11-clockwork-chess/README.md). Install `pygame==2.6.1` in a virtual environment and run `python main.py` from `day-11-clockwork-chess`. Play the computer or another local player with switchable 2D/3D views (V), original medieval-style characters, six piece-specific capture styles and synthesised sound. The clear Python engine follows selected VICE techniques, with upstream MIT attribution retained; this is not VICE feature parity or a Battle Chess asset recreation.

Read the [beginner guide](day-11-clockwork-chess/LEARNING_GUIDE.md) and [source/licence mapping](day-11-clockwork-chess/SOURCE_NOTES.md).

## Run Day 10

See [Sudoku Studio setup and controls](day-10-sudoku-studio/README.md). Install `pygame==2.6.1` in a virtual environment, then run `python main.py` from `day-10-sudoku-studio`. Generate Easy/Medium/Hard puzzles, enter digits, use pencil marks/hints/undo, or enter a custom board and solve it. Generated grids have exactly one solution; difficulty labels use documented clue-count bands rather than guaranteed human-technique grades.

Read the [beginner algorithm and UI guide](day-10-sudoku-studio/LEARNING_GUIDE.md) to learn backtracking, uniqueness checks and responsive background search.

## Run Day 09

See [Vector Tanks setup and controls](day-09-vector-tanks/README.md). Install `pygame==2.6.1` in a virtual environment, then run `python main.py` from `day-09-vector-tanks`. Press Enter to deploy, use arrows/WASD to drive and Space to fire. Cabinet-inspired independent tracks use T/G (left) and U/J (right). Includes radar, wireframe cover, three enemy types and original synthesised audio. This is an original Battlezone (1980)-inspired tribute, not a ROM-accurate recreation or official Atari product.

Start with the [beginner code guide](day-09-vector-tanks/LEARNING_GUIDE.md) and [history/fidelity notes](day-09-vector-tanks/HISTORY.md).

## Run Day 08

Open `day-08-koan-garden/index.html` directly, or serve that folder with `python3 -m http.server 8000 --bind 127.0.0.1` (Windows: `py`) and visit **http://127.0.0.1:8000**. Enter a statement or question to compose an original koan-inspired passage, then reveal a possible reading and reflection questions. Works offline using transparent English keyword rules, not a runtime AI model. No accounts, packages or saved entries.

See [setup and limitations](day-08-koan-garden/README.md), [beginner code tour](day-08-koan-garden/LEARNING_GUIDE.md) and [koan background](day-08-koan-garden/ABOUT_KOANS.md). The passages are creative prompts, not traditional Zen koans or authoritative teachings. Test from the repository root with `node --test day-08-koan-garden/tests/koan.test.cjs` (Node.js 22+).

## Run Day 07

Open `day-07-engine-explorer/index.html` directly, or serve that folder using `python3 -m http.server 8000 --bind 127.0.0.1` and visit **http://localhost:8000** (Windows: use `py`). Switch between two-/four-stroke engines, pause/scrub the cycle and drag or use arrow buttons/keys to orbit the real 3D cutaway. No runtime libraries or build step.

See [setup and controls](day-07-engine-explorer/README.md), [engine mechanics](day-07-engine-explorer/HOW_ENGINES_WORK.md) and [beginner code tour](day-07-engine-explorer/LEARNING_GUIDE.md). This is an idealised teaching model, not an engineering/combustion simulation. Test from the repository root with `node --test day-07-engine-explorer/tests/engine.test.cjs`.

## Run Day 06

With Python 3.9–3.13, from the repository root on macOS/Linux:

```sh
cd day-06-enigma-lab
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

Type or click A–Z, inspect the lamp and rotor windows, and reset before decrypting. Settings support three distinct rotors I–V, rings, initial windows and up to ten plug pairs; reflector B is fixed. **Historical learning only—not secure encryption.** See [setup and controls](day-06-enigma-lab/README.md), [mechanics](day-06-enigma-lab/HOW_ENIGMA_WORKS.md), [brief history](day-06-enigma-lab/HISTORY.md) and [beginner code tour](day-06-enigma-lab/LEARNING_GUIDE.md). Windows instructions and tests are in the day guide.

## Run Day 05

Open `day-05-typing-sprint/index.html` directly, or serve it from that folder with `python3 -m http.server 8000 --bind 127.0.0.1` and visit **http://localhost:8000** (Windows: use `py`). Type to start a 60-second attempt; correct mistakes with normal editing keys and restart for another try. No accounts or saved results.

Read [the setup/scoring guide](day-05-typing-sprint/README.md) and [the beginner learning tour](day-05-typing-sprint/LEARNING_GUIDE.md). WPM and accuracy use current matching characters; pasting is allowed, so this is practice rather than a verified benchmark. Test from the repository root with `node --test day-05-typing-sprint/tests/sprint.test.cjs`.

## Run Day 04

With Python 3.9–3.13, from the repository root on macOS/Linux:

```sh
cd day-04-maze-explorer
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py --seed 42
```

Arrows/WASD move, H reveals a route, R restarts the same maze, and N generates a fresh one. See [the Maze Explorer guide](day-04-maze-explorer/README.md) for Windows setup and [the learning tour](day-04-maze-explorer/LEARNING_GUIDE.md) for hand-worked DFS/BFS examples. Test from its folder with `python -m unittest discover -s tests -v`.

## Run Day 03

From the repository root:

```sh
cd day-03-pocket-tasks
python3 -m http.server 8000 --bind 127.0.0.1
```

Open **http://localhost:8000** (Windows: use `py` instead of `python3`). Use the same browser, host and port to keep accessing the same saved tasks. No runtime dependencies or accounts. Browser storage isn't a backup or cloud sync; clearing site data can remove tasks. See [the Pocket Tasks guide](day-03-pocket-tasks/README.md) for storage warnings, recovery, controls and the code walkthrough. For a slower introduction, follow [the beginner learning tour](day-03-pocket-tasks/LEARNING_GUIDE.md), including a glossary, debugging exercise and an end-to-end data trace.

Test from the repository root with `node --test day-03-pocket-tasks/tests/tasks.test.cjs` (Node.js 20+).

## Run Day 02

See [the Breakout guide](day-02-breakout/README.md) for Windows and macOS/Linux setup. With Python 3.9–3.13, from the repository root on macOS/Linux:

```sh
cd day-02-breakout
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

Move with arrows or A/D; Space launches; P pauses; R restarts. Run all Day 02 tests from that folder with `python -m unittest discover -s tests -v`.

## Run Day 01

Download and extract the repository, then open **`day-01-pixel-life/index.html`** in your browser. No installation, API key, build step or library is required.

Alternatively, from the repository folder:

```sh
cd day-01-pixel-life
python3 -m http.server 8000 --bind 127.0.0.1
```

Visit **http://localhost:8000**. On Windows use `py` instead of `python3`. Stop the server with Ctrl+C.

Read [the Day 01 guide](day-01-pixel-life/README.md) for controls, a code tour, troubleshooting, exercises and references.

## Test Day 01

With Node.js 20+ installed, from the repository root:

```sh
node --test day-01-pixel-life/tests/life.test.cjs
```

Node is only needed for the tests. GitHub Actions also runs them automatically on pushes and pull requests.

## Repository hygiene and development

The root [`.gitignore`](.gitignore) applies to **all projects and future day folders**. It excludes Python environments/bytecode, Node dependencies, build output, test reports, coverage, editor metadata, logs and local `.direnv/`, `.envrc` and `.env*` configuration. Local files remain on your machine; ignoring them does not delete them.

- Keep real credentials out of source and configuration committed to Git.
- Sanitised `.env.example` files are allowed; never put secrets in an example.
- JavaScript lockfiles are deliberately **not ignored**. If a future day adds dependencies, commit its lockfile for reproducible installs. Day 01 has none.
- Check `git status --short` before staging. For an ignored path, use `git check-ignore -v path/to/file` to see which rule applies.
- `.gitignore` does not untrack an already committed file. Review `git ls-files -ci --exclude-standard` for tracked files that now match ignore rules.

All seven projects separate rules from the interface: `life.js`/`app.js`, `game.py`/`main.py`, `tasks.js`/`app.js`, `maze.py`/`main.py`, `sprint.js`/`app.js`, `enigma.py`/`main.py`, and `engine.js`/`renderer.js`/`app.js`. Refactors should preserve that separation, update each day's walkthrough, and add regression tests for changed behavior.

### Run all checks

From the repository root, after installing each Python day's requirements in its own virtual environment:

```sh
node --check day-01-pixel-life/app.js
node --check day-01-pixel-life/life.js
node --test day-01-pixel-life/tests/life.test.cjs
node --check day-03-pocket-tasks/tasks.js
node --check day-03-pocket-tasks/app.js
node --test day-03-pocket-tasks/tests/tasks.test.cjs
node --check day-05-typing-sprint/sprint.js
node --check day-05-typing-sprint/app.js
node --test day-05-typing-sprint/tests/sprint.test.cjs
node --check day-07-engine-explorer/renderer.js
node --check day-07-engine-explorer/app.js
node --test day-07-engine-explorer/tests/engine.test.cjs
cd day-02-breakout
.venv/bin/python -m unittest discover -s tests -v
cd ../day-04-maze-explorer
.venv/bin/python -m unittest discover -s tests -v
cd ../day-06-enigma-lab
.venv/bin/python -m unittest discover -s tests -v
```

On Windows, use `.venv\\Scripts\\python.exe` for the final command. CI runs these test suites and a headless pygame smoke test on every push and pull request.

## A learning rhythm

1. Run the project before studying it.
2. Read its README and follow one input through the code.
3. Predict what a small change will do, then try it.
4. Run the tests and add a test for a new behaviour.
5. Write down what you learned before starting the next day.

## Licence and attribution

This repository's own code and documentation are available under the **[MIT licence](LICENSE)**, copyright © 2026 kpillai2017. You may reuse, modify and redistribute them subject to the licence, including retaining its notice. The software is provided without warranty.

Third-party dependencies and reference material retain their own licences. In particular, Day 02 uses pygame, which is LGPL-licensed; our MIT licence does not replace its terms. Read [Third-party notices and project provenance](THIRD_PARTY_NOTICES.md) and each day's reference section for details.

The projects were built with AI coding assistance, then reviewed and tested. They are educational implementations and are not affiliated with the creators or publishers of the original games.
