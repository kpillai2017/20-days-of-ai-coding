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

**Days 08–20:** not built yet. Each will be a separate small project in this repository.

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
